#!/usr/bin/env python3
"""Lane C round 3, task 5: the re-key gate against scratch SQLite databases with enc-v1-shaped blobs
(FAKE keys, FAKE ciphertext). Blob layout from the 2.4.0.0 source: "enc-v1:" + SHA256hex(ciphertext)
+ key.Hash + ciphertext, key.Hash = uppercase hex SHA-256 of the UTF-8 key (EncryptedFieldHelper.cs
58-59 and 157-175; HashExtentions.cs 37, 46; Utility.cs 869-872)."""
from __future__ import annotations

import hashlib
import sqlite3
import subprocess
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C")
GATE = S / "frozen/util/ad-hoc/2026-10-03_rekey_gate.py"
OUT = S / "gate_dbs"
OUT.mkdir(exist_ok=True)
NEW, OLD = "NEWKEY-fake-0002-xxxxxxxx", "OLDKEY-fake-0001-xxxxxxxx"
KEYFILE = OUT / "newkey"
KEYFILE.write_text(NEW + "\n")
KEYFILE.chmod(0o600)
COLS = ("option", "backup", "source", "conn", "bturl")


def blob(key: str, ct: str) -> str:
    # ciphertext is hex in the product (AESStringEncryption.EncryptToHex); any string works for the gate
    return "enc-v1:" + hashlib.sha256(ct.encode()).hexdigest().upper() + hashlib.sha256(key.encode()).hexdigest().upper() + ct


def build(name: str, flag="True", keys=None, extra_rows=(), schema_full=True, flag_rows=None, cleartext=()):
    keys = keys if keys is not None else {c: NEW for c in COLS}
    p = OUT / f"{name}.sqlite"
    if p.exists():
        p.unlink()
    con = sqlite3.connect(p)
    con.executescript('CREATE TABLE "Option" ("BackupID" INTEGER, "Filter" TEXT, "Name" TEXT, "Value" TEXT);'
                      'CREATE TABLE "Backup" ("ID" INTEGER, "Name" TEXT, "TargetURL" TEXT, "DBPath" TEXT);'
                      'CREATE TABLE "Source" ("BackupID" INTEGER, "Path" TEXT);')
    if schema_full:
        con.executescript('CREATE TABLE "ConnectionString" ("ID" INTEGER, "Name" TEXT, "Description" TEXT, "BaseUrl" TEXT, "CreatedAt" INTEGER, "UpdatedAt" INTEGER);'
                          'CREATE TABLE "BackupTargetUrl" ("ID" INTEGER, "BackupID" INTEGER, "TargetUrlKey" TEXT, "TargetURL" TEXT);')
    for v in (flag_rows if flag_rows is not None else ([flag] if flag is not None else [])):
        con.execute('INSERT INTO "Option" VALUES (-2, "", "encrypted-fields", ?)', (v,))
    con.execute('INSERT INTO "Option" VALUES (-2, "", "startup-delay", "0s")')
    if keys.get("option"):
        con.execute('INSERT INTO "Option" VALUES (-2, "", "pbkdf-config", ?)', (blob(keys["option"], "op1"),))
        con.execute('INSERT INTO "Option" VALUES (2, "", "passphrase", ?)', (blob(keys["option"], "op2"),))
    if keys.get("backup"):
        con.execute('INSERT INTO "Backup" VALUES (2, "Yamaguchi", ?, "x.sqlite")', ("file:///mnt/cleartext" if "backup" in cleartext else blob(keys["backup"], "bt"),))
    if keys.get("source"):
        for i in range(3):
            con.execute('INSERT INTO "Source" VALUES (2, ?)', (blob(keys["source"], f"s{i}"),))
    if schema_full and keys.get("conn"):
        con.execute('INSERT INTO "ConnectionString" VALUES (1, "c", "", ?, 0, 0)', (blob(keys["conn"], "cs"),))
    if schema_full and keys.get("bturl"):
        con.execute('INSERT INTO "BackupTargetUrl" VALUES (1, 2, "k", ?)', (blob(keys["bturl"], "bu"),))
    for sql, params in extra_rows:
        con.execute(sql, params)
    con.commit()
    con.close()
    return p


def gate(p: Path, keyfile: Path = KEYFILE):
    r = subprocess.run(["python3", str(GATE), str(p), str(keyfile)], capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    return r


def show(label: str, r, expect: int):
    ok = "as expected" if r.returncode == expect else "!! UNEXPECTED"
    print(f"{label:62s} exit={r.returncode} ({ok})  {r.stdout.strip()}")


show("all five columns under NEW", gate(build("pass")), 0)
for c in COLS:
    k = {x: NEW for x in COLS}
    k[c] = OLD
    show(f"one column under OLD: {c}", gate(build(f"old_{c}", keys=k)), 1)
# ONE blob of three in Source.Path under OLD, the other two under NEW
show("one of three Source.Path rows under OLD", gate(build("old_one_source", extra_rows=[('INSERT INTO "Source" VALUES (3, ?)', (blob(OLD, "s9"),))])), 1)
# one Option.Value blob for a JOB (BackupID 2) under OLD among NEW ones
show("one job Option.Value (BackupID 7) under OLD", gate(build("old_job_option", extra_rows=[('INSERT INTO "Option" VALUES (7, "", "auth-password", ?)', (blob(OLD, "ap"),))])), 1)
show("encrypted-fields False", gate(build("flag_false", flag="False")), 1)
show("encrypted-fields absent", gate(build("flag_absent", flag=None)), 1)
show("encrypted-fields NULL", gate(build("flag_null", flag_rows=[None])), 1)
show("encrypted-fields 'true' (lower case)", gate(build("flag_lower", flag="true")), 0)
show("encrypted-fields ' True' (leading space)", gate(build("flag_space", flag=" True")), 1)
show("zero blobs, flag True", gate(build("zero", keys={})), 1)
show("only the 2.3 tables (ConnectionString/BackupTargetUrl absent)", gate(build("old_schema", schema_full=False)), 0)
show("a truncated blob 'enc-v1:ABC' among NEW ones", gate(build("trunc", extra_rows=[('INSERT INTO "Source" VALUES (4, ?)', ("enc-v1:ABC",))])), 1)
show("duplicate flag rows: True then False", gate(build("dup_tf", flag_rows=["True", "False"])), 0)
show("duplicate flag rows: False then True", gate(build("dup_ft", flag_rows=["False", "True"])), 1)
show("Backup.TargetURL CLEARTEXT, every blob under NEW", gate(build("cleartext_target", cleartext=("backup",))), 0)
# the key file itself: CRLF and empty
crlf = OUT / "newkey_crlf"
crlf.write_bytes((NEW + "\r\n").encode())
show("key file NEW+CRLF vs a DB under NEW (Python drops the CR)", gate(build("pass2"), crlf), 0)
empty = OUT / "emptykey"
empty.write_text("\n")
show("empty key file", gate(build("pass3"), empty), 2)
# a blob stored as a SQLite BLOB (bytes), not TEXT
show("an OLD-key blob stored as SQLite BLOB type in Source.Path", gate(build("bytes_blob", extra_rows=[('INSERT INTO "Source" VALUES (5, ?)', (blob(OLD, "sb").encode(),))])), 1)
