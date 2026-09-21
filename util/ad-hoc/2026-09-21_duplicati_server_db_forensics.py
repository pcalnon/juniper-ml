#!/usr/bin/env python3
"""
Read-only forensics of Duplicati *server* databases (Duplicati-server.sqlite), from COPIES.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
         (root-cause analysis of "the server on :8300 has no backups defined")

WHY COPIES
  A Duplicati server database runs in SQLite WAL mode. Opening the live file in place
  can checkpoint or truncate its -wal when the connection closes, and a torn read of a
  live file proves nothing. So every database named on the command line is first copied
  -- main file plus its -wal and -shm siblings, when present -- into a work directory,
  and only the copy is opened, read-only (URI mode=ro).

WHAT IS PRINTED, AND WHAT IS NOT
  Printed: SQLite header fields, WAL header (salts, frame count), quick_check, the Version
  table, table names, Backup rows (ID, Name, Tags, DBPath, TargetURL with any query string
  MASKED), Schedule rows, Source paths, Filter expressions, allow-listed Metadata names
  with values, Option NAMES only (never values), Log/ErrorLog/Notification counts and the
  newest few rows' timestamp/title/message.
  Never printed: Option values (the passphrase can be cleartext there), TargetURL query
  strings (backend credentials), UIStorage, anything from a per-job database.
  Do not widen the allow-lists without re-reading the "Passphrase exposure has two
  channels" trap in the Yamaguchi handoffs.

USAGE
  2026-09-21_duplicati_server_db_forensics.py --workdir /path/to/scratch \
      label=/path/to/Duplicati-server.sqlite [label2=/path/to/other.sqlite ...]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import struct
import sys
from urllib.parse import urlsplit

ALLOWED_META = {
    "LastBackupDate", "LastBackupStarted", "LastBackupFinished", "LastBackupDuration",
    "LastErrorDate", "LastErrorMessage", "SourceSizeString", "SourceFilesCount",
    "SourceFilesSize", "TargetSizeString", "TargetFilesCount", "TargetFilesSize",
    "BackupListCount", "LastCompactStarted", "LastCompactFinished", "LastCompactDuration",
    "LastVerificationDate", "LastRestoreStarted", "LastRestoreFinished", "LastRestoreDuration",
    "LastPurgeStarted", "LastPurgeFinished", "LastRepairStarted", "LastRepairFinished",
}
ROW_COLS_OK = {"ID", "BackupID", "Timestamp", "Message", "Title", "Type", "Action", "MessageID",
               "MessageLogTag", "Time", "Repeat", "LastRun", "Rule", "Tags", "Order", "Include",
               "Expression", "Path", "Name", "Version", "Description", "DBPath"}
ERRLOG_LIMIT = 5
ERRLOG_EXC = 0


def human(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return str(n)


def mask_url(url: str | None) -> str:
    if not url:
        return repr(url)
    try:
        u = urlsplit(url)
    except Exception:  # noqa: BLE001 - forensic printer, keep going
        return "<unparseable url, len %d>" % len(url)
    q = f"?<{len(u.query)} chars masked>" if u.query else ""
    return f"{u.scheme}://{u.netloc}{u.path}{q}"


def sqlite_header(path: str) -> dict:
    with open(path, "rb") as fh:
        b = fh.read(100)
    if len(b) < 100 or not b.startswith(b"SQLite format 3\x00"):
        return {"error": "not a SQLite 3 file (or shorter than 100 bytes)"}
    ps = struct.unpack(">H", b[16:18])[0]
    return {
        "page_size": 65536 if ps == 1 else ps,
        "write_version": b[18], "read_version": b[19],  # 2 = WAL
        "change_counter": struct.unpack(">I", b[24:28])[0],
        "db_size_pages": struct.unpack(">I", b[28:32])[0],
        "schema_cookie": struct.unpack(">I", b[40:44])[0],
        "user_version": struct.unpack(">i", b[60:64])[0],
    }


def wal_header(path: str) -> dict:
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        b = fh.read(32)
    if len(b) < 32:
        return {"size": size, "error": "WAL shorter than its 32-byte header"}
    magic, ver, ps, ckpt, s1, s2, _c1, _c2 = struct.unpack(">IIIIIIII", b)
    frames = (size - 32) // (ps + 24) if ps else None
    return {"size": size, "magic": f"{magic:08x}", "format_version": ver, "page_size": ps,
            "checkpoint_seq": ckpt, "salt1": f"{s1:08x}", "salt2": f"{s2:08x}", "frames": frames}


def copy_set(src: str, workdir: str, label: str) -> str:
    dst_dir = os.path.join(workdir, label)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(src))
    copied = []
    for suffix in ("", "-wal", "-shm"):
        s = src + suffix
        if os.path.exists(s):
            try:
                shutil.copy2(s, dst + suffix)
                copied.append((suffix or "<main>", os.path.getsize(s)))
            except PermissionError as exc:
                copied.append((suffix or "<main>", f"PERMISSION DENIED ({exc.strerror})"))
    print(f"  copied: {copied}")
    return dst


def q(conn: sqlite3.Connection, sql: str, params=()):
    try:
        cur = conn.execute(sql, params)
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, cur.fetchall()
    except sqlite3.Error as exc:
        return None, f"<sqlite error: {exc}>"


def table_cols(conn, table):
    cols, rows = q(conn, f'PRAGMA table_info("{table}")')
    return [r[1] for r in rows] if cols else []


def print_rows(title, cols, rows, limit=None, trunc=300):
    print(f"  {title}: {len(rows)} row(s)")
    for r in rows[:limit] if limit else rows:
        parts = []
        for c, v in zip(cols, r):
            if c not in ROW_COLS_OK:
                continue
            s = str(v)
            if len(s) > trunc:
                s = s[:trunc] + f"...<{len(s) - trunc} more>"
            parts.append(f"{c}={s!r}")
        print("    - " + ", ".join(parts))


def inspect(label: str, src: str, workdir: str) -> None:
    print("=" * 100)
    print(f"[{label}] {src}")
    if not os.path.exists(src):
        print("  ABSENT")
        return
    st = os.stat(src)
    print(f"  size={st.st_size} mode={oct(st.st_mode & 0o777)} uid={st.st_uid} mtime={st.st_mtime}")
    for suffix in ("-wal", "-shm"):
        if os.path.exists(src + suffix):
            s2 = os.stat(src + suffix)
            print(f"  sibling {suffix}: size={s2.st_size} mtime={s2.st_mtime}")
    dst = copy_set(src, workdir, label)
    if not os.path.exists(dst):
        print("  main file could not be copied; stopping")
        return
    print(f"  header: {sqlite_header(dst)}")
    if os.path.exists(dst + "-wal"):
        print(f"  wal   : {wal_header(dst + '-wal')}")
    try:
        conn = sqlite3.connect(f"file:{dst}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        print(f"  OPEN FAILED: {exc}")
        return
    with conn:
        _, chk = q(conn, "PRAGMA quick_check")
        print(f"  quick_check: {chk if isinstance(chk, str) else [r[0] for r in chk]}")
        _, uv = q(conn, "PRAGMA user_version")
        print(f"  user_version: {uv if isinstance(uv, str) else uv[0][0]}")
        _, pc = q(conn, "PRAGMA page_count")
        print(f"  page_count (after WAL replay): {pc if isinstance(pc, str) else pc[0][0]}")
        _, tabs = q(conn, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        names = [] if isinstance(tabs, str) else [r[0] for r in tabs]
        print(f"  tables ({len(names)}): {names}")
        if "Version" in names:
            cols, rows = q(conn, "SELECT * FROM Version ORDER BY 1")
            vals = list(rows) if cols else rows
            print(f"  Version table: {vals}")
        if "Backup" in names:
            bcols = table_cols(conn, "Backup")
            cols, rows = q(conn, "SELECT * FROM Backup ORDER BY ID")
            if cols:
                print(f"  Backup: {len(rows)} row(s); columns={bcols}")
                for r in rows:
                    d = dict(zip(cols, r))
                    print(f"    - ID={d.get('ID')} Name={d.get('Name')!r} Tags={d.get('Tags')!r} "
                          f"DBPath={d.get('DBPath')!r} TargetURL={mask_url(d.get('TargetURL'))} "
                          f"Description={str(d.get('Description'))[:80]!r}")
            else:
                print(f"  Backup: {rows}")
        for t in ("Schedule", "Source", "Filter"):
            if t in names:
                cols, rows = q(conn, f'SELECT * FROM "{t}" ORDER BY 1')  # nosec B608 -- t is a name read from sqlite_master of a read-only COPY
                if cols:
                    print_rows(t, cols, rows, limit=60)
                else:
                    print(f"  {t}: {rows}")
        if "Metadata" in names:
            cols, rows = q(conn, "SELECT BackupID, Name, Value FROM Metadata ORDER BY BackupID, Name")
            if cols:
                print(f"  Metadata: {len(rows)} row(s)")
                for bid, name, value in rows:
                    if name in ALLOWED_META:
                        print(f"    - backup {bid}: {name} = {str(value)[:200]!r}")
                    else:
                        print(f"    - backup {bid}: {name} = <not printed>")
            else:
                print(f"  Metadata: {rows}")
        if "Option" in names:
            cols, rows = q(conn, "SELECT BackupID, Name FROM Option ORDER BY BackupID, Name")
            if cols:
                by_backup: dict = {}
                for bid, name in rows:
                    by_backup.setdefault(bid, []).append(name)
                print(f"  Option: {len(rows)} row(s) (values never printed)")
                for bid, ns in by_backup.items():
                    print(f"    - backup {bid}: {len(ns)} options: {ns}")
            else:
                print(f"  Option: {rows}")
        for t in ("Log", "ErrorLog", "Notification", "TempFile", "UIStorage"):
            if t in names:
                _, cnt = q(conn, f'SELECT COUNT(*) FROM "{t}"')  # nosec B608 -- t is a name read from sqlite_master of a read-only COPY
                n = cnt if isinstance(cnt, str) else cnt[0][0]
                print(f"  {t}: count={n}")
                if t in ("ErrorLog", "Notification") and not isinstance(cnt, str) and n:
                    tcols = table_cols(conn, t)
                    order = "Timestamp" if "Timestamp" in tcols else "ID" if "ID" in tcols else "1"
                    cols, rows = q(conn, f'SELECT * FROM "{t}" ORDER BY "{order}" DESC LIMIT {ERRLOG_LIMIT}')  # nosec B608 -- names from sqlite_master; int limit
                    if cols:
                        print_rows(f"  newest {t}", cols, rows, trunc=400)
                        if ERRLOG_EXC and "Exception" in cols:
                            # Exception text carries paths and messages, never option values.
                            ei = cols.index("Exception")
                            ti = cols.index("Timestamp") if "Timestamp" in cols else None
                            for r in rows:
                                exc = str(r[ei]).replace("\r", "")
                                head = exc[:ERRLOG_EXC] + (f"...<{len(exc) - ERRLOG_EXC} more>" if len(exc) > ERRLOG_EXC else "")
                                print(f"      exception@{r[ti] if ti is not None else '?'}: {head}")
        # A file NAMED Duplicati-server.sqlite can hold a per-job (local) schema instead.
        # Summarise it without touching content tables beyond counts and timestamps.
        if "Remotevolume" in names and "Operation" in names:
            print("  ** LOCAL (per-job) database schema detected, not a server schema **")
            cols, rows = q(conn, "SELECT ID, Description, Timestamp FROM Operation ORDER BY ID DESC LIMIT 10")
            if cols:
                print(f"  Operation (newest 10 of {len(rows)} shown): {rows}")
            cols, rows = q(conn, "SELECT Type, State, COUNT(*) FROM Remotevolume GROUP BY Type, State")
            if cols:
                print(f"  Remotevolume by Type/State: {rows}")
            cols, rows = q(conn, "SELECT Name FROM Remotevolume ORDER BY ID LIMIT 3")
            if cols:
                print(f"  Remotevolume sample names: {[r[0] for r in rows]}")
            cols, rows = q(conn, "SELECT COUNT(*), MIN(Timestamp), MAX(Timestamp) FROM Fileset")
            if cols:
                print(f"  Fileset count/min/max timestamp: {rows}")
            cols, rows = q(conn, "SELECT Key FROM Configuration ORDER BY Key")
            if cols:
                print(f"  Configuration keys (values not printed): {[r[0] for r in rows]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", required=True, help="scratch directory that receives the copies")
    ap.add_argument("dbs", nargs="+", help="label=/path/to/Duplicati-server.sqlite")
    ap.add_argument("--errorlog-rows", type=int, default=5, help="newest ErrorLog/Notification rows to print")
    ap.add_argument("--errorlog-exceptions", type=int, default=0,
                    help="also print the Exception column of those rows, truncated to N chars (0 = off)")
    args = ap.parse_args()
    global ERRLOG_LIMIT, ERRLOG_EXC
    ERRLOG_LIMIT = args.errorlog_rows
    ERRLOG_EXC = args.errorlog_exceptions
    os.makedirs(args.workdir, exist_ok=True)
    for spec in args.dbs:
        if "=" not in spec:
            print(f"bad spec (want label=path): {spec}", file=sys.stderr)
            return 2
        label, path = spec.split("=", 1)
        try:
            inspect(label, path, args.workdir)
        except Exception as exc:  # noqa: BLE001 - keep going, this is a forensic sweep
            print(f"  UNEXPECTED ERROR for {label}: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
