#!/usr/bin/env python3
"""Bring MEMORY.md back under the harness's load limit: retire closed or stale rows, trim narrative tails.

Project: juniper-ml
Sub-Project: ad-hoc tooling (memory governance)
Author: Paul Calnon
Created: 2026-10-05
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: memory/feedback_memory_index_target_is_20kb.md; util/ad-hoc/2026-09-23_memory_index_editorial_compaction.py;
         util/ad-hoc/2026-09-12_memory_index_linkset.py

WHY

On 2026-10-05 the index was 25,695 characters (25,906 bytes) against a load limit of ~25,000 characters, and
the harness reported "3 of 89 lines were cut off": the recurrence × equities arc's three newest entries were
absent from every session. This follows the 2026-09-23 pass's rules (``feedback_memory_index_target_is_20kb.md``):
retire entries, never strip a hazard; every dropped fragment must already exist in its topic file, or is moved
there first (``MOVES``); and a link-SET comparison gates the result.

WHAT IT DOES

  * Retires three rows whose files stay reachable through inbound links from other memories:
      - ``project_required_signatures_broke_runner_commits.md`` — closed 2026-08-14 ("ALL lanes fixed"); its
        live lesson is the Commit/PR line's "only GraphQL ``createCommitOnBranch`` signs".
      - ``project_main_verify_red_since_2026-08-12.md`` — "self-perpetuation FIXED" (ml#1291); its hook, "the
        waiver trailer must REACH MAIN", repeats the Commit/PR line's squash-body entry; linked from the
        indexed sequence-safety memory.
      - ``project_canopy_ws_badge_red_herring_2026-05-10.md`` — SUPERSEDED: on canopy ``main`` (``60ae1870``)
        the badge reads the browser WS client's own state (``peekConnectionStatus()``,
        ``dashboard_manager.py:4513-4524``) plus the relay's health, so "the badge tracks status-data
        freshness, not the actual WS state" is no longer true. The file gets a SUPERSEDED banner.
  * Corrects two stale rows: "Deploy envs accept ANY ref" (FIXED 2026-08-17, ml#1151, per its own file) and
    the harness design's "v2 UNTRACKED in worktree" (v3 merged as ml#2110 on 2026-10-03).
  * Trims narrative tails whose facts are in the topic file (checked by grep before writing this), and drops
    one truncated hook ("— D-8 was").

SAFETY (as 2026-09-23's): every ``old`` must occur EXACTLY once, or nothing is written; ``--expect-mtime``
(nanoseconds) must equal the index's current mtime, or nothing is written; link TARGETS are never edited,
only removed with their row.

USAGE

    python3 util/ad-hoc/2026-10-05_memory_index_compaction.py --expect-mtime <ns> [--apply]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

MEM = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory")
INDEX = MEM / "MEMORY.md"

#: (old, new) on MEMORY.md. Each keeps its entry's imperative; a dropped fact lives in the topic file.
REPLACEMENTS: list[tuple[str, str]] = [
    # --- stale facts, corrected ---------------------------------------------------------------------------
    ("— v2 UNTRACKED in worktree `structured-inventing-fairy`; limits ARE observable", "— v3 on main (ml#2110); limits ARE observable"),
    (
        "- [Deploy envs accept ANY ref](project_publish_path_authorization_2026-08-17.md) — all 18, pypi included (ml#1140)",
        "- [Publish envs are TAG-only (ml#1151)](project_publish_path_authorization_2026-08-17.md) — name one on a PR/dispatch job and those runs FAIL with zero steps",
    ),
    # --- retired rows (each file stays reachable by inbound link) -------------------------------------------
    ("[required_signatures broke automations](project_required_signatures_broke_runner_commits.md); ", ""),
    ("- [main-verify self-perpetuation FIXED](project_main_verify_red_since_2026-08-12.md) — the waiver trailer must REACH MAIN\n", ""),
    ("; [WS:Reconnecting badge is a red herring](project_canopy_ws_badge_red_herring_2026-05-10.md)", ""),
    # --- narrative tails (the fact is in the topic file) ----------------------------------------------------
    ("— replay an EXPLICIT save (auto-snapshots have no history);", "— replay an EXPLICIT save;"),
    ("2026-10-04: ml#2134 (the ml#2115 fix-forward) MERGED; the watchdog is DARK", "the watchdog is DARK"),
    ("§8 STOP still on main (see the file); 7 rulings 09-22 (ml#2029); [reconciliation", "§8 STOP still on main; [reconciliation"),
    ("(reference_a_ruling_made_from_a_stale_recommendation_column.md) — D-8 was", "(reference_a_ruling_made_from_a_stale_recommendation_column.md)"),
    ("— rulings §5/§6 final; D1 flip shipped (cascor#683); PF-1 tag `pf1-2026-09-23-blas2`; suite ceiling", "— suite ceiling"),
    ("— two mints of one dataset_id differ in checksum with IDENTICAL arrays; compare arrays", "— compare arrays"),
    ("— −20,345 vs the E-H RFF+ridge config's −0.115 on the SAME artifact; a param-less request", "— a param-less request"),
    ("— ml#1176; they exposed", "— they exposed"),
    (
        "— verdict GO; W0.3–W0.7 merged; W0.1 service-core half DEFERRED (live cascor on :8202 imports from JuniperCascor1); rulings",
        "— W0.1 service-core half DEFERRED; rulings",
    ),
    # --- narrative tails moved to their topic file first (MOVES, below) -------------------------------------
    ("— canopy fixed (canopy#660); root anchors stay data+cascor", "— root anchors stay data+cascor"),
    ("retire-tool gates bypassed; sda SMART PASSED 2026-09-23 (ml#2041)", "retire-tool gates bypassed"),
]

#: Facts that existed only in the index, appended to their topic file before the index loses them.
MOVES: list[tuple[str, str, str]] = [
    (
        "reference_fork_drift_gate_cannot_express_canopy.md",
        "canopy#660",
        "\n**Moved from the MEMORY.md index, 2026-10-05:** canopy's half is fixed (canopy#660); the root anchors stay\n"
        "juniper-data and juniper-cascor.\n",
    ),
    (
        "project_duplicati_yamaguchi_arc_2026-09-08.md",
        "ml#2041",
        "\n**Moved from the MEMORY.md index, 2026-10-05:** sda SMART PASSED on 2026-09-23 (ml#2041). That supersedes\n"
        '"sda SMART still never run" above.\n',
    ),
]

BADGE = "project_canopy_ws_badge_red_herring_2026-05-10.md"
BADGE_BANNER = (
    "> **SUPERSEDED 2026-10-05.** On canopy `main` (`60ae1870`) the badge reads the browser WS client's own state:\n"
    "> `ws-connection-status` is fed by `window._juniperWsDrain.peekConnectionStatus()`\n"
    "> (`src/frontend/dashboard_manager.py:4513-4524`), and `src/frontend/components/connection_indicator.py` adds the\n"
    "> upstream relay's health from `/api/stream_health`. The mechanism below no longer applies, and this note's\n"
    "> MEMORY.md row was retired.\n\n"
)


def compacted(text: str) -> str:
    for old, new in REPLACEMENTS:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"anchor found {n} times (expected 1); nothing written: {old[:90]!r}")
        text = text.replace(old, new)
    return text


def with_banner(text: str) -> str:
    if "SUPERSEDED 2026-10-05" in text:
        return text
    if not text.startswith("---\n"):
        raise SystemExit(f"{BADGE}: no frontmatter; nothing written")
    end = text.index("\n---\n", 4) + len("\n---\n")
    return text[:end] + BADGE_BANNER + text[end:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--expect-mtime", type=int, required=True, help="MEMORY.md's st_mtime_ns when you read it")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    mtime = INDEX.stat().st_mtime_ns
    if mtime != args.expect_mtime:
        raise SystemExit(f"MEMORY.md changed since it was read (mtime {mtime} != {args.expect_mtime}); re-read it")
    before = INDEX.read_text(encoding="utf-8")
    after = compacted(before)
    print(f"MEMORY.md: {len(before)} -> {len(after)} characters ({len(before.encode())} -> {len(after.encode())} bytes), {len(REPLACEMENTS)} replacements")
    moves = []
    for name, marker, block in MOVES:
        text = (MEM / name).read_text(encoding="utf-8")
        moves.append((name, text if marker in text else text.rstrip("\n") + "\n" + block))
        print(f"  {name}: {'already holds' if marker in text else 'appends'} {marker}")
    badge = with_banner((MEM / BADGE).read_text(encoding="utf-8"))
    if not args.apply:
        print("dry run; pass --apply to write")
        return 0
    for name, text in moves:
        (MEM / name).write_text(text, encoding="utf-8")
    (MEM / BADGE).write_text(badge, encoding="utf-8")
    if INDEX.stat().st_mtime_ns != mtime:
        raise SystemExit("MEMORY.md changed during the run; the topic files were written, the index was NOT")
    INDEX.write_text(after, encoding="utf-8")
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
