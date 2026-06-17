# juniper-cascor — Golden / Snapshot Regression Suite: Build Plan (WS-6 Safety Gate)

**Project**: Juniper ML Research Platform — cascor pre-refactor regression safety net (roadmap **OUT-12**)
**Repository**: pcalnon/juniper-cascor (the suite lands here); plan hosted in pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (DRAFT build plan — scoped from a live cascor recon 2026-06-17; OQ-13 resolved by evidence; pending Paul's concurrence on §0)
**Last Updated**: 2026-06-17

---

> **What this is.** A build plan for the **golden / snapshot regression suite** that must exist in `juniper-cascor` *before* the WS-6 cutover (refactoring cascor onto `juniper-service-core` / `juniper-model-core`). It is **OUT-12** in [`JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md`](JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md) and the explicit trigger-gate for WS-6 in the [middleware refactor plan](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md) §2.7 / §3.4 / Part 8. The suite is captured on `origin/main` *now* (as insurance), then re-run post-refactor; WS-6 is accepted only if it — plus the model-core conformance kit — stays green.
>
> **Why now (even though WS-6 is deferred):** capturing the baseline is only valid *before* the refactor touches the code. It is the independent, non-colliding insurance the roadmap (§6.4) flags as safe to do early. It is read-only against behavior — it adds tests, changes no production code.
>
> **Grounding.** Scoped from a live read of `juniper-cascor` at `origin/main` `88fcddb` (a dedicated recon agent; `file:line` evidence below). Dup-guard 2026-06-17: no open cascor PR and zero `golden`/`WS-6`/`conformance` work in the repo.

---

## §0. Status & decisions needing Paul

- **D-G1 — OQ-13 (compare strategy): RESOLVED by evidence → tolerance-based, not hashing** (§1). This was the one open design fork; the evidence is decisive, and the refactor plan's OQ table already leaned "Tolerance (nondeterminism)." Recorded as resolved; flag if you disagree.
- **D-G2 — Suite lives in `juniper-cascor` `src/tests/` (not the conformance kit).** It is cascor-specific regression safety, distinct from the model-agnostic `juniper-model-core` conformance kit (which is the *other* half of the WS-6 gate). Concur?
- **D-G3 — Capture timing.** Capture/commit the goldens **now** on `main` as insurance (recommended), vs. defer until WS-6 actually starts. Recommend **now** — the baseline is only trustworthy pre-refactor.
- **D-G4 — Tolerances** (`atol`/`rtol`) are calibrated empirically during implementation (§3); the starting values below are proposals, finalized against 2–3 real runs.

Everything else is mechanical execution (§7).

## §1. OQ-13 resolution — tolerance-based comparison

**Decision: compare float trajectories/weights with numeric tolerance; compare structural/discrete signals exactly. Do not hash trajectories.**

Evidence (cascor `origin/main`):

- **Candidate training is multiprocessing-parallel by default** — `_calculate_optimal_process_count()` → `max(1, cores-1)`, results reduced across forkserver/spawn (and optional remote WS) workers (`src/cascade_correlation/cascade_correlation.py:2274-2412`). Cross-worker float reduction order is not bit-stable.
- **The resume-determinism test is already `xfail`** (`src/tests/.../test_comprehensive_serialization.py:44`) and even it uses `assert_array_almost_equal(decimal=5)` — exact reproducibility is not a property cascor has today.
- **Every existing numeric assertion is tolerance-based** (`torch.allclose(atol=1e-6)`, `np.testing.assert_array_almost_equal`), never a hash; shared tolerance fixture `{rtol:1e-5, atol:1e-8, correlation_tol:1e-4, ...}` (`src/tests/conftest.py:653`).
- **BLAS threads are pinned to 1 only under xdist** (`conftest.py:137-143`) — a serial golden run would otherwise inherit multi-threaded BLAS nondeterminism.

**Comparison strategy:**

| Signal | Compare how |
|--------|-------------|
| Per-epoch `train_loss` / `train_accuracy` / `value_*`; per-unit `correlation`; learned weights/topology arrays | **Tolerance** — `np.testing.assert_allclose`, start `rtol=1e-3, atol=1e-4` (weights/predict round-trip: `atol=1e-6`) |
| Hidden-unit **growth count sequence**, `hidden_units_added` ordering, `_completion_reason`, topology shapes, route status codes | **Exact** |

**Determinism hardening for the golden lane (mandatory):** set `CASCOR_NUM_PROCESSES=1` (forces `_execute_sequential_training`, `cascade_correlation.py:2336-2339`), pin BLAS threads to 1 explicitly in the fixture (don't rely on the xdist-only block), seed `random_seed=42`. Record the `torch`/`numpy` versions alongside the goldens.

## §2. Scope & file layout

New tests + checked-in reference artifacts under `src/tests/` (none exist today — `src/tests/fixtures/` is absent; the ~14 existing `*snapshot*` tests exercise the **HDF5 serializer feature**, not golden trajectories or API responses):

```text
src/tests/
  fixtures/golden/                          # NEW — checked-in reference artifacts
    two_spiral_seed42.npz                    # frozen (X, y) from SpiralDataGenerator.generate_2_spiral
    golden_trajectory_seed42.json            # per-epoch loss/accuracy + per-iter correlation + growth sequence + completion_reason
    golden_topology_seed42.npz               # post-train output_weights/bias + hidden-unit weights
    api_snapshots/*.json                     # scrubbed response bodies, one per route
  integration/
    test_golden_trajectory.py                # NEW  (markers: integration, slow, golden)
    test_golden_serialization_roundtrip.py   # NEW  (trained-net predict survives save/load)
  integration/api/
    test_golden_api_snapshots.py             # NEW  (scrubbed JSON snapshots via create_app + TestClient)
```

Add a `golden` marker to `pyproject.toml [tool.pytest.ini_options].markers`.

## §3. Deterministic capture config (CI-affordable)

Use the **test-local** generator (lightweight, seed-parameterized), not the production `SpiralProblem`:
`SpiralDataGenerator.generate_2_spiral(n_per_spiral=30, noise=0.05, seed=42)` (`src/tests/unit/test_data/generators.py:42`) — freeze its output to `two_spiral_seed42.npz` so a future generator change can't silently move the goldens.

Network/train config: `random_seed=42`, `max_hidden_units=3`, `candidate_pool_size=2`, `candidate_epochs=3`, `output_epochs=3`, `max_epochs=5`, `early_stopping=False`, `CASCOR_NUM_PROCESSES=1`, BLAS=1. Expected runtime: single-digit seconds, well within the existing `@pytest.mark.timeout(120)`. Trajectory surface = `network.history` (keys `train_loss`, `value_loss`, `train_accuracy`, `value_accuracy`, `hidden_units_added[{correlation, weight_shape, unit_index}]`; `cascade_correlation.py:741-746`).

## §4. What to capture

1. **Trajectory** (`test_golden_trajectory.py`): fixed-seed two-spiral train → assert `history` float series within tolerance, and the growth-count sequence + `_completion_reason` exactly.
2. **Serialization round-trip** (`test_golden_serialization_roundtrip.py`): after the fixed-seed train, `predict(X_holdout)` → `CascadeHDF5Serializer.save_network` → `load_network` → `predict` → `torch.allclose(atol=1e-6)`. (Untrained round-trip is already covered; this adds the **trained** case. Leave the resume-training determinism `xfail` — the gate targets predict-after-load only.)
3. **API snapshots** (`test_golden_api_snapshots.py`): `create_app(Settings(auto_start=False))` under `TestClient` (reuse the daemon-thread `__exit__` fixture shape from `integration/api/test_api_full_lifecycle.py:45-72` to dodge the anyio shutdown hang). Snapshot in the **fresh, no-network** state (deterministic, no 404): `/v1/health`, `/v1/training/status`, `/v1/metrics/history`, `/v1/metrics/transport`, `/v1/history/dataset_swaps`. Then create a network + tiny fixed-seed train and snapshot `/v1/network`, `/v1/network/topology`, `/v1/network/stats`, `/v1/metrics`.

**Volatile fields to scrub** (recursive key-strip before compare; missing one ⇒ flaky): `meta.timestamp`, `git_sha`, `build_date`, `version`, `duration_ms`, `uptime_seconds`, all `*_total` counters, `uuid`, `server_instance_id`, `snapshot_seq`, connection counts, `state_machine.timestamp`, per-element metric `timestamp`s. Weight arrays in `/v1/network/topology|stats` → tolerance-compare, not exact-snapshot.

## §5. CI wiring

- Add the `golden` marker; tag the suite `integration` + `slow` + `golden`.
- Run **serially** (BLAS=1, `CASCOR_NUM_PROCESSES=1`); **never under xdist** (parallel reduction nondeterminism).
- The default `run_tests.bash` is unit-only, so the goldens don't bloat the fast loop; invoke them in a dedicated CI lane/job (e.g. `-m "golden"`) on the GIL 3.13 env (`JuniperCascor1`) — the free-threading guard aborts the lane under `Py_GIL_DISABLED`.
- Per the ecosystem rule, `gh workflow run` the new lane immediately (lint-green ≠ run-green).

## §6. How it gates WS-6

The refactor plan makes this explicit (§3.4, §2.7 kill-criterion, RK-5): capture the goldens on `origin/main` **before** the service-core/model-core repoint; re-run after each of WS-6's 6a (re-export shim) and 6b (interface adoption) steps. Any tolerance-exceeding float drift or any change to a structural sequence / `completion_reason` / route status **blocks the cutover**. If the suite cannot be kept green without changing observable behavior, the WS-6 kill-criterion fires (cascor keeps its own service stack).

## §7. Implementation steps (ordered — for the build thread)

1. Add the `golden` pytest marker + a `golden`-lane invocation (and CI job).
2. Write the deterministic capture fixture (seed, BLAS=1, `CASCOR_NUM_PROCESSES=1`) + the recursive volatile-field scrubber helper.
3. Freeze `two_spiral_seed42.npz`.
4. Implement the 3 test modules in **capture mode** first (write the goldens), eyeball them for sanity, then flip to **assert mode**.
5. Run 2–3 times (and ideally on a second machine / the docker image) to **calibrate tolerances**; widen only with evidence; document chosen tolerances next to each fixture.
6. Confirm the lane is green serially on `JuniperCascor1`; `gh workflow run` the CI lane.
7. PR into `juniper-cascor` (`test(golden): WS-6 pre-refactor regression baseline`), referencing this plan and roadmap OUT-12.

## §8. Risks & guardrails

| Risk | Guardrail |
|------|-----------|
| Multiprocessing/BLAS nondeterminism flakes the goldens | `CASCOR_NUM_PROCESSES=1` + explicit BLAS=1 in the fixture; tolerance (not hash); serial-only lane |
| Volatile API fields cause snapshot flakiness | Robust recursive scrubber; enumerated scrub-list (§4); start from the fresh no-network state |
| Tolerances too tight (cross-machine flakes) / too loose (misses drift) | Calibrate against 2–3 runs + the docker image; record torch/numpy versions; document per-fixture |
| Goldens drift silently when the spiral generator changes | Freeze the dataset to `.npz`; don't regenerate at test time |
| Suite slows the fast loop | Keep in `integration`+`slow`+`golden`; dedicated lane, not the unit default |
| Capturing *after* a refactor would bake in regressions | Capture on `origin/main` first (D-G3) |
| Resume-training determinism is unmet (`xfail`) | Gate on predict-after-load only; leave resume `xfail` |

## §9. Provenance

Scoped from a live, read-only cascor recon (2026-06-17, `origin/main` `88fcddb`) with `file:line` evidence; dup-guarded (no in-flight cascor golden/WS-6 work). OQ-13 resolved by code evidence + the refactor plan's prior lean. Implementation + tolerance calibration are a separate build phase (best run where `JuniperCascor1` + the docker image are available).
