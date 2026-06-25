# Perform Full Documentation Audit, all Repos

Continue the Juniper documentation audit remediation, executing Batches 2-8 from the remediation backlog.

## Completed so far

- Full 4-phase documentation audit executed across all 8 Juniper repos + parent directory
- Consolidated report generated: 161 issues (20 critical, 45 high, 61 medium, 35 low)
- Remediation backlog created with 47 prioritized items in 8 execution batches
- Batch 1 (6 critical quick fixes) completed and committed across 5 repos:
  - R-03: Fixed cascor-client AGENTS.md file references (abc7fd4)
  - R-04: Removed broken juniper-deploy 404 links in 4 READMEs (bba80fa, 0c78c64, 8b6e725, d8fab3d)
  - R-05: Fixed underscore GitHub URLs in cascor docs (0c78c64)
  - R-06: Fixed canopy worktree conda env name (bba80fa)
  - R-07: Fixed port 8050→8100 in juniper-data CONSTANTS_GUIDE.md (8b6e725)
  - R-08: Fixed port 8200→8100 in juniper-data test fixture (8b6e725)

## Remaining work (Batches 2-8)

- Batch 2: 13 high quick fixes (R-16 through R-28) — broken internal links, outdated refs
- Batch 3: Parent directory fixes (R-11, R-12, R-14, R-15, R-28, R-29, R-37, R-38)
- Batch 4: Procedure convergence (R-13, R-30, R-31, R-32)
- Batch 5: Medium quick fixes (R-33 through R-40)
- Batch 6: Moderate effort items (R-02, R-09, R-10)
- Batch 7: juniper-data docs/ overhaul (R-01) — major effort, ~30 files of canopy docs misplaced
- Batch 8: Low priority cleanup (R-41 through R-47)

## Key context

- Audit artifacts live in /home/pcalnon/Development/python/Juniper/notes/audit_data/
- REMEDIATION_BACKLOG.md has full details on every item with severity, effort, and description
- AUDIT_REPORT.md has the consolidated findings and broken links tables
- Per-repo findings are in notes/audit_data/findings/ (38 markdown files)
- Deliberately skipped fixing juniper-data/docs/api/API_REFERENCE.md port — that entire file is misplaced canopy content (part of R-01 Batch 7)
- Pre-existing uncommitted changes exist in juniper-canopy (docs/QUICK_START.md), juniper-cascor (docs/source/quick-start.md, notes/POLYREPO_MIGRATION_PLAN.md), and juniper-ml (prompts/ files) — do NOT touch these
- All 5 Batch 1 commits are local only (not pushed to remotes)

## Verification Commands for New Thread

```bash
# Verify plan exists
cat Juniper/notes/DOCUMENTATION_AUDIT_PLAN.md | head -31

# Verify scripts exist
ls -la Juniper/notes/audit_scripts/

# Verify output dir exists
ls -la Juniper/notes/audit_data/

# Verify Batch 1 commits
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-data && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git log --oneline -1

# Read the remediation backlog
cat /home/pcalnon/Development/python/Juniper/notes/audit_data/REMEDIATION_BACKLOG.md
```

## Phase 1 Launch Script, Optional

**Launching Phase 1 directly, if Desired:**

```bash
# To Run Phase 1, use the following script:
cd /home/pcalnon/Development/python/Juniper
bash notes/audit_scripts/run_phase0.sh
```

## Git status

All 5 repos on main, Batch 1 commits unpushed. juniper-ml also has 1 unpushed commit from prior session (fe56127 audit plan).

---

## Launch Command

```bash
claude --dangerously-skip-permissions --rename "P10.1: Perform Full Documentation Audit, all Repos"
```

---
