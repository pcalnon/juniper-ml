# Juniper Ecosystem Environment-Drift Audit (S-1)

**Audit ID**: S-1 — ecosystem env-drift sweep (custom-agent-suite enhancement plan, final item)
**Auditor**: `auditor` custom-agent (read-only findings reviewer)
**Date**: 2026-07-01
**Repo / branch**: `juniper-ml` @ `worktree-clever-stargazing-allen`
**Head SHA**: `6812da07090e2fc1cc83cb1576d565ccb9717467` (working tree clean at audit time)
**Working dir**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/clever-stargazing-allen`
**Nature**: point-in-time snapshot of the *live on-host conda environments*; read-only; no code / config / lockfile changed.

---

## 1. Scope

Detect any installed `juniper-*` distribution across the live conda environments that is **below its
repo's `pyproject.toml` floor** (`BELOW_FLOOR`), **absent** (`MISSING`), or an **orphaned editable install**
(`ORPHANED`) — the "green tests / dead app" failure class (the canopy incident), swept **ecosystem-wide**
rather than for a single repo.

Two read-only tools produce the evidence (both read `*.dist-info` metadata directly and never invoke the
target interpreter, so they still work when that interpreter is itself broken):

- `util/env_floor_drift_check.py` (gap **E-2 / I-2**, shipped) — installed version vs declared floor.
- `util/editable_install_drift_check.py` — editable-install target liveness.

**(env, repo) pairs audited** (env → repo whose `pyproject.toml` floors are the requirement):

| Conda env | Target repo | Rationale |
|-----------|-------------|-----------|
| `JuniperCanopy1` | `juniper-canopy` | canopy service env |
| `JuniperCascor1` | `juniper-cascor` | cascor **server** env |
| `JuniperCascor1` | `juniper-cascor-worker` | JuniperCascor1 is the unified cascor **server+worker** env |
| `JuniperData` | `juniper-data` | data service env |

Editable-install drift is swept across **all** non-deprecated `Juniper*` conda envs in one pass.

---

## 2. Checklist applied

| # | Item | Pass criterion |
|---|------|----------------|
| C1 | No `BELOW_FLOOR` in any (env, repo) pair | `env_floor_drift_check.py` reports `BELOW_FLOOR: 0` and exits 0 for every pair |
| C2 | No meaningful `MISSING` | Any `MISSING` is triaged: an optional-extra miss is benign; a **core** `[project].dependencies` miss is a finding |
| C3 | `--strict` behaviour recorded | For each pair, note whether `MISSING` flips the plain exit 0 → exit 1 under `--strict` |
| C4 | No `ORPHANED` editable install | `editable_install_drift_check.py` reports `ORPHANED: 0` and exits 0 |
| C5 | `WORKTREE_PINNED` editables noted | Soft/latent warnings recorded with their canonical re-point target |
| C6 | Every target repo + env present | Absent repo/env is recorded as a finding, not a crash |

**Verdict legend**: `verified pass` / `verified fail` / `could not verify` are kept distinct (§8).

---

## 3. Headline verdict

### `DRIFT FOUND`

The **exact canopy-incident class — a plain wheel `BELOW_FLOOR` — is absent ecosystem-wide** (`BELOW_FLOOR: 0`
in all four pairs; C1 **verified pass**). Drift was nonetheless found in two adjacent classes plus one latent
warning:

| ID | Class | Env | Package | Severity |
|----|-------|-----|---------|----------|
| **S1-F1** | `MISSING` core dep | `JuniperCascor1` | `juniper-cascor-model` (worker core dep, not installed) | **medium** |
| **S1-F2** | `ORPHANED` editable | `JuniperCascor1` | `juniper-recurrence-client` (points at a removed worktree) | **medium** |
| **S1-F3** | `WORKTREE_PINNED` editable | `JuniperCascor1` | `juniper-ci-tools` (points inside a live session worktree) | **low** |

All three findings are in `JuniperCascor1`. `JuniperCanopy1` and `JuniperData` are **fully clean**.

---

## 4. Env-floor drift findings (per env, repo pair)

Command shape (paths abbreviated): `python3 util/env_floor_drift_check.py --repo-root <REPO> --env <ENV> --json`
(and again with `--strict`). Full raw JSON + exit codes in the appendix (§10).

### 4.1 `JuniperCanopy1` → `juniper-canopy` — verified pass (CLEAN)

4 juniper floors, all `OK`. Plain exit **0**, `--strict` exit **0**.

| Package | Floor | Installed | Status |
|---------|-------|-----------|--------|
| juniper-cascor-client | 0.5.0 | 0.5.0 | OK |
| juniper-cascor-protocol | 0.1.0 | 0.1.0 | OK |
| juniper-data-client | 0.4.1 | 0.4.1 | OK |
| juniper-observability | 0.4.0 | 0.4.0 | OK |

This directly confirms the **canopy "green tests / dead app" remediation held** — the env that originally
carried the below-floor client wheels is now at or above every declared floor.

### 4.2 `JuniperCascor1` → `juniper-cascor` — verified pass (CLEAN)

5 juniper floors, all `OK`. Plain exit **0**, `--strict` exit **0**.

| Package | Floor | Installed | Status |
|---------|-------|-----------|--------|
| juniper-cascor-protocol | 0.1.0a0 | 0.1.0 | OK |
| juniper-data | 0.4.0 | 0.6.0 | OK |
| juniper-data-client | 0.3.0 | 0.4.2 | OK |
| juniper-model-core | 0.2.0 | 0.2.0 | OK |
| juniper-observability | 0.4.0 | 0.4.0 | OK |

### 4.3 `JuniperCascor1` → `juniper-cascor-worker` — verified fail (**S1-F1**, `MISSING` core dep)

3 juniper floors: 2 `OK`, **1 `MISSING`**. Plain exit **0** (MISSING is a soft note); **`--strict` exit 1**
(the MISSING flips it).

| Package | Floor | Installed | Status |
|---------|-------|-----------|--------|
| **juniper-cascor-model** | **0.1.0** | **(not installed)** | **MISSING** |
| juniper-cascor-protocol | 0.1.0 | 0.1.0 | OK |
| juniper-config-tools | 0.1.0 | 0.1.0 | OK |

**Finding S1-F1.** `juniper-cascor-model>=0.1.0` is declared at `juniper-cascor-worker/pyproject.toml:66`,
which sits **inside the `[project].dependencies` list** (`dependencies = [` opens at `:41`, closes `]` at
`:67`; `[project.optional-dependencies]` only begins at `:69`). It is therefore a **core runtime
dependency**, not an optional extra. The in-file comment (`:61-65`) states it is the CW-05 candidate-training
core that "Provides the top-level `candidate_unit` import" the worker executes. It is **absent** from
`JuniperCascor1`, which is the designated unified cascor **server+worker** env.

- **Evidence**: `env_floor_drift_check.py … --repo-root …/juniper-cascor-worker --env JuniperCascor1 --json`
  → `{"package":"juniper-cascor-model","floor":"0.1.0","installed":null,"status":"MISSING"}`; plain exit 0,
  `--strict` exit 1 (§10). Declaration: `juniper-cascor-worker/pyproject.toml:66` (core dep) + `:61-65` (comment).
- **Why it matters**: if the distributed worker is run from `JuniperCascor1` and reaches the candidate-training
  path, `import candidate_unit` (provided by this package) fails — the "dead app" class the S-1 sweep targets.
  Unlike a silent `BELOW_FLOOR`, a `MISSING` fails **loud** at import, and it is only `--strict`-fatal — hence
  **medium**, not high.
- **Remediation**: install the package into the env —
  `/opt/miniforge3/envs/JuniperCascor1/bin/python -m pip install "juniper-cascor-model>=0.1.0"` (or reinstall
  from the worker's `requirements.lock`). If `juniper-cascor-model` 0.1.0 is not yet on PyPI or the worker is
  intentionally not run from this env, the owner should confirm that expectation instead of installing.
- **Escalation note**: escalate to **high** if (a) the worker is actively executed from `JuniperCascor1`
  **and** (b) `candidate_unit` cannot be resolved from another on-`sys.path` source. Neither is verifiable
  read-only (see §8).

### 4.4 `JuniperData` → `juniper-data` — verified pass (CLEAN)

2 juniper floors, all `OK`. Plain exit **0**, `--strict` exit **0**.

| Package | Floor | Installed | Status |
|---------|-------|-----------|--------|
| juniper-data-client | 0.3.0 | 0.4.1 | OK |
| juniper-observability | 0.4.0 | 0.4.0 | OK |

---

## 5. Editable-install drift findings

Command: `python3 util/editable_install_drift_check.py --json` — swept all non-deprecated `Juniper*` envs
(`*-DEPRECATED` envs are skipped by the tool by design). **Exit 1.** Summary: 9 editables — **7 FRESH,
1 WORKTREE_PINNED, 1 ORPHANED**. Canonical re-point paths below are the tool's own resolution, captured with a
read-only `--fix --dry-run` (prints the pip plan, runs no pip); full JSON in §10.

### S1-F2 — `ORPHANED` editable: `juniper-recurrence-client` (verified fail)

- **Env**: `JuniperCascor1`
- **Broken target**: `…/worktrees/juniper-recurrence--feat--recurrence-client--20260618-1924--6a25cb17/juniper-recurrence-client`
  — the worktree was removed, so `import juniper_recurrence_client` is broken **now** (the classic stale-
  editable-after-worktree-cleanup bit-rot class).
- **Canonical repo to re-point to**: `/home/pcalnon/Development/python/Juniper/juniper-recurrence/juniper-recurrence-client`
  (dir confirmed present; tool resolves it uniquely — `resolvable: true`).
- **Scope note**: `juniper-recurrence-client` is **not** a declared dependency of the env's primary apps
  (it appears in neither `juniper-cascor` nor `juniper-cascor-worker` floors — §4.2/§4.3), so this is leftover
  editable dev cruft in the shared env, not a broken primary-service dependency. Hence **medium**, not high —
  but it is an active broken import and it makes the editable checker exit 1.
- **Remediation**: `util/editable_install_drift_check.py --fix` (auto re-points ORPHANED to canonical), or
  manually `/opt/miniforge3/envs/JuniperCascor1/bin/python -m pip install -e /home/pcalnon/Development/python/Juniper/juniper-recurrence/juniper-recurrence-client --no-deps --force-reinstall`.
  If the env no longer needs it, `pip uninstall juniper-recurrence-client` is the alternative.

### S1-F3 — `WORKTREE_PINNED` editable: `juniper-ci-tools` (verified — latent)

- **Env**: `JuniperCascor1`
- **Target**: `…/juniper-ml/.claude/worktrees/validated-squishing-pond/juniper-ci-tools` — a live session
  worktree. Works today; will **orphan** (become S1-F2's class) the moment that worktree is cleaned.
- **Canonical repo to re-point to**: `/home/pcalnon/Development/python/Juniper/juniper-ml/juniper-ci-tools`
  (tool resolves it uniquely — `resolvable: true`).
- **Remediation**: `util/editable_install_drift_check.py --fix --fix-worktree-pinned`, or manually re-point to
  the canonical checkout above. **low** severity (latent, not yet broken).

### FRESH (verified pass) — no action

7 FRESH editables: `JuniperCanopy1/juniper-canopy`; `JuniperCascor1/{juniper-cascor, juniper-cascor-client,
juniper-data, juniper-recurrence}`; `JuniperData/{juniper-data, juniper-data-client}` — all point at stable
non-worktree checkouts.

---

## 6. Severity table

| ID | Finding | Env / repo | Dep | Class | Likelihood of live impact | Effort to fix | Severity |
|----|---------|------------|-----|-------|---------------------------|---------------|----------|
| S1-F1 | Core dep not installed | JuniperCascor1 / juniper-cascor-worker | `juniper-cascor-model` (floor 0.1.0, installed none) | MISSING (core) | medium (only if worker run from this env) | low (1 pip install) | **medium** |
| S1-F2 | Orphaned editable | JuniperCascor1 | `juniper-recurrence-client` | ORPHANED | high that import fails / low that a primary path hits it | low (`--fix`) | **medium** |
| S1-F3 | Worktree-pinned editable | JuniperCascor1 | `juniper-ci-tools` | WORKTREE_PINNED | latent (only on worktree cleanup) | low (`--fix --fix-worktree-pinned`) | **low** |

**Counts** — `BELOW_FLOOR`: **0** · `MISSING` (core): **1** · `ORPHANED`: **1** · `WORKTREE_PINNED`: **1**.
By severity: high **0**, medium **2**, low **1**.

---

## 7. Remediation checklist

Owner-driven follow-up (this audit changed nothing). All commands are for the **host**, not CI:

- [ ] **S1-F1** — decide intent for `juniper-cascor-model` in `JuniperCascor1`: either
      `/opt/miniforge3/envs/JuniperCascor1/bin/python -m pip install "juniper-cascor-model>=0.1.0"`
      (or reinstall the worker from its `requirements.lock`), **or** confirm the worker is not run from this
      env / the package is pending publish and record that.
- [ ] **S1-F2** — re-point or remove the orphaned `juniper-recurrence-client`:
      `util/editable_install_drift_check.py --fix` (re-points to
      `/home/pcalnon/Development/python/Juniper/juniper-recurrence/juniper-recurrence-client`), or
      `pip uninstall juniper-recurrence-client` if the env no longer needs it.
- [ ] **S1-F3** — re-point `juniper-ci-tools` off the session worktree before it is cleaned:
      `util/editable_install_drift_check.py --fix --fix-worktree-pinned` (→
      `/home/pcalnon/Development/python/Juniper/juniper-ml/juniper-ci-tools`).
- [ ] **Re-run to confirm CLEAN**: repeat §4.3 (`--strict` should return exit 0) and
      `util/editable_install_drift_check.py --json` (should return `ORPHANED: 0`, exit 0) after fixes.
- [ ] **Prevention (shift-left)**: track E-8 (boot-time floor self-check) so a `MISSING`/`BELOW_FLOOR` fails
      loud at first app start rather than waiting on a manual sweep (§9).

---

## 8. Methodology, scope boundaries, and could-not-verify

- **Core-vs-optional triage (C2)**: `env_floor_drift_check.py` aggregates floors from `[project].dependencies`
  **and every** `[project.optional-dependencies]` extra (`util/env_floor_drift_check.py:171-193`). A `MISSING`
  from an optional extra would be benign. The one `MISSING` (S1-F1) was hand-verified to be a **core**
  dependency by reading `juniper-cascor-worker/pyproject.toml:41-67`. **verified fail.**
- **Metadata-only, not import-tested**: the floor checker reads `*.dist-info/METADATA` `Version`; an `OK`
  therefore means "installed at/above floor", **not** "imports successfully". Whether S1-F1's worker actually
  cannot resolve `candidate_unit` at runtime (and whether the worker is run from this env at all) is a runtime
  question — **could not verify** read-only; captured as the S1-F1 escalation note, not asserted.
- **Envs actually scanned**: env-floor runs targeted `JuniperCanopy1`, `JuniperCascor1`, `JuniperData`
  explicitly. The editable sweep (no `--env` filter, glob `Juniper*`, `*-DEPRECATED` excluded by design)
  covered `JuniperCanopy1`, `JuniperCascor1`, `JuniperCassandra`, `JuniperData`; `JuniperCassandra` yielded no
  juniper editables. `JuniperCanopy-DEPRECATED` / `JuniperCascor-DEPRECATED` / `JuniperPython-DEPRECATED` were
  intentionally **not** scanned (dead by design; their drift is expected noise) — **out of scope**, not a gap.
- **Repo/env presence (C6)**: all four target repos and all three named envs exist (verified via `ls` at
  audit start) — no absence findings.
- **`--strict` semantics recorded (C3)**: only §4.3 changed exit code under `--strict` (0 → 1 on the MISSING);
  the other three pairs stayed exit 0 both ways.

---

## 9. Provenance

- **What S-1 is**: the final item of the custom-agent-suite enhancement plan
  (`notes/JUNIPER_2026-06-27_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md`):
  - `:159` — S-1 ledger row: *"Sibling-env plain-wheel drift unaudited … the downstream **use** of E-2 (an
    audit, gated on E-2 landing)."*
  - `:214` — *"Deferred audit: S-1 — the ecosystem env-drift sweep, gated on E-2 landing (the tool S-1 needs
    is E-2)."*
  - `:636` — *"S-1 (a deferred ecosystem env-drift *audit*, run by the `auditor`/E-2 once **E-2 (PR-2)** has
    landed)."*
- **Gating dependency (satisfied)**: S-1 was gated on **E-2 = I-2 fix**, now shipped as
  `util/env_floor_drift_check.py` (the installed-vs-floor checker used here). E-2 is the *detection* half.
- **Complement (not exercised here)**: **E-8** is the *prevention* half — a boot-time self-check that fails
  loud when installed `juniper-*` wheels are below the app's own floors. Per the enhancement plan (`:167`,
  `:212-213`) and the task brief, E-8's runtime boot check now lives in `juniper-service-core` (0.4.0) +
  canopy. That runtime behaviour was **not** independently verified in this audit — S-1 is detection via E-2,
  and E-8 verification is out of scope; it is cited as context, not as a verified finding.
- **Snapshot semantics**: this is a **point-in-time** reading of the live host environments at head SHA
  `6812da07090e2fc1cc83cb1576d565ccb9717467` on 2026-07-01. Environments mutate under normal dev; re-run the
  §4/§5 commands to refresh.

---

## 10. Raw evidence appendix (commands + exit codes)

All commands run from the juniper-ml worktree root
(`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/clever-stargazing-allen`).

### 10.1 Env-floor drift (per pair)

```text
# 4.1 JuniperCanopy1 -> juniper-canopy
python3 util/env_floor_drift_check.py --repo-root .../juniper-canopy --env JuniperCanopy1 --json
  summary: {OK:4, BELOW_FLOOR:0, MISSING:0, total:4}   plain EXIT=0   --strict EXIT=0

