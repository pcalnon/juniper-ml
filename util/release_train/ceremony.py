#!/usr/bin/env python3
"""Juniper PyPI release-train ceremony engine (plan S5.3/S7/S8/S9.3/S10; Phase 3 step 3.2).

Consumes the release-manifest JSON emitted by ``detect.py`` and, for every package the detector
classified ``BUMPED_NOT_RELEASED`` (``declared > released``; no Release cut yet -- plan S5.1), runs the
**automated ceremony**: the middle arc R6 automates without ever touching a gate (plan S5.3). The
version bump that *made* the package ``BUMPED_NOT_RELEASED`` already rode the owner-approved proposal PR
(Gate 1), and the PyPI deploy at the very end still waits at the ``pypi`` environment gate (Gate 2). The
ceremony only automates the middle: notes authoring + central archival, the exempt archive PR, the
Release cut, and TestPyPI verification -- **never** a version bump without approval and **never** a PyPI
deploy without approval.

Per BUMPED_NOT_RELEASED package (in-repo / juniper-ml ONLY this phase -- the ``WRITABLE_REPO`` guard,
reused from ``propose.py``; Phase 4's GitHub App lifts it):

  1. **Preconditions (plan S8)** -- any failure HALTs *that* package with a clear reason and a
     deduplicated GitHub-issue payload (title keyed on ``pypi_name`` + reason); a halt never blocks the
     other packages. Checked: target ``main`` CI green; the ``declared >= released`` re-check against
     live PyPI truth; a non-empty ``CHANGELOG [<version>]`` section to source the notes; (during the
     monitor) TestPyPI install-verify success before Gate 2.
  2. **Final central notes** -- build the archive file (``notes_render``, from the released
     sub-package's ``CHANGELOG [<version>]`` section; ``archive_name`` from ``registry.yaml``).
  3. **Exempt archive PR** -- open the add-only, single-file PR (the thing the S7.2 archive-guard proves).
  4. **Auto-merge** -- enable ``gh pr merge --auto --squash`` on it; if the repo has ``allow_auto_merge``
     off (step 3.3 has not landed yet) enabling **degrades gracefully** to the owner one-click merge,
     it is NOT a halt.
  5. **Cut the Release** -- ``gh release create <tag> --latest=false --notes-file <archive>``. The
     Release **creates** the tag for a sub-package (procedure S11.4), so there is deliberately **no**
     ``--verify-tag`` (there is no pre-existing tag to verify).
  6. **Monitor** -- watch the triggered publish run; the run legitimately parks at the ``pypi``
     environment gate: that terminal state ``PENDING_PYPI_APPROVAL`` **is success for the train** (plan
     S5.1 terminal-healthy). A TestPyPI-verify failure before Gate 2 is a HALT.

**R7 hard invariant (plan S9.3), enforced in code AND asserted by the tests:** the ``gh`` surface the
ceremony's write identity may touch is exactly {``pr create``, ``pr merge --auto``, ``release create``,
``run list/view``, ``issue create/edit``} plus the read guards it needs -- and **nothing** that mutates a
deployment environment or a reviewer. Every live ``gh`` call is routed through ``_assert_gh_allowed``,
which raises ``SeamViolation`` for any subcommand outside ``GH_ALLOWED_SURFACE`` or carrying a forbidden
token (``api`` / ``environment`` / ``deployment`` / ``review`` / ``--admin`` / ...), a bare ``pr merge``
without ``--auto``, or a ``release create --verify-tag``.

**Idempotent re-entry (plan S8 last row):** a re-run re-computes state from PyPI/Release truth -- if PyPI
already serves the target version the run is a no-op; if the Release tag already exists it resumes at the
monitor (never re-cutting, never duplicating the archive PR); an already-open archive PR / an already-on-
``main`` archive file is reused, not duplicated.

Every external effect is injected through a ``CeremonySources`` seam so ``tests/test_release_train_
ceremony.py`` is fully hermetic (no network / gh / git / repo writes). ``--dry-run`` is the DEFAULT: it
prints the complete ceremony *script of actions* and writes nothing / opens nothing / cuts nothing.
``--execute`` (opt-in, overridden by ``--dry-run`` for safety) performs the actions -- it is wired for a
later workflow step and is **never** run against the real repo in this change. ``util/`` is not
pre-commit-lint-gated, so that unittest IS the gate (the ``env_floor_drift_check`` precedent, shared with
``detect.py`` / ``propose.py``).

Exit codes: 0 clean run (no halts), 1 at least one package HALTED (owner attention -- an issue was
filed/updated), 2 invocation error (bad manifest / empty registry / unknown ``--package``).

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-17
Status: permanent utility (Phase 3, exempt-archive ceremony engine)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - only the gh/git binaries with fixed argv (no shell)
import sys
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

# Same-directory siblings; resolvable both when run as a script (script dir on sys.path[0]) and under
# the tests' ``sys.path.insert(UTIL_DIR)`` idiom (mirrors test_release_train_detect / _propose).
import detect  # noqa: E402
import notes_render  # noqa: E402

SourceError = detect.SourceError  # reuse the detector's environmental-failure type

DEFAULT_OWNER = os.environ.get("JUNIPER_RELEASE_TRAIN_OWNER", "pcalnon")

# Only this classification enters the ceremony (plan S5.1/S5.3).
CEREMONIAL = "BUMPED_NOT_RELEASED"

# The single repo whose contents a ``--execute`` ceremony run may write. The Phase-3 pilot runs inside
# the juniper-ml checkout under a juniper-ml-scoped ``GITHUB_TOKEN`` (plan S9.2), which can push a branch
# + open a PR + cut a Release only in juniper-ml -- the meta-package and its six co-located sub-packages.
# Sibling-repo packages are SKIPPED (deferred to Phase 4's GitHub App identity), never attempted. Reuses
# the ``propose.py`` WRITABLE_REPO pattern; overridable for tests / a future multi-repo identity.
WRITABLE_REPO = os.environ.get("JUNIPER_RELEASE_TRAIN_WRITABLE_REPO", detect.META_REPO)

# Monitor bounds (plan S8 TestPyPI gate -> the ``pypi`` env-gate; §12 step 3.2). The publish workflow
# builds + verifies on TestPyPI before its ``pypi``-environment deploy job parks at the owner-gated
# approval, at which point the run's top-level GitHub status becomes ``waiting`` (verified: ``waiting`` is
# a documented workflow-run status and ``gh run view --json status`` is a raw passthrough of that REST
# field). The monitor polls for a BOUNDED wall clock at a short fixed interval so it actually observes
# that ``waiting`` state (-> PENDING_PYPI_APPROVAL) instead of giving up early and reporting IN_PROGRESS.
DEFAULT_MONITOR_TIMEOUT_SECONDS = 900  # ~15 min: headroom for build + TestPyPI publish + install-verify + reaching the gate
MONITOR_POLL_SECONDS = 15  # short fixed poll interval (keeps gh read volume bounded)


# ── R7 gh write-identity surface (plan S9.3) ─────────────────────────────────


class SeamViolation(RuntimeError):
    """A ``gh`` call outside the R7-permitted surface -- a *code* bug, never a runtime condition."""


# The EXACT mutating ``gh`` surface the ceremony's write identity may use (plan S9.3 / R7). Nothing here
# mutates a deployment environment or a reviewer; the PyPI deploy stays owner-gated at the ``pypi`` env.
GH_MUTATING_SURFACE = frozenset(
    {
        ("pr", "create"),  # open the exempt archive PR
        ("pr", "merge"),  # enable --auto --squash (NEVER a bare immediate merge; --auto required)
        ("release", "create"),  # cut the Release (CREATES the tag for a sub-package; no --verify-tag)
        ("issue", "create"),  # open a dedup HALT issue
        ("issue", "edit"),  # update an existing dedup HALT issue
    }
)
# The read-only guards the ceremony needs (dup-guard, idempotency, monitoring). All inherently benign.
GH_READONLY_SURFACE = frozenset(
    {
        ("pr", "list"),  # dup-guard + archive-PR idempotency
        ("release", "view"),  # idempotency: has the Release already been cut?
        ("run", "list"),  # target main-CI status + find the triggered publish run
        ("run", "view"),  # monitor the publish run's jobs/conclusion
        ("issue", "list"),  # dedup a HALT issue
    }
)
GH_ALLOWED_SURFACE = GH_MUTATING_SURFACE | GH_READONLY_SURFACE

# Tokens that must NEVER appear in any ``gh`` argv the ceremony builds -- the R7 red lines. ``api`` is
# forbidden so no raw REST call can reach an environment/deployment endpoint; ``review`` / ``approve``
# would touch a reviewer; ``--admin`` would bypass required checks; env/deploy/secret/variable/ruleset
# are environment- or policy-mutating.
GH_FORBIDDEN_TOKENS = frozenset(
    {
        "api",
        "review",
        "approve",
        "environment",
        "environments",
        "deployment",
        "deployments",
        "secret",
        "secrets",
        "variable",
        "variables",
        "ruleset",
        "rulesets",
        "--admin",
    }
)


def _assert_gh_allowed(args: list) -> None:
    """Raise ``SeamViolation`` unless ``gh <args>`` is within the R7-permitted surface (plan S9.3).

    Enforces: the leading ``(subcommand, verb)`` pair is in ``GH_ALLOWED_SURFACE``; no argv token is in
    ``GH_FORBIDDEN_TOKENS``; ``pr merge`` always carries ``--auto`` (never a bare immediate merge); and
    ``release create`` never carries ``--verify-tag`` (the Release CREATES the tag for a sub-package)."""
    if len(args) < 2:
        raise SeamViolation(f"gh call too short to validate: {args!r}")
    pair = (args[0], args[1])
    forbidden = [tok for tok in args if tok in GH_FORBIDDEN_TOKENS]
    if forbidden:
        raise SeamViolation(f"forbidden gh token(s) {forbidden} in {args!r} -- R7 permits no environment/deployment/reviewer mutation")
    if pair not in GH_ALLOWED_SURFACE:
        raise SeamViolation(f"gh surface {pair} not in the R7 allowlist {sorted(GH_ALLOWED_SURFACE)}")
    if pair == ("pr", "merge") and "--auto" not in args:
        raise SeamViolation("gh pr merge must carry --auto (the ceremony never immediately merges; it enables auto-merge behind the guard)")
    if pair == ("release", "create") and "--verify-tag" in args:
        raise SeamViolation("gh release create must NOT carry --verify-tag (the Release CREATES the sub-package tag; there is no pre-existing tag to verify)")


# ── low-level gh / git runners (fixed argv, no shell) ────────────────────────


def _gh(args: list, timeout: int = 90) -> "str | None":
    """Run ``gh <args>``. None on a 404-ish 'no result'; SourceError on any transport/auth failure."""
    try:
        proc = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603,B607 - fixed argv, no shell
    except FileNotFoundError as exc:
        raise SourceError("gh CLI not found (install/authenticate GitHub CLI)") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"gh timed out: {' '.join(args)}") from exc
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        low = stderr.lower()
        if "not found" in low or "no pull requests" in low or "release not found" in low or "no releases" in low:
            return None
        raise SourceError(f"gh failed ({' '.join(args[:3])}): {stderr[:200]}")
    return proc.stdout


def _git(repo_dir: Path, args: list, timeout: int = 120, check: bool = True) -> "str | None":
    """Run ``git -C <repo_dir> <args>`` (fixed argv, no shell). None on non-zero when ``check`` is False."""
    try:
        proc = subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603,B607 - fixed argv
    except FileNotFoundError as exc:
        raise SourceError("git not found (needed for --execute)") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"git timed out: {' '.join(args)}") from exc
    if proc.returncode != 0:
        if check:
            raise SourceError(f"git failed ({' '.join(args[:3])}): {(proc.stderr or '').strip()[:200]}")
        return None
    return proc.stdout


# ── branch capture / restore (leave the operator's checkout as we found it) ──


def _warn(msg: str) -> None:
    """Best-effort operator warning to stderr (never raises; used by the non-fatal restore path)."""
    print(f"WARNING: {msg}", file=sys.stderr)


def _capture_git_ref(repo_dir: Path, git: Callable) -> "tuple[str, str] | None":
    """The ref to restore the checkout to after the ceremony's branch ops (recorded BEFORE any switch).

    ``("branch", <name>)`` when HEAD is on a branch, ``("detached", <sha>)`` when HEAD is detached, or
    ``None`` when git cannot answer (a later restore then safely no-ops). Uses the SAME injected ``git``
    runner the branch ops use, so it is hermetic under the seam-surface test."""
    branch = git(repo_dir, ["symbolic-ref", "--quiet", "--short", "HEAD"], 30, False)
    if branch and branch.strip():
        return ("branch", branch.strip())
    sha = git(repo_dir, ["rev-parse", "HEAD"], 30, False)
    if sha and sha.strip():
        return ("detached", sha.strip())
    return None


def _restore_git_ref(repo_dir: Path, git: Callable, start_ref: "tuple[str, str] | None", warn: "Callable[[str], None] | None" = None) -> bool:
    """Restore the checkout to ``start_ref`` after the archive-PR branch ops -- but NEVER clobber work.

    Switches back only when the working tree is CLEAN (``git status --porcelain`` empty); a dirty tree is
    left on the ceremony branch with a warning (the operator's uncommitted changes are never discarded).
    A best-effort courtesy, not a hard ceremony step: returns True iff it switched back. Mirrors how
    ``open_archive_pr`` does branch ops -- ``git switch`` through the injected runner."""
    if start_ref is None:
        return False
    kind, ref = start_ref
    status = git(repo_dir, ["status", "--porcelain"], 30, False)
    if status is None:
        return False  # cannot determine cleanliness -> do not risk a clobber
    if status.strip():
        (warn or _warn)(f"release-train ceremony: {repo_dir} has uncommitted changes; left the checkout on the ceremony branch (restore to {ref} skipped -- a dirty tree is never clobbered)")
        return False
    git(repo_dir, ["switch", "--detach", ref] if kind == "detached" else ["switch", ref], 60, False)
    return True


# ── small pure helpers ───────────────────────────────────────────────────────


def release_tag(entry: "detect.PackageEntry", version: str) -> str:
    """The git tag the Release CREATES, from the registry ``tag_pattern`` (procedure S11.4).

    ``v*`` -> ``v0.5.0`` (meta); ``juniper-service-core-v*`` -> ``juniper-service-core-v0.5.0`` (else)."""
    pat = entry.tag_pattern
    return (pat[:-1] + version) if pat.endswith("*") else f"{pat}{version}"


def archive_branch(pypi_name: str, version: str) -> str:
    """Head branch for the exempt add-only archive PR (distinct from propose.py's ``release/`` branch)."""
    return f"release-notes/{pypi_name}-v{version}"


def changelog_rel(entry: "detect.PackageEntry") -> str:
    return os.path.normpath(os.path.join(entry.path, "CHANGELOG.md")).replace(os.sep, "/")


def archive_relpath(entry: "detect.PackageEntry", version: str) -> str:
    """Central archive path from the registry ``archive_name`` template (procedure S11.3 / plan S10.2)."""
    return f"notes/releases/{entry.archive_name.format(version=version)}"


def infer_bump(old_version: "str | None", new_version: str) -> str:
    """Derive the SemVer bump label from the released -> declared delta (for the notes Release-Type)."""

    def triple(v: "str | None") -> tuple:
        m = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)", v or "0.0.0")
        return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)

    old, new = triple(old_version), triple(new_version)
    if new[0] != old[0]:
        return "major"
    if new[1] != old[1]:
        return "minor"
    if new[2] != old[2]:
        return "patch"
    return "minor"


