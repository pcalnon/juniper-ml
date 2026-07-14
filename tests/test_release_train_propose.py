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

``util/`` is not pre-commit-lint-gated, so this unittest IS the gate (the ``env_floor_drift_check``
precedent, shared with ``detect.py``). Imported via the house ``sys.path.insert`` idiom.

Run: python3 -m unittest -v tests/test_release_train_propose.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-07-14
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
import tempfile
import textwrap
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


if __name__ == "__main__":
    unittest.main()
