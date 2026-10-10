#!/usr/bin/env python3
"""
Screen the lines the line read prints for a PR's new or changed files, without printing any of their text.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-05_masked_finding_shape.py (the read whose --names output this takes);
         reports/2026-10-04_consolidated-development-plan/round12-reconciliation.md (tools row 3)

Since round 12 the line read masks names too, so its output alone no longer shows what a listed line holds. This
screens, in-process, every line ``--names`` printed (listed, above or below) in the files that are new or changed
against an earlier set of copies: each run of 12 or more letters that is neither a dictionary word nor a camel-case
join of them is checked against the text of the repository's tracked files on disk. The output names each such run
only by its masked shape, and says whether it occurs in tracked text, how many PR files hold it, and whether it is
random-looking. A run absent from the repository and random-looking is the one to read by hand, masked.

Usage
-----
    git ls-files > tracked.txt   # run in the repository first
    python3 -B util/ad-hoc/2026-10-08_pr_printed_line_screen.py --new <copies> --old <earlier copies> \\
        --names-output <read --names stdout> --tracked tracked.txt [--words /usr/share/dict/words]
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

READ = Path(__file__).resolve().parent / "2026-10-05_masked_finding_shape.py"


def printed_lines(names_out: Path) -> dict:
    printed, cur, pend = {}, None, []
    for line in names_out.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^(\S+):(\d+) len=", line)
        if m:
            cur = m.group(1)
            printed.setdefault(cur, set()).update([int(m.group(2))] + pend)
            pend = []
            continue
        m = re.match(r"^    above L(\d+) ", line)
        if m:
            pend.append(int(m.group(1)))
            continue
        m = re.match(r"^    below L(\d+) ", line)
        if m and cur:
            printed[cur].add(int(m.group(1)))
    return printed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--new", required=True, type=Path)
    ap.add_argument("--old", required=True, type=Path)
    ap.add_argument("--names-output", required=True, type=Path)
    ap.add_argument("--tracked", required=True, type=Path)
    ap.add_argument("--words", default="/usr/share/dict/words", type=Path)
    args = ap.parse_args()
    spec = importlib.util.spec_from_file_location("line_read", READ)
    read = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(read)
    words = {w.strip().lower() for w in args.words.read_text(encoding="utf-8", errors="ignore").split("\n")}

    def wordy(run: str) -> bool:
        return run.lower() in words or all(p.lower() in words or len(p) <= 3 for p in re.split(r"(?<=[a-z])(?=[A-Z])", run))

    new_files = sorted(p for p in args.new.rglob("*") if p.is_file())
    changed = [p.relative_to(args.new).as_posix() for p in new_files
               if not (args.old / p.relative_to(args.new)).exists() or (args.old / p.relative_to(args.new)).read_bytes() != p.read_bytes()]
    printed = printed_lines(args.names_output)
    runs, lines_seen, lines_flagged = set(), 0, 0
    for rel in changed:
        lines = read._read(args.new / rel)
        for n in sorted(printed.get(rel, ())):
            lines_seen += 1
            odd = {x for x in re.findall(r"[A-Za-z]{12,}", lines[n - 1]) if not wordy(x)}
            lines_flagged += bool(odd)
            runs |= odd
    corpus = set()
    for rel in args.tracked.read_text(encoding="utf-8").split("\n"):
        p = Path(rel)
        if rel and p.is_file() and p.stat().st_size < 5_000_000:
            try:
                corpus |= set(re.findall(r"[a-z]{12,}", p.read_text(encoding="utf-8").lower()))
            except (UnicodeDecodeError, OSError):
                pass  # a binary or unreadable tracked file adds no words to the corpus
    texts = [p.read_text(encoding="utf-8") for p in new_files]
    print(f"{len(changed)} new or changed file(s); {lines_seen} printed line(s) in them; {lines_flagged} hold a 12+ letter run that is not dictionary words; {len(runs)} distinct run(s)")
    unexplained = 0
    for x in sorted(runs, key=len):
        on_main = any(x.lower() in c for c in corpus if len(c) >= len(x))
        rl = read.random_looking(x)
        unexplained += (not on_main) and bool(rl)
        compound = any(x[:i].lower() in words and x[i:].lower() in words for i in range(3, len(x) - 2))
        print(f"  {read.mask(x)}: in tracked text {on_main}; two dictionary words joined {compound}; in {sum(x in t for t in texts)} PR file(s); random-looking {rl}")
    print(f"absent from tracked text AND random-looking: {unexplained}")
    return 1 if unexplained else 0


if __name__ == "__main__":
    sys.exit(main())
