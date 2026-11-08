"""Read-only confirmation of stage 9 evidence/app policy; no timing model or scores."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.timing import confirm_timing,build_app_metadata,next_survey_output_metadata
from path_project.evaluation import BoundaryError

if __name__=='__main__':
    policy=json.loads((ROOT/'configs/timing_decision.json').read_text())
    actual=confirm_timing(ROOT)
    stored=json.loads((ROOT/policy['output_evidence']).read_text())
    if stored!=actual:raise BoundaryError('Saved stage 9 evidence differs from current inputs; inspect before regenerating metadata.')
    metadata=json.loads((ROOT/policy['app_metadata']).read_text())
    if metadata!=build_app_metadata(policy,actual):raise BoundaryError('App capability metadata differs from verified timing decision.')
    next_survey_output_metadata(metadata)
    for horizon in [1,2,3]:
        try:next_survey_output_metadata(metadata,elapsed_horizon=horizon)
        except BoundaryError:pass
        else:raise BoundaryError('Unsupported annual-risk request was not rejected.')
    try:next_survey_output_metadata(metadata,request_relapse_date=True)
    except BoundaryError:pass
    else:raise BoundaryError('Unsupported relapse-date request was not rejected.')
    if not (ROOT/'docs/timing_decision.md').is_file():raise BoundaryError('Timing decision document missing.')
    print('Verified decision C: actual headers/schemas and source pages match saved evidence; classifier hash unchanged; elapsed horizons/date requests rejected. No timing fit, model scoring or final-test answer access.')
