#!/usr/bin/env python3
"""
Describe the SHAPE of a KEY=VALUE environment file without ever printing a value.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
         (the duplicati wrapper's .env parser mangles values containing shell metacharacters)

Reads the file from STDIN so the caller can choose the privilege boundary, e.g.
    sg duplicati -c 'cat /home/duplicati/.config/Duplicati/.env' | 2026-09-21_env_file_shape.py

Per non-comment line it prints: the key, the value length, whether the value is quoted,
whether it contains '=', which shell-significant characters it contains, and whether the
line ends in CRLF. With --leak-source <file>, the value of SETTINGS_ENCRYPTION_KEY is
compared (by SHA-256, never by printing) against the credential-shaped literal that file's
comment block carries after "Environment=SETTINGS_ENCRYPTION_KEY=", so an operator can tell
whether the committed literal is the live key without either value leaving the process.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys

META = "$*?[]{}@%&;|<>()`'\" \\#!~"


def leaked_literal(path: str) -> str | None:
    marker = "Environment=SETTINGS_ENCRYPTION_KEY="
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if marker in line:
                return line.split(marker, 1)[1].strip()
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--leak-source", help="file whose comment block carries a committed key literal")
    ap.add_argument("--key-name", default="SETTINGS_ENCRYPTION_KEY")
    ap.add_argument("--compare-to-commented", metavar="NAME",
                    help="also report whether the active key equals the value of a COMMENTED-OUT "
                         "'# export NAME=...' line in the same file (by SHA-256; nothing is printed)")
    args = ap.parse_args()

    leak_hash = None
    if args.leak_source:
        lit = leaked_literal(args.leak_source)
        if lit:
            leak_hash = hashlib.sha256(lit.encode()).hexdigest()
            print(f"committed literal in {args.leak_source}: len={len(lit)} "
                  f"metachars={''.join(c for c in META if c in lit)!r} sha256[:12]={leak_hash[:12]}")
        else:
            print(f"no committed literal found in {args.leak_source}")

    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    commented_hash = None
    if args.compare_to_commented:
        pat = re.compile(r"^\s*#\s*(export\s+)?" + re.escape(args.compare_to_commented) + r"=(.*)$")
        for line in raw.split("\n"):
            m = pat.match(line.rstrip("\r"))
            if m:
                v = m.group(2).strip()
                if len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
                    v = v[1:-1]
                commented_hash = hashlib.sha256(v.encode()).hexdigest()
                break
        print(f"commented '{args.compare_to_commented}=' line found: {commented_hash is not None}")
    for i, line in enumerate(raw.split("\n"), 1):
        crlf = line.endswith("\r")
        s = line.rstrip("\r")
        if s.strip() == "":
            print(f"{i:3}: <blank>{' CRLF' if crlf else ''}")
            continue
        if s.lstrip().startswith("#"):
            # A commented-out assignment is still a secret. Print only the text up to
            # the first '=' and the length of what follows -- never the value.
            if "=" in s:
                head, tail = s.split("=", 1)
                print(f"{i:3}: <comment> {head[:80]}=<{len(tail)} chars redacted>{' CRLF' if crlf else ''}")
            else:
                print(f"{i:3}: <comment> {s[:100]}{' CRLF' if crlf else ''}")
            continue
        m = re.match(r"^(\s*)(export\s+)?([^=\s]+)\s*(=(.*))?$", s)
        if not m:
            print(f"{i:3}: <unparsed line, len {len(s)}>{' CRLF' if crlf else ''}")
            continue
        key, val = m.group(3), m.group(5)
        exported = bool(m.group(2))
        if val is None:
            print(f"{i:3}: key={key!r} (no '=' present) export={exported}{' CRLF' if crlf else ''}")
            continue
        quoted = len(val) >= 2 and val[0] in "'\"" and val[-1] == val[0]
        inner = val[1:-1] if quoted else val
        meta = "".join(c for c in META if c in val)
        extra = ""
        if key == args.key_name and leak_hash:
            extra = f" SAME_AS_COMMITTED_LITERAL={hashlib.sha256(inner.encode()).hexdigest() == leak_hash}"
        if key == args.key_name and commented_hash:
            # Bash strips the quotes; a backslash before '$' inside double quotes is also
            # stripped, so compare both the raw inner text and its backslash-unescaped form.
            raw_h = hashlib.sha256(inner.encode()).hexdigest()
            unesc_h = hashlib.sha256(inner.replace("\\$", "$").replace("\\&", "&").encode()).hexdigest()
            extra += (f" EQUALS_COMMENTED_{args.compare_to_commented}="
                      f"{raw_h == commented_hash or unesc_h == commented_hash}")
        print(f"{i:3}: key={key!r} export={exported} val_len={len(val)} quoted={quoted} "
              f"has_eq={'=' in val} metachars={meta!r}{' CRLF' if crlf else ''}{extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
