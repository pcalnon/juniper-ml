#!/usr/bin/env python3
"""Check the RFC 9110 wording that the primer's Appendix E and its L4222 paraphrase rely on.

Scratch instrument for round-2 Lane B. Reads rfc9110.txt (fetched from www.rfc-editor.org into this
directory), removes page headers/footers, flattens whitespace, and tests each phrase verbatim.
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
t = (HERE / "rfc9110.txt").read_text(encoding="utf-8")
t = re.sub(r"\n\n?Fielding, et al\.[^\n]*\n\f\nRFC 9110[^\n]*\n", "\n", t)
flat = re.sub(r"\s+", " ", t)

CHECKS = {
    "E.1 quote (8.8.1)": "a validator is weak if it is shared by two or more representations of a given resource at the same time, unless those representations have identical representation data",
    "L4222 quoted tail (8.8.1)": "if the data is available prior to the response header fields being sent and the digest does not need to be recalculated every time a validation request is received",
    "L4222 paraphrase basis": "A collision-resistant hash function applied to the representation data is also sufficient",
    "8.8.1 strong definition": "changes value whenever a change occurs to the representation data that would be observable in the content of a 200 (OK) response to GET",
    "8.8.1 unique over time": "A strong validator is unique across all versions of all representations associated with a particular resource over time",
    "13.1.5 client weak ban": "A client MUST NOT generate an If-Range header field containing an entity tag that is marked as weak",
    "13.1.1 strong compare": "An origin server MUST use the strong comparison function when comparing entity tags for If-Match",
    "13.1.2 weak compare": "A recipient MUST use the weak comparison function when comparing entity tags for If-None-Match",
    "8.8.1 gzip example": "if the origin server sends the same validator for a representation with a gzip content coding applied as it does for a representation with no content coding, then that validator is weak",
}
for name, phrase in CHECKS.items():
    print(f"{name:28s} {'VERBATIM' if phrase in flat else 'NOT FOUND'}")

k = flat.rfind("13.1.5. If-Range")
print("\n--- 13.1.5 (flattened, first 1400 chars) ---")
print(flat[k : k + 1400])
