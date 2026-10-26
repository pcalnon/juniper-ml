#!/usr/bin/env python3
"""The juniper-ml 0.11.3 cut's co-changes: REFERENCE.md's Version cell and sentence, and the #2062 entry's controls.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off (the juniper-ml 0.11.3 release proposal)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-25_juniper_ml_0_11_2_cut_cochanges.py (the 0.11.2 cut this follows);
         util/release_train/propose.py (its co-change checklist leaves docs/REFERENCE.md to the cut);
         juniper-ml#2062 and juniper-ml#2333 (the [servers] extras that 0.11.3 ships)

Why this exists
---------------
``util/release_train/propose.py`` bumps ``pyproject.toml``, ``AGENTS.md``'s Version header and README's
compatibility lead-in, and moves ``[Unreleased]``. ``docs/REFERENCE.md`` names the release in two more
places, and no test guards either of them:

* the "Package Overview" Version cell, which 0.11.2's cut set to ``0.11.2``;
* the "Ecosystem Compatibility" sentence, which says 0.11.2 declares the matrix's pins.

0.11.3 moves no floor. juniper-ml#2333 requests the three servers with their own extras
(``juniper-canopy[juniper-cascor,juniper-data]``, ``juniper-cascor[api,juniper-data]`` and
``juniper-data[api]``), and an extras marker has no column in the matrix, so the ``0.11.x`` row stays as
0.11.2's cut wrote it. The row is still rendered from ``pyproject.toml`` and asserted against the row on
disk, so a floor that did move stops the cut instead of being missed.

This parser strips a PEP 508 extras marker before it reads the floor. The 0.11.2 script's did not need
to: since juniper-ml#2333 its pattern would read ``juniper-canopy[juniper-cascor,juniper-data]>=0.9.0``
as the package ``juniper-canopy`` with the spec ``[juniper-cascor,juniper-data]>=0.9.0``.

One more edit is in ``CHANGELOG.md``, inside the ``[0.11.3]`` section the proposal has just made. That section
becomes 0.11.3's release notes and Release body, which cannot be re-cut. The juniper-ml#2062 entry named
only the 0.11.1 control of its differential wheel check, because it was written before 0.11.2 was out.
The re-cut was re-measured against the published 0.11.2 on 2026-10-26 with the same result (juniper-ml#2333),
so the entry now names both controls. The script refuses unless the entry sits under ``## [0.11.3]``.

Every edit asserts its exact old text exactly once. A site already at its target is reported and left
alone, so a re-run after a rebase is safe.

Usage
-----
    python3 util/ad-hoc/2026-10-26_juniper_ml_0_11_3_cut_cochanges.py [--check]

Run it on a tree whose ``pyproject.toml`` already says 0.11.3 (the proposal branch). ``--check`` writes
nothing and exits 1 while an edit is still owed.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
#: A requirement's package name, an optional PEP 508 extras marker (dropped), and its version spec.
_SPEC_RE = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?:\[[^\]]*\])?(?P<spec>.*)$")
_VERSION = "0.11.3"
_REFERENCE = _REPO / "docs" / "REFERENCE.md"
_CHANGELOG = _REPO / "CHANGELOG.md"

#: The compatibility matrix's columns, in table order, with what 0.11.3 declares for each.
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
#: The [servers] extra that the sentence describes (juniper-ml#2333), asserted for the same reason.
_SERVERS = [
    "juniper-canopy[juniper-cascor,juniper-data]>=0.9.0",
    "juniper-cascor[api,juniper-data]>=0.12.0",
    "juniper-data[api]>=0.17.1",
]

_ROW = "| 0.11.x     | >=0.17.1     | >=0.12.0       | >=0.9.0        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.4.1               |"

_STEM = "Every package below ships from PyPI; servers and tools land under their own extras, clients and worker keep their existing groups. The `0.6.x` row is kept for history and covers 0.7.x too -- 0.7.0/0.7.1 changed no floor. "
_RECURRENCE_NEW = "`juniper-recurrence-model>=0.6.0,<0.7.0`, `juniper-recurrence>=0.8.0,<0.9.0` and `juniper-recurrence-client>=0.3.0,<0.4.0`"
_RECURRENCE_OLD = "`juniper-recurrence-model>=0.3.0,<0.4.0`, `juniper-recurrence>=0.5.0,<0.6.0` and `juniper-recurrence-client>=0.3.0,<0.4.0`"
_HISTORY = (
    "0.11.0 published `juniper-observability>=0.2.0`, which 0.11.1 raised to `>=0.4.1`; 0.11.1 also raised `juniper-service-core`, which has no column here, from `>=0.2.0,<0.8.0` to `>=0.7.1,<0.8.0`. "
)
_SENTENCE_OLD = (
    f"`juniper-ml` 0.11.2 declares the following pins. {_STEM}"
    "The `0.11.x` row is 0.11.2's. 0.11.0 and 0.11.1 published `juniper-data>=0.17.0` and `juniper-cascor>=0.11.0`, which 0.11.2 raises to `>=0.17.1` and `>=0.12.0`. "
    f"{_HISTORY}"
    f"The three `recurrence` pins have no columns here; 0.11.0 through 0.11.2 set them to {_RECURRENCE_NEW} (see the extras table above), and 0.8.0 through 0.10.0 published {_RECURRENCE_OLD}."
)
_SENTENCE_NEW = (
    f"`juniper-ml` {_VERSION} declares the following pins. {_STEM}"
    "The `0.11.x` row is 0.11.3's, and its floors are 0.11.2's. 0.11.3 moves no floor: it requests the three servers with their own extras (juniper-ml#2062; the extras table above names them), and an extras marker has no column here. "
    "0.11.0 and 0.11.1 published `juniper-data>=0.17.0` and `juniper-cascor>=0.11.0`, which 0.11.2 raised to `>=0.17.1` and `>=0.12.0`. "
    f"{_HISTORY}"
    f"The three `recurrence` pins have no columns here; 0.11.0 through 0.11.3 set them to {_RECURRENCE_NEW} (see the extras table above), and 0.8.0 through 0.10.0 published {_RECURRENCE_OLD}."
)

_VERSION_CELL_OLD = "| **Version**            | `0.11.2`     |"
_VERSION_CELL_NEW = "| **Version**            | `0.11.3`     |"

#: The juniper-ml#2062 entry named only the 0.11.1 control, because it was written before 0.11.2 was out. The re-cut
#: was re-measured against the published 0.11.2 on 2026-10-26, with the same result (juniper-ml#2333's comment). This
#: section is about to become 0.11.3's notes, and therefore its Release body, so it names both controls.
_MEASURED_OLD = (
    "    with the published 0.11.1's `[servers]` and one with this change's.\n"
    "    - With 0.11.1, JD-8, CC-2 and CC-3 SKIP on `No module named 'juniper_data_client'`, and CP-1 reports\n"
)
_MEASURED_NEW = (
    "    with a published release's `[servers]` and one with this change's. The control was 0.11.1 on 2026-10-25, and\n"
    "    0.11.2 on 2026-10-26, after this change was re-cut on top of the 0.11.2 cut.\n"
    "    - With either control, JD-8, CC-2 and CC-3 SKIP on `No module named 'juniper_data_client'`, and CP-1 reports\n"
)


def _pyproject() -> tuple[str, dict[str, str], list[str]]:
    data = tomllib.loads((_REPO / "pyproject.toml").read_text(encoding="utf-8"))
    extras = data["project"]["optional-dependencies"]
    pins: dict[str, str] = {}
    for extra, members in extras.items():
        if extra == "all":
            continue
        for member in members:
            match = _SPEC_RE.match(member.strip())
            if not match:
                raise SystemExit(f"ERROR: unparsable requirement {member!r}")
            pins[match.group("pkg")] = match.group("spec").strip()
    return data["project"]["version"], pins, [member.strip() for member in extras["servers"]]


def _render_row(label: str, values: list[str]) -> str:
    """A matrix row in the 0.11.x row's cell widths."""
    widths = [len(cell) for cell in _ROW.split("|")[1:-1]]
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

    version, pins, servers = _pyproject()
    if version != _VERSION:
        print(f"ERROR: pyproject.toml declares {version}, not {_VERSION} -- run this on the proposal branch", file=sys.stderr)
        return 2
    for table in (_MATRIX_FLOORS, _OTHER_PINS):
        for pkg, spec in table.items():
            if pins.get(pkg) != spec:
                print(f"ERROR: pyproject.toml pins {pkg}{pins.get(pkg, ' (absent)')}, expected {pkg}{spec}", file=sys.stderr)
                return 2
    if servers != _SERVERS:
        print(f"ERROR: pyproject.toml's [servers] is {servers}, expected {_SERVERS}", file=sys.stderr)
        return 2

    text = _REFERENCE.read_text(encoding="utf-8")
    original = text

    row = _render_row("0.11.x", [pins[pkg] for pkg in _MATRIX_FLOORS])
    if row != _ROW or text.count(_ROW) != 1:
        print(f"ERROR: the 0.11.x row rendered from pyproject.toml is\n  {row}\nbut docs/REFERENCE.md must hold\n  {_ROW}\nexactly once (found {text.count(_ROW)})", file=sys.stderr)
        return 2
    done.append("docs/REFERENCE.md 0.11.x matrix row (no floor moves in 0.11.3)")

    text = _replace_once(text, _VERSION_CELL_OLD, _VERSION_CELL_NEW, "docs/REFERENCE.md Package Overview Version cell", owed, done)
    text = _replace_once(text, _SENTENCE_OLD, _SENTENCE_NEW, "docs/REFERENCE.md compatibility sentence", owed, done)

    changelog = _CHANGELOG.read_text(encoding="utf-8")
    changelog_original = changelog
    section = changelog.find("## [0.11.3]")
    entry = changelog.find(_MEASURED_OLD)
    if section < 0 or 0 <= entry < section:
        print("ERROR: the juniper-ml#2062 entry must sit under CHANGELOG.md's ## [0.11.3] -- run this on the proposal branch", file=sys.stderr)
        return 2
    changelog = _replace_once(changelog, _MEASURED_OLD, _MEASURED_NEW, "CHANGELOG.md [0.11.3] juniper-ml#2062 entry: both controls", owed, done)

    for site in done:
        print(f"  = {site}: already at target")
    for site in owed:
        print(f"  ~ {site}: {'owed' if args.check else 'written'}")
    if args.check:
        print("--check: nothing written")
        return 1 if owed else 0
    if text != original:
        _REFERENCE.write_text(text, encoding="utf-8")
    if changelog != changelog_original:
        _CHANGELOG.write_text(changelog, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
