"""Available-answer UI estimates, with explicit population and evidence scope.

Does not expand the frozen model's validated population. Out-of-profile
answers (not an adult former established smoker, or use in the past 30 days)
and submissions with too few answers are suppressed, never scored. No-answer
submissions receive the separate fitted study baseline, never a fabricated
personal probability.
"""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from path_project.final_inputs import encode_app_answers
from path_project.longitudinal import exact_feature_shap
from path_project.evaluation import BoundaryError


def assess_available(root, bundle, answers, eligibility):
    features = bundle['model'].features
    if set(answers)-set(features):
        raise BoundaryError('Only trained questionnaire inputs are accepted.')
    spec = json.loads((Path(root)/'configs/app_questions.json').read_text())
    if len(eligibility) != len(spec['eligibility_questions']):
        raise BoundaryError('Profile context has an unexpected shape.')
    unknown, outside = [], []
    for i, (value, gate) in enumerate(zip(eligibility, spec['eligibility_questions'])):
        if value is None or str(value).lower().startswith(("don't know", 'dont know', 'prefer not')):
            unknown.append(i)
        elif value not in gate['options']:
            raise BoundaryError('Unknown profile response.')
        elif value != gate['required_answer']:
            outside.append(i)
    usable = dict(answers)
    excluded = []
    recency = usable.get('last_cigarette_recency_days')
    if isinstance(recency, dict) and set(recency) == {'number', 'unit'}:
        try:
            number = float(recency['number'])
        except (ValueError, TypeError):
            number = float('nan')
        multipliers = {'1': 1., '2': 365.25/12, '3': 365.25}
        multiplier = multipliers.get(str(recency['unit']))
        if math.isfinite(number) and number > 0 and number == int(number) and multiplier and number*multiplier <= 30:
            usable['last_cigarette_recency_days'] = 'unanswered'
            excluded.append('last_cigarette_recency_days')
    values, reasons = encode_app_answers(root, usable, 7)
    supplied = sum(reasons[f] == 'observed' for f in features)
    required = math.ceil(len(features)*bundle['config']['minimum_answers_fraction'])
    if supplied and (outside or excluded):
        return {'status': 'suppressed', 'estimate_mode': 'suppressed', 'provided': supplied, 'expected': len(features),
            'reason': 'The model only covers adults who smoked at least 100 cigarettes, have quit and have not smoked in the past 30 days. Your answers fall outside that group, so no probability is shown.'}
    if supplied and (supplied < required or reasons['last_cigarette_recency_days'] != 'observed'):
        return {'status': 'suppressed', 'estimate_mode': 'suppressed', 'provided': supplied, 'expected': len(features),
            'reason': f'Please give the time since your last cigarette and at least {required} of the {len(features)} answers. With fewer, a probability would be unreliable. Unknown answers are allowed up to that limit.'}
    missing = [f for f in features if reasons[f] != 'observed']
    model = bundle['model'] if supplied else bundle['baseline']
    row = pd.DataFrame([{f: values[f] for f in model.features}], dtype=float)
    config, result = bundle['config'], bundle['results']
    horizons = result['supported_horizons_months']
    horizon = config['default_horizon_months']
    curve = model.risk(row, horizons)[0]
    p = float(model.risk(row, [horizon])[0, 0])
    low, high = result['risk_category_cuts']
    category = 'Lower' if p <= low else 'Moderate' if p <= high else 'Higher'
    maximum = max(horizons)
    median = float(12*(np.log(2)/np.exp(model.log_rate(row)[0]))**(1/model.shape)) if curve[-1] >= .5 else None
    base, factors = exact_feature_shap(model, bundle['background'], row, horizon)
    mode = 'study_reference' if supplied == 0 else 'profile_unconfirmed' if unknown else 'assessment'
    support = {'study_reference': 'Study reference only',
               'profile_unconfirmed': 'Former-smoker profile unconfirmed', 'assessment': 'Matches the study profile'}[mode]
    metric = result['metrics'][str(horizon)]['model' if supplied else 'no_input_baseline']
    # Per-horizon evidence: the fitted model must beat the no-input baseline and
    # its mean estimate must be reported against censor-adjusted observed risk.
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
        'test_roc_auc_95_interval': result['default_horizon_bootstrap_95_intervals']['ipcw_roc_auc'] if supplied else None,
        'evidence_model': 'questionnaire_model' if supplied else 'no_input_baseline',
        'test_mean_probability': metric['mean_predicted_risk'],
        'test_observed_risk': metric['ipcw_observed_risk'],
        'timing_evidence': 'Assumed wave midpoints; actual individual resumption dates unavailable.'}
    return {'status': 'scored', 'estimate_mode': mode, 'profile_support': support,
        'unknown_profile_answers': unknown, 'outside_profile_answers': outside, 'excluded_inputs': excluded,
        'missing_inputs': missing, 'probability': p, 'horizon_months': horizon,
        'curve': [{'months': h, 'probability': float(v)} for h, v in zip(horizons, curve)],
        'risk_level': category, 'risk_reference_months': horizon, 'risk_reference_probability': p,
        'risk_cuts': [low, high], 'median_months': median,
        'conditional_median_months': float(model.conditional_median(row, maximum)[0]),
        'conditional_window_months': maximum, 'explanation_reference': base, 'factors': factors,
        'provided': supplied, 'expected': len(features), 'timing_basis': config['timing_assumption'],
        'reliability': reliability, 'horizon_evidence': evidence}
