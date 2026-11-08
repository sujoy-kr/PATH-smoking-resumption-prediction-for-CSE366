"""Correctness tests use explicitly synthetic data, never real participant rows."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.cohort import (CohortError, interval_cohort, load_contract, needed_columns,
                                read_wave, validate_frames, validate_ids, verify_completed_run)


@pytest.fixture(scope='module')
def contract():
    return load_contract(ROOT)


@pytest.fixture
def synthetic(contract):
    config,project,task,mapping=contract
    fixture=json.loads((ROOT/'tests/fixtures/synthetic_cohort.json').read_text())
    assert fixture['synthetic'] and fixture['not_real_PATH_data']
    def frame(records,wave):
        columns=sorted(set(needed_columns(wave,task,mapping,config)) | {key for row in records for key in row})
        return pd.DataFrame([{column:row.get(column,'') for column in columns} for row in records],dtype='string')
    return frame(fixture['baseline_records'],1),frame(fixture['followup_records'],2),fixture['expected']


def prepare(contract,synthetic):
    config,project,task,mapping=contract
    left,right,expected=synthetic
    return interval_cohort(left,right,1,2,task,mapping,config)


def test_binary_labels_missing_followup_and_flow_reconciliation(contract,synthetic):
    cohort,ledger,flow,availability,details=prepare(contract,synthetic)
    for key,value in synthetic[2].items():
        assert flow[key]==value
    assert len(ledger)==5 and len(cohort)==3
    labels=cohort.set_index('PERSONID')['outcome_p30d']
    assert labels.to_dict()=={'SYN_0001':1,'SYN_0002':0,'SYN_0009':0}
    unknown=ledger.set_index('PERSONID')
    assert pd.isna(unknown.loc['SYN_0003','outcome_p30d'])
    assert unknown.loc['SYN_0003','observation_status']=='missing_followup_interview'
    assert pd.isna(unknown.loc['SYN_0004','outcome_p30d'])
    assert unknown.loc['SYN_0004','outcome_reason']=='dont_know'
    assert flow['secondary_valid_records']==2 and flow['secondary_unknown_records']==1
    assert len(availability)==50
    validate_frames(cohort,ledger,contract[3],contract[2],contract[0])


def test_zero_skip_no_answer_and_all_component_reasons_are_distinct(contract,synthetic):
    cohort,ledger,flow,availability,details=prepare(contract,synthetic)
    rows=cohort.set_index('PERSONID')
    assert rows.loc['SYN_0001','alcohol_days_30d']==0
    assert rows.loc['SYN_0001','alcohol_days_30d__reason']=='observed'
    assert pd.isna(rows.loc['SYN_0002','alcohol_days_30d'])
    assert rows.loc['SYN_0002','alcohol_days_30d__reason']=='structural_skip'
    assert rows.loc['SYN_0002','physical_health__reason']=='not_ascertained'
    assert rows.loc['SYN_0002','last_cigarette_recency_days__reason']=='structural_skip'
    assert ledger.set_index('PERSONID').loc['SYN_0002','recency_group']=='unknown_recency'
    # Mixed component missing reasons survive even when one feature reason is primary.
    left,right,expected=synthetic
    right.loc[right['PERSONID']=='SYN_0004','R02R_A_P30D_CIGS']='2'
    cohort,*_=prepare(contract,(left,right,expected))
    reasons=json.loads(cohort.set_index('PERSONID').loc['SYN_0004','last_cigarette_recency_days__component_reasons'])
    assert reasons=={'R01_AC1009_NN':'not_ascertained','R01_AC1009_UN':'structural_skip'}


def test_unit_conversion_coarsening_and_recency_rounding_flag(contract,synthetic):
    cohort,*_=prepare(contract,synthetic)
    rows=cohort.set_index('PERSONID')
    assert rows.loc['SYN_0001','last_cigarette_recency_days']==60.875
    assert rows.loc['SYN_0001','prior_regular_cigarettes_per_day']==40
    assert rows.loc['SYN_0002','age_band']==6 and rows.loc['SYN_0002','education_level']==5
    assert rows.loc['SYN_0009','recency_group']=='recent'
    assert rows.loc['SYN_0009','recency_group_rounding_sensitivity']=='excluded_rounded_boundary'


@pytest.mark.parametrize('side',[0,1])
def test_duplicate_ids_fail_before_join_without_disclosing_values(contract,synthetic,side):
    config,project,task,mapping=contract
    frames=[synthetic[0],synthetic[1]]
    frames[side]=pd.concat([frames[side],frames[side].iloc[[0]]],ignore_index=True)
    with pytest.raises(CohortError,match='duplicate PERSONID') as error:
        interval_cohort(*frames,1,2,task,mapping,config)
    assert 'SYN_' not in str(error.value)


def test_string_ids_preserve_leading_zeros_and_are_not_coerced(tmp_path,contract):
    config=contract[0]
    source=tmp_path/'synthetic.tsv'
    source.write_text('PERSONID\tCODE\n0001\t1\n1\t2\n')
    frame=read_wave(source,1,['PERSONID','CODE'],config)
    assert frame['PERSONID'].tolist()==['0001','1']
    validate_ids(frame,1,'PERSONID',config['invalid_identifiers'])
    for bad in [pd.DataFrame({'PERSONID':[1]}),pd.DataFrame({'PERSONID':[' ']})]:
        with pytest.raises(CohortError):validate_ids(bad,1,'PERSONID',config['invalid_identifiers'])


def test_followup_features_cannot_change_predictors_and_only_labels_are_projected(contract,synthetic):
    before=prepare(contract,synthetic)[0]
    left,right,expected=synthetic
    for column in right.columns:
        if column not in ['PERSONID','R02R_A_P30D_CIGS','R02R_A_CUR_ESTD_CIGS']:
            right[column]='999'
    after=prepare(contract,(left,right,expected))[0]
    pd.testing.assert_frame_equal(before,after)
    assert not any(column.startswith('R02_') for column in after)
    assert not any(column in after for column in ['CASEID','VARPSU','VARSTRAT'])


def test_future_source_mapping_and_nonadjacent_pair_rejected(contract,synthetic):
    config,project,task,mapping=contract
    bad=deepcopy(mapping)
    bad['fields'][0]['waves']['1']['source_wave']=2
    with pytest.raises(CohortError,match='future information'):
        needed_columns(1,task,bad,config)
    with pytest.raises(CohortError,match='adjacent scheduled'):
        interval_cohort(synthetic[0],synthetic[1],1,3,task,mapping,config)


def test_no_global_wave_intersection_and_last_wave_loads_labels_only(contract,synthetic):
    config,project,task,mapping=contract
    cohort,ledger,*_=prepare(contract,synthetic)
    # The pair is built without supplying Waves 3–8 at all.
    assert len(cohort)==3
    assert needed_columns(8,task,mapping,config)==['PERSONID','R08R_A_CUR_ESTD_CIGS','R08R_A_P30D_CIGS']


def test_parquet_round_trip_keeps_string_ids_nullable_features_and_labels(tmp_path,contract,synthetic):
    cohort,ledger,*_=prepare(contract,synthetic)
    for name,frame in [('cohort',cohort),('ledger',ledger)]:
        path=tmp_path/(name+'.parquet')
        frame.to_parquet(path,index=False,engine='pyarrow')
        pd.testing.assert_frame_equal(frame,pd.read_parquet(path,engine='pyarrow'),check_dtype=True)


def test_immutable_run_verification_rejects_changed_signature_and_artifact(tmp_path):
    config={'output_dir':'local','files':{'manifest':'run_manifest.json'}}
    (tmp_path/'local').mkdir()
    artifact=tmp_path/'local/value.txt';artifact.write_text('synthetic only')
    from path_project.documentation import fingerprint
    saved={'signature':'fixed','output_sha256':{'local/value.txt':fingerprint(artifact)}}
    (tmp_path/'local/run_manifest.json').write_text(json.dumps(saved))
    assert verify_completed_run(tmp_path,config,'fixed')==saved
    with pytest.raises(CohortError,match='signature differs'):verify_completed_run(tmp_path,config,'other')
    artifact.write_text('changed synthetic artifact')
    with pytest.raises(CohortError,match='missing/changed'):verify_completed_run(tmp_path,config,'fixed')


def test_raw_one_year_boundary_not_replaced_by_rounded_derived_duration(contract,synthetic):
    left,right,expected=synthetic
    left.loc[left['PERSONID']=='SYN_0001','R01_AC1009_NN']='1'
    left.loc[left['PERSONID']=='SYN_0001','R01_AC1009_UN']='3'
    left['R01R_A_DAYSQUIT_CIGS']='365.3'  # Deliberately unused, synthetic rounded field.
    cohort,*_=prepare(contract,(left,right,expected))
    row=cohort.set_index('PERSONID').loc['SYN_0001']
    assert row['last_cigarette_recency_days']==365.25
    assert row['recency_group']=='recent'
    assert row['recency_group_rounding_sensitivity']=='excluded_rounded_boundary'
