"""Interval-censored piecewise-exponential proportional-hazards model.

Pure numpy/pandas at prediction time and JSON serialization, so no pickle is
ever loaded. Fitting needs scipy (imported lazily).

Data per person: the first observed return lies in (left, right] months from the
baseline interview (events), or the person is event-free through ``right``
(censored). Times are months; hazards are per year.
"""
import math

import numpy as np
import pandas as pd

from path_project.evaluation import BoundaryError

MONTHS_PER_YEAR = 12.


class Preprocessor:
    """Validated one-hot / log-scaled design matrix with explicit missingness."""

    def __init__(self, features, domains):
        self.features = list(features)
        self.domains = {n: (None if d is None else [float(v) for v in d]) for n, d in domains.items()}
        self.categorical = [n for n in self.features if self.domains[n] is not None]
        self.numeric = [n for n in self.features if self.domains[n] is None]
        self.medians, self.means, self.scales = {}, [], []
        self.hinges = {}

    def _validated(self, frame):
        if not isinstance(frame, pd.DataFrame) or set(frame.columns) != set(self.features) or len(frame.columns) != len(self.features):
            raise BoundaryError('Prediction schema must contain exactly the configured feature names.')
        try:
            result = frame[self.features].apply(pd.to_numeric, errors='raise').astype(float)
        except (ValueError, TypeError):
            raise BoundaryError('Model features must be numeric codes/quantities or missing.') from None
        if np.isinf(result.to_numpy()).any():
            raise BoundaryError('Nonfinite feature value.')
        for name in self.categorical:
            if not result[name].dropna().isin(self.domains[name]).all():
                raise BoundaryError(f'{name}: outside documented category codes.')
        for name in self.numeric:
            if result[name].dropna().lt(0).any():
                raise BoundaryError(f'{name}: negative quantity not valid.')
        return result

    def _raw(self, frame):
        values = self._validated(frame)
        blocks = []
        for name in self.categorical:
            column = values[name].fillna(-1.).to_numpy()
            levels = self.domains[name]+[-1.]
            blocks.append((column[:, None] == np.array(levels)[None, :]).astype(float))
        for name in self.numeric:
            column = values[name]
            missing = column.isna().to_numpy()
            filled = column.fillna(self.medians.get(name, 0.)).to_numpy()
            logged = np.log1p(filled)
            blocks.append(logged[:, None])
            # Piecewise-linear terms let a numeric input bend (e.g. very long quits).
            for knot in self.hinges.get(name, []):
                blocks.append(np.maximum(0., logged-knot)[:, None])
            blocks.append(missing[:, None].astype(float))
        return np.hstack(blocks) if blocks else np.zeros((len(frame), 0))

    def fit(self, frame):
        values = self._validated(frame)
        self.medians = {n: (float(values[n].median()) if values[n].notna().any() else 0.) for n in self.numeric}
        self.hinges = {}
        for name in self.numeric:
            logged = np.log1p(values[name].dropna().to_numpy())
            knots = np.unique(np.round(np.quantile(logged, [.2, .4, .6, .8]), 6)) if len(logged) > 50 else np.array([])
            self.hinges[name] = [float(k) for k in knots if logged.min() < k < logged.max()]
        raw = self._raw(frame)
        self.means = raw.mean(axis=0).tolist() if raw.shape[1] else []
        spread = raw.std(axis=0) if raw.shape[1] else np.array([])
        self.scales = np.where(spread > 1e-12, spread, 1.).tolist()
        return self

    def transform(self, frame):
        raw = self._raw(frame)
        return (raw-np.array(self.means))/np.array(self.scales) if raw.shape[1] else raw

    def to_dict(self):
        return {'features': self.features, 'domains': self.domains, 'medians': self.medians,
                'hinges': self.hinges, 'means': self.means, 'scales': self.scales}

    @classmethod
    def from_dict(cls, data):
        result = cls(data['features'], data['domains'])
        result.medians, result.means, result.scales = data['medians'], data['means'], data['scales']
        result.hinges = data.get('hinges', {})
        return result


def _bins(knots_months):
    return np.asarray(knots_months, float)/MONTHS_PER_YEAR


