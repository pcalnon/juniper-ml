# Juniper Stack — Security / Vulnerability Audit Plan (Containerized)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-07-02

---

## 1. Purpose & authorization

This is the **security / vulnerability** companion to
[`JUNIPER_STACK_INTERACTIVE_UX_AUDIT_PLAN_2026-07-02.md`](JUNIPER_STACK_INTERACTIVE_UX_AUDIT_PLAN_2026-07-02.md).
The interactive-UX plan covers dimensions D1–D4 (functionality/UX/docs/output/correctness); this plan is **dimension D5 —
vulnerabilities in architecture and implementation**. It is an **authorized defensive audit of the platform owner's own stack**
(owner: Paul Calnon / `@pcalnon`, sole CODEOWNER), scoped to the **containerized** deployment (`juniper-deploy` compose), for the
purpose of hardening. It enumerates weaknesses and defines **verification steps phrased defensively** ("confirm X rejects Y",
"confirm the secure default"). It is not an offensive playbook: it contains no weaponized payloads or exploit recipes.

**Division of labor (this effort).** The plan, the attack-surface enumeration, the hardening checklist, the defensive
verification steps, and the read-only grounded findings below were produced with Fable. **Execution-phase steps that are
genuinely dual-use** — actively exploiting a live service, firing payloads to prove reachability, authoring PoCs, or deliberate
fault/DoS injection — are **handed off to Opus** and enumerated granularly in §8. Everything a static/read-only defensive audit
can establish is done here; only the active-confirmation steps are deferred.

## 2. Scope

- **In scope:** the containerized services (`juniper-canopy`, `juniper-cascor`, `juniper-cascor-worker` ×2,
  `juniper-data`, `juniper-recurrence`, `juniper-redis`) and the observability profile (prometheus, grafana, alertmanager),
  plus their auth, secrets, transport, container, and dependency posture. Trust boundaries in §3.
- **Out of scope:** on-host (non-containerized) execution; formal pen-test engagement rules; third-party image internals beyond
  version/CVE posture; the `juniper-deploy/k8s/` manifests (not the running stack).
- **Severity scale (this plan):** Critical / High / Medium / Low — aligned with the ecosystem baseline
  `juniper-ml/notes/legacy/SECURITY_AUDIT_PLAN.md` (24 findings) so results diff cleanly against it. A **containerized-exposure
  modifier** applies: a weakness on an `internal:true` network or a loopback-bound port is de-rated relative to the same
  weakness on a host-exposed interface.
- **Evidence bar (anti-hallucination):** every finding carries implementing `file:line`; every *live* claim carries an observed
  response/log/inspect output. The plan and its eventual report both pass independent multi-agent validation (§7 of the UX plan;
  applied here in §9). Findings below are **grounded candidates** from a read-only recon pass and are re-verified in SP1.

## 3. Trust boundaries & threat model (STRIDE-lite)

| #   | Boundary                                                            | Primary threats                                  | Where verified           |
|-----|---------------------------------------------------------------------|--------------------------------------------------|--------------------------|
| B1  | Internet/LAN → canopy `:8050` (host-published, loopback by default) | Spoofing, Tampering, DoS                         | §4 IDA, TRANS, NAT       |
| B2  | Browser → canopy `/api/*`, `/ws/*` control surface                  | CSRF, spoofed Origin, session theft              | §4 IDA (browser-control) |
| B3  | canopy → cascor / data / recurrence (`http://`, `ws://`, internal)  | Cleartext creds, MITM on-bridge, SSRF            | §4 TRANS, INJ            |
| B4  | worker → cascor `/ws/v1/workers`                                    | Token theft, unauth worker, replay               | §4 IDA (WS)              |
| B5  | Prometheus → each `/metrics`                                        | Metrics/PII disclosure, allowlist bypass         | §4 IDA (metrics), NAT    |
| B6  | Operator → grafana/prometheus/alertmanager                          | Default creds, weak admin auth                   | §4 IDA, SECRET           |
| B7  | Secrets at rest (SOPS) + in transit (compose secrets, `_FILE`)      | Key compromise, fail-open provisioning           | §4 SECRET                |
| B8  | Host → containers (privilege, rootfs, caps)                         | Container escape, privilege escalation           | §4 CONT                  |
| B9  | Docker bridge NAT ↔ IP-keyed controls                               | Rate-limit/allowlist evasion, self-DoS           | §4 NAT                   |
| B10 | Untrusted request/file/URL input → sinks                            | SSRF, deserialization, injection, path traversal | §4 INJ                   |

## 4. Weakness-class checklist (grounded)

Each class: what to verify (defensive), the secure state, and the grounded candidate findings from recon. Finding IDs are
`SEC-Fnn`. Severity is calibrated for the **containerized** posture (loopback-bound, internal networks).

### 4.1 IDA — identity & access control

**Verify:** auth enable-condition per service; fail-open vs fail-closed; exempt-path correctness; browser Origin+CSRF gate; WS
worker/control auth; metrics IP allowlist; rate-limit defaults; constant-time key comparison.

