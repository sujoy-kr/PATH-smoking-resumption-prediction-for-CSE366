# Stage 4 cohort preparation

This is deterministic data preparation under `configs/cohort.json`, `configs/prediction_specification.json` and `configs/feature_mapping.json`. It does not fit preprocessing, select predictors, split participants, train or evaluate a model. The original proposal, analysis and survey files remain unchanged. The 25 candidates are retained regardless of their association with outcomes; all counts here are descriptive and unweighted.

## Commands and environment

Run from the workspace root with `/home/hellfire/Downloads/CSE366 Project/.venv/bin/python` (Python 3.13.5). The existing isolated environment supplies pandas 3.1.1 and pyarrow 26.0.1; exact dependency versions are saved in `requirements-lock.txt` and run provenance. No installation was needed. Bare `python` is unavailable.

```bash
.venv/bin/python scripts/build_cohort.py
.venv/bin/python scripts/diagnose_cohort_recency.py
.venv/bin/python scripts/verify_cohort.py
.venv/bin/python -m pytest -q -p no:cacheprovider
.venv/bin/python scripts/verify_inputs.py
```

`build_cohort.py` validates mappings against actual TSV headers before processing. It reads only selected columns from one canonical DS file per wave, with identifiers explicitly read as strings. Wave 8 supplies only PERSONID and the two outcome columns. All eight files have unique, nonempty identifiers. Unexpected duplicates, invalid identifiers or join multiplicity stop execution with counts rather than identifier values. Two selected raw wave frames are held at a time; follow-up projection excludes candidate responses.

## Cohort and labels

At each starting interview in Waves 1–7, include official former-established-cigarette status=Yes AND official past-30-day cigarette use=No. Use only the immediately next scheduled wave (1→2 through 7→8), without requiring any other wave. Predict next-interview past-30-day cigarette use: Yes=1, No=0. Current-established smoking is a separate nullable secondary outcome, never a substitute for the primary label. Baseline unknown or ineligible responses are counted by reason; outcome nonresponse is never a negative label.

The main dataset includes valid observed primary outcomes. The ledger includes every eligible interval: absent follow-up and present interviews with unknown primary responses retain null outcomes and distinct reasons. A participant can contribute several intervals. Their string identifier is solely for internal joins and later participant grouping. Future stages must split participants before learned preprocessing or model choices; interval rows from the same person must not cross a participant split.

| Pair | Eligible | Labeled | Positive | Unobserved |
|---|---:|---:|---:|---:|
| 1→2 | 4,401 | 3,684 | 416 | 717 |
| 2→3 | 4,580 | 4,090 | 447 | 490 |
| 3→4 | 4,685 | 4,164 | 505 | 521 |
| 4→5 | 5,470 | 4,722 | 563 | 748 |
| 5→6 | 5,847 | 4,463 | 393 | 1,384 |
| 6→7 | 5,854 | 4,861 | 478 | 993 |
| 7→8 | 5,802 | 4,906 | 456 | 896 |
| Total | 36,639 | 30,890 | 3,258 | 5,749 |

The labeled records represent 9,597 people with 10.55% positive interval outcomes. There are 6,830 people contributing multiple labeled intervals and 21,293 records beyond each person's first record. The eligible ledger represents 11,717 people. Unobserved outcomes comprise 5,746 absent next interviews and three present interviews with system-missing primary outcomes (one at Wave 7 and two at Wave 8). These are observations missing for this task, not known non-events; no imputation or attrition weighting is performed.

## Harmonization and availability

Fixed transformations use documented response labels and component missing-code metadata. Revised Wave 2/3 indicators are selected by the existing mapping. Missing numeric durations remain null; valid zero remains zero. Each candidate has a nullable numeric value, a `__reason` column, and `__component_reasons` JSON recording nonobserved source-component reasons. This preserves structural skip, refusal, don't know, not ascertained and other documented distinctions even when a multi-component transformation cannot produce a value. Categorical values retain mapped codes and documented labels. No missing-value learning or automatic skip-to-zero occurs.

Raw last-cigarette number/unit responses define approximate recency (days, months×365.25/12, years×365.25 where documented). The proxy recent-quitter subgroup is separately marked `(30, 365.25]` days. Unknown recency remains unknown. A separate boundary sensitivity excludes raw one-month, twelve-month and one-year responses; it does not change main eligibility. These approximate historical quantities are not time until relapse. No undocumented historical reconstruction, carry-forward, future answer or all-wave intersection is used. Conditional questions often yield structural missingness for former smokers.

