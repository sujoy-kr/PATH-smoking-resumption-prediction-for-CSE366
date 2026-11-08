# Reclaim: local smoking-return assessment

```bash
.venv/bin/python -m streamlit run app/streamlit_app.py
```

Open http://127.0.0.1:8501. Restart the existing Streamlit process once after the
UI/configuration update so toolbar settings take effect. There are no API keys
or new package dependencies.

The app uses only the consecutive-wave v2.1 model. The original next-survey
interface has been retired from navigation; `legacy_app.py` and v1 research
artifacts remain archived for reproducibility.

## Assessment and results

- Four eligibility checks and eight model questions, with fixed radio choices.
  There are no searchable/editable dropdowns or horizon selection controls.
- Time since the last cigarette starts blank; entering a numeric amount records
  it directly. There is no separate “supply a number” toggle. The amount can also
  be cleared, including in fictional examples.
- Live completion updates immediately. Partial answers are accepted; unknown
  values use fitted missing handling. A blank submission uses the separate
  no-input study baseline, labeled as a study reference rather than a personal
  prediction. There is no eligibility rejection message.
- Profile answers determine interpretation: a confirmed matching profile yields
  a study-profile assessment; unknown profile answers yield a conditional
  estimate; unsupported answers yield a hypothetical adult former-smoker
  scenario. The model is not validated for current/recent smokers, never-smokers
  or minors. A last-cigarette duration of 30 days or less is excluded from the
  quit-for-over-30-days scenario, with a visible note and the original answer
  preserved in the summary. It is not changed to an invented eligible duration.
- “How reliable is this estimate?” shows usable-answer coverage, population
  support, group test ROC-AUC/its available bootstrap interval and calibration.
  Personal prediction confidence is unvalidated and never fabricated as an
  “X% sure” score. Answer coverage is explicitly not confidence. A blank
  reference uses the baseline's own group metrics, not the questionnaire model's.
- Inputs render outside a batched form so corrections remove stale errors on
  rerun. Editing any answer removes the previous result. Results persist only
  in that browser session until an answer changes.
- Every successful assessment shows 12/18/24/36/48/60-month cumulative
  probabilities, a probability chart, fixed 36-month relative risk and exact
  Shapley contributions to the 36-month probability. The model is unchanged.
- Approximate unconditional median is shown only when risk reaches 50% within
  follow-up; the conditional median is separately labeled.
- The responsive layout stacks question/summary columns on small screens and
  changes the timeline grid from six to three to two columns. Native labeled
  controls preserve keyboard access. CSS respects reduced-motion preferences.
- The deployment toolbar is disabled in `.streamlit/config.toml` and hidden by
  CSS. This is a local app, not a hosted deployment.

Months use assumed wave midpoints, not measured individual resumption dates.
The model underestimates average held-out risk. Calibration limitations and
unvalidated new-user/clinical performance remain visible; detailed study evidence
is in a disclosure panel. See [the study protocol](../docs/longitudinal_v2.md).

Only model resources use the shared resource cache. Answers and the current
result remain in session memory, without files, external calls or shared answer
caches. Close the session to discard them. Fictional examples are labeled.

## Verification

```bash
.venv/bin/python -m pytest tests/test_longitudinal_app.py -q -p no:cacheprovider
.venv/bin/python scripts/verify_longitudinal.py
```

The UI tests exercise manual complete entry, fictional profiles, automatic
horizons, unchanged supported-profile probability/explanation identity,
conditional scenarios, blank reference results, partial inputs, optional
unknowns, reliability scope, numeric clearing, stale-result invalidation, and
absence of editable dropdown/model-selection controls. Responsive breakpoints
and toolbar settings are checked in source. No new interactive-browser viewport
or production hosting validation is claimed by these tests.
