"""Stage 14 documentation checks; reads saved aggregates, never evaluates a model."""
from pathlib import Path
import hashlib,json,re,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
FILES=['README.md','docs/final_project_report.md','docs/proposal_revision_notes.md','docs/presentation_outline.md','docs/viva_questions.md']


def main():
    final=json.loads((ROOT/'reports/final_evaluation_v1/results.json').read_text())
    cv=json.loads((ROOT/'reports/trees_v1/results.json').read_text())
    report=(ROOT/'docs/final_project_report.md').read_text()
    errors=[];links=0;commands=0
    for name in FILES:
        text=(ROOT/name).read_text()
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
            if target.startswith(('https://','http://','#')):continue
            destination=target.split('#')[0]
            if not (ROOT/name).parent.joinpath(destination).exists():errors.append('Broken local link in '+name+': '+destination)
            links+=1
        for command in re.findall(r'\.venv/bin/python(?: -m [^\s`]+)? (scripts/[\w_]+\.py|app/[\w_]+\.py)',text):
            commands+=1
            if not (ROOT/command).is_file():errors.append('Missing documented executable: '+command)
    metric_cells=0
    def cell(model,key):
        x=final['metrics'][model];ci=x['confidence_intervals'][key]
        return f"{x['interval_equal'][key]:.4f} [{ci['lower']:.4f}, {ci['upper']:.4f}]"
    for model in ['training_prevalence','minimal_logistic','app_logistic','minimal_logistic_calibrated','selected_raw','selected_calibrated','minimal_logistic_balanced','app_logistic_balanced']:
        for key in ['average_precision','roc_auc','brier']:
            if cell(model,key) not in report:errors.append('Missing/mismatched final-table metric: '+model+' '+key)
            metric_cells+=1
    for key in ['precision','recall','specificity','log_loss']:
        if cell('selected_calibrated',key) not in report:errors.append('Missing/mismatched threshold/loss metric: '+key)
        metric_cells+=1
    for model in ['training_prevalence','minimal_logistic','app_logistic','rf_minimal_s0_none','rf_app_s0_none','xgb_minimal_s1_none','xgb_app_s1_none']:
        row=next(r for r in cv['candidates'] if r['model']==model)['mean_fold_participant_metrics']
        expected=f"| {model} | {row['average_precision']:.4f} | {row['roc_auc']:.4f} | {row['brier']:.4f} |"
        if expected not in report:errors.append('Development comparison mismatch: '+model)
    flow=json.loads((ROOT/'reports/cohort_v1/cohort_flow.json').read_text())
    for row in flow:
        expected=f"| {row['pair']} | {row['eligible_baseline']:,} | {row['unobserved_outcomes']:,} | {row['labeled_records']:,} | {row['positive_outcomes']:,} | {100*row['positive_prevalence']:.2f}% |"
        if expected not in report:errors.append('Cohort flow mismatch: '+row['pair'])
    for row in final['risk_categories']:
        expected=f"| {row['category']} | {row['records']} | {row['positive_records']} | {100*row['participant_equal_rate']:.2f}% | {100*row['rate_ci']['lower']:.2f}–{100*row['rate_ci']['upper']:.2f}% |"
        if expected not in report:errors.append('Category outcome mismatch: '+row['category'])
    for name in FILES:
        text=(ROOT/name).read_text()
        if name=='README.md' or name.endswith(('proposal_revision_notes.md','presentation_outline.md','viva_questions.md')):
            for key in ['average_precision','roc_auc','brier']:
                value=final['metrics']['selected_calibrated']['interval_equal'][key]
                if f'{value:.4f}' not in text:errors.append('Missing canonical final metric: '+name+' '+key)
    identifiers=set(pd.read_parquet(ROOT/'artifacts/evaluation_v1/participants.parquet',columns=['PERSONID'])['PERSONID'])
    secret_patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'\bAKIA[0-9A-Z]{16}\b',rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b']
    for name in FILES+['reports/literature_verification.json']:
        data=(ROOT/name).read_bytes();tokens=set(re.split(r'''[\s"'`,;|\[\]{}():=]+''',data.decode()))
        if tokens&identifiers:errors.append('Private identifier token in '+name+'; value suppressed')
        if any(re.search(pattern,data) for pattern in secret_patterns):errors.append('Potential secret in '+name+'; value suppressed')
    protected_files=['Smoking_Relapse_Predictor_Presentation.pptx','Project_Analysis_and_Implementation_Plan.md']
    manifest=json.loads((ROOT/'docs/original_inputs.sha256.json').read_text())
    for name in protected_files:
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=manifest[name]['sha256']:errors.append('Original proposal/analysis changed: '+name)
    literature=json.loads((ROOT/'reports/literature_verification.json').read_text())
    assert len(literature['references'])==2
    result={'status':'passed' if not errors else 'failed','files_checked':FILES,'local_links_checked':links,'documented_commands_checked':commands,'final_metric_cells_checked':metric_cells,'development_rows_checked':7,'cohort_rows_checked':7,'category_rows_checked':3,'private_identifier_and_common_secret_scan':'No matches' if not any('Private identifier' in e or 'Potential secret' in e for e in errors) else 'Check errors','original_proposal_and_analysis_checked':protected_files,'literature_source_record':'reports/literature_verification.json','limits':'Literature access/verification scope recorded separately; this checker verifies documented numerical cells against saved aggregate values, not every possible prose implication or external URL availability. Fresh setup/install and new browser run not claimed.','errors':errors,'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES+['reports/literature_verification.json','scripts/verify_documentation.py']}}
    (ROOT/'reports/documentation_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"Documentation {result['status']}: {links} local links, {commands} commands, {metric_cells} final metric cells, 7 development rows, 7 cohort rows, 3 category rows; {len(errors)} errors.")
    for error in errors:print(error)
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
