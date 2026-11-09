"""Versioned final feature profiles and deterministic demo-answer encoding."""
import csv,json,math
from pathlib import Path
from path_project.evaluation import BoundaryError
from path_project.documentation import fingerprint

MISSING={'unanswered':'app_unanswered','dont_know':'app_dont_know','prefer_not_to_answer':'app_refused','not_applicable':'app_not_applicable','not_previously_asked':'app_not_previously_asked'}


def validate_final_inputs(root):
    root=Path(root)
    final=json.loads((root/'configs/feature_mapping_final.json').read_text())
    for name,digest in final['base_sha256'].items():
        if fingerprint(root/name)!=digest:raise BoundaryError('Final input base mapping/specification/dictionary changed.')
    base=json.loads((root/final['base_mapping']).read_text())
    allowed=base['candidate_predictor_names']
    if not set(final['feature_sets']['minimal']).issubset(final['feature_sets']['app']):raise BoundaryError('Minimal comparison must be a subset of the app inputs.')
    for names in final['feature_sets'].values():
        if not names or len(names)!=len(set(names)) or not set(names).issubset(allowed):raise BoundaryError('Final profile contains unavailable/duplicate/forbidden inputs.')
    base_fields={field['name']:field for field in base['fields']}
    for field in final['fields']:
        restored={key:value for key,value in field.items() if key!='final_profiles'}
        if restored!=base_fields[field['name']]:raise BoundaryError('Final mapping changes a locked source meaning or transformation.')
        memberships=[profile for profile,names in final['feature_sets'].items() if field['name'] in names]
        if field['final_profiles']!=memberships:raise BoundaryError('Final field profile membership mismatch.')
    specification=json.loads((root/'configs/prediction_specification_final.json').read_text())
    if specification['final_feature_sets']!=final['feature_sets'] or specification['allowed_inputs']['feature_allowlist']!=final['feature_sets']['app'] or specification['cohort_change']:
        raise BoundaryError('Final prediction specification differs from the input profiles.')
    with (root/'docs/feature_dictionary.csv').open(newline='') as stream:original_rows=list(csv.DictReader(stream))
    with (root/'docs/feature_dictionary_final.csv').open(newline='') as stream:final_rows=list(csv.DictReader(stream))
    if len(original_rows)!=len(final_rows):raise BoundaryError('Final dictionary dropped source rows.')
    for old,new in zip(original_rows,final_rows):
        if any(new[key]!=value for key,value in old.items()):raise BoundaryError('Final dictionary changes a source-mapping cell.')
        expected=';'.join(profile for profile,names in final['feature_sets'].items() if old['common_name'] in names)
        if new['final_profiles']!=expected or new['final_app_input']!=str(old['common_name'] in final['feature_sets']['app']).lower():raise BoundaryError('Final dictionary profile mismatch.')
    questions=json.loads((root/'configs/app_questions.json').read_text())
    if [q['feature'] for q in questions['questions']]!=final['feature_sets']['app']:raise BoundaryError('Question list differs from final app allowlist.')
    for question in questions['questions']:
        base_field=base_fields[question['feature']]
        if question['options']!=base_field['output_labels']:raise BoundaryError('App response labels differ from the documented mapping.')
        if set(question['waves'])!={str(w) for w in range(1,8)}:raise BoundaryError('A prediction-wave app question is missing.')
        for wave,entry in question['waves'].items():
            source=base_field['waves'][wave]
            if entry['source_columns']!=source['source_columns']:raise BoundaryError('App question source differs from the locked baseline mapping.')
            if source['source_time']!='starting_interview' or source['source_wave']!=int(wave):raise BoundaryError('Future information in final input.')
            if question['kind']=='number_unit' and entry['unit_multipliers']!=source['transform']['unit_multipliers']:raise BoundaryError('App duration units differ from the documented mapping.')
            if not entry['source_evidence'] or not entry['prompt']:raise BoundaryError('App question lacks local source meaning.')
    return final,questions


def encode_app_answers(root, answers, wave, allow_recent=False):
    """Return values and explicit reason metadata; never fabricate an answer."""
    final,questions=validate_final_inputs(root)
    if str(wave) not in {str(w) for w in range(1,8)}:raise BoundaryError('Select a documented starting-wave context, 1–7.')
    if set(answers)-set(final['feature_sets']['app']):raise BoundaryError('Unknown/research-only/future app answer rejected.')
    result={};reasons={}
    for question in questions['questions']:
        name=question['feature'];raw=answers.get(name,'unanswered');entry=question['waves'][str(wave)]
        if raw is None:raw='unanswered'
        if isinstance(raw,str) and raw in MISSING:
            result[name]=None;reasons[name]=MISSING[raw];continue
        if question['kind']=='category':
            if str(raw) not in question['options']:raise BoundaryError('App answer is not a configured response option.')
            value=float(raw)
        else:
            if not isinstance(raw,dict) or set(raw)!={'number','unit'}:raise BoundaryError('Recency requires both number and unit, or an explicit missing answer.')
            try:number=float(raw['number'])
            except (ValueError,TypeError):raise BoundaryError('Recency requires a positive whole number.') from None
            unit=str(raw['unit'])
            if not math.isfinite(number) or number<=0 or number!=int(number) or unit not in entry['unit_multipliers']:raise BoundaryError('Recency number/unit outside the documented question domain.')
            maximum=entry['quantity_entry_width_limit_by_unit'].get(unit)
            if maximum is not None and number>maximum:raise BoundaryError('Recency quantity exceeds the documented entry width for this unit/context; do not truncate or invent a value.')
            value=number*entry['unit_multipliers'][unit]
            if not math.isfinite(value):raise BoundaryError('Recency conversion is not finite.')
            if value<=30 and not allow_recent:raise BoundaryError('Recency conflicts with the no-past-30-day-use cohort; clarify eligibility rather than altering answers.')
        result[name]=value;reasons[name]='observed'
    return result,reasons


def fit_profile_pipeline(root, estimator, profile, fold=None):
    """Future fitting helper; no fitting occurs while generating stage 6 metadata."""
    final,_=validate_final_inputs(root)
    if profile not in final['feature_sets']:raise BoundaryError('Unknown final feature profile.')
    from path_project.training_boundaries import fit_development_pipeline
    return fit_development_pipeline(root,estimator,fold=fold,predictors=final['feature_sets'][profile])