Feature availability is reported for each interval in both the eligible ledger population and the labeled population, including every missingness reason and source-component counts. In labeled records, raw recency is available for 10,150/30,890, prior smoking intensity for 4,526/30,890, and regular-smoking duration for 4,793/30,890. These limitations are retained and documented rather than hidden by dropping people. Most other candidates are more widely available, but availability and instrument scope vary by wave. Future feature decisions must use training participants only. No requirement is made that a user provide a value for a structurally unasked question.

## Saved outputs and schema

Internal, ignored files in `data/processed/cohort_v1/`:

- `cohort.parquet`: one row per person and eligible adjacent interval with valid primary outcome; baseline candidates and reason metadata, secondary label, baseline QC and recency subgroup metadata.
- `eligible_interval_ledger.parquet`: all baseline-eligible intervals including unknown/missing follow-up, without candidate-value expansion.
- `schema.json`: column types, roles, units and labels, plus an explicit candidate-predictor allowlist. PERSONID, wave/interval administration, outcomes, QC, subgroup and reason metadata are not automatically model inputs.
- `run_manifest.json`: input/config/code fingerprints, actual interpreter and dependency versions, immutable output hashes and summary.

Aggregate-only `reports/cohort_v1/` contains summary, cohort flow with sequential exclusion reasons, feature availability, component missingness counts, legacy comparison, schema, input audit, provenance, validation and a readable cohort report. JSON and CSV forms are supplied for flow, availability and legacy comparisons. `reports/cohort_v1_recency_diagnostic.json` supplies additional aggregate source-backed explanation without modifying the immutable run. No participant rows or identifier values belong in reports. `verify_cohort.py` reconciles ledger/main labels and keys, aggregates, baseline component provenance and report tokens against internal identifiers without printing those identifiers.

`cohort_v1` is immutable. An identical retry verifies original input and saved output hashes and reuses the run. Changed code/config/environment/input signatures or incomplete/changed saved files fail clearly rather than overwriting. Do not delete outputs, alter the original-input manifest or replace future locked splits to bypass a mismatch. If a substantive correction is required later, preserve this run and configure a separately named run and output directories, documenting the reason. A stale build lock requires investigating an interrupted process before any deliberate recovery; no automatic overwrite is performed.

## Comparison with the preserved analysis

`.analysis/cohort_counts.json` is diagnostic only. All main primary/secondary-status counts match. Recent-quitter counts differ for documented reasons:

- Wave 2→3: the old JavaScript lookup of an absent derived DAYSQUIT column yields undefined/NaN and zero subgroup records. The documented raw number/unit pair gives 812 recent-proxy records, 278 positive. The old zero does not mean nobody quit recently.
- Wave 6→7: raw reconstruction adds 109 recent-proxy records (30 positive), giving 753/231 instead of 644/201.
- Wave 7→8: raw reconstruction adds 113 records (32 positive), giving 698/182 instead of 585/150.

For both latter differences, every extra record reports raw twelve months or one year: the mapped conversion is 365.25 days, while the released derived field is rounded to 365.3 and fails the old ≤365.25 cutoff. The diagnostic verifies exact released values, joins one-to-one internally, checks deltas against the preserved analysis and emits only counts. Source evidence: `PATH/DS6001/36498-6001-Codebook.pdf` physical page 1844, R06R_A_DAYSQUIT_CIGS; `PATH/DS7001/36498-7001-Codebook.pdf` physical page 2179, R07R_A_DAYSQUIT_CIGS (declared one decimal place). No records were changed to reproduce old totals. The prespecified boundary sensitivity addresses approximate-unit ambiguity separately.

## Tests and limits

`tests/fixtures/synthetic_cohort.json` is an explicitly fictional fixture, separate from real data. Tests cover binary coding, missing outcomes, one-to-one ID joins and leading zeros, unit conversion, valid zero versus structural/no-answer states, retained component reasons, unchanged baseline features under future-answer mutations, rejection of future mappings, adjacency without all-wave intersection, nullable Parquet round trips, rounded boundary behavior and immutable output checks.

The endpoint remains next-survey status with unknown varying individual follow-up intervals (timing decision C). Smoking between interviews can be missed; current status does not establish persistent relapse, exact resumption dates or fixed-year risk. Results are unweighted and not nationally representative. No model, fitted transformation, evaluation split, performance estimate or app risk claim is produced in this stage. Stop here and await the next numbered prompt.
