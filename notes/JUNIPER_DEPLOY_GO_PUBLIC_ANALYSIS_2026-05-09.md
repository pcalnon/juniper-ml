# juniper-deploy: Public-Release Risk & Benefit Analysis

**Author**: Paul Calnon (Claude-assisted)
**Date**: 2026-05-09
**Scope**: Evaluate the implications of taking the currently-private
`juniper-deploy` repository public.
**Repo state at time of analysis**:
`pcalnon/juniper-deploy` (PRIVATE), `main` @ `8b35750`, 142 commits,
v0.2.1, MIT license declared.

---

## 0. TL;DR

| Question | Recommendation | Confidence |
|----------|----------------|------------|
| Take `juniper-deploy` public? | **Yes**, after the four blocking remediations in §6. | High |
| Publish to PyPI? | **No.** It is not a Python package — `pyproject.toml` declares only pytest config; there is no `[project]` block, no install entry points, no importable Python module. | Very high |
| Bundle into `pip install juniper-ml[all]`? | **No.** It ships a Docker Compose file, a Helm chart, a Makefile, and `secrets.example/` placeholders. It is a *deployment artifact set*, not a runtime dependency of any Juniper Python app. | Very high |
| CI changes required before going public? | **Yes** — small, mostly already done. See §7. | High |

The work to take it public is **bounded and mostly mechanical**. The only
non-trivial item is rotating the placeholder Grafana password that briefly
sat as the literal string `admin` in `secrets/grafana_admin_password.txt`
in commit history (already remediated functionally; see §5.B).

---

## 1. Investigative Approach

The analysis was performed against the actual on-disk state of
`/home/pcalnon/Development/python/Juniper/juniper-deploy`
(branch `main`, last commit `8b35750`, 142 commits) plus
the public/private status of the surrounding 7 ecosystem repos
fetched via `gh repo view`. Specifically:

1. **Inventory** — listed top-level files, directory tree, file count
   (183 tracked files), git remote, branch, recent commits, license
   declaration, version (0.2.1).
2. **Configuration audit** — read `docker-compose.yml` (629 lines),
   `Makefile` (8.5 KB), `.env.example` (156 lines),
   `.env.demo`, `.env.observability`, `.env.secrets.example`,
   `.env.secrets.enc` (SOPS-encrypted), `.sops.yaml`, `.gitleaks.toml`,
   `.pre-commit-config.yaml`, `pyproject.toml`,
   `prometheus/prometheus.yml`, `alertmanager/alertmanager.yml`,
   the `k8s/helm/juniper/` chart, and `secrets/`/`secrets.example/`
   contents.
3. **CI audit** — read all three GitHub Actions workflows
   (`ci.yml`, `claude.yml`, `security-scan.yml`).
4. **Secret-leak hunt** —
   - `git log --all -p` regex-scanned for AWS keys, GitHub PAT prefixes,
     OpenAI keys, PEM-encoded private keys.
   - Walked every `secrets/*.txt` file's full git history.
   - Listed every author email that appears in `git log`.
   - Searched committed files for real domains, RFC1918 IPs, internal
     hostnames.
5. **Ecosystem context** — checked `gh repo view` visibility for all 8
   peer repos; `grep`'d sibling repos for outbound mentions of
   `juniper-deploy`; read the cross-repo workflow that already tries to
   clone it (`juniper-ml/.github/workflows/docs-full-check.yml`).
6. **Authorial intent** — read `notes/SECURITY_REMEDIATION_PLAN.md`,
   `notes/SOPS_AUDIT_AND_REMEDIATION_PLAN.md`, and the
   `JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` to understand
   the prior security mitigations and the project's framing (already
   anticipates external use).

---

## 2. What `juniper-deploy` Is, and What It Isn't

### Functional surface

`juniper-deploy` is the **deployment-and-integration repo** for the
Juniper ML platform. Concretely, it contains:

- A 30 KB **`docker-compose.yml`** orchestrating 12 services across
  4 profiles (`full`, `demo`, `dev`, `test`) plus the additive
  `observability` profile (Prometheus, AlertManager, Grafana).
- A **Makefile** (23 targets) that wraps `docker compose` for ergonomics
  (`make up`, `make demo`, `make health`, `make obs`, …).
- **`scripts/`** — small bash health-check / wait-for-services /
  integration-test helpers.
- **Integration tests** in `tests/` — pytest, `requirements-test.txt`
  (just `requests` + `pytest`), with `JUNIPER_TEST_*` fixtures that
  auto-skip when Docker isn't running, plus
  `test_compose_security_config.py` (regression test that the compose
  file keeps its security hardening).
- **Observability assets** — Prometheus scrape config, alert/recording
  rules, AlertManager routing, four pre-provisioned Grafana dashboards.
- **`k8s/helm/juniper/`** — a Helm chart (Chart v2 deps on Bitnami Redis
  20.7.1, Bitnami Cassandra 12.1.4, kube-prometheus-stack 72.6.3,
  bundled as `.tgz` files in `charts/`), templates for Deployments,
  Services, ServiceMonitors, NetworkPolicies, and an Ingress.
- **Secrets plumbing** — Docker file-secrets pattern, SOPS+age
  encryption for `.env.secrets`, SOPS pre-commit guard, gitleaks config.
