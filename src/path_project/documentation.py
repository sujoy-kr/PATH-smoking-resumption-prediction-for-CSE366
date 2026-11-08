"""Extract public documentation semantics; never inspect participant records."""
from bisect import bisect_right
import hashlib
from pathlib import Path
import re
import subprocess
import json


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def pdf_text(path, cache_path):
    """Reuse only content whose PDF and text fingerprints match its sidecar."""
    path, cache_path = Path(path), Path(cache_path)
    sidecar = cache_path.with_suffix('.metadata.json')
    source_hash = fingerprint(path)
    if cache_path.exists() and sidecar.exists():
        metadata = json.loads(sidecar.read_text())
        if metadata['pdf_sha256'] == source_hash and metadata['text_sha256'] == fingerprint(cache_path):
            return cache_path.read_text(), source_hash
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['pdftotext', '-layout', str(path), str(cache_path)], check=True)
    sidecar.write_text(json.dumps({'pdf_sha256': source_hash, 'text_sha256': fingerprint(cache_path)}, indent=2) + '\n')
    return cache_path.read_text(), source_hash


def sections(text, questionnaire=False):
    breaks = [m.start() for m in re.finditer('\f', text)]
    pattern = (r'(?m)^[ \t]*Variable\(s\):[^\n]+' if questionnaire else
               r'(?m)(?:^|(?<=\f))[ \t]*(CASEID|PERSONID|VARPSU|VARSTRAT|R\d{2}[A-Z0-9_]+):')
    matches = list(re.finditer(pattern, text))
    result = {}
    for index, match in enumerate(matches):
        start = match.start() if questionnaire else match.start(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].rstrip()
        names = re.findall(r'R\d{2}[A-Z0-9_]+', match.group()) if questionnaire else [match.group(1)]
        record = {'pdf_page_start': bisect_right(breaks, start) + 1,
                  'pdf_page_end': bisect_right(breaks, start + len(content) - 1) + 1,
                  'section_text': content}
        for name in names:
            result[name] = record
    return result


def response_labels(text):
    """Read repeated-code value tables, including wrapped labels across pages."""
    labels = {}
    active = None
    label_column = None
    for line in text.replace('\f', '\n').splitlines():
        match = re.match(r'^\s*(?P<code>-?\d+(?:\.\d+)?)\s+(?P=code)\s*=\s*(?P<label>.*)', line)
        if match:
            # Frequency/percent columns are deliberately not part of a response label.
            label = re.sub(r'\s{2,}[\d,]+\s+[\d.]+\s*%\s*$', '', match['label']).rstrip()
            labels[match['code']] = label
            active = match['code']
            label_column = match.start('label')
            continue
        stripped = line.strip()
        if not active or not stripped:
            continue
        if re.match(r'^(?:Value|Label|Unweighted|Frequency|Missing Data|%)\b', stripped) or re.match(r'^-\s*\d+\s*-$', stripped):
            continue
        if re.search(r'\bTotal\b|This variable has|Percentages for|Location:|Variable Type:|\(Range of\)', stripped):
            active = None
            continue
        indentation = len(line) - len(line.lstrip())
        if indentation >= max(0, label_column - 5) and re.match(r'[A-Za-z(]', stripped):
            labels[active] += ' ' + stripped
        else:
            active = None
    return labels


def missing_codes(text):
    match = re.search(r'\(Range of\) Missing Values:\s*([^\n]+)', text)
    if not match:
        return []
    return [value.strip() for value in match[1].split(',') if value.strip()]


def clean(text):
    lines = []
    for line in text.replace('\f', '\n').splitlines():
        if re.match(r'^\s*-\s*\d+\s*-\s*$', line):
            continue
        if re.match(r'^\s*(Prepared by Westat|PATH [–-] Wave|Public Use File Annotated Instrument|PATH Study Wave)', line):
            continue
        lines.append(line)
    return '\n'.join(lines)


def meaning_blocks(text):
    """Keep full question/routing/program prose before the frequency table."""
    text = clean(text)
    boundary = re.search(r'(?m)^\s*(?:Value\s+Label|Value\s+Missing Data|This variable has|• Mean:|Location:)', text)
    return text[:boundary.start() if boundary else len(text)].strip()


def observed_range(text):
    result = {}
    for key in ['Minimum', 'Maximum']:
        match = re.search(key + r':\s*([\d.,]+)', text)
        if match:
            result[key.lower()] = float(match[1].replace(',', ''))
    return result or None


def explicit_ranges(text):
    return [{'minimum': int(a), 'maximum': int(b),
             'documented_check_strength': strength.lower() if strength else 'not_specified'}
            for strength, a, b in re.findall(
                r'(?i)\b(?:(SOFT|HARD)\s+)?RANGE(?: CHECK)?\s*:\s*(\d+)\s*[-–]\s*(\d+)', clean(text))]
