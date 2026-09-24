#!/usr/bin/env python3
"""Lane A r2: does the PUBLISHED juniper-data 0.15.0 wheel send any of Appendix E's headers?

Reads the wheel downloaded from PyPI (sha256 verified against PyPI's JSON digest by the caller)
and counts, in every .py member under juniper_data/api/, the tokens E.1 says 0.15.0 lacks.
Positive control: the same census over the scratch tree of juniper-data main (1afc3484), which
must find them -- otherwise a zero from the wheel would mean nothing.
"""
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHEEL = HERE / "pypi" / "juniper_data-0.15.0-py3-none-any.whl"
TREE = HERE / "jd_main_1afc3484"
TOKENS = ["ETag", "etag", "Cache-Control", "If-None-Match", "If-Match", "HTTP_304", "304", "no-cache", "immutable", "Content-Location", "http_cache"]


def census(named_texts):
    counts = {t: 0 for t in TOKENS}
    files_hit = {t: set() for t in TOKENS}
    for name, text in named_texts:
        for t in TOKENS:
            n = len(re.findall(re.escape(t), text))
            if n:
                counts[t] += n
                files_hit[t].add(name)
    return counts, {t: sorted(v) for t, v in files_hit.items() if v}


with zipfile.ZipFile(WHEEL) as z:
    members = [m for m in z.namelist() if m.startswith("juniper_data/api/") and m.endswith(".py")]
    wheel_texts = [(m, z.read(m).decode("utf-8", "replace")) for m in members]
    version_lines = [z.read(m).decode() for m in z.namelist() if m.endswith("METADATA")]
wc, wf = census(wheel_texts)
tree_texts = [(str(p.relative_to(TREE)), p.read_text(encoding="utf-8", errors="replace")) for p in (TREE / "juniper_data" / "api").rglob("*.py")]
tc, tf = census(tree_texts)
print("wheel METADATA Version:", [l for l in version_lines[0].splitlines() if l.startswith("Version:")])
print("wheel api/*.py members:", len(members), "| main api/*.py files:", len(tree_texts))
for t in TOKENS:
    print(f"  {t:17s} wheel={wc[t]:3d}  main={tc[t]:3d}   wheel files: {wf.get(t, [])}")
sys.exit(0)
