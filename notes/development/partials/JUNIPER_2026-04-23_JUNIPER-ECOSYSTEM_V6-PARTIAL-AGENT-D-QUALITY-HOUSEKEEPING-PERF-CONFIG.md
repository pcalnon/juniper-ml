# V6 Partial — Agent D: Code Quality, Housekeeping, Performance, Configuration

**Sections Covered**: 6 (Code Quality), 12 (Housekeeping), 16 (Performance), 20 (Configuration)
**Generated**: 2026-04-22
**Source Verification**: Key items verified against live codebase

---

### Issue Remediations, Section 6 — juniper-cascor

#### CLN-CC-01: Delete Legacy `remote_client/` Directory

**Current Code**: `src/remote_client/` — 3 files, superseded by juniper-cascor-worker.
**Root Cause**: Legacy code from pre-polyrepo era not cleaned up.
**Cross-References**: CLN-CC-01 = HSK-02

**Approach A — Delete Directory**:
- *Implementation*: `git rm -r src/remote_client/`. Update `.gitignore` if needed.
- *Strengths*: 10-minute cleanup; removes 3 files of dead code.
- *Weaknesses*: None.
- *Risks*: None — zero callers verified.
- *Guardrails*: Grep for `remote_client` imports before deletion.

**Recommended**: Approach A — trivial deletion of dead code.

---

#### CLN-CC-02: Delete Stale `check.py` Duplicate (600 Lines)

**Current Code**: `src/spiral_problem/check.py` — 600-line copy of spiral_problem.py.
**Root Cause**: Stale duplicate from development; never referenced.
**Cross-References**: CLN-CC-02 = HSK-03

**Approach A — Delete File**:
- *Implementation*: `git rm src/spiral_problem/check.py`.
- *Strengths*: 10-minute cleanup.
- *Weaknesses*: None.
- *Risks*: None — zero callers.
- *Guardrails*: Verify no imports reference `check.py`.

**Recommended**: Approach A — trivial deletion.

---

#### CLN-CC-03: Remove 9 Local `import traceback` in cascade_correlation.py

**Current Code**: `cascade_correlation.py:64,2270,2804,3775,3840` + other files — 9 local `import traceback` scattered throughout; line 64 has the top-level import commented out.
**Root Cause**: Developers added local imports during debugging; never cleaned up.

**Approach A — Uncomment Top-Level, Remove Local Imports**:
- *Implementation*: Uncomment `import traceback` at line 64. Remove all 9 local `import traceback` statements.
- *Strengths*: Clean imports; follows Python convention of top-level imports.
- *Weaknesses*: None.
- *Risks*: None — traceback is stdlib.
- *Guardrails*: Run tests after change.

**Recommended**: Approach A — 30-minute cleanup.

---

#### CLN-CC-04: Enable mypy Strict Mode

**Current Code**: `pyproject.toml` — mypy not in strict mode.
**Root Cause**: Strict mode was deferred during initial development.

**Approach A — Incremental Strict Mode**:
- *Implementation*: Enable strict mode with per-module overrides: `[mypy] strict = true` then `[mypy-module] ignore_errors = true` for modules not yet compliant. Fix one module at a time.
- *Strengths*: Catches type errors; incremental migration.
- *Weaknesses*: Large effort (M); many existing violations.
- *Risks*: May uncover real bugs during migration.
- *Guardrails*: Track compliance percentage; fix highest-impact modules first.

**Recommended**: Approach A because incremental migration is manageable.

---

#### CLN-CC-05: Legacy Spiral Code — Trivial Getter/Setter Methods, No @deprecated

**Current Code**: `src/spiral_problem/spiral_problem.py` — 53 methods, ~20 trivial getters/setters with no deprecation markers.
**Root Cause**: Legacy code with Java-style accessors, no Python property pattern.

**Approach A — Add @deprecated Markers**:
- *Implementation*: Mark unused getters/setters with `@deprecated("Use property directly")`. Remove after one release cycle.
- *Strengths*: Warns consumers; tracks deprecated API surface.
- *Weaknesses*: Effort to identify which methods are still called.
- *Risks*: Deprecation warnings may be noisy.
- *Guardrails*: Grep for all method usages across codebase before deprecating.

**Recommended**: Approach A as first step; follow with deletion of confirmed-unused methods.

---

#### CLN-CC-06: Remove "Roll" Concept in CandidateUnit

**Current Code**: `candidate_unit.py` — Roll concept in CandidateUnit.
**Root Cause**: Legacy concept no longer relevant to algorithm.

**Approach A — Deferred**: 🔵 Explicitly deferred per V5 document. Low priority; address when CandidateUnit is refactored.

---

#### CLN-CC-07: Candidate Factory Refactor

**Current Code**: Candidate creation scattered; should go through `_create_candidate_unit()`.
**Root Cause**: Organic code growth without factory pattern enforcement.

**Approach A — Deferred**: 🔵 Explicitly deferred per V5 document.

---

#### CLN-CC-08: Remove Commented-Out Code Blocks

**Current Code**: Multiple files contain commented-out code.
**Root Cause**: Code commented out during development, never removed.

**Approach A — Deferred**: 🔵 Explicitly deferred per V5 document.

---

#### CLN-CC-09: Line Length Reduction to 120 Characters

**Current Code**: Multiple files exceed 120 char lines.
**Root Cause**: Project convention is 512 chars; 120 is a stricter standard.

**Approach A — Deferred**: 🔵 Explicitly deferred. Note: Project convention is 512 chars per AGENTS.md.

---

#### CLN-CC-10: `utils.py:238` — Broken `check_object_pickleability` Uses `dill` Not in Deps

**Current Code**: `src/utils/utils.py:238` — uses `dill` library which is not in dependencies.
**Root Cause**: Function references `dill` but it's not declared as a dependency.

**Approach A — Add dill or Remove Function**:
- *Implementation*: Option 1: Add `dill` to optional dependencies. Option 2: Remove the function if unused.
- *Strengths*: Either approach resolves the broken import.
- *Weaknesses*: Adding deps for a utility function may be overkill.
- *Risks*: None.
- *Guardrails*: Grep for callers to determine if function is used.

