#!/usr/bin/env python3
"""The juniper-ml 0.11.5 cut's co-changes: REFERENCE.md's Version cell and compatibility sentence, and the CHANGELOG repairs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-13
Status: ad-hoc -- one-off (the juniper-ml 0.11.5 release proposal)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-06_juniper_ml_0_11_4_cut_cochanges.py (the 0.11.4 cut this follows);
         util/ad-hoc/2026-10-25_juniper_ml_0_11_1_cut_cochanges.py (the last cut that moved a matrix column's floor);
         util/ad-hoc/2026-11-12_tools_floors_observability_0_4_2_service_core_0_7_2.py (the floor PR, juniper-ml#2555,
         whose two interim clauses this removes);
         util/release_train/propose.py (its co-change checklist leaves docs/REFERENCE.md to the cut);
         util/ad-hoc/2026-09-23_released_section_drift.py (the check that found the misfiled bullet)

Why this exists
---------------
``util/release_train/propose.py`` bumps ``pyproject.toml``, ``AGENTS.md``'s Version header and README's
compatibility lead-in, and moves ``[Unreleased]``. This cut owes more, and no test on ``main`` guards any of it.

``docs/REFERENCE.md``:

* the "Package Overview" Version cell, which 0.11.4's cut set to ``0.11.4``;
* the "Ecosystem Compatibility" sentence. 0.11.5 ships the ``[tools]`` floors ``juniper-observability>=0.4.2`` and
  ``juniper-service-core>=0.7.2,<0.8.0`` (owner ruling 2026-11-09; juniper-ml#2555). That PR moved the matrix's
  ``0.11.x`` observability cell at once, because ``main``'s row tracks ``pyproject.toml``, and added two clauses that
  call both floors "unreleased; first in juniper-ml 0.11.5". With the cut they are released, so the clauses go, and
  the sentence records the two moves as 0.11.5's. The sentence stays on ONE physical line, with its
  "X.Y.Z declares the following pins." opening and exactly one "X.Y.Z sets them to" clause naming this release:
  the tests of Cursor draft juniper-ml#2507, which the flood-4 arc is carrying, read both.
* the ``0.11.x`` row is rendered from ``pyproject.toml`` and asserted against the row on disk, so a column floor
  that moved without the row stops the cut.

``CHANGELOG.md``, whose ``[0.11.5]`` section becomes the Release body, which cannot be re-cut:

* **A bullet under the wrong release.** juniper-ml#2360 merged on 2026-11-12, six days after v0.11.4 was tagged, and
  its ``### Fixed`` bullet about the orphan reaper landed under the RELEASED ``## [0.11.4]`` heading with no conflict
  (row 5 of section 11.7 of ``notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md``). The v0.11.4
  tag does not carry that change and the v0.11.5 tag does, so the bullet moves, verbatim, to the end of
  ``[0.11.5]``'s ``### Fixed``.
* **Five entries under the wrong category.** The same merge put its own ``### Added`` and ``### Changed`` blocks
  directly under the existing ``### Added`` heading. The five entries that heading held (HARCOT, the yamaguchi
  root-cause analysis, the flood-4 regression tests, operator documentation and disposition record) so came to sit
  under juniper-ml#2360's ``### Changed``, and the section has two ``### Changed`` headings. The parent of
  ``187e3258`` shows where they were filed. The two juniper-ml#2360 bullets move down to the one ``### Changed``
  that remains, which puts the five back under ``### Added``.
* **Sentences that describe a state this release has left.** Each was true when its own PR merged, and another
  entry of the same section has since made it false: the floor entry's account of the paragraph above the matrix
  and of the consumers' locks, an effort default "left as an open question", rulings of which "none ... has landed
  yet", a PR that "still merges cleanly", and a race that "gets its own fix". Each is reworded to what 0.11.5 holds.

Every edit asserts its exact old text exactly once, counted over the whole file. A site already at its target is
reported and left alone, so a re-run after a rebase is safe. The CHANGELOG edit is checked for conservation: apart
from the reworded sentences and the dropped duplicate heading, the file's lines before and after are the same
multiset.

Usage
-----
    python3 util/ad-hoc/2026-11-13_juniper_ml_0_11_5_cut_cochanges.py [--check]

Run it on a tree whose ``pyproject.toml`` already says 0.11.5 and whose CHANGELOG already has ``## [0.11.5]`` (the
proposal branch). ``--check`` writes nothing and exits 1 while an edit is still owed. Exit 2 is a refusal: nothing
is written.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections import Counter
from pathlib import Path
from typing import NoReturn

_REPO = Path(__file__).resolve().parents[2]
#: A requirement's package name, an optional PEP 508 extras marker (dropped), and its version spec.
_SPEC_RE = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?:\[[^\]]*\])?(?P<spec>.*)$")
_VERSION = "0.11.5"
_PREVIOUS = "0.11.4"
_REFERENCE = _REPO / "docs" / "REFERENCE.md"
_CHANGELOG = _REPO / "CHANGELOG.md"

#: The compatibility matrix's columns, in table order, with what 0.11.5 declares for each.
_MATRIX_FLOORS = {
    "juniper-data": ">=0.17.1",
    "juniper-cascor": ">=0.12.0",
    "juniper-canopy": ">=0.9.0",
    "juniper-data-client": ">=0.5.0",
    "juniper-cascor-client": ">=0.8.0",
    "juniper-cascor-worker": ">=0.4.0",
    "juniper-ci-tools": ">=0.1.0",
    "juniper-doc-tools": ">=0.1.0,<0.2.0",
    "juniper-observability": ">=0.4.2",
}
#: Pins the sentence names that have no matrix column, asserted so the prose cannot drift from pyproject.
_OTHER_PINS = {
    "juniper-service-core": ">=0.7.2,<0.8.0",
    "juniper-recurrence-model": ">=0.6.0,<0.7.0",
    "juniper-recurrence": ">=0.8.1,<0.9.0",
    "juniper-recurrence-client": ">=0.3.0,<0.4.0",
}
#: The [servers] extra that the sentence describes (juniper-ml#2333), asserted for the same reason.
_SERVERS = [
    "juniper-canopy[juniper-cascor,juniper-data]>=0.9.0",
    "juniper-cascor[api,juniper-data]>=0.12.0",
    "juniper-data[api]>=0.17.1",
]

#: The floor PR (juniper-ml#2555) already wrote this row; the cut asserts it and changes nothing in it.
_ROW = "| 0.11.x     | >=0.17.1     | >=0.12.0       | >=0.9.0        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.4.2               |"

_STEM = "Every package below ships from PyPI; servers and tools land under their own extras, clients and worker keep their existing groups. The `0.6.x` row is kept for history and covers 0.7.x too -- 0.7.0/0.7.1 changed no floor. "
_NO_COLUMN_MOVE = "0.11.3 and 0.11.4 move no floor in a column: 0.11.3 requests the three servers with their own extras (juniper-ml#2062; the extras table above names them), and an extras marker has no column here. "
_SERVERS_HISTORY = "0.11.0 and 0.11.1 published `juniper-data>=0.17.0` and `juniper-cascor>=0.11.0`, which 0.11.2 raised to `>=0.17.1` and `>=0.12.0`. "
_TOOLS_HISTORY = "0.11.0 published `juniper-observability>=0.2.0`, which 0.11.1 raised to `>=0.4.1`; 0.11.1 also raised `juniper-service-core`, which has no column here, from `>=0.2.0,<0.8.0` to `>=0.7.1,<0.8.0`"
_RECURRENCE_NOW = "`juniper-recurrence-model>=0.6.0,<0.7.0`, `juniper-recurrence>=0.8.1,<0.9.0` and `juniper-recurrence-client>=0.3.0,<0.4.0`"
_RECURRENCE_0_11_0 = "`juniper-recurrence-model>=0.6.0,<0.7.0`, `juniper-recurrence>=0.8.0,<0.9.0` and `juniper-recurrence-client>=0.3.0,<0.4.0`"
_RECURRENCE_OLD = "`juniper-recurrence-model>=0.3.0,<0.4.0`, `juniper-recurrence>=0.5.0,<0.6.0` and `juniper-recurrence-client>=0.3.0,<0.4.0`"
_RECURRENCE_HISTORY = f"0.11.0 through 0.11.3 published {_RECURRENCE_0_11_0}, and 0.8.0 through 0.10.0 published {_RECURRENCE_OLD}."
_RAISED_0_8_1 = "`juniper-recurrence` to `>=0.8.1`, the release that floors `juniper-model-core[crossval]>=0.3.0`. "

#: The floor PR wrote this (util/ad-hoc/2026-11-12_tools_floors_observability_0_4_2_service_core_0_7_2.py).
_SENTENCE_OLD = (
    f"`juniper-ml` {_PREVIOUS} declares the following pins. {_STEM}"
    "The `0.11.x` row is 0.11.4's, and its floors are 0.11.2's, except the `juniper-observability` cell: it holds `main`'s floor, `>=0.4.2` (unreleased; first in juniper-ml 0.11.5), where the published 0.11.4 declares `>=0.4.1`. "
    f"{_NO_COLUMN_MOVE}{_SERVERS_HISTORY}"
    f"{_TOOLS_HISTORY}; `main` raises it to `>=0.7.2,<0.8.0` (unreleased; first in juniper-ml 0.11.5). "
    f"The three `recurrence` pins have no columns here. 0.11.4 sets them to {_RECURRENCE_NOW} (see the extras table above): it raises {_RAISED_0_8_1}"
    f"{_RECURRENCE_HISTORY}"
)
_SENTENCE_NEW = (
    f"`juniper-ml` {_VERSION} declares the following pins. {_STEM}"
    "The `0.11.x` row is 0.11.5's: its floors are 0.11.2's, except `juniper-observability`, which 0.11.5 raises from `>=0.4.1` to `>=0.4.2`. "
    f"{_NO_COLUMN_MOVE}{_SERVERS_HISTORY}"
    f"{_TOOLS_HISTORY}, and 0.11.5 raises it to `>=0.7.2,<0.8.0`. "
    f"The three `recurrence` pins have no columns here. 0.11.5 sets them to {_RECURRENCE_NOW} (see the extras table above), as 0.11.4 did: 0.11.4 raised {_RAISED_0_8_1}"
    f"{_RECURRENCE_HISTORY}"
)

_VERSION_CELL_OLD = "| **Version**            | `0.11.4`     |"
_VERSION_CELL_NEW = "| **Version**            | `0.11.5`     |"

#: What the interim clauses said; none may survive in docs/REFERENCE.md.
_INTERIM_MARKER = "unreleased; first in juniper-ml 0.11.5"

#: CHANGELOG.md, inside [0.11.5]: (site, exact old text, its replacement). Each old text was true when its PR merged.
_REWORDS = (
    (
        "the floor entry's clause about the paragraph above the matrix (juniper-ml#2555)",
        "    service-core **Meta pin** row and `juniper-service-core/README.md`'s pin advice. The compatibility matrix's\n"
        "    `0.11.x` row moves its `juniper-observability` cell with them, and the paragraph above it says that the published\n"
        "    0.11.4 declares `>=0.4.1`; the sentence naming the release moves at the 0.11.5 cut.\n",
        "    service-core **Meta pin** row and `juniper-service-core/README.md`'s pin advice. The compatibility matrix's\n"
        "    `0.11.x` row moves its `juniper-observability` cell with them, and the paragraph above it names 0.11.5 as the\n"
        "    release that raises both floors.\n",
    ),
    (
        "the floor entry's clause about the consumers' locks (juniper-ml#2555)",
        "    juniper-canopy and juniper-recurrence) move in each one's next release PR, by the same day's ruling; their locks\n" "    already pin both releases.\n",
        "    juniper-canopy and juniper-recurrence) move in each one's next release PR, by the same day's ruling; their\n" "    `requirements.lock` files already pin both releases.\n",
    ),
    (
        "the flood-4 regression-test entry's open effort default (juniper-ml#2554 set it)",
        "    `--effort 1` half: its `--effort 0` half pinned `--effort auto`, which Claude Code rejects (\"Unknown --effort\n" '    value"), so the script\'s default is left as an open question rather than locked in.\n',
        "    `--effort 1` half: its `--effort 0` half pinned `--effort auto`, which Claude Code rejects (\"Unknown --effort\n"
        '    value"), so that carrier left the script\'s default open; the launchers entry under Fixed, below, sets it to\n'
        "    `max`.\n",
    ),
    (
        "the flood-4 disposition entry's 'none of these has landed yet'",
        "  fixed, each in its own PR; none of these has landed yet. §5's six manifests and render config are archived under\n",
        "  fixed, each in its own PR; none of these had landed when this record merged. Since then the brace-cap change and the\n"
        "  two `juniper-service-core` fixes among those four (the broadcast-drop and stop-then-start entries under Fixed, below)\n"
        "  have landed in this repository. §5's six manifests and render config are archived under\n",
    ),
    (
        "the doc-link hook entry's 'that PR still merges cleanly' (juniper-ml#2360 merged on 2026-11-12)",
        "  hook only. The hunk is byte-identical to juniper-ml#2360's, so that PR still merges cleanly; it carries\n",
        "  hook only. The hunk is byte-identical to juniper-ml#2360's, which has since merged (2026-11-12 UTC) and carries\n",
    ),
    (
        "the paused-fit entry's race that 'gets its own fix' (juniper-ml#2557 is that fix)",
        "  shared pause gate, and a start is then accepted beside it. The owner has ruled that this race gets\n" "  its own fix, in its own PR (§8, ruling 11 of\n" "  `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`).\n",
        "  shared pause gate, and a start is then accepted beside it. The owner has ruled that this race gets\n"
        "  its own fix, in its own PR (§8, ruling 11 of\n"
        "  `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`); that fix is the\n"
        "  stop-then-start entry below, with which such a start is refused while the stopped `fit` still runs.\n",
    ),
)

#: CHANGELOG.md: juniper-ml#2360's bullet, filed under the released [0.11.4] heading six days after the tag.
_MISFILED = (
    "- **The orphan reaper protected the isolated stack only when its own `TMPDIR` matched the stack's.**\n"
    "  `util/reap_pytest_orphans.bash` derived the stack's protected run dir from `${TMPDIR:-/tmp}`, so a stack launched under\n"  # tmp-path-literal: allow
    "  one `TMPDIR` and reaped under another had no pid-file protection, and every session sets `TMPDIR` now. It protects the\n"
    "  FIXED default (`util/juniper_repo_tmp.bash`), resolved after the arguments are parsed, plus, read-only, the legacy\n"
    "  `/tmp/juniper-e2e` and `${TMPDIR}/juniper-e2e` that older checkouts' stacks may still use. It exits 1, reaping nothing,\n"  # tmp-path-literal: allow
    "  when it cannot resolve the default. `tests/test_reap_pytest_orphans.py` gains 8 tests and redirects the legacy roots.\n"
)
_HEADING_NEW_RE = re.compile(r"^## \[" + re.escape(_VERSION) + r"\] - \d{4}-\d{2}-\d{2}$", re.MULTILINE)
_HEADING_PREVIOUS_RE = re.compile(r"^## \[" + re.escape(_PREVIOUS) + r"\] - \d{4}-\d{2}-\d{2}$", re.MULTILINE)
_UNRELEASED = "## [Unreleased]\n\n"

#: CHANGELOG.md, inside [0.11.5]: the category repair's landmarks.
_CHANGED = "### Changed\n\n"
_FIRST_OF_2360 = "- **Fixed temp paths instead of the system temp dir** (the 2026-10-26 repo `tmp/` rule).\n"
_SECOND_OF_2360 = "- **The owner's 2026-10-26 rulings on `tmp/`**, quoted in section 1 of\n"
_FIRST_DISPLACED = "- **`HARCOT` joins the `notes/` repository tokens (2026-11-10).**"
_LAST_DISPLACED = "- **The Cursor flood-4 disposition record, with its render inputs and provenance scripts (round 1 complete).**"
_LAUNCHERS = "- **`-v` reports Claude Code's version in both launchers,"
_CATEGORIES_BEFORE = ["### Security", "### Added", "### Changed", "### Changed", "### Fixed"]
_CATEGORIES_AFTER = ["### Security", "### Added", "### Changed", "### Fixed"]


def _refuse(message: str) -> NoReturn:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


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
                _refuse(f"unparsable requirement {member!r}")
            spec = match.group("spec").strip()
            if pins.setdefault(match.group("pkg"), spec) != spec:
                _refuse(f"pyproject.toml gives {match.group('pkg')} two specs: {pins[match.group('pkg')]} and {spec}")
    return data["project"]["version"], pins, [member.strip() for member in extras["servers"]]


def _render_row(label: str, values: list[str]) -> str:
    """A matrix row in the 0.11.x row's cell widths."""
    widths = [len(cell) for cell in _ROW.split("|")[1:-1]]
    cells = [f" {text}".ljust(width) for text, width in zip([label] + values, widths)]
    for cell, width in zip(cells, widths):
        if len(cell) != width:
            _refuse(f"{cell.strip()!r} does not fit a {width}-character matrix cell")
    return "|" + "|".join(cells) + "|"


