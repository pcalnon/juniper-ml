#!/usr/bin/env python3
"""Juniper PyPI release-train proposal-PR generator (plan S5.4/S6/S10.1; Phase 2.1 engine, wired in 2.2).

Consumes the release-manifest JSON emitted by ``detect.py`` (Phase 1.2) and, for every
package the detector classified ``UNRELEASED_CHANGES``, builds the **complete content** of a
single **standard-gated release-proposal PR** (plan S5.4):

  * the version bump edit -- ``[project].version`` for a static package, ``_version.py``
    ``__version__`` for a dynamic one (model-core + the 3 recurrence packages, audit S2);
  * the CHANGELOG ``[Unreleased]`` -> ``[<version>] - <date>`` move, leaving a fresh empty
    ``[Unreleased]`` behind (Keep-a-Changelog, plan S5.4);
  * a drafted release-notes body from ``notes_render.py`` (the template, plan S10.1) -- shown
    in the PR body, **not** archived to ``notes/releases/`` (archival is the later exempt step);
  * the meta-package's ``AGENTS.md`` ``**Version**`` co-change (plan S5.4; kept in lockstep by
    ``tests/test_agents_md_version_drift.py``) and the S5.4 co-change checklist (lockfile regen,
    version+pin+lint atomicity);
  * the ``propagation_edges`` -- a pre-1.0 MINOR bump escapes a consumer's ``<next-minor``
    ceiling pin (plan S6/S13), so each reverse-dependency consumer gets a listed follow-on
    ceiling-bump PR (standard-gated, **never** folded into the exempt path -- the 2026-07-06
    ci-tools incident class);
  * the branch name, commit message, and PR title/body.

The proposal PR is **dup-guarded**: before proposing, the train runs ``gh pr list`` for an
existing open release PR for the package (concurrent Claude sessions are a real hazard) and
refuses to duplicate it. A ``changelog_conflict`` flagged by the detector is a **refusal**:
the train will not auto-author notes / move a CHANGELOG the detector found inconsistent.

``--dry-run`` is the DEFAULT: it prints the complete, well-formed proposal (unified diffs +
drafted notes + PR body) and **writes nothing** to the repo and opens nothing. ``--execute``
(opt-in, and overridden by ``--dry-run`` for safety) applies the edits, commits, pushes, and opens
the PR -- wired into ``release-train.yml``'s write-scoped ``propose`` job (Phase 2.2). Under
``--execute`` a package whose registry ``repo`` is not juniper-ml is SKIPPED with a clear reason:
the workflow's single-repo ``GITHUB_TOKEN`` can only open PRs in juniper-ml (cross-repo is Phase 4).

Every external effect -- ``gh pr list`` (dup-guard), file reads, and (execute-only) file
writes / git / ``gh pr create`` -- is injected through a ``ProposeSources`` seam so
``tests/test_release_train_propose.py`` is fully hermetic (no network, no real gh, no real
pip). ``util/`` is not pre-commit-lint-gated, so that unittest IS the gate (the
``env_floor_drift_check`` precedent, shared with ``detect.py``).

Exit codes: 0 clean run (dry-run preview or execute completed); 2 invocation error (bad
manifest / empty registry / unknown ``--package``). A dry-run is always report-only.

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-14
Status: permanent utility (Phase 2, proposal-PR generation)
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess  # nosec B404 - only the gh/git binaries with fixed argv (no shell)
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

# Same-directory siblings; resolvable both when run as a script (script dir on sys.path[0])
# and under the tests' ``sys.path.insert(UTIL_DIR)`` idiom (mirrors test_release_train_detect).
import detect  # noqa: E402
import notes_render  # noqa: E402

SourceError = detect.SourceError  # reuse the detector's environmental-failure type

DEFAULT_OWNER = os.environ.get("JUNIPER_RELEASE_TRAIN_OWNER", "pcalnon")

# Only this classification gets a standard-gated proposal PR (plan S5.4 / S5.1).
PROPOSABLE = "UNRELEASED_CHANGES"

# Keep-a-Changelog categories that make a pre-1.0 bump MINOR (escapes the consumer ceiling).
_MINOR_BUMPS = frozenset({"minor", "major"})

# The single repo whose contents an ``--execute`` run may write. The Phase-2/3 pilot runs the
# release-train workflow inside the juniper-ml checkout under a juniper-ml-scoped ``GITHUB_TOKEN``
# (plan S9.2), which can push a branch + open a PR only in juniper-ml -- the meta-package and its
# six co-located sub-packages. Sibling-repo packages (cascor*, canopy, data*, recurrence*) are
# SKIPPED in ``--execute`` with a clear reason rather than attempted: their edits would otherwise
# land in the juniper-ml checkout (``make_live_sources.write_file`` targets ``repo_root``) and the
# cross-repo ``gh pr create`` would fail. Phase 4's GitHub App identity lifts this (plan S9.2/S9.3,
# S12 step 4.1). ``--dry-run`` is unaffected -- it previews every repo's proposal and writes nothing.
# Overridable for tests / a future multi-repo identity.
WRITABLE_REPO = os.environ.get("JUNIPER_RELEASE_TRAIN_WRITABLE_REPO", detect.META_REPO)


# ── data model ───────────────────────────────────────────────────────────────


@dataclass
class FileEdit:
    """One file's before/after content in the proposal (rendered as a unified diff)."""

    path: str
    old_text: str
    new_text: str
    is_new: bool = False

    def unified_diff(self) -> str:
        from_lines = self.old_text.splitlines(keepends=True)
        to_lines = self.new_text.splitlines(keepends=True)
        label = "(new file)" if self.is_new else ""
        diff = difflib.unified_diff(from_lines, to_lines, fromfile=f"a/{self.path}", tofile=f"b/{self.path} {label}".rstrip())
        return "".join(diff)


