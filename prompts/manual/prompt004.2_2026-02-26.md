# Phase 7 continuation

Continue Phase 7 (Production Readiness) of the Juniper polyrepo migration, starting with Step 7.3 — API Security.

Completed so far (Phase 7):

- 7.1.1 Dependabot — DONE (all 7 repos)
- 7.1.2 SHA-pin GitHub Actions — DONE (all 7 repos, ~123 replacements)
- 7.1.3 CODEOWNERS — DONE (all 7 repos)
- 7.1.4 Harden juniper-data-client CI — DONE (rewritten to 7-job pipeline + CHANGELOG.md)
- 7.2 Cross-Repo CI Integration — DONE (dispatch wiring in 6 repos; 2 manual steps remain for user: create CROSS_REPO_DISPATCH_TOKEN PAT, test end-to-end)

Remaining work:

- 7.3 — API Security (next)
  - 7.3.1: JuniperCascor API auth (API key middleware, rate limiting, WebSocket auth, update cascor-client)
  - 7.3.2: JuniperCanopy API auth (API key middleware, exempt Dash assets)
  - 7.3.3: Update juniper-deploy (env vars, integration tests, docs)
  - Reference implementation: juniper-data/juniper_data/api/security.py has full APIKeyAuth + RateLimiter + SecurityMiddleware
- 7.4 — Observability Foundation (structured logging, Prometheus metrics, Sentry)
- 7.5 — Dependency Management (lockfiles for Docker builds)
- 7.6 — Ecosystem Documentation Update

Key context:

- Canonical migration plan: juniper-cascor/notes/POLYREPO_MIGRATION_PLAN.md (lines 1599-1627 for Step 7.3)
- All repos on main, clean, pushed. juniper-ml has pre-existing uncommitted notes (unrelated)
- juniper-cascor has untracked .env (gitignored, not an issue)
- Canopy lives at JuniperCanopy/juniper_canopy/ (not juniper-canopy/)
- SSH push aliases: github.com-juniper-<name>:pcalnon/juniper-<name>.git
- Shared conda env: JuniperPython at /opt/miniforge3/envs/JuniperPython
- Each repo has its own AGENTS.md / CLAUDE.md — read before working on that repo

Verification commands:

```bash
# Verify all repos clean and on main
for d in juniper-cascor juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-ml; do echo "=== $d ===" && cd /home/pcalnon/Development/python/Juniper/$d && git status --short && git log --oneline -1 && echo; done
cd /home/pcalnon/Development/python/Juniper/JuniperCanopy/juniper_canopy && echo "=== juniper-canopy ===" && git status --short && git log --oneline -1

# Read Step 7.3 in migration plan
head -n 1627 /home/pcalnon/Development/python/Juniper/juniper-cascor/notes/POLYREPO_MIGRATION_PLAN.md | tail -n 29

# Read reference security implementation
cat /home/pcalnon/Development/python/Juniper/juniper-data/juniper_data/api/security.py
```

Git status:

All 7 repos on main, all pushed, no uncommitted work related to Phase 7.

---
