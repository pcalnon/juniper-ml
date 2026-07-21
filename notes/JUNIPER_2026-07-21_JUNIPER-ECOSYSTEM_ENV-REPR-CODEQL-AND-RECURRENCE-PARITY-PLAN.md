# Env-Repr Redaction + CodeQL Subaction Alignment + Recurrence Auth Parity — Execution Plan

**Project**: Juniper
**Repository**: pcalnon/juniper-ml (plan document); execution spans 8 ecosystem repos
**Author**: Paul Calnon
**Date**: 2026-07-21
**Status**: APPROVED as-is (owner, 2026-07-21) — implementation in flight in the authoring session

---

## 1. Context

The SEC-F01 auth-posture arc completed 2026-07-20 (ten PRs: per-service `enforce_auth_posture` adoption, the `JUNIPER_<SVC>_REQUIRE_AUTH` flag tail, and the juniper-deploy fail-closed stack posture). Three follow-ons remain, ordered by the owner:

1. **pytest env-repr key leak** — juniper test suites build `env = os.environ.copy()` and pass it to `subprocess.run`; an observed failure paste rendered the full env dict with live secrets (`ANTHROPIC_API_KEY`, `ALPHA_VANTAGE_TOKEN` — alphabetically early keys, visible even in truncated reprs). Close the class at the source so no failure output can render secret values.
2. **CodeQL subaction mismatch** (3rd recurrence of the known class) — `github/codeql-action` subaction pins split within a repo, producing `Loaded a configuration file for version '4.37.0', but running version '4.37.1'`. Red on juniper-cascor and juniper-data `main` as of 2026-07-20.
3. **Recurrence stack parity** — provision juniper-recurrence's inbound API-key secret in juniper-deploy and set `JUNIPER_RECURRENCE_REQUIRE_AUTH=true`, matching the data/cascor/canopy fail-closed posture, without breaking in-stack consumers.

All factual anchors below were re-probed at current mains on 2026-07-20/21 by this session plus two read-only discovery agents. Per house doctrine: re-verify anchors at HEAD before editing; a drifted anchor is a stop-and-re-ground signal.

## 2. Verified facts

### 2.1 Env-repr leak — mechanism and scope

- **Mechanism (confirmed)**: pytest's `saferepr`/`reprlib` rendering of the `env` frame-local under `--showlocals`/`-l`-style runs. It is the only renderer in the failure path that alphabetically sorts and truncates dict reprs — matching the observed fingerprint exactly. The configured CI paths (`python3 -m unittest` in juniper-ml; `pytest tests/ -v --tb=short` in juniper-deploy) never print frame locals. There is no mock-assert-on-env, no `msg=` embedding of the env mapping, and no bash `set -x` surface anywhere in either repo.
- **Scope (exactly two repos have the genuine pattern)**:
  - juniper-ml `tests/`: 16 sites across 8 files — `test_wake_the_claude.py` (multiple sites + the `_run_script` helpers near lines 52 and 848), `test_juniper_plant_all.py` (3), `test_reap_pytest_orphans.py`, `test_worktree_sweep_scripts.py`, `test_install_agents.py:53`, `test_prompt_discovery.py:49-51`, `test_coverage_gap_mapper_drift.py:315`, `test_env_drift_check.py:84`, `test_agent_suite_doctor.py:101`.
  - juniper-deploy `tests/`: 5 sites — `test_doctor_provenance_derivation.py:78`, `test_image_provenance_preflight.py:66`, `test_build_freshness_preflight.py:80`, `test_compose_bind_posture_attestation.py:178`, `test_script_regressions.py:104`.
  - All other repos use only in-process `patch.dict(os.environ, ...)` — env-var patching, not a subprocess `env=` frame-local; not a leak vector.
- Secondary channel (`msg=proc.stdout+stderr`, the only CI-visible path) leaks only if the spawned program itself dumps the environment; no juniper CLI does. Out of scope unless evidence appears.

### 2.2 CodeQL pin survey (all 8 repos, exact shas)

- juniper-cascor (**red main**): `analyze` + `upload-sarif` @ `7188fc36` (v4.37.1); `init` + `autobuild` @ `99df26d4` (v4.37.0) — init writes a 4.37.0 config, the 4.37.1 analyze refuses it.
- juniper-data (**red main**): `init` @ v4.37.1; `analyze`/`autobuild`/`upload-sarif` @ v4.37.0 — same class, inverted.
- juniper-canopy: init/analyze/autobuild consistent @ v4.37.0; `upload-sarif` @ v4.37.1 in a separate SARIF-upload workflow — main CodeQL green; hygiene-only skew.
- juniper-ml, juniper-cascor-worker, juniper-cascor-client, juniper-data-client: all consistent @ v4.37.0 (latent — will skew on a future partial bump).
- juniper-deploy: standalone `upload-sarif` @ v4.37.1 only — consistent; needs nothing.
- **Root-cause prevention**: no repo's `.github/dependabot.yml` `github-actions` block has a `groups:` stanza (the pip blocks do), so subaction bumps are not atomic. A `codeql-action` group patterned on `github/codeql-action*` makes every future bump one PR touching all subactions together.

