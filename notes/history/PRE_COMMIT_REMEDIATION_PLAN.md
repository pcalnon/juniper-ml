# Pre-Commit Remediation Plan

**Date**: 2026-03-11
**Branch**: `tooling/more_claude_utils`
**Status**: Complete — all 5 projects pass pre-commit checks

---

## Summary

After establishing pre-commit configurations across 5 Juniper ecosystem projects, 9 pre-existing code issues remain that cause hook failures. This plan addresses each issue with a specific fix.

**juniper-data-client**: Clean — no remaining issues.

---

## Issue Inventory

### juniper-cascor-client (2 issues)

| # | Hook | File:Line | Error | Severity |
|---|------|-----------|-------|----------|
| 1 | flake8 | `tests/test_fake_ws_client.py:499` | B018: Useless Tuple expression | Bug |
| 2 | markdownlint | `AGENTS.md:67` | MD040: Fenced code block missing language | Docs |

### juniper-cascor-worker (2 issues)

| # | Hook | File:Line | Error | Severity |
|---|------|-----------|-------|----------|
| 3 | flake8 | `tests/test_worker.py:28` | B017: `assertRaises(Exception)` too broad | Bug |
| 4 | markdownlint | `AGENTS.md:77` | MD040: Fenced code block missing language | Docs |

### juniper-ml (4 issues)

| # | Hook | File(s) | Error | Severity |
|---|------|---------|-------|----------|
| 5 | check-case-conflict | `images/alligator-juniper-full-canopy.JPG` vs `.jpg` | Case conflict between two tracked files | Cleanup |
| 6 | flake8 | `tests/test_wake_the_claude.py:591,1221,1223` | F841 unused var, F821 undefined `args`, E302 spacing | Bug |
| 7 | shellcheck | `scripts/a.bash`, `scripts/b.bash` | SC2199, SC2145, SC2089, SC2090, SC1073, SC1072, SC1085 | Cleanup |
| 8 | markdownlint | `scripts/test_prompt-000.md:1`, `scripts/test_prompt-001.md:1` | MD041: First line must be top-level heading | Docs |

### juniper-deploy (1 issue)

| # | Hook | File:Line | Error | Severity |
|---|------|-----------|-------|----------|
| 9 | markdownlint | `AGENTS.md:81`, `README.md:15` | MD040: Fenced code block missing language | Docs |

---

## Remediation Details

### Issue 1: B018 useless Tuple expression (juniper-cascor-client)

**File**: `tests/test_fake_ws_client.py:499`

**Current code**:

```python
cb.assert_called_once(), f"Callback for '{msg_type}' should have been called exactly once"
```

**Problem**: The comma creates a tuple `(None, "message")` that is never used. The assertion message is not passed to `assert_called_once()` — it just floats as the second element of a discarded tuple.

**Fix**: Use an explicit `assert` to attach the message, or replace with a call that accepts a message. Since `assert_called_once()` takes no arguments, wrap in an assert:

```python
assert cb.call_count == 1, f"Callback for '{msg_type}' should have been called exactly once"
```

### Issue 2: MD040 fenced code block missing language (juniper-cascor-client)

**File**: `AGENTS.md:67`

**Current code**:

````markdown
```
juniper-ml[clients] --> juniper-cascor-client --> JuniperCascor (service)
JuniperCanopy --> juniper-cascor-client --> JuniperCascor (service)
```
````

**Fix**: Add `text` language specifier:

````markdown
```text
juniper-ml[clients] --> juniper-cascor-client --> JuniperCascor (service)
JuniperCanopy --> juniper-cascor-client --> JuniperCascor (service)
```
````

### Issue 3: B017 `assertRaises(Exception)` too broad (juniper-cascor-worker)

**File**: `tests/test_worker.py:28`

**Current code**:

```python
with pytest.raises(Exception):
    CandidateTrainingWorker(config)
```

**Problem**: Catching bare `Exception` can mask unrelated errors. The constructor calls `config.validate()` which raises `WorkerConfigError` for invalid config.

**Fix**: Use the specific exception:

```python
with pytest.raises(WorkerConfigError):
    CandidateTrainingWorker(config)
```

Add `WorkerConfigError` to the file's imports if not already present.

### Issue 4: MD040 fenced code block missing language (juniper-cascor-worker)

**File**: `AGENTS.md:77`

**Current code**:

````markdown
```
juniper-ml[worker] --> juniper-cascor-worker --> JuniperCascor (manager)
```
````

**Fix**: Add `text` language specifier.

### Issue 5: Case conflict in images directory (juniper-ml)

