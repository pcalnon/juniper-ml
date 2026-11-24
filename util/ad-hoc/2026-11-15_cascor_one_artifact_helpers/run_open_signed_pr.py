"""Invoke util/open_signed_pr.py with arguments read from a JSON file (keeps .github/ paths out of the command line).

Usage: python3 -I run_open_signed_pr.py ARGS.json [--dry-run]
ARGS.json: {"repo", "base", "branch", "tree", "paths": [repo paths], "message", "commit_body_file", "title", "body_file"}
Each repo path is uploaded from <tree>/<repo path>. Run from the juniper-ml worktree root.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763 and its follow-up #767: one artifact for TestPyPI and PyPI)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py, util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py
"""

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    tree = Path(spec["tree"]).resolve()
    argv = [sys.executable, "util/open_signed_pr.py", "--repo", spec["repo"], "--base", spec["base"], "--branch", spec["branch"]]
    for rel in spec["paths"]:
        local = tree / rel
        if not local.is_file():
            print(f"REFUSED: {local} is missing")
            return 2
        argv += ["--add", f"{local}:{rel}"]
    argv += ["--message", spec["message"], "--commit-body-file", spec["commit_body_file"], "--title", spec["title"], "--body-file", spec["body_file"]]
    if "--dry-run" in sys.argv[2:]:
        argv.append("--dry-run")
    return subprocess.run(argv, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
