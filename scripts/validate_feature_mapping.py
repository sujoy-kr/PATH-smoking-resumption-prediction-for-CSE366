"""Validate source headers, roles, evidence and the metadata-only CSV dictionary."""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from path_project.feature_validation import validate_feature_mapping


def run(root=ROOT):
    mapping = json.loads((root / 'configs/feature_mapping.json').read_text())
    evidence = json.loads((root / mapping['output_evidence']).read_text())
    errors = validate_feature_mapping(root, mapping, evidence)
    with (root / mapping['output_dictionary']).open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    expected = {(field['name'],wave):(field,entry) for field in mapping['fields'] for wave,entry in field['waves'].items()}
    if len(rows) != len(expected) or {(r['common_name'],r['wave']) for r in rows} != set(expected):
        errors.append('CSV dictionary rows do not match every configured field/wave exactly once.')
    for row in rows:
        pair = expected.get((row['common_name'],row['wave']))
        if pair is None:
            continue
        field, entry = pair
        if row['role'] != field['role'] or json.loads(row['source_columns']) != entry['source_columns']:
            errors.append(f"CSV dictionary mismatch: {row['common_name']} wave {row['wave']}")
        if json.loads(row['transform']) != entry['transform']:
            errors.append(f"CSV transformation mismatch: {row['common_name']} wave {row['wave']}")
        expected_labels = {c['column']:c['source_value_labels'] for c in entry['components']}
        if json.loads(row['source_response_labels']) != expected_labels:
            errors.append(f"CSV response-label mismatch: {row['common_name']} wave {row['wave']}")
        expected_text = {'description': entry.get('description', field['description']),
                         'app_prompt': entry.get('app_prompt', field['app']['prompt']) or '',
                         'app_notes': entry.get('app_notes', field['app']['notes'])}
        if any(row[key] != value for key, value in expected_text.items()):
            errors.append(f"CSV wave-specific wording mismatch: {row['common_name']} wave {row['wave']}")
        if json.loads(row['product_scope']) != entry.get('product_scope', {}):
            errors.append(f"CSV product-scope mismatch: {row['common_name']} wave {row['wave']}")
        if json.loads(row['semantic_source_assertions']) != entry.get('semantic_source_assertions', []):
            errors.append(f"CSV semantic-evidence mismatch: {row['common_name']} wave {row['wave']}")
    return {'candidate_predictors': len(mapping['candidate_predictor_names']),
            'role_counts': {role:len(names) for role,names in mapping['role_groups'].items()},
            'waves_checked': 8, 'field_wave_rows': len(rows),
            'unique_source_columns_by_wave': {wave:len(item['configured_source_columns']) for wave,item in evidence['header_audit'].items()},
            'source_column_references_checked': sum(len(entry['source_columns']) for field in mapping['fields'] for entry in field['waves'].values()),
            'source_documents_checked': len(evidence['documents']),
            'documentation_records': len(evidence['records']),
            'errors': errors, 'method': 'Actual TSV headers only; original PDF fingerprints, declared roles/temporal availability, documented code domains and dictionary consistency. No survey rows or outcomes used.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-write', action='store_true', help='Read-only validation; do not update the saved aggregate report.')
    args = parser.parse_args()
    result = run()
    if not args.no_write:
        (ROOT / 'reports/feature_mapping_validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f"Feature mapping: {result['candidate_predictors']} candidates, {result['source_column_references_checked']} column references, {result['field_wave_rows']} dictionary rows; {len(result['errors'])} errors")
    for error in result['errors']:
        print(error)
    raise SystemExit(bool(result['errors']))
