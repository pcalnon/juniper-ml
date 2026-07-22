#!/usr/bin/env python3
"""Hermetic regression tests for util/release_train/propose.py + notes_render.py (plan S5.4/S6/S10.1, Phase 2.1).

NO network, NO real gh, NO real pip, NO repo writes. The dup-guard ``gh pr list`` and every
file read run through an injected ``ProposeSources`` seam; version / CHANGELOG / AGENTS.md reads
run against a synthetic on-disk repo built per test (the ``test_release_train_detect.py`` idiom).
The release-notes template is copied into each synthetic tree so rendering is offline and the
"dry-run writes nothing" snapshot is self-contained.

Covers (task acceptance list):
  * a well-formed dry-run proposal for a STATIC-version package and a DYNAMIC-version package
  * CHANGELOG [Unreleased] -> [version] move correctness (fresh empty Unreleased; order preserved)
  * notes render matches the template skeleton + the archive_name convention
    (RELEASE_NOTES_<pkg>_v<version>.md, central home notes/releases/)
  * dup-guard suppression (open release PR already exists) + the -v delimiter disambiguation
  * changelog_conflict refusal path (the detector flagged an inconsistency)
  * dry-run writes NOTHING to the repo (tmpdir tree byte-identical before/after)
  * version-file editors (static pyproject / dynamic _version.py / meta AGENTS.md), propagation
    edges (MINOR escapes ceilings; PATCH does not), and CLI exit codes 0 / 2
  * in-repo meta consumer-pin co-changes (plan S5.4; closes the ml#657 RK-11 gap): an escaping MINOR
    bump emits all three lockstep edits (root pyproject.toml + tests/test_pyproject_extras.py + the
    AGENTS.md extras table) with correct raised ceilings; a non-escaping PATCH bump and a package
    absent from the extras emit ZERO co-changes + the explicit "none needed" body line; the pyproject
    edit round-trips byte-identically (only the ceiling moves); the AGENTS true-up is scoped to the
    extras table (prose / minimum-pin mentions never move) and fixes a drifted row; the meta itself
    yields no self-pin co-change; dry-run with a co-change scenario still writes nothing

``util/`` is not pre-commit-lint-gated, so this unittest IS the gate (the ``env_floor_drift_check``
precedent, shared with ``detect.py``). Imported via the house ``sys.path.insert`` idiom.

Run: python3 -m unittest -v tests/test_release_train_propose.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-07-14
"""

from __future__ import annotations

import difflib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import textwrap
import tomllib
import unittest
from collections import OrderedDict
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UTIL_DIR = REPO_ROOT / "util" / "release_train"
sys.path.insert(0, str(UTIL_DIR))

import detect as d  # noqa: E402
import notes_render as nr  # noqa: E402
import propose as pr  # noqa: E402

REAL_TEMPLATE = REPO_ROOT / "notes" / "templates" / "TEMPLATE_RELEASE_NOTES.md"
REAL_SECURITY_TEMPLATE = REPO_ROOT / "notes" / "templates" / "TEMPLATE_SECURITY_RELEASE_NOTES.md"


# ── helpers ──────────────────────────────────────────────────────────────────


def _entry(**over) -> d.PackageEntry:
    base = {
        "pypi_name": "juniper-thing",
        "repo": "juniper-ml",
        "path": "juniper-thing/",
        "version_source": "static",
        "tag_pattern": "juniper-thing-v*",
        "archive_name": "RELEASE_NOTES_juniper-thing_v{version}.md",
        "trigger": {"now": "release", "target": "release"},
        "verify": {"now": "strict", "target": "strict"},
        "depends_on": [],
        "ship_paths": ["juniper-thing/juniper_thing/"],
        "exclude_paths": [],
    }
    base.update(over)
    return d.PackageEntry(**base)


def _manifest_pkg(**over) -> dict:
    base = {
        "pypi_name": "juniper-thing",
        "repo": "juniper-ml",
        "released_version": "0.4.0",
        "declared_version": "0.4.0",
        "classification": "UNRELEASED_CHANGES",
        "proposed_bump": "minor",
        "proposed_version": "0.5.0",
        "ship_evidence": [{"file": "juniper-thing/juniper_thing/mod.py", "reason": "substantive code hunk"}],
        "changelog_unreleased_categories": ["added"],
        "changelog_conflict": None,
        "propagation_edges": [],
    }
    base.update(over)
    return base


def _write_pkg(repo_root: Path, path: str, *, name: str, version: str, changelog: str = "", dynamic: bool = False, import_pkg: str = "") -> None:
    pkg_dir = repo_root if path == "." else repo_root / path.rstrip("/")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    if dynamic:
        (pkg_dir / "pyproject.toml").write_text(f'[project]\nname = "{name}"\ndynamic = ["version"]\n')
        ip = import_pkg or name.replace("-", "_")
        (pkg_dir / ip).mkdir(parents=True, exist_ok=True)
        (pkg_dir / ip / "_version.py").write_text(f'"""Version."""\n__version__ = "{version}"\n')
    else:
        (pkg_dir / "pyproject.toml").write_text(f'[project]\nname = "{name}"\nversion = "{version}"\ndescription = "x"\n')
    if changelog:
        (pkg_dir / "CHANGELOG.md").write_text(changelog)


def _install_templates(repo_root: Path) -> None:
    dest = repo_root / "notes" / "templates"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(REAL_TEMPLATE, dest / "TEMPLATE_RELEASE_NOTES.md")
    shutil.copy(REAL_SECURITY_TEMPLATE, dest / "TEMPLATE_SECURITY_RELEASE_NOTES.md")


# The meta-package's consumer surface the in-repo pin co-change reads + edits (root pyproject.toml,
# the tests/test_pyproject_extras.py membership contract, and the AGENTS.md "Dependency extras
# reference" table). Exercises: a single-extra ceiling pin (service-core <0.5.0), a floorless pin
# (observability, no ceiling), and a package in TWO extras (doc-tools in [tools] AND [doc-tools]).
_META_PYPROJECT = textwrap.dedent("""\
    [build-system]
    requires = ["setuptools>=61.0", "wheel"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "juniper-ml"
    version = "0.6.0"
    dependencies = []

    [project.optional-dependencies]
    tools = [
        "juniper-service-core>=0.2.0,<0.5.0",
        "juniper-model-core>=0.1.0,<0.4.0",
        "juniper-observability>=0.2.0",
        "juniper-doc-tools>=0.1.0,<0.2.0",
    ]
    doc-tools = [
        "juniper-doc-tools>=0.1.0,<0.2.0",
    ]
    all = [
        "juniper-ml[tools,doc-tools]",
    ]
    """)

