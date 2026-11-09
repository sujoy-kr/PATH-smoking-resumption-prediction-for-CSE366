"""Write configs/inputs_v2_4.json: wording, options and units for every candidate input.

Existing eleven inputs are copied from configs/app_questions.json (their documented
options and prompts); newly added inputs are defined here from the PATH codebook.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
old = json.loads((ROOT/'configs/app_questions.json').read_text())
PROMPTS = {
    'age_band': 'What is your age group?', 'education_level': 'What is your highest completed education?',
    'employment_status': 'What is your current work situation?',
    'electronic_nicotine_p30d': 'Have you used electronic nicotine products in the past 30 days?',
    'household_tobacco_any': 'Does anyone else at home use tobacco or nicotine?',
    'mental_health': 'How would you rate your overall mental health?',
    'emotional_problems_7d': 'How often have emotional problems bothered you in the past 7 days?'}
spec = {}
for q in old['questions']:
    f = q['feature']
    if q['kind'] == 'category':
        spec[f] = {'kind': 'category', 'options': q['options'], 'prompt': PROMPTS.get(f, q['waves']['7']['prompt'])}
    else:
        spec[f] = {'kind': 'number_unit', 'prompt': 'How long has it been since your last cigarette?',
                   'units': {'1': ['Days', 1.], '2': ['Months', 30.4375], '3': ['Years', 365.25]}, 'minimum': 0, 'maximum': None, 'default_unit': '2'}
spec['last_cigarette_recency_days']['minimum_exclusive'] = 0
yn = {'0': 'No', '1': 'Yes'}
def cat(prompt, options, help=None):
    return {'kind': 'category', 'options': options, 'prompt': prompt, **({'help': help} if help else {})}
spec.update({
    'sex_recorded': cat('What is your sex?', {'1': 'Male', '2': 'Female'}),
    'traditional_cigar_p30d': cat('In the past 30 days, have you smoked traditional cigars?', yn),
    'cigarillo_p30d': cat('In the past 30 days, have you smoked cigarillos?', yn),
    'filtered_cigar_p30d': cat('In the past 30 days, have you smoked filtered cigars?', yn),
    'hookah_p30d': cat('In the past 30 days, have you used a hookah (waterpipe)?', yn),
    'smokeless_tobacco_p30d': cat('In the past 30 days, have you used smokeless tobacco (not snus)?', yn),
    'snus_p30d': cat('In the past 30 days, have you used snus?', yn),
    'depressive_problem_recency': cat('When did you last have a problem with depression?', {'1': 'Past month', '2': '2–12 months ago', '3': 'Over a year ago', '4': 'Never'}),
    'anxiety_problem_recency': cat('When did you last have a problem with anxiety?', {'1': 'Past month', '2': '2–12 months ago', '3': 'Over a year ago', '4': 'Never'}),
    'tried_to_quit_12m': cat('In the past 12 months, have you tried to quit using tobacco completely?', yn),
    'quit_plan_timeframe': cat('When do you plan to quit using tobacco for good?', {'1': 'In the next 7 days', '2': 'In the next 30 days', '3': 'In the next 6 months', '4': 'In the next year', '5': 'More than one year from now', '6': 'I do not plan to quit'}),
    'tobacco_addiction_self': cat('Do you consider yourself addicted to tobacco products?', {'1': 'No, not at all', '2': 'Yes, somewhat addicted', '3': 'Yes, very addicted'}),
    'alcohol_days_30d': {'kind': 'number', 'prompt': 'On how many of the past 30 days did you drink alcohol?', 'minimum': 0, 'maximum': 30},
    'alcohol_drinks_per_drinking_day': {'kind': 'number', 'prompt': 'On days when you drink, about how many drinks do you have?', 'minimum': 1, 'maximum': 90},
    'prior_regular_cigarettes_per_day': {'kind': 'number_unit', 'prompt': 'When you last smoked regularly, about how many did you smoke per day?',
        'units': {'1': ['Cigarettes', 1.], '2': ['Packs', 20.]}, 'minimum': 0, 'minimum_exclusive': 0, 'maximum': None, 'default_unit': '1'},
    'regular_smoking_months': {'kind': 'number_unit', 'prompt': 'For about how long have you smoked (or did you smoke) cigarettes regularly?',
        'units': {'1': ['Months', 1.], '2': ['Years', 12.]}, 'minimum': 0, 'minimum_exclusive': 0, 'maximum': None, 'default_unit': '2'},
    'cigarettes_per_day': {'kind': 'number_unit', 'prompt': 'On days you smoke, about how many cigarettes do you smoke per day?',
        'units': {'1': ['Cigarettes', 1.], '2': ['Packs', 20.]}, 'minimum': 0, 'minimum_exclusive': 0, 'maximum': None, 'default_unit': '1'},
    'minutes_to_first_cigarette': {'kind': 'number_unit', 'prompt': 'How soon after waking do you smoke your first cigarette?',
        'units': {'1': ['Minutes', 1.], '2': ['Hours', 60.]}, 'minimum': 0, 'minimum_exclusive': 0, 'maximum': None, 'default_unit': '1'}})
(ROOT/'configs/inputs_v2_4.json').write_text(json.dumps(spec, indent=2, ensure_ascii=False)+'\n')
print(len(spec), 'inputs written')
