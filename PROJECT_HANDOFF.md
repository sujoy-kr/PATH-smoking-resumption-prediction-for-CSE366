# CSE366 project handoff

**Current extension (2026-11-08):** The user subsequently authorized a separate
consecutive-wave study with approximate months, current-established smoking
return, probability percentages, relative risk and contributing factors. The
app now uses v2.1 only; v1 has been retired from navigation and remains archived. See
[the new protocol and results](docs/longitudinal_v2.md) and the appended status
entry. The remainder of this handoff describes the original completed v1 study;
its timing prohibition and four-input model are not the v2.1 capability contract.
Approximate v2.1 months use assumed collection-window midpoints and must not be
presented as precise individual resumption times. The new study has separately
partitioned participants and does not retune the original exposed-test model.

Stages 1–14 are implemented, with completion evidence in PROJECT_STATUS.md and the stage reports; stage 15 checks the final deliverable and supplies this handoff. The final test was evaluated once, is exposed, and is closed to further tuning. Earlier “unopened”/pending stage descriptions are historical. No publication, deployment, commit or push has occurred.

## What the project predicts

Among adult former established cigarette smokers reporting no cigarette use in the past 30 days at a starting interview, the model estimates **past-30-day cigarette smoking reported at the next scheduled interview**, conditional on valid observed follow-up. It does not identify every temporary resumption between interviews, persistent relapse, a guaranteed event, an annual risk or an exact return-to-smoking date. A negative follow-up window is not proof of continuous abstinence. Missing follow-up is unobserved, never a negative label.

The cohort uses seven adjacent pairs across eight canonical local adult PATH waves. It has 30,890 labeled intervals from 9,597 people, including 3,258 positives; the eligible ledger retains 5,749 unobserved outcomes among 36,639 intervals. It does not require an all-eight-wave intersection. PERSONID is a string join/group key, never a predictor. Local source pages, revisions, response labels and skip rules are traceable through [the specification](docs/prediction_specification.md) and [inventory](docs/data_inventory.md).

## Start the already-trained app

From the project root, using the existing Python 3.13.5 environment:

```bash
.venv/bin/python scripts/verify_final_evaluation.py
.venv/bin/python -m streamlit run app/streamlit_app.py
```

Open http://127.0.0.1:8501. Bare `python` is unavailable here. Paths containing spaces have been exercised by the isolated verification. Do not activate or replace the environment unnecessarily. Full dependency versions are in [requirements-lock.txt](requirements-lock.txt); setup, exact data placement and troubleshooting are in [README](README.md).

The user-supplied browser screenshot and explicit confirmation establish local launch, blank-submit suppression and successful submissions of all three fictional presets. This is user browser evidence, not an agent HTTP test. The runner cannot create sockets or drive a new browser; no redundant launch is needed. Automated tests separately verify exact prediction identity. Use fictional presets for a demonstration, not participant records.

**Retain the full local evidence bundle.** Model loading verifies cohort, split, model and report provenance; a lone model file is insufficient. Preserve the existing source/config/docs/reports and private `data/processed/` and `artifacts/` directories. Do not upload them. Missing or mismatched files require restoration/investigation, not silent refitting or bypassing signatures. Fresh installation, another Python build/OS and a complete newly repeated expensive search were not verified.

## Inputs, outputs and selected model

| Input | Supported meaning |
|---|---|
| Age band | 18–24, 25–34, 35–44, 45–54, 55–64, 65+ |
| Education | Five documented harmonized categories from less than high school to bachelor/advanced degree |
| Employment | Full-time ≥35 hours/week, part-time 15–34, part-time under 15, not currently working for pay |
| Last-cigarette recency | Historical positive whole quantity with days/months/years; Wave 7 form permits 1–99 units. Months/years convert to approximate days, not a future event time. |

The four inputs are the selected minimal profile; the eleven-input app-compatible comparison and 25-candidate research dictionary are not silently supplied to this model. Exact questions/options/missing rules are in [app questions](docs/app_questions.md) and `configs/app_questions.json`. Eligibility checks approximate the official cohort (adult, established smoking history, currently not smoking, no past-30-day use). Unknown eligibility or fewer than two supplied model inputs withhold the estimate. Invalid/conflicting recency is rejected; supported unknowns use trained missing handling, not zero or invented history.

