"""Stage 5 tests use only invented participants; no model fits on real PATH."""
import json,sys
from pathlib import Path
from copy import deepcopy
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyClassifier
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.evaluation import (assign_people,assign_rows,select_keys,assert_batch,
    fit_training_pipeline,participant_weights,BoundaryError,validate_membership,create_splits)


@pytest.fixture
def fixture():
    config=json.loads((ROOT/'configs/evaluation.json').read_text())
    data=json.loads((ROOT/'tests/fixtures/synthetic_evaluation.json').read_text())
    assert data['synthetic']
    people=assign_people(data['identifiers'],config)
    keys=pd.DataFrame([(p,w,w+1) for p in data['identifiers'] for w in data['starting_waves']],columns=['PERSONID','starting_wave','followup_wave'])
    rows=assign_rows(keys,people,config)
    def batch(purpose='fit',fold=None):
        frame=select_keys(rows,config,purpose,fold)
        frame['synthetic_value']=range(len(frame))
        frame['outcome_p30d']=[n%2 for n in range(len(frame))]
        return frame
    return config,people,rows,batch


def test_assignment_is_order_invariant_and_ignores_outcomes(fixture):
    config,people,rows,batch=fixture
    pd.testing.assert_frame_equal(people,assign_people(list(reversed(people['PERSONID'].tolist())),config))
    reordered=assign_rows(rows[['PERSONID','starting_wave','followup_wave']].sample(frac=1,random_state=366),people,config)
    assert set(map(tuple,reordered.to_numpy()))==set(map(tuple,rows.to_numpy()))
    assert rows.groupby('PERSONID')['fold'].nunique().eq(1).all()
    assert rows.loc[rows['participant_role'].eq('heldout') & rows['starting_wave'].lt(7),'partition'].eq('heldout_excluded').all()
    assert rows.loc[rows['participant_role'].ne('heldout') & rows['starting_wave'].eq(7),'partition'].eq('development_later_excluded').all()


def test_group_folds_and_all_partitions_disjoint(fixture):
    config,people,rows,batch=fixture
    for fold in range(config['folds']):
        train=select_keys(rows,config,'fit',fold)
        valid=select_keys(rows,config,'validation',fold)
        assert not set(train['PERSONID'])&set(valid['PERSONID'])
    groups=[set(select_keys(rows,config,p)['PERSONID']) for p in ['fit','calibration','threshold']]
    held=set(people.loc[people['participant_role'].eq('heldout'),'PERSONID'])
    assert all(not g&held for g in groups)
    assert all(not groups[a]&groups[b] for a in range(3) for b in range(a+1,3))


@pytest.mark.parametrize('purpose',['test','heldout_excluded','development_later_excluded','anything'])
def test_no_development_test_accessor(fixture,purpose):
    config,people,rows,batch=fixture
    with pytest.raises(BoundaryError):select_keys(rows,config,purpose)


@pytest.mark.parametrize('forbidden',['test','heldout_excluded','calibration','threshold','development_later_excluded'])
def test_forbidden_participants_and_intervals_never_fit(fixture,forbidden):
    config,people,rows,batch=fixture
    bad=rows.loc[rows['partition'].eq(forbidden),['PERSONID','starting_wave','followup_wave']].iloc[:1].copy()
    assert len(bad)==1
    bad['synthetic_value']=100000
    bad['outcome_p30d']=1
    frame=pd.concat([batch(),bad],ignore_index=True)
    with pytest.raises(BoundaryError,match='authorized partition'):
        fit_training_pipeline(Pipeline([('scale',StandardScaler()),('model',DummyClassifier())]),frame,rows,config,['synthetic_value'])


