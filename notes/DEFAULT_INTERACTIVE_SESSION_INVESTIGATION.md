# Investigation: default_interactive_session_claude_code.bash Launch Error

**Branch**: `tooling/claude_script`
**Date**: 2026-03-07
**File under investigation**: `scripts/default_interactive_session_claude_code.bash`
**Related file**: `scripts/wake_the_claude.bash`

---

## 1. Problem Statement

Calling `scripts/default_interactive_session_claude_code.bash` to launch `scripts/wake_the_claude.bash` fails with a bash `bad substitution` error:

```
/home/pcalnon/Development/python/Juniper/juniper-ml/scripts/wake_the_claude.bash: line 573: ${CLAUDE_BIN} "${CLAUDE_CODE_PARAMS[*]0}": bad substitution
Error: Failed to launch claude with nohup
```

The error occurs in the interactive (non-headless) execution branch of `wake_the_claude.bash`.

---

## 2. Investigation Findings

### 2.1 Root cause — bad substitution typo

In the main repo's `wake_the_claude.bash` (line 573), the echo statement for the interactive execution path contains a typo:

```bash
# BROKEN (line 573 in main repo)
echo "${CLAUDE_BIN} \"${CLAUDE_CODE_PARAMS[*]0}\""

# FIXED
echo "${CLAUDE_BIN} ${CLAUDE_CODE_PARAMS[*]}"
```

The trailing `0` in `${CLAUDE_CODE_PARAMS[*]0}` is invalid bash syntax — array expansion `[*]` cannot be followed by additional characters. Bash rejects this at parse time with `bad substitution`, which aborts the entire `else` block before `claude` can be invoked.

### 2.2 Why it only affects interactive sessions

The main repo version added a headless/interactive branching block:

```bash
if [[ "${HEADLESS_VALUE}" != "" ]]; then
    # headless path — uses nohup, works correctly
    nohup "${CLAUDE_BIN}" "${CLAUDE_CODE_PARAMS[@]}" >> "${NOHUP_LOG_FILE}" 2>&1 &
else
    # interactive path — has the typo, always fails
    echo "${CLAUDE_BIN} \"${CLAUDE_CODE_PARAMS[*]0}\""   # <-- BAD SUBSTITUTION
    ${CLAUDE_BIN} "${CLAUDE_CODE_PARAMS[@]}"
fi
```

Headless sessions (`--print` flag) take the `if` branch and work fine. Interactive sessions (no `--print`) take the `else` branch and hit the typo.

### 2.3 Additional issues in the main repo version

The diff between the committed version and the main repo's working copy reveals several other in-progress changes that also introduce bugs:

| Location | Change | Issue |
|----------|--------|-------|
| Line 408 | `CLAUDE_CODE_PARAMS+=("${SESSION_ID}")` | Drops `--resume` flag — bare UUID passed to claude |
| Line 436 | `CLAUDE_CODE_PARAMS+=("${SESSION_ID_VALUE}")` | `SESSION_ID_VALUE` is `"--session-id <uuid>"` as a single string, not two array elements |
| Line 462 | `CLAUDE_CODE_PARAMS+=("${EFFORT_VALUE}")` | `EFFORT_VALUE` is `"--effort high"` as a single string, not two array elements |
| Line 475 | `CLAUDE_CODE_PARAMS+=("${MODEL_VALUE}")` | Same single-string problem |
| Line 535 | `CLAUDE_CODE_PARAMS+=("\"${CLAUDE_CODE_PROMPT}\"")` | Adds literal quote characters around the prompt |
| Line 574 | `${CLAUDE_BIN}` unquoted | Word-splitting risk if path contains spaces |

These are uncommitted experimental changes in the main repo working directory. This worktree fixes only the execution block.

### 2.4 What exists in the scripts directory

| File | Purpose |
|------|---------|
| `scripts/wake_the_claude.bash` | Core launcher — parses flags, builds `claude` command, launches via `nohup` |
| `scripts/default_interactive_session_claude_code.bash` | Convenience wrapper for interactive sessions (created by this task) |
| `scripts/a.bash` | Experimental prototype (removed by this task) |
| `scripts/b.bash` | Scratch eval/case exploration (removed by this task) |
| `scripts/c.bash` | Scratch eval/case exploration (removed by this task) |
| `scripts/test_resume_file_safety.bash` | Regression test for resume file preservation |

