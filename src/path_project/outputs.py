"""Frozen development score bands and exact calibrated-probability SHAP outputs.

No fitting, final-test access, time-to-event estimates or causal interpretations.
"""
import hashlib,json,os,sys,time
from pathlib import Path
from importlib.metadata import version
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from path_project.cohort import json_write
from path_project.documentation import fingerprint
from path_project.evaluation import load_locked,select_keys,participant_weights,BoundaryError
from path_project.final_inputs import encode_app_answers,validate_final_inputs
from path_project.timing import next_survey_output_metadata
from path_project.trees import verify_tree_run

KEYS=['PERSONID','starting_wave','followup_wave']


def weighted_cuts(probabilities,weights,quantiles):
    p=np.asarray(probabilities,dtype=float);w=np.asarray(weights,dtype=float)
    if len(p)==0 or len(p)!=len(w) or len(quantiles)!=2 or not 0<quantiles[0]<quantiles[1]<1:raise BoundaryError('Two ordered quantiles and nonempty matching scores/weights required.')
    if not np.isfinite(p).all() or ((p<0)|(p>1)).any() or not np.isfinite(w).all() or (w<=0).any():raise BoundaryError('Invalid development scores/weights for category definition.')
    order=np.argsort(p,kind='stable');cumulative=np.cumsum(w[order]);total=cumulative[-1]
    cuts=[float(p[order[min(int(np.searchsorted(cumulative,q*total,side='left')),len(p)-1)]]) for q in quantiles]
    if not 0<=cuts[0]<cuts[1]<=1:raise BoundaryError('Distinct three-group cuts unsupported; do not invent or optimize alternative bands.')
    return cuts


def category_for(probability,cuts):
    p=float(probability)
    if not np.isfinite(p) or not 0<=p<=1:raise BoundaryError('Category needs a finite probability in [0,1].')
    return 'lower' if p<=cuts[0] else 'moderate' if p<=cuts[1] else 'higher'


def category_summary(frame,cuts):
    weights=participant_weights(frame);assigned=frame['calibrated_probability'].map(lambda p:category_for(p,cuts))
    rows=[]
    for name in ['lower','moderate','higher']:
        mask=assigned.eq(name);block=frame.loc[mask];w=weights.loc[mask]
        if block.empty:raise BoundaryError('Three nonempty score groups unsupported; do not invent new cutoffs.')
        rows.append({'category':name,'interval_records':len(block),'unique_people':int(block['PERSONID'].nunique()),'positive_outcomes':int(block['outcome_p30d'].sum()),'observed_interval_fraction':float(block['outcome_p30d'].mean()),'participant_weight_total':float(w.sum()),'participant_equal_observed_fraction':float(np.average(block['outcome_p30d'],weights=w)),'participant_equal_mean_probability':float(np.average(block['calibrated_probability'],weights=w))})
    return rows


def deterministic_people(frame,count,namespace,seed,exclude=()):
    data=frame.loc[~frame['PERSONID'].isin(exclude)].copy()
    def digest(values):return hashlib.sha256((namespace+'|'+str(seed)+'|'+'|'.join(map(str,values))).encode()).hexdigest()
    data['_record_order']=[digest(row) for row in data[KEYS].itertuples(index=False,name=None)]
    data=data.sort_values('_record_order',kind='stable').drop_duplicates('PERSONID')
    data['_person_order']=[digest([p]) for p in data['PERSONID']]
    if len(data)<count:raise BoundaryError('Too few tuning participants for configured explanation sample.')
    return data.sort_values('_person_order',kind='stable').head(count).drop(columns=['_record_order','_person_order']).reset_index(drop=True)


class ProbabilityCallable:
    def __init__(self,model,features):self.model=model;self.features=features
    def __call__(self,values):
        return self.model.predict_proba(pd.DataFrame(np.asarray(values,dtype=float),columns=self.features))[:,1]


def exact_explainer(model,features,background,root):
    os.environ.setdefault('MPLCONFIGDIR',str(Path(root)/'.cache/matplotlib'))
    import shap
    matrix=background[features].to_numpy(dtype=float,na_value=np.nan)
    masker=shap.maskers.Independent(matrix,max_samples=len(matrix))
    return shap.ExactExplainer(ProbabilityCallable(model,features),masker,feature_names=features)


