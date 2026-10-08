#!/usr/bin/env python3
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  ad-hoc evaluation helper (Cursor flood #3, "clients" slice)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
#
# Ad-hoc, single-use. Fleet docs PRs bump `**Version**` / `**Date**` / `**Last Updated**`
# stamps; the flood-3 assembler bumps each file ONCE, so prepared consolidations must carry
# main's stamps unchanged. This rewrites every stamp line in the working file back to the
# value main has at the same occurrence index, and refuses when the stamp COUNTS differ
# (that would mean a stamp line was added or removed, which needs a human).
"""Usage: 2026-10-08_flood3_restore_doc_stamps.py <repo> <ref> <path> [<path> ...]"""
import re
import subprocess
import sys
from pathlib import Path

STAMP = re.compile(r"^\*\*(Version|Date|Last Updated)(\*\*:|:\*\*) .*$")


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2
    repo, ref, paths = Path(argv[1]), argv[2], argv[3:]
    rc = 0
    for rel in paths:
        base = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], capture_output=True, text=True, check=True).stdout.splitlines()
        target = repo / rel
        cur_text = target.read_text(encoding="utf-8")
        cur = cur_text.splitlines()
        base_stamps = [ln for ln in base if STAMP.match(ln)]
        cur_idx = [i for i, ln in enumerate(cur) if STAMP.match(ln)]
        if len(base_stamps) != len(cur_idx):
            print(f"REFUSE {rel}: {len(base_stamps)} stamp line(s) at {ref}, {len(cur_idx)} in the working file")
            rc = 1
            continue
        changed = 0
        for i, want in zip(cur_idx, base_stamps):
            if cur[i] != want:
                cur[i] = want
                changed += 1
        out = "\n".join(cur) + ("\n" if cur_text.endswith("\n") else "")
        target.write_text(out, encoding="utf-8")
        print(f"{rel}: restored {changed} stamp line(s) of {len(cur_idx)}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
