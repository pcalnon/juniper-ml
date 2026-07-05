# Task — Add a shared `juniper-env-drift-check` console script to `juniper-ci-tools` (closing the plain-wheel client-floor-drift gap) with a juniper-ml dogfood test; then wire `juniper-canopy` to run it as a preflight

<!--
Custom-agent suite: a filled copy of prompts/agent_templates/task.md (execution-class).
Implements Phase A1 / §10.1 of notes/JUNIPER_2026-06-26_JUNIPER-ECOSYSTEM_TEST-SUITE-AUDIT-PLAN.md.
Grounded first-party against juniper-ml (HEAD = current main) + juniper-canopy (HEAD 31c7c995);
validated against prompts/agent_templates/RUBRIC.md by the prompt-validator subagent.
The downstream session WRITES CODE + opens PRs (it does not merge or publish).
-->

## Role

You are a senior engineer executing this task end-to-end across **`juniper-ml`** (primary) and **`juniper-canopy`** (follow-on), with the discipline to make the smallest correct change, verify it against each repo's real tests/lint, and land it as a reviewable pull request (never a direct merge).

## Resources

Ground every claim in these real, re-verified artifacts; **re-confirm each in-repo before relying on it** (HEADs move) — if a path/symbol/version/flag is absent, **stop and report rather than inventing**:

**The plan of record (what this implements):**

- `juniper-ml/notes/JUNIPER_2026-06-26_JUNIPER-ECOSYSTEM_TEST-SUITE-AUDIT-PLAN.md` — **§10.1** (the dependency-satisfaction check / durable guard), **§9.3 row `EFD`**, **§11 Phase A1 + Phase D "D-tool"**. This task builds §10.1's **shared, reusable** tool. The canopy-local MVP already shipped (next bullet), so **do not re-create it — generalize it**.

**Reference logic to GENERALIZE (do NOT duplicate — the canopy test stays):**

- `juniper-canopy/src/tests/unit/test_client_version_floors.py` (canopy HEAD `31c7c995`). It reads installed versions via `importlib.metadata.version(name)` (which **bypasses** the `conftest.py` session mocks), parses `pyproject.toml` floors with `tomllib` + `packaging` (`Requirement` / `SpecifierSet` / `canonicalize_name`), is parametrized over every floored `juniper-*` dep, and **skips-if-absent** (only *installed-but-stale* fails). Its module docstring documents the 2026-06-26 incident and explicitly names the editable-only gap below.

**The gap this closes (why a new tool, not the existing one):**

- `juniper-ml/util/editable_install_drift_check.py:148,153-154` inspects **only EDITABLE** installs (`*.dist-info/direct_url.json`, `dir_info.editable`). Canopy's drift was **plain wheels**, so that tool misses this class. The new checker must cover **plain wheels** (read `importlib.metadata` for **all** installed `juniper-*` distributions, not just editable ones).

**Host package — `juniper-ml/juniper-ci-tools/` (PyPI `juniper-ci-tools`, `_version.py` = `0.4.0`):**

- Console-script idiom: `juniper-ci-tools/pyproject.toml:37-41` `[project.scripts]`, e.g. `juniper-generate-dep-docs = "juniper_ci_tools.cli:main"`; module form via `juniper_ci_tools/__main__.py`.
- Tool idiom to mirror: `juniper_ci_tools/cli_lint_workflow_paths.py` — `_build_parser()` + `def main(argv=None) -> int` returning an exit code.
- ci-tools deps: `juniper-ci-tools/pyproject.toml:26-29` (`PyYAML`, `tomli` backport for <3.11) — **add `packaging`** (needed for `SpecifierSet`/`Requirement`). `tomllib` is stdlib (requires-python `>=3.11`).
- Conventions in ci-tools: ruff `pyproject.toml:67-76` (py311; select `E/F/W/B/I/N`; ignore `N803/N806`); line-length **512**; standardized file headers.

**Test gates:**

- ci-tools CI gate: `juniper-ml/.github/workflows/ci-ci-tools.yml:65-70` runs `python -m pytest --cov=juniper_ci_tools --cov-report=term-missing --cov-fail-under=85`. The new module's own unit tests live in `juniper-ci-tools/tests/` and must keep aggregate ≥**85%** (aim **≥90% per-file**, this being the coverage audit).
- Dogfood test home (the chosen scope): **`juniper-ml/tests/test_env_drift_check.py`** (new), mirroring `juniper-ml/tests/test_ci_tools_drift.py` (`unittest.TestCase`; invokes the tool; asserts exit codes + behavior). `util/` and `juniper-ci-tools/` are outside juniper-ml's flake8/pre-commit scope, so this unittest is the integration gate.
- Consumer-pin guards (keep green): `juniper-ml/tests/test_pyproject_extras.py:52` hardcodes juniper-ml's `juniper-ci-tools>=0.1.0` [tools] pin (**unchanged by this work**). **Critically**, `juniper-ml/tests/test_ci_tools_drift.py::test_juniper_ml_own_workflows_pin_current_version` is **ungated (runs every PR)** and asserts the current ci-tools `_version` is **below** the upper bound pinned in juniper-ml's OWN workflows — which today pin **`juniper-ci-tools>=0.1.0,<0.5.0`** in `.github/workflows/ci.yml:459`, `docs-full-check.yml:226`, and `lockfile-update.yml:48`. So a minor bump to `0.5.0` **requires widening those three pins in the same PR** (directive 3e). The sibling `test_consumer_repos_pin_current_version` covers cloned consumer repos (canopy) and is skip-on-absent.

