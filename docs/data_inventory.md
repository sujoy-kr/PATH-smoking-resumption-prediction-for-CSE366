# Verified local data inventory

## Scope and source preservation

Stage 1 inventories local inputs only. No participant records, IDs, cohort joins, splits, or models are generated. All 59 original source files are recorded with byte size and SHA-256 in `docs/original_inputs.sha256.json`; this baseline was taken before implementation edits. `.venv`, backups, caches and orchestration/control directories are outside the input baseline. Original proposal, analysis, and survey files are read-only inputs to this project.

No applicable AGENTS.md was found in workspace descendants (excluding environment trees) or the ancestor locations checked. The existing `.git` placeholder is not a usable repository (`git status --short` exited 128). No Git initialization or repository mutation was performed.

## Adult survey files

Counts below were verified by streaming every canonical TSV with Python csv.reader. Headers include PERSONID for all waves. Zero row-width mismatches were found. Wave identity was checked against each local adult codebook and questionnaire cover.

| Wave | Canonical input | Bytes | Rows | Columns | Duplicate identical |
|---|---|---:|---:|---:|---|
| 1 | `PATH/DS1001/36498-1001-Data.tsv` | 209,655,859 | 32,320 | 1,742 | Yes |
| 2 | `PATH/DS2001/36498-2001-Data.tsv` | 221,592,895 | 28,362 | 2,208 | Yes |
| 3 | `PATH/DS3001/36498-3001-Data.tsv` | 185,793,364 | 28,148 | 2,140 | Yes |
| 4 | `PATH/DS4001/36498-4001-Data.tsv` | 228,996,579 | 33,822 | 2,181 | Yes |
| 5 | `PATH/DS5001/36498-5001-Data.tsv` | 242,967,682 | 34,309 | 2,315 | Yes |
| 6 | `PATH/DS6001/36498-6001-Data.tsv` | 218,121,275 | 30,516 | 2,588 | Yes |
| 7 | `PATH/DS7001/36498-7001-Data.tsv` | 240,119,283 | 30,801 | 2,813 | Yes |
| 8 | `PATH/DS8001/36498-8001-Data.tsv` | 270,360,608 | 31,477 | 3,085 | Yes |

Each has a byte-identical duplicate at `PATH/TSV/36498-N001-Data.tsv` (N = wave 1–8). Full SHA-256 values and duplicate paths are in `reports/input_inventory.json`. Only `configs/project.json` canonical DS paths are selected; copies remain untouched. No other adult data copies were found in the original workspace file listing.

## Documentation and auxiliary inputs

| Wave | Codebook | Main questionnaire | Other local documentation |
|---|---|---|---|
| 1 | `PATH/DS1001/36498-1001-Codebook.pdf` | `PATH/DS1001/36498-1001-Questionnaire.pdf` | `36498-1001-Documentation-Informed_Consent.pdf`; `36498-1001-Documentation-Nonresponse_Report.pdf` |
| 2 | `PATH/DS2001/36498-2001-Codebook.pdf` | `PATH/DS2001/36498-2001-Questionnaire.pdf` | `36498-2001-Documentation-Nonresponse_Report.pdf` |
| 3 | `PATH/DS3001/36498-3001-Codebook.pdf` | `PATH/DS3001/36498-3001-Questionnaire.pdf` | `36498-3001-Documentation-Nonresponse_Report.pdf` |
| 4 | `PATH/DS4001/36498-4001-Codebook.pdf` | `PATH/DS4001/36498-4001-Questionnaire.pdf` | `36498-4001-Documentation-Informed_Consent.pdf`; `36498-4001-Documentation-Nonresponse_Report.pdf` |
| 5 | `PATH/DS5001/36498-5001-Codebook.pdf` | `PATH/DS5001/36498-5001-Questionnaire.pdf` | `36498-5001-Documentation-Nonresponse_Report.pdf` |
| 6 | `PATH/DS6001/36498-6001-Codebook.pdf` | `PATH/DS6001/36498-6001-Questionnaire-English.pdf` | `36498-6001-Documentation-Nonresponse_Report.pdf` |
| 7 | `PATH/DS7001/36498-7001-Codebook.pdf` | `PATH/DS7001/36498-7001-Questionnaire-English.pdf` | `36498-7001-Documentation-Nonresponse_Report.pdf`; `36498-7001-Questionnaire-English_Telephone_Showcards.pdf`; `36498-7001-Questionnaire-Spanish_Telephone_Showcards.pdf` |
| 8 | `PATH/DS8001/36498-8001-Codebook.pdf` | `PATH/DS8001/36498-8001-Questionnaire-English.pdf` | `36498-8001-Documentation-Nonresponse_Report.pdf` |

