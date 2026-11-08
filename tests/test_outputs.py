"""Stage 10 tests use software profiles and inference only, never model fitting."""
import json,sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.outputs import weighted_cuts,category_for,category_summary,OutputEngine,deterministic_people,transformed_question_map
from path_project.evaluation import BoundaryError
from path_project.final_inputs import validate_final_inputs


def test_categories_use_score_weights_not_outcome_optimization_and_keep_ties():
    frame=pd.DataFrame({'PERSONID':['SYN_A','SYN_A','SYN_B','SYN_C','SYN_D','SYN_E'],'calibrated_probability':[.02,.02,.10,.10,.4,.8],'outcome_p30d':[0,1,0,1,0,1]})
    cuts=weighted_cuts(frame['calibrated_probability'],[.5,.5,1,1,1,1],[1/3,2/3])
    frame['outcome_p30d']=1-frame['outcome_p30d']
    assert weighted_cuts(frame['calibrated_probability'],[.5,.5,1,1,1,1],[1/3,2/3])==cuts
    assert cuts==[.1,.4]
    assert category_for(.1,cuts)=='lower' and category_for(.4,cuts)=='moderate'
    assert category_for(np.nextafter(.1,1),cuts)=='moderate'
    assert category_for(np.nextafter(.4,1),cuts)=='higher'
    assert sum(row['interval_records'] for row in category_summary(frame,cuts))==len(frame)


@pytest.mark.parametrize('scores,weights', [([],[]),([.1,.1],[1,1]),([np.nan,.2],[1,1]),([.1,.3],[1,0]),([.1],[1,1])])
def test_unsupported_category_data_rejected_without_inventing_bands(scores,weights):
    with pytest.raises(BoundaryError):weighted_cuts(scores,weights,[1/3,2/3])


def test_reference_sampling_is_deterministic_one_per_person_and_excludes_heldout_keys():
    data=pd.DataFrame({'PERSONID':['SYN_A','SYN_A','SYN_B','SYN_C'],'starting_wave':[1,2,1,1],'followup_wave':[2,3,2,2]})
    first=deterministic_people(data,2,'synthetic',366,exclude=['SYN_C'])
    other=deterministic_people(data.iloc[::-1],2,'synthetic',366,exclude=['SYN_C'])
    pd.testing.assert_frame_equal(first,other)
    assert first['PERSONID'].nunique()==2 and 'SYN_C' not in set(first['PERSONID'])


@pytest.fixture(scope='module')
def engine():
    settings=json.loads((ROOT/'configs/output_explanations.json').read_text());metadata=json.loads((ROOT/'configs/app_metadata.json').read_text())
    final,questions=validate_final_inputs(ROOT);fields={f['name']:f for f in final['fields']}
    model=joblib.load(ROOT/metadata['classifier']['artifact'])
    background=pd.DataFrame({'age_band':[1,2,4,6],'education_level':[2,3,4,5],'employment_status':[1,2,4,4],'last_cigarette_recency_days':[60,365.25,None,3652.5]},dtype=float)
    return OutputEngine(ROOT,model,background,settings,{'cuts':[.1,.3]},metadata,questions,fields)


def profiles():return json.loads((ROOT/'tests/fixtures/output_profiles.json').read_text())['profiles']


def test_valid_profiles_explain_actual_calibrated_probability_and_category(engine):
    for profile in profiles()[:5]:
        result=engine.output(profile['answers'],profile['eligibility'],wave=profile['wave'])
        assert result['status']=='scored' and 0<=result['probability']<=1
        assert result['category']['code']==category_for(result['probability'],[.1,.3])
        reconstructed=result['explanation']['reference_model_probability']+sum(f['contribution'] for f in result['contributing_factors'])
        assert reconstructed==pytest.approx(result['probability'],abs=1e-8)
        assert result['explanation']['scale']=='calibrated_probability'
        assert len(result['contributing_factors'])==4
        assert result['model_version']['artifact_sha256']==engine.metadata['classifier']['sha256']
        assert 'confidence' not in result and 'timing' not in result and 'relapse_date' not in result


def test_missing_reasons_are_preserved_and_all_unknown_outputs_suppressed(engine):
    partial=profiles()[4];result=engine.output(partial['answers'],partial['eligibility'])
    assert result['input_completeness']['provided']==2
    reasons=result['input_completeness']['reasons']
    assert reasons['employment_status']=='app_refused' and reasons['last_cigarette_recency_days']=='app_dont_know'
    for profile,status in zip(profiles()[5:],['insufficient_input','eligibility_unconfirmed','outside_cohort']):
        result=engine.output(profile['answers'],profile['eligibility'])
        assert result['status']==status and result['probability'] is None and result['category'] is None
        assert result['contributing_factors']==[] and result['suppression_reason']


def test_output_rejects_time_estimates_and_nonmodel_answers(engine):
    profile=profiles()[0]
    with pytest.raises(BoundaryError):engine.output(profile['answers'],profile['eligibility'],elapsed_horizon=1)
    with pytest.raises(BoundaryError):engine.output(profile['answers'],profile['eligibility'],request_relapse_date=True)
    with pytest.raises(BoundaryError):engine.output({**profile['answers'],'PERSONID':'SYN_ONLY'},profile['eligibility'])
    with pytest.raises(BoundaryError):engine.output({**profile['answers'],'physical_health':'1'},profile['eligibility'])


def test_transformed_columns_map_to_exact_selected_questions_and_categories(engine):
    mapping=transformed_question_map(engine.model,engine.fields)
    assert [r['transformed_feature'] for r in mapping]==engine.model.base['preprocess'].get_feature_names_out().tolist()
    assert {r['question_feature'] for r in mapping}==set(engine.features)
    assert any(r['category_label']=='18–24' for r in mapping)
    assert any('missing indicator' in r['transform'] for r in mapping)
