# Build order and safe verification

Run commands from the project root with `.venv/bin/python` (Python 3.13.5 in the verified environment). Bare `python` is unavailable here. Commands use argument lists internally, so the existing `CSE366 Project` path and isolated paths containing spaces work. Do not copy command strings through `eval` or interpolate unquoted paths.

The local package snapshot is `requirements-lock.txt`; `pyproject.toml` declares dependencies. Discover a compatible Python and create an isolated environment if one is absent. Fresh dependency installation and another operating system have not been verified. No API keys or external databases are required.

| Order | Inputs → outputs | Implementation |
|---|---|---|
| 1 | Original files → inventory and checksum baseline | `scripts/inventory_inputs.py`; preserve the existing `docs/original_inputs.sha256.json` |
| 2 | Local PDFs and TSV headers → endpoint/source evidence | `scripts/inspect_prediction_sources.py`, `scripts/validate_prediction_specification.py` |
| 3 | Curated recipe and source evidence → mapping/dictionary | `scripts/build_feature_mapping.py`, `scripts/validate_feature_mapping.py --no-write` |
| 4 | Canonical eight waves and mapping → cohort/eligible ledger/aggregate flow | `scripts/build_cohort.py`, `scripts/verify_cohort.py` |
| 5 | Cohort keys and deterministic hash rule → participant/record split lock | `scripts/create_evaluation_splits.py`, `scripts/verify_evaluation_splits.py` |
| 6 | Tuning participants only → exploration and final feature/question metadata | `scripts/explore_development.py`, `scripts/finalize_inputs.py`, `scripts/write_development_summary.py` |
| 7 | Grouped tuning folds and reserved development groups → frozen baselines | `scripts/train_baselines.py`, `scripts/verify_baselines.py` |
| 8 | Same protocol → frozen tree comparison/selected classifier | `scripts/train_tree_models.py`, `scripts/verify_tree_models.py` |
| 9 | Timing evidence/schema → omission decision C and capability metadata | `scripts/confirm_timing.py`, `scripts/verify_timing.py` |
| 10 | Selected classifier and development reference data → frozen bands/explanations | `scripts/build_outputs.py`, `scripts/verify_outputs.py` |
| 11 | Pre-test freeze → one-shot reserved-test evidence, already completed | `scripts/evaluate_final.py --prepare-only` then `scripts/evaluate_final.py` **only before original exposure**; now use `scripts/verify_final_evaluation.py` |
| 12 | Frozen model/output API and saved aggregate results → local Streamlit UI | `.venv/bin/python -m streamlit run app/streamlit_app.py` |
| 13 | Existing evidence + independent synthetic checks → verification report | commands below |

This table describes dependencies, not an instruction to rerun training or evaluation now. Existing training/build commands verify/reuse completed immutable outputs and reject changed/partial runs. Never delete locks, rewrite input baselines, reseed, change directories to bypass a provenance failure, or rerun final scoring to make a check pass. Current final test is exposed and closed to tuning. The old split verifier's “unopened” text is historical; it checks membership, not current exposure.

Safe project verification:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_project.py --isolated-build
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/audit_deliverables.py
```

The verifier runs the full synthetic/correctness suite and saved-evidence validators. It creates a **new** ignored `.cache/stage13/verification with spaces .../clean generated output workspace` with copied code/config/docs, read-only-by-convention source references, and initially empty generated reports/data/artifacts. It rebuilds source evidence, mappings, cohort and deterministic membership there, and compares hashes to the original locked files. This is a replay of the original assignment rule, not replacement of the authoritative split. Final input metadata is regenerated from the recorded development-only decisions; feature selection is not repeated on test outcomes.

After regeneration, the verifier copies the existing frozen models/report evidence into that isolated workspace and runs integrity plus synthetic UI/inference/serialization checks. It does **not** repeat model searches, calibration, threshold/category selection, SHAP background selection, or final evaluation. Full expensive model fitting is supported by saved historical execution evidence, not claimed freshly reproduced in stage 13. All original cohort/artifact/report bytes and modification times are checked before/after. Workspaces/logs are retained locally for inspection; the script never deletes original files.

The intentional user edit of `run_prompts.py` makes the unchanged legacy `scripts/verify_inputs.py` return nonzero (58/59 unchanged). `configs/verification.json` permits only the exact user-confirmed SHA-256 for that orchestration exception, separately reports it, and still fails on any other change. No raw data, proposal or existing analysis exception is allowed. The original baseline is never regenerated.

`audit_deliverables.py` checks effective ignore rules with temporary Git metadata inside ignored cache, not a repository initialized in the project. If no real Git repository exists, it reports that tracked-file verification is not applicable and scans shareable candidates instead. It checks known real-ID tokens, sensitive extensions and common secret patterns; it does not promise exhaustive secret detection. No sensitive match value is emitted.

Runtime launch/visual verification uses the user-supplied screenshot and explicit interaction confirmation in `PROJECT_STATUS.md`. The runner cannot bind sockets or drive a browser here. Do not repeat sandbox launch attempts as a condition of accepting the already-confirmed external local launch. Automated Streamlit tests execute the form and results without a listening socket; they do not substitute for unobserved visual details.
