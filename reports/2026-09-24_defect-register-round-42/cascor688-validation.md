<!-- Archived verbatim 2026-09-24 from subagent a9ffba2344397011a of session bc31e993 (final message). -->

PR #688 merged while I was validating it. It still carries two MEDIUM issues, a refusal check that misfires on real juniper-data errors and a test gap in the #687 interaction, both now follow-ups. #688's own handling of #687's refusal is correct in every ordering I tried.

**Merge.** It merged at 2026-09-24T18:56:25Z as `7f4a721325721f70ee79a01e851f227db14587cd`, whose parent is `ec8b5bd`. The squash tree `6851243d` is identical to the tree of head `521ebed`. On `7f4a721`, every CI job that had finished was green, including "Symbol & Docs Screen", so the `Allow-Symbol-Loss` line was recognised. A second round of unit-test jobs was still running.

**Runs at 521ebed** (JuniperCascor1, with the three env vars unset):
- The four shortfall files: 181 passed (43 / 37 / 37 / 64).
- `test_start_fresh_carries_params.py` 10 passed; `test_start_refuses_wider_staged_dataset.py` 10 passed; 201 in total across the six files.
- `tests/unit/api`: 2506 passed.
- The implementer's harness, re-run on my copy: 48 of 48 killed, including the base pseudo-mutant against main's code (23 failed, 2 errors).
- `gh pr checks 688`: every check passed; five Cursor automations and "Publish manifest" were skipped.
- McCabe complexity of `start_training` is 11 (15 on main).

## Findings

### 1. MEDIUM: the refusal check matches field names, so real juniper-data 400s are reported as shortfalls
- **Where:** `src/api/lifecycle/manager.py:4305`. The docs and comments that promise otherwise are at `AGENTS.md:188-191`, `CHANGELOG.md:260-265`, `manager.py:4244-4251` and `manager.py:218-221`.
- **What's wrong:** `"allow_truncation" in detail or "incomplete_rows" in detail` checks neither the status code nor the refusal's wording. juniper-data main rejects a bad parameter with a **400**, and that message names the field.
- **Evidence:** I ran juniper-data main (`0f0f7e0`) as a real server; `probes/probe_realjd_refusals.py` and `probes/probe_realjd_blank.py` drove it.
  ```
  flag=false equities incomplete_rows='keep'  jd=400 token=True  names_flag=True
  flag=false csv_import allow_truncation=''   jd=400 token=True  "...could not produce the requested dataset in full ... carried allow_truncation with no value, which defers to the producer's own deployment default ... Producer detail: Validation error (400): Invalid parameters: ... allow_truncation Input should be a valid boolean [type=bool_parsing, input_value='']..."
  flag=false csv_import allow_truncation=null jd=-   STARTED (dataset delivered in full)
  spiral n_spirals=1                          jd=400 token=False   (same on main)
  ```
- **Consequences:**
  - The CSV in the blank-string case is within its cap, yet it is reported as partial and canopy opens its partial-data prompt.
  - The new comment at `manager.py:218-221` calls a blank string a deferral; juniper-data rejects it instead.
  - With the flag off, a mistyped `incomplete_rows` is told to set `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS`, which cannot fix it.
  - Main gives the same outcomes, so the misclassification itself is not new. But the new docs say "Only a 422 that names…" and "recognised by its remedy", and the CHANGELOG's example, `n_spirals=1` as a 422, is really a 400 that main already reported plainly. Item 4 changes no outcome against the real producer.
  - My mutant NV4, which drops the `incomplete_rows` part of the check, survives all 2506 tests. That part is untested and never needed: both real refusal texts contain `Re-submit with allow_truncation=true`.
- **Fix:** `looks_like_shortfall = "Re-submit with allow_truncation=true" in detail` (the wording at juniper-data `limits.py:168` and `:189`), optionally also requiring `getattr(exc, "status_code", None) == 422`. Stop describing a blank string as a deferral, and correct the `n_spirals` example.

### 2. MEDIUM: nothing tests that #687's refusal leaves the partition record alone
- **Where:** `src/tests/unit/api/test_start_refuses_wider_staged_dataset.py:92` (`_assert_nothing_moved`); the code is `manager.py:4920` and `:4953`.
- **What's wrong:** Mutant NV1 moves the `_described_partitions` assignment (`:4953`) above the wider-dataset check (`:4920`). It survives 201 and 2506. `_assert_nothing_moved` does not check `_described_partitions`, and `_previous_run` fills all three partitions, so adding the check alone would not catch NV1.
- **Evidence** (`probes/probe_687_interaction.py` against the NV1 tree). Scenario P2: fetch A, then a start carrying inline train while a wider dataset is staged (refused), then inline val+test (refused again):
  ```
  NV1:  train=inline-2 val=inline-3 test=inline-3 | sf=ds-5 cd=['A'] parts=['test','train','val']
  head: train=inline-2 val=inline-3 test=inline-3 | sf=None cd=None parts=[]
  ```
  Under NV1 the status still names A with none of A's data loaded.
- **Fix:** assert `_described_partitions` in `_assert_nothing_moved`. Add an arm that is refused after an inline-train start (set = {val, test}) and then checks that an inline val+test start clears the record.

