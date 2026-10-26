#!/usr/bin/env python3
"""juniper-ml#2062, option (a+): [servers] requests each server's own client and [api] extras.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — migration
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2062 (the defect, and options (a) / (b) / (c)); the owner chose (a+) on 2026-10-25,
         which is (a) plus `[api]` for cascor and data; juniper-ml#2326 (the floors this keeps);
         util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py (the edit pattern)

Why this exists
---------------
``[servers]`` installed ``juniper-canopy``, ``juniper-cascor`` and ``juniper-data`` bare. canopy declares
both clients only as extras (``[juniper-cascor]``, ``[juniper-data]``), and cascor its data client
(``[juniper-data]``). So a ``[servers]`` install started three services that failed at their first
cross-service call. cascor and data also keep their web runtime -- fastapi, starlette, uvicorn,
pydantic-settings -- behind ``[api]``, which arrived only because canopy's base dependencies carry
it. data's ``[api]`` also holds its two security floors.

This is a script, not a hand edit, so the change can be replayed on a newer ``main``: the owner ruled
that it must not ride juniper-ml 0.11.2, so the PR is re-cut on top of the 0.11.2 proposal before it
merges. Every edit asserts its exact old text and must match exactly once. A site already at its
target is skipped, so a re-run is a no-op. ``AGENTS.md``'s ``**Last Updated**:`` is set to the run's
UTC date.

Usage
-----
    python3 util/ad-hoc/2026-10-25_servers_own_extras_ml2062.py [--check]

Then regenerate README's compatibility table (this script teaches the generator the extras marker):
    python3 util/ad-hoc/2026-09-21_sync_readme_compat_table.py
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

#: (bare pin on main, pin with the server's own extras)
_PINS: list[tuple[str, str]] = [
    ("juniper-canopy>=0.9.0", "juniper-canopy[juniper-cascor,juniper-data]>=0.9.0"),
    ("juniper-cascor>=0.12.0", "juniper-cascor[api,juniper-data]>=0.12.0"),
    ("juniper-data>=0.17.1", "juniper-data[api]>=0.17.1"),
]

_OLD_SERVERS_BLOCK = "servers = [\n" + "".join(f'    "{old}",\n' for old, _ in _PINS) + "]\n"
_NEW_SERVERS_BLOCK = (
    "# Each server is requested WITH the extras that make it run as a service (juniper-ml#2062):\n"
    "# canopy's two client extras, cascor's data-client extra, and the [api] web runtime\n"
    "# (fastapi, starlette, uvicorn, pydantic-settings) that cascor and data declare. Requested\n"
    "# bare, the three services started and failed at their first cross-service call. torch stays\n"
    "# out: cascor's [ml] and canopy's [demo] are deliberately not requested.\n"
    "servers = [\n" + "".join(f'    "{new}",\n' for _, new in _PINS) + "]\n"
)

_OLD_EXPECTED = '    "servers": {\n' + "".join(f'        "{old}",\n' for old, _ in _PINS) + "    },\n"
_NEW_EXPECTED = '    "servers": {\n' + "".join(f'        "{new}",\n' for _, new in _PINS) + "    },\n"

_TEST = "tests/test_pyproject_extras.py"
_SYNC = "util/ad-hoc/2026-09-21_sync_readme_compat_table.py"
_SELF = "util/ad-hoc/2026-10-25_servers_own_extras_ml2062.py"

#: (path, exact old text, exact new text) -- each old text must occur exactly once.
_EDITS: list[tuple[str, str, str]] = [
    ("pyproject.toml", _OLD_SERVERS_BLOCK, _NEW_SERVERS_BLOCK),
    (_TEST, _OLD_EXPECTED, _NEW_EXPECTED),
    # The three docs-table parsers learn a PEP 508 extras marker.
    (
        _TEST,
        '# Full pin inside backticks: `juniper-foo>=0.1.0,<0.2.0`\n_INLINE_PIN_RE = re.compile(r"`(juniper-[a-z0-9-]+>=[^`]+)`")\n',
        "# Full pin inside backticks: `juniper-foo>=0.1.0,<0.2.0`, optionally with a PEP 508 extras marker:\n"
        "# `juniper-foo[bar,baz]>=0.1.0` (juniper-ml#2062 put three in [servers]).\n"
        '_INLINE_PIN_RE = re.compile(r"`(juniper-[a-z0-9-]+(?:\\[[a-z0-9,-]+\\])?>=[^`]+)`")\n',
    ),
    (
        _TEST,
        '_REFERENCE_ROW_RE = re.compile(r"^\\|\\s*(?:`(?P<extra>[a-z0-9-]+)`)?\\s*\\|\\s*`(?P<pkg>juniper-[a-z0-9-]+)`" r"[^|]*\\|\\s*`(?P<spec>[^`]+)`\\s*\\|")\n',
        '_REFERENCE_ROW_RE = re.compile(r"^\\|\\s*(?:`(?P<extra>[a-z0-9-]+)`)?\\s*\\|\\s*`(?P<pkg>juniper-[a-z0-9-]+(?:\\[[a-z0-9,-]+\\])?)`" r"[^|]*\\|\\s*`(?P<spec>[^`]+)`\\s*\\|")\n',
    ),
    (
        _TEST,
        '# README "Ecosystem Compatibility" two-column row: | `juniper-foo` | `>=1.2.3` |\n_COMPAT_ROW_RE = re.compile(r"^\\|\\s*`(?P<pkg>juniper-[a-z0-9-]+)`\\s*\\|\\s*`(?P<spec>[^`]+)`\\s*\\|\\s*$")\n',
        '# README "Ecosystem Compatibility" two-column row: | `juniper-foo` | `>=1.2.3` |, where the package\n'
        "# cell keeps an extras marker (`juniper-foo[bar]`), as ReadmeCompatTableTest keys a row by\n"
        "# everything before `>=`.\n"
        '_COMPAT_ROW_RE = re.compile(r"^\\|\\s*`(?P<pkg>juniper-[a-z0-9-]+(?:\\[[a-z0-9,-]+\\])?)`\\s*\\|\\s*`(?P<spec>[^`]+)`\\s*\\|\\s*$")\n'
        "# A requirement's name and its optional extras marker, for the [servers] contract test.\n"
        '_REQUIREMENT_EXTRAS_RE = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?:\\[(?P<extras>[^\\]]*)\\])?")\n',
    ),
    # The contract test, after test_version_is_semver_ish.
    (
        _TEST,
        '            self.assertTrue(head.isdigit(), f"version component {part!r} (from {version!r}) is not numeric")\n\n\ndef _pins_from_compat_table',
        '            self.assertTrue(head.isdigit(), f"version component {part!r} (from {version!r}) is not numeric")\n'
        "\n"
        "    def test_servers_requests_what_each_server_needs_to_run(self) -> None:\n"
        '        """juniper-ml#2062: `[servers]` must request each server\'s client and `[api]` extras, and no torch.\n'
        "\n"
        "        `[servers]` used to install juniper-canopy, juniper-cascor and juniper-data bare. canopy's\n"
        "        service mode then died importing `juniper_cascor_client`, and cascor's dataset fetch on a\n"
        "        missing juniper-data-client. The web runtime cascor and data declare under `[api]` arrived\n"
        "        only because canopy's base dependencies happen to carry it. EXPECTED_EXTRAS pins the exact\n"
        "        strings; this names the reason, so an edit that drops a bracket fails with it attached.\n"
        '        """\n'
        "        required = {\n"
        '            "juniper-canopy": {"juniper-cascor", "juniper-data"},\n'
        '            "juniper-cascor": {"api", "juniper-data"},\n'
        '            "juniper-data": {"api"},\n'
        "        }\n"
        "        # cascor's [ml] and canopy's [demo] pull torch; docs/QUICK_START.md promises [servers] has none.\n"
        '        torch_extras = {"juniper-canopy": {"demo"}, "juniper-cascor": {"ml"}}\n'
        "        requested: dict[str, set[str]] = {}\n"
        '        for member in self.extras["servers"]:\n'
        "            match = _REQUIREMENT_EXTRAS_RE.match(member)\n"
        '            self.assertIsNotNone(match, f"unparsable [servers] member {member!r}")\n'
        "            assert match is not None\n"
        '            extras = match.group("extras") or ""\n'
        '            requested[match.group("name")] = {e.strip() for e in extras.split(",") if e.strip()}\n'
        "        for name, needs in required.items():\n"
        "            with self.subTest(server=name):\n"
        '                self.assertIn(name, requested, f"[servers] no longer requests {name}")\n'
        "                missing = needs - requested[name]\n"
        '                self.assertFalse(missing, f"[servers] requests {name} without its {sorted(missing)} extra(s) (juniper-ml#2062)")\n'
        "                torch = torch_extras.get(name, set()) & requested[name]\n"
        '                self.assertFalse(torch, f"[servers] must stay torch-free, but requests {name}{sorted(torch)}")\n'
        "\n"
        "\n"
        "def _pins_from_compat_table",
    ),
    # The parser test, after test_inline_parser_detects_stale_tools_ceiling.
    (
        _TEST,
        '        self.assertNotEqual(parsed["tools"], self.pyproject_pins["tools"])\n\n\nclass ReadmeCompatTableTest',
        '        self.assertNotEqual(parsed["tools"], self.pyproject_pins["tools"])\n'
        "\n"
        "    def test_parsers_keep_an_extras_marker(self) -> None:\n"
        '        """Synthetic: a `pkg[extra,...]` pin parses whole in all three table shapes (juniper-ml#2062).\n'
        "\n"
        "        Before the parsers knew the marker, `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0` matched\n"
        "        nothing, and a row the parser cannot see reads as an extras set that drifted.\n"
        '        """\n'
        '        inline = "| `servers` | `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0`, `juniper-data[api]>=0.17.1` |\\n"\n'
        "        self.assertEqual(\n"
        '            _pins_from_inline_extras_table(inline)["servers"],\n'
        '            {"juniper-canopy[juniper-cascor,juniper-data]>=0.9.0", "juniper-data[api]>=0.17.1"},\n'
        "        )\n"
        '        reference = "### Available Extras\\n\\n| `servers`   | `juniper-cascor[api,juniper-data]` | `>=0.12.0` |\\n"\n'
        '        self.assertEqual(_pins_from_reference_extras_table(reference)["servers"], {"juniper-cascor[api,juniper-data]>=0.12.0"})\n'
        '        compat = "| `juniper-data[api]` | `>=0.17.1` |\\n"\n'
        '        self.assertEqual(_pins_from_compat_table(compat), {"juniper-data[api]": ">=0.17.1"})\n'
        "\n"
        "\n"
        "class ReadmeCompatTableTest",
    ),
    # The synthetic stale-row test keyed canopy's row by the bare name; the row is now keyed with its marker.
    (
        _TEST,
        '        stale = "| Package | Pin |\\n|---|---|\\n| `juniper-canopy` | `>=0.5.0` |\\n"\n'
        "        parsed = _pins_from_compat_table(stale)\n"
        '        self.assertEqual(parsed, {"juniper-canopy": ">=0.5.0"})\n'
        '        self.assertNotEqual(parsed.get("juniper-canopy"), self.expected["juniper-canopy"])\n',
        '        canopy = "juniper-canopy[juniper-cascor,juniper-data]"\n'
        '        stale = f"| Package | Pin |\\n|---|---|\\n| `{canopy}` | `>=0.5.0` |\\n"\n'
        "        parsed = _pins_from_compat_table(stale)\n"
        "        self.assertEqual(parsed, {canopy: \">=0.5.0\"})\n"
        "        self.assertNotEqual(parsed.get(canopy), self.expected[canopy])\n",
    ),
    # The README compatibility-table generator keeps the marker with the package, and sorts on the
    # bare name so `juniper-cascor[...]` stays ahead of `juniper-cascor-client`.
    (
        _SYNC,
        '_SPEC_RE = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?P<spec>.*)$")\n',
        "# A PEP 508 extras marker stays with the package (juniper-ml#2062): ReadmeCompatTableTest keys a\n"
        "# row by everything before `>=`, so `juniper-data[api]` is the package and `>=0.17.1` the pin.\n"
        '_SPEC_RE = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+(?:\\[[^\\]]*\\])?)(?P<spec>.*)$")\n',
    ),
    (
        _SYNC,
        "    for pkg in sorted(pins):\n",
        "    # Sort on the bare name, so `juniper-cascor[api,...]` stays ahead of `juniper-cascor-client`.\n"
        '    for pkg in sorted(pins, key=lambda name: (name.split("[", 1)[0], name)):\n',
    ),
    # Prose that says what [servers] installs.
    (
        "README.md",
        "pip install juniper-ml[servers]        # juniper-canopy + juniper-cascor + juniper-data\n",
        "pip install juniper-ml[servers]        # juniper-canopy + juniper-cascor + juniper-data, with the clients they call\n",
    ),
    (
        "AGENTS.md",
        'pip install -e ".[servers]"    # canopy + cascor + data service packages\n',
        'pip install -e ".[servers]"    # canopy + cascor + data services, with their clients\n',
    ),
    (
        "docs/QUICK_START.md",
        "# Server packages (juniper-canopy + juniper-cascor + juniper-data)\n",
        "# Server packages (juniper-canopy + juniper-cascor + juniper-data, with the clients they call)\n",
    ),
    # The size note was stale before this change (measured 2026-10-25), and the fix touches its sentence.
    (
        "docs/QUICK_START.md",
        "> Callers who do not need the worker or server distributions should prefer a narrower extra: `[clients]`, `[tools]`, and `[doc-tools]` each resolve to under 50 MB; `[servers]` is under 200 MB (no torch).",
        "> Callers who do not need the worker or server distributions should prefer a narrower extra. Measured on disk on 2026-10-25 (Python 3.12, Linux x86_64, pip itself excluded): `[doc-tools]` is about 1 MB, `[clients]` about 85 MB and `[tools]` about 91 MB. `[servers]` is about 410 MB, with no torch: it requests each server's client and `[api]` extras, never cascor's `[ml]` or canopy's `[demo]`. scipy, plotly, numpy and dash are about three quarters of it.",
    ),
    (
        "docs/REFERENCE.md",
        "pip install juniper-ml[servers]   # Canopy + Cascor + Data services\n",
        "pip install juniper-ml[servers]   # Canopy + Cascor + Data services, with their clients\n",
    ),
    (
        "docs/REFERENCE.md",
        "that `[all]` aggregates every non-alias extra exactly once, and that `[project].version` is semver-ish.",
        "that `[all]` aggregates every non-alias extra exactly once, that `[servers]` requests each server's client and `[api]` extras and no torch-pulling one (juniper-ml#2062), and that `[project].version` is semver-ish.",
    ),
    (
        "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
        "| Install just the service distributions: canopy + cascor + data (editable) |",
        "| Install just the service distributions: canopy + cascor + data, with their clients (editable) |",
    ),
    (
        "docs/DOCUMENTATION_OVERVIEW.md",
        "juniper-ml[servers]    ──> juniper-canopy, juniper-cascor, juniper-data\n",
        "juniper-ml[servers]    ──> juniper-canopy, juniper-cascor, juniper-data\n                           (with their client and [api] extras; no torch)\n",
    ),
]

