# Whole-project verification — stage 13

Verification runner status: **passed**. This report describes executed checks; saved historical evidence is identified separately.

The original frozen four-input XGBoost, preprocessing, sigmoid calibration, thresholds, SHAP path and reserved participant assignment are retained. No final-test scoring, metric/bootstrap calculation, tuning, model search or real-data fitting was repeated. The final test remains exposed and closed to tuning.

## Executed commands

All commands use the isolated workspace Python 3.13.5. The root command was `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_project.py --isolated-build`. Argument lists and explicit working directories handle spaces without shell interpolation. Logs contain no intentionally emitted participant records and remain in ignored cache.

| Scope | Command (after Python executable) | Exit | Seconds |
|---|---|---:|---:|
| existing evidence | `-m pytest -q -p no:cacheprovider` | 0 | 16.582 |
| existing evidence | `scripts/validate_feature_mapping.py --no-write` | 0 | 0.257 |
| existing evidence | `scripts/validate_prediction_specification.py` | 0 | 0.025 |
| existing evidence | `scripts/verify_cohort.py` | 0 | 0.761 |
| existing evidence | `scripts/verify_evaluation_splits.py` | 0 | 0.511 |
| existing evidence | `scripts/verify_development.py` | 0 | 0.537 |
| existing evidence | `scripts/verify_baselines.py` | 0 | 2.945 |
| existing evidence | `scripts/verify_tree_models.py` | 0 | 7.071 |
| existing evidence | `scripts/verify_timing.py` | 0 | 1.724 |
| existing evidence | `scripts/verify_outputs.py` | 0 | 2.969 |
| existing evidence | `scripts/verify_final_evaluation.py` | 0 | 1.139 |
| clean isolated build | `scripts/inspect_prediction_sources.py` | 0 | 92.466 |
| clean isolated build | `scripts/build_feature_mapping.py` | 0 | 88.019 |
| clean isolated build | `scripts/validate_feature_mapping.py --no-write` | 0 | 0.291 |
| clean isolated build | `scripts/validate_prediction_specification.py` | 0 | 0.039 |
| clean isolated build | `scripts/build_cohort.py` | 0 | 23.373 |
| clean isolated build | `scripts/verify_cohort.py` | 0 | 0.828 |
| clean isolated build | `scripts/create_evaluation_splits.py` | 0 | 0.824 |
| clean isolated build | `scripts/verify_evaluation_splits.py` | 0 | 0.545 |
| clean isolated build | `scripts/finalize_inputs.py` | 0 | 0.522 |
| isolated frozen replay integrity | `scripts/verify_final_evaluation.py` | 0 | 1.364 |
| isolated synthetic end-to-end inference | `-m pytest tests/test_demo.py tests/test_project_smoke.py -q -p no:cacheprovider` | 0 | 7.376 |

Executed pytest summaries: existing evidence: 132 passed in 15.79s; isolated synthetic end-to-end inference: 7 passed in 6.60s.

Full-suite coverage includes cohort labels/unobserved outcomes, one-to-one string-ID joins, no all-wave intersection, documented units/skips, future-feature exclusion, participant/temporal separation, training-fold-only preprocessing, unseen categories, invalid schemas, missing answers, risk boundary ties and timing capability rejection. No resampling is configured in the real pipelines; synthetic tests verify the fixed no-resampling search and training-only class ratios.

`tests/test_project_smoke.py` sends the three clearly fictional app presets through the actual frozen artifact and Exact SHAP. It serializes a copy into a temporary path containing spaces, reloads it, and requires identical probabilities even with reversed input-column order. It also checks schema and identifier rejection. Streamlit AppTest checks displayed score/category/model version and percentage-point attribution consistency, suppression and reset behavior. This is actual inference, not a mocked model or a performance estimate.

## Clean generated-output replay

The isolated workspace began with no generated reports/data/artifacts. Code/config/docs were copied; original PATH documentation/data and legacy diagnostic were referenced without modification. The recorded dependency order regenerated source evidence, feature mapping/dictionary, cohort, eligible ledger, deterministic split membership and final input metadata.

