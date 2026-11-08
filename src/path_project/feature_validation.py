"""Validate feature roles, scientific metadata and actual local header mappings."""
import csv
import json
from pathlib import Path
import re

from path_project.documentation import fingerprint, response_labels, missing_codes


def validate_feature_mapping(root, mapping=None, evidence=None):
    root = Path(root)
    mapping = mapping or json.loads((root / 'configs/feature_mapping.json').read_text())
    evidence = evidence or json.loads((root / mapping['output_evidence']).read_text())
    project = json.loads((root / 'configs/project.json').read_text())
    task = json.loads((root / 'configs/prediction_specification.json').read_text())
    originals = json.loads((root / mapping['source_manifest']).read_text())
    errors = []
    if mapping['recipe_sha256'] != fingerprint(root / 'configs/feature_mapping_recipe.json'):
        errors.append('Curated recipe changed; rebuild documentation outputs before validation.')
    names = [f['name'] for f in mapping['fields']]
    if len(names) != len(set(names)):
        errors.append('Duplicate common feature names.')
    candidates = [f for f in mapping['fields'] if f['role'] == 'candidate_predictor']
    if not 20 <= len(candidates) <= 40:
        errors.append('Expected 20–40 compact candidate predictors.')
    expected_names = [f['name'] for f in candidates]
    if mapping['candidate_predictor_names'] != expected_names:
        errors.append('Candidate allowlist differs from role-tagged dictionary.')
    if task['allowed_inputs']['feature_allowlist'] != expected_names:
        errors.append('Prediction contract candidate allowlist differs from feature mapping.')
    roles = {'candidate_predictor', 'cohort_field', 'outcome_field', 'identifier', 'design_weight_field'}
    headers = {}
    for wave in project['waves']:
        with (root / wave['data']).open(newline='', encoding='utf-8-sig') as stream:
            headers[str(wave['wave'])] = next(csv.reader(stream, delimiter='\t'))
    for file, metadata in evidence['documents'].items():
        if metadata['sha256'] != originals[file]['sha256'] or fingerprint(root / file) != metadata['sha256']:
            errors.append(f'Documentation fingerprint changed: {file}')
    forbidden = re.compile(r'^(?:PERSONID|CASEID|VARPSU|VARSTRAT)$|_PWGT|_ADULT_MODE$|R_A_(?:FMR_ESTD_CIGS|CUR_ESTD_CIGS|P30D_CIGS)(?:_REV)?$')
    for field in mapping['fields']:
        name = field['name']
        if field['role'] not in roles:
            errors.append(f'{name}: unknown field role.')
        for required in ['description', 'former_smoker_applicability', 'historical_dependency', 'prediction_time_availability', 'cross_wave_notes', 'output_units']:
            if not field.get(required):
                errors.append(f'{name}: missing {required}.')
        if set(field['waves']) != set(headers):
            errors.append(f'{name}: incomplete eight-wave mapping.')
            continue
        if field['role'] == 'candidate_predictor' and (not field['app']['can_supply'] or not field['app']['prompt']):
            errors.append(f'{name}: candidate has no realistic documented app input.')
        for wave, entry in field['waves'].items():
            label = f'{name} wave {wave}'
            if entry['source_wave'] != int(wave):
                errors.append(f'{label}: source points to a different wave.')
            if entry['availability'] != 'available':
                if entry['source_columns'] or field['role'] != 'design_weight_field':
                    errors.append(f'{label}: unjustified unavailable feature mapping.')
                continue
            if not entry['source_columns']:
                errors.append(f'{label}: available mapping has no columns.')
            if [c['column'] for c in entry['components']] != entry['source_columns']:
                errors.append(f'{label}: source/component column mismatch.')
            if field['role'] == 'candidate_predictor':
                if entry['source_time'] != 'starting_interview' or not entry['available_at_prediction_time']:
                    errors.append(f'{label}: future information is not a candidate predictor.')
                if any(forbidden.search(column) for column in entry['source_columns']):
                    errors.append(f'{label}: identifier, administrative or task-label predictor forbidden.')
                if not entry.get('prediction_time_basis'):
                    errors.append(f'{label}: missing temporal availability justification.')
            if field['role'] == 'outcome_field' and (entry['source_time'] != 'following_interview' or entry['available_at_prediction_time']):
                errors.append(f'{label}: outcome timing is not explicitly separated.')
            if not entry['structural_skip_rule']:
                errors.append(f'{label}: no structural-skip policy.')
            for component in entry['components']:
                column = component['column']
                if column not in headers[wave]:
                    errors.append(f'{label}: column absent: {column}')
                prefix = re.match(r'^R(\d{2})', column)
                if prefix and int(prefix[1]) != int(wave):
                    errors.append(f'{label}: cross-wave input column {column}')
                refs = component['evidence_refs']
                cb = evidence['records'].get(f'{wave}:codebook:{column}')
                if not refs or cb is None or cb['pdf_page_start'] < 1:
                    errors.append(f'{label}: no exact source evidence for {column}')
                    continue
                if cb['variable'] != column or cb['sha256'] != evidence['documents'][cb['file']]['sha256']:
                    errors.append(f'{label}: source record mismatch for {column}')
                if component['missing_codes'] != missing_codes(cb['section_text']):
                    errors.append(f'{label}: undocumented missing-code map for {column}')
                parsed = response_labels(cb['section_text'])
                expected_labels = {k: v for k, v in parsed.items() if k not in component['missing_codes'] and not k.startswith('-')}
                if component['source_value_labels'] != expected_labels:
                    errors.append(f'{label}: response labels differ from documentation for {column}')
                if field['role'] == 'candidate_predictor':
                    dependencies = re.findall(r'\b(?:R|X|T)(\d{2})[A-Z0-9_]+\b', component['meaning_and_eligibility'])
                    if any(int(number) > int(wave) for number in dependencies):
                        errors.append(f'{label}: source derivation references a later interview for {column}')
                if set(component['missing_reason_by_code']) != set(component['missing_codes']):
                    errors.append(f'{label}: missing reasons do not cover documented sentinels.')
                for ref in refs:
                    if ref not in evidence['records']:
                        errors.append(f'{label}: unresolved evidence reference {ref}')
            for ref in entry['additional_evidence_refs']:
                if ref not in evidence['records']:
                    errors.append(f'{label}: unresolved additional reference {ref}')
            for assertion in entry.get('semantic_source_assertions', []):
                ref = assertion['evidence_key']
                record = evidence['records'].get(ref)
                if record is None or ref not in entry['additional_evidence_refs']:
                    errors.append(f'{label}: unresolved semantic evidence {ref}')
                    continue
                normalize = lambda text: re.sub(r'\s+', ' ', text).casefold()
                texts = {'source': record['section_text'],
                         'description': entry.get('description', field['description']),
                         'app_prompt': entry.get('app_prompt', field['app']['prompt']),
                         'app_notes': entry.get('app_notes', field['app']['notes'])}
                for target, text in texts.items():
                    for phrase in assertion.get(target + '_must_contain', []):
                        if normalize(phrase) not in normalize(text):
                            errors.append(f'{label}: semantic {target} lacks documented term {phrase!r}')
                    for phrase in assertion.get(target + '_must_not_contain', []):
                        if normalize(phrase) in normalize(text):
                            errors.append(f'{label}: semantic {target} contradicts product scope: {phrase!r}')
            transform = entry['transform']
            kind = transform.get('kind')
            if not isinstance(kind, str) or kind not in {'categorical_map','numeric','number_unit','household_checkboxes','metadata_only'}:
                errors.append(f'{label}: unsupported transformation schema.')
                continue
            if kind == 'metadata_only' and field['role'] == 'candidate_predictor':
                errors.append(f'{label}: candidate cannot use a metadata-only transform.')
            if transform['kind'] == 'categorical_map' and entry['components']:
                domain = set(entry['components'][0]['source_value_labels'])
                if set(transform['mapping']) != domain:
                    errors.append(f'{label}: category recode does not cover exactly valid source codes.')
                if not set(map(str,transform['mapping'].values())).issubset(field['output_labels']):
                    errors.append(f'{label}: recode output lacks an understandable label.')
            if transform['kind'] == 'number_unit':
                unit = next((c for c in entry['components'] if c['column'] == transform['unit_column']), None)
                if unit is None or set(transform['unit_multipliers']) != set(unit['source_value_labels']):
                    errors.append(f'{label}: conversion unit codes differ from source labels.')
    # Check primary cohort/outcome fields against the preserved endpoint contract.
    by_name = {f['name']: f for f in mapping['fields']}
    for wave in headers:
        for name, task_key in [('former_established_baseline','former_established'),('past30_cigarettes_baseline','past_30_day'),('current_established_baseline_qc','current_established'),('past30_cigarettes_followup','past_30_day'),('current_established_followup','current_established')]:
            if by_name[name]['waves'][wave]['source_columns'] != [task['waves'][wave][task_key]]:
                errors.append(f'Wave {wave}: task status mapping changed for {name}.')
    if mapping['policy']['missing_duration_is_zero'] or not mapping['policy']['no_outcome_feature_selection']:
        errors.append('Missing-duration or outcome-selection policy violates the scientific contract.')
    return errors