@dataclass
class Proposal:
    """The full content of one release-proposal PR (or a skipped/refused stub)."""

    pypi_name: str
    repo: str
    from_version: "str | None"
    to_version: "str | None"
    bump: str
    branch: "str | None" = None
    commit_message: "str | None" = None
    pr_title: "str | None" = None
    pr_body: "str | None" = None
    edits: list = field(default_factory=list)
    notes_relpath: "str | None" = None
    notes_draft: "str | None" = None
    propagation_edges: list = field(default_factory=list)
    co_change_checklist: list = field(default_factory=list)
    ship_evidence: list = field(default_factory=list)
    existing_pr: "dict | None" = None
    skipped_reason: "str | None" = None

    @property
    def skipped(self) -> bool:
        return self.skipped_reason is not None

    def to_dict(self) -> dict:
        return {
            "pypi_name": self.pypi_name,
            "repo": self.repo,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "bump": self.bump,
            "branch": self.branch,
            "commit_message": self.commit_message,
            "pr_title": self.pr_title,
            "pr_body": self.pr_body,
            "edits": [{"path": e.path, "is_new": e.is_new, "diff": e.unified_diff()} for e in self.edits],
            "notes_relpath": self.notes_relpath,
            "notes_draft": self.notes_draft,
            "propagation_edges": self.propagation_edges,
            "co_change_checklist": self.co_change_checklist,
            "ship_evidence": self.ship_evidence,
            "existing_pr": self.existing_pr,
            "skipped_reason": self.skipped_reason,
        }


# ── injectable I/O seam (all external effects) ───────────────────────────────


@dataclass
class ProposeSources:
    """External effects the generator needs, injected for hermetic testing.

    ``read_file`` / ``list_open_prs`` are the only members the dry-run path (Phase 2.1) uses;
    ``write_file`` / ``run_git`` / ``open_pr`` are execute-only (Phase 2.2) and may be ``None``."""

    read_file: Callable[["detect.PackageEntry", str], "str | None"]
    list_open_prs: Callable[[str], list]
    write_file: "Callable[[str, str], None] | None" = None
    run_git: "Callable[[list], None] | None" = None
    open_pr: "Callable[..., str] | None" = None


def _gh(args: list, timeout: int = 60) -> "str | None":
    """Run ``gh <args>`` with a fixed argv (no shell). None on a 404-ish 'no result'."""
    try:
        proc = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603,B607 - fixed argv, no shell
    except FileNotFoundError as exc:
        raise SourceError("gh CLI not found (install/authenticate GitHub CLI)") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"gh timed out: {' '.join(args)}") from exc
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if "no pull requests" in stderr.lower() or "not found" in stderr.lower():
            return None
        raise SourceError(f"gh failed ({' '.join(args)}): {stderr[:200]}")
    return proc.stdout


