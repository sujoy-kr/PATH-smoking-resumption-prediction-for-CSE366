"""Stage 7 baseline training or immutable-run verification/reuse only."""
from pathlib import Path
import sys,json,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
settings=json.loads((ROOT/'configs/baseline_models.json').read_text())
for variable in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[variable]=str(settings['cpu_threads'])
from path_project.baselines import train_baselines,BoundaryError
if __name__=='__main__':
    try:mode,result=train_baselines(ROOT)
    except BoundaryError as error:
        print(f'Baseline training stopped: {error}',file=sys.stderr);raise SystemExit(1)
    print(mode)
    print('Selected baseline:',result['selected_model'])
    print('Final-test data remain closed.')