#: The comma-joined extras tables: one `servers` row each, rewritten cell-wise to keep the width.
_INLINE_TABLES = ("README.md", "AGENTS.md", "docs/QUICK_START.md")
_OLD_INLINE = ", ".join(f"`{old}`" for old, _ in _PINS)
_NEW_INLINE = ", ".join(f"`{new}`" for _, new in _PINS)

#: docs/REFERENCE.md's split-column extras table: the package cell gains the marker.
_REFERENCE_CELLS = [(f"`{old.split('>=')[0]}`", f"`{new.split('>=')[0]}`", f"`>={old.split('>=')[1]}`") for old, new in _PINS]

_ENTRY_MARKER = "`[servers]` installs what each server needs to run as a service"
_CL_ENTRY = f"""- **{_ENTRY_MARKER}** (juniper-ml#2062; option (a+), owner ruling 2026-10-25).
  `[servers]` installed `juniper-canopy`, `juniper-cascor` and `juniper-data` bare, but canopy declares both clients and
  cascor its data client only as extras. So the three services started and failed at their first cross-service call:
  canopy's service mode on `ModuleNotFoundError: No module named 'juniper_cascor_client'`, and cascor's dataset fetch on
  `RuntimeError("juniper-data-client is not installed; cannot reload dataset")`. `[all]` was not affected, because it
  also installs `[clients]`.
  - `[servers]` now requests `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0`,
    `juniper-cascor[api,juniper-data]>=0.12.0` and `juniper-data[api]>=0.17.1`. Each client comes from its server's own
    extra, inside that server's caps (canopy's `juniper-cascor-client<0.9.0` and `juniper-data-client<0.7.0`), not
    from `[clients]`'s floors.
  - `[api]` is cascor's and data's web runtime (fastapi, starlette, uvicorn, pydantic-settings). It used to arrive only
    through canopy's base dependencies, so cascor's and data's own lower bounds were never applied. data's `[api]` also
    carries its `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1` floors, which `[servers]` now applies
    for the first time.
  - torch stays out: cascor's `[ml]` and canopy's `[demo]` are not requested.
  - **Pre-flighted against real PyPI** with `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`. `[servers]`
    resolves in 63 packages on Python 3.12, 3.13 and 3.14, up from 61; the two added are juniper-cascor-client 0.8.0
    and juniper-data-client 0.6.0. `[all]` is unchanged at 95.
  - **Verified on the built wheel** by `util/ad-hoc/2026-10-25_verify_servers_extras_ml2062.bash`. It runs
    `util/ad-hoc/2026-09-21_decision11_wheel_contract_probe.py` in two clean Python 3.12 venvs with CPU torch, one
    with the published 0.11.1's `[servers]` and one with this change's.
    - With 0.11.1, JD-8, CC-2 and CC-3 SKIP on `No module named 'juniper_data_client'`, and CP-1 reports
      `backend.service_backend` not importable (`No module named 'juniper_cascor_client'`).
    - With this change, all four pass and `service_backend` imports. CP-1 is a defect probe that records PASS either
      way, so its text is the measurement.
  - **`docs/QUICK_START.md`'s install sizes were stale before this change.** Measured on disk on 2026-10-25 (Python 3.12,
    Linux x86_64, pip excluded), `[servers]` is about 410 MB both at 0.11.1 and with this change (+1 MB, the two
    clients), not "under 200 MB". `[clients]` is 85 MB and `[tools]` 91 MB, not "under 50 MB", and `[doc-tools]` is
    about 1 MB. The note now gives the measured sizes.
  - `tests/test_pyproject_extras.py` pins the contract (`test_servers_requests_what_each_server_needs_to_run`), and its
    three docs-table parsers now read a PEP 508 extras marker (`test_parsers_keep_an_extras_marker`).
    `{_SYNC}` keeps the marker with the package in README's compatibility table.
  - Applied by `{_SELF}`, which asserts each site's exact text and requires exactly one match apiece.
"""


