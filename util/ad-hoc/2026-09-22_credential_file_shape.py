#!/usr/bin/env python3
"""Report the SHAPE of a credential file without printing any value.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md section 8

Written for one question that decides whether Procedure A0 can run at all: is the value of
PASSPHRASE in ~/.config/duplicati-backup/env quoted, and does it carry shell metacharacters?
An UNQUOTED value containing `$` makes `set -a; . <file>` under `set -u` abort with
"<fragment>: unbound variable" -- printing part of the secret to stderr -- and a `&` makes the
shell run the tail of the value as a command. `2026-09-21_env_file_shape.py` answers the same
class of question for the duplicati-side .env; this one takes an arbitrary path.

Prints: name, export flag, value LENGTH, whether the value is quoted, and the SET of shell
metacharacters present. Never the value, never a substring of it.

Usage:  python3 util/ad-hoc/2026-09-22_credential_file_shape.py <file> [<file> ...]
"""

from __future__ import annotations

import os
import re
import sys

ASSIGN_RE = re.compile(r"^\s*(export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
# Characters that change how a POSIX shell parses an unquoted assignment value.
SHELL_META = set("$*@&#%!`\\\"'();|<>? \t[]{}~^")


def describe(path: str) -> int:
    try:
        st = os.stat(path)
    except OSError as exc:
        print(f"{path}: {exc.strerror}", file=sys.stderr)
        return 1
    print(f"file: {path}  mode={oct(st.st_mode)[-4:]}  size={st.st_size}  uid={st.st_uid} gid={st.st_gid}")
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
    except OSError as exc:
        print(f"  unreadable: {exc.strerror}", file=sys.stderr)
        return 1
    n_active = n_commented = 0
    for n, line in enumerate(lines, 1):
        stripped = line.lstrip()
        commented = stripped.startswith("#")
        probe = stripped.lstrip("#").lstrip() if commented else line
        m = ASSIGN_RE.match(probe)
        if not m:
            continue
        raw = m.group(3)
        quoted = len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]
        meta = "".join(sorted(c for c in set(raw) if c in SHELL_META))
        kind = "commented" if commented else "ACTIVE"
        if commented:
            n_commented += 1
        else:
            n_active += 1
        sourceable = quoted or not meta
        print(
            f"  line {n:>3}: {kind:<9} name={m.group(2)!r} export={bool(m.group(1))} "
            f"len={len(raw)} quoted={quoted} metachars={meta!r} "
            f"dot-sourceable={'yes' if sourceable else 'NO'}"
        )
    print(f"  totals: active={n_active} commented={n_commented}")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip().split("\n\n")[-1], file=sys.stderr)
        return 2
    rc = 0
    for path in sys.argv[1:]:
        rc |= describe(os.path.expanduser(path))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
