"""Check effective Git ignores and public candidate files without exposing private values."""
from pathlib import Path
import hashlib,json,os,re,subprocess,tempfile
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]


def main():
    cache=ROOT/'.cache/stage13';cache.mkdir(parents=True,exist_ok=True)
    repo=Path(tempfile.mkdtemp(prefix='ignore audit ',dir=cache))/'audit.git'
    subprocess.run(['git','init','--bare','--quiet',str(repo)],check=True)
    def ignored(names):
        process=subprocess.run(['git','--git-dir='+str(repo),'--work-tree='+str(ROOT),'check-ignore','--stdin','-z'],input='\0'.join(names)+'\0',text=True,capture_output=True)
        if process.returncode not in [0,1]:raise RuntimeError('Ignore-rule audit failed; no sensitive output emitted.')
        return set(process.stdout.rstrip('\0').split('\0'))-{''}
    private=['PATH/DS1001/36498-1001-Data.tsv','PATH/TSV/36498-1001-Data.tsv','.analysis/cohort_counts.json','data/processed/cohort_v1/cohort.parquet','artifacts/trees_v1/selected_calibrated.joblib','.env','.aws/credentials','.streamlit/secrets.toml','secrets.toml','.prompt-runner/session.log']
    assert ignored(private)==set(private),'Sensitive paths are not all ignored.'
    names=[]
    for base,dirs,files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in ['.git','.venv','.venv-windows-backup','.cache','PATH','.analysis','.aws','.codex','.agents','.prompt-runner','__pycache__','.pytest_cache','data','artifacts']]
        names.extend(str((Path(base)/f).relative_to(ROOT)) for f in files)
    candidates=sorted(set(names)-ignored(names))
    people=pd.read_parquet(ROOT/'artifacts/evaluation_v1/participants.parquet',columns=['PERSONID'])
    identifiers=set(people['PERSONID'])
    patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'\bAKIA[0-9A-Z]{16}\b',rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b']
    issues=[]
    for name in candidates:
        p=ROOT/name
        if p.suffix.lower() in ['.parquet','.tsv','.sav','.dta','.joblib','.pkl','.pickle','.feather']:issues.append({'path':name,'reason':'Participant/artifact-capable file is shareable'})
        data=p.read_bytes()
        if any(re.search(pattern,data) for pattern in patterns):issues.append({'path':name,'reason':'Potential secret pattern; value suppressed'})
        if p.suffix.lower() in ['.md','.json','.py','.csv','.toml','.txt','.yaml','.yml']:
            tokens=set(re.split(r'''[\s"'`,;|\[\]{}():=]+''',data.decode('utf-8',errors='replace')))
            if tokens&identifiers:issues.append({'path':name,'reason':'Real participant identifier token; value suppressed'})
    tracked=subprocess.run(['git','-C',str(ROOT),'ls-files','-z'],capture_output=True)
    result={'git_tracking_status':'No Git repository in workspace; no tracked deliverables exist' if tracked.returncode else 'Existing repository inspected','tracked_query_exit_code':tracked.returncode,'candidate_files_checked':len(candidates),'sensitive_ignore_probes':{p:True for p in private},'public_real_identifier_token_matches':sum(i['reason'].startswith('Real participant') for i in issues),'issues':issues,'scan_limits':'Effective Git-ignore rules, known participant tokens and common secret patterns checked. No claim of exhaustive secret detection. Private directories not traversed; no secret values emitted. Metadata dictionaries and fictional fixtures are permitted. Original proposal retained.','temporary_git_metadata':str(repo.relative_to(ROOT)),'original_git_repository_modified':False,'candidate_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in candidates if n!='reports/deliverable_audit.json'}}
    (ROOT/'reports/deliverable_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"Checked {len(candidates)} public candidates and {len(private)} sensitive ignore probes; {len(issues)} issues. Workspace Git tracking query exit {tracked.returncode}; original repository untouched.")
    return bool(issues)


if __name__=='__main__':raise SystemExit(main())
