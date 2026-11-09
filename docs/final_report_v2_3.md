# Predicting smoking transitions for any adult (PATH Study)

CSE366 course project. Final model: v2.3 ([protocol and tables](longitudinal_v2_3.md)).
No clinical, causal or national-representativeness claim.

**Data.** PATH Study adult public-use files, waves 1-8. Three populations: 10,412
former smokers (3,058 returns), 14,258 current smokers
(5,724 stops) and 28,604 adults with fewer than 100
lifetime cigarettes (2,092 starting regular smoking).

**Method.** One interval-censored proportional-hazards model per population, chosen by
the person's answers. Participant-level split; selection on validation; test scored once.

**Results.** At 36 months held-out ROC-AUC is 0.815 (former),
0.689 (current) and 0.782 (never-established); every shown
horizon beats a no-input model on Brier score.

**Limitations.** Modest discrimination for current smokers, approximate timing, snapshot
outcomes, possibly informative attrition, adults only. See the protocol.
