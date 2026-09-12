#!/usr/bin/env python3
"""One-shot edit: teach util/safe_merge.py to see a foreign stale auto-merge snapshot.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-11

Applies two changes, both established by independent consensus 2026-09-11:

1. `pr_state` also fetches `autoMergeRequest` -- one more field on a call already made,
   and the only way to see a net armed by something other than this tool.
2. `stale_snapshot_refusal` classifies the stored `commitBody` and refuses on the
   destructive states, without ever mutating foreign auto-merge state.

Idempotent; refuses on a drifted anchor rather than clobbering.
"""

from __future__ import annotations

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().parents[3] / "util" / "safe_merge.py"

OLD_FIELDS = '            "state,mergeStateStatus,mergeable,headRefOid,isDraft,title",'
NEW_FIELDS = (
    "            # `autoMergeRequest` costs nothing here -- one more field on a call already\n"
    "            # being made -- and it is the only way to see a net someone ELSE armed. See\n"
    "            # `stale_snapshot_refusal` for why that matters.\n"
    '            "state,mergeStateStatus,mergeable,headRefOid,isDraft,title,autoMergeRequest",'
)

OLD_ARMABLE = 'ARMABLE_STATES = ("BLOCKED", "BEHIND", "UNKNOWN")'

NEW_ARMABLE = '''ARMABLE_STATES = ("BLOCKED", "BEHIND", "UNKNOWN")


def stale_snapshot_refusal(info: dict) -> "str | None":
    """Why this PR must not be merged through a net that carries a stored body.

    Returns a refusal reason, or None when the PR is safe to proceed with.

    THE HAZARD IS NOT THIS TOOL. Established 2026-09-11 by independent consensus over
    1877 PRs: ``gh pr merge --auto --<method>`` with no body flags OMITS ``commitBody``,
    so GitHub stores ``null`` -- and a history search for ``--body-file`` in this file
    returns no commits, in any version. This module has never supplied one. The one
    incident (ml#1228) was armed by something else, 5m42s AFTER this tool's own disarm.

    ``commitBody`` has THREE states and only one is safe:

    * ``null``  -- omitted. The repo's ``squash_merge_commit_message`` (COMMIT_MESSAGES on
      all nine repos) is resolved at MERGE time, so commits pushed after arming are still
      included. Measured: 60 post-arm commits across 48 PRs, ZERO losses, lags to 40.7h.
    * ``""``    -- an actual empty string, and NOT the same as null: the squash lands with
      no body at all. Eight cases here, all bodyless at source so none lost anything --
      but the state is real, and ``length`` cannot tell it from null. That indistinguish-
      ability is what produced the superseded diagnosis this function replaces.
    * non-empty -- an ARM-TIME SNAPSHOT that binds when the net fires. Of the 29 PRs where
      a single-parent commit landed AFTER the arm, 23 lost that commit's body from the
      squash message. ml#1228 lost an ``Allow-Symbol-Loss:`` waiver that way and
      ``Post-Merge Main Verification`` failed on the landed SHA three seconds later;
      ml#1877 silently lost nine commit messages.

    WHY REFUSE RATHER THAN REPAIR. The obvious remedy -- disarm, then re-arm with no body
    -- is not available to a merge GATE. ``--auto`` on a mergeable PR merges ON THE SPOT
    (see ``arm_auto_merge``), so a repair attempt can land a PR whose required checks never
    finished: ml#932 / ml#924, the exact failure this tool exists to prevent. That is not
    hypothetical -- the same disarm/re-arm sequence merged three sibling PRs on the spot on
    2026-09-11. It also cannot fail safe: if the disarm succeeds and the re-arm's
    ``--match-head-commit`` then fails -- which happens precisely when the head has moved,
    the common case -- the PR is left with NO net at all. So this reports and refuses; the
    operator decides.

    NOT A BLANKET BAN ON STORED BODIES. A body supplied AFTER the last commit is correct,
    and is the only way to guarantee a waiver trailer's exact text: twelve PRs here carry a
    deliberately curated message, and the alternative on a large PR is ml#1797's
    26,052-character auto-concatenation. The hazard is a body stored BEFORE further commits
    land. This therefore refuses only on the empty string, which is destructive
    unconditionally; staleness of a non-empty snapshot depends on commits this function
    cannot see, and is measured by
    ``util/ad-hoc/2026-09-10_soak_stopping_rule/armed_snapshot_staleness.py``.
    """
    amr = info.get("autoMergeRequest")
    if not amr:
        return None
    body = amr.get("commitBody")
    if body is None:
        return None  # the safe state: resolved at merge time
    if body == "":
        return (
            "an auto-merge net is armed with an EMPTY commit body. That is NOT the same "
            "as no body: it overrides the repository's COMMIT_MESSAGES default, so the "
            "squash lands with no body at all -- every trailer included. Disarm it and "
            "re-arm with no body flags, or merge deliberately."
        )
    return None'''


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    if "stale_snapshot_refusal" in src:
        print("already applied")
        return 0
    for name, old in (("pr_state fields", OLD_FIELDS), ("ARMABLE_STATES", OLD_ARMABLE)):
        if src.count(old) != 1:
            print(f"REFUSING: anchor {name!r} found {src.count(old)} times (expected 1)",
                  file=sys.stderr)
            return 1
    src = src.replace(OLD_FIELDS, NEW_FIELDS).replace(OLD_ARMABLE, NEW_ARMABLE)
    TARGET.write_text(src, encoding="utf-8")
    print(f"applied to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
