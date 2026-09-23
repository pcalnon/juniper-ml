<!-- markdownlint-disable -->

# Canopy E2E arc — validator reports, 2026-09-22 (verbatim)

Archived by `util/ad-hoc/2026-09-22_archive_consensus_reports_canopy.py` from the session's subagent
transcripts. Each section is the agent's final report exactly as delivered; they are EVIDENCE for
Phase 7 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, not conclusions — the
reconciliation, including where a report was itself corrected, is in that phase.

## Lane B — F-CANOPY-048 mechanism (the two-callback cycle and the starved breaker)

*agent `ae36b838954f7bb30` · last-assistant-text · 10212 chars*

## F-CANOPY-048 Lane B verdict: the mechanism survives in substance, but four statements need correcting

The two-callback cycle is real and is the necessary cause of the lock. Every attack I was asked to run was carried out. The claim's own explanation of the feeder, of the WS drain chain, of "each" callback, and of the census counts is wrong in places. The merge fix works on canopy `main`, but only conditionally.

### Verdict per claim part

**Part 1: the two-callback cycle. SURVIVES.**
- On canopy `origin/main` `886147b5`, `metrics_panel.py:959-980` (`handle_replay_controls`, B) takes `replay-slider.value` as an Input and writes `replay-state.data`.
- `metrics_panel.py:1074-1094` (`update_replay_ui`, A) takes `replay-state.data` as an Input and writes `replay-slider.value`.
- Nothing changed between the measured build `9bffaba1` (an ancestor of `main`) and `main`; the only diffs are unrelated dataset-gating edits.
- `git grep` shows only these four `metrics_panel.py` callbacks write replay props.

**Part 2: the readiness rules. SURVIVES for A and B; WEAKENED on "each".**
- `getReadyCallbacks` (`dev.js:1633`) and the transitive closure (`:1617`) are as described. Pending is `requested + prioritized + blocked + executing + watched + executed` (`:3827`, reducer `:3575`). The observer uses that same set (`:2967` → `:3045`).
- **Correction:** `update_play_button` has no self-closure. Its only output, `replay-play.children`, feeds nothing. It is held only because A or B is pending.
- **Missing nuances:**
  - Readiness checks Inputs only, never State (`:1743`), minus the callback's own Outputs (`:1661`).
  - **An `allow_duplicate` output carries `@<sha256>` on its property** (`dash/_utils.py:159-163`). The renderer keeps the suffix (`splitIdAndProp :5895`, `combineIdAndProp :1539`, `inputMap[id][prop] :1552`).
  - So an `allow_duplicate` writer's closure reaches nothing. `append_ws_metrics_store` (`dashboard_manager.py:4518`) and `replay_tick` can hold nothing. Lane A's `served_writers_of_replay_state` shows `replay_tick` served literally as `…replay-state.data@20746ef1…`.

**Part 3: the breaker is starved. Source SURVIVES; the canopy half is WEAKENED to "supported, not demonstrated at pass level".**
- The breaker condition is at `dev.js:3064`, inside the `requestedCallbacks` observer (module `:2908`), which runs only on `requested`/`completed` changes (`:3166`).
- The served bundle is `min.js`, which carries the identical condition (`G=Yn(p,y,b,d)…G.length||!y.length||y.length!==b.length`, with a closure-based `Yn`). Canopy mounts Flask under FastAPI (`main.py:618`) and never enables dev tools. The load-time "Circular Dependencies" check therefore never runs: its multigraph is filled only under `validate_callbacks` (`:6553`, `:6570`).
- Nuance: `requested` is compared after de-duplication and pruning, but pending is raw, so duplicates suppress the breaker for one pass.
- **Census:** `2026-09-22_slots_replay_click_requested_census.txt` shows something executing or watched in 6459/6471 samples. The other 12 samples are unresolved, because the census does not record `blocked` or `executed`.
- **Lane A** (run2_redux): `watched` is 3-12 at all 14 snapshots.
- **Strongest indirect evidence:** the position stayed `0 / 0` with a full store in every run. A single breaker firing would have promoted A.
- A quiescent *sample* does not imply a quiescent *pass*. In the clean room's unrelated-feeder cycle arm, 2 quiescent samples occurred after the feeder started in each run and the lock held; the observer reads state after `wait(0)` (`:2962`).

**Part 4(a): the clean room. Result SURVIVES; its explanation is REFUTED.**
- I re-ran it: FEEDER-CYCLE-LOCK, cycle arm 2/2 locked, acyclic arm 2/2 live (`…_feeder_laneB.json`).
- The feeder is `allow_duplicate`, so its closure is `{data.data@hash}`, not `data→A→slider→B`. The acyclic arm's A applied the fill in 7/7 feeder runs, which is impossible under the docstring's account.
- Fidelity: the Input/Output graph matches canopy's. The missing interval outputs and missing `replay_tick` do not change any closure.
- Server saturation is excluded. Flask runs `threaded=True` (`flask/app.py:655`). The acyclic arm saw B 3/3 requests and responses every run. The JSON has no timing fields.
- **Discriminating variants** (30 runs, predictions fixed before the first run, all 30 matched):

| Feeder (always pending unless noted) | cycle arm | acyclic arm | merged A+B arm |
|---|---|---|---|
| `allow_duplicate` writer of data (the original) | locked 2/2 | live, fill shown 2/2 | live 2/2 |
| primary writer of an unrelated store | **locked 2/2** | live 2/2 | live 2/2 |
| primary writer of data | locked 2/2 | controls live, **fill never shown** 2/2 | **locked 2/2** |
| gapped (0.2 s sleep), either kind | live 4/4 | live 4/4 | live 4/4 |

