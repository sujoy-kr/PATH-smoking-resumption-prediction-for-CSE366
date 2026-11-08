# Stage 3 feature mapping notes

**Stage 6 final profiles:** the original 25-candidate crosswalk below remains immutable source provenance. Final app/minimal/research membership is now in `configs/feature_mapping_final.json` and [feature_dictionary_final.csv](feature_dictionary_final.csv), with 11 app inputs, four minimal inputs and a separate 25-input research comparison. See [app_questions.md](app_questions.md) and the [tuning-only summary](../reports/development_data_summary.md). No original mapping, response recoding, cohort or held-out assignment changed.

The initial set contains **25 candidate predictors**, selected from local documentation for scientific relevance and a realistic demonstration question. No participant rows, final-test outcomes, correlations, performance scores, feature ranking or learned preprocessing were used to choose them. These are documented candidates, not a promise that all will survive a later training-only coverage/usability review.

`configs/feature_mapping_recipe.json` holds the curated choices and transformations. `scripts/build_feature_mapping.py` enriches it from the canonical local PDF codebooks/questionnaires and TSV headers, writing `configs/feature_mapping.json`, the requested `docs/feature_dictionary.csv`, and `reports/feature_mapping_evidence.json`. All source documents are checked against the unchanged original-file hash manifest. Cached text is reused only when both PDF and text hashes match its sidecar. The build never constructs cohort rows or reads survey answers.

## How to read the dictionary

The JSON is the executable contract. Each named field has a role, description, family, output units/labels, former-smoker applicability, historical-dependency policy, app prompt and an eight-wave mapping. Each available mapping lists **real input columns**, source-time role, transformation, source components and documentation references. Components retain exact source labels, missing-code ranges/labels, questionnaire/algorithm prose, numeric precision, source range-check strength and observed descriptive extrema separately. Supplemental references connect derived inputs to their raw question/routing sections and verify unit conversions.

The CSV has one row per common field per wave: **288 rows covering 36 separated fields**. Nested cells are valid JSON so multiselect sources, unit pairs, missing labels and citations remain machine-readable without inventing extra participant rows. Filter `role=candidate_predictor` for the 200 predictor/wave mappings. Exact file paths, variable section IDs and one-based physical PDF pages are in `source_evidence`; resolve the corresponding evidence keys in the JSON report to see the source excerpts. These are physical viewer pages, not the printed footer numbering.

The five roles are:

- `candidate_predictor`: 25 baseline/current-or-earlier response constructs only.
- `cohort_field`: former-established and past-30-day baseline entry fields, plus current-established baseline QC (not an additional inclusion rule).
- `outcome_field`: primary next-wave past-30-day smoking and secondary next-wave current-established smoking. These fields are explicitly unavailable at prediction time and never enter the feature allowlist.
- `identifier`: PERSONID for joins/grouped splitting and CASEID as administrative metadata. Neither is an input to the model or app.
- `design_weight_field`: PSU, stratum, final person weight and 100 replicate weights where available (waves 1–2). Later waves explicitly list no mapping for these absent fields; no nonexistent weight column is fabricated. No survey-weighted pooled model or national inference is enabled.

The stage 2 prediction contract now links to these 25 documented candidate names. Its scientific task, seven adjacent pairs, cohort, valid label mapping, timing decision C and app-claim restrictions remain unchanged. The candidate allowlist does not select a fitted feature set or authorize any training in stage 3. Wave 8 is mapped for complete documentation, but is follow-up only under the current seven-pair protocol: never pull Wave 8 candidate responses into a 7→8 baseline feature vector.

## Candidate summary

The following examples show the primary source(s) at waves 1 and 8. All eight mappings, exact source labels and full eligibility/routing are in the CSV/JSON.

