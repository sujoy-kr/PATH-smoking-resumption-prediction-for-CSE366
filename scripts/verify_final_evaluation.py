"""Read-only integrity audit of saved final evaluation: no model/test rescoring."""
from pathlib import Path
import json,sys
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_project.final_evaluation import verify_final_results
from path_project.documentation import fingerprint
from path_project.evaluation import load_locked,BoundaryError

if __name__=='__main__':
    manifest=verify_final_results(ROOT)
    settings=json.loads((ROOT/'configs/final_evaluation.json').read_text());output=ROOT/settings['output_dir'];report=ROOT/settings['report_dir']
    frozen=json.loads((output/'pretest_freeze.json').read_text());metadata=json.loads((output/'frozen/metadata.json').read_text());result=json.loads((report/'results.json').read_text())
    events=[json.loads(line) for line in (output/'exposure_log.jsonl').read_text().splitlines()]
    assert [e['event'] for e in events]==['freeze_complete','test_access_started','test_predictions_saved','evaluation_complete']
    assert [e['sequence'] for e in events]==[1,2,3,4]
    freeze_hash=fingerprint(output/'pretest_freeze.json')
    assert events[0]['pretest_manifest_sha256']==events[1]['pretest_manifest_sha256']==freeze_hash
    assert events[0]['utc_from_host_clock']<=events[1]['utc_from_host_clock']<=events[2]['utc_from_host_clock']<=events[3]['utc_from_host_clock']
    assert events[2]['sha256']==fingerprint(output/'test_predictions.parquet')
    assert events[3]['results_sha256']==fingerprint(report/'results.json')
    assert pq.ParquetFile(output/'test_predictions.parquet').metadata.num_rows==result['records']==frozen['test_keys_expected']
    assert result['unique_people']==result['records'] and result['people_with_repeated_test_records']==0
    assert result['positive_records']+result['negative_records']==result['records']
    confusion=result['metrics']['selected_calibrated']['interval_equal']['confusion']
    assert sum(confusion.values())==result['records']
    assert confusion['tp']+confusion['fn']==result['positive_records']
    assert confusion['tn']+confusion['fp']==result['negative_records']
    assert sum(g['records'] for g in result['risk_categories'])==result['records']
    assert sum(g['positive_records'] for g in result['risk_categories'])==result['positive_records']
    assert result['risk_cuts']==metadata['risk_cuts']
    def intervals(value):
        if isinstance(value,dict):
            if 'valid_replicates' in value:
                assert value['valid_replicates']+value['undefined_replicates']==settings['bootstrap_replicates']
                if not value['valid_replicates']:assert value['lower'] is None and value['upper'] is None
            for child in value.values():intervals(child)
        elif isinstance(value,list):
            for child in value:intervals(child)
    intervals(result)
    for spec in metadata['models']:
        assert fingerprint(ROOT/spec['source'])==spec['source_sha256']==fingerprint(ROOT/spec['snapshot'])
        assert not set(spec['features'])&set(['PERSONID','starting_wave','followup_wave','outcome_p30d','sex_recorded'])
    _,_,split,people,rows=load_locked(ROOT)
    assert split['signature']==metadata['split_signature']
    ids=set(people['PERSONID'])
    import re
    for path in [report/'results.json',ROOT/settings['report_markdown'],ROOT/'configs/final_evaluation_status.json']:
        tokens=set(re.split(r'''[\s"'`,;|\[\]{}():]+''',path.read_text()))
        if tokens&ids:raise BoundaryError('Participant identifier found in public final evaluation; values suppressed.')
    print(f"Verified saved one-shot evaluation: {result['records']} people, {result['positive_records']} positives; freeze precedes sole test access; artifact/checkpoint/report hashes and aggregate/CI counts reconcile. No predictions, metrics, bootstrap or fitting rerun.")
