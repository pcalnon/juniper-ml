#!/usr/bin/env python3
"""The juniper-ml 0.11.2 cut's co-changes: docs/REFERENCE.md's Version cell, compatibility sentence and 0.11.x row.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — one-off (the juniper-ml 0.11.2 release proposal)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-25_juniper_ml_0_11_1_cut_cochanges.py (the 0.11.1 cut this follows);
         util/release_train/propose.py (its co-change checklist leaves docs/REFERENCE.md to the cut);
         juniper-ml#2326 (the [servers] floors 0.11.2 ships, R-ML-SERVERS)

Why this exists
---------------
``util/release_train/propose.py`` bumps ``pyproject.toml``, ``AGENTS.md``'s Version header and README's
compatibility lead-in, and moves ``[Unreleased]``. ``docs/REFERENCE.md`` names the release in three more
places, and no test guards any of them:

* the "Package Overview" Version cell, which 0.11.1's cut set to ``0.11.1``;
* the "Ecosystem Compatibility" sentence, which says 0.11.1 declares the matrix's pins;
* the matrix's ``0.11.x`` row, whose ``juniper-data`` and ``juniper-cascor`` cells still say 0.11.1's
  ``>=0.17.0`` and ``>=0.11.0``. juniper-ml#2326 raised ``[servers]`` to ``juniper-data>=0.17.1`` and
  ``juniper-cascor>=0.12.0`` after 0.11.1 was cut, so 0.11.2 is the first release to declare them.

The matrix is one row per minor, so the ``0.11.x`` row now carries 0.11.2's floors, and the sentence
keeps 0.11.0's and 0.11.1's as history: the precedent is 0.11.1's own cut, which kept 0.11.0's
``juniper-observability`` floor the same way. The row is rendered from ``pyproject.toml`` and asserted
against what 0.11.2 declares. Every other edit asserts its exact old text exactly once. A site already at
its target is reported and left alone, so a re-run after a rebase is safe.

Usage
-----
    python3 util/ad-hoc/2026-10-25_juniper_ml_0_11_2_cut_cochanges.py [--check]

Run it on a tree whose ``pyproject.toml`` already says 0.11.2 (the proposal branch). ``--check`` writes
nothing and exits 1 while an edit is still owed.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SPEC_RE = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?P<spec>.*)$")
_VERSION = "0.11.2"
_REFERENCE = _REPO / "docs" / "REFERENCE.md"

#: The compatibility matrix's columns, in table order, with what 0.11.2 declares for each.
_MATRIX_FLOORS = {
    "juniper-data": ">=0.17.1",
    "juniper-cascor": ">=0.12.0",
    "juniper-canopy": ">=0.9.0",
    "juniper-data-client": ">=0.5.0",
    "juniper-cascor-client": ">=0.8.0",
    "juniper-cascor-worker": ">=0.4.0",
    "juniper-ci-tools": ">=0.1.0",
    "juniper-doc-tools": ">=0.1.0,<0.2.0",
    "juniper-observability": ">=0.4.1",
}
#: Pins the sentence names that have no matrix column, asserted so the prose cannot drift from pyproject.
_OTHER_PINS = {
    "juniper-service-core": ">=0.7.1,<0.8.0",
    "juniper-recurrence-model": ">=0.6.0,<0.7.0",
    "juniper-recurrence": ">=0.8.0,<0.9.0",
    "juniper-recurrence-client": ">=0.3.0,<0.4.0",
}

_ROW_OLD = "| 0.11.x     | >=0.17.0     | >=0.11.0       | >=0.9.0        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.4.1               |"

_STEM = "Every package below ships from PyPI; servers and tools land under their own extras, clients and worker keep their existing groups. The `0.6.x` row is kept for history and covers 0.7.x too -- 0.7.0/0.7.1 changed no floor. "
_RECURRENCE_NEW = "`juniper-recurrence-model>=0.6.0,<0.7.0`, `juniper-recurrence>=0.8.0,<0.9.0` and `juniper-recurrence-client>=0.3.0,<0.4.0`"
_RECURRENCE_OLD = "`juniper-recurrence-model>=0.3.0,<0.4.0`, `juniper-recurrence>=0.5.0,<0.6.0` and `juniper-recurrence-client>=0.3.0,<0.4.0`"
_SENTENCE_OLD = (
    f"`juniper-ml` 0.11.1 declares the following pins. {_STEM}"
    "The `0.11.x` row is 0.11.1's: 0.11.0 published `juniper-observability>=0.2.0`, and 0.11.1 also raised `juniper-service-core`, which has no column here, from `>=0.2.0,<0.8.0` to `>=0.7.1,<0.8.0`. "
    f"The three `recurrence` pins have no columns here; 0.11.0 and 0.11.1 set them to {_RECURRENCE_NEW} (see the extras table above), and 0.8.0 through 0.10.0 published {_RECURRENCE_OLD}."
)
_SENTENCE_NEW = (
    f"`juniper-ml` {_VERSION} declares the following pins. {_STEM}"
    "The `0.11.x` row is 0.11.2's. 0.11.0 and 0.11.1 published `juniper-data>=0.17.0` and `juniper-cascor>=0.11.0`, which 0.11.2 raises to `>=0.17.1` and `>=0.12.0`. "
    "0.11.0 published `juniper-observability>=0.2.0`, which 0.11.1 raised to `>=0.4.1`; 0.11.1 also raised `juniper-service-core`, which has no column here, from `>=0.2.0,<0.8.0` to `>=0.7.1,<0.8.0`. "
    f"The three `recurrence` pins have no columns here; 0.11.0 through 0.11.2 set them to {_RECURRENCE_NEW} (see the extras table above), and 0.8.0 through 0.10.0 published {_RECURRENCE_OLD}."
)

_VERSION_CELL_OLD = "| **Version**            | `0.11.1`     |"
_VERSION_CELL_NEW = "| **Version**            | `0.11.2`     |"


def _pyproject_pins() -> tuple[str, dict[str, str]]:
    data = tomllib.loads((_REPO / "pyproject.toml").read_text(encoding="utf-8"))
    pins: dict[str, str] = {}
    for extra, members in data["project"]["optional-dependencies"].items():
        if extra == "all":
            continue
        for member in members:
            match = _SPEC_RE.match(member.strip())
            if not match:
                raise SystemExit(f"ERROR: unparsable requirement {member!r}")
            pins[match.group("pkg")] = match.group("spec").strip()
    return data["project"]["version"], pins


def _render_row(label: str, values: list[str]) -> str:
    """A matrix row in the old 0.11.x row's cell widths."""
    widths = [len(cell) for cell in _ROW_OLD.split("|")[1:-1]]
    cells = [f" {text}".ljust(width) for text, width in zip([label] + values, widths)]
    for cell, width in zip(cells, widths):
        if len(cell) != width:
            raise SystemExit(f"ERROR: {cell.strip()!r} does not fit a {width}-character matrix cell")
    return "|" + "|".join(cells) + "|"


