"""
Re-derive the N-3 round-2 carrier's measured claims in the validator's own juniper-cascor worktree.

Claims lens, flood-4 round 2 (fix N-3, /ws/training resume losses). Three phases, run in order in ONE scratch worktree
(never the carrier's, which is only read):
  main     -- main's sources (7640d420): count the unit selection, sweep 2,000 seeds, then run the six WebSocket
              test files with the carrier's four test files copied in (claim: 79 of the 86 new tests fail, plus the
              2 updated tests).
  round1   -- main's sources plus round 1's three source edits (applied from the round-1 code validator's
              fix.patch, sha256-checked against the carrier's hashes_round1.json), with round 2's tests (claim:
              exactly the 11 cursor cases fail).
  carrier  -- all 11 carrier files copied in and sha256-checked against the carrier's manifest: count the unit
              selection (claim: 86 more than main), the six WebSocket files (claim: 0 of 238 fail), a 20,000-seed
              sweep (claim: 0 violations) and CI's unit selection with -n 4 (claim: 5,948 passed, 1 failed).

Usage: python3 <this> --phase main|round1|carrier   (results go to the lens's scratch directory)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
CARRIER = JUNIPER / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
MINE = JUNIPER / "worktrees" / "juniper-cascor--val--flood4r2-n3-r2-claims--20261109-0916--7640d420"
ORCH = Path(__file__).resolve().parents[2]
SCRATCH = ORCH / "tmp" / "flood4r2-val" / "n3-r2-claims-lens"
ROUND1_PATCH = ORCH / "tmp" / "flood4r2-val" / "n3-code-lens" / "fix.patch"
SWEEP = Path(__file__).resolve().parent / "2026-11-09_flood4r2_n3-r2_seed_sweep.py"
PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
N3R2 = CARRIER / "tmp" / "flood4-fix" / "n3-r2"

SOURCES = ["src/api/observability.py", "src/api/websocket/manager.py", "src/api/websocket/training_stream.py"]
TESTS = [
    "src/tests/unit/api/test_websocket_resume_continuity.py",
    "src/tests/unit/api/test_training_stream_coverage.py",
    "src/tests/unit/api/test_metrics_obs_wire_02.py",
    "src/tests/unit/api/test_websocket_manager.py",
]
WS_FILES = TESTS + ["src/tests/unit/api/test_websocket_seq_replay.py", "src/tests/unit/api/test_ws_broadcast_fault_isolation.py"]
DOCS = ["CHANGELOG.md", "docs/DEVELOPER_CHEATSHEET.md", "docs/api/API_SCHEMAS.md", "docs/api/JUNIPER_CASCOR_API_REFERENCE.md"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def env(extra: dict) -> dict:
    out = dict(os.environ)
    out.pop("JUNIPER_CASCOR_LOG_DIR", None)
    out["PYTHONDONTWRITEBYTECODE"] = "1"
    out.update(extra)
    return out


def log(msg: str) -> None:
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open(SCRATCH / "reruns.log", "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def run(cmd: list, label: str, extra_env: dict) -> dict:
    start = time.monotonic()
    proc = subprocess.run(cmd, cwd=MINE, env=env(extra_env), capture_output=True, text=True, check=False)
    (SCRATCH / f"rerun_{label}.out").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    secs = round(time.monotonic() - start, 1)
    log(f"{label}: exit {proc.returncode} in {secs}s")
    return {"exit": proc.returncode, "seconds": secs, "tail": proc.stdout.strip().splitlines()[-3:]}


def collect(label: str) -> dict:
    res = run([PY, "-m", "pytest", "-p", "no:cacheprovider", "-m", "unit and not slow", "--collect-only", "-q", "src/tests/unit"], label, {})
    text = (SCRATCH / f"rerun_{label}.out").read_text(encoding="utf-8")
    # This repo's addopts already carry -q, so --collect-only -q prints one "<file>: <count>" line per file.
    per_file = re.findall(r"^(src/tests/\S+\.py): (\d+)$", text, flags=re.MULTILINE)
    res["selected"] = sum(int(n) for _, n in per_file)
    res["files"] = len(per_file)
    res["new_file"] = sum(int(n) for f, n in per_file if f.endswith("test_websocket_resume_continuity.py"))
    log(f"{label}: selected {res['selected']} tests in {res['files']} files (new file: {res['new_file']})")
    return res


def junit_counts(path: Path) -> dict:
    root = ET.parse(path).getroot()
    failed = []
    total = 0
    for case in root.iter("testcase"):
        total += 1
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(case.get("classname", "") + "::" + case.get("name", ""))
    return {"tests": total, "failed": len(failed), "failed_ids": failed}


def pytest_files(label: str, files: list, workers: int = 4, timeout: int = 120) -> dict:
    junit = SCRATCH / f"junit_{label}.xml"
    (MINE / "tmp").mkdir(exist_ok=True)
    cmd = [PY, "-m", "pytest", "-p", "no:cacheprovider", "-m", "unit and not slow", f"--timeout={timeout}", "-q", "-rfE"]
    cmd += ["-n", str(workers), f"--junitxml={junit}", f"--basetemp={MINE / 'tmp' / ('val-basetemp-' + label)}"] + files
    res = run(cmd, label, {})
    res.update(junit_counts(junit))
    log(f"{label}: {res['tests']} tests, {res['failed']} failed")
    return res


def sweep(label: str, first: int, n: int) -> dict:
    out = SCRATCH / f"sweep_{label}.json"
    res = run([PY, str(SWEEP), "--first", str(first), "--n", str(n), "--out", str(out)], label, {"SWEEP_SRC": str(MINE / "src")})
    data = json.loads(out.read_text(encoding="utf-8"))
    res.update({k: data[k] for k in ("code_under_test", "n", "outcomes", "violations")})
    log(f"{label}: {data['violations']} of {data['n']} seeds violate; outcomes {data['outcomes']}")
    return res


def copy_from_carrier(paths: list) -> dict:
    out = {}
    for rel in paths:
        (MINE / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CARRIER / rel, MINE / rel)
        out[rel] = sha(MINE / rel) == sha(CARRIER / rel)
    return out


def save(phase: str, result: dict) -> None:
    path = SCRATCH / "reruns.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data[phase] = result
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def phase_main() -> dict:
    keep = SCRATCH / "main_sources"
    keep.mkdir(exist_ok=True)
    for rel in SOURCES:
        shutil.copyfile(MINE / rel, keep / Path(rel).name)
    result = {"main_source_sha256": {rel: sha(MINE / rel) for rel in SOURCES}}
    result["collect"] = collect("collect_main")
    result["sweep"] = sweep("main_0_2000", 0, 2000)
    result["copied_tests"] = copy_from_carrier(TESTS)
    result["ws_files"] = pytest_files("ws6_on_main", WS_FILES)
    new = [f for f in result["ws_files"]["failed_ids"] if "test_websocket_resume_continuity" in f]
    result["new_file_failed"] = len(new)
    return result


def phase_round1() -> dict:
    for rel in SOURCES:
        shutil.copyfile(SCRATCH / "main_sources" / Path(rel).name, MINE / rel)
    includes = [f"--include={rel}" for rel in SOURCES]
    applied = run(["git", "-C", str(MINE), "apply"] + includes + [str(ROUND1_PATCH)], "apply_round1", {})
    want = {f["path"]: f["sha256"] for f in json.loads((N3R2 / "hashes_round1.json").read_text(encoding="utf-8"))["files"]}
    result = {"apply": applied, "round1_sha256_match": {rel: sha(MINE / rel) == want[rel] for rel in SOURCES}}
    result["copied_tests"] = copy_from_carrier(TESTS)
    result["ws_files"] = pytest_files("ws6_on_round1", WS_FILES)
    return result


def phase_carrier() -> dict:
    manifest = {f["path"]: f["sha256"] for f in json.loads((N3R2 / "manifest.json").read_text(encoding="utf-8"))["files"]}
    result = {"copied": copy_from_carrier(SOURCES + TESTS + DOCS)}
    result["matches_manifest"] = {rel: sha(MINE / rel) == manifest[rel] for rel in manifest}
    result["collect"] = collect("collect_carrier")
    result["ws_files"] = pytest_files("ws6_on_carrier", WS_FILES)
    result["sweep"] = sweep("carrier_0_20000", 0, 20000)
    result["unit"] = pytest_files("unit_carrier", ["src/tests/unit"], timeout=60)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["main", "round1", "carrier"], required=True)
    args = ap.parse_args()
    log(f"phase {args.phase} start")
    phases = {"main": phase_main, "round1": phase_round1, "carrier": phase_carrier}
    result = phases[args.phase]()
    save(args.phase, result)
    log(f"phase {args.phase} done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
