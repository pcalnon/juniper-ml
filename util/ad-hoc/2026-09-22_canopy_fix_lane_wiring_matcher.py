#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_fix_lane_wiring_matcher.py
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- migration
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#650
#
# Description:
#    juniper-canopy#650 follow-up: `test_ci_lane_wiring._installs_extra` tests bracket EQUALITY
#    where it means MEMBERSHIP.
#
#        re.search(rf"pip\\s+install\\b[^\\n]*\\[{re.escape(EXTRA)}\\]", line)
#
#    That matches `pip install -e ".[juniper-cascor]"` and nothing else. #650 changes the lanes to
#    `.[test,juniper-cascor,observability]` -- every lane still installs the extra, which is all the
#    guard is there to enforce -- and the assertion fires anyway, naming ci.yml and
#    scheduled-tests.yml as offenders. The guard is right about intent and wrong about syntax, and
#    it would reject any future multi-extra lane for the same reason.
#
#    This rewrites the matcher to parse the bracketed extras list and test token membership, and
#    refreshes the two docstring lines that still describe the pre-#650 install shapes.
#
#    Patches the file as it exists ON THE BRANCH, not from the local canopy checkout, which is
#    behind origin/main.
#
#    Usage:  python3 util/ad-hoc/2026-09-22_canopy_fix_lane_wiring_matcher.py <out-dir>
#####################################################################################################################################################################################################

from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

REPO = "pcalnon/juniper-canopy"
BRANCH = "fix/ci-install-from-pyproject-extras"
TARGET = "src/tests/regression/test_ci_lane_wiring.py"

OLD_FUNC = '''def _installs_extra(shell: str) -> bool:
    """True iff some ``pip install`` COMMAND (not a comment) requests the extra."""
    return any(re.search(rf"pip\\s+install\\b[^\\n]*\\[{re.escape(EXTRA)}\\]", line) for line in shell.splitlines())'''

NEW_FUNC = '''def _installs_extra(shell: str) -> bool:
    """True iff some ``pip install`` COMMAND (not a comment) requests the extra.

    MEMBERSHIP in the bracketed extras list, not equality with it. The original pattern was
    ``\\\\[juniper-cascor\\\\]`` -- the extra had to be the WHOLE bracket -- so a lane installing
    ``.[test,juniper-cascor,observability]`` read as not installing it at all. That is what this
    guard reported against canopy#650, where every lane did install the extra, and it would have
    rejected any future multi-extra lane the same way. The guard's subject is whether the real
    client reaches the lane, not how many extras share the brackets.
    """
    for line in shell.splitlines():
        if not re.search(r"pip\\s+install\\b", line):
            continue
        for match in re.finditer(r"\\[([^\\]]*)\\]", line):
            if EXTRA in [part.strip() for part in match.group(1).split(",")]:
                return True
    return False'''

OLD_DOC = '''* ``.github/workflows/ci.yml``              -- ``pip install -e ".[juniper-cascor]"``  (real client)
* ``.github/workflows/scheduled-tests.yml`` -- ``pip install -e .``                    (stub)'''

NEW_DOC = '''* ``.github/workflows/ci.yml``              -- ``pip install -e ".[juniper-cascor]"``  (real client)
* ``.github/workflows/scheduled-tests.yml`` -- ``pip install -e .``                    (stub)

Both lanes now install several extras at once
(``.[test,juniper-cascor,observability]``, canopy#650), so the check below is membership in the
bracketed list rather than a match against the whole bracket.'''


def fetch(path: str) -> str:
    r = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{path}?ref={BRANCH}", "--jq", ".content"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise SystemExit(f"fetch {path} failed: {r.stderr.strip()}")
    return base64.b64decode(r.stdout).decode("utf-8")


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)

    text = fetch(TARGET)
    for old, new, what in ((OLD_FUNC, NEW_FUNC, "matcher"), (OLD_DOC, NEW_DOC, "docstring")):
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"ABORT: {what}: expected 1 occurrence, found {n}")
        text = text.replace(old, new)

    dst = out / TARGET
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    print(f"patched {TARGET}")

    # Self-check: the new matcher must accept the new shape and still reject a bare `pip install -e .`
    ns: dict = {}
    exec(compile(NEW_FUNC.replace("EXTRA", '"juniper-cascor"'), "<new_func>", "exec"),
         {"re": __import__("re")}, ns)
    fn = ns["_installs_extra"]
    cases = [
        ('pip install -e ".[test,juniper-cascor,observability]"', True),
        ('pip install -e ".[juniper-cascor]"', True),
        ('pip install -e ".[test,ui-test,observability]"', False),
        ("pip install -e .", False),
        ('pip install -e ".[juniper-data,juniper-cascor,observability]"', True),
    ]
    print("\nself-check:")
    ok = True
    for shell, expected in cases:
        got = fn(shell)
        flag = "ok " if got == expected else "BAD"
        if got != expected:
            ok = False
        print(f"  {flag} {got!s:5} (want {expected!s:5})  {shell}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
