# Thread Handoff — R-OBS-SC-2's follow-ups: four ruled (session 6e3bdef0 is carrying them out), four open

**Date**: 2026-11-12 UTC (local 2026-11-11, UTC−6). Facts below were re-probed on 2026-11-12 between 00:21Z and 01:20Z; a fact that moved within that window carries its own time.
**Session**: `a4e1e914`, the Linux host, worktree `.claude/worktrees/harmonic-yawning-pancake` (branch `worktree-harmonic-yawning-pancake`, at `a03680c8`; at 01:14Z `origin/main` was `49c26023`, 10 commits ahead).
- Three of those 10 touch files that step 5 edits, though every cited line still holds (the anchor check, below):
  - ml#2534: `CHANGELOG.md` and `docs/REFERENCE.md`. It also makes service-core's next release a minor, 0.8.0 (step 5).
  - ml#2538: `AGENTS.md` and `CHANGELOG.md`.
  - ml#2536: `.github/workflows/lockfile-update.yml`. This file lands in its own PR through `util/open_signed_pr.py` (branch `docs/handoff-r-obs-sc-2-follow-ups-2026-11-12`), which this session merges under its own approval. If that PR is still open, merging it is yours, under your approval.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-09_r-obs-sc-2-recorded-plan-v1-15-15-owner-items-next.md` (session `09366253`). Its step 1 (post-merge re-check) passed here. Its step 2 (owner items) went to the owner in two rounds: round 1 ruled four items, and round 2's four came back unanswered (both below).
**Already continued, from a draft. `6e3bdef0` owns this arc while it is live.**
- **Who.** Session `6e3bdef0`: worktree `logical-percolating-sparkle`; it appears as `r-obs-sc-2-follow-ups-four-ruled-four-open` in `ListAgents`.
- **Grant.** It started at 2026-11-12 00:38:29Z with the owner's grant "approval granted for merging and related git operations for this work arc" (00:39:16Z).
- **What it read.** At 00:40:05Z it took this file's **first, unvalidated draft** from this worktree.
- **What it started.** By 00:43:54Z it had cut five worktrees under `Juniper/worktrees/` from `origin/main`: `fix/fastapi-telemetry-opt-out` in cascor and canopy (step 3), and `fix/rate-limit-retry-after-round-up` in cascor, canopy and data (step 4).
- **Un-blanked runs.** Before the corrections reached it, it ran cascor's `src/tests/unit/api/test_api_app.py` twice without blanking the Sentry DSNs (00:48:37Z and 00:48:55Z). Its own probe found that this path never imports `main` and starts no Sentry client, so nothing was sent (its message of 00:52:45Z).
- **Corrections sent.** This session messaged it corrections at 00:49:13Z and 00:53:16Z, and at 01:15:16Z retracted one item of the second. It re-read an intermediate revision at 00:50:20Z.
- **A new session checks `ListAgents` and those five worktrees first, and works with `6e3bdef0` rather than redoing its work.**

## Goal

Continue R-OBS-SC-2's follow-ups. They are recorded in `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (below, "the plan"), at §5's note on R-OBS-SC-2 ("Follow-ups", "What it leaves open", "No running image carries it yet") and §6's mid-wave sitting ("R-OBS-SC-2's follow-ups").

1. **Your first turn asks the owner three things.** `6e3bdef0` already holds a group grant for this work arc, so for it the first is settled and the other two are not.
   - Merge approval for a **named group**: the two telemetry PRs, the three fork RateLimiter PRs, the juniper-ml register-and-guard PR, the `[tools]` floor PR, 0.11.5's proposal and archive PRs, the plan v1.15.16 PR, and this handoff's own PR if it is still open. Approvals are per-session, and this session's ("approval granted for merging and related PR operations", 2026-11-09) does not carry (`feedback_headless_merge_approval_policy.md`).
   - Whether you may cut v0.11.5. Ruling 2 below names "this session" (`a4e1e914`) as the one that cuts.
   - **What the owner wants clarified about round 2.** On 2026-11-12 the owner sent round 2 back to clarify, then asked for this handoff.
2. Carry out round 1's rulings.
   - Until the plan edit (step 7), they are recorded only here, in this session's transcript, and in the memory file named under "Documents".
   - This session did nothing on them. `6e3bdef0` began steps 3 and 4 at 00:43Z (header).
