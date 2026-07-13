# juniper-cascor-protocol v0.1.0 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.1.0]` section (with package-summary context carried
> from the `[0.1.0a0]` section) plus the git tag date; it is **not** a verbatim copy of a GitHub Release body.
> Central-archive convention:
> [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.3.
> **No GitHub Release exists for tag `juniper-cascor-protocol-v0.1.0`** (published tag-only — audit F-1);
> this file is the durable in-repo record.

---

# juniper-cascor-protocol v0.1.0 Release Notes

**Release Date:** 2026-04-30
**Version:** 0.1.0
**Release Type:** Stable promotion (from `0.1.0a0`; first stable)
**Repository:** pcalnon/juniper-cascor (path `juniper-cascor-protocol/`)
**Git tag:** `juniper-cascor-protocol-v0.1.0` (tag-only; no GitHub Release — audit F-1)
**PyPI:** <https://pypi.org/project/juniper-cascor-protocol/0.1.0/>

---

## Overview

First stable promotion of the shared CasCor wire-protocol package (METRICS-MON R2.2.3 / seed-05). It
promotes the `0.1.0a0` alpha to stable now that the first consumer (the juniper-cascor server) has shipped
without surfacing a wire-format regression. There are **no public-API changes** vs `0.1.0a0` — same surface,
same behavior; only the version string and the trove classifier change.

---

## Changed

- **First stable promotion** (METRICS-MON R2.2.3 / seed-05). Promoted from pre-release to stable now that the
  first consumer (juniper-cascor server,
  [pcalnon/juniper-cascor#159](https://github.com/pcalnon/juniper-cascor/pull/159)) has shipped without
  surfacing a wire-format regression. **No public-API changes** vs `0.1.0a0` — same surface, same behavior;
  only the version string and trove classifier change.
- Trove classifier moved from `Development Status :: 3 - Alpha` to `Development Status :: 4 - Beta` to
  reflect the 0.1.x stability commitment.
- Consumers should pin `juniper-cascor-protocol>=0.1.0` going forward. Existing pins of `>=0.1.0a0` continue
  to resolve to the latest published version, which is now `0.1.0`.

## Notes

- The previous alpha (`0.1.0a0`) remains on PyPI for reproducibility of historical builds. Yanking is
  intentionally avoided; consumers can downgrade in a hotfix scenario by pinning explicitly.

---

## Package summary (carried from `0.1.0a0`, unchanged in this release)

The package provides the canonical Pydantic v2 envelope schemas for the ten typed `/ws/training` and
`/ws/control` frames, `validate_envelope(frame)` with an R1.1 cardinality bound on unknown types, and a
numpy-only `worker` subpackage (`WorkerMessageType` + `BinaryFrame` codec) that lets the cascor-worker adopt
the wire contract without a runtime Pydantic dependency (the top-level namespace re-exports only worker
symbols; Pydantic loads only on an explicit `juniper_cascor_protocol.envelope` import). Wire-compat snapshot
tests pin every envelope byte-for-byte against the pre-migration cascor server shapes.

---

## Links

- Package CHANGELOG (`[0.1.0]` section): <https://github.com/pcalnon/juniper-cascor/blob/main/juniper-cascor-protocol/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-cascor-protocol/0.1.0/>
- Git tag: <https://github.com/pcalnon/juniper-cascor/releases/tag/juniper-cascor-protocol-v0.1.0>
