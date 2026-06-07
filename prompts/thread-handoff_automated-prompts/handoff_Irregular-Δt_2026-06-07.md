# Irregular-Δt / WS-1 data foundation

## Evaluation

The CI-rescue track is fully closed (5 PRs merged, main green). The real forward work is the irregular-Δt / WS-1 data foundation — now unblocked because Paul ratified OQ-7 as gating and filed juniper-data#168. My Δt note is the ready-to-use spec (contract §6, windowing+property test

§7, Approach C §8 with verified reference code). That's the natural continuation; OQ-4 (model pick) and the deferred TestPyPI 2-step hardening are parallel/trigger-conditioned.

Continue the juniper-recurse irregular-Δt / WS-1 data-foundation work. The CI-rescue
that consumed the prior thread is done (juniper-ml main is green); this is the
substantive forward track.

## Completed so far (prior thread)

- Δt analysis shipped (juniper-ml #378, MERGED): notes/JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md
  (the spec — §6 dt/observed_mask contract, §7 windowing-leakage + Hypothesis property test,
  §8 Approach C), util/ad-hoc/verify_delta_t_reference_code.py (verified: e_reg≈0.035,
  grid-invariant; windowing invariants I1–I5), and a §1.3.4 amendment to
  notes/JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md (solver-free LMU variable-Δt).
- Paul ratified 2026-06-06: OQ-7 (irregular-Δt) is GATING, not deferred. WS-1 filed as
  juniper-data#168 (folds in OQ-5 datasets + gating OQ-7). OQ-4 (model pick) still open (#377 doc).
- CI fully restored+hardened (juniper-ml #379–#384 merged; main green); TestPyPI no-fallback
  policy generalized (memory: testpypi-publish-verify-noextraindex-policy).

## Remaining work — WS-1 (juniper-data#168, the gating critical path; spec = the Δt note above)

1. Add the additive 3-D NPZ contract (optional keys dt/t/observed_mask≠padding_mask/target_dt/
   seq_lengths; X.ndim dispatch keeps 2-D byte-identical) to juniper-data + juniper-data-client. (§6)
2. Add a shared temporal_split + per-ticker windowing with leakage invariants (no train-target≥cut;
   no cross-ticker window). Lift the reference impl + property test from §6.3/§7.4.
3. Add the equities SEQUENCE variant: window the flat 2-D equities NPZ into 3-D, derive dt from the
   existing date_* (YYYYMMDD) arrays (weekend/holiday gaps = the irregular Δt). New variant, not in-place.
4. Add synthetic time-series regression generators per OQ-5: multi-sine, Mackey-Glass, AR(p).
   (Deferred to WS-4, after OQ-4: implement Approach C / LMU variable-Δt from §8 + the verify script.)

## Key context

- The equities NPZ today is FLAT 2-D (one row/day), NOT sequenced; dates live in date_* beside
  features (juniper-data .../equities/generator.py:439-443). Windowing→3-D first, then dt.
- WS-1 is additive/low-risk and does NOT depend on the OQ-4 model pick; the decisions it needs
  (OQ-5 datasets, OQ-7 gating) are settled.
- OQ numbering on origin/main is consistent (OQ-7=irregular-Δt model; OQ-6=NPZ-3D refactor); a
  concurrent session had an uncommitted renumber [OQ-7]→[OQ-6] — if it lands, re-assert OQ-7.

## Parallel / deferred (not WS-1)

- OQ-4 model-pick (RCC+group-units vs ESN/NEAT) — #377 doc.
- 2-step TestPyPI hardening for deps-needing publish workflows (ci-tools/observability/publish.yml)
  — trigger: next release (can't CI-dry-run).
- Housekeeping: discard the stray 1-line uncommitted edit to
  notes/JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md (not ours, ```→```bash); prune ~10
  merged session branches; do NOT reuse the prior session worktree.

## Start state / verify

- Work primarily in juniper-data (#168), referencing the juniper-ml Δt note for the spec. Use a
  FRESH worktree off main per notes/WORKTREE_SETUP_PROCEDURE.md.
- Verify: gh pr view 378 = MERGED; gh issue view 168 --repo pcalnon/juniper-data;
  gh run list --workflow ci.yml --branch main -L1 (green).

---