**Recommended**: Check usage first — remove if unused, add `dill` if used.

---

#### CLN-CC-11: `snapshot_serializer.py` — Extend Optimizer Support (In-Code TODO)

**Current Code**: `snapshot_serializer.py:~756` — TODO for extended optimizer support.
**Root Cause**: Only a subset of optimizers are serialized; others are silently skipped.

**Approach A — Add Missing Optimizer Support**:
- *Implementation*: Extend serialization to cover all PyTorch optimizer types (Adam, AdamW, SGD, RMSprop). Use generic `optimizer.state_dict()` approach.
- *Strengths*: Complete snapshot coverage; enables optimizer persistence.
- *Weaknesses*: Must test each optimizer type.
- *Risks*: New optimizers may have non-serializable state.
- *Guardrails*: Add parametrized test for each supported optimizer.

**Recommended**: Approach A because incomplete serialization silently loses optimizer state.

---

#### CLN-CC-12: `.ipynb_checkpoints` Directories Committed to Repository

**Current Code**: `src/cascade_correlation/.ipynb_checkpoints/`, `src/candidate_unit/`, `src/` — checkpoint directories in repo.
**Root Cause**: `.gitignore` missing `.ipynb_checkpoints` entry.

**Approach A — Remove and Ignore**:
- *Implementation*: `git rm -r --cached */.ipynb_checkpoints/`. Add `.ipynb_checkpoints/` to `.gitignore`.
- *Strengths*: 10-minute cleanup; prevents future commits.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Verify removal with `git status`.

**Recommended**: Approach A — trivial cleanup.

---

#### CLN-CC-13: `sys.path.append` at Module Level in cascade_correlation.py

**Current Code**: `src/cascade_correlation/cascade_correlation.py:69` — `sys.path.append(...)`.
**Root Cause**: Legacy monorepo path manipulation.

**Approach A — Remove and Fix Imports**:
- *Implementation*: Remove `sys.path.append` line. Fix any imports that relied on it to use package-relative imports.
- *Strengths*: Clean imports; no runtime path mutation.
- *Weaknesses*: Must verify all affected imports.
- *Risks*: Import failures if dependencies aren't properly installed.
- *Guardrails*: Run tests after removal; fix any ImportError.

**Recommended**: Approach A because sys.path manipulation is fragile.

---

#### CLN-CC-14: Empty `# TODO :` Headers in 18+ Files

**Current Code**: Multiple file headers have empty `# TODO :` comments.
**Root Cause**: Boilerplate template included empty TODO sections.

**Approach A — Remove Empty TODOs**:
- *Implementation*: `grep -rl "# TODO :" src/ | xargs sed -i '/^# TODO :$/d'`.
- *Strengths*: Reduces noise; trivial.
- *Weaknesses*: None.
- *Risks*: Must not remove non-empty TODOs.
- *Guardrails*: Only remove lines matching exactly `# TODO :` (with nothing after).

**Recommended**: Approach A — trivial cleanup.

---

#### CLN-CC-15: `_object_attributes_to_table` Return Type Annotation Wrong

**Current Code**: `src/utils/utils.py:197` — annotated as `-> str` but returns `list` or `None`.
**Root Cause**: Type annotation not updated when function was modified.

**Approach A — Fix Annotation**:
- *Implementation*: Change return type to `-> Optional[list]` or the actual return type.
- *Strengths*: Correct type annotation; mypy compliance.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Run mypy on the file after fix.

**Recommended**: Approach A — one-line fix.

---

### Issue Remediations, Section 6 — juniper-canopy

#### CLN-CN-01: `theme-table` CSS Class Never Implemented

**Current Code**: No `.theme-table` in any CSS file.
**Root Cause**: CSS class referenced in templates but never defined.

**Approach A — Implement or Remove References**:
- *Implementation*: Either add `.theme-table` CSS rules or remove all HTML references to the class.
- *Strengths*: Resolves dead reference.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Grep for all `theme-table` references.

**Recommended**: Approach A — implement if styling is needed, remove if not.

---

#### CLN-CN-02: NPZ Validation Only in DemoMode, Not ServiceBackend

**Current Code**: `_validate_npz_arrays()` exists only in `demo_mode.py:767`.
**Root Cause**: Validation not extracted to shared utility.

**Approach A — Extract to Shared Module**:
- *Implementation*: Move `_validate_npz_arrays()` to a shared `validation.py` module. Call from both DemoMode and ServiceBackend.
- *Strengths*: Consistent validation; DRY.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add test for validation in service backend path.

**Recommended**: Approach A because inconsistent validation is a reliability gap.

---

#### CLN-CN-03: Performance Test Suite Minimal

**Current Code**: Only `test_button_responsiveness.py`.
**Root Cause**: Performance testing not prioritized.

**Approach A — Expand Test Suite**:
- *Implementation*: Add tests for: callback execution time, WebSocket message throughput, dashboard render time, memory usage during long sessions.
- *Strengths*: Catches performance regressions; establishes baselines.
- *Weaknesses*: Medium effort.
- *Risks*: Flaky tests if timing-dependent.
- *Guardrails*: Use relative thresholds (e.g., "no more than 2x baseline") not absolute times.

**Recommended**: Approach A because performance testing prevents silent regressions.

---

#### CLN-CN-04: JuniperData-Specific Error Handling Missing

**Current Code**: Only cascor-client errors caught; no data-client error classes.
**Root Cause**: Error handling only implemented for cascor-client.

**Approach A — Add Data-Client Error Handling**:
- *Implementation*: Import and catch `DataClientError` (or equivalent) in service adapter. Add appropriate error messages and fallback behavior.
- *Strengths*: Resilient to data service errors.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add test simulating data service errors.

**Recommended**: Approach A because unhandled data-client errors crash the dashboard.

---

#### CLN-CN-05: DashboardManager Extraction (3,232 → Component Classes)

