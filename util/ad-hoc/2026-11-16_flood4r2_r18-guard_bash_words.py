#!/usr/bin/env python3
"""
Print the words bash builds from shell words, printf only, in a scratch home: the bash side of the guard's word checks.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py (gap 12 of its docstring); util/ad-hoc/2026-11-16_flood4r2_r18-guard_probe.py.

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_bash_words.py <scratch dir> <items.json> <out.json>

<items.json> is a JSON list. A string item is a shell WORD as typed (no unquoted whitespace or metacharacter): bash
runs ``ulimit -v 409600; ulimit -t 3; set -f; printf '%s\\037' WORD`` and the output is the list of words it printed.
An item {"script": "..."} runs that script as written: every script in this arc's item files prints with printf
(a marker such as ``printf N-RAN``) or with ``:`` and nothing else. bash runs as ``bash --norc --noprofile -c``
with HOME the scratch home under <scratch dir>, PATH an EMPTY directory under <scratch dir> (so only builtins run),
cwd the scratch home's ``work`` directory, LC_ALL=C and a 10 s timeout, at most 4 at a time. Output names the scratch
home ``<home>``. ``bash_words`` is the function the differential calls.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 -- printf-only bash probes in a scratch home with an empty PATH
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SEP = "\x1f"


def scratch_dirs(scratch: Path) -> tuple:
    home = scratch / "home"
    empty_path = scratch / "empty-path"
    for path in (home / "work", empty_path):
        path.mkdir(parents=True, exist_ok=True)
    return home, empty_path


def run_one(item, home: Path, empty_path: Path) -> dict:
    if isinstance(item, dict):
        script = "ulimit -v 409600; ulimit -t 3; " + item["script"]
    else:
        script = "ulimit -v 409600; ulimit -t 3; set -f; printf '%s\\037' " + item
    env = {"HOME": str(home), "PATH": str(empty_path), "LC_ALL": "C"}
    try:
        proc = subprocess.run(["/bin/bash", "--norc", "--noprofile", "-c", script], env=env, cwd=str(home / "work"), capture_output=True, text=True, timeout=10, check=False)  # nosec B603 -- printf-only probe
    except subprocess.TimeoutExpired:
        return {"exit": "timeout", "words": [], "stderr": ""}
    out = proc.stdout.replace(str(home), "<home>")
    words = out.split(SEP)[:-1] if not isinstance(item, dict) else out.splitlines()
    return {"exit": proc.returncode, "words": words, "stderr": proc.stderr.replace(str(home), "<home>").strip()[:200]}


def bash_words(items: list, scratch: Path, workers: int = 4) -> list:
    home, empty_path = scratch_dirs(scratch)
    with ThreadPoolExecutor(max_workers=max(1, min(4, workers))) as pool:
        return list(pool.map(lambda item: run_one(item, home, empty_path), items))


def main(argv: list) -> int:
    scratch = Path(argv[1]).resolve()
    items = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    results = bash_words(items, scratch)
    rows = [{"item": item, **result} for item, result in zip(items, results)]
    Path(argv[3]).write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        label = row["item"]["script"] if isinstance(row["item"], dict) else row["item"]
        print("%-40r exit=%s words=%r%s" % (label, row["exit"], row["words"], ("  stderr=" + row["stderr"][:90]) if row["stderr"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
