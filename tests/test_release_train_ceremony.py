#!/usr/bin/env python3
"""Hermetic regression tests for util/release_train/ceremony.py (plan S5.3/S7/S8/S9.3/S10, Phase 3.2).

NO network, NO real gh, NO real git, NO repo writes: every external effect runs through an injected
`CeremonySources` seam, and the release-notes template is read from the real in-repo
`notes/templates/` (a read). `util/` is not pre-commit-lint-gated, so this unittest IS the gate (the
`env_floor_drift_check` precedent, shared with `detect.py` / `propose.py`). Imported via the house
`sys.path.insert` idiom.

Covers (task acceptance list):
  * every S8 precondition HALT (main CI not green; declared<released anomaly; missing declared
    version; not-in-registry; missing CHANGELOG [<version>] section; TestPyPI-verify failure in the
    monitor)
  * the happy path's EXACT action sequence (open_archive_pr -> enable_auto_merge -> cut_release ->
    monitor_publish)
  * dup-guard / idempotent re-entry (already-released no-op; Release already cut -> resume-monitor;
    open archive PR reused; archive already on main -> skip the PR)
  * the S9.3 seam-surface invariant, in CODE and in TEST: `_assert_gh_allowed` rejects every
    environment/deployment/reviewer-mutating call, a bare `pr merge` without `--auto`, and a
    `release create --verify-tag`; and the LIVE seam driven with a recording gh issues ONLY
    allowlisted calls, with `--auto`/`--squash`, `--latest=false`/`--notes-file`, and no `--verify-tag`
  * `--dry-run` writes NOTHING (a git-tracked repo_root's `git status` stays clean)
  * the execute happy path (PENDING_PYPI_APPROVAL), the auto-merge graceful-degrade, and the pure
    helpers (classify_publish_run, changelog_version_section, infer_bump, release_tag)

Run: python3 -m unittest -v tests/test_release_train_ceremony.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-07-17
"""

from __future__ import annotations

import io
import json
import subprocess  # nosec B404 - git init/commit/status of a throwaway tmp repo for the dry-run snapshot
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UTIL_DIR = REPO_ROOT / "util" / "release_train"
sys.path.insert(0, str(UTIL_DIR))

import ceremony as ce  # noqa: E402
import detect as d  # noqa: E402

REAL_TEMPLATE = REPO_ROOT / "notes" / "templates" / "TEMPLATE_RELEASE_NOTES.md"

CHANGELOG_050 = textwrap.dedent("""\
    # Changelog

    ## [Unreleased]

    ## [0.5.0] - 2026-07-17

    ### Added

    - A new capability.

    ### Fixed

    - A real bug.

    ## [0.4.0] - 2026-06-01

    ### Added

    - The prior thing.
    """)


def _entry(**over) -> d.PackageEntry:
    base = {
        "pypi_name": "juniper-service-core",
        "repo": "juniper-ml",
        "path": "juniper-service-core/",
        "version_source": "static",
        "tag_pattern": "juniper-service-core-v*",
        "archive_name": "RELEASE_NOTES_juniper-service-core_v{version}.md",
        "trigger": {"now": "release", "target": "release"},
        "verify": {"now": "strict", "target": "strict"},
        "depends_on": [],
        "ship_paths": ["juniper-service-core/juniper_service_core/"],
        "exclude_paths": [],
    }
    base.update(over)
    return d.PackageEntry(**base)


def _manifest_pkg(**over) -> dict:
    base = {
        "pypi_name": "juniper-service-core",
        "repo": "juniper-ml",
        "released_version": "0.4.0",
        "declared_version": "0.5.0",
        "classification": "BUMPED_NOT_RELEASED",
    }
    base.update(over)
    return base


class _Recorder:
    """A record-and-canned-response fake for the write seam members + the monitor."""

    def __init__(self):
        self.calls = []

    def open_archive_pr(self, repo, base, branch, relpath, content, title, body):
        self.calls.append(("open_archive_pr", repo, branch, relpath))
        return f"https://github.com/pcalnon/{repo}/pull/900"

    def enable_automerge(self, repo, pr, ok=True):  # ok overridden per-test via functools.partial-like closure
        self.calls.append(("enable_automerge", repo, pr))
        return True

    def create_release(self, repo, tag, title, notes_relpath, content):
        self.calls.append(("create_release", repo, tag, notes_relpath))
        return f"https://github.com/pcalnon/{repo}/releases/tag/{tag}"

    def upsert_halt_issue(self, repo, title, body):
        self.calls.append(("upsert_halt_issue", repo, title))
        return f"https://github.com/pcalnon/{repo}/issues/1"


def _sources(
    *,
    pypi_version="0.4.0",
    changelog=CHANGELOG_050,
    main_ci="success",
    open_prs=None,
    release_cut=False,
    on_main=False,
    run_status=None,
    recorder=None,
    automerge_ok=True,
) -> ce.CeremonySources:
    rec = recorder

    def pypi_json(name):
        return {"info": {"version": pypi_version}} if pypi_version else None

    def read_file(entry, filename):
        return changelog if filename.endswith("CHANGELOG.md") else None

    def main_ci_conclusion(repo):
        return main_ci

    def list_open_prs(repo):
        return list(open_prs or [])

    def release_exists(repo, tag):
        return release_cut

    def archive_on_main(relpath):
        return on_main

    def publish_run_status(repo, tag):
        return run_status

    def enable_automerge(repo, pr):
        if rec is not None:
            rec.calls.append(("enable_automerge", repo, pr))
        return automerge_ok

    return ce.CeremonySources(
        pypi_json=pypi_json,
        read_file=read_file,
        main_ci_conclusion=main_ci_conclusion,
        list_open_prs=list_open_prs,
        release_exists=release_exists,
        archive_on_main=archive_on_main,
        publish_run_status=publish_run_status,
        open_archive_pr=(rec.open_archive_pr if rec else None),
        enable_automerge=enable_automerge if rec else None,
        create_release=(rec.create_release if rec else None),
        upsert_halt_issue=(rec.upsert_halt_issue if rec else None),
    )


def _plan(entry=None, pkg=None, **src_kwargs) -> ce.CeremonyPlan:
    entry = entry or _entry()
    pkg = pkg or _manifest_pkg()
    return ce.plan_ceremony(entry, pkg, _sources(**src_kwargs), REPO_ROOT, REPO_ROOT.parent, "2026-07-17")


# ── pure helpers ─────────────────────────────────────────────────────────────


