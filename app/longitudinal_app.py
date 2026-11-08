"""Single-model assessment with fixed choices and automatic horizon results."""
from pathlib import Path
from html import escape
import json
import sys
import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from path_project.evaluation import BoundaryError
from path_project.longitudinal import load_study
from path_project.assessment import assess_available

st.set_page_config(page_title='Reclaim · Your smoking outlook', page_icon='◈', layout='wide', initial_sidebar_state='collapsed')
st.html('<style>'+(ROOT/'app/styles.css').read_text()+'</style>')


@st.cache_resource(show_spinner=False)
def engine():
    return load_study(ROOT)


def heading(number, title, copy):
    st.html(f'<div class="section-heading"><span class="step">{number}</span><h2>{escape(title)}</h2></div><p class="section-copy">{escape(copy)}</p>')


st.html('<div class="brand"><div class="brand-name"><span class="brand-mark">↗</span>reclaim<span style="color:#8a9da8;font-weight:400"> / </span></div><div class="brand-meta">Your quit journey, in perspective</div></div>')
st.html('''<section class="hero"><div class="eyebrow">A clearer view of what comes next</div>
<h1>You’ve quit.<br>Understand your outlook.</h1>
<p>A short assessment of your current situation. Explore the estimated chance of returning to smoking over time, and the factors influencing your result.</p>
<div class="hero-chips"><span>8 questions + eligibility</span><span>No account needed</span><span>Answers stay in this session</span></div></section>''')
st.caption('Survey-based research estimate · Months are approximate, using wave collection-window midpoints. Personal and clinical accuracy are unvalidated.')

try:
    bundle = engine()
except (OSError, BoundaryError, ValueError):
    st.error('The assessment is temporarily unavailable because the local model could not be verified. No substitute prediction is shown.')
    st.stop()

question_spec = json.loads((ROOT/'configs/app_questions.json').read_text())
features = bundle['model'].features
questions = {q['feature']: q for q in question_spec['questions']}
config, results, summary = bundle['config'], bundle['results'], bundle['summary']
labels = {
    'age_band': 'Age group', 'education_level': 'Education', 'employment_status': 'Employment',
    'last_cigarette_recency_days': 'Time since last cigarette', 'electronic_nicotine_p30d': 'Electronic nicotine use',
    'household_tobacco_any': 'Household tobacco exposure', 'mental_health': 'Mental health',
    'emotional_problems_7d': 'Recent emotional difficulties', 'home_combustible_smoking_rules': 'Home smoking rules',
    'physical_health': 'Physical health', 'social_satisfaction': 'Social satisfaction'
}
prompts = {
    'age_band': 'What is your age group?',
    'education_level': 'What is your highest completed education?',
    'employment_status': 'What is your current work situation?',
    'electronic_nicotine_p30d': 'Have you used electronic nicotine products in the past 30 days?',
    'household_tobacco_any': 'Does anyone else at home use tobacco or nicotine?',
    'mental_health': 'How would you rate your overall mental health?',
    'emotional_problems_7d': 'How often have emotional problems bothered you in the past 7 days?'
}
presets = {
    'My assessment': {},
    'Example · recent quit': {'age_band': '2', 'education_level': '4', 'employment_status': '1',
        'last_cigarette_recency_days': {'number': 6, 'unit': '2'}, 'electronic_nicotine_p30d': '1',
        'household_tobacco_any': '1', 'mental_health': '4', 'emotional_problems_7d': '4',
        'home_combustible_smoking_rules': '2', 'physical_health': '3', 'social_satisfaction': '3'},
    'Example · longer quit': {'age_band': '5', 'education_level': '5', 'employment_status': '1',
        'last_cigarette_recency_days': {'number': 8, 'unit': '3'}, 'electronic_nicotine_p30d': '0',
        'household_tobacco_any': '0', 'mental_health': '2', 'emotional_problems_7d': '2',
        'home_combustible_smoking_rules': '1', 'physical_health': '2', 'social_satisfaction': '2'}
}
with st.expander('Try an example assessment'):
    preset = st.radio('Assessment profile', list(presets), index=0, horizontal=True, key='assessment_profile')
    st.caption('Examples contain fictional answers. Choose “My assessment” to enter your own.')
example = presets[preset]
if example:
    st.info('You’re viewing fictional example answers. These are not a real participant or a known outcome.')

