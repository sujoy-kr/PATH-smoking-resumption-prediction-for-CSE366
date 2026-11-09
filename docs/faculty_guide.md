# Faculty presentation guide — current consecutive-wave model

This guide describes the active model. Restored reports and presentation notes
for the older next-survey classifier are historical references.

## What to demonstrate

1. Run `python run_app.py` using the configured environment. Its startup check
   compares five fictional profiles with the included trained model.
2. Show the eight-question form and one clearly labeled fictional example.
3. Explain the automatically displayed 12/18/24/36/48/60-month cumulative risks.
4. Show the 36-month relative risk group and contributing factors for the same
   probability. Contributions plus the model reference equal the displayed risk.
5. Explain timing and reliability limitations. Unknown/unsupported profiles are
   suppression of out-of-profile or too-sparse answers; a blank assessment shows the no-input study reference.

## Questions to be ready for

**Who is in the dataset?** 7,643 former established smokers with at least three
consecutive adult survey appearances from an eligible starting interview. There
are 1,939 first observed returns to current established smoking and 5,704 without
an observed return before follow-up ended.

**What is being predicted?** First reported current established smoking after
baseline, meaning every-day or some-day smoking. This is not an exact
first-cigarette date or proof of permanent relapse.

**How are months obtained?** Differences between survey-window midpoints.
Individual interview dates and actual resumption times are unavailable. Month
outputs depend on this clock and a parametric survival assumption.

**Why a survival model?** It incorporates variable observation duration and
participants whose follow-up ends without an observed return. Those participants
are not treated as known permanent abstainers. Censoring and attendance-selection
assumptions can still be wrong.

**How was leakage controlled?** One origin per participant, baseline answers
only, disjoint fitting/selection/calibration/test participants. Transformations
are fitted in development only; final test results do not guide retuning.

**What was selected?** An eight-input penalized Weibull model, comparing eight
and eleven inputs, exponential/Weibull shape and two penalties. See the current
protocol for the selection rule and preserved validation results.

**What performance can be claimed?** Held-out 18-month ROC-AUC 0.7461 and Brier
0.0809; 36-month ROC-AUC 0.7764 and Brier 0.1269. AUC is ranking performance, not
“percent accurate” or personal confidence. At 36 months the mean prediction was
13.61% versus 17.26% censor-adjusted observed risk: calibration underestimates risk.

**How sure is an individual prediction?** Personal confidence has not been
validated. The app distinguishes input completeness, profile support and group
test evidence. Out-of-profile profiles are suppressed; accuracy for partial answers is unvalidated. At 12 months the model did not beat the no-input baseline (Brier 0.0311 vs 0.0305) and overestimates risk (5.1% vs 3.0%); 36-month risk is underestimated (13.6% vs 17.3%).

**Where do predictions come from?** The included frozen model in
`artifacts/longitudinal_v2_1/model.joblib`, not a live search through survey rows.
It includes preprocessing/calibration and sixteen survey-derived reference
records for explanations. Raw PATH files and processed histories are excluded
from the handoff; runtime answers remain in session memory.

**Can someone reproduce the demo?** Yes, using the matching bundle and pinned
dependencies, subject to the startup numerical tolerances. The current test
suite runs without raw data. Full cohort rebuilding uses the preserved local
PATH files and is a separate verification step.

Detailed evidence: [protocol](longitudinal_v2.md),
[results](../reports/longitudinal_v2_1/results.json),
[cohort summary](../reports/longitudinal_v2_1/summary.json) and
[research reference index](RESEARCH_GUIDE.md).
