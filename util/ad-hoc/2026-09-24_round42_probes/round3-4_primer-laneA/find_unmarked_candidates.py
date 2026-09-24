"""List primer lines (before Appendix E) that make juniper-data artifact/checksum/immutability claims,
and say whether each sits in a rendered paragraph that carries the E.1 marker."""

import re
from pathlib import Path

PRIMER = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md")
MARK = "**[Corrected: E.1](#e1-artifact-validator)**"
lines = PRIMER.read_text(encoding="utf-8").split("\n")
end = next(i for i, ln in enumerate(lines) if ln.startswith("## Appendix E"))
body = lines[:end]

# paragraph id per line (blank-line / fence delimited); fenced code blocks are their own paragraphs
para = [0] * len(body)
pid = 0
in_fence = False
for i, ln in enumerate(body):
    if ln.strip().startswith("```"):
        pid += 1
        in_fence = not in_fence
    elif ln.strip() == "" and not in_fence:
        pid += 1
    para[i] = pid
marked_paras = {para[i] for i, ln in enumerate(body) if MARK in ln}

pat = re.compile(r"immutable|content-address|content address|checksum|strong validator|strong `ETag`|cannot change|cannot have changed|max-age=31536000|juniper.data.*ETag|ETag.*juniper.data|conditional GET|artifact.*ETag|record_access|access_count", re.I)
for i, ln in enumerate(body):
    if pat.search(ln) and ("juniper" in ln.lower() or "checksum" in ln.lower() or "artifact" in ln.lower() or "record_access" in ln or "access_count" in ln or "max-age=31536000" in ln):
        flag = "MARKED-PARA" if para[i] in marked_paras else "unmarked"
        print(f"{i + 1:5d} [{flag:11s}] {ln[:230]}")
