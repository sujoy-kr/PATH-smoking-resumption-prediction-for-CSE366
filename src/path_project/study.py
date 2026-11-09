"""Runtime for the v2.2 study bundle: verified JSON loading and exact explanations.

No pickle/joblib is read; the model is plain JSON parsed into numpy objects.
The manifest hashes detect accidental corruption only, not malicious edits.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from path_project.evaluation import BoundaryError
from path_project.survival import PiecewiseHazardModel

CONFIG = 'configs/longitudinal_v2_2.json'


def read_config(root):
    return json.loads((Path(root)/CONFIG).read_text())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_study(root):
    root = Path(root)
    config = read_config(root)
    report, artifact = root/config['report_dir'], root/config['artifact_dir']
    manifest = json.loads((report/'manifest.json').read_text())
    for name, digest in manifest['output_sha256'].items():
        if sha256(root/name) != digest:
            raise BoundaryError('Model/report integrity check failed (corrupted or changed file).')
    if manifest['config_sha256'] != sha256(root/CONFIG):
        raise BoundaryError('Study configuration changed after training; retrain under a new version.')
    stored = json.loads((artifact/'model.json').read_text())
    if stored.get('format') != 'reclaim-survival-json-v1':
        raise BoundaryError('Unsupported model format.')
    model = PiecewiseHazardModel.from_dict(stored['model'])
    baseline = PiecewiseHazardModel.from_dict(stored['baseline'])
    background = pd.DataFrame(stored['background']['rows'], columns=stored['background']['columns']).astype(float)
    return {'model': model, 'baseline': baseline, 'background': background, 'config': config,
            'results': json.loads((report/'results.json').read_text()),
            'summary': json.loads((report/'summary.json').read_text())}


def exact_feature_shap(model, background, row, horizon):
    """Exact Shapley values of the horizon probability over the original inputs.

    Features outside a coalition take values from independent draws of the
    training marginals (interventional Shapley; feature dependence ignored).
    """
    features, n = model.features, len(model.features)
    batches = []
    for mask in range(1 << n):
        block = background[features].copy()
        for j, feature in enumerate(features):
            if mask & (1 << j):
                block[feature] = row[feature].iloc[0]
        batches.append(block)
    values = model.risk(pd.concat(batches, ignore_index=True), [horizon])[:, 0].reshape(1 << n, len(background)).mean(axis=1)
    contributions = []
    for j, feature in enumerate(features):
        total = 0.
        for mask in range(1 << n):
            if not mask & (1 << j):
                weight = 1/(n*math.comb(n-1, mask.bit_count()))
                total += weight*(values[mask | (1 << j)]-values[mask])
        contributions.append({'feature': feature, 'contribution': float(total)})
    predicted = float(model.risk(row, [horizon])[0, 0])
    if not np.isclose(values[0]+sum(c['contribution'] for c in contributions), predicted, atol=1e-8):
        raise BoundaryError('Probability explanation does not reconcile.')
    return float(values[0]), sorted(contributions, key=lambda c: -abs(c['contribution']))
