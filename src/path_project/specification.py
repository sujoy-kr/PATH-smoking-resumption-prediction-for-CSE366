"""Validate the stage 2 scientific contract, without constructing a cohort."""
import csv
import json
from pathlib import Path
import re


def validate_specification(root):
    root = Path(root)
    spec = json.loads((root / 'configs/prediction_specification.json').read_text())
    project = json.loads((root / 'configs/project.json').read_text())
    evidence = json.loads((root / 'reports/prediction_source_evidence.json').read_text())
    originals = json.loads((root / 'docs/original_inputs.sha256.json').read_text())
    errors = []
    if spec['pairs'] != [[n, n + 1] for n in range(1, 8)]:
        errors.append('Core intervals must be the seven adjacent scheduled wave pairs.')
    if spec['timing_decision'] != 'C' or spec['skip_missing_wave'] or spec['require_all_eight_waves']:
        errors.append('Timing/cohort policy conflicts with the documented classification task.')
    if spec['identifier'] != 'PERSONID' or spec['identifier_role'] != 'join_and_participant_group_only':
        errors.append('PERSONID must remain join/group metadata.')
    if spec['baseline_requirements'] != {'former_established_equals': '1', 'past_30_day_equals': '2'}:
        errors.append('Baseline status codes do not match the specified cohort.')
    if spec['outcome_mapping'] != {'1': 1, '2': 0}:
        errors.append('Outcome must accept exactly documented Yes/No codes.')
    allowed = set(spec['allowed_inputs']['feature_allowlist'])
    if allowed.intersection(spec['forbidden_predictors']):
        errors.append('Forbidden predictor in feature allowlist.')
    for wave, proof in zip(project['waves'], evidence['waves'], strict=True):
        n = wave['wave']
        if proof['wave'] != n or proof['data_file'] != wave['data']:
            errors.append(f'Wave {n}: evidence source mismatch.')
        for kind in ('codebook', 'questionnaire'):
            if proof[kind + '_sha256'] != originals[wave[kind]]['sha256']:
                errors.append(f'Wave {n}: documentation fingerprint differs from original baseline.')
        mapping = spec['waves'][str(n)]
        sections = {r['variable']: r for r in proof['codebook_sections']}
        with (root / wave['data']).open(newline='', encoding='utf-8-sig') as source:
            header = next(csv.reader(source, delimiter='\t'))
        for role, variable in mapping.items():
            if variable not in header or variable not in sections:
                errors.append(f'Wave {n}: {role} lacks header/codebook support.')
            elif sections[variable]['file'] != wave['codebook'] or sections[variable]['pdf_page_start'] < 1:
                errors.append(f'Wave {n}: invalid source reference for {variable}.')
        for role in ('former_established', 'past_30_day', 'current_established'):
            content = sections.get(mapping[role], {}).get('section_text', '')
            if '1 = Yes' not in content or '2 = No' not in content:
                errors.append(f'Wave {n}: status value labels not verified for {role}.')
            missing = re.search(r'\(Range of\) Missing Values:\s*([^\n]+)', content)
            expected_missing = spec['documented_status_missing_codes'][str(n)][role]
            if missing is None or [v.strip() for v in missing.group(1).split(',')] != expected_missing:
                errors.append(f'Wave {n}: missing-code map lacks source support for {role}.')
        expected_suffix = '_REV' if n in (2, 3) else '_CIGS'
        if not mapping['former_established'].endswith(expected_suffix):
            errors.append(f'Wave {n}: wrong revised-status selection.')
        for variable in (mapping['last_smoked_number'], f'R{n:02d}_AC1004', f'R{n:02d}_AN0135'):
            if not any(variable in record['variables'] for record in proof['questionnaire_sections']):
                errors.append(f'Wave {n}: missing questionnaire routing evidence for {variable}.')
    for item in evidence.get('supplementary_documentation', []):
        if item['sha256'] != originals[item['file']]['sha256']:
            errors.append('Supplementary documentation differs from original baseline.')
        if set(item['page_text']) != {str(n) for n in item['pdf_pages']}:
            errors.append('Supplementary page evidence is incomplete.')
    return errors
