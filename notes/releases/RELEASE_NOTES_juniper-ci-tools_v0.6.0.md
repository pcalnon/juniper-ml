# juniper-ci-tools v0.6.0 Release Notes

**Release Date:** 2026-06-30
**Version:** 0.6.0
**Package:** juniper-ci-tools (subdirectory of juniper-ml)
**Release Type:** MINOR
**Codename:** Per-file coverage gate (C-0 enabler)

---

## Overview

Adds an **opt-in enforcing mode** to the `juniper-coverage-gap-map` console script so the per-file coverage-gap mapper can *block* a build, not just report. This is work-unit **C-0** of the per-file coverage rollout — the enabler the rest of the rollout (C-1+) turns on per unit. The advisory exit-0-always behavior remains the **default**; no other console script is affected.

> **Status:** STABLE — additive minor; the default (advisory) behavior is unchanged, enforcing is strictly opt-in via `--enforce`.

---

## Release Summary

- **Release type:** MINOR (additive feature — a new opt-in flag set)
- **Primary focus:** NEW FEATURE (blocking per-file coverage gate)
- **Breaking changes:** NO — advisory remains the default; existing callers are unaffected
- **Priority summary:** Ships the C-0 enabler; no unit CI is switched to the blocking gate yet (C-1+)

---

## What's New

### Enforcing mode for `juniper-coverage-gap-map` (work-unit C-0)

The mapper gains an opt-in blocking gate. When `--enforce` is set, the CLI exits **1** if, after `--omit` exclusions, **any** source file's **statement** coverage is below `--fail-under-file` (default `90`) **or** **any** sub-module's **pooled** (statement-weighted) coverage is below `--fail-under-submodule` (default `95`); it exits **0** when clean, listing every offending file and sub-module (no silent truncation). Without `--enforce`, the output and exit code are unchanged (advisory — exit 0 always).

```bash
# Advisory (default) — unchanged: report only, exit 0 always.
juniper-coverage-gap-map --coverage-json coverage.json

# Enforcing (opt-in): exit 1 on a per-file statement gap or a sub-module pooled gap.
juniper-coverage-gap-map --coverage-json coverage.json --enforce \
    --fail-under-file 90 --fail-under-submodule 95 --omit '*/__main__.py'
```

**Changes:**

- New flags: `--enforce`, `--fail-under-file` (default 90), `--fail-under-submodule` (default 95), and repeatable `--omit GLOB`.
- New exit code **1** — returned **only** under `--enforce` when a file or sub-module is under its floor. The advisory default never returns 1.
- `--json` output gains an `"enforcement"` object (thresholds, bases, the offending files/sub-modules, and `passed`) **only** when `--enforce` is set; the default JSON shape is unchanged.

### The two enforcing bases (deliberately different from the advisory display)

The gate uses different bases than the advisory report so it is apples-to-apples across units regardless of each unit's branch setting (the basis choices ratified in `notes/JUNIPER_ECOSYSTEM_PER_FILE_COVERAGE_ROLLOUT_SCOPING_2026-06-30.md` §0):

- **Per-file basis = statement** coverage (`covered_statements / num_statements`), surfaced as the new `FileCoverage.statement_percent` property — **not** the branch-inclusive `percent_covered` the advisory report shows (a repo running `branch = true` reports a branch-inclusive percent).
- **Sub-module basis = pooled** (statement-weighted `Σcovered / Σstatements`) via `SubmoduleCoverage.below_pooled_bar` — **not** the mean-of-files average the advisory report shows. The two diverge for small files and can flip a sub-module's outcome.

### Exclusions (`--omit`)

