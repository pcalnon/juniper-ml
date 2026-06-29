# juniper-ci-tools v0.5.0 Release Notes

**Release Date:** 2026-06-29
**Version:** 0.5.0
**Package:** juniper-ci-tools (subdirectory of juniper-ml)
**Release Type:** MINOR

---

## Overview

Adds **`juniper-env-drift-check`**, a shared, pip-distributable console script that asserts an active environment's installed `juniper-*` distributions satisfy a target repo's `pyproject.toml` version floors (and, with `--check-lock`, its `requirements.lock` pins). It generalizes canopy's proven client-floor-drift guard into a reusable, CI-wireable tool — the durable form of §10.1 of the ecosystem test-suite audit plan.

> **Status:** STABLE — additive, backward-compatible.

---

## Release Summary

- **Release type:** MINOR (additive console script; no breaking changes)
- **Primary focus:** new shared tooling — environment dependency-floor drift detection
- **Breaking changes:** NO
- **Priority summary:** ships the plain-wheel-aware "green tests / dead app" guard the canopy runtime-breakage post-mortem called for (unlike the editable-only `util/editable_install_drift_check.py`)

---

## What's New

### `juniper-env-drift-check` (test-suite audit §10.1; shipped in juniper-ml#579)

A console script (with a `python -m juniper_ci_tools` module-form sibling pattern) that:

- Parses `juniper-*` floors from a target repo's `pyproject.toml` (`--repo-root`).
- Reads **installed** versions via `importlib.metadata` — so **plain wheels are checked identically to editable installs**, closing the exact 2026-06-26 client-floor-drift class that `util/editable_install_drift_check.py` (editable-only) misses.
- Classifies each distribution `OK` / `BELOW_FLOOR` / `MISSING`; with `--check-lock`, additionally validates that `requirements.lock` pins satisfy the floors.
- Exit codes: `0` (ok) / `1` (drift) / `2` (usage); human-readable and `--json` output; lists every drifted and ok dist (no silent truncation).

**Changes:**

- New `juniper_ci_tools/env_drift_check.py` (core) + `juniper_ci_tools/cli_env_drift_check.py` (CLI).
- New `[project.scripts]` entry `juniper-env-drift-check`.
- New runtime dependency `packaging>=22.0`.

---

## Improvements

### Adversarial hardening (a real false-OK caught pre-release)

A second adversarial review of the drift logic found — and fixed — a **false-OK**: the installed-version dedup originally kept the *highest* version, masking a coexisting below-floor copy (a leftover `dist-info` from a failed upgrade, or an editable+wheel double-install). It now keeps the **lowest** version (fail-safe — `importlib` loads first-on-path). Also: unparseable versions are treated as drift rather than crashing, malformed `dependencies`/`optional-dependencies` are tolerated, and the lock regex tolerates `[extras]`. Each fix carries a regression test.

### Test coverage

| Component | Coverage | Gate | Status |
| --------- | -------- | ---- | ------ |
| `env_drift_check.py` | 100% | 85% | Exceeded |
| `cli_env_drift_check.py` | 98% | 85% | Exceeded |
| `juniper_ci_tools` (aggregate) | 95% | 85% | Exceeded |

---

## Test Results

| Metric | Result |
| ------ | ------ |
| Tests passed | 155 |
| Tests failed | 0 |
| Coverage | 95% aggregate (gate 85%) |

Plus a juniper-ml dogfood test (`tests/test_env_drift_check.py`, 8 tests) that drives the installed console script end-to-end as a subprocess. All publishing-relevant CI green: ci-tools Test (Python 3.11–3.14), Build distribution (entry-point smoke), Pre-commit.

---

## Upgrade Notes

Backward-compatible MINOR release. No migration required.

```bash
pip install --upgrade juniper-ci-tools==0.5.0
juniper-env-drift-check --help

# Check the active env against a repo's floors (and its lockfile):
juniper-env-drift-check --repo-root /path/to/repo --check-lock
```

Consumers pinning `juniper-ci-tools` with an upper bound `<0.5.0` must widen it to adopt 0.5.0. juniper-ml's own three workflows were widened to `<0.6.0` in #579; the meta-package `[tools]` extra pin (`>=0.1.0`) already admits it.

---

## Known Issues

- **Tool overlap (consolidation deferred):** `util/env_floor_drift_check.py` (juniper-ml#574, a juniper-ml-local/manual floor checker from a separate plan) overlaps in intent. `juniper-env-drift-check` is the pip-distributable, CI-wireable form with `--check-lock`. Both currently coexist without file/test collision; consolidation is a tracked follow-up.
- None functional.

---

## What's Next

- **PR2 (juniper-canopy):** widen canopy's `juniper-ci-tools>=0.2.0,<0.5.0` pin to admit 0.5.0 and add a `juniper-env-drift-check --repo-root . --check-lock` CI preflight + a `make check-env` target.
- Consolidate `util/env_floor_drift_check.py` with this tool.

---

## Version History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 0.5.0 | 2026-06-29 | Add `juniper-env-drift-check` shared env floor-drift guard |
| 0.4.0 | (prior) | AGENTS.md header-schema lint console script |

---

## Links

- Test-suite audit plan §10.1: [../JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md](../JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md)
- Shipped in: juniper-ml#579 · Notes archival: this PR

---
