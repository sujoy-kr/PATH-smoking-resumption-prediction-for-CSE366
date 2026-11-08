"""Stage 9 tests guard unsupported timing; no survival/real model fitting."""
from copy import deepcopy
import json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.timing import validate_timing_policy,build_app_metadata,next_survey_output_metadata,CAPABILITIES
from path_project.evaluation import BoundaryError


def policy():return json.loads((ROOT/'configs/timing_decision.json').read_text())


def test_c_decision_matches_implemented_target_and_empty_horizons():
    p=policy();validate_timing_policy(p)
    for name in ['configs/prediction_specification.json','configs/prediction_specification_final.json']:
        assert json.loads((ROOT/name).read_text())['timing_decision']=='C'
    schema=json.loads((ROOT/'data/processed/cohort_v1/schema.json').read_text())
    assert schema['timing_decision'].startswith('C')
    assert p['supported_elapsed_time_horizons']==[]


@pytest.mark.parametrize('capability',CAPABILITIES)
def test_no_unsupported_timing_capability_can_be_enabled(capability):
    p=policy();p[capability]=True
    with pytest.raises(BoundaryError):validate_timing_policy(p)


def test_no_elapsed_horizon_can_be_enabled():
    p=policy();p['supported_elapsed_time_horizons']=[1,2,3]
    with pytest.raises(BoundaryError):validate_timing_policy(p)
    p=policy();p['decision']='A'
    with pytest.raises(BoundaryError):validate_timing_policy(p)


def metadata():
    return build_app_metadata(policy(),{'classifier':{'artifact':'synthetic_only.joblib','sha256':'synthetic-hash','status':'not a trained fixture'}})


@pytest.mark.parametrize('horizon',[0,1,2,3,365.25,'one year'])
def test_app_rejects_horizon_requests_instead_of_placeholder_probability(horizon):
    with pytest.raises(BoundaryError,match='unavailable'):next_survey_output_metadata(metadata(),elapsed_horizon=horizon)


def test_app_rejects_relapse_date_and_keeps_classification_label():
    with pytest.raises(BoundaryError,match='unavailable'):next_survey_output_metadata(metadata(),request_relapse_date=True)
    output=next_survey_output_metadata(metadata())
    assert output['elapsed_time_estimates_available'] is False
    assert 'next scheduled PATH survey' in output['endpoint']
    assert not any(key in output for key in ['annual_probability','relapse_date','survival_curve'])


def test_saved_app_metadata_has_no_probability_or_date_payload():
    m=json.loads((ROOT/'configs/app_metadata.json').read_text())
    assert m['classifier_available'] and m['supported_elapsed_time_horizons']==[]
    assert all(m[key] is False for key in CAPABILITIES)
    assert m['classifier']['features']==['age_band','education_level','employment_status','last_cigarette_recency_days']
    assert not any(key in m for key in ['annual_probability','one_year_probability','two_year_probability','three_year_probability','estimated_relapse_date'])
    assert 'historical' in m['historical_recency_role'] or 'history' in m['historical_recency_role']


def test_confirmation_rechecks_actual_headers_schemas_and_documentation_only():
    result=json.loads((ROOT/'reports/timing_confirmation_v1.json').read_text())
    assert result['decision']=='C' and result['timing_analysis_omitted']
    assert len(result['header_checks'])==8 and len(result['documentation_hashes'])==16
    assert all(not row['interview_clock_candidates'] and row['rows_read']==0 for row in result['header_checks'])
    assert len(result['cohort_schema_checks'])==2
    assert all(row['rows_read']==0 for row in result['cohort_schema_checks'])
    assert len(result['live_documentation_rechecks'])==4 and all(row['matched'] for row in result['live_documentation_rechecks'])
    assert result['survey_or_cohort_answer_rows_read']==0 and result['models_fitted']==0
    assert not result['final_test_features_or_outcomes_read']