3. Record them in the plan as v1.15.16. At v1.15.15, §6 lists seven of these items as open, and the eighth (the consumer cuts) is §5's "No running image carries it yet".
4. Re-ask round 2 as soon as the clarification is given (step 1). It does not wait on the PR work.

## Completed this session

- **Post-merge re-check** of ml#2532 (`a03680c8`) passed:
  - `util/ad-hoc/2026-11-09_consolidated_plan_v1_15_15_r_obs_sc_2_shipped.py --check` exits 0 (55 already applied);
  - the plan reads `Version**: 1.15.15`;
  - `util/ad-hoc/2026-11-09_r_obs_sc_2_record_reprobe.py` reads 0 FAIL, on 2026-11-09 and again on 2026-11-12.
- **Peer check, to 2026-11-12 00:48Z.**
  - `util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py` was run over every transcript written since 2026-11-09 11:00Z: `09366253`, `d0da1827`, `6290230e`, `da0ef143`, `4d06bd18`, `aee58c29`, `07e7105d`, `fbb54863`, `d730b17b` (the backup arc) and `6e3bdef0`.
  - None asked the owner about these items. Only `6e3bdef0`, this arc's successor (header), acts on them.
  - `4d06bd18`'s O13 ruling (2026-11-09 14:13:29Z, "Date rule, stated") settles which pulls O13 *lists*, not who may move the juniper-ml primary.
  - `07e7105d` (canopy E2E arc, worktree `distributed-giggling-clarke`) has had a question open since 2026-11-12 00:36:37Z: should juniper-ml#2360 land before Phase 16 or stay last? #2360's head `684c9751` is what the juniper-ml primary has checked out (Q4).
  - Open PRs on 2026-11-12: none in juniper-cascor, -canopy, -recurrence, -deploy or -data-client.
    - juniper-data has only Cursor drafts #520–#524. Of them, **data#521** documents the throttle's current `Retry-After` formula, "`max(1, int(window_seconds - elapsed))`", which ruling 3 replaces (step 4).
    - juniper-ml has #2360, #2545 (flood-4's handoff, opened 00:29:06Z) and 40 Cursor drafts. Of the drafts, **#2507** touches `tests/test_pyproject_extras.py`, a co-change file of the floor PR (step 5).
- **Round 1** was asked at 2026-11-09 14:27:13Z and answered at 14:48:41Z, after each option was checked against the code.
- **Round 2** was asked at 14:49:42Z. The owner sent it back at 2026-11-12 00:20:11Z ("wants to clarify"), then asked for this handoff, with the open questions documented in it.
- No PR, code change or plan edit besides this file. The memory file is updated (see "Documents").

## Round 1: the owner's rulings (2026-11-09 14:48:41Z; label and option text verbatim)

1. **Floor PRs** — "In release PRs (Recommended)": "Each consumer's next release/<pkg>-v<ver> bump PR raises the floors: the regen skips release/ branches, and the locks already satisfy the floors. Nothing opens now. Recurrence, which has no regen workflow, follows the same rule." This answers P3 D-03's third part (P3-17). The floors are `juniper-observability>=0.4.2` and `juniper-service-core>=0.7.2`, in data, cascor, canopy and recurrence.
2. **0.11.5** — "Floor PR, then 0.11.5 (Recommended)": "This session opens the floor PR (observability>=0.4.2; service-core>=0.7.2,<0.8.0, whose only module change is the throttle round-up) and merges it once green. Then it proposes and cuts v0.11.5 as a patch, as for 0.11.4, and you approve the pypi gate."
3. **RateLimiter** — "Row + fix all three (Recommended)": "File APD-ECO-016 (§2.3 copy drift). Open one PR per fork that ports service-core's max(1, ceil(...)) to both limiter paths (and to the throttle in data and cascor), with tests, plus a fork-drift guard naming the row. No pyproject change, so no lock regen; each fix ships with its repo's next release."
4. **Telemetry** — "Port to both now (Recommended)": "One small PR each in cascor and canopy: data#454's 7-line change and its test. No pyproject change, so no lock regen; each ships with its repo's next release."

## Remaining work, in order

