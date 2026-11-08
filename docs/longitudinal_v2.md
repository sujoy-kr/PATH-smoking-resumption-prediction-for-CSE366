# Consecutive-wave smoking-return extension (v2.1)

This is a separately trained study requested after completion of v1. It adds
approximate calendar horizons to a **first observed return to current established
smoking** endpoint. It does not validate actual first-cigarette/resumption dates.
The current app uses only this model; the original next-survey interface has
been retired from navigation. Original v1 cohorts, memberships, fitted artifacts and
evaluation results remain unchanged.

## Population and outcome

Use one canonical adult file per main wave and link lexical PERSONID strings.
Include a person with an eligible origin followed by at least two more consecutive
attended waves, for a run of 3–8 interviews. Never bridge a missing main wave.
For each person, select the earliest such origin: official former-established
smoking=Yes, past-30-day use=No, current-established smoking=No. Eligibility is a
documented established-smoking proxy (lifetime threshold and current status), not
a measured guarantee of a previously permanent/regular habit or a successful
permanent quit. A preceding observed smoking interview is not required.

At follow-up, an event is the first official current-established smoking=Yes
(currently every day or some days). Thus this endpoint differs from v1's any
past-30-day use. Record its observation wave, not an inferred first cigarette.
Stop at the first unknown current status or the end of the uninterrupted run if
no event occurs. Such people contribute right-censored **observation** time, not
an assumed permanent negative outcome. Future answers determine outcomes only;
baseline features never use them. Attendance-based selection uses future
participation and can bias the sample. It is not an input required from app users.

There are **7,643 unique people**, **1,939 observed returns**, and **5,704 with no
return observed before follow-up ended**. Baseline run lengths: 3=1,826; 4=1,313;
5=1,351; 6=737; 7=706; 8=1,710. All follow-up current statuses in the selected
corrected sample were valid until an event or run end. Missing interview gaps
still end a run. These are unweighted descriptive counts.

## Approximate clock and interpretation

