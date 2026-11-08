"""Explain legacy recent-quitter deltas using aggregate, local-only comparisons.

This is a stage 4 preparation diagnostic, not feature selection or model evaluation.
It leaves the immutable cohort run untouched and emits no participant records/IDs.
"""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import re
import sys

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.cohort import CohortError, json_write, load_contract, read_wave, verify_completed_run
from path_project.documentation import fingerprint
from path_project.features import canonical_code


def diagnose(root=ROOT):
    config,project,task,mapping=load_contract(root)
    manifest=verify_completed_run(root,config)
    evidence=json.loads((root/'reports/feature_mapping_evidence.json').read_text())
    comparison=json.loads((root/config['aggregate_dir']/'legacy_comparison.json').read_text())
    changed=sorted({int(row['pair'].split('-')[0]) for row in comparison if row['metric']=='recent_recency_observed_records' and row['difference']})
    ledger_columns=[config['identifier'],'starting_wave',config['outcome_name'],config['recency_feature'],'recency_group']
    cohort=pd.read_parquet(root/config['output_dir']/config['files']['cohort'],columns=ledger_columns)
    waves={wave['wave']:wave for wave in project['waves']}
    rows=[]
    for wave in changed:
        prefix=f'R{wave:02d}'
        derived=prefix+'R_A_DAYSQUIT_CIGS'
        row={'pair':f'{wave}-{wave+1}'}
        new=cohort.loc[cohort['starting_wave'].eq(wave)].copy()
        current_comparison=[item for item in comparison if item['pair']==row['pair'] and item['metric'].startswith('recent_recency_')]
        row['legacy_deltas']=current_comparison
        header_audit=json.loads((root/'reports/feature_mapping_evidence.json').read_text())['header_audit'][str(wave)]
        if not header_audit['derived_daysquit_present']:
            row.update({'reason':'Derived DAYSQUIT absent. Legacy findIndex=-1 yields undefined/NaN, not evidence of no recent quitters.',
                        'new_recent_records':int(new['recency_group'].eq('recent').sum()),
                        'new_recent_positive_outcomes':int(new.loc[new['recency_group'].eq('recent'),config['outcome_name']].eq(1).sum()),
                        'no_person_level_comparison_possible_for_absent_field':True})
            rows.append(row)
            continue
        nn=task['waves'][str(wave)]['last_smoked_number'];unit=task['waves'][str(wave)]['last_smoked_unit']
        raw_path=root/waves[wave]['data']
        expected=manifest['provenance']['canonical_inputs_sha256'][waves[wave]['data']]
        if fingerprint(raw_path)!=expected:
            raise CohortError('Canonical input changed since cohort construction; diagnostic stopped.')
        raw=read_wave(raw_path,wave,[config['identifier'],nn,unit,derived],config)
        # Strict one-to-one joining to the already labeled interval; IDs never emitted.
        joined=new.merge(raw,on=config['identifier'],how='left',validate='one_to_one',indicator=True)
        if not joined['_merge'].eq('both').all():
            raise CohortError('A diagnostic cohort record lacks its original baseline interview; no values emitted.')
        released=pd.to_numeric(joined[derived],errors='coerce')
        lower=config['recent_lower_exclusive_days'];upper=config['recent_upper_inclusive_days']
        old_recent=released.gt(lower)&released.le(upper)
        new_recent=joined['recency_group'].eq('recent')
        extra=new_recent&~old_recent.fillna(False)
        lost=old_recent.fillna(False)&~new_recent
        raw_boundary=(joined[nn].map(canonical_code).eq('12')&joined[unit].map(canonical_code).eq('2')) | (joined[nn].map(canonical_code).eq('1')&joined[unit].map(canonical_code).eq('3'))
        rounding_at_upper=raw_boundary & released.gt(upper).fillna(False) & joined[config['recency_feature']].eq(upper).fillna(False)
        source=evidence['records'][f'{wave}:codebook:{derived}']
        precision=re.search(r'decimal:\s*(\d+)',source['section_text'])
        if precision is None:
            raise CohortError('Derived duration precision is undocumented; cannot claim a rounding explanation.')
        digits=int(precision[1])
        rounded_upper=float(Decimal(str(upper)).quantize(Decimal(1).scaleb(-digits),rounding=ROUND_HALF_UP))
        exact_rounding_matches=extra & released.eq(rounded_upper).fillna(False)
        row.update({'reason':'Raw 12-month/1-year reports convert to 365.25 days (included); the released derived field is rounded above the 365.25 cutoff and is excluded by the legacy rule.',
                    'source_file':waves[wave]['data'],'source_sha256':expected,
                    'source_codebook':source['file'],'source_variable':derived,'physical_pdf_page':source['pdf_page_start'],
                    'declared_derived_decimal_places':int(precision[1]) if precision else None,
                    'analytic_upper_boundary_days':upper,
                    'released_rounded_upper_boundary_days':rounded_upper,
                    'extras_matching_exact_released_rounded_boundary':int(exact_rounding_matches.sum()),
                    'new_recent_records':int(new_recent.sum()),'legacy_recomputed_recent_records':int(old_recent.fillna(False).sum()),
                    'new_recent_extra_records':int(extra.sum()),'new_recent_lost_records':int(lost.sum()),
                    'extra_positive_outcomes':int(joined.loc[extra,config['outcome_name']].eq(1).sum()),
                    'extras_at_documented_raw_upper_boundary':int((extra&rounding_at_upper).sum()),
                    'all_extras_explained_by_upper_boundary_rounding':bool((extra==rounding_at_upper).all())})
        # Verify explanations against the historical file, not just a plausible story.
        count_delta=next(item['difference'] for item in current_comparison if item['metric']=='recent_recency_observed_records')
        positive_delta=next(item['difference'] for item in current_comparison if item['metric']=='recent_recency_positive_outcomes')
        if row['new_recent_extra_records']-row['new_recent_lost_records']!=count_delta or row['extra_positive_outcomes']!=positive_delta or not row['all_extras_explained_by_upper_boundary_rounding'] or int(exact_rounding_matches.sum())!=int(extra.sum()):
            raise CohortError('Recency explanation does not fully account for the observed legacy deltas; inspect locally without printing records.')
        rows.append(row)
    return {'cohort_signature':manifest['signature'],'diagnostic_code_sha256':fingerprint(root/'scripts/diagnose_cohort_recency.py'),
            'rows':rows,'no_participant_records_or_ids_emitted':True,
            'scope':'Descriptive preparation diagnostic only. Main cohort remains unchanged. Approximate history cutoffs are not elapsed event times or fixed-year predicted risks.',
            'rounding_sensitivity':'The prespecified subgroup sensitivity excludes raw 1-month, 12-month and 1-year boundary reports; it is stored separately and never changes core eligibility.'}


if __name__=='__main__':
    result=diagnose()
    json_write(ROOT/'reports/cohort_v1_recency_diagnostic.json',result)
    print(f"Legacy recency diagnostic: {len(result['rows'])} changed intervals explained; no participant records emitted.")
    for row in result['rows']:
        print(row['pair'],row['reason'])
