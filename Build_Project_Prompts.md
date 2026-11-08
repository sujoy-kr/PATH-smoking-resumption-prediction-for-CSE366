# Prompts to Build the Smoking Resumption Prediction Project

## How to use this file

Open the project folder in a coding AI that can read files, run code, and edit the project. Give it the **master instructions** first, followed by **one numbered prompt at a time**, in order. Let it finish and review the result before sending the next prompt.

The prompts ask the AI to build working software, not just explain what you should build. You do not need to paste the entire guide at once. If you start a new AI conversation, paste the master instructions again and tell it which prompt to continue from.

Your existing inputs are:

- `Smoking_Relapse_Predictor_Presentation.pptx`: unfinished proposal.
- `PATH/DS1001` through `PATH/DS8001`: adult survey data and documentation.
- `PATH/TSV`: additional TSV copies and an existing participant-filtering script.
- `Project_Analysis_and_Implementation_Plan.md`: initial analysis and recommendations.
- `.analysis/cohort_counts.json` and `.analysis/cohort.cjs`: preliminary counts and their calculation.

The initial analysis is a starting point, not a substitute for checking the codebooks. None of the preliminary counts are model-performance results.

## What you are building

A research application where someone answers a manageable set of questions and receives:

1. An estimated probability of the defined smoking outcome.
2. A lower, moderate, or higher risk category based on documented thresholds.
3. The main factors influencing the model's estimate.
4. Timing estimates only if the data and evaluation support them.

The core outcome is **reporting cigarette smoking at the next survey after reporting abstinence at the starting survey**. This does not prove continuous abstinence or capture every smoking episode between surveys.

The app is a course-project research demonstration. It must not present its output as a diagnosis, certainty about an individual's future, or a clinically validated treatment recommendation.

---

## Master instructions — paste these before Prompt 1

```text
You are my coding collaborator. Build a complete, reproducible CSE366 AI course project in the current workspace using the local PATH data and project proposal.

Read any applicable AGENTS.md instructions. Read Project_Analysis_and_Implementation_Plan.md, but verify its assumptions against the actual data and codebooks. Preserve the original dataset, proposal, and existing analysis files. Do not overwrite them or edit raw survey files.

Build working code and run appropriate checks at each stage. Make reasonable implementation decisions without repeatedly asking for confirmation. Ask only when missing information prevents correct work. If a dependency, internet access, data field, or permission is unavailable, explain the concrete limitation and continue independent work where possible. Never fabricate data, performance, dates, citations, trained models, or successful checks.

Use Python for the data and modeling pipeline and Streamlit for the demonstration unless inspection reveals a material reason to choose otherwise. Prefer a modest, understandable solution that we can explain in a course presentation. Use CPU-friendly models and avoid unnecessary services, API keys, paid tools, and external databases.

Maintain PROJECT_STATUS.md throughout the work. Record completed stages, exact commands run, important decisions, limitations, output paths, and the next step. A new AI conversation should be able to continue from that file. Keep configuration in files rather than scattered constants. Use fixed random seeds and save dependency versions.

Do not put raw PATH data, PERSONIDs, participant-level derived data, or trained artifacts into version control by default. Do not publish, upload, deploy, commit, or push anything unless I explicitly request it. Do not send messages to other people.

Scientific rules:
- Define the cohort, prediction time, outcome, and follow-up meaning before training.
- Distinguish next-survey smoking status from any smoking resumption during an interval and from persistent relapse.
- Do not assume every pair of PATH waves is exactly one year apart.
- Do not use the all-eight-waves participant intersection as the default cohort.
- Verify variable meanings, revised variables, units, missing codes, and skip patterns from documentation.
- Use PERSONID for joining and grouping, never as a predictor.
- Only use information available at prediction time as model inputs.
- Split participants before learning preprocessing, selecting features, resampling, tuning, calibration, or threshold selection.
- Preserve the original prevalence in evaluation data. Keep final-test data untouched until the evaluation stage.
- Never fabricate exact relapse dates from survey dates or use time since quitting as time until relapse.
- SHAP explains model behavior; it does not prove causes or intervention effects.
- Probability estimates and risk categories need validation. Do not invent a personal confidence percentage.
- Do not claim national representativeness without matching survey weights and design handling.
- Do not promise ROC-AUC above 0.80 or any other result.

Follow the numbered prompt I send. At each stage, report what you built, how you verified it, any remaining limitation, and the next stage. Do not silently skip required work.
```

