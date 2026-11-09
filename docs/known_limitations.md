# Known limitations

The v2.3 models resolve the v2.1 design and logic flaws (see the table in
[longitudinal_v2_2.md](longitudinal_v2_2.md)) and extend coverage to every adult
([longitudinal_v2_3.md](longitudinal_v2_3.md)). What remains is inherent to the
data or the question:

1. Interview dates are not in the public-use files; wave-window midpoints are used.
2. Returns that began and ended between interviews are invisible.
3. Attrition after the first follow-up interview may be informative.
4. Evaluation under interval censoring is partly identified: observed risk is a range.
5. Explanations assume independent inputs.
6. Former-smoker estimates at 36–60 months run 1–2 points above the observed range; the current-smoker model discriminates only modestly (ROC-AUC about 0.68) and its stop event can be temporary.
7. Sample is unweighted, U.S.-only; not clinical advice; no validated personal confidence.
8. Hashes in the manifest detect accidental corruption only. The model is plain
   JSON, so loading it cannot execute code.
9. The retired v2.1 pickle remains in git history (it embedded 16 survey-derived
   baseline rows). Rewrite history if your data-use terms require removal.
10. v1 (next-survey) documents, scripts and the Oct-10 PPTX describe a retired
    model. The slide deck still needs to be updated by the team.
11. Under-18s are not covered (no minors in the adult PATH files).
