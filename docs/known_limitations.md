# Known limitations

The v2.2 model resolves the v2.1 design and logic flaws (see the table in
[longitudinal_v2_2.md](longitudinal_v2_2.md)). What remains is inherent to the
data or the question:

1. Interview dates are not in the public-use files; wave-window midpoints are used.
2. Returns that began and ended between interviews are invisible.
3. Attrition after the first follow-up interview may be informative.
4. Evaluation under interval censoring is partly identified: observed risk is a range.
5. Explanations assume independent inputs.
6. The 60-month mean estimate is 0.3 points above its observed-risk upper bound.
7. Sample is unweighted, U.S.-only; not clinical advice; no validated personal confidence.
8. Hashes in the manifest detect accidental corruption only. The model is plain
   JSON, so loading it cannot execute code.
9. The retired v2.1 pickle remains in git history (it embedded 16 survey-derived
   baseline rows). Rewrite history if your data-use terms require removal.
10. v1 (next-survey) documents, scripts and the Oct-10 PPTX describe a retired
    model. The slide deck still needs to be updated by the team.