---

## Prompt 1 — Inspect the workspace and set up the project

```text
Implement stage 1: inspect the workspace and establish the project structure.

Read the proposal's contents and the existing analysis. Inventory the eight adult data files, codebooks, questionnaires, existing scripts, and any weights or linkage files. Check for duplicate dataset copies so we do not process the same wave twice. Discover the available Python interpreter and tools rather than assuming that the command `python` works. Use an isolated environment inside the workspace if supported.

Create a clear structure such as:
- src/ for reusable code
- scripts/ for executable stages
- configs/ for configuration
- docs/ for decisions and documentation
- tests/ for meaningful correctness checks
- data/processed/ for generated analysis data
- artifacts/ for fitted pipelines and metadata
- reports/ for aggregate tables and figures
- app/ for the Streamlit app

Create .gitignore, an initial README.md, PROJECT_STATUS.md, and dependency configuration. Keep sensitive participant-level outputs ignored. Do not initialize or change a Git repository unnecessarily.

Write docs/data_inventory.md with the verified inputs, local tools, and any missing files. Do not train any model yet.

Completion check: show the intended commands, confirm which Python executable will be used, and verify that original input files remain unchanged.
```

## Prompt 2 — Define the prediction question and check timing feasibility

```text
Implement stage 2: decide exactly what the model can predict.

Inspect relevant codebook and questionnaire sections across waves. Document the exact local file, variable, page/section, labels, and eligibility rules supporting each decision.

Define the core task:
Among former established cigarette smokers reporting no cigarette use in the past 30 days at a starting interview, predict past-30-day cigarette smoking at the next interview with an observed valid outcome.

Check whether this definition is consistent enough across all eight waves. If not, explain and configure the defensible subset or harmonization rules. Define secondary analyses, such as recent quitters and current established smoking at follow-up, separately.

Investigate timing support:
- Are individual interview dates, interview intervals, or only general wave collection dates available?
- Are actual smoking resumption dates or durations reported?
- Do retrospective questions distinguish any resumption from current smoking status?
- How are participants without an observed event and participants lost to follow-up handled?
- What events can be missed between interviews?

Create docs/prediction_specification.md and docs/timing_feasibility.md. Record one of these timing decisions with evidence:
A. A defensible time-to-event endpoint and usable time information are available, supporting an appropriately censored analysis.
B. Only time to first observed smoking status can be modeled, requiring that exact wording and an explanation of observation gaps.
C. Timing estimates are unsupported; retain next-survey classification and explain the prediction interval honestly.

Do not estimate one-, two-, or three-year risks from general survey-year labels alone. Do not substitute interview date for exact relapse date. If a survival endpoint requires assumptions about unobserved events or persistence, state and assess those assumptions explicitly.

Completion check: the specification must state who enters the cohort, what inputs are allowed, when the prediction occurs, what outcome is measured, and what the app may claim.
```

## Prompt 3 — Build the feature dictionary and wave mappings

```text
Implement stage 3: create a documented, machine-readable feature mapping.

Select an initial compact set of approximately 20–40 candidate predictors with a realistic path to answering them in a demonstration app. Cover demographics, quit history, prior smoking intensity, other tobacco use, household smoking, and selected health or behavioral responses where available.

For every feature record:
- Common name and understandable description.
- Wave-specific source columns.
- Exact response labels, valid ranges, and units.
- Missing and structural-skip rules.
- Whether the question applies to former smokers.
- Any historical-wave dependency.
- Whether a user could reasonably supply the value in the app.
- Source evidence from the local documentation.

Verify former-established, current-established, and past-30-day smoking indicators. Handle revised Wave 2 and Wave 3 variables explicitly. Investigate the absence of the same derived cigarette days-since-quitting field in Wave 2; use raw number/unit questions or justified historical reconstruction only when documented. Do not interpret missing duration as zero.

Save configs/feature_mapping.yaml or JSON and docs/feature_dictionary.csv. Separate cohort fields, outcome fields, identifiers, design/weight fields, and candidate predictors. Build a validation command checking configured columns against the actual TSV headers.

Do not select predictors using the final-test outcomes. Do not include future-wave answers, identifiers, or administrative fields as predictors.

Completion check: all configured mappings resolve to real columns and every included feature has a documented meaning and prediction-time availability.
```

