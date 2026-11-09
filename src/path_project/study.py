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

CONFIG = 'configs/longitudinal_v2_4.json'


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
    if stored.get('format') != 'reclaim-survival-json-v4':
        raise BoundaryError('Unsupported model format.')
    results = json.loads((report/'results.json').read_text())
    summary = json.loads((report/'summary.json').read_text())['populations']
    populations = {}
    for name, item in stored['populations'].items():
        populations[name] = {
            'model': PiecewiseHazardModel.from_dict(item['model']),
            'baseline': PiecewiseHazardModel.from_dict(item['baseline']),
            'background': pd.DataFrame(item['background']['rows'], columns=item['background']['columns']).astype(float),
            'spec': config['populations'][name], 'results': results[name], 'summary': summary[name]}
    return {'populations': populations, 'config': config}


def exact_feature_shap(model, background, row, horizon, groups=None, chunk=256):
    """Exact Shapley values of the horizon probability over input groups.

    ``groups`` maps a group name to its features (default: one group per feature).
    Inputs outside a coalition take values from independent draws of the training
    marginals (interventional Shapley; dependence between inputs is ignored).
    """
    features = model.features
    groups = groups or {f: {'features': [f]} for f in features}
    names = list(groups)
    n = len(names)
    if n > 14:
        raise BoundaryError('Too many input groups for exact explanations.')
    columns = {name: [features.index(f) for f in groups[name]['features']] for name in names}
    base = background[features].to_numpy(float)
    target = row[features].to_numpy(float)[0]
    masks = np.arange(1 << n)
    values = np.empty(1 << n)
    for start in range(0, len(masks), chunk):
        block = masks[start:start+chunk]
        data = np.broadcast_to(base, (len(block),)+base.shape).copy()
        for j, name in enumerate(names):
            on = ((block >> j) & 1).astype(bool)
            for c in columns[name]:
                data[on, :, c] = target[c]
        frame = pd.DataFrame(data.reshape(-1, len(features)), columns=features)
        values[start:start+len(block)] = model.risk(frame, [horizon])[:, 0].reshape(len(block), len(base)).mean(axis=1)
    contributions = []
    for j, name in enumerate(names):
        total = 0.
        for mask in masks:
            if not (mask >> j) & 1:
                total += (values[mask | (1 << j)]-values[mask])/(n*math.comb(n-1, int(mask).bit_count()))
        contributions.append({'feature': name, 'contribution': float(total)})
    predicted = float(model.risk(row, [horizon])[0, 0])
    if not np.isclose(values[0]+sum(c['contribution'] for c in contributions), predicted, atol=1e-8):
        raise BoundaryError('Probability explanation does not reconcile.')
    return float(values[0]), sorted(contributions, key=lambda c: -abs(c['contribution']))
