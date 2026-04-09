# Juniper Ecosystem Release Preparation Plan

**Date**: 2026-04-08
**Scope**: juniper-ml, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-deploy
**Prerequisite**: Cross-Project Code Review (CROSS_PROJECT_CODE_REVIEW_2026-04-08.md)
**Purpose**: Phased plan to resolve all release blockers and prepare each application for deployment

---

## Target Release Versions

Based on the code review findings, the following release versions are recommended:

| Application | Current Declared | Recommended Release | Rationale |
|-------------|-----------------|---------------------|-----------|
| juniper-ml | 0.3.0 | 0.4.0 | Post-0.3.0 features (systemd, startup/shutdown scripts, worker integration) |
| juniper-data | 0.5.0 | 0.6.0 | Post-0.5.0 features (versioning, batch endpoints, Docker secrets, systemd) |
| juniper-data-client | 0.3.2 | 0.4.0 | New public API surface (6 methods) requires MINOR bump |
| juniper-cascor-client | 0.3.0 | 0.3.0 | Current version appropriate; needs changelog and tags |
| juniper-cascor-worker | 0.3.0 | 0.3.0 | Current version appropriate; needs changelog and tags |
| juniper-deploy | 0.2.0 | 0.2.0 | First formal release at documented version |

---

## Phase 1: Critical Security & Correctness Fixes

**Priority**: MUST complete before any release
**Estimated scope**: 6 applications, 10 critical issues

### 1.1 juniper-data: Version Synchronization

**Files to modify**:

- `juniper_data/__init__.py:17` — change `__version__ = "0.4.2"` to `"0.6.0"`
- `Dockerfile:36` — change `org.opencontainers.image.version="0.4.0"` to `"0.6.0"`
- `pyproject.toml:7` — update header comment to `Version: 0.6.0`
- `pyproject.toml:30` — change `version = "0.5.0"` to `"0.6.0"`

**Validation**: Run health endpoint and verify reported version; run `python -c "import juniper_data; print(juniper_data.__version__)"`.

### 1.2 juniper-data: CSV Import Path Traversal Fix

**Root cause**: `csv_import/generator.py:80-87` passes `file_path` directly to `Path()`.

**Recommended approach** (Option A — base directory restriction):

1. Add `JUNIPER_DATA_IMPORT_DIR` to `Settings` with default `/data/imports`
2. In `CsvImportGenerator.generate()`, resolve the user-provided path relative to the import directory
3. Validate that the resolved absolute path starts with the import directory (prevents `../` traversal)
4. Raise `ValidationError` if path escapes the import directory

**Alternative approach** (Option B — disable API exposure):

- Remove `csv_import` from the API generator registry
- Keep it available for direct Python usage only
- Lower risk but reduces functionality

**Strengths of A**: Preserves functionality, standard security pattern, configurable per deployment
**Weaknesses of A**: Requires new settings field, migration for existing deployments
**Risks**: Existing CSV import users must configure the import directory
**Recommended**: Option A

### 1.3 juniper-data-client: Version Alignment

**Files to modify**:

- `pyproject.toml` — bump version to `0.4.0`
- `juniper_data_client/__init__.py` — update `__version__` to `"0.4.0"`
- `juniper_data_client/testing/__init__.py` — update header to `0.4.0`
- `juniper_data_client/testing/fake_client.py` — update header to `0.4.0`
- `juniper_data_client/testing/generators.py` — update header to `0.4.0`

### 1.4 juniper-deploy: Network Isolation

**File**: `docker-compose.yml` lines 494-503

**Change**:

```yaml
networks:
  backend:
    driver: bridge
    internal: true    # ADD: prevent external connectivity
  data:
    driver: bridge
    internal: true    # ADD: prevent external connectivity
  frontend:
    driver: bridge
  monitoring:
    driver: bridge
```

**Validation**: `docker compose config --profiles full | grep -A2 "internal"`

**Risk assessment**:

