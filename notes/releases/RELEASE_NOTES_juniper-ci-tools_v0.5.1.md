# juniper-ci-tools v0.5.1 Release Notes

**Release Date:** 2026-06-29
**Version:** 0.5.1
**Package:** juniper-ci-tools (subdirectory of juniper-ml)
**Release Type:** PATCH

---

## Overview

Restores the **`juniper-env-drift-check`** console-script entry point that was inadvertently dropped from `[project.scripts]` in 0.5.0, and adds a regression guard so a console-script entry point cannot be silently dropped again.

> **Status:** STABLE — patch; no API or behavior change to the tool itself.

---

## Bug Fixes

### `juniper-env-drift-check` console script missing from 0.5.0

**Problem:** `juniper-ci-tools==0.5.0` shipped the `env_drift_check` module but **not** the `juniper-env-drift-check` console script (`juniper-env-drift-check` → exit 127). The checker was reachable in 0.5.0 only via `python -m juniper_ci_tools.cli_env_drift_check`.

**Root cause:** PR #579 added `juniper-env-drift-check` to `[project.scripts]`; PR #580 (the coverage-gap mapper), merged after #579, **replaced** the `[project.scripts]` block instead of appending — a semantic (non-textual) merge conflict that dropped the `juniper-env-drift-check` line and reverted the package description. It shipped green because the only entry-point exercise was the build smoke, while the always-on pytest suite asserted the *module* (via `python -m`), never the *console-script registration*.

**Solution:** Re-added `juniper-env-drift-check = "juniper_ci_tools.cli_env_drift_check:main"` to `[project.scripts]` and restored the description suffix.

**Files:** `juniper-ci-tools/pyproject.toml`, `juniper-ci-tools/juniper_ci_tools/_version.py`

---

## Improvements

### Regression guard (the durable fix)

New `tests/test_env_drift_check_drift.py` (modeled on `tests/test_coverage_gap_mapper_drift.py`), wired into the always-on pytest job (`.github/workflows/ci.yml`), asserts:

- `juniper-env-drift-check` is registered in `[project.scripts]` → `juniper_ci_tools.cli_env_drift_check:main`;
- both module halves ship; version/pin coherence; and
- **a class guard** — *every* `juniper_ci_tools/cli*.py` module has a corresponding `[project.scripts]` entry, so a future concurrent-merge clobber that drops *any* tool's console script fails loudly in CI rather than silently at publish.

---

## Upgrade Notes

```bash
pip install --upgrade juniper-ci-tools==0.5.1
juniper-env-drift-check --help    # now resolves (was exit 127 in 0.5.0)
```

`0.5.0` remains on PyPI (immutable) but lacks the console script — use `0.5.1`. Consumers that require the console script may pin `juniper-ci-tools>=0.5.1,<0.6.0`.

---

## Known Issues

- `0.5.0` (immutable) lacks the `juniper-env-drift-check` console script; superseded by `0.5.1`.
- The `util/env_floor_drift_check.py` ↔ ci-tools `juniper-env-drift-check` consolidation remains a tracked follow-up (juniper-ml#588).

---

## Version History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 0.5.1 | 2026-06-29 | Restore `juniper-env-drift-check` entry point + entry-point regression guard |
| 0.5.0 | 2026-06-29 | Add `juniper-env-drift-check` (entry point dropped by a concurrent merge) |
| 0.4.0 | (prior) | AGENTS.md header-schema lint console script |

---

## Links

- Original tool: #579 · Entry-point clobber: #580 · Consolidation follow-up: #588
- Test-suite audit plan §10.1: [../JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md](../JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md)

---
