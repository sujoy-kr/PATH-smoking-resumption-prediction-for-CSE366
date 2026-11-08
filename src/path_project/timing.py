"""Evidence-backed timing omission and app capability guards; no model fitting."""
import csv,json,re,subprocess
from pathlib import Path
import pyarrow.parquet as pq
from path_project.documentation import fingerprint
from path_project.cohort import load_contract
from path_project.evaluation import BoundaryError
from path_project.trees import verify_tree_run

CAPABILITIES=['elapsed_time_estimates_available','survival_model_available','fixed_horizon_probabilities_available','estimated_relapse_date_available']


def validate_timing_policy(policy):
    if policy['decision']!='C' or not policy['timing_analysis_omitted']:
        raise BoundaryError('This implementation supports the documented timing-unsupported branch only; a new supported endpoint needs a separate protocol.')
    if any(policy[key] is not False for key in CAPABILITIES) or policy['supported_elapsed_time_horizons']!=[]:
        raise BoundaryError('Unsupported timing capability or horizon enabled.')


def confirm_timing(root):
    root=Path(root);policy=json.loads((root/'configs/timing_decision.json').read_text());validate_timing_policy(policy)
    cc,project,task,mapping=load_contract(root)
    final_task=json.loads((root/policy['prediction_specification']).read_text())
    if task['timing_decision']!='C' or final_task['timing_decision']!='C':raise BoundaryError('Timing decision differs from locked prediction specifications.')
    evidence=json.loads((root/policy['source_evidence']).read_text())
    originals=json.loads((root/cc['input_manifest']).read_text())
    local_files=[str(path.relative_to(root)) for path in (root/'PATH').rglob('*') if path.is_file()]
    unexpected=[name for name in local_files if name not in originals]
    if unexpected:raise BoundaryError('New local PATH files require timing/linkage review before affirming the previous evidence; no values read.')
    wave_evidence={w['wave']:w for w in evidence['waves']}
    headers=[];sources=[]
    for wave in project['waves']:
        number=wave['wave'];stored=wave_evidence[number]
        with (root/wave['data']).open(newline='',encoding=cc['read_encoding']) as stream:
            header=next(csv.reader(stream,delimiter='\t'))
        clocks=[name for name in header if re.search(policy['clock_header_pattern'],name,re.I)]
        if clocks:raise BoundaryError(f'Wave {number}: potential clock fields found; review before affirming unsupported timing. No values read.')
        if len(header)!=stored['header_columns']:raise BoundaryError('Actual TSV header differs from timing source evidence.')
        titles=[row for row in stored['timing_variable_catalog'] if re.search(policy['clock_title_pattern'],row['title'],re.I)]
        if titles:raise BoundaryError('A potentially usable clock title needs manual review before this timing omission can be affirmed.')
        prefix=f'R{number:02d}'
        recency=[prefix+'_AC1009_NN',prefix+'_AC1009_UN']
        attempts=[prefix+'_AN0135',prefix+'_AN0135_VALUE_INFO']
        if not set(recency+attempts).issubset(header):raise BoundaryError('Expected recency/conditional-date source fields differ from documentation.')
        headers.append({'wave':number,'file':wave['data'],'columns':len(header),'interview_clock_candidates':clocks,'potential_clock_titles':titles,'raw_quit_recency_fields':recency,'conditional_last_attempt_date_fields':attempts,'rows_read':0})
        for kind in ['codebook','questionnaire']:
            source=wave[kind];digest=fingerprint(root/source)
            if digest!=originals[source]['sha256'] or digest!=stored[kind+'_sha256']:raise BoundaryError('Source documentation changed since verified timing feasibility.')
            sources.append({'file':source,'sha256':digest})
    # Inspect physical Parquet schemas only, never participant rows or final labels.
    schema_report=json.loads((root/cc['output_dir']/cc['files']['schema']).read_text())
    schema_checks=[]
    for kind,definition in [('cohort','cohort_columns'),('ledger','ledger_columns')]:
        path=root/cc['output_dir']/cc['files'][kind]
        actual=pq.read_schema(path).names
        if actual!=[field['name'] for field in schema_report[definition]]:raise BoundaryError('Saved schema differs from actual Parquet schema.')
        prospective=[n for n in actual if re.search(r'interview_date|elapsed|event_time|time_to_|event_date|censor_time|relapse_date',n,re.I)]
        if prospective:raise BoundaryError('Cohort contains prospective timing fields; review rather than assuming they are valid survival data.')
        schema_checks.append({'file':str(path.relative_to(root)),'schema_columns':len(actual),'prospective_timing_columns':prospective,'rows_read':0})
    if not schema_report['timing_decision'].startswith('C'):raise BoundaryError('Implemented cohort schema timing decision differs.')
    rechecks=[]
    for check in policy['source_rechecks']:
        digest=fingerprint(root/check['file'])
        if digest!=originals[check['file']]['sha256']:raise BoundaryError('Timing source recheck original hash differs.')
        command=['pdftotext','-f',str(check['first_page']),'-l',str(check['last_page']),'-layout',str(root/check['file']),'-']
        try:result=subprocess.run(command,check=True,capture_output=True,text=True)
        except (FileNotFoundError,subprocess.CalledProcessError):raise BoundaryError('Local pdftotext unavailable/failed; cannot claim live documentation rechecks passed.') from None
        normalized=' '.join(result.stdout.split()).lower()
        if not all(text.lower() in normalized for text in check['required_text']):raise BoundaryError('Required source wording not found in page-restricted timing recheck.')
        rechecks.append({**check,'sha256':digest,'matched':True,'page_convention':'One-based physical PDF pages'})
    tree_manifest=verify_tree_run(root)
    classifier=root/policy['classifier_artifact']
    if fingerprint(classifier)!=tree_manifest['output_sha256'][policy['classifier_artifact']]:raise BoundaryError('Working classifier artifact differs.')
    model_result=json.loads((root/policy['classifier_result']).read_text())
    chosen=next(row for row in model_result['candidates'] if row['model']==model_result['selected_model'])
    profiles=json.loads((root/'configs/feature_mapping_final.json').read_text())['feature_sets']
    paths=['configs/timing_decision.json',policy['timing_feasibility'],policy['prediction_specification'],policy['source_evidence'],'src/path_project/timing.py']
    return {'decision':'C','timing_analysis_omitted':True,'local_PATH_inventory':{'files_checked':len(local_files),'unexpected_files':unexpected},'reason':policy['unsupported_reasons'],'header_checks':headers,'documentation_hashes':sources,
        'cohort_schema_checks':schema_checks,'live_documentation_rechecks':rechecks,
        'classifier':{'model':model_result['selected_model'],'profile':chosen['profile'],'features':profiles[chosen['profile']],'artifact':policy['classifier_artifact'],'sha256':fingerprint(classifier),'stage8_signature':tree_manifest['signature'],'status':'Retained unchanged; development-selected/calibrated, final-test evaluation pending'},
        'source_sha256':{name:fingerprint(root/name) for name in paths},'survey_or_cohort_answer_rows_read':0,'membership_note':'Existing split key membership is verified by the retained-model integrity checker; no test features/outcomes or survey/cohort answer rows are read.','models_fitted':0,'final_test_features_or_outcomes_read':False}


