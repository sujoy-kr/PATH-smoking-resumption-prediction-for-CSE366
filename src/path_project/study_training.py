"""Build, fit and evaluate the v2.2 interval-censored study from raw PATH files.

Differences from v2.1 (see docs/longitudinal_v2_2.md): no conditioning on future
attendance beyond one follow-up interview; interval-censored likelihood; wave-7
baselines; flexible baseline hazard; loss-aware IPCW stratified by baseline wave;
synthetic independent-marginal explanation background (no participant rows).
"""
from collections import Counter
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from path_project.cohort import (field_index, harmonize_features, json_write,
    load_contract, read_wave, status_series)
from path_project.documentation import fingerprint
from path_project.evaluation import BoundaryError
from path_project.longitudinal import history_status, wave_clock, months_between
from path_project.study import CONFIG, read_config, sha256
from path_project.survival import (PiecewiseHazardModel, censor_curves, horizon_metrics)

CLOCKS = ['midpoint', 'start', 'end']


def suffix(position):
    return '' if position == 'midpoint' else f'_{position}'


def choose_origin(records, baseline_waves):
    """Earliest eligible baseline with at least one later known-status interview.

    Observation then continues through consecutive attended waves until the
    first reported return, loss of a known status, or the last wave. Interviews
    after the first return and later attendance never influence inclusion.
    """
    indexed = {r['wave']: r for r in records}
    for wave in sorted(indexed):
        base = indexed[wave]
        if wave not in baseline_waves or base['former'] != 1 or base['p30'] != 2 or base['current'] != 2:
            continue
        if indexed.get(wave+1, {}).get('current') not in (1, 2):
            continue
        last, event, reason, step = wave, False, 'end_of_consecutive_observation', wave+1
        while step in indexed and indexed[step]['current'] in (1, 2):
            if indexed[step]['current'] == 1:
                event, reason = True, 'first_observed_return'
                last = step
                break
            last, step = step, step+1
        else:
            if step in indexed:
                reason = 'unknown_status'
        previous = last-1 if event else last
        return {'starting_wave': wave, 'end_wave': last, 'last_clear_wave': previous, 'event': int(event),
                'followup_interviews': last-wave, 'observation_end_reason': reason}
    return None


def build_cohort(root, config):
    root = Path(root)
    cc, project, _, mapping = load_contract(root)
    fields = field_index(mapping)
    all_features = list(dict.fromkeys(n for names in config['feature_profiles'].values() for n in names))
    reduced = {**mapping, 'fields': [f for f in mapping['fields'] if f['name'] in all_features]}
    baseline_waves = set(config['baseline_waves'])
    people, features, audits = {}, {}, []
    for source in project['waves']:
        wave = source['wave']
        names = {'former': cc['baseline_former_field'],
                 'p30': cc['baseline_p30_field'] if wave < 8 else cc['outcome_field'],
                 'current': cc['baseline_current_field'] if wave < 8 else cc['secondary_outcome_field']}
        if wave == 8:
            names.pop('former')
        columns = {'PERSONID'}
        for name in names.values():
            columns.update(fields[name]['waves'][str(wave)]['source_columns'])
        if wave in baseline_waves:
            for f in reduced['fields']:
                columns.update(f['waves'][str(wave)]['source_columns'])
        raw = read_wave(root/source['data'], wave, sorted(columns), cc)
        status = {k: status_series(raw, fields[v]['waves'][str(wave)])[0] for k, v in names.items()}
        for i, person in enumerate(raw['PERSONID']):
            record = {'wave': wave, 'former': None}
            record.update({k: history_status(v.iloc[i], outcome_coded=wave == 8) for k, v in status.items()})
            people.setdefault(person, []).append(record)
        if wave in baseline_waves:
            eligible = status['former'].eq(1).fillna(False) & status['p30'].eq(2).fillna(False) & status['current'].eq(2).fillna(False)
            subset = raw.loc[eligible].reset_index(drop=True)
            values, _ = harmonize_features(subset, wave, reduced, cc)
            for person, row in zip(subset['PERSONID'], values[all_features].to_dict('records')):
                features[(person, wave)] = {k: (np.nan if pd.isna(v) else float(v)) for k, v in row.items()}
        audits.append({'wave': wave, 'interviews': len(raw), 'columns_read': len(columns), 'sha256': fingerprint(root/source['data'])})
        print(f'Wave {wave}: read and harmonized (aggregate only).', flush=True)
    clocks = {p: wave_clock(config, p) for p in CLOCKS}
    rows, exclusions = [], Counter()
    for person, records in people.items():
        origin = choose_origin(records, baseline_waves)
        if origin is None:
            exclusions['no_eligible_baseline_with_a_follow_up_interview'] += 1
            continue
        start, end, clear = origin['starting_wave'], origin['end_wave'], origin['last_clear_wave']
        row = {'PERSONID': person, **origin, **features[(person, start)]}
        for position, clock in clocks.items():
            right = months_between(clock[start], clock[end])
            left = months_between(clock[start], clock[clear]) if origin['event'] else 0.
            row['left_months'+suffix(position)] = max(left, 0.)
            row['right_months'+suffix(position)] = right
        rows.append(row)
    cohort = pd.DataFrame(rows).sort_values('PERSONID').reset_index(drop=True)
    for position in CLOCKS:
        if cohort['right_months'+suffix(position)].le(0).any():
            raise BoundaryError('Nonpositive follow-up time.')
        event = cohort['event'].eq(1)
        if (cohort.loc[event, 'left_months'+suffix(position)] >= cohort.loc[event, 'right_months'+suffix(position)]).any():
            raise BoundaryError('Return interval is empty.')
    if cohort['PERSONID'].duplicated().any():
        raise BoundaryError('Duplicate participant.')
    return cohort, {'wave_audit': audits, 'exclusions': dict(exclusions)}


