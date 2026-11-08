"""Deterministic dictionary transformations; no fitting, joins or file writes.

Stage 3 tests exercise synthetic examples; stage 4 applies these fixed rules to
local baseline responses. No parameters are learned from any participant.
"""
from decimal import Decimal, InvalidOperation
import math


def canonical_code(value):
    if value is None:
        return ''
    token = str(value).strip()
    try:
        number = Decimal(token)
        if number.is_finite() and number == number.to_integral_value():
            return str(int(number))
    except InvalidOperation:
        pass
    return token


def decode_component(component, value):
    code = canonical_code(value)
    if code in component['missing_codes']:
        return None, component['missing_reason_by_code'][code]
    if code.lower() in ('', '.', 'nan', 'none', '<na>'):
        return None, 'system_missing'
    if component['variable_type'] == 'character':
        return code, 'observed'
    try:
        numeric = float(code)
    except ValueError:
        return None, 'invalid_value'
    if not math.isfinite(numeric):
        return None, 'invalid_value'
    domain = component['valid_domain']
    if domain.get('decimal_places_as_released') == 0 and numeric != math.trunc(numeric):
        return None, 'out_of_documented_precision'
    if domain['kind'] == 'enumerated':
        if code not in component['source_value_labels']:
            return None, 'invalid_code'
    else:
        # An unrecognized negative sentinel is never a valid numeric measurement.
        if numeric < 0:
            return None, 'invalid_value'
        for bound in domain['explicit_documented_bounds']:
            if numeric < bound['minimum'] or numeric > bound['maximum']:
                return None, 'out_of_documented_range'
    return numeric, 'observed'


def transform_entry(entry, source_values):
    """Return (value, reason); preserve missingness before any unit arithmetic."""
    transform = entry['transform']
    if entry['availability'] != 'available':
        return None, 'unavailable_in_local_release'
    if transform['kind'] == 'metadata_only':
        raise ValueError('Identifiers and design/weight metadata are not feature transformations.')
    values = {}
    reasons = {}
    for component in entry['components']:
        column = component['column']
        values[column], reasons[column] = decode_component(component, source_values.get(column))
    # A removed answer or structural skip is not filled from another component.
    for column in entry['source_columns']:
        if reasons[column] != 'observed':
            return None, reasons[column]
    kind = transform['kind']
    if kind == 'categorical_map':
        code = canonical_code(values[entry['source_columns'][0]])
        if code not in transform['mapping']:
            return None, 'unmapped_code'
        output = transform['mapping'][code]
    elif kind == 'numeric':
        output = values[entry['source_columns'][0]]
    elif kind == 'number_unit':
        code = canonical_code(values[transform['unit_column']])
        if code not in transform['unit_multipliers']:
            return None, 'invalid_unit'
        output = values[transform['number_column']] * transform['unit_multipliers'][code]
    elif kind == 'household_checkboxes':
        marked = transform['marked_code']
        products = [canonical_code(values[column]) for column in transform['product_columns']]
        none = canonical_code(values[transform['none_column']])
        any_product = marked in products
        if any_product and none == marked:
            return None, 'conflicting_household_marks'
        if any_product:
            return 1, 'observed'
        if none == marked:
            return 0, 'observed'
        return None, 'no_household_option_selected'
    else:
        raise ValueError(f'Unsupported transformation: {kind}')
    if isinstance(output, (float, int)):
        if not math.isfinite(output):
            return None, 'invalid_value'
        if 'minimum_exclusive' in transform and output <= transform['minimum_exclusive']:
            return None, 'outside_analytic_range'
        if 'minimum' in transform and output < transform['minimum']:
            return None, 'outside_analytic_range'
        if transform.get('maximum') is not None and output > transform['maximum']:
            return None, 'outside_analytic_range'
    return output, 'observed'
