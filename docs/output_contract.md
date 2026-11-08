# Output contract

Runtime entry point: `path_project.outputs.load_engine(workspace).output(answers, eligibility, wave=7)`. Loading verifies immutable output/model/category fingerprints. Probability uses the actual stage 8 calibrated wrapper. The context wave selects source wording/units only; it is not a model predictor or time horizon.

| Field | Meaning |
|---|---|
| `status` | scored, insufficient_input, eligibility_unconfirmed or outside_cohort |
| `probability` | Unrounded calibrated probability in [0,1]; null if suppressed; not personal confidence |
| `endpoint` | Past-30-day cigarette smoking reported at the next scheduled PATH survey |
| `prediction_interval` | Next scheduled interview; unknown individual elapsed time and varying study intervals |
| `category` | Lower/moderate/higher estimated risk, or null; project-defined relative score groups, not medical cutoffs |
| `category_thresholds` | Full-precision calibrated-score cuts and inclusive boundaries; category computed before rounding |
| `contributing_factors` | Four selected questions, readable supplied/missing answers and exact signed calibrated-probability SHAP attributions; empty if suppressed |
| `input_completeness` | Number supplied/expected, missing feature names and distinct reasons; input count is not a confidence estimate |
| `model_version` | Selected model ID, unchanged artifact SHA-256, stage 8 signature and frozen output version |
| `limitations` | Category-development status, pending external/final-test validity, missingness, no causal/personal-confidence/national claims and unsupported timing |
| `explanation` | For scored responses: probability scale, named 64-person tuning model-output reference, additivity residual and noncausal interpretation |
| `suppression_reason` | For withheld responses: why no probability/category/explanation is issued |

Eligibility keys: adult=Yes, established_history=Yes, current_smoking=Not at all, past30_use=No. Exact question text/options come from `configs/app_questions.json`. Unknown gates suppress scoring; outside-cohort responses also suppress. Accepted answer features are age_band, education_level, employment_status, last_cigarette_recency_days only. Categories use documented numeric response codes; recency uses {number, unit}; explicit missing options preserve their reasons. Do not feed a fabricated historical value or an identifier to this API.

The lower cut is inclusive for lower; the upper cut is inclusive for moderate; higher requires p greater than the upper cut. Unrounded probability controls the category. Cuts are frozen in `configs/risk_categories_v1.json` and cannot be reselected on final-test outcomes. The prior binary classifier threshold is a different decision rule, even when its numerical value happens to coincide with a category cut.

Exact SHAP is on the calibrated wrapper probability. Sum of contributions plus reference model probability reconstructs the displayed score. Contributions are not log-odds, confidence, causes or predictions of intervention effects. The reference is a mean model output over a named 64-person tuning background, not a study outcome rate. Development observed outcome rates are reported only with their named source cohort, interval/person denominators and weighting in `model_outputs.md`.

No timing estimates are included. Requests for an elapsed horizon or estimated relapse date raise a clear unsupported-output error under decision C. Suppressed outputs use null probability/category and an empty factor list, never a placeholder risk of zero. The two-observed-input minimum is an application completeness rule without a validated accuracy guarantee. No clinical recommendation follows from the category.