**Current Code**: `src/frontend/dashboard_manager.py` — 3,232 lines.
**Root Cause**: God class accumulated all dashboard logic.
**Cross-References**: Related to BUG-CN-02.

**Approach A — Progressive Extraction**:
- *Implementation*: Same as BUG-CN-02 Approach A. Extract component classes incrementally.
- *Strengths*: Testable components; reduced cognitive load.
- *Weaknesses*: Large effort (L).
- *Risks*: Tightly coupled Dash callbacks resist decomposition.
- *Guardrails*: Maintain integration tests; one component at a time.

**Recommended**: Approach A — incremental extraction.

---

#### CLN-CN-06: Re-enable Remaining MyPy Disabled Codes

**Current Code**: 7 MyPy error codes currently suppressed.
**Root Cause**: Codes disabled during development to bypass type errors.

**Approach A — Fix Types and Re-enable**:
- *Implementation*: Fix underlying type errors for each suppressed code, then remove suppression. One code at a time.
- *Strengths*: Better type safety; catches bugs.
- *Weaknesses*: Must fix all violations per code.
- *Risks*: Some codes may be suppressed for valid reasons.
- *Guardrails*: Document any codes that must remain suppressed with justification.

**Recommended**: Approach A — incremental, one code at a time.

---

#### CLN-CN-07: Real Backend Path Test Coverage

**Current Code**: No tests exercise real CasCor paths; all use fakes/mocks.
**Root Cause**: Integration tests not written.

**Approach A — Add Integration Tests**:
- *Implementation*: Add tests with `requires_server` marker that exercise real CascorServiceAdapter with a running cascor instance.
- *Strengths*: Validates real integration; catches API contract issues.
- *Weaknesses*: Requires running server in CI.
- *Risks*: Flaky tests from network/server issues.
- *Guardrails*: Use Docker-based test fixtures; skip if server unavailable.

**Recommended**: Approach A because unit tests with fakes cannot catch integration issues.

---

#### CLN-CN-08: Convert Skipped Integration Tests (4 Files with `requires_server`)

**Current Code**: 4 test files with `requires_server` skip marker.
**Root Cause**: Tests written but never run in CI.

**Approach A — Add CI Integration Job**:
- *Implementation*: Add a CI job that starts cascor/data via Docker, runs `requires_server` tests, tears down.
- *Strengths*: Existing tests become valuable.
- *Weaknesses*: CI complexity.
- *Risks*: Docker-in-CI setup.
- *Guardrails*: Run as optional (non-blocking) CI step initially.

**Recommended**: Approach A because existing tests should be exercised.

---

#### CLN-CN-09: main.py Coverage Gap (84% vs 95% Target)

**Current Code**: `main.py` at 84% coverage.
**Root Cause**: Large file with many untested paths.

**Approach A — Targeted Test Addition**:
- *Implementation*: Identify uncovered lines via `coverage html`. Write tests for highest-impact uncovered paths (error handlers, edge cases).
- *Strengths*: Focused effort on coverage gaps.
- *Weaknesses*: 95% target may be aspirational for a 2,543-line file.
- *Risks*: Some paths may be difficult to test without refactoring.
- *Guardrails*: Set intermediate target (90%) before pushing to 95%.

**Recommended**: Approach A with intermediate target of 90%.

---

#### CLN-CN-10: `main.py` Is 2,543 Lines — Second God File

**Current Code**: `src/main.py` — 65 functions/methods; 30+ route handlers.
**Root Cause**: All route handlers in a single file.

**Approach A — Extract Route Modules**:
- *Implementation*: Extract routes into modules: `routes/training.py`, `routes/datasets.py`, `routes/websocket.py`, `routes/health.py`. Import and mount in `main.py`.
- *Strengths*: Smaller files; organized by domain; testable independently.
- *Weaknesses*: Large effort (L).
- *Risks*: Dash callback registration may complicate extraction.
- *Guardrails*: Extract one route group at a time; maintain full test suite.

**Recommended**: Approach A — incremental extraction by route group.

---

#### CLN-CN-11: `metrics_panel.py` Is 1,790 Lines — Third God File

**Current Code**: 18 `@app.callback` decorators in single file.
**Root Cause**: All metric panel callbacks in one file.

**Approach A — Extract by Metric Type**:
- *Implementation*: Split into `training_metrics.py`, `candidate_metrics.py`, `validation_metrics.py`.
- *Strengths*: Organized by domain; manageable file sizes.
- *Weaknesses*: Large effort (L); callback cross-dependencies.
- *Risks*: Dash callback registration order may matter.
- *Guardrails*: Extract one metric group at a time.

**Recommended**: Approach A — incremental extraction.

---

#### CLN-CN-12: `network_visualizer.py:1512` — Active TODO Indicating Logging Error Bug

**Current Code**: `# TODO: this is throwing a logging error` on `_create_new_node_highlight_traces`.
**Root Cause**: Known logging error in visualization code not fixed.

**Approach A — Fix Logging Error**:
- *Implementation*: Investigate and fix the logging error. Likely a string format issue or incorrect log level.
- *Strengths*: Removes known bug; clean logs.
- *Weaknesses*: Must investigate root cause.
- *Risks*: None.
- *Guardrails*: Add test that triggers the code path and verifies no logging error.

**Recommended**: Approach A because active TODOs indicating bugs should be fixed.

---

#### CLN-CN-13: Deprecated `_generate_spiral_dataset_local()` Still Called

**Current Code**: `demo_mode.py:938` — `@deprecated` but called as fallback at L554 and L1667.
**Root Cause**: Deprecated function kept as fallback when JuniperData service is unavailable.

**Approach A — Remove After Ensuring JuniperData Reliability**:
- *Implementation*: Remove the deprecated function and its fallback calls once JuniperData service reliability is sufficient. Until then, keep but rename to `_generate_spiral_dataset_fallback()`.
- *Strengths*: Clean code once JuniperData is reliable.
- *Weaknesses*: Can't remove until service dependency is stable.
- *Risks*: Removing fallback too early breaks demo mode when data service is down.
- *Guardrails*: Track JuniperData availability metrics before removal.

