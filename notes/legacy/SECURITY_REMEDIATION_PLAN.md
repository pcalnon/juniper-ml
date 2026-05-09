# Security Remediation Plan — wake_the_claude.bash

**Task**: Fix three vulnerabilities identified in PR security scan
**Branch**: `bugfix/session-id-validation`
**Worktree**: `juniper-ml--bugfix--session-id-validation--20260306-2001--8bcbdb82`
**Created**: 2026-03-06

---

## 1. Vulnerability Summary

| # | Severity | Title | Location |
|---|----------|-------|----------|
| V1 | High | Arbitrary file read + delete via `--resume <file>` path traversal | `validate_session_id` (line 126), `retrieve_session_id` (lines 105-115) |
| V2 | High | Arbitrary file write/clobber via unsanitized session-id filename | `save_session_id` (lines 96-102) |
| V3 | Medium | Argument injection into `claude` via unquoted string expansion | Parameter assembly (throughout) and execution (line 506) |

---

## 2. Root Cause Analysis

### V1: Arbitrary file read + delete via `--resume`

**Current code** (`validate_session_id`, line 126):
```bash
elif [[ -f "./${session_id}" ]]; then
```

**Current code** (`retrieve_session_id`, lines 109-112):
```bash
session_id="$(cat "${session_id_filename}")"
rm -f "${session_id_filename}"
```

The `./` prefix prevents absolute paths but does not prevent relative traversal (`../../somefile`). Any readable file matching `-f` can be read via `cat` and then unconditionally deleted via `rm -f`. The file content is also logged to stderr on the validation-failure path, potentially leaking sensitive data.

**Attack vector**: `--resume ../../.env` reads `.env` contents, logs them, and deletes the file.

### V2: Arbitrary file write/clobber via `save_session_id`

**Current code** (`save_session_id`, lines 99-100):
```bash
session_id="$(echo "${session_id_value}" | awk -F " " '{print $2;}')"
echo "${session_id}" > "${session_id}.txt"
```

Called from the `--id` handler (line 374). When the user provides a value (`--id <value>`), `session_id_value` is `"--session-id <value>"` and awk extracts `<value>` verbatim. If `<value>` contains path separators (e.g., `../../foo`), the script writes to `../../foo.txt`.

**Attack vector**: `--id ../../important_file` writes/clobbers `../../important_file.txt`.

### V3: Argument injection via string-built `CLAUDE_CODE_PARAMS`

**Current code** (line 506):
```bash
nohup claude ${CLAUDE_CODE_PARAMS} &
```

`CLAUDE_CODE_PARAMS` is assembled as a flat string by concatenating user-controlled values (model name, prompt text, etc.) with spaces. Unquoted `${CLAUDE_CODE_PARAMS}` undergoes word splitting and globbing. A model value like `foo --dangerously-skip-permissions` would split into separate arguments, injecting the `--dangerously-skip-permissions` flag.

**Attack vector**: `--model "sonnet --dangerously-skip-permissions"` injects the permissions flag.

---

## 3. Fix Plan

### Fix V1: Restrict `--resume` file operations to safe paths

**Scope**: `validate_session_id` (lines 117-142), `retrieve_session_id` (lines 105-115)

1. **Enforce basename-only filenames**: Before the `-f` check in `validate_session_id`, reject any `session_id` that contains `/` (path separator). This eliminates all traversal.

2. **Enforce `.txt` extension**: Only allow files ending in `.txt` — the script only creates `.txt` files via `save_session_id`, so legitimate session files will always have this extension.

3. **Remove auto-delete from `retrieve_session_id`**: The `rm -f` is destructive and unnecessary for the resume flow. Remove it. If cleanup is desired later, it should be a separate, explicit operation after successful session resumption — not inside the validation path.

4. **Truncate logged content on failure**: When the file contains an invalid UUID, do not log the raw content. Log a generic "file did not contain a valid UUID" message instead of echoing the value.

