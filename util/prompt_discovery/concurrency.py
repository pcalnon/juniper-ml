"""concurrency: open PRs (``gh``) + worktrees -- a *work* dup-guard.

Flags duplicate *work* (an open PR / a sibling worktree already touching the area), NOT a
filename collision. ``gh`` may be unavailable (no auth, headless CI) -- that slice then
degrades to ``unavailable`` rather than failing the bundle (design S5.6).
"""

from __future__ import annotations

import json

from _util import run


def probe(repo_root: str) -> dict:
    prs_status, prs = "unavailable", []
    rc, out, _ = run(["gh", "pr", "list", "--state", "open", "--json", "number,title,headRefName"], cwd=repo_root)
    if rc == 0:
        try:
            prs = json.loads(out or "[]")
            prs_status = "ok"
        except ValueError:
            prs_status = "unavailable"
    rc2, wt_out, _ = run(["git", "-C", repo_root, "worktree", "list"])
    worktrees = [ln.split()[0] for ln in wt_out.splitlines() if ln.strip()] if rc2 == 0 else []
    overall = "ok" if (prs_status == "ok" or worktrees) else "unavailable"
    return {"status": overall, "open_prs": prs, "open_prs_status": prs_status, "worktrees": worktrees}
