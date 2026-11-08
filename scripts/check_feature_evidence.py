"""Independently verify every indexed documentation heading on its cited PDF page.

Groups references by PDF page; reads documentation only, without rewriting sources
or touching participant/split/model files. --no-write is suitable for audits.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    evidence = json.loads((root / 'reports/feature_mapping_evidence.json').read_text())
    groups = defaultdict(list)
    for key, record in evidence['records'].items():
        groups[(record['file'], record['pdf_page_start'])].append((key, record['variable']))
    results = []
    for (file, page), records in sorted(groups.items()):
        result = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), '-layout', str(root / file), '-'],
                                check=True, capture_output=True, text=True)
        for key, variable in records:
            results.append({'evidence_key': key, 'file': file, 'pdf_page': page,
                            'variable': variable, 'found': variable in result.stdout})
    return {'method': 'Independent page-restricted pdftotext heading checks; documentation only.',
            'references_checked': len(results), 'unique_pdf_pages_checked': len(groups),
            'references_passed': sum(item['found'] for item in results),
            'errors': [item for item in results if not item['found']], 'checks': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-write', action='store_true')
    args = parser.parse_args()
    result = check()
    if not args.no_write:
        (ROOT / 'reports/feature_evidence_checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f"Feature source headings: {result['references_passed']}/{result['references_checked']}; {result['unique_pdf_pages_checked']} physical PDF pages; {len(result['errors'])} errors")
    for error in result['errors']:
        print(error['evidence_key'], error['file'], error['pdf_page'])
    raise SystemExit(bool(result['errors']))
