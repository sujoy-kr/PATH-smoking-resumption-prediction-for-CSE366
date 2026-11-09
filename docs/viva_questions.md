> **Historical (v1 next-survey model).** Not the current v2.1 consecutive-wave app; see docs/faculty_guide.md and docs/known_limitations.md.

# Viva questions and short answers

## What exactly is predicted?

Past-30-day cigarette smoking reported at the next scheduled interview, among eligible adult former established smokers with no past-30-day use at baseline and an observed valid follow-up. It is a survey snapshot, not every smoking episode, persistent relapse or a date.

## When are inputs known?

At the end of the starting interview. The four selected inputs describe baseline age band, education, employment and historical last-cigarette recency. Follow-up answers provide the outcome only. PERSONID joins and groups records; it never enters the model.

## Why not use every person present in all eight waves?

That would select long-term respondents, exclude later entrants and lose eligible adjacent pairs. We need the starting interview and an observed valid next outcome, not participation in every wave.

## Why are 30,890 records not 30,890 people?

A person can contribute multiple adjacent intervals. The labeled cohort contains 9,597 people. Training/validation/test grouping and uncertainty must account for repeated observations.

## What happens to missing follow-up?

The eligible ledger retains it as unobserved. It is not labeled sustained abstinence or a negative outcome. Analysis conditional on observed follow-up may be affected by attrition; descriptive baseline comparisons do not remove that bias.

## Why is accuracy alone misleading?

The final sample has 128 positives among 1,243 people. Predicting No for everyone would look 89.70% accurate while finding no positive cases. Average precision, ROC-AUC, probability losses, calibration and threshold errors reveal different weaknesses.

## Are average precision and PR-AUC interchangeable?

No. We use stepwise average precision matching sklearn `average_precision_score`, not trapezoidal integration of a precision–recall curve. AP should be interpreted alongside positive prevalence and the evaluation weighting.

## What do ROC-AUC, Brier and calibration mean?

ROC-AUC measures ranking across thresholds. Brier is mean squared probability error; lower is better. Calibration asks whether similar predicted probabilities agree with observed frequencies. Good ranking does not guarantee accurate probabilities or clinical usefulness.

## What were the measured final results?

On 1,243 held-out Wave 7→8 people with 128 positive outcomes, selected AP was 0.2447, ROC-AUC 0.7392 and Brier 0.0885. Full CIs, precision/recall/specificity, confusion counts and baselines are in [the final report](final_project_report.md). These are not personal confidence percentages.

## Did the complex model beat every baseline?

No. It was selected using development AP, but several frozen logistic baselines had higher final-test AP. We report that without changing the chosen model. Selecting a new winner using this test would turn it into development data.

## Did calibration help?

It was fitted on separate development participants, which prevents direct fitting leakage. Nevertheless, final-test Brier worsened from 0.0851 raw to 0.0885 calibrated, and the mean calibrated score exceeded observed prevalence. Calibration transfer is empirical, not guaranteed. We did not repair it using test labels.

## Why split people rather than rows?

The same person's answers and histories can recur. A random row split can expose nearly the same individual in fitting and validation, overstating generalization. Five participant-grouped folds and separate calibration/threshold/test participants prevent that overlap; held-out people's earlier records are also excluded.

## Is this a purely time-ordered forecast at every development wave?

No. Internal validation uses held-out people from pooled earlier intervals; training can contain other people's later intervals within that earlier-wave pool. The outer Wave 7→8 test additionally enforces later-wave time and unseen-person restrictions. We state those different targets explicitly.

## Where are preprocessing and resampling fitted?

Median/missing-indicator transformations, categorical handling, encoders and scaling fit inside authorized training folds. Valid unseen categories are handled safely; invalid codes are rejected. No class resampling was used. Class ratios/weights were training-only; Random Forest bagging is training-only model fitting.

## Are class weights, participant weights and survey weights the same?

No. Class weights change the fitting loss under imbalance and may distort raw probabilities. Participant metric weights prevent frequent respondents from dominating the chosen evaluation estimand. Survey weights/design address a population target and sampling/nonresponse. Our first two do not substitute for the third; no national estimates are claimed.

## How was uncertainty estimated?

The final analysis used 1,000 participant-cluster bootstrap draws with seed 366 and percentile 95% intervals. Repeated records move with their person and repeated draws retain their multiplicity. Undefined metrics are recorded explicitly and omitted metric by metric. The test has one row per person, so this reduces to sampling people/rows. CIs do not include all training/selection or survey-design uncertainty.

## Why four questions rather than the full dictionary?

The selected minimal model had the best prespecified development AP and a lower question burden. Eleven app-compatible inputs were compared; 25 initial research candidates were documented. Sparse historical inputs cannot simply be invented for a new user. The four-input result does not prove other information has no value.

## Why is unknown duration not zero?

Zero would mean recent use, while missing can mean refusal, unknown or questionnaire routing. Persistent former smokers were often unasked. We preserve missing reasons and let the trained pipeline handle supported unknowns. A new user's missingness pattern can still differ from PATH's instrument.

## How do lower, moderate and higher categories work?

They use frozen development score tertiles and exact inclusive boundaries, not probability thirds or medical cutoffs. Categories use the unrounded score. Their observed final-test rates and denominators are reported; they are not a guarantee for an individual. A binary threshold tie can be moderate but binary-positive because the two declared boundary rules differ.

## What does SHAP explain here?

Exact SHAP explains the actual sigmoid-calibrated probability shown by the app. The reference model output plus four contributions reconstructs that score. Positive and negative contributions are directions relative to a background mixture; multiplying by 100 gives percentage-point attributions. They are not raw log-odds and not effects of interventions.

## Can a user lower risk by changing a high-contributing answer?

The model does not establish that. Correlation, missingness/routing and unmeasured influences can explain associations. SHAP describes model behavior, not causes, treatment benefit or a counterfactual experiment. We provide no unsupported treatment instructions.

## Why no time-to-relapse or annual risk?

Individual elapsed follow-up and complete first-resumption histories are not available for this implemented cohort. General survey-year labels and last-use history cannot supply them. Temporary events may occur and resolve between interviews. Decision C retains next-survey classification without annual horizons or a relapse date.

## Does PATH make this model nationally representative?

No. Matching survey weights and design handling were not implemented for the pooled target. It is unweighted local research. Performance for Bangladesh, other populations, new app users and clinical decisions remains unvalidated.

## What prior work should be acknowledged?

The verified PATH relapse and cessation papers in [the references](final_project_report.md#references-and-evidence). Their cohorts, available predictors and metrics differ, so we do not turn literature results into promised scores or claim first-ever PATH relapse prediction.

## Can someone reproduce and run it?

Use the existing isolated environment and retained private evidence bundle for the app. The README gives exact startup/setup commands and a separate research build order. Stage 13 verified clean early-stage regeneration and frozen-model replay in a workspace containing spaces. Fresh dependency installation, another OS and a fully repeated expensive search were not claimed. The original-data baseline is preserved, with only the user-confirmed runner edit excepted.

## What should happen if a bug is discovered after test exposure?

Preserve logs, predictions and artifact versions; document the concrete bug, fix and prior exposure. Do not quietly rerun a supposedly untouched final test, retune or conceal weaker results. A substantive changed model needs an honest new evaluation plan and suitable independent data.