def exposure(times_years, knots_years):
    """Time spent in each baseline-hazard bin by t (last bin is open-ended)."""
    t = np.asarray(times_years, float)[:, None]
    lower = knots_years[None, :]
    upper = np.append(knots_years[1:], np.inf)[None, :]
    return np.clip(np.minimum(t, upper)-lower, 0., None)


class PiecewiseHazardModel:
    """Penalized piecewise-exponential survival model.

    Hazard in time bin j for person i:  exp(x_i (beta + delta_j) + log baseline[g, j]),
    where g is the person's baseline-wave group. ``delta`` (time-varying effects) is
    shrunk toward zero by ``tvc_penalty``; ``tvc_penalty=None`` gives plain
    proportional hazards. Frames without ``starting_wave`` (a new app user) get the
    average over wave groups, weighted by training rows.
    """
    MIN_ROWS, MIN_EVENTS = 300, 40

    def __init__(self, features, domains, knots_months, penalty=1., tvc_penalty=None):
        self.features = list(features)
        self.preprocessor = Preprocessor(self.features, domains)
        self.knots_months = list(map(float, knots_months))
        self.knots = _bins(self.knots_months)
        self.penalty = float(penalty)
        self.tvc_penalty = None if tvc_penalty is None else float(tvc_penalty)
        self.coefficients = np.zeros(0)
        self.deltas = np.zeros((len(self.knots), 0))
        self.wave_group = {}
        self.group_weights = np.ones(1)
        self.log_baseline = np.zeros((1, len(self.knots)))
        self.shift = 0.
        self.slope = 1.
        self.replicates = []

    # ---- strata -------------------------------------------------------
    def _define_groups(self, frame):
        """Merge consecutive baseline waves until each group has enough rows and events."""
        if 'starting_wave' not in frame:
            return {0: 0}
        groups, current, rows, events = {}, 0, 0, 0
        for wave in np.sort(frame['starting_wave'].unique()):
            mask = frame['starting_wave'].eq(wave)
            groups[int(wave)] = current
            rows += int(mask.sum())
            events += int(frame.loc[mask, 'event'].sum())
            if rows >= self.MIN_ROWS and events >= self.MIN_EVENTS:
                current, rows, events = current+1, 0, 0
        if rows and current > 0:  # undersized tail merges into the previous group
            for wave in groups:
                if groups[wave] == current:
                    groups[wave] = current-1
        return groups

    def _group_index(self, frame):
        if not self.wave_group or 'starting_wave' not in frame:
            return None
        known = frame['starting_wave'].map(self.wave_group)
        return None if known.isna().any() else known.to_numpy(int)

    # ---- linear predictors ---------------------------------------------
    def _eta_matrix(self, design, coefficients, deltas, shift, slope=1.):
        """(rows x bins) log-hazard ratios; calibration is ``shift + slope * linear predictor``."""
        base = (design@coefficients)[:, None]
        raw = base+design@deltas.T if deltas.size else np.repeat(base, len(self.knots), axis=1)
        return shift+slope*raw

    def _eta(self, frame):
        return self._eta_matrix(self.preprocessor.transform(frame[self.features]), self.coefficients, self.deltas, self.shift, self.slope)

    def log_rate(self, frame):
        """Reference-bin log hazard ratio (the proportional-hazards part)."""
        return self.preprocessor.transform(frame[self.features])@self.coefficients*self.slope+self.shift

    # ---- likelihood ---------------------------------------------------
    def _arrays(self, frame):
        left = frame['left_months'].to_numpy(float)/MONTHS_PER_YEAR
        right = frame['right_months'].to_numpy(float)/MONTHS_PER_YEAR
        event = frame['event'].to_numpy(int) == 1
        # Fitting weights are optional and default to one per row; 'row_weight' is evaluation-only.
        self._weight = frame['fit_weight'].to_numpy(float) if 'fit_weight' in frame else np.ones(len(frame))
        if (right <= 0).any() or (left < 0).any() or (left[event] >= right[event]).any():
            raise BoundaryError('Observation intervals must satisfy 0 <= left < right.')
        index = self._group_index(frame)
        self._group = index if index is not None else np.zeros(len(frame), int)
        return left, right, event

    def _nll(self, eta, loglam, left, right, event, grads=False):
        """Mean negative log-likelihood; ``eta`` is (rows x bins). Returns (value, dEta, dLogLam) with grads."""
        lam_rows = np.exp(loglam)[self._group]
        rate = np.exp(eta)*lam_rows
        el, er = exposure(left, self.knots), exposure(right, self.knots)
        hl, hr = (rate*el).sum(axis=1), (rate*er).sum(axis=1)
        d = np.maximum(hr-hl, 1e-12)
        g = 1./np.expm1(d)
        ll = np.where(event, -hl+np.log(-np.expm1(-d)), -hr)
        w = self._weight/self._weight.sum()
        value = -np.sum(w*ll)
        if not grads:
            return value
        dl = np.where(event, -1.-g, 0.)
        dr = np.where(event, g, -1.)
        m = (dl[:, None]*el+dr[:, None]*er)*rate*w[:, None]      # d(-value)/d eta == d/d loglam per cell
        d_log = np.zeros(lam_rows.shape[1]*(self._group.max()+1)).reshape(-1, lam_rows.shape[1])
        np.add.at(d_log, self._group, m)
        return value, -m, -d_log

    def fit(self, frame, preprocessor=None, start=None):
        from scipy.optimize import minimize
        if start is None or not self.wave_group:
            self.wave_group = self._define_groups(frame)
        groups = max(self.wave_group.values())+1
        left, right, event = self._arrays(frame)
        if preprocessor is None:
            self.preprocessor.fit(frame[self.features])
        else:
            self.preprocessor = preprocessor
        design = self.preprocessor.transform(frame[self.features])
        n, p, j = self._weight.sum(), design.shape[1], len(self.knots)
        tvc = self.tvc_penalty is not None and p > 0
        self.group_weights = np.bincount(self._group, weights=self._weight, minlength=groups)/n
        total_time = max(np.sum(self._weight*right), 1e-9)
        rate = math.log(max(np.sum(self._weight*event), 1e-9)/total_time)
        size_delta = j*p if tvc else 0
        initial = np.r_[np.zeros(p+size_delta), np.full(groups*j, rate)] if start is None else np.asarray(start, float)

        def unpack(theta):
            beta = theta[:p]
            delta = theta[p:p+size_delta].reshape(j, p) if tvc else np.zeros((j, 0))
            return beta, delta, theta[p+size_delta:].reshape(groups, j)

        def loss(theta):
            beta, delta, loglam = unpack(theta)
            eta = self._eta_matrix(design, beta, delta, 0.)
            value, d_eta, d_log = self._nll(eta, loglam, left, right, event, True)
            value += self.penalty*beta@beta/(2*n)
            g_beta = design.T@d_eta.sum(axis=1)+self.penalty*beta/n
            pieces = [g_beta]
            if tvc:
                value += self.tvc_penalty*np.sum(delta**2)/(2*n)
                pieces.append((design.T@d_eta).T.ravel()+self.tvc_penalty*delta.ravel()/n)
            return value, np.r_[np.concatenate(pieces), d_log.ravel()]

        bounds = [(-6, 6)]*(p+size_delta)+[(-12, 3)]*(groups*j)
        fit = minimize(loss, initial, jac=True, method='L-BFGS-B', bounds=bounds, options={'maxiter': 5000, 'ftol': 1e-12})
        if not fit.success:
            raise BoundaryError(f'Survival optimization failed: {fit.message}')
        self.coefficients, self.deltas, self.log_baseline = unpack(fit.x)
        self.shift = 0.
        self.optimization = {'success': True, 'iterations': int(fit.nit), 'objective': float(fit.fun)}
        return self

    def parameters(self):
        return np.r_[self.coefficients, self.deltas.ravel(), self.log_baseline.ravel()]

    def log_likelihood(self, frame):
        left, right, event = self._arrays(frame)
        return -self._nll(self._eta(frame), self.log_baseline, left, right, event)*self._weight.sum()

    def calibrate(self, frame):
        """Maximum-likelihood multiplicative hazard shift on calibration people only."""
        from scipy.optimize import minimize_scalar
        left, right, event = self._arrays(frame)
        eta = self._eta(frame)
        fit = minimize_scalar(lambda s: self._nll(eta+s, self.log_baseline, left, right, event), bounds=(-2, 2), method='bounded')
        self.shift += float(fit.x)
        return float(fit.x)

    def likelihood_shift(self, frame):
        """Log-hazard shift a sample would need (0 means calibrated in the large)."""
        from scipy.optimize import minimize_scalar
        left, right, event = self._arrays(frame)
        eta = self._eta(frame)
        return float(minimize_scalar(lambda s: self._nll(eta+s, self.log_baseline, left, right, event), bounds=(-3, 3), method='bounded').x)

    def mean_log_likelihood(self, frame):
        """Held-out interval-censored log-likelihood per person (proper score)."""
        left, right, event = self._arrays(frame)
        return float(-self._nll(self._eta(frame), self.log_baseline, left, right, event))

    # ---- prediction ---------------------------------------------------
    def _risk_from(self, eta, loglam, group, times_years):
        """Risk matrix (rows x times); ``group`` None averages over wave groups."""
        ex = exposure(times_years, self.knots)                  # (times, bins)
        if group is not None:
            rate = np.exp(eta)*np.exp(loglam)[group]            # (rows, bins)
            return -np.expm1(-(rate@ex.T))
        total = 0.
        for g, weight in enumerate(self.group_weights):
            total = total+weight*-np.expm1(-((np.exp(eta)*np.exp(loglam[g])[None, :])@ex.T))
        return total

    def risk(self, frame, months):
        times = np.atleast_1d(np.asarray(months, float))
        if not np.isfinite(times).all() or (times < 0).any():
            raise BoundaryError('Horizons must be finite nonnegative months.')
        return self._risk_from(self._eta(frame), self.log_baseline, self._group_index(frame), times/MONTHS_PER_YEAR)

    def _invert_risk(self, frame, target):
        """Months at which risk reaches ``target`` (scalar or per row), by bisection."""
        eta = np.exp(self._eta(frame))
        group = self._group_index(frame)
        lam = np.exp(self.log_baseline)
        target = np.broadcast_to(np.asarray(target, float), (len(eta),))
        low, high = np.zeros(len(eta)), np.full(len(eta), 2400.)

        def risk_at(t):
            ex = exposure(t/MONTHS_PER_YEAR, self.knots)
            if group is not None:
                return -np.expm1(-(eta*lam[group]*ex).sum(axis=1))
            return sum(w*-np.expm1(-(eta*lam[g][None, :]*ex).sum(axis=1)) for g, w in enumerate(self.group_weights))
        for _ in range(80):
            mid = (low+high)/2
            above = risk_at(mid) >= target
            high, low = np.where(above, mid, high), np.where(above, low, mid)
        return (low+high)/2

    def median_months(self, frame):
        return self._invert_risk(frame, .5)

    def conditional_median(self, frame, maximum):
        """Median first-event time given an event occurs by ``maximum`` months."""
        return self._invert_risk(frame, self.risk(frame, [maximum])[:, 0]/2)

    def risk_interval(self, frame, months, level=.95):
        """Percentile range of risk across bootstrap-refitted parameter sets.

        Reflects sampling uncertainty of the fitted model only, not individual
        outcome randomness or model misspecification.
        """
        if not self.replicates:
            raise BoundaryError('Model has no bootstrap replicates.')
        design = self.preprocessor.transform(frame[self.features])
        times = np.atleast_1d(np.asarray(months, float))/MONTHS_PER_YEAR
        group = self._group_index(frame)
        out = np.stack([self._risk_from(
            self._eta_matrix(design, np.asarray(r['coefficients']), np.asarray(r['deltas']).reshape(len(self.knots), -1) if r.get('deltas') else np.zeros((len(self.knots), 0)), self.shift, self.slope),
            np.asarray(r['log_baseline']), group, times) for r in self.replicates])
        tail = (1-level)/2*100
        return np.percentile(out, tail, axis=0), np.percentile(out, 100-tail, axis=0)

    def replicate_from(self, parameters):
        """Package a parameter vector (as returned by ``parameters``) for storage."""
        p, j = len(self.coefficients), len(self.knots)
        size = j*p if self.deltas.size else 0
        return {'coefficients': parameters[:p].tolist(), 'deltas': parameters[p:p+size].reshape(j, p).tolist() if size else [],
                'log_baseline': parameters[p+size:].reshape(self.log_baseline.shape).tolist()}

    # ---- serialization ------------------------------------------------
    def to_dict(self):
        return {'features': self.features, 'knots_months': self.knots_months, 'penalty': self.penalty,
                'tvc_penalty': self.tvc_penalty, 'coefficients': self.coefficients.tolist(),
                'deltas': self.deltas.tolist(), 'log_baseline': self.log_baseline.tolist(),
                'wave_group': {str(k): v for k, v in self.wave_group.items()},
                'group_weights': self.group_weights.tolist(), 'shift': self.shift, 'slope': self.slope,
                'preprocessor': self.preprocessor.to_dict(), 'replicates': self.replicates}

    @classmethod
    def from_dict(cls, data):
        pre = data['preprocessor']
        result = cls(data['features'], pre['domains'], data['knots_months'], data['penalty'], data['tvc_penalty'])
        result.preprocessor = Preprocessor.from_dict(pre)
        result.coefficients = np.asarray(data['coefficients'], float)
        result.deltas = np.asarray(data['deltas'], float).reshape(len(result.knots), -1) if data['deltas'] else np.zeros((len(result.knots), 0))
        result.log_baseline = np.asarray(data['log_baseline'], float)
        result.wave_group = {int(k): v for k, v in data['wave_group'].items()}
        result.group_weights = np.asarray(data['group_weights'], float)
        result.shift = float(data['shift'])
        result.slope = float(data.get('slope', 1.))
        result.replicates = data.get('replicates', [])
        return result