def explain_frame(model,features,explainer,frame,tolerance):
    with threadpool_limits(limits=1):
        probability=model.predict_proba(frame[features])[:,1]
        explanation=explainer(frame[features].to_numpy(dtype=float,na_value=np.nan),max_evals=2**len(features),silent=True)
    values=np.asarray(explanation.values,dtype=float);base=np.asarray(explanation.base_values,dtype=float).reshape(-1)
    reconstructed=base+values.sum(axis=1)
    residual=np.abs(reconstructed-probability)
    if values.shape!=(len(frame),len(features)) or not np.isfinite(values).all() or not np.allclose(reconstructed,probability,rtol=0,atol=tolerance):raise BoundaryError('SHAP does not reconstruct the actual calibrated probability; do not display an explanation for a different scale/model.')
    return probability,base,values,residual


def transformed_question_map(model,fields):
    preprocess=model.base['preprocess'];names=preprocess.get_feature_names_out().tolist();result=[]
    for name,transformer,columns in preprocess.transformers_:
        if name=='remainder':continue
        indices=preprocess.output_indices_[name];output_names=names[indices.start:indices.stop]
        if name=='categorical':
            index=0
            for column,categories in zip(columns,transformer['encode'].categories_):
                for category in categories:
                    code=str(int(category));label='Missing response (model category)' if float(category)==-1 else fields[column]['output_labels'][code]
                    result.append({'transformed_feature':output_names[index],'question_feature':column,'question':fields[column]['description'],'category_label':label,'transform':'one-hot encoded training category'});index+=1
        else:
            for output_name in output_names:
                column=next(c for c in columns if c in output_name)
                result.append({'transformed_feature':output_name,'question_feature':column,'question':fields[column]['description'],'category_label':None,'transform':'standardized missing indicator' if 'missingindicator' in output_name else 'training-median-imputed, standardized numerical history'})
    if [r['transformed_feature'] for r in result]!=names:raise BoundaryError('Transformed-to-question mapping is incomplete.')
    return result


def signature_for(root,settings,tree_manifest):
    files=['configs/output_explanations.json','configs/app_metadata.json','configs/app_questions.json','configs/feature_mapping_final.json',*settings['code_inputs']]
    provenance={'tree_signature':tree_manifest['signature'],'tree_output_sha256':tree_manifest['output_sha256'],'source_sha256':{name:fingerprint(root/name) for name in files},'python':sys.version,'versions':{name:version(name) for name in ['shap','xgboost','scikit-learn','numpy','pandas','joblib','pyarrow']}}
    return hashlib.sha256(json.dumps(provenance,sort_keys=True).encode()).hexdigest(),provenance


def verify_outputs(root):
    root=Path(root);settings=json.loads((root/'configs/output_explanations.json').read_text());tree=verify_tree_run(root)
    signature,_=signature_for(root,settings,tree)
    path=root/settings['output_dir']/'manifest.json'
    if not path.is_file():raise BoundaryError('Output/explanation run incomplete; preserve and inspect rather than overwrite.')
    manifest=json.loads(path.read_text())
    if manifest['signature']!=signature:raise BoundaryError('Frozen output signature changed; no silent threshold/explanation regeneration.')
    for name,digest in manifest['output_sha256'].items():
        if not (root/name).is_file() or fingerprint(root/name)!=digest:raise BoundaryError('Frozen category/output artifact changed or missing.')
    return manifest


