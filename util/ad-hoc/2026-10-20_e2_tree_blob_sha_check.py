#!/usr/bin/env python3
"""Prove which commit a .git-less tree serves: compare its files' git blob ids with the GitHub contents API.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc)
Application:  canopy E2E validation arc -- item 30 (the Phase 4 fix wave's live re-drive)
Author:       Paul Calnon
Created:      2026-10-20
Status:       ad-hoc -- investigation
Retire when:  RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      util/ad-hoc/2026-10-20_turing_canopy_leg.bash;
              notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 13, item 30)
License:      MIT License

WHY. turing's E2 canopy tree is an rsync of the primary checkout with .git excluded, so a leg launched from
it cannot stamp its serving commit from git ("a checkout is not a deployment", ledger item 7). This script
computes each file's git blob id locally -- sha1 over ``blob <len>\\0<bytes>`` -- and compares it with the
``sha`` the GitHub contents API reports for the same path at the claimed commit. A match on every file the
fixes touched (and the files the drives read) is the provenance the leg's ``git_sha`` stamp rests on. No
git binary is invoked, which is also why it runs under the worktree guard.

Usage:
    python3 -I util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py --repo pcalnon/juniper-canopy \\
        --ref 571743dba37fa39ac70dbd94fa5822d0822d5e68 --root ~/.local/state/juniper/turing-e2/trees/juniper-canopy \\
        src/frontend/dashboard_manager.py src/frontend/components/network_editor_panel.py ...
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess  # noqa: S404 -- gh api with literal arguments
import sys
import time


def blob_id(path: str) -> str:
    with open(path, "rb") as fh:
        data = fh.read()
    h = hashlib.sha1()  # noqa: S324 -- git's own blob id algorithm
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def remote_blob_id(repo: str, ref: str, path: str) -> str:
    out = subprocess.run(  # noqa: S603
        ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "--jq", ".sha"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if out.returncode != 0:
        return f"ERROR: {out.stderr.strip()[:200]}"
    return out.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default=None, help="write the per-file record as JSON here")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    root = os.path.expanduser(args.root)
    rec = {"repo": args.repo, "ref": args.ref, "root": root, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": []}
    all_ok = True
    for rel in args.paths:
        local = blob_id(os.path.join(root, rel))
        remote = remote_blob_id(args.repo, args.ref, rel)
        ok = local == remote
        all_ok &= ok
        rec["files"].append({"path": rel, "local": local, "remote": remote, "match": ok})
        print(f"{'MATCH   ' if ok else 'MISMATCH'} {rel}  local={local[:12]} remote={remote[:12]}")
    rec["all_match"] = all_ok
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print(f"record -> {args.out}")
    print("ALL MATCH" if all_ok else "NOT ALL MATCH")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
