# Project continuation status

Latest stage requested: **15 only — final objective audit and project handoff**. Stages 1–14 remain complete.
Current state: **Stage 15 complete — final objective audit passed; PROJECT_HANDOFF.md records the runnable local project, measured results and limits**. The final test was evaluated once in stage 11 and remains closed to tuning. Frozen model/categories unchanged; no test rescoring/bootstrap/refitting. Timing C remains unsupported.

## Scope and decisions

- Read original proposal PPTX (all slide text and tables), implementation plan, `.analysis/profile.cjs`, `.analysis/cohort.cjs`, `.analysis/cohort_counts.json`, and both legacy Python scripts. Originals preserved.
- No applicable AGENTS.md found in workspace or ancestor locations checked (`/`, `/home`, `/home/hellfire`, `/home/hellfire/Downloads`).
- Reuse existing working workspace `.venv` with Python 3.13.5. Bare `python` is unavailable; use `.venv/bin/python` explicitly. Windows backup environment preserved and unused.
- Canonical sources: `PATH/DS1001` through `PATH/DS8001`; exclude `PATH/TSV` copies from processing. Seed configured as 366; no random operations yet.
- Historical stage 4 checkpoint: cohort extraction was complete before split creation, training, or final-test evaluation. Stages 5–11 subsequently completed as recorded below. No deployment, Git initialization, commit, or external messaging performed.
- Existing `.git` is a protected placeholder and `git status --short` reports “not a git repository”; do not alter it.

## Completed so far

- Added project directories, configuration, read-only inventory/integrity utilities, meaningful integrity and canonical-path tests.
- Created SHA-256 baseline of 59 original files in `docs/original_inputs.sha256.json` before implementation edits. Includes raw/duplicate inputs, proposal, analysis and existing scripts; excludes mutable virtual environments/control directories.
- `scripts/inventory_inputs.py` completed: aggregate inventory in `reports/input_inventory.json`.
- `.venv/bin/python -m pytest -q`: **2 passed**.
- Saved existing dependency versions in `requirements-lock.txt`; no dependency installation attempted.

## Commands and evidence

Inspection: `pwd`; `ls -la`; `rg --files`; `find . -name AGENTS.md -not -path './.venv/*' -not -path './.venv-windows-backup*/*'`; checked ancestor AGENTS.md files using a shell loop; `command -v python python3 uv pip pip3 git pdftotext unzip`; `.venv/bin/python --version`; `/usr/bin/python3 --version`; `.venv/bin/python -m pip list --format=json`; `git status --short` (failed because placeholder is not repository).
Read plan and legacy scripts using `cat`; extracted original presentation via `python-pptx` (text frames and tables). Converted codebooks to `/tmp/path-wN-codebook.txt` using `pdftotext -layout`; inspected questionnaire covers with `pdftotext -f 1 -l 3`. Original PDFs untouched.
Implementation creation command: `.venv/bin/python /tmp/stage1_setup.py` (one-time scaffolding, not a required pipeline command; final files are the deliverable).
Inventory command: `.venv/bin/python scripts/inventory_inputs.py`.
Test command: `.venv/bin/python -m pytest -q`.
Environment check: inline import/version probe writes `reports/environment.json`.

## Final verification and outputs

- `.venv/bin/python scripts/check_environment.py`: exited 0; selected absolute workspace interpreter, isolated=True, 10/10 essential imports succeeded. Output: `reports/environment.json`.
- `.venv/bin/python scripts/inventory_inputs.py`: exited 0; output `reports/input_inventory.json`. All eight duplicate TSV copies have matching SHA-256. All canonical files have PERSONID, expected row/column counts, zero malformed rows and their codebook/questionnaire present.
- `.venv/bin/python -m pytest -q`: exited 0, **2 passed in 0.01s** (initial and final runs). Tests detect changed/missing source files and enforce canonical unique wave paths.
- `.venv/bin/python -m compileall -q src scripts tests`: exited 0.
- `.venv/bin/python scripts/verify_inputs.py`: exited 0, **59/59 original files unchanged**. Includes all sixteen TSVs, original proposal, original analysis and legacy scripts.
- `docs/data_inventory.md`: verified paths, byte sizes, counts, duplicates, documentation/weight availability, legacy scripts, local tools, scientific cautions and missing inputs.
- `README.md`: current scope, runnable commands, structure and reproducibility instructions.
- `configs/project.json`: eight canonical wave sources, documentation paths, seed 366, output directories, runtime cache and essential imports.
- `pyproject.toml` and `requirements-lock.txt`: intended dependencies and exact current environment snapshot. No install or network access needed; fresh installation was not tested.
- `.gitignore`: preserves prior orchestration rules and adds raw/derived data, environments, artifacts and caches. No repository initialized or mutated; no commit/push performed.

## Limitations and decisions to carry forward

- No separate later-wave weight/linkage datasets or general public-use user guide found. Wave 1–2 TSVs have weights/design columns; waves 3–8 do not have matching columns. Do not claim national representativeness.
- Codebook cohort/outcome sections checked across all eight waves; questionnaire covers inspected. Detailed feature units, eligibility and skip-pattern mapping remain future work. The existing analysis's pairwise cohort numbers were read, not recomputed or adopted as final results.
- Full original PPTX text and tables were inspected; external references and exact collection dates were not independently verified in this stage. No invented citations or dates added.
- Initial Matplotlib probe reported a read-only home cache and fell back successfully to /tmp. The reusable environment checker now uses configured workspace `.cache`, and its check passed without that warning. pip reported a disabled nonwritable home cache during version listing/freezing; both commands succeeded.
- Existing environment reused; Windows backup untouched. Snapshot includes incidental optional packages; only essential dependencies were import-checked. Future model stages should stay CPU-friendly.
- No participant-level output, model, evaluation split or app implementation was generated. Existing all-eight-wave ID output preserved but unused.

## Next step

Await the next numbered prompt. Do not advance automatically. The next data-definition work must harmonize revised variables, missing values, units and questionnaire routing before cohort construction or training. Keep all original inputs and any subsequently locked evaluation splits unchanged on retries. No user action is needed to finish stage 1.

## Stage 2 — implementation and inspection history

Authorized scope: prediction specification and timing feasibility only. No cohort extraction, splitting, training or evaluation. Re-read original implementation plan; no new applicable AGENTS.md found. Inspecting all eight local codebooks and main questionnaires with `pdftotext -layout` into ignored `.cache/stage2/`. Original files will be checked against the stage 1 hash baseline.

Commands so far: `.venv/bin/python /tmp/inspect_stage2.py > /tmp/stage2-inspection.txt` (inspection helper); `rg -n -i` timing, relapse and interview searches against extracted codebooks; stage 1 status/configuration/plan read via `cat`.

Next: finish source inspection, record exact PDF pages and question sections, configure endpoint/harmonization, test specification consistency and verify originals.

### Stage 2 decisions and checks in progress

- Created `configs/prediction_specification.json`, `docs/prediction_specification.md`, `docs/timing_feasibility.md`, documentation inspection/validation scripts, reusable contract validator, and tests. README updated for stage 2.
- Decision C: next-scheduled-survey past-30-day classification. Retain all eight source waves using official derived status; seven adjacent pairs; wave 2–3 revised former indicators. No equal-year intervals, no fabricated event dates. Separate recent-recency/current-established follow-up/Wave 1-exclusion analyses configured.
- Resolved Wave 1 >100 descriptive wording using its actual raw category 6=100 or more and derivation. Found Wave 2 AC1009 skip error and days/months-only units. Approximate last-quit-attempt end dates do exist, but limited routing, product scope and lack of complete first-event history prevent treating them as the core relapse clock.
- Local Wave 8 nonresponse report Table 2.1 (physical PDF pp. 18–19) verifies general wave collection dates; no individual released interview-date/elapsed-interval field found. Questionnaire INTVDATE instruction is not a released data column.
- `.venv/bin/python scripts/validate_prediction_specification.py`: 0 errors on first saved evidence.
- First `.venv/bin/python -m pytest -q`: 4 passed, 1 failed. A synthetic form-feed-only PDF page boundary exposed a parser bug; fixed the heading regex. Next run: **5 passed in 0.02s**. Evidence is being regenerated with the corrected parser before final checks.
- `.venv/bin/python scripts/verify_inputs.py`: **59/59 original files unchanged**. The original baseline has not been rewritten. No split/artifact/data files have been created.

Next action: finish regenerated evidence and final contract/page-reference checks, record results, then stop at stage 2.

## Stage 2 — final results and continuation handoff

**Complete.** The next-survey task is specified before any training. Timing decision **C** is selected and configured. No survival endpoint, fixed-year risk, exact relapse date or persistent-relapse claim is supported for this cohort with the supplied files. No user action is needed to complete stage 2.

### Deliverables

- `docs/prediction_specification.md`: exact cohort entry/exclusion rules, prediction time, all-eight-wave crosswalk with exact local files/physical PDF pages, valid labels, wave-specific missing codes and routing, harmonization, input boundary, secondary definitions, attrition and app claims.
- `docs/timing_feasibility.md`: timing decision C with affirmative evidence about approximate retrospective date/duration fields; why they are not a complete cigarette event history; no usable released individual interview clock; locally verified general collection windows; missed events, censoring assumptions and rejected A/B alternatives.
- `configs/prediction_specification.json`: versioned contract, all seven adjacent pairs, revised former indicators in waves 2–3, label mapping, missing policies, documented missing-code ranges, secondary analyses, source search patterns and restricted app claims. Empty predictor allowlist deliberately awaits feature-level documentation. Existing `configs/project.json` and dependency snapshot unchanged.
- `scripts/inspect_prediction_sources.py`: reproducible full-document text extraction plus **header-only** TSV inspection; handles PDF form-feed page boundaries; writes `reports/prediction_source_evidence.json`.
- `reports/prediction_source_evidence.json`: **189 codebook sections, 89 questionnaire sections across eight waves**, source hashes and exact pages, timing-variable catalog and questionnaire timing mentions. Also includes local Wave 8 nonresponse-report physical PDF pages 9, 15, 18, 19 (collection windows, eligibility/attrition context). Documentation-only excerpts and public aggregate tables, no raw participant values.
- `src/path_project/specification.py` and `scripts/validate_prediction_specification.py`: validate configured crosswalk against actual TSV headers, source evidence, source-baseline fingerprints, status labels, missing-code maps and temporal policies.
- `scripts/check_prediction_evidence.py`: independently re-extracts cited starting PDF pages and verifies variable identifiers; writes aggregate `reports/prediction_specification_checks.json`.
- `tests/test_prediction_specification.py`: contract/source checks, PDF page-boundary regression and secondary-definition/app restrictions. Existing stage 1 tests retained. README updated with stage 2 scope and commands.

### Exact reproducible commands and actual results

1. `.venv/bin/python scripts/inspect_prediction_sources.py` — exited 0; eight waves, all 16 main PDFs and one supplemental PDF inspected. Repeated during parser development; final regenerated evidence uses corrected page-boundary parsing.
2. `.venv/bin/python scripts/validate_prediction_specification.py` — exited 0, **0 errors**, including final regenerated evidence.
3. `.venv/bin/python scripts/check_prediction_evidence.py` — exited 0, **64/64 cited PDF starting-page checks**, 0 errors. Saved checks cover core/secondary status, last-cigarette recency and approximate quit-attempt end-date references across all eight waves.
4. `.venv/bin/python -m pytest -q` — final run exited 0, **5 passed in 0.02s**. Earlier failure and fix recorded above; no failed result is reported as passed.
5. `.venv/bin/python scripts/verify_inputs.py` — exited 0, **59/59 original files unchanged**, final stage 2 run. Original hash baseline remains unchanged.
6. `pdftotext -v` — version **25.03.0**; `.venv/bin/python --version` — **Python 3.13.5**. No packages installed or changed; stage 1 dependency versions retained.

Exploration additionally used `cat PROJECT_STATUS.md`, `cat configs/project.json`, `cat Project_Analysis_and_Implementation_Plan.md`, ancestor/workspace AGENTS.md searches, and `rg -n -i` searches for interview/date, relapse/resumption, last-use and quit-attempt terminology in extracted documents. One-time local helpers `.venv/bin/python /tmp/inspect_stage2.py > /tmp/stage2-inspection.txt`, `.venv/bin/python /tmp/write_stage2_docs.py` and an inline execution of `/tmp/write_timing_docs.py` assisted inspection/table authoring; delivered Markdown is maintained documentation, while the committed-source-style evidence generator and validator above provide the reproducible checks. No Git commit was made.

Final inline checks verified all local links in README and the two new specification documents resolve; source catalog coverage includes all R-prefixed header variables and PERSONID (only CASEID and early design fields outside the R-variable index); there are no interview-date header candidates; `data/processed/` and `artifacts/` still contain only their README placeholders. Documentation caches are ignored under `.cache/stage2/`.

### Scientific limitations to preserve

- Status constructs are harmonized using supplied official derivations, not assumed identically worded or measured in every wave. Wave 1 threshold prose is resolved by category 6=100 or more and the algorithm. Wave 1 exclusion sensitivity is configured; remaining instrument/population/interval differences require interval-specific reporting later.
- Recent-quitter analysis is an **observed recency proxy**, with distinct Wave 1 wording, routed missingness, Wave 2 days/months-only units and documented skip error. Unknown recency is not assigned to a long-term category. Boundary-rounding sensitivity is configured.
- Approximate last-quit-attempt dates exist, but restricted eligibility, product-dependent questions, incomplete event history and absent individual elapsed follow-up prevent using them as universal first cigarette-relapse times. No individual raw date values were parsed or emitted.
- General collection dates were verified locally from Table 2.1 of the Wave 8 nonresponse report. They cannot yield individual intervals, one-/two-/three-year risk or fabricated relapse dates.
- Valid follow-up No means no past-30-day smoking at that interview, not continuous abstinence; absent/invalid follow-up is unlabeled and requires attrition reporting. No final sample-size or outcome-prevalence claim was made.
- No detailed candidate-predictor dictionary yet; only temporal admissibility is established. Existing later-wave weights/user-guide limitations from stage 1 remain. No national, clinical, causal or performance claims are supported.

### Next step

Await the next numbered user prompt. Do not advance automatically. Future authorized data work must document candidate predictors, units, skip patterns, baseline availability and harmonization before extracting a cohort. Verify PERSONID uniqueness before joining. Lock participant splits before learning preprocessing or models, and preserve those split files on retries. No splits currently exist; none were opened, overwritten or evaluated in stage 2.

## Stage 3 — implementation and inspection history

Inspecting the existing plan, stage 2 endpoint contract, actual headers and cached local PDF sections for a compact candidate feature set. No new AGENTS.md found in workspace/ancestors. No participant rows or final-test outcomes are used to choose candidates. Original survey/proposal/analysis baseline and any existing splits will be preserved.

Next: inspect exact labels and eligibility across waves; create feature mapping plus flattened dictionary; implement and run header/source validation and meaningful mapping-rule tests; verify original hashes.

### Stage 3 implementation and interim checks

- Curated 25 candidates: 5 demographic, 1 quit-recency, 2 prior-intensity/duration, 7 other-tobacco, 2 household, 8 health/behavior constructs. No outcome-informed selection. All eight waves mapped; missing/conditional applicability retained.
- Added `configs/feature_mapping_recipe.json`, enriched `configs/feature_mapping.json`, `docs/feature_dictionary.csv`, `docs/feature_mapping_notes.md`, public-documentation source evidence and header/role/source validator. Added deterministic scalar transformations exercised on synthetic inputs only.
- Linked stage 2 candidate allowlist to the dictionary without changing cohort/outcome/timing definitions. The old stage 2 test requiring an empty allowlist now checks documented role-based membership. README and the active prediction-specification paragraph updated to describe stage 3.
- `.gitignore` adds only `!/docs/feature_dictionary.csv` as a metadata exception; raw survey, participant-level, split and artifact ignore rules remain.
- Initial recipe-authoring helper had a bracket syntax error and produced no recipe until corrected. First mapping build correctly stopped on an ambiguous 0–30 versus 1–90 alcohol range: routing dependencies were being treated as a question's own range. Fixed range attribution to the actual question. An interim validation found one missing employment cross-wave note; added it.
- First transformation test run: 13 passed, 1 failed, exposing nested transform specifications in the authored recipe. Flattened those records, strengthened the schema validator and added a synthetic valid-response test for every candidate/wave. Subsequent 16-test run passed. After preserving soft/hard range-check distinction and source numeric precision, final-so-far run: **18 passed in 0.61s**. No failed run is reported as successful.
- `.venv/bin/python scripts/validate_feature_mapping.py`: **25 candidates, 494 source-column references, 288 dictionary rows, 0 errors**. Header-only actual-data validation; no participant rows read.
- `.venv/bin/python scripts/validate_prediction_specification.py`: **0 errors** after allowlist linkage.

Next: complete independent documentation-heading checks, reproducibility check and final original-file verification; then record stage 3 completion and stop.

## Stage 3 — final results and continuation handoff

**Complete.** The project now has a documented, machine-readable 25-candidate feature mapping. Every configured nonempty source mapping resolves to a real column in the appropriate canonical adult TSV header. Candidate meanings, categorical labels, numeric units/constraints, missing/structural routing, former-smoker applicability, historical dependencies, app questions and prediction-time availability are documented. No user action is needed for this stage.

### Final artifacts and important decisions

