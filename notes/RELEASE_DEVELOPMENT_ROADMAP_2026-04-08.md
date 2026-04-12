# Juniper Project — Release Development Roadmap

**Date**: 2026-04-08
**Author**: Claude Code (Principal Engineer Review)
**Scope**: juniper-ml, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-deploy

---

## Roadmap Summary

This roadmap documents all required work as detailed, prioritized phases, steps, and tasks to bring all 6 Juniper applications to release-ready status. Tasks are ordered by priority and dependency.

**Total blockers**: 13 (1 originally reported blocker verified as already fixed)
**Total tasks**: 36
**Estimated effort**: 3-5 hours

---

## Phase 1: Critical Security & Code Fixes

**Priority**: P0 — MUST COMPLETE BEFORE ANY RELEASE
**Estimated effort**: 45 minutes
**Dependencies**: None

### 1.1 juniper-data: Path Traversal Fix (P0-SECURITY)

| Task | Description | File | Est. |
|---|---|---|---|
| 1.1.1 | Add `JUNIPER_DATA_IMPORT_DIR` env var to settings | api/settings.py | 5 min |
| 1.1.2 | Implement `_validate_file_path()` with realpath validation | generators/csv_import/generator.py | 15 min |
| 1.1.3 | Add path validation tests (absolute, traversal, symlink, valid) | tests/unit/test_csv_import.py | 10 min |
| 1.1.4 | Document breaking change in CHANGELOG.md [0.5.0] Security section | CHANGELOG.md | 2 min |
| 1.1.5 | Add `JUNIPER_DATA_IMPORT_DIR` to .env.example and docs | Multiple | 3 min |

**Approach**: Use `os.path.realpath()` to resolve the target path and verify it falls within the configured base directory. Reject absolute paths, `..` traversal, and symlinks that escape the boundary.

**Strengths**: Defense-in-depth, configurable, handles symlink attacks
**Weaknesses**: Breaking change for users with absolute paths
**Risks**: LOW — csv_import is not commonly used in production
**Guardrails**: Environment variable override, clear error messaging

### ~~1.2 juniper-data: Health Check Logic Fix~~ — RESOLVED

**Status**: VERIFIED FIXED (2026-04-08). Code at `api/routes/health.py:70` already reads:
`overall = "ready" if storage_dep.status == "healthy" else "degraded"` — correct behavior. **No action needed.**

### 1.3 juniper-deploy: Makefile Variable Fix (P0-CONFIG)

| Task | Description | File | Est. |
|---|---|---|---|
| 1.3.1 | Define `SECRETS_DIR` and `SECRETS_FILES` variables | Makefile | 5 min |
| 1.3.2 | Verify `make prepare-secrets` succeeds | Manual test | 2 min |
| 1.3.3 | Verify `make up` succeeds (without running services) | Manual test | 2 min |

**Approach**: Add variable definitions matching docker-compose.yml secrets configuration
**Strengths**: Simple, enables all downstream make targets
**Weaknesses**: None
**Risks**: None
**Guardrails**: CI validation of compose config already passes

---

## Phase 2: Code Quality Fixes

**Priority**: P1 — REQUIRED BEFORE RELEASE
**Estimated effort**: 25 minutes
**Dependencies**: None (can run parallel with Phase 1)

### 2.1 juniper-cascor-client: Duplicate Method (P1-QUALITY)

| Task | Description | File | Est. |
|---|---|---|---|
| 2.1.1 | Delete duplicate `_success_envelope()` (lines 138-145) | testing/fake_client.py | 1 min |
| 2.1.2 | Verify tests still pass | pytest tests/ | 2 min |

**Approach**: Simple deletion — both definitions are identical
**Risks**: None

### 2.2 juniper-cascor-client: wait_for_ready() Logic (P1-BUG)

| Task | Description | File | Est. |
|---|---|---|---|
| 2.2.1 | Change `is_alive()` to `is_ready()` in polling loop | client.py:80-90 | 2 min |
| 2.2.2 | Add test for wait_for_ready timeout expiration | tests/ | 5 min |
| 2.2.3 | Update FakeCascorClient.wait_for_ready if needed | testing/fake_client.py | 2 min |

**Approach**: Direct method substitution — the method name semantics require readiness checking
**Strengths**: Correct API contract
**Weaknesses**: May be slower to return true (readiness > liveness)
**Risks**: LOW — callers already have timeout parameter
**Guardrails**: Timeout mechanism provides safety net

### 2.3 juniper-cascor-client: Unused Import (P1-QUALITY)

