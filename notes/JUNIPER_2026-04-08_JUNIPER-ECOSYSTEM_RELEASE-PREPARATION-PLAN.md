# Juniper Project — Release Preparation Plan

**Date**: 2026-04-08
**Author**: Claude Code (Principal Engineer Review)
**Scope**: juniper-ml, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-deploy
**Purpose**: Phased plan to resolve all release blockers and prepare applications for deployment

---

## Plan Overview

This plan addresses 14 release blockers across 5 applications (juniper-data-client is already release-ready). Work is organized into 4 phases with clear dependencies and prioritization.

**Estimated total effort**: 3-5 hours
**Critical path**: Phase 1 (code fixes) -> Phase 2 (metadata) -> Phase 3 (validation) -> Phase 4 (release)

---

## Phase 1: Code-Level Fixes (Priority: CRITICAL)

These are the only blockers that require actual source code changes. They must be fixed first because they affect application behavior and security.

### Step 1.1: Fix juniper-data Path Traversal Vulnerability

**Application**: juniper-data
**File**: `juniper_data/generators/csv_import/generator.py:81`
**Priority**: CRITICAL (security vulnerability)
**Estimated time**: 30 minutes

**Problem**: The CSV import generator accepts arbitrary file paths without validation, enabling path traversal attacks (e.g., `../../../etc/passwd`).

**Remediation Options**:

**Option A: Environment-configured allowlist directory (RECOMMENDED)**
```python
import os

IMPORT_BASE_DIR = os.environ.get("JUNIPER_DATA_IMPORT_DIR", "/data/imports")

def _validate_file_path(file_path: str) -> str:
    """Validate file path is within allowed base directory."""
    base = os.path.realpath(IMPORT_BASE_DIR)
    resolved = os.path.realpath(os.path.join(base, file_path))
    if not resolved.startswith(base + os.sep) and resolved != base:
        raise ValueError(f"Path '{file_path}' is outside allowed directory")
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"File not found: {resolved}")
    return resolved
```

- **Strengths**: Configurable, defense-in-depth (realpath resolves symlinks), clear error messages
- **Weaknesses**: Requires setting env var for non-default locations
- **Risks**: Existing users with absolute paths will break (breaking change)
- **Guardrails**: Environment variable override, clear error messages

**Option B: Reject absolute paths and traversal patterns only**
```python
def _validate_file_path(file_path: str) -> str:
    if os.path.isabs(file_path):
        raise ValueError("Absolute paths not allowed")
    if ".." in file_path.split(os.sep):
        raise ValueError("Path traversal not allowed")
    return file_path
```

- **Strengths**: Simpler, less likely to break existing usage
- **Weaknesses**: Still allows reading from CWD (less restrictive), doesn't resolve symlinks
- **Risks**: Symlink-based traversal still possible
- **Guardrails**: None beyond basic validation

**Recommendation**: Option A is recommended. The security benefit outweighs the migration cost. Document the breaking change in CHANGELOG and provide `JUNIPER_DATA_IMPORT_DIR` environment variable.

**Tests to add**:
- Test rejection of absolute paths (`/etc/passwd`)
- Test rejection of traversal patterns (`../../etc/passwd`)
- Test rejection of paths outside base directory
- Test acceptance of valid relative paths within base directory
- Test symlink resolution behavior

### ~~Step 1.2: Fix juniper-data Health Check Logic~~ — RESOLVED

**Status**: VERIFIED FIXED (2026-04-08)
**File**: `juniper_data/api/routes/health.py:70`

The code at line 70 already reads: `overall = "ready" if storage_dep.status == "healthy" else "degraded"` — this is correct. The initial audit reported stale analysis. **No action needed.**

### Step 1.3: Fix juniper-cascor-client Duplicate Method

**Application**: juniper-cascor-client
**File**: `juniper_cascor_client/testing/fake_client.py`
**Priority**: HIGH (code quality, flake8 F811)
**Estimated time**: 2 minutes

**Problem**: `_success_envelope()` method defined twice (lines 102 and 139). Second definition shadows first.

**Fix**: Delete lines 138-145 (the duplicate definition). Both definitions are identical.

**Analysis**:
- **Strengths**: Simple deletion, no behavior change
- **Risks**: None — definitions are identical
- **Guardrails**: Existing tests will catch any regression

### Step 1.4: Fix juniper-cascor-client wait_for_ready() Logic

**Application**: juniper-cascor-client
**File**: `juniper_cascor_client/client.py:80-90`
**Priority**: MEDIUM (API contract violation)
**Estimated time**: 5 minutes

**Problem**: `wait_for_ready()` calls `is_alive()` (liveness check) instead of `is_ready()` (readiness check with network loaded verification).

**Current code**:
```python
def wait_for_ready(self, timeout=30.0, poll_interval=0.5):
    # ... polling loop ...
    if self.is_alive():  # BUG: checks liveness, not readiness
        return True
```

