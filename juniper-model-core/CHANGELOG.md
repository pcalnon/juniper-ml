# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-14

### Added

- **Initial scaffold (WS-3).** `juniper-model-core` defines the shared model-contract template
  for the Juniper ML platform, designed against two real implementers (Cascade-Correlation +
  the Δt-native LMU) per the ratified decision ledger D1–D10
  (`notes/JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md`):
  - `TrainableModel` / `GrowableModel` ABCs (`interfaces.py`) — numpy at the boundary, no
    classification assumptions in the generic surface (RK-6); `GrowableModel` kept minimal /
    provisional until RCC is the second implementer (RK-4).
  - The `TrainingEvent` vocabulary (`events.py`) and the `describe_topology()` schema
    (`topology.py`) — the model-agnostic monitoring and rendering seams.
  - The `ModelSerializer` strategy interface (`serialization.py`).
  - Inspectable validation free functions (`validation.py`): `validate_metrics`,
    `validate_topology`, `legal_event_order` — the shared behavior the ABCs deliberately
    exclude (C1).
  - The `TrainingLifecycleBase` seam (`lifecycle.py`) — declared in WS-3; body deferred to
    WS-2 (co-designed with juniper-service-core).
  - The reusable conformance kit (`conformance/`) — `TrainableModelConformance` /
    `GrowableModelConformance` plus a reference regression model that serves as the kit's own
    RK-6 canary.
- **Dependency-free contract.** `import juniper_model_core` pulls no third-party runtime
  dependency (numpy is type-annotation-only); numpy/pytest live in the `[conformance]` extra.

### Notes

- Not yet published to PyPI. Per the publish-first rule, juniper-ml's `[all]`/`[tools]` extras
  will pin `juniper-model-core` only after a TestPyPI soak (a follow-up PR).
