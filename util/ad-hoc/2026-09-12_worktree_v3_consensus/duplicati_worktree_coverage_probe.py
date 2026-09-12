#!/usr/bin/env python3
"""Read-only: does the live Duplicati job actually back up the session worktrees?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-12
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md

Why
---
The V3 cleanup design (`notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`)
asserts that `.claude/worktrees/` has ZERO backup coverage, and builds its whole
irreversibility premise on that. A Lane B reviewer refuted it from the Duplicati server DB.
That is a lone finding on the single most load-bearing claim in the document, so the
reconciler re-derives it here rather than taking it on trust.

The question is NOT "is there a Duplicati job" -- it is "does a path under
.claude/worktrees/ fall inside a Source AND escape every exclusion Filter".

Opens the DB strictly read-only (immutable URI): this must not perturb a live service.

KNOWN LIMITATION -- found by round 2, read this before trusting the output
-------------------------------------------------------------------------
The path below is a ROOT-WRITTEN SNAPSHOT of the server DB, not the live one. The live DB is at
/usr/lib/duplicati/data/ (drwx------ root root) and is unreadable as this user. Consequences:

  * the snapshot lags -- observed 2026-09-12 reading LastRun=2026-09-10T14:00Z while the
    DESTINATION already held a completed 20260911T140000Z fileset;
  * its `Log` table has ZERO rows, so this probe can say nothing about run history,
    success/failure, or whether any restore has ever been verified.

So this tool answers "which paths does the CONFIGURATION cover" and NOT "is the data
recoverable". For depth and recoverability, count the *.dlist.zip.aes files at the destination
-- there are only 9, the oldest is 20260825T102739Z, and retention deletes FILESETS, so a file
whose whole lifetime falls between two survivors is in none of them.
"""

from __future__ import annotations

import pathlib
import sqlite3
import sys

DB = pathlib.Path.home() / ".local/state/duplicati-server-db/Duplicati-server.sqlite"

# Concrete paths the design names as at-risk. Each must be tested against real filters.
PROBES = [
    "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/"
    + "curious-plotting-hummingbird/.env",
    "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/"
    + "dreamy-swinging-sunrise/.playwright-mcp/console-x.log",
    "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/"
    + "nifty-tinkering-wave/reports/soak/runs/run-1.json",
    "/home/pcalnon/Development/python/Juniper/Juniper/worktrees/some-tree/logs/system.log",
]


def main() -> int:
    if not DB.exists():
        print(f"NO DB at {DB}", file=sys.stderr)
        return 1
    con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True)
    cur = con.cursor()

    def table(name: str) -> list[str]:
        rows = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchall()
        if not rows:
            return []
        cols = [r[1] for r in cur.execute(f"PRAGMA table_info({name})").fetchall()]
        return cols

    print("=== Backup jobs ===")
    for row in cur.execute("SELECT ID, Name FROM Backup").fetchall():
        print(f"  id={row[0]}  name={row[1]!r}")

    print("\n=== Sources (the include set) ===")
    sources: list[tuple[int, str]] = []
    for row in cur.execute("SELECT BackupID, Path FROM Source").fetchall():
        sources.append((row[0], row[1]))
        print(f"  backup={row[0]}  path={row[1]!r}")

    print("\n=== Filters ===")
    filters: list[tuple[int, int, str]] = []
    cols = table("Filter")
    order_col = '"Order"' if "Order" in cols else "rowid"
    q = f"SELECT BackupID, Include, Expression FROM Filter ORDER BY {order_col}"
    for row in cur.execute(q).fetchall():
        filters.append((row[0], row[1], row[2]))
    n_inc = sum(1 for f in filters if f[1])
    print(f"  total={len(filters)}  include-type={n_inc}  exclude-type={len(filters) - n_inc}")
    for bid, inc, expr in filters:
        kind = "INCLUDE" if inc else "exclude"
        print(f"    [{kind}] {expr!r}")

    print("\n=== Any filter mentioning the at-risk directory names? ===")
    hot = ("claude", "worktree", "playwright", "reports", "\\.env", "logs")
    for bid, inc, expr in filters:
        low = expr.lower()
        for h in hot:
            if h.strip("\\.") in low:
                print(f"    MATCH {h!r}: [{'INCLUDE' if inc else 'exclude'}] {expr!r}")

    print("\n=== Verdict per probe path ===")
    for p in PROBES:
        in_source = [s for (_b, s) in sources if p.startswith(s)]
        print(f"  {p}")
        print(f"      inside Source? {bool(in_source)}  via {in_source}")

    print("\n=== Schedule / last run ===")
    if table("Schedule"):
        for row in cur.execute("SELECT ID, Repeat, LastRun FROM Schedule").fetchall():
            import datetime as _dt

            try:
                ts = _dt.datetime.fromtimestamp(int(row[2]), _dt.timezone.utc).isoformat()
            except Exception:
                ts = str(row[2])
            print(f"  id={row[0]} repeat={row[1]!r} lastrun={row[2]} ({ts})")

    print("\n=== Options that would silently drop large files ===")
    if table("Option"):
        for row in cur.execute("SELECT BackupID, Name, Value FROM Option").fetchall():
            if any(k in str(row[1]).lower() for k in ("skip", "size", "retention", "exclude")):
                print(f"  backup={row[0]} {row[1]}={row[2]!r}")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
