"""Create or verify/reuse the stage 5 lock; no training or test labels."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.evaluation import create_splits,BoundaryError
if __name__=='__main__':
    try:
        mode,report=create_splits(ROOT)
    except BoundaryError as error:
        print(f'Split creation stopped: {error}',file=sys.stderr);raise SystemExit(1)
    print(mode)
    print(json.dumps(report,indent=2))