- `configs/feature_mapping_recipe.json`: curated configuration/decisions and deterministic transformation recipes; all scientific constants/conversion factors live in configuration.
- `configs/feature_mapping.json`: enriched executable mapping; **25 candidates**, **36 total separated fields** (25 candidate, 3 cohort/QC, 2 outcome, 2 identifier, 4 design/weight). Each has eight wave entries. All candidates use starting-wave columns only.
- `docs/feature_dictionary.csv`: requested public metadata dictionary, **288 field/wave rows**, including 200 candidate/wave mappings. Nested cells are JSON; no participant values or PERSONIDs are stored.
- `docs/feature_mapping_notes.md`: candidate summary, cross-wave harmonization, source/CSV navigation, conditional eligibility, unit and numeric-range decisions, rejected candidates, app limits and reproduction commands.
- `reports/feature_mapping_evidence.json`: **1,061 documentation reference records** from all 16 main local PDFs, source fingerprints and actual-header audits. Full source labels/ASK/GOTO/program/algorithm evidence retained. Only documentation/public aggregate summaries, no participant rows.
- `reports/feature_mapping_validation.json`: actual-header, role, source, dictionary and transformation checks; **494 source-column references**, 0 errors. Unique configured source columns by wave: 139, 140, 39, 32, 32, 32, 32, 32. Missing late-wave design/weight fields are explicitly unavailable with no fabricated column.
- `reports/feature_evidence_checks.json`: independent page-restricted PDF extraction verified **1,061/1,061 indexed variable headings on 668 physical pages**, 0 errors.
- `reports/feature_mapping_reproducibility.json`: final rebuild of mapping, CSV and source evidence was **byte-identical**; before/after SHA-256 values saved and correspond to the final artifacts.
- Reusable modules: `src/path_project/documentation.py`, `src/path_project/features.py`, `src/path_project/feature_validation.py`. These inspect public documentation, apply deterministic scalar mappings, and validate the contract; no learning or cohort construction. Tests transform synthetic examples only.
- Commands: `scripts/build_feature_mapping.py`, `scripts/validate_feature_mapping.py`, `scripts/check_feature_evidence.py`. Both validation/check commands support `--no-write` for read-only audits. Builder caches text only when PDF and cached-text fingerprints match; cache under ignored `.cache/stage3/documents/`.
- Active `configs/prediction_specification.json` allowlist now links to the 25 documentation-selected candidates. Cohort, outcome, seven adjacent pairs, timing decision C and scientific claims remain unchanged. README and one active-specification paragraph updated accordingly. The prior empty-allowlist test now verifies dictionary role membership instead.
- `.gitignore` retains all prior sensitive-output rules, with only `!/docs/feature_dictionary.csv` added for public dictionary metadata. No repository initialization, commit, push, publication or deployment. Dependency configuration/versions and fixed seed 366 unchanged; no packages installed.

### Final commands and actual check results

1. `.venv/bin/python scripts/build_feature_mapping.py` — exited 0, generated the three requested/documentation artifacts; 25 candidates, 36 separated fields, 1,061 evidence references.
2. `.venv/bin/python scripts/validate_feature_mapping.py` — exited 0, **25 candidates / 494 column references / 288 rows / 0 errors**, including the final build. `--no-write` avoids updating the saved report during an audit.
3. `.venv/bin/python scripts/check_feature_evidence.py` — exited 0, **1,061/1,061 headings**, 668 physical PDF pages, 0 errors. Documentation-only page extraction, no model/evaluation activity.
4. `.venv/bin/python scripts/validate_prediction_specification.py` — exited 0, **0 errors** after feature-contract linkage.
5. `.venv/bin/python -m pytest -q` — final run exited 0, **19 passed in 0.61s**. Includes the original stage 1/2 checks plus missing-duration/skip semantics, per-question unit codes, all 200 candidate/wave transforms on synthetic valid answers, age/education coarsening, household contradictions, source range versus observed extrema, source precision, soft range checks, future/identifier rejection, malformed-schema rejection and binary outcome labels.
6. `.venv/bin/python scripts/verify_inputs.py` — final stage 3 run exited 0, **59/59 original files unchanged**. Original input-hash baseline was never rewritten.
7. Reproducibility command: an inline Python script fingerprints `configs/feature_mapping.json`, `docs/feature_dictionary.csv`, `reports/feature_mapping_evidence.json`, executes `[sys.executable, 'scripts/build_feature_mapping.py']`, fingerprints again and saves `reports/feature_mapping_reproducibility.json`. Final comparison **True**; fresh rebuild byte-identical.

One-time authored helpers were `.venv/bin/python /tmp/create_feature_recipe.py` and `.venv/bin/python /tmp/write_feature_notes.py`; delivered configuration/Markdown are maintained source documentation, and the workspace builder/validators above are the reproducible pipeline commands. Header/catalog and local-link inspections used inline Python plus `rg` on ignored extracted text. Inspection re-read the implementation plan and endpoint contract and found no new applicable AGENTS.md. The original proposal/analysis remained protected by the verified input manifest.

The earlier development failures and fixes are recorded above. Final review additionally corrected the **output** labels for recoded outcome fields to 0=No/1=Yes while retaining their **source** labels 1=Yes/2=No; strengthened label-domain validation for every categorical role and added a regression test. This did not alter the stage 2 outcome definition. Soft source checks and explicit analytic admissibility rules are distinguished; observed maxima never became validity bounds.

### Limitations to preserve

- All 25 are candidates, not a fitted or outcome-selected subset. No final-test outcomes or participant rows were inspected to choose them. No cohort table, fit, imputation, encoder, calibration, resampling or model evaluation exists from this stage.
- Wave 2 has no derived cigarette DAYSQUIT field; raw AC1009 number/unit supplies only days/months. Other waves can include years. Missing or skipped duration remains unknown; no historical reconstruction or carry-forward enabled. Recorded recency is history, never time until relapse.
- Prior regular intensity/duration and quit recency are conditional and often structurally absent, especially later-wave repeated former respondents. Future authorized preparation must report coverage, preserve reasons, and only make data-driven feature reductions on training participants after split locking. App-answerability does not imply complete observed PATH coverage.
- Age and education are explicitly coarsened; income is nominal USD; released sex/gender is limited to the recorded binary categories and historical meaning. Product lists change, notably e-cigarette→electronic-nicotine and household nicotine-product scope. Do not claim perfect measurement invariance.
- Some numeric questions lack a universal finite upper validity bound; source precision, unit-specific digit notes and range-check strength are retained without inventing an upper bound from observed sample extrema. An analytic out-of-range flag is not learned clipping.
- Identifier/design/outcome roles are never predictors. Wave 8 candidate mappings are schema documentation only under the current seven-pair task; its answers cannot become 7→8 baseline inputs. Later-wave weight availability remains limited; national inference is not enabled.
- Stage 2 timing/app limits remain: next-survey status only, variable intervals, observed-outcome conditioning, no exact relapse dates/fixed-year risks/persistent-relapse/clinical/causal/national/performance claims.

### Scope/preservation checks and next step

Final local-link checks passed for README, prediction specification and feature notes. `data/processed/` and `artifacts/` still contain only their README placeholders; no participant-level or fitted output or locked split was created, read, rewritten or evaluated. Original PATH copies, proposal, scripts and `.analysis` files all match their original hashes.

Await the next numbered prompt; do not advance automatically. Future authorized cohort extraction must consume the machine-readable role/temporal mapping, validate PERSONID uniqueness before joins, preserve structural missingness/attrition, and retain only baseline predictors for each pair. Lock participant evaluation splits before learning transformations or selecting features from data, and preserve any subsequently locked split files on retries.

## Stage 3 audit correction — in progress

Audit found that the smokeless-tobacco common description/app prompt incorrectly excluded all snus although Wave 2 AS1004 explicitly includes loose snus (questionnaire physical p. 93). Rechecking all eight wave-specific AS/AU question definitions, including the companion snus feature, before correcting recipe/JSON/CSV and adding semantic source regression coverage. The previous complete declaration is superseded while this correction is underway. Original inputs and previous evaluation state remain protected; no participant-row processing or later-stage work.

## Stage 3 audit correction — completed and verified

The audit finding is corrected. The previous complete declaration missed a semantic mismatch even though header tests passed: “smokeless tobacco other than snus” incorrectly excluded loose snus in early waves. This correction supersedes the earlier wording and earlier 19-test completion evidence.

### Source findings and scientific correction

- Rechecked relevant AS/AU questionnaire sections across all eight waves and the official P30D_SMKLS/P30D_SNUS derivations. Wave 1 questionnaire physical PDF p. 49 includes AS1002_02 (loose snus, moist snuff, dip, spit or chewing tobacco) and a separate snus-pouch choice. Wave 2 AS1004 explicitly includes loose snus (physical p. 93), while AU1004 asks about snus pouches (p. 91). Wave 3 preserves that question distinction.
- Waves 4–8 AS1004 excludes snus, while AU1004's image instruction includes **both loose and pouches**. The companion `snus_p30d` field therefore also required a wave-specific description; a universal pouches-only label would be wrong later. Exact local file/variable/page citations are in the dictionary and the added product-scope section of `docs/feature_mapping_notes.md`.
- Early AU brand screens/derived algorithms include Skoal Bandits routing. Its evidence is explicitly attached. No universal brand exclusion, new product reassignment or replacement derivation was invented: use the supplied official status and preserve unknown where source routing/history cannot be reproduced in a demo. Measurement invariance is not asserted.

### Files and behavior changed

- `configs/feature_mapping_recipe.json`: corrected common descriptions/prompts for `smokeless_tobacco_p30d` and `snus_p30d`; added per-wave `description`, `app_prompt`, `app_notes`, structured `product_scope` and documentation-backed `semantic_source_assertions` for both. All 25 candidate names, source columns, unit conversions, missing rules and label mappings retained.
- `scripts/build_feature_mapping.py`: registers semantic evidence and exports wave-specific descriptions/prompts/notes rather than repeating the common text. CSV now also includes `product_scope` and `semantic_source_assertions` JSON cells.
- Regenerated `configs/feature_mapping.json`, `docs/feature_dictionary.csv`, `reports/feature_mapping_evidence.json`. The mapping still has **25 candidates, 36 separated fields, 288 field/wave rows**. No cohort, outcome, prediction-time or timing-decision changes.
- `src/path_project/feature_validation.py`: checks configured source phrases and required/forbidden product wording against per-wave descriptions/prompts/notes; an available column alone no longer passes the corrected semantic assertions.
- `scripts/validate_feature_mapping.py`: additionally checks CSV descriptions, app prompts/notes, scope and semantic assertions against the wave-specific mapping, preventing loss of overrides in export.
- `tests/test_feature_mapping.py`: added three semantic tests: actual Wave 2 loose-snus source/prompt agreement; rejection when the original bad prompt is restored; and all-eight-wave paired scope/CSV propagation checks.
- `docs/feature_mapping_notes.md`: corrected summary rows and added an all-wave source table, brand-routing caveat, audit explanation and the app's required per-wave prompt lookup. README notes the starting-wave-specific product distinction.
- Refreshed `reports/feature_mapping_validation.json`, `reports/feature_evidence_checks.json` and `reports/feature_mapping_reproducibility.json`. Original raw/analysis/proposal files and original hash baseline untouched.

### Exact commands and actual final results

- Inspection: AGENTS.md workspace/ancestor searches (none found), `head -10 PROJECT_STATUS.md`, reads of the existing builder/validator/tests, original implementation plan and saved source evidence. Direct source check used `pdftotext -f 49 -l 50 -layout PATH/DS1001/36498-1001-Questionnaire.pdf -`; the Wave 2 physical-p.93 wording was also retained in the evidence and regression test.
- One-time recipe edit helper: `.venv/bin/python /tmp/correct_product_scope.py`; all enduring decisions are in the recipe, not dependent on the helper.
- `.venv/bin/python scripts/build_feature_mapping.py` — exited 0, **25 candidates, 36 fields, 1,061 documentation references**. Repeated for deterministic rebuild verification; no survey rows read.
- `.venv/bin/python scripts/validate_feature_mapping.py` — exited 0, **494 source-column references, 288 dictionary rows, 0 errors**. Reads actual canonical TSV headers and checks source/semantic/CSV consistency.
- `.venv/bin/python scripts/validate_prediction_specification.py` — exited 0, **0 errors**. Cohort/outcome/timing and candidate allowlist remain consistent.
- `.venv/bin/python -m pytest -q` — final run exited 0, **22 passed in 0.82s**. Tests use synthetic values or documentation/header metadata, not participant/final-test outcomes.
- `.venv/bin/python scripts/check_feature_evidence.py` — exited 0, **1,061/1,061 source headings across 668 physical PDF pages**, 0 errors. Saved evidence refreshed.
- `.venv/bin/python scripts/verify_inputs.py` — exited 0, **59/59 original files unchanged**.
- An inline Python reproducibility check fingerprints mapping/CSV/evidence, runs `[sys.executable, 'scripts/build_feature_mapping.py']`, fingerprints again and saves `reports/feature_mapping_reproducibility.json`: **byte-identical=True**, with corrected current-artifact SHA-256 values.
- Final inline CSV checks confirmed the Wave 2 smokeless prompt includes loose snus, the Wave 4/8 snus prompts include loose snus and pouches, and `data/processed/` and `artifacts/` still contain only their README placeholders.

### Remaining limits and next step

This corrects wording and its validation, not instrument differences in the underlying surveys. Product scope and early brand routing remain explicit limitations; use the starting-wave prompt/notes and supplied derived indicator, and do not claim cross-wave measurement invariance. All other documented stage 3 limitations (conditional history, missing values, numeric bounds, app scope and missing later weights) still apply. No dependency changes or random operations; fixed seed and version snapshot retained.

Stop at stage 3 and await the next numbered prompt. No cohort extraction, split creation, training, tuning, calibration, final evaluation, Git initialization, commit/push, publication, upload, deployment or external messaging occurred. No locked split was changed. No user action is needed to finish this correction.

## Stage 4 — in progress

Re-read the prediction definition, corrected feature mappings and legacy cohort-count diagnostic. No new AGENTS.md found. Selected `.venv/bin/python` (Python 3.13.5); pandas 3.1.1 and pyarrow 26.0.1 imports succeed. Existing processed/artifact directories contain README placeholders only; no locked splits exist. Will load only canonical selected TSV columns as strings, validate per-wave PERSONID uniqueness, construct adjacent-pair labeled rows and an unobserved-outcome ledger, and report aggregate flow/missingness. No raw files, original analysis, proposal or input manifest will be modified.

Next: implement/test pure cohort functions with a clearly synthetic fixture, then execute and verify the actual pipeline.


## Stage 4 — completed implementation and verification

Implemented `configs/cohort.json`, `src/path_project/cohort.py`, `scripts/build_cohort.py`, `scripts/verify_cohort.py`, `scripts/diagnose_cohort_recency.py`, `tests/test_cohort.py`, and the clearly fictional `tests/fixtures/synthetic_cohort.json`. Added pyarrow to declared core dependencies; the existing lock already pins pyarrow 26.0.1, so no installation or network access was needed. Updated README and `docs/cohort_pipeline.md`. Stage 1–3 history above describes those stages at their completion; their earlier “no cohort” statements are historical.

### Results and decisions

- Canonical DS files only, once per wave; no PATH/TSV duplicates processed. All eight PERSONID columns validated unique and stable strings. Selected columns per wave: 35, 36, 38, 31, 31, 31, 31, 3. Duplicate/invalid IDs fail without printing values; joins validate one-to-one.
- Seven adjacent pairs, no all-eight-wave intersection, documented baseline-only transformations, no learned preprocessing or participant splits. Candidate missing values and component-specific skip/no-answer reasons retained separately; no feature-based complete-case exclusion.
- Saved 30,890 labeled intervals from 9,597 people; 3,258 positive, 27,632 negative (10.5471% positive). Of these people 6,830 contribute multiple intervals; 21,293 records are beyond the first per person.
- Ledger preserves all 36,639 eligible intervals from 11,717 people, including 5,749 unobserved outcomes: 5,746 absent next interviews and three system-missing responses. None are coded negative.
- Pair labeled/positive/unobserved: 1→2 3684/416/717; 2→3 4090/447/490; 3→4 4164/505/521; 4→5 4722/563/748; 5→6 4463/393/1384; 6→7 4861/478/993; 7→8 4906/456/896.
- Main and secondary status counts match preserved `.analysis/cohort_counts.json`. Recent-proxy differences are fully explained in `reports/cohort_v1_recency_diagnostic.json`: Wave 2's absent derived field caused legacy zero vs raw-pair 812 records/278 positive; Wave 6 and Wave 7 raw one-year boundary conversions add 109/30 and 113/32 respectively because released 365.3-day rounded values exceed the legacy 365.25-day cutoff. Exact released values, source precision, joins and all deltas checked. Separate preconfigured boundary sensitivity retained.
- Important availability limits: raw recency 10,150/30,890, prior intensity 4,526/30,890, regular-smoking duration 4,793/30,890; most missingness is conditional routing. All 25 candidates retained; future decisions must use training participants only. No undocumented reconstruction/carry-forward. Timing remains C, next-survey status with varying unknown individual intervals; no calendar event time, exact relapse date or fixed-year risk.
- Data outputs are ignored local files `data/processed/cohort_v1/cohort.parquet`, `eligible_interval_ledger.parquet`, `schema.json`, `run_manifest.json`. Aggregates: `reports/cohort_v1/` JSON/CSV flow, availability, component missingness, legacy comparison, schema, provenance, validation, input audit and Markdown report. No participant IDs or individual rows emitted in reports.
- Run is immutable; identical retries verify and reuse. Signature: `da0b2d5bed66345a66c93393bbcafd8f6e36ff3bddc925b585b331c895492965`. Preserve v1 on any future correction, and use a separately documented new run rather than replacing this output or any future locked split.

### Commands and checks actually run

