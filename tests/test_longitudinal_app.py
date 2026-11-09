"""Actual UI regressions with fictional profiles; no held-out data access."""
from pathlib import Path
import json
import sys
import pytest
from streamlit.testing.v1 import AppTest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from path_project.study import load_study
from path_project.evaluation import BoundaryError


def launch(profile=None):
    app = AppTest.from_file(str(ROOT/'app/streamlit_app.py'), default_timeout=120).run()
    assert not app.exception
    if profile:
        app.radio(key='assessment_profile').set_value(profile).run()
    return app


def submit(app):
    return app.button(key='predict_assessment').click().run(timeout=120)


def fixture(name):
    data = json.loads((ROOT/'tests/fixtures/handoff_profiles.json').read_text())
    return next(c for c in data['profiles'] if c['name'] == name)


def record(app):
    return json.loads(app.json[0].value)


def test_blank_submission_shows_no_result_and_no_dropdowns():
    app = launch()
    assert not app.sidebar.radio
    assert not app.selectbox and not app.text_input
    assert not any('Show the chance' in r.label for r in app.radio)
    submit(app)
    assert not app.exception and not app.error
    assert not app.json and not app.metric
    assert any('Please answer' in w.value for w in app.warning)


@pytest.mark.parametrize('profile', ['Example · recent quit', 'Example · longer quit'])
def test_automatic_full_curve_and_matching_probability_factors(profile):
    app = launch(profile)
    submit(app)
    assert not app.exception and len(app.metric) == 3
    output = record(app)
    assert output['status'] == 'scored' and output['horizon_months'] == 36
    shown = load_study(ROOT)['populations'][output['population']]['results']['supported_horizons_months']
    assert [p['months'] for p in output['curve']] == shown
    assert all(p['low'] <= p['probability'] <= p['high'] for p in output['curve'])
    lo, hi = output['probability_interval']
    assert lo <= output['probability'] <= hi
    assert app.metric[0].value == f"{100*output['probability']:.1f}%"
    assert app.metric[1].value == output['risk_level']
    assert output['explanation_reference']+sum(f['contribution'] for f in output['factors']) == pytest.approx(output['probability'], abs=1e-8)
    assert 0 < output['conditional_median_months'] < output['conditional_window_months']
    assert output['provided'] == output['expected']
    assert not app.error
    # Editing an answer clears the previously computed result.
    app.radio(key=profile+'_mental_health').set_value('1').run()
    assert not app.metric
    submit(app)
    assert not app.error and record(app)['provided'] == record(app)['expected']
    app.radio(key='assessment_profile').set_value('My assessment').run()
    assert not app.metric


def test_manual_complete_answers_work_for_every_question_type():
    app = launch()
    spec = json.loads((ROOT/'configs/app_questions.json').read_text())
    for i, gate in enumerate(spec['eligibility_questions']):
        app.radio(key=f'My assessment_gate_{i}').set_value(gate['required_answer'])
    app.run()  # the question list depends on the routed population
    inputs = json.loads((ROOT/'configs/inputs_v2_4.json').read_text())
    features = load_study(ROOT)['populations']['former']['model'].features
    for feature in features:
        item, key = inputs[feature], 'My assessment_'+feature
        if item['kind'] == 'category':
            app.radio(key=key).set_value(list(item['options'])[0])
        elif item['kind'] == 'number':
            app.number_input(key=key).set_value(int(max(item['minimum'], 1)))
        else:
            app.number_input(key=key).set_value(5)
    submit(app)
    assert not app.exception and not app.error
    assert record(app)['provided'] == len(features) and record(app)['status'] == 'scored'
    assert app.progress[0].value == 100


def test_eligibility_conflict_specific_errors_and_correction():
    profile = 'Example · recent quit'
    app = launch(profile)
    app.radio(key=profile+'_gate_3').set_value('Yes')
    submit(app)
    assert not app.exception and not app.error
    assert any('conflict' in w.value for w in app.warning)
    assert not app.json
    app.radio(key=profile+'_gate_3').set_value('No').run()
    assert not app.error
    app.radio(key=profile+'_last_cigarette_recency_days_unit').set_value('1')
    app.number_input(key=profile+'_last_cigarette_recency_days').set_value(2)
    submit(app)
    assert not app.exception and not app.error
    assert any('conflict' in w.value for w in app.warning)
    app.radio(key=profile+'_last_cigarette_recency_days_unit').set_value('2').run()
    assert not app.error
    submit(app)
    assert not app.error and record(app)['provided'] == record(app)['expected']


def test_unknown_answers_are_optional_and_missing_number_is_explicit():
    profile = 'Example · recent quit'
    app = launch(profile)
    app.radio(key=profile+'_education_level').set_value('dont_know')
    app.radio(key=profile+'_household_tobacco_any').set_value('not_applicable')
    submit(app)
    assert not app.error and record(app)['provided'] == record(app)['expected']-2
    app.number_input(key=profile+'_last_cigarette_recency_days').set_value(None)
    submit(app)
    assert not app.exception and not app.error
    assert any('time since your last cigarette' in w.value for w in app.warning)