1. **First turn**: the three questions in Goal 1, then the verification block below. As soon as the owner says what to clarify, clarify it and re-ask round 2 (next section). That does not wait for steps 2–7.
2. **How to change a fork.** Never pull a primary checkout or switch its branch.
   - **Get a tree**:
     - **A worktree** under `/home/pcalnon/Development/python/Juniper/worktrees/`, made with exactly two commands:
       - `git -C <primary> fetch origin` (it moves only remote-tracking refs);
       - `git -C <primary> worktree add -b <branch> <path> origin/main`.

       This is what `6e3bdef0` did. Do **not** follow Steps 1–2 of the repos' `notes/WORKTREE_SETUP_PROCEDURE.md`: they stash a dirty primary and run `git checkout main` and `git pull origin main` in it (cascor's lines 36–44).
     - **A tarball**, if your isolation guard refuses git in other checkouts: one of the exact `main` SHA, in your worktree's `tmp/`, as `util/ad-hoc/2026-11-09_lock_round_2_fetch_consumers.py` does.
   - **Test it**:
     - **Blank the six Sentry DSN variables** first (Traps).
     - The cleanest environment is a venv built from the tree's own lock, as `…_lock_round_2_probe.py` does.
     - The trio's conda envs hold editable installs of the primaries, cascor's and data-client's among them in `JuniperCascor1`. If you test there, confirm from the suite's working directory that it imports the tree under test: `python -c 'import <module>; print(<module>.__file__)'`.
   - **Land it** with a signed commit: `python3 util/open_signed_pr.py --repo juniper-<x> --branch <b> --add LOCAL:REPOPATH --message … --title … --body-file …` (a signed API commit), or a signed local commit and push where your host signs. Check with `git log -1 --format=%G?`; `N` means unsigned.
3. **Telemetry** (the smallest step).
   - cascor's `src/api/app.py:773` and canopy's `src/main.py:541` call `FastAPI(` with no `telemetry=`.
   - Port data#454 (`b8237603`: `juniper_data/api/app.py` +7, `juniper_data/tests/unit/test_api_app.py` +12). All five keys are `False`, and the test `importorskip`s `fastapi.telemetry` and asserts each `app._telemetry[...] is False`.
   - Below FastAPI 0.142 the keyword lands in `app.extra`, so no floor moves. Canopy builds `app` at module level, not in a factory.
