"""Adjacent-wave cohort preparation. No learned preprocessing, splits or models.

Participant records remain local; logs/reports contain aggregates only.
"""
from collections import Counter
import csv
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import sys
import tempfile

import pandas as pd

from path_project.documentation import fingerprint
from path_project.features import canonical_code, decode_component, transform_entry


class CohortError(ValueError):
    """An input/contract/integrity error whose message never includes respondent IDs."""


def json_write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def load_contract(root):
    root = Path(root)
    config = json.loads((root / 'configs/cohort.json').read_text())
    project = json.loads((root / config['project_config']).read_text())
    task = json.loads((root / config['prediction_config']).read_text())
    mapping = json.loads((root / config['feature_mapping']).read_text())
    return config, project, task, mapping


def validate_ids(frame, wave, identifier, invalid_identifiers):
    if identifier not in frame:
        raise CohortError(f'Wave {wave}: identifier column absent.')
    values = frame[identifier]
    bad_type = values.map(lambda value: not isinstance(value, str))
    if bad_type.any():
        raise CohortError(f'Wave {wave}: {int(bad_type.sum())} non-string/missing identifiers; IDs were not coerced.')
    invalid = values.isin(invalid_identifiers) | values.ne(values.str.strip())
    if invalid.any():
        raise CohortError(f'Wave {wave}: {int(invalid.sum())} empty/sentinel/whitespace identifiers; no values emitted.')
    duplicated = values.duplicated(keep=False)
    if duplicated.any():
        raise CohortError(f'Wave {wave}: {int(duplicated.sum())} rows have duplicate PERSONID; one-to-one join required. No IDs emitted.')


def field_index(mapping):
    return {field['name']: field for field in mapping['fields']}


def needed_columns(wave, task, mapping, config):
    columns = {config['identifier']}
    starts = {left for left, right in task['pairs']}
    follows = {right for left, right in task['pairs']}
    fields = field_index(mapping)
    if wave in starts:
        for name in [config['baseline_former_field'], config['baseline_p30_field'], config['baseline_current_field']]:
            columns.update(fields[name]['waves'][str(wave)]['source_columns'])
        for field in mapping['fields']:
            if field['role'] != 'candidate_predictor':
                continue
            entry = field['waves'][str(wave)]
            if entry['source_wave'] != wave or entry['source_time'] != 'starting_interview' or not entry['available_at_prediction_time']:
                raise CohortError(f"{field['name']}: future information cannot enter a baseline feature vector.")
            if entry['prior_wave_dependency']['explicit_join_required']:
                raise CohortError('Explicit historical reconstruction is not implemented/authorized by this cohort contract.')
            columns.update(entry['source_columns'])
    if wave in follows:
        for name in [config['outcome_field'], config['secondary_outcome_field']]:
            columns.update(fields[name]['waves'][str(wave)]['source_columns'])
    return sorted(columns)


def read_wave(path, wave, columns, config):
    """Read selected columns once as strings, preserving lexical IDs and sentinels."""
    with Path(path).open(newline='', encoding=config['read_encoding']) as stream:
        header = next(csv.reader(stream, delimiter='\t'))
    missing = set(columns) - set(header)
    if missing:
        raise CohortError(f'Wave {wave}: {len(missing)} configured columns absent; check the feature header validator.')
    frame = pd.read_csv(path, sep='\t', usecols=columns, dtype='string',
                        keep_default_na=False, na_filter=False, encoding=config['read_encoding'])
    frame = frame[columns]
    validate_ids(frame, wave, config['identifier'], config['invalid_identifiers'])
    return frame


def status_series(frame, entry):
    column = entry['source_columns'][0]
    transformed = [transform_entry(entry, {column: value}) for value in frame[column]]
    return (pd.Series(pd.array([v for v,r in transformed], dtype='Int8'), index=frame.index),
            pd.Series(pd.array([r for v,r in transformed], dtype='string'), index=frame.index))


