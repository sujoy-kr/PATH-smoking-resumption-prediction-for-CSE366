# Faculty presentation guide — current v2.4 interval-censored model

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

**Who is covered?** Any adult: former smokers, current smokers and adults with fewer
than 100 lifetime cigarettes, each with its own model (about 10,400 / 14,300 / 28,600
people). Under-18s are not covered because the adult PATH files contain no minors.

**What is predicted?** Former smokers: first reported return to current smoking. Current
smokers: first reported stopping (may be temporary). Never-established: first reported
current established smoking. Not exact dates or lasting change.

**How did you use the data more efficiently?** 29 candidate inputs (up from 11) with
greedy selection on validation; one row per state entry (more people-time without
survivor bias); a baseline hazard per survey period; weighted and subgroup checks.
Reusing every wave for the same unbroken stay was tried and rejected: it overpredicted.

**What performance can be claimed?** 36-month ROC-AUC 0.82 (former), 0.78 (current;
0.69 before the extra smoking-dependence inputs), 0.77 (never-established); every shown horizon
beats a no-input model. Honest caveat: for former and current smokers the mean estimate at
36+ months is above a simple Kaplan-Meier observed range even though likelihood-based
calibration checks look fine, so absolute percentages may be somewhat high. The cause is unresolved.

**What are the uncertainty ranges?** 95% ranges from 100 bootstrap refits: sampling
uncertainty of the fitted model only, not individual outcome randomness.

**How sure is an individual prediction?** Personal confidence is not validated. The app
withholds a result only for under-18s, un-routable or contradictory answers, or too few answers.

**Where do predictions come from?** `artifacts/longitudinal_v2_4/model.json`, plain
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
