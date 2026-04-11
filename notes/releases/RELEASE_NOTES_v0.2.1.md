# Juniper ML v0.2.1 Release Notes

**Release Date:** 2026-03-06
**Version:** 0.2.1
**Codename:** Claude Launcher Hardening
**Release Type:** PATCH (with security fixes)

---

## Overview

This patch release introduces `wake_the_claude.bash` (the canonical Claude Code launcher) and addresses three security findings in its early implementation: a path traversal in `--resume`, an arbitrary file write in `save_session_id`, and an argument injection vector via `CLAUDE_CODE_PARAMS`. Also fixes session-ID validation regressions.

> **Status:** STABLE — Tooling-only release with no impact on the published meta-package's runtime dependencies.

---

## Release Summary

- **Release type:** PATCH (security fixes + bug fixes)
- **Primary focus:** Claude Code launcher script hardening and session-ID validation reliability
- **Breaking changes:** No
- **Priority summary:** Three security findings (2 High, 1 Medium) resolved; session-ID handling made robust

---

## What's New

### Claude Code Launcher

- `scripts/wake_the_claude.bash` — Shell script to launch Claude Code sessions with configurable flags, session persistence, and `--resume` support

### Documentation & Templates

- `notes/SESSION_ID_VALIDATION_BUGFIX_PLAN.md` — Root cause analysis and fix plan for session-ID handling regressions
- `notes/SECURITY_REMEDIATION_PLAN.md` — Security vulnerability analysis and remediation plan
- `notes/pull_requests/PR_SESSION_ID_VALIDATION_BUGFIX.md` — PR description archive
- `notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md` — PR description template (adopted from sibling repos)

---

## Bug Fixes

### Session ID Validation Regression

**Problem:** Diagnostic `echo` statements in `is_valid_uuid`, `retrieve_session_id`, and `validate_session_id` were writing to stdout instead of stderr, polluting return values captured via `$(...)`. As a result, callers received noise concatenated with the intended UUID, breaking session resume.

**Solution:**

- Redirected diagnostic `echo` statements to stderr (`>&2`), reserving stdout for actual return values
- Moved `RETURN_VALUE=$?` to a separate line so the exit status propagates to the parent scope
- Replaced `usage`/`exit` calls with `return` inside `validate_session_id` (since `exit` inside `$(...)` only terminates the subshell, leading to a double-printed usage message)
- Added a `session_id_filename` local variable to preserve the original filename for the "from file" log message

**Files:** `scripts/wake_the_claude.bash`

---

## Security

### Path Traversal in `--resume` (HIGH)

**Risk:** A crafted `--resume` filename containing path separators (e.g., `../../../etc/passwd`) could cause `retrieve_session_id` to read arbitrary files from the host filesystem. Additionally, an embedded `rm -f` against the user-supplied path created a destructive code path.

**Fix:**

- Reject filenames containing path separators (`/`)
- Require the `.txt` extension for resume filenames
- Removed the destructive `rm -f` from `retrieve_session_id`
- Suppressed raw file content in error logs to prevent information leakage

### Arbitrary File Write in `save_session_id` (HIGH)

**Risk:** Unvalidated input passed to `save_session_id` could be used to write arbitrary files via crafted UUID-like strings.

**Fix:**

- Added UUID format validation before any filesystem write
- Applied `basename` defense-in-depth to strip any directory components
- Scoped `session_id` as `local` to prevent leakage into the parent shell environment

### Argument Injection via `CLAUDE_CODE_PARAMS` (MEDIUM)

**Risk:** `CLAUDE_CODE_PARAMS` was a flat string, so multi-token values were word-split and re-evaluated, allowing argument injection through shell metacharacters.

**Fix:** Converted `CLAUDE_CODE_PARAMS` from a flat string to a bash array; execute Claude Code with `"${CLAUDE_CODE_PARAMS[@]}"` to prevent word-splitting injection.

---

## Upgrade Notes

This release does not affect the published `juniper-ml` meta-package's runtime dependencies. The `pip install juniper-ml[all]` install path is unchanged.

```bash
# Update via git (for tooling)
git pull origin main
git checkout v0.2.1

# Install the meta-package itself (unchanged)
pip install --upgrade juniper-ml==0.2.1
```

If you previously sourced `wake_the_claude.bash` from a fork or copied it locally, replace it with the v0.2.1 version to pick up the security fixes.

---

## Known Issues

None known at time of release.

---

## Version History

| Version | Date       | Description                                                                                |
| ------- | ---------- | ------------------------------------------------------------------------------------------ |
| 0.1.0   | 2026-02-22 | Initial `juniper` meta-package with optional dependency extras                             |
| 0.2.0   | 2026-02-27 | Renamed to `juniper-ml`, raised Python minimum to >=3.12, added publish workflow tweaks    |
| 0.2.1   | 2026-03-06 | `wake_the_claude.bash` launcher with session ID security fixes (path traversal, file write, arg injection) |

---

## Links

- [Full Changelog](../../CHANGELOG.md)
- [Security Remediation Plan](../history/SECURITY_REMEDIATION_PLAN.md)
- [Previous Release: v0.2.0](https://github.com/pcalnon/juniper-ml/releases/tag/v0.2.0)
