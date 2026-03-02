# New Task Worktree Setup Procedure

**Project**: juniper
**Last Updated**: 2026-02-25

---

## Overview

When beginning a new task that involves code changes, agents MUST create an isolated
git worktree. This ensures that:

- The main working tree remains clean and on the primary branch
- Multiple tasks can be worked on in parallel without interference
- Work-in-progress changes are isolated and easily discarded if needed
- Branch history remains clean and reviewable

## When to Use

**ALWAYS** use this procedure when starting a task that involves:

- Code modifications (features, bug fixes, refactoring)
- Configuration changes
- Documentation updates that accompany code changes
- Any change that will result in a commit

**Exceptions** (worktree NOT required):

- Read-only exploration or research
- Running tests or diagnostics on the current codebase
- Reviewing existing code without modifications

## Procedure

### Step 1: Determine Task Metadata

Before creating the worktree, identify:

| Field | Description | Example |
|-------|-------------|---------|
| **Parent branch** | Branch to base work on (default: `main`) | `main` |
| **Branch prefix** | Category of work | `task/`, `feature/`, `fix/`, `refactor/`, `docs/` |
| **Short description** | Kebab-case task summary (2-5 words) | `fix-logging-levels` |
| **Full branch name** | `<prefix><description>` | `fix/logging-levels` |

### Step 2: Ensure Parent Branch Is Up to Date

```bash
cd /home/pcalnon/Development/python/Juniper/juniper
git checkout main
git pull origin main
```

### Step 3: Create Worktree with New Branch

Generate the unique worktree directory name and create the worktree in a single
operation:

```bash
REPO_NAME="juniper"
BRANCH_NAME="<prefix>/<description>"
SANITIZED_BRANCH=$(echo "$BRANCH_NAME" | tr '/' '-')
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
HEX_SUFFIX=$(head -c 2 /dev/urandom | xxd -p)
WORKTREE_DIR="/home/pcalnon/Development/python/Juniper/worktrees/${REPO_NAME}_${SANITIZED_BRANCH}_${TIMESTAMP}_${HEX_SUFFIX}"

git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME"
```

**Directory naming format**: `<repo-name>_<sanitized-branch>_<YYYYMMDD-HHMMSS>_<hex4>`

Components:

| Component | Description | Example |
|-----------|-------------|---------|
| `<repo-name>` | Repository name | `juniper` |
| `<sanitized-branch>` | Branch name with `/` replaced by `-` | `fix-logging-levels` |
| `<YYYYMMDD-HHMMSS>` | Creation timestamp | `20260225-143022` |
| `<hex4>` | 4-character random hex suffix for uniqueness | `a1b2` |

**Full example**: `juniper_fix-logging-levels_20260225-143022_a1b2`

### Step 4: Navigate to Worktree

```bash
cd "$WORKTREE_DIR"
```

All subsequent work for this task MUST be performed within the worktree directory.

### Step 5: Verify Setup

```bash
# Confirm correct branch
git branch --show-current

# Confirm worktree is registered
git worktree list

# Confirm clean working state
git status
```

### Step 6: Record Worktree Metadata

Include the following in thread context for later cleanup:

| Field | Value |
|-------|-------|
| **Main repo path** | `/home/pcalnon/Development/python/Juniper/juniper` |
| **Worktree path** | `$WORKTREE_DIR` |
| **Working branch** | `$BRANCH_NAME` |
| **Parent branch** | `main` (or as determined in Step 1) |

## Worktree Directory Location

All worktrees are created under:

```
/home/pcalnon/Development/python/Juniper/worktrees/
```

This directory is shared across all Juniper repos. The repo name prefix in the
directory name prevents collisions between repos.

## Branch Naming Conventions

| Prefix | Use Case | Example |
|--------|----------|---------|
| `task/` | General tasks | `task/update-dependencies` |
| `feature/` | New features | `feature/add-spiral-generator` |
| `fix/` | Bug fixes | `fix/logging-levels` |
| `refactor/` | Code refactoring | `refactor/extract-base-class` |
| `docs/` | Documentation only | `docs/update-api-reference` |

## Error Handling

- If `git worktree add` fails because the branch already exists, choose a
  different branch name or delete the stale branch first
- If the `worktrees/` directory doesn't exist, create it:
  `mkdir -p /home/pcalnon/Development/python/Juniper/worktrees/`
- If the parent branch has diverged from remote, rebase or merge before creating
  the worktree
