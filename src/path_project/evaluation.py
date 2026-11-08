"""Deterministic participant partitions and executable fitting boundaries.

No test labels/features are loaded by split creation or development accessors.
"""
import hashlib
import json
from pathlib import Path
import sys
from importlib.metadata import version
import pandas as pd
from path_project.cohort import CohortError, load_contract, verify_completed_run, json_write
from path_project.documentation import fingerprint


class BoundaryError(CohortError):
    """A sanitized evaluation protocol violation."""


def bucket(person, namespace, config, modulus):
    if not isinstance(person, str) or not person:
        raise BoundaryError('Participant keys must be nonempty strings.')
    token=f"{namespace}|{config['seed']}|{person}".encode('utf-8')
    return int.from_bytes(hashlib.sha256(token).digest()[:8], 'big') % modulus


def assign_people(identifiers, config):
    rows=[]
    for person in sorted(set(identifiers)):
        heldout=bucket(person,config['test_namespace'],config,config['bucket_count']) < config['test_buckets']
        value=bucket(person,config['development_namespace'],config,config['bucket_count'])
        role='heldout' if heldout else next(role for role,limit in config['development_role_cutoffs'].items() if value<limit)
        fold=bucket(person,config['fold_namespace'],config,config['folds']) if role=='tuning' else -1
        rows.append((person,role,fold))
    return pd.DataFrame(rows,columns=['PERSONID','participant_role','fold']).astype({'PERSONID':'string','participant_role':'string','fold':'int8'})


def assign_rows(keys, people, config):
    if people['PERSONID'].duplicated().any() or keys.duplicated(['PERSONID','starting_wave','followup_wave']).any():
        raise BoundaryError('Duplicate membership keys; no values emitted.')
    rows=keys.merge(people,on='PERSONID',how='left',validate='many_to_one')
    if rows['participant_role'].isna().any():
        raise BoundaryError('A cohort participant lacks assignment.')
    roles=[]
    for start,end,role in zip(rows['starting_wave'],rows['followup_wave'],rows['participant_role']):
        if end!=start+1:raise BoundaryError('Non-adjacent interval in split input.')
        if role=='heldout':
            assigned='test' if start==config['test_start_wave'] and end==config['test_followup_wave'] else 'heldout_excluded'
        else:
            assigned=role if start<=config['development_max_start_wave'] else 'development_later_excluded'
        roles.append(assigned)
    rows['partition']=pd.array(roles,dtype='string')
    validate_membership(rows,people,config)
    return rows


def validate_membership(rows, people, config):
    expected=assign_people(people['PERSONID'],config)
    actual=people.sort_values('PERSONID').reset_index(drop=True)
    try:pd.testing.assert_frame_equal(actual,expected)
    except AssertionError:raise BoundaryError('Participant assignment differs from the fixed hash rule; values suppressed.') from None
    if rows.duplicated(['PERSONID','starting_wave','followup_wave']).any():raise BoundaryError('Duplicate interval membership.')
    development=rows['partition'].isin(['tuning','calibration','threshold'])
    if rows.loc[development,'starting_wave'].gt(config['development_max_start_wave']).any():raise BoundaryError('Future interval entered development.')
    if rows.loc[development,'participant_role'].eq('heldout').any():raise BoundaryError('Held-out participant entered development.')
    test=rows['partition'].eq('test')
    if not (rows.loc[test,'participant_role'].eq('heldout') & rows.loc[test,'starting_wave'].eq(config['test_start_wave']) & rows.loc[test,'followup_wave'].eq(config['test_followup_wave'])).all():raise BoundaryError('Test temporal or participant restriction failed.')
    groups=[set(rows.loc[rows['partition'].eq(role),'PERSONID']) for role in ['tuning','calibration','threshold','test']]
    if any(groups[a]&groups[b] for a in range(4) for b in range(a+1,4)):raise BoundaryError('Participant overlap across partitions.')
    for fold in range(config['folds']):
        tune=rows.loc[rows['partition'].eq('tuning')]
        if set(tune.loc[tune['fold'].eq(fold),'PERSONID']) & set(tune.loc[tune['fold'].ne(fold),'PERSONID']):raise BoundaryError('Participant crosses fold boundary.')


