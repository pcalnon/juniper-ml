"""
Fix a sibling repo's inbound links to juniper-ml's renamed notes/ files.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-07-04
Status: ad-hoc — one-off migration
Retire when: all sibling link-fix PRs from the notes/ naming migration are merged
Related: juniper-ml#620 (rename PR); util/ad-hoc/2026-07-04_notes_rename_map.tsv

Rewrites old->new basenames ONLY where the surrounding path proves the
reference targets juniper-ml's notes tree (`juniper-ml/notes/...`, incl.
absolute paths and GitHub blob/tree URLs). Bare basenames are left alone —
a sibling's own notes/ may hold a coincidentally identical name.

Usage:
  python 2026-07-04_notes_rename_sibling_links.py --repo-dir <sibling> \
      [--map <tsv>] [--apply]
Default is a dry run printing per-file hit counts. Exit 0 always.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ML_CTX = r"(?<![A-Za-z0-9-])juniper-ml(?:/(?:blob|tree)/[^\s/]+)?/notes/[^\s`\"'()\[\]]*?"
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".xcf", ".pdf", ".zip", ".enc", ".npz", ".pt", ".woff", ".woff2"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-dir", required=True)
    ap.add_argument("--map", default=str(Path(__file__).parent / "2026-07-04_notes_rename_map.tsv"))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_dir).resolve()
    rules = []
    for line in Path(args.map).read_text().splitlines():
        old, new = line.split("\t")
        old_base, new_base = old.rsplit("/", 1)[-1], new.rsplit("/", 1)[-1]
        rules.append((re.compile(f"({ML_CTX}){re.escape(old_base)}"), new_base))
    tracked = subprocess.run(["git", "-C", str(repo), "ls-files"], check=True, capture_output=True, text=True).stdout.splitlines()
    total_files = total_hits = 0
    for rel in tracked:
        p = repo / rel
        if p.suffix in BINARY_EXT or not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = 0
        for rx, new_base in rules:
            text, n = rx.subn(lambda m, nb=new_base: m.group(1) + nb, text)
            hits += n
        if hits:
            total_files += 1
            total_hits += hits
            print(f"{hits:5d}  {rel}")
            if args.apply:
                p.write_text(text, encoding="utf-8")
    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"{mode} [{repo.name}]: {total_hits} link updates in {total_files} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
