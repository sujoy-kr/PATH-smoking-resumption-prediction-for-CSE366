"""Read-only aggregate consistency and final-profile/source validation."""
from pathlib import Path
import json,sys,re
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.final_inputs import validate_final_inputs
from path_project.evaluation import load_locked,BoundaryError

if __name__=='__main__':
    final,questions=validate_final_inputs(ROOT)
    config,cc,lock,people,rows=load_locked(ROOT)
    settings=json.loads((ROOT/'configs/development_exploration.json').read_text());output=ROOT/settings['output_dir']
    read=lambda name:json.loads((output/(name+'.json')).read_text())
    summary=read('summary');expected=rows.loc[rows['partition'].eq('tuning')]
    assert summary['labeled_records']==len(expected) and summary['labeled_people']==expected['PERSONID'].nunique()
    assert sum(read('summary')['recency_distribution'].values())==summary['labeled_records']
    assert sum(int(k)*v for k,v in summary['repeat_distribution'].items())==summary['labeled_records']
    intervals=read('interval_prevalence');assert sum(r['positive'] for r in intervals)==summary['positives']
    assert sum(r['records'] for r in intervals)==summary['labeled_records']
    for r in read('missingness'):
        assert sum(r['reasons'].values())==r['records'] and r['observed']==r['reasons'].get('observed',0)
    attrition=read('followup_by_baseline')
    for feature in settings['attrition_features']:
        groups=[r for r in attrition if r['starting_wave']=='pooled' and r['feature']==feature]
        assert sum(r['eligible_intervals'] for r in groups)==summary['eligible_intervals']
        assert sum(r['observed_outcomes'] for r in groups)==summary['labeled_records']
        for row in groups:assert row['eligible_intervals']==row['observed_outcomes']+row['missing_interviews']+row['unknown_present_outcomes']
    audit=read('access_audit')
    assert not audit['test_features_or_outcomes_read'] and not audit['calibration_threshold_used']
    assert {r['starting_wave'] for r in audit['canonical_baselines']}==set(range(1,7))
    ids=set(people['PERSONID'])
    files=[*output.glob('*.json'),ROOT/settings['summary_file'],ROOT/'docs/app_questions.md']
    for p in files:
        tokens=set(re.split(r'''[\s"'`,;|\[\]{}():]+''',p.read_text()))
        if tokens&ids:raise BoundaryError('Participant identifier found in a stage 6 report; values suppressed.')
    for name in ['interval_prevalence','missingness','quit_recency','feature_distributions','repeated_observations','followup_availability']:
        assert (output/(name+'.png')).is_file()
    print(f"Verified tuning-only aggregates: {summary['labeled_records']} labeled / {summary['eligible_intervals']} eligible intervals; six figures; app/minimal/research profiles; source metadata; no report IDs.")