def split_participants(frame, seed):
    """60/15/10/15 train/selection/calibration/test split, one row per person."""
    train, other = train_test_split(frame.index, test_size=0.4, random_state=seed, stratify=frame['event'])
    validation, other = train_test_split(other, train_size=0.375, random_state=seed+1, stratify=frame.loc[other, 'event'])
    calibration, test = train_test_split(other, train_size=0.4, random_state=seed+2, stratify=frame.loc[other, 'event'])
    result = frame.copy()
    result['split'] = ''
    for name, index in [('train', train), ('validation', validation), ('calibration', calibration), ('test', test)]:
        result.loc[index, 'split'] = name
    return result


def with_clock(frame, position):
    result = frame.copy()
    result['left_months'] = frame['left_months'+suffix(position)]
    result['right_months'] = frame['right_months'+suffix(position)]
    return result


def domains_for(features, mapping):
    fields = field_index(mapping)
    return {n: (list(map(float, fields[n]['output_labels'])) if fields[n]['output_labels'] else None) for n in features}


def make_model(features, mapping, config, penalty):
    return PiecewiseHazardModel(features, domains_for(features, mapping), config['baseline_hazard_knots_months'], penalty)


def bootstrap_intervals(test, probabilities, horizon, curves, upper, repetitions, seed):
    rng = np.random.default_rng(seed)
    runs = []
    for _ in range(repetitions):
        ix = rng.integers(0, len(test), len(test))
        metric = horizon_metrics(test.iloc[ix].reset_index(drop=True), probabilities[ix], horizon, curves, curves_upper=upper)
        if metric['supported']:
            runs.append(metric)
    result = {}
    for key in ['ipcw_brier', 'ipcw_roc_auc', 'ipcw_average_precision', 'calibration_ratio', 'observed_risk_lower', 'observed_risk_upper']:
        values = [m[key] for m in runs if m[key] is not None]
        result[key] = [float(x) for x in np.quantile(values, [.025, .975])] if values else None
    return result


