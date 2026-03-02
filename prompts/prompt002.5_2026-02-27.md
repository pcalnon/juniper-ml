# Microservices Roadmap

Continue the Juniper Microservices Architecture Development Roadmap. Begin Phase 6: Client Library Fakes.

## Completed so far

- Phases 1-5 complete — all merged to main across all repos
- Phase 5 (BackendProtocol): BackendProtocol abstraction with DemoBackend, ServiceBackend, create_backend() factory, 75 unit tests, mypy clean — merged as commit 82236b1 on juniper-canopy main
- Full test suite: 3324 passed, 19 skipped, 0 failed, 95% coverage
- Feature branch feature/phase5-backend-protocol deleted (local + remote), worktree cleaned up

## Remaining work — Phase 6 (14 tasks)

The authoritative task list is at:
/home/pcalnon/Development/python/Juniper/juniper-ml/notes/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md lines 2870-3291

## Tasks by repo

### juniper-cascor-client (Tasks 6.1-6.6)

- 6.1: Create juniper_cascor_client/testing/__init__.py
- 6.2: Create testing/scenarios.py — metric curves, topology templates, scenario data
- 6.3: Implement FakeCascorClient with scenario presets (idle, two_spiral_training, xor_converged, empty, error_prone)
- 6.4: Implement FakeCascorTrainingStream — async WebSocket stream simulation
- 6.5: Tests for FakeCascorClient
- 6.6: Tests for FakeCascorTrainingStream

### juniper-data-client (Tasks 6.7-6.10)

- 6.7: Create juniper_data_client/testing/__init__.py
- 6.8: Create testing/generators.py — synthetic spiral, xor, circle, moon datasets
- 6.9: Implement FakeDataClient with all methods
- 6.10: Tests for FakeDataClient

### juniper-canopy (Tasks 6.11-6.14)

- 6.11: Add client parameter to CascorServiceAdapter.__init__() for dependency injection
- 6.12: Integration test: ServiceBackend + CascorServiceAdapter + FakeCascorClient
- 6.13: Verify both client library test suites pass
- 6.14: Verify JuniperCanopy test suite passes with no regressions

## Key context

- Work spans 3 repos: juniper-cascor-client, juniper-data-client, juniper-canopy
- Use worktrees per the CLAUDE.md worktree procedures (centralized in /home/pcalnon/Development/python/Juniper/worktrees/)
- Each repo has its own AGENTS.md — read it before starting work
- All repos share the JuniperPython conda environment
- NPZ data contract: keys X_train, y_train, X_test, y_test, X_full, y_full, dtype float32
- FakeCascorClient must raise the same exception types as the real client (JuniperCascorClientError subclasses)
- Fakes go in testing/ submodule within each client library — no separate [test] extra needed
- Dependency order: 6.1-6.2 first (no deps), then 6.3-6.4, then 6.5-6.6 (tests), then 6.7-6.8, 6.9, 6.10, then 6.11-6.14

## Git status

- juniper-canopy/main at commit 82236b1 — clean (except unrelated feature/7.4-observability worktree)
- juniper-cascor-client/main — verify with git status
- juniper-data-client/main — verify with git status

## Verification for new thread

### Verify Phase 5 is on main

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
git log --oneline -1  # Should show 82236b1
```

### Verify client library repos are clean

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client && git status
cd /home/pcalnon/Development/python/Juniper/juniper-data-client && git status
```

### Read Phase 6 task definitions

File: /home/pcalnon/Development/python/Juniper/juniper-ml/notes/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md lines 2870-3291

#### Read each repo's AGENTS.md before working on it

---
