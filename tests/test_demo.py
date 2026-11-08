"""Stage 12 UI tests: fictional profiles, frozen inference only."""
from pathlib import Path
import sys
import pytest
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.demo import load_demo_engine,read_json
from path_project.outputs import category_for


def launch(preset=None):
    app=AppTest.from_file(str(ROOT/'app/legacy_app.py'),default_timeout=120).run()
    assert not app.exception
    if preset:app.selectbox(key='preset').select(preset).run()
    return app


def test_blank_form_withholds_and_shows_actual_final_results():
    app=launch();app.button[0].click().run()
    assert not app.exception
    assert any('Confirm all cohort' in w.value for w in app.warning)
    assert not app.metric
    assert any('1,243' in m.value for m in app.markdown)
    assert any('Calibration was imperfect' in w.value for w in app.warning)


@pytest.mark.parametrize('preset',[
    'Fictional example · recent last use',
    'Fictional example · longer last use',
    'Fictional example · some unknown answers'])
def test_ui_matches_actual_frozen_probability_category_and_explanation(preset):
    app=launch(preset);app.button[0].click().run(timeout=120)
    assert not app.exception
    config=read_json(ROOT,'configs/demo.json');engine=load_demo_engine(ROOT)
    gates={k:q['required_answer'] for k,q in zip(engine.settings['eligibility_keys'],engine.gates)}
    output=engine.output(config['presets'][preset],gates,wave=7)
    assert app.metric[0].value==f"{100*output['probability']:.1f}%"
    assert app.metric[1].value==output['category']['label']
    assert output['category']['code']==category_for(output['probability'],engine.bands['cuts'])
    assert output['explanation']['reference_model_probability']+sum(f['contribution'] for f in output['contributing_factors'])==pytest.approx(output['probability'],abs=1e-8)
    import json
    identity=json.loads(app.json[0].value)
    assert identity['unrounded_probability']==output['probability']
    assert identity['model_version']==output['model_version']
    assert identity['explanation']['scale']=='calibrated_probability'
    table=app.dataframe[0].value
    assert table['Contribution (percentage points)'].tolist()==pytest.approx([100*f['contribution'] for f in output['contributing_factors']])
    assert not any('pending' in m.value for m in app.markdown)


def test_outside_cohort_and_invalid_recency_no_prediction():
    preset='Fictional example · recent last use';app=launch(preset)
    app.selectbox(key=preset+'_past30_use').select('Yes')
    app.button[0].click().run()
    assert not app.exception and not app.metric
    assert any('do not match' in w.value for w in app.warning)
    app.selectbox(key=preset+'_past30_use').select('No')
    app.selectbox(key=preset+'_unit').select('1')
    app.number_input[0].set_value(2)
    app.button[0].click().run()
    assert not app.exception and not app.metric
    assert any('conflicts' in e.value for e in app.error)


def test_two_input_guard_unknown_and_reset_does_not_retain_result():
    app=launch('Fictional example · some unknown answers')
    app.button[0].click().run();assert app.metric
    app.selectbox(key='preset').select('Blank form').run()
    assert not app.metric
    # Confirm eligibility but leave every model answer missing.
    q=read_json(ROOT,'configs/app_questions.json')
    for key,gate in zip(['adult','established_history','current_smoking','past30_use'],q['eligibility_questions']):
        app.selectbox(key='Blank form_'+key).select(gate['required_answer'])
    app.button[0].click().run()
    assert not app.metric and any('at least 2' in w.value for w in app.warning)
