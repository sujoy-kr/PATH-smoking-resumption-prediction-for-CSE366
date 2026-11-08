"""CPU-friendly baseline Pipelines, development metrics and immutable training.

No accessor for final-test features/outcomes exists in this module.
"""
import json
import sys
import warnings
from pathlib import Path
from importlib.metadata import version
import hashlib
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (average_precision_score, roc_auc_score, brier_score_loss,
    log_loss, precision_score, recall_score, f1_score, confusion_matrix, precision_recall_curve)
from path_project.cohort import json_write
from path_project.documentation import fingerprint
from path_project.evaluation import (BoundaryError, load_locked, load_development,
    assert_batch, fit_training_pipeline, participant_weights)
from path_project.final_inputs import validate_final_inputs

KEYS=['PERSONID','starting_wave','followup_wave']


class FeatureSchema(TransformerMixin,BaseEstimator):
    """Validate/project only baseline features; accept unseen *valid* categories."""
    def __init__(self,features,domains):
        self.features=features;self.domains=domains
    def _validate(self,X):
        if not isinstance(X,pd.DataFrame) or len(X.columns)!=len(self.features) or set(X.columns)!=set(self.features):
            raise BoundaryError('Prediction schema must contain exactly the configured feature names; identifiers/labels/extra columns forbidden.')
        try:result=X[self.features].apply(pd.to_numeric,errors='raise').astype(float)
        except (ValueError,TypeError):raise BoundaryError('Model features must be numeric codes/quantities or missing; values suppressed.') from None
        values=result.to_numpy()
        if np.isinf(values).any():raise BoundaryError('Nonfinite feature value; no values emitted.')
        for name,domain in self.domains.items():
            observed=result[name].dropna()
            if domain is not None:
                if not observed.isin(domain).all():raise BoundaryError(f'{name}: outside documented category codes.')
            elif observed.lt(0).any():raise BoundaryError(f'{name}: negative quantity not valid.')
        return result
    def fit(self,X,y=None):
        self._validate(X);self.feature_names_in_=np.asarray(self.features,dtype=object);self.n_features_in_=len(self.features);return self
    def transform(self,X):return self._validate(X)
    def get_feature_names_out(self,input_features=None):return np.asarray(self.features,dtype=object)


