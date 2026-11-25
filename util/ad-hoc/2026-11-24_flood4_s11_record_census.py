#!/usr/bin/env python3
"""
Census of every "ruling N" / "rulings N and M" / "rulings N-M" citation in snapshots of the Juniper repositories.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- census for the record update (rulings 15-48)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (its ruling numbers are
         cited from other repositories' CHANGELOGs, docs and tests, so the record must agree with each citation)

Why
---
The disposition record numbers the Overtoad's rulings, and merged texts in several repositories already cite those
numbers ("ruling 17", "rulings 16 and 18", "rulings 39-41"). Other arcs number their own rulings too, so a hit is
only a candidate: this lists each one with its context and whether "flood-4", "flood 4", the disposition record or a
Cursor carrier is named within ``--near`` lines, and the reader decides which arc it belongs to.

Input
-----
A directory holding one sub-directory per repository snapshot (``<dir>/<repo>/...``, e.g. extracted from
``gh api repos/<owner>/<repo>/tarball/<sha>`` or ``git archive``), and optionally loose files (``--files``) such as a
release tag's CHANGELOG. Only text files (.md .py .yml .yaml .toml .txt .cfg .ini) are read. Files under a ``tmp/``
directory are skipped (the repo-tmp convention: a count searches the repository with its tmp/ excluded).

Output
------
``--out`` JSON list: repo, path, line, the cited numbers, the matched text, a context window, and ``flood_near``.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_record_census.py --root <census dir> --out <hits.json> \\
        [--files <tag CHANGELOG> ...] [--near 6]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".toml", ".txt", ".cfg", ".ini"}
# "ruling 17", "rulings 16 and 18", "rulings 39-41", "rulings 39–41", "rulings 15, 16 and 17", "Ruling 10's"
CITE = re.compile(r"\b[Rr]ulings?\s+(\d+(?:\s*(?:,|and|to|-|–|—)\s*\d+)*)")
FLOOD = re.compile(r"flood[- ]?4|flood-four|fourth Cursor|CURSOR-FLOOD-4|disposition record|flood4", re.IGNORECASE)


def numbers(spec: str) -> list[int]:
    """The ruling numbers a matched list names, ranges expanded."""
    out: list[int] = []
    parts = re.split(r"\s*(?:,|and)\s*", spec)
    for part in parts:
        rng = re.match(r"(\d+)\s*(?:-|–|—|to)\s*(\d+)$", part.strip())
        if rng:
            lo, hi = int(rng.group(1)), int(rng.group(2))
            out.extend(range(lo, hi + 1) if 0 < hi - lo < 60 else [lo, hi])
        elif part.strip().isdigit():
            out.append(int(part.strip()))
    return out


def scan_file(repo: str, rel: str, path: Path, near: int) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return []
    hits: list[dict] = []
    for n, line in enumerate(lines, 1):
        for m in CITE.finditer(line):
            lo, hi = max(0, n - 1 - near), min(len(lines), n + near)
            window = "\n".join(lines[lo:hi])
            start = max(0, m.start() - 260)
            hits.append(
                {
                    "repo": repo,
                    "path": rel,
                    "line": n,
                    "numbers": numbers(m.group(1)),
                    "match": m.group(0),
                    "context": line[start : m.end() + 260],
                    "flood_near": bool(FLOOD.search(window)),
                }
            )
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="directory of per-repository snapshot directories")
    ap.add_argument("--files", nargs="*", default=[], help="loose files to scan too (repo name = file stem)")
    ap.add_argument("--near", type=int, default=6, help="lines either side searched for a flood-4 mention")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    root = Path(args.root)
    hits: list[dict] = []
    for repo_dir in sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("juniper-")):
        for path in sorted(repo_dir.rglob("*")):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            rel = path.relative_to(repo_dir).as_posix()
            if "tmp" in Path(rel).parts:
                continue
            hits.extend(scan_file(repo_dir.name, rel, path, args.near))
    for loose in args.files:
        p = Path(loose)
        hits.extend(scan_file(p.stem, p.name, p, args.near))
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(hits, fh, indent=1, ensure_ascii=False)
    print(f"{len(hits)} citation(s); {sum(h['flood_near'] for h in hits)} with a flood-4 mention within {args.near} lines -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
