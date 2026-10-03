# HANDOFF 2026-09-09 — round 38: the three-way prompt shipped, and two of this round's own corrections reversed under validation

Successor to
`HANDOFF_2026-09-07_defect-register-round-37-the-inert-cache-and-the-partial-data-contracts-last-mile.md`
(the **predecessor**; every bare "round 37" below means that file). Corrections to it are in §4.

**Validate this document with independent agents before trusting it** (memory
`feedback_validate_handoff_prompts_independently`). Its own record is §7. Read §4's last two rows
first: this round issued two confident corrections to the predecessor and **round-2 validation
reversed both**. Treat consensus as evidence, not proof — in this arc the validators were wrong
twice as well, and §7 says where.

**A bare "§N" means a section OF this document.** Every reference to another file names it. All
dates and times UTC.

**Register** (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`): **112 rows, 85
fixed, 27 open** — the 96 primer rows plus **16** filed this round in a new §4.9. Open splits 17
primer (16 parked, `APD-DATA-019` unparked) + 10 post-primer. **The set of rows a session may
action without asking the owner first is still empty**; §4.9's rows do not change that, and §0.5
says why the attempt to claim otherwise was withdrawn.

---

## 0. Remaining work

1. **Successor, first — validate this document (§7).** Round 2 ran on the corrections and the
   register edit, not on the finished document.

2. **cascor partial-data follow-ups — DONE: juniper-cascor#640, merged 2026-09-09T21:45:03Z as `53c0338`.**
   Register rows `APD-CASCOR-009` / `-010` / `-012` are closed against it. Left below for the
   record of what it covered: Scope, all re-confirmed on cascor `main` after `44dafe0`:
   `_auto_start_training` (`src/api/app.py`) fetches the dataset itself and so never sets
   `dataset_shortfall` on its own path, forwards no opt-in, and swallows its failure
   (`except Exception: logger.exception(...)` — service up, healthy, no training);
   `get_metrics()` (`src/api/lifecycle/manager.py`) carries no annotation; no operator-facing doc
   names `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS` (`AGENTS.md`'s env table and `.env.example` are
   the two places — `src/main.py`'s `--help` mentions it, which is not a doc).
   `APD-CASCOR-011` (the CLI flag) is **still open and still parked**: #640 took a third path —
   the flag is kept, and its `--help`, a WARNING on use and the operator docs now say what it does
   and does not affect — so the inertness is no longer silent, but the parked question is *drop it
   or rewire the path* and that is still owed a ruling.
   **One correction was needed on review before that PR merged**, and it is the reusable part: the
   PR explained the flag's inertness by saying `main.py` trains an in-process spiral problem,
   synthesised locally, that never contacts juniper-data. `main.py` health-checks `/v1/health` and
   refuses to start when the service is unreachable. The true reason is that the generator is
   hardcoded `spiral`, which juniper-data always delivers in full and which is not truncatable. A
   test had pinned the wrong wording by asserting the phrase "two-spiral" appeared in the warning;
   it now asserts the reason instead. **A test that pins prose pins whatever the prose got wrong.**

3. **`APD-CASCOR-013`, filed this round and unbuilt:** `_dataset_shortfall` is written at exactly
   one line in `src/api/lifecycle/manager.py` and **never cleared**, so a run started through the
   inline path with no staged dataset config reports the *previous* run's annotation, naming a
   foreign `dataset_id`. Parked — *when* it clears is a contract question.

4. **A live end-to-end run of the prompt on `equities` is still impossible at canopy's defaults.**
   `start_date=2000-01-01` with `fundamentals_fill="nan"` yields a NaN-laden artifact that
   cascor#630's finiteness loop refuses. Note the ordering, corrected in §4: the shortfall
   annotation is written *before* that refusal, so the acceptance path is fully observable on
   `/v1/training/status` even on an artifact cascor then rejects — what you cannot get is a
   *trained* run. To exercise it end to end, stage `equities` with `start_date` ≥ 2010 or
   `fundamentals_fill="drop"`, Start, answer the modal. Record the run in the canopy E2E ledger
   (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`), not here.

