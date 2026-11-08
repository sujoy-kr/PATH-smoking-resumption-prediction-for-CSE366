"""Record actual runtime versions and check essential imports without installation."""
import importlib
import json
import os
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'configs/project.json').read_text())
cache = ROOT / config['runtime_cache_dir']
cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(cache / 'matplotlib'))
result = {'executable': sys.executable, 'version': sys.version,
          'platform': platform.platform(), 'prefix': sys.prefix,
          'base_prefix': sys.base_prefix, 'isolated': sys.prefix != sys.base_prefix,
          'imports': {}}
for name in config['environment_check_imports']:
    try:
        module = importlib.import_module(name)
        result['imports'][name] = {'ok': True, 'version': getattr(module, '__version__', 'not exposed')}
    except Exception as exc:
        result['imports'][name] = {'ok': False, 'error': str(exc)}
output = ROOT / config['report_dir'] / 'environment.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(f"Python: {sys.executable}; isolated: {result['isolated']}")
print(f"Imports passed: {sum(v['ok'] for v in result['imports'].values())}/{len(result['imports'])}")
raise SystemExit(not (result['isolated'] and all(v['ok'] for v in result['imports'].values())))
