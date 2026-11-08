"""Local demo adapter. No fitting, test scoring, or answer persistence."""
import copy
import json
from pathlib import Path
from path_project.documentation import fingerprint
from path_project.evaluation import BoundaryError
from path_project.outputs import load_engine


def read_json(root, path):
    return json.loads((Path(root)/path).read_text())


def load_demo_engine(root):
    root=Path(root)
    config=read_json(root,'configs/demo.json')
    status=read_json(root,config['final_status'])
    metadata=read_json(root,config['metadata'])
    if not status['final_evaluation_complete'] or status['model_sha256']!=metadata['classifier']['sha256']:
        raise BoundaryError('Final evidence and selected model do not agree.')
    if fingerprint(root/status['results_file'])!=status['results_sha256']:
        raise BoundaryError('Saved final evidence has changed; restore verified evidence before running.')
    engine=load_engine(root)
    # Older metadata is immutable pre-test evidence. Override only this in-memory
    # display copy; never change the fitted estimator, thresholds, or old files.
    engine.metadata=copy.deepcopy(engine.metadata)
    engine.metadata['probability_validation_status']='Evaluated once on held-out Wave 7→8 participants. New-user and clinical validity remain unestablished; calibration was imperfect.'
    return engine
