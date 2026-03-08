# PR #40 Security Remediation Plan

**Date:** 2026-03-08
**PR:** https://github.com/pcalnon/juniper-ml/pull/40
**Branch:** `tooling/claude_script` -> `main`
**Author:** Paul Calnon (remediation by Claude Code)

---

## Security Review Findings Validation

### Finding 1: HIGH — Unsafe Shell Argument Expansion

**Status:** CONFIRMED

**Evidence:**

The PR branch introduces two interrelated anti-patterns in `scripts/wake_the_claude.bash`:

1. **Single-string flag+value packing**: CLI flags and their values are concatenated into a single array element (e.g., `CLAUDE_CODE_PARAMS+=("${EFFORT_VALUE}")` where `EFFORT_VALUE="--effort high"`). This occurs for:
   - `--effort` (line ~459 on PR branch)
   - `--model` (line ~471 on PR branch)
   - `--session-id` when auto-generated (line ~434 on PR branch)
   - `--resume` omits the flag entirely and adds only the UUID (line ~408 on PR branch)

2. **Unquoted array expansion**: The invocation lines use `${CLAUDE_CODE_PARAMS[@]}` (without quotes) to force the shell to word-split the concatenated strings back into separate tokens:
   ```bash
   nohup "${CLAUDE_BIN}" ${CLAUDE_CODE_PARAMS[@]} >> "${NOHUP_LOG_FILE}" 2>&1 &
   "${CLAUDE_BIN}" ${CLAUDE_CODE_PARAMS[@]}
   ```

**Why this is dangerous:**

Unquoted expansion subjects every array element to:
- **Word splitting** (IFS-based): Intentional here, but brittle
- **Pathname/glob expansion**: Characters `*`, `?`, `[`, `]` in any parameter value (including prompt text) will be expanded by the shell to matching filenames in the current directory
- **Argument boundary injection**: A crafted value containing spaces would be split into multiple arguments

**Specific attack vectors:**
- A prompt containing `*` would expand to all files in the working directory
- A prompt containing `$(command)` in a context where it reaches unquoted expansion could execute arbitrary commands (mitigated by bash array semantics but still risky)
- The prompt wrapping `CLAUDE_CODE_PARAMS+=("\"${CLAUDE_CODE_PROMPT}\"")` adds literal quote characters that become part of the argument, not shell quoting

**On `main` branch (correct pattern):**
```bash
CLAUDE_CODE_PARAMS+=("${CLAUDE_RESUME_FLAGS}" "${SESSION_ID}")  # one token per element
nohup "${CLAUDE_BIN}" "${CLAUDE_CODE_PARAMS[@]}" >> ...          # quoted expansion
```

### Finding 2: MEDIUM — Default Launcher Disables Permission Boundary

**Status:** CONFIRMED

**Evidence:**

`scripts/default_interactive_session_claude_code.bash` (line 14 on PR branch):
```bash
"${SCRIPT_PATH}/wake_the_claude.bash" --id --worktree --dangerously-skip-permissions --effort high --prompt "${DEFAULT_PROMPT}"
```

The `cly` symlink at the repo root points directly to this script, making the most permissive mode the default invocation path.

**Risk:** Any user running `./cly` gets `--dangerously-skip-permissions` without explicit opt-in. This increases blast radius for prompt injection or operator mistakes.

### Finding 3: LOW — Committed Session ID Artifacts

**Status:** CONFIRMED

**Evidence:**

Three session ID files are committed on the PR branch:
- `scripts/21c5f66d-4b09-4bdd-b4d5-269dcbf68098.txt`
- `scripts/38c3bb49-33de-4081-b46a-47fca1c1dcac.txt`
- `scripts/9196be9d-4651-4b0e-93db-604429ca2dcf.txt`

These contain Claude Code session UUIDs. While the practical risk is low (sessions expire, and access requires authentication), publishing resumable identifiers in a public repo is poor security hygiene.

**Note:** The PR body itself acknowledges these should be removed before merge.

### Additional Issues Identified

1. **Commented-out code throughout**: Both scripts contain multiple blocks of commented-out code from debugging. This clutters the codebase and makes security review harder.

2. **Broken path parsing on PR branch**: The `if -f` check was commented out with `# fi` and connected to the `elif` below, creating a broken conditional structure where file paths that aren't directories fail immediately.

3. **Prompt wrapping adds literal quotes**: `CLAUDE_CODE_PARAMS+=("\"${CLAUDE_CODE_PROMPT}\"")` adds literal `"` characters to the prompt text, which the claude CLI would receive as part of the prompt content.

4. **Missing `--resume` flag in params**: The resume handler on the PR branch adds only the UUID without the `--resume` flag: `CLAUDE_CODE_PARAMS+=("${SESSION_ID}")`.

