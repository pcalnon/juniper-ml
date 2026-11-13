# Handoff: R-OBS-SC-2 follow-ups -- five PRs merged; guard + register, 0.11.5, plan v1.15.16 and round 2 remain

**Written**: 2026-11-13 01:15Z by session `6e3bdef0` (`r-obs-sc-2-follow-ups-four-ruled-four-open`), which ends
with this file. The filename keeps its first, checkpoint-time slug because juniper-ml#2555's description cites it.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md`
(the owner's four rulings verbatim, the seven steps, and round 2's four questions verbatim; read it first).
**Working record, item by item**: `tmp/lps/fixpass_r1.md` in the worktree named under "Git status" (gitignored;
every review finding and what was done about it; keep it until plan v1.15.16 has merged).

## Goal

Continue the R-OBS-SC-2 follow-ups. Rulings 2 (first half), 3 (two of three forks) and 4 are carried out and on
`main`. What remains: the juniper-ml guard and register PR for `APD-ECO-016` (after juniper-data's fix lands), the
0.11.5 cut (owner's go-ahead first), plan v1.15.16, and the re-ask of round 2's four questions.

## Completed so far (all merged on 2026-11-13 UTC, each one GitHub-signed commit, squash-merged with `util/safe_merge.py`)

| PR | What | Merge |
| --- | --- | --- |
| juniper-ml#2555 | `[tools]` floors `juniper-observability>=0.4.2`, `juniper-service-core>=0.7.2,<0.8.0`; 22 edits by `util/ad-hoc/2026-11-12_tools_floors_observability_0_4_2_service_core_0_7_2.py`; five tools | `26ea0ecb`, 00:49Z |
| juniper-cascor#755 | `create_app` opts out of FastAPI's native telemetry (ruling 4) | `5834709a`, 00:27Z |
| juniper-canopy#816 | the app opts out of FastAPI's native telemetry (ruling 4) | `b9417b2f`, 00:34Z |
| juniper-cascor#757 | `Retry-After` / `X-RateLimit-Reset` round up, never 0; 44-test module (ruling 3) | `66b39a5c`, 01:07Z |
| juniper-canopy#817 | the same for canopy's limiter; 30-test module (ruling 3) | `55ac2168`, 01:02Z |

- **Checked in CI, not only locally**: #755's unit lane shows 16 dots for `test_api_app.py` and `5993 passed`;
  #816's shows 24 + 15 dots for `test_main_import_and_lifespan.py` and `8350 passed, 16 skipped` (both on FastAPI
  0.162.5, so the ported test ran rather than skipped; each PR carries a comment with the run and job ids). #757's
  lane ends `6050 passed`; #817's `8380 passed, 16 skipped`.
- **Validation**: two rounds, six independent reviewers; every finding applied or recorded. Evidence:
  `tmp/lps/validation/round1/lane{A,B,C,D}/`, `tmp/lps/validation/round2/{A,B}/`.
- **Ruling 1** (consumers' floors move in each next release PR): nothing to open, by the ruling.
- **Tools now on `main`** (`util/ad-hoc/2026-11-12_*.py`): `run_with_blank_sentry_dsns`,
  `fastapi_telemetry_opt_out_mutation_check`, `fork_retry_after_round_up_mutation_check`, `upload_set_hashes`,
  `rehome_worktree_edits_on_new_main`.

## Remaining work

1. **Guard and register PR in juniper-ml** -- only after juniper-data's `Retry-After` fix is on `main`. That fix is
   the Cursor flood-4 arc's carrier (session `flood4-session5-seven-more-landed-queue-and-decisions-pending`), not
   open at 01:15Z; it said it will message this session's name with the PR number at open and at merge, so ask it.
   - The guard is written and uncommitted in the worktree: `tests/test_service_fork_drift.py` gains
     `retry-after-rounds-up` (register ids `APD-ECO-016`, `APD-SVCCORE-004`; 11 scoped sites in 4 copies);
     `util/ad-hoc/2026-11-12_retry_after_guard_mutation_check.py` checks it. Re-run that script against an
     ecosystem root assembled from each repository's `main` (`--main-ref main`, `--prefix REPO=<the fix's parent
     commit>`: the parents of `66b39a5c`, `55ac2168` and juniper-data's fix).
   - File `APD-ECO-016` already FIXED in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`: the five
     touches, §2.3's table and counts, §4.2, §4.3, §4.9, §5.1 (26 anchors located by `tmp/lps/register_anchor_probe.py`;
     re-run it, `main` has moved; template juniper-ml#2365, `tmp/lps/ml2365.diff`). Update `docs/REFERENCE.md`'s
     fork-drift entry ("all eight guards" becomes nine; canopy now forks `RateLimiter`). Run
     `util/ad-hoc/register_open_set.py` and `util/ad-hoc/register_status_crosscheck.py`. After the merge dispatch
     Docs Full Check, the only place the cross-repo arms run.
2. **juniper-ml 0.11.5** -- ask the owner for the go-ahead first (asked twice on 2026-11-12, unanswered). Then
   §11 of `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`, as a patch (set the manifest to
   patch: the detector reads `[Unreleased]` as a minor). **In the proposal PR, remove by hand the two clauses
   #2555 added to `docs/REFERENCE.md` line 184**: "except the `juniper-observability` cell: it holds `main`'s
   floor, `>=0.4.2` (unreleased; first in juniper-ml 0.11.5), where the published 0.11.4 declares `>=0.4.1`" and
   "; `main` raises it to `>=0.7.2,<0.8.0` (unreleased; first in juniper-ml 0.11.5)". Keep line 184 one physical
   line. **If the cut is not a 0.11.x**, also put the `0.11.x` row's `juniper-observability` cell back to
   `>=0.4.1`. No test notices either omission. Stop at the `pypi` gate: the owner approves it.
3. **Plan v1.15.16** (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`; writer script
   with `--check`, ID coverage 381 of 381, two independent reviewers, a new dated re-probe). Record the four
   rulings, the five PRs, round 2's outcome, and what the reviews found outside the rulings (the list "For the
   handoff and plan v1.15.16" in `tmp/lps/fixpass_r1.md`):
   - juniper-service-core's app factory passes no `telemetry=`, and juniper-recurrence builds with it (its lock is
     at FastAPI 0.141.1; a full re-resolution crosses 0.142);
   - a telemetry test that does not skip below FastAPI 0.142 (`app.extra["telemetry"]`), as one change for
     juniper-data, juniper-cascor and juniper-canopy (both fork PR bodies say it goes into this plan);
   - a wall clock stepped backwards makes the wait read above the window in all four limiter copies, and canopy's
     `_evict_expired` then answers differently from the others;
   - juniper-cascor's `docs/api/JUNIPER_CASCOR_API_REFERENCE.md` "Exempt paths" row still lists `/docs`,
     `/openapi.json`, `/redoc`; the code exempts only health and `/metrics`;
   - the WebSocket control `retry_after` and `HandshakeCooldown.get_block_remaining` read `0.0` under 50 ms, in
     juniper-cascor and in juniper-service-core;
   - `tests/test_release_train_registry.py` walks the checkout for `pyproject.toml` without skipping `tmp/` (3
     tests fail locally whenever `tmp/` holds a repository copy);
   - juniper-ml#2507's row test makes the compatibility row track `pyproject.toml` between a floor PR and its
     release, and nothing checks that the paragraph says so (flood-4 is taking this to the owner);
   - juniper-service-core's next release is 0.8.0, so every `<0.8.0` cap has to widen first.
   **Read first**: `main` gained a draft v2 of the plan on 2026-11-12 (juniper-ml#2550, "a draft re-plan, not
   validated"); settle with the owner which document takes the record.
4. **Round 2**: ask the owner what to clarify, then re-ask the four questions (verbatim in the predecessor).
5. **Housekeeping**: remove the four merged fork worktrees and, after flood-4's fix merges, the juniper-data one
   (each `tmp/` checked under the retention rule first); this worktree after the guard PR merges.

## Key context

- **Bases move, often.** Before any whole-file upload: `python3 util/ad-hoc/2026-11-12_upload_set_hashes.py --fetch
  --record FILE --set NAME=WORKTREE:paths` (it refuses a worktree whose HEAD is not `origin/main`); on a refusal,
  `util/ad-hoc/2026-11-12_rehome_worktree_edits_on_new_main.py --worktree DIR`, re-run that set's tests, record.
  A PR that goes BEHIND: `gh api -X PUT repos/pcalnon/<repo>/pulls/N/update-branch`, then re-run `safe_merge`
  (it refuses when the head moved under it).
- **juniper-data is flood-4's.** This arc's juniper-data worktree was never opened; flood-4's carrier keeps
  `_seconds_until_reset` and the `max(1, math.ceil(` expressions byte for byte, which is what the guard matches.
- **Blank the six Sentry DSN variables for every test run** (`util/ad-hoc/2026-11-12_run_with_blank_sentry_dsns.py`;
  never through an interactive shell). **A mutation check writes over the real source file**: never upload from a
  worktree while one runs in it.
- **Sub-agents cannot write report files** here: brief them to return the report as their final message. Two
  credit outages (6 h and 14 h) killed reviewers mid-run; `SendMessage` to the agent id resumed them.
- `Verify AGENTS.md Last Updated` (not required) fails a stamp later than the run's UTC date.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/logical-percolating-sparkle
git fetch origin && git status --short      # M tests/test_service_fork_drift.py; ?? the guard mutation script
git log --oneline -1 origin/main
python3 util/ad-hoc/2026-11-12_tools_floors_observability_0_4_2_service_core_0_7_2.py --check   # 22 of 22
python3 -m unittest tests/test_service_fork_drift.py                                           # OK (skipped=3)
gh pr list --repo pcalnon/juniper-data --state all --limit 5       # flood-4's Retry-After carrier
```

## Git status (2026-11-13 01:15Z)

- juniper-ml worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/logical-percolating-sparkle`,
  branch `worktree-logical-percolating-sparkle`, HEAD `26ea0ecb` (`main` at #2555's merge); nothing staged.
  Uncommitted: `tests/test_service_fork_drift.py` (the guard) and
  `util/ad-hoc/2026-11-12_retry_after_guard_mutation_check.py`, both for the guard PR. This file lands in its own
  docs PR.
- Fork worktrees under `/home/pcalnon/Development/python/Juniper/worktrees/`, each holding uncommitted edits that
  equal what its PR merged: `juniper-cascor--fix--fastapi-telemetry-opt-out--20261111-1855--9f632eac` (#755),
  `juniper-canopy--fix--fastapi-telemetry-opt-out--20261111-1855--0d7c393f` (#816),
  `juniper-cascor--fix--rate-limit-retry-after-round-up--20261111-1855--9f632eac` (#757),
  `juniper-canopy--fix--rate-limit-retry-after-round-up--20261111-1855--0d7c393f` (#817); and
  `juniper-data--fix--rate-limit-retry-after-round-up--20261111-1855--399eeffb` (never opened).
