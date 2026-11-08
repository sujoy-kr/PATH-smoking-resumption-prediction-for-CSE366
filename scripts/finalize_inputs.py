"""Build versioned final mapping/dictionary/specification and app question list.

Original locked source mappings, cohort and split files are never altered.
"""
from pathlib import Path
import csv,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.documentation import fingerprint
from path_project.cohort import json_write
from path_project.final_inputs import validate_final_inputs


def build(root=ROOT):
    settings=json.loads((root/'configs/development_exploration.json').read_text())
    mapping=json.loads((root/'configs/feature_mapping.json').read_text())
    task=json.loads((root/'configs/prediction_specification.json').read_text())
    evidence=json.loads((root/mapping['source_evidence']).read_text())['records']
    fields={f['name']:f for f in mapping['fields']}
    profiles={key:settings[key+'_features'] for key in ['app','minimal','research']}
    base_files=['configs/feature_mapping.json','configs/prediction_specification.json','docs/feature_dictionary.csv']
    final={'version':'1.0','base_mapping':'configs/feature_mapping.json','base_sha256':{name:fingerprint(root/name) for name in base_files},'feature_sets':profiles,'selection_scope':settings['selection_population'],'decisions':settings['decisions'],'cohort_or_recoding_changed':False,'model_features_only':True,'mapping_policy':'Each final field retains all original wave-specific columns, exact labels, missing codes, units and source evidence. Use the named profile, never silently default to research inputs for the app.','fields':[{**f,'final_profiles':[key for key,names in profiles.items() if f['name'] in names]} for f in mapping['fields']]}
    json_write(root/'configs/feature_mapping_final.json',final)
    updated_task={**task,'specification_version':'1.1-final-inputs','base_specification':'configs/prediction_specification.json','base_specification_sha256':fingerprint(root/'configs/prediction_specification.json'),'final_feature_sets':profiles,'final_mapping':'configs/feature_mapping_final.json','app_questions':'configs/app_questions.json','allowed_inputs':{**task['allowed_inputs'],'feature_allowlist':profiles['app'],'feature_allowlist_scope':'Default app model only; explicit minimal/research profiles have separately named allowlists.'},'cohort_change':False,'no_model_or_probability_validated':True}
    json_write(root/'configs/prediction_specification_final.json',updated_task)
    with (root/'docs/feature_dictionary.csv').open(newline='') as stream:
        reader=csv.DictReader(stream);columns=reader.fieldnames+['final_profiles','final_app_input'];rows=list(reader)
    with (root/'docs/feature_dictionary_final.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for row in rows:
            row['final_profiles']=';'.join(key for key,names in profiles.items() if row['common_name'] in names)
            row['final_app_input']=str(row['common_name'] in profiles['app']).lower();writer.writerow(row)
    prompts={
      'age_band':'What is your age group at the starting interview?',
      'education_level':'What is the highest level of education you have completed?',
      'employment_status':'What is your current paid employment status and usual weekly hours category?',
      'last_cigarette_recency_days':'About how long has it been since you last smoked a cigarette?',
      'electronic_nicotine_p30d':'Have you used any electronic nicotine product at all in the past 30 days?',
      'household_tobacco_any':'Not including yourself, does anyone who lives with you now use one of the listed tobacco/nicotine products?',
      'home_combustible_smoking_rules':'Which statement best describes the rules about smoking products that are burned inside your home?',
      'physical_health':'In general, how would you rate your physical health?',
      'mental_health':'In general, how would you rate your mental health, which includes stress, depression, and problems with emotions?',
      'social_satisfaction':'In general, how satisfied are you with your social activities and relationships?',
      'emotional_problems_7d':'In the past 7 days, how often have you been bothered by emotional problems such as feeling anxious, depressed or irritable?'
    }
    household_scope={1:'cigarettes; smokeless tobacco; cigars, cigarillos or filtered cigars; any other form of tobacco',2:'cigarettes; smokeless tobacco; traditional cigars, cigarillos or filtered cigars; any other form of tobacco',3:'cigarettes; e-cigarettes or other electronic nicotine products; snus pouches; other smokeless tobacco; traditional cigars, cigarillos or filtered cigars; hookah; any other form of tobacco',4:'cigarettes, cigars/cigarillos/filtered cigars, pipe tobacco, electronic products, other tobacco including smokeless, snus and hookah',5:'cigarettes, cigars/cigarillos/filtered cigars, pipe tobacco, electronic products, other tobacco including smokeless, snus and hookah',6:'cigarettes, cigars/cigarillos/filtered cigars, pipe tobacco, electronic products, other tobacco including smokeless, snus, hookah and IQOS',7:'cigarettes, cigars/cigarillos/filtered cigars, pipe tobacco, electronic products, other tobacco including smokeless, snus, hookah, IQOS, pouches and oral nicotine products'}
    questions=[]
    for name in profiles['app']:
        f=fields[name];waves={}
        for wave in range(1,8):
            e=f['waves'][str(wave)];prompt=prompts[name]
            if name=='last_cigarette_recency_days' and wave==1:prompt='About how long has it been since you completely quit smoking cigarettes?'
            if name=='electronic_nicotine_p30d' and wave<=2:prompt='Have you used an e-cigarette at all in the past 30 days?'
            if name=='household_tobacco_any':prompt+=' Products in this survey context: '+household_scope[wave]+'. If you live alone, choose not applicable.'
            refs=sorted({ref for component in e['components'] for ref in component['evidence_refs']})
            waves[str(wave)]={'prompt':prompt,'source_columns':e['source_columns'],'source_evidence':[{key:evidence[ref][key] for key in ['file','variable','pdf_page_start','pdf_page_end']} for ref in refs],'former_smoker_applicability':e['former_smoker_applicability'],'availability_warning':'A new self-report is not identical to a historically routed/derived survey value. Unknown and not-asked remain missing.'}
            if name=='last_cigarette_recency_days':
                waves[str(wave)]['unit_multipliers']=e['transform']['unit_multipliers'];waves[str(wave)]['unit_options']={k:{'1':'Days','2':'Months','3':'Years'}[k] for k in e['transform']['unit_multipliers']}
                constraints=e['components'][0]['valid_domain']['program_entry_constraints_verbatim']
                waves[str(wave)]['quantity_constraints_verbatim']=constraints
                text=' '.join(constraints)
                width_limits={}
                if re.search(r'2 digits for days and 2 digits for months',text,re.I):
                    width_limits={unit:99 for unit in ['1','2'] if unit in e['transform']['unit_multipliers']}
                elif re.search(r'Allow 2 digits',text,re.I):
                    width_limits={unit:99 for unit in e['transform']['unit_multipliers']}
                waves[str(wave)]['quantity_entry_width_limit_by_unit']=width_limits
        questions.append({'feature':name,'kind':'number_unit' if name=='last_cigarette_recency_days' else 'category','options':f['output_labels'],'units':f['output_units'],'missing_options':{'unanswered':'Not answered (default)','dont_know':"Don't know",'prefer_not_to_answer':'Prefer not to answer','not_applicable':'Not applicable','not_previously_asked':'Not previously asked/recorded'},'missing_behavior':settings['missing_answer_policy'],'waves':waves})
    app={'version':'1.0','purpose':'Question specification only; no trained app or validated risk estimates yet','eligibility_questions':[{'question':'Are you age 18 or older?','options':['Yes','No',"Don't know / prefer not to answer"],'required_answer':'Yes'},{'question':'Have you smoked at least 100 cigarettes in your entire life?','options':['Yes','No',"Don't know / prefer not to answer"],'required_answer':'Yes'},{'question':'Do you now smoke cigarettes every day, some days, or not at all?','options':['Every day','Some days','Not at all',"Don't know / prefer not to answer"],'required_answer':'Not at all'},{'question':'Have you smoked a cigarette, even one or two puffs, in the past 30 days?','options':['Yes','No',"Don't know / prefer not to answer"],'required_answer':'No'}],'eligibility_behavior':'If any required answer is absent or differs, explain outside/unknown cohort eligibility and do not issue a prediction. These gates approximate official survey-derived eligibility; they are not model features.','context':'Starting-wave context 1–7 selects wording/units only, never a predictor or a calendar-time guarantee. No automatic claim that a modern user matches a historical wave.','questions':questions,'research_only_policy':'The research profile must use actual survey-available values. No made-up histories or proxy sex/gender answers are supplied to it.','recency_warning':'Supply a positive whole number and valid unit, or explicit missing. If converted recency <=30 days, clarify the no-past-30-day-use eligibility conflict; never change the answer to fit. Recency is approximate historical time, not time to resumption. Persistent former respondents often were not asked; answering today may shift the missingness distribution.'}
    json_write(root/'configs/app_questions.json',app)
    validate_final_inputs(root)
    lines=['# Exact app input specification','',app['purpose'],'','## Eligibility gates','',app['eligibility_behavior'],'']
    for gate in app['eligibility_questions']:lines.append(f"- {gate['question']} Options: {'; '.join(gate['options'])}. Required: **{gate['required_answer']}**.")
    lines+=['','## Optional model questions','',app['context'],'',settings['missing_answer_policy'],'','Common missing options: Not answered (default); Don’t know; Prefer not to answer; Not applicable; Not previously asked/recorded. Each produces null plus its separate reason, never numeric zero. No hand-chosen mean/median is inserted by the UI. Later preprocessing must be learned inside tuning training folds.','']
    for q in questions:
        lines += [f"### {q['feature']}",'']
        unique={w['prompt'] for w in q['waves'].values()}
        if len(unique)==1:lines.append(next(iter(unique)))
        else:
            for w,e in q['waves'].items():lines.append(f"- Wave {w}: {e['prompt']}")
        if q['kind']=='category':lines+=['','Response options: '+'; '.join(f"{code} = {label}" for code,label in q['options'].items())+'.']
        else:lines+=['','Response: positive whole-number quantity plus Days/Months/Years; Wave 2 permits Days/Months only. Approximate conversions: days ×1, months ×30.4375, years ×365.25. Documented entry width: Waves 2–4 allow two digits for Days/Months; Waves 5–7 allow two digits for all supplied units (maximum quantity 99). Wave 1 has no finite bound documented in this mapping; no hard bound is invented. Do not truncate a duration to fit; use another supported equivalent unit if appropriate or choose unknown/not recorded. >100 years is a review flag, not an accepted clinical history.']
        lines+=['','Missing options as above. '+ ('Living alone is not applicable, not No.' if q['feature']=='household_tobacco_any' else ''),'','Source columns and exact physical PDF page references for every context are in `configs/app_questions.json`; routing and all labels remain in `docs/feature_dictionary_final.csv`.','']
    lines+=['## Deployment limitations','',app['recency_warning'],'','No sex/gender input is requested: the released category is often inherited from a historical first interview and cannot safely be substituted with an invented historical answer from a new user. Research-only history, product scope and alcohol questions are not requested by the app.','',app['research_only_policy'],'','No model or probability validation exists yet. The app may eventually describe next-survey smoking status only, with unknown varying individual intervals; no fixed-year, persistent-relapse, causal or personal-confidence claims.']
    (root/'docs/app_questions.md').write_text('\n'.join(lines)+'\n')
    print(f"Final profiles: app={len(profiles['app'])}, minimal={len(profiles['minimal'])}, research={len(profiles['research'])}; no cohort or split changes.")

if __name__=='__main__':build()