## Prompt 4 — Build the reproducible cohort pipeline

```text
Implement stage 4: load, harmonize, join, and label the analysis cohort.

Read only needed TSV columns and preserve PERSONID as a stable string. Process one canonical copy of each wave. Validate uniqueness of PERSONID within each wave and fail clearly on unexpected duplicate joins.

Construct one row per eligible person and adjacent-wave prediction interval according to docs/prediction_specification.md. Do not require participation in all eight waves. Retain identifiers only for internal joining and grouping. Treat missing follow-up or unknown outcomes as unobserved, not as negative outcomes.

Apply documented response recoding, unit conversions, and structural-skip handling. Keep no answer, not applicable, and valid zero distinguishable when their meanings differ. Derive historical predictors only from information available before or at the prediction interview.

Save the processed cohort in an efficient local format, its schema, and aggregate cohort-flow tables for each interval. Record exclusions, missing outcomes, positive prevalence, unique people, repeated records, and feature availability. Compare against .analysis/cohort_counts.json as a diagnostic, not as numbers the code must force itself to reproduce. Explain differences.

Add meaningful tests for label coding, missing outcomes, ID joins, unit conversion, skip handling, and future-information exclusion. Include a tiny synthetic test fixture, clearly separate from real analysis data.

Completion check: run the pipeline successfully and show aggregate counts without exposing PERSONIDs or individual records in reports.
```

## Prompt 5 — Create and lock the evaluation splits

```text
Implement stage 5: create the evaluation protocol before model development.

Use participant-grouped development folds so the same PERSONID never crosses training and validation boundaries. Reserve an untouched later-wave test, preferably eligible Wave 7 to Wave 8 records from a held-out participant group whose earlier records are excluded from all model fitting.

Use a documented deterministic assignment rule that does not repeatedly inspect final-test outcomes to find a favorable split. Check whether development folds have enough positive cases. If the proposed test is too small, choose and explain an alternative protocol before model development rather than weakening it silently.

Save split membership locally in ignored files, configuration, and docs/evaluation_protocol.md. Define which development data will support hyperparameter tuning, probability calibration, risk thresholds, and model selection. Keep test features and outcomes out of these decisions.

Implement assertions for participant separation, temporal restrictions, feature exclusion, and the pipeline's training boundaries. Explain how repeated person-wave records are handled in metrics and uncertainty estimates. Document that class weighting and survey weighting serve different purposes.

Completion check: tests prove that no held-out participant or future outcome is used in fitting. Do not report final-test model performance yet.
```

## Prompt 6 — Explore the development data and finalize app inputs

```text
Implement stage 6: explore only the development data and finalize a practical predictor set.

Create aggregate summaries and readable figures showing outcome prevalence by interval, missingness, quit-duration distributions, relevant feature distributions, and repeated-observation counts. Check for implausible values and cohort-dependent question availability.

Compare observed follow-up availability across baseline characteristics to describe possible attrition bias. Avoid causal conclusions and unsupported national estimates.

Finalize a compact app-compatible feature set. Also define a minimal comparison model using basic demographics and quit duration where supported. If richer historical fields cannot realistically be provided by a new app user, keep a distinct research model and app model; do not feed invented historical answers into the research model.

Update the mapping, dictionary, and prediction specification with the final input set. If a feature change affects cohort construction, regenerate data and rerun integrity checks without changing held-out participant assignment.

Completion check: produce reports/development_data_summary.md and a list of exact app questions, response options, and missing-answer behavior. Keep final-test data out of this exploration.
```

## Prompt 7 — Train baselines and establish correct probability handling

