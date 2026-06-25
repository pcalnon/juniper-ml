"""file_probe: grep the task subject for candidate ``file:line`` anchors.

Lets a generated prompt's ``## Resources`` cite *real* anchors instead of invented ones.
Prefers ``git grep`` (fast, tracked-files only, repo-relative paths); falls back to
``grep -rn`` when git is unavailable.
"""

from __future__ import annotations

from _util import run


def probe(repo_root: str, subject, max_hits: int = 25) -> dict:
    if not subject:
        return {"status": "ok", "subject": None, "anchors": [], "reason": "no subject supplied"}
    rc, out, _ = run(["git", "-C", repo_root, "grep", "-nI", "--", subject])
    if rc not in (0, 1):  # 1 == no matches; anything else == git grep unavailable
        rc, out, _ = run(["grep", "-rnI", "--", subject, repo_root])
    anchors = []
    truncated = False
    for line in out.splitlines():
        parts = line.split(":", 2)
        if len(parts) >= 3 and parts[1].isdigit():
            anchors.append({"file": parts[0], "line": int(parts[1]), "text": parts[2][:200]})
        if len(anchors) >= max_hits:
            truncated = True
            break
    return {"status": "ok", "subject": subject, "anchors": anchors, "truncated": truncated}