def harmonize_features(frame, wave, mapping, config):
    """Fixed dictionary operations only; all inputs come from this baseline frame."""
    result = pd.DataFrame(index=frame.index)
    component_counts = {}
    for field in mapping['fields']:
        if field['role'] != 'candidate_predictor':
            continue
        name = field['name']
        entry = field['waves'][str(wave)]
        if entry['source_wave'] != wave or entry['source_time'] != 'starting_interview' or not entry['available_at_prediction_time']:
            raise CohortError(f'{name}: future-information exclusion failed.')
        if config['identifier'] in entry['source_columns']:
            raise CohortError('PERSONID cannot be a feature input.')
        values, reasons, details = [], [], []
        counts = Counter()
        for raw in frame[entry['source_columns']].to_dict(orient='records'):
            value, reason = transform_entry(entry, raw)
            missing = {}
            for component in entry['components']:
                _, component_reason = decode_component(component, raw[component['column']])
                if component_reason != 'observed':
                    missing[component['column']] = component_reason
                    counts[component_reason] += 1
            values.append(value)
            reasons.append(reason)
            details.append(json.dumps(missing, sort_keys=True) if missing else None)
        result[name] = pd.array(values, dtype='Float64')
        result[name + config['feature_reason_suffix']] = pd.array(reasons, dtype='string')
        result[name + config['component_reason_suffix']] = pd.array(details, dtype='string')
        component_counts[name] = dict(sorted(counts.items()))
    return result, component_counts


def availability_rows(features, pair, population, config):
    rows = []
    for column in features:
        if not column.endswith(config['feature_reason_suffix']) or column.endswith(config['component_reason_suffix']):
            continue
        name = column[:-len(config['feature_reason_suffix'])]
        reason_counts = features[column].value_counts(dropna=False).to_dict()
        observed = int(features[name].notna().sum())
        rows.append({'pair': pair, 'population': population, 'feature': name,
                     'rows': len(features), 'observed': observed, 'missing': len(features)-observed,
                     'availability_fraction': observed / len(features) if len(features) else None,
                     'valid_zero_values': int(features[name].eq(0).fillna(False).sum()),
                     'reason_counts': {str(k):int(v) for k,v in sorted(reason_counts.items())}})
    return rows


