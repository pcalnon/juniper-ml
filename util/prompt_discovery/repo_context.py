"""repo_context probe: repo name / branch / dirty / HEAD sha of the target ``--repo-root``.

Cites the *actual* target-repo state so a generated prompt never asserts the wrong repo.
A failure here is what makes the whole bundle a hard stop (cli.py): the Template Agent must
never proceed on an empty-but-valid bundle (design S5.1 step 2).
"""

from __future__ import annotations

from pathlib import Path

from _util import run


def probe(repo_root: str) -> dict:
    rc, sha, _ = run(["git", "-C", repo_root, "rev-parse", "HEAD"])
    if rc != 0 or not sha.strip():
        return {
            "status": "unavailable",
            "reason": "not a git repository or git unavailable",
            "repo": Path(repo_root).name,
            "branch": None,
            "head_sha": None,
            "dirty": None,
        }
    _, branch, _ = run(["git", "-C", repo_root, "rev-parse", "--abbrev-ref", "HEAD"])
    _, status_out, _ = run(["git", "-C", repo_root, "status", "--porcelain"])
    _, toplevel, _ = run(["git", "-C", repo_root, "rev-parse", "--show-toplevel"])
    name = Path(toplevel.strip()).name if toplevel.strip() else Path(repo_root).name
    return {
        "status": "ok",
        "repo": name,
        "branch": branch.strip() or None,
        "head_sha": sha.strip(),
        "dirty": bool(status_out.strip()),
    }
