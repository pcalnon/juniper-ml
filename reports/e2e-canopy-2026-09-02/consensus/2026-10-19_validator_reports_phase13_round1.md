<!-- markdownlint-disable -->

# Phase 13 ledger validation, round 1 — validator reports (verbatim)

Round 1 of the consensus review of the canopy E2E ledger's Phase 13 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen local commit 566cb72a (the Phase 13 draft, juniper-ml worktree federated-stargazing-blanket, branch docs/canopy-e2e-phase13, base main ad6013f4). Three lanes, briefed separately with different entry points (reports/e2e-canopy-2026-09-02/drafts/lane13{A,B,C}_phase13_ledger_brief.md): Lane 13-A rated the twenty open findings from canopy's manual first and re-derived every fact; Lane 13-B was adversarial on the five re-ratings, the ten not reached, the owner's question, the counts and item 30; Lane 13-C replayed the apply pass and checked the seven files against each other, the ledger, the repo's tests and GitHub. Each report is the lane's final message, archived verbatim; the orchestrator's dispositions are in the ledger's Phase 13 consensus record.

## Lane 13-A (manual-first re-derivation)

*agent `a8568dff172fd4240` · round 1 · last-assistant-text (not resumed) · 9881 chars*

**Lane 13-A** (manual-first re-derivation, round 1)
**VERDICT: SOUND-WITH-FIXES** — all 20 of my manual-first ratings match the phase's, and every manual, GitHub, source, triage, matrix and ledger fact re-derived holds. The fixes are three citation/wording NITs and one MINOR evidence gap (the F-CANOPY-049 row); none changes a number, disposition or action.