5. **Owner decisions. The empty set is still empty — do not action any of these without a ruling.**
   - **Is option 3 a caller right?** Round 37 said expressing it caller-side needs a schema change.
     This round "refuted" that on `model_fields_set`; **round 2 reversed the refutation** and round
     37 is substantially right (§4). Mechanism: `EquitiesGenerator.bind_deployment_defaults` ends in
     `model_copy(update=...)`, which *adds* the updated keys to `model_fields_set`, and the route
     binds before `generate` — so downstream of the binder an omitted flag and an explicit `false`
     are indistinguishable, and a presence guard at any of the three `or settings.*` sites is a
     constant-true guard. It survives only *inside the route, above the bind*. And canopy sends an
     explicit `allow_truncation: false` on every equities stage from the schema default, so a
     presence guard would read an untouched default as a deliberate refusal — the exact
     serialised-defaults hazard `csv_import/generator.py`'s own comment gives as the reason
     `model_fields_set` cannot carry this. juniper-data's OR is deliberate and test-pinned. The
     question is privilege, not mechanism, and the mechanism is harder than this round claimed.
   - **The three look-ahead paths in `equities`** — register rows `APD-DATA-041` (`adj_close`),
     `APD-DATA-042` (`cost_basis`), `APD-DATA-043` (`_SHARES_OUTLIER_FACTOR`). All reachable at
     default parameters. Fixing any changes the artifact and needs a `generator_version` bump.
   - **First-publication vs latest-filed in `_fetch_shares`** (`APD-DATA-040`): 162 of 485 cached
     CIKs carry a re-stated period end, 17,569 rows, ADM in the default prefix off by up to +11.55%.
   - **The SEC shares cache key is CIK-only** (`APD-DATA-039`), and share counts go stale silently
     (`APD-DATA-045`: 26 of 485 delivered series stop before 2025-06-01, SPG 16.7 years back,
     against a cache-wide median of 2026-04-24). A versioned key plus a TTL is a plain fix; the
     refresh horizon is the ruling.

