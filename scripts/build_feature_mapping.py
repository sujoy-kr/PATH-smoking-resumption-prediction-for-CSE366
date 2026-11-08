"""Enrich the curated feature recipe using local PDFs and TSV headers only.

No participant rows, cohort records, splits or outcomes are read. Numeric codebook
summary extrema are recorded as descriptive evidence, never as validity limits.
"""
import csv
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from path_project.documentation import (fingerprint, pdf_text, sections, response_labels, missing_codes,
                                        meaning_blocks, observed_range, explicit_ranges)


def build(root=ROOT):
    recipe = json.loads((root / 'configs/feature_mapping_recipe.json').read_text())
    project = json.loads((root / recipe['source_inputs']).read_text())
    manifest = json.loads((root / recipe['source_manifest']).read_text())
    evidence = {'page_convention': 'One-based physical PDF pages; exact section variables are recorded.',
                'selection_basis': recipe['selection_basis'], 'documents': {}, 'records': {}, 'header_audit': {}}
    mappings = deepcopy(recipe)
    mappings['recipe_sha256'] = fingerprint(root / 'configs/feature_mapping_recipe.json')
    mapping_fields = mappings['fields']
    for wave in project['waves']:
        number = wave['wave']
        prefix = f'R{number:02d}'
        with (root / wave['data']).open(newline='', encoding='utf-8-sig') as stream:
            header = next(csv.reader(stream, delimiter='\t'))
        catalogs = {}
        for kind in ['codebook', 'questionnaire']:
            cache = root / recipe['cache_dir'] / f'w{number}-{kind}.txt'
            text, digest = pdf_text(root / wave[kind], cache)
            if digest != manifest[wave[kind]]['sha256']:
                raise ValueError(f'Original documentation changed: {wave[kind]}')
            evidence['documents'][wave[kind]] = {'sha256': digest}
            catalogs[kind] = sections(text, questionnaire=kind == 'questionnaire')

        def register(kind, variable):
            record = catalogs[kind].get(variable)
            if record is None:
                return None
            key = f'{number}:{kind}:{variable}'
            evidence['records'][key] = {'file': wave[kind], 'variable': variable,
                                        'sha256': evidence['documents'][wave[kind]]['sha256'], **record}
            return key

        def describe(variable):
            if variable not in header:
                raise ValueError(f'Wave {number}: missing configured input column {variable}')
            cbkey = register('codebook', variable)
            if cbkey is None:
                raise ValueError(f'Wave {number}: codebook section absent for {variable}')
            content = catalogs['codebook'][variable]['section_text']
            all_labels = response_labels(content)
            missing = missing_codes(content)
            valid = {k: v for k, v in all_labels.items() if k not in missing and not k.startswith('-')}
            raw_references = sorted(set([variable] + re.findall(r'\b'+prefix+r'_[A-Z0-9_]+\b', meaning_blocks(content))))
            qkeys = sorted({key for var in raw_references if (key := register('questionnaire', var))})
            qprose = [meaning_blocks(evidence['records'][key]['section_text']) for key in qkeys]
            type_match = re.search(r'Variable Type:\s*(\w+)', content)
            historical = sorted({token for token in re.findall(r'\b(?:R|X|T)\d{2}[A-Z0-9_]+\b', meaning_blocks(content))
                                 if int(token[1:3]) < number})
            bounds = explicit_ranges(meaning_blocks(content))
            # A routing dependency's range is not this variable's response range.
            # For example alcohol days (0–30) occurs in the drinks/day ASK rule.
            own_questionnaire = catalogs['questionnaire'].get(variable)
            if own_questionnaire:
                bounds += explicit_ranges(meaning_blocks(own_questionnaire['section_text']))
            own_prose = meaning_blocks(content) + '\n' + (meaning_blocks(own_questionnaire['section_text']) if own_questionnaire else '')
            entry_constraints = [line.strip() for line in own_prose.splitlines()
                                 if re.search(r'(?i)\ballow\b.*\bdigits?\b|\bwhole number\b|\brange(?: check)?\s*:', line)]
            precision = re.search(r'decimal:\s*(\d+)', content)
            # Preserve source boundaries; never substitute observed extrema for them.
            domain = {'kind': 'enumerated' if valid else 'unlabelled_numeric_or_identifier',
                      'valid_codes': list(valid), 'explicit_documented_bounds': [] if valid else bounds,
                      'related_program_ranges_not_category_code_bounds': bounds if valid else [],
                      'decimal_places_as_released': int(precision[1]) if precision else None,
                      'program_entry_constraints_verbatim': entry_constraints,
                      'bounds_note': 'Source check strength (soft/hard/not specified) is retained. Transform bounds are declared analytic admissibility rules, not observed extrema. When no numeric range is listed, inspect digit/unit/routing constraints retained verbatim; no finite bound is invented.'}
            return {'column': variable, 'variable_type': type_match[1] if type_match else 'not stated',
                    'source_value_labels': valid, 'missing_codes': missing,
                    'missing_reason_by_code': {k: recipe['policy']['missing_code_reasons'].get(k, 'documented_missing') for k in missing},
                    'missing_value_labels': {k: all_labels.get(k, 'System missing' if k == '.' else 'See exact missing-value table in source') for k in missing},
                    'valid_domain': domain, 'observed_codebook_range_not_validity_bounds': observed_range(content),
                    'meaning_and_eligibility': meaning_blocks(content), 'questionnaire_eligibility_and_program': qprose,
                    'historical_references_in_source': historical,
                    'evidence_refs': [cbkey] + qkeys}

        for field in mapping_fields:
            entry = field['waves'][str(number)]
            entry['source_wave'] = number
            entry['source_time'] = 'following_interview' if field['role'] == 'outcome_field' else 'starting_interview'
            entry['available_at_prediction_time'] = field['role'] != 'outcome_field'
            entry['availability'] = 'available' if entry['source_columns'] else 'unavailable_in_local_release'
            entry['components'] = [describe(variable) for variable in entry['source_columns']]
            extra_q = []
            for variable in entry.pop('questionnaire_variables'):
                key = register('questionnaire', variable)
                if key:
                    extra_q.append(key)
            for assertion in entry.get('semantic_source_assertions', []):
                source_wave, kind, variable = assertion['evidence_key'].split(':', 2)
                if int(source_wave) != number or kind not in catalogs:
                    raise ValueError(f'Wave {number}: invalid semantic source {assertion["evidence_key"]}')
                key = register(kind, variable)
                if key is None:
                    raise ValueError(f'Wave {number}: semantic evidence absent for {variable}')
                extra_q.append(key)
            # Intensity eligibility belongs to the raw questions; retain the supplied
            # derived counterparts as a unit-conversion cross-check, not a second input.
            supporting = []
            if field['name'] == 'prior_regular_cigarettes_per_day':
                supporting.append(prefix + 'R_A_PERDAY_FMR_CIGS')
            if field['name'] == 'last_cigarette_recency_days' and number != 2:
                supporting.append(prefix + 'R_A_DAYSQUIT_CIGS')
            for variable in supporting:
                key = register('codebook', variable)
                if key:
                    extra_q.append(key)
            entry['additional_evidence_refs'] = sorted(set(extra_q))
            entry['additional_eligibility_prose'] = [meaning_blocks(evidence['records'][key]['section_text']) for key in entry['additional_evidence_refs']]
            entry['prior_wave_dependency'] = {
                'explicit_join_required': False,
                'earlier_fields_referenced_in_official_derivations': sorted({token for item in entry['components'] for token in item['historical_references_in_source']}),
                'policy': field['historical_dependency']}
            if not entry['source_columns']:
                entry['unavailability_reason'] = 'No corresponding design/weight columns in this local adult header; no placeholder column is invented.'
            if field['role'] == 'candidate_predictor':
                entry['former_smoker_applicability'] = field['former_smoker_applicability']
                entry['input_units'] = ('See exact response labels and question/program prose per source component; output units are ' + field['output_units'])
                if field['name'] == 'alcohol_drinks_per_drinking_day':
                    limits = [b for component in entry['components'] for b in component['valid_domain']['explicit_documented_bounds']]
                    if limits:
                        # A repeated source range is the same check, not data-learned clipping.
                        unique = {(b['minimum'], b['maximum']) for b in limits}
                        if len(unique) != 1:
                            raise ValueError(f'Wave {number}: ambiguous drinks range checks {unique}')
                        low, high = next(iter(unique))
                        entry['transform'].update(minimum=low, maximum=high)
                entry['prediction_time_basis'] = 'All configured input columns are from the starting-wave file. These are current/retrospective interview responses or official derivations of current/earlier information. No future interview values or learned transformation are used.'
        evidence['header_audit'][str(number)] = {
            'data_file': wave['data'], 'header_columns': len(header),
            'configured_source_columns': sorted({col for field in mapping_fields for col in field['waves'][str(number)]['source_columns']}),
            'derived_daysquit_present': prefix + 'R_A_DAYSQUIT_CIGS' in header,
            'raw_last_cigarette_number_present': prefix + '_AC1009_NN' in header,
            'raw_last_cigarette_unit_present': prefix + '_AC1009_UN' in header,
            'missing_configured_columns': []}
    mappings['source_evidence'] = recipe['output_evidence']
    mappings['candidate_predictor_names'] = [f['name'] for f in mapping_fields if f['role'] == 'candidate_predictor']
    mappings['role_groups'] = {role: [f['name'] for f in mapping_fields if f['role'] == role] for role in sorted({f['role'] for f in mapping_fields})}
    evidence['extractor_version'] = subprocess.run(['pdftotext', '-v'], capture_output=True, text=True, check=True).stderr.splitlines()[0]
    (root / recipe['output_mapping']).write_text(json.dumps(mappings, indent=2, ensure_ascii=False) + '\n')
    (root / recipe['output_evidence']).write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + '\n')
    write_dictionary(root, mappings, evidence)
    return mappings, evidence