# Stable widget identities within each profile. No form batching: each selection
# immediately updates completion and clears stale errors/results.
prefix = preset
eligibility = []
with st.container(border=True, key='eligibility_card'):
    heading('01', 'Tell us where you are in your journey', 'These answers help us explain how closely the study matches your situation. You can leave them unknown.')
    columns = st.columns(2, gap='large')
    for i, q in enumerate(question_spec['eligibility_questions']):
        with columns[i % 2]:
            value = st.radio(q['question'], q['options'],
                index=q['options'].index(q['required_answer']) if example else None,
                horizontal=True, key=f'{prefix}_gate_{i}')
            eligibility.append(value)

answers, displayed = {}, []
with st.container(border=True, key='situation_card'):
    heading('02', 'A little about your current situation', 'Answer what you can. Unknown answers use the model’s fitted missing-value handling, with reduced personal support.')
    columns = st.columns(2, gap='large')
    categories = [f for f in features if f != 'last_cigarette_recency_days']
    for i, feature in enumerate(categories):
        q = questions[feature]
        options = {**q['options'], 'dont_know': 'Not sure / prefer not to say'}
        if feature == 'household_tobacco_any':
            options['not_applicable'] = 'I live alone / not applicable'
        raw = example.get(feature)
        with columns[i % 2]:
            value = st.radio(prompts.get(feature, q['waves']['7']['prompt']), list(options),
                format_func=lambda v, options=options: options[v],
                index=list(options).index(raw) if raw is not None else None,
                key=f'{prefix}_{feature}',
                horizontal=feature in ['age_band', 'electronic_nicotine_p30d', 'household_tobacco_any'],
                help='Includes stress, depression and problems with emotions.' if feature == 'mental_health' else
                     'For example, anxiety, depression or irritability.' if feature == 'emotional_problems_7d' else
                     'Includes cigarettes, cigars, electronic nicotine and other tobacco/nicotine products.' if feature == 'household_tobacco_any' else None)
        answers[feature] = value if value is not None else 'unanswered'
        displayed.append({'Question': labels[feature], 'Answer': options[value] if value is not None else 'Not answered'})
    st.divider()
    st.markdown('**How long has it been since your last cigarette?**')
    left, right = st.columns([1, 2], gap='large')
    raw = example.get('last_cigarette_recency_days', {})
    recency_key = f'{prefix}_recency_number'
    if recency_key not in st.session_state and raw.get('number') is not None:
        st.session_state[recency_key] = raw['number']
    number = left.number_input('Amount', min_value=1, max_value=99, step=1,
        value=None, placeholder='Enter a whole number', key=recency_key)
    units = {'1': 'Days', '2': 'Months', '3': 'Years'}
    unit = right.radio('Time unit', list(units), format_func=lambda v: units[v],
        index=list(units).index(raw.get('unit', '2')), horizontal=True, key=f'{prefix}_recency_unit')
    answers['last_cigarette_recency_days'] = {'number': number, 'unit': unit} if number is not None else 'unanswered'
    displayed.append({'Question': labels['last_cigarette_recency_days'], 'Answer': f'{number} {units[unit].lower()}' if number is not None else 'Not answered'})
    st.caption('Entering an amount records your answer automatically. Recent or current use is shown as a hypothetical former-smoker scenario; it is not treated as a validated prediction for your current situation.')

supplied = sum(isinstance(v, dict) or v in questions[f]['options'] for f, v in answers.items())
gates_answered = sum(v is not None for v in eligibility)
st.progress((supplied+gates_answered)/(len(features)+4), text=f'{supplied} of {len(features)} answers entered · {gates_answered} of 4 profile questions')
st.caption('More usable answers give the model more context. You can continue with partial answers; with no usable model answers, we show the study reference instead.')
signature = json.dumps({'adapter': 'available_answers_v1', 'profile': preset, 'answers': answers, 'eligibility': eligibility}, sort_keys=True)
if st.session_state.get('assessment_signature') != signature:
    st.session_state.pop('assessment_result', None)
    st.session_state['assessment_signature'] = signature

submitted = st.button('See my complete outlook →', type='primary', width='stretch', key='predict_assessment')
st.caption('All supported month horizons are included automatically. No account or contact information is needed.')
if submitted:
    try:
        with st.spinner('Building your outlook and explaining the factors…'):
            st.session_state['assessment_result'] = assess_available(ROOT, bundle, answers, eligibility)
    except (BoundaryError, ValueError) as error:
        st.error(str(error))

