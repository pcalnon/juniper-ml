"""Lint test: pyproject.toml advertises the expected set of optional
dependency groups, each containing the expected packages, and ``[all]``
recursively bundles every other extra exactly once.

Catches the failure class where an edit to ``[project.optional-dependencies]``
silently drops, mistypes, or fails to roll up an extra. The PR that added
``[servers]`` + ``[tools]`` (juniper-ml#295) had no regression coverage for
this surface; one accidental deletion of ``servers`` from ``[all]`` would
have shipped without test failure.

The test is intentionally schema-strict (asserts the exact set of extras +
the exact set of packages per extra), so adding a new extra requires
updating this file in the same PR. That gate is the point of the lint.

Also pins the documented extras tables (AGENTS.md / README.md /
docs/QUICK_START.md / docs/REFERENCE.md) to the same pin strings — the
drift class that left README / QUICK_START ``tools`` ceilings stale while
pyproject moved (juniper-ml#905 follow-up), and that forces Dependabot-only
pin bumps to fail until a human co-updates both the contract and the docs.

Which pins carry a ``<`` ceiling, and why (APD-ML-001)
------------------------------------------------------
This test asserts the pin strings but says nothing about their *shape*, so the
rule they follow is recorded here and beside the pins themselves in
``pyproject.toml``. Every first-party pin is pre-1.0, so ``>=X.Y.0`` alone
admits the next breaking minor; the ceiling is applied selectively:

* **Ceiling** — shared libraries a consumer imports and must migrate to:
  ``juniper-config-tools``, ``juniper-doc-tools``, ``juniper-model-core``,
  ``juniper-service-core`` and the three ``juniper-recurrence`` packages.
* **No ceiling** — the standalone applications and their clients:
  ``juniper-canopy``, ``juniper-cascor``, ``juniper-data``,
  ``juniper-data-client``, ``juniper-cascor-client``,
  ``juniper-cascor-worker``. Capping these would make juniper-ml gate every
  sibling ``0.y`` release, which the APD-ML-001 ruling weighed and rejected.

**Two pins do not fit, and a reader comparing them to the rule should know it
is not an oversight in this docstring.** ``juniper-ci-tools`` is a shared
library that the rule says should be capped: it *was* capped ``<0.2.0`` when
its extra was added (#293) and lost the ceiling in #295, in the same diff that
folded ``ci-tools`` into ``[tools]`` — while ``doc-tools`` kept its ceiling in
that same PR. ``juniper-observability`` has never carried one.

**Deliberately NOT enforced as an assertion.** Encoding the rule as a test
would turn both exceptions red and force either a dependency change or a
waiver, and the ruling is explicit that the pins stay as they are — the defect
was the silence, not the pins. If the exceptions are ever resolved, an
assertion becomes the right instrument; until then it would fail for a reason
nobody intends to fix.
"""

from __future__ import annotations