def fit_study(frame, config, mapping):
    part = {name: frame.loc[frame['split'].eq(name)].reset_index(drop=True) for name in ['train', 'validation', 'calibration', 'test']}
    train, validation, calibration, test = part['train'], part['validation'], part['calibration'], part['test']
    candidates = []
    for profile, names in config['feature_profiles'].items():
        for penalty in config['regularization']:
            model = make_model(names, mapping, config, penalty).fit(train)
            score = model.mean_log_likelihood(validation)
            candidates.append({'profile': profile, 'penalty': penalty, 'validation_mean_loglik': score, '_model': model})
            print(f'Candidate {profile}, penalty={penalty}: validation log-likelihood {score:.5f}', flush=True)
    best = max(candidates, key=lambda c: c['validation_mean_loglik'])
    compact = max((c for c in candidates if c['profile'] == 'compact'), key=lambda c: c['validation_mean_loglik'])
    if compact['validation_mean_loglik'] >= best['validation_mean_loglik']-config['compact_preference_loglik_tolerance']:
        best = compact
    # Horizons are shown only when supported by follow-up and the selected
    # model beats the no-input baseline on validation people (never on test).
    null = make_model([], mapping, config, 1.).fit(train)
    shown, horizon_rule = [], {}
    for h in config['display_horizons_months']:
        at_risk = int(train['right_months'].ge(h).sum())
        curves = censor_curves(train, h)
        m = horizon_metrics(validation, best['_model'].risk(validation, [h])[:, 0], h, curves)
        b = horizon_metrics(validation, null.risk(validation, [h])[:, 0], h, curves)
        ok = bool(at_risk >= config['minimum_horizon_at_risk'] and m['supported'] and b['supported'] and m['ipcw_brier'] < b['ipcw_brier'])
        horizon_rule[str(h)] = {'train_people_at_risk': at_risk, 'validation_brier_model': m.get('ipcw_brier'),
                                'validation_brier_no_input': b.get('ipcw_brier'), 'displayed': ok}
        if ok:
            shown.append(h)
    if config['default_horizon_months'] not in shown:
        raise BoundaryError('The default horizon is not supported by validation evidence.')
    development = pd.concat([train, validation], ignore_index=True)
    model = make_model(best['_model'].features, mapping, config, best['penalty']).fit(development)
    model.calibrate(calibration)
    baseline = make_model([], mapping, config, 1.).fit(development)
    baseline.calibrate(calibration)
    default = config['default_horizon_months']
    pool = pd.concat([development, calibration], ignore_index=True)
    cuts = np.quantile(model.risk(pool, [default])[:, 0], [1/3, 2/3]).tolist()
    metrics, intervals = {}, {}
    for h in config['display_horizons_months']:
        curves, upper = censor_curves(development, h), censor_curves(development, h, straddle_lost=False)
        p = model.risk(test, [h])[:, 0]
        metrics[str(h)] = {'model': horizon_metrics(test, p, h, curves, curves_upper=upper),
                           'no_input_baseline': horizon_metrics(test, baseline.risk(test, [h])[:, 0], h, curves, curves_upper=upper),
                           'displayed': h in shown}
        if h in shown:
            intervals[str(h)] = bootstrap_intervals(test, p, h, curves, upper, config['bootstrap_repetitions'], config['seed']+h)
    sensitivity = {}
    p = model.risk(test, [default])[:, 0]
    for position in ['start', 'end']:
        alt_test, alt_dev = with_clock(test, position), with_clock(development, position)
        sensitivity[position] = horizon_metrics(alt_test, p, default, censor_curves(alt_dev, default), curves_upper=censor_curves(alt_dev, default, straddle_lost=False))
    results = {
        'selected_candidate': {k: v for k, v in best.items() if k != '_model'},
        'candidates': [{k: v for k, v in c.items() if k != '_model'} for c in candidates],
        'features': model.features, 'supported_horizons_months': shown, 'horizon_selection': horizon_rule,
        'category_reference_horizon_months': default, 'risk_category_cuts': cuts,
        'calibration_log_hazard_shift': float(model.shift), 'metrics': metrics,
        'default_horizon_bootstrap_95_intervals': intervals[str(default)],
        'bootstrap_95_intervals_by_horizon': intervals,
        'test_mean_loglik': {'model': model.mean_log_likelihood(test), 'no_input_baseline': baseline.mean_log_likelihood(test)},
        'test_log_hazard_shift_needed': model.likelihood_shift(test),
        'clock_sensitivity_at_default_horizon': sensitivity,
        'selection_rule': 'Maximum validation interval-censored log-likelihood; prefer eight inputs within tolerance. Horizons shown only if validation Brier beats a no-input baseline. Refit on train+validation; calibration shift fitted on calibration people; test evaluated once after all decisions.',
        'censoring_assumption': 'Interval-censored likelihood assumes loss to follow-up is noninformative given the model inputs. IPCW evaluation weights by baseline-wave-stratified Kaplan-Meier loss curves, treating returns whose interval straddles the horizon as unresolved.',
        'calibration_method': 'One maximum-likelihood log-hazard shift on calibration people only, on top of a flexible piecewise baseline hazard.'}
    return model, baseline, results, development, calibration