class PureHelperTest(unittest.TestCase):
    def test_release_tag(self):
        self.assertEqual(ce.release_tag(_entry(), "0.5.0"), "juniper-service-core-v0.5.0")
        self.assertEqual(ce.release_tag(_entry(pypi_name="juniper-ml", tag_pattern="v*"), "0.6.0"), "v0.6.0")

    def test_archive_relpath_and_branch(self):
        self.assertEqual(ce.archive_relpath(_entry(), "0.5.0"), "notes/releases/RELEASE_NOTES_juniper-service-core_v0.5.0.md")
        self.assertEqual(ce.archive_branch("juniper-service-core", "0.5.0"), "release-notes/juniper-service-core-v0.5.0")

    def test_infer_bump(self):
        self.assertEqual(ce.infer_bump("0.4.0", "0.5.0"), "minor")
        self.assertEqual(ce.infer_bump("0.4.1", "0.4.2"), "patch")
        self.assertEqual(ce.infer_bump("0.4.0", "1.0.0"), "major")

    def test_changelog_version_section(self):
        sections = ce.changelog_version_section(CHANGELOG_050, "0.5.0")
        self.assertEqual(list(sections.keys()), ["Added", "Fixed"])
        self.assertEqual(sections["Added"], ["A new capability."])
        self.assertEqual(sections["Fixed"], ["A real bug."])
        # a version with no section -> empty (drives the HALT).
        self.assertEqual(ce.changelog_version_section(CHANGELOG_050, "9.9.9"), {})

    def test_writable_repo_skip_reason(self):
        self.assertIsNone(ce.writable_repo_skip_reason("juniper-ml"))
        self.assertIn("cross-repo", ce.writable_repo_skip_reason("juniper-cascor"))


# ── S9.3 seam-surface invariant (CODE half) ──────────────────────────────────


class GhSurfaceInvariantTest(unittest.TestCase):
    def test_mutating_surface_is_exactly_permitted(self):
        self.assertEqual(
            ce.GH_MUTATING_SURFACE,
            {("pr", "create"), ("pr", "merge"), ("release", "create"), ("issue", "create"), ("issue", "edit")},
        )

    def test_allowed_surface_has_no_env_or_reviewer_verb(self):
        for sub, verb in ce.GH_ALLOWED_SURFACE:
            self.assertNotIn(sub, ce.GH_FORBIDDEN_TOKENS, (sub, verb))
            self.assertNotIn(verb, ce.GH_FORBIDDEN_TOKENS, (sub, verb))
        self.assertFalse(any(sub == "api" for sub, _ in ce.GH_ALLOWED_SURFACE))

    def test_assert_gh_allowed_rejects_forbidden(self):
        forbidden_calls = [
            ["api", "repos/pcalnon/juniper-ml/environments/pypi", "-X", "PUT"],  # environment mutation via raw api
            ["pr", "review", "--approve", "1"],  # reviewer mutation
            ["pr", "merge", "1", "--squash"],  # bare immediate merge (no --auto)
            ["release", "create", "v1", "--verify-tag", "--notes-file", "x"],  # verify-tag on a Release that creates the tag
            ["run", "cancel", "1"],  # not in the allowlist
            ["secret", "set", "X"],  # secret mutation
            ["api", "repos/x/deployments"],  # deployment mutation
        ]
        for bad in forbidden_calls:
            with self.assertRaises(ce.SeamViolation, msg=bad):
                ce._assert_gh_allowed(bad)

    def test_assert_gh_allowed_permits_the_real_calls(self):
        for good in (
            ["pr", "create", "--repo", "pcalnon/juniper-ml", "--base", "main", "--head", "b", "--title", "t", "--body", "b"],
            ["pr", "merge", "1", "--repo", "pcalnon/juniper-ml", "--auto", "--squash"],
            ["release", "create", "v1", "--repo", "pcalnon/juniper-ml", "--notes-file", "x", "--latest=false"],
            ["run", "list", "--repo", "pcalnon/juniper-ml", "--branch", "main"],
            ["run", "view", "5"],
            ["issue", "create", "--repo", "pcalnon/juniper-ml", "--title", "t", "--body", "b"],
            ["issue", "edit", "3", "--body", "b"],
        ):
            ce._assert_gh_allowed(good)  # must not raise

    # ── Phase 4.1: the --repo value bound (cross-repo expressed WITHOUT widening the verb allowlist) ──
    def test_assert_gh_allowed_repo_value_bound(self):
        allowed = frozenset({"pcalnon/juniper-ml", "pcalnon/juniper-cascor-client"})
        # a --repo naming one of the allowed publishing repos passes (the surface is unchanged)
        ce._assert_gh_allowed(["release", "create", "v0.5.0", "--repo", "pcalnon/juniper-cascor-client", "--notes-file", "x", "--latest=false"], allowed)
        ce._assert_gh_allowed(["pr", "create", "--repo", "pcalnon/juniper-ml", "--base", "main", "--head", "b", "--title", "t", "--body", "b"], allowed)
        # a --repo OUTSIDE the allowlist -- wrong repo or wrong owner -- is a SeamViolation
        with self.assertRaises(ce.SeamViolation):
            ce._assert_gh_allowed(["release", "create", "v1", "--repo", "pcalnon/juniper-evil", "--notes-file", "x"], allowed)
        with self.assertRaises(ce.SeamViolation):
            ce._assert_gh_allowed(["pr", "create", "--repo", "someone-else/juniper-ml", "--base", "main", "--head", "b", "--title", "t", "--body", "b"], allowed)
        # allowed_repos=None leaves the --repo VALUE unchecked (surface + token guards still apply)
        ce._assert_gh_allowed(["release", "create", "v1", "--repo", "pcalnon/anything", "--notes-file", "x"])  # must not raise
        # even with the bound, a forbidden token still fails first
        with self.assertRaises(ce.SeamViolation):
            ce._assert_gh_allowed(["api", "repos/pcalnon/juniper-ml/environments/pypi", "--repo", "pcalnon/juniper-ml"], allowed)

    def test_publishing_repo_slugs_from_registry(self):
        entries = d.load_registry(UTIL_DIR / "registry.yaml")
        slugs = ce.publishing_repo_slugs(entries, "pcalnon")
        # exactly the 8 publishing repos, each owner-qualified
        self.assertEqual(len(slugs), 8)
        self.assertIn("pcalnon/juniper-ml", slugs)
        self.assertIn("pcalnon/juniper-cascor-client", slugs)
        self.assertIn("pcalnon/juniper-recurrence", slugs)
        self.assertTrue(all(s.startswith("pcalnon/") for s in slugs))


# ── S9.3 seam-surface invariant (LIVE seam, recording gh) ────────────────────