**Files**: `images/alligator-juniper-full-canopy.JPG` and `images/alligator-juniper-full-canopy.jpg`

**Problem**: Two files with identical names differing only by extension case. On case-insensitive filesystems (macOS, Windows), these would collide.

**Analysis**: Neither file is referenced in any code, README, or documentation file. Both can coexist on Linux, but the `.JPG` variant is the original (larger, likely the source image). The `.jpg` variant may be a downsized copy or accidental duplicate.

**Fix**: Remove the `.jpg` variant (lowercase) since the `.JPG` file is the original. Alternatively, remove `.JPG` and keep `.jpg` for lowercase consistency. Choose whichever is the actual image (non-zero size, correct content). If both are valid, keep one and delete the other.

**Verification**: Check file sizes and content to determine which to keep.

### Issue 6: Flake8 errors in test_wake_the_claude.py (juniper-ml)

**File**: `tests/test_wake_the_claude.py`

Three distinct errors:

#### 6a: F841 — Unused variable `result` (line 591)

```python
result = self._run_script(
    ["--id", VALID_UUID, "--file", prompt_file.name, "--path", str(prompt_dir)],
    cwd=temp_dir,
    env=env,
)
```

**Fix**: Prefix with underscore: `_result = self._run_script(...)` — or remove the assignment if the return value is truly unused. However, the script execution itself is needed for its side effects, so just prefix with underscore.

#### 6b: F821 — Undefined name `args` (line 1221)

```python
invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
self.assertEqual(invocations, [])
self.assertIn("prompt from combined file-then-path", args)  # <-- `args` undefined
```

**Problem**: This assertion references `args` which is not defined in this test method (`test_path_directory_and_missing_filename_fail_without_invoking_claude`). The test verifies that claude is NOT invoked (invocations should be empty), so there are no args to check. This line appears to be a copy-paste error from a neighboring test.

**Fix**: Delete line 1221. The test's purpose is to verify the script fails early without invoking claude — asserting on non-existent args is both incorrect and contradicts the test intent (if invocations is empty, there are no args).

#### 6c: E302 — Expected 2 blank lines (line 1223)

**Problem**: Only 1 blank line between `test_path_directory_and_missing_filename_fail_without_invoking_claude` and `class DefaultInteractiveLauncherRuntimeTests`.

**Fix**: After removing line 1221 (issue 6b), ensure there are exactly 2 blank lines between the end of the previous class and the start of `DefaultInteractiveLauncherRuntimeTests`. This will resolve automatically once the erroneous line is removed and proper spacing is maintained.

### Issue 7: ShellCheck errors in experimental scripts (juniper-ml)

**Files**: `scripts/a.bash`, `scripts/b.bash`

**Analysis**: These are early prototyping/scratch scripts from the initial commit (`8bcbdb8 — "adding script to drive claude code. this is the start of a more automated approach"`). They are not referenced by any test, CI pipeline, or documentation. The functionality they were prototyping was fully superseded by `wake_the_claude.bash`.

**Fix**: Delete both files. They are dead code with no consumers.

### Issue 8: MD041 first-line heading in test prompt files (juniper-ml)

**Files**: `scripts/test_prompt-000.md`, `scripts/test_prompt-001.md`

**Analysis**: These are test fixture files used by `scripts/test.bash` (the manual end-to-end harness). They contain plain-text prompts for Claude Code ("Hello Claude!") and intentionally lack markdown structure. Adding a heading would change their purpose.

**Fix**: Exclude these files from markdownlint. Add an entry to `.markdownlint.yaml`:

```yaml
# Ignore test prompt fixture files (not real documentation)
```

And add a `.markdownlintignore` file or use the pre-commit hook's `exclude` pattern to skip `scripts/test_prompt-*.md`.

**Preferred approach**: Add an `exclude` regex to the markdownlint hook in `.pre-commit-config.yaml`:

```yaml
exclude: '^scripts/test_prompt-.*\.md$'
```

### Issue 9: MD040 fenced code blocks missing language (juniper-deploy)

**Files**: `AGENTS.md:81`, `README.md:15`

**Current code** (both files): Fenced code blocks using bare ` ``` ` for plain-text diagrams.

**Fix**: Add `text` language specifier to each fenced code block.

---

## Implementation Order

1. **juniper-cascor-client**: Fix issues 1, 2
2. **juniper-cascor-worker**: Fix issues 3, 4
3. **juniper-deploy**: Fix issue 9
4. **juniper-ml**: Fix issues 5, 6, 7, 8 (most changes, do last)

---

## Verification

After all fixes, run in each project:

```bash
pre-commit run --all-files
```

All hooks must pass (exit code 0) with no failures.
