# Fix Roadmap: eval Removal and debug_log Ordering

**Branch**: `bugfix/eval-and-debug-log-ordering`
**Parent**: `bugfix/session-id-validation` (commit `77d609e`)
**File**: `scripts/wake_the_claude.bash`

---

## Issue 1: `matches_pattern()` Uses `eval` (Line 92)

### Root Cause

Bash `case` patterns do not expand variables — pattern content is treated literally. To support `|`-delimited pattern variables (e.g., `"-u | --usage"`), the script injects the pattern into a `case` statement via `eval`. While the pattern values currently come from internal constants (lines 43-56), `eval` is a latent RCE vector if any pattern variable were ever sourced from external input.

### Fix Approach

Replace the `eval "case ..."` with an IFS-based loop that splits the pattern on `" | "` and compares each candidate with `==`:

```bash
function matches_pattern() {
    local ip_value="$1"
    local pattern="$2"
    local candidate
    while IFS= read -r -d '|' candidate || [[ -n "$candidate" ]]; do
        candidate="${candidate# }"
        candidate="${candidate% }"
        [[ "$ip_value" == "$candidate" ]] && return 0
    done <<< "$pattern"
    return 1
}
```

This eliminates `eval` entirely while preserving the exact same matching behavior for all 15 call sites (lines 285-453).

### Validation

- All 15 `matches_pattern` call sites pass `${*_FLAGS}` variables defined on lines 43-56
- Pattern format is consistent: `"-flag1 | --long-flag1 | --long-flag2"` with ` | ` separators
- No call site passes user input directly as the pattern argument

---

## Issue 2: `debug_log` Called Before Definition (Lines 21, 32, 41, 62, 66)

### Root Cause

`debug_log()` is defined on line 73, but called on lines 21, 32, 41, 62, and 66 — all in the constants/flags section above the function definitions block. When bash encounters an undefined function, it emits `debug_log: command not found` to stderr. This noise breaks tests that assert on stderr content (e.g., `test_session_id_save_rejects_symlink_target` asserts `"symlink" in result.stderr`).

### Fix Approach

Move `debug_log()` and `redact_uuid()` definitions to immediately after the globals section (after line 15), before the first `debug_log` call on line 21. `redact_uuid()` is moved alongside because `debug_log` doesn't depend on it but they form a logical pair, and `redact_uuid` is also called from multiple functions that come later.

The `matches_pattern()`, `is_valid_uuid()`, `save_session_id()`, `retrieve_session_id()`, `validate_session_id()`, and `usage()` functions remain in the existing function definitions block (currently starting at line 72), since they are not called until after that block.

### Validation

- Lines 21, 32, 41, 62, 66: all call `debug_log` — will now find it defined above
- `redact_uuid` first called inside `save_session_id` (line 126) and `validate_session_id` (line 142) — both after the definitions block, no ordering issue currently, but moving it early is harmless and consistent
- No other functions are called before their definition

---

## Test Plan

1. Run existing test suite: `python -m pytest tests/test_wake_the_claude.py -v`
2. Verify zero `command not found` on stderr: `bash scripts/wake_the_claude.bash -u 2>&1 | grep "command not found"` (expect empty)
3. Verify `--usage` flag works: `bash scripts/wake_the_claude.bash -u` (expect usage output + exit 1)
4. Verify `--help` flag works: `bash scripts/wake_the_claude.bash -h` (expect usage output + exit 0)
5. Verify debug mode: `WTC_DEBUG=1 bash scripts/wake_the_claude.bash -u 2>&1` (expect debug output without errors)
6. Verify invalid flag: `bash scripts/wake_the_claude.bash --bogus 2>&1` (expect error + usage)
7. Verify no `eval` remains: `grep 'eval' scripts/wake_the_claude.bash` (expect empty)

---

## Commit Plan

Single commit covering both fixes since they affect the same file and are both pre-existing bugs from the same section of code.