`--omit <glob>` (repeatable `fnmatch`) is applied to the parsed `coverage.json` **before** aggregation and gating, so the report and the gate both honor it — the tool is the single source of truth for what counts (it does not rely on coverage's own `[report] omit`). Zero-statement files (re-export `__init__.py`) already score 100 %, so `--omit` is for thin `__main__.py` / CLI shims and the like, per the rollout's excluded-files policy (scoping doc §2).

---

## Library API additions

- `FileCoverage.statement_percent` (property) — the enforcing per-file basis; also surfaced in the `--json` per-file objects.
- `SubmoduleCoverage.below_pooled_bar(bar)` — the enforcing sub-module predicate (companion to the advisory `below_bar`).
- `CoverageReport.files_below_statement_threshold(threshold)` / `CoverageReport.submodules_below_pooled_bar(bar)` — enforcing query methods (statement / pooled bases), alongside the unchanged advisory `files_below_threshold` / `submodules_below_bar`.
- `parse_coverage_json` / `load_coverage_json` / `run_coverage` gained an `omit=` parameter (forwarded from the CLI's `--omit`).

---

## Improvements

### Test coverage

| Component | Before | After | Change |
| --------- | ------ | ----- | ------ |
| `coverage_gap_mapper.py` | 100% | 100% | — |
| `cli_coverage_gap_mapper.py` | 100% | 100% | — |

New enforcing-mode tests in `juniper-ci-tools/tests/test_coverage_gap_mapper.py`: clean→exit 0, per-file statement gap→exit 1 (naming the file), sub-module pooled gap→exit 1, `--omit` exclusion, advisory-default→exit 0, and the two basis distinctions — a file with **branch < 90 but statement ≥ 90 PASSES**, a sub-module with **mean ≥ 95 but pooled < 95 FAILS**. The full suite's `--cov-fail-under=85` gate stays green (total 96.19 %).

The juniper-ml dogfood gate `tests/test_coverage_gap_mapper_drift.py` gained a structural check (the `--enforce`/`--fail-under-*`/`--omit` flags are wired) plus an end-to-end synthetic-`coverage.json` invocation of the shipped entry point (exit 1 on a gap, 0 clean, 0 on `--help`, 0 for the advisory default).

---

## Test Results

### Test Suite (`juniper-ci-tools`)

| Metric | Result |
| ------ | ------ |
| **Tests passed** | 199 |
| **Tests failed** | 0 |
| **Coverage** | 96.19% overall (both changed modules 100%) |

---

## Upgrade Notes

This is a backward-compatible release. No migration is required — the default (advisory) behavior is unchanged; enforcing is strictly opt-in.

```bash
pip install --upgrade juniper-ci-tools==0.6.0
juniper-coverage-gap-map --coverage-json coverage.json --enforce   # opt-in gate
```

Consumers that need the enforcing mode may pin `juniper-ci-tools>=0.6.0,<0.7.0`. juniper-ml's own workflow pins (`ci.yml`, `lockfile-update.yml`, `docs-full-check.yml`) were widened from `<0.6.0` to `<0.7.0` in the same PR; the meta-package `[tools]` extra pin (`juniper-ci-tools>=0.1.0`) is unchanged.

### Rollback Instructions

```bash
pip install --force-reinstall juniper-ci-tools==0.5.1
```

---

## Known Issues

- **No unit CI is on the blocking gate yet.** C-0 ships the enforcing *mode* only; wiring `--enforce` as a blocking step into each unit's CI is work-unit C-1+ of the rollout (`notes/JUNIPER_ECOSYSTEM_PER_FILE_COVERAGE_ROLLOUT_SCOPING_2026-06-30.md` §5).
- **Waiver file (`coverage-waivers.yaml`) not yet implemented.** The audit plan's structured-waiver mechanism (§7.4) is deferred; the current excluded-files lever is `--omit`.

---

## Version History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 0.6.0 | 2026-06-30 | Opt-in `--enforce` mode (statement per-file / pooled sub-module bases) + `--omit`; C-0 enabler |
| 0.5.1 | 2026-06-29 | Restore `juniper-env-drift-check` entry point + entry-point regression guard |
| 0.5.0 | 2026-06-28 | Add the advisory per-file coverage-gap mapper |

---

## Links

- Per-file coverage rollout scoping (C-0): [../JUNIPER_ECOSYSTEM_PER_FILE_COVERAGE_ROLLOUT_SCOPING_2026-06-30.md](../JUNIPER_ECOSYSTEM_PER_FILE_COVERAGE_ROLLOUT_SCOPING_2026-06-30.md)
- Test-suite audit plan (§6 contract, §7 enforcement design): [../JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md](../JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md)
- Package changelog: [../../juniper-ci-tools/CHANGELOG.md](../../juniper-ci-tools/CHANGELOG.md)
- Previous release: [RELEASE_NOTES_juniper-ci-tools_v0.5.1.md](RELEASE_NOTES_juniper-ci-tools_v0.5.1.md)

---
