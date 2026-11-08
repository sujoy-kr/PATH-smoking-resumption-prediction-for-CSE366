"""Separate consecutive-wave study; approximate time to first observed smoking.

Original v1 cohorts, locked splits and models are never modified. No claim is
made about actual first resumption, permanent abstinence or clinical validity.
"""
from collections import Counter
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from path_project.baselines import FeatureSchema
from path_project.cohort import (field_index, harmonize_features, json_write,
    load_contract, read_wave, status_series)
from path_project.documentation import fingerprint
from path_project.evaluation import BoundaryError
from path_project.final_inputs import encode_app_answers


def read_config(root):
    return json.loads((Path(root)/'configs/longitudinal_v2.json').read_text())


def wave_clock(config, position='midpoint'):
    result = {}
    for wave, (start, end) in config['wave_windows'].items():
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        result[int(wave)] = start if position == 'start' else end if position == 'end' else start+(end-start)/2
    return result


def months_between(start, end):
    return (end-start).total_seconds()/(86400*365.25/12)


def history_status(value, outcome_coded=False):
    """Normalize mapped outcome 0/1 versus baseline 1/2, preserving unknown."""
    if pd.isna(value):
        return None
    if outcome_coded:
        return {0: 2, 1: 1}.get(int(value))
    return int(value) if int(value) in (1, 2) else None


def consecutive_runs(waves):
    runs = []
    for wave in sorted(set(waves)):
        if not runs or wave != runs[-1][-1]+1:
            runs.append([])
        runs[-1].append(wave)
    return runs


def choose_history(records, minimum=3):
    """Earliest eligible origin with >=minimum consecutive *attended* waves.

    Future attendance selects the retrospective study sample only. It is never
    a feature. An unknown follow-up status stops observation, never bridges it.
    """
    indexed = {r['wave']: r for r in records}
    for run in consecutive_runs(indexed):
        for offset, start in enumerate(run):
            tail = run[offset:]
            baseline = indexed[start]
            if len(tail) < minimum or baseline['former'] != 1 or baseline['p30'] != 2 or baseline['current'] != 2:
                continue
            end = start
            event = False
            reason = 'end_of_consecutive_observation'
            for wave in tail[1:]:
                status = indexed[wave]['current']
                if status not in (1, 2):
                    reason = 'unknown_status'
                    break
                end = wave
                if status == 1:
                    event = True
                    reason = 'first_observed_return'
                    break
            return {'starting_wave': start, 'end_wave': end, 'event': int(event),
                    'consecutive_waves': len(tail), 'observation_end_reason': reason}
    return None