**Fix**:
```python
    if self.is_ready():  # CORRECT: checks readiness
        return True
```

**Analysis**:
- **Strengths**: Correct semantics — "wait for ready" should check readiness
- **Weaknesses**: `is_ready()` may take longer to become true than `is_alive()`
- **Risks**: Consumer code that relied on quick `wait_for_ready()` returns may timeout. Unlikely since the method name implies readiness.
- **Guardrails**: Timeout parameter already exists for callers to control wait duration

### Step 1.5: Remove juniper-cascor-client Unused Import

**Application**: juniper-cascor-client
**File**: `juniper_cascor_client/testing/fake_client.py:21`
**Priority**: LOW (code cleanliness)
**Estimated time**: 1 minute

**Fix**: Remove `SCENARIO_DEFAULTS` from the import line.

### Step 1.6: Fix juniper-cascor-client Type Errors

**Application**: juniper-cascor-client
**Files**: `client.py:76`, `client.py:322`, `ws_client.py:205`
**Priority**: LOW (type safety)
**Estimated time**: 10 minutes

**Remediation Options**:

**Option A: Add type: ignore comments (RECOMMENDED for speed)**
```python
return result.get("details", {}).get("network_loaded", False)  # type: ignore[return-value]
```

**Option B: Add explicit casts**
```python
return bool(result.get("details", {}).get("network_loaded", False))
```

**Recommendation**: Option B for `is_ready()` (bool cast is correct), Option A for `_request()` and `command()` (json return typing is a known requests/json library limitation).

### Step 1.7: Fix juniper-deploy Makefile Variables

**Application**: juniper-deploy
**File**: `Makefile:71-72`
**Priority**: CRITICAL (makes `make up` unusable)
**Estimated time**: 5 minutes

**Problem**: `SECRETS_DIR` and `SECRETS_FILES` used in `prepare-secrets` target but never defined.

**Fix**: Add variable definitions near the top of the Makefile:
```makefile
SECRETS_DIR := ./secrets
SECRETS_FILES := \
    ./secrets/juniper_data_api_keys.txt \
    ./secrets/juniper_cascor_api_keys.txt \
    ./secrets/canopy_api_key.txt \
    ./secrets/grafana_admin_password.txt
```

**Analysis**:
- **Strengths**: Simple addition, enables all dependent targets
- **Risks**: File list must match docker-compose.yml secrets configuration
- **Guardrails**: `prepare-secrets` only creates empty placeholder files if missing

---

## Phase 2: Metadata & Documentation Updates (Priority: HIGH)

These are changelog, version, and git tag updates. They require no code changes but are essential for release consistency.

### Step 2.1: Update juniper-ml Changelog and Version

**Decision required**: Should the next release be v0.3.1 (patch) or v0.4.0 (minor)?

Given 228 unreleased commits including major features (systemd service management), **v0.4.0 is recommended**.

**Tasks**:
1. Update `pyproject.toml` version to 0.4.0
2. Populate CHANGELOG.md [Unreleased] -> [0.4.0] with categorized changes:
   - **Added**: systemd service management, juniper-all-ctl, startup/shutdown overhauls
   - **Changed**: Script improvements, CI/CD updates
   - **Fixed**: Script regressions, bug fixes
3. Create git tag v0.3.0 on commit bea883d (retroactive)
4. After release: create git tag v0.4.0
5. Update CLAUDE.md/AGENTS.md version references

### Step 2.2: Update juniper-data Version Sync

**Tasks**:
1. Update `juniper_data/__init__.py` __version__ from "0.4.2" to "0.5.0"
2. Update `Dockerfile` LABEL version from "0.4.0" to "0.5.0"
3. Verify CHANGELOG already documents v0.5.0 (it does)

### Step 2.3: Update juniper-cascor-client Changelog

**Tasks**:
1. Close [Unreleased] section in CHANGELOG.md
2. Create [0.3.0] entry with date
3. Document: FakeCascorClient, snapshot endpoints, worker status endpoints, CascorControlStream
4. Fix version in scenarios.py meta field from "0.4.0" to "0.3.0"

### Step 2.4: Update juniper-cascor-worker Changelog and Tags

**Tasks**:
1. Add [0.3.0] section to CHANGELOG.md documenting:
   - WebSocket worker as primary mode
   - Security hardening (setuptools >= 82.0)
   - AGENTS.md comprehensive documentation
   - CI/CD improvements
2. Create git tag v0.2.0 at appropriate historical commit
3. Create git tag v0.3.0 on current HEAD (after changelog update)

---

## Phase 3: Validation (Priority: HIGH)

After all fixes and updates, re-validate everything.

### Step 3.1: Re-run All Test Suites