| Task | Description | File | Est. |
|---|---|---|---|
| 2.3.1 | Remove `SCENARIO_DEFAULTS` from import line 21 | testing/fake_client.py | 1 min |

### 2.4 juniper-cascor-client: Type Errors (P1-QUALITY)

| Task | Description | File | Est. |
|---|---|---|---|
| 2.4.1 | Add `bool()` cast to `is_ready()` return | client.py:76 | 1 min |
| 2.4.2 | Add `# type: ignore[return-value]` to `_request()` | client.py:322 | 1 min |
| 2.4.3 | Add `# type: ignore[return-value]` to `command()` | ws_client.py:205 | 1 min |

**Approach**: Use explicit cast for bool returns, type: ignore for known library typing limitations
**Alternative**: Could use `cast()` from typing module for all three — more explicit but verbose

### 2.5 juniper-cascor-client: Version in Scenarios (P2-COSMETIC)

| Task | Description | File | Est. |
|---|---|---|---|
| 2.5.1 | Change version from "0.4.0" to "0.3.0" in meta field | testing/scenarios.py | 1 min |

---

## Phase 3: Changelog & Version Synchronization

**Priority**: P1 — REQUIRED BEFORE RELEASE
**Estimated effort**: 60-90 minutes
**Dependencies**: Phase 1 (code fixes inform changelog entries)

### 3.1 juniper-data: Version Sync (P0)

| Task | Description | File | Est. |
|---|---|---|---|
| 3.1.1 | Update __version__ from "0.4.2" to "0.5.0" | juniper_data/__init__.py | 1 min |
| 3.1.2 | Update LABEL version from "0.4.0" to "0.5.0" | Dockerfile | 1 min |
| 3.1.3 | Verify CHANGELOG v0.5.0 entry includes security fixes | CHANGELOG.md | 3 min |
| 3.1.4 | Add path traversal fix to CHANGELOG if not present | CHANGELOG.md | 2 min |

### 3.2 juniper-ml: Changelog & Version (P1)

| Task | Description | File | Est. |
|---|---|---|---|
| 3.2.1 | Decide version: v0.3.1 (patch) or v0.4.0 (minor) | Decision | 5 min |
| 3.2.2 | Review `git log` for all 228 commits since v0.3.0 | Git | 20 min |
| 3.2.3 | Categorize changes (Added/Changed/Fixed/Removed) | CHANGELOG.md | 20 min |
| 3.2.4 | Update pyproject.toml version | pyproject.toml | 1 min |
| 3.2.5 | Update CLAUDE.md/AGENTS.md version references | CLAUDE.md | 2 min |
| 3.2.6 | Create retroactive git tag v0.3.0 on bea883d | Git | 1 min |

### 3.3 juniper-cascor-client: Changelog (P1)

| Task | Description | File | Est. |
|---|---|---|---|
| 3.3.1 | Close [Unreleased] section | CHANGELOG.md | 1 min |
| 3.3.2 | Create [0.3.0] entry with date (2026-04-08) | CHANGELOG.md | 10 min |
| 3.3.3 | Document: FakeCascorClient, snapshots, workers, control stream | CHANGELOG.md | 5 min |
| 3.3.4 | Add comparison link ([0.3.0] vs [0.1.0]) | CHANGELOG.md | 1 min |

### 3.4 juniper-cascor-worker: Changelog & Tags (P1)

| Task | Description | File | Est. |
|---|---|---|---|
| 3.4.1 | Add [0.3.0] section documenting all changes since v0.1.1 | CHANGELOG.md | 15 min |
| 3.4.2 | Document WebSocket default, security hardening, CI | CHANGELOG.md | 5 min |
| 3.4.3 | Identify correct commit for retroactive v0.2.0 tag | Git | 5 min |
| 3.4.4 | Create retroactive git tag v0.2.0 | Git | 1 min |

---

## Phase 4: Validation & Release

**Priority**: P1 — FINAL GATE
**Estimated effort**: 30-45 minutes
**Dependencies**: Phases 1-3 complete

### 4.1 Full Validation Pass

| Task | Description | Est. |
|---|---|---|
| 4.1.1 | Re-run all test suites (6 applications) | 15 min |
| 4.1.2 | Re-run all pre-commit checks (6 applications) | 10 min |
| 4.1.3 | Cross-reference versions: pyproject.toml, __init__.py, CHANGELOG, AGENTS.md | 5 min |
| 4.1.4 | Verify git tag plan (which commits get which tags) | 5 min |

### 4.2 Commit & Push

