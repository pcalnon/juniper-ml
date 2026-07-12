# juniper-doc-tools v0.1.1 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.1.1]` section plus the git tag date; it is **not** a
> verbatim copy of a GitHub Release body. Central-archive convention:
> [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.3.
> **No GitHub Release exists for tag `juniper-doc-tools-v0.1.1`** (published tag-only — audit F-1); this file
> is the durable in-repo record.

---

# juniper-doc-tools v0.1.1 Release Notes

**Release Date:** 2026-05-19
**Version:** 0.1.1
**Release Type:** PATCH
**Repository:** pcalnon/juniper-ml (path `juniper-doc-tools/`)
**Git tag:** `juniper-doc-tools-v0.1.1` (tag-only; no GitHub Release — audit F-1)
**PyPI:** <https://pypi.org/project/juniper-doc-tools/0.1.1/>

---

## Overview

A patch release for the shared markdown link validator (`juniper-check-doc-links`). It corrects the CLI
summary line so the "files with errors" count matches the inline-script behavior the CLI replaced, and
exposes that count programmatically. No behavioral change beyond the summary line: the per-error output and
the exit code are unchanged.

---

## Fixed

- **CLI summary line `FOUND N broken link(s) in M file(s)`** — the `M` count now matches the inline-script
  behavior it replaced. The 0.1.0 CLI estimated `M` by string-deduping error prefixes, which double-counted
  any markdown file that had *both* a broken-anchor error (prefixed with the absolute `Path`) and a
  broken-link error (prefixed with the path relative to `repo_root`). The count is now tracked at iteration
  time in `validate_directory` and exposed on `ValidationResult` as the new `files_with_errors` attribute.
- Programmatic consumers gain access to the file count via `ValidationResult.files_with_errors` (additive;
  existing fields unchanged).

---

## Links

- Package CHANGELOG (`[0.1.1]` section): <https://github.com/pcalnon/juniper-ml/blob/main/juniper-doc-tools/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-doc-tools/0.1.1/>
- Git tag: <https://github.com/pcalnon/juniper-ml/releases/tag/juniper-doc-tools-v0.1.1>
