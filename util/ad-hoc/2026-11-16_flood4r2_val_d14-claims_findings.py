"""
Write the D-14 claims lens's findings.json and text_fixes.json from one spec file, and check every text fix's old
string occurs exactly once in its file (and its new string not at all).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator MN2, claims lens, flood-4 session 9)
Created: 2026-11-16
Status: ad-hoc - investigation
Retire when: RETAINED - ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Cursor flood-4 disposition record (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md)

Usage: python3 <this file> <spec.json>
spec.json: {"status": ..., "carrier": ..., "lens": "claims", "checked": [...], "not_checked": [...], "findings": [...],
"text_fixes": [{"finding": "F1", "repo": "ml"|"cascor", "file": "<path in the carrier>", "old": "...", "new": "..."}]}
Writes <scratch>/findings.json and <scratch>/text_fixes.json (each fix gains "old_count" and "new_count"), prints a
summary, and exits 1 when any old string does not occur exactly once. Read-only on both carriers.
"""

import json
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
O = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
LENS = O / "tmp" / "flood4r2-val" / "d14-claims-lens"
ROOTS = {
    "ml": JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "agent-aa1160aea3f9c907d",
    "cascor": JUNIPER / "worktrees" / "juniper-cascor--test--ws-resume-shared-answer-table--20261115-0558--a1b0409d",
}


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    fixes = []
    bad = 0
    for fix in spec.get("text_fixes", []):
        text = (ROOTS[fix["repo"]] / fix["file"]).read_text(encoding="utf-8")
        row = {**fix, "old_count": text.count(fix["old"]), "new_count": text.count(fix["new"])}
        if row["old_count"] != 1:
            bad += 1
        fixes.append(row)
        print(f"{fix['finding']} {fix['repo']}:{fix['file']} old x{row['old_count']} new x{row['new_count']}")
    findings = {key: spec[key] for key in ("carrier", "lens", "status", "checked", "not_checked", "findings")}
    (LENS / "findings.json").write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
    (LENS / "text_fixes.json").write_text(json.dumps({"roots": {k: str(v) for k, v in ROOTS.items()}, "fixes": fixes}, indent=2) + "\n", encoding="utf-8")
    counts = {}
    for finding in spec["findings"]:
        counts[finding["severity"]] = counts.get(finding["severity"], 0) + 1
    print("findings:", counts, "fixes:", len(fixes), "bad olds:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
