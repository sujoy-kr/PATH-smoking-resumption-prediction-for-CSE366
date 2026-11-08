"""Check the scientific contract against header-only inspection and saved source evidence."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from path_project.specification import validate_specification

if __name__ == '__main__':
    errors = validate_specification(ROOT)
    for error in errors:
        print(error)
    print(f'Prediction specification: {len(errors)} errors')
    raise SystemExit(bool(errors))