_META_TEST_EXTRAS = textwrap.dedent('''\
    """Lint contract mirror (exact-string membership)."""
    EXPECTED_EXTRAS = {
        "tools": {
            "juniper-service-core>=0.2.0,<0.5.0",
            "juniper-model-core>=0.1.0,<0.4.0",
            "juniper-observability>=0.2.0",
            "juniper-doc-tools>=0.1.0,<0.2.0",
        },
        "doc-tools": {
            "juniper-doc-tools>=0.1.0,<0.2.0",
        },
        "all": {
            "juniper-ml[tools,doc-tools]",
        },
    }
    ''')

# The AGENTS table row for `tools` plus a `doc-tools` row (doc-tools in two rows) AND a prose pin
# OUTSIDE the table that must never move (the ml#657 scoping hazard: a `juniper-observability>=0.2.0`
# minimum-pin note and a `juniper-service-core` bare mention live elsewhere in the real AGENTS.md).
_META_AGENTS = textwrap.dedent("""\
    # AGENTS

    **Version**: 0.6.0

    ## Shared Observability Helpers

    Minimum pin: `juniper-observability>=0.2.0`. Do not move this prose mention.

    ### Dependency extras reference

    | Extra       | Packages                                                                                                                                              |
    |-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
    | `tools`     | `juniper-service-core>=0.2.0,<0.5.0`, `juniper-model-core>=0.1.0,<0.4.0`, `juniper-observability>=0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`            |
    | `doc-tools` | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`)                                                              |

    ## Conventions

    A prose pin that must NOT be edited: `juniper-service-core>=0.2.0,<0.5.0`.
    """)


def _write_meta_surface(repo_root: Path) -> None:
    """Write the meta-package's root pyproject.toml + tests/test_pyproject_extras.py + AGENTS.md so
    build_proposal's in-repo consumer-pin co-change (step 5b) can read + edit the real three files."""
    (repo_root / "pyproject.toml").write_text(_META_PYPROJECT)
    (repo_root / "tests").mkdir(parents=True, exist_ok=True)
    (repo_root / "tests" / "test_pyproject_extras.py").write_text(_META_TEST_EXTRAS)
    (repo_root / "AGENTS.md").write_text(_META_AGENTS)


_CHANGELOG = textwrap.dedent("""\
    # Changelog

    ## [Unreleased]

    ### Added

    - new validation module for the thing

    ### Fixed

    - a latent off-by-one in the parser

    ## [0.4.0] - 2026-06-01

    ### Added

    - initial release
    """)


class _FakeSources:
    """Assemble a ProposeSources with a disk-backed read_file over the synthetic tree and an
    in-memory open-PR list for the dup-guard. write/git/pr are None (dry-run/tests never mutate)."""

    def __init__(self, repo_root: Path, ecosystem_root: Path):
        self.repo_root = repo_root
        self.ecosystem_root = ecosystem_root
        self.open_prs: dict = {}

    def read_file(self, entry, filename):
        base = d.base_dir_for(entry, self.repo_root, self.ecosystem_root)
        try:
            return (base / filename).read_text(encoding="utf-8")
        except OSError:
            return None

    def build(self) -> pr.ProposeSources:
        return pr.ProposeSources(read_file=self.read_file, list_open_prs=lambda repo: list(self.open_prs.get(repo, [])))


def _sha_tree(root: Path) -> dict:
    """relpath -> sha256 for every file under root (the writes-nothing snapshot)."""
    out: dict = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# ── notes_render ─────────────────────────────────────────────────────────────


class NotesRenderTest(unittest.TestCase):
    def test_archive_name_convention(self):
        self.assertEqual(nr.archive_name("juniper-observability", "0.4.1"), "RELEASE_NOTES_juniper-observability_v0.4.1.md")
        self.assertEqual(nr.archive_name("juniper-ml", "0.7.0"), "RELEASE_NOTES_v0.7.0.md")  # meta special-case
        self.assertEqual(nr.archive_relpath("juniper-observability", "0.4.1"), "notes/releases/RELEASE_NOTES_juniper-observability_v0.4.1.md")

    def test_parse_unreleased_groups_bullets_by_category(self):
        sections = nr.parse_unreleased(_CHANGELOG)
        self.assertEqual(list(sections), ["Added", "Fixed"])  # order + casing preserved; released 0.4.0 not included
        self.assertIn("new validation module for the thing", sections["Added"][0])
        self.assertIn("off-by-one", sections["Fixed"][0])

    def test_render_matches_template_skeleton_and_names(self):
        sections = nr.parse_unreleased(_CHANGELOG)
        text = nr.render_notes("juniper-thing", "0.5.0", bump="minor", release_date="2026-07-14", sections=sections, repo_root=REPO_ROOT)
        # metadata block + core template sections present
        self.assertIn("# juniper-thing v0.5.0 Release Notes", text)
        self.assertIn("**Release Date:** 2026-07-14", text)
        self.assertIn("**Version:** 0.5.0", text)
        self.assertIn("**Release Type:** MINOR", text)
        for heading in ("## Overview", "## Release Summary", "## What's New", "### Added", "### Fixed"):
            self.assertIn(heading, text)
        self.assertIn("new validation module for the thing", text)
        self.assertIn("notes/releases/RELEASE_NOTES_juniper-thing_v0.5.0.md", text)  # archive target named
        # skeleton conformance: every filled section is drawn from the live template's titles
        titles = nr.template_section_titles(REAL_TEMPLATE.read_text(encoding="utf-8"))
        for key in nr.STANDARD_FILLED_SECTIONS:
            self.assertTrue(any(t.startswith(key) for t in titles), f"filled section {key!r} not in template titles {titles}")

    def test_security_release_uses_security_template(self):
        sections = OrderedDict([("Security", ["patched a transitive CVE"]), ("Fixed", ["a bug"])])
        self.assertTrue(nr.is_security_release(sections))
        text = nr.render_notes("juniper-thing", "0.4.1", bump="patch", release_date="2026-07-14", sections=sections, repo_root=REPO_ROOT)
        self.assertIn(":lock: SECURITY PATCH RELEASE", text)
        self.assertIn("## Security Impact", text)
        self.assertIn("## Changes in v0.4.1", text)
        self.assertIn("patched a transitive CVE", text)
        sec_titles = nr.template_section_titles(REAL_SECURITY_TEMPLATE.read_text(encoding="utf-8"))
        for key in nr.SECURITY_FILLED_SECTIONS:
            self.assertTrue(any(t.startswith(key) for t in sec_titles), f"security filled section {key!r} not in {sec_titles}")

    def test_render_wellformed_without_changelog(self):
        text = nr.render_notes("juniper-thing", "0.5.0", release_date="2026-07-14", sections=OrderedDict(), repo_root=REPO_ROOT)
        self.assertIn("# juniper-thing v0.5.0 Release Notes", text)
        self.assertIn("## What's New", text)  # still well-formed with a placeholder body

    def test_cli_print_archive_name(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = nr.main(["--package", "juniper-thing", "--version", "0.5.0", "--print-archive-name"])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "notes/releases/RELEASE_NOTES_juniper-thing_v0.5.0.md")