output = st.session_state.get('assessment_result')
if output:
    st.divider()
    st.markdown('## '+('Your outlook, over time' if output['estimate_mode'] == 'assessment' else 'Your conditional scenario outlook' if output['estimate_mode'] != 'study_reference' else 'The study reference outlook'))
    if output['estimate_mode'] == 'study_reference':
        st.info('No usable model answers were supplied, so this is the fitted study reference—not a personalized prediction. Add answers to build a more informed scenario.')
    elif output['estimate_mode'] == 'scenario':
        st.info('This is a hypothetical scenario for an adult former established smoker who has quit for more than 30 days, using your compatible answers. The model has not been validated for your reported profile; this is not a personal forecast for current smoking, recent use, never-smokers or minors.')
    elif output['estimate_mode'] == 'profile_unconfirmed':
        st.info('This estimate assumes an adult former established smoker with no current or past-30-day smoking. Some profile answers are unknown, so it is a conditional scenario rather than a confirmed profile match.')
    if output['excluded_inputs']:
        st.caption('Your recent-use duration was retained in your answer summary but excluded from this quit-for-over-30-days scenario. The model uses its fitted missing-value handling for that input.')
    st.caption('Estimated first reported return to current smoking. Each percentage is cumulative by that approximate month horizon, not an additional monthly risk.')
    a, b, c = st.columns(3)
    a.metric(f'Chance by approx. {output["horizon_months"]} months', f'{100*output["probability"]:.1f}%')
    b.metric(f'Relative risk · {output["risk_reference_months"]} months', output['risk_level'])
    if output['median_months'] is not None:
        c.metric('Approximate median observation time', f'{round(output["median_months"])} months')
    else:
        c.metric('Median observation time', f'Not reached by {output["conditional_window_months"]} months')
    reliability = output['reliability']
    with st.container(border=True, key='reliability_card'):
        st.markdown('### How reliable is this estimate?')
        st.html(f'<div class="reliability-grid"><div class="reliability-tile evidence"><small>MODEL EVIDENCE</small><strong>{escape(reliability["label"])}</strong><span>Imperfect calibration & approximate timing</span></div><div class="reliability-tile coverage"><small>USABLE ANSWER COVERAGE</small><strong>{reliability["answer_coverage_percent"]:.0f}%</strong><span>{output["provided"]} of {output["expected"]} model inputs · not confidence</span></div><div class="reliability-tile scope"><small>PROFILE SUPPORT</small><strong>{escape(output["profile_support"])}</strong><span>Population match determines interpretation</span></div></div>')
        st.write('A validated personal “percent sure” score is unavailable. Even complete answers do not make a forecast certain.')
        interval = reliability['test_roc_auc_95_interval']
        interval_text = f' (95% participant-bootstrap interval {interval[0]:.3f}–{interval[1]:.3f})' if interval else ''
        evidence_name = 'questionnaire model' if output['provided'] else 'no-input study baseline'
        st.caption(f'At {output["horizon_months"]} months, the {evidence_name} had held-out ROC-AUC {reliability["test_roc_auc"]:.3f}{interval_text}. This is group-level discrimination, not your chance of the prediction being correct or validation for a partial/out-of-profile scenario. Mean predicted risk was {100*reliability["test_mean_probability"]:.1f}% versus {100*reliability["test_observed_risk"]:.1f}% observed after censoring adjustment.')
    outlook_tab, factors_tab, details_tab = st.tabs(['Probability timeline', 'Contributing factors', 'How to read your result'])
    with outlook_tab:
        cards = ''.join(f'<div class="outlook-card {"featured" if p["months"] == 18 else ""}"><dt>Within ≈ {p["months"]} months</dt><dd>{100*p["probability"]:.1f}%</dd><small>Cumulative probability</small></div>' for p in output['curve'])
        st.html('<dl class="outlook-grid" aria-label="Probabilities by approximate follow-up horizon">'+cards+'</dl>')
        chart_data = pd.DataFrame(output['curve']).assign(percentage=lambda f: 100*f['probability'])
        base = alt.Chart(chart_data).encode(
            x=alt.X('months:Q', title='Approximate months from your assessment', axis=alt.Axis(values=[p['months'] for p in output['curve']], grid=False)),
            y=alt.Y('percentage:Q', title='Cumulative probability (%)', scale=alt.Scale(domain=[0, 100])),
            tooltip=[alt.Tooltip('months:Q', title='Approximate months'), alt.Tooltip('percentage:Q', title='Probability (%)', format='.1f')])
        chart = (base.mark_area(color='#087f72', opacity=.08)+base.mark_line(color='#087f72', strokeWidth=3, point=alt.OverlayMarkDef(size=65, filled=True))).properties(height=280).configure_view(strokeWidth=0)
        st.altair_chart(chart, width='stretch')
        if output['median_months'] is None:
            st.write(f'The modeled probability does **not reach 50% within {output["conditional_window_months"]} months**. A return is therefore not predicted as more likely than not within that window.')
        st.html(f'<div class="note"><strong>About the timing:</strong> if a return is observed within {output["conditional_window_months"]} months, the model’s conditional median observation time is approximately <strong>{round(output["conditional_median_months"])} months</strong>. This conditional estimate does not mean a return is likely for the person represented by this scenario. Month estimates use assumed survey timing, not a measured first-cigarette date.</div>')
    with factors_tab:
        st.write(f'These factors explain your **{output["horizon_months"]}-month probability**, relative to a fixed model reference. They show model associations, not causes.')
        table = pd.DataFrame([{'Factor': labels[f['feature']], 'Contribution': 100*f['contribution']} for f in output['factors']], columns=['Factor', 'Contribution'])
        if output['provided'] == 0:
            st.info('The study reference has no personalized contributing factors because no usable model answers were supplied.')
        factors_chart = alt.Chart(table).mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X('Contribution:Q', title='Contribution to probability (percentage points)'),
            y=alt.Y('Factor:N', sort=table['Factor'].tolist(), title=None),
            color=alt.condition(alt.datum.Contribution > 0, alt.value('#b56c3e'), alt.value('#087f72')),
            tooltip=['Factor', alt.Tooltip('Contribution:Q', format='+.2f', title='Percentage points')]).properties(height=320).configure_view(strokeWidth=0)
        if not table.empty:
            st.altair_chart(factors_chart, width='stretch')
        st.caption('Right / warm bars increase the estimate; left / teal bars decrease it. Changing an answer does not establish a real-world benefit or harm.')
        st.caption(f'Reference estimate {100*output["explanation_reference"]:.2f}% + all contributions = {100*output["probability"]:.2f}% before rounding. Exact Shapley values explain the same displayed probability.')
        with st.expander('See every contribution'):
            st.dataframe(table.rename(columns={'Contribution': 'Contribution (percentage points)'}), hide_index=True, width='stretch')
    with details_tab:
        low, high = output['risk_cuts']
        st.write(f'**Risk level:** a relative category using the {output["risk_reference_months"]}-month score. Lower ≤ {100*low:.2f}%; moderate through {100*high:.2f}%; higher above that. These are project-defined groups, not medical thresholds.')
        st.write('**Timing:** approximate months use survey-window midpoints. Smoking may resume before it is reported; brief episodes between surveys can be missed. A reported return does not prove persistent smoking.')
        st.write(f'**Your answers:** {output["provided"]} of {output["expected"]} model inputs supplied. Missing answers use fitted missing-value handling; completeness is not confidence.')
        st.dataframe(pd.DataFrame(displayed), hide_index=True, width='stretch')
        with st.expander('Technical prediction record'):
            st.json(output)

