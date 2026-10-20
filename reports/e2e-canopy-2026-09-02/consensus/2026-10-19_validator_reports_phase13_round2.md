<!-- markdownlint-disable -->

# Phase 13 ledger validation, round 2 — validator reports (verbatim)

Round 2 of the consensus review of the canopy E2E ledger's Phase 13 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen local commit c741351c (round 1's corrections applied by util/ad-hoc/2026-10-19_phase13_ledger_round1_corrections.py; juniper-ml worktree federated-stargazing-blanket, branch docs/canopy-e2e-phase13). Two lanes from one brief on the corrections only (reports/e2e-canopy-2026-09-02/drafts/lane13R2_phase13_ledger_brief.md): Lane 13-R2A replayed the pass and re-derived every claim it introduced; Lane 13-R2B was adversarial on the pass. Each agent ran once, so the archiver's round-1 slot holds its only report. Each report is the lane's final message, archived verbatim; the orchestrator's dispositions are in the ledger's Phase 13 consensus record.

## Lane 13-R2A (replay and re-derivation)

*agent `acbb641580f62d525` · round 1 · last-assistant-text (not resumed) · 11120 chars*

**Lane 13-R2A** (replay and re-derivation, round 2)
**VERDICT: SOUND-WITH-FIXES** — the pass replays byte for byte, every number it introduced re-derives (GitHub API, canopy source executed, manual, matrix, CHANGELOG, triage), and no count, rating or disposition moves. One MAJOR: the 2026-05-05 audit records g-3 as shipped in more than "an activity line" (its §5.2 is the same per-PR table the pass corrected in the roadmap), so the record's description of that artifact and the ground given under "Not applied" do not match it. Three MINOR, three NIT.

