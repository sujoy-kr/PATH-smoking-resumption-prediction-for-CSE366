"""Source/model/fictional-prediction check; requires no PATH or processed data."""
from importlib import metadata
from pathlib import Path
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    root = Path(root)
    # These packages affect loading, numeric predictions or the current UI.
    expected = json.loads((root/'configs/runtime_handoff.json').read_text())
    errors, notes = [], []
    # Packages that change unpickling or numbers are strict; UI-only ones warn.
    strict = set(expected['strict_packages'])
    for package, pinned in expected['core_versions'].items():
        try:
            actual = metadata.version(package)
        except metadata.PackageNotFoundError:
            (errors if package in strict or package == 'streamlit' else notes).append(f'{package}: not installed (expected {pinned})')
            continue
        if actual != pinned:
            (errors if package in strict else notes).append(f'{package}: installed {actual}, expected {pinned}')
    for note in notes:
        print(f'Warning (UI-only package differs): {note}', file=sys.stderr)
    if errors:
        raise ValueError('Dependency mismatch:\n'+'\n'.join(errors)+
            '\nInstall the app dependencies with: python -m pip install -r requirements-app.txt')
    sys.path.insert(0, str(root/'src'))
    from path_project.study import load_study
    from path_project.assessment import assess_available
    bundle = load_study(root)
    features = bundle['model'].features
    background = bundle['background']
    if list(background.columns) != features or background.shape != (bundle['config']['background_size'], len(features)):
        raise ValueError('Unexpected explanation reference schema; no values emitted.')
    fixture = json.loads((root/'tests/fixtures/handoff_profiles.json').read_text())
    checks = []
    for case in fixture['profiles']:
        result = assess_available(root, bundle, case['answers'], case['profile_answers'])
        saved = case['expected']
        if saved.get('status') == 'suppressed':
            if result.get('status') != 'suppressed' or 'probability' in result:
                raise ValueError(f'Fictional profile {case["name"]}: expected suppression.')
            checks.append(case['name'])
            continue
        for key in ['estimate_mode', 'risk_level', 'provided']:
            if result[key] != saved[key]:
                raise ValueError(f'Fictional profile {case["name"]}: {key} differs.')
        if not math.isclose(result['probability'], saved['probability'], rel_tol=0, abs_tol=1e-10):
            raise ValueError(f'Fictional profile {case["name"]}: probability differs.')
        for got, want in zip(result['curve'], saved['curve'], strict=True):
            if got['months'] != want['months'] or not math.isclose(got['probability'], want['probability'], rel_tol=0, abs_tol=1e-10):
                raise ValueError(f'Fictional profile {case["name"]}: horizon result differs.')
        if not math.isclose(result['conditional_median_months'], saved['conditional_median_months'], rel_tol=0, abs_tol=1e-8):
            raise ValueError(f'Fictional profile {case["name"]}: timing differs.')
        if len(result['factors']) != len(saved['factors']):
            raise ValueError('Explanation feature count differs.')
        for got, want in zip(result['factors'], saved['factors'], strict=True):
            if got['feature'] != want['feature'] or not math.isclose(got['contribution'], want['contribution'], rel_tol=0, abs_tol=1e-10):
                raise ValueError('Fictional explanation differs.')
        checks.append(case['name'])
    return {'status': 'passed', 'model_version': bundle['config']['version'],
        'fictional_profiles_verified': checks,
        'raw_or_processed_data_required': False,
        'model_refitted': False, 'saved_test_predictions_recomputed': False,
        'environment': {'python': sys.version.split()[0], 'core_versions': expected['core_versions']}}


if __name__ == '__main__':
    try:
        print(json.dumps(verify(), indent=2))
    except (OSError, ValueError, ImportError) as error:
        print(f'Runtime check failed: {error}', file=sys.stderr)
        raise SystemExit(1)