def build_cohort(root, config):
    root = Path(root)
    cc, project, _, mapping = load_contract(root)
    fields = field_index(mapping)
    all_features = list(dict.fromkeys(n for names in config['feature_profiles'].values() for n in names))
    reduced_mapping = {**mapping, 'fields': [f for f in mapping['fields'] if f['name'] in all_features]}
    people, baseline_features = {}, {}
    audits = []
    for source in project['waves']:
        wave = source['wave']
        columns = {'PERSONID'}
        status_names = {
            'former': cc['baseline_former_field'],
            'p30': cc['baseline_p30_field'] if wave < 8 else cc['outcome_field'],
            'current': cc['baseline_current_field'] if wave < 8 else cc['secondary_outcome_field']}
        # Wave 8 is observation-only; no former-status field is required.
        if wave == 8:
            status_names.pop('former')
        for name in status_names.values():
            columns.update(fields[name]['waves'][str(wave)]['source_columns'])
        if wave <= 6:
            for f in reduced_mapping['fields']:
                columns.update(f['waves'][str(wave)]['source_columns'])
        raw = read_wave(root/source['data'], wave, sorted(columns), cc)
        status = {name: status_series(raw, fields[field]['waves'][str(wave)])[0] for name, field in status_names.items()}
        for i, person in enumerate(raw['PERSONID']):
            record = {'wave': wave}
            record.update({name: history_status(values.iloc[i], outcome_coded=wave == 8) for name, values in status.items()})
            record.setdefault('former', None)
            people.setdefault(person, []).append(record)
        if wave <= 6:
            eligible = status['former'].eq(1).fillna(False) & status['p30'].eq(2).fillna(False) & status['current'].eq(2).fillna(False)
            subset = raw.loc[eligible].reset_index(drop=True)
            values, _ = harmonize_features(subset, wave, reduced_mapping, cc)
            for person, row in zip(subset['PERSONID'], values[all_features].to_dict('records')):
                baseline_features[(person, wave)] = row
        audits.append({'wave': wave, 'interviews': len(raw), 'columns_read': len(columns), 'sha256': fingerprint(root/source['data'])})
        print(f'Wave {wave}: read and harmonized (aggregate only).', flush=True)
    clocks = {position: wave_clock(config, position) for position in ['midpoint', 'start', 'end']}
    rows, exclusions = [], Counter()
    attendance = Counter()
    for person, records in people.items():
        attendance[max(map(len, consecutive_runs(r['wave'] for r in records)))] += 1
        history = choose_history(records, config['minimum_consecutive_waves'])
        if history is None:
            exclusions['no_eligible_origin_with_three_consecutive_interviews'] += 1
            continue
        if history['end_wave'] == history['starting_wave']:
            exclusions['no_valid_followup_before_unknown_status'] += 1
            continue
        start, end = history['starting_wave'], history['end_wave']
        row = {'PERSONID': person, **history, **baseline_features[(person, start)]}
        for position, clock in clocks.items():
            row['months' if position == 'midpoint' else f'months_{position}_sensitivity'] = months_between(clock[start], clock[end])
        rows.append(row)
    cohort = pd.DataFrame(rows).sort_values('PERSONID').reset_index(drop=True)
    if cohort['PERSONID'].duplicated().any() or cohort['months'].le(0).any():
        raise BoundaryError('Longitudinal cohort key/time validation failed.')
    return cohort, {'wave_audit': audits, 'attendance_longest_run_distribution': dict(sorted(attendance.items())),
                    'exclusions': dict(exclusions)}


def split_participants(frame, seed):
    """60/15/10/15 train/selection/calibration/test; one row per person."""
    train, other = train_test_split(frame.index, test_size=0.4, random_state=seed, stratify=frame['event'])
    validation, other = train_test_split(other, train_size=0.375, random_state=seed+1, stratify=frame.loc[other, 'event'])
    calibration, test = train_test_split(other, train_size=0.4, random_state=seed+2, stratify=frame.loc[other, 'event'])
    result = frame.copy()
    result['split'] = ''
    for name, indices in [('train', train), ('validation', validation), ('calibration', calibration), ('test', test)]:
        result.loc[indices, 'split'] = name
    return result


