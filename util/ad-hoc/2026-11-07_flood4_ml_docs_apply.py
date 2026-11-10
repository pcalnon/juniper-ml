#!/usr/bin/env python3
"""
Re-apply Cursor flood-4 docs drafts' OWN hunks onto main's files by context search, then apply recorded fixes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs-carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md;
         util/ad-hoc/2026-11-07_flood4_ml_docs_extract.py (produces the stamp-stripped own diffs)

Every fleet docs draft edits the same four docs from a different (stale) base, so `git apply` and a
3-way merge both conflict on the shared insertion points. This applies each hunk by locating its
old block (context + removed lines) in the CURRENT file. When the full block is not found -- usually
because an earlier draft inserted a line at the same anchor -- it trims context from the end, then from
the start (up to all but one context line), and applies at the match nearest the hunk's own line
number. A hunk that still cannot be placed is reported FAILED and left for a hand edit; nothing is
applied silently. A draft's Version History row (`| 0.6.NN  | 2026-...`) is dropped: the carrier adds
one row of its own.

Fixes: --fixes <json> lists {"pr": N, "path": ..., "old": ..., "new": ...}; each `old` must occur
exactly once in the file after all drafts are applied, or the run reports it and changes nothing for it.

Usage: 2026-11-07_flood4_ml_docs_apply.py <worktree> <own-diff-dir> [--fixes F.json] [--log L.txt] -- <N> [<N> ...]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
HISTORY_ROW = re.compile(r"^\| 0\.6\.\d+(\+\d+)? +\| 20\d\d-\d\d-\d\d +\|")


def parse(diff_text: str) -> list[tuple[str, int, list[str]]]:
    """Return (path, old_start, body_lines) per hunk."""
    out: list[tuple[str, int, list[str]]] = []
    path = None
    lines = diff_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            i += 1
            continue
        m = HUNK.match(line)
        if m and path:
            start = int(m.group(1))
            body: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("diff --git "):
                body.append(lines[i])
                i += 1
            while body and body[-1] == "":
                body.pop()
            out.append((path, start, body))
            continue
        i += 1
    return out


def find_block(content: list[str], block: list[str], near: int) -> int | None:
    if not block:
        return None
    hits = [k for k in range(len(content) - len(block) + 1) if content[k : k + len(block)] == block]
    if not hits:
        return None
    return min(hits, key=lambda k: abs(k - near))


def split_groups(start: int, body: list[str], ctx: int = 3) -> list[tuple[int, list[str]]]:
    """Split one hunk into one sub-hunk per change group, each with up to `ctx` context lines a side."""
    body = [b for b in body if not b.startswith("\\")]
    changed = [k for k, b in enumerate(body) if b.startswith(("+", "-"))]
    if not changed:
        return []
    groups: list[list[int]] = [[changed[0]]]
    for k in changed[1:]:
        if k == groups[-1][-1] + 1:
            groups[-1].append(k)
        else:
            groups.append([k])
    def is_ctx(line: str) -> bool:
        return line.startswith(" ") or line == ""

    out: list[tuple[int, list[str]]] = []
    for g in groups:
        lo = g[0]
        while lo > 0 and g[0] - lo < ctx and is_ctx(body[lo - 1]):
            lo -= 1
        hi = g[-1]
        while hi + 1 < len(body) and hi - g[-1] < ctx and is_ctx(body[hi + 1]):
            hi += 1
        old_line = start + sum(1 for b in body[:lo] if b.startswith((" ", "-")) or b == "")
        out.append((old_line, [(" " if b == "" else b) for b in body[lo : hi + 1]]))
    return out


def protected_span(content: list[str], start_heading: str, end_heading: str) -> tuple[int, int] | None:
    try:
        lo = content.index(start_heading)
    except ValueError:
        return None
    try:
        hi = content.index(end_heading, lo + 1)
    except ValueError:
        hi = len(content)
    return lo, hi


def apply_hunk(content: list[str], start: int, body: list[str], protect: tuple[int, int] | None = None) -> tuple[list[str] | None, str]:
    body = [b for b in body if not b.startswith("\\")]
    kept = [b for b in body if not (b.startswith("+") and HISTORY_ROW.match(b[1:]))]
    dropped_rows = len(body) - len(kept)
    if not any(b.startswith(("+", "-")) for b in kept):
        return content, f"history-row-only hunk dropped ({dropped_rows} row)"
    # split into leading context, change core, trailing context
    first = next(k for k, b in enumerate(kept) if b.startswith(("+", "-")))
    last = max(k for k, b in enumerate(kept) if b.startswith(("+", "-")))
    lead = [b[1:] for b in kept[:first]]
    core = kept[first : last + 1]
    trail = [b[1:] for b in kept[last + 1 :]]
    core_old = [b[1:] for b in core if b.startswith((" ", "-"))]
    core_new = [b[1:] for b in core if b.startswith((" ", "+"))]
    # Most context first; ties prefer keeping the leading context (an insertion lands after its anchor).
    attempts = sorted(((ld, t) for ld in range(len(lead) + 1) for t in range(len(trail) + 1)), key=lambda p: (-(p[0] + p[1]), -p[0]))
    for ld, t in attempts:
        use_lead = lead[len(lead) - ld :] if ld else []
        use_trail = trail[:t]
        block = use_lead + core_old + use_trail
        if not use_lead and not use_trail and not core_old:
            continue
        if not core_old and not (use_lead or use_trail):
            continue
        k = find_block(content, block, start - 1 + (len(lead) - ld))
        if k is None:
            continue
        if protect is not None:
            change_lo, change_hi = k + len(use_lead), k + len(use_lead) + max(len(core_old), 1)
            if change_lo < protect[1] and change_hi > protect[0]:
                return content, f"SKIPPED: change at line {change_lo + 1} lies in a protected block (lines {protect[0] + 1}-{protect[1]})"
        new = content[:k] + use_lead + core_new + use_trail + content[k + len(block) :]
        note = "exact" if (ld == len(lead) and t == len(trail)) else f"fuzz lead={ld}/{len(lead)} trail={t}/{len(trail)}"
        if dropped_rows:
            note += f"; {dropped_rows} history row dropped"
        return new, f"{note} at line {k + 1}"
    return None, "FAILED: no placement"


def main(argv: list[str]) -> int:
    if "--" not in argv:
        print(__doc__)
        return 2
    sep = argv.index("--")
    opts = argv[1:sep]
    prs = argv[sep + 1 :]
    root, diff_dir = Path(opts[0]), Path(opts[1])
    fixes_path = log_path = None
    if "--fixes" in opts:
        fixes_path = Path(opts[opts.index("--fixes") + 1])
    if "--log" in opts:
        log_path = Path(opts[opts.index("--log") + 1])
    # --protect PATH::START_HEADING::END_HEADING (repeatable): never change lines between the two headings.
    protects: list[tuple[str, str, str]] = []
    for k, o in enumerate(opts):
        if o == "--protect":
            p_path, p_start, p_end = opts[k + 1].split("::")
            protects.append((p_path, p_start, p_end))
    log: list[str] = []
    failed = 0
    cache: dict[str, list[str]] = {}

    def load(rel: str) -> list[str]:
        if rel not in cache:
            cache[rel] = (root / rel).read_text(encoding="utf-8").split("\n")
        return cache[rel]

    for n in prs:
        hunks = parse((diff_dir / f"{n}.diff").read_text(encoding="utf-8"))
        for idx, (rel, start, body) in enumerate(hunks):
            for gidx, (gstart, gbody) in enumerate(split_groups(start, body)):
                span = None
                for p_path, p_start, p_end in protects:
                    if p_path == rel:
                        span = protected_span(load(rel), p_start, p_end)
                new, note = apply_hunk(load(rel), gstart, gbody, span)
                if new is None:
                    failed += 1
                else:
                    cache[rel] = new
                log.append(f"#{n} hunk {idx + 1}.{gidx + 1} {rel} @-{gstart}: {note}")
    if fixes_path is not None:
        with open(fixes_path, encoding="utf-8") as fh:
            fixes = json.load(fh)
        for fx in fixes:
            if "move" in fx:
                # Markers are line PREFIXES. Cut from the first line starting with `from` up to (not including)
                # the first run of lines after it matching the `to_excl` prefixes; optionally take the blank line
                # just before the block too (`take_blank_before`). Drop the block's `strip_tail` lines and
                # re-insert it, plus one blank line, before the one run of lines matching the `before` prefixes.
                mv = fx["move"]
                lines = load(fx["path"])

                def run_at(seq: list[str], k: int, prefixes: list[str]) -> bool:
                    return k + len(prefixes) <= len(seq) and all(seq[k + n].startswith(p) for n, p in enumerate(prefixes))

                starts = [k for k, ln in enumerate(lines) if ln.startswith(mv["from"])]
                ends = [k for k in range(starts[0] + 1, len(lines)) if run_at(lines, k, mv["to_excl"])] if len(starts) == 1 else []
                if len(starts) != 1 or not ends:
                    failed += 1
                    log.append(f"FIX #{fx['pr']} {fx['path']}: FAILED move markers (from x{len(starts)}, to_excl found={bool(ends)})")
                    continue
                i, j = starts[0], ends[0]
                cut_from = i - 1 if mv.get("take_blank_before") and i > 0 and lines[i - 1] == "" else i
                block = lines[i:j]
                tail = mv.get("strip_tail", [])
                if tail and block[-len(tail) :] == tail:
                    block = block[: -len(tail)]
                rest = lines[:cut_from] + lines[j:]
                before = mv["before"]
                hits = [k for k in range(len(rest)) if run_at(rest, k, before)]
                if len(hits) != 1:
                    failed += 1
                    log.append(f"FIX #{fx['pr']} {fx['path']}: FAILED move target occurs {len(hits)}x")
                    continue
                k = hits[0]
                cache[fx["path"]] = rest[:k] + block + [""] + rest[k:]
                log.append(f"FIX #{fx['pr']} {fx['path']}: moved {len(block)} lines ({fx.get('why', '')[:80]})")
                continue
            text = "\n".join(load(fx["path"]))
            count = text.count(fx["old"])
            if count != 1:
                failed += 1
                log.append(f"FIX #{fx['pr']} {fx['path']}: FAILED old occurs {count}x: {fx['old'][:90]!r}")
                continue
            cache[fx["path"]] = text.replace(fx["old"], fx["new"]).split("\n")
            log.append(f"FIX #{fx['pr']} {fx['path']}: applied ({fx.get('why', '')[:80]})")
    for rel, lines in cache.items():
        (root / rel).write_text("\n".join(lines), encoding="utf-8")
    text = "\n".join(log) + f"\nFAILED={failed}\n"
    print(text)
    if log_path is not None:
        log_path.write_text(text, encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
