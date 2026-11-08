# Reclaim — Smoking Return Outlook

A Python and Streamlit research application for exploring the estimated chance
of a **first reported return to current established smoking** after quitting.
Built for CSE366 using the Population Assessment of Tobacco and Health (PATH)
Study, with participants observed in at least **three consecutive main waves**.

The active application uses the **consecutive-wave v2.1 model**. It presents
approximate month horizons, relative risk and contributing factors through a
responsive interface. The original next-survey application is retired.

**This repository contains source code, configuration, metadata and aggregate
research results. Raw survey data and trained models are excluded. A fresh
clone cannot generate predictions until a compatible private model bundle is
restored or a new study is built from authorized data.**

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
produce conditional estimates; unsupported profiles produce explicitly labeled
hypothetical adult former-smoker scenarios. With no usable model answers, the
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
private `artifacts/longitudinal_v2_1/model.joblib` bundle. Loading checks model,
source, configuration and report fingerprints. A mismatched bundle is rejected
rather than silently replaced. The full cohort verifier additionally requires
the raw data and private processed participant file.

## Set up a fresh clone

The working environment uses **Python 3.13.5 on Linux**. `pyproject.toml` declares
Python 3.11+, but fresh installations and other platforms have not been verified.
The lock file records the existing environment, including research dependencies.

Run these commands inside your cloned repository:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.
The archived PDF-inspection pipeline also needs the system `pdftotext` command;
the current longitudinal training command does not parse PDFs.

Then choose one of the following paths:

1. **Restore an authorized, compatible private bundle.** Restore its matching
   source/configuration, model and aggregate manifests/results. Private files
   remain ignored; do not bypass fingerprint checks or load untrusted joblib
   files. Launch the app using the command above.
2. **Build a new local experiment.** Obtain the authorized survey files and
   follow the next section. This creates a newly trained model, rather than
   restoring the already evaluated model.

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
with the saved output paths will fail. **For a fresh-clone experiment only**,
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
  partial/out-of-profile scenarios are not validated. Complete answers do not
  guarantee a precise prediction.
- This unweighted U.S. study does not establish national representativeness,
  clinical usefulness or performance for present-day users or other countries.

## Verification

Synthetic longitudinal tests can run without private data or model artifacts:

```bash
.venv/bin/python -m pytest tests/test_longitudinal.py -q -p no:cacheprovider
```

With a compatible current private bundle and raw data available:

```bash
.venv/bin/python scripts/verify_longitudinal.py
# Optional exact cohort reconstruction; no fitting or test rescoring:
.venv/bin/python scripts/verify_longitudinal.py --rebuild-cohort
.venv/bin/python -m pytest tests/test_longitudinal_app.py -q -p no:cacheprovider
```

The full original workspace passed **151 tests**, including current UI tests.
Running the full suite also requires private **archived v1** artifacts; it is not
a source-only-clone check. The historical `verify_inputs.py` check has a
documented 58/59 match because of the user-edited orchestration runner; do not
rewrite its original checksum baseline. These results describe the local
workspace, not a verified fresh install or production hosting deployment.

## Repository layout and upload boundaries

| Path | Purpose | Included in source repository? |
|---|---|---|
| `app/` | Active UI, styles and archived original UI | Yes |
| `src/path_project/` | Cohort, modeling, inference and explanation code | Yes |
| `scripts/`, `configs/` | Build/verification commands and versioned contracts | Yes |
| `tests/` | Tests and fictional fixtures | Yes |
| `docs/` | Protocols, source metadata and historical research documentation | Yes |
| `reports/longitudinal_v2_1/` | Current aggregate results and verification | Yes |
| `reports/longitudinal_v2/` | **Invalid initial diagnostic**, preserved and labeled; do not use its results | Yes, historical only |
| Other `reports/` and v1 documents | Archived original next-survey study | Yes, historical only |
| `.streamlit/config.toml` | Local UI/server settings; no credentials | Yes |
| `PATH/`, `data/`, `artifacts/` | Raw data, participant records, fitted models and private references | **No** |
| `.venv*/`, `.cache/`, `.analysis/`, `.prompt-runner/` | Environment, caches and local research/orchestration state | **No** |
| `.env*`, `.streamlit/secrets.toml`, `.aws/` | Local configuration/secrets | **No** |

`.gitignore` excludes CSV/TSV and binary data/model formats by default. The two
feature-dictionary CSVs are explicitly allowed because they contain public
metadata; aggregate report CSVs are ignored, with JSON equivalents retained.
Only reviewed aggregate results belong in the public reports directory.

The active app writes no answer files and uses no external prediction API.
Answers and the current result stay in session memory; only model resources are
shared-cached. This privacy behavior does not make trained artifacts public:
they can contain private explanation backgrounds and must remain excluded.

Archived [v1 final report](docs/final_project_report.md) and
[historical build order](docs/build_order.md) concern a different next-survey
target. Their four-question UI, performance and timing restrictions do not
describe the active v2.1 application. Consult
[PROJECT_STATUS.md](PROJECT_STATUS.md) for the chronological audit history and
[the app guide](app/README.md) for current UI details.