| Regenerated file | SHA-256 identical to original |
|---|---|
| `reports/prediction_source_evidence.json` | True |
| `configs/feature_mapping.json` | True |
| `docs/feature_dictionary.csv` | True |
| `configs/feature_mapping_final.json` | True |
| `configs/app_questions.json` | True |
| `data/processed/cohort_v1/cohort.parquet` | True |
| `data/processed/cohort_v1/eligible_interval_ledger.parquet` | True |
| `artifacts/evaluation_v1/participants.parquet` | True |
| `artifacts/evaluation_v1/records.parquet` | True |

Then existing fitted artifacts and aggregate evidence were copied into the isolated tree. Frozen integrity verification and synthetic app/serialization tests ran there successfully. Model searches, calibration/threshold fits, exploration-based feature decisions and final evaluation were deliberately reused, not newly executed. Prior execution evidence is retained in stage reports/manifests. No clean full training run or fresh dependency installation is claimed.

Protected original generated evidence: **212 files** checked for SHA-256 and modification-time changes; **0 changes**.

## Originals and intentional orchestration exception

58/59 original files match the unchanged baseline. The legacy `scripts/verify_inputs.py` returns nonzero for the intentional user edit of `run_prompts.py`. The stage 13 verifier accepts only its exact documented SHA-256 in `configs/verification.json`, reports it separately, and rejects any other original-input difference. Raw survey data, original proposal and existing analysis remain unchanged; no baseline was rewritten.

## Privacy and shareable deliverables

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/audit_deliverables.py` checked **188 candidate files**, **10 sensitive-path ignore probes**, and found **0 issues**. `git ls-files` returned exit128 because the workspace has no real Git repository, so there are no tracked deliverables to inspect. The candidate-file scan is reported instead of inventing a clean Git status. Temporary bare Git metadata inside ignored cache tested effective ignore rules without changing the workspace Git placeholder.

Raw sources, participant-level outputs, trained artifacts, environments, orchestration logs, `.env`, `.aws` and Streamlit secrets are ignored. Common private-key/API-key patterns and known real participant-ID tokens are checked without emitting matched values. Fictional fixtures and metadata dictionaries are allowed. This is bounded secret-pattern/token verification, not a guarantee that every possible secret format is detectable. No upload, commit, publication or deployment occurred.

## App launch and visual evidence

The documented command is `.venv/bin/python -m streamlit run app/streamlit_app.py`. The user-supplied screenshot at `/home/hellfire/Downloads/screencapture-127-0-0-1-8501-2026-11-08-06_25_34.png` confirms external localhost launch and initial form/performance rendering. The user explicitly confirmed: “Blank submission correctly warns without a prediction; all three presets show results without errors.” These are user browser observations, not an agent HTTP health check. The initial screenshot does not itself show submitted prediction details. Executed automated tests establish exact probability/category/explanation/model identity.

The runner cannot create server sockets or drive a browser here. No redundant socket preflight or launch was requested. No new agent-driven interactive visual inspection is claimed; layout evidence is limited to the supplied screenshot and user-reported interactions. This limitation does not undo the already-confirmed local start.

## Concrete fixes and remaining limits

- Added explicit ignore rules for `.streamlit/secrets.toml` and local `secrets.toml`.
- Corrected stale current README statements about the app being future work and final-test metrics being unavailable. Historical stage descriptions remain historical.
- Added a clear build/replay order and a configuration-driven verifier with safe isolated regeneration and original-artifact preservation.
- Added real-artifact synthetic serialization/end-to-end inference coverage.

No material model/cohort defect was found by the executed checks; therefore no frozen research source was changed and no test-exposure bug/recovery evaluation was needed. The measured calibration shortcomings remain reported honestly, without replacing the model. Scientific limitations remain observed-follow-up selection/attrition, instrument/period shifts, unweighted survey design, unvalidated new-user/non-U.S./clinical performance and unsupported timing. No annual risks, relapse dates, causal intervention effects or personal-confidence claims are created.

Fresh installation, cross-platform behavior, full fresh expensive training and a new agent browser session were not run. The safe isolated regeneration and frozen-artifact replay above are the actual reproducibility checks. See `reports/verification_evidence.json`, `reports/deliverable_audit.json`, `reports/demo_verification_v1.json`, `docs/build_order.md` and `PROJECT_STATUS.md` for precise provenance. Stop at stage 13.
