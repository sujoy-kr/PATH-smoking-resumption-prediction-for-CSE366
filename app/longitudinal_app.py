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
from path_project.study import load_study
from path_project.assessment import assess_available, route

st.set_page_config(page_title='Reclaim · Your smoking outlook', page_icon='◈', layout='wide', initial_sidebar_state='collapsed')
st.html('<style>'+(ROOT/'app/styles.css').read_text()+'</style>')


@st.cache_resource(show_spinner=False)
def engine():
    return load_study(ROOT)


def heading(number, title, copy):
    st.html(f'<div class="section-heading"><span class="step">{number}</span><h2>{escape(title)}</h2></div><p class="section-copy">{escape(copy)}</p>')


st.html('<div class="brand"><div class="brand-name"><span class="brand-mark">↗</span>reclaim<span style="color:#8a9da8;font-weight:400"> / </span></div><div class="brand-meta">Your quit journey, in perspective</div></div>')
st.html('''<section class="hero"><div class="eyebrow">A clearer view of what comes next</div>
<h1>Where are you on your smoking journey?<br>Understand your outlook.</h1>
<p>Whether you have quit, still smoke or have never smoked regularly, answer a few questions to see the estimated chance of what happens next (returning, stopping or starting) over time, and the factors behind it.</p>
<div class="hero-chips"><span>Up to 10 questions + 4 profile questions</span><span>No account needed</span><span>Answers stay in this session</span></div></section>''')
st.caption('Survey-based research estimate · Months are approximate: a return is only known to fall between two survey interviews. Personal and clinical accuracy are unvalidated.')

try:
    bundle = engine()
except Exception:  # unreadable/incompatible pickle, dependency mismatch, tampered files
    st.error('The assessment is temporarily unavailable because the local model could not be verified. No substitute prediction is shown.')
    st.stop()

question_spec = json.loads((ROOT/'configs/app_questions.json').read_text())
inputs = json.loads((ROOT/'configs/inputs_v2_4.json').read_text())
config = bundle['config']
FILL = {'age_band': '3', 'education_level': '3', 'employment_status': '1', 'electronic_nicotine_p30d': '0',
    'household_tobacco_any': '0', 'mental_health': '3', 'emotional_problems_7d': '3', 'sex_recorded': '2',
    'home_combustible_smoking_rules': '2', 'physical_health': '3', 'social_satisfaction': '3',
    'traditional_cigar_p30d': '0', 'cigarillo_p30d': '0', 'filtered_cigar_p30d': '0', 'hookah_p30d': '0',
    'smokeless_tobacco_p30d': '0', 'snus_p30d': '0', 'depressive_problem_recency': '4', 'anxiety_problem_recency': '4',
    'alcohol_days_30d': 4, 'alcohol_drinks_per_drinking_day': 2,
    'prior_regular_cigarettes_per_day': {'number': 1, 'unit': '2'}, 'regular_smoking_months': {'number': 10, 'unit': '2'},
    'cigarettes_per_day': {'number': 10, 'unit': '1'}, 'minutes_to_first_cigarette': {'number': 30, 'unit': '1'},
    'tried_to_quit_12m': '1', 'quit_plan_timeframe': '4', 'tobacco_addiction_self': '2'}
GATES_QUIT = ['Yes', 'Yes', 'Not at all', 'No']
presets = {
    'My assessment': {},
    'Example · current smoker': {**FILL, '_gates': ['Yes', 'Yes', 'Every day', 'Yes'], 'electronic_nicotine_p30d': '1', 'household_tobacco_any': '1'},
    'Example · never smoked regularly': {**FILL, '_gates': ['Yes', 'No', 'Not at all', 'No'], 'age_band': '1', 'electronic_nicotine_p30d': '1'},
    'Example · recent quit': {**FILL, '_gates': GATES_QUIT, 'last_cigarette_recency_days': {'number': 6, 'unit': '2'},
        'electronic_nicotine_p30d': '1', 'household_tobacco_any': '1', 'mental_health': '4', 'emotional_problems_7d': '4'},
    'Example · longer quit': {**FILL, '_gates': GATES_QUIT, 'age_band': '5', 'education_level': '5',
        'last_cigarette_recency_days': {'number': 8, 'unit': '3'}, 'mental_health': '2', 'emotional_problems_7d': '2'}
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
                index=q['options'].index(example['_gates'][i]) if example else None,
                horizontal=True, key=f'{prefix}_gate_{i}')
            eligibility.append(value)

