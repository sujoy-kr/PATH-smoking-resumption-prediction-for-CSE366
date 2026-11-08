# Exact app input specification

Question specification only; no trained app or validated risk estimates yet

## Eligibility gates

If any required answer is absent or differs, explain outside/unknown cohort eligibility and do not issue a prediction. These gates approximate official survey-derived eligibility; they are not model features.

- Are you age 18 or older? Options: Yes; No; Don't know / prefer not to answer. Required: **Yes**.
- Have you smoked at least 100 cigarettes in your entire life? Options: Yes; No; Don't know / prefer not to answer. Required: **Yes**.
- Do you now smoke cigarettes every day, some days, or not at all? Options: Every day; Some days; Not at all; Don't know / prefer not to answer. Required: **Not at all**.
- Have you smoked a cigarette, even one or two puffs, in the past 30 days? Options: Yes; No; Don't know / prefer not to answer. Required: **No**.

## Optional model questions

Starting-wave context 1–7 selects wording/units only, never a predictor or a calendar-time guarantee. No automatic claim that a modern user matches a historical wave.

All optional model questions permit don't know, prefer not to answer, and not applicable/not previously asked; encode null plus distinct reason, never zero. No invented historical responses or fixed imputation values. Later preprocessing learns from tuning training folds only.

Common missing options: Not answered (default); Don’t know; Prefer not to answer; Not applicable; Not previously asked/recorded. Each produces null plus its separate reason, never numeric zero. No hand-chosen mean/median is inserted by the UI. Later preprocessing must be learned inside tuning training folds.

### age_band

What is your age group at the starting interview?

Response options: 1 = 18–24; 2 = 25–34; 3 = 35–44; 4 = 45–54; 5 = 55–64; 6 = 65+.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### education_level

What is the highest level of education you have completed?

Response options: 1 = Less than high school; 2 = GED; 3 = High school graduate; 4 = Some college or associate degree; 5 = Bachelor or advanced degree.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### employment_status

What is your current paid employment status and usual weekly hours category?

Response options: 1 = Full-time, at least 35 hours/week; 2 = Part-time, 15–34 hours/week; 3 = Part-time, under 15 hours/week; 4 = Not currently working for pay.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### last_cigarette_recency_days

- Wave 1: About how long has it been since you completely quit smoking cigarettes?
- Wave 2: About how long has it been since you last smoked a cigarette?
- Wave 3: About how long has it been since you last smoked a cigarette?
- Wave 4: About how long has it been since you last smoked a cigarette?
- Wave 5: About how long has it been since you last smoked a cigarette?
- Wave 6: About how long has it been since you last smoked a cigarette?
- Wave 7: About how long has it been since you last smoked a cigarette?

Response: positive whole-number quantity plus Days/Months/Years; Wave 2 permits Days/Months only. Approximate conversions: days ×1, months ×30.4375, years ×365.25. Documented entry width: Waves 2–4 allow two digits for Days/Months; Waves 5–7 allow two digits for all supplied units (maximum quantity 99). Wave 1 has no finite bound documented in this mapping; no hard bound is invented. Do not truncate a duration to fit; use another supported equivalent unit if appropriate or choose unknown/not recorded. >100 years is a review flag, not an accepted clinical history.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### electronic_nicotine_p30d

- Wave 1: Have you used an e-cigarette at all in the past 30 days?
- Wave 2: Have you used an e-cigarette at all in the past 30 days?
- Wave 3: Have you used any electronic nicotine product at all in the past 30 days?
- Wave 4: Have you used any electronic nicotine product at all in the past 30 days?
- Wave 5: Have you used any electronic nicotine product at all in the past 30 days?
- Wave 6: Have you used any electronic nicotine product at all in the past 30 days?
- Wave 7: Have you used any electronic nicotine product at all in the past 30 days?

Response options: 0 = No; 1 = Yes.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### household_tobacco_any

