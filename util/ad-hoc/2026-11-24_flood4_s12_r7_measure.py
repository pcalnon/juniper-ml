#!/usr/bin/env python3
"""Measure each candidate worktree's size, its tmp/, and its recent modifications, read-only (flood-4 session 12, ruling 7).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (ruling 7's read-only worktree inventory; tmp/flood4/session12/r7/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session12/briefs/R7_inventory.txt (items 1 and "Live use"); util/ad-hoc/2026-11-24_flood4_s12_r7_scan.py

For each path in --paths (one per line): ``du -sb`` of the whole worktree and of its ``tmp/`` (each its own du call, since
one du call de-duplicates directories across its arguments), and one os.walk (no symlink following) that counts files
and finds the newest mtime, overall and inside ``tmp/``. Two more counts:
  * ``recent_files``: files modified after --since (the brief's six-hour LIVE rule), with the newest three named;
  * ``rename_window_files``: files modified inside --window-start..--window-end, the 2026-11-20..22 "owner -> Overtoad"
    pass. A file the pass rewrote has its mtime there, but so has any file legitimately written then, so this count is
    a measured signal, not proof that the pass touched the tree.
Counts and mtimes cover regular files and symlinks (lstat); directories count only toward du.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r7_measure.py --paths FILE --out FILE.json --since ISO8601Z \
        [--window-start 2026-11-20T00:00:00Z --window-end 2026-11-23T00:00:00Z] [--jobs N]
It reads only, runs du (never git) and writes only --out.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import os
import subprocess  # nosec B404 -- runs du only, with an argument list
import sys
from pathlib import Path


def _ts(s: str) -> float:
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()


def _iso(t: float | None) -> str | None:
    if t is None:
        return None
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _du(path: Path) -> int | None:
    proc = subprocess.run(["/usr/bin/du", "-sb", str(path)], capture_output=True, text=True, check=False)  # nosec B603 -- fixed argv
    try:
        return int(proc.stdout.split("\t", 1)[0])
    except (ValueError, IndexError):
        return None


def measure(path_s: str, since: float, w0: float, w1: float) -> dict:
    path = Path(path_s)
    row: dict = {"path": path_s, "exists": path.exists()}
    if not path.is_dir():
        return row
    row["total_bytes"] = _du(path)
    tmp = path / "tmp"
    row["tmp_exists"] = tmp.is_dir() and not tmp.is_symlink()
    row["tmp_is_symlink"] = tmp.is_symlink()
    row["tmp_bytes"] = _du(tmp) if row["tmp_exists"] else 0
    files = tmp_files = recent = window = 0
    newest = tmp_newest = None
    recent_names: list[tuple[float, str]] = []
    tmp_prefix = str(tmp) + os.sep
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
        in_tmp = (dirpath + os.sep).startswith(tmp_prefix)
        # symlinked dirs are listed in dirnames but not followed; count them as entries
        entries = filenames + [d for d in dirnames if os.path.islink(os.path.join(dirpath, d))]
        for name in entries:
            fp = os.path.join(dirpath, name)
            try:
                st = os.lstat(fp)
            except OSError:
                continue
            m = st.st_mtime
            files += 1
            if newest is None or m > newest:
                newest = m
            if in_tmp:
                tmp_files += 1
                if tmp_newest is None or m > tmp_newest:
                    tmp_newest = m
            if m > since:
                recent += 1
                recent_names.append((m, os.path.relpath(fp, path)))
            if w0 <= m < w1:
                window += 1
    recent_names.sort(reverse=True)
    row.update({"files": files, "newest_mtime": _iso(newest), "tmp_files": tmp_files, "tmp_newest_mtime": _iso(tmp_newest),
                "recent_files": recent, "recent_newest": [f"{_iso(m)} {n}" for m, n in recent_names[:3]],
                "rename_window_files": window})
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--paths", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--since", required=True)
    ap.add_argument("--window-start", default="2026-11-20T00:00:00Z")
    ap.add_argument("--window-end", default="2026-11-23T00:00:00Z")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    paths = [ln.strip() for ln in a.paths.read_text(encoding="utf-8").splitlines() if ln.strip()]
    since, w0, w1 = _ts(a.since), _ts(a.window_start), _ts(a.window_end)
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        rows = list(ex.map(lambda p: measure(p, since, w0, w1), paths))
    out = {"started_utc": started, "finished_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "since": a.since, "window": [a.window_start, a.window_end], "rows": rows}
    a.out.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"measured {len(rows)} paths; {sum(1 for r in rows if r.get('recent_files'))} with files newer than {a.since}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
