"""Generate stage 6 tuning-only aggregate tables/figures. No fitting."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.development import run_exploration
if __name__=='__main__':
    tables,settings,mapping=run_exploration(ROOT)
    print(json.dumps(tables['summary'],indent=2))
