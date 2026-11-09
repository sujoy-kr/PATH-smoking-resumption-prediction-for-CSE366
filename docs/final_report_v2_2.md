# Predicting a first reported return to smoking among former smokers (PATH Study)

CSE366 course project. Final model: v2.2. Protocol, tables and limitations:
[longitudinal_v2_2.md](longitudinal_v2_2.md). This report makes no clinical,
causal or national-representativeness claim.

**Data.** PATH Study adult public-use files, waves 1-8. 9,593 former established
smokers (no smoking in the past 30 days at baseline) with at least one
follow-up interview; 2,311 reported returning to current established smoking.

**Method.** Participant-level 60/15/10/15 split. Penalized proportional-hazards
model with a piecewise-exponential baseline and an interval-censored likelihood,
using eight baseline answers. Inputs, profile, penalty and shown horizons were
chosen on validation data; one calibration shift was fitted on separate
calibration people; the test set was scored once.

**Results.** At 36 months: held-out ROC-AUC 0.781 (95% interval 0.757-0.809),
Brier 0.118 vs 0.141 for a model without inputs, mean estimate 22.4% against an
observed-risk range of 18.1-23.1%. Horizons shown: 18, 24, 36, 48 and 60
months. 12 months is not shown because the model did not beat the no-input
baseline there.

**Interpretation.** Inputs rank people moderately well at the group level. The
app shows percentages as approximate; it does not claim personal confidence.
Answers outside the study population or with too few inputs get no probability.

**Limitations.** See the protocol: approximate timing, snapshot outcomes,
possibly informative attrition, independence assumed in explanations, unweighted
U.S. sample. Earlier v1 (next-survey) and v2.1 reports are historical.