def interval_cohort(baseline, followup, start, end, task, mapping, config):
    if end != start + 1 or [start,end] not in task['pairs']:
        raise CohortError('Only configured adjacent scheduled wave pairs are permitted; do not bridge a missing wave.')
    identifier = config['identifier']
    validate_ids(baseline, start, identifier, config['invalid_identifiers'])
    validate_ids(followup, end, identifier, config['invalid_identifiers'])
    fields = field_index(mapping)
    former, former_reason = status_series(baseline, fields[config['baseline_former_field']]['waves'][str(start)])
    p30, p30_reason = status_series(baseline, fields[config['baseline_p30_field']]['waves'][str(start)])
    current, current_reason = status_series(baseline, fields[config['baseline_current_field']]['waves'][str(start)])
    former_yes = former.eq(config['inclusion']['former_value']).fillna(False)
    eligible_mask = former_yes & p30.eq(config['inclusion']['past30_value']).fillna(False)
    eligible = baseline.loc[eligible_mask].copy().reset_index(drop=True)
    features, component_counts = harmonize_features(eligible, start, mapping, config)
    meta = eligible[[identifier]].copy()
    meta['starting_wave'] = pd.array([start]*len(meta),dtype='Int8')
    meta['followup_wave'] = pd.array([end]*len(meta),dtype='Int8')
    meta['baseline_current_established_qc'] = pd.array(current.loc[eligible_mask],dtype='Int8')
    # The follow-up projection is limited to the identifier and the two labels.
    primary_entry = fields[config['outcome_field']]['waves'][str(end)]
    secondary_entry = fields[config['secondary_outcome_field']]['waves'][str(end)]
    primary, primary_reason = status_series(followup, primary_entry)
    secondary, secondary_reason = status_series(followup, secondary_entry)
    labels = pd.DataFrame({identifier:followup[identifier],
                           config['outcome_name']:primary, 'outcome_reason':primary_reason,
                           config['secondary_outcome_name']:secondary, 'secondary_outcome_reason':secondary_reason})
    try:
        ledger = meta.merge(labels,on=identifier,how='left',sort=False,validate='one_to_one',indicator=True)
    except pd.errors.MergeError:
        raise CohortError('Unexpected duplicate join; one-to-one PERSONID merge required. No IDs emitted.') from None
    present = ledger['_merge'].eq('both')
    valid = present & ledger[config['outcome_name']].notna()
    ledger['observation_status'] = pd.array(['observed_valid' if v else 'invalid_followup_outcome' if p else 'missing_followup_interview' for p,v in zip(present,valid)],dtype='string')
    for column in ['outcome_reason','secondary_outcome_reason']:
        ledger.loc[~present,column] = 'missing_followup_interview'
    ledger = ledger.drop(columns='_merge')
    # Recency subgroups are metadata, not a new core inclusion criterion or risk clock.
    recent = task['secondary_analyses']['recent_quitters']
    recency_name = config['recency_feature']
    recency = features[recency_name]
    ledger['recency_group'] = pd.array(['unknown_recency' if pd.isna(v) else 'recent' if config['recent_lower_exclusive_days'] < v <= config['recent_upper_inclusive_days'] else 'other_observed_recency' for v in recency],dtype='string')
    raw_duration = fields[recency_name]['waves'][str(start)]['transform']
    exclusions = recent['unit_rounding_sensitivity']['exclude_raw_boundary_reports']
    boundary = [any(canonical_code(row[raw_duration['unit_column']])==b['unit'] and canonical_code(row[raw_duration['number_column']])==str(b['number']) for b in exclusions) for row in eligible[[raw_duration['number_column'],raw_duration['unit_column']]].to_dict('records')]
    ledger['recency_boundary_report'] = pd.array(boundary,dtype='boolean')
    ledger['recency_group_rounding_sensitivity'] = ledger['recency_group'].mask(ledger['recency_boundary_report'],'excluded_rounded_boundary')
    joined = pd.concat([ledger,features],axis=1)
    cohort = joined.loc[valid].copy().reset_index(drop=True)
    ledger = ledger.reset_index(drop=True)
    # Keep all feature missingness; complete-case feature filtering is forbidden here.
    exclusion_counts = Counter()
    for index in baseline.index:
        if pd.isna(former.loc[index]):
            exclusion_counts['former_unknown:' + former_reason.loc[index]] += 1
        elif not former_yes.loc[index]:
            exclusion_counts['not_former_established'] += 1
        elif pd.isna(p30.loc[index]):
            exclusion_counts['baseline_p30_unknown:' + p30_reason.loc[index]] += 1
        elif p30.loc[index] != config['inclusion']['past30_value']:
            exclusion_counts['baseline_p30_smoking'] += 1
    primary_positive = int(cohort[config['outcome_name']].eq(1).sum())
    secondary_valid = cohort[config['secondary_outcome_name']].notna()
    recent_mask = cohort['recency_group'].eq('recent')
    flow = {'pair':f'{start}-{end}', 'starting_wave':start, 'followup_wave':end,
            'baseline_records':len(baseline), 'former_established':int(former_yes.sum()),
            'former_no':int(former.eq(2).fillna(False).sum()), 'former_unknown':int(former.isna().sum()),
            'baseline_p30_positive_among_former':int((former_yes & p30.eq(1).fillna(False)).sum()),
            'baseline_p30_unknown_among_former':int((former_yes & p30.isna()).sum()),
            'eligible_baseline':len(eligible), 'missing_followup_interview':int((~present).sum()),
            'invalid_followup_outcome':int((present & ~valid).sum()), 'unobserved_outcomes':int((~valid).sum()),
            'labeled_records':len(cohort), 'positive_outcomes':primary_positive,
            'negative_outcomes':len(cohort)-primary_positive,
            'positive_prevalence':primary_positive/len(cohort) if len(cohort) else None,
            'unique_labeled_people':int(cohort[identifier].nunique()),
            'secondary_valid_records':int(secondary_valid.sum()),
            'secondary_unknown_records':int((~secondary_valid).sum()),
            'secondary_positive_outcomes':int(cohort[config['secondary_outcome_name']].eq(1).fillna(False).sum()),
            'secondary_positive_prevalence':int(cohort[config['secondary_outcome_name']].eq(1).fillna(False).sum())/int(secondary_valid.sum()) if secondary_valid.sum() else None,
            'recent_recency_observed_records':int(recent_mask.sum()),
            'recent_recency_positive_outcomes':int(cohort.loc[recent_mask,config['outcome_name']].eq(1).sum()),
            'unknown_recency_labeled_records':int(cohort['recency_group'].eq('unknown_recency').sum()),
            'rounded_boundary_labeled_records':int(cohort['recency_boundary_report'].sum()),
            'eligible_baseline_current_yes_qc':int(current.loc[eligible_mask].eq(1).fillna(False).sum()),
            'eligible_baseline_recency_le30_qc':int(recency.le(config['recent_lower_exclusive_days']).fillna(False).sum()),
            'baseline_exclusion_reasons':dict(sorted(exclusion_counts.items())),
            'invalid_outcome_reasons':{str(k):int(v) for k,v in ledger.loc[present & ~valid,'outcome_reason'].value_counts().items()}}
    assert flow['baseline_records'] == sum(exclusion_counts.values()) + len(eligible)
    assert len(eligible) == len(cohort)+flow['unobserved_outcomes']
    assert primary_positive+flow['negative_outcomes'] == len(cohort)
    availability = availability_rows(features,flow['pair'],'eligible_baseline',config)
    availability += availability_rows(features.loc[valid],flow['pair'],'labeled_cohort',config)
    return cohort, ledger, flow, availability, component_counts