import re
import sys
import tomllib
import unittest
from pathlib import Path
from typing import Any, ClassVar


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "pyproject.toml").is_file() and (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate juniper-ml repo root from {here}")


_REPO = _repo_root()
_PYPROJECT = _REPO / "pyproject.toml"

# Full pin inside backticks: `juniper-foo>=0.1.0,<0.2.0`
_INLINE_PIN_RE = re.compile(r"`(juniper-[a-z0-9-]+>=[^`]+)`")
# Extra name in the first table column: | `tools` | … |
_EXTRA_CELL_RE = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|")
# REFERENCE.md three-column row: | [`extra`| ] | `pkg` [(…)] | `>=…` |
_REFERENCE_ROW_RE = re.compile(r"^\|\s*(?:`(?P<extra>[a-z0-9-]+)`)?\s*\|\s*`(?P<pkg>juniper-[a-z0-9-]+)`" r"[^|]*\|\s*`(?P<spec>[^`]+)`\s*\|")

# README "Ecosystem Compatibility" two-column row: | `juniper-foo` | `>=1.2.3` |
_COMPAT_ROW_RE = re.compile(r"^\|\s*`(?P<pkg>juniper-[a-z0-9-]+)`\s*\|\s*`(?P<spec>[^`]+)`\s*\|\s*$")
# The lead-in sentence that introduces that table, naming the package's own version.
_COMPAT_LEAD_RE = re.compile(r"^The pyproject pins matching `juniper-ml` (?P<version>[0-9][^:]*):$", re.MULTILINE)

_DOCS_INLINE_TABLES = (
    _REPO / "AGENTS.md",
    _REPO / "README.md",
    _REPO / "docs" / "QUICK_START.md",
)
_REFERENCE_MD = _REPO / "docs" / "REFERENCE.md"


def _pins_from_inline_extras_table(text: str) -> dict[str, set[str]]:
    """Parse AGENTS / README / QUICK_START extras tables (comma-joined pins)."""
    found: dict[str, set[str]] = {}
    for line in text.splitlines():
        match = _EXTRA_CELL_RE.match(line)
        if match is None:
            continue
        extra = match.group(1)
        if extra == "all":
            continue
        pins = set(_INLINE_PIN_RE.findall(line))
        if not pins:
            continue
        # Prefer the first extras table if a file repeats the heading elsewhere.
        found.setdefault(extra, pins)
    return found


def _pins_from_reference_extras_table(text: str) -> dict[str, set[str]]:
    """Parse docs/REFERENCE.md's three-column Extras Reference table."""
    found: dict[str, set[str]] = {}
    current: str | None = None
    in_section = False
    for line in text.splitlines():
        if line.startswith("### Available Extras"):
            in_section = True
            continue
        if in_section and line.startswith("### "):
            break
        if not in_section:
            continue
        match = _REFERENCE_ROW_RE.match(line)
        if match is None:
            continue
        if match.group("extra"):
            current = match.group("extra")
        if current is None or current == "all":
            continue
        spec = match.group("spec").strip()
        if spec == "--":
            continue
        pin = f"{match.group('pkg')}{spec}"
        found.setdefault(current, set()).add(pin)
    return found


# The canonical extras contract. Updating pyproject.toml without updating
# this table (or vice versa) is the failure mode this lint catches.
EXPECTED_EXTRAS = {
    "clients": {
        "juniper-data-client>=0.5.0",
        "juniper-cascor-client>=0.8.0",
    },
    "worker": {
        "juniper-cascor-worker>=0.4.0",
    },
    "servers": {
        "juniper-canopy>=0.8.1",
        "juniper-cascor>=0.11.0",
        "juniper-data>=0.14.0",
    },
    "tools": {
        "juniper-ci-tools>=0.1.0",
        "juniper-config-tools>=0.1.0,<0.2.0",
        "juniper-doc-tools>=0.1.0,<0.2.0",
        "juniper-model-core>=0.1.0,<0.4.0",
        "juniper-observability>=0.2.0",
        "juniper-service-core>=0.2.0,<0.8.0",
    },
    "doc-tools": {
        "juniper-doc-tools>=0.1.0,<0.2.0",
    },
    "recurrence": {
        "juniper-recurrence-model>=0.3.0,<0.4.0",
        "juniper-recurrence>=0.5.0,<0.6.0",
        "juniper-recurrence-client>=0.3.0,<0.4.0",
    },
    "all": {
        "juniper-ml[clients,worker,servers,tools,recurrence]",
    },
}


class PyprojectExtrasTest(unittest.TestCase):
    """Pin the optional-dependency surface so accidental edits fail loudly."""

    pyproject: ClassVar[dict[str, Any]]
    extras: ClassVar[dict[str, list[str]]]

    @classmethod
    def setUpClass(cls) -> None:
        if sys.version_info < (3, 11):
            raise unittest.SkipTest("tomllib requires Python 3.11+")
        with _PYPROJECT.open("rb") as handle:
            cls.pyproject = tomllib.load(handle)
        cls.extras = cls.pyproject["project"].get("optional-dependencies", {})

    def test_expected_extras_present(self) -> None:
        self.assertEqual(
            set(self.extras.keys()),
            set(EXPECTED_EXTRAS.keys()),
            "pyproject.toml extras set drifted from the lint contract; " "update tests/test_pyproject_extras.py in the same PR as the " "pyproject change so reviewers see the diff.",
        )

    def test_each_extra_has_expected_members(self) -> None:
        for name, expected in EXPECTED_EXTRAS.items():
            with self.subTest(extra=name):
                self.assertEqual(
                    set(self.extras[name]),
                    expected,
                    f"[{name}] member set drifted from the lint contract",
                )

    def test_all_bundles_every_non_all_extra(self) -> None:
        """`[all]` must list every other extra (except itself and the
        back-compat `[doc-tools]` alias, which is already covered by the
        doc-tools member of `[tools]`)."""
        non_all = {n for n in EXPECTED_EXTRAS if n not in {"all", "doc-tools"}}
        (all_recursive_ref,) = self.extras["all"]
        # Parse "juniper-ml[a,b,c]" -> {"a","b","c"}
        self.assertTrue(
            all_recursive_ref.startswith("juniper-ml[") and all_recursive_ref.endswith("]"),
            f"Unexpected [all] recursive ref shape: {all_recursive_ref!r}",
        )
        inner = all_recursive_ref[len("juniper-ml[") : -1]
        referenced = {token.strip() for token in inner.split(",")}
        self.assertEqual(
            referenced,
            non_all,
            "[all] must aggregate every non-alias extra exactly once",
        )

    def test_version_is_semver_ish(self) -> None:
        version = self.pyproject["project"]["version"]
        # X.Y.Z, optionally with a pre-release/build suffix
        parts = version.split(".")
        self.assertGreaterEqual(len(parts), 3, f"version {version!r} is not X.Y.Z[.…]")
        for part in parts[:3]:
            head = part.split("-", 1)[0].split("+", 1)[0]
            self.assertTrue(head.isdigit(), f"version component {part!r} (from {version!r}) is not numeric")


def _pins_from_compat_table(text: str) -> dict[str, str]:
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


class ExtrasDocsLockstepTest(unittest.TestCase):
    """Documented extras tables must match pyproject pin strings exactly."""

    pyproject_pins: ClassVar[dict[str, set[str]]]

    @classmethod
    def setUpClass(cls) -> None:
        if sys.version_info < (3, 11):
            raise unittest.SkipTest("tomllib requires Python 3.11+")
        with _PYPROJECT.open("rb") as handle:
            extras = tomllib.load(handle)["project"].get("optional-dependencies", {})
        cls.pyproject_pins = {name: set(members) for name, members in extras.items() if name != "all"}

    def test_inline_docs_tables_match_pyproject(self) -> None:
        for path in _DOCS_INLINE_TABLES:
            with self.subTest(doc=path.relative_to(_REPO).as_posix()):
                documented = _pins_from_inline_extras_table(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    set(documented.keys()),
                    set(self.pyproject_pins.keys()),
                    f"{path.name}: extras set drifted from pyproject.toml; " "co-update the documented table in the same PR as the pin change",
                )
                for extra, expected in self.pyproject_pins.items():
                    with self.subTest(doc=path.name, extra=extra):
                        self.assertEqual(
                            documented[extra],
                            expected,
                            f"{path.name} [{extra}] pin set drifted from pyproject.toml",
                        )

    def test_reference_extras_table_matches_pyproject(self) -> None:
        documented = _pins_from_reference_extras_table(_REFERENCE_MD.read_text(encoding="utf-8"))
        self.assertEqual(
            set(documented.keys()),
            set(self.pyproject_pins.keys()),
            "docs/REFERENCE.md extras set drifted from pyproject.toml; " "co-update the Extras Reference table in the same PR as the pin change",
        )
        for extra, expected in self.pyproject_pins.items():
            with self.subTest(extra=extra):
                self.assertEqual(
                    documented[extra],
                    expected,
                    f"docs/REFERENCE.md [{extra}] pin set drifted from pyproject.toml",
                )

    def test_inline_parser_detects_stale_tools_ceiling(self) -> None:
        """Synthetic pin: parser must surface the README/QUICK_START drift class."""
        stale = "| Extra | Packages |\n" "|---|---|\n" "| `tools` | `juniper-ci-tools>=0.1.0`, " "`juniper-service-core>=0.2.0,<0.3.0` |\n"
        parsed = _pins_from_inline_extras_table(stale)
        self.assertEqual(
            parsed["tools"],
            {"juniper-ci-tools>=0.1.0", "juniper-service-core>=0.2.0,<0.3.0"},
        )
        self.assertNotEqual(parsed["tools"], self.pyproject_pins["tools"])


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
        stale = "| Package | Pin |\n|---|---|\n| `juniper-canopy` | `>=0.5.0` |\n"
        parsed = _pins_from_compat_table(stale)
        self.assertEqual(parsed, {"juniper-canopy": ">=0.5.0"})
        self.assertNotEqual(parsed.get("juniper-canopy"), self.expected["juniper-canopy"])


if __name__ == "__main__":
    unittest.main()