def select_keys(rows, config, purpose, fold=None):
    if purpose not in ['fit','validation','calibration','threshold']:
        raise BoundaryError('No test or excluded-data accessor is available during development.')
    role='tuning' if purpose in ['fit','validation'] else purpose
    mask=rows['partition'].eq(role)
    if purpose=='validation' and fold is None:raise BoundaryError('Validation requires a development fold.')
    if fold is not None:
        if purpose not in ['fit','validation'] or fold not in range(config['folds']):raise BoundaryError('Invalid fold or purpose.')
        mask &= rows['fold'].eq(fold) if purpose=='validation' else rows['fold'].ne(fold)
    chosen=rows.loc[mask,['PERSONID','starting_wave','followup_wave']].copy()
    if chosen.empty:raise BoundaryError('Requested development partition is empty.')
    if chosen['starting_wave'].gt(config['development_max_start_wave']).any():raise BoundaryError('Future outcome cannot enter development.')
    return chosen


def assert_batch(frame, rows, config, predictors, purpose, fold=None):
    keys=['PERSONID','starting_wave','followup_wave']
    allowed=select_keys(rows,config,purpose,fold)
    if frame.duplicated(keys).any():raise BoundaryError('Duplicate records in development batch.')
    check=frame[keys].merge(allowed,on=keys,how='outer',indicator=True,validate='one_to_one')
    if not check['_merge'].eq('both').all():raise BoundaryError('Batch is not exactly the authorized partition; no values emitted.')
    if set(frame.columns)!=set(keys+predictors+['outcome_p30d']):raise BoundaryError('Batch has missing or forbidden feature columns.')
    if set(predictors)&set(keys+['outcome_p30d','outcome_current_established','CASEID','VARPSU','VARSTRAT']):raise BoundaryError('Identifiers, outcomes or administrative fields cannot be predictors.')
    if not frame['outcome_p30d'].isin([0,1]).all():raise BoundaryError('Development labels must be observed binary values.')


def fit_training_pipeline(estimator, frame, rows, config, predictors, fold=None):
    """Fit the entire caller-supplied sklearn Pipeline on authorized tuning rows.

    Never prefit an imputer/selector/resampler outside this function. Calibration
    and threshold data have separate score-only accessors, not base-model fitting.
    """
    assert_batch(frame,rows,config,predictors,'fit',fold)
    from sklearn.pipeline import Pipeline
    if not isinstance(estimator,Pipeline):raise BoundaryError('Supply an unfitted sklearn Pipeline including preprocessing.')
    from sklearn.base import clone
    fitted=clone(estimator)
    fitted.fit(frame[predictors],frame['outcome_p30d'])
    return fitted


def participant_weights(keys):
    """Each participant contributes total weight one in a repeated-row metric."""
    counts=keys.groupby('PERSONID')['PERSONID'].transform('size')
    return 1.0/counts


def protocol_signature(root, config, cohort_manifest):
    paths=['configs/evaluation.json',*config['code_inputs']]
    parts={'cohort_signature':cohort_manifest['signature'],'cohort_output_sha256':cohort_manifest['output_sha256'],
           'files':{name:fingerprint(root/name) for name in paths},
           'python':sys.version,'versions':{name:version(name) for name in ['pandas','pyarrow','scikit-learn']}}
    return hashlib.sha256(json.dumps(parts,sort_keys=True).encode()).hexdigest(),parts


def load_locked(root):
    root=Path(root);config=json.loads((root/'configs/evaluation.json').read_text())
    cohort_config,_,_,_=load_contract(root)
    cohort_manifest=verify_completed_run(root,cohort_config)
    signature,_=protocol_signature(root,config,cohort_manifest)
    output=root/config['output_dir'];path=output/'manifest.json'
    if not path.is_file():raise BoundaryError('Split lock missing/incomplete; preserve existing files and investigate.')
    manifest=json.loads(path.read_text())
    if manifest['signature']!=signature:raise BoundaryError('Locked protocol signature changed; no split overwritten.')
    for name,digest in manifest['output_sha256'].items():
        if not (root/name).is_file() or fingerprint(root/name)!=digest:raise BoundaryError('Locked split/report file changed or missing; no overwrite allowed.')
    people=pd.read_parquet(output/'participants.parquet');rows=pd.read_parquet(output/'records.parquet')
    validate_membership(rows,people,config)
    return config,cohort_config,manifest,people,rows


def load_development(root, purpose, fold=None):
    """Projection and Parquet filters exclude test participants and test waves."""
    config,cohort_config,manifest,people,rows=load_locked(root)
    keys=select_keys(rows,config,purpose,fold)
    mapping=json.loads((Path(root)/cohort_config['feature_mapping']).read_text())
    predictors=mapping['candidate_predictor_names']
    columns=['PERSONID','starting_wave','followup_wave',*predictors,'outcome_p30d']
    # Predicate pushdown never requests any held-out participant's feature/label.
    frame=pd.read_parquet(Path(root)/cohort_config['output_dir']/cohort_config['files']['cohort'],columns=columns,
                          filters=[('PERSONID','in',keys['PERSONID'].unique().tolist()),('starting_wave','<=',config['development_max_start_wave'])])
    assert_batch(frame,rows,config,predictors,purpose,fold)
    return frame