population, context_flag = route(eligibility)
pop = bundle['populations'].get(population) if population else None
features = pop['model'].features if pop else []
answers, displayed = {}, []
HELP = {'mental_health': 'Includes stress, depression and problems with emotions.',
        'emotional_problems_7d': 'For example, anxiety, depression or irritability.',
        'household_tobacco_any': 'Includes cigarettes, cigars, electronic nicotine and other tobacco/nicotine products.'}
with st.container(border=True, key='situation_card'):
    heading('02', 'A little about your current situation', 'Answer what you can. Unknown answers use the model’s fitted missing-value handling, with reduced personal support.')
    if pop is None:
        _, reason = route(eligibility)
        st.info('Answer the four profile questions above so we can choose the model fitted for your situation. ' + (reason if isinstance(reason, str) else ''))
    else:
        st.caption(f'Model used: **{pop["spec"]["label"]}** · outcome: {pop["spec"]["outcome_long"]}.')
    columns = st.columns(2, gap='large')
    for i, feature in enumerate(features):
        item, raw = inputs[feature], example.get(feature)
        key = f'{prefix}_{feature}'
        with columns[i % 2]:
            if item['kind'] == 'category':
                options = {**item['options'], 'dont_know': 'Not sure / prefer not to say'}
                if feature == 'household_tobacco_any':
                    options['not_applicable'] = 'I live alone / not applicable'
                value = st.radio(item['prompt'], list(options), format_func=lambda v, o=options: o[v],
                    index=list(options).index(raw) if raw is not None else None, key=key,
                    horizontal=len(options) <= 4, help=HELP.get(feature))
                answers[feature] = value if value is not None else 'unanswered'
                shown = options[value] if value is not None else 'Not answered'
            elif item['kind'] == 'number':
                if key not in st.session_state and raw is not None:
                    st.session_state[key] = raw
                number = st.number_input(item['prompt'], min_value=item['minimum'], max_value=item['maximum'], step=1,
                    value=None, placeholder='Enter a whole number', key=key)
                answers[feature] = int(number) if number is not None else 'unanswered'
                shown = f'{number}' if number is not None else 'Not answered'
            else:
                if key not in st.session_state and raw is not None:
                    st.session_state[key] = raw['number']
                st.markdown(f'**{item["prompt"]}**')
                left, right = st.columns([1, 2], gap='small')
                number = left.number_input('Amount', min_value=1, max_value=999, step=1, value=None,
                    placeholder='Whole number', key=key, label_visibility='collapsed')
                units = {k: v[0] for k, v in item['units'].items()}
                unit = right.radio('Unit', list(units), format_func=lambda v, u=units: u[v],
                    index=list(units).index(raw['unit'] if raw else item['default_unit']), horizontal=True,
                    key=key+'_unit', label_visibility='collapsed')
                answers[feature] = {'number': number, 'unit': unit} if number is not None else 'unanswered'
                shown = f'{number} {units[unit].lower()}' if number is not None else 'Not answered'
        displayed.append({'Question': item['prompt'], 'Answer': shown})
    if 'last_cigarette_recency_days' in features:
        st.caption('Your last-cigarette answer must agree with your past-30-day smoking answer above.')

