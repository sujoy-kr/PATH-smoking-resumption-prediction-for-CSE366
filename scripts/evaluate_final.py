"""Freeze before answer access, then evaluate once or verify/reuse saved results."""
from pathlib import Path
import argparse,json,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
settings=json.loads((ROOT/'configs/final_evaluation.json').read_text())
os.environ['MPLCONFIGDIR']=str(ROOT/'.cache/matplotlib')
for variable in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[variable]=str(settings['cpu_threads'])
from path_project.final_evaluation import prepare_final,run_final,BoundaryError
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    try:
        if args.prepare_only:
            result=prepare_final(ROOT);print('Pre-test freeze saved and verified. No test answers accessed.');print('Evaluation signature:',result['evaluation_signature'])
        else:
            mode,result=run_final(ROOT);print(mode);print(f"Reserved test: records={result['records']}, people={result['unique_people']}, positives={result['positive_records']}");print('Selected metrics:',json.dumps(result['metrics']['selected_calibrated']['participant_equal']))
    except BoundaryError as error:
        print(f'Final evaluation stopped: {error}',file=sys.stderr);raise SystemExit(1)
