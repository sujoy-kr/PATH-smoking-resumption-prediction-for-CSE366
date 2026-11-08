# Stage 9 timing decision: C — elapsed-time estimation omitted

**Elapsed-time prediction is unsupported for this cohort and the supplied local files. Keep the working next-survey classifier. No survival model, survival curve, annual probability or estimated relapse date is produced.** Stage 9 is complete by confirming and enforcing this scientifically justified omission, not by obtaining a curve from software.

The stage 2 decision in [timing_feasibility.md](timing_feasibility.md) remains consistent with the actual implemented cohort and current inputs. This conclusion is scoped to the supplied public-use files and target. It does not assert that all PATH releases lack useful timing information.

## Confirmed against the implementation

`scripts/confirm_timing.py` freshly reads only the headers of all eight canonical adult TSVs (one copy per wave), verifies the hashes of their sixteen main codebooks/questionnaires, checks the actual Parquet schemas against the saved cohort schema, and rechecks four specific source-page ranges directly with local pdftotext. Evidence is saved in `reports/timing_confirmation_v1.json`, including file names, physical PDF pages, header columns, source hashes and unchanged classifier reference. It reads no survey/cohort answer rows. Existing internal split membership keys are loaded by the retained-model integrity checker; no held-out features/outcomes are opened.

Both the original and final machine-readable prediction specifications say C. The actual cohort/ledger contain starting/follow-up wave indices and status labels, not an individual interview date, elapsed interval, event date, time-to-event or censoring time. `last_cigarette_recency_days` is present as historical baseline information. `regular_smoking_months` describes earlier smoking history. Their units do not make them prospective follow-up clocks.

The retained model is `artifacts/trees_v1/selected_calibrated.joblib`, selected in stage 8 using tuning CV only. Its four baseline inputs are age band, education, employment and quit/last-cigarette recency. Its file hash is pinned in the new app metadata; no classifier, calibration, threshold, cohort predicate or participant assignment is changed. The next-survey classifier's target is unchanged: former established cigarette smokers reporting no use in the starting interview's past-30-day window, predicting past-30-day smoking at the immediately next scheduled interview when its outcome is valid and observed. Final-test evaluation remains pending.

## Evidence and distinctions

| Question | Verified local evidence | Consequence |
|---|---|---|
| Individual interview clock? | `PATH/DS1001/36498-1001-Questionnaire.pdf`, physical p.24, instructs creation of INTVDATE. It is absent from every canonical adult TSV header. Fresh configured header searches find no usable interview-date/elapsed-interval candidate; reviewed unchanged codebook timing catalogs contain no matching interview-clock title. | Questionnaire programming is not a released participant-level clock. No elapsed follow-up can be manufactured from wave numbers. |
| General calendar windows? | `PATH/DS8001/36498-8001-Documentation-Nonresponse_Report.pdf`, physical pp.18–19, Section 2.4/Table 2.1, reports differing study collection windows. | These are population collection windows, not individual origin/end times. Do not use wave start/end dates, year labels or window midpoints as person-time. |
| Last-use/quit recency? | AC1009 number/unit fields exist across all eight headers; exact cross-wave sections are in `timing_feasibility.md` and the feature dictionary. Wave 1 asks since completely quitting, later waves since last cigarette. Wave 2 permits days/months and lacks the corresponding derived DAYSQUIT field. | Historical recency can be an optional baseline predictor, with routing-related unknown values. It is not future time until relapse, an exact quit date, or follow-up length. No missing duration becomes zero. |
| Retrospective approximate dates? | AN0135 and AN0135_VALUE_INFO exist in all eight headers. `PATH/DS1001/36498-1001-Codebook.pdf`, physical pp.692–693, describes the approximate end of the last product-dependent quit attempt among routed current users; `PATH/DS8001/36498-8001-Codebook.pdf`, physical pp.1389–1390, also documents the approximate last-attempt end date. | Dates are not universally absent, but these restricted retrospective fields are not a complete, cigarette-specific first resumption after this cohort's starting interview. The last attempt may be a later episode or refer to another product. A valid-looking calendar string does not repair the endpoint mismatch. |
| Any interval resumption versus status? | AC1002_12M and quit-attempt questions are documented in the all-wave source crosswalk; their eligibility and recall windows differ from the next-interview 30-day status. | A 12-month recall can extend before baseline or miss early events in a longer interview gap. It does not establish every resumption during the individual interval. |

