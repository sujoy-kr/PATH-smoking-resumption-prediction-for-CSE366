"""Verify the new model; optionally reconstruct its cohort without fitting."""
from pathlib import Path
import argparse
import json
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from path_project.cohort import json_write
from path_project.documentation import fingerprint
from path_project.longitudinal import (read_config, load_study, build_cohort,
                                       split_participants)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rebuild-cohort', action='store_true')
    args = parser.parse_args()
    config = read_config(ROOT)
    report = ROOT/config['report_dir']
    manifest = json.loads((report/'manifest.json').read_text())
    bundle = load_study(ROOT)
    for name, digest in manifest['output_sha256'].items():
        assert fingerprint(ROOT/name) == digest, 'Output fingerprint mismatch'
    project = json.loads((ROOT/'configs/project.json').read_text())
    for wave in project['waves']:
        assert fingerprint(ROOT/wave['data']) == manifest['source_data_sha256'][str(wave['wave'])], 'Raw source fingerprint mismatch'
    frame = pd.read_parquet(ROOT/config['data_dir']/'participants.parquet')
    assert not frame['PERSONID'].duplicated().any()
    assert frame['consecutive_waves'].between(3, 8).all()
    assert frame['event'].isin([0, 1]).all()
    assert frame['months'].gt(0).all()
    assert frame['end_wave'].gt(frame['starting_wave']).all()
    assert frame['end_wave'].lt(frame['starting_wave']+frame['consecutive_waves']).all()
    assert set(frame['split']) == {'train', 'validation', 'calibration', 'test'}
    assert len(frame) == bundle['summary']['people']
    assert int(frame['event'].sum()) == bundle['summary']['observed_returns']
    pd.testing.assert_series_equal(split_participants(frame.drop(columns='split'), config['seed'])['split'], frame['split'])
    if args.rebuild_cohort:
        rebuilt, _ = build_cohort(ROOT, config)
        pd.testing.assert_frame_equal(rebuilt, frame.drop(columns='split'))
    result = {'version': config['version'], 'source_and_output_hashes_valid': True,
              'unique_people_and_disjoint_splits': True, 'consecutive_run_bounds_valid': True,
              'aggregate_counts_reconciled': True, 'split_assignment_reproduced': True,
              'cohort_rebuilt_exactly': args.rebuild_cohort,
              'model_refitted': False, 'test_predictions_recomputed': False}
    json_write(report/'verification.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