def changelog_version_section(changelog_text: str, version: str) -> "OrderedDict[str, list]":
    """Parse the ``## [<version>]`` block into ``{Category: [bullets]}`` (Keep-a-Changelog).

    This is the section the proposal PR created when it moved ``[Unreleased] -> [<version>]`` (plan
    S5.4); the ceremony sources the FINAL notes from it. Mirrors ``notes_render.parse_unreleased`` but
    anchored on the concrete version heading, and reuses its bullet grouping."""
    result: "OrderedDict[str, list]" = OrderedDict()
    if not changelog_text:
        return result
    lines = changelog_text.splitlines()
    vpat = re.compile(r"^##\s*\[?" + re.escape(version) + r"\]?", re.IGNORECASE)
    start = None
    for i, line in enumerate(lines):
        if vpat.match(line.strip()):
            start = i + 1
            break
    if start is None:
        return result
    current_cat: "str | None" = None
    body: list = []
    for line in lines[start:]:
        if re.match(r"^##\s", line) and not re.match(r"^###", line):
            break  # next version section
        hm = re.match(r"^###\s+([A-Za-z]+)", line.strip())
        if hm:
            if current_cat is not None:
                bullets = notes_render._split_bullets(body)
                if bullets:
                    result[current_cat] = bullets
            current_cat = hm.group(1)
            body = []
            continue
        if current_cat is not None:
            body.append(line)
    if current_cat is not None:
        bullets = notes_render._split_bullets(body)
        if bullets:
            result[current_cat] = bullets
    return result