def _git(repo_dir: Path, args: list, timeout: int = 120) -> None:
    try:
        proc = subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603,B607 - fixed argv
    except FileNotFoundError as exc:
        raise SourceError("git not found (needed for --execute)") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"git timed out: {' '.join(args)}") from exc
    if proc.returncode != 0:
        raise SourceError(f"git failed ({' '.join(args)}): {(proc.stderr or '').strip()[:200]}")


def make_live_sources(owner: str, repo_root: Path, ecosystem_root: Path) -> ProposeSources:
    def read_file(entry: "detect.PackageEntry", filename: str) -> "str | None":
        target = detect.base_dir_for(entry, repo_root, ecosystem_root) / filename
        try:
            return target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def list_open_prs(repo: str) -> list:
        out = _gh(["pr", "list", "--repo", f"{owner}/{repo}", "--state", "open", "--json", "number,title,headRefName", "--limit", "100"])
        if not out:
            return []
        try:
            return json.loads(out) or []
        except ValueError as exc:
            raise SourceError(f"gh pr list returned non-JSON for {repo}") from exc

    def write_file(rel_path: str, content: str) -> None:
        target = repo_root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def run_git(args: list) -> None:
        _git(repo_root, args)

    def open_pr(repo: str, base: str, head: str, title: str, body: str) -> str:
        out = _gh(["pr", "create", "--repo", f"{owner}/{repo}", "--base", base, "--head", head, "--title", title, "--body", body])
        return (out or "").strip()

    return ProposeSources(read_file=read_file, list_open_prs=list_open_prs, write_file=write_file, run_git=run_git, open_pr=open_pr)


# ── version-file editing (static pyproject / dynamic _version.py / AGENTS.md) ─


def version_file_rel(entry: "detect.PackageEntry") -> str:
    """Repo-relative path of the file carrying the version to bump."""
    if entry.version_source == "dynamic":
        return os.path.normpath(os.path.join(entry.path, entry.import_package, "_version.py")).replace(os.sep, "/")
    return entry.pyproject_rel


def set_pyproject_version(text: str, new_version: str) -> tuple:
    """Replace the ``version = "..."`` line inside the ``[project]`` table. -> (new_text, old|None)."""
    lines = text.splitlines(keepends=True)
    section = None
    for i, line in enumerate(lines):
        hm = re.match(r"^\[([^\]]+)\]\s*$", line.strip())
        if hm:
            section = hm.group(1)
            continue
        if section == "project":
            m = re.match(r'^(\s*version\s*=\s*["\'])([^"\']+)(["\'].*)$', line.rstrip("\n"))
            if m:
                old = m.group(2)
                rebuilt = f"{m.group(1)}{new_version}{m.group(3)}" + ("\n" if line.endswith("\n") else "")
                lines[i] = rebuilt
                return "".join(lines), old
    return text, None


def set_dynamic_version(text: str, new_version: str) -> tuple:
    """Replace ``__version__ = "..."`` (first occurrence). -> (new_text, old|None)."""
    m = re.search(r'^(\s*__version__\s*=\s*["\'])([^"\']+)(["\'])', text, re.MULTILINE)
    if not m:
        return text, None
    old = m.group(2)
    new_text = text[: m.start()] + f"{m.group(1)}{new_version}{m.group(3)}" + text[m.end():]
    return new_text, old


def set_agents_version(text: str, new_version: str) -> tuple:
    """Replace the ``**Version**:`` header value in AGENTS.md. -> (new_text, old|None)."""
    m = re.search(r"^(\*\*Version\*\*:\s*)(\S+)(.*)$", text, re.MULTILINE)
    if not m:
        return text, None
    old = m.group(2)
    new_text = text[: m.start()] + f"{m.group(1)}{new_version}{m.group(3)}" + text[m.end():]
    return new_text, old


# ── CHANGELOG [Unreleased] -> [version] move ─────────────────────────────────


