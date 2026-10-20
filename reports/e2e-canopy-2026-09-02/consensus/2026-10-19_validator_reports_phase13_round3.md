<!-- markdownlint-disable -->

# Phase 13 ledger validation, round 3 — validator reports (verbatim)

Round 3 of the consensus review of the canopy E2E ledger's Phase 13 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen local commit 10194b8c (round 2's corrections applied by util/ad-hoc/2026-10-19_phase13_ledger_round2_corrections.py; juniper-ml worktree federated-stargazing-blanket, branch docs/canopy-e2e-phase13). Two lanes from one brief on round 2's corrections only (reports/e2e-canopy-2026-09-02/drafts/lane13R3_phase13_ledger_brief.md): Lane 13-R3A replayed the pass and re-derived every claim it introduced; Lane 13-R3B was adversarial on the pass. Each agent ran once, so the archiver's round-1 slot holds its only report. Each report is the lane's final message, archived verbatim; the orchestrator's dispositions are in the ledger's Phase 13 consensus record.

## Lane 13-R3A (replay and re-derivation)

*agent `a1fbc83cfe4541610` · round 1 · last-assistant-text (not resumed) · 10791 chars*

**Lane 13-R3A** (replay and re-derivation, round 3)
**VERDICT: SOUND-WITH-FIXES** — the pass replays byte for byte on all six files, every claim it introduced re-derives (the audit at `c741351c`, the GitHub-fetched CHANGELOG, manual and parser source executed, the triage before and after), and no count, header, rating or disposition moves. Two MINORs, both in the record's description of itself (where the reach statement lives; five hunks its change list omits), and two NITs.