def _replace_once(text: str, old: str, new: str, site: str, owed: list[str], done: list[str]) -> str:
    if text.count(new) == 1 and old not in text:
        done.append(site)
        return text
    if text.count(old) != 1 or new in text:
        _refuse(f"{site}: expected the old text exactly once and the new text nowhere, found {text.count(old)} and {text.count(new)}")
    owed.append(site)
    return text.replace(old, new, 1)


def _section_bounds(text: str, heading: re.Pattern[str]) -> tuple[int, int]:
    """Character offsets of the one section whose heading line matches, up to the next ``## [`` heading."""
    starts = [match.start() for match in heading.finditer(text)]
    if len(starts) != 1:
        _refuse(f"CHANGELOG.md: expected exactly one heading matching {heading.pattern!r}, found {len(starts)}")
    following = re.search(r"^## \[", text[starts[0] + 1 :], flags=re.MULTILINE)
    if following is None:
        _refuse(f"CHANGELOG.md: no version heading follows {heading.pattern!r}")
    return starts[0], starts[0] + 1 + following.start()


def _categories(section: str) -> list[str]:
    return re.findall(r"^### .*$", section, flags=re.MULTILINE)


def _reword(text: str, owed: list[str], done: list[str]) -> tuple[str, list[tuple[str, str]]]:
    """Apply each rewording inside [0.11.5]; return the text and the (old, new) pairs that were applied."""
    applied: list[tuple[str, str]] = []
    for name, old, new in _REWORDS:
        site = f"CHANGELOG.md {name}"
        start, end = _section_bounds(text, _HEADING_NEW_RE)
        for candidate in (old, new):
            if candidate in text and not start < text.index(candidate) < end:
                _refuse(f"{site}: found outside the [{_VERSION}] section")
        before = len(owed)
        text = _replace_once(text, old, new, site, owed, done)
        if len(owed) != before:
            applied.append((old, new))
    return text, applied


