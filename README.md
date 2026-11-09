# Reclaim — Smoking Return Outlook

A Python and Streamlit research application for exploring the estimated chance
of a **first reported return to current established smoking** after quitting.
Built for CSE366 using the Population Assessment of Tobacco and Health (PATH)
Study, with participants observed in at least **three consecutive main waves**.

The active application uses the **consecutive-wave v2.1 model**. It presents
approximate month horizons, relative risk and contributing factors through a
responsive interface. The obsolete prompt runner remains removed. Useful
earlier research code, tests and documentation are restored as clearly indexed
references, not reactivated in the UI. **Use `run_app.py` to launch the project.**

**The handoff includes the exact trained prediction model**, source code,
configuration, metadata, aggregate results and fictional regression examples.
Teammates and faculty can generate the same model outputs without downloading
raw PATH data or retraining. Raw surveys, processed participant histories and
other research models remain excluded. See [TEAM_SETUP.md](TEAM_SETUP.md).

## Download and run

Download/clone the complete repository or extract the provided handoff ZIP,
then open a terminal in the folder containing `run_app.py`. Use **Python 3.13**
(tested: **3.13.5**).

Linux/macOS:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-app.txt
.venv/bin/python run_app.py
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-app.txt
.venv\Scripts\python.exe run_app.py
```

Open **http://127.0.0.1:8501**. The launcher checks the model, dependencies and
five fictional prediction profiles before starting Streamlit. Runtime
dependencies are CPU-only; no GPU, CUDA, XGBoost, external API or raw survey
files are needed for the active app. Install dependencies once; internet is
not required for local prediction afterward.

The tested handoff uses the existing Linux environment. New installations on
Windows/macOS have not been verified. Identical answers must reproduce the
included regression examples within numerical tolerance; this is reproducible
software behavior, not a guarantee of individual forecast accuracy.

## What the app shows

- Cumulative probability at approximately **12, 18, 24, 36, 48 and 60 months**,
  displayed automatically without choosing a horizon.
- A relative risk category and exact Shapley contributing factors for the
  **36-month** probability.
- Approximate median observation time when modeled risk reaches 50% within
  follow-up, plus a separately labeled conditional timing estimate.
- A reliability panel separating answer coverage, population support and
  measured group performance. It does not invent a personal “percent sure.”

The questionnaire covers age, education, employment, time since the last
cigarette, electronic nicotine use, household tobacco/nicotine use, mental
health and recent emotional problems. Four profile questions establish context.
Fixed-choice controls prevent arbitrary category entry.

Partial answers use fitted missing-value handling. Unknown profile answers
produce conditional estimates; unsupported profiles are suppressed with an explanation, as are
submissions with fewer than six usable answers or no recency answer. With no usable model answers, the
app shows the fitted study reference rather than a personal prediction. These
fallbacks do not expand the model's validated population.

## Run in the existing trained workspace

From the project root:

```bash
.venv/bin/python -m streamlit run app/streamlit_app.py
```

Open **http://127.0.0.1:8501**. If that port is occupied, add
`--server.port 8502`. Restart an existing server after configuration changes.
The local configuration disables telemetry and hides the deployment toolbar.
No API keys, account or external prediction service are required.

Keep the compatible `configs/`, `src/` and aggregate `reports/` files with the
included `artifacts/longitudinal_v2_1/model.joblib` bundle. Loading checks model,
source, configuration and report fingerprints. A mismatched bundle is rejected
rather than silently replaced. The full cohort verifier additionally requires
the raw data and private processed participant file.

## Set up a fresh clone

Use the download-and-run steps above for normal teammate/faculty use. The
following files must be present; they are included in the prepared handoff:

| File or folder | Why it is needed |
|---|---|
| `artifacts/longitudinal_v2_1/model.joblib` | Exact fitted model, preprocessing, calibration and explanation reference |
| `src/`, `app/` | Prediction code and responsive UI |
| `configs/`, `docs/feature_dictionary*.csv` | Model contracts, question coding and fingerprinted metadata |
| `reports/longitudinal_v2_1/` | Matching model manifest and aggregate evidence |
| `requirements-app.txt`, `run_app.py` | Pinned app setup and verified startup |
| `tests/fixtures/handoff_profiles.json` | Fictional expected outputs checked at startup |
| `.gitattributes`, `.streamlit/config.toml` | Byte-preserving checkout and local server/UI settings |

If the model is missing from a downloaded copy, that copy is incomplete for
inference. Include the exact file permitted by `.gitignore`; do not upload all
of `artifacts/`, disable integrity checks, or substitute an untrusted joblib file.

Use `requirements-app.txt` for the app and `requirements-test.txt` for tests.
The restored `requirements-lock.txt` is a historical full Linux research
snapshot, including optional GPU/research packages. It is not needed for the
app. PDF-based source inspection in the restored research tools also requires
system `pdftotext`; the current app and longitudinal training do not parse PDFs.

## Obtain data and build a new experiment

Obtain PATH public-use adult questionnaire data through the official study's
data-access links. Access and reuse remain subject to the provider's terms:
[FDA PATH overview and data access](https://www.fda.gov/tobacco-products/research/fda-and-nih-study-population-assessment-tobacco-and-health).
There is no automatic data download or bundled participant dataset.

Place the eight canonical adult TSV files as configured in
[configs/project.json](configs/project.json), for example:

```text
PATH/DS1001/36498-1001-Data.tsv
PATH/DS2001/36498-2001-Data.tsv
...
PATH/DS8001/36498-8001-Data.tsv
```

The training script refuses to overwrite existing data, artifact **or report**
directories. A clone includes published aggregate reports, so simply running it
with the saved output paths will fail. **For a separate research experiment only**,
first give the experiment separate output paths:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path('configs/longitudinal_v2.json')
config = json.loads(path.read_text())
run = 'longitudinal_local_01'
config.update(
    version=run,
    data_dir=f'data/processed/{run}',
    artifact_dir=f'artifacts/{run}',
    report_dir=f'reports/{run}',
)
path.write_text(json.dumps(config, indent=2) + '\n')
PY

.venv/bin/python scripts/train_longitudinal.py
.venv/bin/python scripts/verify_longitudinal.py --rebuild-cohort
.venv/bin/python -m streamlit run app/streamlit_app.py
```