| Common name | Family | Meaning | Wave 1 input → physical codebook page | Wave 8 input → physical codebook page |
|---|---|---|---|---|
| `age_band` | demographics | Age category at the starting interview. | `R01R_A_AGECAT7` p. 1084 | `R08R_A_AGECAT6` p. 2219 |
| `sex_recorded` | demographics | Male/female sex or gender category as recorded by the survey. | `R01R_A_SEX` p. 1086 | `R08R_A_SEX` p. 2221 |
| `education_level` | demographics | Highest completed education, harmonized to five categories. | `R01R_A_AM0018` p. 1065 | `R08R_A_AM0018_V2` p. 2204 |
| `household_income_band` | demographics | Total household income during the prior 12 months in nominal US dollar bands. | `R01R_A_AM0030` p. 1068 | `R08R_A_AM0030` p. 2208 |
| `employment_status` | demographics | Current paid employment status and weekly hours category. | `R01_AM0014` p. 867 | `R08_AM0014` p. 1579 |
| `last_cigarette_recency_days` | quit_history | Approximate time since completely quitting (Wave 1) or last cigarette (Waves 2–8). | `R01_AC1009_NN` p. 67; `R01_AC1009_UN` p. 68 | `R08_AC1009_NN` p. 17; `R08_AC1009_UN` p. 18 |
| `prior_regular_cigarettes_per_day` | prior_smoking_intensity | Average daily cigarettes when previously smoking fairly regularly. | `R01_AC9003_NN` p. 70; `R01_AC9003_UN` p. 71 | `R08_AC9003_NN` p. 195; `R08_AC9003_UN` p. 195 |
| `regular_smoking_months` | prior_smoking_intensity | Total duration of fairly regular cigarette smoking, excluding periods off cigarettes. | `R01R_A_MNTHSMK_CIGS` p. 1205 | `R08R_A_MNTHSMK_CIGS` p. 2234 |
| `electronic_nicotine_p30d` | other_tobacco | Any use of e-cigarettes/electronic nicotine products in the past 30 days at baseline. | `R01R_A_P30D_ECIG` p. 1107 | `R08R_A_P30D_EPRODS` p. 2241 |
| `traditional_cigar_p30d` | other_tobacco | Any use of traditional cigars in the past 30 days at baseline. | `R01R_A_P30D_GTRAD` p. 1117 | `R08R_A_P30D_GTRAD` p. 2258 |
| `cigarillo_p30d` | other_tobacco | Any use of cigarillos in the past 30 days at baseline. | `R01R_A_P30D_GRILLO` p. 1127 | `R08R_A_P30D_GRILLO` p. 2268 |
| `filtered_cigar_p30d` | other_tobacco | Any use of filtered cigars in the past 30 days at baseline. | `R01R_A_P30D_GFILTR` p. 1138 | `R08R_A_P30D_GFILTR` p. 2278 |
| `hookah_p30d` | other_tobacco | Any use of hookah tobacco in the past 30 days at baseline. | `R01R_A_P30D_HOOK` p. 1158 | `R08R_A_P30D_HOOK` p. 2305 |
| `smokeless_tobacco_p30d` | other_tobacco | Past-30-day use of the smokeless tobacco products defined for the starting wave; loose-snus classification changes across waves. | `R01R_A_P30D_SMKLS` p. 1168 | `R08R_A_P30D_SMKLS` p. 2323 |
| `snus_p30d` | other_tobacco | Past-30-day snus use as defined for the starting wave: snus pouches in Waves 1–3; loose snus and pouches in Waves 4–8. | `R01R_A_P30D_SNUS` p. 1179 | `R08R_A_P30D_SNUS` p. 2313 |
| `household_tobacco_any` | household | Whether another person living in the home uses any listed tobacco/nicotine product. | `R01_AX0066_01` p. 871; `R01_AX0066_02` p. 871; `R01_AX0066_03` p. 872; `R01_AX0066_04` p. 873; `R01_AX0066_05` p. 873 | `R08R_A_AX0066_V3` p. 1585 |
| `home_combustible_smoking_rules` | household | Rules about smoking products that are burned inside the home. | `R01_AR1045` p. 874 | `R08_AR1045` p. 1587 |
| `physical_health` | health_behavior | Self-rated general physical health. | `R01_AX0090` p. 878 | `R08_AX0090` p. 1657 |
| `mental_health` | health_behavior | Self-rated general mental health including stress and emotions. | `R01_AX0091` p. 879 | `R08_AX0091` p. 1658 |
| `social_satisfaction` | health_behavior | Satisfaction with social activities and relationships. | `R01_AX0092` p. 881 | `R08_AX0092` p. 1663 |
| `emotional_problems_7d` | health_behavior | How often emotional problems bothered the respondent in the past 7 days. | `R01_AX0103` p. 899 | `R08_AX0103` p. 1670 |
| `depressive_problem_recency` | health_behavior | Last significant problems with feeling trapped, lonely, sad, blue, depressed or hopeless. | `R01_AX0161` p. 960 | `R08_AX0161` p. 1866 |
| `anxiety_problem_recency` | health_behavior | Last significant problems with feeling anxious, nervous, tense, scared, panicked or impending harm. | `R01_AX0163` p. 962 | `R08_AX0163` p. 1867 |
| `alcohol_days_30d` | health_behavior | Number of days with at least one alcoholic drink in the past 30 days. | `R01_AX0075` p. 973 | `R08_AX0075` p. 1894 |
| `alcohol_drinks_per_drinking_day` | health_behavior | Usual number of alcoholic drinks per drinking day in the past 30 days. | `R01_AX0076` p. 974 | `R08_AX0076` p. 1895 |