def _strip_blank_edges(lines: list) -> list:
    out = list(lines)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def move_unreleased(changelog_text: str, version: str, date: str) -> tuple:
    """Move ``[Unreleased]`` bullets into a new ``[<version>] - <date>`` section, leaving a
    fresh empty ``[Unreleased]`` (Keep-a-Changelog, plan S5.4). -> (new_text, reason|None);
    a non-None reason means REFUSE (no move): no Unreleased heading, or an empty section."""
    if not changelog_text:
        return None, "CHANGELOG is empty or unreadable"
    lines = changelog_text.splitlines()
    unrel = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s*\[?unreleased\]?", line.strip(), re.IGNORECASE):
            unrel = i
            break
    if unrel is None:
        return None, "no '## [Unreleased]' heading in CHANGELOG"
    end = len(lines)
    for j in range(unrel + 1, len(lines)):
        if re.match(r"^##\s", lines[j]) and not re.match(r"^###", lines[j]):
            end = j
            break
    body = _strip_blank_edges(lines[unrel + 1:end])
    if not body:
        return None, "[Unreleased] section has no content to move"
    rebuilt: list = []
    rebuilt.extend(lines[: unrel + 1])  # up to and including '## [Unreleased]'
    rebuilt.append("")  # fresh empty Unreleased
    rebuilt.append(f"## [{version}] - {date}")
    rebuilt.append("")
    rebuilt.extend(body)
    if end < len(lines):
        rebuilt.append("")
        rebuilt.extend(lines[end:])
    new_text = "\n".join(rebuilt)
    if changelog_text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, None


# ── dup-guard + propagation ──────────────────────────────────────────────────


def release_branch(pypi_name: str, version: str) -> str:
    return f"release/{pypi_name}-v{version}"


def find_existing_release_pr(open_prs: list, pypi_name: str) -> "dict | None":
    """An open PR whose head branch is this package's release branch (any version) -> dup.

    The ``-v`` delimiter keeps ``juniper-cascor`` from matching ``juniper-cascor-model``."""
    prefix = f"release/{pypi_name}-v"
    for pr in open_prs or []:
        head = (pr or {}).get("headRefName", "")
        if head.startswith(prefix):
            return pr
    return None


def reverse_dependents(entries: list, pypi_name: str) -> list:
    """Registered packages that declare ``pypi_name`` in their ``depends_on`` (consumers)."""
    return sorted(e.pypi_name for e in entries if pypi_name in (e.depends_on or []))


def propagation_edges(entries: list, entry: "detect.PackageEntry", bump: str) -> list:
    """For a pre-1.0 MINOR (or MAJOR) bump, each consumer needs a ceiling-bump follow-on PR
    (plan S6/S13). PATCH stays within ``<next-minor`` ceilings -> no propagation."""
    if bump not in _MINOR_BUMPS:
        return []
    by_name = {e.pypi_name: e for e in entries}
    edges: list = []
    for consumer in reverse_dependents(entries, entry.pypi_name):
        cons_entry = by_name.get(consumer)
        edges.append(
            {
                "consumer": consumer,
                "repo": cons_entry.repo if cons_entry else None,
                "reason": f"pre-1.0 {bump.upper()} bump of {entry.pypi_name} escapes its '<next-minor' ceiling pin",
                "action": "standard-gated ceiling-bump follow-on PR (D6); never folded into this PR or the exempt path",
            }
        )
    return edges


# ── proposal construction ────────────────────────────────────────────────────


def _changelog_rel(entry: "detect.PackageEntry") -> str:
    return os.path.normpath(os.path.join(entry.path, "CHANGELOG.md")).replace(os.sep, "/")


def _co_change_checklist(entry: "detect.PackageEntry", bump: str, edges: list, agents_edited: bool) -> list:
    items: list = []
    if entry.pypi_name == notes_render.META_PACKAGE:
        state = "included in this PR" if agents_edited else "REQUIRED (edit could not be computed -- do it manually)"
        items.append(f"AGENTS.md **Version** header bump ({state}); guarded by tests/test_agents_md_version_drift.py.")
    items.append("If this bump raises a runtime dependency floor, regenerate the lockfile (requirements.lock) in this PR (memory: 'regen on floor bump or gate fails').")
    items.append("Version+pin+lint atomicity: if a consumer pins this package behind a drift-lint contract (tests/test_*_drift.py), move the pin + the lint bound in the same change set (model-core precedent).")
    if edges:
        items.append(f"Consumer ceiling propagation: {len(edges)} follow-on ceiling-bump PR(s) needed (see propagation edges) -- standard-gated, opened separately, NEVER folded into this PR or the exempt notes-archive path (2026-07-06 ci-tools incident class).")
    return items