The setup snippet uses a shell heredoc; on other shells, edit those four
configuration fields directly. Choose a new unused run name for each subsequent
experiment. **Do not run this configuration change in the existing trained
workspace:** its frozen bundle depends on the original configuration hash.
Do not delete saved outputs or edit manifests to force a retry.

Training constructs the cohort, partitions people, selects and calibrates a
survival model, evaluates the selected model and writes separate outputs. A new
data release or environment may produce different results or fail schema checks.
Do not assume a new experiment inherits the published model's validation.

## Study design and measured results

The saved v2.1 study contains **7,643 distinct people**: **1,939** first observed
returns to current established smoking and **5,704** with no observed return
before follow-up ended. Each person has one eligible origin with at least two
further consecutive attended interviews. Missing main waves are not bridged.

The model uses baseline answers only. People are separated for training,
selection, calibration and testing. Participants without observed returns
contribute censored follow-up; they are not labeled as permanently quit. The
selected model is a penalized Weibull survival model with eight inputs.

Held-out test: **1,148 people**, including **291** observed returns over their
available follow-up. Under the assumed midpoint clock:

| Approximate horizon | IPCW ROC-AUC | IPCW Brier score | No-input baseline Brier |
|---|---:|---:|---:|
| 18 months | 0.7461 | 0.0809 | 0.0853 |
| 36 months | 0.7764 | 0.1269 | 0.1437 |
| 60 months | 0.7748 | 0.1516 | 0.1807 |

Lower Brier scores indicate smaller probability errors. IPCW adjusts for
censoring under assumptions described in the protocol. ROC-AUC measures ranking;
it is **not** a personal confidence percentage or percentage of correct forecasts.

**Calibration is imperfect:** at 36 months, mean predicted risk was **13.61%**
versus **17.26%** estimated observed risk. The model underestimates average test
risk. See the [full protocol](docs/longitudinal_v2.md),
[saved results](reports/longitudinal_v2_1/results.json) and
[cohort summary](reports/longitudinal_v2_1/summary.json).

## Interpretation and limitations

- Months use **wave collection-window midpoints**, not individual interview or
  resumption dates. The endpoint is first **observed/reported** current smoking;
  actual smoking may resume earlier, and episodes between interviews can be missed.
- Current established smoking means every-day or some-day smoking. It does not
  prove persistent relapse. No observed return does not prove continuous abstinence.
- Consecutive attendance selects participants using future participation.
  Attrition, self-report and censoring assumptions limit generalization.
- Risk levels are relative calibration-score groups, not medical thresholds.
  Contributing factors explain model associations, not causes.
- Individual confidence, actual month-of-resumption error, and performance for
  personalized estimates for partial answers are not validated. Complete answers do not
  guarantee a precise prediction.
- This unweighted U.S. study does not establish national representativeness,
  clinical usefulness or performance for present-day users or other countries.

## Verification

Check the included model and compare five fictional profiles with saved
probabilities, timing estimates and explanations. This needs no raw PATH data:

```bash
.venv/bin/python scripts/verify_runtime.py
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m pytest tests/test_longitudinal.py tests/test_longitudinal_app.py tests/test_runtime_handoff.py -q -p no:cacheprovider
```

For research verification only, with separately obtained raw data and the
processed cohort available:

```bash
.venv/bin/python scripts/verify_longitudinal.py
# Optional exact cohort reconstruction; no fitting or test rescoring:
.venv/bin/python scripts/verify_longitudinal.py --rebuild-cohort
```

The complete current suite has **22 tests**, covering the longitudinal model,
UI and distributable handoff. Run all of them with
`.venv/bin/python -m pytest -q -p no:cacheprovider`. They need the included model
but no raw PATH files or obsolete next-survey artifacts. Historical research
tests are restored but opt in with `--research-tests`; some require separately
restored private v1 artifacts and extra dependencies. They are not part of the
default current-app run. See [the research guide](docs/RESEARCH_GUIDE.md) for
usable synthetic selections and dependency limits. The current model and
expected predictions are unchanged. These checks do not claim a verified fresh
install or production hosting deployment.

## Repository layout and upload boundaries

| Path | Purpose | Included in source repository? |
|---|---|---|
| `app/` | Active consecutive-wave UI/styles plus historical legacy source | Yes |
| `src/path_project/` | Cohort, modeling, inference and explanation code | Yes |
| `scripts/`, `configs/` | Build/verification commands and versioned contracts | Yes |
| `tests/` | Tests and fictional fixtures | Yes |
| `docs/` | Current protocol/metadata and indexed historical research references | Yes |
| `reports/longitudinal_v2_1/` | Current aggregate results and verification | Yes |
| `reports/feature_mapping_evidence.json`, `reports/prediction_source_evidence.json` | Source-documentation evidence for survey fields | Yes |
| `reports/cleanup.json` | Record of removed obsolete files and preservation checks | Yes |
| `reports/restoration.json`, historical v1 reports | Restoration record and earlier comparison/audit evidence; not current-model results | Yes |
| `.streamlit/config.toml` | Local UI/server settings; no credentials | Yes |
| `artifacts/longitudinal_v2_1/model.joblib` | Exact current prediction/explanation bundle | **Yes, authorized team/faculty handoff** |
| `PATH/`, `data/` | Preserved local survey files and current processed cohort | **No** |
| `Smoking_Relapse_Predictor_Presentation.pptx` | Original coursework presentation | Yes |
| `.venv*/`, `.cache/`, `.analysis/`, `.prompt-runner/` | Environment, caches and local research/orchestration state | **No** |
| `.env*`, `.streamlit/secrets.toml`, `.aws/` | Local configuration/secrets | **No** |

`.gitignore` excludes CSV/TSV and binary data/model formats by default. The two
feature-dictionary CSVs are explicitly allowed because they contain public
metadata; aggregate report CSVs are ignored, with JSON equivalents retained.
The only model exception is the exact current bundle listed above. Do not
unignore other artifacts. `.gitattributes` preserves model and fingerprinted
source/dictionary bytes across checkouts.
Only reviewed aggregate results belong in the public reports directory.

The active app writes no answer files and uses no external prediction API.
Answers and the current result stay in session memory; only model resources are
shared-cached. The included model contains **16 survey-derived baseline
reference records** for explanations, but no PERSONIDs or full histories.
Share the handoff with authorized teammates/faculty and respect the source
data's access/reuse terms; including a model does not establish unrestricted
redistribution rights. Other artifacts remain excluded. No commit, upload,
public publication or deployment is performed by the setup tools.

To create an offline handoff archive from this workspace (dependencies still
need installation), run:

```bash
.venv/bin/python scripts/build_handoff.py
```

It produces `releases/reclaim-team-handoff.zip` with a per-file SHA-256 manifest.
Archives are ignored by Git; source files and the one model are included
directly. The builder refuses to overwrite an existing archive.

Some shared modules and fingerprinted metadata retain historical names because
the saved model and validated transformations depend on them. They are still
needed; renaming/removing them would break the trained bundle. Consult
[the study protocol](docs/longitudinal_v2.md),
[PROJECT_STATUS.md](PROJECT_STATUS.md) and [the app guide](app/README.md) for the
current project. Cleanup did not alter the trained model or `PATH/` contents.

For further development and faculty preparation, use the
[current faculty guide](docs/faculty_guide.md) and
[research/maintenance index](docs/RESEARCH_GUIDE.md). Restored old reports describe
the earlier next-survey classifier; do not present their metrics or timing
restrictions as the current app's results. The old ignored private model runs,
participant artifacts and caches were not restored from Git.
