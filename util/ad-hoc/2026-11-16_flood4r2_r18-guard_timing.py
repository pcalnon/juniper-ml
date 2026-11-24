#!/usr/bin/env python3
"""
Time the agent guard as the hook runs, on adversarial words aimed at the 1.4.0 reading (bash's own word structure).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_timing.py (the 1.3.0 carrier's shapes, aimed at brace_expand);
         util/claude_agent_guard.py 1.4.0 (_comsub_close, _param_close, _brace_mask, bash_brace_expand).

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_timing.py <out.json> <label>=<guard.py> [...]

Each shape is grown to n = 2000 and wrapped as ``echo <word>`` and as ``cat ~/X/../<word>``; each guard runs as the
hook does (``python3 -I <guard.py>``, the payload on stdin, ``JUNIPER_GUARD_HOME`` a directory that does not
exist), one child at a time, with a 20 s timeout. The hook's own timeout is 10 s. Recorded: wall seconds, exit code
and whether stdout held a deny. Nothing else is read or run.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 -- runs guard copies on JSON payloads
import sys
import time
from pathlib import Path

N = 2000
SHAPES = {
    "nested-comsub": lambda n: "$(" * min(n, 300) + ":" + ")" * min(n, 300),
    "comsub-chain": lambda n: "$(:)" * n,
    "heredocs-in-comsub": lambda n: "$(" + " ".join(": <<E%d" % k for k in range(n)) + "\n" + "\n".join("E%d" % k for k in range(n)) + "\n)",
    "case-in-comsub": lambda n: "$(case x in a) : ;; esac)" * n,
    "comments-in-comsub": lambda n: "$(: # )\n)" * n,
    "param-defaults-unclosed": lambda n: "${x:-{" * n,
    "param-defaults-nested": lambda n: "${x:-" * n + "}" * n,
    "escaped-braces": lambda n: "\\{a," * n + "b\\}",
    "quoted-lists": lambda n: "'{a,b}'" * n,
    "dq-backtick-quirk": lambda n: '"`echo "{h,x}"`"' * min(n, 6),
    "extglob-groups": lambda n: "@(a)" * n,
    "hop-chain": lambda n: "X/../" * n + ".ssh",
    "splices": lambda n: ".ss$(:)" * n,
    "ansi-c": lambda n: "$'\\x7d'" * n,
}


def run(guard: str, command: str) -> dict:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/nonexistent-guard-timing-cwd"})
    env = {"PATH": "/usr/bin:/bin", "JUNIPER_GUARD_HOME": "/nonexistent-guard-timing-home", "HOME": "/nonexistent-guard-timing-home", "LC_ALL": "C"}
    started = time.monotonic()
    try:
        proc = subprocess.run([sys.executable, "-I", "-B", guard], input=payload, env=env, capture_output=True, text=True, timeout=20, check=False)  # nosec B603 -- a guard copy on a payload
    except subprocess.TimeoutExpired:
        return {"seconds": 20.0, "outcome": "TIMEOUT"}
    seconds = round(time.monotonic() - started, 3)
    outcome = "exit %d%s" % (proc.returncode, " deny" if proc.stdout.strip() else "")
    return {"seconds": seconds, "outcome": outcome}


def main(argv: list) -> int:
    out = Path(argv[1])
    guards = [arg.split("=", 1) for arg in argv[2:]]
    rows = []
    for name, build in SHAPES.items():
        word = build(N)
        for wrap in ("echo %s", "cat ~/X/../%s"):
            command = wrap % word
            results = {label: run(path, command) for label, path in guards}
            rows.append({"shape": name, "wrap": wrap.split(" ")[0], "length": len(command), "results": results})
            print("%-24s %-5s %7d  %s" % (name, wrap.split(" ")[0], len(command), "  ".join("%s=%.3fs %s" % (label, r["seconds"], r["outcome"]) for label, r in results.items())))
    worst = {label: max(row["results"][label]["seconds"] for row in rows) for label, _ in guards}
    out.write_text(json.dumps({"n": N, "worst_seconds": worst, "rows": rows}, indent=1) + "\n", encoding="utf-8")
    print("worst:", worst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