def csv_write(path, rows):
    if not rows:
        raise CohortError('Cannot write an empty aggregate table without a schema.')
    with Path(path).open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({key:json.dumps(value,sort_keys=True) if isinstance(value,(dict,list)) else value for key,value in row.items()} for row in rows)


def run_signature(root, config, project):
    manifest=json.loads((root/config['input_manifest']).read_text())
    configuration=['configs/cohort.json',config['project_config'],config['prediction_config'],config['feature_mapping'],config['input_manifest'],config['legacy_diagnostic']]
    inputs={}
    for wave in project['waves']:
        name=wave['data']
        actual=fingerprint(root/name)
        if actual != manifest[name]['sha256']:
            raise CohortError(f'Original input fingerprint differs: {name}; raw inputs were not modified by this pipeline.')
        inputs[name]=actual
    parts={'canonical_inputs_sha256':inputs,
           'configuration_sha256':{name:fingerprint(root/name) for name in configuration},
           'code_sha256':{name:fingerprint(root/name) for name in config['code_inputs']},
           'versions':{name:version(name) for name in config['versions']},
           'python':sys.version}
    digest=hashlib.sha256(json.dumps(parts,sort_keys=True).encode()).hexdigest()
    return digest,parts


def verify_completed_run(root, config, expected_signature=None):
    output=root/config['output_dir']
    path=output/config['files']['manifest']
    if not path.is_file():
        raise CohortError('Existing output is incomplete: run manifest missing. Preserve it and inspect before choosing a new configured output directory.')
    saved=json.loads(path.read_text())
    if expected_signature is not None and saved['signature'] != expected_signature:
        raise CohortError('Existing cohort signature differs. No files overwritten. Preserve this run; use a new configured run/output directory after reviewing the changed contract.')
    for relative,digest in saved['output_sha256'].items():
        file=root/relative
        if not file.is_file() or fingerprint(file) != digest:
            raise CohortError(f'Existing output missing/changed: {relative}. No cohort or split was overwritten.')
    return saved


