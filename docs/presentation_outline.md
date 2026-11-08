# Presentation outline

A 10–12 minute presentation plus a short local demonstration. Keep the original proposal PPTX unchanged; this is an outline for a future revised deck. Use only aggregate figures and fictional app presets.

| Slide | Plain-language message | Evidence / visual |
|---|---|---|
| 1 · Question | Can baseline survey answers identify former smokers who will report smoking in the next interview's 30-day window? | State target, eligible adults and variable interview interval; avoid “annual relapse.” |
| 2 · What already exists | PATH relapse and cessation ML studies exist; this course project focuses on reproducibility and strict evaluation. | Verified references in the final report; distinguish target populations and metrics. |
| 3 · Data and cohort | Eight adult waves, one canonical copy each, adjacent pairs rather than the all-wave intersection. | Final report cohort-flow table: eligible → unobserved versus labeled; 30,890 labeled intervals are 9,597 people. |
| 4 · What the model sees | Selected model uses age band, education, employment and approximate historical last-cigarette recency. | Exact question labels; explain 25 initial candidates, eleven-input comparison and selected four-input model. |
| 5 · Missingness matters | A skipped duration is not zero; persistent former smokers often were not asked. | Development missingness figure. Fully answered app users can differ from survey respondents. |
| 6 · Prevent leakage | One person cannot appear on both sides of a fitting/validation boundary. | Simple diagram: tuning folds → separate calibration → separate threshold → held-out-person Wave 7→8 test. All test people's earlier records excluded. |
| 7 · Models and decision rule | Compare training-prevalence baseline, logistic and modest CPU tree searches. | Raw development AP table; explain participant-equal weighting and that selection occurred before test access. |
| 8 · Honest final result | 1,243 people, 128 positives; selected AP 0.2447, ROC-AUC 0.7392, Brier 0.0885. | Final metric CIs/confusion matrix. Accuracy alone rewards predicting No for everyone. |
| 9 · Where it falls short | Mean predicted 13.90% exceeds 10.30% observed; several logistic baselines have higher AP. | Calibration and frozen baseline table. No test-driven model replacement. |
| 10 · Explain an estimate | SHAP attributions reconstruct the actual calibrated score, with clear scale/direction. | Fictional preset only; show probability, frozen category, factors, submitted answers/completeness and model hash. Contributions are not causes. |
| 11 · Time and scope | No exact return-to-smoking time, annual probability or continuous-abstinence claim. | Timing decision C; absent individual clock/event history. U.S. source, unweighted design, no clinical or other-population validity claim. |
| 12 · What we delivered | Working local code/app and auditable outputs are the contribution; weak results are valid. | README quick start, verification report, reproducible hashes and remaining limitations. |

## Demonstration sequence

1. Run `.venv/bin/python -m streamlit run app/streamlit_app.py` from the existing verified project root. Open the localhost address; do not deploy or enter participant information.
2. Submit Blank form. Explain why the cohort warning replaces a personal estimate; the always-visible study-performance table is not a prediction.
3. Select the fictional recent-last-use preset and submit. Read the endpoint and interval before the percentage/category.
4. Open the identity/explanation expander. Show that the version/hash belongs to the selected frozen calibrated model; contributions plus reference model output reconstruct its score.
5. Submit the fictional longer-history and partial/unknown presets. Explain missing handling and completeness without calling it confidence.
6. Finish on the actual final-test limitations and scope statement. Do not describe changing an answer as a treatment recommendation.

Browser launch and the three fictional submissions were user-confirmed; automated tests independently verify the prediction path. A live run depends on the retained private artifact bundle and matching environment. If a presentation machine lacks it, use the saved aggregate figures and clearly label the absence of a live run. Never fabricate a successful demo or regenerate the exposed final test for presentation screenshots.

## Before presenting

Use [the final report](final_project_report.md) for numerical values and [viva questions](viva_questions.md) for defense. Label development and final metrics separately; show the CIs and denominators. Avoid claiming statistical/clinical superiority from small differences. Rehearse explaining why the selected model stays fixed even when a simpler baseline performs better on the final test.
