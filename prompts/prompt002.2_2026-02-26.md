# Microservices Architecture Changes

Continue developing MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md by adding
detailed implementation plans for the Modes of Operation section (Section 3 from
MICROSERVICES_ARCHITECTURE_ANALYSIS.md).

## Completed so far

- Created juniper-ml/notes/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md
- Wrote detailed development roadmaps for all four Coordinated Application Startup phases:
  - Phase 1: Makefile + Docker Compose (Immediate) — 10 sections, 7 tasks
  - Phase 2: systemd Service Units (Near-Term) — 11 sections, 14 tasks
  - Phase 3: Docker Compose Profiles (Near-Term) — 12 sections, 15 tasks
  - Phase 4: Kubernetes via k3s (Intermediate) — 13 sections, 17 tasks

## Remaining work

- Add new sections to MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md covering the Modes of Operation roadmap, following the phased recommendation from MICROSERVICES_ARCHITECTURE_ANALYSIS.md Section 3.5:
  - Phase 1 (Immediate): Refactor Option 1 — unify DemoMode and CascorServiceAdapter behind a common BackendProtocol interface. Eliminate scattered if/else branching in main.py.
  - Phase 2 (Near-term): Adopt Option 3 — add FakeCascorClient and FakeDataClient to client libraries. Use dependency injection in CascorServiceAdapter to swap real and fake clients. Improves unit testing.
  - Phase 3 (With Docker): Adopt Option 5 — add a demo profile to Docker Compose that runs real CasCor with auto-start configuration. Most realistic demo experience for stakeholders.

## Key context

- The roadmap file is at: juniper-ml/notes/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md
- The analysis file is at: juniper-ml/notes/MICROSERVICES_ARCHITECTURE_ANALYSIS.md
- CLAUDE.md has been updated: JuniperCanopy/ is now legacy. The active dashboard code may have moved or been absorbed into juniper-cascor or another active repo.  Verify before referencing file paths.
- Active repos: juniper-cascor, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-ml, juniper-deploy
- Legacy dirs (no .git): JuniperCanopy/, JuniperCascor/, JuniperData/
- The existing demo mode implementation is in JuniperCanopy/juniper_canopy/src/demo_mode.py (~1100 lines) — this is legacy code that the new roadmap should plan to migrate/refactor
- CascorServiceAdapter is at JuniperCanopy/juniper_canopy/src/backend/cascor_service_adapter.py
- Config: JuniperCanopy uses YAML+env vars (ConfigManager), cascor/data use Pydantic BaseSettings
- All services use FastAPI + uvicorn, health endpoints at /v1/health, /v1/health/live, /v1/health/ready
- This is a planning task only — NO code changes

## Verification for new thread

- Read juniper-ml/notes/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md to see current state
- Read juniper-ml/notes/MICROSERVICES_ARCHITECTURE_ANALYSIS.md Section 3 for the analysis
- Read the parent CLAUDE.md at /home/pcalnon/Development/python/Juniper/CLAUDE.md for
  updated ecosystem structure
- Check if JuniperCanopy code has been migrated to an active repo

## Git status

- juniper-ml/notes/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md is a new untracked file
- No other changes in flight
- No active worktree for this task (planning only, no code changes)

---