- Extensive **`docs/`** (8 user-facing docs) and **`notes/`** (~20 plans
  / runbooks / audits, including a `SECURITY_REMEDIATION_PLAN.md` that
  closes a public-disclosure-grade SOPS gap from PR #14).

### What it is **NOT**

- **Not a Python package.** `pyproject.toml` only declares
  `[tool.pytest.ini_options]`. There is no `[project]` block, no
  `[project.scripts]`, no version, no PyPI metadata. There is no
  importable Python module in the repo (the only `.py` files live
  under `tests/`).
- **Not a runtime dependency** of any Juniper service. Nothing in
  `juniper-cascor`, `juniper-data`, `juniper-canopy`, `juniper-ml`, or
  any client library imports anything from `juniper-deploy`.
- **Not a release artifact** — it has no `CHANGELOG`-driven semver tag
  publishing pipeline (versions are only tracked inside `AGENTS.md` and
  `CHANGELOG.md` — useful internal docs, not a release surface).

This shape is decisive for the PyPI / `juniper-ml[all]` questions
(§§9–10): there is nothing meaningful to package or import.

---

## 3. Role in the Juniper Development Ecosystem

### Dependency direction (today)

```text
juniper-deploy ──orchestrates──> juniper-data, juniper-cascor,
                                  juniper-canopy (via Docker)
                ──orchestrates──> Redis, Cassandra, Prometheus,
                                  Grafana, AlertManager
juniper-ml's docs-full-check.yml ──clones──> juniper-deploy
juniper-ml/README.md, DEVELOPER_CHEATSHEET ──link to──> juniper-deploy
```

There is **no inbound code dependency** — just **documentation and CI
references**. The 7 public peer repos already advertise
juniper-deploy's existence and role to the world, but a curious external
collaborator cannot follow those references today.

### Importance to the dev environment for collaborators

For an external collaborator who wants to evaluate or contribute to
Juniper, the path to a working local environment is **drastically
shorter with `juniper-deploy` than without**:

| Path | Steps | Likelihood of a clean first run |
|------|-------|----|
| **With `juniper-deploy` (public)** | `git clone` four sibling repos, `cd juniper-deploy && make demo`, wait for healthcheck. | High — this is the validated golden path the maintainers also use. |
| **Without** | Read 3+ AGENTS.md files, build 3 conda envs (`JuniperData`, `JuniperCanopy1`, `JuniperCascor1`), wire `JUNIPER_DATA_URL` / `CASCOR_SERVICE_URL`, manage 3 separate processes. | Low — the ecosystem has Python 3.13/3.14 free-threading wrinkles, env-bound `LIBTORCH` collisions (see memory `project_canopy_libtorch_python_collision_2026-05-07`), and lockfile-freshness gates that are easy to trip on. |

In other words, **`juniper-deploy` is the user-facing front door to the
project as a whole**, and right now that door is locked. Making it
public is the single highest-leverage thing one can do for "potential
collaborators" — keeping the rest of the platform open while hiding the
launcher is the worst of both worlds.

The demo profile is particularly important here: `make demo` runs a
self-seeding spiral-dataset CasCor training without the user needing to
configure anything. That is exactly the artifact that lowers the
activation energy for a new contributor or evaluator.

---

## 4. Theoretical Security Risks of Going Public

These are the *categories* of risk associated with publishing any
infra/deploy repository, before looking at this specific one. Each is
graded against `juniper-deploy` in §5.

| # | Risk class | Description | Severity (generic) |
|---|------------|-------------|-------------------|
| T1 | Hard-coded secrets | API keys / passwords / tokens / DSNs / SMTP creds committed in plaintext or in git history. | Critical |
| T2 | Encrypted-but-leaked | SOPS / age / sealed-secrets ciphertext leaks if private key is ever shared, or the encrypted regex is too narrow. | High |
| T3 | Default-credential footguns | Hard-coded admin defaults (e.g. `admin`/`admin` for Grafana, default `root` Redis, default Postgres) that downstream users keep. | High |
| T4 | Network exposure defaults | Services bound to `0.0.0.0` by default, no authentication on `/metrics`, open Redis/Cassandra ports on the host. | High |
| T5 | Container hardening regressions | Missing `cap_drop`, `read_only`, `no-new-privileges`, running as UID 0, mounting docker.sock. | Medium–High |
| T6 | Supply-chain (image / chart pinning) | Floating tags (`:latest`), unpinned action SHAs, unpinned Helm chart deps that allow remote tampering. | Medium |
| T7 | Internal-detail disclosure | Internal hostnames, real email addresses, employee-only URLs, customer references, real Sentry DSNs. | Medium |
| T8 | PII in commit metadata | Author names/emails in `git log` are forever-public once the repo is. | Low (but irreversible) |
| T9 | Confused-deputy via CI | `pull_request_target` / `workflow_run` patterns letting forks read repo secrets; over-broad `GITHUB_TOKEN` permissions. | High |
| T10 | Vendored binary blobs | Helm chart `.tgz` files committed without provenance / version pinning; binary plugins; legacy backups. | Low–Medium |
| T11 | Documentation that names current vulnerabilities | Plans like `SECURITY_REMEDIATION_PLAN.md` that publicly describe how the project *used* to be exploitable, even if the issue is fixed. | Low–Medium |

---

## 5. Actual Security Posture of `juniper-deploy`

A point-by-point evaluation against the §4 risk catalog, based on the
audit performed.

### A. Hard-coded secrets (T1) — **CLEAN**

- `git log --all -p | grep -E '(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|sk-[a-zA-Z0-9]{40,}|-----BEGIN.*PRIVATE KEY-----)'`
  returned **one** match: `AWS_SECRET_KEY=AKIAIOSFODNN7EXAMPLE` inside
  `notes/SECURITY_REMEDIATION_PLAN.md` line 73. This is AWS's own
  canonical example access key (used in AWS public docs precisely
  because it is **not** a real key); the document is illustrating a
  past SOPS-validation gap. **Not a real secret** but should be
  re-checked by `gitleaks` on the public repo (the existing
  `.gitleaks.toml` allowlist does not currently exempt this string —
  see §6.4).
- `secrets/*.txt` (the *real* secrets directory, not
  `secrets.example/`) contains only **empty placeholder files** with a
  `.gitkeep`. The directory itself is gitignored
  (`secrets/` in `.gitignore`).
- `.env.secrets.enc` is fully SOPS-encrypted; the file's preamble
  states "All values are CHANGE_BEFORE_PRODUCTION_USE placeholders".
  The `sops_age` recipient is an age **public** key and is safe to
  share. Decrypting is impossible without the corresponding age
  *private* key, which is not in the repo.
- `.env.example`, `.env.demo`, `.env.observability` contain no
  secrets — only commented-out keys and non-sensitive defaults
  (`GRAFANA_ADMIN_USER=admin`, host/port wiring).
- `secrets.example/*.txt` contains only literal placeholders like
  `your-canopy-api-key-here`, `replace-with-real-key`,
  `CHANGE_BEFORE_PRODUCTION_USE`.

### B. Default-credential footguns (T3) — **MOSTLY CLEAN, ONE HISTORICAL ARTIFACT**

- Commit `f0665b9` (2026-04-01) **removed** the
  `GF_SECURITY_ADMIN_PASSWORD=:-admin` fallback from
  `docker-compose.yml`. Grafana now sources its admin password
  exclusively from a Docker file-secret. Good.
- However, the **placeholder file** `secrets/grafana_admin_password.txt`
  briefly contained the literal string `admin` (visible in
  `git log -p` for that path). This was always a placeholder default
  in the `secrets/` directory (not a deployed production secret), and
  the working-tree file is now empty. Still: **anyone who deploys the
  default repo today by copying `secrets/` placeholders forward needs
  to set this** — the docs and `Makefile prepare-secrets` target should
  call this out loudly.
- AlertManager: SMTP `from`, `auth_username`, and `smtp_smarthost` are
  baked in as `juniper-alerts@example.com` / `smtp.gmail.com:587` —
  flagged with `CHANGE_BEFORE_PRODUCTION_USE` comments. The SMTP
  password is supplied via Docker secret. Acceptable.

### C. Encrypted-but-leaked (T2) — **CLEAN**

- `.gitleaks.toml` already has an explicit comment forbidding the use
  of `[allowlist].paths` to exempt `*.enc` files (so a future plaintext
  drop into a `.enc` file wouldn't slip past). The `[allowlist].regexes`
  exempt the `age1...` public-key form and SOPS ciphertext envelope —
  both correct.
- `ci.yml`'s `sops-validation` job structurally validates SOPS
  metadata (presence of `sops_version`, `sops_lastmodified`,
  `sops_age__*` recipients) and asserts every value line matches
  `ENC[AES256_GCM,...]`. This is the exact gap that the
  `SECURITY_REMEDIATION_PLAN.md` PR #14 incident closed — already
  remediated.

### D. Network-exposure defaults (T4) — **GOOD**

- Default `BIND_HOST=127.0.0.1`. Services that need cross-host access
  must opt in (`BIND_HOST=0.0.0.0`).
- Two of the four Docker networks (`backend`, `data`) are declared
  `internal: true` — no host bridge, no inter-container leakage to
  the LAN.
- Prometheus' scrape of `juniper-data:/metrics` is gated by
  `MetricsAuthMiddleware` (SEC-16, IP allowlist). `notes/METRICS_AUTH_RATIONALE.md`
  documents the per-service split (cascor/canopy /metrics is only
  reachable via the internal compose network).
- No Redis or Cassandra host port is bound by default.

### E. Container hardening (T5) — **GOOD**

`grep` of `docker-compose.yml` shows widespread use of
`security_opt: [no-new-privileges:true]` and `cap_drop: [ALL]`.
`tests/test_compose_security_config.py` is a regression test that
asserts these stay configured (so a future PR can't silently strip
them). No service mounts `docker.sock`.

### F. Supply-chain pinning (T6) — **VERY GOOD**

- All GitHub Actions are pinned to **40-character SHAs** with a
  `# vX.Y.Z` comment (e.g.
  `actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd  # v6.0.2`,
  `aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25`,
  `anthropics/claude-code-action@fefa07e9c665b7320f08c3b525980457f22f58aa`).
- Helm chart deps (Bitnami Redis 20.7.1, Bitnami Cassandra 12.1.4,
  kube-prometheus-stack 72.6.3) are **vendored as `.tgz`** in
  `charts/` with `Chart.lock`.
- A scheduled `security-scan.yml` runs Trivy on the filesystem weekly
  and is now a **hard gate** (per the file's comment "Promoted from
  soft-fail to hard gate on 2026-04-29 after two consecutive green runs").

### G. Internal-detail disclosure (T7) — **CLEAN**

- No internal corporate hostnames, no real customer references, no
  real Sentry DSNs (only the `https://...@sentry.io/...` placeholder).
- Email addresses found: `juniper-alerts@example.com` (placeholder)
  and `noreply@anthropic.com` (Co-Authored-By trailer; standard).
- The author email `paul.calnon@gmail.com` appears in `git log` —
  already public on every other Juniper repo; no incremental exposure.

### H. CI confused-deputy (T9) — **GOOD**

- `ci.yml` has `permissions: contents: read` at the workflow level.
- `claude.yml` requests broader perms (`contents: write`,
  `pull-requests: write`, `issues: write`, `id-token: write`) but
  guards every job behind an `if:` clause that requires `@claude` in
  comment / review / issue body — and runs only on
  `issue_comment` / `pull_request_review_comment` /
  `pull_request_review` / `issues`. **No `pull_request_target`**, no
  `workflow_run`. Forks cannot trigger it.
- `security-scan.yml` is `schedule` + `workflow_dispatch` only.
- `ANTHROPIC_API_KEY` is read from `secrets.ANTHROPIC_API_KEY` —
  expected to be an org-level secret. Worth confirming the secret is
  scoped so that public-repo workflows from forks cannot inherit it
  (GitHub default behavior since 2023 is to **not** expose secrets to
  fork PRs, so this is fine).

### I. Vendored blobs (T10) — **ACCEPTABLE**

- `k8s/helm/juniper/charts/*.tgz` are upstream Helm charts. SHA-pinned
  via `Chart.lock`. License-compatible (Bitnami / prometheus-community
  Apache-2.0).
- `.benchmarks/` and `.coverage` are working-directory artifacts and
  are gitignored (verified: `find` shows them only outside the tracked
  set).

### J. Documentation that describes prior weaknesses (T11) — **ACCEPTABLE, FLAG**

- `notes/SECURITY_REMEDIATION_PLAN.md`, `SOPS_AUDIT_AND_REMEDIATION_PLAN.md`,
  and parts of `CHANGELOG.md` describe historical vulnerabilities
  that *were fixed* (the SOPS-validation bypass, the predictable
  Grafana password, etc.). This is fine — the issues are closed —
  but note that going public makes these public, too. Consider:
  - Leaving them: shows responsiveness and rigor; a feature.
  - Sanitizing the AKIA-shaped example string in
    `SECURITY_REMEDIATION_PLAN.md` so future automated scanners
    don't keep flagging it (or add it to `.gitleaks.toml`'s allowlist).

### K. PII in commit metadata (T8) — **NO INCREMENTAL EXPOSURE**

- All author emails (`paul.calnon@gmail.com`, `Overtoad`,
  `cursoragent@cursor.com`, the bot accounts) already appear publicly
  in commits on the 7 sister repos. Nothing new is leaked by going
  public.

### Net assessment

There is **no critical (T1)** finding and the only T3 / T11 items are
either historical or already mitigated. The repo has been hardened with
clearly more attention than is typical for an "internal" deploy repo,
which makes the gap between its current visibility and its readiness
for public release unusually small.

---

## 6. Pre-Public-Release Remediation Punchlist

These are the items that should land **before** flipping the visibility
toggle. Listed in priority order.

### 6.1 Rotate any defaults that ever held a real value (BLOCKER, ~30 min)

- The `secrets/grafana_admin_password.txt` placeholder once contained
  the string `admin`. Even though the working tree is empty and the
  default fallback is removed, document in
  `docs/SECRETS_ONBOARDING.md` and the `make prepare-secrets` output
  that anyone deploying must populate this before exposing Grafana
  to a network. Already implied — make it loud.

### 6.2 Confirm `secrets.example/` placeholders are obviously fake (BLOCKER, ~10 min)

- Audit every file in `secrets.example/` and ensure each one's contents
  contain a literal "REPLACE_ME" / "CHANGE_BEFORE_PRODUCTION_USE"
  string. Current state: 9 of 10 placeholder files do so; one
  (`grafana_admin_password.txt`) reads `your-grafana-admin-password-here`,
  which is fine, but worth standardizing on the
  `CHANGE_BEFORE_PRODUCTION_USE` token to make the intent grep-able.

### 6.3 Re-run `gitleaks` against the full history (BLOCKER, ~15 min)

```bash
gitleaks detect --config .gitleaks.toml --log-opts="--all"
```

Expectation: only the `AKIAIOSFODNN7EXAMPLE` string from
`notes/SECURITY_REMEDIATION_PLAN.md` should fire. Resolution options:
either (a) replace the example with `AKIA...EXAMPLE` (drop the
realistic-looking middle), or (b) add a precise allowlist entry to
`.gitleaks.toml`. Option (a) is preferable because it doesn't
require allowlist drift.

### 6.4 Verify `ANTHROPIC_API_KEY` org-secret scoping (BLOCKER, ~5 min)

Once the repo is public, `claude.yml` runs in a public repo. Check the
GitHub org settings → Secrets → repository access for
`ANTHROPIC_API_KEY` and confirm:

- Public-repo workflows can read it (selected repos / all repos).
- Fork PRs **cannot** trigger `claude.yml` paths (verified via the
  `if:` guard — only `issue_comment` / `*_review*` events from the base
  repo, never `pull_request` or `pull_request_target`).

### 6.5 Decide on `notes/` policy (NON-BLOCKER, judgment call)

`notes/` contains plans, audits, and roadmaps that are useful to
contributors but reveal internal process detail. Recommend **leaving
them as-is** — they're a feature, not a bug, for a research-platform
repo. If desired, move the most internal-process-specific ones (e.g.
`THREAD_HANDOFF_PROCEDURE.md`, `WORKTREE_*_PROCEDURE.md`) into a
gitignored or separate `notes-internal/` subtree, but this is purely
optional and arguably loses signal for collaborators.

### 6.6 Update README to acknowledge public status (NON-BLOCKER, ~5 min)

Add a "Project status" / "Stability" note. The current README is
written assuming an internal audience; minor tone changes (e.g. an
explicit "Contributions welcome — see CONTRIBUTING.md", which would
need creating) would land it.

---

## 7. CI Changes Required Before Going Public

Most of the heavy lifting is **already done** — the CI was hardened
during the SOPS-audit and metric-auth work. The remaining items are
small.

### 7.1 No changes needed (already correct)

- ✅ Action SHA-pinning (all three workflows).
- ✅ Workflow-level `permissions: contents: read` on `ci.yml`.
- ✅ Concurrency groups + cancel-in-progress.
- ✅ `claude.yml` has narrow event triggers + `@claude` body guard.
- ✅ `security-scan.yml` is schedule/dispatch only and uses Trivy with
  `severity: HIGH,CRITICAL` as a hard gate.

### 7.2 Add a `gitleaks` job to `ci.yml` (RECOMMENDED, ~30 min)

Currently `gitleaks` is only enforced via the existing
`.gitleaks.toml` if a developer runs it locally; it is not part of
`ci.yml`. The peer repos (memory note
`project_gitleaks_node24_override_followup`) already run gitleaks
in CI with the Node24 override. Adopt the same pattern here:

```yaml
gitleaks:
  name: Gitleaks
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@<sha>  # v6.0.2
      with: { fetch-depth: 0 }
    - uses: gitleaks/gitleaks-action@<sha>
      env:
        FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"   # remove when upstream ships node24
        GITLEAKS_CONFIG: .gitleaks.toml
```

This is the same pattern already in use across the 6 other repos and
it closes the only meaningful CI gap.

### 7.3 Wire `gitleaks` into the `required-checks` quality gate

After 7.2, add `gitleaks` to the `needs:` list and the result-checking
script of `required-checks` so a leak blocks merge.

### 7.4 No-op verification: cross-repo `docs-full-check.yml` will start working

`juniper-ml/.github/workflows/docs-full-check.yml` already attempts to
clone `juniper-deploy` (line 56 of its `ECOSYSTEM_REPOS` list) but
swallows the failure with
`|| echo "WARNING: Failed to clone $repo (may not exist or be private)"`.
**No action needed here** — once `juniper-deploy` is public, the clone
just succeeds, and the cross-repo link checks light up automatically.
Worth noting and worth re-running the workflow manually after the flip
to confirm there are no broken links from `juniper-deploy` → siblings.

### 7.5 Optional: enable Dependabot for Helm + GitHub Actions ecosystems

`.github/dependabot.yml` already exists. Confirm it covers:

- `package-ecosystem: github-actions` (so action SHA bumps land
  automatically),
- `package-ecosystem: docker` against the build contexts (so base
  image CVEs surface),
- and consider adding `helm` once Dependabot's experimental Helm
  support is stable enough.

---

## 8. The PyPI Question

**Recommendation: do not publish to PyPI.** The reasoning:

1. **There is nothing to install.** `juniper-deploy` is a Docker
   Compose file, a Makefile, a Helm chart, and shell scripts.
   PyPI is for Python packages; `pyproject.toml` doesn't even declare
   `[project]`.
2. **`pip install juniper-deploy` would not give a user a working
   stack.** They would still need Docker, Compose v2 ≥ 2.20, the four
   sibling source repos cloned alongside, and `make` — none of which
   pip can deliver.
3. **Discoverability is already adequate via GitHub.** The repo's
   value is its `git clone`-able state, not its
   `pip install`-able state.
4. **PyPI reservation is fine if you want the name.** A *stub*
   package (one `juniper_deploy/__init__.py` that prints "this is a
   git-only project, see https://github.com/...") would prevent
   typo-squatting but should be done **only** if name protection is
   actually a concern. For an unambiguous, project-namespaced name,
   it usually isn't.

---

## 9. Bundling Into `pip install juniper-ml[all]`

**Recommendation: do not bundle.** Three reasons:

1. **Different artifact type.** `juniper-ml[all]` already pulls in
   exactly the Python wheels a researcher needs to use the platform
   from Python (`juniper-data-client`, `juniper-cascor-client`,
   `juniper-cascor-worker`). Bundling a Helm chart + a docker-compose
   tree into a `pip install` would put non-Python artifacts in a Python
   site-packages directory, where they cannot be invoked directly.
2. **Different lifecycle.** `juniper-deploy` versions track
   *infrastructure* changes (compose schema, profile additions, k8s
   chart bumps), not API surface. Tying its release cadence to
   `juniper-ml`'s would either over-release `juniper-ml` or
   under-release `juniper-deploy`.
3. **Different prerequisites.** `juniper-ml` users may be running
   inside a Jupyter notebook or a CI test runner with no Docker
   daemon. Auto-installing a 70MB+ docker-compose-and-Helm tree they
   cannot use would be hostile.

The right pointer is **README + DOCUMENTATION_OVERVIEW**: have
`juniper-ml`'s README direct people who want a running stack to
`git clone juniper-deploy` and `make demo`. (`juniper-ml/README.md`
already does this on line 29.)

---

## 10. Benefits of Going Public

| Benefit | Severity / Value |
|---------|------------------|
| **Closes the discoverability hole** — every public sister repo points at `juniper-deploy` but external readers hit a 404 today. | High |
| **Unlocks `docs-full-check.yml`** in `juniper-ml` (currently warns instead of validating cross-repo links into juniper-deploy). | Medium |
| **Enables Dependabot ecosystem coverage** — Bitnami/kube-prometheus-stack chart bumps and base image bumps become visible to community contributors. | Medium |
| **Enables `make demo` as the project's pitch** — a single command that boots the spiral-CasCor demo is a strong story for collaborators / talks / papers. | High (if outreach is a goal) |
| **Permits citing the repo by URL** in papers, talks, bug reports. | Medium |
| **Symmetrizes with the rest of the ecosystem** — having one private repo in an otherwise-public stack creates ongoing maintenance friction (auth tokens for cross-repo CI, separate access lists). | Medium |
| **No marginal cost** to maintenance — already CI-gated, already Trivy-scanned, already SOPS-encrypted, already license-declared (MIT). | — |

---

## 11. Risks of Going Public

| Risk | Likelihood | Severity | Mitigation |
|------|-----------:|---------:|------------|
| Someone deploys the stack with placeholder secrets and gets popped. | Medium | High | The `secrets.example/` placeholders are obvious; default `BIND_HOST=127.0.0.1`; Grafana / SMTP secrets must be supplied (no fallback). Add a **prominent** warning to README + `make prepare-secrets`. |
| Someone copies the SOPS age **public** key and we lose track of where it's used. | Low | Low | Public keys are not sensitive; this is fine. |
| Drive-by issues / spam PRs raise maintenance load. | Medium | Low | `CODEOWNERS` is set; `claude.yml` provides triage assistance; Dependabot reviewers are already configured. |
| Someone reads `notes/SECURITY_REMEDIATION_PLAN.md` and reverse-engineers an exploit against an out-of-date deployment. | Low | Low–Medium | The vulnerability is closed; describe current state, optionally redact the exact bypass example. |
| `claude.yml` consumes API budget from spam mentions in public issues. | Medium | Low | The `if:` guard already requires `@claude`; rate-limit at the org level if needed. |
| External user's PR introduces a regression in container hardening. | Low | Medium | `tests/test_compose_security_config.py` already regresses; add a CI badge so it's visible. |

The dominant risk is **(1)** — a downstream operator deploying the stack
without rotating placeholders. This is a *documentation* problem more
than a security one, and the existing `docs/SECRETS_ONBOARDING.md`
already addresses it; making the warning louder closes the loop.

---

## 12. Final Recommendation

**Take `juniper-deploy` public**, but do these four things first
(estimated total effort: **2–3 hours**):

1. Run `gitleaks detect --log-opts="--all"` and act on any new findings
   (likely: drop `AKIAIOSFODNN7EXAMPLE` from
   `notes/SECURITY_REMEDIATION_PLAN.md`).
2. Add the **gitleaks** job to `ci.yml` and wire it into
   `required-checks` (mirroring the 6 sister repos).
3. Confirm the `ANTHROPIC_API_KEY` org-secret access scope is what you
   expect on a public repo.
4. Add a top-of-README "Before deploying" callout that lists the four
   placeholder files in `secrets/` that **must** be populated, plus a
   pointer to `docs/SECRETS_ONBOARDING.md`.

**Do not publish to PyPI**, and **do not bundle into
`juniper-ml[all]`** — the artifact is fundamentally not a Python
package, and bundling would put non-Python files in a site-packages
tree where they cannot be used. Continue to advertise the project the
way `juniper-ml/README.md` already does: a one-line pointer to
`git clone juniper-deploy && make demo`.

Once public:

- Re-run `juniper-ml/.github/workflows/docs-full-check.yml` manually
  and address any cross-repo link breakage.
- Consider promoting `juniper-deploy` from `pcalnon/juniper-deploy` to
  the same conventions as the rest of the ecosystem (CODEOWNERS,
  branch protection on `main`, signed-tag releases via
  `release-please` or equivalent — though this is hygiene, not a
  blocker for going public).

The repo is in unusually good shape for the transition; the
remediation list is short and bounded, and the upside (a working
`make demo` that any prospective collaborator can run in under five
minutes) is substantial.
