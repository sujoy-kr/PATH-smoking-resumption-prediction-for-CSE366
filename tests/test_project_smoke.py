"""Synthetic inputs through the actual frozen selected model; never final-test data."""
import json,sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.demo import load_demo_engine
from path_project.final_inputs import encode_app_answers
from path_project.evaluation import BoundaryError


def test_real_frozen_calibrated_pipeline_serialization_and_explanation(tmp_path):
    engine=load_demo_engine(ROOT)
    profiles=json.loads((ROOT/'configs/demo.json').read_text())['presets']
    eligibility={k:q['required_answer'] for k,q in zip(engine.settings['eligibility_keys'],engine.gates)}
    frames=[]
    for answers in [p for p in profiles.values() if p]:
        values,_=encode_app_answers(ROOT,answers,7)
        frame=pd.DataFrame([{f:values[f] for f in engine.features}],dtype=float)
        output=engine.output(answers,eligibility,wave=7)
        assert output['probability']==pytest.approx(engine.model.predict_proba(frame)[0,1],abs=1e-12)
        assert output['explanation']['reference_model_probability']+sum(f['contribution'] for f in output['contributing_factors'])==pytest.approx(output['probability'],abs=1e-8)
        frames.append(frame)
    frame=pd.concat(frames,ignore_index=True)
    path=tmp_path/'synthetic inference copy with spaces.joblib'
    before=engine.model.predict_proba(frame)
    joblib.dump(engine.model,path)
    restored=joblib.load(path)
    np.testing.assert_array_equal(before,restored.predict_proba(frame[frame.columns[::-1]]))
    assert list(restored.base['schema'].features)==list(engine.features)
    with pytest.raises(BoundaryError):restored.predict_proba(frame.assign(PERSONID='SYNTHETIC_ONLY'))