class LiveSeamSurfaceTest(unittest.TestCase):
    """Drive the real live-seam argv construction with a recording gh: prove the surface is exactly
    the R7-permitted set and nothing environment/reviewer-mutating -- hermetically (no real gh/git)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.gh_calls = []

    def _rec_gh(self, args, timeout=90):
        self.gh_calls.append(list(args))
        pair = (args[0], args[1])
        if pair in (("pr", "list"), ("run", "list")):
            return "[]"
        if pair == ("run", "view"):
            return "{}"
        if pair in (("release", "view"), ("issue", "list")):
            return ""
        return "https://github.com/pcalnon/juniper-ml/x/1"

    def _rec_git(self, repo_dir, args, timeout=120, check=True):
        return ""  # all git ops succeed, empty stdout

    def _drive(self):
        src = ce.make_live_sources("pcalnon", self.tmp, self.tmp.parent, gh=self._rec_gh, git=self._rec_git)
        src.main_ci_conclusion("juniper-ml")
        src.list_open_prs("juniper-ml")
        src.release_exists("juniper-ml", "juniper-service-core-v0.5.0")
        src.publish_run_status("juniper-ml", "juniper-service-core-v0.5.0")
        src.open_archive_pr("juniper-ml", "main", "release-notes/juniper-service-core-v0.5.0", "notes/releases/RELEASE_NOTES_juniper-service-core_v0.5.0.md", "notes body\n", "release-notes: juniper-service-core v0.5.0", "pr body")
        src.enable_automerge("juniper-ml", "https://github.com/pcalnon/juniper-ml/pull/1")
        src.create_release("juniper-ml", "juniper-service-core-v0.5.0", "juniper-service-core v0.5.0", "notes/releases/RELEASE_NOTES_juniper-service-core_v0.5.0.md", "notes body\n")
        src.upsert_halt_issue("juniper-ml", "[release-train] HALT: juniper-service-core -- main-ci-not-green", "body")
        return src

    def test_every_gh_call_is_within_the_allowlist(self):
        self._drive()
        self.assertTrue(self.gh_calls)
        for args in self.gh_calls:
            self.assertIn((args[0], args[1]), ce.GH_ALLOWED_SURFACE, args)
            self.assertFalse(set(args) & ce.GH_FORBIDDEN_TOKENS, args)

    def test_mutating_calls_carry_the_required_flags(self):
        self._drive()

        def one(sub, verb):
            hits = [a for a in self.gh_calls if a[0] == sub and a[1] == verb]
            self.assertTrue(hits, f"expected a `{sub} {verb}` call")
            return hits[0]

        merge = one("pr", "merge")
        self.assertIn("--auto", merge)
        self.assertIn("--squash", merge)
        rel = one("release", "create")
        self.assertIn("--latest=false", rel)
        self.assertIn("--notes-file", rel)
        self.assertNotIn("--verify-tag", rel)
        one("pr", "create")
        # the HALT-issue upsert is a read (issue list) + a write (issue create/edit) -- both benign.
        self.assertTrue(any(a[:2] == ["issue", "list"] for a in self.gh_calls))
        self.assertTrue(any(a[:2] in (["issue", "create"], ["issue", "edit"]) for a in self.gh_calls))


# ── S8 precondition HALTs ────────────────────────────────────────────────────


class PreconditionHaltTest(unittest.TestCase):
    def _assert_halt(self, plan, reason_key):
        self.assertEqual(plan.state, "HALTED")
        self.assertTrue(plan.halted)
        self.assertIsNotNone(plan.issue)
        self.assertEqual(plan.issue["reason_key"], reason_key)
        self.assertEqual(plan.action_kinds, ["halt_issue"])  # the only action is filing the dedup issue

    def test_main_ci_not_green_halts(self):
        self._assert_halt(_plan(main_ci="failure"), "main-ci-not-green")

    def test_declared_less_than_released_anomaly_halts(self):
        # PyPI already serves a HIGHER version than declared -> yank/rollback anomaly.
        self._assert_halt(_plan(pypi_version="0.6.0"), "declared-lt-released-anomaly")

    def test_missing_changelog_section_halts(self):
        no_section = "# Changelog\n\n## [Unreleased]\n\n## [0.3.0] - 2026-01-01\n\n### Added\n\n- old\n"
        self._assert_halt(_plan(changelog=no_section), "changelog-section-missing")

    def test_missing_declared_version_halts(self):
        self._assert_halt(_plan(pkg=_manifest_pkg(declared_version=None)), "missing-declared-version")

    def test_pypi_truth_missing_halts(self):
        # manifest said released 0.4.0 but PyPI now returns nothing.
        self._assert_halt(_plan(pypi_version=None), "pypi-truth-missing")

    def test_halt_issue_title_keyed_on_pkg_and_reason(self):
        plan = _plan(main_ci="failure")
        self.assertEqual(plan.issue["title"], "[release-train] HALT: juniper-service-core -- main-ci-not-green")


# ── happy path + idempotency ─────────────────────────────────────────────────


class HappyPathAndIdempotencyTest(unittest.TestCase):
    def test_happy_path_exact_action_sequence(self):
        plan = _plan()  # green, released 0.4.0 < declared 0.5.0, no PR, not cut, not on main
        self.assertEqual(plan.state, "CEREMONY_PLANNED")
        self.assertFalse(plan.halted)
        self.assertEqual(plan.action_kinds, ["open_archive_pr", "enable_auto_merge", "cut_release", "monitor_publish"])
        self.assertEqual(plan.tag, "juniper-service-core-v0.5.0")
        self.assertEqual(plan.archive_relpath, "notes/releases/RELEASE_NOTES_juniper-service-core_v0.5.0.md")
        self.assertIn("0.5.0", plan.archive_content)
        self.assertIn("A new capability.", plan.archive_content)  # sourced from the [0.5.0] CHANGELOG section

    def test_already_released_is_noop(self):
        plan = _plan(pypi_version="0.5.0")  # PyPI already serves the target
        self.assertEqual(plan.state, "ALREADY_RELEASED")
        self.assertEqual(plan.action_kinds, [])

    def test_release_already_cut_resumes_monitor_only(self):
        plan = _plan(release_cut=True)
        self.assertEqual(plan.state, "RESUME_MONITOR")
        self.assertEqual(plan.action_kinds, ["monitor_publish"])  # no re-open, no re-cut (idempotent)

    def test_open_archive_pr_is_reused_not_duplicated(self):
        existing = [{"number": 900, "headRefName": "release-notes/juniper-service-core-v0.5.0", "title": "x"}]
        plan = _plan(open_prs=existing)
        self.assertEqual(plan.action_kinds, ["enable_auto_merge", "cut_release", "monitor_publish"])  # open skipped
        self.assertTrue(any("reuse" in n for n in plan.notes))

    def test_archive_already_on_main_skips_the_pr(self):
        plan = _plan(on_main=True)
        self.assertEqual(plan.action_kinds, ["cut_release", "monitor_publish"])  # no PR, no auto-merge needed

    def test_cross_repo_is_skipped_not_halted(self):
        plan = _plan(entry=_entry(pypi_name="juniper-cascor", repo="juniper-cascor", path=".", tag_pattern="v*"), pkg=_manifest_pkg(pypi_name="juniper-cascor", repo="juniper-cascor"))
        self.assertEqual(plan.state, "SKIPPED_CROSS_REPO")
        self.assertFalse(plan.halted)
        self.assertEqual(plan.action_kinds, [])


# ── classify_publish_run (the monitor's brain) ───────────────────────────────


class ClassifyPublishRunTest(unittest.TestCase):
    def test_none_is_not_found(self):
        self.assertEqual(ce.classify_publish_run(None), "NOT_FOUND")

    def test_testpypi_ok_pypi_waiting_is_pending_approval(self):
        run = {
            "status": "waiting",
            "conclusion": None,
            "jobs": [
                {"name": "publish-testpypi", "status": "completed", "conclusion": "success"},
                {"name": "publish-pypi", "status": "waiting", "conclusion": None},
            ],
        }
        self.assertEqual(ce.classify_publish_run(run), "PENDING_PYPI_APPROVAL")

    def test_testpypi_failure_halts(self):
        run = {
            "status": "completed",
            "conclusion": "failure",
            "jobs": [
                {"name": "publish-testpypi", "status": "completed", "conclusion": "failure"},
            ],
        }
        self.assertEqual(ce.classify_publish_run(run), "HALT_TESTPYPI")

    def test_both_gates_done_is_released(self):
        run = {
            "status": "completed",
            "conclusion": "success",
            "jobs": [
                {"name": "publish-testpypi", "status": "completed", "conclusion": "success"},
                {"name": "publish-pypi", "status": "completed", "conclusion": "success"},
            ],
        }
        self.assertEqual(ce.classify_publish_run(run), "RELEASED")

    def test_in_progress(self):
        run = {
            "status": "in_progress",
            "conclusion": None,
            "jobs": [
                {"name": "publish-testpypi", "status": "in_progress", "conclusion": None},
            ],
        }
        self.assertEqual(ce.classify_publish_run(run), "IN_PROGRESS")


# ── execute path (fake write seam; NEVER touches the real repo) ───────────────


PENDING_RUN = {
    "status": "waiting",
    "conclusion": None,
    "jobs": [
        {"name": "publish-testpypi", "status": "completed", "conclusion": "success"},
        {"name": "publish-pypi", "status": "waiting", "conclusion": None},
    ],
}
FAILED_TESTPYPI_RUN = {
    "status": "completed",
    "conclusion": "failure",
    "jobs": [
        {"name": "publish-testpypi", "status": "completed", "conclusion": "failure"},
    ],
}


class ExecuteTest(unittest.TestCase):
    def _mk(self, **over):
        rec = _Recorder()
        src = _sources(recorder=rec, **over)
        return rec, src

    def test_execute_happy_path_reaches_pending_pypi_approval(self):
        rec, src = self._mk(run_status=PENDING_RUN)
        plan = ce.plan_ceremony(_entry(), _manifest_pkg(), src, REPO_ROOT, REPO_ROOT.parent, "2026-07-17")
        result = ce.execute_ceremony(plan, src, monitor_kwargs={"timeout_seconds": 0, "sleep": lambda s: None})
        self.assertEqual(result["state"], "PENDING_PYPI_APPROVAL")
        self.assertIsNotNone(result["pr_url"])
        self.assertIsNotNone(result["release_url"])
        kinds = [c[0] for c in rec.calls]
        self.assertEqual(kinds, ["open_archive_pr", "enable_automerge", "create_release"])

    def test_execute_auto_merge_degrades_gracefully(self):
        rec, src = self._mk(run_status=PENDING_RUN, automerge_ok=False)
        plan = ce.plan_ceremony(_entry(), _manifest_pkg(), src, REPO_ROOT, REPO_ROOT.parent, "2026-07-17")
        result = ce.execute_ceremony(plan, src, monitor_kwargs={"timeout_seconds": 0, "sleep": lambda s: None})
        # not a halt -- still parks at the pypi gate; a note records the owner one-click fallback.
        self.assertEqual(result["state"], "PENDING_PYPI_APPROVAL")
        self.assertFalse(result.get("auto_merge_enabled"))
        self.assertTrue(any("one-click" in n for n in result["notes"]))

    def test_execute_testpypi_failure_halts_and_files_issue(self):
        rec, src = self._mk(run_status=FAILED_TESTPYPI_RUN)
        plan = ce.plan_ceremony(_entry(), _manifest_pkg(), src, REPO_ROOT, REPO_ROOT.parent, "2026-07-17")
        result = ce.execute_ceremony(plan, src, monitor_kwargs={"timeout_seconds": 0, "sleep": lambda s: None})
        self.assertEqual(result["state"], "HALTED")
        self.assertIn("issue_url", result)
        self.assertTrue(any(c[0] == "upsert_halt_issue" for c in rec.calls))


# ── CLI: dry-run writes nothing + exit codes ─────────────────────────────────


class CliDryRunTest(unittest.TestCase):
    def _git(self, repo, *args):
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)  # nosec B603,B607

    def _manifest_file(self, *pkgs):
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump({"schema": "juniper-release-train/manifest/v1", "packages": list(pkgs)}, fh)
        fh.close()
        self.addCleanup(lambda: Path(fh.name).unlink(missing_ok=True))
        return fh.name

    def test_dry_run_writes_nothing(self):
        # A git-tracked tmp repo_root with the notes template present; a dry-run must leave it clean.
        repo = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(repo, ignore_errors=True))
        (repo / "notes" / "templates").mkdir(parents=True)
        (repo / "notes" / "templates" / "TEMPLATE_RELEASE_NOTES.md").write_text(REAL_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
        (repo / "notes" / "releases").mkdir(parents=True)
        self._git(repo, "init", "-q")
        self._git(repo, "add", "-A")
        self._git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "base")

        manifest = self._manifest_file(_manifest_pkg())
        src = _sources()  # read-only seam (no write members) -> a pure dry-run
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ce.main(["--manifest", manifest, "--dry-run", "--repo-root", str(repo), "--registry", str(UTIL_DIR / "registry.yaml"), "--release-date", "2026-07-17"], sources=src)
        self.assertEqual(rc, 0)
        self.assertIn("CEREMONY", buf.getvalue())
        status = self._git(repo, "status", "--porcelain").stdout
        self.assertEqual(status, "", f"dry-run dirtied the repo:\n{status}")

    def test_dry_run_json_and_halt_exit_code(self):
        manifest = self._manifest_file(_manifest_pkg())
        # main CI red -> the single package HALTs -> exit 1.
        src = _sources(main_ci="failure")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ce.main(["--manifest", manifest, "--dry-run", "--json", "--repo-root", str(REPO_ROOT), "--registry", str(UTIL_DIR / "registry.yaml")], sources=src)
        self.assertEqual(rc, 1)  # a halt -> exit 1 (owner attention)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["summary"]["halted"], 1)
        self.assertEqual(payload["plans"][0]["state"], "HALTED")

    def test_unknown_package_exit_2(self):
        manifest = self._manifest_file(_manifest_pkg())
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(buf):
            import contextlib

            with contextlib.redirect_stderr(err):
                rc = ce.main(["--manifest", manifest, "--package", "juniper-nonesuch", "--registry", str(UTIL_DIR / "registry.yaml")], sources=_sources())
        self.assertEqual(rc, 2)
        self.assertIn("unknown --package", err.getvalue())


# ── defect fix 1: open_archive_pr restores the operator's starting branch ─────


BUILDING_RUN = {
    "status": "in_progress",  # still building (TestPyPI not done, gate not reached) -> IN_PROGRESS
    "conclusion": None,
    "jobs": [
        {"name": "Build and Validate", "status": "completed", "conclusion": "success"},
        {"name": "Publish to TestPyPI", "status": "in_progress", "conclusion": None},
    ],
}
# Real publish-workflow job names (verified against run 29707696002): the gate reached at the JOB level
# while the run's top-level status has not yet flipped to 'waiting' -- exercises the job-level fallback.
GATE_PARKED_JOBLEVEL_RUN = {
    "status": "in_progress",
    "conclusion": None,
    "jobs": [
        {"name": "Publish to TestPyPI", "status": "completed", "conclusion": "success"},
        {"name": "Publish to PyPI", "status": "waiting", "conclusion": None},
    ],
}


class _GitRecorder:
    """A recording fake for the injected ``git`` runner: reports a branch/detached/dirty checkout and can
    raise on a chosen verb to simulate a mid-ceremony failure. Drives ``make_live_sources`` hermetically
    (mirrors ``LiveSeamSurfaceTest._rec_git`` but with restore-relevant answers)."""

    def __init__(self, *, branch="main", detached=None, dirty=False, raise_on=None):
        self.calls = []
        self._branch = branch
        self._detached = detached
        self._dirty = dirty
        self._raise_on = raise_on

    def __call__(self, repo_dir, args, timeout=120, check=True):
        self.calls.append(list(args))
        if self._raise_on and args and args[0] == self._raise_on:
            raise ce.SourceError(f"fake git {self._raise_on} failed")
        if args[:1] == ["symbolic-ref"]:
            return None if self._detached else f"{self._branch}\n"  # real _git returns None on a detached HEAD
        if args[:1] == ["rev-parse"]:
            return f"{self._detached or 'deadbeef'}\n"
        if args[:1] == ["status"]:
            return " M dirty_file\n" if self._dirty else ""
        return ""


class BranchRestoreUnitTest(unittest.TestCase):
    """Unit coverage of the capture/restore helpers (defect 1: leave the checkout as we found it)."""

    def test_capture_returns_branch_detached_or_none(self):
        def on_branch(repo_dir, args, *a):
            return "main\n" if args[0] == "symbolic-ref" else ""

        self.assertEqual(ce._capture_git_ref(Path("/x"), on_branch), ("branch", "main"))

        def detached(repo_dir, args, *a):
            if args[0] == "symbolic-ref":
                return None  # real _git returns None (non-zero, check=False) on a detached HEAD
            return "abc1234\n" if args[0] == "rev-parse" else ""

        self.assertEqual(ce._capture_git_ref(Path("/x"), detached), ("detached", "abc1234"))
        self.assertIsNone(ce._capture_git_ref(Path("/x"), lambda *a: ""))

    def test_restore_switches_back_when_clean(self):
        calls = []

        def git(repo_dir, args, *a):
            calls.append(list(args))
            return ""  # status --porcelain empty -> clean

        self.assertTrue(ce._restore_git_ref(Path("/x"), git, ("branch", "main")))
        self.assertIn(["switch", "main"], calls)

    def test_restore_detached_uses_switch_detach(self):
        calls = []

        def git(repo_dir, args, *a):
            calls.append(list(args))
            return ""

        self.assertTrue(ce._restore_git_ref(Path("/x"), git, ("detached", "abc1234")))
        self.assertIn(["switch", "--detach", "abc1234"], calls)

    def test_restore_skipped_and_warns_when_dirty(self):
        calls, warns = [], []

        def git(repo_dir, args, *a):
            calls.append(list(args))
            return " M dirty_file\n" if args[0] == "status" else ""

        self.assertFalse(ce._restore_git_ref(Path("/x"), git, ("branch", "main"), warn=warns.append))
        self.assertNotIn(["switch", "main"], calls)  # a dirty tree is NEVER clobbered
        self.assertTrue(warns and "uncommitted" in warns[0])

    def test_restore_noop_when_capture_none(self):
        calls = []

        def git(repo_dir, args, *a):
            calls.append(list(args))
            return ""

        self.assertFalse(ce._restore_git_ref(Path("/x"), git, None))
        self.assertEqual(calls, [])  # nothing to restore to -> no git touched


class OpenArchivePrRestoreTest(unittest.TestCase):
    """Integration: drive the LIVE ``open_archive_pr`` seam member with a recording git and prove the
    starting branch is restored on success AND on a mid-ceremony failure, and skipped for a dirty tree."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))

    def _gh(self, args, timeout=90):
        if (args[0], args[1]) in (("pr", "list"), ("run", "list")):
            return "[]"
        return "https://github.com/pcalnon/juniper-ml/pull/1"

    def _open(self, git_rec):
        src = ce.make_live_sources("pcalnon", self.tmp, self.tmp.parent, gh=self._gh, git=git_rec)
        return src.open_archive_pr(
            "juniper-ml",
            "main",
            "release-notes/juniper-service-core-v0.5.0",
            "notes/releases/RELEASE_NOTES_juniper-service-core_v0.5.0.md",
            "notes body\n",
            "release-notes: juniper-service-core v0.5.0",
            "pr body",
        )

    def test_restores_starting_branch_on_success(self):
        rec = _GitRecorder(branch="main")
        self._open(rec)
        create = ["switch", "-c", "release-notes/juniper-service-core-v0.5.0", "main"]
        restore = ["switch", "main"]
        self.assertIn(create, rec.calls)  # created the ceremony branch
        self.assertIn(restore, rec.calls)  # ... and restored the operator's branch
        self.assertLess(rec.calls.index(create), rec.calls.index(restore))  # restore happens on the way OUT

    def test_restores_on_mid_ceremony_failure(self):
        rec = _GitRecorder(branch="main", raise_on="push")  # push blows up after the branch switch
        with self.assertRaises(ce.SourceError):
            self._open(rec)
        self.assertIn(["switch", "main"], rec.calls)  # finally: restored despite the failure

    def test_dirty_tree_left_on_ceremony_branch_with_warning(self):
        import contextlib

        rec = _GitRecorder(branch="main", dirty=True)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self._open(rec)
        self.assertNotIn(["switch", "main"], rec.calls)  # never clobber uncommitted work
        self.assertIn("WARNING", err.getvalue())
        self.assertIn("dirty tree", err.getvalue().lower())


