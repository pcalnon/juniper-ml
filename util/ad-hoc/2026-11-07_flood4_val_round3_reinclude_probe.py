"""
Probe: does appending `!.claude/settings.json` to juniper-ml's .gitignore make
`.claude/settings.json` committable, given the same file also ignores the `.claude`
directory itself? Builds a throwaway repo under this worktree's tmp/, copies the
.gitignore, and asks git, with and without the re-include.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 docs carrier, round-3 validation (round-2 F8, REFERENCE idle-compaction table)
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def trial(root, label, extra):
    d = root / label
    if d.exists():
        shutil.rmtree(d)
    (d / ".claude").mkdir(parents=True)
    (d / ".claude" / "settings.json").write_text("{}\n")
    gi = (REPO / ".gitignore").read_text() + extra
    (d / ".gitignore").write_text(gi)
    git(d, "init", "-q")
    rc_ci, out_ci = git(d, "check-ignore", "-v", ".claude/settings.json")
    _rc_st, out_st = git(d, "status", "--porcelain", "--untracked-files=all")
    rc_add, out_add = git(d, "add", ".claude/settings.json")
    _rc_ls, out_ls = git(d, "ls-files", "--cached", ".claude/settings.json")
    print(f"[{label}] check-ignore rc={rc_ci}: {out_ci or '(not ignored)'}")
    print(f"[{label}] status shows settings.json: {'.claude/settings.json' in out_st}")
    print(f"[{label}] git add rc={rc_add}: {out_add[:200] or '(ok)'}")
    print(f"[{label}] staged: {bool(out_ls)}")


def main():
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=True)
    trial(root, "as_is", "")
    trial(root, "with_reinclude", "\n!.claude/settings.json\n")


if __name__ == "__main__":
    main()
