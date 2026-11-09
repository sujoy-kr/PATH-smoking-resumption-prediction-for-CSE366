# Reclaim — Smoking Return Outlook

A Python/Streamlit research application (CSE366) that estimates, for **any adult**, the
chance of the next smoking transition, using the Population Assessment of Tobacco and
Health (PATH) Study adult files, waves 1–8:

| Your situation | Chance estimated |
|---|---|
| Quit smoking (100+ lifetime cigarettes, now not at all) | returning to smoking |
| Smoke every day or some days | stopping smoking |
| Fewer than 100 lifetime cigarettes | becoming a regular smoker |

Each situation has its **own model** (interval-censored survival model with 100 bootstrap refits, plain JSON in
`artifacts/longitudinal_v2_4/model.json`, no pickle). Protocol and held-out results:
[docs/longitudinal_v2_4.md](docs/longitudinal_v2_4.md); short report:
[docs/final_report_v2_4.md](docs/final_report_v2_4.md); limits:
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
  (for example, last-cigarette time only for former smokers; cigarettes per day and
  time to first cigarette only for current smokers).
- Cumulative probability at every horizon that beat a no-input baseline on validation
  (12, 18, 24, 36, 48 and 60 months), each with a **95% uncertainty range** from 100
  bootstrap refits of the model (shaded band on the chart).
- A relative level, exact Shapley contributing factors (by input group) and a held-out
  evidence panel with ROC-AUC, Brier score and the observed-risk range.
- No result only when: under 18 (adult data only), a profile that can't be routed,
  contradictory answers, or too few answers. Nothing is forced through the wrong model.

## Headline results (held-out, 36 months)

| Model | ROC-AUC | Mean estimate | Observed-risk range |
|---|---|---|---|
| Former → return | 0.820 | 26.6% | 19.4–23.3% |
| Current → stopping | 0.781 | 30.3% | 19.0–26.2% |
| Never-established → regular smoker | 0.771 | 6.9% | 6.3–7.6% |

For former and current smokers the mean estimate at 36+ months sits above the simple
observed-risk range, so absolute percentages for those groups may be somewhat high
(rankings are more reliable); the app says so. Personal confidence, exact timing and
clinical use are **not** validated. Months are approximate (wave midpoints).

## Reproduce the study (needs the PATH files, which are not in Git)

```bash
.venv/bin/python scripts/train_longitudinal_v2_4.py           # writes data/, artifacts/, reports/
.venv/bin/python scripts/verify_longitudinal_v2_4.py --rebuild-cohort
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
| `configs/longitudinal_v2_4.json` | Study configuration | Yes |
| `artifacts/longitudinal_v2_4/model.json` | Fitted model (JSON, no participant rows) | Yes |
| `reports/longitudinal_v2_4/` | Aggregate results, manifest, verification | Yes |
| `tests/` | 36 default tests; `--research-tests` adds historical ones | Yes |
| `PATH/`, `data/`, `.venv/`, `releases/` | Raw survey data, processed cohort, environment, local archives | **No** |

v1 (next-survey) and v2.1 material, and the Oct-10 presentation, describe retired
models. `.gitignore` excludes tabular data and every binary model format;
the only model exception is the JSON file above. Answers stay in session memory;
there is no external prediction API.
