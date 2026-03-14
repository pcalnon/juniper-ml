# Session ID Validation Bugfix Plan

**Task**: Fix session ID validation errors in `wake_the_claude.bash`
**Branch**: `bugfix/session-id-validation`
**Worktree**: `juniper-ml--bugfix--session-id-validation--20260306-2001--8bcbdb82`
**Created**: 2026-03-06

---

## 0. Operational Reference (Post-Fix)

Use this section as the quick runbook for `scripts/wake_the_claude.bash --resume` behavior.

### Supported `--resume` inputs

- `--resume <uuid>`: accepts a UUID string (hex + dashes)
- `--resume <file.txt>`: accepts a basename `.txt` file in the current directory; file content must be a UUID

### Security and validation constraints

- Filenames containing path separators (for example `nested/session-id.txt` or `../session-id.txt`) are rejected
- Non-`.txt` filenames are rejected
- Session ID files are read-only in resume flow; they are **not** deleted by `retrieve_session_id`
- Invalid session values fail with exit code `1` and print usage once

### Examples

```bash
# Resume directly from a UUID
bash scripts/wake_the_claude.bash --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd --prompt "continue prior task"

# Resume from file in current directory
echo "7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd" > session-id.txt
bash scripts/wake_the_claude.bash --resume session-id.txt --prompt "continue prior task"
```

### Troubleshooting quick checks

| Symptom | Likely Cause | Check |
|---|---|---|
| `path separators — rejected` | Filename included `/` | Use basename only (e.g. `session-id.txt`) |
| `.txt extension — rejected` | Wrong extension | Rename to `.txt` |
| `Session ID file did not contain a valid UUID` | File content is malformed | Ensure file contains only a UUID string |
| Usage printed and script exits | Invalid resume argument | Re-run with valid UUID or valid `.txt` basename |

## 1. Investigation Summary

### Symptom

When `test.bash` runs the second invocation of `wake_the_claude.bash` with `--resume <uuid>.txt`, the session ID validation code produces cascading error messages containing repeated multi-line blocks, ultimately failing with "Session ID is invalid" and printing the usage statement twice.

### Error Flow (from test output)

1. `--resume 3e160ecb-feb5-4047-8438-171fb13db8e5.txt` is received
2. `validate_session_id` is called with `3e160ecb-feb5-4047-8438-171fb13db8e5.txt`
3. UUID check correctly rejects it (has `.txt` suffix)
4. File check correctly identifies it as a file and calls `retrieve_session_id`
5. **Bug manifests**: The returned session ID is corrupted with log messages
6. UUID re-validation fails on the corrupted string
7. Usage is printed twice (once from inside `validate_session_id`, once from the caller)

---

## 2. Root Cause Analysis

### Root Cause 1: Functions mix logging (stdout) with return values (stdout)

**Affected functions**: `retrieve_session_id` (lines 105-114), `validate_session_id` (lines 116-141)

Both functions use `echo` for diagnostic logging AND for returning their result value. When called inside `$(...)` command substitution, ALL `echo` output is captured — logging and return value alike — corrupting the variable.

**Example** — `retrieve_session_id` (line 127 of `validate_session_id`):
```bash
session_id="$(retrieve_session_id "${session_id}")"
```
Intended capture: `3e160ecb-feb5-4047-8438-171fb13db8e5`
Actual capture:
```
Retrieve saved Session ID from file: 3e160ecb-feb5-4047-8438-171fb13db8e5.txt
Completed retrieving saved Session ID: "3e160ecb-feb5-4047-8438-171fb13db8e5" from file: "..."
Removing file: "..."
Completed removing file: "..."
3e160ecb-feb5-4047-8438-171fb13db8e5
```

The same problem cascades upward when the caller on line 339 captures `validate_session_id`:
```bash
SESSION_ID="$(validate_session_id "${SESSION_ID}"; RETURN_VALUE=$?)"
```

### Root Cause 2: `RETURN_VALUE=$?` executes inside the subshell

Line 339:
```bash
SESSION_ID="$(validate_session_id "${SESSION_ID}"; RETURN_VALUE=$?)"
```

The `RETURN_VALUE=$?` after the semicolon runs inside the `$(...)` subshell. The assignment is lost when the subshell exits. The parent shell's `RETURN_VALUE` remains at its initialized value of `"${FALSE}"` (from line 337), so the success check on line 341 always fails.

### Root Cause 3: `exit` inside `$(...)` only exits the subshell

`validate_session_id` calls `usage "${FALSE}"` on error paths (lines 122, 134), which calls `exit`. But when the function runs inside `$(...)`, `exit` terminates the subshell, not the parent script. The parent continues executing with a corrupt `SESSION_ID` and a stale `RETURN_VALUE`, leading to the second usage print on line 351.