- Re-read implementation plan, prediction specification, feature mapping/notes, existing cohort JavaScript and `.analysis/cohort_counts.json`; no applicable AGENTS.md found. Existing stage 1 proposal extraction and original-input inventory retained. Interpreter/import probe confirmed `.venv/bin/python`, Python 3.13.5, pandas 3.1.1, pyarrow 26.0.1.
- `.venv/bin/python -m pytest -q`: initial synthetic failure identified incorrect raw missing codes in the fixture for a derived indicator. Corrected fictional fixture to documented derived codes; did not weaken production validation. Subsequent run: 33 passed. Added explicit one-year rounding regression.
- `.venv/bin/python scripts/build_cohort.py`: exit 0, built new immutable run successfully. Reports validate unique interval keys, adjacent pairs, binary observed labels, null unknown outcomes, stable string identifiers, feature/reason consistency and exact nullable Parquet round trip. No trained artifact generated.
- `.venv/bin/python scripts/diagnose_cohort_recency.py`: exit 0; all three changed intervals explained, including exact 365.3 released rounding checks. Emits aggregate counts only; leaves immutable run untouched.
- `.venv/bin/python scripts/verify_cohort.py`: exit 0; 30,890 labeled rows and 36,639 eligible intervals verified; main/ledger keys and labels, aggregate availability, baseline component provenance and report-ID checks passed.
- `.venv/bin/python -m pytest -q -p no:cacheprovider`: exit 0, **34 passed in 1.68s**. No real participant records in test fixtures, no training/evaluation.
- `.venv/bin/python scripts/verify_inputs.py`: exit 0, **59/59 original files unchanged**, including datasets, proposal, original analysis and scripts. Baseline manifest not regenerated.

### Next step

Stage 4 is complete. Await the next numbered prompt; do not advance automatically. No participant split, training, tuning, calibration, reserved evaluation, app implementation, Git operation, publication, upload, deployment or external message occurred. Future participant grouping must use internal PERSONID while model inputs use only the schema's explicit 25-candidate allowlist. No user action is required.

### Final retry-preservation check

- `.venv/bin/python /tmp/verify_stage4_retry.py` snapshots the 17 immutable data/report files, invokes `.venv/bin/python scripts/build_cohort.py` through the selected interpreter, and compares SHA-256 plus modification times. Exit 0: `Mode: reused_verified_immutable_run`; **17/17 files unchanged**. Saved aggregate evidence: `reports/cohort_v1_retry_verification.json`. This helper is not required for routine use; its evidence records the exact builder command. No run file or locked split was replaced.

## Stage 5 — in progress

Authorized evaluation protocol and split locking only; no model development or final-test performance. No new AGENTS.md found. Re-read implementation plan split requirements and stage 4 prediction contract. Will use deterministic SHA-256 participant buckets with 25% held out, Wave 7→8 as test only, and all earlier records of held-out participants excluded. Non-held-out Waves 1→2 through 6→7 support separate tuning/calibration/threshold participants; their Wave 7→8 rows are excluded from development. Assignment and minimum-size gates configured before reading split-specific development outcomes; final-test outcomes will not be read. Existing cohort and future locked memberships must remain immutable.


## Stage 5 — completed protocol and locked membership

### Files and implementation

- `configs/evaluation.json`: prespecified hash namespaces/seed 366, 25% held-out participant buckets, 70/15/15 development-role buckets, five grouped folds, temporal restrictions, minimum case/size gates and later selection/calibration/threshold/uncertainty rules. Created before inspecting split-specific development labels. No outcome-based split search or alternative was needed.
- `src/path_project/evaluation.py`: deterministic role/fold assignment, membership assertions, immutable creation/reuse, development-only filtered data access, exact authorized-batch checks, clone-and-fit complete Pipeline boundary, participant metric weights. No test accessor provided.
- `src/path_project/training_boundaries.py`: public future fitting entry point loads its own locked tuning data, checks the cohort-mapping fingerprint and nonempty unique candidate subset, and rejects arbitrary future/admin/outcome fields. No real model was fitted through this entry point.
- `scripts/create_evaluation_splits.py` and `scripts/verify_evaluation_splits.py`: aggregate-only creation and read-only verification; no final-test labels/features loaded. Split provenance saves actual Python and pandas/pyarrow/scikit-learn versions; existing `requirements-lock.txt` retained, no install/network needed.
- `tests/test_evaluation.py`, `tests/fixtures/synthetic_evaluation.json`: 21 synthetic-only boundary tests added (suite now 55). Cover order invariance, hash/group folds, test-access rejection, held-out/calibration/threshold/future/validation rows excluded from fitting, feature allowlist, temporal labels, duplicates, participant weights, and a toy Pipeline fit proving training-only preprocessing. Synthetic DummyClassifier fits are correctness tests only, never PATH models.
- `docs/evaluation_protocol.md`: exact hash rule, all partition purposes, feasibility counts, future evaluation/metric/uncertainty procedures, class-vs-survey weighting, attrition and temporal/generalization limitations. README updated.

### Actual locked counts and decisions

- Assigned 11,717 eligible people by identifiers only: heldout 2,929; tuning 6,212; calibration 1,268; threshold 1,308. People without suitable observed development rows retain membership without being added to training.
- Test: **1,243 eligible Wave 7→8 records from 1,243 held-out people**. The prespecified minimum of 500 records passes. No test prevalence/positive count inspected or reported; sample size is not a power/precision guarantee.
- All 6,516 earlier labeled records of held-out people excluded. All 3,663 non-held-out Wave 7→8 records excluded from development. No leakage through pooled later-period labels. Every development interval starts at Wave ≤6, with outcome at Wave ≤7.
- Tuning: 13,757 records / 4,692 people / 1,487 positives / 12,270 negatives. Five validation folds have records 2799/2619/2537/2861/2941 and positives 292/302/299/296/298, satisfying the fixed 30-positive/30-negative minima. Each participant stays in one fold; fold training uses only the other four tuning folds.
- Calibration: 2,801 records / 947 people / 312 positive / 2,489 negative. Threshold: 2,910 records / 990 people / 336 positive / 2,574 negative. Both exceed fixed 50-positive/30-negative gates.
- Tune/select only within grouped tuning CV; mean participant-weighted AP primary, simpler candidate on exact tie. Refit frozen base Pipeline on tuning people only. Later sigmoid calibration uses calibration people only; threshold maximizes participant-weighted F1 on threshold people, tie chooses larger threshold. No refit on calibration/threshold participants under this protocol. Risk categories remain unsupported without separate validation.
- Repeated records handled by participant-equal metric weights (1/n records) with ordinary interval metrics secondary; future uncertainty is participant-cluster bootstrap, seed 366, 1000 replicates, percentile 95% intervals and explicit invalid-replicate reporting. Final test has one record per person. No bootstrap or model metrics run now.
- Class weighting is train-only imbalance handling, not survey design weighting or participant metric weighting. Evaluation rows are never resampled/balanced. No national representativeness, calendar-year risk, personal confidence or causal claim. Test remains conditional on valid observed follow-up; whole-cohort stage 4 descriptive counts predate this label-blind split.

### Output paths and actual commands/checks

- `.venv/bin/python scripts/create_evaluation_splits.py`: exit 0, `created_immutable_lock`, saved ignored `artifacts/evaluation_v1/participants.parquet`, `records.parquet`, `manifest.json`; aggregates in `reports/evaluation_protocol_v1.json`. No label/feature columns in membership files.
- `.venv/bin/python -m pytest tests/test_evaluation.py -q -p no:cacheprovider`: initial 19 stage-5 tests passed in 1.15s. Added two public-entry-point tests afterward.
- `.venv/bin/python -m pytest -q -p no:cacheprovider`: exit 0, **55 passed in 2.59s**, including all stage 1–4 regression tests. Real participant data are not used for synthetic fits.
- `.venv/bin/python scripts/verify_evaluation_splits.py`: exit 0, verified all 30,890 labeled cohort keys covered exactly; immutable membership, temporal restrictions and five participant-disjoint folds passed; test features/outcomes unopened.
- `.venv/bin/python /tmp/check_stage5_access_retry.py`: exit 0. Wrapped the actual development Parquet reader to assert held-out participants absent from the read predicate and maximum start wave 6; returned fold-0 training keys also exclude held-out people and follow-up beyond Wave 7. No model fitted. Invoked `.venv/bin/python scripts/create_evaluation_splits.py` again and verified `reused_verified_lock`; **21/21 existing cohort/split files retained identical SHA-256 and mtime**. Evidence in `reports/evaluation_boundary_verification_v1.json`, also recording supplemental boundary/test source hashes. Temporary helper is not a required project command.
- No new applicable AGENTS.md found in workspace/ancestors; original implementation-plan evaluation sections read. Previous dataset, proposal, analysis and immutable cohort preserved; no Git operations, publication, upload, deployment or external messages.

### Next stage and limitations

Stop at stage 5. Await the next numbered prompt. Model development must use the locked public boundary API and the tuning folds; keep calibration/threshold roles separate and final test closed until the authorized final-evaluation stage. Low historical-feature availability, conditional questionnaire routing, instrument changes and informative missing follow-up from stage 4 remain limitations. No split alternative, user input or dependency installation is needed. A protocol-code or membership mismatch must fail rather than silently regenerate; preserve v1 on any future correction. Earlier status entries refer to their stages' historical scope.

### Stage 5 final preservation/privacy checks

- `.venv/bin/python scripts/verify_inputs.py`: exit 0, **59/59 original files unchanged**.
- `.venv/bin/python scripts/verify_cohort.py`: exit 0; prior 30,890-row labeled cohort and 36,639-row ledger retain valid keys, labels, availability, baseline provenance and aggregate-report privacy.
- Final `.venv/bin/python scripts/verify_evaluation_splits.py`: exit 0; unchanged locked membership and five separated folds verified.
- Inline read-only report/document token check against internal identifiers passed; no participant-ID tokens in the stage 5 reports or protocol. Membership files contain no outcomes or predictor values. Saved versions: pandas 3.1.1, pyarrow 26.0.1, scikit-learn 1.9.1.

## Stage 6 — in progress

Explore tuning participants only at starting Waves 1–6; calibration/threshold/test participants excluded from all summaries and feature choices. Stage 4 cohort and stage 5 hash memberships remain immutable. Existing mapping/specification JSON files are fingerprinted by those locks, so final profiles will be added as explicit versioned mapping/specification/dictionary supplements referencing unchanged originals rather than breaking the locked inputs. No cohort definition or recoding changes planned. Inspecting missingness, numerical review flags, repeated observations and baseline-characteristic follow-up availability. Attrition requires baseline answers for eligible unlabeled intervals: read selected earlier-wave raw columns in chunks, filter immediately to tuning-ledger IDs, and harmonize only those rows. Never read Wave 7/8 raw files or test features/outcomes. No model fitting authorized.


## Stage 6 — completed tuning-only exploration and final inputs

### Scope, decisions and actual findings

- No applicable AGENTS.md found in workspace/ancestors. Re-read implementation-plan harmonization/baseline/leakage sections and existing specifications, mappings and split code. Used the existing isolated `.venv/bin/python` (Python 3.13.5); no installs, network or extra services.
- Only locked tuning participants and starting Waves 1–6 explored. Calibration, threshold and all held-out people excluded from statistics and feature decisions. Source-document inspection of later-wave definitions uses documentation, never test responses. SHA checks may stream all original files as opaque bytes; no final-test feature/outcome interpretation occurred.
- 13,757 labeled tuning intervals / 4,692 people / 1,487 positives. Eligible ledger: 16,338 intervals / 5,716 people / 2,581 unobserved outcomes. 3,191 people have repeated labeled records; 9,065 records are beyond each person's first. Counts agree with the locked tuning partition.
- Observed raw quit recency 4,820/13,757 (8,937 unknown/skipped); prior intensity 2,294 observed; regular-smoking duration 2,411 observed. Recency minimum 31 days, median 365.25, maximum 25,567.5 approximate days. Missing history is often routing-related, not zero; Wave 2 skip errors and persistent-former non-reasking remain limitations.
- Descriptive plausibility flags: 13 intensity records above 100 cigarettes/day (maximum 400), four alcohol-quantity records above 30 drinks/drinking day (maximum 60). No negative observed numeric values; categories checked against mapped labels. Thresholds are review flags, not invented hard validity limits. Source 20-cigarettes-per-pack conversion retained. No raw/cohort value was guessed, capped or changed. Extreme and sparse histories remain research-only; later robust research transformations must respect training-fold boundaries.
- Baseline-characteristic follow-up availability compares observed vs unobserved tuning-ledger intervals. Selected canonical Waves 1–6 columns read in chunks and immediately filtered to tuning-ledger IDs before harmonization. TSV cannot push down an ID filter, so other earlier-wave rows are discarded unprocessed; no Wave 7/8 raw table parsed. Pooled valid follow-up: age 18–24 78.7%, age 55–64 88.5%; unknown-age n=2 is too small for substantive interpretation. Unknown recency group 85.9% vs recent-proxy 81.0%. Pooled/per-wave tables cover age, recorded sex, education, recency, physical/mental health and electronic use. These associations describe possible selection, not causes or bias correction; repeated intervals and wave mix matter. No national estimates or significance claims.
- Final **app profile = 11**: age_band, education_level, employment_status, last_cigarette_recency_days, electronic_nicotine_p30d, household_tobacco_any, home_combustible_smoking_rules, physical_health, mental_health, social_satisfaction, emotional_problems_7d.
- **Minimal = 4**: age_band, education_level, employment_status, last_cigarette_recency_days. **Research = 25** original candidates in a separate survey-only comparison. No importance ranking or feature-outcome association screening used. Research has actual baseline survey values and missingness only; no fabricated app histories.
- Initially considered a 12-input app including recorded sex/gender, then source review showed its historical first-interview carryover makes direct new-user substitution inappropriate. Removed it from app/minimal; it remains research-only. Other research-only fields include sparse histories, detailed product inventories, nominal-US income, diagnostic recency and conditional alcohol quantities. No trained-model performance or incremental utility claimed.
- App questions preserve early e-cigarette versus later electronic-product wording, changing household product scope, living-alone inapplicability and Wave 1 quit wording. Recency units: Wave 2 Days/Months only, others Days/Months/Years; documented quantity-entry widths retained (Waves 2–4 two digits for days/months; Waves 5–7 two digits for all listed units; no finite Wave 1 bound invented). Positive whole quantities convert using 30.4375/365.25. Answers contradicting no-past-30-day-use eligibility are rejected for clarification, never altered.
- All optional inputs default null; unanswered, don't know, refusal, not applicable and not previously asked preserve distinct reasons. Household No is valid zero; living alone is not automatically No. No UI imputation value or historical reconstruction. Four eligibility gates (adult, ≥100 lifetime cigarettes, current not-at-all, no cigarette even puffs past 30 days) are required before a later prediction and approximate the official derived cohort. No model/probability validation yet; form completion does not establish applicability under routing/distribution shift.

### Enduring files

- `configs/development_exploration.json`: scope, profile lists, attrition features, fixed bins and numerical review flags.
- `src/path_project/development.py`, `scripts/explore_development.py`: tuning-only loaders, filters, source hashing, aggregate distributions/availability and six Matplotlib figures. No fitting.
- `reports/development_data_summary.md`: requested readable report, actual counts/figures, availability/attrition interpretation and decisions. Aggregate JSON plus six PNGs in `reports/development_v1/`: interval_prevalence, missingness, numeric_distributions, categorical_distributions, followup_by_baseline, summary and access_audit.
- `configs/feature_mapping_final.json`, `docs/feature_dictionary_final.csv`, `configs/prediction_specification_final.json`: explicit versioned final-profile supplements referencing immutable base hashes. All original source columns/labels/units/skip rules/evidence retained across 288 field/wave dictionary rows. Original locked mapping, dictionary and JSON prediction specification untouched. Updated human-readable mapping/specification docs to point to final supplements.
- `configs/app_questions.json` and `docs/app_questions.md`: exact eligibility gates, all optional app questions/options, wave-specific wording/units, physical local PDF page references and missing-answer behavior. No actual Streamlit app implemented yet.
- `src/path_project/final_inputs.py`: final-profile/source/dictionary consistency checks, deterministic answer encoding and future `fit_profile_pipeline` wrapper delegating explicitly named subsets to the existing locked tuning-only fitter. No real fit called in stage 6.
- `scripts/finalize_inputs.py`, `scripts/write_development_summary.py`, `scripts/verify_development.py`: reproducible metadata/report generation and read-only aggregate reconciliation/privacy checks. README and `.gitignore` updated; only final dictionary metadata CSV is allowlisted, all real data/split/model outputs remain ignored.
- `tests/test_development.py`: 11 synthetic/metadata tests added. Check tuning-only scope, future exclusion, loader predicates before feature access, null vs zero/missing reasons, duration units/entry widths and conflicts, per-wave semantic wording, preserved source mappings/profiles and future fitting delegation (mocked, no real training).

### Exact commands and actual verification

- `.venv/bin/python scripts/explore_development.py`: exit 0; tuning counts above, aggregate files and six figures produced. Ran again after figure-label clarification and for deterministic verification; no model evaluation to invalidate by repetition. Visually inspected feature-distribution PNG for readability.
- `.venv/bin/python scripts/finalize_inputs.py`: exit 0; app=11, minimal=4, research=25, no cohort/split changes. Refined source wording for mental health and retained documented recency entry widths before final verification.
- `.venv/bin/python scripts/write_development_summary.py`: exit 0, wrote `reports/development_data_summary.md` from aggregates only.
- `.venv/bin/python scripts/verify_development.py`: exit 0; 13,757 labeled / 16,338 eligible interval totals, prevalence/missingness/recency/repeat counts, attrition denominators, source-preserving profiles, six images and report identifier-token checks passed.
- `.venv/bin/python -m pytest -q -p no:cacheprovider`: final full run exit 0, **66 passed in 4.07s** (prior run 66 in 4.02s). Synthetic/metadata tests only for stage 6; earlier synthetic fitting tests run on invented records, not PATH.
- `.venv/bin/python /tmp/check_stage6_reproducibility.py`: exit 0; reruns explore/finalize/write/verify through the selected interpreter. **19/19 outputs byte-identical**, **24/24 prior cohort/split/base metadata files unchanged in SHA-256 and mtime**. Saved evidence/code/config/output hashes/versions in `reports/development_reproducibility_v1.json`. Actual versions: pandas 3.1.1, numpy 2.5.4, matplotlib 3.11.2, pyarrow 26.0.1, scikit-learn 1.9.1. Temporary helper is not required for normal project commands.
- `.venv/bin/python scripts/verify_evaluation_splits.py`: exit 0; 30,890 saved keys and the unchanged participant/temporal lock verified; test still unopened for development.
- `.venv/bin/python scripts/verify_cohort.py`: exit 0; immutable previous cohort/ledger labels, keys, availability and provenance/privacy checks passed.
- `.venv/bin/python scripts/verify_inputs.py`: exit 0, **59/59 originals unchanged**, including datasets, proposal, implementation analysis and original scripts. Original baseline not regenerated.

