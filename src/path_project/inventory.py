"""Read-only input integrity checks; never serialize respondent records."""
from pathlib import Path
import hashlib
import json


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_manifest(root, manifest):
    failures = []
    for name, expected in manifest.items():
        path = Path(root) / name
        if not path.is_file():
            failures.append(name + ": missing")
        elif path.stat().st_size != expected["bytes"] or sha256(path) != expected["sha256"]:
            failures.append(name + ": changed")
    return failures


def load_config(root):
    return json.loads((Path(root) / "configs/project.json").read_text())
