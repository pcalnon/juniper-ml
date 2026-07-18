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
from contextlib import redirect_stdout
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
        result = ce.execute_ceremony(plan, src, monitor_kwargs={"max_attempts": 1, "sleep": lambda s: None})
        self.assertEqual(result["state"], "PENDING_PYPI_APPROVAL")
        self.assertIsNotNone(result["pr_url"])
        self.assertIsNotNone(result["release_url"])
        kinds = [c[0] for c in rec.calls]
        self.assertEqual(kinds, ["open_archive_pr", "enable_automerge", "create_release"])

    def test_execute_auto_merge_degrades_gracefully(self):
        rec, src = self._mk(run_status=PENDING_RUN, automerge_ok=False)
        plan = ce.plan_ceremony(_entry(), _manifest_pkg(), src, REPO_ROOT, REPO_ROOT.parent, "2026-07-17")
        result = ce.execute_ceremony(plan, src, monitor_kwargs={"max_attempts": 1, "sleep": lambda s: None})
        # not a halt -- still parks at the pypi gate; a note records the owner one-click fallback.
        self.assertEqual(result["state"], "PENDING_PYPI_APPROVAL")
        self.assertFalse(result.get("auto_merge_enabled"))
        self.assertTrue(any("one-click" in n for n in result["notes"]))

    def test_execute_testpypi_failure_halts_and_files_issue(self):
        rec, src = self._mk(run_status=FAILED_TESTPYPI_RUN)
        plan = ce.plan_ceremony(_entry(), _manifest_pkg(), src, REPO_ROOT, REPO_ROOT.parent, "2026-07-17")
        result = ce.execute_ceremony(plan, src, monitor_kwargs={"max_attempts": 1, "sleep": lambda s: None})
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


if __name__ == "__main__":
    unittest.main()
