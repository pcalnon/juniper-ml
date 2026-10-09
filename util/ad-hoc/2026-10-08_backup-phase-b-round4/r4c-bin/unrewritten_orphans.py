#!/usr/bin/env python3
"""Round 4 lane C: an Option / Source row of NO backup (no FK on either table, Schema.sql 44-45, 72-73)
holds an enc-v1 blob under the OLD key. Does the re-key pre-flight (--unrewritten) see it, and does the
exit gate then fail AFTER the swap?  Usage: unrewritten_orphans.py <a0-tree> <scratch>
"""

import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

tree, scratch = Path(sys.argv[1]), Path(sys.argv[2])
scratch.mkdir(parents=True, exist_ok=True)
GATE = tree / "util/ad-hoc/2026-10-03_rekey_gate.py"
OLD, NEW = "old-fake-key-aaaaaaaa", "new-fake-key-bbbbbbbb"


def blob(key: str) -> str:
    h = hashlib.sha256(key.encode()).hexdigest().upper()
    return "enc-v1:" + "0" * 64 + h + "ffff"


for table, orphan_sql in (("Option", 'INSERT INTO "Option" VALUES (7, "", "passphrase", ?)'),
                          ("Source", 'INSERT INTO "Source" VALUES (7, ?)')):
    db = scratch / f"orphan_{table}.sqlite"
    db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.executescript('''
        CREATE TABLE "Backup" ("ID" INTEGER PRIMARY KEY, "TargetURL" TEXT);
        CREATE TABLE "Option" ("BackupID" INTEGER NOT NULL, "Filter" TEXT, "Name" TEXT, "Value" TEXT);
        CREATE TABLE "Source" ("BackupID" INTEGER NOT NULL, "Path" TEXT);
        CREATE TABLE "ConnectionString" ("BaseUrl" TEXT);
        CREATE TABLE "BackupTargetUrl" ("BackupID" INTEGER NOT NULL, "TargetURL" TEXT);
    ''')
    # After the product's rewrite: everything it re-saves is under the NEW key, the flag True.
    con.execute('INSERT INTO "Backup" VALUES (1, ?)', (blob(NEW),))
    con.execute('INSERT INTO "Option" VALUES (-2, "", "encrypted-fields", "True")')
    con.execute('INSERT INTO "Option" VALUES (1, "", "passphrase", ?)', (blob(NEW),))
    con.execute('INSERT INTO "Source" VALUES (1, ?)', (blob(NEW),))
    con.execute(orphan_sql, (blob(OLD),))  # a row of no backup: never rewritten (Connection.cs 131-153)
    con.commit()
    con.close()
    key = scratch / "newkey"
    key.write_text(NEW, encoding="utf-8")
    pre = subprocess.run([sys.executable, str(GATE), "--unrewritten", str(db)], capture_output=True, text=True)
    post = subprocess.run([sys.executable, str(GATE), str(db), str(key)], capture_output=True, text=True)
    print(f"orphan {table}: --unrewritten exit={pre.returncode} [{pre.stdout.strip()}]")
    print(f"orphan {table}: exit gate     exit={post.returncode} [{post.stdout.strip()}]")