def writable_repo_skip_reason(repo: str, writable_repo: str = WRITABLE_REPO) -> "str | None":
    """Reason to SKIP a package because it lives outside the writable repo (Phase-3 in-repo pilot).

    ``None`` when ``repo`` is the writable repo; else a clear reason. The pilot workflow's single-repo
    ``GITHUB_TOKEN`` can open a PR + cut a Release only in ``writable_repo`` (juniper-ml); a sibling-repo
    package is deferred to Phase 4's GitHub App identity (plan S9.2 / S12 step 4.1), never attempted."""
    if repo == writable_repo:
        return None
    return f"cross-repo: package lives in '{repo}', not the writable repo '{writable_repo}' -- the Phase-3 pilot's single-repo GITHUB_TOKEN cannot open a PR / cut a Release there (Phase 4's GitHub App identity lifts this, plan S9.2 / S12 step 4.1)"


def find_open_archive_pr(open_prs: list, branch: str) -> "dict | None":
    """An open PR whose head is this package's archive branch -> reuse it (idempotency, no duplicate)."""
    for pr in open_prs or []:
        if (pr or {}).get("headRefName") == branch:
            return pr
    return None


def halt_issue_payload(pypi_name: str, version: "str | None", reason_key: str, detail: str, when: str) -> dict:
    """The deduplicated HALT-issue payload (plan S8/S11). Title keyed on ``pypi_name`` + ``reason_key``."""
    vtag = f" v{version}" if version else ""
    title = f"[release-train] HALT: {pypi_name} -- {reason_key}"
    body = (
        f"The Juniper release-train ceremony HALTED **{pypi_name}**{vtag} and took no further action on this package.\n\n"
        f"- **Reason ({reason_key}):** {detail}\n"
        f"- **Detected:** {when}\n"
        f"- **Policy:** release-train plan S8 -- a precondition failed, so this package HALTs, this dedup issue is opened/updated, and the ceremony never proceeds on it. A halt on one package does not block the others.\n\n"
        f"Resolve the condition and re-run the ceremony: it re-computes state from PyPI/Release truth and resumes (it never duplicates an archive PR)."
    )
    return {"title": title, "body": body, "reason_key": reason_key}