# ---- evaluation under interval censoring ---------------------------------
def horizon_status(frame, horizon, straddle_lost=True):
    """Return (positive, negative, followup_time, lost_flag) for one horizon.

    Positive: a return is known by the horizon. Negative: event-free through the
    horizon (censored later, or the return interval starts at/after it). Unknown:
    censored earlier, or the return interval straddles the horizon.
    """
    left, right = frame['left_months'].to_numpy(float), frame['right_months'].to_numpy(float)
    event = frame['event'].to_numpy(int) == 1
    positive = event & (right <= horizon)
    negative = (~event & (right >= horizon)) | (event & (left >= horizon))
    straddle = event & (left < horizon) & (right > horizon)
    if not straddle_lost:  # upper bound: a return that began before the horizon may count
        return positive | straddle, negative, np.minimum(right, horizon), (~event & (right < horizon))
    lost = (~event & (right < horizon)) | straddle
    follow = np.where(straddle, left, right)
    return positive, negative, follow, lost


def censor_curves(frame, horizon, straddle_lost=True):
    """Kaplan-Meier curves for loss of information, stratified by baseline wave."""
    _, _, follow, lost = horizon_status(frame, horizon, straddle_lost)
    strata = frame['starting_wave'].to_numpy(int)
    pooled = _km(follow, lost)
    curves = {}
    for wave in np.unique(strata):
        mask = strata == wave
        curves[int(wave)] = _km(follow[mask], lost[mask]) if mask.sum() >= 50 else pooled
    return {'pooled': pooled, 'strata': curves}