### Root Cause 4: Ambiguous echo on line 128

```bash
echo "Completed retrieving Session ID: \"${session_id}\" from file: \"${session_id}\""
```

After `session_id` is reassigned from `retrieve_session_id` output (already corrupted), the same variable is used for both the "value" and "file" placeholders in the log message. Even with a correct value, this log message would be misleading — it should reference the filename, not the session ID, for the "from file" portion.

---

## 3. Fix Plan

### Fix 1: Redirect diagnostic echo statements to stderr in all functions

In `retrieve_session_id`, `validate_session_id`, and `is_valid_uuid`, redirect all diagnostic/logging `echo` statements to stderr (`>&2`). Reserve stdout exclusively for return values.

**Files**: `scripts/wake_the_claude.bash`
**Functions**: `is_valid_uuid` (lines 82-93), `retrieve_session_id` (lines 105-114), `validate_session_id` (lines 116-141)

### Fix 2: Capture exit status correctly in the caller

Change line 339 from:
```bash
SESSION_ID="$(validate_session_id "${SESSION_ID}"; RETURN_VALUE=$?)"
```
To:
```bash
SESSION_ID="$(validate_session_id "${SESSION_ID}")"
RETURN_VALUE=$?
```

This ensures `RETURN_VALUE` captures the subshell's exit status in the parent scope.

### Fix 3: Remove `usage`/`exit` calls from `validate_session_id`

`validate_session_id` should not call `usage`/`exit` — it should return a non-zero status and let the caller decide how to handle the error. This prevents the double-usage-print and ensures `exit` actually terminates the script when the caller invokes it.

Replace `usage "${FALSE}"` calls in `validate_session_id` with `return "${FALSE}"`.

### Fix 4: Fix the ambiguous log message on line 128

Preserve the original filename in a separate local variable before reassigning `session_id`, and use it in the log message.

---

## 4. Test Plan

### Test A: Direct flag matching (regression)

Verify all flag aliases still work after no changes to `matches_pattern`/flag definitions:
```bash
# Short flags
./wake_the_claude.bash -u
./wake_the_claude.bash -h
./wake_the_claude.bash -v

# Long flags
./wake_the_claude.bash --usage
./wake_the_claude.bash --help
```

### Test B: Session ID flow (primary fix verification)

Run the full `test.bash` script and verify:
- Test 000 completes and saves a session ID file
- Test 001 loads the file, extracts the UUID, validates it, and resumes

### Test C: Edge cases for session ID validation

```bash
# Valid UUID directly
./wake_the_claude.bash --resume 3e160ecb-feb5-4047-8438-171fb13db8e5 --print

# UUID in a .txt file
echo "3e160ecb-feb5-4047-8438-171fb13db8e5" > test-uuid.txt
./wake_the_claude.bash --resume test-uuid.txt --print

# Invalid value (not UUID, not a file)
./wake_the_claude.bash --resume invalid-value --print

# Empty resume value
./wake_the_claude.bash --resume -- --print
```

### Test D: No regressions in other parameter parsing

```bash
./wake_the_claude.bash --id --worktree --skip-permissions --path "../../../Juniper/juniper-ml/scripts/test_prompt-000.md" -- --effort high --print
```

---

## 5. Execution Log

| Step | Status | Notes |
|------|--------|-------|
| Investigation | Complete | Traced error flow through error messages and source code |
| Root cause analysis | Complete | 4 root causes identified (stdout/stderr mixing, subshell RETURN_VALUE, exit-in-subshell, ambiguous log) |
| Implement Fix 1 (stderr redirects) | Complete | Added `>&2` to all diagnostic echo in `is_valid_uuid`, `retrieve_session_id`, `validate_session_id` |
| Implement Fix 2 (RETURN_VALUE capture) | Complete | Moved `RETURN_VALUE=$?` to separate line after `$(...)` |
| Implement Fix 3 (remove exit from validate) | Complete | Replaced `usage "${FALSE}"` with `return "${FALSE}"` in `validate_session_id` |
| Implement Fix 4 (ambiguous log message) | Complete | Added `session_id_filename` local var, used in "from file" log message |
| Test A (flag regression) | Pass | `-u`, `--usage`, `-h` all produce correct output |
| Test B (session ID flow) | Not run | Requires `claude` CLI; skipped in this environment |
| Test C (edge cases) | Pass | All 5 isolated unit tests pass: valid UUID, UUID-from-file, invalid, empty, file-with-bad-content |
| Test D (other params) | Not run | Requires `claude` CLI for full end-to-end |
| Commit and push | Pending | Awaiting user approval |

### Regressions Identified

None. The `matches_pattern` logic and all parameter parsing branches were not modified. Only the 4 session-ID-related functions and the resume handler's RETURN_VALUE capture were changed.