So the lock needs the cycle plus any callback that is pending at every pass. A merely periodic poller is not enough.

**Part 4(b): the live census. SURVIVES, with wording fixed.**
- A and the label were in `requested` 6471/6471 samples. **B was there 4030/6471**, from the click at about 30.9 s onward. The `util/ad-hoc/README.md` line saying "three … 6471 of 6471" is wrong for B.
- The "server-side census" is really a browser wire census (`2026-09-08_replay_block_redrive.py:146-163`). It saw 0 replay-state responses in all three runs.
- Lane A agrees: 0/559 and 0/602 requests naming replay-state, a positive control answering in 1-2 s, and B requested for about 162 s, never prioritized.

**Part 4(c): parking the poll. SURVIVES, and is more discriminating than the claim realises.**
- With the poll parked, and the WS append inert, only B can hold A's Inputs. The primary writers are B alone (`:961`) and `update_metrics_store` alone (`dashboard_manager.py:4485`). So A's block requires the cycle.
- Caveat: the parked run and the census were separate runs. The parked run shows A never applied, not where A sat in the queue. One run combining the parked poll, the census and a click would close this.

### Alternative explanations
- **12-slot cap:** fails. The cap acts on `prioritized` (`:2846`), and the block sits in `requested`.
- **`prevent_initial_call`:** fails. B is requested on the click.
- **Components missing from `paths`:** fails. `pruneCallbacks` (`:1745`) would remove the callbacks, and the DOM shows the controls present.
- **`replay_tick`:** fails. It is inert (`allow_duplicate`) and its interval stayed disabled throughout.
- **Real but excluded here:** in the same census, `ws-connection-indicator` sat in `requested` at every sample **with no cycle**. Its upstream writers were pending in 45% and 83% of samples (`dashboard_manager.py:4298-4305`). "Stuck in `requested`" alone does not prove a cycle; for the replay block, it is the parked-poll run plus the writer enumeration that rules this out.

### Fix implication and recommended fix shape
**Merge A and B into one callback that branches on `ctx.triggered_id`; keep the label callback and `replay_tick`.**
- `differenceBasedOnId` removes the merged callback's own outputs from its readiness check (`:1661`).
- Circular pruning (`:2972`) stops its own slider write from re-triggering it.

Conditions to state with the fix:
1. The merged callback is **still locked by any always-pending primary writer of the metrics store** (locked 2/2 in the table). It works on `main` only because `update_metrics_store` is gated by `running=` (`:4490`) and has gaps; the census has it in `watched` 4083/6471. Canopy's own comment qualifications 2 and 3 describe how it can re-request mid-flight.
2. `getUniqueIdentifier` ignores the trigger, so a store write that re-requests the callback evicts an in-flight click. During training this may lose clicks; measure it. Two of the 12 gapped runs missed a toggle within 3 s (unexplained).
3. **A latent defect is masked by the lock.** Chains that start at `replay_tick` or at a store write are not pruned (`:2487`, `:2972`). So B's slider branch (`:1036-1038`) would pause playback on every programmatic slider write. In the gapped cycle arms, B fired 9-11 times for 3 clicks, against 3 in the acyclic arm. The merge removes this, but a fix that keeps B reading the slider as an Input would not.
4. **Rejected:** moving B's trigger to `drag_value`. Dash 4.2's slider echoes every programmatic `value` change into `drag_value` (`dcc/async-slider.js`).
5. **Add a CI test** that fails on any Input-graph cycle spanning two or more callbacks (`@hash` outputs mapped to their base property). The dev-tools check never runs in canopy.
6. **Unverified robustness idea:** trigger on the store's `modified_timestamp`, with `data` as State. It needs its own clean-room arm.

The evidence doc's F-048 text (around `:7204`) and the clean-room docstring's feeder paragraph both need the `allow_duplicate` correction.

### Documents
- **Referenced:**
  - `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`
  - `util/ad-hoc/2026-09-22_f048_replay_cycle_cleanroom.py`, `util/ad-hoc/2026-09-08_replay_block_redrive.py`, `util/ad-hoc/e2e_f027_slots.py`, `util/ad-hoc/README.md`
  - in `reports/e2e-canopy-2026-09-02/transcripts/`: `2026-09-22_f048_cycle_cleanroom*.json`, `2026-09-22_slots_replay_click_requested_census.txt`, `2026-09-22_replay_block_redrive_8051_main*.json`, `2026-09-22_laneA_f038_m18_claim2_replay_run{1,2_redux}.json`, `2026-09-22_idle_cpu_profile_training_metrics.json`
- **Changed (created):** `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/lively-humming-pixel/reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_f048_cycle_cleanroom_feeder_laneB.json`
- **Scratchpad, not in the repo:** `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2a1ec942-45a0-42ee-a732-5e977907ca7a/scratchpad/laneB-f048/` holds `f048_laneB_variants.py`, `f048_laneB_variants.json`, `f048_laneB_variants.log`, `f048_laneB_smoke.json` and `mincol.py`. If the variant results are cited in a document of record, the script must first move to `util/ad-hoc/` and its JSON to `reports/…/transcripts/`, per the script-placement rule.

---
