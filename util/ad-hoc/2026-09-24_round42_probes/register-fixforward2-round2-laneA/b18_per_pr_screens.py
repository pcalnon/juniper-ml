#!/usr/bin/env python3
"""Lane A round 2: run the three per-PR screens (head's juniper-ci-tools symbol-loss + docs-additions, and
head's util/markdown_structure_delta.py) read-only against the session worktree's object store, base df21367d
(main, the branch's merge base) and head 990ef3f9. The screens only run `git diff` / `git show` on refs."""
import subprocess
import sys

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
HEAD = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA/head"
env_pp = {"PYTHONPATH": HEAD + "/juniper-ci-tools", "PATH": "/usr/bin:/bin", "HOME": "/home/pcalnon"}
base, head = "df21367d", "990ef3f9"
mb = subprocess.run(["git", "merge-base", base, head], cwd=WT, capture_output=True, text=True).stdout.strip()
print("merge-base(df21367d, 990ef3f9) =", mb[:12])
runs = [
    ("symbol-loss", [sys.executable, "-m", "juniper_ci_tools.cli_symbol_loss_check", "--scope", "tests/*.py", "--scope", "util/**/*.py", "--scope", "util/**/*.bash", "--base", base, "--head", head, "--repo-root", WT]),
    ("docs-additions", [sys.executable, "-m", "juniper_ci_tools.cli_docs_additions_check", "--base", base, "--head", head, "--repo-root", WT]),
]
for name, cmd in runs:
    p = subprocess.run(cmd, capture_output=True, text=True, env=env_pp, cwd=WT)
    print(f"== {name}: rc={p.returncode}")
    print((p.stdout + p.stderr).strip()[-2500:])
