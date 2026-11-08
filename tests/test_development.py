"""Stage 6 tests use synthetic keys/answers or metadata; no real model fitting."""
import json,sys
from pathlib import Path
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.development import ensure_tuning,recency_groups,load_tuning
from path_project.final_inputs import validate_final_inputs,encode_app_answers,fit_profile_pipeline
from path_project.evaluation import BoundaryError


def test_profiles_preserve_locked_source_meanings():
    final,questions=validate_final_inputs(ROOT)
    assert len(final['feature_sets']['app'])==11
    assert len(final['feature_sets']['minimal'])==4
    assert len(final['feature_sets']['research'])==25
    assert not set(['sex_recorded','prior_regular_cigarettes_per_day','regular_smoking_months']) & set(final['feature_sets']['app'])
    assert not final['cohort_or_recoding_changed']


@pytest.mark.parametrize('role',['heldout','calibration','threshold'])
def test_eda_rejects_every_non_tuning_role(role):
    people=pd.DataFrame({'PERSONID':['SYN_TUNE','SYN_OTHER'],'participant_role':['tuning',role]})
    frame=pd.DataFrame({'PERSONID':['SYN_OTHER'],'starting_wave':[1],'followup_wave':[2]})
    with pytest.raises(BoundaryError):ensure_tuning(frame,people,{'development_max_start_wave':6})


def test_eda_rejects_future_interval_and_accepts_tuning():
    people=pd.DataFrame({'PERSONID':['SYN_TUNE'],'participant_role':['tuning']})
    frame=pd.DataFrame({'PERSONID':['SYN_TUNE'],'starting_wave':[1],'followup_wave':[2]})
    ensure_tuning(frame,people,{'development_max_start_wave':6})
    frame['starting_wave']=7;frame['followup_wave']=8
    with pytest.raises(BoundaryError):ensure_tuning(frame,people,{'development_max_start_wave':6})


def test_unknown_recency_is_never_zero_or_recent():
    settings=json.loads((ROOT/'configs/development_exploration.json').read_text())
    grouped=recency_groups(pd.Series([None,31,365.25,365.3,50000],dtype='Float64'),settings)
    assert grouped.tolist()==['Unknown / skipped','over 30 days to 1 year','over 30 days to 1 year','over 1 to 5 years','over 100 years (review)']


def test_missing_app_answers_are_null_with_distinct_reasons():
    values,reasons=encode_app_answers(ROOT,{},7)
    assert all(v is None for v in values.values())
    assert set(reasons.values())=={'app_unanswered'}
    for response,reason in [('dont_know','app_dont_know'),('prefer_not_to_answer','app_refused'),('not_applicable','app_not_applicable'),('not_previously_asked','app_not_previously_asked')]:
        values,reasons=encode_app_answers(ROOT,{'household_tobacco_any':response},7)
        assert values['household_tobacco_any'] is None and reasons['household_tobacco_any']==reason
    values,reasons=encode_app_answers(ROOT,{'household_tobacco_any':'0'},7)
    assert values['household_tobacco_any']==0 and reasons['household_tobacco_any']=='observed'


def test_recency_encoding_units_eligibility_conflict_and_no_fabricated_history():
    values,_=encode_app_answers(ROOT,{'last_cigarette_recency_days':{'number':2,'unit':'2'}},2)
    assert values['last_cigarette_recency_days']==60.875
    for answer in [{'number':1,'unit':'3'},{'number':100,'unit':'2'},{'number':0,'unit':'1'},{'number':1,'unit':'1'},{'number':2.5,'unit':'2'},{'number':float('inf'),'unit':'2'}]:
        with pytest.raises(BoundaryError):encode_app_answers(ROOT,{'last_cigarette_recency_days':answer},2)
    with pytest.raises(BoundaryError):encode_app_answers(ROOT,{'prior_regular_cigarettes_per_day':20},7)
    with pytest.raises(BoundaryError):encode_app_answers(ROOT,{},8)


def test_wave_specific_electronic_product_and_health_question_semantics():
    _,spec=validate_final_inputs(ROOT)
    questions={q['feature']:q for q in spec['questions']}
    assert 'e-cigarette' in questions['electronic_nicotine_p30d']['waves']['2']['prompt']
    assert 'electronic nicotine product' in questions['electronic_nicotine_p30d']['waves']['3']['prompt']
    assert 'stress, depression' in questions['mental_health']['waves']['7']['prompt']
    assert 'completely quit' in questions['last_cigarette_recency_days']['waves']['1']['prompt']
    assert 'pouches and oral nicotine' in questions['household_tobacco_any']['waves']['7']['prompt']


def test_profile_fitter_delegates_only_explicit_allowlist(monkeypatch):
    import path_project.training_boundaries as boundary
    calls=[]
    monkeypatch.setattr(boundary,'fit_development_pipeline',lambda root,estimator,fold,predictors:calls.append((fold,predictors)))
    fit_profile_pipeline(ROOT,object(),'app',fold=2)
    final,_=validate_final_inputs(ROOT)
    assert calls==[(2,final['feature_sets']['app'])]
    with pytest.raises(BoundaryError):fit_profile_pipeline(ROOT,object(),'unknown')


def test_tuning_loader_pushes_participant_and_wave_filters_before_features(monkeypatch,tmp_path):
    import path_project.development as module
    mapping=json.loads((ROOT/'configs/feature_mapping.json').read_text())
    (tmp_path/'mapping.json').write_text(json.dumps(mapping))
    people=pd.DataFrame({'PERSONID':['SYN_TUNE','SYN_TEST','SYN_CAL'],'participant_role':['tuning','heldout','calibration']})
    config={'development_max_start_wave':6}
    cc={'feature_mapping':'mapping.json','output_dir':'local','files':{'cohort':'cohort.parquet','ledger':'ledger.parquet'}}
    keys={'PERSONID':['SYN_TUNE'],'starting_wave':[1],'followup_wave':[2]}
    rows=pd.DataFrame({**keys,'partition':['tuning']})
    cohort=pd.DataFrame({**keys,'outcome_p30d':[0]})
    for name in mapping['candidate_predictor_names']:cohort[name]=None;cohort[name+'__reason']='structural_skip'
    ledger=pd.DataFrame({**keys,'observation_status':['observed_valid']})
    monkeypatch.setattr(module,'load_locked',lambda root:(config,cc,{},people,rows))
    calls=[]
    def reader(path,**kwargs):
        assert kwargs['filters']==[('PERSONID','in',['SYN_TUNE']),('starting_wave','<=',6)]
        calls.append(Path(path).name)
        return cohort.copy() if Path(path).name=='cohort.parquet' else ledger.copy()
    monkeypatch.setattr(module.pd,'read_parquet',reader)
    result=load_tuning(tmp_path,{})
    assert calls==['cohort.parquet','ledger.parquet'] and len(result[-1])==1