def schema_for(cohort, ledger, mapping, config):
    predictors=[field for field in mapping['fields'] if field['role']=='candidate_predictor']
    names={field['name'] for field in predictors}
    def columns(frame):
        result=[]
        for name,dtype in frame.dtypes.items():
            if name==config['identifier']:
                role='identifier_join_group_only'
            elif name in names:
                role='candidate_predictor'
            elif name in [config['outcome_name'],config['secondary_outcome_name']]:
                role='outcome_never_predictor'
            elif name.endswith(config['feature_reason_suffix']) or name.endswith(config['component_reason_suffix']):
                role='baseline_missingness_metadata_not_automatically_a_predictor'
            else:
                role='interval_or_quality_control_metadata_never_automatic_predictor'
            result.append({'name':name,'pandas_dtype':str(dtype),'role':role})
        return result
    return {'version':config['schema_version'],'row_key':[config['identifier'],'starting_wave','followup_wave'],
            'identifier_policy':'Stable string, never a predictor; no identifier values in this schema.',
            'prediction_target':'Past-30-day cigarette smoking reported at the next scheduled survey, conditional on valid observed follow-up.',
            'timing_decision':'C; no individual duration or relapse date created.',
            'predictor_columns':[field['name'] for field in predictors],
            'predictor_definitions':{field['name']:{'units':field['output_units'],'output_labels':field['output_labels'],'description':field['description'],'applicable_mapping':'configs/feature_mapping.json; choose starting-wave entry, including product-scope notes'} for field in predictors},
            'cohort_columns':columns(cohort),'ledger_columns':columns(ledger),
            'outcome_values':{'0':'No past-30-day cigarette smoking at follow-up','1':'Past-30-day cigarette smoking at follow-up','null':'Unobserved/invalid; ledger only for primary outcome'},
            'feature_missingness':'Null value plus feature__reason and optional component-reason JSON. Valid observed zero remains zero; no imputation learned.',
            'ledger_policy':'All baseline-eligible adjacent intervals, including labeled intervals. Features only stored in labeled cohort; ledger records observation/secondary/subgroup metadata.',
            'survey_weighting':'Unweighted, no national inference.'}


def legacy_comparison(flows, legacy):
    pairs={item['pair']:item for item in legacy['pairs']}
    metrics={'former_established':'former','eligible_baseline':'abstinent30','labeled_records':'observed',
             'positive_outcomes':'relapse30','secondary_positive_outcomes':'currentRelapse',
             'recent_recency_observed_records':'recentQuitObserved',
             'recent_recency_positive_outcomes':'recentQuitRelapse'}
    rows=[]
    for flow in flows:
        old=pairs.get(flow['pair'])
        if old is None:
            rows.append({'pair':flow['pair'],'metric':'legacy_interval_absent','actual':None,'legacy':None,'difference':None})
            continue
        for current,prior in metrics.items():
            rows.append({'pair':flow['pair'],'metric':current,'actual':flow[current],
                         'legacy':old[prior],'difference':flow[current]-old[prior]})
    return rows


