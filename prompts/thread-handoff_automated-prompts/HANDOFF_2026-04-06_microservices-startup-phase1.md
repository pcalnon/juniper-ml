# Thread Handoff: Microservices Startup Review -- Begin Phase 1

**Handoff Date**: 2026-04-06
**From Thread**: Microservices code review, analysis, and P0 script overhaul
**Worktree**: `vivid-herding-star`
**Branch**: `worktree-vivid-herding-star`

---

Continue the Juniper Microservices Startup/Shutdown automation project -- starting **Phase 1: Critical Fixes (P0)** from `notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md`.

## Prior Thread Completed

- **Comprehensive code review** of all startup/shutdown scripts, Dockerfiles, systemd units, compose files, and documentation across all 8 Juniper repos (juniper-data, juniper-cascor, juniper-canopy, juniper-deploy, juniper-ml, juniper-data-client, juniper-cascor-client, juniper-cascor-worker).
- **Analysis document written**: `notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` -- 700+ lines covering inventory, gap analysis, 3 design approaches with strengths/weaknesses/risks, and a 5-phase development roadmap.
- **Rewrote `util/juniper_plant_all.bash`**: Added `wait_for_health()` polling, `check_port_available()`, `validate_conda_env()`, `ensure_dir()`, per-service Python binaries (fixed S-05 bug), `set -euo pipefail`, `trap cleanup_on_failure ERR` (recursive-safe), configurable paths/timeouts via env vars, pre-flight checks for curl/ss/uvicorn.
- **Rewrote `util/juniper_chop_all.bash`**: Added `validate_pid()` via `/proc/<pid>/cmdline`, `graceful_stop()` with SIGTERM->SIGKILL fallback, fixed PID parsing (colon-delimited split), optional `KILL_WORKERS=1` mode, post-shutdown PID file cleanup.
- **Removed `util/get_cascor_dkdk.bash`** (incomplete dead code).
- **Committed and pushed** to branch `worktree-vivid-herding-star`. PR created: pcalnon/juniper-ml#103.
- **All 88 tests pass**, shellcheck clean, pre-commit hooks pass.

## Phase 1 Status: Largely Complete -- Needs Validation Update

The Phase 1 roadmap items from `notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` Section 10 are:

| Step | Task                                               | Status                          |
|------|----------------------------------------------------|---------------------------------|
| 1.1  | Add `wait_for_health()` to plant script            | **Done**                        |
| 1.2  | Add error handling (`set -euo pipefail`, `trap`)   | **Done**                        |
| 1.3  | Fix Python binary: per-service conda env paths     | **Done**                        |
| 1.4  | Add `validate_pid()` and `graceful_stop()` to chop | **Done**                        |
| 1.5  | Fix worker-not-found exit (make optional)          | **Done** (KILL_WORKERS env var) |
| 1.6  | Add SIGKILL fallback with configurable timeout     | **Done**                        |
| 1.7  | Add port availability check                        | **Done**                        |
| 1.8  | Add conda env validation                           | **Done**                        |
| 1.9  | Complete or remove `get_cascor_dkdk.bash`          | **Done** (removed)              |
| 1.10 | Fix quoting issues in PID file operations          | **Done**                        |

## Remaining Work

1. **Update the analysis document** (`notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md`):
   - Update Section 10 Phase 1 to mark all steps as completed with references to the implementing commit.
   - Update Sections 3.1 and 3.2 to reflect the new script behavior (they currently describe the OLD scripts).
   - Update Section 7.3 to note the conda env bug is now fixed.
   - Update the Gap Analysis (Section 8.1) to mark P0 items as resolved.
   - Stage and commit the updated document.

2. **Validation bugs identified during review** that should be addressed:
   - **`$LINENO` in functions**: Log messages inside functions (`check_port_available`, `wait_for_health`, etc.) report misleading line numbers. Consider using `${FUNCNAME[0]}` instead or accepting this bash limitation.
   - **`nohup` PID vs child PID**: `$!` captures the nohup wrapper PID, not the final uvicorn/python PID. If uvicorn forks workers, the recorded PID may not cover all children. Evaluate whether this is an actual problem for single-worker mode.
   - **`conda activate` stacking**: Three successive `conda activate` calls stack environments. Consider adding `conda deactivate` between each, or restructuring to use subshells.
   - These are known trade-offs documented by the validation agent -- decide whether to fix or document as accepted limitations.

3. **Begin Phase 2** if time permits (systemd units for juniper-data and juniper-cascor). See Section 10 Phase 2 in the analysis document.

## Key Context

- **Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/vivid-herding-star`
- **Branch**: `worktree-vivid-herding-star` (pushed, tracking `origin/worktree-vivid-herding-star`)
- **PR**: pcalnon/juniper-ml#103 (open, targeting `main`)
- **Unstaged change**: `notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` has a pre-commit auto-format diff (trailing whitespace). Stage and commit as part of the document update.
- **The analysis document describes the OLD scripts in sections 3.1 and 3.2**. The new scripts are already committed. Update the document to match reality.
- **Approach A (Incremental Fix) was chosen** as the recommended approach (Section 9.4). Do not switch approaches.
- **Phase 1 P0 items are all implemented** but the document hasn't been updated to reflect this.

## Verification Commands

```bash
# Verify worktree state
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/vivid-herding-star
git status
git log --oneline -3

# Verify tests pass
python3 -m unittest -v tests/test_wake_the_claude.py tests/test_check_doc_links.py tests/test_worktree_cleanup.py

# Verify scripts pass shellcheck
shellcheck util/juniper_plant_all.bash util/juniper_chop_all.bash

# Verify pre-commit
pre-commit run --files util/juniper_plant_all.bash util/juniper_chop_all.bash

# Read the analysis document
cat notes/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md
```
