# Finished Task Worktree Cleanup Procedure

**Project**: juniper
**Last Updated**: 2026-02-25

---

## Overview

When a task is complete and changes have been committed in a worktree, agents MUST
follow this cleanup procedure to merge changes, remove the worktree, and clean up
the working branch.

## When to Use

**ALWAYS** use this procedure when:

- A task performed in a worktree is complete
- All changes have been committed
- The task is ready for merge

**Defer cleanup when**:

- The task is paused but not complete (leave worktree intact)
- A thread handoff is occurring (document worktree state in handoff goal)
- The user explicitly requests the worktree be preserved

## Procedure

### Step 1: Finalize Work in Worktree

Ensure all work is committed:

```bash
cd <WORKTREE_PATH>

# Check for uncommitted changes
git status

# Stage and commit any remaining changes
git add <files>
git commit -m "<final commit message>"
```

### Step 2: Run Verification (Project-Specific)

Before merging, verify the changes are sound. See project AGENTS.md for specific
test and validation commands.

### Step 3: Determine Merge Target

| Scenario | Merge Target | Notes |
|----------|-------------|-------|
| **Default** | Parent branch (usually `main`) | Most common case |
| **Feature branch hierarchy** | Parent feature branch | When working on a sub-task of a larger feature |
| **Release preparation** | `release/<version>` | When preparing a release |
| **User-specified** | As directed | User may specify a different target |

If the merge target differs from the default parent branch, confirm with the user
before proceeding.

### Step 4: Navigate to Main Repository

```bash
cd /home/pcalnon/Development/python/Juniper/juniper
```

### Step 5: Update and Merge

```bash
# Checkout the merge target
git checkout <merge-target-branch>

# Pull latest changes
git pull origin <merge-target-branch>

# Merge the working branch
git merge <working-branch-name>
```

**Merge conflict resolution**:

- If conflicts arise, resolve them in the main repo directory
- After resolution: `git add <resolved-files> && git commit`
- If conflicts are complex, consult the user before proceeding

### Step 6: Push Merged Changes

> **Requires user confirmation** — Do not push without explicit approval.

```bash
git push origin <merge-target-branch>
```

### Step 7: Remove Worktree

```bash
git worktree remove <WORKTREE_PATH>
```

If the worktree has uncommitted changes and removal fails:

```bash
git worktree remove --force <WORKTREE_PATH>
```

**Only use `--force` after confirming all important changes are committed or
intentionally discarded.**

### Step 8: Delete Working Branch

```bash
git branch -d <working-branch-name>
```

If the branch has not been fully merged (e.g., squash merge was used):

```bash
git branch -D <working-branch-name>
```

### Step 9: Prune and Verify

```bash
# Prune stale worktree references
git worktree prune

# Verify worktree is removed
git worktree list

# Verify branch is deleted
git branch --list <working-branch-name>

# Verify clean state
git status
```

## Quick Reference

```bash
# 1. Finalize work in worktree
cd <WORKTREE_PATH>
git status  # ensure clean

# 2. Switch to main repo
cd /home/pcalnon/Development/python/Juniper/juniper

# 3. Merge
git checkout <merge-target>
git pull origin <merge-target>
git merge <working-branch>

# 4. Push (requires user confirmation)
git push origin <merge-target>

# 5. Cleanup
git worktree remove <WORKTREE_PATH>
git branch -d <working-branch>
git worktree prune
```

## Special Cases

### Squash Merge

If a squash merge is preferred (for cleaner history):

```bash
git merge --squash <working-branch>
git commit -m "<squash commit message>"
```

Note: After squash merge, use `git branch -D` (capital D) to delete the branch
since Git won't recognize it as fully merged.

### Rebase Before Merge

If the merge target has advanced since the worktree was created:

```bash
# In the worktree, rebase onto the updated target
cd <WORKTREE_PATH>
git fetch origin
git rebase origin/<merge-target>

# Then proceed with merge from Step 4
```

### Preserving Worktree for Review

If the user wants to review before cleanup:

1. Complete Steps 1-6 (merge and push)
2. Skip Steps 7-9
3. Inform the user the worktree is preserved at `<WORKTREE_PATH>`
4. User will request cleanup when ready

### Thread Handoff with Active Worktree

If a thread handoff occurs while a worktree is active:

1. Include the following in the handoff goal:
   - Worktree path
   - Working branch name
   - Parent branch / merge target
   - Current state of work (what's committed, what's pending)
2. Do NOT clean up the worktree during handoff
3. The new thread should pick up from the worktree state
