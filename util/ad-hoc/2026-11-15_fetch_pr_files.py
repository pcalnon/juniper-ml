#!/usr/bin/env python3
"""Fetch files from a branch or commit of a pcalnon repo, exactly as GitHub holds them, into a local directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (verify the one-artifact publish ports as pushed, not as the porting session's copies)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_publish_port_template_identity.py (checks the files this fetches)

Why
---
A port is checked against what its pull request carries, never against the local tree it was uploaded from: an upload
can omit or misplace a file, and the porting session's copy can move afterwards. The contents API returns each blob
base64-encoded (and no inline content above 1 MB: such a file is fetched through its git blob instead). A path list
from ``--pr N`` takes every file the pull request changes.

    python3 -I util/ad-hoc/2026-11-15_fetch_pr_files.py --repo juniper-canopy --ref fix/publish-one-artifact --out DIR \\
        [--pr N] [PATH ...]

Each file lands at DIR/<path>. Exit status: 0; 1 when a file could not be fetched.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

OWNER = "pcalnon"


def gh_json(path: str) -> object:
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return json.loads(proc.stdout)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--pr", type=int)
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    paths = list(args.paths)
    if args.pr:
        files = gh_json(f"repos/{OWNER}/{args.repo}/pulls/{args.pr}/files?per_page=100")
        paths += [f["filename"] for f in files if f.get("status") != "removed" and f["filename"] not in paths]
    failed = 0
    for rel in paths:
        try:
            meta = gh_json(f"repos/{OWNER}/{args.repo}/contents/{urllib.parse.quote(rel)}?ref={urllib.parse.quote(args.ref, safe='')}")
            content = meta.get("content") or ""
            if not content and meta.get("size", 0) > 0:
                content = gh_json(f"repos/{OWNER}/{args.repo}/git/blobs/{meta['sha']}")["content"]
            data = base64.b64decode(content)
        except (RuntimeError, KeyError, ValueError) as exc:
            print(f"FAILED {rel}: {exc}")
            failed += 1
            continue
        target = args.out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"{len(data):8d} bytes  {rel}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
