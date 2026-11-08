"""Audit final deliverable presence, saved evidence, links and timing without test scoring."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.inventory import verify_manifest
from path_project.evaluation import load_locked
from path_project.outputs import verify_outputs
from path_project.final_evaluation import verify_final_results

STAGES={
1:['docs/data_inventory.md','reports/input_inventory.json','docs/original_inputs.sha256.json'],
2:['docs/prediction_specification.md','docs/timing_feasibility.md','reports/prediction_source_evidence.json'],
3:['configs/feature_mapping.json','docs/feature_dictionary.csv','reports/feature_evidence_checks.json'],
4:['src/path_project/cohort.py','data/processed/cohort_v1/cohort.parquet','data/processed/cohort_v1/schema.json','reports/cohort_v1/cohort_flow.json'],
5:['configs/evaluation.json','artifacts/evaluation_v1/participants.parquet','artifacts/evaluation_v1/records.parquet','artifacts/evaluation_v1/manifest.json'],
6:['reports/development_data_summary.md','configs/feature_mapping_final.json','configs/app_questions.json'],
7:['reports/baseline_results.md','artifacts/baselines_v1/selected_calibrated.joblib','artifacts/baselines_v1/manifest.json'],
8:['docs/model_selection.md','artifacts/trees_v1/selected_calibrated.joblib','artifacts/trees_v1/manifest.json'],
9:['docs/timing_decision.md','configs/timing_decision.json','reports/timing_confirmation_v1.json'],
10:['src/path_project/outputs.py','configs/risk_categories_v1.json','configs/output_contract.json','artifacts/outputs_v1/manifest.json'],
11:['reports/final_evaluation.md','reports/final_evaluation_v1/results.json','artifacts/final_evaluation_v1/pretest_freeze.json','artifacts/final_evaluation_v1/complete_manifest.json'],
12:['app/streamlit_app.py','tests/test_demo.py','reports/demo_verification_v1.json'],
13:['reports/verification.md','reports/verification_evidence.json','tests/test_project_smoke.py'],
14:['README.md','docs/final_project_report.md','docs/proposal_revision_notes.md','docs/presentation_outline.md','docs/viva_questions.md','reports/documentation_checks.json','reports/literature_verification.json']}


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    errors=[]
    def read(name):return json.loads((ROOT/name).read_text())
    stages={str(stage):{'required_files':names,'files_present_nonempty':all((ROOT/n).is_file() and (ROOT/n).stat().st_size>0 for n in names),'status':'supported omission' if stage==9 else 'complete evidence present'} for stage,names in STAGES.items()}
    for stage,item in stages.items():
        if not item['files_present_nonempty']:errors.append('Missing/empty stage '+stage+' deliverable')
    verify_outputs(ROOT);verify_final_results(ROOT)
    _,_,_,people,rows=load_locked(ROOT)
    meta=read('configs/app_metadata.json');timing=read('configs/timing_decision.json');contract=read('configs/output_contract.json')
    if timing['decision']!='C' or contract['timing_estimates_included']:errors.append('Timing decision/contract mismatch')
    for key in ['elapsed_time_estimates_available','survival_model_available','fixed_horizon_probabilities_available','estimated_relapse_date_available']:
        if meta[key]:errors.append('Unsupported timing capability enabled: '+key)
    if meta['supported_elapsed_time_horizons']:errors.append('Unsupported horizons present')
    demo=read('reports/demo_verification_v1.json');browser=demo['browser_evidence']
    if not browser['launch_confirmed'] or not browser['interaction_confirmation']['blank_submission_warning_and_no_prediction'] or not browser['interaction_confirmation']['three_fictional_preset_submissions_without_errors']:errors.append('Browser evidence incomplete')
    if digest(Path(browser['path']))!=browser['sha256']:errors.append('Browser screenshot differs from recorded evidence')
    docs=read('reports/documentation_checks.json')
    for name,h in docs['source_sha256'].items():
        if digest(ROOT/name)!=h:errors.append('Stage14 checked document/source changed: '+name)
    verification=read('reports/verification_evidence.json')
    if verification['status']!='passed' or not all(verification['isolated_build']['reproduced_sha256'].values()):errors.append('Stage13 verification/rebuild incomplete')
    originals=read('docs/original_inputs.sha256.json');failures=verify_manifest(ROOT,originals);allowed=read('configs/verification.json')['intentional_original_exceptions'];exceptions=[]
    for failure in failures:
        name=failure.rsplit(': ',1)[0]
        if name in allowed and (ROOT/name).is_file() and digest(ROOT/name)==allowed[name]['sha256']:exceptions.append(name)
        else:errors.append('Unexpected original-file difference: '+name)
    handoff=(ROOT/'PROJECT_HANDOFF.md').read_text();links=0;commands=0
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',handoff):
        if target.startswith(('http://','https://','#')):continue
        if not (ROOT/target.split('#')[0]).exists():errors.append('Broken handoff link: '+target)
        links+=1
    for command in re.findall(r'\.venv/bin/python(?: -m [^\s`]+)? (scripts/[\w_]+\.py|app/[\w_]+\.py)',handoff):
        if not (ROOT/command).is_file():errors.append('Missing documented handoff executable: '+command)
        commands+=1
    if '.venv/bin/python -m streamlit run app/streamlit_app.py' not in handoff:errors.append('Missing exact app startup command')
    final=read('reports/final_evaluation_v1/results.json');model='selected_calibrated'
    for key in ['average_precision','roc_auc','brier','precision','recall','specificity']:
        x=final['metrics'][model];ci=x['confidence_intervals'][key]
        expected=f"{x['interval_equal'][key]:.4f} [{ci['lower']:.4f}, {ci['upper']:.4f}]"
        if expected not in handoff:errors.append('Handoff metric differs: '+key)
    if meta['classifier']['sha256'] not in handoff:errors.append('Handoff model hash differs')
    tokens=set(re.split(r'''[\s"'`,;|\[\]{}():=]+''',handoff))
    if tokens&set(people['PERSONID']):errors.append('Participant identifier in handoff; value suppressed')
    result={'status':'passed' if not errors else 'failed','stages':stages,'handoff_links_checked':links,'handoff_commands_checked':commands,'frozen_model_sha256':meta['classifier']['sha256'],'frozen_test_records':final['records'],'frozen_positive_records':final['positive_records'],'timing_decision':'C','timing_outputs_enabled':False,'browser_evidence_source':'User-supplied screenshot and explicit confirmation; not an agent launch. Synthetic UI/path tests recorded separately.','originals_unchanged':len(originals)-len(failures),'originals_total':len(originals),'documented_original_exceptions':exceptions,'no_final_test_scoring_metrics_bootstrap_or_fit':True,'errors':errors,'source_sha256':{'PROJECT_HANDOFF.md':digest(ROOT/'PROJECT_HANDOFF.md'),'scripts/verify_handoff.py':digest(ROOT/'scripts/verify_handoff.py')}}
    (ROOT/'reports/handoff_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"Handoff {result['status']}:14 stages, {links} links, {commands} commands, frozen artifact identity and disabled timing; {len(errors)} errors.")
    for error in errors:print(error)
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
