"""Route any adult answer set to the matching population model, or explain why not.

Three separately fitted populations (see docs/longitudinal_v2_3.md):
  former  - quit smoking (any time since the last cigarette): chance of returning
  current - smoke every day / some days: chance of stopping
  never   - have not smoked 100 cigarettes: chance of becoming a regular smoker
People under 18 are not covered (the adult PATH files contain no minors). A
result is withheld only when the answers are too sparse, contradict each other,
or cannot be routed; it is never forced through a model fitted on someone else.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from path_project.evaluation import BoundaryError
from path_project.inputs import encode_answers, load_inputs
from path_project.study import exact_feature_shap

UNKNOWN = ("don't know", 'dont know', 'prefer not')


def _unknown(value):
    return value is None or str(value).lower().startswith(UNKNOWN)


def suppressed(reason, provided=0, expected=0):
    return {'status': 'suppressed', 'estimate_mode': 'suppressed', 'reason': reason,
            'provided': provided, 'expected': expected}


def route(eligibility):
    """Return (population, unconfirmed_profile) or (None, reason)."""
    age, hundred, now, _ = eligibility
    if age == 'No':
        return None, 'This tool is built on adult (18+) PATH Study data, so it cannot estimate for people under 18.'
    if hundred == 'No':
        return 'never', age is None or _unknown(age)
    if _unknown(hundred) or _unknown(now):
        return None, ('Please answer “Have you smoked at least 100 cigarettes in your life?” and “Do you now smoke…?” '
                      'with a definite answer, so the model fitted for your situation can be chosen.')
    if now in ('Every day', 'Some days'):
        return 'current', _unknown(age)
    return 'former', _unknown(age)


def assess_available(root, bundle, answers, eligibility):
    spec = json.loads((Path(root)/'configs/app_questions.json').read_text())
    gates = spec['eligibility_questions']
    if len(eligibility) != len(gates):
        raise BoundaryError('Profile context has an unexpected shape.')
    for value, gate in zip(eligibility, gates):
        if value is not None and value not in gate['options']:
            raise BoundaryError('Unknown profile response.')
    if set(answers)-set(load_inputs(root)):
        raise BoundaryError('Only trained questionnaire inputs are accepted.')
    population, flag = route(eligibility)
    if population is None:
        return suppressed(flag)
    pop = bundle['populations'][population]
    model, config, result, label = pop['model'], bundle['config'], pop['results'], pop['spec']
    features = model.features
    usable = {f: v for f, v in answers.items() if f in features}
    recency = usable.get('last_cigarette_recency_days')
    if population == 'former' and isinstance(recency, dict):
        try:
            days = float(recency['number'])*{'1': 1., '2': 365.25/12, '3': 365.25}[str(recency['unit'])]
        except (KeyError, ValueError, TypeError):
            days = float('nan')
        past30 = eligibility[3]
        if math.isfinite(days) and ((past30 == 'Yes' and days > 30.5) or (past30 == 'No' and days <= 30.5)):
            return suppressed('Your answers conflict: the past-30-day smoking answer and the time since your last cigarette do not match. Please correct one of them.')
    values, reasons = encode_answers(root, usable, features)
    supplied = sum(reasons[f] == 'observed' for f in features)
    required = math.ceil(len(features)*config['minimum_answers_fraction'])
    needs_recency = 'last_cigarette_recency_days' in features
    if supplied < required or (needs_recency and reasons['last_cigarette_recency_days'] != 'observed'):
        extra = 'give the time since your last cigarette and ' if needs_recency else ''
        return suppressed(f'Please answer the questions above: {extra}at least {required} of the {len(features)} answers. With fewer, a probability would be unreliable. “Not sure” counts as unanswered.', supplied, len(features))
    missing = [f for f in features if reasons[f] != 'observed']
    row = pd.DataFrame([{f: values[f] for f in features}], dtype=float)
    horizons = result['supported_horizons_months']
    horizon = config['default_horizon_months']
    curve = model.risk(row, horizons)[0]
    p = float(model.risk(row, [horizon])[0, 0])
    low, high = result['risk_category_cuts']
    category = 'Lower' if p <= low else 'Moderate' if p <= high else 'Higher'
    maximum = max(horizons)
    median = float(model.median_months(row)[0]) if curve[-1] >= .5 else None
    base, factors = exact_feature_shap(model, pop['background'], row, horizon, result['selected_groups'])
    low_ci, high_ci = model.risk_interval(row, horizons, config['prediction_interval_level'])
    p_low, p_high = float(model.risk_interval(row, [horizon], config['prediction_interval_level'])[0][0, 0]), float(model.risk_interval(row, [horizon], config['prediction_interval_level'])[1][0, 0])
    unknown_context = flag or (population == 'former' and _unknown(eligibility[3]))
    mode = 'profile_unconfirmed' if unknown_context else 'assessment'
    support = {'assessment': 'Matches the study population', 'profile_unconfirmed': 'Population assumed (some context answers unknown)'}[mode]
    metric = result['metrics'][str(horizon)]['model']
    evidence = {}
    for h in horizons:
        pair = result['metrics'][str(h)]
        m, b = pair['model'], pair['no_input_baseline']
        evidence[str(h)] = {'beats_no_input_baseline': bool(m['ipcw_brier'] < b['ipcw_brier']),
            'test_roc_auc': m['ipcw_roc_auc'], 'mean_predicted_risk': m['mean_predicted_risk'],
            'observed_risk': m['ipcw_observed_risk']}
    reliability = {
        'label': 'Limited', 'profile_support': support,
        'answer_coverage_percent': 100*supplied/len(features),
        'personal_confidence_percent': None,
        'explanation': 'Personal prediction confidence has not been validated. Answer coverage is completeness, not the chance this prediction is correct.',
        'test_roc_auc': metric['ipcw_roc_auc'],
        'test_roc_auc_95_interval': result['default_horizon_bootstrap_95_intervals']['ipcw_roc_auc'],
        'evidence_model': 'questionnaire_model',
        'test_mean_probability': metric['mean_predicted_risk'],
        'test_observed_risk': metric['ipcw_observed_risk'],
        'test_observed_risk_bounds': [metric['observed_risk_lower'], metric['observed_risk_upper']],
        'timing_evidence': 'Assumed wave midpoints; actual individual dates unavailable.'}
    return {'status': 'scored', 'estimate_mode': mode, 'profile_support': support,
        'population': population, 'population_label': label['label'], 'outcome': label['outcome'],
        'outcome_long': label['outcome_long'], 'missing_inputs': missing,
        'probability': p, 'horizon_months': horizon,
        'probability_interval': [p_low, p_high], 'interval_level': config['prediction_interval_level'],
        'curve': [{'months': h, 'probability': float(v), 'low': float(lo), 'high': float(hi)} for h, v, lo, hi in zip(horizons, curve, low_ci[0], high_ci[0])],
        'risk_level': category, 'risk_reference_months': horizon, 'risk_reference_probability': p,
        'risk_cuts': [low, high], 'median_months': median,
        'conditional_median_months': float(model.conditional_median(row, maximum)[0]),
        'conditional_window_months': maximum, 'explanation_reference': base, 'factors': factors,
        'provided': supplied, 'expected': len(features), 'features': features,
        'timing_basis': config['timing_assumption'], 'reliability': reliability, 'horizon_evidence': evidence}
