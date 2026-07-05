# Juniper Stack Regression — Remediation Plan — 2026-05-27

**Author**: Paul Calnon (with Claude Opus 4.7 sub-agent investigation)
**Date**: 2026-05-27
**Companion**: [`JUNIPER_2026-05-27_JUNIPER-ECOSYSTEM_STACK-REGRESSION-ANALYSIS.md`](JUNIPER_2026-05-27_JUNIPER-ECOSYSTEM_STACK-REGRESSION-ANALYSIS.md)
**Repos in scope**: `juniper-cascor`, `juniper-cascor-client`, `juniper-canopy`, `juniper-deploy`

This document presents remediation options for each root cause from the analysis doc, with the strengths / weaknesses / risks of each approach, the recommended path, and the tests that must accompany each fix.

---

## 0. Roll-out Sequencing

Even with multiple repos in scope, the dependency order is forced and short:

1. `juniper-cascor-client` — add `origin=` support to `CascorControlStream` (pure additive, no breaking change). **Required first** because canopy depends on this surface.
2. `juniper-cascor` — make `ws_control_allowed_origins` env-driven. **Independent of #1**; can be merged in parallel.
3. `juniper-canopy` — wire `origin=` through `CascorServiceAdapter`; fix the double-`/v1` path. **Depends on #1**.
4. `juniper-deploy` — set the new env vars in `docker-compose.yml`. **Depends on #2 + #3**.

Worker-side (`juniper-cascor-worker`) is **not** touched — its `/ws/v1/workers` policy deliberately rejects any Origin (analysis §3.2). The fan-out is canopy-only.

---

## 1. RC-1 — `/ws/control` Origin Fail-Closed

Three approaches considered; **Approach A is recommended**. Approaches B and C are documented so the trade-off is visible.

### 1.1 Approach A — Explicit Origin from canopy + env-driven allowlist on cascor *(RECOMMENDED)*

**What changes**

- `juniper-cascor-client`: `CascorControlStream.__init__` gains `origin: Optional[str] = None`; `.connect()` forwards it to `websockets.connect(url, additional_headers=…, origin=…)`. Same change at the second `websockets.connect` call site (line 124). If `origin is None`, no Origin header is sent (existing behavior preserved → no breaking change for direct CLI users / tests).
- `juniper-canopy`: `BackendSettings` (or whichever Settings module holds the cascor URL) gains `cascor_ws_origin: str = "http://juniper-canopy:8050"` with env alias `JUNIPER_CANOPY_CASCOR_WS_ORIGIN`. `CascorServiceAdapter.__init__` accepts and forwards `ws_origin=…`; `ControlStreamSupervisor` is updated to pass `origin=ws_origin` when constructing the stream.
- `juniper-cascor`: `Settings.ws_control_allowed_origins` is changed from a hard-coded literal to a `Field(default_factory=…, alias_priority=…)` with env alias `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` (comma-separated CSV in the env var, parsed into a list by an `_parse_allowed_origins` validator that mirrors `_parse_api_keys`). Default list keeps `localhost:8050` + `127.0.0.1:8050` so dev-from-host still works.
- `juniper-deploy/docker-compose.yml`: cascor service env gains `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://juniper-canopy:8050,http://localhost:8050,http://127.0.0.1:8050`. Canopy service env gains `JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://juniper-canopy:8050`.

**Strengths**

- **No policy weakening on the server.** Origin fail-closed remains the default; the allowlist is just deployment-configurable.
- **Backward-compatible client.** `origin` is opt-in; CLI tools, juniper-cascor's own self-tests, and any third-party caller continue to work without change.
- **Symmetric to existing CFG-06 / CFG-09 pattern.** The Juniper convention is "Settings field with env alias"; this fits the rest of the ecosystem.
- **Diagnoseable.** Stack misconfiguration ("canopy set the wrong Origin", "cascor's allowlist doesn't include it") produces a single log line in `control_security.py` naming the rejected Origin string. Operators can copy-paste the rejected string into the cascor allowlist env var.
- **Trivial to test.** Add an integration test in juniper-cascor's `src/tests/integration/test_websocket_control.py` that boots the FastAPI app with a custom allowlist, connects a client with `origin=`, and asserts 200 / `connection_established`.

**Weaknesses / risks**