def classify_publish_run(run: "dict | None") -> str:
    """Map a publish run's status to a ceremony terminal signal (plan S8 TestPyPI gate / S5.1).

    Returns: ``PENDING_PYPI_APPROVAL`` (TestPyPI verify passed; the pypi deploy job is parked at the env
    gate -- SUCCESS for the train), ``HALT_TESTPYPI`` (TestPyPI verify failed before Gate 2),
    ``HALT_PUBLISH`` (the run failed otherwise), ``RELEASED`` (both gates done -- owner already
    approved), ``IN_PROGRESS`` (still running -> keep polling), ``NOT_FOUND`` (no run yet)."""
    if not run:
        return "NOT_FOUND"
    jobs = run.get("jobs") or []

    def named(sub: str) -> list:
        return [j for j in jobs if sub in (j.get("name") or "").lower()]

    testpypi_jobs = named("testpypi")
    pypi_jobs = [j for j in jobs if "pypi" in (j.get("name") or "").lower() and "testpypi" not in (j.get("name") or "").lower()]

    if any((j.get("conclusion") or "").lower() == "failure" for j in testpypi_jobs):
        return "HALT_TESTPYPI"

    run_status = (run.get("status") or "").lower()
    run_conclusion = (run.get("conclusion") or "").lower()
    if run_status == "completed":
        if run_conclusion == "success":
            return "RELEASED"
        if run_conclusion in ("failure", "cancelled", "timed_out"):
            return "HALT_PUBLISH"

    testpypi_ok = bool(testpypi_jobs) and all((j.get("conclusion") or "").lower() == "success" for j in testpypi_jobs)
    pypi_parked = bool(pypi_jobs) and all((j.get("status") or "").lower() in ("waiting", "queued", "pending", "") for j in pypi_jobs)
    # The run's top-level status is 'waiting' while parked at the owner-gated `pypi` deployment env
    # (verified: a documented workflow-run status that `gh run view --json status` passes through). The
    # job-level (testpypi succeeded + pypi job parked) check is the belt-and-suspenders fallback.
    if run_status == "waiting" or (testpypi_ok and pypi_parked):
        return "PENDING_PYPI_APPROVAL"
    return "IN_PROGRESS"


# ── data model ───────────────────────────────────────────────────────────────


@dataclass
class CeremonyAction:
    """One planned ceremony step. ``kind`` is the machine label the tests assert the sequence of."""

    kind: str  # open_archive_pr | enable_auto_merge | cut_release | monitor_publish | halt_issue
    summary: str
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"kind": self.kind, "summary": self.summary, "detail": self.detail}


@dataclass
class CeremonyPlan:
    """The full ceremony plan for one BUMPED_NOT_RELEASED package (or a halt / skip / no-op)."""

    pypi_name: str
    repo: str
    released_version: "str | None"
    target_version: "str | None"
    tag: "str | None" = None
    state: str = "CEREMONY_PLANNED"  # CEREMONY_PLANNED | RESUME_MONITOR | ALREADY_RELEASED | HALTED | SKIPPED_CROSS_REPO
    halted: bool = False
    halt_reason: "str | None" = None
    skipped_reason: "str | None" = None
    actions: list = field(default_factory=list)
    archive_relpath: "str | None" = None
    archive_content: "str | None" = None
    archive_branch: "str | None" = None
    issue: "dict | None" = None
    notes: list = field(default_factory=list)

    @property
    def action_kinds(self) -> list:
        return [a.kind for a in self.actions]

    def to_dict(self) -> dict:
        return {
            "pypi_name": self.pypi_name,
            "repo": self.repo,
            "released_version": self.released_version,
            "target_version": self.target_version,
            "tag": self.tag,
            "state": self.state,
            "halted": self.halted,
            "halt_reason": self.halt_reason,
            "skipped_reason": self.skipped_reason,
            "archive_relpath": self.archive_relpath,
            "archive_branch": self.archive_branch,
            "issue": self.issue,
            "actions": [a.to_dict() for a in self.actions],
            "notes": self.notes,
        }


# ── injectable seam (all external effects) ───────────────────────────────────


@dataclass
class CeremonySources:
    """External effects the ceremony needs, injected for hermetic testing.

    The read/query members are used by the planner (safe in ``--dry-run``); the write members
    (``open_archive_pr`` / ``enable_automerge`` / ``create_release`` / ``upsert_halt_issue``) are
    execute-only and may be ``None`` in a read-only seam."""

    pypi_json: Callable[[str], "dict | None"]
    read_file: Callable[["detect.PackageEntry", str], "str | None"]
    main_ci_conclusion: Callable[[str], "str | None"]
    list_open_prs: Callable[[str], list]
    release_exists: Callable[[str, str], bool]
    archive_on_main: Callable[[str], bool]
    publish_run_status: Callable[[str, str], "dict | None"]
    open_archive_pr: "Callable[..., str] | None" = None
    enable_automerge: "Callable[..., bool] | None" = None
    create_release: "Callable[..., str] | None" = None
    upsert_halt_issue: "Callable[..., str] | None" = None


