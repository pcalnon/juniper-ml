<!-- Archived verbatim 2026-09-24 from subagent a7b8f376d87c32f5e of session bc31e993 (turn-ending report 2 of 5; an earlier report of a resumed agent). -->

I pushed signed fixup `e452a66` to https://github.com/pcalnon/juniper-cascor/pull/686, and all five findings are fixed. **#686 is now blocked a different way:** #687 merged into main at 09:46Z (`ec8b5bd`) while I worked. GitHub reports #686 **CONFLICTING / DIRTY**, so auto-merge (still armed) can't fire, and no `pull_request` CI will run until someone resolves it.

**The conflict.** Two lines in `src/api/lifecycle/manager.py` that both PRs changed: the staged-reload call in `start_training`, and the `_reload_dataset` signature. `CHANGELOG.md` merges cleanly. No single-parent commit can clear it: both sides changed the same lines from the shared base, so it needs a real merge commit, which I'm not allowed to make. The fix is to keep both keywords, and keep #687's two new methods:
```python
                self._reload_dataset(fetch_path=_FETCH_PATH_STAGED_START, refuse_wider_than=self._continued_network_dims_locked(start_fresh), **self._pending_dataset_config)
    def _reload_dataset(self, *, fetch_path: Optional[str] = None, refuse_wider_than: Optional[Tuple[int, int]] = None, **cfg: Any) -> None:
```
I tested this resolution on a scratch copy: 201 passed (the named files plus #687's `test_start_refuses_wider_staged_dataset.py`), `tests/unit/api` 2506 passed, the 17 importers 213 passed, and `start_training` C901 is 11 with flake8 clean. I've added this to the PR description, updated via `gh api -X PATCH`.

**Head SHA:** `e452a66059d17c254157d781fca1963594b598ec`, parent `8f28272`. It is signed (verified), its tree is byte-identical to the one I tested, and both attribution trailers parse.

**The five findings:**
1. **C901** (CI flake8 was 16, local fixed tree 11): the binding block moved into a new `_bind_start_tensors_locked`. It is still called before the staged reload, and there is no `noqa`.
2. **Auto-start is bound wholesale:** it now calls `start_training(..., as_fetch=True)`. A partition the artifact lacks is cleared, and the record describes only the partitions it filled. An annotation passed without `as_fetch` now raises `ValueError`. The validator's `probe_s9_log.py` now shows the log and the status agreeing.
3. **Four new tests in `TestKeepWhileFetchedSplitsStay`**, one per surviving mutant: start-fresh (NM19, NM20), a promoted val split (NM1), and inline train beside a staged fetch (NM11). I also added a test for finding 2's case and removed the "full matrix" wording from `CHANGELOG.md`.
4. **A bare 422 is no longer a refusal:** only messages naming `allow_truncation` or `incomplete_rows` count. I checked juniper-data main: both refusals (`limits.py:168` and `:189`) say "Re-submit with allow_truncation=true", the route sends that text as the 422 detail, and juniper-data-client puts it in the exception message. New tests cover both flag states; `probe_ordinary422.py` now gives `token=False` for both.
5. **Docs:** `AGENTS.md` and the API reference now match the final code.

**Test counts on `e452a66`:**

| Suite | Result |
|---|---|
| The four shortfall files + `test_start_fresh_carries_params.py` | **191 passed** (43 / 37 / 37 / 64 / 10) |
| `tests/unit/api` | **2496 passed**, 0 failed |
| The 17 importers, `--integration --slow --golden` | **213 passed**, 0 skipped |

**Mutation check:** 46 of 46 killed, 0 survived, over a green control of 191, run on a scratch copy.
- **NM1:** killed by `test_a_promoted_val_split_is_the_fetchs_own`.
- **NM11:** killed by `test_inline_train_beside_a_staged_fetch_is_replaced_by_the_fetch`.
- **NM19 and NM20:** killed by `test_a_start_fresh_keeps_the_record_and_what_it_stands_on[retained|inline-train]`.
- **NM4 needs a caveat.** As the validator wrote it, NM4 now edits a path that never sees an annotation, so it "fails" only with a `NameError`, which proves nothing. I re-expressed its behaviour on the new code (adopt the caller's annotation but keep the old test split). That version is killed by two tests: the manager-level one, and a new one that runs the real auto-start twice.
- **All 35 first-round mutants** were re-anchored onto the refactor and re-run; all are killed.
- **Reverting to `8f28272`** fails 7 of the new tests.
- **One survivor on the first pass:** `I1f` (a caller-named inline dataset, like the in-process spiral, loses its name). I added a test for it and it is now killed.
- **The validator's own matrix probe** reports "PROBLEMS: none" over 69 steps.

**Pre-commit:** CI's own command, `pre-commit run --all-files`, passes every hook with nothing rewritten.

**Symbol-loss screen:** the fixup alone (`8f28272..e452a66`) has 0 findings. Against current main it reports 2 FAIL LOST plus 1 WARN, all of them #687's symbols that this branch doesn't have yet. The resolving merge brings them in.

**Left undone:** the conflict merge itself. I did not touch the canopy `" The resulting dataset"` cut; one of my tests avoids asserting through it.

**Changed (cascor, commit `e452a66`):**
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`
- `src/api/app.py`
- `src/api/lifecycle/manager.py`
- `src/tests/unit/api/test_allow_truncated_datasets.py`
- `src/tests/unit/api/test_auto_start_shortfall.py`
- `src/tests/unit/api/test_shortfall_lifecycle.py`
- `src/tests/unit/api/test_truncatable_generators.py`

I also updated the PR #686 description. The new mutation harness is at `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/util/ad-hoc/2026-09-24_cascor686_fixup_mutation_check.py`, uncommitted.