The codebooks are at `PATH/DSN001/36498-N001-Codebook.pdf`, where N is the wave number. The machine-readable citations use full paths, not this abbreviation. This short table is not a substitute for eligibility and missing-code details in the dictionary.

## Harmonization and applicability decisions

**Demographics.** Age uses six bands: 18–24, 25–34, 35–44, 45–54, 55–64, 65+. Collapse the two oldest bands in waves 1–3; do not assign category midpoints. Education combines bachelor and advanced degree in waves 1–3 to match `_V2` in waves 4–8. Household income remains nominal-US-dollar bands, without inflation adjustment. Employment retains four paid-work categories. The released sex/gender variable is binary and its historical meaning differs: Wave 8 explicitly supplies sex reported at first interview. Its app input is optional; current gender identities outside those categories must remain unknown, not be forced into a category. No raw age, birth date or interview date is a candidate.

**Quit recency.** All eight mappings use the observed raw `AC1009_NN`/`AC1009_UN` pair. Wave 2 has **no corresponding derived DAYSQUIT_CIGS column**; its units are 1=Days and 2=Months. The other waves also permit 3=Years. One month converts to 30.4375 approximate days and one year to 365.25, as documented in the official derived algorithms elsewhere. These are approximate history conversions, never relapse durations or dates. Wave 1 asks since completely quitting, while subsequent waves ask since last cigarette; preserve that wording difference in interpretation and the app's interval context.

Wave 2's questionnaire AC1009 section (physical PDF p. 30) documents a skip error affecting some previously former/experimental former smokers; it was corrected during collection on January 29, 2015. Persistent former smokers are often not re-asked in later waves. A missing number or unit therefore stays unknown/structurally skipped, never zero. No backward/forward fill, subtraction of wave years, or reconstruction from a future interview is configured. Actual nonpositive recency in an otherwise eligible no-past-30-day-smoking cohort is analytically flagged as outside the recency feature's range, not silently converted to a valid duration.

**Prior intensity and duration.** `prior_regular_cigarettes_per_day` uses raw AC9003 number/unit pairs; 1=Cigarettes per day, 2=Packs per day, with 20 cigarettes per pack confirmed against each wave's PERDAY_FMR derivation. These questions apply to former smokers who smoked fairly regularly, and later waves restrict re-asking to specific newly/recently former and newly reported regular-smoking histories. They are not universal former-smoker questions. `regular_smoking_months` uses the supplied derived months field where present; Wave 2 uses raw AC9002 units **1=Months, 2=Years**. Unit code 2 thus means different things in three different question families: months of last-use recency, packs/day of prior intensity, and years of regular-smoking duration. The conversions are question-specific.

