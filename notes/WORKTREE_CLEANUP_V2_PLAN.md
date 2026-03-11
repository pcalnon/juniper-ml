# Worktree Cleanup V2 — Development Plan

**Purpose**: Fix the CWD-trap bug and redesign the worktree cleanup procedure for Claude Code sessions
**Project**: juniper-ml
**Date**: 2026-03-11
**Status**: COMPLETE

---

## Problem Statement

The current `WORKTREE_CLEANUP_PROCEDURE.md` instructs the Claude Code agent to:

1. `cd` to the main repo directory
2. Merge the worktree branch
3. `git worktree remove` the old worktree directory

**Bug**: Claude Code sessions run with their CWD set to the worktree directory. When the worktree directory is removed, the CWD becomes invalid — the session is "trapped" in a non-existent directory path and cannot recover.

**Root cause**: The procedure does not create a new worktree for session continuity *before* removing the old one, and does not explicitly set the CWD to the new worktree.

---

## Analysis of Existing Components

### Procedure Files

| File | Location | Issues |
|------|----------|--------|
| `notes/WORKTREE_CLEANUP_PROCEDURE.md` | Current | CWD trap; no PR creation; no new worktree; hardcoded main merge |
| `notes/history/WORKTREE_CLEANUP_PROCEDURE.md` | History | Same CWD trap; references wrong repo path (`juniper` not `juniper-ml`) |
| `notes/WORKTREE_SETUP_PROCEDURE.md` | Current | Works, but references centralized `worktrees/` dir (not `.claude/worktrees/`) |
| `notes/history/WORKTREE_SETUP_PROCEDURE.md` | History | Same centralized path issue; different naming convention |

### Helper Scripts (on `tooling/more_claude_utils`)

| Script | Purpose | Issues |
|--------|---------|--------|
| `scripts/cleanup_open_worktrees.bash` | Push all worktree branches | Brittle branch-name-to-dir mapping; no error handling; no cleanup |
| `scripts/prune_git_branches_without_working_dirs.bash` | Delete branches without worktree dirs | Hardcoded branch type; regex issues; no safety checks |
| `scripts/remove_stale_worktrees.bash` | Remove all worktrees | Removes ALL worktrees indiscriminately; dangerous |

### Ad-hoc Scripts (current worktree, removed on `tooling/more_claude_utils`)

| Script | Purpose |
|--------|---------|
| `scripts/a.bash` | Bash arg parsing prototype |
| `scripts/b.bash` | Bash case/eval prototype |
| `scripts/c.bash` | Bash case/eval prototype |

These are debugging artifacts and should be removed.

---

## Requirements

### R1: CWD Safety (Critical)

The cleanup process MUST:
- Create a new worktree for the current session BEFORE removing the old one
- Change the CWD to the new worktree BEFORE removing the old one
- Verify the new CWD is valid after the old worktree is removed

### R2: Branch Merge Rules

| Parent Branch | Merge Strategy |
|---------------|----------------|
| `main` | Do NOT merge directly — create a PR |
| Not `main` | Merge worktree branch into parent branch, then create a PR from parent → main |

### R3: PR Creation

- Use `gh pr create` with description generated from:
  - `notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md` (structure)
  - `notes/pull_requests/` (content/format reference from prior PRs)
- PR title: short, descriptive (<70 chars)
- PR body: full template format

### R4: Session Continuity

After cleanup:
- A new worktree exists for the continuing session
- CWD is set to the new worktree root
- The new worktree is on a clean branch based on `main`

### R5: Complete Cleanup

- Old worktree directory removed
- Old worktree branch deleted (local and remote)
- `git worktree prune` run
- Stale worktrees from other sessions optionally cleaned

---

## Updated Cleanup Procedure (V2)

### Phase 1: Save & Push Current Work

1. **Verify clean state** — `git status` in current worktree
2. **Commit remaining changes** — `git add` + `git commit` if needed
3. **Push worktree branch to remote** — `git push origin <branch>`

### Phase 2: Create New Worktree for Session Continuity

4. **Generate new worktree metadata**:
   - Branch name: auto-generated (Claude Code worktree naming convention)
   - Base: `main` (freshly fetched)
5. **Create new worktree** — `git worktree add <new-worktree-dir> -b <new-branch> main`
6. **Change CWD to new worktree** — `cd <new-worktree-dir>`
7. **Verify new CWD** — `pwd && git status`

### Phase 3: Merge & PR

8. **Determine parent branch** of the old worktree
9. **If parent is `main`**:
   - Create PR: `gh pr create --base main --head <old-branch>`
10. **If parent is NOT `main`**:
    - In main repo: `git checkout <parent>`, `git merge <old-branch>`
    - Push parent: `git push origin <parent>`
    - Create PR: `gh pr create --base main --head <parent>`

