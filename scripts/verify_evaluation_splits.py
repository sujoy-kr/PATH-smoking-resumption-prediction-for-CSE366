"""Read-only stage 5 verification; no test features/outcomes or model fitting."""
from pathlib import Path
import json,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.evaluation import load_locked,select_keys,BoundaryError

if __name__=='__main__':
    config,cc,manifest,people,rows=load_locked(ROOT)
    keys=['PERSONID','starting_wave','followup_wave']
    original=pd.read_parquet(ROOT/cc['output_dir']/cc['files']['cohort'],columns=keys)
    compared=original.merge(rows[keys],on=keys,how='outer',indicator=True,validate='one_to_one')
    if not compared['_merge'].eq('both').all():raise BoundaryError('Locked membership does not cover the original labeled keys exactly.')
    report=json.loads((ROOT/config['report_file']).read_text())
    assert not report['test_outcomes_read'] and not report['test_features_read']
    for fold in range(config['folds']):
        train=select_keys(rows,config,'fit',fold);valid=select_keys(rows,config,'validation',fold)
        if set(train['PERSONID'])&set(valid['PERSONID']):raise BoundaryError('Fold participant overlap.')
    print(f"Verified immutable split: {len(rows)} labeled keys; test={report['test_records']} later-wave people/records; five participant-disjoint development folds; test features/outcomes unopened.")
