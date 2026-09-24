#!/usr/bin/env python3
"""Render-level check of PR #2075's markers with markdown-it-py (CommonMark + GFM tables).

Scratch instrument for round-2 Lane B. Local rendering only; nothing is sent anywhere.

1. Renders base (9866 lines) and head's first 9866 lines. Every rendered block that differs must,
   after deleting exactly the marker's rendered HTML, equal the base block -- unless it is a code
   block (the declared II.11 / II.3 rewrites) or one of the two declared prose rewrites (L5, L4222).
   A marker that broke emphasis, a code span, a link or a table would leave a residual difference.
2. Confirms each marker renders as <strong><a href="#eN-...">Corrected: E.N</a></strong>.
3. Computes GitHub-style slugs (github-slugger semantics, with -N de-duplication) for every heading
   outside code fences and resolves the three fragments the PR uses.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt

HERE = Path(__file__).resolve().parent
MD = MarkdownIt("commonmark").enable("table")
MARK_HTML = re.compile(r' ?<strong><a href="#e([12])-[a-z-]+">Corrected: E\.\1</a></strong>')


def blocks(text: str) -> list[tuple[tuple[int, int], str]]:
    tokens = MD.parse(text)
    out = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.level == 0 and t.map is not None:
            # find the matching close for *_open tokens, else a single token (fence, hr, html_block)
            if t.nesting == 1:
                depth, j = 1, i + 1
                while depth:
                    depth += tokens[j].nesting
                    j += 1
                seg = tokens[i:j]
                i = j
            else:
                seg = [t]
                i += 1
            html = MD.renderer.render(seg, MD.options, {})
            out.append(((t.map[0] + 1, t.map[1]), html))
        else:
            i += 1
    return out


def slug(text: str) -> str:
    # github-slugger: lowercase, drop characters that are not letters/numbers/marks/connectors,
    # spaces or hyphens, then spaces -> hyphens. Inline markup is stripped first (GitHub slugs the
    # rendered text).
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    text = text.lower()
    text = "".join(ch for ch in text if ch.isalnum() or ch in " -_" or ch == "‍")
    return text.replace(" ", "-")


def main() -> int:
    base = (HERE / "primer_base.md").read_text(encoding="utf-8")
    head_full = (HERE / "primer_head.md").read_text(encoding="utf-8")
    head = "\n".join(head_full.split("\n")[:9866]) + "\n"
    bb, hb = blocks(base), blocks(head)
    print(f"blocks: base {len(bb)}, head(first 9866 lines) {len(hb)}")
    if len(bb) != len(hb):
        print("BLOCK COUNT DIFFERS -- a marker changed block structure")
    diffs = 0
    for (rb, b), (rh, h) in zip(bb, hb):
        if b == h:
            continue
        diffs += 1
        stripped, n = MARK_HTML.subn("", h)
        kind = "code" if h.lstrip().startswith("<pre>") else "prose"
        if stripped == b and n == 1:
            verdict = "OK: differs only by one rendered marker"
        elif kind == "code":
            verdict = "code block rewritten (declared)"
        else:
            verdict = f"RESIDUAL DIFFERENCE after removing {n} marker(s)"
        print(f"  lines {rh[0]}-{rh[1]} [{kind}] {verdict}")
        if verdict.startswith("RESIDUAL"):
            import difflib

            for d in difflib.unified_diff(b.splitlines(), stripped.splitlines(), lineterm="", n=0):
                print("     ", d[:300])
    print(f"differing blocks: {diffs}")

    # 3. slugs over the whole head document
    seen: dict[str, int] = {}
    anchors: dict[str, tuple[int, str]] = {}
    fence = False
    for i, ln in enumerate(head_full.split("\n"), start=1):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", ln)
        if not m:
            continue
        s = slug(m.group(2))
        if s in seen:
            seen[s] += 1
            s2 = f"{s}-{seen[s]}"
        else:
            seen[s] = 0
            s2 = s
        anchors[s2] = (i, ln)
    for frag in ("appendix-e--corrections", "e1-artifact-validator", "e2-conditional-tag-writes", "appendix-d--running-the-examples"):
        hit = anchors.get(frag)
        dup = seen.get(frag, 0)
        print(f"#{frag}: {'line %d %r' % hit if hit else 'UNRESOLVED'}; duplicates of base slug: {dup}")
    used = set(re.findall(r"\]\(#([^)\s]+)\)", head_full))
    missing = sorted(u for u in used if u not in anchors)
    print(f"in-document fragment links: {len(used)} distinct; unresolved under this slugger: {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
