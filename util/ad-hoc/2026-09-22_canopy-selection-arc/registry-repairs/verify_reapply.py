"""Verify the re-application onto origin/main. Scratch only.

1. Files origin/main did not touch must be byte-identical to the saved copies.
2. For EVERY file, the +/- lines of `git diff HEAD` must equal those of the original patch (same
   edit, just on a new base) -- multiset comparison, so a duplicated or dropped line is caught.
"""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

WT = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--registry-record-repairs--20260922-2021--26e0546f")
SAVED = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/6452333c-87c8-4e42-a56d-8b7d4ef20767/scratchpad/agent-e/saved-work")
MOVED = set(sys.argv[1:])


def changed_lines(diff_text: str) -> dict[str, Counter]:
    per_file: dict[str, Counter] = {}
    current = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            current = line.split(" b/", 1)[1]
            per_file[current] = Counter()
        elif current and (line.startswith("+") or line.startswith("-")) and not line.startswith(("+++", "---")):
            per_file[current][line] += 1
    return per_file


manifest = json.loads((SAVED / "manifest.json").read_text())
original = changed_lines((SAVED / "my-changes.patch").read_text())
current = changed_lines(subprocess.run(["git", "-C", str(WT), "diff", "HEAD"], check=True, capture_output=True, text=True).stdout)
ok = True
for rel, digest in manifest["files"].items():
    now = hashlib.sha256((WT / rel).read_bytes()).hexdigest()
    same_edit = original.get(rel) == current.get(rel)
    if rel in MOVED:
        verdict = "same edit on new base" if same_edit else "EDIT DIFFERS"
        ok &= same_edit
    else:
        identical = now == digest
        verdict = ("byte-identical" if identical else "BYTES DIFFER") + (", same edit" if same_edit else ", EDIT DIFFERS")
        ok &= identical and same_edit
    print(f"{rel}: {verdict} (+{sum(v for k, v in (current.get(rel) or Counter()).items() if k.startswith('+'))} / -{sum(v for k, v in (current.get(rel) or Counter()).items() if k.startswith('-'))})")
extra = set(current) - set(manifest["files"])
if extra:
    print("UNEXPECTED changed files:", sorted(extra))
    ok = False
print("VERIFY", "OK" if ok else "PROBLEM")
sys.exit(0 if ok else 1)