**REPLAY** (`git show c741351c:<path>` → scratch copy → `python3 -B util/ad-hoc/2026-10-19_phase13_ledger_round2_corrections.py --root <copy>` → byte compare with `git show 10194b8c:<path>`; the pass printed "ledger: 19 substitutions + the round-2 record, 1015879 -> 1022846 chars / handoff: 9; parent: 2; index: 1; roadmap: 1; audit: 2 / written", exit 0)
- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: byte-identical (1,028,570 B)
- `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`: byte-identical (15,130 B)
- `HANDOFF_2026-10-03_canopy-consolidated.md`: byte-identical (58,903 B)
- `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: byte-identical (9,959 B)
- `notes/JUNIPER_2026-05-25_…V7-IMPLEMENTATION-ROADMAP.md`: byte-identical (684,649 B)
- `notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md`: byte-identical (38,009 B)
- No hand edit. `--check` against the worktree: "this is not the round-2 freeze (c741351c)", exit 1, nothing written; `--check` on a fresh `c741351c` copy exits 0 with all six hashes unchanged. The worktree's six files equal `10194b8c`; `git status --short` shows only the untracked round-3 brief, before and after.

**TABLE**

| claim | re-derived | result | evidence |
|---|---|---|---|
| Audit @c741351c: §5.1 `:107`, `:112` "CAN-015g replay V2 wired" under juniper-canopy; §5.2 `:122`, `:124` "both are **shipped end-to-end** on `main`", eight rows `:130-137`, g-3 `:132`; §11.4 `:318`, `:323` "#180 (g-1), #191 (g-6)", no #189/#190 | `git show c741351c:<audit> \| grep -n` / `sed -n` | MATCH | `:113`, cascor's own row, names "CAN-015g weight history (g-1)" only |
| Audit last changed 2026-07-04 | `git log --format='%h %ad %s' --date=short -3 -- <audit>` | MATCH | `86f1fd3d`, `432ed644` (2026-07-04), then `10194b8c`; absent from `c741351c` |
| Correction @10194b8c = design note `:61-80` = §28.1 `:15148-15157` = F-057 History `:9192-9200` | read side by side | MATCH | #190 → `…-weight-cache-v2` 2026-05-03T20:05:12Z; #189 → `main` 19:52:10Z; thirteen minutes; `dbc25277` 3 ahead / 537 behind `4c26919f` (2026-10-16; History's 512 is at the older `0e016a7c`, the Status bullet carries 537); canopy#684 2026-09-24; the added §11.4 sentence is what `:323` says |
| No markdown link added; g-3 row annotated | `git diff … -- <audit> \| grep '^+' \| grep -c ']('` → 0; roadmap `](` 3 before / 3 after | MATCH | audit `:142` "— **not on `main`**: merged into a stacked base (correction 2026-10-19; F-CANOPY-057)" |
| Roadmap CAN-015 row annotated; nothing else changed | `grep -n 'g-3 did not ship'` → `:5196` (+ `:15149`, §28.1's own note); `git diff --numstat` 1/1 | MATCH | `grep -c 'Correction 2026-10-19'` stays 1 (the row's "correction" is lower-case) |
| CHANGELOG @571743db: `## [0.6.0] - 2026-07-28` `:2171`, `## [0.5.0] - 2026-05-23` `:2919`, `:2909` under 0.6.0 | `gh api … contents/CHANGELOG.md?ref=571743db`; `grep -n '^## \['` | MATCH | `:2909` "#1 TAB-FEEDBACK-LOOP — collapse to one tab-persistence system" under `### Fixed` `:2893`; `:1436-1437` "survives to the modal" under `## [0.8.0]` `:1295` |
| Manual @571743db: Phase `:686`, Candidate Epoch Progress condition `:687-688` → cite `:686-688` | fetched; `sed -n '683,690p'` | MATCH | `:687` "shown only while the training state carries" / `:688` "`candidate_epoch` and `candidate_total_epochs`"; `:328` Phase Duration |
| `_resolve_patch_values` `:457-506`, `len(rows) > 1` branch `:490-495` returns rows unchanged; one-value rows right only for one output | AST-lifted from the fetch and executed | MATCH | `"1;2;3;4"` and `"1\n2\n3\n4"` → `[[1],[2],[3],[4]]`: 4×1 ≠ (2, 2) for topology (1, 1, 2), = (4, 1) for (2, 2, 1); `"1,2,3,4"` → 2×2 for (1, 1, 2); "rejected wherever the network has more than one output" is the right scope (the ledger's `:457-507` is round 1's, off by one) |
| Handoff verification commands @10194b8c | all run, read-only | MATCH | tail -7 = 79/56/1/2/20, 9, 11; `grep -c '^OPEN   P1 '` 9 (the nine IDs as listed); "P1 since" 5; Phase 13 `:11845`; design note 2, roadmap 1, audit 1; compare `behind`; manual `:510`; `gh pr list` `[]`; lsof nothing |
| Triage 79/56/1/2/20, 9 P1, 11 P2, unchanged; five headers unchanged | triage on the `c741351c` pre-image (`--note`) and on the freeze; `--open-only` outputs `cmp`-identical; `git diff … -- <ledger> \| grep -c '^[-+]\*\*F-'` → 0 | MATCH | |
| Record vs diff hunk by hunk: 19 + record / 9 / 2 / 1 / 1 / 2 | each hunk mapped to a bullet | nothing listed that the diff does not make; five hunks unlisted (F2); one overstatement (F1) | |
| Amended round-1 sentences vs round 1's pass | `grep -n` in `…round1_corrections.py` | MATCH | the five "omitted hunks" are its lines 98, 209, 274, 417, 459; `[0.5.0]` is its lines 272/357 and the round-1 report has 0 `0.5.0` ("round 1 wrote" is right); F-056 bullet `:9143` "**Re-rated P1**, on plan §6.3's rule", `:9141` "has not been driven live" |
| Three figures in four places at `c741351c` | `git show c741351c:… \| grep -n broadest` | MATCH | ledger `:11897` (Summary), `:12175` (Matrix effect), handoff `:44-45`, parent `:465`; INDEX 0 |
| Credits and dissents | round-2 report file; round-1 record `:12162-12170` | MATCH | R2A F1/R2B F1 MAJOR (audit); R2B F2 MAJOR, R2A F3 (item 8); R2A F2/R2B F3 (0.6.0); R2A F4/R2B F4 (record); R2A F7 (one output; CAN-015 row); R2B F6 (`:686-688`); R2A F5/R2B F5 (F-067 in the Summary); R2A F6 ("from Phase 5's on"); F-028 "one lane P2" (13-B, 8/12; 13-A "P1, narrowly"), F-067 "one lane P1 by source" (13-B, 10/10) |
| Stale-phrase scan @10194b8c (eight files) | scratch `scan_phrases.py` | MATCH | "only through … audit" 0; "broadest reading", "dated snapshot", "activity line", "commit themes" only inside the record or as round 1's described ground; `:686-687` 0; "since Phase 5's" 0; "decides F-CANOPY-065 alone" only with "among the findings Phase 11 named" (Matrix effect, handoff `:98`, parent `:465`) |
| Gates | `python3 -B -m unittest` (4 suites) | 38 tests OK | |

**FINDINGS**

1. **MINOR** — the record places the reach statement where it is not. Text (round 1's amended sentence, `:12105-12109`): "the reach statement is restated in all nine of the Summary, …, the parent's O17 and the INDEX, with the three figures … in four of them (…; the INDEX carries counts only)"; (round 2, `:12198-12201`): "Stated so in the Summary, …, the handoff, the parent's O17 and item 4, and the INDEX". Evidence: the INDEX's P2 row has no "first limb", "F-CANOPY-065" or "broadest" at `c741351c` or `10194b8c` (0 hits); the parent's item 4 (`:125-129`) has no "first limb"; both carry the counts and the list of corrected documents only, so the reach statement is in eight places, and round 2 changed item 4 and the INDEX only by adding "and the 2026-05-05 roadmap audit's §5.2" to that list. The round-3 brief inherits "and the INDEX". Fix: "in eight of them (the INDEX carries counts only)"; "…, the parent's O17, and, as the list of corrected documents, the parent's item 4 and the INDEX". Changes a number, disposition or action? no.

2. **MINOR** — "What round 2 changed" omits five hunks the diff makes (the class round 2 itself corrected in round 1's record): the ledger's "Sources read" amendment ("after rounds 1 and 2 … §5.1, §5.2 and §11.4", `:11939-11940`); the amendment of round 1's "Not applied" ("declined in round 1 on a reading of its `:112` line alone …", `:12156-12158`); the handoff's PR-contents sentence ("and the audit's corrections", `:57`); the handoff's added audit grep (`:133`); the handoff's two "Changed by this session" entries (`:160-161`). (Item 4 also gained the `[0.8.0]`/`[0.6.0]` tags, which the 0.6.0 bullet credits to "Still owed" and round 1's record only.) Fix: a clause in the "round 1's record" bullet and one under "wording". Changes a number, disposition or action? no.

3. **NIT** — the audit cites are `c741351c`'s and the pass moved the lines. The ten-line note inserted at `:124` shifts the sentence to `:134`, the g-3 row to `:142`, §11.4 to `:328` and the cascor line to `:333` at `10194b8c`, so the Summary's "(`…ROADMAP-AUDIT.md:124`, `:132`)" and "(`:323`)" and "The design note's correction"'s "(`:122-134`)", "(`:318-323`)" now point into the correction block and the heading. Same convention as the roadmap's `:15146-15160`, whose g-3 row has sat at `:15167` since round 1. Fix: "(at `c741351c`)" once, or re-point. Changes? no.

4. **NIT** — "four documents" vs "four sites". The handoff's item 4 (`:89`) says "the four documents that recorded F-CANOPY-057's stream as shipped are corrected"; the ledger (`:12059`, `:12244`), the record (`:12197`) and item 8 (`:99`) say "four sites", which sit in three documents (design note; roadmap §28.1 and CAN-015 row; audit §5.2). And the Summary (`:11896`) and F-057's Status (`:9184-9186`) say the CAN-015 row carries "the same (dated) correction", where it carries a one-clause pointer to §28.1's note ("The design note's correction", `:12058`, says exactly that: "annotated the CAN-015 row"). Fix: "four sites in three documents"; "§28.1 carries the same correction and the CAN-015 row points to it". Changes? no.

**WHAT YOU COULD NOT CHECK**
Nothing live (no service here; none touched). The GitHub shas and times beyond the compare, taken as rounds 1 and 2 verified them (the design note, §28.1 and History agree with each other and with the new note). cascor's own shape validator was not fetched, so "cascor's shape check rejects" a 4×1 body for a (2, 2) target rests on the entry's original 422 and canopy's docstring. Whether §5.1's "CAN-015g replay V2 wired" under the canopy row "stands" is the orchestrator's reading; the artifact supports it (cascor's row names g-1 only), and whether any audit counts as a design plan is O17 itself. The lanes' unarchived scratch probes and the owner's merge approval.

**SECRETS/PII:** nothing printed; no `.env*` read; git read-only inside the worktree (`show`, `diff`, `status --short`, `log --format='%h %s'` / `'%h %ad %s' --date=short`); `gh` read-only (raw contents, `compare --jq .status`, `pr list`); the diff's five non-hunk `@` are the archived round-2 reports' "@566cb72a"/"@c741351c" table shorthand and three backticked rule texts (masked scan: 0 e-mail shapes, 0 token prefixes, 0 secret-like assignments).

---

## Lane 13-R3B (adversarial on the pass)

*agent `a3b155d26199f2574` · round 1 · last-assistant-text (not resumed) · 11384 chars*

**Lane 13-R3B** (adversarial on the pass, round 3)
**VERDICT: SOUND-WITH-FIXES** — the pass replays byte for byte, every figure it introduced re-derives, no count, rating or disposition moves, and the reach statement is consistent where it was rewritten. What round 2 left: its absolute "no document … still records the stream as shipped" is contradicted by two un-annotated rows of the same audit it corrected; the record repeats the two record-keeping faults it charged round 1 with (hunks unlisted; "nine" places where there are eight); "10 and 10 remains only by the F-CANOPY-067 dissent" forgets the F-CANOPY-049 counter-reading; the F-012 qualifier did not reach item 30; the handoff's landing trap names one of three passes. Six MINOR, three NIT.

**REPLAY** — `git show c741351c:<path>` for the six files under `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/438B5B69-ACCF-4C62-BE45-EEFFF048856D/scratchpad/lane13R3B/replay_root/`, then `python3 -B util/ad-hoc/2026-10-19_phase13_ledger_round2_corrections.py --root <copy>` ("ledger: 19 substitutions + the round-2 record, 1015879 -> 1022846 chars; handoff: 9; parent: 2; index: 1; roadmap: 1; audit: 2; written", exit 0), each result compared as bytes with `git show 10194b8c:<path>`:
- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: byte-identical
- `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`: byte-identical
- `HANDOFF_2026-10-03_canopy-consolidated.md`: byte-identical
- `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: byte-identical
- `notes/JUNIPER_2026-05-25_…V7-IMPLEMENTATION-ROADMAP.md`: byte-identical
- `notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md`: byte-identical
No hand edit. `--check --root <worktree>` exits 1, "this is not the round-2 freeze (c741351c)", nothing written. `git diff --stat 10194b8c -- <six files>` is empty; `git status --short` shows only the untracked round-3 brief.

**TABLE**

| claim | re-derived | result | evidence |
|---|---|---|---|
| audit @c741351c: §5.2 `:122`, sentence `:124`, g-3 `:132`; §11.4 `:318`, cascor line `:323`; §5.1 `:112`; last change 2026-07-04 | `git show … \| grep -n`; `git log --format='%h %ad %s' --date=short -3` | MATCH; the eight-row table is `:128-137` (g-7 `:137`), so `:122-134` is short (F8) | "#180 (g-1), #191 (g-6) — all confirmed on main"; `86f1fd3d 2026-07-04` |
| the note @10194b8c = design note `:61-73` = §28.1 `:15148-15157` = F-057 History `:9177`, `:9199`, `:12031-12032`; no link added; g-3 row annotated | sed over all four; `grep -c '^+.*]('` on the diff | MATCH: `…-v2` 20:05:12Z, #189 on `main` 19:52:10Z, 3 ahead / 537 behind at `4c26919f`, canopy#684; the one `+` link hit is the roadmap row's pre-existing links; audit `:142` annotated | diffs |
| roadmap: CAN-015 row annotated, nothing else changed | `grep -n 'g-3 did not ship'`; `git diff --stat` | MATCH: `:5196` and `:15149` (round 1's note); 1 insertion, 1 deletion | |
| CHANGELOG @571743db | fetched to scratch; `grep -n '^## \['` | MATCH: `## [0.6.0] - 2026-07-28` `:2171`, `## [0.5.0] - 2026-05-23` `:2919`; `:2909` "#1 TAB-FEEDBACK-LOOP — collapse to one tab-persistence system"; `:1436-1437` "survives to the modal" under `[0.8.0]` `:1295` | |
| manual `:686-688` | fetched | MATCH: `:686` Phase, `:687-688` the Candidate Epoch Progress condition; `:328` Phase Duration | |
| `_resolve_patch_values` scope | fetched; read | MATCH by source: `_parse_float_rows` `:437-455`; `_resolve_patch_values` `:457-507`; `len(rows) > 1` (`:490`) returns rows (`:495`) after an equal-width check only, so N one-value rows reach the wire as (N, 1): right when output_size is 1 and N = I+H, cascor's shape check otherwise | |
| handoff verification @10194b8c | all run, read-only | MATCH: `gh pr list` `[]`; triage 79/56/1/2/20, P1 9, P2 11; `^OPEN   P1 ` 9; 'P1 since' 5; Phase 13 `:11845`; design note 2; roadmap 1; audit 1; compare `behind`; `:510`; lsof nothing | |
| triage; five headers | run; `git diff c741351c 10194b8c -- <ledger> \| grep -c '^[-+]\*\*F-'` | MATCH: 9 P1 = 012, 013, 018, 028, 032, 064, 065, CASCOR-001, -002; 11 P2; 0 header lines | |
| record vs diff hunk by hunk; credits; dissents | 19/9/2/1/1/2 counted against the script; round-2 file; round-1 file `:140`, `:142` | lists match, nothing listed the diff does not make; six hunks unlisted (F2); credits match R2A F1–F7 / R2B F1–F6; Lane 13-B "I would rate P2 … Counts 8/12" and "P1 by source today (10/10)", Lane 13-A "P1, narrowly" / "unchanged" — stated so | |
| round 1's amended record vs round 1's pass | round-1 script read | item 18's F-067 sentence, the "Sources read" sentence, the FAQ parenthetical, the handoff's PR sentence and roadmap grep are all round-1 substitutions — MATCH; 10/10 in four places — MATCH; "all nine" — FALLS (F3) | |
| stale phrases across nine files ("only through … audit", "activity line", "broadest reading", "dated snapshot", "commit themes", "now decides … alone", "[0.5.0]", ":686-687", "since Phase 5's") | phrase_scan.py | 0 hits outside the consensus record's quotations of round 1 and the Phase 13 apply script's frozen pre-image strings (by design) | |
| gates | unittest, 4 suites | 38 tests OK | |

**FINDINGS**

1. **MINOR** — the absolute reach sentence overstates what the audit now says. Text: "No document this phase or its lanes read still records the stream as shipped" (F-057 Status, `:9185`); "With the four sites corrected, no document this phase or its lanes read records the stream as shipped" (`:12059-12060`); handoff `:89` "the four documents that recorded F-CANOPY-057's stream as shipped are corrected". Evidence: the audit at `10194b8c` still says, un-annotated and outside §5.2, "CAN-015g/h shipped end-to-end without any roadmap delta | All 15 sub-tasks" (§8.1, `:225`) and "§5 CAN-015g/h shipping claim | CONFIRMED via git log + roadmap line 5121 quote" (§11.7, `:360`); inside §5.2 under the note, "**Status delta**: … code says 'shipped, hardened, integration-tested'" (`:168`). Lane 13-R2B cited the first and third (as `:215`, `:158`); the pass annotated neither and "Not applied" says "Nothing" — the reading error round 2 rated MAJOR, here against a corrected section. Fix: annotate `:225` and `:360` with a pointer to §5.2's note as the CAN-015 row was, or narrow the three sentences to "records it without a dated correction in the section that makes the claim". Changes a number, disposition or action? no count, rating, disposition or O17 framing; an audit edit only if the pointer treatment is chosen.

2. **MINOR** — "What round 2 changed" omits six hunks, the fault round 2 charged round 1 with. Evidence (diff vs `:12193-12217`): the "Sources read" sentence ("after rounds 1 and 2 … §5.1, §5.2 and §11.4", `:11939-11940`); the rewrite of round 1's "Not applied" bullet (`:12156-12158`) and the "(reversed in round 2)" parenthetical (`:12105`); the handoff's PR-contents sentence (`:57`), its verification block's audit grep (`:133`) and its two "Changed by this session" lines (`:160-161`). Fix: a clause under "wording". Changes? no.

3. **MINOR** — "nine" places where there are eight. Text: round 1's amended record, "the reach statement is restated in all nine of … the parent's O17 and the INDEX" (`:12106-12108`); round 2's "the reach statement in nine, the INDEX carrying counts only" (`:12206-12207`) and "Stated so in … the parent's O17 and item 4, and the INDEX" (`:12199-12201`). Evidence: the INDEX row (`:26`) at `c741351c` and `10194b8c` carries counts and the corrected-document list and no reach statement (0 hits for "first limb", "F-CANOPY-065", "F-CANOPY-057", "O17", "9/11"); the parent's item 4 (`:128`) likewise. Fix: "eight; the INDEX and the parent's item 4 name the corrected documents only". Changes? no.

4. **MINOR** — "10 and 10 remains only by the F-CANOPY-067 dissent" (`:12198`). Evidence: the ledger's F-CANOPY-049 counter-reading also counts 10 and 10 ("A reader who takes the other view would count 10 open P1 and 10 open P2", `:11932`; round 1's record `:12119`). The Summary's counts line, which speaks of dissents only, is right. Fix: "by the F-CANOPY-067 dissent and the F-CANOPY-049 counter-reading". Changes? no.

5. **MINOR** — the F-012 qualifier stops short of item 30. Text: item 30 `:12281` "by source the semicolon and newline forms become one row per value and are rejected"; handoff item 2 `:70-71` "read as rows and rejected". Evidence: the pass qualified the entry (`:3898`), "The five re-ratings" (`:11984`) and the handoff's Completed bullet (`:52-54`) with "wherever the network has more than one output"; item 30 sets the drive's expectation, and on a one-output network the two forms are accepted by the ledger's own new sentence. Fix: the same qualifier in both. Changes? no (the measured network has two outputs).

6. **MINOR** — the landing trap names one of three passes. Text (handoff `:118-119`): "Build each from a fresh `origin/main` copy at upload time and re-apply with `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py --root <copy>`". Evidence: that script reproduces `566cb72a`'s text; `10194b8c` needs `…round1_corrections.py` then `…round2_corrections.py` on top, the audit's correction and both consensus records exist only in them, and item 1's post-merge check ('P1 since 2026-10-19' = 5) passes on the apply script alone. Fix: "then the round-1 and round-2 correction passes, in that order". Changes? no ledger count, rating or disposition; it changes the landing recipe's re-apply step.

7. **NIT** — handoff item 4 `:89` "the four documents": three documents, four sites (ledger `:12059`, handoff `:99` "four sites"). Changes? no.

8. **NIT** — pre-pass line numbers. The ledger cites the audit at `:124`, `:132`, `:323` (`:11893-11894`), `:122-134`, `:318-323` (`:12053-12055`, `:12218-12219`); after the ten-line note they sit at `:134`, `:142`, `:333`, `:132-144`, `:328-333`, and `:122-134` ends at g-5a. Fix: "at `c741351c`", or the new numbers and `:122-137`. Changes? no.

9. **NIT** — the corrected-site list differs by file: the ledger and handoff count four (the CAN-015 row's pointer included, called "the same dated correction" at `:11896`); the parent's item 4 (`:128`) and the INDEX (`:26`) name the design note, §28.1 and §5.2; the Phase 12 handoff's SUPERSEDED banner (`:4-5`) names the design note's correction only. Changes? no.

**WHAT YOU COULD NOT CHECK**
The GitHub shas and times (20:05:12Z, 19:52:10Z, 3 ahead / 537 behind) were matched across the three in-repo statements and round 2's API re-derivation, not re-queried; cascor's shape validator was not fetched (the one-output scope is canopy source plus the entry's 422); nothing live, no service touched; the lanes' unarchived probes; the owner's merge approval; whether an audit's root-cause row counts as a "design plan" is O17 itself.

**SECRETS/PII:** nothing printed; git read-only inside the worktree (`show`, `diff`, `status --short`, `log --format='%h %s'` / `'%h %ad %s' --date=short`, `--oneline`); `gh` read-only (raw contents, `compare --jq .status`, `pr list --json`); the diff's five `@` outside hunk headers are the `@566cb72a` / `@c741351c` table cells and backticked rule text of the archived round-2 reports and brief; 0 e-mail shapes, 0 token prefixes; no `.env*` read; worktree unchanged (only the untracked round-3 brief).

---
