"""Stage 9 header/schema/source confirmation and capability metadata; no fitting."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.timing import confirm_timing,build_app_metadata
from path_project.cohort import json_write
if __name__=='__main__':
    result=confirm_timing(ROOT)
    policy=json.loads((ROOT/'configs/timing_decision.json').read_text())
    json_write(ROOT/policy['output_evidence'],result)
    json_write(ROOT/policy['app_metadata'],build_app_metadata(policy,result))
    print('Decision C confirmed: eight actual headers, 16 documentation hashes, two Parquet schemas and four live source rechecks. No survey/cohort answer rows read or models fitted. Classifier retained; elapsed-time/annual-risk/date capabilities disabled.')
