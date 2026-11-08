"""Synthetic tests of the new study's observation, censoring and inference rules."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from path_project.longitudinal import (ApproximateReturnModel, choose_history,
    consecutive_runs, censor_curve, horizon_metrics, exact_feature_shap,
    split_participants, wave_clock, months_between, read_config, history_status)


def records(waves, statuses):
    return [{'wave': w, 'former': 1 if s == 2 else 2, 'p30': 2 if s == 2 else 1,
             'current': s} for w, s in zip(waves, statuses)]


def test_at_least_three_consecutive_attended_and_earliest_eligible_origin():
    assert consecutive_runs([1, 2, 4, 5, 6, 8]) == [[1, 2], [4, 5, 6], [8]]
    assert choose_history(records([1, 3, 5], [2, 2, 1])) is None
    h = choose_history(records([1, 2, 4, 5, 6], [2, 2, 2, 2, 1]))
    assert h['starting_wave'] == 4 and h['end_wave'] == 6 and h['event'] == 1
    assert h['consecutive_waves'] == 3
    # First return may be at the second interview; don't require survival to third.
    h = choose_history(records([1, 2, 3], [2, 1, 2]))
    assert h['end_wave'] == 2 and h['event'] == 1


def test_unknown_stops_observation_and_no_return_is_censored():
    h = choose_history(records([1, 2, 3, 4], [2, 2, None, 1]))
    assert h['end_wave'] == 2 and h['event'] == 0
    assert h['observation_end_reason'] == 'unknown_status'
    h = choose_history(records([1, 2, 3], [2, 2, 2]))
    assert h['event'] == 0 and h['end_wave'] == 3


def test_outcome_mapping_zero_is_nonsmoking_not_unknown():
    assert history_status(0, outcome_coded=True) == 2
    assert history_status(1, outcome_coded=True) == 1
    assert history_status(2) == 2
    assert history_status(pd.NA, outcome_coded=True) is None
    h = choose_history(records([6, 7, 8], [2, 2, history_status(0, outcome_coded=True)]))
    assert h['end_wave'] == 8 and h['event'] == 0


def test_future_status_does_not_change_origin_or_predictor_data():
    a = choose_history(records([2, 3, 4, 5], [2, 2, 1, 2]))
    b = choose_history(records([2, 3, 4, 5], [2, 2, 2, 1]))
    assert a['starting_wave'] == b['starting_wave'] == 2
    assert a['end_wave'] != b['end_wave']


def test_clock_is_explicit_midpoint_and_variable_gap():
    clock = wave_clock(read_config(ROOT))
    assert 10 < months_between(clock[2], clock[3]) < 13
    assert months_between(clock[5], clock[6]) > 24


def synthetic_survival(n=700):
    rng = np.random.default_rng(366)
    x = rng.integers(0, 2, n)
    event_time = 12*(-np.log(rng.uniform(size=n))/(.12*np.exp(.7*x)))**(1/1.3)
    censor_time = rng.uniform(12, 72, n)
    return pd.DataFrame({'PERSONID': [f'FICTIONAL_{i}' for i in range(n)],
                         'x': x.astype(float), 'months': np.minimum(event_time, censor_time),
                         'event': (event_time <= censor_time).astype(int)})


MAPPING = {'fields': [{'name': 'x', 'output_labels': {'0': 'No', '1': 'Yes'}}]}


def test_participant_splits_are_disjoint_reproducible_and_preserve_both_classes():
    frame = synthetic_survival()
    a = split_participants(frame, 366)
    b = split_participants(frame, 366)
    pd.testing.assert_frame_equal(a, b)
    assert set(a['split']) == {'train', 'validation', 'calibration', 'test'}
    assert not a['PERSONID'].duplicated().any()
    assert all(part['event'].nunique() == 2 for _, part in a.groupby('split'))


def test_censored_fit_monotonic_probability_and_conditional_timing():
    frame = synthetic_survival()
    model = ApproximateReturnModel(['x'], MAPPING).fit(frame)
    p = model.risk(pd.DataFrame({'x': [0., 1.]}), [0, 12, 18, 36, 60])
    assert np.all(p[:, 0] == 0)
    assert np.all(np.diff(p, axis=1) >= 0)
    assert np.all((p >= 0) & (p <= 1))
    assert p[1, -1] > p[0, -1]
    assert .8 < model.shape < 1.8
    med = model.conditional_median(frame.head(), 60)
    np.testing.assert_allclose(model.risk(frame.head(), [60])[:, 0]/2,
                               np.array([model.risk(frame.iloc[[i]], [m])[0, 0] for i, m in enumerate(med)]))
    assert np.all((med > 0) & (med < 60))
    # No-input censored baseline must also fit, rather than using raw event prevalence.
    baseline = ApproximateReturnModel([], MAPPING).fit(frame)
    assert baseline.risk(frame.head(), [36]).shape == (5, 1)


def test_calibration_uses_censored_exposure_and_exact_explanations_reconcile():
    frame = synthetic_survival()
    model = ApproximateReturnModel(['x'], MAPPING).fit(frame)
    model.calibrate(frame)
    expected = np.sum(np.exp(model.log_rate(frame))*(frame['months'].to_numpy()/12)**model.shape)
    assert expected == pytest.approx(frame['event'].sum())
    reference, factors = exact_feature_shap(model, frame[['x']].head(8), frame[['x']].iloc[[9]], 36)
    assert reference+sum(f['contribution'] for f in factors) == pytest.approx(model.risk(frame.iloc[[9]], [36])[0, 0])


def test_ipcw_excludes_early_censoring_without_labeling_negative():
    frame = pd.DataFrame({'months': [10., 12., 30., 40.], 'event': [1, 0, 1, 0]})
    m = horizon_metrics(frame, np.array([.5]*4), 18, censor_curve(frame))
    assert m['known_outcomes'] == 3
    assert m['censored_before_horizon'] == 1
    assert m['events_by_horizon'] == 1
    assert m['ipcw_observed_risk'] == pytest.approx(.25)
