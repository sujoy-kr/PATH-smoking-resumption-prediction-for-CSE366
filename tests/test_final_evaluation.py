"""Pre-exposure synthetic tests for final metric/bootstrap/report implementations."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score,roc_auc_score,brier_score_loss,log_loss
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.final_evaluation import (MetricCalculator,bootstrap_weights,participant_weights,interval,
    compare_predictions,rate_summary,calibration_bins,subgroup_results,category_results,verify_freeze,BoundaryError)
from path_project.final_report import render_final_report


def settings():
    config=json.loads((ROOT/'configs/final_evaluation.json').read_text())
    return {**config,'bootstrap_replicates':30,'subgroup_min_people':2,'subgroup_min_positive_records':1,'subgroup_min_negative_records':1}


def synthetic():
    y=[0,1,0,0,1,1,0,1]
    frame=pd.DataFrame({'PERSONID':['SYN_A','SYN_A','SYN_B','SYN_C','SYN_D','SYN_D','SYN_E','SYN_F'],'outcome_p30d':y,
        'age_band':[1,1,2,3,4,4,5,6],'sex_recorded':[1,1,2,1,2,2,1,None],
        'last_cigarette_recency_days':[60,60,None,800,200,200,None,1800],
        'recency_boundary_report':[False,False,False,False,True,True,False,False]})
    frame['probability__selected_calibrated']=[.1,.6,.2,.3,.8,.8,.2,.9]
    frame['probability__selected_raw']=[.05,.4,.1,.2,.6,.6,.1,.7]
    frame['probability__minimal_logistic_calibrated']=[.1,.5,.2,.3,.7,.7,.2,.8]
    frame['probability__training_prevalence']=.25
    return frame


def models():return {name:{'description':'Synthetic comparator only','threshold':.5} for name in ['selected_calibrated','selected_raw','minimal_logistic_calibrated','training_prevalence']}


def test_cached_order_ap_auc_losses_match_sklearn_ties_weights_and_zero_draws():
    rng=np.random.default_rng(366)
    for _ in range(30):
        y=rng.integers(0,2,40);p=np.round(rng.uniform(.01,.99,40),1);weights=rng.integers(0,5,40).astype(float)
        mask=weights>0
        if len(np.unique(y[mask]))<2:continue
        result=MetricCalculator(y,p,.5,np.finfo(float).eps).evaluate(weights)
        assert result['average_precision']==pytest.approx(average_precision_score(y[mask],p[mask],sample_weight=weights[mask]),abs=1e-12)
        assert result['roc_auc']==pytest.approx(roc_auc_score(y[mask],p[mask],sample_weight=weights[mask]),abs=1e-12)
        assert result['brier']==pytest.approx(brier_score_loss(y,p,sample_weight=weights),abs=1e-12)
        assert result['log_loss']==pytest.approx(log_loss(y,p,sample_weight=weights,labels=[0,1]),abs=1e-12)


def test_undefined_class_and_prediction_metrics_explicit():
    score=MetricCalculator([0,0],[.1,.2],.5,np.finfo(float).eps).evaluate([1,1])
    assert score['average_precision'] is None and score['roc_auc'] is None and score['precision'] is None and score['recall'] is None and score['f1'] is None
    assert score['specificity']==1 and score['brier'] is not None
    score=MetricCalculator([1,1],[.1,.9],.5,np.finfo(float).eps).evaluate([1,1])
    assert score['average_precision']==1 and score['roc_auc'] is None and score['specificity'] is None
    counts=interval([None,1,None],3,.95)
    assert counts['valid_replicates']==1 and counts['undefined_replicates']==2
    assert interval([None,None],2,.95)['lower'] is None


def test_cluster_draws_preserve_each_occurrence_and_not_independent_rows():
    ids=pd.Series(['SYN_A','SYN_A','SYN_B'])
    class Draw:
        def integers(self,*args,**kwargs):return np.array([0,0])
    weights=bootstrap_weights(ids,Draw())
    np.testing.assert_array_equal(weights,[1,1,0]) # two A draws, each distributed over its two rows
    assert weights.sum()==2
    np.testing.assert_array_equal(participant_weights(ids),[.5,.5,1])


def test_paired_bootstrap_identical_models_have_zero_differences_and_determinism():
    data=synthetic();data['probability__selected_raw']=data['probability__selected_calibrated']
    chosen={name:spec for name,spec in models().items() if name in ['selected_calibrated','selected_raw']}
    first,paired=compare_predictions(data,chosen,settings());second,again=compare_predictions(data,chosen,settings())
    assert first==second and paired==again
    assert paired['selected_raw']['average_precision']['lower']==0
    assert paired['selected_raw']['brier']['upper']==0
    assert first['selected_calibrated']['confidence_intervals']['roc_auc']['valid_replicates']<=settings()['bootstrap_replicates']


def test_fixed_calibration_bins_keep_empty_undefined_cells_and_all_records():
    data=synthetic();bins=calibration_bins(data['outcome_p30d'],data['probability__selected_calibrated'],data['PERSONID'],settings())
    assert sum(row['records'] for row in bins)==len(data)
    empty=[row for row in bins if row['records']==0]
    assert empty and all(row['observed_fraction'] is None and row['observed_fraction_ci']['valid_replicates']==0 for row in empty)


def test_category_and_subgroup_counts_and_small_group_suppression():
    data=synthetic();groups=category_results(data,[.2,.7],settings())
    assert sum(row['records'] for row in groups)==len(data)
    assert sum(row['positive_records'] for row in groups)==data['outcome_p30d'].sum()
    results=subgroup_results(data,settings(),.5)
    assert any(row['performance_supported'] for row in results)
    assert any(not row['performance_supported'] and row['performance'] is None for row in results)
    unknown=next(row for row in results if row['subgroup']=='unknown_last_use_recency')
    assert unknown['records']==2


def test_freeze_rejects_absent_manifest_before_any_test_access(tmp_path):
    (tmp_path/'configs').mkdir();(tmp_path/'configs/final_evaluation.json').write_text(json.dumps({'output_dir':'local'}))
    with pytest.raises(BoundaryError,match='absent/incomplete'):verify_freeze(tmp_path)


def test_final_report_smoke_with_fictional_results(tmp_path):
    data=synthetic();config=settings();scores,paired=compare_predictions(data,models(),config)
    result={'model_version':'SYNTHETIC-NOT-A-PATH-MODEL','evaluation_signature':'synthetic','endpoint':'Synthetic test fixture only','test_pair':[7,8],'records':len(data),'unique_people':data['PERSONID'].nunique(),'positive_records':int(data['outcome_p30d'].sum()),'negative_records':int(data['outcome_p30d'].eq(0).sum()),'positive_prevalence':data['outcome_p30d'].mean(),'people_with_repeated_test_records':2,'metrics':scores,'paired_difference_selected_minus_baseline':paired,
        'calibration':{name:calibration_bins(data['outcome_p30d'],data['probability__'+name],data['PERSONID'],config) for name in config['calibration_plot_models']},'risk_categories':category_results(data,[.2,.7],config),'risk_cuts':[.2,.7],'subgroups':subgroup_results(data,config,.5),'bootstrap_replicates':config['bootstrap_replicates'],'bootstrap_seed':366,'bootstrap_method':config['bootstrap_method'],'timing_decision':'C','app_input_coverage':{'records_meeting_input_count':len(data),'minimum_supplied_inputs':2}}
    render_final_report(tmp_path,result,config)
    assert (tmp_path/config['report_markdown']).is_file()
    assert len(list((tmp_path/config['report_dir']).glob('*.png')))==3
    assert 'Synthetic test fixture' in (tmp_path/config['report_markdown']).read_text()
