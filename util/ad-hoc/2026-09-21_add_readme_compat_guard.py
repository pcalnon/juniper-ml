#!/usr/bin/env python3
"""Insert the README "Ecosystem Compatibility" regression guard into tests/test_pyproject_extras.py.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc test wiring
Author:      Paul Calnon
Created:     2026-09-21
Version:     0.1.0
License:     MIT License
Status:      single-use (decision-11 floor record repair)

Why this exists
---------------
The guard is added to an EXISTING suite rather than a new file on purpose: juniper-ml's
CI regression list is hand-maintained in ``.github/workflows/ci.yml``, so a new
``tests/test_*.py`` would sit on disk and never run. Extending a suite already invoked
there needs no CI wiring.

Insertion points are asserted, and the new tests go in BEFORE the ``__main__`` block --
anything appended after it is never collected.

Idempotent: re-running detects the guard is present and exits 0 without writing.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_TEST = _REPO / "tests" / "test_pyproject_extras.py"

_REGEX_BLOCK = '''# README "Ecosystem Compatibility" two-column row: | `juniper-foo` | `>=1.2.3` |
_COMPAT_ROW_RE = re.compile(r"^\\|\\s*`(?P<pkg>juniper-[a-z0-9-]+)`\\s*\\|\\s*`(?P<spec>[^`]+)`\\s*\\|\\s*$")
# The lead-in sentence that introduces that table, naming the package's own version.
_COMPAT_LEAD_RE = re.compile(r"^The pyproject pins matching `juniper-ml` (?P<version>[0-9][^:]*):$", re.MULTILINE)

'''

_PARSER_BLOCK = '''def _pins_from_compat_table(text: str) -> dict[str, str]:
    """Parse README.md's flat "Ecosystem Compatibility" | Package | Pin | table.

    Distinct from the extras tables: this one is keyed by PACKAGE, not by extra, so it
    has its own drift surface. It is the table that reached PyPI stale at 0.8.0 --
    README.md is the long_description, so its rows are what pypi.org serves.
    """
    found: dict[str, str] = {}
    for line in text.splitlines():
        match = _COMPAT_ROW_RE.match(line)
        if match:
            found[match.group("pkg")] = match.group("spec").strip()
    return found


def _compat_table_version(text: str) -> str | None:
    """Return the juniper-ml version named in the table's lead-in sentence, if present."""
    match = _COMPAT_LEAD_RE.search(text)
    return match.group("version").strip() if match else None


'''

_TESTS_BLOCK = '''
class ReadmeCompatTableTest(unittest.TestCase):
    """README's flat pin table must match pyproject, and name the current version.

    Regression guard for the drift that shipped in juniper-ml 0.8.0: the
    "Ecosystem Compatibility" table still advertised the 0.6.0 floors -- five pins
    stale, five packages missing entirely -- and said so in its lead-in sentence,
    while the "Available Extras" table two sections below was correct. Two tables in
    one file, only one of them guarded. Because README.md is the PyPI
    long_description, the stale rows were what pypi.org/project/juniper-ml served.

    Regenerate with util/ad-hoc/2026-09-21_sync_readme_compat_table.py.
    """

    expected: ClassVar[dict[str, str]]
    declared_version: ClassVar[str]
    readme: ClassVar[str]

    @classmethod
    def setUpClass(cls) -> None:
        if sys.version_info < (3, 11):
            raise unittest.SkipTest("tomllib requires Python 3.11+")
        with _PYPROJECT.open("rb") as handle:
            project = tomllib.load(handle)["project"]
        cls.declared_version = project["version"]
        flat: dict[str, str] = {}
        for extra, members in project.get("optional-dependencies", {}).items():
            if extra == "all":
                continue
            for member in members:
                if member.startswith("juniper-ml["):
                    continue
                name, sep, spec = member.partition(">=")
                if not sep:
                    raise AssertionError(f"requirement without a floor: {member!r}")
                flat[name.strip()] = (">=" + spec).strip()
        cls.expected = flat
        cls.readme = (_REPO / "README.md").read_text(encoding="utf-8")

    def test_compat_table_matches_pyproject(self) -> None:
        documented = _pins_from_compat_table(self.readme)
        self.assertEqual(
            set(documented),
            set(self.expected),
            "README.md Ecosystem Compatibility package set drifted from pyproject.toml; " "regenerate with util/ad-hoc/2026-09-21_sync_readme_compat_table.py",
        )
        for pkg, spec in self.expected.items():
            with self.subTest(package=pkg):
                self.assertEqual(documented[pkg], spec, f"README.md pin for {pkg} drifted from pyproject.toml")

    def test_compat_table_lead_in_names_current_version(self) -> None:
        named = _compat_table_version(self.readme)
        self.assertIsNotNone(named, "README.md lost its 'pyproject pins matching' lead-in sentence")
        self.assertEqual(
            named,
            self.declared_version,
            "README.md Ecosystem Compatibility lead-in names a stale juniper-ml version",
        )

    def test_compat_parser_detects_a_stale_row(self) -> None:
        """Synthetic: the parser must surface a drifted pin, not silently match nothing."""
        stale = "| Package | Pin |\\n|---|---|\\n| `juniper-canopy` | `>=0.5.0` |\\n"
        parsed = _pins_from_compat_table(stale)
        self.assertEqual(parsed, {"juniper-canopy": ">=0.5.0"})
        self.assertNotEqual(parsed.get("juniper-canopy"), self.expected["juniper-canopy"])

'''


def main() -> int:
    text = _TEST.read_text(encoding="utf-8")

    if "ReadmeCompatTableTest" in text:
        print("guard already present; nothing to do")
        return 0

    regex_anchor = "_DOCS_INLINE_TABLES = ("
    parser_anchor = "class ExtrasDocsLockstepTest(unittest.TestCase):"
    main_anchor = '\nif __name__ == "__main__":'

    for anchor in (regex_anchor, parser_anchor, main_anchor):
        if anchor not in text:
            print(f"ERROR: anchor not found: {anchor!r}", file=sys.stderr)
            return 1

    text = text.replace(regex_anchor, _REGEX_BLOCK + regex_anchor, 1)
    text = text.replace(parser_anchor, _PARSER_BLOCK + parser_anchor, 1)
    text = text.replace(main_anchor, _TESTS_BLOCK + main_anchor, 1)

    _TEST.write_text(text, encoding="utf-8")
    print(f"inserted ReadmeCompatTableTest into {_TEST.relative_to(_REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
