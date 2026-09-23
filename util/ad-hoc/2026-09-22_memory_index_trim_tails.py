#!/usr/bin/env python3
"""2026-09-22_memory_index_trim_tails.py -- shrink MEMORY.md by dropping LONG prose tails only.

Project: juniper-ml
Sub-Project: ad-hoc tooling (memory governance)
Application: ad-hoc maintenance
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS -- AND THE RULE IT NEARLY BROKE

The memory index must stay under the owner's 20 KB target, and the standing rule in
`memory/feedback_memory_index_target_is_20kb.md` is **compact by RETIRING entries, never by
stripping hooks**.

**THE FIRST VERSION OF THIS TOOL DEFINED "HOOK" AS THE LINK TEXT, AND THAT IS WRONG.** The
owner's own byte budget lists `titles | 6,522 | mean 30.9 -- the scannable label` and
`hooks | ~4,300 | ~20 bytes per entry` as SEPARATE rows: the title is the link text, the
hook is the `-- ...` tail. The three examples that memory gives for why the index is worth
loading at all -- *"NEVER run it"*, *"`_is_dirty` fails OPEN"*, *"exit 0 != merged"* -- are
tail text. Run with `--keep-under 56` on 2026-09-22, this tool deleted the first two, and
the compaction had to be reverted. The memory closes: *"treat 20 KB as a ceiling to drift
back toward as entries genuinely close, **not a number to hit this week by deleting live
warnings**."*

So this tool now REFUSES to drop a tail that names a hazard (see `HAZARD`), whatever its
length, and says so in its output. What remains safely trimmable is the narrative tail --
the sentence that explains an incident -- which
`util/ad-hoc/2026-09-11_memory_index_preserve.py` has already appended VERBATIM to the
line's topic file.

Measured on the 2026-09-22 index: 17,743 of 25,817 bytes are link markup that must survive
intact. All of the headroom is in the remaining 8,074 bytes of labels, separators and tails,
and the hazard tails inside that are not headroom either.

WHY NOT A REGEX

The obvious `(?<=\\))\\s*--\\s*[^;]*` spans link boundaries and eats the NEXT pointer's hook.
A first attempt at this scored the index at 12,220 bytes, which looked like a triumph and
was actually 5,500 bytes of deleted hooks. This tokenises each line into LINK tokens and the
prose runs between them, and only ever edits a prose run.

WHAT IS KEPT, ALWAYS

  * every `[hook](target.md)` token, byte-identical;
  * the leading prose of a line (its category label, e.g. `Verification discipline: `);
  * any tail at or under `--keep-under` bytes -- these are the operational imperatives
    (`-- do not relitigate`, `-- use gh api -X PATCH`, `-- safe_merge.py`) whose value is
    exactly their being in front of you, not one hop away;
  * the `; ` separators, so the line still reads as a list.

LIMITS -- read before trusting the output

  * IT PROVES NOTHING ABOUT LOSS. Run
    `util/ad-hoc/2026-09-11_memory_index_verify_lossless.py <snapshot>` and
    `util/ad-hoc/2026-09-12_memory_index_linkset.py compare <snapshot>` afterwards; a
    link-count check is set-blind and cannot see a swap.
  * It requires the preserve step to have run first. Dropping a tail whose text exists
    nowhere else is data loss, and this script cannot tell the difference -- the verifier
    can.
  * MEMORY.md is written by several sessions at once. Snapshot immediately before, and
    re-check the mtime before writing.

EXIT CODES

  * 0 -- ran and reported (or wrote, with --apply).
  * 2 -- the index could not be read, or a line's link tokens would not survive the edit
         (a self-check; it refuses rather than writing a line that lost a pointer).

Usage:
    python3 util/ad-hoc/2026-09-22_memory_index_trim_tails.py                 # dry run
    python3 util/ad-hoc/2026-09-22_memory_index_trim_tails.py --keep-under 56 --apply
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

INDEX = pathlib.Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md")

#: A markdown link whose target is a memory file. Nothing inside one is ever edited.
LINK = re.compile(r"\[[^\]]*\]\([^)]+\.md\)")

#: A prose run is a "tail" when it opens with an em dash (optionally after a separator).
TAIL = re.compile(r"^(\s*[;,]?\s*)(—\s*.*)$", re.S)

#: A tail matching any of these NAMES A HAZARD and is never dropped, at any length. The
#: owner's rule is "never strip a hook that names a hazard"; length is not a proxy for
#: imperativeness, and treating it as one is what deleted "NEVER run it" on 2026-09-22.
HAZARD = re.compile(
    r"NEVER|DO NOT|never |do not |must not|cannot|BROKEN|BLOCK|blind|LIES|fails OPEN" r"|≠|!=|WRONG|stale|UNRECOVERABLE|DESTROY|kills|corrupt|silent|hangs|waits FOREVER" r"|first|before|instead|use `|exit 0|refus",
    re.I,
)


def tokenize(line: str) -> "list[tuple[str, str]]":
    """Split into [('link', text) | ('prose', text)] preserving every byte."""
    out: list[tuple[str, str]] = []
    pos = 0
    for m in LINK.finditer(line):
        if m.start() > pos:
            out.append(("prose", line[pos : m.start()]))
        out.append(("link", m.group(0)))
        pos = m.end()
    if pos < len(line):
        out.append(("prose", line[pos:]))
    return out


def trim_line(line: str, keep_under: int) -> "tuple[str, int, list[str]]":
    """Return (new_line, bytes_dropped, hazards_kept). Only prose runs AFTER a link are touched."""
    toks = tokenize(line)
    seen_link = False
    dropped = 0
    kept_hazards: list[str] = []
    out: list[str] = []
    for kind, text in toks:
        if kind == "link":
            seen_link = True
            out.append(text)
            continue
        if not seen_link:
            out.append(text)  # the category label
            continue
        m = TAIL.match(text)
        if m and HAZARD.search(m.group(2)):
            # Owner rule: never strip a hook that names a hazard. Length is irrelevant here.
            kept_hazards.append(m.group(2).strip()[:60])
            out.append(text)
            continue
        if m and len(m.group(2)) > keep_under:
            # A dropped tail must leave its SEPARATOR behind, or the pointers on either
            # side fuse into `...md)[next hook](...` and the line stops being a list.
            # The first version of this omitted it and produced exactly that.
            out.append("; ")
            dropped += len(text) - 2
            continue
        out.append(text)
    new = "".join(out)
    new = re.sub(r"(?:\s*;\s*){2,}", "; ", new)
    new = re.sub(r"[ \t]+$", "", new)
    new = re.sub(r"\s*;\s*$", "", new)
    return new, dropped, kept_hazards


def main(argv: "list[str] | None" = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--keep-under", type=int, default=56, help="keep tails of at most N bytes (default 56)")
    p.add_argument("--apply", action="store_true", help="write the index (default: dry run)")
    p.add_argument("--index", default=str(INDEX))
    args = p.parse_args(argv)

    path = pathlib.Path(args.index)
    try:
        original = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 2

    lines = original.splitlines()
    before_links = LINK.findall(original)

    new_lines: list[str] = []
    total_dropped = 0
    touched = 0
    hazards: list[str] = []
    for line in lines:
        new, dropped, kept = trim_line(line, args.keep_under)
        hazards.extend(kept)
        if dropped:
            touched += 1
            total_dropped += dropped
        new_lines.append(new)

    new_text = "\n".join(new_lines) + ("\n" if original.endswith("\n") else "")
    after_links = LINK.findall(new_text)

    # Self-check: a trim that loses a pointer is the failure this tool exists to avoid.
    if before_links != after_links:
        lost = [x for x in before_links if x not in after_links]
        print(f"REFUSING: link tokens changed ({len(before_links)} -> {len(after_links)})", file=sys.stderr)
        for x in lost[:10]:
            print(f"   lost: {x[:100]}", file=sys.stderr)
        return 2

    print(f"index {len(original.encode())} -> {len(new_text.encode())} bytes " f"({total_dropped} dropped across {touched} line(s)); links {len(before_links)} -> {len(after_links)}")
    print(f"target 20480: {'MET' if len(new_text.encode()) <= 20480 else 'NOT met'}")
    print(f"hazard tails KEPT regardless of length: {len(hazards)}")
    for h in hazards[:8]:
        print(f"    kept: {h}")
    if len(new_text.encode()) > 20480:
        print("\nStill over target with every hazard tail intact. That is the CORRECT outcome:")
        print("20 KB is a ceiling to drift back toward as entries genuinely close, NOT a number")
        print("to hit this week by deleting live warnings. Retire entries instead --")
        print("util/ad-hoc/2026-09-12_memory_index_linkset.py unreachable")
    if not args.apply:
        print("\n(dry run -- pass --apply to write)")
        return 0

    path.write_text(new_text, encoding="utf-8")
    print(f"wrote {path}")
    print("NOW VERIFY: 2026-09-11_memory_index_verify_lossless.py <snapshot> " "and 2026-09-12_memory_index_linkset.py compare <snapshot>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
