<!-- Archived verbatim 2026-09-24 from subagent a7b8f376d87c32f5e of session bc31e993 (turn-ending report 4 of 5; an earlier report of a resumed agent). -->

I opened juniper-cascor **#690**: https://github.com/pcalnon/juniper-cascor/pull/690. I read it back: OPEN, MERGEABLE, base `main`, branch `fix/shortfall-688-validation`. It fixes #688's validation findings, and every check below passed, including all mutants killed.

**Head SHA:** `c4e002d2b3e65ea42ae693deb2a22529a00e8a97`. It is one commit, signed and verified. Its parent is `7f4a72132572`, and its tree (`47ebd9ae…`) is byte-identical to the one I tested. The commit body carries the `Allow-Symbol-Loss` line, and the two attribution lines are its last paragraph.

**CI at report time:** 8 success, including Sequence Safety, Memory Budget, Verify AGENTS.md Last Updated, Golden and Documentation Links. Five Cursor automations are neutral. Seven are still running: Pre-commit on 3.12, 3.13 and 3.14, CodeQL, and the two image builds.

**Per item:**
1. **400s read as refusals (MEDIUM).**
   - The check now matches juniper-data's sentence "Re-submit with allow_truncation=true", verified at `limits.py:168` and `:189` on juniper-data main `0f0f7e0`. When the error carries a status, it must also be a 422.
   - A blank string is no longer a deferral; only `null` defers.
   - Fixed the comment and docstrings in `manager.py`, the refusal rule in `AGENTS.md`, and #688's `CHANGELOG.md` bullet, including the `n_spirals=1` example, which is a 400.
   - The tests now use juniper-data's own texts, captured from a real server.
   - Mutants killed: P1a–P1g (P1b and P1c are NV4's two clauses dropped), A1, and B1a–B1c.
   - On a rebuilt real juniper-data main server, both of the validator's probes show every 400 plain in both flag positions, and every real refusal keeps its token.
2. **Partition record on #687's refusal (MEDIUM).** `_assert_nothing_moved` now also checks `_described_partitions`. A new arm is refused after an inline-train start, then shows an inline val+test start clears the record. NV1 is killed by my harness, by the validator's `mutate_v688.py`, and on the tree `make_nv1_tree.py` builds.
3. **Auto-start log vs status (LOW).** The log now runs after the staged reload, only if the annotation is still the one bound. Two new arms cover P4a and P4b, and mutants L3a–L3d are killed. `probe_687_interaction.py` reports `PROBLEMS: none`.
4. **"Nothing was loaded" (LOW).** Reworded as you specified; the old text was not pinned by any test. W4a is killed.
5. **NV3 and NV5 (LOW).** NV3 is killed by a partial auto-start fetch followed by a clean one, run through the real auto-start. NV5 is killed by a fetch followed by the route's spiral start. Both arms are new.
6. **NITs.** The CHANGELOG now lists all four corrections. The canopy citation is re-derived as `7ab994e5`, `:8404-8413`; the function body is unchanged.

**Counts:**

| Check | Result |
|---|---|
| Four shortfall files, start-fresh file, #687's file | 233 passed (63 / 38 / 41 / 69 / 10 / 12); was 201 |
| `tests/unit/api` | 2538 passed |
| Importers, `--integration --slow --golden` | 255 passed, 0 skipped, 10 subtests |
| Mutation (my harness) | 64 of 64 killed, green control of 233; putting main's code back fails 28 of the new arms |
| Validator's `mutate_v688.py` | NV1, NV2, NV3, NV5 killed; NV4 skipped because its anchor no longer exists (covered by P1b and P1c) |
| `pre-commit run --all-files` | every hook passed, nothing rewritten |
| C901 | `start_training` 11 → 12 (max 15) |
| Symbol-loss screen | 3 findings, all waived: two replaced tests and `_previous_run` |
| Docs screen | 1 warning, 0 failures |
| AGENTS.md size budget | 52,076 / 58,189 chars |

I ran 19 importer files rather than the 17 from last round, because I widened the search for files that import the changed code.

**Not done, and new findings:**
- canopy's second cut is left alone, as instructed.
- **New defect, not fixed:** `_as_bool_stance` reads `"f"` and `"n"` as `True`, while juniper-data reads them as `False`. So a caller sending `"f"` gets a plain failure with no remedy when juniper-data refuses.
- canopy's `test_start_fresh_refusal_and_modal_text.py` keeps a verbatim copy of the old #687 sentence (`CASCOR_SENTENCE`). canopy's own alert also says "Nothing was loaded". Nothing breaks, because canopy parses only the marker and the first sentence, but the copy is stale.

**Changed files** (juniper-cascor): `AGENTS.md`, `CHANGELOG.md`, `src/api/app.py`, `src/api/lifecycle/manager.py`, and five test files in `src/tests/unit/api/`: `test_allow_truncated_datasets.py`, `test_auto_start_shortfall.py`, `test_shortfall_lifecycle.py`, `test_start_refuses_wider_staged_dataset.py`, `test_truncatable_generators.py`.

**Retained harnesses** (uncommitted, in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/util/ad-hoc/`):
- `2026-09-24_cascor688_fixforward_mutation_check.py` — the round-3 mutation harness.
- `2026-09-24_cascor688_realjd_error_texts.py` — captures real juniper-data error texts.

The two earlier rounds' harnesses are still there, also uncommitted.

**Cleanup:** I deleted the juniper-data tree I rebuilt (`v688/jd`, `jdstore`, `jdimport`), all mutation scratch trees and the NV1 tree; the scratch server has exited. The local branch now points at the signed PR head. Nothing was pushed, merged, armed or branch-updated.
