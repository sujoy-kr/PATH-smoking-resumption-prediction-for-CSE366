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


def record(app):
    return json.loads(app.json[0].value)


def test_single_model_no_editable_dropdowns_or_horizon_selector():
    app = launch()
    assert not app.sidebar.radio
    assert not app.selectbox and not app.text_input
    assert not any('Show the chance' in r.label for r in app.radio)
    submit(app)
    assert not app.exception and not app.error
    assert record(app)['estimate_mode'] == 'study_reference'
    assert record(app)['provided'] == 0
    assert record(app)['factors'] == []
    assert record(app)['reliability']['test_roc_auc'] == .5
    assert record(app)['reliability']['test_roc_auc_95_interval'] is None
    assert any('not a personalized prediction' in i.value for i in app.info)


@pytest.mark.parametrize('profile', ['Example · recent quit', 'Example · longer quit'])
def test_automatic_full_curve_and_matching_probability_factors(profile):
    app = launch(profile)
    submit(app)
    assert not app.exception and len(app.metric) == 3
    output = record(app)
    assert output['status'] == 'scored' and output['horizon_months'] == 36
    assert [p['months'] for p in output['curve']] == [18, 24, 36, 48, 60]
    assert app.metric[0].value == f"{100*output['probability']:.1f}%"
    assert app.metric[1].value == output['risk_level']
    assert output['explanation_reference']+sum(f['contribution'] for f in output['factors']) == pytest.approx(output['probability'], abs=1e-8)
    assert 0 < output['conditional_median_months'] < output['conditional_window_months']
    assert output['provided'] == 8
    assert not app.error
    # Editing an answer clears the previously computed result.
    app.radio(key=profile+'_mental_health').set_value('1').run()
    assert not app.metric
    submit(app)
    assert not app.error and record(app)['provided'] == 8
    app.radio(key='assessment_profile').set_value('My assessment').run()
    assert not app.metric


def test_manual_complete_answers_work_without_hidden_recency_toggle():
    app = launch()
    spec = json.loads((ROOT/'configs/app_questions.json').read_text())
    for i, gate in enumerate(spec['eligibility_questions']):
        app.radio(key=f'My assessment_gate_{i}').set_value(gate['required_answer'])
    values = {'age_band': '2', 'education_level': '4', 'employment_status': '1',
        'electronic_nicotine_p30d': '0', 'household_tobacco_any': '0',
        'mental_health': '2', 'emotional_problems_7d': '2'}
    for feature, value in values.items():
        app.radio(key='My assessment_'+feature).set_value(value)
    app.number_input(key='My assessment_recency_number').set_value(6)
    submit(app)
    assert not app.exception and not app.error
    assert record(app)['provided'] == 8
    assert app.progress[0].value == 100


def test_eligibility_conflict_specific_errors_and_correction():
    profile = 'Example · recent quit'
    app = launch(profile)
    app.radio(key=profile+'_gate_3').set_value('Yes')
    submit(app)
    assert not app.exception and not app.error
    assert any('outside that group' in w.value for w in app.warning)
    assert not app.json
    app.radio(key=profile+'_gate_3').set_value('No').run()
    assert not app.error
    app.radio(key=profile+'_recency_unit').set_value('1')
    app.number_input(key=profile+'_recency_number').set_value(2)
    submit(app)
    assert not app.exception and not app.error
    assert any('outside that group' in w.value for w in app.warning)
    app.radio(key=profile+'_recency_unit').set_value('2').run()
    assert not app.error
    submit(app)
    assert not app.error and record(app)['provided'] == 8


def test_unknown_answers_are_optional_and_missing_number_is_explicit():
    profile = 'Example · recent quit'
    app = launch(profile)
    app.radio(key=profile+'_education_level').set_value('dont_know')
    app.radio(key=profile+'_household_tobacco_any').set_value('not_applicable')
    submit(app)
    assert not app.error and record(app)['provided'] == 6
    app.number_input(key=profile+'_recency_number').set_value(None)
    submit(app)
    assert not app.exception and not app.error
    assert any('time since your last cigarette' in w.value for w in app.warning)


def test_too_few_answers_are_suppressed_not_scored():
    app = launch()
    app.radio(key='My assessment_age_band').set_value('3')
    submit(app)
    assert not app.exception and not app.error
    assert any('at least 6 of the 8' in w.value for w in app.warning)
    assert not app.json and not app.metric


def test_reliability_never_claims_personal_confidence_and_drops_unsupported_horizon():
    app = launch('Example · recent quit')
    submit(app)
    output = record(app)
    assert output['estimate_mode'] == 'assessment'
    assert output['reliability']['personal_confidence_percent'] is None
    assert output['reliability']['label'] == 'Limited'
    assert '12' not in output['horizon_evidence']
    assert all(e['beats_no_input_baseline'] for e in output['horizon_evidence'].values())
    assert [p['months'] for p in output['curve']] == [18, 24, 36, 48, 60]
    assert any('percent sure' in m.value for m in app.markdown)


def test_assessment_suppresses_out_of_profile_and_matches_gate_by_text():
    from path_project.assessment import assess_available
    bundle = load_study(ROOT)
    spec = json.loads((ROOT/'configs/app_questions.json').read_text())
    gates = [q['required_answer'] for q in spec['eligibility_questions']]
    answers = {'age_band': '2', 'education_level': '4', 'employment_status': '1',
        'last_cigarette_recency_days': {'number': 6, 'unit': '2'},
        'electronic_nicotine_p30d': '0', 'household_tobacco_any': '0',
        'mental_health': '2', 'emotional_problems_7d': '2'}
    assert assess_available(ROOT, bundle, answers, ['Yes', 'Yes', 'Some days', 'No'])['status'] == 'suppressed'
    unsure = [q['options'][-1] for q in spec['eligibility_questions']]
    assert assess_available(ROOT, bundle, answers, unsure)['estimate_mode'] == 'profile_unconfirmed'
    assert assess_available(ROOT, bundle, {**answers, 'last_cigarette_recency_days': {'number': 5, 'unit': '1'}}, gates)['status'] == 'suppressed'



def test_backend_guards_remain_intact():
    from path_project.assessment import assess_available
    bundle = load_study(ROOT)
    spec = json.loads((ROOT/'configs/app_questions.json').read_text())
    gates = [q['required_answer'] for q in spec['eligibility_questions']]
    with pytest.raises(BoundaryError, match='trained questionnaire'):
        assess_available(ROOT, bundle, {'PERSONID': 'FICTIONAL'}, gates)
    assert assess_available(ROOT, bundle, {}, gates)['estimate_mode'] == 'study_reference'



def test_deploy_toolbar_disabled_and_responsive_styles_present():
    import tomllib
    config = tomllib.loads((ROOT/'.streamlit/config.toml').read_text())
    assert config['client']['toolbarMode'] == 'minimal'
    assert config['ui']['hideTopBar'] is True
    css = (ROOT/'app/styles.css').read_text()
    assert '@media (max-width: 640px)' in css
    assert 'prefers-reduced-motion' in css
