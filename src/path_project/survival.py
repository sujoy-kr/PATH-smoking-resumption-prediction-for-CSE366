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
            blocks.append(np.log1p(filled)[:, None])
            blocks.append(missing[:, None].astype(float))
        return np.hstack(blocks) if blocks else np.zeros((len(frame), 0))

    def fit(self, frame):
        values = self._validated(frame)
        self.medians = {n: (float(values[n].median()) if values[n].notna().any() else 0.) for n in self.numeric}
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
                'means': self.means, 'scales': self.scales}

    @classmethod
    def from_dict(cls, data):
        result = cls(data['features'], data['domains'])
        result.medians, result.means, result.scales = data['medians'], data['means'], data['scales']
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
    def __init__(self, features, domains, knots_months, penalty=1.):
        self.features = list(features)
        self.preprocessor = Preprocessor(self.features, domains)
        self.knots_months = list(map(float, knots_months))
        self.knots = _bins(self.knots_months)
        self.penalty = float(penalty)
        self.coefficients = np.zeros(0)
        self.log_baseline = np.zeros(len(self.knots))
        self.shift = 0.

    # ---- fitting ------------------------------------------------------
    def _arrays(self, frame):
        left = frame['left_months'].to_numpy(float)/MONTHS_PER_YEAR
        right = frame['right_months'].to_numpy(float)/MONTHS_PER_YEAR
        event = frame['event'].to_numpy(int) == 1
        if (right <= 0).any() or (left < 0).any() or (left[event] >= right[event]).any():
            raise BoundaryError('Observation intervals must satisfy 0 <= left < right.')
        return left, right, event

    def _nll(self, eta, loglam, left, right, event, grads=False, design=None):
        lam = np.exp(loglam)
        el, er = exposure(left, self.knots), exposure(right, self.knots)
        scale = np.exp(eta)
        hl, hr = scale*(el@lam), scale*(er@lam)
        d = np.maximum(hr-hl, 1e-12)
        g = 1./np.expm1(d)
        ll = np.where(event, -hl+np.log(-np.expm1(-d)), -hr)
        value = -np.mean(ll)
        if not grads:
            return value
        dl = np.where(event, -1.-g, 0.)
        dr = np.where(event, g, -1.)
        d_eta = dl*hl+dr*hr
        d_log = (dl*scale)[:, None]*(el*lam[None, :])+(dr*scale)[:, None]*(er*lam[None, :])
        return value, -(design.T@d_eta)/len(eta), -d_log.sum(axis=0)/len(eta)

    def fit(self, frame):
        from scipy.optimize import minimize
        left, right, event = self._arrays(frame)
        design = self.preprocessor.fit(frame[self.features]).transform(frame[self.features])
        n, p = len(frame), design.shape[1]
        j = len(self.knots)
        total_time = max(right.sum(), 1e-9)
        start = np.r_[np.zeros(p), np.full(j, math.log(max(event.sum(), 1)/total_time))]

        def loss(theta):
            beta, loglam = theta[:p], theta[p:]
            value, g_beta, g_log = self._nll(design@beta, loglam, left, right, event, True, design)
            value += self.penalty*beta@beta/(2*n)
            g_beta = g_beta+self.penalty*beta/n
            return value, np.r_[g_beta, g_log]

        bounds = [(-6, 6)]*p+[(-12, 3)]*j
        fit = minimize(loss, start, jac=True, method='L-BFGS-B', bounds=bounds, options={'maxiter': 2000, 'ftol': 1e-12})
        if not fit.success:
            raise BoundaryError(f'Survival optimization failed: {fit.message}')
        self.coefficients, self.log_baseline = fit.x[:p], fit.x[p:]
        self.shift = 0.
        self.optimization = {'success': True, 'iterations': int(fit.nit), 'objective': float(fit.fun)}
        return self

    def log_likelihood(self, frame):
        left, right, event = self._arrays(frame)
        eta = self.log_rate(frame)
        return -self._nll(eta, self.log_baseline, left, right, event)*len(frame)

    def calibrate(self, frame):
        """Maximum-likelihood multiplicative hazard shift on calibration people only."""
        from scipy.optimize import minimize_scalar
        left, right, event = self._arrays(frame)
        eta = self.log_rate(frame)
        fit = minimize_scalar(lambda s: self._nll(eta+s, self.log_baseline, left, right, event), bounds=(-2, 2), method='bounded')
        self.shift += float(fit.x)
        return float(fit.x)

    def likelihood_shift(self, frame):
        """Log-hazard shift a sample would need (0 means calibrated in the large)."""
        from scipy.optimize import minimize_scalar
        left, right, event = self._arrays(frame)
        eta = self.log_rate(frame)
        return float(minimize_scalar(lambda s: self._nll(eta+s, self.log_baseline, left, right, event), bounds=(-3, 3), method='bounded').x)

    def mean_log_likelihood(self, frame):
        """Held-out interval-censored log-likelihood per person (proper score)."""
        left, right, event = self._arrays(frame)
        return float(-self._nll(self.log_rate(frame), self.log_baseline, left, right, event))

    # ---- prediction ---------------------------------------------------
    def log_rate(self, frame):
        design = self.preprocessor.transform(frame[self.features])
        return design@self.coefficients+self.shift

    def cumulative_baseline(self, months):
        t = np.asarray(months, float)/MONTHS_PER_YEAR
        return exposure(t, self.knots)@np.exp(self.log_baseline)

    def risk(self, frame, months):
        times = np.atleast_1d(np.asarray(months, float))
        if not np.isfinite(times).all() or (times < 0).any():
            raise BoundaryError('Horizons must be finite nonnegative months.')
        hazard = np.exp(self.log_rate(frame))[:, None]*self.cumulative_baseline(times)[None, :]
        return -np.expm1(-hazard)

    def _invert(self, frame, target):
        """Months at which cumulative hazard reaches ``target`` (scalar or per row)."""
        eta = np.exp(self.log_rate(frame))
        need = np.broadcast_to(np.asarray(target, float), eta.shape)/eta
        lam = np.exp(self.log_baseline)
        starts = np.r_[0., np.cumsum(lam[:-1]*np.diff(self.knots))]
        index = np.clip(np.searchsorted(starts, need, side='right')-1, 0, len(lam)-1)
        years = self.knots[index]+(need-starts[index])/lam[index]
        return years*MONTHS_PER_YEAR

    def median_months(self, frame):
        return self._invert(frame, math.log(2.))

    def conditional_median(self, frame, maximum):
        """Median first-return time given a return occurs by ``maximum`` months."""
        p = self.risk(frame, [maximum])[:, 0]
        return self._invert(frame, -np.log1p(-p/2))

    # ---- serialization ------------------------------------------------
    def to_dict(self):
        return {'features': self.features, 'knots_months': self.knots_months, 'penalty': self.penalty,
                'coefficients': self.coefficients.tolist(), 'log_baseline': self.log_baseline.tolist(),
                'shift': self.shift, 'preprocessor': self.preprocessor.to_dict()}

    @classmethod
    def from_dict(cls, data):
        pre = data['preprocessor']
        result = cls(data['features'], pre['domains'], data['knots_months'], data['penalty'])
        result.preprocessor = Preprocessor.from_dict(pre)
        result.coefficients = np.asarray(data['coefficients'], float)
        result.log_baseline = np.asarray(data['log_baseline'], float)
        result.shift = float(data['shift'])
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
    return float(np.sum(weights*positive)/len(frame))


