"""Synthetic tests of v2.2 observation rules, interval-censored fitting and safety."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from path_project.evaluation import BoundaryError
from path_project.study import exact_feature_shap, load_study, read_config
from path_project.study_training import choose_origin, split_participants
from path_project.survival import (PiecewiseHazardModel, censor_curves, horizon_metrics,
    horizon_status, Preprocessor)
from path_project.longitudinal import history_status, wave_clock, months_between

WAVES = {1, 2, 3, 4, 5, 6, 7}


def records(waves, statuses):
    return [{'wave': w, 'former': 1 if s == 2 else 2, 'p30': 2 if s == 2 else 1, 'current': s}
            for w, s in zip(waves, statuses)]


def test_origin_needs_only_one_followup_and_later_attendance_is_irrelevant():
    assert choose_origin(records([1], [2]), WAVES) is None
    assert choose_origin(records([1, 3], [2, 2]), WAVES) is None  # non-consecutive: no known interval
    h = choose_origin(records([1, 2], [2, 1]), WAVES)
    assert h['event'] == 1 and h['end_wave'] == 2 and h['last_clear_wave'] == 1
    # A return followed by dropout is included exactly as one followed by more waves.
    a = choose_origin(records([2, 3, 4, 5], [2, 2, 1, 2]), WAVES)
    b = choose_origin(records([2, 3, 4], [2, 2, 1]), WAVES)
    assert (a['starting_wave'], a['end_wave'], a['event']) == (b['starting_wave'], b['end_wave'], b['event']) == (2, 4, 1)
    assert a['last_clear_wave'] == 3


def test_unknown_status_censors_and_wave7_is_a_valid_baseline():
    h = choose_origin(records([1, 2, 3, 4], [2, 2, None, 1]), WAVES)
    assert h['event'] == 0 and h['end_wave'] == 2 and h['observation_end_reason'] == 'unknown_status'
    h = choose_origin(records([7, 8], [2, history_status(0, outcome_coded=True)]), WAVES)
    assert h['starting_wave'] == 7 and h['end_wave'] == 8 and h['event'] == 0
    assert choose_origin(records([8], [2]), WAVES) is None
    assert history_status(0, outcome_coded=True) == 2 and history_status(1, outcome_coded=True) == 1


def test_earlier_origin_without_followup_falls_through_to_later_origin():
    h = choose_origin(records([1, 4, 5], [2, 2, 2]), WAVES)
    assert h['starting_wave'] == 4


def test_clock_gaps_vary_so_intervals_matter():
    clock = wave_clock(read_config(ROOT))
    assert months_between(clock[5], clock[6]) > 24 > months_between(clock[2], clock[3]) > 10


def synthetic_interval(n=3000, seed=366):
    rng = np.random.default_rng(seed)
    x = rng.integers(0, 2, n).astype(float)
    t = 12*rng.exponential(1/(.12*np.exp(.7*x)))
    last = rng.choice([22., 34., 46., 58., 70.], n)
    grid = np.array([0., 10., 22., 34., 46., 58., 70.])
    left, right, event = np.zeros(n), last.copy(), np.zeros(n, int)
    for i in range(n):
        if t[i] <= last[i]:
            k = np.searchsorted(grid, t[i])
            left[i], right[i], event[i] = grid[k-1], grid[k], 1
    return pd.DataFrame({'PERSONID': [f'FICTIONAL_{i}' for i in range(n)], 'x': x, 'left_months': left,
                         'right_months': right, 'event': event, 'starting_wave': rng.integers(1, 4, n)})


def fitted(frame=None, penalty=1.):
    frame = synthetic_interval() if frame is None else frame
    return PiecewiseHazardModel(['x'], {'x': [0., 1.]}, [0, 12, 24, 36, 48], penalty).fit(frame), frame


def test_interval_censored_fit_recovers_effect_and_is_monotone():
    model, frame = fitted()
    pair = pd.DataFrame({'x': [0., 1.]})
    assert model.log_rate(pair.iloc[[1]])[0]-model.log_rate(pair.iloc[[0]])[0] == pytest.approx(.7, abs=.2)
    p = model.risk(pair, [0, 12, 36, 60])
    assert np.all(p[:, 0] == 0) and np.all(np.diff(p, axis=1) > 0) and np.all(p[1, 1:] > p[0, 1:])
    median = model.median_months(pair)
    assert np.all(median > 0) and median[1] < median[0]
    cond = model.conditional_median(pair, 60)
    np.testing.assert_allclose(model.risk(pair, [60])[:, 0]/2, [model.risk(pair.iloc[[i]], [c])[0, 0] for i, c in enumerate(cond)], rtol=1e-9)
    shift = model.calibrate(frame)
    assert abs(shift) < .05 and abs(model.likelihood_shift(frame)) < .01


def test_json_round_trip_is_exact_and_needs_no_pickle():
    model, frame = fitted()
    clone = PiecewiseHazardModel.from_dict(json.loads(json.dumps(model.to_dict())))
    np.testing.assert_array_equal(model.risk(frame, [12, 36]), clone.risk(frame, [12, 36]))


def test_inputs_are_validated():
    model, _ = fitted()
    with pytest.raises(BoundaryError):
        model.risk(pd.DataFrame({'x': [7.]}), [12])
    with pytest.raises(BoundaryError):
        model.preprocessor.transform(pd.DataFrame({'x': [1.], 'y': [1.]}))
    with pytest.raises(BoundaryError):
        model.risk(pd.DataFrame({'x': [1.]}), [-1])
    pre = Preprocessor(['q'], {'q': None})
    with pytest.raises(BoundaryError):
        pre.fit(pd.DataFrame({'q': [-1., 2.]}))


def test_split_is_disjoint_reproducible_and_keeps_both_classes():
    frame = synthetic_interval()
    a, b = split_participants(frame, 366), split_participants(frame, 366)
    pd.testing.assert_frame_equal(a, b)
    assert set(a['split']) == {'train', 'validation', 'calibration', 'test'}
    assert all(g['event'].nunique() == 2 for _, g in a.groupby('split'))


def test_horizon_status_separates_resolved_from_straddling_and_lost():
    frame = pd.DataFrame({'left_months': [0, 10, 40, 0, 0], 'right_months': [10, 22, 50, 30, 12],
                          'event': [1, 1, 1, 0, 0], 'starting_wave': 1})
    positive, negative, _, lost = horizon_status(frame, 18)
    assert positive.tolist() == [True, False, False, False, False]
    assert negative.tolist() == [False, False, True, True, False]
    assert lost.tolist() == [False, True, False, False, True]  # straddling interval; censored early
    pos_u, _, _, lost_u = horizon_status(frame, 18, straddle_lost=False)
    assert pos_u.tolist() == [True, True, False, False, False] and lost_u.tolist() == [False, False, False, False, True]


def test_metrics_report_observed_risk_bounds_that_bracket_prediction():
    model, frame = fitted()
    curves, upper = censor_curves(frame, 36), censor_curves(frame, 36, straddle_lost=False)
    m = horizon_metrics(frame, model.risk(frame, [36])[:, 0], 36, curves, curves_upper=upper)
    assert m['observed_risk_lower'] <= m['ipcw_observed_risk'] <= m['observed_risk_upper']
    assert m['predicted_within_observed_bounds'] and 0.6 < m['ipcw_roc_auc'] < .8


def test_exact_explanations_reconcile_with_synthetic_background():
    model, frame = fitted()
    background = frame[['x']].sample(8, random_state=1)
    reference, factors = exact_feature_shap(model, background, frame[['x']].iloc[[9]], 36)
    assert reference+sum(f['contribution'] for f in factors) == pytest.approx(model.risk(frame.iloc[[9]], [36])[0, 0])


def test_shipped_bundle_has_no_participant_rows_or_pickle_and_beats_baseline():
    bundle = load_study(ROOT)
    assert not list((ROOT/'artifacts/longitudinal_v2_2').glob('*.joblib'))
    results = bundle['results']
    assert 12 not in results['supported_horizons_months']
    assert bundle['config']['default_horizon_months'] in results['supported_horizons_months']
    for h in results['supported_horizons_months']:
        pair = results['metrics'][str(h)]
        assert pair['model']['ipcw_brier'] < pair['no_input_baseline']['ipcw_brier']
    assert results['test_mean_loglik']['model'] > results['test_mean_loglik']['no_input_baseline']
    assert abs(results['test_log_hazard_shift_needed']) < .05
    bg = bundle['background']
    assert len(bg) == bundle['config']['background_size'] and 'PERSONID' not in bg.columns
