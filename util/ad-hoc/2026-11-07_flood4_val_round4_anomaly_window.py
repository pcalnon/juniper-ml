#!/usr/bin/env python3
"""Round-4 validator helper: exercise main's AnomalyDetector duplicate window.

Project: Juniper
Sub-Project: juniper-ml
Application: flood-4 docs-carrier round-4 validation (ad hoc, single use)
Author: Paul Calnon
Version: 0.1.0
License: MIT License
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 4 (findings: tmp/flood4/ml-docs/val-round4/)

Loads juniper-service-core/juniper_service_core/workers/security.py from a named commit's blob
(never from a checkout, so nothing writes a __pycache__ anywhere), registers it in sys.modules
before exec (its @dataclass needs that), and checks the REFERENCE "Duplicate window" claims:
window 0 trimming / flagging / total_results, window 1-2 never flag, and whether total_results
equals the lifetime count for a non-zero window before the window fills.

Usage: python3 -I <this> <repo_dir> <commit>
"""

from __future__ import annotations

import subprocess  # nosec B404 - fixed argv, no shell
import sys
import types


def load(repo: str, commit: str) -> types.ModuleType:
    blob = subprocess.run(["git", "-C", repo, "show", f"{commit}:juniper-service-core/juniper_service_core/workers/security.py"], check=True, capture_output=True, text=True).stdout  # nosec B603 B607
    mod = types.ModuleType("val_round4_workers_security")
    mod.__file__ = f"{commit}:workers/security.py"
    sys.modules[mod.__name__] = mod
    exec(compile(blob, mod.__file__, "exec"), mod.__dict__)  # nosec B102 - main's own source blob
    return mod


def run(mod: types.ModuleType, window: int, scores: list[float]) -> dict:
    det = mod.AnomalyDetector(duplicate_window=window)
    flags = []
    for i, s in enumerate(scores):
        res = det.check_result("w", s, 1.0, f"t{i}")
        flags.append([a.split(":")[0] for a in res])
    return {"window": window, "n_sent": len(scores), "flags_per_result": flags, "total_results": det.get_worker_stats("w")["total_results"]}


def main() -> int:
    mod = load(sys.argv[1], sys.argv[2])
    cases = [
        ("window 0, 5 identical: does the flag fire although the doc says the flag needs a window of 3 or more?", 0, [0.5] * 5),
        ("window 0, 25 mixed: total_results lifetime?", 0, [0.1 * (i % 7) + 0.05 for i in range(25)]),
        ("window 1, 6 identical: never fires?", 1, [0.5] * 6),
        ("window 2, 6 identical: never fires?", 2, [0.5] * 6),
        ("window 10 (default), 5 results: total_results == lifetime count before the window fills?", 10, [0.1, 0.2, 0.3, 0.4, 0.6]),
        ("window 10 (default), 14 results: total_results capped at 10?", 10, [0.05 * i + 0.05 for i in range(14)]),
        ("window 3 doc example 0.10, 0.50, 0.50, 0.50", 3, [0.10, 0.50, 0.50, 0.50]),
    ]
    for label, window, scores in cases:
        print(label)
        print("   ", run(mod, window, scores))
    print("unknown worker:", mod.AnomalyDetector().get_worker_stats("nobody"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
