"""Build and fit the separately versioned v2.3 study; never overwrites older runs."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from path_project.study_training import build_study

if __name__ == '__main__':
    build_study(ROOT)
