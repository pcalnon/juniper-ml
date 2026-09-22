## Summary

Reconciles **consensus round 1** into the backup infrastructure design, then **rounds 2 and 3** into the
result, and stages the thirteen artifacts §8 tells an operator to run — which until now existed only as
fenced code blocks inside the document.

82 reconciliation edits, then 113 correction edits, applied by two chained scripts that rebuild the document
from its pristine `origin/main` blob on every run. Re-running them reproduces the result byte for byte, so the
edit set is re-derivable rather than remembered.

The arc was paused by the owner on 2026-09-21 with four of round 1's six lanes unapplied and a STOP warning
at the top of §8. That warning is now gone, and §8 is executable — in a stated order, behind stated owner
gates.

**Nothing in §8 was executed. No live system state was changed.** The one production-visible change is
`scripts/duplicati-wrapper.bash` (see **Impact** below).

## Context

- Design of record: [`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`](../../../notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md)
- Round 1's six verbatim reports: [`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`](../../../notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md)
- Rounds 2 and 3's five verbatim reports, **new in this PR**: [`notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`](../../../notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md)
- Procedure: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- Instruction that scoped this work: [`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`](../../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md)

## What round 2 caught, and why it mattered

Round 2 validated the *reconciliation*, and found that it had introduced defects of its own — several in the
exact areas round 1 had just corrected. The five that would have cost the most:

1. **Both Procedure A0 scripts could not run.** They `.`-sourced `~/.config/duplicati-backup/env`, whose
   `PASSPHRASE` is unquoted and carries `$ & @ # ^`. Under `set -u` that aborts *and echoes a fragment of the
   live passphrase to stderr* — the channel §6 exists to close. A0 is the **preferred** recovery route, so the
   failure would have pushed the operator to a destructive wipe or a full rebuild. Both scripts now parse the
   file, as `util/ad-hoc/yamaguchi_build_job.py:57-63` already did. Measured with the new
   `util/ad-hoc/2026-09-22_credential_file_shape.py`: `dot-sourceable=NO`.
2. **`ReadWritePaths=` was one directory too high.** It opened `…/Dropbox/Backups`, whose children —
   `_yamaguchi_keys/` (the passphrase escrow) and `_yamaguchi_frozen_20260826/` — are `drwxrwx---
   pcalnon:duplicati` with **no sticky bit**. The confined service could read *and unlink* the only key custody
   T1 and T1c have, with the deletion propagating to Dropbox, contradicting §8's own "nothing is deleted or
   moved" rule. Now scoped to `…/Backups/Yamaguchi`, with the escrow additionally masked.
3. **Two `Environment=` lines were inert.** `DUPLICATI__DISABLE_UPDATE_CHECK` and
   `DUPLICATI__USAGE_REPORTER_LEVEL` do not exist in the install — verified across all 1,443 files in **both**
   UTF-8 and UTF-16LE with the new `util/ad-hoc/2026-09-22_duplicati_literal_scan.py` (an ASCII-only grep gives
   false negatives, because .NET stores user strings as UTF-16LE). Replaced with the names the software reads,
   plus `--disable-update-check` in `DAEMON_OPTS` where AC-14's grep can see a typo.
4. **The step-3 probe's negative control could not fail**, and the reconciliation had **regressed** a round-1
   fix by putting the candidate key back on `systemd-run`'s argv. Both fixed; the key now travels by a 0600
   `EnvironmentFile`, and a harness error reports `INDETERMINATE` instead of "key rejected" — the direction
   that would have discarded a *correct* key.
5. **`sqlite3` is not installed on this host**, so the probe's containment queries returned empty and its
   refusal misreported a query failure as *"the copy is cleartext"* — which §4.2 and §5.4 have primed the
   operator to read as "the second key-free recovery source is found". Preflight added.

Round 2 also corrected a claim in §7.3.3 that had it backwards: 2.4.0.0 **warns and continues** on an
unrecognised option, so a `.env` typo is a silent misconfiguration rather than a start failure. **AC-14** now
pins the journal grep, because nothing else can catch that class.

## What round 3 caught

Round 3 read a **frozen** document and confirmed 13 of round 2's 20 corrections outright, found 6
present-but-incomplete, and swept every internal cross-reference — 15 defects, all applied here. Its sharpest
finding is the one round 2 created: the **P0.5a/P0.5b split was made by adding headings, not by relocating
content**, so the re-key procedure was still printed in full inside the list headed *"before anything in P0"* —
the exact ordering error the split exists to prevent. An operator working that list top to bottom would have
run it before the data folder it operates on existed. Also: `usermod` was announced as moved from P4 but only
copied, nine references still said bare `P0.5` (three landing on the wrong half), §8 still claimed nine scripts
did not exist when nine of ten had been staged, and §11 stated round 3's verdict before round 3 had run.

