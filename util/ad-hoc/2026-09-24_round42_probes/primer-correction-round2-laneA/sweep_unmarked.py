#!/usr/bin/env python3
"""Lane A r2: sweep the head primer (lines 1..9866) for UNMARKED passages that make the claims
Appendix E corrects, to test E's universal claim "Each affected prose passage keeps its text and
gains a Corrected link" (L9871-9872) and E.1's list of named-but-unmarked passages (L9884-9886).

A paragraph (blank-line delimited, fenced code excluded) is a candidate when it mentions
juniper-data (or its code paths) AND one of the corrected topics. Paragraphs that contain a
marker anywhere are reported as covered. Output is for human review, not a verdict: a regex
sweep cannot decide whether a sentence is false.
"""
import re
from pathlib import Path

S = Path(__file__).resolve().parent
lines = (S / "primer_head.md").read_text(encoding="utf-8").split("\n")[:9866]
JD = re.compile(r"juniper[-_]data|DatasetMeta|compute_checksum|generate_dataset_id|dataset_id\.py|update_dataset_tags|record_access|/v1/datasets|artifacts\.py|download_artifact", re.I)
TOPIC = re.compile(r"ETag|validator|checksum|digest|content[- ]address|immutable|Cache-Control|cache header|max-age|If-None-Match|If-Match|304|conditional|lost update|lost-update|read-modify-write|last writer|version check|_version_lock|Content-Location|caching|cache", re.I)
MARK = re.compile(r"\*\*\[Corrected: E\.\d\]\(#e\d-[a-z-]+\)\*\*")
NAMED = {3426, 3431, 5332}  # named in E.1 L9884-9886

paras, cur, fence = [], [], False
for i, l in enumerate(lines, start=1):
    if l.strip().startswith("```"):
        fence = not fence
        if cur:
            paras.append(cur)
            cur = []
        continue
    if fence:
        continue
    if l.strip() == "":
        if cur:
            paras.append(cur)
            cur = []
    else:
        cur.append((i, l))
if cur:
    paras.append(cur)

covered, named, unmarked = 0, 0, []
for p in paras:
    text = " ".join(l for _, l in p)
    if not (JD.search(text) and TOPIC.search(text)):
        continue
    nums = [n for n, _ in p]
    if MARK.search(text):
        covered += 1
    elif NAMED & set(nums):
        named += 1
    else:
        unmarked.append((nums[0], nums[-1], text))
print(f"candidate paragraphs: covered-by-marker={covered} named-in-E.1={named} unmarked={len(unmarked)}")
for a, b, t in unmarked:
    print(f"--- L{a}-{b}: {t[:600]}")