**Recommended**: Approach A — keep as fallback for now; remove when data service is production-stable.

---

#### CLN-CN-14: `np.random.seed(42)` Sets Global Numpy Seed

**Current Code**: `demo_mode.py:960` — mutates global RNG state.
**Root Cause**: Global seed set for reproducibility but affects all concurrent numpy users.

**Approach A — Use `np.random.default_rng(42)` Local Generator**:
- *Implementation*: Replace `np.random.seed(42)` with `rng = np.random.default_rng(42)`. Use `rng` for all random operations instead of module-level `np.random`.
- *Strengths*: Isolated RNG; thread-safe; reproducible.
- *Weaknesses*: Must update all `np.random.*` calls to `rng.*`.
- *Risks*: Slight API differences between module-level and Generator methods.
- *Guardrails*: Test reproducibility with same seed.

**Recommended**: Approach A because global seed is a numpy anti-pattern.

---

### Issue Remediations, Section 6 — juniper-data

#### CLN-JD-01: `python-dotenv` Hard Dependency for Optional ARC-AGI Feature

**Current Code**: `pyproject.toml` requires `python-dotenv`; only used in `__init__.py:get_arc_agi_env()`.
**Root Cause**: Hard dependency for a feature that's rarely used.

**Approach A — Move to Optional Extra**:
- *Implementation*: Move `python-dotenv` to `[project.optional-dependencies] arc-agi = ["python-dotenv"]`. Add conditional import with graceful fallback.
- *Strengths*: Smaller base install; explicit feature dependency.
- *Weaknesses*: Users must install extra for ARC-AGI.
- *Risks*: Breaking change if users rely on dotenv being available.
- *Guardrails*: Add helpful error message when dotenv not installed but ARC-AGI requested.

**Recommended**: Approach A because hard dependencies for optional features bloat installs.

---

#### CLN-JD-02: `FakeDataClient.close()` Destroys Data

**Current Code**: `testing/fake_client.py:762-766` — `close()` clears `_datasets`.
**Root Cause**: Fake treats `close()` as "destroy all state" instead of "release resources".

**Approach A — Don't Clear Data on Close**:
- *Implementation*: Remove `self._datasets.clear()` from `close()`. Only clear network resources (if any).
- *Strengths*: Matches real client behavior; tests can verify state after close.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add separate `reset()` method for tests that need clean state.

**Recommended**: Approach A because close() should release resources, not destroy data.

---

#### CLN-JD-03: Module-Level `create_app()` at `app.py:142` — Import-Time Side Effects

**Current Code**: `app.py:142` — `create_app()` called at import time.
**Root Cause**: App creation happens during import, reading env vars and creating middleware.

**Approach A — Lazy Initialization**:
- *Implementation*: Move `create_app()` call into a `get_app()` function or guard with `if __name__ == "__main__":`. Use `functools.lru_cache` for singleton behavior.
- *Strengths*: No import-time side effects; testable configuration.
- *Weaknesses*: Must update ASGI server config (uvicorn import path).
- *Risks*: ASGI server must call `get_app()` instead of importing `app`.
- *Guardrails*: Use uvicorn factory pattern: `uvicorn.run("module:get_app", factory=True)`.

**Recommended**: Approach A because import-time side effects break testing and configuration.

---

### Issue Remediations, Section 12

#### HSK-01: 3 Broken Symlinks in canopy `notes/development/`

**Current Code**: Symlinks pointing to deleted juniper-ml files.
**Root Cause**: Source files removed; symlinks not cleaned up.

**Approach A — Remove Broken Symlinks**:
- *Implementation*: `find notes/development/ -xtype l -delete` in canopy repo.
- *Strengths*: 5-minute cleanup.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Verify symlinks are indeed broken before deletion.

**Recommended**: Approach A — trivial cleanup.

---

#### HSK-02: `src/remote_client/` Directory Still Exists

**Cross-References**: HSK-02 = CLN-CC-01
**Approach A**: See CLN-CC-01 remediation.

---

#### HSK-03: `src/spiral_problem/check.py` — 600-Line Stale Duplicate

**Cross-References**: HSK-03 = CLN-CC-02
**Approach A**: See CLN-CC-02 remediation.

---

#### HSK-04: 32 Test Files with Hardcoded `sys.path.append`

**Cross-References**: Related to BUG-CC-06
**Approach A**: See BUG-CC-06 remediation.

---

#### HSK-05: cascor-client AGENTS.md Header Version 0.3.0 vs Package 0.4.0

**Current Code**: AGENTS.md shows version 0.3.0.
**Root Cause**: Document version not updated during release.

**Approach A — Update Version**:
- *Implementation*: Change version in AGENTS.md header to match `pyproject.toml`.
- *Strengths*: 1-minute fix.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add CI check comparing AGENTS.md version with pyproject.toml.

**Recommended**: Approach A — trivial update.

---

#### HSK-06: juniper-data AGENTS.md Header Version 0.5.0 vs Package 0.6.0

**Approach A**: Same as HSK-05 — update version header.
**Recommended**: Approach A.

---

#### HSK-07: cascor-client File Headers Show Versions 0.1.0–0.3.0

**Approach A**: Update all file headers to current version, or remove file-level version headers (see BUG-CC-04 approach).
**Recommended**: Remove file-level versions in favor of single source in pyproject.toml.

---

#### HSK-08: data-client `tests/conftest.py` Version Header Says 0.3.1

**Approach A**: Same as HSK-07 — update or remove file-level version.
**Recommended**: Same approach.

---

#### HSK-09: Dead Code `_STATE_TO_FSM` and `_STATE_TO_PHASE` in cascor-client

**Current Code**: Class attributes never referenced.
**Root Cause**: Mapping tables defined but never used.

