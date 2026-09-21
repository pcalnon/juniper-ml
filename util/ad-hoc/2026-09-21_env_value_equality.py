#!/usr/bin/env python3
"""
Boolean-only equality between the duplicati .env values (stdin) and the pcalnon credential file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc — investigation (written by consensus Lane B1; archived verbatim, header added)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §6 S-2/S-3;
         notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md (Lane B1, finding 9)

Prints only True/False per comparison and lengths. Never prints a value or a hash.
Result on 2026-09-21: the .env's ACTIVE settings key equals the live pcalnon PASSPHRASE (the
Yamaguchi backup passphrase); the commented PASSPHRASE / PASSPHRASE_OLD lines equal the live
values; the three commented key lines differ from each other and equal neither passphrase.

Usage:
    sg duplicati -c 'cat /home/duplicati/.config/Duplicati/.env' | \\
        python3 util/ad-hoc/2026-09-21_env_value_equality.py ~/.config/duplicati-backup/env
"""
import re
import sys

PC_ENV = sys.argv[1]


def strip_quotes(v):
    v = v.strip()
    if len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
        return v[1:-1]
    return v


pc = {}
with open(PC_ENV, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        m = re.match(r"^\s*(export\s+)?(PASSPHRASE|PASSPHRASE_OLD)=(.*)$", line.rstrip("\n"))
        if m:
            pc[m.group(2)] = strip_quotes(m.group(3))

env = {}
keys = []
for line in sys.stdin.read().split("\n"):
    s = line.rstrip("\r")
    m = re.match(r"^\s*#\s*(export\s+)?(PASSPHRASE|PASSPHRASE_OLD|SETTINGS_ENCRYPTION_KEY)=(.*)$", s)
    if m:
        if m.group(2) == "SETTINGS_ENCRYPTION_KEY":
            keys.append(strip_quotes(m.group(3)))
        else:
            env["C_" + m.group(2)] = strip_quotes(m.group(3))
        continue
    m = re.match(r"^\s*(export\s+)?SETTINGS_ENCRYPTION_KEY=(.*)$", s)
    if m:
        env["ACTIVE_KEY"] = strip_quotes(m.group(2))

print("pcalnon file keys:", sorted(pc), "| .env keys:", sorted(env), "| commented key lines:", len(keys))
print("env commented PASSPHRASE == pcalnon live PASSPHRASE:", env.get("C_PASSPHRASE") == pc.get("PASSPHRASE"))
print("env commented PASSPHRASE_OLD == pcalnon live PASSPHRASE_OLD:", env.get("C_PASSPHRASE_OLD") == pc.get("PASSPHRASE_OLD"))
print("env ACTIVE settings key == pcalnon live PASSPHRASE:", env.get("ACTIVE_KEY") == pc.get("PASSPHRASE"))
print("commented key lines identical to each other:", len(set(keys)) == 1 if keys else None,
      "| lengths after quote-strip:", [len(k) for k in keys])
print("any commented key == PASSPHRASE / PASSPHRASE_OLD:", any(k == pc.get("PASSPHRASE") for k in keys), any(k == pc.get("PASSPHRASE_OLD") for k in keys))
