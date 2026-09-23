# Say where §10.2 step 1's restore drill is discharged, and why it cannot precede P0

## The ambiguity

`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` §10.2 opens
with *"it runs after the recovery, not during it"*, and its step 1 reads *"SMART test `sda`;
restore-drill the CURRENT set"*. Together those invite exactly the wrong reading — that a drill
should be run now, ahead of P0.

The SMART half **did** run early, on 2026-09-23, and correctly: you want the disk holding the only
copy proven healthy before anything touches it. That is what makes the drill half look equally
ready. It is not, and an operator who tried would find nothing to drill against.

## Why the drill cannot precede P0

A drill needs a **job index**. §8 P0 step 0(c) already records that the index has to come from
**P0 step 1's freeze**, because `--no-local-db` rebuilds it from all 877 dindex volumes and was
measured at *">30 minutes for a single small file here, without completing"*
(`util/ad-hoc/duplicati_drill_run.py`).

The distinction that makes a drill possible at all — and which is easy to lose — is that the
**server** database is the file locked under an unmatched key (§5.4), while the **job** index
(`BMXWPAOGLP.sqlite`, last written 09-18) is a separate file, and it is the one a drill reads.

## What discharges it

**AC-4's first drill** — from `duplicati-20260918T140000Z`, the pre-recovery fileset — which §8 P0
step 11 already requires alongside the post-recovery drill. §10.2 step 1 now *names* that drill as
its gate rather than implying a second, independent one.

Its terms come from §3.3 item 6 and are restated in the new note so they are not re-litigated by
whoever runs it: never pass `--restore-with-local-blocks` (`--no-local-blocks` is **deprecated** in
2.4.0.0 because not using local blocks is now the default), select by `--time=`, compare **SHA-256
and length** on ≥ 15 files, include a negative control that must fail, and treat the **exit code as
not evidence**.

## Consequence

The closing paragraph now states the operative fact plainly: **the next action in this arc is §8's
P0 recovery, not anything in §10.2.**

## Changes

**Changed**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
(§10.2 step 1 row; new note 10.2c; the closing paragraph).

**Added**: `util/ad-hoc/2026-09-23_clarify_drill_ordering.py`.

No tagged block is touched, so no artifact changes.

## Verification

- `markdownlint 0.42.0` (pinned hook version) — exit 0.
- `util/ad-hoc/2026-09-22_stage_design_artifacts.py --check`: **0 staged, 13 already current**.
- Edit script idempotent; second run reports every edit `ALREADY` and writes nothing.
- The `edit()` substring guard **fired during authoring** on the note-insertion edit, whose anchor
  preceded the insertion point rather than spanning it — the third time that guard has caught a
  non-idempotent edit since it was added on 2026-09-22. Anchor widened; no double-application
  reached the document.

## Requirements

References JR-DEP-SEC-005.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_016TcEz8juUrgh8PWf2LqZGX
