# Continue v7 §20/§21 (CFG-XX / API-XX) — Remaining Items After CFG-06

## Reference Thread

Continuation of the CFG-XX / API-XX series most recently advanced through CFG-06. When you need verbatim details of what shipped, use `read_thread` on the immediately-preceding thread (Paul will paste the ID); otherwise rely on the public artifacts cited below — the working document and per-PR descriptions cover everything load-bearing.

## Working Document

@notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md (juniper-ml) — see **§2.2 v7.0.1 → v7.0.2 status pass** for the live status table this session built and maintains.

## Description

I have been working through the v7 roadmap's Configuration (§20) and API/Protocol (§21) items, one or two at a time, in their own design-first PRs. As of 2026-05-23 the roadmap §2.2 audit pass shipped, every confirmed-shipped item is marked, and the remaining work is bucketed into "Confirmed TODO" (4 items) and "Ambiguous, needs investigation" (5 items).

## Completed in this session

- **CFG-16** (canopy PR #312): consolidate `CASCOR_DEMO_MODE` + `CASCOR_SERVICE_URL` onto Settings fields (no deprecation timeline change — Settings validators already deprecated).
- **v7 §2.2 status pass** (juniper-ml #317): swept all 15 remaining §20/§21 items, catalogued 7 newly-discovered-shipped + 5 confirmed-TODO + 5 ambiguous.
- **CFG-06** full arc — 10 PRs across 4 repos + 1 PyPI release:
  - Design doc (cascor-worker #84)
  - juniper-config-tools migration plan (juniper-ml #318)
  - juniper-config-tools 0.1.0 PyPI package (juniper-ml #320 + release tag) — stdlib-only env-var alias helper
  - Worker implementation (cascor-worker #86) — 15 ENV_* now `JUNIPER_CASCOR_WORKER_*`, legacy via `juniper-config-tools.env_with_legacy_alias`
  - Roadmap §2.2 mark-shipped (juniper-ml #321)
  - Deploy compose + Helm rename (juniper-deploy #80)
  - Worker docs sweep (cascor-worker #87)
  - Deploy REFERENCE.md fix (juniper-deploy #81)

## Remaining work

### Confirmed TODO (file:line evidence in §2.2)

1. **CFG-01** — canopy `pyproject.toml` lacks `torch` in `[project] dependencies`; `src/backend/demo_backend.py:45` imports it unconditionally. May be transitive via worker; verify before adding.
2. **CFG-02** — cascor `pyproject.toml:44` still has `"sentry-sdk>=2.0.0"` in core deps; should move to optional `[sentry]` extra.
3. **CFG-09** — canopy `src/settings.py:172` defaults `audit_log_path` to `/var/log/canopy/audit.log` (requires root). User-space default needed.
4. **API-06** — cascor-client `constants.py` has no `candidate_progress` / `WS_MSG_TYPE_CANDIDATE_PROGRESS`; cascor server already broadcasts it. Add constant + client handler (XREPO-17).

### Ambiguous — need deeper investigation before scoping

5. **CFG-07** — port 8200/8201 confusion. Compose parameterizes `${CASCOR_HOST_PORT:-8201}:${CASCOR_PORT:-8200}`; partial docs only. Check if a dedicated docs section closes the item.
6. **CFG-08** — rate-limit defaults differ across services. Roadmap Approach A was "document differences" — confirm whether central docs (e.g. `juniper-ml/docs/REFERENCE.md`) cover it.
7. **API-03** — canopy `src/demo_mode.py` has no formal TRANSITIONS dict; verify whether FAILED/COMPLETED → STOPPED auto-reset is present.
8. **API-04** — no `fake_client.py` in cascor-client; may have been renamed. `rg -l 'FakeClient'` across cascor-client + cascor.
9. **API-05** — cross-service error envelope. cascor uses `ResponseEnvelope` (API-09); data still emits raw `JSONResponse({"detail": …})` in `juniper_data/api/app.py:138, 146`; canopy unclear. Inventory needed.

## Key context / patterns established (carry forward)

- **Roadmap staleness rule**: re-verify each item against current code via `rg` + `git log --grep` before any worktree. The §2.2 audit hit ~67% already-shipped — same rate likely applies to the remaining ambiguous items.
- **Design-first**: items with multiple approaches or cross-repo impact get a `notes/<TOPIC>_DESIGN_<DATE>.md` PR first. CFG-04 / CFG-16 / CFG-09 / CFG-02 are mechanical enough to skip. CFG-01 (torch dep) and CFG-07/08/API-03/04/05 likely warrant designs.
- **Cleanup gate (mandatory)**: never delete branches/worktrees until Paul says "PR merged" AND `gh pr view <N>` confirms `state=MERGED` with non-null `mergedAt`. Two-gate rule, no exceptions.
- **Sequential PR flow**: Paul prefers one PR open at a time. Wait for explicit "PR merged" before opening the next, even when PRs are in different repos.
- **`juniper-config-tools` 0.1.0 is now available** on PyPI for any future env-var prefix migration. Stdlib-only — safe for cascor-worker (no Pydantic at runtime). See `notes/JUNIPER_CONFIG_TOOLS_PYPI_MIGRATION_PLAN_2026-05-22.md` and `juniper-cascor-worker/notes/CFG_06_ENV_PREFIX_CONVERGENCE_DESIGN_2026-05-22.md` for the pattern.
- **Worktrees**: branch from `origin/main` (not local `main`) since other Claude sessions may leave local `main` divergent — pattern is `git branch <name> origin/main && git worktree add ...`.
- **CHANGELOG**: every PR adds an `[Unreleased]` entry; version bumps tied to runtime-affecting changes only.

## Suggested next item

CFG-01 (canopy torch dep) — small, mechanical, likely no design doc needed. Verify whether torch is transitive via `juniper-cascor-worker` (canopy's `[clients]`-extra-pulled deps), and either:

- (a) Add explicit `"torch>=2.0.0"` to canopy core deps (matches CFG-01's roadmap Approach A); OR
- (b) Document the transitive dep with a comment in pyproject explaining the demo_backend.py import.

Re-verify per the staleness rule before any worktree.

## Active git state at handoff

- All session worktrees cleaned.
- Repos at:
  - juniper-ml `origin/main`: `dad60ff` (§2.2 mark-shipped #321)
  - juniper-cascor-worker `origin/main`: `a303e2e` (worker docs sweep #87)
  - juniper-deploy `origin/main`: `fc52295` (REFERENCE.md fix #81)
  - juniper-canopy `origin/main`: ahead of where this session last touched (CFG-16 #312); refetch to confirm.
- juniper-config-tools 0.1.0 live on PyPI.

## Verification on entry

```bash
# Confirm origin/main HEADs match the handoff snapshot
cd /home/pcalnon/Development/python/Juniper/juniper-ml          && git fetch origin --prune && git log --oneline -1 origin/main
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-worker && git fetch origin --prune && git log --oneline -1 origin/main
cd /home/pcalnon/Development/python/Juniper/juniper-deploy      && git fetch origin --prune && git log --oneline -1 origin/main
cd /home/pcalnon/Development/python/Juniper/juniper-canopy      && git fetch origin --prune && git log --oneline -1 origin/main

# Confirm juniper-config-tools 0.1.0 still resolvable from PyPI
pip index versions juniper-config-tools | head -2

# Re-verify the next-item-suggested status (CFG-01)
rg -n 'torch' /home/pcalnon/Development/python/Juniper/juniper-canopy/pyproject.toml
rg -n 'import torch' /home/pcalnon/Development/python/Juniper/juniper-canopy/src/backend/demo_backend.py

# Read §2.2 for the current roadmap status table
sed -n '146,190p' /home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md
```

After verification, ask which item to start with (Confirmed TODO recommended) and proceed under the design-first + sequential + cleanup-gate patterns above.

---