def build_app_metadata(policy,confirmation):
    validate_timing_policy(policy)
    return {'version':'1.0','timing_decision':'C','endpoint':policy['endpoint_label'],'prediction_time':'End of starting interview, using baseline answers only',
        'classifier_available':True,'classifier':confirmation['classifier'],'probability_validation_status':'Development only; final-test and new-user validity not established',
        **{key:False for key in CAPABILITIES},'supported_elapsed_time_horizons':[],
        'interval_description':policy['interval_description'],'timing_unavailable_message':policy['timing_unavailable_message'],
        'historical_recency_role':'last_cigarette_recency_days is an optional baseline history predictor, not follow-up time or time until relapse',
        'negative_outcome_meaning':'No cigarette smoking in the observed follow-up 30-day window; not continuous abstinence or an event-free survival interval',
        'missing_followup_meaning':'Unobserved outcome; not sustained abstinence or a fabricated censoring time',
        'claim_limits':policy['claim_limits'],'decision_document':'docs/timing_decision.md'}


def next_survey_output_metadata(metadata,elapsed_horizon=None,request_relapse_date=False):
    """Future app output guard: no conversion of a classifier score to time risk."""
    if metadata['timing_decision']!='C':raise BoundaryError('App timing decision differs from the documented classifier-only scope.')
    if any(metadata[key] is not False for key in CAPABILITIES) or metadata['supported_elapsed_time_horizons']:
        raise BoundaryError('App timing policy conflicts with documented unsupported timing.')
    if elapsed_horizon is not None or request_relapse_date:
        raise BoundaryError(metadata['timing_unavailable_message'])
    return {'endpoint':metadata['endpoint'],'interval_description':metadata['interval_description'],'elapsed_time_estimates_available':False,'timing_note':metadata['timing_unavailable_message']}
