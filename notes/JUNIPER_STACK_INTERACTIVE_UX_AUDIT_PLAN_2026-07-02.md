# Juniper Stack — Interactive UX Audit Plan (Containerized)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-07-02

---

## 1. Purpose

Validate that the **interactive** aspects of the Juniper stack — everything a user can click, type, select, or toggle in the
`juniper-canopy` dashboard, and the backend behavior each action drives — deliver the functionality the application *presents*
and the behavior the project documentation (`notes/`, `docs/`, `README`, `AGENTS.md`) *claims*. The audit is driven by a
**live, per-click walk-through** of the containerized stack, with backend containers observed in lockstep, so that every claim
in the resulting findings is backed by an observed request/response, a log line, or a cited `file:line`.

This document is the **plan** (methodology + walk-through script + finding taxonomy + execution phases). It is not the audit
report; §11 seeds the report with pilot observations already captured while validating the methodology.

## 2. Scope

### 2.1 In scope — four gap dimensions

| Dim | Name | Question the audit answers |
| --- | --- | --- |
| **D1** | Functionality vs. user experience | Does each control do what the UI implies it does, with correct enable/disable, feedback, and state transitions? |
| **D2** | Functionality vs. documentation | Does observed behavior match `USER_MANUAL.md`, `README.md`, `AGENTS.md`, and the `notes/` designs-of-record? Undocumented-but-present and documented-but-absent both count. |
| **D3** | Output accuracy | Are displayed values (metrics, versions, counts, statuses, network info) correct and internally consistent across surfaces? |
| **D4** | Correctness — syntactic, logical, functional, architectural | Do responses/state machines behave correctly (no contradictory payloads, dead controls, mis-routed backends, or invariant violations)? |

### 2.2 Out of scope (deferred)

- **Security / vulnerability assessment** (architecture and implementation) is covered in the **companion plan**
  [`JUNIPER_STACK_SECURITY_AUDIT_PLAN_2026-07-02.md`](JUNIPER_STACK_SECURITY_AUDIT_PLAN_2026-07-02.md) as dimension **D5**. The
  planning + read-only enumeration were done here (with Fable); genuinely dual-use *execution* steps (active exploitation,
  PoCs) are handed off to Opus in that doc's §8 register. This UX plan itself does **not** hunt for vulnerabilities; where a
  *reliability/functional* defect happens to touch an auth or rate-limit code path (e.g. the WebSocket per-IP cap in §11 F-A —
  which the companion picks up as SEC-F19 — or the CSRF gate in F-B), it is recorded here **only** for its UX/correctness impact.
- On-host (non-containerized) execution. This audit targets the **containerized** stack only (per directive). The on-host
  conda stack is a follow-up.
- Load/soak/perf benchmarking beyond the coarse responsiveness observations the walk-through naturally produces.

## 3. Stack Under Test (containerized)

Authoritative topology (verified live 2026-07-02 via `docker ps` + `docker compose ls`; details in
`notes/`-cited agent recon, reconfirmed against `juniper-deploy/docker-compose.yml`). Compose project `juniper-deploy`,
profiles `full` / `demo` / `dev` / `test` / `observability`.

| Service | Host port | Container port | Health | Notes |
| --- | --- | --- | --- | --- |
| juniper-canopy | `127.0.0.1:8050` | 8050 | `/v1/health` | Dash UI at `/dashboard`; the click-through target |
| juniper-cascor | `127.0.0.1:8201` | 8200 | `/v1/health` | CasCor backend; canopy → cascor via `JuniperCascorClient` |
| juniper-cascor-worker ×2 | none | 8210 | `/v1/health/ready` | distributed training workers |
| juniper-recurrence | `127.0.0.1:8211` | 8210 | `/v1/health` | LMU / one-shot backend |
| juniper-data | none (internal) | 8100 | `/v1/health` | dataset service; no host port (reach via `docker compose exec`) |
| juniper-redis | none (internal) | 6379 | `redis-cli ping` | canopy `REDIS_URL=redis://redis:6379/0` |
| Observability (profile) | prometheus `127.0.0.1:9090`, grafana `127.0.0.1:3001` | — | — | alertmanager has **no** host port |

