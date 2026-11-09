# Faculty presentation guide — current v2.2 interval-censored model

This guide describes the active model. Restored reports and presentation notes
for the older next-survey classifier are historical references.

## What to demonstrate

1. Run `python run_app.py` using the configured environment. Its startup check
   compares five fictional profiles with the included trained model.
2. Show the eight-question form and one clearly labeled fictional example.
3. Explain the automatically displayed 18/24/36/48/60-month cumulative risks.
4. Show the 36-month relative risk group and contributing factors for the same
   probability. Contributions plus the model reference equal the displayed risk.
5. Explain timing and reliability limitations. Unknown/unsupported profiles are
   suppression of out-of-profile or too-sparse answers; a blank assessment shows the no-input study reference.

## Questions to be ready for

**Who is in the dataset?** 9,593 former established smokers with an eligible baseline and at
least one follow-up interview. There are 2,311 first reported returns and 7,282
without an observed return before follow-up ended.

**What is being predicted?** First reported current established smoking after
baseline, meaning every-day or some-day smoking. This is not an exact
first-cigarette date or proof of permanent relapse.

**How are months obtained?** Interval-censored: a return lies between two interviews; interview times are window midpoints.
Individual interview dates and actual resumption times are unavailable. Month
outputs depend on this clock and a parametric survival assumption.

**Why a survival model?** It incorporates variable observation duration and
participants whose follow-up ends without an observed return. Those participants
are not treated as known permanent abstainers. Censoring and attendance-selection
assumptions can still be wrong.

**How was leakage controlled?** One origin per participant, baseline answers
only, disjoint fitting/selection/calibration/test participants. Transformations
are fitted in development only; final test results do not guide retuning.

**What was selected?** An eight-input penalized proportional-hazards model with a
piecewise-exponential baseline and an interval-censored likelihood, chosen by
held-out log-likelihood over two input sets and three penalties. See
[longitudinal_v2_2.md](longitudinal_v2_2.md).

**What performance can be claimed?** Held-out ROC-AUC 0.736 (18 months), 0.781
(36 months, 95% interval 0.757-0.809) and 0.790 (60 months); Brier at 36 months
0.118 vs 0.141 without inputs. At 36 months the mean estimate was 22.4% against an
observed-risk range of 18.1-23.1%; at 60 months the estimate (25.4%) is 0.3 points
above its range. AUC is ranking performance, not "percent accurate" or personal
confidence. The 12-month horizon is not shown because it did not beat a
no-input baseline.

**How sure is an individual prediction?** Personal confidence has not been
validated. Out-of-profile or too-sparse answers get no probability.

**Where do predictions come from?** `artifacts/longitudinal_v2_2/model.json`, plain
JSON coefficients and preprocessing parameters; no pickle and no participant
rows (explanations use synthetic independent draws from training marginals).

**Can someone reproduce the demo?** Yes, using the matching bundle and pinned
dependencies, subject to the startup numerical tolerances. The current test
suite runs without raw data. Full cohort rebuilding uses the preserved local
PATH files and is a separate verification step.

Detailed evidence: [protocol](longitudinal_v2.md),
[results](../reports/longitudinal_v2_1/results.json),
[cohort summary](../reports/longitudinal_v2_1/summary.json) and
[research reference index](RESEARCH_GUIDE.md).