### Stop point and next stage

Stage 6 complete; await the next numbered prompt. No cohort regeneration is required because no cohort predicate, target, source mapping or recoding changed. Participant assignment and earlier outputs remain intact. Future model development must explicitly select app/minimal/research profile, fit preprocessing inside tuning training folds, preserve calibration/threshold roles and keep the test closed. App self-report equivalence and routing-related missingness require later validation; neither final profiles nor questionnaire completion establish calibrated personal risk. No real model training, calibration, threshold selection, final evaluation, publication, upload, deployment, Git operation or external messaging occurred. No user action needed.

### Stage 6 continuation — existing outputs verified and retained

The repeated stage 6 implementation request was satisfied by continuing the existing completed work. No later stage ran and no unnecessary regeneration was performed. Current saved evidence verified all eight stage-6 source/config hashes and all 19 generated-output hashes with zero changes (`reports/development_reproducibility_v1.json`). Exact verification commands used the workspace interpreter with `PYTHONDONTWRITEBYTECODE=1`:

- `.venv/bin/python scripts/verify_development.py`: exit 0; tuning-only 13,757 labeled / 16,338 eligible intervals, six figures, final profiles/source metadata and report privacy passed.
- `.venv/bin/python scripts/verify_evaluation_splits.py`: exit 0; saved membership and temporal separation unchanged; final-test features/outcomes unopened.
- `.venv/bin/python -m pytest -q -p no:cacheprovider`: exit 0, **66 passed in 4.12s**.
- `.venv/bin/python scripts/verify_inputs.py`: exit 0, **59/59 original files unchanged**.

Final deliverables remain `reports/development_data_summary.md`, `docs/app_questions.md`, `configs/app_questions.json`, the three versioned final mapping/dictionary/specification files and aggregate tables/figures. App/minimal/research profiles remain 11/4/25 inputs. No cohort predicate or recoding change; no cohort rebuild, held-out reassignment, fitting, calibration, threshold selection or final evaluation. Stage 6 remains complete; await the next numbered prompt.

## Stage 7 — in progress

Authorized baseline model training only under the locked development protocol. No new AGENTS.md found. Re-read plan baseline/calibration/leakage sections and immutable stage 5 boundary code. Prespecified five candidates before fitting in `configs/baseline_models.json`: training-prevalence-only, minimal logistic (4 inputs) and full selected app logistic (11 inputs), each logistic unweighted/balanced. C=1 fixed, no broad hyperparameter search. Research-only 25 inputs remain a separate future comparison, not an app fallback. Will select by mean participant-weighted five-fold AP with fixed simplicity tie-break, fit the selected sigmoid calibrator only on reserved calibration people, and choose threshold on reserved threshold people per locked rules. No final-test accessor or evaluation. All preprocessing learned inside training Pipeline fits; save local ignored models/predictions and aggregate metrics/provenance with immutable retries.


## Stage 7 — completed executed baseline training

### Implementation and scope

- No new applicable AGENTS.md found in workspace/ancestors. Re-read original plan baseline/class-weight/calibration/leakage sections and locked evaluation/training-boundary code. Existing `.venv/bin/python` selected; inspected actual installed sklearn signatures before using APIs. No install, external service, publication, Git operation or deployment.
- `configs/baseline_models.json`: fixed seed 366, one CPU thread, five candidates in simplicity order: training_prevalence; minimal_logistic; minimal_logistic_balanced; app_logistic; app_logistic_balanced. Minimal uses four stage-6 inputs; full selected uses all eleven app inputs. The separate 25-field research-only profile is not trained in this baseline stage and is never an app fallback. Logistic C=1, lbfgs, max_iter=2000, tol=1e-4 fixed before fitting; no broad hyperparameter search.
- `src/path_project/baselines.py`: reusable feature-schema transformer and complete sklearn Pipelines, metrics/reliability tables, sigmoid calibration and frozen calibrated bundle, and immutable training/provenance. Missing categorical values use a distinct -1 missing category; OneHotEncoder ignores unseen documented categories. Numeric recency uses training-only median plus missing indicator and standard scaling; empty numeric columns keep an internal zero constant plus missing indicator, never changing a raw/app answer. Original skip/no-answer reasons remain separate in processed data but are not automatically model predictors. Schema rejects extra IDs/outcomes, missing columns, invalid category codes, nonfinite and negative quantities, and normalizes column order.
- Each base fit delegates to the existing exact authorized-key training boundary and clones the entire Pipeline. All learned preprocessing is inside the fold fit. Participants/future periods are excluded using the unchanged stage 5 development loader; final profiles are validated against the source-fingerprinted mapping. No test accessor or final-test label/feature projection exists in the new module.
- `scripts/train_baselines.py`: create new exclusive run, or verify and reuse a matching completed run; refuses changed/incomplete runs instead of overwriting/retraining. Configured CPU thread environment is set before sklearn/numpy imports.
- `tests/test_baselines.py`: 16 synthetic-only tests added; total 82. Covers training-prevalence vs evaluation prevalence, fold-only imputation/scaling, unseen valid categories, feature-name preservation, schema rejection, reload/column-order consistency, AP distinct from trapezoidal PR area, weighted constant-score AP, threshold rule, frozen-base calibration, calibration-bin accounting and empty numeric columns. No real PATH data in synthetic fixtures. Initial threshold-test failure was a one-ulp floating-point F1 difference (0.7499999999999999 vs 0.75); retained exact threshold equality and used approximate numeric F1 comparison. Production threshold rule was not weakened or changed.

### Actual development results

- Executed **25 grouped fold fits** (five candidates × five locked tuning folds), then **five full-tuning refits**. All converged under the fixed iteration limit; ConvergenceWarning would stop the run. Saved trained objects and actual predictions, not placeholders. No evaluation records were balanced, resampled or dropped.
- Primary PR metric is **sklearn average_precision_score**, stepwise precision weighted by recall increments, not trapezoidal PR-AUC. Selection uses mean five-fold participant-equal AP; each participant has total evaluation weight one (1/n interval records). Ordinary interval metrics are also saved. Fold SD is descriptive, not an independent-sample uncertainty interval; no cluster bootstrap/CI run in stage 7.
- Mean-fold participant AP / ROC-AUC / Brier:
  - training_prevalence: **0.208326 / 0.500000 / 0.175000**.
  - minimal_logistic: **0.432941 / 0.775885 / 0.144294**.
  - minimal_logistic_balanced: **0.427501 / 0.774059 / 0.220603**.
  - app_logistic: **0.425128 / 0.776269 / 0.144591**.
  - app_logistic_balanced: **0.419429 / 0.773936 / 0.220478**.
- Mean fold participant-equal evaluation prevalence **0.208326**, while pooled tuning interval prevalence is **0.108090**. Different repeated-record weighting targets explain the context; do not interchange them or present weighted confusion numbers as integer event counts. The prevalence-only estimator is unweighted DummyClassifier(strategy=prior): each fold predicts only its empirical **training interval prevalence**, checked against training labels. Its AP equals weighted evaluation prevalence because its score is constant within that fold, not because it reads evaluation labels. Pooled OOF baseline scores vary slightly across folds; per-fold baseline AP/ROC are the proper selection context.
- Selected **minimal_logistic** by the prespecified mean AP rule, before calibration/threshold data were used. Its four-feature subset is app-compatible; the full eleven-question profile remains a separate trained comparison. Balanced variants raise raw mean probabilities (~0.47 participant-weighted) and worsen Brier in this run; no claim that weights always help. No statistical significance or final performance claim is made for small AP differences.
- Frozen selected base model refit only on 13,757 tuning records / 4,692 people. **Sigmoid calibration** fits logit(raw probability), clipped at 1e-6, on reserved **2,801 records / 947 people**, with participant-equal fitting weights and no base-model/preprocessing refit. No example/person used for that base estimator's fitting trains the calibrator. Calibration-fit metrics are explicitly apparent for the calibrator.
- Separate **2,910 threshold records / 990 people** are held out from base and sigmoid fitting. Their participant-equal raw→calibrated Brier is **0.148806→0.143946**, log loss **0.466987→0.449197**, mean predicted probability **0.149330→0.202382**, observed weighted prevalence **0.215101**. AP remains **0.449289**, ROC-AUC **0.767734**. These are held-out development probability diagnostics, not final-test results and not grounds for choosing another model.
- Threshold selected by locked participant-weighted F1 rule (largest threshold on ties): **0.16677679805083043**. Apparent threshold-selection-group F1 **0.521416**, precision **0.392851**, sensitivity **0.775065**, specificity **0.671729**. Clearly labeled apparent because the same group chooses the threshold. Fixed 0.5 fold diagnostics and confusion matrices for both weightings are saved. No low/medium/high risk category, personal confidence percentage, clinical guarantee or fixed-year risk is established.

### Outputs and exact successful commands

- `.venv/bin/python scripts/train_baselines.py`: exit 0, `trained_new_immutable_run`; all 25 fold logs emitted actual AP/Brier; selected minimal_logistic. Signature: `df836e506ac5336e4c50c9a4567ca66a14e69c13af6caa687d8f2b0a4c440aea`.
- Ignored `artifacts/baselines_v1/`: 25 fold Pipelines in `folds/`, five tuning-refit Pipelines in `models/`, `selected_calibrated.joblib`, detailed `pipeline_metadata.json` including transformed feature names/coefficients/medians, `oof_predictions.parquet`, `calibration_predictions.parquet`, `threshold_predictions.parquet`, immutable `manifest.json`. Participant-level predictions and learned parameters remain ignored. PERSONID is only an internal key/group field, never a predictor.
- Public `reports/baselines_v1/results.json`, `fold_metrics.json`, structural `pipeline_metadata.json` and `provenance.json`: aggregate metrics, fixed-0.5 diagnostics, calibration bins and actual versions/config/code/split hashes. Detailed learned coefficients remain in ignored artifact metadata, not public structural metadata.
- `.venv/bin/python scripts/verify_baselines.py`: exit 0; loads existing artifacts, verifies hashes and all 25 fold predictions against saved OOF probabilities; independently recomputes metrics, checks empirical training prevalence and training-only imputation medians, feature names, selected-model rule, calibrated bundle reload and threshold selection, and participant separation. No refits or final-test data access.
- `.venv/bin/python scripts/write_baseline_report.py`: exit 0; aggregate-only `reports/baseline_results.md` and `reports/baseline_calibration.png`. Visually inspected figure for readability. Report distinguishes average precision from trapezoidal area, participant vs interval/class/survey weights, apparent calibration/threshold metrics and final-test unknowns.
- `.venv/bin/python -m pytest -q -p no:cacheprovider`: exit 0, **82 passed in 4.68s** (pre-training run 82 in 4.70s). New tests fit only synthetic models; no reserved evaluation repeated.
- `.venv/bin/python scripts/verify_evaluation_splits.py`: exit 0, unchanged 30,890-key membership and participant/temporal separation; final test closed.
- `.venv/bin/python scripts/verify_inputs.py`: exit 0, **59/59 original files unchanged**; baseline hash manifest not rewritten.

### Remaining limits and next step

Stage 7 complete. Await the next numbered stage. Earlier no-model statements in historical status entries describe those earlier stages. Baseline models and development-calibrated bundle now exist locally; there is still no final-test performance or completed Streamlit demonstration. Do not choose a future classifier using reserved calibration/threshold results; later authorized comparisons must use tuning CV only. Keep this run, source profiles, cohort, participant assignments and final test intact. Probabilities may shift across waves/new-user routing, class weighting and repeated-record metric targets; calibration has not validated future-user clinical risk. No uncertainty interval, cause, exact relapse time, national inference or result guarantee is fabricated. No user action is required.

### Stage 7 final preservation/retry evidence

- `.venv/bin/python /tmp/check_stage7_preservation.py`: exit 0. The pre-training snapshot confirms **21/21 prior cohort/split files unchanged** in SHA-256 and modification time. A retry of `.venv/bin/python scripts/train_baselines.py` returned `reused_verified_run`; **40/40 baseline artifact/aggregate files retained hashes and mtimes**, with no refit or calibration/threshold reselection. Readable report/figure regeneration was byte-identical. Public report identifier-token checks passed. Saved evidence and verification-source hashes: `reports/baseline_verification_v1.json`.
- Core baseline signature and all artifact/report hashes still verify. README, evaluation-protocol execution note and this continuation status explain the current trained-baseline state and the still-closed final test. No earlier split/cohort or source mapping was regenerated.

## Stage 8 — in progress

Authorized tree-vs-baseline comparison only. No new AGENTS.md found; re-read plan baseline/weighting/leakage sections and locked protocol. Local interpreter `.venv/bin/python`; installed XGBoost **3.4.1** imports successfully with sklearn **1.9.1**, so no installation/network needed. Search frozen before new fits in `configs/tree_models.json`: two paired complexity settings × two training-only weight options × minimal/app profiles × RF/XGBoost = 16 candidates, 80 grouped fold fits, one CPU thread, seed 366, no adaptive expansion or early stopping. Existing five baseline candidates will be reused on identical folds, never retrained for timing. Preserve locked AP-primary/simplicity selection; explicitly report Brier/log loss/calibration tradeoffs and require reserved sigmoid calibration for a newly selected tree. No resampling experiment justified beyond weights given adequate training positives; no held-out features/outcomes, calibration/threshold scores or final test may select the classifier. Existing cohort, split and baseline artifacts remain unchanged.


## Stage 8 — completed tree comparison and model selection

### Scope and fixed search

- No new AGENTS.md found in workspace/ancestors. Re-read plan baseline/class-weight/leakage sections and locked protocol. Existing `.venv/bin/python` used. Actual imports: XGBoost **3.4.1**, sklearn **1.9.1**, numpy **2.5.4**, joblib **1.6.0**. XGBoost actually ran on CPU; no installation, network, services or keys required. HistGradientBoosting fallback exists and was tested only on synthetic data; it was not substituted for real XGBoost.
- `configs/tree_models.json` froze 16 new candidates before fitting: two paired complexity settings × minimal/app profiles × no/balanced weights × RandomForest/XGBoost. Seed 366, one CPU thread. Search is intentionally modest, not a Cartesian exhaustive sweep or adaptive expansion. No early stopping or validation-fitted transforms.
- RF settings: 150 trees, sqrt feature sampling, native training-only bootstrap; (depth4, min_leaf20) or (depth8, min_leaf10); class_weight None/balanced. XGB: hist CPU, lambda5, row/column sample1; (120 trees, depth2, lr0.05, min_child_weight10) or (180 trees, depth3, lr0.05, min_child_weight10); scale_pos_weight1 or training-fold negative/positive ratio.
- Reused the five saved stage 7 baselines on the exact same validation keys/labels; did not retrain them or invent missing baseline runtimes. All 80 new fits use cloned fold-only Pipelines via the existing authorized-key guard. Minimal four and full selected eleven inputs match stage 6; no research-only 25-field app fallback, no new features/cohort changes, no held-out participants or future Wave 7→8 outcomes.
- No targeted resampling experiment added: folds have adequate positive cases; class-weight comparisons are sufficient for this modest course experiment and raw probability distortion is visible. RF bootstrap is intrinsic bagging within training, not class balancing. Evaluation membership/prevalence unchanged.
- Selection preserves the locked mean-fold participant-weighted AP criterion with deterministic existing simplicity order on exact ties. Bounded finite probabilities and finite Brier/log loss are checked; raw probability quality, calibration curves and ROC are mandatory tradeoff diagnostics. Probability quality determines calibration/readiness cautions rather than a hidden post-hoc composite ranking. Calibration/threshold groups never choose a classifier, hyperparameter or feature set; final test unopened.

### Executed results and tradeoffs

- **80 grouped tree fold fits** executed successfully, plus **four best-family/profile full-tuning refits**. All searched fold Pipelines saved. Measured tree workflow elapsed **29.963142 seconds** including loading, prediction, model serialization, refits and reserved calibration; individual fit/predict times saved. Timing is local hardware/load dependent; stage 7 baseline timing is explicitly unavailable.
- Selected **xgb_minimal_s1_none**: unweighted XGBoost, 180 trees, depth3, lr0.05, min_child_weight10, reg_lambda5; minimal features age_band, education_level, employment_status, last_cigarette_recency_days. Mean five-fold participant AP **0.453882**, ROC-AUC **0.784236**, Brier **0.141601**. Minimal logistic baseline: AP **0.432941**, ROC **0.775885**, Brier **0.144294**. Constant baseline AP **0.208326** in the participant-equal metric context (ordinary tuning interval prevalence **0.108090**). AP is sklearn average_precision_score, not trapezoidal PR-AUC.
- Best RF minimal: **rf_minimal_s0_none**, AP **0.451465**, ROC **0.779671**, Brier **0.147666**. Best RF full: **rf_app_s0_none**, AP **0.446532**, ROC **0.782045**, Brier **0.151202**. Best XGB full: **xgb_app_s1_none**, AP **0.452306**, ROC **0.788092**, Brier **0.141388**. Full XGB has slightly better raw Brier/ROC than the selected minimal variant but lower AP; the locked rule and lower question burden favor the AP winner. No statistical significance or universal superiority claim; CV fold SD is descriptive, not a CI. All 21 baseline/tree candidates are reported.
- Balanced tree variants mostly have raw Brier ~0.206–0.215 and high mean probabilities, illustrating class-weight probability distortion. No score target promised. All ranking/probability tradeoffs are explicit in `docs/model_selection.md`, including full-versus-minimal and unweighted-versus-balanced comparisons.
- Only after selecting by tuning CV, fit the new selected-tree sigmoid on **2,801 reserved calibration records / 947 people**, using the unchanged fixed logit/clip method and participant-equal weights. Base model trained only on **13,757 tuning records / 4,692 people**. New calibration examples were never used to fit this base estimator. Earlier stage 7 reserved diagnostics were not used to select this classifier, and reserved results did not trigger another search.
- Separate threshold group **2,910 records / 990 people**: participant-equal raw→calibrated Brier **0.146165→0.140948**, log loss **0.451763→0.434680**, mean predicted probability **0.150333→0.201870**, weighted prevalence **0.215101**. AP **0.445382**, ROC **0.782405**. Reserved AP is slightly below the earlier baseline's **0.449289**, and is reported rather than used to reverse selection.
- Chosen calibrated threshold **0.2590049599706509** (locked weighted-F1/largest-tie rule). Apparent threshold-selection F1 **0.534737**, precision **0.439061**, sensitivity **0.683729**, specificity **0.760612**. These are selection-set metrics, not independent threshold performance. Calibration-fit metrics are explicitly apparent; final-test calibration/performance remains unknown. No risk categories, personal confidence, causal effects, fixed-year timing, clinical utility or national inference established.

