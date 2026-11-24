#!/usr/bin/env python3
"""
Check that a venv satisfies every requirement of a pyproject.toml (the core dependencies and the named extras).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 7: validating the d2-unrun-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session7/briefs/VF_validate_data_unrun_tests.txt ("use the existing venvs ... if they match
         main's floors (check)")

Usage (run it WITH the venv's interpreter, so that importlib.metadata reads that venv):
  <venv>/bin/python 2026-11-12_flood4r2_val_d2-data_venv_floors.py --pyproject <file> [--extra NAME ...] [--out <json>]

A requirement that names the project itself (the ``all`` self-reference) is expanded into the extras it lists. A
requirement whose marker is false for this interpreter is skipped and counted. Exit 0 when nothing is missing and
no installed version falls outside its specifier, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--pyproject", required=True)
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--out")
    ns = parser.parse_args()
    project = tomllib.loads(Path(ns.pyproject).read_text(encoding="utf-8"))["project"]
    own = canonicalize_name(project["name"])
    optional = project.get("optional-dependencies", {})
    pending = [(text, "core") for text in project.get("dependencies", [])]
    queue = list(ns.extra)
    seen: set[str] = set()
    while queue:
        extra = queue.pop()
        if extra in seen:
            continue
        seen.add(extra)
        for text in optional[extra]:
            requirement = Requirement(text)
            if canonicalize_name(requirement.name) == own:
                queue.extend(requirement.extras)
            else:
                pending.append((text, extra))
    rows, bad, skipped = [], [], 0
    for text, origin in pending:
        requirement = Requirement(text)
        if requirement.marker is not None and not requirement.marker.evaluate({"extra": origin}):
            skipped += 1
            continue
        try:
            installed = metadata.version(requirement.name)
        except metadata.PackageNotFoundError:
            installed = None
        ok = installed is not None and requirement.specifier.contains(installed, prereleases=True)
        rows.append({"requirement": text, "from": origin, "installed": installed, "ok": ok})
        if not ok:
            bad.append(f"{text} (from {origin}): installed {installed}")
    report = {"python": sys.version.split()[0], "executable": sys.executable, "extras": sorted(seen), "checked": len(rows), "skipped_by_marker": skipped, "unsatisfied": bad, "rows": rows}
    if ns.out:
        Path(ns.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"python {report['python']}: {len(rows)} requirements checked ({skipped} skipped by marker), {len(bad)} unsatisfied")
    for line in bad:
        print("UNSATISFIED:", line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