Outputs: calibrated percentage with endpoint/variable interval, lower/moderate/higher project risk category, frozen boundaries, top probability-scale Exact SHAP contributions, submitted answers, input completeness, model version/hash and limitations. Contributions plus reference model output reconstruct the displayed score. They are percentage-point attributions after multiplying by 100, not log-odds, personal confidence or intervention effects. No names, contact details or IDs are collected; answers are not persisted to files. Only model resources are cached.

Selected model: **xgb_minimal_s1_none**, CPU XGBoost with 180 trees, maximum depth 3, learning rate 0.05, min_child_weight 10, lambda 5, no class reweighting. The fitted preprocessing and separate-development sigmoid calibrator are preserved. Artifact: `artifacts/trees_v1/selected_calibrated.joblib`. SHA-256:

```text
9b46cdb1783302c05c3b56b83d5695a1ad58b90da0614f04188ee687170eae36
```

Selection used five grouped development folds, not the test. Base fitting, sigmoid calibration and threshold selection use distinct authorized participant partitions. Every held-out test person's earlier records are excluded from fitting. Class weights, participant metric weights and survey weights have different purposes; no matching survey-design analysis supports national estimates.

## Actual final results

Reserved observed-valid Wave 7→8 test: **1,243 people/records, 128 positive (10.30%), 1,115 negative**. The conditional 95% intervals below use 1,000 participant-bootstrap draws. They are uncertainty in aggregate evaluation, not personal confidence or full model-selection/generalization uncertainty. Undefined bootstrap metrics are handled explicitly in saved results.

| Selected calibrated metric | Estimate [95% interval] |
|---|---|
| Average precision | 0.2447 [0.1961, 0.3146] |
| ROC-AUC | 0.7392 [0.6955, 0.7810] |
| Brier score | 0.0885 [0.0782, 0.0993] |
| Precision | 0.2791 [0.2170, 0.3351] |
| Recall | 0.4688 [0.3828, 0.5547] |
| Specificity | 0.8610 [0.8415, 0.8805] |

Average precision is the stepwise metric matching sklearn, not trapezoidal PR-AUC. At the frozen binary threshold 0.2590049599706509: TN=960, FP=155, FN=68, TP=60. Final test has one record per person; clustered and ordinary person-resampling coincide here.

Risk cuts: 0.0750747765280418 and 0.2590049599706509. Lower includes the first cut, moderate includes the second, higher is strictly above it. These are development-defined relative strata, not medical cutoffs. The binary rule uses ≥its threshold; ties can therefore be moderate but binary-positive. Observed final outcomes: lower 23/570 (4.04%), moderate 45/460 (9.78%), higher 60/213 (28.17%), with CIs in the saved report.

**Retain weak findings:** mean calibrated prediction 13.90% exceeded observed 10.30%; raw selected-tree Brier 0.0851 was better than calibrated 0.0885. Several frozen logistic baselines had higher final AP. The selected model, sigmoid and cuts were not changed after exposure. Full comparisons, subgroup counts/suppressions, calibration and figures are in [final evaluation](reports/final_evaluation.md) and [saved aggregate JSON](reports/final_evaluation_v1/results.json).

## Timing implementation

**No elapsed-time prediction was implemented: justified decision C.** Individual follow-up clocks and a complete first-resumption event history are unavailable for this implemented cohort. General wave-year labels, conditional past-year questions and historical quit duration cannot provide exact relapse times or supported annual horizons. No survival curve/model, annual probability, estimated relapse date or fabricated censoring time is supplied. See [timing feasibility](docs/timing_feasibility.md) and [timing decision](docs/timing_decision.md). This is an intentional, evidence-supported omission, not a missing classifier.

## Exact stage commands and safe reproduction