### Phase 4: Cleanup Old Worktree

11. **Remove old worktree** — `git worktree remove <old-worktree-dir>`
12. **Delete old branch (local)** — `git branch -d <old-branch>`
13. **Delete old branch (remote)** — `git push origin --delete <old-branch>`
14. **Prune** — `git worktree prune`

### Phase 5: Verify

15. **Verify CWD is valid** — `pwd && ls`
16. **Verify worktree list** — `git worktree list`
17. **Verify branch list** — `git branch -a`
18. **Verify git status** — `git status`

---

## Script Plan

### New: `scripts/worktree_cleanup.bash`

**Purpose**: Automate the V2 cleanup procedure as a single executable script.

**Arguments**:
| Flag | Description | Required |
|------|-------------|----------|
| `--old-worktree` | Path to the worktree being cleaned up | Yes |
| `--old-branch` | Branch name of the old worktree | Yes |
| `--parent-branch` | Parent branch (default: `main`) | No |
| `--new-branch` | Name for the new worktree branch (auto-generated if omitted) | No |
| `--skip-pr` | Skip PR creation | No |
| `--dry-run` | Print commands without executing | No |

**Key behaviors**:
- Creates new worktree BEFORE removing old one
- Outputs the new worktree path so the caller can `cd` to it
- Handles PR creation with `gh pr create`
- Validates all preconditions before destructive operations
- Returns non-zero on any failure

### Update: `scripts/cleanup_open_worktrees.bash`

- Fix branch-name-to-directory mapping
- Add safety checks (don't remove the current worktree)
- Add `--dry-run` support

### Update: `scripts/remove_stale_worktrees.bash`

- Add confirmation prompt
- Exclude the current active worktree
- Add `--dry-run` support

### Update: `scripts/prune_git_branches_without_working_dirs.bash`

- Accept branch type as argument (not hardcoded)
- Fix regex patterns for branch filtering
- Add `--dry-run` support

### Remove: `scripts/a.bash`, `scripts/b.bash`, `scripts/c.bash`

These are prototyping artifacts already removed on `tooling/more_claude_utils`.

---

## Updated Procedure Document

### New: `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`

Replaces `notes/WORKTREE_CLEANUP_PROCEDURE.md` with the V2 procedure. The old file will be moved to `notes/history/`.

Key changes from V1:
1. **CWD safety**: New worktree created before old one removed
2. **PR workflow**: PRs required for main merges (no direct merge)
3. **Parent branch handling**: Different flows for main vs non-main parents
4. **Script integration**: References `scripts/worktree_cleanup.bash`
5. **Session continuity**: Explicit steps for maintaining a valid session

---

## Implementation Order

1. [x] Analysis complete
2. [x] Write `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` — updated procedure
3. [x] Write `scripts/worktree_cleanup.bash` — main cleanup script (5 phases, dry-run support)
4. [ ] Update existing scripts (cleanup_open_worktrees, remove_stale, prune_branches) — deferred to `tooling/more_claude_utils` branch
5. [x] Remove ad-hoc scripts (a.bash, b.bash, c.bash)
6. [x] Update CLAUDE.md/AGENTS.md references from old to new procedure
7. [x] Write tests for worktree_cleanup.bash — 17 tests, all passing
8. [x] Validate with sub-agents (plan logic + git worktree best practices)
9. [x] Final testing round — 17 tests passing, all merge conflict markers resolved
10. [ ] Commit, push, and create PR

### Additional fixes
- [x] Fixed merge conflict markers in `notes/DEVELOPER_CHEATSHEET.md` (lines 1244-1299)
- [x] Updated `notes/DEVELOPER_CHEATSHEET.md` worktree cleanup reference to V2
- [x] Moved V1 procedure to `notes/history/WORKTREE_CLEANUP_PROCEDURE_V1.md`
- [x] Updated `notes/WORKTREE_CLEANUP_PROCEDURE.md` to redirect to V2

---

## Validation Criteria

- [ ] `scripts/worktree_cleanup.bash --dry-run` produces correct command sequence
- [ ] New worktree is created before old one is removed
- [ ] CWD changes to new worktree before old is removed
- [ ] PR is created when parent is `main`
- [ ] Direct merge works when parent is not `main`
- [ ] Old worktree directory is fully removed
- [ ] Old branch is deleted locally and remotely
- [ ] All references to old procedure file are updated
- [ ] Tests pass for new script

---

## References

- Current procedure: `notes/WORKTREE_CLEANUP_PROCEDURE.md`
- Setup procedure: `notes/WORKTREE_SETUP_PROCEDURE.md`
- PR template: `notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md`
- Example PRs: `notes/pull_requests/PR_*.md`
- Thread handoff: `notes/THREAD_HANDOFF_PROCEDURE.md`
