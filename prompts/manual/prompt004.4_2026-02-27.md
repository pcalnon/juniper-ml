# Migration steps

Continue Phase 7 — Polyrepo Migration: Steps 7.5 and 7.6

## Execute the plan

file located at /home/pcalnon/Development/python/Juniper/notes/plan_7.5_7.6_dependency_management.md.
Read it first, then implement step by step.

## Quick state verification

cd /home/pcalnon/Development/python/Juniper/juniper-data && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git log --oneline -1 && git status --short
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git log --oneline -1 && git status --short
which uv && uv --version

## Git status

- All repos on main, pushed.
- juniper-cascor has unstaged migration plan changes.
- juniper-canopy has unstaged .gitignore changes.
- No active worktrees for this task.

---