# ── CHANGELOG move ───────────────────────────────────────────────────────────


class ChangelogMoveTest(unittest.TestCase):
    def test_move_unreleased_correctness(self):
        new_text, reason = pr.move_unreleased(_CHANGELOG, "0.5.0", "2026-07-14")
        self.assertIsNone(reason)
        self.assertIsNotNone(new_text)
        # a fresh empty [Unreleased] remains, a new dated version section is inserted below it
        self.assertIn("## [Unreleased]", new_text)
        self.assertIn("## [0.5.0] - 2026-07-14", new_text)
        # ordering: Unreleased header < new version header < moved bullet < prior 0.4.0 section
        i_unrel = new_text.index("## [Unreleased]")
        i_new = new_text.index("## [0.5.0] - 2026-07-14")
        i_bullet = new_text.index("new validation module for the thing")
        i_old = new_text.index("## [0.4.0] - 2026-06-01")
        self.assertLess(i_unrel, i_new)
        self.assertLess(i_new, i_bullet)
        self.assertLess(i_bullet, i_old)
        # the moved bullet no longer sits inside the (now empty) [Unreleased] block
        unreleased_block = new_text[i_unrel:i_new]
        self.assertNotIn("new validation module", unreleased_block)

    def test_move_refuses_without_unreleased_heading(self):
        _, reason = pr.move_unreleased("# Changelog\n\n## [0.4.0] - 2026-06-01\n- x\n", "0.5.0", "2026-07-14")
        self.assertIsNotNone(reason)

    def test_move_refuses_empty_unreleased(self):
        _, reason = pr.move_unreleased("# Changelog\n\n## [Unreleased]\n\n## [0.4.0] - 2026-06-01\n- x\n", "0.5.0", "2026-07-14")
        self.assertIsNotNone(reason)


# ── version-file editors ─────────────────────────────────────────────────────


class VersionEditTest(unittest.TestCase):
    def test_set_pyproject_version(self):
        text = '[build-system]\nrequires = ["setuptools"]\n\n[project]\nname = "x"\nversion = "0.4.0"\n'
        new_text, old = pr.set_pyproject_version(text, "0.5.0")
        self.assertEqual(old, "0.4.0")
        self.assertIn('version = "0.5.0"', new_text)
        self.assertNotIn('version = "0.4.0"', new_text)

    def test_set_pyproject_version_ignores_other_tables(self):
        # a [tool.poetry] version must not be the one edited; only [project].
        text = '[project]\nname = "x"\nversion = "0.4.0"\n\n[tool.black]\nversion = "should-not-touch"\n'
        new_text, old = pr.set_pyproject_version(text, "0.5.0")
        self.assertEqual(old, "0.4.0")
        self.assertIn('version = "should-not-touch"', new_text)

    def test_set_dynamic_version(self):
        text = '"""m."""\n__version__ = "0.3.0"\n'
        new_text, old = pr.set_dynamic_version(text, "0.4.0")
        self.assertEqual(old, "0.3.0")
        self.assertIn('__version__ = "0.4.0"', new_text)

    def test_set_agents_version(self):
        text = "# AGENTS\n\n**Version**: 0.6.0\n**Author**: x\n"
        new_text, old = pr.set_agents_version(text, "0.7.0")
        self.assertEqual(old, "0.6.0")
        self.assertIn("**Version**: 0.7.0", new_text)

    def test_editors_return_none_when_absent(self):
        self.assertIsNone(pr.set_pyproject_version('[project]\nname = "x"\n', "0.5.0")[1])
        self.assertIsNone(pr.set_dynamic_version("x = 1\n", "0.5.0")[1])
        self.assertIsNone(pr.set_agents_version("no header\n", "0.5.0")[1])


# ── dup-guard + propagation ──────────────────────────────────────────────────


class DupGuardAndPropagationTest(unittest.TestCase):
    def test_find_existing_release_pr_matches_package_branch(self):
        prs = [{"number": 7, "headRefName": "release/juniper-thing-v0.9.0", "title": "release: thing"}]
        self.assertIsNotNone(pr.find_existing_release_pr(prs, "juniper-thing"))

    def test_dup_guard_delimiter_disambiguates_siblings(self):
        # an open cascor release PR must NOT dup-guard cascor-model (the -v delimiter).
        prs = [{"number": 8, "headRefName": "release/juniper-cascor-v0.5.1"}]
        self.assertIsNone(pr.find_existing_release_pr(prs, "juniper-cascor-model"))
        self.assertIsNotNone(pr.find_existing_release_pr(prs, "juniper-cascor"))

    def test_propagation_minor_lists_consumers_patch_does_not(self):
        entries = [
            _entry(pypi_name="juniper-model-core", path="juniper-model-core/"),
            _entry(pypi_name="juniper-service-core", path="juniper-service-core/", depends_on=["juniper-model-core"]),
            _entry(pypi_name="juniper-recurrence-model", path="rm/", depends_on=["juniper-model-core"]),
        ]
        mc = entries[0]
        minor = pr.propagation_edges(entries, mc, "minor")
        self.assertEqual({e["consumer"] for e in minor}, {"juniper-service-core", "juniper-recurrence-model"})
        self.assertEqual(pr.propagation_edges(entries, mc, "patch"), [])  # PATCH stays within ceilings


# ── build_proposal: static / dynamic dry-run + refusals ──────────────────────


class BuildProposalTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        self.eco = self.root
        self.fake = _FakeSources(self.repo_root, self.eco)

    def tearDown(self):
        self._tmp.cleanup()

    def test_static_package_dry_run_is_wellformed(self):
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual(prop.branch, "release/juniper-thing-v0.5.0")
        self.assertEqual(prop.pr_title, "release: juniper-thing v0.5.0 (proposal)")
        self.assertIn("chore(release): juniper-thing v0.5.0", prop.commit_message)
        paths = {e.path for e in prop.edits}
        self.assertIn("juniper-thing/pyproject.toml", paths)
        self.assertIn("juniper-thing/CHANGELOG.md", paths)
        vedit = next(e for e in prop.edits if e.path == "juniper-thing/pyproject.toml")
        self.assertIn('version = "0.5.0"', vedit.new_text)
        self.assertIn('version = "0.4.0"', vedit.old_text)
        self.assertEqual(prop.notes_relpath, "notes/releases/RELEASE_NOTES_juniper-thing_v0.5.0.md")
        self.assertIn("# juniper-thing v0.5.0 Release Notes", prop.notes_draft or "")
        self.assertIn("Release proposal", prop.pr_body or "")
        # the drafted notes are NOT presented as a repo edit (archival is the later exempt step)
        self.assertNotIn(prop.notes_relpath, paths)

    def test_dynamic_package_edits_version_file(self):
        _write_pkg(self.repo_root, "juniper-model-core/", name="juniper-model-core", version="0.3.0", changelog=_CHANGELOG, dynamic=True, import_pkg="juniper_model_core")
        entry = _entry(pypi_name="juniper-model-core", path="juniper-model-core/", version_source="dynamic", tag_pattern="juniper-model-core-v*", archive_name="RELEASE_NOTES_juniper-model-core_v{version}.md", ship_paths=["juniper-model-core/juniper_model_core/"])
        pkg = _manifest_pkg(pypi_name="juniper-model-core", released_version="0.3.0", declared_version="0.3.0", proposed_version="0.4.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        vpath = "juniper-model-core/juniper_model_core/_version.py"
        vedit = next(e for e in prop.edits if e.path == vpath)
        self.assertIn('__version__ = "0.4.0"', vedit.new_text)
        self.assertNotIn('__version__ = "0.3.0"', vedit.new_text)

    def test_meta_package_co_changes_agents_md(self):
        _write_pkg(self.repo_root, ".", name="juniper-ml", version="0.6.0", changelog=_CHANGELOG)
        (self.repo_root / "AGENTS.md").write_text("# AGENTS\n\n**Version**: 0.6.0\n**Author**: Paul\n")
        entry = _entry(pypi_name="juniper-ml", path=".", tag_pattern="v*", archive_name="RELEASE_NOTES_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-ml", released_version="0.6.0", declared_version="0.6.0", proposed_version="0.7.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        agents = next((e for e in prop.edits if e.path == "AGENTS.md"), None)
        self.assertIsNotNone(agents, "meta bump must co-change AGENTS.md **Version**")
        self.assertIn("**Version**: 0.7.0", agents.new_text)
        self.assertTrue(any("AGENTS.md" in item for item in prop.co_change_checklist))

    def test_minor_bump_emits_propagation_checklist_item(self):
        _write_pkg(self.repo_root, "juniper-model-core/", name="juniper-model-core", version="0.3.0", changelog=_CHANGELOG, dynamic=True, import_pkg="juniper_model_core")
        mc = _entry(pypi_name="juniper-model-core", path="juniper-model-core/", version_source="dynamic")
        consumer = _entry(pypi_name="juniper-service-core", path="juniper-service-core/", depends_on=["juniper-model-core"])
        pkg = _manifest_pkg(pypi_name="juniper-model-core", released_version="0.3.0", declared_version="0.3.0", proposed_version="0.4.0")
        prop = pr.build_proposal(mc, pkg, self.fake.build(), self.repo_root, self.eco, [mc, consumer], "2026-07-14")
        self.assertEqual({e["consumer"] for e in prop.propagation_edges}, {"juniper-service-core"})
        self.assertTrue(any("propagation" in item.lower() for item in prop.co_change_checklist))

    def test_dup_guard_suppresses_proposal(self):
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        self.fake.open_prs["juniper-ml"] = [{"number": 42, "headRefName": "release/juniper-thing-v0.5.0", "title": "release: thing"}]
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("dup-guard", prop.skipped_reason)
        self.assertEqual(prop.edits, [])  # nothing computed once suppressed
        self.assertIsNotNone(prop.existing_pr)

    def test_changelog_conflict_is_refused(self):
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        entry = _entry()
        pkg = _manifest_pkg(changelog_conflict="UNRELEASED_CHANGES but CHANGELOG [Unreleased] has no feature/fix bullets")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("changelog conflict", prop.skipped_reason)
        self.assertEqual(prop.edits, [])


# ── in-repo meta consumer-pin co-changes: pure helpers (plan S5.4; ml#657 RK-11 gap) ─────


class ConsumerPinHelperTest(unittest.TestCase):
    def test_requirement_names_package(self):
        self.assertTrue(pr.requirement_names_package("juniper-service-core>=0.2.0,<0.5.0", "juniper-service-core"))
        self.assertTrue(pr.requirement_names_package("juniper-observability>=0.2.0", "juniper-observability"))  # floorless still names it
        # the [all] recursive self-ref names extras, not a versioned package
        self.assertFalse(pr.requirement_names_package("juniper-ml[clients,worker,tools]", "juniper-ml"))
        # a longer package name must not match its prefix
        self.assertFalse(pr.requirement_names_package("juniper-cascor-worker>=0.4.0", "juniper-cascor"))

    def test_next_minor_ceiling(self):
        self.assertEqual(pr.next_minor_ceiling("0.5.0"), "<0.6.0")
        self.assertEqual(pr.next_minor_ceiling("0.5.3"), "<0.6.0")  # patch of a minor still caps at the next minor
        self.assertEqual(pr.next_minor_ceiling("0.9.0"), "<0.10.0")  # multi-digit minor

    def test_raise_requirement_ceiling(self):
        # escaping: 0.5.0 is NOT < 0.5.0 -> raise to <0.6.0
        self.assertEqual(pr.raise_requirement_ceiling("juniper-service-core>=0.2.0,<0.5.0", "0.5.0"), "juniper-service-core>=0.2.0,<0.6.0")
        # non-escaping patch under the ceiling -> no change
        self.assertIsNone(pr.raise_requirement_ceiling("juniper-service-core>=0.2.0,<0.5.0", "0.4.1"))
        # no upper bound -> any higher version still satisfies >=floor
        self.assertIsNone(pr.raise_requirement_ceiling("juniper-ci-tools>=0.1.0", "0.9.0"))
        # a <= ceiling: 0.5.0 <= 0.5.0 satisfies -> no change; 0.5.1 escapes -> raise
        self.assertIsNone(pr.raise_requirement_ceiling("juniper-x>=0.2.0,<=0.5.0", "0.5.0"))
        self.assertEqual(pr.raise_requirement_ceiling("juniper-x>=0.2.0,<=0.5.0", "0.5.1"), "juniper-x>=0.2.0,<0.6.0")

    def test_compute_multi_extra_and_absent_and_meta_self(self):
        # doc-tools is pinned in BOTH [tools] and [doc-tools] -> one co-change per extra
        cc = pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-doc-tools", "0.2.0")
        self.assertEqual({c.extra for c in cc}, {"tools", "doc-tools"})
        self.assertTrue(all(c.new_req == "juniper-doc-tools>=0.1.0,<0.3.0" for c in cc))
        # a package not named in any extra -> zero
        self.assertEqual(pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-config-tools", "0.9.0"), [])
        # the meta-package does not pin ITSELF with a version (only the [all] recursive ref) -> zero
        self.assertEqual(pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-ml", "0.7.0"), [])
        # a floorless pin (observability) escapes no ceiling -> zero
        self.assertEqual(pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-observability", "0.9.0"), [])

    def test_pyproject_edit_round_trips_byte_identical(self):
        cc = pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-service-core", "0.5.0")
        self.assertEqual(len(cc), 1)
        new_text = pr.apply_pin_edits_exact(_META_PYPROJECT, cc)
        # re-parse: the target ceiling is raised, the floor is intact
        after = tomllib.loads(new_text)["project"]["optional-dependencies"]
        self.assertIn("juniper-service-core>=0.2.0,<0.6.0", after["tools"])
        self.assertNotIn("juniper-service-core>=0.2.0,<0.5.0", after["tools"])
        # every OTHER extras entry is byte-identical (floors + siblings untouched)
        before = tomllib.loads(_META_PYPROJECT)["project"]["optional-dependencies"]
        for extra in before:
            unchanged_before = {r for r in before[extra] if "juniper-service-core" not in r}
            unchanged_after = {r for r in after[extra] if "juniper-service-core" not in r}
            self.assertEqual(unchanged_before, unchanged_after, f"[{extra}] sibling entries drifted")
        # exactly ONE textual line differs, and single-digit-minor keeps the byte length
        diff = [ln for ln in difflib.unified_diff(_META_PYPROJECT.splitlines(), new_text.splitlines()) if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
        self.assertEqual(diff, ['-    "juniper-service-core>=0.2.0,<0.5.0",', '+    "juniper-service-core>=0.2.0,<0.6.0",'])
        self.assertEqual(len(new_text), len(_META_PYPROJECT))

    def test_agents_table_true_up_is_scoped(self):
        new_req = "juniper-service-core>=0.2.0,<0.6.0"
        out = pr.apply_pin_edits_agents_table(_META_AGENTS, "juniper-service-core", new_req)
        # the [tools] table row is trued up ...
        self.assertIn("`juniper-service-core>=0.2.0,<0.6.0`", out)
        # ... but the prose pin in the ## Conventions section is NOT moved
        self.assertIn("A prose pin that must NOT be edited: `juniper-service-core>=0.2.0,<0.5.0`.", out)
        # the observability minimum-pin prose note is untouched too
        self.assertIn("Minimum pin: `juniper-observability>=0.2.0`.", out)
        # doc-tools sits in TWO table rows -> both are trued up, none outside the table
        dt = pr.apply_pin_edits_agents_table(_META_AGENTS, "juniper-doc-tools", "juniper-doc-tools>=0.1.0,<0.3.0")
        self.assertEqual(dt.count("`juniper-doc-tools>=0.1.0,<0.3.0`"), 2)
        self.assertNotIn("`juniper-doc-tools>=0.1.0,<0.2.0`", dt)

    def test_agents_table_true_up_fixes_a_drifted_row(self):
        # the ml#657 class: the table row lags pyproject at <0.4.0; the name-anchored true-up corrects it
        stale = _META_AGENTS.replace("`juniper-service-core>=0.2.0,<0.5.0`, `juniper-model-core", "`juniper-service-core>=0.2.0,<0.4.0`, `juniper-model-core")
        fixed = pr.apply_pin_edits_agents_table(stale, "juniper-service-core", "juniper-service-core>=0.2.0,<0.6.0")
        self.assertIn("`juniper-service-core>=0.2.0,<0.6.0`", fixed)
        # only the table row is affected; the model-core sibling and the prose pins are intact
        self.assertIn("`juniper-model-core>=0.1.0,<0.4.0`", fixed)
        self.assertIn("A prose pin that must NOT be edited: `juniper-service-core>=0.2.0,<0.5.0`.", fixed)


# ── in-repo meta consumer-pin co-changes: build_proposal integration ─────────────────────


class BuildProposalConsumerPinTest(unittest.TestCase):
    """The escaping / non-escaping / absent / multi-extra / meta-self cases through build_proposal,
    against a synthetic repo carrying the real three-file meta surface. Fully offline (no writes)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        _write_meta_surface(self.repo_root)
        self.eco = self.root
        self.fake = _FakeSources(self.repo_root, self.eco)

    def tearDown(self):
        self._tmp.cleanup()

    def _subpkg_entry(self, name: str, path: str) -> "d.PackageEntry":
        return _entry(pypi_name=name, path=path, tag_pattern=f"{name}-v*", archive_name=f"RELEASE_NOTES_{name}_v{{version}}.md", ship_paths=[f"{path}{name.replace('-', '_')}/"])

    def _edit(self, prop, path):
        return next((e for e in prop.edits if e.path == path), None)

    def test_escaping_minor_bump_emits_all_three_cochanges(self):
        _write_pkg(self.repo_root, "juniper-service-core/", name="juniper-service-core", version="0.4.0", changelog=_CHANGELOG)
        entry = self._subpkg_entry("juniper-service-core", "juniper-service-core/")
        pkg = _manifest_pkg(pypi_name="juniper-service-core", released_version="0.4.0", declared_version="0.4.0", proposed_version="0.5.0")
        before = _sha_tree(self.repo_root)
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        # build_proposal itself writes NOTHING (dry-run purity)
        self.assertEqual(before, _sha_tree(self.repo_root))
        # the version-file edit stays edits[0] (root pyproject is an ADDITIONAL edit, not the version bump)
        self.assertEqual(prop.edits[0].path, "juniper-service-core/pyproject.toml")
        # co-change record + all three lockstep edits present with the raised ceiling
        self.assertEqual([(c.extra, c.old_req, c.new_req) for c in prop.consumer_pin_cochanges], [("tools", "juniper-service-core>=0.2.0,<0.5.0", "juniper-service-core>=0.2.0,<0.6.0")])
        root = self._edit(prop, "pyproject.toml")
        self.assertIsNotNone(root, "root pyproject.toml pin co-change missing")
        self.assertIn("juniper-service-core>=0.2.0,<0.6.0", root.new_text)
        self.assertNotIn("juniper-service-core>=0.2.0,<0.5.0", tomllib.loads(root.new_text)["project"]["optional-dependencies"]["tools"])
        test_edit = self._edit(prop, "tests/test_pyproject_extras.py")
        self.assertIsNotNone(test_edit, "test_pyproject_extras.py lockstep edit missing")
        self.assertIn("juniper-service-core>=0.2.0,<0.6.0", test_edit.new_text)
        agents = self._edit(prop, "AGENTS.md")
        self.assertIsNotNone(agents, "AGENTS.md extras-table co-change missing")
        self.assertIn("`juniper-service-core>=0.2.0,<0.6.0`", agents.new_text)
        # scoping: the AGENTS prose pin is NOT moved by the table true-up
        self.assertIn("A prose pin that must NOT be edited: `juniper-service-core>=0.2.0,<0.5.0`.", agents.new_text)
        # the PR body carries the Consumer-pin co-changes section listing the edit
        self.assertIn("Consumer-pin co-changes", prop.pr_body or "")
        self.assertIn("`[tools]`: `juniper-service-core>=0.2.0,<0.5.0` -> `juniper-service-core>=0.2.0,<0.6.0`", prop.pr_body or "")
        self.assertTrue(any("In-repo meta consumer pin" in item for item in prop.co_change_checklist))

    def test_doc_tools_bump_updates_both_extras(self):
        _write_pkg(self.repo_root, "juniper-doc-tools/", name="juniper-doc-tools", version="0.1.5", changelog=_CHANGELOG)
        entry = self._subpkg_entry("juniper-doc-tools", "juniper-doc-tools/")
        pkg = _manifest_pkg(pypi_name="juniper-doc-tools", released_version="0.1.5", declared_version="0.1.5", proposed_version="0.2.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual({c.extra for c in prop.consumer_pin_cochanges}, {"tools", "doc-tools"})
        root = self._edit(prop, "pyproject.toml")
        extras = tomllib.loads(root.new_text)["project"]["optional-dependencies"]
        self.assertIn("juniper-doc-tools>=0.1.0,<0.3.0", extras["tools"])
        self.assertIn("juniper-doc-tools>=0.1.0,<0.3.0", extras["doc-tools"])
        agents = self._edit(prop, "AGENTS.md")
        self.assertEqual(agents.new_text.count("`juniper-doc-tools>=0.1.0,<0.3.0`"), 2)

    def test_non_escaping_patch_bump_emits_none_needed(self):
        _write_pkg(self.repo_root, "juniper-service-core/", name="juniper-service-core", version="0.4.0", changelog=_CHANGELOG)
        entry = self._subpkg_entry("juniper-service-core", "juniper-service-core/")
        pkg = _manifest_pkg(pypi_name="juniper-service-core", released_version="0.4.0", declared_version="0.4.0", proposed_bump="patch", proposed_version="0.4.1")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual(prop.consumer_pin_cochanges, [])
        # NO root pyproject / test / AGENTS edits (only the sub-package version bump + its CHANGELOG)
        self.assertEqual({e.path for e in prop.edits}, {"juniper-service-core/pyproject.toml", "juniper-service-core/CHANGELOG.md"})
        self.assertIn("none needed -- new version within existing ceilings", prop.pr_body or "")

    def test_package_absent_from_extras_emits_zero(self):
        # juniper-config-tools is in-repo but NOT named in the fixture's extras -> zero co-changes
        _write_pkg(self.repo_root, "juniper-config-tools/", name="juniper-config-tools", version="0.1.0", changelog=_CHANGELOG)
        entry = self._subpkg_entry("juniper-config-tools", "juniper-config-tools/")
        pkg = _manifest_pkg(pypi_name="juniper-config-tools", released_version="0.1.0", declared_version="0.1.0", proposed_version="0.2.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual(prop.consumer_pin_cochanges, [])
        self.assertIsNone(self._edit(prop, "pyproject.toml"))
        self.assertIsNone(self._edit(prop, "AGENTS.md"))
        self.assertIn("none needed", prop.pr_body or "")

    def test_meta_self_bump_has_no_pin_cochange_only_version_header(self):
        # the meta-package bumping itself: AGENTS **Version** co-change, but NO extras-table pin change.
        # _write_meta_surface already laid down the extras pyproject + AGENTS; add the meta CHANGELOG.
        (self.repo_root / "CHANGELOG.md").write_text(_CHANGELOG)
        entry = _entry(pypi_name="juniper-ml", path=".", tag_pattern="v*", archive_name="RELEASE_NOTES_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-ml", released_version="0.6.0", declared_version="0.6.0", proposed_version="0.7.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual(prop.consumer_pin_cochanges, [])
        agents = self._edit(prop, "AGENTS.md")
        self.assertIsNotNone(agents)
        self.assertIn("**Version**: 0.7.0", agents.new_text)  # the version header co-change (step 5)
        self.assertIn("`juniper-service-core>=0.2.0,<0.5.0`", agents.new_text)  # extras table NOT touched
        self.assertIn("none needed", prop.pr_body or "")

    def test_meta_consumer_excluded_from_propagation_when_in_repo(self):
        # a sub-package MINOR bump: the meta (in-repo) is folded into THIS PR, so it is NOT also a
        # cross-repo propagation follow-on; a genuine sibling consumer still is.
        mc = self._subpkg_entry("juniper-model-core", "juniper-model-core/")
        meta = _entry(pypi_name="juniper-ml", repo="juniper-ml", path=".", depends_on=["juniper-model-core"])
        sibling = _entry(pypi_name="juniper-recurrence", repo="juniper-recurrence", path=".", depends_on=["juniper-model-core"])
        edges = pr.propagation_edges([mc, meta, sibling], mc, "minor")
        consumers = {e["consumer"] for e in edges}
        self.assertNotIn("juniper-ml", consumers)  # folded into the same PR
        self.assertIn("juniper-recurrence", consumers)  # cross-repo follow-on remains


# ── CLI: dry-run report / json / writes-nothing / exit codes ─────────────────


_MINI_REGISTRY = textwrap.dedent("""\
    packages:
      - pypi_name: juniper-thing
        repo: juniper-ml
        path: "juniper-thing/"
        version_source: static
        tag_pattern: "juniper-thing-v*"
        archive_name: "RELEASE_NOTES_juniper-thing_v{version}.md"
        trigger: {now: release, target: release}
        verify: {now: strict, target: strict}
        depends_on: []
        ship_paths: ["juniper-thing/juniper_thing/"]
        exclude_paths: []
    """)


class CliTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        self.registry = self.root / "registry.yaml"
        self.registry.write_text(_MINI_REGISTRY)
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps({"schema": "juniper-release-train/manifest/v1", "packages": [_manifest_pkg()]}))
        self.fake = _FakeSources(self.repo_root, self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, *extra) -> "tuple[int, str]":
        buf = io.StringIO()
        argv = ["--manifest", str(self.manifest), "--repo-root", str(self.repo_root), "--ecosystem-root", str(self.root), "--registry", str(self.registry), "--release-date", "2026-07-14", *extra]
        with redirect_stdout(buf):
            code = pr.main(argv, sources=self.fake.build())
        return code, buf.getvalue()

    def test_dry_run_report_is_default_and_wellformed(self):
        code, out = self._run()  # no --dry-run flag: dry-run is the default
        self.assertEqual(code, 0)
        self.assertIn("DRY-RUN", out)
        self.assertIn("PROPOSE  juniper-thing", out)
        self.assertIn("release/juniper-thing-v0.5.0", out)
        self.assertIn('version = "0.5.0"', out)

    def test_json_mode(self):
        code, out = self._run("--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["schema"], "juniper-release-train/proposals/v1")
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["summary"]["proposed"], 1)
        self.assertEqual(payload["proposals"][0]["branch"], "release/juniper-thing-v0.5.0")

    def test_dry_run_writes_nothing(self):
        before = _sha_tree(self.repo_root)
        code, _ = self._run()
        self.assertEqual(code, 0)
        after = _sha_tree(self.repo_root)
        self.assertEqual(before, after, "dry-run must not create/modify/delete any repo file")

    def test_package_filter_and_skip_non_unreleased(self):
        # a manifest with an UP_TO_DATE package produces no proposal (only UNRELEASED_CHANGES proposed)
        self.manifest.write_text(json.dumps({"packages": [_manifest_pkg(classification="UP_TO_DATE")]}))
        code, out = self._run()
        self.assertEqual(code, 0)
        self.assertIn("nothing to propose", out)

    def test_exit_two_bad_manifest(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pr.main(["--manifest", str(self.root / "nope.json"), "--repo-root", str(self.repo_root), "--registry", str(self.registry)], sources=self.fake.build())
        self.assertEqual(code, 2)

    def test_exit_two_unknown_package(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pr.main(["--manifest", str(self.manifest), "--repo-root", str(self.repo_root), "--registry", str(self.registry), "--package", "juniper-nope"], sources=self.fake.build())
        self.assertEqual(code, 2)

    def test_dry_run_overrides_execute_flag(self):
        # even with --execute, --dry-run wins (safety); nothing is written.
        before = _sha_tree(self.repo_root)
        code, out = self._run("--execute", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("DRY-RUN", out)
        self.assertEqual(before, _sha_tree(self.repo_root))


# ── execute path: cross-repo guard + headless-commit gpgsign landmine (Phase 2.2) ────


_TWO_PKG_REGISTRY = textwrap.dedent("""\
    packages:
      - pypi_name: juniper-thing
        repo: juniper-ml
        path: "juniper-thing/"
        version_source: static
        tag_pattern: "juniper-thing-v*"
        archive_name: "RELEASE_NOTES_juniper-thing_v{version}.md"
        trigger: {now: release, target: release}
        verify: {now: strict, target: strict}
        depends_on: []
        ship_paths: ["juniper-thing/juniper_thing/"]
        exclude_paths: []
      - pypi_name: juniper-sibling
        repo: juniper-sibling
        path: "."
        version_source: static
        tag_pattern: "v*"
        archive_name: "RELEASE_NOTES_juniper-sibling_v{version}.md"
        trigger: {now: release, target: release}
        verify: {now: strict, target: strict}
        depends_on: []
        ship_paths: ["juniper_sibling/"]
        exclude_paths: ["juniper_sibling/tests/"]
    """)


class ExecuteCrossRepoGuardTest(unittest.TestCase):
    """--execute capability boundary (Phase 4.1, plan S9.2 / S12 step 4.1). The DEGRADED single-repo
    ``GITHUB_TOKEN`` path (no --cross-repo) opens PRs ONLY for juniper-ml and SKIPS sibling-repo packages
    with the same clear reason as before; the CROSS-REPO-capable path (--cross-repo, an on-disk sibling
    checkout) additionally opens a sibling's PR in ITS OWN repo -- branched from that repo's origin/main,
    written into that repo's checkout, never touching the meta from the sibling context. Also pins the
    headless-commit gpgsign landmine fix. Fully hermetic: every repo-aware write / git / pr effect is a
    recording spy (no real repo writes, no gh, no git)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        # An in-repo (writable) package AND a cross-repo sibling, BOTH readable on disk -- so the
        # ONLY thing that skips the sibling under --execute is the cross-repo guard, not a failed
        # file read (proving the guard, not an incidental read failure, is the gate).
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        sibling = self.root / "juniper-sibling"
        sibling.mkdir()
        _write_pkg(sibling, ".", name="juniper-sibling", version="0.4.0", changelog=_CHANGELOG)
        self.registry = self.root / "registry.yaml"
        self.registry.write_text(_TWO_PKG_REGISTRY)
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(
            json.dumps(
                {
                    "packages": [
                        _manifest_pkg(pypi_name="juniper-thing", repo="juniper-ml"),
                        _manifest_pkg(pypi_name="juniper-sibling", repo="juniper-sibling"),
                    ]
                }
            )
        )
        self.calls = {"write": [], "git": [], "pr": []}

    def tearDown(self):
        self._tmp.cleanup()

    def _read_file(self, entry, filename):
        base = d.base_dir_for(entry, self.repo_root, self.root)
        try:
            return (base / filename).read_text(encoding="utf-8")
        except OSError:
            return None

    def _sources(self) -> pr.ProposeSources:
        # Repo-aware recording seam (Phase 4.1): write_file/run_git carry the target repo, so the test
        # can prove a sibling's edits/branches land in the SIBLING checkout, never the juniper-ml one.
        def open_pr(repo, base, head, title, body):
            self.calls["pr"].append((repo, base, head))
            return f"https://github.com/pcalnon/{repo}/pull/1"

        return pr.ProposeSources(
            read_file=self._read_file,
            list_open_prs=lambda repo: [],
            write_file=lambda repo, path, content: self.calls["write"].append((repo, path)),
            run_git=lambda repo, args: self.calls["git"].append((repo, list(args))),
            open_pr=open_pr,
        )

    def _run_execute(self, *extra) -> "tuple[int, str]":
        buf = io.StringIO()
        argv = ["--manifest", str(self.manifest), "--repo-root", str(self.repo_root), "--ecosystem-root", str(self.root), "--registry", str(self.registry), "--release-date", "2026-07-14", "--execute", *extra]
        with redirect_stdout(buf):
            code = pr.main(argv, sources=self._sources())
        return code, buf.getvalue()

    # ── capability helper (degraded vs cross-repo-capable) ───────────────────────────────────
    def test_cross_repo_skip_reason_capability(self):
        # in-repo is always writable (both paths)
        self.assertIsNone(pr.cross_repo_skip_reason("juniper-ml"))
        # sibling on the DEGRADED path (no capability) -> the SAME clear reason as before (preserved)
        degraded = pr.cross_repo_skip_reason("juniper-cascor")
        self.assertIsNotNone(degraded)
        self.assertIn("cross-repo", degraded)
        self.assertIn("juniper-cascor", degraded)
        self.assertIn("single-repo GITHUB_TOKEN", degraded)  # today's degraded-path wording
        # capable but the checkout is absent under the ecosystem root -> a distinct reason
        absent = pr.cross_repo_skip_reason("juniper-cascor", cross_repo_capable=True, ecosystem_root=self.root)
        self.assertIsNotNone(absent)
        self.assertIn("checkout is not present", absent)
        # capable AND the sibling checkout is on disk (setUp created self.root/juniper-sibling) -> writable
        self.assertIsNone(pr.cross_repo_skip_reason("juniper-sibling", cross_repo_capable=True, ecosystem_root=self.root))
        # the writable repo is still overridable (env / future multi-repo identity)
        self.assertIsNone(pr.cross_repo_skip_reason("juniper-cascor", writable_repo="juniper-cascor"))

    # ── DEGRADED path (no --cross-repo): in-repo only, sibling skipped (preserved) ───────────
    def test_degraded_path_opens_in_repo_and_skips_cross_repo(self):
        code, out = self._run_execute()  # NO --cross-repo
        self.assertEqual(code, 0, out)
        # exactly one PR opened, and it is the juniper-ml package (never the sibling); base 'main'
        self.assertEqual(self.calls["pr"], [("juniper-ml", "main", "release/juniper-thing-v0.5.0")])
        self.assertIn("opened: juniper-thing", out)
        self.assertIn("skip: juniper-sibling", out)
        self.assertIn("cross-repo", out)
        self.assertIn("single-repo GITHUB_TOKEN", out)  # the degraded-path skip reason, preserved
        # every write targeted the juniper-ml checkout for the in-repo package; nothing for the sibling
        for repo, path in self.calls["write"]:
            self.assertEqual(repo, "juniper-ml")
            self.assertTrue(path.startswith("juniper-thing/"), f"unexpected write to {path!r} -- sibling clobber?")

    # ── CROSS-REPO-capable path (--cross-repo): sibling opens in its OWN repo ────────────────
    def test_cross_repo_opens_sibling_in_its_repo_with_correct_branch_and_base(self):
        code, out = self._run_execute("--cross-repo")
        self.assertEqual(code, 0, out)
        # BOTH open now, each in its OWN repo; the PR --base is 'main' in both cases
        self.assertEqual(
            self.calls["pr"],
            [
                ("juniper-ml", "main", "release/juniper-thing-v0.5.0"),
                ("juniper-sibling", "main", "release/juniper-sibling-v0.5.0"),
            ],
        )
        self.assertIn("opened: juniper-thing", out)
        self.assertIn("opened: juniper-sibling", out)
        # the sibling branched from origin/main (fresh clone's authoritative ref); the in-repo from main
        sib_switch = next(args for repo, args in self.calls["git"] if repo == "juniper-sibling" and "switch" in args)
        self.assertEqual(sib_switch, ["switch", "-c", "release/juniper-sibling-v0.5.0", "origin/main"])
        inrepo_switch = next(args for repo, args in self.calls["git"] if repo == "juniper-ml" and "switch" in args)
        self.assertEqual(inrepo_switch, ["switch", "-c", "release/juniper-thing-v0.5.0", "main"])

    def test_cross_repo_sibling_edits_target_sibling_checkout_never_the_meta(self):
        self._run_execute("--cross-repo")
        sib_writes = [path for repo, path in self.calls["write"] if repo == "juniper-sibling"]
        # the sibling proposal edited only its OWN files (version bump + CHANGELOG at path '.')
        self.assertEqual(set(sib_writes), {"pyproject.toml", "CHANGELOG.md"})
        # NO sibling-shaped edit landed in the juniper-ml checkout (the clobber the guard prevents) ...
        self.assertNotIn(("juniper-ml", "pyproject.toml"), self.calls["write"])
        # ... and the sibling proposal NEVER edited the meta's consumer-pin lockstep files (#661 is
        # in-repo only; a sibling emits the S13 propagation edge instead)
        for repo, path in self.calls["write"]:
            if repo == "juniper-sibling":
                self.assertNotIn(path, {"tests/test_pyproject_extras.py", "AGENTS.md"})
        # every juniper-ml write is for the in-repo package's own subtree
        for repo, path in self.calls["write"]:
            if repo == "juniper-ml":
                self.assertTrue(path.startswith("juniper-thing/"), f"unexpected juniper-ml write {path!r}")

    def test_execute_commit_disables_gpg_signing(self):
        self._run_execute("--cross-repo")  # exercise BOTH repos' commits
        commits = [(repo, args) for repo, args in self.calls["git"] if "commit" in args]
        self.assertTrue(commits, "expected a git commit call in the --execute path")
        self.assertEqual({repo for repo, _ in commits}, {"juniper-ml", "juniper-sibling"})
        for _repo, args in commits:
            self.assertIn("commit.gpgsign=false", args)
            # the -c flag must precede the commit subcommand for git to honour it
            self.assertLess(args.index("commit.gpgsign=false"), args.index("commit"))

    def test_execute_proposal_direct_refuses_cross_repo_without_capability(self):
        # belt-and-suspenders: called directly WITHOUT capability, execute_proposal must never write a
        # sibling-repo proposal's edits into a checkout or open its PR.
        prop = pr.Proposal(pypi_name="juniper-sibling", repo="juniper-sibling", from_version="0.4.0", to_version="0.5.0", bump="minor", branch="release/juniper-sibling-v0.5.0")
        prop.edits.append(pr.FileEdit(path="pyproject.toml", old_text="a", new_text="b"))
        url = pr.execute_proposal(prop, self._sources(), "main")  # cross_repo defaults False
        self.assertEqual(url, "")
        self.assertEqual(self.calls["write"], [])
        self.assertEqual(self.calls["git"], [])
        self.assertEqual(self.calls["pr"], [])

    def test_execute_proposal_direct_opens_sibling_when_capable(self):
        # the direct path is capability-aware too: --cross-repo + an on-disk sibling checkout opens it.
        prop = pr.Proposal(pypi_name="juniper-sibling", repo="juniper-sibling", from_version="0.4.0", to_version="0.5.0", bump="minor", branch="release/juniper-sibling-v0.5.0", pr_title="t", pr_body="b", commit_message="chore(release): juniper-sibling v0.5.0")
        prop.edits.append(pr.FileEdit(path="pyproject.toml", old_text="a", new_text="b"))
        url = pr.execute_proposal(prop, self._sources(), "main", cross_repo=True, ecosystem_root=self.root)
        self.assertTrue(url)
        self.assertEqual(self.calls["pr"], [("juniper-sibling", "main", "release/juniper-sibling-v0.5.0")])
        self.assertIn(("juniper-sibling", ["switch", "-c", "release/juniper-sibling-v0.5.0", "origin/main"]), self.calls["git"])
        self.assertIn(("juniper-sibling", "pyproject.toml"), self.calls["write"])


if __name__ == "__main__":
    unittest.main()
