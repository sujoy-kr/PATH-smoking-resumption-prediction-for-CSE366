"""One-shot, pre-frozen final evaluation. No fitting or test-driven selection."""
import datetime,hashlib,json,os,shutil,sys,time
from pathlib import Path
from importlib.metadata import version
import joblib
import numpy as np
import pandas as pd
from path_project.cohort import json_write
from path_project.documentation import fingerprint
from path_project.evaluation import load_locked,BoundaryError
from path_project.outputs import verify_outputs
from path_project.trees import verify_tree_run
from path_project.baselines import verify_run as verify_baselines

KEYS=['PERSONID','starting_wave','followup_wave']
METRICS=['prevalence','average_precision','roc_auc','brier','log_loss','mean_probability','precision','recall','specificity','f1']


class MetricCalculator:
    """Weighted tie-aware AP/ROC with reusable score ordering for bootstrap."""
    def __init__(self,y,p,threshold,epsilon):
        self.y=np.asarray(y,dtype=int);self.p=np.asarray(p,dtype=float);self.threshold=float(threshold)
        if len(self.y)!=len(self.p) or not np.isin(self.y,[0,1]).all() or not np.isfinite(self.p).all() or ((self.p<0)|(self.p>1)).any():raise BoundaryError('Invalid frozen-test labels/probabilities; values suppressed.')
        self.order=np.argsort(-self.p,kind='stable');ordered=self.p[self.order]
        self.starts=np.r_[0,np.flatnonzero(ordered[1:]!=ordered[:-1])+1]
        clipped=np.clip(self.p,epsilon,1-epsilon)
        self.loss=-(self.y*np.log(clipped)+(1-self.y)*np.log1p(-clipped))
        self.predicted=self.p>=threshold
    def evaluate(self,weights):
        w=np.asarray(weights,dtype=float)
        if len(w)!=len(self.y) or not np.isfinite(w).all() or (w<0).any() or w.sum()<=0:raise BoundaryError('Invalid metric weights.')
        pos=float(np.dot(w,self.y));neg=float(np.dot(w,1-self.y));total=pos+neg
        positive=np.add.reduceat((w*self.y)[self.order],self.starts)
        negative=np.add.reduceat((w*(1-self.y))[self.order],self.starts)
        tp_curve=np.cumsum(positive);all_curve=np.cumsum(positive+negative)
        precision_curve=np.divide(tp_curve,all_curve,out=np.zeros_like(tp_curve),where=all_curve>0)
        ap=float(np.sum(precision_curve*positive)/pos) if pos>0 else None
        roc=float(np.clip(np.sum(positive*(neg-np.cumsum(negative)+.5*negative))/(pos*neg),0,1)) if pos>0 and neg>0 else None
        tp=float(w[(self.y==1)&self.predicted].sum());fp=float(w[(self.y==0)&self.predicted].sum())
        fn=float(w[(self.y==1)&~self.predicted].sum());tn=float(w[(self.y==0)&~self.predicted].sum())
        result={'prevalence':pos/total,'average_precision':ap,'roc_auc':roc,'brier':float(np.dot(w,(self.p-self.y)**2)/total),'log_loss':float(np.dot(w,self.loss)/total),'mean_probability':float(np.dot(w,self.p)/total),
                'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,'specificity':tn/(tn+fp) if tn+fp else None,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
        result['confusion']={'tn':tn,'fp':fp,'fn':fn,'tp':tp}
        return result


def cluster_structure(ids):
    codes,people=pd.factorize(pd.Series(ids),sort=True);counts=np.bincount(codes)
    return codes,counts


def participant_weights(ids):
    codes,counts=cluster_structure(ids);return 1.0/counts[codes]


def bootstrap_weights(ids,rng):
    codes,counts=cluster_structure(ids);draws=rng.integers(0,len(counts),size=len(counts));multiplicity=np.bincount(draws,minlength=len(counts))
    # Each sampled occurrence of a participant contributes weight one, including
    # repeated draws. Do not regroup duplicated draws into one cluster.
    return multiplicity[codes]/counts[codes]


def interval(values,repetitions,confidence):
    finite=[float(v) for v in values if v is not None and np.isfinite(v)]
    alpha=(1-confidence)/2
    return {'lower':float(np.quantile(finite,alpha)) if finite else None,'upper':float(np.quantile(finite,1-alpha)) if finite else None,'valid_replicates':len(finite),'undefined_replicates':repetitions-len(finite),'method':'participant-cluster percentile bootstrap','confidence_level':confidence}


def calibration_bins(y,p,ids,settings):
    y=np.asarray(y);p=np.asarray(p);weights=participant_weights(ids);edges=settings['calibration_bin_edges'];index=np.minimum(np.searchsorted(edges,p,side='right')-1,len(edges)-2)
    rng=np.random.default_rng(settings['seed']);samples=[[] for _ in range(len(edges)-1)]
    for _ in range(settings['bootstrap_replicates']):
        w=bootstrap_weights(ids,rng)
        for i in range(len(samples)):
            mask=index==i;mass=w[mask].sum();samples[i].append(float(np.dot(w[mask],y[mask])/mass) if mass else None)
    rows=[]
    for i in range(len(samples)):
        mask=index==i;mass=weights[mask].sum()
        rows.append({'lower':edges[i],'upper':edges[i+1],'records':int(mask.sum()),'positive_records':int(y[mask].sum()),'mean_probability':float(np.average(p[mask],weights=weights[mask])) if mass else None,'observed_fraction':float(np.average(y[mask],weights=weights[mask])) if mass else None,'observed_fraction_ci':interval(samples[i],settings['bootstrap_replicates'],settings['confidence_level'])})
    return rows


def compare_predictions(frame,models,settings):
    y=frame['outcome_p30d'].to_numpy(dtype=int);ids=frame['PERSONID'];weights=participant_weights(ids)
    calculators={name:MetricCalculator(y,frame['probability__'+name],spec['threshold'],settings['log_loss_epsilon']) for name,spec in models.items()}
    samples={name:{metric:[] for metric in METRICS} for name in models}
    differences={name:{metric:[] for metric in ['average_precision','brier','roc_auc']} for name in models if name!='selected_calibrated'}
    rng=np.random.default_rng(settings['seed'])
    for _ in range(settings['bootstrap_replicates']):
        w=bootstrap_weights(ids,rng);computed={name:calculator.evaluate(w) for name,calculator in calculators.items()}
        for name,scores in computed.items():
            for metric in METRICS:samples[name][metric].append(scores[metric])
        selected=computed['selected_calibrated']
        for name,metrics in differences.items():
            for metric in metrics:
                a,b=selected[metric],computed[name][metric]
                differences[name][metric].append(a-b if a is not None and b is not None else None)
    result={}
    for name,calculator in calculators.items():
        result[name]={'description':models[name]['description'],'threshold':models[name]['threshold'],'participant_equal':calculator.evaluate(weights),'interval_equal':calculator.evaluate(np.ones(len(frame))),
                      'confidence_intervals':{metric:interval(values,settings['bootstrap_replicates'],settings['confidence_level']) for metric,values in samples[name].items()}}
    paired={name:{metric:interval(values,settings['bootstrap_replicates'],settings['confidence_level']) for metric,values in metrics.items()} for name,metrics in differences.items()}
    return result,paired


def rate_summary(frame,settings,seed_offset=0):
    if frame.empty:return {'records':0,'people':0,'positive_records':0,'interval_rate':None,'participant_equal_rate':None,'rate_ci':interval([],settings['bootstrap_replicates'],settings['confidence_level'])}
    y=frame['outcome_p30d'].to_numpy(dtype=int);ids=frame['PERSONID'];w=participant_weights(ids);rng=np.random.default_rng(settings['seed']+seed_offset)
    samples=[]
    for _ in range(settings['bootstrap_replicates']):
        draw=bootstrap_weights(ids,rng);samples.append(float(np.average(y,weights=draw)))
    return {'records':len(frame),'people':int(ids.nunique()),'positive_records':int(y.sum()),'interval_rate':float(y.mean()),'participant_equal_rate':float(np.average(y,weights=w)),'rate_ci':interval(samples,settings['bootstrap_replicates'],settings['confidence_level'])}


def subgroup_masks(frame,settings):
    recency=frame['last_cigarette_recency_days'];lower=settings['recent_lower_exclusive_days'];upper=settings['recent_upper_inclusive_days']
    masks=[('recent_observed_last_use_30_to_365_25_days',recency.gt(lower)&recency.le(upper)),('longer_observed_last_use_over_365_25_days',recency.gt(upper)),('unknown_last_use_recency',recency.isna()),
           ('recent_boundary_excluded_sensitivity',recency.gt(lower)&recency.le(upper)&~frame['recency_boundary_report'].fillna(False))]
    for label,codes in settings['age_groups'].items():masks.append(('age_'+label,frame['age_band'].isin(codes)))
    masks.append(('age_unknown',frame['age_band'].isna()))
    for label,codes in settings['sex_groups'].items():masks.append(('recorded_sex_'+label,frame['sex_recorded'].isin(codes)))
    masks.append(('recorded_sex_unknown',frame['sex_recorded'].isna()))
    return [(name,mask.fillna(False)) for name,mask in masks]


def subgroup_results(frame,settings,selected_threshold):
    results=[]
    for index,(name,mask) in enumerate(subgroup_masks(frame,settings)):
        data=frame.loc[mask];record=rate_summary(data,settings,index+10)
        supported=record['people']>=settings['subgroup_min_people'] and record['positive_records']>=settings['subgroup_min_positive_records'] and record['records']-record['positive_records']>=settings['subgroup_min_negative_records']
        row={'subgroup':name,**record,'performance_supported':supported,'performance':None,'limitation':None}
        if supported:
            # Reuse paired bootstrap implementation for one frozen selected model.
            scores,_=compare_predictions(data,{'selected_calibrated':{'description':'Frozen selected classifier within prespecified subgroup','threshold':selected_threshold}},settings)
            row['performance']=scores['selected_calibrated']
        else:row['limitation']='Below prespecified 100-person and/or 20-positive/20-negative minimum; counts and outcome-rate uncertainty only. No regrouping or minimum change after exposure.'
        results.append(row)
    return results


def category_results(frame,cuts,settings):
    p=frame['probability__selected_calibrated'];groups=np.where(p<=cuts[0],'lower',np.where(p<=cuts[1],'moderate','higher'))
    result=[]
    for index,name in enumerate(['lower','moderate','higher']):
        data=frame.loc[groups==name];result.append({'category':name,**rate_summary(data,settings,30+index),'mean_probability':float(data['probability__selected_calibrated'].mean()) if len(data) else None})
    return result


def clean(value):
    if isinstance(value,np.generic):return clean(value.item())
    if isinstance(value,np.ndarray):return clean(value.tolist())
    if isinstance(value,float) and not np.isfinite(value):return str(value)
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    if value is None or isinstance(value,(str,int,float,bool)):return value
    return repr(value)


def event(output,name,**details):
    path=output/'exposure_log.jsonl';previous=path.read_text().splitlines() if path.exists() else []
    record={'sequence':len(previous)+1,'event':name,'utc_from_host_clock':datetime.datetime.now(datetime.timezone.utc).isoformat(),**details}
    with path.open('a') as stream:stream.write(json.dumps(record)+'\n');stream.flush();os.fsync(stream.fileno())


def source_signature(root,settings):
    files=['configs/final_evaluation.json',*settings['code_inputs']]
    inputs={'source_sha256':{name:fingerprint(root/name) for name in files},'python':sys.version,'versions':{name:version(name) for name in ['numpy','pandas','scikit-learn','xgboost','pyarrow','joblib']}}
    return hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),inputs


