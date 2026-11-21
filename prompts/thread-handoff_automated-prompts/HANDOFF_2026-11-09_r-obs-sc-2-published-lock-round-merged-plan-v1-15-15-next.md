# Thread Handoff — R-OBS-SC-2 published, its second lock round merged; plan v1.15.15 next

**Date**: 2026-11-09 UTC (host clock is local time, UTC−6)
**Session**: `e21d1414`, the Linux host, worktree `.claude/worktrees/bright-giggling-metcalfe` (branch `worktree-bright-giggling-metcalfe`, HEAD `4bae7520` = `origin/main` at 09:20Z, nothing committed). Every file this session made is **uncommitted in that worktree**: a session in another worktree must `cp` them in, because the isolation guard refuses `git -C` into a sibling. Commits go only through `util/open_signed_pr.py` / `util/push_signed_commit.py` (signed API commits).
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-09_r-obs-sc-2-lock-round-prepped-probe-ruled-gates-pending.md` (session `b4208d23`; ported here byte-identical, sha256 `b0074c2a…`, from worktree `enchanted-foraging-rocket`). Its steps 1, 2 and 4 are DONE; steps 3 and 5 carry forward.

## Goal

Write plan v1.15.15 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`: R-OBS-SC-2 end to end (Wave 1 "Security delivery", plan L817–826: steps 1, 3 and 4 are done; step 5 is the owner's). Step 2's P3 D-03 has no recorded answer beyond the owner's 11-08 "Approve both cuts", so read L1122 before calling it done. Commit the three handoffs and the session tools listed under Git state in the same PR.

**Approvals are per-session** (`feedback_headless_merge_approval_policy.md`). This session held "approval granted for merge and other PR actions" (the user's turn, 2026-11-09 ~09:19Z). **Re-ask in yours.** Paul approves every `pypi` gate.

## Completed this session

- **Step 1, both releases published.** The session sent AskUserQuestion at 09:29:35Z, and the owner answered "Approving now: wait" at 09:49:26Z (transcript timestamps). The approvals are the `pypi` deployments leaving `waiting` (`gh api repos/pcalnon/juniper-ml/deployments/<id>/statuses`):
  - **observability 0.4.2** (run 42500706778, deployment 7638679639): queued at 09:51:22Z; `Publish to PyPI` ran 09:51:24–09:51:39Z; files uploaded at 09:51:35Z.
  - **service-core 0.7.2** (run 42499466753, deployment 7638506538): queued at 09:52:23Z; ran 09:52:25–09:52:50Z; files uploaded at 09:52:45Z.

  Both wheels are `py3-none-any`. The times in `tmp/lr2/gates-watch.log` (written by `util/ad-hoc/2026-11-09_wait_for_pypi_gates.py`; 200 first seen at 09:52:19Z and 09:53:35Z) are the watcher's 30-second polls, not the events themselves.
- **Step 2, the second lock round: four PRs, each moving exactly `juniper-observability` 0.4.1→0.4.2 and `juniper-service-core` 0.7.1→0.7.2**, plus a CHANGELOG `[Unreleased]` `### Security` entry. Each is one GitHub-signed commit (verified) on branch `deps/r-obs-sc-2-lock-round-2`. `pyproject.toml` is untouched in every one: floors go in each repo's release PR. That departs from recurrence#199, which moved recurrence's floors in its lock PR; recurrence#233's body says so.

  | PR | Locks | Merged |
  | --- | --- | --- |
  | data#525 | `requirements.lock` (69 pins) | 10:07:34Z, `272ff615` |
  | cascor#748 | `requirements.lock` (73), `requirements-cpu.lock` (54, header kept) | 10:14:23Z, `7640d420` |
  | canopy#806 | `requirements.lock` (60) | 10:21:36Z, `b4b01904` |
  | recurrence#233 | `juniper-recurrence/requirements.lock` (31, dated `REGENERATED 2026-11-09, TARGETED` header paragraph) | 10:01:54Z, `857efbc5` |

- **The per-lock probe (owner ruling 00:24:20Z), before → after**, all on the same `main` SHAs (data `4f04fc8d`, cascor `f3dfee8c`, canopy `63a2f3d7`, recurrence `3529dfd9`, re-resolved unchanged before each PR opened). P3-07's wire probe: data, cascor and canopy **LEAK (6 items) → CLEAN (0)**; recurrence N/A (no `sentry-sdk` in its lock). Suites unchanged: data 247, cascor 290, canopy 454, recurrence 364 (all `tests/`, which holds W1.14's tests from recurrence#203). `pin_drift` 0 everywhere. A constraint-mode replay reproduced all five locks before and after the refresh. For the three `requirements.lock` files (data, cascor, canopy) it was CI's own command. Cascor's `requirements-cpu.lock` and recurrence's lock used their header commands: no CI gate checks either one, except CI's check that the CPU lock names every image dependency. Cascor's probe venv was built from `requirements-cpu.lock` plus CPU torch, so its `requirements.lock` was replayed but not probed. cascor#748's image builds (linux/amd64 and linux/arm64) passed on the new CPU lock. Recurrence's arm64 pre-flight: OK, 31 pins. Each PR body carries the table, the telemetry record and the sentence saying it is NOT S0.11's relay run.
- **What each pin changes** (stated in each PR): observability 0.4.2 fixes the live Sentry path in data, cascor and canopy. Under 0.4.1 the three headers `Sec-WebSocket-Protocol`, `X-CSRF-Token` and `X-XSRF-Token` went out in every event and transaction. cascor samples every transaction (`_LOGGER_SENTRY_TRACES_SAMPLE_RATE` 1.0), and canopy's WebSocket key rides `Sec-WebSocket-Protocol` when its opt-in `ws_auth_enabled` is on. Only data can turn `send_pii` on, so the `X-API-Key` and cookie paths were reachable only there. service-core 0.7.2's `Retry-After` round-up reaches **recurrence only** (its `SecurityMiddleware` builds the default throttle). data, cascor and canopy import only `enforce_auth_posture` (and canopy `AuthPostureError` and `enforce_dependency_floors`), so for them the pin is consistency.
- **Step 4**: memory `project_recurrence_equities_p0_arc_2026-10-04.md` updated (description and top block).

## Remaining work, in order

1. **Plan v1.15.15**: an ad-hoc writer modelled on `util/ad-hoc/2026-11-07_consolidated_plan_v1_15_14_juniper_ml_0_11_4_published.py` (anchor edits, idempotent, `--check`, no new line over 512 characters). Record:
   - P3-07 (ml#2523), the carry (ml#2524), the proposals (ml#2525, ml#2526) and the cuts.
   - Both gates' approval and publish times (above, the deployment-status times), and rounds 2 and 3's findings (from the 11-08 handoff).
   - The 00:24:20Z ruling, and the four lock PRs with their before/after.
   - Security step 4 done by the per-lock probe in place of S0.11's run, which is still unwritten (A1).
   - **§9's lock gate (L1315) is met for each consumer's next image release. No merged lock reaches a running image until that repository cuts one.**
     - R-DATA-2 (data 0.18.0) is owed; its lock gate (L627, L863) is now met.
     - R-CASCOR (L978) still has its other gates. It was "bypassed in part" by 0.12.0, and 0.12.0 and 0.13.0 shipped with observability 0.4.1, so a new cascor cut is owed.
     - R-CANOPY-A shipped as canopy 0.9.0 before R-OBS-SC-2 existed (L975, L1036), so a second canopy cut is owed.
     - Recurrence's next release carries it too.
   - The follow-ups (step 2 below).

   Check §2, §5 (the R-OBS-SC-2 row, L974; R-CASCOR, L978), §9 (cross-path dependencies, L1315–1318), Wave 1's "Security delivery" and the exit list (L905) for every statement this moves. Commit the three handoffs and the tools below in the same PR.
2. **Owner items to surface (report, do not act)**:
   - juniper-ml's `[tools]` floor `juniper-observability>=0.4.2` needs meta 0.11.5.
   - New image cuts are owed before any running image carries the fix: data (R-DATA-2), cascor, canopy and recurrence (see step 1).
   - The forks' `RateLimiter` still truncates with no floor (data `juniper_data/api/security.py:250/:254`, cascor `src/api/security.py:229/:233`, canopy `src/security.py:270/:274`), so APD-SVCCORE-004's `Retry-After: 0` is live in all three, with no register row. Separately, data `:427` and cascor `:386` keep `FailedAuthThrottle`'s `max(1, int(...))` round-down (the wait comes out a second short), which 0.7.2 fixed only in service-core.
   - The 0.4.3 design (query strings, including canopy's `?api_key=`; Sentry Logs; bodies; breadcrumbs; exception values; list-shaped headers).
   - The `/tmp/juniper-e2e/canopy-805{2,3}.log` writer.
   - S0.11's relay tests are still unwritten (A1).
   - cascor and canopy run FastAPI's default telemetry: inert while no OTel SDK is locked, but data#454's opt-out is missing in both.
   - Security step 5: the trio's environment upgrade (XC-SENTRY) is unblocked. The restart is not: it waits for a recorded pass of S0.11's relay tests (plan L823–824), which are unwritten. Whether the per-lock probe may stand in there too is the owner's question.

## Corrections to the predecessor

- Its owner item "The forks' truncating `RateLimiter`/`FailedAuthThrottle` (… `:427` … `:386` …) leave APD-SVCCORE-004's `Retry-After: 0` live" merges two defects. `Retry-After: 0` comes only from the forks' `RateLimiter` lines. Data `:427` and cascor `:386` are `max(1, int(...))`, which cannot return 0: they are the round-down that service-core 0.7.2 fixed. The 11-08 handoff stated this correctly; the 11-09 condensation lost it.
- An independent fact-check (one agent; 2 MAJOR, 7 MINOR) checked this document, and every finding is applied above. The two MAJORs were the R-CASCOR / R-CANOPY-A "prerequisite met" claim and "CI's replay reproduced all five locks".

## Traps (new this session, plus the carried ones)

- **The CLAUDE.md injection fires on a plain `sed`/`cat` too**, not only on Read: reading cascor's `ci.yml` under `tmp/lr2/src/` pulled in its whole `AGENTS.md`. Use a script that prints only what you need.
- **`safe_merge.py` can exit 0 without a `MERGED` line**: its armed auto-merge net merged recurrence#233 while it was re-syncing, so its own update-branch call got a 422. Read the PR's `state` yourself.
- The sandbox refuses `for` loops and heredocs that mention `git`, `$VAR`-built `sed`/`python` programs, and complex pipelines. Write a script in `util/ad-hoc/`.
- `grep` is ugrep and honours `.gitignore`, so a recursive grep skips `tmp/`; use `command grep`. Never type `\uXXXX` escapes through Write/Edit; build them with `chr()`.
- A whole-file upload from a stale tree reverts what merged since: re-resolve `main` against the tree's `.sha` just before `open_signed_pr.py`, then check the PR's files and its `+/-` counts.

## Verification commands

```bash
cd ~/Development/python/Juniper/juniper-ml/.claude/worktrees/bright-giggling-metcalfe   # or cp the files below from it
git fetch origin && git log -1 --format='%h %s' origin/main            # 4bae7520 or later
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-observability/0.4.2/json   # 200
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-service-core/0.7.2/json    # 200
gh pr view 525 --repo pcalnon/juniper-data --json state,mergeCommit
gh pr view 748 --repo pcalnon/juniper-cascor --json state,mergeCommit
gh pr view 806 --repo pcalnon/juniper-canopy --json state,mergeCommit
gh pr view 233 --repo pcalnon/juniper-recurrence --json state,mergeCommit
```

Run each `gh` and `curl` as its own command.

## Git state and files

Worktree `bright-giggling-metcalfe` at `4bae7520`, nothing staged. Uncommitted, all new:

- From session `b4208d23` (ported byte-identical): `util/ad-hoc/2026-11-09_lock_round_2_{fetch_consumers,facts,env_record,probe}.py`, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_r-obs-sc-2-cut-pypi-gates-lock-round-next.md`, and `…HANDOFF_2026-11-09_r-obs-sc-2-lock-round-prepped-probe-ruled-gates-pending.md`.
- This session's: `util/ad-hoc/2026-11-09_lock_round_2_run_probes.py` (the four recorded invocations; `--verify-against` mutation-checked), `…_lock_round_2_refresh.py` (the five recipes), `…_lock_round_2_changelog_insert.py`, `…_lock_round_2_tested_section.py`, `…_wait_for_pypi_gates.py`, and this file.

Ignored `tmp/lr2/` holds the trees (`src/`, each `.sha` and `.sha.before`), `facts-*.txt`, `runs/` (before and after, with their venvs), `runs-*-{before,after}.out`, `gates-watch.log` and `drafts/` (the PR bodies, CHANGELOG entries and commit bodies as sent). Keep it, and `enchanted-foraging-rocket`'s and `fizzy-enchanting-deer`'s `tmp/`, until v1.15.15 merges (retention rule). `witty-tickling-phoenix`'s `tmp/` holds P3-07's pre-port draft. It is superseded, but check it before any removal.

## Documents referenced / changed

- **Referenced**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (Security delivery L817–826; L627, L863, L905, L974, L1315–1318); `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md`; `notes/releases/RELEASE_NOTES_juniper-service-core_v0.7.2.md`; the two predecessor handoffs named above; data#478, cascor#711, canopy#739, recurrence#199, recurrence#203.
- **Changed**: in this repo, the twelve files listed under Git state (nine ad-hoc tools and three handoffs). In the consumers (merged): data `requirements.lock` and `CHANGELOG.md`; cascor `requirements.lock`, `requirements-cpu.lock` and `CHANGELOG.md`; canopy `requirements.lock` and `CHANGELOG.md`; recurrence `juniper-recurrence/requirements.lock` and `juniper-recurrence/CHANGELOG.md`. Outside the repos: the memory file named above.