Commands below are run from the project root with the existing environment. This is the dependency order, **not an instruction to repeat searches or final evaluation now**. Existing complete immutable runs verify/reuse and reject incompatible/partial outputs. Never delete locks, rehash changed inputs, reseed participants or remove exposure logs to force regeneration. [Build-order documentation](docs/build_order.md) explains safe isolated replay and provenance constraints.

| Stage | Exact executable commands |
|---|---|
| 1 · Inventory/environment | `.venv/bin/python scripts/check_environment.py` then `.venv/bin/python scripts/inventory_inputs.py`; check originals with `.venv/bin/python scripts/verify_inputs.py` |
| 2 · Target/source evidence | `.venv/bin/python scripts/inspect_prediction_sources.py` then `.venv/bin/python scripts/validate_prediction_specification.py` and `.venv/bin/python scripts/check_prediction_evidence.py` |
| 3 · Mapping/dictionary | `.venv/bin/python scripts/build_feature_mapping.py` then `.venv/bin/python scripts/validate_feature_mapping.py --no-write` and `.venv/bin/python scripts/check_feature_evidence.py` |
| 4 · Cohort/labels | `.venv/bin/python scripts/build_cohort.py` then `.venv/bin/python scripts/verify_cohort.py`; optional documented diagnostic `.venv/bin/python scripts/diagnose_cohort_recency.py` |
| 5 · Participant lock | `.venv/bin/python scripts/create_evaluation_splits.py` then `.venv/bin/python scripts/verify_evaluation_splits.py` |
| 6 · Tuning exploration/inputs | `.venv/bin/python scripts/explore_development.py` then `.venv/bin/python scripts/finalize_inputs.py`, `.venv/bin/python scripts/write_development_summary.py`, `.venv/bin/python scripts/verify_development.py` |
| 7 · Baselines | `.venv/bin/python scripts/train_baselines.py` then `.venv/bin/python scripts/verify_baselines.py` and `.venv/bin/python scripts/write_baseline_report.py` |
| 8 · Trees/selection | `.venv/bin/python scripts/train_tree_models.py` then `.venv/bin/python scripts/verify_tree_models.py` and `.venv/bin/python scripts/write_model_selection.py` |
| 9 · Supported timing omission | `.venv/bin/python scripts/confirm_timing.py` then `.venv/bin/python scripts/verify_timing.py` |
| 10 · Frozen outputs/explanations | `.venv/bin/python scripts/build_outputs.py` then `.venv/bin/python scripts/verify_outputs.py` and `.venv/bin/python scripts/write_output_report.py` |
| 11 · Saved final evidence only | `.venv/bin/python scripts/verify_final_evaluation.py` — never a new evaluation of the exposed test |
| 12 · Local app | `.venv/bin/python -m streamlit run app/streamlit_app.py` |
| 13 · Whole-project verification | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_project.py --isolated-build` then `.venv/bin/python scripts/audit_deliverables.py` and `.venv/bin/python scripts/write_verification_report.py` |
| 14 · Documentation consistency | `.venv/bin/python scripts/verify_documentation.py`; Markdown is maintained documentation, not dependent on an ephemeral authoring helper |
| 15 · Handoff audit | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_handoff.py` |

For historical completeness, stage 11 originally ran `.venv/bin/python scripts/evaluate_final.py --prepare-only` **before access**, followed by `.venv/bin/python scripts/evaluate_final.py` once. Those are not commands to run again for this handoff. Its completed retry path only verifies/reuses saved results; an incomplete exposed run must stop for documented investigation. Any substantive changed model needs an exposure-aware new evaluation plan and appropriate independent data.