```text
Implement stage 7: train the baseline models using the locked development protocol.

Build reusable preprocessing-and-model pipelines. Fit imputers, encoders, scalers, and any learned transformations within training folds only. Handle unseen categories safely and preserve feature names for interpretation.

Train:
1. A training-prevalence-only baseline.
2. Logistic regression using the minimal feature set.
3. Logistic regression using the full selected feature set.

Evaluate using grouped development validation. Report average precision with prevalence context, ROC-AUC, Brier score, calibration, and threshold metrics where appropriate. State exactly which PR metric is calculated; do not interchange average precision and trapezoidal PR-AUC without explanation.

Compare unweighted and class-weighted fitting where justified. Explain that weighting can distort raw probabilities. Fit any needed calibration only through the reserved development procedure, never on final-test data or predictions from examples used to fit the same estimator.

Save development results and pipeline metadata. Test schema validation and prediction consistency. Do not inspect final-test performance.

Completion check: baseline predictions and development metrics come from executed code, and the prevalence-only baseline uses training prevalence rather than evaluation labels.
```

## Prompt 8 — Compare Random Forest and XGBoost

```text
Implement stage 8: compare tree models with the baselines.

Train Random Forest and XGBoost with a modest reproducible hyperparameter search using the same grouped development protocol. Use CPU-friendly settings and record search spaces, seeds, and runtimes. If XGBoost cannot be installed, document the limitation and use an available appropriate alternative rather than pretending XGBoost ran.

Start with no resampling and appropriate class-weight options. Add an imbalance-handling experiment only if justified. If testing oversampling, keep it inside training folds, use a method compatible with the categorical features, and retain natural prevalence in evaluation data.

Compare all candidates fairly using the same development splits and a documented selection rule that considers discrimination and probability quality. Include the minimal-versus-full-feature comparison. Fit calibration using the locked development procedure if needed.

Save aggregate development results, model configuration, fitted candidate pipelines as appropriate, and docs/model_selection.md. Select the model without using final-test results. Do not promise any target score.

Completion check: run the comparisons, explain the selected candidate and tradeoffs, and keep the final test untouched.
```

## Prompt 9 — Implement timing only if the evidence supports it

```text
Implement stage 9 according to docs/timing_feasibility.md.

First confirm the timing decision against the implemented cohort and available fields. This stage must not be marked successful merely because code produces a survival curve.

If timing is unsupported:
- Record a clear decision in docs/timing_decision.md.
- Keep the working next-survey classifier.
- Add app metadata specifying that elapsed-time estimates are unavailable.
- Do not create placeholder annual probabilities or an estimated relapse date.

If a defensible timing analysis is supported:
- Define the time origin, event, observation windows, censoring, entry rules, and prediction-time features precisely.
- Preserve uncertain event times as intervals when appropriate. Do not substitute interval endpoints or midpoints as exact dates without a justified sensitivity analysis.
- Choose a method whose implementation actually supports the required censoring and observation structure. A generic right-censored model is not automatically suitable for interval-censored data.
- Reuse participant separation and development-only model selection. Handle event-free follow-up and attrition according to the specification.
- Evaluate time-based probabilities using methods appropriate to censoring and observed follow-up. Check whether each proposed horizon has sufficient support.
- Output only supported horizons. Do not extrapolate one-year probabilities from next-survey classification scores.
- Explain whether the endpoint is actual smoking resumption or first observed smoking status. Never treat these as interchangeable.

Keep timing as a separate, clearly described model if its target differs from the classifier. Record verified results or the reason timing was omitted. Do not compromise the core project to force this extension.
```

## Prompt 10 — Finalize risk categories and explanations

```text
Implement stage 10: make the selected model's outputs understandable.

Use development data to define and freeze lower, moderate, and higher estimated-risk thresholds. State that these are project-defined categories, not established medical cutoffs. Explain the selection rule and report category sizes and observed outcomes in development data. Avoid arbitrary 0–33%, 34–66%, and 67–100% ranges.

Implement global and local explanations appropriate to the selected model, using SHAP where supported. Map transformed features back to understandable questions and categories. Check the output scale: log-odds contributions must not be described as percentage-point changes.

Ensure explanations refer to the actual model and probability shown. If the displayed probability comes from a calibrated wrapper while SHAP explains its underlying estimator, disclose that distinction and validate the explanation path. Do not silently explain a different candidate model.

Create the output contract: probability, endpoint, prediction interval, category, category thresholds, contributing factors, input completeness, model version, and limitations. Include timing only when stage 9 supports it. Any study-group reference rate must have a named cohort and denominator.

Do not invent personal confidence percentages or claim that changing a factor would cause a reduction in risk.

Completion check: explanations work for several valid input profiles, categories agree with the displayed score, and missing answers produce honest behavior.
```

