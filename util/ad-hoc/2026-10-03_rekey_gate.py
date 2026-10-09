#!/usr/bin/env python3
"""The re-key's exit gate: is a COPY of the Duplicati server database fully encrypted under ONE key?

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-10-03
Version:     1.2.0 (2026-10-08: Phase B round-4 fold-in -- see HISTORY)
Status:      ad-hoc -- recovery (the assessment's B4; called by 2026-10-03_rekey_settings_key.bash steps 1 and 8)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md
             notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md (section 7.3.5, P0.5b)

Usage:  2026-10-03_rekey_gate.py <copy-of-Duplicati-server.sqlite> <key-file>
        exit 0 = PASS; 1 = FAIL (the reason on stderr); 2 = usage / unreadable input.
        2026-10-03_rekey_gate.py --unrewritten <copy-of-Duplicati-server.sqlite>
        exit 0 = no blob the product's re-encryption would leave behind; 1 = at least one; 2 = unreadable.

What the gate checks, on the copy and never on the live file:
  * `encrypted-fields` (Option row at BackupID -2) is the string "True";
  * every `enc-v1:` blob in EVERY column 2.4.0.0 encrypts carries sha256hex(key) in its key-hash
    field. The blob is "enc-v1:" + sha256hex(ciphertext) + sha256hex(key) + ciphertext
    (Library/Encryption/EncryptedFieldHelper.cs: writer at 157-175, reader at 118-131). The five columns
    are the product's own list (Server/WipeEncryption.cs 119-141): Option.Value, Backup.TargetURL,
    Source.Path, ConnectionString.BaseUrl and BackupTargetUrl.TargetURL. The first draft scanned three of
    them; ReWriteAllFieldsIfEncryptionChanged (Library/RestAPI/Database/Connection.cs 131-153) never
    rewrites ConnectionString, so a row there under the OLD key would have passed the gate and survived
    the shredding of that key (Phase B validation, Lanes A and C). A table that does not exist in this
    schema is skipped. A value stored with SQLite type BLOB rather than TEXT is decoded and checked too
    (round 3, R3C N-12; the product never writes one, so this only closes a blind spot);
  * at least one blob exists (an empty result is a FAIL, not a vacuous pass).

What `--unrewritten` counts (the re-key's PRE-FLIGHT, before anything is stopped; round 3, R3A D-5 and
R3C D-2): the `enc-v1:` blobs that the product's own rewrite pass would leave under the OLD key, so
that the re-key can refuse BEFORE the keys are swapped instead of failing this gate after it --
  * every blob in ConnectionString.BaseUrl: the rewrite pass never touches that table (Connection.cs
    131-153: it re-saves each Backup with its children, then the server settings);
  * the ORPHANED blobs -- in a row whose BackupID names no Backup row -- of the three child tables the
    rewrite reaches only through a backup: BackupTargetUrl.TargetURL (LoadChildren loads a backup's rows,
    Library/RestAPI/Database/Backup.cs 54, and AddOrUpdateBackup re-saves them through
    SetBackupTargetUrls, Connection.cs 892-893, 1773-1810), Source.Path and Option.Value (SetSources and
    SetSettings, Connection.cs 882-883). `Option` and `Source` have NO foreign key (Schema.sql 44-45,
    72-73), so an orphan there outlives its backup; `BackupTargetUrl` cascades (Schema.sql 199), so an
    orphan there is unlikely but still counted (round 4, R4C DEFECT-2). `Option` rows at BackupID -1
    (ANY_BACKUP_ID) and -2 (SERVER_SETTINGS_ID; Connection.cs 56-57) are NOT orphans: the pass re-saves
    -1 itself (Connection.cs 145) and -2 through the EncryptedFields setter (ServerSettings.cs 851-855 ->
    SetAndSaveSetting -> SaveSettings 209-218 -> SetSettings(-2), which deletes and re-inserts every
    row, Connection.cs 387-407). Rows that belong to a backup are counted and printed as `attached`,
    but do not refuse.

Only counts are printed -- never a value, never the key. A key file holding a carriage return or a NUL
is refused: the unit hands the server the file's bytes with the CR (the wrapper keeps it), and the
wrapper's `$(<file)` drops a NUL, while a read here would judge a different key (round 3, R3C N-2;
round 4, R4C NIT-6).

HISTORY
  1.0.0  2026-10-03  first version (the assessment's B4), widened to all five columns in the Phase B
                     validation fold-in.
  1.1.0  2026-10-08  round-3 fold-in: `--unrewritten` pre-flight count; SQLite-BLOB values decoded; a key
                     file with a CR refused; docstring citations corrected (R3A N-8).
  1.2.0  2026-10-08  round-4 fold-in: `--unrewritten` also counts orphaned Option.Value (BackupID not -1,
                     -2 or a backup) and Source.Path blobs (R4C DEFECT-2); a key file with a NUL refused
                     (R4C NIT-6).
"""

from __future__ import annotations

import hashlib
import sqlite3
import sys

PREFIX = "enc-v1:"
COLUMNS = (
    ('SELECT "Value" FROM "Option"', "Option.Value"),
    ('SELECT "TargetURL" FROM "Backup"', "Backup.TargetURL"),
    ('SELECT "Path" FROM "Source"', "Source.Path"),
    ('SELECT "BaseUrl" FROM "ConnectionString"', "ConnectionString.BaseUrl"),
    ('SELECT "TargetURL" FROM "BackupTargetUrl"', "BackupTargetUrl.TargetURL"),
)