def _recategorise(text: str, owed: list[str], done: list[str]) -> tuple[str, bool]:
    """Move juniper-ml#2360's two ``### Changed`` bullets under the later ``### Changed``, dropping its heading."""
    site = "CHANGELOG.md the five entries juniper-ml#2360's merge moved from Added to Changed"
    start, end = _section_bounds(text, _HEADING_NEW_RE)
    section = text[start:end]
    landmarks = {name: section.count(mark) for name, mark in (("2360a", _FIRST_OF_2360), ("2360b", _SECOND_OF_2360), ("first", _FIRST_DISPLACED), ("last", _LAST_DISPLACED), ("launchers", _LAUNCHERS))}
    if set(landmarks.values()) != {1}:
        _refuse(f"{site}: each landmark bullet must appear exactly once in [{_VERSION}], found {landmarks}")
    at = {name: section.index(mark) for name, mark in (("2360a", _FIRST_OF_2360), ("2360b", _SECOND_OF_2360), ("first", _FIRST_DISPLACED), ("last", _LAST_DISPLACED), ("launchers", _LAUNCHERS))}
    categories = _categories(section)
    if categories == _CATEGORIES_AFTER:
        changed = section.index(_CHANGED)
        if not at["first"] < at["last"] < changed < at["2360a"] < at["2360b"] < at["launchers"]:
            _refuse(f"{site}: one '### Changed', but the bullets are not in the repaired order")
        done.append(site)
        return text, False
    if categories != _CATEGORIES_BEFORE:
        _refuse(f"{site}: [{_VERSION}]'s categories are {categories}, expected {_CATEGORIES_BEFORE} or {_CATEGORIES_AFTER}")
    first = section.index(_CHANGED)
    second = section.index(_CHANGED, first + 1)
    block = section[first + len(_CHANGED) : at["first"]]
    if not (first < at["2360a"] < at["2360b"] < at["first"] < at["last"] < second < at["launchers"]):
        _refuse(f"{site}: the bullets are not in the order juniper-ml#2360's merge left")
    if not block.startswith(_FIRST_OF_2360) or not block.endswith("\n\n") or len(re.findall(r"^- ", block, flags=re.MULTILINE)) != 2:
        _refuse(f"{site}: the block under the first '### Changed' is not juniper-ml#2360's two bullets")
    if section[second + len(_CHANGED) :].find(_LAUNCHERS) != 0 or section[first - 1 : first] != "\n":
        _refuse(f"{site}: the later '### Changed' does not open with the launchers entry")
    repaired = section[:first] + section[at["first"] : second + len(_CHANGED)] + block + section[second + len(_CHANGED) :]
    owed.append(site)
    return text[:start] + repaired + text[end:], True


