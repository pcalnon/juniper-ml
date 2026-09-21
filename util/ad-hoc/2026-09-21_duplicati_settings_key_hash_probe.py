#!/usr/bin/env python3
"""
Offline settings-key candidate test against COPIES of Duplicati server databases.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc — investigation (written by consensus Lane B1; archived verbatim, header added)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §5.4 / §8 P0 step 3;
         notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md (Lane B1, finding 1)

Duplicati 2.4.0.0 `EncryptedFieldHelper`: an encrypted field is
    "enc-v1:" + sha256hex(ciphertext) + sha256hex(key) + ciphertext
so every encrypted field carries the SHA-256 of the key that encrypted it. A candidate key can
therefore be tested WITHOUT running a server and without any value leaving this process. The
content hash doubles as a self-check of the layout parse: if it verifies, the key-hash slice is
the right slice, and a "no match" is a real negative rather than a parse artifact.

Result on 2026-09-21 (Lane B1, on copies of the 09-20 root snapshot and the pcalnon
`Duplicati-server.backup`): content hashes verified 4/4 and 6/6, one distinct key hash per DB,
and NONE of the candidates or their shell-mangling variants matched either — the committed
36-character literal and the backup passphrase are both excluded as the 2026-09-18 key.

Prints ONLY: per DB, whether the blob layout parses (content hash verifies), how many distinct
key hashes the DB carries, and which candidate LABELS/variants match. Never prints a value or a hash.

Candidates:
  L                 the credential-shaped literal committed in scripts/duplicati-wrapper.bash
                    (read from the file named by argv[1]; absent once P1 removes the block)
  PASSPHRASE        from the pcalnon credential file named by argv[2] (~/.config/duplicati-backup/env)
  PASSPHRASE_OLD    same file
  ENV_ACTIVE_KEY, ENV_C_PASSPHRASE, ENV_C_PASSPHRASE_OLD, ENV_C_KEY_1..3
                    from the duplicati .env supplied on STDIN (commented and active lines)

Usage (the .env is group-readable only; use sg, never a copy in a world-readable place):
    sg duplicati -c 'cat /home/duplicati/.config/Duplicati/.env' | \\
        python3 util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py \\
            scripts/duplicati-wrapper.bash ~/.config/duplicati-backup/env \\
            snapshot0920=/path/to/COPY/of/Duplicati-server.sqlite [label=path ...]
Always run against a copy made with the -wal/-shm siblings (see
util/ad-hoc/2026-09-21_duplicati_server_db_forensics.py); never against the live file.
"""
import hashlib
import re
import sqlite3
import sys

WRAPPER = sys.argv[1]
PC_ENV = sys.argv[2]
DBS = sys.argv[3:]


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()


def strip_quotes(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
        return v[1:-1]
    return v


def variants(v: str):
    out = {"raw": v, "noquote": strip_quotes(v)}
    b = strip_quotes(v)
    out["unesc"] = b.replace("\\$", "$").replace("\\&", "&").replace("\\\\", "\\").replace("\\%", "%")
    out["no_dollar_star"] = b.replace("$*", "")
    out["no_dollar_at"] = b.replace("$@", "")
    out["no_dollar_star_at"] = b.replace("$*", "").replace("$@", "")
    out["pct_doubled"] = b.replace("%", "%%")
    out["newline"] = b + "\n"
    out["cr"] = b.rstrip("\r")
    out["stripped"] = b.strip()
    # bash double-quote expansion of $* / $@ with no positional params, and of ${...}
    out["bash_dq"] = re.sub(r"\$(\*|@|[0-9]|[A-Za-z_][A-Za-z0-9_]*|\{[^}]*\})", "", b)
    return out


cands = {}

# L from the wrapper comment block
marker = "Environment=SETTINGS_ENCRYPTION_KEY="
with open(WRAPPER, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        if marker in line:
            cands["L"] = line.split(marker, 1)[1].rstrip("\n")
            break

# pcalnon credential file
with open(PC_ENV, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        m = re.match(r"^\s*(export\s+)?(PASSPHRASE|PASSPHRASE_OLD)=(.*)$", line.rstrip("\n"))
        if m:
            cands[m.group(2)] = m.group(3)

# duplicati .env on stdin (may be empty if not supplied)
if not sys.stdin.isatty():
    raw = sys.stdin.read()
    n = 0
    for line in raw.split("\n"):
        s = line.rstrip("\r")
        m = re.match(r"^\s*#\s*(export\s+)?(PASSPHRASE|PASSPHRASE_OLD|SETTINGS_ENCRYPTION_KEY)=(.*)$", s)
        if m:
            if m.group(2) == "SETTINGS_ENCRYPTION_KEY":
                n += 1
                cands[f"ENV_C_KEY_{n}"] = m.group(3)
            else:
                cands[f"ENV_C_{m.group(2)}"] = m.group(3)
            continue
        m = re.match(r"^\s*(export\s+)?SETTINGS_ENCRYPTION_KEY=(.*)$", s)
        if m:
            cands["ENV_ACTIVE_KEY"] = m.group(2)

print("candidates loaded:", sorted(cands))

# precompute hashes of all variants
table = {}
for label, val in cands.items():
    for vname, vv in variants(val).items():
        if vv:
            table.setdefault(sha(vv), set()).add(f"{label}/{vname}")

for spec in DBS:
    label, path = spec.split("=", 1)
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    blobs = []
    for sql in ("SELECT TargetURL FROM Backup",
                "SELECT Value FROM Option WHERE Name IN ('passphrase','--passphrase','jwt-config','pbkdf-config')"):
        try:
            blobs += [r[0] for r in con.execute(sql) if r[0] and str(r[0]).startswith("enc-v1:")]
        except sqlite3.Error as exc:
            print(f"[{label}] query error: {exc}")
    con.close()
    keyhashes = set()
    parse_ok = 0
    for b in blobs:
        body = b[len("enc-v1:"):]
        ch, kh, content = body[:64], body[64:128], body[128:]
        if ch.upper() == sha(content):
            parse_ok += 1
        keyhashes.add(kh.upper())
    print(f"[{label}] encrypted blobs={len(blobs)} content-hash-verified={parse_ok} distinct-key-hashes={len(keyhashes)}")
    for kh in keyhashes:
        hits = sorted(table.get(kh, ()))
        print(f"[{label}]   key-hash match: {hits if hits else 'NONE of the candidates/variants'}")
