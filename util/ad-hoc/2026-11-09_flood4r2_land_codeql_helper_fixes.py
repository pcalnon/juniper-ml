#!/usr/bin/env python3
"""
Clear the CodeQL prescreen's predicted alerts in three session-4 validator helpers before they ship as provenance,
without changing what any of them does.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 session 4: committing the session's helpers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-05_codeql_python_prescreen.py (predicted the alerts); session 3's precedent: three record
         probes fixed for CodeQL in juniper-ml#2530

Usage:
  2026-11-09_flood4r2_land_codeql_helper_fixes.py [--dry-run]

Edits, each refused unless its pattern matches exactly as expected:
  * ..._val_m1-r4_gh_facts.py: every ``rc, X = gh(...)`` (``rc`` is never read in main()) becomes ``X = gh(...)[1]``
    (gh returns ``(returncode, stdout)``), clearing the multiple-definition and unused-local predictions;
  * ..._val_m1-r4_real_engine.py: the first ``base, merge, head = conflict_merge(...)``, whose ``merge`` is rebound
    before it is read, keeps the triple and unpacks only base and head;
  * ..._val_m1-r4_shim_attack.py: the unused ``import os`` is removed.
Prints each file's sha256 before and after.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
GH_FACTS = ADHOC / "2026-11-09_flood4r2_val_m1-r4_gh_facts.py"
REAL_ENGINE = ADHOC / "2026-11-09_flood4r2_val_m1-r4_real_engine.py"
SHIM_ATTACK = ADHOC / "2026-11-09_flood4r2_val_m1-r4_shim_attack.py"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def fix_gh_facts(text: str) -> str:
    pattern = re.compile(r"^(?P<indent>\s+)rc, (?P<name>\w+) = (?P<call>gh\(.*\))\s*$", re.M)
    hits = pattern.findall(text)
    if not hits:
        raise SystemExit("REFUSED: gh_facts.py has no `rc, X = gh(...)` line")
    print(f"gh_facts.py: rewriting {len(hits)} `rc, X = gh(...)` line(s)")
    fixed = pattern.sub(lambda m: f"{m.group('indent')}{m.group('name')} = {m.group('call')}[1]", text)
    main_body = fixed.split("def main(", 1)[1]
    if re.search(r"\brc\b", main_body.split("\ndef ", 1)[0]):
        raise SystemExit("REFUSED: main() still reads rc after the rewrite")
    return fixed


def fix_real_engine(text: str) -> str:
    old = '    base, merge, head = conflict_merge(r, p, "a\\nb\\nc\\n", "a\\nPR\\nc\\n", "a\\nBASE\\nc\\n", "a\\nRESOLVED\\nc\\n")\n'
    new = '    triple = conflict_merge(r, p, "a\\nb\\nc\\n", "a\\nPR\\nc\\n", "a\\nBASE\\nc\\n", "a\\nRESOLVED\\nc\\n")\n    base, head = triple[0], triple[2]\n'
    if text.count(old) != 1:
        raise SystemExit(f"REFUSED: real_engine.py holds the conflict_merge line {text.count(old)} times, expected 1")
    return text.replace(old, new)


def fix_shim_attack(text: str) -> str:
    if text.count("\nimport os\n") != 1 or re.search(r"\bos\.", text):
        raise SystemExit("REFUSED: shim_attack.py's `import os` is not a single unused import")
    return text.replace("\nimport os\n", "\n", 1)


def main() -> int:
    dry_run = "--dry-run" in sys.argv[1:]
    for path, fixer in ((GH_FACTS, fix_gh_facts), (REAL_ENGINE, fix_real_engine), (SHIM_ATTACK, fix_shim_attack)):
        before = path.read_text(encoding="utf-8")
        after = fixer(before)
        compile(after, str(path), "exec")
        print(f"{path.name}: {sha(before)} -> {sha(after)}{' (dry run)' if dry_run else ''}")
        if not dry_run:
            path.write_text(after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