6. **Two canopy findings from this round are written down in no ledger** — only in this document.
   The schema-driven form was sending an explicit `allow_truncation: false` on every equities apply
   (fixed in canopy#605 by excluding the two policy fields), and `val_ratio` renders in the sidebar
   while `train_ratio` / `test_ratio` are excluded as infrastructure. File them in the canopy E2E
   ledger named in §0.4. **The `val_ratio` item is not the one-line fix an earlier draft called
   it**: adding it to `INFRASTRUCTURE_FIELDS` makes the set consistent but removes the only sidebar
   control over the in-loop selection split, and the ecosystem data contract makes `val` the split
   that selects. Say which direction is intended before touching it.

7. **`equities_seq` still has no `data_quality` consumer in the recurrence tier.** juniper-data#388
   made the producer refuse and annotate; nothing reads the annotation there
   (`grep -rn data_quality --include='*.py'` in juniper-recurrence returns nothing). See §5.10 for
   how to run that tier at all — it has no conda environment.

8. **The 16 parked primer rows are unchanged** and need owner unparking, as do the 13 open
   post-primer rows, each of which carries its own park sentence under the §4.9 table.

---

## 1. Verify starting state

Run each line standalone (§5.1). From the juniper-ml worktree root:

```bash
git fetch origin
grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
python3 util/ad-hoc/register_open_set.py
python3 util/ad-hoc/register_status_crosscheck.py
python3 -m unittest tests/test_thread_handoff_archive.py
```

Expected: FIXED rows **85**; **`112 rows | 85 fixed | 27 open`**; cross-check **85 / 85 / 85,
AGREE**; the archive test **passes**.

**That last line is not decoration.** The register's §4.9 cites this handoff by filename, and
`tests/test_thread_handoff_archive.py` requires every handoff a top-level note cites to exist in
`prompts/thread-handoff_automated-prompts/`. Until both land in the same PR the test fails — which
is why they are bundled. An earlier draft of this section listed only the three register commands,
all of which read green on a register that reddens CI.

---

## 2. What this session did

**Changed files, by name.** In juniper-ml:
`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; this document;
`reports/2026-09-08_round-37-consensus/` (six round-1 lane reports + `README.md`) and
`reports/2026-09-09_round-38-consensus/` (round 2); `util/ad-hoc/register_round38_file.py`,
`register_round38_dates.py`, `register_round38_round2_fixes.py`, `cascor_fix_shortfall_all.py`, and
`util/ad-hoc/2026-09-08_round38_pr_edit_scripts/` (the eleven one-shot PR edit scripts plus a
`README.md`, kept under the script-placement rule). Memories updated:
`project_partial_data_contract_arc_2026-09-05.md`, `reference_fixture_can_encode_the_defect.md`,
`reference_bandit_b105_flags_token_names.md`, `reference_executor_agent_invents_pr_numbers.md`, and
`MEMORY.md`. In juniper-data, `util/ad-hoc/2026-09-08_equities_shares_cache_census/` (13 files).

| PR | State | What |
|---|---|---|
| **juniper-cascor#633** | MERGED 2026-09-09T17:57:06Z, `44dafe0` | `dataset_shortfall` says WHO accepted: `accepted_by_this_run`, `acceptance_source` ∈ `request_params` / `allow_truncated_datasets` / `producer`, the original field kept with its literal meaning. The refusal keys its remedy off the WIRE stance and opens with `[dataset_shortfall_refused]`. WS misclaim corrected. 28 passed. **It also broke `main` — see §5.3.** |
| **juniper-canopy#605** | MERGED 2026-09-09T19:25:55Z, `b587e54` | The three-way prompt, hanging off **Start** (§0.4), on both transports; `dataset_shortfall` carried through `normalize_status`; status-bar `· partial data`; Network Info note; `detail_full` on the clientside JS; `PARTIAL_DATA_POLICY_FIELDS` excluded from the form; 3 manifest rows. **27** new test functions (an earlier draft said 24); the new prompt suite alone collects 28 items. |
| **juniper-data#388** | MERGED 2026-09-09T17:14:32Z, `d7f4be5` | `EquitiesSeqGenerator.bind_deployment_defaults` (its `dataset_id` was IDENTICAL under the env var on and off — proven by execution); the incomplete-data policy shared via `EquitiesGenerator._apply_incomplete_policy`; the seq fixtures' unreachable filings fixed (§5.4); stale comments; the round-37 instruments graduated. **220 passed** across the nine suites (an earlier draft said 228, which no subset can produce). |
| **juniper-cascor#639** | MERGED 2026-09-09T21:03:09Z, `38ca3a5` | Repairs the `main` breakage #633 left (§5.3). `CI — juniper-cascor-model` is green on `main` again, and the two constants copies are byte-identical. |
| **juniper-cascor#640** | MERGED 2026-09-09T21:45:03Z, `53c0338` | The four follow-ups (§0.2): auto-start forwards the stance, annotates and records its failure; `get_metrics()` carries the shortfall; the CLI flag says what it does; the operator docs name the knob. Closes `APD-CASCOR-009` / `-010` / `-012`. |
| **juniper-ml#1858** | this document + the register + the reports + the scripts, 30 files | Bundled for the reason §1 gives. |

Auto-merge was armed natively on every PR under the owner's session-wide approval. Verify each with
`gh pr view <N> --json state,mergedAt,mergeCommit` **and** check the content is on `main` — a MERGED
badge is not ancestry, and `util/safe_merge.py` prints the *head* SHA, not the squash commit (§5.9).

## 3. Owner rulings — carried, none new

No ruling was sought. Round 37's §3 table stands (option 3 = fail/cancel/deselect;
`fundamentals_fill="nan"`; `APD-DATA-019` kept open and re-scoped). §0.5 lists what now needs one.

---

## 4. Corrections to the predecessor — and to this round's own first draft

Every row's "claim" is from
`HANDOFF_2026-09-07_defect-register-round-37-the-inert-cache-and-the-partial-data-contracts-last-mile.md`
unless it says otherwise. Each was re-derived from source before being applied.

| Claim | Verdict | Correction |
|---|---|---|
| §7/§8 "ml#1813 is still OPEN; `origin/main` still carries the old wording" | **False at archive time** | Merged 2026-09-07T15:15:42Z (`26e12019`), 66 min 53 s before ml#1818 archived the text unchanged. |
| §0.2 "canopy must POLL … budget for that" | **Overstated** | canopy already polls at 1 Hz through its status cache, ungated. The gap was `normalize_status`'s whitelist — but see the last row: "one line" was this round's overstatement in the other direction. |
| §0.12 "a third OR consumer" | **Wording** | Three sites; `equities_seq` is a third *generator* through an existing site. Its real gap — no incomplete-data policy at all — was not in round 37. |
| §0.5 "no `.md` or `.env` file mentions the flag" | **Literally false** | juniper-ml's own handoffs mention it; true for operator-facing docs. |
| §2 "all four merge SHAs verified" / "round 36's five PRs" | **Miscounts** | Three SHAs listed; six PRs listed. |
| §6 "two pre-existing juniper-data stash entries" | **Inherited miscount** | Three. |
| §5.6 `-p juniper_data.api.app` | **Stale since juniper-data#333** | Not needed; the circular import is gone. |
| §5.1 "heredocs into `python3 -` DO work" | **Mode-dependent** | Write scripts to a file and run them by path. |
| Line anchors `:505`, `:866/:868`, `:771`, `:3933` | **Stale when written** | `:508`, `:869/:871`, `:774`, `:3956` at the frozen SHAs — and **all four are stale again today**; re-derive, never transcribe. |
| "0 of 485 cached payloads are empty" | **True under four definitions, and misleading** | Six *delivered* series carry unusable counts; see `APD-DATA-044`, restated at the delivered level. |
| §0.13's scenario needs a finite artifact "or cascor#630 refuses first" — **this round's claim** | **Reversed by round 2** | The ordering is the other way: `_dataset_shortfall` is written ~21 lines *before* `_artifact_to_tensors` is called, so the annotation is observable even on an artifact the finiteness loop then rejects. The precondition is real for getting a *trained* run, false as an ordering claim. |
| §0.3 "expressing option 3 caller-side needs a schema change; cascor#624's remedy is NOT portable" — **this round called this refuted** | **Reversed by round 2; round 37 substantially right** | `model_fields_set` does distinguish the two states at construction, but `bind_deployment_defaults`' `model_copy(update=...)` adds the key, and the route binds before `generate`. Downstream the distinction is gone; a presence guard there is constant-true. See §0.5. |

**Dissent recorded, unresolved:** round 1 split round 37's §0.9 "never executes the empty-units
guard" into a true half (the concept-loop guard) and a false half (the post-load guard runs on a
warm hit). Both agree on the consequence.

**Two round-2 findings were themselves refuted, by re-derivation before editing.** A lane reported
that juniper-data#388 left a stale "no shares concept to SEC at all (KO and ABT among them)"
comment standing; the matched text is the *corrective* comment that same PR added, quoting the old
claim in order to retract it (`git log -S` lands on `d7f4be5`). A lane inferred a latent bandit
failure from cascor shipping a `*_TOKEN` constant with no suppression; bandit 1.9.4 walks
`ast.Assign` only, so an annotated assignment is invisible to B105 — verified by probe, and the
memory that said otherwise has been corrected.

---

## 5. Traps

### 5.1 The sandbox refuses shell STRUCTURE — and it is mode-dependent
Loops, `&&`+heredoc, `${PIPESTATUS}`, unquoted variables in an option position, `git -C` at
juniper-ml's own checkout, and any command computing a `git`/`gh` argument at runtime were all
refused this session. Put every multi-line edit in a scratch script under `util/ad-hoc/` and run it
by absolute path.

### 5.2 Signed follow-ups, and a merge doctrine this round got WRONG
Local signing hangs (the key needs a hardware touch), so commits go through the GitHub API:
`util/open_signed_pr.py` opens branch + commit + PR and refuses an existing branch;
**`util/ad-hoc/push_signed_commit.py` adds a follow-up commit to an existing branch** — it was
already on `main` before this arc (ml#1830, extended by ml#1853 to read back what it wrote), and a
second independently-written copy sits beside it as `util/ad-hoc/2026-09-08_push_signed_commit.py`.
Three sessions wrote the same tool inside two days; check `util/` before writing a fourth.
Both tools send **whole files** — re-check `git log HEAD..origin/main -- <path>` immediately before
every push.

**The doctrine this round invented here was false, and round 2 disproved it by experiment.** When a
release moves the whole `## [Unreleased]` block, an open CHANGELOG PR goes DIRTY — that part is
real. This document previously claimed that re-applying your entry onto `main`'s file does *not*
clear it, "because the merge base is still the old commit and two insertions at the same point
conflict". A scratch-repo `git merge-tree` on this episode's own captured files returns **exit 0,
no conflict, byte-identical to the intended file**: git takes the identical release-move hunk once
from both sides and applies only your entry. The elaborate temp-ref rebase performed here was
unnecessary, and the PR's own history shows two ordinary `Merge branch 'main'` commits later
clearing the state the doctrine said they could not. **Re-apply on `main`'s file and push; if it is
still DIRTY, read the conflict before inventing a mechanism.**
Related and also wrong as written: "a force-update alone may fire no CI". On this PR the
force-update fired all seven contexts; four were then cancelled by concurrency when the next push
superseded them 21 seconds later. Cancelled is not "did not fire" — read the conclusions, not the
count.

### 5.3 cascor's `juniper-cascor-model` drift test — and how this arc fell into it
Any edit under `src/cascor_constants/`, `candidate_unit/`, `utils/` or `log_config/` must be
mirrored **byte-for-byte** into `juniper-cascor-model/<same path>` or
`juniper-cascor-model/tests/test_drift.py` fails.
**cascor#633 merged with that test red and left `main` red**, and nobody noticed because
`Test (Python 3.12)` is evidently not a required check there. The cause is worth learning: the four
new constants were never added to the module's real `__all__`, CodeQL flagged them as unused
globals, and the remedy added a **second** `__all__` mid-file — to the mirror only. That broke the
mirror *and* did not fix the finding, because the module already ends with its own complete
`__all__`, which replaces the mid-file binding at import time. juniper-cascor#639 repairs both.
Two lessons: mirror-check with `diff`, not by remembering that you copied the file; and a linter
remedy that does not make the linter go quiet is not a remedy.

### 5.4 A fixture can encode the defect
juniper-data's `equities_seq` fixtures filed their synthetic shares after the mocked frame's last
trade date, so every seq test ran on all-NaN fundamentals and stayed green — there was no policy to
notice. Sharing the policy helper turned 18 unrelated tests red. Fix the fixture, not the gate.
Memory `reference_fixture_can_encode_the_defect`.

### 5.5 canopy tests must run under `conda run -n JuniperCanopy1`
The env's python invoked directly skips the hook that strips the Rust `libtorch` path; anything
importing torch then fails with `libtorch_python.so: undefined symbol`. Unit tests that never
import torch pass either way, which is how a partial run reads healthy.

### 5.6 `-q` doubles with addopts
cascor, juniper-data and canopy all carry `-q` in `addopts`; adding `-q` hides the `N passed` line.
Use `-v … | grep ' passed'`, and `-p no:cacheprovider` when reading someone else's tree.

### 5.7 Bandit B105 keys on the NAME — but only on a plain assignment
`X_TOKEN = "..."` trips `hardcoded_password_string`; `X_TOKEN: str = "..."` does not, because the
check walks `ast.Assign` only. That is why the identical constant failed canopy's hook and merged
green in cascor. Rename to `*_MARKER` rather than suppress, and do not reach for the annotation as
the fix — it blinds the scanner instead of making the name honest. Memory
`reference_bandit_b105_flags_token_names`.

### 5.8 A delegated agent cited its own future PR number
The task-executor wrote `(juniper-data#385)` into a code comment before opening anything; #385 was
taken by an unrelated PR an hour later. Brief agents to cite dates, and grep the diff for `#NNN`
before merging. Memory `reference_executor_agent_invents_pr_numbers`.

### 5.9 Recipes recovered from the predecessor chain
Round 1 found four lost in round 37; round 2 found two more lost in this round's first draft. All
six:
- `util/safe_merge.py` prints `MERGED #N at <sha>` with the **head** SHA, not the squash commit, so
  `merge-base --is-ancestor <that sha> origin/main` false-negatives on every squash merge.
- juniper-data's `test_shares_are_not_visible_before_they_were_filed` asserts `ages.min() >= 0`,
  which catches a *future* value and cannot catch a **stale** one — `APD-DATA-040` and
  `APD-DATA-045` are invisible to it by construction.
- The owner's partial-data spec exists verbatim only in memory
  `project_partial_data_contract_arc_2026-09-05` (its table of the three options and their wire
  forms); the register and the handoffs paraphrase it.
- The `-q` doubling recipe — kept, at §5.6.
- **CodeQL on subclass-registration imports**: `py/side-effect-in-assert` and `py/unused-import`
  survive a `# noqa: F401`. The fix that works is `importlib.import_module(...)` — a **call**, not
  an import.
- **juniper-recurrence has no conda environment**: borrow one and set
  `PYTHONPATH=juniper-recurrence-model`, or a stale installed copy shadows the worktree. In a
  borrowed env `test_crossval.py` does not collect (stale `juniper_model_core`) and one torch test
  skips — **both pre-existing**, so do not chase them as your own breakage.

### 5.10 Environments
juniper-data → `/opt/miniforge3/envs/JuniperData/bin/python`; juniper-cascor →
`.../JuniperCascor1/bin/python` (trailing `1`); juniper-canopy → `conda run -n JuniperCanopy1`
(§5.5); juniper-recurrence → §5.9's last bullet.
**Primary checkouts drift.** The juniper-data checkout was pre-#388 while `origin/main` was
post-#388 during this round's validation; a lane reading "main today" from a checkout reads
whatever that checkout last fetched. Read `git show origin/main:<path>`.

---

## 6. Git status

Written from the juniper-ml worktree `pure-toasting-token`, on branch
**`worktree-pure-toasting-token`** at `44de51c5`, with `origin/main` ahead at `5fbe3bc1` — the
register was refreshed from `origin/main` before editing, so diff the register against
`origin/main`, not against `HEAD`. Untracked in that worktree: `reports/2026-09-08_round-37-consensus/`,
`reports/2026-09-09_round-38-consensus/`, `util/ad-hoc/2026-09-08_round38_pr_edit_scripts/`, and the
four `util/ad-hoc/` scripts named in §2. The juniper-ml PR branch exists only on GitHub (API-created).

Worktrees created this round and **deliberately not removed** (cleanup needs the owner's explicit
signal, and `git worktree remove` deletes ignored files):
`juniper-cascor--fix--dataset-shortfall-acceptance-source--20260908-0716--d39d537e`,
`juniper-canopy--feature--partial-data-three-way-prompt--20260908-0729--eb05021d`,
`juniper-data--fix--equities-seq-deployment-defaults-and-incomplete-policy--20260908-0730--03b7548f`,
`juniper-cascor--fix--mirror-shortfall-constants-all--20260909-1600--3de89b11`. Round 37's three are
also still present. juniper-data holds three stash entries belonging to other sessions.

---

## 7. Validation of this document

Procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

**Round 1 (2026-09-08, on the predecessor):** six lanes, one launch, four distinct entry points —
A1 git/`gh` receipts only, A2 source at the frozen SHAs, A3 the on-disk SEC cache with its own
scripts, A4 a self-built storage benchmark — plus two refutation briefs. Verdicts: A1 PASS with 4
corrections; A2 **FAIL** (2 refuted, 2 partial, 4 stale lines); A3 PASS 10/10 with 6 new findings;
A4 PASS 9/9; B1 0 succeeded / 2 partial / 4 failed; B2 NEEDS CORRECTIONS on all three lenses.
Reports: `reports/2026-09-08_round-37-consensus/`.

**Round 2 (2026-09-09, on this round's corrections and the register edit):** three lanes — A
receipts-and-source, B1 refutation, B2 amputation/executability/naming. Verdicts: **A** confirmed
the register arithmetic and 25 of 35 claims but **refuted four**, including the two false
verification receipts now fixed (§2) and the live `main` breakage (§5.3); **B1** 3 succeeded / 4
partial / 1 failed, its successes being the `model_fields_set` reversal, the merge-doctrine
disproof (§5.2) and the withdrawal of the register's licensing clause (§0.5); **B2** NEEDS
CORRECTIONS on all three lenses, recovering two more lost recipes (§5.9) and 10 unfilled
placeholders. Reports: `reports/2026-09-09_round-38-consensus/`. Two lane findings were refuted
before editing (§4). **No round 3 has run on the finished document** — that is §0.1.

**What the evidence cannot support:** anything about SEC's live endpoint (no network in any lane);
the harm magnitude of the `adj_close` channel (mechanism proven, next-day correlation 0.004);
whether the six placeholder series are placeholders at SEC or cache artifacts; whether cascor's
`Test (Python 3.12)` failure was the drift assertion or coverage (the job log was not read);
whether round 37's own validation rounds ran as it describes (no record exists).

---

## 8. Session-close checklist

- [x] Round-37 handoff validated by six lanes; corrections applied (§4)
- [x] juniper-cascor#633 — the annotation says who accepted; refusal token — MERGED
- [x] juniper-canopy#605 — the three-way prompt — MERGED
- [x] juniper-data#388 — `equities_seq` binder + incomplete-data policy — MERGED
- [x] Register: §4.9 filed (16 rows), `APD-DATA-019`'s precision withdrawn, §2 staleness fixed
- [x] juniper-cascor#639 — repairs the `main` breakage #633 left (§5.3) — MERGED, drift green on `main`
- [x] This document validated by three round-2 lanes; both reversals applied (§4)
- [x] cascor follow-ups PR — juniper-cascor#640, MERGED `53c0338`; three register rows closed (§0.2)
- [ ] The two canopy findings filed in the E2E ledger (§0.6)
- [ ] Live E2E of the prompt on equities (§0.4)
- [ ] Owner decisions (§0.5)
- [ ] Round 3, on this finished document (§0.1)