## Prompt 11 — Run the reserved final evaluation

```text
Implement stage 11: evaluate the frozen model on the reserved test set.

Before accessing test outcomes, save the selected feature schema, fitted pipeline/calibrator, hyperparameters, risk thresholds, timing decision, and evaluation code. Record an artifact hash and model version.

Run the final evaluation using the locked protocol. Report sample size, unique people, positive prevalence, average precision, ROC-AUC, Brier score, calibration plot, confusion matrix, precision, recall, specificity, and risk-category outcome rates. Estimate uncertainty by resampling participants when observations repeat, and handle bootstrap samples with undefined metrics explicitly.

Compare against the frozen baseline models. If supported and sufficiently sized, report recent-versus-long-term-quitter performance and selected demographic subgroup results, including counts and uncertainty. Do not overinterpret small groups. Do not call a model nationally representative based only on PATH's study design.

For any supported timing model, report separate endpoint-appropriate metrics and supported horizons rather than mixing them with classifier metrics.

Save reports/final_evaluation.md and aggregate figures/tables. Do not tune in response to final-test performance. If an implementation bug requires a fix, document the test exposure and its implications; do not conceal repeated evaluation.

Completion check: all reported values are traceable to executed code and frozen artifacts. A weak result is a valid result and must be reported honestly.
```

## Prompt 12 — Build the Streamlit application

```text
Implement stage 12: build a polished, understandable Streamlit research demonstration around the frozen app-compatible model.

Use the exact schema and preprocessing from training. Include a short explanation of the task and an input form using documented question wording, labels, units, and valid options. Support unknown answers only where the trained pipeline supports them. Validate inputs and identify unsupported profiles rather than silently forcing a prediction.

After submission show:
1. Estimated percentage with its exact endpoint and timeframe.
2. Lower/moderate/higher estimated risk using the frozen thresholds.
3. Top contributing factors, with plain descriptions and correct direction/scale.
4. A summary of submitted answers and information completeness.
5. A short model-performance section using actual final-test results.
6. Optional study-group comparison with a clearly labeled source cohort.
7. Timing estimates only if stage 9 produced a validated timing model and supported horizons. Otherwise explain that the model predicts next-survey status and cannot estimate an exact return-to-smoking time.

Avoid presenting next-survey probability as an annual risk. Do not label an individual as certain to relapse, provide unsupported treatment instructions, or invent confidence scores. Explain that PATH represents a U.S. survey population and performance for other populations is unvalidated.

Keep runtime prediction local. Do not collect names, contact details, or PERSONIDs. Do not persist user answers by default. Cache model loading, not private answer histories. Use clearly labeled demonstration presets rather than real participant profiles.

Completion check: launch the app, verify the form and results, and confirm that the displayed probability, category, explanation, and model version all correspond to the same frozen prediction path.
```

## Prompt 13 — Test the full application and reproducibility

```text
Implement stage 13: verify the whole project and fix concrete defects.

Run appropriate automated checks for:
- Cohort labels, missing outcomes, joins, and unit conversions.
- Participant separation and prediction-time feature restrictions.
- Training-only preprocessing and resampling.
- Saved-model loading and probability consistency before/after serialization.
- App-schema consistency and category boundaries.
- Missing/unknown answers, unseen categories, and invalid inputs.
- Explanation handling and timing-output eligibility.

Run an end-to-end smoke test using clearly synthetic inputs and a real trained artifact. Confirm the app can start with the documented command. Inspect the UI if a browser is available; otherwise explicitly state the visual verification limitation.

Verify the documented build order from a clean generated-output directory or a safe isolated workspace. Do not delete original files, repeat expensive model searches unnecessarily, or rerun final-test evaluation without a justified change. Make commands work from the project root and handle file paths containing spaces.

Create reports/verification.md with executed checks and any unresolved limitations. Confirm no raw or participant-level data, local secrets, or private inputs are included in tracked deliverables.

Completion check: resolve material defects and distinguish tests actually run from checks that could not run.
```

