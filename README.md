# Reclaim — Smoking Return Outlook

A Python/Streamlit research application (CSE366) that estimates, for **any adult**, the
chance of the next smoking transition, using the Population Assessment of Tobacco and
Health (PATH) Study adult files, waves 1–8:

| Your situation | Chance estimated |
|---|---|
| Quit smoking (100+ lifetime cigarettes, now not at all) | returning to smoking |
| Smoke every day or some days | stopping smoking |
| Fewer than 100 lifetime cigarettes | becoming a regular smoker |

Each situation has its **own model** (interval-censored survival model, plain JSON in
`artifacts/longitudinal_v2_3/model.json`, no pickle). Protocol and held-out results:
[docs/longitudinal_v2_3.md](docs/longitudinal_v2_3.md); short report:
[docs/final_report_v2_3.md](docs/final_report_v2_3.md); limits:
[docs/known_limitations.md](docs/known_limitations.md).

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

- Four profile questions route you to the right model; the question list adapts
  (last-cigarette time is asked only of former smokers).
- Cumulative probability at the horizons that beat a no-input baseline on validation
  (18/24/36/48/60 months for former and current smokers; 12–60 for never-established).
- A relative level, exact Shapley contributing factors and a held-out evidence panel
  with ROC-AUC, Brier score and the **range** of observed risk.
- No result only when: under 18 (adult data only), a profile that can't be routed,
  contradictory answers, or too few answers. Nothing is forced through the wrong model.

## Headline results (held-out, 36 months)

| Model | ROC-AUC | Mean estimate | Observed range |
|---|---|---|---|
| Former → return | 0.815 | 28.3% | 24.0–28.1% |
| Current → stopping | 0.689 | 29.3% | 21.5–30.5% |
| Never-established → regular smoker | 0.782 | 6.1% | 5.1–6.4% |

The current-smoker model discriminates only modestly. Personal confidence, exact timing
and clinical use are **not** validated. Months are approximate (wave midpoints).

## Reproduce the study (needs the PATH files, which are not in Git)

```bash
.venv/bin/python scripts/train_longitudinal_v2_3.py           # writes data/, artifacts/, reports/
.venv/bin/python scripts/verify_longitudinal_v2_3.py --rebuild-cohort
```

Retraining reproduces `model.json` byte-for-byte. A changed protocol needs a new
version name; the script refuses to overwrite an existing run.

## Repository map

| Path | Purpose | In Git |
|---|---|---|
| `app/`, `run_app.py` | Streamlit UI and checked launcher | Yes |
| `src/path_project/survival.py`, `study.py` | Survival model, metrics, runtime loader, explanations | Yes |
| `src/path_project/study_training.py` | Cohorts, split, fitting, evaluation (three populations) | Yes |
| `src/path_project/assessment.py`, `final_inputs.py` | App answer encoding and suppression rules | Yes |
| other `src/`, `scripts/`, `configs/`, `docs/`, `reports/` | Supporting code and historical v1/v2.1 research (restored for reference) | Yes |
| `configs/longitudinal_v2_3.json` | Study configuration | Yes |
| `artifacts/longitudinal_v2_3/model.json` | Fitted model (JSON, no participant rows) | Yes |
| `reports/longitudinal_v2_3/` | Aggregate results, manifest, verification | Yes |
| `tests/` | 30 default tests; `--research-tests` adds historical ones | Yes |
| `PATH/`, `data/`, `.venv/`, `releases/` | Raw survey data, processed cohort, environment, local archives | **No** |

v1 (next-survey) and v2.1 material, and the Oct-10 presentation, describe retired
models. `.gitignore` excludes tabular data and every binary model format;
the only model exception is the JSON file above. Answers stay in session memory;
there is no external prediction API.
