#!/usr/bin/env python3
"""Lane A r2: resolve every in-document #fragment link in the primer under GitHub's heading-slug rules.

Slugger modelled on github-slugger (the algorithm GitHub uses for heading ids): lowercase, drop the
punctuation set (ASCII punctuation except '-' and '_', plus Unicode general punctuation such as the
em dash), spaces -> '-', and a '-N' suffix for the Nth duplicate. Headings inside fenced code are
skipped; inline markup is reduced to its text first (links -> link text, emphasis markers dropped).
Cross-check: juniper_doc_tools.check_doc_links._heading_to_anchor from the PR head tree.
Runs on both base and head so a link the PR broke (or fixed) shows up as a set difference.
"""
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "doctools" / "juniper-doc-tools"))
from juniper_doc_tools.check_doc_links import _heading_to_anchor  # noqa: E402


def gh_slug_base(text: str) -> str:
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> text
    t = t.lower()
    out = []
    for ch in t:
        cat = unicodedata.category(ch)
        if ch in "-_ ":
            out.append(ch)
        elif cat[0] in ("L", "N") or cat in ("Mn", "Mc"):
            out.append(ch)
        # everything else (punctuation P*, symbols S*) is dropped
    return "".join(out).replace(" ", "-")


def headings(md: str):
    res, seen, fence = [], {}, None
    for i, line in enumerate(md.split("\n"), start=1):
        s = line.strip()
        m = re.match(r"^(`{3,}|~{3,})", s)
        if m:
            if fence is None:
                fence = m.group(1)[0] * 3
            elif s.startswith(fence):
                fence = None
            continue
        if fence:
            continue
        h = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if h:
            base = gh_slug_base(h.group(2))
            n = seen.get(base, 0)
            slug = base if n == 0 else f"{base}-{n}"
            seen[base] = n + 1
            res.append((i, h.group(2), slug))
    return res


def links(md: str):
    out, fence = [], None
    for i, line in enumerate(md.split("\n"), start=1):
        s = line.strip()
        m = re.match(r"^(`{3,}|~{3,})", s)
        if m:
            fence = (m.group(1)[0] * 3) if fence is None else (None if s.startswith(fence) else fence)
            continue
        if fence:
            continue
        for lm in re.finditer(r"\]\(#([^)\s]+)\)", line):
            out.append((i, lm.group(1)))
    return out


def run(path: Path):
    md = path.read_text(encoding="utf-8")
    hs = headings(md)
    slugs = {}
    for ln, txt, sl in hs:
        slugs.setdefault(sl, []).append((ln, txt))
    unresolved = [(ln, fr) for ln, fr in links(md) if fr not in slugs]
    return hs, slugs, links(md), unresolved


for label in ("base", "head"):
    hs, slugs, ls, unresolved = run(HERE / f"primer_{label}.md")
    print(f"== {label}: {len(hs)} headings, {len(ls)} in-doc fragment links, {len(unresolved)} unresolved")
    for ln, fr in unresolved[:40]:
        print(f"   unresolved L{ln} #{fr}")
    if label == "head":
        for frag in ("e1-artifact-validator", "e2-conditional-tag-writes", "appendix-e--corrections"):
            tgt = slugs.get(frag)
            users = [ln for ln, fr in ls if fr == frag]
            print(f"   #{frag}: target={tgt} unique={tgt is not None and len(tgt) == 1} used_on={len(users)} lines {users}")
            if tgt:
                print(f"      doc-tools _heading_to_anchor({tgt[0][1]!r}) = {_heading_to_anchor(tgt[0][1])!r}")
        # any other heading whose base slug would collide with these?
        for ln, txt, sl in hs:
            if sl.startswith(("e1-", "e2-", "appendix-e")):
                print(f"   heading L{ln} {txt!r} -> {sl}")
        base_unres = set(fr for _, fr in run(HERE / "primer_base.md")[3])
        head_unres = set(fr for _, fr in unresolved)
        print(f"   unresolved fragments new at head: {sorted(head_unres - base_unres)}; fixed at head: {sorted(base_unres - head_unres)}")
