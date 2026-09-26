<!-- Archived verbatim 2026-09-24 from subagent a7b8f376d87c32f5e of session bc31e993 (turn-ending report 3 of 5; an earlier report of a resumed agent). -->

I opened **PR #688**, read back with `gh pr view`: https://github.com/pcalnon/juniper-cascor/pull/688. It supersedes #686, which I commented on and closed; both states are read back.

- **Head:** `521ebed5393a4845f2133784c28760c5d5593dbc`, one signed commit (verified) on current main `ec8b5bd`, which includes #687.
- **Tree:** byte-identical to the tree I tested.
- **State:** open, MERGEABLE, not a draft, auto-merge not armed. At read-back 7 checks had passed and 8 were pending; I did not wait for them to finish.

**Contents.** It is #686's complete change set, with the #687 conflict resolved exactly as tested on the scratch copy:
- The staged-reload call passes both `fetch_path=` and `refuse_wider_than=`.
- `_reload_dataset` takes both keywords.
- #687's `_continued_network_dims_locked` and `_refuse_dataset_wider_than_network` are kept unchanged.
- `CHANGELOG.md` has one additions-only hunk: 55 lines added, 0 removed, every line on main kept.
- Main had not moved since my scratch test, so no re-merge was needed.

**Commit message.** The body opens with the supersede note, the reason and the resolution. It carries `Allow-Symbol-Loss: method:TestDerivation.test_an_entry_with_no_usable_schema_is_not_truncatable`. The two attribution lines are the last paragraph.

**PR description.** It is #686's description plus the supersede paragraph up top. I made three edits you didn't ask for, because leaving them would have been false:
- #686's "This PR now CONFLICTS with main" block is replaced by the resolution and this PR's own test results.
- The Summary's ruling bullets now say "once all of the fetch's partitions have been replaced" and include the start-fresh.
- "Not done here" now mentions the canopy `" The resulting dataset"` cut as being routed separately.

**Checks on the exact PR tree:**

| Check | Result |
|---|---|
| Four shortfall files, `test_start_fresh_carries_params.py`, #687's `test_start_refuses_wider_staged_dataset.py` | **201 passed** (43 / 37 / 37 / 64 / 10 / 10) |
| `tests/unit/api` | **2506 passed**, 0 failed |
| 17 importers, `--integration --slow --golden` | **213 passed**, 0 skipped, 10 subtests passed |
| flake8 C901 | `start_training` **11**, `_bind_start_tensors_locked` 8; exit 0 at max-complexity 15 |
| `pre-commit run --all-files` | every hook passed, nothing rewritten |
| Symbol-loss screen vs `origin/main` | OK: 1 finding, the renamed test, WAIVED |
| Docs-additions screen vs `origin/main` | OK: 3 small in-place edits (WARN), 0 FAIL |

**Mutation results:** 48 of 48 killed, 0 survived, 0 skipped, over a green control of 201, run on a scratch copy. I re-anchored the harness for this tree and noted that in its docstring.
- **NM1** is killed by `test_a_promoted_val_split_is_the_fetchs_own`.
- **NM11** is killed by `test_inline_train_beside_a_staged_fetch_is_replaced_by_the_fetch`.
- **NM19** fails 2 tests and **NM20** fails 3, starting with `test_a_start_fresh_keeps_the_record_and_what_it_stands_on[retained|inline-train]`.
- **NM4:** the literal version fails only through a `NameError`, so that verdict doesn't count. Its behaviour, ported to the new code, is killed by the manager-level test and by the real auto-start test.
- **Two new mutants pin the resolution itself.** Dropping `refuse_wider_than` from the call is killed by 5 of #687's tests. Dropping `fetch_path` is killed by `test_a_staged_start_is_told_to_start_again`.
- **Base check:** swapping in main's own `manager.py`/`app.py` fails 23 tests and errors 2.

**Changed (cascor, commit `521ebed`):**
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`
- `src/api/app.py`
- `src/api/lifecycle/manager.py`
- `src/tests/unit/api/test_allow_truncated_datasets.py`
- `src/tests/unit/api/test_auto_start_shortfall.py`
- `src/tests/unit/api/test_shortfall_lifecycle.py`
- `src/tests/unit/api/test_truncatable_generators.py`

In juniper-ml I edited `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/util/ad-hoc/2026-09-24_cascor686_fixup_mutation_check.py`, which is still uncommitted.

The existing worktree now tracks `fix/shortfall-mixed-provenance-and-678-followups-v2` at `521ebed`, clean. The old `fix/shortfall-mixed-provenance-and-678-followups` branch remains local and on the remote, since cleanup wasn't part of the brief.