Collection windows come from the [FDA PATH page](https://www.fda.gov/tobacco-products/research/fda-and-nih-study-population-assessment-tobacco-and-health).
Month-only source windows are expanded to the first/last calendar day of the
listed months. Every interview is assigned the midpoint of its wave window.
Approximate months are day differences divided by 365.25/12. An event is assigned
its first positive observation's midpoint; censoring uses the last valid
observation midpoint. Individual interview dates and actual event dates are not
available in these files. Time origin is the baseline interview midpoint, not
the historical quit date. No last-cigarette recency is substituted for follow-up.

The displayed probability is first **reported/observed current-established
smoking** by an approximate horizon (12, 18, 24, 36, 48 or 60 months), under an
assumed continuous parametric observation-time model. Collection-window dates
do not establish that an individual event occurred within a particular month
threshold. Interpolation between scheduled observations is model-based. A
negative snapshot does not prove continuous abstinence; a positive snapshot
does not prove persistent smoking. The first observed event can follow earlier
unobserved quit/resume episodes. Do not describe this as precise actual
time-to-relapse prediction, even when the UI displays whole months.

If modeled risk reaches 50% within the supported window, show its median time.
Otherwise explicitly state that no median is reached. Separately show the
median conditional on an observation occurring by 60 months, labeled with that
condition. A low-risk person is not told that a return is likely merely because
the conditional timing can be computed. No prediction beyond 60 months is shown.

The report includes evaluations using all window starts and all window ends as
alternative clocks, holding predictions fixed. These assess sensitivity of
horizon labels; they are not bounds on individual timing and do not include
every possible combination of individual interview dates.

## Training and questionnaire

One row per person, stratified by observed event, seeded disjoint splits:

| Split | People | Observed returns |
|---|---:|---:|
| Training | 4,585 | 1,163 |
| Model selection | 1,146 | 291 |
| Calibration | 764 | 194 |
| Held-out test | 1,148 | 291 |

This is a new protocol and split, not a reuse of the closed v1 test for v1
tuning. Some participants therefore change research roles between the two
separate studies. Do not treat their performance estimates as independent
replications. No class balancing, row duplication or synthetic observations are
introduced. Both event and censored participants enter the likelihood at their
observed frequencies. An artificially balanced evaluation would misstate risk.

Fit penalized exponential and Weibull proportional-hazard models with penalties
1 and 10 for eight-input and eleven-input profiles. All transforms are fitted
on the fitting partition only: categorical missing level and one-hot encoding;
median imputation, missing indicators, log1p and standardization for recency.
Select by mean validation inverse-probability-of-censoring-weighted (IPCW) Brier
score at 18/36/60 months. Prefer eight questions if its score is within 0.002
of the best eleven-question candidate. Refit only the selected specification on
training+selection, then fit a single cumulative-hazard multiplier on the
independent calibration partition. Freeze it before final test evaluation.

Eight questions won validation: age band, education, employment, time since last
cigarette, past-30-day electronic nicotine use, household tobacco/nicotine use,
general mental health, and emotional problems in the past seven days. The chosen
Weibull model has penalty 10 and fitted shape approximately 0.991. These inputs
are a validated profile comparison, not a claim that all eight are individually
necessary or that no other predictor could help. The form asks four separate
eligibility questions. The original strict backend still requires six model
answers including recency; the current UI uses a separate available-answer
adapter without altering that frozen model or strict API. Partial inputs use
fitted missing-value handling and have unvalidated personal performance. Unknown
profile answers produce a conditional estimate; known unsupported profiles
produce a clearly labeled hypothetical adult former-smoker scenario, not a
validated forecast for that user's reported situation. Recency of 30 days or
less is excluded from this scenario and documented as excluded, never replaced
with a fabricated eligible value. No usable model answers yields the separately
fitted no-input baseline, with no personalized factor attributions.

The UI reliability panel displays usable-answer coverage (not confidence),
profile support, held-out group discrimination with its available bootstrap
interval, and calibration evidence. No individual confidence percentage is
available. Incomplete/out-of-profile estimates have not been separately
validated; group metrics do not establish their accuracy. The no-input reference
uses its own baseline metrics rather than the full questionnaire model's.

The remaining three extended inputs—home smoking rules, physical health and
social satisfaction—did not improve validation enough to retain them. Detailed
historical smoking quantities and income are not requested. All accepted
answers use the existing documented coding; missing is never a zero response.
Wave 7 wording provides a fixed app context, not a matching guarantee for users.

## Results and explanations

Held-out test, using assigned midpoint observation times:

| Approx. horizon | IPCW ROC-AUC | IPCW Brier | No-input baseline Brier | Mean probability | IPCW observed risk |
|---|---:|---:|---:|---:|---:|
| 18 months | 0.7461 | 0.0809 | 0.0853 | 7.37% | 9.41% |
| 36 months | 0.7764 | 0.1269 | 0.1437 | 13.61% | 17.26% |
| 60 months | 0.7748 | 0.1516 | 0.1807 | 20.63% | 23.68% |

The model improves Brier score over a no-input survival baseline but
**underestimates average test risk**. Calibration is imperfect, and performance
for current app users is unvalidated. These measurements assess discrimination
and probability errors for assumed observation-time labels; they do not measure
error in actual resumption dates. There is no observed ground truth for actual
month-of-resumption accuracy. No such accuracy percentage is reported.

IPCW uses a development-fitted censoring Kaplan–Meier curve. It excludes
unresolved early-censored labels rather than counting them negative; evaluates
their contribution through censoring weights; and reports unsupported horizons
if weights become excessive. Censoring assumptions may fail under informative
attrition. Training-horizon support requires at least 100 participants followed
to a horizon. The report includes 200 participant-bootstrap intervals at the
36-month reference horizon; these do not quantify individual or midpoint error.

Risk categories are calibration-score tertiles at a fixed 36-month reference
horizon. The app shows all supported month horizons automatically and explains
the fixed 36-month reference probability. Risk categories are
relative project groups, not medical cutoffs. Exact original-feature Shapley
values explain the selected horizon probability using a fixed sixteen-person
development background. Reference output + contributions equals the probability.
Factors are associations, not causes. No participant background rows are exposed
in public reports or UI. Inference and explanations stay local; only model
resources are cached, never answer or prediction histories.

## Commands and preservation

```bash
# Already-trained local app (consecutive-wave model only)
.venv/bin/python -m streamlit run app/streamlit_app.py

# Integrity and exact cohort reproduction; no model refit/test rescoring
.venv/bin/python scripts/verify_longitudinal.py --rebuild-cohort
.venv/bin/python -m pytest -q -p no:cacheprovider
.venv/bin/python scripts/verify_inputs.py

# Fresh build only, when the configured new output directories do not exist
.venv/bin/python scripts/train_longitudinal.py
```

Configuration: `configs/longitudinal_v2.json`; implementation:
`src/path_project/longitudinal.py`. Current outputs live in
`data/processed/longitudinal_v2_1`, `artifacts/longitudinal_v2_1` (private local
data/artifacts) and `reports/longitudinal_v2_1` (aggregates only). Loading verifies
source/config/model/report hashes. Existing outputs refuse overwrite. Preserve
this experiment and choose a separately versioned run for future changes.

An initial diagnostic `longitudinal_v2` run is retained, marked **invalid**, and
never loaded by the app. It exposed a Wave 8 coding difference: follow-up 0/1
needed normalization to baseline history 1/2. The separately versioned v2.1 run
corrects this, with a regression test. The diagnostic is not a model comparison
or a source of valid performance claims. Original v1 evidence remains intact.