def _apply(text: str, old: str, new: str, where: str, check: bool) -> tuple[str, bool]:
    # The new text first: some edits only append to the old text, which then still matches.
    if new in text:
        print(f"  = {where}: already at target")
        return text, False
    found = text.count(old)
    if found != 1:
        raise SystemExit(f"ERROR: {where}: expected exactly 1 occurrence of {old[:80]!r}, found {found}")
    print(f"  {'~' if check else '+'} {where}: {'WOULD rewrite' if check else 'rewrote'} 1 occurrence")
    return (text if check else text.replace(old, new, 1)), True


def _rewrite_cell(line: str, index: int, content: str) -> str:
    """Replace one ``|``-delimited cell, keeping its width when the new content fits."""
    cells = line.split("|")
    cell = f" {content} "
    cells[index] = cell.ljust(len(cells[index])) if len(cell) <= len(cells[index]) else cell
    return "|".join(cells)


def _inline_table(text: str, where: str, check: bool) -> tuple[str, bool]:
    lines = text.split("\n")
    hits = [i for i, ln in enumerate(lines) if ln.startswith("| `servers`") and _OLD_INLINE in ln]
    done = [i for i, ln in enumerate(lines) if ln.startswith("| `servers`") and _NEW_INLINE in ln]
    if not hits and len(done) == 1:
        print(f"  = {where} [servers row]: already at target")
        return text, False
    if len(hits) != 1:
        raise SystemExit(f"ERROR: {where}: expected exactly 1 `servers` row holding {_OLD_INLINE!r}, found {len(hits)}")
    print(f"  {'~' if check else '+'} {where} [servers row]: {'WOULD rewrite' if check else 'rewrote'}")
    if not check:
        lines[hits[0]] = _rewrite_cell(lines[hits[0]], 2, _NEW_INLINE)
    return "\n".join(lines), True