def _replace_once(text: str, old: str, new: str, site: str, owed: list[str], done: list[str]) -> str:
    if text.count(new) == 1 and old not in text:
        done.append(site)
        return text
    if text.count(old) != 1:
        raise SystemExit(f"ERROR: {site}: expected the old text exactly once, found {text.count(old)}")
    owed.append(site)
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 while an edit is owed)")
    args = ap.parse_args()
    owed: list[str] = []
    done: list[str] = []

    version, pins = _pyproject_pins()
    if version != _VERSION:
        print(f"ERROR: pyproject.toml declares {version}, not {_VERSION} -- run this on the proposal branch", file=sys.stderr)
        return 2
    for table in (_MATRIX_FLOORS, _OTHER_PINS):
        for pkg, spec in table.items():
            if pins.get(pkg) != spec:
                print(f"ERROR: pyproject.toml pins {pkg}{pins.get(pkg, ' (absent)')}, expected {pkg}{spec}", file=sys.stderr)
                return 2

    text = _REFERENCE.read_text(encoding="utf-8")
    original = text

    text = _replace_once(text, _VERSION_CELL_OLD, _VERSION_CELL_NEW, "docs/REFERENCE.md Package Overview Version cell", owed, done)
    text = _replace_once(text, _SENTENCE_OLD, _SENTENCE_NEW, "docs/REFERENCE.md compatibility sentence", owed, done)
    row_new = _render_row("0.11.x", [pins[pkg] for pkg in _MATRIX_FLOORS])
    text = _replace_once(text, _ROW_OLD, row_new, "docs/REFERENCE.md 0.11.x matrix row", owed, done)

    for site in done:
        print(f"  = {site}: already at target")
    for site in owed:
        print(f"  ~ {site}: {'owed' if args.check else 'written'}")
    if args.check:
        print("--check: nothing written")
        return 1 if owed else 0
    if text != original:
        _REFERENCE.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
