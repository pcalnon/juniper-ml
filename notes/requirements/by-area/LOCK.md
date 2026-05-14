# Requirements — LOCK

**Area**: lockfile-and-deps — uv lockfiles, pyproject pins, dep updates, env rebuilds

**Total entries**: 12

**By status**: proposed=8 | shipped=4

**By priority**: P0=2 | P1=2 | P2=3 | P3=5

**By owner**: can=5 | cas=3 | ccl=2 | dat=1 | ml=1

---

### JR-CAS-LOCK-001 — Add missing PyYAML, h5py, pytest-cov, psutil dependencies to conda environment.

**Status**: shipped  **Priority**: P0  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 256-306)

### JR-DAT-LOCK-001 — Dependabot configuration at .github/dependabot.yml with weekly schedule, grouped updates, PR limits.

**Status**: shipped  **Priority**: P0  **Category**: LOCK  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 242-323)

**Notes**:

RD-002 complete during migration 2026-02-21. File present, 3 dependabot PRs open.

### JR-CCL-LOCK-001 — Add JUNIPER_CASCOR_API_KEY environment variable fallback for API key authentication.

**Status**: shipped  **Priority**: P1  **Category**: LOCK  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 43-46)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAN-LOCK-001 — pyproject.toml must define 'dev' extra for dependency management.

**Status**: proposed  **Priority**: P1  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 116-116)

**Detail**:

Issue 2.1.4: Missing dev extra for development dependencies. Define
[project.optional-dependencies] with 'dev' key including test/lint tools.

### JR-CCL-LOCK-002 — Propagate V2 worktree cleanup procedure (CWD-trap bug fix) to juniper-cascor-client.

**Status**: shipped  **Priority**: P2  **Category**: LOCK  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 90-96)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-ML-LOCK-001 — 2.8 juniper-ml.

**Status**: proposed  **Priority**: P2  **Category**: LOCK  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 369-381)

**Detail**:

| ML-01 | **Medium** | `scripts/wake_the_claude.bash` | 37      | `DEBUG="${TRUE}"` hardcoded ON in production — all invocations emit debug output               |

### JR-CAS-LOCK-002 — Move dill to test-only dependencies or add proper import guard - currently undeclared runtime dep.

**Status**: proposed  **Priority**: P2  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 532-544)

**Detail**:

check_object_pickleability in src/utils/utils.py:248 imports dill (not in dependencies).
Will crash with ModuleNotFoundError if called. Move to test dependencies or add guard.

### JR-CAN-LOCK-002 — Black code formatter must have py314 in target-version.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 230-230)

**Detail**:

Issue 5.1.4: pyproject.toml Black config needs py314 for Python 3.14 compatibility.
Add to target-version list.

### JR-CAN-LOCK-003 — CASCOR_SNAPSHOT_DIR env var must be migrated to JUNIPER_CANOPY_SNAPSHOT_DIR.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 229-229)

**Detail**:

Issue 5.1.3: Old env var still referenced. Support both for compatibility
but document migration path and plan removal date.

### JR-CAN-LOCK-004 — CPU-only conda environment must be created for deployment without CUDA.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 231-231)

**Detail**:

Issue 5.1.5: Current environment assumes CUDA. Create environment-cpu.yml
with PyTorch CPU variant and document usage.

### JR-CAN-LOCK-005 — Pre-commit hook suite must be auto-updated.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 253-253)

**Detail**:

Issue 5.4.3: pre-commit hooks may be outdated. Run `pre-commit autoupdate`
to refresh all hook versions and update .pre-commit-config.yaml.

### JR-CAS-LOCK-003 — Reconcile version across pyproject.toml, file headers, and API response metadata.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 820-824)

**Detail**:

Consider using single-source-of-truth version via importlib.metadata.version() instead of file header strings.