def _reference_table(text: str, check: bool) -> tuple[str, bool]:
    lines = text.split("\n")
    start = lines.index("### Available Extras")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("### "))
    changed = False
    for old_cell, new_cell, spec_cell in _REFERENCE_CELLS:
        rows = [i for i in range(start, end) if lines[i].count("|") == 4 and lines[i].split("|")[2].strip() == old_cell and lines[i].split("|")[3].strip() == spec_cell]
        done = [i for i in range(start, end) if lines[i].count("|") == 4 and lines[i].split("|")[2].strip() == new_cell]
        where = f"docs/REFERENCE.md [{old_cell}]"
        if not rows and len(done) == 1:
            print(f"  = {where}: already at target")
            continue
        if len(rows) != 1:
            raise SystemExit(f"ERROR: {where}: expected exactly 1 Available Extras row with {spec_cell}, found {len(rows)}")
        print(f"  {'~' if check else '+'} {where}: {'WOULD rewrite' if check else 'rewrote'}")
        if not check:
            lines[rows[0]] = _rewrite_cell(lines[rows[0]], 2, new_cell)
        changed = True
    return "\n".join(lines), changed


_LAST_UPDATED_RE = re.compile(r"^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}$", re.MULTILINE)


def _bump_last_updated(text: str, check: bool) -> tuple[str, bool]:
    today = datetime.now(timezone.utc).date().isoformat()
    found = _LAST_UPDATED_RE.findall(text)
    if len(found) != 1:
        raise SystemExit(f"ERROR: AGENTS.md: expected exactly one '**Last Updated**: YYYY-MM-DD' line, found {len(found)}")
    target = f"**Last Updated**: {today}"
    if found[0] == target:
        print("  = AGENTS.md [Last Updated]: already today's UTC date")
        return text, False
    print(f"  {'~' if check else '+'} AGENTS.md [Last Updated]: {'WOULD set' if check else 'set'} {today}")
    return (text if check else _LAST_UPDATED_RE.sub(target, text, count=1)), True


