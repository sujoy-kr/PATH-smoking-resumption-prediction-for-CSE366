# Study protocol and results: v2.4

v2.4 extends v2.3 (any adult, three population models) with more PATH data and checks.
Reproduce with `scripts/train_longitudinal_v2_4.py` (about 7 minutes); verify with
`scripts/verify_longitudinal_v2_4.py --rebuild-cohort`. v2.1–v2.3 are history.

## What changed in v2.4
| Item | Change |
|---|---|
| More inputs | Candidate pool grew from 11 to 29: sex, other tobacco products, depression/anxiety history, alcohol, past smoking pattern, plus (current smokers) cigarettes per day, time to first cigarette, quit attempts and plans, self-rated addiction. Groups are added greedily only if they raise held-out likelihood by at least 0.0005; the app asks only for the selected ones |
| More rows | One row per **state entry** (first interview, or after leaving and re-entering a state, or after a skipped wave). Unbroken stays contribute only the entry interview, because later interviews of the same stretch are survivor-biased (a trial that reused every wave overpredicted and was dropped) |
| Baseline hazard | Stratified by baseline wave group (survey period), shared covariate effects; new app users get the average over periods |
| Effects over time | Time-varying effects (shrunk toward proportional hazards) are candidates; chosen by validation (selected for never-smokers only) |
| Flexible numbers | Numeric inputs use piecewise-linear terms on the log scale |
| Calibration | Shift and slope fitted on 5-fold out-of-fold predictions (folds by person) |
| Uncertainty ranges | 100 bootstrap refits per model (participant-level resampling); the app shows the 2.5–97.5 percentile range for the probability and every horizon |
| Subgroups | Sex, age group and education reported (below) |
| Survey weights | Weighted sensitivity check, limited to baseline waves 1–2: the supplied PATH files contain weights only for those waves |

## Data
| Population | People | Baseline rows | Events | Inputs selected | Horizons shown |
|---|---|---|---|---|---|
| Former smokers → return to smoking | 10,412 | 11,917 | 3,068 | 12 (11 groups) | 12, 18, 24, 36, 48, 60 |
| Current smokers → stopping | 14,258 | 16,341 | 5,837 | 14 (12 groups) | 12, 18, 24, 36, 48, 60 |
| <100 cigarettes → becoming a regular smoker | 28,604 | 29,803 | 2,110 | 17 (11 groups) | 12, 18, 24, 36, 48, 60 |

## Input selection
| Population | Added input groups (by validation) | Validation log-likelihood: core inputs → final |
|---|---|---|
| Former smokers → return to smoking | smoking_history, home_rules, social | -0.7294 → -0.7233 |
| Current smokers → stopping | dependence, smoking_duration, quit_behaviour, addiction, home_rules | -1.1209 → -1.0646 |
| <100 cigarettes → becoming a regular smoker | alcohol, home_rules, sex, other_tobacco | -0.3022 → -0.2961 |

## Held-out results (test participants, scored once)
| Model | Months | ROC-AUC (95%) | Brier model vs no inputs | Mean estimate | Observed-risk range | Inside |
|---|---|---|---|---|---|---|
| Former smokers → return to smoking | 12 | 0.796 (0.744–0.846) | 0.0527 vs 0.0575 | 16.1% | 3.4–18.0% | yes |
| Former smokers → return to smoking | 18 | 0.841 (0.811–0.868) | 0.0859 vs 0.0973 | 19.7% | 10.8–20.1% | yes |
| Former smokers → return to smoking | 24 | 0.810 (0.783–0.836) | 0.1102 vs 0.1315 | 23.2% | 15.7–21.5% | **no** |
| Former smokers → return to smoking | 36 | 0.820 (0.796–0.843) | 0.1164 vs 0.1440 | 26.6% | 19.4–23.3% | **no** |
| Former smokers → return to smoking | 48 | 0.828 (0.805–0.849) | 0.1214 vs 0.1540 | 28.8% | 23.0–25.0% | **no** |
| Former smokers → return to smoking | 60 | 0.839 (0.818–0.863) | 0.1204 vs 0.1551 | 29.8% | 24.3–25.6% | **no** |
| Current smokers → stopping | 12 | 0.675 (0.632–0.719) | 0.0663 vs 0.0722 | 15.1% | 6.1–18.7% | yes |
| Current smokers → stopping | 18 | 0.756 (0.729–0.784) | 0.0902 vs 0.1009 | 20.1% | 10.0–20.6% | yes |
| Current smokers → stopping | 24 | 0.755 (0.728–0.781) | 0.1217 vs 0.1443 | 24.2% | 16.6–25.0% | yes |
| Current smokers → stopping | 36 | 0.781 (0.758–0.807) | 0.1305 vs 0.1533 | 30.3% | 19.0–26.2% | **no** |
| Current smokers → stopping | 48 | 0.773 (0.748–0.795) | 0.1486 vs 0.1774 | 35.0% | 24.8–31.5% | **no** |
| Current smokers → stopping | 60 | 0.785 (0.762–0.808) | 0.1551 vs 0.1871 | 40.2% | 28.5–33.4% | **no** |
| <100 cigarettes → becoming a regular smoker | 12 | 0.900 (0.868–0.924) | 0.0197 vs 0.0219 | 3.2% | 2.3–4.9% | yes |
| <100 cigarettes → becoming a regular smoker | 18 | 0.863 (0.830–0.890) | 0.0255 vs 0.0284 | 4.1% | 3.0–5.4% | yes |
| <100 cigarettes → becoming a regular smoker | 24 | 0.822 (0.794–0.852) | 0.0391 vs 0.0439 | 5.4% | 5.1–6.7% | yes |
| <100 cigarettes → becoming a regular smoker | 36 | 0.771 (0.735–0.808) | 0.0439 vs 0.0493 | 6.9% | 6.3–7.6% | yes |
| <100 cigarettes → becoming a regular smoker | 48 | 0.777 (0.749–0.810) | 0.0519 vs 0.0586 | 7.8% | 7.6–8.1% | yes |
| <100 cigarettes → becoming a regular smoker | 60 | 0.788 (0.762–0.813) | 0.0541 vs 0.0614 | 8.3% | 8.0–8.3% | **no** |

