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

**Remaining work.** Items 1–3 are one PR-sequence and must be done in order; 4–8 are independent;
9–17 are record repairs and smaller gaps.

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

**The design phases this as PR 2 alongside item 1** (`…REACHABILITY-DESIGN.md:349` — *"§4.10
hydration, **both** axes (X1's dataset-side sibling, Y3)"*).

### B. CLAIMED by a peer session — do not start these

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

The canopy-side defect: `main.py:2573`/`:2818` gate the snapshot path on
`backend.backend_type == "service"`; the `else` branch writes cascor-shaped meta via h5py — zero
LMU state — and returns `"Snapshot created successfully"` with `"mode": "real"`.

> **That gate is deliberate, not an oversight.** `main.py:2568-2573` carries the A1-iii-a rationale:
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

The substantive finding is unaffected and verified: the sampled drivers **reuse**
`create_signed_commit` (`util/open_signed_pr.py:117`) rather than redefining it, a canonical helper
is already promoted with a hermetic test (`tests/test_open_signed_pr.py`), and
`util/ad-hoc/push_signed_commit.py` self-declares as a promotion candidate. **The set grows weekly**
— `2026-09-21_signed_move_on_branch.py` and `2026-09-22_append_signed_commit.py` both postdate the
predecessor's count. That growth rate is the argument for the item.

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
