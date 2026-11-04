# juniper-config-tools v0.1.1 – PATCH RELEASE

**Release Date:** 2026-11-04
**Release Type:** Patch (packaging)
**Priority:** Low: upgrade at leisure; it changes what a type checker sees, not runtime behaviour
**Package Affected:** juniper-config-tools

---

This is a packaging patch of `juniper-config-tools` v0.1.1. The wheel now ships the PEP 561 `py.typed` marker, which 0.1.0 lacked. There is no API or behaviour change, and consumers pinned `>=0.1.0,<0.2.0` (juniper-ml's `[tools]`) receive it as-is.

---

## Changes in v0.1.1

### Fixed

- **The wheel ships `py.typed`** (juniper-ml#1237, `APD-SVCCORE-008` / `APD-OBS-002`). The published 0.1.0 wheel holds `__init__.py`, `__main__.py`, `_env_aliases.py`, `_version.py` and its dist-info, but no `py.typed` (checked against PyPI on 2026-11-04). Without the marker, mypy and pyright treat the package as untyped, so `env_with_legacy_alias` is `Any` in every consumer although its source is annotated. The marker is now declared package data, and the classifiers add `Typing :: Typed`. #1237 fixed all six juniper-ml sub-packages on 2026-08-22, and this is config-tools' first release since.

### Changed

- Repository-internal configuration only, with no shipped code changed: strict pytest markers and config, dash/playwright plugin autoload blocked (juniper-ml#490), Ruff lint (juniper-ml#508), and the notes links renamed under the 2026-07-04 naming convention.

---

## Upgrade

```bash
pip install -U "juniper-config-tools>=0.1.1,<0.2.0"
```

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-ml/blob/juniper-config-tools-v0.1.1/juniper-config-tools/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-config-tools_v0.1.1.md`
