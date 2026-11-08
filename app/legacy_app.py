"""Streamlit research demonstration; all inference stays local."""
from pathlib import Path
import sys
import pandas as pd
import streamlit as st
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.demo import load_demo_engine,read_json
from path_project.evaluation import BoundaryError

st.set_page_config(page_title='PATH · Research demo',page_icon='◌',layout='centered')
config=read_json(ROOT,'configs/demo.json')
questions=read_json(ROOT,config['questions'])
metadata=read_json(ROOT,config['metadata'])
features=metadata['classifier']['features']
wave=str(config['wave_context'])
selected=[next(q for q in questions['questions'] if q['feature']==f) for f in features]

@st.cache_resource(show_spinner=False)
def engine():
    return load_demo_engine(ROOT)

st.caption('CSE366  /  PATH  /  LOCAL RESEARCH PROTOTYPE')
st.title(config['title'])
st.write('Explore an estimate of cigarette smoking reported in the **past 30 days at the next scheduled survey**, among adult former established smokers reporting no use in the past 30 days now.')
st.info('This is next-survey status, not annual risk. Survey intervals vary. The model cannot estimate when smoking will resume or an exact return-to-smoking date.')
st.caption('No names, contact details or participant IDs. Answers stay in this browser session and local process; they are not saved to files or cached as prediction histories. Close the session to discard them.')
preset=st.selectbox('Start with your answers or a fictional demonstration',list(config['presets']),key='preset')
example=config['presets'][preset] or {}
if example:st.warning('Fictional software example — not a real PATH participant or evidence of an individual outcome.')

with st.form('prediction',clear_on_submit=False):
    st.subheader('1 · Confirm the study profile')
    st.caption('These checks approximate survey eligibility. Unknown or unsupported eligibility withholds the estimate.')
    eligibility={}
    gatekeys=['adult','established_history','current_smoking','past30_use']
    for key,q in zip(gatekeys,questions['eligibility_questions']):
        default=q['options'].index(q['required_answer']) if example else len(q['options'])-1
        eligibility[key]=st.selectbox(q['question'],q['options'],index=default,key=preset+'_'+key)
    st.subheader('2 · Four model inputs')
    st.caption('Wording and units follow the documented Wave 7 baseline context. A new self-report may differ from a historically routed survey answer. Supply at least two inputs; unknown is never treated as zero.')
    answers={};summary=[]
    for q in selected:
        name=q['feature'];entry=q['waves'][wave];raw=example.get(name,'unanswered')
        missing=q['missing_options']
        if q['kind']=='category':
            options={**missing,**q['options']}
            value=st.selectbox(entry['prompt'],list(options),format_func=lambda x,o=options:o[x],index=list(options).index(raw),key=preset+'_'+name)
            answers[name]=value;summary.append({'Question':entry['prompt'],'Answer':options[value]})
        else:
            options={**missing,'supplied':'Supply a number and unit'}
            default='supplied' if isinstance(raw,dict) else raw
            mode=st.selectbox(entry['prompt'],list(options),format_func=lambda x,o=options:o[x],index=list(options).index(default),key=preset+'_recency_mode')
            left,right=st.columns(2)
            number=left.number_input('Time since last cigarette · whole number',min_value=1,max_value=99,value=raw['number'] if isinstance(raw,dict) else 2,step=1,key=preset+'_number')
            units=entry['unit_options']
            unit=right.selectbox('Time unit',list(units),format_func=lambda x:units[x],index=list(units).index(raw['unit']) if isinstance(raw,dict) else 1,key=preset+'_unit')
            answers[name]={'number':number,'unit':unit} if mode=='supplied' else mode
            summary.append({'Question':entry['prompt'],'Answer':f'{number} {units[unit]}' if mode=='supplied' else options[mode]})
            st.caption('1–99 whole units. Months convert to 30.4375 days; years to 365.25 days. Historical recency is not future relapse time. A value of 30 days or less conflicts with eligibility and is rejected.')
    submitted=st.form_submit_button('Show research estimate',type='primary',use_container_width=True)