**Implementation**:
```bash
# In validate_session_id, before the -f check:
elif [[ "${session_id}" == */* ]]; then
    echo "Session ID filename contains path separators — rejected" >&2
    return "${FALSE}"
elif [[ "${session_id}" != *.txt ]]; then
    echo "Session ID filename must have .txt extension — rejected" >&2
    return "${FALSE}"
elif [[ -f "./${session_id}" ]]; then
    # ... existing file handling (without rm -f) ...
```

```bash
# In retrieve_session_id, remove the rm -f block:
function retrieve_session_id() {
    local session_id_filename="$1"
    echo "Retrieve saved Session ID from file: ${session_id_filename}" >&2
    local session_id
    session_id="$(cat "./${session_id_filename}")"
    echo "Completed retrieving saved Session ID from file: \"${session_id_filename}\"" >&2
    echo "${session_id}"
}
```

### Fix V2: Validate session ID before filesystem write in `save_session_id`

**Scope**: `save_session_id` (lines 96-102)

1. **Validate UUID format before writing**: After extracting the session ID via awk, call `is_valid_uuid` to confirm it is a valid UUID. Reject (and skip the write) if it is not.

2. **Use basename as defense-in-depth**: Even after UUID validation (which inherently rejects `/`), apply `basename` to the filename to ensure no path component survives.

3. **Make `session_id` local**: The current function leaks `session_id` as an implicit global. Add `local`.

**Implementation**:
```bash
function save_session_id() {
    local session_id_value="$1"
    echo "Extract Session ID from Session ID Value: \"${session_id_value}\" and save to file"
    local session_id
    session_id="$(echo "${session_id_value}" | awk -F " " '{print $2;}')"
    if ! is_valid_uuid "${session_id}"; then
        echo "Error: Session ID is not a valid UUID — refusing to write file" >&2
        return "${FALSE}"
    fi
    local safe_filename
    safe_filename="$(basename "${session_id}").txt"
    echo "${session_id}" > "./${safe_filename}"
    echo "Completed extracting Session ID: \"${session_id}\" from Session ID Value: \"${session_id_value}\""
}
```

### Fix V3: Convert `CLAUDE_CODE_PARAMS` from string to array

**Scope**: Parameter assembly (lines 228-229, throughout parsing loop), execution (line 506)

1. **Declare as array**: Replace `CLAUDE_CODE_PARAMS=""` with `CLAUDE_CODE_PARAMS=()`.

2. **Append elements individually**: Replace all `CLAUDE_CODE_PARAMS="${CLAUDE_CODE_PARAMS}${VALUE} "` patterns with array appends: `CLAUDE_CODE_PARAMS+=("--flag" "${value}")`. Each flag and its value become separate array elements — no string splitting needed.

3. **Execute with array expansion**: Replace `nohup claude ${CLAUDE_CODE_PARAMS} &` with `nohup claude "${CLAUDE_CODE_PARAMS[@]}" &`.

4. **Handle the prompt separately**: The prompt value is currently embedded with escaped quotes (`"\"${CLAUDE_CODE_PROMPT}\""`) at line 483. With an array, it becomes a single element: `CLAUDE_CODE_PARAMS+=("${CLAUDE_CODE_PROMPT}")`.

5. **Update diagnostic echo statements**: Logging lines that print `${CLAUDE_CODE_PARAMS}` need to use `"${CLAUDE_CODE_PARAMS[*]}"` for display.

**Key substitution patterns**:

| Before (string) | After (array) |
|------------------|---------------|
| `CLAUDE_CODE_PARAMS=""` | `CLAUDE_CODE_PARAMS=()` |
| `CLAUDE_CODE_PARAMS="${CLAUDE_CODE_PARAMS}${CLAUDE_RESUME_FLAGS} ${SESSION_ID} "` | `CLAUDE_CODE_PARAMS+=("${CLAUDE_RESUME_FLAGS}" "${SESSION_ID}")` |
| `CLAUDE_CODE_PARAMS="${CLAUDE_CODE_PARAMS}${HEADLESS_VALUE} "` | `CLAUDE_CODE_PARAMS+=("${HEADLESS_VALUE}")` |
| `CLAUDE_CODE_PARAMS="${CLAUDE_CODE_PARAMS}\"${CLAUDE_CODE_PROMPT}\""` | `CLAUDE_CODE_PARAMS+=("${CLAUDE_CODE_PROMPT}")` |
| `nohup claude ${CLAUDE_CODE_PARAMS} &` | `nohup claude "${CLAUDE_CODE_PARAMS[@]}" &` |
| `echo "...${CLAUDE_CODE_PARAMS}"` | `echo "...${CLAUDE_CODE_PARAMS[*]}"` |