# 4.2 JuniperCascor1 -> juniper-cascor
python3 util/env_floor_drift_check.py --repo-root .../juniper-cascor --env JuniperCascor1 --json
  summary: {OK:5, BELOW_FLOOR:0, MISSING:0, total:5}   plain EXIT=0   --strict EXIT=0

# 4.3 JuniperCascor1 -> juniper-cascor-worker   (S1-F1)
python3 util/env_floor_drift_check.py --repo-root .../juniper-cascor-worker --env JuniperCascor1 --json
  findings: juniper-cascor-model floor=0.1.0 installed=null status=MISSING
            juniper-cascor-protocol floor=0.1.0 installed=0.1.0 status=OK
            juniper-config-tools    floor=0.1.0 installed=0.1.0 status=OK
  summary: {OK:2, BELOW_FLOOR:0, MISSING:1, total:3}   plain EXIT=0   --strict EXIT=1

# 4.4 JuniperData -> juniper-data
python3 util/env_floor_drift_check.py --repo-root .../juniper-data --env JuniperData --json
  summary: {OK:2, BELOW_FLOOR:0, MISSING:0, total:2}   plain EXIT=0   --strict EXIT=0
```

### 10.2 Editable-install drift (all non-deprecated Juniper* envs)

```text
python3 util/editable_install_drift_check.py --json          # EXIT=1
  summary: {FRESH:7, WORKTREE_PINNED:1, ORPHANED:1, total:9}

  ORPHANED         JuniperCascor1  juniper-recurrence-client
    from: .../worktrees/juniper-recurrence--feat--recurrence-client--20260618-1924--6a25cb17/juniper-recurrence-client
  WORKTREE_PINNED  JuniperCascor1  juniper-ci-tools
    from: .../juniper-ml/.claude/worktrees/validated-squishing-pond/juniper-ci-tools
  FRESH            JuniperCanopy1  juniper-canopy
  FRESH            JuniperCascor1  juniper-cascor
  FRESH            JuniperCascor1  juniper-cascor-client
  FRESH            JuniperCascor1  juniper-data
  FRESH            JuniperCascor1  juniper-recurrence
  FRESH            JuniperData     juniper-data
  FRESH            JuniperData     juniper-data-client

