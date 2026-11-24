#!/usr/bin/env python3
"""
List the CHANGELOG entries that are filed under the wrong version or category at a commit, and the commit that put
each one there.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups, item R50)
Author: Paul Calnon
Created: 2026-11-24
Version: 0.4.0
License: MIT License
Status: ad-hoc — investigation (the second CHANGELOG check a release cut needs)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-09-23_released_section_drift.py (the predecessor, kept as provenance);
         notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md (item R50);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md
         (":298": "a read of the category headings against the parent of any long-lived PR's merge")

Why
---
juniper-ml#2360 was open from 2026-10-26 to 2026-11-12, and 0.11.4 was cut in between. Its squash merge, ``187e3258``,
misfiled ``CHANGELOG.md`` entries in two ways, and ml#2558 (``48b66130``, the 0.11.5 cut) repaired both:

- it added a bullet (the orphan reaper's ``TMPDIR`` fix) under the RELEASED ``## [0.11.4]``;
- it inserted its own ``### Changed`` heading near the top of ``[Unreleased]``'s ``### Added``, so the five Added
  bullets below it, which other PRs had written, read as Changed.

The predecessor compares a released section with its archived release notes. It sees the first kind and cannot see
the second, and neither can any check of one snapshot: a category heading looks the same whether the bullets under it
belong there or not, and a repeated heading is an ordinary merge result, not a defect
(``ceremony.changelog_version_section``'s docstring). The PR head is no reference either: #2360's head had ``main``
merged in. The reference is the history: where each bullet was filed, and which release first shipped the commit
that added it.

What it does
------------
1. Lists the first-parent commits that changed PATH: with ``--since A``, every one in ``A..AT``; with ``--merge M``,
   M and then the ones in ``M..AT``, where only the bullets M added or moved are judged.
2. Parses PATH at each commit and at its first parent with the release train's own rules
   (``notes_render.heading_key`` for a category heading, ``notes_render._split_bullets`` for a bullet). A bullet under
   no category heading is kept as "(no category)", and one above the first version heading as "(no version)": the
   release train drops both. A repeated version heading (a second ``## [Unreleased]``) is a version of its own,
   ``Unreleased#2``: the train reads only the first. A bullet's text ends where Markdown ends the list item (a blank
   line, then an unindented line) and holds no link-reference definition, so a link footer or a closing comment,
   which the train's split folds into the oldest bullet, is not part of it.
3. Follows every bullet through the walk: equal text at the same place first, then equal text anywhere, then the most
   similar removed bullet at a ``difflib`` ratio of 0.75 or more (an edit). Text appended to a bullet of three words
   or more is an edit of it whatever the ratio. For bullets of eight words or more, a word overlap below 0.5 rules a
   pair out before ``difflib`` runs.
4. Judges each followed bullet at AT:

   - ``WRONG VERSION``: not under the version it belongs to. A bullet that was already under a version at the start of
     the walk, or was first written above every version heading (a preamble list), belongs there. Any other bullet
     belongs to the first FINAL release whose tag contains the commit that added it: under that version once the tag
     is in AT's history, and before that under ``[Unreleased]`` or that version's own heading. It may also sit under a
     released pre-release that shipped it, since a pre-release's notes are a preview. A bullet no final release
     contains yet belongs under ``[Unreleased]``, such a pre-release, or a version heading not yet released that looks
     like a version. This covers a bullet added under a released version, one a cut left behind in ``[Unreleased]``
     (blamed on the release's tagged commit, unless a later commit moved it back, which is then blamed), and one moved
     between versions.
   - ``RECATEGORIZED``: not under the category heading it was filed under, ``(no category)`` included. Case alone is
     not a change.
   - ``TEXT ADDED UNDER RELEASED``: four or more words one commit inserted into a bullet whose version was already
     released, still there at AT. Words are aligned with ``difflib``, so a rename pass, a reword of the same length or
     a reflow inserts none, and a deletion elsewhere in the bullet does not cancel an insertion; words a later commit
     inserts are that commit's finding, not this one's.

   "Released" means the version's tag (``--tag-prefix`` + version) is in the commit's history, or a later final
   version's tag is (which covers a version with no tag, and one tagged off this history). Versions are ordered as
   PEP 440 orders them, so ``0.1.1a`` is a release of its own, before ``0.1.1``, and identified by their canonical
   spelling, so ``[1.1]`` is tag ``1.1.0`` and ``[1.1.0-rc1]`` is tag ``1.1.0rc1``. ``--ignore-tag VERSION`` drops a tag whose
   release never shipped; a tag in AT's history whose version has no heading in the file is named in a WARNING, and
   so is every version heading with no local tag, with whether it is treated as released.
5. Prints each commit's events, then the findings open at AT, each with the commit that caused it, and exits 1 if any
   is open. ``--accept COMMIT`` records a ruling that the commit's changes were deliberate: its findings print as
   ``ACCEPTED`` and do not count.

What it cannot do
-----------------
- Tell a deliberate change from an accidental one, until a person rules (``--accept``). Measured on real history,
  these read as findings until ruled: a commit that backfills a missing section for an already released version
  (juniper-ci-tools ``9d98702e``), one that restores a released section to the text that shipped (juniper-service-core
  ``a10820ed``: the restored words read as added, since the tool does not compare with the release's own text), one
  that appends a qualifier to category headings (``9cea64c5``: ``### Added`` -> ``### Added, 0.2.1``), a dated
  correction (``40815bb4``), and a release that was tagged and never shipped while its section stayed (``v0.7.0``,
  ``54bf722d``: with or without ``--ignore-tag 0.7.0`` one of the two sections reads as misfiled).
- Judge the category of a bullet a commit ADDS. Only the PR's intent says where that belongs.
- Know a release from its tag alone: every local tag under the prefix is taken as a shipped release, and a version
  with no local tag reads as not yet released, or as released when a later final release is tagged (the WARNINGs
  name each such version).
- See before the walk. A bullet's place at the start is taken as correct, and a commit before ``--since`` is never
  blamed. For a released section, the predecessor's check against the archived release notes still finds a bullet
  the release did not ship.
- Follow a bullet rewritten past the edit ratio, which reads as one removal and one addition. Similar bullets can
  also be paired with the wrong partner, which can hide or invent a move.
- Read a version heading that is indented, or a release tag outside ``--tag-prefix``.

Usage
-----
    python3 util/ad-hoc/2026-11-24_released_section_drift.py --since v0.11.4 [--at origin/main] [--path CHANGELOG.md]
    python3 util/ad-hoc/2026-11-24_released_section_drift.py --merge 187e3258 --at 48b66130^
    python3 util/ad-hoc/2026-11-24_released_section_drift.py --since juniper-service-core-v0.7.0 \
        --path juniper-service-core/CHANGELOG.md            # --tag-prefix defaults to "<dir>-v" for <dir>/CHANGELOG.md
    python3 util/ad-hoc/2026-11-24_released_section_drift.py --since v0.8.0 --accept 40815bb4
    python3 util/ad-hoc/2026-11-24_released_section_drift.py --since v0.5.0 --at v0.8.0 --ignore-tag 0.7.0
    python3 util/ad-hoc/2026-11-24_released_section_drift.py --self-test

Exit status: 0 no finding open at AT; 1 at least one; 2 a usage or git error.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess  # nosec B404 -- runs git with an argv list, no shell
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "util" / "release_train"))  # the release train's modules import each other top-level

import notes_render  # noqa: E402

UNRELEASED = "Unreleased"
NO_CATEGORY = "(no category)"
EDIT_RATIO = 0.75
_WORD_OVERLAP = 0.5  # a cheap filter before difflib, for long bullets only: an edit keeps most of its words
_WORD_FILTER_MIN = 8
_CHARACTER_RATIO_MAX = 600  # two texts this long in all are compared character by character; longer, word by word
_VERSION_HEADING_RE = re.compile(r"^##\s")
_BRACKETED_RE = re.compile(r"^##\s+\[([^\]]+)\]")
_BARE_RE = re.compile(r"^##\s+(\S+)")
_LOOKS_LIKE_VERSION_RE = re.compile(r"^v?\d+(\.\d+)*")
_LINK_DEFINITION_RE = re.compile(r"""^\s{0,3}\[[^\]]+\]:\s+(<[^>]*>|\S+)(\s+("[^"]*"|'[^']*'|\([^)]*\)))?\s*$""")