**Bring-up (reference):** `make monitor` (= full + observability) or `make demo` / `make obs-demo` (auto-training demo).
`make prepare-secrets` first; `make doctor` reports image freshness (data/cascor/canopy/worker only — **not** recurrence).

**Two canopy control transports to exercise separately (D4-critical):**

1. **Browser path** — clientside JS → `ws://<host>/ws/control` (with CSRF), REST fallback `POST /api/train/*` (Origin + CSRF +
   session cookie). Active when `enable_ws_control_buttons=True` (production default).
2. **Server-side self-call path** — Dash callback → canopy's own FastAPI via `requests.*` with an internal token.

Both converge on the same `backend.*` methods, but only the browser path reflects real user experience — the walk-through must
drive the **browser** path and treat the server-side path as a control/comparison.

## 4. Audit Rubric

Each surface is scored against the four dimensions with a fixed evidence bar. A finding is admissible only if it carries **at
least one** of: (a) an observed HTTP request+response (method, path, status, body excerpt); (b) a container log line with
timestamp; (c) a UI state observation (snapshot/screenshot); plus the `file:line` of the implementing code and, for D2, the
`file:line` of the documentation claim. No claim ships on inference alone — this is the anti-hallucination bar carried into the
findings report (and re-checked in the §9 validation phase).

Severity: **S1** user-facing broken / wrong output shown as correct · **S2** degraded or contradictory behavior with a
workaround · **S3** documentation/consistency gap · **S4** cosmetic/informational.

## 5. Methodology — the per-click walk-through

### 5.1 Harness

- **Driver:** `chrome-devtools` MCP against `http://127.0.0.1:8050/dashboard/` (the container's host-published port).
- **Backend observation:** a `docker logs --since <T> -f` tail per service (canopy, cascor, worker, data, recurrence) time-aligned
  to each click via a recorded `date -u` baseline before each step.
- **Endpoint truth:** direct `curl` against `127.0.0.1:8050` (and `:8201`) to capture exact status codes/bodies when the Dash
  network panel is too noisy (it is — see 5.4).
- **State:** `GET /v1/health`, `GET /api/status`, `GET /api/state` snapshots before/after each mutating action.

### 5.2 Per-click protocol (repeat for every control in §6)

1. Record `T0 = date -u`; snapshot UI (a11y tree) + relevant status fields.
2. Perform exactly one action (click/fill/select/toggle).
3. Capture: the request(s) it fired (path, method, status, body), the UI delta, and each backend log slice since `T0`.
4. Compare observed behavior to (i) what the UI implies, (ii) the documented behavior (cited), (iii) the expected backend call.
5. Classify any gap under D1–D4 with severity; attach evidence. Reset state if the action mutated it.

### 5.3 Reproducibility & isolation

- Use **one** browser client; reap between steps. The per-IP WebSocket cap counts all host clients as the Docker gateway IP
  (§11 F-A), so multiple tabs/clients distort behavior — the audit tooling itself must not saturate the cap.
- Pin the image under test: record `git_sha` + `build_date` from `/v1/health` at the start of every session (the running
  canopy currently reports `541cafe-dirty` — a dirty build; see F-I). Re-running after a rebuild requires re-recording.
- Prefer `make demo` (auto-trains, open auth) for exercising *training-active* surfaces without standing up a network by hand,
  and `make monitor` (full, auth on) for the realistic authenticated path. Note which profile produced each finding.

### 5.4 Known tooling traps (from the pilot)

- Dash floods `POST /dashboard/_dash-update-component` (1900+ requests in minutes) — filter the network log to `/api/` + `/ws/`
  or probe endpoints directly with `curl`.
- Dash tabs need a full pointer-event sequence (`pointerdown→mousedown→pointerup→mouseup→click`), not a bare `.click()`, to
  activate; verify the active tab after switching (some clicks silently no-op).
- `dbc.Input(type=number)` cannot be driven by synthetic input events (React `onChange` never fires → Dash `State` stays null).
  For numeric params, POST `/api/set_params` directly to exercise the backend path, and treat the input-driving gap as a known
  harness limitation, not a stack defect.
- A single-worker canopy degrades badly under the tool's own polling + WS reconnect storm (health latency hit ~10 s in the
  pilot). Let it quiesce between steps; distinguish "timeout under load" (transport `000`) from a real status code.