def _pr_body(prop: Proposal, date: str) -> str:
    lines: list = []
    lines.append(f"## Release proposal: `{prop.pypi_name}` v{prop.from_version} -> v{prop.to_version}")
    lines.append("")
    lines.append("Generated by the Juniper release-train (`util/release_train/propose.py`) from the release manifest.")
    lines.append(f"Classification `UNRELEASED_CHANGES`; proposed bump **{prop.bump}** (plan S6). This PR is **standard-gated**: the owner reviews and merges it (plan S7). It is never auto-merged and touches neither TestPyPI nor PyPI.")
    lines.append("")
    lines.append("### Version bump")
    lines.append(f"- `{version_change_summary(prop)}` (via `{version_file_rel_for(prop)}`)")
    lines.append("")
    lines.append("### CHANGELOG")
    lines.append(f"- Move `[Unreleased]` -> `[{prop.to_version}] - {date}`, leaving a fresh empty `[Unreleased]` (Keep-a-Changelog).")
    lines.append("")
    lines.append("### Drafted release notes (NOT archived here)")
    lines.append(f"Archival to the central `{prop.notes_relpath}` is the later **exempt** ceremony step (plan S10.2); this PR only drafts the notes for review.")
    lines.append("")
    lines.append("<details><summary>Drafted release notes</summary>")
    lines.append("")
    lines.append("```markdown")
    lines.append((prop.notes_draft or "").rstrip("\n"))
    lines.append("```")
    lines.append("")
    lines.append("</details>")
    lines.append("")
    if prop.ship_evidence:
        lines.append("### Ship evidence (from the detector)")
        for item in prop.ship_evidence:
            lines.append(f"- `{item.get('file', '?')}` -- {item.get('reason', '')}")
        lines.append("")
    lines.append("### Propagation edges (D6)")
    if prop.propagation_edges:
        for edge in prop.propagation_edges:
            lines.append(f"- `{edge['consumer']}` ({edge.get('repo')}): {edge['action']}")
    else:
        lines.append("- None -- PATCH within consumer `<next-minor` ceilings (no propagation).")
    lines.append("")
    lines.append("### Co-change checklist (plan S5.4)")
    for item in prop.co_change_checklist:
        lines.append(f"- [ ] {item}")
    lines.append("")
    lines.append("### Files changed in this proposal")
    for edit in prop.edits:
        lines.append(f"- `{edit.path}`{' (new file)' if edit.is_new else ''}")
    lines.append("")
    return "\n".join(lines)


def version_change_summary(prop: Proposal) -> str:
    return f"{prop.pypi_name}: {prop.from_version} -> {prop.to_version}"


def version_file_rel_for(prop: Proposal) -> str:
    """The version file path from the proposal's first edit (always the version bump)."""
    return prop.edits[0].path if prop.edits else "(version file)"