def create_splits(root):
    root=Path(root);config=json.loads((root/'configs/evaluation.json').read_text())
    cohort_config,_,_,_=load_contract(root)
    cohort_manifest=verify_completed_run(root,cohort_config)
    signature,provenance=protocol_signature(root,config,cohort_manifest)
    output=root/config['output_dir'];report=root/config['report_file']
    if output.exists() or report.exists():
        locked=load_locked(root)
        return 'reused_verified_lock',json.loads(report.read_text())
    ledger_path=root/cohort_config['output_dir']/cohort_config['files']['ledger']
    cohort_path=root/cohort_config['output_dir']/cohort_config['files']['cohort']
    keys=['PERSONID','starting_wave','followup_wave']
    # Assignment is based on keys only; no test or development labels inspected.
    identifiers=pd.read_parquet(ledger_path,columns=['PERSONID'])['PERSONID']
    people=assign_people(identifiers,config)
    rows=assign_rows(pd.read_parquet(cohort_path,columns=keys),people,config)
    test_count=int(rows['partition'].eq('test').sum())
    if test_count<config['minimum_test_records']:raise BoundaryError('Fixed test has insufficient records; document an alternative protocol before modeling, without searching test labels.')
    dev_people=people.loc[people['participant_role'].ne('heldout'),'PERSONID'].tolist()
    dev=pd.read_parquet(cohort_path,columns=keys+['outcome_p30d'],filters=[('PERSONID','in',dev_people),('starting_wave','<=',config['development_max_start_wave'])])
    dev=dev.merge(rows[keys+['partition','fold']],on=keys,validate='one_to_one')
    summaries=[]
    for role in ['tuning','calibration','threshold']:
        item=dev.loc[dev['partition'].eq(role)]
        positives=int(item['outcome_p30d'].sum())
        summaries.append({'partition':role,'records':len(item),'people':int(item['PERSONID'].nunique()),'positive':positives,'negative':len(item)-positives,'prevalence':positives/len(item) if len(item) else None})
    fold_counts=[]
    for fold in range(config['folds']):
        item=dev.loc[dev['partition'].eq('tuning')&dev['fold'].eq(fold)]
        positives=int(item['outcome_p30d'].sum());negative=len(item)-positives
        if positives<config['minimum_fold_positives'] or negative<config['minimum_fold_negatives']:raise BoundaryError('Fixed development fold lacks configured case counts; no split search performed.')
        fold_counts.append({'validation_fold':fold,'records':len(item),'people':int(item['PERSONID'].nunique()),'positive':positives,'negative':negative})
    for role in ['calibration','threshold']:
        item=next(s for s in summaries if s['partition']==role)
        if item['positive']<config[f'minimum_{role}_positives'] or item['negative']<config['minimum_fold_negatives']:raise BoundaryError('Calibration/threshold partition lacks configured cases; stop before modeling.')
    aggregate={'protocol':config['run_name'],'development':summaries,'development_folds':fold_counts,
               'test_records':test_count,'test_people':int(rows.loc[rows['partition'].eq('test'),'PERSONID'].nunique()),
               'test_outcomes_read':False,'test_features_read':False,
               'record_partition_counts':{str(k):int(v) for k,v in rows['partition'].value_counts().items()},
               'participant_role_counts':{str(k):int(v) for k,v in people['participant_role'].value_counts().items()},
               'minimum_case_checks_passed':True,'participant_and_temporal_assertions_passed':True,
               'no_model_fit_or_final_evaluation':True}
    # Exclusive directory creation: incomplete builds are never silently replaced.
    output.mkdir(parents=True,exist_ok=False)
    people.to_parquet(output/'participants.parquet',index=False)
    rows.to_parquet(output/'records.parquet',index=False)
    json_write(report,aggregate)
    files=[output/'participants.parquet',output/'records.parquet',report]
    manifest={'signature':signature,'provenance':provenance,'output_sha256':{str(p.relative_to(root)):fingerprint(p) for p in files},'policy':'Immutable; fail on changes; never reseed/search based on test outcomes.'}
    json_write(output/'manifest.json',manifest)
    load_locked(root)
    return 'created_immutable_lock',aggregate
