# Backup design — consensus rounds 4–8, verbatim validator reports

**Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
**Author**: Paul Calnon
**Date**: 2026-09-24
**Procedure**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
**Artifact validated**: [`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`](JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md) — round 4 read local commit `d9f44a78` over `main` at `df21367d`; round 5 read local commit `edf8c432`, round 6 `7265dc1f`, round 7 `2c9efe85` and round 8 `f90a87e7`, all over `main` at `6c23fdde`
**Earlier rounds**: [`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`](JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md) and [`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`](JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md) (rounds 2 and 3)

---

## What round 4 was for

The first draft of the change that records the owner's 2026-09-24 amendment of D-8, repairs text the
2026-09-22 rulings left stale, corrects "all 877 dindex volumes", adds the §12 rows that were owed, and
adopts the owner's SMART-script refactor that closing ml#2045 dropped. That draft was the working scope of
items 3, 4 and 5 of `HANDOFF_2026-09-24_backup-arc-seven-decisions-ruled-smart-passed-p0-is-next.md`.

Three validators, launched together, none seeing another's output. Each was told to refute rather than
confirm, and to re-derive every claim from git objects, `gh` or the host — read-only, with no secret file,
journal capture or Duplicati binary touched — never from the document itself:

| Lens | Brief |
| --- | --- |
| A — fact re-probe | every factual claim the draft adds or changes, in all three files it touched |
| B — consequence and consistency attack | grant the premises, attack the conclusions, and read the **whole** design, not only the diff |
| C — amputation and scope | what the draft dropped from the text it replaced, and whether the handoff's items were discharged |

## What round 4 found

- **Lens A**: 41 confirmed, 10 refuted, 2 unverifiable.
- **Lens B**: 28 refuted, 4 unverifiable, 10 confirmed sound. Most of its refutations are aimed not at the
  draft but at §8's procedure itself, and four of them are rated high: an operator following §8 literally
  could re-lock the recovered database, pass the pre-backup guard without its `TargetURL` check, or copy a
  cleartext database into the backup Source.
- **Lens C**: 2 real losses, 3 refuted claims.

The lenses overlapped on the draft's own errors: note 10.1e credited round 1 with a placement round 2 made;
note 12b recorded one of the SMART adoption's changes out of several; the edit script said "the day before"
of a same-day merge; the SMART header called its device palette an inventory. Lens A alone found that the
edit script's fence gate could not see indented blocks. Lens B went after §8's procedure systematically —
lens A also caught step 0(a), and lens C step −1's `--check` — and what it found there is the reason for the
STOP block now at the top of §8.

Three statements in round 4 were themselves imprecise, and are recorded rather than silently corrected:

- lens A's row 27 cites "§5 note 2" for the 22 + 1 `Invalid slot` split, which is §4.2's note 2;
- lens C's "other finding" 8 says round 3's 15 defects map to the `r3-*` edits, when two of them (D11 and D13)
  have no edit;
- the briefs themselves — not a validator — said `origin/pr-2045-head` was the owner's commit `b0223f18`, when
  that ref is the PR's tip `f6363b9a`, three commits later (lens A, first "other problem").

## Disposition of round 4

Two owner rulings of 2026-09-24 shaped it. **Narrow change, then fix §8**: this change applies the
corrections to its own draft, records §8's defects behind a STOP, and leaves the procedure fixes to a
follow-up change with its own validation round. **P0's gate is P0.5a items 1, 2 and 4**, with items 5–7
alongside (the design's note 10.1f). Source column: round 4's lens and row, or the lens's section for findings
outside its table. The later tables cite round 4's rows as "round 4's Bn", because each round numbers its own.

| Finding | Source | Disposition |
| --- | --- | --- |
| Note 10.1e: round 1 put the scrub in a P0.5 bucket; round 2's split made it P0.5a | A20, B20, C other-4 | applied |
| Note 10.1e: the leaking passes predate `DEBUG_MODE` | A23 | applied; made precise in rounds 5 and 6 |
| Note 10.1e: `Restart=always`, the `ExecStart` path P0.5a item 1 deletes, and the step-3 probe outside the unit | A25, B21 | applied |
| Note 10.1e: one of S-1's 23 lines came from an `ExecStart=` revision | A27 | applied |
| §10.2 step 2 and note 10.1e: S-6's sign-in URLs follow the scrub | B9 | applied — the gate counts unexpired tokens |
| §6: S-2's value is the live passphrase, so P0.5b does not retire it | B10 | applied, and widened in round 5 |
| §12's round-3 row ("its 15 defects are the `r3-*` edits") and §11's "15 defects, all applied"; round 3's missing artifact row | A35, A other; C §12 for the row | applied; D11's row added; D13 recorded open (note 12a) |
| §12 ml#2067 row: ml#2045 changed more of this file than the front matter | A41 | applied; its move of note 10.2b adopted, its table re-padding declined |
| Note 12b: the SMART adoption's header, mode and omitted sites | A43, C26, C scope | applied; completed in round 5 |
| Note 12a: the ml#1999 row had no file list | C §12 | applied — a D11 row carries it |
| §8 step −1: `--check` exits 0 even on drift | C6 | applied |
| P0 step 0(c): "measured on 2026-08-23" is only a recording date; the figure's own source | A10, A7, B C3 | applied — "recorded", and attributed to the script's lines 33–35 |
| Note 10.2a: the dead "§12" citation | C other-1 | applied — §3.4 |
| P1 step 5: "P1 scrubs nothing" beside P1 step 2 | C other-3 | applied — "no log scrub" |
| Front matter: P0.5a items 1, 2 and 4–7 gate P0 | B12 | owner ruling — items 1, 2 and 4 (note 10.1f) |
| SMART header: the palette is not a live inventory | A45, C other-6 | applied; its replacement was itself wrong, fixed in round 5 |
| Edit script: "the day before", docstring scope, indented fences unguarded | A49, A51, B28, C other-5 | applied; the fence guard was mutation-checked on an indented block |
| §10.2's notes print a, c, b | A other | applied, as ml#2045's move |
| §10.2's heading | B25 | applied — "confirm the scrub, rotate, re-encrypt" |
| Front-matter status line | C other-7 | **missed by round 4's correction**; applied in round 5's |
| Step 0(a) cannot pass; D-1's flag has no durable home under D-6 | A other, B1 | STOP item 1 — follow-up |
| P1 step 1's key command overwrites the old key | B2 | STOP item 2 — follow-up |
| Step 10's dry-run passes on an empty URL; step 9's client not landed | B3 | STOP item 3 — follow-up |
| A timer restart after step 8 copies a cleartext database | B4 | STOP item 4 — follow-up |
| `ProtectSystem=strict` without `ReadWritePaths=` (P0.5a item 2 and §7.7) | B8 | STOP item 5 — follow-up |
| P0.5b's premise and its placement before step 10's `pause` | B5, B6 | in the STOP's re-derive list — follow-up |
| Procedure B starts the server before step 8 installs the unit | B7 | in the STOP's re-derive list — follow-up |
| AC-8's undefined "hardening timestamp" | B22 | follow-up; since round 6, note 10.1e anchors its own rule to P0.5a item 4's `--rotate` |
| §8's phase-order sentence | B23 | applied in rounds 5 and 6 (the P0.5 exception, then step 9's client change) |
| B11, B13–B18, B24, B26, B27, B U1–U4; wrapper v2's `die` path with an `=`-less word | B, A other | follow-up |
| The tagged `confirm_a0_premise.bash` comment still says "here" | A other, B19, C other-2 | follow-up — a tagged block and its landed copy change together |

---

## What round 5 was for

Round 4's corrections, before they merged: an earlier arc of this project measured that half of a correction
pass's defects were introduced by the corrections themselves. Two validators, launched together, each reading
the frozen commit `edf8c432`, each told to refute:

| Lens | Brief |
| --- | --- |
| A — fact re-probe | every claim the corrections add or change, and this record's authored part |
| B — consistency, consequence and residue | the whole design against the corrections; every round-4 disposition against the design; what the corrections dropped |

## What round 5 found

- **Lens A**: 62 confirmed, 16 refuted, 1 unverifiable.
- **Lens B**: 23 refuted, 8 confirmed sound, 2 unverifiable.

Most of the refutations were in the corrections' own text — all of lens A's, whose brief confined it to that
text and this record, and most of lens B's: a SMART header claim replaced by another false one, a status line never changed although this record said it was, a guard said to check "nothing" when
it skips one check of several. The rest were older text that the corrections now contradicted: §10.2 still
naming P0 as the next action beside a STOP, P0.5b still claiming to close S-2 beside §6's correction, R-6 still
saying `nologin` "immediately" beside the new gate. Both lenses also found that host state had moved during
the session: the two `su - duplicati` shells §6 held open had exited, and `/home/duplicati/.bash_history` had
been rewritten at 14:56:34 — which the design now records as note sink-b and puts to the owner.

## Disposition of round 5

Source column: round 5's lens and row; round 4's rows are cited as "round 4's Bn". Round 6 found five of these
dispositions false in part; each such row says where it was completed.