st.divider()
with st.expander('Research evidence & limitations'):
    st.markdown('### Built on consecutive-wave follow-up')
    st.write(f'{summary["people"]:,} former established smokers with at least three consecutive surveys: {summary["observed_returns"]:,} first observed returns to current-established smoking, and {summary["no_return_observed_before_followup_ended"]:,} without an observed return before follow-up ended. No observed return is not a permanent negative label.')
    st.write('Model: consecutive-wave Weibull survival model, using baseline answers only. Participants are separated for fitting, selection, calibration and testing. Evaluation retains observed class proportions.')
    rows = []
    for horizon in results['supported_horizons_months']:
        m = results['metrics'][str(horizon)]['model']
        if m['supported']:
            rows.append({'Approximate months': horizon, 'ROC-AUC (IPCW)': m['ipcw_roc_auc'], 'Brier score': m['ipcw_brier'], 'Mean estimate (%)': 100*m['mean_predicted_risk'], 'Observed risk (IPCW %)': 100*m['ipcw_observed_risk']})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
    st.caption('IPCW adjusts aggregate evaluation for censoring under an independent-censoring assumption. These measurements do not validate actual month-of-resumption predictions.')
    st.write('Consecutive attendance selects people using future participation. Attrition can be informative. This unweighted U.S. study does not establish performance for current app users, other populations, or clinical decisions. Current-established means every-day or some-day smoking; it does not establish persistent smoking.')
    st.markdown('[FDA wave collection dates]('+config['timing_source']+')')
    st.caption('Local documentation: docs/longitudinal_v2.md · reports/longitudinal_v2_1/results.json')
reference = results['metrics'][str(config['default_horizon_months'])]['model']
st.caption(f'Probability limitation: at {config["default_horizon_months"]} months, the mean held-out estimate was {100*reference["mean_predicted_risk"]:.1f}% versus {100*reference["ipcw_observed_risk"]:.1f}% censor-adjusted observed risk. The model underestimates average risk; percentages are not precise personal probabilities.')
st.html('<div class="page-footer"><span>reclaim / CSE366 · Consecutive-wave research model</span><span>Local inference · No answer files · No external prediction API</span></div>')