All eight codebooks and main questionnaires are present. Wave 7 additionally has English and Spanish telephone showcards; these are not substitutes for the main English questionnaire. Codebooks were converted to temporary text for inspection; questionnaires were inspected at their covers, not fully harmonized at this stage.

Weights/design: Wave 1 has `VARPSU`, `VARSTRAT`, `R01_A_PWGT` and replicate weights `R01_A_PWGT1`–`100`; Wave 2 has the analogous `R02_A_PWGT` and 100 replicates. No header matches for WGT/WEIGHT/STRAT/PSU occur in waves 3–8. No separate weight datasets, linkage files, or public-use user guide were found among local inputs. The Wave 8 questionnaire cover says “with Weights”, but the actual local adult TSV contains no weight columns; the cover does not establish weight availability. Weight choice/design handling is unresolved and national representativeness must not be claimed. PERSONID is present for future joins; no separate linkage file is required for joining these adult files, though its cross-wave properties still require validation.

## Existing proposal, analysis and scripts

- `Smoking_Relapse_Predictor_Presentation.pptx`: 14 slides, text and tables inspected using python-pptx. Proposes ensembles, MICE, SMOTE, SHAP and binary classification while subtitle promises time-to-relapse. Claims about >0.80 AUC, 85% relapse, national and clinical usefulness are proposal claims, not established project results. Embedded visual artwork was not independently interpreted as scientific evidence.
- `Project_Analysis_and_Implementation_Plan.md`: read in full. Actual row/column counts match its eight-wave table. Its pairwise outcome counts and literature claims remain preliminary; no cohort computation or external citation verification was performed in this stage.
- `.analysis/profile.cjs`: legacy Node TSV profiler; `.analysis/cohort.cjs`: legacy pairwise cohort calculator. The latter writes `.analysis/cohort_counts.json`, so it was inspected but not executed. `.analysis/cohort_counts.json` and extracted codebook texts `w1.txt`, `w2.txt`, `w8.txt` preserved.
- `PATH/DS1001/convert.py`: pandas TSV-to-CSV conversion with append behavior; do not run, as full conversion is unnecessary and reruns could append duplicate rows.
- `PATH/TSV/filter_all_waves.py`: computes all-eight-wave PERSONID intersection and writes `common_all_8_waves_ids.csv`. Preserved and unused; not the default cohort.
- `PATH/TSV/common_all_8_waves_ids.csv`: existing participant identifier output, sensitive and ignored. `PATH/TSV/all columns.txt`: legacy column listing, preserved.
- `run_prompts.py`, `RUNNER_README.md`, `Build_Project_Prompts.md`: existing prompt orchestration materials, preserved. No additional pipeline scripts existed at inspection. `.venv-windows-backup-20261107-074423` preserved and unused.

## Scientific decisions and verified cautions

Working research definition for subsequent stages: former established cigarette smokers with no past-30-day smoking at interview t; prediction at t using only information available then; positive outcome is past-30-day smoking reported at the next observed scheduled wave t+1. Missing follow-up is not a negative label. This measures next-survey smoking status; it misses temporary interval smoking and does not establish persistent relapse or an exact relapse date. Adjacent-wave availability, rather than all-eight-wave intersection, is the intended starting point. Final cohort definition and variable mapping must be documented before training.

