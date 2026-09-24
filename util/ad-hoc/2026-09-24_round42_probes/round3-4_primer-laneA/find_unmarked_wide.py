"""Wider sweep: any pre-appendix line naming juniper-data (or its artifact/checksum/dataset id) together with a
caching / validator / digest term. Prints paragraph-marked status. Complements find_unmarked_candidates.py."""

import re
from pathlib import Path

PRIMER = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md")
MARK = "**[Corrected: E.1](#e1-artifact-validator)**"
lines = PRIMER.read_text(encoding="utf-8").split("\n")
end = next(i for i, ln in enumerate(lines) if ln.startswith("## Appendix E"))
body = lines[:end]
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
fence = [False] * len(body)
state = False
for i, ln in enumerate(body):
    if ln.strip().startswith("```"):
        fence[i] = True
        state = not state
    else:
        fence[i] = state
marked_paras = {para[i] for i, ln in enumerate(body) if MARK in ln}

subject = re.compile(r"juniper[-_]data|Juniper's dataset|dataset_id|DatasetMeta|/artifact|artifacts?\b", re.I)
term = re.compile(r"cach|304|validator|digest|SHA-256|sha256|ETag|immutab|content.address|If-None-Match|If-Match|If-Range|Range|revalidat|max-age|stale", re.I)
for i, ln in enumerate(body):
    if subject.search(ln) and term.search(ln):
        # print paragraph-level context once per paragraph
        status = "MARKED" if para[i] in marked_paras else ("fence " if fence[i] else "UNMARK")
        print(f"{i + 1:5d} [{status}] {ln[:200]}")