def validate_frames(cohort, ledger, mapping, task, config):
    identifier=config['identifier']
    key=[identifier,'starting_wave','followup_wave']
    if cohort.duplicated(key).any() or ledger.duplicated(key).any():
        raise CohortError('Duplicate participant/interval rows in generated output; no IDs emitted.')
    if not cohort[config['outcome_name']].isin([0,1]).all():
        raise CohortError('Labeled cohort contains an unknown/invalid outcome.')
    for frame in [cohort,ledger]:
        if not frame['followup_wave'].eq(frame['starting_wave']+1).all():
            raise CohortError('Non-adjacent generated interval.')
        if not frame[identifier].map(lambda value:isinstance(value,str)).all():
            raise CohortError('Identifier string dtype lost.')
    observed=ledger['observation_status'].eq('observed_valid')
    if int(observed.sum()) != len(cohort) or ledger.loc[~observed,config['outcome_name']].notna().any():
        raise CohortError('Unobserved ledger outcomes were lost or recoded as negatives.')
    if set(cohort.columns) & {'CASEID','VARPSU','VARSTRAT'}:
        raise CohortError('Administrative/design field accidentally retained in model table.')
    for field in mapping['fields']:
        if field['role']!='candidate_predictor':
            continue
        name=field['name'];reason=name+config['feature_reason_suffix']
        if not (cohort[name].notna()==cohort[reason].eq('observed')).all():
            raise CohortError(f'{name}: feature value/reason consistency failed.')
    return {'unique_interval_keys':True,'adjacent_intervals_only':True,'primary_labels_binary_observed':True,
            'unobserved_labels_preserved_null':True,'identifier_strings_preserved':True,
            'feature_value_reason_consistency':True,'no_learned_preprocessing_or_training':True}