def _km(follow, lost):
    times = np.unique(follow[lost]) if lost.any() else np.array([])
    survival, values = 1., []
    for time in times:
        at_risk = (follow >= time).sum()
        survival *= 1-((follow == time) & lost).sum()/at_risk
        values.append(survival)
    return np.asarray(times), np.asarray(values)


def _lookup(curve, t, strictly_before=False):
    times, values = curve
    if not len(times):
        return np.ones_like(np.asarray(t, float))
    idx = np.searchsorted(times, t, side='left' if strictly_before else 'right')-1
    return np.where(idx >= 0, values[np.clip(idx, 0, len(values)-1)], 1.)


def ipcw_weights(frame, horizon, curves, straddle_lost=True):
    positive, negative, follow, _ = horizon_status(frame, horizon, straddle_lost)
    strata = frame['starting_wave'].to_numpy(int)
    weights = np.zeros(len(frame))
    for wave in np.unique(strata):
        mask = strata == wave
        curve = curves['strata'].get(int(wave), curves['pooled'])
        at_event = _lookup(curve, follow[mask], strictly_before=True)
        at_horizon = _lookup(curve, np.full(mask.sum(), float(horizon)))
        weights[mask] = np.where(positive[mask], 1/np.maximum(at_event, 1e-12),
                                 np.where(negative[mask], 1/np.maximum(at_horizon, 1e-12), 0.))
    return weights, positive, negative