- **Strength**: Matches documented security model; prevents container internet access on backend/data
- **Risk**: If any service on backend/data networks needs to pull external resources (e.g., HuggingFace datasets), it will fail. The `frontend` network (which juniper-canopy uses) remains external.
- **Mitigation**: Services needing external access should be on `frontend` network in addition to internal networks

### 1.5 juniper-cascor-worker: CHANGELOG & Tags

**CHANGELOG changes**: Add sections for v0.1.1, v0.3.0 covering:

- WebSocket-based `CascorWorkerAgent` (new default mode)
- Legacy mode deprecation with `CandidateTrainingWorker`
- `api_key` → `auth_token` rename with backward compatibility
- TLS/mTLS support
- Binary tensor framing protocol
- setuptools security fix (>=82.0)
- Pre-commit hooks and CI enhancements

### 1.6 juniper-ml: CHANGELOG & Tags

**CHANGELOG changes**: Populate [Unreleased] section, then rename to [0.4.0] covering:

- `juniper_plant_all.bash` and `juniper_chop_all.bash` startup/shutdown scripts
- Systemd integration (Phase 2)
- Cascor-worker integration (Phase 3)
- `worktree_cleanup.bash` V2
- `test_worktree_cleanup.py` regression tests
- Dependabot CI action bumps

---

## Phase 2: High-Priority Bug Fixes

**Priority**: SHOULD complete before release
**Estimated scope**: 18 issues across all 6 applications

### 2.1 juniper-ml: CI & Script Fixes

**2.1.1 CI path fix** (`ci.yml:244`):

- Change `bash scripts/generate_dep_docs.sh` to `bash util/generate_dep_docs.sh`

**2.1.2 PID parsing fix** (`util/juniper_chop_all.bash:275-325`):

**Approach A** (Recommended — `mapfile`):

```bash
mapfile -t JUNIPER_PIDS < "${JUNIPER_PROJECT_PID_FILE}"
```

Remove the `done < "${JUNIPER_PROJECT_PID_FILE}"` from the for loop.

**Approach B** (while-read loop):

```bash
while IFS= read -r line; do
    service_name="${line%%:*}"
    pid="${line##*:}"
    pid="${pid// /}"  # trim whitespace
    # ... process
done < "${JUNIPER_PROJECT_PID_FILE}"
```

**Strengths of A**: Minimal change, retains array indexing pattern
**Strengths of B**: More explicit parsing, handles whitespace in values
**Recommended**: Approach A for minimal diff; Approach B if refactoring the loop

**2.1.3 Add test_worktree_cleanup.py to CI** (`ci.yml:109-110`):
Add `python3 -m unittest -v tests/test_worktree_cleanup.py` to the test execution step.

**2.1.4 Fix chop_all defaults** (`util/juniper_chop_all.bash:69-71`):

- Remove hardcoded assignments at lines 69-71
- Let `${KILL_WORKERS:-0}` at line 82 take effect
- Change `WORKER_SEARCH_TERM` from `"cascor"` to `"juniper.cascor.worker"` or `"juniper-cascor-worker"`

### 2.2 juniper-data: Code Fixes

**2.2.1 n_spirals fallback** (`datasets.py:114`):

```python
# Before:
n_classes = arrays["y_train"].shape[1] if n_train > 0 else params.n_spirals

# After:
n_classes = arrays["y_train"].shape[1] if n_train > 0 else (
    arrays["y_test"].shape[1] if n_test > 0 else 2
)
```

**2.2.2 Dockerfile label** (`Dockerfile:36`):
Update `org.opencontainers.image.version` to match release version.

### 2.3 juniper-data-client: Test & Retry Fixes

**2.3.1 Add PATCH to retry allowed_methods** (`client.py:101`):

```python
allowed_methods=["HEAD", "GET", "POST", "PATCH", "DELETE"]
```

**2.3.2 Add HTTP-level tests for batch and versioning**:
Add `TestBatchOperations` and `TestVersioning` classes in `test_client.py` using `@responses.activate`. Cover:

- Success paths for all 6 methods
- 404 error paths
- Validation error paths
Target: raise `client.py` coverage from 75.68% to ~95%.

