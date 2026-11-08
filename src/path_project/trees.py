"""Fixed-budget tree comparison on locked tuning folds; never final-test access."""
import hashlib,json,sys,time
from pathlib import Path
from importlib.metadata import version,PackageNotFoundError
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from path_project.baselines import (make_pipeline,metrics,reliability,fit_sigmoid,logits,
    choose_threshold,CalibratedBaseline,verify_run as verify_baselines,KEYS)
from path_project.cohort import json_write
from path_project.documentation import fingerprint
from path_project.evaluation import load_locked,load_development,fit_training_pipeline,assert_batch,BoundaryError
from path_project.final_inputs import validate_final_inputs


def available_booster():
    try:
        from xgboost import XGBClassifier
        return 'xgboost',{'available':True,'version':version('xgboost'),'alternative_used':False}
    except (ImportError,OSError) as error:
        return 'hist_gradient_boosting',{'available':False,'reason':f'{type(error).__name__}: {error}','alternative_used':True}


def candidates_for(settings,boost_family):
    candidates=[]
    for family,key,prefix in [('random_forest','random_forest','rf'),(boost_family,'xgboost' if boost_family=='xgboost' else 'alternative','xgb' if boost_family=='xgboost' else 'hgb')]:
        for index,params in enumerate(settings[key]['search']):
            for profile in settings['profiles']:
                for weight in settings['class_weight_options']:
                    candidates.append({'name':f'{prefix}_{profile}_s{index}_{weight}','family':family,'profile':profile,'weight':weight,'params':{**settings[key]['fixed'],**params}})
    return candidates


def tree_pipeline(candidate,final,baseline_settings,settings,training_y):
    counts=pd.Series(training_y).value_counts()
    if not {0,1}.issubset(counts.index):raise BoundaryError('Training fold must contain both classes.')
    ratio=float(counts[0]/counts[1])
    weight='balanced' if candidate['weight']=='balanced' else None
    params={**candidate['params'],'random_state':settings['seed']}
    if candidate['family']=='random_forest':model=RandomForestClassifier(**params,class_weight=weight)
    elif candidate['family']=='xgboost':
        from xgboost import XGBClassifier
        model=XGBClassifier(**params,scale_pos_weight=ratio if weight else 1.0)
    else:model=HistGradientBoostingClassifier(**params,class_weight=weight)
    pipeline=make_pipeline({'kind':'logistic','profile':candidate['profile'],'class_weight':None},final,baseline_settings)
    pipeline.set_params(model=model)
    return pipeline,ratio if weight else None


def quality_check(score):
    for weighting in ['participant_equal','interval_equal']:
        for name in ['brier','log_loss','average_precision','roc_auc']:
            if score[weighting][name] is None or not np.isfinite(score[weighting][name]):raise BoundaryError('Candidate failed finite probability/discrimination quality checks.')


def select_candidate(summaries):
    if not summaries:raise BoundaryError('No candidate summaries.')
    # Ordered summaries preserve the locked deterministic simplicity tie break.
    for row in summaries:quality_check(row['pooled_oof'])
    return max(summaries,key=lambda row:row['mean_fold_participant_metrics']['average_precision'])['model']


def signature_for(root,settings,baseline_manifest,split_manifest,dependency):
    paths=['configs/tree_models.json','configs/baseline_models.json','configs/feature_mapping_final.json',*settings['code_inputs']]
    parts={'baseline_signature':baseline_manifest['signature'],'split_signature':split_manifest['signature'],'baseline_outputs':baseline_manifest['output_sha256'],
           'files':{name:fingerprint(root/name) for name in paths},'dependency':dependency,'python':sys.version,
           'versions':{name:version(name) for name in ['scikit-learn','numpy','pandas','pyarrow','joblib']}}
    return hashlib.sha256(json.dumps(parts,sort_keys=True).encode()).hexdigest(),parts