# ── defect fix 2: bounded monitor -> PENDING_PYPI_APPROVAL / honest IN_PROGRESS ──


def _monitor_sources(*statuses):
    """A minimal seam whose ``publish_run_status`` yields ``statuses`` in order (then repeats the last);
    ``box['polls']`` records how many times it was polled."""
    seq = list(statuses)
    box = {"polls": 0}

    def publish_run_status(repo, tag):
        i = box["polls"]
        box["polls"] += 1
        return seq[i] if i < len(seq) else seq[-1]

    src = ce.CeremonySources(
        pypi_json=lambda n: None,
        read_file=lambda e, f: None,
        main_ci_conclusion=lambda r: "success",
        list_open_prs=lambda r: [],
        release_exists=lambda r, t: False,
        archive_on_main=lambda r: False,
        publish_run_status=publish_run_status,
    )
    return src, box


class MonitorTimeoutTest(unittest.TestCase):
    def test_reaches_pending_on_run_level_waiting(self):
        src, _ = _monitor_sources(PENDING_RUN)  # run.status == 'waiting'
        self.assertEqual(ce.monitor_publish_run(src, "juniper-ml", "tag", sleep=lambda s: None), "PENDING_PYPI_APPROVAL")

    def test_reaches_pending_on_job_level_gate_when_run_not_yet_waiting(self):
        src, _ = _monitor_sources(GATE_PARKED_JOBLEVEL_RUN)  # run.status 'in_progress' but pypi job parked
        self.assertEqual(ce.monitor_publish_run(src, "juniper-ml", "tag", sleep=lambda s: None), "PENDING_PYPI_APPROVAL")

    def test_polls_through_building_until_waiting(self):
        src, box = _monitor_sources(BUILDING_RUN, BUILDING_RUN, PENDING_RUN)
        verdict = ce.monitor_publish_run(src, "juniper-ml", "tag", timeout_seconds=1000, poll_seconds=0, sleep=lambda s: None)
        self.assertEqual(verdict, "PENDING_PYPI_APPROVAL")
        self.assertEqual(box["polls"], 3)  # did not give up while the run was still building

    def test_honest_in_progress_on_timeout(self):
        src, box = _monitor_sources(BUILDING_RUN)  # never reaches the gate
        clock = {"t": 0.0}

        def monotonic():
            v = clock["t"]
            clock["t"] += 20.0
            return v

        verdict = ce.monitor_publish_run(src, "juniper-ml", "tag", timeout_seconds=30, poll_seconds=1, sleep=lambda s: None, monotonic=monotonic)
        self.assertEqual(verdict, "IN_PROGRESS")  # bounded wall clock -> honest 'still building'
        self.assertGreaterEqual(box["polls"], 2)  # ... but only after actually polling more than once

    def test_monitor_timeout_flag_default_and_override(self):
        self.assertEqual(ce.parse_args(["--manifest", "m.json"]).monitor_timeout, ce.DEFAULT_MONITOR_TIMEOUT_SECONDS)
        self.assertEqual(ce.parse_args(["--manifest", "m.json", "--monitor-timeout", "42"]).monitor_timeout, 42)


