# HANDOFF 2026-10-30 — backup arc: Phase D's two missing commands designed, validated and merged; now the sitting

Session "backup-ac11-passed-transcript-count-zero-then-phase-d" (worktree `lively-finding-wand`), continuing `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_backup-ac11-passed-transcript-count-zero-then-phase-d.md` (juniper-ml#2387). Host `yamaguchi`.

The session ran no step of Phase D and changed nothing on the host. **Tier 1 (Duplicati) is still down**: no backup since 2026-09-18 14:12 UTC. Tier 2 and Tier 3 run.

| Short form | File |
| --- | --- |
| **the runbook** | `notes/JUNIPER_2026-10-29_JUNIPER-ECOSYSTEM_BACKUP-PHASE-D-STEP0-TRIAL-AND-KEY-WRITE-RUNBOOK.md`: step 0, step 7's route, step 9's key write on Procedure A, A0's command lines, the owner rulings (its §3) |
| `…10-29…md` | the predecessor handoff above: its Remaining §1 deltas and Key context still apply wherever the runbook does not replace them |
| `…RECOVERY-PLAN.md` | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`: §6.4 is Phase D; §6.3.1 is the running record |
| `…INTEGRATED-DESIGN.md` | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` ("D"); its §8 is the procedure §6.4 checks against |

## Continue

**Phase D's sitting, steps 0 to 14, interactively with the owner** (about two hours).

1. Run the verify block below. If any line differs from its comment, stop and show the owner.
2. Read the runbook in full. Then read `…10-29…md`'s Remaining §1 and Key context, and `…RECOVERY-PLAN.md` §6.4.
3. **Step 0 is the runbook's §1.** Steps 1 to 6 are §6.4 with `…10-29…md`'s deltas. Step 7 is the runbook's §2.1, then
   its §2.2 on an `ENV_ACTIVE_KEY` match, or its §2.4 (A0) on none. Step 9 on Procedure A is the runbook's §2.3. Steps 10
   to 14 are §6.4 with `…10-29…md`'s deltas.
4. **Who runs what** is unchanged. The owner runs every step that changes the host or reaches the server, in the root
   shell or the pcalnon shell the runbook's §0 names. The owner pastes counts and the tools' own summary lines, never a
   raw journal from a server start. The session checks each step read-only and keeps a running record.
5. **Land the record** in `…RECOVERY-PLAN.md` in one signed PR at the end. If the record changes a §6.4 step, run one
   narrow validation lane on it first (§6.7).

Merge approval for this sitting's PRs: ask the owner again (2026-10-29's approval covered that session's PRs).

## Completed, 2026-10-29 and 10-30

- **#2387's verify block held** on every line (2026-10-29, about 20:55 CDT).
- **The design PR** (the one that landed this file) adds:
  - the runbook;
  - `util/ad-hoc/2026-10-29_duplicati-trial-override.conf`, the trial's drop-in;
  - `util/ad-hoc/2026-10-29_write_matched_settings_key.py` 1.3.0, Procedure A's verified key write, with its suite (26 tests) and a 30-mutant check;
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
  - **A 243 with the key present is a credential-setup failure**, not the `/etc/credstore` mask.
  - **The listener count is 2**: loopback binds both IPv4 and IPv6.
- **Owner rulings, 2026-10-29** (the runbook's §3):
  - the trial's form: a runtime unit plus the drop-in;
  - all the other departures;
  - `PrivateTmp` accepted for Phase D;
  - the sitting runs in this fresh thread;
  - still open: AC-14's Phase E ruling (the runbook's §5).
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
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --check | tail -1                            # 0 staged, 14 already current, 0 skipped
ls -la /run/systemd/system/ /usr/local/lib/duplicati-trial 2>&1                                        # /run/systemd/system empty; no duplicati-trial dir
findmnt -no OPTIONS /run                                            # ...noexec... (why the trial's inputs are not under /run)
ls -la /home/duplicati/.config/Duplicati/preload.json /usr/lib/duplicati/preload.json 2>&1            # both absent
```

The owner's checkout must be at `origin/main` including the design PR (the runbook's §0).

**Git state at handoff.** Worktree `lively-finding-wand`, branch `worktree-lively-finding-wand`. Everything the session
wrote is in the design PR. The worktree's `tmp/phase-d/` holds the round-1 to round-4 lane workspaces and the source
copies they fetched. They hold no secrets, and none is needed once the PR merges; the `tmp/` retention ruling then allows
deleting them.

## Limits (unchanged; every lane brief must carry them, and now say "no `sudo` in any form, not even `-n` or `-l`")

- Never start, stop, restart, enable, disable or reload a unit.
- Never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`.
- Nothing under `/mnt/Backups/Ubuntu/` beyond `stat`.
- Never read a secret file; never print an environment variable or a token.
- No `git stash`; no interactive shells; no host actions.

The owner may direct a named action in person, which releases that action only. Nothing releases one of
`…RECOVERY-PLAN.md` §6.0 item 6's absolutes. Phase D's `sudo` steps, server calls and credential writes are the owner's.