def _observed_upper(frame, horizon, curves_upper):
    weights, positive, _ = ipcw_weights(frame, horizon, curves_upper, straddle_lost=False)
    row_w = frame['row_weight'].to_numpy(float) if 'row_weight' in frame else np.ones(len(frame))
    if 'survey_weight' in frame.columns:
        row_w = row_w*frame['survey_weight'].to_numpy(float)
    return float(np.sum(weights*row_w*positive)/row_w.sum())


def _weighted_km(time, event, weight, horizon):
    """Weighted Kaplan-Meier cumulative incidence at ``horizon``."""
    survival = 1.
    for u in np.unique(time[event & (time <= horizon)]):
        at_risk = weight[time >= u].sum()
        survival *= 1-weight[(time == u) & event].sum()/at_risk
    return 1-survival


def observed_risk_range(frame, probabilities, horizon, row_weight, minimum_at_risk=25):
    """Observed risk by the horizon as a (lower, upper) range, plus the matching mean estimate.

    Product-limit estimates within each baseline-wave stratum, with each return
    placed at the end (lower) or the start (upper) of its interview interval, then
    averaged with person weights over strata that still have people at risk at the
    horizon. The mean estimate is taken over the same rows.
    """
    left, right = frame['left_months'].to_numpy(float), frame['right_months'].to_numpy(float)
    event = frame['event'].to_numpy(int) == 1
    strata = frame['starting_wave'].to_numpy(int)
    lower = upper = predicted = total = 0.
    for wave in np.unique(strata):
        mask = strata == wave
        if (right[mask] >= horizon).sum() < minimum_at_risk:
            continue
        w = row_weight[mask]
        lower += w.sum()*_weighted_km(right[mask], event[mask], w, horizon)
        upper += w.sum()*_weighted_km(np.where(event[mask], np.maximum(left[mask], 1e-9), right[mask]), event[mask], w, horizon)
        predicted += float(np.sum(w*probabilities[mask]))
        total += w.sum()
    if total == 0:
        return None
    return lower/total, upper/total, predicted/total


