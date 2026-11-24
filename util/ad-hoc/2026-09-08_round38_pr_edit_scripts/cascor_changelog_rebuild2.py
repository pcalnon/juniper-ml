#!/usr/bin/env python3
"""Rebuild the cascor PR-A CHANGELOG entry on top of origin/main AFTER the v0.11.0 release
(cascor#635 moved every [Unreleased] entry under `## [0.11.0] - 2026-09-08`), session scratch.

The four bullets now open a fresh `### Fixed` block under the empty `## [Unreleased]`.
Reads the entry text out of cascor_pr_a_changelog.py with ``ast`` (importing it would execute
its stale top-level replacement).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — one-off (applied once, on 2026-09-08, to the PR worktree named below; the paths inside are that session's)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#633 (worktree juniper-cascor--fix--dataset-shortfall-acceptance-source--20260908-0716--d39d537e);
         HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--dataset-shortfall-acceptance-source--20260908-0716--d39d537e")
CHANGELOG = W / "CHANGELOG.md"

module = ast.parse((HERE / "cascor_pr_a_changelog.py").read_text())
new_text = None
for node in module.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NEW" for t in node.targets):
        new_text = ast.literal_eval(node.value)
if new_text is None:
    sys.exit("FAIL: could not find NEW in cascor_pr_a_changelog.py")

BULLET = "- **An ingested artifact carrying NaN or Inf now fails at the boundary, by name.**\n"
bullets = new_text.replace("## [Unreleased]\n\n### Fixed\n\n", "", 1)
assert bullets.endswith(BULLET)
bullets = bullets[: -len(BULLET)]  # my four bullets, ending in a blank line
assert bullets.endswith("\n\n"), repr(bullets[-20:])
assert bullets.count("- **") == 4, bullets.count("- **")

main_text = subprocess.run(["git", "-C", str(W), "show", "origin/main:CHANGELOG.md"], check=True, capture_output=True, text=True).stdout
ANCHOR = "## [Unreleased]\n\n## [0.11.0] - 2026-09-08\n"
if main_text.count(ANCHOR) != 1:
    sys.exit(f"FAIL: anchor found {main_text.count(ANCHOR)} times")
rebuilt = main_text.replace(ANCHOR, "## [Unreleased]\n\n### Fixed\n\n" + bullets + "## [0.11.0] - 2026-09-08\n", 1)
CHANGELOG.write_text(rebuilt)
print("CHANGELOG rebuilt on post-v0.11.0 main; PR-A entries open [Unreleased] > ### Fixed")