def make_pipeline(candidate,final,settings):
    features=final['feature_sets'][candidate['profile']]
    fields={f['name']:f for f in final['fields']}
    categorical=[n for n in features if fields[n]['output_labels']]
    numeric=[n for n in features if n not in categorical]
    domains={n:[float(code) for code in fields[n]['output_labels']] if n in categorical else None for n in features}
    transforms=[]
    if categorical:transforms.append(('categorical',Pipeline([
        ('impute',SimpleImputer(strategy='constant',fill_value=settings['categorical_imputation_value'],keep_empty_features=True)),
        ('encode',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),categorical))
    if numeric:transforms.append(('numeric',Pipeline([
        ('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
        ('scale',StandardScaler())]),numeric))
    model=DummyClassifier(strategy='prior') if candidate['kind']=='prevalence' else LogisticRegression(**settings['logistic'],class_weight=candidate['class_weight'],random_state=settings['seed'])
    return Pipeline([('schema',FeatureSchema(features,domains)),('preprocess',ColumnTransformer(transforms,verbose_feature_names_out=True)),('model',model)])


def metric_block(y,p,threshold,weights):
    y=np.asarray(y,dtype=int);p=np.asarray(p,dtype=float);w=np.asarray(weights,dtype=float)
    if len(y)!=len(p) or not np.isfinite(p).all() or ((p<0)|(p>1)).any():raise BoundaryError('Invalid development probability vector.')
    pred=p>=threshold
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1],sample_weight=w).ravel()
    return {'prevalence':float(np.average(y,weights=w)),
        'average_precision':float(average_precision_score(y,p,sample_weight=w)) if y.sum() else None,
        'roc_auc':float(roc_auc_score(y,p,sample_weight=w)) if len(np.unique(y))==2 else None,
        'brier':float(brier_score_loss(y,p,sample_weight=w)),
        'log_loss':float(log_loss(y,p,sample_weight=w,labels=[0,1])),
        'mean_predicted_probability':float(np.average(p,weights=w)),
        'threshold':float(threshold),'precision':float(precision_score(y,pred,sample_weight=w,zero_division=0)),
        'sensitivity':float(recall_score(y,pred,sample_weight=w,zero_division=0)),
        'specificity':float(tn/(tn+fp)) if tn+fp else None,
        'f1':float(f1_score(y,pred,sample_weight=w,zero_division=0)),
        'confusion':{'tn':float(tn),'fp':float(fp),'fn':float(fn),'tp':float(tp)}}


def metrics(frame,p,threshold):
    y=frame['outcome_p30d'].astype(int).to_numpy()
    return {'records':len(frame),'people':int(frame['PERSONID'].nunique()),
        'participant_equal':metric_block(y,p,threshold,participant_weights(frame)),
        'interval_equal':metric_block(y,p,threshold,np.ones(len(frame)))}


def reliability(frame,p,edges):
    y=frame['outcome_p30d'].to_numpy(dtype=int);p=np.asarray(p);w=participant_weights(frame).to_numpy()
    bins=np.minimum(np.searchsorted(edges,p,side='right')-1,len(edges)-2)
    result=[]
    for index in range(len(edges)-1):
        mask=bins==index
        if mask.any():result.append({'lower':edges[index],'upper':edges[index+1],'records':int(mask.sum()),'participant_weight':float(w[mask].sum()),'mean_prediction':float(np.average(p[mask],weights=w[mask])),'observed_fraction':float(np.average(y[mask],weights=w[mask]))})
    return result


def logits(p,epsilon):
    p=np.clip(np.asarray(p,dtype=float),epsilon,1-epsilon)
    return np.log(p/(1-p)).reshape(-1,1)


def fit_sigmoid(frame,p,settings):
    parameters={k:v for k,v in settings['calibrator'].items() if k in ['C','solver','max_iter','tol']}
    calibration=LogisticRegression(**parameters,random_state=settings['seed'])
    calibration.fit(logits(p,settings['calibrator']['clip_epsilon']),frame['outcome_p30d'].astype(int),sample_weight=participant_weights(frame))
    return calibration


def choose_threshold(frame,p):
    precision,recall,thresholds=precision_recall_curve(frame['outcome_p30d'].astype(int),p,sample_weight=participant_weights(frame))
    f1=np.divide(2*precision[:-1]*recall[:-1],precision[:-1]+recall[:-1],out=np.zeros_like(precision[:-1]),where=(precision[:-1]+recall[:-1])>0)
    best=float(f1.max());threshold=float(thresholds[np.flatnonzero(f1==best)[-1]])
    return threshold,best


class CalibratedBaseline:
    """Frozen tuning-trained pipeline plus held-out sigmoid and chosen threshold."""
    def __init__(self,base,calibrator,epsilon,threshold):
        self.base=base;self.calibrator=calibrator;self.epsilon=epsilon;self.threshold=threshold
    def predict_proba(self,X):
        raw=self.base.predict_proba(X)[:,1]
        return self.calibrator.predict_proba(logits(raw,self.epsilon))
    def predict(self,X):return (self.predict_proba(X)[:,1]>=self.threshold).astype(int)


def signature_for(root,settings,split_manifest):
    files=['configs/baseline_models.json','configs/feature_mapping_final.json','configs/prediction_specification_final.json','configs/app_questions.json','docs/feature_dictionary_final.csv','configs/evaluation.json',*settings['code_inputs']]
    evidence={'split_signature':split_manifest['signature'],'split_output_sha256':split_manifest['output_sha256'],
        'source_sha256':{name:fingerprint(root/name) for name in files},'python':sys.version,
        'versions':{name:version(name) for name in ['numpy','pandas','scikit-learn','scipy','joblib','pyarrow']}}
    return hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest(),evidence


def verify_run(root):
    root=Path(root);settings=json.loads((root/'configs/baseline_models.json').read_text())
    _,_,split_manifest,_,_=load_locked(root)
    signature,_=signature_for(root,settings,split_manifest)
    path=root/settings['output_dir']/'manifest.json'
    if not path.is_file():raise BoundaryError('Existing baseline run is incomplete; preserve and inspect, never overwrite.')
    saved=json.loads(path.read_text())
    if saved['signature']!=signature:raise BoundaryError('Existing baseline signature differs; no retraining or overwrite permitted.')
    for name,digest in saved['output_sha256'].items():
        if not (root/name).is_file() or fingerprint(root/name)!=digest:raise BoundaryError('Saved baseline artifact/report changed; no overwrite permitted.')
    return saved


def train_baselines(root):
    root=Path(root);settings=json.loads((root/'configs/baseline_models.json').read_text())
    config,cc,split_manifest,people,rows=load_locked(root)
    final,_=validate_final_inputs(root)
    signature,provenance=signature_for(root,settings,split_manifest)
    output=root/settings['output_dir'];report=root/settings['report_dir']
    if output.exists() or report.exists():
        verify_run(root);return 'reused_verified_run',json.loads((report/'results.json').read_text())
    # Exclusive creation: preserve partial failed runs for investigation, no retry overwrite.
    output.mkdir(parents=True,exist_ok=False);report.mkdir(parents=True,exist_ok=False)
    (output/'models').mkdir();(output/'folds').mkdir()
    candidates=settings['models_in_simplicity_order'];fold_results=[];predictions=[];metadata=[]
    with warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        for fold in range(config['folds']):
            training=load_development(root,'fit',fold)
            validation=load_development(root,'validation',fold)
            if set(training['PERSONID'])&set(validation['PERSONID']):raise BoundaryError('Fold participant overlap.')
            prevalence=float(training['outcome_p30d'].mean())
            for candidate in candidates:
                features=final['feature_sets'][candidate['profile']]
                train=training[KEYS+features+['outcome_p30d']]
                valid=validation[KEYS+features+['outcome_p30d']]
                estimator=make_pipeline(candidate,final,settings)
                fitted=fit_training_pipeline(estimator,train,rows,config,features,fold)
                p=fitted.predict_proba(valid[features])[:,1]
                if candidate['kind']=='prevalence' and not np.allclose(p,prevalence,rtol=0,atol=1e-14):raise BoundaryError('Prevalence baseline did not use training labels only.')
                joblib.dump(fitted,output/'folds'/f"{candidate['name']}_fold{fold}.joblib")
                score=metrics(valid,p,settings['fixed_diagnostic_threshold'])
                fold_results.append({'model':candidate['name'],'fold':fold,'training_records':len(train),'training_people':int(train['PERSONID'].nunique()),'training_prevalence':prevalence,'metrics':score,'calibration_bins':reliability(valid,p,settings['calibration_bin_edges'])})
                local=valid[KEYS+['outcome_p30d']].copy();local['fold']=fold;local['model']=candidate['name'];local['probability']=p;predictions.append(local)
                print(f"Fold {fold} {candidate['name']}: AP={score['participant_equal']['average_precision']:.4f}, Brier={score['participant_equal']['brier']:.4f}",flush=True)
        oof=pd.concat(predictions,ignore_index=True)
        summary=[]
        for candidate in candidates:
            folds=[r for r in fold_results if r['model']==candidate['name']]
            local=oof.loc[oof['model'].eq(candidate['name'])]
            row={'model':candidate['name'],'profile':candidate['profile'],'class_weight':candidate['class_weight'],'mean_fold_participant_metrics':{},'fold_sd_descriptive_only':{},'pooled_oof':metrics(local,local['probability'],settings['fixed_diagnostic_threshold']),'pooled_oof_calibration_bins':reliability(local,local['probability'],settings['calibration_bin_edges'])}
            for key in ['average_precision','roc_auc','brier','log_loss','prevalence','mean_predicted_probability','f1','precision','sensitivity','specificity']:
                values=[f['metrics']['participant_equal'][key] for f in folds]
                row['mean_fold_participant_metrics'][key]=float(np.mean(values));row['fold_sd_descriptive_only'][key]=float(np.std(values,ddof=1))
            summary.append(row)
        # Stable list order is the prespecified simplicity order on exact AP ties.
        winner=max(summary,key=lambda r:r['mean_fold_participant_metrics']['average_precision'])['model']
        selected_candidate=next(c for c in candidates if c['name']==winner)
        all_training=load_development(root,'fit')
        bases={}
        for candidate in candidates:
            features=final['feature_sets'][candidate['profile']]
            training=all_training[KEYS+features+['outcome_p30d']]
            fitted=fit_training_pipeline(make_pipeline(candidate,final,settings),training,rows,config,features)
            bases[candidate['name']]=fitted
            path=output/'models'/(candidate['name']+'.joblib');joblib.dump(fitted,path)
            reloaded=joblib.load(path)
            # Exact serialization consistency checked on authorized development rows only.
            if not np.array_equal(fitted.predict_proba(training[features]),reloaded.predict_proba(training[features])):raise BoundaryError('Reloaded model predictions differ; no values emitted.')
            transformed=fitted[:-1].get_feature_names_out().tolist()
            counts=training['outcome_p30d'].value_counts()
            metadata.append({'model':candidate['name'],'profile':candidate['profile'],'features':features,'transformed_features':transformed,'training_records':len(training),'training_people':int(training['PERSONID'].nunique()),'training_prevalence':float(training['outcome_p30d'].mean()),'class_weight':candidate['class_weight'],'balanced_class_weights':{str(int(label)):len(training)/(2*int(count)) for label,count in counts.items()} if candidate['class_weight']=='balanced' else None,'numeric_medians':fitted['preprocess'].named_transformers_['numeric']['impute'].statistics_.tolist(),'coefficients':fitted['model'].coef_[0].tolist() if candidate['kind']=='logistic' else None,'intercept':fitted['model'].intercept_.tolist() if candidate['kind']=='logistic' else None,'iterations':fitted['model'].n_iter_.tolist() if candidate['kind']=='logistic' else None,'serialization_predictions_exact':True,'identifiers_in_predictors':False})
        features=final['feature_sets'][selected_candidate['profile']]
        calibration=load_development(root,'calibration')[KEYS+features+['outcome_p30d']]
        threshold_data=load_development(root,'threshold')[KEYS+features+['outcome_p30d']]
        assert_batch(calibration,rows,config,features,'calibration');assert_batch(threshold_data,rows,config,features,'threshold')
        if set(all_training['PERSONID'])&set(calibration['PERSONID']) or set(all_training['PERSONID'])&set(threshold_data['PERSONID']) or set(calibration['PERSONID'])&set(threshold_data['PERSONID']):raise BoundaryError('Calibration/base/threshold participant overlap.')
        base=bases[winner]
        raw_cal=base.predict_proba(calibration[features])[:,1]
        sigmoid=fit_sigmoid(calibration,raw_cal,settings)
        epsilon=settings['calibrator']['clip_epsilon']
        raw_threshold=base.predict_proba(threshold_data[features])[:,1]
        calibrated_threshold=sigmoid.predict_proba(logits(raw_threshold,epsilon))[:,1]
        threshold,best_f1=choose_threshold(threshold_data,calibrated_threshold)
        bundle=CalibratedBaseline(base,sigmoid,epsilon,threshold)
        joblib.dump(bundle,output/'selected_calibrated.joblib')
        reloaded=joblib.load(output/'selected_calibrated.joblib')
        if not np.array_equal(bundle.predict_proba(threshold_data[features]),reloaded.predict_proba(threshold_data[features])):raise BoundaryError('Calibrated serialization prediction mismatch.')
        reserved=threshold_data[KEYS+['outcome_p30d']].copy();reserved['raw_probability']=raw_threshold;reserved['calibrated_probability']=calibrated_threshold;reserved.to_parquet(output/'threshold_predictions.parquet',index=False)
        cal_local=calibration[KEYS+['outcome_p30d']].copy();cal_local['raw_probability']=raw_cal;cal_local['calibrated_probability']=sigmoid.predict_proba(logits(raw_cal,epsilon))[:,1];cal_local.to_parquet(output/'calibration_predictions.parquet',index=False)
        calibration_report={'selected_model':winner,'selection_uses':'Mean five-fold tuning validation participant-weighted average_precision_score; no calibration/threshold/test model selection.',
            'method':'Sigmoid logistic regression on clipped raw-probability logit; base model frozen; calibration people only. Participant-equal calibration fitting weights.',
            'calibrator_coefficient':sigmoid.coef_.tolist(),'calibrator_intercept':sigmoid.intercept_.tolist(),
            'calibration_fit_apparent_raw':metrics(calibration,raw_cal,.5),'calibration_fit_apparent_calibrated':metrics(calibration,cal_local['calibrated_probability'],.5),
            'threshold_group_raw_fixed_0_5':metrics(threshold_data,raw_threshold,.5),'threshold_group_calibrated_fixed_0_5':metrics(threshold_data,calibrated_threshold,.5),
            'threshold_selection_apparent_at_chosen_threshold':metrics(threshold_data,calibrated_threshold,threshold),'chosen_threshold':threshold,'threshold_selection_f1':best_f1,
            'threshold_group_raw_calibration_bins':reliability(threshold_data,raw_threshold,settings['calibration_bin_edges']),
            'threshold_group_calibrated_bins':reliability(threshold_data,calibrated_threshold,settings['calibration_bin_edges']),
            'caution':'Calibration-fit metrics are in-sample for the calibrator. Threshold-group probabilities are held out from base/calibrator fitting, but chosen-threshold metrics are apparent for threshold selection. These are not final-test results or a validated clinical risk category.'}
    oof.to_parquet(output/'oof_predictions.parquet',index=False)
    results={'pr_metric':'sklearn.metrics.average_precision_score: stepwise precision weighted by recall increments, not trapezoidal PR-AUC.',
        'primary_weighting':'Each evaluated participant total weight one (1/n interval records); interval-equal metrics also saved. No survey weights/national inference.',
        'full_selected_feature_set':'11 app-compatible inputs; minimal comparator uses 4. Research-only 25-field model not fitted.',
        'candidates':summary,'selected_model':winner,'selection_rule':config['metric_selection'],'calibration':calibration_report,
        'no_final_test_features_or_outcomes_read':True,'no_final_test_performance':True,'no_resampling_of_evaluation_rows':True,'final_test_assignment_unchanged':True}
    json_write(report/'fold_metrics.json',fold_results);json_write(report/'results.json',results);json_write(output/'pipeline_metadata.json',metadata)
    public=[{key:item[key] for key in ['model','profile','features','transformed_features','training_records','training_people','class_weight','serialization_predictions_exact','identifiers_in_predictors']} for item in metadata]
    json_write(report/'pipeline_metadata.json',public)
    json_write(report/'provenance.json',provenance)
    files=[p for folder in [output,report] for p in folder.rglob('*') if p.is_file()]
    saved={'signature':signature,'provenance':provenance,'output_sha256':{str(p.relative_to(root)):fingerprint(p) for p in files},'policy':'Verify and reuse on retry; no overwrites/retraining of completed runs. No test access.'}
    json_write(output/'manifest.json',saved)
    verify_run(root)
    return 'trained_new_immutable_run',results