**Approach A — Delete Dead Code**:
- *Implementation*: Remove `_STATE_TO_FSM` and `_STATE_TO_PHASE` attributes.
- *Strengths*: Cleaner code.
- *Weaknesses*: None.
- *Risks*: None — zero references.
- *Guardrails*: Grep for any references before deletion.

**Recommended**: Approach A — trivial dead code removal.

---

#### HSK-10: `scripts/test.bash` Outdated/Non-Functional

**Current Code**: References removed `nohup.out` file.
**Root Cause**: Script not updated when `nohup.out` was removed.

**Approach A — Update or Delete Script**:
- *Implementation*: Update script to use current test infrastructure, or delete if superseded by `pytest` commands.
- *Strengths*: Working or removed script.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Check if script is referenced anywhere.

**Recommended**: Approach A — update if used, delete if not.

---

#### HSK-11: `wake_the_claude.bash` `DEBUG="${TRUE}"` Hardcoded ON

**Current Code**: `scripts/wake_the_claude.bash` — `DEBUG="${TRUE}"` hardcoded.
**Root Cause**: Debug mode left on during development.
**Cross-References**: Related to HSK-20.

**Approach A — Use Environment Variable Default**:
- *Implementation*: Change `DEBUG="${TRUE}"` to `DEBUG="${DEBUG:-false}"`. Respects env var; defaults to off.
- *Strengths*: Configurable; quiet by default.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Document `DEBUG=true` usage in script comments.

**Recommended**: Approach A — one-line fix.

---

#### HSK-12: `NOHUP_STATUS=$?` Captures Fork Status (Always 0)

**Current Code**: Dead error check capturing nohup fork status.
**Root Cause**: `$?` after `nohup &` captures the fork status (always 0), not the command result.

**Approach A — Remove Dead Check**:
- *Implementation*: Remove the `NOHUP_STATUS` check since it's always 0.
- *Strengths*: Removes misleading code.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A.

---

#### HSK-13: 169 Hardcoded ThemeColors Remain in canopy

**Current Code**: 169 hardcoded theme color values instead of using ThemeColors class.
**Root Cause**: MED-026 ThemeColors rollout was deferred.

**Approach A — Incremental ThemeColors Migration**:
- *Implementation*: Replace hardcoded colors with `ThemeColors.*` constants in batches of 10-20 per PR.
- *Strengths*: Consistent theming; centralized color management.
- *Weaknesses*: Large effort across 169 locations.
- *Risks*: Visual regressions if colors don't match.
- *Guardrails*: Visual comparison screenshots before/after each batch.

**Recommended**: Approach A — incremental migration by component.

---

#### HSK-14: `resume_session.bash` Contains Hardcoded Session UUID

**Current Code**: One-time-use script committed with hardcoded session UUID.
**Root Cause**: Script was used once and committed without parameterization.

**Approach A — Parameterize or Delete**:
- *Implementation*: Either make the UUID a required parameter (`$1`) or delete the script.
- *Strengths*: Reusable or removed.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A — parameterize for reuse.

---

#### HSK-15: `util/global_text_replace.bash` Is a No-Op

**Current Code**: Search == replace are identical strings; also has misspelled `KIBAB`.
**Root Cause**: Script was used once with specific values; committed without cleanup.

**Approach A — Fix or Delete**:
- *Implementation*: Parameterize search/replace as `$1` and `$2`, or delete the script.
- *Strengths*: Functional utility or removed noise.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Fix `KIBAB` → `KEBAB` if keeping.

**Recommended**: Approach A — parameterize for reuse.

---

#### HSK-16: `util/kill_all_pythons.bash` Uses `sudo kill -9` on ALL Python Processes

**Current Code**: Indiscriminate kill of all Python processes.
**Root Cause**: Emergency utility not scoped to Juniper processes.

**Approach A — Scope to Juniper Processes**:
- *Implementation*: Filter by process name or CWD: `pgrep -f "juniper" | xargs kill`. Add confirmation prompt. Remove `sudo` (user processes only).
- *Strengths*: Safe; targeted; no collateral damage.
- *Weaknesses*: May miss Juniper processes with non-standard names.
- *Risks*: None (safer than current).
- *Guardrails*: Add `--dry-run` mode; list processes before killing.

**Recommended**: Approach A because killing ALL Python processes is dangerous.

---

#### HSK-17: `util/worktree_new.bash` Hardcodes Branch/Repo Names

**Current Code**: Hardcoded branch names and conda env; stray `}` in error message.
**Root Cause**: Script written for one-time use; not parameterized.

**Approach A — Parameterize**:
- *Implementation*: Accept branch, repo, and conda env as parameters. Fix stray `}`.
- *Strengths*: Reusable across repos.
- *Weaknesses*: Must update callers.
- *Risks*: None.
- *Guardrails*: Add `--help` usage output.

**Recommended**: Approach A.

---

#### HSK-18: `util/worktree_close.bash` Hardcodes Default Identifier

**Current Code**: Not reusable without args due to hardcoded defaults.
**Root Cause**: Same as HSK-17 — one-time script not parameterized.

**Approach A — Require Parameters**:
- *Implementation*: Make identifier a required parameter. Error if not provided.
- *Strengths*: Explicit; reusable.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Add usage help.

**Recommended**: Approach A.

---

#### HSK-19: Stale Files in Repo Root

**Current Code**: `bla`, `juniper_cascor.log`, `juniper-project-pids.txt`, `JuniperProject.pid`, `.mcp.json.swp`.
**Root Cause**: Development artifacts committed or generated but not gitignored.

**Approach A — Delete and Gitignore**:
- *Implementation*: `git rm` the stale files. Add patterns to `.gitignore`: `*.log`, `*.pid`, `*.swp`, `bla`.
- *Strengths*: Clean repo root; prevents future commits.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Verify none of the files are used by any script.

**Recommended**: Approach A — trivial cleanup.

---

#### HSK-20: `claude_interactive.bash:17` `DEBUG="${TRUE}"` Hardcoded

