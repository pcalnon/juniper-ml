#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_add_observability_extra.py
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
#    Incremental follow-up patch for juniper-canopy#650: add the `observability` extra to the test
#    lanes so `sentry-sdk` returns.
#
#    #650's first CI round failed on all four unit legs with `ModuleNotFoundError: No module named
#    'sentry_sdk'`. The flattened conf/requirements_ci.txt carried `sentry-sdk>=2.0.0`; the new
#    install shape did not, because canopy's source never imports sentry_sdk --
#    juniper_observability.configure_sentry imports it internally -- so neither collection nor an
#    import grep could see the need. `observability` is canopy's declared home for it.
#
#    Patches the files AS THEY EXIST ON THE BRANCH rather than re-deriving them from the local
#    canopy checkout, which is behind origin/main; rebuilding from a stale base is how a fix
#    silently reverts someone else's merged commit.
#
#    Usage:  python3 util/ad-hoc/2026-09-22_canopy_add_observability_extra.py <out-dir>
#####################################################################################################################################################################################################

from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

REPO = "pcalnon/juniper-canopy"
BRANCH = "fix/ci-install-from-pyproject-extras"

SUBS: dict[str, list[tuple[str, str, int]]] = {
    ".github/workflows/ci.yml": [
        ('pip install -e ".[test,juniper-cascor]"',
         'pip install -e ".[test,juniper-cascor,observability]"', 2),
        ('pip install -e ".[test,ui-test]"',
         'pip install -e ".[test,ui-test,observability]"', 1),
    ],
    ".github/workflows/scheduled-tests.yml": [
        ('pip install -e ".[test,juniper-cascor]"',
         'pip install -e ".[test,juniper-cascor,observability]"', 1),
    ],
}


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

    for path, rules in SUBS.items():
        text = fetch(path)
        for old, new, expected in rules:
            got = text.count(old)
            if got != expected:
                raise SystemExit(
                    f"ABORT {path}: expected {expected} occurrence(s) of {old!r}, found {got}"
                )
            text = text.replace(old, new)
        dst = out / path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        print(f"patched {path}")
        for line in text.splitlines():
            if "pip install -e" in line:
                print("   ", line.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
