#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Yamaguchi backup -- server DB snapshot
Author      : Paul Calnon
Version     : 1.2.0 (2026-10-08: no -wal/-shm residue in the destination; see HISTORY)
License     : MIT License

Capture a consistent copy of the Duplicati *server* database into a path the
Yamaguchi job actually backs up.

Two databases live in the server's data folder -- /home/duplicati/.config/Duplicati/
since the service-user migration (0700 duplicati; /usr/lib/duplicati/data/ was the
root server's, abandoned 2026-09-18 and frozen by P0 step 1) -- and they have opposite
loss profiles (note section 8.19):

  BMXWPAOGLP.sqlite       the per-job LOCAL INDEX. "Recreate" rebuilds it from
                          the destination. Slow, not fatal. NOT copied here.

  Duplicati-server.sqlite the BRAIN: job definition, 2 sources, 44 filters, 10
                          settings, the schedule, and the passphrase -- encrypted
                          under the settings key since 2026-09-18, cleartext before
                          (design section 5.4; the 09-17/09-18 filesets carry the
                          cleartext copy that Procedure A0 restores). "Recreate" does
                          NOT restore it. This is what we copy.

Why sqlite3.backup() and not cp: the server is running and writing. A byte copy
of a live SQLite file can land mid-transaction and restore as a corrupt DB that
still opens. The online-backup API takes a consistent snapshot of a live
database; `PRAGMA integrity_check` on the result then proves it.

Destination default: /home/pcalnon/.local/state/duplicati-server-db/
  - inside backup Source /home/pcalnon/
  - matched by NONE of the job's 44 exclusion filters (verified 2026-08-29;
    filter 36 excludes .cache/ and filter 37 .local/share/Steam/, neither of
    which covers .local/state/)
  - so the snapshot rides along in the next backup

NOTE this does NOT solve key escrow, and must not be mistaken for it. The
passphrase inside this DB is encrypted under the settings key, and the archive this
DB is copied into is encrypted with the very passphrase you would be trying to
recover -- a circle. Key escrow is yamaguchi_key_escrow.py, and it is a separate,
independent control.

Runs as root (the data folder is drwx------ duplicati). Installed by
util/install_duplicati_service.bash as /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py
and executed from there by yamaguchi-server-db-snapshot.service under ProtectSystem=strict
with ReadWritePaths= on the destination directory (design section 7.7).

HISTORY
  1.1.0  2026-10-03  the installed copy reads the service user's data folder (P0.5a item 2).
  1.2.0  2026-10-08  Phase B round-3 fold-in (R3C N-8): the online backup copies a WAL-mode
                     source's header, so the snapshot was itself WAL-mode, and the read-only
                     integrity check left two root-owned files (<name>.tmp-wal, <name>.tmp-shm)
                     in the destination on every run, riding along in the backup. The snapshot is
                     now switched to journal_mode=DELETE before it is closed -- a self-contained
                     single file -- and residue of earlier runs is removed. A restored copy in
                     DELETE mode is an ordinary SQLite database; the server sets its own mode.
"""

from __future__ import annotations

import argparse
import os
import pwd
import sqlite3
import sys
from datetime import datetime, timezone

SRC = "/home/duplicati/.config/Duplicati/Duplicati-server.sqlite"
DEST_DIR = "/home/pcalnon/.local/state/duplicati-server-db"
OWNER = "pcalnon"


def human(n):
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n:.1f} GiB"


def main():
    ap = argparse.ArgumentParser(description="Snapshot the Duplicati server DB into a backed-up path.")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--dest-dir", default=DEST_DIR)
    ap.add_argument("--owner", default=OWNER, help="chown the snapshot to this user")
    ap.add_argument("--dry-run", action="store_true", help="check gates, write nothing")
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    print(f"== Duplicati server-DB snapshot at {stamp}")

    # Distinguish "absent" from "not root". The data folder is drwx------
    # duplicati, so an unprivileged os.path.isfile() on a DB that is perfectly
    # present returns False -- reporting that as "missing" would send an
    # operator hunting for a deleted file instead of prefixing sudo.
    try:
        src_size = os.stat(args.src).st_size
    except PermissionError:
        sys.exit(f"REFUSE: cannot stat {args.src} -- permission denied on its "
                 f"directory. This says nothing about whether the DB exists; "
                 f"re-run as root (sudo).")
    except FileNotFoundError:
        sys.exit(f"REFUSE: source DB genuinely absent: {args.src}")
    if not os.access(args.src, os.R_OK):
        sys.exit(f"REFUSE: {args.src} is present but unreadable -- run as root (sudo).")

    print(f"source      : {args.src} ({human(src_size)})")

    dest = os.path.join(args.dest_dir, os.path.basename(args.src))
    print(f"dest        : {dest}")

    if args.dry_run:
        print("dry run -- nothing written")
        return 0

    try:
        pw = pwd.getpwnam(args.owner)
    except KeyError:
        sys.exit(f"REFUSE: no such user: {args.owner}")

    os.makedirs(args.dest_dir, mode=0o700, exist_ok=True)
    os.chown(args.dest_dir, pw.pw_uid, pw.pw_gid)
    os.chmod(args.dest_dir, 0o700)

    tmp = dest + ".tmp"
    # The snapshot and its side files, including the -wal/-shm residue 1.1.0 left behind.
    stale = [tmp, tmp + "-wal", tmp + "-shm", tmp + "-journal", dest + "-wal", dest + "-shm"]
    for path in stale:
        if os.path.exists(path):
            os.unlink(path)

    # Online backup API: consistent snapshot of a live, actively-written DB.
    src_conn = sqlite3.connect(f"file:{args.src}?mode=ro", uri=True)
    try:
        dst_conn = sqlite3.connect(tmp)
        try:
            src_conn.backup(dst_conn)
            # The backup copies the source's header, WAL flag included; a WAL-mode snapshot needs
            # -wal/-shm beside it whenever it is opened. DELETE mode makes it one file (R3C N-8).
            dst_conn.execute("PRAGMA journal_mode=DELETE")
        finally:
            dst_conn.close()
    finally:
        src_conn.close()

    # Prove the snapshot is not silently corrupt before it replaces the last
    # good one -- a copy that opens is not the same as a copy that is intact.
    check = sqlite3.connect(f"file:{tmp}?mode=ro", uri=True)
    try:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
        tables = check.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    finally:
        check.close()

    for path in stale[1:4]:
        if os.path.exists(path):
            os.unlink(path)

    if result != "ok":
        os.unlink(tmp)
        sys.exit(f"REFUSE: integrity_check on the snapshot returned {result!r}; "
                 "previous snapshot left in place")

    os.chmod(tmp, 0o600)
    os.chown(tmp, pw.pw_uid, pw.pw_gid)
    os.replace(tmp, dest)

    print(f"integrity   : ok ({tables} tables)")
    print(f"wrote       : {dest} ({human(os.path.getsize(dest))}, mode 0600, owner {args.owner})")
    print("this snapshot rides along in the next Yamaguchi backup (14:00Z daily).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