The source algorithms can incorporate historical survey knowledge already available by the starting interview, including youth/special-wave history carried into official derived columns. The dictionary records those earlier-variable references but requires **no extra historical-wave join**. For raw conditional items, earlier-history references explain why an answer may be skipped; they do not authorize filling a skip from an earlier response. In Wave 1, the supplied MNTHSMK algorithm has a documented partial-component rule when years or months is structurally inapplicable; use its released result rather than generalizing that exception to all number/unit fields.

Historical regular-smoking answers can be extremely sparse in later waves because of routing. They remain candidates with explicit limitations; do not assume their app availability implies that every training respondent answered them. Later authorized data work must report missingness/eligibility, and any data-driven feature reduction must use training participants only after splits are locked. Zero intensity, when a valid observed raw value, differs from a missing response. No smoking-history answer is assumed to describe a future event.

**Other tobacco.** All seven product-use features use their official starting-wave derived past-30-day indicators, 1=Yes and 2=No, mapped to 1 and 0. Unknown/system missing/derived missing are not No. E-cigarette items in waves 1–2 broaden to electronic nicotine products in waves 3–8; this is a documented product-scope difference, not exact measurement invariance. Snus and other smokeless tobacco remain separate wave-defined indicators; their product-form scope changes as documented below. These are valid baseline constructs for former cigarette smokers even when they currently use another tobacco product.

### Smokeless/snus product-scope correction after audit

The earlier description and app prompt “smokeless tobacco other than snus” were incorrect for the early waves. **Loose snus belongs in the other-smokeless question in Waves 1–3; the snus question concerns pouches. Waves 4–8 exclude snus from the other-smokeless item and show both loose snus and pouches in the snus item.** The paired `snus_p30d` description was also corrected so it does not imply pouches only in the later waves. No source columns, official derived indicators, binary mappings, cohort rules or predictor count were changed.

The recipe and generated mapping now store `description`, `app_prompt`, `app_notes`, `product_scope` and `semantic_source_assertions` in each wave entry for both features. **An app must select `fields[name].waves[starting_wave].app_prompt`**, not use one common product exclusion for every wave. The common prompt explicitly points to the starting-wave examples. CSV descriptions/prompts are the wave-specific overrides, with the scope and semantic assertions in separate JSON cells.

| Wave | Other-smokeless source | Snus source | Loose-snus classification |
|---|---|---|---|
| 1 | `PATH/DS1001/36498-1001-Questionnaire.pdf`, `R01_AS1001`, physical PDF p. 49 | `PATH/DS1001/36498-1001-Questionnaire.pdf`, `R01_AS1004SU`, physical PDF p. 54 | Other-smokeless question; snus-pouch question is separate. |
| 2 | `PATH/DS2001/36498-2001-Questionnaire.pdf`, `R02_AS1004`, physical PDF p. 93 | `PATH/DS2001/36498-2001-Questionnaire.pdf`, `R02_AU1004`, physical PDF p. 91 | Other-smokeless question; snus-pouch question is separate. |
| 3 | `PATH/DS3001/36498-3001-Questionnaire.pdf`, `R03_AS1004`, physical PDF p. 103 | `PATH/DS3001/36498-3001-Questionnaire.pdf`, `R03_AU1004`, physical PDF p. 93 | Other-smokeless question; snus-pouch question is separate. |
| 4 | `PATH/DS4001/36498-4001-Questionnaire.pdf`, `R04_AS1004`, physical PDF p. 130 | `PATH/DS4001/36498-4001-Questionnaire.pdf`, `R04_AU1004`, physical PDF p. 119 | Snus question includes loose snus and pouches; other-smokeless excludes snus. |
| 5 | `PATH/DS5001/36498-5001-Questionnaire.pdf`, `R05_AS1004`, physical PDF p. 122 | `PATH/DS5001/36498-5001-Questionnaire.pdf`, `R05_AU1004`, physical PDF p. 114 | Snus question includes loose snus and pouches; other-smokeless excludes snus. |
| 6 | `PATH/DS6001/36498-6001-Questionnaire-English.pdf`, `R06_AS1004`, physical PDF p. 137 | `PATH/DS6001/36498-6001-Questionnaire-English.pdf`, `R06_AU1004`, physical PDF p. 127 | Snus question includes loose snus and pouches; other-smokeless excludes snus. |
| 7 | `PATH/DS7001/36498-7001-Questionnaire-English.pdf`, `R07_AS1004`, physical PDF p. 161 | `PATH/DS7001/36498-7001-Questionnaire-English.pdf`, `R07_AU1004`, physical PDF p. 150 | Snus question includes loose snus and pouches; other-smokeless excludes snus. |
| 8 | `PATH/DS8001/36498-8001-Questionnaire-English.pdf`, `R08_AS1004`, physical PDF p. 142 | `PATH/DS8001/36498-8001-Questionnaire-English.pdf`, `R08_AU1004`, physical PDF p. 133 | Snus question includes loose snus and pouches; other-smokeless excludes snus. |

