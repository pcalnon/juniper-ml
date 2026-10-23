<!-- markdownlint-disable -->

# Canopy E2E ledger Phase 15 — validator report, round 3 (2026-10-21)

Round 3 was one lane, Lane 15-R3, on the round-3 freeze 71417d33, scoped to round 2's corrections and the handoff (reports/e2e-canopy-2026-09-02/drafts/lane15R3_phase15_ledger_brief.md). It changes no number, disposition or action, so the review ended with it (§4 of the consensus procedure). The archive tool labels the section 'round 1' because this agent was never resumed; it is the procedure's round 3. Archived verbatim by util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py.

## Lane 15-R3 — round 2's corrections and the handoff (round 3)

*agent `a73d511d3acc8d9cf` · round 1 · last-assistant-text (not resumed) · 26152 chars*

# Lane 15-R3: round 3 of the canopy E2E ledger's Phase 15 (round 2's corrections and the handoff)

**Verdict: SOUND-WITH-FIXES.**

**This round changes no number, no disposition and no action.** Under the procedure's termination rule (§4), the review ends with this round.

In summary:

- **The five MAJOR corrections are true** against the evidence round 2 cited. MAJOR 1 missed one place in the repo (a driver comment) and one outside it (auto-memory).
- **Thirteen of the fifteen MINOR corrections are true as applied.** MINOR 8 was applied in part, and what it left no longer matters. MINOR 10 was applied with a deviation that the consensus record does not disclose.
- **The handoff's verification commands** all print what their comments say, but one comment names the wrong item.
- **The handoff's remaining tasks** are all present and sensibly ordered. Three of them would be easier to act on with an instrument named.
- **The replay** prints MATCH for all six files and ABSENT for the draft name.
- **The counts stand:** 80 / 63 / 1 / 2 / 14, with 0 P0, 4 P1 and 10 P2. F-CANOPY-069 is FIXED at P0 and F-CANOPY-028 is FIXED at P1.

**What I reviewed**

