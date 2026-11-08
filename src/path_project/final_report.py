"""Final-evaluation rendering from saved aggregates, never test rescoring."""
import os
from pathlib import Path
import numpy as np


def fmt(value,digits=4):return 'undefined' if value is None else f'{value:.{digits}f}'


def with_ci(result,metric):
    point=result['participant_equal'][metric];ci=result['confidence_intervals'][metric]
    return f"{fmt(point)} [{fmt(ci['lower'])}, {fmt(ci['upper'])}] ({ci['valid_replicates']}/{ci['valid_replicates']+ci['undefined_replicates']})"


def render_final_report(root,result,settings):
    root=Path(root);report=root/settings['report_dir'];report.mkdir(parents=True,exist_ok=True)
    selected=result['metrics']['selected_calibrated'];m=selected['participant_equal'];raw=result['metrics'].get('selected_raw')
    lines=['# Final reserved-test evaluation','',
      '**One frozen evaluation; no test-driven model selection, fitting, recalibration, regrouping or threshold changes.** The selected model is still the stage 8 four-input XGBoost with its development-fitted sigmoid and binary threshold. Final results are valid evidence even when weak. This is an unweighted local PATH research project, not a nationally representative or clinically validated prediction tool.','',
      f"Model version: `{result['model_version']}`. Evaluation signature: `{result['evaluation_signature']}`. Pre-test artifacts/code/schema/hyperparameters/categories/timing are saved in `artifacts/final_evaluation_v1/frozen/` and `pretest_freeze.json`, before the recorded answer access in `exposure_log.jsonl`.",'',
      '## Cohort, endpoint and prevalence','',result['endpoint'], '',
      f"Reserved pair: **Wave {result['test_pair'][0]}→{result['test_pair'][1]}** from the label-blind held-out participant group. All these people's earlier records were excluded from fitting/development. **{result['records']:,} records from {result['unique_people']:,} people**, **{result['positive_records']:,} positive** and **{result['negative_records']:,} negative** outcomes; positive prevalence **{100*result['positive_prevalence']:.2f}%**. People with repeated test records: {result['people_with_repeated_test_records']}. No all-eight-wave participation or test-feature completeness filter was imposed.",'',
      'A positive is reported cigarette use in the next interview’s 30-day window, not the exact first resumption, any resumption during the whole interval, or persistent relapse. A negative window does not prove continuous abstinence. The cohort is conditional on valid observed next-wave outcomes; missing follow-up is not a negative label. These estimates do not remove informative attrition or instrument/routing changes. Individual elapsed intervals are unavailable.','',
      f"Observed selected-input coverage: {result['app_input_coverage']['records_meeting_input_count']:,}/{result['records']:,} records meet the frozen {result['app_input_coverage']['minimum_supplied_inputs']}-input usability count. All locked records remain in classifier evaluation; the application guard is a separate coverage description and does not justify a post-hoc test exclusion or new-user accuracy guarantee.",'',
      '## Selected frozen classifier','',
      '95% intervals are participant-cluster percentile bootstrap intervals conditional on this fitted model and observed follow-up sample. Parentheses give valid/attempted replicates. They do not include model-selection, survey-design or all population-generalization uncertainty.','',
      '| Metric | Point [95% interval] (valid/attempted) |','|---|---|']
    for metric in ['prevalence','average_precision','roc_auc','brier','log_loss','mean_probability','precision','recall','specificity','f1']:lines.append(f'| {metric} | {with_ci(selected,metric)} |')
    lines+=['',f"Operating threshold: **{selected['threshold']:.17g}**, frozen on development data. Average precision is stepwise weighted precision over recall increments, matching sklearn average_precision_score; it is **not trapezoidal PR-AUC**. Compare AP to the reported positive prevalence. ROC measures ranking; Brier/log loss measure probability quality. Precision can be undefined if no positive predictions; it is not silently replaced with zero.",'',
      '![Frozen-test confusion matrix](final_evaluation_v1/confusion_matrix.png)','',
      'Confusion matrix uses the actual test record counts at the frozen threshold. Participant and interval metrics are both saved. With one record per test person they coincide; the implementation still supports participant-cluster uncertainty for repeated observations.','',
      '## Frozen baseline comparisons','',
      'All comparator pipelines/calibrators and thresholds were saved before test answers were accessed. Raw baseline models use a fixed diagnostic 0.5 threshold, while calibrated comparators retain their development-selected thresholds. These threshold metrics answer different operating-point choices, so probability/ranking comparisons should also be read. No comparator is promoted or retuned because of this table. Stage 7 training-prevalence-only predictions remain their **training prevalence**, not test prevalence. Raw class-weighted outputs are not silently recalibrated on the test.',
      '', '| Frozen model | AP [95% CI] | ROC [95% CI] | Brier [95% CI] | Log loss | Threshold |','|---|---|---|---|---:|---:|']
    for name,scores in result['metrics'].items():lines.append(f"| {name} | {with_ci(scores,'average_precision')} | {with_ci(scores,'roc_auc')} | {with_ci(scores,'brier')} | {fmt(scores['participant_equal']['log_loss'])} | {fmt(scores['threshold'],6)} |")
    lines+=['','Paired differences use the same participant draws for all models: selected minus comparator; positive AP/ROC favors selected, negative Brier favors selected. These descriptive comparisons do not authorize choosing a new test winner.','',
      '| Comparator | AP difference 95% CI | ROC difference 95% CI | Brier difference 95% CI |','|---|---|---|---|']
    for name,differences in result['paired_difference_selected_minus_baseline'].items():
        cells=[f"[{fmt(differences[k]['lower'])}, {fmt(differences[k]['upper'])}] ({differences[k]['valid_replicates']} valid)" for k in ['average_precision','roc_auc','brier']]
        lines.append('| '+name+' | '+' | '.join(cells)+' |')
    lines+=['','## Calibration and honest probability limitations','',
      '![Frozen-test calibration](final_evaluation_v1/calibration.png)','',
      'Bins are fixed before test access at 0.0, 0.1, …, 1.0. Empty bins have no observed rate. Selected-model points are annotated with record counts; sparse bins and percentile intervals can be unstable or degenerate. Saved calibration tables include all bins and valid/undefined bootstrap counts. No intercept, slope or recalibrator is fitted on this test.','']
    if raw:
        r=raw['participant_equal'];direction='higher' if m['brier']>r['brier'] else 'lower' if m['brier']<r['brier'] else 'equal'
        lines.append(f"Selected calibrated mean probability is **{fmt(m['mean_probability'])}** versus observed prevalence **{fmt(m['prevalence'])}**. Its Brier **{fmt(m['brier'])}** is **{direction}** than the same frozen raw model’s **{fmt(r['brier'])}**. This is reported as measured; calibration is not assumed to transfer perfectly from earlier-wave development. Differences may reflect observation/period/weighting-target shifts, but this evaluation does not establish their causes. The sigmoid is not changed in response.")
    lines+=['','## Frozen project risk categories','',
      f"Cuts: {result['risk_cuts'][0]:.17g} and {result['risk_cuts'][1]:.17g}. Lower includes the lower cut; moderate includes the upper cut; higher is strictly above it. These development-defined relative strata are not medical cutoffs. Their test outcomes are evaluated without moving a cut. Rates below refer to eligible observed-outcome held-out Wave 7→8 records with the listed denominators, not all PATH participants or a national population.",'',
      '| Category | Records | People | Positive records | Observed fraction [95% CI] | Mean probability |','|---|---:|---:|---:|---|---:|']
    for row in result['risk_categories']:
        ci=row['rate_ci'];lines.append(f"| {row['category']} | {row['records']} | {row['people']} | {row['positive_records']} | {fmt(row['participant_equal_rate'])} [{fmt(ci['lower'])}, {fmt(ci['upper'])}] ({ci['valid_replicates']} valid) | {fmt(row['mean_probability'])} |")
    lines+=['','![Frozen category outcomes](final_evaluation_v1/risk_categories.png)','',
      'A category with no observed positive outcomes does not have proven zero future risk; empirical bootstrap bounds can be degenerate and do not rule out unobserved events. Differences in category rates are descriptive, not an intervention effect or a personal confidence percentage.','',
      '## Prespecified recent-use and demographic subgroups','',
      f"Definitions and minimums were frozen before exposure: at least {settings['subgroup_min_people']} people, {settings['subgroup_min_positive_records']} positive and {settings['subgroup_min_negative_records']} negative records for subgroup performance estimates. Counts and outcome-rate uncertainty are retained for smaller groups, with performance suppressed rather than regrouping or weakening thresholds. Group comparisons are exploratory, multiple and not powered fairness/causal claims. The overlapping recent boundary sensitivity is not a separate independent cohort.",'',
      'Recent means observed raw last-cigarette recency >30 to ≤365.25 approximate days; longer means >365.25; unknown duration stays unknown, never zero or presumed long-term. The boundary-excluded sensitivity uses the already-documented raw one-month/twelve-month/one-year reports. Conditional questionnaire routing makes observed-duration groups selected subsets, not all quitters. Age groups use published bands, not invented exact ages. Recorded male/female categories may inherit a historical first interview and are not current gender identity; unknown is retained.',
      '', '| Subgroup | Records / people | Positives | Observed rate [95% CI] | Performance supported |','|---|---:|---:|---|---|']
    for row in result['subgroups']:
        ci=row['rate_ci'];lines.append(f"| {row['subgroup']} | {row['records']}/{row['people']} | {row['positive_records']} | {fmt(row['participant_equal_rate'])} [{fmt(ci['lower'])}, {fmt(ci['upper'])}] | {'yes' if row['performance_supported'] else 'no: size/event minimum'} |")
    lines+=['', '| Supported subgroup | AP [95% CI] | ROC [95% CI] | Brier [95% CI] | Precision [95% CI] | Recall [95% CI] | Specificity [95% CI] |','|---|---|---|---|---|---|---|']
    for row in result['subgroups']:
        if row['performance_supported']:
            cells=[with_ci(row['performance'],key) for key in ['average_precision','roc_auc','brier','precision','recall','specificity']];lines.append('| '+row['subgroup']+' | '+' | '.join(cells)+' |')
    lines+=['','No subgroup-specific feature selection, calibration or thresholds are fitted. Uncertain/small strata cannot establish reliability for an individual demographic group. Missing-recency performance is included where supported because missingness can encode survey routing, not because unknown duration means a particular quit history.',
      '', '## Bootstrap and undefined metrics','',result['bootstrap_method'],'',
      f"Seed **{result['bootstrap_seed']}**, **{result['bootstrap_replicates']}** replicates. The whole observed participant cluster is sampled with replacement, and each sampled occurrence contributes one total metric weight even if a participant is drawn more than once. Because this outer test has one row/person, this reduces to resampling people/records. Paired comparisons share draws. Subgroup/rate intervals resample participants within the reported subgroup. A no-positive AP or absent-class ROC is undefined; zero-denominator precision/recall/specificity/F1 is undefined. CIs omit only that metric’s undefined replicates and report valid/undefined counts; no new seed is searched. Other valid metrics are retained.",'',
      'The custom cached-order weighted AP/ROC implementation was tested against sklearn on synthetic tied/weighted data before test access. It avoids repeated sorting during bootstrap without changing the metric definition. Probability losses use the frozen machine-epsilon clip. These are empirical conditional intervals, not total predictive uncertainty or personal confidence.','',
      '## Timing, exposure record and stop point','',result['timing_decision'],'. No separate timing model/horizon is supported, so no survival metrics, annual probabilities or relapse dates are mixed with classification.','',
      'The exposure log records the completed pre-test freeze, the start of the sole test answer read, the saved prediction-checkpoint hash and evaluation completion. There was no test-driven fitting/tuning. All reported values come from that frozen code and those saved predictions. Fitted Pipelines/calibrators, schemas/hyperparameters, thresholds, category/timing decisions, package versions and code copies are in the pre-test snapshot. All participant-level test predictions/subgroup fields stay in ignored `artifacts/final_evaluation_v1/test_predictions.parquet`; public results/figures are aggregates only.','',
      'Completed retries verify and reuse saved final results; they do not rescore, rebootstrap or select another model. If an implementation bug or incomplete exposed run is found, preserve the log/checkpoint and record the specific fix, prior exposure and implications before any recovery. Never conceal a repeated evaluation or present a revised post-test model as untouched. Earlier immutable app metadata retains its historical pending-test text; `configs/final_evaluation_status.json` supplies current completion evidence without rewriting old artifacts. New-user/clinical validity and national representativeness remain unestablished regardless of these metrics.',
      '', 'Weak results are retained as valid research outcomes. Stop at stage 11; await the next numbered prompt. No publication, deployment or external messaging occurred.']
    (root/settings['report_markdown']).write_text('\n'.join(lines)+'\n')
    os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,5),dpi=150)
    for name,bins in result['calibration'].items():
        nonempty=[b for b in bins if b['records']]
        ax.plot([b['mean_probability'] for b in nonempty],[b['observed_fraction'] for b in nonempty],marker='o',markersize=3,label=name)
        if name=='selected_calibrated':
            for b in nonempty:
                ci=b['observed_fraction_ci']
                if ci['lower'] is not None:ax.vlines(b['mean_probability'],ci['lower'],ci['upper'],alpha=.4)
                ax.annotate('n='+str(b['records']),(b['mean_probability'],b['observed_fraction']),fontsize=7,xytext=(4,4),textcoords='offset points')
    ax.plot([0,1],[0,1],'k--',linewidth=1);ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean frozen predicted probability',ylabel='Observed test fraction',title='Reserved Wave 7→8 calibration; no recalibration');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(report/'calibration.png',bbox_inches='tight');plt.close(fig)
    confusion=selected['interval_equal']['confusion'];matrix=np.array([[confusion['tn'],confusion['fp']],[confusion['fn'],confusion['tp']]])
    fig,ax=plt.subplots(figsize=(5,4),dpi=150);ax.imshow(matrix,cmap='Blues')
    for (i,j),value in np.ndenumerate(matrix):ax.text(j,i,f'{value:g}',ha='center',va='center',color='white' if value>matrix.max()/2 else 'black')
    ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['No smoking','Smoking'],yticklabels=['No smoking','Smoking'],xlabel='Frozen predicted class',ylabel='Observed follow-up class',title='Reserved test confusion matrix');fig.tight_layout();fig.savefig(report/'confusion_matrix.png',bbox_inches='tight');plt.close(fig)
    groups=result['risk_categories'];fig,ax=plt.subplots(figsize=(7,4),dpi=150)
    ax.bar([f"{r['category']}\nn={r['records']}" for r in groups],[100*r['participant_equal_rate'] if r['participant_equal_rate'] is not None else float('nan') for r in groups]);ax.set(ylabel='Observed positive fraction (%)',title='Frozen project categories: observed test outcomes');fig.tight_layout();fig.savefig(report/'risk_categories.png',bbox_inches='tight');plt.close(fig)