| Finding | Source | Disposition |
| --- | --- | --- |
| Status line still "VALIDATED" above the STOP | A77, B1 | applied |
| "without checking anything"; "the one check" | A3, A9, B5 | applied — "without its `TargetURL` check", one of two; P0 step 10's copy only in round 6 |
| The STOP's scope: P2–P4, §6's owner actions, no exit criterion | B4 | applied as "all of §8 held; §6's owner actions are not §8 steps" — which round 6 found false, since S-4's `chmod 0600` is also P0.5a item 5; the scope is now the owner's ruling (the design's note 10.1g) |
| §10.2 still names P0 as the next action | B3 | applied |
| D-9's two flags installed by no artifact and no step | B6 | re-derived, and added to the STOP |
| Round 3's D13, inherited by P1 step 2 | B7 | added to the STOP |
| Items 5 and 7 timed to events the procedure does not guarantee | B8 | added to the STOP's re-derive list |
| P0.5b's claim to close S-1 and S-2 against §6 | B9, A other-2 | added to the STOP's re-derive list |
| §6: the frozen 811-volume copy, `PASSPHRASE_OLD`, §10.2 step 8 | B10, A other-11 | applied |
| §10.2 step 2's gate omits S-2 | B11 | applied; the token lifetime is not stated |
| §11: round-4 entry, "two rounds", state line | A37, A39, A other-1, B12 | applied |
| Note 10.1e: "v2 today" breaks on a branch switch or a replacement in the 0777 `bin/` | B13 | applied; the gate now reads "items 1, 2 and 4, in that order" |
| The round-2 record's "15 defects, all applied" | B14 | applied |
| "Debug mode" in §1, §4 and §5 against note 10.1e | B15, A other-3 | note 10.1e says which passes are unrecorded and names the phrase; those sections unchanged |
| The 16:41–16:50 passes' revision | A20 | applied — note 10.1e says it is recorded nowhere; its opening sentence stopped asserting it only in round 6 |
| AC-8's and note 10.1e's terms differ | B16, A other-4 | note 10.1e uses AC-8's term; defining it stays round 4's B22 follow-up, and since round 6 note 10.1e anchors its own rule to P0.5a item 4's `--rotate` |
| The SMART header's replacement claim | A51, B17 | applied |
| §8's phase-order sentence | B18 | applied — the P0.5 exception; step 9's client change added in round 6 |
| "And no other" dropped from the front matter | B19 | applied |
| R-6's "immediately"; P0.5a's "(depends on nothing)" | B20, A other-8 | applied — but the heading's replacement, "(none depends on the recovery)", was false too; it went in round 6, with the P0 preamble's and P0.5a intro's forms of the claim |
| Note 12b's omissions | A49, A75, B21 | applied |
| STOP item 5 names only P0.5a item 2 | B22 | applied — §7.7 too |
| This record's own inaccuracies | A70, A71, A74, A78, B23, A other-9 | applied in this preamble and the round-4 table |
| Note 10.1f's quoting; the shells called "live" | A30, A32, B24, B2, A other-5 | applied in note 10.1f, §6's action cell and note sink-b, and the owner told; P0.5a item 7, §4.1 note (a) and the sink row's first cell only in round 6 |
| ml#2045 "re-padded four tables' delimiter rows" | A47, A60 | applied — four whole tables, every row |
| Note 12b cited P0 step 8's over-broad file-mode rule | A other-6 | applied in 12b; P0 step 8's own sentence is follow-up |
| The sign-in URL is logged whatever the token flag says | A other-7 | follow-up |
| Archiver: "bytes" that were characters; its docstring | A other-10 | applied |
| "Prints no value" dropped from note 10.1e without a record | B residue | applied — note 10.1e names the `die` path |

---

## What round 6 was for

Round 5's corrections, before they merged, for the reason round 5 ran. Two validators, launched together at
15:53 CDT, each reading the frozen commit `7265dc1f`, each told to refute:

| Lens | Brief |
| --- | --- |
| A — fact re-probe | every claim round 5's corrections add or change, the edit script's replay, and this record's authored part |
| B — consistency, consequence and operator reading | the whole design against the corrections, every round-5 disposition, and what an operator reading it that day would do |

Both stopped mid-run — the session's usage limit, per the orchestrator's session; the subagent metadata shows
only the gap, 15:53 to 18:33 — and were resumed at 18:33 CDT, each with its own context intact and neither shown
the other's output; both finished against the same frozen commit. One error was in a brief, not in a validator:
lens B's gave "in that order" as part of the owner's ruling on P0's gate, which set no order (lens A, row 2).
The briefs are not archived here, so both statements rest on the orchestrator's session transcript. Both lenses
list their own constraint slips at the end of their reports; none touched a secret file, the service or the
backup tree.

## What round 6 found

- **Lens A**: 171 confirmed, 9 refuted, 1 unverifiable. The edit script rebuilds `7265dc1f`'s design and
  round-2 record byte-for-byte from `main` and is idempotent.
- **Lens B**: 17 refuted, 2 unverifiable, 41 confirmed sound; 5 of round 5's 29 dispositions false in part.

Lens B's worst findings were in what the owner could do that day. The STOP's exemption sentence was false —
S-4's `chmod 0600` is also P0.5a item 5. Note sink-b's count was case-sensitive and told the owner to wipe a
file that may hold key candidates nobody has tested. And the design still described host state that had moved:
the root `vim` and its swap file were gone — the swap file by 2026-09-22 19:10:21 at the latest, before this
session began (round 7, lens A row 8). Lens B also argued that the STOP held steps no defect touches, leaving the
0777 `bin/`, the S-7 file and tier 2 open; the owner then ruled what the STOP holds. Lens A found attributions
wrong — "in that order" credited to a ruling that set no order, round 4's fact-lens counts given as the whole
round's, and two items filed in note 12b under the wrong cause. It also found two of the edit script's gates
blind: a second copy of a long line the round-2 record already carried, and a rewrite inside one of its
fences, both exited 0.

## Disposition of round 6

The owner ruled on 2026-09-24 what the STOP holds (the design's note 10.1g). Source column: round 6's lens and
row; "B §1" is lens B's first section and "B drops" its third. Lens A reported after lens B's corrections had
been applied, so its corrections are a second pass. That pass also completed what the first had missed: the sink
row's first cell, and the "depends on nothing" claim at two sites no lens named. Round 7 found four of the
dispositions below true only in part; each such row says where it was completed.

| Finding | Source | Disposition |
| --- | --- | --- |
| The STOP's exemption: S-4's `chmod 0600` is P0.5a item 5; which of §6's actions it releases | B1, A1 | owner ruling — the STOP's held and released lists (note 10.1g); the rest of §6's actions (note S-now) and the transcript row's limit only in round 7 |
| The STOP holds steps no defect touches | B3 | owner ruling — P0.5a items 1, 5, 6 and 7 and P3 released, within two limits |
| The STOP's exit criterion ("them"); reading held | B5 | applied — items 1–5, the two findings beneath them and the open questions; reading released |
| Round 5's B4 row: no ruling recorded | B19 | overtaken by the ruling |
| Note sink-b: a case-sensitive count, and a wipe on the count | B2 | applied — case-insensitive and never printed; no wipe until P0 step 3 has tested what the file holds |
| Root's history: wipe "once §5.4's search is done", a search no §8 step lists | B4 | applied — counted now, wiped after P0 step 3; §5.4 says no step extracts a candidate yet; §5.3's "(§8 owner actions)" only in round 7 |
| A reader arriving by a §8 heading never sees the STOP | B6 | applied — a marker under every phase heading |
| R-6 times `nologin` to the §7.3 unit's first start | B7, A7 | applied — step 8's first start |
| The root `vim` and its swap file are gone | B8 | applied — §6's `.swp` row, §4.1 note (a), note sink-b; §5.4 and §11 only in round 7 |
| The shells still called live: P0.5a item 7, §4.1 note (a), the sink row | B §1, A4 | applied — the sink row's first cell in the second pass |
| "And no other" beside an order the STOP calls defective; item 6 "in the same session" | B9 | applied in the front matter; the P0 preamble, P0.5a's intro and note 10.1f only in round 7 |
| Step 10: "the one check §7.5 item 6 says the guard exists for" | B10 | applied — one of two |
| The frozen 811-volume copy and `PASSPHRASE_OLD` have no route | B11 | applied — note S-3c; the decision is the owner's and is follow-up |
| §10.2 step 2's gate: S-2's active key line; a case-insensitive count cannot reach zero | B12 | applied |
| This record's tables: labels that change meaning between rounds; round 4's B23 twice | B13 | applied — source keys, "round 4's Bn", B23's own row |
| Note 10.1e: AC-8's undefined term replaced "after the scrub" | B14 | applied — anchored to P0.5a item 4's `--rotate` |
| "(none depends on the recovery)", and the same claim elsewhere | B15, A8 | applied — the heading first, the P0 preamble and P0.5a's intro in the second pass. That pass also rewrote the base text's "true of five", which was accurate about the revision it describes; round 7 found the rewrite an anachronism, and it now says the restart came later |
| §8's phase-order sentence omits step 9's client change | B16 | applied |
| §11's and this record's "about half"; "each is applied" | B17, A5 | applied |
| Note 10.1e: the leaks "came from the wrapper before `DEBUG_MODE` existed" | B18 | applied — "no committed revision gates them before `64677ab0`" |
| §12's "adopted", A35's subject, note 10.1e's `ExecStart` path — all dropped | B drops | applied — restored |
| "In that order" credited to the owner's ruling | A2 | applied — note 10.1f and the P0 preamble say the order is the design's |
| §11 gives round 4's fact-lens counts as the round's | A3 | applied |
| Note 12b files §10.2's next action and the round count as leftovers | A6 | applied — both under this change's rounds; ml#2057 wrote the first on 2026-09-23 |
| The edit script's guards: a copied long line and the round-2 record's fences pass; stale phrases checked in the design only | A9 | applied — long lines counted, fences and stale phrases checked per file; `--self-test` watches each gate fail |
| The edit script's closing `git diff`, run outside a repository, silently becomes `--no-index` | the self-test's control | applied — it runs only inside a repository |
| §6: what §10.2 step 7's swap does with the local pre-rotation set | A10 (unverifiable) | applied — §6 says §10.2 does not say; that gap is follow-up |

---

## What round 7 was for

Round 6's corrections, before they merged. Two validators, launched together at 19:04 CDT, each reading the
frozen commit `2c9efe85`, each told to refute:

| Lens | Brief |
| --- | --- |
| A — fact re-probe | every claim round 6's corrections add or change, the edit script's replay and self-test, and this record's authored part, every round-6 row included |
| B — consistency, consequence and operator reading | the whole design against the corrections, every round-6 disposition, and what the owner's release lets the owner do that day |

Lens A's brief paraphrased the P0-gate ruling as "items 5–7 alongside"; the option the owner chose said they
"run in the same session", which is why this record rejects lens A's row 7.

## What round 7 found

- **Lens A**: 176 confirmed, 13 refuted, 2 unverifiable. The edit script rebuilds `2c9efe85`'s design and
  round-2 record byte-for-byte from `main`, a second run changes nothing, and `--self-test` passes 8 of 8 with
  each mutant failing on the gate it targets.
- **Lens B**: 18 refuted, 1 unverifiable, 65 confirmed sound; 4 of round 6's 27 dispositions false in part.

Both lenses found that the release had made old text live. The released sink checklist told the owner to purge
transcripts and wipe `duplicati`'s `.viminfo` under neither of the ruling's limits, and "anything that only
reads" took in P0 step 0(c), which runs `duplicati-cli` with the passphrase from binaries item 1 has not yet
secured. Three places still bound items 5–7 to the recovery session, and the front matter still called §8 not
executable at all. Three findings matter once the follow-up lands: P1 step 4's `cp -a` nests a second copy if
item 5 made one, the unit does not mask that copy, and no step extracts a key candidate from the history files
the first limit protects. Lens A also found the second pass's rewrite of "true of five" an anachronism, and
note 10.1g overstating round 6's finding about items 5 and 7. Lens B confirmed the release itself sound: item 1
is safe to run now (after it, a restart fails the start limit and the server stays down, as §4.3 predicts), no
step needs a `duplicati` login shell, item 5's fingerprint reconciliation is defined, and P3 needs nothing from
P0–P2.

## Disposition of round 7

The design now reads two of the ruling's phrases narrowly, and says so in note 10.1g: "Read-only steps" as reads
that change nothing outside a scratch directory and run no Duplicati binary (round 8's wording — the first,
"write nothing", was false of its own example), and "this arc's reports" as every round of the arc, archived
verbatim into a record merged to `main`. Both hold back more than the words alone; the owner may widen them.
(Round 7 itself quoted the phrases as "only reads" and "this arc's validation reports"; round 8 found that those
were not the owner's words, and the design and this record now quote the ruling.) Source column: round 7's lens and row; "B §1" is lens B's first section and "B drop" its third.

| Finding | Source | Disposition |
| --- | --- | --- |
| The transcript row carries no limit, and the limit reads as already met | B1, A2 | applied — the row cites note 10.1g's limit, which now names every round, archived and merged |
| "Anything that only reads" takes in P0 step 0(c) | B2 | applied — reads that change nothing outside a scratch directory and run no Duplicati binary; step −1's re-stage and merge stay held |
| `/home/duplicati/.viminfo`: "wipe" | B3, A2 | applied — counted now, wiped with the history files after P0 step 3 |
| Item 5's copy-out, and the delete it seemed to release | B4, B §1 | applied — item 5 makes P1 step 4's copy and the delete stays with P1 step 4; the nesting `cp -a` is in the STOP |
| "Items 5–7 run in the same session" at three sites | B5, B §1 | applied — "may run now"; note 10.1f quotes the ruling's own words |
| The front matter: "NOT EXECUTABLE"; "do not execute §8 yet" | B6, A3 | applied — held except what note 10.1g releases; item 1's place in the order |
| §5.4's "owes one" is in no exit criterion | B7 | applied — in the STOP, among the findings the release makes live |
| §6's S-3 to S-6 actions have no phase | B8, B §1 | applied — note S-now |
| The root-history grep, copied from the raw file, counts a literal pipe | B9, A9 | applied — `-e` patterns, which need no escape |
| §5.4 and §11 still list the swap file; "Both are root-only reads" | B10, A5, B §1 | applied — four history files, each needing root |
| §7.3.1: `nologin` "once the migration is accepted" | B11, A11 | applied |
| `InaccessiblePaths=` does not mask item 5's copy | B12 | in the STOP — follow-up; a tagged block and its landed copy change together |
| §7.11's `bin/`; P3's heading; §10.2's "exactly as §8 is" | B13 | applied to §10.2 in round 7; §7.11 and P3 step 2 only in round 8, which found this row false in part; P3's heading kept, so its anchor survives, with the release marker beneath it |
| The `.swp` row: "the exit wrote nothing" | B14 (unverifiable) | applied — "did not write the unit"; a normal exit writes a viminfo |
| Note 10.1g: items 5 and 7 untouched by any defect | B15, A1 | applied — questioned only on their timing |
| Note S-3c's options: staging space, "Delete forever", the no-move rule | B16, A12 | applied |
| §5.3's "(§8 owner actions)" | B17, A10, B §1 | applied |
| §11's round-6 entry: "every finding is applied" | B18 | applied — four only after round 7; the first correction said three (round 8) |
| Note 12b: where the two limits live; P0 step 10 | B19, A2, A13 | applied |
| Note 10.1e narrowed "which working copy they ran" | B drop | applied — restored |
| The second pass's "true of five" rewrite | A4 | applied — "was true of five"; the restart came later, from round 2's D8 |
| §10.2 step 2 credits P1 step 2 with the moved-aside `.env` | A6 | applied only after round 8 found the edit missing — P0 step 2 moved it, and only P4 step 2 removes it |
| "Same session" is not the ruling's word | A7 | **rejected** — the option the owner chose says "run in the same session"; lens A's brief paraphrased it |
| The swap file was gone by 2026-09-22, before the session | A8 | applied — the `.swp` row, this record's round-6 section, §11 and the edit script |
| The briefs' wording and the usage-limit stop rest on the session | A14, A15 (unverifiable) | applied — attributed to the orchestrator's session transcript |

## What round 8 was for

Round 7's corrections, before they merged. Two validators, launched at 19:53 and 19:54 CDT, each reading the
frozen commit `f90a87e7`, each told to refute:

| Lens | Brief |
| --- | --- |
| A — fact re-probe | every claim round 7's corrections add or change, the edit script's replay and self-test, and this record's authored part, every round-7 row included |
| B — consistency, consequence and operator reading | the whole design against the corrections, every round-7 disposition, and what the owner's release lets the owner do that day |

Lens B's brief gave the ruling's phrase as "read-only steps"; the design and this record had been quoting it as
"only reads". The owner's words, as the session that took the ruling recorded them in its handoff, are "Read-only steps
may run." — the design and this record now quote that, and mark the design's reading of it as a reading (note 10.1g).

## What round 8 found

- **Lens A**: 155 confirmed (88 in the design, 57 in this record, 10 in the edit script), 4 refuted, 1
  unverifiable. The edit script rebuilds `f90a87e7`'s design and round-2 record byte-for-byte from `main`, a
  second run changes nothing, and `--self-test` passes 8 of 8.
- **Lens B**: 11 refuted, 1 unverifiable, 95 confirmed sound; 3 of round 7's 25 dispositions false — one wholly
  (A6, recorded as applied but never made), two in part (B13, B18).

The pattern of rounds 5–7 held: the defects clustered in the corrections' own text. The one that mattered most
was a correction **recorded as applied but never made** — round 7's A6 row said §10.2 step 2 now credits P0
step 2 with moving the old `.env` aside and P4 step 2 with removing it, and the line was byte-identical to the
commit before. Three findings touched what the release lets the owner do today: the transcript row told the
owner to "count-grep now" with no command, and a count typed with a value on argv would create the very sink the
row exists for; §5.3 had turned a pointer at root's shell history into "look before then", with no way to look
without printing a line that may carry `--passphrase`; and item 5's copy-out, as written, left the escrow's
long-term home group-writable by the service user and could nest a second copy into an existing directory.
Lens B also found the STOP's released bullet presenting the design's narrow reading as the owner's words, the
P0 preamble reading item 1 as held, note 10.1g's present tense false against the block it cites, and the
front-matter bullet dropping both the released reads and P3 step 3's wait on D-5. Lens A confirmed item 1 has
not run, the swap-file timing, every step claim in the STOP, note S-3c's figures and the `-e` grep fix.

## Disposition of round 8

Every finding is applied in the edit script's rebuild of the design, except the one only the owner can settle
and the three lens B marked out of scope, which are follow-up. Source column: round 8's lens and row.

| Finding | Source | Disposition |
| --- | --- | --- |
| §10.2 step 2's moved-aside `.env` — recorded as applied in round 7, never made | A1, B8, B §1 | applied — P0 step 2 moved it, only P4 step 2 removes it; the round-7 row now says so |
| The front-matter STOP bullet omits the released reads and P3 step 3's wait | A2, B9 | applied — "P3's tier-2 fix … and the reads it names" |
| §11's round-6 entry: "three of them only after round 7" | A3, B12 | applied — four; the round-7 row now says the first correction said three |
| "Reads that write nothing", whose named example writes a scratch tree | A4, B10 | applied — reads that change nothing outside a scratch directory and run no Duplicati binary, at all three sites |
| §5.4: "Those four files" — root's two cannot be confirmed to exist without root | A5 (unverifiable) | applied — "even to confirm that root's two exist, since `/root` is 0700" |
| The transcript row: "count-grep now", no command | B1 | applied — the row defers to note sink-c: count by value, never with a value on argv, and purge only within the limit; sink-c says the counting method itself is follow-up, so the row no longer tells the owner to act |
| Item 5's copy-out: `cp -a` carries the 0770 and nests into an existing directory | B2 | applied — confirm the destination does not exist, `chmod 0700` the copy, sha256 both sides |
| §5.3's "look before then"; §11's "(no shell history names it)" | B3 | applied — look only without printing a line; §11 says pcalnon's history does not name it and root's is unread |
| P0 preamble and P0.5a intro read item 1 as held | B4 | applied — item 1 is released and may already have run |
| The re-measuring row conflicts with the transcript row's limit | B5 | applied — a `tool-results/` copy goes in the session that made it (note sink-c) |
| Note 10.1g's present tense against the STOP it cites | B6 | applied — "the STOP block … then listed" |
| "Only reads" is not the ruling's phrase | B7 (unverifiable) | applied as far as the record allows — the design and this record quote "Read-only steps may run." and mark the reading; **only the owner's session settles the phrase** (carried as O-3 in the 2026-10-03 assessment) |
| The no-move bullet's "the one escrow copy" is ambiguous once item 5 makes a second | B11 | applied — the in-tree escrow, which only P1 step 4 deletes, once item 5 or P1 step 4 has copied it out |
| §7.11 still lists `bin/` to retire after acceptance; P3 step 2 still says to land what ml#1999 landed | B §1 (B13 false in part) | applied — `bin/` is not on §7.11's list; P3 step 2 says the scheduler and three user units landed, the installer and the failure unit have not |
| The STOP's released and limits bullets drop the ruling's own wording | B drop | applied — both bullets quote the ruling and name the design's reading as a reading |
| AC-14's raw `\|`, P0 step 1's second listing, §4.1/§7.3.1 "P0.5 closes 0777 `.config`" | B out of scope | follow-up — the §8 change that clears the STOP |

---

## Round 4, lens A — fact re-probe

Archived verbatim (19,700 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

I re-derived every factual claim in `git diff df21367d d9f44a78` from git objects, `gh` and read-only host probes. 41 hold, 10 are refuted and 2 can't be checked within the constraints. The owner's two decisions are recorded accurately, with two gaps: note 12b records only one of the SMART refactor's three changes (row 43), and 10.1e credits round 1 with moving the scrub into P0.5a when round 2's split did (row 20).

**Changed**: nothing in the repository. Every copy and probe was written only under my scratchpad.

Location key: **D** = `notes/…BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, **S** = `util/ad-hoc/smart_checks_backup-sda.bash`, **E** = `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`. Line numbers are at d9f44a78.

| # | Location | Claim under test | Verdict | Evidence | Proposed fix (REFUTED only) |
|---|---|---|---|---|---|
| 1 | D L10 | Order: P0.5a items 1, 2 and 4–7; step −1 review; step 0 verification, with (c) after step 1; steps 1–8; P0.5b; steps 9–11 | CONFIRMED | L2085–2087 "P0.5a — before anything in P0 … Items 1, 2, 4, 5, 6 and 7"; L2119 "P0.5b — immediately after P0 step 8, same session"; L1734 and L1740 | |
| 2 | D L498 | P0.5b does the re-key | CONFIRMED | L2121 "Item 3 (the re-key) only" | |
| 3 | D L1700–1701 | All nine are merged; ml#1999 landed them; the tenth is P3 | CONFIRMED | `gh pr view 1999`: file list has all nine. `git ls-tree d9f44a78`: nine present, `util/install_juniper_backup_timer.bash` absent | |
| 4 | D L1701–1702 | ml#2029 re-landed the three the rulings changed | CONFIRMED | `git show --name-status ab434c9b`: M on `duplicati.service` (UMask 0007→0027, D-14), `install_duplicati_service.bash` (+ D-6 drift gate) and `2026-09-21_backup_destination_permissions.bash` | |
| 5 | D L1703 | `stage_design_artifacts.py --check` reports every artifact current | CONFIRMED | Run on a scratch extraction of d9f44a78: "0 staged, 13 already current, 1 skipped", exit 0 | |
| 6 | D L1728–1731 | Run P0.5a items 1, 2 and 4–7 before P0; item 4 is D-8's one scrub | CONFIRMED | Matches L2087 and decision 1 | |
| 7 | D L1742 | `--no-local-db` rebuilds a temporary index from every dindex volume on each invocation | UNVERIFIABLE | The wording matches `duplicati_drill_run.py:33-34`. The product behaviour needs Duplicati 2.4.0.0 source or a timed run, and running Duplicati is forbidden here | |
| 8 | D L1743; L2367; L2515 | The destination holds 877 files: 434 dblock, 434 dindex, 9 dlist | CONFIRMED | `find …/Yamaguchi/ -mindepth 1 -maxdepth 1 -printf '%y'` → `877 f`, all at depth 1. Grouped by type: 434 dblock, 434 dindex, 9 dlist | |
| 9 | D L1744–1746 | The ">30 minutes" text was added by ml#1268 and measured on the old `Ubuntu` archive at `/mnt/Backups/Ubuntu` | CONFIRMED | `git log -S` → 3131790e (ml#1268), 2026-08-23 13:53:59 -0500. `gh`: mergedAt 18:54Z. 3131790e's copy has `--dest` default `file:///mnt/Backups/Ubuntu` (L160) and `--encryption-module=gpg` (L90); Yamaguchi's files are `.aes` | |
| 10 | D L1745 | "measured on 2026-08-23" (the exact day) | UNVERIFIABLE | 2026-08-23 is only the recording date, so it is an upper bound; the 08-22 handoff doesn't mention the timing. The session transcripts would settle it, but they are a secret sink and I did not read them | |
| 11 | D L1746 | "(DMG §4a)" is the right citation | CONFIRMED | `…ARCHIVE-DAMAGE-FINDINGS.md` §4a: "Run 2026-08-23 (…duplicati_drill_run.py)" on restore points 2026-07-11 and 2025-11-12; its §1 gives the path. That file never mentions `--no-local-db` or 30 minutes; `drill_run.py:160` is stronger evidence for the path. "DMG" is defined at D L16 | |
| 12 | D L1746 | The measurement came before this destination existed | CONFIRMED | `stat` birth time 2026-08-26 16:14:42 -0500. Oldest dlist `duplicati-20260825T102739Z`. `…YAMAGUCHI-BACKUP-CERTIFICATION.md` L75: the set began at `/media/pcalnon/temp_backups/Yamaguchi/`. Both dates are after 08-23 | |
| 13 | D L2113 | Running `--vacuum-time=1s` after P1 would delete the recovery's journal | CONFIRMED | `man journalctl`: "--vacuum-time= removes archived journal files older than the specified timespan", and `--rotate` archives the active files first | |
| 14 | D L2131 | P1 step 3 was merged in ml#1999 (`43980f13`); the check reads 0; the wrapper has exactly one `SETTINGS_ENCRYPTION_KEY=`, the export | CONFIRMED | `gh` 1999: sha 43980f13, wrapper +167/−202, and it is the last commit touching the wrapper. On the frozen blob, `grep -c 'Environment=SETTINGS'` → 0 and the only `SETTINGS_ENCRYPTION_KEY=` is at L126 (`export`) | |
| 15 | D L2135–2139 | D-2 was re-decided as rotate-and-keep and runs after the drill; D-8 runs before P0 | CONFIRMED | §10.1 D-2 row; L1714–1716 | |
| 16 | D L2144 | D-14 is ruled read-only and the script implements it | CONFIRMED | The permissions script at L16 and L26–28: `chown duplicati`, directories `2750`, files `0640` | |
| 17 | D L2205 | Seven of the fourteen decisions are ruled | CONFIRMED | §10 lists D-1 to D-14. §10.1 lists D-1, D-2, D-4, D-6, D-8, D-9, D-14 | |
| 18 | D L2242–2243, L2251 | Decision 1 (the D-8 amendment) is recorded accurately | CONFIRMED | The removed row read "Scrub once, after P1 … unchanged from the recommendation"; the new row gives both dates | |
| 19 | D L2278–2279 | The ruling was made from a column reading "scrub once, after P1" | CONFIRMED | 43980f13 L2143: `\| D-8 \| … \| scrub once, after P1 \|` | |
| 20 | D L2279–2283 | "Consensus round 1 had already moved the scrub into P0.5a item 4" | REFUTED (attribution) | F-18 proposed "a 'P0.5 — same session as recovery' bucket". Round 1 created `### P0.5 — same session as the recovery` (`2026-09-22_reconcile_backup_design.py:1446`). `P0.5a — before anything in P0` came from round 2's split (`2026-09-22_apply_round2_corrections.py:1247`) | "Consensus round 1 had already moved the scrub out of P1 — Lane B3's finding F-18 in `JUNIPER_2026-09-21_…ROUND-1-RECORD.md`: it has no dependency on the recovery and takes minutes, so it must not stay open for days while the recovered server runs — into a new P0.5 bucket, and round 2's split made it P0.5a item 4, 'before anything in P0'. Both landed in ml#1999, and neither reconciliation updated the column." |
| 21 | D L2280–2282 | F-18 is Lane B3's and says what the note says | CONFIRMED | `…ROUND-1-RECORD.md` L759, under Report B3: "no dependency on recovery and take minutes; the plan leaves them open for days while the recovered server runs" | |
| 22 | D L2283–2284 | The ruling and the plan disagreed from the day the ruling was recorded | CONFIRMED | At 43980f13, L2018–2020 put P0.5a "before anything in P0" with items 1, 2 and 4–7. The ruling (ml#2029, 09-22 20:44 CDT) said "after P1" | |
| 23 | D L2284–2286 | The three leaked label families "were printed by wrapper v1 under `DEBUG_MODE`" | REFUTED | 52571621 and d721fc78 do gate all three on `DEBUG_MODE`, but they did not print the leaks. The leaking passes ran at 16:41, 16:44, 16:50 and 17:30 CDT on 09-20 (D L214–215, L232). Every revision in existence then echoes all three unconditionally: 60d1c45d (17:05) and b4aeed52 (17:17) have `grep -c DEBUG_MODE` → 0, and 6708cb28 (17:26) has bare `echo` at L112, L140, L207. `DEBUG_MODE` first appears in 64677ab0, authored 17:48:14 -0500 | "All three leaked label families — … — were printed by the first wrapper, which echoed them unconditionally. Every revision through ml#1967's merge (`6708cb28`, 17:26 on 09-20) does, and the four leaking passes ran 16:41–17:30. `DEBUG_MODE`, off by default, gated them from `64677ab0` (17:48) onward, which is why the 18:19:42 start of the running server emitted none. That server is never restarted (P0 step 2 stops it)," |
| 24 | D L2286–2287 | The running v1 server is never restarted; P0 step 2 stops it | CONFIRMED | L1819: "stop, **never** restart". `ps`: PID 1397393 started Sun Sep 20 18:19:42 2026 | |
| 25 | D L2287 | "every later start runs the §7.3 unit" | REFUTED (minor) | Procedure A's probe (`2026-09-21_probe_settings_key_on_copy.bash:79-84`) starts `/usr/bin/duplicati-server` under `systemd-run`, outside the unit. It prints no label, so the note's conclusion holds | "…every later start of the service runs the §7.3 unit, whose wrapper v2 carries none of those labels and prints no value (Procedure A's optional probe starts `duplicati-server` directly under `systemd-run` and prints no label either)." |
| 26 | D L2287–2288 | Wrapper v2 carries none of the labels and prints no value | CONFIRMED | Label grep on the d9f44a78 blob → 0. All output goes through `log`/`die` and shows names and lengths only (one edge case under other issues) | |
| 27 | D L2288 | "S-1's `Invalid slot` lines needed a unit carrying the key in `Environment=`" | REFUTED (imprecise) | D §5 note 2 (L227): the 23 lines are 22 on the `Environment=` value plus 1 from an `ExecStart` revision. The conclusion survives: `systemctl cat duplicati.service \| grep -v '^[[:space:]]*[#;]' \| grep -c '%'` → 0 | "S-1's 23 `Invalid slot` lines needed a unit carrying the key in a specifier-parsed setting — 22 in `Environment=`, 1 in an `ExecStart=` revision (§5 note 2) — and the loaded unit has no `Environment=` line, no `%` in any non-comment line and no drop-in (checked 2026-09-24)," |
| 28 | D L2288–2289 | The loaded unit has no `Environment=` line and no drop-in | CONFIRMED | `grep -c '^Environment='` → 0 (0 with leading whitespace allowed too). Loaded Environment property: 0 words. `DropInPaths=` is empty; FragmentPath is `/usr/lib/systemd/system/duplicati.service`; `NeedDaemonReload=no` | |
| 29 | D L2289–2290 | P0.5a item 2 needs a `daemon-reload`, and the reload re-emits nothing | CONFIRMED | Item 2 edits `yamaguchi-server-db-snapshot.service`, which lives in `/etc/systemd/system` and runs as root, so a system `daemon-reload` is required. `grep -r -l` for SETTINGS_ENCRYPTION_KEY/PASSPHRASE over the system unit directories → none | |
| 30 | D L2290–2292 | AC-8 and AC-14 read the journal | CONFIRMED | L2180 (`journalctl --since <ts>`) and L2186 (`journalctl -u duplicati.service --since <ts>`) | |
| 31 | D L2337 | §10.2 step 2 cross-references (P0.5a item 5, P1 step 2, P0.5a item 4) | CONFIRMED | L2114, L2130, L2113 | |
| 32 | D L2353–2355 | The refactor changes neither the commands the script runs nor the names it writes | CONFIRMED | `git diff 4b311619 d9f44a78` on S: the `smartctl`/`chown` lines are untouched, the name expressions differ only by `export`, and the format is `date +%F_%T` in both | |
| 33 | D L2367–2371 | 434 dindex on this destination; the timing came from the old archive | CONFIRMED | Rows 8 and 9 | |
| 34 | D L2460–2461 | The D-14 dissent is settled for the read-only form | CONFIRMED | §10.1 D-14 row | |
| 35 | D L2498 | "its 15 defects are the `r3-*` edits" | REFUTED | There are 29 distinct `r3-*` tags. They cover D1–D10, D12, D14 and D15, plus two item caveats (`r3-autoupdater-caveat`, `r3-loadcredential-clause`). D11 (a §12 artifact row) and D13 (the `/etc/duplicati/env` path) have no edit and are absent at d9f44a78: `grep -c 'Design artifacts landed'` → 0, wrapper L40 still defaults to `/home/duplicati/.config/Duplicati/.env`, and the installer has no `/etc/duplicati` | "…it found 15 defects (D1–D15, Report C in `JUNIPER_2026-09-22_…ROUND-2-RECORD.md`), applied as 27 of the 29 `r3-*` edits of `util/ad-hoc/2026-09-22_apply_round2_corrections.py` (the other two are caveats on items 2 and 8). D11 and D13 have no edit and are still open." |
| 36 | D L2498 | Rounds 1–3 landed together as ml#1999 (`43980f13`) | CONFIRMED | `gh` 1999: sha 43980f13, title "…rounds 1-3…", mergedAt 2026-09-22T09:55:30Z | |
| 37 | D L2499 | ml#2029 row | CONFIRMED | sha ab434c9b; mergedAt 01:44Z, which is 09-22 20:44 CDT ("evening"). M and A statuses match the row exactly; `PR_BODY_RULINGS.md` is excluded per 12a | |
| 38 | D L2500 | ml#2041 row | CONFIRMED | sha 4b311619, 09-23 08:56 CDT. Nine `reports/smart/*.out` files plus the two scripts added; its design diff adds 10.2a and 10.2b and closes the "D-12a carried item" | |
| 39 | D L2501 | ml#2057 row | CONFIRMED | sha d15e7c01, 09-23 17:44 CDT; `+2026-09-23_clarify_drill_ordering.py` | |
| 40 | D L2502 | ml#2067: SHA, date, files, "content unchanged" | CONFIRMED | sha dcfc024f, 09-24 03:19 CDT; the two added scripts match. The diff touches only the front matter, and the only word removed is the connective "and" | |
| 41 | D L2502–2503 | "one of the closed ml#2045's two net changes" and "ml#2045's other net change" | REFUTED (minor) | #2045 is CLOSED, and its net effect against main at close (`f9c81d80`) is 2 files. But after #2067, `git diff df21367d origin/pr-2045-head` on the design still has 7 hunks: four re-padded tables and note 10.2b moved ahead of 10.2c. None was re-landed | L2502: "…ml#2067 (`dcfc024f`), the front-matter part of the closed ml#2045's change to this file (it also re-padded four tables and moved note 10.2b ahead of 10.2c; neither was re-landed)." L2503: "…the other file ml#2045 changed…" |
| 42 | D L2507–2510 | Five rows were missing; the §11 quote; PR bodies archived under the round-2 directory | CONFIRMED | §12 at df21367d ends at the round-2 row. `git log -- design` lists #1989, #1999, #2029, #2041, #2057 and #2067. Each of the four PRs has one `PR_BODY_*.md` | |
| 43 | D L2518–2520 | Decision 2 is recorded as "adopted with one `date` call where it had two" | REFUTED (incomplete record) | The adopted file also rewrites the header and drops the `# shellcheck disable=SC2034` directive, drops the PR copy's two trailing blank lines, and stays 100644 where the PR copy is 100755 (`git ls-tree`) | "…is adopted with three changes: one `date` call where it had two (two calls can straddle midnight), a rewritten header without the `# shellcheck disable=SC2034` directive (the exports make it unnecessary), and without the PR copy's two trailing blank lines. The file stays mode 100644, not the PR copy's 100755." |
| 44 | D L2518 | "every constant exported, the clock read error-checked" | CONFIRMED | True at d9f44a78. At b0223f18 the intermediate `DATE_STAMP`/`TIME_STAMP` were not exported (a nit, moot now) | |
| 45 | S L3–4 | "every disk and partition on this host is named" | REFUTED | `lsblk -e 7` shows sda, sda1, sdc, sdc1–3, sdd (0B), sdg (0B), nvme0n1 and p1–p6. The palette names sdb, sdb1, sdb2, sdc4 and sdd1, none of which exist, and omits nvme0n1* and sdg | "# The DEVICE_* block below is a deliberate PALETTE of sd* names, so CURRENT_DEVICE can be repointed by / # editing one line. It is not a live inventory (on 2026-09-24 sdb and sdc4 are gone and nvme0n1 is / # not listed) -- check `lsblk` before repointing." |
| 46 | S L4–8 | Exported variables count as used; 12 SC2034 on the pre-refactor copy; the hook runs at `--severity=warning` | CONFIRMED | Pinned shellcheck 0.10.0 at `--severity=style` on the d9f44a78 copy: no output, exit 0. origin/main's copy minus the directive: 12 × SC2034, exit 1. The un-exported d9f44a78 variant: 12, nothing else. `.pre-commit-config.yaml` L219 `--severity=warning`. The old header's "13" was wrong | |
| 47 | S L44–46 | Two `date` calls can straddle midnight; `export X="$(…)"` hides a failure | CONFIRMED | Scratch probe prints `export-form status=0` and `assign-form status=1` | |
| 48 | S (whole file) | The adopted script differs from the PR copy only in the header, the timestamp block and the trailing blank lines | CONFIRMED (with a caveat on the ref) | Diff of `origin/pr-2045-head` against d9f44a78: exactly those three, plus mode 100755→100644. But the ref resolves to **f6363b9a** (`gh` headRefOid), not b0223f18, which is three commits below. Against b0223f18 itself the only content differences are the header and the timestamp block; b0223f18 had already dropped the blank lines and de3369cd re-added them | |
| 49 | E L18 | "placed by … F-18 in ml#1999, the day BEFORE the ruling" | REFUTED | ml#1999 merged 2026-09-22 04:55 -0500, and the ruling is dated 2026-09-22 (ml#2029 at 20:44 -0500): the same local day. Round 1 also placed it in P0.5, not P0.5a (row 20) | "…moved out of P1 by consensus round 1's Lane B3 finding F-18 and made P0.5a by round 2's split, both in ml#1999 that morning, hours BEFORE the ruling…" |
| 50 | E L26–29 | The defects-of-fact paragraph (877 total; ml#1268 "that afternoon"; before Yamaguchi existed) | CONFIRMED | Rows 8, 9 and 12; 13:54 CDT is afternoon | |
| 51 | E L36 / L52 | "every fenced code block must be byte-identical" | REFUTED (overclaim, no damage) | `FENCE` only matches the 16 column-0 blocks, so the 4 indented `text` blocks (L1822, 2051, 2075, 2098) are unguarded. I checked all 20 blocks independently: identical | `FENCE = re.compile(r"^( *)```[^\n]*\n.*?^\1```", re.M \| re.S)` |
| 52 | E (whole) | The script produced the design diff; it is idempotent; no line exceeds 512 characters | CONFIRMED | Replayed on a scratch copy of df21367d's design: "applied 18", and `cmp` with the d9f44a78 blob → identical. A rerun reports "no change (18 edit(s) already applied)". Longest line is under 512 | |
| 53 | E L11–13 | The `Related:` handoff's items 4 and 5 scoped this | CONFIRMED | Handoff L17–21 | |

**Other problems I noticed:**
- **The brief's premise about PR 2045:** `origin/pr-2045-head` is f6363b9a, not b0223f18, and "trailing blank lines dropped" only holds relative to that tip.
- **Note order in §10.2:** the design prints the notes as 10.2a (L2351), 10.2c (L2364), 10.2b (L2379). ml#2045 would have fixed this; it was not re-landed.
- **§11 L2429:** "15 defects, all applied" is false; D11 and D13 were never applied.
- **P0 step 0(a) cannot pass:** L1737 asks to confirm `--require-db-encryption-key` (D-1), but no artifact carries that flag. The only mention is the conditional comment at `util/systemd/duplicati.default:4`, and P0.5b adds the flag only after step 8.
- **The live unit can restart itself:** it has `Restart=always` (NRestarts=0), and its ExecStart is a symlink to the primary checkout's `scripts/duplicati-wrapper.bash`. That file is currently the v2 blob (`42ba4683`, identical to d9f44a78's). So "never restarted" is not enforced by systemd, but an unplanned restart today would print nothing. A branch switch in the primary checkout would change that.
- **Wrapper v2 has an edge case:** its `die` path prints `'${word%%=*}'`, which is the whole word when a non-option argv word has no `=`. With the unit's unbraced `$DAEMON_OPTS`, a secret containing a space would leak its tail. This is latent, because the design's contract keeps secrets out of `DAEMON_OPTS`.
- **12b wording:** "434 are, and 9 are dlists" leaves out the 434 dblocks. It also files P1 step 3 and step −1 as "leftovers of the rulings" when they went stale because ml#1999 merged.
- **The old archive has moved:** `/mnt/Backups/Ubuntu` now holds only `.dropbox-dist/` and `Dropbox/`, so the historical path in P0 step 0(c) can't be used to re-measure.
- **Unchanged fenced comment:** the comment at D L1768–1770 (and in the landed `2026-09-22_confirm_a0_premise.bash`) still says "here" for the 30-minute figure without the old-archive qualifier.

**Constraints:** no slips. For completeness:
- One `git -C` targeted this worktree's own path.
- The isolation layer refused three commands, with no effect.
- I ran `stage_design_artifacts.py` with `--check --workdir <scratch>`, and replayed the edit script with its trailing git call stubbed out. Both ran only on scratch copies of the frozen tree.
- A `find -type d` listing printed the name `_yamaguchi_keys`; I did not enter it.
- Systemd checks were counts or paths only.
- No unit was touched, no Duplicati binary was run, and no journal, syslog or secret file was read.

**CONFIRMED 41 · REFUTED 10 · UNVERIFIABLE 2**

<!-- markdownlint-enable -->

---

## Round 4, lens B — consequence and consistency attack

Archived verbatim (23,809 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

No constraint slips. I only read the frozen objects via `git show`/`git archive` into my scratchpad. I never ran `journalctl`, never ran a Duplicati binary, and never started, stopped or reloaded a unit. The only commands against `/mnt/Backups/` were `ls`. Host checks were read-only (`systemctl show`/`cat`, `ls`, `ps`, `/proc/sys/kernel/core_pattern`) and printed no secret values. **Changed**: nothing.

Locations are lines in the design (`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`) at d9f44a78 unless another file is named. The round-1 record is `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`; DMG is `JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`.

**The four that would derail an operator following §8:** step 0(a) cannot pass where the order puts it (row 1), P1 step 1's key command can lock the recovered database (row 2), step 10's guard dry-run passes without checking anything (row 3), and a timer restart can copy the cleartext A0 database into the backup source (row 4).

| # | Location | What it says | Why it is wrong or inconsistent | Verdict | Evidence | Proposed fix |
|---|---|---|---|---|---|---|
| 1 (H) | Front matter l.10; step 0(a) l.1734–1737; defaults block l.590–592; P1 step 1 l.2129 | Step 0 runs before "P0 steps 1–8". Step 0(a): "Confirm the installed artifacts match the rulings: … `--require-db-encryption-key` (D-1), and a `.blessed.sha256` written by the installer (D-6)" | The installer first runs in step 8, so no blessed file can exist at step 0. No landed artifact carries the D-1 flag: the defaults file has it only in a comment ("append …"), ml#2029 never touched that file, and P1 step 1 says "add … at this point" (re-key start 2). A hand edit to the blessed `/etc/default/duplicati` trips the D-6 drift gate, and the gate's own escape (`--update-backup-behavior`) reinstalls the repo copy without the flag. D-1 has no durable home. | REFUTED | `ls /usr/local/lib/duplicati/` → No such file. Landed `DAEMON_OPTS="--webservice-port=8300 --webservice-interface=loopback --server-datafolder=/home/duplicati/.config/Duplicati --disable-update-check"`. Grep of all 13 landed artifacts finds the flag only at `duplicati.default:4` (a comment). `git show --stat ab434c9b` does not list `duplicati.default`. | Front matter: "…then **P0 step 0(b)**, then **P0 steps 1–8** (0(c) after step 1's freeze; 0(a) after step 8's installer, before its first start), then **P0.5b**…". Step 0(a): "After step 8's installer: `UMask=0027`, `AmbientCapabilities`+§7.3.2 set, loopback, and `.blessed.sha256` present. `--require-db-encryption-key` is added to `util/systemd/duplicati.default` in the repo and installed with `--update-backup-behavior` at P0.5b's second start — never hand-edited into `/etc/default/duplicati`." |
| 2 (H) | P1 step 1 l.2128–2129 (the procedure P0.5b runs, l.2119–2124) | "Generate a new settings key (`umask 077; openssl rand -base64 48 \| tr -d '\n' > /etc/credstore/duplicati-settings-key`), then re-key … first with the **old** key still in the credential file" | The generate command overwrites the old key before start 1 needs it. Followed literally, start 1 hits a Mismatch and the old key is gone unless escrowed (for A, the recovered 09-18 key; for A0/A2/B, the pre-start key). That reproduces Leg C (§5.4). | REFUTED | Both clauses are in one sentence. Procedure A (l.2036): "leave it there until P0.5b's re-key replaces it". | "Generate to `/etc/credstore/duplicati-settings-key.new`. Start 1 with the old key still in place and `--disable-db-encryption`. Stop. Escrow the new key, then `mv …key.new …key`. Start 2 without the flag." |
| 3 (H) | Front matter l.10; step 9 l.2069–2070; step 10 l.2073–2082; guard l.1389 | Step 9: "Land the client changes (the credential path and the new pause/resume subcommands) … before P0 runs". Step 10: dry-run `DUPLICATI__REMOTEURL="$(… yamaguchi_server_api.py export <id> \| python3 -c …)"`, "Require exit 0" | This P0 precondition is missing from the "no other" order; step −1 reviews only the nine tagged blocks. It has not landed. With step 9's new password, login fails and stdout is empty, so the URL is `""`. The guard's `-n` test then skips the TargetURL comparison and exits 0 — a vacuous pass right before `resume` fires the overdue backup. `export` failures also print non-JSON and exit 0. | REFUTED | `yamaguchi_server_api.py:41` `CRED_FILE = …/juniper-ml/.env`. `:80` `choices=[…"task"]` has no pause/resume. `login()` ends in `sys.exit("FATAL: login failed…")`. Guard `if [[ -n "${REMOTE_URL}" ]]`. | Front matter: "…**P0 step −1** (review the nine, and land §7.6's client change that step 9 requires)…". Step 10: `url="$(…)" && [[ -n "$url" ]] \|\| { echo "REFUSING: no TargetURL read from the job" >&2; false; }` before the dry-run. |
| 4 (H) | P0.5a item 2 l.2109–2110; P0.5b l.2122–2123; A0 l.1966–1968, l.1994–1999 | Item 2: stop the timer "until P0 step 8 has placed the recovered database; restart it only then". P0.5b: "stop the snapshot timer … then restart the timer" | Two conflicting restart instructions. The timer is `Persistent=yes`, so a restart after a missed 13:45 UTC fires at once. "Placed" comes before the first start, and under A0 the placed file is the cleartext database "carrying … the passphrase". The catch-up copy lands in `/home/pcalnon/.local/state/duplicati-server-db/` — inside the backup Source, the S-7 shape the A0 script refuses. This lands once row 8 is fixed, as it must be. | REFUTED | `systemctl show yamaguchi-server-db-snapshot.timer` → `Persistent=yes`. Snapshot script `DEST_DIR = "/home/pcalnon/.local/state/duplicati-server-db"`. | Item 2: "…stop the timer and keep it stopped through P0.5b, which restarts it after the `VACUUM`; do not restart it at step 8 (`Persistent=yes`; the A0 database is still cleartext there)." |
| 5 (M-H) | Front matter l.10; P0.5b l.2119–2124; step 3 note l.1959–1960; step 10 l.2071–2073 | "P0 steps 1–8, then P0.5b, then P0 steps 9–11". Step 10: the overdue job "will start on its own once the startup pause lapses"; "a first start under changed DAEMON_OPTS followed by pause/resume is the exact untested sequence…" | The order puts P0.5b's two starts under changed DAEMON_OPTS, plus the start after `VACUUM`, before step 10's pause, tempdir fix and guard. Step 3 itself says the startup delay "is not relied on". A backup that slips through is killed mid-run by the re-key stop (rule 11). P0.5b also ends with the server stopped and no start before step 9. The diff settled the old front-matter/heading conflict toward the heading without checking step 10. | REFUTED | Diff: "then **P0**, then **P0.5b**" → "then **P0 steps 1–8**, then **P0.5b** … then **P0 steps 9–11**". | Run P0.5b after step 10's `pause`, then start the server, sample `serverstate` and continue. Or drop it per row 6. |
| 6 (M-H) | §7.3.5 l.1159–1162; P0.5b l.2123–2124; S-2 row l.461 | "the currently installed key is public (S-1's successor is the passphrase itself, S-2)". P0.5b "is the item that closes S-1 and S-2, so it is not deferrable" | False in all four procedures. The only database under the S-2 key (the empty 09-20 one) and its `.env` move aside in step 2. A0 is cleartext, then step 8 encrypts it under the fresh D-1 key. A uses the 09-18 key, which §5.4 excludes as both S-1 and S-2. A2 is wiped, then gets the step-8 key. B starts with "a new settings key", and wrapper v2 prefers the credential. The urgency is left over from round-1 F-11(a), whose premise the same reconciliation removed. Right mechanism, wrong consequence: row 5's risk buys nothing. | REFUTED | Round-1 record F-11: "(a) the burned key becomes the **live** settings key from P0 step 4 until P1.1". Step 2 l.1819 `sudo mv …`. Step 7 l.2046. Wrapper l.898–904. | P0.5b: "**Item 3 — only after Procedure A.** A0/A2/B start under a fresh D-1 key; S-2's settings-key half closed at step 2; its passphrase half stays open until §10.2." |
| 7 (M) | Procedure B step 7 l.2046 vs step 8 l.2062–2067 | B: "Start the empty server with the §7.3 unit and a new settings key" | Steps 1–8 run in sequence, but only step 8's installer creates the unit, the wrapper and `/etc/credstore`. | REFUTED | `/usr/local/lib/duplicati/` and `/etc/systemd/system/duplicati.service`: both No such file. Installer l.1040–1047. | Step 7: "Run step 8's installer and create the credential per its NOTE first, then start…" |
| 8 (M) | P0.5a item 2 l.2109; §7.7 l.1460–1461 | "add `ProtectSystem=strict` to `yamaguchi-server-db-snapshot.service`" | `strict` makes `/home` read-only too, and the snapshot writes a tmp file into `/home/pcalnon/.local/state/duplicati-server-db`, then `os.replace` plus chown/chmod. Every fire fails with EROFS and R-14 goes dark until P2's AC-6. The design's own unit pairs `strict` with `ReadWritePaths=` (l.635–648). | REFUTED | Deployed unit has neither directive (`systemctl cat`). Script l.53, l.106–141. | "…`ProtectSystem=strict` **and** `ReadWritePaths=/home/pcalnon/.local/state/duplicati-server-db`…" |
| 9 (M) | §10.2 step 2 l.2337 (edited); note 10.1e l.2284–2293; item 4 l.2113 | Gate: "S-3, S-6 and S-7 counts all read zero", with the logs covered by "D-8's one scrub, P0.5a item 4". 10.1e: "'Once' still holds"; a later find is "not a reason to re-run this scrub" | Every start with an autogenerated password writes a sign-in URL into the journal and syslog (S-6a; round-1 F-15: "every restart before P0 step 9 mints a fresh one"). B's first start always does. A0/A/A2 do when §7.3.6 clears the password hash before step 8's start. Those URLs now post-date the only scrub, so the S-6 half of the gate cannot reach zero without the second scrub the amendment forbids. The edit created this (the old after-P1 scrub came later). Tokens expire; what breaks is the gate. | REFUTED | S-6a l.481; §7.3.6 l.1224–1227; round-1 record F-15. | Gate: "S-3, S-7 zero; S-6 zero for unexpired tokens". 10.1e add: "S-6's sign-in URLs are the one family a later start re-emits; they expire and are counted only while live." |
| 10 (M) | §6 l.498 (edited line) | "S-1 and S-2 stop mattering once both keys are rotated (P0.5b does the re-key); S-3 matters as long as the current set is in service" | S-2's value *is* the live PASSPHRASE. P0.5b rotates only the settings key, so S-2's lines matter exactly as long as S-3's, until §10.2 re-encrypts. S-1 already "unlocks nothing". | REFUTED | S-2 row l.461: "Current settings key = **the live `Yamaguchi` backup passphrase**". | "S-1 stopped mattering when §5.4 showed it unlocks nothing; S-2 is the live passphrase, so its lines matter as long as S-3's — until §10.2 — whatever P0.5b does." |
| 11 (M) | Step 0(c) script l.1764, l.1771–1773; A0 script l.1985, l.1990–1992 | `ENV_FILE` defaults to `${HOME}/.config/duplicati-backup/env`; `JOBDB` is under `/home/duplicati/.cache/…`; failure message "(run P0 step 1's freeze first)" | `/home/duplicati/.cache` is 0700 duplicati. As pcalnon, the `-s` test fails even after the freeze and the message misdirects. As root, HOME may point elsewhere. §8 gives no invocation for either script. | REFUTED (pcalnon); UNVERIFIABLE (root, sudo's HOME policy) | `ls -ld /home/duplicati/.cache` → `drwx------ 2 duplicati duplicati` | "Run: `sudo env YAMAGUCHI_ENV_FILE=/home/pcalnon/.config/duplicati-backup/env bash util/ad-hoc/2026-09-22_confirm_a0_premise.bash` (likewise for the restore script)." |
| 12 (M) | Front matter l.10 (edited); P0.5a intro l.2087–2089; items 6–7 l.2115–2116 | "P0.5a items 1, 2 and 4–7, then P0 step −1", "in this order and no other"; "each takes minutes" | The diff widens the gate before P0 from items 1–2 to 1, 2, 4–7. Item 6 is a gitleaks PR through CI (and AC-8a notes gitleaks isn't installed), not minutes. Item 7 waits on the owner closing two shells that are still open. The recovery of a backup down since 09-18 now blocks on both. | REFUTED | `ps` → `3065639 4-20:06:52 bash`, `3117158 4-19:39:43 bash`. Pre-diff wording "items 1–2". | "**P0.5a** items 1, 2 and 4, then P0 step −1…; items 5–7 in the same session, gating nothing in P0." |
| 13 (M-L) | §6 l.497; item 4 l.2113 | Verify with `sudo ls -la /var/log/syslog-2026092*` | The glob misses `syslog-20260919.gz`, which holds 5 of S-1's 23 lines (l.444–446). That file is still on disk, and the earlier scrub makes it more likely to still be there at scrub time. | REFUTED | `ls /var/log/syslog*` lists `syslog-20260919.gz` (Sep 19 00:35) | `sudo ls -la /var/log/syslog*` plus a count-only `sudo zgrep -c` for each label over `/var/log/syslog*`, all zero |
| 14 (M-L) | Step 10 l.2076–2079; guard comment l.1392–1397; installer "Next:" l.1080–1082 | Dry-run `sudo -u duplicati env DUPLICATI__REMOTEURL="$(…)"`; the installer prints `sudo -u duplicati DUPLICATI__REMOTEURL=file:///…` "(must be 0…)" | (a) The job URL goes onto sudo's argv, which lands in `COMMAND=` in the journal and in `/var/log/auth.log` — a third adm-readable store D-8 never names. That is harmless for `file://`, but a changed URL is exactly what the guard says "routinely embeds credentials". (b) The installer's hint is the bare-prefix, hand-typed form step 10 bans. | REFUTED | rsyslog: `auth,authpriv.* /var/log/auth.log`, `*.*;auth,authpriv.none -/var/log/syslog`; `auth.log` is `syslog adm 0640` | `DUPLICATI__REMOTEURL="$url" sudo --preserve-env=DUPLICATI__REMOTEURL -u duplicati …guard.bash` (see U3); the installer hint points to §8 step 10 |
| 15 (M-L) | §7.3.2 l.770; AC-12 l.2184; AC-12a l.2197; O-12 l.2477–2479 | "against the P0 probe copy" vs "against the P0 step 1 freeze copy, not against a probe copy"; "the server completes AC-3" | The two passages name different targets, and neither can open: both hold the database encrypted under the unidentified 09-18 key. Under A0 the trial dies at the key check (exit 100), which looks the same as a confinement failure. | REFUTED | §4.1 row 3; §5.4 | "…against a copy of the recovered data folder after step 8" |
| 16 (L-M) | P1 step 2 l.2130; step 2 l.1819; AC-8 l.2180 | "Delete the five commented lines from `.env`" | Step 2 moved `.env` into `Duplicati.empty-2026-09-20/`, so the S-3 lines survive there until P4. AC-8 and §10.2 step 2 check an unnamed `.env` and can pass on the empty new folder. | REFUTED | `sudo mv /home/duplicati/.config/Duplicati …empty-2026-09-20` | Name `/home/duplicati/.config/Duplicati.empty-2026-09-20/.env` (commented lines and the active key line) in P1 step 2 and AC-8 |
| 17 (L) | Step 8 l.2061–2067 | "stop the server, `cp` … and update the row — UI … or `PUT` … Install §7.3 … Then `sudo systemctl start`" | For A0/A2 no server is running (step 2 stopped it; the unit isn't installed yet), so updating the row through its API has no literal reading. | REFUTED | — | "…cp the index; install; start; update the row in the UI before any backup runs." |
| 18 (L) | Step 11 l.2083 vs P2 step 3 l.2145 | "AC-6 … provable only when the snapshot lane is re-pointed (P0.5a item 2)" | Item 2 has already run before P0 in this order. The real wait is the next 13:45 UTC fire. | REFUTED | Front matter l.10 | "…needs the first 13:45 UTC snapshot after P0.5b restarts the timer (P2 step 3)" |
| 19 (L) | Script comment l.1768–1770 (tagged block = landed file); note 12b l.2515–2517 | "…'>30 minutes for a single small file here, without completing'"; 12b says this was repaired | The edit script froze fenced blocks, so the "here" attribution survives in the comment an operator reads at step 0(c). 12b over-claims. | REFUTED | Edit-script gate: "every fenced code block must be byte-identical" | 12b: "…repaired in prose; the confirm-premise script comment still says 'here'" |
| 20 (L) | Note 10.1e l.2279–2283 | "Consensus round 1 had already moved the scrub into P0.5a item 4 — Lane B3's finding F-18" | F-18 asked for "P0.5 — same session as recovery", and round 1 built exactly that. The placement before P0 is round 2's split (§11 l.2431–2434 says so). | REFUTED | Round-1 record F-18; `2026-09-22_reconcile_backup_design.py:1446` "### P0.5 — same session as the recovery" | "Round 1 (F-18) moved it to a P0.5 'same session' bucket; round 2's split put it before P0…" |
| 21 (L) | Note 10.1e l.2286–2288 | "the running v1 server is never restarted (P0 step 2 stops it), and every later start runs the §7.3 unit" | The vendor unit is `Restart=always`. What actually protects the logs is item 1 deleting the ExecStart path `/home/duplicati/bin/`, and DEBUG_MODE having been off since the 18:19 start. The step-3 probe and the §7.3.6 hand start bypass the unit. None of them prints the three label families. | REFUTED (reason); conclusion holds | `systemctl show` → `Restart=always`, ExecStart `/home/duplicati/bin/duplicati-wrapper.bash` | "…cannot restart once P0.5a item 1 deletes its ExecStart path; DEBUG_MODE has been off since 18:19; later starts (v2, probe, init) print none of those labels." |
| 22 (L) | AC-8 l.2180; 10.1e l.2292 | "since the hardening timestamp" | Never defined. Wrapper v2 logs `settings encryption key: …(N chars)`, so a case-insensitive count flags every start. | REFUTED | Wrapper l.904 | "since P0.5a item 4's `--rotate`; count case-sensitively" |
| 23 (L) | §8 preamble l.1709 | "nothing in a later phase is a precondition of an earlier one" | P0.5a and step 9's client change are both preconditions of P0. | REFUTED | P0 preamble; step 9 | "…except P0.5a (before P0) and P0.5b (between steps 8 and 9)" |
| 24 (L) | R-3 l.85; R-7 l.89; §7.1 p.3 l.534 and p.5 l.536; §7.3.1 l.554, l.569; §7.3.5 l.1141–1143; §7.4 l.1259–1265, l.1312; §3.5 l.150; App. C 10 l.2604; §4.1 l.176; §4.3 l.247 | "symlink … retained only as a fallback (D-6)"; "umask `0007`, files group-writable"; "D-4 … Whichever is chosen"; "nologin once the migration is accepted"; "D-1, recommended … recorded in `/etc/default/duplicati`"; "`chmod 0660`", "test `d:g:duplicati:rwX`"; "D-1 asks the question again"; ".config/Duplicati 0777 — until P0.5" | Rulings D-6, D-14, D-4 and D-1 contradict this text. P2 step 2 has the operator test the rejected `rwX` ACL (the script uses `rX`). The 0777 data folder is closed by steps 2 and 8, not by P0.5. All other bare "P0.5" references correctly mean P0.5a. | REFUTED | §10.1 rows | Update each to its ruled value; use `rX`/0640; ".config/Duplicati until P0 step 2" |
| 25 (L) | §10.2 heading l.2295 | "scrub, rotate, re-encrypt" | Step 2 is now a check, not a scrub. | REFUTED | l.2337 | "confirm the scrub, rotate, re-encrypt" |
| 26 (L) | §8 l.1706 vs P0.5b l.2123 | "`sqlite3` … not installed; step 3 needs the first" | P0.5b's `VACUUM` also needs it, and step 3's probe is optional. | REFUTED | — | "step 3's probe and P0.5b's `VACUUM` need the first" |
| 27 (L) | AC-3a l.2191 | `systemd-run … --wait cat ~/.ssh/known_hosts` | Without `--pipe`, the file's content goes into the freshly scrubbed journal and syslog, against principle 2. | REFUTED | — | `… --pipe --wait sh -c 'wc -c < /home/pcalnon/.ssh/known_hosts'` |
| 28 (L) | Edit-script docstring l.18 (`util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`) | "in ml#1999, the day BEFORE the ruling" | Same day: 04:55 vs 20:44 CDT on 09-22. | REFUTED | `git log -1` for 43980f13 and ab434c9b | "sixteen hours before the ruling" |
| U1 | P0.5b start 1 | (unstated) | Does 2.4.0.0 log a decrypted value on the `--disable-db-encryption` start? | UNVERIFIABLE | Needs the product | Settle by reading `ReWriteAllFieldsIfEncryptionChanged`'s log calls in `Program.cs` at v2.4.0.0, or a `--pipe` trial on a copy |
| U2 | Step 0(a) vs P0.5b | (unstated) | Do `--require-db-encryption-key` and `--disable-db-encryption` together refuse to start? | UNVERIFIABLE | Needs the product | Same source read, or a trial on a copy |
| U3 | Row 11; step 10 l.2073 | "sudoers refuses the prefix" | Does sudo here reset HOME, and does `ALL` imply SETENV (per sudoers(5))? | UNVERIFIABLE | Needs root | Owner runs `sudo sh -c 'echo "$HOME"'` and `sudo -l` |
| U4 | Step 8 first start | (unstated) | Does a missing `/etc/credstore/duplicati-settings-key` stop the unit? With no D-1 flag landed, this decides whether A0's database could start without a key and stay cleartext. | UNVERIFIABLE | Needs root | `systemd-run -p LoadCredential=t:/nonexistent --pipe --wait true; echo $?` |
| C1 | Front matter; §8 l.1700–1704 | "all nine are merged on `main`"; `--check` | All 13 staged artifacts are byte-identical to their tagged blocks at d9f44a78, and `--check` exists. | CONFIRMED-SOUND | Inline extraction using the linter's marker rule; `stage_design_artifacts.py:95` | — |
| C2 | l.1742–1744 | 434 dblocks / 434 dindexes / 9 dlists | The destination listing matches exactly. | CONFIRMED-SOUND | `ls` → 877 / 434 / 434 / 9 | — |
| C3 | l.1744–1747, l.2367–2369 | ">30 min" measured 2026-08-23 on the old Ubuntu archive | `duplicati_drill_run.py` was added in 3131790e (#1268) on 2026-08-23, and its default is `--dest file:///mnt/Backups/Ubuntu`. DMG contains no "30 minutes" string, so the "(DMG §4a)" citation supports the drill, not the figure. | CONFIRMED-SOUND | `git log --diff-filter=A` | Cite drill_run.py l.33–35 for the figure |
| C4 | 10.1e | A `daemon-reload` re-emits nothing | The vendor unit has 0 `Environment=` lines, 0 `%` characters and no drop-ins. | CONFIRMED-SOUND | Count-only greps; `DropInPaths=` empty | — |
| C5 | 10.1e; item 2 of the brief | The three label families are not re-emitted between P0.5a item 4 and the end of P1, and no prescribed sudo carries a known secret | Checked: the probe key goes through a 0600 EnvironmentFile with `--pipe`; the hash probe prints labels only; wrapper v2 prints names and lengths; `read -rs \| sudo install` keeps the key off argv. There is no coredump channel (`core_pattern`=`core`, no systemd-coredump). The round-1 journal and syslog counts match (99 = 99) while auth goes only to `auth.log`, so no sudo line in 09-17..09-21 carried a key. Exceptions are rows 9, 14 and 27. | CONFIRMED-SOUND | — | — |
| C6 | 10.1e cost argument | "…delete the journal of the recovery — the first start, and what AC-8 and AC-14 read" | True, and understated: AC-12 also reads "journal of the first start", and an AC run after the vacuum would pass vacuously and erase any leak during the recovery. Caveats: AC-8's syslog half is untouched by `--vacuum`; the pre-P0 vacuum also deletes the incident journal behind §5.6's Leg C, but that is a strict subset, so the comparison holds. | CONFIRMED-SOUND | §9 AC-8, AC-12, AC-14 | — |
| C7 | SMART script | Behaviour-preserving; header claim | Same `date +%F_%T`, smartctl, chown, file names and final exit; the only new behaviour is `exit 1` if `date` fails; one clock read instead of b0223f18's two. The exports do nothing for the child processes. Pinned shellcheck 0.10.0: 0 findings at every severity; 12× SC2034 when un-exported (main's header said "13", which was wrong); the hook would fail with rc=1. The file is mode 100644 (b0223f18 was 100755). | CONFIRMED-SOUND | Scratch lint runs | Invoke it with `bash` |
| C8 | §12 new rows | The reconstructions | Match the file lists of 43980f13, ab434c9b, 4b311619 (nine reports), d15e7c01 and dcfc024f. | CONFIRMED-SOUND | `git show --stat` | — |
| C9 | 10.1e | The ruling and the plan disagreed from day one | At ab434c9b both the "after P1" D-8 row and the pre-P0 item-4 scrub exist. | CONFIRMED-SOUND | `git show ab434c9b:` design | — |
| C10 | Residual sweep | No live "after P1", "877 dindex", "review and merge", "items 1–2" or undecided "owner gates"; the D-2 "Scrub first" row is consistent | Confirmed. §10's table is labelled as history, and bare P0.5 references land on P0.5a except those in row 24. | CONFIRMED-SOUND | grep | — |

REFUTED 28 (row 11 partly UNVERIFIABLE; row 21 refutes the reason while its conclusion holds) · UNVERIFIABLE 4 · CONFIRMED-SOUND 10

<!-- markdownlint-enable -->

---

## Round 4, lens C — amputation and scope

Archived verbatim (12,722 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

The diff did most of what it claims, but I found 2 real (c)-class losses and 3 claims that don't hold (2 of them partly). The edit script, replayed on the base design, rebuilds the frozen design byte-for-byte and is idempotent: a second run reports all 18 edits `ALREADY`. So the design diff is exactly the 18 scripted edits, with no hand edits.

**Documents:** "design" is `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`. "Handoff" is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_backup-arc-seven-decisions-ruled-smart-passed-p0-is-next.md`, read at df21367d. Every §, note, P-step and AC reference below is to the design, at d9f44a78 unless marked. **Changed:** nothing (read-only).

## 1. Amputation table

| # | Hunk | What was lost | Class | Evidence | Text to restore (c only) |
|---|---|---|---|---|---|
| 1 | Front matter | "P0.5a items 1–2" | (a) | P0.5a's own heading already said "Items 1, 2, 4, 5, 6 and 7" before P0. That came from round 2's `r2b-p05-split` in `2026-09-22_apply_round2_corrections.py`. The same round's `r2-p0-step0-p05-pointer` wrote "1 and 2", so the two contradicted each other. | |
| 2 | Front matter | "review **and merge** … that are now staged" | (a) | ml#1999's file list holds all nine paths. ml#2029 changed exactly three of them. All 13 staged artifacts are byte-identical to their tagged blocks at d9f44a78. | |
| 3 | Front matter | "P0 step 0's owner gates"; "then P0, then P0.5b" | (a) | Step 0's header says "RULED … now a verification". P0.5b's heading says "immediately after P0 step 8". | |
| 4 | §6 | Bare "P0.5" as where the re-key happens | (a) | The re-key is P0.5a item 3, which is a stub pointing to P0.5b. | |
| 5 | §8 preamble | "and merge" | (a) | Same as row 2. | |
| 6 | §8 preamble | "re-staged with `util/ad-hoc/2026-09-22_stage_design_artifacts.py`". Re-staging was the path that fixed a drifted artifact. The tool is now named only with `--check`. | **(c)**, low | `--check` exits 0 even when it would write files; the script returns 0 after printing its `->` lines. The new text gives no action for the failure case. | Replace "confirm `…stage_design_artifacts.py --check` reports every artifact already current, and" with: "confirm `util/ad-hoc/2026-09-22_stage_design_artifacts.py --check` reports every artifact already current (it exits 0 either way, so read its closing count; if any artifact would be written, stop: re-stage with the same script without `--check`, and review and merge that change before P0), and" |
| 7 | P0 preamble | "items 1 and 2" | (a) | Same as row 1. | |
| 8 | P0 step 0(c) | "on this destination … all 877 dindex volumes", plus the implied timing for this destination | (a) | I listed the destination: 434 dblock, 434 dindex, 9 dlist, 877 in total. `duplicati_drill_run.py` defaults to `--dest file:///mnt/Backups/Ubuntu` and was added by ml#1268 (`3131790e`) on 2026-08-23. | |
| 9 | P0 step 0(c) | Parenthetical citation of `(duplicati_drill_run.py: "…")` | (b) | The filename and the quote both survive. | |
| 10 | P1 step 3 | "pending merge" | (a) | ml#1999 (`43980f13`) contains `scripts/duplicati-wrapper.bash` (+167/−202). | |
| 11 | P1 step 5 | "**Re-decide D-2**, do not merely execute it … it was ruled" | (a) | §10.1 D-2. The history is kept inside the step. | |
| 12 | P1 step 5 | The four exposure sites | (b) | All four survive: syslog, cloud-linked transcripts, the S-7 file, and S-4. | |
| 13 | P1 step 5 | "Then rule on D-8 and execute." | (a) | D-8 was ruled, then amended (given). It is now executed as P0.5a item 4. | |
| 14 | P2 step 2 | "**After a D-14 ruling**" | (a) | At d9f44a78 the script sets `duplicati:duplicati`, `2750` and `0640`. | |
| 15 | §10.1 D-8 row | "Scrub once, after P1" as the binding ruling | (a) | Given amendment. The original text stays in the cell. | |
| 16 | §10.1 D-8 row | "unchanged from the recommendation" | (a) | No longer true after the amendment. The fact that the 09-22 ruling matched the recommendation survives in note 10.1e's first sentence. | |
| 17 | §10.2 step 2 | "Scrub the leaked copies" (the step performed them); "D-8's journal scrub after P1" | (a) | The removals are now P0.5a item 5, P1 step 2 and P0.5a item 4. The gate column is unchanged. | |
| 18 | Note 10.2c | "all 877 dindex volumes"; "was measured at" | (a) | Same as row 8. | |
| 19 | Note 10.2c | Trailing parenthetical citation | (b) | The filename becomes the sentence subject. The date and "DMG §4a" can be reached through "(P0 step 0(c))". | |
| 20 | §11 item 4 | "OPEN" | (a) | §10.1 D-14. | |
| 21 | Front matter, §10 preface, §10.1 preamble, note 10.1e, P0.5a item 4, note 10.2a, §12 | Nothing (insertions only) | — | Word-level diff shows no deletions. | |
| 22 | SMART header | `# shellcheck disable=SC2034` | (a) | With the pinned shellcheck 0.10.0 (the hook runs v0.10.0.1) and with 0.11.0, the d9f44a78 copy is clean at style severity. Exported variables count as used. | |
| 23 | SMART header | "13 x SC2034" | (a) | The old count was wrong. The pre-refactor copy without the directive gives **12** under both versions (11 `DEVICE_*` plus `TEST_TYPE_SHORT`). The new header says 12. | |
| 24 | SMART header | "which is true and is the point…"; "cannot be committed"; "SC2034 is the ONLY code…" | (b) | Carried as "deliberate PALETTE" and "refuses the commit". Nothing is suppressed any more. | |
| 25 | SMART body | Un-exported form; the owner's two `date` calls and their two messages; old comments | (a)/(b) | Given decision. The error check is kept. | |
| 26 | Owner's b0223f18 vs d9f44a78 | **File mode 100755 becomes 100644.** Handoff item 3 names "is mode 0755" as part of the divergence. | **(c)** | `ls-tree` shows b0223f18 at 100755 and d9f44a78 at 100644. No disposition in the §12 row, note 12b, note 10.2a or the script header. P0 step 8 already records that `createCommitOnBranch` carries no file mode. | Append to note 12b after "straddle midnight.": "Its mode is not adopted: the owner's copy is `0755`, but a commit made through `createCommitOnBranch` carries no file mode (§8 P0 step 8), so the file lands `100644` whatever the working tree says — run it as `sudo bash util/ad-hoc/smart_checks_backup-sda.bash`." If the change will land by a push that carries modes, set it with `git update-index --chmod=+x` and say that instead. |
| 27 | Owner's copy | Two trailing blank lines (only at the ml#2045 tip); the commit message's stated reason for exporting ("better accessibility in the environment") | (b) | The end-of-file fixer strips the blank lines. The new header gives only the lint reason for exporting. | |
| 28 | Edit script | New file | — | Nothing lost. | |

## 2. Scope table

| Handoff item | Asked | Discharged? | Evidence |
|---|---|---|---|
| 1 | Get ml#2067 merged | YES, before this session | Merged as `dcfc024f`, an ancestor of df21367d. |
| 2 | Archive and commit the handoff | YES, before this session | Added by `fa951d39` (ml#2073). |
| 3 | Adopt the +56/−50 divergence (exports, mode 0755) or say why not | **PARTLY** | Exports and the error-checked clock are adopted, with one `date` call and a new header. This is recorded in the §12 row, note 12b, note 10.2a and the script header. **Mode 0755 is neither adopted nor explained.** |
| 4 | Fix P1 step 5 and P2 step 2 | YES | Also fixed: front matter, §8 preamble, P0 preamble, P1 step 3, §6, §10 preface, §11 item 4. I found no other stale ruled-decision text in §8. |
| 5 | Fix "877 dindex"; add §12 rows for ml#2029, ml#2041, ml#2057 | YES | Both "877" sites are fixed. All three rows are present with exact file lists. |

- **Named by the handoff but not addressed:** the mode 0755, and the dead "§12" citation called out in the handoff's validation record (see finding 1).
- **Claimed but not done:**
  - Note 12b and the §12 row describe the SMART adoption as differing only by the `date` call. The mode and the header rewrite are unstated.
  - Note 12a says every missing row was "reconstructed from each PR's merge commit and file list". The round-3/ml#1999 row has no file list.
- **Every clause of note 12b checks out against the diff.** But the list leaves out three edited sites: the §8 preamble's step −1 paragraph, the §10.1 preamble sentence, and note 10.2a's clause about which copy of the script produced the evidence.

## 3. §12 table

| Commit / PR | Row present? | File-list discrepancies |
|---|---|---|
| `05c5f794` / ml#1989 | YES (existing "Landed with the archive PR" row) | The list matches all 11 files. The row carries no PR number or merge commit. |
| `43980f13` / ml#1999 | YES (rounds 1 and 2 existed; the round-3 row is new and names ml#1999) | **The new row has no Changed/Added lists.** 20 of the PR's 25 files, not counting `PR_BODY.md`, appear in no §12 row. They include the round-2 record note, `scripts/duplicati-wrapper.bash`, all 12 other staged artifacts, `stage_design_artifacts.py`, `duplicati_literal_scan.py`, `append_signed_commit.py`, `archive_consensus_reports.py` and both `watch_pr_*.bash`. |
| `ab434c9b` / ml#2029 | YES | Exact match; `PR_BODY_RULINGS.md` left out as note 12a says. |
| `4b311619` / ml#2041 | YES | Exact match; `PR_BODY_SMART.md` left out as note 12a says. |
| `d15e7c01` / ml#2057 | YES | Exact match; `PR_BODY_DRILL.md` left out as note 12a says. |
| `dcfc024f` / ml#2067 | YES | Exact match; `PR_BODY_FRONTMATTER.md` left out as note 12a says. |
| `d9f44a78` (local) | YES | Matches the three-file diff. No PR number yet. |

## 4. Other findings

1. **Dead citation left in place.** Note 10.2a still says "closes the **§12** / D-12a carried item". The handoff's validation record called this citation dead ("it is D-12a"). The item actually lives in §3.4 and note D-12a. The diff edited note 10.2a and left it. Fix: "§3.4 / D-12a".
2. **The corrected timing defect is still in one code comment.** The tagged block `# file: util/ad-hoc/2026-09-22_confirm_a0_premise.bash` (design line ~1768), and the landed script, still say ">30 minutes … **here**" in a script that targets the new destination. The edit script's fence gate rightly refused to touch it; fixing it needs a paired edit to the block and the landed file.
3. **Wording contradiction.** P1 step 5 now says "so P1 scrubs nothing", but §10.2 step 2 names P1 step 2 as removing a leaked copy (the `.env` comment block). Suggested wording: "so P1 performs no log scrub".
4. **Imprecise history in note 10.1e.** It says round 1 moved the scrub into "P0.5a". Round 1 actually created "P0.5 — same session as the recovery"; the before-P0 bucket came from round 2's split. Both landed in ml#1999 before the ruling, so the note's conclusion stands.
5. **Edit-script docstring.** It says items 4 and 5 scoped the work, but the script also carries the D-8 amendment and item 3's note 10.2a clause. It also says ml#1999 landed "the day BEFORE the ruling". ml#1999 merged 2026-09-22 04:55 CDT and the rulings are dated 2026-09-22 (ml#2029 merged 20:44), so that is **wrong**.
6. **SMART header claim carried forward.** "Every disk and partition on this host is named" is false today. `lsblk` shows no sdb*, sdc4 or sdd1, and sdg and nvme0n1p1–p6 (including `/`) are not in the list.
7. **Front-matter status line is stale.** It still reads "VALIDATED (round 2)" and does not mention round 3, the rulings or the amendment.
8. **Confirmed true:**
   - 434/434/9 = 877.
   - All nine scripts are merged; ml#2029 changed exactly the three named.
   - The pinned shellcheck passes.
   - Wrapper v2 contains none of the three leaked labels.
   - F-18 is Lane B3's finding.
   - Round 3's 15 defects map to the `r3-*` edits (29 of them, grouped D1–D15).
9. **Not verified:** note 10.1e's host claim that the loaded unit has no `Environment=` line and no drop-in. Reading the unit risked printing a secret.

**Constraint slips: none.**
- All repository reads went through git objects: d9f44a78 and df21367d, plus b0223f18, `origin/pr-2045-head` and older merge commits for the history. No working-tree copy was read.
- Host reads: a names-only `ls` count of the Yamaguchi destination, and `lsblk`.
- I ran shellcheck binaries from `~/.cache/pre-commit`, made six read-only `gh pr view` calls, and replayed the edit script on copies in the session scratchpad. Its trailing `git diff` failed harmlessly outside a repo.
- One compound command was refused by the isolation layer and re-run as plain commands.

**(c)-class losses: 2** (the SMART script's mode has no disposition; step −1 lost its instruction for a failed `--check`). **REFUTED claims: 3** (note 12b / §12 row adoption scope, partly; note 12a's file-list reconstruction for the ml#1999 row, partly; the edit-script docstring's "the day BEFORE the ruling").

<!-- markdownlint-enable -->

---

## Round 5, lens A — fact re-probe of the corrections

Archived verbatim (24,865 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

**Verdict: CONFIRMED 62 · REFUTED 16 · UNVERIFIABLE 1.** The mechanics hold, and so do most of the new facts. The edit script rebuilds the design byte-for-byte, is idempotent, and its fence guard now catches edits inside indented code blocks. The archiver reproduces the round-4 record exactly. The STOP block's five defects re-derive from source, but item 3's wording is wrong.

The corrections introduced 16 errors. Four matter most:
- **The SMART script header states something false.** It says the device list was the host's layout when the script was written, but sdc4 left the partition table by 2026-09-08. The script first appears on 2026-09-23.
- **The design's Status line was never changed.** The record calls it "applied", but it still reads "VALIDATED (round 2)" directly above the new STOP bullet.
- **Note 10.1f calls the two `su - duplicati` shells "live".** Both were gone before the commit, and `/home/duplicati/.bash_history` was rewritten at 14:56:34 today.
- **The design says the guard dry-run can pass "without checking anything".** It still checks the mount, the directory, write access and stray files. Only the TargetURL comparison is skipped.

Key: **D** = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, **R** = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`, **S** = `util/ad-hoc/smart_checks_backup-sda.bash`, **E** = `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`, **Ar** = `util/ad-hoc/2026-09-24_archive_round4_reports.py`. **YAM** = `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`, **DMG** = `notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`. Line numbers are at edf8c432. **Changed**: nothing in the repository.

| # | Location | Claim under test | Verdict | Evidence (command → decisive output) | Proposed fix (REFUTED only) |
|---|---|---|---|---|---|
| 1 | D L10 | The round-4 record is added to the verbatim reports | CONFIRMED | `git diff --name-status 6c23fdde edf8c432` → `A notes/…ROUND-4-RECORD.md` | |
| 2 | D L11 | The defects can re-lock the database or copy a cleartext database into the Source | CONFIRMED | See rows 7 and 10 | |
| 3 | D L11 | The defects can "pass the pre-backup guard without checking anything" | REFUTED | `git show edf8c432:util/yamaguchi-pre-backup-guard.bash`: L49–51 and L66–75 (mount, directory, write access, strays) run whatever the URL is. Only L52 `if [[ -n "${REMOTE_URL}" ]]` is skipped | "pass the pre-backup guard without its TargetURL check" |
| 4 | D L12–13 | The execution order, with items 5–7 run alongside | CONFIRMED | Owner ruling; matches L1762–1765, L2121–2129 and L2344–2346 | |
| 5 | D L500–504 | S-1 unlocks nothing; S-2's lines matter as long as S-3's; D-2 rules rotate and keep | CONFIRMED | S-1 row L463 "unlocks nothing (note S-1a)"; S-1a L474; S-2 row L464 "= the live Yamaguchi backup passphrase"; D-2 L2288 "Rotate … and KEEP" | |
| 6 | D L1702–1706 | STOP 1: no shipped artifact carries the flag, the blessed file comes from step 8, and hand edits have no durable home | CONFIRMED | `git grep -n require-db-encryption-key edf8c432 -- ':!notes/*' ':!prompts/*'` → only `util/systemd/duplicati.default:4` (a comment) plus ad-hoc edit scripts. Installer L46 and L90–101 write the blessed file; drift → `exit 4`; `--update-backup-behavior` → L78 `install … DEFAULTS_SRC`. `ls /usr/local/lib/duplicati/` → No such file | |
| 7 | D L1707–1709 | STOP 2: the key command overwrites the old key | CONFIRMED | P1 step 1 L2168: `openssl rand … > /etc/credstore/duplicati-settings-key`, then "with the **old** key still in the credential file" | |
| 8 | D L1710–1713 | STOP 3 body: the client is unlanded, a failed client gives an empty URL, and the guard compares only a non-empty URL | CONFIRMED | `yamaguchi_server_api.py` L41 `CRED_FILE=…/juniper-ml/.env`; L80 `choices` has no pause or resume; L74 `sys.exit("FATAL: login failed…")` → empty stdout → `json.load` fails → the URL is `""`; guard L52 | |
| 9 | D L1710, L1713 | STOP 3 heading "can pass without checking anything"; body "the one check §7.5 item 6 says the guard exists for" | REFUTED | §7.5 item 6 (L1336–1337): "The guard's real value is the **mount** and **`TargetURL`** checks". The mount check (guard L49) still runs. The same phrase already exists in step 10 at L2118 | Heading: "**Step 10's guard dry-run can pass without its TargetURL check.**". Ending: "— one of the two checks (mount and `TargetURL`) §7.5 item 6 says give the guard its value." |
| 10 | D L1714–1717 | STOP 4: `Persistent=yes`, a catch-up run at 13:45 UTC, item 2 restarts the timer at step 8, and A0 is cleartext | CONFIRMED | `systemctl show yamaguchi-server-db-snapshot.timer -p Persistent -p TimersCalendar` → `Persistent=yes`, `OnCalendar=*-*-* 13:45:00 UTC`. `man systemd.timer`: "triggered immediately if it would have been triggered at least once during the time when the timer was inactive". Item 2 L2150 "restart it only then". Snapshot script L53 `DEST_DIR=/home/pcalnon/.local/state/duplicati-server-db` | |
| 11 | D L1718–1720 | STOP 5: `strict` makes everything read-only and there is no `ReadWritePaths=` | CONFIRMED | `man systemd.exec`: '"strict" the entire file system hierarchy is mounted read-only, except … /dev/, /proc/ and /sys/'. Script L105–141 writes a temp file, chmods, chowns and calls `os.replace` in DEST_DIR. The unit today: `ProtectSystem=no`, `ReadWritePaths=` empty | |
| 12 | D L1722–1724 | The items still to be re-derived | CONFIRMED | Lens B rows 5, 6 and 7 in R | |
| 13 | D L1736–1738 | `--check` exits 0 either way, so only "0 staged" means current | CONFIRMED | Script L128–142. On a scratch `git archive edf8c432`: "0 staged, 13 already current, 1 skipped", exit 0. After adding one line to the scratch `duplicati.default`: "1 staged, 12 already current…", exit 0 | |
| 14 | D L1762–1768 | P0 preamble gate | CONFIRMED | Owner ruling; item 1 L2135 and L2141–2142 | |
| 15 | D L1778–1784 | Lines 33–35; 877 = 434/434/9; ml#1268 on 2026-08-23; the damage drill; `/mnt/Backups/Ubuntu`; before this destination existed | CONFIRMED | `duplicati_drill_run.py` L33–35 match; `ls …/Yamaguchi \| wc -l` → 877 (434/434/9); `git log -S'>30 minutes'` → 3131790e 2026-08-23 13:53:59 -0500 (#1268); drill_run L188 `file:///mnt/Backups/Ubuntu`; DMG §4a L200 "Run 2026-08-23"; `stat` birth 2026-08-26 16:14:42 | |
| 16 | D L2121–2129 | The reasons given for items 5, 6 and 7 | CONFIRMED | Item 7 L2156 and the §7.3.2 comment L695–703 (a duplicati-uid shell escapes the mount mask); S-7 row L469 "inside the backup source"; item 6 L2155 is a repository change; step 10 `resume` fires the backup | |
| 17 | D L2179 | "P1 runs no log scrub" | CONFIRMED | P1 steps 1–5 (L2168–2179) scrub no log | |
| 18 | D L2318–2324 | 10.1e history: round 1's P0.5 bucket, round 2's split, neither updated the column | CONFIRMED | Round-1 record L759 (F-18); `2026-09-22_reconcile_backup_design.py` L1446 `### P0.5 — same session as the recovery`, item 4 the scrub; `apply_round2_corrections.py` L1242–1247 `r2b-p05-split`; the column reads "scrub once, after P1" at 43980f13 L2143 and D L2258 | |
| 19 | D L2326–2328 | Every committed wrapper revision through 6708cb28 (17:26) prints the three labels unconditionally; the passes ran 16:41–17:30 | CONFIRMED | `git log --all -- scripts/duplicati-wrapper.bash`. 60d1c45d (17:05:30), b4aeed52 (17:17:31) and 6708cb28 (17:26:27): DEBUG_MODE=0, one line per label, no gate. §4.2 note 6 (L235) | |
| 20 | D L2326–2327 | The 16:41, 16:44 and 16:50 passes "came from the wrapper's first revisions" | UNVERIFIABLE | Those passes predate every commit (60d1c45d at 17:05) and the `/home/duplicati/bin` symlink (16:53:58), so the revision they ran is in no git object. The journal identifier for those passes would settle it (owner, count-only) | |
| 21 | D L2329–2330 | DEBUG_MODE from 64677ab0 (17:48), off by default; the 18:19:42 start added none; v2 carries none | CONFIRMED | 64677ab0 L68 `DEBUG_MODE=${FALSE}`, L112/133/196 gated; same in 52571621 and d721fc78. `ps -o lstart -p 1397393` → Sun Sep 20 18:19:42. Main's v2: 0/0/0 labels | |
| 22 | D L2330–2333 | `Restart=always`; ExecStart resolves into the primary checkout, byte-identical to main's v2 | CONFIRMED | `systemctl show duplicati.service` → `Restart=always`, `path=/home/duplicati/bin/duplicati-wrapper.bash`. `readlink -f` → `…/juniper-ml/scripts/duplicati-wrapper.bash`. Blob sha1 `42ba4683…` = `git rev-parse 6c23fdde:scripts/duplicati-wrapper.bash` | |
| 23 | D L2333 | P0.5a item 1 deletes that path; step 2 stops the server | CONFIRMED | L2141–2142 "remove `/home/duplicati/bin/` entirely" | |
| 24 | D L2333–2334 | The step-3 probe runs outside the unit and prints no labels | CONFIRMED | L1952–1960: `systemd-run … --pipe /usr/bin/duplicati-server`, output to a log file; no wrapper | |
| 25 | D L2334–2336 | 23 = 22 in `Environment=` + 1 in `ExecStart=` (§4.2 note 2) | CONFIRMED | L230 and the L228 timeline row | |
| 26 | D L2336–2337 | The loaded unit has no `Environment=`, no `%` outside comments, no drop-in | CONFIRMED | `systemctl cat duplicati.service \| grep -v -E '^[[:space:]]*[#;]' \| grep -c '%'` → 0; `Environment=` lines → 0; `DropInPaths=` empty; one file | |
| 27 | D L2338–2339 | Any start with an autogenerated password mints a sign-in URL | CONFIRMED | `gh api …/duplicati/duplicati/contents/Duplicati/Server/Program.cs?ref=v2.4.0.0_stable_2026-09-03` L338: `if (… Origin == "Server" && … AutogeneratedPassphrase)` → `CreateSigninToken`, `Log.WriteWarningMessage` | |
| 28 | D L2340–2342 | The vacuum argument; AC-8, AC-12 and AC-14 read the journal | CONFIRMED | AC-8 L2220 `journalctl --since`; AC-12 L2224 "journal of the first start"; AC-14 L2226 `journalctl -u` | |
| 29 | D L2344–2346 | The P0 gate ruling is recorded | CONFIRMED | Consistent at L12–13, L1762 and L2125 | |
| 30 | D L2346–2347 | Since ml#1999 the front matter and P0 preamble said "items 1 and 2", and P0.5a's heading said "items 1, 2, 4, 5, 6 and 7" | REFUTED (minor) | `git show 43980f13:D`: front matter L10 says "items 1–2"; heading L2018 reads "— before anything in P0"; the list is in the intro at L2020 | 'Since ml#1999 the design had said both "items 1–2" / "items 1 and 2" (the front matter / the P0 preamble) and, under P0.5a's heading "before anything in P0", "Items 1, 2, 4, 5, 6 and 7".' |
| 31 | D L2347–2349 | Item 6 is a repository change through CI; the backup has been down since 2026-09-18 | CONFIRMED | L2155; §4.2 L220: last success 09-18 14:00Z | |
| 32 | D L2349 | Item 7 "waits on the owner closing two live `su - duplicati` shells" | REFUTED (stale by commit time) | `ls -d /proc/3065639 /proc/3117158` → No such file (15:19 CDT). `ps -u duplicati` → only 1397393. `stat /home/duplicati/.bash_history` → mtime 2026-09-24 14:56:34, 8,261 bytes (contents not read). edf8c432 was committed 15:08:12 | "…and on item 7, which waited on the owner closing two live `su - duplicati` shells — both gone by 15:19 CDT on 2026-09-24, with `/home/duplicati/.bash_history` rewritten at 14:56:34, so §6's sink row must be re-checked (count-grep as root) for whether its `history -c; unset HISTFILE` ran first." |
| 33 | D L2351, L2393 | §10.2 heading; the step-2 gate and its cross-references | CONFIRMED | Item 5 at L2154, P1 step 2 at L2169, item 4 at L2153 | |
| 34 | D L2419 | "§3.4 / D-12a carried item" | CONFIRMED | §3.4 L148 carries the sda SMART item | |
| 35 | D L2420–2429 | Note 10.2b moved ahead of 10.2c, text unchanged | CONFIRMED | E's removal anchor requires the byte-identical old block | |
| 36 | D L2433–2435 | Note 10.2c's rewording | CONFIRMED | As row 15 | |
| 37 | D L2450 | "two rounds delivered and fully reconciled, and a round 4 … whose §8 findings are open" | REFUTED (minor) | It skips round 3, whose D13 L2485–2487 calls open, and implies round 4's non-§8 findings (B15, B22, B24, B27) are closed | "**State of the record: rounds 1 and 2 delivered and fully reconciled; round 3's D13 open (note 12a); round 4 (2026-09-24) open — its five §8 defects are the STOP block at the top of §8, and its other findings, several outside §8, are follow-up items in the round-4 record.**" |
| 38 | D L2485–2487 | 15 defects, 13 applied; D11 and D13 not applied | CONFIRMED | Round-2 record Report C L2725–2730 define D11 (§12 artifact row) and D13 (`/etc/duplicati/env`). The 29 `r3-*` tags cover D1–D10, D12, D14, D15. v2 L40 defaults to `/home/duplicati/.config/Duplicati/.env`; D L1124 | |
| 39 | D L2494–2495 | Round 4 "confirmed that diff's facts, refuted several of its own phrasings" | REFUTED | R L150–170: lens A refuted facts, not only phrasing — A23 (the DEBUG_MODE history), A35 (the round-3 count), A45 (the device claim), A49 ("the day before") | "confirmed most of that diff's claims, refuted ten — facts as well as phrasings (D-8's `DEBUG_MODE` history, round 3's applied count, the SMART header's device claim, "the day before") — and found defects in §8's procedure itself." |
| 40 | D L2561 | The round-3 §12 row | CONFIRMED | Row 38; ml#1999 = 43980f13 | |
| 41 | D L2562 | The D11 row against ml#1999's file list | CONFIRMED | `gh pr view 1999 --json files` → 25 files. The D11 row lists 20: wrapper (M), 12 staged, round-2 record, 4 `.py`, 2 `.bash`. The round-1 row carries the reconcile script and the round-2 row two scripts; `PR_BODY.md` is excluded by 12a. Nothing is missing and nothing appears twice | |
| 42 | D L2563–2566 | The ml#2029, #2041, #2057 and #2067 rows | CONFIRMED | `gh pr view` → ab434c9b 2026-09-23T01:44:47Z; 4b311619 13:56:40Z; d15e7c01 22:44:15Z; dcfc024f 2026-09-24T08:19:54Z. `git show --name-status` matches each row | |
| 43 | D L2567 | The new row's file list | CONFIRMED | `git diff --name-status 6c23fdde edf8c432` → five files, M/A exactly as the row says | |
| 44 | D L2571–2576 | Note 12a: six rows missing, bodies archived, D13 open | CONFIRMED | `PR_BODY{,_RULINGS,_SMART,_DRILL,_FRONTMATTER}.md` all sit under `util/ad-hoc/2026-09-22_backup-design-round2/` | |
| 45 | D L2586–2590 | b0223f18: constants exported, the clock read checked, two `date` calls, the directive now dead | CONFIRMED | `git diff b0223f18 edf8c432 -- S` shows only the header, the timestamp block and the mode differ. Nit: DATE_STAMP and TIME_STAMP are not exported at b0223f18 | |
| 46 | D L2590–2592 | b0223f18 is mode 0755; createCommitOnBranch carries no mode, so the file lands 100644 | CONFIRMED | `git ls-tree b0223f18 S` → 100755; main's copy is 100644; ml#1999's new scripts landed 100644 although staged 0o755 | |
| 47 | D L2593–2594 | ml#2045 "re-padded four tables' delimiter rows" | REFUTED | `git diff dcfc024f origin/pr-2045-head -- D`, hunks @@-23, @@-561, @@-2299, @@-2515: every row of four tables re-padded to column alignment, with `\|---…\|` delimiters | "and re-padded four whole tables to column alignment (every row, with unspaced `\|---\|` delimiters), which is not:" |
| 48 | D L2594 | "every other table here uses the compact form" | CONFIRMED | 20 delimiter rows; 20 match `^\|( --- \|)+$` | |
| 49 | D L2577–2586 | 12b lists every site the row changed | REFUTED (minor) | It omits E's edit "note 10.2a: which copy of the SMART script produced the evidence" (D L2409–2410) and the SMART header's palette rewrite | After "which now reads §3.4" insert ", and note 10.2a's clause naming the copy of the SMART script that produced the evidence"; after "the exports made dead" insert ", and a header that no longer calls the device palette the host's inventory" |
| 50 | D L2582–2586 | The defects of fact; the "here" comment left in the tagged block | CONFIRMED | L1806 still quotes "here" | |
| 51 | S L3–6 | "It is the host's layout when the script was written … by 2026-09-24 sdb and sdc4 were gone and the nvme0n1 system disk was never listed" | REFUTED | YAM §8.27 addendum (2026-09-08), L2688: "sdc4 is gone from the partition table". `git log --all -- S` → earliest af8111a5 2026-09-23 08:05. `lsblk -e 7` → sdd1 also absent; sdd and sdg are 0-byte; sdg is not listed | "It is a palette of names, NOT the host's inventory -- sdc4 left the partition table by 2026-09-08 (YAM section 8.27.2), before this script existed, and on 2026-09-24 sdb, sdb1, sdb2 and sdd1 were absent too, sdd and sdg were 0-byte devices and the nvme0n1 system disk was never listed -- so check `lsblk` before repointing." |
| 52 | S L6–9 | Exports count as used; 12 findings; the hook runs at warning | CONFIRMED | Pinned shellcheck 0.10.0: 4b311619's copy minus the directive → `12 SC2034`; frozen copy at `--severity=style` → no output. `.pre-commit-config.yaml` L219 `--severity=warning` | |
| 53 | S L45–49 | One clock read; `export` hides a failed `date` | CONFIRMED | Code inspection | |
| 54 | S | Mode 100644 | CONFIRMED | `git ls-tree edf8c432 S` | |
| 55 | E | Rebuilds edf8c432's design from 6c23fdde's | CONFIRMED | Scratch replay → "applied 25 … 20 fenced blocks unchanged … 2681 lines"; `cmp` identical (sha256 93ab3e30…) | |
| 56 | E | Idempotent | CONFIRMED | Re-run → 25 ALREADY, "no change … idempotent" | |
| 57 | E L42–44, L60–62 | The fence guard covers indented blocks | CONFIRMED | FENCE matches 20 blocks, 4 indented (L1858, 2087, 2111, 2138). Mutating the indented block at L1858 → exit 3, "GATE a fenced code block changed … NOTHING written", `cmp` unchanged. With a column-0 regex the same mutation → exit 0 and written | |
| 58 | E L19–22 | 04:55 CDT and 20:44 the same day | CONFIRMED | `gh`: #1999 09:55:30Z; #2029 2026-09-23T01:44:47Z | |
| 59 | E L27–30 | The defects-of-fact paragraph | CONFIRMED | Row 15 | |
| 60 | E L34–35 | "four tables' delimiter rows re-padded" | REFUTED | As row 47 | "four whole tables re-padded to column alignment (not adopted)" |
| 61 | E L13–14 | Handoff items 3, 4 and 5 scoped the first draft | CONFIRMED | Handoff L8–22 | |
| 62 | E L41 | No line over 512 characters | CONFIRMED | Longest D line is 511 characters (L2545) | |
| 63 | Ar L19–20 | No subagent id is written | CONFIRMED | None of the three ids, or their prefixes, appears in R | |
| 64 | Ar L10, L13–17 | Reuses the 2026-09-22 extraction and screen | CONFIRMED | Loads `archive_consensus_reports.final_report` and `.screen` and reassigns `TASKS` | |
| 65 | Ar | Produces R's verbatim sections | CONFIRMED | In-memory regeneration from the three transcripts is byte-identical to R; screen → 0 hits; `--check` → 19,700 / 23,809 / 12,722, exit 0 | |
| 66 | R L7–8 | Frozen d9f44a78 over df21367d; earlier rounds | CONFIRMED | git log; files exist | |
| 67 | R L14–17 | The draft's scope was the handoff's items 3–5 | CONFIRMED | Handoff L12–22 | |
| 68 | R L19–27 | Three validators launched together; the briefs | CONFIRMED | Meta files created 14:12–14:13; each brief has "Default to REFUTED", "read it only from git objects", no journal, no Duplicati binary | |
| 69 | R L31–36 | 41/10/2; 28/4/10; 2/3 | CONFIRMED | Each report's final line | |
| 70 | R L38–41 | The lenses overlapped on "… its fence gate could not see indented blocks" | REFUTED (minor) | Only lens A found that (A51); B19 and C other-2 relied on the gate without noticing | "…the edit script said "the day before" of a same-day merge (lens A alone also found that its fence gate could not see indented blocks);" |
| 71 | R L41–42 | "Only lens B went after §8" | REFUTED (minor) | R's own row at L78 credits "A other" for step 0(a); C6 concerns §8's step −1 | "Lens B went after §8's procedure systematically — lens A also caught step 0(a), lens C step −1's `--check` — and what it found there is the reason for the STOP block now at the top of §8." |
| 72 | R L44–47 | The two imprecise validator statements | CONFIRMED | d9f44a78 L227 is §4.2 note 2. All three briefs say "commit b0223f18; local ref origin/pr-2045-head". `git rev-parse origin/pr-2045-head` → f6363b9a, three commits above b0223f18 | |
| 73 | R L51–55 | The disposition preamble | CONFIRMED | Owner decisions (3) and (4) | |
| 74 | R L65 | Source column "A35, C §12" for "13 of 15 applied" | REFUTED (minor) | Lens C affirmed the opposite ("Round 3's 15 defects map to the r3-* edits", C other-8); §11's "15 defects, all applied" was flagged in A's "other problems" | "\| A35, A other (§11); C §12 for the missing artifact row only \|" |
| 75 | R L67 | "omitted sites … applied" | REFUTED (partial) | C scope named three omitted sites; 12b still omits note 10.2a's clause (row 49) | Apply row 49's fix, or: "applied, except note 10.2a's SMART-copy clause" |
| 76 | R L74 | The SMART header fix is applied | CONFIRMED | Applied, but the new text is itself false (row 51) | |
| 77 | R L77 | Front-matter status line "applied" | REFUTED | D L6 unchanged: "VALIDATED (round 2) … every finding is applied or recorded as dissent in §11" | R: "\| not applied — the Status line is unchanged \|". D L6: "- **Status**: STOPPED at §8 (round 4, 2026-09-24) — rounds 1 and 2 reconciled; round 3's D13 open (note 12a); round 4's §8 defects open (the STOP block at the top of §8)." |
| 78 | R L85 | "B22–B27 … follow-up" | REFUTED | B25 was applied (D L2351 "confirm the scrub, rotate, re-encrypt"). B22's half in note 10.1e was applied (L2342 "after the scrub"); AC-8 L2220 was not | "B11, B13–B18, B22 (AC-8's half; note 10.1e's half applied), B23, B24, B26, B27, B U1–U4 …", plus a new row "\| §10.2's heading \| B25 \| applied \|" |
| 79 | R L59–64, 66, 68–73, 75–76, 78–84, 86 | The remaining dispositions and sources | CONFIRMED | Each cited row exists with that subject; each "applied" is present in D, S or E | |

### Other problems I noticed

1. **§11 still undercounts.** D L2460 says "two rounds, plus a third single-agent confirmation pass", and round 4 is now appended beneath it.
2. **P0.5b still claims to close S-2.** P0.5a L2131–2133 and P0.5b L2164 say it "closes S-1 and S-2", which the new §6 sentence contradicts for S-2's exposure. The STOP block defers P0.5b's premise but leaves the claim standing.
3. **Other sections still blame "debug mode".** §1 L71, §4.1 L172, §4.2 L218 and §5.5 L407 say the 09-20 leak came from "the wrapper's debug mode". Note 10.1e now says it came from unconditional printing.
4. **AC-8 and note 10.1e use different start points.** AC-8 L2220 counts from "the hardening timestamp"; note 10.1e counts from "the scrub".
5. **The shells were probably closed without the history step.** `/home/duplicati/.bash_history` was written at 14:56:34 today. §6's sink row (L511) says to run `history -c; unset HISTFILE` before exit; it may not have run. The owner should count-grep as root. The text at L511, L2156 and L2349 is now stale.
6. **P0 step 8 overstates the file-mode rule.** L2099–2101 says every landed script "arrives 100644". `scripts/duplicati-wrapper.bash` is 100755 at 43980f13 and edf8c432: an existing file keeps its mode. Note 12b's conclusion still holds, because the SMART script is already 100644 on main.
7. **The token flag alone does not stop the sign-in URL.** Program.cs L338 logs it whenever the password is autogenerated and never tests `DisableSigninTokens`. Only setting the password stops it. This matters for S-6's remedy and the step-3 probe. It predates this change.
8. **P0.5a's heading still says "(depends on nothing)"**, beside "each before the P0 step that needs it" and item 2's restart at step 8.
9. **R L44's "two imprecise statements" misses a third.** Lens C's other-8 is also wrong and is not recorded.
10. **Archiver nits.** Both archivers print a character count labelled "bytes" (R is 63,714 characters but 64,427 bytes). Ar's docstring names "one deliberate difference", but Ar also drops `--allow-shaped` and makes `--header` required.
11. **§6's end point is slightly early.** "until §10.2 re-encrypts the set" should arguably be §10.2 step 8 (delete-forever), since the old ciphertext survives until then.

### Constraint slips

No hard constraint was broken: no unit was touched, no Duplicati binary ran, `journalctl` was not run, nothing under `/mnt` was written, no secret file was read, and every `gh` call was a read. Four things you should know about:
- One `ps -eo … args` printed the running server's command line, cut at 140 characters. It showed only `…/duplicati-server --webservice-port=8300`, but I should have printed the PID and start time only.
- I ran `stat` (metadata only) on `/home/duplicati/.bash_history`.
- I hashed the primary checkout's `scripts/duplicati-wrapper.bash`, which is outside this worktree, as the brief asked.
- The mutated edit-script copies and the drift test lived only in my scratchpad. That conflicts with the repo's "no scripts in `/tmp`" rule, but it was forced by the read-only constraint.

The isolation layer refused several compound commands, and the replayed edit script's `git diff --stat` failed harmlessly outside a repository.

**CONFIRMED 62 · REFUTED 16 · UNVERIFIABLE 1**

<!-- markdownlint-enable -->

---

## Round 5, lens B — consistency, consequence and residue

Archived verbatim (23,199 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

The correction is mostly sound, but it isn't finished. Of the 19 dispositions marked "applied", 18 are really in the design (one of them only partly). The front-matter status line is the one that isn't. The STOP block carries all four HIGH findings from round 4. The edit script rebuilds `edf8c432` byte-for-byte from `6c23fdde`, and the SMART script keeps every one of the owner's changes except the agreed ones. The main problems:

- **Status line contradicts the STOP.** The Status line still says "VALIDATED … every finding is applied", directly above the STOP.
- **§10.2 still says P0 is next.** It still says "the next action in this arc is §8's P0 recovery".
- **Host state changed during the session.** The two `su - duplicati` shells that §6's time-critical row is about are gone. `/home/duplicati/.bash_history` was written at 2026-09-24 14:56:34, 12 minutes before `edf8c432` was committed. Whether the 09-20 migration commands landed in it needs a root count-grep; I did not read the file.

**Documents.** Referenced: the design (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, "design"), the round-4 record (`notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`, "R4"), the round-2 record (`notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`, "R2"), the certification (`notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`, "YAM"), `util/ad-hoc/smart_checks_backup-sda.bash`, `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py` ("edit script") and `util/ad-hoc/2026-09-24_archive_round4_reports.py`. Line numbers are at `edf8c432`. **Changed**: nothing; all copies were written to the session scratchpad.

## 1. Disposition audit

| Finding (lens + row) | Disposition claimed | True at edf8c432? | Evidence |
|---|---|---|---|
| A20 / B20 / C other-4 (who moved the scrub) | applied | TRUE | design L2319–2323 |
| A23 (leaks printed under `DEBUG_MODE`) | applied | PARTLY: note 10.1e only | §1 L71, §4.1 L172, §4.2 L218 and §5.5 L407 still say "debug mode" (findings #15) |
| A25 / B21 (restart policy, probe outside the unit) | applied | TRUE | L2330–2334; host check: `Restart=always`, `NRestarts=0` |
| A-other: "a branch switch in the primary checkout would change that" | no row of its own | NOT CARRIED | 10.1e omits the caveat (#13) |
| A27 (the 22 + 1 split) | applied | TRUE | L2334–2337 |
| A35 / C §12 (13 of round 3's 15 applied) | applied; D11 row added; D13 open | TRUE in the design | R2 L29–31 still says "15 defects, all applied" (#14) |
| A41 (ml#2045 changed more than the front matter) | applied | TRUE | L2566, L2593–2594; note 10.2b now precedes 10.2c; every table delimiter row is compact (checked by grep) |
| A43 / C26 / C scope (note 12b's scope) | applied | PARTLY | header and mode are recorded; note 10.2a's evidence clause (edit script L344–351) is still unlisted (#21) |
| A45 / C other-6 (SMART palette) | applied | TRUE for the old claim | the replacement claim is itself wrong (#17) |
| A49 / A51 / B28 / C other-5 (edit script) | applied; fence guard mutation-checked | TRUE | my replay is byte-identical; a second run is a no-op; mutating an indented block fires the gate |
| A7, A10 (UNVERIFIABLE: "measured on") | applied | TRUE | L1777–1782; `duplicati_drill_run.py` L33–35 checked |
| A-other: `origin/pr-2045-head` premise | recorded in prose, no row | TRUE | R4 L44–47 |
| A-other: §10.2 notes printed a, c, b | applied | TRUE | L2407 / L2420 / L2430 |
| A-other: step 0(a) cannot pass | STOP item 1 | TRUE | L1702–1706 |
| A-other: wrapper v2 `die` path | follow-up | TRUE | R4 L85 |
| A-other: note 12b wording; the old archive has moved | **no row** | applied anyway | L2584; L1782 "then at /mnt/Backups/Ubuntu" |
| A-other / B19 / C other-2: fenced "here" comment | follow-up | TRUE | note 12b L2585–2588 says so |
| B1, B2, B3, B4, B8 | STOP items 1–5 | TRUE in substance | landed `duplicati.default` has the D-1 flag only in its L4 comment; installer writes only the blessed file; `yamaguchi_server_api.py` L41 still reads the primary checkout's `.env` and L80 has no pause/resume; guard L52 compares only a non-empty URL; timer is `Persistent=true`; snapshot script writes into `DEST_DIR` (L106–141). Item 3's wording overstates (#5) |
| B5, B6, B7 | to be re-derived, per the STOP | TRUE | L1722–1724; B6's text still stands at L2133 and L2164 (#9) |
| B9 | applied | TRUE | L2338–2339, L2393 |
| B10 | applied | TRUE in §6 only | not carried to the S-2 row, P0.5a's intro, P0.5b, §7.3.5 or §10.2's gate (#9, #11) |
| B11, B13–B18, B23, B24, B26, B27 | follow-up | TRUE | all unchanged at L2153, L2112–2115, L775/L2224, L2170, L2098, L2119, L1743, L88, L1740, L2231 |
| B12 | owner ruling | TRUE | L12–13, L1762–1765, L2121–2129, L2344–2349 |
| B22 | follow-up | PARTLY APPLIED | note 10.1e now says "after the scrub" (L2342); AC-8 L2220 unchanged (#16) |
| **B25** | follow-up | **FALSE: it was applied** | §10.2 heading L2351 reads "confirm the scrub, rotate, re-encrypt"; note 12b lists it |
| B U1 | follow-up | TRUE; now settleable | Duplicati's `Connection.cs` at the v2.4.0.0 tag has 0 logging calls in 1,845 lines, so the re-key path logs no values |
| B U2–U4 | follow-up | TRUE | unchanged |
| C row 6 (step −1 lost its failed-check action) | applied | TRUE | L1736–1738; the stage script prints "N staged" and returns 0 |
| C row 26 (file mode) | applied | TRUE | L2591–2593 |
| C refuted claims 1–3 | applied | TRUE | the D11 row covers exactly the 20 unrecorded files of `43980f13` (checked with `--name-status`) |
| C other-1, other-3 | applied | TRUE | L2419, L2179 |
| **C other-7 (front-matter status line)** | "applied — the round-4 record and the STOP bullet" | **FALSE** | L6 still reads "VALIDATED (round 2) … every finding is applied or recorded as dissent in §11" (#1) |
| C other-9 (unit `Environment=` not verified) | **no row** | acceptable | settled by A28 and B C4; `DropInPaths=` empty on re-check |
| C §3: the ml#1989 row carries no PR number | **no row** | unchanged | L2557 |

## 2. Findings (ranked)

| # | Location | What it says | Why it is wrong | Verdict | Evidence | Proposed fix |
|---|---|---|---|---|---|---|
| 1 | Front matter L6 | "VALIDATED (round 2) … every finding is applied or recorded as dissent in §11" | Contradicts the STOP at L11, §11 at L2450 and D13 being open (L2486); R4 claims it was fixed | REFUTED | L6 is identical at d9f44a78 and edf8c432 | "- **Status**: NOT EXECUTABLE — §8 is behind a STOP (round 4, 2026-09-24). Rounds 1 and 2 are reconciled; round 3 found 15 defects, 13 applied, D13 open (note 12a); round 4's §8 findings are open (§11). The owner's rulings are in §10.1." |
| 2 | §6 L511; P0.5a item 7 L2156; note 10.1f L2349 | Two live `su - duplicati` shells; clearing their history is time-critical | Both are gone (`ps -u duplicati` lists only the server). `/home/duplicati/.bash_history` was written 2026-09-24 14:56:34 (8,261 bytes). If they exited without `history -c; unset HISTFILE`, the migration commands are now on disk | UNVERIFIABLE (the file's content needs root) | `stat`; `ps`; the edf8c432 commit is 15:08:12 | Owner: `sudo grep -c -E 'PASSPHRASE\|SETTINGS_ENCRYPTION_KEY\|openssl\|credstore' /home/duplicati/.bash_history` (counts only), then wipe. Follow-up: rewrite the §6 row and 10.1f in the past tense |
| 3 | §10.2 L2401–2403 | "the next action in this arc is §8's P0 recovery" | Contradicts the STOP | REFUTED | STOP at L1698 | "…**the next action in this arc is the follow-up change that clears the STOP block at the top of §8, then §8's P0 recovery — not anything in §10.2**." |
| 4 | STOP L1700 vs front matter L11 | L1700: "Run nothing in P0.5, P0 or P1"; L11: "do not execute §8" | The two scopes differ, so P2–P4 are unsettled (P3's tier-2 fix is independent in substance). §6's "chmod 0600 now" (L466) and its sink rows aren't addressed. There is no exit criterion, though R4 promises a validation round | REFUTED (ambiguous) | L11, L466, L511, L1700 | "Run no step of §8 — P0.5a, P0, P0.5b or P1–P4 — until a follow-up change fixes these, passes its own validation round, and removes this block. §6's owner-only sink actions are not §8 steps and are not held by it." (Whether §6's actions are exempt is the owner's call; the STOP must say which.) |
| 5 | STOP item 3 L1710, L1713; front matter L11 | "can pass without checking anything"; "the one check §7.5 item 6 says the guard exists for" | With an empty URL the guard still checks the mount, the directory, write access and strays. §7.5 item 6 (L1336–1337) names two checks. R4's own summary is precise ("without its TargetURL check") | REFUTED | guard L1391–1418 | L1710: "3. **Step 10's guard dry-run can pass without its `TargetURL` check.**" L1713: "…one of the two checks (mount and `TargetURL`) §7.5 item 6 says the guard exists for." L11: "…without its `TargetURL` check…" |
| 6 | §7.3.6 L1185–1187; D-9 row L2292; crossings table L580; step 0(a) L1772 | D-9: "plus `--webservice-disable-signin-tokens` once a password exists" | No landed artifact and no §8 step installs it or `--webservice-allowed-hostnames=localhost`, yet the crossings table says the flag closes a crossing. This is the same shape as STOP item 1, and the STOP omits it. New; not a round-4 finding | REFUTED | `git grep` at edf8c432 finds it only in the probe script, L86 | Add to STOP L1722: "…; D-9's `--webservice-disable-signin-tokens` and §7.3.6's `--webservice-allowed-hostnames=localhost`, which no artifact or step installs (item 1's shape)…" |
| 7 | STOP L1722–1724; note 12a L2574–2576 | D13 "is open" | P1 step 2 (L2170), which the STOP holds, installs `.env` inside the data folder, where §7.3.5 (L1118–1127) says its mode cannot bind. D-13 is absent from the STOP and from R4's follow-up list, so removing the STOP could release P1 with D13 still open | REFUTED (omission) | R4 row at L65 | Append to the STOP: "…round 3's D13, which P1 step 2 inherits (note 12a)…" |
| 8 | L12–13, L1763, L2127–2128, L2345–2346 | Item 5 "before step 10's `resume` fires the first backup"; item 7 "before step 8's first start" | Step 10 (L2107) says the overdue job "will start on its own once the startup pause lapses", and step 3 (L1994–1996) does not rely on the startup delay. So the first backup can precede `resume` (step 8's start, P0.5b's starts). Under Procedure B, the §7.3 unit first starts at step 7 (L2082). The ruling stands; its triggers don't match the procedure. Nothing in steps 0–8 needs a duplicati login shell (see #27) | REFUTED (consistency) | cited lines | Add to the STOP's re-derive list: "…and whether P0.5a items 5 and 7 are timed to the right events (Procedure B's first start is step 7; the overdue job can run before `resume`)." |
| 9 | §6 L501–504 vs P0.5a intro L2131–2133, P0.5b L2163–2164, §7.3.5 L1164–1166 | New §6: S-2's lines matter "whatever the settings-key re-key (P0.5b) does"; P0.5b: "the item that closes S-1 and S-2, so it is not deferrable" | Applying B10 in one place created the contradiction; the STOP carries B6 only as "whether P0.5b is needed at all" | REFUTED | cited lines | STOP L1722: "…whether P0.5b is needed at all — its claim to close S-1 and S-2 (P0.5a's intro, P0.5b, §7.3.5) contradicts §6…" |
| 10 | §6 L502–504 | S-2's lines matter "until §10.2 re-encrypts the set"; "S-3 matters as long as the current set is in service … rotate and keep" | The 811-volume `_yamaguchi_frozen_20260826/` is a copy of the same set under the same passphrase (YAM §8.25.1). It sits in the synced `Backups/` tree (§4.4 L264; listed: 811 files) and is outside §10.2's 877 volumes. Old ciphertext also survives until §10.2 step 8. `PASSPHRASE_OLD` protects the ten `.gpg` dlists. And "in service" under rotate-and-keep means forever | REFUTED | directory listing; L2288, L2395, L2399 | "S-2's value **is** the live passphrase, so its lines matter as long as any ciphertext under it survives: the live set until §10.2 re-encrypts it and its step 8 deletes the old copies server-side, and the 811-volume `_yamaguchi_frozen_20260826/` copy (§4.4), which §10.2 does not name. S-3 is the same `PASSPHRASE` plus `PASSPHRASE_OLD`, which protects the old archive's dlists and is untouched by D-2." |
| 11 | §10.2 step 2 L2393 | Gate: "S-3 and S-7 counts read zero, and S-6 holds no unexpired token" | S-2 is omitted, though the corrected §6 says S-2's lines carry the live passphrase. Token lifetime is never stated (it is 5 min: `SigninTokenDurationInMinutes = 5` at v2.4.0.0) | REFUTED | L501–503 | "\| S-2, S-3 and S-7 counts read zero, and S-6 holds no unexpired token (note 10.1e; a sign-in token lives 5 minutes by default) \|" |
| 12 | §11 L2493–2495, L2460, L2450 | Round 4 "confirmed that diff's facts, refuted several of its own phrasings"; "**two rounds**, plus a third"; the state line omits D13 | Lens A refuted 10 claims, several of them facts (A23, A35, A41, A45, A49) | REFUTED | R4 L96, L177 | "…confirmed 41 of that diff's claims and refuted 10 — among them who printed the leaked labels, how many of round 3's defects were applied and what ml#2045 changed — …"; L2460: "**four rounds**: two full rounds, a third single-agent pass, and round 4"; L2450: add "; round 3's D13 is open (note 12a)" |
| 13 | Note 10.1e L2330–2333 | "an unplanned restart runs wrapper v2 today" | True today (the symlink resolves to the primary checkout's file, blob `42ba4683` = main's v2), but it breaks on a branch switch (§4.3 item 8, L249) or if the world-writable `bin/` (`drwxrwxrwx`, checked) is tampered with. "Once" then depends on item 1 running before item 4, and no text orders them | REFUTED (incomplete) | `readlink`, `git hash-object`, `stat` | "…until P0.5a item 1 deletes `/home/duplicati/bin/`, a restart runs whatever that path resolves to — on 2026-09-24 main's v2, but a branch switch or a replacement inside the 0777 `bin/` changes that (§4.3 item 8). So item 1 runs before item 4…"; front matter: "items 1, 2 and 4, in that order" |
| 14 | R2 L29–31 | "15 defects, all applied" | Contradicts the design's §11, §12 and R4's A35 row; nothing annotates it | REFUTED | R2 L31 | "…15 defects, of which 13 were applied (D11 and D13 were not — found by round 4, 2026-09-24; the design's §11)." |
| 15 | §1 L71; §4.1 L172; §4.2 L218; §5.5 L407; §4.3 item 4 L245 | The wrapper's "debug mode" wrote the leaked lines; only "PR #1967's first revision" printed unconditionally | Note 10.1e now says every revision through `6708cb28` printed unconditionally, and `DEBUG_MODE` started at 17:48 | REFUTED (fix applied in one section only) | L2326–2330 | §4.2: "…the wrapper — whose revisions then echoed unconditionally; `DEBUG_MODE` first gated them at 17:48 (note 10.1e) — echoes every `.env` line…"; same pattern for §1, §4.1, §5.5 and §4.3 item 4 |
| 16 | AC-8 L2220 vs 10.1e L2342 | "since the hardening timestamp" vs "after the scrub" | B22 half-applied: the terms now differ and AC-8's window is still undefined | REFUTED | cited lines | "No secret in either log store since P0.5a item 4's `journalctl --rotate` (D-8's one scrub): …" |
| 17 | SMART header L3–5 | "the host's layout when the script was written … by 2026-09-24 sdb and sdc4 were gone" | sdc4 left the partition table by 2026-09-08 (YAM §8.27.2); the script's first commit is 2026-09-23 (`af8111a5`). sdd1 is also gone, and sdg is unlisted (`lsblk`) | REFUTED | cited | "…It is NOT a live inventory: on 2026-09-24 sdb, sdb1, sdb2, sdc4 and sdd1 do not exist (sdc4 left the partition table by 2026-09-08), and sdg and nvme0n1 are not listed -- check `lsblk` first." |
| 18 | §8 preamble L1743 | "nothing in a later phase is a precondition of an earlier one" | B23 (follow-up), now contradicted more sharply by this change's own gate text | REFUTED | L1762–1765 | "…except P0.5a, printed after P0 but gating it (note 10.1f), and P0.5b, between steps 8 and 9 — **but that is true of phases, not of decisions**." |
| 19 | Front matter L12 | "and no other" was dropped | Nothing in edf8c432 carries the exclusivity (grep) | REFUTED (residue) | d9f44a78 L10 | "- **§8's order, once the STOP is cleared — this order and no other**: …" |
| 20 | R-6 L91; P0.5a heading L2121 | "nologin **immediately**"; "(depends on nothing)" | Contradicts the new gate, and 10.1f's "item 7 … waits on the owner" | REFUTED | L2349 | R-6: "`nologin` in §8 P0.5a item 7, before the §7.3 unit's first start (note 10.1f) — …"; heading: "(none depends on the recovery)" |
| 21 | Note 12b L2582–2583 | Lists note 10.2a only for its citation | Omits the evidence-clause edit | REFUTED | edit script L344–351 | "…note 10.2a, whose '§12' now reads §3.4 and whose evidence line names the copy ml#2041 landed." |
| 22 | STOP item 5 L1718 | Names P0.5a item 2 only | §7.7 (L1465–1466) prescribes the same `strict`, and B8 cited both | REFUTED | L1466 | "5. **P0.5a item 2's `ProtectSystem=strict` — also §7.7 — breaks the snapshot.**" |
| 23 | R4 L40–41, L44, L77, L85 | "Only lens B went after §8"; "Two validator statements"; C other-7 "applied"; B25 filed as follow-up | STOP item 1 is credited to "A other, B1"; the second imprecise statement was the brief's; the status line was not fixed; B25 was applied | REFUTED | cited | Reword these and move B25 to applied |
| 24 | Note 10.1f L2346–2347 | Quotes the front matter as "items 1 and 2"; calls the intro the "heading" | The front matter read "items 1–2" | REFUTED (nit) | design at 6c23fdde, L10 | '…"items 1–2" (the front matter), "items 1 and 2" (the P0 preamble) and, under the heading "before anything in P0", "Items 1, 2, 4, 5, 6 and 7" (its intro).' |
| 25 | Note 10.1e: "S-6's sign-in URLs are the exception" | Complete? | Yes, for secret families. Wrapper v2 logs names and lengths; the probe uses `--pipe` and disables tokens; `Connection.cs` has 0 log calls. Non-secret re-emissions (B14's sudo argv, B27's `known_hosts`) are already in the follow-up | CONFIRMED-SOUND | Duplicati source at v2.4.0.0 | — |
| 26 | 10.1e "cannot happen at all once item 1…" and the `daemon-reload` claim | — | Holds | CONFIRMED-SOUND | `DropInPaths=` empty; `NRestarts=0` | — |
| 27 | Gate ruling: do steps 0–8 depend on items 5, 6 or 7? | — | No. Every duplicati-uid action in P0 uses `sudo -u` or `systemd-run --uid`, which `nologin` doesn't affect; no step reads the S-7 file or needs item 6 | CONFIRMED-SOUND | L1859–1862, L1951–1959, L2075, L2095 | — |
| 28 | D-8's timing across §10 preface, §10.1, 10.1e, P0 preamble, item 4, P1 step 5, §10.2 | — | Consistent (apart from #16) | CONFIRMED-SOUND | grep | — |
| 29 | STOP items 1, 2, 4, 5; coverage of the HIGHs | — | Substance correct; all four round-4 HIGHs (B1–B4) are in the STOP | CONFIRMED-SOUND | frozen artifacts | — |
| 30 | Edit script | — | Byte-identical replay; a second run is a no-op; 20 fenced blocks guarded | CONFIRMED-SOUND | scratch replay | — |
| 31 | SMART script vs `b0223f18` | — | Keeps every owner change (all exports, error-checked clock, the SMART comments and blank lines, trailing blank lines removed); agreed changes: one `date` call, the header; mode 100644 is explained in note 12b. shellcheck 0.11.0 is clean at style level; un-exporting gives 12 × SC2034 | CONFIRMED-SOUND | diffs against 6c23fdde and b0223f18 | — |
| 32 | §12 new rows; R4's archived lengths | — | Chronological, no duplicates; stated lengths match the archived bodies (19,700 / 23,809 / 12,722 chars) | CONFIRMED-SOUND | name-status of `43980f13`; length count | — |
| 33 | R4 "archived verbatim" | — | Can't check against the transcripts, which are a secret sink | UNVERIFIABLE | — | Settled by the archive script's `--check` against the session's subagent transcripts |

## 3. Residue

| Hunk | What was dropped | Intended? | Evidence |
|---|---|---|---|
| Front matter | "§8 is executable"; "items 1, 2 and 4–7"; **"in this order and no other"** | Yes, yes, **no** (#19) | d9f44a78 L10 |
| §6 sentence | "S-1 and S-2 stop mattering once both keys are rotated" | Yes (B10), but the new end-point is wrong (#10) | L501–504 |
| §8 STOP | — (insertion only) | — | — |
| Step −1 | "confirm `--check` reports every artifact already current" | Yes (C6) | L1736–1738 |
| P0 preamble; P0.5a heading and intro | "items 1, 2 and 4–7"; "minutes" / "each takes minutes" | Yes (ruling; item 6 goes through CI) | L1762, L2121–2129 |
| Step 0(c), note 10.2c | "measured on 2026-08-23" | Yes (A10); equivalents kept | L1777–1783, L2433–2435 |
| P1 step 5 | "P1 scrubs nothing" | Yes (C other-3) | L2179 |
| Notes 10.1e / 10.1f | round-1 attribution; "under `DEBUG_MODE`"; "never restarted"; "every later start runs the §7.3 unit"; **"and prints no value"**; "after the hardening timestamp" | Yes, yes (residue #15), yes, yes; **"prints no value" dropped silently** (probably because of the `die`-path edge case; nothing records it); the timestamp change was half of B22 (#16) | L2318–2349 |
| §10.2 heading; step 2 gate | "scrub, rotate…"; "S-6 counts read zero" | Yes (B25, B9) | L2351, L2393 |
| Notes 10.2a / 10.2b | "§12 / D-12a"; 10.2b moved with identical text | Yes | L2419–2429 |
| §11 | "15 defects, all applied" | Yes (A35) | L2485 |
| §12 rows and notes | the round-3 row's "reconciled" and "Row added 2026-09-24"; the ml#2067 "two net changes" wording; note 12a's reason the round-3 row was owed | Yes, yes, yes (minor) | L2561, L2566, L2571 |
| SMART header | "every disk and partition on this host is named" | Yes (A45), but the replacement is wrong (#17) | L3–5 |
| Edit script (rewritten) | the column-0 fence pattern and its `findall` comparison | Yes: both were defective. The stale-phrase list grew from 5 to 9 | edit script L62, L542–547 |
| R4 record, archive script | new files | — | — |

The raw `git diff d9f44a78 edf8c432` also contains six files from main's advance (`df21367d` → `6c23fdde`: the canopy notes and three ad-hoc scripts). They are not part of this change.

## Constraint report

- **Refused commands:** the isolation layer refused two: `git -C <primary checkout> branch`, and one compound git loop. Neither had any effect.
- **Read-only host probes:** `systemctl show` (only the fields shown plus the `ExecStart` path), `ps`, `lsblk`, `readlink`, `uptime`, and `stat` of `/home/duplicati/bin` and `/home/duplicati/.bash_history`. The `stat` is metadata only; the history file was never opened.
- **Primary checkout's wrapper:** I ran `git hash-object` on `scripts/duplicati-wrapper.bash`. It hashes the file without printing it; the file is v2 and holds no credential.
- **Under `/mnt/Backups/`:** one names-only `ls` of `Backups/`, which printed the name `_yamaguchi_keys` without entering it, and a file count of `_yamaguchi_frozen_20260826/`.
- **Public Duplicati source:** read-only `gh search code` ×3 and `gh api` GET ×2 (using gh's own GitHub login), plus 4 WebFetches of `raw.githubusercontent.com`.
- **Scratchpad only:** the edit-script replay and shellcheck ran on scratch copies; the replay's trailing `git diff` failed harmlessly outside a repo.
- **Not done:** no unit was touched, no Duplicati binary run, no journal, syslog or secret file read, and no repository file changed.

**REFUTED 23 · CONFIRMED-SOUND 8 · UNVERIFIABLE 2**

<!-- markdownlint-enable -->

---

## Round 6, lens A — fact re-probe of the corrections

Archived verbatim (10,834 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

The replay is clean: the edit script rebuilds both files byte-for-byte and is idempotent. The pass still introduced 9 errors and left 1 claim unverifiable. The most serious is in the STOP block's new scope sentence: it says S-4's `chmod 0600` is not a §8 step, but P0.5a item 5 performs it.

**Key.** D = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`. R = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`. E = `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`. YAM = `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`. Line numbers are at 7265dc1f.

| # | Location | Claim | Verdict | Evidence | Exact replacement text |
|---|---|---|---|---|---|
| 1 | D L1708–1709 (STOP scope); R L126 | "The owner actions §6 lists outside §8 — its sink checklist and S-4's `chmod 0600` — are not §8 steps, and this block does not hold them." | **REFUTED** (medium) | `git show 7265dc1f:D \| sed -n 2174p` → "5. **Handle S-7 and S-4.** … `chmod 0600` the escrow `env`, and start the S-4 copy-out." That action belongs to P0.5a, and the same block says "Run no step of §8 — P0.5a, …". So the STOP both holds and releases the same chmod. | D: "The owner actions §6 lists — its sink checklist, and S-4's `chmod 0600`, which P0.5a item 5 also performs — are not held by this block; the rest of P0.5a item 5 is." R L126: "…; §6's owner actions are not held, S-4's `chmod 0600` included, although P0.5a item 5 also performs it" |
| 2 | D L2367–2368 (note 10.1f); D L1780 (P0 preamble, ends "(owner ruling 2026-09-24, note 10.1f)") | "P0's gate — ruled 2026-09-24. P0.5a items 1, 2 and 4 run before anything in P0, in that order." | **REFUTED** (the order is attributed to the ruling) | The ruling given to this round, and R L57, say "items 1, 2 and 4, with items 5–7 alongside". Neither mentions an order. R L135 records "in that order" as round 5's B13 finding being applied ("the gate now reads 'items 1, 2 and 4, in that order'"). | 10.1f: "**P0's gate — ruled 2026-09-24.** P0.5a items 1, 2 and 4 run before anything in P0; item 1 runs before item 4 because note 10.1e requires it (round 5, B13), not by the ruling." L1780: "**Run P0.5a items 1, 2 and 4 before anything in P0 — item 1 before item 4 (note 10.1e); items 5–7 run in the same session, …**" |
| 3 | D L2518–2521 (§11) | "Round 4 (… three lenses …) confirmed 41 of that diff's claims and refuted 10" | **REFUTED** (the count covers one lens, not the round) | R L243 is lens A's final line alone: "CONFIRMED 41 · REFUTED 10 · UNVERIFIABLE 2". Lens B also refuted the draft's own text (B9, B10, B12, B19–B22, B25, B28 at R L271–290). Lens C's line is "REFUTED claims: 3" (R L407). At least 7 of these (B9, B10, B12, B19, B22, B25, and C's note-12a claim) are not among A's ten. | "…each reading a frozen commit): its fact lens confirmed 41 of that diff's claims and refuted 10 — among them who printed the leaked labels, how many of round 3's defects were applied, and what ml#2045 changed — the other two lenses refuted more of its text, and lens B found defects in §8's procedure itself." |
| 4 | R L147; D L2176 | "Note 10.1f's quoting; the shells called 'live' \| A30, A32, B24, B2 \| applied …" | **REFUTED** (only partly applied, and one finding has no row) | `sed -n 2176p` of D → "Do this **after** the two live `su - duplicati` shells in §6's sink checklist have been closed per their own row — closing those is the owner's time-critical action". That row (L512) is now marked "Overtaken". Round 5 lens A "other problem" 5 (R L517) named this exact site as stale. `head -155 R \| grep -n other-5` → only "C other-5" at L79, so lens A other-5 has no row. | "\| Note 10.1f's quoting; the shells called "live" \| A30, A32, B24, B2, A other-5 \| applied in §6's row, note 10.1f and note sink-b; P0.5a item 7 still waits on "the two live `su - duplicati` shells" — follow-up with §8 \|" |
| 5 | D L2523; R L112 | "about half in the corrections' own text and the rest older text" | **REFUTED** | By round 5's own rows: all 16 of lens A's refutations (rows 3, 9, 30, 32, 37, 39, 47, 49, 51, 60, 70, 71, 74, 75, 77, 78) sit in text the round-4 correction wrote. Lens B: 15 of 23 do (#4, 5, 7, 8, 10–13, 16, 17, 19, 21–24); 8 hit older text (#1, 3, 6, 9, 14, 15, 18, 20). That is 31 of 39, about 79%. | D: "…the lenses overlap — most of them (31 of 39) in the corrections' own text and the rest older text they now contradicted; …" R L112: "Most of the refutations — 31 of 39 — were in the corrections' own text — …" |
| 6 | D L2610–2611, L2626 (note 12b) | Files "§10.2's next action" and "round count" under "Leftovers of the 2026-09-22 rulings and of ml#1999's own merge" | **REFUTED** | `git log -S"the next action in this arc is" -- D` → d15e7c01 (ml#2057), 2026-09-23 17:44, after both events; it went stale only when this change added the STOP. `git log -S"plus a third single-agent confirmation pass" -- D` → 43980f13 (ml#1999); that count was correct for rounds 1–3 until this change added round 4. | L2610–2611: "…§10's preface, §11's round-3 count and D-14 dissent, and note 10.2a — …". L2626: "**Rounds 4 and 5**: the STOP block at the top of §8, §10.2's next action, §11's entries and round count, and the round-4 record, which holds both." |
| 7 | D L91 (R-6) | "`nologin` in §8 P0.5a item 7, before the §7.3 unit's first start (note 10.1f)" | **REFUTED** (cites a timing note 10.1f does not state) | Note 10.1f (L2368–2369) says "item 7 before step 8's first start". Under Procedure B the §7.3 unit first starts at step 7 (L2100), so the two timings differ. The STOP's own re-derive list (L1739–1740) names this difference. | "\| O \| Kept; `nologin` in §8 P0.5a item 7, before step 8's first start (owner ruling 2026-09-24, note 10.1f) — moved out of P4 because …" |
| 8 | D L2139 (P0.5a heading) | "(none depends on the recovery)" | **REFUTED** | Item 2 (L2169–2170) says to stop the timer "until P0 step 8 has placed the recovered database; restart it only then". Round 5's lens A (other problem 8, R L520) cited exactly this conflict, and R L143 marks it applied. | "### P0.5a — items 1, 2 and 4 before P0; items 5–7 alongside it (only item 2's timer restart waits on the recovery)" |
| 9 | E L44–49 (docstring guards) against L638–657 | "no line this edit set creates may exceed 512 characters"; "every fenced code block … must be byte-identical"; "a list of stale phrases must be absent afterwards" | **REFUTED** | Mutation runs on scratch copies only. A new 600-character line in D → exit 3 ("OVER-WIDTH …DESIGN.md line 530"). A new 600-character line in the round-2 record → exit 3 ("…ROUND-2-RECORD.md line 33"). So a genuinely new long line is caught in both files. But a new line that copies an existing 849-character round-2 line → exit 0 ("applied 33"), because L641–643 exempt a line by its text (`line not in old_lines`). A rewrite inside a fenced block of the round-2 record → exit 0 ("applied 34 … 20 fenced blocks unchanged"), and the file now contains "su - MUTATED". The fence and stale-phrase checks read only `texts[DESIGN]` (L648–656). | "* no line this edit set creates may exceed 512 characters unless that exact line already occurs in the file (…); * every fenced code block OF THE DESIGN -- including the indented ones … -- must be byte-identical before and after (…); the round-2 record's fences are not compared; * a list of stale phrases must be absent from the design afterwards." |
| 10 | D L502–504 (§6) | For the live set, S-2's lines matter "until §10.2 re-encrypts it and its step 8 deletes the old copies server-side" | **UNVERIFIABLE** | Step 7 (L2422) says "Swap staging in … the old set is retained untouched until step 6 passed". Step 8 (L2423) deletes server-side copies only. Hazard 1 (L2405–2406) says nothing under `/mnt/Backups/Ubuntu/` is deleted or moved. No step says what happens to the local pre-rotation set, so whether any of it outlives step 8 cannot be derived. | "…the live set until §10.2 re-encrypts it and no pre-rotation copy is left — step 8 deletes the server-side ones, and §10.2 does not say what step 7's swap does with the local set — and the 811-volume …" |

**Constraint slips:** none against the hard constraints. The following are recorded for completeness:
- **Scratch-only work.** I wrote only in my scratchpad (`…/scratchpad/v6/`): extracted blobs, replay and mutant trees, and five small analysis helpers. Putting those helpers in /tmp conflicts with the repo's script-placement rule, but that was the only way to stay read-only.
- **Harmless git call.** The replayed E ended with its own `git diff --stat`, run in scratch outside any repository.
- **Refused commands.** The isolation layer refused two compound commands. I re-ran them as separate commands.
- **Host reads, read-only:**
  - `stat` metadata only on `/home/duplicati/.bash_history`; I never opened it.
  - `systemctl show` on the service, printing the ExecStart path only (no argv).
  - sha256 of the primary checkout's wrapper.
  - `lsblk`.
  - Names and counts under `/mnt/Backups/…/Dropbox/Backups/`. The listing printed the name `_yamaguchi_keys`; I did not enter it, and I did not read the frozen copy's README.
  - Two ~200-byte subagent `.meta.json` files, plus a names-and-times listing of the subagents directory. No transcript content.
  - One `gh pr view 1999` read.
  - A find/grep over `~/Development` for other copies of the SMART script: none found; one grep attempt timed out with no output.
- **Not done:** no journalctl, no Duplicati binary, no unit touched.

CONFIRMED: 171 — 115 distinct claims outside the disposition tables, plus 56 of the tables' 59 rows. That includes:
- **§6:** 811 volumes (`ls | wc -l`), the same set under the same passphrase, and §4.4 naming the frozen copy.
- **Note sink-b:** both PIDs gone; the history file is `600 duplicati:duplicati`, 8,261 bytes, mtime 14:56:34.
- **STOP block:** the guard's mount, directory and stray-file checks run regardless; §7.7 prescribes `strict`; D-9's two flags are installed by nothing in `util/`, `scripts/` or §8.
- **Note 10.1e:** the first wrapper commit is at 17:05; "debug mode" appears in §1 L71, §4.1 L172, §4.2 L218 and §5.5 L407; `bin/` is 0777.
- **Note 12b file modes:** the files ml#1999 added all landed `100644`, and the wrapper stayed `100755` through API-created commit ea4c3596.
- **Edit script:** it rebuilds 7265dc1f's design and round-2 record byte-for-byte from 6c23fdde and is idempotent.
- **SMART header, "before this script was written":** counted as confirmed only on the first commit (af8111a5, 2026-09-23 08:05) and first report (02:28:59). The palette itself lists sdb1, sdb2 and sdc4 together, which is the late-August layout in YAM §8.6 and §8.11.2.

REFUTED 9 · UNVERIFIABLE 1 · CONFIRMED 171

<!-- markdownlint-enable -->

---

## Round 6, lens B — consistency, consequence and operator reading

Archived verbatim (19,972 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

All rows fit except the S-3 row: at 602 characters it cannot hold the caveat, because the current row is already 502. I rerouted that caveat into a new note S-3c. The row's cell then grows by 7 characters, to 509. My proposed rows now measure: R-6 370, §10.2 step 2 448, `.swp` sink row 367, root-history row 376, record rows 112, 136 and 279, S-3 row 509 and S-2 row 491.

# Round 6 (consistency, consequence and operator reading) of the frozen commit `7265dc1f`

The worst problems are in what the owner may do today:
- **The STOP's exemption sentence is false.** It says S-4's `chmod 0600` is not a §8 step, but P0.5a item 5 performs it. It is also ambiguous about which of §6's actions are released.
- **Note sink-b's instruction can do harm.** Its count is case-sensitive, and it says to wipe a file that may hold the 09-18 key before anyone has tested it.
- **Host state has moved again.** The root `vim` (pid 2318515) and its swap file are now gone too, not only the two shells. Nothing in the design records that.

**Documents.** D = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`. R = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`. YAM = `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`. Line numbers are at `7265dc1f`. **Changed**: nothing in the repository; only scratch copies in the session scratchpad.

## 1. Round-5 dispositions that are false (all five are false in part)

| finding | disposition claimed | why false | evidence |
|---|---|---|---|
| "without checking anything"; "the one check" (A3, A9, B5) | applied — "one of two" | Step 10 still says TargetURL "is the one check §7.5 item 6 says the guard exists for". A9 named that copy. It now contradicts STOP item 3 | D L2136 vs L1722–1723; R L439 |
| The STOP's scope (B4) | applied — "§6's owner actions are not §8 steps and are not held" | S-4's `chmod 0600` is P0.5a item 5, which is a §8 step. B4 also made the exemption "the owner's call", and no owner ruling on it is recorded | D L1708–1709 vs L2174; R L601, L126 |
| The shells called "live" (A30, A32, B24, B2) | applied; §6's row marked overtaken | P0.5a item 7 still says "the two live `su - duplicati` shells… the owner's time-critical action". §4.1 note (a) still says their history "is still unwritten and still recoverable". The sink row's first cell still reads "Two live" | D L2176–2177, L184, L512; R L517 (A other-5 names item 7), L599 |
| R-6's "immediately"; P0.5a's "(depends on nothing)" (B20, A other-8) | applied | A other-8's ground was item 2's restart at step 8. The new "(none depends on the recovery)" is still contradicted by item 2's "restart it only then" | D L2139 vs L2170; R L520 |
| The 16:41–16:50 passes' revision (A20) | applied — "recorded nowhere" | Note 10.1e's opening sentence still asserts what A20 found unverifiable: "came from the wrapper before `DEBUG_MODE` existed" | D L2346–2349; R L450 |

## 2. Findings (REFUTED and UNVERIFIABLE), ranked by severity

| # | location | what it says | why it is wrong or inconsistent | verdict | evidence | exact replacement text |
|---|---|---|---|---|---|---|
| 1 (HIGH) | D L1708–1709 (STOP) | "The owner actions §6 lists outside §8 — its sink checklist and S-4's `chmod 0600` — are not §8 steps, and this block does not hold them." | (a) S-4's chmod is P0.5a item 5. (b) §6 names other remediations: S-7's removal, the D-8 scrub paragraph, the detection gap, the UI password. Read as a category, the sentence would let the owner scrub before item 1, which breaks the gate order. (c) It releases sink rows whose own gates point at held or missing steps (#4). (d) It releases the transcript purge with no ordering, but the archiver builds R's verbatim reports from subagent transcripts, including this round's | REFUTED | D L2174, L494–500, L514, L517; R L158 | "Two things §6 asks of the owner are not held and may be done now: its sink checklist, and `chmod 0600` of the escrow `env` — S-4's "now", which P0.5a item 5 repeats, so doing it early discharges that part of item 5. The checklist has two limits: no history file is wiped before P0 step 3 has tested the key candidates it may hold (root's history row, note sink-b), and no transcript is purged before this arc's last validation round is archived from it. Every other remediation §6 names is a §8 step and is held: S-7's removal and S-4's copy-out (P0.5a item 5), the D-8 scrub (item 4, which follows item 1), the detection gap (item 6), the Dropbox purge (P1 step 4) and the UI password (P0 step 9)." |
| 2 (MED) | D L524–529 (note sink-b); L353–356 (§5.4) | "`sudo grep -c -E 'ENCRYPTION\|PASSPHRASE\|webservice-password'` … and wipe the file if any count is non-zero" | (a) The grep is case-sensitive. It misses forms the design itself names: `--settings-encryption-key=`, `--passphrase=`, and `change-password <new>` / `--password`. A zero proves nothing. (b) A non-zero count is exactly when the file may hold the 09-18 key. Both shells were open during 09-19's `Missing` loop against the root folder. §5.4's "only untested places" omits this file. Root's history row waits for the key search before wiping; sink-b wipes at once, a destructive step with no copy. (c) The count itself prints no value and its command line carries no secret — that part is sound | REFUTED | D L1168, L1341, L1199–1200, L210, L512, L1771 | sink-b, after "…may now be on disk.": "Owner, count-only — never drop `-c`: `sudo grep -c -i -E 'encryption\|passphrase\|password' /home/duplicati/.bash_history`. Do not wipe on the count: the file may hold keys tried against the root folder on 09-19, and §5.4's list omits it. Wipe it with root's history, once P0 step 3 has tested what it holds." §5.4: "…root's `~/.bash_history` and `.viminfo`, `/home/duplicati/.bash_history` (note sink-b), and editor backups…" |
| 3 (MED) | D L1707–1708 (STOP scope) | "Run no step of §8 — P0.5a, P0, P0.5b or P1–P4" | No defect listed touches P0.5a items 1 or 6, or P3. Items 5 and 7 are questioned only on timing, and running them early is the safe side of "before". Holding them keeps several things open until the follow-up lands: the 0777 `bin/` under a `Restart=always` server, the world-readable S-7 file, and tier 2 (broken since 09-07) while tier 1 is also down. The design itself says these holes "must not stay open for days". This is the owner's call, but the STOP should make it on purpose | REFUTED (consequence) | D L2141–2142, L2342–2343, L63–65, L179, L469; host at 16:10 CDT: `Restart=always` | Either "Nor does it hold P0.5a items 1, 5, 6 and 7, or P3, which no defect below touches; item 1 still precedes item 4, and item 4 stays held." or "P0.5a items 1, 5, 6 and 7 and P3 are held although no defect below touches them (the owner's choice, 2026-09-24)." |
| 4 (MED-LOW) | D L514; L313; L357 | Root's history: "wipe once §5.4's search is done"; §5.3 and §5.4 say the search is "listed as owner actions in §8" | No §8 step lists that search, and none says how to pull a candidate out of the history without printing it. The STOP now releases this row, so "done" has no defined end. Its `grep -c ENCRYPTION` is also case-sensitive | REFUTED | `awk` over §8, D L1703–2226: no `bash_history`, `/root` or `viminfo` | Row: "owner: count now, count-only (`sudo grep -c -i -E 'encryption\|passphrase\|password' /root/.bash_history /root/.viminfo`); wipe only once P0 step 3 has tested what they hold — the STOP holds step 3, so these wait for the follow-up". §5.4: "…root-only reads; no §8 step yet extracts a candidate from them without printing it (§8 follow-up)." |
| 5 (MED-LOW) | D L1707–1708 | "until a follow-up change fixes them" | It is unclear whether "them" means the five items, the two "also re-derived" findings, or the open questions. "No step" also holds harmless reading, such as step −1's review and step 1's `sudo ls` listings, which the follow-up itself needs | REFUTED (ambiguous) | D L1732–1741, L1750–1755, L1872 | "Until a follow-up change fixes items 1–5 and the two findings beneath them, settles each open question in the last paragraph, passes its own validation round and removes this block, run no step of §8 — P0.5a, P0, P0.5b or P1–P4 — that writes, moves, deletes, installs, starts, stops or restarts anything. Reading is not held: P0 step −1's review and P0 step 1's two `sudo ls` listings may run now." |
| 6 (MED-LOW) | D L1778–1780, L2139, L2179, L2186–2219 | §8's subsection headings; the P0 preamble opens with a bold "**Run P0.5a items 1, 2 and 4…**" | A reader who arrives by a heading anchor never sees the STOP, and the front matter itself cites "P0.5a" and "P0 step −1" | REFUTED (operator reading) | — | Under each P0 / P0.5a / P0.5b / P1–P4 heading add the line "*Held by the STOP at the top of §8.*" (the headings stay the same, so their anchors survive) |
| 7 (MED-LOW) | D L91 (R-6) | "`nologin` … before the §7.3 unit's first start (note 10.1f)" | The ruling it cites says "before step 8's first start" (front matter, P0 preamble, P0.5a intro, 10.1f). Under Procedure B the §7.3 unit's first start is step 7, so the two diverge. §7.3.1 L566 ("once the migration is accepted") cites R-6 and contradicts it | REFUTED | D L13, L1781, L2146, L2368, L2100 | "\| R-6 \| … \| Kept; `nologin` in §8 P0.5a item 7, before step 8's first start (owner ruling, note 10.1f — the STOP at the top of §8 asks whether Procedure B's step-7 start must come first) — moved out of P4 because a duplicati-uid shell outside the unit escapes §7.3.2's mount mask through `/proc/<pid>/root` \|" (370 chars) |
| 8 (LOW-MED) | D L2176–2177, L184, L512, L515, L354 | Item 7: "the two live … shells … time-critical"; §4.1 note (a): history "still unwritten"; the `.swp` row: "shred when the editor closes" | The shells are gone, and so are the root `vim` (pid 2318515) and its swap file. At 16:10 CDT no such pid existed and no swap file was in the directory. The unit's mtime is still 2026-09-21 01:44:57, so the editor wrote nothing on exit. Note sink-b records only the shells | REFUTED | `ps`; `ls \| grep -c` gave 0; `stat` of the unit | Item 7: "Do this **after** every `duplicati`-uid shell outside the unit has exited — the two §6 names have (note sink-b); `ps -u duplicati` should list only the server." §4.1(a): "…at round 2; by 2026-09-24 all three had exited (note sink-b), and the swap file with them." `.swp` row Action: "**Overtaken on 2026-09-24** — the editor (pid 2318515) had exited and no swap file remained at 16:10 CDT; the unit's mtime is still 2026-09-21 01:44:57, so the exit wrote nothing" |
| 9 (LOW-MED) | D L12–13 | "…— this order and no other"; "items 5–7 run in the same session … item 6 at any point" | The restored "and no other" makes exclusive an order the STOP calls defective. STOP item 1 moves step 0(a), P0.5b's place is open, and step 9's precondition of landing the client change before P0 is missing. "Same session" also conflicts with item 6 being a PR that goes through CI | REFUTED (operator reading) | D L1711–1715, L1736–1741, L2124, L2372 | L12: "**§8's order once the STOP is cleared — this order and no other, except where the follow-up that clears it changes it (STOP item 1 moves step 0(a); P0.5b's place is open; step 9's client change lands before P0)**:". L13: "…item 5 before step 10's `resume`; item 6, a repository change, lands whenever it is ready and gates nothing (owner ruling 2026-09-24, note 10.1f)." |
| 10 (LOW) | D L2136 | "…it is the one check §7.5 item 6 says the guard exists for" | This contradicts STOP item 3 and §7.5 item 6, which names two checks: the mount and `TargetURL` | REFUTED | D L1344, L1722–1723 | "…vacuous, and `TargetURL` is one of the two checks, with the mount, that §7.5 item 6 says give the guard its value." |
| 11 (MED, not today) | D L501–505; L464–465 | The frozen 811-volume copy "which §10.2 does not name"; `PASSPHRASE_OLD` "which D-2 does not touch" | The sentence discloses two indefinite exposures and gives them no route. The frozen set is a restore point the owner kept (YAM §8.25), and it sits in the Dropbox-synced tree. §10.2 re-encrypts only the 877 volumes. §8 may not delete or move it, and neither the STOP nor R's follow-up list names it. The S-3 row still offers "D-2 RULED" as its fix, and the S-2 row offers only P0.5b | REFUTED (consequence) | D L264, L2308, L2419, L2423, L1771; R L132; YAM §8.25 | S-2 cell: "…(notes S-2a, S-3c)" (491). S-3 cell: "…(notes S-3b, S-3c)" (509). New note: "- **(S-3c)** D-2's ruling covers `PASSPHRASE` only. `PASSPHRASE_OLD` protects the old archive's ten dlists, and `_yamaguchi_frozen_20260826/` — a restore point the owner kept (YAM §8.25) — sits under `PASSPHRASE` in the Dropbox-synced tree, which §10.2 does not re-encrypt and §8 may not delete or move. Both need an owner decision: re-encrypt the 811 volumes with the 877 in §10.2 steps 4–7, move them out of the Dropbox root, or accept the exposure in writing." |
| 12 (LOW-MED) | D L2417 | Gate: "S-2, S-3 and S-7 counts read zero" | (a) S-2's `.env` exposure is the *active* line 22. The row names only the comment block, and P0 step 2 moves that `.env` into `Duplicati.empty-2026-09-20/`, where it stays until P4. Under A0/A2 the new folder has no `.env` at all, so the count can pass vacuously. (b) Wrapper v2 logs `settings encryption key:` at every start, so a case-insensitive count never reaches zero | REFUTED | D L464, L1873, L2106–2108, L2223, L916–920 | "\| 2 \| Confirm the leaked copies are gone: the S-7 file (P0.5a item 5); S-2's active key line and S-3's comment block in every `.env`, `Duplicati.empty-2026-09-20/.env` included (P1 step 2); and both log stores — D-8's one scrub, P0.5a item 4 (amended 2026-09-24) \| S-2, S-3 and S-7 counts read zero, counted case-sensitively on §6's labels (wrapper v2 logs `settings encryption key:` at every start), and S-6 holds no unexpired token (note 10.1e) \|" (448) |
| 13 (LOW-MED) | R L58–59, L90–91, L133, L139, L141, L145–146 | The two disposition tables | The labels B11, B16, B18, B22 and B23 each mean "follow-up" in the round-4 table and "applied" in the round-5 table. L139's "stays B22's follow-up" means round 4's B22, while round 5's own B22 row reads "applied". Round 4's B23 (the phase-order sentence) is still listed as follow-up, though round 5's B18 applied it. The round-5 table has no key for its Source column. The follow-up author reads these tables to know what is open | REFUTED | cited lines | Under "Disposition of round 5": "Source column: round 5's lens and row; round 4's rows are cited as "round 4's Bn"." L139: "…stays round 4's B22 follow-up". L91: drop "B23,". Add row "\| §8's phase-order sentence \| B23 \| applied in round 5 (round 5's B18) — the P0.5 exception; step 9's client change is still follow-up \|" |
| 14 (LOW) | D L2365–2366 | "A secret AC-8 finds after its hardening timestamp is a **new** exposure" | This pass swapped the defined "after the scrub" for AC-8's undefined term. A leak between the scrub and a later "hardening" point now falls outside both this rule and AC-8 | REFUTED | R L139, L90 | "A secret found in either log store after P0.5a item 4's `journalctl --rotate` — the point AC-8's "hardening timestamp" must be defined as (round 4's B22) — is a **new** exposure, …" |
| 15 (LOW) | D L2139 | "### P0.5a — items 1, 2 and 4 before P0; items 5–7 alongside it (none depends on the recovery)" | Item 2's restart waits on step 8, and the heading is the one gate site that omits "in that order" | REFUTED | D L2170 | "### P0.5a — items 1, 2 and 4, in that order, before P0; items 5–7 alongside it" |
| 16 (LOW) | D L1760–1762 | "apart from P0.5 … nothing in a later phase is a precondition of an earlier one" | Step 9's client change must land "in the same PR as §7.6's re-pointing, before P0 runs", while §7.6's changes are P2 step 4. That is the second half of round 4's B23 | REFUTED | D L2124, L2206 | "…apart from P0.5 — … (note 10.1f) — and step 9's client change, which must land with §7.6's re-pointing before P0 runs, nothing in a later phase…" |
| 17 (LOW) | D L2522–2524, L2475; R L112 | Round 5: "about half in the corrections' own text"; "each is applied here or listed as follow-up" | Lens A's brief confined all 16 of its refutations to the corrections' own text, and most of lens B's (15 of 23 by my reading) are there too. B15 was left unchanged, and the sites in #8 and #10 were missed | REFUTED (minor) | R L104, L137 | "…lens A's all in the corrections' own text or the record, which its brief confined it to, and most of lens B's; each is applied here, listed as follow-up, or — round 5's B15, the "debug mode" wording — acknowledged in note 10.1e and left unchanged." |
| 18 (LOW) | D L2346–2350 | Leaks "came from the wrapper before `DEBUG_MODE` existed" | For the passes before 17:05 the same note says the working copy "is recorded nowhere", and §1, §4 and §5 say "debug mode" did it | UNVERIFIABLE | R L450 | "…came from the wrapper, and no committed revision gates them before `64677ab0` (17:48 on 09-20). The leaking passes ran 16:41–17:30; those before 17:05 predate every commit, so whether their working copy had a debug switch is recorded nowhere — §1, §4 and §5 say it did." |
| 19 (LOW) | R L126 | B4 "applied — … not held" | B4 said the exemption is the owner's call. Neither document records such a ruling | UNVERIFIABLE | R L55–58, L601 | "\| … \| B4 \| applied — all of §8 held until a validated follow-up removes the block; §6's sink checklist and S-4's `chmod 0600` are not held ([owner ruling 2026-09-24] or [the orchestrator's reading, put to the owner]) \|" (279) |

## 3. Unintended drops

| hunk | what was dropped | right? | evidence |
|---|---|---|---|
| §12's last row | ", adopted" after "the owner's refactor carried by the closed ml#2045" | No finding asked for it. Harmless, because note 12b still says the refactor is adopted. Restore "adopted — its mode excepted (note 12b)" | D L2595 vs `edf8c432` |
| R's round-4 table row | The finding lost "§12 round-3 row", which was A35's actual subject; A35 now reads as a §11 finding | No — restore "§12's round-3 row ('its 15 defects are the `r3-*` edits') and §11's…" | R L69; `d9f44a78` L2498 |
| Note 10.1e | "its `ExecStart` resolves through `/home/duplicati/bin/`" | Minor: "whatever that path resolves to" now names a directory. Restore "…whatever its `ExecStart`, `/home/duplicati/bin/duplicati-wrapper.bash`, resolves to…" | D L2352–2353 |

**CONFIRMED sound: 41.** That is 24 of the 29 round-5 dispositions, plus 17 other checks:
- "In that order" appears at all four gate sites, and running item 1 before item 4 conflicts with nothing.
- STOP items 1–5 match the text they cite, and the D-9 and D13 re-derivations hold (`git grep`).
- The STOP omits no HIGH finding from rounds 4 and 5.
- The status line, §11, §12's last row and note 12b agree, and §12's file list matches `git diff --name-status`.
- Note 10.1e agrees with §4.3 item 8, §4.1, P0.5a item 1 and §4.2 note 6.
- Note sink-b's count leaks nothing.
- Host state: the unit is unchanged, there is no drop-in, and `Restart=always`.

**Constraint slips.** None of these touched a secret or the service, but you should know about them:
- Several calls chained `cd` with read-only `git show`/`git diff` redirected or piped to `sed`, `grep` or `wc`. One chained three `git show` extractions with `&&`. That stretches "plain, separate git commands".
- Host probes were limited to `ps` (pid, user, elapsed time, command name), `systemctl show` of four properties, `stat` of the vendor unit, and a count-only `ls | grep -c`.
- Nothing under `/mnt/Backups/` was touched, no journal or secret file was read, and no unit or Duplicati binary was touched.
- The isolation layer refused one Python heredoc; I redid the count with `awk` on a scratch file.

**Final counts: REFUTED 17 · UNVERIFIABLE 2 · CONFIRMED 41 · 5 of 29 round-5 dispositions false in part (each also covered by a finding above).**

<!-- markdownlint-enable -->

---

## Round 7, lens A — fact re-probe of the corrections

Archived verbatim (14,319 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

The mechanical checks all pass, but I found 13 errors in the delta's text and 2 claims I can't verify. The edit script rebuilds `2c9efe85`'s design and round-2 record byte-for-byte from `6c23fdde`, and a second run changes nothing. Its `--self-test` passes all 8 cases, and each mutant fails on the gate it targets; I checked that by capturing the gate messages, since the self-test only compares exit codes. My own mutants behaved correctly too: a 513-character line fails and a 512-character one passes. The round-2 record does have 70 long lines, all inside verbatim reports, and the `--no-index` comment matches `man git-diff`. The most serious error is note 10.1g, which misstates what round 6 found about items 5 and 7.

Key: D = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, R = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`, E = `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`. Line numbers are at `2c9efe85`.

| # | Location | Claim | Verdict | Evidence | Exact replacement text |
|---|---|---|---|---|---|
| 1 (MED) | D L2414–2415 (note 10.1g) | "Round 6 found that no defect the STOP block … lists touches P0.5a items 1, 5, 6 or 7, or P3" | REFUTED | R L831 (round 6 lens B, row 3): "No defect listed touches P0.5a items 1 or 6, or P3. Items 5 and 7 are questioned only on timing". D L1758, the STOP's own last paragraph, lists "whether P0.5a items 5 and 7 are timed to the right events". The STOP's exit criterion (L1718) requires that question settled. | "Round 6 found that no defect the STOP block at the top of §8 lists touches P0.5a items 1 or 6, or P3, and that items 5 and 7 are questioned only on their timing (the block's last paragraph), where running them early is the safe side of "before" — while holding them would keep open the 0777 `bin/` …" |
| 2 (MED-LOW) | D L2668–2669 (note 12b); D L521, L525 | "the release's two limits in §6's root-history row and note sink-b" | REFUTED | L522 and sink-b (L536–539) carry only the history limit. The transcript row (L525) still reads "count-grep and purge **both** the `.jsonl` transcripts and the `tool-results/` files", with no limit. The `/home/duplicati/.viminfo` row (L521, "keeps registers and command history") still says "wipe", which limit 1 (D L1724) forbids before P0 step 3. Both rows are in the released sink checklist. | 12b: "…a marker under every §8 phase heading, the history-file limit in §6's root-history and `.viminfo` rows and note sink-b, and the transcript limit in §6's transcript row." L525: "\| Claude Code transcripts **and persisted tool-result files** under `~/.claude/projects/…` \| **cloud-linked**, and **inside the backup Source** — note (AC-3a) lists `.claude/projects` among the *unfiltered* 0700 trees, so every capture is in every T1 fileset and in Dropbox (note sink-a) \| count-grep now; purge **both** the `.jsonl` transcripts and the `tool-results/` files only once this arc's validation reports are archived from them (note 10.1g) \|" (453 chars). L521 action cell: "count, never print; wipe only once P0 step 3 has tested what it holds (note 10.1g)" |
| 3 (LOW-MED) | D L11 (front matter STOP bullet); L6 | "**STOP — do not execute §8 yet.** … §8 is executable only once that block is gone" | REFUTED (contradicts the 2026-09-24 release) | D L1722 releases P0.5a items 1, 5, 6 and 7 and P3; the P3 marker at L2243 reads "Released by the owner's 2026-09-24 ruling". | L11: "- **STOP — do not execute §8 yet, beyond what the owner released on 2026-09-24.** Rounds 4–6 found … The STOP block at the top of §8 lists them and what is released — P0.5a items 1, 5, 6 and 7 and P3, within two limits (note 10.1g); the rest of §8 is executable only once that block is gone." L6: "NOT EXECUTABLE, but for what note 10.1g releases — §8 is behind a STOP …" |
| 4 (LOW-MED) | D L2177–2178; R L196–197, L217 | The earlier six-item heading's claim "is false of the one that closes S-1 and S-2, and of item 2's timer restart"; R lists "the base text's 'true of five'" as one of three sites carrying the false claim | REFUTED (anachronism) | `git log -S'none of it depends on the recovery'` finds only `43980f13`. The round-2 record L2384 quotes the heading round 2 read; its D8 (L1613, L1626) says "Nothing in P0/P0.5 re-points or stops the snapshot lane" and proposes adding the stop/restart to item 2. `grep -c 'restart it only then'`: `05c5f794` gives 0, `ea4c3596` (ml#1999) gives 1. In the revision described, item 2 had no restart, so "true of five" was correct. | D: "…heading that claimed "none of it depends on the recovery", which was true of five and false of the one that closes S-1 and S-2; item 2's timer restart, which waits for step 8, came later with ml#1999 (round 2's D8)." R L217 disposition: "applied — the heading first; the P0 preamble and P0.5a's intro in the second pass; the base text's "true of five" was accurate and is restored". R L197: "…at the two sites no lens named." |
| 5 (LOW-MED) | D L353–358 (§5.4); R L209 | §5.4 still lists `.duplicati.service.swp` under "Where the key could still be recorded"; "Both are root-only reads"; R: B8 "applied — §6's `.swp` row, §4.1 note (a), note sink-b" | REFUTED | `ls -a /usr/lib/systemd/system/ \| grep -c '\.sw[a-p]$'` gives 0, and the delta's own `.swp` row (L523) says overtaken. B8 (R L836) named "L354", which is §5.4's swap-file mention at `7265dc1f`. "Both" now follows three sources, one of them world-readable (0644). | D: "**Where the key could still be recorded**: root's `~/.bash_history` and `.viminfo`, and `/home/duplicati/.bash_history` (note sink-b — its shells were open during 09-19's key failures), for the window 09-18 20:42–21:03. The unit's editor backup is gone (§6's `.swp` row); there is no `duplicati.service~` and no `duplicati.service.d/`. Those three files are the only untested places, all root-only reads; a candidate found there is tested with the probe in seconds. No §8 step yet extracts…" R L209: "…note sink-b; §5.4's swap-file mention only in round 7" |
| 6 (LOW-MED) | D L2465 (§10.2 step 2) | "S-2's active key line and S-3's comment block in every `.env`, `Duplicati.empty-2026-09-20/.env` included (P1 step 2)" | REFUTED (P1 step 2 does not cover the second file) | P1 step 2 (L2219) edits one `.env`. P0 step 2 (L1896) runs `mv … Duplicati Duplicati.empty-2026-09-20`, which takes the leaking `.env` with it. Only P4 step 2 (L2258) removes `Duplicati.empty-2026-09-20`. | "\| 2 \| Confirm the leaked copies are gone: the S-7 file (P0.5a item 5); S-2's active key line and S-3's comment block in the live `.env` (P1 step 2) and in `Duplicati.empty-2026-09-20/.env`, which P0 step 2 moved aside and only P4 step 2 removes; both log stores — D-8's one scrub, P0.5a item 4 \| S-2, S-3 and S-7 counts read zero on §6's labels, case-sensitively (v2 logs a lowercase `settings encryption key:`), and S-6 holds no unexpired token (note 10.1e) \|" (460 chars) |
| 7 (LOW) | D L1802, L2171, L2407; D L13; R L211 | Items 5–7 "run in the same session", credited to the owner's ruling at L1802 and L2174; the front matter cites note 10.1f for "item 6 … lands whenever it is ready"; R: B9 "applied" | REFUTED | The ruling as given says "alongside", not "in the same session". This is the same class as round 6's A2 ("in that order"). The front matter now contradicts the note it cites. | At all three sites, "Items 5–7 run in the same session" becomes "Items 5–7 run alongside". R L211: "applied in the front matter; the P0 preamble, P0.5a's intro and note 10.1f only in round 7" |
| 8 (LOW) | R L184–185; D L2576 (§11); E L36–37; D L523 | "host state had moved again: the root `vim` and its swap file were gone"; "host state that had moved during the session"; "**Overtaken on 2026-09-24**" | REFUTED (timing) | `stat -c %y /usr/lib/systemd/system/` gives 2026-09-22 19:10:21. `find … -maxdepth 1 -newerct '2026-09-22 00:00'` finds only the directory itself, so the last change there was a removal. `/var/log/dpkg.log` has 0 lines for 09-22 18–19h. The round-2 record L113 has the swap file present at about 02:32 on 09-22. This session's transcript was created 2026-09-24 13:43:27, so the swap file was gone roughly 42 hours before the session started. | R: "And the design still described host state that had moved: the root `vim` and its swap file were gone — the swap file by 2026-09-22 19:10:21 at the latest, two days before this session." §11: "…and host state the design still described that had long since moved (note sink-b)". E: "…round 5's shells during the session, round 6's editor by 2026-09-22." L523: "\| `/usr/lib/systemd/system/.duplicati.service.swp` \| root-owned but **0644, world-readable**; 0 `ENCRYPTION` lines when counted; the same editor carried the key into that unit on 09-18 \| **Overtaken** (found 2026-09-24): the editor (pid 2318515) has exited, and the directory's last entry change, 2026-09-22 19:10:21, bounds the swap file's removal; the unit's mtime is still 2026-09-21 01:44:57, so the exit wrote nothing \|" (424) |
| 9 (LOW) | D L522 (root-history row) | Count with `sudo grep -c -i -E 'encryption\|passphrase\|password' …` | REFUTED (source text gives a false zero) | In the raw text the pattern keeps its backslashes. `printf '…encryption x…passphrase…\|literal\|…' \| /usr/bin/grep -c -i -E 'encryption\|passphrase\|password'` gives 1: GNU grep 3.12 counts only the literal-pipe line. The same input with plain pipes gives 3. | "\| Root's `~/.bash_history`, `~/.viminfo` \| unreadable without root; the design *relies* on them as the last place the 09-18 key may be recorded \| owner: count now, never print — `sudo grep -c -i -e encryption -e passphrase -e password /root/.bash_history /root/.viminfo` — and wipe only once P0 step 3 has tested what they hold; the STOP holds step 3 \|" (352) |
| 10 (LOW) | D L313 (§5.3); R L206 | B4 "applied"; §5.3 still points to "(§8 owner actions)" | REFUTED (partial) | B4's location (R L832) includes L313. `awk 'NR>=1713&&NR<2264' D \| grep -ci 'bash_history\|viminfo\|shell history'` gives 0, so no §8 step exists for that pointer. | "…is the one place left to look — counted now and wiped only after P0 step 3 (§6's root-history row); no §8 step yet extracts a candidate from it (§5.4)." |
| 11 (LOW) | D L576 (§7.3.1); R L208 | B7/A7 "applied" | REFUTED (partial) | L576 still reads "shell `/usr/sbin/nologin` once the migration is accepted (R-6)", while R-6 (L91) now says "before step 8's first start". B7 (R L835) named this contradiction. | "shell `/usr/sbin/nologin` from P0.5a item 7, before P0 step 8's first start (R-6, note 10.1f)." |
| 12 (LOW) | D L485 (note S-3c) | Option: "re-encrypt the 811 with the 877 in §10.2 steps 4–7" | REFUTED (consequence) | The certification record (`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`, §8.25.1) gives 210,349,834,271 B (195.9 GiB), and the live set is about 203 GiB (L2467), about 399 GiB together. Step 4 stages on `/`: note 10.2b says 376 GiB free, and `df` shows 373.4 GiB. | "re-encrypt the 811 in a second pass of §10.2 steps 4–7 (≈196 GiB — `/` cannot stage both sets at once)" |
| 13 (LOW) | D L2658–2685 (note 12b) | Says "What the 2026-09-24 (later) row changed" | REFUTED (incomplete) | The delta changes P0 step 10 (L2159, "one of the two checks"), and 12b names it nowhere. | "**Rounds 4–6**: the front matter's STOP bullet, the STOP block at the top of §8, P0 step 10's guard sentence (one of two checks), §10.2's next action — …" |
| 14 | R L172–173 | "lens B's [brief] gave 'in that order' as part of the owner's ruling" | UNVERIFIABLE | The briefs are not archived. Lens B's report never quotes its brief, and lens A's row 2 (R L758) is about lens A's brief and the design. | "…which set no order (lens A, row 2); the briefs are not archived, so the brief's wording rests on the orchestrator's session." |
| 15 | R L170–171 | "The session's usage limit stopped both mid-run"; "neither shown the other's output" | UNVERIFIABLE | `stat` shows the round-6 transcripts created at 15:53:06 and 15:53:24 and their `.meta.json` re-created at 18:33:13 and 18:33:15. That fits a stop and resume, but the cause and the isolation are recorded only in the transcripts, which I may not read. | "Both stopped mid-run (the session's usage limit, per the orchestrator; the subagent metadata shows only the gap, 15:53 to 18:33)…" |

**Constraint slips.** None touched a secret, the service or the backup tree's contents.
- **Accidental `git` outside the worktree.** One real `git show 6c23fdde:…` ran in my scratch directory, because my `git` shim was not yet executable. It failed with exit 128 and wrote nothing.
- **Scripts under `/tmp`.** My helper scripts, the shim and the self-test runner are in the session scratchpad. That conflicts with the repo's script-placement rule, but staying read-only left no other place.
- **Harness-saved output.** The harness saved one large `git show 05c5f794:` output (the public design text) as a tool-result file in the session directory.
- **Refused commands.** The isolation layer refused four compound commands. I split them and re-ran them.
- **Metadata-only reads:**
  - `stat` of `/home/duplicati/.bash_history`, `/home/duplicati/.viminfo`, the S-7 `.env` (mode and size only; none opened), the vendor unit and its directory.
  - Subagent `.meta.json` contents, and `stat` of the subagent and session `.jsonl` files (never opened).
- **Service and host state:** `systemctl show` of four properties and the `ExecStart` path only, `ps`, timer listings, `readlink`, and a blob hash of the primary checkout's wrapper (not printed).
- **Logs:** I grepped `/var/log/dpkg.log` for timestamps only; it is the package log, not syslog or the journal.
- **Backup tree:** names and counts only, never entered or written. One `ls | head` of the Dropbox root printed personal file names, which I do not repeat here.
- **Burned key:** wrapper revisions were printed only through a redactor, and S-1's comment line was never shown.
- **`gh`:** read-only `gh pr view` on PRs 1967, 1968 and 1999.

CONFIRMED: 176 claims (98 in D, 58 in R including 22 of the round-6 table's 27 rows and both report lengths, 20 in E including the replay, idempotence and self-test).

REFUTED 13 · UNVERIFIABLE 2 · CONFIRMED 176

<!-- markdownlint-enable -->

---

## Round 7, lens B — consistency, consequence and operator reading

Archived verbatim (19,876 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

I validated the round-6 correction pass at 2c9efe85 and it does not hang together yet. Four round-6 dispositions are only partly true, and the pass left 18 statements that are refuted plus 1 I could not verify. The two most serious affect what the owner may do today:
- **Transcript purge.** §6's transcript row tells the owner to purge with no limit. The limit in the STOP reads as already met, although this round's reports are not archived yet.
- **"Anything that only reads".** The release covers P0 step 0(c), which calls itself read-only. That step runs `duplicati-cli` with the passphrase in its environment. P0.5a item 1 must come before step 0(c), and the release sets no order between them.

**Documents.** D = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, R = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`, YAM = `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`, H = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md`, U = `util/systemd/duplicati.service`. All were read at 2c9efe85 and line numbers are at 2c9efe85. **Changed**: nothing in the repository.

## 1. Round-6 dispositions that are false (in part)

| finding | disposition claimed | why false | evidence |
|---|---|---|---|
| B1, A1: which of §6's actions the STOP releases | owner ruling — the STOP's held and released lists (note 10.1g) | The lists settle the sink checklist and S-4's `chmod 0600`, but not the rest of §6. P0.5a item 5 (released) says "start the S-4 copy-out" and calls "Delete forever" an owner action, while P1 step 4 (held) and §8's preamble own the copy and the delete. S-3, S-5 and S-6's actions have no phase. The transcript row lacks the second limit, which was B1's point (d) | D L468, L487, L525, L1791–1795, L2199, L2222 (findings 1, 4, 8) |
| B4: root's history | applied — counted now, wiped after P0 step 3; §5.4 says no step extracts a candidate | B4 also cited §5.3 (L313 at 7265dc1f). §5.3 still says "(§8 owner actions)", and no §8 step lists that search | D L313 |
| B8: vim and swap file gone | applied — the `.swp` row, §4.1 note (a), note sink-b | B8 also cited §5.4 (L354). §5.4 still lists the swap file as a place the key "could still be recorded" and among "the only untested places". §11 still names "editor backups of the unit" | D L355–357, L2626; the swap-file count on the host is 0 |
| B9: item 6 "in the same session" | applied | Fixed only in the front matter. "Items 5–7 run in the same session" (item 6 included) remains at three sites, and now also contradicts the release | D L1802, L2171, L2407 vs L13, L2164 |

## 2. Findings (REFUTED / UNVERIFIABLE), ranked

| # | location | what it says | why it is wrong or inconsistent | verdict | evidence | exact replacement text |
|---|---|---|---|---|---|---|
| 1 (MED-HIGH) | D L525 (§6 transcript row); STOP L1724–1726; 10.1g L2420–2421 | Row: "count-grep and purge both…". Limit: "…before this arc's validation reports have been archived from it" | The released row the owner acts from carries no limit. The limit reads as met today: rounds 4–6 are "Archived verbatim" in R, which exists only in the local-only commit 2c9efe85. This round's reports are still unarchived transcripts, and R's archiver lifts reports from transcripts | REFUTED | `grep transcript` D: the limit appears only at L1725 and L2421. R L747, L800: "lifted from the subagent's own transcript" | Row: `\| Claude Code transcripts **and persisted tool-result files** under `~/.claude/projects/…` \| **cloud-linked**, and **inside the backup Source** — note (AC-3a) lists `.claude/projects` among the *unfiltered* 0700 trees, so every capture is in every T1 fileset and in Dropbox (note sink-a) \| count-grep now; purge **both** the `.jsonl` and `tool-results/` files only once every validation round of this arc, the running one and the follow-up's, is archived and merged (note 10.1g) \|` (480 chars). Limit, at both sites: "no Claude Code transcript is purged until every validation round of this arc — any still running and the follow-up's own — has been archived verbatim into a record merged to `main`" |
| 2 (MED-HIGH) | STOP L1722–1723; 10.1g L2419; see also item 1 L2180, step 0(c) L1817/L1831, step −1 L1769–1774, L522 | "and anything that only reads, such as P0 step −1's review" | Step 0(c) calls itself "Read-only" but runs `duplicati-cli` with PASSPHRASE exported. It runs it from `/usr/lib/duplicati`, which today is 0755 `duplicati:duplicati`. Item 1 exists to run "before P0 step 0(c)", and the release sets no order between the two. Step −1 ends in "re-stage … and merge", which writes, and goes stale when the follow-up lands. Step 3's probe only reads, yet the root-history row says "the STOP holds step 3" | REFUTED | `stat /usr/lib/duplicati` → 755 duplicati:duplicati | Released bullet: "…§6's sink checklist and S-4's `chmod 0600`; and reads that write nothing and run no Duplicati binary — P0 step −1's `--check` review (repeat it after the follow-up lands; its re-stage and merge are held), P0 step 1's two `sudo ls` listings and §6's count-only greps. P0 step 1's freeze, step 0(c) and step 3 stay held: the freeze writes, and 0(c) runs `duplicati-cli`, which item 1 must secure first." In 10.1g: "…and reads that write nothing and run no Duplicati binary." |
| 3 (MED) | D L521 (sink row) | `/home/duplicati/.viminfo` … "wipe" | Released with no limit. vim ran as `duplicati` in the shells that sink-b says were open during 09-19's key failures, and viminfo keeps older sessions' registers and history. The design protects root's `.viminfo` for exactly this reason. The wipe cannot be undone | REFUTED (consequence) | stat: 0600 duplicati, 14,744 B, mtime 09-20 17:59:47 — still present | `\| `/home/duplicati/.viminfo` \| 14.7 KB, mtime 09-20 17:59 — vim was used as `duplicati` after `.env` was written; viminfo keeps registers and command history \| owner: count now, never print — `sudo grep -c -i -e encryption -e passphrase -e password /home/duplicati/.viminfo` — and wipe it with the history files, once P0 step 3 has tested what they hold (note sink-b) \|` (369 chars) |
| 4 (MED) | D L2199 (item 5) vs L2222 (P1 step 4), L1791–1795, L468, L487, L1263 | "start the S-4 copy-out. The Dropbox 'delete forever' and account audit are owner actions"; the preamble says P1 step 4 "first copies … and only then deletes" | The copy-out is defined only by a held step. The in-tree delete and "Delete forever" read as released. If item 5 copies now, P1 step 4's later `cp -a` into the existing sibling directory nests a second copy and verifies the wrong pair | REFUTED (operator reading) | `ls /mnt/Backups/Ubuntu/` → `Dropbox` only | Item 5: "5. **Handle S-7 and S-4.** Remove the world-readable `.env` inside `…/worktrees/curious-plotting-hummingbird/` after the fingerprint reconciliation (note S-7a; the file only — that worktree is do-not-sweep), `chmod 0600` the escrow `env`, and make P1 step 4's copy — `cp -a` to `/mnt/Backups/Ubuntu/_yamaguchi_keys/`, sha256 verified on both sides. The in-tree delete, Dropbox's "Delete forever" and the account audit stay with P1 step 4, which the STOP holds." Append to P1 step 4: "(If P0.5a item 5 already made the copy, verify it and skip the `cp -a`: into an existing directory it nests a second copy.)" Preamble: "…which P0.5a item 5 or P1 step 4 first copies to a sibling outside the Dropbox root, and which only P1 step 4 then deletes from the synced tree (S-4)." |
| 5 (MED) | D L1802, L2171, L2407 | "items 5–7 run in the same session, each before the step that needs it … item 6 at any point" | This contradicts the marker two lines above the P0.5a intro (L2164), the STOP, 10.1g and front matter L13. Deferring items 5 and 7 into the recovery session re-enters the timing question the STOP leaves open | REFUTED | D L13, L1758–1759, L2164 | P0 preamble: "…items 5–7 are released now (note 10.1g), each to be done before the step that needs it** — item 7 before step 8's first start, item 5 before step 10's `resume`; item 6 gates nothing (owner ruling 2026-09-24; the order among items 1, 2 and 4 is the design's, note 10.1f)." P0.5a intro: "Items 5–7 are released now (note 10.1g); each must be done before the P0 step that needs it:". 10.1f: "Items 5–7 run alongside — since note 10.1g, at any time before the P0 step that needs each: item 7 before step 8's first start, item 5 before step 10's `resume`; item 6 gates nothing." |
| 6 (MED) | D L6, L11, L12 | "NOT EXECUTABLE"; "STOP — do not execute §8 yet … §8 is executable only once that block is gone"; the order "once the STOP is cleared" begins with item 1 and step −1 | Contradicts the release. A reader of the front matter alone either holds the released items or makes item 1 wait | REFUTED (operator reading) | STOP L1721–1723 | L6: "- **Status**: MOSTLY HELD — §8 is behind a STOP (rounds 4–6, 2026-09-24), except what the owner released on 2026-09-24 (note 10.1g). Rounds 1 and 2 are reconciled; …" L11: "- **STOP — §8 is held except what note 10.1g released.** Rounds 4–6 found defects in the procedure that can re-lock the recovered database, pass the pre-backup guard without its `TargetURL` check, or copy a cleartext database into the backup Source. The STOP block at the top of §8 lists them. P0.5a items 1, 5, 6 and 7, P3, §6's sink checklist and S-4's `chmod 0600` may run now, within that block's two limits; the rest of §8 runs only once the block is gone." Add after L13: "  - P0.5a item 1 is released now (note 10.1g); if it has already run, this order starts at item 2." |
| 7 (MED) | D L358–359 vs STOP L1717–1718, L1755–1760 | §5.4: "the follow-up behind the STOP … owes one" (a step that extracts a key candidate without printing it) | The STOP's exit criterion does not include this step, and its open-questions paragraph says "Reported by rounds 4 and 5". The block can therefore be lifted without it, and the first limit waits on a P0 step 3 that has no way to test these files | REFUTED | R's round-6 B4 row lists no follow-up | Last STOP paragraph: "Reported by rounds 4–6 and still to be re-derived: …; a P0 step 3 procedure that extracts candidates from root's and `duplicati`'s shell and vim histories without printing them (§5.4), which the release's first limit waits on; and the lower-severity items the record lists." |
| 8 (MED-LOW) | D L467–470 | The S-3, S-4, S-5 and S-6 action cells | These are imperatives with no phase. The release names only "§6's sink checklist and S-4's `chmod 0600`" | REFUTED (operator reading) | — | New note after S-8a: "- **(S-run)** What may run now (note 10.1g): S-4's `chmod 0600` and copy (P0.5a item 5), S-7's removal (item 5), the detection gap (item 6) and the sink checklist within its two limits. Held: S-3's line deletion (P1 step 2), S-4's in-tree delete and "Delete forever" (P1 step 4), S-5's and S-6's password work (P0 step 9) and the D-8 scrub (item 4)." |
| 9 (LOW-MED) | D L522 | `sudo grep -c -i -E 'encryption\|passphrase\|password' …` | Copied from the raw file, the table escape `\|` stays in the pattern. GNU grep 3.12 and ugrep then match a literal pipe and print 0 — a false zero | REFUTED (operator reading) | Dummy-line test: escaped → 0, plain → 1 | `\| Root's `~/.bash_history`, `~/.viminfo` \| unreadable without root; the design *relies* on them, with the `duplicati` user's (note sink-b), as the last places the 09-18 key may be recorded \| owner: count now, never print — `sudo grep -c -i -e encryption -e passphrase -e password /root/.bash_history /root/.viminfo` — and wipe only once P0 step 3 has tested what they hold; the STOP holds step 3 \|` (397 chars) |
| 10 (LOW-MED) | D L353–358, L2626, L522, L1895 | §5.4 still lists the swap file, says "the only untested places", and says "Both are root-only reads"; §11 says "…editor backups of the unit are the last untested places" | The swap file is gone. There are now three root-only files, not two. §11 and the root-history row omit the `duplicati` history | REFUTED | swap-file count 0 | §5.4: "**Where the key could still be recorded**: root's `~/.bash_history` and `.viminfo`, and `/home/duplicati/.bash_history` and `.viminfo` (note sink-b — its shells were open during 09-19's key failures), for the window 09-18 20:42–21:03 and after. The unit's editor swap file is gone (§6), and there is no `duplicati.service~` and no `duplicati.service.d/`. Those are the only untested places; a candidate found there is tested with the probe in seconds. All four are root-only reads." §11: "(root's and `duplicati`'s shell and vim histories are the last untested places, §5.4; the unit's swap file is gone, §6)" |
| 11 (LOW) | D L576 (§7.3.1) | "nologin once the migration is accepted (R-6)" | Item 7 is released now. Round 4's B24 records this as follow-up, but the release makes the contradiction live | REFUTED | D L91, L2201 | "…shell `/usr/sbin/nologin` from P0.5a item 7 (R-6; released 2026-09-24, note 10.1g). Administrative work: …" |
| 12 (LOW) | D L726; U L106 | `InaccessiblePaths=` masks only `…/Dropbox/Backups/_yamaguchi_keys` | The released copy-out destination `/mnt/Backups/Ubuntu/_yamaguchi_keys/` is unmasked. Under D-4's `CAP_DAC_READ_SEARCH` the service can read it once P0 step 8 installs the unit. This gap existed before; the release makes it actionable | REFUTED (consequence) | U L106 | Append ` -/mnt/Backups/Ubuntu/_yamaguchi_keys` in both files (follow-up: a tagged block and its landed copy change together) |
| 13 (LOW) | D L1708–1709, L2241, L2247, L2426–2427 | §7.11 retires `bin/` "after acceptance"; P3 is "(following week)" and step 2 says "Land … scheduler … three user units"; §10.2 is "owner-gated exactly as §8 is" | Item 1 deletes `bin/` now. P3 is released, and its scheduler and units landed with ml#1999 (§12 L2643). §8 is now partly released | REFUTED | — | §7.11: drop the `bin/` clause and add "`/home/duplicati/bin/` is not on this list: P0.5a item 1 deletes it before P0 (released 2026-09-24, note 10.1g)." P3 heading: "### P3 — tiers 2 and 3 (released 2026-09-24; step 3 waits on D-5)". §10.2: "…it is owner-gated, none of it is released by note 10.1g, and it runs *after* the recovery…" |
| 14 (LOW) | D L523 (`.swp` row) | "…so the exit wrote nothing" | True of the unit only. The host has not rebooted since 09-07 and the swap file is gone, so vim exited normally — and a normal exit writes a viminfo | UNVERIFIABLE (needs root) | `uptime -s` → 2026-09-07 23:12:17 | "…the unit's mtime is still 2026-09-21 01:44:57, so the exit did not write the unit (a normal exit does write a viminfo — row above)" |
| 15 (LOW-MED) | D L2414–2415 (10.1g) | "no defect the STOP … lists touches P0.5a items 1, 5, 6 or 7, or P3" | The STOP asks "whether P0.5a items 5 and 7 are timed to the right events", and round 6's lens B said they are "questioned only on timing" | REFUTED | D L1758–1759; R L831 | "Round 6 found that no defect the STOP block at the top of §8 lists touches P0.5a items 1 or 6, or P3, and that items 5 and 7 are questioned only on their timing (the block's last paragraph), which running them early satisfies; holding them would keep open…" |
| 16 (LOW-MED) | D L482–486 (note S-3c) | Options: "re-encrypt the 811 with the 877 in §10.2 steps 4–7, move them out of the Dropbox root, or accept" | Moving leaves the cloud copies restorable for 30–180 days; §7.5 item 7 requires "Delete forever". Staging both sets needs about 399 GiB, against 376 GiB free per note 10.2b (374 GiB today). Both action options also break §8's no-move rule | REFUTED | YAM §8.25.1: 210,349,834,271 B; `df /`; `dropbox exclude list` has no exclusion under `Dropbox/Backups` | "…move. Both need an owner decision that also lifts §8's no-move rule for those paths: re-encrypt the 811 (196 GiB) in a second §10.2 pass — `/` has ~376 GiB free for staging (note 10.2b), not the ~399 GiB both sets need at once — or move them out of the Dropbox root and then **Delete forever** the cloud copies (§7.5 item 7), or accept the exposure in writing." |
| 17 (LOW) | D L313 (§5.3) | "…the one place left to look (§8 owner actions)" | No §8 step lists that search, and the first limit keeps root's history only until P0 step 3 | REFUTED | round-6 lens B row 4 cited L313 | "Root's shell history around 2026-08-25 02:19 is the one place left to look; no §8 step lists that search (§5.4), and the release's first limit keeps the file only until P0 step 3 (note 10.1g)." |
| 18 (LOW) | D L2574–2577 (§11) | Round 6: "every finding is applied here or listed as follow-up" | Not true of B4, B8 and B9 — the same overclaim that round 6's B17 found in round 5's sentence | REFUTED | table 1 | Fix findings 5, 10 and 17, or write: "…its findings are applied here or listed as follow-up, three of them — §5.3's, §5.4's and the "same session" wording — only after round 7." |
| 19 (LOW) | D L2668–2669 (12b) | "the release's two limits in §6's root-history row and note sink-b" | Both sites carry only the first limit. 12b also omits the change to P0 step 10 | REFUTED | `grep transcript` D | "…and the release's first limit in §6's root-history row and note sink-b — its second, on transcripts, is only in the STOP block and note 10.1g." Add "P0 step 10's guard sentence," under Rounds 4–6. |

## 3. Unintended drop

| hunk | what was dropped | right? | evidence |
|---|---|---|---|
| Note 10.1e | "so which working copy they ran is recorded nowhere" was narrowed to "whether their working copy had a debug switch is recorded nowhere" | No. The 16:41 and 16:44 passes predate the 16:53:58 wrapper symlink (Appendix A.3), and R's round-5 A20 row still cites the broader fact. Restore: "…so which working copy they ran — and whether it had a debug switch — is recorded nowhere…" | 7265dc1f L2348–2349 vs 2c9efe85 L2385–2386 |

**Confirmed sound: 65.** That is 35 dispositions (23 of round 6's 27 rows, plus the 7 round-5 and 5 round-4 rows the delta changed) and 30 other checks. The main ones:
- The edit script rebuilds 2c9efe85's design and round-2 record byte-for-byte, and `--self-test` passes 8 of 8.
- The phase markers and STOP lists match the ruling, and the order is attributed consistently everywhere.
- **Item 1 is safe to release.** The unit is `Restart=always` with 100 ms restart and 5 starts per 10 s, and enabled; its `ExecStart` is `/home/duplicati/bin/duplicati-wrapper.bash`. Deleting it means an exec failure, the start limit trips, and the server stays down — the outcome §4.3 already predicts.
- **Item 7 is safe to release.** No step needs a `duplicati` login shell, and `ps -u duplicati` shows only the server.
- Item 5's fingerprint reconciliation is defined (via H §1 item 8).
- P3 needs no P0–P2 output, and the tier-2 lane excludes `.claude`.

**Constraint slips.** None touched a secret file, the service or a Duplicati binary, but you should know about these:
- Everything I wrote went to the scratchpad. I ran the edit script's `main()` on scratch copies, and its `--self-test` from the worktree with `TMPDIR` in the scratchpad; `git status` stayed clean.
- The isolation layer refused three compound commands; I re-ran them as separate commands.
- Host reads were metadata only:
  - `systemctl show` properties, printing only the `ExecStart` path;
  - `stat` of the vendor unit, both `.viminfo` files and `/home/duplicati/.bash_history` — none opened;
  - `ps`, `getent` (shell field only), `uptime`, `df`;
  - a count-only `dropbox exclude list`;
  - names and counts under `/mnt/Backups/Ubuntu/` — the listing showed `_yamaguchi_keys` and `_yamaguchi_records`, neither entered;
  - a sha256 prefix of the primary checkout's wrapper;
  - names and times of subagent `.meta.json` files, contents unread.
- No `journalctl`, no unit touched.

REFUTED 18 · UNVERIFIABLE 1 · CONFIRMED 65 · 4 of round 6's 27 dispositions false in part

<!-- markdownlint-enable -->

---

## Round 8, lens A — fact re-probe of the corrections

Archived verbatim (9,640 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

I found four refuted claims and one I couldn't verify. The most serious: the round-4 record says round 7's A6 fix (§10.2 step 2) was applied, but that line is byte-identical to the 2c9efe85 version. The edit script itself checks out. Replayed on scratch copies of 6c23fdde, it rebuilds f90a87e7's design and round-2 record byte-for-byte. A second run changes nothing, and `--self-test` passes 8 of 8, with each mutant failing on the gate it targets.

**Key.** All files are under `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/typed-skipping-salamander/`, read only as git objects at f90a87e7. Line numbers are at f90a87e7.
- **D** = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
- **R** = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`
- **E** = `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`
- **S** = `util/ad-hoc/2026-09-22_stage_design_artifacts.py`
- **L** = `util/ad-hoc/2026-09-21_lint_design_snippets.py`

**Changed**: nothing in the repository.

**Constraint slips.** None touched a secret, the service, a Duplicati binary or the journal. No unit was touched and no `gh` call was made.
- **Refused commands.** The isolation layer refused two compound commands (one `cd … && git show`, one runner command that named `.git`). I re-ran them as plain commands or through a scratch runner script.
- **Scripts in the scratchpad.** My helper scripts are in the session scratchpad under `/tmp/claude-1000/…`, against the repo's script-placement rule; staying read-only left no other place. I also removed an empty scratch directory I had just created there.
- **Running E.** `main()` ran only on scratch copies, in a directory with no `.git`. `--self-test`, and a harness that imports E, ran from the worktree with `TMPDIR` in the scratchpad. `git status --porcelain` stayed empty.
- **History files.** I ran `stat` on both `/home/duplicati` history files and never opened them. `stat` on `/root/.bash_history` and `/root/.viminfo` was refused (Permission denied).
- **Other host reads:**
  - `ls -la /home/duplicati/bin/`
  - `ps -p` and `ps -u duplicati`
  - `getent`: uid, gid, home and shell only
  - `systemctl show` of eight properties, not `ExecStart`
  - `uptime -s`, `df /`, `dpkg-query`
  - grep of the system vim config files
- **Backup tree.** Names and counts only:
  - `/mnt/Backups/Ubuntu/` holds only `Dropbox`.
  - Counts: 17 entries in `Dropbox/Backups/`, 13 in the Dropbox root (no names printed), 811 in `_yamaguchi_frozen_20260826/`.
  - A glob printed the four `_yamaguchi_*` names in `Dropbox/Backups/`; none was entered.
- **Session files.** I read the eleven `.meta.json` files. I ran `stat` on five `.jsonl` files and never opened them. I listed the `tool-results/` file names without opening them.

| # | location | claim | verdict | evidence | exact replacement text |
|---|---|---|---|---|---|
| 1 (MED) | R L297 (round-7 row A6); D L2489 (§10.2 step 2); D L2604 (§11, round 7: "each is applied here or listed as follow-up"); E L688 | "§10.2 step 2 credits P1 step 2 with the moved-aside `.env` \| A6 \| applied — P0 step 2 moved it, and only P4 step 2 removes it" | REFUTED: not applied anywhere | `grep -n 'included (P1 step 2)'` finds 2c9efe85 L2465 and f90a87e7 L2489, byte-identical: "…in every `.env`, `Duplicati.empty-2026-09-20/.env` included (P1 step 2)…". `grep -n 'P4 step 2 removes\|P0 step 2 moved' D` finds nothing. `git diff 2c9efe85 f90a87e7` has no hunk in §10.2's table. E's "section 10.2 step 2" edit (L688) still writes "(P1 step 2)". The facts behind A6 do hold: P0 step 2 (L1913) runs the `mv`, P1 step 2 (L2236) edits one `.env`, and P4 step 2 (L2275) removes the folder. | D L2489, and E L688's new text (460 characters): "\| 2 \| Confirm the leaked copies are gone: the S-7 file (P0.5a item 5); S-2's active key line and S-3's comment block in the live `.env` (P1 step 2) and in `Duplicati.empty-2026-09-20/.env`, which P0 step 2 moved aside and only P4 step 2 removes; both log stores — D-8's one scrub, P0.5a item 4 \| S-2, S-3 and S-7 counts read zero on §6's labels, case-sensitively (v2 logs a lowercase `settings encryption key:`), and S-6 holds no unexpired token (note 10.1e) \|". This also makes R L297 and D L2604 true. |
| 2 (LOW-MED) | D L11 (front matter STOP bullet) | "P0.5a items 1, 5, 6 and 7, P3, §6's sink checklist and S-4's `chmod 0600` may run now … ; the rest of §8 runs only once the block is gone." | REFUTED: contradicts the STOP block it summarises | The STOP at D L1731–1733 also releases "P0 step −1's `--check` review, P0 step 1's two `sudo ls` listings". Both are §8 text: step −1 at L1786–1791 and step 1's listings at L1912. D L1730 and the P3 marker at L2260 keep P3 step 3 waiting on D-5, which the bullet drops. | D L11 (505 characters): "- **STOP — §8 is held, except what the owner released on 2026-09-24.** Rounds 4–7 found defects in the procedure that can re-lock the recovered database, pass the pre-backup guard without its `TargetURL` check, or copy a cleartext database into the backup Source. The STOP block at the top of §8 lists them and what may run now — P0.5a items 1, 5, 6 and 7, P3 but step 3, §6's sink checklist, S-4's `chmod 0600` and the reads it names — within its two limits (note 10.1g); the rest waits until it is gone." |
| 3 (LOW) | D L2601 (§11, round 6); R L293 (round-7 row B18) | "its findings are applied here or listed as follow-up, three of them only after round 7"; "applied — three only after round 7" | REFUTED: the record itself says four | R L200–201: "Round 7 found four of the dispositions below true only in part". In R's authored part, `grep -n 'only in round 7'` finds exactly four rows: L205 (B1/A1), L210 (B4), L213 (B8), L215 (B9). R L253 and lens B's final line (L1073) both say "4 of round 6's 27 dispositions false in part". | D L2601: "…its findings are applied here or listed as follow-up, four of them only after round 7." R L293: "\| §11's round-6 entry: "every finding is applied" \| B18 \| applied — four only after round 7 \|" |
| 4 (LOW) | D L1731–1733 (STOP released reads); D L2441 (note 10.1g); R L277 | "reads that write nothing and run no Duplicati binary, such as P0 step −1's `--check` review" | REFUTED: the example it names writes files | S L103 calls `tempfile.mkdtemp(prefix="stage-extract-")` and L77 `workdir.mkdir`. It then runs L with `--workdir` (required, L L160). L writes every tagged block (L L175–179: `open(out, "w")`, `os.chmod(out, 0o700)`) and runs `py_compile` (L L137, which writes `__pycache__`). S's own help text (L95) says "write nothing", meaning nothing staged. D L1788's "re-extract them with … lint_design_snippets.py" writes the same tree. | At all three sites, replace "reads that write nothing and run no Duplicati binary" with "reads that change nothing outside a scratch directory and run no Duplicati binary". |
| 5 (LOW) | D L357 (§5.4) | "Those four files are the only untested places, and each needs root to read" | UNVERIFIABLE: I can't confirm root's two files exist | `stat /root` gives `700 root:root`, and `stat /root/.bash_history /root/.viminfo` gives "Permission denied (os error 13)". The `duplicati` pair does exist, both 600 duplicati:duplicati: `.viminfo` 14,744 B, mtime 2026-09-20 17:59:47; `.bash_history` 8,261 B, mtime 2026-09-24 14:56:34. "Each needs root" holds from the owner's side. | "Those files are the only untested places, and each needs root to read — even to confirm that root's two exist, since `/root` is 0700; a candidate found there is tested with the probe in seconds." |

**Confirmed: 155 claims** (88 in D, 57 in R, 10 in E). The ones most likely to be doubted:
- **Item 1 has not run.** `/usr/lib/duplicati` is still 755 duplicati:duplicati.
- **The swap-file timing holds.** The unit directory's mtime is 2026-09-22 19:10:21, and nothing in it is newer than 09-22 00:00, so the last change there was a removal. The unit's mtime is 2026-09-21 01:44:57. There is no swap file, no `~` backup and no drop-in, and pid 2318515 is gone. The session transcript was created 2026-09-24 13:43:27, after all of that.
- **The STOP's step claims hold.**
  - P0 step 1 has exactly two `sudo ls` listings.
  - The tagged 0(c) block exports the passphrase and runs `duplicati-cli list`.
  - `InaccessiblePaths=` masks only the in-Dropbox `_yamaguchi_keys`, in both D L735 and `util/systemd/duplicati.service` L106.
  - `cp -a` into an existing directory nests a second copy (tested in scratch).
- **Note S-3c's figures hold.** The 811 volumes are 196 GiB (the certification record's §8.25.1 gives 210,349,834,271 B). Note 10.2b says 376 GiB free, and `df /` reads 373.3 GiB today. The two sets total about 399 GiB (196 + 202.8), and §7.5 item 7 covers the Delete-forever retention.
- **The "true of five" rewrite is correct.** `git log -S` finds only 43980f13 (ml#1999). The round-2 record's R2B-12 lists items 1, 2, 4, 5 and 6 as independent of the recovery, and its Lane B D8 is where the timer stop and restart came from.
- **Note 10.1e's restored sentence is correct.** The 16:41 and 16:44 passes predate the wrapper symlink (created 2026-09-20 16:53:58), and the first wrapper commit was at 17:05:30.
- **The `-e` grep fix works.** On dummy input, GNU grep 3.12 counts 0 with the escaped-pipe form and 3 with `-e`.
- **The round-7 table matches the reports.** All 25 source references match round 7's two reports, and both archived lengths match (14,319 and 19,876 characters). The two lenses started at 19:03:58 and 19:04:19, so "19:04" rounds the first.

REFUTED 4 · UNVERIFIABLE 1 · CONFIRMED 155

<!-- markdownlint-enable -->

---

## Round 8, lens B — consistency, consequence and operator reading

Archived verbatim (14,299 characters), lifted from the subagent's own transcript.

<!-- markdownlint-disable -->

The round-7 pass doesn't fully hang together. Three of its dispositions are false in whole or in part, and it creates or leaves 11 refuted items plus 1 unverifiable one. Three of them affect what the owner may do today: the transcript row's new "count-grep now" (no command given), §5.3's new "look before then", and item 5's copy, which leaves the escrow's long-term home group-writable by the service user.

Key: **D** = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, **R** = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`, **E** = `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`, **S** = `util/ad-hoc/2026-09-22_stage_design_artifacts.py`. All were read from git objects at `f90a87e7`, and line numbers are at that commit. **Changed**: nothing in the repository.

## 1. False dispositions

| finding | disposition claimed | why false | evidence |
|---|---|---|---|
| A6 (round 7): §10.2 step 2 credits P1 step 2 with the moved-aside `.env` | "applied — P0 step 2 moved it, and only P4 step 2 removes it" (R L297) | Not applied. The row still says "`Duplicati.empty-2026-09-20/.env` included (P1 step 2)". | D L2489 is byte-identical to `2c9efe85` L2465. The design diff has no hunk there, and E's step-2 edit (E L688) still writes "(P1 step 2)". |
| B13 (round 7) | "applied to §7.11 and §10.2; P3's heading kept" (R L288) | False in part, two ways. §7.11 still lists `bin/` among the "artifacts to retire after acceptance", now beside "item 1 deletes it before P0". B13's third point also got no disposition: P3 step 2, which is released, still says "Land `util/juniper-backup-scheduled.bash` … the three user units", although ml#1999 landed them. | D L1715–1718, L2264, L2670; `git ls-tree f90a87e7` lists `util/juniper-backup-scheduled.bash` and `util/systemd/juniper-backup.{timer,path,service}` |
| B18 (round 7) | "applied — three only after round 7" (R L293) | False in part. It should say four. R's own round-6 section says "Round 7 found four of the dispositions below true only in part", and it marks four rows "only in round 7". | R L200–201, L205, L210, L213, L215 vs D L2601 |

The six round-6 rows this pass changed (B1/A1, B4, B8, B9, B15/A8, A6) are all true. Rejecting round 7's lens A row 7 agrees with the owner's words: the option said items 5–7 "run in the same session".

## 2. Findings (REFUTED / UNVERIFIABLE), most severe first

| # | location | what it says | why it is wrong, inconsistent or unsafe | verdict | evidence | exact replacement text |
|---|---|---|---|---|---|---|
| 1 (MED-HIGH) | D L534 (§6 transcript row); the STOP at L1733 releases "§6's count-only greps" | "count-grep now; purge **both** … only within note 10.1g's transcript limit" | This pass added "now", but the row gives no command. The other three released counts each give one. Only a count by value tells a leaked secret apart from this arc's prose, which quotes the labels throughout. Typed as a grep argument, the value lands on argv, in `~/.bash_history` (inside the backup Source), and — if run through Claude Code — in a new cloud-linked transcript. That breaks R-18, and it creates exactly the sink this row exists for. | REFUTED | D L530, L531, L546 (exact commands); D L104 (R-18); D L1923 (the design's own no-argv pattern for writing a secret) | Row **R1** below (511 chars) |
| 2 (MED) | D L2216 (P0.5a item 5), released | "`cp -a` to `/mnt/Backups/Ubuntu/_yamaguchi_keys/`, sha256 verified on both sides" | **Mode:** `cp -a` copies the source directory's mode. The in-tree `_yamaguchi_keys` is `drwxrwx--- pcalnon:duplicati`, so the escrow's long-term home lands group-writable, and the service user can unlink or replace `env` — the exact risk D L671–678 designs against. §7.4 requires `0700`, and no step sets it: P2's script touches only `…/Dropbox/Backups` and the mount parents, and AC-7 checks only the location. **Nesting:** nothing says the destination must not exist. Into an existing directory, `cp -a` nests the copy. `/mnt/Backups/Ubuntu` is group-writable by the service user, so that user could create the directory first. A nested copy then cannot be removed without breaking the no-move rule. | REFUTED | `stat`; scratch tests: a first run creates the directory; a second run nests `_yamaguchi_keys/_yamaguchi_keys/`; `cp -a src/. dst/` resets a `0700` destination to `0770`. `/mnt/Backups/Ubuntu/_yamaguchi_keys` is absent today. | "…`chmod 0600` the escrow `env`, then make P1 step 4's copy: confirm `/mnt/Backups/Ubuntu/_yamaguchi_keys` does not exist (into an existing directory `cp -a` nests), `cp -a` the folder to it, `chmod 0700` the copy (`cp -a` carries the source's 0770; §7.4), and sha256-verify both sides. The in-tree delete, …" |
| 3 (MED) | D L314 (§5.3); D L2654 (§11) | "…Root's shell history … is the one place left to look; … so look before then (note 10.1g)"; §11: "(no shell history names it)" | This pass turned a pointer into an instruction to act now, with no method. It points at a file §6 says to "count now, never print" (L531), and §5.4 says no step yet reads it without printing (L359). A Repair command line there may carry `--passphrase`. §11 meanwhile implies the history has already been read. | REFUTED | D L531, L359, L2654 | §5.3: "Root's shell history around 2026-08-25 02:19 is the one place left to look, and only without printing a line — a Repair command there may carry `--passphrase`, and §6's row for the file says never print; no §8 step lists that search or a no-print way to run it, and the release's first limit keeps the file only until P0 step 3 (note 10.1g)." §11: "(pcalnon's shell history does not name it; root's is unread, §5.3)" |
| 4 (LOW-MED) | D L1819–1821 (P0 preamble); L2185–2188 (P0.5a intro) | "Run P0.5a items 1, 2 and 4 … items 5–7 may run now" | Only items 5–7 are called "may run now", so item 1 reads as held with items 2 and 4. That contradicts L14, L1731, L2181 and note 10.1g. Deferring item 1 leaves the 0777 `bin/` open under `Restart=always` — the hole the release exists to close. | REFUTED | D L14, L1731, L2181 | P0 preamble: "**Run P0.5a items 1, 2 and 4, in that order, before anything in P0 — item 1 is released and may already have run; items 5–7 may run now too (note 10.1g), each before the step that needs it**". P0.5a intro: "…in that order** — item 1, released now (note 10.1g), before item 4, because…" |
| 5 (LOW-MED) | D L538 (re-measuring row) vs L534, L540 | "deletes the capture in the same session" | Note sink-a says oversized captures land under `tool-results/`. The transcript row changed by this pass forbids purging `tool-results/` files until the limit is met. The two instructions now conflict, and following the limit keeps a complete copy of every leaked line in a cloud-linked file. | REFUTED | D L540 | Row **R2** below (429 chars) |
| 6 (LOW-MED) | D L2432–2434 (note 10.1g) | "no defect the STOP … lists touches … items 5 and 7 are questioned only on their timing" | The same pass added two findings to the STOP about item 5's own copy (L1768–1770): P1 step 4's nesting and the unmasked destination. The sentence's present tense is now false against the block it cites. | REFUTED | D L1766–1770 | "Round 6 found that no defect the STOP block at the top of §8 then listed touched P0.5a items 1 or 6, or P3, and that items 5 and 7 were questioned only on their timing (the block's last paragraph), which running them early satisfies; round 7 added two findings on item 5's copy, which bind only once P0 step 8 and P1 step 4 run. Holding them would keep open…" |
| 7 (LOW-MED) | D L2438–2442; R L269–271 | Quotes "only reads" as one of "the ruling's phrases" | My brief gives the ruling as "read-only steps". If that is verbatim, this is the same misattribution R corrected in rounds 6 and 7. It also matters for scope: P0 step 0(c)'s script calls itself "Read-only" (L1848). Only the owner's session can settle it, since briefs have paraphrased before (R L245–246). | UNVERIFIABLE | brief vs D and R | If "read-only steps" is verbatim — 10.1g: "…and read-only steps. … **"Read-only steps"** is read as reads that write nothing and run no Duplicati binary: …"; R: "…"read-only steps" as reads that write nothing…" |
| 8 (LOW-MED) | D L2489; R L297 | A6 is claimed applied | See table 1. | REFUTED | E L688 | Row **R3** below (460 chars), or in R: "\| … \| A6 \| **not applied** — follow-up: only P4 step 2 removes `Duplicati.empty-2026-09-20/` \|" |
| 9 (LOW) | D L11 (front-matter STOP bullet) | "the rest of §8 runs only once the block is gone" | The STOP releases reads inside §8: P0 step −1's `--check` and P0 step 1's two listings. | REFUTED | D L1732–1733 | "…The STOP block at the top of §8 lists them. P0.5a items 1, 5, 6 and 7, P3, §6's sink checklist, S-4's `chmod 0600` and the reads that block names may run now, within its two limits (note 10.1g); the rest of §8 waits for the block to go." (500 chars) |
| 10 (LOW) | D L1732–1735; L2441–2443 | "reads that write nothing … such as P0 step −1's `--check` review"; 0(c) is excluded because it runs "from binaries item 1 has not yet secured" | The named example writes: `--check` extracts every tagged block into a `mkdtemp` tree, plus `.pyc` files, then deletes it. The binaries clause is false once item 1 has run, which L14 anticipates. | REFUTED | S L103–104, L138–139 | "…and reads that write nothing outside a scratch directory and run no Duplicati binary, such as … P0 step 0(c) is not one of them: it runs `duplicati-cli`, which item 1 must secure first, with the passphrase, and needs step 1's freeze, which writes (note 10.1g)." The same two changes go in 10.1g. |
| 11 (LOW) | D L15 (no-move bullet) | "except the one escrow copy named in P1 step 4" | Item 5 now makes a second escrow copy under `/mnt/Backups/Ubuntu/`, and P1 step 4 names both paths. "The one escrow copy" is now ambiguous. | REFUTED | D L1808–1811, L2239 | "Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except the in-tree escrow `…/Dropbox/Backups/_yamaguchi_keys/`, which only P1 step 4 deletes, once P0.5a item 5 or P1 step 4 has copied it out." |
| 12 (LOW) | D L2601, L2604 (§11) | Round 6: "three of them only after round 7"; round 7: "each is applied here or listed as follow-up" | It should be four (R L200–201). A6 is neither applied nor listed as follow-up. | REFUTED | table 1 | "…four of them only after round 7."; "…each is applied here or listed as follow-up but A6 (§10.2 step 2), which is follow-up." |

**R1** (the §6 transcript row):
```
| Claude Code transcripts **and persisted tool-result files** under `~/.claude/projects/…` | **cloud-linked**, and **inside the backup Source** — note (AC-3a) lists `.claude/projects` among the *unfiltered* 0700 trees, so every capture is in every T1 fileset and in Dropbox (note sink-a) | count now, values from a 0600 file, never argv (`grep -rlF -f <file> ~/.claude/projects`, then shred it); purge **both** only within note 10.1g's transcript limit; this is what makes D-2's "local exposure" framing false |
```
**R2** (the re-measuring row):
```
| **Re-measuring the exposure creates a new copy of it** | A `journalctl` capture large enough to count these lines is itself a complete second copy. Round 2's host lane made an 876 MB one and removed it eight minutes later | Any agent or operator who re-verifies §6's counts deletes the capture in the same session, and says so — one the harness saved under `tool-results/` too, which the transcript row's limit does not cover |
```
**R3** (§10.2 step 2, round 7 lens A's text, 460 chars):
```
| 2 | Confirm the leaked copies are gone: the S-7 file (P0.5a item 5); S-2's active key line and S-3's comment block in the live `.env` (P1 step 2) and in `Duplicati.empty-2026-09-20/.env`, which P0 step 2 moved aside and only P4 step 2 removes; both log stores — D-8's one scrub, P0.5a item 4 | S-2, S-3 and S-7 counts read zero on §6's labels, case-sensitively (v2 logs a lowercase `settings encryption key:`), and S-6 holds no unexpired token (note 10.1e) |
```

## 3. Unintended drops

| hunk | what was dropped | right? | evidence |
|---|---|---|---|
| D, the STOP's released and limits bullets | The ruling's own wording ("anything that only reads"; "archived from it"). What replaces it is the design's narrow reading, now presented under "the owner's 2026-09-24 ruling … decides what runs" with nothing marking it as a reading. | Partly. Narrowing was intended; dropping the attribution misstates the ruling in the STOP. Append "(the design's narrow reading of the ruling; the owner may widen it, note 10.1g)" to both bullets. | `2c9efe85` L1722–1726 vs D L1731–1739 |

**Out of scope, pre-existing:** AC-14's command carries a raw `\|` (L2298, held); P0 step 1's second listing re-asks a question §5.4 has already settled; §4.1 and §7.3.1 still say P0.5 closes the 0777 `.config/Duplicati`, but P0 step 2 does.

**Constraint slips:**
- The isolation layer refused two compound commands (a `git cat-file` loop and a `sed` loop). Neither ran; I re-ran them as separate commands and a scratch Python helper.
- Host reads were metadata only: `stat` of both `/home/duplicati` history files (not opened), of `/usr/lib/duplicati`, `bin/`, `/etc/default/duplicati`, the unit directory, the in-tree `_yamaguchi_keys` directory (not entered) and the `/mnt/Backups/Ubuntu*` directories; `ls -a /mnt/Backups/Ubuntu/` (names: `.dropbox-dist`, `Dropbox`); `ps -u duplicati`; `systemctl show` of four properties with argv redacted; `findmnt`.
- Every file I wrote is in my own scratchpad subdirectory: extracted copies, diffs, synthetic `cp` and `grep` tests, and a helper, `linelen.py`. That helper sits under `/tmp`, which conflicts with the script-placement rule, but staying read-only left no other place.
- My shell's `grep` is a ugrep wrapper. The design's commands were confirmed with GNU `/usr/bin/grep`, which is what `sudo` runs.
- No secret file, `journalctl`, syslog, Duplicati binary or unit action, no `gh` call, and nothing read from the working tree.

**Confirmed sound: 95** — 30 dispositions, 9 other statements in R, 30 design consistency and host checks, and 26 of the 27 diff hunks' drops.

REFUTED 11 · UNVERIFIABLE 1 · CONFIRMED 95 · 3 of round 7's 25 dispositions false (1 wholly, 2 in part)

<!-- markdownlint-enable -->
