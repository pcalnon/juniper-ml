#!/usr/bin/env python3
"""Fetch a sibling repo file at a ref through GitHub's contents API (read-only GET) into scratch.

Usage: ghshow.py <repo> <ref> <path> [dest]
Default dest: <scratch>/gh/<repo>/<ref>/<path>. Prints the dest and its line count.
"""
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA")
repo, ref, path = sys.argv[1:4]
dest = Path(sys.argv[4]) if len(sys.argv) > 4 else S / "gh" / repo / ref / path
if not dest.exists():
    data = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/pcalnon/{repo}/contents/{path}?ref={ref}"],
        check=True, capture_output=True,
    ).stdout
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
print(dest, len(dest.read_bytes().splitlines()))