# ── Phase 4.1: cross-repo ceremony (central archive PR + owning-repo Release) ─────────────────


def _sibling_entry(**over) -> d.PackageEntry:
    base = {
        "pypi_name": "juniper-cascor-client",
        "repo": "juniper-cascor-client",
        "path": ".",
        "tag_pattern": "v*",
        "archive_name": "RELEASE_NOTES_juniper-cascor-client_v{version}.md",
    }
    base.update(over)
    return _entry(**base)


class CrossRepoCeremonyTest(unittest.TestCase):
    """A sibling package's ceremony (Phase 4.1): the exempt archive PR STILL lands in juniper-ml (central,
    plan S10.2) while the Release is cut on the OWNING repo. Capability-gated: skipped without --cross-repo,
    ceremoniable with it + an on-disk sibling checkout. Hermetic (synthetic ecosystem; seam-backed reads)."""

    def setUp(self):
        # A synthetic ecosystem root with the sibling checked out on disk (an empty dir is enough -- the
        # CHANGELOG is served by the seam), so the capability check's is_dir() precondition holds offline.
        self.eco = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.eco, ignore_errors=True))
        (self.eco / "juniper-cascor-client").mkdir()

    def _pkg(self):
        return _manifest_pkg(pypi_name="juniper-cascor-client", repo="juniper-cascor-client")

    def test_without_capability_sibling_is_skipped(self):
        plan = ce.plan_ceremony(_sibling_entry(), self._pkg(), _sources(), REPO_ROOT, self.eco, "2026-07-17")  # cross_repo defaults False
        self.assertEqual(plan.state, "SKIPPED_CROSS_REPO")
        self.assertIn("cross-repo", plan.skipped_reason)
        self.assertIn("single-repo GITHUB_TOKEN", plan.skipped_reason)  # degraded-path wording preserved

    def test_capable_but_checkout_absent_is_skipped_with_distinct_reason(self):
        empty_eco = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(empty_eco, ignore_errors=True))
        plan = ce.plan_ceremony(_sibling_entry(), self._pkg(), _sources(), REPO_ROOT, empty_eco, "2026-07-17", cross_repo=True)
        self.assertEqual(plan.state, "SKIPPED_CROSS_REPO")
        self.assertIn("checkout is not present", plan.skipped_reason)

    def test_cross_repo_plan_archive_central_release_owning(self):
        plan = ce.plan_ceremony(_sibling_entry(), self._pkg(), _sources(), REPO_ROOT, self.eco, "2026-07-17", cross_repo=True)
        self.assertEqual(plan.state, "CEREMONY_PLANNED")
        self.assertEqual(plan.repo, "juniper-cascor-client")  # owning repo -> Release + monitor
        self.assertEqual(plan.archive_repo, "juniper-ml")  # central archive PR (plan S10.2)
        self.assertEqual(plan.tag, "v0.5.0")  # tag_pattern v* -> v<version>
        self.assertEqual(plan.archive_relpath, "notes/releases/RELEASE_NOTES_juniper-cascor-client_v0.5.0.md")
        self.assertEqual(plan.action_kinds, ["open_archive_pr", "enable_auto_merge", "cut_release", "monitor_publish"])
        self.assertIn("A new capability.", plan.archive_content)  # notes sourced from the [0.5.0] CHANGELOG section

    def test_cross_repo_dup_guard_checks_central_archive_repo(self):
        # an open archive PR is deduped against juniper-ml (where the archive PR lives), NOT the owning repo.
        existing = [{"number": 900, "headRefName": "release-notes/juniper-cascor-client-v0.5.0", "title": "x"}]
        plan = ce.plan_ceremony(_sibling_entry(), self._pkg(), _sources(open_prs=existing), REPO_ROOT, self.eco, "2026-07-17", cross_repo=True)
        self.assertEqual(plan.action_kinds, ["enable_auto_merge", "cut_release", "monitor_publish"])  # open skipped (reused)
        self.assertTrue(any("reuse" in n for n in plan.notes))

    def test_cross_repo_execute_archive_in_juniper_ml_release_in_owning(self):
        rec = _Recorder()
        src = _sources(recorder=rec, run_status=PENDING_RUN)
        plan = ce.plan_ceremony(_sibling_entry(), self._pkg(), src, REPO_ROOT, self.eco, "2026-07-17", cross_repo=True)
        result = ce.execute_ceremony(plan, src, monitor_kwargs={"timeout_seconds": 0, "sleep": lambda s: None})
        self.assertEqual(result["state"], "PENDING_PYPI_APPROVAL")
        # the archive PR + auto-merge targeted juniper-ml (central); the Release targeted the OWNING repo
        archive = next(c for c in rec.calls if c[0] == "open_archive_pr")
        self.assertEqual(archive[1], "juniper-ml")
        automerge = next(c for c in rec.calls if c[0] == "enable_automerge")
        self.assertEqual(automerge[1], "juniper-ml")
        release = next(c for c in rec.calls if c[0] == "create_release")
        self.assertEqual(release[1], "juniper-cascor-client")
        self.assertEqual(release[2], "v0.5.0")  # the owning-repo tag


