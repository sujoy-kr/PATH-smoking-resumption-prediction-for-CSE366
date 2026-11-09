# Research, maintenance and faculty reference

## Current application

The active project is the **interval-censored v2.4 survival model** ([protocol](longitudinal_v2_4.md)); v2.1 is retired history. Start with
[the v2.1 protocol (superseded)](longitudinal_v2.md), [the app guide](../app/README.md),
[team setup](../TEAM_SETUP.md) and the corrected results in
`reports/longitudinal_v2_4/`. Launch with `run_app.py`.

The original next-survey classifier is **historical research only**. Its code,
tests, reports and documentation have been restored for comparison, maintenance
and audit, not reactivated in the current interface. No model was retrained.

## Restored material and when to use it

| Purpose | Reference |
|---|---|
| Source data structure and survey definitions | [Data inventory](data_inventory.md), [cohort preparation](cohort_pipeline.md), [mapping notes](feature_mapping_notes.md) |
| Feature mapping validation and future changes | `src/path_project/feature_validation.py`, `scripts/build_feature_mapping.py`, `scripts/validate_feature_mapping.py`, `scripts/inspect_prediction_sources.py` |
| Participant separation and leakage safeguards | [Evaluation protocol](evaluation_protocol.md), `src/path_project/evaluation.py`, `tests/test_evaluation.py` |
| Future alternative models and calibration | `scripts/train_baselines.py`, `scripts/train_tree_models.py`, `src/path_project/trees.py`, `tests/test_baselines.py`, `tests/test_trees.py` |
| Historical results and design rationale | [Model selection](model_selection.md), [original final report](final_project_report.md), `reports/baselines_v1/`, `reports/trees_v1/`, `reports/final_evaluation_v1/` |
| Faculty presentation preparation | [Current faculty guide](faculty_guide.md); historical [viva questions](viva_questions.md) and [presentation outline](presentation_outline.md) |
| Original planning | [Implementation plan](../Project_Analysis_and_Implementation_Plan.md), [original handoff](../PROJECT_HANDOFF.md) |

**Historical documents describe the v1 next-survey target, four-input XGBoost,
old timing decision and earlier metrics. They are not the final report for the
current app.** Use the current faculty guide/protocol for actual claims.
The restored `app/legacy_app.py` is an archival source dependency, not a model
choice in the active UI.

Some historical configuration names also support the current model's shared
schemas. Preserve their fingerprinted meanings. New scientific changes require
a separate named experiment, appropriate participant separation and evaluation;
do not overwrite frozen study artifacts or rerun old exposed-test selection.

## Tests

Default tests exercise the supported current model and handoff:

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider
```

The restored synthetic research tests can be selected explicitly, for example:

```bash
.venv/bin/python -m pytest --research-tests tests/test_cohort.py tests/test_evaluation.py tests/test_baselines.py tests/test_development.py tests/test_inventory.py -q -p no:cacheprovider
```

To collect all historical tests, add `--research-tests` without a file filter.
**Do not expect that full historical suite to pass from the app handoff:** some
tests require the removed private v1 cohort, memberships/models, raw survey
files and research dependencies. Those ignored artifacts were not in Git and
have not been restored. This is not a reason to fabricate artifacts or alter
checksums. CPU-only app dependencies remain in `requirements-app.txt`; the
restored `requirements-lock.txt` is an archival Linux environment snapshot with
optional GPU/research packages, not the recommended app installation command.

After restoration, the 22 default current tests passed. A selected 99 historical
tests covering cohort construction, participant boundaries, baseline models,
feature semantics, source specifications, metric/report logic and small tree
models also passed using synthetic examples (plus local headers/documentation
where applicable). No frozen model was retrained or held-out participant
prediction recomputed. The artifact-dependent historical tests were not claimed
to pass.

Restoration details and original-byte hashes are in `reports/restoration.json`.
The development prompt runner, disposable caches/logs and invalid first
longitudinal diagnostic remain removed. `PATH/` and the current model/cohort
were not changed.
