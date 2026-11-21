# Handoff: backup Phase D -- step 14's tools are merged; the sitting resumes at C.1, drills unblocked again

**Date**: 2026-11-14 (facts read between 10:11Z and 22:40Z unless a time is given)
**Session**: host yamaguchi, worktree `juniper-ml/.claude/worktrees/humble-dreaming-quail`. It acted on the worktree
`W` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swift-stargazing-spindle`.
**Predecessors, on `main`**:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_backup-phase-d-tools-pr-last-commit-built-step-14-checks-not-started.md`
(below: `HANDOFF_2026-11-13_…md`; its step A is DONE), and through it
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_backup-phase-d-step14-tools-pr-open-false-alert-source-found.md`
(below: `HANDOFF_2026-11-12_…md`). **Read `HANDOFF_2026-11-12_…md` first**: its steps C.1 to C.11, its open questions (Q1 to Q4,
Q6 to Q8), its Key context and its limits still hold, except where this file says otherwise.

---

## Goal statement

1. Continue the Phase D sitting at step C.1 of `HANDOFF_2026-11-12_…md`. None of C.1 to C.11 has run.
2. Carry the open questions to the Overtoad (first: Q7 before the retention save of C.4, and whether the probe may list the
   destination's file names; then Q2, Q3, Q6; then Q1, Q4, Q8).

The working pattern holds: the Overtoad runs every command that changes the host or reaches the server and pastes summary
lines; the session checks read-only, keeps the running record, names each next command with its expected output.
Ask the Overtoad for merge approval again in a new session.

### What changed since `HANDOFF_2026-11-13_…md`

- **juniper-ml#2548 MERGED** on 2026-11-14 at 11:04:33Z as `76488449` (squash of `dfef5f01`). update-branch `165c513f`
  (10:14:28Z); the last commit was rebuilt for 2026-11-14 (242 suites) and pushed as `dfef5f01`, whose tree equals a probe
  commit that passed both sequence-safety screens. On `main` the CHANGELOG entry sits under `[Unreleased]` / `### Added`, the
  juniper-ml#2559 entry under `### Fixed` (step A.7 done). The three post-merge runs on `76488449` succeeded.
  - The squash message is GitHub's default concatenation, not `final-squash-body.md`: `util/safe_merge.py`'s local merge
    (no body flags) beat the re-armed auto-merge net. Nothing depends on it. Recorded in the memory note
    `reference_squash_body_excludes_merge_commits.md`; a fix to `safe_merge.py` is an open follow-up.
- **`D`**: the tools are on `main`. The primary checkout was at `4a786c81` when #2548 merged. After the Overtoad runs
  `git -C /home/pcalnon/Development/python/Juniper/juniper-ml pull --ff-only`, `D` can be the primary. Until then `D` = `W`
  (detached at `165c513f` with the five built files: the same content as `main`). The seven SHA-256 prefixes in `W` match
  the list in `HANDOFF_2026-11-12_…md` ("Key context").
- **The host's Python, 2026-11-14.** Between 08:14Z and 09:19Z `/usr/bin/python3` was switched to 3.15.2 (apt `python3.15`,
  alternatives priority 90) and `JuniperCascor1`'s `bin/python`, `bin/python3`, `bin/python3.1` were re-pointed from
  `python3.14` to `/usr/bin/python(3)`. Under 3.15.2 the AC-4 driver could not import `cryptography`'s ciphers, so drills
  would have read `ERROR`. **The Overtoad deferred the default switch**: at 22:20Z `/usr/bin/python3` is 3.14.4 again
  (alternatives manual mode) and the driver's import works. **`JuniperCascor1`'s three links still point at `/usr/bin`**:
  that env's `python3` runs the system 3.14.4 without the env's packages, and its console scripts fail. The restore (three
  `ln -sfn python3.14 …` commands) was offered to the Overtoad and not run. It does not affect the drills (the tools run
  `/usr/bin/python3 -I`). Memory: `project_host_python3_switched_to_315_2026-11-14.md`.
- **Host, read-only, 10:18Z:** no aside directory, no `~/.local/state/duplicati/acceptance.json`, no probe unit. Watchdog
  records of 11-11, 11-12 and 11-13 all read `OK RUNNING` (task ids 46, 48, 49). Q6 asks whether such a day counts for AC-5.
- **Running record**: 792 lines, `W/tmp/phase-d-sitting/running-record.md`, rebuilt by `W/tmp/phase-d-sitting/assemble_record.py`
  from the segments (this session's: `segment-2026-11-14.md`) and archived to the primary's `tmp/phase-d-sitting/`.

### Remaining work, in order

**B. The sitting**, steps C.1 to C.11 of `HANDOFF_2026-11-12_…md`, with `T="$D/util/ad-hoc/2026-11-11_phase_d_finish.bash"`:

1. C.1 (root): `bash "$T" status --backup-id 2`; if it lists `/root/phase-d-tmp/ac4-20260918T140000-20261109-050909`, then
   `bash "$T" shred --run-dir <that path>`. It runs under 3.14 or 3.15 alike.
2. C.2 (root): `bash "$T" drill 1`, after that day's backup has finished (the job starts 14:00Z and has run 6 to 12 h; the
   tool refuses while the server reports an active task). Check `/usr/bin/python3 --version` is 3.14 first.
3. C.3 to C.11 as written there.

**C. For the Overtoad**: the open questions, as in the goal.

**D. The record PR** (C.10): add this file's findings: the 11-14 Python switch and its effect on the drills; `safe_merge.py`'s
local path and the squash text; the regression runs on 3.15.2 (227 of 243) against 3.14.7 (239 of 243).

## Verification commands (start of the next thread)

```bash
gh pr view 2548 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit --jq '"\(.state) \(.mergedAt) \(.mergeCommit.oid)"'
/usr/bin/python3 --version
/usr/bin/python3 -I -c 'from cryptography.hazmat.primitives.ciphers import Cipher; print("AC-4 import ok")'
ls -l /opt/miniforge3/envs/JuniperCascor1/bin/python3
git -C /home/pcalnon/Development/python/Juniper/juniper-ml log -1 --format=%h   # run by the Overtoad; a worktree session is refused
tail -n 20 /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swift-stargazing-spindle/tmp/phase-d-sitting/segment-2026-11-14.md
```

**Expect:** `MERGED 2026-11-14T11:04:33Z 76488449…`; Python 3.14.x; `AC-4 import ok`; the link target (`python3.14` once
the Overtoad restored it, `/usr/bin/python3` before); the primary at `76488449` or later once pulled; the segment's last
lines naming the three green post-merge runs.

## Git status at handoff

- `main` holds juniper-ml#2548 (`76488449`). No PR of this arc is open, except the one that carries this file.
- `W`: HEAD detached at `165c513f`, five files modified (= `main`'s content). **Do not remove `W`, or the worktree
  `parallel-strolling-meteor`,** until the record PR has merged: their `tmp/` hold the scripts, the running record, the
  alert traces and files the primary's archive lacks.
- This session's worktree `humble-dreaming-quail`: `tmp/backup-phase-d-2026-11-14/` holds its check scripts, the
  Python 3.14.7 PATH shim (`py314-bin/`) and the `safe_merge` log.
