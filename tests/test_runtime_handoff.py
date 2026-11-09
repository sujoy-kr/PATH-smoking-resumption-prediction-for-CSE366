"""The distributable app must work without raw data or archived artifacts."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_bundle_matches_fictional_predictions():
    result = load_script('verify_runtime').verify(ROOT)
    assert result['status'] == 'passed'
    assert len(result['fictional_profiles_verified']) == 10
    assert not result['raw_or_processed_data_required']


def test_handoff_archive_has_json_model_and_runs_without_raw_data(tmp_path):
    builder = load_script('build_handoff')
    archive_path = tmp_path/'course-handoff.zip'
    builder.build(ROOT, archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        assert 'reclaim/'+builder.MODEL in names
        assert not any(p.endswith(('.joblib', '.pkl', '.pickle')) for p in names)
        assert not any(p.startswith(('reclaim/PATH/', 'reclaim/data/', 'reclaim/.venv/', 'reclaim/.aws/', 'reclaim/.cache/')) for p in names)
        assert not any(p.endswith('secrets.toml') for p in names)
        assert not any(p.endswith(('.parquet', '.tsv', '.pyc')) for p in names)
        manifest = json.loads(archive.read('reclaim/HANDOFF_MANIFEST.json'))
        import hashlib
        for name, digest in manifest['files'].items():
            assert hashlib.sha256(archive.read('reclaim/'+name)).hexdigest() == digest
        archive.extractall(tmp_path/'unpacked')
    unpacked = tmp_path/'unpacked/reclaim'
    check = subprocess.run([sys.executable, str(unpacked/'scripts/verify_runtime.py')],
        cwd=unpacked, capture_output=True, text=True)
    assert check.returncode == 0, check.stderr
    assert json.loads(check.stdout)['status'] == 'passed'


def test_runtime_requirements_exclude_archived_gpu_packages():
    requirements = (ROOT/'requirements-app.txt').read_text().lower()
    pins = [line.split('==')[0] for line in requirements.splitlines() if line and not line.startswith('#')]
    assert not any(name.startswith('nvidia') for name in pins)
    assert not {'xgboost', 'shap', 'matplotlib'} & set(pins)
    assert {'numpy', 'pandas', 'streamlit', 'altair'} <= set(pins)
    assert not {'scikit-learn', 'scipy', 'joblib'} & set(pins)  # JSON model: no pickle/sklearn at runtime
