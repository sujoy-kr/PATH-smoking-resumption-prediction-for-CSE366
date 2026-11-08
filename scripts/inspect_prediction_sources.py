"""Build a reproducible documentation evidence index. Reads headers, never survey rows.

PDF page numbers are one-based physical pages, not printed footer numbers.
Extracted PDF text stays in the ignored cache; the report contains documentation only.
"""
from pathlib import Path
import csv
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from path_project.inventory import sha256


def load_pdf_text(source, target):
    # Always regenerate from the original PDF: do not trust stale/truncated cached text.
    subprocess.run(['pdftotext', '-layout', str(source), str(target)], check=True)
    return target.read_text()


def codebook_sections(text):
    pattern = r'(?m)(?:^|(?<=\f))[ \t]*(PERSONID|R\d{2}[A-Z0-9_]+):'
    matches = list(re.finditer(pattern, text))
    sections = {}
    for index, match in enumerate(matches):
        start = match.start(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        end = start + len(text[start:end].rstrip())
        sections[match.group(1)] = (start, end, text[start:end].strip())
    return sections


def reference(text, start, end, source):
    return {'file': source, 'pdf_page_start': text[:start].count('\f') + 1,
            'pdf_page_end': text[:max(start, end - 1)].count('\f') + 1}


def inspect(root=ROOT):
    project = json.loads((root / 'configs/project.json').read_text())
    settings = json.loads((root / 'configs/prediction_specification.json').read_text())
    cache = root / project['runtime_cache_dir'] / 'stage2'
    cache.mkdir(parents=True, exist_ok=True)
    report = {'page_convention': 'One-based physical PDF pages; section IDs are authoritative.',
              'method': 'pdftotext -layout for all 16 main PDFs; header-only TSV inspection.',
              'waves': []}
    for wave in project['waves']:
        number = wave['wave']
        prefix = f'R{number:02d}'
        with (root / wave['data']).open(newline='', encoding='utf-8-sig') as source:
            header = next(csv.reader(source, delimiter='\t'))
        cb = load_pdf_text(root / wave['codebook'], cache / f'w{number}-codebook.txt')
        qt = load_pdf_text(root / wave['questionnaire'], cache / f'w{number}-questionnaire.txt')
        sections = codebook_sections(cb)
        wanted = settings['source_review_suffixes']
        variables = [prefix + suffix for suffix in wanted]
        variables += ['PERSONID']
        evidence = []
        for variable in variables:
            if variable not in sections:
                continue
            start, end, content = sections[variable]
            evidence.append({'variable': variable, 'in_data_header': variable in header,
                             **reference(cb, start, end, wave['codebook']), 'section_text': content})
        qmatches = list(re.finditer(r'(?m)^[ \t]*Variable\(s\):[^\n]+', qt))
        qsections = []
        for index, match in enumerate(qmatches):
            tokens = re.findall(r'R\d{2}[A-Z0-9_]+', match.group())
            if not set(tokens).intersection(variables):
                continue
            start = match.start()
            end = qmatches[index + 1].start() if index + 1 < len(qmatches) else len(qt)
            # Routing boxes between questions are intentionally retained.
            qsections.append({'variables': tokens, **reference(qt, start, end, wave['questionnaire']),
                              'section_text': qt[start:end].strip()})
        date_catalog = []
        for variable, (start, end, content) in sections.items():
            title = content.split('\n\n', 1)[0].replace('\n', ' ')
            if re.search(settings['timing_title_pattern'], title, re.I):
                date_catalog.append({'variable': variable, 'title': title,
                                     'in_data_header': variable in header,
                                     **reference(cb, start, end, wave['codebook'])})
        qt_timing = []
        for page_number, page in enumerate(qt.split('\f'), 1):
            for line in page.splitlines():
                if re.search(settings['questionnaire_timing_pattern'], line, re.I):
                    qt_timing.append({'file': wave['questionnaire'], 'pdf_page': page_number, 'line': line.strip()})
        report['waves'].append({'wave': number, 'data_file': wave['data'],
            'codebook_sha256': sha256(root / wave['codebook']),
            'questionnaire_sha256': sha256(root / wave['questionnaire']),
            'header_columns': len(header), 'header_variables_without_codebook_section': sorted(set(header) - set(sections)),
            'interview_date_header_candidates': [h for h in header if re.search(settings['interview_header_pattern'], h, re.I)],
            'codebook_sections': evidence, 'questionnaire_sections': qsections,
            'timing_variable_catalog': date_catalog, 'questionnaire_timing_mentions': qt_timing})
    report['supplementary_documentation'] = []
    for item in settings.get('supplementary_documentation', []):
        source = root / item['file']
        text = load_pdf_text(source, cache / (source.stem + '.txt'))
        pages = text.split('\f')
        report['supplementary_documentation'].append({
            **item, 'sha256': sha256(source),
            'page_text': {str(page): pages[page - 1] for page in item['pdf_pages']}})
    return report


if __name__ == '__main__':
    output = ROOT / 'reports/prediction_source_evidence.json'
    result = inspect()
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(f"Wrote {output}: {len(result['waves'])} waves")
