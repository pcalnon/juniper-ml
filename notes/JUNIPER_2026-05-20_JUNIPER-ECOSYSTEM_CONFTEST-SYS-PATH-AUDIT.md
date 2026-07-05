# Conftest sys.path Hack — Audit

**Date**: 2026-05-20
**Author**: Paul Calnon (with Claude Opus 4.7)
**Trigger**: CLN-CC-13 ecosystem-wide sweep ([v7 roadmap](./JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md)). Production-code `sys.path.append` hacks were cleaned up across cascor + canopy (PRs cascor [#279](https://github.com/pcalnon/juniper-cascor/pull/279)/[#280](https://github.com/pcalnon/juniper-cascor/pull/280), canopy [#297](https://github.com/pcalnon/juniper-canopy/pull/297)). This doc audits whether the remaining test-infrastructure `sys.path.insert` calls in cascor + canopy conftests are still necessary or can be removed in a follow-up pass.

---

## 1. Inventory

### juniper-cascor

| Location | Lines | Pattern |
|----------|-------|---------|
| `src/tests/conftest.py:95-96` | 2 | `sys.path.insert(0, …)` (src/) + `sys.path.insert(1, …)` (src/tests/) |
| `src/tests/integration/api/conftest.py:9` | 1 | `sys.path.insert(0, _SRC_DIR)` (guarded by an `if` block) |
| `src/tests/unit/test_*.py` and `src/tests/integration/test_*.py` (~15 files) | 1 each | Per-test `sys.path.append(<3 dirs up>)` adding the project root |

### juniper-canopy

| Location | Lines | Pattern |
|----------|-------|---------|
| `conftest.py:7-10` (project root) | 4 | `sys.path.insert(0, str(src_path))` (guarded by `not in sys.path`) |
| `src/tests/conftest.py:34-50` | ~17 | `sys.path.insert(0, str(src_dir))` + `PYTHONPATH` set + verbose `print` instrumentation. Bundled with stub `juniper_data_client` injection. |
| `src/tests/integration/test_*.py` and `src/tests/regression/test_*.py` (~15 files) | 1 each | Per-test `sys.path.insert(0, str(src_dir))` |

### juniper-data, juniper-cascor-worker (out of scope, called out for completeness)

- `juniper-data/juniper_data/tests/fixtures/generate_golden_datasets.py:33` — cross-repo `sys.path.insert(0, str(JUNIPER_CASCOR_SRC))`. Legitimate cross-repo fixture; can't be replaced by editable install.
- `juniper-cascor-worker/juniper_cascor_worker/cli.py:63` — `sys.path.insert(0, args.cascor_path)` from a user-supplied CLI argument. Intentional runtime feature, not a hack.

---

## 2. What each defense protects against

### 2.1 cascor `src/tests/conftest.py:95-96`

The inline comment is explicit:

> Use insert(0, ...) to ensure local src/ takes precedence over any editable installs of legacy JuniperCascor that may shadow the api package.

**Threat model**: a developer activates the wrong conda env (e.g., `JuniperCascor-DEPRECATED`) where a stale `pip install -e .` from a different worktree points at an outdated `cascade_correlation` package. Without the `sys.path.insert(0, …)`, that stale install resolves first and tests run against the wrong code path.

**Active threat?** Yes:

```text
$ conda env list | grep -i Juniper
JuniperCanopy-DEPRECATED     /opt/miniforge3/envs/JuniperCanopy-DEPRECATED
JuniperCanopy1               /opt/miniforge3/envs/JuniperCanopy1
JuniperCascor-DEPRECATED     /opt/miniforge3/envs/JuniperCascor-DEPRECATED
JuniperCascor1           *   /opt/miniforge3/envs/JuniperCascor1
JuniperCassandra             /opt/miniforge3/envs/JuniperCassandra
JuniperData                  /opt/miniforge3/envs/JuniperData
JuniperPython-DEPRECATED     /opt/miniforge3/envs/JuniperPython-DEPRECATED
```

The legacy envs are renamed (`-DEPRECATED`) but still on disk — `conda activate JuniperCascor-DEPRECATED` still works. The defense still applies.

The defense is also useful in multi-worktree development: only one worktree at a time can hold the `pip install -e .` slot in a given env, and the conftest's `sys.path.insert(0, src)` ensures the CURRENT worktree's tests use the CURRENT worktree's source regardless of which worktree holds the editable install.

**Verdict**: keep.

### 2.2 cascor per-test `sys.path.append(<3 dirs up>)`

Adds the project root (3 dirs up from a `src/tests/unit/test_*.py` file) to the end of `sys.path`. With where=[".", "src"] in `pyproject.toml`, the project root contains no top-level Python packages — `cascade_correlation`, `candidate_unit`, etc. live under `src/`, not at the root. So this `append` adds a directory that has nothing useful in it.

**Threat model**: none observed. Cargo-culted from before the `where=["src"]` packaging change.

**Verdict**: redundant. Safe to remove in a follow-up.

### 2.3 canopy `conftest.py:7-10` (project root)

Adds `src/` to `sys.path[0]` if not already present.

**Threat model**: same as cascor 2.1 — protect against env contamination from the deprecated `JuniperCanopy-DEPRECATED` env, plus enable test discovery before any editable install runs.

**Active threat?** Yes — `JuniperCanopy-DEPRECATED` still on disk.

**Verdict**: keep.

### 2.4 canopy `src/tests/conftest.py:34-50`

The `sys.path` manipulation is **bundled** with other essential test setup that can't be moved:

- `JUNIPER_CANOPY_DEMO_MODE=1`, `JUNIPER_DATA_URL`, `JUNIPER_CANOPY_RATE_LIMIT_ENABLED=false` (must be set before any module-level imports of `main.py`)
- Migration shims for legacy `CASCOR_*` env vars → new `JUNIPER_CANOPY_*` names
- Stub `juniper_data_client` injection into `sys.modules` for CI envs where the data client isn't installed

The `sys.path` lines are 3 of ~17 setup lines. Removing them in isolation gains very little; the conftest needs to load early either way.

**Verdict**: keep. The instrumented `print` statements at lines 40-43, 48-50 could be downgraded to a debug-only diagnostic block but that's cosmetic.

### 2.5 canopy per-test `sys.path.insert(0, str(src_dir))`

Same pattern as cascor 2.2 — redundant once `conftest.py` has run, since conftest already put `src/` at `sys.path[0]`.

**Threat model**: none, except in the edge case where a test file is imported standalone (without pytest collecting `conftest.py` first). That's not a real workflow.

**Verdict**: redundant. Safe to remove in a follow-up.

---

## 3. Recommendations

| Action | Repo | Risk | Estimated effort |
|--------|------|------|------------------|
| **Keep** root + src/tests conftests in cascor + canopy | both | n/a | n/a — no change |
| **Remove** per-test `sys.path.append`/`insert` (Tier 3) | cascor (~15 files), canopy (~15 files) | Low — conftests already cover what they were doing | S–M (1 PR per repo, mostly mechanical sed-style edits + full test-suite verification) |
| **Audit annual** of the `-DEPRECATED` envs | n/a | Low | If/when Paul removes `JuniperCascor-DEPRECATED` and `JuniperCanopy-DEPRECATED` from disk, revisit §2.1 and §2.3 — the shadowing threat is then gone and the `insert(0, src)` in the root conftests becomes purely defensive against an unsupported workflow. |

---

## 4. Trigger conditions for the deferred per-test sweep

- The cascor PR for Tier 3 can land any time; risk is independent of unrelated work.
- The canopy PR for Tier 3 should wait until Paul's local main work (`be838e9` "fixing environment issues and normalizing settings across repos", 2026-05-18) is either pushed or rebased on, so the per-test cleanup doesn't conflict with concurrent test-infrastructure changes.
- Suggested branch names:
  - `chore/cln-cc-13-tier3-cascor-per-test-syspath-cleanup-YYYY-MM-DD`
  - `chore/cln-cc-13-tier3-canopy-per-test-syspath-cleanup-YYYY-MM-DD`

## 5. Verification protocol if the Tier 3 sweep is attempted

For each repo, in a fresh worktree off `origin/main`:

1. `pip install -e ".[all]"` in the active env (JuniperCascor1 / JuniperCanopy1).
2. Identify per-test `sys.path` calls: `grep -rn "sys.path" src/tests/ --include="*.py" | grep -v conftest`.
3. For each match: confirm the directory it adds is already covered by `sys.path` after the relevant conftest runs (typical assertion: the dir matches `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` or shallower — already on `sys.path[0]`).
4. Delete the redundant lines + any now-unused `import os` / `import sys` at the top of the test file. Run `pre-commit run --files <changed>` to confirm linting passes (flake8 will not catch unused imports if the module is reused for other things, so a manual scan is needed).
5. `pytest src/tests/ -q --timeout=120` → should match baseline run from main.

---

## 6. Out of scope (separate concerns)

- **`juniper-data/juniper_data/tests/fixtures/generate_golden_datasets.py:33`** — cross-repo `JUNIPER_CASCOR_SRC` injection for a fixture that depends on cascor source. The fixture exists because golden-dataset generation reuses cascor's data generators directly; replacing it with an installed-package call would require either publishing cascor's generators as a separate package or extracting them into juniper-data. Tracking this separately as a roadmap-style item rather than rolling it into the sweep.
- **`juniper-cascor-worker/juniper_cascor_worker/cli.py:63`** — `sys.path.insert(0, args.cascor_path)` from a user-supplied CLI argument. This is an intentional runtime feature, not a hack — the worker connects to a cascor source tree the user names at the command line. No action needed.
