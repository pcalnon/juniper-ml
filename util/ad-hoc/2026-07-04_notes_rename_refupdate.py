"""
Rewrite in-repo references to renamed notes/ files (old basename -> new basename).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-07-04
Status: ad-hoc — one-off migration
Retire when: the notes/ naming-convention migration PR is merged and verified
Related: util/ad-hoc/2026-07-04_notes_rename_convention.py (rename generator)

Reads util/ad-hoc/2026-07-04_notes_rename_map.tsv (old-path<TAB>new-path) and
rewrites every git-tracked text file. Because every rename stayed within its
directory, a basename swap preserves any path prefix (relative, repo-relative,
absolute, or GitHub URL). Three old basenames existed in two directories
(top-level + development/ or code-review/); their dir-qualified occurrences are
rewritten first, then bare occurrences fall back to the top-level mapping.
Matches are boundary-guarded so a basename never rewrites inside a longer name.

Usage:  python util/ad-hoc/2026-07-04_notes_rename_refupdate.py [--apply]
Default is a dry run printing per-file replacement counts.
"""

import re
import subprocess
import sys
from pathlib import Path

MAP_TSV = Path("util/ad-hoc/2026-07-04_notes_rename_map.tsv")
SKIP_FILES = {
    "util/ad-hoc/2026-07-04_notes_rename_map.tsv",
    "util/ad-hoc/2026-07-04_notes_rename_convention.py",
    "util/ad-hoc/2026-07-04_notes_rename_refupdate.py",
}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".xcf", ".pdf", ".zip", ".enc", ".woff", ".woff2", ".AppImage"}
BOUNDARY = r"(?<![A-Za-z0-9_.-])"


def load_rules():
    pairs = [line.split("\t") for line in MAP_TSV.read_text().splitlines() if line.strip()]
    by_old_base = {}
    for old, new in pairs:
        by_old_base.setdefault(old.rsplit("/", 1)[-1], []).append((old, new))
    qualified, bare = [], []
    for old_base, entries in by_old_base.items():
        if len(entries) > 1:
            for old, new in entries:
                if "/" in old[len("notes/"):]:  # subdir copy: rewrite dir-qualified form first
                    subdir = old[len("notes/"):].rsplit("/", 1)[0]
                    qualified.append((f"{subdir}/{old_base}", f"{subdir}/{new.rsplit('/', 1)[-1]}"))
                else:  # top-level copy wins the bare-basename fallback
                    bare.append((old_base, new.rsplit("/", 1)[-1]))
        else:
            bare.append((old_base, entries[0][1].rsplit("/", 1)[-1]))
    rules = sorted(qualified, key=lambda r: -len(r[0])) + sorted(bare, key=lambda r: -len(r[0]))
    return [(re.compile(BOUNDARY + re.escape(src)), dst) for src, dst in rules]


def target_files():
    out = []
    for path in subprocess.run(["git", "ls-files"], check=True, capture_output=True, text=True).stdout.splitlines():
        p = Path(path)
        if path in SKIP_FILES or p.suffix in BINARY_EXT or not p.is_file():
            continue
        out.append(p)
    return out


def main():
    apply_edits = "--apply" in sys.argv[1:]
    rules = load_rules()
    total_files = total_hits = 0
    for p in target_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = 0
        for rx, dst in rules:
            text, n = rx.subn(dst, text)
            hits += n
        if hits:
            total_files += 1
            total_hits += hits
            print(f"{hits:5d}  {p}")
            if apply_edits:
                p.write_text(text, encoding="utf-8")
    mode = "APPLIED" if apply_edits else "DRY RUN"
    print(f"{mode}: {total_hits} replacements in {total_files} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
