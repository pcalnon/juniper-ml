#!/usr/bin/env python3
"""
Run the orchestrator's last screens over a frozen landing snapshot's Python files before a signed push: parse, the
CodeQL prescreen, the unused-global check, the home-path gate, a system-temp-literal grep and the unmodelled CodeQL
shapes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 5: landing the validated carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_land_snapshot.py (writes <freeze>/snapshot),
         util/ad-hoc/2026-10-05_codeql_python_prescreen.py, util/ad-hoc/2026-11-09_flood4r2_land_unused_globals.py,
         util/home_path_literal_check.py, tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt (the seven CodeQL shapes)

Usage:
  2026-11-12_flood4r2_s5_snapshot_gate.py <freeze dir> [--allow-prescreen <substring> ...]

Run from the juniper-ml checkout that holds the three tools above. For every ``*.py`` under <freeze>/snapshot it:
  * parses the file (``ast.parse``; nothing is compiled, so no ``__pycache__`` appears in the snapshot);
  * runs the CodeQL prescreen and the unused-global check, and prints each prediction. A prediction line containing an
    ``--allow-prescreen`` substring is listed but not counted (the standing case: a module-level ``pytestmark``,
    which CodeQL has never flagged in these repositories);
  * for a file under ``util/``, reports a home-directory literal (``/home/<name>`` or ``/Users/<name>``). The
    repository's own gate, util/home_path_literal_check.py, is NOT used here: handed a path outside the repository it
    reports "0 files" and passes, which would be a vacuous pass on a snapshot;
  * reports any line that names the system temp directory as a path literal, and any of four shapes the prescreen
    does not model: ``except BaseException``, a bare ``except:``, a bare ``await <name>`` statement, and ``if True:``
    / ``if False:`` (``while True:`` is the ordinary infinite loop and is not a finding).
A line-shape hit whose stripped text also occurs in main's copy of the same file (<freeze>/main/<path>) is listed as
pre-existing and not counted: CodeQL comments only on lines a pull request changes.
It reads the freeze and writes nothing. Exit 0 = nothing counted; 1 = at least one counted hit (each is printed).
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

PRESCREEN = "util/ad-hoc/2026-10-05_codeql_python_prescreen.py"
UNUSED_GLOBALS = "util/ad-hoc/2026-11-09_flood4r2_land_unused_globals.py"
TEMP_LITERAL = re.compile(r"""(?:^|[\s"'=(,\[])/(?:var/)?tmp(?:/|["'\s)\],]|$)""")
HOME_LITERAL = re.compile(r"""/(?:home|Users)/[A-Za-z0-9_.-]+""")
SHAPES = {
    "except BaseException": re.compile(r"^\s*except\s+BaseException\b"),
    "bare except": re.compile(r"^\s*except\s*:\s*(#.*)?$"),
    "bare await of a name": re.compile(r"^\s+await\s+[A-Za-z_][A-Za-z_0-9]*\s*(#.*)?$"),
    "constant conditional": re.compile(r"^\s*(if|elif)\s+(True|False)\s*:"),
}


def run(tool: str, files: list[str]) -> list[str]:
    done = subprocess.run([sys.executable, tool, *files], capture_output=True, text=True, check=False)
    return [line for line in (done.stdout + done.stderr).splitlines() if line.strip()]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    snapshot = Path(argv[1]) / "snapshot"
    allowed = [argv[index + 1] for index, word in enumerate(argv[:-1]) if word == "--allow-prescreen"]
    files = sorted(snapshot.rglob("*.py"))
    counted = 0
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            counted += 1
            print(f"SYNTAX  {path.relative_to(snapshot)}: {exc}")
    names = [str(path) for path in files]
    if names:
        for tool, label in ((PRESCREEN, "prescreen"), (UNUSED_GLOBALS, "unused-global")):
            for line in run(tool, names):
                if ".py" not in line or "predicted alert(s)" in line or "unused global(s)" in line:
                    continue
                shown = line.replace(str(snapshot) + "/", "")
                if any(text in line for text in allowed):
                    print(f"allowed {label}: {shown[:200]}")
                else:
                    counted += 1
                    print(f"COUNTED {label}: {shown[:200]}")
    pre_existing = 0
    for path in files:
        rel = path.relative_to(snapshot)
        main_copy = Path(argv[1]) / "main" / rel
        on_main = {line.strip() for line in main_copy.read_text(encoding="utf-8").splitlines()} if main_copy.is_file() else set()
        in_util = rel.parts[0] == "util"
        for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            hits = [label for label, pattern in SHAPES.items() if pattern.search(text)]
            if TEMP_LITERAL.search(text):
                hits.append("temp literal")
            if in_util and HOME_LITERAL.search(text):
                hits.append("home-directory literal")
            for label in hits:
                if text.strip() in on_main:
                    pre_existing += 1
                    print(f"pre-existing on main, not counted ({label}): {rel}:{number}: {text.strip()[:120]}")
                else:
                    counted += 1
                    print(f"COUNTED {label}: {rel}:{number}: {text.strip()[:140]}")
    print(f"python files: {len(files)}  counted hits: {counted}  pre-existing: {pre_existing}")
    return 1 if counted else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
