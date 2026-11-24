"""
Hash every file the two D-14 carriers' manifests list, and their text deliverables, and compare with the manifests.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator MN2, claims lens, flood-4 session 9)
Created: 2026-11-16
Status: ad-hoc - investigation
Retire when: RETAINED - ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Cursor flood-4 disposition record (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md)

Usage: python3 <this file> <label>   (writes <scratch>/carrier_hashes_<label>.json and prints a summary)
Read-only on both carriers.
"""

import hashlib
import json
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ML = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "agent-aa1160aea3f9c907d"
CC = JUNIPER / "worktrees" / "juniper-cascor--test--ws-resume-shared-answer-table--20261115-0558--a1b0409d"
O = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
SCRATCH = O / "tmp" / "flood4r2-val" / "d14-claims-lens"
TEXTS = ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt", "stamps.json", "manifest.json", "DESIGN.md", "REPORT.txt")


def sha256(path):
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(root):
    deliver = root / "tmp" / "flood4-fix" / "d14-resume"
    manifest = json.loads((deliver / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    entries = list(manifest.get("files", []))
    for helper in manifest.get("provenance_helpers", []) or []:
        if isinstance(helper, dict):
            entries.append(helper)
    for entry in entries:
        got = sha256(root / entry["path"])
        rows.append({"path": entry["path"], "status": entry.get("status"), "manifest": entry.get("sha256"), "now": got, "equal": got == entry.get("sha256")})
    texts = {name: sha256(deliver / name) for name in TEXTS}
    return {"root": str(root), "base_sha": manifest.get("base_sha"), "files": rows, "texts": texts, "all_equal": all(r["equal"] for r in rows)}


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "start"
    out = {"ml": check(ML), "cascor": check(CC)}
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / f"carrier_hashes_{label}.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for key, res in out.items():
        bad = [r["path"] for r in res["files"] if not r["equal"]]
        print(f"{key}: base {res['base_sha']}; {len(res['files'])} files; all equal to manifest: {res['all_equal']}; differing: {bad}")


if __name__ == "__main__":
    main()
