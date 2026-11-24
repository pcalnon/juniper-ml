"""
Mutation runs for juniper-cascor's resume-loss fix (validator n3): the two-lock-section mutant plus two of n3's own.

Edits a SCRATCH cascor worktree only (never the frozen artifact), runs the builder's six WebSocket test files and,
separately, n3's extra tests, then restores each file and verifies its hash.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-cascor fix/ws-resume-losses
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

WT = Path(Path.home(), "Development/python/Juniper/worktrees/juniper-cascor--validate--ws-resume-losses-n3-code--20261109-0324--f3dfee8c")
FROZEN = Path(Path.home(), "Development/python/Juniper/worktrees/juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c")
OUT = Path(Path.home(), "Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert/tmp/flood4r2-val/n3-code-lens/mutants")
PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
MANAGER = "src/api/websocket/manager.py"
STREAM = "src/api/websocket/training_stream.py"
BUILDER_TESTS = [
    "src/tests/unit/api/test_websocket_resume_continuity.py",
    "src/tests/unit/api/test_training_stream_coverage.py",
    "src/tests/unit/api/test_metrics_obs_wire_02.py",
    "src/tests/unit/api/test_websocket_manager.py",
    "src/tests/unit/api/test_websocket_seq_replay.py",
    "src/tests/unit/api/test_ws_broadcast_fault_isolation.py",
]
EXTRA_TESTS = ["src/tests/unit/api/test_n3_validator_extra.py"]

MUTANTS = [
    {
        "name": "MA-two-lock-sections-final-check-then-activate",
        "why": "the parallel service-core finding: the final check and the activation in two `async with self._lock` sections",
        "edits": [
            (
                MANAGER,
                "                if not missed:\n                    # No await between this check and the activation: a\n                    # broadcast numbered after the check fans out to the socket.\n                    self._activate(websocket)\n                    return True\n",
                "                if not missed:\n                    break\n",
            ),
            (
                MANAGER,
                '                cursor = event["seq"]\n\n    async def disconnect(',
                '                cursor = event["seq"]\n        async with self._lock:\n            self._activate(websocket)\n        return True\n\n    async def disconnect(',
            ),
        ],
    },
    {
        "name": "MB-no-catch-up-when-nothing-was-replayed",
        "why": "n3 #1: _handle_resume promotes unconditionally when the replay snapshot was empty",
        "edits": [
            (
                STREAM,
                '    if not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n        await _abort("the catch-up after the replay did not complete")\n',
                '    if not events:\n        await ws_manager.promote_to_active(websocket)\n    elif not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n        await _abort("the catch-up after the replay did not complete")\n',
            )
        ],
    },
    {
        "name": "MC-eviction-checked-on-the-first-catch-up-pass-only",
        "why": "n3 #2: later catch-up passes read the buffer without replay_since's range check, so a later eviction is skipped silently",
        "edits": [
            (MANAGER, "        cursor = max(replayed_through, 0)\n        while True:\n", "        cursor = max(replayed_through, 0)\n        first_pass = True\n        while True:\n"),
            (
                MANAGER,
                "                    missed = self.replay_since(cursor)\n",
                '                    missed = self.replay_since(cursor) if first_pass else [m for m in list(self._replay_buffer) if m["seq"] > cursor]\n                    first_pass = False\n',
            ),
        ],
    },
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(label: str, files: list) -> dict:
    env = dict(os.environ)
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    pyc = OUT / "pycache-empty"
    pyc.mkdir(parents=True, exist_ok=True)
    env["PYTHONPYCACHEPREFIX"] = str(pyc)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [PY, "-m", "pytest", "-p", "no:cacheprovider", "-m", "unit and not slow", "--timeout=120", "-rfE", *files]
    t0 = time.monotonic()
    proc = subprocess.run(cmd, cwd=WT, env=env, capture_output=True, text=True)
    (OUT / f"{label}.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", proc.stdout, re.M)))
    summary = next((ln for ln in reversed(proc.stdout.splitlines()) if re.search(r"\d+ (passed|failed)", ln)), "")
    return {"rc": proc.returncode, "secs": round(time.monotonic() - t0, 1), "summary": summary.strip("= "), "failed": failed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    hashes = {rel: sha(WT / rel) for rel in (MANAGER, STREAM)}
    frozen_same = {rel: sha(FROZEN / rel) == hashes[rel] for rel in (MANAGER, STREAM)}
    results = {"scratch_matches_frozen": frozen_same, "baseline": {}, "mutants": {}}
    if not all(frozen_same.values()):
        print("scratch worktree does not match the frozen artifact; stopping", frozen_same)
        return 2
    results["baseline"]["builder"] = run("BASELINE-builder", BUILDER_TESTS)
    results["baseline"]["extra"] = run("BASELINE-extra", EXTRA_TESTS)
    print("BASELINE", results["baseline"]["builder"]["summary"], "|", results["baseline"]["extra"]["summary"])
    if results["baseline"]["builder"]["rc"] or results["baseline"]["extra"]["rc"]:
        print("baseline not green; stopping")
        (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        return 1
    for m in MUTANTS:
        if args.only and not any(m["name"].startswith(p) for p in args.only):
            continue
        originals = {}
        try:
            for rel, old, new in m["edits"]:
                p = WT / rel
                originals.setdefault(rel, p.read_bytes())
                text = p.read_text(encoding="utf-8")
                if text.count(old) != 1:
                    raise SystemExit(f"{m['name']}: edit matched {text.count(old)} times in {rel}")
                p.write_text(text.replace(old, new), encoding="utf-8")
            rb = run(f"{m['name']}--builder", BUILDER_TESTS)
            rx = run(f"{m['name']}--extra", EXTRA_TESTS)
        finally:
            for rel, data in originals.items():
                (WT / rel).write_bytes(data)
                if sha(WT / rel) != hashes[rel]:
                    raise SystemExit(f"RESTORE FAILED {rel}")
        results["mutants"][m["name"]] = {"why": m["why"], "builder_suite": rb, "builder_killed": bool(rb["rc"] and rb["failed"]), "n3_extra": rx, "n3_extra_killed": bool(rx["rc"] and rx["failed"])}
        print(f"{m['name']}: builder_killed={results['mutants'][m['name']]['builder_killed']} ({rb['summary']}) | n3_extra_killed={results['mutants'][m['name']]['n3_extra_killed']} ({rx['summary']})")
    results["after"] = {rel: sha(WT / rel) == hashes[rel] for rel in (MANAGER, STREAM)}
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print("restored:", results["after"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
