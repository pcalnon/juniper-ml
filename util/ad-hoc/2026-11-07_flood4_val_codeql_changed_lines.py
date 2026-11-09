"""
Flood-4 validation: run util/ad-hoc/2026-10-05_codeql_python_prescreen.py on EVERY changed .py of the
carrier (including the builder's util/ad-hoc helpers, read from the carrier's staged tree into a scratch
copy) and classify each prediction as on a CHANGED line (a finding) or on an unchanged main line.

Usage: python3 <this> <out.json>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens), item 6
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
TREE = "ddfae11e73e0663bf798fef2834dfc559493e7fe"
PRESCREEN = HERE / "util" / "ad-hoc" / "2026-10-05_codeql_python_prescreen.py"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=HERE, check=True, capture_output=True, text=True).stdout


def changed_lines(path: str) -> set[int]:
    out: set[int] = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", git("diff", "-U0", "--no-renames", BASE, TREE, "--", path), re.M):
        start, count = int(m.group(1)), int(m.group(2) or "1")
        out.update(range(start, start + count))
    return out


def main() -> int:
    out = Path(sys.argv[1])
    paths = [p for p in git("diff", "--name-only", "--no-renames", BASE, TREE).splitlines() if p.endswith(".py")]
    scratch = HERE / "tmp" / "val_codeql_scratch"
    files = []
    for p in paths:
        dst = scratch / p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(subprocess.run(["git", "cat-file", "blob", f"{TREE}:{p}"], cwd=HERE, check=True, capture_output=True).stdout)
        files.append((p, dst))
    r = subprocess.run([sys.executable, str(PRESCREEN), *[str(d) for _, d in files]], cwd=HERE, capture_output=True, text=True)
    preds = []
    for line in r.stdout.splitlines():
        m = re.match(r"^(.*?):(\d+): (\S+): (.*)$", line)
        if not m:
            continue
        rel = str(Path(m.group(1)).resolve().relative_to(scratch.resolve()))
        ln = int(m.group(2))
        preds.append({"path": rel, "line": ln, "rule": m.group(3), "msg": m.group(4)[:200], "on_changed_line": ln in changed_lines(rel)})
    res = {"files": len(files), "prescreen_rc": r.returncode, "tail": r.stdout.strip().splitlines()[-1:], "predictions": preds, "on_changed_lines": [p for p in preds if p["on_changed_line"]]}
    out.write_text(json.dumps(res, indent=2) + "\n")
    print(f"files={len(files)} rc={r.returncode} predictions={len(preds)} on_changed_lines={len(res['on_changed_lines'])}")
    for p in preds:
        print(("CHANGED " if p["on_changed_line"] else "main    ") + f"{p['path']}:{p['line']}: {p['rule']}: {p['msg'][:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
