# D-8's one scrub runs before P0, P0's gate and the STOP's scope are ruled, and §8 goes behind a STOP — validation found defects in the procedure itself

## Summary

**Landed on 2026-10-03 as Phase A of `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` (§6.1).** The change was paused mid-round-8 on 2026-09-24 as three local-only commits; this session folded round 8's corrections into the edit script and the record (the consolidated handoff's sub-steps 1a–1h), rebuilt the design from `6c23fdde`, ran the gates, and validated the delta with one narrow lane (below). Nothing on `main` had touched the nine files since that base. Merging the record discharges the release's second limit: every validation round of this arc is now archived verbatim on `main`, so the transcript sink may be purged.

This change records three owner rulings of 2026-09-24 in the backup design of record,
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`. It also repairs text
the 2026-09-22 rulings left stale, corrects two defects of fact, adds the six §12 rows that were owed, and
adopts the owner's SMART-script refactor that closing ml#2045 dropped. Together those discharge items 3, 4
and 5 of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_backup-arc-seven-decisions-ruled-smart-passed-p0-is-next.md`.
Items 1 and 2 were done before this session: ml#2067 merged as `dcfc024f`, and ml#2073 archived the handoff.

Validating the first draft found **defects in §8's procedure itself**. Three were re-derived from source as
high severity. An operator following §8 literally could re-lock the recovered database, pass the pre-backup
guard without its `TargetURL` check, or copy a cleartext database into the backup Source. The owner ruled
that this change stays narrow: it puts **§8 behind a STOP** that lists the defects, and a follow-up change
fixes the procedure.

**Nothing on the host was executed or changed.** `duplicati.service` is still the empty server, `active` as
PID 1397393 since 2026-09-20 18:19:42 CDT.

## The rulings

**D-8 is amended: the one scrub runs before P0**, as P0.5a item 4 (note 10.1e). The 2026-09-22 ruling said
"scrub once, after P1", but P0.5a item 4 had scrubbed before P0 since ml#1999 merged that morning. The
ruling was made from §10's Recommendation column, which nobody updated after round 1 moved the scrub and
round 2's split made it P0.5a item 4. Note 10.1e records why "once" holds:

- The three leaked label families came from wrapper revisions that printed them unconditionally.
  `DEBUG_MODE` gated them from `64677ab0`, and wrapper v2 prints none of them.
- S-6's sign-in URLs are the one family a later start re-emits. They expire, so §10.2 step 2 counts only
  unexpired ones.
- A vacuum after P1 would also delete the journal of the recovery itself.

**P0's gate** (note 10.1f): P0.5a items 1, 2 and 4 run before anything in P0. Items 5–7 run alongside:
item 7 before step 8's first start, item 5 before step 10's `resume`, and item 6 at any point. The ruling
set no order among items 1, 2 and 4. The design runs them in number order because item 1 must precede
item 4.

**What the STOP holds** (note 10.1g):

- **Held**: P0.5a items 2 and 4, P0, P0.5b, P1, P2 and P4.
- **Released**: P0.5a items 1, 5, 6 and 7, and P3 (its step 3 still waits on D-5). Also released: §6's sink
  checklist, S-4's `chmod 0600`, and anything that only reads.
- **Two limits on the release**: no history file is wiped before P0 step 3 has tested the key candidates it
  may hold, and no transcript is purged before this arc's reports are archived.

**Two readings for the owner to confirm or widen.** Validation found two of the ruling's phrases wider than
they look, and the design now reads both narrowly, saying so in note 10.1g:

- **"Only reads"** means reads that write nothing and run no Duplicati binary. P0 step 0(c) calls itself
  read-only, but it runs `duplicati-cli` with the passphrase from `/usr/lib/duplicati` — still `755
  duplicati:duplicati`, so the service user can swap the binaries — and it needs P0 step 1's freeze, which
  writes.
- **"This arc's reports"** means every round of the arc, including any still running and the follow-up's own,
  archived verbatim into a record merged to `main`.

