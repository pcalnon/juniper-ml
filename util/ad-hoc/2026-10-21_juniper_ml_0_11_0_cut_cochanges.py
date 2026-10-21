#!/usr/bin/env python3
"""The juniper-ml 0.11.0 cut's co-changes: README's compatibility lead-in and docs/REFERENCE.md's pins record.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-21
Status: ad-hoc — one-off (the juniper-ml 0.11.0 release proposal)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the 0.11.0 proposal PR (branch release/juniper-ml-v0.11.0, opened by util/release_train/propose.py);
         notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.13, "Next");
         util/ad-hoc/2026-09-21_sync_readme_compat_table.py; util/ad-hoc/2026-10-08_raise_data_floor_0_17_0.py

Why this exists
---------------
``util/release_train/propose.py`` bumps ``pyproject.toml``, moves ``[Unreleased]`` and bumps the
``AGENTS.md`` Version header. Two more files name the release, and the generator touches neither:

* ``README.md``'s "Ecosystem Compatibility" lead-in ("The pyproject pins matching `juniper-ml` X:").
  ``tests/test_pyproject_extras.py`` ``ReadmeCompatTableTest`` requires it to name the pyproject
  version, so the bare proposal fails Regression Tests (measured on a scratch copy, 2026-10-21).
  juniper-ml's previous bump (0.10.0, #2033) was made by hand, and this is the first generated
  juniper-ml proposal since that guard landed (#1972).
* ``docs/REFERENCE.md``: the "Ecosystem Compatibility" sentence names 0.10.0 and the recurrence
  ranges 0.8.0 introduced, the matrix has no ``0.11.x`` row (the data-floor raise to 0.17.0 left it
  for the cut, ``util/ad-hoc/2026-10-08_raise_data_floor_0_17_0.py``), and the "Package Overview"
  Version cell has said 0.6.0 since 0.6.0.

The matrix row and the recurrence ranges are read from ``pyproject.toml`` and asserted against what
0.11.0 declares. Every other edit asserts its exact old text exactly once. A site already at its
target is reported and left alone, so a re-run after a rebase is safe.

Usage
-----
    python3 util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py [--check]

Run it on a tree whose ``pyproject.toml`` already says 0.11.0 (the proposal branch). ``--check``
writes nothing and exits 1 while an edit is still owed.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SPEC_RE = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?P<spec>.*)$")
_VERSION = "0.11.0"
_REFERENCE = _REPO / "docs" / "REFERENCE.md"
_README_SYNC = _REPO / "util" / "ad-hoc" / "2026-09-21_sync_readme_compat_table.py"

#: The compatibility matrix's columns, in table order, with what 0.11.0 declares for each.
_MATRIX_FLOORS = {
    "juniper-data": ">=0.17.0",
    "juniper-cascor": ">=0.11.0",
    "juniper-canopy": ">=0.9.0",
    "juniper-data-client": ">=0.5.0",
    "juniper-cascor-client": ">=0.8.0",
    "juniper-cascor-worker": ">=0.4.0",
    "juniper-ci-tools": ">=0.1.0",
    "juniper-doc-tools": ">=0.1.0,<0.2.0",
    "juniper-observability": ">=0.2.0",
}
#: The [recurrence] ranges 0.11.0 declares, and the ones 0.8.0 through 0.10.0 published (read from PyPI).
_RECURRENCE_NEW = {
    "juniper-recurrence-model": ">=0.6.0,<0.7.0",
    "juniper-recurrence": ">=0.8.0,<0.9.0",
    "juniper-recurrence-client": ">=0.3.0,<0.4.0",
}
_RECURRENCE_OLD = "`juniper-recurrence-model>=0.3.0,<0.4.0`, `juniper-recurrence>=0.5.0,<0.6.0` and `juniper-recurrence-client>=0.3.0,<0.4.0`"

_ROW_PREVIOUS = "| 0.10.x     | >=0.15.0     | >=0.11.0       | >=0.8.1        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.2.0               |"

_SENTENCE_STEM = "Every package below ships from PyPI; servers and tools land under their own extras, clients and worker keep their existing groups. The `0.6.x` row is kept for history and covers 0.7.x too -- 0.7.0/0.7.1 changed no floor. The three `recurrence` pins have no columns here; "
_SENTENCE_OLD = f"`juniper-ml` 0.10.0 declares the following pins. {_SENTENCE_STEM}0.8.0 sets them to {_RECURRENCE_OLD} (see the extras table above)."

_VERSION_CELL_OLD = "| **Version**            | `0.6.0`      |"
_VERSION_CELL_NEW = "| **Version**            | `0.11.0`     |"


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
    """A matrix row in the previous row's cell widths."""
    widths = [len(cell) for cell in _ROW_PREVIOUS.split("|")[1:-1]]
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
    for table in (_MATRIX_FLOORS, _RECURRENCE_NEW):
        for pkg, spec in table.items():
            if pins.get(pkg) != spec:
                print(f"ERROR: pyproject.toml pins {pkg}{pins.get(pkg, ' (absent)')}, expected {pkg}{spec}", file=sys.stderr)
                return 2

    text = _REFERENCE.read_text(encoding="utf-8")
    original = text

    recurrence_new = ", ".join(f"`{pkg}{spec}`" for pkg, spec in list(_RECURRENCE_NEW.items())[:2]) + f" and `juniper-recurrence-client{_RECURRENCE_NEW['juniper-recurrence-client']}`"
    sentence_new = f"`juniper-ml` {_VERSION} declares the following pins. {_SENTENCE_STEM}{_VERSION} sets them to {recurrence_new} (see the extras table above), and 0.8.0 through 0.10.0 published {_RECURRENCE_OLD}."
    text = _replace_once(text, _SENTENCE_OLD, sentence_new, "docs/REFERENCE.md compatibility sentence", owed, done)
    text = _replace_once(text, _VERSION_CELL_OLD, _VERSION_CELL_NEW, "docs/REFERENCE.md Package Overview Version cell", owed, done)

    row_site = "docs/REFERENCE.md 0.11.x matrix row"
    row_new = _render_row("0.11.x", [pins[pkg] for pkg in _MATRIX_FLOORS])
    if row_new in text:
        done.append(row_site)
    elif "| 0.11.x " in text:
        raise SystemExit("ERROR: docs/REFERENCE.md has a 0.11.x row that differs from pyproject.toml; fix it by hand")
    else:
        if text.count(_ROW_PREVIOUS + "\n") != 1:
            raise SystemExit("ERROR: docs/REFERENCE.md: the 0.10.x matrix row is not there exactly once")
        text = text.replace(_ROW_PREVIOUS + "\n", _ROW_PREVIOUS + "\n" + row_new + "\n", 1)
        owed.append(row_site)

    readme_site = "README.md Ecosystem Compatibility table"
    readme_owed = subprocess.run([sys.executable, str(_README_SYNC), "--check"], capture_output=True, text=True).returncode != 0
    (owed if readme_owed else done).append(readme_site)

    for site in done:
        print(f"  = {site}: already at target")
    for site in owed:
        print(f"  ~ {site}: {'owed' if args.check else 'written'}")
    if args.check:
        print("--check: nothing written")
        return 1 if owed else 0
    if text != original:
        _REFERENCE.write_text(text, encoding="utf-8")
    if readme_owed:
        sys.stdout.flush()
        subprocess.run([sys.executable, str(_README_SYNC)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