### Files and actual commands

- `src/path_project/trees.py`: tree factories/fixed candidate generation, training-only weight ratios, dependency fallback, immutable run signatures, fold checks, saved-baseline alignment, aggregate comparison and selected-only reserved calibration. `scripts/train_tree_models.py`: CPU-thread setup then create or verified reuse, no final-test accessor.
- `artifacts/trees_v1/` ignored: **80 fold Pipelines**, **four tuning-refit Pipelines**, `selected_calibrated.joblib`, `oof_predictions.parquet`, `calibration_predictions.parquet`, `threshold_predictions.parquet`, immutable `manifest.json`. Fitted node parameters and individual predictions/IDs remain ignored. Public `reports/trees_v1/results.json`, `fold_metrics.json`, `provenance.json` include aggregate metrics, fixed search configurations, actual runtimes, versions and baseline/split/code hashes.
- `scripts/write_model_selection.py` produced required **docs/model_selection.md** and `reports/tree_comparison_calibration.png` from saved aggregates only. Visually inspected calibration figure for readability. README/evaluation-protocol execution note updated; old source mappings, cohort and split configuration unchanged.
- `tests/test_trees.py`: nine synthetic tests added (search pairing/budget, RF/XGB/fallback schema/serialization/unseen categories, training-only weight ratios, finite probability checks, exact AP/simplicity rule and one-class training rejection). Optional XGB tests skip only when genuinely unavailable; actual local run had no skips. No real PATH or reserved-test models fitted in tests.
- `.venv/bin/python -m pytest tests/test_trees.py -q -p no:cacheprovider`: exit 0, **9 passed in 1.14s**. `.venv/bin/python -m pytest -q -p no:cacheprovider`: final exit 0, **91 passed in 4.97s** (pre-training 91 in 4.94s).
- `.venv/bin/python scripts/train_tree_models.py`: exit 0, `trained_new_immutable_run`, emitted actual fold AP/Brier and measured times, selected xgb_minimal_s1_none.
- `.venv/bin/python scripts/verify_tree_models.py`: exit 0; all **80 saved fold Pipeline** predictions and OOF labels/metrics reconcile, medians and class ratios match training folds, AP selection/bundle/threshold and participant separation verified. Existing saved development predictions scored only; no refits or final-test access.
- `.venv/bin/python scripts/write_model_selection.py`: exit 0; required document and readable calibration plot generated.
- `.venv/bin/python /tmp/check_stage8_preservation.py`: exit 0; **61/61 previous cohort/split/baseline files unchanged** in SHA-256 and mtime. Retry of `.venv/bin/python scripts/train_tree_models.py` returned `reused_verified_run`, preserving **92/92 tree artifact/aggregate files** without refitting, calibration reselection or overwrites. Selection document/figure regeneration byte-identical; public report identifier-token check passed. Evidence and verifier/test source hashes: `reports/tree_verification_v1.json`. Temporary helper is not required for routine use.
- `.venv/bin/python scripts/verify_evaluation_splits.py`: exit 0; unchanged 30,890-key membership, held-out/temporal restrictions and five participant-disjoint folds verified; final test closed.
- `.venv/bin/python scripts/verify_inputs.py`: exit 0, **59/59 original files unchanged**. Original input manifest not regenerated.

### Stop point

Stage 8 complete. Await the next numbered prompt; do not perform final evaluation or build/deploy an app automatically. Selected calibrated tree artifact is `artifacts/trees_v1/selected_calibrated.joblib` and its actual required features are the minimal four, a subset of the eleven-question app profile. Reserved groups may not be used for further tuning/selection. Preserve all original data, prior fitted baselines, cohort and participant assignments on retries. Source-question routing, sparse recency, repeated-record metric targets, attrition and unknown follow-up intervals remain limitations; later-wave and new-user probability validity is not established. No external messages, commits, pushes, uploads or services. No user action required.

## Stage 9 — in progress

Authorized timing decision only. No applicable AGENTS.md found. Read `docs/timing_feasibility.md`, implemented cohort schema/specification and original plan's timing caveats. Decision C is still indicated: no usable individual elapsed clock; raw quit recency is historical, and AN0135 is a conditional approximate last-attempt date rather than a complete first-cigarette-resumption endpoint. Rechecked local Wave 1 questionnaire physical p.24 (INTVDATE programming) and codebook pp.692–693 (AN0135/current-user eligibility) directly with page-restricted pdftotext. Will confirm all eight actual TSV headers, documentation hashes and Parquet schema without reading participant rows; preserve the classifier/splits and add separate app capability metadata (do not edit fingerprinted stage 6/7/8 inputs). No survival fitting, annual probabilities, relapse dates or final-test access.


## Stage 9 — completed supported omission of timing

### Decision, scope and scientific basis

- **Decision C confirmed.** No defensible elapsed-time endpoint/clock exists for the implemented cohort in the supplied local files. Retain next-survey classification; no survival model or curve, annual probabilities, relapse dates, midpoint events or calendar-time extrapolation created. This stage is complete through the prompt's explicitly allowed unsupported-timing branch, not because a survival tool can draw a curve.
- Read `docs/timing_feasibility.md`, cohort schema, original/final prediction specifications, source evidence, input inventory and original implementation-plan timing caveats. No applicable AGENTS.md found in workspace/ancestors. Existing isolated `.venv/bin/python` and local pdftotext work; no dependency installation, internet, service or permission needed.
- All eight actual canonical adult TSV headers freshly checked; no matching usable interview-date/elapsed-clock candidate. Raw AC1009 number/unit history and conditional AN0135/AN0135_VALUE_INFO fields are present across all waves. All current PATH files are registered in the original input inventory: zero new/unreviewed files that could contain additional timing/linkage data. Original codebook/questionnaire hashes still match both the original manifest and saved all-wave source review. Search conclusions remain scoped to these files and documented constructs.
- Actual Parquet **schemas only** checked against saved schema for cohort and ledger: starting/follow-up wave indices and status labels, no elapsed interview interval, event date/time or censoring time. Historical quit recency/regular-smoking months are not prospective clocks. No survey/cohort answer rows or final-test features/outcomes read. The retained-model integrity checker does verify internal split membership keys, so evidence explicitly distinguishes key verification from answer-row reading.
- Four live source rechecks with page-restricted pdftotext: Wave 1 questionnaire physical p.24 (INTVDATE programming, absent from headers); Wave 1 codebook pp.692–693 (AN0135 approximate last-attempt date/current-user and product routing); Wave 8 codebook pp.1389–1390 (approximate last-attempt date); Wave 8 nonresponse report pp.18–19 (general collection windows/Table 2.1). The instrument's internal date and general study windows are not released individual clocks.
- AN0135 dates are not denied or silently ignored: conditional approximate **last** quit-attempt ends can concern another tobacco product or a later episode and do not establish cigarette-specific **first** post-baseline resumption for all former-smoker entrants. AC1009 is since prior quitting/last cigarette, not future time until resumption. Twelve-month retrospective use can precede baseline or miss early episodes in a longer gap; it is not identical to any use in the individual survey interval.
- A negative next 30-day window does not establish event-free follow-up; brief resume/quit cycles may be missed. Missing follow-up remains unobserved, not negative or a fabricated censoring time; no missing wave is bridged. Actual first resumption, first observed positive status and persistent relapse are different targets. A first positive wave index would be detection order in a separately designed study, not elapsed time; it is not modeled here. No unsupported absorbing-state/persistence, full-event-capture or independent-censoring assumption is adopted. Even interval-censored methods would need defensible event-free bounds; a generic right-censored model cannot supply them. Verified competing-event/time data would also be needed for a future analysis.

### Files and app contract

- `docs/timing_decision.md`: requested clear decision, all supporting distinctions, exact local source pages, implemented-cohort confirmation, censoring/attrition assessment, why A/B are not enabled, conditions for future reconsideration and explicit preservation of classifier scope.
- `configs/timing_decision.json`: fixed decision C, unsupported reasons, fresh header/title searches, selected-model reference, exact source rechecks and disabled capabilities. No original fingerprinted specification/mapping/question file edited.
- `src/path_project/timing.py`: header/documentation/schema confirmation and app capability/output guard, no fitting/scoring methods. Raises on new local PATH inputs or potential clock fields/titles requiring review; it does not silently assume they remain absent. Reads physical schemas without participant answer rows and verifies retained classifier artifact hash.
- `configs/app_metadata.json`: additive app contract, pinned selected classifier path/hash and four actual feature names, development-only probability-validation status; `elapsed_time_estimates_available`, `survival_model_available`, `fixed_horizon_probabilities_available`, `estimated_relapse_date_available` are false; `supported_elapsed_time_horizons` is empty. Contains no numeric annual placeholders or individual relapse date. Next-survey output guard rejects elapsed horizons/date requests rather than manufacturing probabilities. Historical recency is explicitly a baseline predictor only.
- `scripts/confirm_timing.py`: deterministic confirmation/evidence and capability metadata generator; `scripts/verify_timing.py`: read-only current-source/evidence/metadata/guard verification. `reports/timing_confirmation_v1.json`: eight header checks, sixteen documentation hashes, local inventory, two schema checks, four live source checks and unchanged classifier hash. `reports/timing_verification_v1.json`: preservation/reproducibility/source hashes and actual Python/pyarrow/pdftotext versions.
- `tests/test_timing.py`: 15 synthetic-policy/metadata tests for C consistency, empty horizons, disabled capabilities, rejection of zero/one/two/three-year/other elapsed horizons and relapse dates, correct next-survey wording, no placeholder payload and source/schema confirmation. No real timing model or final-test prediction used. Full suite's earlier model tests fit only fictional fixtures.
- README and `app/README.md` now point future Streamlit work to the timing-disabled capability contract and `path_project.timing.next_survey_output_metadata`. No app UI, deployment, model rewrite, new classifier target or source-cohort regeneration performed.

### Exact actual checks and preservation

- Direct reads: `pdftotext -f 24 -l 24 -layout PATH/DS1001/36498-1001-Questionnaire.pdf -` and `pdftotext -f 692 -l 693 -layout PATH/DS1001/36498-1001-Codebook.pdf -`, followed by script-driven all-source checks below. Only documentation and raw headers, never survey answer values.
- `.venv/bin/python scripts/confirm_timing.py`: exit 0, **eight actual headers, 16 source documentation hashes, two actual Parquet schemas, four live page-range source rechecks** passed; classifier unchanged; no answer rows, timing fits or model scoring. Repeated after source-confirmation code refinement to save current source fingerprints; no performance evaluation involved.
- `.venv/bin/python scripts/verify_timing.py`: exit 0; fresh confirmation equals saved evidence, metadata matches C, classifier artifact hash unchanged, elapsed horizons/date requests rejected. Does not write project files or refit models.
- `.venv/bin/python -m pytest tests/test_timing.py -q -p no:cacheprovider`: exit 0, **15 passed in 0.81s**.
- `.venv/bin/python -m pytest -q -p no:cacheprovider`: final exit 0, **106 passed in 4.95s** (earlier 106 in 4.92s). No real model training or reserved final evaluation in tests.
- `.venv/bin/python /tmp/verify_stage9_preservation.py`: exit 0. Repeated confirm/verify checks and metadata generation are deterministic; **153/153 existing cohort/split/baseline/tree artifact/report files unchanged in SHA-256 and mtime**. Metadata/evidence retry byte-identical, no refit or test-answer access. Saved proof: `reports/timing_verification_v1.json`. Temporary helper is not required for routine project commands.
- `.venv/bin/python scripts/verify_evaluation_splits.py`: exit 0; unchanged 30,890 labeled keys and participant/temporal lock; final-test feature/outcome access remains closed.
- `.venv/bin/python scripts/verify_inputs.py`: exit 0, **59/59 original files unchanged**. Original dataset/proposal/analysis/scripts and baseline manifest preserved; no Git operations.

### Next step / stop point

Stage 9 complete by verified decision C. No user action needed. Await the next numbered prompt. The working classifier remains `artifacts/trees_v1/selected_calibrated.joblib`; no model parameters, sigmoid, threshold, feature profile, cohort or held-out assignment changed. Do not create elapsed-time outputs or a survival extension without separately authorized data, an appropriately observed endpoint and a new protocol/method supporting its censoring/observation structure. Do not open final-test data, build/deploy the app, upload/publish or proceed to any later stage automatically. This omission protects the core project rather than compromising it to fulfill the proposal's unsupported timing subtitle.

## Stage 10 — in progress

Authorized output interpretation, development-defined risk categories and explanations only; no final-test access or model refitting. No applicable AGENTS.md found. Read proposal-plan SHAP guidance, selected calibrated-wrapper implementation, app question encoders and timing-disabled metadata. SHAP **0.54.1** imports with existing XGBoost **3.4.1**. Initial import fell back from a read-only home Matplotlib cache to /tmp; enduring scripts will set workspace MPLCONFIGDIR before importing SHAP. No install/network needed.

Before inspecting category outcomes, fixed `configs/output_explanations.json`: participant-weighted score tertiles from the reserved threshold-selection group, inclusive boundary/tie rule, minimum group size, no outcome-optimized cuts. For exact probability-scale explanations, use SHAP ExactExplainer on the actual calibrated wrapper over its four original inputs, with deterministic 64-person tuning background and 128-person tuning global sample. This avoids presenting raw-tree log-odds as calibrated probability contributions. Will map fitted one-hot/numeric/missing-indicator columns back to four readable questions, freeze artifact identity, test complete/partial/missing/eligibility profiles, suppress unsupported timing and low-completeness outputs, and preserve all model/split files.


## Stage 10 — completed understandable output contract

### Decisions and frozen score categories

- No applicable AGENTS.md found in workspace/ancestors. Read original plan's SHAP guidance, actual selected-wrapper code, app question encoder and timing metadata. Existing SHAP **0.54.1** and XGBoost **3.4.1** work locally. Initial exploratory SHAP import reported a read-only home Matplotlib cache and successfully fell back to /tmp; enduring scripts/functions now use workspace `.cache/matplotlib`. No dependency installation or network/service access.
- `configs/output_explanations.json` fixed score-band rule before category outcomes were inspected: first observed calibrated score reaching cumulative **participant-equal** weight 1/3 and 2/3, ties together, lower p≤cut1, moderate cut1<p≤cut2, higher p>cut2. Cuts use scores and weights only, no outcome optimization. The source is the already-reserved threshold-selection group, not calibration/tuning/final-test data used to reselect a classifier. Project-defined relative strata, not medical cutoffs or independently validated categories. A 100-record minimum per band is a descriptive feasibility guard, not a clinical validity threshold.
- Frozen `configs/risk_categories_v1.json` cuts: **0.0750747765280418** and **0.2590049599706509**. Category calculation uses full-precision score before rounding. Upper cut happens to equal the prior F1 binary threshold, independently obtained here by the quantile rule; category includes equality in moderate, while the separate binary rule uses ≥. No classifier binary threshold or calibrator changed.
- Named source cohort: **reserved threshold-selection people with eligible starting Waves 1–6 and valid observed next-survey outcomes**, 2,910 interval records / 990 people / 336 positive intervals. Interval prevalence 336/2910 = **0.1154639175**; participant-equal prevalence **0.2151010101** with total weight 990. These are different observed-data estimands, not population risks.
- Lower: **1,411 intervals**, 443 distinct people appearing, **36 positives**, interval rate **2.5514%**, participant weight mass **353.316667**, weighted observed fraction **4.5332%**. Moderate: **886 intervals**, 471 people, **95 positives**, interval rate **10.7223%**, weight mass **306.733333**, weighted observed fraction **17.1702%**. Higher: **613 intervals**, 455 people, **205 positives**, interval rate **33.4421%**, weight mass **329.95**, weighted observed fraction **43.7238%**. Unique-person counts overlap across bands because intervals can change category; do not sum them as the cohort denominator. Weighted group fractions use fixed whole-source 1/n weights and listed weight mass, not per-group unique people. Descriptions are development-only, not independent outcome validation, confidence intervals or guarantees.

### Explanation identity, scale and sampling

- `src/path_project/outputs.py` calls SHAP **ExactExplainer on the actual calibrated wrapper's positive-class probability** across its four original inputs. It does not substitute an underlying raw-tree margin or a different candidate. All imputation, encoding/scaling and nonlinear sigmoid calibration are inside the callable. This is practical because there are only 16 coalitions for four inputs.
- Deterministic seed-366 key hashes choose one tuning interval/person, then **64 tuning people** for the empirical independent background and **128 separate tuning people** for global explanation summaries. No outcome column read for this selection, no calibration/threshold/test participants in background/probe. IDs are internal join/sampling metadata only, never model/explainer predictors.
- Maximum additivity residual on all 128 global profiles: **8.881784197001252e-16**, below 1e-8 tolerance. Reference model probability **0.1919374525299298**, the mean model output over the named 64-person tuning background, not an observed outcome rate. For every scored local profile: base + four contributions = the displayed calibrated probability. Contributions are calibrated probability units; multiplying by 100 only expresses attribution in percentage points, never a log-odds conversion or an intervention effect.
- Global mean absolute probability attributions: recency **0.12283633296757498**, age **0.04492074422467911**, education **0.01590461541793188**, employment **0.012736675536814278**. These summarize model behavior on tuning people, not causal importance or independent performance. Marginal-background mixtures can combine correlated answers unrealistically; background choice/routing/measurement shift matter.
- Every fitted one-hot category/numerical/missing-indicator column is mapped back to readable questions/categories in `reports/outputs_v1/transformed_question_mapping.json`. Four-question SHAP directly explains the complete wrapper; no transformed raw-tree values are silently summed into calibrated probability attributions.

