#!/usr/bin/env python3
"""Lane A: are the register's two owner-ruling quotes exact openings of the archived descriptions, cut where the
ellipsis says, and does owner-rulings-verbatim.md hold each description in full (i.e. longer than the quote)?

Parses the "label"/"description" JSON pairs in owner-rulings-verbatim.md, then extracts each quote from the head
register (the text between `begins "` and ` …"`), normalising the register's hard line wraps to single spaces.
"""
import json
import pathlib
import re

S = pathlib.Path(__file__).resolve().parent
v = (S / "eco/juniper-ml/reports/2026-09-24_defect-register-round-42/owner-rulings-verbatim.md").read_text(encoding="utf-8")
reg = (S / "head/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md").read_text(encoding="utf-8")

pairs = re.findall(r'"label":\s*("(?:[^"\\]|\\.)*"),\s*"description":\s*("(?:[^"\\]|\\.)*")', v)
desc = {json.loads(a): json.loads(b) for a, b in pairs}
for label in ("Keep while fetched splits stay (Recommended)", "Keep while any split is fetched (Recommended)"):
    print(f"label {label!r}: archived description {len(desc[label])} chars")

block = reg[reg.index("Mixed provenance RULED 2026-09-24") : reg.index("each description in full, are archived verbatim")]
flat = re.sub(r"\s*\n\s*", " ", block)
quotes = re.findall(r'begins "(.*?) …"', flat)
print("quotes found:", len(quotes))
for q, label in zip(quotes, ("Keep while fetched splits stay (Recommended)", "Keep while any split is fetched (Recommended)")):
    d = desc[label]
    print(f"- quote ({len(q)} chars) is a prefix of the description: {d.startswith(q)}; remainder: {d[len(q):][:160]!r}")