# read-only canonical re-point resolution (prints pip plan, runs no pip):
python3 util/editable_install_drift_check.py --fix --fix-worktree-pinned --dry-run --json
  juniper-ci-tools           -> /home/pcalnon/Development/python/Juniper/juniper-ml/juniper-ci-tools           (resolvable)
  juniper-recurrence-client  -> /home/pcalnon/Development/python/Juniper/juniper-recurrence/juniper-recurrence-client (resolvable)
```

### 10.3 Corroborating source citations

```text
juniper-cascor-worker/pyproject.toml:41   dependencies = [            # core-dep list opens
juniper-cascor-worker/pyproject.toml:61-65  # CW-05 comment: "Provides the top-level candidate_unit import"
juniper-cascor-worker/pyproject.toml:66   "juniper-cascor-model>=0.1.0",   # core runtime dep (MISSING)
juniper-cascor-worker/pyproject.toml:67   ]                            # core-dep list closes
juniper-cascor-worker/pyproject.toml:69   [project.optional-dependencies]  # extras begin AFTER the miss
util/env_floor_drift_check.py:39-43       exit-code contract (0 clean / 1 BELOW_FLOOR|--strict MISSING / 2 error)
util/env_floor_drift_check.py:171-193     floors aggregated from dependencies + all optional-dependencies
util/editable_install_drift_check.py:29-33  exit-code contract (0 / 1 ORPHANED|--strict WORKTREE / 2)
util/editable_install_drift_check.py:163-173  FRESH / WORKTREE_PINNED / ORPHANED classification
```

---

*End of S-1 audit. This report is the sole artifact produced; no code, pyproject, or lockfile was modified.*
