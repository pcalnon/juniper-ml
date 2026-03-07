# Security Logging Remediation Plan — wake_the_claude.bash

**Task**: Fix sensitive data exposure via default logging + symlink hardening
**Branch**: `bugfix/session-id-validation`
**Worktree**: `juniper-ml--bugfix--session-id-validation--20260306-2001--8bcbdb82`
**Created**: 2026-03-06

---

## 1. Vulnerability Summary

| # | Severity | Title | Location |
|---|----------|-------|----------|
| V4 | Medium | Sensitive data exposure via default logging | `scripts/wake_the_claude.bash` (throughout — ~80 echo statements) |
| V5 | Low | Possible symlink clobber on session-id file write | `save_session_id` (line 107) |

---

## 2. Root Cause Analysis

### V4: Sensitive data exposure via default logging

The script unconditionally emits diagnostic `echo` statements that include:

- **Session IDs** (bearer tokens for `--resume`): logged verbatim in `validate_session_id`, `retrieve_session_id`, `save_session_id`, the resume handler, and the session-id handler
- **Prompt content**: the full assembled `CLAUDE_CODE_PARAMS[*]` (which includes the prompt text) is logged at multiple points including the final `nohup` execution echo
- **All input parameters**: `echo "Input Params: \"${*}\""` logs every argument including session IDs and prompt strings
- **Full command line**: `echo "nohup claude ${CLAUDE_CODE_PARAMS[*]} &"` leaks the entire assembled command

These values can end up in `nohup.out`, CI logs, terminal scrollback, and shared logging systems.

### V5: Symlink clobber on session-id file write

In `save_session_id`, the write path:
```bash
echo "${session_id}" > "./${safe_filename}"
```

If `./<uuid>.txt` is a symlink (e.g., placed by another user in a shared temp directory), the write follows the symlink, overwriting or creating the target file. While the UUID validation already limits the filename to hex + dashes, the symlink itself could point anywhere.

---

## 3. Fix Plan

### Fix V4: Opt-in debug logging with redaction

**Scope**: Entire script

1. **Add `WTC_DEBUG` environment variable** at the top of the globals section, defaulting to `"0"` (off). Activated by `WTC_DEBUG=1 ./wake_the_claude.bash ...`.

2. **Add `debug_log()` function**: Only emits output when `WTC_DEBUG=1`. Replaces all diagnostic `echo` calls.

3. **Add `redact_uuid()` function**: Returns first 8 chars + `...` + last 4 chars of a UUID. Used in all log messages that reference session IDs, even in debug mode.

4. **Convert all diagnostic `echo` to `debug_log`**: Every `echo` statement that serves a diagnostic/tracing purpose (not error messages, not usage output) becomes `debug_log`.

5. **Never log raw prompt content**: Replace prompt-value logging with metadata only (`[prompt: N chars]` or `[prompt from file: <filename>]`).

6. **Redact `CLAUDE_CODE_PARAMS` in logs**: Replace `${CLAUDE_CODE_PARAMS[*]}` with `${#CLAUDE_CODE_PARAMS[@]} args` in all diagnostic lines.

7. **Redact the final execution echo**: The `nohup claude ...` echo before execution should use redacted params.

**What stays as `echo`** (always visible):
- Error messages (`"Error: ..."`)
- Warning messages (`"Warning: ..."`)
- The `usage()` function body
- The final execution confirmation: `"Executing claude with ${#CLAUDE_CODE_PARAMS[@]} args"`

### Fix V5: Symlink rejection in `save_session_id`

**Scope**: `save_session_id` function

1. **Reject symlink targets**: Before writing, check `[[ -L "./${safe_filename}" ]]` and return `${FALSE}` if the path is a symlink.

**Implementation**:
```bash
if [[ -L "./${safe_filename}" ]]; then
    echo "Error: target file is a symlink — refusing to write" >&2
    return "${FALSE}"
fi
```

---

## 4. Test Plan

### Test A: Default mode is quiet

```bash
# Run with no WTC_DEBUG — should produce minimal output
output=$(./wake_the_claude.bash --resume 3e160ecb-feb5-4047-8438-171fb13db8e5 --print 2>&1)
# Verify no session IDs, no "Parsing", no "Define" messages
echo "$output" | grep -c "3e160ecb" # Should be 0
```

### Test B: Debug mode produces output

```bash
WTC_DEBUG=1 ./wake_the_claude.bash --resume 3e160ecb-feb5-4047-8438-171fb13db8e5 --print 2>&1 | grep "Parsing"
# Should produce debug output
```

### Test C: Session IDs are redacted even in debug mode

```bash
output=$(WTC_DEBUG=1 ./wake_the_claude.bash --resume 3e160ecb-feb5-4047-8438-171fb13db8e5 --print 2>&1)
# Should NOT contain the full UUID
echo "$output" | grep -c "3e160ecb-feb5-4047-8438-171fb13db8e5" # Should be 0
# Should contain the redacted form
echo "$output" | grep -c "3e160ecb...b8e5" # Should be > 0
```

### Test D: Prompt content never logged

```bash
echo "super secret prompt" > test_prompt.txt
output=$(WTC_DEBUG=1 ./wake_the_claude.bash --path test_prompt.txt --print 2>&1)
echo "$output" | grep -c "super secret" # Should be 0
rm -f test_prompt.txt
```

### Test E: Symlink write rejected

```bash
ln -s /tmp/evil_target ./fake-session.txt
# Attempt to write — should be rejected
# (Tested via save_session_id internal logic)
rm -f ./fake-session.txt
```

### Test F: Existing flag/regression tests pass

```bash
./wake_the_claude.bash -u 2>&1 | grep "^usage:"    # Should still work
./wake_the_claude.bash --usage 2>&1 | grep "^usage:" # Should still work
./wake_the_claude.bash -h 2>&1 | grep "^usage:"      # Should still work
```

---

## 5. Execution Log

| Step | Status | Notes |
|------|--------|-------|
| Write remediation plan | Complete | This document |
| Implement Fix V4 (debug logging) | Complete | Added `WTC_DEBUG`, `debug_log`, `redact_uuid`; converted ~80 echo → debug_log; redacted session IDs; never log prompt content; log arg counts instead of full params |
| Implement Fix V5 (symlink rejection) | Complete | Added `-L` symlink check before write in `save_session_id` |
| Test A (default quiet) | Pass | No UUID, no "Define", no "Parsing" in default output |
| Test B (debug produces output) | Pass | WTC_DEBUG=1 produces "Parsing" and "Define" messages |
| Test C (session IDs redacted) | Pass | Full UUID never appears; redacted form `3e160ecb...b8e5` appears 3 times |
| Test D (prompt never logged) | Pass | "super secret" never in output; "[N chars]" metadata logged instead |
| Test E (symlink rejected) | Pass | `save_session_id` returns 1 with "target file is a symlink" error |
| Test F (regression) | Pass | `-u`, `--usage`, `-h` all produce usage output; .txt resume works |
| Commit and push | Pending | |