### 2.4 juniper-cascor-client: Semantic & Coverage Fixes

**2.4.1 Fix `wait_for_ready()`** (`client.py:86`):
Change `self.is_alive()` to `self.is_ready()`.

**2.4.2 Write CHANGELOG v0.2.0 and v0.3.0 entries** from git log.

**2.4.3 Add tests for uncovered FakeCascorClient methods**:
Cover `get_dataset_data()`, snapshot methods in `test_fake_client.py`.

### 2.5 juniper-cascor-worker: Thread Safety & Coverage

**2.5.1 Fix signal handler thread safety** (`worker.py:121`, `cli.py:95`):

**Approach A** (Recommended — `call_soon_threadsafe`):

```python
# In CascorWorkerAgent.__init__:
self._loop = None

# In run():
self._loop = asyncio.get_running_loop()

# In stop():
if self._loop:
    self._loop.call_soon_threadsafe(self._stop_event.set)
```

**Approach B** (threading.Event with async polling):
Replace `asyncio.Event` with `threading.Event` and poll it periodically in the async loop.

**Strengths of A**: Idiomatic asyncio, minimal code change
**Strengths of B**: Eliminates cross-thread asyncio usage entirely
**Risks of A**: `self._loop` may be None if `stop()` called before `run()` starts
**Recommended**: Approach A with a None guard

**2.5.2 Add core control flow tests**:
Add tests for `run()` → `_message_loop()` → `_handle_task_assign()` flow, `_heartbeat_loop`, and connection loss/reconnection. Target: `worker.py` above 80%.

### 2.6 juniper-deploy: Makefile & Dockerfile Fixes

**2.6.1 Fix Makefile variables** (`Makefile:70-72`):
Add at top of Makefile:

```makefile
SECRETS_DIR := secrets
SECRETS_FILES := $(SECRETS_DIR)/juniper_data_api_keys.txt \
    $(SECRETS_DIR)/juniper_cascor_api_keys.txt \
    $(SECRETS_DIR)/canopy_api_key.txt \
    $(SECRETS_DIR)/grafana_admin_password.txt
```

**2.6.2 Fix Dockerfile.test** (`Dockerfile.test:30`):
Remove `COPY conftest.py .` — conftest.py is already inside `tests/` which is copied on line 29.

**2.6.3 Correct AGENTS.md documentation**:

- Remove Cassandra from profile table (or re-add Cassandra service)
- Remove Redis from demo profile
- Remove Redis port binding reference
- Replace `make obs`/`make obs-demo` with `make monitor`

---

## Phase 3: Changelog & Documentation Updates

**Priority**: Required for release
**Estimated scope**: All 6 applications

### 3.1 Changelog Updates

For each application, compile changelog entries from git history:

| Application | Action | Target Section |
|-------------|--------|---------------|
| juniper-ml | Populate [Unreleased], rename to [0.4.0] | Added, Changed, Fixed, CI |
| juniper-data | Add [0.6.0] section | Added (versioning, batch, secrets, systemd), Fixed (postgres), Changed (CI) |
| juniper-data-client | Add [0.4.0] section | Added (batch ops, versioning, benchmarks), Fixed (PATCH retry) |
| juniper-cascor-client | Add [0.2.0] and [0.3.0] sections | Added (workers, snapshots, testing module), Fixed (response format) |
| juniper-cascor-worker | Add [0.1.1] and [0.3.0] sections | Added (WebSocket agent, TLS), Deprecated (legacy mode), Security |
| juniper-deploy | Restructure into [0.2.0] section | Added (all features), Security, Infrastructure |

### 3.2 README & Documentation Updates

| Application | Documents to Update |
|-------------|-------------------|
| juniper-data-client | README API table (+6 methods), REFERENCE.md (version + batch/versioning), QUICK_START.md (FakeDataClient class name) |
| juniper-cascor-client | README API table (+9 methods), WebSocket reconnection documentation |
| juniper-deploy | AGENTS.md (profile table, port bindings, Makefile targets), CHANGELOG image versions |

### 3.3 Release Description Documents

