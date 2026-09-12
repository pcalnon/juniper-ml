#!/usr/bin/env python3
"""One-shot: stop util/worktree_cleanup.bash from escalating past git's own refusals.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-12

Why
---
Two fall-through blocks defeated the only two safety refusals git offers:

    git worktree remove "$WT" || { ... worktree remove --force "$WT"; }
    git branch -d "$BR"       || { ... branch -D "$BR"; }

`git worktree remove` refuses EXACTLY when the tree has uncommitted or untracked work;
`--force` then deletes it. `git branch -d` refuses EXACTLY when the branch holds commits
not merged anywhere; `-D` then drops them. So both escalations converted "git protected
you" into "git was overruled", automatically and unattended -- in the tool the ecosystem
documents as the sanctioned path.

Established by independent consensus 2026-09-12 (4 reviewers, distinct entry points).

An escape hatch is retained deliberately. The repo's own memory records that a gate with no
way past it is its own hazard: "Refusing with no escape hatch ... pushes people to remove by
hand, which is exactly where the loss happens." The difference is that `--force-destructive`
must now be typed by a human who has read what would be lost.

Idempotent; refuses on a drifted anchor.
"""

from __future__ import annotations

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().parents[3] / "util" / "worktree_cleanup.bash"

OLD_FLAGS = """            --skip-remote-delete)
                SKIP_REMOTE_DELETE="${TRUE}"
                shift
                ;;
"""
NEW_FLAGS = """            --skip-remote-delete)
                SKIP_REMOTE_DELETE="${TRUE}"
                shift
                ;;
            --force-destructive)
                FORCE_DESTRUCTIVE="${TRUE}"
                shift
                ;;
"""

OLD_DECL = 'SKIP_REMOTE_DELETE="${FALSE}"\n'
NEW_DECL = 'SKIP_REMOTE_DELETE="${FALSE}"\nFORCE_DESTRUCTIVE="${FALSE}"\n'

OLD_USAGE = "  --skip-remote-delete     Skip remote branch deletion (useful when PR is open)\n"
NEW_USAGE = (
    "  --skip-remote-delete     Skip remote branch deletion (useful when PR is open)\n"
    "  --force-destructive      Allow 'worktree remove --force' and 'branch -D'. These defeat\n"
    "                           git's ONLY two refusals -- uncommitted/untracked work, and\n"
    "                           unmerged commits. Without it, this script REFUSES instead of\n"
    "                           escalating, and prints exactly what would have been destroyed.\n"
)

OLD_BODY = '''    # Remove old worktree
    log_info "Removing worktree: ${OLD_WORKTREE}"
    run_cmd git -C "${MAIN_REPO}" worktree remove "${OLD_WORKTREE}" || {
        log_warn "Standard removal failed, trying --force"
        run_cmd git -C "${MAIN_REPO}" worktree remove --force "${OLD_WORKTREE}"
    }

    # Delete local branch
    log_info "Deleting local branch: ${OLD_BRANCH}"
    run_cmd git -C "${MAIN_REPO}" branch -d "${OLD_BRANCH}" || {
        log_warn "Standard delete failed (branch not fully merged), trying -D"
        run_cmd git -C "${MAIN_REPO}" branch -D "${OLD_BRANCH}"
    }
'''

NEW_BODY = '''    # Remove old worktree.
    #
    # DO NOT ESCALATE TO --force ON FAILURE. `git worktree remove` refuses in exactly one
    # situation: the tree holds uncommitted or untracked work. That refusal is the only
    # protection git offers here, and an automatic `--force` converts it into deletion of
    # the very thing it was protecting. Note also what the refusal does NOT cover: git
    # considers a tree with only IGNORED files clean, so those are deleted with no refusal
    # and no --force -- 330 MB of them sat across 19 live worktrees when this was measured,
    # including a .env and 60 files of soak run evidence.
    log_info "Removing worktree: ${OLD_WORKTREE}"
    run_cmd git -C "${MAIN_REPO}" worktree remove "${OLD_WORKTREE}" || {
        if [[ "${FORCE_DESTRUCTIVE}" == "${TRUE}" ]]; then
            log_warn "Removal refused; --force-destructive given, forcing"
            run_cmd git -C "${MAIN_REPO}" worktree remove --force "${OLD_WORKTREE}"
        else
            log_error "git REFUSED to remove ${OLD_WORKTREE} -- it holds uncommitted or untracked work."
            log_error "Below is what is there. Nothing has been deleted."
            git -C "${OLD_WORKTREE}" status --porcelain --ignored=no >&2 || true
            log_error "Commit, push, or move that work; then re-run. To delete it anyway, pass --force-destructive."
            return 1
        fi
    }

    # Delete local branch.
    #
    # DO NOT ESCALATE TO -D ON FAILURE, for the same reason. `git branch -d` refuses in
    # exactly one situation: the branch holds commits reachable from nowhere else. `-D`
    # drops them, and the reflog is the only remaining anchor until it expires.
    log_info "Deleting local branch: ${OLD_BRANCH}"
    run_cmd git -C "${MAIN_REPO}" branch -d "${OLD_BRANCH}" || {
        if [[ "${FORCE_DESTRUCTIVE}" == "${TRUE}" ]]; then
            log_warn "Delete refused; --force-destructive given, forcing"
            run_cmd git -C "${MAIN_REPO}" branch -D "${OLD_BRANCH}"
        else
            log_error "git REFUSED to delete ${OLD_BRANCH} -- it holds commits merged nowhere."
            log_error "These commits would be lost. Nothing has been deleted:"
            git -C "${MAIN_REPO}" log --oneline --no-merges "${OLD_BRANCH}" --not --branches --remotes --tags >&2 || true
            log_error "Merge or push them; then re-run. To drop them anyway, pass --force-destructive."
            return 1
        fi
    }
'''


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    if "FORCE_DESTRUCTIVE" in src:
        print("already applied")
        return 0
    for name, old in (("decl", OLD_DECL), ("usage", OLD_USAGE),
                      ("flags", OLD_FLAGS), ("body", OLD_BODY)):
        if src.count(old) != 1:
            print(f"REFUSING: anchor {name!r} found {src.count(old)} times", file=sys.stderr)
            return 1
    src = (src.replace(OLD_DECL, NEW_DECL)
              .replace(OLD_USAGE, NEW_USAGE)
              .replace(OLD_FLAGS, NEW_FLAGS)
              .replace(OLD_BODY, NEW_BODY))
    TARGET.write_text(src, encoding="utf-8")
    print(f"de-escalated {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
