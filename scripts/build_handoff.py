"""Package source plus the single authorized current model; no raw/derived cohort."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ['app', 'src', 'scripts', 'configs', 'docs', 'reports', 'tests']
ROOT_NAMES = ['.gitignore', '.gitattributes', 'pyproject.toml', 'run_app.py']
MODEL = 'artifacts/longitudinal_v2_2/model.json'


def handoff_files(root):
    root = Path(root)
    files = {root/name for name in ROOT_NAMES}
    files.update(root.glob('*.md'))
    files.update(root.glob('requirements*.txt'))
    files.update(root.glob('*.pptx'))
    files.add(root/'.streamlit/config.toml')
    files.add(root/MODEL)
    for directory in DIRECTORIES:
        for path in (root/directory).rglob('*'):
            if not path.is_file() or any(p in ['__pycache__', '.pytest_cache'] for p in path.parts):
                continue
            if path.suffix in ['.pyc', '.pyo', '.parquet', '.joblib', '.pkl', '.tsv', '.sav', '.dta', '.feather']:
                continue
            if path.suffix == '.csv' and path.relative_to(root).as_posix() not in ['docs/feature_dictionary.csv', 'docs/feature_dictionary_final.csv']:
                continue
            if path.name == 'secrets.toml' or path.name.startswith('.env'):
                continue
            files.add(path)
    for path in files:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Missing/nonregular package file: {path.relative_to(root)}')
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def build(root, output):
    root, output = Path(root), Path(output)
    if output.exists():
        raise ValueError('Archive already exists; use a new output name instead of overwriting.')
    files = handoff_files(root)
    names = [p.relative_to(root).as_posix() for p in files]
    if MODEL not in names or any(n.endswith(('.joblib', '.pkl', '.pickle')) for n in names):
        raise ValueError('The handoff must contain the current JSON model and no pickle files.')
    manifest = {'purpose': 'Authorized teammate/faculty inference handoff',
        'model_included': MODEL, 'raw_and_processed_data_included': False,
        'survey_derived_reference_rows_in_model': 0,
        'files': {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo('reclaim/'+relative, date_time=(2026, 11, 8, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
        archive.writestr('reclaim/HANDOFF_MANIFEST.json', json.dumps(manifest, indent=2)+'\n')
    return {'archive': str(output), 'files': len(files), 'bytes': output.stat().st_size,
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'releases/reclaim-team-handoff.zip')
    args = parser.parse_args()
    try:
        print(json.dumps(build(ROOT, args.output), indent=2))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
