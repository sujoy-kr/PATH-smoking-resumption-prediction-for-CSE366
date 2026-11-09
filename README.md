# Reclaim — Smoking Return Outlook

A Python/Streamlit research application (CSE366) that estimates the chance of a
**first reported return to current established smoking** after quitting, using
the Population Assessment of Tobacco and Health (PATH) Study, waves 1–8.

The active model is **v2.2**: a penalized, interval-censored proportional-hazards
survival model with a flexible baseline hazard. It is stored as plain JSON
(`artifacts/longitudinal_v2_2/model.json`); no pickle is loaded. Design,
protocol and held-out results: [docs/longitudinal_v2_2.md](docs/longitudinal_v2_2.md).
Short report: [docs/final_report_v2_2.md](docs/final_report_v2_2.md). Remaining
limits: [docs/known_limitations.md](docs/known_limitations.md).

## Run

Python 3.13 (tested 3.13.5):

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-app.txt
.venv/bin/python run_app.py            # Windows: .venv\Scripts\python.exe run_app.py
```

Open http://127.0.0.1:8501. The launcher first checks the model hashes, numpy/pandas
versions and five fictional regression profiles. No raw data, GPU, API key or
scikit-learn is needed to run the app. Tests/training: `pip install -r requirements-test.txt`,
then `python -m pytest -q -p no:cacheprovider`.

## What the app shows

- Cumulative probability at approximately **18, 24, 36, 48 and 60 months**. The
  12-month horizon is not shown because it did not beat a no-input baseline.
- A relative risk group (tertiles of predicted 36-month risk) and exact Shapley
  contributing factors for the 36-month probability.
- A held-out evidence panel with ROC-AUC, Brier score and the **range** of
  observed risk (a return is only known to lie between two interviews).
- No probability is shown for answers outside the study population (current or
  recent smokers, never-smokers, minors, last cigarette 30 days ago or less) or
  with fewer than 6 of 8 answers / no recency answer. A blank form shows no result.
  

## Headline results (1,440 held-out people)

| Months | ROC-AUC | Brier (model / no inputs) | Mean estimate | Observed range |
|---|---|---|---|---|
| 18 | 0.736 | 0.091 / 0.097 | 16.2% | 10.4–19.6% |
| 36 | 0.781 | 0.118 / 0.141 | 22.4% | 18.1–23.1% |
| 60 | 0.790 | 0.136 / 0.168 | 25.4% | 23.1–25.1% |

Personal confidence, actual month-of-return accuracy and clinical use are **not**
validated. Months are approximate (window midpoints; no interview dates).

## Reproduce the study (needs the PATH files, which are not in Git)

```bash
.venv/bin/python scripts/train_longitudinal_v2_2.py           # writes data/, artifacts/, reports/ for v2.2
.venv/bin/python scripts/verify_longitudinal_v2_2.py --rebuild-cohort
```

Retraining reproduces `model.json` byte-for-byte. A changed protocol needs a new
version name; the script refuses to overwrite an existing run.

## Repository map

| Path | Purpose | In Git |
|---|---|---|
| `app/`, `run_app.py` | Streamlit UI and checked launcher | Yes |
| `src/path_project/survival.py`, `study.py` | v2.2 model, metrics, runtime loader, explanations | Yes |
| `src/path_project/study_training.py` | v2.2 cohort, split, fitting, evaluation | Yes |
| `src/path_project/assessment.py`, `final_inputs.py` | App answer encoding and suppression rules | Yes |
| other `src/`, `scripts/`, `configs/`, `docs/`, `reports/` | Supporting code and historical v1/v2.1 research (restored for reference) | Yes |
| `configs/longitudinal_v2_2.json` | Study configuration | Yes |
| `artifacts/longitudinal_v2_2/model.json` | Fitted model (JSON, no participant rows) | Yes |
| `reports/longitudinal_v2_2/` | Aggregate results, manifest, verification | Yes |
| `tests/` | 26 default tests; `--research-tests` adds historical ones | Yes |
| `PATH/`, `data/`, `.venv/`, `releases/` | Raw survey data, processed cohort, environment, local archives | **No** |

v1 (next-survey) and v2.1 material, and the Oct-10 presentation, describe retired
models. `.gitignore` excludes tabular data and every binary model format;
the only model exception is the JSON file above. Answers stay in session memory;
there is no external prediction API.
