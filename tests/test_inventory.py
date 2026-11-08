import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from path_project.inventory import sha256, verify_manifest, load_config


def test_integrity_detects_mutation_and_missing(tmp_path):
    source = tmp_path / "input.txt"
    source.write_text("original")
    manifest = {"input.txt": {"bytes": source.stat().st_size, "sha256": sha256(source)}}
    assert verify_manifest(tmp_path, manifest) == []
    source.write_text("modified")
    assert verify_manifest(tmp_path, manifest) == ["input.txt: changed"]
    source.unlink()
    assert verify_manifest(tmp_path, manifest) == ["input.txt: missing"]


def test_canonical_wave_selection():
    root = Path(__file__).resolve().parents[1]
    waves = load_config(root)["waves"]
    assert [w["wave"] for w in waves] == list(range(1, 9))
    assert len({w["data"] for w in waves}) == 8
    assert all("/TSV/" not in w["data"] for w in waves)
    assert all((root / w[k]).is_file() for w in waves for k in ("data", "codebook", "questionnaire"))
