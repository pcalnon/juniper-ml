# juniper-config-tools v0.1.0 — Release Notes (archived)

> Archived verbatim from the GitHub Release [`juniper-config-tools-v0.1.0`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-config-tools-v0.1.0) (pcalnon/juniper-ml), backfilled 2026-06-18
> per the release-notes archival convention (see [`notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md)).

---

First release of **juniper-config-tools** — stdlib-only env-var alias-with-deprecation helper for the Juniper ML platform.

## What's in 0.1.0

Single public function:

```python
juniper_config_tools.env_with_legacy_alias(
    new_name: str,
    legacy_name: str | None = None,
    default: str | None = None,
) -> str | None
```

Reads `new_name` from the environment; falls back to `legacy_name` with one `DeprecationWarning` (`stacklevel=2`) when only the legacy is set. See [`juniper-config-tools/CHANGELOG.md`](https://github.com/pcalnon/juniper-ml/blob/main/juniper-config-tools/CHANGELOG.md) for the full release notes.

## Why this package exists

`juniper-cascor-worker`'s no-Pydantic-at-runtime invariant (`tests/test_no_pydantic_at_runtime.py`, R2 exit-gate per juniper-ml#168) ruled out `juniper-observability` as the helper's home. juniper-config-tools is stdlib-only by policy (`os` + `warnings`; runtime `dependencies = []`).

## Shipped via

- Wave 0 scaffold: #320 (merged 2026-05-22)
- Migration plan: [`notes/JUNIPER_2026-05-22_JUNIPER-ML_CONFIG-TOOLS-PYPI-MIGRATION-PLAN.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-05-22_JUNIPER-ML_CONFIG-TOOLS-PYPI-MIGRATION-PLAN.md) (#318)

Next: Wave 2 — juniper-cascor-worker CFG-06 implementation consumes `juniper-config-tools>=0.1.0,<0.2.0`.
