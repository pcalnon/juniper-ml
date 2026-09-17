#!/usr/bin/env python3
"""Does the spend-guard test actually fail against a build WITHOUT the guard?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-16
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     tests/test_soak_ledger.py::test_an_invalidate_that_would_reopen_spending_is_refused

Why
---
Three consensus rounds in this arc have found controls that could not fail -- including one I
labelled "THE NEGATIVE CONTROL" which passed against both the fixed and the unfixed build. A
test that asserts a refusal is worthless unless the un-guarded build actually refuses nothing.

This copies util/soak_ledger.py to a scratch dir, removes ONLY the guard block, and runs the
same CLI invocation the test runs against both builds. Touches no real file.
"""

from __future__ import annotations

import json
import pathlib
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "util" / "soak_ledger.py"
GUARD_ANCHOR = 'if before["verdict"] != "IN-PROGRESS" and after["verdict"] == "IN-PROGRESS":'


def build_unguarded(dst: pathlib.Path) -> pathlib.Path:
    src = SRC.read_text(encoding="utf-8")
    if GUARD_ANCHOR not in src:
        raise SystemExit("REFUSING: guard anchor not found; the source has drifted")
    # Flip the condition to something that can never hold -> guard present but inert.
    out = src.replace(GUARD_ANCHOR, 'if False and before["verdict"] == "\\x00":')
    p = dst / "soak_ledger_unguarded.py"
    p.write_text(out, encoding="utf-8")
    return p


def make_ledger(dst: pathlib.Path, mod) -> tuple[pathlib.Path, str]:
    """A ledger sitting exactly at the distinct-probe floor, with one lone-run probe."""
    rows, i = [], 0
    for k in range(mod.MIN_DISTINCT_PROBES):
        rows.append({"obs_id": f"o{i}", "kind": "observation", "arm": "seeded",
                     "in_scope": True, "probe_id": f"P{k:02d}-x", "outcome": "follow",
                     "session": f"s{i}", "ts": "2026-01-01T00:00:00Z"})
        i += 1
    for k in range(mod.TARGET_PROBE_RUNS):
        rows.append({"obs_id": f"o{i}", "kind": "observation", "arm": "seeded",
                     "in_scope": True, "probe_id": "P00-x", "outcome": "follow",
                     "session": f"p{i}", "ts": "2026-01-01T00:00:00Z"})
        i += 1
    lone = f"o{mod.MIN_DISTINCT_PROBES - 1}"
    p = dst / "l.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p, lone


def run(module: pathlib.Path, ledger: pathlib.Path, obs_id: str, *extra: str):
    return subprocess.run(  # nosec B603
        [sys.executable, str(module), "--ledger", str(ledger), "invalidate",
         "--obs-id", obs_id, "--reason", "test", "--dry-run", *extra],
        capture_output=True, text=True,
    )


def main() -> int:
    import importlib.util
    spec = importlib.util.spec_from_file_location("sl_real", SRC)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sl_real"] = mod
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)
        ledger, lone = make_ledger(d, mod)
        unguarded = build_unguarded(d)

        guarded_rc = run(SRC, ledger, lone).returncode
        forced_rc = run(SRC, ledger, lone, "--force").returncode
        unguarded_rc = run(unguarded, ledger, lone).returncode

        print(f"  guarded build, no --force : rc={guarded_rc}   (test asserts NON-ZERO)")
        print(f"  guarded build, --force    : rc={forced_rc}   (test asserts 0)")
        print(f"  UNGUARDED build           : rc={unguarded_rc}   <- if this is 0, the test")
        print("                                        discriminates; if non-zero it does not")
        print()
        ok = guarded_rc != 0 and forced_rc == 0 and unguarded_rc == 0
        print("VERDICT:", "the test DISCRIMINATES" if ok
              else "*** the test does NOT discriminate -- it would pass either way ***")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
