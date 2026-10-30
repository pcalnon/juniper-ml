# HANDOFF 2026-10-30 — backup arc: Phase D's two missing commands designed, validated and merged; now the sitting

Session "backup-ac11-passed-transcript-count-zero-then-phase-d" (worktree `lively-finding-wand`), continuing `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_backup-ac11-passed-transcript-count-zero-then-phase-d.md` (juniper-ml#2387). Host `yamaguchi`.

The session ran no step of Phase D. Outside the repo it changed only its memory notes and Claude Code's own files (Git state, below). **Tier 1 (Duplicati) is still down**: no backup since 2026-09-18 14:12 UTC. Tier 2 and Tier 3 run.

| Short form | File |
| --- | --- |
| **the runbook** | `notes/JUNIPER_2026-10-29_JUNIPER-ECOSYSTEM_BACKUP-PHASE-D-STEP0-TRIAL-AND-KEY-WRITE-RUNBOOK.md`: step 0, step 7's route, step 9's key write on Procedure A, A0's command lines, the owner rulings and the pending departures (its §3) |
| `…10-29…md` | the predecessor handoff above. Its Continue item 1, Remaining §1 (the deltas), Remaining §2 (after Phase D), Key context and Corrections still apply wherever the runbook does not replace them |
| `…RECOVERY-PLAN.md` | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`: §6.4 is Phase D; §6.3.1 is the running record |
| `…INTEGRATED-DESIGN.md` | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` ("D"); its §8 is the procedure `…RECOVERY-PLAN.md` §6.4 checks against |

## Continue

**Phase D's sitting, steps 0 to 14, interactively with the owner** (about two hours).

1. Run the verify block below. If any line differs from its comment, stop and show the owner.
2. **If a tool, path or flag is not where the runbook, `…10-29…md`, `…RECOVERY-PLAN.md` or `…INTEGRATED-DESIGN.md` says,
   stop and report it; never substitute one** (`…10-29…md` Continue item 1). Where `…10-29…md` or the runbook departs
   from D on purpose, it wins; a runbook departure wins only once the owner has ruled on it.
3. Read the runbook in full. Then read `…10-29…md`'s Remaining §1, Remaining §2 and Key context, and `…RECOVERY-PLAN.md`
   §6.4.
4. **Before step 0, put the runbook's three pending departures to the owner** (its §3, "Not yet put to the owner"):
   - the trial's inputs under `/usr/local/lib/duplicati-trial/`, with the drop-in's `DUPLICATI_ENV_FILE` and `Description=`;
   - the throwaway key under `/etc/credstore`;
   - step 7's glob copy, its `Backup` listing and its two added trust conditions.

   A ruling against one means a fix PR before step 0.
5. **Step 0 is the runbook's §1.** Steps 1 to 6 are `…RECOVERY-PLAN.md` §6.4 with `…10-29…md`'s deltas. Step 7 is the
   runbook's §2.1, then its §2.2 on an `ENV_ACTIVE_KEY` match, or its §2.4 (A0) on none. Step 9 on Procedure A is the
   runbook's §2.3. Steps 10 to 14 are `…RECOVERY-PLAN.md` §6.4 with `…10-29…md`'s deltas.
6. **Who runs what** is unchanged: the owner runs every step that changes the host or reaches the server, in the shell
   the runbook's §0 names, and pastes counts and the tools' own summary lines, never a raw journal from a server start.
   The session checks each step read-only and keeps a running record.
7. **Land the record** in `…RECOVERY-PLAN.md` §6.3.1 in one signed PR at the end. If the record changes a step of
   `…RECOVERY-PLAN.md` §6.4, first run one narrow validation lane on it (`…RECOVERY-PLAN.md` §6.7).
8. **After Phase D**: `…10-29…md` Remaining §2 (Phase E's order; O-11, whose TestPyPI token stays live until rotated;
   D-12; finding 15), plus the runbook's §5 (AC-14's Phase E ruling).

Merge approval for this sitting's PRs: ask the owner again (2026-10-29's approval covered that session's PRs).

## Completed, 2026-10-29 and 10-30

- **`…10-29…md`'s verify block held** on every line (2026-10-29, about 20:55 CDT).
- **The design PR** (the one that landed this file) adds:
  - the runbook;
  - `util/ad-hoc/2026-10-29_duplicati-trial-override.conf`, the trial's drop-in;
  - `util/ad-hoc/2026-10-29_write_matched_settings_key.py` 1.3.1, Procedure A's verified key write, with its suite (26 tests) and a 33-mutant check;
  - the password-init helper 1.4.0: the unit's no-phone-home environment and `TMPDIR`;
  - the re-key 1.4.0: a VACUUM under `temp_store=MEMORY`;
  - a 5-mutant check for the helper.
