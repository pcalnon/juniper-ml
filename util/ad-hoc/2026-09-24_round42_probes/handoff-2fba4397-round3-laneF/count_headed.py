"""Count reports carrying the archiver's agent header on a ref (default origin/main), and on #2097's head. Read-only.

Runs `git ls-tree` / `git show` via subprocess from inside the worktree (read-only object reads).
"""
import re
import subprocess

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
DIRP = "reports/2026-09-24_defect-register-round-42/"
HEADER_RE = re.compile(r"^<!-- Archived verbatim \S+ from subagent (a[0-9a-f]{16}) of session ([0-9a-f]{8}) \(final message\)\. -->\n\n")


def run(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=WT, capture_output=True, text=True, check=True).stdout


for ref in ("origin/main", "2e4917c2727fcd57a8cb7885118782a7da1d2eef"):
    try:
        names = [n for n in run("ls-tree", "--name-only", ref, DIRP).split("\n") if n.endswith(".md")]
    except subprocess.CalledProcessError as exc:
        print(ref, "ls-tree failed:", exc.stderr.strip()[:200])
        continue
    headed = [n for n in names if HEADER_RE.match(run("show", f"{ref}:{n}"))]
    print(f"{ref[:12]}: {len(names)} .md files, {len(headed)} with the agent header")
