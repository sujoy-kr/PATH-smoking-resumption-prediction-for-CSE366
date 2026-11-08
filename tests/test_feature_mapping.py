"""Synthetic correctness cases only; never access or print participant rows."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from path_project.documentation import response_labels, sections
from path_project.feature_validation import validate_feature_mapping
from path_project.features import transform_entry


@pytest.fixture(scope='module')
def mapping():
    return json.loads((ROOT / 'configs/feature_mapping.json').read_text())


def entry(mapping, name, wave):
    return next(f for f in mapping['fields'] if f['name'] == name)['waves'][str(wave)]


def test_real_headers_and_documented_contract(mapping):
    assert validate_feature_mapping(ROOT, mapping) == []


def test_duration_missing_and_skips_never_become_zero(mapping):
    spec = entry(mapping, 'last_cigarette_recency_days', 2)
    nn, unit = spec['source_columns']
    for raw, reason in [('-1', 'structural_skip'),('-9','not_ascertained'),('-8','dont_know'),('-97777','removed_at_respondent_request'),('.', 'system_missing')]:
        assert transform_entry(spec, {nn:raw,unit:'1'}) == (None,reason)
    assert transform_entry(spec,{nn:'2',unit:'3'}) == (None,'invalid_code')  # No Wave 2 years option.
    assert transform_entry(spec,{nn:'0',unit:'1'}) == (None,'outside_analytic_range')


def test_unit_codes_depend_on_question_not_a_global_unit_assumption(mapping):
    recency = entry(mapping,'last_cigarette_recency_days',2)
    months = entry(mapping,'regular_smoking_months',2)
    intensity = entry(mapping,'prior_regular_cigarettes_per_day',2)
    assert transform_entry(recency,dict(zip(recency['source_columns'],['2','2']))) == (60.875,'observed')
    assert transform_entry(months,dict(zip(months['source_columns'],['2','2']))) == (24,'observed')
    assert transform_entry(intensity,dict(zip(intensity['source_columns'],['2','2']))) == (40,'observed')


def test_age_and_education_coarsening_preserves_later_wave_definitions(mapping):
    age = entry(mapping,'age_band',1)
    education = entry(mapping,'education_level',1)
    assert transform_entry(age,{age['source_columns'][0]:'7'}) == (6,'observed')
    assert transform_entry(education,{education['source_columns'][0]:'6'}) == (5,'observed')
    assert transform_entry(entry(mapping,'age_band',8),{'R08R_A_AGECAT6':'7'}) == (None,'invalid_code')


def test_household_marked_not_marked_and_missing_are_distinct(mapping):
    spec = entry(mapping,'household_tobacco_any',1)
    values = {column:'2' for column in spec['source_columns']}
    assert transform_entry(spec,values) == (None,'no_household_option_selected')
    values[spec['transform']['none_column']] = '1'
    assert transform_entry(spec,values) == (0,'observed')
    values[spec['transform']['product_columns'][0]] = '1'
    assert transform_entry(spec,values) == (None,'conflicting_household_marks')
    values[spec['transform']['none_column']] = '2'
    assert transform_entry(spec,values) == (1,'observed')
    assert transform_entry(spec,{column:'-1' for column in spec['source_columns']}) == (None,'structural_skip')


def test_documented_range_not_observed_maximum(mapping):
    spec = entry(mapping,'alcohol_drinks_per_drinking_day',8)
    component = spec['components'][0]
    assert component['observed_codebook_range_not_validity_bounds']['maximum'] == 30
    assert spec['transform']['maximum'] == 90
    assert transform_entry(spec,{component['column']:'60'}) == (60,'observed')
    assert transform_entry(spec,{component['column']:'91'}) == (None,'out_of_documented_range')
    days = entry(mapping,'alcohol_days_30d',8)
    assert transform_entry(days,{'R08_AX0075':'31'}) == (None,'out_of_documented_range')


def test_validator_rejects_future_and_identifier_predictor(mapping):
    altered = deepcopy(mapping)
    target = altered['fields'][0]['waves']['1']
    target['source_wave'] = 2
    target['source_time'] = 'following_interview'
    target['source_columns'][0] = 'PERSONID'
    errors = validate_feature_mapping(ROOT,altered)
    assert any('source points to a different wave' in e for e in errors)
    assert any('future information' in e for e in errors)
    assert any('identifier, administrative or task-label predictor forbidden' in e for e in errors)


def test_metadata_cannot_be_transformed_into_predictor(mapping):
    with pytest.raises(ValueError,match='not feature transformations'):
        transform_entry(entry(mapping,'person_id',1),{})


def test_wrapped_labels_and_pdf_sections_do_not_swallow_metadata():
    text = ('Cover\fR08R_A_AX0066_V3: Example\n\n'
            '   Value   Label      Unweighted %\n'
            '     3       3 = Other tobacco, including pouches,        100    3.0%\n'
            '             and oral nicotine products\n'
            '     4       4 = No one uses tobacco                     200    6.0%\n'
            '             Total                                      300    9.0%\n'
            '\nR08_AR1045: Next variable')
    parsed = sections(text)['R08R_A_AX0066_V3']
    assert parsed['pdf_page_start'] == 2
    assert response_labels(parsed['section_text']) == {'3':'Other tobacco, including pouches, and oral nicotine products','4':'No one uses tobacco'}


def test_every_candidate_wave_transforms_a_documented_synthetic_response(mapping):
    for field in mapping['fields']:
        if field['role'] != 'candidate_predictor':
            continue
        for wave,spec in field['waves'].items():
            raw = {}
            for component in spec['components']:
                labels = component['source_value_labels']
                bounds = component['valid_domain']['explicit_documented_bounds']
                raw[component['column']] = next(iter(labels)) if labels else str(max(1, max((b['minimum'] for b in bounds),default=1)))
            if spec['transform']['kind'] == 'household_checkboxes':
                raw = {column:'2' for column in spec['source_columns']}
                raw[spec['transform']['product_columns'][0]] = '1'
            value,reason = transform_entry(spec,raw)
            assert reason == 'observed' and value is not None,(field['name'],wave,reason)


def test_validator_rejects_malformed_transform_schema(mapping):
    altered = deepcopy(mapping)
    altered['fields'][0]['waves']['1']['transform']['kind'] = {'kind':'numeric'}
    assert any('unsupported transformation schema' in error for error in validate_feature_mapping(ROOT,altered))


def test_unit_conversion_preserves_fractional_output_but_not_fractional_raw_counts(mapping):
    spec = entry(mapping,'last_cigarette_recency_days',2)
    nn,unit = spec['source_columns']
    assert transform_entry(spec,{nn:'1',unit:'2'}) == (30.4375,'observed')
    assert transform_entry(spec,{nn:'1.5',unit:'2'}) == (None,'out_of_documented_precision')


def test_soft_range_checks_remain_distinguishable_from_analytic_policy(mapping):
    spec = entry(mapping,'alcohol_drinks_per_drinking_day',1)
    bounds = spec['components'][0]['valid_domain']['explicit_documented_bounds']
    assert any(bound['documented_check_strength'] == 'soft' for bound in bounds)
    assert spec['transform']['minimum'] == 1 and spec['transform']['maximum'] == 90


def test_outcomes_recode_source_yes_no_to_correct_binary_labels(mapping):
    for name in ['past30_cigarettes_followup','current_established_followup']:
        field = next(f for f in mapping['fields'] if f['name'] == name)
        assert field['role'] == 'outcome_field'
        assert field['output_labels'] == {'0':'No','1':'Yes'}
        for wave,spec in field['waves'].items():
            column = spec['source_columns'][0]
            assert not spec['available_at_prediction_time']
            assert transform_entry(spec,{column:'1'}) == (1,'observed')
            assert transform_entry(spec,{column:'2'}) == (0,'observed')


def test_wave2_smokeless_prompt_matches_loose_snus_source(mapping):
    evidence = json.loads((ROOT / mapping['output_evidence']).read_text())
    spec = entry(mapping,'smokeless_tobacco_p30d',2)
    source = evidence['records']['2:questionnaire:R02_AS1004']
    assert source['file'] == 'PATH/DS2001/36498-2001-Questionnaire.pdf'
    assert source['pdf_page_start'] == 93
    assert 'loose snus' in source['section_text'].lower()
    assert 'loose snus' in spec['description'].lower()
    assert 'loose snus' in spec['app_prompt'].lower()
    assert 'snus pouches' in spec['app_prompt'].lower()
    assert 'other than snus' not in spec['app_prompt'].lower()
    assert spec['product_scope']['loose_snus_in_question_scope'] is True


def test_semantic_validator_rejects_original_snus_exclusion_regression(mapping):
    altered = deepcopy(mapping)
    spec = entry(altered,'smokeless_tobacco_p30d',2)
    spec['app_prompt'] = 'Have you used smokeless tobacco other than snus at all in the past 30 days?'
    errors = validate_feature_mapping(ROOT,altered)
    assert any('smokeless_tobacco_p30d wave 2: semantic app_prompt' in error for error in errors)


def test_paired_snus_scope_and_csv_prompts_are_wave_specific(mapping):
    import csv
    evidence = json.loads((ROOT / mapping['output_evidence']).read_text())
    with (ROOT / mapping['output_dictionary']).open(newline='',encoding='utf-8') as stream:
        rows = {(row['common_name'],row['wave']):row for row in csv.DictReader(stream)}
    for wave in range(1,9):
        sm = entry(mapping,'smokeless_tobacco_p30d',wave)
        sn = entry(mapping,'snus_p30d',wave)
        assert sm['product_scope']['loose_snus_in_question_scope'] is (wave <= 3)
        assert sn['product_scope']['loose_snus_in_question_scope'] is (wave >= 4)
        for name,spec in [('smokeless_tobacco_p30d',sm),('snus_p30d',sn)]:
            row = rows[name,str(wave)]
            assert row['description'] == spec['description']
            assert row['app_prompt'] == spec['app_prompt']
            assert json.loads(row['product_scope']) == spec['product_scope']
        if wave >= 4:
            source = evidence['records'][f'{wave}:questionnaire:R{wave:02d}_AU1004']
            assert 'both loose and pouches' in ' '.join(source['section_text'].lower().split())
            assert 'loose snus and snus pouches' in sn['app_prompt'].lower()
        else:
            assert 'do not count loose snus' in sn['app_prompt'].lower()
            assert 'brand' in sn['app_notes'].lower()
