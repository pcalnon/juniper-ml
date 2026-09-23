#!/usr/bin/env python3
"""
Round-3 fix check: the reprobe's soak probe must list a queued/running soak job as IN FLIGHT,
not score it as a lost log (which made `all` exit 2 whenever CI was busy).

Project: juniper-ml
Sub-Project: ad-hoc tooling (consensus round 3 fix pass)
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- single-use verification; hermetic (every GitHub read is stubbed; no network)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Feeds probe_soak one queued check-run and one completed check-run whose log examined a file.
PASS = no Unmeasurable, one in-flight job listed, one completed run scored. A copy of the probe
with the status guard deleted must FAIL the same check (the control that the check can fail).
Usage: python3 check_soak_in_flight.py
"""

import importlib.util
import subprocess  # nosec B404 -- only the stubbed CompletedProcess type is used; nothing is executed
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TARGET = ROOT / "util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py"
GUARD = '            if cr.get("status") != "completed":\n'
HEAD = "a" * 40
BASE = "b" * 40
LOG = f"examining 1 changed markdown file(s) against {BASE}\n[ OK ] doc.md\n"


def load(source: str, name: str):
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(TARGET)  # the probe resolves ROOT from its own path
    sys.modules[name] = mod
    exec(compile(source, str(TARGET), "exec"), mod.__dict__)  # nosec B102 -- executes the repo's own probe source
    return mod


def stub(mod) -> None:
    runs = [{"head_sha": HEAD}]
    checks = [
        {"id": 1, "status": "queued", "conclusion": None, "started_at": None},
        {"id": 2, "status": "completed", "conclusion": "success", "started_at": "2026-09-23T01:00:00Z"},
    ]

    def gh_pages(path, key=None, limit_pages=30):
        return runs

    def gh_json(path, attempts=3):
        if "/check-runs?" in path:
            return {"check_runs": checks}
        if path.endswith("/pulls"):
            return [{"number": 42}]
        if "/pulls/42" in path:
            return {"head": {"sha": HEAD}, "merged_at": None, "state": "open"}
        raise AssertionError(f"unexpected read {path}")

    def run(argv, cwd=None, check=True):
        job = argv[-1].split("/jobs/")[1].split("/")[0]
        if job == "1":
            return subprocess.CompletedProcess(argv, 1, "", "HTTP 404")
        return subprocess.CompletedProcess(argv, 0, LOG, "")

    mod.gh_pages, mod.gh_json, mod.run = gh_pages, gh_json, run
    mod.time.sleep = lambda s: None


def verdict(mod) -> str:
    try:
        res = mod.probe_soak("2026-09-23T00:00:00Z")
    except mod.Unmeasurable as exc:
        return f"UNMEASURABLE: {exc}"
    return f"in_flight={len(res['in_flight'])} completed={res['soak_runs']} examined={res['examined_runs']}"


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    if source.count(GUARD) != 1:
        print("GUARD NOT FOUND -- the check is stale, not passing")
        return 2
    fixed = load(source, "reprobe_soak_fixed")
    stub(fixed)
    got = verdict(fixed)
    print(f"fixed probe:   {got}")
    unguarded_src = source.replace(GUARD, '            if False:  # guard deleted for the control\n')
    unguarded = load(unguarded_src, "reprobe_soak_unguarded")
    stub(unguarded)
    ctrl = verdict(unguarded)
    print(f"guard deleted: {ctrl}")
    # The control must fail for the RIGHT reason: the queued run scored as a lost log.
    expected_ctrl = "UNMEASURABLE: soak: 1 completed run(s) whose log could not be read after retries: [1]"
    ok = got == "in_flight=1 completed=1 examined=1" and ctrl == expected_ctrl
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