The sixteen documentation hashes still match both the original-input manifest and the saved source evidence. The fresh evidence includes every wave's relevant recency and conditional-date source columns. No date values or final-test records are parsed to reach this decision: the documented construct and eligibility already rule out a complete event history for this cohort. The existing local inventory found no separate usable timing/linkage file; unavailable restricted/supplemental data are not assumed present.

## Why neither A nor B is enabled

**A: actual first smoking resumption time.** A common starting interview origin exists conceptually, but there is no usable individual elapsed clock or complete first-event observation rule for this cohort. A person can resume and stop again before the next past-30-day window. A negative follow-up therefore cannot be treated as an event-free interval or a right-censored first-resumption record. A positive window establishes reported recent use, not the first post-baseline cigarette, duration of use or persistent relapse. Last-attempt dates cannot fill that gap for all entrants. These are endpoint/observation failures, not merely a missing survival-library dependency.

**B: time to first observed smoking status.** A first positive wave index could describe detection order in a separately designed repeated-follow-up study, but a wave index is not elapsed time and the current person–adjacent-wave classifier does not implement that target. Intermittent missing waves and variable observation gaps would require their own observation model. Even individual interview dates, if obtained later, would date detection rather than establish exact resumption. No first-observed-status timing model or calendar horizon is enabled here.

**C: next-survey classification.** Retained. y=1 means cigarette use reported in the next interview's past-30-day window; y=0 means no use in that window, not continuous abstinence throughout the gap. It predicts a status snapshot and can miss intervening brief episodes and repeated quit/resume cycles. Two adjacent positive responses would not prove continuous smoking between them.

For the retained classifier, absent interviews and unknown follow-up responses stay unobserved in the ledger, never negative labels. Missing waves are not bridged. No death/withdrawal reason is assigned from absence. For a hypothetical timing study, censoring at last observation would require usable elapsed time and a defensible conditional-independent-censoring assumption. Informative attrition is plausible; the stage 6 availability comparisons do not justify such an assumption or correct it. Verified death could be a competing event, but no competing-event history is invented.

No unsupported persistence/absorbing-state, fully observed episode or noninformative-censoring assumption is adopted to force a survival extension. A generic right-censored estimator cannot represent unknown intervals automatically; even an interval-censored estimator would need genuinely known event-free bounds and appropriate observation data. Interval endpoints or midpoints are not substituted for exact relapse dates. No horizon has sufficient verified elapsed-time support for this target, so **the supported elapsed-time horizon list is empty**.

## App metadata and enforced output limits

`configs/app_metadata.json` is a separate additive capability contract. Existing fingerprinted mapping/question/specification files are preserved. The metadata marks:

- classifier available, with its existing artifact hash and development-only validation status;
- elapsed-time estimates, survival model, fixed-horizon probabilities and relapse-date estimates unavailable;
- supported elapsed-time horizons as an empty list;
- next-interview interval length unknown for an individual and variable across the study;
- historical recency as a predictor only, and the snapshot/attrition interpretation above.

The exact timing message is: “Elapsed-time risks and estimated relapse dates are unavailable. This research classifier predicts smoking reported at the next survey, not when smoking will resume.”

`path_project.timing.next_survey_output_metadata` rejects requests for elapsed horizons or relapse dates rather than returning annual placeholders. It does not transform a classifier probability into a survival function, rescale it by survey years, calculate an expected relapse date or generate a personal confidence percentage. The metadata contains no placeholder annual probabilities or individual predicted dates. Future Streamlit work must respect this capability guard. No UI is implemented or deployed in stage 9, and no clinical/new-user probability validity is claimed.

## Verification and continuation

```bash
.venv/bin/python scripts/confirm_timing.py
.venv/bin/python scripts/verify_timing.py
.venv/bin/python -m pytest -q -p no:cacheprovider
.venv/bin/python scripts/verify_evaluation_splits.py
.venv/bin/python scripts/verify_inputs.py
```

Tests use synthetic policies/metadata and existing documentation/schema metadata, not final-test predictions. Classifier and earlier immutable artifacts must retain their hashes and timestamps on retries. No models are fitted or recalibrated and no final evaluation is performed.

Revisit timing only if separately authorized with additional documented individual observation times and an event history that distinguishes cigarette-specific first resumption from snapshots/last attempts, with justified entry, observation gaps, censoring/competing events and supported horizons. Such an analysis must have its own target/protocol, appropriate censoring implementation, participant separation and development-only selection; it must not silently replace this classifier. No user action is required to finish this stage. Stop here and await the next numbered prompt.