At Wave 1, physical PDF p. 49 also contains the AS1002 product grid: AS1002_01 is snus pouches and AS1002_02 includes loose snus, moist snuff, dip, spit or chewing tobacco. The Wave 2 AS1004 wording explicitly includes loose snus (physical p. 93), while AU1004 asks snus pouches (p. 91). From Wave 4, AU1004 includes the image instruction “BOTH LOOSE AND POUCHES” and AS1004 excludes snus. These are documented instrument differences, not interchangeable labels.

Early AU brand screens also matter: Wave 1 `R01_AU1003` and routing boxes (questionnaire physical p. 50 onward), Wave 2 `R02_AU9003` (p. 92) and Wave 3 `R03_AU9003` (see exact evidence reference in the dictionary) distinguish Skoal Bandits from other pouch brands. The official SMKLS/SNUS algorithms use this routing alongside other smoking/recency answers. The correction therefore **retains those supplied derived indicators**, not a new blanket brand rule or a retrospective reassignment based only on product form. An app must respect the source routing or retain unknown for unsupported histories; no replacement survey-classification algorithm or app is implemented here.

The semantic validator checks source text and wave-specific descriptions/prompts against configured source assertions, including the loose-snus example and brand-screen evidence. A regression test restores the original bad Wave 2 prompt and requires validation to fail. Further tests check the paired early/later form distinction and CSV override propagation. A passing header check alone is not evidence that a feature description is scientifically correct.

**Household.** Early household sources are multi-select flags: 1=Marked, 2=Not Marked, not direct yes/no answers. The conservative collapse returns any use only with an affirmative product mark and no contradictory none mark; it returns no use only with an affirmative none mark and all product marks unselected. Contradictions, no selected option, missing flags, living-alone skips and parent-interview skips remain unknown with a reason. Waves 4–8 use the official four-level household recode, collapsing use categories 1–3 to any use and category 4 to none. Later lists broaden to additional nicotine products; no conversion claims cigarette-specific exposure or exposure intensity. Home combustible-smoking rules are a separate three-category response covering products that burn. A rule does not prove whether smoking occurred.

**Health and behavior.** Self-rated physical/mental health, social satisfaction, seven-day emotional distress, significant depressive/anxiety-problem recency and alcohol questions are self-reports, not diagnoses. Exact health-problem definitions and recall periods are retained in the source prose. Documented software/skip/data errors, including some Wave 8 health items, remain missing; they are never coded as good health or absence of symptoms. Alcohol days and drinks/day are conditional on alcohol screening. A non-drinker skipped out of the numeric item is not silently assigned zero. The app must expose a not-applicable/unknown option and must use the original drink-serving definition.

## Valid ranges, units and missingness

Categorical inputs use exactly the source valid-code labels, followed by the explicit common-code map. Missing codes are wave- and variable-specific; raw -1 and derived -99911 retain structural-skip meaning, while unknown, refusal, not-ascertained, improbable, prior-wave-missing and respondent-removed codes retain distinct reasons. Dot/blank missing values are never numerical zero.

