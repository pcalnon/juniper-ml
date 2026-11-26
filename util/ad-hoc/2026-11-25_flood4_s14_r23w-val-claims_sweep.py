#!/usr/bin/env python3
"""
Sweep a juniper-ml tree for sentences that state one of ruling 23's three "WebSocket gaps beside N-4" as open.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14 claims lens r23w-val-claims, run in session 15 on 2026-11-26 UTC)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

What it does
------------
Walks --tree (skipping the version-control directory, any directory named tmp, venvs and caches), reads every text
file, and reports each line matching one of the pattern groups below, as JSON (--out) and as text on stdout:
group, repo-relative path, line number, whether the path is one of the carrier's files (--carrier-paths, one
repo-relative path per line), and the line (cut to 400 characters). It reports; it decides nothing.

Usage
-----
    python3 -I <this file> --tree DIR --carrier-paths PATHS.txt --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

GROUPS: dict[str, list[str]] = {
    "slot": [
        r"past `?max_connections_per_ip`?",
        r"exceeded briefly",
        r"per-IP cap can be exceeded",
        r"releases? the socket's connection and per-IP slots",
        r"released? (its|the|both) (per-IP )?slots? at (once|the drop)",
        r"slots? (is|are) (freed|released) (before|at the drop)",
        r"freed before it has closed",
        r"close does not hold the socket",
        r"per-IP slot the drop released",
        r"forgets every failed socket",
        r"drop (still )?releases",
    ],
    "unsendable": [
        r"cannot seriali[sz]e",
        r"can't seriali[sz]e",
        r"unseriali[sz]able",
        r"has no `?default=`?",
        r"every resume across",
        r"until the (replay )?buffer evicts",
        r"refuses such a message once",
        r"this manager does not",
    ],
    "control": [
        r"/ws/control`? still",
        r"still calls `?receive_text",
        r"after its heartbeat's close",
        r"executed and cannot be acknowledged",
        r"late command",
        r"control_stream_handler`? with Starlette",
    ],
    "status": [
        r"[Kk]nown limits?\b",
        r"WebSocket gaps beside N-4",
        r"[Ss]till open",
    ],
}

SKIP_DIRS = {".git", "tmp", "venvs", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
TEXT_SUFFIXES = {".md", ".py", ".txt", ".yml", ".yaml", ".toml", ".json", ".bash", ".sh", ".cfg", ".ini", ".rst", ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--carrier-paths", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    tree = args.tree.resolve()
    carrier = {line.strip() for line in args.carrier_paths.read_text(encoding="utf-8").splitlines() if line.strip()}
    compiled = {group: [re.compile(p) for p in pats] for group, pats in GROUPS.items()}
    hits: list[dict] = []
    for root, dirs, files in os.walk(tree):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            path = Path(root) / name
            if path.suffix not in TEXT_SUFFIXES or path.is_symlink():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = path.relative_to(tree).as_posix()
            for lineno, line in enumerate(text.splitlines(), start=1):
                for group, pats in compiled.items():
                    matched = [p.pattern for p in pats if p.search(line)]
                    if matched:
                        hits.append({"group": group, "path": rel, "line": lineno, "carrier_file": rel in carrier, "patterns": matched, "text": line.strip()[:400]})
    args.out.write_text(json.dumps(hits, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for h in hits:
        print(f"{h['group']:<10} {'CARRIER' if h['carrier_file'] else 'main   '} {h['path']}:{h['line']}: {h['text'][:200]}")
    print(f"summary: {len(hits)} hits in {len({h['path'] for h in hits})} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
