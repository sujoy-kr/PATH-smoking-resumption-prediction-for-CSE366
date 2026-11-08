# Cohort preparation results (unweighted)

Target: past-30-day cigarette smoking at the next scheduled interview among eligible former established smokers. No model trained; these are cohort counts, not model performance or national estimates.

| Pair | Baseline eligible | Missing interview | Invalid outcome | Labeled | Positive | Prevalence |
|---|---:|---:|---:|---:|---:|---:|
| 1-2 | 4,401 | 717 | 0 | 3,684 | 416 | 11.29% |
| 2-3 | 4,580 | 490 | 0 | 4,090 | 447 | 10.93% |
| 3-4 | 4,685 | 521 | 0 | 4,164 | 505 | 12.13% |
| 4-5 | 5,470 | 748 | 0 | 4,722 | 563 | 11.92% |
| 5-6 | 5,847 | 1,384 | 0 | 4,463 | 393 | 8.81% |
| 6-7 | 5,854 | 992 | 1 | 4,861 | 478 | 9.83% |
| 7-8 | 5,802 | 894 | 2 | 4,906 | 456 | 9.29% |

Overall: 30,890 labeled person-interval records, 9,597 unique people, 3,258 positive outcomes. Repeated records beyond each person's first: 21,293. No all-eight-wave intersection was used.

All baseline-eligible intervals are retained in the separate local observation ledger. Missing/invalid primary outcomes remain null and do not enter the labeled cohort. Feature missingness causes no cohort exclusions. Per-feature eligible/labeled availability and distinct missing/skip/error reasons are in the aggregate JSON/CSV tables. Identifiers and participant rows are not shown.

## Legacy diagnostic comparison

The original `.analysis/cohort_counts.json` is read as a diagnostic only and is never rewritten. Primary and secondary status counts use the official indicators, the same adjacent-pair eligibility and valid primary outcome requirement. The new pipeline validates unique string identifiers and proper one-to-one joins; it does not force any count to match.

| Pair | Metric | Actual | Legacy | Difference |
|---|---|---:|---:|---:|
| 2-3 | recent_recency_observed_records | 812 | 0 | +812 |
| 2-3 | recent_recency_positive_outcomes | 278 | 0 | +278 |
| 6-7 | recent_recency_observed_records | 753 | 644 | +109 |
| 6-7 | recent_recency_positive_outcomes | 231 | 201 | +30 |
| 7-8 | recent_recency_observed_records | 698 | 585 | +113 |
| 7-8 | recent_recency_positive_outcomes | 182 | 150 | +32 |

Quit-recency differences are expected especially for Wave 2: the legacy JavaScript selects a nonexistent DAYSQUIT column (findIndex=-1), so its recent-quit comparisons use an undefined/NaN value and count zero. This pipeline uses documented raw number/unit reports, never missing-as-zero. Other differences, if present, must be assessed against the saved metric deltas and observed feature validity reasons; source precision/range checks can also reject inconsistent raw values. The rounding sensitivity is separate and does not change the core cohort.

Individual elapsed interview times and resumption dates remain unavailable. A negative follow-up window does not prove interval-long abstinence; a positive does not prove persistent relapse. Attrition can be informative. No imputers, learned feature selection, resampling, splits, calibration or final-test evaluation were run.
