"""Read-only stage 10 verification; no fitting, category changes or test access."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.outputs import verify_outputs,load_engine,weighted_cuts,category_summary,category_for
from path_project.evaluation import load_locked,participant_weights

if __name__=='__main__':
    manifest=verify_outputs(ROOT);settings=json.loads((ROOT/'configs/output_explanations.json').read_text())
    output=ROOT/settings['output_dir'];report=ROOT/settings['report_dir']
    engine=load_engine(ROOT);summary=json.loads((report/'summary.json').read_text())
    config,cc,split,people,rows=load_locked(ROOT)
    threshold=pd.read_parquet(ROOT/settings['category_predictions'])
    cuts=weighted_cuts(threshold['calibrated_probability'],participant_weights(threshold),settings['category_quantiles'])
    assert cuts==engine.bands['cuts']==summary['cuts']
    assert category_summary(threshold,cuts)==summary['category_groups']
    assert sum(r['interval_records'] for r in summary['category_groups'])==summary['reference_interval_records']
    assert sum(r['positive_outcomes'] for r in summary['category_groups'])==summary['reference_positive_interval_outcomes']
    tuning=set(people.loc[people['participant_role'].eq('tuning'),'PERSONID'])
    bg=pd.read_parquet(output/'background.parquet');probe=pd.read_parquet(output/'global_sample.parquet')
    for frame in [bg,probe]:
        assert set(frame['PERSONID']).issubset(tuning) and frame['followup_wave'].le(7).all()
        assert frame['PERSONID'].is_unique
    assert not set(bg['PERSONID'])&set(probe['PERSONID'])
    values=pd.read_parquet(output/'global_attributions.parquet')
    predictions=engine.model.predict_proba(probe[engine.features])[:,1]
    np.testing.assert_allclose(predictions,values['probability'],rtol=0,atol=1e-12)
    contributions=values[[name+'__shap_probability' for name in engine.features]].to_numpy()
    np.testing.assert_allclose(values['base_value']+contributions.sum(axis=1),predictions,rtol=0,atol=settings['additivity_absolute_tolerance'])
    for row in json.loads((report/'global_explanations.json').read_text()):
        index=engine.features.index(row['feature']);assert abs(row['mean_absolute_probability_contribution']-np.abs(contributions[:,index]).mean())<1e-12
    fixtures=json.loads((ROOT/'tests/fixtures/output_profiles.json').read_text())
    stored=json.loads((report/'synthetic_profile_outputs.json').read_text())
    for profile,old in zip(fixtures['profiles'],stored):
        result=engine.output(profile['answers'],profile['eligibility'],wave=profile['wave'])
        assert result['status']==old['output']['status']
        if result['status']=='scored':
            assert abs(result['probability']-old['output']['probability'])<1e-12
            assert result['category']['code']==category_for(result['probability'],cuts)
            assert result['explanation']['additivity_residual']<=settings['additivity_absolute_tolerance']
            assert result['model_version']['artifact_sha256']==engine.metadata['classifier']['sha256']
        else:assert result['probability'] is None and result['category'] is None and result['contributing_factors']==[]
    print(f"Verified frozen score bands and development counts; {len(probe)} exact calibrated-probability explanations; eight fictional profiles; missing/eligibility suppression; same-model identity. No refitting, timing outputs or final-test access.")
