#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_dropped_import_check.py
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- investigation
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#650
#
# Description:
#    Which distributions does juniper-canopy#650's install change REMOVE from the unit lane, and
#    are any of them actually imported by src/ (application or tests)?
#
#    Motivation: collection parity passed (345 files / 7538 tests, identical sets) and CI still
#    failed, because `sentry_sdk` is imported INSIDE test bodies -- it collects fine and raises at
#    run time. Collection is not execution. Rather than discover the rest one CI round at a time,
#    this cross-checks every dropped distribution against a real import grep.
#
#    KNOWN BLIND SPOT, stated because it already bit: this only sees packages canopy's OWN source
#    imports. `sentry-sdk` is not flagged here and is nonetheless required -- canopy never imports
#    it; `juniper_observability.configure_sentry` imports it internally, and five unit tests drive
#    that path. A dropped package needed only by a DEPENDENCY is invisible to an import grep. Use
#    this to triage, never as the gate; the gate is running the suite.
#
#    Reads the two `pip list --format=freeze` captures produced by
#    2026-09-22_canopy_collect_parity.bash, which deliberately keeps its workdir.
#
#    Usage:  python3 util/ad-hoc/2026-09-22_canopy_dropped_import_check.py [parity-workdir]
#####################################################################################################################################################################################################

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

DEFAULT_WORK = Path(
    "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/"
    "b71ebef9-0742-4ce0-b72d-110ca6a9dbbf/scratchpad/parity"
)
CANOPY = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy")


def freeze_names(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "==" in line:
            n, v = line.split("==", 1)
            out[n.strip().lower()] = v.strip()
    return out


def import_sites(module: str) -> list[str]:
    """Files under canopy/src that import `module` at any indentation (incl. inside functions)."""
    if not module:
        return []
    pattern = rf"^[[:space:]]*(import|from)[[:space:]]+{re.escape(module)}\b"
    r = subprocess.run(
        ["grep", "-rlE", pattern, str(CANOPY / "src"), "--include=*.py"],
        capture_output=True,
        text=True,
    )
    return r.stdout.strip().splitlines() if r.returncode == 0 else []


def candidate_modules(dist: str) -> set[str]:
    """Plausible import names for a distribution.

    Deliberately does NOT include `dist.split("-")[0]`. That heuristic made `pytest-html` and
    `pytest-metadata` both match a bare `import pytest` in 60+ files and report as load-bearing
    when neither is imported anywhere.
    """
    base = dist.lower()
    return {base.replace("-", "_"), base.replace("-", "")}


def main() -> int:
    work = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WORK
    today = freeze_names(work / "today.dists")
    new = freeze_names(work / "new.dists")

    dropped = sorted(set(today) - set(new))
    added = sorted(set(new) - set(today))

    print(f"today={len(today)} dists   proposed={len(new)} dists")
    print(f"dropped={len(dropped)}   added={len(added)}\n")

    risky: list[tuple[str, list[str]]] = []
    for dist in dropped:
        files: list[str] = []
        for mod in sorted(candidate_modules(dist)):
            files.extend(import_sites(mod))
        files = sorted(set(files))
        flag = "  <-- IMPORTED BY src/" if files else ""
        print(f"  - {dist:30} {today[dist]:14}{flag}")
        if files:
            risky.append((dist, files))

    if added:
        print("\nadded:")
        for dist in added:
            print(f"  + {dist:30} {new[dist]}")

    print("\n" + "=" * 78)
    print("DROPPED **AND** IMPORTED -- each of these must come back via a declared extra")
    print("=" * 78)
    if not risky:
        print("  (none)")
    for dist, files in risky:
        print(f"\n  {dist}")
        for f in files[:8]:
            print(f"     {f.replace(str(CANOPY) + '/', '')}")
    return 1 if risky else 0


if __name__ == "__main__":
    raise SystemExit(main())
