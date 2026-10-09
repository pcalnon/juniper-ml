#!/usr/bin/env python3
"""What the Yamaguchi job's retention pass deletes from the nine pre-recovery filesets, by date and policy.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-10-08
Status:      ad-hoc -- evidence for the round-3 fold-in (R3B DEFECT-1 and the owner's 2026-10-08 ruling)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md (section 8, P0 steps 10-11)
             notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md (section 6.4)
             util/ad-hoc/2026-10-04_backup-phase-b-round3/R3B.md (DEFECT-1; its own port lived in /tmp and is lost)

A port of Duplicati 2.4.0.0's RetentionPolicyRemover.GetFilesetsToDelete
(tag v2.4.0.0_stable_2026-09-03, Duplicati/Library/Main/Operation/DeleteHandler.cs 339-433), read at the tag:

  * filesets sorted newest first; the newest (the run that just finished) is set aside and never deleted
    (allow-full-removal is not set on this job);
  * frames are applied smallest first; each takes, from the newest remaining, every fileset at or after
    `now - timeframe`; inside a frame, walking oldest to newest, a fileset is KEPT if it is the first or is at
    least `interval` after the last kept one, otherwise DELETED;
  * anything older than every frame is DELETED.

Units come from Timeparser.ParseTimeSpan (Duplicati/Library/Utility/Timeparser.cs 76-79), which
RetentionPolicyValue.CreateFromString uses (Library/Main/Options.cs 2053, 2065): D = 1 day, W = 7 days,
M = 30 days, Y = 365 days -- fixed spans, not calendar months.

The nine filesets are ROUND-1-RECORD:58 (`find ... -name '*.dlist.*'` on the destination, 2026-09-21); none has
been written since. All are assumed FULL backups (a partial one is never deleted -- it would only make the
result smaller). Post-recovery filesets are newer than all nine, so they cannot change what happens to the nine
(each frame keeps from its oldest member upward); the default scenario still models them.

Usage:  retention_table.py [--policy P] [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--recovered-days N]
        Prints one row per run of dates with the same outcome for the nine. --check reproduces R3B's
        published table for the OLD policy and exits non-zero on a mismatch.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone

UTC = timezone.utc
EXISTING = (
    "20260825T102739Z", "20260901T140000Z", "20260908T140000Z", "20260912T140000Z", "20260915T085649Z",
    "20260915T204850Z", "20260916T183346Z", "20260917T221344Z", "20260918T140000Z",
)
OLD_POLICY = "1W:1D,1M:1W,1Y:1M,3Y:2M"
NEW_POLICY = "2W:1D,6M:1W,2Y:1M,5Y:2M"
UNIT_DAYS = {"D": 1, "W": 7, "M": 30, "Y": 365}
# No post-recovery fileset can predate this: the recovery has not run before 2026-10-08.
EARLIEST_RECOVERY = datetime(2026, 10, 8, 14, 10, tzinfo=UTC)


def parse_span(text: str) -> timedelta:
    n, unit = int(text[:-1]), text[-1]
    return timedelta(days=n * UNIT_DAYS[unit])


def parse_policy(text: str) -> list[tuple[timedelta, timedelta]]:
    return [(parse_span(a), parse_span(b)) for a, b in (pair.split(":") for pair in text.split(","))]


def stamp(text: str) -> datetime:
    return datetime.strptime(text, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)


def to_delete(filesets: list[datetime], now: datetime, policy: list[tuple[timedelta, timedelta]]) -> set[datetime]:
    remaining = sorted(filesets, reverse=True)[1:]  # the newest is set aside
    deleted: set[datetime] = set()
    for frame, interval in sorted(policy):
        lower = now - frame
        in_frame: list[datetime] = []
        while remaining and remaining[0] >= lower:
            in_frame.insert(0, remaining.pop(0))
        last = None
        for f in in_frame:
            if last is None or f - last >= interval:
                last = f
            else:
                deleted.add(f)
    deleted.update(remaining)
    return deleted


def short(d: datetime) -> str:
    return d.strftime("%m-%dT%H:%M")


def outcome(day: datetime, policy, recovered_days: int, recovered_on: datetime = EARLIEST_RECOVERY) -> tuple[str, ...]:
    """The nine's survivors for a pass at `day` 14:30Z, with up to `recovered_days` daily post-recovery filesets.

    A post-recovery fileset is never dated before the recovery (`recovered_on`, default the earliest possible,
    2026-10-08): until round 4 (R4B N-4) a large --recovered-days invented "post-recovery" filesets dated in
    September, among the nine, and reported deletions that cannot happen. The pass's own run always exists.
    """
    old = [stamp(s) for s in EXISTING]
    run = day.replace(hour=14, minute=10)
    new = [run] + [run - timedelta(days=k) for k in range(1, recovered_days) if run - timedelta(days=k) >= recovered_on]
    gone = to_delete(old + new, day, policy)
    return tuple(short(x) for x in old if x not in gone)


def table(start: datetime, end: datetime, policy, recovered_days: int) -> list[tuple[str, str, tuple[str, ...]]]:
    rows: list[tuple[str, str, tuple[str, ...]]] = []
    day, prev, first = start, None, start
    while day <= end:
        kept = outcome(day, policy, recovered_days)
        if kept != prev:
            if prev is not None:
                rows.append((first.date().isoformat(), (day - timedelta(days=1)).date().isoformat(), prev))
            prev, first = kept, day
        day += timedelta(days=1)
    if prev is not None:
        rows.append((first.date().isoformat(), end.date().isoformat(), prev))
    return rows


# R3B's published table (first run at 14:30Z each day, OLD policy): a self-check on the port.
R3B_ROWS = [
    ("2026-10-05", "2026-10-07", ("08-25T10:27", "09-08T14:00", "09-15T20:48")),
    ("2026-10-08", "2026-10-11", ("08-25T10:27", "09-12T14:00")),
    ("2026-10-12", "2026-10-14", ("08-25T10:27", "09-15T08:56")),
    ("2026-10-15", "2026-10-15", ("08-25T10:27", "09-15T20:48")),
    ("2026-10-16", "2026-10-16", ("08-25T10:27", "09-16T18:33")),
    ("2026-10-17", "2026-10-17", ("08-25T10:27", "09-17T22:13")),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--policy", default=NEW_POLICY)
    ap.add_argument("--from", dest="start", default="2026-10-08")
    ap.add_argument("--to", dest="end", default="2027-03-06")
    ap.add_argument("--recovered-days", type=int, default=2,
                    help="post-recovery daily filesets present at the pass (default 2: the first backup and one more)")
    ap.add_argument("--check", action="store_true", help="reproduce R3B's OLD-policy table and exit")
    a = ap.parse_args()
    if a.check:
        got = table(datetime(2026, 10, 5, 14, 30, tzinfo=UTC), datetime(2026, 10, 17, 14, 30, tzinfo=UTC), parse_policy(OLD_POLICY), 1)
        ok = got == R3B_ROWS
        for row in got:
            print(f"  {row[0]} .. {row[1]}: keeps {', '.join(row[2])}")
        print("R3B table reproduced" if ok else "MISMATCH with R3B's table")
        return 0 if ok else 1
    policy = parse_policy(a.policy)
    start = datetime.strptime(a.start, "%Y-%m-%d").replace(hour=14, minute=30, tzinfo=UTC)
    end = datetime.strptime(a.end, "%Y-%m-%d").replace(hour=14, minute=30, tzinfo=UTC)
    print(f"policy {a.policy}; first pass at 14:30Z on each date; {a.recovered_days} post-recovery fileset(s) present")
    print("| First pass on | Deletes (of the 9) | Keeps (of the 9) | Deleted |")
    print("| --- | --- | --- | --- |")
    for first, last, kept in table(start, end, policy, a.recovered_days):
        gone = [short(stamp(s)) for s in EXISTING if short(stamp(s)) not in kept]
        span = first if first == last else f"{first} to {last}"
        print(f"| {span} | {len(gone)} | {', '.join(kept)} | {', '.join(gone)} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