ADDED_WORDS_MIN = 4  # words one commit must insert into a released bullet for TEXT ADDED; a rename inserts none

WRONG_VERSION = "WRONG VERSION"
RECATEGORIZED = "RECATEGORIZED"
TEXT_ADDED = "TEXT ADDED UNDER RELEASED"
NO_VERSION = "(no version)"


class GitError(RuntimeError):
    """A git command failed."""


# ── parsing ─────────────────────────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Entry:
    """One top-level bullet: the version it sits under (``vid`` identifies a repeated heading apart from the first),
    its category heading (``None`` when it has none), its text and its first line."""

    version: str
    vid: str
    heading: str | None
    text: str
    line: int

    @property
    def key(self) -> str:
        return normalize(self.text)

    @property
    def hid(self) -> str:
        return (self.heading or NO_CATEGORY).casefold()

    @property
    def place(self) -> tuple[str, str]:
        return (self.vid, self.hid)

    def where(self) -> str:
        return f"[{self.version if self.vid == vid_of(self.version) else self.vid}] ### {self.heading or NO_CATEGORY}"

    def lead(self, width: int = 96) -> str:
        first = self.text.splitlines()[0] if self.text else ""
        return first if len(first) <= width else first[: width - 1] + "…"


@dataclass(frozen=True)
class Parsed:
    entries: list[Entry]
    versions: list[str]  # vids, in file order
    labels: dict[str, str] = field(default_factory=dict)  # vid -> the version as its heading writes it


def normalize(text: str) -> str:
    return " ".join(text.split())


def vid_of(label: str) -> str:
    """A version's identity: ``Unreleased``; for a label that is a version, its canonical PEP 440 spelling, so ``1.1``
    and ``1.1.0`` are one version, as are ``1.1.0-rc1`` and ``1.1.0rc1``, and ``0.1.1a`` and ``0.1.1a0``; any other
    label casefolded."""
    if label.casefold() == UNRELEASED.casefold():
        return UNRELEASED
    if _PEP440_RE.fullmatch(label.strip()) is None:
        return label.casefold()
    release, pre, post, dev = version_key(label.strip())
    text = ".".join(str(n) for n in release + (0,) * (3 - len(release)))  # at least major.minor.patch, as written here
    if pre[0] in (0, 1, 2):
        text += ("a", "b", "rc")[pre[0]] + str(pre[1])
    if post:
        text += f".post{post - 1}"
    if dev[0] == 0:
        text += f".dev{dev[1]}"
    return text


def _is_final(vid: str) -> bool:
    _release, pre, _post, dev = version_key(vid)
    return pre == (3, 0) and dev == (1, 0)


def looks_like_version(vid: str) -> bool:
    return bool(_LOOKS_LIKE_VERSION_RE.match(vid))


_PEP440_RE = re.compile(r"^v?(\d+(?:\.\d+)*)(?:[-_.]?(a|alpha|b|beta|c|rc|pre|preview)[-_.]?(\d*))?(?:[-_.]?(post|rev|r)[-_.]?(\d*))?(?:[-_.]?(dev)[-_.]?(\d*))?", re.IGNORECASE)
_PRE_RANK = {"a": 0, "alpha": 0, "b": 1, "beta": 1, "c": 2, "rc": 2, "pre": 2, "preview": 2}


def version_key(vid: str) -> tuple:
    """A sort key in PEP 440's order: ``0.1.1.dev0`` < ``0.1.1a`` < ``0.1.1rc1`` < ``0.1.1`` < ``0.1.1.post1``, and
    ``0.1`` equals ``0.1.0``. Text after the version is ignored; a label that is not a version sorts first."""
    match = _PEP440_RE.match(vid.split("#", 1)[0])
    if match is None:
        return ((), (-2, 0), 0, (1, 0))
    release = tuple(int(n) for n in match.group(1).split("."))
    while len(release) > 1 and release[-1] == 0:
        release = release[:-1]
    if match.group(2):
        pre = (_PRE_RANK[match.group(2).lower()], int(match.group(3) or 0))
    elif match.group(6) and not match.group(4):
        pre = (-1, 0)  # a development release of a final version sorts before its pre-releases
    else:
        pre = (3, 0)
    post = int(match.group(5) or 0) + 1 if match.group(4) else 0
    dev = (0, int(match.group(7) or 0)) if match.group(6) else (1, 0)
    return (release, pre, post, dev)


def version_label(line: str) -> str | None:
    """The version a ``## `` heading opens (``## [0.11.4] - 2026-11-06`` -> ``0.11.4``; a bare ``## `` ->
    ``(blank)``), or ``None`` for any other line. A version heading is what ``ceremony.changelog_version_section``
    stops at: ``^##\\s`` and not ``###``."""
    if not _VERSION_HEADING_RE.match(line) or line.startswith("###"):
        return None
    match = _BRACKETED_RE.match(line) or _BARE_RE.match(line)
    if match is None:
        return "(blank)"
    label = match.group(1).strip()
    return UNRELEASED if label.casefold() == UNRELEASED.casefold() else label


