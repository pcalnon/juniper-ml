# Test Failure Remediation Plan

**Date**: 2026-03-12
**Branch**: `tooling/more_claude_utils`
**Scope**: `tests/test_wake_the_claude.py` — 9 user-reported failures + 6 independently reproduced failures

---

## Executive Summary

Test failures fall into three root cause categories:

1. **Incorrect test assertions** (6 tests) — wrong expected values, contradictory assertions, stray code in wrong scope
2. **Environment contamination** (6 tests) — `CLAUDE_SKIP_PERMISSIONS` leaking from the host shell into test subprocesses
3. **User-environment-specific failures** (3 tests) — nohup log and write-check tests that fail in certain shell environments but pass in clean environments; resolved by category 2 fix

---

## Root Cause Analysis

### Category A: Incorrect Test Assertions

These tests have wrong expected values or contradictory assertions that fail regardless of environment.

| # | Test Method | Line | Bug Description |
|---|-------------|------|-----------------|
| A1 | `WakeTheClaudeResumeTests::test_custom_session_and_logs_dirs_are_created_when_missing` | 624 | Asserts `last_invocation_args[-1] == "from-prompt-file"` but the test invokes with `--prompt hello`. Expected value should be `"hello"`. |
| A2 | `WakeTheClaudeResumeTests::test_default_interactive_script_forwards_expected_defaults` | 651, 658 | **Three contradictory assertions**: (1) expects `--dangerously-skip-permissions` present (wrong — not set by default), (2) expects prompt tokens after `effort_index + 2` but permissions flag sits between, (3) expects `args == ["--session-id", VALID_UUID, "--print", "hello"]` which is a completely unrelated args list. |
| A3 | `WakeTheClaudeSecurityTests::test_path_then_file_flags_resolve_combined_prompt_file` | 1161 | Expects `"prompt from path+file"` but prompt file contains `"prompt from combined path-then-file"`. |
| A4 | `WakeTheClaudeSecurityTests::test_file_then_path_flags_resolve_combined_prompt_file` | 1200 | Expects `"prompt from file+path"` but prompt file contains `"prompt from combined file-then-path"`. |
| A5 | `WakeTheClaudeSecurityTests::test_path_directory_and_filename_resolve_prompt_when_file_precedes_path` | 1181 | Expects `"prompt from combined path-then-file"` but prompt file contains `"prompt from file+path"`. |
| A6 | `WakeTheClaudeSecurityTests::test_path_directory_and_missing_filename_fail_without_invoking_claude` | 1221 | Stray assertion `self.assertIn("prompt from combined file-then-path", args)` references undefined variable `args`. Belongs in a different test method. |

### Category B: Environment Contamination

Both `_install_fake_claude()` methods (in `WakeTheClaudeResumeTests` and `WakeTheClaudeSecurityTests`) call `os.environ.copy()` without sanitizing shell-specific variables. When the host shell has `CLAUDE_SKIP_PERMISSIONS=1` (common for Claude Code users), the variable leaks into the `default_interactive_session_claude_code.bash` subprocess, causing it to unconditionally inject `--dangerously-skip-permissions`.