def build_cohort(root):
    root=Path(root)
    config,project,task,mapping=load_contract(root)
    if task['timing_decision']!='C' or task['skip_missing_wave'] or task['require_all_eight_waves']:
        raise CohortError('This pipeline implements the documented adjacent-wave classification contract only.')
    signature,provenance=run_signature(root,config,project)
    output=root/config['output_dir'];aggregate=root/config['aggregate_dir']
    if output.exists() or aggregate.exists():
        saved=verify_completed_run(root,config,signature)
        return {'mode':'reused_verified_immutable_run','summary':saved['summary'],'signature':signature}
    output.parent.mkdir(parents=True,exist_ok=True);aggregate.parent.mkdir(parents=True,exist_ok=True)
    lock=output.parent/(config['run_name']+'.build.lock')
    try:
        lock_handle=lock.open('x')
    except FileExistsError:
        raise CohortError('A cohort build lock already exists. Verify no build is active before inspecting a stale lock; existing outputs are preserved.') from None
    lock_handle.close()
    staged_output=Path(tempfile.mkdtemp(prefix='.'+config['run_name']+'-',dir=output.parent))
    staged_reports=Path(tempfile.mkdtemp(prefix='.'+config['run_name']+'-',dir=aggregate.parent))
    try:
        waves={wave['wave']:wave for wave in project['waves']}
        audit=[]
        def load(wave):
            columns=needed_columns(wave,task,mapping,config)
            data=read_wave(root/waves[wave]['data'],wave,columns,config)
            audit.append({'wave':wave,'canonical_file':waves[wave]['data'],'rows':len(data),'columns_read':len(columns),
                          'selected_columns':columns,'unique_personids':int(data[config['identifier']].nunique()),
                          'duplicate_personid_rows':0,'identifier_dtype':str(data[config['identifier']].dtype)})
            return data
        baseline=load(task['pairs'][0][0]);current_wave=task['pairs'][0][0]
        cohorts=[];ledgers=[];flows=[];availability=[];component_missing=[]
        for start,end in task['pairs']:
            if start!=current_wave:
                raise CohortError('Configured intervals are not a contiguous adjacent chain; do not silently reload/bridge waves.')
            following=load(end)
            frame,ledger,flow,feature_rows,components=interval_cohort(baseline,following,start,end,task,mapping,config)
            cohorts.append(frame);ledgers.append(ledger);flows.append(flow);availability.extend(feature_rows)
            component_missing.append({'pair':flow['pair'],'population':'eligible_baseline','counts_are_input_components_not_people':True,'missing_component_reason_counts':components})
            print(f"Interval {start}->{end}: eligible={flow['eligible_baseline']}, labeled={flow['labeled_records']}, positive={flow['positive_outcomes']}, unobserved={flow['unobserved_outcomes']}",flush=True)
            baseline=following;current_wave=end
        if len(audit)!=len({item['canonical_file'] for item in audit}):
            raise CohortError('A canonical wave file was processed more than once.')
        identifier=config['identifier']
        cohort=pd.concat(cohorts,ignore_index=True).sort_values([identifier,'starting_wave'],kind='stable').reset_index(drop=True)
        ledger=pd.concat(ledgers,ignore_index=True).sort_values([identifier,'starting_wave'],kind='stable').reset_index(drop=True)
        checks=validate_frames(cohort,ledger,mapping,task,config)
        contributions=cohort.groupby(identifier,sort=False).size()
        positives=int(cohort[config['outcome_name']].sum())
        summary={'run_name':config['run_name'],'labeled_records':len(cohort),'positive_outcomes':positives,
                 'negative_outcomes':len(cohort)-positives,'positive_prevalence':positives/len(cohort) if len(cohort) else None,
                 'unique_labeled_people':int(cohort[identifier].nunique()),
                 'people_with_multiple_labeled_intervals':int(contributions.gt(1).sum()),
                 'repeated_records_beyond_first_per_person':len(cohort)-int(cohort[identifier].nunique()),
                 'maximum_labeled_intervals_per_person':int(contributions.max()) if len(contributions) else 0,
                 'participant_record_count_distribution':{str(k):int(v) for k,v in contributions.value_counts().sort_index().items()},
                 'eligible_interval_records':len(ledger),'unique_baseline_eligible_people':int(ledger[identifier].nunique()),
                 'unobserved_interval_outcomes':int(ledger['observation_status'].ne('observed_valid').sum()),
                 'canonical_wave_files_processed':len(audit),'candidate_features':len(mapping['candidate_predictor_names']),
                 'intervals':len(flows),'weighted':False,'timing':'Next scheduled survey; varying unknown individual elapsed intervals. No relapse dates or fixed-year risks.'}
        # Save only internal participant-level tables under the ignored data directory.
        cohort.to_parquet(staged_output/config['files']['cohort'],index=False,engine=config['parquet_engine'],compression=config['compression'])
        ledger.to_parquet(staged_output/config['files']['ledger'],index=False,engine=config['parquet_engine'],compression=config['compression'])
        schema=schema_for(cohort,ledger,mapping,config)
        json_write(staged_output/config['files']['schema'],schema)
        # Round-trip ID/key/label/missing-value checks without displaying records.
        reloaded=pd.read_parquet(staged_output/config['files']['cohort'],engine=config['parquet_engine'])
        reloaded_ledger=pd.read_parquet(staged_output/config['files']['ledger'],engine=config['parquet_engine'])
        try:
            pd.testing.assert_frame_equal(cohort,reloaded,check_dtype=True)
            pd.testing.assert_frame_equal(ledger,reloaded_ledger,check_dtype=True)
        except AssertionError:
            raise CohortError('Parquet round-trip differs; participant values suppressed. Inspect locally before continuing.') from None
        checks['parquet_round_trip_exact']=True
        legacy=json.loads((root/config['legacy_diagnostic']).read_text())
        comparison=legacy_comparison(flows,legacy)
        json_write(staged_reports/'summary.json',summary)
        json_write(staged_reports/'cohort_flow.json',flows);csv_write(staged_reports/'cohort_flow.csv',flows)
        json_write(staged_reports/'feature_availability.json',availability);csv_write(staged_reports/'feature_availability.csv',availability)
        json_write(staged_reports/'component_missingness_counts.json',component_missing)
        json_write(staged_reports/'legacy_comparison.json',comparison);csv_write(staged_reports/'legacy_comparison.csv',comparison)
        json_write(staged_reports/'schema.json',schema)
        json_write(staged_reports/'validation.json',checks)
        json_write(staged_reports/'input_audit.json',audit)
        json_write(staged_reports/'provenance.json',{'signature':signature,**provenance,'identifier_values_emitted':False,'participant_records_emitted':False})
        write_flow_report(staged_reports,flows,summary,comparison)
        paths={}
        for stage,final in [(staged_output,output),(staged_reports,aggregate)]:
            for file in stage.iterdir():
                paths[str((final/file.name).relative_to(root))]=fingerprint(file)
        saved={'signature':signature,'provenance':provenance,'summary':summary,'output_sha256':paths,
               'no_identifier_values_in_reports':True,'no_training_or_evaluation':True,
               'retry_policy':config['retry_policy']}
        json_write(staged_output/config['files']['manifest'],saved)
        staged_output.rename(output);staged_reports.rename(aggregate)
        verify_completed_run(root,config,signature)
        return {'mode':'built_new_immutable_run','summary':summary,'signature':signature}
    finally:
        for folder in [staged_output,staged_reports]:
            if folder.exists():
                shutil.rmtree(folder)  # Only this invocation's temporary staging directories.
        lock.unlink(missing_ok=True)


