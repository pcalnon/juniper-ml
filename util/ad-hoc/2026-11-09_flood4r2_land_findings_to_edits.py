#!/usr/bin/env python3
"""
Turn a final check's findings.json into an edits spec for 2026-11-08_flood4r2_fix_apply_edits.py, after
snapshotting every file the edits touch.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 session 4: landing the fix carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-08_flood4r2_fix_apply_edits.py (applies the spec this writes)

Usage:
  2026-11-09_flood4r2_land_findings_to_edits.py <tree> <findings.json> <deliverables-rel> <out-dir>

<tree> is the carrier worktree. <deliverables-rel> is the carrier's deliverables directory relative to <tree>
(for example ``tmp/flood4-fix/m3-r3``): a fix whose ``file`` is a bare name with no directory part
(``pr_body.txt``, ``commit_body.txt``) is mapped into it. Every fix must carry ``applies: true`` (or omit the key).
A finding's edits are read from its ``fixes`` list or, failing that, its ``fix`` list (the two checkers' schemas).
Writes <out-dir>/edits.json and copies each touched file to <out-dir>/pristine/<repo-relative path> first.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(__doc__)
        return 2
    tree = Path(argv[1]).resolve()
    findings = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    deliverables = argv[3].strip("/")
    out = Path(argv[4])
    edits = []
    for finding in findings["findings"]:
        for fix in finding.get("fixes", finding.get("fix", [])) or []:
            if not isinstance(fix, dict):
                print(f"REFUSED: {finding['id']} carries a prose fix, not an old -> new edit: apply it by hand")
                return 1
            if fix.get("applies", True) is not True:
                print(f"REFUSED: {finding['id']} {fix['file']} is marked applies={fix.get('applies')!r}")
                return 1
            rel = fix["file"]
            if "/" not in rel and not (tree / rel).exists():
                rel = f"{deliverables}/{rel}"
            edits.append({"id": finding["id"], "file": rel, "old": fix["old"], "new": fix["new"]})
    files = sorted({edit["file"] for edit in edits})
    for rel in files:
        source = tree / rel
        if not source.is_file():
            print(f"REFUSED: {rel} does not exist in {tree}")
            return 1
        target = out / "pristine" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    out.mkdir(parents=True, exist_ok=True)
    (out / "edits.json").write_text(json.dumps({"worktree": str(tree), "edits": edits}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(edits)} edits over {len(files)} files: {', '.join(files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
