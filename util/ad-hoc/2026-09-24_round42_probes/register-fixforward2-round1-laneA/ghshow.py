#!/usr/bin/env python3
"""Lane A helper: fetch files at a pinned ref from GitHub (read-only GET via `gh api`).

usage: ghshow.py <owner/repo> <ref> <out_root> <path> [<path> ...]
Writes <out_root>/<path> (directories created). Uses the raw media type so large files are returned whole.
"""
import pathlib
import subprocess
import sys

repo, ref, out_root = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
for p in sys.argv[4:]:
    r = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/{repo}/contents/{p}?ref={ref}"],
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        print(f"FAIL {repo}@{ref}:{p}: {r.stderr.decode()[:200]}")
        continue
    dst = out_root / p
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(r.stdout)
    print(f"{repo}@{ref}:{p} -> {dst} ({len(r.stdout)} B)")