class CreateReleaseTempNotesTest(unittest.TestCase):
    """The 07-19 micro-fix: the Release --notes-file is rendered to a SCRATCH temp path, never written
    into any checkout (the stray-untracked-file bug). Drives the LIVE create_release seam member."""

    def test_notes_file_is_a_scratch_temp_path_cleaned_up_and_never_in_the_checkout(self):
        repo = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(repo, ignore_errors=True))
        (repo / "notes" / "releases").mkdir(parents=True)
        seen: dict = {}

        def rec_gh(args, timeout=90):
            i = args.index("--notes-file")
            p = Path(args[i + 1])
            seen["path"] = p
            seen["content"] = p.read_text(encoding="utf-8")  # the temp file exists AT CALL TIME
            seen["under_checkout"] = str(p).startswith(str(repo))
            return "https://github.com/pcalnon/juniper-ml/releases/tag/v0.6.0"

        def rec_git(repo_dir, args, timeout=120, check=True):
            return ""

        src = ce.make_live_sources("pcalnon", repo, repo.parent, gh=rec_gh, git=rec_git)
        url = src.create_release("juniper-ml", "v0.6.0", "juniper-ml v0.6.0", "notes/releases/RELEASE_NOTES_v0.6.0.md", "the notes body\n")
        self.assertTrue(url)
        self.assertEqual(seen["content"], "the notes body\n")  # content rendered to the temp file
        self.assertFalse(seen["under_checkout"], "the --notes-file must be a scratch path OUTSIDE the checkout")
        self.assertFalse(seen["path"].exists(), "the temp notes file must be cleaned up after the release cut")
        # the checkout was never dirtied by a stray archived notes file
        self.assertFalse((repo / "notes" / "releases" / "RELEASE_NOTES_v0.6.0.md").exists())