### Output API and honest missingness

- Public API: `path_project.outputs.load_engine(workspace).output(answers, eligibility, wave=7)`. Loading verifies the same selected artifact SHA-256 as stage 9 and the frozen output signature. Accept only age_band, education_level, employment_status, last_cigarette_recency_days. Unused app/research fields and identifiers are rejected, not shown as contributing factors. Source response codes/unit conversion/missing reasons come from the existing verified encoder.
- `configs/output_contract.json` plus `docs/output_contract.md`: probability, endpoint, honest next-interview prediction interval, category/full-precision cuts, readable factors/answers/scale, input completeness and reasons, model version/artifact hash, explanation reference/additivity, limitations and explicit suppression status/reason. No personal confidence field. All cohort gates (adult, established history, current not-at-all, no past-30-day smoking) must be confirmed.
- At fewer than **two supplied model inputs**, unknown eligibility or outside cohort, probability/category are **null** and factors empty, with suppression explanation. Two-of-four is a fixed project usability guard, not a validated accuracy guarantee. Otherwise actual trained missing handling applies; unanswered/don't-know/refused/not-applicable/not-previously-asked remain distinct in metadata and are never assumed zero/No or displayed as invented histories. Completeness counts are not confidence estimates.
- Eight explicitly fictional inference profiles in `tests/fixtures/output_profiles.json` (no actual people/outcomes) executed. Five valid complete/partial profiles scored with matching categories and exact local explanations: recent quitter **0.4952650969**; one-year history **0.2177298603**; longer history **0.0881433171**; not-asked recency **0.0486282331**; partial answers **0.1084525110**. All-unknown, unknown-eligibility and outside-cohort cases suppress appropriately. These are actual model predictions on fictional software inputs, not accuracy or observed-outcome evidence. No personal confidence percentages or causal reduction claims.
- Decision C enforced through the existing timing guard: horizon/date requests rejected; no annual probabilities, event times, estimated relapse dates or survival outputs. Endpoint remains next-survey 30-day smoking status, not every interval resumption or persistent relapse. Development calibration/category outcomes do not establish final-test, clinical or new-user validity.

### Files, actual checks and reproducibility

- Core scripts: `scripts/build_outputs.py`, `scripts/verify_outputs.py`, `scripts/write_output_report.py`. Immutable `artifacts/outputs_v1/` ignored: 64-person background, 128-person global sample, individual global attribution table, manifest. Public `reports/outputs_v1/`: category/global summary, aggregate explanations, transformation mapping, clearly synthetic local outputs and actual versions/code/model provenance. No real participant ID or local real-profile row in reports.
- `docs/model_outputs.md`: required category-selection rule/observed development counts/denominators, global and two detailed fictional local explanations, scale/model identity, correlations/noncausality, missingness and limitations. `docs/output_contract.md` and machine schema document exact fields. Two readable aggregate figures: `reports/output_global_explanations.png` and `reports/output_risk_categories.png`. Visually inspected global figure and corrected overlapping labels to wrapped horizontal labels before final reproducibility proof. README/app README point future UI work to the output API; no actual Streamlit app built or deployed in this stage.
- `tests/test_outputs.py`: **11** synthetic/inference-only tests for outcome-independent weighted cuts/ties/boundaries, unsupported band inputs, deterministic sampling, actual calibrated-wrapper additivity, category/score consistency, missing reasons/suppression, timing/identifier/nonmodel-input rejection and exact transformed-question mapping. No real model fit; existing suite model fits use fictional fixtures only.
- `MPLCONFIGDIR="$PWD/.cache/matplotlib" .venv/bin/python -m pytest tests/test_outputs.py -q -p no:cacheprovider`: exit 0, **11 passed in 1.95s**.
- `.venv/bin/python scripts/build_outputs.py`: exit 0, `built_new_immutable_run`, two frozen cuts, group counts, 64/128-person samples, eight fictional-profile checks, exact probability-scale additivity; **0 models fitted**, no final-test features/outcomes. Workflow measured ~2.99 seconds, not a universal timing guarantee.
- `.venv/bin/python scripts/verify_outputs.py`: exit 0; recomputed frozen score cuts/group descriptions from saved reserved predictions, reconciled private global attributions with actual calibrated model scores, checked source tuning-only membership, nonoverlapping people, exact fictional local outputs/categories/model identity and suppression. No model refit or cutoff reselection.
- `.venv/bin/python scripts/write_output_report.py`: exit 0, two documents/two figures generated from saved aggregate/fictional outputs only. No new real scoring needed for report generation.
- `MPLCONFIGDIR="$PWD/.cache/matplotlib" .venv/bin/python -m pytest -q -p no:cacheprovider`: final exit 0, **117 passed in 6.10s** (pre-build 117 in 6.14s).
- `.venv/bin/python scripts/verify_timing.py`: exit 0; unchanged decision C, schemas/sources/classifier and horizon/date rejection passed.
- `.venv/bin/python scripts/verify_evaluation_splits.py`: exit 0; unchanged participant/temporal boundaries, five grouped folds and held-out membership; final-test answers unopened.
- `.venv/bin/python scripts/verify_inputs.py`: exit 0, **59/59 originals unchanged**.
- `MPLCONFIGDIR="$PWD/.cache/matplotlib" .venv/bin/python /tmp/check_stage10_preservation.py`: exit 0; **158/158 prior cohort/split/baseline/tree/timing artifacts/contracts unchanged** in SHA-256 and mtime. Matching build retry returned `reused_verified_run`, preserving **11/11 frozen output files** in hash/mtime, with no model refit, band reselection or new explanations. Two docs/two figures regenerate byte-identically; public identifier-token scan passed. Proof/verifier source hashes: `reports/output_verification_v1.json`. Temporary helper not required for normal project commands.

### Next stage / stop point

Stage 10 complete. Await the next numbered prompt. Final test remains closed, and no calibrated model, binary threshold, feature mapping, cohort predicate or participant assignment changed. Use the actual four-input model and frozen output engine in a later authorized Streamlit implementation; display project-defined categories, probability-scale attribution limits, missing-input suppression and timing C honestly. Do not turn attributions into intervention advice, a confidence percentage, medical cutoffs or annual risk. Any future final evaluation must assess the frozen model/categories without selecting new cuts from test outcomes. No publication, upload, deployment, Git operation or external message occurred. No user action required.

## Stage 11 — in progress, final-test answers still unopened

Authorized final evaluation only. No applicable AGENTS.md found. Read locked protocol, current model/category/output contracts and original plan evaluation requirements. No existing final-evaluation run/exposure files found. Before accessing any test answer, will save a pre-test freeze containing fitted selected/baseline models, feature schemas, hyperparameters, calibration/thresholds, timing C, evaluation code/config and artifact hashes/version. Static `configs/final_evaluation.json` fixes 1000 participant-cluster bootstrap replicates (seed366), paired model comparisons, fixed calibration bins and subgroup minima (100 people, 20 positive/20 negative records). Selected age and recorded-sex groups and raw-recency definitions fixed before exposure. Weak/undefined results will be reported; no model, calibration, category/binary threshold or group definition will be tuned from test results. Need test evaluator thoroughly on synthetic fixtures, then freeze and run once. Completed retries must reuse saved evidence; partial exposed runs require an explicit incident record rather than silent repeated evaluation.


## Stage 11 — completed one-shot final evaluation

### Pre-test freeze and actual exposure history

- No applicable AGENTS.md found. Read original plan evaluation instructions, locked participant/bootstrap protocol, current selected model/calibrator, feature/category/timing/output contracts and prior status. No existing final-evaluation/exposure run found before implementation. Final test answer rows remained unopened while the evaluator, reporter and all subgroup/CI rules were written and tested.
- `configs/final_evaluation.json` fixed seed366, 1000 paired participant-cluster bootstrap replicates, 95% percentile intervals, fixed probability bins and subgroup definitions/minima before exposure. No test-based model selection, tuning, calibration, threshold changes, resampling to balance evaluation classes or feature selection.
- `src/path_project/final_evaluation.py`, `src/path_project/final_report.py`, `scripts/evaluate_final.py`: one-shot evaluator with source/artifact freeze, exclusive lock, exposure log, prediction checkpoint and completed-result reuse. New metric calculations cache score ordering for efficient tied weighted AP/ROC; tested against sklearn before exposure. No fitting methods are called. Undefined AP/ROC/zero-denominator metrics retain null and explicit valid/undefined bootstrap counts.
- Before any test answer access: `.venv/bin/python -m pytest tests/test_final_evaluation.py -q -p no:cacheprovider` exited0, **8 passed in 1.76s**; full suite `.venv/bin/python -m pytest -q -p no:cacheprovider` exited0, **125 passed in 6.79s**. Tests use fictional data; cover weighted/tied AP/ROC/loss equivalence, absent classes/undefined counts, correct duplicate cluster-draw weights, paired CI determinism, empty calibration bins, subgroup minima, categories, freeze guard and full reporter smoke test. No test outcome was read for these checks.
- `.venv/bin/python scripts/evaluate_final.py --prepare-only`: exit0, **28 pre-test frozen files** saved/verified under `artifacts/final_evaluation_v1/frozen/`: all eight selected/baseline model snapshots (including raw/calibrated comparisons), fitted feature schemas, actual hyperparameters/calibrator coefficients, code/config/test copies, risk thresholds, timing C, source cohort/schema hashes and reserved key snapshot. Full fitted Pipeline/calibrator bytes included, not unfitted configurations. Verified exposure log contained **only freeze_complete** before proceeding.
- Frozen evaluation signature: **0b301df0a9a28468b25d24c5b9e478a4df8859bdbc350cf73a3da90cf04b5e30**. Model version: `xgb_minimal_s1_none:9b46cdb1783302c05c3b56b83d5695a1ad58b90da0614f04188ee687170eae36`.
- `.venv/bin/python scripts/evaluate_final.py`: exit0, **evaluated_frozen_test_once**. Exposure log has exactly four ordered events: freeze_complete, test_access_started, test_predictions_saved, evaluation_complete. Actual host-clock UTC: freeze **2026-11-07T06:09:43.051212+00:00**, test answer access **2026-11-07T06:10:51.350487+00:00**, prediction checkpoint **06:10:51.502103**, completion **06:10:57.733304**. These are infrastructure audit timestamps, not survey or relapse dates. No evaluation_failed event, implementation fix or repeated evaluation occurred.

### Final measured results — retain weak findings honestly

- Locked held-out **Wave 7→8**: **1,243 records / 1,243 people**, **128 positive / 1,115 negative**, prevalence **0.1029766693 (10.30%)**. No repeated test records (cluster bootstrap therefore reduces to participant/record resampling). All test people's earlier rows remain excluded from development. Every locked observed-valid test record evaluated; none dropped for feature availability. All1,243 meet the app's two-input count, which is coverage only, not an accuracy guarantee.
- Selected calibrated model, participant-equal point metrics and 95% bootstrap CI:
  - AP **0.244651**, CI **[0.196115, 0.314595]**; exact stepwise average precision, not trapezoidal PR-AUC. Compare to test prevalence0.102977, not the earlier participant-weighted development prevalence0.208326.
  - ROC-AUC **0.739238**, CI **[0.695498, 0.780962]**.
  - Brier **0.088530**, CI **[0.078152, 0.099269]**.
  - Log loss **0.305075**, CI **[0.275138, 0.336498]**.
  - Mean probability **0.138978**, CI **[0.131478, 0.146730]**, above observed10.30%.
  - Frozen threshold **0.2590049599706509**: TP **60**, FP **155**, FN **68**, TN **960**. Precision **0.279070**, CI **[0.216977,0.335081]**; recall **0.468750**, CI **[0.382807,0.554709]**; specificity **0.860987**, CI **[0.841494,0.880535]**; F1 **0.349854**, CI **[0.283077,0.410667]**. These classifier metrics are not personal-confidence percentages or intervention guarantees.
- All primary selected-model CI metrics had **1000 valid / 0 undefined** replicates. Other models/bins with undefined precision or absent support report metric-specific undefined counts, never invented zero values. Constant prevalence baseline precision is undefined because it predicts no positives at0.5; recall0 and specificity1 are defined. Bootstrap samples bring all records of each sampled person together; duplicate draws each contribute one total participant weight. Paired differences share the same draws. Conditional empirical CIs exclude training/model-selection/survey-design uncertainty.
- Frozen comparisons (no re-ranking or replacement): prevalence baseline AP **0.102977**, ROC0.5, Brier **0.092399**, constant probability **0.1080904267** from training only. Raw minimal logistic AP **0.275942**, Brier **0.084758**; raw full-app logistic AP **0.279608**, Brier **0.084648**. Balanced minimal/full logistic AP **0.279985/0.282184** but poor raw Brier **0.180134/0.184120**. Frozen calibrated minimal logistic AP **0.275942**, Brier **0.087961**. Selected raw tree shares AP/ROC with its calibrated wrapper but Brier **0.085091**, mean score **0.100887**.
- Thus calibration **worsened** selected-tree test Brier0.085091→0.088530, and several frozen logistic baselines had higher test AP. These results remain reported; neither model nor sigmoid/threshold/category cut was changed. Differences can reflect shifts in observation, period and weighting targets but do not identify causes. The selected classifier remains the tuning-chosen artifact. Paired differences and confidence intervals for all frozen comparisons are saved; no new test winner is promoted.
- Frozen risk-category outcomes: lower **23/570 (4.04%)**, CI **[2.46%,5.79%]**, mean predicted **4.44%**; moderate **45/460 (9.78%)**, CI **[7.17%,12.61%]**, mean predicted **12.80%**; higher **60/213 (28.17%)**, CI **[22.07%,34.27%]**, mean predicted **41.58%**. Denominators are observed-valid held-out Wave7→8 records/people, not all PATH/national people. Cuts unchanged0.0750747765280418 /0.2590049599706509; categories remain project-defined, not medical cutoffs.
- Predefined subgroup minima100 people/20 positives/20 negatives applied without relaxation: recent observed last-use recency **191 people/57 positives**, unknown recency **960/55**, recent boundary-excluded sensitivity **157/46**, age18–34 **357/59**, age35–54 **434/50**, recorded male **643/71**, recorded female **598/57** have performance metrics+CIs. Longer observed recency **92/16**, age55+ **452/19**, age unknown0 and recorded-sex unknown **2/0** receive counts and outcome-rate uncertainty only; performance suppressed as prespecified. Do not treat unknown duration as long-term or zero; conditional history questions select observed-recency groups. Recorded binary sex can be inherited from an earlier interview and is not current gender identity. Multiple/small-group comparisons are exploratory, not powered fairness/causal conclusions.
- Timing C retained: no supported survival endpoint/horizon, no timing metrics mixed in, no annual probabilities or relapse dates. The target is next-survey status conditional on observed follow-up, not every interval resumption or persistent relapse. Missing follow-up is not a negative label. No nationally representative or clinical/new-user validity claim.

### Saved evidence and read-only checks

- Required **reports/final_evaluation.md** contains all metrics/CIs, frozen comparator table, paired differences, calibration, confusion matrix, category outcome rates, prespecified subgroup counts/uncertainty/suppression, undefined-metric rules and exposure limitations. Aggregate `reports/final_evaluation_v1/results.json` and three figures: calibration.png, confusion_matrix.png, risk_categories.png. Visually inspected the actual calibration figure; sparse bins retain counts/uncertainty and are not silently hidden.
- Ignored `artifacts/final_evaluation_v1/`: `pretest_freeze.json`, frozen models/code/schema/metadata/test keys, `exposure_log.jsonl`, `test_predictions.parquet`, `complete_manifest.json`. Raw/test participant-level predictions/subgroup fields remain ignored, never public. No raw survey file edited or uploaded.
- Additive **configs/final_evaluation_status.json** records current completion/model/results hashes without rewriting older immutable metadata. **Important:** older stage-specific pending/unopened wording is historical. The old split verifier still prints its stage-5 saved-state “unopened” message; its post-evaluation exit0 verifies only unchanged split membership. It is not authoritative about current exposure. Use the new final verifier/log/status instead. The reserved test has been opened **once and is now closed to tuning**.
- `.venv/bin/python scripts/verify_final_evaluation.py`: exit0; read-only frozen-source/artifact/checkpoint/report hash verification, freeze-before-sole-access event order, Parquet metadata row count, aggregate count/CI consistency, unchanged source model hashes, split signature and public report identifier-token scan. **No test probabilities/metrics/bootstrap recomputed**. Source code is a verifier added after the evaluation; actual evaluation/calculation/rendering code was frozen before access.
- `MPLCONFIGDIR="$PWD/.cache/matplotlib" .venv/bin/python /tmp/check_stage11_saved_evidence.py`: exit0; **174/174 prior cohort/split/model/output files unchanged** in SHA-256 and mtime. A normal evaluation-command retry returned **reused_saved_final_evaluation**, preserving **38/38 final evidence files** including exposure log/prediction checkpoint. No rescoring/rebootstrap/refitting. Rendering report/three figures into /tmp from saved aggregates reproduces exact bytes. Saved proof/verifier hash: `reports/final_evaluation_verification_v1.json`. Temporary helper is not a required project command.
- `.venv/bin/python scripts/verify_inputs.py`: exit0, **59/59 originals unchanged**; input baseline not regenerated. Legacy split verification also exits0 for unchanged 30,890-key membership, with the historical-message caveat above.
- README/app README updated with measured weak results, the current authoritative exposure state and final-evidence paths. All earlier stage status entries describe historical scope. No original proposal/analysis, model/source mapping, cohort or assignment changed; no services, messages, commits, pushes, uploads or deployment.

