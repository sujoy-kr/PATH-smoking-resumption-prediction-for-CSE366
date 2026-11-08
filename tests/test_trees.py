"""Synthetic tree tests; no real PATH or final-test fitting."""
import json,sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.trees import candidates_for,tree_pipeline,select_candidate,quality_check,available_booster
from path_project.evaluation import BoundaryError


@pytest.fixture
def setup():
    settings=json.loads((ROOT/'configs/tree_models.json').read_text())
    baseline=json.loads((ROOT/'configs/baseline_models.json').read_text())
    final=json.loads((ROOT/'configs/feature_mapping_final.json').read_text())
    X=pd.DataFrame({'age_band':[1,1,2,2,1,2,1,2],'education_level':[1,2,1,2,2,1,1,2],'employment_status':[1,2,1,2,1,2,1,2],'last_cigarette_recency_days':[40,60,None,100,200,300,400,None]})
    y=np.array([0,0,0,0,0,1,0,1])
    return settings,baseline,final,X,y


def test_search_is_fixed_and_paired_across_profiles_and_weights(setup):
    candidates=candidates_for(setup[0],'xgboost')
    assert len(candidates)==16 and len({c['name'] for c in candidates})==16
    for family in ['random_forest','xgboost']:
        for profile in ['minimal','app']:
            assert len([c for c in candidates if c['family']==family and c['profile']==profile])==4
    assert all(c['params']['n_jobs']==1 for c in candidates)
    assert not any('early_stopping_rounds' in c['params'] for c in candidates)


@pytest.mark.parametrize('family',['random_forest','xgboost','hist_gradient_boosting'])
def test_tiny_tree_pipeline_preserves_schema_and_unseen_categories(setup,family,tmp_path):
    settings,baseline,final,X,y=setup
    if family=='xgboost' and available_booster()[0]!='xgboost':pytest.skip('Optional XGBoost unavailable; alternative covered separately.')
    boost='hist_gradient_boosting' if family=='hist_gradient_boosting' else 'xgboost'
    candidate=next(c for c in candidates_for(settings,boost) if c['family']==family and c['profile']=='minimal' and c['weight']=='none')
    candidate['params']={**candidate['params']}
    if family=='random_forest':candidate['params']['n_estimators']=3
    elif family=='xgboost':candidate['params']['n_estimators']=3
    else:candidate['params']['max_iter']=3
    pipeline,ratio=tree_pipeline(candidate,final,baseline,settings,y)
    assert ratio is None
    pipeline.fit(X,y)
    valid=X.copy();valid['age_band']=6;valid['last_cigarette_recency_days']=None
    predicted=pipeline.predict_proba(valid)
    assert np.isfinite(predicted).all() and np.allclose(predicted.sum(axis=1),1)
    assert pipeline[:-1].get_feature_names_out().size>len(final['feature_sets']['minimal'])
    path=tmp_path/'synthetic_tree.joblib';joblib.dump(pipeline,path)
    np.testing.assert_allclose(predicted,joblib.load(path).predict_proba(valid),rtol=0,atol=1e-12)
    with pytest.raises(BoundaryError):pipeline.predict_proba(valid.assign(PERSONID='SYN_ONLY'))


@pytest.mark.parametrize('family',['random_forest','xgboost','hist_gradient_boosting'])
def test_balanced_options_derive_only_training_class_counts(setup,family):
    settings,baseline,final,X,y=setup
    if family=='xgboost' and available_booster()[0]!='xgboost':pytest.skip('Optional XGBoost unavailable; alternative covered separately.')
    candidates=candidates_for(settings,'hist_gradient_boosting' if family=='hist_gradient_boosting' else 'xgboost')
    candidate=next(c for c in candidates if c['family']==family and c['weight']=='balanced')
    pipeline,ratio=tree_pipeline(candidate,final,baseline,settings,y)
    assert ratio==3
    if family=='xgboost':assert pipeline['model'].get_params()['scale_pos_weight']==3
    else:assert pipeline['model'].class_weight=='balanced'
    _,new_ratio=tree_pipeline(candidate,final,baseline,settings,np.array([0,1,1,1]))
    assert new_ratio==pytest.approx(1/3)


def test_selector_preserves_ap_then_existing_order_and_requires_probability_quality():
    def row(name,ap,brier):
        score={'brier':brier,'log_loss':.5,'average_precision':ap,'roc_auc':.7}
        return {'model':name,'mean_fold_participant_metrics':{'average_precision':ap},'pooled_oof':{'participant_equal':score.copy(),'interval_equal':score.copy()}}
    assert select_candidate([row('simpler',.4,.15),row('other',.4,.14)])=='simpler'
    assert select_candidate([row('lower_ap',.4,.14),row('higher_ap',.5,.18)])=='higher_ap'
    with pytest.raises(BoundaryError):select_candidate([row('bad',.4,float('nan'))])


def test_single_class_training_refused(setup):
    settings,baseline,final,X,y=setup
    candidate=candidates_for(settings,'xgboost')[0]
    with pytest.raises(BoundaryError):tree_pipeline(candidate,final,baseline,settings,np.zeros(8))
