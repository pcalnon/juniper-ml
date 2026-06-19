# juniper-ml v0.5.0 — servers + tools extras — Release Notes (archived)

> Archived verbatim from the GitHub Release [`v0.5.0`](https://github.com/pcalnon/juniper-ml/releases/tag/v0.5.0) (pcalnon/juniper-ml), backfilled 2026-06-18
> per the release-notes archival convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).

---


### Added

- **TestPyPI extras-resolution verification step** in
  `.github/workflows/publish.yml`. After the bare-package install
  verification, the workflow now also installs `juniper-ml[clients]`
  from TestPyPI and imports both client modules. This exercises the
  full `[project.optional-dependencies]` resolution path against the
  published metadata, so a broken extras declaration (mistyped name,
  missing roll-up into `[all]`, dangling self-reference) fails the
  publish rather than landing on PyPI silently. `[clients]` is chosen
  because it is the lightest extra (no torch) and still walks the full
  resolver path.

- **`notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md`**
  -- runbook for the v0.5.0 release. Documents preconditions, the
  TestPyPI / PyPI flow, the new extras-resolution verification step,
  and the rollback options (yank vs. patch release) for a meta-package
  whose extras surface has expanded.

- **`tests/test_agents_md_version_drift.py`** -- new lint test pinning
  `AGENTS.md`'s `**Version**:` header to `pyproject.toml`'s
  `[project].version`. juniper-ml#295 bumped `pyproject.toml` from
  0.4.1 to 0.5.0 but left `AGENTS.md` at 0.4.0 for ~6 days (drift
  caught by ad-hoc grep + fixed in juniper-ml#304); this lint makes
  the failure class impossible to ship. Wired into the main CI tests
  job; intentionally portable (auto-locates the repo root) so the
  same module can be dropped into any Juniper repo's `tests/` to
  catch the same drift class there.

- **`notes/META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md`** -- source
  requirements doc for the meta-package extras surface. Specifies the
  declared groups, `[all]` aggregate semantics, version-bump policy,
  documentation-consistency surfaces, regression-coverage expectations,
  and the install-size advisory. Written in the source-doc format that
  the next snapshot consolidation pass can ingest; `JR-ML-*` IDs will
  be assigned at that pass and referenced retroactively in PRs #293,
  #295, #299.

- **Install-size advisory for `juniper-ml[all]`** in `docs/QUICK_START.md`.
  Calls out that `[all]` transitively pulls a multi-GB dependency tree
  (notably `torch` via `juniper-cascor-worker` and `juniper-cascor`,
  approx. 2 GB on a fresh env) and recommends narrower extras
  (`[clients]`, `[tools]`, `[doc-tools]`) when the worker / server
  distributions are not needed.

- **`tests/test_pyproject_extras.py`** -- new lint test pinning the
  `[project.optional-dependencies]` surface so accidental edits (drop,
  mistype, fail to roll up into `[all]`) fail loudly in CI. Schema-strict:
  any future change to extras must update the lint contract in the same
  PR. Wired into the main CI tests job; runs alongside
  `test_doc_tools_drift.py` and `test_workflow_script_paths.py`.

- **`[servers]` optional dependency group** for the three Juniper service
  packages on PyPI. `pip install juniper-ml[servers]` now installs
  `juniper-canopy>=0.3.0`, `juniper-cascor>=0.3.17`, and
  `juniper-data>=0.6.0` in a single step. Previously the meta-package
  only aggregated the client/worker libraries; the server distributions
  had to be installed by name.

- **`[tools]` optional dependency group** that aggregates the three
  PyPI-published Juniper tool packages: `juniper-ci-tools>=0.1.0`
  (dependency-documentation generator, Wave 1 of the dep-docs migration
  plan), `juniper-doc-tools>=0.1.0,<0.2.0` (markdown link validator),
  and `juniper-observability>=0.2.0` (shared Prometheus collector
  helpers + structured logging + Starlette middleware). The
  pre-existing `[doc-tools]` extra is retained for back-compat with
  callers that already installed via that name.

- **`[all]` extra expanded** to cover the new `[servers]` and `[tools]`
  groups in addition to `[clients]` and `[worker]`. A single
  `pip install juniper-ml[all]` now pulls in every published Juniper
  package: 3 servers, 2 clients, 1 worker, and 3 tools.

### Changed

- **Pre-tag docs polish for the 0.5.0 release.** Refreshes the three
  Ecosystem Compatibility tables (`README.md`, `docs/REFERENCE.md`,
  `docs/DOCUMENTATION_OVERVIEW.md`) to enumerate every package the
  meta-package now pins -- canopy / cascor / data / data-client /
  cascor-client / cascor-worker / ci-tools / doc-tools / observability
  -- with their actual pyproject pins (the previous tables only listed
  3-5 packages and used stale `0.4.x` headers). Adds `[servers]`,
  `[tools]`, and `[doc-tools]` editable-install commands to `AGENTS.md`
  and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, plus an explicit
  multi-GB callout on `[all]`.

- **Version bumped to 0.5.0** (semver minor) to mark the new optional
  dependency surface. No removals or breaking changes -- existing
  `[clients]`, `[worker]`, `[doc-tools]`, and `[all]` install commands
  continue to work; `[all]` is now a strict superset.
- **`juniper-observability` is now aggregated under `juniper-ml[tools]`
  and `juniper-ml[all]`.** Until 0.4.1 it was published from this
  repository as a sibling package that had to be installed directly.
  Documentation in `README.md`, `docs/QUICK_START.md`,
  `docs/REFERENCE.md`, and `docs/DOCUMENTATION_OVERVIEW.md` updated to
  reflect this. Independent versioning and the
  `juniper-observability-v*` tag pipeline are unchanged.

- **§5 drift-detection guard rails** for the `juniper-doc-tools` PyPI
  migration (plan
  [`notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md)
  §5.1 + §5.2). Closes the open follow-ups from Wave 4.
  - `tests/test_doc_tools_drift.py` — consumer-version-pin lint. Reads
    the current `juniper-doc-tools` version from
    `juniper-doc-tools/pyproject.toml`, then walks each cloned consumer
    repo's `ci.yml` and asserts the `juniper-doc-tools>=X,<Y` pin still
    admits current. Soft-warns when a pin lags by more than 2 minors;
    hard-fails when the upper bound excludes current. Also lints
    juniper-ml's own `ci.yml` + `docs-full-check.yml` for the same pin
    rule (this case runs even per-PR; the cross-repo assertion auto-
    skips when siblings aren't on disk). Local runs skip the cross-repo
    assertion by default to avoid stale-working-tree false positives;
    set `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` to override.
  - `.github/workflows/docs-full-check.yml` — two new steps in the
    weekly cross-repo workflow:
    - "Lint doc-tools pins across consumer repos" invokes the new test.
    - "Downstream-consumer integration check" installs `juniper-doc-tools`,
      runs `juniper-check-doc-links` against each cloned consumer repo's
      docs with the canonical Juniper exclude set, and aggregates per-
      repo results. Per-repo failures are warned; the step fails only
      when `>=DOWNSTREAM_FAIL_THRESHOLD` consumers regress in the same
      week (default 5 of 6 = catastrophic juniper-doc-tools regression).

### Removed

- **`util/check_doc_links.py`** (the inline v0.7.0 validator) — Wave 2 + Wave 4 of the doc-link migration plan. Replaced by the PyPI-published `juniper-doc-tools` package; install with `pip install juniper-doc-tools` and invoke via `juniper-check-doc-links`. The CI docs jobs (`ci.yml`, `docs-full-check.yml`) now install the package and run the console script. Inline copies in all 7 sibling repos (canopy / cascor / data / cascor-client / cascor-worker / data-client / ml) are deleted in the same wave.
- `scripts/check_doc_links.py` (symlink to the old `util/` copy), `util/check_doc_links.bash` (local-path-only convenience wrapper), and `tests/test_check_doc_links.py` (now covered by `juniper-doc-tools/tests/`).

### Added

- `util/check_doc_links.py` bumped to **v0.7.0**: classifies ecosystem-root paths (`../../CLAUDE.md`, `../../AGENTS.md`, `../../notes/`, `../../prompts/`, `../../resources/`, `../../backups/`, `../../logs/`, `../../worktrees/`, `../../juniper-legacy/`, `../../Juniper{,1}.code-workspace`) the same way as cross-repo `../juniper-X/` links: subject to the `--cross-repo` policy (skip/warn/check). Restores parity with the more permissive behavior repo docs were already relying on without silently accepting truly broken outside-repo links. 5 new regression tests in `tests/test_check_doc_links.py` cover the ecosystem-root paths and a guard against misclassifying intra-repo links that happen to traverse a `notes/`-named directory.
- `tests/test_workflow_script_paths.py` — new lint test that walks `.github/workflows/*.yml`, extracts every script path referenced via `python|bash <path>` / `python3 -m unittest ... <path.py>` / `$VAR <path>` patterns, and asserts each path exists in the repo. Cross-repo paths (`juniper-X/...`) are skipped as runtime-resolved. Catches the failure class that broke 3 juniper-X CIs on 2026-05-18 when a script was renamed without updating the workflow. Designed to be copy-and-paste portable into the other Juniper repos' `tests/` directories.
- **`juniper-doc-tools` subpackage scaffold** — Wave 0 of the doc-link
  validator PyPI migration ([plan](notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md)).
  New `juniper-doc-tools/` subdirectory packages the v0.7.0 markdown link
  validator as a PyPI distribution with a stable CLI surface
  (`juniper-check-doc-links` + `python -m juniper_doc_tools`), a small
  library API (`validate_directory`, `validate_file`, `ValidationResult`),
  and the new `--strict-repo-boundary` opt-out flag from §3.4.1 / §8.4.
  Tests use pytest (§8.1); 30 tests cover the v0.7.0 behavior, the new
  flag, and CLI argparse end-to-end. `.github/workflows/ci-doc-tools.yml`
  runs the test matrix (3.12/3.13/3.14) + build + wheel smoke-test on
  PRs touching `juniper-doc-tools/**`. `.github/workflows/publish-doc-tools.yml`
  publishes to TestPyPI → PyPI on tags matching `juniper-doc-tools-v*`,
  mirroring the existing `publish-observability.yml`.
- **`juniper-doc-tools` 0.1.0 published to PyPI** — Wave 1 of the
  migration plan. Tag `juniper-doc-tools-v0.1.0` cut from `main` on
  2026-05-19; OIDC trusted publish went through TestPyPI → PyPI without
  intervention (TestPyPI verified install + console-script + module-form
  on a fresh runner). `pip install juniper-doc-tools` now works from
  any environment. New `[doc-tools]` extra in this `pyproject.toml`
  pins the consumer to `>=0.1.0,<0.2.0` so a future breaking minor
  bump does not auto-adopt before Wave 2 swaps each repo's CI over.
  Next: Wave 2 (per-repo CI swap) starts in juniper-ml itself, then
  fans out to the 7 other ecosystem repos.