def test_pipeline_preprocessing_is_fit_on_training_fold_only(fixture):
    config,people,rows,batch=fixture
    frame=batch('fit',0)
    pipeline=Pipeline([('scale',StandardScaler()),('model',DummyClassifier())])
    fitted=fit_training_pipeline(pipeline,frame,rows,config,['synthetic_value'],0)
    assert not hasattr(pipeline['scale'],'mean_')  # Original remains unfitted.
    assert fitted['scale'].n_samples_seen_==len(frame)
    assert fitted['scale'].mean_[0]==frame['synthetic_value'].mean()
    valid=batch('validation',0)
    with pytest.raises(BoundaryError):fit_training_pipeline(pipeline,valid,rows,config,['synthetic_value'],0)


@pytest.mark.parametrize('forbidden',['PERSONID','followup_wave','outcome_current_established','CASEID'])
def test_feature_exclusions(fixture,forbidden):
    config,people,rows,batch=fixture
    frame=batch()
    if forbidden not in frame:frame[forbidden]=1
    with pytest.raises(BoundaryError):assert_batch(frame,rows,config,['synthetic_value',forbidden],'fit')


def test_future_outcomes_and_duplicate_batches_rejected(fixture):
    config,people,rows,batch=fixture
    frame=batch();frame['followup_wave']=8
    with pytest.raises(BoundaryError):assert_batch(frame,rows,config,['synthetic_value'],'fit')
    frame=batch();frame['outcome_p30d']=None
    with pytest.raises(BoundaryError):assert_batch(frame,rows,config,['synthetic_value'],'fit')
    frame=pd.concat([batch(),batch().iloc[:1]],ignore_index=True)
    with pytest.raises(BoundaryError):assert_batch(frame,rows,config,['synthetic_value'],'fit')


def test_participant_metric_weights_sum_to_one(fixture):
    frame=fixture[3]()
    weighted=frame[['PERSONID']].assign(weight=participant_weights(frame))
    assert weighted.groupby('PERSONID')['weight'].sum().eq(1).all()


def test_changed_assignment_and_temporal_membership_rejected(fixture):
    config,people,rows,batch=fixture
    bad=people.copy();bad.loc[0,'fold']=99
    with pytest.raises(BoundaryError):validate_membership(rows,bad,config)
    bad=rows.copy();mask=bad['partition'].eq('tuning');bad.loc[mask,'starting_wave']=7
    with pytest.raises(BoundaryError):validate_membership(bad,people,config)


def test_public_feature_allowlist_rejects_any_future_or_unknown_column():
    from path_project.training_boundaries import assert_candidate_features
    allowlist=['age_band','quit_history']
    assert_candidate_features(['age_band'],allowlist)
    for names in [['R08_FUTURE_ANSWER'],['outcome_p30d'],['PERSONID'],['age_band','age_band'],[]]:
        with pytest.raises(BoundaryError):assert_candidate_features(names,allowlist)


def test_public_fitter_loads_own_authorized_batch_and_rejects_bad_features(fixture,monkeypatch,tmp_path):
    import path_project.training_boundaries as boundary
    from path_project.documentation import fingerprint
    config,people,rows,batch=fixture
    (tmp_path/'mapping.json').write_text(json.dumps({'candidate_predictor_names':['synthetic_value']}))
    (tmp_path/'local').mkdir()
    (tmp_path/'local/manifest.json').write_text(json.dumps({'provenance':{'configuration_sha256':{'mapping.json':fingerprint(tmp_path/'mapping.json')}}}))
    cc={'feature_mapping':'mapping.json','output_dir':'local','files':{'manifest':'manifest.json'}}
    monkeypatch.setattr(boundary,'load_locked',lambda root:(config,cc,{},people,rows))
    calls=[]
    def loader(root,purpose,fold):
        calls.append((purpose,fold));return batch(purpose,fold)
    monkeypatch.setattr(boundary,'load_development',loader)
    pipeline=Pipeline([('scale',StandardScaler()),('model',DummyClassifier())])
    with pytest.raises(BoundaryError):boundary.fit_development_pipeline(tmp_path,pipeline,predictors=['R08_FUTURE_ANSWER'])
    assert calls==[]
    boundary.fit_development_pipeline(tmp_path,pipeline,fold=0)
    assert calls==[('fit',0)]
