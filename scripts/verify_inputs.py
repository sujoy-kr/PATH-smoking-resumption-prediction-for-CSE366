"""Verify originals against the stage 1 baseline; safe to rerun."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from path_project.inventory import verify_manifest

if __name__ == "__main__":
    manifest = json.loads((ROOT / "docs/original_inputs.sha256.json").read_text())
    failures = verify_manifest(ROOT, manifest)
    for failure in failures:
        print(failure)
    print(f"Verified {len(manifest) - len(failures)}/{len(manifest)} original files unchanged")
    raise SystemExit(bool(failures))
