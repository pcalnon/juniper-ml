# Repo Migration

Continue Phase 7 — Polyrepo Migration: Steps 7.5 and 7.6

## Completed so far

- Steps 7.1–7.4 are all complete and merged to main across all repos
- Step 7.4 (Observability Foundation): structured JSON logging, Prometheus metrics, Sentry error tracking added to juniper-data, juniper-cascor, juniper-canopy; Prometheus+Grafana stack added to juniper-deploy
- All 4 feature/7.4-observability worktrees cleaned up (merged, pushed, branches deleted)
- Migration plan checkboxes updated in juniper-cascor/notes/POLYREPO_MIGRATION_PLAN.md (v1.7.1)
- Stashed .gitignore changes popped for juniper-cascor and juniper-canopy (unstaged, not committed)

## Remaining work

- Step 7.5 — Dependency Management: Generate lockfiles (requirements.lock) for Docker builds using pip-compile or uv pip compile; update Dockerfiles; document lockfile regeneration workflow
- Step 7.6 — Ecosystem Documentation Update: Update parent CLAUDE.md at /home/pcalnon/Development/python/Juniper/CLAUDE.md to reflect all 9 repos (currently only lists 5); update dependency graph and directory structure
- Step 7.2 remaining items: Create GitHub PAT for cross-repo CI dispatch; test end-to-end dispatch
- Deferred 7.4 items: Service-specific Prometheus metrics (WebSocket connections, training counters, dataset metrics); default Grafana dashboard

## Key context

- juniper-canopy had a pre-existing merge of feature/phase5-backend-protocol that was committed during cleanup (82236b1)
- juniper-cascor and juniper-canopy both have unstaged .gitignore modifications from popped stashes
- There are existing phase 6 worktrees in /home/pcalnon/Development/python/Juniper/worktrees/ for juniper-cascor-client and juniper-data-client (unrelated)
- The plan file at /home/pcalnon/.claude/plans/peaceful-wishing-meerkat.md covers the 7.4 work (now complete)

## Verification

### Verify all repos on main with 7.4 merged

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-data && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-deploy && git log --oneline -1
```

### Check migration plan

```bash
grep -A2 "Step 7.4" /home/pcalnon/Development/python/Juniper/juniper-cascor/notes/POLYREPO_MIGRATION_PLAN.md | head -5
```

## Git status

All 4 repos on main, pushed to remote. juniper-cascor and juniper-canopy have unstaged .gitignore changes. No worktrees for 7.4 remain.

---