- **SEC-F01 (High) — fail-open auth chain, secret-provisioning-coupled.** All four HTTP services enable auth only when
  `len(api_keys) > 0`; when unset, `validate()`→True / `__call__`→None (canopy `src/security.py:48,64-65,84-85`; cascor
  `src/api/security.py:33,49-50,69-70`; data `.../api/security.py:55,71-72,100-101`; recurrence via
  `juniper_service_core/security.py:40,56-57,76-77`). `prepare_secrets.bash` maps the literal `CHANGE_BEFORE_PRODUCTION_USE`
  placeholder to an **empty** secret file (`:107-110`), and an empty key file ⇒ auth disabled (compose comment
  `docker-compose.yml:904-905`). **Net: a missing/undecryptable SOPS bundle silently drops the whole stack into fail-open.**
  Verify: with no/placeholder secret, protected routes must NOT be reachable — or the services must **fail closed** (refuse to
  start) instead. Cascor WS worker+control also fail-open when `api_keys` empty (`src/api/websocket/manager.py:45-50`).
- **SEC-F02 (Medium) — Grafana/Alertmanager default to placeholder credentials.** Compose secret defaults for
  `grafana_admin_password` and `alertmanager_smtp_password` resolve to `./secrets.example/*.txt` = `CHANGE_BEFORE_PRODUCTION_USE`
  (`docker-compose.yml:936-937,944-945`), while `prepare_secrets.bash` writes the real value to `./secrets/…` — a path compose
  does not read unless the operator exports the `*_FILE` override. The Grafana `.env.secrets.example:33-34` doc **contradicts**
  the code default. Net: default Grafana admin login is a publicly-known string (loopback `:3001`) unless overridden. Verify the
  effective mounted value; align doc↔compose; make rotation loud in `prepare_secrets`.
- **SEC-F03 (Medium) — inconsistent rate-limit + worker rate-limit off by default.** `rate_limit_enabled` = canopy False
  (`settings.py:293`), cascor False (`settings.py:276`), data True, recurrence True; cascor worker connection rate-limiter
  `worker_rate_limit_enabled=False` (`settings.py:351`). Verify intended posture per service; document the divergence.
- **SEC-F04 (Low) — recurrence API docs reachable with auth on.** data (`app.py:74`), cascor (`app.py:425,431-433`), and canopy
  (`main.py:348,355-357`) all auto-disable `/docs`,`/redoc`,`/openapi.json` when auth is enabled; **only juniper-recurrence** leaves
  them permanently exposed (its `juniper_service_core.create_app` at `juniper_service_core/app.py:45` sets no `docs_url`). Verify
  whether recurrence docs should be gated in prod. (Validation corrected the original "only juniper-data gates" over-scope.)
- **SEC-F05 (Low, verified strength) — constant-time key comparison (SEC-01 timing side-channel).** data compares constant-time
  over the full key list (`api/security.py:80-84`), canopy CSRF uses `hmac.compare_digest` (`csrf.py:53-72`), and cascor uses
  `any(hmac.compare_digest(...))` (`api/security.py:53`). **CONFIRMED constant-time (HO-8):** empirical wrong-vs-near-miss delta
  1.49%, under the noise floor — no gross byte-position signal. Only theoretical residual: the `any()` short-circuit could leak
  key-slot/count under a multi-key config (never key content). (Requirement `JR-ML-SEC-003`.)
- **SEC-F22 (Medium; CONFIRMED live, HO-6) — browser-control gate bypassable from any in-network foothold.** `/api/train/*` are
  key-exempt and gated only by an Origin allowlist (a **case-insensitive string compare**, `ws_security.py:16-36`) + a CSRF token
  that `/api/csrf` mints **anonymously** for a same-origin/no-Origin caller (`main.py:485-519`). A non-loopback in-network client
  (demonstrated: a sidecar at `172.23.0.5`) can mint a token and present a **spoofed `Origin: http://127.0.0.1:8050`** to clear
  `require_browser_control_auth` (`security.py:308-368`) and drive the full training-control surface (start/pause/resume/stop/
  reset) **with no real credential**. Two negative controls (no-Origin → 403, no-CSRF → 403) prove the gate is genuinely active,
  so this is not the SEC-F01 fail-open case — it is a design residual (auth design §7.3) now confirmed exploitable. The **only**
  effective control today is the loopback bind. Remediation: require a real per-session credential (authenticated-cookie-bound
  token, or force the server `X-API-Key` via a trusted proxy) — not a spoofable Origin + anonymous CSRF; keep the control surface
  loopback-bound; never expose it on a routable interface without a fronting authenticating proxy; document the in-network trust.
- **Good-news (document as verified, with one caveat):** `MetricsAuthMiddleware` is **fail-closed** on absent/unparseable client
  IP and fail-loud on a bad allowlist (`juniper_observability/middleware/metrics_auth.py:65-84,153-184`); worker `X-API-Key` is
  validated against the same accept-list as REST and the server assigns worker IDs (does not trust client-proposed IDs). Caveat:
  the browser-control gate is fail-closed on a *missing/disallowed* Origin (`src/security.py:308-368`) but its allowlist is a
  spoofable string compare — see **SEC-F22** — so it is not an authenticator against a non-browser client.

### 4.2 SECRET — secret handling

**Verify:** SOPS key hygiene; provisioning completeness; no placeholder-as-real; no secret in logs/response/layers; `_FILE`
indirection honored everywhere.

