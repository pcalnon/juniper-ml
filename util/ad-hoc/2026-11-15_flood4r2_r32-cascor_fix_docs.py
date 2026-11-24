#!/usr/bin/env python3
"""
Build the r32 pause FIX carrier's three documents on top of whatever main holds, in one command.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — one-off (Cursor flood-4 round 2: the Overtoad's ruling of 2026-11-13, "Fix it + document")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#764 (the document carrier: the "Known, not fixed" entry this rewrites as fixed)
Updated: 2026-11-16 -- the texts follow the Overtoad's rulings of 2026-11-16 (a pause is refused while the run that
         owns the lifecycle has its stop raised; a resume that loses its race answers 409) and carry the claims
         lens's fixes T6b and T7d; one API_SCHEMAS.md sentence and the two POST /v1/training/resume edits added.

Reads ``docs/api/API_SCHEMAS.md``, ``CHANGELOG.md`` and ``docs/api/JUNIPER_CASCOR_API_REFERENCE.md`` from
``--main-tree`` (a checkout of main as it is at the freeze, or the document carrier's head before it
merges), applies the fix carrier's edits, and writes the three files into ``--out-tree``:

- API_SCHEMAS.md: the document carrier's "Known, not fixed: a `pause` that overlaps ..." bullet is
  replaced by the fixed bullet; when main does not carry it (the document carrier never landed), the
  fixed bullet goes directly after the first "Known, not fixed" bullet's sub-list instead. One sentence
  of the "A normal return" bullet (a pause or resume racing the settle) is rewritten. The stamp becomes
  main's version + 0.0.1 and ``--date``, header and footer alike. Run against a main that another
  carrier has already stamped, it bumps from that stamp (a plain ``git merge-file`` would keep this
  carrier's old stamp and print one version twice).
- CHANGELOG.md: under the TOP ``## [Unreleased]``, the document carrier's ``### Documentation`` entry is
  removed (and the group heading, if nothing else is left under it), and the fix's entry is appended
  as the last entry of that section's ``### Fixed`` group.
- the API reference: three sentences of ``POST /v1/training/pause`` and two of
  ``POST /v1/training/resume``, anchored by exact text.

Every anchor must match exactly once or the script stops without writing anything.

Usage:
  2026-11-15_flood4r2_r32-cascor_fix_docs.py --main-tree <dir> --out-tree <fix worktree> --date YYYY-MM-DD
Exit: 0 when all three files were written; 1 when an anchor did not match (nothing is written).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCHEMAS = Path("docs/api/API_SCHEMAS.md")
CHANGELOG = Path("CHANGELOG.md")
REFERENCE = Path("docs/api/JUNIPER_CASCOR_API_REFERENCE.md")

DOC_ENTRY_LEAD = "- **Known, not fixed: a `pause` that overlaps a `stop` and a `start` can hold the new run at its first checkpoint.**"
FIRST_KNOWN_LAST_SUB = "  - A fit that reaches no further checkpoint and does not return keeps the single training worker:"
DOC_CHANGELOG_LEAD = "- **`docs/api/API_SCHEMAS.md` lists a `pause` that overlaps a `stop` and a `start` as known, not fixed.**"

FIXED_ENTRY = (
    "- **A `pause` holds only the run it was accepted for, and a `pause` or `resume` that loses its race is refused.** `pause_training` makes its check, its transition and its close of the pause gate one step under a lock of the gate's own, which `resume_training` also takes, and which a `start` or a live swap takes to reopen the gate before it submits its run; a `stop`, a `reset` and a run's settle do not take it. "
    "A `pause` whose transition is refused, because a `stop`, a `reset` or the run's own settle moved `state_machine.status` after the check, reopens the gate and answers `409`, as a `pause` sent a moment later does. "
    "A `pause` is also refused (`409`) while the run that owns the lifecycle has its stop raised, as one sent after a `stop` is: after a live swap has stopped the old fit, `state_machine.status` reads `STARTED` for that fit until it settles, and the swapped run, queued behind it once the swap's join on it has timed out, trains on. "
    "A `resume` whose transition is refused, because a `stop`, a `reset` or the paused run's own settle moved `state_machine.status` off `PAUSED` after its check, answers `409` and writes nothing. "
    "Every settle a run owns reopens the gate after its transition, so a pause ends with the run it held. "
    "In juniper-cascor 0.14.0 a `pause` whose check passed just before a `stop` and a `start` landed closed the gate the `start` had reopened and still reported success (`/ws/control` acknowledged it with `status` `success` and `paused`), with `state_machine.status` `STOPPED` beside `training_state.status` `Paused`; the new run was then held at its first checkpoint with `state_machine.status` `STARTED`, `training_state.status` `Started` and `training_active` `true`, `resume` and `start` answered `409`, a `pause` then a `resume` freed it, and a `stop` or a `reset` ended it there. "
    "After a live swap whose join on the old fit timed out, a `pause` sent while that fit still ran, over REST too, was accepted for it, and once it stopped the swapped run was held the same way (`resume` answered `409`; a `pause` then a `resume` freed it). "
    "A `resume` that lost its race answered `200` and left `training_state.status` `Started` beside `STOPPED` or `COMPLETED`."
)

CHANGELOG_ENTRY = """- **A pause holds only the run it was accepted for, and a pause or resume that loses its race is refused.** Two
  routes left the pause gate closed under a run the pause was never meant for, and that run was held at its first
  checkpoint while `state_machine.status` read `STARTED`: `resume` and `start` answered `409`, and only a `pause` then
  a `resume` freed it.
  - `pause_training` checked the FSM, then closed the gate, then issued PAUSE and ignored its answer, with no lock. A
    `stop` and a `start` landing between its check and its close left the gate closed after the `start` had reopened
    it, and the `pause` still answered `paused`. Over REST alone the three cannot overlap, because the routes run the
    lifecycle on the event loop; a `pause` sent over `/ws/control`, which runs each command on a worker thread, can.
    Now the check, the transition and the gate write are one step under `_pause_lock`, which `resume_training` and
    the gate open before a `start`'s or a live swap's submit also take, and a `pause` whose transition is refused
    reopens the gate and is refused.
  - Only the completion settle reopened the gate. After a live swap whose join on the old fit timed out, the FSM still
    read `STARTED`, so a `pause` sent then, over REST too, was accepted for the old fit, and once that fit stopped the
    closed gate held the swapped run. Now a `pause` is refused while the run that owns the lifecycle has its stop
    raised, and the stop, interrupted and failure settles reopen the gate too, after their transition and inside
    their ownership check.
  - Three answers change from `200` to `409`:
    - a `pause` whose FSM check passed but whose transition a `stop`, a `reset` or the run's own settle beat answers
      `409` "Training cannot be paused in the current state" (on `/ws/control` an `error` ack, "Command execution failed"),
      as one sent a moment later does; it answered `200` `paused`, with nothing paused;
    - a `pause` sent after a live swap has stopped the old fit and before that fit settles (over REST, after a swap
      whose join on the old fit timed out; over `/ws/control`, also while the swap joins it) answers the same `409`, as
      one sent after a `stop` does, and the swapped run trains on; it answered `200` `paused`, and after a timed-out
      join the swapped run was then held at its first checkpoint;
    - a `resume` whose FSM check passed but whose transition a `stop`, a `reset` or the paused run's own settle beat
      answers `409` "Training cannot be resumed in the current state" (on `/ws/control` an `error` ack,
      "Command execution failed") and writes nothing; it answered `200` `resumed` and left `training_state.status`
      `Started` beside `STOPPED` or `COMPLETED`.
