# Known limitations of the frozen v2.1 model

Fixed in the application layer (this revision): out-of-profile and too-sparse
answers are suppressed; the 75% answer rule is enforced in the UI path;
unknown eligibility answers are detected by text, not position; short horizons
that fail to beat the no-input baseline are flagged; calibration wording is
computed per horizon; unreadable/incompatible model files show the safe error.

The items below live inside the frozen, fingerprinted model or its data and
cannot be fixed without a new, separately versioned run (v2.2) trained from the
raw PATH files. Do not edit `longitudinal.py` to "fix" them: `load_study`
verifies its hash against the manifest.

| Limitation | Effect | v2.2 remedy |
|---|---|---|
| Sample requires >=3 consecutive attended waves counted *after* a return | People who return then drop out are excluded; estimates describe a filtered group, not new users | Define the cohort from baseline plus at-risk time only; handle attrition by censoring |
| Interval-censored returns are timed at the observing wave's midpoint | Event times late by up to one wave gap (about 10-28 months); medians biased upward | Interval-censored survival likelihood |
| IPCW uses one marginal Kaplan-Meier censoring curve | Censoring is largely administrative and depends on baseline wave | Censoring model conditional on baseline wave |
| Model trained on wave 1-6 baselines; app encodes answers with the wave-7 mapping | Wording/coding drift is unchecked | Include wave 7 or verify mapping equivalence |
| One multiplicative calibration shift | Overestimates at 12 months (5.1% vs 3.0%), underestimates from 18 | Horizon-specific or flexible-baseline hazard |
| 12-month Brier 0.0311 vs 0.0305 for no-input baseline | No benefit at 12 months | Drop 12 months from display |
| SHAP background is 16 survey-derived rows | Noisy explanations; redistribution of survey-derived rows needs data-terms review | Larger aggregate background; confirm PATH/ICPSR terms |
| Hash manifest includes source files and sits beside them | Detects accidents only; `joblib` loading still executes pickled code | Load only trusted bundles; sign releases |
| Risk tertile cuts from 764 calibration participants | Unstable category boundaries | Cuts from larger development data |

Historical v1 files (`final_project_report.md`, viva questions, presentation
outline, the Oct-10 PPTX) describe the retired next-survey model. A v2.1 final
report and revised slide deck still need to be written by the team.
