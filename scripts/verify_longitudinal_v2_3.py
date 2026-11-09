"""Verify the v2.2 study outputs; optionally rebuild the cohort from raw PATH files."""
from pathlib import Path
import argparse
import json
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from path_project.cohort import json_write
from path_project.documentation import fingerprint
from path_project.study import CONFIG, load_study, read_config, sha256


def bundle_summary(bundle):
    return {name: pop['summary'] for name, pop in bundle['populations'].items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rebuild-cohort', action='store_true')
    args = parser.parse_args()
    from path_project.study_training import build_cohorts, split_participants
    config = read_config(ROOT)
    report = ROOT/config['report_dir']
    manifest = json.loads((report/'manifest.json').read_text())
    bundle = load_study(ROOT)
    assert sha256(ROOT/config['data_dir']/'participants.parquet') == manifest['cohort_sha256'], 'Cohort fingerprint mismatch'
    project = json.loads((ROOT/'configs/project.json').read_text())
    for wave in project['waves']:
        assert fingerprint(ROOT/wave['data']) == manifest['source_data_sha256'][str(wave['wave'])], 'Raw source fingerprint mismatch'
    frame = pd.read_parquet(ROOT/config['data_dir']/'participants.parquet')
    for name, summary in bundle_summary(bundle).items():
        part = frame.loc[frame['population'].eq(name)]
        assert not part['PERSONID'].duplicated().any()
        assert part['event'].isin([0, 1]).all() and part['right_months'].gt(0).all()
        ev = part['event'].eq(1)
        assert (part.loc[ev, 'left_months'] < part.loc[ev, 'right_months']).all()
        assert part.loc[~ev, 'left_months'].eq(0).all()
        assert part['end_wave'].gt(part['starting_wave']).all() and part['starting_wave'].between(1, 7).all()
        assert set(part['split']) == {'train', 'validation', 'calibration', 'test'}
        assert len(part) == summary['people'] and int(part['event'].sum()) == summary['events']
        pd.testing.assert_series_equal(split_participants(part.drop(columns=['split', 'population']), config['seed'])['split'], part['split'])
    if args.rebuild_cohort:
        rebuilt, _ = build_cohorts(ROOT, config)
        for name, cohort in rebuilt.items():
            part = frame.loc[frame['population'].eq(name)].drop(columns=['split', 'population']).reset_index(drop=True)
            pd.testing.assert_frame_equal(cohort, part[cohort.columns])
    result = {'version': config['version'], 'hashes_valid': True, 'unique_people_and_disjoint_splits': True,
              'interval_bounds_valid': True, 'split_assignment_reproduced': True,
              'cohort_rebuilt_exactly': args.rebuild_cohort, 'model_refitted': False, 'test_predictions_recomputed': False}
    json_write(report/'verification.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
