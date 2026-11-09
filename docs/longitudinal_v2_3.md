# Study protocol and results: v2.3 multi-population survival models

v2.3 extends v2.2 so the app answers for **any adult**, using the PATH adult files
(waves 1-8) instead of refusing people outside the former-smoker group. v2.2 and
v2.1 are history. Reproduce with `scripts/train_longitudinal_v2_3.py`
(byte-identical rerun); verify with `scripts/verify_longitudinal_v2_3.py --rebuild-cohort`.

## Populations, events and routing
The four profile questions choose the model. Each person is scored only by the model
fitted on people in their situation.

| Answers | Model | Event (first reported at a later interview) |
|---|---|---|
| 100+ cigarettes, now "Not at all" (any time since last cigarette) | Former | current established smoking (every/some day) |
| 100+ cigarettes, now "Every day"/"Some days" | Current | not smoking every/some day (a stop that may be temporary) |
| Fewer than 100 cigarettes | Never-established | current established smoking |
| Under 18 | not covered | PATH adult files contain no minors |

A result is withheld only for: under 18, a profile that cannot be routed
("don't know" on the 100-cigarette or current-smoking question), contradictory
answers (past-30-day smoking versus time since last cigarette), or fewer than
75% of the model's answers (and, for former smokers, no last-cigarette time).

| Population | People | Events | Features | Shown horizons |
|---|---|---|---|---|
| Former smokers → return to smoking | 10,412 | 3,058 | 8 (compact) | 18, 24, 36, 48, 60 |
| Current smokers → stopping | 14,258 | 5,724 | 10 (extended) | 18, 24, 36, 48, 60 |
| Not yet 100 cigarettes → becoming a regular smoker | 28,604 | 2,092 | 10 (extended) | 12, 18, 24, 36, 48, 60 |

## Method (all three models)
Baselines at waves 1-7 (earliest eligible, one row per person, at least one later
known-status interview; later attendance never affects inclusion). Interval-censored
penalized proportional-hazards model with a piecewise-exponential baseline
(knots 0/12/24/36/48 months). Participant-level 60/15/10/15 split. Profile and
penalty chosen on validation log-likelihood; a horizon is shown only if validation Brier
beats a no-input baseline. Final fit uses all non-test people; the calibration shift
comes from 5-fold out-of-fold predictions; the test set is scored once. Explanations
are exact Shapley values over synthetic, independent training marginals.

## Held-out results
| Model | Months | ROC-AUC (95%) | Brier model vs no inputs | Mean estimate | Observed range | Inside |
|---|---|---|---|---|---|---|
| Former smokers → return to smoking | 18 | 0.791 (0.755–0.824) | 0.1047 vs 0.1195 | 21.9% | 13.1–24.8% | yes |
| Former smokers → return to smoking | 24 | 0.801 (0.775–0.827) | 0.1245 vs 0.1536 | 24.5% | 19.4–26.5% | yes |
| Former smokers → return to smoking | 36 | 0.815 (0.788–0.839) | 0.1320 vs 0.1719 | 28.3% | 24.0–28.1% | **no** |
| Former smokers → return to smoking | 48 | 0.814 (0.786–0.837) | 0.1395 vs 0.1830 | 30.5% | 26.7–29.4% | **no** |
| Former smokers → return to smoking | 60 | 0.812 (0.787–0.837) | 0.1443 vs 0.1893 | 31.5% | 28.1–29.6% | **no** |
| Current smokers → stopping | 18 | 0.670 (0.636–0.706) | 0.0996 vs 0.1044 | 19.0% | 10.9–22.3% | yes |
| Current smokers → stopping | 24 | 0.671 (0.643–0.702) | 0.1430 vs 0.1530 | 23.3% | 18.9–28.6% | yes |
| Current smokers → stopping | 36 | 0.689 (0.659–0.713) | 0.1544 vs 0.1689 | 29.3% | 21.5–30.5% | yes |
| Current smokers → stopping | 48 | 0.679 (0.653–0.708) | 0.1801 vs 0.1979 | 34.4% | 27.5–36.2% | yes |
| Current smokers → stopping | 60 | 0.686 (0.659–0.716) | 0.1893 vs 0.2098 | 38.9% | 30.5–38.1% | **no** |
| Not yet 100 cigarettes → becoming a regular smoker | 12 | 0.796 (0.747–0.844) | 0.0233 vs 0.0249 | 3.7% | 2.5–4.8% | yes |
| Not yet 100 cigarettes → becoming a regular smoker | 18 | 0.793 (0.748–0.841) | 0.0272 vs 0.0292 | 4.5% | 3.0–5.1% | yes |
| Not yet 100 cigarettes → becoming a regular smoker | 24 | 0.789 (0.754–0.825) | 0.0399 vs 0.0439 | 5.2% | 4.6–6.2% | yes |
| Not yet 100 cigarettes → becoming a regular smoker | 36 | 0.782 (0.745–0.817) | 0.0430 vs 0.0475 | 6.1% | 5.1–6.4% | yes |
| Not yet 100 cigarettes → becoming a regular smoker | 48 | 0.785 (0.759–0.820) | 0.0494 vs 0.0555 | 6.9% | 6.0–7.2% | yes |
| Not yet 100 cigarettes → becoming a regular smoker | 60 | 0.781 (0.747–0.810) | 0.0520 vs 0.0588 | 7.4% | 6.4–7.5% | yes |

Observed risk under interval censoring is a range (returns known by the horizon;
plus returns that began before it). "Inside" says whether the mean estimate falls in it.

## Limitations
- The current-smoker model discriminates only modestly (ROC-AUC about 0.68): PATH
  variables such as cigarettes per day are not in this feature mapping. Its stop
  event can be temporary.
- Former-smoker estimates at 36-60 months run 1-2 points above the observed range.
- Interview dates are unavailable (wave midpoints); snapshot statuses miss short episodes.
- Attrition after the first follow-up may be informative; explanations assume independent inputs.
- Unweighted U.S. adult sample; no validated personal confidence; not clinical advice.
- Under-18s are not covered.