Held-out log-likelihood per person (model vs no inputs): former -0.726 vs -0.827; current -1.069 vs -1.151; never -0.297 vs -0.330.
Versus v2.3 (36 months, ROC-AUC): former 0.815 → 0.820; current 0.689 → 0.781; never 0.782 → 0.771.

## Calibration: what is and is not established
- **Likelihood-based** (proper under interval censoring): the shift each model would still need on the test sample is small (former -0.01, current -0.08, never +0.02 log-hazard). By risk quarter the current and never-smoker models need almost none; for former smokers only the lowest-risk quarter was over-predicted (shift about -0.2 after flexible numeric terms, -0.7 before).
- **Observed-risk range** (Kaplan–Meier by baseline wave, each return placed at the end or start of its interview interval): never-smokers fall inside the range at most horizons. For **former and current smokers the mean estimate at 24–60 months is above the range** (by roughly 3–7 points at 36 months). The likelihood checks above do not show this, so the cause (loss to follow-up related to risk, or baseline-hazard shape) is unresolved. Practical reading: *rankings and comparisons are reliable; absolute percentages for these two groups at 36+ months may be somewhat high.* The app states this next to every result.

## Uncertainty ranges
- Former smokers → return to smoking: mean 95% range width at 36 months 10.4 percentage points
- Current smokers → stopping: mean 95% range width at 36 months 9.2 percentage points
- <100 cigarettes → becoming a regular smoker: mean 95% range width at 36 months 4.0 percentage points
They reflect sampling uncertainty of the fitted model only (not individual outcome randomness or model misspecification).

## Subgroups (ROC-AUC at 36 months, test participants; groups under 150 people omitted)
- Former smokers → return to smoking: sex: AUC 0.80–0.84 across 2 groups; age: AUC 0.62–0.95 across 6 groups; education: AUC 0.79–0.83 across 4 groups
- Current smokers → stopping: sex: AUC 0.78–0.78 across 2 groups; age: AUC 0.71–0.82 across 6 groups; education: AUC 0.75–0.79 across 5 groups
- <100 cigarettes → becoming a regular smoker: sex: AUC 0.75–0.79 across 2 groups; age: AUC 0.70–0.91 across 6 groups; education: AUC 0.70–0.87 across 4 groups
Calibration against the observed-risk range by subgroup is in `reports/longitudinal_v2_4/results.json` (`subgroups_at_default_horizon`); the pattern matches the overall one.

## Survey-weighted sensitivity (36 months)
- Former smokers → return to smoking: 828 test people with wave 1–2 baselines; weighted ROC-AUC 0.917; weighted mean estimate 15.0% vs observed range 8.9–10.5%
- Current smokers → stopping: 1,592 test people with wave 1–2 baselines; weighted ROC-AUC 0.763; weighted mean estimate 26.4% vs observed range 17.8–23.1%
- <100 cigarettes → becoming a regular smoker: 2,147 test people with wave 1–2 baselines; weighted ROC-AUC 0.822; weighted mean estimate 7.2% vs observed range 3.9–4.4%
Cross-sectional adult weights of baseline waves 1–2 only; attrition is handled by IPCW, not weights, so this is a sensitivity check, not a national estimate. Weights for waves 3–8 would have to be added from the full PATH release.

## Limitations
- Estimates for former and current smokers at 36+ months may be high (above).
- Current-smoker discrimination is moderate (ROC-AUC about 0.78); "stopping" can be temporary.
- Interview dates are unavailable (wave midpoints); snapshot statuses miss short episodes.
- Attrition after the first follow-up may be informative; explanations assume independent inputs and are exact over input groups.
- Unweighted U.S. adult sample (weighted check only for waves 1–2); no validated personal confidence; not clinical advice; under-18s not covered.