def _rehome_misfiled(text: str, owed: list[str], done: list[str]) -> str:
    """Move juniper-ml#2360's bullet from [0.11.4]'s ``### Fixed`` to the end of [0.11.5]'s."""
    site = "CHANGELOG.md the orphan-reaper bullet (juniper-ml#2360), re-homed from [0.11.4] to [0.11.5]"
    if text.count(_MISFILED) != 1:
        _refuse(f"{site}: expected the bullet exactly once in the file, found {text.count(_MISFILED)}")
    new_start, new_end = _section_bounds(text, _HEADING_NEW_RE)
    old_start, old_end = _section_bounds(text, _HEADING_PREVIOUS_RE)
    if new_end != old_start:
        _refuse(f"{site}: the [{_PREVIOUS}] section does not directly follow [{_VERSION}]")
    new_section = text[new_start:new_end]
    categories = _categories(new_section)
    if not categories or categories[-1] != "### Fixed":
        _refuse(f"{site}: [{_VERSION}]'s last category is {categories[-1] if categories else None!r}, not '### Fixed'")
    at = text.index(_MISFILED)
    if new_start < at < new_end:
        if text[at + len(_MISFILED) : new_end] != "\n":
            _refuse(f"{site}: the bullet is in [{_VERSION}], but not as the last entry of its '### Fixed'")
        done.append(site)
        return text
    if not old_start < at < old_end:
        _refuse(f"{site}: the bullet is in neither section")
    if not new_section.endswith("\n\n"):
        _refuse(f"{site}: [{_VERSION}] does not end with one blank line")
    lead = "### Fixed\n\n"
    if text[at - len(lead) : at] != lead or text[old_start:at].count(lead) != 1:
        _refuse(f"{site}: the bullet is not the first under [{_PREVIOUS}]'s '### Fixed'")
    after = at + len(_MISFILED)
    if text[after : after + 3] != "\n- ":
        _refuse(f"{site}: the bullet is not followed by a blank line and another bullet")
    owed.append(site)
    # Drop the bullet and the blank line after it; append the bullet, then one blank line, to [0.11.5].
    return text[:new_end] + _MISFILED + "\n" + text[new_end:at] + text[after + 1 :]