def horizon_metrics(frame, probabilities, horizon, curves, max_weight=20., curves_upper=None):
    from sklearn.metrics import average_precision_score, roc_auc_score
    weights, positive, negative = ipcw_weights(frame, horizon, curves)
    known = positive | negative
    probabilities = np.asarray(probabilities, float)
    if not known.any() or weights.max() > max_weight or not positive.any():
        return {'supported': False, 'known_outcomes': int(known.sum())}
    y, p, w = positive[known].astype(int), probabilities[known], weights[known]
    n = len(frame)
    observed = float(np.sum(weights*positive)/n)
    upper = _observed_upper(frame, horizon, curves_upper) if curves_upper is not None else observed
    mid = (observed+upper)/2
    return {'supported': True, 'known_outcomes': int(known.sum()), 'events_by_horizon': int(positive.sum()),
            'unresolved_at_horizon': int((~known).sum()),
            'ipcw_brier': float(np.sum(w*(y-p)**2)/n),
            'ipcw_roc_auc': float(roc_auc_score(y, p, sample_weight=w)) if len(np.unique(y)) == 2 else None,
            'ipcw_average_precision': float(average_precision_score(y, p, sample_weight=w)),
            'mean_predicted_risk': float(probabilities.mean()),
            'observed_risk_lower': observed, 'observed_risk_upper': float(max(upper, observed)),
            'ipcw_observed_risk': float(mid),
            'predicted_within_observed_bounds': bool(observed-1e-9 <= probabilities.mean() <= max(upper, observed)+1e-9),
            'calibration_ratio': float(probabilities.mean()/mid) if mid > 0 else None,
            'maximum_censor_weight': float(weights.max())}
