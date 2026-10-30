# Thread Handoff — Recurrence × Equities: plans v1.15.9 and v1.7.24 record 2026-10-30; the owner's items are next

**Date**: 2026-10-30 UTC (this host's clock is local time, UTC−5)
**Session**: `856140dc` (`ListAgents` name `recurrence-equities-trio-stopped-notify-matrix-deploy-0-13-0-test-accuracy-filled`), the Linux host, worktree `.claude/worktrees/vast-wiggling-parnas`. Commits are signed only through the API (`util/open_signed_pr.py`), never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_recurrence-equities-trio-stopped-notify-matrix-deploy-0-13-0-test-accuracy-filled.md` (landed by juniper-ml#2390). Start from this file. Its item 1 passed, its item 2 is this handoff's PR, and its items 3 and 4 are carried below.

---

## Goal

Continue the recurrence × equities arc (P12 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.15.9 once this PR merges). **No session-side work is left.** The next step is the post-merge re-check of this PR, then the owner's items, which a session surfaces and does not act on without the owner's word.

## Completed this session (each probed here)

- **The predecessor's post-merge re-check passed** (2026-10-30 18:21–18:25Z).
  - ml#2390 is `4a513dcf` on `main`, and both `util/ad-hoc/2026-10-30_*` files from it are present.
  - `util/ad-hoc/2026-10-30_index_correction_row_failed.py --check` exits 0, and `index.jsonl` has 484 lines.
  - juniper-deploy's `docker-compose.yml` pins `juniper-cascor:0.13.0` at `:233` and `:427`, and juniper-data's notify matrix is `[juniper-recurrence, juniper-canopy]` (`:78`).
  - Only the four canopy legs listen (`:8052`, `:8053`, `:8058`, `:8059`). The trio-stop `MANIFEST.tsv` lists its three logs.
  - The arc memory already named ml#2390 (the predecessor wrote it after its merge), so that part of the item needed nothing.
- **The cascor primary moved again** at 2026-10-30 18:18:33Z: its `main` reflog records `pull origin: Fast-forward` from `e8e8bf4d` to `d042de23`, which is cascor `main` (cascor#735 and #736, merged 01:44Z and 02:01Z). Every change they make under `src/` is in `src/tests/`; the rest is CI, docs and `util/check_junit_executed.py`. The actor is unrecorded, as for the 10-29 pull.
- **The owner's answers are dated from source.** Session `904851c9` (`ListAgents` ref `6f4d37`) asked two question sets, and its transcript timestamps the answers.
  - The first set was asked 2026-10-29 22:48Z and answered **2026-10-29 23:10:11Z**:
    - the work to do (the `test_accuracy` run, the deploy pin, the notify matrix);
    - "Append 'failed'";
    - "i don't think the PR was mine. let's stop the :8202 stack".
  - The second, the stop's scope, was answered **2026-10-30 08:20:32Z**: "Trio via --down".
  - The session acted on all of them on 2026-10-30. So index line 483's text ("The owner ruled on 2026-10-30") and the superseded handoff's "about 9.6 h after the question" both date the first set a day late. Line 483 is append-only and stays as written.
  - The deploy-pin option the owner chose reads: "Choosing it rules that 0.13.0, which has no F-S10 fix, counts for the consolidated plan's R-CASCOR pin route."
- **Consolidated plan v1.15.9** (`util/ad-hoc/2026-10-30_consolidated_plan_v1_15_9_deploy_pin_test_accuracy_trio_stopped.py`, 23 edits, `--check`):
  - deploy#266 at the Overview's Sentry paragraph, §5 R-CASCOR, §8's juniper-deploy row, XC-P12 action 4 and §4's P6 line;
  - `test_accuracy` filled (run `20261030T084056Z-0ac7`; 0.575 in `metrics_final.json`, `stats.json` and `aggregate.csv`) at XC-P12 action 4 (with a "Filled" pointer), §2, §4 and Appendix A's T5; the register row's close stays the owner's;
  - the trio stop under §4 Wave 1's trio route (O13), with pointers at the Overview, W0.1 (action 5) and the XC-SENTRY step;
  - juniper-data#501 and the token result under XC-P12's follow-ups; index line 483 at §4's P12 row and Appendix A's T2; action 6 points at v1.7.24;
  - the primary's second move under §5; P4-39 / P4-40 measured (below); the record lines.
- **Recurrence plan v1.7.24** (`util/ad-hoc/2026-10-30_plan_v1_7_24_failed_stands_notify_matrix_trio_stopped.py`, 6 edits, `--check`): a Status summary, a Progress bullet, **Next** rewritten (notify and `failed` items removed as done; preflight re-dated; juniper-canopy#778 cited for `mnist`'s Noise, not for the training fields, which #778 leaves out of scope), a pointer after the `failed` sentence at `:711` and in the v1.7.23 row, W0.1's row closure (`:571`), and the v1.7.24 revision row.
- **New measurements behind those edits**:
  - P4-39: cascor#672's version fix (`0d2d826b`) is an ancestor of `v0.12.0` (compare: behind 0), and both tags read the version from `importlib.metadata`. So P4-39 rode 0.12.0 and deploy#258; deploy#266 carries it on.
  - P4-40: cascor's CHANGELOG at `v0.13.0` repeats `### Added` and `### Fixed` in `[0.12.0]`, and no heading in `[0.13.0]`.
  - `util/recurrence_env_preflight.bash` still REFUSES `JuniperCascor1` (2 findings, both `juniper-service-core` 0.5.0 against `>=0.6.0,<0.8.0`; re-run 2026-10-30, exit 1).
  - None of the host's 12 TCP listeners runs from `JuniperCascor1`, but short-lived processes do. It is this host's `python3`, and `util/experiment_stack.bash:200` makes it the default cascor environment: the 08:40Z `test_accuracy` run's cascor ran from it (no override in its `launch.env`; Python 3.14.7 in its manifest).
  - cascor's `requirements-cpu.lock` at `v0.13.0` pins observability 0.4.1, service-core 0.7.1 and data-client 0.6.0.
  - The test pin canopy#777's diff missed was `test_notify_consumers_dispatch.py:438` at data#501's parent; on `main` it is `:441`, asserting `CONSUMERS`.
  - GHCR's `juniper-cascor:0.13.0` index is `sha256:721417527c4f429c…` (registry API).
- **Independent fact-check**: one read-only reviewer checked the first draft against primary sources. It found 1 BLOCKER, 2 MAJOR, 5 MINOR and 7 NIT, verified 26 claims, and left 6 explicitly unverified. All findings are applied.
  - **BLOCKER**: the ruling dates. The first draft dated all four answers 2026-10-30, and three came on 2026-10-29.
  - **MAJOR**: "a `/proc` scan found no Python process running from `JuniperCascor1`" read as "nothing uses it". Another session's script ran from it minutes later, and the experiment stack uses it by default. The plans now say no listening service runs from it.
  - **MAJOR (residue)**: the Overview's "it pins data 0.17.1 and cascor 0.12.0".
  - **MINORs**:
    - the stop's order of events: the canopy session's no-hold reply had arrived but was read after the stop;
    - the Overview's "the stack trio runs";
    - action 6's pointer at v1.7.23's **Next**;
    - juniper-canopy#778 "proposes" rather than "carries" the change;
    - the record's source list.
  - **NITs**: the owner's own words ("the PR", not "the pull"), the session alias, the changed-file list, the parent `AGENTS.md` item, and a "Filled" pointer. The Date line's 10-30 list stays short, because it is 510 of 512 characters.

## Remaining work, in order

1. **Post-merge re-check of this PR.**
   - On `main`, the plans read 1.15.9 and 1.7.24, and both new scripts' `--check` exit 0.
   - This handoff is present. Write the PR's number and merge sha into the arc memory's state block.
2. **The owner's items** (surface them; do not act on them).
   - **Close APD-ML-002.** The evidence is run `20261030T084056Z-0ac7`. The close is the five touches in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (`:43`), and its `:1304` / `:1364` ("unreleased") are stale since Release v0.13.0.
   - **The parent `Juniper/AGENTS.md` cascor 0.13.0 bullet** (`:240-248`) says "juniper-deploy still pins the `0.12.0` image", which is stale since deploy#266. It is unversioned and shared: get the owner's approval, back it up to the primary's `tmp/`, and check its sha256 first (`5082c9c8…` at 2026-10-30 18:43Z).
   - **Who pulls the trio's primaries** (O13), and the cascor primary's two unrecorded pulls (2026-10-29 20:48:58Z, 2026-10-30 18:18:33Z). A trio `--up` now runs cascor `main` whole, which §4 Wave 1's trio route admits only after P3-05, with #683's deployment note applied.
   - **R-DATA-2** (juniper-data 0.17.2): W5.7 is a default change. canopy#777's drift job goes red then by design, and since data#501 the release's own dispatch runs it.
   - **juniper-config-tools 0.2.0** (backfill `[Unreleased]` first).
   - **W0.1's service-core half**: never modify `JuniperCascor1` from a session. It was ruled for "the next cascor restart" (2026-10-18). The `:8202` cascor that ran from it is stopped, but the environment is still in use: it is this host's `python3` and the experiment stack's default cascor environment.
   - **Index line 483's date**: its text says the owner ruled on 2026-10-30, and the answer came on 2026-10-29 at 23:10Z. The index is append-only, and any further correction row needs the owner's word. The plans record the right date.
   - **§6 A1 / A9**.
   - juniper-canopy#778 needs a canopy session.
3. **Follow-ups.**
   - `save_model`'s live run (juniper-ml#2316) is BLOCKED on W0.1.
   - Worktrees awaiting an owner or canopy-session signal: the canopy worktrees `…declared-param-staging-735-736…` and `…juniper-data-schema-drift-check…`; the juniper-ml worktrees `keen-popping-wilkes`, `cosmic-puzzling-lovelace`, `declarative-snuggling-sparrow` and this one, `vast-wiggling-parnas`. Check each one's `tmp/` before removing it.
   - `MEMORY.md` is about 21.5 KB, over the 20 KB target; the excess is other arcs'.

## Rules that held this session

- **Re-probe a handoff's state before writing it as current.** The cascor primary moved 6 minutes before this session's re-check, and the handoff's own verification line ("e8e8bf4d... until the primary moves") caught it.
- **Date an owner's answer from the transcript, not from the record of the action.** The predecessor's handoff and index line 483 dated answers given at 2026-10-29 23:10Z as 2026-10-30, the day they were acted on. Only a reviewer reading the transcript's timestamps caught it.
- **A process scan is a point in time, and "no process" is the wrong claim about a shared environment.** A first draft said "that day no Python process ran from `JuniperCascor1`". That was false: this shell's `python3` is that environment's interpreter, and so is the experiment stack's default cascor. Write what was measured: no listening service runs from it.
- **A pre-PR line number moves with the PR**: `:438` became `:441`.
- **Read the owner's words at the source.** The ruling's scope came from the option text the owner chose, read from the predecessor's transcript, not from the predecessor's paraphrase.
- **Tooling on this host**:
  - The Write tool refuses the primary's `tmp/` from a worktree session (scratch went to the worktree's `tmp/s2/`).
  - The worktree guard refuses `sed` with a variable operand, `for` loops that run `gh`, and `${PIPESTATUS}` next to `git`. Spell paths out, or write a script.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -5 origin/main
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.24 and 1.15.9
python3 -I util/ad-hoc/2026-10-30_consolidated_plan_v1_15_9_deploy_pin_test_accuracy_trio_stopped.py --check; echo $?   # 0
python3 -I util/ad-hoc/2026-10-30_plan_v1_7_24_failed_stands_notify_matrix_trio_stopped.py --check; echo $?            # 0
python3 -I util/ad-hoc/2026-10-30_index_correction_row_failed.py --check; echo $?                                      # 0
wc -l ~/.local/state/juniper-experiments/index.jsonl                                                                     # 484 or more
cat /home/pcalnon/Development/python/Juniper/juniper-cascor/.git/refs/heads/main                                         # d042de23... until the primary moves
ss -ltnpH | grep -E ':(8051|8052|8053|8058|8059|8101|8202) '                                                             # only the four legs
grep -n 'juniper-deploy still pins' /home/pcalnon/Development/python/Juniper/AGENTS.md                                   # stale until the owner approves the edit
bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python; echo $?                 # 1 (2 findings) until W0.1
```

## Git state

- **This worktree** (`vast-wiggling-parnas`) is on `worktree-vast-wiggling-parnas` at `2e2a65cc`.
- This handoff's PR carries the worktree's uncommitted copies of five files, uploaded through `util/open_signed_pr.py`, so the local branch never moves.
- **Gitignored scratch** is in this worktree's `tmp/s2/` (a transcript reader, cascor's `v0.13.0` CHANGELOG, the PR body) and `tmp/review/` (the reviewer's). None of it is the only copy of a record.

## Documents created or modified this session

- **juniper-ml, via this handoff's PR**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.8 → v1.15.9);
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.23 → v1.7.24);
  - `util/ad-hoc/2026-10-30_consolidated_plan_v1_15_9_deploy_pin_test_accuracy_trio_stopped.py` (new);
  - `util/ad-hoc/2026-10-30_plan_v1_7_24_failed_stands_notify_matrix_trio_stopped.py` (new);
  - this file (new).
- **Outside any repo**: the auto-memory `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description). `MEMORY.md` is unchanged.
- **Referenced, not changed**:
  - the superseded handoff (above), `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` and `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`;
  - `util/ad-hoc/2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py` and `util/ad-hoc/2026-10-27_plan_v1_7_23_client_0_3_1_published_followups_closed.py` (the patterns), `util/recurrence_env_preflight.bash` and `util/ad-hoc/2026-10-05_codeql_python_prescreen.py`;
  - `/home/pcalnon/Development/python/Juniper/AGENTS.md`;
  - `~/.local/state/juniper-experiments/index.jsonl`, run `20261030T084056Z-0ac7`'s results and its suite's `aggregate.csv`, `juniper-ml/tmp/2026-10-30-trio-stop/` and `juniper-ml/tmp/2026-10-30-recurrence-equities-y2/`.
