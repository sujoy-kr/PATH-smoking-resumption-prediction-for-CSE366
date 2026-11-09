# Study protocol and results: v2.2 interval-censored survival model

v2.2 replaces v2.1 and corrects its design flaws. v2.1 files remain only as
history. Everything below is reproduced by `scripts/train_longitudinal_v2_2.py`
(byte-identical model on rerun) and checked by `scripts/verify_longitudinal_v2_2.py`.

## Question and population
Among adult former established smokers with no smoking in the past 30 days, how
likely is a first *reported* return to current established smoking (every-day or
some-day) by approximate month horizons? Not a clinical tool; not validated for
anyone outside this population.

## What changed from v2.1, and why
| v2.1 flaw | v2.2 fix |
|---|---|
| Required 3 consecutive attended waves, counting waves after a return (people who returned then dropped out were excluded) | Inclusion needs only a baseline plus one later known-status interview. Later attendance never affects inclusion. 9,593 people instead of 7,643 |
| Return timed at the observing wave's midpoint | Interval-censored likelihood: a return lies between the previous and observing interview |
| Weibull baseline + one shift; 12-month overestimated | Piecewise-exponential baseline hazard (knots 0/12/24/36/48 months) + maximum-likelihood calibration shift |
| IPCW from one marginal censoring curve | Loss-to-follow-up curves stratified by baseline wave; returns whose interval straddles the horizon are unresolved; observed risk reported as lower/upper bounds |
| Wave-1..6 baselines but wave-7 question coding in the app | Waves 1..7 are baselines |
| 12-month horizon shown although it did not beat the no-input baseline | A horizon is shown only if validation Brier beats a no-input baseline. 12 months fails and is dropped |
| Model selection on IPCW Brier | Selection on held-out interval-censored log-likelihood (a proper score) |
| 16 survey-derived rows in the bundle | Explanation background is 128 synthetic rows drawn independently from training marginals; no participant row ships |
| `model.joblib` (pickle) guarded by hashes that include source code | `model.json` (plain JSON). Hashes cover outputs only and detect accidents; no pickle is loaded; scikit-learn/scipy are no longer runtime dependencies |
| Risk tertiles from 764 calibration people | Tertiles of predicted 36-month risk over 6,714 development+calibration people |
| App and strict API disagreed | One path (`assess_available`); sparse or out-of-profile input is suppressed |

## Cohort and timing
Eligible baseline (waves 1-7): former established smoker, no past-30-day use,
not currently smoking. The earliest eligible baseline with a consecutive
later interview is used, one row per person. Follow-up continues through
consecutive attended waves until a first reported return, an unknown status, or
wave 8. 2,311 returns; 7,282 people had no observed return. Wave windows are in
`configs/longitudinal_v2_2.json`; interviews use window midpoints (sensitivity:
window start/end).

## Model
Proportional hazards, penalized, piecewise-constant baseline hazard, eight
baseline questionnaire inputs (compact profile selected; penalty 30). Split 60/15/10/15 by
participant: fit / selection / calibration / test. Test data are used once,
after every decision.

## Held-out results (1,440 test people, 347 returns)
| Months | ROC-AUC (95% bootstrap) | Brier model vs no-input | Mean estimate | Observed-risk range | Inside range |
|---|---|---|---|---|---|
| 18 | 0.736 (0.693-0.770) | 0.0909 vs 0.0970 | 16.2% | 10.4-19.6% | yes |
| 24 | 0.750 (0.713-0.780) | 0.1127 vs 0.1265 | 18.8% | 15.1-21.9% | yes |
| 36 | 0.781 (0.757-0.809) | 0.1179 vs 0.1412 | 22.4% | 18.1-23.1% | yes |
| 48 | 0.781 (0.751-0.808) | 0.1323 vs 0.1609 | 24.3% | 21.6-24.4% | yes |
| 60 | 0.790 (0.761-0.823) | 0.1357 vs 0.1681 | 25.4% | 23.1-25.1% | **no** (0.3 points above) |

Held-out log-likelihood per person: -0.692 (model) vs -0.770 (no-input).
Log-hazard shift the test sample would still need: +0.004 (calibrated in the
large). 12 months (not shown): validation Brier 0.0479 vs 0.0411 for no inputs.

## Remaining limitations (cannot be removed by modeling)
- Public-use PATH has only wave windows, not interview dates; times are approximate.
- A snapshot status misses returns that began and ended between interviews.
- A baseline needs at least one follow-up interview; people lost immediately
  are unobservable. Attrition after that is handled only by censoring and may be
  informative. IPCW assumes loss is noninformative given baseline wave.
- Under interval censoring, Brier/AUC use only people resolved at the horizon;
  calibration is therefore judged against bounds, and the proper likelihood score.
- Explanations use independent training marginals; correlated inputs are ignored.
- 60-month estimate sits just above its observed-risk upper bound.
- Unweighted U.S. sample; no personal-confidence measure; not clinical advice.
