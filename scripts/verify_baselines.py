"""Verify saved development predictions/metrics/models without retraining/test access."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.baselines import verify_run,metrics,reliability,logits,choose_threshold,KEYS
from path_project.evaluation import load_locked,load_development,BoundaryError
from path_project.final_inputs import validate_final_inputs

if __name__=='__main__':
    saved=verify_run(ROOT)
    config,cc,lock,people,rows=load_locked(ROOT)
    final,_=validate_final_inputs(ROOT)
    settings=json.loads((ROOT/'configs/baseline_models.json').read_text())
    output=ROOT/settings['output_dir'];report=ROOT/settings['report_dir']
    results=json.loads((report/'results.json').read_text())
    fold_results=json.loads((report/'fold_metrics.json').read_text())
    metadata={m['model']:m for m in json.loads((output/'pipeline_metadata.json').read_text())}
    oof=pd.read_parquet(output/'oof_predictions.parquet')
    tuning=load_development(ROOT,'fit')
    membership=rows.loc[rows['partition'].eq('tuning'),KEYS+['fold']]
    tuning=tuning.merge(membership,on=KEYS,validate='one_to_one')
    expected=set(map(tuple,membership[KEYS].to_numpy()))
    allowed=set(people.loc[people['participant_role'].ne('heldout'),'PERSONID'])
    with threadpool_limits(limits=settings['cpu_threads']):
        for candidate in settings['models_in_simplicity_order']:
            name=candidate['name'];features=final['feature_sets'][candidate['profile']]
            local=oof.loc[oof['model'].eq(name)]
            assert set(map(tuple,local[KEYS].to_numpy()))==expected and not local.duplicated(KEYS).any()
            assert set(local['PERSONID']).issubset(allowed) and local['followup_wave'].le(7).all()
            for fold in range(config['folds']):
                valid=tuning.loc[tuning['fold'].eq(fold)]
                training=tuning.loc[tuning['fold'].ne(fold)]
                pred=local.loc[local['fold'].eq(fold)].merge(valid[KEYS],on=KEYS,validate='one_to_one')
                assert len(pred)==len(valid)
                aligned=pred[KEYS].merge(valid,on=KEYS,validate='one_to_one')
                fitted=joblib.load(output/'folds'/f'{name}_fold{fold}.joblib')
                actual=fitted.predict_proba(aligned[features])[:,1]
                np.testing.assert_allclose(actual,pred['probability'],rtol=0,atol=1e-12)
                actual_metrics=metrics(pred,pred['probability'],settings['fixed_diagnostic_threshold'])
                stored=next(r for r in fold_results if r['model']==name and r['fold']==fold)
                for weighting in ['participant_equal','interval_equal']:
                    for metric in ['average_precision','roc_auc','brier','log_loss','prevalence','f1']:
                        assert abs(actual_metrics[weighting][metric]-stored['metrics'][weighting][metric])<1e-12
                if candidate['kind']=='prevalence':np.testing.assert_allclose(actual,training['outcome_p30d'].mean(),rtol=0,atol=1e-14)
                else:
                    np.testing.assert_allclose(fitted['preprocess'].named_transformers_['numeric']['impute'].statistics_,[training['last_cigarette_recency_days'].median()],rtol=0,atol=1e-12)
            fitted=joblib.load(output/'models'/(name+'.joblib'))
            assert fitted['schema'].features==features
            assert fitted[:-1].get_feature_names_out().tolist()==metadata[name]['transformed_features']
        selected=max(results['candidates'],key=lambda r:r['mean_fold_participant_metrics']['average_precision'])['model']
        assert selected==results['selected_model']
        features=final['feature_sets'][next(c for c in settings['models_in_simplicity_order'] if c['name']==selected)['profile']]
        threshold_data=load_development(ROOT,'threshold')[KEYS+features+['outcome_p30d']]
        model=joblib.load(output/'selected_calibrated.joblib')
        reserved=pd.read_parquet(output/'threshold_predictions.parquet')
        aligned=reserved[KEYS].merge(threshold_data,on=KEYS,validate='one_to_one')
        probabilities=model.predict_proba(aligned[features])[:,1]
        np.testing.assert_allclose(probabilities,reserved['calibrated_probability'],rtol=0,atol=1e-12)
        threshold,f1=choose_threshold(reserved,probabilities)
        assert abs(threshold-model.threshold)<1e-12
        assert abs(f1-results['calibration']['threshold_selection_f1'])<1e-12
        calibration=pd.read_parquet(output/'calibration_predictions.parquet')
        allowed_cal=set(people.loc[people['participant_role'].eq('calibration'),'PERSONID'])
        allowed_threshold=set(people.loc[people['participant_role'].eq('threshold'),'PERSONID'])
        assert set(calibration['PERSONID']).issubset(allowed_cal)
        assert set(reserved['PERSONID']).issubset(allowed_threshold)
        assert not set(tuning['PERSONID'])&set(calibration['PERSONID'])
        assert not set(tuning['PERSONID'])&set(reserved['PERSONID'])
        assert not set(calibration['PERSONID'])&set(reserved['PERSONID'])
    print('Verified 25 saved fold models and OOF probabilities/metrics; training-only prevalence/medians; named features; frozen calibration/threshold separation; reload consistency. No refit or final-test data access.')
