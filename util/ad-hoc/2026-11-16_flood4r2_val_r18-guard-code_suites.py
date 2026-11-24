"""
Run the agent-guard unittest suites of a juniper-ml tree under a chosen interpreter, one process per suite, with the
six Sentry variables empty and a dead session bus (validator JL1, r18-guard code lens).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (flood-4 round-2 validation, r18-guard code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tests/test_claude_agent_guard*.py

Usage: python3 <this file> <tree> <interpreter> <log> [suite ...]   (default: every tests/test_claude_agent_guard*.py)
"""

import os
import subprocess  # nosec B404 -- runs unittest on a validation worktree
import sys
import time
from pathlib import Path

SENTRY = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


def main(argv: list) -> int:
    tree = Path(argv[0]).resolve()
    interpreter = argv[1]
    log = Path(argv[2])
    suites = argv[3:] or sorted(str(p.relative_to(tree)) for p in (tree / "tests").glob("test_claude_agent_guard*.py"))
    env = dict(os.environ)
    env.update({name: "" for name in SENTRY})
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    env.pop("CLAUDE_PROJECT_DIR", None)
    lines = ["tree %s" % tree, "interpreter %s" % interpreter]
    failed = 0
    for suite in suites:
        t0 = time.perf_counter()
        proc = subprocess.run([interpreter, "-m", "unittest", suite], cwd=str(tree), env=env, capture_output=True, text=True, timeout=1500, check=False)  # nosec B603 -- unittest on a validation worktree
        tail = [ln for ln in proc.stderr.strip().splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
        status = "PASS" if proc.returncode == 0 else "FAIL"
        failed += proc.returncode != 0
        lines.append("%s %-55s %6.1fs %s" % (status, suite, time.perf_counter() - t0, " | ".join(tail)))
        if proc.returncode != 0:
            lines.append(proc.stderr[-3000:])
    lines.append("suites %d, failed %d" % (len(suites), failed))
    log.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-len(suites) - 1 :]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
