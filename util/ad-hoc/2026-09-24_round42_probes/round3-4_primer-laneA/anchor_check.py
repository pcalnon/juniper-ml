"""Does #e1-artifact-validator resolve to '### E.1 Artifact validator' under GitHub's slug rules?

GitHub (html-pipeline TableOfContentsFilter / github-slugger): lowercase; drop every character that is
not a word character, space or hyphen (Unicode-aware); each space -> '-'; a repeated slug gets -1, -2...
Headings inside fenced code blocks are not headings. Cross-checked against juniper-doc-tools'
_heading_to_anchor (which has no duplicate numbering)."""

import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map/juniper-doc-tools")
from juniper_doc_tools.check_doc_links import _heading_to_anchor  # noqa: E402

PRIMER = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md")


def gh_slug(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


seen: dict[str, int] = {}
slugs: list[tuple[int, str, str]] = []
in_fence = False
for n, line in enumerate(PRIMER.read_text(encoding="utf-8").split("\n"), start=1):
    if line.lstrip().startswith("```"):
        in_fence = not in_fence
        continue
    if in_fence:
        continue
    m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
    if not m:
        continue
    base = gh_slug(m.group(2))
    k = seen.get(base, 0)
    slug = base if k == 0 else f"{base}-{k}"
    seen[base] = k + 1
    slugs.append((n, m.group(2), slug))

target = "e1-artifact-validator"
hits = [(n, h, s) for n, h, s in slugs if s == target]
print("headings resolving to", target, "->", hits)
print("repo _heading_to_anchor('E.1 Artifact validator') ->", _heading_to_anchor("E.1 Artifact validator"))
dups = [(n, h, s) for n, h, s in slugs if re.search(r"-\d+$", s) and s.rsplit("-", 1)[0] in seen and seen[s.rsplit("-", 1)[0]] > 1]
print("appendix E heading slug:", [s for n, h, s in slugs if h.startswith("Appendix E")])
links = re.findall(r"\]\(#e1-artifact-validator\)", PRIMER.read_text(encoding="utf-8"))
print("links to #e1-artifact-validator in the primer:", len(links))
# any other in-document anchor link in the appendix region that fails to resolve?
text = PRIMER.read_text(encoding="utf-8")
app = text[text.index("## Appendix E"):]
all_slugs = {s for _, _, s in slugs}
for a in re.findall(r"\]\(#([^)]+)\)", app):
    print("appendix link #%s resolves: %s" % (a, a in all_slugs))