def synthetic_background(development, features, size, seed):
    """Independent draws from each training marginal; no real participant row."""
    rng = np.random.default_rng(seed)
    data = {f: rng.choice(development[f].to_numpy(float), size=size, replace=True) for f in features}
    return pd.DataFrame(data)


def build_study(root):
    root = Path(root)
    config = read_config(root)
    dirs = [root/config[k] for k in ['data_dir', 'artifact_dir', 'report_dir']]
    if any(p.exists() for p in dirs):
        raise BoundaryError('v2.2 outputs already exist; preserve them and use a new version for changes.')
    cohort, audit = build_cohort(root, config)
    frame = split_participants(cohort, config['seed'])
    mapping = json.loads((root/'configs/feature_mapping_final.json').read_text())
    model, baseline, results, development, calibration = fit_study(frame, config, mapping)
    pool = pd.concat([development, calibration], ignore_index=True)
    background = synthetic_background(pool, model.features, config['background_size'], config['seed'])
    summary = {'people': len(frame), 'observed_returns': int(frame['event'].sum()),
               'no_return_observed_before_followup_ended': int(frame['event'].eq(0).sum()),
               'followup_interview_distribution': {str(k): int(v) for k, v in frame['followup_interviews'].value_counts().sort_index().items()},
               'baseline_wave_distribution': {str(k): int(v) for k, v in frame['starting_wave'].value_counts().sort_index().items()},
               'observation_end_reasons': frame['observation_end_reason'].value_counts().to_dict(),
               'splits': {n: {'people': len(g), 'events': int(g['event'].sum())} for n, g in frame.groupby('split')},
               'feature_missingness': {n: float(frame[n].isna().mean()) for n in model.features},
               'median_followup_months': float(frame['right_months'].median()),
               'maximum_display_months': max(results['supported_horizons_months']), **audit}
    for p in dirs:
        p.mkdir(parents=True, exist_ok=False)
    data_dir, artifact_dir, report_dir = dirs
    frame.to_parquet(data_dir/'participants.parquet', index=False)
    rows = [[None if pd.isna(v) else float(v) for v in r] for r in background.to_numpy()]
    (artifact_dir/'model.json').write_text(json.dumps({
        'format': 'reclaim-survival-json-v1', 'version': config['version'], 'model': model.to_dict(),
        'baseline': baseline.to_dict(), 'background': {'kind': 'independent_training_marginals', 'columns': model.features, 'rows': rows}}))
    json_write(report_dir/'summary.json', summary)
    json_write(report_dir/'results.json', results)
    outputs = [artifact_dir/'model.json', report_dir/'summary.json', report_dir/'results.json']
    json_write(report_dir/'manifest.json', {
        'version': config['version'], 'config_sha256': sha256(root/CONFIG),
        'output_sha256': {str(p.relative_to(root)): sha256(p) for p in outputs},
        'cohort_sha256': sha256(data_dir/'participants.parquet'),
        'source_data_sha256': {str(w['wave']): w['sha256'] for w in audit['wave_audit']},
        'integrity_note': 'Hashes detect accidental corruption, not tampering.'})
    print(json.dumps({k: summary[k] for k in ['people', 'observed_returns', 'splits']}), flush=True)
    return model