def bullets_with_lines(body: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """``notes_render._split_bullets`` with each bullet's first line number kept; it refuses to disagree with it."""
    out: list[tuple[int, str]] = []
    current: list[str] = []
    start = 0
    for number, raw in body:
        stripped = raw.strip()
        is_marker = stripped.startswith(("- ", "* ")) or stripped in ("-", "*")
        indent = len(raw) - len(raw.lstrip())
        if is_marker and indent == 0:
            if current:
                out.append((start, "\n".join(current).rstrip()))
            current = [stripped[1:].strip()]
            start = number
        elif current:
            current.append(raw.rstrip())
    if current:
        out.append((start, "\n".join(current).rstrip()))
    out = [(number, bullet) for number, bullet in out if bullet.strip()]
    if [bullet for _, bullet in out] != notes_render._split_bullets([raw for _, raw in body]):
        raise RuntimeError("bullets_with_lines disagrees with notes_render._split_bullets")
    return out


def bullet_text(raw: str) -> str:
    """A bullet's own text from the release train's split: its lines up to a blank line followed by an unindented
    line, where Markdown ends the list item, and without link-reference definitions (``[0.1.1]: https://…``). The
    train's split runs on into what follows the oldest bullet, such as a link footer or a closing comment."""
    lines = raw.split("\n")
    kept: list[str] = []
    for index, line in enumerate(lines):
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if not line.strip() and following.strip() and not following[:1].isspace():
            break
        kept.append(line)
    return "\n".join(line for line in kept if not _LINK_DEFINITION_RE.match(line)).rstrip()


def parse(text: str) -> Parsed:
    """Every bullet in file order, with its version (``(no version)`` above the first version heading) and its
    category heading or ``None``; and the version headings in file order."""
    entries: list[Entry] = []
    versions: list[str] = []
    labels: dict[str, str] = {}
    seen: Counter = Counter()
    label = NO_VERSION  # a bullet above the first version heading belongs to no version (the release train drops it)
    vid = NO_VERSION
    heading: str | None = None
    body: list[tuple[int, str]] = []

    def flush() -> None:
        if body:
            for number, bullet in bullets_with_lines(body):
                entries.append(Entry(label, vid, heading, bullet_text(bullet), number))

    for number, raw in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        new_label = version_label(raw)
        if new_label is not None:
            flush()
            label, heading, body = new_label, None, []
            base = vid_of(new_label)
            seen[base] += 1
            vid = base if seen[base] == 1 else f"{base}#{seen[base]}"
            versions.append(vid)
            labels.setdefault(vid, new_label if seen[base] == 1 else f"{new_label}#{seen[base]}")
            continue
        key = notes_render.heading_key(raw)
        if key is not None:
            flush()
            heading, body = key, []
            continue
        body.append((number, raw))
    flush()
    return Parsed(entries, versions, labels)


# ── pairing ─────────────────────────────────────────────────────────────────────────────────────────────────────────


def _similar(a: str, b: str) -> float:
    words_a, words_b = set(a.split()), set(b.split())
    if not words_a or not words_b:
        return 0.0
    shorter = a if len(a) <= len(b) else b
    if len(shorter.split()) >= 3 and (a.startswith(b) or b.startswith(a)):
        return max(EDIT_RATIO, difflib.SequenceMatcher(None, a, b).ratio())  # text appended to a bullet is an edit of it
    if min(len(words_a), len(words_b)) >= _WORD_FILTER_MIN and len(words_a & words_b) / len(words_a | words_b) < _WORD_OVERLAP:
        return 0.0
    # No autojunk: on a text of 200 characters or more it drops every character that is common in it, and the ratio of
    # a long bullet edited in the middle collapses (0.15 for one with six words cut and eight added). A long text is
    # compared word by word, which is what an edit changes, and stays fast.
    if len(a) + len(b) <= _CHARACTER_RATIO_MAX:
        return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    return difflib.SequenceMatcher(None, a.split(), b.split(), autojunk=False).ratio()


def pair(old: list[Entry], new: list[Entry]) -> tuple[list[tuple[Entry, Entry]], list[Entry], list[Entry]]:
    """Pair each OLD bullet with itself in NEW: equal normalized text at the same place first, then equal text anywhere
    (in file order), then the most similar leftover at ``EDIT_RATIO`` or more (an edit), preferring one that stayed
    where it was. Returns (pairs, removed, added)."""
    pairs: list[tuple[Entry, Entry]] = []
    remaining_new = list(new)
    remaining_old: list[Entry] = []
    by_text_place: dict[tuple[str, tuple[str, str]], list[int]] = {}
    for index, entry in enumerate(remaining_new):
        by_text_place.setdefault((entry.key, entry.place), []).append(index)
    taken: set[int] = set()
    for entry in old:
        bucket = by_text_place.get((entry.key, entry.place))
        if bucket:
            index = bucket.pop(0)
            taken.add(index)
            pairs.append((entry, remaining_new[index]))
        else:
            remaining_old.append(entry)
    by_text: dict[str, list[int]] = {}
    for index, entry in enumerate(remaining_new):
        if index not in taken:
            by_text.setdefault(entry.key, []).append(index)
    removed: list[Entry] = []
    for entry in remaining_old:
        bucket = by_text.get(entry.key)
        if bucket:
            index = bucket.pop(0)
            taken.add(index)
            pairs.append((entry, remaining_new[index]))
        else:
            removed.append(entry)
    added = [entry for index, entry in enumerate(remaining_new) if index not in taken]
    scored = []
    for i, gone in enumerate(removed):
        for j, came in enumerate(added):
            ratio = _similar(gone.key, came.key)
            if ratio >= EDIT_RATIO:
                scored.append((ratio + (0.001 if gone.place == came.place else 0.0), i, j))
    used_removed: set[int] = set()
    used_added: set[int] = set()
    for _, i, j in sorted(scored, reverse=True):
        if i in used_removed or j in used_added:
            continue
        used_removed.add(i)
        used_added.add(j)
        pairs.append((removed[i], added[j]))
    removed = [entry for i, entry in enumerate(removed) if i not in used_removed]
    added = [entry for j, entry in enumerate(added) if j not in used_added]
    return pairs, removed, added


# ── releases ────────────────────────────────────────────────────────────────────────────────────────────────────────


class Releases(Protocol):
    tags: dict[str, str]
    labels: dict[str, str]

    def released(self, vid: str, at: str) -> bool:
        """Whether version VID is released at commit AT, by ``_released_by_rule``."""

    def containing(self, commit: str) -> list[str]:
        """Every tagged version whose tag contains COMMIT, in version order."""


def _released_by_rule(vid: str, merged: frozenset[str], tags: dict[str, str]) -> bool:
    """Whether VID is released, given the tagged versions MERGED into the commit: when its own tag is, or when a later
    FINAL version's tag is. The second rule covers a version with no tag and one whose tag sits off this history (a
    release tagged on a branch that was squash-merged); a later pre-release does not imply it."""
    if vid in merged:
        return True
    if not looks_like_version(vid) or "#" in vid:
        return False
    key = version_key(vid)
    return any(version_key(v) > key and _is_final(v) for v in merged)


class GitReleases:
    """Release tags ``PREFIX<version>`` read from git: a version is released at a commit when its tag is in that
    commit's history. A version in IGNORE is treated as having no tag (a release that was tagged and never shipped)."""

    def __init__(self, repo: Path, prefix: str, ignore: frozenset[str] = frozenset()) -> None:
        self.repo, self.prefix, self.ignore = repo, prefix, ignore
        self.tags: dict[str, str] = {}
        self.labels: dict[str, str] = {}
        for name in git(repo, "tag", "--list", f"{prefix}*").split():
            vid = self._vid(name)
            if vid is not None:
                self.tags[vid] = git(repo, "rev-parse", f"{name}^{{commit}}").strip()
                self.labels[vid] = name[len(prefix) :]
        self._merged: dict[str, frozenset[str]] = {}
        self._containing: dict[str, list[str]] = {}

    def _vid(self, name: str) -> str | None:
        version = name[len(self.prefix) :]
        if not looks_like_version(version) or vid_of(version) in self.ignore:
            return None
        return vid_of(version)

    def merged(self, at: str) -> frozenset[str]:
        """The tagged versions in AT's history: one ``git tag --merged`` per commit, cached."""
        if at not in self._merged:
            names = git(self.repo, "tag", "--merged", at, "--list", f"{self.prefix}*").split()
            self._merged[at] = frozenset(v for v in (self._vid(n) for n in names) if v is not None)
        return self._merged[at]

    def released(self, vid: str, at: str) -> bool:
        return _released_by_rule(vid, self.merged(at), self.tags)

    def containing(self, commit: str) -> list[str]:
        """Every tagged version whose tag contains COMMIT, in version order: one ``git tag --contains``, cached."""
        if commit not in self._containing:
            names = git(self.repo, "tag", "--contains", commit, "--list", f"{self.prefix}*").split()
            self._containing[commit] = sorted((v for v in (self._vid(n) for n in names) if v is not None), key=version_key)
        return self._containing[commit]


class FakeReleases:
    """Releases over a straight history (the self-test's): ``order`` lists the commits oldest first and ``tags`` maps a
    version to the commit it tags."""

    def __init__(self, order: list[str], tags: dict[str, str]) -> None:
        self.order, self.tags = order, {vid_of(v): c for v, c in tags.items()}
        self.labels = {vid_of(v): v for v in tags}

    def is_ancestor(self, a: str, b: str) -> bool:
        return self.order.index(a) <= self.order.index(b)

    def released(self, vid: str, at: str) -> bool:
        return _released_by_rule(vid, frozenset(v for v, c in self.tags.items() if self.is_ancestor(c, at)), self.tags)

    def containing(self, commit: str) -> list[str]:
        return sorted((v for v, c in self.tags.items() if self.is_ancestor(commit, c)), key=version_key)


# ── the walk ────────────────────────────────────────────────────────────────────────────────────────────────────────


@dataclass
class Step:
    """One commit of the walk: its label and full id, its first parent's id, subject, the file at its parent and at
    itself, and whether the bullets it adds or moves are judged (``--merge`` judges only the merge's)."""

    label: str
    commit: str
    parent: str
    subject: str
    old_text: str
    new_text: str
    seeds: bool = True


@dataclass
class Bullet:
    """One bullet followed through the walk."""

    entry: Entry
    origin: str  # commit that added it, or the walk's base commit for one already there
    origin_label: str
    pinned: str | None  # the version it was under at the start of the walk, if not [Unreleased]
    category: str  # casefolded heading it was filed under
    category_text: str
    judged: bool
    baseline: bool = False  # already in the file at the walk's start
    version_by: str | None = None
    version_by_commit: str | None = None  # the full id of that commit
    category_by: str | None = None
    inserted: list[tuple[str, str, list[str]]] = field(default_factory=list)  # (commit, text before it, words it inserted)


@dataclass
class Finding:
    kind: str
    by: str
    entry: Entry
    detail: str
    accepted: bool = False


@dataclass
class WalkResult:
    findings: list[Finding] = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    @property
    def open(self) -> list[Finding]:
        return [f for f in self.findings if not f.accepted]


def expected_versions(bullet: Bullet, at: str, versions_at: list[str], releases: Releases, show=lambda vid: vid) -> tuple[set[str], str]:
    """The versions BULLET may sit under at AT (identities), and a phrase saying why, with each version as SHOW
    writes it. A bullet belongs to the first FINAL release that contains the commit that added it; it may also sit
    under a released pre-release of that line that shipped it, since a pre-release's notes are a preview."""
    if bullet.pinned is not None:
        return {bullet.pinned}, f"it stood under [{show(bullet.pinned)}] when the walk first saw it"
    source = f"it was in [{UNRELEASED}] at the walk's start, {bullet.origin[:8]}, which" if bullet.baseline else f"{bullet.origin_label}, which added it,"
    containing = releases.containing(bullet.origin)
    finals = [v for v in containing if _is_final(v)]
    first = finals[0] if finals else None
    previews = {v for v in containing if not _is_final(v) and (first is None or version_key(v) < version_key(first)) and releases.released(v, at)}
    also = f" (or the pre-release {', '.join(show(v) for v in sorted(previews, key=version_key))} that shipped it)" if previews else ""
    if first is not None and releases.released(first, at):
        return {first} | previews, f"{source} first shipped in {show(first)}{also}"
    if first is not None:
        return {UNRELEASED, first} | previews, f"{source} first ships in {show(first)}, not released at this commit{also}"
    pending = {v for v in versions_at if v != UNRELEASED and looks_like_version(v) and "#" not in v and not releases.released(v, at)}
    return {UNRELEASED} | pending | previews, f"no final release contains {bullet.origin[:8]} yet{also}"


def inserted_words(before: str, after: str) -> list[str]:
    """The words AFTER inserts into BEFORE, word by word as ``difflib`` aligns them: each inserted run, and the growth
    of a replaced run. A rename, a reword of the same length, a reflow or a deletion inserts none, and a deletion
    elsewhere does not cancel an insertion."""
    old, new = before.split(), after.split()
    out: list[str] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag == "insert":
            out.extend(new[j1:j2])
        elif tag == "replace" and (j2 - j1) > (i2 - i1):
            out.extend(new[j1 + (i2 - i1) : j2])
    return out


def still_inserted(before: str, now: str, words: list[str]) -> list[str]:
    """Which of the WORDS one commit inserted (in its order) into a bullet that read BEFORE are still in it when it
    reads NOW: words a later commit added are not counted against this one."""
    left = Counter(now.split()) - Counter(before.split())
    out = []
    for word in words:  # only this commit's words, each at most as often as it is still there
        if left[word] > 0:
            left[word] -= 1
            out.append(word)
    return out


def walk(steps: list[Step], releases: Releases, at: str, accept: frozenset[str] = frozenset(), start: str | None = None) -> WalkResult:
    """Follow every bullet through STEPS (oldest first, each one's old text the previous one's new text) and judge the
    bullets at AT, the last step's commit or a later one that did not change the file. START is the walk's start
    commit (``--since``, or the merge's parent), the latest commit a bullet already in the file can have come from;
    it defaults to the first step's parent, which can be later."""
    result = WalkResult()
    if not steps:
        return result
    base = steps[0]
    origin = start or base.parent
    state: dict[tuple[int, str], Bullet] = {}
    judge_all = all(step.seeds for step in steps)
    for entry in parse(base.old_text).entries:
        state[(entry.line, entry.key)] = Bullet(entry, origin, f"the walk's start ({origin[:8]})", entry.vid if entry.vid != UNRELEASED else None, entry.hid, entry.heading or NO_CATEGORY, judge_all, baseline=True)
    previous_text = base.old_text
    for step in steps:
        if step.old_text != previous_text:
            raise RuntimeError(f"the walk is not contiguous at {step.label}: its parent's file differs from the previous step's")
        previous_text = step.new_text
        before, after = parse(step.old_text), parse(step.new_text)
        pairs, removed, added = pair(before.entries, after.entries)
        events: list[str] = []
        cut_moves: Counter = Counter()
        new_state: dict[tuple[int, str], Bullet] = {}
        for old, new in pairs:
            bullet = state.pop((old.line, old.key))
            if old.hid != new.hid:
                bullet.category_by = step.label
                bullet.judged = bullet.judged or step.seeds
                events.append(f"  recategorized  {old.where()} -> {new.where()}  L{new.line}  {new.lead()}")
            if old.vid != new.vid:
                bullet.version_by, bullet.version_by_commit = step.label, step.commit
                bullet.judged = bullet.judged or step.seeds
                if old.vid == UNRELEASED and looks_like_version(new.vid) and "#" not in new.vid and not releases.released(new.vid, step.parent) and old.hid == new.hid:
                    cut_moves[new.version] += 1
                else:
                    events.append(f"  moved  {old.where()} -> {new.where()}  L{new.line}  {new.lead()}")
            elif releases.released(old.vid, step.parent):
                words = inserted_words(old.text, new.text)
                if len(words) >= ADDED_WORDS_MIN:
                    bullet.inserted.append((step.label, old.text, words))
                    bullet.judged = bullet.judged or step.seeds
                    events.append(f"  {len(words)} word(s) added to a bullet under released {new.where()}  L{new.line}  {new.lead()}")
            bullet.entry = new
            new_state[(new.line, new.key)] = bullet
        for new in added:
            # A bullet first written above every version heading (a preamble list) belongs there; only a bullet that
            # was under a version and fell out of it is misfiled there.
            pinned = NO_VERSION if new.vid == NO_VERSION else None
            bullet = Bullet(new, step.commit, step.label, pinned, new.hid, new.heading or NO_CATEGORY, step.seeds, version_by=step.label, version_by_commit=step.commit)
            new_state[(new.line, new.key)] = bullet
            allowed, _why = expected_versions(bullet, step.commit, after.versions, releases)
            if new.vid not in allowed or new.heading is None:
                events.append(f"  added under {new.where()}  L{new.line}  {new.lead()}")
        if removed:
            events.append(f"  {len(removed)} bullet(s) removed: " + "; ".join(entry.lead(48) for entry in removed[:3]) + (" …" if len(removed) > 3 else ""))
        for version, count in cut_moves.items():
            events.insert(0, f"  release cut: {count} bullet(s) [{UNRELEASED}] -> [{version}]")
        state = new_state
        if events:
            result.log.append(f"commit {step.label}  {step.subject[:100]}")
            result.log.extend(events)
    final = parse(steps[-1].new_text)
    versions_at = final.versions

    def show(vid: str) -> str:
        return final.labels.get(vid) or releases.labels.get(vid) or vid

    for bullet in sorted(state.values(), key=lambda b: b.entry.line):
        if not bullet.judged:
            continue
        entry = bullet.entry
        allowed, why = expected_versions(bullet, at, versions_at, releases, show)
        if entry.vid not in allowed:
            by = bullet.version_by or bullet.origin_label
            release = next((v for v in allowed if _is_final(v)), None)
            if entry.vid == UNRELEASED and UNRELEASED not in allowed and release is not None:
                # Left behind in [Unreleased]: the release's cut did it, unless a commit made after that release moved
                # it back, and then that commit did. The PR that filed it correctly never did.
                moved_after = bullet.version_by_commit is not None and releases.released(release, bullet.version_by_commit)
                if not moved_after:
                    by = releases.tags.get(release, by)[:8]
            want = " or ".join(f"[{show(v)}]" for v in sorted(allowed, key=lambda v: (v != UNRELEASED, version_key(v))))
            result.findings.append(Finding(WRONG_VERSION, by, entry, f"belongs under {want}: {why}", by in accept))
        if entry.hid != bullet.category:
            by = bullet.category_by or bullet.origin_label
            result.findings.append(Finding(RECATEGORIZED, by, entry, f"was filed under ### {bullet.category_text}", by in accept))
        for by, before_text, words in bullet.inserted:
            still = still_inserted(before_text, entry.text, words)
            if len(still) >= ADDED_WORDS_MIN:
                result.findings.append(Finding(TEXT_ADDED, by, entry, f"{len(still)} word(s) added after its release: {' '.join(still[:12])[:90]!r}", by in accept))
    return result


# ── git ─────────────────────────────────────────────────────────────────────────────────────────────────────────────


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.strip()[:300]}")
    return proc.stdout


