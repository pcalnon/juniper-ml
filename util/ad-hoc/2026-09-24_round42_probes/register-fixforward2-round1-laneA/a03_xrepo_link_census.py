#!/usr/bin/env python3
"""Lane A: census of juniper-ml's cross-repo links, using the checker's OWN classification.

Runs juniper_doc_tools.check_doc_links.validate_file (imported from the head tree, which equals the PyPI 0.1.2
wheel docs-full-check.yml installs) in "warn" mode, which prints one "WARN (cross-repo): <rel>:<line> -> <path>"
line per link that CROSS_REPO_PATTERN classifies, after its own code-fence and inline-code stripping. Excludes
are the workflow's: templates, history, legacy. Reports per-repo link counts AND distinct-file counts.
"""
import collections
import contextlib
import io
import pathlib
import re
import sys

S = pathlib.Path(__file__).resolve().parent
ML = S / "eco/juniper-ml"
sys.path.insert(0, str(ML / "juniper-doc-tools"))
from juniper_doc_tools import check_doc_links as cdl  # noqa: E402
from juniper_doc_tools._ecosystem import CROSS_REPO_PATTERN  # noqa: E402

files = cdl._find_markdown_files([ML], ML, {"templates", "history", "legacy"})
print("scanned files:", len(files))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    for f in files:
        cdl.validate_file(f, ML, cross_repo_mode="warn", ecosystem_root=None)
links = collections.defaultdict(list)
eco_root_links = 0
for line in buf.getvalue().splitlines():
    m = re.match(r"\s*WARN \(cross-repo\): (.+?):(\d+) -> (.+)$", line)
    if m:
        repo = CROSS_REPO_PATTERN.match(m.group(3)).group(1)
        links[repo].append((m.group(1), int(m.group(2)), m.group(3)))
    elif "WARN (ecosystem-root)" in line:
        eco_root_links += 1
for repo in sorted(links):
    fs = sorted({x[0] for x in links[repo]})
    print(f"{repo}: {len(links[repo])} links in {len(fs)} files")
    for src, ln, tgt in links[repo]:
        print(f"    {src}:{ln} -> {tgt}")
print("juniper-data links:", len(links.get("juniper-data", [])))
print("ecosystem-root links (warn):", eco_root_links)

# a cross-check with a naive regex (no fence/inline stripping), to see whether the checker's stripping hides any
naive = collections.Counter()
for f in files:
    for ln, text in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for mm in re.finditer(r"\]\((?:\.\./)*(juniper-data)/", text):
            naive[str(f.relative_to(ML))] += 1
print("naive (unstripped) juniper-data link occurrences:", sum(naive.values()), dict(naive))