**Current Code**: Forces `--dangerously-skip-permissions` when DEBUG is on.
**Root Cause**: Debug mode hardcoded on.
**Cross-References**: Related to HSK-11.

**Approach A — Same as HSK-11**:
- *Implementation*: Change to `DEBUG="${DEBUG:-false}"`.
- *Strengths*: Same fix pattern.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A.

---

#### HSK-21: `wake_the_claude.bash:53` Stale TODO Comment

**Current Code**: TODO says `debug_log` should write to stderr — but it already does.
**Root Cause**: TODO not removed after implementation.

**Approach A — Remove TODO**:
- *Implementation*: Delete the stale TODO comment.
- *Strengths*: Removes noise.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None.

**Recommended**: Approach A — 30-second fix.

---

#### HSK-22: `wake_the_claude.bash:547` TODO — Model Parameter Never Validated

**Current Code**: `--model` parameter accepted but never validated against valid model list.
**Root Cause**: Validation TODO never implemented.

**Approach A — Add Validation**:
- *Implementation*: Validate `--model` against known Claude model names. Error on invalid model.
- *Strengths*: Catches typos; clearer errors.
- *Weaknesses*: Must maintain valid model list.
- *Risks*: New models added before list updated.
- *Guardrails*: Use warning instead of error to avoid blocking new models.

**Recommended**: Approach A with warning (not error) for unknown models.

---

#### HSK-23: `scripts/juniper-all-ctl:38` Cascor Port Defaults to 8200 (Container) vs Host 8201

**Current Code**: Port defaults to 8200 but Docker maps cascor to host port 8201.
**Root Cause**: Script uses container port instead of host port.

**Approach A — Default to 8201**:
- *Implementation*: Change default port to 8201 (host port). Add comment explaining container vs host port.
- *Strengths*: Works correctly for local development.
- *Weaknesses*: Wrong inside container (but script runs on host).
- *Risks*: None.
- *Guardrails*: Make port configurable via env var.

**Recommended**: Approach A.

---

#### HSK-24: Dead Constants in cascor-client

**Current Code**: `ERROR_PRONE_INITIAL_HIDDEN_UNITS` / `ERROR_PRONE_INITIAL_EPOCH` never used.
**Root Cause**: Constants defined but never referenced.

**Approach A — Delete**:
- *Implementation*: Remove both constants.
- *Strengths*: Cleaner code.
- *Weaknesses*: None.
- *Risks*: None — zero references.
- *Guardrails*: Grep before deletion.

**Recommended**: Approach A.

---

### Issue Remediations, Section 16

#### PERF-CN-01: 33 of 50 Dash Callbacks Missing `prevent_initial_call=True`

**Current Code**: `metrics_panel.py` (14), `candidate_metrics_panel.py` (7), 12 others — 33 unnecessary initial callback executions.
**Root Cause**: Default `prevent_initial_call=False` causes every callback to fire on page load.

**Approach A — Add `prevent_initial_call=True`**:
- *Implementation*: Add `prevent_initial_call=True` to all 33 callback decorators where initial call is not needed.
- *Strengths*: Faster page load; reduced initial CPU; simple decorator change.
- *Weaknesses*: Must verify each callback doesn't need initial execution.
- *Risks*: Some callbacks may depend on initial call for setup.
- *Guardrails*: Test each callback group after change; revert any that break.

**Recommended**: Approach A because 33 unnecessary callback fires is measurable performance waste.

---

#### PERF-CN-02: f-string Logging in Hot Paths (71 Occurrences)

**Current Code**: `demo_mode.py` (20), `main.py` (51) — string interpolation evaluated even when log level suppresses.
**Root Cause**: Using f-strings instead of lazy `%s` formatting in log calls.

**Approach A — Use Lazy Formatting**:
- *Implementation*: Change `logger.debug(f"Value: {val}")` to `logger.debug("Value: %s", val)`.
- *Strengths*: No interpolation when log level is above DEBUG; standard practice.
- *Weaknesses*: 71 locations to change.
- *Risks*: None.
- *Guardrails*: Add flake8 plugin to catch future f-string logging.

**Recommended**: Approach A for hot paths; lower priority for cold paths.

---

#### PERF-CC-01: Blocking `torch.save`/`torch.load` in Async-Adjacent Code Paths

**Current Code**: `src/api/lifecycle/manager.py:870,894` — synchronous HDF5 I/O from async REST handlers.
**Root Cause**: Snapshot operations block the event loop during I/O.

**Approach A — asyncio.to_thread Wrapper**:
- *Implementation*: Wrap `torch.save()` and `torch.load()` calls in `await asyncio.to_thread(...)`.
- *Strengths*: Non-blocking; minimal code change.
- *Weaknesses*: Thread pool limits concurrent snapshot operations.
- *Risks*: Thread-safety of torch save/load must be verified.
- *Guardrails*: Add timeout for snapshot operations.

**Recommended**: Approach A because blocking I/O in async handlers impacts all concurrent requests.

---

#### PERF-CC-02: `replay_since` Scans Entire Replay Buffer O(n)

**Current Code**: `src/api/websocket/manager.py:248` — linear scan of 1024-entry deque.
**Root Cause**: No index on replay buffer by sequence number.

**Approach A — Binary Search**:
- *Implementation*: Since sequence numbers are monotonically increasing, use `bisect.bisect_left` on the deque.
- *Strengths*: O(log n) instead of O(n); simple.
- *Weaknesses*: `bisect` doesn't directly support deque (convert to list or use custom key).
- *Risks*: Minimal — 1024 entries is small even for O(n).
- *Guardrails*: Benchmark before/after to verify improvement.

**Recommended**: Approach A as a nice-to-have; low priority since N ≤ 1024.

---

#### PERF-CC-03: `_broadcast_training_state` Uses `hasattr` Check

**Current Code**: `src/api/lifecycle/manager.py:153` — `hasattr(self, "_last_state_broadcast_time")` on every call.
**Root Cause**: Attribute not initialized in `__init__`; `hasattr` used as workaround.

