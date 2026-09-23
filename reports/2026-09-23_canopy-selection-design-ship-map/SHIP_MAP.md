# Selection-reachability design: ship map and stale claims (2026-09-23)

**Project**: Juniper · **Sub-Project**: juniper-ml (evidence) · **Application**: canopy selection-reachability arc ·
**Author**: Paul Calnon · **License**: MIT License

This is a read-only research agent's report, **archived verbatim**. The agent mapped every §4.x,
§5 guardrail and §7 row of `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`
to the juniper-canopy PR that shipped it, verified in source on canopy `origin/main` (`2f973ca2`,
then `7950bf9e`). It also listed every line of that design that `main` contradicts. It is the input
for reconciling the design document. **Applied to the design on 2026-09-23** (see the second set of
archivist's notes at the end, which also records where this report turned out wrong).

Line numbers are as the agent read them, in the design at juniper-ml `91da4b0e` and in canopy at
`7950bf9e`. Both drift, so locate by symbol. The mutants (M1–M20) ran on `git archive` copies
extracted to the session scratchpad; their logs were not retained.

---

**Scope.** canopy `origin/main` was at `2f973ca2` when I started and at `7950bf9e` when I finished. **#665 merged at 2026-09-23T06:17:13Z (`7950bf9e`) while I was working.** It was on your list of open PRs and it closes G11, so I count it as shipped and flag it. The files I cite for §4.x (`src/frontend/dashboard_manager.py`, `src/main.py`, `src/demo_mode.py`, `src/backend/recurrence_backend.py`, `src/frontend/components/connection_indicator.py`) are identical at both tips, and line numbers are as of `7950bf9e`. Merge times are UTC, from `gh`.

**How I tested "would it fail".** I ran the tests on `git archive` copies extracted to the scratchpad, using JuniperCanopy1. There was no checkout, and the canopy tree was not touched. The unmodified baseline passed 189 test items in 4 modules at `2f973ca2`, and 303 in 5 modules at `7950bf9e`. I then made 16 mutants (M1–M20; M2, M8, M12, M13 and M15 were planned and not run), each breaking one behaviour on a fresh copy. A "catch" means the suite went red.

## 1. Ship map

Sections are those of `JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`.

| element | status | PR (merged, SHA) | evidence on origin/main | notes |
|---|---|---|---|---|
| §4.1 dataset ✕ | SHIPPED | #593 (09-06, `aa611561`) | `dashboard_manager.py:1408` `clearable=True` | #652 (09-22, `32e7feea`) changed the traversal's third step: the gate clears the dataset and the operator picks. #656 (09-22, `886147b5`) made a re-fire at ⊥ silent. |
| §4.2 null guard | SHIPPED | #593 | `_apply_dataset_handler` :3319; Apply disabled at :5219/:8409; `_restage_dataset` :6418 | Also guards the live-swap path. `TestCommitPathsAreGuarded` exists, not mutation-checked. |
| §4.3 naming/channels | **PARTIAL** | #594 (09-06, `7bc53cca`) Y9; #595 (09-06, `0096f567`) notices; #652 docstring | `_build_model_selection_table` :3682-3687; `dataset-gate-notice` with `role="status"`/`aria-live` at :1418; `_empty_dataset_set_notice` (persistent); `_dataset_cleared_notice` (`duration=8000`) | **Not shipped: the Y7 bullet.** No `describedby` anywhere in canopy `src/`, and the Select still uses `title=reason` (:3699). Open #671 claims it. There is no Toast component; the "toast" is an auto-dismissing inline `dbc.Alert`. The mislabelled docstring was fixed last (#652), not first. |
| §4.4 model-state truth | SHIPPED, with a deliberate departure | #592 (09-06, `b5ad897b`); extended by #601 (09-09, `5d7dd6aa`), #607, #662 | `_selection_is_live` :3511; `_model_summary_text` :3540; `_select_model_handler` returns the whole payload (:3403) | The predicate is "does the backend serve this model", **not** `swapped is False`, which would be a false positive when re-selecting the live model. |
| §4.5 restart modal | SHIPPED | #593 | `open_restart_confirm_modal` Output `restart-ds-type.options` :6035, State :6059; handler :6254 | **No test covers it:** M6 (regate against the default model instead of the selected one) passed every test. Keeps the `enabled[0]` fallback by owner ruling. |
| §4.6 alias | SHIPPED | #599 (09-07, `de253e93`) | `_resolve_oneshot_start_body_handler` :2916 | M7 caught, but only by `TestX3OneShotBodyUsesTheResolvedName`. |
| §4.7 empty set | SHIPPED | #595; conflict branch #652; ⊥ branch #656 | `_gate_dataset_options_handler` :2998-3035 | M3 caught (9 test items). |
| §4.8 Start needs a dataset | SHIPPED | #593 | Input :5238; `_update_button_appearance_handler` :8378-8381 | M4 caught. |
| §4.9 staging | SHIPPED | #599 (501 guard), #601, #607 (09-09, `95284f37`) | `api_stage_dataset` :4376-4390; `RecurrenceBackend.stage_dataset` `recurrence_backend.py:375` | Fixed inside canopy only. Tests not mutation-checked. |
| §4.11 model clear | SHIPPED | #594 | `model-selection-clear` :2320; clear branch :3451-3456; no-model early return removed | M5 caught. |
| §4.12 demo mode | SHIPPED | #596 (09-06, `f8fb4a2c`) | `demo_mode.py:1147`; `main._demo_dataset_source` :1470; `connection_indicator.py:95-98` | A red connection badge, not a banner. There are three fallback call sites, not one. M10 caught. |
| (OQ-N2, ⊥ at mount) | NOT SHIPPED | open #667 | layout still seeds `DEFAULT_DATASET_TYPE` (:1400) | |
| G1a | SHIPPED | #593; search extended in #594/#595 | `TestG1Reachability::test_g1a_*` | **Stays green if only one clear affordance is reverted** (M1, M5), because the dataset ✕ and the model clear each unblock the pair on their own. Removing the ✕ alone is caught only by `test_g2_either_clear_alone_opens_the_graph[withheld1]`. The helper docstring at test :186 is stale. |
| G1b | SHIPPED | #593, #594 | `test_g1b_no_reachable_state_is_invalid` | M16 (the gate keeps an incompatible dataset) is **not** caught by G1b: its search never reaches that branch and has no mount-hydration step. The notice tests and G7 catch it. M17 (M16 plus every Select enabled) is caught. |
| G1c | SHIPPED | #598 (09-07, `f56f46c2`) | `TestG1cThreeComponents` | M14 caught (3). |
| G1d | SHIPPED | #595 | `TestG1dNothingAvailable` | M3 caught. |
| G2 | SHIPPED as a property; the name is reused | #593, rewritten #594 | Property asserted by G1b plus the G1c/G1d invalid-state tests | The tests *named* `test_g2_*` check something else: the deadlock returns only when both clears are withheld. |
| G3 | SHIPPED | #595 | `TestG3EmptySetRecovery` | M3 caught. |
| G4 | SHIPPED, re-specified | #599 | `TestG4GeneratorNameResolution` | It does not compare against juniper-data's registry; G10's `test_every_seeded_value_resolves_to_a_known_generator` does (#612, against a snapshot dated 2026-09-09). M7 and M19: the G4 class stayed green. |
| G5 | SHIPPED | #592 | `TestG5ModelStateTruth` | M9 caught. |
| G6 | SHIPPED | #593 | `TestG6StartRequiresACompleteSelection` | M4 caught. |
| G7 | SHIPPED | #662 (09-23, `2f973ca2`) | `TestG7MountDatasetIsTheBackendsDataset`, `TestG7AcrossTheRealSeams` | M11 caught (6). |
| G8 | SHIPPED | #594 | `TestG8ClearedModelUngatesTheDataset` | M5 caught. |
| G9 | SHIPPED | #596 | `test_demo_mode_local_fallback.py` | M10 caught. |
| G10 | SHIPPED | #612 (09-10, `8cfb29ac`) | `TestG10EveryUpstreamGeneratorIsSeededOrNamed`; `UNSEEDED_GENERATORS` (2 entries); `KNOWN_UPSTREAM_GENERATORS` (16) | Upstream generators added after 09-09 are not caught. Not mutation-checked directly (2 of its tests failed under M19). |
| G11 | SHIPPED today, reworded | **#665** (09-23T06:17Z, `7950bf9e`); before that, #610 covered only the equities pair | `TestG11EverySeedIsBounded`; `SEEDED_GENERATOR_BOUNDS` `model_registry.py:432` (14 entries) | Classifies each seed rather than following the design's literal wording. M20 caught. |
| Y3 | SHIPPED | #662 | `TestY3TheModelAxisHasAReadSide` | M18 caught. |
| §7 PR 1 | SHIPPED | #592 | | The N5 Start gate and server refusals followed in #601. |
| §7 PR 3 | PARTIAL | #593, #594, #595, #598 (+#596 for §4.12/G9) | | Missing only §4.3's Y7 item. Both ⊥ states were accepted in a browser: `reports/2026-09-05_canopy-deadlock-consensus/browser_acceptance.md` (@`aa61156`) and `browser_acceptance_prb.md` (@`f8fb4a2`). |
| §7 PR 4 | SHIPPED | §4.5 in #593; §4.6/G4 in #599; §4.9 in #599+#601+#607 | | Because §4.5 landed with PR 3, the "quarantine the restart modal" fallback was never needed. |
| §7 PR 5 | SHIPPED | Y5 #609 (`39998791`); seeds #610 (`94ff71c9`), #612, #616 (`b7883d5d`), #621 (`b01f33f7`), #622 (`1597c679`); G11 #665; §12.9 follow-ons #625 (`f7bbc4ee`), #632 (`812f26c0`), #644 (`ba3b16ff`) | | The `mackey_glass` seed flag was never built: `seed` is in `INFRASTRUCTURE_FIELDS` (`dataset_schema.py:110`), so it never reaches the form. |
| §7 ∥ | MERGED, NOT RELEASED | juniper-data#421 | see section 3 | |

`notes/JUNIPER_2026-09-05_JUNIPER-CANOPY_SELECTION-DEADLOCK-CONSENSUS-VALIDATION.md` lines 176-183 already carries a shipped map for #592–#598.

## 2. Claims in the design doc that main contradicts

Line numbers are in `JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`.

- **L62-67:** says Start is ungated at ⊥ and the handler takes no dataset. Main's signature at :8334 takes `dataset_value`, and Start is disabled on either axis (#593).
- **L76:** "only the dropdown ✕ is in scope". The model clear shipped in #594.
- **L116:** says recurrence's enabled list is just `["equities_seq"]`. It is six datasets (#612), pinned by `test_the_lmu_s_compatible_set_is_the_six_rank_3_seeds`.
- **L135-138:** calls the ⊥ POST "vacuous" and `_restage_dataset` "the correct idiom". Main (:3312-3318, :6415-6417) records that the empty body clears any prior staging, and that idiom produced the same empty body. Both now refuse (#593).
- **L142-144:** the "dataset-primary" docstring is fixed (#652).
- **L147-148, L153-156:** the notice was to name the old and new value. #652 replaced it with a "Dataset cleared" notice, since the gate no longer moves the dataset.
- **L161:** "zero aria-* attributes". Main has `role`/`aria-live` at :1418.
- **L169-172:** says the handler "mirrors only nn_model and execution" and uses `swapped`. Main mirrors the whole payload (#601) and tests provider agreement (#592).
- **L179:** says `restart-ds-type` has no options writer. It does, at :6035.
- **L187-188:** "as both sibling handlers do". The siblings use the alias only to look up schemas; the staging payload must stay untranslated (#599's counter-test).
- **L192-195:** quotes the pre-fix gate code. That code was split by #595.
- **L205-209:** "RecurrenceBackend has no stage_dataset … → 500". It exists (#607), and the route returns 409/501 guards.
- **L214-215:** "the follow-on staging PR" is #607 and is not named.
- **L275-277:** the `not model_key` early return was removed (#594).
- **L292-300:** describes one fallback site. Main has three call sites (`demo_mode.py:561, :1918, :2369`).
- **L317:** G4 "fails" before. #599 found it already passed as worded.
- **L322:** G9 "degrades silently". It logged a warning; it was silent only in the UI (#596).
- **L324:** G11 "passes". #665's own comment calls that a vacuous pass until #665.
- **L336-341:** says the five resolvers are not injectable. All are (#598), and the gate handler takes `generators=` (#595).
- **L382-387:** the PR 1/3/4/5 rows carry no SHIPPED markers.
- **L399-400:** "PR 2's … one keyword … a revert restores the deadlock". PR 2 is hydration (#662). Reverting the keyword alone does not restore the deadlock (M1).
- **L408-411:** yfinance "absent" from the lock and "zero available datasets". The lock on juniper-data main has yfinance (#421), and #612's synthetics need no extra.
- **L417-419:** "Y1–Y9" not fixed. Main has Y3 (#662), Y5 (#609), Y9 (#594) and half of Y7 (#595). Y1 is fixed per the titles of #633/#643; I did not verify the source.
- **L481-483:** "⊥ states not observed". Both were observed in the two reports named in the PR 3 row.
- **L584-585, L589-590, L775-777:** yfinance/equities extra absent. Present on juniper-data main (#421), not yet released.
- **L630:** G11 enforced by `TestEquitiesSeedIsGenerableAndFinite`. Now `TestG11EverySeedIsBounded` (#665).
- **L765-766:** "all seven carry {}". mnist carries `{"flatten": True}` (#625).
- **L860-861:** `:604` is now `:631` (line drift only).
- **L893-894, L924-926, L928:** `flatten` rendered as a checkbox. It is withheld via `SHAPE_DETERMINING_FIELDS` (`dataset_schema.py:171`); #623 was fixed by #625.
- **L976-980:** the split-plumbing and `sizing_mode` defects were fixed by #632.
- **L986:** arc_agi is "classification". Canopy main's registry text says upstream moved it to `structured` (juniper-data#402, which I did not verify).

## 3. The ∥ row: juniper-data#421 release status

- #421 merged 2026-09-23T00:56:08Z as `68c3cd7c` and is on juniper-data `origin/main`. The lock now compiles with `--extra equities` and pins `yfinance==1.7.0` (line 214).
- **No release contains it.** `git tag --contains 68c3cd7c` is empty, and `merge-base --is-ancestor … v0.15.0` exits 1.
- The latest GitHub release is v0.15.0 (published 2026-09-22T18:55:30Z, tag `46894ba1`), and its lock has no yfinance. PyPI's latest is also 0.15.0.
- Not verified: the GHCR image tags (the token lacks `read:packages`). GitHub's "Latest" badge also still points at v0.13.0.

I changed no files in any repository. Five untracked `util/ad-hoc/` entries appeared in this worktree between 01:11 and 01:31 local time; they came from another process, not from me. Mutant run logs are in the scratchpad (`m*_run.txt`); I deleted the extracted trees.

---

**Archivist's notes (2026-09-23, not part of the agent's report).**

- The "five untracked `util/ad-hoc/` entries" were the parent session's own scripts, written into the same
  worktree while the agent ran. They are retained in juniper-ml#2039 and in the PR that archives this file.
- The §4.3 Y7 "not shipped" finding is superseded if juniper-canopy#671 merges. At archive time it was open
  and armed, carrying the model-table half of Y7 (`aria-describedby` on every Select).
- The mutants M1–M20 were run by the agent and are **not independently reproduced**. Treat each "caught" or
  "not caught" as one agent's measurement, not a verified property. M6, "§4.5 has no test", is the one
  worth confirming first, since it names an untested shipped behaviour.

**Archivist's notes, second set (2026-09-23, after the reconciliation).**

- **Applied.** `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` now carries a
  status line under every §4.x heading, the §5 guardrail statuses, §7's shipped record, and a dated
  correction under each line in section 2 above. The original text is kept, with the note after it.
- **Two mutants reproduced**, with `util/ad-hoc/2026-09-23_mutation_check_m1_m6.py` on canopy
  `48074653`:
  - **M6** holds. With the restart modal regated against `DEFAULT_MODEL_KEY` instead of the selected model,
    canopy's **whole CI unit lane** passed with 0 failures. canopy#675 adds
    `TestX2RestartModalIsGatedAgainstTheSelectedModel`, which fails twice under M6.
  - **M1** holds. Reverting the dataset dropdown's `clearable=True` fails only
    `test_g2_either_clear_alone_opens_the_graph[withheld1]`.

  The other mutants remain unreproduced.
- **Where this report is wrong or out of date:**
  - Section 2's L336-341 item says "the gate handler takes `generators=` (#595)". That is wrong: it
    came with canopy#594, absent at `aa611561` and present at `7bc53cca`.
  - The §4.3 "Y7 not shipped" finding and the OQ-N2 row are superseded. canopy#671 (`7cd8a9d4`) and
    canopy#667 (`2c56e8a3`) both merged on 2026-09-23.
  - Section 3's "Latest" badge "still v0.13.0" is out of date. `gh release list` now shows v0.15.0
    as Latest. No release contains juniper-data#421; that part still holds.
  - "The siblings use the alias only to look up schemas" is imprecise. `_apply_dataset_handler` also
    uses it to choose the spiral branch.
- **Verified since**, where the report had said it had not checked:
  - juniper-data#402 moved `arc_agi` to `structured`.
  - Y1 is fixed in source.
