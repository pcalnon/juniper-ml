#!/usr/bin/env python3
"""
Run juniper-ci-tools' docs deletion screen over an UNCOMMITTED tree, fence-aware as 0.9.1 runs it in CI.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation (canopy#791's deleted ```yaml block); adapted from
         2026-10-08_flood3_worktree_screens.py, which predates 0.9.1 and calls classify_file() without
         the fence maps, so a `#` comment inside a deleted code fence still reads as a heading there.

Usage: 2026-11-07_flood4_worktree_docs_screen.py <repo> <base-ref> -- <file.md> [...]
Exit 1 on any FAIL. Uses this checkout's juniper-ci-tools/ source (0.9.1, what CI's >=0.9.0,<0.10.0 pin resolves to).
"""

import subprocess
import sys
from pathlib import Path

_CI_TOOLS = Path(__file__).resolve().parents[2] / "juniper-ci-tools"
sys.path.insert(0, str(_CI_TOOLS))

from juniper_ci_tools import docs_additions_check as docs  # noqa: E402


def main(argv: list[str]) -> int:
    if "--" not in argv or len(argv) < 4:
        print(__doc__)
        return 2
    split = argv.index("--")
    repo, ref = argv[1], argv[2]
    fails = 0
    for path in argv[split + 1 :]:
        diff = subprocess.run(["git", "-C", repo, "diff", "--unified=0", "--no-color", ref, "--", path], capture_output=True, text=True, check=True).stdout
        base = subprocess.run(["git", "-C", repo, "show", f"{ref}:{path}"], capture_output=True, text=True, check=False)
        base_fenced = docs.fenced_lines(base.stdout) if base.returncode == 0 else None
        head_fenced = docs.fenced_lines((Path(repo) / path).read_text(encoding="utf-8"))
        findings = docs.classify_file(path, docs.parse_hunks(diff), docs.DEFAULT_MIN_RUN, base_fenced=base_fenced, head_fenced=head_fenced)
        for f in findings:
            print(f"docs   {f.severity:5s} {path}: {f.reason} {f.detail}")
            fails += f.severity == "FAIL"
        if not findings:
            print(f"docs   CLEAN {path}")
    print(f"ci-tools source: {_CI_TOOLS}; FAIL count: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