Method: manual fetched at `571743db` (1,606 lines; `cmp` IDENTICAL to the local canopy checkout's copy); the 20 entries read from the ledger at `main` `ad6013f4` via `git show`, so the phase's re-ratings could not leak; answers written to `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/438B5B69-ACCF-4C62-BE45-EEFFF048856D/scratchpad/lane13A/step1_answers.md` before Phase 13 was opened; own 50-term case-insensitive scan (`term_scan.py` there) and own header-rule script (`header_tail_check.py`).

**YOUR 20 ANSWERS** (finding | manual line(s) | reached? | mine | ledger's | agree?)

- F-CANOPY-001 | none (dark/theme/glyph 0 hits) | no | P2 | P2 | yes
- F-CANOPY-012 | 493-501 (`output_weights` listed; "comma-, semicolon-, or newline-separated floats") | yes | P1 | P1 | yes
- F-CANOPY-013 | 510 (step 6, confirm the edit from the status alert) | yes | P1 | P1 | yes
- F-CANOPY-018 | 267-268 ("enables only when a value differs from the last applied set") | yes | P1 | P1 | yes (cite NIT, F1)
- F-CANOPY-028 | 754-755 ("survives a reload") | yes, narrowly: it survives the reload, the next pin destroys it | P1 | P1 | yes
- F-CANOPY-032 | 732 ("when the upstream call fails") | yes | P1 | P1 | yes
- F-CANOPY-033 | none | no | P2 | P2 | yes
- F-CANOPY-034 | none ("network stats" 0) | no | P2 | P2 | yes
- F-CANOPY-049 | 155-171, 173-176 describe canopy's own dots and the browser socket; "relay" 0; but see F3 (328, 686-688) | no | P2 | P2 | yes
- F-CANOPY-051 | none ("active tab" 0; "persist" only Cassandra) | no | P2 | P2 | yes
- F-CANOPY-057 | 714-715, 820-821 state the absence | no | P2 | P2 | yes
- F-CANOPY-060 | none (shortfall/truncat 0; 225-244 is start-fresh) | no | P2 | P2 | yes
- F-CANOPY-063 | 225-244 name the two controls, silent on the tail | no | P2 | P2 | yes
- F-CANOPY-064 | 311, 316, 338 | yes | P1 | P1 | yes
- F-CANOPY-065 | 267-269 promise no toast content (toast/declin 0) | no | P2 by the manual alone; P1 only via the first limb | unchanged, first limb | yes
- F-CANOPY-066 | 121; 298-300 hide five tabs, silent on the sidebar panel | no | P2 | P2 | yes
- F-CANOPY-067 | 311/316 generic; "initial_metrics" 0; not observed live | not specifically | P2 pending a live drive | unchanged | yes
- F-CASCOR-001 | none ("stall" hits are only "install") | no | P1 (own merits) | P1 | yes
- F-CASCOR-002 | 777-780, nothing on optimizer state (491 is the editor's remove-unit) | no | P1 (own merits) | P1 | yes
- F-ML-002 | none | no | P2 | P2 | yes

My P1 set equals the ledger's nine. Term scan: no hit bearing on an open finding that the phase does not account for; the hits it does not list are inert ("skipped" :710 evolution grid; "applied" :235/:240 start-fresh modal; "optimizer" :491 remove-unit; "capped" :652/:692; "iteration" :329-330 progress bars; "learning rate" :262-:346 sidebar/card).

**TABLE** (claim | re-derived | result | evidence)

| claim | re-derived | result | evidence |
|---|---|---|---|
| Manual quotes at :493-501, :510, :754-755, :732, :311/:316/:338, :820-822, :714-715, :155-171, :173-176, :1144, :225-244, :121, :777 | each read at `571743db` | MATCH | fetched file |
| :266-268 (F-018), :266-269 (F-065) | sentence spans 267-268(-269); 266 is the `__DEFAULT` env line | holds (NIT F1) | manual :266-269 |
| same words at `28da69f8^` :407-415, :424 | parent 58d72c12 fetched; identical | MATCH | `commits/28da69f8` parents |
| `571743db` = main head, 2026-10-17T23:01:09Z, after v0.9.0 | main sha 571743db…, v0.9.0 published 2026-10-17T19:45:37Z | MATCH | gh api |
| PRs 532/533/535: `359e1bf7` 04:16:14Z, `6b55399d` 05:09:29Z, `28da69f8` 04:54:55Z; titles name F-001/-013/-015/-034, F-018/-028 + F-032 pin, F-012 | same | MATCH | `gh pr view` |
| each an ancestor of v0.7.0 | `behind`, 0 ahead (63/60/61 behind) | MATCH | compare |
| v0.7.0 published 2026-09-09T07:15:13Z | same; tag `d8b1592d` | MATCH | releases API |
| CHANGELOG: no `#533`/`#535`; `#532` only :534-541 under `[0.9.0]` (:12) for F-CANOPY-059; none of F-001/-012/-013/-018/-028/-034; toast :2360-2365 under `[0.6.0]` (:2171); `[0.7.0]` :1700; 5,887 lines | same | MATCH | grep/sed |
| `_resolve_patch_values` :457-507, rows and flat idioms | def :457, last return :507 | MATCH | sed |
| `_envelope_payload` :563-585; calls :731, :828 | same | MATCH | sed |
| `_to_dashboard_metric` :1960-1991, no `weights`, no `kind` | same | MATCH | sed+grep |
| cascor main `4c26919f` 2026-10-16T09:33:36Z | same | MATCH | commits/main |
| `_emit_frame` :1260-1297, keys epoch/loss/accuracy/validation_loss/validation_accuracy/phase/replay/snapshot_id, no `weights`; `weights_at` :1244 sole occurrence | same | MATCH | sed+grep |
| cascor 187→`feature/can-015g-2-replay-weight-cache` 07:31:04Z `d85c9ddd`; 189→main 19:52:10Z `b1d19948`; 190→`…-v2` 20:05:12Z `dbc25277` | same | MATCH | `gh pr view` |
| `main...dbc25277` diverged 3/537 | same | MATCH | compare |
| triage 79/56/1/2/20; 9 P1 = 012, 013, 018, 028, 032, 064, 065, CASCOR-001, -002; 11 P2 | same | MATCH | triage run |
| five headers: first token P1, no FIXED/HEALED/ACCEPTED/WITHDRAWN in last 170 chars | same (057 P2, 065 P1) | MATCH | own script |
| matrix: C2.9-05 FAIL (F-018); M-WORKERS-02 FAIL; M-NE-09/-13 PASS/FAIL(F-013); M-NE-17 PASS(2 of 4)/FAIL(F-012); M-PARAMETERS-04/-06 PASS, -05 PASS (name arm; value pending an Apply); C2.1-01 PASS, C2.1-02 PASS(stated expectation); M-METRICS-03 FAIL FA-3 = F-026's row, entry FIXED | same | holds (NIT F2) | matrix :198-199, :350, :420, :807, :822-824, :895-903 |
| Phase 4 "Still owed (unchanged, plus)" rows; disposition table; F-032 NOT fixed | main :6211-6215, :6164-6178 | MATCH | ledger |
| F-032 two-arm correction; segment 12 "Apply stays enabled … until a page reload"; segment 7 "Removed unit 9 (now None hidden units)" | main :3128-3131, :4876, :4086 | MATCH | ledger |
| Phase 11: 057/018/012 in reach, 013 unsettled; Phase 12 names four; item 26 "stays, unchanged" | main :11198-11221, :11699-11700, :11728 | MATCH | ledger |
| no numbered Still-owed since Phase 9 carries the rows | no row id after main :6214; Phase 5 already omitted them | holds (NIT F4) | grep |
| F-064 cites :266/:271/:293, moved not changed | main :10092-10093 vs :311/:316/:338 | MATCH | ledger |
| plan §6.3 :357-360 | "P1 (breaks a documented behaviour)" at :359-360 | MATCH | plan |
| design-note correction's facts | match rows above | MATCH | `git diff` |

**FINDINGS**

1. **NIT** — citation start line. Ledger: "(`:266-268`)" (sweep table F-018 row; F-018 blockquote) and "(`:266-269`)" (F-065 row; F-065 status bullet). Evidence: line 266 is `JUNIPER_CANOPY_TRAINING__LEARNING_RATE__DEFAULT / …HIDDEN_UNITS__DEFAULT`; "Edits are staged until you click **Apply** — the button" is :267, "enables only when a value differs…" :268. Fix: `:267-268` / `:267-269`. Changes a number, disposition or action? no.
2. **NIT** — Matrix effect wording. Ledger: "M-PARAMETERS-04/-05/-06, read PASS with the pin value 'pending an Apply'" and "rows whose FAIL halves carry the five re-rated findings … M-WORKERS-02 (F-CANOPY-032)". Evidence: only -05 carries "(name arm; value pending an Apply)", -04/-06 are plain PASS; M-WORKERS-02 and C2.9-05 are whole-row FAILs, and M-WORKERS-02's row names no finding id (the F-032 entry names the row). Fix: say "-05's value pending an Apply" and "rows whose FAIL (or FAIL half) rests on". Changes? no.
3. **MINOR** — F-049 row incomplete. Ledger: "None describes the canopy-to-cascor relay or `/api/state`'s freshness". Evidence: the manual does describe two surfaces fed by the fields the entry measured frozen through a live candidate phase (`phase_started_at: ""`, `candidate_pool_status: Inactive`): `:328` "Phase Duration — shows elapsed time from `phase_started_at` during active phases" and `:686-688` "Phase (`Idle` until a pool is active)" / Candidate Epoch Progress "shown only while the training state carries …". I keep P2: the entry measured no page surface, the manual conditions both on the state carrying the fields, and the staleness originates in the F-CASCOR-004 drop (F-049 is the non-recovery). Fix: cite and dispose of `:328` and `:686-688` in the row and the "Reached" paragraph, so the counter-reading is on record as F-028's is. Changes? no (a lane that reads it otherwise would make the counts 10 and 10).
4. **NIT** — history wording. Ledger (Summary): the re-drive "fell out of the numbered list when Phase 9 renumbered it". Evidence: the first Still owed after Phase 4 (Phase 5, prose, main :6318-6324) already omitted the rows (only F-026's confirmation survived, F-015's later), and no list from Phase 5 on names them; item 30's "carried by no numbered item since Phase 9" is literally true. Fix: "carried by no Still-owed list since Phase 4". Changes? no.

**WHAT YOU COULD NOT CHECK**
Nothing live (no service on this host). The handoff, INDEX and apply-script changes in the same commit lie outside steps 1-3 and were not reviewed. "The owner granted merge approval" is not checkable from artifacts. Where `/api/state`'s `candidate_pool_status` / `phase_started_at` come from (relay frames vs REST) was not traced; F3 rests on the entry's own measurement. `weights_at` "called only by its unit tests": only `manager.py` was checked, not cascor's tests.

**SECRETS/PII:** none printed; no `.env*` read; git used read-only (`show`, `diff`, `status --short`, `log --format='%h %s'`) inside the worktree only; `gh` read-only; no tracked file modified (`git status` shows only the three untracked lane briefs).

---

## Lane 13-B (adversarial on the re-ratings)

*agent `af16ea58d053ee6f5` · round 1 · last-assistant-text (not resumed) · 10492 chars*

I have everything needed; no further checks required. Composing the report now.

**Lane 13-B** (adversarial on the re-ratings, round 1)
**VERDICT: SOUND-WITH-FIXES**

**TABLE**

| claim | attack | result | evidence |
|---|---|---|---|
| F-012 P1: "no entry for the listed group could pass" | manual `:493-501` lists `output_weights` + delimiter forms; "lets CasCor validate the exact target shape" read as documenting the rejection | STANDS (second counter-reading, see DISSENT) | manual 571743db `:495,:500,:501`; same words at #535's parent `58d72c12:407-415`; F-012 entry: flat parse, no reshape |
| F-013 P1: step 6 "confirm the edit" vs `index None` | step 6 names only a surface? | STANDS | manual `:510`; entry: success path misreported at both call sites; Phase 11 `:11213` |
| F-018 P1: Apply "enables only when a value differs" | was "Apply stayed enabled" measured or inferred? | STANDS | segment 12 ledger `:4939`: "Apply stays enabled and the status stays ⚠️ Unsaved changes until a page reload"; manual `:267-268` |
| F-028 P1 ("narrowest") | the sentence promises reload survival, which held | DISSENT (I rate P2) | manual `:754-755`; entry: store and card survived; writer discarded on next pin |
| F-032 P1 with no fix in code; re-drive first? | rating before re-drive breaks practice? | STANDS | F-056 was P1 "by source… not driven live"; cascor-down arm's API carried `error` |
| "Not reached" ×10 | each tried from the manual + term scan | STANDS ×8; F-049 MINOR (#4); F-067 DISSENT | scan 0 hits for dark/theme/truncat/shortfall/symbol/active tab/RESET/relay/reconnect/503; `:298-300` names tabs only (F-066) |
| F-064 "lines moved, not changed" | compared both commits | STANDS | `1b2dd438:266/271/293` == `571743db:311/316/338`, verbatim |
| First limb "now decides F-CANOPY-065 alone" | other plans recording g-3 as shipped | FALLS (#1) | V7 roadmap §28.1 `:15146-15160`; ROADMAP-AUDIT `:112` |
| FAQ no longer promises the stream | read FAQ at 571743db | STANDS | status note 2026-09-24 "describe the design, not what runs today" |
| Counts 79/56/1/2/20, 9/11; alternatives | triage + by hand | STANDS (ranges incomplete, #1) | triage output; 20−9=11; F-028 reading → 8/12 |
| "every release from 0.7.0 carries the fixes" | compare API | STANDS | #532/#533/#535 behind v0.7.0 (0 ahead); v0.8.0/0.8.1/0.9.0 ahead of v0.7.0, 0 behind; v0.6.0 lacks #535; no tag between |
| CHANGELOG "names none of the three PRs… its one `#532`" | grep | NIT (#8) | `#532` at `:534,:535,:541` (one F-059 entry) |
| API facts (dates, shas, bases, 3/537) | re-derived with `gh api` | STANDS | all exact: 571743db 2026-10-17T23:01:09Z = main head; cascor#190 base `…-v2`, 20:05:12Z; #189 main 19:52:10Z; 4c26919f main head; diverged 3/537 |
| Host copy "byte-identical" | `cmp` | STANDS | exit 0 |
| Item 30 legs, M-METRICS-03, rows uncarried | matrix + ledger grep | STANDS (one arm missing, #3; pins assumption, #7) | matrix `:420` FAIL; `:895/:899/:903` demo 501; manual `:285`, `:515`; no row id named in ledger `:6310-11834` |
| Handoff verification commands | ran all but none touch a service | FALLS one (#2) | `--open-only \| grep -c 'P1 '` prints 10 |
| SUPERSEDED banner; parent item 4/O17; INDEX row | compared | STANDS, NIT (#9) | Phase 12 handoff `:69-73` item 3 has two halves |

**FINDINGS**

1. **MAJOR** — "The first limb now decides F-CANOPY-065 alone" (Summary; Matrix effect; parent O17; INDEX) and "9 and 11 … or 8 and 12". Evidence: `notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md:15146-15160` is headed "CAN-015g + CAN-015h — Phase 6E deferred, shipped end-to-end" and its g-3 row reads "cascor #190 (retarget of #187) | Sample-boundary weight emission | `dbc25277`"; `:5196` "CAN-015 ✅ Shipped end-to-end"; `notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md:112` "CAN-015g replay V2 wired". Phase 11 placed F-057 within the first limb because a plan "records every CAN-015g item as merged to main"; the phase corrected one such plan and left two. Correcting the design note was legitimate (item 26 required it; the fact is API-verified) but it settles nothing while another plan records the same. Fix: add the same dated correction to §28.1 (and the audit, or note it as a dated snapshot), or state the ruling range as "9/11, 8/12, or 10/10 if a design-plan promise counts and the V7 roadmap's §28.1 is read as one"; item 26's second step names both files. Changes a number, disposition or action? **yes** (the ruling's alternative counts; item 26's scope) — today's triage counts do not move.

2. **MINOR** — handoff: "`python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c 'P1 '   # 9`". Evidence: prints **10**; the tenth match is the summary line `open P1      : 9`. Fix: `grep -c '^OPEN   P1 '` (prints 9) or expect 10. Changes…? **yes** (a successor chases a phantom P1).

3. **MINOR** — F-012 blockquote / "The five re-ratings": "A note, not a finding: the manual's Patch Weights text does not describe the row idiom #535 added; every form it names still parses." Evidence: `_parse_float_rows` (`network_editor_panel.py:437-456` at 571743db) makes newlines and semicolons row separators, so the manual's "semicolon- or newline-separated floats" for `output_weights` — 24 values — becomes 24 rows of width 1 (`:490-494` accepts equal widths) and is sent as `(24, 1)`; only the comma form reaches the reshape. Two of the three documented forms now mis-shape on the wire. Fix: say so in the note; add a semicolon-separated flat list to item 30's F-012 arms; the manual sentence needs the row idiom. Changes…? **yes** (item 30's drive; a manual correction owed).

4. **MINOR** — F-049 row: sections read were Status Indicators, Update Intervals, Troubleshooting 1/5, WebSocket; "None describes the canopy-to-cascor relay or `/api/state`'s freshness". Evidence: the entry's own measured consequences are `/api/state` holding `candidate_pool_status: Inactive` and `phase_started_at: ""` "through a live candidate phase"; the manual documents both: `:328` "**Phase Duration** — Shows elapsed time from `phase_started_at` during active phases" and `:686` "**Pool Status Badge**, **Phase** (`Idle` until a pool is active)". The instrument's definition is about behaviour, not component; the sweep should name these sentences and say why they do not reach (the drop that triggered it, F-CASCOR-004, is FIXED; a close frame is noticed). Fix: add that line to the row. Changes…? **no** (I accept P2 on the trigger's being fixed).

5. **NIT** — F-032 blockquote: "absent for 60 s under each of two inductions while canopy's own API reported the error" — the next sentence says the control-WS arm's route returned no `error` key. Fix: "under the cascor-down induction, while …". Changes…? no.

6. **NIT** — F-018 / item 30: C2.9-05's matrix expectation (`:350`) is the toast text; "Apply disabled and `params-status` clean" is a new arm. Fix: record it as an added expectation so the row's result and the P1 behaviour are scored separately. Changes…? no.

7. **NIT** — item 30 / F-018 blockquote: "the manual says they work in both modes". Manual `:285` sits under Configuration Parameters (sidebar controls), not the Parameters tab's pin checkboxes; for F-028 the demo-leg expectation is source-based. Fix: "for the Apply controls; the pins by source". Changes…? no.

8. **NIT** — "canopy's CHANGELOG at 571743db names none of the three PRs … (its one `#532` …)" and handoff trap "no entry names them". Evidence: `#532` at `:534,:535,:541`. Fix: "names none as a fix entry; canopy#532 appears three times in the 0.9.0 F-059 entry". Changes…? no.

9. **NIT** — SUPERSEDED banner: "item 3 (item 26's first step …) … done". Phase 12 handoff `:69-73` item 3 also carries the CHANGELOG/design-plan step, which the new handoff's item 4 still owes. Fix: "item 3's first half". Changes…? no.

10. **NIT** — handoff "Created: … `consensus/2026-10-19_validator_reports_phase13_round*.md`; `…ledger_round*_corrections.py`" — none exists at the freeze (0 files). Expected once rounds run; mark as pending. Changes…? no.

**DISSENT**

- **F-028**: I would rate P2. The sentence promises survival of a reload; the store, the card and `localStorage` survived (entry); the discard is a writer defect no sentence describes. The ledger's own precedent reads the manual literally (F-057 went P2 the moment the manual said "none reaches the page"). Counts 8/12; with #1, 8/12 or 9/11. The phase's "user following the manual" reading is defensible, so dissent, not a finding.
- **F-012** is a second re-rating with a counter-reading: the manual's forms are 1-D and it says CasCor validates the shape, so a rejection on shape is arguably the documented outcome. Weaker than F-028's (the group is listed as patchable), so I keep P1, but "F-CANOPY-028 is the one re-rating a different reading of the manual would reverse" overstates.
- **F-067**: "unchanged" applies a stricter standard than F-056's. The entry's header says "by source the zeros can persist, which would make it P1"; F-056 was rated P1 on source and a hand-built probe, "not driven live"; the plots F-067 corrupts are documented (`:315-316`, `:338`). By the ledger's precedent F-067 is P1 by source today (10/10), the live drive deciding the disposition, not the rating. Phase 10 set the condition; Phase 13 chose not to re-open it, so dissent.
- **O17 via the CHANGELOG** (not swept, by design): candidates the ruling could reach — F-060 (`CHANGELOG.md:1436-1437`, 0.8.0: "the producer's own sentence — which symbols, how many rows — survives to the modal"; F-060 is exactly that sentence cut); F-051 (`:2909`, "one tab-persistence system", weaker); F-001's dark-mode entries (`:4226`, `:4680`) do not mention the glyph.

**WHAT YOU COULD NOT CHECK**

- Nothing live: whether the four fixes work on a page, whether F-032's alert renders on 0.9.0, or that a demo leg reaches the pins.
- Merge approval "granted in the session that wrote it" and `gh pr list … docs/canopy-e2e-phase13` (returns `[]` — no PR at the freeze).
- The apply script's `--check` mode (not run; not shown to be read-only) and the auto-memory edits (outside the repo).
- That the V7 roadmap counts as a "design plan" for the owner's first limb — that is O17 itself; #1 stands either way because the phase asserts the answer.

**SECRETS/PII:** none read or printed; no `.env*` opened; git used read-only inside the worktree with `--format='%h %s'`; no service started or reached.

---

## Lane 13-C (cross-file consistency)

*agent `adfb235ce7e6f1f95` · round 1 · last-assistant-text (not resumed) · 12405 chars*

**Lane 13-C** (cross-file consistency, round 1)
**VERDICT: SOUND-WITH-FIXES**

**REPLAY** — pre-images of the five tracked files copied from `ad6013f4` into scratch under their relative paths; `python3 -B util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py --root <copy>` printed "5 headers, 7 inserts, Phase 13 appended; 968917 -> 1001017 chars … written", exit 0; each result `cmp`'d against `git show 566cb72a:<path>`:
- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: byte-identical
- `notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`: byte-identical
- `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md` (written by the script): byte-identical
- `HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md`: byte-identical
- `HANDOFF_2026-10-03_canopy-consolidated.md`: byte-identical
- `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: byte-identical
- No hand edit anywhere. `--check` against the worktree: "the ledger already has a Phase 13: nothing to do", exit 1; `git status` unchanged (only the three untracked lane briefs). HEAD = `566cb72a`, unsigned (`%G?` = N), as the handoff's Git state says.

**TABLE**

| check | result | evidence |
|---|---|---|
| 20 open ids vs triage `--open-only` | match | the same 20 ids; the sweep table has 20 rows |
| 79/56/1/2/20, 9 P1, 11 P2 | match | triage summary; Phase 13 Summary + Matrix effect, handoff, parent item 4, O17, INDEX all 9/11 (8/12 by ruling) |
| nine P1 ids | match | triage P1 rows = 012, 013, 018, 028, 032, 064, 065, CASCOR-001, -002 |
| five headers vs triage rules | pass | first token P1 in all five (`e2e_finding_triage.py:39`); no FIXED/HEALED/ACCEPTED/WITHDRAWN in the last 170 chars (`:58-76`); `check_headers()` asserts both; triage prints OPEN P1 |
| RE-RATED quotes vs entries | match | F-012 `expects (12, 2), got (24,)` (ledger 3875, segment 7 4161), "loud, precise, and non-mutating"; F-013 `Appended unit at index None…` (3909), segment 7 `Removed unit 9 (now None…)` (4149), "Cosmetic only"; F-018 toast ~900 ms then `⚠️ Unsaved changes`, never clean until reload (4935-4939), `demo_mode:false` = service mode (4840); F-028 store survives, first pin drops (3080); F-032 60 s × two inductions, API carries `error` (3136), segment 16's `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` induction (5402) |
| vs Phase 4 | match | table 6228-6240 (#532 F-013; #533 F-018 "3 keys", F-028 "the writer"; #535 F-012; F-032 NOT fixed, pins only); "not reproduced from source" (3104); "four contract tests", traced "end to end" (3146-3152); owed rows 6276-6278 |
| F-057 bullet vs History / Status 10-04 | match | History 9185-9191: #187 07:31:04Z `d85c9ddd` → `…-cache`; #190 20:05:12Z `dbc25277` → `…-v2`, 13 min after #189 `b1d19948` 19:52:10Z; 3 ahead / 512 behind at `0e016a7c`; Status 10-04's `:764-766` text now at `:820-822` (verified) |
| F-065 bullet vs Severity | consistent | Severity 10222-10232: "No manual or REFERENCE text makes this promise"; manual `:266-269` says nothing of the toast (verified) |
| Still owed vs Phase 12 | ok | Phase 12: "items 0 to 26" + new 27-29 → "0 to 29"; no `30.` before Phase 13; item 18 (10615, F-064/F-067) and 20 (10640, F-065) as cited |
| Phase 4 rows in earlier numbered items | none | `C2.9-05`, `M-PARAMETERS-04`, `M-WORKERS-02`, `M-NETWORK-EDITOR-17` occur only in segments 11-16, Phase 4's prose (6277) and Phase 13; no list from Phase 5 to 12 names them — but see F3 |
| Phase 11's "four within reach" | partly wrong | Phase 11 (11277-11292) names three: 057, 018, 012; F-013 "recorded as unsettled" (11168) — F2 |
| matrix rows | match | C2.9-05 `FAIL (F-CANOPY-018)` (:350); M-WORKERS-02 `FAIL` (:807, names no finding; the F-032 entry names the row); M-NETWORK-EDITOR-09/-13 `FAIL(status message -- F-CANOPY-013)`, -17 `FAIL(default target -- F-CANOPY-012)`; M-PARAMETERS-04/-06 PASS, -05 "PASS (name arm; value pending an Apply)"; C2.1-02 names F-CANOPY-001; M-METRICS-03 = `metrics-panel-phase-duration`, FA-3, FAIL, and F-CANOPY-026 (ledger 310) is the phase-duration UTC finding, FIXED |
| handoff vs diff | match (forward-looking) | "Modified" = exactly the five modified files; "Created" also names briefs, consensus reports and round scripts not in the diff — F5 |
| banner vs Phase 12 handoff | match | its items 1-7 (:60-84): 1 = the PR (#2263 merged 2026-10-19T08:49:20Z per GitHub), 3 = item 26; 2, 4, 5, 6, 7 carry as the new handoff's 3, 5, 6, 7, 8 — F6 |
| parent item 4 / O17 / INDEX vs Phase 13 | match | same counts, item 30, "9/11 or 8/12" |
| design note vs F-057 History vs Phase 13 §correction | match | same shas, times, bases, 3/537 at `4c26919f`; `grep -c 'Correction 2026-10-19'` = 2; `](` in changed lines 2 before / 2 after (no link added) |
| gates | pass | 38 tests OK (the four suites); filename matches `_CANONICAL_NAME` (`tests/test_thread_handoff_archive.py:28`); no `HANDOFF_*.md` name in Phase 13 or the design-note diff; `notes/`, `prompts/` excluded by markdownlint (`.pre-commit-config.yaml:240`); flake8 with the hook's own args clean (E501 ignored; `util/` outside its `^(scripts\|tests)/` scope; line 531 is 528 chars) |
| ad-hoc header | drift with precedent | `#` block, no `Retire when:` / `Related:` (README :17-31); same form as `2026-10-19_phase12_ledger_round1_corrections.py` — F4 |
| GitHub | all match | #532 2026-08-28T04:16:14Z `359e1bf7`; #535 04:54:55Z `28da69f8`; #533 05:09:29Z `6b55399d` (titles name the findings; #533: "F-CANOPY-018 / -028, and an F-CANOPY-032 contract pin"); compare v0.7.0…each = behind, 0 ahead; v0.7.0 published 2026-09-09T07:15:13Z; v0.9.0 2026-10-17T19:45:37Z; canopy `main` = `571743db` 2026-10-17T23:01:09Z, still head; cascor #187 base `…-cache` 07:31:04Z `d85c9ddd`, #189 base `main` 19:52:10Z `b1d19948`, #190 base `…-v2` 20:05:12Z `dbc25277`; `main...dbc25277` diverged 3/537; cascor `main` `4c26919f` 2026-10-16T09:33:36Z; #684 2026-09-24T11:10:28Z `f2147403`; #731 2026-10-09; `gh pr list --head docs/canopy-e2e-phase13` = [] |
| cited lines at `571743db` | match | manual 1,606 lines: `:493-501`, `:510`, `:266-268`, `:754-755`, `:732`, `:311/316/338`, `:820-822`, `:714-715`, `:121`, `:777`, `:1144`, `:155`, `:173`, `:225`; `28da69f8^` = `58d72c12`: `:407-415`, `:424` same words; CHANGELOG 5,887 lines, `#532` only at 534-541 (the [0.9.0] F-059 entry), no `#533`/`#535`/F-012/-013/-018/-028/-032, toast text at 2360-2365 inside [0.6.0] (2171-2918); `_resolve_patch_values` :457, `_envelope_payload` :563, calls :731/:828; `_to_dashboard_metric` :1960; cascor `weights_at` :1244 (sole occurrence), `_emit_frame` :1260 with no `weights` in its body; the local canopy checkout's manual is byte-identical to `571743db` |
| handoff verification commands | 9 of 10 as commented | all as the comments say except `grep -c 'P1 '` → 10 (F1); `gh pr list` → [] (no comment given); lsof: nothing on 8101/8202/8051-8053 |

**FINDINGS**

1. **MINOR** — a verification command's expected value is wrong. Text (handoff, Verification commands): "`python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c 'P1 '   # 9`". Evidence: it prints **10**; the summary line "`      open P1      : 9`" also matches `P1 `. Fix: `grep -c '^OPEN   P1 '` (prints 9), or drop the line (the `tail -7` line already shows "open P1 : 9"). Changes a number, disposition or action? no.

2. **MINOR** — "the four findings Phase 11 placed within the first limb's reach" is not what Phase 11 says, and the set shifts inside Phase 13. Text: Summary "Of the four findings Phase 11 placed within the first limb's reach, three (F-CANOPY-012, -013, -018) … the fourth (F-CANOPY-057)"; Still owed "of the four findings Phase 11 named, F-CANOPY-065 is the only one the ruling can still move"; handoff item 4 "Only F-CANOPY-065's rating can still move among the four Phase 11 named". Evidence: Phase 11 (ledger 11277-11292) says "three open P2s are already known to be within reach of the first limb" — 057, 018, 012 — and records F-CANOPY-013 "as unsettled" (11168; its Matrix bullet names step 6, 11218). The Summary's four exclude 065, so "of the four … 065 is the only one" cannot be read against that set; the four-with-013 reading comes from Phase 12's Counts bullet (11776), not Phase 11. Fix: Summary: "Of the three findings Phase 11 placed within the first limb's reach (F-CANOPY-057, -018, -012) and F-CANOPY-013, which it left unsettled, three are P1 by the manual…"; Still owed and handoff item 4: "of the findings Phase 11 named (F-CANOPY-065 and the three within the first limb's reach), F-CANOPY-065 is the only one…". Changes a number, disposition or action? no.

3. **MINOR** — the re-drive did not fall out at Phase 9. Text (Summary): "that re-drive fell out of the numbered list when Phase 9 renumbered it"; item 30: "carried by no numbered item since Phase 9 renumbered the list". Evidence: Phase 4's "Still owed (unchanged, plus)" (6274-6278) is prose; Phase 5's list the same day (6381-6386) carries only F-039, F-037's topology re-drive, F-038, F-036 and F-026; nothing from Phase 5 to Phase 8 (6310-8565) mentions the wave, the eight fixes, #532/#533/#535 (only the F-037 A/B note, 6340) or the row ids; Phase 9 renumbered "Phase 8's list" (9762), which never carried it. Fix: "that re-drive was last listed in Phase 4's prose and has been carried by no numbered item since Phase 5's list (2026-08-28)"; item 30 likewise. Changes a number, disposition or action? no (item 30 restores it either way; "owed since 2026-08-28" stands).

4. **NIT** — ad-hoc header convention. Text: `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py:1-10`, a `#` block with "Status : ad-hoc — one-off apply pass; RETAINED as provenance". Evidence: `util/ad-hoc/README.md:17-31` asks for a docstring header with `Retire when:` and `Related:`; the block form has precedent in `2026-10-19_phase12_ledger_round1_corrections.py`. Fix: add `Retire when: RETAINED — …` and `Related: ledger Phase 13; HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`. Changes a number, disposition or action? no.

5. **NIT** — the handoff describes the landed state, not the freeze. Text: "**Written**: … as its PR was opened"; "landed from turing through the API as signed commits"; Created: "`reports/…/consensus/2026-10-19_validator_reports_phase13_round*.md`; `util/ad-hoc/2026-10-19_phase13_ledger_round*_corrections.py`". Evidence: `gh pr list --head docs/canopy-e2e-phase13` = []; `566cb72a` is unsigned; the consensus files do not exist yet and the three briefs are untracked. Fix: none if these are true when it lands; re-read Git state and Created at landing. Changes a number, disposition or action? no.

6. **NIT** — documents referenced by role without filename, and one carry-over unstated. Text: handoff "under plan §6.3's rule", item 2 "still FAIL in the matrix"; banner "recorded as the ledger's Phase 13"; banner "items 2, 4, 5, 6 and 7 carry there" while item 3's second step (CHANGELOG + design plans after the ruling) also carries (handoff item 4). Fix: name `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`, `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` and the ledger once each; banner: "item 3's first step … is done; its second step and items 2, 4, 5, 6 and 7 carry there". Changes a number, disposition or action? no.

7. **NIT** — the five headers name a second severity in prose ("P1 since 2026-10-19 …; P2 before that"); `util/ad-hoc/README.md:139` says not to, but the triage takes the first token and F-CANOPY-057's header (9158) set the precedent. Fix: none required; keep `P1` first. Changes a number, disposition or action? no.

**WHAT YOU COULD NOT CHECK**
- The owner's merge approval ("granted in this session"), the turing link figures (0% loss, 12.6 Mbps), and the auto-memory edits.
- Whether the four fixes work on a live page (the phase says so itself); `--check` was run only against this worktree; no service was touched.
- The manual's "term scan" was not repeated; the section readings for the ten "not reached" findings were spot-checked at the cited lines only.
- `28da69f8^` was resolved through the API (`58d72c12`, the squash parent), not locally.

**SECRETS/PII:** none in the diff — the 23 `@` hits are hunk headers; no token prefixes, no `NAME=value`, no e-mail address; nothing printed.

---