DOCS_BULLET"""
DOCS_BULLET_REPLACED = """  - `docs/api/API_SCHEMAS.md` (STAMP_VERSION) describes the fixed behaviour in place of the "Known, not fixed" entry
    that listed it, and `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`'s `POST /v1/training/pause` and
    `POST /v1/training/resume` say what a refused `pause` or `resume` answers. The new
    `src/tests/unit/api/test_lifecycle_pause_check_then_act.py` (29 tests) pins both routes and the three answers: 25
    of them fail on the code before this change, and four guards pass on it.
"""
DOCS_BULLET_ADDED = """  - `docs/api/API_SCHEMAS.md` (STAMP_VERSION) describes the fixed behaviour, and
    `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`'s `POST /v1/training/pause` and `POST /v1/training/resume` say what a
    refused `pause` or `resume` answers. The new `src/tests/unit/api/test_lifecycle_pause_check_then_act.py` (29
    tests) pins both routes and the three answers: 25 of them fail on the code before this change, and four guards
    pass on it.
"""

SCHEMAS_EDITS = (
    (
        "it lands before the transition and is settled with the run, or finds `COMPLETED`. Its own answer can still be `200` with `training_state.status` out of step until the next `start` (see `POST /v1/training/pause`).",
        "it lands before the transition and is settled with the run, or finds `COMPLETED` and is refused (`409`). One whose transition landed just before the settle's still answers `200` and can leave `training_state.status` out of step until the next `start` (see `POST /v1/training/pause`).",
    ),
)

REFERENCE_EDITS = (
    (
        "Metrics history is preserved.\n\nA pause that lands after the fit's last checkpoint cannot hold it.",
        "Metrics history is preserved. The `pause` acts only for the run it found `STARTED`: its check, its transition and its close of the gate are one step under a lock that a `start`, a `resume` and a live swap also take, and when a `stop`, a `reset` or the run's own settle, which do not take it, moves the FSM between its check and its transition, it reopens the gate and answers `409`. "
        "It is also refused (`409`) while the run that owns the lifecycle has its stop raised, as one sent after a `stop` is: after a live swap has stopped the old fit, `state_machine.status` reads `STARTED` for that fit until it settles, and the swapped run, queued behind it once the swap's join on it has timed out, trains on.\n\nA pause that lands after the fit's last checkpoint cannot hold it.",
    ),
    (
        "One whose check passed just before the settle can still answer `200`",
        "One whose transition landed just before the settle's can still answer `200`",
    ),
    (
        "**Error handling** — `409` if not currently `STARTED` (`error.message`: `Training cannot be paused in the current state`); `503` if lifecycle unbound.",
        '**Error handling** — `409` if not currently `STARTED` (`error.message`: `Training cannot be paused in the current state`; on `/ws/control` an `error` ack, "Command execution failed"). '
        "The `409` also answers two `pause`s that juniper-cascor 0.14.0 answered `200` `paused`: one whose transition a `stop`, a `reset` or the run's own settle beat after its check (0.14.0 could then hold the next run at its first checkpoint), and one sent after a live swap has stopped the old fit and before that fit settles, which over REST means after a swap whose join on the old fit timed out (0.14.0 accepted it for the old fit and, once that fit stopped, held the swapped run at its first checkpoint; see [`API_SCHEMAS.md`](API_SCHEMAS.md#training-failure-propagation-and-ownership)). `503` if lifecycle unbound.",
    ),
    (
        "the training thread continues from the checkpoint it waited at. A `resume` whose check passed just before a paused run's returned fit settled can still answer `200`",
        "the training thread continues from the checkpoint it waited at. The `resume`'s check, its transition and its open of the gate are one step under the lock the `pause` takes. When a `stop`, a `reset` or the paused run's own settle, which do not take it, moves the FSM off `PAUSED` between its check and its transition, the `resume` answers `409` and writes nothing. One whose transition landed just before a paused run's returned fit settled can still answer `200`",
    ),
    (
        "**Error handling** — `409` if not currently `PAUSED` (`error.message`: `Training cannot be resumed in the current state`), including after a paused run whose fit had already returned has settled `COMPLETED` (see `POST /v1/training/pause` above); `503` if lifecycle unbound.",
        '**Error handling** — `409` if not currently `PAUSED` (`error.message`: `Training cannot be resumed in the current state`; on `/ws/control` an `error` ack, "Command execution failed"), including after a paused run whose fit had already returned has settled `COMPLETED` (see `POST /v1/training/pause` above), and when a `stop`, a `reset` or that settle moves the FSM off `PAUSED` between the `resume`\'s check and its transition, a `resume` that juniper-cascor 0.14.0 answered `200` `resumed`, leaving `training_state.status` `Started` beside `STOPPED` or `COMPLETED`. `503` if lifecycle unbound.',
    ),
)


class AnchorError(Exception):
    """An anchor did not match exactly once."""


def _once(text: str, needle: str, what: str) -> int:
    count = text.count(needle)
    if count != 1:
        raise AnchorError(f"{what}: {count} matches for {needle[:80]!r}")
    return text.index(needle)


def _bump(version: str) -> str:
    major, minor, patch = (int(part) for part in version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def build_schemas(text: str, date: str) -> tuple:
    lines = text.split("\n")
    doc_rows = [i for i, line in enumerate(lines) if line.startswith(DOC_ENTRY_LEAD)]
    if len(doc_rows) > 1:
        raise AnchorError(f"API_SCHEMAS: {len(doc_rows)} document-carrier entries")
    if doc_rows:
        lines[doc_rows[0]] = FIXED_ENTRY
        replaced = True
    else:
        anchor = [i for i, line in enumerate(lines) if line.startswith(FIRST_KNOWN_LAST_SUB)]
        if len(anchor) != 1:
            raise AnchorError(f"API_SCHEMAS: {len(anchor)} matches for the first Known-not-fixed bullet's last sub-bullet")
        lines.insert(anchor[0] + 1, FIXED_ENTRY)
        replaced = False
    out = "\n".join(lines)
    for old, new in SCHEMAS_EDITS:
        _once(out, old, "API_SCHEMAS")
        out = out.replace(old, new, 1)
    header = re.search(r"^\*\*Version\*\*: (\d+\.\d+\.\d+)$", out, re.MULTILINE)
    footer = re.search(r"^\*\*Document Version\*\*: (\d+\.\d+\.\d+)$", out, re.MULTILINE)
    if header is None or footer is None or header.group(1) != footer.group(1):
        raise AnchorError("API_SCHEMAS: header and footer versions missing or unequal")
    version = _bump(header.group(1))
    out = re.sub(r"^\*\*Version\*\*: \d+\.\d+\.\d+$", f"**Version**: {version}", out, count=1, flags=re.MULTILINE)
    out = re.sub(r"^\*\*Document Version\*\*: \d+\.\d+\.\d+$", f"**Document Version**: {version}", out, count=1, flags=re.MULTILINE)
    out, dates = re.subn(r"^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}$", f"**Last Updated**: {date}", out, flags=re.MULTILINE)
    if dates != 2:
        raise AnchorError(f"API_SCHEMAS: {dates} Last Updated stamps, expected 2")
    return out, version, replaced


def build_changelog(text: str, version: str, replaced: bool) -> tuple:
    start = _once(text, "\n## [Unreleased]\n", "CHANGELOG [Unreleased]") + 1
    end = text.index("\n## [", start + 1) + 1
    section = text[start:end]
    removed_doc_entry = False
    if DOC_CHANGELOG_LEAD in section:
        lead = _once(section, DOC_CHANGELOG_LEAD, "CHANGELOG document-carrier entry")
        stop = section.find("\n- ", lead + 1)
        heading = section.find("\n### ", lead + 1)
        candidates = [pos for pos in (stop, heading) if pos != -1]
        entry_end = min(candidates) + 1 if candidates else len(section)
        section = section[:lead] + section[entry_end:]
        section = re.sub(r"### Documentation\n\n(?=### |\Z)", "", section)
        section = section.rstrip("\n") + "\n\n"
        removed_doc_entry = True
    fixed = _once(section, "\n### Fixed\n", "CHANGELOG ### Fixed under [Unreleased]") + 1
    next_heading = section.find("\n### ", fixed + 1)
    group_end = next_heading + 1 if next_heading != -1 else len(section)
    group = section[fixed:group_end].rstrip("\n") + "\n\n"
    bullet = DOCS_BULLET_REPLACED if replaced else DOCS_BULLET_ADDED
    entry = CHANGELOG_ENTRY.replace("DOCS_BULLET", bullet).replace("STAMP_VERSION", version)
    group += entry + "\n"
    section = section[:fixed] + group + section[group_end:]
    return text[:start] + section + text[end:], removed_doc_entry


def build_reference(text: str) -> str:
    for old, new in REFERENCE_EDITS:
        _once(text, old, "API reference")
        text = text.replace(old, new, 1)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--main-tree", required=True, type=Path)
    parser.add_argument("--out-tree", required=True, type=Path)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
        print("bad --date", file=sys.stderr)
        return 1
    try:
        schemas, version, replaced = build_schemas((args.main_tree / SCHEMAS).read_text(encoding="utf-8"), args.date)
        changelog, removed = build_changelog((args.main_tree / CHANGELOG).read_text(encoding="utf-8"), version, replaced)
        reference = build_reference((args.main_tree / REFERENCE).read_text(encoding="utf-8"))
    except AnchorError as exc:
        print(f"ANCHOR: {exc}; nothing written", file=sys.stderr)
        return 1
    (args.out_tree / SCHEMAS).write_text(schemas, encoding="utf-8")
    (args.out_tree / CHANGELOG).write_text(changelog, encoding="utf-8")
    (args.out_tree / REFERENCE).write_text(reference, encoding="utf-8")
    print(f"API_SCHEMAS.md stamp {version} ({args.date}); document-carrier entry {'replaced' if replaced else 'absent, fixed entry inserted'}; CHANGELOG document entry {'removed' if removed else 'absent'}; API reference: {len(REFERENCE_EDITS)} edits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
