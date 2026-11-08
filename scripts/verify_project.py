"""Stage 13: safe checks plus an optional clean isolated rebuild; never train/search/evaluate test."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from path_project.inventory import verify_manifest


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-build',action='store_true')
    args=parser.parse_args()
    settings=json.loads((ROOT/'configs/verification.json').read_text())
    cache=ROOT/settings['cache'];cache.mkdir(parents=True,exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='verification with spaces ',dir=cache))
    protected={str(p.relative_to(ROOT)):(digest(p),p.stat().st_mtime_ns) for folder in settings['protected_directories'] for p in (ROOT/folder).rglob('*') if p.is_file()}
    result={'stage':13,'checks':[],'isolated_build':None,'log_directory':str(run.relative_to(ROOT)),'no_final_test_evaluation':True,'no_real_model_training':True}
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','MPLCONFIGDIR':str(run/'matplotlib')}
    def execute(arguments,cwd,kind):
        start=time.monotonic();index=len(result['checks']);log=run/f'check_{index:02d}.log'
        with log.open('w') as stream:
            completed=subprocess.run([sys.executable,*arguments],cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT)
        item={'command':[sys.executable,*arguments],'cwd':str(cwd),'kind':kind,'exit_code':completed.returncode,'seconds':round(time.monotonic()-start,3),'log':str(log.relative_to(ROOT))}
        result['checks'].append(item);print(f"{kind}: {' '.join(arguments)} -> exit {completed.returncode}",flush=True)
        if completed.returncode:raise RuntimeError(f'Check failed; inspect {log.relative_to(ROOT)}')
    try:
        for command in settings['checks']:execute(command,ROOT,'existing evidence')
        manifest=json.loads((ROOT/'docs/original_inputs.sha256.json').read_text())
        failures=verify_manifest(ROOT,manifest)
        unexpected=[];exceptions=[]
        for failure in failures:
            name=failure.rsplit(': ',1)[0];allowed=settings['intentional_original_exceptions'].get(name)
            if allowed and (ROOT/name).is_file() and digest(ROOT/name)==allowed['sha256']:exceptions.append({'file':name,**allowed})
            else:unexpected.append(failure)
        result['original_inputs']={'baseline_files':len(manifest),'unchanged':len(manifest)-len(failures),'documented_exceptions':exceptions,'unexpected_failures':unexpected,'baseline_rewritten':False}
        if unexpected:raise RuntimeError('Unexpected original-input difference; no values printed.')
        if args.isolated_build:
            sandbox=run/'clean generated output workspace';sandbox.mkdir()
            for directory in ['src','scripts','configs','docs','tests','app','.streamlit']:
                shutil.copytree(ROOT/directory,sandbox/directory,ignore=shutil.ignore_patterns('__pycache__'))
            (sandbox/'reports').mkdir()
            # Read-only source references; no raw copies or symlinks for generated outputs.
            (sandbox/'PATH').symlink_to(ROOT/'PATH',target_is_directory=True)
            (sandbox/'.analysis').symlink_to(ROOT/'.analysis',target_is_directory=True)
            for command in settings['isolated_build_order']:execute(command,sandbox,'clean isolated build')
            compared={name:digest(ROOT/name)==digest(sandbox/name) for name in settings['rebuild_compare']}
            result['isolated_build']={'workspace':str(sandbox.relative_to(ROOT)),'clean_data_artifacts_reports_at_start':True,'reproduced_sha256':compared,'searches_repeated':False,'final_test_evaluation_repeated':False}
            if not all(compared.values()):raise RuntimeError('Regenerated evidence differs; inspect aggregate comparison flags before proceeding.')
            # Restore frozen research evidence into the isolated tree, never refit.
            shutil.copytree(ROOT/'artifacts',sandbox/'artifacts',dirs_exist_ok=True)
            shutil.copytree(ROOT/'reports',sandbox/'reports',dirs_exist_ok=True)
            execute(['scripts/verify_final_evaluation.py'],sandbox,'isolated frozen replay integrity')
            execute(['-m','pytest','tests/test_demo.py','tests/test_project_smoke.py','-q','-p','no:cacheprovider'],sandbox,'isolated synthetic end-to-end inference')
        result['status']='passed'
    except Exception as error:
        result['status']='failed';result['failure']=str(error)
    finally:
        changed=[name for name,(h,mtime) in protected.items() if not (ROOT/name).exists() or digest(ROOT/name)!=h or (ROOT/name).stat().st_mtime_ns!=mtime]
        result['protected_evidence']={'files_checked':len(protected),'hash_and_mtime_changes':changed}
        if changed:result['status']='failed'
        (ROOT/settings['report']).write_text(json.dumps(result,indent=2)+'\n')
    print(f"Verification {result['status']}; saved {settings['report']}")
    return result['status']!='passed'


if __name__=='__main__':raise SystemExit(main())
