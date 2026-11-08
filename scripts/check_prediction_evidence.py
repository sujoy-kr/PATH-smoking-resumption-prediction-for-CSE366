"""Independently check cited PDF pages using page-restricted pdftotext extraction.

Does not read participant rows, fit anything, or touch evaluation data.
"""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from path_project.specification import validate_specification


def check():
    spec = json.loads((ROOT / 'configs/prediction_specification.json').read_text())
    evidence = json.loads((ROOT / 'reports/prediction_source_evidence.json').read_text())
    failures = validate_specification(ROOT)
    checked = []
    for wave in evidence['waves']:
        number = wave['wave']
        mapping = spec['waves'][str(number)]
        codebook_variables = [mapping[key] for key in ('former_established', 'past_30_day', 'current_established', 'last_smoked_number')]
        codebook_variables.append(f'R{number:02d}_AN0135')
        questionnaire_variables = [f'R{number:02d}_AC1004', mapping['last_smoked_number'], f'R{number:02d}_AN0135']
        for kind, variables in [('codebook', codebook_variables), ('questionnaire', questionnaire_variables)]:
            for variable in variables:
                record = next(x for x in wave[kind + '_sections'] if
                              (x.get('variable') == variable if kind == 'codebook' else variable in x['variables']))
                page = str(record['pdf_page_start'])
                result = subprocess.run(['pdftotext', '-f', page, '-l', page, '-layout', str(ROOT / record['file']), '-'],
                                        check=True, capture_output=True, text=True)
                ok = variable in result.stdout
                checked.append({'file': record['file'], 'variable': variable, 'pdf_page': int(page), 'found': ok})
                if not ok:
                    failures.append(f'{variable}: not found on cited starting PDF page {page}')
    return {'method': 'Independent pdftotext -f PAGE -l PAGE page extraction plus contract validation',
            'page_checks': checked, 'page_checks_passed': sum(r['found'] for r in checked),
            'page_checks_total': len(checked), 'errors': failures}


if __name__ == '__main__':
    result = check()
    output = ROOT / 'reports/prediction_specification_checks.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"Cited PDF page checks: {result['page_checks_passed']}/{result['page_checks_total']}; errors: {len(result['errors'])}")
    for error in result['errors']:
        print(error)
    raise SystemExit(bool(result['errors']))
