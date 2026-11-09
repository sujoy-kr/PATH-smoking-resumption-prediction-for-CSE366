# Predicting smoking transitions for any adult (PATH Study)

CSE366 course project. Final model: v2.4 ([protocol and tables](longitudinal_v2_4.md)). No clinical, causal or national-representativeness claim.

**Data.** PATH Study adult public-use files, waves 1-8: 10,412 former smokers (3,068 returns), 14,258 current smokers (5,837 stops) and 28,604 adults with fewer than 100 lifetime cigarettes (2,110 starting regular smoking). One row per entry into a state; 29 candidate inputs.

**Method.** One interval-censored survival model per population, chosen from the person's answers; a baseline hazard per survey period; inputs chosen on validation data; shift and slope calibration from out-of-fold predictions; 100 bootstrap refits for uncertainty ranges; test set scored once.

**Results.** 36-month held-out ROC-AUC 0.82 (former), 0.78 (current, up from 0.69 with the older inputs) and 0.77 (never-established). Every shown horizon beats a no-input model on Brier score.

**Limitations.** Absolute percentages for former and current smokers at 36+ months may be somewhat high against a simple observed-risk range (the likelihood checks do not show it; unresolved); moderate discrimination for current smokers; approximate timing; adults only. See the protocol.