Safe everyday checks without regenerating research evidence:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_final_evaluation.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_handoff.py
```

`verify_project.py --isolated-build` is the heavier safe reconstruction option: it creates a new ignored output workspace, rebuilds early stages, compares deterministic cohort/membership, restores frozen models and runs synthetic inference. Stage 13 actually executed 132 tests, seven isolated synthetic checks and nine matching regenerated-file comparisons, preserving 212 original generated files. It did not repeat fresh expensive model searches or final evaluation. Legacy split-check “unopened” output and older app metadata's “pending” wording are historical; current exposure is recorded in the final manifest/log and `configs/final_evaluation_status.json`.

## Locations and stage-completion evidence

| Deliverable | Files / directories |
|---|---|
| Cohort code and schema | [cohort module](src/path_project/cohort.py), [pipeline guide](docs/cohort_pipeline.md), ignored `data/processed/cohort_v1/` |
| Verified mapping and sources | `configs/feature_mapping.json`, `configs/feature_mapping_final.json`, [dictionary](docs/feature_dictionary_final.csv), `reports/feature_mapping_evidence.json` |
| Participant lock | Ignored `artifacts/evaluation_v1/participants.parquet`, `records.parquet`, `manifest.json`; [evaluation protocol](docs/evaluation_protocol.md) |
| Fitted models | Ignored `artifacts/baselines_v1/` and `artifacts/trees_v1/`; [selection report](docs/model_selection.md) |
| Probability explanations | [output module](src/path_project/outputs.py), `configs/output_contract.json`, `configs/risk_categories_v1.json`, ignored `artifacts/outputs_v1/` |
| Final evaluation | [final report](reports/final_evaluation.md), `reports/final_evaluation_v1/`; private pre-test snapshots/log/predictions under `artifacts/final_evaluation_v1/` |
| Application | [Streamlit source](app/streamlit_app.py), [app instructions](app/README.md), `configs/demo.json` |
| Tests | [synthetic fixtures](tests/fixtures/README.md), [real-artifact synthetic smoke test](tests/test_project_smoke.py), all `tests/test_*.py` |
| Verification | [whole-project report](reports/verification.md), `reports/verification_evidence.json`, `reports/demo_verification_v1.json`, `reports/documentation_checks.json`, `reports/handoff_checks.json` |
| Student/reviewer documentation | [final project report](docs/final_project_report.md), [proposal corrections](docs/proposal_revision_notes.md), [presentation](docs/presentation_outline.md), [viva](docs/viva_questions.md) |

Stages 1–8 have source, cohort/split and executed-model evidence; stage 9 is the justified timing omission; stages 10–11 have actual explanations and frozen measured results; stage 12 has user browser evidence plus automated identity checks; stage 13 has clean isolated replay; stage 14 has result/link/citation verification. No missing trained model or unrun final evaluation is being labeled complete. Literature full-method access and timing-description ambiguity are explicitly limited in `reports/literature_verification.json`; no first-ever PATH relapse claim is made.

## Limitations, preservation and future work

- Results are conditional on observed follow-up and self-report, with attrition, instrument/routing and period differences. Recency missingness can encode questionnaire routing; a fully answered new app user may differ from the training population.
- Probability calibration transferred imperfectly; risk categories are project-defined. Neither SHAP nor subgroup comparisons establish causation, fairness, treatment benefit or clinical reliability.
- Matching survey weighting/design handling is absent; no national, non-U.S. or present-day new-user validity claim. PATH is a U.S. source, not a validation dataset for Bangladesh.
- Unsupported time horizons/dates remain omitted. A future timing study requires valid clocks/event ascertainment and appropriate censoring/observation methods, not a curve generated from wave numbers.
- Original dataset, proposal PPTX and existing analysis remain preserved. The original integrity baseline has 58/59 matches because the user intentionally changed `run_prompts.py` runner instructions; its exact permitted hash is documented. Do not call the legacy check passing or rewrite the baseline.
- Raw/participant data, models, private reference rows, environments and secrets remain ignored. No actual Git repository exists; candidate-file checks substitute for a tracked-file scan. No commit, push, upload or deployment is authorized by this handoff.

Sensible future work: independently validate on appropriate new people/periods before reconsidering calibration; investigate instrument/missingness transport; acquire matching survey design data for a clearly specified population target; evaluate subgroup reliability only with sufficient support; and obtain defensible timing information before a separate survival extension. These are proposals, not verified improvements or permission to reopen this final test.

The next step is reviewer/course use of the existing project, or a separately requested audit/change. Preserve all current artifacts and request an exposure-aware plan for substantive research revisions.
