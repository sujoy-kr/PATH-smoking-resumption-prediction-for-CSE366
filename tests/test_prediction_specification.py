"""Contract checks protect the research endpoint and documentation parser."""
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from path_project.specification import validate_specification


def test_documented_specification_matches_sources():
    assert validate_specification(ROOT) == []


def test_pdf_page_boundary_does_not_hide_variable():
    module_spec = importlib.util.spec_from_file_location('inspect_sources', ROOT / 'scripts/inspect_prediction_sources.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    text = 'Cover\fR04R_A_DAYSQUIT_CIGS: Example\nAlgorithm here\n\fR04_AC1009_UN: Units'
    sections = module.codebook_sections(text)
    start, end, content = sections['R04R_A_DAYSQUIT_CIGS']
    assert module.reference(text, start, end, 'example.pdf')['pdf_page_start'] == 2
    assert 'Algorithm here' in content
    assert 'R04_AC1009_UN:' not in content


def test_secondary_definitions_do_not_change_primary_or_invent_year_risk():
    spec = json.loads((ROOT / 'configs/prediction_specification.json').read_text())
    recent = spec['secondary_analyses']['recent_quitters']
    assert recent['allowed_units_by_wave']['2'] == ['1', '2']
    assert recent['unit_days']['2'] * 12 == recent['unit_days']['3']
    assert spec['secondary_analyses']['current_established_followup']['requires_core_primary_valid_outcome']
    mapping = json.loads((ROOT / 'configs/feature_mapping.json').read_text())
    candidates = [field['name'] for field in mapping['fields'] if field['role'] == 'candidate_predictor']
    assert spec['allowed_inputs']['feature_allowlist'] == candidates
    assert not set(candidates).intersection(spec['forbidden_predictors'])
    assert not any(value for key, value in spec['app_claim'].items() if key.startswith('allow_'))