def build_proposal(entry: "detect.PackageEntry", pkg: dict, sources: ProposeSources, repo_root: Path, ecosystem_root: Path, entries: list, date: str) -> Proposal:
    """Build the full proposal for one UNRELEASED_CHANGES manifest package (or a refusal stub)."""
    from_version = pkg.get("released_version") or pkg.get("declared_version")
    bump = pkg.get("proposed_bump") or "none"
    to_version = pkg.get("proposed_version") or detect.bump_version(from_version or "0.0.0", bump)
    prop = Proposal(pypi_name=entry.pypi_name, repo=entry.repo, from_version=from_version, to_version=to_version, bump=bump, ship_evidence=list(pkg.get("ship_evidence") or []))

    # 1. dup-guard (cheapest; concurrent-session hazard, plan S8/S5.4).
    existing = find_existing_release_pr(sources.list_open_prs(entry.repo), entry.pypi_name)
    if existing is not None:
        prop.existing_pr = existing
        prop.skipped_reason = f"dup-guard: open release PR already exists (#{existing.get('number')} {existing.get('headRefName')})"
        return prop

    # 2. changelog-conflict refusal (the detector flagged an inconsistency, plan S4.2 step 6).
    conflict = pkg.get("changelog_conflict")
    if conflict:
        prop.skipped_reason = f"changelog conflict -- refuse to auto-author: {conflict}"
        return prop

    if not to_version or bump == "none":
        prop.skipped_reason = f"no proposable version (bump={bump}, proposed_version={pkg.get('proposed_version')!r})"
        return prop

    # 3. version bump edit.
    vfile = version_file_rel(entry)
    vtext = sources.read_file(entry, vfile)
    if vtext is None:
        prop.skipped_reason = f"could not read the version file {vfile}"
        return prop
    if entry.version_source == "dynamic":
        new_vtext, old = set_dynamic_version(vtext, to_version)
    else:
        new_vtext, old = set_pyproject_version(vtext, to_version)
    if old is None:
        prop.skipped_reason = f"could not locate the version assignment in {vfile}"
        return prop
    prop.edits.append(FileEdit(path=vfile, old_text=vtext, new_text=new_vtext))

    # 4. CHANGELOG move (+ source the notes bullets from the same text).
    clog_rel = _changelog_rel(entry)
    clog_text = sources.read_file(entry, clog_rel)
    sections = notes_render.parse_unreleased(clog_text or "")
    if clog_text is not None:
        moved, reason = move_unreleased(clog_text, to_version, date)
        if reason is not None:
            prop.skipped_reason = f"CHANGELOG move refused: {reason}"
            return prop
        prop.edits.append(FileEdit(path=clog_rel, old_text=clog_text, new_text=moved))
    else:
        prop.skipped_reason = f"could not read {clog_rel}"
        return prop

    # 5. meta-package AGENTS.md **Version** co-change (plan S5.4).
    agents_edited = False
    if entry.pypi_name == notes_render.META_PACKAGE:
        atext = sources.read_file(entry, "AGENTS.md")
        if atext is not None:
            new_atext, aold = set_agents_version(atext, to_version)
            if aold is not None and new_atext != atext:
                prop.edits.append(FileEdit(path="AGENTS.md", old_text=atext, new_text=new_atext))
                agents_edited = True

    # 6. drafted release notes (template-driven; NOT archived here, plan S10.1/S10.2).
    prop.notes_relpath = notes_render.archive_relpath(entry.pypi_name, to_version)
    prop.notes_draft = notes_render.render_notes(entry.pypi_name, to_version, bump=bump, release_date=date, sections=sections, repo_root=repo_root)

    # 7. propagation edges + co-change checklist.
    prop.propagation_edges = propagation_edges(entries, entry, bump)
    prop.co_change_checklist = _co_change_checklist(entry, bump, prop.propagation_edges, agents_edited)

    # 8. branch / commit / PR metadata.
    prop.branch = release_branch(entry.pypi_name, to_version)
    prop.commit_message = f"chore(release): {entry.pypi_name} v{to_version} -- version bump + CHANGELOG move"
    prop.pr_title = f"release: {entry.pypi_name} v{to_version} (proposal)"
    prop.pr_body = _pr_body(prop, date)
    return prop


# ── output ───────────────────────────────────────────────────────────────────


def _print_proposal(prop: Proposal) -> None:
    print("=" * 78)
    if prop.skipped:
        print(f"SKIP  {prop.pypi_name}  ({prop.repo})")
        print(f"      reason: {prop.skipped_reason}")
        print()
        return
    print(f"PROPOSE  {prop.pypi_name}  {prop.from_version} -> {prop.to_version}  [{prop.bump}]  ({prop.repo})")
    print()
    print(f"  branch:  {prop.branch}")
    print(f"  commit:  {prop.commit_message}")
    print(f"  PR title: {prop.pr_title}")
    print()
    for edit in prop.edits:
        print(f"  --- file edit: {edit.path}{' (new file)' if edit.is_new else ''} ---")
        diff = edit.unified_diff()
        for line in diff.splitlines():
            print(f"  {line}")
        print()
    print("  --- drafted release notes (NOT archived; eventual home:", prop.notes_relpath, ") ---")
    for line in (prop.notes_draft or "").splitlines():
        print(f"  {line}")
    print()
    if prop.propagation_edges:
        print("  --- propagation edges (D6, separate standard-gated PRs) ---")
        for edge in prop.propagation_edges:
            print(f"  - {edge['consumer']} ({edge.get('repo')}): {edge['action']}")
        print()
    print("  --- PR body ---")
    for line in (prop.pr_body or "").splitlines():
        print(f"  {line}")
    print()