**REPLAY** (`git show 566cb72a:<path>` → scratch copy → `python3 -B util/ad-hoc/2026-10-19_phase13_ledger_round1_corrections.py --root <copy>` → cmp with `git show c741351c:<path>`; script printed "ledger: 24 substitutions + the round-1 record, 1001017 -> 1015879 chars / handoff: 13; parent: 2; index: 1; phase12: 1; apply script: 1; roadmap: 2 / written", exit 0)
- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: byte-identical (1,021,574 B)
- `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`: byte-identical
- `HANDOFF_2026-10-03_canopy-consolidated.md`: byte-identical
- `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: byte-identical
- `HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md`: byte-identical
- `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`: byte-identical
- `notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md`: byte-identical
- No hand edit. `--check --root <worktree>` exits 1: "this is not the round-1 freeze (566cb72a)"; `--check` on a fresh 566cb72a copy exits 0 and writes nothing. The worktree's seven files equal c741351c; `git status` shows only the untracked R2 brief.

**TABLE**

| claim | re-derived | result | evidence |
|---|---|---|---|
| Roadmap @566cb72a: §28.1 heading "shipped end-to-end" :15146, g-3 row :15156 "cascor #190 (retarget of #187) \| Sample-boundary weight emission \| `dbc25277`", CAN-015 row :5196 "8 PRs for CAN-015g" → §28.1 | `git show 566cb72a:<roadmap> \| sed -n` | MATCH | both ranges |
| Audit :112 "CAN-015g replay V2 wired" | sed | MATCH, but :122-134 and :318-323 say more (F1) | audit §5.1 header "commit volume since 2026-04-23" :107 |
| Roadmap correction = design note = F-057: #190 → `…-v2` 2026-05-03T20:05:12Z `dbc25277`; #189 → `main` 19:52:10Z `b1d19948`; 13 min; 3 ahead / 537 behind `4c26919f` (2026-10-16T09:33:36Z, still cascor `main` head); canopy#684 2026-09-24 | `gh api pulls/190,189,187`, `compare/4c26919f...dbc25277`, `commits/main` | MATCH (#187 07:31:04Z, base `…-cache`; History's 512 is at the older `0e016a7c`, the Status 2026-10-19 bullet carries 537) | design note :61-76, :107; ledger 9192-9200, 9171-9176 |
| Correction adds no markdown link | diff grep `^+.*](` | MATCH: the one hit is the g-3 row's pre-existing `[cascor #190]` | roadmap diff |
| Roadmap last changed 2026-07-04 | `git log --format='%h %ad %s' --date=short -3 -- <roadmap>` | MATCH: 86f1fd3d, 432ed644 (2026-07-04) before c741351c | log |
| `_parse_float_rows` :437-456: `;` and `\n` are row separators; `len(rows) > 1` returns rows unchanged | fetched at 571743db; functions lifted by AST and executed | MATCH (def :437-455, :456 blank; the branch is :490-495). `"1;2;3;4"` → rows `[[1],[2],[3],[4]]`, resolve returns them unchanged (4×1 for a (2,2) net); `"1,2,3,4"` → `[[1,2],[3,4]]`; `"1\n2\n3\n4"` behaves as `;` | exec_funcs.py |
| Manual :266 env line; :267-269 Apply sentence; :285 both modes; :328 Phase Duration; :686-687 Phase / Candidate Epoch Progress | fetched at 571743db | MATCH | sed |
| Matrix :807 M-WORKERS-02 FAIL, no id; :822-824 PASS / PASS (name arm; value pending an Apply) / PASS; C2.9-05 whole-row FAIL (F-018); NE-09/-13/-17 PASS/FAIL halves | sed | MATCH | matrix :350, :807, :822-824, :895-903 |
| Phase 5's Still owed names F-039, F-037, F-038, F-036, F-026 only; no Still-owed list from Phase 5's on carries the wave; Phase 4's prose does | ledger 6385-6391; scan of all 12 `### Still owed*` sections | MATCH (last listing 6279-6280; Phases 11/12 name F-012/-013 for item 26 only) | still_owed_scan.py |
| Phase 11 "three open P2s are already known to be within reach"; F-013 unsettled | sed | MATCH | 11286-11287, 11301, 11176 |
| F-CASCOR-004 FIXED by cascor#674; F-056 "re-rated P1, on plan §6.3's rule", "has not been driven live" | sed | MATCH (the F-056 bullet is labelled "Re-rated P1", not "Severity") | 6455; 9142, 9140 |
| Handoff verification commands @c741351c | all run read-only | MATCH: pr list `[]`; tail -7 = 79/56/1/2/20, 9, 11; `grep -c '^OPEN   P1 '` 9; "P1 since" 5; Phase 13 at :11843; design note 2; roadmap 1; compare `behind`; :510; lsof 0 | outputs |
| CHANGELOG `#532` at :534/:535/:541 only, in the [0.9.0] F-059 entry; :1436-1437 under [0.8.0] | fetched | MATCH | headings :12, :1295 |
| `[0.5.0]`'s tab-persistence entry at :2909 | fetched | FALLS: :2909 is under `## [0.6.0] - 2026-07-28` (:2171-2918); `## [0.5.0]` starts :2919 (F2) | grep `^## ` |
| Triage 79/56/1/2/20, 9 P1, 11 P2; `grep -c 'P1 '` 10; five headers unchanged | run; `git diff … \| grep '^[-+]\*\*F-'` | MATCH; empty | triage_full.txt |
| Record lists every hunk and nothing else; credits; "Not applied"; dissent wording | diff hunk by hunk vs report file | 24/13/7 substitutions match; credits and dissent wording match 13-A/13-B/13-C verbatim; two hunks unlisted (F4); audit ground (F1) | ledger.diff, others.diff |
| Alternatives "9/11, 8/12, or 10/10 by the broadest reading" consistent across files | grep | Summary, Matrix effect, handoff Counts, parent O17 identical; F-057/F-065 bullets, Still owed, handoff item 4 state the scope the same way; INDEX states counts only (never carried alternatives); handoff item 8 stale (F3) | grep `9/11\|alone` |
| Banner "item 3's first half" vs Phase 12 item 3; "Changed by this session" vs diff; apply header vs README :17-31 | read | MATCH (item 3 :71-75 = sweep, then CHANGELOG/plans after the ruling, plus the note's correction; roadmap listed; `Retire when:` / `Related:` present) | files |
| Gates | `python3 -B -m unittest` (4 suites) | 38 tests OK | run |

**FINDINGS**

1. **MAJOR** — the audit is mis-described. Text: "the 2026-05-05 audit's activity line (`…ROADMAP-AUDIT.md:112`) still reads "CAN-015g replay V2 wired" and is left as a dated snapshot, the one document through which the first limb could still reach this entry" (F-057 Status bullet); "a dated snapshot of commit themes since 2026-04-23, not a plan's promise" ("The design note's correction"; "Not applied"); "F-CANOPY-057 only if an audit's activity line is read as a design-plan promise" (Summary). Evidence: `notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md:122-134`, "### 5.2 Critical blind spot — CAN-015g and CAN-015h … As of 2026-05-05 both are **shipped end-to-end** on `main`", with a per-sub-task table whose g-3 row (:132) reads "cascor #190 (retarget of #187) | Sample-boundary weight emission" — the same table the pass annotated in the roadmap's §28.1; §11.4 "CAN-015g/h shipping verification" (:318-323) confirms on `main` only cascor #180 (g-1) and #191 (g-6), so the audit's own verification never confirmed #190. Round 1 (Lane 13-B) cited :112 only; the orchestrator re-derived :112 only. Fix: name §5.2 (:124, :132) beside :112 in the Summary, "The design note's correction", F-057's Status bullet, Still owed, the handoff and the parent's O17; ground "Not applied" on "an audit, not a plan" rather than "commit themes", or give §5.2 the same dated note as §28.1 (it is the same table), citing §11.4. Changes a number, disposition or action? no count or disposition (10/10 remains the broadest reading; the audit stays history); the action "leave the audit" was decided on a description the artifact does not match.

2. **MINOR** — wrong release tag on a lead. Text: "`[0.5.0]`'s "one tab-persistence system" (`:2909`) for F-CANOPY-051" (Still owed, 12195) and "`[0.5.0]`'s tab-persistence entry" (record, 12109). Evidence: CHANGELOG at 571743db, `## [0.6.0] - 2026-07-28` :2171, `## [0.5.0] - 2026-05-23` :2919; :2909 is the "#1 TAB-FEEDBACK-LOOP — collapse to one tab-persistence system" bullet under 0.6.0's second `### Fixed` (:2893). Lane 13-B named only `:2909`; the tag is the orchestrator's. Fix: `[0.6.0]`. Changes a number, disposition or action? no.

3. **MINOR** — a stale sentence the pass left in the handoff. Text (handoff :96, item 8): "the owner batch O1–O17 (O17's first limb now decides F-CANOPY-065 alone)". Evidence: unchanged by the pass (others.diff); contradicts the same file's :39-41, :44-45 and every corrected statement. Fix: "(O17's first limb decides F-CANOPY-065, and F-CANOPY-057 only through the 2026-05-05 audit)". Changes a number, disposition or action? no.

4. **MINOR** — "What round 1 changed" omits two hunks. Evidence: the sentence added to "Sources read" (11932-11933, "In this repo, after round 1: the V7 roadmap's §28.1 and CAN-015 row and the 2026-05-05 audit's §5.1") and the handoff's new verification line (:129, `grep -c 'Correction 2026-10-19' <roadmap>   # 1`); the FAQ re-read parenthetical (12037-12038) likewise. Fix: add a clause to the wording bullet. Changes a number, disposition or action? no.

5. **NIT** — the F-067 dissent is recorded in the Consensus record, item 18 and the handoff but not in the Summary, which names only F-028's ("one round-1 lane dissents from it"). Fix: "and from F-CANOPY-067's 'unchanged'". Changes? no.

6. **NIT** — handoff :54 "carried by no Still-owed list since Phase 5's" reads as if Phase 5's carried it; the ledger says "from Phase 5's on" (Phase 4's prose, 6279-6280, is the last listing). Fix: "from Phase 5's on". Changes? no.

7. **NIT** — "cascor rejects the shape" for the `;`/newline forms holds for the measured (12, 2) network and any output_size > 1; with one output, one-value rows are the right shape (`_resolve_patch_values` :490-495 returns them unchanged). And the roadmap's CAN-015 row (:5196) still reads "Shipped end-to-end … 8 PRs for CAN-015g" un-annotated (the ledger says it "points to §28.1 and is left"), so "only through that audit line" is slightly over-stated. Fix: "rejected wherever the network has more than one output"; "through the audit, or the CAN-015 row read without its pointer". Changes? no.

**WHAT YOU COULD NOT CHECK**
Nothing live (no service here; none touched). The lanes' scratch probes (not archived) and the owner's merge approval. The handoff's `**Consensus**: CONSENSUS_SUMMARY_PENDING` is a placeholder for landing, not reviewed. Whether an audit (§5.1 or §5.2) counts as a "design plan" is O17 itself. `weights_at` callers in cascor's tests were not read; `28da69f8^` was not resolved.

**SECRETS/PII:** nothing printed; no `.env*` read; git read-only inside the worktree with `--format='%h %s'` / `--oneline`; `gh` read-only with `--jq` field selection; the diff's two `@` outside hunk headers are the archived report's and Lane 13-C brief's own rule text (masked check: 0 e-mail patterns, 0 token prefixes).

---

## Lane 13-R2B (adversarial on the pass)

*agent `ac230b4cab2cbe395` · round 1 · last-assistant-text (not resumed) · 10921 chars*

**Lane 13-R2B** (adversarial on the pass, round 2)
**VERDICT: SOUND-WITH-FIXES** — the pass replays byte for byte, every count and disposition holds, and the record's credits and dissents match the round-1 file. Two MAJORs: the 2026-05-05 audit the pass disposes of as "a dated snapshot of commit themes" at `:112` also states, in its §5.2, that CAN-015g is "shipped end-to-end on `main`" with a g-3 row; and the handoff's item 8 still carries the sentence round 1's MAJOR withdrew. Neither moves today's 9/11.

**REPLAY** — the seven pre-images copied from `566cb72a` under their relative paths; `python3 -B util/ad-hoc/2026-10-19_phase13_ledger_round1_corrections.py --root <copy>` printed "ledger: 24 substitutions + the round-1 record, 1001017 -> 1015879 chars; handoff: 13; parent: 2; index: 1; phase12: 1; apply script: 1; roadmap: 2; written", exit 0; each result `cmp`'d with `git show c741351c:<path>`:
- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: byte-identical
- `notes/JUNIPER_2026-05-25_…V7-IMPLEMENTATION-ROADMAP.md`: byte-identical
- `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`: byte-identical
- `HANDOFF_2026-10-03_canopy-consolidated.md`: byte-identical
- `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: byte-identical
- `HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md`: byte-identical
- `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`: byte-identical
No hand edit. `--check` against the worktree: "this is not the round-1 freeze (566cb72a)", exit 1, nothing written; `git status --short` before and after shows only the untracked round-2 brief.

**TABLE**

| claim | re-derived | result | evidence |
|---|---|---|---|
| roadmap at 566cb72a: §28.1 heading `:15146`, g-3 row `:15156`, CAN-015 row `:5196`; audit `:112` | `git show`, `sed` | MATCH | "shipped end-to-end"; g-3 `… \| dbc25277 \|`; `:5196` "✅ Shipped end-to-end … 8 PRs for CAN-015g … see new §28.1"; `:112` "CAN-015g replay V2 wired" |
| roadmap correction = design note = F-057 History; no link added; last change | diff; design note `:61-80`; ledger `:9191-9196`; `](` in +/- lines; `git log --date=short` | MATCH | #190 → `…-v2` 20:05:12Z, #189 on `main` 19:52:10Z, 3/537 at `4c26919f`, canopy#684 2026-09-24; 1 link before, 1 after (the g-3 row's own); `86f1fd3d 2026-07-04` |
| `_parse_float_rows` `:437-455`; `_resolve_patch_values` `:457-506`, `len(rows) > 1` → `return rows` (`:495`) | fetched at `571743db`; AST-extracted, executed, topology (1, 1, 2) | MATCH | `"1;2;3;4"` → `[[1],[2],[3],[4]]` (4×1); `"1\n2\n3\n4"` → 4×1; `"1,2,3,4"` → `[[1,2],[3,4]]`; `"1,2;3,4"` → 2×2 |
| manual `:266`, `:267-269`, `:285`, `:328`, `:686-687` | fetched | MATCH, span NIT | `:266` env line; `:285` "active in both demo and service modes"; `:328` Phase Duration; the Candidate Epoch Progress condition ends `:688` |
| matrix `:350`, `:807`, `:822-824` | `sed` | MATCH | `FAIL (F-CANOPY-018)`; `FAIL`, no id; PASS / `PASS (name arm; value pending an Apply)` / PASS |
| ledger: Phase 5 Still owed; Phase 11; F-CASCOR-004; F-056 | `:6385-6391`, `:11285-11286`, `:11176`, `:6455`, `:9140`, `:9142` | MATCH | F-039, F-037, F-038, F-036, F-026 only; "are already known to be within reach of the first limb"; "recorded as unsettled"; "FIXED by juniper-cascor#674"; "has not been driven live"; "**Re-rated P1**, on plan §6.3's rule" |
| handoff verification commands at c741351c | all run, read-only | MATCH | 79/56/1/2/20, P1 9, P2 11; `^OPEN   P1 ` 9 (unanchored 10); 'P1 since' 5; Phase 13 `:11843`; design note 2; roadmap 1; compare `behind`; `:510`; `gh pr list` `[]`; lsof none |
| CHANGELOG `#532`; the two leads | fetched | one MISMATCH (F3) | `#532` at `:534,:535,:541` only, in `[0.9.0]` (`:12-1184`); `:1436-1437` in `[0.8.0]` (`:1295`); `:2909` in `[0.6.0]` (`:2171-2918`, § Fixed `:2893`); `[0.5.0]` starts `:2919` |
| triage; five headers unchanged | run; `git diff … \| grep '^[-+]\*\*F-'` | MATCH | 9 P1 = 012, 013, 018, 028, 032, 064, 065, CASCOR-001, -002; 11 P2; 0 header lines |
| record: 24/13/7; lane credits; "Not applied"; dissents | script lists; round-1 file | MATCH | B1 MAJOR, B2+C1, B3, A3+B4, C2, A4+C3, B's O17 leads, B6+B7, A1, A2, B8, B5, B9+C6, C4; F-028 as B wrote it (8/12), A "P1, narrowly"; F-067 as B wrote it (10/10) |
| banner vs Phase 12 handoff item 3; handoff "Changed" vs `git diff ad6013f4 c741351c --name-status`; apply header vs README `:17-31` | read | MATCH | item 3 `:69-73` = sweep + (after the ruling) CHANGELOG/plans + the design note's correction; 6 M + 7 A all listed (`lane13*` covers the round-2 brief); `Retire when:` verbatim, `Related:` a notes/ doc |
| the alternatives in all nine places; the audit's characterization | read; audit §5.2/§11.4 | FALLS | F1, F2 |
| stale-phrase scan ("every form it names", "Phase 9 renumber", "7 and 13", "9/11 or 8/12", "four findings Phase 11", "recorded as such", "decides F-CANOPY-065 alone") | grep over the five docs | one hit (F2) | handoff `:96`; the rest only inside the record's own quotations |
| gates | unittest | pass | 38 tests OK |

**FINDINGS**

1. **MAJOR** — the audit is disposed of on `:112` alone. Text: Summary "the 2026-05-05 audit's per-repo activity table (`…ROADMAP-AUDIT.md:112`)", "the audit is a dated snapshot of commit themes and is left as history", "F-CANOPY-057 only if an audit's activity line is read as a design-plan promise"; "The design note's correction": "Until the owner rules, the first limb reaches F-CANOPY-057 only through that audit line"; the same in F-057's and F-065's Status bullets, "Still owed", the Matrix effect, the handoff (`:40-41`, `:51`, `:87`), the parent's O17; record "Not applied … it is a dated snapshot of commit themes, not a plan". Evidence: the same audit's §5.2 "Critical blind spot — CAN-015g and CAN-015h" (`:122`) says "As of 2026-05-05 both are **shipped end-to-end** on `main`" (`:124`), carries the 8-row table with "g-3 | cascor #190 (retarget of #187) | Sample-boundary weight emission" (`:132`) and "**Status delta**: … code says 'shipped, hardened, integration-tested'" (`:158`); `:215` "CAN-015g/h shipped end-to-end"; and §11.4 "CAN-015g/h shipping verification" (`:318-331`) lists what it confirmed on cascor `main`, "#180 (g-1), #191 (g-6)" (`:323`), never #189 or #190, so the audit's own verification is evidence for the ledger. Lane 13-B cited `:112` only; the record re-derived `:112` and the §5.1 heading. Fix: in the eight places and the record, name §5.2 (`:124`, `:132`) as the audit's shipping claim and §11.4 (`:323`) as its non-confirmation of g-3; re-take "Not applied" on that reading (annotate §5.2's g-3 row as §28.1's was, or state why a status table dated 2026-05-05 is still history); "activity line" → "§5.1 line and §5.2 table". Changes a number, disposition or action? **yes** (the Not-applied action and how O17 is put to the owner); the alternatives 9/11, 8/12, 10/10 and today's counts do not move.

2. **MAJOR** — the withdrawn sentence survives in the handoff. Text (handoff `:96`, item 8): "Then the parent's items 5 and 7, and the owner batch O1–O17 (O17's first limb now decides F-CANOPY-065 alone)." Evidence: this is the sentence round 1's MAJOR found "did not hold" (record `:12082`); the same file says the opposite at `:40-41`, `:44-45` and `:86-87`, and the record claims the alternatives are consistent "in … the handoff" (`:12093`). Fix: "(O17's first limb decides F-CANOPY-065, and F-CANOPY-057 only through the audit: 9/11, 8/12 or 10/10)". Changes a number, disposition or action? **yes** (the reach the successor presents at O17); no triage count.

3. **MINOR** — wrong release for a lead. Text (Still owed `:12195`; record `:12109`): "`[0.5.0]`'s 'one tab-persistence system' (`:2909`)". Evidence: canopy's CHANGELOG at `571743db` has `## [0.6.0] - 2026-07-28` at `:2171` and `## [0.5.0] - 2026-05-23` at `:2919`; `:2909` is `[0.6.0]`'s § Fixed (`:2893`) "#1 TAB-FEEDBACK-LOOP — collapse to one tab-persistence system". Lane 13-B named no release; the pass added one. Fix: `[0.6.0]`. Changes a number, disposition or action? no.

4. **MINOR** — the record misdescribes its own change set. Text (`:12091-12093`): "the ruling's alternatives are 9/11, 8/12 or 10/10 by the broadest reading, in the Summary, 'The design note's correction', the Matrix effect, F-CANOPY-057's and F-CANOPY-065's Status bullets, 'Still owed', the handoff, the parent's O17 and the INDEX". Evidence: the three figures appear in the Summary (`:11896-11897`), the Matrix effect (`:12172-12175`), the handoff's Counts (`:44-45`) and the parent's O17; the other four carry only the reach statement, and the INDEX row carries "9 open P1 / 11 open P2" and no alternative, before or after the pass. The change list also omits four hunks: item 18's new F-067 sentence (`:12196-12198`), the "Sources read" addition with "§5.1" (`:11932-11933`), the FAQ-re-read parenthetical (`:12037-12038`), and the handoff's PR-contents sentence and added roadmap grep (`:55-57`, `:129`). Fix: "the reach statement in all nine, the three figures in four"; add the four. Changes a number, disposition or action? no.

5. **NIT** — the Summary records one dissent, the handoff two. Text (Summary `:11878-11879`): "F-CANOPY-067's rating stays 'P2 pending a live drive', its own condition; … the live drive is all that is left to decide it"; handoff `:41-42`: "One round-1 lane dissents on F-CANOPY-028 (P2) and on F-CANOPY-067 (P1 by source)". Fix: append "one round-1 lane would rate it P1 by source today (Consensus record)". Changes a number, disposition or action? no.

6. **NIT** — citation span. Text ("Reached" `:11922`, F-049 row `:11951`, record `:12101`, `:12128`): "(`:686-687`)". Evidence: the Candidate Epoch Progress condition "shown only while the training state carries `candidate_epoch` and `candidate_total_epochs`" spans `:687-688` (Lane 13-A cited `:686-688`). Fix: `:686-688`. Changes a number, disposition or action? no.

**WHAT YOU COULD NOT CHECK**
- That cascor rejects a (4, 1) body for a (2, 2) target: "cascor rejects the shape, loudly" is inferred from the entry's original 422; cascor's validator was not fetched.
- Nothing live; the owner's merge approval; the lanes' unarchived scratch probes; the GitHub shas and times beyond the compare and the manual (taken as round 1 verified them).
- Whether the audit's §5.2 counts as a "design plan" for the first limb — that is O17; finding 1 stands either way, because the ledger describes the audit.

**SECRETS/PII:** none printed; the diff's two non-hunk `@` are backticked literal `@` in the archived Lane 13-C report and a brief; 0 token prefixes, 0 e-mail shapes; git read-only inside the worktree (`show`, `diff`, `status --short`, `log --format='%h %s'` / `'%h %ad %s' --date=short`); no `.env*` read; no service touched; worktree unchanged (only the untracked round-2 brief).

---