def dictionary_rows(mapping, evidence):
    for field in mapping['fields']:
        for wave, entry in field['waves'].items():
            all_refs = sorted({ref for component in entry['components'] for ref in component['evidence_refs']} | set(entry['additional_evidence_refs']))
            references = [{'file': evidence['records'][key]['file'], 'variable': evidence['records'][key]['variable'],
                           'pdf_page_start': evidence['records'][key]['pdf_page_start'], 'evidence_key': key} for key in all_refs]
            components = entry['components']
            yield {'common_name': field['name'], 'role': field['role'], 'family': field['family'],
                   'description': entry.get('description', field['description']), 'wave': wave, 'availability': entry['availability'],
                   'source_columns': entry['source_columns'], 'source_time': entry['source_time'],
                   'source_response_labels': {c['column']: c['source_value_labels'] for c in components},
                   'source_valid_ranges': {c['column']: c['valid_domain'] for c in components},
                   'output_units': field['output_units'], 'output_labels': field['output_labels'],
                   'missing_codes_and_labels': {c['column']: {'codes': c['missing_codes'], 'labels': c['missing_value_labels']} for c in components},
                   'structural_skip_rule': entry['structural_skip_rule'],
                   'eligibility_and_program': {c['column']: {'codebook': c['meaning_and_eligibility'], 'questionnaire': c['questionnaire_eligibility_and_program']} for c in components},
                   'additional_eligibility_prose': entry['additional_eligibility_prose'],
                   'former_smoker_applicability': field['former_smoker_applicability'],
                   'historical_dependency': entry['prior_wave_dependency'],
                   'available_at_prediction_time': entry['available_at_prediction_time'],
                   'app_can_supply': field['app']['can_supply'], 'app_prompt': entry.get('app_prompt', field['app']['prompt']),
                   'app_notes': entry.get('app_notes', field['app']['notes']),
                   'product_scope': entry.get('product_scope', {}),
                   'semantic_source_assertions': entry.get('semantic_source_assertions', []),
                   'transform': entry['transform'],
                   'cross_wave_notes': field['cross_wave_notes'], 'source_evidence': references}


def write_dictionary(root, mapping, evidence):
    rows = list(dictionary_rows(mapping, evidence))
    with (root / mapping['output_dictionary']).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()})


if __name__ == '__main__':
    mapping, evidence = build()
    print(f"Built {len(mapping['candidate_predictor_names'])} candidate predictors; {len(mapping['fields'])} separated fields; {len(evidence['records'])} documentation references.")
    print(f"Wrote {mapping['output_mapping']}, {mapping['output_dictionary']}, {mapping['output_evidence']}")
