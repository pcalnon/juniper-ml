<!-- markdownlint-disable -->

# Phase 12 ledger validation, round 1 — validator reports (verbatim)

Round 1 of the consensus review of the canopy E2E ledger's Phase 12 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen local commit c626e847 (the Phase 12 draft, juniper-ml worktree squishy-growing-breeze, branch docs/canopy-e2e-phase12), 2026-10-19. Three lanes, briefed separately from reports/e2e-canopy-2026-09-02/drafts/lane12{A,B,C}_phase12_ledger_brief.md, with different entry points: Lane 12-A the artifacts first, Lane 12-B the ledger first (adversarial on the dispositions), Lane 12-C the handoff documents first (cross-document consistency). Each report below is the lane's final message, verbatim; each lane ran once. The orchestrator's dispositions are in the ledger's Phase 12 Consensus record, and the correction pass is util/ad-hoc/2026-10-19_phase12_ledger_round1_corrections.py.

## Lane 12-A (artifact-first re-derivation)

**Lane 12-A** (artifact-first re-derivation, round 1)
**VERDICT: SOUND-WITH-FIXES**

Worktree `squishy-growing-breeze` at `c626e847`; diff `git diff 0e144c3c c626e847 -- notes/` (380+/5−, one file). Own reader: `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/D227803E-A1C2-4957-9A7C-824C3F8B44BD/scratchpad/lane12A/my_census_reader.py`, written and run before the archived reader. No tracked file modified (`git status` shows only the three untracked briefs).

**TABLE**

