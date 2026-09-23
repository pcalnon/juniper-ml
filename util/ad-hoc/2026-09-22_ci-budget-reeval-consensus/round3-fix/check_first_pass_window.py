#!/usr/bin/env python3
"""
Round-3 fix check: does the reprobe's first-pass probe now print and record each row's window?

Project: juniper-ml
Sub-Project: ad-hoc tooling (consensus round 3 fix pass)
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- single-use verification; read-only (GitHub REST reads only)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Runs probe_first_pass on ONE repo with a small sample, so the check costs a few dozen calls.
Usage: python3 check_first_pass_window.py [repo] [n]
"""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TARGET = ROOT / "util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py"


def main() -> int:
    repo = sys.argv[1] if len(sys.argv) > 1 else "juniper-deploy"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    spec = importlib.util.spec_from_file_location("reprobe_window_check", TARGET)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["reprobe_window_check"] = mod
    spec.loader.exec_module(mod)
    mod.REPOS = [repo]
    res = mod.probe_first_pass(n=n)
    row = res["rows"][0]
    print(json.dumps({k: row.get(k) for k in ("repo", "window", "sample_prs", "healthy", "verdict")}))
    ok = bool(row.get("window")) and row.get("window") != "empty" and len(row.get("sample_prs") or []) == n
    print("WINDOW RECORDED" if ok else "WINDOW MISSING")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