### Stop point / continuation

Stage 11 complete. Await the next numbered prompt. Do not retune, recalibrate, change categories/groups or swap to a test-favored comparator using this final test. Current selected model still has SHA9b46cdb1783302c05c3b56b83d5695a1ad58b90da0614f04188ee687170eae36. Final results are weaker than development and probability calibration is imperfect; a later demonstration must show research limitations and current measured evidence, not the older pending-test text as if current. Any substantive future model correction needs an explicit exposure-aware plan and appropriate new independent evaluation data, not concealment/repeated “final” testing. No implementation bug or recovery was needed in this run. No user action required to complete stage11; no Streamlit UI or later stage implemented automatically.


## Stage 12 — Streamlit demo implemented; HTTP launch verification blocked

Scope: only stage 12. No applicable AGENTS.md found in workspace/previously checked ancestors. Re-read all 14 proposal slides (6,738 text characters) and the existing 15,755-character implementation analysis; retained the verified snapshot endpoint and timing C rather than the proposal's unsupported time-to-relapse promise. No raw files, proposal, existing analysis, model, calibration, thresholds or locked evaluation splits changed.

Built:
- `app/streamlit_app.py`: centered native Streamlit form with consistent theme, four documented Wave 7 questions, exact categorical response labels, explicit missing choices, whole-number recency and documented units/ranges/conversions. Eligibility gates and the existing two-input guard withhold unsupported estimates. Conflicting ≤30-day recency is rejected. Blank inputs never default to demographic answers. Demonstration presets are clearly fictional, not participant profiles.
- `configs/demo.json`: paths, fixed wording context, selected schema and invented presets. `.streamlit/config.toml`: localhost-only server, telemetry disabled, file watcher disabled, native theme. Existing Streamlit 1.67.0 dependency is already pinned in `requirements-lock.txt`; no installation needed.
- `src/path_project/demo.py`: verifies current final evidence/model identity and loads the unchanged output engine. It updates only an in-memory copy of historical pending-test metadata so UI limitations reflect completed final evaluation. No old frozen files are rewritten.
- Results show calibrated percentage with exact endpoint/variable interval, unrounded category rules, all four top Exact SHAP contributions in calibrated percentage-point units, reference-model-output disclosure, submitted answers/eligibility, completeness and model version/hash. SHAP identity/additivity and actual probability are shared with the existing frozen engine, not a replacement candidate.
- Saved final-test aggregates provide actual performance/uncertainty and a clearly denominated observed-follow-up reference rate. Calibration shortcomings and higher logistic baseline AP are disclosed. No final metric, prediction or bootstrap is recomputed. No annual risks, relapse dates, causal benefits, medical instructions or personal confidence. U.S. survey source, unweighted design, non-U.S./new-user/clinical validity limits are explicit.
- Only engine resources are cached, never answer histories or predictions. No answer file, database, external request, participant ID or contact collection. Form widget state is local session memory; changing presets removes the prior result. Local ephemeral session state is necessary to operate the form.
- `app/README.md` and root README document launch, privacy, missing-resource behavior, tests and limits. `reports/demo_verification_v1.json` records executed checks/source hashes and the uncompleted launch check.

Executed commands and actual outcomes:
1. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_demo.py -q -p no:cacheprovider`: exit0, **6 passed in 4.68s**. Real Streamlit AppTest executes forms and results on three fictional scored profiles, comparing shown percentage/category/SHAP table/model identity with direct frozen inference; checks additive calibrated probability, unknown eligibility, insufficient answers, outside cohort, conflicting recency, blank defaults and reset behavior.
2. `.venv/bin/python -m streamlit run app/streamlit_app.py --server.port 8501`: exit1. Streamlit attempted local server startup but Python `socket.socket` raised **PermissionError: [Errno 1] Operation not permitted**. This sandbox forbids creating listening sockets and approval is unavailable. No HTTP health check or actual browser visual test could run; do not claim the launch passed. AppTest renders the real app without a listening socket and passed independently.
3. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`: exit0, **131 passed in 10.99s**. No retraining/reserved evaluation run by this check; tests operate on synthetic data and frozen inference paths.
4. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_final_evaluation.py`: exit0, saved one-shot artifact/checkpoint/report hashes and aggregate counts reconcile; no rescoring, metric or bootstrap rerun.
5. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_inputs.py`: exit0, **59/59 originals unchanged**.

Remaining blocker and precise next action: launch outside this socket-restricted environment with `.venv/bin/python -m streamlit run app/streamlit_app.py`, open `http://127.0.0.1:8501`, and check the three fictional presets, blank form, warnings and result layout. Record the actual browser/HTTP outcome before marking stage 12 complete. Do not remove sandbox controls or silently treat AppTest as a successful HTTP launch. No other user information, service keys or installation is required. Stop at stage 12; do not retrain, retune, re-evaluate the final test, deploy, commit or advance automatically.


### Stage 12 continuation — 2026-11-08

Continued existing work without changing app sources, frozen artifacts or evaluation splits. Compared all five app/source/config/test SHA-256 values to `reports/demo_verification_v1.json`: unchanged. Retried `.venv/bin/python -m streamlit run app/streamlit_app.py --server.port 8501`: exit1, same `PermissionError: [Errno 1] Operation not permitted` creating a socket. HTTP launch remains unverified; no successful server/browser check is claimed.

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_demo.py -q -p no:cacheprovider`: exit0, **6 passed in 10.42s**, including real Streamlit form/results and direct frozen-path agreement on fictional inputs. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_final_evaluation.py`: exit0, saved one-shot evidence intact with no rescoring/bootstrap/fitting. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_inputs.py`: exit0, **59/59 originals unchanged**. App evidence JSON records this retry separately; prior checks preserved. No later stage run.

Still blocked only on actual socket-enabled launch/browser verification. User action: run `.venv/bin/python -m streamlit run app/streamlit_app.py` from the workspace in an ordinary local terminal, open `http://127.0.0.1:8501`, and confirm the blank form, fictional presets and result layout. Return that observed outcome (or provide a socket-enabled execution environment) before stage 12 is marked complete. Repeating this prompt inside the same restricted sandbox cannot supply the missing launch evidence.

### Stage 12 repeated request — socket preflight

Ran `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python` with a read-only SHA-256 comparison of the five demo source files and a localhost socket preflight. All source hashes match saved passing UI verification. `socket.socket()` still raises `PermissionError: [Errno 1] Operation not permitted`; no server was launched and no HTTP/browser success is claimed. Existing six passing form/result tests remain saved evidence; no redundant test, fitting or final evaluation rerun. Stage 12 remains blocked solely on launch verification. Next action remains running the documented Streamlit command outside this sandbox and reporting the observed form/results outcome.

Stage 12 repeated-request check: executed `.venv/bin/python` localhost socket preflight; `socket.socket()` still fails with `PermissionError: [Errno 1] Operation not permitted`. Verified all five demo source SHA-256 values match saved passing UI evidence. No files in the model/evaluation path changed, no final evaluation rerun, no HTTP launch claimed. Existing blocker and required outside-sandbox launch action remain unchanged.


### Stage 12 user-supplied browser evidence — 2026-11-08

This update supersedes the earlier claim that no successful browser launch has been observed. The user supplied a screenshot of the app at http://127.0.0.1:8501, saved as `/home/hellfire/Downloads/screencapture-127-0-0-1-8501-2026-11-08-06_25_34.png`. The screenshot confirms the local server serves the app and the blank form, eligibility controls, four input controls, submit button, saved study-performance table, calibration warning and limitations expander render in the browser. This is user-supplied visual evidence, not an agent-run HTTP health check. Sandbox socket restrictions remain applicable to the runner itself and need not be retried to disprove the external browser launch.

The user subsequently reported “all blank form submission shows result.” This is ambiguous: it does not establish whether a personal probability appeared or only the suppression warning and always-visible study-performance table. Do not record blank-form suppression or all three fictional preset interactions as browser-passed until the user confirms their actual behavior. An independent targeted check in this session, `.venv/bin/python -m pytest tests/test_demo.py::test_blank_form_withholds_and_shows_actual_final_results -q`, passed (1 passed in 3.17s); it verifies a cohort-confirmation warning and no personal probability metrics for blank submission, but does not replace the pending browser observations.

Remaining browser confirmation: blank submission displays a cohort-confirmation warning without a personal probability/risk category; each of the three fictional presets submits and displays its expected estimate or appropriate warning without an error. Stage 12 is not marked complete by this partial evidence. No model, split, app source or final evaluation was changed.

Stage 12 continuation: rechecked saved five-source SHA-256 evidence (all unchanged) and localhost socket creation using `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python`. Socket creation still denied: `PermissionError: [Errno 1] Operation not permitted`. No model/test evaluation or redundant UI tests run; existing six passing form/result tests retained. Launch verification remains blocked pending an outside-sandbox local launch. No later stage advanced.


### Stage 12 — authoritative reconciliation of browser evidence

Read current status from disk before acting and inspected the actual user screenshot `/home/hellfire/Downloads/screencapture-127-0-0-1-8501-2026-11-08-06_25_34.png`. Local external browser launch and blank-form/performance-section rendering are confirmed. **The later appended socket-preflight entry is stale as a statement about external launch and is superseded by this entry. Do not repeat socket preflight or ask for a new launch.** Screenshot alone does not show a submission result, SHAP table, category or model identity expander. The user's “all blank form submission shows result” remains ambiguous between a personal estimate and the always-visible saved performance table.

Reviewed actual app/adapter/test code: fixed four-input frozen schema, documented options and units, eligibility and insufficient-input suppression, actual calibrated-wrapper SHAP scale/direction, unrounded categories, answer summaries, completeness, local resource-only cache, fictional presets, endpoint/time/population/clinical limitations and saved performance evidence are implemented. No applicable workspace AGENTS.md found. App sources match all five saved source hashes. No implementation change was needed.

Executed `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_demo.py -q -p no:cacheprovider`: exit0, **6 passed in 8.94s**, including all three fictional profiles, exact probability/category/model-version/SHAP consistency, blank/unknown/outside-cohort/recency suppression and reset. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_final_evaluation.py`: exit0, frozen evidence intact, no test rescoring/metrics/bootstrap/fitting. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_inputs.py`: **exit1, 58/59 unchanged; run_prompts.py changed relative to original baseline**. This continuation did not edit or restore run_prompts.py; change provenance is unestablished, and the original hash baseline was preserved. Earlier 59/59 checks remain historical results, not current claims.

Updated README/app README and reports/demo_verification_v1.json to distinguish confirmed launch from pending browser interactions and retain historical failed sandbox launch evidence. No model, raw data, source analysis/proposal or split changed; no final evaluation rerun. Requested only these observations in the already-running app: blank submit produces eligibility warning with no personal percentage/category (study-performance remains visible); each fictional preset submits and shows percentage/category/contributing factors without error. Stage 12 remains blocked on these specific user observations, not server launch. Do not infer they passed from the screenshot or automated tests, and do not advance to another stage or skip its later requested audit.


### Stage 12 browser interaction confirmation — 2026-11-08

The user explicitly confirmed: "Blank submission correctly warns without a prediction; all three presets show results without errors."

Together with the previously supplied browser screenshot, this confirms the required external local launch and browser interaction checks: blank submission correctly withholds the personal prediction and shows the eligibility warning; the recent-last-use, longer-last-use and some-unknown-answers fictional presets all submit and display results without errors. These are user-reported browser observations, not agent-run HTTP or browser automation. This confirmation supersedes all earlier entries requesting these same observations or another outside-sandbox launch. Do not repeat the sandbox socket preflight as a prerequisite for accepting this external verification.

The runner may now assess stage 12 completion using this confirmation and the saved automated evidence, perform its required audit, and proceed to the remaining numbered stages if accepted. No runner checkpoint was manually advanced. No model, split or final-evaluation computation was changed. The previously reported run_prompts.py checksum difference is an intentional runner-instruction edit in this conversation to read current status evidence and avoid stale launch requests; it is not a research-data change. Preserve the original checksum baseline and report the exception transparently.


## Stage 12 — completion audit accepted

Read current on-disk status, including latest explicit user confirmation, before acting. Accepted user-reported browser launch/blank-submit/preset observations with their stated scope; no socket preflight or duplicate launch request. Initial screenshot verifies rendering, user confirmation verifies interactions, and automated checks verify exact frozen prediction identity. Earlier pending/blocked entries are historical and superseded.

Completion audit: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_demo.py -q -p no:cacheprovider` exited0, **6 passed in 10.73s**. All three fictional profiles agree with direct inference for displayed percentage, frozen category, calibrated-probability Exact SHAP contributions/additivity and model version. Blank/unknown/unsupported eligibility, conflicting recency, insufficient inputs and reset paths pass. Reviewed actual adapter/config and app code; no answer persistence, answer-history caching, model substitutions or unsupported timing outputs. All five app-source/config/test SHA-256 values still match saved evidence. No new source change required.

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_final_evaluation.py` exited0: frozen model/calibrator/category/code/split and final saved results reconcile; no predictions, metrics, bootstrap or fitting rerun. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_inputs.py` exited1: **58/59 unchanged**, sole difference `run_prompts.py`. User explicitly identifies this as the intentional runner-instruction edit; it is an allowed orchestration exception, not a raw survey/proposal/analysis/model change. Preserved original checksum baseline and the edited file; did not disguise verifier failure or regenerate hashes.

Updated `reports/demo_verification_v1.json`, root README and app README with completed audit and user evidence, preserving historical failed sandbox launch records. Stage 12 meets completion checks using actual user browser observations plus executed model-path tests. Limitations remain imperfect test calibration, research-only/new-user/non-U.S./clinical validity unestablished, no national inference and timing C (no annual risks/dates). No further user action needed for stage 12. Stop and await the next numbered prompt; do not run another stage, omit a subsequently requested audit, retrain, retune, re-evaluate the reserved test, commit, publish or deploy.


## Stage 13 — verification in progress

Read latest on-disk stage 12 browser confirmation before acting. No socket preflight/launch repetition. Added configuration-driven `scripts/verify_project.py`, `configs/verification.json`, `scripts/audit_deliverables.py`, `tests/test_project_smoke.py` and `docs/build_order.md`. Running `.venv/bin/python scripts/verify_project.py --isolated-build` with PYTHONDONTWRITEBYTECODE=1; logs retained in ignored cache and aggregate evidence will be saved to reports/verification_evidence.json. First full suite: 132 passed in15.79s; eleven existing-evidence commands exited0. Source/mapping/cohort/split regeneration is running in an empty isolated generated-output workspace with spaces in its path. No model searches or final evaluation repeated.

Concrete fixes: explicit ignores for Streamlit/local secrets; corrected current README claims that app was future work and final metrics unavailable, and documented safe dependency/build/replay order. Frozen code and artifacts untouched. First sharing audit: 183 candidate files,10 sensitive ignore probes,0 issues; git ls-files exit128 confirms no real workspace repository, so no tracked deliverables exist. Temporary bare Git metadata used only inside ignored cache to exercise actual ignore rules. Existing original-input baseline/intentional runner edit exception preserved.


## Stage 13 — completed verification and concrete fixes

Only stage 13 executed. Read the current status and user-supplied browser confirmation first; did not repeat socket preflight, HTTP launch or final evaluation. Applicable AGENTS.md searches found none; source assumptions remain the verified cohort/mapping/timing contracts, not unverified proposal claims.

Executed `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_project.py --isolated-build`: **exit0, all22 child commands passed**, aggregate evidence `reports/verification_evidence.json`. Original-root full suite: **132 passed in15.79s**. Eleven existing-evidence commands passed (suite, mapping/header dictionary validation, prediction specification, cohort integrity, split separation, development provenance, baseline and tree serialization/prediction/metric checks, timing capability, calibrated SHAP outputs and saved final integrity). The old split verifier's “unopened” phrase remains historical and was not treated as current exposure evidence.

Actual clean workspace: `.cache/stage13/verification with spaces osmferd6/clean generated output workspace`. Copied code/config/docs, original sources referenced without changes, initially no generated data/artifacts/reports. Regenerated documentation evidence, mapping/dictionary, cohort/ledger, deterministic membership and final input metadata. **9/9 selected regenerated files matched original SHA-256 byte for byte**, including both participant/record split files. Full aggregate cohort30,890labeled/9,597people/3,258positive; ledger36,639eligible/5,749unobserved, as before. Original authoritative locks were never replaced.

Copied existing fitted artifacts/reports into the isolated tree and ran frozen final integrity (no scoring) plus real-artifact synthetic Streamlit/serialization smoke checks: **7 passed in6.60s**. The new smoke test serializes a copy of the actual fitted calibrated pipeline into a temporary path with spaces and verifies identical probabilities after reload/reordered columns; Exact SHAP reconstructs that same probability for all three fictional presets. **212 protected original generated files unchanged in both SHA-256 and mtime**, zero changes. (This saved count is authoritative; an intermediate progress comment estimated197.) No real model search/fit, calibrator/threshold/category refit, test probabilities/metrics/bootstrap or new test selection occurred.

Executed `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_inputs.py` after isolated replay: **exit1,58/59 unchanged**, sole `run_prompts.py` intentional user-confirmed runner-instruction edit. Exact allowed SHA remains in `configs/verification.json`; all other changes are failures. Original baseline preserved, no raw/proposal/existing analysis exception allowed. Do not call the unchanged legacy command passing.

Executed `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/audit_deliverables.py`: zero issues,10/10 sensitive-path ignore probes passed; public candidate count recorded in `reports/deliverable_audit.json`. Real participant-ID tokens and common secret patterns scanned without emitting values. `git ls-files`/`git status` exit128 because the protected `.git` placeholder is not a repository: no tracked deliverables exist, and shareable candidates were checked instead. Temporary bare Git metadata lives only in ignored cache to test actual ignore semantics. No repository initialized/changed in workspace, no uploads/messages/commits/deployment.

Concrete defects fixed: added explicit `.streamlit/secrets.toml`/`secrets.toml` ignores; corrected current README app/final-metric claims and structure table; added `docs/build_order.md`, configuration-driven isolated verifier and report renderer, and required real-artifact synthetic serialization coverage. Frozen scientific code/files were not changed. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/write_verification_report.py` renders `reports/verification.md` from actual aggregate evidence without any research recomputation. Reports retain full command exits/durations and private cache log paths.