def read_at(repo: Path, rev: str, path: str) -> str:
    """PATH's text at REV, or "" where REV has no such file."""
    probe = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{rev}:{path}"], capture_output=True, check=False)  # nosec B603 B607
    if probe.returncode != 0:
        return ""
    return git(repo, "show", f"{rev}:{path}")


def build_steps(repo: Path, path: str, at: str, since: str | None, merge: str | None) -> list[Step]:
    start = merge if merge is not None else since
    assert start is not None
    if subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", start, at], capture_output=True, check=False).returncode != 0:  # nosec B603 B607
        raise GitError(f"{start} is not an ancestor of {at}")
    if merge is not None:
        first = git(repo, "rev-parse", "--verify", f"{merge}^{{commit}}").strip()
        commits = [first] + git(repo, "rev-list", "--first-parent", "--reverse", f"{merge}..{at}", "--", path).split()
        seeded = {first}
    else:
        commits = git(repo, "rev-list", "--first-parent", "--reverse", f"{since}..{at}", "--", path).split()
        seeded = set(commits)
    steps = []
    for sha in commits:
        subject = git(repo, "log", "-1", "--format=%s", sha).strip()
        parent = git(repo, "rev-parse", f"{sha}^").strip()
        steps.append(Step(sha[:8], sha, parent, subject, read_at(repo, parent, path), read_at(repo, sha, path), sha in seeded))
    return steps