### 2.3 Recurrence parity — gap list (all deploy-side; NO canopy code change needed)

- Canopy already ships complete outbound recurrence key support (A1-era, in current images): `src/settings.py:270` `recurrence_api_key` (validator at lines 527-549 resolves `JUNIPER_CANOPY_RECURRENCE_API_KEY[_FILE]`, falling back to shared `JUNIPER_RECURRENCE_API_KEY`, via `secrets_util.get_secret`); wired at `src/backend/__init__.py:132` into `RecurrenceServiceAdapter`, which attaches `X-API-Key` (`recurrence_service_adapter.py:297-301`) and maps 401/403 to a typed auth error.
- Gaps to fill in `juniper-deploy` (verified file:line at current main):
  1. Top-level `secrets:` block (`docker-compose.yml:1007-1029`): no `juniper_recurrence_api_keys` entry; `secrets.example/` has 9 placeholder files, none for recurrence.
  2. Provisioning sync (the known incomplete-set incident class): `scripts/prepare_secrets.bash` `MAPPINGS` (lines 51-59) and `Makefile` `SECRETS_FILES` (lines 61-66) both lack the recurrence file.
  3. Recurrence service block (lines 540-565): needs `JUNIPER_RECURRENCE_API_KEYS_FILE=/run/secrets/juniper_recurrence_api_keys`, `JUNIPER_RECURRENCE_REQUIRE_AUTH` (operator-overridable, default true), the secret in its `secrets:` list, and the deploy#158 opt-in comment (lines 556-563) rewritten as active wiring.
  4. Consumers: `juniper-canopy` service (secrets list at lines 673-676 + env `JUNIPER_CANOPY_RECURRENCE_API_KEY_FILE`, beside the line-645 juniper-data mirror) and `juniper-canopy-demo` (lines 700-771 — env + a NEW `secrets:` block; it has none today). `juniper-canopy-dev` sets no recurrence URL — not a consumer.
  5. Nothing else needs the key: the compose healthcheck, `scripts/health_check.sh`, and `scripts/wait_for_services.sh` all probe `/v1/health[/ready]`, which is exempt per juniper-service-core `EXEMPT_PATHS` (`juniper-service-core/juniper_service_core/middleware.py:24-38`, applied at line 203); Prometheus scrapes `/metrics` behind the separate `MetricsAuthMiddleware` IP allowlist. The port-8210 hits in the worker healthcheck and helm values are the worker's own health server (coincidental port reuse).
  6. `.env.example` lines 70-73 opt-in comment updated to reflect auth-on default.
- Naming nuance (matches the data/cascor precedent): the recurrence service reads the plural accept-list `JUNIPER_RECURRENCE_API_KEYS[_FILE]`; canopy sends the singular `JUNIPER_CANOPY_RECURRENCE_API_KEY[_FILE]`; both mount the same secret file per the symmetric-mount design (compose lines 990-998) — the asymmetry class caused past 401s (`notes/SECRET_MOUNT_SYMMETRY_2026-05-28.md` in juniper-deploy).
- Recurrence is in all four compose profiles, so parity applies stack-wide (like data), including demo.

## 3. Implementation

### 3.1 Item 1 — env-repr redaction (juniper-ml PR + juniper-deploy PR)

- New ~10-line helper `tests/redacted_env.py` in each repo: `class RedactedEnv(dict)` with `__repr__`/`__str__` returning `<RedactedEnv: N vars (values redacted)>`, a constructor accepting base mappings + keyword overrides, and a `copy()` that preserves the type. A real `str -> str` mapping: `subprocess.run(env=...)` accepts it; item get/set (`env["PATH"] = ...`) is untouched, so existing overrides keep working. Because the leak is the frame-local's repr, building the mapping as `RedactedEnv` neutralizes every traceback mode.
- Convert all 16 juniper-ml sites and all 5 juniper-deploy sites: `os.environ.copy()` / `dict(os.environ[, ...])` / `{**os.environ, ...}` become `RedactedEnv(os.environ[, ...])`.
- **Lint gate** per repo: `tests/test_env_repr_safety.py` scans `tests/*.py` (excluding itself and the helper) and fails on any raw `os.environ`-derived mapping construction — regex `os\.environ\.copy\(\)`, `(?<!patch\.)\bdict\(os\.environ`, `\{\*\*os\.environ` — so `patch.dict(os.environ, ...)` is deliberately not flagged. Includes a synthetic-violation self-test proving the scanner bites, plus behavioural tests: `repr()` shows no values, and a spawned `sys.executable -c` child sees the injected vars.
- juniper-ml co-changes: register the new test file in `.github/workflows/ci.yml`'s unittest list and in `AGENTS.md` (test-command list + tests-section bullet), per house convention.
- Gates: juniper-ml full unittest battery + pre-commit; juniper-deploy `pytest tests/ -v --tb=short` + pre-commit.