class OutputEngine:
    def __init__(self,root,model,background,settings,bands,metadata,questions,fields):
        self.root=Path(root);self.model=model;self.features=model.base['schema'].features
        self.settings=settings;self.bands=bands;self.metadata=metadata;self.questions={q['feature']:q for q in questions['questions']};self.gates=questions['eligibility_questions'];self.fields=fields
        self.reference_intervals=len(background)
        self.reference_people=int(background['PERSONID'].nunique()) if 'PERSONID' in background else None
        self.explainer=exact_explainer(model,self.features,background,self.root)
    def output(self,answers,eligibility,wave=7,elapsed_horizon=None,request_relapse_date=False):
        interval=next_survey_output_metadata(self.metadata,elapsed_horizon,request_relapse_date)
        if set(answers)-set(self.features):raise BoundaryError('Only the selected model questions are accepted; research/unused/identifier fields are not scored.')
        gate_keys=self.settings['eligibility_keys']
        if set(eligibility)-set(gate_keys):raise BoundaryError('Unknown cohort-eligibility field.')
        outside=False;unknown=False
        for key,gate in zip(gate_keys,self.gates):
            answer=eligibility.get(key)
            if answer is None or answer==gate['options'][-1]:unknown=True
            elif answer not in gate['options']:raise BoundaryError('Eligibility answer outside configured choices.')
            elif answer!=gate['required_answer']:outside=True
        values,reasons=encode_app_answers(self.root,answers,wave)
        observed=[name for name in self.features if reasons[name]=='observed'];missing=[name for name in self.features if name not in observed]
        limitations=[self.settings['category_caution'],self.metadata['probability_validation_status'],self.metadata['timing_unavailable_message'],'Model associations and SHAP contributions are not causes or effects of changing an answer. No personal confidence percentage or clinical action guarantee.','Survey-conditioned observed-follow-up research cohort; no national representativeness. Correlated-feature mixtures in marginal SHAP may be unrealistic.']
        if missing:limitations.append('Missing answers use trained imputation/missing-category handling, not assumed zero/No. Routing and new-user missingness may differ from development data.')
        result={'contract_version':'1.0','status':'scored','probability':None,'endpoint':interval['endpoint'],'prediction_interval':interval['interval_description'],'category':None,
            'category_thresholds':{'lower_upper_inclusive':self.bands['cuts'][0],'moderate_upper_inclusive':self.bands['cuts'][1],'higher_rule':'probability > moderate_upper_inclusive','scale':'calibrated_probability','uses_unrounded_score':True},
            'contributing_factors':[],'input_completeness':{'provided':len(observed),'expected':len(self.features),'missing':missing,'reasons':{name:reasons[name] for name in self.features},'meaning':'Input counts, not a personal confidence estimate'},
            'model_version':{'selected_model':self.metadata['classifier']['model'],'artifact_sha256':self.metadata['classifier']['sha256'],'stage8_signature':self.metadata['classifier']['stage8_signature'],'output_version':self.settings['run_name']},'limitations':limitations}
        if outside:result['status']='outside_cohort';result['suppression_reason']='Eligibility answers do not match the model cohort; no estimate is issued.';return result
        if unknown:result['status']='eligibility_unconfirmed';result['suppression_reason']='Confirm all cohort eligibility questions before requesting an estimate.';return result
        if len(observed)<self.settings['minimum_observed_inputs']:result['status']='insufficient_input';result['suppression_reason']=f'Provide at least {self.settings["minimum_observed_inputs"]} of {len(self.features)} model inputs; an estimate would otherwise rely too heavily on missing-value handling.';return result
        frame=pd.DataFrame([{name:values[name] for name in self.features}],columns=self.features,dtype=float)
        p,base,contributions,residual=explain_frame(self.model,self.features,self.explainer,frame,self.settings['additivity_absolute_tolerance'])
        result['probability']=float(p[0]);category=category_for(p[0],self.bands['cuts'])
        result['category']={'code':category,'label':self.settings['category_labels'][category],'definition':self.settings['category_caution']}
        factors=[]
        for index,name in enumerate(self.features):
            value=values[name];field=self.fields[name]
            if reasons[name]!='observed':answer='Not supplied ('+reasons[name]+'); uses trained missing handling'
            elif field['output_labels']:answer=field['output_labels'][str(int(value))]
            else:answer=f'{value:g} {field["output_units"]}'
            contribution=float(contributions[0,index])
            factors.append({'feature':name,'question':self.questions[name]['waves'][str(wave)]['prompt'],'answer':answer,'answer_reason':reasons[name],
                'contribution':contribution,'contribution_units':'calibrated probability units; multiply by 100 only for percentage-point attribution',
                'interpretation':'Pushes the model estimate up relative to the background mixture' if contribution>0 else 'Pushes the model estimate down relative to the background mixture' if contribution<0 else 'No contribution relative to this background mixture'})
        result['contributing_factors']=sorted(factors,key=lambda r:abs(r['contribution']),reverse=True)
        result['explanation']={'method':'Exact SHAP on the actual calibrated wrapper probability','scale':'calibrated_probability','reference_model_probability':float(base[0]),'reference_meaning':f'Mean model output for {self.reference_intervals} reference intervals/profiles; {self.reference_people} distinct tuning people when known; not an observed outcome rate','background_people':self.reference_people,'additivity_residual':float(residual[0]),'identity':'Same artifact and calibrated probability as displayed; no raw-margin/log-odds explanation substituted','caution':'Contributions are relative model attributions, not the probability change that an intervention would cause.'}
        return result


