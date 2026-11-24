#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml (cross-repo tooling)
# Application:   util/ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Created:       2026-11-23
# Status:        ad-hoc (single arc: repair of the 2026-11-20 "owner -> Overtoad" rename PRs)
"""Build the follow-up commit that turns a GitHub revert of juniper-recurrence#237 into a symlink fix.

Why this exists
---------------
#237 (merged 2026-11-20, ``93a28202``) replaced ``juniper-recurrence-client/CLAUDE.md -> AGENTS.md`` with
a regular file holding AGENTS.md's text after the blind rename. The signed-commit API cannot write a
symlink, but a revert that GitHub generates can, and GitHub signs it. That revert also undoes #237's
correct renames, so this writes every other reverted file back at main's bytes. It also gives
``juniper-recurrence-client/AGENTS.md`` the person-only rename: #237 meant to rename that text and wrote
it into the copy instead.

Usage
-----
    python3 2026-11-23_recurrence_237_symlink_restore.py --revert-head SHA --out DIR --today YYYY-MM-DD

Writes the files under DIR at their repository paths and prints what the follow-up commit carries.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import re
import subprocess
import sys

REPO = "pcalnon/juniper-recurrence"
MAIN = "93a28202"
LINK = "juniper-recurrence-client/CLAUDE.md"
TARGET = "juniper-recurrence-client/AGENTS.md"
HERE = os.path.dirname(os.path.abspath(__file__))


def gh(path: str) -> dict | list:
    return json.loads(subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout)


def content(path: str, ref: str) -> bytes:
    meta = gh(f"repos/{REPO}/contents/{path}?ref={ref}")
    if meta.get("type") != "file":
        raise SystemExit(f"{path}@{ref} is a {meta.get('type')}, not a file")
    return base64.b64decode(meta["content"] or gh(f"repos/{REPO}/git/blobs/{meta['sha']}")["content"])


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--revert-head", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--today", required=True)
    args = ap.parse_args(argv)

    # the contents API follows a link whose target is a file, so read the mode from the tree
    tree = gh(f"repos/{REPO}/git/trees/{args.revert_head}?recursive=1")
    entry = next((e for e in tree["tree"] if e["path"] == LINK), {})
    target_text = base64.b64decode(gh(f"repos/{REPO}/git/blobs/{entry['sha']}")["content"]).decode() if entry else ""
    if entry.get("mode") != "120000" or target_text != "AGENTS.md":
        raise SystemExit(f"REFUSED: {LINK} at the revert head is mode {entry.get('mode')} -> {target_text!r}")
    print(f"{LINK} at the revert head: mode 120000 -> {target_text}")
    files = [f["filename"] for f in gh(f"repos/{REPO}/compare/{MAIN}...{args.revert_head}")["files"]]
    restore = sorted({path for path in files if path != LINK})
    for path in restore:
        data = content(path, MAIN)
        target = os.path.join(args.out, path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as handle:
            handle.write(data)
    print(f"restore at main's bytes: {len(restore)} files")

    spec = importlib.util.spec_from_file_location("pr2606_rebuild", os.path.join(HERE, "2026-11-23_pr2606_rebuild.py"))
    rebuild = importlib.util.module_from_spec(spec)
    sys.modules["pr2606_rebuild"] = rebuild
    spec.loader.exec_module(rebuild)
    agents = content(TARGET, MAIN).decode("utf-8")
    renamed, decisions = rebuild.person_only(agents, False, True)
    renamed = re.sub(r"(?m)^\*\*Last Updated\*\*: .*$", f"**Last Updated**: {args.today}", renamed, count=1)
    copy = content(LINK, MAIN).decode("utf-8")
    path = os.path.join(args.out, TARGET)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(renamed)
    keep = sum(d[1] == "KEEP" for d in decisions)
    restored = [d for d in decisions if d[1] != "KEEP" and d[1] != "UNCHANGED"]
    print(f"{TARGET}: person-only rename, {keep} renamed, {len(restored)} technical kept")
    for number, verdict, why, ctx in restored:
        print(f"  {verdict} line {number}: {why} | {ctx[:120]}")
    same = renamed == copy
    print(f"matches #237's copy in {LINK}: {same}")
    if not same:
        import difflib

        for line in difflib.unified_diff(copy.split("\n"), renamed.split("\n"), "237-copy", "rebuilt", n=0, lineterm=""):
            if not line.startswith(("---", "+++")):
                print("  " + line[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
