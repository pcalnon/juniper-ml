"""
Repeat-run and mutation-check canopy's fixed-sleep follow-up (the five tests canopy#664 listed but did not change).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy fix/fixed-sleep-lower-bounds-followup; canopy#664's "Other instances of the shape (listed, not changed)"

Two questions, both about the NEW assertions rather than the old sleeps:

1. ``--repeat N``: is ``test_cascade_unit_addition``'s new ``len(hidden_units) >= 1`` stable? It replaced a
   vacuous ``>= 0``, and an install is only reached when a candidate clears ``MIN_CANDIDATE_CORRELATION``,
   so "always" is empirical. ``--burn K`` adds K busy processes (a loaded runner).
2. mutations: does each new assertion fail on the defect it exists for? Notably M2 -- a broadcast whose
   send RAISES -- which the old ``send_json.called or manager.message_count > 0`` accepted, because
   ``message_count`` is incremented before the send.

Mutations edit canopy SOURCE in the given worktree, one at a time; each anchor must match exactly once
(else the script refuses), and the file is restored byte-for-byte in a ``finally`` and verified.

Usage:
    python util/ad-hoc/2026-09-23_fixed_sleep_followup_checks.py <canopy-worktree> [--repeat 30] [--burn 0] [--skip-mutations]
"""

import argparse
import multiprocessing as mp
import os
import subprocess
import sys
import time
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
TESTS = [
    "tests/unit/test_demo_mode_advanced.py::TestDemoModeThreadSafety::test_reset_functionality",
    "tests/unit/test_demo_mode_advanced.py::TestDemoModeDataGeneration::test_metrics_consistency",
    "tests/unit/test_demo_mode_advanced.py::TestDemoModeDataGeneration::test_cascade_unit_addition",
    "tests/unit/test_websocket_manager_unit.py::TestWebSocketManagerUnit::test_broadcast_sync_with_event_loop",
    "tests/unit/test_websocket_manager_unit.py::TestWebSocketManagerUnit::test_broadcast_from_thread",
    "tests/integration/test_mvp_functionality.py::TestDemoMode::test_metrics_generation",
]

# name -> (file relative to src/, anchor, replacement, tests that MUST fail)
MUTATIONS = {
    "M1 the loop never installs the best candidate": (
        "demo_mode.py",
        "                self.network.install_candidate(best_unit)\n",
        "                pass  # MUTATION: install skipped\n",
        ["test_cascade_unit_addition"],
    ),
    "M2 every broadcast send raises (attempted, never delivered)": (
        "communication/websocket_manager.py",
        "                await connection.send_json(message)\n            except Exception as e:\n                self.logger.warning(f\"Failed to broadcast to client: {e}\")",
        "                raise RuntimeError(\"MUTATION: send failed\")\n            except Exception as e:\n                self.logger.warning(f\"Failed to broadcast to client: {e}\")",
        ["test_broadcast_sync_with_event_loop", "test_broadcast_from_thread"],
    ),
    "M3 the demo never records a metrics sample": (
        "demo_mode.py",
        "            self.metrics_history.append(metrics)\n",
        "            pass  # MUTATION: metrics not recorded\n",
        ["test_reset_functionality", "test_metrics_consistency", "test_metrics_generation"],
    ),
}


def _burn(seconds):
    end = time.monotonic() + seconds
    x = 0
    while time.monotonic() < end:
        x = (x * 1103515245 + 12345) % 2147483648


def run(src, tests):
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="")
    proc = subprocess.run([PYTHON, "-m", "pytest", *tests, "-p", "no:cacheprovider", "-rA"], cwd=src, env=env, capture_output=True, text=True, check=False)
    failed = sorted({line.split("::")[-1].split(" ")[0] for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))})
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr.strip()[-300:]
    return proc.returncode, failed, tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("worktree")
    ap.add_argument("--repeat", type=int, default=30)
    ap.add_argument("--burn", type=int, default=0)
    ap.add_argument("--skip-mutations", action="store_true")
    args = ap.parse_args()
    src = Path(args.worktree).resolve() / "src"

    burners = [mp.Process(target=_burn, args=(3600,), daemon=True) for _ in range(args.burn)]
    for p in burners:
        p.start()
    try:
        cascade = [t for t in TESTS if t.endswith("test_cascade_unit_addition")]
        fails = 0
        t0 = time.monotonic()
        for i in range(args.repeat):
            code, failed, tail = run(src, cascade)
            if code != 0:
                fails += 1
                print(f"repeat {i}: FAIL {failed} :: {tail}", flush=True)
        print(f"REPEAT test_cascade_unit_addition: {args.repeat - fails}/{args.repeat} passed, burn={args.burn}, {time.monotonic() - t0:.1f}s total", flush=True)
    finally:
        for p in burners:
            p.terminate()

    if args.skip_mutations:
        return 0 if fails == 0 else 1

    code, failed, tail = run(src, TESTS)
    print(f"baseline: exit={code} failed={failed} :: {tail}")
    if code != 0:
        print("baseline not green; refusing to judge mutations")
        return 2

    survivors = []
    for name, (rel, anchor, replacement, must_fail) in MUTATIONS.items():
        target = src / rel
        original = target.read_bytes()
        text = original.decode()
        if text.count(anchor) != 1:
            print(f"{name}: anchor found {text.count(anchor)} times, expected 1 -- REFUSING")
            return 2
        try:
            target.write_text(text.replace(anchor, replacement))
            code, failed, tail = run(src, TESTS)
        finally:
            target.write_bytes(original)
        assert target.read_bytes() == original, f"restore failed for {rel}"
        missed = [t for t in must_fail if t not in failed]
        verdict = "KILLED" if not missed else f"SURVIVED by {missed}"
        if missed:
            survivors.append(name)
        print(f"{name}: {verdict} (failed={failed}) :: {tail}")

    print(f"restored byte-for-byte; survivors: {survivors or 'none'}")
    return 1 if (survivors or fails) else 0


if __name__ == "__main__":
    sys.exit(main())
