# HANDOFF 2026-10-08 — backup arc: Phase B MERGED (ml#2199); B9 next; owner actions owed

Session 097ae87b ("backup phase b round 3"), continuing `HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md`.

| Name | File |
| --- | --- |
| D | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` |
| A | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` |
| record | `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md` (42 sections, every report verbatim) |

## Continue

Continue the backup arc with **B9** of A §6.2. Phase B is merged; B9 is its own PR.

## Completed (2026-10-08)

- **ml#2199 merged** as `cb4d63a4` (squash of signed commits `fa5bd8f8` and `6c5c94e4`). Its post-merge runs on `main` are green: Post-Merge Main Verification, CodeQL and CI/CD. §8's STOP is cleared on `main`.
- **Round 3 was folded in**, then rounds 4 to 7 ran on each fold-in's delta:
  - round 4: 0 BLOCKER / 6 DEFECT / 28 NIT;
  - round 5: 0 / 4 / 12;
  - round 6: 0 / 3 / 4;
  - round 7: **0 / 0 / 7**.

  Every finding is fixed or recorded in A §8 as residue, by round and finding id.
- **Owner ruling (R3B DEFECT-1).** Retention is suspended through recovery, in the job and in the server defaults (`BackupID` −1). It is restored after AC-4's first drill as `2W:1D,6M:1W,2Y:1M,5Y:2M`. That first pass deletes 5 of the 9 old dlists, 09-18 among them, so A0 cannot be re-run afterwards; the five are copied aside first. `keep-time` and `keep-versions` defaults are never restored.
- **Artifact versions:** wrapper 2.4.0, installer 1.5.1, re-key 1.3.0, gate 1.2.0, hand start 1.3.0, snapshot 1.2.0.
- **Five new suites, 122 tests:**
  - `tests/test_duplicati_wrapper_contract.py` (53)
  - `tests/test_duplicati_installer_real_path.py` (18)
  - `tests/test_backup_rekey_real_path.py` (25)
  - `tests/test_a0_restore_scripts.py` (17)
  - `tests/test_clear_stop_backup_design.py` (9)
- **The fleet PRs the 2026-10-04 handoff listed** (#2119, #2121, #2124, #2127–#2129, #2137, #2138, #2140, #2159) were all closed by the flood-3 sweep before this session.

## Remaining

1. **B9, as its own PR**: a gitleaks content rule plus a pre-commit hook (A §6.2 row B9; read it first).
   - Go is at `/snap/bin/go`.
   - The repo setting `secret_scanning_non_provider_patterns` is the owner's to change. Do not change it.
2. **Owner actions.** These are not a session's to do; list them for the owner.
   - **The watchdog deploy:** `bash util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id 2`. Until it runs, every 12:00 check records `JOB_MISSING`.
   - **Before §8's install, check the option NAMES in `/etc/duplicati/env`.** An `--option` outside the wrapper's allow-list stops the installer.
   - **Expect one refusal.** The installer refuses `/etc/default/duplicati` as UNBLESSED; re-run it with `--update-backup-behavior`.
   - **Open decision O-12** (env-file mode) is still open. The installer accepts either form.

## Key context and traps

- **The verbatim reports are not committed.** The lane reports' `.md` copies are untracked in this worktree (`golden-floating-willow`), under `util/ad-hoc/2026-10-08_backup-phase-b-{fold-in,round4}/`. The record is their durable copy. `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/resave_reports.bash` re-saves them from the subagent transcripts.
- **Never run pre-commit over untracked report copies.** The whitespace fixers rewrite them, and they stop matching the record.
- **`util/ad-hoc/2026-10-04_save_subagent_report.py` saves an agent's LAST message.** That can be a one-line wait-loop notice. Use `util/ad-hoc/2026-10-08_save_subagent_report_by_heading.py`.
- **Simulate CI's missing mount with a `mountpoint` PATH stub.** Do not edit the wrapper's default: a test pins it on purpose.
- **Signed commits:** `util/open_signed_pr.py`, or `util/ad-hoc/2026-09-23_open_signed_pr_from_file_list.py` for a file list, and `util/push_signed_commit.py` for a follow-up commit (full 40-character `--expected-head`). Rebase a local WIP with `-c commit.gpgsign=false`.
- The sibling worktree `sorted-stargazing-garden` is no longer needed for Phase B. It still holds round 3's untracked drafts; the owner decides whether to sweep it.
- **Bundles:**
  - `Juniper/backups/juniper-ml_feature-backup-phase-b_2026-10-08.bundle` (this session's local branch);
  - `…_wip-backup-phase-b_c3d0e890_2026-10-05.bundle` (the frozen round-3 commit).

## Verify first

```bash
git fetch origin main
git log --oneline -1 cb4d63a4                     # fix(backup): Phase B … (#2199)
gh pr view 2199 --json state,mergeCommit          # MERGED cb4d63a4
grep -n 'B9' notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md | head
bash util/ad-hoc/2026-10-05_reassemble_phase_b_record.bash --check   # IDENTICAL, exit 0
```

Git state at handoff: this worktree's branch `feature/backup-phase-b` holds a local, unsigned WIP commit whose tree equals `main` at `cb4d63a4`. Nothing is staged. Untracked: the verbatim report copies only.

## Limits (unchanged; every lane brief must carry them)

- never start, stop, restart, enable, disable or reload a unit;
- never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`;
- nothing under `/mnt/Backups/Ubuntu/` beyond `stat`;
- never read a secret file;
- never print an environment variable or a token;
- no `git stash`; no interactive shells; no host actions.