def as_text(value: object) -> str:
    """A column value as text: a SQLite BLOB is decoded (R3C N-12), anything else is str()."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def blobs_of(con: sqlite3.Connection, sql: str) -> list[str]:
    """The `enc-v1:` values a query returns."""
    return [t for t in (as_text(r[0]) for r in con.execute(sql) if r[0]) if t.startswith(PREFIX)]


def key_hash_of(blob: str) -> str:
    """The key-hash field of an enc-v1 blob, upper-cased; '' when the blob is too short to carry one."""
    return blob[len(PREFIX) + 64:len(PREFIX) + 128].upper()


def gate(copy: str, key: str) -> tuple[bool, str]:
    """Return (passed, one-line report). `key` is the key text with its trailing newline removed."""
    want = hashlib.sha256(key.encode("utf-8")).hexdigest().upper()
    con = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
    try:
        flag = con.execute('SELECT "Value" FROM "Option" WHERE "BackupID" = -2 AND "Name" = ?', ("encrypted-fields",)).fetchone()
        per_column: list[str] = []
        blobs: list[str] = []
        for sql, name in COLUMNS:
            try:
                found = blobs_of(con, sql)
            except sqlite3.OperationalError:
                per_column.append(f"{name}=absent")
                continue
            per_column.append(f"{name}={len(found)}")
            blobs += found
    finally:
        con.close()
    bad = sum(1 for b in blobs if key_hash_of(b) != want)
    flag_text = str(flag[0]) if flag else None
    report = (f"encrypted-fields={flag_text} blobs={len(blobs)} under-this-key={len(blobs) - bad} "
              f"under-another-key={bad} [{' '.join(per_column)}]")
    passed = bool(flag) and str(flag[0]).lower() == "true" and bool(blobs) and bad == 0
    return passed, report


SETTINGS_IDS = frozenset({-1, -2})   # ANY_BACKUP_ID and SERVER_SETTINGS_ID (Connection.cs 56-57): both re-saved


def orphans_of(con: sqlite3.Connection, sql: str, keep: frozenset[int]) -> tuple[int, int]:
    """(orphaned, attached) `enc-v1:` values of `sql` (which selects BackupID, value): a row is attached when
    its BackupID is in `keep`. Filtered here, not in SQL, so an absent Backup table means 'no backup'."""
    orphaned = attached = 0
    for backup_id, value in con.execute(sql):
        if value and as_text(value).startswith(PREFIX):
            if backup_id in keep:
                attached += 1
            else:
                orphaned += 1
    return orphaned, attached


def unrewritten(copy: str) -> tuple[int, str]:
    """Return (blobs the product's rewrite would leave behind, one-line report). See the module docstring."""
    con = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
    parts: list[str] = []
    total = 0
    try:
        try:
            backups = frozenset(r[0] for r in con.execute('SELECT "ID" FROM "Backup"'))
        except sqlite3.OperationalError:
            backups = frozenset()
        try:
            conn = len(blobs_of(con, 'SELECT "BaseUrl" FROM "ConnectionString"'))
            parts.append(f"ConnectionString.BaseUrl={conn}")
            total += conn
        except sqlite3.OperationalError:
            parts.append("ConnectionString.BaseUrl=absent")
        for name, sql, keep in (("Option.Value", 'SELECT "BackupID", "Value" FROM "Option"', backups | SETTINGS_IDS),
                                ("Source.Path", 'SELECT "BackupID", "Path" FROM "Source"', backups),
                                ("BackupTargetUrl.TargetURL", 'SELECT "BackupID", "TargetURL" FROM "BackupTargetUrl"', backups)):
            try:
                orphaned, attached = orphans_of(con, sql, keep)
            except sqlite3.OperationalError:
                parts.append(f"{name}=absent")
                continue
            parts.append(f"{name} orphaned={orphaned} attached={attached}")
            total += orphaned
    finally:
        con.close()
    return total, "never-rewritten enc-v1 blobs: " + " ".join(parts) + " (attached rows are rewritten)"


def read_key(key_file: str) -> str | None:
    """The key text with its trailing newlines removed (as the wrapper's `$(<file)` removes them), read
    without newline translation; None (and a FATAL line on stderr) when it is unreadable, empty,
    multi-line or holds a carriage return."""
    try:
        with open(key_file, encoding="utf-8", newline="") as fh:
            key = fh.read()
    except OSError as exc:
        print(f"FATAL: cannot read the key file: {exc.strerror}", file=sys.stderr)
        return None
    key = key.rstrip("\n")
    if "\r" in key:
        print("FATAL: the key file holds a carriage return -- the unit would hand the server a different key than this gate checks", file=sys.stderr)
        return None
    if "\0" in key:
        print("FATAL: the key file holds a NUL byte -- the wrapper drops it, so the server gets a different key than this gate checks", file=sys.stderr)
        return None
    if not key or "\n" in key:
        print("FATAL: the key file must hold exactly one non-empty line", file=sys.stderr)
        return None
    return key


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--unrewritten":
        try:
            n, report = unrewritten(argv[2])
        except sqlite3.Error as exc:
            print(f"FATAL: cannot read the copy: {exc}", file=sys.stderr)
            return 2
        print(report)
        return 1 if n else 0
    if len(argv) != 3 or argv[1].startswith("--"):
        print(f"usage: {argv[0]} <copy-of-Duplicati-server.sqlite> <key-file>\n       {argv[0]} --unrewritten <copy-of-Duplicati-server.sqlite>", file=sys.stderr)
        return 2
    copy, key_file = argv[1], argv[2]
    key = read_key(key_file)
    if key is None:
        return 2
    try:
        passed, report = gate(copy, key)
    except sqlite3.Error as exc:
        print(f"FATAL: cannot read the copy: {exc}", file=sys.stderr)
        return 2
    print(report)
    if not passed:
        print("GATE FAILED: the database is not fully encrypted under this key -- do not shred the old key; read the journal", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
