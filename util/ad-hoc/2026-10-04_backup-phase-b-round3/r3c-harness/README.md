# Round 3, lane C — the harness

These are the instruments of round 3's lane C ("run the things"), the lane whose report is the "Round 3,
lane C — run the things" section of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md`.
The lane wrote them on 2026-10-04 in session c9277a65's scratch directory. They were copied here so they
outlive that directory, which is tmpfs.

## Before you run one

- **Every script hard-codes the lane's scratch directory**
  (`/tmp/claude-1000/…/c9277a65-…/scratchpad/val/R3C`), which is tmpfs and will be reaped. Most set it as
  `S=` and expect a `frozen/` copy of the frozen Phase B commit `c3d0e890` under it, so repoint `S=` first.
- **Six do not use `S=`.**
  - Five load a sibling script by an absolute path under `…/val/R3C/bin/`: `t1_b3_redo.py`,
    `t1_empty_new.py` and `t1_stop_block_drift.py` load `t1_gate_attacks.py`; `t4_rerun.py` and
    `t4_timer_state.py` load `t4_rekey_trap.py`. Point each at the copy beside it.
  - `t_record_screen.py` sets `F=` to the `frozen/` copy instead.
- **They were written to run only against scratch copies.** `mkstubs.bash` puts PATH stubs in place of
  `systemctl` and the other host commands. Read a script before running it: none may touch the host, the
  repository or a unit.

## What they are for

The fold-in of round 3 builds its real-path tests from them. That lane found that the suites let 14 of 25
mutants of the new code survive (its D-5).

| Scripts | Subject |
| --- | --- |
| `t1_*` | the clearing script: its declared fence run against stubs, its gates attacked on copies, idempotence, an empty replacement, the STOP block's replacement, and the staged input |
| `t2_rekey_test_hermetic.py` | whether the re-key's dry-run test is hermetic on the owner's host (its D-4) |
| `t3_*` | the installer (dry run, real path, drift), the re-key's dry run, the password-init hand start, the wrapper's argv and env-file deny list, the snapshot lane's WAL claim, and whether one credential file gives all three readers one key |
| `t4_*`, `t5_gate.py` | the re-key's non-dry-run path and EXIT trap, re-runs after a failure, the timer pre-flight, the drop-in it writes, and its gate |
| `t6_mutations.py` | the 25 mutants and which suites kill them |
| `t_record_screen.py` | the archiver's credential screen |
| `mkstubs.bash` | the PATH stubs |

## Changed from the lane's copies

Eight lines, none of which changes what a script does.

Two make the repository's shellcheck hook (`--severity=warning`) pass:

- `t3_installer_real.bash`: `ls "$P"/etc/default/ | grep -c drifted` became
  `find "$P/etc/default/" -mindepth 1 -maxdepth 1 -name '*drifted*' | wc -l` (SC2010).
- `t3_wrapper_paramfile.bash`: the unquoted `$(sed …)` that split `DAEMON_OPTS` into words became an array
  read once before the loop, `"${OPTS[@]}"` (SC2046).

Six clear what CodeQL would raise as review threads, which block a merge here:

- unused imports, removed: `stat` in `t1_fence_snippet.py`, `time` in `t3_snapshot_wal.py`, `json` in
  `t4_timer_state.py`, `re` in `t_record_screen.py`;
- an unused local, removed: `last` in `t3_pwinit.py`'s `show()`;
- an unclosed file: `t3_cr_key.py`'s `open(keyfile, encoding="utf-8").read()` became
  `keyfile.read_text(encoding="utf-8")`, the same read.