def make_live_sources(owner: str, repo_root: Path, ecosystem_root: Path, *, gh: "Callable | None" = None, git: "Callable | None" = None) -> CeremonySources:
    """The live seam. Every ``gh`` call is routed through ``_assert_gh_allowed`` (the R7 code gate).

    ``gh`` / ``git`` are injectable so the seam-surface test can drive the real argv construction with a
    recording fake -- proving the live surface is exactly the R7-permitted set, hermetically."""
    gh = gh or _gh
    git = git or _git

    def _cgh(args: list, timeout: int = 90) -> "str | None":
        _assert_gh_allowed(args)  # CODE half of the R7 invariant: a forbidden call raises before gh runs
        return gh(args, timeout)

    def _repo_dir(repo: str) -> Path:
        return repo_root if repo == detect.META_REPO else (ecosystem_root / repo)

    def pypi_json(name: str) -> "dict | None":
        return detect._http_get_json(detect.PYPI_JSON_URL.format(name=name))

    def read_file(entry: "detect.PackageEntry", filename: str) -> "str | None":
        target = detect.base_dir_for(entry, repo_root, ecosystem_root) / filename
        try:
            return target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def main_ci_conclusion(repo: str) -> "str | None":
        out = _cgh(["run", "list", "--repo", f"{owner}/{repo}", "--branch", "main", "--limit", "1", "--json", "conclusion,status", "--jq", ".[0].conclusion"])
        return (out or "").strip() or None

    def list_open_prs(repo: str) -> list:
        out = _cgh(["pr", "list", "--repo", f"{owner}/{repo}", "--state", "open", "--json", "number,title,headRefName", "--limit", "100"])
        if not out:
            return []
        try:
            return json.loads(out) or []
        except ValueError as exc:
            raise SourceError(f"gh pr list returned non-JSON for {repo}") from exc

    def release_exists(repo: str, tag: str) -> bool:
        out = _cgh(["release", "view", tag, "--repo", f"{owner}/{repo}", "--json", "tagName", "--jq", ".tagName"])
        return bool((out or "").strip())

    def archive_on_main(relpath: str) -> bool:
        # Remote-authoritative git read (no local-branch truth, plan S8 remote-freshness): is the file
        # present on origin/main? A best-effort fetch keeps origin/main current.
        git(_repo_dir(detect.META_REPO), ["fetch", "--quiet", "origin", "main"], 120, False)
        return git(_repo_dir(detect.META_REPO), ["cat-file", "-e", f"origin/main:{relpath}"], 60, False) is not None

    def publish_run_status(repo: str, tag: str) -> "dict | None":
        out = _cgh(["run", "list", "--repo", f"{owner}/{repo}", "--event", "release", "--json", "databaseId,headBranch,displayTitle,status,conclusion", "--limit", "20"])
        runs = json.loads(out) if out else []
        match = next((r for r in runs if tag in (r.get("displayTitle") or "") or tag == (r.get("headBranch") or "")), None)
        if match is None:
            return None
        out2 = _cgh(["run", "view", str(match["databaseId"]), "--repo", f"{owner}/{repo}", "--json", "status,conclusion,jobs"])
        data = json.loads(out2) if out2 else {}
        return {
            "status": data.get("status"),
            "conclusion": data.get("conclusion"),
            "jobs": [{"name": j.get("name"), "status": j.get("status"), "conclusion": j.get("conclusion")} for j in (data.get("jobs") or [])],
        }

    def open_archive_pr(repo: str, base: str, branch: str, relpath: str, content: str, title: str, body: str) -> str:
        rdir = _repo_dir(repo)
        start_ref = _capture_git_ref(rdir, git)  # record the operator's branch BEFORE any switch, to restore on the way out
        try:
            git(rdir, ["switch", "-c", branch, base])
            target = rdir / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            git(rdir, ["add", "--", relpath])
            # -c commit.gpgsign=false: the CI runner has no GPG key and the owner's YubiKey signing config
            # must never reach a headless commit (memory: the YubiKey pinentry landmine).
            git(rdir, ["-c", "commit.gpgsign=false", "commit", "-m", title])
            git(rdir, ["push", "--set-upstream", "origin", branch])
            return (_cgh(["pr", "create", "--repo", f"{owner}/{repo}", "--base", base, "--head", branch, "--title", title, "--body", body]) or "").strip()
        finally:
            # Return the operator to the branch they started on -- even if a step above raised
            # (try/finally). Never clobbers a dirty tree (see _restore_git_ref).
            _restore_git_ref(rdir, git, start_ref)

    def enable_automerge(repo: str, pr: str) -> bool:
        # Graceful degrade (plan S12 step 3.3 not yet landed -> allow_auto_merge may be off): a failure
        # to ENABLE --auto is the owner one-click fallback, NOT a halt. SeamViolation still propagates.
        try:
            _cgh(["pr", "merge", str(pr), "--repo", f"{owner}/{repo}", "--auto", "--squash"])
            return True
        except SourceError:
            return False

    def create_release(repo: str, tag: str, title: str, notes_relpath: str, content: str) -> str:
        rdir = _repo_dir(repo)
        # Write the just-built central notes into the checkout so --notes-file points at the archived
        # content (it is also what the exempt archive PR carries). --latest=false: a sub-package Release
        # never steals the meta-package's "latest" badge (procedure S11.4). NO --verify-tag: the Release
        # CREATES the tag.
        target = rdir / notes_relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return (_cgh(["release", "create", tag, "--repo", f"{owner}/{repo}", "--title", title, "--notes-file", notes_relpath, "--latest=false"]) or "").strip()

    def upsert_halt_issue(repo: str, title: str, body: str) -> str:
        existing = _cgh(["issue", "list", "--repo", f"{owner}/{repo}", "--state", "open", "--search", f"in:title {title}", "--json", "number", "--jq", ".[0].number"])
        num = (existing or "").strip()
        if num:
            return (_cgh(["issue", "edit", num, "--repo", f"{owner}/{repo}", "--body", body]) or "").strip()
        return (_cgh(["issue", "create", "--repo", f"{owner}/{repo}", "--title", title, "--body", body]) or "").strip()

    return CeremonySources(
        pypi_json=pypi_json,
        read_file=read_file,
        main_ci_conclusion=main_ci_conclusion,
        list_open_prs=list_open_prs,
        release_exists=release_exists,
        archive_on_main=archive_on_main,
        publish_run_status=publish_run_status,
        open_archive_pr=open_archive_pr,
        enable_automerge=enable_automerge,
        create_release=create_release,
        upsert_halt_issue=upsert_halt_issue,
    )


# ── planner (pure decisions; reads only) ─────────────────────────────────────


def _halt(plan: CeremonyPlan, reason_key: str, detail: str, when: str) -> CeremonyPlan:
    plan.state = "HALTED"
    plan.halted = True
    plan.halt_reason = detail
    plan.issue = halt_issue_payload(plan.pypi_name, plan.target_version, reason_key, detail, when)
    plan.actions = [CeremonyAction("halt_issue", f"open/update the dedup HALT issue: {plan.issue['title']}", {"issue": plan.issue})]
    return plan


def _monitor_action(tag: str) -> CeremonyAction:
    return CeremonyAction(
        "monitor_publish",
        f"monitor the publish run triggered by Release {tag}; report PENDING_PYPI_APPROVAL when it parks at the pypi env gate (SUCCESS for the train); a TestPyPI-verify failure before Gate 2 HALTs",
        {"tag": tag},
    )