supplied = sum(v != 'unanswered' and v not in ('dont_know', 'prefer_not_to_answer', 'not_applicable') for v in answers.values())
gates_answered = sum(v is not None for v in eligibility)
st.progress((supplied+gates_answered)/(len(features)+4), text=f'{supplied} of {len(features)} answers entered · {gates_answered} of 4 profile questions')
if pop:
    need = -(-int(len(features)*config['minimum_answers_fraction']*100)//100)
    st.caption(f'A personalized estimate needs {"the time since your last cigarette and " if "last_cigarette_recency_days" in features else ""}at least {need} of {len(features)} answers (“not sure” counts as unanswered). With fewer, no probability is shown.')
signature = json.dumps({'adapter': 'available_answers_v1', 'profile': preset, 'answers': answers, 'eligibility': eligibility}, sort_keys=True)
if st.session_state.get('assessment_signature') != signature:
    st.session_state.pop('assessment_result', None)
    st.session_state['assessment_signature'] = signature

submitted = st.button('See my complete outlook →', type='primary', width='stretch', key='predict_assessment')
st.caption('All horizons supported by validation evidence are included automatically. No account or contact information is needed.')
if submitted:
    try:
        with st.spinner('Building your outlook and explaining the factors…'):
            st.session_state['assessment_result'] = assess_available(ROOT, bundle, answers, eligibility)
    except (BoundaryError, ValueError) as error:
        st.error(str(error))

output = st.session_state.get('assessment_result')
if output:
    st.divider()
    if output['status'] == 'suppressed':
        st.warning(output['reason'])
        st.stop()
    results, summary = bundle['populations'][output['population']]['results'], bundle['populations'][output['population']]['summary']
    meaning = {'former': 'more likely to return to smoking', 'current': 'more likely to stop smoking', 'never': 'more likely to become a regular smoker'}[output['population']]
    st.markdown(f'## Your outlook · chance of {output["outcome"]}')
    st.caption(f'Model: {output["population_label"]}. “Higher” means {meaning}.')
    if output['estimate_mode'] == 'profile_unconfirmed':
        st.info('Some profile answers (such as age or past-30-day smoking) are unknown, so this assumes you belong to the study population above. It is a conditional estimate rather than a confirmed profile match.')
    weak = [h for h, e in output['horizon_evidence'].items() if not e['beats_no_input_baseline']]
    if weak:
        st.warning('Short horizons are the least reliable: at ≈ ' + ', '.join(weak) + ' months the model did not beat a no-information baseline on held-out data. Treat those percentages as uninformative; use the longer horizons.')
    st.caption(f'Outcome: {output["outcome_long"]}. Each percentage is cumulative by that approximate month horizon, not an additional monthly risk.')
    a, b, c = st.columns(3)
    a.metric(f'Chance by approx. {output["horizon_months"]} months', f'{100*output["probability"]:.1f}%')
    lo_p, hi_p = output['probability_interval']
    a.caption(f'{100*output["interval_level"]:.0f}% uncertainty range: **{100*lo_p:.1f}–{100*hi_p:.1f}%**')
    b.metric(f'Relative level · {output["risk_reference_months"]} months', output['risk_level'])
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
        st.caption(f'At {output["horizon_months"]} months, the {evidence_name} had held-out ROC-AUC {reliability["test_roc_auc"]:.3f}{interval_text}. This is group-level discrimination, not your chance of the prediction being correct or validation for a partial/out-of-profile scenario. Mean predicted risk was {100*reliability["test_mean_probability"]:.1f}% versus an observed range of {100*reliability["test_observed_risk_bounds"][0]:.1f}–{100*reliability["test_observed_risk_bounds"][1]:.1f}%.')
    outlook_tab, factors_tab, details_tab = st.tabs(['Probability timeline', 'Contributing factors', 'How to read your result'])
    with outlook_tab:
        cards = ''.join(f'<div class="outlook-card {"featured" if p["months"] == 18 else ""}"><dt>Within ≈ {p["months"]} months</dt><dd>{100*p["probability"]:.1f}%</dd><small>{100*p["low"]:.0f}–{100*p["high"]:.0f}% range · </small><small>{"Cumulative · not better than baseline" if not output["horizon_evidence"][str(p["months"])]["beats_no_input_baseline"] else "Cumulative probability"}</small></div>' for p in output['curve'])
        st.html('<dl class="outlook-grid" aria-label="Probabilities by approximate follow-up horizon">'+cards+'</dl>')
        chart_data = pd.DataFrame(output['curve']).assign(percentage=lambda f: 100*f['probability'], low_pct=lambda f: 100*f['low'], high_pct=lambda f: 100*f['high'])
        base = alt.Chart(chart_data).encode(
            x=alt.X('months:Q', title='Approximate months from your assessment', axis=alt.Axis(values=[p['months'] for p in output['curve']], grid=False)),
            y=alt.Y('percentage:Q', title='Cumulative probability (%)', scale=alt.Scale(domain=[0, 100])),
            tooltip=[alt.Tooltip('months:Q', title='Approximate months'), alt.Tooltip('percentage:Q', title='Probability (%)', format='.1f')])
        band = alt.Chart(chart_data).mark_area(color='#087f72', opacity=.16).encode(x='months:Q', y=alt.Y('low_pct:Q', scale=alt.Scale(domain=[0, 100])), y2='high_pct:Q')
        chart = (band+base.mark_line(color='#087f72', strokeWidth=3, point=alt.OverlayMarkDef(size=65, filled=True))).properties(height=280).configure_view(strokeWidth=0)
        st.altair_chart(chart, width='stretch')
        st.caption(f'Shaded band and ranges: {100*output["interval_level"]:.0f}% interval from {bundle["populations"][output["population"]]["results"]["prediction_interval"]["replicates"]} bootstrap refits of the model. It shows how much the estimate could shift with different training samples; it is not a range for what will happen to one person and does not cover model misspecification.')
        if output['median_months'] is None:
            st.write(f'The modeled probability does **not reach 50% within {output["conditional_window_months"]} months**. A return is therefore not predicted as more likely than not within that window.')
        st.html(f'<div class="note"><strong>About the timing:</strong> if the outcome is observed within {output["conditional_window_months"]} months, the model’s conditional median observation time is approximately <strong>{round(output["conditional_median_months"])} months</strong>. This conditional estimate does not mean a return is likely for the person represented by this scenario. Month estimates use assumed survey timing, not a measured first-cigarette date.</div>')
    with factors_tab:
        st.write(f'These factors explain your **{output["horizon_months"]}-month probability**, relative to a fixed model reference. They show model associations, not causes.')
        table = pd.DataFrame([{'Factor': results['selected_groups'][f['feature']]['label'], 'Contribution': 100*f['contribution']} for f in output['factors']], columns=['Factor', 'Contribution'])
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
        st.write('**Timing:** approximate months use survey-window midpoints. Changes may happen before they are reported; brief episodes between surveys can be missed. A reported event does not prove a lasting change.')
        st.write(f'**Your answers:** {output["provided"]} of {output["expected"]} model inputs supplied. Missing answers use fitted missing-value handling; completeness is not confidence.')
        st.dataframe(pd.DataFrame(displayed), hide_index=True, width='stretch')
        with st.expander('Technical prediction record'):
            st.json(output)

if output and output['status'] == 'scored':
    st.divider()
    with st.expander('Research evidence & limitations'):
        st.markdown('### Built on PATH Study follow-up')
        st.write(f'{summary["people"]:,} people in the “{output["population_label"]}” group with at least one follow-up interview: {summary["events"]:,} first reported events ({output["outcome_long"]}) and {summary["no_event_observed_before_followup_ended"]:,} without an observed event before follow-up ended. No observed event is not a permanent negative label.')
        st.write('Model: interval-censored proportional-hazards survival model with a flexible baseline hazard, using baseline answers only. Participants are separated for fitting, selection, calibration and testing. Evaluation retains observed class proportions.')
        rows = []
        for horizon in results['supported_horizons_months']:
            m = results['metrics'][str(horizon)]['model']
            if m['supported']:
                rows.append({'Approximate months': horizon, 'ROC-AUC (IPCW)': m['ipcw_roc_auc'], 'Brier score': m['ipcw_brier'], 'Mean estimate (%)': 100*m['mean_predicted_risk'], 'Observed risk range (%)': f"{100*m['observed_risk_lower']:.1f}–{100*m['observed_risk_upper']:.1f}", 'Estimate within range': 'yes' if m['predicted_within_observed_bounds'] else 'no'})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
        st.caption('A return is known only to lie between interviews, so observed risk at a horizon is a range (lower: returns known by then; upper: also returns that began before it). IPCW weights adjust for lost follow-up by baseline wave. These measurements do not validate actual month-of-resumption predictions.')
        st.write('People are included if they had at least one follow-up interview; later attendance never affects inclusion, but attrition can still be informative. This unweighted U.S. study does not establish performance for current app users, other populations, or clinical decisions. Current-established means every-day or some-day smoking; it does not establish persistent smoking.')
        st.markdown('[FDA wave collection dates]('+config['timing_source']+')')
        st.caption('Local documentation: docs/longitudinal_v2_4.md · reports/longitudinal_v2_4/results.json')
    reference = results['metrics'][str(config['default_horizon_months'])]['model']
    low, high = reference['observed_risk_lower'], reference['observed_risk_upper']
    inside = 'inside' if reference['predicted_within_observed_bounds'] else 'outside'
    outside = [h for h in results['supported_horizons_months'] if not results['metrics'][str(h)]['model']['predicted_within_observed_bounds']]
    st.caption(f'Calibration: at {config["default_horizon_months"]} months the mean held-out estimate was {100*reference["mean_predicted_risk"]:.1f}%, {inside} the {100*low:.1f}–{100*high:.1f}% observed-risk range' + (f'; it fell outside the range at ≈ {", ".join(map(str, outside))} months' if outside else '') + '. Percentages are not precise personal probabilities.')
    if reference['mean_predicted_risk'] > reference['observed_risk_upper']:
        st.warning(f'Heads-up: for this group the average estimate at {config["default_horizon_months"]} months is above the simple observed-risk range, so absolute percentages may be somewhat high. Rankings and comparisons between answers are more reliable than the exact number.')
st.html('<div class="page-footer"><span>reclaim / CSE366 · Interval-censored research model</span><span>Local inference · No answer files · No external prediction API</span></div>')