**Approach A — Initialize in `__init__`**:
- *Implementation*: Add `self._last_state_broadcast_time = 0.0` to `__init__`. Remove `hasattr` check.
- *Strengths*: Faster; cleaner; proper initialization.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Covered by CONC-02 fix.

**Recommended**: Approach A — trivial fix, covered by CONC-02 remediation.

---

#### PERF-JD-01: Readiness Probe Does Filesystem Glob on Every Call

**Current Code**: `api/routes/health.py:57` — `len(list(storage_path.glob("*.npz")))` per probe.
**Root Cause**: Counting all datasets on every health check; O(n) per probe.

**Approach A — Cache Dataset Count**:
- *Implementation*: Maintain a cached dataset count updated on save/delete. Health probe reads cached value.
- *Strengths*: O(1) per probe; accurate within save/delete cycle.
- *Weaknesses*: Cache may be stale if files are modified outside the application.
- *Risks*: Minimal for health probes.
- *Guardrails*: Refresh cache periodically (every 60s) as fallback.

**Approach B — Simplified Readiness Check**:
- *Implementation*: Replace glob with a simpler check: `storage_path.exists() and storage_path.is_dir()`.
- *Strengths*: O(1); simpler; sufficient for readiness.
- *Weaknesses*: Doesn't verify data accessibility.
- *Risks*: Probe may report ready when storage is corrupted.
- *Guardrails*: Keep liveness separate from readiness.

**Recommended**: Approach B because readiness probes should be fast and simple.

---

#### PERF-JD-02: High-Cardinality Prometheus Labels

**Current Code**: `api/observability.py:98` — `endpoint = request.url.path`.
**Root Cause**: Full URL path used as label, including dataset IDs.
**Cross-References**: PERF-JD-02 = BUG-JD-09

**Approach A**: See BUG-JD-09 remediation (use route template).
**Recommended**: See BUG-JD-09.

---

### Issue Remediations, Section 20

#### CFG-01: `torch` Imported but Missing from canopy Dependencies

**Current Code**: `demo_backend.py:45` imports torch; not in canopy's `pyproject.toml`.
**Root Cause**: torch imported unconditionally but never declared as dependency.

**Approach A — Add torch to Dependencies**:
- *Implementation*: Add `torch>=2.0` to canopy's `pyproject.toml` dependencies or optional extras `[demo]`.
- *Strengths*: Explicit dependency; install doesn't fail at runtime.
- *Weaknesses*: Large dependency (~2GB).
- *Risks*: May conflict with other PyTorch versions in environment.
- *Guardrails*: Use optional extra `[demo]` if torch is only needed for demo mode.

**Recommended**: Approach A with `[demo]` optional extra to avoid bloating base install.

---

#### CFG-02: `sentry-sdk` in Core Dependencies but Only Used Optionally

**Current Code**: `sentry-sdk` in cascor core deps but only when `SENTRY_SDK_DSN` is set.
**Root Cause**: SDK always installed even when Sentry is not configured.

**Approach A — Move to Optional Extra**:
- *Implementation*: Move to `[project.optional-dependencies] observability = ["sentry-sdk"]`. Conditional import with graceful fallback.
- *Strengths*: Smaller base install; explicit opt-in.
- *Weaknesses*: Users must install extra for Sentry.
- *Risks*: Existing deployments with Sentry need to update install command.
- *Guardrails*: Clear error message when DSN is set but SDK not installed.

**Recommended**: Approach A because optional features should use optional dependencies.

---

#### CFG-03: `SENTRY_SDK_DSN` vs `JUNIPER_CASCOR_SENTRY_DSN` — Dual Env Vars

**Current Code**: `main.py:58` reads `SENTRY_SDK_DSN`; `settings.py:189` reads `JUNIPER_CASCOR_SENTRY_DSN`.
**Root Cause**: Two different code paths independently added Sentry support with different env var names.

**Approach A — Consolidate to Settings**:
- *Implementation*: Remove raw `os.getenv("SENTRY_SDK_DSN")` from `main.py`. Use only `settings.sentry_dsn` which reads `JUNIPER_CASCOR_SENTRY_DSN`. Add alias for backward compat.
- *Strengths*: Single source of truth; validated via Settings.
- *Weaknesses*: Breaking change for deployments using `SENTRY_SDK_DSN`.
- *Risks*: Must update deployment configs.
- *Guardrails*: Settings validator reads both env vars, preferring `JUNIPER_CASCOR_SENTRY_DSN`.

**Recommended**: Approach A because dual env vars is confusing and error-prone.

---

#### CFG-04: `JUNIPER_DATA_URL` Read via Raw `os.getenv`, Bypasses Settings

**Current Code**: `app.py:121,185,253`, `health.py:56` — raw `os.getenv()` calls bypass Settings validation.
**Root Cause**: URL was added before Settings class was comprehensive.

**Approach A — Move to Settings Class**:
- *Implementation*: Add `juniper_data_url: Optional[str] = None` to Settings. Replace all `os.getenv("JUNIPER_DATA_URL")` with `settings.juniper_data_url`.
- *Strengths*: Validated; documented; visible in Settings dump.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Use `AliasChoices` for both env var names if needed.

**Recommended**: Approach A because all config should go through Settings.

---

#### CFG-05: `CASCOR_LOG_LEVEL` vs `JUNIPER_CASCOR_LOG_LEVEL` — Both Needed

**Current Code**: `constants.py:580` reads `CASCOR_LOG_LEVEL`; `settings.py:116` reads `JUNIPER_CASCOR_LOG_LEVEL`.
**Root Cause**: Legacy env var name not migrated to ecosystem prefix convention.

**Approach A — Consolidate with Alias**:
- *Implementation*: Use `JUNIPER_CASCOR_LOG_LEVEL` as primary. Add `CASCOR_LOG_LEVEL` as deprecated alias via `AliasChoices` in Settings. Log deprecation warning when old name is used.
- *Strengths*: Backward compatible; ecosystem-consistent.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Remove deprecated alias after two release cycles.