def plan_ceremony(entry: "detect.PackageEntry", pkg: dict, sources: CeremonySources, repo_root: Path, ecosystem_root: Path, when: str) -> CeremonyPlan:
    """Compute the ceremony plan for one BUMPED_NOT_RELEASED manifest package (reads only; no writes)."""
    target = pkg.get("declared_version")
    plan = CeremonyPlan(pypi_name=entry.pypi_name, repo=entry.repo, released_version=pkg.get("released_version"), target_version=target)

    # 0. writable-repo guard (Phase-3 in-repo pilot; reuse propose's WRITABLE_REPO pattern).
    reason = writable_repo_skip_reason(entry.repo)
    if reason is not None:
        plan.state, plan.skipped_reason = "SKIPPED_CROSS_REPO", reason
        return plan

    if not target:
        return _halt(plan, "missing-declared-version", "manifest has no declared_version for a BUMPED_NOT_RELEASED package", when)

    # 1. idempotency + the S8 declared>=released re-check against LIVE PyPI truth (remote-authoritative).
    pypi = sources.pypi_json(entry.pypi_name)
    released_now = (pypi or {}).get("info", {}).get("version") if pypi else None
    plan.released_version = released_now or plan.released_version
    if released_now:
        cmpv = detect.version_cmp(target, released_now)
        if cmpv == 0:
            plan.state = "ALREADY_RELEASED"
            plan.notes.append(f"PyPI already serves {target}: the deploy completed; nothing to do (idempotent no-op).")
            return plan
        if cmpv < 0:
            return _halt(plan, "declared-lt-released-anomaly", f"declared {target} < released {released_now}: a yanked/rolled-back anomaly a human must resolve", when)
    elif plan.released_version:
        return _halt(plan, "pypi-truth-missing", f"manifest said released {plan.released_version} but PyPI now returns no version -- a first-publish/yank a human must resolve (trusted-publisher precheck, plan S8)", when)

    plan.tag = release_tag(entry, target)
    plan.archive_relpath = archive_relpath(entry, target)
    plan.archive_branch = archive_branch(entry.pypi_name, target)

    # 2. S8: target main CI must be green.
    conclusion = sources.main_ci_conclusion(entry.repo)
    if conclusion != "success":
        return _halt(plan, "main-ci-not-green", f"target main CI latest conclusion is {conclusion!r}, not 'success' -- do not cut a Release onto a red main", when)

    # 3. build the FINAL central notes file from the released CHANGELOG [<version>] section.
    clog = sources.read_file(entry, changelog_rel(entry))
    sections = changelog_version_section(clog or "", target)
    if not sections:
        return _halt(plan, "changelog-section-missing", f"no non-empty CHANGELOG [{target}] section to source the release notes from (the proposal PR should have created it)", when)
    bump = infer_bump(plan.released_version, target)
    try:
        plan.archive_content = notes_render.render_notes(entry.pypi_name, target, bump=bump, release_date=when, sections=sections, repo_root=repo_root)
    except OSError as exc:
        return _halt(plan, "notes-render-failed", f"could not render the release notes template: {exc}", when)

    # 4. idempotent re-entry from Release/PR truth (plan S8 last row; dup-guard).
    if sources.release_exists(entry.repo, plan.tag):
        plan.state = "RESUME_MONITOR"
        plan.notes.append(f"Release {plan.tag} already exists: resume monitoring only (no re-cut, no duplicate archive PR).")
        plan.actions = [_monitor_action(plan.tag)]
        return plan

    open_pr = find_open_archive_pr(sources.list_open_prs(entry.repo), plan.archive_branch)
    on_main = sources.archive_on_main(plan.archive_relpath)

    actions: list = []
    if open_pr is not None:
        plan.notes.append(f"archive PR already open (#{open_pr.get('number')} {open_pr.get('headRefName')}): reuse it (no duplicate).")
    elif on_main:
        plan.notes.append(f"archive file already on main ({plan.archive_relpath}): skip the archive PR; cut the Release.")
    else:
        actions.append(CeremonyAction("open_archive_pr", f"open the exempt add-only archive PR ({plan.archive_relpath}) on branch {plan.archive_branch} -- the single-file diff the S7.2 guard proves", {"relpath": plan.archive_relpath, "branch": plan.archive_branch, "title": f"release-notes: {entry.pypi_name} v{target}"}))

    if not on_main:
        actions.append(CeremonyAction("enable_auto_merge", "enable `gh pr merge --auto --squash` on the archive PR (degrades to the owner one-click merge if allow_auto_merge is off -- step 3.3 not yet landed)", {"branch": plan.archive_branch}))

    actions.append(CeremonyAction("cut_release", f"`gh release create {plan.tag} --latest=false --notes-file {plan.archive_relpath}` -- the Release CREATES the tag (no --verify-tag)", {"tag": plan.tag, "notes_relpath": plan.archive_relpath, "latest": False}))
    actions.append(_monitor_action(plan.tag))
    plan.state = "CEREMONY_PLANNED"
    plan.actions = actions
    return plan


# ── execute (Phase-3 wiring; NEVER run against the real repo in this change) ──


def monitor_publish_run(sources: CeremonySources, repo: str, tag: str, *, timeout_seconds: int = DEFAULT_MONITOR_TIMEOUT_SECONDS, poll_seconds: int = MONITOR_POLL_SECONDS, sleep: "Callable[[float], None]" = time.sleep, monotonic: "Callable[[], float]" = time.monotonic) -> str:
    """Poll the triggered publish run until a terminal ceremony signal or a bounded timeout (plan S8 / §12-3.2).

    Polls ``publish_run_status`` at ``poll_seconds`` for up to ``timeout_seconds`` (a bounded wall clock).
    Returns as soon as ``classify_publish_run`` reaches a terminal signal: ``PENDING_PYPI_APPROVAL`` (the
    run parked at the owner-gated ``pypi`` env -- its GitHub status is ``waiting`` -- which is SUCCESS for
    the train), ``RELEASED``, or a HALT. If the timeout elapses while the run is still building it returns
    ``IN_PROGRESS`` -- now an honest 'still building' rather than a premature give-up; the ceremony is
    idempotent, so a re-run resumes at the monitor. ``monotonic`` is injected for hermetic timeout tests."""
    deadline = monotonic() + max(0, timeout_seconds)
    while True:
        verdict = classify_publish_run(sources.publish_run_status(repo, tag))
        if verdict in ("PENDING_PYPI_APPROVAL", "HALT_TESTPYPI", "HALT_PUBLISH", "RELEASED"):
            return verdict
        if monotonic() >= deadline:
            return "IN_PROGRESS"
        sleep(poll_seconds)