def write_flow_report(path,flows,summary,comparison):
    lines=['# Cohort preparation results (unweighted)','',
           'Target: past-30-day cigarette smoking at the next scheduled interview among eligible former established smokers. No model trained; these are cohort counts, not model performance or national estimates.','',
           '| Pair | Baseline eligible | Missing interview | Invalid outcome | Labeled | Positive | Prevalence |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for f in flows:
        rate=f"{100*f['positive_prevalence']:.2f}%" if f['positive_prevalence'] is not None else 'undefined'
        lines.append(f"| {f['pair']} | {f['eligible_baseline']:,} | {f['missing_followup_interview']:,} | {f['invalid_followup_outcome']:,} | {f['labeled_records']:,} | {f['positive_outcomes']:,} | {rate} |")
    lines += ['',f"Overall: {summary['labeled_records']:,} labeled person-interval records, {summary['unique_labeled_people']:,} unique people, {summary['positive_outcomes']:,} positive outcomes. Repeated records beyond each person's first: {summary['repeated_records_beyond_first_per_person']:,}. No all-eight-wave intersection was used.",'',
              'All baseline-eligible intervals are retained in the separate local observation ledger. Missing/invalid primary outcomes remain null and do not enter the labeled cohort. Feature missingness causes no cohort exclusions. Per-feature eligible/labeled availability and distinct missing/skip/error reasons are in the aggregate JSON/CSV tables. Identifiers and participant rows are not shown.','',
              '## Legacy diagnostic comparison','',
              'The original `.analysis/cohort_counts.json` is read as a diagnostic only and is never rewritten. Primary and secondary status counts use the official indicators, the same adjacent-pair eligibility and valid primary outcome requirement. The new pipeline validates unique string identifiers and proper one-to-one joins; it does not force any count to match.','']
    changed=[row for row in comparison if row['difference'] not in (0,None)]
    if changed:
        lines += ['| Pair | Metric | Actual | Legacy | Difference |','|---|---|---:|---:|---:|']
        for row in changed:
            lines.append(f"| {row['pair']} | {row['metric']} | {row['actual']} | {row['legacy']} | {row['difference']:+d} |")
    else:
        lines.append('All compared metrics match the legacy diagnostic.')
    lines += ['',
              'Quit-recency differences are expected especially for Wave 2: the legacy JavaScript selects a nonexistent DAYSQUIT column (findIndex=-1), so its recent-quit comparisons use an undefined/NaN value and count zero. This pipeline uses documented raw number/unit reports, never missing-as-zero. Other differences, if present, must be assessed against the saved metric deltas and observed feature validity reasons; source precision/range checks can also reject inconsistent raw values. The rounding sensitivity is separate and does not change the core cohort.','',
              'Individual elapsed interview times and resumption dates remain unavailable. A negative follow-up window does not prove interval-long abstinence; a positive does not prove persistent relapse. Attrition can be informative. No imputers, learned feature selection, resampling, splits, calibration or final-test evaluation were run.']
    (path/'cohort_report.md').write_text('\n'.join(lines)+'\n')