| claim | re-derived | result | evidence |
|---|---|---|---|
| Census answered/evicted 188/0, 164/0, 256/0, 304/0; 912 total | own reader: A=188/164/256/304, X=0 in all; archived reader identical | MATCH | `pacer-live/f058-census-run{1,2,3-v2,4-final}.json` `raw.req` |
| Still in flight at close 1 / 0 / 1 / 0 | ids 189 / — / 257 / — never ended | MATCH | same |
| In-flight median/p90/max per run (6,194/12,113/16,363; 7,891/11,748/17,308; 4,809/6,707/9,547; 3,991/5,179/6,655) | identical to the ms | MATCH | both readers |
| Clamp episode 58.4 / 59.9 / 59.4 / 59.1 s | 58,439 / 59,920 / 59,429 / 59,088 ms, one episode per run | MATCH | `raw.lane` |
| Fires 0, eviction runs none | `raw.fires` empty; no X records | MATCH | all four |
| 845 inside scored windows (170/149/240/286) | baseline+idle+4 triggers resolved = 170/149/240/286 | MATCH | `baseline`, `idle`, `triggers[].stats` |
| "Gate wrote `false` onto an enabled lane 8 or 9 times per run … in flight at most of them" | total gate writes 9/8/8/8; `false` onto an **enabled** lane 7/6/6/6; plus one `false` onto the disabled lane (clamp release) and one `true` per run; `false`-onto-enabled with a request in flight 5/5/5/**2** | MISMATCH | `raw.gate`; archived reader's per-write list |
| Gate's one `true` per run is T-apply's clamp | one `False->True` per run at 678001/722743/677019/667027 ms, T-apply ~60 s later | MATCH | `raw.gate`, `triggers` |
| T-gate/T-tab/T-mode/T-apply NO-EFFECT, `took` false | all 16 `took=false`, verdict NO-EFFECT | MATCH | `triggers[]` |
| Run 4 cycle ~5.0 s, "5.0–6.3 s by window" | cadence medians 5081 / 4996 / 5785 / 5357 / 5069 / 6272 | MATCH | run 4 stats |
| `served` field = `3029d07d` runs 1–3, `2689a207` run 4 | `served_sha` as stated | MATCH | transcripts |
| Status bar: APPLIES 56/56, 42; VOID 9/9, 8; APPLIES 12/11, 11; NEVER-APPLIES 34/0, 0 | verdicts and counts identical; control `git_sha` null | MATCH | four `2026-10-08_status_bar_apply_census_*.json` |
| Bar showed `Completed — early stopped`, epoch 76; control `Stopped`/`0` | `dom_bar` on all three pacer legs; control `Stopped`/`0`/`""` | MATCH | same |
| Status-bar final leg served `2689a207` | `serving.git_sha` 2689a207… | MATCH | `…_final_2689a207.json` |
| Health: `git_sha` 2689a207, `version` 0.6.0 | as stated | MATCH | `2026-10-08_final_leg_health_2689a207.json` |
| Deps: no `running=` guard, one Input per feeder, 179 callbacks | 179 entries; no `running` key; `update_metrics_store` Input = `metrics-store-request.data` only; status-bar feeder Input = `status-bar-request.data` only | MATCH | `…dash_dependencies_2689a207.json` |
| Renderer table, every cell (172/171, 172/171, 198/197; 0/0/88 (70+18); 0/0/96 (69+27); 4 fires; 145,0,4161 / 146,0,4153 / 167,—,4618; 12/12, 12/12, 2/12; strand 30,999/3,969 and 30,995/3,968; ack-derived k=118, k=109; PASS/PASS/FAIL) | all identical (30998.96→30,999; 3969.33→3,969; 30994.82→30,995; 3968.49→3,968); guard `next_applied` true only on tab rep 1 and 2 | MATCH | three `*_score.json` |
| `pacer_stdout.json` keeps first score (1 eviction, k=109, FAIL) | evicted_total 1, PASS false | MATCH | `pacer_stdout.json` |
| Renderer config: rtt 3,600 ms, clip 888–5,345, strand 45 s, dash 4.2.0 | `args.rtt_ms` 3600, `strand_ms` 45000, seed 1; clip constants at script line 132 | MATCH | `*_run.json`, script |
| Final renderer run 20:04–20:16 CDT | requests 20:04:17–20:16:29 CDT | MATCH | `20261008T201631_pacer_run.json` |
| First pacer run "17:41 CDT", control "17:40 CDT", "started 17:40–17:41 CDT" | pacer requests 17:28:58–17:41:10; guard 17:28:59–17:40:15; the stamps are end times | MISMATCH | `…T174112_pacer_run.json`, `…T174018_guard_run.json` |
| Final JS = commit 3's, unchanged by 4 and 5 | `poll_pacer_js` sha identical at 2689a207, 65ead946, 25c5c887; commit 4 differs from 3 only in one docstring sentence (emitted JS unchanged) | holds | fetched sources |
| #731: 8 commits, five + three merges, head `13834945`, merged 2026-10-09T02:27:27Z as `25c5c887` | identical; all 8 verify signed (ledger does not say the merges are unsigned) | MATCH | `gh api pulls/731`, `/commits` |
| One review thread, CodeQL `_PACED_POLLS` unused, `dashboard_manager.py:520`, resolved | 1 thread, `github-advanced-security`, line 520, `isResolved` true | MATCH | GraphQL |
| CHANGELOG `[0.9.0]` dated 2026-10-10; fix is first Fixed item; three ids, stale bound, cost, `[0.8.0]` correction | heading line 12; `### Fixed` at 223, pacer item first; all elements present ("could not do") | MATCH | CHANGELOG at `main` |
| Release v0.9.0 published 2026-10-17T19:45:37Z at `bd001153` | identical; tag → commit `bd001153` | MATCH | `releases/tags/v0.9.0` |
| PyPI juniper-canopy 0.9.0 | 0.9.0, uploaded 2026-10-17T22:08Z | MATCH | pypi JSON |
| juniper-ml#2196 `0174c3dd`, 2026-10-09T02:36:55Z; four instruments, two evidence dirs, consensus record | identical; 35 files | MATCH | `gh api pulls/2196/files` |
| Design: rule, `extra` over `stale`, bound `min(120 s, max(30 s, 3×maxRtt))`, `performance.now()`, keyed by request-store id, `_PACED_POLLS`, `_setup_poll_pacers`, `prevent_initial_call=False` on `update_metrics_store`, ack on every path | all present at `25c5c887` (`reason = changed ? 'extra' : (acked ? 'tick' : 'stale')`; `PACER_STALE_CAP_MS = 120000`; `POLL_PACER_STALE_MS = 30000`; `n=seq` into the modulus gate) | MATCH (two wording NITs) | `dm_25c5c887.py` 505–606, 2657–2700, 4880–4935, 8050–8113 |
| Triage 79 / 56 / 1 / 2 / 20; P1 4 (064, 065, CASCOR-001, -002); P2 16 | identical | MATCH | `e2e_finding_triage.py` |
| Text-corrected sites in #731's diff | "harmless window" (−467 hunk), "THREE QUALIFICATIONS"/"Self-healing, bounded" (−4727 hunk), watchdog comment "must not re-enable DURING a legitimate fetch" (−2500 hunk), `METRICS_STORE_STRAND_TIMEOUT_MS` (−407 hunk), `test_poll_gating.py` "continuously ``True``" (−187 hunk, covers 194–197) and "the apply clamp alone" (−308 hunk, covers 313), modulus comment, CHANGELOG "could not do" | MATCH | `pr731.diff` |
| CI: all 25 checks on `2689a207` | 25 success, 5 neutral, 1 skipped | holds | check-runs |
| Consensus record: R1 three lanes, 16 mutations, M2; R2 two lanes, 20 mutations, M18; R3 one lane; "condensed in transcription" | all present | MATCH | consensus file |

**FINDINGS**

1. **MINOR** — gate-write count. Ledger: "The gate wrote `false` onto an enabled lane 8 or 9 times per run, at page load, at each trigger and at the clamp's release, with a request in flight at most of them". Evidence: `raw.gate` holds 9/8/8/8 writes in total; of these one per run is the T-apply `true` and one per run is the `false` that releases the clamp onto a *disabled* lane, leaving `false` onto an enabled lane **7/6/6/6**. A request was in flight at 5/5/5 of those in runs 1–3 but at only **2 of 6** in run 4. Fix: "The gate wrote 8 or 9 times per run: `false` onto an enabled lane 7, 6, 6 and 6 times (page load, each trigger, the census's own release), once `true` (the clamp) and once `false` onto the disabled lane (the clamp's release); a request was in flight at 5, 5, 5 and 2 of the enabled-lane writes". Changes a number, disposition or action? yes (a number); no disposition or action.

2. **MINOR** — renderer run times. Ledger table: "pacer, first (… 17:41 CDT)", "guard + watchdog control (17:40 CDT)"; text: "The two runs started 17:40–17:41 CDT beside two canopy unit suites". Evidence: the first request of `20261008T174112_pacer_run.json` is at 17:28:58 CDT and the last at 17:41:10; the guard run spans 17:28:59–17:40:15. The file stamps are end times. Fix: "17:29–17:41 CDT" in both cells and "The two runs ran 17:29–17:41 CDT". (The README's "17:40–17:54" is wrong the same way; not under review.) The earlier start strengthens, not weakens, "before commit 1" (`7aed1f2b` committed 18:28 CDT). Changes a number, disposition or action? yes (a time); no disposition or action.

3. **NIT** — pacer rule. Ledger: "If the ack has caught up, or no request has been made, it writes request `seq + 1`". Evidence: with no request and no ack the JS returns `no_update` until the stale bound (`issuedAt` = first sighting); in practice the layout's seq-0 request is acked by the feeder's mount call, so the clause is moot. Fix: drop "or no request has been made" or say "(the layout's seq-0 request is acked by the mount call)". Changes a number, disposition or action? no.

4. **NIT** — modulus. Ledger: "now counts acknowledged requests, not ticks". Evidence: the feeder passes `n=seq`, so it counts issued request numbers, including a stale re-issue that was never acked. Fix: "counts requests (`seq`), not ticks". Changes a number, disposition or action? no.

5. **NIT** — tests "as the PR records them". Ledger: "run with `LD_LIBRARY_PATH`, `LIBTORCH` and `LIBTORCH_LIB` unset". Evidence: the PR body says "`LD_LIBRARY_PATH` / `LIBTORCH` unset"; `LIBTORCH_LIB` appears only in the handoff. Fix: cite the handoff or drop `LIBTORCH_LIB`. Changes a number, disposition or action? no.

6. **NIT** — "the five that session signed … and three merges". Evidence: all eight commits, merges included, verify as signed on GitHub. The sentence is not false; adding "(the merges are GitHub-signed)" would forestall the reading that they are unsigned. Changes a number, disposition or action? no.

Nothing refutes FIXED for F-CANOPY-055, -058 or -068, or the 79/56/1/2/20 counts, or the 4 open P1.

**WHAT YOU COULD NOT CHECK**

- The load readings (32.7 / 13.8 / 5.4 / 9.9; 9.9 before and 5.9 after the final run): README assertions, no transcript records them.
- That runs 1–2 and the first status-bar run served "the tree before commit 1" and run 3 "commit 2's tree": by edit history / `__junPollPacerLastUnacked` only, as the ledger discloses; `served_sha` is `3029d07d` for all three. The leg build times (22:43Z, 00:02:18Z sixteen seconds after commit 2, 00:33:31Z after commit 4) are consistent.
- `2026-10-08_compare_canopy_wiring.py`'s "179, symmetric difference 0" against commit 5: needs a built canopy app; I confirmed only that the capture has 179 entries and that `poll_pacer_js` is identical at 2689a207 and 65ead946.
- The six lane reports' full texts (condensed in the consensus file), the full canopy unit-suite counts (6,819; 33 + 1 xfailed), and E-3's 60 s force-release as the clamp's releaser (inferred from timing, as the ledger says).
- Anything live: no service, no trio, no 0.9.0 wheel run.

**SECRETS/PII:** none read or printed; no `.env*` opened; git log used `%h %s` only; GitHub queries returned no author e-mail fields.

## Lane 12-B (adversarial on the dispositions)

**Lane 12-B** (adversarial on the dispositions, round 1)
**VERDICT: SOUND-WITH-FIXES**

The three FIXED dispositions stand; the counts (79 / 56 / 1 / 2 / 20; 4 P1 = F-CANOPY-064, -065, F-CASCOR-001, -002; 16 P2) reproduce from `python3 -B util/ad-hoc/e2e_finding_triage.py`. The fixes below are to numbers inside the phase text, provenance labelling, one undisclosed user-visible change, and wording. No count, disposition or owner action changes.

**FINDINGS**

1. **MINOR — the gate-write count is wrong by two per run, and "most" is false for run 4.** Ledger: "The gate wrote `false` onto an enabled lane 8 or 9 times per run … with a request in flight at most of them. The gate's one `true` per run is the T-apply clamp." Evidence: `util/ad-hoc/2026-10-04_f058_census_v2_analyze.py` on `reports/e2e-canopy-2026-09-02/pacer-live/f058-census-run{1,2,3-v2,4-final}.json` lists 9 / 8 / 8 / 8 gate writes in all, of which one per run is `False->True` (the clamp) and one is `True->False` onto the *disabled* lane (its release). `false` onto an enabled lane is 7 / 6 / 6 / 6, with a request in flight at 5 of 7, 4 of 6, 5 of 6 and **2 of 6** (run 4). Fix: "7 (run 1) or 6 times per run … with a request in flight at about half of them, 2 of 6 in run 4". The conclusion (none evicted) is unchanged. Changes a number, disposition or action? yes (a phase-text number; no count).

2. **MINOR — run 3's provenance rests on a discriminator that is false in letter and unarchived.** Ledger: "Run 3 ran commit 2's tree, known from the page carrying `__junPollPacerLastUnacked`, which only commit 2 has." Evidence: `poll_pacer_js` at the merge (`dashboard_manager.py` at `25c5c887`, `var lastUnacked = window.__junPollPacerLastUnacked || …`) carries that name, as do commits 3, 4 and 5; it separates commit ≥ 2 from commit 1, not 2 from 3. The string occurs in no archived JSON or `*.log.txt`, only in `pacer-live/README.md`. The archived basis that does discriminate: the leg's `build_date` `2026-10-09T00:02:18Z` (`…_status_bar_apply_census_8052_pacer_v2.json`, same `:8052` leg as census run 3, whose log starts 19:04:39 CDT) against commit 2 at `00:02:02Z` and commit 3 at `00:19:57Z` (GitHub API), on the assumption the leg does not hot-reload. Fix: replace "known from the page carrying …" with the build-time basis and its assumption. Changes a number, disposition or action? no.

3. **MINOR — a user-visible cost of the pacer is not disclosed, and the sentence that covers it contradicts itself.** Ledger (The design, as merged): "A display-mode change issues an `extra` request at once, after the fetch in flight is acknowledged." Evidence: the pacer runs on the mode-store Input and on the 1 s tick (`METRICS_STORE_POLL_INTERVAL_MS = 1000`, `canopy_constants.py:412`); with a request in flight it returns `no_update`, so the `extra` request goes out at the first tick after the ack. In `pacer-renderer-check/20261008T201631_pacer_run.json` the three mode changes' `extra` requests were issued 3,010 / 4,693 / 3,687 ms after the switch (0.8–0.9 s after the in-flight response ended) and their data landed 6,695 / 8,047 / 7,397 ms after it, at a 3.6 s round trip; the first run reads 2,005 / 4,012 / 3,690 ms. On `main` the mode store was an Input of the feeder, so the fetch was issued at once (evicting the one in flight). Fix: under "Also changed": a Full/Hidden-units switch now waits for the fetch in flight plus up to one tick before its own fetch is issued (2–4.7 s in the renderer check; up to the lane's in-flight time, 17 s under the load of runs 1–2, on a real page), and reword "at once". Changes a number, disposition or action? no.

4. **MINOR — "Item 0 is DONE, both halves" closes an item one of whose asks is carried, and F-CANOPY-055's own verification rule is half met.** Ledger: "Item 0 is DONE, both halves … the allow-arm drive it also asked for did not run (item 27)"; F-055 header "verified live on the branch". Evidence: Phase 9's item 0 (ledger `:9693-9720`) asks for "the census and its triggers on the fix's leg, and F-CANOPY-025's allow arm re-driven on a leg … whose training may be started"; F-055's own entry (`:8320-8325`) says "The fix is verified by re-running this census … plus a Live Switch allow-arm drive". The census ran; the allow arm did not; the scored triggers are item 25. Phase 7's precedent is "closed or converted". Fix: "Item 0 is closed, its allow-arm drive converted to item 27 and its trigger scoring to item 25"; add to F-055's header or Status that the entry's second verification half is item 27. FIXED stands: the finding as stated (never applies → applies, 11 of 12 executed, NEVER-APPLIES on the control) is verified. Changes a number, disposition or action? no.

5. **MINOR — three results are stated as the phase's own re-derivation but have no archived output.** Ledger: "This phase re-derived every number below from those files"; "The callback graph of `65ead946` is identical to the capture …: 179 callbacks, symmetric difference 0"; "Each new node test fails on its own mutation (`…_pacer_round2_mutation_check.py`…)". Evidence: the capture (`2026-10-08_final_leg_dash_dependencies_2689a207.json`) has 179 callbacks, no `running=`, one writer each of `metrics-store-interval.disabled` and `fast-update-interval.disabled`, and each feeder's only Input is its request store (re-derived here); but the symmetric difference needs the built app, and the mutation check's result exists only in the PR body and `consensus/…rounds1-3.md`. Fix: label both as the session's results, as "Tests on the branch, as the PR records them" already does. Changes a number, disposition or action? no.

6. **MINOR — the two residual re-request paths and the modulus change are recorded but not dispositioned.** Ledger: "Two paths still re-request a feeder, each costing at most one response and no chain … the PR and the CHANGELOG disclose them." Evidence: a reader of the open findings cannot tell whether the ledger declined them. By §6.3 one lost response that the initial call itself replaces, with no chain (no guard to release; confirmed by the capture's single `disabled` writer), is below drift; the modulus now gates on `seq` with the same 1 s tick, so the full-view cadence is equivalent pending Phase 9's item 4 measurement. Fix: one sentence each: not filed, and why. Changes a number, disposition or action? no.

7. **NIT — item 27 omits the gate's other condition, so it can fail for the wrong reason.** Ledger: "expecting the switch enabled while a run is active and disabled after." Evidence: `_gate_live_switch_button_handler` returns `not (flags_ok and running)` (`dashboard_manager.py:7167` at `25c5c887`); the allow arm needs the experimental-functions toggle on. Fix: add "with the experimental toggle on". Changes a number, disposition or action? no.

8. **NIT — the cost bounds are the re-issue bounds, not the wait before an applied answer, and the bound never decays.** Ledger: "waits out its stale bound: at least 30 s, at most 120 s." Evidence: `staleMs = min(120000, max(30000, 3 * maxRtt))` is checked only on a tick, and the re-issued request then needs its own round trip: the renderer check's strand was re-issued at 30,999 ms and applied at 34,961 ms. `maxRtt` is a running maximum, so runs 1–2's 16–17 s in-flight times would set a 49–52 s bound for the life of that page. Fix: "re-issued after the bound, 30–120 s, and answered a tick and a round trip later; the bound only grows". Changes a number, disposition or action? no.

9. **NIT — the merge is a squash, and the modulus wording.** Ledger: "merged … as `25c5c887`", "eight commits … the head at the merge"; "counts acknowledged requests, not ticks". Evidence: `25c5c887` has one parent (`4f69524b`); the compare base of the head and the squash is `4f69524b`, so the merged tree is the head's. `seq` advances on every request issued, stale re-issues and `extra` included; the gate applies on `tick`/`stale` reasons (`_metrics_store_trigger`). Fix: "squash-merged as"; "counts requests issued". Changes a number, disposition or action? no.

**TRIED AND COULD NOT REFUTE**

- FIXED for all three, by precedent: F-CANOPY-053 ("FIXED by canopy#657 `d7d641b9`, verified live on `17588539`", a branch commit squashed) and F-CANOPY-054 (verified on v3 `a967a5bd`, squash `48074653`) accept branch-commit verification; F-CANOPY-059's "FIXED IN CODE … stays OPEN until the live re-drive" applied when no live check existed. The limits list is complete for what the evidence shows; CI is green on the head (25 success) and on the squash (46 success, 7 skipped), which the ledger does not claim and could add.
- Every table number: answered 188 / 164 / 256 / 304 = 912, 0 evicted, 2 never ended; in-flight medians/p90/max; clamp 58.4–59.9 s; scored windows 170 / 149 / 240 / 286 = 845; run 4's window cadence 4,996–6,272 ms; all four T-* `took=False`; status-bar 56/56, 9/9, 12/11, 34/0 with 42 / 8 / 11 / 0 latency changes and `Completed` on each pacer leg; renderer 172/171/0 and 198/197/88 (70 idle), 96 in flight, 4 fires, gaps 4,153 / 4,161 / 4,618 ms, `applied_by_ack_only` [109] and [118], `pacer_stdout.json` evicted 1.
- Metadata: merged `2026-10-09T02:27:27Z`; release `v0.9.0` at `bd001153` `2026-10-17T19:45:37Z`, `25c5c887` its ancestor (only `CHANGELOG.md` and the version fallback in `canopy_constants.py` differ); CHANGELOG `[0.9.0] - 2026-10-10` with the pacer as the first Fixed item, the three ids, 120 s, "at least 30 s" and the `[0.8.0]` correction; PyPI 0.9.0 uploaded 2026-10-17; one review thread, resolved, `dashboard_manager.py:520`; juniper-ml#2196 `0174c3dd` `2026-10-09T02:36:55Z`; `notes/releases/RELEASE_NOTES_juniper-canopy_v0.9.0.md` present.
- The corrected canopy text: `gh pr diff 731` removes "harmless window", "THREE QUALIFICATIONS", "Self-healing, bounded to one cycle", "continuously", the strand constant and `running=`, rewrites "apply clamp alone", and adds the `[0.8.0]` correction.
- Dropping item 24's reader change: Phase 11 (`:10854`, `:11063`) records two lanes' push-order walks identical to the type selection; the readers read guard releases and watchdog samples, which the branch lacks; the v2 analyzer's eviction count comes from request records, not `disabled` episodes.
- The counts logic, the two limbs, O17's reach (F-057, -018, -012, -013 named in Phase 11), Phase 9 item 5's closure and item 18's correction (code and capture).
- Runs 1–2 "before commit 1": leg built `22:43:05Z`, commit 1 `23:28:34Z`.

**WHAT YOU COULD NOT CHECK**

Anything live (no service, no trio); the built-app wiring comparison and the mutation check (need canopy's environment); the node tests; the renderer under dash 4.4.1; commit signatures; whether the `:8052` leg hot-reloads (finding 2's assumption); the Linux-host worktrees of item 29.

**SECRETS/PII:** none read or printed; no `.env*` opened; git used read-only with `--format='%h %s'`; GitHub queries printed dates and SHAs only.

## Lane 12-C (cross-document consistency)

**Lane 12-C** (cross-document consistency, round 1)
**VERDICT: SOUND-WITH-FIXES**

**TABLE**

| check | result | evidence |
|---|---|---|
| Phase 11 items 0, 24, 25, 26 vs Phase 12's closures | agree | ledger 11227-11234, 10534-10548 (Phase 11 text) vs 11571-11586; item 24's reader change quoted verbatim; item 0's allow-arm ask traces to Phase 9 item 0 (9716-9718) |
| Phase 10 item 18 watchdog sentence | quoted exactly | 10550-10551 "strand a page's metrics poll for about 30 s (the watchdog's 30 s, counted from a 5 s slow tick)" = 11581-11582 |
| Phase 9 items 0, 4, 5, 14; Phase 8 item 6 | agree | 9693-9722, 9728, 9730-9732, 9777-9787 (fourth rule = window/floor sizing), 8472-8474 (clamp defeat) |
| Phase 11 line citations re-used by Phase 12 | agree | `467-472`/`4734-4737`/`:313`/`194-197`/`2514-2522`/`412-424` at 10716-10727, 11231-11232; "none runs the predicate" 10757-10760 |
| Counts arithmetic Phase 11 → 12 | agree | 79/53/1/2/23, 7 P1, 16 P2 (11190-11196) → 79/56/1/2/20, 4 P1, 16 P2; triage output identical |
| Three headers: `FIXED` in last 170 chars; severity first-token | pass | tails 170 all contain FIXED, no OPEN; F-068 first token P1 (REFERENCE.md § Canopy E2E Finding Triage: dispositions from tail, severity first match in full body); triage prints FIXED P1 for 055/058/068 |
| "Still owed" numbering | 27, 28, 29 new, nothing renumbered | 11588-11605; Phase 11 ended at 26 |
| F-CANOPY-025 / canopy#514 (item 27's premise) | **disagrees with Phase 9** | see Finding 1 |
| canopy#731 merge, commits, review thread | agree | `gh pr view 731`: MERGED 2026-10-09T02:27:27Z, merge `25c5c887`, head `13834945`, 8 commits `7aed1f2b b344ff97 957176de 2689a207 65ead946 13dcc58a d777a86e 13834945`; 1 thread, resolved, CodeQL `_PACED_POLLS` at `dashboard_manager.py:520` |
| v0.9.0 release | agree | published 2026-10-17T19:45:37Z, target `bd001153` (tag → commit) |
| CHANGELOG `[0.9.0]` at `bd001153` | agree | `## [0.9.0] - 2026-10-10`; pacer entry is the first `### Fixed` item, names 055/058/068, 30 s/120 s bound, cost, `[0.8.0]` "could not do" correction |
| PyPI | agree | juniper-canopy 0.9.0, uploaded 2026-10-17T22:08:40Z |
| ml#2196, ml#2183 | agree | `0174c3dd` 2026-10-09T02:36:55Z (`docs/canopy-pacer-731-evidence`); `0fca7ada` 2026-10-08T12:55:46Z (`docs/canopy-e2e-phase11`) |
| Named paths exist | 22 of 23 | **missing** `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` (Finding 2); `util/ad-hoc/2026-10-19_phase12_*` and `consensus/2026-10-19_*` not yet created (Finding 5) |
| Verification commands (runnable here) | all match | triage tail -7 = 79/56/1/2/20, P1 4, P2 16; analyze head -3 = `served 2689a207…`, 304 A / 0 X, 3991/5179/6655 ms (= table row 4); lsof: nothing |
| Renderer-check scores | agree | `20261008T201631_pacer_score.json` 172/171, idle 145/0; guard 198/197, 70+18 = 88 evicted |
| Parent handoff item 4 / O17 / items 5, 7 / O13 | consistent | O13 = who may stop the trio (line 450) ↔ item 28; item 7 cleanup ↔ item 29; O17 note's 4/16 or 3/17 ↔ Phase 12 Matrix |
| INDEX P2 row | consistent | Phase 11 = ml#2183 (verified), six rounds (ledger Phase 11 has round 6) |
| SUPERSEDED banner | consistent | 10-08 handoff items 1-3 = #731 merge, ml PR, Phase 12; items 4-6 = 25, 26, parent 5/7/O-batch — carried as handoff items 2, 3, 7 |
| Dates/tenses | consistent | UTC `Z` for merges/release, CDT for runs, both labelled; CHANGELOG 10-10 vs Release 10-17 stated side by side in Phase 12 Summary and item 4 |
| Lint | no blocking issue | see Finding 6 |

**FINDINGS**

1. **MAJOR** — Phase 12 item 27 contradicts Phase 9 on the allow arm's history.
   Text (ledger 11590-11591; echoed by handoff item 4 and parent item 4 "F-055's Live Switch allow arm"): "F-CANOPY-025's gate is computed inside the status-bar feeder, which now applies, so the arm is inferred reachable again; it has not been driven since canopy#514's own verification."
   Evidence: Phase 9, ledger 8898-8906, "**F-CANOPY-025's allow arm, driven on demo legs** (new `2026-09-23_f055_f025_allow_arm_demo_drive.py` …)" with a table: `:8058 884d22fb` (first fix) ALLOW **LANDS** 13.0 s, DENY RETURNS 7.8 s; `:8059 78c057e2` (parent, `src/` = `ce78e0de`) LANDS 19.7 s. Phase 9 Matrix (9672-9674): "F-CANOPY-025: stays counted FIXED. Its allow arm lands on F-055's first fix and on a demo parent page, so Phase 8's 'inferred regressed' is not established." Phase 9 is right: it holds the drive record; Phase 12 ran nothing and re-states Phase 8's inference.
   Fix: in item 27 (and the two handoff echoes) replace the clause with "last driven 2026-09-23 on demo legs (Phase 9), where it landed on the unfixed parent as well; never driven on a page at the trio's latency, nor on the pacer", and drop "inferred reachable again" (Phase 9 already found it not established as regressed).
   Changes a number, disposition or action? no — the drive stays owed; its stated reason changes.

2. **MINOR** — Dead path. Text (ledger 11592; handoff line 71): "per `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`". No such file; the document is `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` (renamed under the 2026-07-04 convention). The short name is inherited from the 10-08 and 10-03 handoffs, but this commit writes it twice more. Fix: use the full filename in both places. Changes a number, disposition or action? no.

3. **MINOR** — The new handoff disagrees with itself on where item 27 runs. Goal statement (lines 16-17): "Items 25, 27 and 28 need a host that can run a canopy verify leg against the trio". Item 4 (line 62-63) and ledger item 27: "on a leg … whose training may be started (never the trio)". Phase 9 (8899-8901) ran the arm in `CANOPY_VERIFY_DEMO_MODE=1`, cascor URL pointed at nothing. The item text is right. Fix: "Items 25 and 28 need a verify leg against the trio (the Linux host); item 27 needs a demo leg that trains, never the trio; item 26 runs anywhere." Changes a number, disposition or action? no.

4. **MINOR** — The filename rule. The new handoff references "the CAN-015g/h design note" (item 3), "canopy's manual" (item 3), "the pacer-live README" (Traps) and "a project note on the canopy E2E arc's state" (Changed, auto-memory) without filenames; two or more documents are cited, so every reference must carry one. Fix: `notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`, canopy `docs/USER_MANUAL.md`, `reports/e2e-canopy-2026-09-02/pacer-live/README.md`, and the memory note's filename. Changes a number, disposition or action? no.

5. **MINOR** — Anticipatory claims not yet true. Handoff "Git state": "landed from turing through the API as signed commits"; "Completed": "This session's PR carries … Phase 12's consensus records"; "Created": `consensus/2026-10-19_validator_reports_phase12_round*.md`, `util/ad-hoc/2026-10-19_phase12_ledger_round*_corrections.py`. Evidence: `gh api repos/pcalnon/juniper-ml/branches/docs/canopy-e2e-phase12` → 404; `gh pr list --head docs/canopy-e2e-phase12 --state all` → `[]`; neither glob matches a file. Expected at a round-1 freeze (the file says CONSENSUS_ROUNDS_PENDING), but the final text must be re-run against these three checks after landing. Fix: none now; verify before the PR is marked ready. Changes a number, disposition or action? no.

6. **NIT** — Lint. The pre-commit markdownlint hook excludes `^(…notes/|docs/|prompts/…)` and CI runs pre-commit, so none of the five files is linted; `pre-commit` was not run (its hook carries `--fix`). `markdownlint-cli2` (newer than the pinned cli v0.42.0; MD060 ignored) reports on the diff: MD026 trailing "." in the new handoff's H1 (6 of 62 existing handoffs do the same); MD013 on the INDEX P2 row, 914 chars (was 701), and the F-058/F-068 headers, 674/939 (were 522/784) — all already over 512, nothing newly crosses. The F-068 header's "else P2" prose is pre-existing and harmless under the first-token rule. Changes a number, disposition or action? no.

7. **NIT** — Two conventions worth a glance, not defects of this diff: (a) item 18's watchdog sentence is corrected by annotation in Phase 12 only; Phase 10's text at 10550 stands, as the ledger's append-only practice allows; (b) `reports/e2e-canopy-2026-09-02/pacer-live/README.md:16-18` labels runs 1-4 "F-055 census" though they are the F-058 census v2 files (`f058-census-run*.json`); Phase 12 names them correctly (11393). Changes a number, disposition or action? no.

**WHAT YOU COULD NOT CHECK**

- The 2026-10-08 session's transcript-only claims Phase 12 repeats (6,819 unit tests, 25 CI checks on `2689a207`, the "condensed in transcription" lane reports, the `uptime` readings).
- The Traps' host claims: the 2026-10-19 network probe (5 GHz, SNR 41 dB), "two of this phase's three headers first failed" the 170-char rule, the worktree-guard behaviour list.
- Auto-memory files outside the repo; the Linux host's two worktrees (item 29); whether `agile-napping-popcorn`'s staged copies equal what ml#2196 merged.
- `pre-commit run` (would rewrite files; the markdown hook excludes these paths anyway); commit signature status of the five #731 commits (not re-probed).
- Anything live: no service, no trio, no browser on this host.

**SECRETS/PII:** none printed; no `.env*` read; `git log` used `%h %s` only; no e-mail address, token or environment value appears above.