def _changelog(owed: list[str], done: list[str]) -> tuple[str, str]:
    original = _CHANGELOG.read_text(encoding="utf-8")
    text = original
    new_start, _ = _section_bounds(text, _HEADING_NEW_RE)
    if original.count("## [Unreleased]") != 1 or text[new_start - len(_UNRELEASED) : new_start] != _UNRELEASED:
        _refuse(f"CHANGELOG.md: '## [Unreleased]' must be empty and sit directly above '## [{_VERSION}]' -- re-home what it holds before the cut")

    text, reworded = _reword(text, owed, done)
    text, recategorised = _recategorise(text, owed, done)
    text = _rehome_misfiled(text, owed, done)

    # Arrangement: the result must be a tree on which every step finds its target, so a step that put the right
    # lines in the wrong place is refused here and not written. (Line counts alone cannot see placement.)
    still_owed: list[str] = []
    again, _ = _reword(text, still_owed, [])
    again, _ = _recategorise(again, still_owed, [])
    again = _rehome_misfiled(again, still_owed, [])
    if still_owed or again != text:
        _refuse(f"CHANGELOG.md: the edited text is not at its target; still owed: {still_owed}")

    # Conservation: apart from the reworded sentences and the dropped duplicate heading, the same lines, each as often.
    expected = Counter(original.split("\n"))
    for old, new in reworded:
        expected.subtract(old.split("\n")[:-1])
        expected.update(new.split("\n")[:-1])
    if recategorised:
        expected.subtract(["### Changed", ""])
    actual = Counter(text.split("\n"))
    if any(count < 0 for count in expected.values()) or +expected != +actual:
        differing = sorted(line for line in set(expected) | set(actual) if expected[line] != actual[line])
        _refuse(f"CHANGELOG.md: the edit does not conserve lines; {len(differing)} differ, first {differing[:2]!r}")
    return original, text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 while an edit is owed)")
    args = ap.parse_args()
    owed: list[str] = []
    done: list[str] = []

    version, pins, servers = _pyproject()
    if version != _VERSION:
        _refuse(f"pyproject.toml declares {version}, not {_VERSION} -- run this on the proposal branch")
    for table in (_MATRIX_FLOORS, _OTHER_PINS):
        for pkg, spec in table.items():
            if pins.get(pkg) != spec:
                _refuse(f"pyproject.toml pins {pkg}{pins.get(pkg, ' (absent)')}, expected {pkg}{spec}")
    if servers != _SERVERS:
        _refuse(f"pyproject.toml's [servers] is {servers}, expected {_SERVERS}")
    for sentence in (_SENTENCE_OLD, _SENTENCE_NEW):
        if "\n" in sentence:
            _refuse("the compatibility sentence must stay one physical line")

    reference_original = _REFERENCE.read_text(encoding="utf-8")
    reference = reference_original
    row = _render_row("0.11.x", [pins[pkg] for pkg in _MATRIX_FLOORS])
    if row != _ROW or reference.count(_ROW) != 1:
        _refuse(f"the 0.11.x row rendered from pyproject.toml is\n  {row}\nbut docs/REFERENCE.md must hold\n  {_ROW}\nexactly once (found {reference.count(_ROW)})")
    done.append("docs/REFERENCE.md 0.11.x matrix row (juniper-ml#2555 moved its observability cell; the cut changes nothing in it)")
    reference = _replace_once(reference, _VERSION_CELL_OLD, _VERSION_CELL_NEW, "docs/REFERENCE.md Package Overview Version cell", owed, done)
    reference = _replace_once(reference, _SENTENCE_OLD, _SENTENCE_NEW, "docs/REFERENCE.md compatibility sentence", owed, done)
    if _INTERIM_MARKER in reference:
        _refuse(f"docs/REFERENCE.md still says {_INTERIM_MARKER!r} after the edit ({reference.count(_INTERIM_MARKER)} time(s))")
    declares = [line for line in reference.split("\n") if "declares the following pins." in line]
    if len(declares) != 1 or declares[0] != _SENTENCE_NEW or declares[0].count(" sets them to ") != 1 or f"{_VERSION} sets them to " not in declares[0]:
        _refuse("docs/REFERENCE.md: the 'declares' sentence and its one 'sets them to' clause are not one line naming this release")

    changelog_original, changelog = _changelog(owed, done)

    for site in done:
        print(f"  = {site}: already at target")
    for site in owed:
        print(f"  ~ {site}: {'owed' if args.check else 'written'}")
    if args.check:
        print("--check: nothing written")
        return 1 if owed else 0
    if reference != reference_original:
        _REFERENCE.write_text(reference, encoding="utf-8")
    if changelog != changelog_original:
        _CHANGELOG.write_text(changelog, encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        _status = main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001 -- a malformed input is a refusal (exit 2), never "an edit is owed" (exit 1)
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    raise SystemExit(_status)