5. **Duplicate .gitignore entries**: `**/nohup*` appears twice in the added .gitignore lines.

---

## Remediation Plan

### Phase 1: Fix Security Vulnerabilities (HIGH priority)

#### Step 1.1: Restore proper array construction (one token per element)

**Tasks:**
- [ ] 1.1.1: Fix `--resume` handler — add flag and value as separate array elements: `CLAUDE_CODE_PARAMS+=("${CLAUDE_RESUME_FLAGS}" "${SESSION_ID}")`
- [ ] 1.1.2: Fix `--session-id` auto-generated handler — add flag and value separately: `CLAUDE_CODE_PARAMS+=("${CLAUDE_SESSION_ID_FLAGS}" "${generated_uuid}")`
- [ ] 1.1.3: Fix `--effort` handler — add flag and value separately: `CLAUDE_CODE_PARAMS+=("${CLAUDE_EFFORT_FLAGS}" "${1}")`
- [ ] 1.1.4: Fix `--model` handler — add flag and value separately: `CLAUDE_CODE_PARAMS+=("${CLAUDE_MODEL_FLAGS}" "${1}")`
- [ ] 1.1.5: Fix prompt appending — remove literal quote wrapping: `CLAUDE_CODE_PARAMS+=("${CLAUDE_CODE_PROMPT}")`

#### Step 1.2: Restore quoted array expansion at invocation

**Tasks:**
- [ ] 1.2.1: Change all invocation lines to use `"${CLAUDE_CODE_PARAMS[@]}"` (quoted) instead of `${CLAUDE_CODE_PARAMS[@]}` (unquoted)
- [ ] 1.2.2: Remove commented-out invocation lines

#### Step 1.3: Restore path file check

**Tasks:**
- [ ] 1.3.1: Restore the `if [[ -f "${PATH_NAME}" ]]` check that was commented out, properly closing the trailing-slash `if` block

### Phase 2: Fix Permission Boundary Default (MEDIUM priority)

#### Step 2.1: Remove `--dangerously-skip-permissions` from defaults

**Tasks:**
- [ ] 2.1.1: Remove `--dangerously-skip-permissions` from the default flags in `default_interactive_session_claude_code.bash`
- [ ] 2.1.2: Add support for an environment variable `CLAUDE_SKIP_PERMISSIONS=1` or a CLI passthrough flag to opt in explicitly
- [ ] 2.1.3: Remove commented-out code from `default_interactive_session_claude_code.bash`

### Phase 3: Remove Session ID Artifacts (LOW priority)

#### Step 3.1: Clean up committed session files

**Tasks:**
- [ ] 3.1.1: Ensure `.gitignore` covers `scripts/*.txt` session files (already partially addressed — `scripts/sessions/` is covered but not `scripts/*.txt`)
- [ ] 3.1.2: The three `.txt` files exist only on the PR branch and won't be merged since we're fixing the code on `main`. Verify they don't exist on `main`.

### Phase 4: Code Cleanup

#### Step 4.1: Remove commented-out code

**Tasks:**
- [ ] 4.1.1: Remove all commented-out code blocks in `wake_the_claude.bash`
- [ ] 4.1.2: Remove all commented-out code blocks in `default_interactive_session_claude_code.bash`

#### Step 4.2: Fix .gitignore duplicates

**Tasks:**
- [ ] 4.2.1: Remove duplicate `**/nohup*` entry

### Phase 5: Testing

#### Step 5.1: Write new tests for security fixes

**Tasks:**
- [ ] 5.1.1: Test that `--effort` flag and value are passed as separate arguments to claude
- [ ] 5.1.2: Test that `--model` flag and value are passed as separate arguments to claude
- [ ] 5.1.3: Test that prompt text containing glob characters (`*`, `?`) is passed as a single argument without expansion
- [ ] 5.1.4: Test that prompt text containing shell metacharacters is preserved as-is
- [ ] 5.1.5: Test that `--dangerously-skip-permissions` is not present in default interactive launcher unless explicitly opted in
- [ ] 5.1.6: Test that interactive mode (no `--print`) invokes claude in foreground with correct arguments
- [ ] 5.1.7: Test that headless mode invokes claude via nohup with correct arguments

#### Step 5.2: Run full regression suite

**Tasks:**
- [ ] 5.2.1: Run all 25 existing tests to verify no regressions
- [ ] 5.2.2: Run new security tests
- [ ] 5.2.3: Run `scripts/test_resume_file_safety.bash`

---

## Implementation Notes

All changes are made against the `main` branch (this worktree). The PR branch's changes that are correct (interactive/headless branching logic) will be re-implemented properly with quoted expansion. The changes that introduced the vulnerabilities will be corrected.

The key principle: **one CLI token per array element, always quoted expansion at invocation.**