**Recommended**: Approach A.

---

#### CFG-06: `CASCOR_*` Env Prefix Inconsistent with `JUNIPER_*` Convention

**Current Code**: `cascor-worker/constants.py:126-138` — 13 env vars use bare `CASCOR_*`.
**Root Cause**: Worker predates the ecosystem `JUNIPER_*` prefix convention.

**Approach A — Add `JUNIPER_` Prefix with Aliases**:
- *Implementation*: Support both `JUNIPER_CASCOR_WORKER_*` and `CASCOR_*` via `AliasChoices`. Deprecate old prefix.
- *Strengths*: Ecosystem-consistent; backward compatible.
- *Weaknesses*: 13 env vars to alias.
- *Risks*: Must update deployment configs eventually.
- *Guardrails*: Deprecation warnings on old prefix usage.

**Recommended**: Approach A.

---

#### CFG-07: Port 8200 vs 8201 Confusion

**Current Code**: Cascor binds 8200; Docker maps to host 8201; clients default to 8200.
**Root Cause**: Docker port mapping creates confusion between container and host ports.

**Approach A — Document and Standardize Defaults**:
- *Implementation*: Document the port mapping clearly in AGENTS.md and client READMEs. Client defaults to 8200 (correct for direct connections); add note about Docker mapping.
- *Strengths*: Clarifies confusion; no breaking changes.
- *Weaknesses*: Port confusion persists for new developers.
- *Risks*: None.
- *Guardrails*: Consider changing Docker host port to 8200 for consistency.

**Recommended**: Approach A because changing ports has deployment impact.

---

#### CFG-08: Rate Limiting Defaults Differ Across Services

**Current Code**: Data has rate limiting enabled; cascor/canopy disabled by default.
**Root Cause**: Each service independently configured rate limiting defaults.

**Approach A — Document Default Differences**:
- *Implementation*: Document rate limiting defaults in each service's AGENTS.md and in deployment guide. Note that production should enable rate limiting on all services.
- *Strengths*: Clear documentation; no behavioral changes.
- *Weaknesses*: Doesn't fix the inconsistency.
- *Risks*: None.
- *Guardrails*: Add rate limit config to deployment templates.

**Recommended**: Approach A because different defaults may be intentional per-service.

---

#### CFG-09: `audit_log_path` Defaults to `/var/log/` — Requires Root

**Current Code**: `settings.py:172` — `audit_log_enabled: True` with `/var/log/canopy/audit.log` default.
**Root Cause**: Default path requires root permissions; crashes non-root deployments.

**Approach A — User-Space Default**:
- *Implementation*: Change default to `~/.local/share/canopy/audit.log` or `./logs/audit.log`. Create directory if needed.
- *Strengths*: Works without root; follows XDG convention.
- *Weaknesses*: Different path than production systems expect.
- *Risks*: None.
- *Guardrails*: Document production path in deployment guide.

**Approach B — Make Audit Log Optional**:
- *Implementation*: Change `audit_log_enabled: bool = False`. Require explicit opt-in.
- *Strengths*: No path issues by default.
- *Weaknesses*: Audit logging off by default.
- *Risks*: Production may miss enabling audit log.
- *Guardrails*: Log warning at startup if audit logging disabled.

**Recommended**: Approach A because audit logging should work out-of-the-box.

---

#### CFG-12: `setuptools>=82.0` vs `>=61.0` Elsewhere

**Current Code**: Worker requires `setuptools>=82.0`; all others use `>=61.0`.
**Root Cause**: Unnecessarily restrictive constraint.

**Approach A — Align to `>=61.0`**:
- *Implementation*: Change worker's `setuptools>=82.0` to `>=61.0` (or whatever is actually required).
- *Strengths*: Consistent; reduces install friction.
- *Weaknesses*: None if 61.0 is sufficient.
- *Risks*: Must verify no 82.0-specific features are used.
- *Guardrails*: Test build with setuptools 61.0.

**Recommended**: Approach A — trivial version constraint fix.

---

#### CFG-13: `python-dotenv` in canopy Core Deps but Never Imported

**Current Code**: `python-dotenv` in canopy deps; no `import dotenv` in `src/`.
**Root Cause**: Dependency added speculatively or pydantic-settings handles `.env` natively.

**Approach A — Remove from Dependencies**:
- *Implementation*: Remove `python-dotenv` from canopy's `pyproject.toml`.
- *Strengths*: Smaller dependency set; removes unused package.
- *Weaknesses*: Must verify pydantic-settings doesn't need it (it doesn't — uses its own `.env` reader).
- *Risks*: None.
- *Guardrails*: Test settings loading after removal.

**Recommended**: Approach A because unused dependencies are bloat.

---

#### CFG-14: `juniper-cascor-client>=0.1.0` Allows Outdated Incompatible Versions

**Current Code**: Canopy allows cascor-client 0.1.0+ (current is 0.4.0).
**Root Cause**: Version constraint not tightened as API evolved.

**Approach A — Tighten Constraint**:
- *Implementation*: Change to `juniper-cascor-client>=0.3.0` (minimum compatible version per juniper-ml).
- *Strengths*: Prevents installation of incompatible versions.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Align with juniper-ml's constraint.

**Recommended**: Approach A — one-line fix.

---

#### CFG-16: `CASCOR_DEMO_MODE` Read Directly, Bypasses Settings

**Current Code**: `backend/__init__.py:66` reads `CASCOR_DEMO_MODE` via raw `os.getenv`.
**Root Cause**: Config bypass for demo mode detection.

**Approach A — Route Through Settings**:
- *Implementation*: Read from `Settings.demo_mode` instead of raw `os.getenv`. Settings already has demo mode detection.
- *Strengths*: Consistent configuration access; validated.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Verify Settings includes demo mode detection.

**Recommended**: Approach A because all config should go through Settings.

---

*End of Agent D partial — 15 cascor cleanup + 14 canopy cleanup + 3 data cleanup + 24 housekeeping + 7 performance + 13 config = 76 items covered*