if submitted:
    try:
        with st.spinner('Running the frozen model and explaining its calibrated probability…'):
            result=engine().output(answers,eligibility,wave=config['wave_context'])
    except (BoundaryError,ValueError) as error:
        st.error(str(error));st.stop()
    except Exception:
        st.error('The verified local model or explanation resources could not be loaded. Check the local installation and artifact verification; no substitute estimate is shown.');st.stop()
    st.subheader('Your research estimate')
    if result['status']!='scored':st.warning(result['suppression_reason'])
    else:
        a,b=st.columns(2)
        a.metric('Estimated next-survey probability',f"{100*result['probability']:.1f}%")
        b.metric('Project risk category',result['category']['label'])
        st.write(result['endpoint']+'. '+result['prediction_interval'])
        cuts=result['category_thresholds']
        st.caption(f"Categories use the unrounded score: lower ≤ {100*cuts['lower_upper_inclusive']:.4f}%; moderate above that through {100*cuts['moderate_upper_inclusive']:.4f}%; higher above the upper cut. Rounded display values near a boundary can look equal. These are project-defined strata, not medical cutoffs.")
        st.subheader('What contributed to this estimate?')
        st.caption('Exact SHAP explains the same calibrated probability shown above. Positive contributions push up and negative contributions push down relative to a background mixture of model outputs. These are percentage-point attributions, not causal effects or promised benefits from changing an answer.')
        factors=pd.DataFrame([{'Question':f['question'],'Model answer':f['answer'],'Contribution (percentage points)':100*f['contribution']} for f in result['contributing_factors']])
        st.dataframe(factors,hide_index=True,use_container_width=True)
        base=result['explanation']['reference_model_probability']
        st.caption(f"Reference model output {100*base:.2f}% + contributions = displayed probability (rounding aside). This reference is not an observed study-group smoking rate.")
        with st.expander('Prediction identity and explanation check'):
            st.json({'unrounded_probability':result['probability'],'category':result['category']['code'],'thresholds':result['category_thresholds'],'model_version':result['model_version'],'explanation':result['explanation']})
    st.subheader('Submitted information')
    st.dataframe(pd.DataFrame(summary),hide_index=True,use_container_width=True)
    st.dataframe(pd.DataFrame([{'Eligibility question':q['question'],'Answer':eligibility[k]} for k,q in zip(gatekeys,questions['eligibility_questions'])]),hide_index=True,use_container_width=True)
    complete=result['input_completeness']
    st.write(f"{complete['provided']} of {complete['expected']} model inputs supplied. This is information completeness, not prediction confidence.")
    if complete['missing']:st.warning('Unknown answers use the trained missing-value handling. Survey routing and missingness may differ for new users; fewer answers do not establish reliable personalized estimates.')
    st.caption('Model: '+result['model_version']['selected_model']+' · SHA-256 '+result['model_version']['artifact_sha256'])

st.divider()
st.subheader('How did the frozen model perform?')
results=read_json(ROOT,config['final_results'])
score=results['metrics']['selected_calibrated']['interval_equal']
ci=results['metrics']['selected_calibrated']['confidence_intervals']
st.write(f"Reserved Wave 7→8 test: {results['unique_people']:,} held-out people, {results['positive_records']} observed positive outcomes ({100*results['positive_prevalence']:.2f}%). This is a study-group rate among eligible people with valid observed follow-up, not a national rate.")
st.dataframe(pd.DataFrame([{'Metric':label,'Estimate':f'{score[key]:.4f}','95% participant-bootstrap interval':f"{ci[key]['lower']:.4f}–{ci[key]['upper']:.4f}"} for key,label in [('average_precision','Average precision (stepwise PR metric)'),('roc_auc','ROC-AUC'),('brier','Brier score (lower is better)')]]),hide_index=True,use_container_width=True)
st.warning('Calibration was imperfect: the mean estimate was 13.90% versus 10.30% observed. Calibration worsened Brier score, and several frozen logistic baselines had higher average precision. The selected model was not changed in response.')
st.caption('Intervals describe uncertainty in aggregate test metrics, not personal confidence. Performance outside this observed-follow-up sample is unvalidated.')
with st.expander('Scope, privacy and limitations'):
    st.write('PATH is a U.S. survey population. Performance for other populations and present-day app users is unvalidated. This unweighted project does not establish national representativeness or clinical usefulness. No treatment decisions or instructions are provided.')
    st.write('The outcome is a smoking snapshot: temporary use between surveys may be missed. A negative outcome does not prove continuous abstinence; a positive does not prove persistent relapse. Missing follow-up was not labeled negative.')
    st.write(metadata['timing_unavailable_message'])
    st.write('Predictions and explanations run locally with the original fitted preprocessing, model and sigmoid calibrator. Only model resources are cached. No user answer file, database, external API, analytics or answer-history cache is created.')
    st.caption('Detailed local evidence: reports/final_evaluation.md · docs/output_contract.md · docs/timing_decision.md')