## 6. Walk-Through Script (surface-by-surface)

Ordered to build state naturally: idle → create/apply → train → observe → snapshot/replay → edit. Every row states the
**expected behavior + doc citation** and the **backend interaction to confirm**. Citations are source-grounded; the §9
validation pass re-verifies each before the report is authored.

### 6.1 Training controls (sidebar "Training Controls")

| Control (id) | Expected behavior + doc | Backend interaction to confirm | Dim focus |
| --- | --- | --- | --- |
| Start `start-button` | "Starts or restarts from beginning; auto-resets on start" (`USER_MANUAL.md:174`). | Browser: `/ws/control {command:start}` or `POST /api/train/start`; → `backend.start_training` → cascor. **Confirm the response payload is self-consistent** (see F-C). | D1 D4 |
| Pause `pause-button` | "Pauses without losing state" (`USER_MANUAL.md:187`). | `POST /api/train/pause` → adapter. | D1 |
| Resume `resume-button` | UI has a dedicated Resume button; manual says resume = "click Pause again" (`USER_MANUAL.md:198`) — **doc/impl mismatch**. | `POST /api/train/resume`. | D2 |
| Stop `stop-button` | "Stops completely; cannot resume (use Start)" (`USER_MANUAL.md:200`). | `POST /api/train/stop`. | D1 |
| Reset `reset-button` | Listed in overview + `AGENTS.md` API table; **no `USER_MANUAL` subsection**. | `POST /api/train/reset`. | D2 |
| Outcome alert `training-control-outcome-alert` | Rejected commands surface a dismissable danger alert (the "dead button" fix, `CANOPY_TRAINING_CONTROL_ERROR_SURFACING_DESIGN_2026-06-14.md`). | Reads `training-control-action` store. **Confirm 4xx/timeout actually renders an alert** — pilot start showed none (F-C). | D1 D4 |
| Train-gate notice `train-gate-notice` | Explains why Start is disabled for a non-live/coming-soon model (D8). | derived from `model-selection-store`. | D1 |

### 6.2 Model + dataset selection ("A1" surface)