**Affected tests** (from user's reported failures):

| # | Test Method | Symptom |
|---|-------------|---------|
| B1 | `WakeTheClaudeSecurityTests::test_default_launcher_does_not_skip_permissions` | `--dangerously-skip-permissions` found in args |
| B2 | `WakeTheClaudeSecurityTests::test_default_launcher_executes_with_expected_default_arguments` | Same |
| B3 | `WakeTheClaudeSecurityTests::test_default_launcher_runtime_omits_skip_permissions_by_default` | Same (even though it pops the var, `BASH_ENV` re-sources it) |
| B4 | `WakeTheClaudeSecurityTests::test_default_launcher_runtime_honors_skip_permissions_opt_in` | Second half (clean env) shows permissions |
| B5 | `DefaultInteractiveLauncherRuntimeTests::test_default_launcher_omits_skip_permissions_by_default` | Same |

**Secondary vector**: `BASH_ENV` in the host environment can point to a profile script that re-exports `CLAUDE_SKIP_PERMISSIONS=1`, defeating the `env.pop()` in tests that attempt to clear it.

### Category C: Environment-Specific Failures

Three tests from the user's report that pass in a clean environment but fail when env contamination changes script behavior:

| # | Test Method | Symptom |
|---|-------------|---------|
| C1 | `test_no_writable_log_location_fails_without_silent_success` | Script exits 0 instead of 1 |
| C2 | `test_non_writable_logs_dir_falls_back_to_home_log_and_still_launches` | Nohup log not found at HOME fallback path |
| C3 | `test_headless_mode_invokes_claude_via_nohup` | Nohup log not created in logs dir |

These are resolved by the Category B fix (env sanitization), as confirmed by successful reproduction: they pass in a clean environment.

---

## Fix Plan

### Fix 1: Sanitize test environment in `_install_fake_claude()` (Category B)

**Files**: `tests/test_wake_the_claude.py`
**Methods**: `WakeTheClaudeResumeTests._install_fake_claude()` (line 60) and `WakeTheClaudeSecurityTests._install_fake_claude()` (line 831)

Add after `env = os.environ.copy()`:
```python
# Prevent host shell variables from contaminating test subprocess behavior
for var in ("CLAUDE_SKIP_PERMISSIONS", "BASH_ENV", "ENV"):
    env.pop(var, None)
```

Also add to `DefaultInteractiveLauncherRuntimeTests._install_fake_launcher_stack()` and individual tests that construct their own env dict.

### Fix 2: Correct test_custom_session_and_logs_dirs_are_created_when_missing (A1)

**Line 624**: Change expected value from `"from-prompt-file"` to `"hello"` to match the actual prompt passed.

### Fix 3: Rewrite test_default_interactive_script_forwards_expected_defaults (A2)

**Lines 626-658**: Remove contradictory assertions. The correct expected behavior for the default launcher (without `CLAUDE_SKIP_PERMISSIONS=1`) is:
- `--session-id` followed by a generated UUID
- `--worktree`
- `--effort high`
- `Hello World, Claude!` as the final prompt arg
- NO `--dangerously-skip-permissions`

Remove the stray final assertion at line 658.

### Fix 4: Correct prompt text expectations (A3, A4, A5)

For each test, align the expected string with the actual content written to the prompt file:

| Test | Current Expected | Correct Expected |
|------|-----------------|-----------------|
| `test_path_then_file_flags_resolve_combined_prompt_file` | `"prompt from path+file"` | `"prompt from combined path-then-file"` |
| `test_file_then_path_flags_resolve_combined_prompt_file` | `"prompt from file+path"` | `"prompt from combined file-then-path"` |
| `test_path_directory_and_filename_resolve_prompt_when_file_precedes_path` | `"prompt from combined path-then-file"` | `"prompt from file+path"` |

### Fix 5: Remove stray assertion (A6)

**Line 1221**: Remove `self.assertIn("prompt from combined file-then-path", args)` from `test_path_directory_and_missing_filename_fail_without_invoking_claude`. The variable `args` is not defined in this scope.

---

## Verification

After applying all fixes, run the full test suite in both environments:

```bash
# Clean environment
python3 -m pytest tests/test_wake_the_claude.py -v

# With CLAUDE_SKIP_PERMISSIONS=1 (simulates user's environment)
CLAUDE_SKIP_PERMISSIONS=1 python3 -m pytest tests/test_wake_the_claude.py -v
```

Both must produce 0 failures.

## Implementation Results

All fixes applied and verified:

```
# Clean environment
56 passed in 7.45s

# With CLAUDE_SKIP_PERMISSIONS=1
56 passed in 7.46s

# Resume file safety regression
PASS: invalid resume file is preserved
```

---

## Risk Assessment

- **No script changes required** — all issues are in test assertions or test infrastructure
- **No behavioral changes** — fixes align tests with existing correct script behavior
- **Low regression risk** — only test expectations are modified, not production code
