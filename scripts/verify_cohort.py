"""Read-only verification of processed cohort integrity, reports and privacy."""
import json
from pathlib import Path
import re
import sys

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.cohort import CohortError, load_contract, validate_frames, verify_completed_run


def verify(root=ROOT):
    config,project,task,mapping=load_contract(root)
    saved=verify_completed_run(root,config)
    output=root/config['output_dir'];report_dir=root/config['aggregate_dir']
    cohort=pd.read_parquet(output/config['files']['cohort'])
    ledger=pd.read_parquet(output/config['files']['ledger'])
    validate_frames(cohort,ledger,mapping,task,config)
    key=[config['identifier'],'starting_wave','followup_wave']
    primary=key+[config['outcome_name'],config['secondary_outcome_name']]
    try:
        pd.testing.assert_frame_equal(cohort[primary].reset_index(drop=True),ledger.loc[ledger['observation_status'].eq('observed_valid'),primary].reset_index(drop=True))
    except AssertionError:
        raise CohortError('Labeled cohort and observed ledger keys/labels differ; values suppressed.') from None
    schema=json.loads((output/config['files']['schema']).read_text())
    if schema['predictor_columns']!=mapping['candidate_predictor_names'] or config['identifier'] in schema['predictor_columns']:
        raise CohortError('Predictor allowlist contains wrong fields or identifiers.')
    flows=json.loads((report_dir/'cohort_flow.json').read_text())
    for flow in flows:
        rows=cohort.loc[cohort['starting_wave'].eq(flow['starting_wave'])]
        eligible=ledger.loc[ledger['starting_wave'].eq(flow['starting_wave'])]
        if len(rows)!=flow['labeled_records'] or len(eligible)!=flow['eligible_baseline'] or int(rows[config['outcome_name']].sum())!=flow['positive_outcomes']:
            raise CohortError('Saved interval flow does not reconcile with local tables.')
    availability=json.loads((report_dir/'feature_availability.json').read_text())
    for row in availability:
        if row['observed']+row['missing']!=row['rows'] or sum(row['reason_counts'].values())!=row['rows']:
            raise CohortError('Availability/missingness totals fail reconciliation.')
    fields={field['name']:field for field in mapping['fields']}
    for name in schema['predictor_columns']:
        details=name+config['component_reason_suffix']
        for wave in sorted(cohort['starting_wave'].unique()):
            permitted=set(fields[name]['waves'][str(int(wave))]['source_columns'])
            for encoded in cohort.loc[cohort['starting_wave'].eq(wave),details].dropna():
                if not set(json.loads(encoded)).issubset(permitted):
                    raise CohortError('A component missingness record refers to non-baseline columns.')
    # Check for leaked full IDs as report tokens without ever displaying them.
    identifiers=set(ledger[config['identifier']])
    reports=list(report_dir.glob('*'))
    supplemental=root/'reports/cohort_v1_recency_diagnostic.json'
    if supplemental.exists():reports.append(supplemental)
    for report in reports:
        if report.is_file():
            tokens=set(re.split(r'''[\s"'`,;|\[\]{}():]+''',report.read_text()))
            if identifiers.intersection(tokens):
                raise CohortError('A report contains a participant identifier; values suppressed.')
    print(f"Cohort verification: {len(cohort)} labeled rows, {len(ledger)} eligible intervals; keys, labels, availability, baseline component provenance and report-ID checks passed.")
    return saved


if __name__=='__main__':
    verify()