Launch/visual scope: existing user screenshot confirms the documented command served the app and initial layout; explicit user confirmation covers blank suppression and three fictional submissions. No agent browser/HTTP session was available; no new visual observation claimed. Automated UI tests establish actual score/category/model identity and probability-scale explanation agreement. Fresh dependency installation, cross-platform run and complete fresh expensive model training were not repeated; safe early-stage regeneration plus frozen model replay was executed instead. Poor calibration/generalization and timing C limitations remain visible and unfixed by test-driven tuning.

Stage13 complete, no material unresolved implementation defect found. No additional user action needed. Await next numbered prompt, including any requested audit; do not advance automatically or reopen final test. Preserved isolated outputs/logs locally for review; they are ignored and need not be shared.


## Stage 14 — documentation and literature verification in progress

Read latest on-disk status and preserved stage12 user browser evidence/stage13 audit. No new app launch, model fit, search or final evaluation. README rewritten with separate already-trained-app quick start, setup/data placement, exact build-order commands, expected outputs, privacy and troubleshooting. Created `docs/final_project_report.md`, `docs/proposal_revision_notes.md`, `docs/presentation_outline.md`, `docs/viva_questions.md`, `reports/literature_verification.json` and `scripts/verify_documentation.py`. Tables authored from saved JSON rather than new model predictions.

Live primary-source verification: PLOS full-text Citation/Discussion confirms the cessation paper's publication details and reported best RF-with-bagging balanced accuracy72%/ROC-AUC0.76. Springer publisher page plus PubMed indexed metadata confirm the required PATH relapse paper, online21March2025, issue2026, volume13 pp1910–1928 and race-specific abstract AUCs. Public abstract's one-year/four-year wording conflict remains unresolved; full methods subscription-restricted. Direct PubMed open returned footer-only; search metadata and publisher accessible. PLOS separate Table2 viewer failed, but full-text Discussion explicitly supports the cited metrics. No unresolved timing wording or universal85% relapse rate adopted as project truth. Original PPTX untouched.

Initial `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_documentation.py`: exit0,49 local links,25 commands,28 final metric cells,7 development rows,7 cohort rows and3 category rows,0errors; original proposal/analysis hashes and new-document private-ID/common-secret checks passed. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_final_evaluation.py`: exit0, saved evidence intact, no computation repeated. Original-input full check running/recorded next; intentional runner exception remains known. Final documentation pass will refresh docs-only evidence without overwriting stage13 historical audit.


## Stage 14 — completed documentation handoff

Completed only stage14. New README has short existing-model quick start, precise local-bundle requirements (not a standalone joblib), discovered Python/environment details, source placement and duplicate policy, a separate research rebuild sequence with dependency order, expected outputs and troubleshooting. Fresh-install/cross-platform behavior remains explicitly unrun; app browser launch/interactions use the already-confirmed user evidence. No repeat launch was requested.

Created `docs/final_project_report.md` (question, related work, source/cohort flow, features/missingness/attrition, leakage/protocol, actual models/development/final metrics and CIs, calibration failures, category rates, exact explanation scale, timingC, limitations and conclusion); `docs/proposal_revision_notes.md` (concrete title/target/metric/rate/promise/national/clinical corrections); `docs/presentation_outline.md` (slides and fictional demo sequence); and `docs/viva_questions.md` (plain defenses of inputs/outputs, accuracy, participant separation, probability quality, SHAP and timing). Original PPTX and existing implementation analysis untouched. No claim of first PATH relapse model; no unrun 25-feature research model claimed trained. Aggregate tables populated directly from saved JSON, figures linked to existing aggregate PNGs.

Literature verified using live web tools against primary publisher pages and PubMed indexed record: required relapse paper DOI10.1007/s40615-025-02385-x has online21March2025/issue2026 metadata; public race-specific AUCs accurately scoped. Public Methods/Results follow-up contradiction remains flagged, full methods paywalled. Required cessation paper DOI10.1371/journal.pone.0286883 full text Citation/Discussion verifies June8,2023 and best RF-bagging balanced accuracy72%/ROC-AUC0.76; cessation and some follow-up predictors differ from this project's baseline-only target. Separate Table2 viewer inaccessible, direct Discussion supports values. `reports/literature_verification.json` records access methods, section provenance and explicit unresolved items. Generic85% relapse assertion remains unverified for this cohort and is recommended for deletion, not adopted.

Executed checks:
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_documentation.py`: exit0, **49 local links,25 documented executables,28 final metric cells,7 development rows,7 cohort rows,3 category rows;0errors**. Checks actual saved aggregates, new-doc known participant-ID/common-secret patterns, original proposal/analysis hashes. `reports/documentation_checks.json` records hashes and scope. Numeric prose and terminology also reviewed against final/development reports; not a new performance calculation.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_final_evaluation.py`: exit0, saved frozen evidence reconciles; **no predictions, metrics, bootstrap, fits or searches repeated**.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_inputs.py`: exit1, **58/59 originals unchanged**, sole intentional user-edited `run_prompts.py`. Baseline remains preserved; no input restored/overwritten to hide this exception.
- Inline source readability/heading check: no duplicate final-report headings; all required files/figures resolve. Docs have no real participant records, raw data or private user inputs. Original stage13 privacy/verification reports were retained as historical checks rather than overwritten for this documentation stage.

One-time authoring helper `/tmp/write_stage14_docs.py` populated tables from existing saved JSON; documentation itself and the reusable verifier are deliverables, not a requirement to rerun that temporary authoring helper. No package installation, new browser run, fresh expensive pipeline, commit, upload, external message, deployment or original-PPTX edit. Model/calibrator/split/threshold/timing decisions remain frozen; probability transfer weaknesses remain explicit.

Stage14 complete; no user action needed. Await next numbered prompt or requested stage14 audit. Do not advance automatically, skip audits or reopen the final test.


## Stage 15 — final objective audit and handoff completed

Read on-disk status and latest stage12 browser observations before acting; stages1–14 have completion artifacts/evidence. Older pending/unopened descriptions are historical. No additional AGENTS.md found in the workspace; original implementation plan/proposal assumptions remain governed by verified scientific contracts. No socket preflight or new external launch requested.

Created **PROJECT_HANDOFF.md** with actual next-survey endpoint, four inputs and supported missing behavior, output/calibrated Exact SHAP meaning, frozen model hash/hyperparameters, actual test metrics/CIs/confusion/category rates, weaker calibration/baseline results, supported timing omissionC, exact app command, stage1–15 command map, private/public output locations, original preservation exception, limitations and sensible future work. Archival pre-test commands are distinctly labeled historical; current final verification reads saved evidence only. No standalone-model-bundle shortcut or fresh-install/full-search success invented.

Created reusable `scripts/verify_handoff.py` and `reports/handoff_checks.json`. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_handoff.py`: **exit0,14 prior stages,26 file links,40 executable references,0errors**. Required code/mapping/dictionary, cohort/schema, participant locks, actual fitted baselines/selected app model, explanation engine, frozen final evidence, app/test/doc files all present/nonempty. Existing output/model/split/final manifests verify; stage14 checked source/document hashes match; stage13 successful isolated-rebuild evidence remains available. All unsupported elapsed/survival/horizon/date flags are false and timingC is justified, not an unrun promised survival model. Handoff numeric cells match actual saved final results; no identifier tokens present.

Executed `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_demo.py tests/test_project_smoke.py tests/test_timing.py -q -p no:cacheprovider`: **22 passed in6.51s**. Fictional input app results, calibrated-score/category/version/explanation identity, actual-artifact serialization consistency, eligibility/missing/invalid handling and timing rejection pass. No reserved participant profiles used as synthetic examples.

Executed `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_final_evaluation.py`: exit0, frozen files/checkpoint/report reconcile without predictions/metrics/bootstrap/fitting. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_inputs.py`: **exit1,58/59 unchanged**, sole exact documented user-confirmed `run_prompts.py` orchestration edit. Original source baseline preserved; no raw/proposal/analysis file edited. Do not misreport this legacy check as passing.

Startup command remains `.venv/bin/python -m streamlit run app/streamlit_app.py` from project root; user browser launch/blank/preset confirmation plus executed Streamlit tests establish working behavior. No new agent HTTP/browser session claimed. No annual probability/date, guaranteed event, medical intervention effect or personal-confidence output is enabled. Original PPTX, locked participant assignment, model/calibrator/threshold/category/timing and one-shot test results remain unchanged. No publication/deployment/Git mutation/commit/push/upload/external message.

Final state: **stages1–15 complete**, with timingC supported omission, intentional runner checksum exception, limited literature-method access, imperfect calibration/generalization, unweighted survey inference, and unrun fresh-install/cross-platform/full-search/new-agent-browser checks explicit. No pending required user action. Retain all local private evidence and consult PROJECT_HANDOFF.md for course/reviewer use. Await any separately requested audit/change; do not advance, skip audits, retune or reopen the exposed final test automatically.


## User-requested consecutive-wave extension — 2026-11-08

The user explicitly authorized approximate month estimates based on FDA wave
collection windows, a short current-situation questionnaire, and probabilities,
risk levels and contributing factors for former smokers returning to smoking.
Include at least three consecutive main surveys (up to eight), with both observed
returns and no observed return. This supersedes v1-only timing restrictions for
a **separate exploratory study**, not for the original frozen classifier.

Implemented configs/longitudinal_v2.json, src/path_project/longitudinal.py,
scripts/train_longitudinal.py, scripts/verify_longitudinal.py and
app/longitudinal_app.py. The entry point defaults to the new model and offers the
preserved original app/legacy_app.py via sidebar. Existing v1 tests now target
the preserved legacy file; new tests exercise the default entry point and route.
README, app/README and handoff identify the new default and link the full
protocol in docs/longitudinal_v2.md.

Corrected v2.1: 7,643 distinct baseline former-established smokers with no
past-30-day use and >=3 consecutive attended interviews from the chosen origin;
1,939 first observed returns to current-established every-day/some-day smoking;
5,704 censored without observed return. One earliest eligible origin per person,
no missing-wave bridging, no future predictors, no artificial class balancing.
Future attendance selects the retrospective sample and can bias generalization.
Wave midpoint differences supply explicitly assumed observation times, not
measured relapse times. End-of-follow-up does not establish permanent quitting.

Initial diagnostic v2 incorrectly interpreted Wave 8 outcome-coded 0/1 as
baseline 1/2. It was caught before app delivery, preserved and marked invalid;
separate corrected v2.1 artifacts/reports are the only ones loaded. Regression
tests cover coding normalization. No v1 cohort/model/split was changed.

Compared 8 vs 11 inputs, exponential vs Weibull, penalties 1/10 using separate
validation IPCW Brier. Selected 8-input Weibull, penalty10; refit training+validation
and calibrated on independent participants. Splits: train4585/validation1146/
calibration764/test1148. Tests are a new study partition, not an independent
replication of v1 and not a v1 retune. Eight inputs: age, education, employment,
last-cigarette recency, electronic nicotine use, household use, mental health,
emotional problems7d. At least6 including recency required as a usability guard.

Held-out assumed-time metrics: at18months AUC0.7461/Brier0.0809 vs no-input0.0853;
at36months AUC0.7764/Brier0.1269 vs baseline0.1437; at60months AUC0.7748/
Brier0.1516 vs baseline0.1807. Mean predictions underestimate IPCW observed risk
(36months13.61% vs17.26%); app explicitly reports imperfect calibration. No test
retuning. Report includes participant-bootstrap intervals and alternative clock
sensitivity, not individual timing confidence or actual-relapse error.

Outputs: 12/18/24/36/48/60-month assumed-time probabilities, fixed36-month
calibration-tertile relative risk, whole-month approximate median only if risk
reaches50% by60months, otherwise explicit no-median message; separately labeled
median conditional on observation by60months. Exact original-feature Shapley
attributions sum to the displayed horizon probability. No causal claim, clinical
validity, precise actual resumption date or national/non-US validity asserted.
Answers stay local/session-only. No packages, deployment, upload or messages.

Executed: full pytest suite146passed; new synthetic observation/censoring/model
checks and actual Streamlit profile/horizon/invalid-input/legacy-route checks;
verify_longitudinal.py --rebuild-cohort exactly reconstructed the saved cohort,
verified hashes and reproduced disjoint membership without fits/test rescoring;
verify_final_evaluation.py passed for v1 without predictions/fits; verify_inputs.py
returned1 with58/59 unchanged, the same previously user-confirmed run_prompts.py
exception documented in stages14/15. No baseline overwritten to hide it.

Current run: data/processed/longitudinal_v2_1 and artifacts/longitudinal_v2_1 are
private local artifacts; reports/longitudinal_v2_1 holds aggregate results and
verification. Run .venv/bin/python -m streamlit run app/streamlit_app.py. Preserve
all v1 and new frozen evidence. Substantive future model changes require another
separately versioned experiment. No interactive new browser launch claimed.


## User-requested single-model UI revision — 2026-11-08

User requested automatic month/probability outlook, professional responsive UI,
only the consecutive-wave model, no editable dropdowns, no deploy button, and
correction of false missing-input errors. Implemented without changing the
frozen longitudinal model, original data or existing artifact hashes.

The entry point routes directly to the redesigned Reclaim assessment. Original
next-survey UI is retired from navigation; its files remain archived. Removed
horizon selection; all12/18/24/36/48/60-month cumulative probabilities appear
automatically. The primary probability, relative risk and exact contributing
factors consistently use the existing36-month reference. Timing conditions,
approximate midpoint basis and calibration caveat remain visible.

Added app/styles.css for a navy/teal responsive layout: native fixed-choice
radio controls, cards, live completion, charts, factor/details tabs and research
disclosure. Source includes mobile breakpoints, wrapping metric text, keyboard
focus and reduced-motion rules. No searchable selectboxes or free-text category
controls. Numeric duration input remains intentionally numeric and editable.

Fixed the recency bug: entering an amount now directly records the answer;
removed the separate unknown/supplied mode that could discard a visible number.
The numeric input always allows an empty value, including when examples were
prefilled. Outside-form native widgets rerun immediately. Completion reflects
actual supplied answers; errors name missing gates/fields, and correcting an
answer clears stale errors. Result/session signature changes invalidate old
predictions. At least6/8 answers including recency still required by backend;
unknown answers remain unknown and are never invented.

Disabled top/deployment toolbar via client.toolbarMode=minimal, ui.hideTopBar,
showSidebarNavigation=false and CSS. Changed watcher to auto. Existing server
needs one restart to load configuration. No deployment, server launch, package
installation, external request, model fit or held-out test rescoring performed.
Model resources alone are shared-cached; current result/answers are session-only.

Verification: full suite149passed; eight actual new-UI regression tests cover
manual complete entry, both fictional profiles, automatic full curves, accurate
probability/explanation identity, optional unknowns, invalid and corrected
eligibility/recency, numeric clearing, stale-result invalidation, single model,
no editable dropdowns, responsive source breakpoints and toolbar configuration.
scripts/verify_longitudinal.py passed source/output/raw hashes, aggregates and
membership without model refit or held-out prediction recomputation. The earlier
exact cohort reconstruction remains prior-stage evidence; current integrity run
did not repeat it. UI source fingerprints and scope recorded in
reports/longitudinal_v2_1/ui_revision.json. No interactive browser viewport test
or production hosting validation claimed. Updated README/app guide/handoff and
protocol for the retired legacy route. The known original run_prompts.py checksum
exception from stages14/15 remains unrelated and untouched.


## Available-answer scenarios and reliability panel — 2026-11-08

User requested removing the eligibility rejection, using available answers,
showing how sure predictions are, and a more colorful professional interface.
Added src/path_project/assessment.py as a separate inference adapter, preserving
the frozen model/source and strict predict_profile API. Current UI no longer
blocks incomplete profile/feature answers. Confirmed supported profiles retain
exact previous probability, curve and explanation. Unknown profiles are
conditional; known unsupported profiles are explicitly hypothetical adult
former-smoker scenarios, not forecasts validated for current/recent smokers,
never-smokers or minors. A duration<=30days is visibly excluded from that
hypothetical scenario and uses fitted missing handling, not a fabricated
eligible value. Original entered value stays in the summary. Blank submissions
use the separately fitted no-input baseline, never a fabricated personal score;
no personalized factors are attributed when no model answers are supplied.

Added visible reliability panel: Limited model evidence, usable-answer coverage
percentage explicitly not confidence, population support, held-out group ROC-AUC
and available participant-bootstrap interval, calibration means and approximate
clock limitation. Personal confidence percentage is unavailable/null; group AUC
is not presented as personal correctness. The no-input reference displays its
own baseline metrics rather than the full questionnaire model's. Missing-input
and unsupported-profile performance is explicitly unvalidated. Versioned the
session signature so results from the prior UI are invalidated on hot reload.

Professional palette expanded with subtle blue/teal/violet/gold timeline cards,
light gradients and distinct evidence/coverage/scope tiles; responsive stacking,
fixed choices and hidden deploy toolbar retained. Updated app/readme/protocol
and UI evidence. Full suite151passed; ten current UI tests exercise supported,
partial, unknown, unsupported, blank-reference, corrected-input cases and exact
matched-profile score preservation. Frozen model source/artifact hashes pass.
No refit, held-out prediction rescoring, package installation, external request
or browser viewport validation. Original raw/model artifacts remain unchanged.
