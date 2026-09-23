#!/usr/bin/env python
"""Mutation-check the F-CANOPY-054 fix's tests: each mutation must turn at least one test red.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy fix/f054-replay-block-clientside; ledger Phase 8 (F-CANOPY-054)

Applies one textual mutation at a time to ``src/frontend/components/metrics_panel.py`` in the given
canopy checkout, runs the two replay test files, records whether they FAILED, and restores the file
byte-for-byte (verified by sha256 at the end, and in a ``finally``). Bytecode is disabled and the
module's ``__pycache__`` entries are removed before every run: a same-size edit inside the same
second can otherwise be served from a stale ``.pyc`` (the arc's mutation-check trap).

A mutation whose search text is absent is reported NOT-APPLIED, never as caught.

WHICH TEST CAUGHT IT MATTERS. ``TestSourceBackstop`` pins source TEXT so that something runs where
node does not; a mutation that deletes pinned text fails it whatever the behaviour. The first v2
runs used ``-x`` and scored four mutations on the backstop alone, which says the text is pinned,
not that any behaviour is tested. So by default every test runs and the verdict is split:
  CAUGHT-BY-BEHAVIOUR   at least one failing test outside ``TestSourceBackstop``;
  CAUGHT-BY-BACKSTOP    only backstop tests failed -- the behaviour is UNPINNED;
  CAUGHT-BY-ERROR       a non-zero exit with no FAILED line (collection or import error);
  SURVIVED              nothing failed.
``--fail-fast`` restores the old ``-x`` scoring (CAUGHT / SURVIVED), for reproducing those runs.

Usage:
    python3 util/ad-hoc/2026-09-23_f054_mutation_check.py --canopy <worktree> \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_mutation_check.json
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
TESTS = ["tests/unit/frontend/test_f048_replay_cycle.py", "tests/unit/frontend/test_f054_replay_block_clientside.py"]

MUTATIONS = [
    ("play-does-not-record-tick_n", 'if (state.mode === "playing") { state.tick_n = tickN; }', "/* mutated */"),
    ("tick-advances-one-not-the-delta", "var next = state.current_index + steps;", "var next = state.current_index + 1;"),
    ("tick-ignores-mode (the F-054 core)", 'if (state.mode !== "playing") { continue; }', "/* mutated */"),
    ("end-leaves-interval-running", "return [state, disabled, noUpdate, sliderOut, noUpdate, position, label];", "return [state, false, noUpdate, sliderOut, noUpdate, position, label];"),
    ("stray-tick-rewrites-state", "return [noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate];", "return [state, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate];"),
    ("label-glyphs-swapped", 'var label = (state.mode === "playing") ? "\\\\u23f8" : "\\\\u25b6";', 'var label = (state.mode === "playing") ? "\\\\u25b6" : "\\\\u23f8";'),
    (
        "metrics-store-as-input",
        '                Input(f"{self.component_id}-replay-interval", "n_intervals"),\n            ],\n            [\n                State(f"{self.component_id}-replay-state", "data"),\n                State(f"{self.component_id}-metrics-store", "data"),\n            ],',
        '                Input(f"{self.component_id}-replay-interval", "n_intervals"),\n                Input(f"{self.component_id}-metrics-store", "data"),\n            ],\n            [\n                State(f"{self.component_id}-replay-state", "data"),\n            ],',
    ),
    ("refill-callback-removed", "        app.clientside_callback(\n            REPLAY_REFILL_POSITION_JS,", "        (lambda *a, **k: None)(\n            REPLAY_REFILL_POSITION_JS,"),
    ("state-input-not-copied", "var state = currentState ? Object.assign({}, currentState) :", "var state = currentState ? currentState :"),
]

# v2: the round-1 corrections -- events from values (``clicks``, ``slider_w``), the NaN guard, and
# the refill writing the max alone. The v1 mutations whose target text survived are kept; the
# return-array ones are re-spelled for the eight outputs.
MUTATIONS_V2 = [
    ("play-does-not-record-tick_n", 'if (state.mode === "playing") { state.tick_n = tickN; }', "/* mutated */"),
    ("tick-advances-one-not-the-delta", "var next = state.current_index + steps;", "var next = state.current_index + 1;"),
    ("tick-ignores-mode (the F-054 core)", 'if (state.mode !== "playing") { continue; }', "/* mutated */"),
    ("end-leaves-interval-running", "return [state, disabled, noUpdate, sliderOut, noUpdate, String(idx), String(maxIndex), label];", "return [state, false, noUpdate, sliderOut, noUpdate, String(idx), String(maxIndex), label];"),
    ("stray-tick-rewrites-state", "return [noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate];", "return [state, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate];"),
    ("label-glyphs-swapped", 'var label = (state.mode === "playing") ? "\\\\u23f8" : "\\\\u25b6";', 'var label = (state.mode === "playing") ? "\\\\u25b6" : "\\\\u23f8";'),
    MUTATIONS[6],  # metrics-store-as-input
    MUTATIONS[7],  # refill-callback-removed
    MUTATIONS[8],  # state-input-not-copied
    ("lost-events-dropped (round-1 defect 1)", "order = lost.concat(order);", "order = order;"),
    ("lost-events-after-the-triggers", "order = lost.concat(order);", "order = order.concat(lost);"),
    ("clicks-not-recorded", "state.clicks = seen;", "/* mutated */"),
    ("slider_w-not-recorded", "state.slider_w = sliderOut;", "/* mutated */"),
    ("NaN-is-a-seek (round-1 defect 2)", 'var sliderOk = (typeof sliderValue === "number") && isFinite(sliderValue);', 'var sliderOk = (typeof sliderValue === "number");'),
    ("triggered-button-not-applied-at-least-once", "Math.max(pending[ev], inTriggers[ev] ? 1 : 0)", "pending[ev]"),
    ("recreated-button-not-reset", "if (n < s) { s = 0; }", "/* mutated */"),
    ("play-toggles-by-parity", 'state.mode = (state.mode === "playing") ? "paused" : "playing";', 'if (times % 2 === 1) { state.mode = (state.mode === "playing") ? "paused" : "playing"; }'),
    ("refill-writes-the-index (round-1 defect 3)", 'Output(f"{self.component_id}-replay-position-max", "children", allow_duplicate=True),', 'Output(f"{self.component_id}-replay-position-index", "children", allow_duplicate=True),'),
]


# v3: round 2's corrections (Lane B2). A button applies exactly its pending count and a trigger only orders
# it (v2's "count OR trigger" applied one click twice: D1 undid a pause, D2 stepped two rows); a slider
# trigger carrying the value this callback last wrote is not a seek (D3); and a run whose events all had
# nothing to do writes nothing. v2's "at least once" mutation has no target any more, so it is replaced by
# its inverse: re-introducing v2's rule must be caught.
_V3_BUTTON_OLD = '        } else if (pending[ev] <= 0) {\n            continue;\n        }\n        var times = (ev === "replay-slider") ? 1 : pending[ev];'
_V3_BUTTON_NEW = '        }\n        var times = (ev === "replay-slider") ? 1 : Math.max(pending[ev], inTriggers[ev] ? 1 : 0);'
MUTATIONS_V3 = [m for m in MUTATIONS_V2 if m[0] != "triggered-button-not-applied-at-least-once"] + [
    ("count-or-trigger-restored (round-2 D1/D2)", _V3_BUTTON_OLD, _V3_BUTTON_NEW),
    ("the-sliders-own-value-is-a-seek (round-2 D3)", '            if (typeof state.slider_w === "number" && sliderValue === state.slider_w) { continue; }\n', ""),
    ("a-no-op-run-re-renders", "    if (order.length > 0 && !controlFired && !ticked && !sliderReset) {", "    if (false) {"),
]


def _run_tests(src: Path, fail_fast: bool) -> tuple:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", LIBTORCH="", LD_LIBRARY_PATH="")
    for pyc in (src / "frontend" / "components" / "__pycache__").glob("metrics_panel*.pyc"):
        pyc.unlink()
    cmd = [PY, "-m", "pytest", *TESTS, "-q", "-p", "no:cacheprovider", "--no-header", "-rf"] + (["-x"] if fail_fast else [])
    proc = subprocess.run(cmd, cwd=src, env=env, capture_output=True, text=True, timeout=1800, check=False)
    tail = [ln for ln in proc.stdout.splitlines() if ln.startswith(("FAILED", "ERROR")) or "Error" in ln][:3]
    failed = sorted({ln.split(" ", 1)[1].split(" - ", 1)[0] for ln in proc.stdout.splitlines() if ln.startswith("FAILED ")})
    return proc.returncode, tail, failed


def _verdict(code: int, failed: list, fail_fast: bool) -> str:
    if code == 0:
        return "SURVIVED"
    if fail_fast:
        return "CAUGHT"
    if not failed:
        return "CAUGHT-BY-ERROR"
    return "CAUGHT-BY-BEHAVIOUR" if any("TestSourceBackstop" not in t for t in failed) else "CAUGHT-BY-BACKSTOP"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canopy", required=True, help="canopy checkout holding the fix")
    ap.add_argument("--set", choices=("v1", "v2", "v3"), default="v1", help="v1 = canopy#670 as opened (c0530279); v2 = after the round-1 corrections (85415f3c); v3 = after round 2's")
    ap.add_argument("--fail-fast", action="store_true", help="pytest -x and CAUGHT/SURVIVED only (the scoring of the first runs)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    mutations = {"v1": MUTATIONS, "v2": MUTATIONS_V2, "v3": MUTATIONS_V3}[args.set]

    src = Path(args.canopy) / "src"
    target = src / "frontend" / "components" / "metrics_panel.py"
    original = target.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    results = {"target": str(target), "set": args.set, "fail_fast": args.fail_fast, "sha256": digest, "baseline": None, "mutations": []}
    try:
        code, tail, failed = _run_tests(src, args.fail_fast)
        results["baseline"] = {"exit": code, "tail": tail, "failed": failed}
        print(f"baseline: exit {code}", flush=True)
        if code != 0:
            print("baseline is red -- refusing to score mutations", flush=True)
            return 2
        text = original.decode("utf-8")
        for name, old, new in mutations:
            if text.count(old) != 1:
                results["mutations"].append({"name": name, "verdict": "NOT-APPLIED", "occurrences": text.count(old)})
                print(f"  {name:40s} NOT-APPLIED (search text occurs {text.count(old)}x)", flush=True)
                continue
            target.write_text(text.replace(old, new), encoding="utf-8")
            code, tail, failed = _run_tests(src, args.fail_fast)
            target.write_bytes(original)
            verdict = _verdict(code, failed, args.fail_fast)
            results["mutations"].append({"name": name, "verdict": verdict, "exit": code, "tail": tail, "failed_tests": failed})
            print(f"  {name:40s} {verdict} (exit {code}; {len(failed)} failed) {tail[:1]}", flush=True)
    finally:
        target.write_bytes(original)
    restored = hashlib.sha256(target.read_bytes()).hexdigest() == digest
    results["restored"] = restored
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"restored byte-for-byte: {restored}; results -> {args.out}", flush=True)
    return 0 if restored else 3


if __name__ == "__main__":
    sys.exit(main())