New note S-now maps each §6 exposure's action to its §8 step, and says which of those the release lets run
now.

## §8 behind a STOP

Five defects, re-derived from source, head §8:

1. **Step 0(a) cannot pass where it sits.** Nothing yet installs the flag or the blessed file it checks.
   The flag also has no durable home under D-6's drift gate.
2. **P1 step 1's key command overwrites the old key** before the first re-key start needs it.
3. **Step 10's guard dry-run can pass without its `TargetURL` check.** Step 9's client change has not
   landed, and the guard skips that comparison on an empty URL.
4. **Restarting the snapshot timer after step 8 can copy A0's cleartext database into the backup Source.**
   The timer is `Persistent=yes`.
5. **`ProtectSystem=strict` without `ReadWritePaths=` breaks the snapshot.** P0.5a item 2 and §7.7 both
   prescribe it.

Also re-derived: D-9's two web-service flags are installed by no artifact and no step, and round 3's D13
(the `.env` path) is still open. Three more matter because of the release:

- no P0 step 3 procedure extracts key candidates from the history files without printing them;
- P1 step 4's `cp -a` nests a second copy if P0.5a item 5 already made one;
- the unit's `InaccessiblePaths=` does not mask the copy item 5 makes outside the Dropbox root.

Still to be re-derived: P0.5b's premise and placement, Procedure B's start before step 8, items 5 and 7's
trigger events, and the lower-severity items the record lists.

## Other corrections

- **Stale text.** The front matter's status and order, §8's step −1 paragraph, P1 steps 3 and 5, P2 step 2,
  §10's preface, §11's round-3 count and D-14 dissent, and note 10.2a's dead "§12" citation.
  `stage_design_artifacts.py --check` exits 0 even on drift, so step −1 now says to read its count.
- **§6.** S-2's value *is* the live passphrase, so the settings-key re-key does not retire its lines. New
  note S-3c names two exposures D-2 does not reach: the frozen 811-volume copy and `PASSPHRASE_OLD`.
- **Host state that moved during the session.** Both `su - duplicati` shells and the root `vim` had
  exited, so §6's rows for them are overtaken. Note sink-b gives the owner a count-only check of
  `/home/duplicati/.bash_history` — case-insensitive, never wiped on the count.
- **"All 877 dindex volumes".** The destination holds 434 dindex, 434 dblock and 9 dlist files. The ">30
  minutes" figure was ml#1268's, measured against the old `Ubuntu` archive.