def report(result: WalkResult, at_label: str) -> int:
    for line in result.log:
        print(line)
    still = result.open
    accepted = [f for f in result.findings if f.accepted]
    print()
    print(f"At {at_label}: {len(still)} finding(s) open" + (f", {len(accepted)} accepted" if accepted else "") + ".")
    for finding in sorted(result.findings, key=lambda f: (f.accepted, f.entry.line)):
        state = "ACCEPTED" if finding.accepted else "OPEN"
        print(f"  {state} {finding.kind}  {finding.entry.where()}  L{finding.entry.line}  by {finding.by}  {finding.entry.lead()}")
        print(f"      {finding.detail}")
    return 1 if still else 0


# ── self-test ───────────────────────────────────────────────────────────────────────────────────────────────────────


def _doc(*sections: str) -> str:
    return "\n".join(["# Changelog", "", *sections, ""])


def _lines(*lines: str) -> str:
    return "\n".join(lines)


def _run(texts: list[str], tags: dict[str, str], seeds: list[bool] | None = None, at: str | None = None, accept: frozenset[str] = frozenset()) -> WalkResult:
    """Walk TEXTS (the base, then one text per commit c1, c2, ...); TAGS maps a version to a label: "t0" (a commit
    before the base), "base", or a commit."""
    labels = ["base"] + [f"c{i}" for i in range(1, len(texts))]
    steps = [Step(labels[i], labels[i], labels[i - 1], f"step {i}", texts[i - 1], texts[i], True if seeds is None else seeds[i - 1]) for i in range(1, len(texts))]
    return walk(steps, FakeReleases(["t0", *labels], tags), at or labels[-1], accept)


def _kinds(result: WalkResult) -> list[tuple[str, str]]:
    return sorted((f.kind, f.entry.lead().split("**")[1] if "**" in f.entry.lead() else f.entry.lead()) for f in result.open)


def _git_self_test(check) -> None:
    """The git-backed paths (``build_steps``, ``GitReleases``, ``--ignore-tag``, ``--accept``, the WARNINGs and
    ``main``) on a throwaway repository: the ml#2360 shape, tagged. It is built under the system temp directory
    (``TMPDIR``, the repository's own ``tmp/`` on this host) with signing switched off in its own config, as the
    fixture repositories in ``tests/`` do."""
    import contextlib
    import io
    import tempfile

    r100 = _lines("## [1.0.0] - 2026-01-01", "", "### Fixed", "", "- **R1** released fix.")
    texts = [
        ("base", _doc("## [Unreleased]", "", r100), ["v1.0.0", "v0.9.9"]),
        ("added", _doc(_lines("## [Unreleased]", "", "### Added", "", "- **A1** first added.", "- **A2** second added."), "", r100), []),
        ("misfile", _doc(_lines("## [Unreleased]", "", "### Added", "", "- **P1** the PR's addition.", "", "### Changed", "", "- **A1** first added.", "- **A2** second added."), "", r100 + "\n- **P3** filed under the released version."), []),
        ("repair", _doc("## [Unreleased]", "", _lines("## [1.1.0] - 2026-02-01", "", "### Added", "", "- **P1** the PR's addition.", "- **A1** first added.", "- **A2** second added.", "", "### Fixed", "", "- **P3** filed under the released version."), "", r100), ["v1.1.0"]),
    ]
    with tempfile.TemporaryDirectory(prefix="r50-self-test-") as directory:
        repo = Path(directory)

        def run(*args: str) -> None:
            subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)  # nosec B603 B607

        run("init", "-q")
        for key, value in (("user.name", "self-test"), ("user.email", "self-test@example.invalid"), ("commit.gpgsign", "false"), ("tag.gpgsign", "false")):
            run("config", key, value)
        for name, text, names in texts:
            (repo / "CHANGELOG.md").write_text(text, encoding="utf-8")
            run("add", "CHANGELOG.md")
            run("commit", "-q", "-m", name)
            for tag in names:
                run("tag", tag)

        def main_out(*args: str) -> tuple[int, str]:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([*args, "--repo", str(repo)])
            return code, out.getvalue()

        code, text = main_out("--since", "v1.0.0", "--at", "HEAD~1")
        check("git: the misfile, three open", code == 1 and "3 finding(s) open" in text)
        check("git: a tag with no heading is named", "tag v0.9.9 is in the history of --at" in text)
        code, text = main_out("--since", "v1.0.0", "--at", "HEAD")
        check("git: the tagged repair, none open", code == 0 and "0 finding(s) open" in text)
        code, text = main_out("--merge", "HEAD~1", "--at", "HEAD~1", "--ignore-tag", "0.9.9")
        check("git: --merge and --ignore-tag", code == 1 and "3 finding(s) open" in text and "v0.9.9" not in text)
        code, text = main_out("--since", "v1.0.0", "--at", "HEAD~1", "--accept", "HEAD~1")
        check("git: --accept by commit", code == 0 and "0 finding(s) open, 3 accepted" in text)
        code, text = main_out("--since", "v1.0.0", "--at", "HEAD~1", "--ignore-tag", "1.0.0")
        check("git: --ignore-tag drops the release", code == 1 and "no local tag for [1.0.0]" in text)


