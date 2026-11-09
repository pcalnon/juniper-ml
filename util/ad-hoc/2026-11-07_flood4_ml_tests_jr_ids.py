"""
List the JR requirement ids the flood-4 test drafts cite, and whether each exists in the requirements index.

Reads each draft's body with `gh pr view N --json body` (read-only), extracts `JR-<REPO>-<AREA>-<NNN>` ids,
and checks every id against notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md in this tree
(auto-memory: JR-ML-QA-001 was a fabricated id, so a cited id is not evidence that it exists).
Writes `<out>` as JSON: {"by_pr": {N: [ids]}, "exists": {id: bool}}.

Usage: python3 util/ad-hoc/2026-11-07_flood4_ml_tests_jr_ids.py <out.json> N [N ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md (flood-4 consolidation)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

INDEX = Path("notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md")
JR = re.compile(r"JR-[A-Z]+(?:-[A-Z]+)*-[0-9]{3,}")


def main() -> int:
    out = Path(sys.argv[1])
    index_text = INDEX.read_text(encoding="utf-8")
    by_pr: dict[str, list[str]] = {}
    for n in sys.argv[2:]:
        proc = subprocess.run(["gh", "pr", "view", n, "--repo", "pcalnon/juniper-ml", "--json", "body"], capture_output=True, text=True, check=False)
        body = json.loads(proc.stdout).get("body", "") if proc.returncode == 0 else ""
        by_pr[n] = sorted(set(JR.findall(body)))
        print(f"#{n}: rc={proc.returncode} {by_pr[n]}")
    ids = sorted({i for v in by_pr.values() for i in v})
    exists = {i: i in index_text for i in ids}
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"by_pr": by_pr, "exists": exists}, fh, indent=2)
    print(json.dumps(exists, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