**Publish + consumer (the follow-on, sequenced — NOT part of PR1):**

- Publish: `juniper-ml/.github/workflows/publish-ci-tools.yml` triggers on tag `juniper-ci-tools-v*`. Per the release convention, **cut a GitHub Release** (notes templated from `notes/templates/TEMPLATE_RELEASE_NOTES.md` → archived `notes/releases/RELEASE_NOTES_ci-tools_v<ver>.md`), never a bare tag push. **Publishing/deploy approval is the owner's.**
- Canopy already installs ci-tools in CI — `juniper-canopy/.github/workflows/ci.yml:542-546` (dependency-docs job) and `:679-682` (docs job), both pinned **`juniper-ci-tools>=0.2.0,<0.5.0`**. Canopy does NOT list ci-tools in `pyproject.toml`/`requirements`. The `<0.5.0` upper bound must be widened to admit the new version.

**Conventions (current canonical):** line-length **512**; deliverable docs → `notes/`; Python `>=3.11` (ci-tools) / `>=3.12` (juniper-ml); one-PR-per-work-unit; no-merge-without-PR; worktree isolation under `/home/pcalnon/Development/python/Juniper/worktrees/`; thread-handoff at **95–99%** of compaction. Canopy test env: `JuniperCanopy1`.

**Known red herring (do not chase):** the canopy discovery bundle's `test_status.failing_count: 188` is the documented **stale-`.pytest_cache` artifact** (`juniper-ml/notes/JUNIPER_2026-06-26_JUNIPER-CANOPY_DEBUG-PROMPT-ANALYSIS.md` §5 — a 6-week-old `lastfailed`); canopy collects cleanly. Ignore it.

## Primary Objective

Generalize canopy's proven client-floor-drift guard into a reusable **`juniper-env-drift-check`** console script in `juniper-ci-tools` that detects when an active environment's installed `juniper-*` distributions (**plain wheels included**) violate a target repo's `pyproject.toml` floors (and, with `--check-lock`, its `requirements.lock` pins) — the durable, ecosystem-reusable form of plan §10.1. Land it as a **self-contained juniper-ml PR** with the tool's own unit tests (≥85% gate) and a juniper-ml dogfood test; then, **after the owner publishes ci-tools**, wire canopy to run it as a preflight.

## Assigned Tasks / Directives

1. Run `gh pr list` (juniper-ml) first — dup-guard (concurrent sessions are common). Work in a worktree under `/home/pcalnon/Development/python/Juniper/worktrees/` on a `feature/...` branch off current `main`.
2. Re-confirm every anchor in `## Resources` in-repo before relying on it; **stop and report** on any missing path/symbol/version/flag rather than guessing.
3. **PR1 (juniper-ml — primary, self-contained):**
   - a. Add the checker to `juniper-ci-tools/juniper_ci_tools/`: a core module + a `cli_env_drift_check.py` (`_build_parser()` + `def main(argv=None) -> int`), mirroring `cli_lint_workflow_paths.py`. Generalize `test_client_version_floors.py`'s logic: parse floors from a target repo's `pyproject.toml` (`--repo-root`), read installed versions via `importlib.metadata` (**plain wheels included — explicitly not limited to editable installs**), compare; `--check-lock` additionally asserts `requirements.lock` pins satisfy those floors; exit **0** (ok) / **1** (drift) / **2** (usage); human-readable + `--json` output; **list every drifted and every ok dist (no silent truncation)**.
   - b. Register `juniper-env-drift-check = "juniper_ci_tools.cli_env_drift_check:main"` in `pyproject.toml [project.scripts]`; add `packaging>=<floor>` to `[project].dependencies`.
   - c. Add the tool's unit tests in `juniper-ci-tools/tests/` (synthetic `pyproject.toml`/`requirements.lock` fixtures + a stubbed `importlib.metadata`; cover ok / drift / absent-skips / lock-mismatch / usage-error) reaching aggregate ≥85% (aim ≥90% per-file for the new module).
   - d. Add `juniper-ml/tests/test_env_drift_check.py` (dogfood; mirror `test_ci_tools_drift.py`) invoking the console script / `python -m` form end-to-end against a synthetic fixture; assert exit codes + drift detection + JSON shape.
   - e. Bump `juniper_ci_tools/_version.py` per the ci-tools release convention — an additive console script is a **minor** bump (`0.4.0` → `0.5.0`). Because juniper-ml's own three workflows pin `juniper-ci-tools>=0.1.0,<0.5.0`, **in the SAME PR widen those upper bounds** (`.github/workflows/ci.yml:459`, `docs-full-check.yml:226`, `lockfile-update.yml:48` → e.g. `<0.6.0`) so `tests/test_ci_tools_drift.py::test_juniper_ml_own_workflows_pin_current_version` stays green. Update the package description + README to list the new script. Do **not** change juniper-ml's unbounded `>=0.1.0` [tools] pin (`tests/test_pyproject_extras.py:52`). (A patch bump would avoid the pin edits but is semantically wrong for a new console script — prefer the minor + pin-widen.)