def print_proposals(proposals: list, dry_run: bool) -> None:
    mode = "DRY-RUN (report-only; writes nothing, opens nothing)" if dry_run else "EXECUTE"
    print(f"Juniper PyPI release-train -- proposal generation [{mode}]")
    print()
    if not proposals:
        print("  no UNRELEASED_CHANGES packages in the manifest -- nothing to propose.")
        return
    for prop in proposals:
        _print_proposal(prop)
    proposed = sum(1 for p in proposals if not p.skipped)
    skipped = sum(1 for p in proposals if p.skipped)
    print("=" * 78)
    print(f"  {len(proposals)} package(s): {proposed} proposal(s), {skipped} skipped/refused.")


def build_output(proposals: list, dry_run: bool) -> dict:
    return {
        "schema": "juniper-release-train/proposals/v1",
        "generated_by": "util/release_train/propose.py",
        "dry_run": dry_run,
        "summary": {"total": len(proposals), "proposed": sum(1 for p in proposals if not p.skipped), "skipped": sum(1 for p in proposals if p.skipped)},
        "proposals": [p.to_dict() for p in proposals],
    }


# ── execute path (Phase 2.2; wired into release-train.yml's write-scoped propose job) ─


def cross_repo_skip_reason(repo: str, writable_repo: str = WRITABLE_REPO) -> "str | None":
    """Reason to skip a proposal under ``--execute`` because its package is outside the writable repo.

    ``None`` when ``repo`` is the writable repo (``--execute`` may open a PR there); otherwise a
    clear, human-readable reason. The release-train workflow's single-repo ``GITHUB_TOKEN`` can push
    a branch + open a PR only in ``writable_repo`` (juniper-ml), so a sibling-repo package is skipped,
    not attempted -- executing it would write the edits into the juniper-ml checkout and the cross-repo
    ``gh pr create`` would fail (plan S9.2/S9.3, S12 step 2.2; Phase 4's App identity lifts it)."""
    if repo == writable_repo:
        return None
    return f"cross-repo: package lives in '{repo}', not the writable repo '{writable_repo}' -- the release-train workflow's single-repo GITHUB_TOKEN cannot open a PR there (Phase 2/3 in-repo pilot; Phase 4's GitHub App identity lifts this, plan S9.2 / S12 step 4.1)"


def execute_proposal(prop: Proposal, sources: ProposeSources, base_branch: str) -> str:
    """Apply one proposal to the repo and open the PR. Requires the write/git/pr seam members.

    Guarded so it can only run under an explicit ``--execute`` (never the default), and only for a
    package in the writable repo (cross-repo is skipped upstream in ``main`` and here)."""
    if sources.write_file is None or sources.run_git is None or sources.open_pr is None:
        raise SourceError("execute mode needs write_file/run_git/open_pr seam members")
    if prop.skipped or not prop.branch:
        return ""
    # Cross-repo guard (belt-and-suspenders -- main() already skips these before calling): never
    # write a sibling-repo package's edits into the juniper-ml checkout / open a doomed cross-repo
    # PR under the single-repo GITHUB_TOKEN (plan S9.2 / S12 step 2.2).
    if cross_repo_skip_reason(prop.repo) is not None:
        return ""
    sources.run_git(["switch", "-c", prop.branch, base_branch])
    for edit in prop.edits:
        sources.write_file(edit.path, edit.new_text)
        sources.run_git(["add", "--", edit.path])
    # ``-c commit.gpgsign=false``: the CI runner has no GPG key, and the owner's YubiKey-resident
    # signing config must never reach a headless commit (it would fail). The workflow's git-config
    # step also sets this; pinning it on the commit itself makes the job immune regardless of config.
    sources.run_git(["-c", "commit.gpgsign=false", "commit", "-m", prop.commit_message or f"release: {prop.pypi_name}"])
    sources.run_git(["push", "--set-upstream", "origin", prop.branch])
    return sources.open_pr(prop.repo, base_branch, prop.branch, prop.pr_title or "", prop.pr_body or "")


# ── CLI ──────────────────────────────────────────────────────────────────────


def parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="release_train/propose.py", description="Generate standard-gated release-proposal PR content from the release manifest (plan S5.4). Dry-run by default.")
    default_repo_root = Path(__file__).resolve().parents[2]
    p.add_argument("--manifest", required=True, help="path to the release-manifest JSON emitted by detect.py (--json)")
    p.add_argument("--package", action="append", metavar="PYPI_NAME", help="restrict to these pypi_name(s) (repeatable)")
    p.add_argument("--repo-root", default=str(default_repo_root), help="juniper-ml checkout root (version-file reads + notes template)")
    p.add_argument("--ecosystem-root", default=None, help="parent dir holding sibling repos (default: --repo-root's parent)")
    p.add_argument("--owner", default=DEFAULT_OWNER, help=f"GitHub owner for the dup-guard (default: {DEFAULT_OWNER})")
    p.add_argument("--registry", default=None, help="path to registry.yaml (default: alongside detect.py)")
    p.add_argument("--release-date", default=None, help="release date for the CHANGELOG/notes (default: today UTC; use for deterministic output)")
    p.add_argument("--dry-run", action="store_true", help="(default behaviour) print the proposal; write nothing, open nothing. Overrides --execute.")
    p.add_argument("--execute", action="store_true", help="Phase 2.2 opt-in: apply edits + open PRs. NOT used in Phase 2.1; --dry-run overrides it.")
    p.add_argument("--json", action="store_true", help="emit the proposals as JSON instead of the human report")
    return p.parse_args(argv)


def main(argv: "list[str] | None" = None, sources: "ProposeSources | None" = None) -> int:
    args = parse_args(argv)
    dry_run = args.dry_run or not args.execute  # dry-run is the default and always wins for safety
    repo_root = Path(args.repo_root).resolve()
    ecosystem_root = Path(args.ecosystem_root).resolve() if args.ecosystem_root else repo_root.parent
    date = args.release_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

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
    by_name = {e.pypi_name: e for e in entries}

    wanted = set(args.package) if args.package else None
    if wanted:
        unknown = wanted - set(by_name)
        if unknown:
            print(f"ERROR: unknown --package {sorted(unknown)}", file=sys.stderr)
            return 2

    if sources is None:
        sources = make_live_sources(args.owner, repo_root, ecosystem_root)

    proposals: list = []
    try:
        for pkg in manifest_pkgs:
            name = pkg.get("pypi_name")
            if pkg.get("classification") != PROPOSABLE:
                continue
            if wanted and name not in wanted:
                continue
            entry = by_name.get(name)
            if entry is None:
                proposals.append(Proposal(pypi_name=name or "?", repo=pkg.get("repo") or "?", from_version=pkg.get("released_version"), to_version=None, bump=pkg.get("proposed_bump") or "none", skipped_reason="package not in registry.yaml"))
                continue
            proposals.append(build_proposal(entry, pkg, sources, repo_root, ecosystem_root, entries, date))
    except SourceError as exc:
        print(f"ERROR: source failure during proposal generation: {exc}", file=sys.stderr)
        return 2

    if not dry_run:
        opened: list = []
        skipped: list = []
        try:
            for prop in proposals:
                # Cross-repo takes precedence over any build-time skip so the reported reason is the
                # authoritative one (a sibling-repo package can also fail its file reads when the
                # siblings are not checked out; the cross-repo reason is the real cause).
                reason = cross_repo_skip_reason(prop.repo)
                if reason is not None:
                    skipped.append(prop)
                    print(f"skip: {prop.pypi_name} ({prop.repo}) -- {reason}")
                    continue
                if prop.skipped:
                    skipped.append(prop)
                    print(f"skip: {prop.pypi_name} ({prop.repo}) -- {prop.skipped_reason}")
                    continue
                url = execute_proposal(prop, sources, "main")
                if url:
                    opened.append(prop)
                    print(f"opened: {prop.pypi_name} ({prop.repo}) -- {url}")
                else:
                    skipped.append(prop)
                    print(f"skip: {prop.pypi_name} ({prop.repo}) -- execute opened no PR (empty URL)")
        except SourceError as exc:
            print(f"ERROR: execute failed: {exc}", file=sys.stderr)
            return 2
        print(f"execute summary: {len(opened)} PR(s) opened, {len(skipped)} skipped.")
        return 0

    if args.json:
        print(json.dumps(build_output(proposals, dry_run), indent=2))
    else:
        print_proposals(proposals, dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
