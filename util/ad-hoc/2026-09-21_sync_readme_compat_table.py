#!/usr/bin/env python3
"""Regenerate README.md's "Ecosystem Compatibility" pin table from pyproject.toml.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-21
Version:     0.1.0
License:     MIT License
Status:      single-use (decision-11 floor record repair)

Why this exists
---------------
``README.md`` carries TWO pin tables. The "Available Extras" table (grouped by extra) is
already pinned to ``pyproject.toml`` by ``tests/test_pyproject_extras.py``. The
"Ecosystem Compatibility" table -- a flat two-column ``| Package | Pin |`` -- is NOT, and
drifted: it still advertises the floors of ``juniper-ml`` 0.6.0, naming that version in
its lead-in sentence, while the package shipped 0.8.0. Because ``README.md`` is the
PyPI long_description, those stale floors are what pypi.org/project/juniper-ml serves.

Regenerating rather than hand-editing so the change can be replayed after a rebase --
the decision-11 release train lost a whole-file upload to exactly that (held-open PR
accumulating merges, see HANDOFF_2026-09-12 section 4).

Usage
-----
    python3 util/ad-hoc/2026-09-21_sync_readme_compat_table.py [--check]
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_README = _REPO / "README.md"
_PYPROJECT = _REPO / "pyproject.toml"

_LEAD_RE = re.compile(r"^The pyproject pins matching `juniper-ml` [0-9][^:]*:$", re.MULTILINE)
_SPEC_RE = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?P<spec>.*)$")


def _collect_pins() -> tuple[str, dict[str, str]]:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    version = data["project"]["version"]
    pins: dict[str, str] = {}
    for extra, members in data["project"]["optional-dependencies"].items():
        if extra == "all":
            continue
        for member in members:
            if member.startswith("juniper-ml["):
                continue
            match = _SPEC_RE.match(member.strip())
            if not match:
                raise SystemExit(f"unparsable requirement: {member!r}")
            pkg, spec = match.group("pkg"), match.group("spec").strip()
            prior = pins.get(pkg)
            if prior is not None and prior != spec:
                raise SystemExit(f"{pkg} declared with conflicting specs: {prior!r} vs {spec!r}")
            pins[pkg] = spec
    return version, pins


def _render(version: str, pins: dict[str, str]) -> str:
    width_pkg = max(len(f"`{p}`") for p in pins)
    width_pin = max(len(f"`{s}`") for s in pins.values())
    width_pkg = max(width_pkg, len("Package"))
    width_pin = max(width_pin, len("Pin"))
    rows = [
        f"| {'Package'.ljust(width_pkg)} | {'Pin'.ljust(width_pin)} |",
        f"|{'-' * (width_pkg + 2)}|{'-' * (width_pin + 2)}|",
    ]
    for pkg in sorted(pins):
        rows.append(f"| {f'`{pkg}`'.ljust(width_pkg)} | {f'`{pins[pkg]}`'.ljust(width_pin)} |")
    lead = f"The pyproject pins matching `juniper-ml` {version}:"
    return lead + "\n\n" + "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if the table is stale; write nothing")
    args = ap.parse_args()

    version, pins = _collect_pins()
    text = _README.read_text(encoding="utf-8")

    lead = _LEAD_RE.search(text)
    if not lead:
        raise SystemExit("could not locate the 'pyproject pins matching' lead-in in README.md")

    # The table runs from the lead-in to the first blank line after the last table row.
    tail = text[lead.end():]
    rows = re.match(r"\n\n(?:\|[^\n]*\n)+", tail)
    if not rows:
        raise SystemExit("could not locate the pin table rows after the lead-in")

    old_block = text[lead.start(): lead.end() + rows.end()].rstrip("\n")
    new_block = _render(version, pins)

    if old_block == new_block:
        print("README.md Ecosystem Compatibility table is already in sync.")
        return 0
    if args.check:
        print("STALE: README.md Ecosystem Compatibility table does not match pyproject.toml", file=sys.stderr)
        return 1

    _README.write_text(text.replace(old_block, new_block, 1), encoding="utf-8")
    print(f"Rewrote README.md Ecosystem Compatibility table ({len(pins)} packages, version {version}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