def self_test() -> int:
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    r100 = _lines("## [1.0.0] - 2026-01-01", "", "### Fixed", "", "- **R1** released fix.")
    unreleased = _lines("## [Unreleased]", "", "### Added", "", "- **A1** first added.", "- **A2** second added,", "  with a continuation line.", "", "### Fixed", "", "- **F1** a fix.")
    base = _doc(_lines("## [Unreleased]", "", "### Added", "", "- **A0** already here."), "", r100)
    before = _doc(unreleased, "", r100)  # A1, A2, F1 added by c1 under [Unreleased]
    # The ml#2360 shape: the PR's Added bullet, then its own Changed heading and bullet, inserted above A1 and A2; and
    # its fix filed under the released version.
    misfiled = _doc(
        _lines("## [Unreleased]", "", "### Added", "", "- **P1** the PR's addition.", "", "### Changed", "", "- **P2** the PR's change.", "- **A1** first added.", "- **A2** second added,", "  with a continuation line.", "", "### Fixed", "", "- **F1** a fix."),
        "",
        r100 + "\n- **P3** the PR's fix, filed under the released version.",
    )
    repaired_cut = _doc(
        "## [Unreleased]",
        "",
        _lines("## [1.1.0] - 2026-02-01", "", "### Added", "", "- **P1** the PR's addition.", "- **A1** first added.", "- **A2** second added,", "  with a continuation line, edited by the Overtoad.", "", "### Changed", "", "- **P2** the PR's change.", "", "### Fixed", "", "- **F1** a fix.", "- **P3** the PR's fix, filed under the released version."),
        "",
        r100,
    )
    unrepaired_cut = _doc(
        "## [Unreleased]",
        "",
        _lines("## [1.1.0] - 2026-02-01", "", "### Added", "", "- **P1** the PR's addition.", "", "### Changed", "", "- **P2** the PR's change.", "- **A1** first added.", "- **A2** second added,", "  with a continuation line.", "", "### Fixed", "", "- **F1** a fix."),
        "",
        r100 + "\n- **P3** the PR's fix, filed under the released version.",
    )
    tags = {"1.0.0": "base"}

    # 1. The misfiling: one bullet under a released version, two recategorized; the PR's own bullets are fine.
    result = _run([base, before, misfiled], tags)
    check("misfiling: kinds", _kinds(result) == [(RECATEGORIZED, "A1"), (RECATEGORIZED, "A2"), (WRONG_VERSION, "P3")])
    check("misfiling: blamed on c2", all(f.by == "c2" for f in result.open))
    # 2. A release cut, tagged, that repairs all three (A2 also edited): nothing open.
    result = _run([base, before, misfiled, repaired_cut], {**tags, "1.1.0": "c3"})
    check("repair: none open", not result.open)
    check("repair: cut logged", any("release cut:" in line for line in result.log))
    # 3. A tagged cut that repairs nothing leaves all three open.
    result = _run([base, before, misfiled, unrepaired_cut], {**tags, "1.1.0": "c3"})
    check("cut only: three open", _kinds(result) == [(RECATEGORIZED, "A1"), (RECATEGORIZED, "A2"), (WRONG_VERSION, "P3")])
    # 4. A clean cut: nothing; a bullet written straight under the version being cut: nothing.
    clean = _doc("## [Unreleased]", "", _lines("## [1.1.0] - 2026-02-01", "", "### Added", "", "- **A0** already here.", "- **A1** first added.", "- **A2** second added,", "  with a continuation line.", "", "### Fixed", "", "- **F1** a fix."), "", r100)
    check("clean cut: nothing", not _run([base, before, clean], {**tags, "1.1.0": "c2"}).findings)
    check("cut writes a note: nothing", not _run([base, before, clean.replace("- **F1** a fix.", "- **F1** a fix.\n- **C1** written at the cut.")], {**tags, "1.1.0": "c2"}).findings)
    # 4b. A cut that also changes a category: recategorized, blamed on the cut.
    result = _run([base, before, clean.replace("### Fixed\n\n- **F1** a fix.", "### Changed\n\n- **F1** a fix.")], {**tags, "1.1.0": "c2"})
    check("cut that recategorizes", [(f.kind, f.by) for f in result.open] == [(RECATEGORIZED, "c2")])
    # 4c. A two-step cut: the heading first (c2), the bullets moved under it by the tagged commit (c3): nothing.
    early = before.replace("## [Unreleased]\n", "## [Unreleased]\n\n## [1.1.0] - 2026-02-01\n\n### Added\n\n- **V1** version bump.\n", 1)
    late = _doc("## [Unreleased]", "", _lines("## [1.1.0] - 2026-02-01", "", "### Added", "", "- **V1** version bump.", "- **A0** already here.", "- **A1** first added.", "- **A2** second added,", "  with a continuation line.", "", "### Fixed", "", "- **F1** a fix."), "", r100)
    result = _run([base, before, early, late], {**tags, "1.1.0": "c3"})
    check("two-step cut: nothing", not result.findings)
    # 4d. The same, judged at c2, before the tag: V1 sits under the pending [1.1.0], where it may.
    steps_c2 = [Step("c1", "c1", "base", "s", base, before), Step("c2", "c2", "c1", "s", before, early)]
    check("judged before the tag: nothing", not walk(steps_c2, FakeReleases(["base", "c1", "c2", "c3"], {**tags, "1.1.0": "c3"}), "c2").findings)
    # 4e. A cut no tag names yet: its bullets may sit under it.
    check("untagged pending cut: nothing", not _run([base, before, clean], tags).findings)
    # 4f. A version without a tag, below a released tagged one, counts as released.
    old_untagged = _doc("## [Unreleased]", "", r100, "", _lines("## [0.9.0] - 2025-12-01", "", "### Fixed", "", "- **O1** old fix."))
    check("added under an old untagged version", _kinds(_run([old_untagged, old_untagged.replace("- **O1** old fix.", "- **O1** old fix.\n- **O2** filed under it now.")], tags)) == [(WRONG_VERSION, "O2")])
    # 5. A second block of the same category, and a case-only heading fix: nothing.
    check("repeated heading: nothing", not _run([base, before, before.replace("- **F1** a fix.", "- **F0** another fix.\n\n### Fixed\n\n- **F1** a fix.")], tags).findings)
    check("heading case fix: nothing", not _run([base, before.replace("### Fixed", "### fixed"), before], tags).findings)
    # 6. --merge semantics: an unseeded step's moves are not judged; a seeded one's are.
    deliberate = before.replace("### Fixed\n\n- **F1** a fix.", "### Changed\n\n- **F1** a fix.")
    check("unseeded: nothing", not _run([base, before, deliberate], tags, seeds=[False, False]).findings)
    check("seeded: recategorized", _kinds(_run([base, before, deliberate], tags)) == [(RECATEGORIZED, "F1")])
    base_r = _doc("## [Unreleased]", "", r100)
    moved_r = base_r.replace("### Fixed", "### Changed")
    check("unseeded step, start bullet: nothing", not _run([base_r, moved_r], tags, seeds=[False]).findings)
    check("seeded step, start bullet: recategorized", _kinds(_run([base_r, moved_r], tags)) == [(RECATEGORIZED, "R1")])
    accepted_both = _run([base, before, deliberate.replace("- **R1** released fix.", "- **R1** released fix.\n- **F2** also filed here.")], tags, accept=frozenset({"c2"}))
    check("--accept covers every kind", not accepted_both.open and sorted(f.kind for f in accepted_both.findings) == [RECATEGORIZED, WRONG_VERSION])
    # 7. Deleting a misfiled bullet leaves nothing to judge.
    check("deleted: two left", len(_run([base, before, misfiled, misfiled.replace("\n- **P3** the PR's fix, filed under the released version.", "")], tags).open) == 2)
    # 8. A bullet moved from [Unreleased] into the released version: wrong version.
    moved = before.replace("- **F1** a fix.", "").replace("- **R1** released fix.", "- **R1** released fix.\n- **F1** a fix.")
    check("moved into released", _kinds(_run([base, before, moved], tags)) == [(WRONG_VERSION, "F1")])
    # 9. Left behind by a tagged cut, then repaired into the released section.
    left = clean.replace("- **F1** a fix.", "").replace("## [Unreleased]\n", "## [Unreleased]\n\n### Fixed\n\n- **F1** a fix.\n", 1)
    left_out = _run([base, before, left], {**tags, "1.1.0": "c2"})
    check("left out of the cut", _kinds(left_out) == [(WRONG_VERSION, "F1")])
    check("left out: blamed on the cut, not the PR that filed it", [f.by for f in left_out.open] == ["c2"])
    moved_back = _run([base, before, clean, left], {**tags, "1.1.0": "c2"})
    check("moved back after the cut: blamed on the commit that moved it", [(f.kind, f.by) for f in moved_back.open] == [(WRONG_VERSION, "c3")])
    check("left out, then repaired", not _run([base, before, left, clean], {**tags, "1.1.0": "c2"}).open)
    # 9b. The bfdfb3bb shape, walked from the tag: a bullet the tagged start "s" left in [Unreleased] is moved into
    #     [1.0.0] by c1. Its origin is the start, not c1's parent "t" (a later commit that did not touch the file).
    text0 = _doc(_lines("## [Unreleased]", "", "### Fixed", "", "- **X1** left out of the cut."), "", r100)
    text1 = _doc("## [Unreleased]", "", r100 + "\n- **X1** left out of the cut.")
    text2 = _doc("## [Unreleased]", "", _lines("## [1.1.0] - 2026-02-01", "", "### Added", "", "- **N1** new."), "", r100 + "\n- **X1** left out of the cut.")
    gap = [Step("c1", "c1", "t", "repair", text0, text1), Step("c2", "c2", "c1", "cut", text1, text2)]
    gap_releases = FakeReleases(["s", "t", "c1", "c2"], {"1.0.0": "s", "1.1.0": "c2"})
    check("repair walked from the tag: nothing", not walk(gap, gap_releases, "c2", start="s").findings)
    # 10. Text added to a released bullet (a sub-bullet, or words on its last line); a reword, a reflow, a reword that
    #     also rewraps, or text added to an [Unreleased] bullet is not; text added and later removed is not open;
    #     --accept records a ruling.
    grown = before.replace("- **R1** released fix.", "- **R1** released fix.\n  - **P4** the PR's own fix, which its merge put inside a released bullet.")
    check("text added under released", _kinds(_run([base, before, grown], tags)) == [(TEXT_ADDED, "R1")])
    same_line = before.replace("- **R1** released fix.", "- **R1** released fix. Also **P4**: the PR's own fix (#2360).")
    check("text appended on the same line", _kinds(_run([base, before, same_line], tags)) == [(TEXT_ADDED, "R1")])
    check("added, then removed: nothing open", not _run([base, before, grown, before], tags).open)
    rewritten = before.replace("- **R1** released fix.", "- **R1** a released fix the PR rewrote,\n  - **P4** and filled with its own fix.")
    check("a released bullet rewritten past the edit ratio: still reported", _kinds(_run([base, before, rewritten], tags)) == [(WRONG_VERSION, "R1")])
    check("reword under released: nothing", not _run([base, before, before.replace("**R1** released fix.", "**R1** released fix, reworded.")], tags).findings)
    long_text = "- **R1** a released fix whose description runs long enough to reflow onto a second line."
    base_long, before_long = base.replace("- **R1** released fix.", long_text), before.replace("- **R1** released fix.", long_text)
    reflowed = before_long.replace("to reflow onto a second line.", "to reflow\n  onto a second line.")
    check("reflowed released bullet: nothing", not _run([base_long, before_long, reflowed], tags).findings)
    rewrapped = before_long.replace("whose description runs long enough to reflow onto a second line.", "whose text runs long enough\n  to wrap onto another line.")
    check("reword that rewraps: nothing", not _run([base_long, before_long, rewrapped], tags).findings)
    unreleased_grown = before.replace("- **F1** a fix.", "- **F1** a fix.\n  - with a sub-bullet its own PR added later on.")
    check("text added to an [Unreleased] bullet: nothing", not _run([base, before, unreleased_grown], tags).findings)
    accepted = _run([base, before, grown], tags, accept=frozenset({"c2"}))
    check("accepted: nothing open", not accepted.open and len(accepted.findings) == 1)
    # 10b. --merge: a later, unjudged step that moves another bullet into a released version is not judged.
    later_move = deliberate.replace("- **A2** second added,\n  with a continuation line.\n", "").replace("- **R1** released fix.", "- **R1** released fix.\n- **A2** second added,\n  with a continuation line.")
    check("unjudged later move: only the merge's finding", _kinds(_run([before, deliberate, later_move], {"1.0.0": "t0"}, seeds=[True, False])) == [(RECATEGORIZED, "F1")])
    # 10b'. A version whose own tag is off this history counts as released once a later version's tag is in it.
    off = _doc("## [Unreleased]", "", _lines("## [1.1.0] - 2026-02-01", "", "### Added", "", "- **N1** new."), "", r100)
    check("off-history tag: released by a later one", _kinds(_run([off, off.replace("- **R1** released fix.", "- **R1** released fix.\n- **L1** filed late.")], {"1.1.0": "base"})) == [(WRONG_VERSION, "L1")])
    # 10b''. A link footer after the oldest bullet is not that bullet's text.
    footer = _doc("## [Unreleased]", "", r100, "", "[1.0.0]: https://example.invalid/compare/v0.9.0...v1.0.0")
    check("link footer: nothing", not _run([footer, footer + "[1.1.0]: https://example.invalid/compare/v1.0.0...v1.1.0\n[1.2.0]: https://example.invalid/compare/v1.1.0...v1.2.0\n"], tags).findings)
    # 10c. Version labels compare without case; a bullet above every version heading belongs to none.
    check("label case: nothing", not _run([_doc("## [Unreleased]", "", r100.replace("1.0.0", "1.0.0-RC1")), _doc("## [Unreleased]", "", r100.replace("1.0.0", "1.0.0-rc1"))], {"1.0.0-rc1": "base"}).findings)
    check("[Unreleased] heading deleted", _kinds(_run([base, before, before.replace("## [Unreleased]\n", "")], tags)) == [(WRONG_VERSION, "A1"), (WRONG_VERSION, "A2"), (WRONG_VERSION, "F1")])
    # 10d. Version order is PEP 440's: a pre-release before its final release.
    order = ["0.1.0.dev1", "0.1.0a0", "0.1.0a1", "0.1.0b2", "0.1.0rc1", "0.1.0", "0.1.0.post1", "0.1.1a", "0.1.1", "0.2", "0.10.0"]
    check("version order", sorted(reversed(order), key=version_key) == order and version_key("0.2") == version_key("0.2.0"))
    pre = _doc("## [Unreleased]", "", _lines("## [0.1.1a] - 2026-01-01", "", "### Added", "", "- **Q1** alpha."))
    check("a pre-release tag is its own release", not _run([_doc("## [Unreleased]"), pre, pre.replace("## [Unreleased]", "## [Unreleased]\n\n## [0.1.1] - 2026-02-01\n\n### Added\n\n- **Q2** final.")], {"0.1.1a": "c1", "0.1.1": "c2"}).findings)
    # 10e. Equal versions spelled two ways are one version; a later pre-release does not release an earlier version.
    check("[1.1] is tag 1.1.0", not _run([_doc("## [Unreleased]", "", _lines("## [1.1] - 2026-02-01", "", "### Added", "", "- **S1** short.")), _doc("## [Unreleased]", "", _lines("## [1.1] - 2026-02-01", "", "### Added", "", "- **S1** short.", "- **S2** another."))], {"1.1.0": "c1"}).findings)
    check("[1.1.0-rc1] is tag 1.1.0rc1", vid_of("1.1.0-rc1") == vid_of("1.1.0rc1") == "1.1.0rc1" and vid_of("0.1.1a") == "0.1.1a0" and vid_of("v1.1") == "1.1.0" and vid_of("0.11.4") == "0.11.4")
    pending_110 = _doc("## [Unreleased]", "", _lines("## [1.1.0] - 2026-02-01", "", "### Added", "", "- **T1** pending."), "", r100)
    check("a later pre-release does not release [1.1.0]", not _run([pending_110, pending_110.replace("- **T1** pending.", "- **T1** pending.\n- **T2** also pending.")], {"1.0.0": "t0", "1.2.0a1": "base"}).findings)
    # 10e'. A pre-release's notes are a preview: a bullet it shipped may sit under the final release or under it.
    u_a1 = _doc(_lines("## [Unreleased]", "", "### Added", "", "- **A1** first added."), "", r100)
    rc_cut = _doc(_lines("## [Unreleased]", "", "### Added", "", "- **A1** first added."), "", _lines("## [1.1.0rc1] - 2026-02-01", "", "### Added", "", "- **B1** in the rc."), "", r100)
    final_cut = _doc("## [Unreleased]", "", _lines("## [1.1.0] - 2026-03-01", "", "### Added", "", "- **A1** first added."), "", _lines("## [1.1.0rc1] - 2026-02-01", "", "### Added", "", "- **B1** in the rc."), "", r100)
    check("rc tagged, final [1.1.0] untagged: nothing", not _run([u_a1, rc_cut, final_cut], {"1.0.0": "t0", "1.1.0rc1": "c1"}).findings)
    check("rc and final tagged: nothing", not _run([u_a1, rc_cut, final_cut], {"1.0.0": "t0", "1.1.0rc1": "c1", "1.1.0": "c2"}).findings)
    to_pending = _doc("## [Unreleased]", "", _lines("## [1.1.0] - 2026-03-01", "", "### Added", "", "- **A1** first added."), "", r100)
    check("a later pre-release, a baseline bullet under the pending [1.1.0]: nothing", not _run([u_a1, to_pending], {"1.0.0": "t0", "1.2.0a1": "c1"}).findings)
    preamble = "\n".join(["# Changelog", "", "Categories used here:", "", "- Added for new features.", "", u_a1])
    check("a preamble list item added: nothing", not _run([preamble, preamble.replace("- Added for new features.", "- Added for new features.\n- Security for vulnerabilities.")], {"1.0.0": "t0"}).findings)
    # 10f. TEXT ADDED: a net-zero edit cannot hide an insertion, and words a later commit inserts are its own finding.
    long_r = "- **R1** a released fix with enough words in it to delete a few of them from the middle later on, as a real entry runs on: it names the files it changed, the test that pins it, the ruling behind it and the release that first carried it."
    base_l, before_l = base.replace("- **R1** released fix.", long_r), before.replace("- **R1** released fix.", long_r)
    netzero = before_l.replace("with enough words in it to delete", "with").replace("first carried it.", "first carried it, plus the PR's own eight extra words here.")
    check("insertion with deletions elsewhere", _kinds(_run([base_l, before_l, netzero], tags)) == [(TEXT_ADDED, "R1")])
    reworded5 = before_l.replace("names the files it changed, the test", "lists every file it touched, each test")
    check("a same-length reword of five words: nothing", not _run([base_l, before_l, reworded5], tags).findings)
    first = before_l.replace("first carried it.", "first carried it, and six words from c2.")
    second = first.replace("from c2.", "from c2. A dated correction by c3 follows.")
    third = second.replace(", and six words from c2.", ".")
    later = _run([base_l, before_l, first, second, third], tags, accept=frozenset({"c3"}))
    check("a later insertion is not the earlier one's", not later.open and [(f.kind, f.by) for f in later.findings] == [(TEXT_ADDED, "c3")])
    # 10g. A closing comment after the oldest bullet is not that bullet's text; a "[Note]: …" line inside one is.
    check("closing comment: nothing", not _run([footer, footer + "\n<!-- markdownlint-disable-file MD024 MD036 MD013 -->\n"], tags).findings)
    tight = _doc("## [Unreleased]", "", r100 + "\n[1.0.0]: https://example.invalid/compare/v0.9.0...v1.0.0")
    check("link definitions right under a bullet: nothing", not _run([tight, tight + "[1.1.0]: https://example.invalid/compare/v1.0.0...v1.1.0\n[1.2.0]: <https://example.invalid/compare/v1.1.0...v1.2.0> \"1.2.0\"\n"], tags).findings)
    noted = footer.replace("- **R1** released fix.", "- **R1** released fix.\n  [Note]: also fixes the TMPDIR fallback for every isolated stack (#2360).")
    check("a [Note]: line inside a released bullet", _kinds(_run([footer, noted], tags)) == [(TEXT_ADDED, "R1")])
    _git_self_test(check)
    # 11. Bullets left under no category heading, a renamed [Unreleased], and a second [Unreleased] below the releases.
    check("no category", _kinds(_run([base, before, before.replace("### Added\n\n- **A1**", "- **A1**")], tags)) == [(RECATEGORIZED, "A1"), (RECATEGORIZED, "A2")])
    check("[Unreleased] renamed [Next]", _kinds(_run([base, before, before.replace("## [Unreleased]", "## [Next]")], tags)) == [(WRONG_VERSION, "A1"), (WRONG_VERSION, "A2"), (WRONG_VERSION, "F1")])
    second = before.replace("- **F1** a fix.", "") + "\n## [Unreleased]\n\n### Fixed\n\n- **F1** a fix.\n"
    check("second [Unreleased]", _kinds(_run([base, before, second], tags)) == [(WRONG_VERSION, "F1")])
    # 12. Equal texts in two versions are paired at their own places; a short bullet's edit is an edit.
    same = _lines("## [1.0.0] - 2026-01-01", "", "### Fixed", "", "- **R1** released fix.", "- Dependency updates.")
    check("equal texts: nothing", not _run([_doc("## [Unreleased]", "", same), _doc(_lines("## [Unreleased]", "", "### Fixed", "", "- Dependency updates."), "", same)], tags).findings)
    # 12b. A bullet still in [Unreleased] at the tagged start of the walk was left out of that release.
    check("left out before the walk", _kinds(_run([_doc(unreleased, "", same), _doc(unreleased, "", same).replace("- **F1** a fix.", "- **F1** a fix.\n- **N1** new.")], tags)) == [(WRONG_VERSION, "A1"), (WRONG_VERSION, "A2"), (WRONG_VERSION, "F1")])
    check("short edit: nothing", not _run([base, before, before.replace("**A1** first added.", "**A1** first added (#12).")], tags).findings)
    # 13. Version headings, and parity with the release train's bullet split.
    check("label: unreleased", version_label("## [Unreleased]") == UNRELEASED and version_label("## unreleased") == UNRELEASED)
    check("label: dated", version_label("## [0.11.4] - 2026-11-06") == "0.11.4")
    check("label: blank", version_label("## ") == "(blank)" and version_label("### Added") is None and version_label("##[1.0.0]") is None)
    body = [(i, line) for i, line in enumerate(["- one", "  more of one", "* two", "  - nested", "", "prose", "---", "-", "- three"], start=1)]
    check("bullets: first lines", [number for number, _ in bullets_with_lines(body)] == [1, 3, 9])
    real_split = notes_render._split_bullets
    notes_render._split_bullets = lambda lines: []
    try:
        bullets_with_lines(body)
        refused = False
    except RuntimeError:
        refused = True
    finally:
        notes_render._split_bullets = real_split
    check("bullets: a disagreeing split is refused", refused)
    try:
        walk([Step("x", "x", "base", "s", "a", "b"), Step("y", "y", "x", "s", "c", "d")], FakeReleases(["base", "x", "y"], {}), "y")
        contiguous_refused = False
    except RuntimeError:
        contiguous_refused = True
    check("a walk with a gap is refused", contiguous_refused)

    for name in failures:
        print(f"FAIL {name}")
    if not failures:
        print("self-test: every check passed")
    return 1 if failures else 0


