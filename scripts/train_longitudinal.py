"""Build the separately versioned consecutive-wave study; never overwrite v1."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from path_project.longitudinal import build_study

if __name__ == '__main__':
    build_study(ROOT)