- **Worktree HEAD:** `71417d33ed991727cbbf7a7261e48b423344b2c9`. That is the round-3 freeze over the round-2 freeze `f65541a5`, on the session's base `907b6b3e`. `git status` shows only the untracked `item31-turing/shots/`.
- **The corrections:** `git diff HEAD~1 HEAD` (14 files), the round-2 pass `util/ad-hoc/2026-10-21_phase15_ledger_round2_corrections.py`, and round 2's report.
- **juniper-ml `main`:** `origin/main` is `2f831b60` (#2300), equal to the remote's `main`.
- **canopy `main`:** `aeeaf29b`.
- **Ground rules:** I wrote nothing in the worktree, installed nothing and started no service or leg. The one fix-leg call used a malformed sha: it exited 2, and nothing listens on :8062. My scratch is under `/private/tmp/claude-501/lane15R3/`.

## The corrections, one by one

### MAJOR 1 — F-CANOPY-028's account. TRUE, but one place in the repo was missed

**The gaps.** The driver's log lines and its request timestamps use the same clock (`time.time() - _T0`, `2026-10-20_item30_fixwave_redrive.py:93` and `:174`). I measured from each arm's `after reload:` line to its third `pin writer fired` line:

| Parent arms | Gaps (s) | Ledger |
|---|---|---|
| `delay2`, `delay4` (4) | 6.61, 5.40, 5.74, 5.87 | 5.4–8.1 ✓ |
| early forced (6) | 6.76, 8.06, 7.14, 6.41, 7.53, 6.32 | (same range) ✓ |
| settled forced (6) | 3.32, 2.08, 1.28, 2.51, 2.34, 3.35 | 1.3–3.4 ✓ |

- The parent's other delays (6–14 s) give 1.7–5.1 s.
- On the fix the same gaps are 6.2–8.7 s for the early-like arms and 1.2–3.6 s for the settled ones. Round 2's 1.2–3.6 s was therefore the parent's and the fix's settled arms together; see D4.

**The pin step comes before the second render; the click comes after it.**

- In all four parent 2 s and 4 s arms and all six early forced arms, the `after reload:` line itself was logged before the second render's writer firing: by 2.2–5.2 s and 4.3–6.1 s respectively.
- Yet in all 26 parent drives the click's writer came after that firing.
- Over the delay sweep, the second render came 6.64–9.04 s after the mount render and the click 0.585–9.548 s after the second render. The ledger's 6.6–9.0 and 0.6–9.5 are right.

**The body argument holds for all 26.** Each drive has three firings: the second reads `learning_rate` alone over 22 boxes, the third both, with State `["learning_rate"]`. `early#2`'s third body (`item30-turing/demo_leg_8062_dash441.json`) is 22 triggered, `learning_rate` checked and `max_iterations` not, State `["max_iterations","learning_rate"]`. That is the reset the argument relies on.

**The driver.** Between `:536` (`second_pin_at_s_after_reload`) and `:544` (`pin_click`) run:

- `pin_state`, `ls_get` and `text_of` (three evaluates);
- the log line (`:540`);
- `shot` (`:541`);
- one more `ls_get` (`:543`).

The ledger's "three page evaluates, a log line and a screenshot" is right up to the screenshot. The screenshot step is unchanged since `907b6b3e`, so Phase 14's early arms had it too.

**The renderer (dash 4.4.1 `dash_renderer.dev.js`).**

- `getReadyCallbacks` (`:1708-1757`) holds a requested callback while any of its Inputs, less its own Outputs, is an output of a pending callback, or of anything downstream of one.
- `getPendingCallbacks` (`:4097`) counts every callback list except `stored` and `completed`, so an in-flight writer counts as pending.
- So the table render (Inputs: the params store and the pin store) is held while the writer (Output: the pin store) is pending.
- The writer is never held behind the render: its Inputs are the `param-pin` values, and no callback outputs one.

**The records show the writer was in flight when the forced write landed.** In all 12 parent forced arms, the driver's first store poll after the write still read `["learning_rate"]`. The change was read 0.4–1.3 s after the click at the settled timing and 1.1–3.0 s after it at the early timing. So the render the write requested did have to wait.

**The eviction residual (`:3379`).** It is true, with one precision:

- An in-flight call sits in `watched`, not `executing`: the executing observer (`:2846-2905`) moves calls with a pending promise there.
- The eviction is the `wDuplicates` removal (`:3243-3245`), dispatched on the same line, `:3379`.
- The evicted call's result is dropped at `:2884-2890`.

See D10 (optional).

**Places that carried the old account.** Corrected:

- the F-028 "Driven" paragraph;
- the item 31 section;
- "cannot support";
- the handoff's Completed bullet and its trap;
- the driver's `:503-508` and `:515-520` comments and both help strings;
- both pass scripts' headers;
- canopy#761: the 05:30Z drive comment stands, and a 06:34Z follow-up corrects it and names item 34.

**Not corrected:**

- **In the repo:** the driver's comment on the forced write itself (`:546-550`) still states the premise round 2 refuted (D3).
- **Outside the repo:** auto-memory `canopy-e2e-arc-state.md:16` still says "the click's writer queues behind the second render" and that the forced arm reproduces `early#2`'s order (D12).

The apply pass `2026-10-20_phase15_items31_32_apply.py` keeps the old text by design, because later passes replace it.

### MAJOR 2 — item 31b. TRUE and complete

**The manual and the parser.**

- canopy `main` is `aeeaf29b`. I fetched `docs/USER_MANUAL.md` and `src/frontend/components/network_editor_panel.py` from `main`; both are byte-identical to the `-f028` tree's copies.
- `:500` reads "Values are floats separated by commas or spaces."
- `_parse_float_list` (`:418-434`) turns newlines and semicolons into commas, then splits on commas only.
- `float('0.1 0.2')` raises `could not convert string to float: '0.1 0.2'`.
- The function's docstring says "comma/whitespace-separated".
- `_parse_float_rows` splits values within a row on commas and whitespace. So the sentence is right for `output_weights`.

**Item 34 is stated right and carried everywhere:**

- the ledger's Still owed and item 34 (`:13224-13226`, `:13252-13256`);
- the handoff's title, goal, Completed list, Remaining 2, and Remaining 8 ("after item 34");
- the INDEX's Next list;
- the parent's pointer (`:132-136`);
- the banner ("new items 33 and 34").

### MAJOR 3 — items 18–21. TRUE and complete

Handoff item 3 matches Phase 10 (`:10841-10869`) and Phase 13's re-statement (`:12589-12592`). Its `grep -n '^18\. \*\*F-CANOPY-064'` finds `:10841`. Its summary of item 18 names two of that item's three drives (D7).

**Every Still-owed item, 0–34, and what carries it:**

| Items | Carrier |
|---|---|
| 0, 5, 24, 30, 32 | closed (Phases 12, 12, 12, 14, 15) |
| 1, 2, 6, 7, 8, 11, 12, 13, 14 | the parent's item 5 |
| 9 | the parent's item 5 (test gap / M-TOPOLOGY-16) and O6 (M-DATASET) |
| 3, 4, 10 | O6 |
| 15 | O2, O4, O5 |
| 16 | done; its fixture sweep moved to item 19 |
| 17 | O3 |
| 18–21 | handoff item 3 |
| 22 | O9 / the parent's C4 (handoff item 10) |
| 23 | **no carrier**. It is done in fact: the INDEX's P2 ↔ P3 row says P3 was told on 2026-10-08, under its item 11. But no Still-owed list marks it DONE (D13, optional). |
| 25, 28, 29 | handoff item 5 |
| 26 (second step) | handoff item 7 |
| 27 | handoff item 4 |
| 31 | done, except (b), which moved to item 34 |
| 33 | handoff item 6 |
| 34 | handoff item 2 |

### MAJOR 4 — item 33. TRUE and complete

**The venv layout.** I ran read-only `pip show` and `pip list` with the E2 venv's interpreter.

- `venvs/JuniperCanopy1/pyvenv.cfg` has `include-system-site-packages = true` over the conda env `JuniperCanopy1` (Python 3.14.2).
- The venv's `juniper-canopy` 0.9.0 is an editable install of `trees/juniper-canopy`, which is `571743db` with floor `dash>=3.0.0`.
- dash 3.3.0 comes from the conda env. pydantic is 2.12.5. comm and janus are absent.

**The floor and PyPI.** The fix tree's floor is `dash>=4.0.0`, with no upper bound. PyPI's newest dash is 4.4.1; 4.5.0rc1 is a pre-release, which pip skips.

**So the recipe works.** After the re-sync, `<venv>/bin/python -m pip install -e <tree>` installs dash 4.4.1, comm and janus into the venv, where they shadow the conda env's 3.3.0. That brings the legs and the E2 lanes to 4.x, since the E2 runner tests in that overlay.

What it leaves unsaid (D8):

- the conda env itself stays at 3.3.0 on this route;
- `util/ad-hoc/2026-10-19_turing_e2_validate_envs.py canopy --phase all` already does the re-sync, the install and the lanes in one run.

### MAJOR 5 — item 27. TRUE and complete

**The drive script.** `2026-09-23_f055_f025_allow_arm_demo_drive.py` samples, once a second, `live-dataset-switch-button`'s `disabled` and the text of `top-status-display` and `top-epoch-display`. Its only modal reference is `ensure_no_modal`. The ids the extension needs exist on `main`:

- `live-switch-accept-button` (`:2271`);
- `live-switch-progress-alert` (`:2303`);
- `restart-progress-alert` (`:2432`);
- the two `running=` specs (`:6349-6351`, `:6513`).

**The wrapper.** In `2026-10-20_f069_fix_leg.bash` the sixth argument defaults to `571743db…` and must match `^[0-9a-f]{40}$`. I ran it with the handoff's arguments and `aeeaf29b` as the sixth: it exited 2 with its usage line, and nothing listens on :8062.

**Item 4's command lines are complete and runnable.**

- I ran the blob check exactly as written (read-only). It prints MATCH for all 12 files, then ALL MATCH.
- The 12 are the union of #760's and #761's files, less `requirements.lock`. Checked separately, `requirements.lock` is the one file that differs.
- The launch line's sha is canopy `main`'s, and its interpreter and tree exist.

**Two gaps:**

- The handoff names no interpreter for the drive, and not where the chrome channel and the CDN abort live (D9).
- It does not warn that `legs/serving-commit` still reads `571743db`, which the plain launcher stamps on a leg of a re-synced E2 tree (D11).

### The MINORs

| # | Verdict | Evidence |
|---|---|---|
| 1 | true | Restart: the opener answered at +0.638 s, the worker at +2.61 s, and the alert's DOM life was 1.906 s (`pair_members.json`). |
| 2 | true | The fix legs' restart responses came at +1.043 s and +1.205 s, the Live Switch's at +0.705 s and +0.262 s. |
| 3 | true | `early#2`'s third body is as stated. The unit test's `ALL_KEYS` is `learning_rate, max_iterations, patience, output_epochs`. |
| 4 | true | The driver returns before M-06 unless `arm == "settled"` (`:573`). Every record has M06 unset, and M04 and M05 true. |
| 5 | true | The conda file pins `comm=0.2.3`, `janus=2.0.0`, `dash=4.4.1` and `pydantic=2.12.5`, which meets `pydantic>=2.10`. |
| 6 | true | canopy#760's body says the fix does not depend on the dash version and that keeping `>=3.0.0` would need a CI lane at the floor. It does not say 4.0.0 is untested, so the credit split is right. |
| 7 | true | At `:13156`, `:13168-13169` and `:13179-13181`. |
| 8 | partly applied | The replay's pass list and command were fixed. No "(at landing)" marks and no landing check were added. MEMORY.md has since been updated: its canopy line names Phase 15, and it is 6,059 bytes. What stays unmarked is the PR, the branch and the round-3 files, which are landing-time by design. |
| 9 | true | `push_signed_commit.py:212` takes `--expected-head`; `safe_merge.py`'s arguments (`:1153-1179`) do not. |
| 10 | applied with a deviation | The facts are true. But the sentence keeps a same-day check of `conf/requirements_ci.txt` and `test_poll_gating.py` that "kept no record". Round 2, reading the records, called run 3 their first check: runs 1 and 2 (18:12Z and 18:14Z) hold neither file, and run 3 (2026-10-21T05:23:58Z) holds both. The record does not say so (D5, D6). |
| 11 | true | With the `watched` precision above. |
| 12 | true | `forcedearly` takes the early-like path (`:524`, `:532`) plus the forced write. Pass 1's records show `values_after_s` unset and a pin step of 2.6–3.2 s, which that path produces. Pass 1's script now calls `forcedearly`. |
| 13 | true | Three PNGs, all timestamped 15:52 (the last arm), untracked. |
| 14 | true | M-PARAMETERS-04's row is rewritten. |
| 15 | true at all four sites | `_callback.py:311` (3.3.0) and `:338` (4.4.1) are `callback_map[callback_id] = {…}`, with `callback_id = create_callback_id(output, inputs, no_output)` (`:290`, `:315`). That id is the whole output string. `pair_members.json` serves both members of each pair. Phase 14's consensus record (`:12951`) still quotes Lane 14-B's "the registry overwrites"; it is a record of what a lane said, so I leave it. |

**Is the round-2 consensus record faithful to the report?** Yes, with two exceptions:

- "all five MAJORs and fifteen MINORs as proposed" (D6);
- the scope of the recomputed click gaps (D4).

## The handoff

**The verification block.** Every command prints what its comment says; `python3` resolves to JuniperPython.

| Command | Output |
|---|---|
| `git log --oneline -3` | `71417d33`, `f65541a5`, `6f933d07` |
| `gh pr list … --head docs/canopy-e2e-phase15` | `[]`, expected before the landing |
| the triage | 80 / 63 / 1 / 2 / 14; open P1 4; open P2 10; no open P0 line |
| the open-P1 count | 4 |
| `grep -c '^## Phase 15'` | 1 |
| `gh pr view 760` / `761` | MERGED `fbf01dff` / MERGED `aeeaf29b` |
| `gh release list` | v0.9.0 Latest, 2026-10-17 |
| the fix matrix | two ALIVE |
| the stuck-spinner check | True, True on the parent labels; False, False on the fix |
| `ls` of the venvs | the seven named |
| `lsof` | nothing |

One comment is stale. The release line says the output "means item 7 is still owed", but round 2's renumbering made the canopy release item 8 (D1).

**Remaining tasks.** All present, in a sensible order:

1. land the PR;
2. item 34;
3. items 18–21;
4. item 27;
5. items 25, 28 and 29;
6. item 33 (the owner's);
7. item 26's second step (on O17);
8. the canopy release (the owner's, after item 34);
9. cleanup;
10. the parent's items 5 and 7, and O1–O17.

Against the other lists:

- **The Phase 14 handoff's items 1–7:** all done or carried.
- **The parent's items:** 1–4 are done, 5 and 7 are carried, and 6 is moot (MEMORY.md is 6,059 bytes). Items 8–11 belong to Lanes B and C.
- **The ledger's items 0–34:** see MAJOR 3.

Actionability gaps: D7, D8, D9 and D11.

**The Changed list** matches the 49 paths of `git diff --name-status 907b6b3e HEAD`, plus the round-3 pass and report:

- scripts created: 10, plus the round-3 pass;
- item 32 records: 8;
- item 31: 7 driver records, 2 Lane 15-A records and 9 logs;
- briefs: 4;
- reports: 2, plus round 3's;
- the new handoff;
- modified files: 6.

One Completed line is stale: "the matrix (M-PARAMETERS-06's cell)" (D2).

**The banner, the parent's pointer and the INDEX row** agree with the handoff and the ledger:

- the banner's mapping of the Phase 14 handoff's items 1–7;
- the pointer's counts and items 33 and 34;
- the INDEX's Next list and its "two … pairs … three output ids".

## The replay

I ran `python3 -I util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py --out-root /private/tmp/claude-501/lane15R3/rebuild`.

- `origin/main` is `2f831b60`, equal to the remote's `main`.
- All three passes exit 0.
- It prints MATCH for the five shared files and the new handoff, and ABSENT for the draft-named handoff.

So no shared file has moved on `main` since the base, and there are no hand edits. A masked scan of the round-3 diff's added lines found no e-mail or key shape.

## Defects

**All are MINOR. None changes a number, a disposition, an item or an action.** D10, D13 and D14 are optional.

**D1. Handoff `:174`, a verification comment.**

- Current: `gh release list --repo pcalnon/juniper-canopy --limit 2   # v0.9.0 Latest (2026-10-17) means item 7 is still owed`
- Replace with: `gh release list --repo pcalnon/juniper-canopy --limit 2   # v0.9.0 Latest (2026-10-17) means item 8, the canopy release, is still owed`

**D2. Handoff `:63`.**

- Current: "**This session's PR** carries the ledger, the matrix (M-PARAMETERS-06's cell), this file,"
- Replace with: "**This session's PR** carries the ledger, the matrix (M-PARAMETERS-06's status cell and M-PARAMETERS-04's Expected cell), this file,"

**D3. `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py:546-550`, the forced write's comment.** It still states the refuted premise, and it ships in this PR.

- Current: "# item 31 (F-CANOPY-028): reproduce early#2's order on purpose. A params-store write dispatched inside the click's own store-write latency rebuilds the tables from the pin set the renderer holds at dispatch (the pre-click set); the rebuild's writer firing then carries the new pin unchecked, and a writer that merges the rendered set persists that over the click. The payload is {} (the tables render their defaults until the next poll); only the checkbox column takes part."
- Replace with: "# item 31 (F-CANOPY-028): the forced write, written to reproduce early#2's order. It cannot: the table render a params-store write requests is held behind the click's in-flight writer (the pin store is the writer's Output and the render's Input), so the rebuild reads the post-click pin set, whereas early#2's stale render was requested BEFORE the click's writer (ledger Phase 15, round 2). The payload is {} (the tables render their defaults until the next poll); only the checkbox column takes part."

**D4. The scope of the click gaps.** Ledger `:3233-3234`:

- Current: "and the click's writer went out 5.4–8.1 s after that log line in the 2 s, 4 s and early forced arms (1.3–3.4 s at the settled timing, nothing pending)."
- Replace with: "and on the parent the click's writer went out 5.4–8.1 s after that log line in the 2 s, 4 s and early forced arms (1.3–3.4 s in the settled forced arms, nothing pending; on the fix 6.2–8.7 s and 1.2–3.6 s)."

And the consensus record, `:13203-13204`:

- Current: "the click gaps recomputed from the logs (5.4–8.1 s early, 1.3–3.4 s settled)"
- Replace with: "the click gaps recomputed from the logs for the parent's arms (5.4–8.1 s early, 1.3–3.4 s settled; round 2's settled 1.2–3.6 s included the fix's arms)"

**D5. Ledger `:13074-13077`, the provenance sentence (MINOR 10).**

- Current: "so their target `conf/requirements_ci.txt` was checked instead, with `test_poll_gating.py`, in a check the same day that kept no record: re-run against the same unchanged tree and recorded on 2026-10-21 as `…_run3.json`, with three of the files the item 31 script touches)."
- Replace with: "so their target `conf/requirements_ci.txt` was checked instead, with `test_poll_gating.py`, in a check the same day that kept no record (the session's account; the first record of either is `…_run3.json`, 2026-10-21, against the same unchanged tree, with three of the files the item 31 script touches)."

**D6. The consensus record, `:13202-13203`.**

- Current: "all five MAJORs and fifteen MINORs as proposed,"
- Replace with: "all five MAJORs and fifteen MINORs as proposed, except MINOR 8, whose "(at landing)" marks were not added (its replay list was fixed, and MEMORY.md was updated before the landing), and MINOR 10, where the provenance sentence keeps the session's unrecorded same-day check, marked as such,"

**D7. Handoff item 3, `:86-87`.**

- Current: "18 F-CANOPY-064 (P1) and -067 (first decide -067's rating on unfixed `main` with the recurrence leg up and a canopy restart on an idle cascor; never the trio)"
- Replace with: "18 F-CANOPY-064 (P1) and -067 (first decide -067's rating on unfixed `main` in three drives: W8 step 13 after a CasCor run with the recurrence leg up, a canopy restart on an idle cascor, and the same restart mid-run; never the trio)"

**D8. Handoff item 6, `:104-109` (ledger item 33, `:13243-13248`, likewise).** After "(that venv, a system-site venv over the conda env, holds the editable canopy; pip takes the newest dash 4.x with `comm` and `janus`).", add:

> "Once the owner has pulled the canopy primary to `main`, `python3 -I util/ad-hoc/2026-10-19_turing_e2_validate_envs.py canopy --phase all` does the re-sync, that install (with the `[test,juniper-cascor,observability]` extras) and the lanes the E2 record cites in one run. On this route the conda env itself keeps dash 3.3.0, shadowed by the venv."

**D9. Handoff item 4, `:97-98`.**

- Current: "Then `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py`, adapted to the chrome channel and the CDN route, samples"
- Replace with: "Then `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py`, run with `~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python -I` (the interpreter `2026-10-20_item31_f028_drives.bash` gives the driver) and adapted to the chrome channel and the CDN route (`2026-10-20_item30_fixwave_redrive.py`'s `launch`, `:129-138`, and `_route_cdn` with `new_page`'s route, `:141-160`), samples"

**D10 (optional). Ledger `:3261-3262`, the residual.**

- Current: "dash evicts the older executing call (`dash_renderer.dev.js:3379` in 4.4.1),"
- Replace with: "dash evicts the older in-flight call (in 4.4.1 it sits in `watched`; the duplicate removal is dispatched at `dash_renderer.dev.js:3379` and its response is dropped at `:2884-2890`),"

**D11. Handoff Traps.** Add after the driver trap (`:146-151`):

> "- **`~/.local/state/juniper/turing-e2/legs/serving-commit` still reads `571743db`**, and `2026-10-20_turing_canopy_leg.bash` stamps it on `/v1/health` whenever no sha is passed. After a re-sync of the E2 tree (items 27 and 33), launch through `2026-10-20_f069_fix_leg.bash` with its sixth argument, or rewrite that file only after the blob check prints ALL MATCH for the new commit."

**D12. Auto-memory `canopy-e2e-arc-state.md:16` (outside the repo; the handoff lists it as changed).**

- Current: "a parent sweep (dash 4.4.1 leg 8062) showed no loss at fixed delays 2–12 s (the click's writer queues behind the second render), so the loss needs early#2's order, which the `forced` arm reproduces (a params-store write 150 ms after the click)."
- Replace with: "a parent sweep (dash 4.4.1 leg 8062) showed no loss at driver delays of 2–14 s: every click landed after the second render (the driver clicks seconds after its pin step, behind a screenshot), and a params-store write 150 ms after the click (the `forced`/`forcedearly` arms) cannot stage early#2's order, because the renderer holds its render behind the click's writer."

**D13 (optional). Ledger Phase 15 Still owed.** After the items 18–21 bullet (`:13227-13228`), add:

> "- **Item 23 is DONE**: the defect-register arc was told on 2026-10-08, under its item 11 (the INDEX's P2 ↔ P3 row); no Still-owed list had marked it."

**D14 (optional). "The write is held" should be "the render it requests is held".** Three places:

- **Ledger `:13112-13113`.**
  - Current: "a synthetic params-store write 150 ms after the click is held behind the click's writer and cannot stage `early#2`'s order"
  - Replace with: "the table render a synthetic params-store write 150 ms after the click requests is held behind the click's writer, so it cannot stage `early#2`'s order"
- **Handoff `:54`.**
  - Current: "which the renderer holds behind the click's writer"
  - Replace with: "whose table render the renderer holds behind the click's writer"
- **Handoff `:149-150`.**
  - Current: "A params-store write after the click (the forced arms) is held behind the click's writer by the renderer (the pin store is the render's Input)"
  - Replace with: "The table render a params-store write after the click requests (the forced arms) is held behind the click's writer by the renderer (the pin store is the writer's Output and the render's Input)"

## What I could not check, and why

- **No page-clocked click time.** No leg or drive may run, so the click-time account rests on the logs, the request bodies, the driver's code and the renderer's source, plus the store-poll evidence above.
- **I did not run canopy's tests.** That would mean writing into a tree. So "7 of 9 fail on `571743db`" and "`test_callback_map_and_served_list_agree` passes on `571743db`" stay read, not run.
- **I did not run item 33's recipe**, because nothing may be installed. It is judged from pip's resolution rules, the venv's contents and PyPI's version list.
- **dash 4.2.0** (the Linux host's version) is not on this host.
- **Why the render after the click's own write fires no writer call is not established** from the source. Every arm has three firings and none after the click. The ledger makes no claim about it, and nothing here depends on it.
- **The session's unrecorded same-day blob check (D5) cannot be verified,** only bounded by the records.
- **Landing-time statements cannot be checked before the landing:** the PR, the branch, the round-3 pass and report, round 3's entry in `DEFAULT_PASSES`, and the placeholders. Nor can a concurrent upload that reverts lines after the merge.
- **A note for future briefs.** The `pip show juniper-canopy` the brief names prints the package's author e-mail field. I have kept it out of this report. Filter it, for example with `| grep -E '^(Version|Location|Editable project location):'`.

---