def verify_freeze(root):
    root=Path(root);settings=json.loads((root/'configs/final_evaluation.json').read_text());output=root/settings['output_dir']
    path=output/'pretest_freeze.json'
    if not path.is_file():raise BoundaryError('Pre-test freeze absent/incomplete; no test access permitted.')
    frozen=json.loads(path.read_text());signature,_=source_signature(root,settings)
    if signature!=frozen['evaluation_signature']:raise BoundaryError('Frozen evaluation code/config/environment changed. Preserve exposure history and document implications before any recovery.')
    for name,digest in frozen['frozen_files_sha256'].items():
        if not (root/name).is_file() or fingerprint(root/name)!=digest:raise BoundaryError('Pre-test frozen artifact changed/missing; no evaluation permitted.')
    return frozen


def prepare_final(root):
    root=Path(root);settings=json.loads((root/'configs/final_evaluation.json').read_text());output=root/settings['output_dir']
    if output.exists():return verify_freeze(root)
    verify_outputs(root);tree=verify_tree_run(root);baseline=verify_baselines(root);protocol,cc,split,people,rows=load_locked(root)
    if settings['seed']!=protocol['seed'] or settings['bootstrap_replicates']!=protocol['bootstrap_replicates']:raise BoundaryError('Final bootstrap differs from locked protocol.')
    signature,provenance=source_signature(root,settings)
    output.mkdir(parents=True,exist_ok=False);(output/'frozen/models').mkdir(parents=True);(output/'frozen/code').mkdir()
    (root/settings['report_dir']).mkdir(parents=True,exist_ok=False)
    app=json.loads((root/settings['app_metadata']).read_text());bands=json.loads((root/settings['risk_categories']).read_text());timing=json.loads((root/settings['timing_decision']).read_text())
    if timing['decision']!='C' or not timing['timing_analysis_omitted']:raise BoundaryError('This frozen evaluator supports timing C only; do not mix unsupported survival results.')
    if bands['model_sha256']!=app['classifier']['sha256']:raise BoundaryError('Category thresholds refer to another selected model.')
    specs=[]
    def snapshot_model(name,source,threshold=None,raw_only=False,description=''):
        path=root/source;model=joblib.load(path);pipeline=model.base if hasattr(model,'base') else model
        destination=output/'frozen/models'/(name+'.joblib');shutil.copy2(path,destination)
        actual_threshold=float(threshold if threshold is not None else model.threshold)
        specs.append({'name':name,'snapshot':str(destination.relative_to(root)),'source':source,'source_sha256':fingerprint(path),'features':list(pipeline['schema'].features),'feature_domains':pipeline['schema'].domains,'threshold':actual_threshold,'raw_only':raw_only,'description':description,'estimator_class':type(pipeline['model']).__module__+'.'+type(pipeline['model']).__name__,'hyperparameters':clean(pipeline['model'].get_params(deep=False)),
                      'calibrator_parameters':clean(model.calibrator.get_params(deep=False)) if hasattr(model,'calibrator') else None,'calibrator_coefficient':clean(model.calibrator.coef_) if hasattr(model,'calibrator') else None,'calibrator_intercept':clean(model.calibrator.intercept_) if hasattr(model,'calibrator') else None})
    snapshot_model('selected_calibrated',app['classifier']['artifact'],description='Stage 8 selected XGBoost with frozen reserved sigmoid and operating threshold')
    if specs[0]['source_sha256']!=app['classifier']['sha256']:raise BoundaryError('Selected classifier differs from metadata.')
    if settings['compare_selected_raw']:snapshot_model('selected_raw',app['classifier']['artifact'],settings['fixed_raw_diagnostic_threshold'],True,'Frozen selected base XGBoost, uncalibrated; diagnostic threshold 0.5')
    for name in settings['baseline_models']:snapshot_model(name,'artifacts/baselines_v1/models/'+name+'.joblib',settings['fixed_raw_diagnostic_threshold'],False,'Stage 7 frozen raw '+name+' at fixed diagnostic 0.5')
    if settings['compare_calibrated_baseline']:snapshot_model('minimal_logistic_calibrated','artifacts/baselines_v1/selected_calibrated.joblib',description='Stage 7 frozen selected minimal logistic with reserved sigmoid/threshold')
    files=['configs/final_evaluation.json',settings['risk_categories'],settings['timing_decision'],settings['app_metadata'],settings['output_contract'],'configs/feature_mapping_final.json','configs/prediction_specification_final.json','configs/tree_models.json','configs/baseline_models.json','configs/evaluation.json',str(Path(cc['output_dir'])/cc['files']['schema']),*settings['code_inputs']]
    for name in files:
        dest=output/'frozen/code'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,dest)
    frozen_metadata={'models':specs,'selected_model_version':app['classifier']['model']+':'+app['classifier']['sha256'],'risk_cuts':bands['cuts'],'timing_decision':'C','source_cohort':{'file':str(Path(cc['output_dir'])/cc['files']['cohort']),'sha256':fingerprint(root/cc['output_dir']/cc['files']['cohort'])},'cohort_config':cc,'split_signature':split['signature'],'tree_signature':tree['signature'],'baseline_signature':baseline['signature'],'model_contract':json.loads((root/settings['output_contract']).read_text()),'test_keys_expected':int(rows['partition'].eq('test').sum()),'provenance':provenance}
    rows.loc[rows['partition'].eq('test'),KEYS].to_parquet(output/'frozen/test_keys.parquet',index=False)
    json_write(output/'frozen/metadata.json',frozen_metadata)
    frozen_paths=[p for p in (output/'frozen').rglob('*') if p.is_file()]
    frozen={'evaluation_signature':signature,'model_version':frozen_metadata['selected_model_version'],'prepared_before_test_answer_access':True,'frozen_files_sha256':{str(p.relative_to(root)):fingerprint(p) for p in frozen_paths},'test_keys_expected':frozen_metadata['test_keys_expected']}
    json_write(output/'pretest_freeze.json',frozen)
    event(output,'freeze_complete',pretest_manifest_sha256=fingerprint(output/'pretest_freeze.json'),test_outcomes_accessed=False)
    verify_freeze(root)
    return frozen