| Task | Description | Est. |
|---|---|---|
| 4.2.1 | Commit changes per application in respective worktrees | 10 min |
| 4.2.2 | Push branches to origin | 5 min |
| 4.2.3 | Create PRs for all applications with changes | 10 min |

### 4.3 Merge & Tag

| Task | Description | Est. |
|---|---|---|
| 4.3.1 | Wait for CI to pass on all PRs | Variable |
| 4.3.2 | Merge PRs in dependency order | 10 min |
| 4.3.3 | Create git tags post-merge | 5 min |
| 4.3.4 | Create GitHub releases (triggers PyPI publish) | 10 min |

### 4.4 Post-Release Verification

| Task | Description | Est. |
|---|---|---|
| 4.4.1 | Verify PyPI packages are installable | 5 min |
| 4.4.2 | Verify Docker images build with correct tags | 5 min |
| 4.4.3 | Run smoke test of full stack via juniper-deploy | 10 min |
| 4.4.4 | Clean up worktrees (V2 procedure) | 5 min |

---

## Release Version Summary

| Application | Current | Release | Change Type |
|---|---|---|---|
| juniper-ml | 0.3.0 | **0.4.0** | Minor (major new features) |
| juniper-data | 0.5.0 (code: 0.4.2) | **0.5.0** | Sync only |
| juniper-data-client | 0.3.2 | **0.3.2** | Already ready |
| juniper-cascor-client | 0.3.0 | **0.3.0** | Changelog + fixes |
| juniper-cascor-worker | 0.3.0 | **0.3.0** | Changelog + tags |
| juniper-deploy | 0.2.0 | **0.2.0** | Makefile fix |

---

## Release Dependency Order

```
1. juniper-data v0.5.0          (no Juniper dependencies)
2. juniper-data-client v0.3.2   (depends on juniper-data API)
3. juniper-cascor-client v0.3.0 (depends on juniper-cascor API)
4. juniper-cascor-worker v0.3.0 (depends on juniper-cascor API)
5. juniper-ml v0.4.0            (meta-package: clients + worker)
6. juniper-deploy v0.2.0        (orchestrates all services)
```

---

## Task Priority Legend

| Priority | Meaning | Action |
|---|---|---|
| P0-SECURITY | Security vulnerability | Fix immediately, block release |
| P0-BUG | Critical bug | Fix before release |
| P0-CONFIG | Configuration breaks functionality | Fix before release |
| P1-QUALITY | Code quality issue (flake8/mypy) | Fix before release |
| P1-BUG | Non-critical bug | Fix before release |
| P2-COSMETIC | Cosmetic/documentation issue | Fix if time permits |

---

## Appendix: Per-Application Blocker Resolution Checklist

### juniper-ml (3 blockers)

- [ ] Decide release version (v0.3.1 or v0.4.0)
- [ ] Populate CHANGELOG [Unreleased] with 228 commits of changes
- [ ] Create retroactive git tag v0.3.0 on bea883d
- [ ] Update pyproject.toml and CLAUDE.md versions
- [ ] Re-run tests and pre-commit

### juniper-data (2 blockers)

- [ ] Implement path traversal validation in csv_import generator
- [x] ~~Fix health check logic (health.py:70)~~ — VERIFIED ALREADY FIXED
- [ ] Sync __init__.py and Dockerfile versions to 0.5.0
- [ ] Add path traversal fix to CHANGELOG
- [ ] Re-run tests and pre-commit

### juniper-data-client (0 blockers)

- [ ] No changes needed — ready for release
- [ ] Create git tag v0.3.2 and GitHub release

### juniper-cascor-client (5 blockers)

- [ ] Delete duplicate `_success_envelope()` method
- [ ] Remove unused `SCENARIO_DEFAULTS` import
- [ ] Fix `wait_for_ready()` to check `is_ready()`
- [ ] Fix type errors (3 locations)
- [ ] Close [Unreleased] and create [0.3.0] changelog entry
- [ ] Fix version in scenarios.py meta field
- [ ] Re-run tests and pre-commit

### juniper-cascor-worker (2 blockers)

- [ ] Add [0.3.0] section to CHANGELOG
- [ ] Create retroactive git tags (v0.2.0, v0.3.0)
- [ ] Re-run tests and pre-commit

### juniper-deploy (1 blocker)

- [ ] Define `SECRETS_DIR` and `SECRETS_FILES` in Makefile
- [ ] Verify `make prepare-secrets` and `make up` work
- [ ] Re-run tests and pre-commit