def _default_prefix(path: str) -> str:
    parent = Path(path).parent.as_posix()
    return "v" if parent in ("", ".") else f"{Path(path).parent.name}-v"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0].strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", help="walk every first-parent commit that changed PATH after this one (e.g. the previous release tag)")
    ap.add_argument("--merge", help="judge only the bullets this commit added or moved, then follow them to --at")
    ap.add_argument("--at", default="HEAD", help="the commit the bullets are judged at (default HEAD)")
    ap.add_argument("--path", default="CHANGELOG.md", help="the CHANGELOG, relative to the repository root")
    ap.add_argument("--tag-prefix", help='release tags are PREFIX<version> (default "v" for CHANGELOG.md, "<dir>-v" for <dir>/CHANGELOG.md)')
    ap.add_argument("--accept", action="append", default=[], metavar="COMMIT", help="a commit whose changes a person ruled deliberate (repeatable)")
    ap.add_argument("--ignore-tag", action="append", default=[], metavar="VERSION", help="a version whose tag never shipped, e.g. a retired release (repeatable)")
    ap.add_argument("--repo", type=Path, default=_REPO, help="the git repository (default: this script's)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if (args.since is None) == (args.merge is None):
        ap.error("give exactly one of --since and --merge")
    prefix = args.tag_prefix if args.tag_prefix is not None else _default_prefix(args.path)
    try:
        steps = build_steps(args.repo, args.path, args.at, args.since, args.merge)
        at = git(args.repo, "rev-parse", "--verify", f"{args.at}^{{commit}}").strip()
        start = git(args.repo, "rev-parse", "--verify", f"{args.since}^{{commit}}" if args.since is not None else f"{args.merge}^").strip()
        releases = GitReleases(args.repo, prefix, frozenset(vid_of(v) for v in args.ignore_tag))
        accept = frozenset(git(args.repo, "rev-parse", "--verify", f"{c}^{{commit}}").strip()[:8] for c in args.accept)
        parsed_at = parse(read_at(args.repo, at, args.path))
        merged = releases.merged(at)
    except GitError as exc:
        print(f"ERROR: {exc}")
        return 2
    headings = parsed_at.versions
    if not releases.tags:
        print(f"WARNING: no tag matches {prefix!r}*; no version counts as released, so only categories are judged soundly. Pass --tag-prefix.")
    for vid in sorted(merged - set(headings), key=version_key):
        written = releases.labels.get(vid, vid)
        print(f"WARNING: tag {prefix}{written} is in the history of --at, but the file has no [{written}] heading. If that release never shipped, pass --ignore-tag {written}.")
    untagged = [v for v in headings if looks_like_version(v) and "#" not in v and v not in releases.tags]
    pending = [v for v in untagged if not releases.released(v, at)]
    implied = [v for v in untagged if releases.released(v, at)]
    if pending:
        print(f"WARNING: no local tag for {', '.join(f'[{parsed_at.labels.get(v, v)}]' for v in pending)}; treated as not yet released. If one was released, fetch its tag (git fetch --tags).")
    if implied:
        print(f"WARNING: no local tag for {', '.join(f'[{parsed_at.labels.get(v, v)}]' for v in implied)}; treated as released, since a later final release is tagged. If one never shipped, its bullets read as filed under a release.")
    print(f"{len(steps)} commit(s) changed {args.path}; {len(releases.tags)} release tag(s) {prefix}*; {'every one' if args.merge is None else 'only ' + steps[0].label} is judged.\n")
    return report(walk(steps, releases, at, accept, start), f"{at[:8]} ({args.at})")


if __name__ == "__main__":
    raise SystemExit(main())
