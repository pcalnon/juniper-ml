#!/usr/bin/env python3
"""
Keep a cleanup target's evidence as the 2026-10-30 script does, and also skip the ``main`` tarball extracts that a
pristine check verified, keeping only the files in them that differ from their commit's tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-04
Status: ad-hoc — one-off (flood-3: the predecessor worktree's cleanup, owner ruling 2026-11-04 "Remove; keep evidence")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-30_worktree_cleanup_keep_evidence.py (the copy, skip and verify logic this runs);
         util/ad-hoc/2026-11-04_tarball_extract_pristine_check.py (writes ``extracts.tsv``);
         notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§6, §8)

Why this exists
---------------
The 2026-10-30 script skips virtualenvs, bytecode caches, pytest temp dirs and a base export or tar, and copies the
rest of ``tmp/``. The predecessor worktree's ``tmp/`` is 723 MB, and about 600 MB of it is ``main`` tarball
extracts at recorded SHAs, which that script would copy. Skipping them by name would be wrong, because one copy was
edited in place (the pin lane's ``CHANGELOG.md`` and ``agents-md-touch-up.yml`` in seven repositories). So this:

- reads the pristine check's ``ROOT`` rows and treats exactly those directories as regenerable
  (``SKIPPED-REGEN:extract@<sha8>`` in the MANIFEST, with their file count and size);
- runs the 2026-10-30 script unchanged otherwise;
- then copies every ``EDITED`` and ``EXTRA`` file the check found in a skipped extract (``EXTRA-PYCACHE`` and the
  ``MISSING`` kinds need no copy), as MANIFEST rows ``KEPT-EXTRACT-EDITED`` / ``KEPT-EXTRACT-EXTRA``, and re-hashes
  each copy.

    python3 -I util/ad-hoc/2026-11-04_worktree_cleanup_keep_evidence_skip_extracts.py <dest-root> <targets.tsv> <extracts.tsv>

``targets.tsv`` is the 2026-10-30 script's input, unchanged. Every extract root must lie under one of its worktrees.
Exit 0 when every copy verified, 1 on a mismatch, an unreadable file or an extract outside every target, 2 on bad
arguments.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEEP_KINDS = {"EDITED", "EXTRA"}


def _load_keep():
    spec = importlib.util.spec_from_file_location("worktree_cleanup_keep_evidence", HERE / "2026-10-30_worktree_cleanup_keep_evidence.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_extracts(path: Path) -> tuple[dict[str, str], dict[str, list[tuple[str, str]]]]:
    """({root: sha}, {root: [(verdict, rel)]}) from the pristine check's output."""
    roots: dict[str, str] = {}
    devs: dict[str, list[tuple[str, str]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        cols = line.split("\t")
        if cols[0] == "ROOT":
            roots[os.path.abspath(cols[1])] = cols[3]
        elif cols[0] == "DEV":
            devs.setdefault(os.path.abspath(cols[1]), []).append((cols[2], cols[3]))
    return roots, devs


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    dest_root, targets, extracts = Path(argv[1]), Path(argv[2]), Path(argv[3])
    roots, devs = read_extracts(extracts)
    worktrees = [Path(line.split("\t")[0]).resolve() for line in targets.read_text().splitlines() if line.strip() and not line.startswith("#")]
    owner: dict[str, Path] = {}
    for root in roots:
        hits = [wt for wt in worktrees if Path(root).is_relative_to(wt)]
        if len(hits) != 1:
            print(f"ERROR extract outside every target (or in two): {root}", file=sys.stderr)
            return 1
        owner[root] = hits[0]

    keep = _load_keep()
    original = keep.regen_reason

    def regen_reason(path: Path, name: str) -> str | None:
        reason = original(path, name)
        if reason:
            return reason
        sha = roots.get(os.path.abspath(path))
        return f"extract@{sha[:8]}" if sha and path.is_dir() and not path.is_symlink() else None

    keep.regen_reason = regen_reason  # Target.tmp() looks the name up in its module at call time
    saved = sys.argv
    sys.argv = [saved[0], str(dest_root), str(targets)]  # the 2026-10-30 main() reads its arguments from sys.argv
    try:
        status = keep.main()
    finally:
        sys.argv = saved

    kept = bad = 0
    with (dest_root / "MANIFEST.tsv").open("a", encoding="utf-8") as manifest:
        for root, rows in sorted(devs.items()):
            wt = owner.get(root)
            if wt is None:
                continue
            for verdict, rel in rows:
                if verdict not in KEEP_KINDS:
                    continue
                src = Path(root) / rel
                rel_wt = str(src.relative_to(wt))
                dst = dest_root / wt.name / rel_wt
                try:
                    digest = keep.sha256(src)
                    keep.copy_one(src, dst)
                    again = keep.sha256(dst)
                except OSError as exc:
                    print(f"  ERROR {rel_wt}: {exc}")
                    bad += 1
                    continue
                if again != digest:
                    print(f"  MISMATCH {dst}")
                    bad += 1
                    continue
                manifest.write(f"{wt.name}\tTMP\tKEPT-EXTRACT-{verdict}\t{rel_wt}\t{digest}\n")
                kept += 1
    print(f"extract deviations kept={kept}\tbad={bad}")
    return 1 if (status or bad) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