- Wave 1: Not including yourself, does anyone who lives with you now use one of the listed tobacco/nicotine products? Products in this survey context: cigarettes; smokeless tobacco; cigars, cigarillos or filtered cigars; any other form of tobacco. If you live alone, choose not applicable.
- Wave 2: Not including yourself, does anyone who lives with you now use one of the listed tobacco/nicotine products? Products in this survey context: cigarettes; smokeless tobacco; traditional cigars, cigarillos or filtered cigars; any other form of tobacco. If you live alone, choose not applicable.
- Wave 3: Not including yourself, does anyone who lives with you now use one of the listed tobacco/nicotine products? Products in this survey context: cigarettes; e-cigarettes or other electronic nicotine products; snus pouches; other smokeless tobacco; traditional cigars, cigarillos or filtered cigars; hookah; any other form of tobacco. If you live alone, choose not applicable.
- Wave 4: Not including yourself, does anyone who lives with you now use one of the listed tobacco/nicotine products? Products in this survey context: cigarettes, cigars/cigarillos/filtered cigars, pipe tobacco, electronic products, other tobacco including smokeless, snus and hookah. If you live alone, choose not applicable.
- Wave 5: Not including yourself, does anyone who lives with you now use one of the listed tobacco/nicotine products? Products in this survey context: cigarettes, cigars/cigarillos/filtered cigars, pipe tobacco, electronic products, other tobacco including smokeless, snus and hookah. If you live alone, choose not applicable.
- Wave 6: Not including yourself, does anyone who lives with you now use one of the listed tobacco/nicotine products? Products in this survey context: cigarettes, cigars/cigarillos/filtered cigars, pipe tobacco, electronic products, other tobacco including smokeless, snus, hookah and IQOS. If you live alone, choose not applicable.
- Wave 7: Not including yourself, does anyone who lives with you now use one of the listed tobacco/nicotine products? Products in this survey context: cigarettes, cigars/cigarillos/filtered cigars, pipe tobacco, electronic products, other tobacco including smokeless, snus, hookah, IQOS, pouches and oral nicotine products. If you live alone, choose not applicable.

Response options: 0 = No; 1 = Yes.

Missing options as above. Living alone is not applicable, not No.

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### home_combustible_smoking_rules

Which statement best describes the rules about smoking products that are burned inside your home?

Response options: 1 = Not allowed anywhere or at any time; 2 = Allowed in some places or at some times; 3 = Allowed anywhere and at any time.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### physical_health

In general, how would you rate your physical health?

Response options: 1 = Excellent; 2 = Very good; 3 = Good; 4 = Fair; 5 = Poor.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### mental_health

In general, how would you rate your mental health, which includes stress, depression, and problems with emotions?

Response options: 1 = Excellent; 2 = Very good; 3 = Good; 4 = Fair; 5 = Poor.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### social_satisfaction

In general, how satisfied are you with your social activities and relationships?

Response options: 1 = Extremely satisfied; 2 = Very satisfied; 3 = Moderately satisfied; 4 = A little satisfied; 5 = Not at all satisfied.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

### emotional_problems_7d

In the past 7 days, how often have you been bothered by emotional problems such as feeling anxious, depressed or irritable?

Response options: 1 = Never; 2 = Rarely; 3 = Sometimes; 4 = Often; 5 = Very often.

Missing options as above. 

Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.

## Deployment limitations

Supply a positive whole number and valid unit, or explicit missing. If converted recency <=30 days, clarify the no-past-30-day-use eligibility conflict; never change the answer to fit. Recency is approximate historical time, not time to resumption. Persistent former respondents often were not asked; answering today may shift the missingness distribution.

No sex/gender input is requested: the released category is often inherited from a historical first interview and cannot safely be substituted with an invented historical answer from a new user. Research-only history, product scope and alcohol questions are not requested by the app.

The research profile must use actual survey-available values. No made-up histories or proxy sex/gender answers are supplied to it.

No model or probability validation exists yet. The app may eventually describe next-survey smoking status only, with unknown varying individual intervals; no fixed-year, persistent-relapse, causal or personal-confidence claims.