def load_engine(root):
    root=Path(root);verify_outputs(root)
    settings=json.loads((root/'configs/output_explanations.json').read_text());metadata=json.loads((root/'configs/app_metadata.json').read_text())
    final,questions=validate_final_inputs(root);fields={f['name']:f for f in final['fields']}
    model=joblib.load(root/metadata['classifier']['artifact'])
    background=pd.read_parquet(root/settings['output_dir']/'background.parquet')
    bands=json.loads((root/settings['category_config']).read_text())
    return OutputEngine(root,model,background,settings,bands,metadata,questions,fields)


def build_outputs(root):
    root=Path(root);started=time.perf_counter();settings=json.loads((root/'configs/output_explanations.json').read_text())
    tree=verify_tree_run(root);config,cc,split,people,rows=load_locked(root)
    final,questions=validate_final_inputs(root);fields={f['name']:f for f in final['fields']}
    metadata=json.loads((root/'configs/app_metadata.json').read_text());model_path=root/metadata['classifier']['artifact']
    if fingerprint(model_path)!=metadata['classifier']['sha256']:raise BoundaryError('Output model differs from the pinned selected classifier.')
    signature,provenance=signature_for(root,settings,tree)
    output=root/settings['output_dir'];report=root/settings['report_dir'];bands_path=root/settings['category_config']
    if output.exists() or report.exists() or bands_path.exists():verify_outputs(root);return 'reused_verified_run',json.loads((report/'summary.json').read_text())
    model=joblib.load(model_path);features=model.base['schema'].features
    if features!=metadata['classifier']['features'] or len(features)!=4:raise BoundaryError('Exact four-input explanation design must be reviewed for a changed selected model.')
    # Category definition uses only the already-reserved threshold group.
    reserved=pd.read_parquet(root/settings['category_predictions'])
    authorized=select_keys(rows,config,'threshold')
    merged=reserved[KEYS].merge(authorized,on=KEYS,how='outer',indicator=True,validate='one_to_one')
    if not merged['_merge'].eq('both').all():raise BoundaryError('Category source does not match the reserved threshold keys.')
    cuts=weighted_cuts(reserved['calibrated_probability'],participant_weights(reserved),settings['category_quantiles'])
    groups=category_summary(reserved,cuts)
    if any(group['interval_records']<settings['minimum_category_records'] for group in groups):raise BoundaryError('Score-band group too small; do not silently optimize new category cutoffs.')
    # Explanation background/global sample need only tuning feature columns, no labels.
    tune_ids=people.loc[people['participant_role'].eq('tuning'),'PERSONID'].tolist()
    tuning=pd.read_parquet(root/cc['output_dir']/cc['files']['cohort'],columns=KEYS+features,filters=[('PERSONID','in',tune_ids),('starting_wave','<=',config['development_max_start_wave'])])
    if set(map(tuple,tuning[KEYS].to_numpy()))!=set(map(tuple,select_keys(rows,config,'fit').to_numpy())):raise BoundaryError('Explanation data differ from tuning-only membership.')
    background=deterministic_people(tuning,settings['background_people'],settings['background_namespace'],settings['seed'])
    probe=deterministic_people(tuning,settings['global_explanation_people'],settings['global_namespace'],settings['seed'],exclude=background['PERSONID'])
    output.mkdir(parents=True,exist_ok=False);report.mkdir(parents=True,exist_ok=False)
    bands={'version':'1.0','cuts':cuts,'labels':settings['category_labels'],'source':settings['category_source'],'selection_rule':settings['category_rule'],'boundary_rule':'lower: p<=cut1; moderate: cut1<p<=cut2; higher: p>cut2','caution':settings['category_caution'],'source_prediction_sha256':fingerprint(root/settings['category_predictions']),'source_records':len(reserved),'source_people':int(reserved['PERSONID'].nunique()),'model_sha256':metadata['classifier']['sha256']}
    json_write(bands_path,bands)
    background.to_parquet(output/'background.parquet',index=False);probe.to_parquet(output/'global_sample.parquet',index=False)
    explainer=exact_explainer(model,features,background,root)
    p,base,phi,residual=explain_frame(model,features,explainer,probe,settings['additivity_absolute_tolerance'])
    global_summary=[{'feature':name,'question':fields[name]['description'],'mean_absolute_probability_contribution':float(np.abs(phi[:,i]).mean()),'mean_signed_probability_contribution':float(phi[:,i].mean())} for i,name in enumerate(features)]
    global_summary.sort(key=lambda row:row['mean_absolute_probability_contribution'],reverse=True)
    local=probe[KEYS].copy()
    for i,name in enumerate(features):local[name+'__shap_probability']=phi[:,i]
    local['probability']=p;local['base_value']=base;local.to_parquet(output/'global_attributions.parquet',index=False)
    mapping=transformed_question_map(model,fields)
    engine=OutputEngine(root,model,background,settings,bands,metadata,questions,fields)
    examples=json.loads((root/'tests/fixtures/output_profiles.json').read_text())
    if not examples['synthetic']:raise BoundaryError('Software example fixture must be explicitly synthetic.')
    example_outputs=[{'synthetic':True,'name':profile['name'],'output':engine.output(profile['answers'],profile['eligibility'],wave=profile['wave'])} for profile in examples['profiles']]
    for case in example_outputs:
        value=case['output']
        if value['status']=='scored' and category_for(value['probability'],cuts)!=value['category']['code']:raise BoundaryError('Example category differs from displayed score.')
    summary={'cuts':cuts,'category_groups':groups,'reference_cohort':settings['category_source'],'reference_interval_records':len(reserved),'reference_unique_people':int(reserved['PERSONID'].nunique()),'reference_positive_interval_outcomes':int(reserved['outcome_p30d'].sum()),'reference_interval_prevalence':float(reserved['outcome_p30d'].mean()),'reference_participant_equal_prevalence':float(np.average(reserved['outcome_p30d'],weights=participant_weights(reserved))),
        'category_cutoffs_use_outcomes':False,'background_intervals':len(background),'background_people':int(background['PERSONID'].nunique()),'global_intervals':len(probe),'global_people':int(probe['PERSONID'].nunique()),'global_reference_model_probability':float(base.mean()),'max_additivity_error':float(residual.max()),'explanation_scale':'Actual calibrated positive-class probability, not raw tree log odds','synthetic_profiles_verified':len(example_outputs),'final_test_features_or_outcomes_read':False,'models_fitted':0,'elapsed_seconds':time.perf_counter()-started}
    json_write(report/'summary.json',summary);json_write(report/'global_explanations.json',global_summary);json_write(report/'transformed_question_mapping.json',mapping);json_write(report/'synthetic_profile_outputs.json',example_outputs);json_write(report/'provenance.json',provenance)
    contract={'version':'1.0','required_output_fields':['probability','endpoint','prediction_interval','category','category_thresholds','contributing_factors','input_completeness','model_version','limitations'],'probability':'Unrounded calibrated positive-class probability in [0,1], null if suppressed; not personal confidence','statuses':['scored','insufficient_input','eligibility_unconfirmed','outside_cohort'],'category_rule':bands['boundary_rule'],'category_config':settings['category_config'],'explanation_scale':'calibrated_probability','timing_estimates_included':False,'model_sha256':metadata['classifier']['sha256'],'minimum_observed_inputs':settings['minimum_observed_inputs'],'eligibility_keys':settings['eligibility_keys'],'suppressed_output':'probability/category null; no contributing factors; explain eligibility/input limitation','missing_answer_policy':settings['incomplete_input_policy'],'no_confidence_field':True}
    json_write(root/'configs/output_contract.json',contract)
    paths=[p for folder in [output,report] for p in folder.rglob('*') if p.is_file()]+[bands_path,root/'configs/output_contract.json']
    json_write(output/'manifest.json',{'signature':signature,'provenance':provenance,'output_sha256':{str(path.relative_to(root)):fingerprint(path) for path in paths},'policy':'Frozen verified reuse; do not silently regenerate bands/background/explanations on retry.'})
    verify_outputs(root)
    return 'built_new_immutable_run',summary
