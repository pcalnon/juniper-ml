#!/usr/bin/env python3
"""Lane A: do the facts this change corrected survive, in their OLD form, anywhere else in the live tree?

Searches every .md/.py/.yml file of the head tree (eco/juniper-ml) EXCEPT the archives (reports/, prompts/,
notes/history/, notes/legacy/, CHANGELOG.md) for phrasings of the corrected claims, printing hits with context.
"""
import pathlib
import re

S = pathlib.Path(__file__).resolve().parent
ML = S / "eco/juniper-ml"
PATTERNS = {
    "all anchors fixed by #2080": r"corrected all the rest|nothing left to shift|every anchor past it was three short",
    "notes link into both": r"link into both|fails on a missing sibling",
    "skip only those forks": r"skip only those forks",
    "record_access every read": r"every metadata read|fires on every",
    "two lock-less writers": r"Neither of those two takes the lock, so|batch-tags` and `DELETE` took",
    "#2071 then added": r"#2071\]\([^)]*\) then added|#2071 then added",
    "sibling group closed 08-21": r"sibling-package-drift group is CLOSED\*\* \(2026-08-21\)",
    "seventh of the kind (end)": r"seventh of the kind, one where the shared package was itself among the drifted copies\. The other",
    "#2059 closed 09-24": r"#2059[^.]{0,80}closed 2026-09-24\)",
    "row-level sentence": r"row-level sentence",
    "reads (ruling quote)": r"which the owner was shown, reads",
    "43 anchors": r"43 anchors",
}
EXCL = re.compile(r"^(reports/|prompts/|notes/history/|notes/legacy/|CHANGELOG\.md)")
for f in sorted(ML.rglob("*")):
    if not f.is_file() or f.suffix not in (".md", ".py", ".yml", ".yaml"):
        continue
    rel = str(f.relative_to(ML))
    if EXCL.match(rel):
        continue
    try:
        text = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for label, pat in PATTERNS.items():
        for m in re.finditer(pat, text):
            ln = text.count("\n", 0, m.start()) + 1
            ctx = text[max(0, m.start() - 90) : m.end() + 60].replace("\n", " / ")
            print(f"[{label}] {rel}:{ln}: ...{ctx}...")
