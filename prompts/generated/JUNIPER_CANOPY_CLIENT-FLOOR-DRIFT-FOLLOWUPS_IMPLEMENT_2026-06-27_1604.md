# Implement Plan — juniper-canopy client-floor-drift follow-ups (#3 demo-launcher env name · #4 requirements comment drift · #5 setuptools/torch lock pin)

<!--
Generated prompt — Juniper custom-agent suite. Template: implement-plan (execution-class).
Grounded against juniper-canopy @ main 31c7c99 (discovery bundle 2026-06-27, head_sha
31c7c995eca5bf1f9df161a49f41bfe412e1a61b, all probes ok). Plan = the "Secondary findings" +
"Prevention" sections of notes/CANOPY_RUNTIME_CLIENT_FLOOR_DRIFT_ROOT_CAUSE_2026-06-26.md.
Paste this as the opening message of a fresh session.
-->

## Role

You are an experienced principal software engineer implementing three **already-documented, ratified follow-ups** from the canopy runtime client-floor-drift root-cause writeup. The regression itself (env drift below `pyproject.toml` client floors) is already fixed and guarded (juniper-canopy #402/#403, merged). Your job is to faithfully realize the *documented* follow-ups — not to re-diagnose the regression, and not to expand beyond what the plan lists.

## Resources

**Target repo / state (re-confirm before trusting):**

- Repo: `/home/pcalnon/Development/python/Juniper/juniper-canopy/`, branch `main`, HEAD `31c7c99`, version `0.5.0`. Live conda env: **`JuniperCanopy1`** (Python 3.13); never `JuniperCanopy-DEPRECATED`.
- **The plan (source of truth):** `notes/CANOPY_RUNTIME_CLIENT_FLOOR_DRIFT_ROOT_CAUSE_2026-06-26.md` — implement its **"Secondary findings" items #3, #4, #5** and the matching **"Prevention"** bullets. (Items #1/#2 are already done or are explicit non-issues; item #6 and the "Considered and declined" hardening are **out of scope** — see Constraints.)
- Test commands (real, from this repo): the **CI unit lane** `python -m pytest -m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/` is the marker-filtered, locally-achievable bar. A bare `make test` also runs live-service integration tests that need a running cascor/data, so it is **not** a clean local green bar — do not gate on it. Lint via `pre-commit run --all-files` (canopy's plain `ruff check` is a deliberate no-op — `[tool.ruff.lint]` ships an empty `select`; the real ruff gate is the pre-commit `ruff-async-audit` hook). Run everything in `JuniperCanopy1` (e.g. `conda run -n JuniperCanopy1 …`).

**Item #3 — stale `./demo` launcher conda env name (grep-verified anchors):**

- `util/juniper_canopy-demo.bash:104` → `conda activate JuniperCanopy` — the env `JuniperCanopy` **does not exist** (only `JuniperCanopy1` and `JuniperCanopy-DEPRECATED`), so on-host `./demo` breaks at activation. Supporting stale references in the same script: `:78` (`conda env list | grep -q "JuniperCanopy"`), `:79`, `:94`, `:101` (user-facing messages naming the unversioned env).
- Repo-root `demo` is a symlink → `util/juniper_canopy-demo.bash`.
- Canonical convention: `AGENTS.md:27` states the env name is **versioned** ("rebuilds increment the suffix and rename the old env `*-DEPRECATED`") and instructs discovery via `conda env list | grep JuniperCanopy`. A hardcoded literal (`JuniperCanopy1`) will re-drift on the next rebuild (`JuniperCanopy2`).
- A good in-repo pattern to emulate: `util/setup_environment.bash` already parameterizes the env via a `${ENV_NAME}` variable rather than hardcoding (no drift there).
- Hardcoded port `8050` (canonical canopy port): `util/juniper_canopy-demo.bash:209,210,211,212` (banner URLs) and `:225` (`uvicorn … --port 8050`).
- Same-class drift **outside** the launcher, to **assess (not blind-replace)**: `conf/conda_environment_ci.yaml:45` (`name: JuniperCanopy` — may be intentionally unversioned for an ephemeral CI build), `docs/USER_MANUAL.md` and `src/tests/integration/test_setup.py` (a printed `conda activate JuniperCanopy` instruction).
- Existing launcher test: `src/tests/regression/test_demo_script_error_handling.py` covers dependency-check error handling only; **no test asserts the launcher's env name** — that guard is absent.

**Item #4 — misleading commented client pins (grep-verified anchors):**

- `conf/requirements_ci.txt:81-85` carries **commented OLD-version** juniper pins: `# juniper-canopy==0.5.0`, `# juniper-cascor-client==0.3.0`, `# juniper-cascor-protocol==0.1.0`, `# juniper-data-client==0.4.0`, `# juniper-observability==0.2.0` (a frozen `pip freeze` block; the live flexible constraints are lower in the file, e.g. the PyTorch CPU index at `:154`).
- Root `requirements.txt` is a **symlink** to `conf/requirements.txt` (asserted by integrity test RQ-4); confirm whether `conf/requirements.txt` carries its own commented OLD pins and treat both files.
- `requirements.lock` is the only authoritative pin source.
- **Invariants that must survive any edit** — `src/tests/regression/test_requirements_integrity.py` (RQ-1…RQ-7): the PyTorch CPU `--extra-index-url` line must remain (RQ-3/RQ-7), CI requirements must still include `torch` (RQ-6), root `requirements.txt` must stay a symlink to `conf/requirements.txt` (RQ-4), no duplicate packages (RQ-5). Pre-commit hook `require-requirements-lock` (`.pre-commit-config.yaml:316-325`) must keep passing.

**Item #5 — `setuptools` vs `torch` lock conflict (grep-verified anchors):**

- `requirements.lock:135` → `setuptools==82.0.1`; `torch` is **absent** from `requirements.lock` (verified: no `^torch` line). `torch` lives only in the `pyproject.toml` `demo` extra (`pyproject.toml:178` → `torch>=2.0.0`) and is installed via the PyTorch CPU index (`conf/requirements_ci.txt:154`).
- Mechanism: the lockfile is compiled **without** the `demo` extra — `.github/workflows/lockfile-update.yml:87-92` runs `uv pip compile pyproject.toml --extra juniper-data --extra juniper-cascor --extra observability --upgrade -o requirements.lock` (no `--extra demo`), and the "Lockfile Freshness" gate `.github/workflows/ci.yml:604-609` uses the *same* extras with `--constraint requirements.lock`. So torch's `setuptools<82` constraint never enters the lock, and `pip install -r requirements.lock` emits a benign-but-alarming conflict line. `import torch` nonetheless succeeds with setuptools 82.0.1 (non-breaking).

## Primary Objective

Implement the canopy-local follow-ups #3, #4, and #5 from the root-cause plan so each is syntactically, logically, idiomatically, and architecturally correct and matches the plan's intent: `./demo` activates the real live env again, the requirements files no longer mislead a reinstaller, and the setuptools/torch lock conflict is resolved or deliberately recorded — each guarded against silent recurrence and verified against this repo's own tests.

## Assigned Tasks / Directives

1. **Re-ground first.** In `JuniperCanopy1`, re-confirm every `file:line` anchor in *Resources* against the live repo (the discovery bundle is a snapshot). If any anchor no longer resolves, **stop and report** rather than inventing a replacement. Run `gh pr list` against `pcalnon/juniper-canopy` as a duplicate-work guard before starting.
2. **Item #3 — fix the `./demo` launcher env name (its own work-unit/PR).** Make `util/juniper_canopy-demo.bash` resolve the **live, versioned, non-`-DEPRECATED`** `JuniperCanopy*` env dynamically (honoring `AGENTS.md:27`'s versioned-env convention; emulate the `${ENV_NAME}` parameterization in `util/setup_environment.bash`) rather than hardcoding a suffix that will re-drift — with a clear error if none (or more than one non-deprecated) is found. Update the supporting messages (`:78/:79/:94/:101`) for consistency. **Add the missing regression guard** (extend `src/tests/regression/test_demo_script_error_handling.py` or add a sibling test) asserting the launcher targets a real/live env and contains no bare-`JuniperCanopy` activation — it must run in the CI unit lane (`src/tests/regression/` is in scope). For each *outside-launcher* reference (`conf/conda_environment_ci.yaml:45`, `docs/USER_MANUAL.md`, `src/tests/integration/test_setup.py`), **assess and justify** whether to update it (the launcher is the definite bug; the CI yaml name may be intentionally ephemeral). The plan also notes the hardcoded port `8050` (`:209-212`, `:225`); addressing it is **optional** and must not block or expand the env-name fix — leave it untouched unless a trivial, co-located change.
3. **Item #4 — de-mislead the requirements files (its own work-unit/PR).** Make the stale commented OLD-version juniper pins in `conf/requirements_ci.txt:81-85` (and `conf/requirements.txt` if it carries them) non-misleading — your choice of removing the dead frozen block or annotating it to point at `requirements.lock` as the authoritative source; pick the smaller correct change and justify it. **Preserve every `test_requirements_integrity.py` invariant** (RQ-1…RQ-7: CPU index line, torch in CI reqs, root symlink, no duplicates) and keep the `require-requirements-lock` pre-commit hook green.
4. **Item #5 — resolve or record the setuptools/torch lock conflict (its own work-unit/PR or a doc decision).** Evaluate the options and choose one **with written justification**: (a) compile the lock *with* `--extra demo` in **both** `lockfile-update.yml:87-92` and the freshness check `ci.yml:604-609` (keeping them identical) so torch's `setuptools<82` constraint enters the lock — note this pulls torch into the lock; (b) add a narrow `setuptools<82` constraint; or (c) keep the current behavior and **record it as a known-benign conflict** in the root-cause doc. If you change the lock, regenerate it per this repo's mechanism (compile to a temp path then move; respect the constraint-mode freshness gate) and confirm the gate still passes. This item is owner-relevant — present your recommendation.
5. **Write status back to the plan.** In `notes/CANOPY_RUNTIME_CLIENT_FLOOR_DRIFT_ROOT_CAUSE_2026-06-26.md`, mark items #3/#4/#5 (and the matching "Prevention" bullets) with their implemented/decided status and the PR number(s).

## Key Deliverables & Requirements

- **#3:** `./demo` launches against the live `JuniperCanopy1` env (demonstrate: `./demo` reaches uvicorn bind in `JuniperCanopy1` with no "env not found"); a new regression test that **fails on a bare-`JuniperCanopy` activation and passes on the dynamic resolution**, runnable via the CI unit lane; a justified disposition for each outside-launcher reference. Landed as a PR.
- **#4:** No reinstaller-misleading OLD-version pins remain; `python -m pytest src/tests/regression/test_requirements_integrity.py` and `pre-commit run --all-files` both pass; the root `requirements.txt` symlink is intact. Landed as a PR.
- **#5:** A written decision (implemented change **or** a recorded "known-benign" note in the plan doc); if the lock changed, the "Lockfile Freshness" check command (`ci.yml:604-609`) passes locally. Landed as a PR (or a doc-only PR for option (c)).
- The plan document updated with per-item status + PR numbers.
- Each work-unit is its own PR with passing tests + clean lint; **no test weakened**.

## Constraints

- **Scope is juniper-canopy only**, items #3/#4/#5. Explicitly **out of scope** (do not implement here): item #6 (an ecosystem plain-wheel drift checker — that belongs in juniper-ml as a separate effort), the **declined** `src/demo_mode.py` graceful-degradation hardening (an owner design choice, not a default), the test-pollution **non-issue** #2 (`test_generate_route_rejects_non_spiral_when_juniper_data_unavailable` — its expectation is correct; do NOT "fix" it), and the sibling-env (`JuniperCascor1`) drift (operational, not a canopy code change).
- Do not invent paths, env names, flags, versions, or ports — every reference must resolve in the grounding bundle or the live repo; **STOP and report** if an expected anchor is missing rather than fabricating it.
- Do not weaken, skip, or delete any existing test to make a suite pass.
- **One PR per work-unit** (#3, #4, #5 are separate); never merge (the owner merges and approves any deploy/PyPI gate); create work in a worktree under `/home/pcalnon/Development/python/Juniper/worktrees/`; worktree cleanup only after the owner confirms the merge.

## Finalize / Validation

- Paste passing evidence per item: the relevant test target(s) green — the CI unit lane (`pytest -m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/`), `src/tests/regression/test_requirements_integrity.py`, and the new launcher guard — plus `pre-commit run --all-files` clean, and for #5 the freshness-check command (`ci.yml:604-609`) if the lock changed. Do not gate on a bare `make test` (it runs live-service integration tests).
- Re-confirm each cited `file:line` in-task before relying on it; for any change you could not verify against a live run, say so explicitly rather than claiming success.
- Verify per the standing rules: `gh pr list` dup-guard before starting; one PR per work-unit; no merge without a PR; worktree cleanup only on merge.
