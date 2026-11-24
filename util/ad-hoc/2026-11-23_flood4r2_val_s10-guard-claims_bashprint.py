#!/usr/bin/env python3
"""
Print, with bash 5.3's printf only, the words bash builds from the spellings the agent guard 1.4.0 leaves open.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- read-only validation (claims lens on the agent guard 1.4.0 texts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py (gap 12 of its docstring)

Usage:
    python3 -I 2026-11-23_flood4r2_val_s10-guard-claims_bashprint.py <out.json> <scratch home>

Probe hygiene: each probe is ``printf '%s\\n' <word>`` (with, for some, a plain assignment before it), run as
``bash --norc --noprofile -c`` with HOME set to <scratch home> (an empty directory, never a real home),
PATH=/usr/bin:/bin, ``ulimit -t 5`` and a 10 s timeout. A substitution in a word runs only printf or echo, which
print. Nothing is read, written or executed beyond printing; the printed paths are not opened.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 -- printf-only bash probes in a scratch home
import sys
from pathlib import Path

PROBES = [
    ("W01", "", "/x/$(printf %s .s sh)/config"),
    ("W03", "", "~/.config/$(printf %s gi t)/config"),
    ("W04", "", ".git/$(printf %s hoo ks)/post-commit"),
    ("W05", "d=hooks; ", ".git/$d/post-commit"),
    ("W09", "d=ssh; ", "/x/.$d/config"),
    ("O11", "d=git; ", "~/.config/$d/config"),
    ("O14", "", 'd"`echo "{o,Q}"`"as'),
    ("O15", "", "s\"${x$':'-\"{u,Q}\"}\""),
    ("V05", "", '--inpu"`echo "{t,Q}"`"'),
]


def main(argv: list) -> int:
    out, home = Path(argv[1]), Path(argv[2]).resolve()
    work = home / "work"
    work.mkdir(parents=True, exist_ok=True)
    rows = []
    for case_id, prefix, word in PROBES:
        script = "ulimit -t 5; " + prefix + "printf '%s\\n' " + word
        proc = subprocess.run(["bash", "--norc", "--noprofile", "-c", script], env={"HOME": str(home), "PATH": "/usr/bin:/bin", "LC_ALL": "C"}, cwd=str(work), capture_output=True, text=True, timeout=10, check=False)  # nosec B603 B607
        lines = [line.replace(str(home), "<home>") for line in proc.stdout.splitlines()]
        rows.append({"id": case_id, "probe": prefix + "printf '%s\\n' " + word, "exit": proc.returncode, "printed": lines, "stderr": proc.stderr.replace(str(home), "<home>")[-200:]})
        print("%-4s exit=%d printed=%s" % (case_id, proc.returncode, lines))
    version = subprocess.run(["bash", "--version"], capture_output=True, text=True, check=False).stdout.splitlines()[0]  # nosec B603 B607
    out.write_text(json.dumps({"bash": version, "rows": rows}, indent=1) + "\n", encoding="utf-8")
    print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
