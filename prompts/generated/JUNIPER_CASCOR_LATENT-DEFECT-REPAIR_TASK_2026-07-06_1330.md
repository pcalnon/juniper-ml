# Task — Repair five verified latent defects in juniper-cascor: dead snapshot restore, dead snapshot listing, dead None guard, suite-wide logging-init bypass, and a merge-clobbered bind-guard helper

## Role

You are a senior engineer executing the task above end-to-end on the named repo(s), with the discipline to make the smallest correct change, verify it, and land it as a reviewable PR.

## Resources

**Target repo**: `/home/pcalnon/Development/python/Juniper/juniper-cascor` (pcalnon/juniper-cascor). Grounding bundle provenance: HEAD `4c9b4c28829e4c3ae107f2b9be142eb542ac01fc` on branch `cursor/missing-test-coverage-8d4a` (dirty: one untracked file `src/api/JUNIPER_2026-07-05_CASCOR.md`). Defects 1–4 were independently verified on `origin/main` @ `0a44938` (line anchors below match origin/main AND the current checkout); defect 5 exists ONLY on the `cursor/missing-test-coverage-8d4a` branch (open PR juniper-cascor#380).

**Defect anchors** (re-confirm each in-task before editing; stop and report on any mismatch):

1. **`restore_snapshot` can never succeed** — `src/cascade_correlation/cascade_correlation.py:4723-4724`:
    - `restore_snapshot` is a `@classmethod`; line `4756` executes `cls.__dict__.update(loaded_network.__dict__)`.
    - A class's `__dict__` is a read-only `mappingproxy` with no `.update` attribute, so every load-then-restore raises `AttributeError`, lands in the `except` at `4759-4764`, and returns `False`.
    - The success path (`4757-4758`) is unreachable; snapshot restore is dead code.
    - `cls._load_from_hdf5(...)` (called at `4746-4750`) does return a usable loaded network before the broken copy step.
    - Existing tests cover ONLY the failure paths: `src/tests/unit/test_cascade_correlation_coverage_deep.py:1294-1370` and `src/tests/unit/test_cascade_correlation_coverage_90.py:268-290`; no test asserts a successful restore.
2. **`list_hdf5_snapshots` always returns `[]`**:
    - `src/cascade_correlation/cascade_correlation.py:4998` defines `list_hdf5_snapshots`; line `5014` calls `HDF5Utils.list_hdf5_files(directory)`. `HDF5Utils` (defined at `src/snapshots/snapshot_utils.py:25`) has NO `list_hdf5_files` method anywhere in the codebase — the nearest existing capability is `HDF5Utils.list_networks_in_directory(directory)` at `src/snapshots/snapshot_utils.py:66`.
    - Every existing-directory call therefore raises `AttributeError` and falls through the `except` at `5017` to `return []`.
    - The success path (`5015-5016`) is unreachable.
3. **Dead `None` guard in `calculate_accuracy`**:
    - `src/cascade_correlation/cascade_correlation.py:5375-5376` default `x`/`y` via the tuple-index idiom (`x = (x, torch.empty(0, self.input_size))[x is None]`), so the `if x is None or y is None:` guard at `5380` (body `5381-5384`) can never fire — it is dead defensive code that silently duplicates the defaulting above it.
4. **`_init_logging_system` bypassed suite-wide**:
    - `src/cascade_correlation/cascade_correlation.py:630-658` (`_init_logging_system`) is monkey-patched away for the entire unit run by the autouse session fixture `_cache_logging_system` (`src/tests/conftest.py:829`), which installs `_fast_init_logging_system` (`src/tests/conftest.py:785`) at `conftest.py:847-848` and restores the original at `conftest.py:887`.
    - The real method body is never exercised by the CI unit subset, so regressions in it are invisible.
5. **`_settings_with_uvicorn_cli_bind` undefined (branch-scoped)**:
    - on branch `cursor/missing-test-coverage-8d4a` (PR #380), `src/api/app.py:518` calls `_settings_with_uvicorn_cli_bind(get_settings())` but the function is not defined anywhere on that branch: flake8 reports `src/api/app.py:518:20: F821 undefined name '_settings_with_uvicorn_cli_bind'`, and `src/tests/unit/api/test_bind_guard.py:17` imports it (and calls it at `:106` as `_settings_with_uvicorn_cli_bind(Settings(), argv)`), so API test collection fails.
    - Root cause: merge commit `4c9b4c2` (parents `00dd05b` + `20db489`) dropped the block that `origin/main` still carries — `import sys`, `_cli_option_value` (`origin/main` `src/api/app.py:85`), and `_settings_with_uvicorn_cli_bind` (`origin/main` `src/api/app.py:96`), part of the SEC-F22/D2 bind-guard shipped in juniper-cascor#372/#377/#379.
    - The canonical implementation to restore is on `origin/main`, recoverable via `git show origin/main:src/api/app.py`.

**Verification commands** (the repo's real ones; conda env `JuniperCascor`):

- Full suite: `bash src/tests/scripts/run_tests.bash` (from the repo root)
- Targeted: `cd src && python -m pytest tests/unit/ -v` and `cd src && python -m pytest tests/unit/api/ -v`
- Lint for defect 5: `python -m flake8 --select=F821 src/api/app.py` (must exit 0)
- Pre-commit: `pre-commit run --all-files`

**Conventions**: line length 512 for all linters; worktrees live in `/home/pcalnon/Development/python/Juniper/worktrees/` named `<repo>--<branch>--<YYYYMMDD-HHMM>--<short-hash>`; changes land as PRs only (the owner merges); `src/snapshots/` already contains committed `.h5` artifacts — write test snapshot files only to pytest `tmp_path`, never into the repo tree.

## Primary Objective

Make the smallest correct change set that meets the following requirements:

1. makes snapshot restore and snapshot listing actually work and pins them with real-behavior regression tests
2. removes the dead `None` guard in `calculate_accuracy` without changing behavior for valid inputs
3. makes the real `_init_logging_system` body reachable by at least one test while keeping the suite-wide fast-logging fixture
4. restores the merge-clobbered `_settings_with_uvicorn_cli_bind`/`_cli_option_value` block on the PR #380 branch

Each requirement verified against the repo's real tests and lint and landed as pull requests for the owner to merge.

## Assigned Tasks / Directives

1. Run `gh pr list` in juniper-cascor first (the dup-guard): confirm no in-flight PR already addresses any of the five defects, and confirm PR #380 is still open with `src/api/app.py` still missing `_settings_with_uvicorn_cli_bind` at its current head. If PR #380 has been merged, closed, or already repaired, re-assess defect 5 against `origin/main` and report instead of duplicating.
2. Re-confirm every anchor in `## Resources` against the live tree (grep the path, read the cited lines) before changing anything; if any cited line/symbol has moved or disappeared, stop and report rather than guessing.
3. **Track A (defects 1–4)** — work in an isolated worktree on a `fix/...` branch cut from `origin/main`:
   a. **Defect 1**: make `restore_snapshot` actually deliver a restored network.
       - `cls._load_from_hdf5` already returns a usable instance, so the design latitude is how to hand it to the caller (e.g., return the loaded network, or convert to an instance method that updates `self.__dict__`) — pick the smallest design consistent with the method's existing signature, docstring, and call sites, and update the docstring/return contract coherently.
       - Preserve the existing `False`-on-error semantics for the failure paths the current tests pin.
   b. **Defect 2**: make `list_hdf5_snapshots` actually list.
       - Either implement `HDF5Utils.list_hdf5_files` in `src/snapshots/snapshot_utils.py` (matching the class's existing static-method idiom) or call an existing equivalent; the method must return the HDF5 file paths in an existing directory.
   c. **Defect 3**: eliminate the dead `if x is None or y is None:` branch in `calculate_accuracy` so the remaining code has one real validation/defaulting path.
       - Behavior for valid tensor inputs must be unchanged.
   d. **Defect 4**: keep `_cache_logging_system`'s suite-wide speedup, but make the real `_init_logging_system` body reachable by at least one unit test — e.g., a dedicated test that temporarily reinstates the original method (the fixture already preserves it as `original_init` at `conftest.py:847`) and exercises it against a minimal config.
       - Mechanism is your latitude; the requirement is that the real body executes under pytest and its regression would be caught.
   e. **Regression tests (Track A)**: add tests that pin the REAL success behavior — a round-trip test that saves a snapshot to `tmp_path`, restores it, and asserts restored state matches (not merely `is not None`), and a listing test that creates `.h5` files in `tmp_path` and asserts the returned list is non-empty and correct.
       - These must fail against the pre-fix code; do not write tests that pass via the `except` fallbacks.
4. **Track B (defect 5)** — on the existing `cursor/missing-test-coverage-8d4a` branch (PR #380), restore the dropped block from `origin/main`'s `src/api/app.py` (`import sys`, `_cli_option_value` at main `:85`, `_settings_with_uvicorn_cli_bind` at main `:96`) verbatim as a fix commit, so `src/tests/unit/api/test_bind_guard.py` collects and passes and F821 is clean.
    - Do not rewrite or force-push the branch's existing history; add a commit.
5. Keep the two tracks in separate PRs/commits — do not mix the main-based fixes with the PR #380 repair.

## Key Deliverables & Requirements

- **Track A**: one pull request against `main` (never a direct merge) containing the four fixes plus their regression tests, with a description of what changed and why (per-defect).
- **Track B**: one fix commit pushed to `cursor/missing-test-coverage-8d4a` updating PR #380 (or, if that PR is gone, a report of the re-assessment — see directive 1).
- **Acceptance criteria** (all must hold, with command output as evidence):
  - `cd src && python -m pytest tests/unit/ -v` passes on the Track A branch, including the NEW round-trip restore test and the NEW listing test.
  - The new restore and listing tests demonstrably fail when run against the unfixed code (state this check's result in the PR description).
  - At least one test exercises the real `_init_logging_system` body (verifiable by coverage or by a marker/assertion inside the test), while the autouse fast-logging fixture remains in place for the rest of the suite.
  - `python -m flake8 --select=F821 src/api/app.py` exits 0 on the Track B branch, and `cd src && python -m pytest tests/unit/api/test_bind_guard.py -v` passes there.
  - `bash src/tests/scripts/run_tests.bash` and `pre-commit run --all-files` pass on each track's branch.

## Constraints

- Do NOT delete, disable, or weaken any test to make a suite pass — a CRITICAL and ABSOLUTE requirement. (Context: an earlier automated change removed a test that had been "passing" through the `list_hdf5_snapshots` except-path; do not repeat that class of change.)
- Never invent APIs / paths / flags / versions; if the grounding above does not contain it, stop and report rather than guessing.
- Do not modify unrelated in-flight work: the cascor checkout has other active worktrees and an untracked `src/api/JUNIPER_2026-07-05_CASCOR.md` scratch file — leave them untouched.
- Never write snapshot/HDF5 artifacts into the repo tree; tests use `tmp_path`.

## Finalize / Validation

- Verify with the repo's ACTUAL tests + lint + pre-commit (the exact commands in `## Resources`), not a generic "run the tests"; the acceptance evidence is real command output pasted into the PR description, not a promise.
- Recover / abort: no merge without a PR; the owner approves all merges; worktree cleanup only after merge; if any acceptance criterion cannot be met without weakening a test or inventing a fact, stop and report what is blocking.

---