### 3.2 Item 2 — CodeQL align + prevention (fleet-wide, 7 PRs; owner decision 2026-07-21)

One small PR in each of: juniper-cascor, juniper-data (red), juniper-canopy (skew), juniper-ml, juniper-cascor-worker, juniper-cascor-client, juniper-data-client (latent). Each PR:

1. Aligns every `github/codeql-action/{init,autobuild,analyze,upload-sarif}` ref in every workflow file to the single sha `7188fc363630916deb702c7fdcf4e481b751f97a  # v4.37.1` (already live in cascor/data/canopy/deploy — no new version introduced).
2. Adds to the `github-actions` block of `.github/dependabot.yml` a `groups:` stanza named `codeql-action` with pattern `github/codeql-action*` (shape mirrors the existing pip `groups:` precedent).

juniper-deploy needs nothing (already consistent @ v4.37.1).

### 3.3 Item 3 — recurrence auth parity (one juniper-deploy PR)

Execute the section-2.3 gap list in a single PR (branch `feature/recurrence-auth-parity`): compose secret + `secrets.example/` placeholder + `prepare_secrets.bash`/`Makefile` sync + recurrence service env/secret/flag + canopy and canopy-demo consumer wiring + comment and `.env.example` updates. Shared-secret single-source-of-truth convention exactly as `juniper_data_api_keys` (recurrence validates the one-element accept-list; canopy sends the same token as `X-API-Key`). No merge-order dependency on any other PR. After merge, `prepare-secrets` (or `.env.secrets.enc`) must populate the new file with a real token — an empty file now refuses recurrence boot by design (SEC-F01 fail-closed; escape hatches: `JUNIPER_RECURRENCE_REQUIRE_AUTH=false` or `JUNIPER_SKIP_AUTH_POSTURE_CHECK=1`).

## 4. Verification

- Item 1 (both repos): grep proves zero raw `os.environ`-derived sites remain under `tests/`; the lint gate's synthetic-violation self-test bites; `repr()` of a built `RedactedEnv` shows no values; juniper-ml full unittest battery and juniper-deploy pytest lane green; pre-commit green.
- Item 2 (7 repos): per-repo grep shows exactly one distinct sha across all codeql refs; pre-commit/yamllint green; post-merge CodeQL run green on `main` (cascor and data flip red-to-green), triggered or observed via `gh` per the verify-new-CI-workflows feedback rule.
- Item 3: `docker compose --profile "*" config` clean and renders the new secret + env on all four touched blocks; `bash scripts/prepare_secrets.bash` creates the 10th file; `scripts/doctor.sh` full-set derivation intact. Post-merge bring-up (owner): recurrence returns 401 for keyless protected routes, health stays 200, canopy-to-recurrence A1 flow works with the shared token.

## 5. Delivery and sequencing (10 implementation PRs + this plan doc; all owner-merge, no auto-merge)

1. **Wave 1 (parallel, independent)**: juniper-ml env-redaction PR; juniper-deploy env-redaction PR; 7 CodeQL align+group PRs. The juniper-ml env and CodeQL PRs use separate branches/worktrees.
2. **Wave 2** (after wave 1 is open, per the owner's sequencing): the juniper-deploy recurrence-parity PR (separate branch from deploy's env PR; trivial rebase expected if one merges first).
3. House rules throughout: centralized worktrees, `-c commit.gpgsign=false` headless commits, `gh pr list` dup-guard per repo before opening, one tidy commit per PR.

## 6. Validation record

Discovery performed 2026-07-20/21 by the authoring session (direct probes: CodeQL pin survey across all 8 repos, dependabot group audit, canopy main CodeQL state) plus two read-only Explore agents: (a) recurrence-parity discovery across juniper-canopy / juniper-deploy / juniper-service-core — which overturned the working assumption that canopy needed outbound-key code (it exists since A1) and produced the section-2.3 gap list with file:line evidence; (b) env-leak forensics across all repos — which pinned the saferepr frame-local mechanism, bounded the scope to juniper-ml + juniper-deploy, and cleared mock/msg/bash channels. Owner approved the plan as-is on 2026-07-21, selecting fleet-wide CodeQL scope (7 repos) and the two-repo redaction scope.
