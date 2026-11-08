"""Verify existing tree artifacts/development predictions; no retraining/test access."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.trees import verify_tree_run,select_candidate
from path_project.baselines import metrics,choose_threshold,KEYS
from path_project.evaluation import load_locked,load_development
from path_project.final_inputs import validate_final_inputs

if __name__=='__main__':
    manifest=verify_tree_run(ROOT)
    settings=json.loads((ROOT/'configs/tree_models.json').read_text());baseline=json.loads((ROOT/'configs/baseline_models.json').read_text())
    config,cc,split,people,rows=load_locked(ROOT);final,_=validate_final_inputs(ROOT)
    output=ROOT/settings['output_dir'];report=ROOT/settings['report_dir']
    results=json.loads((report/'results.json').read_text());folds=json.loads((report/'fold_metrics.json').read_text())
    oof=pd.read_parquet(output/'oof_predictions.parquet')
    tuning=load_development(ROOT,'fit').merge(rows.loc[rows['partition'].eq('tuning'),KEYS+['fold']],on=KEYS,validate='one_to_one')
    expected=set(map(tuple,tuning[KEYS].to_numpy()))
    heldout=set(people.loc[people['participant_role'].eq('heldout'),'PERSONID'])
    assert not set(oof['PERSONID'])&heldout and oof['followup_wave'].le(7).all()
    with threadpool_limits(limits=settings['cpu_threads']):
        for candidate in results['search_candidates']:
            name=candidate['name'];features=final['feature_sets'][candidate['profile']]
            local=oof.loc[oof['model'].eq(name)]
            assert set(map(tuple,local[KEYS].to_numpy()))==expected and not local.duplicated(KEYS).any()
            for fold in range(config['folds']):
                train=tuning.loc[tuning['fold'].ne(fold)];valid=tuning.loc[tuning['fold'].eq(fold)]
                pred=local.loc[local['fold'].eq(fold)]
                aligned=pred[KEYS+['outcome_p30d']].merge(valid,on=KEYS,validate='one_to_one',suffixes=('_saved',''))
                assert len(pred)==len(valid) and aligned['outcome_p30d_saved'].eq(aligned['outcome_p30d']).all()
                fitted=joblib.load(output/'folds'/f'{name}_fold{fold}.joblib')
                actual=fitted.predict_proba(aligned[features])[:,1]
                np.testing.assert_allclose(actual,pred['probability'],rtol=0,atol=1e-12)
                np.testing.assert_allclose(fitted['preprocess'].named_transformers_['numeric']['impute'].statistics_,[train['last_cigarette_recency_days'].median()],rtol=0,atol=1e-12)
                ratio=float(train['outcome_p30d'].eq(0).sum()/train['outcome_p30d'].eq(1).sum())
                if candidate['family']=='xgboost':assert fitted['model'].get_params()['scale_pos_weight']==(ratio if candidate['weight']=='balanced' else 1)
                stored=next(f for f in folds if f['model']==name and f['fold']==fold)
                score=metrics(pred,pred['probability'],.5)
                assert stored['fit_seconds']>0 and stored['predict_seconds']>=0
                for weight in ['participant_equal','interval_equal']:
                    for metric in ['average_precision','roc_auc','brier','log_loss','f1','prevalence']:
                        assert abs(score[weight][metric]-stored['metrics'][weight][metric])<1e-12
        assert select_candidate(results['candidates'])==results['selected_model']
        model=joblib.load(output/'selected_calibrated.joblib');features=model.base['schema'].features
        threshold=load_development(ROOT,'threshold')[KEYS+features+['outcome_p30d']]
        source=output if (output/'threshold_predictions.parquet').exists() else ROOT/baseline['output_dir']
        saved=pd.read_parquet(source/'threshold_predictions.parquet')
        aligned=saved[KEYS].merge(threshold,on=KEYS,validate='one_to_one')
        p=model.predict_proba(aligned[features])[:,1]
        np.testing.assert_allclose(p,saved['calibrated_probability'],rtol=0,atol=1e-12)
        chosen,_=choose_threshold(saved,p);assert abs(chosen-model.threshold)<1e-12
        calibration=pd.read_parquet(source/'calibration_predictions.parquet')
        assert set(calibration['PERSONID']).issubset(set(people.loc[people['participant_role'].eq('calibration'),'PERSONID']))
        assert set(saved['PERSONID']).issubset(set(people.loc[people['participant_role'].eq('threshold'),'PERSONID']))
        assert not set(tuning['PERSONID'])&(set(calibration['PERSONID'])|set(saved['PERSONID']))
    print(f"Verified {len(folds)} saved tree fold Pipelines, OOF labels/probabilities/metrics, training-only medians/weights, AP selection and separated calibration/threshold bundle. No refits or final-test access.")
