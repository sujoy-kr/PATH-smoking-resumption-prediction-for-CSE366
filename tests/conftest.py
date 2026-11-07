"""Separate current app tests from the restored historical research suite."""
from pathlib import Path

RESEARCH_TESTS = {
    'test_baselines.py', 'test_cohort.py', 'test_demo.py',
    'test_development.py', 'test_evaluation.py', 'test_feature_mapping.py',
    'test_final_evaluation.py', 'test_inventory.py', 'test_outputs.py',
    'test_prediction_specification.py', 'test_project_smoke.py',
    'test_timing.py', 'test_trees.py',
}


def pytest_addoption(parser):
    parser.addoption('--research-tests', action='store_true', default=False,
        help='Include historical next-survey research tests; some require separately restored private v1 artifacts, raw data and research dependencies.')


def pytest_ignore_collect(collection_path, config):
    return (Path(collection_path).name in RESEARCH_TESTS
            and not config.getoption('--research-tests'))