- **Validation**: four rounds and seven independent lanes. The runbook's §6 maps every finding to where it landed. The
  findings that changed the design:
  - **AC-14 cannot fail on production's journal.** `Unknown option supplied` reaches the console only under
    `--log-console`. The trial measures it instead, with console logging on and a planted unknown option as its control.
  - **The hand start would have reported usage** (`sudo -u` drops `DO_NOT_TRACK`). Fixed in helper 1.4.0.
  - **`/run` is mounted `noexec` on this host**, so the trial's wrapper lives in `/usr/local/lib/duplicati-trial/`.
  - **A SIGTERM or SIGHUP mid-write could leave an unverified key.** The tool now defers SIGINT, SIGTERM, SIGHUP and
    SIGQUIT across the write, and turns core dumps off.
  - **Round 4 found the rulings overstated** (three departures were never asked) and this file missing three items of
    `…10-29…md`'s. Both are fixed: the runbook's §3, and Continue items 2, 4 and 8 here.
- **Owner rulings, 2026-10-30** (the runbook's §3):
  - the trial's form: a runtime unit plus the drop-in;
  - the five departures the question listed (the runbook's §3 items 5 to 8, and item 4's redirect);
  - `PrivateTmp` accepted for Phase D;
  - the sitting runs in this fresh thread;
  - pending: Continue item 4; still open: AC-14's Phase E ruling (the runbook's §5).
- **Lane slips, disclosed**: a round-2 lane ran `sudo -n true` once (output discarded). A round-3 lane wrote and then
  deleted one gitignored `.pyc`.

## Key context (new; `…10-29…md`'s Key context and traps still apply)

- **No `sudo` inside the root shell.** Export `TMPDIR=/root/phase-d-tmp` once there, and re-check it before step 9's
  installer and before A0's scripts (the runbook's §0).
- **Trust the key-write tool's last decision line** (`wrote … both match` or `removed …`), whatever follows it. On any
  non-zero exit, `ls -la /etc/credstore` (the runbook's §2.3).
- **A failed trial pauses Phase D at step 0** (the runbook's §1.4). The no-reboot window is open from now until step
  10's start is checked, and on Procedure A until step 12's re-key is done.
- **`systemctl show` prints `LoadCredential` as `[unprintable]`**; read it with `busctl` (the runbook's §1.4 gate).
- **`/home/duplicati/.config/Duplicati` is world-writable (0777) until step 6.** The trial's gate checks that no
  `preload.json` sits there.

## Verify first

```bash
git fetch origin main && git log --oneline -1 origin/main
git log --oneline -1 origin/main -- notes/JUNIPER_2026-10-29_JUNIPER-ECOSYSTEM_BACKUP-PHASE-D-STEP0-TRIAL-AND-KEY-WRITE-RUNBOOK.md   # the design PR
ps -o pid=,lstart= -u duplicati                                     # 1397393 Sun Sep 20 18:19:42 2026
systemctl is-enabled duplicati.service                              # enabled -- so no reboot
systemctl is-enabled yamaguchi-server-db-snapshot.timer             # disabled
systemctl --user list-timers 'juniper-backup*' --no-pager           # both timers listed
cat ~/.local/state/juniper-backup/last-run.status ~/.local/state/juniper-backup-full/last-run.status   # SKIPPED or OK; never FAILED
systemctl --user list-units --state=failed --no-legend 'juniper-backup*'                              # nothing
systemctl list-units --all --type=mount --no-legend --plain --state=inactive 'snap-*.mount' | wc -l    # 0
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --check | tail -1                            # 0 staged, 14 already current, 0 skipped
ls -la /run/systemd/system/ /usr/local/lib/duplicati-trial 2>&1                                        # /run/systemd/system empty; no duplicati-trial dir
findmnt -no OPTIONS /run                                            # ...noexec... (why the trial's inputs are not under /run)
ls -la /home/duplicati/.config/Duplicati/preload.json /usr/lib/duplicati/preload.json 2>&1            # both absent
ls -d /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/ac11-restore-2026-10-28* 2>&1           # absent: removed 10-28
```

The owner's checkout must be at `origin/main` including the design PR (the runbook's §0).

**Git state at handoff.** Worktree `lively-finding-wand`, branch `worktree-lively-finding-wand`. Everything the session
wrote in the repo is in the design PR. Outside it:

- **memory**: the hub `project_backup_arc_hub.md` (a 10-29/30 paragraph) and its `MEMORY.md` line;
- **the worktree's `tmp/phase-d/`**: the round-1 to round-4 lane workspaces, the source copies they fetched, the
  mutation and suite logs, and the PR and commit bodies;
- **the primary's `tmp/claude-1000/…-lively-finding-wand/`**: this session's task outputs (`ded2ed6d-…/tasks/`) and its
  empty scratchpad (`c44c3c3e-…/scratchpad/`).

None of the `tmp/` files holds a secret or is needed once the PR merges, so the `tmp/` retention ruling then allows
deleting them.

## Limits (unchanged; every lane brief must carry them, and now say "no `sudo` in any form, not even `-n` or `-l`")

- Never start, stop, restart, enable, disable or reload a unit.
- Never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`.
- Nothing under `/mnt/Backups/Ubuntu/` beyond `stat`.
- Never read a secret file; never print an environment variable or a token.
- No `git stash`; no interactive shells; no host actions.

The owner may direct a named action in person, which releases that action only. Nothing releases one of
`…RECOVERY-PLAN.md` §6.0 item 6's absolutes. Phase D's `sudo` steps, server calls and credential writes are the owner's.
A lane brief that turns bytecode off writes `PYTHONDONTWRITEBYTECODE=1`: an empty value turns it on.