Codebook checks by variable section:
- All eight past-30-day indicators use 1 = Yes and 2 = No, not binary 0/1. These are derived smoking status indicators, not relapse dates.
- Former-established variables in waves 2 and 3 end in `_REV`; revised descriptions exclude recanters. Wave 1 description uses more than 100 lifetime cigarettes; later descriptions use at least 100. Algorithms and eligibility must be harmonized rather than assumed identical.
- Early-wave derived missing codes include -99999 (not ascertained), -99988 (don’t know), -99977 (refused), -99955 (deleted) and -99911 (inapplicable); some include -99966. These are variable-specific, not universal encodings.
- Waves 6–7 cohort/outcome sections list system missing `.` and -97777 (removed at respondent request); Wave 8 selected sections list `.`. Negative or dot values must never be interpreted as valid no-smoking responses.
- Header verification confirms Wave 2 lacks the derived `_DAYSQUIT_CIGS` column. Raw number/unit fields require questionnaire routing and unit validation before use. Time since quitting is never time until relapse.
- Detailed candidate-feature units, skip patterns, ID uniqueness, longitudinal eligibility, exact wave collection periods and historical cohort rates are not established by this structural inventory. Variable dictionary work remains for the next requested stage. No assumption of equal annual intervals is permitted.
- Split participants before learning transformations or tuning; keep evaluation prevalence and final test untouched. PERSONID is joining/grouping metadata only. No splits exist from stage 1. SHAP describes model behavior, not causal effects. Risk categories and probabilities require validation.

## Local tools and reproducibility

Selected executable: `/home/hellfire/Downloads/CSE366 Project/.venv/bin/python` (Python 3.13.5). This existing environment is isolated (`sys.prefix != sys.base_prefix`). `/usr/bin/python3` also reports 3.13.5; bare `python` and `uv` were not found. Available tools include `/usr/bin/pip`, `/usr/bin/pip3`, `/usr/bin/git`, `/usr/bin/pdftotext`, `/usr/bin/unzip`. Use interpreter-qualified pip; do not use global pip for installation.

`reports/environment.json` records actual interpreter/platform/import versions. Core data/model/Streamlit and documentation/testing imports succeeded. `requirements-lock.txt` is an exact pip-freeze snapshot of the preinstalled environment (including optional packages); `pyproject.toml` declares the smaller intended dependency set. The snapshot is not a hash-locked, cross-platform guarantee; fresh installation has not been tested and no network or dependency installation was needed. Optional SHAP/XGBoost were listed as installed but are not part of the essential-import check. CPU-only execution is intended; preinstalled NVIDIA packages are incidental and not required by stage 1.

Initial Matplotlib import could not write to the read-only home configuration directory and successfully used /tmp. `scripts/check_environment.py` now sets a writable workspace cache using `configs/project.json`. pip also warned about its nonwritable home cache and disabled caching; version listing/freezing still succeeded.

Intended commands (run at workspace root):
```bash
.venv/bin/python scripts/check_environment.py
.venv/bin/python scripts/inventory_inputs.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_inputs.py
```
For a future fresh machine, install Python 3.13, create `.venv` with the discovered interpreter (`/usr/bin/python3 -m venv .venv` only if absent), then `.venv/bin/python -m pip install -r requirements-lock.txt`. Installation requires an available package source and was not exercised here. No model-training or app command exists yet.

New structure: `src/path_project/`, `scripts/`, `configs/`, `docs/`, `tests/`, `data/processed/`, `artifacts/`, `reports/`, `app/`. Raw PATH, legacy analysis, all data, trained artifacts, CSV/TSV outputs, environments, and caches are ignored. Reports may contain only reviewed aggregate results. Nothing was published, deployed, committed or pushed.

## Missing inputs and remaining limitations

No local separate later-wave weights/design datasets or general public-use user guide found. These are not blockers for this unweighted course-project scaffold, but are needed if later scope calls for population inference or routing details absent from supplied materials. No model or derived participant data exists. Stage 1 does not verify literature references or collection dates, estimate performance, create a feature dictionary, or define a locked final-test split.
