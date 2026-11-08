"""Profile canonical TSV structure and duplicate hashes, without exposing IDs."""
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from path_project.inventory import load_config, sha256


def inventory(root):
    results = []
    for wave in load_config(root)["waves"]:
        path = root / wave["data"]
        with path.open(newline="", encoding="utf-8-sig") as source:
            reader = csv.reader(source, delimiter="\t")
            header = next(reader)
            count = 0
            malformed = 0
            for row in reader:
                count += 1
                malformed += len(row) != len(header)
        duplicate = root / "PATH/TSV" / path.name
        digest = sha256(path)
        results.append({**wave, "rows": count, "columns": len(header),
            "malformed_rows": malformed, "personid_present": "PERSONID" in header,
            "former_columns": [c for c in header if "FMR_ESTD_CIGS" in c],
            "outcome_columns": [c for c in header if c.endswith("_A_P30D_CIGS")],
            "quit_days_columns": [c for c in header if c.endswith("_DAYSQUIT_CIGS")],
            "weight_design_columns": [c for c in header if any(t in c.upper() for t in ("WGT", "WEIGHT", "STRAT", "PSU"))],
            "sha256": digest, "duplicate_path": str(duplicate.relative_to(root)),
            "duplicate_identical": duplicate.is_file() and sha256(duplicate) == digest,
            "documentation_present": all((root / wave[k]).is_file() for k in ("codebook", "questionnaire"))})
    return results

if __name__ == "__main__":
    output = ROOT / "reports/input_inventory.json"
    output.write_text(json.dumps(inventory(ROOT), indent=2) + "\n")
    print(f"Wrote aggregate inventory: {output}")
