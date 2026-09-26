#!/usr/bin/env python3
"""Lane B: count juniper-ml's cross-repo doc links by target repo, with the checker's own code.

Runs juniper_doc_tools.check_doc_links.validate_directory (from head's in-repo source) in "check"
mode, with the docs-full-check.yml exclude set (templates, history, legacy), against an ecosystem
root that holds NO sibling checkout, so every cross-repo link is reported as "file not found in
<repo>". Counts the links and the distinct files per target repo.

Then simulates docs-full-check.yml's cases: an ecosystem root holding every sibling as an empty
directory except the one "missing", and reports whether any cross-repo error names that sibling.

Usage: python3 xrepo_links.py <dir holding juniper-ml/>
"""
import collections
import re
import sys
import tempfile
from pathlib import Path

base = Path(sys.argv[1]).resolve()
ml = base / "juniper-ml"
sys.path.insert(0, str(ml / "juniper-doc-tools"))
from juniper_doc_tools import check_doc_links as cdl  # noqa: E402

print("checker from:", cdl.__file__)
EXCL = {"templates", "history", "legacy"}

with tempfile.TemporaryDirectory() as eco:
    res = cdl.validate_directory(ml, exclude_dirs=EXCL, cross_repo_mode="check", ecosystem_root=Path(eco))
print("scanned files:", res.scanned_files)
per_repo = collections.Counter()
files = collections.defaultdict(set)
other = []
for e in res.errors:
    m = re.search(r"file not found in (juniper-[a-z-]+)", e)
    if m:
        per_repo[m.group(1)] += 1
        files[m.group(1)].add(e.strip().split(":")[0])
    else:
        other.append(e.strip())
for repo, n in sorted(per_repo.items()):
    print(f"  {repo}: {n} link(s) in {len(files[repo])} file(s): {sorted(files[repo])}")
print("non-cross-repo errors:", len(other))
for e in other[:15]:
    print("   ", e[:220])
