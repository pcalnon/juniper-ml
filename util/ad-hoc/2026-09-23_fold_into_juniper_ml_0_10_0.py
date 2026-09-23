#!/usr/bin/env python3
"""Re-home five misfiled CHANGELOG bullets into juniper-ml's [0.10.0] before the release is cut.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-23
Version:     0.1.0
License:     MIT License
Status:      single-use (the juniper-ml 0.10.0 ceremony pre-flight)

Why this exists
---------------
The ceremony renders the Release body -- which cannot be re-cut -- from ``## [0.10.0]`` alone.
The tag it cuts carries every commit on ``main``. Two PRs in that window filed their bullets
where the 0.10.0 notes cannot see them:

* **juniper-ml#2002** merged at 09:44:48Z, 22 minutes AFTER ``v0.9.0`` was tagged, and its four
  bullets landed under the RELEASED ``## [0.9.0]``. It was authored against ``[Unreleased]``;
  #1997 then turned that slot into ``[0.9.0]``, and the squash merged into the released heading
  with no conflict. ``util/ad-hoc/2026-09-23_released_section_drift.py`` shows those four are the
  only ``[0.9.0]`` bullets absent from ``notes/releases/RELEASE_NOTES_v0.9.0.md`` (4 of 22). So the
  CHANGELOG claims 0.9.0 shipped D2 and D6, and the 0.10.0 notes would never mention them.
* **juniper-ml#2036** merged after the 0.10.0 bump (#2033) and filed under ``[Unreleased]``,
  correct normally and wrong here, because a Release tags the branch HEAD.

Both are the shapes recorded in ``notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md``
§11.7 (items 1 and 4). The fix moves each bullet verbatim; it rewrites no text.

Every anchor is asserted exactly, and post-conditions are checked BEFORE anything is written:
``[0.9.0]`` must then match the archived 0.9.0 notes bullet for bullet, no bullet may be lost or
duplicated, ``[Unreleased]`` must be empty, and every byte outside the three sections must be
unchanged.

Usage
-----
    python3 util/ad-hoc/2026-09-23_fold_into_juniper_ml_0_10_0.py [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "util" / "release_train"))  # the modules import each other top-level

import ceremony  # noqa: E402

_CHANGELOG = _REPO / "CHANGELOG.md"
_ARCHIVE_090 = _REPO / "notes" / "releases" / "RELEASE_NOTES_v0.9.0.md"

_H_UNRELEASED = "## [Unreleased]"
_H_0100 = "## [0.10.0] - 2026-09-23"
_H_090 = "## [0.9.0] - 2026-09-22"
_H_080 = "## [0.8.0] - 2026-09-11"

#: First-line prefixes of the bullets to move, with the category each belongs to in [0.10.0].
_FROM_UNRELEASED = [("Added", "- **`util/push_signed_commit.py` -- one GitHub-signed commit onto an EXISTING branch")]
_FROM_090 = [
    ("Added", "- **D2 implemented — the experiment `runtime:` block BINDS"),
    ("Added", "- **D6's gate discharged — `epochs_completed` has ZERO spread"),
    ("Added", "- **The measurement existed already, UNCOMMITTED, and three searches missed it.**"),
    ("Fixed", '- **The thread-width sweep\'s "initial pass" column is NOT the initial pass**'),
]
_CATEGORY_ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


def _index(lines: list, heading: str) -> int:
    hits = [i for i, line in enumerate(lines) if line == heading]
    if len(hits) != 1:
        raise SystemExit(f"ERROR: expected exactly one {heading!r}, found {len(hits)}")
    return hits[0]


def _bullet_span(lines: list, start: int, stop: int) -> tuple[int, int]:
    """[start, end) of the top-level bullet at ``start``: up to the next top-level bullet or heading."""
    end = start + 1
    while end < stop and not (lines[end].startswith("- ") or lines[end].startswith("#")):
        end += 1
    return start, end


def _take(lines: list, lo: int, hi: int, prefix: str) -> tuple[int, int]:
    hits = [i for i in range(lo, hi) if lines[i].startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit(f"ERROR: expected exactly one bullet starting {prefix[:60]!r} in lines {lo}-{hi}, found {len(hits)}")
    return _bullet_span(lines, hits[0], hi)


def _block(lines: list, span: tuple[int, int]) -> str:
    return "\n".join(lines[span[0] : span[1]]).rstrip("\n").rstrip()


def _bullets(text: str, version: str) -> list:
    sections = ceremony.changelog_version_section(text, version)
    return sorted(b for bullets in sections.values() for b in bullets)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    text = _CHANGELOG.read_text(encoding="utf-8")
    lines = text.split("\n")
    i_unr, i_new, i_090, i_080 = (_index(lines, h) for h in (_H_UNRELEASED, _H_0100, _H_090, _H_080))
    if not i_unr < i_new < i_090 < i_080:
        raise SystemExit("ERROR: section order is not [Unreleased] < [0.10.0] < [0.9.0] < [0.8.0]")

    moved: dict = {c: [] for c in _CATEGORY_ORDER}
    drop: list = []

    for category, prefix in _FROM_UNRELEASED:
        span = _take(lines, i_unr, i_new, prefix)
        moved[category].append(_block(lines, span))
    # [Unreleased] must hold exactly that one bullet under one heading; drop the whole body.
    body = [line for line in lines[i_unr + 1 : i_new] if line.strip()]
    if sum(1 for line in body if line.startswith("- ")) != 1 or sum(1 for line in body if line.startswith("### ")) != 1:
        raise SystemExit("ERROR: [Unreleased] does not hold exactly one heading and one bullet -- re-read it before folding")
    drop.append((i_unr + 1, i_new))

    for category, prefix in _FROM_090:
        span = _take(lines, i_090, i_080, prefix)
        moved[category].append(_block(lines, span))
        drop.append(span)

    # [0.10.0] as it stands: existing bullets per category, in file order.
    existing = ceremony.changelog_version_section(text, "0.10.0")
    for category, bullets in existing.items():
        if category not in moved:
            raise SystemExit(f"ERROR: unexpected [0.10.0] category {category!r}")
        moved[category].extend("- " + b for b in bullets)

    # Build the new [0.10.0] body. Moved bullets precede the existing ones within a category.
    new_body = [""]
    for category in _CATEGORY_ORDER:
        if moved[category]:
            new_body += [f"### {category}", ""]
            for block in moved[category]:
                new_body += block.split("\n") + [""]
    drop.append((i_new + 1, i_090))  # replace the old [0.10.0] body wholesale

    keep = [True] * len(lines)
    for lo, hi in drop:
        for k in range(lo, hi):
            keep[k] = False
    out: list = []
    for k, line in enumerate(lines):
        if k == i_unr:
            out += [line, ""]
            continue
        if k == i_new:
            out += [line] + new_body
            continue
        if keep[k]:
            out.append(line)
    result = "\n".join(out)

    # ── post-conditions, checked before any write ─────────────────────────────
    archive = _ARCHIVE_090.read_text(encoding="utf-8")
    left_in_090 = [b for bullets in ceremony.changelog_version_section(result, "0.9.0").values() for b in bullets]
    stray = [b.splitlines()[0][:80] for b in left_in_090 if b.splitlines()[0].strip() not in archive]
    if stray:
        raise SystemExit(f"ERROR: [0.9.0] still carries bullets its release did not: {stray}")
    before = sorted(_bullets(text, "0.10.0") + _bullets(text, "0.9.0") + [b for bs in ceremony.notes_render.parse_unreleased(text).values() for b in bs])
    after = sorted(_bullets(result, "0.10.0") + _bullets(result, "0.9.0") + [b for bs in ceremony.notes_render.parse_unreleased(result).values() for b in bs])
    if before != after:
        raise SystemExit(f"ERROR: bullet conservation failed ({len(before)} before, {len(after)} after)")
    if ceremony.notes_render.parse_unreleased(result):
        raise SystemExit("ERROR: [Unreleased] is not empty after the fold")
    n_new = sum(len(b) for b in ceremony.changelog_version_section(result, "0.10.0").values())
    if n_new != 6:
        raise SystemExit(f"ERROR: [0.10.0] should hold 6 bullets after the fold, holds {n_new}")
    if text.split(_H_UNRELEASED)[0] != result.split(_H_UNRELEASED)[0] or text[text.index(_H_080) :] != result[result.index(_H_080) :]:
        raise SystemExit("ERROR: bytes outside [Unreleased]..[0.9.0] changed")

    print(f"[Unreleased]: 1 bullet moved out; [0.9.0]: 4 moved out, {len(left_in_090)} left, all in RELEASE_NOTES_v0.9.0.md")
    print(f"[0.10.0]: {n_new} bullets -- " + ", ".join(f"{c} {len(v)}" for c, v in moved.items() if v))
    print(f"conservation: {len(before)} bullets before, {len(after)} after, identical")
    if args.check:
        print("--check: nothing written")
        return 1
    _CHANGELOG.write_text(result, encoding="utf-8")
    print(f"wrote {_CHANGELOG.relative_to(_REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
