"""Stage 7 correctness uses synthetic data only, never reserved final evaluation."""
import json,sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import auc,precision_recall_curve,f1_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.baselines import (make_pipeline,metric_block,metrics,reliability,
    fit_sigmoid,choose_threshold,CalibratedBaseline,BoundaryError)


@pytest.fixture
def setup():
    final=json.loads((ROOT/'configs/feature_mapping_final.json').read_text())
    settings=json.loads((ROOT/'configs/baseline_models.json').read_text())
    X=pd.DataFrame({'age_band':[1,1,2,2,1,2,1,2],
        'education_level':[1,2,1,2,2,1,1,2],
        'employment_status':[1,2,1,2,1,2,1,2],
        'last_cigarette_recency_days':[40,60,None,100,200,300,400,None]})
    y=np.array([0,0,1,0,0,1,0,0])
    return final,settings,X,y


def fit(setup,name='minimal_logistic'):
    final,settings,X,y=setup
    candidate=next(c for c in settings['models_in_simplicity_order'] if c['name']==name)
    model=make_pipeline(candidate,final,settings).fit(X,y)
    return model,X,y


def test_prevalence_baseline_is_training_not_evaluation_prevalence(setup):
    model,X,y=fit(setup,'training_prevalence')
    evaluation=X.iloc[:3].copy();evaluation['last_cigarette_recency_days']=10000
    # Evaluation labels are entirely positive; never passed to training or prediction.
    evaluation_y=np.ones(3)
    p=model.predict_proba(evaluation)[:,1]
    assert np.array_equal(p,np.repeat(y.mean(),3))
    assert not np.isclose(p[0],evaluation_y.mean())


def test_imputation_encoding_scaling_fit_only_training_and_unseen_category_safe(setup):
    model,X,y=fit(setup)
    med=model['preprocess'].named_transformers_['numeric']['impute'].statistics_.copy()
    mean=model['preprocess'].named_transformers_['numeric']['scale'].mean_.copy()
    expected=np.nanmedian(X['last_cigarette_recency_days'])
    assert med[0]==expected
    valid=X.iloc[:2].copy();valid['age_band']=6;valid['education_level']=5;valid['last_cigarette_recency_days']=[None,30000]
    prediction=model.predict_proba(valid)
    assert np.isfinite(prediction).all() and np.allclose(prediction.sum(axis=1),1)
    np.testing.assert_array_equal(med,model['preprocess'].named_transformers_['numeric']['impute'].statistics_)
    np.testing.assert_array_equal(mean,model['preprocess'].named_transformers_['numeric']['scale'].mean_)
    names=model[:-1].get_feature_names_out().tolist()
    assert any('missingindicator' in name for name in names)
    assert len(names)==model['model'].coef_.shape[1]
    assert not any('PERSONID' in name or 'outcome' in name for name in names)


@pytest.mark.parametrize('change',['extra_id','extra_outcome','missing_feature','bad_code','infinity','negative','text'])
def test_schema_rejects_forbidden_or_invalid_prediction_inputs(setup,change):
    model,X,y=fit(setup);bad=X.copy()
    if change=='extra_id':bad['PERSONID']='SYN_ONLY'
    elif change=='extra_outcome':bad['outcome_p30d']=1
    elif change=='missing_feature':bad=bad.drop(columns='age_band')
    elif change=='bad_code':bad['age_band']=99
    elif change=='infinity':bad['last_cigarette_recency_days']=np.inf
    elif change=='negative':bad['last_cigarette_recency_days']=-20
    else:bad['education_level']='unmapped string'
    with pytest.raises(BoundaryError):model.predict_proba(bad)


def test_reload_and_column_order_prediction_consistency(setup,tmp_path):
    model,X,y=fit(setup);path=tmp_path/'synthetic.joblib';joblib.dump(model,path)
    restored=joblib.load(path)
    np.testing.assert_array_equal(model.predict_proba(X),restored.predict_proba(X[X.columns[::-1]]))


def test_average_precision_is_not_trapezoidal_pr_auc():
    y=np.array([0,1]);p=np.array([.9,.8]);weights=np.ones(2)
    result=metric_block(y,p,.5,weights)
    precision,recall,_=precision_recall_curve(y,p)
    assert result['average_precision']==.5
    assert result['average_precision']!=auc(recall,precision)
    assert result['prevalence']==.5


def test_constant_score_ap_equals_evaluation_prevalence_with_metric_weights():
    y=[0,1,0,1];p=[.2]*4;weights=[1,.5,1,.5]
    result=metric_block(y,p,.5,weights)
    assert result['average_precision']==pytest.approx(1/3)
    assert result['mean_predicted_probability']==pytest.approx(.2)


def frame(y):
    return pd.DataFrame({'PERSONID':['SYN_A','SYN_A','SYN_B','SYN_C'],'outcome_p30d':y})


def test_threshold_rule_matches_exhaustive_participant_weighted_f1():
    data=frame([0,1,1,0]);p=np.array([.2,.7,.8,.9])
    chosen,value=choose_threshold(data,p)
    weights=np.array([.5,.5,1,1])
    values=[(f1_score(data['outcome_p30d'],p>=threshold,sample_weight=weights),threshold) for threshold in np.unique(p)]
    expected_value,expected_threshold=max(values)
    assert value==pytest.approx(expected_value)
    assert chosen==expected_threshold


def test_reserved_sigmoid_does_not_refit_base_pipeline_and_bundle_roundtrip(setup,tmp_path):
    final,settings,X,y=setup;model,X,y=fit(setup,'minimal_logistic_balanced')
    coefficients=model['model'].coef_.copy();median=model['preprocess'].named_transformers_['numeric']['impute'].statistics_.copy()
    # Explicitly synthetic calibration participants differ from synthetic base data.
    cal=frame([0,1,1,0]);raw=model.predict_proba(X.iloc[:4])[:,1]
    sigmoid=fit_sigmoid(cal,raw,settings)
    bundle=CalibratedBaseline(model,sigmoid,settings['calibrator']['clip_epsilon'],.3)
    path=tmp_path/'bundle.joblib';joblib.dump(bundle,path)
    np.testing.assert_array_equal(bundle.predict_proba(X),joblib.load(path).predict_proba(X))
    np.testing.assert_array_equal(coefficients,model['model'].coef_)
    np.testing.assert_array_equal(median,model['preprocess'].named_transformers_['numeric']['impute'].statistics_)
    assert np.isfinite(bundle.predict_proba(X)).all()


def test_reliability_bins_and_participant_vs_interval_metric_context():
    data=frame([0,1,1,0]);p=np.array([0,.2,.8,1])
    bins=reliability(data,p,[0,.5,1])
    assert sum(r['records'] for r in bins)==4
    scores=metrics(data,p,.5)
    assert scores['people']==3 and scores['records']==4
    assert scores['interval_equal']['prevalence']==.5
    assert scores['participant_equal']['prevalence']==.5


def test_all_missing_numeric_training_still_preserves_feature_dimension(setup):
    final,settings,X,y=setup;X['last_cigarette_recency_days']=np.nan
    candidate=settings['models_in_simplicity_order'][1]
    model=make_pipeline(candidate,final,settings).fit(X,y)
    assert np.isfinite(model.predict_proba(X)).all()
    assert len(model[:-1].get_feature_names_out())==model['model'].coef_.shape[1]