class LiveSeamRepoBoundTest(unittest.TestCase):
    """The LIVE seam bounds every --repo to the registry-derived allowlist (Phase 4.1). Cross-repo is
    expressed by --repo owner/<owning-of-the-8>; anything else raises before gh runs -- hermetically."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.allowed = frozenset({"pcalnon/juniper-ml", "pcalnon/juniper-cascor-client"})
        self.calls = []

    def _gh(self, args, timeout=90):
        self.calls.append(list(args))
        if (args[0], args[1]) in (("pr", "list"), ("run", "list")):
            return "[]"
        return "https://github.com/pcalnon/x/1"

    def _git(self, repo_dir, args, timeout=120, check=True):
        return ""

    def _src(self):
        return ce.make_live_sources("pcalnon", self.tmp, self.tmp.parent, allowed_repos=self.allowed, gh=self._gh, git=self._git)

    def test_cross_repo_release_on_allowed_owning_repo_passes(self):
        url = self._src().create_release("juniper-cascor-client", "v0.5.0", "juniper-cascor-client v0.5.0", "notes/releases/RELEASE_NOTES_juniper-cascor-client_v0.5.0.md", "notes\n")
        self.assertTrue(url)
        rel = next(a for a in self.calls if a[:2] == ["release", "create"])
        self.assertIn("--repo", rel)
        self.assertIn("pcalnon/juniper-cascor-client", rel)  # cross-repo --repo, no widened verb surface
        self.assertNotIn("--verify-tag", rel)
        self.assertIn("--latest=false", rel)

    def test_release_on_repo_outside_allowlist_raises_before_gh(self):
        with self.assertRaises(ce.SeamViolation):
            self._src().create_release("juniper-not-a-publishing-repo", "v1", "t", "n", "c")
        # nothing reached the recording gh (the guard raised before the call)
        self.assertFalse(any(a[:2] == ["release", "create"] for a in self.calls))

    def test_archive_pr_and_release_split_are_both_within_the_allowlist(self):
        src = self._src()
        src.open_archive_pr("juniper-ml", "main", "release-notes/juniper-cascor-client-v0.5.0", "notes/releases/RELEASE_NOTES_juniper-cascor-client_v0.5.0.md", "body\n", "release-notes: juniper-cascor-client v0.5.0", "pr body")
        src.create_release("juniper-cascor-client", "v0.5.0", "t", "n", "c")
        for args in self.calls:
            if "--repo" in args:
                slug = args[args.index("--repo") + 1]
                self.assertIn(slug, self.allowed, args)


# ── Phase 4.3: graceful HALT-issue degradation (App token may lack the Issues permission) ─────


class FileHaltIssueDegradationTest(unittest.TestCase):
    """Deliverable-2 unit coverage of ``_file_halt_issue``: the HALT-issue upsert degrades GRACEFULLY on a
    gh-issue-API failure (most plausibly the cross-repo App token lacking the Issues permission, plan S11)
    -- a LOUD log line + a step-summary-visible ``halt_issue_failed`` flag, never a crash -- while a
    ``SeamViolation`` (an R7 *code* bug) still propagates and a missing seam member raises."""

    def _issue(self):
        return ce.halt_issue_payload("juniper-service-core", "0.5.0", "main-ci-not-green", "target main CI is red", "2026-07-17")

    def _src_with_upsert(self, fn):
        src = _sources()  # read-only base seam (upsert_halt_issue starts None)
        src.upsert_halt_issue = fn
        return src

    def test_happy_path_records_issue_url(self):
        src = self._src_with_upsert(lambda repo, title, body: "https://github.com/pcalnon/juniper-ml/issues/7")
        result = {"pypi_name": "juniper-service-core", "notes": []}
        ce._file_halt_issue(src, "juniper-ml", self._issue(), result)
        self.assertEqual(result["issue_url"], "https://github.com/pcalnon/juniper-ml/issues/7")
        self.assertNotIn("halt_issue_failed", result)  # no degradation flag on the happy path

    def test_source_error_degrades_loudly_without_raising(self):
        def boom(repo, title, body):
            raise ce.SourceError("gh failed (issue create): HTTP 403: Resource not accessible by integration")

        src = self._src_with_upsert(boom)
        result = {"pypi_name": "juniper-service-core", "notes": []}
        warns = []
        ce._file_halt_issue(src, "juniper-ml", self._issue(), result, warn=warns.append)  # must NOT raise
        self.assertIsNone(result["issue_url"])
        self.assertTrue(result["halt_issue_failed"])
        self.assertIn("403", result["halt_issue_error"])
        self.assertTrue(warns and "could NOT file the HALT issue" in warns[0])  # the loud operator log line
        self.assertTrue(any("Issues permission" in n for n in result["notes"]))  # the step-summary-visible note

    def test_seam_violation_still_propagates(self):
        def bug(repo, title, body):
            raise ce.SeamViolation("R7: forbidden gh token")  # a code bug, NOT a runtime condition

        src = self._src_with_upsert(bug)
        result = {"pypi_name": "juniper-service-core", "notes": []}
        with self.assertRaises(ce.SeamViolation):  # never swallowed by the SourceError degrade
            ce._file_halt_issue(src, "juniper-ml", self._issue(), result)
        self.assertNotIn("halt_issue_failed", result)

    def test_missing_seam_member_raises_source_error(self):
        src = _sources()  # upsert_halt_issue is None (a developer wiring error, raised OUTSIDE the try)
        result = {"pypi_name": "juniper-service-core", "notes": []}
        with self.assertRaises(ce.SourceError):
            ce._file_halt_issue(src, "juniper-ml", self._issue(), result)


class ExecuteHaltIssueDegradationTest(unittest.TestCase):
    """execute_ceremony surfaces the degradation end-to-end: both a precondition HALT and a TestPyPI HALT
    stay HALTED (never crash) when the gh-issue-API fails, flagging halt_issue_failed for the step summary."""

    def _raising_src(self, exc, **over):
        rec = _Recorder()
        src = _sources(recorder=rec, **over)

        def boom(repo, title, body):
            rec.calls.append(("upsert_halt_issue", repo, title))
            raise exc

        src.upsert_halt_issue = boom
        return rec, src

    def test_precondition_halt_degrades(self):
        rec, src = self._raising_src(ce.SourceError("HTTP 403: Resource not accessible by integration"), main_ci="failure")
        plan = ce.plan_ceremony(_entry(), _manifest_pkg(), src, REPO_ROOT, REPO_ROOT.parent, "2026-07-17")
        self.assertEqual(plan.state, "HALTED")
        result = ce.execute_ceremony(plan, src)  # must NOT raise
        self.assertEqual(result["state"], "HALTED")
        self.assertTrue(result["halt_issue_failed"])
        self.assertIsNone(result["issue_url"])
        self.assertTrue(any(c[0] == "upsert_halt_issue" for c in rec.calls))  # it DID try

    def test_testpypi_halt_degrades(self):
        rec, src = self._raising_src(ce.SourceError("HTTP 403"), run_status=FAILED_TESTPYPI_RUN)
        plan = ce.plan_ceremony(_entry(), _manifest_pkg(), src, REPO_ROOT, REPO_ROOT.parent, "2026-07-17")
        result = ce.execute_ceremony(plan, src, monitor_kwargs={"timeout_seconds": 0, "sleep": lambda s: None})  # must NOT raise
        self.assertEqual(result["state"], "HALTED")
        self.assertTrue(result["halt_issue_failed"])


class ExecuteOutputFormatTest(unittest.TestCase):
    """main(--execute) emits one stable ``ceremony-result:`` line per package (the workflow ceremony step
    summary parses these). Covers a happy PENDING_PYPI_APPROVAL line and a DEGRADED HALT (issue_failed=1)."""

    def _manifest_file(self, *pkgs):
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump({"schema": "juniper-release-train/manifest/v1", "packages": list(pkgs)}, fh)
        fh.close()
        self.addCleanup(lambda: Path(fh.name).unlink(missing_ok=True))
        return fh.name

    def _fields(self, line):
        return dict(tok.split("=", 1) for tok in line.split() if "=" in tok)

    def _result_line(self, text):
        return next(ln for ln in text.splitlines() if ln.startswith("ceremony-result:"))

    def test_execute_emits_pending_result_line(self):
        rec = _Recorder()
        src = _sources(recorder=rec, run_status=PENDING_RUN)
        manifest = self._manifest_file(_manifest_pkg())
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ce.main(["--manifest", manifest, "--execute", "--repo-root", str(REPO_ROOT), "--registry", str(UTIL_DIR / "registry.yaml"), "--release-date", "2026-07-17"], sources=src)
        self.assertEqual(rc, 0)
        f = self._fields(self._result_line(buf.getvalue()))
        self.assertEqual(f["plan"], "CEREMONY_PLANNED")
        self.assertEqual(f["state"], "PENDING_PYPI_APPROVAL")
        self.assertEqual(f["pkg"], "juniper-service-core")
        self.assertEqual(f["version"], "0.5.0")
        self.assertEqual(f["issue_failed"], "0")
        self.assertNotEqual(f["release"], "-")  # a Release URL was recorded

    def test_execute_emits_degraded_halt_result_line(self):
        rec = _Recorder()
        src = _sources(recorder=rec, main_ci="failure")

        def boom(repo, title, body):
            raise ce.SourceError("HTTP 403")

        src.upsert_halt_issue = boom
        manifest = self._manifest_file(_manifest_pkg())
        buf, err = io.StringIO(), io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            rc = ce.main(["--manifest", manifest, "--execute", "--repo-root", str(REPO_ROOT), "--registry", str(UTIL_DIR / "registry.yaml"), "--release-date", "2026-07-17"], sources=src)
        self.assertEqual(rc, 1)  # HALTED -> exit 1 (owner attention), NOT a crash (exit 2)
        f = self._fields(self._result_line(buf.getvalue()))
        self.assertEqual(f["state"], "HALTED")
        self.assertEqual(f["issue_failed"], "1")
        self.assertIn("could NOT file the HALT issue", err.getvalue())  # the loud log line reached stderr

    def test_execute_no_bumped_packages_prints_nothing_to_do(self):
        # an UP_TO_DATE manifest package is not ceremonial -> no ceremony-result lines, a clean "nothing to do".
        src = _sources()
        manifest = self._manifest_file(_manifest_pkg(classification="UP_TO_DATE"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ce.main(["--manifest", manifest, "--execute", "--repo-root", str(REPO_ROOT), "--registry", str(UTIL_DIR / "registry.yaml"), "--release-date", "2026-07-17"], sources=src)
        self.assertEqual(rc, 0)
        self.assertIn("no BUMPED_NOT_RELEASED packages", buf.getvalue())
        self.assertNotIn("ceremony-result:", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
