#!/usr/bin/env python3
"""Lane A round 2: which juniper-ml markdown files link into which sibling repo, as the docs-full-check link step
sees them (the head tree's own juniper-doc-tools checker, `--exclude templates --exclude history --exclude legacy
--cross-repo check`), with an EMPTY synthetic ecosystem root so every cross-repo link reports its repo."""
import collections
import re
import sys
import tempfile
from pathlib import Path

HEAD = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA/head")
sys.path.insert(0, str(HEAD / "juniper-doc-tools"))
from juniper_doc_tools.check_doc_links import validate_directory  # noqa: E402

with tempfile.TemporaryDirectory(dir=str(HEAD.parent / "tmp")) as eco:
    res = validate_directory(HEAD, exclude_dirs={"templates", "history", "legacy"}, cross_repo_mode="check", ecosystem_root=Path(eco))
print(f"scanned {res.scanned_files} files; {len(res.errors)} errors")
by_repo = collections.defaultdict(list)
other = []
for e in res.errors:
    m = re.search(r"file not found in (juniper-[a-z-]+)$", e)
    if m:
        by_repo[m.group(1)].append(e.strip().split(":")[0] + ":" + e.strip().split(":")[1])
    else:
        other.append(e.strip())
for repo, hits in sorted(by_repo.items()):
    files = collections.Counter(h.split(":")[0] for h in hits)
    print(f"{repo}: {len(hits)} link(s) in {len(files)} file(s)")
    for f, n in files.items():
        lines = [h.split(":")[1] for h in hits if h.startswith(f + ":")]
        print(f"    {f} x{n} (lines {', '.join(lines)})")
print(f"juniper-data links: {len(by_repo.get('juniper-data', []))}")
print(f"other errors: {len(other)}")
for o in other[:10]:
    print("   ", o[:200])
