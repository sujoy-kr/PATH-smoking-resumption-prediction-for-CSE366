"""Public development fitting entry point: features and membership from locks.

This module defines boundaries; no real model is fitted in stage 5.
"""
import json
from pathlib import Path
from path_project.evaluation import (BoundaryError, load_locked, load_development,
                                    fit_training_pipeline)
from path_project.documentation import fingerprint


def assert_candidate_features(requested, allowlist):
    if not requested or len(set(requested))!=len(requested) or not set(requested).issubset(allowlist):
        raise BoundaryError('Predictors must be a nonempty unique subset of the locked baseline candidate allowlist.')


def fit_development_pipeline(root, estimator, fold=None, predictors=None):
    """Load authorized tuning records internally and fit an unfitted Pipeline.

    Callers cannot supply test rows, labels or arbitrary administrative/future
    columns. Any candidate subset must be chosen using tuning data only.
    """
    root=Path(root)
    config,cohort_config,manifest,people,rows=load_locked(root)
    mapping_path=cohort_config['feature_mapping']
    cohort_manifest=json.loads((root/cohort_config['output_dir']/cohort_config['files']['manifest']).read_text())
    if fingerprint(root/mapping_path)!=cohort_manifest['provenance']['configuration_sha256'][mapping_path]:
        raise BoundaryError('Candidate mapping differs from the cohort-locked mapping.')
    allowlist=json.loads((root/mapping_path).read_text())['candidate_predictor_names']
    predictors=allowlist if predictors is None else predictors
    assert_candidate_features(predictors,allowlist)
    frame=load_development(root,'fit',fold)
    frame=frame[['PERSONID','starting_wave','followup_wave',*predictors,'outcome_p30d']]
    return fit_training_pipeline(estimator,frame,rows,config,predictors,fold)
