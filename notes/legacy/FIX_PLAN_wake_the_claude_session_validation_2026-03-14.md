# Fix Plan: wake_the_claude.bash Session ID Validation Failures

**Date**: 2026-03-14
**Repository**: juniper-ml
**Status**: Implemented and verified

## Context

25 of 58 tests in `tests/test_wake_the_claude.py` were failing due to 4 bugs in `scripts/wake_the_claude.bash`. All bugs related to session ID validation and UUID generation logic. The core failure: `validate_session_id()` was refactored to require `.txt` extension on all inputs, breaking the `--resume <UUID>` flow that most tests rely on.

## Root Causes and Fixes

### RC1: `validate_session_id()` rejects raw UUIDs (23 tests)

- **Location**: `scripts/wake_the_claude.bash:275`
- **Bug**: 1st Pass validation unconditionally requires `.txt` extension. Raw UUIDs passed via `--resume` are rejected before reaching 2nd Pass UUID validation at line 290.
- **Fix**: Added `is_valid_uuid` check as a fast-path before the `.txt` extension check. If the input is a valid UUID, it is returned immediately without going through file-based validation.
- **Safety**: `.txt` filenames (e.g., `session-id.txt`) are not valid UUIDs and fall through to existing logic. `UUID.txt` filenames won't collide because the regex requires exactly 32 hex digits with no trailing characters.

### RC2: `generate_uuid()` validation is a no-op (1 test)

- **Location**: `scripts/wake_the_claude.bash:194`
- **Bug**: `[[ "$(is_valid_uuid "${generated_uuid}")" == "${FALSE}" ]]` captures stdout (always empty) instead of checking the return code. The validation never triggers.
- **Fix**: Changed to `! is_valid_uuid "${generated_uuid}"` to correctly check the return code.

### RC3: `generate_uuid()` fallback chain doesn't validate intermediate results (1 test)

- **Location**: `scripts/wake_the_claude.bash:166-190`
- **Bug**: Each fallback step (uuidgen, /proc, python3) only checks `generated_uuid == ""`. If uuidgen or /proc returns an invalid non-empty string, subsequent fallbacks are skipped.
- **Fix**: Added `is_valid_uuid` validation after each fallback step. When validation fails, `generated_uuid` is reset to `""` so the next fallback runs. This was the original design (visible as commented-out code).

### RC4: Nohup error message goes to stdout instead of stderr (1 test)

- **Location**: `scripts/wake_the_claude.bash:632`
- **Bug**: `echo "Error: Failed to open nohup log file..."` goes to stdout, but tests correctly expect error messages on stderr.
- **Fix**: Added `>&2` redirect to send error message to stderr.

## Files Modified

- `scripts/wake_the_claude.bash` — All 4 fixes (lines 166-194, 268-280, 632)

## Validation

- 3 sub-agents validated the plan before implementation:
  - Agent 1: Confirmed RC1 fix won't break `.txt` file lookup path
  - Agent 2: Traced RC2+RC3 fixes through both failing test execution paths
  - Agent 3: Verified zero regression risk across all 33 previously-passing tests
- All 58 tests pass after implementation
- `test_resume_file_safety.bash` regression script passes
