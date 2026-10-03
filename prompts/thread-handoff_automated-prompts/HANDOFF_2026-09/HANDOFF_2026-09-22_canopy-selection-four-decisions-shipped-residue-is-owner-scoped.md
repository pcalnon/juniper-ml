# Thread Handoff — the four owner decisions are shipped; the residue is larger than the predecessor recorded

- **Date**: 2026-09-22
- **Arc**: juniper-canopy model/dataset selection reachability (the "Recurrence cannot be selected" defect)
- **Session**: `velvety-pondering-frost` (`session_01AkuYSrqxuHKY19ZhVS24VW`)
- **Predecessor**: [`HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md`](HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md) — its § *Status as of 2026-09-21* addendum is this session's work-in-progress record and was corrected **five** times (the fifth is below, § Key context); **this document supersedes it**
- **Designs of record**: [`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md) (§12 closed at §12.9) and [`notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](../../notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md) (§5.6.1 records OQ-6's closure)
- **Validation**: three adversarial agents + one peer session returned **29 defects against this document's first draft**; all are folded in. See § Validation record — this document is not self-certifying.

---

## READ THIS FIRST — two numbering schemes, six colliding labels

Two documents in this arc both use `N<n>` labels and **six collide**. The predecessor mixed them
silently; this document's first draft used `N7` and `N10` in **both** senses, 92 and 16 lines apart.

| prefix used here | source | range |
|---|---|---|
| **`D-N<n>`** | `…SELECTION-REACHABILITY-DESIGN.md` — design decisions | N1–N13 |
| **`A-N<n>`** | the 2026-09-21 status addendum (juniper-ml#1977) — new items | N0–N10 |

Colliding: **N2, N3, N5, N7, N8, N10**. `D-N7` is OQ-6 (**answered 2026-09-22**); `A-N7` is the
registry-drift test (**deliberately not built**). `D-N10` is the hydration-before-`⊥` ordering
constraint; `A-N10` is canopy#368's `nn_model` mirror. **Always write the prefix.**

---

## Goal statement

Continue the juniper-canopy selection-reachability arc. **All four owner decisions taken on
2026-09-21/22 are shipped and verified on `main`.** What remains is not the predecessor's list
re-sorted: it is a mix of *accepted-but-unbuilt* deliverables, *record repairs this session's own
PRs created*, and *cross-repo work claimed by a peer*.

**Shipped this session — ten canopy PRs**, all merged (canopy `origin/main` = `9bffaba1`):

| PR | what it closed |
|---|---|
| #641 | `Scheduled Tests` red for **63 consecutive runs**; `contract/` + `performance/` ran in **no lane**. Dispatch verified `413 → 506 passed`, `4 → 0 errors` |
| #643 | `Y1` — protocol 22 → 27 methods; the guard reads the requirement from the **caller**, because a plain conformance test passes vacuously |
| #644 | canopy#625 shipped the render half; "nor forward" was never enforced |
| #647 | the data-client floor admitted a pre-decision-11 client (`A-N8`); **partially** closes canopy#559 |
| #648 | `A-N4` + `A-N9` — the `equities` evidence and the `task_type` vocabulary have both gone stale |
| #649 | the X7 health deadline sat on the runner's noise floor (predecessor item 10) |
| #651 | `A-N3` — a recurrence run's completion reason never reached the operator |
| #652 | **OQ-6 ratified** — model-primary, a conflict *clears* the dataset instead of snapping it |
| #653 | `A-N5` — availability has a third state, **unknown** |
| #654 | the WS-silent poll failure could not name which sentinel it saw; closes canopy#637 |

Plus **juniper-ml#1977, #1981, #1982, #1984, #2003**, and **juniper-data#409** filed.

> **The predecessor said nine.** It was ten: **canopy#648** was dropped from the list, and `A-N4`
> and `A-N9` vanished from the record with it. Both are restored as items 11 and 12 below.

**Remaining work.**

- **Items 1, 3 and 3b are ONE PR** — the design's **PR 2**
  (`…REACHABILITY-DESIGN.md:349`): §4.10 hydration on *both* axes plus `G7`.
- **Item 2 FOLLOWS it**, and may not precede it (`D-N10`,
  `…REACHABILITY-DESIGN.md:404-409`: *"§4.10 lands dataset-axis hydration **first** (PR 2), after
  which `⊥` appears only when the backend truly holds nothing"*).
- **4–8** are independent; **9–17** are record repairs and smaller gaps; **18–21** are § F items
  this document dropped and a peer restored; **22** is a live defect it never carried; **23** is
  already fixed (canopy#656) and is kept as the record of what shipped.

> **This line was wrong in the revision merged as juniper-ml#2021**, which said *"Items 1, 2, 3 and
> 3b … must be done in order"*. That puts `⊥`-at-mount **before** the hydration it depends on —
> contradicting `D-N10`, and contradicting item 2's own text two screens below. **Round 4's fix
> introduced it**: adding `3b` forced a rewrite of the range line, and the rewrite asserted an order
> without re-reading the ordering constraint it was restating.

> **Why `3b` and not a renumber.** Items **4, 6, 14, 15, 19, 21 and 22** are cited from outside this
> file — PR bodies, squash messages, and the peer addendum being added to
> [`HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md`](HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md).
> (Items 11 and 12 are cited only *within* this file; juniper-ml#2021 named the wrong set.)
> Renumbering would silently re-point every external citation, so the letter suffix stands.

---

## Remaining work

### A. Blocked on a prerequisite, not a ruling — do these as one sequence

**1. `§4.10` hydration, dataset axis (`X1`).**
`_init_params_from_backend_handler` (`src/frontend/dashboard_manager.py:8866`, `NUM_OUTPUTS = 29`
at `:8868`) has **29 outputs and not one is on the dataset axis** — no `nn-dataset-type-dropdown`,
`nn-dataset-schema-params`, `nn-dataset-typed-fields`, `sidebar-nn-model`, `model-selection-store`.
It hydrates 28 hyperparameter / spiral / element knobs plus `applied-params-store`. On reload the
dataset axis is whatever the mount seeded.

> **This line number moves.** `:8679` (09-12) → `:8715` (09-21) → `:8866` (today). Locate by
> symbol, never by line.

**2. `⊥`-at-mount (`OQ-N2` / decision `D-N13`) — RESTORED. The predecessor's item 2, dropped from this document's first draft.**
This is **owner-ACCEPTED work that is blocked, not closed**
(`…SELECTION-REACHABILITY-DESIGN.md:389-405`, OQ-N2 *"ACCEPTED, with a prerequisite (N10)"*;
`D-N13` at `:92`). Re-verified open on `main` today: `dashboard_manager.py:1400` seeds
`value=DEFAULT_DATASET_TYPE`, `:6085` does the same for `restart-ds-type`, and
`params-init-interval` appears **×11**.

`D-N10` is the ordering constraint: **hydration (item 1) must land before `⊥`-at-mount**, or two
writers race for the dropdown's value — the `§4.1`-vs-`§4.10` two-writer contradiction from the
09-05 consensus document `§4`, still unanswered.

> canopy#652 made `⊥` a state the **gate** can clear into. That is the *conflict* path. **Mount is
> a different writer and is untouched.** Do not read #652 as having closed this. A successor who
> does item 1 will otherwise finish the prerequisite with nothing telling them the deliverable exists.

**3. `Y3` — the read side of the model axis.** Unmentioned since the 09-08 handoff; verified open.
`src/main.py` has `@app.post("/api/model/select")` at `:4014` and **no GET route**;
`/api/train/status` (`:3764-3772`) returns `{"backend", "execution", **status}` with **no
`nn_model`**. So `current_nn_model` is write-only and a reload shows "Active: CasCor" over a
recurrence backend. Register entry: [`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md) §6.4.

**The design phases this as PR 2 alongside item 1**
(`…REACHABILITY-DESIGN.md:349` — *"§4.10 hydration, **both** axes (X1's dataset-side sibling, Y3)
+ **G7**"*).

> **Item 3 has NO guardrail, and that is a gap to close, not an omission to work around.** `G7`
> is **dataset-axis only** (below), and the design's §5 test table
> (`…REACHABILITY-DESIGN.md:274-291`) runs `G1a`–`G11` with **nothing covering the Y3 read side** —
> `G5` is about `swapped is False`, not about hydrating `nn_model`. So item 3 can ship fully broken
> with every guardrail green. **Specify a Y3 guardrail as part of this PR.**

**3b. `G7` — the guardrail that proves ITEM 1 worked. Do not build hydration without it.**
`…REACHABILITY-DESIGN.md:287` defines it: *"the mount **dataset** value equals the backend's staged
dataset (§4.10)"*, status **"fails — no hydration exists at all"**. The PR plan at `…REACHABILITY-DESIGN.md:349` puts it in
the same row as hydration, so it is not a follow-up: it is **item 1's acceptance criterion**. The
only `G7` anywhere in canopy `src/` is a header comment
(`src/tests/regression/test_selection_reachability_guardrails.py:13`) — **no test asserts it**.

> **`G7` cannot stand in for a Y3 test.** It compares a *dataset* value against the backend's
> *staged dataset*; no Y3 defect can make it fail. The revision merged as juniper-ml#2021 called it
> *"the acceptance criterion for items 1 and 3"*, which both overstates its reach and **conceals the
> missing Y3 guardrail above** — and contradicted this item's own heading in the same breath.

> **Both earlier revisions of this document quoted `…REACHABILITY-DESIGN.md:349` and stopped one token short of `+ G7`** —
> juniper-ml#2014's and #2018's alike, not #2018's alone. The result was a handoff that told a
> successor to build the feature and not the test that proves it. Verified 0 hits for `G7` in the
> revision merged as juniper-ml#2018.

### B. CLAIMED by a peer session — do not start these

> **These claims LAPSE at 2026-09-29T00:00Z. Until then they hold — do not start items 4 or 20.**
>
> **From 2026-09-29T00:00Z onward**, treat them as unclaimed and start them **unless** an **open
> PR** or a **pushed branch** carries the work. At that point, and only then, a *document* asserting
> the claim — this one, or the peer's addendum to
> [`HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md`](HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md)
> — stops counting as evidence that it is live; only an open PR or a pushed branch does.
>
> Without a lapse, a claim made by a session that has since ended blocks every successor
> indefinitely, and the successor cannot tell a busy peer from a dead one.

> **The revision merged as juniper-ml#2021 got this wrong in a way that inverted it.** Its
> "a document does not count; only a PR or a branch does" carried **no time qualifier**, and no PR
> exists for either item today — so read literally it cancelled "do not start" *immediately*, which
> is the opposite of a claim lapse. A rule about what happens *after* a deadline has to say so in
> the same sentence.

**4. `Y2` — model persistence for recurrence. Waves 2 and 3.**
**Design of record: [`notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md`](../../notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md)**
(juniper-ml#1949, #1950). §11 carries the owner rulings — a **bind mount** mirroring cascor (not a
named volume), no-deletion inherited from §6.4, and a third service status `"restored"` with
`restored_from`. §11.4 fixes the order: recurrence service → juniper-deploy bind mount → canopy wiring.

- **Wave 1 is SHIPPED**: juniper-recurrence#172, merged 2026-09-18T00:57Z — `POST`/`GET
  /v1/model/snapshots`, `GET …/{id}`, `POST …/{id}/restore`, `state="restored"`, and
  `JUNIPER_RECURRENCE_SNAPSHOTS_DIR`.
- **But it is not released.** Still under `[Unreleased]`; no release since
  `juniper-recurrence-v0.5.0` (2026-09-10); juniper-deploy still pins
  `ghcr.io/pcalnon/juniper-recurrence:0.5.0`. **The published image has no snapshot routes.**
  Cutting that release is **owner-gated**; the peer has explicitly declined to.
- **Waves 2 and 3 were never opened** — no branch or PR in juniper-deploy or canopy, and
  `recurrence_service_adapter.py` still has only `train` and `training_status`. Peer session
  `canopy` is doing both now.

The canopy-side defect: `main.py` gates the snapshot path on `backend.backend_type == "service"`;
the `else` branch writes cascor-shaped meta via h5py — zero LMU state — and returns
`"Snapshot created successfully"` with `"mode": "real"`.

> **There are THREE such conditions on that path, not two** — create, the **restore lookup**, and
> restore itself. The middle one is the one every count so far has missed: under a
> `RecurrenceBackend` the lookup returns **404 first**, because `_demo_snapshots` is populated only
> in demo mode. A peer session probed it with a `TestClient` against a git archive of canopy
> `886147b5` and measured **SAVE 201 `"success"` / RESTORE 404** — so the save silently lies and the
> restore cannot find what the save claimed to write.
>
> **Neither this item nor the design counts the third.**
> [`notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md`](../../notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md)
> §8 item 3 and §11.4 step 3 both name two. Peer session `canopy` **claims wave 3 and will handle
> all three there.**
>
> Cited by behaviour rather than line: the peer's line numbers are from `886147b5` and do not match
> a current checkout. Locate by the `backend_type == "service"` predicate on the snapshot routes.

> **That gate is deliberate, not an oversight.** `main.py` carries the A1-iii-a rationale beside it:
> *"recurrence also exposes `_adapter` but it is a `RecurrenceServiceAdapter` with
> cascor-incompatible semantics."* The fix is a **third branch**, never a widened predicate.

### C. Ready to do, no ruling needed

**5. `A-N10` — canopy#368's `nn_model` mirror.** `SetParamsRequest` carries **36** fields and
`StageDatasetRequest` **6**; neither carries `nn_model` (AST-verified; `extra` is not forbidden on
either). canopy#368 is OPEN with one comment (this session's, 2026-09-21T15:17Z).

**6. Consolidate the ad-hoc signed-commit drivers.**
**State the unit — three criteria give three different numbers**, and the predecessor, this
document's first draft, one agent and one peer each used a different one:

| criterion | count |
|---|---|
| files under `util/ad-hoc/` matching `signed\|commit`, on `origin/main` | **11** |
| of those, general existing-branch drivers (excludes the PR-opener `2026-09-10_open_signed_lockfile_prs.bash`) | **10** |
| reusing `open_signed_pr.create_signed_commit`, as sampled in a 14-commit-stale worktree | **6** |

**CORRECTED 2026-09-22 (peer re-probe). The paragraph that stood here was half wrong**, and its
error was the same class as the count above — a true fact about one thing offered as evidence
about another:

- ~~"a canonical helper is already promoted with a hermetic test"~~ — **true of the function,
  false of the job.** `create_signed_commit` is importable and **6** ad-hoc files reuse it, but
  the promoted *tool*, `util/open_signed_pr.py`, **refuses an existing branch by design**
  (`:46-47`: *"Refuses when an open PR already exists for the branch … and when the branch already
  exists — it never force-updates someone else's ref"*). That refusal is correct for a PR opener
  and is exactly why it cannot serve the existing-branch case. **No existing-branch driver has
  ever been promoted**, which is the whole of the open work.
- **The duplicated work is 4 files.** This set has now been counted **five** times and been wrong
  five times, so here is the whole taxonomy instead of a number — **do not re-derive it, and do not
  quote one of these figures without its row**:

  | figure | what it actually counts | files |
  |---|---|---|
  | **17** | mention `createCommitOnBranch` anywhere | — |
  | **14** | mention it **and** lack `create_signed_commit` | — |
  | **8** | contain a literal `createCommitOnBranch(input` **mutation site** | the 4 below, plus `2026-08-12_open_branch_protection_probes.py`, `2026-08-13_sweep_duplicate_ci_runs.py`, `2026-09-15_fan_out_pr_budget_alarm.py` (new-branch openers: they `POST git/refs`) and `2026-08-21_d4_expected_head_oid_probe.py` (a one-off probe) |
  | **4** | **existing-branch drivers carrying their own mutation** — the actual duplication | `2026-08-24_commit_driver_fix_to_pr_branch.py`, `2026-08-26_commit_files_to_pr_branch.py`, `2026-09-21_signed_move_on_branch.py`, `2026-09-22_append_signed_commit.py` |
  | **6** | existing-branch drivers that **reuse** the helper | — |
  | **10** | existing-branch drivers in total (4 + 6) | — |

  > **Five wrong numbers, each defensible in isolation, is the finding.** `4` (predecessor, stale);
  > `6` (sampled from a 14-commit-stale worktree); `14` (string matches published as a duplication
  > count); `8` (mutation sites, but counting openers and a probe as drivers); and `17` if you grep
  > the bare name. Every correction was more precise than the last and still answered a slightly
  > different question than the sentence asked.
  >
  > **The lesson is sharper than "state your criterion" — the paragraph that shipped `14` already
  > did that, and warned about criterion mismatch in the same breath.** A criterion can be precise,
  > reproducible, honestly disclosed, and *still* measure something other than what the sentence
  > asserts. Read the claim and the criterion as two separate sentences and ask what satisfies one
  > but not the other: a file that **documents** the mutation satisfies the grep and not the claim;
  > a **new-branch opener** carries the mutation but is not the duplication the item is about.
- Therefore the **09-08 item stands as written** — *"promote one into `util/` with a hermetic test
  and retire the others"* — and **this session's 09-21 verdict on it ("MISSTATED — do not action
  as written") was wrong.** Do not inherit that verdict.
- When consolidating, **keep `push_signed_commit.py`'s `--expected-head` pin**. The `append_*`
  drivers read the head live, which loses the concurrent-push guard.

**The set grows weekly** — `2026-09-21_signed_move_on_branch.py` and
`2026-09-22_append_signed_commit.py` both postdate the predecessor's count. That growth rate, over
a mutation that four existing-branch drivers each re-implement, is the argument for the item.

> Two distinct files are named `push_signed_commit.py` (181 vs 116 lines, **not** identical) and one
> driver lives in a **subdirectory** (`2026-09-10_soak_stopping_rule/`). A flat top-level listing undercounts.

**7. Repair the three sites still describing the `enabled[0]` snap that canopy#652 DELETED — this session created this debt.**
#652 replaced the snap with a clear (`dashboard_manager.py:2955-2975`). Three sites still present it
as current, **one of them production code**:

- **`src/model_registry.py:144-146`** (live on `main`): *"They sit BEFORE `equities_seq`.
  `_gate_dataset_options_handler` snaps the dropdown to `enabled[0]` … so this order decides which
  dataset the operator lands on when they pick Recurrence."* **The ordering rationale for five seeds
  is now false** — the operator lands on `⊥`.
- **`…REACHABILITY-DESIGN.md:613-617`** (§12.6), headed *"order is load-bearing"* — the same false
  claim, elevated to a design lesson.
- **`…REACHABILITY-DESIGN.md:119`** (§4.1) — the I-cover traversal diagram cites *"the existing snap
  at `:2702-2706`"*, demonstrating deadlock-escape via a deleted mechanism.

**8. `§12.9`'s VR-5 rejection cites as open a defect canopy#651 closed.**
`…REACHABILITY-DESIGN.md:800-805` argues VR-5 fails partly because *"`_completion_reason_label` …
maps five cascor reasons only — … **still open**"*. #651 shipped both halves: recurrence's three
tokens at `dashboard_manager.py:7041-7051` and the missing `Failed` branch at `:7260-7269`.
**VR-5's primary rejection (the D5 allocation of correctness) stands** — only the compounding
argument is stale.

### D. Awaiting others / owner-gated

**9. juniper-data#409** — OPEN, zero comments. **juniper-data#411** — OPEN since 2026-09-21T18:45Z,
zero comments: *"hf_store / kaggle_store emit the retired `*_full` contract below the decision-11
floor, and a shipped test pins it (S-1)"*. Same repo, same decision-11 contract canopy#647 turns on.

**10. juniper-data v0.15.0 shipped a BREAKING change today (2026-09-22T18:55Z) and canopy has not absorbed it.**
`allow_truncation` became tri-state `bool | None`, and an explicit **`false` now REFUSES even where
the deployment opted in** (juniper-data `7aaab46` / #418). canopy excludes that field from the form
*precisely because* an unticked checkbox used to send `false` on every apply
(`src/dataset_schema.py:120-130`, `PARTIAL_DATA_POLICY_FIELDS`). **The failure mode changed from
"overrides the operator" to "422s the request"**, and the guard's rationale comment now understates
it. canopy's `KNOWN_UPSTREAM_GENERATORS` snapshot (`src/model_registry.py:312`) is still dated 2026-09-09.

> This is exactly the drift `A-N7` exists to catch, arriving within hours of `A-N7` being deferred.

### E. Restored residue and smaller gaps

**11. `A-N4`** — nothing has re-measured the `equities` seed at generator **5.0.0**. canopy#648
*annotated* the stale numbers; it did not re-measure, and says so in-code
(`model_registry.py:210-215`, *"STALE, and knowingly left in place"*). canopy's recorded
`(15799, 16)` was taken at `3.0.0`; `juniper-data/juniper_data/generators/equities/generator.py:58`
is now `VERSION = "5.0.0"`.

**12. `A-N9`** — no `ModelSpec.supported_task_types` contains `"structured"`. #648 corrected the
*comment* that said the vocabulary had two values; the gap stands. A future `structured` generator
is compatible with nothing and greys out everywhere.

**13. canopy#649 fixed half of the predecessor's item 10.** That item said explicitly *"Not confined
to the X7 modules"*. #649 touched **one file**. The named test is untouched at
`src/tests/unit/test_main_import_and_lifespan.py:349-362` and still asserts `mock_ping.await_count
>= 2` after `await asyncio.sleep(0.05)` against a 0.01s interval — 2 of 5 expected ticks on a loaded
runner. Its sibling at `:332-346` has the identical shape.

> #649 also raised `HEALTH_DEADLINE_SECONDS` **0.5 → 1.0**, leaving **0.6s of headroom** before
> `STUB_BLOCK_SECONDS * 0.8 = 1.6`, past which a genuinely blocked loop passes. The commit says:
> *"go to just under 1.6 s and no higher. Past that, fix the harness or the runner, not the number."*

**14. `G11` is enforced by name-enumeration, and its stated authority does not exist.**
`model_registry.py:153` and `src/tests/unit/test_model_registry.py:99` both point the reader at
**`UNBOUNDED_IMPORT_GENERATORS`** — an identifier with **exactly one occurrence repo-wide: the
reference itself.** No test iterates `DATASET_TYPES` asserting boundedness (`:70`, `:96-102`,
`:105-127` all enumerate names), so seed #15 with unbounded `default_params` passes all of them.
Contrast `G10`, which *is* universal. The design's §5 table (`:291`) records G11 *"status after:
passes"* — the vacuous-pass shape this arc keeps catching.

**15. `X8` — the `equities_seq` `task_type` divergence.** canopy says `regression`, juniper-data says
`classification`; aligning to upstream gives the LMU **zero** datasets. Pinned at
`src/tests/regression/test_dataset_generator_contract.py:152`
(`TestX8TaskTypeDivergenceIsDeliberate`). The 09-08 instruction — *"settle before any §12 seed
sources `task_type` upstream"* — was dropped by 09-12. `A-N9` makes it more pressing, not less.

**16. `Y4` and `Y8`.** `Y4`: `dashboard_manager.py:4042-4059` restores `active_tab` guarding only
`!state.active_tab` and `=== currentTab`; nothing checks the tab still exists, so a model swap that
deletes a tab strands the store on it. `Y8`: `gated_dataset_options` (`model_registry.py:706-713`)
derives `disabled` from `dataset_reason` (`:602-616`), which re-implements all three compatibility
axes inline instead of calling `compatible()` (`:576-583`) — two independent expressions of the
load-bearing predicate, one of them a reason-string builder.

**17. Post status comments on canopy#559 and canopy#371.** Both have **zero** comments; #559's
`updatedAt` is 2026-09-01, #371's 2026-06-17. canopy#647 shipped #559's first half and the issue
still reads as wholly open.

> **#371's trigger has NOT fired.** Its text is a **conjunction**: promote when A1 lands **and** the
> rendered gate UX needs browser-level proof a pure-function test cannot express. Only the first
> conjunct is satisfied. The predecessor's "the trigger has fired" was wrong.

### F. Found by a peer re-probe, 2026-09-22 — mostly dropped by THIS document, not all of it

> **Items 18–21 were dropped** by this document and restored here. **Item 22 was never carried** —
> it is a live defect no revision had found. **Item 23 is already fixed** (canopy#656) and is kept
> as the record of what shipped. The revision merged as juniper-ml#2021 called all six "restored
> after this document dropped them", which is true of four of them.

**This section exists because the rewrite that restored six dropped items dropped four more.**
The three validation agents were briefed on the *first draft*; nothing validated the rewrite, which
is precisely the rule stated in § Validation record below. Found by peer session `canopy`, not by
this session. Each item re-derived in source before being accepted here.

**18. `A-N2` — §12.4's `generate → stage → train → render` loop through canopy has never been run.**
It was item 1 of this document's own first draft and has **0 hits** in the archived revision. §12.4
(`…REACHABILITY-DESIGN.md:538`) requires the loop "observed once"; §12.6 records fitting
`juniper_recurrence_model.LMURegressor` directly and §12.7 records `generate → NPZ →
CascadeCorrelationNetwork.fit` — **neither goes through `/api/stage_dataset`**. The 09-08
predecessor's caveat is verbatim at
[`HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md`](HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md)
§ *Not established (carry forward)*. **Cited by heading, not by line.** This was `:128`; a peer
session is inserting 91 lines above it, which would have silently re-pointed the citation into
the new text. A line number is not a durable citation across concurrent sessions.

**19. ∥ packaging — `yfinance` and `arc-agi` are absent from juniper-data's lockfile.**
`requirements.lock` line 2 is `uv pip compile pyproject.toml --extra api --extra observability
--extra mnist`; `yfinance>=0.2.40` lives in the `equities` extra (`pyproject.toml:48-53`), which is
not compiled in, and **the image installs only the lock**. So the LMU has zero available datasets in
the container regardless of any UI change — the deployment fact behind `_empty_dataset_set_notice`.
Was under "Awaiting others" in the first draft; **0 hits** in the archived revision.

**20. `X10` — `RecurrenceBackend.initialize()` is unconditional and `selection_is_live` consults no health signal.**
`recurrence_backend.py:473-476` is a log line and `return True`: no probe. `selection_is_live`
(`model_registry.py:516-537`) reads only `model_key`, `backend_type` and `spec.provider`. So a
"live" selection is a claim about configuration, never about reachability. Section B of the archived
revision recorded only the `Y2` claim; X10 appears nowhere. **CLAIMED by peer session `canopy`,
unstarted — do not start it here. This claim LAPSES at 2026-09-29T00:00Z** on the same terms as
§ B: after that, start it unless an open PR or a pushed branch carries the work. A document
asserting the claim does not count.

**21. `Y7`, model-table half — `aria-describedby` is 0 occurrences repo-wide.**
Design §4.3: *"Give the reason cell an id and point the row's control at it with
`aria-describedby` (Y7)"*. At `9bffaba1`, `_build_model_selection_table`
(`dashboard_manager.py:3530`) renders the reason as an **id-less** `html.Span` and the Select button
carries it only via `title=`. The 09-21 correction's "accessibility half SHIPPED" covers **only**
the dropdown's `role="status"` / `aria-live="polite"` notice at `:1418`. **canopy#368's
accessibility clause stays open.**

**22. OQ-6 has a SECOND site, and it still snaps. Unruled.**
`dashboard_manager.py:6154-6155`, the restart-modal opener:
`if not selection_axis_unset(dataset_type) and dataset_type not in enabled: dataset_type =
enabled[0] if enabled else None`. A stranded **non-`⊥`** dataset is still replaced by the first
enabled option — the behaviour canopy#652 removed from the sidebar. `⊥` itself is correctly
preserved, and the in-code rationale ("never seed the field with a value its own list disables") is
defensible, so **this may be deliberate — but it was never ruled under OQ-6**, and the ratification
in `…MODEL-DATASET-SELECTION-DESIGN.md` §5.6.1 does not mention it. After #652 the sidebar rarely
hands the modal a stranded value, but an availability change **between the gate firing and the modal
opening** still can. **Needs an owner ruling: does model-primary-by-clearing bind this site too?**

**23. Two live defects in this session's own merged PRs — FIXED in canopy#656 (see § Validation record).**
Both were found by the peer, both reproduced here before fixing:
- **canopy#653's `unknown` state could never fire for the case it was built for.** The dashboard
  calls canopy's *own* route; `main.py`'s `list_dataset_generators` catches a juniper-data outage
  (`:1908`) or refusal (`:1895`) and answers **HTTP 200 with four built-in generators carrying no
  `available` flag**. So `resp.ok` was true, a list came back, `availability_is_known` was true, and
  `is_generator_available` fail-open reported `equities_seq` selectable against a dead service —
  verbatim the `A-N5` complaint. #653's tests drove the failure by making `requests.get` raise,
  which simulates **canopy** being down, not juniper-data: **the fixture mocked the near seam.**
- **canopy#652 announced a clear that never happened.** With the dataset already `⊥`, any gate
  re-fire produced *"**none** is not compatible with CasCor (Cascade-Correlation), so it was
  cleared"* — `_dataset_label(None)` renders the literal string `none`. Reachable the moment #652
  made `⊥` a state the gate clears into. No test passed a `None` current value.

---

## Key context — traps this session paid for

**The recurring failure mode was a true fact paired with a wrong consequence.** It appeared in three
agent findings and at least four of my own claims, and is recorded as variant 5 of
`reference_partial_read_generalisation`: *a declaration is the right evidence for what a thing IS
and the wrong evidence for what it CONTAINS*, and *a zero is the most persuasive wrong answer*.
Concretely: a type annotation read instead of its values; a declared method set read instead of the
caller's requirement; a guard satisfied by its own explanatory comment instead of the command that
comment described.

**Corrections to the superseded record — do not re-derive these as findings:**

- **`A-N7`'s second clause was wrong, and the code it accused is right.** The addendum claimed the
  comments at `src/model_registry.py:314` and
  `src/tests/regression/test_dataset_generator_contract.py:31`/`:283` *"claim the env has
  juniper-data 0.6.0; it has 0.14.0"*. Measured today: `JuniperCanopy1` really does carry
  **`juniper_data 0.6.0`**
  (`/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/juniper_data-0.6.0.dist-info`),
  and `juniper_data.core.registry` **does not exist there**. The comments are correct; the
  refutation was not. `A-N7`'s *first* clause (the drift test is deliberately unbuilt) stands.
- **"Ten new items" in the addendum was eleven** — `N0` through `N10`. juniper-ml#1977's own title
  inherits the off-by-one.
- **"Three were already closed" was one** unqualified `CLOSED` (item 8); item 4 was "Y1 closed / Y2
  open" and item 11 "half closed".

**`Scheduled Tests` is red again.** canopy#641 repaired the lane and its dispatch went green
(2026-09-21T13:13:51Z), but the next scheduled run **failed 2026-09-22T06:18:46Z** — Python 3.13 leg
only; 3.12 and 3.14 green. Logs were not retrievable via `gh run view --log`. **#641 is not a closed
chapter.**

**canopy#650 rewrote the install surface canopy#641 had just established**, hours later, from a
*different* session (`session_01NZA8uLfGy4RSVg2MPXWGTa`). It replaced `-r conf/requirements_ci.txt`
with pyproject extras across the unit / integration / ui / dependency-docs lanes (107 → 74
distributions) and rewrote #641's comment in `scheduled-tests.yml`. **Any advice to "run the full
unit lane" now runs against a different install set than #641 assumed.** #650's body also carries an
unfiled ecosystem finding: *"juniper-data and juniper-data-client carry the identical contradiction
in their own `conf/requirements_ci.txt` right now."*

**Environment drift is real and larger than it looks.** `JuniperCanopy1` differs from
`juniper-canopy/requirements.lock` by **33 version changes plus one absent package (`comm`) = 34
install actions** — not "one package". Measure with `python -s` so user-site cannot mask it.

---

## Verification commands

Run from the repo named in each block. **Judge by exit code, never by pytest's progress output —
`[100%]` prints on failing runs too** (`.F [100%]` precedes `1 failed, 1 passed`).

```bash
# --- juniper-ml: this worktree is NOT current; check before trusting anything local
git rev-list --count HEAD..origin/main                          # was 14 at handoff time
git merge-base --is-ancestor HEAD origin/main && echo merged || echo UNMERGED

# --- canopy, item 2: is ⊥-at-mount still open?
grep -n 'value=DEFAULT_DATASET_TYPE' src/frontend/dashboard_manager.py   # expect :1400 and :6085
grep -c 'params-init-interval' src/frontend/dashboard_manager.py         # expect 11

# --- item 1: does the hydration callback reach the dataset axis yet?
grep -n 'NUM_OUTPUTS' src/frontend/dashboard_manager.py
grep -c 'nn-dataset-type-dropdown' src/frontend/dashboard_manager.py || true

# --- item 3: is there a GET route for the model axis yet?
grep -n '@app.get("/api/model' src/main.py || echo "still write-only"

# --- item 4: DISCRIMINATING check. The names live on the ADAPTER, not the backend classes.
grep -n 'hasattr(backend._adapter, "save_snapshot")' src/main.py || true
grep -n 'def save_snapshot\|def load_snapshot' src/backend/cascor_service_adapter.py || true
#   A grep of recurrence_backend.py / service_backend.py / demo_backend.py returns 0 for all
#   three and proves nothing. Do not use it as the check.

# --- item 7: do the three stale enabled[0] sites still claim the snap exists?
grep -n 'enabled\[0\]' src/model_registry.py
grep -n 'enabled\[0\]\|2702-2706' \
  ../juniper-ml/notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md

# --- item 14: the authority G11 cites
grep -rn 'UNBOUNDED_IMPORT_GENERATORS' src/    # expect 2 references, 0 definitions

# --- item 3b: G7 CANDIDATE FINDER. This is not a verdict -- read the next comment.
grep -rn 'G7' src/tests/            # today: 1 hit, the header comment at
                                    # test_selection_reachability_guardrails.py:13 listing G7
                                    # among the guardrails that "arrive with their own"
#   A MENTION IS NOT A GUARDRAIL. Open every hit and confirm it ASSERTS that the mount dataset
#   value equals the backend's staged dataset. A test named for G7 that asserts nothing satisfies
#   this grep and closes nothing.

# --- item 3: Y3 guardrail CANDIDATE FINDER. File-scoped on purpose, and noisy on purpose.
grep -rl 'nn_model' src/tests/ | xargs grep -ln 'reload\|hydrat\|restore' || echo "no candidates"
#   Measured 2026-09-22: 4 candidate files, and ALL FOUR are incidental -- "auto-restored" in a
#   fixture docstring, "silently restore the deadlock" in a comment. There is still no Y3
#   guardrail, which the design's §5 table independently confirms (G1a-G11, nothing on the Y3
#   read side). Open each candidate; do not trust the count.

# --- §12 still closed: 14 seeds / cascor 8 / recurrence 6 / unseeded arc_agi + csv_import
python -c "from src.model_registry import DATASET_TYPES; print(len(DATASET_TYPES))"
```

---

## Git status at handoff

**juniper-ml**: worktree `velvety-pondering-frost`, branch **`docs/oq6-ratified`** at `f4d5fd65`.
**This branch is NOT an ancestor of `origin/main`** and is **14 commits behind** (`origin/main` =
`e3186919`). juniper-ml#2008 and #2009 both merged *before* canopy#654 — so this document's first
draft claim that "both repos are current" was already false when written. **This document was the
only untracked file in the worktree, and `git worktree remove` deletes untracked files.**

**juniper-canopy**: `origin/main` = `9bffaba1`, clean. No session worktree or remote branch survives.

**Open in the arc**: canopy#368 (1 comment), #371 (0), #559 (0); juniper-data#409 (0), #411 (0).
canopy#552 is open but is *not* this arc.

---

## Validation record

This document's first draft was checked by three adversarial agents and one peer session, returning
**29 distinct defects**. The load-bearing ones, each independently re-derived in source before being
accepted:

| defect | status |
|---|---|
| `⊥`-at-mount dropped as an item while its ordering constraint was kept | CONFIRMED — restored as item 2 |
| "nine canopy PRs" — canopy#648 missing, taking `A-N4` and `A-N9` with it | CONFIRMED — restored as items 11–12 |
| `N7`/`N10` used in two incompatible senses inside one document | CONFIRMED — prefix scheme added |
| item 4's verification grep non-discriminating (0 / 0 / 0 across all three backends) | CONFIRMED — replaced |
| "judge by `[100%]`" — a progress marker, not a verdict | CONFIRMED — rule deleted |
| "both repos current" — the ml worktree is 14 behind, on an unmerged branch | CONFIRMED |
| signed-commit driver count | CONFIRMED wrong — **and three criteria give 11 / 10 / 6**, so the unit is now stated |
| `model_registry.py:144-146` describes a mechanism canopy#652 deleted | CONFIRMED — item 7 |
| `A-N7`'s refutation was itself wrong; `JuniperCanopy1` really has juniper-data 0.6.0 | CONFIRMED by direct measurement |

One agent claim was **partly refuted on re-derivation** and is recorded rather than silently
dropped: pytest's `N passed` summary does *not* print under this session's doubled `-q`, so that
half of the reasoning was wrong — but the dangerous half (a `[100%]` marker on a **failing** run)
reproduced exactly, so the conclusion held for a different reason than the agent gave.

> **Do not treat the next handoff as validated because this one was.** The 09-12 predecessor was
> also consensus-checked, and its residue still lost `⊥`-at-mount, canopy#648, `A-N4`, `A-N9`, `Y3`
> and `X8`. The failure mode is not carelessness in the moment: **a shipped item and a dropped item
> look identical in a summary.** Check the predecessor's list item by item against source, never
> against its own status table.

### This document proved its own warning within the hour

**The archived revision dropped four items while restoring six** — `A-N2`, ∥ packaging, `X10` and
`Y7`, all restored as § F above. It also shipped a half-wrong item 6 and missed a second live OQ-6
site (§ F item 22). A peer session found every one of them; this session found none.

The mechanism is stated plainly because it is the reusable part: **the three agents were briefed on
the first draft, and nothing validated the rewrite.** The rewrite is where the six restorations
happened, so it was simultaneously the most-changed and the least-checked text in the document.
This is the 2026-08-18 lesson — *"the fix pass is the least trustworthy part; always run round 2 on
the corrections"* — recorded in `feedback_validate_handoff_prompts_independently` and violated by
the session that had just re-read it.

**Two live defects in this session's own merged PRs** (§ F item 23) share one root: *a guard that
tests the seam you were thinking about rather than the seam the defect crosses.* canopy#653's
fixture made `requests.get` raise, which proves the `None` path works and never exercises the
juniper-data outage the feature was built for. Fixed in **canopy#656**, mutation-checked at all
three sites (route flag fires 1 test, the `⊥` guard 4, the consumer translation 2 including the
end-to-end one).

`X11` (first paint passes no backend) is deliberately **not** a separate item: it overlaps item 3
(`Y3`) and the design phases the two together, so it belongs to item 3's owner.

### Round 3 — the correction pass needed a correction pass

The revision merged as juniper-ml#2018 was itself wrong in three ways, all found by the same peer
session, none by this one:

| defect | correction |
|---|---|
| **`G7` had 0 hits** — both prior revisions quoted `…REACHABILITY-DESIGN.md:349` and stopped one token before `+ **G7**` | restored as item 3b, with its definition at `…REACHABILITY-DESIGN.md:287` and the fact that no test asserts it |
| **item 6's "14"** was a *string-match* count published as a *duplication* count | superseded by the taxonomy table in item 6 — the duplicated work is **4 files** |
| **items 4 and 20 claimed work with no expiry** | both now lapse **2026-09-29T00:00Z**, after which an **open PR** or **pushed branch** is required to keep the claim |

### Round 5 — two MAJOR, seven MINOR, all from the peer

| defect | correction |
|---|---|
| **`G7` called "the acceptance criterion for items 1 and 3"** — it is **dataset-axis only** and cannot fail on a `Y3` defect | scoped to item 1, and **the missing Y3 guardrail is now recorded as a gap** under item 3 |
| **the order line put item 2 before hydration** — contradicting `D-N10` *and* item 2's own text | items **1, 3, 3b** are design PR 2; **item 2 follows** |
| the count again (`8` counted openers and a probe as drivers; `14` was mis-described) | **taxonomy table** replaces the number — 17 / 14 / 8 / **4** / 6 / 10, each row with its criterion |
| the lapse had **no time qualifier**, so read literally it cancelled the claim immediately | rewritten: the claim **holds until** the date, and the PR-or-branch test applies **from** it |
| "why 3b" named the wrong externally-cited items; § Verification commands had no `G7` check | corrected to **4, 6, 14, 15, 19, 21, 22**; a `G7` check added |
| "18–23 … this document dropped them" — 22 was never in it, 23 is already fixed | range line now distinguishes dropped / never-carried / already-shipped |
| "round 2 shipped the truncated quote" — it is identical in #2014 | attributed to **both** earlier revisions |
| bare `:349` / `:287`; unnamed peer addendum; `**+ G7**` vs `+ **G7**`; "~130 lines" | all named and corrected; the insertion is **91** lines |

**Five rounds, and each one's fix introduced the next one's defect.** Round 1 fixed 29 draft
defects and dropped four items. Round 2 restored those and shipped a wrong count plus a truncated
quotation. Round 3 fixed those and left a stale range line. Round 4 fixed the range line and
asserted an order that contradicted the design. Round 5 fixed that.

**The rate is falling and the severity is falling, but the pattern has not broken once in five
attempts.** A sixth round is the correct default. The one structural lesson: **every round's defect
was introduced by that round's own fix**, never inherited — so the text to re-read hardest is the
text you just changed, and the statements most likely to be stale are the ones that *scope* what
you changed (ranges, orders, counts, "the only X") rather than the change itself.

> **Round 5 did it again, in the commands it added to catch exactly this.** Both new §
> Verification commands were defective on first write, and both produced the *right answer today by
> luck*:
>
> - The `G7` check **grepped the label** while the comment beside it said *"grep for the ASSERTION,
>   not the label"*. A test named for `G7` that asserts nothing would have satisfied it.
> - The `Y3` check was **line-scoped** (`grep nn_model | grep reload`), so a guardrail naming the
>   concern in its title and touching `nn_model` twenty lines down would not match. It printed
>   "no Y3 guardrail" — the correct answer, by accident. File-scoped, it finds **4 candidates**,
>   all of them incidental matches in docstrings and comments.
>
> Both are now **candidate finders that say so**, with the measured result recorded beside them.
> **A verification command is an assertion about the world and needs the same scepticism as a
> sentence** — including "does it produce this output because the claim is true, or because the
> command is too narrow to see the counter-example?"

**The count lesson is now sharper than "state your criterion", which item 6 already did.** The
criterion was executed exactly and still measured the wrong thing: *matching a string* is not
*carrying a mutation*. **A criterion can be precise, reproducible, honestly disclosed, and answer a
different question than the sentence asks.** Four miscounts of one set in one day, by three
different readers, is the evidence.