- **Touches four repos** → four PRs to coordinate. Risk: a juniper-canopy / juniper-cascor-client cross-merge mismatch if the canopy PR lands before juniper-cascor-client's release (canopy would call `CascorControlStream(origin=…)` which would raise `TypeError` on the older client). Mitigation: bump `juniper-cascor-client` minimum pin in canopy's `pyproject.toml` in the same PR that introduces the `origin=` kwarg, and pre-release `juniper-cascor-client` to PyPI (or pin to a git SHA).
- **Origin string drift.** If someone changes the canopy compose service name from `juniper-canopy` to e.g. `canopy`, the Origin string changes and the cascor allowlist must be updated. Mitigation: deploy a single env var (`JUNIPER_CANOPY_SERVICE_HOSTNAME`) that both ends of the handshake read; defer to RC-3 follow-up.
- **Doesn't address browser-originated `/ws/control` flow** if any. Browsers always send Origin from the page's location, so they would Just Work as long as the page is at `http://juniper-canopy:8050` (or whatever's in the allowlist). Today no production browser path exists, so this is non-blocking.

**Test additions**

| Repo | Test | Asserts |
|---|---|---|
| juniper-cascor-client | `tests/test_ws_client.py::test_connect_sends_origin_when_set` | mock `websockets.connect` captures kwargs; assert `origin="http://juniper-canopy:8050"` is forwarded. |
| juniper-cascor-client | `tests/test_ws_client.py::test_connect_omits_origin_when_unset` | mock confirms no `origin=` kwarg → preserves M2M default. |
| juniper-cascor | `src/tests/unit/api/test_control_security.py::test_origin_allowlist_env_override` | set `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://x:1,http://y:2`; assert the loaded Settings field contains exactly `["http://x:1", "http://y:2"]`. |
| juniper-cascor | `src/tests/integration/test_websocket_control.py::test_canopy_origin_accepted_via_env_allowlist` | new test — boot app with custom env allowlist; open WS with matching `Origin`; assert `connection_established` frame is received. |
| juniper-canopy | `src/tests/unit/backend/test_cascor_service_adapter.py::test_supervisor_passes_origin_to_stream` | construct `CascorServiceAdapter(service_url=…, ws_origin="http://juniper-canopy:8050")`; mock `CascorControlStream`; assert constructor receives `origin="http://juniper-canopy:8050"`. |
| juniper-deploy | `tests/integration/test_compose_up.sh` (new) | `docker compose up -d`; `docker logs juniper-canopy 2>&1 | grep -m1 "Control stream supervisor connected"` within 30s; fail if "no Origin header" appears in cascor logs. |

### 1.2 Approach B — Relax server policy (any-of {valid X-API-Key, valid Origin})

**What changes**

`juniper-cascor/src/api/websocket/control_security.py` is rewritten so that the WS upgrade is accepted if **either** (a) the Origin is in the allowlist **or** (b) a valid `X-API-Key` is presented in the `additional_headers`. Canopy already sends a valid X-API-Key, so this restores connectivity without any client- or deploy-side change.

**Strengths**

- **Single-repo fix.** No coordination across four PRs.
- **Restores connectivity immediately** as soon as canopy upgrades to whichever image carries the new cascor.
- **No deploy env-var changes required.**

**Weaknesses / risks**

- **Weakens the security model** introduced in PR #129. Origin validation was added explicitly because a stolen API key can be replayed from anywhere; tying acceptance to "matched Origin" is a defense-in-depth layer. Approach B collapses the matrix from `(origin ∈ allowlist) AND (api_key valid)` to `(origin ∈ allowlist) OR (api_key valid)`.
- **Hidden incompatibility with rate-limiter scoping.** PR #129 also keys rate-limit buckets by Origin; degrading to API-key-only-acceptance means upgrades from non-allowlisted origins still hit the rate-limiter but on a fallback key bucket, which is undocumented behavior.
- **Reviewer-visible policy change.** Likely to draw scrutiny in code review; would need a fresh threat-model write-up. Out of proportion to the actual integration ask.

**Test additions**

Would need to replicate every test the current policy has, then add the "X-API-Key without Origin is accepted" path. Larger surface to maintain than Approach A.

### 1.3 Approach C — Internal-network skip (`X-Forwarded-For` / docker-network detection)

**What changes**

`control_security.py` inspects the upgrade's source IP. If it falls within an internal CIDR (e.g., `172.16.0.0/12` for docker default bridges), skip the Origin check entirely.

**Strengths**

- No client-side or deploy-side change.

**Weaknesses / risks**

- **Wrong layer.** TCP source IP says nothing about *what* sent the request; a compromised container in the same network could connect with no Origin and be accepted.
- **Docker default bridge IPs are not stable.** This conflict with the audit findings in the PoC remediation plan (`juniper-deploy/notes/poc/POC_REMEDIATION_PLAN_2026-05-27.md`) which explicitly recommends *not* relying on docker-bridge IP CIDR.
- **Asymmetric with prod intent.** In Kubernetes, "internal CIDR" has very different semantics from docker compose; the heuristic would need a re-implementation per environment.

**Recommendation**: do not adopt. Documented for completeness only.

### 1.4 Decision

**Adopt Approach A.** It preserves the policy intent of PR #129, distributes the change cleanly across already-coupled repos, and provides a future-proof env-var contract that scales to Kubernetes (where the canopy → cascor Origin will be `http://juniper-canopy.juniper.svc:8050` or similar — just a different env-var value).

---

## 2. RC-2 — Double `/v1/v1` Path Bug

Single bug, single-line fix; no architecturally-meaningful alternatives.

### 2.1 Fix

`juniper-canopy/src/backend/cascor_service_adapter.py:1069`:

```diff
- result = self._client._request("GET", "/v1/history/dataset_swaps", params=params)
+ result = self._client._request("GET", "/history/dataset_swaps", params=params)
```

### 2.2 Test additions

| Repo | Test | Asserts |
|---|---|---|
| juniper-canopy | `src/tests/unit/backend/test_cascor_service_adapter.py::test_get_dataset_swap_events_path` | monkeypatch `self._client._request`; call `adapter.get_dataset_swap_events()`; assert the captured path argument is `/history/dataset_swaps`, not `/v1/history/dataset_swaps`. |
| juniper-canopy | `src/tests/unit/backend/test_cascor_service_adapter.py::test_no_callsite_passes_v1_prefix` | reflective test — walks `cascor_service_adapter.py`'s AST looking for `self._client._request(` calls whose path string literal starts with `/v1/`. Fails the build if any do (cheap regression guard against the same class of bug appearing elsewhere). |

### 2.3 Risks

- **The `_request` API contract is not documented.** Adding the AST-level guard test surfaces the contract: *paths passed to `_request` MUST NOT include `/v1`*. Should be documented in `juniper-cascor-client/juniper_cascor_client/client.py`'s `_request` docstring.
- **None other.**

---

## 3. RC-3 — Latent Asymmetric Secrets

**Recommendation**: defer to a follow-up PR explicitly tracked against the open juniper-deploy `docs/poc-remediation-plan` branch's scope. The live stack is HTTP-auth-functional by coincidence; opening this fix in the same PR cluster as RC-1 + RC-2 would conflate "fix the user-visible regression" with "harden the deploy contract", which slows review and risks scope creep.

**Tracking artifact** *(to add to the existing PoC remediation plan or as a sibling doc)*:

1. Standardize on **comma-CSV** placeholder shape across all `*_api_keys` files (`secrets.example/juniper_cascor_api_keys.txt = CHANGE_BEFORE_PRODUCTION_USE`). Removes the JSON-list rendering quirk that produces `['["CHANGE_BEFORE_PRODUCTION_USE"]']`.
2. Update `make prepare-secrets` to populate *all* compose-referenced secret files (not the strict subset memory `project_make_prepare_secrets_incomplete_2026-05-10` documents).
3. Add `juniper-deploy/tests/integration/test_compose_secrets_symmetry.sh` that asserts every container-side `/run/secrets/*` file matches its counterpart sibling across services that share a secret (canopy and cascor both reading `juniper_cascor_api_keys` should see byte-identical content).
4. Document the canonical local-stack `--env-file` pattern (memory `reference_juniper_deploy_local_secrets_env_2026-05-10`) as a checked-in `docs/LOCAL_STACK_QUICK_START.md` in juniper-deploy.

---

## 4. Acceptance / "Done" Checklist

The combined fix is "done" when **all** of the following hold against a freshly-rebuilt stack:

- [ ] `docker compose down && docker compose build && docker compose up -d` (no env-file overrides; default secrets path)
- [ ] `docker logs juniper-canopy 2>&1 | grep "Control stream supervisor connected to"` shows the success line within 30s
- [ ] `docker logs juniper-cascor 2>&1 | grep "no Origin header"` returns nothing (no fail-closed events for canopy)
- [ ] `docker logs juniper-cascor 2>&1 | grep "/v1/v1/"` returns nothing
- [ ] Browser → Dataset View tab — Save Params button reports success (and live dashboard reflects updated params)
- [ ] Browser → Dataset View tab — Generate Dataset button completes (and the new dataset appears in the dataset list)
- [ ] Browser → Dataset View tab — Launch Training button starts training (FSM transitions to STARTED → BUILDING → … visible in dashboard)
- [ ] All four repos' full test suites pass:
  - `cd juniper-cascor-client && pytest tests/ -v`
  - `cd juniper-cascor && bash src/tests/scripts/run_tests.bash`
  - `cd juniper-canopy && bash src/tests/scripts/run_tests.bash`
  - `cd juniper-deploy && bash tests/integration/test_compose_up.sh` (new; from §1.1 above)
- [ ] PR descriptions cite the `JR-*` requirement IDs for any affected requirements (per juniper-ml CLAUDE.md PR conventions)

---

## 5. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| juniper-cascor-client release lag — canopy PR merges before juniper-cascor-client is on PyPI / pinned | Medium | High (CI breaks across canopy + downstream) | Bump the pin in canopy's `pyproject.toml` *in the same PR* as the `origin=` integration; cut juniper-cascor-client release candidate first. |
| Stale cascor image in the running stack — new `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` env var ignored because the running image is from before Approach A merged | Medium | Critical (looks like the fix didn't take) | Add image-build-time `BUILD_INFO_IMAGE_CREATED` label inspection to the acceptance script in §4. Reference memory `project_juniper_cascor_image_2_months_stale_2026-05-27`. |
| Canopy `internal_api_headers()` regression on a future endpoint — RC-3 surfaces | Low | High | RC-3 follow-up (§3); not blocking on this fix. |
| Other callsites in `cascor_service_adapter.py` also pass `/v1/...` paths to `_request` | Low | Low | The reflective AST-level test in §2.2 covers this. |
| Origin-related test failures on the existing cascor pytest suite from Settings field-mode change | Low | Medium | The change is additive (adds env alias; keeps default list). Existing tests use programmatic `Settings(ws_control_allowed_origins=[...])` which is unaffected by env aliasing. |

---

## 6. PR Plan

Four PRs, in the following order:

### PR-1 — `juniper-cascor-client`: add `origin=` to `CascorControlStream`

- Add `origin: Optional[str] = None` to `CascorControlStream.__init__`.
- Forward to `websockets.connect(..., origin=self.origin)` when not None.
- Add tests from §1.4 (client side).
- Release as `juniper-cascor-client` minor bump (`0.4.x` → `0.5.0`). Update `juniper-ml/pyproject.toml`'s `[clients]` extra accordingly.

### PR-2 — `juniper-cascor`: env-driven `ws_control_allowed_origins`

- Convert the hard-coded list to a Settings field with env alias.
- Add `_parse_allowed_origins` validator (CSV-splitting; mirrors `_parse_api_keys`).
- Tests from §1.4 (server side).
- Document the env var in `docs/REFERENCE.md`.

### PR-3 — `juniper-canopy`: pass Origin through `CascorServiceAdapter` + fix double-`/v1`

- Add `cascor_ws_origin` Settings field (env alias `JUNIPER_CANOPY_CASCOR_WS_ORIGIN`).
- Wire through `CascorServiceAdapter` and `ControlStreamSupervisor`.
- Fix `cascor_service_adapter.py:1069` `/v1` strip.
- Tests from §1.4 (canopy side) + RC-2 tests from §2.2.
- Bump `juniper-cascor-client>=0.5.0` (PR-1's release) in `pyproject.toml`.

### PR-4 — `juniper-deploy`: set the new env vars

- Add `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` to cascor service block.
- Add `JUNIPER_CANOPY_CASCOR_WS_ORIGIN` to canopy service block.
- Add new `tests/integration/test_compose_up.sh` acceptance script (§4).

---

## 7. Out-of-Scope (Tracked Separately)

- RC-3 secrets symmetry: covered in §3, deferred to a follow-up PR on top of the existing `docs/poc-remediation-plan` work.
- New canopy `/v1/health` deep-check that includes supervisor `is_connected`: deferred — call it a follow-up "canopy healthcheck depth" PR after RC-1 lands. Reference: §6 of the analysis doc.
- Documentation of the `_request` path-prefix contract on juniper-cascor-client: small follow-up, can ride with PR-1's docstring updates.
- Browser-originated `/ws/control` policy (currently dead code path; no in-browser dashboard hits `/ws/control` directly): no action; revisit when / if the dashboard frontend grows a direct-WS path.