def make_preprocessor(features, mapping):
    fields = field_index(mapping)
    categorical = [n for n in features if fields[n]['output_labels']]
    numeric = [n for n in features if n not in categorical]
    domains = {n: list(map(float, fields[n]['output_labels'])) if n in categorical else None for n in features}
    parts = []
    if categorical:
        parts.append(('categories', Pipeline([
            ('impute', SimpleImputer(strategy='constant', fill_value=-1, keep_empty_features=True)),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), categorical))
    if numeric:
        parts.append(('quantities', Pipeline([
            ('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
            ('log', FunctionTransformer(np.log1p, feature_names_out='one-to-one')),
            ('scale', StandardScaler())]), numeric))
    return Pipeline([('schema', FeatureSchema(features, domains)), ('columns', ColumnTransformer(parts))])


class ApproximateReturnModel:
    """Penalized Weibull PH model of first *observed* established smoking.

    Event times are assigned observation midpoints. Censored records contribute
    their survival likelihood; negatives are not permanent non-return labels.
    """
    def __init__(self, features, mapping, penalty=1., shape=True):
        self.features = list(features)
        self.preprocessor = make_preprocessor(self.features, mapping)
        self.penalty = penalty
        self.shape_enabled = shape
        self.calibration_shift = 0.

    def fit(self, frame):
        x = self.preprocessor.fit_transform(frame[self.features])
        design = np.column_stack([np.ones(len(x)), x])
        time = frame['months'].to_numpy(float)/12
        event = frame['event'].to_numpy(float)
        logs = np.log(time)
        width = design.shape[1]
        def loss(theta):
            beta = theta[:width]
            shape = np.exp(theta[-1]) if self.shape_enabled else 1.
            eta = design@beta
            cumulative = np.exp(eta+shape*logs)
            nll = np.mean(cumulative-event*(np.log(shape)+eta+(shape-1)*logs))
            nll += self.penalty*np.dot(beta[1:], beta[1:])/(2*len(x))
            grad = design.T@(cumulative-event)/len(x)
            grad[1:] += self.penalty*beta[1:]/len(x)
            if self.shape_enabled:
                grad = np.r_[grad, np.mean(cumulative*shape*logs-event*(1+shape*logs))]
            return nll, grad
        initial = np.zeros(width+int(self.shape_enabled))
        initial[0] = np.log(max(event.sum(), 1)/time.sum())
        bounds = [(-12, 5)]+[(-8, 8)]*(width-1)+([(-1.5, 1.5)] if self.shape_enabled else [])
        fit = minimize(loss, initial, method='L-BFGS-B', jac=True, bounds=bounds,
                       options={'maxiter': 1000, 'ftol': 1e-10})
        if not fit.success:
            raise BoundaryError(f'Survival optimization failed: {fit.message}')
        self.coefficients = fit.x[:width]
        self.shape = float(np.exp(fit.x[-1])) if self.shape_enabled else 1.
        self.optimization = {'success': bool(fit.success), 'iterations': int(fit.nit), 'objective': float(fit.fun)}
        return self

    def log_rate(self, frame):
        x = self.preprocessor.transform(frame[self.features])
        return self.coefficients[0]+x@self.coefficients[1:]+self.calibration_shift

    def risk(self, frame, months):
        times = np.atleast_1d(np.asarray(months, float))
        if not np.isfinite(times).all() or (times < 0).any():
            raise BoundaryError('Horizons must be finite nonnegative months.')
        hazard = np.exp(self.log_rate(frame))[:, None]*(times[None, :]/12)**self.shape
        return -np.expm1(-hazard)

    def calibrate(self, frame):
        expected = np.sum(np.exp(self.log_rate(frame))*(frame['months'].to_numpy(float)/12)**self.shape)
        observed = int(frame['event'].sum())
        if not observed:
            raise BoundaryError('Calibration sample contains no observed returns.')
        self.calibration_shift += float(np.log(observed/expected))
        return self

    def conditional_median(self, frame, maximum):
        """Median conditional on first observation occurring by maximum months."""
        p = self.risk(frame, [maximum])[:, 0]
        return 12*(-np.log1p(-p/2)/np.exp(self.log_rate(frame)))**(1/self.shape)


def censor_curve(frame):
    t, e = frame['months'].to_numpy(float), frame['event'].to_numpy(int)
    survival, values = 1., []
    for time in np.unique(t):
        at_risk = (t >= time).sum()
        survival *= 1-np.sum((t == time) & (e == 0))/at_risk
        values.append((float(time), float(survival)))
    return values


def censor_probability(curve, time, left=False):
    result = 1.
    for point, value in curve:
        if point < time or (point == time and not left):
            result = value
        else:
            break
    return result


def horizon_metrics(frame, probabilities, horizon, curve):
    t, event = frame['months'].to_numpy(float), frame['event'].to_numpy(int)
    positive = (event == 1) & (t <= horizon)
    negative = t > horizon
    # An event-free observation at exactly the horizon is known negative.
    negative |= (event == 0) & np.isclose(t, horizon, atol=1e-9)
    weights = np.zeros(len(frame))
    for i in np.flatnonzero(positive):
        weights[i] = 1/max(censor_probability(curve, t[i], left=True), 1e-12)
    weights[negative] = 1/max(censor_probability(curve, horizon), 1e-12)
    known = positive | negative
    if not known.any() or weights.max() > 20:
        return {'supported': False, 'known_outcomes': int(known.sum())}
    y, p, w = positive[known].astype(int), np.asarray(probabilities)[known], weights[known]
    brier = float(np.sum(w*(y-p)**2)/len(frame))
    return {'supported': True, 'known_outcomes': int(known.sum()), 'events_by_horizon': int(positive.sum()),
            'censored_before_horizon': int((~known).sum()), 'ipcw_brier': brier,
            'ipcw_roc_auc': float(roc_auc_score(y, p, sample_weight=w)) if len(np.unique(y)) == 2 else None,
            'ipcw_average_precision': float(average_precision_score(y, p, sample_weight=w)) if y.sum() else None,
            'mean_predicted_risk': float(np.mean(probabilities)),
            'ipcw_observed_risk': float(np.sum(weights*positive)/len(frame)),
            'maximum_censor_weight': float(weights.max())}


def fit_study(frame, config, mapping):
    train = frame.loc[frame['split'].eq('train')].copy()
    validation = frame.loc[frame['split'].eq('validation')].copy()
    calibration = frame.loc[frame['split'].eq('calibration')].copy()
    test = frame.loc[frame['split'].eq('test')].copy()
    horizons = [h for h in config['display_horizons_months'] if int(train['months'].ge(h).sum()) >= config['minimum_horizon_at_risk']]
    if config['default_horizon_months'] not in horizons:
        raise BoundaryError('Insufficient training follow-up for the default horizon.')
    selection_horizons = [h for h in config['selection_horizons_months'] if h in horizons]
    curve = censor_curve(train)
    candidates = []
    for profile, features in config['feature_profiles'].items():
        for shape in [False, True]:
            for penalty in config['regularization']:
                model = ApproximateReturnModel(features, mapping, penalty, shape).fit(train)
                scores = {str(h): horizon_metrics(validation, model.risk(validation, [h])[:, 0], h, curve) for h in selection_horizons}
                score = np.mean([m['ipcw_brier'] for m in scores.values() if m['supported']])
                candidates.append({'profile': profile, 'shape': shape, 'penalty': penalty,
                                   'validation_mean_ipcw_brier': float(score), 'metrics': scores})
                print(f"Candidate {profile}, Weibull={shape}, penalty={penalty}: validation Brier {score:.4f}", flush=True)
    best = min(candidates, key=lambda c: c['validation_mean_ipcw_brier'])
    compact = min((c for c in candidates if c['profile'] == 'compact'), key=lambda c: c['validation_mean_ipcw_brier'])
    if compact['validation_mean_ipcw_brier'] <= best['validation_mean_ipcw_brier']+config['compact_preference_brier_tolerance']:
        best = compact
    development = pd.concat([train, validation], ignore_index=True)
    model = ApproximateReturnModel(config['feature_profiles'][best['profile']], mapping, best['penalty'], best['shape']).fit(development)
    uncalibrated_shift = model.calibration_shift
    model.calibrate(calibration)
    curve = censor_curve(development)
    default = config['default_horizon_months']
    cuts = np.quantile(model.risk(calibration, [default])[:, 0], [1/3, 2/3]).tolist()
    # Baseline has no questionnaire inputs, fitted only to development data.
    baseline = ApproximateReturnModel([], mapping, 1., True).fit(development)
    baseline.calibrate(calibration)
    metrics = {}
    for h in horizons:
        metrics[str(h)] = {'model': horizon_metrics(test, model.risk(test, [h])[:, 0], h, curve),
                           'no_input_baseline': horizon_metrics(test, baseline.risk(test, [h])[:, 0], h, curve)}
    rng = np.random.default_rng(config['seed'])
    p = model.risk(test, [default])[:, 0]
    bootstrap = []
    for _ in range(config['bootstrap_repetitions']):
        ix = rng.integers(0, len(test), len(test))
        metric = horizon_metrics(test.iloc[ix], p[ix], default, curve)
        if metric['supported']:
            bootstrap.append(metric)
    intervals = {}
    for key in ['ipcw_brier', 'ipcw_roc_auc', 'ipcw_average_precision']:
        values = [m[key] for m in bootstrap if m[key] is not None]
        intervals[key] = [float(x) for x in np.quantile(values, [.025, .975])]
    # Timing sensitivity: same fitted model, different assumed clocks. No retuning.
    sensitivity = {}
    for position in ['start', 'end']:
        alternate = test.copy()
        alternate['months'] = alternate[f'months_{position}_sensitivity']
        alt_development = development.copy()
        alt_development['months'] = alt_development[f'months_{position}_sensitivity']
        sensitivity[position] = horizon_metrics(alternate, p, default, censor_curve(alt_development))
    result = {'selected_candidate': best, 'candidates': candidates, 'features': model.features,
              'supported_horizons_months': horizons, 'shape': model.shape,
              'calibration_log_rate_shift': model.calibration_shift-uncalibrated_shift,
              'category_reference_horizon_months': default, 'risk_category_cuts': cuts,
              'metrics': metrics, 'default_horizon_bootstrap_95_intervals': intervals,
              'clock_sensitivity_at_default_horizon': sensitivity,
              'selection_rule': 'Minimum validation mean IPCW Brier; prefer eight inputs if within 0.002. Refit train+validation; independent calibration; held-out test evaluated after selection.',
              'censoring_assumption': 'IPCW and survival fitting assume conditionally noninformative observation loss; consecutive-attendance selection and smoking snapshots may violate this.',
              'calibration_method': 'One multiplicative cumulative-hazard adjustment fitted on calibration participants only.'}
    return model, baseline, result, development


def build_study(root):
    root = Path(root)
    config = read_config(root)
    data_dir, artifact_dir, report_dir = [root/config[k] for k in ['data_dir', 'artifact_dir', 'report_dir']]
    if any(path.exists() for path in [data_dir, artifact_dir, report_dir]):
        raise BoundaryError('Longitudinal v2 outputs already exist; preserve them and choose a separately versioned run for substantive changes.')
    cohort, audit = build_cohort(root, config)
    frame = split_participants(cohort, config['seed'])
    mapping = json.loads((root/'configs/feature_mapping_final.json').read_text())
    model, baseline, results, development = fit_study(frame, config, mapping)
    maximum = max(results['supported_horizons_months'])
    # Fixed training-only background for exact original-feature SHAP.
    background = development[model.features].sample(n=min(16, len(development)), random_state=config['seed']).astype(float)
    aggregate = {'people': len(frame), 'observed_returns': int(frame['event'].sum()),
                 'no_return_observed_before_followup_ended': int(frame['event'].eq(0).sum()),
                 'consecutive_run_distribution': {str(k): int(v) for k, v in frame['consecutive_waves'].value_counts().sort_index().items()},
                 'baseline_wave_distribution': {str(k): int(v) for k, v in frame['starting_wave'].value_counts().sort_index().items()},
                 'observation_end_reasons': frame['observation_end_reason'].value_counts().to_dict(),
                 'splits': {name: {'people': len(part), 'events': int(part['event'].sum())} for name, part in frame.groupby('split')},
                 'feature_missingness': {name: float(frame[name].isna().mean()) for name in model.features},
                 'median_observed_event_months': float(frame.loc[frame['event'].eq(1), 'months'].median()),
                 'maximum_display_months': maximum, **audit}
    for path in [data_dir, artifact_dir, report_dir]:
        path.mkdir(parents=True, exist_ok=False)
    frame.to_parquet(data_dir/'participants.parquet', index=False)
    bundle = {'model': model, 'baseline': baseline, 'background': background,
              'config': config, 'results': results, 'summary': aggregate}
    joblib.dump(bundle, artifact_dir/'model.joblib')
    json_write(report_dir/'summary.json', aggregate)
    json_write(report_dir/'results.json', results)
    files = ['configs/longitudinal_v2.json', 'src/path_project/longitudinal.py', 'configs/feature_mapping_final.json',
             'configs/app_questions.json', 'configs/feature_mapping.json', 'configs/cohort.json']
    outputs = [data_dir/'participants.parquet', artifact_dir/'model.joblib', report_dir/'summary.json', report_dir/'results.json']
    json_write(report_dir/'manifest.json', {'version': config['version'],
        'source_sha256': {p: fingerprint(root/p) for p in files},
        'output_sha256': {str(p.relative_to(root)): fingerprint(p) for p in outputs},
        'source_data_sha256': {str(w['wave']): w['sha256'] for w in audit['wave_audit']},
        'original_v1_unchanged': True})
    print(json.dumps({k: aggregate[k] for k in ['people', 'observed_returns', 'splits']}), flush=True)
    return bundle


def load_study(root):
    root = Path(root)
    config = read_config(root)
    manifest = json.loads((root/config['report_dir']/'manifest.json').read_text())
    # Inference verifies code/config/model/report identity without loading data rows.
    for name, digest in manifest['source_sha256'].items():
        if fingerprint(root/name) != digest:
            raise BoundaryError('Longitudinal model source/config changed; preserve the run and rebuild under a new version.')
    for name, digest in manifest['output_sha256'].items():
        if name.endswith('.parquet'):
            continue
        if fingerprint(root/name) != digest:
            raise BoundaryError('Longitudinal model/report integrity check failed.')
    return joblib.load(root/config['artifact_dir']/'model.joblib')


def exact_feature_shap(model, background, row, horizon):
    """Exact Shapley values of the displayed horizon probability, original inputs."""
    features, n = model.features, len(model.features)
    batches = []
    for mask in range(1 << n):
        block = background[features].copy()
        for j, feature in enumerate(features):
            if mask & (1 << j):
                block[feature] = row[feature].iloc[0]
        batches.append(block)
    values = model.risk(pd.concat(batches, ignore_index=True), [horizon])[:, 0].reshape(1 << n, len(background)).mean(axis=1)
    contributions = []
    for j, feature in enumerate(features):
        value = 0.
        for mask in range(1 << n):
            if not mask & (1 << j):
                size = mask.bit_count()
                weight = 1/(n*math.comb(n-1, size))
                value += weight*(values[mask | (1 << j)]-values[mask])
        contributions.append({'feature': feature, 'contribution': float(value)})
    predicted = float(model.risk(row, [horizon])[0, 0])
    if not np.isclose(values[0]+sum(c['contribution'] for c in contributions), predicted, atol=1e-8):
        raise BoundaryError('Probability explanation does not reconcile.')
    return float(values[0]), sorted(contributions, key=lambda c: -abs(c['contribution']))


def predict_profile(root, bundle, answers, eligibility, horizon):
    gates = json.loads((Path(root)/'configs/app_questions.json').read_text())['eligibility_questions']
    if len(eligibility) != len(gates) or any(value != q['required_answer'] for value, q in zip(eligibility, gates)):
        return {'status': 'suppressed', 'reason': 'Confirm all eligibility answers: adult, previous established smoking, no current smoking and no use in the past 30 days.'}
    model, config = bundle['model'], bundle['config']
    if horizon not in bundle['results']['supported_horizons_months']:
        raise BoundaryError('That approximate horizon lacks configured follow-up support.')
    if set(answers)-set(model.features):
        raise BoundaryError('Only the trained questionnaire inputs are accepted.')
    values, reasons = encode_app_answers(root, answers, 7)
    supplied = sum(reasons[f] == 'observed' for f in model.features)
    required = math.ceil(len(model.features)*config['minimum_answers_fraction'])
    if supplied < required or reasons['last_cigarette_recency_days'] != 'observed':
        return {'status': 'suppressed', 'reason': f'Please supply time since last cigarette and at least {required} of the {len(model.features)} model answers. Unknown answers remain missing.'}
    row = pd.DataFrame([{f: values[f] for f in model.features}], dtype=float)
    horizons = bundle['results']['supported_horizons_months']
    probabilities = model.risk(row, horizons)[0]
    p = float(model.risk(row, [horizon])[0, 0])
    # Categories use a fixed reference horizon, independent of chosen display horizon.
    reference_horizon = config['default_horizon_months']
    reference_risk = float(model.risk(row, [reference_horizon])[0, 0])
    low, high = bundle['results']['risk_category_cuts']
    category = 'Lower' if reference_risk <= low else 'Moderate' if reference_risk <= high else 'Higher'
    maximum = max(horizons)
    conditional = float(model.conditional_median(row, maximum)[0])
    median = None
    if probabilities[-1] >= .5:
        median = float(12*(np.log(2)/np.exp(model.log_rate(row)[0]))**(1/model.shape))
    base, factors = exact_feature_shap(model, bundle['background'], row, horizon)
    return {'status': 'scored', 'probability': p, 'horizon_months': horizon,
            'curve': [{'months': h, 'probability': float(v)} for h, v in zip(horizons, probabilities)],
            'risk_level': category, 'risk_reference_months': reference_horizon,
            'risk_reference_probability': reference_risk, 'risk_cuts': [low, high],
            'median_months': median, 'conditional_median_months': conditional,
            'conditional_window_months': maximum, 'explanation_reference': base,
            'factors': factors, 'provided': supplied, 'expected': len(model.features),
            'timing_basis': config['timing_assumption']}