def _insert_changelog_entry(text: str, check: bool) -> tuple[str, bool]:
    """First entry under [Unreleased]'s ``### Fixed``; creates the heading, or [Unreleased] itself, if absent."""
    if text.count("## [Unreleased]\n") > 1:
        raise SystemExit("ERROR: CHANGELOG.md: more than one '## [Unreleased]' heading")
    if _ENTRY_MARKER in text:
        start = text.find("## [Unreleased]\n")
        if start >= 0 and _ENTRY_MARKER in text[start : text.find("\n## [", start + 1)]:
            print("  = CHANGELOG.md [Unreleased]: entry already present")
            return text, False
        raise SystemExit("ERROR: CHANGELOG.md: the entry exists OUTSIDE [Unreleased]; refusing to add a second")
    if "## [Unreleased]\n" not in text:
        first = text.find("\n## [")
        if first < 0:
            raise SystemExit("ERROR: CHANGELOG.md: no release section to put [Unreleased] above")
        new_text = text[: first + 1] + "## [Unreleased]\n\n### Fixed\n\n" + _CL_ENTRY + "\n" + text[first + 1 :]
        how = "a new [Unreleased] section"
    else:
        start = text.find("## [Unreleased]\n")
        end = text.find("\n## [", start + 1)
        if end < 0:
            raise SystemExit("ERROR: CHANGELOG.md: no released section follows [Unreleased]")
        section = text[start:end]
        if section.count("\n### Fixed\n") > 1:
            raise SystemExit("ERROR: CHANGELOG.md: [Unreleased] has more than one '### Fixed' heading")
        if "\n### Fixed\n" in section:
            anchor = section.index("\n### Fixed\n") + len("\n### Fixed\n")
            if section[anchor : anchor + 1] != "\n":
                raise SystemExit("ERROR: CHANGELOG.md: '### Fixed' in [Unreleased] is not followed by a blank line")
            new_section = section[: anchor + 1] + _CL_ENTRY + "\n" + section[anchor + 1 :]
            how = "first entry under the existing '### Fixed'"
        else:
            # Keep a Changelog order puts Fixed before Security. One blank line on each side of the block.
            security = section.find("\n### Security\n")
            head = section[:security] if security >= 0 else section
            tail = section[security:] if security >= 0 else ""
            new_section = head.rstrip("\n") + "\n\n### Fixed\n\n" + _CL_ENTRY + tail
            how = "a new '### Fixed' heading"
        new_text = text[:start] + new_section + text[end:]
    print(f"  {'~' if check else '+'} CHANGELOG.md [Unreleased]: {'WOULD add' if check else 'added'} the entry as {how}")
    return (text if check else new_text), True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()

    by_file: dict[str, str] = {}

    def text_of(rel: str) -> str:
        if rel not in by_file:
            by_file[rel] = (_REPO / rel).read_text(encoding="utf-8")
        return by_file[rel]

    changed_any = False
    for rel, old, new in _EDITS:
        by_file[rel], did = _apply(text_of(rel), old, new, f"{rel} [{old.strip().splitlines()[0][:60]}]", args.check)
        changed_any |= did
    for rel in _INLINE_TABLES:
        by_file[rel], did = _inline_table(text_of(rel), rel, args.check)
        changed_any |= did
    by_file["docs/REFERENCE.md"], did = _reference_table(text_of("docs/REFERENCE.md"), args.check)
    changed_any |= did
    by_file["CHANGELOG.md"], did = _insert_changelog_entry(text_of("CHANGELOG.md"), args.check)
    changed_any |= did
    by_file["AGENTS.md"], did = _bump_last_updated(text_of("AGENTS.md"), args.check)
    changed_any |= did

    if args.check:
        return 1 if changed_any else 0
    for rel, text in by_file.items():
        (_REPO / rel).write_text(text, encoding="utf-8")
    print(f"\nNow run {_SYNC} to regenerate README's Ecosystem Compatibility table, then the tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
