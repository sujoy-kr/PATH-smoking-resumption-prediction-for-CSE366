"""Stage 10 freeze development score categories/explanations, never fit models."""
from pathlib import Path
import os,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
settings=json.loads((ROOT/'configs/output_explanations.json').read_text())
os.environ['MPLCONFIGDIR']=str(ROOT/'.cache/matplotlib')
for variable in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[variable]=str(settings['cpu_threads'])
from path_project.outputs import build_outputs,BoundaryError
if __name__=='__main__':
    try:mode,summary=build_outputs(ROOT)
    except BoundaryError as error:
        print(f'Output build stopped: {error}',file=sys.stderr);raise SystemExit(1)
    print(mode);print(json.dumps(summary,indent=2))