def test_too_few_answers_are_suppressed_not_scored():
    app = launch()
    for i, answer in enumerate(['Yes', 'Yes', 'Not at all', 'No']):
        app.radio(key=f'My assessment_gate_{i}').set_value(answer)
    app.run()
    app.radio(key='My assessment_age_band').set_value('3')
    submit(app)
    assert not app.exception and not app.error
    assert any('at least' in w.value and 'answers' in w.value for w in app.warning)
    assert not app.json and not app.metric


def test_reliability_never_claims_personal_confidence_and_drops_unsupported_horizon():
    app = launch('Example · recent quit')
    submit(app)
    output = record(app)
    assert output['estimate_mode'] == 'assessment'
    assert output['reliability']['personal_confidence_percent'] is None
    assert output['reliability']['label'] == 'Limited'
    assert all(e['beats_no_input_baseline'] for e in output['horizon_evidence'].values())
    shown = load_study(ROOT)['populations'][output['population']]['results']['supported_horizons_months']
    assert [p['months'] for p in output['curve']] == shown
    assert all(p['low'] <= p['probability'] <= p['high'] for p in output['curve'])
    lo, hi = output['probability_interval']
    assert lo <= output['probability'] <= hi
    assert any('percent sure' in m.value for m in app.markdown)


def test_every_adult_profile_is_routed_to_its_own_model_or_explained():
    from path_project.assessment import assess_available
    bundle = load_study(ROOT)
    run = lambda a, g: assess_available(ROOT, bundle, a, g)
    quit_answers = fixture('fictional_recent_quit')['answers']
    full = fixture('fictional_current_smoker')['answers']
    r = run(quit_answers, ['Yes', 'Yes', 'Not at all', 'No'])
    assert (r['status'], r['population'], r['estimate_mode']) == ('scored', 'former', 'assessment')
    assert run(fixture('fictional_just_quit_20_days')['answers'], ['Yes', 'Yes', 'Not at all', 'Yes'])['population'] == 'former'
    assert run(full, ['Yes', 'Yes', 'Every day', 'Yes'])['population'] == 'current'
    assert run(full, ['Yes', 'Yes', 'Some days', 'No'])['population'] == 'current'
    assert run(full, ['Yes', 'No', 'Not at all', 'No'])['population'] == 'never'
    assert run(full, ['Yes', 'No', 'Every day', 'Yes'])['population'] == 'never'
    assert run(quit_answers, [None, 'Yes', 'Not at all', 'No'])['estimate_mode'] == 'profile_unconfirmed'
    assert run(quit_answers, ['Yes', "Don't know / prefer not to answer", 'Not at all', 'No'])['status'] == 'suppressed'
    assert 'under 18' in run(quit_answers, ['No', 'Yes', 'Not at all', 'No'])['reason']
    assert 'conflict' in run(quit_answers, ['Yes', 'Yes', 'Not at all', 'Yes'])['reason']
    assert run({**quit_answers, 'last_cigarette_recency_days': {'number': 5, 'unit': '1'}}, ['Yes', 'Yes', 'Not at all', 'No'])['status'] == 'suppressed'
    assert run({**quit_answers, 'alcohol_days_30d': 'dont_know', 'alcohol_drinks_per_drinking_day': 'not_applicable'}, ['Yes', 'Yes', 'Not at all', 'No'])['status'] == 'scored'


def test_outcome_direction_is_labelled_per_population():
    from path_project.assessment import assess_available
    bundle = load_study(ROOT)
    r = assess_available(ROOT, bundle, fixture('fictional_current_smoker')['answers'], ['Yes', 'Yes', 'Every day', 'Yes'])
    assert r['outcome'] == 'stopping smoking' and 'last_cigarette_recency_days' not in r['features']
    assert r['reliability']['test_roc_auc'] > .6


@pytest.mark.parametrize('profile,population', [('Example · current smoker', 'current'), ('Example · never smoked regularly', 'never')])
def test_ui_examples_for_other_populations(profile, population):
    app = launch(profile)
    submit(app)
    assert not app.exception and not app.error and len(app.metric) == 3
    assert record(app)['population'] == population and record(app)['status'] == 'scored'


def test_backend_guards_remain_intact():
    from path_project.assessment import assess_available
    bundle = load_study(ROOT)
    spec = json.loads((ROOT/'configs/app_questions.json').read_text())
    gates = [q['required_answer'] for q in spec['eligibility_questions']]
    with pytest.raises(BoundaryError, match='trained questionnaire'):
        assess_available(ROOT, bundle, {'PERSONID': 'FICTIONAL'}, gates)
    assert assess_available(ROOT, bundle, {}, gates)['status'] == 'suppressed'



def test_deploy_toolbar_disabled_and_responsive_styles_present():
    import tomllib
    config = tomllib.loads((ROOT/'.streamlit/config.toml').read_text())
    assert config['client']['toolbarMode'] == 'minimal'
    assert config['ui']['hideTopBar'] is True
    css = (ROOT/'app/styles.css').read_text()
    assert '@media (max-width: 640px)' in css
    assert 'prefers-reduced-motion' in css
