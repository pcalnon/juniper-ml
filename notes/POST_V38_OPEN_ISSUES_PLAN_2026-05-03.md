# Post-V38 Open-Issues Remediation Plan

**Author:** Paul Calnon
**Date:** 2026-05-03
**Cycle:** Post-V01-V38 alignment closeout (juniper-ml)
**Status:** P-2 + P-3 implementations landed in cascor PR #183 (open, awaiting CI).
**Priority items:** P-2 + P-3 (net-new cascor main failures from PRs #177-180).

---

## 0. Context

The V01-V38 alignment cycle catalogue is closed. At cycle end, the absolute-final closeout enumerated five remaining open items handed off to follow-up work:

1. RC-4 multiprocessing race in cascor's candidate-training distributor (narrowed during V38 Phase A.2; needs a Docker repro env).
2. Net-new `test_snapshot_route_coverage.py` failure on cascor main from PRs #177-179.
3. Net-new lockfile drift on cascor main from PR #180.
4. Pinned-`isort` version mismatch between local conda envs (8.x) and pre-commit (5.13.2).
5. `torch._C` shadow in all three Juniper conda envs blocking local repro.

Subsequent investigation (this document, §2 below) revealed the cascor-main test failure is broader than originally captured — it's actually 5 failing tests across **two** test files added by PRs #179 + #180, not just one. P-2 has been re-scoped accordingly.

The rest of this document evaluates all five items, prioritizes P-2 and P-3 for immediate execution, and lays out the implementation plan.

---

## 1. Issue Inventory and Evaluation

### P-1 — Cascor candidate-training distributor RC-4 multiprocessing race

**Symptom.** When candidate training runs with sub-second per-candidate budgets (the parameters cascor's unit-test fixtures use), the parent process's `_process_training_results` occasionally sees `best_candidate=None` even though every worker returned `success=True` with a healthy non-None candidate object.
Phase A.2 of the V38 investigation confirmed the diagnostic `print(..., flush=True)` calls at four checkpoints in `train_candidates` / `_execute_candidate_training` / `_process_training_results` make the failure disappear deterministically — a classic Heisenbug.

**Severity.** Medium. The race only manifests under sub-second budgets; production-realistic candidate-training runs (which use larger candidate-pool sizes and longer per-candidate epochs) don't trip it. The four flaky tests have been retagged `@pytest.mark.integration` (V38 PR #181, merged) so the unit-test gate is unblocked.

**Blast radius.** Confined to the parallel candidate-training path in cascor; does not affect any other Juniper service.

**Suspected location.** `_task_distributor.distribute_and_collect` IPC boundary or the parent-side post-processing of worker-written `CandidateTrainingResult` objects.

**Blocker for direct investigation.** No working torch import in any local conda env (see P-5).

**Status.** Future-cycle item, narrowed but not fixed.

### P-2 — Net-new cascor unit-test failures from PRs #177-180

**Tests failing on cascor main HEAD `868d186` (post-PR-#181 merge):**

| Test | File | Source PR | Symptom |
|------|------|-----------|---------|
| `TestReplaySnapshot.test_replay_control_range` | `src/tests/unit/api/test_snapshot_route_coverage.py:767` | #179 (Feature/b 4 restore investigating) | `AssertionError: assert {'end': 4, 'start': 1} == {'end': 4, 's...ime_index': 1}` — response payload lacks `time_index` field |
| `TestWeightHistoryRoundTrip.test_meta_attrs_persist` | `src/tests/unit/test_snapshot_weight_history.py` | #180 (snapshot persist with adaptive sampling) | `assert False` — meta-attrs missing from persisted snapshot |
| `TestWeightHistoryRoundTrip.test_sample_indices_round_trip` | same | #180 | `assert None is not None` — sample-indices array not present after load |
| `TestWeightHistoryRoundTrip.test_output_tensors_round_trip` | same | #180 | `TypeError: 'NoneType' object is not subscriptable` — load returns None for the output-tensors record |
| `TestWeightHistoryRoundTrip.test_hidden_unit_tensors_round_trip` | same | #180 | same TypeError, hidden-unit-tensors record |

**Severity.** High. Cascor main is currently red. Until P-2 is fixed, every PR opened against cascor inherits this failure (V38 PR #181 already did) and the unit-test gate cannot serve as a release signal.

**Blast radius.** Cascor only. Other repos' CI is unaffected.

**Likely root cause shape.** The four `test_snapshot_weight_history` failures cluster strongly: they all reduce to "load returns None where the test expects data". This suggests a single upstream defect — either:

1. The save path (added in #180) does not actually persist the new fields, or
2. The load path does not deserialize them, or
3. The fixture's save invocation does not flush correctly before the load runs.

The single `test_replay_control_range` failure is independent: it expects a `time_index` field that the actual replay-control-range response endpoint does not include. Could be (a) endpoint never returned it (test stale) or (b) endpoint stopped returning it (regression).

**Effort.** Low-medium. Both clusters are likely 1-2 line fixes per cluster once the source-of-truth is identified.

### P-3 — Net-new cascor lockfile drift from juniper-data-client 0.4.1

**Symptom.** `Lockfile Freshness` job on cascor main fails with a 1-line diff:

```text
@@ -48,7 +48,7 @@
-juniper-data-client==0.4.0
+juniper-data-client==0.4.1
```

**Cause.** juniper-data-client released 0.4.1 (an alignment-cycle artifact — increment for downstream alignment). cascor's `pyproject.toml` declares `juniper-data-client>=0.4.0`, which now resolves to 0.4.1. The lockfile was last regenerated when 0.4.0 was the latest available.

**Severity.** Low. Single transitive-pin bump. No code changes needed in cascor; just regenerate `requirements.lock`.

**Blast radius.** Cascor only.

**Effort.** Trivial. One `uv pip compile` invocation, one commit, one PR.

### P-4 — Local-vs-pre-commit isort version mismatch

**Symptom.** Local `JuniperCascor` conda env ships `isort 8.0.1`. The cascor `.pre-commit-config.yaml:122` pins `pycqa/isort@5.13.2`. Auto-fix output differs (e.g., 8.x expands long imports to multi-line; 5.13.2 with `--line-length=512` collapses them). During the V38 diagnostic cycle, this caused two unnecessary CI iterations (round 2 + round 3) where local-applied auto-fixes did not match what CI expected.

**Severity.** Low. Causes occasional CI churn but does not break correctness. Workaround: always run `pre-commit run isort --all-files` (which uses pre-commit's pinned version) instead of `isort` directly.

**Blast radius.** Affects every cascor PR's developer feedback loop until aligned.

**Effort.** Trivial. Pick one side: either upgrade pre-commit's pin to 8.x or downgrade local conda env's isort to 5.13.2.

### P-5 — `torch._C` shadow in all three Juniper conda envs

**Symptom.** All three envs (`JuniperCascor`, `JuniperCanopy`, `JuniperData`) have `torch/_C/` (a directory of `.pyi` type stubs) **and** `torch/_C.cpython-3*.so` (the C extension) in `site-packages`. Python's import machinery prefers the directory, so `import torch` raises `ImportError: Failed to load PyTorch C extensions`.

**Severity.** Medium. Blocks any local repro of cascor tests that exercise torch (which is most of them). During the V38 investigation, P-5 forced the entire investigation into CI-only mode (Phase A.2 instead of Phase A.1).

**Blast radius.** All three Juniper application conda envs.

**Likely root cause.** Mixed install of torch as both a wheel (which ships `_C.cpython-*.so`) and a separate type-stubs package (which ships `_C/__init__.pyi`). On install, the stubs package's `_C/` directory landed alongside the wheel's `_C.so` — Python sees the directory first and ignores the .so.

**Effort.** Low per-env. Either remove the stubs `_C/` directory, reinstall torch, or pin a torch version that doesn't ship clashing stubs. Best done in `juniper-deploy`'s conda environment YAMLs so it's reproducible.

---

## 2. Prioritization

Per the user's directive, **P-2 and P-3 are prioritized for immediate execution**. The remaining items (P-1, P-4, P-5) are documented here but deferred to subsequent cycles.

### Execution order for P-2 + P-3

1. **P-3 (lockfile bump).** Smallest, safest, fastest. Single-line `requirements.lock` regeneration. Land first to demonstrate cascor main can return to green for at least one job.

2. **P-2 cluster A (test_snapshot_weight_history — 4 failures from PR #180).** Investigate the persist/load round-trip. Fix the upstream defect. Either repair the implementation or amend the test if the implementation is intentional.

3. **P-2 cluster B (test_replay_control_range — 1 failure from PR #179).** Investigate the endpoint vs test mismatch. Decide whether the endpoint should return `time_index` or whether the test is stale.

4. Confirm cascor main goes fully green on the next CI run after P-3 + P-2 land.

### Why this order

- P-3 is independent of P-2 (lockfile vs test). Landing P-3 first means even if P-2 takes longer, P-3 closes one gate.
- P-2 cluster A (4 tests, 1 file, 1 PR source, similar symptom shape) almost certainly reduces to a single root cause; fix once, land four checkmarks.
- P-2 cluster B is independent of cluster A and may be quick (1-line endpoint fix) but is ranked third because it's a payload-shape question that may require reading the spec.

### Why P-1, P-4, P-5 are not prioritized

- **P-1.** Needs P-5 fixed first (no Docker repro env yet). Distinct from cascor-main-red status — cascor's unit-test gate now passes the rest of the matrix; only P-2 is blocking.
- **P-4.** Workaround exists (`pre-commit run isort` always does the right thing). Cosmetic/DX, not correctness.
- **P-5.** Foundational for P-1 but not blocking any current CI. A separate workspace-setup project.

---

## 3. Per-Issue Remediation Plans

### P-3 — Lockfile bump

#### Steps

1. Create branch `fix/v39-lockfile-bump-juniper-data-client` off cascor main.
2. Run `uv pip compile pyproject.toml --extra ml --extra api --extra observability --extra juniper-data --index-strategy unsafe-best-match --no-emit-package torch -o requirements.lock` (the canonical invocation per the workflow).
3. Verify the diff is exactly the `juniper-data-client==0.4.0` → `0.4.1` line and nothing else (any unexpected churn warrants investigation before committing).
4. Commit: `fix(deps): bump juniper-data-client lockfile pin 0.4.0 → 0.4.1 (P-3)`.
5. Push, open PR to main, merge once CI clears the Lockfile Freshness gate.

#### Risks

- Other transitive pins might drift during regeneration. Mitigation: inspect the diff before commit; if scope expands beyond expected, separate into its own analysis.

### P-2 cluster A — Snapshot weight-history round-trip

#### Investigation steps

1. Check out cascor `868d186` locally.
2. Read `src/tests/unit/test_snapshot_weight_history.py` end-to-end — fixtures, what the round-trip flow looks like, what each of the 4 failing tests expects.
3. Read PR #180's diff to find what was added on the save side (likely `src/api/routes/snapshots.py` and/or a `src/snapshot/*.py` helper) and the load side.
4. Identify which side of the round-trip is broken:
   - If save writes the field but load doesn't read it → fix load.
   - If save doesn't write the field at all → fix save.
   - If both correct in isolation but the fixture path has a sequencing bug → fix fixture.
5. Apply minimum fix.

#### Possible outcomes

- **Implementation defect** (most likely given the test-was-just-added pattern). Fix in the implementation file.
- **Test/spec disagreement**. Bring the spec docstring (often in PR description or design doc) and the test into alignment.
- **Fixture sequencing bug**. Reorder save/load steps in the fixture.

#### Risk

The 4 failures share a symptom shape, so the root cause is almost certainly upstream of all four. Fixing it fixes all four. Risk is low.

### P-2 cluster B — Replay-control-range `time_index` field

#### Investigation steps

1. Read `src/tests/unit/api/test_snapshot_route_coverage.py:767` (the assertion).
2. Read the corresponding endpoint handler (`src/api/routes/snapshots.py` — the `replay_control` route).
3. Determine whether `time_index` should be in the response payload:
   - If the spec / design doc says yes → fix the endpoint to include it.
   - If the spec says no (or the field was deprecated) → fix the test.
4. Apply minimum fix.

#### Risk

Low. The field is either there or it isn't.

### P-2 + P-3 PR shape

Two paths:

- **Bundled.** Single PR fixes lockfile + both test clusters. Cleaner from a CI-green perspective (one PR to verify). Slightly larger blast radius if reverted.
- **Separate.** Three PRs (P-3 alone, P-2 cluster A, P-2 cluster B). Each is independently revertible.

**Recommendation:** start with two PRs: one for P-3 (smallest, lands first), one for P-2 (clusters A + B together — both are snapshot-related test maintenance). If P-2's investigation reveals deeper defects in either cluster, split P-2 at the commit level inside that PR.

---

## 4. Implementation Tracking

This plan is followed by immediate execution per the user directive. Implementation will run as:

1. Push P-3 fix; verify CI green on the Lockfile Freshness job.
2. Investigate P-2 cluster A (snapshot weight-history) on a feature branch off main; fix; verify the four tests pass.
3. Investigate P-2 cluster B (replay-control-range) on the same branch; fix; verify the test passes.
4. Open the P-2 PR; merge once CI green.
5. Confirm cascor main is fully green on the post-merge CI run.
6. Update the deferred-items list in `notes/CI_ALIGNMENT_AUDIT_2026-04-29.md` (and findings doc) to mark P-2 and P-3 as closed; the cascor-side post-V38 backlog reduces to P-1 only.

P-1, P-4, P-5 remain documented here as future-cycle items.

---

## 4a. Implementation Results (2026-05-03)

### P-2 cluster A — root cause and fix

The cluster collapses to a single defect. ``CascadeHDF5Serializer._save_weight_history`` writes per-sample hidden-unit bias as a 0-d ndarray (``np.asarray(float_value, dtype=np.float32)``), and the generic ``snapshot_common.save_numpy_array`` helper was unconditionally requesting ``compression=gzip`` for every dataset. h5py rejects chunk/filter options on scalar datasets with ``TypeError: Scalar datasets don't support chunk/filter options``, and because the writer is called inside ``save_network``'s try/except, the entire save returns False mid-flight. Every downstream round-trip assertion then fails because ``loaded.weight_history`` is None.

Verified locally with a 3-line h5py reproducer: ``create_dataset(..., compression="gzip")`` on a 0-d array raises with exactly that message; the same call without compression succeeds.

**Fix.** In ``snapshot_common.save_numpy_array``, fall back to an uncompressed dataset when ``array.ndim == 0``. Compression behaviour for every 1+-d call site is unchanged. Two-line diff. Documented schema (``bias/0050  (float32 dataset, [])  — scalar``) is preserved.

### P-2 cluster B — root cause and fix

The ``range`` action handler in ``TrainingLifecycleManager.replay_control`` discarded the dict returned by ``session.set_range(start, end)`` (which carries the re-clamped ``time_index``) and instead returned ``session.state_summary()``, whose ``range`` field is ``{start, end}`` only.

**Fix.** Capture ``set_range``'s return value and merge it into ``state_summary`` so the route response carries ``{start, end, time_index}``. Five-line diff.

### P-3 — cherry-picked into the P-2 branch

Originally opened as PR #182 (1-line lockfile bump, ``juniper-data-client==0.4.0`` → ``0.4.1``). PR #182's CI failed on the same P-2 unit-test failures, so the lockfile bump was cherry-picked into the P-2 branch to keep CI green and form one self-consistent merge unit. PR #182 will be closed superseded once #183 lands.

### Final delivery

| PR | Repo | Branch | Scope |
|---|---|---|---|
| #183 | juniper-cascor | ``fix/p2-snapshot-test-failures`` | P-2 cluster A + cluster B + P-3 |
| #182 | juniper-cascor | ``fix/p3-lockfile-juniper-data-client-0.4.1`` | superseded by #183 |

---

## 5. Decision Log

| Decision | Reasoning |
|---|---|
| Bundle P-2 cluster A and B in one PR | Both are snapshot-test maintenance; reviewers can evaluate them together. Each cluster is internally cohesive. |
| Land P-3 separately | Fully independent of P-2; trivial to verify; landing it first restores one CI gate immediately. |
| Defer P-1 | Cannot proceed without a Docker repro env; gated on P-5. |
| Defer P-4 | Workaround exists; cosmetic. |
| Defer P-5 | Foundational for P-1 but a separate workstream (env / Docker), not a CI-pipeline fix. |
| Use the canonical `uv pip compile` invocation from cascor's lockfile-update workflow | Matches what CI uses to verify; guarantees the regenerated file passes the freshness check. |

---

## 6. Linting

After saving, run:

```bash
markdownlint -c .markdownlint.yaml notes/POST_V38_OPEN_ISSUES_PLAN_2026-05-03.md
```

Compliance: line-length 512, no trailing-punctuation in headings, single h1.
