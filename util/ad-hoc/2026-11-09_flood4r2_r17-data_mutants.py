#!/usr/bin/env python3
"""
Show the 44 newly selected test_security.py tests are non-vacuous: one-line mutants of the code they pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4, owner ruling 17: "data: 44 unrun tests")
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (mutation check for the juniper-data unit-mark fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 17 is recorded in the record-update PR)

PER MUTANT (one at a time; never run this while another pytest imports the same worktree)
  1. sha256 the target; delete every __pycache__ under juniper_data/ (runs use -B, so none should exist).
  2. Replace one exact line fragment (it must occur exactly once).
  3. Run the four newly marked classes under the unit lane's -m and --timeout: KILLED when pytest exits 1 with
     at least one FAILED test.
  4. With --main-lane: run CI's whole unit-lane selection as main had it (the fixed tree with the four classes
     --deselect-ed; the collect helper proves that set equals main's 2,271), without coverage. A pass there means
     CI's unit lane on main could not see this break (the other lanes are not run here).
  5. Restore the original bytes in a ``finally`` and require the sha256 to match the step-1 value.
Writes <out>/mutants.json and one log per run under <out>/logs/mutants/.

Usage:
    python3 <this> --worktree <juniper-data worktree> --out <dir> [--main-lane] [--only M1,M2]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argv: the JuniperData interpreter running pytest
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperData/bin/python"
SEC = "juniper_data/tests/unit/test_security.py"
NEW_CLASSES = ("TestAPIKeyAuth", "TestRateLimiter", "TestSecurityModuleFunctions", "TestApiKeysSettingsValidator")
MUTANTS = [
    {
        "id": "M1",
        "file": "juniper_data/api/security.py",
        "what": "APIKeyAuth.__init__ keeps blank and whitespace-only keys (drops the APD-DATA-003 'and k.strip()' filter)",
        "old": "if isinstance(k, str) and k.strip()))",
        "new": "if isinstance(k, str)))",
    },
    {
        "id": "M2",
        "file": "juniper_data/api/security.py",
        "what": "RateLimiter._get_key's no-client fallback becomes 'ip:none' instead of 'ip:unknown'",
        "old": 'client_ip = request.client.host if request.client else "unknown"',
        "new": 'client_ip = request.client.host if request.client else "none"',
    },
    {
        "id": "M3",
        "file": "juniper_data/api/settings.py",
        "what": "Settings._parse_api_keys' list branch returns every entry unfiltered (the APD-DATA-003 list-branch defect)",
        "old": "cleaned = [k.strip() if isinstance(k, str) else k for k in v if not isinstance(k, str) or k.strip()]",
        "new": "cleaned = list(v)",
    },
]
FAILED_RE = re.compile(r"^FAILED (\S+)")
# Bordered or bare; pytest's addopts already carry one -q, and a second (-qq) prints no summary line at all.
SUMMARY_RE = re.compile(r"^=*\s*(\d+ (?:passed|failed|error|skipped|deselected).*?)\s*=*$")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _purge_pycache(root: Path) -> int:
    dirs = [p for p in root.rglob("__pycache__") if p.is_dir()]
    for d in dirs:
        shutil.rmtree(d)
    return len(dirs)


def _pytest(wt: Path, argv_tail: list[str], log: Path) -> dict:
    argv = [PYTHON, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-p", "no:randomly", "-m", "unit and not slow", *argv_tail]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(f"$ (cwd={wt}) {' '.join(argv)}\n")
        fh.flush()
        proc = subprocess.run(argv, cwd=wt, env=env, stdout=fh, stderr=subprocess.STDOUT, check=False)  # nosec B603
        fh.write(f"\n[exit {proc.returncode}]\n")
    with open(log, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    failed = [m.group(1) for ln in lines if (m := FAILED_RE.match(ln))]
    summ = [m.group(1) for ln in lines if (m := SUMMARY_RE.match(ln.strip()))]
    return {"exit": proc.returncode, "summary": summ[-1] if summ else "<none>", "failed": failed, "log": str(log)}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--main-lane", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    wt, out = args.worktree.resolve(), args.out.resolve()
    wanted = {s for s in args.only.split(",") if s}
    new44 = [f"{SEC}::{c}" for c in NEW_CLASSES]
    results = []
    for mut in MUTANTS:
        if wanted and mut["id"] not in wanted:
            continue
        target = wt / mut["file"]
        original = target.read_bytes()
        sha_before = _sha(target)
        text = original.decode("utf-8")
        if text.count(mut["old"]) != 1:
            raise SystemExit(f"{mut['id']}: the fragment occurs {text.count(mut['old'])} times in {mut['file']}, not once")
        line_no = text[: text.index(mut["old"])].count("\n") + 1
        rec = {**{k: mut[k] for k in ("id", "file", "what", "old", "new")}, "line": line_no, "sha256_before": sha_before}
        rec["pycache_dirs_removed"] = _purge_pycache(wt / "juniper_data")
        try:
            target.write_bytes(text.replace(mut["old"], mut["new"], 1).encode("utf-8"))
            rec["sha256_mutated"] = _sha(target)
            new_run = _pytest(wt, [*new44, "--timeout=60", "-rf"], out / "logs" / "mutants" / f"{mut['id']}_new44.log")
            rec["new44"] = new_run
            rec["killed_by_new44"] = new_run["exit"] == 1 and bool(new_run["failed"])
            if args.main_lane:
                deselect = [f"--deselect={n}" for n in new44]
                lane = _pytest(wt, ["juniper_data/tests/unit", "--timeout=60", "--maxfail=5", "-rf", *deselect], out / "logs" / "mutants" / f"{mut['id']}_main_selection_lane.log")
                rec["main_selection_lane"] = lane
                rec["survives_main_selection_lane"] = lane["exit"] == 0
        finally:
            target.write_bytes(original)
            rec["sha256_after"] = _sha(target)
            rec["restored_byte_for_byte"] = rec["sha256_after"] == sha_before
            rec["pycache_dirs_removed_after"] = _purge_pycache(wt / "juniper_data")
        results.append(rec)
        print(json.dumps({k: rec[k] for k in rec if k in ("id", "line", "killed_by_new44", "survives_main_selection_lane", "restored_byte_for_byte")} | {"new44": rec["new44"]["summary"], "new44_failed": rec["new44"]["failed"]}, indent=1), flush=True)
    dest = out / ("mutants_main_lane.json" if args.main_lane else "mutants.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
        fh.write("\n")
    print(f"wrote {dest}")
    ok = all(r["killed_by_new44"] and r["restored_byte_for_byte"] for r in results)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