def execute_ceremony(plan: CeremonyPlan, sources: CeremonySources, base_branch: str = "main", *, monitor_kwargs: "dict | None" = None) -> dict:
    """Perform a plan's actions in order via the seam. Opt-in (``--execute``); never the dry-run default.

    Returns a result dict (final state + any PR/Release URLs). A halt files/updates the dedup issue and
    stops. Auto-merge failure degrades to the owner one-click fallback (a note, not a halt)."""
    result: dict = {"pypi_name": plan.pypi_name, "repo": plan.repo, "state": plan.state, "pr_url": None, "release_url": None, "notes": list(plan.notes)}

    if plan.state == "SKIPPED_CROSS_REPO":
        result["skipped_reason"] = plan.skipped_reason
        return result

    pr_ref: "str | None" = None
    for action in plan.actions:
        if action.kind == "halt_issue":
            if sources.upsert_halt_issue is None:
                raise SourceError("execute needs the upsert_halt_issue seam member")
            result["issue_url"] = sources.upsert_halt_issue(plan.repo, plan.issue["title"], plan.issue["body"])
            result["state"] = "HALTED"
            return result
        if action.kind == "open_archive_pr":
            if sources.open_archive_pr is None:
                raise SourceError("execute needs the open_archive_pr seam member")
            pr_ref = sources.open_archive_pr(plan.repo, base_branch, plan.archive_branch, plan.archive_relpath, plan.archive_content, action.detail.get("title") or plan.archive_branch, _archive_pr_body(plan))
            result["pr_url"] = pr_ref
        elif action.kind == "enable_auto_merge":
            if sources.enable_automerge is None:
                raise SourceError("execute needs the enable_automerge seam member")
            enabled = sources.enable_automerge(plan.repo, pr_ref or plan.archive_branch)
            if not enabled:
                result["notes"].append("auto-merge could not be enabled (allow_auto_merge off? -- step 3.3); owner one-click merge fallback (NOT a halt).")
            result["auto_merge_enabled"] = enabled
        elif action.kind == "cut_release":
            if sources.create_release is None:
                raise SourceError("execute needs the create_release seam member")
            result["release_url"] = sources.create_release(plan.repo, plan.tag, f"{plan.pypi_name} v{plan.target_version}", plan.archive_relpath, plan.archive_content)
        elif action.kind == "monitor_publish":
            verdict = monitor_publish_run(sources, plan.repo, plan.tag, **(monitor_kwargs or {}))
            if verdict == "HALT_TESTPYPI":
                if sources.upsert_halt_issue is not None:
                    issue = halt_issue_payload(plan.pypi_name, plan.target_version, "testpypi-verify-failed", "the publish workflow's TestPyPI install-verify step failed before Gate 2 -- the run is not healthy", _today())
                    result["issue_url"] = sources.upsert_halt_issue(plan.repo, issue["title"], issue["body"])
                result["state"] = "HALTED"
                return result
            if verdict == "HALT_PUBLISH":
                result["state"] = "HALTED"
                result["notes"].append("the publish run failed before the pypi gate.")
                return result
            result["state"] = verdict  # PENDING_PYPI_APPROVAL (success) / RELEASED / IN_PROGRESS
    return result


def _archive_pr_body(plan: CeremonyPlan) -> str:
    return (
        f"## Release-notes archive: `{plan.pypi_name}` v{plan.target_version}\n\n"
        f"Auto-generated by the Juniper release-train ceremony (`util/release_train/ceremony.py`).\n\n"
        f"This PR **adds a single file** -- `{plan.archive_relpath}` -- and nothing else. It is the "
        f"gate-exempt notes-archive PR (plan §7 / R5); the `release-train-archive-guard` check proves the "
        f"diff is add-only, path-confined, name-valid, and single-purpose, which is why it may auto-merge "
        f"behind that required check. It deploys nothing: the PyPI deploy is the subsequent Release cut, "
        f"whose publish workflow waits at the owner-gated `pypi` environment (R7).\n"
    )


# ── output ───────────────────────────────────────────────────────────────────


def _print_plan(plan: CeremonyPlan) -> None:
    print("=" * 78)
    if plan.state == "SKIPPED_CROSS_REPO":
        print(f"SKIP  {plan.pypi_name}  ({plan.repo})")
        print(f"      {plan.skipped_reason}")
        print()
        return
    if plan.halted:
        print(f"HALT  {plan.pypi_name}  v{plan.target_version}  ({plan.repo})")
        print(f"      reason: {plan.halt_reason}")
        print(f"      issue:  {plan.issue['title'] if plan.issue else '-'}")
        print()
        return
    header = {"ALREADY_RELEASED": "DONE", "RESUME_MONITOR": "RESUME", "CEREMONY_PLANNED": "CEREMONY"}.get(plan.state, plan.state)
    print(f"{header}  {plan.pypi_name}  {plan.released_version} -> {plan.target_version}  ({plan.repo})")
    if plan.tag:
        print(f"  tag:     {plan.tag}")
    if plan.archive_relpath:
        print(f"  archive: {plan.archive_relpath}")
    for note in plan.notes:
        print(f"  - {note}")
    if plan.actions:
        print("  planned ceremony script (in order):")
        for i, action in enumerate(plan.actions, 1):
            print(f"    {i}. [{action.kind}] {action.summary}")
    else:
        print("  (no actions -- nothing to do)")
    print()


def print_plans(plans: list, dry_run: bool) -> None:
    mode = "DRY-RUN (report-only; writes nothing, opens nothing, cuts nothing)" if dry_run else "EXECUTE"
    print(f"Juniper PyPI release-train -- ceremony [{mode}]")
    print()
    if not plans:
        print("  no BUMPED_NOT_RELEASED packages in the manifest -- nothing to do.")
        return
    for plan in plans:
        _print_plan(plan)
    ceremonies = sum(1 for p in plans if p.state == "CEREMONY_PLANNED")
    resumes = sum(1 for p in plans if p.state == "RESUME_MONITOR")
    halted = sum(1 for p in plans if p.halted)
    skipped = sum(1 for p in plans if p.state == "SKIPPED_CROSS_REPO")
    done = sum(1 for p in plans if p.state == "ALREADY_RELEASED")
    print("=" * 78)
    print(f"  {len(plans)} package(s): {ceremonies} ceremony, {resumes} resume-monitor, {done} already-released, {skipped} skipped, {halted} HALTED.")