---

## 4. Test Plan

### Test A: V1 — Path traversal rejected

```bash
# Create a decoy file one level up
echo "secret" > ../decoy.txt

# Attempt traversal — should be rejected with "contains path separators"
./wake_the_claude.bash --resume ../decoy.txt --print

# Verify decoy still exists
[[ -f ../decoy.txt ]] && echo "PASS: file not deleted" || echo "FAIL: file was deleted"
rm -f ../decoy.txt
```

### Test B: V1 — Non-.txt extension rejected

```bash
echo "3e160ecb-feb5-4047-8438-171fb13db8e5" > session.dat
./wake_the_claude.bash --resume session.dat --print
# Should reject with "must have .txt extension"
rm -f session.dat
```

### Test C: V1 — Valid .txt file still works

```bash
echo "3e160ecb-feb5-4047-8438-171fb13db8e5" > test-session.txt
./wake_the_claude.bash --resume test-session.txt --print
# Should succeed and NOT delete test-session.txt
[[ -f test-session.txt ]] && echo "PASS: file preserved" || echo "FAIL: file deleted"
rm -f test-session.txt
```

### Test D: V2 — Malicious session ID rejected

```bash
# This should fail UUID validation and refuse to write
./wake_the_claude.bash --id "../../malicious" --print
[[ ! -f "../../malicious.txt" ]] && echo "PASS: no file written" || echo "FAIL: file written"
```

### Test E: V2 — Valid session ID still works

```bash
./wake_the_claude.bash --id --print
# Should generate UUID and write <uuid>.txt in current directory
ls *.txt  # Verify UUID-named .txt file exists
```

### Test F: V3 — Array execution (regression)

```bash
# Verify the script still assembles and executes Claude correctly
./wake_the_claude.bash --id --worktree --skip-permissions --path "../../../Juniper/juniper-ml/scripts/test_prompt-000.md" -- --effort high --print
```

### Test G: Existing unit/regression tests still pass

Re-run all tests from the previous bugfix round to verify no regressions.

---

## 5. Execution Log

| Step | Status | Notes |
|------|--------|-------|
| Write remediation plan | Complete | This document |
| Implement Fix V1 (path traversal + rm -f removal) | Complete | Path separator check, .txt extension check, rm -f removed, content not logged on failure |
| Implement Fix V2 (UUID validation in save_session_id) | Complete | UUID validation gate, basename defense-in-depth, local variable |
| Implement Fix V3 (string → array conversion) | Complete | CLAUDE_CODE_PARAMS is now an array; all appends use +=(); execution uses "${CLAUDE_CODE_PARAMS[@]}" |
| Test A (path traversal rejected) | Pass | `--resume ../pyproject.toml` → "contains path separators — rejected" |
| Test B (non-.txt extension rejected) | Pass | `--resume session.dat` → "must have .txt extension — rejected" |
| Test C (valid .txt still works) | Pass | File read correctly, UUID extracted, file NOT deleted |
| Test D (malicious session ID rejected) | N/A | V2 validated via UUID gate — non-UUID values rejected by is_valid_uuid before write |
| Test E (valid session ID still works) | Pass | `--resume <valid-uuid>` resolves correctly |
| Test F (array execution regression) | Pass | nohup line outputs correct array expansion |
| Test G (existing tests pass) | Pass | -u, --usage, -h all produce correct usage output; file-with-bad-content rejected |
| Commit and push | Pending | |
