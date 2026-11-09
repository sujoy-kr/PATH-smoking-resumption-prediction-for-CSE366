# Current project status

Latest change: the app now suppresses out-of-profile and too-sparse inputs, flags horizons that do not beat the baseline, and reports per-horizon calibration. Remaining model-level limitations are in docs/known_limitations.md.

## Active application

Reclaim uses the frozen consecutive-wave v2.1 model. Launch with
`.venv/bin/python run_app.py`; setup instructions are in TEAM_SETUP.md.
Only the current model/UI are supported. The old prompt runner and next-survey
application, models, scripts, reports and tests have been removed.

The current study has 7,643 people with at least three consecutive main-wave
interviews, 1,939 observed returns and 5,704 without an observed return before
follow-up ended. Eight baseline inputs produce approximate 12–60-month
probabilities, fixed 36-month relative risk and exact feature explanations.
Timing uses assumed survey-window midpoints, not individual resumption dates.
Calibration varies by horizon (overestimates at 12 months, underestimates from 18); personal confidence is not
validated. Out-of-profile or too-sparse answers are suppressed;
blank submissions use the fitted study reference. No personal confidence
percentage is invented. Runtime answers/results stay in session memory.

## Necessary files retained

- PATH/: all original survey data and documentation, unchanged and Git-ignored.
- artifacts/longitudinal_v2_1/model.joblib: exact original18,202-byte model bundle,
  included for authorized teammate/faculty inference. Contains sixteen survey-
  derived baseline explanation reference records; no PERSONIDs or full histories.
- data/processed/longitudinal_v2_1/: private current cohort for research verification.
- app/, src/, configs/: current interface and runtime/training dependency closure.
  Some shared module/metadata names are historical and remain necessary for
  deserialization and validated transformations. Do not remove/rename them.
- scripts/: launcher verification, cohort verification, training and handoff builder.
- docs/: current protocol, fingerprinted dictionaries and original input checksums.
- reports/: corrected current model evidence, source-documentation evidence and
  current validation/cleanup records. Source/model/result manifests remain intact.
- tests/:22 current-model, UI and handoff tests with five fictional profiles.
- Smoking_Relapse_Predictor_Presentation.pptx: original coursework presentation.

## Cleanup verification

User explicitly authorized removal of obsolete files while keeping PATH.
The reviewed removal list is in reports/cleanup.json. Approximately 517 MiB of
old prompt logs, caches, initial analysis, retired model/data runs and obsolete
code/docs were removed. The Python environment and Git repository were kept.
The obsolete full research dependency lock was removed; use requirements-app.txt
and requirements-test.txt. No pip uninstall/install performed.

All 22 current tests passed. The current cohort rebuilt exactly, including
features, observation labels, assumed times and participant assignments. All 48
original PATH files matched the retained original-input hashes. Current model
source/artifact/result hashes and five fictional prediction/explanation/timing
checks pass. No model refit or held-out prediction rescoring occurred.
Old v1 test totals are historical and do not describe the cleaned current suite.
The old runner checksum exception is irrelevant because both that runner and its
legacy verifier were removed; the original checksum metadata remains unmodified.

The handoff includes source, matching metadata/evidence and exactly one model.
Its .gitignore exception does not include raw/processed data, secrets or other
artifacts. A clean extracted handoff supports the full current suite without
PATH data. Fresh dependency installation, Windows/macOS runtime validation,
interactive browser verification and public deployment are not claimed.


## Research and faculty-reference restoration

The user requested restoring files useful for maintenance, development and
faculty review. Restored 165 versioned files from HEAD without changing the Git
index/history or overwriting any existing current file. They include original
research/model comparison code, validation utilities, synthetic tests/configs,
aggregate reports, planning/final-report/viva/presentation documentation, archived
legacy-app source and the original full research dependency snapshot.

The previous cleanup removal list is historical and partly reversed; see
reports/restoration.json for exact recovered paths/hashes. All 165 restored files
match their original Git bytes. Current model, inference behavior, source
fingerprints, processed cohort and PATH data are unchanged. No model refit or
held-out participant rescoring. Old ignored model/cohort artifacts were not in
Git and have not been restored. The development prompt runner, master prompt
instructions, invalid first longitudinal diagnostic and disposable logs/caches
remain removed; they are not needed for normal development or app use.

Added docs/RESEARCH_GUIDE.md to distinguish historical v1 references from the
current v2.1 protocol, and docs/faculty_guide.md for current presentation claims.
The original legacy-app source is not routed in the active interface. Current
app dependencies stay CPU-only. Historical tests opt in through
--research-tests; the default suite remains the 22 supported current app tests.
The research dependency snapshot/optional extras are not the app setup route.

Validation: 22 current tests passed; 99 selected restored research tests passed,
covering synthetic cohort, leakage/group boundaries, preprocessing/calibration,
feature mapping and local source headers, metrics/report logic and tiny tree
comparisons. Full old artifact-dependent tests were not claimed runnable without
separately recovered original artifacts. Model startup regression checks remain
unchanged. Earlier work is on GitHub (main); see git log for what is committed. Restored handoff archive
contains code/docs/reports plus exactly the current authorized model, not raw
PATH data or removed private v1 artifacts.