def verify_tree_run(root):
    root=Path(root);settings=json.loads((root/'configs/tree_models.json').read_text())
    _,_,split,_,_=load_locked(root);base=verify_baselines(root)
    _,dependency=available_booster();signature,_=signature_for(root,settings,base,split,dependency)
    path=root/settings['output_dir']/'manifest.json'
    if not path.is_file():raise BoundaryError('Tree run incomplete; preserve existing files and inspect, never overwrite.')
    manifest=json.loads(path.read_text())
    if manifest['signature']!=signature:raise BoundaryError('Tree run signature changed; no silent retraining or overwrite.')
    for name,digest in manifest['output_sha256'].items():
        if not (root/name).is_file() or fingerprint(root/name)!=digest:raise BoundaryError('Saved tree artifact/report changed or missing.')
    return manifest


def train_tree_models(root):
    root=Path(root);started=time.perf_counter()
    settings=json.loads((root/'configs/tree_models.json').read_text())
    baseline_settings=json.loads((root/'configs/baseline_models.json').read_text())
    config,cc,split,people,rows=load_locked(root);base_manifest=verify_baselines(root)
    final,_=validate_final_inputs(root);boost_family,dependency=available_booster()
    signature,provenance=signature_for(root,settings,base_manifest,split,dependency)
    output=root/settings['output_dir'];report=root/settings['report_dir']
    if output.exists() or report.exists():
        verify_tree_run(root);return 'reused_verified_run',json.loads((report/'results.json').read_text())
    output.mkdir(parents=True,exist_ok=False);report.mkdir(parents=True,exist_ok=False)
    (output/'folds').mkdir();(output/'models').mkdir()
    candidates=candidates_for(settings,boost_family)
    baseline_results=json.loads((root/baseline_settings['report_dir']/'results.json').read_text())
    baseline_oof=pd.read_parquet(root/baseline_settings['output_dir']/'oof_predictions.parquet')
    fold_results=[];predictions=[]
    for fold in range(config['folds']):
        train=load_development(root,'fit',fold);valid=load_development(root,'validation',fold)
        if set(train['PERSONID'])&set(valid['PERSONID']):raise BoundaryError('Tree fold participant overlap.')
        # Validate exactly the same evaluation keys/labels as every saved baseline.
        for name,stored in baseline_oof.loc[baseline_oof['fold'].eq(fold)].groupby('model'):
            merged=valid[KEYS+['outcome_p30d']].merge(stored[KEYS+['outcome_p30d']],on=KEYS,how='outer',indicator=True,validate='one_to_one')
            if not merged['_merge'].eq('both').all() or not merged['outcome_p30d_x'].eq(merged['outcome_p30d_y']).all():raise BoundaryError('Baseline/tree validation keys or labels differ.')
        for candidate in candidates:
            features=final['feature_sets'][candidate['profile']]
            training=train[KEYS+features+['outcome_p30d']];validation=valid[KEYS+features+['outcome_p30d']]
            pipeline,ratio=tree_pipeline(candidate,final,baseline_settings,settings,training['outcome_p30d'])
            begin=time.perf_counter()
            fitted=fit_training_pipeline(pipeline,training,rows,config,features,fold)
            fit_seconds=time.perf_counter()-begin;begin=time.perf_counter()
            p=fitted.predict_proba(validation[features])[:,1]
            predict_seconds=time.perf_counter()-begin
            score=metrics(validation,p,baseline_settings['fixed_diagnostic_threshold']);quality_check(score)
            fold_results.append({'model':candidate['name'],'fold':fold,'training_records':len(training),'training_people':int(training['PERSONID'].nunique()),'training_negative_positive_ratio':float(training['outcome_p30d'].eq(0).sum()/training['outcome_p30d'].eq(1).sum()),'training_weight_ratio_if_enabled':ratio,'fit_seconds':fit_seconds,'predict_seconds':predict_seconds,'metrics':score,'calibration_bins':reliability(validation,p,baseline_settings['calibration_bin_edges'])})
            joblib.dump(fitted,output/'folds'/f"{candidate['name']}_fold{fold}.joblib")
            local=validation[KEYS+['outcome_p30d']].copy();local['model']=candidate['name'];local['fold']=fold;local['probability']=p;predictions.append(local)
            print(f"Fold {fold} {candidate['name']}: AP={score['participant_equal']['average_precision']:.4f}, Brier={score['participant_equal']['brier']:.4f}, fit={fit_seconds:.2f}s",flush=True)
    oof=pd.concat(predictions,ignore_index=True);oof.to_parquet(output/'oof_predictions.parquet',index=False)
    summaries=[]
    for candidate in candidates:
        folds=[r for r in fold_results if r['model']==candidate['name']];local=oof.loc[oof['model'].eq(candidate['name'])]
        row={'model':candidate['name'],'family':candidate['family'],'profile':candidate['profile'],'weight':candidate['weight'],'params':candidate['params'],
             'mean_fold_participant_metrics':{},'fold_sd_descriptive_only':{},'pooled_oof':metrics(local,local['probability'],.5),
             'pooled_oof_calibration_bins':reliability(local,local['probability'],baseline_settings['calibration_bin_edges']),
             'total_fold_fit_seconds':sum(f['fit_seconds'] for f in folds),'total_fold_predict_seconds':sum(f['predict_seconds'] for f in folds)}
        for metric in ['average_precision','roc_auc','brier','log_loss','prevalence','mean_predicted_probability','f1','precision','sensitivity','specificity']:
            values=[f['metrics']['participant_equal'][metric] for f in folds]
            row['mean_fold_participant_metrics'][metric]=float(np.mean(values));row['fold_sd_descriptive_only'][metric]=float(np.std(values,ddof=1))
        summaries.append(row)
    baselines=[{**row,'family':'baseline','weight':row['class_weight'],'total_fold_fit_seconds':None,'runtime_limitation':'Not recorded in stage 7; not fabricated or retrained for timing.'} for row in baseline_results['candidates']]
    combined=baselines+summaries;winner=select_candidate(combined)
    # Refit only best per tree family/profile; all searched fold Pipelines retained.
    refits=[];models={};all_training=load_development(root,'fit')
    for family in ['random_forest',boost_family]:
        for profile in settings['profiles']:
            choices=[row for row in summaries if row['family']==family and row['profile']==profile]
            best=max(choices,key=lambda row:row['mean_fold_participant_metrics']['average_precision'])
            candidate=next(c for c in candidates if c['name']==best['model']);features=final['feature_sets'][profile]
            training=all_training[KEYS+features+['outcome_p30d']]
            pipeline,ratio=tree_pipeline(candidate,final,baseline_settings,settings,training['outcome_p30d'])
            begin=time.perf_counter();fitted=fit_training_pipeline(pipeline,training,rows,config,features);seconds=time.perf_counter()-begin
            path=output/'models'/(candidate['name']+'.joblib');joblib.dump(fitted,path);models[candidate['name']]=fitted
            np.testing.assert_allclose(fitted.predict_proba(training[features]),joblib.load(path).predict_proba(training[features]),rtol=0,atol=1e-12)
            refits.append({'model':candidate['name'],'family':family,'profile':profile,'features':features,'transformed_features':fitted[:-1].get_feature_names_out().tolist(),'training_records':len(training),'training_people':int(training['PERSONID'].nunique()),'training_weight_ratio_if_enabled':ratio,'fit_seconds':seconds,'serialization_predictions_consistent':True})
    if winner in {r['model'] for r in baselines}:
        if winner!=baseline_results['selected_model']:raise BoundaryError('Baseline winner differs from its saved AP selection.')
        bundle=joblib.load(root/baseline_settings['output_dir']/'selected_calibrated.joblib')
        joblib.dump(bundle,output/'selected_calibrated.joblib')
        calibration={**baseline_results['calibration'],'stage8_action':'Reused existing winning baseline calibration and threshold unchanged; no new reserved-group fitting.'}
    else:
        candidate=next(c for c in candidates if c['name']==winner);features=final['feature_sets'][candidate['profile']];base=models[winner]
        calibration_data=load_development(root,'calibration')[KEYS+features+['outcome_p30d']]
        threshold_data=load_development(root,'threshold')[KEYS+features+['outcome_p30d']]
        assert_batch(calibration_data,rows,config,features,'calibration');assert_batch(threshold_data,rows,config,features,'threshold')
        if set(all_training['PERSONID'])&set(calibration_data['PERSONID']) or set(all_training['PERSONID'])&set(threshold_data['PERSONID']) or set(calibration_data['PERSONID'])&set(threshold_data['PERSONID']):raise BoundaryError('Tree calibration/threshold/training participant overlap.')
        raw_cal=base.predict_proba(calibration_data[features])[:,1];begin=time.perf_counter()
        sigmoid=fit_sigmoid(calibration_data,raw_cal,baseline_settings);cal_seconds=time.perf_counter()-begin
        epsilon=baseline_settings['calibrator']['clip_epsilon'];raw=base.predict_proba(threshold_data[features])[:,1]
        calibrated=sigmoid.predict_proba(logits(raw,epsilon))[:,1];threshold,best_f1=choose_threshold(threshold_data,calibrated)
        bundle=CalibratedBaseline(base,sigmoid,epsilon,threshold);joblib.dump(bundle,output/'selected_calibrated.joblib')
        np.testing.assert_allclose(bundle.predict_proba(threshold_data[features]),joblib.load(output/'selected_calibrated.joblib').predict_proba(threshold_data[features]),rtol=0,atol=1e-12)
        local=calibration_data[KEYS+['outcome_p30d']].copy();local['raw_probability']=raw_cal;local['calibrated_probability']=sigmoid.predict_proba(logits(raw_cal,epsilon))[:,1];local.to_parquet(output/'calibration_predictions.parquet',index=False)
        local=threshold_data[KEYS+['outcome_p30d']].copy();local['raw_probability']=raw;local['calibrated_probability']=calibrated;local.to_parquet(output/'threshold_predictions.parquet',index=False)
        calibration={'selected_model':winner,'stage8_action':'Selected classifier by tuning AP before opening reserved groups; new sigmoid fitted only on calibration participants; threshold only on threshold group.',
            'sigmoid_fit_seconds':cal_seconds,'chosen_threshold':threshold,'threshold_selection_f1':best_f1,
            'calibration_group_fit_apparent_raw':metrics(calibration_data,raw_cal,.5),
            'calibration_group_fit_apparent_calibrated':metrics(calibration_data,sigmoid.predict_proba(logits(raw_cal,epsilon))[:,1],.5),
            'threshold_group_raw_fixed_0_5':metrics(threshold_data,raw,.5),'threshold_group_calibrated_fixed_0_5':metrics(threshold_data,calibrated,.5),
            'threshold_selection_apparent_at_chosen_threshold':metrics(threshold_data,calibrated,threshold),
            'threshold_group_raw_calibration_bins':reliability(threshold_data,raw,baseline_settings['calibration_bin_edges']),
            'threshold_group_calibrated_bins':reliability(threshold_data,calibrated,baseline_settings['calibration_bin_edges']),
            'caution':'Calibration-fit scores apparent; chosen-threshold metrics apparent for threshold selection. Not final-test performance or a clinical guarantee. Do not re-rank candidates using these reserved diagnostics.'}
    results={'candidates':combined,'selected_model':winner,'search_candidates':candidates,'new_candidate_count':len(candidates),'new_fold_fit_count':len(fold_results),'refits':refits,'dependency':dependency,
        'selection_rule':settings['selection_rule'],'probability_quality_policy':settings['probability_quality_policy'],
        'pr_metric':baseline_results['pr_metric'],'baseline_prevalence_context':baselines[0]['mean_fold_participant_metrics']['prevalence'],
        'calibration':calibration,'same_baseline_validation_keys_and_labels_verified':True,'no_imbalance_resampling':True,
        'no_final_test_features_or_outcomes_read':True,'reserved_groups_used_to_select_model':False,
        'elapsed_training_workflow_seconds':time.perf_counter()-started}
    json_write(report/'results.json',results);json_write(report/'fold_metrics.json',fold_results);json_write(report/'provenance.json',provenance)
    files=[p for folder in [output,report] for p in folder.rglob('*') if p.is_file()]
    json_write(output/'manifest.json',{'signature':signature,'provenance':provenance,'output_sha256':{str(p.relative_to(root)):fingerprint(p) for p in files},'policy':'Immutable verified reuse; no silent refitting or replacement of existing outputs.'})
    verify_tree_run(root)
    return 'trained_new_immutable_run',results