```bash
# juniper-ml
cd /home/pcalnon/Development/python/Juniper/juniper-ml && python3 -m unittest -v tests/test_wake_the_claude.py tests/test_check_doc_links.py tests/test_worktree_cleanup.py

# juniper-data
cd /home/pcalnon/Development/python/Juniper/juniper-data && python3 -m pytest juniper_data/tests/ -v -m "not integration and not performance"

# juniper-data-client
cd /home/pcalnon/Development/python/Juniper/juniper-data-client && python3 -m pytest tests/ -v --cov=juniper_data_client --cov-fail-under=80

# juniper-cascor-client
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client && python3 -m pytest tests/ -v --cov=juniper_cascor_client --cov-fail-under=80

# juniper-cascor-worker
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-worker && python3 -m pytest tests/ -v --cov=juniper_cascor_worker --cov-fail-under=80

# juniper-deploy
cd /home/pcalnon/Development/python/Juniper/juniper-deploy && docker compose config --quiet && python3 -m pytest tests/ -v
```

### Step 3.2: Re-run All Pre-commit Checks

```bash
for repo in juniper-ml juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-deploy; do
    echo "=== $repo ==="
    cd /home/pcalnon/Development/python/Juniper/$repo && pre-commit run --all-files
    echo
done
```

### Step 3.3: Verify Version Consistency

For each application, verify:
- pyproject.toml version matches \_\_init\_\_.py
- CHANGELOG latest entry matches version
- Git tag will match version
- AGENTS.md/CLAUDE.md references correct version

### Step 3.4: Verify Changelog Completeness

Cross-reference `git log` output against CHANGELOG entries for each application:
```bash
for repo in juniper-ml juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-deploy; do
    echo "=== $repo ==="
    cd /home/pcalnon/Development/python/Juniper/$repo && git log --oneline $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~30)..HEAD
    echo
done
```

---

## Phase 4: Release Execution (Priority: NORMAL)

### Step 4.1: Create Worktrees for Each Application

Per the Worktree Setup Procedure, create isolated worktrees for each application that needs changes:

```bash
# For each application needing fixes:
cd /home/pcalnon/Development/python/Juniper/<repo>
git fetch origin && git checkout main && git pull origin main
BRANCH_NAME="release/v<version>-prep"
git branch "$BRANCH_NAME" main
# ... (full worktree creation per WORKTREE_SETUP_PROCEDURE.md)
```

### Step 4.2: Apply Fixes in Worktrees

Apply all Phase 1 and Phase 2 changes in their respective worktrees.

### Step 4.3: Commit, Push, and Create PRs

For each application with changes:
1. Stage and commit changes
2. Push branch to origin
3. Create PR with release preparation description
4. Wait for CI to pass
5. Merge PR

### Step 4.4: Tag Releases

After PRs are merged:
```bash
# For each application:
cd /home/pcalnon/Development/python/Juniper/<repo>
git checkout main && git pull origin main
git tag v<version>
git push origin v<version>
```

### Step 4.5: Create GitHub Releases

For each application (triggers publish workflows):
```bash
gh release create v<version> --title "v<version>" --notes-file RELEASE_NOTES.md
```

### Step 4.6: Verify PyPI Publication

After GitHub Actions publish workflow completes:
```bash
pip install juniper-data-client==0.3.2
pip install juniper-cascor-client==0.3.0
pip install juniper-cascor-worker==0.3.0
pip install juniper-ml==0.4.0
```

### Step 4.7: Worktree Cleanup

Per WORKTREE_CLEANUP_PROCEDURE_V2.md, clean up all worktrees after successful releases.

---

## Dependency Order

Releases should be executed in dependency order to ensure consumers can resolve their dependencies:

1. **juniper-data** (v0.5.0) — upstream service, no Juniper dependencies
2. **juniper-data-client** (v0.3.2) — already ready, depends on juniper-data API
3. **juniper-cascor-client** (v0.3.0) — depends on juniper-cascor API
4. **juniper-cascor-worker** (v0.3.0) — depends on juniper-cascor API
5. **juniper-ml** (v0.4.0) — meta-package, depends on client/worker packages
6. **juniper-deploy** (v0.2.0) — orchestrates all services, independent of pip packages

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Path traversal fix breaks CSV import users | LOW | MEDIUM | Document breaking change, provide env var |
| wait_for_ready() change causes timeouts | LOW | LOW | Existing timeout parameter provides control |
| Version bump causes dependency resolution issues | LOW | HIGH | Test install from TestPyPI before production |
| Changelog gap causes confusion | MEDIUM | LOW | Be thorough in documenting all changes |
| Missing git tags cause CI/CD issues | LOW | MEDIUM | Create tags in correct order |

---

## Success Criteria

All of the following must be true before declaring release complete:

- [ ] All 14 release blockers resolved
- [ ] All test suites pass (1,311+ tests)
- [ ] All pre-commit checks pass (106 hooks)
- [ ] Version consistency verified across all config files
- [ ] Changelogs complete and accurate
- [ ] Git tags created for all new versions
- [ ] GitHub releases created (triggers publish)
- [ ] PyPI packages verified installable
- [ ] Docker images tagged with semantic versions
- [ ] Worktrees cleaned up