4. **RateLimiter**: the fork PRs first. The juniper-ml PR follows **after all three have merged**.
   - **Why the order matters.** `.github/workflows/docs-full-check.yml` runs the fork-drift test's cross-repo checks on a weekly schedule (Monday 06:00Z) and on dispatch, never on PRs, and `ci.yml` skips those checks.
   - So a guard opened too early passes its own PR and fails the next weekly run. Before merging, check the guard against an assembled ecosystem root, as `util/ad-hoc/2026-10-26_throttle_check_guard_mutation_check.py` did. Dispatch Docs Full Check after the merge.
   - **Sites**:
     - data `juniper_data/api/security.py:250` and `:254` (`RateLimiter.check`), `:427` (`FailedAuthThrottle.check`);
     - cascor `src/api/security.py:229`, `:233` and `:386`;
     - canopy `src/security.py:270` and `:274` (that file has no `FailedAuthThrottle`).
   - **Reference**: service-core's `RateLimiter._seconds_until_reset` (`juniper-service-core/juniper_service_core/security.py:216-236`) rounds with `max(1, math.ceil(...))` and is applied to the allowed path too, since it feeds `X-RateLimit-Reset`. `FailedAuthThrottle.check` returns at `:474`. The tests are at `juniper-service-core/tests/test_security.py:342`.
   - **Test to tighten**: cascor's `src/tests/unit/api/test_api_security.py:437` asserts `Retry-After >= 0`.
   - data#529 (merged 2026-11-09) made CI run the 44 tests of data's `test_security.py` that its unit lane had deselected, `TestRateLimiter`'s 15 among them.
   - Cursor draft data#521 documents the old throttle formula. data's fix PR should state the new one wherever data documents it, and #521's disposition (the flood-4 arc's) should know of the change.
   - **The juniper-ml PR** files APD-ECO-016 in §4.9 of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (ECO-013 and -014 are RESERVED; ECO-015 is the last used).
     - It also updates §2.3's copy-drift table and its count ("Twenty entries share one shape"), and corrects §4.2's "import none of it" (line 954), which is true of imports and false of the defect.
     - It adds the guard to `tests/test_service_fork_drift.py` as ENFORCED, with a mutation check, and updates `docs/REFERENCE.md`'s "all eight guards are `ENFORCED`".
   - **Precedent**: APD-ECO-015 (juniper-ml#2365). The copies were fixed first, the row was filed already FIXED, and `throttle-check-never-inserts` went in as ENFORCED, checked by `util/ad-hoc/2026-10-26_throttle_check_guard_mutation_check.py`. Read the register's §1, "Closing a row — the five touches", before filing.
   - **The other order also satisfies ruling 3**: file the row OPEN with a `KNOWN_GAP` guard first; the gate then fails, and demands promotion to ENFORCED, when a fork closes the gap. It costs a second juniper-ml PR, which the APD-ECO-015 order avoids.
5. **The `[tools]` floor, then 0.11.5.**
   - **The floor PR**: `pyproject.toml:98-99` → `juniper-observability>=0.4.2`, `juniper-service-core>=0.7.2,<0.8.0`.
     - **Its template is ml#2314**, 0.11.1's floor PR. `gh pr diff 2314 --name-only` lists nine files: `pyproject.toml`, `tests/test_pyproject_extras.py`, `README.md`, `docs/QUICK_START.md`, `docs/REFERENCE.md`, `AGENTS.md`, `CHANGELOG.md`, `juniper-observability/README.md` and `juniper-service-core/README.md`.
     - Sites on `main` (2026-11-12):
       - `tests/test_pyproject_extras.py:164-165`;
       - `README.md:47` and `:51` (the flat table) and `:93`;
       - `docs/QUICK_START.md:61`;
       - `docs/REFERENCE.md:131-132` (the Extras Reference rows) and `:8894`;
       - `AGENTS.md:214`'s extras table;
       - `juniper-service-core/README.md:114` ("Pin with `juniper-service-core>=0.7.1,<0.8.0`").
     - `ReadmeCompatTableTest` and `ExtrasDocsLockstepTest` in `tests/test_pyproject_extras.py` pin the tables, so a missed site fails CI.
     - `docs/REFERENCE.md:8784` and `:8891`, the sub-packages' "Current Version" cells, still read `0.4.1` and `0.7.1`, stale since 2026-11-09's publish.
     - `docs/REFERENCE.md:192` is the compatibility matrix's `0.11.x` row, whose observability cell reads `>=0.4.1`. The matrix is "one row per minor", and 0.11.1's cut rewrote that row to the newest floors rather than splitting it (step 5's cut bullet).
     - **service-core's `[Unreleased]` says its next release is a minor, 0.8.0** (ml#2534). That is outside ruling 2's `<0.8.0` and every consumer's service-core cap. Those caps widen before that Release (§5: "Cap PRs land before the Release"); record it in v1.15.16.
     - Add a `CHANGELOG.md` `[Unreleased]` entry.
     - juniper-ml's `lockfile-update.yml` runs on schedule or dispatch only, so this PR fires no regen.
   - **Coordinate with the flood-4 arc** (now session `fbb54863`, worktree `humming-stargazing-papert`). Its ruling 14 on Cursor draft juniper-ml#2507 is "Carry + extend propose.py (Recommended)", the owner's answer to session `d0da1827` at 2026-11-09 00:10:24Z (`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` §8, "Open items", item 14).
     - That pins four `docs/REFERENCE.md` sites to `pyproject.toml`, `:184` and `:192` among them, and makes `util/release_train/propose.py` edit them.
     - Before the cut, check whether its carrier has landed.
   - **The cut** follows §11 of `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (§11.7: "Run it from a clean checkout at `origin/main`": your own worktree, never the primary) and 0.11.4's record.
     - That record is in the plan's XC-P12, "What followed the 2026-11-06 rulings": `detect.py` proposed 0.12.0, and the manifest was set to the patch.
     - Write a 0.11.5 co-change tool. Its template is `util/ad-hoc/2026-10-25_juniper_ml_0_11_1_cut_cochanges.py`, which rewrites the matrix's `0.11.x` row when a column floor moves ("The matrix is one row per minor").
     - 0.11.4's `util/ad-hoc/2026-11-06_juniper_ml_0_11_4_cut_cochanges.py` cannot serve: it asserts that row is unchanged and stops if it is not.
     - 0.11.1's floor-only precedent was ml#2314 (floor), ml#2319 (proposal) and ml#2321 (archive).
   - **Gates**: cut only after the owner confirms that you may (Goal 1). The owner approves the `pypi` gate; no session does. After publish, an edit to the parent `Juniper/AGENTS.md`'s released paragraph (unversioned) is the owner's to approve, as 0.11.4's was.
6. **Floors**: nothing now (ruling 1).
7. **Plan v1.15.16.**
   - Check first that `origin/main`'s plan still reads 1.15.15.
   - Use a writer script with `--check`, as for v1.15.15. It must meet v1.15.15's bar: no new lines over 512 characters (`main` had 19), ID coverage unchanged (381 of 381), and two independent reviewers.
   - Record rulings 1–4, what was done, round 2's outcome, and the new facts below.
   - Write a new dated re-probe for the post-fix state. Do not edit `…_r_obs_sc_2_record_reprobe.py`: it is RETAINED as provenance, and its rows record the pre-fix state (the note under Verification).

## Round 2: the open questions (asked 2026-11-09 14:49:42Z; sent back 2026-11-12 00:20:11Z)

Ask what the owner wants clarified first. `owner_answers.py` prints questions only, never options, so they are reproduced here **verbatim as asked** (the dates in them are 2026-11-09's), followed by what has moved since.

**Q1 — "0.4.3 design".** *Asked*: "R-OBS-SC-3 (juniper-observability 0.4.3, owed under your 2026-11-08 ruling) covers what 0.4.2 left open: - query strings (canopy's ?api_key=, sent under the default send_pii=False); - a Sentry Logs policy (enable_logs=True has no before_send_log); - request bodies, breadcrumbs, exception values and list-shaped headers. Until it ships, XC-SENTRY's interim mitigations (a: a Sentry-side scrubbing rule; b: blank DSNs at the next restart) stay in force. When should its design start?"
- "Now, own thread (Recommended)": "A fresh session writes the design to notes/ and runs its validation rounds; implementation, a cut and a third lock round follow your ruling on it."
- "After consumer cuts": "First get 0.4.2 into running images; design 0.4.3 after that."
- "You'll schedule it": "Leave it open on the plan."
- *New since*: the deploy stack's DSNs are empty (Q2). That lowers the urgency for that stack only.

**Q2 — "Lock cuts".** *Asked*: "No running image carries 0.4.2 yet: each consumer's newest Release predates its lock PR (data v0.17.1, cascor v0.13.0, canopy v0.9.0, recurrence v0.8.1). data's R-DATA-2 is 0.18.0 by your 2026-11-03 ruling and waits for P3-03 and P3-09. A cut from main carries everything merged since the last Release: cascor 15 commits (incl. pillow 13, munkres 3 and a 35-package minor bump), canopy 44, recurrence 2. Which releases should carry the new locks and this arc's fixes?"
- "cascor+canopy after fixes (Recommended)": "Once this arc's RateLimiter and telemetry PRs merge, sessions prepare cascor and canopy releases from main, with the floors in each release PR, and you approve the gates; juniper-deploy's pins and a restart follow. cascor's precedes R-CASCOR's P3-05/P3-08 gates, as 0.12.0 and 0.13.0 did; canopy's is P4 D-4's second cut. data waits for 0.18.0, and recurrence for its next release."
- "Canopy only": "Cut canopy after the fixes (P4 D-4's second cut); cascor waits for R-CASCOR's gates (P3-05, P3-08), keeping the fix-forward question in one place."
- "Next planned releases": "No extra cuts: R-CASCOR after its gates, canopy per P4 D-4, data 0.18.0, recurrence's next."
- *New since*:
  - On 2026-11-12, `main` is cascor 23, canopy 54, recurrence 4 and data 40 commits past those Releases.
    - Beyond the asked list, cascor's range adds python-dateutil 4, importlib-metadata 10 and cascor#753's lifecycle fix, plus cascor#749's 29 updates, in `conf/` only.
    - The "35-package minor bump" was cascor#744, which also moved both image locks.
  - A juniper-deploy Docker stack has run on this host for about two days (`docker ps`): canopy 0.9.0 (:8050), cascor 0.13.0 (:8201), data 0.17.1, recurrence 0.8.0 (:8211), and two workers at 0.6.1.
    - Its four service images lock observability 0.4.1. The workers carry no observability.
  - The cascor, canopy and data containers set `JUNIPER_*_SENTRY_DSN` to empty, and recurrence has no Sentry variable (a names-only read).
    - The cascor container also mounts `juniper-deploy/secrets.example/cascor_sentry_dsn.txt` at `/run/secrets/cascor_sentry_dsn`, and no Sentry `*_FILE` variable is set. Per a reviewer's read of cascor 0.13.0, the code takes the DSN from the variable only, so it initializes no Sentry.
    - That answers, for this stack, the plan's "Whether the running services actually send to Sentry was not probed". The file's content was not read.
- *Related, still open*:
  - whether a fix-forward is owed for cascor 0.12.0 (§6);
  - P4 D-5, the cascor cut timing (§6 A5);
  - P4 D-4, the canopy cut timing.
  - R-DATA-2's lock gate is met; recurrence's two bench caps (`<0.18.0`) widen before its Release (§5).
  - A data-client fix accepted at A1 would need another lock PR after its release (§4 Wave 1, step 4).
  - P2-09's and P12-28's service-core halves wait for a later service-core release (§5).

**Q3 — "Restart gate".** *Asked*: "The trio (data :8101, cascor :8202, canopy :8051) has been stopped since 2026-10-30. Its restart also waits for P3-05 (your O13 ruling of 2026-11-03). Security step 5 has a session run S0.11's relay tests in each upgraded conda env before the restart, and those tests are unwritten: canopy's part needs no A1 ruling, while the data-client and cascor parts wait on A1's open limbs. The lock round carried your per-lock probe instead. That probe sends secrets in headers and cookies and checks what reaches Sentry; S0.11 drives F-S10's relays (the data key in relayed error bodies, logs and events), which the probe never touches. At the restart, may the probe stand in?" No option was recommended.
- "Re-run probe per env": "After you upgrade JuniperData (python3.14t), JuniperCanopy1 and JuniperCascor1, a session re-runs the probe in each and records it; the restart proceeds on that, P3-05 and XC-SENTRY (b). F-S10's relays stay untested until S0.11 exists."
- "Write S0.11 first": "The restart waits for S0.11: canopy's relay test is written now, and the data-client and cascor parts after A1's limbs are ruled."
- "Decide at the restart": "Leave it open until P3-05 clears and a restart is near."
- *New since*:
  - The trio's ports were still closed on 2026-11-12. Its `--up` is `util/isolated_stack.bash --up`, the counterpart of the `--down` that stopped it (§4 Wave 1, "The trio").
  - JuniperData and JuniperCanopy1 still hold observability 0.4.0 and service-core 0.5.0.
  - Security step 5 also says to record the commit the editable installs run, not pip's version. 0.4.2 does not scrub exception values (R-OBS-SC-3).

**Q4 — "ml primary".** *Asked*: "JuniperCascor1 imports juniper-observability and juniper-service-core as editable installs of the juniper-ml primary checkout (your W0.1 refresh, 2026-11-04). So whatever that checkout holds is what the next cascor restart, the experiment stack's default cascor env and this host's python3 import. Your O13 rule of 2026-11-03 (guarded session pulls) names the cascor, data, data-client and recurrence primaries, not juniper-ml. Today the juniper-ml primary was pulled at 09:46Z, switched to a feature branch at 10:40Z, and returned to main with a pull at 14:19Z. Who may move it?"
- "Guarded session pulls (Recommended)": "O13's rule extended: a session may fast-forward it to origin/main only when it is on main and clean, after ss, /proc/<pid>/cwd and the run dirs' pid files show that no live stack imports it, and it names the pull (time, from and to SHAs). Sessions never switch its branch; your own moves stay free."
- "Only you": "Sessions never move the juniper-ml primary."
- "No rule; record it": "It moves freely; the restart records the commit JuniperCascor1 imports, as Security step 5 already says."
- *New since*:
  - Its reflog shows pulls of `main` (2026-11-09 21:57:12Z; 2026-11-10 11:56:31Z and 22:45:00Z) and two short branches with one commit each: 2026-11-10 21:19:59–21:27:50Z, the branch that became ml#2542, and 2026-11-11 23:43:51–23:45:03Z, `fix/gitignore-update`.
  - From there it went straight to `fix/repo-tmp-dir-2026-10-26` (#2360's branch) and pulled it to `684c9751` at 23:45:39Z. It was back on `main` from 00:00:27Z to 00:02:37Z, and has sat on #2360's branch since.
    - So `JuniperCascor1` imports that branch's code now. Its `juniper-observability/` and `juniper-service-core/` trees equal `origin/main`'s (`git diff --stat origin/main 684c9751 --` on both is empty).
  - `07e7105d` reports that this head fails six launcher tests, and asks the owner whether #2360 lands before Phase 16.
  - Who may pull the canopy primary is open too (O13, the owner's answer of 2026-11-06).

**Owner items carried from the plan's §6, not asked this session**:
- cascor's fix-forward, and P4 D-4 and D-5 (all under Q2);
- A1's open limbs: the data-client and cascor F-S10 fixes;
- the trio's environment upgrade (Security step 5, an owner action).

## Not this arc's

- The canopy legs `:8052` and `:8053` still log to `/tmp/juniper-e2e/` (`canopy-8052.log` and `canopy-8053.log`, 45.2 MB each by `ls`; the directory is 87 MiB by `du -sh`), against the 2026-10-26 directive. The four legs (:8052, :8053, :8058, :8059) are guarded: check against `ss` before any reaper run.

## Traps

- **Blank the six Sentry DSN variables before any suite or service run.** Set `SENTRY_SDK_DSN`, `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN` and `JUNIPER_CANOPY_SENTRY_DSN` to `""` and never unset them (the plan's XC-SENTRY; H-14). `SENTRY_SDK_DSN` is **set, non-empty, in this host's session environment** (2026-11-12), and cascor's `src/main.py` still accepts it as a legacy name.
- **Never pull or switch a primary checkout.**
  - `tests/test_service_fork_drift.py:632`'s skip text says siblings "must be `git pull`ed to origin/main first", and publish procedure §11.7 asks for a clean checkout at `origin/main`. Meet both with your own worktrees or tarballs.
  - The drift test finds its siblings by walking up to the primaries' parent (`_find_ecosystem_root`, `:433`), so it sees a worktree or tarball tree only through an assembled ecosystem root, as the 2026-10-26 mutation check built.
  - O13 permits guarded pulls of four primaries only. The canopy and juniper-ml primaries are open questions (Q4).
- Write and Edit refuse the primary checkout's `tmp/`, though Bash may write there (`$TMPDIR`). Put tool-written files in your worktree's `tmp/`.
- **The isolation guard refuses**, so run one plain command per call:
  - `git -C` into another checkout;
  - heredocs;
  - compound commands around `gh api -H "Accept: application/vnd.github.raw"`;
  - shell loops over `gh`;
  - `${!var}` indirection;
  - `ss` filters with parentheses.

  Read another checkout's state from its files (`.git/HEAD`, `.git/logs/HEAD`).
- `ss -p` names no process for a Docker-published port (`docker-proxy` runs as root); use `docker ps`. Read env vars by name and emptiness only, never by value.
- `util/ad-hoc/2026-10-05_codeql_python_prescreen.py` takes file paths only: `--help` is read as a path.
- The pre-commit secrets hook is vacuous on unstaged files. Run gitleaks `dir` over copies, with a planted control.
- In data, cascor and canopy, a PR touching `pyproject.toml` fires `lockfile-update.yml`, which pushes a full `--upgrade` regen onto the branch; only `release/` heads skip it. None of the fork PRs above needs `pyproject.toml`.
- An armed auto-merge merges whatever head is current. If a bot commit lands on an armed PR, run `gh pr merge N --disable-auto` at once.
- An agent's finding is evidence, not a verdict: re-check it at the source.

## Verification commands (one per call)

```bash
git fetch origin
git log -1 --format='%h %s' origin/main
git show origin/main:notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md | command grep -c 'Version\*\*: 1.15.15'   # 1 until v1.15.16
python3 util/ad-hoc/2026-11-09_r_obs_sc_2_record_reprobe.py          # 0 FAIL before this arc's PRs land (see below)
python3 util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py a4e1e914   # round 1 answered 14:48:41Z; round 2 sent back 2026-11-12 00:20:11Z
find ~/.claude/projects -maxdepth 2 -name '*.jsonl' -newermt '2026-11-12T00:45:00Z'   # sessions written since this peer check; then run owner_answers.py over their prefixes
python3 -c "import os; [print(n, 'UNSET' if n not in os.environ else ('EMPTY' if not os.environ[n] else 'SET')) for n in ('SENTRY_SDK_DSN','SENTRY_DSN','JUNIPER_CASCOR_SENTRY_DSN','JUNIPER_DATA_SENTRY_DSN','CANOPY_SENTRY_DSN','JUNIPER_CANOPY_SENTRY_DSN')]"
git show origin/main:notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md | command grep -c 'APD-ECO-016'   # 0 until filed
gh pr list -R pcalnon/juniper-cascor --state open                    # empty on 2026-11-12
gh pr list -R pcalnon/juniper-canopy --state open                    # empty on 2026-11-12
gh pr list -R pcalnon/juniper-data --state open                      # Cursor drafts #520-#524 only on 2026-11-12
gh pr view 2507 -R pcalnon/juniper-ml --json state,isDraft           # OPEN draft on 2026-11-12 (flood-4 ruling 14)
gh pr list -R pcalnon/juniper-ml --head docs/handoff-r-obs-sc-2-follow-ups-2026-11-12 --state all   # this file's PR
```

The re-probe records the pre-fix state. After this arc's PRs merge, its throttle-line section and its two `passes telemetry=: False` rows fail by design. Its floor and consumer-Release rows fail at the next consumer release.

## Git state and files

- **This worktree**: `worktree-harmonic-yawning-pancake` at `a03680c8`, with no tracked change. This file is untracked here and lands through the PR above.
  - The ignored `tmp/harmonic/` holds the review apparatus: the frozen drafts, `anchor_check.py` (32 cited `file:line` anchors against `main`), `verbatim_check.py` (both rounds' texts against the transcript), the transcript reader, the reviewers' `laneA/` outputs and the PR body.
  - `git worktree remove` deletes that directory, so apply the retention rule before removing this worktree.
- **Scratch**, kept under the retention rule, in `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/harmonic-yawning-pancake-2026-11-09/`:
  - the fork files fetched from `main` on 2026-11-09;
  - the re-probe outputs of 2026-11-09 and 2026-11-12;
  - the owner-answers outputs: one taken before round 1, and one of this session taken after round 2 (`owner_answers_a4e1e914_2026-11-12.txt`).
- **The predecessors' evidence stays where it is**, all present on 2026-11-12: `bright-giggling-metcalfe`'s `tmp/lr2/`, `enchanted-foraging-rocket`'s and `fizzy-enchanting-deer`'s `tmp/`, and `groovy-petting-fiddle`'s `tmp/v1-15-15/`. Archive or delete them only under the retention rule.

## Documents referenced / changed

- **Referenced**:
  - the plan, `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`: §3 XC-SENTRY; §4 Wave 1 Security steps 4–5 and "The trio"; §5's R-OBS-SC-2, R-OBS-SC-3, R-DATA-2 and R-CASCOR rows and notes; §6 A5 and the mid-wave sitting; XC-P12's O13, W0.1 and the 2026-11-06 follow-ups;
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (§1, §2.3, §4.2, §4.9);
  - `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` (ruling 14);
  - `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (§11, §11.7);
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`;
  - `notes/releases/RELEASE_NOTES_juniper-service-core_v0.7.2.md`;
  - `docs/REFERENCE.md` (the fork-drift gate entry; the compatibility matrix);
  - `tests/test_service_fork_drift.py` and `.github/workflows/docs-full-check.yml`;
  - juniper-cascor's `notes/WORKTREE_SETUP_PROCEDURE.md` (its Steps 1–2);
  - the predecessor handoff named above.
- **Changed**:
  - this file, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md`;
  - outside the repo, two memory files:
    - `project_recurrence_equities_p0_arc_2026-10-04.md`, with a state block naming this handoff and the round 1 rulings;
    - `feedback_validate_handoff_prompts_independently.md`, with the lesson that a status message naming an unvalidated draft's path let the successor start from it.
