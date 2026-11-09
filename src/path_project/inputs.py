"""Validate and encode app answers for every v2.4 input; never invents a value."""
import json
import math
from pathlib import Path

from path_project.evaluation import BoundaryError

MISSING = {'unanswered': 'app_unanswered', 'dont_know': 'app_dont_know', 'prefer_not_to_answer': 'app_refused',
           'not_applicable': 'app_not_applicable'}


def load_inputs(root):
    return json.loads((Path(root)/'configs/inputs_v2_4.json').read_text())


def encode_answers(root, answers, features):
    """Return (values, reasons) for ``features``; raise on anything invalid."""
    spec = load_inputs(root)
    if set(answers)-set(spec):
        raise BoundaryError('Only trained questionnaire inputs are accepted.')
    values, reasons = {}, {}
    for name in features:
        item, raw = spec[name], answers.get(name, 'unanswered')
        if raw is None:
            raw = 'unanswered'
        if isinstance(raw, str) and raw in MISSING:
            values[name], reasons[name] = None, MISSING[raw]
            continue
        if item['kind'] == 'category':
            if str(raw) not in item['options']:
                raise BoundaryError(f'{name}: not a configured response option.')
            values[name] = float(raw)
        elif item['kind'] == 'number':
            number = _number(name, raw)
            if number < item['minimum'] or number > item['maximum']:
                raise BoundaryError(f'{name}: outside the documented range.')
            values[name] = number
        else:
            if not isinstance(raw, dict) or set(raw) != {'number', 'unit'} or str(raw['unit']) not in item['units']:
                raise BoundaryError(f'{name}: requires a number and a documented unit, or an explicit missing answer.')
            number = _number(name, raw['number'])
            if number <= item.get('minimum_exclusive', -1):
                raise BoundaryError(f'{name}: must be a positive number.')
            values[name] = number*item['units'][str(raw['unit'])][1]
            if not math.isfinite(values[name]):
                raise BoundaryError(f'{name}: conversion is not finite.')
        reasons[name] = 'observed'
    return values, reasons


def _number(name, raw):
    try:
        number = float(raw)
    except (ValueError, TypeError):
        raise BoundaryError(f'{name}: must be a whole number.') from None
    if not math.isfinite(number) or number != int(number):
        raise BoundaryError(f'{name}: must be a whole number.')
    return number
