# Hardcoded Values Refactor Plan — juniper-ml

**Version**: 0.3.0
**Created**: 2026-04-08
**Status**: PLANNING — No source code modifications
**Companion Document**: `HARDCODED_VALUES_ANALYSIS.md`

---

## Phase 1: Utility Script Refactor (Priority: HIGH)

### Step 1.1: Parameterize CasCor API Utilities

**Files**: `util/get_cascor_*.bash` (6 files)
**Changes**: Add `CASCOR_URL=${CASCOR_URL:-http://localhost:8201}` at top of each script, construct URLs from this base.

### Step 1.2: Fix Hardcoded Absolute Path

**File**: `util/worktree_cleanup.bash`
**Changes**: Replace hardcoded `/home/pcalnon/Development/python/Juniper/juniper-ml` with dynamic detection using `git rev-parse --show-toplevel` or `$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)`

### Step 1.3: Make CasCor Host Configurable

**File**: `util/juniper_plant_all.bash`
**Changes**: Add `JUNIPER_CASCOR_HOST=${JUNIPER_CASCOR_HOST:-localhost}` for the one non-configurable host value

---

## Phase 2: Test Constants (Priority: LOW)

### Step 2.1: Extract Test Timeouts

**Files**: `tests/test_worktree_cleanup.py`, `tests/test_wake_the_claude.py`
**Changes**: Define timeout and polling constants at module top or in shared fixture

---

## Phase 3: Validation (Priority: HIGH)

### Step 3.1: Run Test Suite

```bash
python3 -m unittest -v tests/test_wake_the_claude.py
python3 -m unittest -v tests/test_check_doc_links.py
python3 -m unittest -v tests/test_worktree_cleanup.py
bash scripts/test_resume_file_safety.bash
```

### Step 3.2: Pre-commit Hooks

```bash
pre-commit run --all-files
```

---

## Phase 4: Documentation & Release (Priority: MEDIUM)

### Step 4.1: Update AGENTS.md

### Step 4.2: Update CHANGELOG.md

### Step 4.3: Create Release Description