## Prompt 14 — Write the report and proposal corrections

```text
Implement stage 14: write clear documentation for students and reviewers using actual results.

Finish README.md with setup, data placement, exact commands, pipeline order, app startup, expected outputs, and troubleshooting. Provide a short quick-start path for launching the already-trained app and a separate path for rebuilding the research pipeline.

Create docs/final_project_report.md covering the research question, related work, local dataset, cohort flow, feature definitions, missingness, leakage prevention, development protocol, models, final results, calibration, explanations, timing decision, limitations, and conclusion. Include traceable citations and aggregate tables/figures. Use plain language and distinguish measured findings from hypotheses.

Create docs/proposal_revision_notes.md with concrete corrections for the unfinished proposal. Address the mismatch between time-to-relapse and binary classification, incorrect or ambiguous metrics, unverified relapse-rate statements, promised performance, and clinical/national claims.

Verify primary literature where internet access is available. Include the existing PATH relapse paper linked at https://pubmed.ncbi.nlm.nih.gov/40117048/ and the cessation paper at https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0286883 . Do not claim that no PATH relapse models exist. Check exact publication details and metrics before citing them. If verification is unavailable, mark the reference for verification instead of inventing details.

Write docs/presentation_outline.md and docs/viva_questions.md. Explain what the inputs and outputs mean, why accuracy alone is misleading, why people are separated across splits, what SHAP can explain, and why timing may be limited.

Do not alter the original PPTX unless separately requested.

Completion check: every performance claim matches the saved evaluation, all limitations remain visible, and a teammate can understand and run the project from the documentation.
```

## Prompt 15 — Final audit and handoff

```text
Implement stage 15: audit the completed project against the original objective.

Read PROJECT_STATUS.md and verify that stages 1–14 are complete or have explicitly justified omissions. Confirm that the deliverable includes working cohort code, feature mapping, frozen evaluation splits, trained app-compatible model, real metrics, explanation code, Streamlit app, tests, and documentation.

Check that unsupported timing outputs are absent and that supported timing claims match their actual endpoint. Confirm the app never confuses next-survey smoking status with an exact date or a guaranteed event. Verify final file links and startup commands.

Create PROJECT_HANDOFF.md containing:
- What the project actually predicts.
- Final inputs and outputs.
- Selected model and actual evaluation results.
- Whether timing prediction was implemented and why.
- Exact command to start the app.
- Exact commands to reproduce each pipeline stage.
- Where artifacts, reports, and tests are located.
- Known limitations and sensible future work.

Update PROJECT_STATUS.md with the final state. Do not mark missing trained artifacts, unrun evaluations, or broken startup commands as complete. Do not publish, deploy, commit, or push.

Give me a concise final response with the startup command, important file links, actual results, and any remaining limitation.
```

---

## Recovery prompt — use if a conversation ends midway

```text
Continue this project from its existing state. Read the master instructions in Build_Project_Prompts.md, applicable AGENTS.md files, PROJECT_STATUS.md, and the relevant configuration and artifacts. Verify what is already complete rather than rebuilding everything. Resume the next incomplete numbered stage. Preserve locked splits and do not reopen final-test evaluation for tuning. Report the stage you are resuming and continue implementing it.
```

## Optional prompt — revise the actual PowerPoint after the project is complete

```text
Using the final project report, actual evaluation results, and proposal revision notes, create an updated copy of Smoking_Relapse_Predictor_Presentation.pptx. Preserve the original. Follow the applicable presentation skill and inspect the resulting slides. Correct the title, research gap, cohort description, methods, metrics, timing claims, and references to match the implemented project. Replace expected results with actual results. Keep the presentation understandable for a CSE366 audience and do not invent performance or clinical impact. Save the revised deck under a new filename and provide its path.
```

## What success looks like

You can run one documented command to open the app, answer the supported questions, and obtain a real model prediction with an honest explanation. You can also explain where its training examples came from, how it was tested, what its measured performance is, and what it cannot predict. Timing is an optional extension whose inclusion depends on evidence, not a condition to fake or force.
