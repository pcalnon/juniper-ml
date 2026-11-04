#!/usr/bin/env python3
"""
Check each ``main`` tarball extract against its commit's tree on GitHub, so a cleanup calls an extract regenerable only when every file on disk is a blob that tree names, and keeps each file that is not.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-04
Status: ad-hoc — one-off (flood-3: the predecessor worktree's cleanup, owner ruling 2026-11-04 "Remove; keep evidence")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-03_fetch_main_tarballs.py (writes the layout this reads);
         util/ad-hoc/2026-11-04_worktree_cleanup_keep_evidence_skip_extracts.py (reads this script's output);
         notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§6, §8)

Why this exists
---------------
The owner ruled on 2026-11-04 that the predecessor's worktree is removed with its evidence kept, as on 2026-10-30.
About 600 MB of its ``tmp/`` is ``main`` tarball extracts, which the fetcher can make again from the SHA it recorded
beside each one. An extract is regenerable only while nothing in it was edited, and the pin lane DID edit one copy:
it rewrote ``CHANGELOG.md`` and ``agents-md-touch-up.yml`` in place. A modification time cannot settle that,
because tar restores the commit's times and an edit made inside the extraction window would not stand out. So this
hashes every file on disk as a git blob and compares it with the tree GitHub serves for the recorded SHA.

    python3 -I util/ad-hoc/2026-11-04_tarball_extract_pristine_check.py <out.tsv> <layout-dir> [<layout-dir> ...]

A layout dir holds ``<repo>/`` beside ``<repo>.sha``, as the fetcher writes them. Each tree is read with
``gh api repos/pcalnon/<repo>/git/trees/<sha>?recursive=1``; a truncated tree is an error. Rows in ``out.tsv``:

- ``ROOT  <root>  <repo>  <sha>  same=N edited=N extra=N missing=N missing_symlink=N`` for every extract checked;
- ``DEV  <root>  <verdict>  <path>`` for every deviation, where verdict is EDITED (the blob differs), EXTRA (not in
  the tree), EXTRA-PYCACHE (an ``__pycache__/`` file: regenerable), MISSING (a tree blob absent on disk) or
  MISSING-SYMLINK (a mode 120000 entry: the fetcher skips symlinks, so these are expected).

A cleanup may skip an extract's regenerable bulk and must keep its EDITED and EXTRA files. MISSING entries need no
copy: regenerating the extract yields a superset of what was on disk. Runs only ``gh api`` GETs and reads files.
Exit 0 when every extract was checked, whatever it found; 1 on an API error or a truncated tree; 2 on bad arguments.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess  # nosec B404 - fixed gh argv, no shell
import sys
from pathlib import Path


def blob_id(p: Path) -> str:
    """The git blob id of a regular file."""
    data = p.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # nosec B324 -- git's object id, not security


def tree(repo: str, sha: str) -> dict[str, tuple[str, str]]:
    """{path: (mode, blob id)} for every blob in the commit's tree."""
    out = subprocess.run(["gh", "api", f"repos/pcalnon/{repo}/git/trees/{sha}?recursive=1"], check=True, capture_output=True, text=True).stdout  # nosec B603 B607
    doc = json.loads(out)
    if doc.get("truncated"):
        raise RuntimeError(f"{repo}@{sha[:8]}: the tree is truncated")
    return {e["path"]: (e["mode"], e["sha"]) for e in doc["tree"] if e["type"] == "blob"}


def check(root: Path, repo: str, sha: str, out) -> str:
    want = tree(repo, sha)
    seen: set[str] = set()
    counts = {"same": 0, "edited": 0, "extra": 0, "missing": 0, "missing_symlink": 0}
    devs: list[tuple[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            p = Path(dirpath) / name
            rel = p.relative_to(root).as_posix()
            entry = want.get(rel)
            if p.is_symlink():
                devs.append(("EXTRA", rel))  # the fetcher writes no symlinks, so one here was made later
                counts["extra"] += 1
                continue
            seen.add(rel)
            if entry is None:
                devs.append(("EXTRA-PYCACHE" if "__pycache__" in Path(rel).parts else "EXTRA", rel))
                counts["extra"] += 1
            elif blob_id(p) == entry[1]:
                counts["same"] += 1
            else:
                devs.append(("EDITED", rel))
                counts["edited"] += 1
    for rel, (mode, _bid) in sorted(want.items()):
        if rel in seen:
            continue
        if mode == "120000":
            devs.append(("MISSING-SYMLINK", rel))
            counts["missing_symlink"] += 1
        else:
            devs.append(("MISSING", rel))
            counts["missing"] += 1
    summary = " ".join(f"{k}={v}" for k, v in counts.items())
    out.write(f"ROOT\t{root}\t{repo}\t{sha}\t{summary}\n")
    for verdict, rel in devs:
        out.write(f"DEV\t{root}\t{verdict}\t{rel}\n")
    return summary


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    out_path = Path(argv[1])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    status = 0
    with out_path.open("w", encoding="utf-8") as out:
        for layout_s in argv[2:]:
            layout = Path(layout_s).resolve()
            for sha_file in sorted(layout.glob("*.sha")):
                repo = sha_file.stem
                root = layout / repo
                if not root.is_dir():
                    print(f"NO-DIR\t{root}", file=sys.stderr)
                    status = 1
                    continue
                sha = sha_file.read_text().strip()
                try:
                    summary = check(root, repo, sha, out)
                except (subprocess.CalledProcessError, RuntimeError, json.JSONDecodeError) as exc:
                    print(f"ERROR\t{root}\t{exc}", file=sys.stderr)
                    status = 1
                    continue
                print(f"{layout.parent.name}/{layout.name}/{repo}\t{sha[:8]}\t{summary}")  # two components: pin/src and orig/src differ
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
