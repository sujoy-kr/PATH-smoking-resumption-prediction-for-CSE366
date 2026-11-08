"""Fixed-budget stage 8 comparison or verified reuse; no final-test access."""
from pathlib import Path
import json,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
settings=json.loads((ROOT/'configs/tree_models.json').read_text())
for variable in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[variable]=str(settings['cpu_threads'])
from path_project.trees import train_tree_models,BoundaryError
if __name__=='__main__':
    try:mode,result=train_tree_models(ROOT)
    except BoundaryError as error:
        print(f'Tree comparison stopped: {error}',file=sys.stderr);raise SystemExit(1)
    print(mode);print('Selected:',result['selected_model']);print('Final test remains unopened.')
