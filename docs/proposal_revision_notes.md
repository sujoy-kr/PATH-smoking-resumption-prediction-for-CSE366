# Proposal revision notes

These are suggested changes to `Smoking_Relapse_Predictor_Presentation.pptx`. The original 14-slide PPTX is unchanged. Slide titles below refer to the original proposal; verify layout when separately authorized to edit it. Use [the final report](final_project_report.md) for replacement figures and references.

| Original issue | Concrete replacement |
|---|---|
| Subtitle promises time-to-relapse while methods are binary classifiers | Retitle “Explainable Prediction of Next-Survey Cigarette Smoking Among Former Smokers Using PATH.” State that the outcome is past-30-day smoking reported at the next scheduled interview, conditional on a valid observed outcome. |
| Relapse, any interval smoking and persistent relapse used interchangeably | Say “next-survey past-30-day smoking status.” Temporary episodes outside the observation window can be missed, and one positive window does not establish persistence. |
| Implied annual prediction horizon | Remove “12-month,” one-/two-/three-year risk and estimated relapse-date claims. Intervals vary, individual follow-up clocks are unavailable and timing decision C omits survival modeling. Quit history is not future event time. |
| Local baseline described as 45,971 | Identify 32,320 local Wave 1 adult records; the larger number includes youth. Do not sum wave samples as unique people. Show the actual pairwise cohort flow, not an all-eight-wave intersection. |
| Around 85% relapse within 6–12 months asserted without a matched denominator | Delete as a project premise. Mark the original claim **unverified for this cohort**; restore only with a checked primary study specifying abstinence definition, population, endpoint and elapsed follow-up. Our 10.30% is next-survey status among 1,243 held-out observed-follow-up people, not a universal relapse rate. |
| Seven-percent cessation cited as our relapse prevalence | Do not transfer a quitting fraction among current smokers to smoking resumption among former smokers. Cohorts and targets differ. |
| “No existing PATH relapse machine-learning work” | Replace with an explicit citation to the required PATH relapse paper, [reference 1](final_project_report.md#references-and-evidence). Our contribution is local reproducibility, strict participant/later-wave evaluation, compact inputs and transparent explanation, not first-ever novelty. |
| Generic “72% accuracy” for the required cessation paper | Use “72% balanced accuracy and ROC-AUC 0.76 for its reported best model,” citing the full-text Discussion in [reference 2](final_project_report.md#references-and-evidence). It concerns cessation; it is not our outcome or a directly comparable benchmark. |
| Fixed target ROC-AUC >0.80 or guaranteed ensemble superiority | Replace targets with hypotheses evaluated empirically. Report our selected calibrated test ROC-AUC 0.7392, AP 0.2447 and Brier 0.0885 with saved confidence intervals. Several logistic baselines have higher test AP; retain that finding. |
| MICE/SMOTE described as already implemented | State what actually ran: within-fold median/missing-indicator and categorical handling; unweighted versus training-only class weights; no class resampling. Do not claim an unrun imputation/sampling experiment succeeded. |
| Model selected or thresholds optimized on a generic “test split” | Show participant-disjoint tuning folds, separate calibration/threshold groups and held-out-person Wave 7→8 test. Freeze all choices before the single final evaluation. |
| SHAP “risk factors” presented as causes or prevention effects | Describe model contributions relative to a fixed background on the calibrated probability scale. They do not establish that changing a factor changes an outcome. |
| Confident individual prediction or medical cutoff language | Replace with “research estimate” and project-defined relative categories. No invented personal confidence percentage or treatment instruction. |
| PATH study design used as proof of our model's national representativeness | Explain that matching survey-weight/design analysis was not implemented. Results are unweighted local observed-follow-up research; non-U.S., present-day app-user and clinical validity are unestablished. |
| Literature year/details treated as settled from a title | Use verified bibliography/links in the final report and [verification record](../reports/literature_verification.json). The relapse paper has different online/issue years and an unresolved abstract timing inconsistency; do not copy its horizon as fact for this project. |

## Replacement methods paragraph

We harmonized eight local adult PATH waves using documented cohort/response definitions and adjacent interview pairs. Baseline former established smokers reporting no past-30-day cigarette use enter the eligible ledger. Only valid observed next-survey smoking responses receive binary labels. Participants are separated before any learned preprocessing or model decisions. Five grouped development folds compare prevalence-only, logistic, Random Forest and XGBoost candidates; separate development participants support sigmoid calibration and thresholds. The selected four-input calibrated XGBoost is evaluated once on the held-out-person Wave 7→8 test. Exact SHAP explains that same probability. No elapsed-time endpoint is supported.

## Replacement results and conclusion

Use the saved final confusion matrix, calibration figure and model-comparison table, with cohort denominators and uncertainty. Explicitly show calibration worsening test Brier from 0.0851 raw to 0.0885 calibrated. Do not claim every complexity increase helped. Conclude that the course project provides an auditable workflow and research demo with limited probability transfer, rather than a clinically deployable relapse-prevention system. Place speculative benefits on a clearly labeled future-work slide. Any new model needs honest independent evaluation after test exposure.

Do not alter the original presentation, remove weak findings, invent collection/event dates, or introduce unverified references while preparing revisions.