def build_output(plans: list, dry_run: bool) -> dict:
    return {
        "schema": "juniper-release-train/ceremony/v1",
        "generated_by": "util/release_train/ceremony.py",
        "dry_run": dry_run,
        "summary": {
            "total": len(plans),
            "ceremony": sum(1 for p in plans if p.state == "CEREMONY_PLANNED"),
            "resume_monitor": sum(1 for p in plans if p.state == "RESUME_MONITOR"),
            "already_released": sum(1 for p in plans if p.state == "ALREADY_RELEASED"),
            "skipped": sum(1 for p in plans if p.state == "SKIPPED_CROSS_REPO"),
            "halted": sum(1 for p in plans if p.halted),
        },
        "plans": [p.to_dict() for p in plans],
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="release_train/ceremony.py", description="Run the exempt-archive + Release ceremony for BUMPED_NOT_RELEASED packages (plan S7/S8/S10). Dry-run by default.")
    default_repo_root = Path(__file__).resolve().parents[2]
    p.add_argument("--manifest", required=True, help="path to the release-manifest JSON emitted by detect.py (--json)")
    p.add_argument("--package", action="append", metavar="PYPI_NAME", help="restrict to these pypi_name(s) (repeatable)")
    p.add_argument("--repo-root", default=str(default_repo_root), help="juniper-ml checkout root (CHANGELOG/notes reads + central notes/releases/)")
    p.add_argument("--ecosystem-root", default=None, help="parent dir holding sibling repos (default: --repo-root's parent)")
    p.add_argument("--owner", default=DEFAULT_OWNER, help=f"GitHub owner (default: {DEFAULT_OWNER})")
    p.add_argument("--registry", default=None, help="path to registry.yaml (default: alongside detect.py)")
    p.add_argument("--release-date", default=None, help="release date for the notes (default: today UTC; use for deterministic output)")
    p.add_argument("--dry-run", action="store_true", help="(default) print the full ceremony script of actions; write nothing, open nothing, cut nothing. Overrides --execute.")
    p.add_argument("--execute", action="store_true", help="opt-in: perform the ceremony (archive PR + auto-merge + Release + monitor). NOT run against the real repo in Phase 3.2; --dry-run overrides it.")
    p.add_argument("--json", action="store_true", help="emit the ceremony plans as JSON instead of the human report")
    p.add_argument("--monitor-timeout", type=int, default=DEFAULT_MONITOR_TIMEOUT_SECONDS, metavar="SECONDS", help=f"max seconds the (--execute) monitor polls the publish run for the pypi-env-gate 'waiting' state before reporting a still-building IN_PROGRESS (default: {DEFAULT_MONITOR_TIMEOUT_SECONDS} = ~15 min)")
    return p.parse_args(argv)


def _plans_for(manifest_pkgs: list, entries: list, wanted: "set | None", sources: CeremonySources, repo_root: Path, ecosystem_root: Path, when: str) -> list:
    by_name = {e.pypi_name: e for e in entries}
    plans: list = []
    for pkg in manifest_pkgs:
        name = pkg.get("pypi_name")
        if pkg.get("classification") != CEREMONIAL:
            continue
        if wanted and name not in wanted:
            continue
        entry = by_name.get(name)
        if entry is None:
            plan = CeremonyPlan(pypi_name=name or "?", repo=pkg.get("repo") or "?", released_version=pkg.get("released_version"), target_version=pkg.get("declared_version"))
            _halt(plan, "not-in-registry", "package is BUMPED_NOT_RELEASED in the manifest but absent from registry.yaml", when)
            plans.append(plan)
            continue
        plans.append(plan_ceremony(entry, pkg, sources, repo_root, ecosystem_root, when))
    return plans


def main(argv: "list[str] | None" = None, sources: "CeremonySources | None" = None) -> int:
    args = parse_args(argv)
    dry_run = args.dry_run or not args.execute  # dry-run is the default and always wins for safety
    repo_root = Path(args.repo_root).resolve()
    ecosystem_root = Path(args.ecosystem_root).resolve() if args.ecosystem_root else repo_root.parent
    when = args.release_date or _today()

    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read manifest {args.manifest}: {exc}", file=sys.stderr)
        return 2
    manifest_pkgs = manifest.get("packages") if isinstance(manifest, dict) else None
    if not isinstance(manifest_pkgs, list):
        print("ERROR: manifest has no 'packages' list (expected detect.py --json output)", file=sys.stderr)
        return 2

    try:
        entries = detect.load_registry(args.registry)
    except Exception as exc:  # noqa: BLE001 - a missing/broken registry is an invocation error
        print(f"ERROR: cannot load registry: {exc}", file=sys.stderr)
        return 2
    if not entries:
        print("ERROR: registry is empty", file=sys.stderr)
        return 2

    wanted = set(args.package) if args.package else None
    if wanted:
        unknown = wanted - {e.pypi_name for e in entries}
        if unknown:
            print(f"ERROR: unknown --package {sorted(unknown)}", file=sys.stderr)
            return 2

    if sources is None:
        sources = make_live_sources(args.owner, repo_root, ecosystem_root)

    try:
        plans = _plans_for(manifest_pkgs, entries, wanted, sources, repo_root, ecosystem_root, when)
    except SourceError as exc:
        print(f"ERROR: source failure during ceremony planning: {exc}", file=sys.stderr)
        return 2

    if not dry_run:
        results = []
        try:
            for plan in plans:
                results.append(execute_ceremony(plan, sources, monitor_kwargs={"timeout_seconds": args.monitor_timeout}))
        except SourceError as exc:
            print(f"ERROR: execute failed: {exc}", file=sys.stderr)
            return 2
        for r in results:
            print(f"{r['state']:<22} {r['pypi_name']:<28} pr={r.get('pr_url') or '-'} release={r.get('release_url') or '-'}")
        return 1 if any(r["state"] == "HALTED" for r in results) else 0

    if args.json:
        print(json.dumps(build_output(plans, dry_run), indent=2))
    else:
        print_plans(plans, dry_run)
    return 1 if any(p.halted for p in plans) else 0


if __name__ == "__main__":
    sys.exit(main())