def verify_final_results(root):
    root=Path(root);settings=json.loads((root/'configs/final_evaluation.json').read_text());verify_freeze(root)
    path=root/settings['output_dir']/'complete_manifest.json'
    if not path.is_file():raise BoundaryError('Final evaluation not complete. If exposure was recorded, do not rerun silently; inspect the log and saved prediction checkpoint.')
    result=json.loads(path.read_text())
    for name,digest in result['output_sha256'].items():
        if not (root/name).is_file() or fingerprint(root/name)!=digest:raise BoundaryError('Saved final evaluation changed or missing; preserve evidence rather than recompute.')
    return result


def run_final(root):
    root=Path(root);settings=json.loads((root/'configs/final_evaluation.json').read_text());output=root/settings['output_dir'];report=root/settings['report_dir']
    if (output/'complete_manifest.json').is_file():verify_final_results(root);return 'reused_saved_final_evaluation',json.loads((report/'results.json').read_text())
    frozen=prepare_final(root)
    log=output/'exposure_log.jsonl'
    if any(json.loads(line)['event']=='test_access_started' for line in log.read_text().splitlines()):raise BoundaryError('Test exposure already recorded for an incomplete run. Preserve saved predictions; document any bug/fix and implications before recovery. No silent repeated evaluation.')
    lock=output/'evaluation.lock'
    try:handle=lock.open('x');handle.close()
    except FileExistsError:raise BoundaryError('Final evaluation lock exists; inspect active/interrupted run before proceeding.') from None
    try:
        verify_freeze(root);metadata=json.loads((output/'frozen/metadata.json').read_text());protocol,cc,split,people,rows=load_locked(root)
        if split['signature']!=metadata['split_signature']:raise BoundaryError('Participant assignment differs from the pre-test snapshot.')
        test=rows.loc[rows['partition'].eq('test'),KEYS]
        frozen_keys=pd.read_parquet(output/'frozen/test_keys.parquet')
        if set(map(tuple,test.to_numpy()))!=set(map(tuple,frozen_keys.to_numpy())):raise BoundaryError('Reserved participant/interval keys changed after freeze.')
        if len(test)!=frozen['test_keys_expected'] or test['PERSONID'].duplicated().any() or not test['starting_wave'].eq(protocol['test_start_wave']).all() or not test['followup_wave'].eq(protocol['test_followup_wave']).all():raise BoundaryError('Frozen test key/temporal restrictions fail.')
        source=root/metadata['source_cohort']['file']
        if fingerprint(source)!=metadata['source_cohort']['sha256']:raise BoundaryError('Cohort changed after pre-test freeze.')
        features=sorted({name for model in metadata['models'] for name in model['features']})
        columns=list(dict.fromkeys(KEYS+features+settings['additional_test_columns']+['outcome_p30d']))
        event(output,'test_access_started',pretest_manifest_sha256=fingerprint(output/'pretest_freeze.json'),expected_records=len(test),read_columns=columns,policy='One authorized test evaluation; no tuning or model selection from results')
        frame=pd.read_parquet(source,columns=columns,filters=[('PERSONID','in',test['PERSONID'].tolist()),('starting_wave','==',protocol['test_start_wave']),('followup_wave','==',protocol['test_followup_wave'])])
        checked=test.merge(frame[KEYS],on=KEYS,how='outer',indicator=True,validate='one_to_one')
        if not checked['_merge'].eq('both').all() or not frame['outcome_p30d'].isin([0,1]).all():raise BoundaryError('Observed-valid frozen test records do not match exact reserved keys.')
        private=frame[KEYS+['outcome_p30d','age_band','sex_recorded','last_cigarette_recency_days','recency_boundary_report']].copy()
        selected_features=metadata['models'][0]['features'];private['observed_model_inputs']=frame[selected_features].notna().sum(axis=1)
        for spec in metadata['models']:
            model=joblib.load(root/spec['snapshot']);estimator=model.base if spec['raw_only'] else model
            private['probability__'+spec['name']]=estimator.predict_proba(frame[spec['features']])[:,1]
        private.to_parquet(output/'test_predictions.parquet',index=False)
        event(output,'test_predictions_saved',sha256=fingerprint(output/'test_predictions.parquet'),records=len(private),models_scored=len(metadata['models']))
        model_specs={spec['name']:spec for spec in metadata['models']}
        scores,paired=compare_predictions(private,model_specs,settings)
        selected_threshold=metadata['models'][0]['threshold']
        results={'model_version':metadata['selected_model_version'],'evaluation_signature':frozen['evaluation_signature'],'endpoint':'Past-30-day cigarette smoking reported at next scheduled survey among eligible former established smokers, conditional on valid observed follow-up',
            'test_pair':[protocol['test_start_wave'],protocol['test_followup_wave']],'records':len(private),'unique_people':int(private['PERSONID'].nunique()),'positive_records':int(private['outcome_p30d'].sum()),'negative_records':int(private['outcome_p30d'].eq(0).sum()),'positive_prevalence':float(private['outcome_p30d'].mean()),'people_with_repeated_test_records':int(private.groupby('PERSONID').size().gt(1).sum()),
            'metrics':scores,'paired_difference_selected_minus_baseline':paired,'calibration':{name:calibration_bins(private['outcome_p30d'],private['probability__'+name],private['PERSONID'],settings) for name in settings['calibration_plot_models']},
            'risk_categories':category_results(private,metadata['risk_cuts'],settings),'risk_cuts':metadata['risk_cuts'],'subgroups':subgroup_results(private,settings,selected_threshold),
            'bootstrap_replicates':settings['bootstrap_replicates'],'bootstrap_seed':settings['seed'],'bootstrap_method':settings['bootstrap_method'],'confidence_level':settings['confidence_level'],'metric_definition':'Stepwise weighted average_precision_score equivalent, not trapezoidal PR-AUC; weighted tie-aware ROC. Undefined AP when no positive weight; undefined ROC when either class absent. Precision/recall/specificity/F1 undefined on zero denominators.',
            'timing_decision':'C; no survival model or supported elapsed horizons','survey_weighting':'No matching survey weights/design; no national inference','app_input_coverage':{'minimum_supplied_inputs':metadata['model_contract']['minimum_observed_inputs'],'records_meeting_input_count':int(private['observed_model_inputs'].ge(metadata['model_contract']['minimum_observed_inputs']).sum()),'evaluation_policy':'All locked valid-outcome test records evaluated; app input-count guard is descriptive coverage, not a post-hoc test exclusion'},
            'no_fitting_or_test_driven_tuning':True,'test_exposure_policy':'First recorded answer access in this run; predictions saved once; reruns must reuse complete saved evidence.'}
        json_write(report/'results.json',results)
        from path_project.final_report import render_final_report
        render_final_report(root,results,settings)
        event(output,'evaluation_complete',records=len(private),outcomes_used_for_tuning=False,results_sha256=fingerprint(report/'results.json'))
        status={'version':'1.0','model_version':metadata['selected_model_version'],'model_sha256':metadata['models'][0]['source_sha256'],'final_evaluation_complete':True,'results_file':str((report/'results.json').relative_to(root)),'results_sha256':fingerprint(report/'results.json'),'timing_decision':'C','new_user_or_clinical_validity_established':False,'legacy_metadata_note':'Earlier immutable development metadata retains its historical pending-test wording; use this additive evaluation-status record and final report for current evidence. No old artifact was rewritten.'}
        json_write(root/'configs/final_evaluation_status.json',status)
        paths=[p for folder in [output,report] for p in folder.rglob('*') if p.is_file() and p!=lock]+[root/settings['report_markdown'],root/'configs/final_evaluation_status.json']
        json_write(output/'complete_manifest.json',{'evaluation_signature':frozen['evaluation_signature'],'model_version':metadata['selected_model_version'],'output_sha256':{str(p.relative_to(root)):fingerprint(p) for p in paths},'policy':'Saved one-shot evaluation; verified reuse only, no rescore/rebootstrap/tuning on retry.'})
        verify_final_results(root)
        return 'evaluated_frozen_test_once',results
    except Exception as error:
        event(output,'evaluation_failed',exception_type=type(error).__name__,policy='Preserve test exposure and any prediction checkpoint; document fix/implications, never silently rerun.')
        raise
    finally:lock.unlink(missing_ok=True)
