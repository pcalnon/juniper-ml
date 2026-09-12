#!/usr/bin/env python3
"""One-shot edit 2/2: wire the refusal at entry, and make "net armed" a measurement.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-11

Two changes:

1. Call `stale_snapshot_refusal` UNCONDITIONALLY at entry, beside the other entry guards.
   Placement is load-bearing: the dry-run and BEHIND paths both `return` before the arming
   site, and a `CLEAN` PR is never armable at all, so a check placed at the arming site
   could not fire in the cheap read-only mode an operator actually runs, nor on a green PR
   whose foreign net is about to fire.

2. After arming, READ BACK what is actually stored. `gh pr merge --auto` against an
   ALREADY-armed PR exits 0 and prints nothing, so exit 0 proves nothing -- the tool could
   log "net armed pinned to <sha>" over a foreign net with a stale body that is what will
   really fire. Log what is there, not what was requested.

Idempotent; refuses on a drifted anchor.
"""

from __future__ import annotations

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().parents[3] / "util" / "safe_merge.py"

OLD_ENTRY = '''    if info.get("mergeStateStatus") == "DIRTY":
        raise Refused(f"PR #{pr} has merge conflicts — resolve them first")
'''

NEW_ENTRY = '''    if info.get("mergeStateStatus") == "DIRTY":
        raise Refused(f"PR #{pr} has merge conflicts — resolve them first")

    # UNCONDITIONAL, and at ENTRY rather than at the arming site. Both the dry-run and the
    # BEHIND paths return before arming, and a CLEAN PR is never armable, so a check down
    # there cannot fire in the read-only mode an operator actually runs -- nor on a green
    # PR whose foreign net is seconds from firing, which is exactly when it matters.
    snapshot_problem = stale_snapshot_refusal(info)
    if snapshot_problem:
        raise Refused(f"PR #{pr}: {snapshot_problem}")
'''

OLD_ARM = '''    _ARMED = {"owner": owner, "repo": repo, "pr": pr}
    pinned = f" pinned to {head[:8]}" if head else " (UNPINNED)"
    log(
        f"  auto-merge net armed{pinned} — GitHub will complete this merge even if this run "
        "dies (net is checks-green-gated; it does not re-pin the head after arming)"
    )
    return True'''

NEW_ARM = '''    _ARMED = {"owner": owner, "repo": repo, "pr": pr}
    pinned = f" pinned to {head[:8]}" if head else " (UNPINNED)"
    log(
        f"  auto-merge net armed{pinned} — GitHub will complete this merge even if this run "
        "dies (net is checks-green-gated; it does not re-pin the head after arming)"
    )
    # READ BACK. Exit 0 above proves the command did not error; it does NOT prove this run
    # armed anything. `gh pr merge --auto` against an ALREADY-armed PR exits 0 and prints
    # nothing, so without this the line above can announce a pinned net over someone else's
    # net whose stored body is what will actually fire. Report what is stored, not what was
    # asked for. Best-effort: a failed read must never fail a merge that is otherwise fine.
    try:
        after = pr_state(owner, repo, pr)
    except HardError as exc:  # nosec B110 - advisory read; see the comment above
        log(f"  (could not read the net back: {str(exc)[:80]})")
        return True
    amr = after.get("autoMergeRequest") or {}
    body = amr.get("commitBody")
    if body is None:
        log("  net body: none stored — resolved at MERGE time, so later commits still land")
    elif body == "":
        log("  !! net body: EMPTY STRING — this net will land a squash with NO body at all")
    else:
        log(f"  !! net body: a {len(body)}-char ARM-TIME SNAPSHOT, not this run's doing. "
            "Anything pushed from now on will be MISSING from the squash message.")
    return True'''


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    if "snapshot_problem" in src and "net body:" in src:
        print("already applied")
        return 0
    for name, old in (("entry guards", OLD_ENTRY), ("arm tail", OLD_ARM)):
        if src.count(old) != 1:
            print(f"REFUSING: anchor {name!r} found {src.count(old)} times (expected 1)",
                  file=sys.stderr)
            return 1
    src = src.replace(OLD_ENTRY, NEW_ENTRY).replace(OLD_ARM, NEW_ARM)
    TARGET.write_text(src, encoding="utf-8")
    print(f"applied to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
