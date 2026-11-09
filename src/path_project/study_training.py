"""Build, fit and evaluate the v2.4 multi-population study from raw PATH files.

v2.4 adds: every eligible baseline per person (person-weighted), many more candidate
inputs chosen by validation, bootstrap prediction intervals, subgroup and weighted checks.

Three separately fitted populations (former, current, never-established smokers),
each with its own event and evidence. Method as in v2.2:

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
from joblib import Parallel, delayed

CLOCKS = ['midpoint', 'start', 'end']


def suffix(position):
    return '' if position == 'midpoint' else f'_{position}'


def eligible(base, rule):
    return all(base.get(key) in allowed for key, allowed in rule.items())


def origin_at(indexed, wave, rule, event_current):
    base = indexed.get(wave)
    if base is None or not eligible(base, rule) or indexed.get(wave+1, {}).get('current') not in (1, 2):
        return None
    last, event, reason, step = wave, False, 'end_of_consecutive_observation', wave+1
    while step in indexed and indexed[step]['current'] in (1, 2):
        if indexed[step]['current'] == event_current:
            event, reason = True, 'first_observed_event'
            last = step
            break
        last, step = step, step+1
    else:
        if step in indexed:
            reason = 'unknown_status'
    return {'starting_wave': wave, 'end_wave': last, 'last_clear_wave': last-1 if event else last, 'event': int(event),
            'followup_interviews': last-wave, 'observation_end_reason': reason}


def all_origins(records, baseline_waves, rule, event_current):
    """Baseline interviews that *enter* the eligible state (one row per episode).

    A person who stays in the same state over many consecutive interviews contributes only the
    entry interview: later interviews of the same unbroken stretch would be
    survivor-biased and would overlap the entry row's follow-up. Someone who leaves
    and re-enters the state (for example, relapses and quits again) adds a new row.
    """
    indexed = {r['wave']: r for r in records}
    entries = []
    for wave in sorted(indexed):
        if wave not in baseline_waves:
            continue
        # Same unbroken stretch: the immediately preceding wave was attended and eligible.
        # After a skipped wave the state in between is unknown, so the interview is a new entry.
        if wave-1 in indexed and eligible(indexed[wave-1], rule):
            continue
        origin = origin_at(indexed, wave, rule, event_current)
        if origin is not None:
            entries.append(origin)
    return entries


def choose_origin(records, baseline_waves, rule=None, event_current=1):
    """Earliest eligible baseline (kept for single-row analyses and tests)."""
    found = all_origins(records, baseline_waves, rule or {'former': [1], 'current': [2]}, event_current)
    return found[0] if found else None


def read_statuses(root, config):
    cc, project, _, mapping = load_contract(root)
    fields = field_index(mapping)
    people, audits = {}, []
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
        raw = read_wave(root/source['data'], wave, sorted(columns), cc)
        status = {k: status_series(raw, fields[v]['waves'][str(wave)])[0] for k, v in names.items()}
        for i, person in enumerate(raw['PERSONID']):
            record = {'wave': wave, 'former': None}
            record.update({k: history_status(v.iloc[i], outcome_coded=wave == 8) for k, v in status.items()})
            people.setdefault(person, []).append(record)
        audits.append({'wave': wave, 'interviews': len(raw), 'sha256': fingerprint(root/source['data'])})
        print(f'Wave {wave}: statuses read (aggregate only).', flush=True)
    return people, audits


def quit_column(wave):
    # Waves 1-2 ask a multi-part item (_01 = tried to quit); waves 3+ a single yes/no item.
    return f'R{wave:02d}_AN0105_01' if wave <= 2 else f'R{wave:02d}_AN0105'


def extra_columns(wave):
    w = f'R{wave:02d}'
    return [f'{w}R_A_PERDAY_EDY_CIGS', f'{w}R_A_PERDAY_P30D_CIGS', f'{w}R_A_MINFIRST_CIGS',
            quit_column(wave), f'{w}_AN0240', f'{w}_AN0235', f'{w}_AN0010']


def positive(series):
    value = pd.to_numeric(series, errors='coerce')
    return value.where(value > 0)


def extra_features(raw, wave):
    """Current-smoker inputs from documented derived/raw PATH variables; invalid codes -> missing."""
    w = f'R{wave:02d}'
    out = pd.DataFrame(index=raw.index)
    every, some = positive(raw[f'{w}R_A_PERDAY_EDY_CIGS']), positive(raw[f'{w}R_A_PERDAY_P30D_CIGS'])
    out['cigarettes_per_day'] = every.fillna(some)
    out['minutes_to_first_cigarette'] = positive(raw[f'{w}R_A_MINFIRST_CIGS'])
    tried = pd.to_numeric(raw[quit_column(wave)], errors='coerce')
    out['tried_to_quit_12m'] = tried.map({1: 1., 2: 0.})
    plan = pd.to_numeric(raw[f'{w}_AN0240'], errors='coerce')
    no_plan = pd.to_numeric(raw[f'{w}_AN0235'], errors='coerce').eq(2)
    out['quit_plan_timeframe'] = plan.where(plan.between(1, 5)).fillna(pd.Series(np.where(no_plan, 6., np.nan), index=raw.index))
    addicted = pd.to_numeric(raw[f'{w}_AN0010'], errors='coerce')
    out['tobacco_addiction_self'] = addicted.where(addicted.between(1, 3))
    return out


def read_features(root, config, chosen):
    """Harmonize baseline answers only for the (person, wave) pairs actually used."""
    cc, project, _, mapping = load_contract(root)
    extras = list(config['extra_feature_domains'])
    names = [n for n in dict.fromkeys(f for pop in config['populations'].values()
             for g in pop['groups'].values() for f in g['features']) if n not in extras]
    reduced = {**mapping, 'fields': [f for f in mapping['fields'] if f['name'] in names]}
    wanted = {}
    for pop, origins in chosen.items():
        for person, rows in origins.items():
            for origin in rows:
                wanted.setdefault(origin['starting_wave'], set()).add(person)
    features = {}
    for source in project['waves']:
        wave = source['wave']
        if wave not in wanted:
            continue
        columns = {'PERSONID', *extra_columns(wave)}
        weight_column = f'R{wave:02d}_A_PWGT' if wave in config['survey_weight_waves'] else None
        if weight_column:
            columns.add(weight_column)
        for f in reduced['fields']:
            columns.update(f['waves'][str(wave)]['source_columns'])
        raw = read_wave(root/source['data'], wave, sorted(columns), cc)
        subset = raw.loc[raw['PERSONID'].isin(wanted[wave])].reset_index(drop=True)
        values, _ = harmonize_features(subset, wave, reduced, cc)
        table = pd.concat([values[names].astype(float), extra_features(subset, wave)], axis=1)
        table['svy_weight'] = pd.to_numeric(subset[weight_column], errors='coerce').where(lambda x: x > 0) if weight_column else np.nan
        for person, row in zip(subset['PERSONID'], table.to_dict('records')):
            features[(person, wave)] = {k: (np.nan if pd.isna(v) else float(v)) for k, v in row.items()}
        print(f'Wave {wave}: baseline answers harmonized for {len(subset)} participants.', flush=True)
    return features


def build_cohorts(root, config):
    root = Path(root)
    people, audits = read_statuses(root, config)
    baseline_waves = set(config['baseline_waves'])
    chosen = {pop: {} for pop in config['populations']}
    exclusions = {pop: Counter() for pop in config['populations']}
    for pop, spec in config['populations'].items():
        for person, records in people.items():
            origins = all_origins(records, baseline_waves, spec['baseline'], spec['event_current'])
            if origins:
                chosen[pop][person] = origins
            else:
                exclusions[pop]['no_eligible_baseline_with_a_follow_up_interview'] += 1
    features = read_features(root, config, chosen)
    clocks = {p: wave_clock(config, p) for p in CLOCKS}
    cohorts = {}
    for pop, by_person in chosen.items():
        names = list(dict.fromkeys(f for g in config['populations'][pop]['groups'].values() for f in g['features']))
        rows = []
        for person, origins in by_person.items():
            for origin in origins:
                start, end, clear = origin['starting_wave'], origin['end_wave'], origin['last_clear_wave']
                row = {'PERSONID': person, **origin, 'row_weight': 1/len(origins),
                       'svy_weight': features[(person, start)]['svy_weight'], **{n: features[(person, start)][n] for n in names}}
                for position, clock in clocks.items():
                    row['left_months'+suffix(position)] = max(months_between(clock[start], clock[clear]), 0.) if origin['event'] else 0.
                    row['right_months'+suffix(position)] = months_between(clock[start], clock[end])
                rows.append(row)
        cohort = pd.DataFrame(rows).sort_values(['PERSONID', 'starting_wave']).reset_index(drop=True)
        for position in CLOCKS:
            right, left, ev = cohort['right_months'+suffix(position)], cohort['left_months'+suffix(position)], cohort['event'].eq(1)
            if right.le(0).any() or (left[ev] >= right[ev]).any():
                raise BoundaryError('Invalid follow-up interval.')
        if cohort.duplicated(['PERSONID', 'starting_wave']).any():
            raise BoundaryError('Duplicate baseline row.')
        cohorts[pop] = cohort
    return cohorts, {'wave_audit': audits, 'exclusions': {k: dict(v) for k, v in exclusions.items()}}


def split_participants(frame, seed):
    """60/15/10/15 train/selection/calibration/test split by participant (all of a person's rows together)."""
    people = frame.groupby('PERSONID')['event'].max().sort_index()
    ids = people.index.to_numpy()
    train, other = train_test_split(ids, test_size=0.4, random_state=seed, stratify=people.to_numpy())
    flag = people.loc[other].to_numpy()
    validation, other = train_test_split(other, train_size=0.375, random_state=seed+1, stratify=flag)
    calibration, test = train_test_split(other, train_size=0.4, random_state=seed+2, stratify=people.loc[other].to_numpy())
    assignment = {}
    for name, members in [('train', train), ('validation', validation), ('calibration', calibration), ('test', test)]:
        assignment.update({person: name for person in members})
    result = frame.copy()
    result['split'] = result['PERSONID'].map(assignment)
    return result


def with_clock(frame, position):
    result = frame.copy()
    result['left_months'] = frame['left_months'+suffix(position)]
    result['right_months'] = frame['right_months'+suffix(position)]
    return result


def domains_for(features, mapping, config):
    fields = field_index(mapping)
    extra = config['extra_feature_domains']
    return {n: (extra[n] if n in extra else list(map(float, fields[n]['output_labels'])) if fields[n]['output_labels'] else None)
            for n in features}


def make_model(features, mapping, config, penalty, tvc_penalty=None):
    return PiecewiseHazardModel(features, domains_for(features, mapping, config), config['baseline_hazard_knots_months'], penalty, tvc_penalty)


def person_index(frame):
    """Map each person to the row positions they own."""
    return [np.asarray(ix) for ix in frame.groupby('PERSONID', sort=False).indices.values()]


def bootstrap_intervals(test, probabilities, horizon, curves, upper, repetitions, seed):
    """Participant-level bootstrap (all of a person's rows resampled together)."""
    rng = np.random.default_rng(seed)
    groups = person_index(test)
    runs = []
    for _ in range(repetitions):
        ix = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        metric = horizon_metrics(test.iloc[ix].reset_index(drop=True), probabilities[ix], horizon, curves, curves_upper=upper)
        if metric['supported']:
            runs.append(metric)
    result = {}
    for key in ['ipcw_brier', 'ipcw_roc_auc', 'ipcw_average_precision', 'calibration_ratio', 'observed_risk_lower', 'observed_risk_upper']:
        values = [m[key] for m in runs if m[key] is not None]
        result[key] = [float(x) for x in np.quantile(values, [.025, .975])] if values else None
    return result


def oof_calibration(frame, features, mapping, config, penalty, tvc_penalty=None, folds=5):
    """Calibration (shift, slope) from out-of-fold predictions; folds split by person.

    Predictions become ``shift + slope * linear predictor``. A slope above one corrects
    a model that is not extreme enough (typical of strong shrinkage); it is fitted
    only on non-test participants.
    """
    from scipy.optimize import minimize
    from sklearn.model_selection import GroupKFold
    parts = []
    for fit_ix, hold_ix in GroupKFold(folds).split(frame, groups=frame['PERSONID']):
        model = make_model(features, mapping, config, penalty, tvc_penalty).fit(frame.iloc[fit_ix])
        hold = frame.iloc[hold_ix]
        left, right, event = model._arrays(hold)
        raw = model._eta_matrix(model.preprocessor.transform(hold[features]), model.coefficients, model.deltas, 0., 1.)
        parts.append((model, raw, left, right, event, model._weight.sum()))
    total_weight = sum(p[5] for p in parts)
    def total(theta):
        shift, slope = theta
        return sum(w*m._nll(shift+slope*raw, m.log_baseline, l, r, e) for m, raw, l, r, e, w in parts)/total_weight
    if not features:
        from scipy.optimize import minimize_scalar
        return float(minimize_scalar(lambda s: total((s, 1.)), bounds=(-2, 2), method='bounded').x), 1.
    fit = minimize(total, x0=np.array([0., 1.]), bounds=[(-2, 2), (.5, 2.5)], method='L-BFGS-B')
    return float(fit.x[0]), float(fit.x[1])


def _replicate(frame, features, domains, knots, penalty, tvc_penalty, preprocessor, start, wave_group, seed):
    """One person-level bootstrap refit with fixed preprocessing, warm-started."""
    rng = np.random.default_rng(seed)
    groups = person_index(frame)
    ix = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
    model = PiecewiseHazardModel(features, domains, knots, penalty, tvc_penalty)
    model.wave_group = wave_group  # same strata as the full model so parameters line up
    model.fit(frame.iloc[ix], preprocessor=preprocessor, start=start)
    return model.replicate_from(model.parameters())


def select_groups(spec, train, validation, mapping, config):
    """Greedy forward selection of input groups by validation log-likelihood."""
    groups = spec['groups']
    chosen = list(spec['core_groups'])
    feats = lambda names: list(dict.fromkeys(f for g in names for f in groups[g]['features']))
    def score(names):
        model = make_model(feats(names), mapping, config, config['selection_penalty']).fit(train)
        return model.mean_log_likelihood(validation)
    current, path = score(chosen), []
    path.append({'groups': list(chosen), 'validation_mean_loglik': current, 'added': None})
    while len(chosen) < config['max_groups']:
        trials = {g: score(chosen+[g]) for g in groups if g not in chosen}
        if not trials:
            break
        best, value = max(trials.items(), key=lambda kv: kv[1])
        print(f'  + {best}: {value:.5f} (gain {value-current:+.5f})', flush=True)
        if value-current < config['greedy_gain_threshold']:
            break
        chosen.append(best)
        path.append({'groups': list(chosen), 'validation_mean_loglik': value, 'added': best, 'gain': value-current})
        current = value
    return chosen, path, score(list(spec['core_groups']))


def subgroup_report(test, probabilities, horizon, curves, upper, mapping, config):
    fields = field_index(mapping)
    report = {}
    for variable in ['sex_recorded', 'age_band', 'education_level']:
        labels = fields[variable]['output_labels']
        rows = {}
        for code, label in labels.items():
            mask = test[variable].eq(float(code)).to_numpy()
            people = test.loc[mask, 'PERSONID'].nunique()
            entry = {'label': label, 'people': int(people)}
            if people >= config['minimum_subgroup_people']:
                part = test.loc[mask].reset_index(drop=True)
                m = horizon_metrics(part, probabilities[mask], horizon, curves, curves_upper=upper)
                entry.update({k: m.get(k) for k in ['supported', 'ipcw_roc_auc', 'mean_predicted_risk', 'observed_risk_lower', 'observed_risk_upper', 'predicted_within_observed_bounds']})
            else:
                entry['supported'] = False
            rows[code] = entry
        report[variable] = rows
    return report


def weighted_sensitivity(test, probabilities, horizon, curves, upper, config):
    """Population-weighted check using baseline-wave adult weights (PATH extract has waves 1-2 only)."""
    mask = test['starting_wave'].isin(config['survey_weight_waves']).to_numpy() & test['svy_weight'].notna().to_numpy()
    part = test.loc[mask].reset_index(drop=True).assign(survey_weight=lambda f: f['svy_weight'])
    if part['PERSONID'].nunique() < config['minimum_subgroup_people']:
        return {'supported': False}
    m = horizon_metrics(part, probabilities[mask], horizon, curves, curves_upper=upper)
    m['people'] = int(part['PERSONID'].nunique())
    m['note'] = 'Cross-sectional adult weights of baseline waves 1-2 only; later waves have no weights in the supplied files; attrition handled by IPCW, not weights.'
    return m


def fit_study(frame, config, mapping, spec):
    part = {name: frame.loc[frame['split'].eq(name)].reset_index(drop=True) for name in ['train', 'validation', 'calibration', 'test']}
    train, validation, calibration, test = part['train'], part['validation'], part['calibration'], part['test']
    chosen_groups, path, core_score = select_groups(spec, train, validation, mapping, config)
    features = list(dict.fromkeys(f for g in chosen_groups for f in spec['groups'][g]['features']))
    candidates = []
    for penalty in config['regularization']:
        for tvc in config['tvc_penalties']:
            model = make_model(features, mapping, config, penalty, tvc).fit(train)
            score = model.mean_log_likelihood(validation)
            candidates.append({'penalty': penalty, 'tvc_penalty': tvc, 'validation_mean_loglik': score, '_model': model})
            print(f'Penalty {penalty}, time-varying-effect penalty {tvc}: validation log-likelihood {score:.5f}', flush=True)
    best = max(candidates, key=lambda c: c['validation_mean_loglik'])
    null = make_model([], mapping, config, 1.).fit(train)
    shown, horizon_rule = [], {}
    for h in config['display_horizons_months']:
        at_risk = int(train['right_months'].ge(h).sum())
        curves = censor_curves(train, h)
        m = horizon_metrics(validation, best['_model'].risk(validation, [h])[:, 0], h, curves)
        b = horizon_metrics(validation, null.risk(validation, [h])[:, 0], h, curves)
        ok = bool(at_risk >= config['minimum_horizon_at_risk'] and m['supported'] and b['supported'] and m['ipcw_brier'] < b['ipcw_brier'])
        horizon_rule[str(h)] = {'train_rows_at_risk': at_risk, 'validation_brier_model': m.get('ipcw_brier'),
                                'validation_brier_no_input': b.get('ipcw_brier'), 'displayed': ok}
        if ok:
            shown.append(h)
    if config['default_horizon_months'] not in shown:
        raise BoundaryError(f"Default horizon unsupported for {spec['label']}: {horizon_rule}")
    development = pd.concat([train, validation, calibration], ignore_index=True)
    model = make_model(features, mapping, config, best['penalty'], best['tvc_penalty']).fit(development)
    model.shift, model.slope = oof_calibration(development, features, mapping, config, best['penalty'], best['tvc_penalty'])
    baseline = make_model([], mapping, config, 1.).fit(development)
    baseline.shift, baseline.slope = oof_calibration(development, [], mapping, config, 1.)
    start = model.parameters()
    model.replicates = Parallel(n_jobs=-1)(delayed(_replicate)(
        development, features, model.preprocessor.domains, config['baseline_hazard_knots_months'], best['penalty'], best['tvc_penalty'],
        model.preprocessor, start, model.wave_group, config['seed']+1000+i) for i in range(config['prediction_interval_replicates']))
    default = config['default_horizon_months']
    cuts = np.quantile(model.risk(development, [default])[:, 0], [1/3, 2/3]).tolist()
    metrics, intervals = {}, {}
    for h in config['display_horizons_months']:
        curves, upper = censor_curves(development, h), censor_curves(development, h, straddle_lost=False)
        p = model.risk(test, [h])[:, 0]
        metrics[str(h)] = {'model': horizon_metrics(test, p, h, curves, curves_upper=upper),
                           'no_input_baseline': horizon_metrics(test, baseline.risk(test, [h])[:, 0], h, curves, curves_upper=upper),
                           'displayed': h in shown}
        if h in shown:
            intervals[str(h)] = bootstrap_intervals(test, p, h, curves, upper, config['bootstrap_repetitions'], config['seed']+h)
    curves, upper = censor_curves(development, default), censor_curves(development, default, straddle_lost=False)
    p = model.risk(test, [default])[:, 0]
    sensitivity = {}
    for position in ['start', 'end']:
        alt_test, alt_dev = with_clock(test, position), with_clock(development, position)
        sensitivity[position] = horizon_metrics(alt_test, p, default, censor_curves(alt_dev, default), curves_upper=censor_curves(alt_dev, default, straddle_lost=False))
    low, high = model.risk_interval(test, [default], config['prediction_interval_level'])
    results = {
        'selected_groups': {g: spec['groups'][g] for g in chosen_groups}, 'selection_path': path,
        'core_only_validation_loglik': core_score,
        'selected_candidate': {k: v for k, v in best.items() if k != '_model'},
        'candidates': [{k: v for k, v in c.items() if k != '_model'} for c in candidates],
        'features': model.features, 'supported_horizons_months': shown, 'horizon_selection': horizon_rule,
        'category_reference_horizon_months': default, 'risk_category_cuts': cuts,
        'calibration_log_hazard_shift': float(model.shift), 'calibration_slope': float(model.slope), 'metrics': metrics,
        'default_horizon_bootstrap_95_intervals': intervals[str(default)],
        'bootstrap_95_intervals_by_horizon': intervals,
        'prediction_interval': {'replicates': config['prediction_interval_replicates'], 'level': config['prediction_interval_level'],
            'test_mean_width_at_default_horizon': float(np.mean(high-low)), 'meaning': 'Sampling uncertainty of the fitted model only.'},
        'test_mean_loglik': {'model': model.mean_log_likelihood(test), 'no_input_baseline': baseline.mean_log_likelihood(test)},
        'test_log_hazard_shift_needed': model.likelihood_shift(test),
        'clock_sensitivity_at_default_horizon': sensitivity,
        'subgroups_at_default_horizon': subgroup_report(test, p, default, curves, upper, mapping, config),
        'weighted_sensitivity_at_default_horizon': weighted_sensitivity(test, p, default, curves, upper, config),
        'selection_rule': 'Greedy forward selection of input groups by validation interval-censored log-likelihood (gain threshold in config), then ridge and time-varying-effect penalties by validation (proportional hazards stays a candidate). Horizons shown only if validation Brier beats a no-input baseline. Final refit on all non-test people; calibration shift and slope from out-of-fold predictions; test evaluated once after all decisions.',
        'censoring_assumption': 'Interval-censored likelihood assumes loss to follow-up is noninformative given the inputs. IPCW weights use baseline-wave-stratified loss curves; returns whose interval straddles the horizon are unresolved. Fitting counts every baseline row equally; evaluation gives each person total weight one.',
        'calibration_method': 'Log-hazard shift and slope fitted by maximum likelihood on 5-fold out-of-fold predictions (folds by person) over all non-test participants.'}
    return model, baseline, results, development, calibration


def synthetic_background(development, features, size, seed):
    """Independent draws from each training marginal (person-weighted); no real participant row."""
    rng = np.random.default_rng(seed)
    probabilities = development['row_weight'].to_numpy(float)
    probabilities = probabilities/probabilities.sum()
    data = {f: rng.choice(development[f].to_numpy(float), size=size, replace=True, p=probabilities) for f in features}
    return pd.DataFrame(data)


def build_study(root):
    root = Path(root)
    config = read_config(root)
    dirs = [root/config[k] for k in ['data_dir', 'artifact_dir', 'report_dir']]
    if any(p.exists() for p in dirs):
        raise BoundaryError('Outputs already exist; preserve them and use a new version for changes.')
    cohorts, audit = build_cohorts(root, config)
    mapping = json.loads((root/'configs/feature_mapping_final.json').read_text())
    frames, models, results, summaries = {}, {}, {}, {}
    for pop, spec in config['populations'].items():
        print(f'--- {spec["label"]} ---', flush=True)
        frame = split_participants(cohorts[pop], config['seed'])
        model, baseline, result, development, calibration = fit_study(frame, config, mapping, spec)
        background = synthetic_background(development, model.features, config['background_size'], config['seed'])
        frames[pop] = frame.assign(population=pop)
        models[pop] = {'model': model.to_dict(), 'baseline': baseline.to_dict(),
            'background': {'kind': 'independent_training_marginals', 'columns': model.features,
                           'rows': [[None if pd.isna(v) else float(v) for v in r] for r in background.to_numpy()]}}
        results[pop] = result
        persons = frame.groupby('PERSONID')['event'].max()
        summaries[pop] = {'people': int(len(persons)), 'baseline_rows': len(frame), 'events': int(persons.sum()),
            'event_rows': int(frame['event'].sum()),
            'no_event_observed_before_followup_ended': int((persons == 0).sum()),
            'followup_interview_distribution': {str(k): int(v) for k, v in frame['followup_interviews'].value_counts().sort_index().items()},
            'baseline_wave_distribution': {str(k): int(v) for k, v in frame['starting_wave'].value_counts().sort_index().items()},
            'rows_per_person': {str(k): int(v) for k, v in frame.groupby('PERSONID').size().value_counts().sort_index().items()},
            'observation_end_reasons': frame['observation_end_reason'].value_counts().to_dict(),
            'splits': {n: {'people': int(g['PERSONID'].nunique()), 'rows': len(g), 'events': int(g.groupby('PERSONID')['event'].max().sum())} for n, g in frame.groupby('split')},
            'feature_missingness': {n: float(frame[n].isna().mean()) for n in model.features},
            'median_followup_months': float(frame['right_months'].median()),
            'maximum_display_months': max(result['supported_horizons_months']),
            'exclusions': audit['exclusions'][pop]}
    for p in dirs:
        p.mkdir(parents=True, exist_ok=False)
    data_dir, artifact_dir, report_dir = dirs
    union = sorted(set().union(*[f.columns for f in frames.values()]))
    pd.concat(frames.values(), ignore_index=True)[union].to_parquet(data_dir/'participants.parquet', index=False)
    (artifact_dir/'model.json').write_text(json.dumps({'format': 'reclaim-survival-json-v4', 'version': config['version'], 'populations': models}))
    json_write(report_dir/'summary.json', {'populations': summaries, 'wave_audit': audit['wave_audit']})
    json_write(report_dir/'results.json', results)
    outputs = [artifact_dir/'model.json', report_dir/'summary.json', report_dir/'results.json']
    json_write(report_dir/'manifest.json', {
        'version': config['version'], 'config_sha256': sha256(root/CONFIG),
        'output_sha256': {str(p.relative_to(root)): sha256(p) for p in outputs},
        'cohort_sha256': sha256(data_dir/'participants.parquet'),
        'source_data_sha256': {str(w['wave']): w['sha256'] for w in audit['wave_audit']},
        'integrity_note': 'Hashes detect accidental corruption, not tampering.'})
    print(json.dumps({k: {'people': v['people'], 'rows': v['baseline_rows'], 'events': v['events']} for k, v in summaries.items()}), flush=True)