| Control | Expected behavior + doc | Confirm | Dim |
| --- | --- | --- | --- |
| "▸ change" `nn-model-change-button` → `model-selection-modal` | Opens the dedicated selection surface. **Implemented as a modal**, though the design's default lean was a Models *tab* (`JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md`, OQ-1) — resolved-opposite, intentional. | opens modal (no backend). | D2 |
| Model search `model-search-input` | 350 ms-debounced filter over label/family/category/tags. | client-only. | D1 |
| Per-row Select `{model-select-btn}` | Swaps the runtime backend; incompatible rows greyed; non-live selectable-but-not-trainable. | `POST /api/model/select` → `_swap_backend` (recurrence routing). **Selecting recurrence exercises the known 5-site `backend_type` mis-bucketing** (`JUNIPER_CANOPY_A1_III_DASHBOARD_INTEGRATION_SCOPE_2026-06-23.md` §2.1). | D4 |
| Dataset type `nn-dataset-type-dropdown` | Options sourced from the registry (compat forward-gate), not hardcoded. | consumed on Apply/Start. | D1 |
| Apply Dataset `apply-dataset-button` | Stages a cold-swap; restart applies. | `POST /api/stage_dataset` → cascor `POST /training/dataset`. | D1 |
| Live Dataset Switch `live-dataset-switch-button` (disabled by default) | Gated by experimental-flags + training-active (F2.3, `ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md`). | opens `live-switch-modal`. **Confirm it enables only when experimental ON + training active.** | D1 D4 |
| Live-switch accept/cancel | Two-step warning, then commit/cancel. | `POST` / `DELETE /api/live_dataset_swap` → cascor `/training/dataset/live`. | D1 |
| Pending-dataset banner + `restart-with-new-dataset-button` | Shown when cascor reports `pending_dataset`. This button was a **confirmed dead button** (no callback) and is **now wired** (#366) — re-verify live; the class "keeps recurring". | `POST /api/train/start?reset=true`. | D1 D4 |

### 6.3 Parameter form + Apply

Sidebar `dbc.Input(type=number)` set (max-iterations, epochs, learning-rate, hidden-units, spiral/dataset params, candidate-pool
params) + dropdowns (init weights, optimizer, activation). **Apply Parameters** `apply-params-button` (disabled until dirty) →
`POST /api/set_params` → `backend.apply_params` → cascor `update_params`, then reads back `GET /api/state` to verify.

- D2: `USER_MANUAL.md:213–227` documents only Learning Rate + Max Hidden Units; ~15 numeric inputs + 3 dropdowns + a radio are
  undocumented. Record each.
- D3/D4: after Apply, confirm the **Parameters tab** read-only table and the sidebar agree, and that the value round-trips
  through cascor (not just echoed client-side). Drive numeric values via `/api/set_params` (harness limitation, 5.4).

### 6.4 Visualization tabs (15) — render + accuracy

Enumerate and open each: Training Metrics, Candidate Metrics, Network Topology, Network Evolution, Decision Boundary, Dataset
View, Workers, Parameters, Snapshots, Replay, Network Editor, Redis, Cassandra, Tutorial, About. Cascade-only tabs
{candidates, topology, evolution, boundaries, workers} should be **hidden** for one-shot (recurrence) models — verify the
suppression after selecting a recurrence model.

- D2: `USER_MANUAL.md` documents only 5 tabs (Metrics, Topology, Network Editor, Decision Boundary, Dataset View). The other 10
  are undocumented — record each.
- D3: for each data-bearing tab, confirm displayed counts/status match `/api/status` / `/api/state` / cascor network stats.
- D4: **Redis tab** shows DISABLED though the redis container is healthy (F-F); **Cassandra tab** exists with no cassandra
  backend in the stack (F-G); **About** version string vs `/v1/health` version (F-H). Each is a scripted checkpoint.

### 6.5 Per-tab panel controls

Snapshots (create/refresh/restore) → Replay (play/pause/scrub/speed) → Network Editor (add/remove/patch; unlocks only in the
cascor FSM `Investigating` state entered by restoring a snapshot) → Dataset View (generate/load/import-file/import-url) →
Topology (layout/depth) → Decision Boundary (resolution/refresh) → Metrics (save/load/delete layout, replay scrubber). For each,
confirm the documented backend endpoint (`/api/v1/snapshots*`, `/api/v1/metrics/layouts*`, `/api/v1/network/hidden-units`,
`/api/dataset/*`, `/api/topology*`, `/api/decision_boundary`) fires and the panel reflects the result.

### 6.6 Status bar, badges, polling

- WS connection badge `ws-connection-indicator` — 4-state (Connected/Reconnecting/Offline/Demo). Confirm it reflects the **real**
  socket state in the full (non-demo) profile; in demo mode it pins to "Demo" regardless of socket (by design — record as D2
  context, not a defect). Pilot showed it stuck "Reconnecting" (F-A).
- `dcc.Interval` polling: fast 1 s (`/api/status`), slow 5 s (topology/boundary/dataset/history). Confirm cadence and that
  polling is *not* suppressed when WS is connected (JR-ML-UI-001 is proposed, not shipped — expect no suppression; record as D2).

## 7. Prior-Work Integration (re-verify targets)

The audit builds on the existing `notes/` corpus (full ledger compiled during recon). **The plan explicitly re-verifies these
against the running container rather than trusting their status cells**, because several are 1–4 days stale and one headline
finding (the 401) was already fixed after those notes were written — the pilot (F-B) confirms the fix live:

1. `JUNIPER_DOCS_REALITY_AUDIT_2026-06-21.md` — the current-state snapshot; treats per-cluster docs as trailing reality.
2. `juniper-canopy/notes/JUNIPER_CANOPY_CASCOR-TRAINING-401-APIKEY_AUDIT_2026-06-29.md` +
   `.../JUNIPER_CANOPY_TRAINING-CONTROL-AUTH_DESIGN_2026-06-30.md` — the "Start is 401-broken" audit/design. The fix **shipped**
   as canopy #414/#415 (rolled out + verified live 2026-07-01): the browser control surface now authenticates via Origin+CSRF.
   **Pilot F-B confirms this live** (Origin + CSRF token → 200); the recon ledger flagged it "not implemented" only because it
   read the notes without the #415 rollout context. Treat as resolved; keep as a regression checkpoint.
3. `CANOPY_TRAINING_CONTROL_ERROR_SURFACING_DESIGN_2026-06-14.md` — "dead button" error surfacing; needs live confirmation the
   alert renders (F-C is the counter-observation).
4. `JUNIPER_CANOPY_A1_III_DASHBOARD_INTEGRATION_SCOPE_2026-06-23.md` §2.1 — recurrence `backend_type` mis-bucketing at 5 sites.
5. `JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md` — model picker / `task_type` awareness status.
6. `code-review/CANOPY_CASCOR_INTERFACE_ANALYSIS_2026-04-08.md` — WS relay "Partial", "dashboard doesn't consume WS data"
   (P5-RC-05/14); re-verify whether the live-metrics WS path is now consumed end-to-end.
7. `JUNIPER_CANOPY_AUDIT_AND_HARNESS_PLAN_2026-06-15.md` — the L1/L2 UI-regression harness + the `dbc.Input(type=number)` gap;
   the L3 real-browser layer is exactly what this walk-through extends.
8. `JUNIPER_RECURRENCE_FULL_AUDIT_2026-06-24.md` — recurrence app has no runtime logging + no Dockerfile (OBS-01/02, OUT-4);
   affects observability of the recurrence backend during the walk-through.
9. Requirements areas to tag findings against: **UI** (JR-ML-UI-001/002), **WS**, **API**, **OBS**, **DEP**, **DATA**, **TRAIN**,
   **TEST** (`notes/REQUIREMENTS_INDEX.md`, `notes/requirements/by-area/`).

## 8. Findings Ledger Format

The audit report (separate doc, `JUNIPER_STACK_INTERACTIVE_UX_AUDIT_<DATE>.md`) records each finding as:

```text
### F-NN  <one-line title>
- Dimension: D1|D2|D3|D4    Severity: S1..S4
- Surface: <control id / tab / endpoint>
- Expected: <UI implication + doc citation file:line>
- Observed: <evidence: request/response, log line @ ts, UI state>
- Code: <file:line of implementing code>
- Requirement: <JR-* id(s) if applicable>
- Disposition: <new | confirms prior doc X | contradicts prior doc X (stale)>
```

## 9. Anti-Hallucination Validation (of this plan and of the eventual report)

Both this plan and the resulting findings report pass through **independent multi-agent validation** before they are trusted:

- **Re-probe every asserted fact** — each `file:line`, endpoint path, port, version string, env var, feature-flag default, and
  live-finding — against the real repo and the running containers, by validator sub-agents that did not author the claim.
- **Adversarial contradiction** — a separate agent attempts to *refute* each pilot finding (F-A…F-I): can it reproduce the
  opposite? A finding survives only if refutation fails.
- **Staleness reconciliation** — every "confirms/contradicts prior doc" disposition is checked against the cited doc's actual
  text and the current `git_sha` of the running image.

Anything that cannot be independently reproduced is downgraded to "unverified" or dropped.

## 10. Execution Phases

| Phase | Work | Output |
| --- | --- | --- |
| P0 (done) | Recon: topology, canopy surface inventory, prior-audit ledger; pilot walk-through | this plan + §11 |
| P1 | Validate this plan (multi-agent, §9) | corrected plan |
| P2 | Full scripted walk-through §6 under `make monitor` (auth) and `make demo` (auto-train) | raw evidence log |
| P3 | Author findings report from evidence; tag requirements; set dispositions | audit report doc |
| P4 | Validate the report (§9); integrate corrections | final report |
| P5 | (owner) triage → issues/PRs; hand security-adjacent notes to the separate Opus security pass | tracked follow-ups |

## 11. Pilot Walk-Through Observations (live, 2026-07-02 ~02:23–02:41 UTC)

Captured while validating the methodology against the running stack (canopy `0.5.0` / `541cafe-dirty` / build
`2026-07-01T23:23:41Z`, `demo_mode=false`, full profile). Each was then **independently re-verified** by the §9 anti-hallucination
pass — a separate agent that tried to *refute* each finding against the running containers. **All nine reproduced; none were
refuted** (two required wording corrections, folded in below). They demonstrate the method produces evidence-backed results and
seed the report. Security framing intentionally omitted (§2.2).

| ID | Dim/Sev | Observation (evidence) | Disposition |
| --- | --- | --- | --- |
| **F-A** | D1/S2 | WebSocket `/ws/training` + `/ws/control` handshakes return **403**; canopy log root cause `Per-IP limit reached for 172.19.0.1 (5/5)`. `172.19.0.1` is the Docker bridge gateway, so all host browser clients collapse to one IP sharing a single 5-socket budget (`max_connections_per_ip=5`). Slots stayed pinned 5/5 after the browser closed (reap/leak concern; `idle_timeout_seconds=120`). WS badge stuck "Reconnecting". | new (functional/reliability; container-specific NAT visibility) |
| **F-B** | D4/S2 | `GET /api/csrf` (Origin) → **200** `{csrf_token,enabled:true}`; `POST /api/train/start` with Origin + `X-CSRF-Token` → **200**; without the token → **403** "Invalid or missing CSRF token." The token itself is the credential — **no session cookie** (`/api/csrf` sets none). Browser-control auth **works** in this image. | **confirms** the canopy #414/#415 401-fix (shipped + verified live 2026-07-01) — the 06-29/06-30 audit+design were its precursors; mark resolved |
| **F-C** | D4/S1 | `POST /api/train/start` (authed) → HTTP **200** body `{"status":"started","ok":false,"error":"No network created"}` — self-contradictory (claims "started" while `ok:false`). No UI error alert surfaced on the browser click. Logged canopy-side only (root cause below). | new (correctness: transport- vs op-success conflation; Start does not auto-create a network) |
| **F-D** | D1/S3 | Single-worker canopy `/v1/health` latency reached **~10 s** under the tool's polling + WS reconnect storm (39 TCP conns), recovering to ~2 ms once quiesced (24 conns). | new (responsiveness under concurrent clients) |
| **F-E** | D2/S3 | All **15** dashboard tabs render; `USER_MANUAL.md` documents only **5**. | confirms known docs-lag; enumerated live |
| **F-F** | D3/S2 | **Redis** tab shows "DISABLED / Health --" though `juniper-redis` is healthy and `REDIS_URL` is set; canopy logged "Redis metrics/status API request timed out" 37×. Root cause below (single-worker self-call starvation, not redis). | new (architectural: in-process authenticated self-call starves the sole worker) |
| **F-G** | D2/S3 | **Cassandra** tab present, but **no cassandra service exists** in `docker-compose.yml`. | new (surfaced-but-absent backend) |
| **F-H** | D3/S3 | **About** tab reads "Juniper Canopy Version **2.2.0**"; `/v1/health` reports version **0.5.0**. | new (output-accuracy: two version strings for one service) |
| **F-I** | D4/S3 | Running canopy image reports `git_sha=541cafe-**dirty**` — built from an uncommitted tree. | new (provenance/reproducibility) |

### 11.1 Validation outcome & verified root causes (Phase 1)

Independent re-verification (§9) reproduced all nine. Precise root causes surfaced during refutation:

- **F-A cause = per-IP cap, not Origin.** The 403 is `websocket_manager.py:374` → `main.py:626` `websocket.close(code=1013)` before accept; the
  refutation confirmed `ws_origin_rejected` stayed **0** while `Per-IP limit reached for 172.19.0.1 (5/5)` incremented on the probe.
  `docker network inspect` confirms `172.19.0.1` is the frontend bridge gateway (canopy sits at `172.19.0.4`), so every host client
  presents as that one IP.
- **F-C cause.** `main.py:2935` unconditionally returns `{"status": "started", **result}`, merging a
  `ControlResult(ok=False, error="No network created")` from `service_backend.py:92` (raised when the adapter has no network) — so the
  200 body carries both `status:"started"` and `ok:false`. The message is logged **canopy-side only** (its `cascor_service_adapter`,
  1383× over 3 h); cascor emits it as an HTTP 404 detail that canopy logs on receipt (cascor's own logs show it 0×).
- **F-F cause = single-worker self-call starvation.** The `RedisPanel` Dash callback runs *inside* the canopy process and does a
  synchronous `requests.get("http://127.0.0.1:8050/api/v1/redis/{status,metrics}", timeout=2, headers=internal_api_headers())` — an
  authenticated **in-process self-call**. On a single uvicorn worker the callback holds the worker while waiting on the same server, so
  it times out at 2 s and the panel renders empty/DISABLED. The endpoint itself answers instantly (a keyless host probe got a fast 401).
- **Architectural theme (D4).** F-C, F-D, and F-F share one root: **canopy runs a single uvicorn worker** (`Dockerfile` `CMD ["python", "src/main.py"]`,
  `uvicorn.run` with no `workers=`) while several Dash callbacks make **synchronous authenticated HTTP calls back to that same worker**.
  Under the browser's normal polling this self-contention degrades responsiveness (F-D) and starves best-effort panels (F-F). This is the
  highest-value architectural target for the full audit and should be a first-class checkpoint in §6.5–§6.6.
- **F-B correction + disposition.** There is **no session cookie** — `/api/csrf` sets none; CSRF is a server-side hmac token store
  (`csrf.py`) and the returned token is itself the credential. The pass/fail behavior (403 without token, 200 with) is exactly as
  recorded. Disposition is **confirms**, not refutes: the 401 was fixed by canopy #414/#415 (rolled out + verified live
  2026-07-01) — F-B independently re-confirms that fix on the running image. The 06-29 audit / 06-30 design were the fix's
  precursors; the recon ledger's "not implemented" read reflected the notes alone, without the #415 rollout.

## 12. Appendix — key references

- **Topology / ops / secrets flow:** `juniper-deploy/docker-compose.yml`, `juniper-deploy/Makefile`,
  `juniper-deploy/scripts/{prepare_secrets.bash,wait_for_services.sh,doctor.sh}`.
- **Canopy surface:** `juniper-canopy/src/frontend/dashboard_manager.py` (layout + callbacks),
  `juniper-canopy/src/main.py` (FastAPI routes), `src/frontend/components/*.py` (panels),
  `src/tests/ui_contract/control_manifest.py` (the closest thing to an authoritative implemented-control list),
  `util/ui_control_graph.py` (L1 lint).
- **Docs claims:** `juniper-canopy/docs/USER_MANUAL.md`, `README.md`, `AGENTS.md`; A1/selection designs in `juniper-ml/notes/`.
- **Feature flags:** `juniper-canopy/src/settings.py` (`JUNIPER_CANOPY_*`: `enable_ws_control_buttons`,
  `browser_control_auth_enabled`, `csrf_enabled`, `demo_mode`, `*_service_url`, `max_connections_per_ip`, WS timeouts).
- **Inter-service endpoints:** cascor `src/api/routes/*` (`/v1/training/*`, `/v1/metrics*`, `/v1/network*`, `/v1/snapshots*`,
  WS `/ws/{training,control,v1/workers}`); data `juniper_data/api/routes/*` (`/v1/datasets*`, `/v1/generators*`);
  recurrence routers (`/v1/train`, `/v1/training/status`, `/v1/predict`, `/v1/crossval`).

> All `file:line` and endpoint citations here are source-grounded and re-verified in Phase 1 (§9) before the report is authored.
> Pilot observations (§11) are live-verified this session and re-checked adversarially in Phase 1.