def horizon_metrics(frame, probabilities, horizon, curves, max_weight=20., curves_upper=None):
    from sklearn.metrics import average_precision_score, roc_auc_score
    weights, positive, negative = ipcw_weights(frame, horizon, curves)
    known = positive | negative
    unweighted_max = weights.max()
    probabilities = np.asarray(probabilities, float)
    if not known.any() or unweighted_max > max_weight or not positive.any():
        return {'supported': False, 'known_outcomes': int(known.sum())}
    row_w = frame['row_weight'].to_numpy(float) if 'row_weight' in frame else np.ones(len(frame))
    weights = weights*row_w
    if 'survey_weight' in frame.columns:  # optional weighted sensitivity analysis
        weights = weights*frame['survey_weight'].to_numpy(float)
        row_w = row_w*frame['survey_weight'].to_numpy(float)
    y, p, w = positive[known].astype(int), probabilities[known], weights[known]
    n = row_w.sum()
    observed = float(np.sum(weights*positive)/n)
    rng_obs = observed_risk_range(frame, probabilities, horizon, row_w)
    if rng_obs is None:
        return {'supported': False, 'known_outcomes': int(known.sum())}
    observed, upper, predicted = rng_obs
    mid = (observed+upper)/2
    return {'supported': True, 'known_outcomes': int(known.sum()), 'events_by_horizon': int(positive.sum()),
            'unresolved_at_horizon': int((~known).sum()),
            'ipcw_brier': float(np.sum(w*(y-p)**2)/n),
            'ipcw_roc_auc': float(roc_auc_score(y, p, sample_weight=w)) if len(np.unique(y)) == 2 else None,
            'ipcw_average_precision': float(average_precision_score(y, p, sample_weight=w)),
            'mean_predicted_risk': float(predicted),
            'observed_risk_lower': float(min(observed, upper)), 'observed_risk_upper': float(max(upper, observed)),
            'ipcw_observed_risk': float(mid),
            'predicted_within_observed_bounds': bool(min(observed, upper)-1e-9 <= predicted <= max(upper, observed)+1e-9),
            'calibration_ratio': float(predicted/mid) if mid > 0 else None,
            'maximum_censor_weight': float(weights.max()/max(row_w.max(), 1e-12))}
