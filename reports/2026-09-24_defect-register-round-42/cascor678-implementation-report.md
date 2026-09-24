<!-- Archived verbatim 2026-09-24 from subagent a62c802ad61b85d03 of session bc31e993 (final message). -->

All six validation items are fixed and pushed to cascor#678, and it is merged. `pcalnon` merged it at 20:22:13Z as `0e016a7c6cc0`, with the default squash message instead of your curated one. I did not merge anything.

**What the default message means for `main`:**
- `main`'s tree is byte-identical to the final PR head `71310f9`, so the content landed intact.
- The subject is the stale "…re-decided every run…".
- The body opens with the first commit's four now-false statements; the corrections follow in the later commits' messages.
- `Allow-Symbol-Loss:` is not parsed as a trailer on `main`, because it isn't in the message's last paragraph. That's harmless here: both findings are WARNs, which never fail the screen.

**Commits I pushed** (all GitHub-verified):
- `281bc5243a1d55439d301b9bdfe56c3776cc9062`: the validation fixes.
- `update-branch` then created merge commit `40c1c5ea7c6958e5453347fe13ea15ab882b6f20`.
- `71310f9b1e87d9cfbbec46cc2759e0de65656479`: a second, one-line commit. My `AGENTS.md` edit tripped the `Verify AGENTS.md Last Updated` check, so I bumped the date. That makes two commits where you asked for one.

**Per item:**
1. **CodeQL:** the test helper now returns `(result, reads)` and callers unpack `(…), reads`, with no suppression. Alerts #6407–#6411 are all `fixed` as of 19:57:11Z, and none are open on the PR's merge ref. All five threads were already resolved by `github-advanced-security[bot]` itself, which I confirmed via GraphQL, so I did not run `resolveReviewThread`.
2. **Annotation order:** `_reload_dataset` builds the annotation first and assigns it only after the tensors are bound. The restore in `_consume_pending_dataset_locked` guarded nothing any more, so the helper is gone and the staged consume is inline again, still under the C901 ceiling. New tests poll status mid-conversion through the real fetch path, and check that a refused artifact binds neither data nor annotation. An older fixture that depended on the write-first order now runs the reload to completion.
3. **Empty cached set:** a listing in which no entry carries a schema is now a failed read and is not memoised. The resolver's fifth value is a reason code (list unreadable / not truncatable), and the describer is told the flag setting. A refusal never names the flag while it is on, including for an undeclared generator or a request that sent an explicit `null`. Tested on the resolver, the staged path and auto-start.
4. **Retry text:** a failed start stays staged, so start again; a live swap is re-issued; auto-start needs a restart.
5. **Docs:** the `AGENTS.md` table cell was at the 512-column limit, so the details went into a note under the table. It covers the `GET /v1/generators` dependency, the withheld-opt-in remedy and the annotation lifecycle. The `dataset_shortfall` entry in `docs/api/JUNIPER_CASCOR_API_REFERENCE.md` now describes the lifecycle. `AGENTS.md` is at 51,289 of 58,189 characters, and the memory budget passes.
6. **PR:** retitled via `--input`. The two WARNs are now described as not needing a waiver, with the trailer inert for them. The body has the proposed squash message, with `Allow-Symbol-Loss:` exactly as in the first commit plus both attribution lines. It went unused at merge.

**Tests (all `-v`)**
- Before `update-branch`: `tests/unit/api` 2426 passed; the rest of `tests/unit` plus `tests/integration/api` 2785 passed, 157 skipped; the directly affected files 208 passed; drift 3/3.
- On the merged head `71310f9`: 2426 passed, and the rest 2848 passed, 157 skipped. The higher count comes from main's new tests.
- pre-commit passes on every changed file.
- Both sequence-safety screens pass: `fail=0`, WARNs only.
- A 3-way CHANGELOG merge against `main` had 0 conflicts.

**Non-vacuity against `e02020d`:** 18 of 121 tests fail, each on its intended assertion; examples are the mid-conversion poll, `DID NOT RAISE` for a schema-less listing, and the knob named on both paths. The other 103 pass.

**CI:** all 24 required checks were green on `71310f9` before the merge. The post-merge checks on `0e016a7` (tests, CodeQL, the symbol and docs screen, golden, conformance) were still queued when I stopped.

**CHANGELOG headings:** not de-duplicated. The second `### Added`/`### Fixed` pair sits in the section `main` kept appending to (four commits during this PR), so merging them would recreate the conflict for every open PR. The worktree is kept.

**Changed** (juniper-cascor, commits `281bc52` and `71310f9`):
- `src/api/lifecycle/manager.py`
- `src/api/app.py`
- `src/tests/unit/api/test_truncatable_generators.py`
- `src/tests/unit/api/test_shortfall_lifecycle.py`
- `src/tests/unit/api/test_allow_truncated_datasets.py`
- `src/tests/unit/api/test_auto_start_shortfall.py`
- `AGENTS.md`
- `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`
- `CHANGELOG.md`

Plus #678's title and body.