### 3. LOW: auto-start with a dataset staged during its boot window, log and status disagree
- **Where:** `manager.py:2569`. The auto-start fetch's log line is written in `_bind_start_tensors_locked`, before the staged reload at `:2761-2763`.
- **Evidence** (same probe):
  - P4a, a clean dataset staged: the log says `DATASET SHORTFALL: this run is training on a partial dataset` and `DATASET IS PARTIAL: 14 of 503…`, but status shows `dataset_shortfall: None` and `current_dataset: STAGED`.
  - P4b, a wider dataset staged: the same log lines, while `auto_start_failure` is `[start_fresh_required]…` and no run starts.
- **Context:** main behaves the same, but this is the log/status mismatch item 8 says is closed "on both fetch paths". Staging is open for the whole time auto-start waits for juniper-data and builds its dataset.
- **Fix:** log the auto-start annotation after the staged-reload block, only `if self._dataset_shortfall is dataset_shortfall`.

### 4. LOW (from #687): "Nothing was loaded" is false when the start also carried tensors
- **Where:** `manager.py:4766`.
- **What's wrong:** Inline tensors (the route's `inline_data` or spiral) and auto-start's fetch are bound at `:2743`, before the staged reload that refuses; the comment at `:2740` requires that order.
- **Evidence** (P2): `refusal says 'Nothing was loaded': True -- yet train is now inline-2`. #688's record is correct here: it is still A's, standing on val and test.
- **Fix:** reword to "The staged dataset was not loaded: it is still staged…".

### 5. LOW: two more of my mutants survive all 2506 tests
- **NV3** (`manager.py:2560`): a clean auto-start fetch keeps the previous annotation. The existing tests start clean, or go from clean to partial. Add a partial fetch followed by a clean auto-start fetch that must report `None`.
- **NV5** (`manager.py:2618-2621`): while a fetch's partitions remain, a named inline start (the route's spiral) takes over `current_dataset`, which then disagrees with `dataset_shortfall`. Only the probe matrix (scenario S7) sees this. Add a fetch, then a spiral train-only start, and assert `current_dataset` still names the fetch.

### 6. NIT
- `CHANGELOG.md:230` says it "Corrects two statements". It also overturns the earlier "points at the request's own `allow_truncation`" (that case is now a plain failure) and widens "no entry carries a schema" to "any entry".
- `test_allow_truncated_datasets.py:42-43` cites canopy lines 8332-8341; on canopy main (`f2147403`) the function is at `:8404-8413`. The copied body is still identical.

## New mutants

| Mutant | 201 named | 2506 api |
|---|---|---|
| NV1: partition set assigned before the wider-dataset refusal | survived | survived |
| NV2: shortfall logged before that refusal | killed by `test_a_bound_fetch_logs_its_shortfall_after_its_data` | – |
| NV3: clean auto-start fetch keeps the old annotation | survived | survived |
| NV4: check drops `incomplete_rows` | survived | survived |
| NV5: named inline start takes over while fetched partitions remain | survived | survived |

## Attacks that did not land
- **#686's probes at 521ebed:** `probe_ruling_matrix.py` reports "PROBLEMS: none" for scenarios S1–S9. S9 now reads `sf=ds-26 cd=AUTO parts=[train,val]` with the old test partition cleared. `probe_s9_log.py`: log and status agree (`ds-2`). `probe_ordinary422.py`: `token=False` with the flag on and off.
- **#687's refusal leaves the record as it was.** In P1 (fetch, inline train, wider staged) and P3 (a 422, then the wider refusal), every field reads `UNCHANGED`: `current_dataset`, the annotation (equal and the same object), `_described_partitions`, the pending dataset, the validation warning, all six tensors and the network. A retry is refused identically. A start-fresh then loads the wider dataset: `sf=ds-4 cd=WIDE parts=all net=3x2`. #688 no longer logs a shortfall for a refused dataset, which main still does.
- **Ordering:** with no tensors passed, the binding helper returns immediately, and `_reload_dataset` writes the partition set after its refusal check. A refusal can only follow a rebind when the start also carries tensors (finding 4), and the record then matches what is bound.
- **Auto-start clearing missing partitions:** auto-start runs once on a fresh manager. An operator's val/test could only be loaded during the boot window, and keeping them under auto-start's train would mix two datasets. The change is documented in the CHANGELOG, `AGENTS.md` and the API reference.
- **The new `ValueError`:** the only caller that passes an annotation is `app.py:663`, which passes `as_fetch=True`. The route's typed body cannot carry either argument, `control_stream.py:479` calls it bare, canopy only posts over HTTP, and no other repo calls it.
- **Narrowing loses no real refusal:** juniper-data's only refusal 422s come from `datasets.py:279-305`, both texts carry the remedy wording, and the real over-cap csv_import and equities refusals keep the token in every stance.
- **Schema-less entries (item 5):** every entry in the real `/v1/generators` carries a dict schema, available or not (`generators.py:262`).
- **CHANGELOG:** 55 lines added, 0 removed against `ec8b5bd`, so no other PR's line was lost; the entry sits under [Unreleased] › Fixed. The docs' lifecycle wording matches the probe matrix.
- **Other probes:** `probe_start_fresh_interaction.py` and `probe_autostart.py` came back clean.

Everything I wrote is in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v688/`: `probes/` (new files `fakejd3.py`, `probe_687_interaction.py`, `probe_realjd_refusals.py`, `probe_realjd_blank.py`, `mutate_v688.py`, `make_nv1_tree.py`, `run_jd.bash`) and `logs/`. The extracted trees are deleted and the scratch juniper-data server is stopped. I changed no repo file; the only write outside scratch was fetching `pull/688/head` and `main` into the cascor clone.