4. **Follow-on (sequence explicitly; do NOT bundle into PR1):**
   - The owner cuts a `juniper-ci-tools-v<new>` GitHub Release (templated notes → `notes/releases/`) to publish — **owner-gated**.
   - **PR2 (canopy):** widen the `juniper-ci-tools` pin past `<0.5.0` to admit the published version; add a preflight step (after the `requirements.lock` install, before the unit tests) invoking `juniper-env-drift-check --repo-root . --check-lock`; add a local `make check-env` target + a short doc note. (CI installs from the lock, so the CI step mainly guards **lock-below-floor** drift; the local/runtime target — run in `JuniperCanopy1` — is the guard for the original incident class.)

## Key Deliverables & Requirements

- **PR1** landed on juniper-ml (PR, never a direct merge): the `juniper-env-drift-check` tool + `[project.scripts]` entry + `packaging` dep + ci-tools unit tests + `juniper-ml/tests/test_env_drift_check.py` + `_version.py` bump + README/description update.
- **Acceptance criteria (measurable):**
  - `cd juniper-ml/juniper-ci-tools && python -m pytest --cov=juniper_ci_tools --cov-report=term-missing --cov-fail-under=85` **passes** with the new module included (aim ≥90% per-file).
  - `cd juniper-ml && python3 -m unittest -v tests/test_env_drift_check.py` **passes**; `python3 -m unittest tests/test_ci_tools_drift.py tests/test_pyproject_extras.py` **still pass**.
  - `juniper-env-drift-check --help` exits 0; against a synthetic repo whose installed `juniper-*` is **below** a `pyproject` floor it exits **1** and names the offending dist (`==<installed>` vs the floor); against a satisfying env it exits **0**; a **plain-wheel** install is treated identically to an editable one (the gap is closed — assert this explicitly).
  - `--check-lock` exits **1** when a `requirements.lock` pin is below a `pyproject` floor, **0** when consistent.
  - **PR2 acceptance (follow-on):** canopy CI green with the preflight; `juniper-env-drift-check --repo-root . --check-lock` exits 0 in canopy CI (lock satisfies floors); the canopy pin admits the published version.

## Constraints

- Do NOT delete, disable, or weaken any test to make a suite pass — a CRITICAL and ABSOLUTE requirement. Do NOT duplicate `test_client_version_floors.py`; **generalize** its logic (the canopy test remains).
- Never invent APIs / paths / flags / versions; if the grounding does not contain it, stop and report.
- **PR1 must be self-contained and verifiable WITHOUT publishing.** Do not make canopy depend on an unpublished ci-tools; keep PR1 (juniper-ml) and PR2 (canopy) separate (one-PR-per-work-unit). The `<0.5.0` upper bound exists in **two** places: juniper-ml's OWN three workflows (`ci.yml:459`, `docs-full-check.yml:226`, `lockfile-update.yml:48`) — widened in **PR1** (directive 3e), because `test_ci_tools_drift.py` runs there ungated — and canopy's CI (`>=0.2.0,<0.5.0`) — widened in **PR2**, after publish. Keep `test_ci_tools_drift.py` + `test_pyproject_extras.py` green in PR1.
- The owner approves all merges **and** the ci-tools publish/deploy — do not self-merge or self-publish.

## Finalize / Validation

- Verify with the repo's **actual** commands above (the ci-tools pytest+cov gate, the two juniper-ml unittests, and the CLI exit-code checks) — the acceptance evidence is real command output, not a promise; not a generic "run the tests".
- Re-confirm each cited `file:line`/symbol in-task; **stop and report** on any missing anchor.
- **Cross-validate the checker's drift logic** (the high-stakes core — a false "ok" would re-admit the exact 2026-06-26 incident this guards) with a sub-agent or a second adversarial test pass before finalizing (RUBRIC R3.3).
- Recover / abort: no merge without a PR; `gh pr list` dup-guard; worktree cleanup only after merge; if the acceptance criteria cannot be met without weakening a test or inventing a fact, **stop and report what is blocking**.