Numeric domains retain source precision, explicit range checks and verbatim digit/unit constraints. Check strength is preserved: for example Wave 1 alcohol 0–30 days and 1–90 drinks are documented as **soft** range checks. The mapping deliberately adopts those expected ranges as analytic admissibility rules; it does not claim they were universally hard instrument limits. Rejecting/flagging out-of-range entries is not learned clipping or imputation. The released decimal precision is checked before unit arithmetic, while legitimate fractional *converted outputs* (e.g., 30.4375 days for one month) are retained.

Some questions/derived algorithms have no explicit universal finite upper validity bound. The dictionary does not invent one from the codebook's observed maximum. It retains the entry/routing/program text and marks the missing bound rather than claiming verification that the source cannot provide. Unit-specific two-digit notes, such as days/months restrictions that do not mention years, remain verbatim rather than being generalized incorrectly. Codebook sample minima/maxima are stored under an explicitly descriptive name only. For example Wave 8 usual alcohol drinks has an observed maximum of 30 but a documented range check up to 90; a value of 60 is not rejected just because it exceeds the observed maximum.

`src/path_project/features.py` provides deterministic, non-learned scalar transformations and returns `(value, reason)`. Stage 3 exercises these **only on synthetic examples**. Missingness reasons are retained as metadata for subsequent preparation; imputers, encoders, feature selection, sampling and calibration must still be fitted only after participant splitting. No participant-level transformed data have been generated.

## Scope, rejected candidates and app boundary

No PERSONID, CASEID, survey weights, PSU/stratum, interview mode/date, future attendance, next-wave answer or outcome-derived field is a predictor. The app does not collect IDs or weights. Cohort status can be checked separately at intake, but cohort/outcome fields do not enter the candidate model vector.

Product-mixed quit-attempt dates/durations, current-smoker-only nicotine-dependence questions and first-onset age questions with different new-baseline routing were not added merely to reach a desired count. Their applicability or product scope would require more reconstruction than this compact starting model. The proposal's MICE, SMOTE, large feature selection and promised performance are not assumed necessary or successful. No outcome-informed selection has occurred.

The app may eventually ask the optional prompts in the dictionary, with a starting-wave context and source-compatible categories/units. It must mirror eligibility rather than compel an inapplicable history answer. The fact that a person could supply an answer today does not repair routed historical missingness in PATH or validate extrapolation to that person. There is no prediction service or fitted demo in this stage. Stage 2's restriction to next-survey past-30-day smoking, variable intervals, no fixed-year risks, no personal confidence percentage, no causal/clinical/national claims remains in force.

## Reproduction and validation

Run from the workspace root with the existing isolated Python 3.13.5 interpreter:

```bash
.venv/bin/python scripts/build_feature_mapping.py
.venv/bin/python scripts/validate_feature_mapping.py
.venv/bin/python scripts/check_feature_evidence.py
.venv/bin/python scripts/validate_prediction_specification.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_inputs.py
```

The validator reads actual TSV **headers only**, validates source-document fingerprints, exact categorical/missing-code domains, input timing/roles, transformation schemas, unit codes, endpoint mappings and CSV consistency. It writes aggregate `reports/feature_mapping_validation.json`. Use `--no-write` for an audit. `scripts/check_feature_evidence.py` independently verifies indexed variable headings on their cited physical PDF pages and saves `reports/feature_evidence_checks.json`; it also supports `--no-write` for audits. Dependency versions remain those saved in `requirements-lock.txt`; no new package installation or network access is required.

`docs/feature_dictionary.csv` is a deliberate `.gitignore` exception for public metadata only. Raw CSV/TSV survey data, PERSONID outputs, processed participant data, caches, split files and trained artifacts remain ignored. No Git repository was initialized, no commit/push was made and nothing was uploaded. The next stage requires a separately authorized prompt; do not build a cohort or fit a model yet.