- **§11 and §12.** §11's "15 defects, all applied" becomes 13 of 15 (D11 and D13), in the round-2 record
  too. §12 gets its six owed rows, and note 10.2b moves ahead of 10.2c (one of ml#2045's changes).
- **The SMART script** keeps the owner's `b0223f18` refactor, with one `date` call instead of two, since
  two calls can straddle midnight. The header drops the dead `SC2034` directive and no longer calls the
  device palette an inventory. It stays `100644` (`createCommitOnBranch` carries no mode), so run it with
  `sudo bash`. ml#2045's re-padding of four tables is declined.

## Changes

**Changed**:

- `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
- `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` (one sentence)
- `util/ad-hoc/smart_checks_backup-sda.bash`

**Added**:

- `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`: the reports of
  rounds 4 to 8 verbatim, lifted from the subagents' own transcripts, behind a disposition table
  per round.
- `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`: 64 anchor-asserted edits,
  rebuilt from `6c23fdde`, with gates checked before any write and a `--self-test` that watches each gate
  fail.
- `util/ad-hoc/2026-09-24_archive_round4_reports.py`
- `util/ad-hoc/2026-09-22_backup-design-round2/ROUND4_RECORD_HEADER.md.in`: the record's authored preamble and disposition tables (the archiver's `--header`; `.md.in` so the link validator does not resolve its notes-relative links from `util/ad-hoc/`).
- `util/ad-hoc/2026-09-22_backup-design-round2/COMMIT_BODY_D8.txt` and `…/PR_BODY_D8_AMENDMENT.md`: the commit body and this body.

No tagged block is touched, so no staged artifact changes.

## Verification

| Gate | Result |
| --- | --- |
| Edit script, from `6c23fdde` | 64 applied; a re-run reports `no change (64 edit(s) already applied) -- idempotent` |
| Its pre-write gates | no new line over 512 characters; every fenced block byte-identical (20 in the design, 82 in the round-2 record); no stale phrase in either file |
| `--self-test` | 8 of 8: the control passes, and each gate refuses its mutant |
| `util/ad-hoc/2026-09-22_stage_design_artifacts.py --check` | 0 staged, 13 already current |
| `util/ad-hoc/2026-09-21_lint_design_snippets.py` | blocks: 14, failures: 0 |
| markdownlint 0.42.0 (the pinned hook), run directly | exit 0 on all three notes |
| flake8 `--max-line-length=512` on both scripts | clean |
| `/opt/miniforge3/bin/pre-commit run --files` on the nine paths | every applicable hook passed (`Validate documentation links` included, after the header rename) |
| `util/markdown_structure_delta.py --base 6c23fdde --head <wip>` | 0 regressions across the 121 markdown files touched since that base |
| `juniper-symbol-loss-check` / `juniper-docs-additions-check` (`origin/main..<wip>`) | no unwaived symbol-loss findings / no unwaived docs-deletion findings (one `WARN/small-deletion` on the round-2 record's one-sentence change) |
| shellcheck 0.10.0 (pinned) on the SMART script, every severity | 0 findings |
| Record screen | no credential-shaped token, no email, no agent id |

## Validation

One narrow lane on the round-8 delta (the SOP applies because the owner's sweeper arms open PRs), briefed to refute, 53 tool uses, pins matched on entry and exit. Four checks, all re-derived from source:

1. **Rebuild identity** — from `6c23fdde` on a scratch tree: 64 edits applied, the rebuilt design and round-2 record byte-identical to this branch's (sha256 `5d875ed9…`, `5dc7b533…`); a second run `no change … idempotent`; `--self-test` 8 of 8. CONFIRMED.
2. **Verbatim reports** — all eleven re-extracted independently from the transcripts with the archiver's own definition of "final assistant text": character counts and sha256 match for every one; every final record is `end_turn` with no API-error flag (round 6's two lanes carry a mid-run session-limit record, then a resume, then a genuine report); the archiver re-run from the pinned header reproduces the record byte-for-byte; credential, email, agent-id and session-id screens all zero. CONFIRMED.
3. **The owner's words** — the STOP block's Held and Two-limits bullets and note 10.1g quote the ruling as both handoffs carry it; the Released bullet and the front-matter bullet paraphrase, and each marks the design's narrower reading as a reading. CONFIRMED. The lane found the record's **round-7 disposition preamble** still naming `"only reads"` and `"this arc's validation reports"` as the ruling's phrases — REFUTED, record-only; corrected in the header before landing (the round-8 paragraph had it right, so the two had contradicted each other).
4. **The round-8 disposition table** — every row's disposition re-found in the design as rebuilt; no round-8 finding without a row; the three round-7 rows round 8 called false (A6, B13, B18) say so. One row REFUTED on wording: B1's disposition claimed a "count by value from a 0600 file" method that the design's note sink-c does not give (it says the method is follow-up) — corrected in the header before landing. The table's intro also now says the three out-of-scope items are follow-up, not applied.

Both corrections are in `ROUND4_RECORD_HEADER.md.in`; the record was regenerated from it and the pins re-taken. The lane also noted that the consolidated handoff's "two narrow readings" bullets still quote the pre-round-8 phrases — that file is UNVERIFIED-labelled there and is corrected separately.

## Requirements

None. P0.5a item 6, the secret-detection gap, is untouched here.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_0191VV1XpodPzP6sovMEhxpC