- **SEC-F06 (Medium) — `cascor_sentry_dsn` never provisioned.** Absent from `prepare_secrets.bash` MAPPINGS (`:51-59`); compose
  defaults to the placeholder (`:930-931`). Benign (Sentry stays off) but is a provisioning gap; verify intended.
- **SEC-F07 (carry-forward, Critical per prior audit) — single shared SOPS age key, no env separation; version drift.**
  `juniper-deploy/notes/SOPS_AUDIT_AND_REMEDIATION_PLAN.md` (SOPS-002/008; Phases 4–5 **deferred**). Verify current key hygiene,
  re-encryption, and per-repo pre-commit/gitleaks/`.gitattributes` propagation (only juniper-deploy confirmed gitleaks-in-CI).
- **Good-news (document as verified):** no secret value leaks in logs, health, or error responses (recon found only
  presence-booleans logged; health returns `{status,version,service,git_sha,build_date}`); no `/config`/`/debug`/`/env`
  endpoint; no secret baked into any image layer (build ARGs are provenance only; `.dockerignore` excludes `.env`/`.git`).

### 4.3 INJ — injection / SSRF / deserialization / path / command

**Verify:** untrusted-input validation at every entrypoint; SSRF host/scheme/redirect controls; deserialization safety;
server-side value bounds; parameterized queries.

- **SEC-F08 (Medium) — SSRF in `/api/dataset/import-url`.** Handler `juniper-canopy/src/main.py:1345-1401`: scheme allowlist
  (http/https), 10 s timeout, 10 MB cap, **API-key-gated**, and reachable **only when `backend_type=="demo"`** (else 400) — so in
  the running full profile it is inert. But it has **no host/IP validation** (loopback / link-local / `169.254.169.254` /
  RFC-1918 all reachable), `follow_redirects=True` (public→internal 302 bypass), a post-buffering size cap, and its
  `dataset_import_url_enabled` gate **is not a defined Settings field** — and because `Settings` uses `extra="ignore"`, the
  documented off-switch is **entirely non-functional** (cannot be set even via env var), not merely defaulted-on. Do **not** read
  "demo-only" as benign: canopy silently **falls back to demo mode** when a configured cascor backend is unreachable at startup
  (`main.py:280-286`), and the API-key gate is a no-op when no keys are set (SEC-F01) — so the SSRF surface can appear in a
  degraded prod bring-up, and demo configs get copied. **SP2 (read-only, done): confirmed no allowlist/redirect re-validation;
  active reachability + redirect-bypass proof → Opus HO-1/HO-7.** Harden: block private/link-local/loopback, re-validate per
  redirect hop or disable redirects, stream with a pre-check, and make the enable-gate a real setting defaulting off.
  **HO-1/HO-7 outcome (§5.2): PARTIAL — latent, not live.** The endpoint is currently **dead**: `DemoBackend` never defines
  `import_dataset`, so the `hasattr` guard (`main.py:1360`) returns **501 before any fetch** (verified: internal/loopback/
  link-local/external/`file://` all 501, no packet emitted). The SSRF sink itself is unguarded and **re-arms the moment the (dead)
  import feature is fixed** — harden the sink *first*. The off-switch is confirmed non-functional (`extra="ignore"` drops the
  flag). Note the **dead-feature seam** (import-url + import-file both 501 in demo, masked by mocked tests) — a correctness defect
  too. Live severity Low (no egress); latent Medium.
- **SEC-F09 (Low; DEFENSE VERIFIED-STRONG) — deserialization is hardened.** HDF5 snapshot pickle is routed through a
  fail-closed allowlist unpickler `_SnapshotRestrictedUnpickler` (SEC-11, `snapshot_serializer.py:59-79`, called `:1103`; a second
  fail-closed `RestrictedUnpickler` also exists at `cascade_correlation.py:415`); `torch.load(..., weights_only=True)`
  (`utils/utils.py:102`); `np.load(allow_pickle=False)` **explicitly in recurrence** (`model.py:330`, `data.py:53`) while
  juniper-data uses a **bare `np.load`** (`datasets.py:710`) that is safe only by numpy's since-1.16.3 default (add the explicit
  kwarg for defense-in-depth); `yaml.safe_load` throughout; no `os.system`/`shell=True`/builtin `eval`/`exec` on request data in
  production. Document as a strength; SP2 re-confirms the allowlist boundary statically (active escape attempt → Opus HO-4).
