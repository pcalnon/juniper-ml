# Handoff: one-artifact sweep. The owner ruled "Pin exact scripts" for the port checker after round 8's 3 MAJORs; fix pass 7 implements it (running at handoff), then round 9; then the 15 ports in 7 repos, and plan v1.15.18

**Written**: 2026-11-24 at 12:20Z (`date -u`) by session `ffffd3` (`d935c226`), ListAgents name
`one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772`.
**Worktree**: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.
**Supersedes** this session's earlier handoff,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_one-artifact-sweep-cascor-777-merged-checker-round-6-blocker-fix-pass-5-round-7-then-ports-plan-v1-15-18.md`
(juniper-ml#2620). Read that one's "Remaining work" items 2 and 3 (the ports, plan v1.15.18), its traps, and its git
state too: they still hold, except where this file says otherwise.

**Merge approval** is per session. Ask the owner again; nothing merges until the owner grants it in YOUR session.
**Start in `$W`.** The arc's untracked scripts and every review's evidence exist only there.

## State (all recorded in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`; `grep -n '^## '` lists the sections)

- **juniper-cascor#777 is MERGED** (`f5ed3017`, 2026-11-24 00:56:52Z), and its post-merge runs are green. cascor `main`
  has since moved to `b5b28dc3`, through #778 (docs only; the three publishers are byte-identical; fix pass 6 checked).
- **The port checker's reviews since #2620:**
  - **Round 7 was INCOMPLETE.** A safety interruption stopped its executed-mutant step.
  - **Fix pass 6** settled round 7's R7-1: run in three variants, the gap was a real MAJOR (a hidden PyPI reinstall
    before the import check). Its fix gives `789287c5…`.
  - **Round 8 was COMPLETE** and found 3 MAJORs (R8-1..R8-3), all executed.
- **Every round from 4 to 8 found MAJOR-or-worse bypasses**, and all of them come from the checker reading shell
  differently from bash.
- **The owner's ruling (2026-11-24, answered by 12:15:11Z), verbatim:** "Pin exact scripts (Recommended)". Each
  port's install step must equal, after whitespace normalization, a pinned reviewed script for that port. The pins are
  seeded from the 15 port simulations and updated in each port's own review, with one review round on that change,
  then the ports. The full question and options are in the dispositions file.
- **Fix pass 7** implements the ruling. Its brief is `$W/tmp/sweep/FIXPASS7_BRIEF.md`, its work directory
  `tmp/sweep/checker-r8/`, and its new pins file `util/ad-hoc/2026-11-24_publish_port_install_pins.json`. It was
  launched at about 12:19Z and was RUNNING when this handoff was written.
- **ml#2606 (the rename) is MERGED** (05:06:27Z, `5a049144`). It left juniper-ml's `publish*.yml` and
  `tests/test_publish_one_artifact.py` at main's earlier bytes. The ml port builds on the renamed `main` and follows
  its "Overtoad" wording in new text.

## Remaining work

1. **Fix pass 7, then round 9.** Follow the "If you are a new session" header of `$W/tmp/sweep/FIXPASS7_BRIEF.md`.
   - If `REVIEW_DISPOSITIONS.md` has a `## Fix pass 7` section, the pass finished. Check
     `sha256sum -c tmp/arc/sweep_scripts.sha256`, which covers 7 paths from now on. Then launch ONE fresh
     `general-purpose` reviewer on `tmp/sweep/ROUND9_BRIEF.md`, unedited. Its report goes to
     `tmp/r9review/ROUND9_REPORT.md`.
   - If `tmp/r9review/ROUND9_REPORT.md` already exists, record it instead.
   - If `ListAgents` shows this session (ffffd3) busy, ask it before launching anything.
   - Round 9 counts only if it is COMPLETE and reports no BLOCKER and no MAJOR. If its executed-mutant step is
     interrupted, ask the owner (§ "Round-7 review" sets out that rule).
2. **The ports.** This is item 2 of #2620's handoff, plus the following:
   - **Each port's review updates that port's pin** in the pins file, which is untracked in `$W` and lands with plan
     v1.15.18. The expected updates are listed in § "Fix pass 7": R4-5's `find_spec` in six ports, and ml's lag text
     with `tests/test_publish_testpypi_verify.py:477`.
   - **Done** when `bash tmp/ports/verify_all_mains_v2.bash` prints `18 of 18 pass`. Today it prints 3 of 18. If the
     checker now needs a `--pins` argument, adapt the script.
3. **Plan v1.15.18.** This is item 3 of #2620's handoff, plus rounds 7 and 8, fix passes 5-7, the owner's ruling, the
   pins file (the 7th script) and `tmp/arc/plan_v1_15_18_inputs.md`. Build it on a FRESH clone of juniper-ml `main`.

## Traps added

- **A reviewer's mutant step can be safety-interrupted** (round 7). Frame mutants as negative test cases for our own
  CI gate. Require "what was not done" as the report's first section, and treat an incomplete round as not clearing
  anything.
- **Peers' sockets go stale.** The rename sessions have ended; their last message announced ml#2606's merge. Before
  messaging any peer, run `ListAgents`.
- **`/tmp/vFI4WZy/`** (see #2620's handoff) is still unattributed.

## Verification (from `$W`, one per call)

```bash
grep -n '^## ' tmp/sweep/REVIEW_DISPOSITIONS.md       # "Fix pass 7"? "Round-9 review"?
sha256sum -c tmp/arc/sweep_scripts.sha256             # 6 or 7 x OK (7 once fix pass 7 finished)
ls tmp/r9review/ROUND9_REPORT.md                      # round 9 ran?
gh pr view 777 --repo pcalnon/juniper-cascor --json state,mergeCommit
```

## Git state of `$W` (12:20Z)

- Branch `worktree-ethereal-munching-peacock` at `81b8eaf7`, behind juniper-ml `main` `d7709ef7`. Nothing is staged.
- Untracked files:
  - this handoff;
  - #2620's handoff;
  - the predecessor's handoff;
  - 28 copies of files on `main`;
  - the arc's scripts. Never delete these, and keep them in `tmp/arc/sweep_scripts.sha256`. That is 6 now, and 7 once
    fix pass 7 adds the pins file.
- New in `tmp/`, besides what #2620 lists: `sweep/checker-r7/`, `sweep/checker-r8/`, `r7review/`, `r8review/`,
  `sweep/FIXPASS6_BRIEF.md`, `sweep/FIXPASS7_BRIEF.md`, `sweep/ROUND8_BRIEF.md`, and `arc/sweep_scripts.r7.sha256`
  (plus `r8` once made).
- Retention is as in #2620's handoff.

## Documents referenced / changed

- **Referenced:** #2620's handoff (above), `tmp/sweep/REVIEW_DISPOSITIONS.md`, `tmp/sweep/FIXPASS7_BRIEF.md`,
  `tmp/r7review/ROUND7_REPORT.md`, `tmp/r8review/ROUND8_REPORT.md`.
- **Changed in `$W` since #2620:**
  - `util/ad-hoc/2026-11-23_publish_port_template_identity.py`, by fix passes 6 and 7;
  - `tmp/sweep/REVIEW_DISPOSITIONS.md`, appended with § Round-7 review, Fix pass 6, Status, Round-8 review, the
    owner's ruling, and Fix pass 7 by its executor;
  - `tmp/arc/plan_v1_15_18_inputs.md`;
  - the briefs `FIXPASS6`, `FIXPASS7`, `ROUND8` (`ROUND9` by fix pass 7).
- **In memory:** `reference_agents_md_date_check_crosses_midnight_utc.md`.
- This handoff lands through its own one-file PR.
