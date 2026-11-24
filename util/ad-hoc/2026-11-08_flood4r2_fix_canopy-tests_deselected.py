#!/usr/bin/env python3
"""
Name the tests canopy's CI unit lane deselects: collect its path scope with and without the marker expression, diff.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (Cursor flood-4 round 2: canopy-claims-lens F2, the PR body's gating-variable claim)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/canopy-claims-lens/findings.json F2

Usage:
  2026-11-08_flood4r2_fix_canopy-tests_deselected.py <canopy worktree> <out dir>

Both collections run through 2026-11-08_flood4r2_val_canopy-tests_fenced_pytest.py (CI's three gating variables
set to "0"; connects to this host's service ports refused) with the venv over JuniperCanopy1 that carries pytest
9.2.0, ``-I -B``, ``--collect-only -q``. Collection runs no test body. Writes <out dir>/deselected.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
REPO = ADHOC.parents[1]
PYTHON = str(REPO / "tmp" / "flood4r2-fix" / "venv-canopy-py313-pytest92" / "bin" / "python")
RUNNER = str(ADHOC / "2026-11-08_flood4r2_val_canopy-tests_fenced_pytest.py")
MARKERS = "not requires_cascor and not requires_server and not slow"
SCOPE = ["src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/"]


def _collect(wt: str, out: Path, tag: str, marker_args: list[str]) -> tuple[set[str], str, int]:
    # No -q here: canopy's addopts already carries one, and a second collapses the listing to per-file counts.
    cmd = [PYTHON, "-I", "-B", RUNNER, "--wt", wt, "--out", str(out / f"fence_{tag}.json"), "--", "--collect-only", "-p", "no:cacheprovider", *marker_args, *SCOPE]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, env={**os.environ, "LD_LIBRARY_PATH": "", "LIBTORCH": ""})
    (out / f"collect_{tag}.log").write_text(f"$ {' '.join(cmd)}\n# exit={proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}", encoding="utf-8")
    nodes = {line.strip() for line in proc.stdout.splitlines() if line.startswith("src/tests/") and "::" in line}
    tail = [line for line in proc.stdout.splitlines() if "collected" in line or "deselected" in line]
    return nodes, (tail[-1].strip() if tail else "<no summary>"), proc.returncode


def main(argv: list[str]) -> int:
    wt, out = argv[1], Path(argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    selected, sel_summary, sel_exit = _collect(wt, out, "with_markers", ["-m", MARKERS])
    everything, all_summary, all_exit = _collect(wt, out, "without_markers", [])
    deselected = sorted(everything - selected)
    record = {
        "worktree": wt,
        "scope": SCOPE,
        "markers": MARKERS,
        "with_markers": {"exit": sel_exit, "nodes": len(selected), "summary": sel_summary},
        "without_markers": {"exit": all_exit, "nodes": len(everything), "summary": all_summary},
        "deselected": deselected,
        "selected_but_not_in_full": sorted(selected - everything),
    }
    (out / "deselected.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "worktree"}, indent=1))
    return 0 if sel_exit == 0 and all_exit == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