- **SEC-F10 (Low) — canopy set-params has no local bounds; cascor's default path DOES bound (narrow WS residual).**
  canopy `SetParamsRequest` uses bare `int|None`/`float|None` with no `Field(ge=/le=)` (`main.py:3100-3149`) and forwards to the
  backend without clamping (`backend.apply_params(**backend_updates)`, `main.py:3250`). **But cascor's default REST path
  `PATCH /training/params` enforces comprehensive server-side bounds** via pydantic `TrainingParamUpdateRequest`/`TrainingParams`
  in `juniper-cascor/src/api/models/training.py` (e.g. `learning_rate gt=0,le=10.0` `:49`, `candidate_pool_size ge=1,le=256`
  `:52`, `max_hidden_units ge=1,le=10_000` `:53`, `patience ge=1,le=100_000` `:55`, ~15 more), plus a key whitelist in
  `_apply_params_unlocked` (`juniper-cascor/src/api/lifecycle/manager.py:3093`). **The genuine residual is only the opt-in WS
  `set_params` path** (`control_stream.py`) which bypasses that pydantic layer — validated then by the whitelist + candidate-pool
  check alone. Low severity: `use_websocket_set_params` defaults **False** (REST default, WS falls back to REST). Verify and add
  matching `Field` bounds to the canopy request model and the WS path. (Validation corrected the original "cascor has no numeric
  bounds" over-scope + wrong file citations; fault-injection proof → Opus HO-5.)
  **HO-5 outcome (§5.2): CONFIRMED, refined.** START path (`TrainingParams`) is fully bounded (422 on out-of-range). Two live
  residuals: (a) runtime `PATCH /v1/training/params` binds a *different* model `TrainingParamUpdateRequest`
  (`models/training.py:200-268`) with **lower bounds only** — a huge `max_hidden_units` is accepted with a live network; (b) WS
  `set_params` (`control_stream.py:373-376`) bypasses pydantic entirely. **Correction:** `use_websocket_set_params` does not exist
  in cascor; `/ws/control` is **enabled by default** (`disable_ws_control_endpoint=False`), so both surfaces are live (WS is
  auth-gated but range-unvalidated). Fix = mirror `TrainingParams` `le=` ceilings onto `TrainingParamUpdateRequest` + route WS
  `set_params` through the same model.
- **SEC-F11 (Low) — dataset-id traversal guard not uniform across stores.** `_validate_dataset_id` is wired into LocalFS only
  (`storage/local_fs.py:36,93`, with a second `is_relative_to` containment check `:96`). The **postgres** store builds a real
  on-disk artifact path from the id (`postgres_store._artifact_file:136-138`) with **no store-layer guard** — mitigated *solely*
  by the FastAPI `{dataset_id}` route converter (can't contain `/`); the **redis** store uses opaque exact-match keys (`:84-90`,
  genuinely low-risk). SQL is parameterized. Verify the guard is uniform at the store layer (defense-in-depth), especially the
  postgres path.
- **Good-news:** error handling is opaque (`{"error":"Internal server error","error_id":<uuid>}`, tracebacks logged
  server-side only); Postgres queries are parameterized; no archive/zip extraction on uploads; CSV import is bounded
  (10 MB/50k rows/100 feats).

### 4.4 TRANS — transport & headers

**Verify:** TLS posture; security headers; CORS; cookie flags.

- **SEC-F12 (Low, by-design-external) — no in-stack TLS; inter-service creds plaintext.** No TLS terminator in compose; TLS is
  assumed at an external proxy (HSTS emitted only behind `X-Forwarded-Proto: https` `middleware.py:51`; cookie `https_only=False`
  `main.py:392`). `X-API-Key`/worker token traverse the internal bridges in cleartext — mitigated by `backend`/`data` being
  `internal:true`, not encrypted. Verify the deployment contract documents the required fronting TLS proxy.
- **SEC-F13 (Low) — session cookie lacks Secure; ephemeral per-process session secret.** `canopy_session` is `SameSite=Strict`,
  HttpOnly, but `https_only=False` (`main.py:392`); `session_secret_key` defaults `""` → `secrets.token_urlsafe(32)` per process
  (`main.py:385`), so CSRF/session tokens don't survive a restart and aren't shared across replicas. Verify a persistent secret
  for any multi-replica/persistent deployment; set Secure behind TLS.
- **SEC-F14 (Low) — CSP allows `script-src 'unsafe-inline'`.** Required by Dash, but materially weakens XSS defense
  (`canopy_constants.py:387`). Document the residual; consider nonce/hashes if Dash permits. CORS default `[]` (same-origin only)
  and the other security headers (nosniff, `X-Frame-Options: DENY`, Referrer-Policy, Permissions-Policy) are present — document
  as strengths.

### 4.5 CONT — container hardening

**Verify:** non-root; capability drop; privilege; rootfs; base-image pinning; parity across all services.

- **SEC-F15 (Medium) — redis container unhardened.** The 5 first-party app containers run non-root (`USER juniper`), with
  `cap_drop:[ALL]`, `no-new-privileges`, `Privileged:false` (compose `:144-147,195-198,287-290,501-504,558-561`). **redis has
  none** of these (`:859-870`). Also stack-wide: `ReadonlyRootfs=false` for all, no `tmpfs`/`pids_limit`/seccomp/apparmor beyond
  default, and the `test-runner` (test profile) runs as **root** (`Dockerfile.test:22-31`). Verify/extend hardening to redis and
  consider read-only rootfs + `pids_limit`.
- **SEC-F16 (Low) — no image digest pinning.** First-party images are `:latest`; third-party are tag-pinned (not digest):
  `prom/prometheus:v3.10.0`, `prom/alertmanager:v0.27.0`, `grafana/grafana:12.4.0`, `redis:7.4-alpine`. Verify digest pinning for
  supply-chain integrity.
- **Good-news:** default host binding is `${BIND_HOST:-127.0.0.1}` (loopback); `backend`/`data` networks are `internal:true`;
  no secrets in image layers. Note the `.env.example` `BIND_HOST=0.0.0.0` escape hatch exposes every published port at once —
  document as a deployment-hardening checkpoint.

### 4.6 DEP — dependency / CVE posture

**Verify:** pip-audit coverage + consistency; CVE ignore-list justification; version floors; lockfiles; base-image updates.

- **SEC-F17 (Medium) — torch security floor not enforced in app/worker packages.** CVE-2025-3001 (`lstm_cell` memory corruption,
  fixed 2.10.0) floor `torch>=2.10.0` is declared **only** in the two model subpackages (`juniper-cascor-model/pyproject.toml`,
  `juniper-recurrence-model/pyproject.toml`); the app/worker packages declare `torch>=2.0.0` — canopy `pyproject.toml:186`,
  cascor `:87`, cascor-worker `:43`. Installed wheels are current (live-verified **2.12.0+cpu** in cascor/worker/canopy — the risk
  is latent, not live), but the declared minimum permits vulnerable 2.0–2.9. **cascor-worker's `>=2.0.0` is the sharpest instance
  (an unconditional main dep)**; canopy `[demo]` and cascor `[ml]` sit behind opt-in extras. Raise the floor to `>=2.10.0`
  everywhere torch is declared.
- **SEC-F18 (Medium) — pip-audit config inconsistent; recurrence has partial scanning + no lockfile.** The CVE ignore-list
  (torch no-fix advisories, quarterly re-eval) lives in cascor `ci.yml:695-711` **and the kept-in-sync copy in cascor-worker
  `ci.yml:599-613`**; cascor `security-scan.yml:53` runs `--strict` **without** the ignore list (would go red on the same
  advisories); canopy runs pip-audit **without `--strict`**. **juniper-recurrence DOES run pip-audit** (`security-scan.yml:62`,
  `--strict`, 3-package matrix) **and bandit** (pre-commit, CI-enforced) — but has **no CodeQL and no lockfile** (Dockerfile
  installs unpinned from PyPI); deploy has no CodeQL. Dependabot covers `pip` + `github-actions` but **not the `docker` ecosystem**
  → base images are not auto-updated. Verify/normalize the pip-audit flags; add a recurrence lockfile + CodeQL; add docker to
  Dependabot. (Validation corrected the original "ignore-list only in cascor" + "recurrence has no pip-audit/bandit" over-claims.
  Cross-refs: `CI_VALIDATION_FINDINGS_2026-04-29.md`, `JR-DAT-OBS-001` "scanners must hard-fail, not `|| true`".)

### 4.7 NAT — Docker-NAT defeats IP-keyed controls

- **SEC-F19 (Medium, architectural) — every IP-keyed control collapses on the bridge gateway / trusts the whole subnet.** Seven
  controls key on the raw socket peer and **none honor `X-Forwarded-For`**: canopy WS per-IP cap (`settings.py:141`,
  `websocket_manager.py:366,381`), cascor WS per-IP cap (`settings.py:139`), cascor handshake cooldown/blocklist, cascor worker
  per-IP limit, canopy + cascor HTTP rate limiters, and the metrics IP allowlist. Docker DNAT makes every host browser client
  present as the frontend bridge gateway `172.19.0.1`, so per-IP caps + rate buckets are **shared across all users** (one client
  exhausts the cap-of-5 for everyone — the same self-DoS seen live in UX finding F-A), and the metrics-allowlist workaround
  widens `*_METRICS_TRUSTED_IPS` to the **entire** bridge space (`.env.observability:45-47`) so any container can scrape
  `/metrics`. Verify: adopt `X-Forwarded-For` handling behind a trusted proxy, or move rate-limiting/allowlisting to a layer that
  sees real client identity. This is the highest-value *architectural* security item and directly intersects the UX plan's F-A.

### 4.8 OBS-SEC / DOS — logging, exposure, availability

- **SEC-F20 (Medium, cross-ref UX) — single-worker self-call starvation is an availability weakness.** The UX audit's F-C/F-D/F-F
  (one uvicorn worker + synchronous authenticated in-process self-calls) is also a DoS-surface: a slow/last self-call starves the
  sole worker. Verify worker count + async the self-calls. (See UX plan §11.1.)
- **SEC-F21 (carry-forward, Low) — event-loop-freeze deny-list never written; no branch-protection required-checks.** The
  async-route audit shipped and enforces a CI lane, but the project-internal blocking-primitive deny-list (`util/check_async_
  routes.py`) was never written, and **no repo has `required_status_checks` configured** (juniper-data-client has no branch
  protection at all). Verify enforcement is actually required, not just present. (`FOLLOWUP_ASYNC_ROUTE_AUDIT.md`,
  `STATUS_FOLLOWUP_ASYNC_ROUTE_AUDIT_2026-05-19.md`.)

## 5. Grounded candidate findings — severity summary

| ID | Sev | Class | One-line | Containerized bound |
| --- | --- | --- | --- | --- |
| SEC-F01 | High | IDA | Fail-open auth; empty/placeholder secret ⇒ whole stack open — **CONFIRMED live (HO-2)** | loopback-bound, but stack-wide |
| SEC-F07 | High (carry) | SECRET | Single shared SOPS age key, no env sep; drift; Phases 4–5 deferred | at-rest |
| SEC-F22 | Medium | IDA | **NEW: browser-control gate bypass from in-network** (spoofed Origin + anon CSRF → full training-control) — **CONFIRMED live (HO-6)** | loopback-bind is the only guard |
| SEC-F19 | Medium | NAT | IP-keyed caps/allowlists defeated by Docker NAT (self-DoS; dynamic subnet outside allowlist) — **CONFIRMED live (HO-3)** | bridge-wide |
| SEC-F08 | Med (latent) / Low (live) | INJ | import-url SSRF sink unguarded but **dead behind a 501 guard** (re-arms on feature fix); off-switch non-functional — **HO-1/HO-7 latent** | demo-only; latent |
| SEC-F17 | Medium | DEP | torch `>=2.10.0` floor absent in app/worker packages (installed 2.12.0 → latent) | declared-min risk |
| SEC-F18 | Medium | DEP | pip-audit flags inconsistent; recurrence no lockfile/CodeQL; no docker Dependabot | CI-time |
| SEC-F02 | Medium | IDA | Grafana/Alertmanager default placeholder creds; doc↔compose mismatch | loopback `:3001` |
| SEC-F03 | Medium | IDA | Rate-limit + worker limiter inconsistent/off | per-service |
| SEC-F15 | Medium | CONT | redis unhardened; no readonly-rootfs/pids anywhere; test-runner root | internal net |
| SEC-F20 | Medium | DOS | Single-worker self-call starvation (UX cross-ref) | loopback |
| SEC-F06 | Medium | SECRET | `cascor_sentry_dsn` never provisioned | benign |
| SEC-F04/05/10/11/12/13/14/16/21 | Low | mixed | recurrence-docs-exempt, **F05 constant-time CONFIRMED**, **F10 PATCH-upper-bound + WS-pydantic-bypass (refined, HO-5)**, store-guard uniformity, TLS-external, cookie-Secure, CSP-inline, digest-pin, async-denylist | mostly de-rated |

Two items are **verified strengths** to record affirmatively (not findings): deserialization hardening (SEC-F09) and
no-secret-leakage / MetricsAuth fail-closed (§4.1/§4.2 good-news).

### 5.1 Validation outcome (SP1)

These findings passed an independent three-agent anti-hallucination pass (two source re-verifiers that did not author the
claims, one adversarial read-only live prober). Outcome: **no finding was refuted**; SEC-F01/F02/F03/F05/F06/F08/F11/F12/F13/F14/
F15/F17 were confirmed at source, and the live prober confirmed SEC-F08 inert-in-full-profile (401 auth gate before the 400
demo gate), SEC-F15 container hardening, torch **2.12.0+cpu** installed, the `172.19.0.1` bridge gateway + no `X-Forwarded-For`
trust (F19), the placeholder-vs-real secret bytes (F02), and the lone `-dirty` canopy image. Validation **corrected three
over-scoped claims** (now fixed above): **SEC-F04** (docs-under-auth is disabled by data/cascor/canopy — only recurrence is
exposed, not "only data gates"); **SEC-F10** (cascor's default REST path *does* enforce comprehensive pydantic bounds — the
residual is only the opt-in WS path; downgraded Medium→Low, citations fixed); **SEC-F18** (the CVE ignore-list is in cascor
*and* cascor-worker, and recurrence *does* run pip-audit + bandit — only CodeQL + a lockfile are missing). SEC-F09's data-side
`np.load` wording was tightened (safe-by-default, not explicit). SP2′ (the §8 Opus items) is **now complete** — see §5.2.

### 5.2 Live confirmation outcomes (SP2′ — Opus, isolated stack, 2026-07-02)

The §8 hand-off register (HO-1…HO-8) was executed by **Opus** against an **isolated throwaway copy** of the stack (compose
project `secaudit`, bound to loopback `127.0.0.2`, container-name-namespaced; the live 127.0.0.1 stack was untouched throughout
and the isolated stack was torn down after). Three configs were used: full+empty-secrets (fail-open), canopy internal-demo (SSRF),
and full+real-secrets (auth-on). The running image `git_sha 381ecd5` matched source HEAD (#417), so these are current-code results.

| HO | Finding | Verdict | Key evidence |
| --- | --- | --- | --- |
| HO-2 | SEC-F01 fail-open auth | **CONFIRMED (live)** | Empty secrets → cascor `/v1/training/status`, canopy `/api/status`, data `/v1/datasets`, recurrence `/v1/training/status` all **200 with no key**; live auth-on control = 401. Full source chain verified. |
| HO-1/HO-7 | SEC-F08 SSRF | **PARTIAL — latent, not live** | Sink is real + unguarded (no host/IP validation; `follow_redirects=True`, no per-hop check), but the endpoint returns **501 before any fetch** — `DemoBackend` never defines `import_dataset`, so the `hasattr` guard (`main.py:1360`) blocks every request. Off-switch confirmed non-functional (`extra="ignore"` drops the flag). Re-arms the moment the (currently dead) import feature is fixed. |
| HO-3 | SEC-F19 per-IP NAT collapse | **CONFIRMED (live)** | 6 concurrent WS → 5 accept, 6th rejected; log `Per-IP limit reached for 172.23.0.1 (5/5)` = bridge gateway; no `X-Forwarded-For` → one client self-DoSes all. Bridge subnet was **172.23.0.0/16** — *outside* the hardcoded `172.18–21` metrics allowlist, sharpening the dynamic-IPAM risk. |
| HO-6 | **SEC-F22 (new)** browser-control bypass | **CONFIRMED (live)** | From a non-loopback in-network sidecar (172.23.0.5): anonymous `/api/csrf` mint + a **spoofed `Origin: http://127.0.0.1:8050`** → `POST /api/train/start` **200** (gate bypassed). Two negative controls (no-Origin 403, no-CSRF 403) prove the gate is genuinely active — Origin+anon-CSRF are not authenticators vs a non-browser client. Only guard = the loopback bind. |
| HO-4 | SEC-F09 deserialization | **CONFIRMED strength (fails closed)** | 7/7 weaponized payloads (os.system, subprocess, eval/exec, unlisted modules, datetime) rejected at `find_class` before construction; deny-by-default allowlist; corroborated by a 2nd restricted unpickler + `torch.load(weights_only=True)`. A control `pickle.loads` dropped a marker (payloads genuinely RCE); zero markers survived the restricted path. |
| HO-8 | SEC-F05 key-timing | **CONFIRMED constant-time** | `hmac.compare_digest`, single key; empirical (b)-vs-(c) median delta +11.3 µs (1.49%) ≪ ~30% noise floor → no gross byte-position signal. |
| HO-5 | SEC-F10 param bounds | **CONFIRMED (refined)** | START path (`TrainingParams`) fully bounded (422). Residuals: `PATCH /v1/training/params` binds `TrainingParamUpdateRequest` (`models/training.py:200-268`) with **lower bounds only** (huge `max_hidden_units` accepted with a live network); WS `set_params` (`control_stream.py:373-376`) bypasses pydantic. **Correction:** no `use_websocket_set_params` in cascor — `/ws/control` is enabled by default, so both surfaces are live (WS range-unvalidated). |

**Net effect on the findings.** SEC-F01 is confirmed **High** (fail-open is real and silent). A **new confirmed finding
SEC-F22** (browser-control gate bypassable from any in-network foothold; Medium, bounded only by the loopback bind) is the most
serious *live* result — remediation: a real per-session credential (not a spoofable Origin + anonymous CSRF), keep the control
surface loopback-bound, never expose it routable without a fronting authenticating proxy. SEC-F08 is **downgraded live (dead
endpoint, no egress) but flagged latent** (Medium) — the unguarded SSRF sink re-arms on any fix of the import feature; harden the
sink *before* fixing the feature, and note the dead-feature seam (import-url + import-file both 501 in demo, masked by mocked
tests — a correctness defect too). SEC-F19 is confirmed and sharpened (a dynamic bridge subnet can fall outside the metrics
allowlist). SEC-F09 and SEC-F05 are **verified strengths**. SEC-F10 stays Low but is re-framed (PATCH upper-bound omission + WS
pydantic-bypass, both auth-gated). Recommended remediation order: SEC-F01 (fail-closed auth posture) → SEC-F22 (real
control-surface credential) → SEC-F19 (trusted-proxy client identity) → SEC-F08 harden-then-fix → SEC-F10 model parity.

## 6. Prior-work integration & diff base

Build on, do not re-derive: the ecosystem baseline `juniper-ml/notes/legacy/SECURITY_AUDIT_PLAN.md` (24 findings; **diff the new
results against its CRITICAL "WS bypasses auth middleware", HIGH CORS-wildcard/headers/rate-limit, MED pickle-deserialization**);
the SOPS audit + remediation (deferred Phases 4–5); `JUNIPER_DEPLOY_GO_PUBLIC_ANALYSIS_2026-05-09.md`; the RC-3 secret-mount
symmetry work (static guards shipped, runtime byte-symmetry test deferred); the cascor secret-indirection investigation (fixed;
class-level import-guard deferred); the canopy 401 auth — **RESOLVED via #414/#415, verified live 2026-07-01** (see UX plan F-B),
so *not* an open item; the async-route audit follow-ups. SEC requirements area = 246 reqs / 58 P0 (`requirements/by-area/SEC.md`);
security-adjacent OBS via `JR-DAT-OBS-001` and the `/metrics` auth boundary (`requirements/by-area/OBS.md`). Treat all prior
status cells as unverified until re-confirmed (SP1).

## 7. Verification method (defensive; who executes)

Per finding, the SP2 verification is one of:

- **Static / read-only (Fable can execute):** confirm the code path, default, or config that establishes the (in)secure state —
  e.g. grep the SSRF handler for an allowlist (absent), read the compose secret default, read the torch floor in each
  `pyproject.toml`, `docker inspect` the running user/caps. Most findings above are already at this bar.
- **Active / dual-use (→ Opus, §8):** anything that proves a weakness by *exercising* it against a live service — auth-bypass
  demonstration, SSRF reachability/exfil proof, deserialization-escape PoC, deliberate fault/DoS injection, timing measurement,
  Origin/CSRF spoof. Deferred by design (Fable's dual-use safety posture; owner's explicit hand-off).

## 8. Opus hand-off register (granular, execution-phase)

Each item is one surface, scoped, with the inputs Opus needs and the artifact expected. All presuppose the owner's authorization
and an **isolated, non-production** bring-up (a throwaway compose stack), never the live/shared environment.

| HO | Surface / finding | Why handed off | Inputs Opus needs | Expected artifact | Pre-req |
| --- | --- | --- | --- | --- | --- |
| HO-1 | import-url SSRF reachability (SEC-F08) | active exploitation of a live fetch | demo-profile URL, an internal sentinel endpoint | proof the fetch reaches an internal/loopback/metadata address; before/after harden diff | isolated demo stack |
| HO-2 | Fail-open auth demonstration (SEC-F01) | active auth-bypass proof | a bring-up with empty/placeholder secret | evidence a protected route serves unauthenticated; confirm fix = fail-closed startup | isolated stack, no key |
| HO-3 | Per-IP WS cap self-DoS (SEC-F19/F-A) | deliberate DoS injection | canopy `:8050`, N concurrent WS clients | proof one client exhausts the shared cap-of-5 for others | isolated stack |
| HO-4 | Restricted-unpickler boundary (SEC-F09) | offensive deserialization PoC | a crafted HDF5 with a disallowed class | proof the allowlist rejects it (or a gap if not) | isolated stack |
| HO-5 | set_params fault injection (SEC-F10) | deliberate fault/DoS injection | authed session, out-of-range values | proof of NaN-training / resource blowup; proposed bounds | isolated stack |
| HO-6 | Browser-control Origin/CSRF spoof (§4.1, L11 §7.3 residual) | active auth-bypass attempt | a non-loopback client, spoofed Origin | proof the loopback-bind precondition is the only guard; recommend `/api/csrf` Origin hardening | non-loopback bind test |
| HO-7 | SSRF redirect bypass (SEC-F08) | offensive redirect chain | a public URL 302→internal | proof `follow_redirects=True` defeats an initial-URL host check | isolated demo stack |
| HO-8 | API-key timing side-channel (SEC-F05) | offensive timing measurement | cascor/recurrence auth endpoint | measurement of comparison timing variance; confirm constant-time or not | isolated stack |

**Outcomes (SP2′, executed by Opus 2026-07-02 on the isolated `secaudit`/127.0.0.2 stack — full detail in §5.2):** HO-2
CONFIRMED (fail-open) · HO-1/HO-7 PARTIAL (SSRF sink real but latent behind a 501 guard; off-switch non-functional) · HO-3
CONFIRMED (per-IP NAT self-DoS) · HO-6 CONFIRMED (browser-control bypass from in-network → new finding **SEC-F22**) · HO-4
CONFIRMED strength (restricted unpickler fails closed) · HO-8 CONFIRMED constant-time · HO-5 CONFIRMED (REST start bounded;
PATCH-upper-bound + WS-pydantic-bypass residuals). Isolated stack torn down after; live 127.0.0.1 stack untouched.

Non-handed-off (Fable completes in SP2): all static/read-only confirmations in §4 (allowlist-absent, defaults, floors, caps,
container inspect, config parity), the hardening recommendations, and the report authoring.

## 9. Execution phases

| Phase | Work | Executor | Output |
| --- | --- | --- | --- |
| SP0 (done) | Read-only security recon (4 agents) + grounded candidate findings | Fable | §4–§5 |
| SP1 | Independent multi-agent validation of this plan (re-probe every file:line/default/flow; adversarially test each finding) | Fable subagents | corrected plan |
| SP2 | Static/read-only verification of each finding at the evidence bar | Fable | verified findings |
| SP2′ **(done 2026-07-02, §5.2)** | Active/dual-use verification of the §8 register on an isolated stack | Opus | HO-1…HO-8 artifacts ✓ |
| SP3 | Author the security findings report (Critical→Low, diffed vs the 24-finding baseline) | Fable + Opus (HO items) | report doc |
| SP4 | Owner triage → issues/PRs; deploy/secret changes are owner-gated | owner | tracked follow-ups |

## 10. Appendix — key references

- **Auth/secrets:** canopy `src/{security.py,middleware.py,csrf.py,ws_security.py,secrets_util.py}`; cascor
  `src/api/{security.py,middleware.py}` + `websocket/{manager.py,worker_stream.py,control_stream.py,control_security.py}`; data
  `juniper_data/api/{security.py,middleware.py}`; recurrence via `juniper_service_core/{security.py,middleware.py}`; shared
  `juniper_observability/middleware/metrics_auth.py`; deploy `docker-compose.yml` (secrets `:923-945`), `scripts/prepare_secrets.bash`.
- **Input/sinks:** canopy `src/main.py` (import-url `:1345`, set_params `:3152`); cascor `snapshots/snapshot_serializer.py`,
  `utils/utils.py`; data `storage/{local_fs,postgres_store,redis_store}.py`, `routes/datasets.py`.
- **Container/deps:** each repo `Dockerfile` + `pyproject.toml`; `.github/workflows/{ci.yml,security-scan.yml}`;
  `dependabot.yml`; `.env.observability`.
- **Prior docs / requirements:** `legacy/SECURITY_AUDIT_PLAN.md`, `SOPS_AUDIT_AND_REMEDIATION_PLAN.md`,
  `JUNIPER_DEPLOY_GO_PUBLIC_ANALYSIS_2026-05-09.md`, `FOLLOWUP_ASYNC_ROUTE_AUDIT.md`, `requirements/by-area/{SEC,OBS}.md`.

> All `file:line` and every grounded finding here are source-cited and re-verified in SP1 (§9) before the report is authored.
> Live-exercised confirmations are deferred to Opus (§8). Nothing in this plan is a weaponized exploit; it is a defensive
> hardening checklist for the owner's own stack.