## A procedure failure, recorded rather than buried

The design was edited **while two round-2 lanes were still reading it**. The security lane saw three
different sizes and handled it correctly — pinned a sha256 snapshot, cited by heading text, and reported two
of its own findings as AGREE-with-corroboration rather than claiming them. Consequence: any line number in
round 2's reports is void. §11 of the design and the round-2 record both say so, and both draw the lesson:
**freeze the artifact for the duration of a round.**

## Changes

### Added

- `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` — rounds 2 and 3's five reports, verbatim.
- **Thirteen staged artifacts**, extracted from the design's own tagged blocks: `util/systemd/duplicati.service`, `util/systemd/duplicati.default`, `util/systemd/juniper-backup.{timer,path,service}`, `util/yamaguchi-pre-backup-guard.bash`, `util/install_duplicati_service.bash`, `util/juniper-backup-scheduled.bash`, `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`, `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash`, `util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`.
- Six instruments: `util/ad-hoc/2026-09-22_reconcile_backup_design.py`, `…_apply_round2_corrections.py`, `…_stage_design_artifacts.py`, `…_credential_file_shape.py`, `…_duplicati_literal_scan.py`, `…_archive_consensus_reports.py`.

### Changed

- `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` — 1,232 → ~2,000 lines. Status flipped to VALIDATED (round 2); §8's STOP block removed; Procedure A0 added ahead of A; P0 renumbered 0–11 with a new P0.5a/P0.5b; `DBPath` re-pointing made common to all four procedures; §7.3.2's confinement set; S-7, S-8 and a sink checklist in §6; D-13 and D-14; AC-13 and AC-14; §11 and §12 rewritten.
- `scripts/duplicati-wrapper.bash` — replaced with the §7.3.3 rewrite. **This removes the burned 36-character settings key literal from a public repository** (P1 step 3, S-1).

## Impact and risk

**SemVer**: none — no packaged code. `juniper-ml` is a meta-package and none of these paths ship in a wheel.

**The one production-visible change** is `scripts/duplicati-wrapper.bash`, because
`/home/duplicati/bin/duplicati-wrapper.bash` is a symlink into the primary checkout. It takes effect only on
`git pull` **and** a service restart. Assessed before making it: the loaded `ExecStart` passes
`'--daemon-opts="${DAEMON_OPTS}"'` as one word, which v2 rejects with a clear `exit 78`; the current wrapper
fails the 0700 data-folder gate on that same restart anyway. So the swap cannot make the present situation
worse, and it removes a published credential. **The service is down and must not be restarted** until §8 P0
installs the corrected unit and sets the data folder to 0700 — that is unchanged by this PR.

## Testing

| Gate | Result |
| --- | --- |
| Pinned markdownlint 0.42.0, **no `--fix`**, on both notes documents | exit 0 |
| `util/ad-hoc/2026-09-21_lint_design_snippets.py` | `blocks: 14  failures: 0` |
| `pre-commit run --files` over all 18 changed paths | all hooks pass |
| Artifact staging re-run | idempotent (`0 staged, 13 already current`) |
| `systemd-analyze security` on the staged unit | **1.7 OK** (was 5.2 MEDIUM before round 1's hardening) — independently reproduced, and AC-12's gate re-based on it |
| Consensus | round 2 (four lanes) + round 3 (confirmation pass), all five reports archived verbatim |
| Round 3's independent re-measurements | `1.7 OK` and all 15 ✗ rows, the 53/18 syscall-set numbers, the 1,443-file scan, and **byte-identity of all 14 tagged blocks against their landed copies** |

Two findings were verified independently of the agent that raised them: the escrow directory really is
group-writable with no sticky bit, and neither `DUPLICATI__*` environment name exists in the install.

## Requirements

References JR-DEP-SEC-005 — §6's detection-gap paragraph and P0.5a item 6 specify the gitleaks **content**
rule and pre-commit hook that close the allowlisting bypass for this secret class. This PR specifies it and
removes one published literal; it does not implement the rule, so the requirement stays open.

## Follow-ups (not in this PR)

- §8 execution is owner-gated: P0 step 0 requires rulings on D-1, D-4, D-6, D-9, D-14 and a decision on D-2.
- `sqlite3` and `gitleaks` are not installed; P0 step 3 needs the first, AC-8 the second.
- `util/install_juniper_backup_timer.bash` is a P3 deliverable and is deliberately absent.
- Appendix C items 1–10 are corrections *recorded* here and not yet applied to their target documents.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_016TcEz8juUrgh8PWf2LqZGX