Draft release descriptions for each application (templates provided in the code review document). These should be refined and used as GitHub release notes.

---

## Phase 4: Git Tags & Pre-Release Validation

**Priority**: Required for release
**Sequence**: Must follow Phases 1-3

### 4.1 Create Missing Retroactive Tags

| Application | Tags to Create | At Commit |
|-------------|---------------|-----------|
| juniper-ml | v0.2.1, v0.3.0 | Identify from git log |
| juniper-data-client | v0.3.2 | Identify from git log |
| juniper-cascor-client | v0.2.0 | Identify from git log |
| juniper-cascor-worker | v0.2.0 | Identify from git log |

### 4.2 Pre-Release Validation Checklist

For each application, verify:

- [ ] All tests pass (`pytest -v` or `python3 -m unittest -v`)
- [ ] Coverage meets 80% threshold
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] CHANGELOG is complete and follows Keep a Changelog format
- [ ] Version is consistent across all files
- [ ] README and documentation are current
- [ ] Git working directory is clean
- [ ] All changes are committed and pushed

### 4.3 Build & Package Validation (PyPI packages only)

For juniper-ml, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker:

- [ ] `python -m build` succeeds
- [ ] `twine check dist/*` passes
- [ ] `pip install dist/*.whl` succeeds
- [ ] Import and version check passes
- [ ] Extras install correctly (where applicable)

### 4.4 Docker Validation (juniper-deploy)

- [ ] `docker compose config` validates for all profiles
- [ ] `docker compose build` succeeds for all service images
- [ ] `docker compose --profile full up -d` starts successfully
- [ ] All health endpoints respond
- [ ] `docker compose down` cleans up properly

---

## Phase 5: Release Execution

**Sequence**: After Phase 4 validation

### 5.1 Tag & Release Order

Releases must follow the dependency graph:

```
1. juniper-data (upstream, no Juniper dependencies)
2. juniper-data-client (depends on juniper-data API contract)
3. juniper-cascor-client (depends on juniper-cascor API contract)
4. juniper-cascor-worker (depends on juniper-cascor)
5. juniper-ml (meta-package, depends on all client packages)
6. juniper-deploy (orchestration, depends on all application images)
```

### 5.2 Per-Application Release Steps

For each application (in dependency order):

1. Create git tag: `git tag -a v<VERSION> -m "Release v<VERSION>"`
2. Push tag: `git push origin v<VERSION>`
3. Create GitHub release with release description
4. Verify CI publish workflow triggers and succeeds (PyPI packages)
5. Verify package installable from PyPI: `pip install <package>==<VERSION>`
6. Update downstream `pyproject.toml` dependency version pins if needed

### 5.3 Post-Release

- Update juniper-ml extras version requirements to match released versions
- Update juniper-deploy Docker image tags to match released versions
- Run full integration test with all released versions
- Update parent CLAUDE.md with new version numbers

---

## Risk Assessment

### Release Order Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| juniper-data publish fails | Blocks all downstream releases | Test with TestPyPI first; the publish workflow already does this |
| Version pin mismatch | juniper-ml installs wrong versions | Verify all extras resolve correctly before publishing juniper-ml |
| Docker image tag drift | juniper-deploy pulls wrong images | Pin to exact version tags, not `latest` |

### Rollback Plan

- All git tags can be deleted and recreated: `git tag -d v<VERSION> && git push --delete origin v<VERSION>`
- PyPI packages can be yanked (not deleted) if critical issues found post-release
- Docker images can be re-tagged

---

## Dependencies & Prerequisites

| Prerequisite | Status | Required By |
|-------------|--------|-------------|
| All tests passing | DONE (1394 tests across all apps) | Phase 4 |
| All pre-commit passing | DONE (all apps clean) | Phase 4 |
| Code review complete | DONE (this document) | Phase 1 |
| Worktrees for each affected repo | TO CREATE | Phase 1 |
| PyPI trusted publishing configured | TO VERIFY | Phase 5 |
| GitHub Actions secrets configured | TO VERIFY | Phase 5 |
