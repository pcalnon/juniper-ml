"""
Landing-order rehearsal for the D-14 pair: what juniper-ml's drift gate answers in each state the two landings can leave.

Runs ``tests/test_ws_resume_answer_table_drift.py`` from a synthetic ecosystem root (``--eco``: ``juniper-ml/`` holding
the gate and juniper-ml's copy of the table, ``juniper-cascor/`` holding cascor's copy), as the weekly
``docs-full-check`` job lays the checkouts out:

  both-landed             cascor's copy present and identical           expected: OK
  ml-first, forced local  cascor's checkout present, its copy absent    expected: FAILED, naming the absent copy
  ml-first, as Actions    the same, with GITHUB_ACTIONS=true             expected: FAILED, naming the absent copy
  per-PR, no gating       neither variable set (a developer's default)  expected: OK, the comparison skipped

cascor's copy is moved aside for the two "ml-first" runs and moved back in ``finally:``; its sha256 is checked
after. (Per-PR CI clones no sibling at all; that case is the gate's own ``test_no_sibling_checkout_skips``, which
runs in every invocation here too.) Writes one log per run and ``landing_order.json``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
CASCOR_COPY = "juniper-cascor/src/tests/fixtures/ws_resume_answers.json"
GATING = ("GITHUB_ACTIONS", "JUNIPER_DRIFT_TEST_FORCE_LOCAL")


def run_gate(eco: Path, gating: dict, log: Path) -> dict:
    env = {key: value for key, value in os.environ.items() if key not in GATING}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    env.update(gating)
    done = subprocess.run(["/opt/miniforge3/envs/JuniperCascor1/bin/python3.14", "-m", "unittest", "-v", "tests/test_ws_resume_answer_table_drift.py"], cwd=eco / "juniper-ml", env=env, capture_output=True, text=True, check=False)
    text = done.stdout + done.stderr
    log.write_text(text, encoding="utf-8")
    last = [line for line in text.splitlines() if line.startswith(("OK", "FAILED"))]
    return {"gating": gating, "exit": done.returncode, "summary": last[-1] if last else "", "names_the_absent_copy": "does not exist" in text, "log": str(log)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--eco", type=Path, required=True)
    parser.add_argument("--log-dir", type=Path, required=True)
    args = parser.parse_args()
    copy = args.eco / CASCOR_COPY
    held = args.eco / "ws_resume_answers.json.held"
    digest = hashlib.sha256(copy.read_bytes()).hexdigest()
    results = {"both-landed": run_gate(args.eco, {"JUNIPER_DRIFT_TEST_FORCE_LOCAL": "1"}, args.log_dir / "landing_both_landed.log")}
    results["per-PR, no gating"] = run_gate(args.eco, {}, args.log_dir / "landing_no_gating.log")
    copy.rename(held)
    try:
        results["ml-first, forced local"] = run_gate(args.eco, {"JUNIPER_DRIFT_TEST_FORCE_LOCAL": "1"}, args.log_dir / "landing_ml_first_local.log")
        results["ml-first, as Actions"] = run_gate(args.eco, {"GITHUB_ACTIONS": "true"}, args.log_dir / "landing_ml_first_actions.log")
    finally:
        held.rename(copy)
    restored = hashlib.sha256(copy.read_bytes()).hexdigest() == digest
    with open(args.log_dir / "landing_order.json", "w", encoding="utf-8") as handle:
        json.dump({"results": results, "cascor_copy_restored": restored}, handle, indent=1)
        handle.write("\n")
    for name, result in results.items():
        print(f"{name}: exit {result['exit']}, {result['summary']}, names the absent copy: {result['names_the_absent_copy']}")
    print(f"cascor copy restored byte-identical: {restored}")


if __name__ == "__main__":
    main()
