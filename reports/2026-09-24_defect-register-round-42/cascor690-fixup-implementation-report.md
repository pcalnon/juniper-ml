<!-- Archived verbatim 2026-09-24 from subagent a7b8f376d87c32f5e of session bc31e993 (final message). -->

The defect is fixed. #690 was still open, so I pushed a signed fixup onto `fix/shortfall-688-validation`. `_as_bool_stance` now reads `allow_truncation` exactly as juniper-data does: `"f"` and `"n"` are a refusal, and anything juniper-data rejects is no stance.

**Head:** `78e994144aa9884745e3c727e5f8547e543acefe`, signed (verified), parent `c4e002d`. I read the PR back: OPEN, MERGEABLE, two commits. The commit's tree is identical to the one I tested, and the attribution lines are its last paragraph. I updated the PR description (new section 7, refreshed results) via `gh api -X PATCH`. main has not moved from `7f4a721`.

**CI on the new head:** CI was still running when I wrote this: 11 success, 5 neutral (the Cursor automations), 5 in progress, 0 failures. The first head `c4e002d` had gone fully green, including unit tests on 3.12, 3.13, 3.14 and macOS, the integration suites, CodeQL and the Quality Gate.

**The producer rule I matched** (juniper-data main `0f0f7e0`):
- Every class that declares the field types it `allow_truncation: bool | None`, using pydantic's normal (lax) coercion, with no strict mode and no validator:
  - `EquitiesParams`: `juniper_data/generators/equities/params.py:107` (config at `:58`)
  - `EquitiesSeqParams`: inherits it (`juniper_data/generators/equities_seq/params.py:18`)
  - `CsvImportParams`: `juniper_data/generators/csv_import/params.py:66`
- Requests reach those classes as `params: dict[str, Any]` (`juniper_data/core/models.py:158`) through `params_class(**request.params)` (`juniper_data/api/routes/datasets.py:223`).
- pydantic-core's `str_as_bool` (`src/input/shared.rs`) accepts twelve strings, case-insensitive and not stripped:
  - false: `0`, `f`, `n`, `no`, `off`, `false`
  - true: `1`, `t`, `y`, `on`, `yes`, `true`

  Its only other non-bool spellings are the numbers 0 and 1, as int or whole float.
- I measured this through the three real classes over 85 values, and they agree on all of them: 20 true, 21 false, null, and 43 rejected with a 400.
  - The old reader disagreed on 45: `f`/`F`/`n`/`N` read as true, and 41 rejected values read as a stance.
  - The fixed reader disagrees on none.

Rejected values are now treated like a blank string: the key is present, so no default applies, and it is not a deferral.

**Counts on the new head:**
| Check | Result |
|---|---|
| Six named test files | 354 passed (150 / 38 / 41 / 103 / 10 / 12) |
| `tests/unit/api` | 2659 passed |
| 19 importer files, `--integration --slow --golden` | 255 passed, 10 subtests |
| `pre-commit run --all-files` | all passed, nothing rewritten |
| C901 | `_as_bool_stance` 6; flake8 clean |
| Symbol-loss screen | 3 findings, all waived by the first commit's line; the fixup alone has 0 |
| Docs screen | 1 warning, 0 failures |
| Mutation (extended harness) | 95 of 95 killed, control 354 green |

- **Mutation:**
  - Every one of the twelve spellings flipped to the other polarity is killed, and so is every one dropped.
  - Seven mutants for the other rules (whitespace stripping, case, numbers, truthiness fallback) are killed.
  - Round 3's 64 mutants, re-run, are all still killed.
  - Putting `c4e002d`'s code back fails 70 of the new tests.
- **Real juniper-data server:**
  - Now: `f`, `F`, `n`, `N`, `no`, `off`, `"0"`, `0` and `false` are refused (422) and get "explicitly refused", with the flag on or off.
  - At `c4e002d`: `f`/`F`/`n`/`N` got a plain "juniper-data fetch failed". The flag-on half of that run hit juniper-data's rate limit (429) partway through, but only after those four rows.

**Canopy lines** (canopy main `7ab994e5`, unchanged):
- `src/tests/unit/frontend/test_start_fresh_refusal_and_modal_text.py:42`: `CASCOR_SENTENCE`, the verbatim copy of the old #687 sentence (the comment at `:41` says so).
- `src/frontend/dashboard_manager.py:8381`: "Nothing was loaded: the dataset is still staged, and the results shown are still the previous run's.", inside `_start_fresh_required_alert` (`:8359`).

**Changed files (juniper-cascor):** `src/api/lifecycle/manager.py`, `src/tests/unit/api/test_allow_truncated_datasets.py`, `src/tests/unit/api/test_truncatable_generators.py`, `CHANGELOG.md`.

**Harnesses retained this round**, all uncommitted in juniper-ml `util/ad-hoc/`:
- `2026-09-24_cascor690_bool_stance_producer_table.py`: measures the producer's table and compares cascor against it.
- `2026-09-24_cascor690_bool_stance_realjd_probe.py`: runs each spelling against a real server.
- `2026-09-24_cascor690_as_bool_stance_mutation_check.py`: imports `2026-09-24_cascor688_fixforward_mutation_check.py` by path, so the two must stay together.

Earlier harnesses from this session are still there: `2026-09-24_cascor688_fixforward_mutation_check.py` and `2026-09-24_cascor688_realjd_error_texts.py`.

I deleted every tree I extracted this round, and the scratch server is stopped. Nothing was pushed with `git push`, merged, armed or branch-updated.
