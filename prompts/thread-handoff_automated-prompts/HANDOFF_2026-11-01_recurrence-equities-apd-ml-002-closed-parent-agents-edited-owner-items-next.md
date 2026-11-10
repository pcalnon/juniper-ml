# Thread Handoff — Recurrence × Equities: APD-ML-002 closed, the parent AGENTS.md pin edited; the rest is the owner's

**Date**: 2026-11-01 UTC (this host's clock is local time, UTC−5)
**Session**: `856140dc` (`ListAgents` name `recurrence-equities-trio-stopped-notify-matrix-deploy-0-13-0-test-accuracy-filled`), the Linux host, worktree `.claude/worktrees/vast-wiggling-parnas`. Commits are signed only through the API (`util/open_signed_pr.py`), never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_recurrence-equities-plans-v1-15-9-v1-7-24-owner-items-next.md` (landed by juniper-ml#2393). Start from this file. That handoff's item 1 passed, two of its owner items are done (below), and the rest are carried.

---

## Goal

Continue the recurrence × equities arc (P12 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.15.10 once this PR merges). **No session-side work is left.** The next step is the post-merge re-check of this PR; after that, only the owner's items remain.

## Completed this session, since juniper-ml#2393

- **ml#2393 merged** (2026-10-30 20:02:51Z, `af17c984`, by the armed auto-merge net after two BEHIND re-syncs). Post-merge re-check on 2026-11-01 17:56Z: its five files are byte-identical on `main`, the plans read 1.15.9 / 1.7.24, and both scripts' `--check` exit 0.
- **The owner answered this session's three questions** (asked 2026-10-30 19:22:23Z, answered 2026-11-01 17:55:48Z, both from the transcript):
  - APD-ML-002: "Close it (signed PR)";
  - the parent `AGENTS.md`'s 0.12.0 sentence: "Edit it";
  - index line 483's date: "No, leave it". No further correction row; the plans carry the right date.
- **The parent `Juniper/AGENTS.md` is edited** (unversioned; not in this PR).
  - The cascor 0.13.0 bullet now reads "juniper-deploy pins the `0.13.0` image since juniper-deploy#266 (2026-10-30)", re-wrapped as the approved preview showed.
  - Last Updated is 2026-11-01, the edit's own date. The question's option text said 2026-10-30.
  - The diff against the backup is those two hunks. The sha256 went from `5082c9c8…` to `29e375ff…`.
  - Both versions are in `juniper-ml/tmp/2026-11-01-parent-agents-md-backup/`.
- **Register row APD-ML-002 is closed**, by `util/ad-hoc/2026-11-01_register_close_apd_ml_002.py` (`--check`) on `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.
  - The row has no §3 entry, so four touches: the §4 row's `**FIXED` (ml#2145 + ml#2369 + cascor#731 + ml#2381), a §5.1 verification row on run `20261030T084056Z-0ac7`, the §2 line (the enumeration; 36 → 35 open, post-primer 21 → 20) and Last Updated.
  - The whole-file read of every hit also fixed two stale "unreleased" clauses (cascor#731 is in 0.13.0) and gave the 2026-10-26 ruling note a closing sentence. The other five hits are history and stay.
  - `util/ad-hoc/register_open_set.py` reads 137 rows, 102 fixed, 35 open. `util/ad-hoc/register_status_crosscheck.py` reads AGREE (102 / 102 / 102).
- **Consolidated plan v1.15.10** (`util/ad-hoc/2026-11-01_consolidated_plan_v1_15_10_apd_ml_002_closed.py`, 11 edits, `--check`) records both: §2, XC-P12 action 4 (a "Closed" sub-bullet), §4's P6 line, §5's `AGENTS.md` sub-bullet, Appendix A's T5, Appendix B row 11, and the record lines. The recurrence plan stays at v1.7.24: its APD-ML-002 sentences are dated progress records.

## Remaining work, in order

1. **Post-merge re-check of this PR.** On `main` the consolidated plan reads 1.15.10, both new scripts' `--check` exit 0, the two register counters read 35 open and AGREE, and this handoff is present. Write the PR's number into the arc memory's state block.
2. **The owner's items** (surface them; do not act on them):
   - **Who pulls the trio's primaries** (O13), and the cascor primary's two unrecorded pulls (2026-10-29 20:48:58Z; 2026-10-30 18:18:33Z to `d042de23`). A trio `--up` now runs cascor `main` whole, which §4 Wave 1's trio route admits only after P3-05, with #683's deployment note applied.
   - **R-DATA-2** (juniper-data 0.17.2; W5.7 is a default change). canopy#777's drift job goes red then by design, and since data#501 the release's own dispatch runs it.
   - **juniper-config-tools 0.2.0** (backfill `[Unreleased]` first).
   - **W0.1's service-core half**: never modify `JuniperCascor1` from a session. `util/recurrence_env_preflight.bash` still refuses it (2 findings, 2026-10-30). The environment is this host's `python3` and the experiment stack's default cascor environment.
   - **§6 A1 / A9**; and juniper-canopy#778 needs a canopy session.
3. **Follow-ups.**
   - `save_model`'s live run (juniper-ml#2316) is BLOCKED on W0.1.
   - Worktrees that need an owner or canopy-session signal:
     - canopy: `…declared-param-staging-735-736…` and `…juniper-data-schema-drift-check…`;
     - juniper-ml: `keen-popping-wilkes`, `cosmic-puzzling-lovelace`, `declarative-snuggling-sparrow` and `vast-wiggling-parnas`.
     - Check each one's `tmp/` before removing it.
   - `MEMORY.md` is over its 20 KB target; the excess is other arcs'.

## Rules that held this session

- **Re-probe after a long owner wait.** The answers came about 46.5 hours after the questions. `main`, the target files, the parent file's sha256, the cascor primary and the trio ports were all re-read before acting.
- **A close that names no id still moves counts.** The register's §2 count sentence and its history parenthetical were found by grepping for the count words, not the id.
- **Close the record in the same PR as the fix.** v1.15.9 said "the close is the owner's" in five places, and v1.15.10 moves them in the same PR as the close.
- **Date an owner's answer from the transcript** (this session's v1.15.9 lesson): answers given at 2026-10-29 23:10Z were first recorded as 2026-10-30.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -5 origin/main
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.15.10
python3 -I util/ad-hoc/2026-11-01_consolidated_plan_v1_15_10_apd_ml_002_closed.py --check; echo $?   # 0
python3 -I util/ad-hoc/2026-11-01_register_close_apd_ml_002.py --check; echo $?                     # 0
python3 util/ad-hoc/register_open_set.py | head -1                                                  # 137 rows | 102 fixed | 35 open (run from the repo root)
python3 -I util/ad-hoc/register_status_crosscheck.py | tail -1                                      # AGREE
sha256sum /home/pcalnon/Development/python/Juniper/AGENTS.md                                       # 29e375ff... until the next edit
cat /home/pcalnon/Development/python/Juniper/juniper-cascor/.git/refs/heads/main                    # d042de23... until the primary moves
```

## Git state

- **This worktree** (`vast-wiggling-parnas`) is on `worktree-vast-wiggling-parnas`, fast-forwarded to `main` at `7b3e622e`.
- This handoff's PR carries the worktree's uncommitted copies of five files, uploaded through `util/open_signed_pr.py`, so the local branch never moves.
- **Gitignored scratch** is in this worktree's `tmp/s2/` and `tmp/review/`. None of it is the only copy of a record.

## Documents created or modified since juniper-ml#2393

- **juniper-ml, via this handoff's PR**:
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (APD-ML-002 closed);
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.9 → v1.15.10);
  - `util/ad-hoc/2026-11-01_register_close_apd_ml_002.py` (new);
  - `util/ad-hoc/2026-11-01_consolidated_plan_v1_15_10_apd_ml_002_closed.py` (new);
  - this file (new).
- **Outside any repo**:
  - `/home/pcalnon/Development/python/Juniper/AGENTS.md` (owner-approved; two hunks);
  - `juniper-ml/tmp/2026-11-01-parent-agents-md-backup/` (new: the before and after copies);
  - the auto-memory `project_recurrence_equities_p0_arc_2026-10-04.md`. `MEMORY.md` is unchanged.
- **Referenced, not changed**: the superseded handoff (above), `docs/REFERENCE.md` § Defect Register Close Protocol, `util/ad-hoc/register_open_set.py` and `util/ad-hoc/register_status_crosscheck.py`.