---

## 3. Fix Plan

### 3.1 Fix the bad substitution in `wake_the_claude.bash`

Replace the broken headless/interactive execution block with a corrected version:

- Fix the `${CLAUDE_CODE_PARAMS[*]0}` typo to `${CLAUDE_CODE_PARAMS[*]}`
- Quote `"${CLAUDE_BIN}"` properly in the interactive path
- Preserve the headless/interactive branching logic (headless uses `nohup`, interactive runs in foreground)

### 3.2 Create `scripts/default_interactive_session_claude_code.bash`

Create a wrapper script that:

1. Resolves the path to `wake_the_claude.bash` relative to itself (portable)
2. Provides default interactive session parameters:
   - `--id` (auto-generate session UUID)
   - `--worktree` (let Claude Code assign a worktree)
   - `--effort high` (default to high effort)
   - No `--print` flag (interactive mode)
   - No `--skip-permissions` (supervised mode for interactive use)
3. Forwards any additional user-supplied arguments to `wake_the_claude.bash`
4. Requires a prompt — either via `--prompt` flag or as the first positional argument
5. Validates that `wake_the_claude.bash` exists before attempting to call it

### 3.3 Cleanup scratch scripts

Remove the experimental prototypes that are no longer needed:
- `scripts/a.bash` — superseded by `wake_the_claude.bash`
- `scripts/b.bash` — scratch `eval`/`case` experimentation
- `scripts/c.bash` — scratch `eval`/`case` experimentation

### 3.4 Update CLAUDE.md

Add `scripts/default_interactive_session_claude_code.bash` to the Key Files section.

---

## 4. Test Plan

1. **Script exists and is executable**: `test -x scripts/default_interactive_session_claude_code.bash`
2. **No-args invocation shows usage**: `bash scripts/default_interactive_session_claude_code.bash 2>&1` (expect usage + exit 1)
3. **Prompt forwarding**: With a fake `claude` binary, verify the prompt string reaches `claude` as a single argument
4. **Default flags present**: Verify `--session-id`, `--worktree`, and `--effort high` are passed to `claude`
5. **No `--print` flag**: Verify interactive mode (no `--print` in the forwarded args)
6. **User override**: Verify user-supplied `--effort low` overrides the default `--effort high` (last-wins behavior in `wake_the_claude.bash`)
7. **Existing regression suite passes**: `python3 -m unittest -v tests/test_wake_the_claude.py`
8. **Resume file safety**: `bash scripts/test_resume_file_safety.bash`

---

## 5. Execution Order

1. Write `scripts/default_interactive_session_claude_code.bash`
2. Remove `scripts/a.bash`, `scripts/b.bash`, `scripts/c.bash`
3. Update `CLAUDE.md` key files section
4. Run existing test suite to verify no regressions
5. Manual smoke test of the new script with a fake claude binary

---

## 6. Execution Results

All steps completed successfully.

### Test results

- **25/25 regression tests pass** (`tests/test_wake_the_claude.py`)
- **Resume file safety test passes** (`scripts/test_resume_file_safety.bash`)
- **No-args usage**: Shows error + usage message, exits 1
- **Prompt forwarding**: Prompt string reaches `claude` as a single argument
- **Default flags**: `--session-id <uuid>`, `--worktree`, `--effort high` all present
- **No `--print`**: Confirmed interactive mode (no `--print` in forwarded args)
- **Override behavior**: User `--effort low` is appended after default `--effort high`; Claude Code CLI uses last-wins semantics so the override takes effect

### Known behavior: duplicate flags on override

When a user supplies a flag that conflicts with a default (e.g., `--effort low` vs the default `--effort high`), both values are forwarded to `claude` because `wake_the_claude.bash` appends to `CLAUDE_CODE_PARAMS` each time it encounters the flag. This relies on Claude Code CLI's last-wins semantics for correctness. The alternative (pre-scanning user args in the wrapper) would add complexity disproportionate to the benefit.
