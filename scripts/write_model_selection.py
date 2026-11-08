"""Stage 8 selection document/figures from saved aggregate results only."""
from pathlib import Path
import json,os
ROOT=Path(__file__).resolve().parents[1]

def write(root=ROOT):
    settings=json.loads((root/'configs/tree_models.json').read_text())
    result=json.loads((root/settings['report_dir']/'results.json').read_text())
    selected=next(r for r in result['candidates'] if r['model']==result['selected_model'])
    best_logistic=next(r for r in result['candidates'] if r['model']=='minimal_logistic')
    m=selected['mean_fold_participant_metrics'];cal=result['calibration']
    lines=['# Stage 8 model selection: tree models versus baselines','',
      '**Final-test features, outcomes and performance remain unopened.** All choices use the locked five tuning folds; calibration and threshold groups never rank classifiers. Original data, cohort, feature definitions, participant assignments and stage 7 models remain unchanged.','',
      '## Fixed search and fairness','',
      f"Executed {result['new_fold_fit_count']} fits for {result['new_candidate_count']} new tree configurations, compared with five saved stage 7 candidates. XGBoost dependency status: `{result['dependency']}`. XGBoost actually ran locally; no installation, network, API key or paid service was required. The fallback implementation is HistGradientBoostingClassifier only if XGBoost import is unavailable; it was exercised on synthetic data, not substituted for XGBoost in these real results.",'',
      'Search budget fixed before fitting (`configs/tree_models.json`):','',
      '- Random Forest: 150 trees; max_features=sqrt; (max_depth=4, min_samples_leaf=20) or (max_depth=8, min_samples_leaf=10); unweighted or class_weight=balanced.',
      '- XGBoost: histogram CPU trees, lambda=5, full row/column sampling; (120 trees, max_depth=2, learning_rate=0.05, min_child_weight=10) or (180 trees, max_depth=3, learning_rate=0.05, min_child_weight=10); scale_pos_weight=1 or training-fold negatives/positives.',
      '- Both families: minimal four inputs and full selected eleven app inputs; seed 366, one CPU thread. Two paired complexity settings × two weight choices × two profiles × two families = 16 configurations × five folds = 80 fits. This is a modest paired search, not an exhaustive Cartesian search over every numerical parameter. No early stopping, adaptive search expansion or validation-driven preprocessing.',
      '', 'Each tree Pipeline reuses the same fold-fitted schema validation, categorical missing imputation/one-hot encoding, and numerical median/missing-indicator/scaling recipe as stage 7. Scaling is unnecessary for trees but retained for a common preprocessing comparison and does not use validation statistics. Unseen valid categories are ignored safely, and feature names are preserved. Learned imputation/encoding and class-weight ratios use training records only. No target encoding or future questionnaire information is introduced.',
      '', 'Every tree validation key/label was checked against the saved baselines for the same fold. No baseline was retrained. Base fits use unweighted records or training-only class weighting; evaluation metrics use participant-equal weights (1/n records) with interval-equal counterparts also saved. No targeted oversampling or SMOTE is used. Training folds have adequate positives (validation folds previously had 292–302); the weight experiment and observed probability distortion do not justify adding a more complex synthetic-data experiment. RF bootstrap is native training-only bagging, not class balancing. Validation/test prevalence and record membership are unchanged.',
      '', '## Prespecified decision rule and probability quality','',settings['selection_rule'],'',settings['probability_quality_policy'],'',
      'Discrimination is ranked by mean participant-weighted **average_precision_score**, not trapezoidal PR-AUC. Existing baseline simplicity order precedes ordered tree configurations for exact ties. Brier/log loss, mean prediction versus prevalence, calibration bins and ROC-AUC are reported for every candidate. They inform the probability-readiness/calibration decision and explain tradeoffs; they are not an undisclosed new composite objective or a reason to tune against reserved groups. Finite bounded probabilities and finite losses are required. No target score is promised.',
      '',f"Mean-fold participant-equal prevalence context: **{result['baseline_prevalence_context']:.4f}** (ordinary tuning interval prevalence was 0.1081). These are different repeated-record estimands; they must not be interchanged or presented as survey-weighted national risk.",'',
      '| Candidate | Mean fold AP | AP fold SD | ROC-AUC | Brier | Log loss | Five-fold fit seconds |','|---|---:|---:|---:|---:|---:|---:|']
    for row in result['candidates']:
        r=row['mean_fold_participant_metrics'];sd=row['fold_sd_descriptive_only']['average_precision'];runtime=row['total_fold_fit_seconds']
        display='not recorded' if runtime is None else f'{runtime:.3f}'
        lines.append(f"| {row['model']} | {r['average_precision']:.4f} | {sd:.4f} | {r['roc_auc']:.4f} | {r['brier']:.4f} | {r['log_loss']:.4f} | {display} |")
    lines+=['',f"Total executed tree workflow elapsed time: **{result['elapsed_training_workflow_seconds']:.3f} seconds** on this local machine, including loading, prediction, serialization, four refits and reserved calibration. Per-fold fit/prediction times are recorded individually. Timing is measured by perf_counter and is hardware/load dependent; it is not a universal benchmark. Stage 7 baseline timing was not recorded, so it is explicitly missing rather than fabricated or measured by retraining.",'',
      '## Minimal versus full-feature comparisons','',
      '| Family | Best minimal candidate | AP | Brier | Best full candidate | AP | Brier |','|---|---|---:|---:|---|---:|---:|']
    for family in ['baseline','random_forest','xgboost' if result['dependency']['available'] else 'hist_gradient_boosting']:
        rows=[r for r in result['candidates'] if r['family']==family and r['model']!='training_prevalence']
        minimum=max([r for r in rows if r['profile']=='minimal'],key=lambda r:r['mean_fold_participant_metrics']['average_precision'])
        full=max([r for r in rows if r['profile']=='app'],key=lambda r:r['mean_fold_participant_metrics']['average_precision'])
        a=minimum['mean_fold_participant_metrics'];b=full['mean_fold_participant_metrics']
        lines.append(f"| {family} | {minimum['model']} | {a['average_precision']:.4f} | {a['brier']:.4f} | {full['model']} | {b['average_precision']:.4f} | {b['brier']:.4f} |")
    lines+=['','## Selected candidate and tradeoffs','',
      f"Selected **{result['selected_model']}** by tuning CV only. Its mean AP={m['average_precision']:.6f}, ROC-AUC={m['roc_auc']:.6f}, Brier={m['brier']:.6f}, versus minimal logistic AP={best_logistic['mean_fold_participant_metrics']['average_precision']:.6f} and Brier={best_logistic['mean_fold_participant_metrics']['brier']:.6f}. Exact selected search parameters: `{selected.get('params',{})}`.",'',
      'The selected model uses only age band, education, employment and observed raw quit/last-cigarette recency. This reduces question burden and avoids fabricated historical answers. The eleven-feature full app comparison is retained; the survey-only 25-feature research model is not silently used by the app. The full unweighted depth-3 XGBoost has slightly better raw Brier (0.141388) but slightly lower AP (0.452306), so it does not replace the AP winner. A Random Forest also approaches the winning AP. These small differences across a single fixed five-fold search do not establish statistically significant superiority, clinical utility or later-wave performance. Fold SD is descriptive, not an independent confidence interval. More candidate comparisons can make internal winner estimates optimistic; no bootstrap/CI or significance claim is invented.',
      '', 'Class-weighted trees generally predict much higher raw probabilities and have worse Brier in this run; weighting can help ranking/recall without preserving probability calibration. No observation is removed or label rebalanced in evaluation. The selected unweighted model still underestimates participant-equal development prevalence, so the locked sigmoid procedure is applied. Class weights are not survey weights and do not supply population representativeness.',
      '', '![Selected development calibration](../reports/tree_comparison_calibration.png)','',
      '## Reserved calibration and operating threshold','',cal['stage8_action'],'',
      'The selected base estimator fits tuning people only. The new selected-tree sigmoid uses 2,801 calibration records from 947 different people, then the threshold uses 2,910 records from 990 further people. No calibration example/person was used to fit that base model. The groups previously supported the stage 7 baseline diagnostic; their reuse for the prespecified new classifier’s fixed sigmoid does not authorize classifier/hyperparameter/feature selection using them. Neither new nor old reserved-group results re-rank this comparison. No repeated final-test evaluation occurs.',
      '', '| Threshold-group participant-equal metric | Raw selected | Sigmoid calibrated |','|---|---:|---:|']
    raw=cal['threshold_group_raw_fixed_0_5']['participant_equal'];scaled=cal['threshold_group_calibrated_fixed_0_5']['participant_equal']
    for key in ['prevalence','average_precision','roc_auc','brier','log_loss','mean_predicted_probability']:lines.append(f'| {key} | {raw[key]:.4f} | {scaled[key]:.4f} |')
    chosen=cal['threshold_selection_apparent_at_chosen_threshold']['participant_equal']
    lines+=['',f"Calibrated threshold **{cal['chosen_threshold']:.6f}** selected by participant-weighted F1 (largest threshold on ties). Apparent selection-set F1={chosen['f1']:.4f}, precision={chosen['precision']:.4f}, sensitivity={chosen['sensitivity']:.4f}, specificity={chosen['specificity']:.4f}. These metrics are apparent for threshold selection, not independent operating guarantees. Calibration-fit metrics are also explicitly labeled apparent. No low/medium/high risk categories or personal confidence percentage is validated.",'',
      'The reserved threshold-group AP is 0.4454, slightly below the stage 7 selected baseline’s 0.4493, while its Brier/ROC tradeoffs differ. This is reported honestly, not used to reverse the tuning-only selection or launch another search. Sparse probability bins and cross-wave/routing shifts limit interpretation; future user applicability and later-wave calibration remain unknown. No outcome dates, persistent-relapse claims or fixed-year risks are created.',
      '', '## Saved files and reproducibility','',
      'Ignored `artifacts/trees_v1/` contains all 80 searched fold Pipelines, four best-family/profile tuning refits, selected calibrated bundle, local OOF/calibration/threshold predictions and immutable manifest. Aggregate results/configurations/runtimes, fold metrics and provenance are in `reports/trees_v1/`. `configs/tree_models.json` is the exact fixed search space and probability-quality policy. Models/predictions/identifiers remain ignored; public reports contain aggregate results only. Dependency versions, seeds, code/config/baseline/split hashes and measured runtimes are recorded. No service, commit, upload or deployment occurred.',
      '', '```bash','.venv/bin/python scripts/train_tree_models.py','.venv/bin/python scripts/verify_tree_models.py','.venv/bin/python scripts/write_model_selection.py','.venv/bin/python -m pytest -q -p no:cacheprovider','.venv/bin/python scripts/verify_evaluation_splits.py','.venv/bin/python scripts/verify_inputs.py','```','',
      'The training command verifies/reuses a completed identical run and refuses changed/incomplete outputs; it does not silently refit. The verifier scores saved development artifacts only, checking probabilities/metrics, training-only medians and class ratios, exact fold membership, feature schema, selection and calibration boundaries. Synthetic tests cover RF/XGBoost and the optional fallback, safe categories/serialization, training-only weight ratios and the locked selection rule. No final-test performance is produced. Stop at stage 8 and await the next numbered prompt.']
    (root/'docs/model_selection.md').write_text('\n'.join(lines)+'\n')
    os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,5),dpi=150)
    for key,label in [('threshold_group_raw_calibration_bins','Raw selected'),('threshold_group_calibrated_bins','Sigmoid calibrated')]:
        bins=cal[key];ax.plot([b['mean_prediction'] for b in bins],[b['observed_fraction'] for b in bins],marker='o',label=label)
    ax.plot([0,1],[0,1],'k--');ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean predicted probability',ylabel='Observed fraction (participant weighted)',title='Reserved development threshold group; final test closed');ax.legend();fig.tight_layout();fig.savefig(root/'reports/tree_comparison_calibration.png',bbox_inches='tight');plt.close(fig)
    print('Wrote docs/model_selection.md and reports/tree_comparison_calibration.png from saved aggregates only.')

if __name__=='__main__':write()
