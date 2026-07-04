# Round 0 Proposal R0-02: Security Hardening

**Specialization**: WebSocket security, CSWSH, Origin validation, auth model
**Author**: Round 0 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Initial proposal — pre-consolidation
**Source doc**: `notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 1. Scope

This proposal defines the security hardening work required to migrate the
canopy dashboard from REST polling to WebSocket push without introducing
(or failing to close) a set of P0 vulnerabilities around the canopy
`/ws/training` and `/ws/control` endpoints. The work is gated as
**Phase B-pre** in the architecture doc (§9.2) and must land before
Phase D (training-control buttons over WebSocket) and, more conservatively,
before Phase B ships the new browser→canopy attack surface.

In scope:

- Cross-Site WebSocket Hijacking (CSWSH) on `ws://canopy:8050/ws/control`
- Origin header validation parity between canopy and cascor
- Authentication / session-binding for `/ws/*` endpoints
- CSRF token strategy for the first WebSocket frame
- Message-level authorization (per-action) and schema validation
- Per-frame size limits, per-IP connection caps, rate limits
- Audit logging for all control-plane messages
- Interaction between the new security controls and the replay / resume
  protocol (GAP-WS-13), the `server_instance_id` UUID, and the sequence
  number envelope
- Threat modelling for browser → canopy, canopy adapter → cascor, and
  browser → cascor (demo / direct-connect topologies)

Out of scope (owned by other R0 agents):

- Plotly `extendTraces`, `dcc.Store`, `ws-metrics-buffer` wiring
- Cascor broadcaster / `WebSocketManager` backpressure internals
- `juniper-cascor-client` `set_params` method surface and SDK ergonomics

Security hardening of data-plane performance (e.g., `permessage-deflate`,
chunking) is also out of scope except where it intersects with DoS
exposure.

---

## 2. Source-doc cross-references

All identifiers below refer to
`notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` v1.3.

### 2.1 Threat and risk IDs (primary)

| Identifier | Source section | Topic |
|---|---|---|
| P0 security caveat | §1.3 | CSWSH on canopy `/ws/control`, `/ws/training` |
| M-SEC-01 (P0)    | §2.9.2 | Canopy `/ws/*` Origin allowlist |
| M-SEC-01b (P0)   | §2.9.2 | Cascor `/ws/*` Origin allowlist parity |
| M-SEC-02 (P0)    | §2.9.2 | Auth model — cookie session + CSRF first-frame |
| M-SEC-03 (P0)    | §2.9.2 | Per-frame size limits on every WS endpoint |
| M-SEC-04 (P1)    | §2.9.2 | Per-IP connection caps + auth timeout |
| M-SEC-05 (P1)    | §2.9.2 | Command rate limiting |
| M-SEC-06 (P3)    | §2.9.2 | Opaque auth-failure close-reason text |
| M-SEC-07 (P3)    | §2.9.2 | Logging scrubbing allowlist |
| M-SEC-08 (deferred) | §12.2 | Subdomain bypass / CSP header follow-up |
| M-SEC-09 (deferred) | §12.2 | Constant-time API key comparison |
| RISK-15 (High)   | §10    | CSWSH attack exploits missing Origin validation |
| RISK-07 (Low)    | §10    | 50-connection global cap insufficient per-IP |
| RISK-11 (High)   | §10    | Silent data loss via drop-oldest (policy) |

### 2.2 GAP-WS items in scope for this proposal

| GAP ID | Severity | Security relevance |
|---|---|---|
| GAP-WS-22 | P2 | Protocol error responses (close codes, envelope) |
| GAP-WS-27 | P1 | Per-IP connection caps / DoS protection — direct M-SEC-04/05 hook |
| GAP-WS-13 | P1 | Reconnect protocol introduces `server_instance_id` + replay buffer; security controls must not break it |
| GAP-WS-12 | P1 | Heartbeat / ping-pong — must not bypass auth |
| GAP-WS-32 | P2 | Per-command timeouts + `command_id` correlation — interacts with M-SEC-05 rate limits |
| GAP-WS-30 | P3 | Reconnect backoff jitter (mitigates reconnect-flood amplification) |
| GAP-WS-31 | P2 | Unbounded reconnect (interacts with per-IP cap pressure) |
| GAP-WS-19 | P2 | `close_all()` lock — relevant to correctness of shutdown auth state |
| GAP-WS-01 | P1 | SDK `set_params` — must not bypass M-SEC-02 auth headers |
| GAP-WS-09 | P2 | Cascor-side `set_params` integration test — security regression cases |

### 2.3 Phase ordering

Per §9.2 and §9.12: critical path is **A ‖ B-pre → B → C ‖ D**. Phase B-pre
(this proposal) is a hard prerequisite for Phase D. This proposal
additionally argues (see §9) that Phase B-pre is a *soft* prerequisite for
Phase B too: shipping the browser bridge (GAP-WS-02..05) without Origin
validation exposes the CSWSH surface for however long it takes Phase B-pre
to merge after it. Land them together or in the correct order.

---

## 3. Threat model

### 3.1 CSWSH (P0)

**Attack**: a user is logged into the canopy dashboard at
`http://localhost:8050` in Tab A. In Tab B they visit an attacker-controlled
page (`http://evil.example`). The attacker-page runs:

```html
<script>
  const ws = new WebSocket("ws://localhost:8050/ws/control");
  ws.onopen = () => {
    ws.send(JSON.stringify({command: "set_params",
                            params: {learning_rate: 999.0}}));
    ws.send(JSON.stringify({command: "stop"}));
  };
</script>
```

The browser's Same-Origin Policy **does not** prevent cross-origin WebSocket
connections. It *does* restrict cross-origin fetch/XHR, and preflight blocks
custom headers, but for WebSocket the browser:

1. Sends the `Origin: http://evil.example` header automatically.
2. Attaches any `http://localhost:8050` cookies that match
   `SameSite=Lax|None` (the default for most apps is `Lax`; any cookie
   without `SameSite=Strict` is fair game for a cross-site WebSocket
   upgrade, because the upgrade is a top-level navigation-style request
   from the browser's cookie-policy point of view).

If the canopy server does not check `Origin`, the attacker now has an
authenticated WebSocket into `/ws/control` and can issue `start`, `stop`,
`reset`, `set_params`, or (Phase D) button-equivalent commands. From the
server logs it looks like a legitimate dashboard action.

**Blast radius**:

- **Training state**: `stop`, `reset`, `start` on an in-progress training
  run — the user loses hours of work. `reset` is destructive.
- **Parameter injection**: `set_params` with a nonsense `learning_rate` can
  cause divergence, a degenerate network, or the `init_output_weights`
  literal bypass if validation is weak (§2.9.1 threat table item 5).
- **DoS amplification**: an attacker who can call `start` repeatedly with
  large networks can exhaust GPU/CPU on the server.
- **Information exfiltration**: server→client WS events include full state
  payloads (parameter values, topology), which the attacker can exfiltrate
  to their own analytics endpoint.

**Severity**: P0 in the source doc, RISK-15 at `High/Medium`. This
proposal concurs.

**Current status**: VULNERABLE on canopy `/ws/training` and `/ws/control`.
Cascor's `/ws/v1/workers` already has Origin-reject (§2.1), but cascor's
`/ws/training` and `/ws/control` do NOT — see M-SEC-01b.

### 3.2 Unauthenticated control-plane access

**Attack 1 — No auth at all**: any user on the local machine (or any
machine that can reach port 8050) can open a WebSocket and issue control
commands. This is the case today for `ws://localhost:8050/ws/control`.
For a single-user developer machine this is acceptable-by-convention, but
it is NOT acceptable the moment canopy is deployed on a multi-user host,
a shared VM, or a lab cluster.

**Attack 2 — Header-omission regression via a test fake**: §2.9.1 threat
table item 4. Today some unit tests stub out authentication entirely and
exercise handler logic against a fake WebSocket object. If canopy ever
stops sending the `X-API-Key` header (refactor bug), the test suite will
still pass because the fake doesn't check the header. The regression only
manifests against a real cascor.

**Attack 3 — Cookie leakage via bearer-in-localStorage**: a common
alternative to cookie-session auth is storing a bearer token in
`localStorage` and sending it in the WebSocket subprotocol. This makes the
token XSS-exfiltratable — a single XSS on any page served by the
`localhost:8050` origin can read the token and replay it. The source doc
(§2.9.2 M-SEC-02 cookie refinement) explicitly rejects this pattern.

**Attack 4 — Browser WebSocket API cannot set custom headers**: this is
the underlying reason the cascor `X-API-Key` pattern cannot be transplanted
to canopy. The JS `WebSocket` constructor refuses custom headers on the
upgrade; any auth mechanism for browser-originated WebSockets must use
cookies (automatic), subprotocol (visible in URL-ish ways), or a
post-upgrade first-frame handshake. §2.9.2 M-SEC-02 chooses cookie +
first-frame CSRF.

### 3.3 Message-shape exploitation / schema confusion

**Attack 1 — Envelope asymmetry**: per §3.0 and GAP-WS-20, the
client→server and server→client envelopes differ. The client sends
`{command, params}`; the server sends `{type, timestamp, data}`. A handler
that confuses the two shapes is a bug, but specifically a
*security*-relevant bug because a malicious client could send the
server-shape (`{type: "command", data: {command: "set_params", ...}}`)
and a lenient parser might accept it AND log it differently from the
canonical shape — obscuring the audit trail. The controls in §4.4 below
mandate a strict union parser that rejects unknown envelope shapes.

**Attack 2 — `init_output_weights` literal bypass**: §2.9.1 threat table
item 5. The source doc confirms validation is in place at
`juniper-cascor/src/api/models/network.py:23` as `Literal["zero", "random"]`
Pydantic. The risk is that future params added to `set_params` may not
go through the same validator — e.g., if the SDK `set_params` (GAP-WS-01)
or the canopy adapter adds a free-form `str` field. This proposal mandates
a per-key schema whitelist (§4.4).

**Attack 3 — JSON-parse DoS**: a deeply nested JSON payload (e.g.,
`{"a": {"a": {"a": ... }}}` 10,000 levels deep) can exhaust stack or
memory during parsing. Pydantic v2 has a `max_depth` guard if configured;
the default may not. Explicit size-capping (M-SEC-03) catches the
amplitude case but not the depth case. Depth-capping needs a separate
guard.

**Attack 4 — Integer / float out-of-range**: `set_params` with
`learning_rate: 1e308` (or `nan`/`-inf`/`+inf`) that bypasses
range-checks. Pydantic `float` accepts all of those unless explicitly
constrained with `ge=/le=/`. Per-key range validation is mandatory.

**Attack 5 — `command_id` collision / UUID spoofing**: GAP-WS-32 introduces
client-generated `command_id` for correlation. A malicious client can
collide with a legitimate client's command_id and cause the server to
attribute its own command-response to someone else. This is a tenant-
isolation concern rather than a single-user concern. **Control**:
`command_id` is scoped **per-connection only**, never globally keyed. The
server's in-flight command table is `Dict[WebSocket, Dict[command_id,
pending]]`, never `Dict[command_id, pending]`. Two clients choosing the
same UUID is a no-op because the lookup is keyed by the connection object
first. Document this invariant in the handler.

### 3.4 Replay attacks against the replay buffer

The §6.5 GAP-WS-13 reconnect protocol introduces a `resume` frame:
`{type: "resume", data: {last_seq: N, server_instance_id: "<uuid>"}}`.

**Attack 1 — Forge a low `last_seq` to flood a connection**: if the
attacker can connect, they can send `{last_seq: 0}` and force the server
to iterate its entire 1024-event ring buffer and dispatch every event.
Repeat once per second → amplified outbound bandwidth. Mitigation: the
per-connection command rate limit (M-SEC-05) covers this, but `resume` is
not a "command" in the `{command, params}` sense — it's a first-frame
handshake. We need an explicit rule: **one successful `resume` per
connection**. A second `resume` on the same connection closes it with
code 1008.

**Attack 2 — Forge `server_instance_id`**: if the attacker can read the
UUID from a previously-open tab (or from logs), they can include it in
their own `resume` frame. This does not grant new privileges — the server
still authenticates the connection the normal way — but it bypasses the
"your connection is new, start fresh" safety. Mitigation: `resume` is
idempotent against the replay buffer, so there is no privilege escalation.
Documented as accepted risk.

**Attack 3 — Replay-buffer exhaustion (unbounded memory)**: if the buffer
is `maxlen=1024` per `WebSocketManager`, an attacker cannot grow it. The
`maxlen` contract in §6.5 is the mitigation. Verify the `deque(maxlen=…)`
is set at construction, not in a later path that could be skipped.

**Attack 4 — Cross-client replay (tenant crossing)**: the replay buffer
is shared across all WS clients; any authenticated client can `resume`
and receive events that were emitted while a *different* client was
connected. For single-tenant canopy deployments this is fine (both clients
represent the same user). For any multi-tenant deployment this is a
data-mixing defect. M-SEC-04 per-IP caps do NOT solve this — two users
behind the same NAT are indistinguishable. Documented for open-question
§11 follow-up; multi-tenant cascor deployments require per-session
replay buffers.

### 3.5 DoS and resource exhaustion

**Attack 1 — Single-attacker connection exhaustion**: cascor's 50-conn
global cap (§2.2) and canopy's (unset) cap can be saturated by a single
attacker IP. Mitigation is M-SEC-04 per-IP cap (default 5/IP,
configurable).

**Attack 2 — Large inbound frame**: `control_stream.py:23` caps inbound
to 64 KB. Training stream inbound is theoretically `ping`/`pong` only but
the framework allows arbitrary messages, so it MUST be capped too. Canopy
`/ws/training` and `/ws/control` in `main.py:355,417` must be capped.
M-SEC-03.

**Attack 3 — Slow-client amplification (inbound-half)**: an attacker that
sends 1 byte per second over a WebSocket can hold a connection slot open
indefinitely. The auth-timeout in M-SEC-04 (close in 5 s if no valid auth
frame) mitigates the pre-auth version. Post-auth, the per-connection idle
timeout needs to be explicit (this proposal adds **M-SEC-10** — idle
timeout — see §4.5).

**Attack 4 — Slow-client amplification (outbound-half)**: covered by
GAP-WS-07 / Phase E, not this proposal. Noted because the security fix
(per-send timeout 0.5 s) removes a DoS vector even though it's classified
as a correctness fix.

**Attack 5 — Reconnect storm amplification**: GAP-WS-30 jitter and
GAP-WS-31 uncapped reconnect interact — without jitter, 100 dashboards
synchronized-reconnect after a cascor restart. With per-IP cap of 5 and
uncapped reconnects, a malicious 100-dashboard farm from a single IP gets
95 rejections on each wave, amplifying log volume. This is acceptable
(rejections are cheap) but worth a note.

**Attack 6 — Command-response queue exhaustion**: if the attacker can send
commands faster than the server processes them, the pending-command queue
grows. M-SEC-05 rate-limit (10 cmd/s per connection) caps this at the
source.

**Attack 7 — Log injection via Origin / User-Agent / close-reason**:
CRLF bytes in `Origin: http://evil\r\n[FAKE LOG]`. An un-escaped audit
logger writes the forged line to disk as if from a new log event,
confusing post-incident forensics. **Control**: the audit logger must
escape `\r\n\t` in every user-controlled field (see §4.6).

**Attack 8 — TLS termination in the reverse proxy layer**: canopy is
assumed to run behind nginx or traefik in production. If TLS is
terminated at the proxy but the canopy ↔ proxy hop is plaintext HTTP,
an attacker with local network access can read cookies in transit. This
is the reverse-proxy operator's responsibility; document in the
deployment guide. Canopy should refuse to set `Secure` cookies when it
sees an HTTP-only request and warn loudly at startup if
`X-Forwarded-Proto: https` is not forwarded.

### 3.6 Canopy-adapter → cascor trust boundary

The canopy adapter (`cascor_service_adapter.py`) is a long-lived WebSocket
client of cascor. It holds an `X-API-Key` from canopy config. Threats:

- **Credential theft**: if an attacker gains RCE on the canopy host, they
  can read the config file and obtain the cascor API key. Mitigation is
  conventional secret handling (env vars, mode 0600 files) — not new.
- **Malformed server frames**: a compromised cascor can send malicious
  frames to canopy's adapter. The adapter must treat cascor's output as
  untrusted and enforce its own per-frame size + schema validation. This
  proposal includes a new **M-SEC-11** — adapter inbound validation.
- **Adapter-reconnect key rotation**: if the cascor API key rotates, the
  adapter must reconnect with the new key. The current reconnect backoff
  `[1, 2, 5, 10, 30]` (§2.5) is not key-aware. Out of scope but flagged.

### 3.7 Browser → cascor direct exposure (demo / direct-connect)

In demo mode or direct-connect topologies, the browser may open a
WebSocket directly to cascor (bypassing canopy). In that case:

- cascor MUST enforce M-SEC-01b Origin allowlist (cascor Origin parity).
- cascor cannot use canopy's cookie session, so it falls back to the
  existing `X-API-Key` pattern via subprotocol (see §4.2 for the "header
  in subprotocol" trick).
- The CSRF first-frame pattern still applies for defence in depth.

---

## 4. Recommended controls

Each control maps to one or more M-SEC-NN identifiers from §2.9.2. Where
this proposal adds a new control, it is labelled **M-SEC-10+** and flagged
for reviewer awareness.

### 4.1 Origin header validation

**Control**: reject any WebSocket upgrade whose `Origin` header is not in
the configured allowlist. Applies to:

| Endpoint | File | M-SEC |
|---|---|---|
| `ws://<canopy>/ws/training` | `juniper-canopy/src/main.py` (~line 355) | M-SEC-01 |
| `ws://<canopy>/ws/control`  | `juniper-canopy/src/main.py` (~line 417) | M-SEC-01 |
| `ws://<cascor>/ws/training` | `juniper-cascor/src/api/websocket/training_stream.py` | M-SEC-01b |
| `ws://<cascor>/ws/control`  | `juniper-cascor/src/api/websocket/control_stream.py` | M-SEC-01b |
| `ws://<cascor>/ws/v1/workers` | already done at `worker_stream.py:41-44` | (reference) |

**Allowlist default** (canopy):

```
["http://localhost:8050", "http://127.0.0.1:8050",
 "https://localhost:8050", "https://127.0.0.1:8050"]
```

**Allowlist default** (cascor, for the demo / direct-connect case):

```
["http://localhost:8050", "http://127.0.0.1:8050",
 "http://localhost:8201", "http://127.0.0.1:8201"]
```

The cascor default additionally allows the localhost-cascor origin so
that dev-tooling (cascor's own OpenAPI/Swagger playground WebSocket demo,
if any) still works.

**Configurable via**:

- `Settings.allowed_origins: list[str]` (both repos). Semicolon- or
  JSON-list encoded via env var `JUNIPER_WS_ALLOWED_ORIGINS`.

**Rejection mechanics**:

- On non-match, respond to the HTTP upgrade with **HTTP 403 Forbidden**
  where the ASGI framework supports it, else close the TCP with code
  400. Starlette's WebSocket upgrade path calls `ws.close()` which
  produces a 1006/abnormal on the client side; Starlette 0.37+ supports
  `WebSocketDisconnect` with a proper HTTP status via
  `ws.accept(); ws.close(code=1008)` or via raising an
  `HTTPException(403)` before `ws.accept()`. Verify at implementation
  time and document the exact close semantics.
- Log the rejected origin at WARNING level: `origin=<Origin>,
  remote_addr=<ip>, path=<path>, user_agent=<ua>` (M-SEC-07 redaction
  applies; `\r\n\t` escaped per §4.6 rule 10).
- Do NOT advertise the allowlist in the rejection (no leak of config).
- Emit a prom counter `canopy_ws_origin_rejected_total{endpoint}`.
- **Audit log**: origin rejections ARE audit-logged as
  `event: ws_auth, result: origin_rejected`. They are auth events for
  forensic purposes even though no auth frame was exchanged.

**Shared helper**: per §2.9.2 M-SEC-01b, extract the existing
`worker_stream.py:41-44` pattern into `juniper-cascor/src/api/websocket/
origin.py::validate_origin(ws, allowlist) -> bool`. Canopy imports a
sibling helper or vends its own (the cascor module is not a cross-repo
dependency). Both helpers share a unit-test matrix (see §7).

**Case and protocol handling**:

- Compare Origins **case-insensitively on scheme and host**, case-
  sensitively on path (paths don't appear in `Origin` but belt-and-
  suspenders). `http` != `https` is an exact match by convention —
  configurations list both if both are allowed.
- Trailing slash in the `Origin` header is not conventional but some
  buggy clients send one; strip it before compare.
- Port is significant and part of the match.
- `null` origin (file://, sandboxed iframe) is always rejected.
- `*` in the allowlist is explicitly NOT supported (belt-and-suspenders
  against ops misconfiguration).

**Interaction with reverse proxies**: if canopy is deployed behind nginx /
traefik with path-based routing, the browser's `Origin` will still be the
external host, not `localhost`. Document this: when deploying, the ops
runbook must add the public origin (e.g., `https://dashboards.example`)
to the allowlist.

### 4.2 Authentication / session binding

**Control**: every `/ws/*` handler authenticates the connection before
any control action is accepted. Two-layer model:

1. **Handshake cookie check** (pre-accept): the browser sends
   `Cookie: session=<opaque-id>` automatically on upgrade. Canopy's
   session store validates it (reuse canopy's existing session middleware
   if one exists; otherwise add one — see §5.3 below). Session cookie
   attributes MUST be:

   ```
   HttpOnly; Secure; SameSite=Strict; Path=/
   ```

   `SameSite=Strict` is the second-line defence against CSWSH (the
   first being Origin validation). Browsers refuse to send
   `SameSite=Strict` cookies on cross-origin WebSocket upgrades, so the
   CSWSH request loses its credentials and is rejected at the auth
   layer even if Origin validation is misconfigured. Defence in depth.

2. **CSRF first-frame check** (post-accept): within 5 seconds of accept
   (see M-SEC-04 auth-timeout), the client MUST send its first frame:

   ```json
   {
     "type": "auth",
     "csrf_token": "<opaque-token>"
   }
   ```

   The server compares `csrf_token` against a token previously minted
   for the authenticated session. Mismatch or absence → close with code
   `4001 "Authentication failed"` (opaque per M-SEC-06).

   **How the client gets the token**: a `/api/csrf` REST endpoint
   (canopy) that returns `{csrf_token: "<opaque>"}` for the
   authenticated session. The response body is read by the Dash page
   template JS and stashed in a JS variable (**NOT localStorage** —
   the token must not be persistable, to limit XSS impact). The
   `window.cascorWS` client reads it from the variable on each connect.

   **Token lifetime**: the token is valid for the session and rotates
   on:
   - Session login / logout
   - Every 1 hour of activity (sliding)
   - Server restart (new `server_instance_id`)
   - Any auth close from the server (close code 4001)

   On rotation, the WebSocket closes and the client fetches a new
   token before reconnecting. This makes tokens short-lived enough
   that cross-tab token theft is bounded.

   **Token comparison**: the server compares tokens with
   `hmac.compare_digest(expected, actual)` — constant-time — to avoid
   a timing side channel that could leak bytes of a token over many
   attempts. **Never** use `==` on the token.

   **Session fixation prevention**: when a new session is established
   (first request from a new browser, or on login if canopy ever adds
   auth), generate a fresh session ID. Never reuse a client-supplied
   session cookie. Starlette's SessionMiddleware handles this
   correctly by default; verify.

   **Token minting**: `secrets.token_urlsafe(32)` (43-char base64url,
   192 bits of entropy). Stored on the session under
   `session["csrf_token"]`. The token is scoped to the session, not
   global.

**Local-dev escape hatch** (§2.9.2):
`Settings.disable_ws_auth: bool = False`. When True, Origin validation
and cookie checks are skipped. MUST default to False in production.
Logging this flag at INFO on startup is mandatory so operators see when
auth is disabled. A `juniper-deploy` CI guardrail should fail if the
production compose file sets it True.

**Why not subprotocol-based auth**: passing the token in
`Sec-WebSocket-Protocol` is possible and works around the custom-header
restriction, but the token appears in server access logs (same row as
the request), browser dev-tools network panel, and any logging proxy.
Cookies (HttpOnly) are strictly better for browser clients.

**Why not bearer tokens**: (§2.9.2 refinement). Bearer tokens in
`localStorage` are XSS-exfiltratable. Rejected.

**Cascor (non-browser) case**: cascor continues to use `X-API-Key` as
today (it's a custom HTTP header and the canopy adapter is a Python
`websockets` client which CAN set custom headers). The CSRF first-frame
pattern is applied ON TOP of the API key for the browser-direct demo
topology. In pure server-to-server (canopy adapter → cascor), the
adapter sends a synthetic first-frame `{type: "auth", csrf_token: "<api-
key-hash>"}` or skips it behind `Settings.disable_ws_auth=True` at the
cascor side. **Decision point**: recommend adapter sends a synthetic
auth frame so the cascor handler logic is uniform; see open question
§11-sec-1 below.

### 4.3 Message-level authorization (per-action)

**Control**: each control-plane action is authorized against the
session's permissions. Minimum permissions for Round 0 scope:

| Action | Permission required |
|---|---|
| `start`, `stop`, `pause`, `resume` | `training:control` |
| `reset` | `training:destructive` |
| `set_params` (hot keys)  | `training:control` |
| `set_params` (cold keys) | `training:params_cold` |
| `resume` (replay first-frame) | `ws:connect` (implicit with auth) |
| (future) `delete_network` | `training:destructive` |

The permission strings are abstract — canopy's existing user model (if
any) maps them to roles. Today canopy is single-user so every
authenticated session has all permissions; the permission-string layer
exists so that **adding roles later does not require re-plumbing the
handler**.

**Where the check happens**: `control_stream_handler` in canopy calls
`require_permission(session, "training:control")` before dispatching to
the adapter. Reject with `{type: "command_response", data: {status:
"forbidden", command: "<cmd>"}}` (do not close the connection on
permission denial — the connection may still be authorized for other
actions).

**Hot/cold param split**: §5 of the source doc defines the hot/cold param
split. For security purposes, the cold set is the destructive one
(reset-equivalent changes: `max_iterations`, `max_hidden_units`). Require
an explicit `training:params_cold` permission for the cold set.

### 4.4 Schema validation & message size limits

**Control 1 — Per-frame size cap** (M-SEC-03):

| Endpoint | Current | Target | Enforcement |
|---|---|---|---|
| cascor `/ws/control` inbound | 64 KB (verified at `control_stream.py:23`) | 64 KB (unchanged) | keep |
| cascor `/ws/training` inbound | unset | 4 KB (ping/pong only) | add `max_size=4096` |
| cascor `/ws/v1/workers` inbound | per existing worker pattern | n/a | out of scope |
| canopy `/ws/control` inbound | unset | 64 KB | add |
| canopy `/ws/training` inbound | unset | 4 KB | add |
| canopy `/ws/*` outbound | unset | 128 KB | add (note: topology msg can be larger — GAP-WS-18) |
| cascor `/ws/*` outbound | unset | 128 KB | interacts with GAP-WS-18 chunking |

All caps are enforced at the framework level by passing `max_size=<n>` to
the FastAPI/Starlette WebSocket `receive_*()` call. On overflow, close
with code 1009 (Message Too Big).

**Control 2 — JSON depth cap**: set `json.loads(..., parse_constant=_no_nan)`
to reject `NaN`/`Infinity`, and use a custom depth-limiting parser (or
Pydantic v2 with `model_config = ConfigDict(max_depth=16)` if available)
to reject deeply nested payloads. Reject with close 1003 (Unsupported
Data) per the GAP-WS-22 error table.

**Control 3 — Per-key Pydantic models**: every `set_params` key has a
typed Pydantic field with explicit range / literal constraints. The
whitelist:

```python
class SetParamsRequest(BaseModel):
    learning_rate: Optional[float] = Field(default=None, gt=0.0, le=10.0)
    candidate_learning_rate: Optional[float] = Field(default=None, gt=0.0, le=10.0)
    patience: Optional[int] = Field(default=None, ge=0, le=1_000_000)
    correlation_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    candidate_epochs: Optional[int] = Field(default=None, ge=1, le=10_000)
    output_epochs: Optional[int] = Field(default=None, ge=1, le=10_000)
    init_output_weights: Optional[Literal["zero", "random"]] = None
    max_epochs: Optional[int] = Field(default=None, ge=1, le=10_000_000_000)
    max_iterations: Optional[int] = Field(default=None, ge=1, le=1_000_000)
    max_hidden_units: Optional[int] = Field(default=None, ge=1, le=10_000)
    candidate_pool_size: Optional[int] = Field(default=None, ge=1, le=64)
    # ... complete the list from §5 latency matrix

    model_config = ConfigDict(extra="forbid")
```

`extra="forbid"` means any unknown key triggers a validation error that
is converted into `{command_response, status: "error", error: "unknown
parameter: <key>"}`. No silent filtering — the caller gets a clear
rejection (which makes integration bugs surface fast).

**Control 4 — Command envelope validation**: inbound messages on
`/ws/control` must match one of the allowed shapes:

- Current: `{command: str, params: dict}`
- Future (GAP-WS-20, normalized): `{type: "command", timestamp: float,
  data: {command: str, params: dict}}`
- First-frame auth: `{type: "auth", csrf_token: str}`
- First-frame resume: `{type: "resume", data: {last_seq: int,
  server_instance_id: str}}`

Anything else → close with 1003 (GAP-WS-22).

**Control 5 — Outbound schema validation on the adapter**: per §3.6, the
canopy adapter validates cascor's inbound frames with its own Pydantic
models. Budget this as M-SEC-11 (new).

**Control 6 — Close-reason text must not leak internal state**: on any
server-side exception handler that closes a WebSocket, the `reason`
string must be a fixed constant, NOT the exception message. Python's
default `ws.close(code=1011, reason=str(e))` leaks stack-trace
fragments. Wrap with an error-mapping layer that returns canonical
strings: `"Internal error"`, `"Invalid frame"`, `"Rate limited"`,
`"Authentication failed"`, `"Forbidden"`, `"Too many connections"`.
Log the real exception server-side at ERROR level.

### 4.5 Rate limiting and connection caps

**Control 1 — Per-IP connection cap** (M-SEC-04): implemented in
`WebSocketManager` on both sides. Default 5 connections / IP,
configurable via `Settings.ws_max_connections_per_ip`. The concurrency
contract is spelled out in §2.9.2 M-SEC-04 (already in source doc) — a
dict `_per_ip_counts: Dict[str, int]` guarded by `_lock`, decremented in
a `finally` block. This proposal adopts it verbatim.

**Control 2 — Global cap retained**: the existing 50-connection global
cap stays. Per-IP is an additional constraint, not a replacement.

**Control 3 — Auth-timeout** (M-SEC-04): if the client does not send a
valid auth frame within 5 seconds, close with code 1008 (Policy
Violation). This is enforced with `asyncio.wait_for(ws.receive_text(),
timeout=5.0)` in the handler.

**Control 4 — Per-connection command rate limit** (M-SEC-05): 10
commands/second, leaky-bucket. Excess commands respond with
`{type: "command_response", data: {status: "rate_limited",
retry_after: 0.3}}` and do not execute. Implemented as a small
homegrown leaky-bucket rather than pulling in `slowapi` (fewer deps).
Per-connection, not per-IP, so that a well-behaved tab from a shared
IP is not starved by an abusive tab.

**Leaky-bucket parameters**:
- Capacity: 10 tokens
- Refill rate: 10 tokens/second (one token per 100 ms)
- Initial fill: full (10 tokens) — allows a brief burst on connect
- On zero tokens: reject with `rate_limited` response; do NOT close

**Definition of "command" for rate-limit counting**:
- Any inbound frame that parses as a `CommandFrame` (§4.4 control 4)
  consumes one token.
- Auth first-frame (§4.2): does NOT consume a token (pre-rate-limit).
- Resume first-frame (§4.7): does NOT consume a token.
- `ping` application-level frame (GAP-WS-12): does NOT consume.
- Malformed JSON / unknown envelope: does NOT consume (close anyway
  per GAP-WS-22).
- **Rationale**: rate-limiting non-command frames creates confusing
  edge cases and is not the threat model.

**Split counting by command type** (refinement from §8.6 risk): to
keep slider UX smooth, allow `set_params` to consume from a separate
20-token / 20-rps bucket, while `start|stop|reset|pause|resume` use the
default 10-token bucket. Two buckets per connection. Optional; decide
during implementation if single-bucket starvation is observed.

**Control 5 — Idle timeout** (**M-SEC-10, new**): if the server receives
no client frames for 120 seconds AND no server→client messages have been
sent for 120 seconds (i.e., idle in both directions), close with 1000
(Normal Closure). Heartbeat (GAP-WS-12) will dominate this — with a 30 s
ping interval, the idle timer is effectively unreachable unless the
client stops responding. The idle close is a safety net against leaked
connections.

**Control 6 — Resume frame rate limit** (new, micro-control): at most
one `resume` frame per connection. A second `resume` is a **protocol**
violation (not a policy violation) → close with code **1003
(Unsupported Data)**. This aligns with the GAP-WS-22 protocol-error
table in §3.2.4 of the source doc.

**Control 7 — Reconnect backoff jitter** (GAP-WS-30, folded in here
because it affects security-relevant attack surface amplification): see
§4.8 below.

### 4.6 Audit logging for control-plane actions

**Control** (**M-SEC-07 extended**, new aspect): every control-plane
WebSocket action is logged to a dedicated audit logger at INFO level.
The audit line format (JSON):

```json
{
  "event": "ws_control",
  "timestamp": "2026-04-11T21:43:00.000Z",
  "session_id": "<hash of session cookie, not the raw cookie>",
  "remote_addr": "127.0.0.1",
  "origin": "http://localhost:8050",
  "endpoint": "/ws/control",
  "command": "set_params",
  "command_id": "<uuid from client>",
  "params_keys": ["learning_rate", "patience"],
  "params_scrubbed": {"learning_rate": 0.005, "patience": 3},
  "result": "ok",
  "seq": 12345
}
```

Rules:

1. **Never log the raw session cookie** — log a SHA-256 prefix (8 chars)
   for correlation across log lines within the same session.
2. **Never log the CSRF token**.
3. Log `params_keys` always; log `params_scrubbed` with the **M-SEC-07
   allowlist** applied. Today's params are non-sensitive, so all keys in
   `SetParamsRequest` are in the allowlist. The allowlist is a single
   Python constant `AUDIT_SCRUB_ALLOWLIST` in the canopy config module;
   keys outside it are logged as `<redacted>`. Document it so that
   future contributors adding a sensitive key (e.g., `api_token`,
   unlikely but possible) MUST update the allowlist or see redaction.
4. Log failures too: `result: "rate_limited"`, `result: "forbidden"`,
   `result: "validation_error"`, `result: "auth_failed"`,
   `result: "origin_rejected"`, `result: "per_ip_cap"`,
   `result: "token_expired"`.
5. Audit log is separate from the application log (different logger name
   `canopy.audit`). This makes retention/rotation independent. If
   canopy ships with a structured-logging config, the audit logger is
   one of its sinks.
6. **Rotation**: audit log rotated daily via
   `logging.handlers.TimedRotatingFileHandler(when="midnight",
   backupCount=90)`. Retention 90 days. Configurable via
   `Settings.audit_log_retention_days`. Compress rotated files
   (`gzip`) to keep disk usage bounded.
7. **Do not audit-log ping/pong** — keeps volume bounded.
8. **Do not audit-log metrics events** — not a control-plane action.
9. **Log `params_before` AND `params_after`** for every `set_params`
   event (both scrubbed). This gives post-incident forensics a diff
   rather than a snapshot. Prefer `{"before": {"learning_rate": 0.01},
   "after": {"learning_rate": 0.005}}` over just `after`.
10. **Escape CRLF/tab in every user-controlled string field**
    (`origin`, `user_agent`, command strings, error messages). Use
    `repr()`-style escaping or JSON encoding at log-write time. This is
    a direct mitigation for §3.5 attack 7 log injection.
11. **Log the user-agent string verbatim** (escaped per rule 10). It
    is a forensics signal — a CSWSH probe from `curl` looks different
    from one driven by a headless Chromium.

**Interaction with Prometheus**: in addition to audit logs, export
counters:

- `canopy_ws_auth_failure_total{reason}` — `reason` ∈ {origin_rejected,
  missing_cookie, invalid_csrf, missing_csrf, timeout}
- `canopy_ws_command_total{command, status}`
- `canopy_ws_rate_limited_total`
- `canopy_ws_per_ip_rejected_total`
- `canopy_ws_origin_rejected_total`
- `canopy_ws_frame_too_large_total`

These feed operational dashboards. A spike in `canopy_ws_origin_rejected
_total` is a live CSWSH probe; ops should alert on it.

Additional histogram:

- `canopy_ws_auth_latency_ms` — time from upgrade-accept to
  successful auth-frame processing. Buckets at 10/50/100/250/500/
  1000/2500/5000 ms. Feeds §5.6 latency instrumentation (GAP-WS-24)
  for security visibility — a sudden increase in auth latency is an
  early indicator of a brute-force probe or a session-store problem.

### 4.7 Interaction with the replay / resume protocol

Per §6.5 GAP-WS-13, the reconnect protocol sends a `{type: "resume",
data: {last_seq, server_instance_id}}` as the first frame. This
conflicts with §4.2 which says the first frame must be
`{type: "auth", csrf_token}`.

**Resolution**: the auth frame comes first, then the resume frame.
Sequence:

```
1. Client opens WebSocket; server accepts upgrade (Origin OK, cookie OK).
2. Client sends {type: "auth", csrf_token: "<opaque>"}.
3. Server validates CSRF; on fail, close 4001.
4. Server sends {type: "connection_established", data: {connections: N,
   server_instance_id: "<uuid>", server_start_time: <float>}}.
5. Client sends {type: "resume", data: {last_seq: N,
   server_instance_id: "<uuid>"}}   ← optional, only on reconnect
   — OR —
   Client waits for normal live stream (first connect, no resume).
6. Server replays events with seq > last_seq (or rejects per §6.5 rules).
7. Live streaming continues.
```

**Five-second budget**: the auth timeout (M-SEC-04) applies to step 2
only. Step 5 (resume) is not auth-timed — the connection is already
authenticated. If the client never sends a resume frame, it is treated
as a fresh connect (no replay).

**Race with live events**: between steps 4 and 6, cascor may emit live
events (someone is training on the server concurrently). The server must
buffer outbound events until either step 6 completes or step 5 is
skipped. This is a small (<100 ms) hold; implementation is a
`pending_outbound: deque` on the per-connection state that flushes
when resume-or-skip is resolved. Document the buffer cap (e.g., 64
events) and what happens on overflow (close 1013 — "Resume handshake
timeout").

**Security-relevant**: the `server_instance_id` UUID is minted once at
cascor startup. A client that presents a stale UUID gets
`resume_failed: server_restarted` and falls back to REST snapshot. This
is **not** a security control per se — it's a correctness control — but
it matters because a malicious client that guesses or steals a UUID
does not gain privileges (the authentication already decided they're
allowed). The UUID is effectively a correctness token, not a secret.
Documented explicitly to prevent future confusion ("we should make the
UUID secret!" — no, don't, it's advisory).

**Interaction with the seq-number contract**: per §6.5.1, the `_next_seq`
increment happens on the event-loop thread under `_seq_lock`. None of
the security controls in this proposal touch that lock. The per-IP
count lock (`_per_ip_counts`) uses `_lock`; the seq counter uses
`_seq_lock`. Order rule: if both are ever held, acquire `_seq_lock`
first (higher-frequency lock acquired first to reduce contention hold
time). This proposal does not introduce any code path that holds both.

### 4.8 Reconnect-flood mitigation and jitter

**Control** (GAP-WS-30 + GAP-WS-31 intersection): reconnect backoff adds
full jitter:

```javascript
delay = Math.random() * Math.min(CAP, BASE * 2 ** attempt);
```

with `BASE=500ms`, `CAP=30s`. This is GAP-WS-30's fix. Uncapped retries
(GAP-WS-31) without jitter amplify a synchronized-reconnect storm after
cascor restart. The jitter is the security-relevant part here — without
it, a reboot of cascor produces simultaneous reconnects that look like
a DoS from the server's POV.

**Control** (new, per-origin cooldown): if the server rejects 10
consecutive upgrade attempts from the same IP with 403 (Origin) or 4001
(auth) inside a 60-second window, add that IP to a soft block list for
5 minutes. Return 429 Too Many Requests for any upgrade attempt during
the block. This is homegrown rate-limiting of the handshake itself;
`slowapi` could do it too. **Caveat**: the block is by IP, which
punishes NAT-sharing users. For the default single-tenant deployment
this is fine; for multi-tenant, make it opt-in.

### 4.9 Summary of controls → M-SEC mapping

| Control | Maps to | Proposal section | Status |
|---|---|---|---|
| Origin allowlist canopy | M-SEC-01 | §4.1 | source doc |
| Origin allowlist cascor parity | M-SEC-01b | §4.1 | source doc |
| Cookie + CSRF first-frame | M-SEC-02 | §4.2 | source doc + refinement |
| Per-frame size caps | M-SEC-03 | §4.4 control 1 | source doc |
| Per-IP conn cap | M-SEC-04 | §4.5 control 1 | source doc |
| Auth timeout | M-SEC-04 | §4.5 control 3 | source doc |
| Per-cmd rate limit | M-SEC-05 | §4.5 control 4 | source doc |
| Opaque close-reason | M-SEC-06 | §4.2 + §4.5 | source doc |
| Logging scrub allowlist | M-SEC-07 | §4.6 | source doc |
| Idle timeout | **M-SEC-10 (new)** | §4.5 control 5 | this proposal |
| Adapter inbound validation | **M-SEC-11 (new)** | §4.4 control 5 | this proposal |
| Audit logger + metrics | §4.6 | §4.6 | this proposal extends M-SEC-07 |
| Message-level authorization | — | §4.3 | this proposal |
| JSON depth cap | — | §4.4 control 2 | this proposal |
| Resume frame rate limit | — | §4.5 control 6 | this proposal |
| Per-origin handshake cooldown | — | §4.8 | this proposal |
| Permission strings hot/cold split | — | §4.3 | this proposal |

---

## 5. Phase B-pre gate definition

Phase B-pre is the security gate between Phase A (SDK) and Phase B
(browser bridge) / Phase D (control buttons). The source doc §9.2 lists
it as 1 day of effort. This proposal concurs on the scope but argues
the effort is closer to **1.5 to 2 days** because of the CSRF token
plumbing and the audit logger wiring, which are not in the original
estimate.

### 5.1 Must-have (P0) acceptance criteria

Phase B-pre is **not shipped** until all of the following are verified:

1. **CSWSH probe fails**:
   - Playwright test opens a page served from `http://evil.local:9999`
     that attempts to open `ws://localhost:8050/ws/control`.
   - Assert the WebSocket close event fires with code != 1000 and no
     `connection_established` frame is received.
   - Assert the canopy server log contains a
     `canopy_ws_origin_rejected_total` increment.

2. **Missing cookie rejected**:
   - Raw WebSocket client (Python `websockets` library) connects
     without the session cookie.
   - Assert close code 4001 within the auth-timeout window.

3. **Missing CSRF first-frame rejected**:
   - Client connects with a valid session cookie but sends a
     non-auth first frame (e.g., a command).
   - Assert close code 4001 with opaque "Authentication failed"
     close-reason text.

4. **Expired CSRF token rejected**:
   - Client connects with an expired token.
   - Assert close code 4001 and reason "token_expired" (per §2.9.2
     cookie-refinement).

5. **Oversized inbound frame rejected** (M-SEC-03):
   - Client sends a 100 KB frame to `/ws/control`.
   - Assert close code 1009.

6. **Per-IP cap enforced** (M-SEC-04):
   - Client opens 6 connections from one IP.
   - Assert the 6th upgrade closes with 1013 ("Per-IP connection cap").
   - Close one; open again; assert the replacement upgrade succeeds.
   - **Lock contract verified**: simultaneous open and close from the
     same IP do not leave a stale count (regression test for the
     `_per_ip_counts` decrement race).

7. **Command rate limit enforced** (M-SEC-05):
   - Client sends 15 commands in 1 second.
   - Assert 10 succeed, 5 return `{status: "rate_limited"}`.
   - No close — the connection stays up.

8. **`Settings.disable_ws_auth=True` bypass works** for local dev:
   - Dev server boots with the flag set; Playwright connects without
     CSRF and without cookie; assert success.
   - Dev server boots with the flag unset; Playwright connects without
     CSRF; assert failure.

9. **Audit log contains the expected entries** for every test above:
   - Rejections: `result: "origin_rejected" / "auth_failed" / ...`
   - Successes: `result: "ok"` with `params_keys`.

### 5.2 Must-have (P1) acceptance criteria

10. **Origin allowlist is configurable via env var**:
    - Set `JUNIPER_WS_ALLOWED_ORIGINS=http://foo.local`.
    - Assert Playwright from `http://foo.local` succeeds and from
      `http://localhost:8050` fails.

11. **Cascor `/ws/training` and `/ws/control` enforce Origin**
    (M-SEC-01b) — browser-direct / demo test.

12. **Idle timeout closes a dead connection** (M-SEC-10):
    - Client connects, authenticates, sends nothing, server sends
      nothing for 120 s (mock heartbeat disabled).
    - Assert close code 1000.

13. **Reconnect backoff has jitter** (GAP-WS-30): unit test of the
    JS schedule.

### 5.3 Should-have (nice to have; not blocking gate)

14. Per-origin handshake cooldown fires after 10 rejections.
15. JSON depth cap rejects a 1,000-level-nested payload.
16. Canopy `SetParamsRequest` Pydantic model is used by BOTH canopy's
    `/ws/control` handler AND canopy's `/api/params` REST handler
    (single-source-of-truth).

### 5.4 Non-goals for Phase B-pre (explicit)

- Multi-tenant per-session replay buffers (§3.4 attack 4) — deferred.
- OAuth / OIDC integration — out of scope; local session model only.
- Mutual TLS between canopy and cascor — out of scope; rely on
  localhost trust.
- Subdomain bypass / CSP header (M-SEC-08) — deferred per §12.2.
- Constant-time API key comparison (M-SEC-09) — deferred per §12.2.

### 5.5 Exit criteria

Phase B-pre exits when criteria 1-13 pass in CI. The CI job name is
`canopy-ws-security`, runs on every PR that touches
`juniper-canopy/src/main.py`, `juniper-cascor/src/api/websocket/*.py`, or
`juniper-canopy/src/frontend/assets/websocket_client.js`. Failing tests
block merge.

---

## 6. Implementation steps

Ordered, repo/file-specific. Each step has a unique implementation ID
(IMPL-SEC-NN) for cross-reference during consolidation rounds.

### 6.1 Shared helpers first (cascor)

- **IMPL-SEC-01**: create `juniper-cascor/src/api/websocket/origin.py`
  exporting `validate_origin(ws: WebSocket, allowlist: list[str]) ->
  bool`. Extract the existing `worker_stream.py:41-44` pattern.
- **IMPL-SEC-02**: unit tests at `juniper-cascor/src/tests/unit/api/
  test_websocket_origin.py` covering: exact match, case-insensitive
  host, trailing-slash strip, null origin, port mismatch, scheme
  mismatch, wildcard rejection.
- **IMPL-SEC-03**: wire `validate_origin` into
  `training_stream_handler` and `control_stream_handler` at
  `juniper-cascor/src/api/app.py:338-339` call sites.
- **IMPL-SEC-04**: add `Settings.ws_allowed_origins: list[str]` with
  default `[]` (meaning "reject all browser origins, only
  `X-API-Key`-holders allowed") and env-var `JUNIPER_WS_ALLOWED_
  ORIGINS`.

### 6.2 Per-IP connection cap (cascor)

- **IMPL-SEC-05**: add `_per_ip_counts: Dict[str, int] = {}` and
  `_per_ip_lock` (reuse `_lock` per source doc rec) to
  `WebSocketManager` in `juniper-cascor/src/api/websocket/manager.py`.
- **IMPL-SEC-06**: implement the `async with manager._lock:` increment
  and finally-block decrement per the pattern in §2.9.2 M-SEC-04 code
  block.
- **IMPL-SEC-07**: add `Settings.ws_max_connections_per_ip: int = 5`.
- **IMPL-SEC-08**: unit test: simulate 6 connects from same IP, assert
  6th rejected with 1013.
- **IMPL-SEC-09**: unit test: increment/decrement race under
  `asyncio.gather` load.

### 6.3 Canopy Origin validation

- **IMPL-SEC-10**: add `validate_origin` helper in
  `juniper-canopy/src/backend/ws_security.py` (new module).
- **IMPL-SEC-11**: wire into `juniper-canopy/src/main.py` `/ws/training`
  and `/ws/control` route handlers at the line numbers in §2.9.2
  M-SEC-03 (`main.py:355` and `main.py:417` per the source doc).
- **IMPL-SEC-12**: `Settings.allowed_origins` in canopy config.
- **IMPL-SEC-13**: deny-by-default for the empty list? **Decision**:
  default list is the four localhost/127.0.0.1 × http/https entries.
  Empty list means "reject all" (fail closed). This is safer than "allow
  all" but may surprise operators who don't realize they need to set
  the list in prod. Document prominently in canopy README.

### 6.4 Canopy cookie session and CSRF

- **IMPL-SEC-14**: if canopy does not yet have a session middleware, add
  one. Use `starlette.middleware.sessions.SessionMiddleware` with a
  per-deployment `secret_key` loaded from env. Cookie attributes:
  `httponly=True, secure=<auto-detect>, samesite="strict",
  path="/"`.
- **IMPL-SEC-15**: add `/api/csrf` REST endpoint returning `{csrf_token}`.
  The token is a 32-byte `secrets.token_urlsafe(32)` stored on the
  session as `session["csrf_token"]`. Mint-on-first-request; rotate on
  logout and every hour of sliding activity.
- **IMPL-SEC-16**: add the CSRF first-frame check in `/ws/training` and
  `/ws/control` handlers. Read the first frame with `asyncio.wait_for(
  ws.receive_text(), timeout=5.0)`; parse; validate; close 4001 on
  failure.
- **IMPL-SEC-17**: dash page template exposes the token as a JS
  variable (`window.__canopy_csrf`). Do NOT store in localStorage.
- **IMPL-SEC-18**: `juniper-canopy/src/frontend/assets/websocket_client.js`
  reads `window.__canopy_csrf` at connect time and sends the auth frame
  immediately after `onopen`.

### 6.5 Per-frame size caps

- **IMPL-SEC-19**: audit every `ws.receive_text()` / `ws.receive_json()`
  / `ws.receive_bytes()` call in canopy and cascor. Add `max_size` param
  or explicit length check.
- **IMPL-SEC-20**: cascor `training_stream.py` — cap at 4 KB.
- **IMPL-SEC-21**: canopy `main.py /ws/training` — cap at 4 KB.
- **IMPL-SEC-22**: canopy `main.py /ws/control` — cap at 64 KB.
- **IMPL-SEC-23**: **preserve** cascor `control_stream.py:23` existing
  64 KB cap (regression test).
- **IMPL-SEC-24**: unit test per endpoint: send a frame 1 byte over
  the cap, assert close 1009.

### 6.6 Schema validation

- **IMPL-SEC-25**: create `juniper-canopy/src/backend/ws_schemas.py`
  with `SetParamsRequest`, `AuthFrame`, `ResumeFrame`, `CommandFrame`
  Pydantic v2 models. `extra="forbid"` on all.
- **IMPL-SEC-26**: the canopy `control_stream_handler` uses
  `CommandFrame.model_validate_json()` to parse. On ValidationError,
  respond with a structured error (GAP-WS-22 compliance).
- **IMPL-SEC-27**: factor the `SetParamsRequest` model into a shared
  module that the canopy REST `/api/params` handler also uses (one
  source of truth for validation). **Caveat**: this may be premature;
  deferred to Phase C if it adds PR size.
- **IMPL-SEC-28**: JSON-depth guard (custom parser or Pydantic config)
  at the handler entry point.

### 6.7 Rate limiting and idle timeout

- **IMPL-SEC-29**: leaky-bucket rate limiter per-connection. Keep as a
  small utility class in `ws_security.py`. 10 tokens, refill 10/s.
- **IMPL-SEC-30**: idle timeout: wrap `receive_text()` loop in
  `asyncio.wait_for(..., timeout=120)`. On timeout, close 1000.
  Compatible with heartbeat: heartbeat resets the timer.
- **IMPL-SEC-31**: per-origin handshake cooldown: a small IP-keyed
  counter in `WebSocketManager` that tracks recent rejections. This
  is intentionally NOT in `_per_ip_counts` (different semantics).

### 6.8 Audit logging

- **IMPL-SEC-32**: `juniper-canopy/src/backend/audit_log.py` new module.
  Configures a `canopy.audit` logger with a JSON formatter and a
  rotating file handler. The file path is `Settings.audit_log_path`,
  default `~/.local/state/canopy/audit.log` (or
  `/var/log/canopy/audit.log` in production).
- **IMPL-SEC-33**: the control handler calls
  `audit_log.ws_control(event=...)` on every inbound command.
- **IMPL-SEC-34**: the auth handler calls `audit_log.ws_auth(...)` on
  every auth success/failure.
- **IMPL-SEC-35**: scrub-allowlist constant in `ws_schemas.py`:
  `AUDIT_SCRUB_ALLOWLIST: frozenset = frozenset(SetParamsRequest.
  model_fields.keys())`. Auto-derive from the model so adding a param
  key automatically makes it loggable (and removing it makes it
  redacted).
- **IMPL-SEC-36**: prom counters via `prometheus_client` if canopy
  already uses it; else a simple counter module.

### 6.9 Adapter-side hardening (canopy → cascor)

- **IMPL-SEC-37**: in `juniper-canopy/src/backend/
  cascor_service_adapter.py`, parse inbound cascor frames via the
  envelope schema. Reject non-conforming frames; log; reconnect.
- **IMPL-SEC-38**: adapter sends `{type: "auth", csrf_token: "<fake>"}`
  when `Settings.disable_ws_auth=False` on the cascor side. Requires
  coordination: cascor must accept a synthetic auth frame for
  adapter-originated connections. One option is to recognize a
  dedicated header (`X-Juniper-Role: adapter`) and skip the CSRF check
  entirely for that connection class. This is a legitimate deviation
  from the uniform handler rule and must be flagged. See open question
  §11-sec-1.

### 6.10 Cascor-side `set_params` integration tests (hook for GAP-WS-09)

- **IMPL-SEC-39**: extend Phase G's test file
  `juniper-cascor/src/tests/unit/api/test_websocket_control.py` with:
  - `test_set_params_origin_rejected`
  - `test_set_params_unauthenticated_rejected`
  - `test_set_params_oversized_frame_rejected` (already in Phase G)
  - `test_set_params_rate_limit_triggers_after_10_cmds`
  - `test_set_params_bad_init_output_weights_literal_rejected`

### 6.11 Pre-merge guardrails

- **IMPL-SEC-40**: add a `juniper-deploy` compose check that fails if
  `JUNIPER_DISABLE_WS_AUTH=true` is set on a `prod` profile. CI gate.
- **IMPL-SEC-41**: add a pre-commit hook (ruff or grep) that fails on
  any new `localStorage.setItem("csrf"...)` or similar.
- **IMPL-SEC-42**: update `notes/code-review/WEBSOCKET_MESSAGING_
  ARCHITECTURE_2026-04-10.md` §2.9 with cross-references to this
  proposal's IMPL-SEC IDs during the Round 5 canonical plan step.
  (Not now — round 0.)
- **IMPL-SEC-43**: fix GAP-WS-19 (`close_all()` lock) inside
  Phase B-pre rather than deferring. 3-line change; flagged in §8.12.
- **IMPL-SEC-44**: ensure the SDK `set_params` (GAP-WS-01) passes the
  `X-API-Key` header on every WebSocket open. Regression guard: unit
  test that asserts the header is present on the mock server side.
  Prevents a test-fake header-omission regression (§3.2 attack 2).

---

## 7. Verification / acceptance criteria

### 7.1 Test types

- **Unit tests** (cascor pytest, canopy pytest): cover helpers,
  validators, rate limiter math, per-IP cap increment/decrement,
  envelope schema.
- **Integration tests** (cascor `TestClient.websocket_connect()`,
  canopy `TestClient` equivalent): cover endpoint wiring — origin,
  auth, size, rate limit, permissions.
- **End-to-end Playwright tests**: cover the browser experience —
  `window.cascorWS` auth flow, CSWSH probe from a separate origin,
  CSRF token rotation.
- **Fuzzing**: run `atheris` or `hypothesis` against the envelope
  parsers to shake out JSON-parse DoS cases. Not blocking but
  recommended.
- **Regression test**: the existing test suites (especially the fake
  server fixtures in `juniper-cascor-client/juniper_cascor_client/
  testing/`) must be updated to enforce auth so the "header-omission
  regression" attack scenario (§3.2 attack 2) is caught.

### 7.2 Specific new test files

| File | Purpose | Scope |
|---|---|---|
| `juniper-cascor/src/tests/unit/api/test_websocket_origin.py` | Origin helper | cascor |
| `juniper-cascor/src/tests/unit/api/test_websocket_per_ip_cap.py` | Per-IP cap + race | cascor |
| `juniper-cascor/src/tests/unit/api/test_websocket_size_limits.py` | Frame caps | cascor |
| `juniper-cascor/src/tests/unit/api/test_websocket_rate_limit.py` | Leaky bucket | cascor |
| `juniper-canopy/src/tests/unit/test_ws_security_origin.py` | Origin helper | canopy |
| `juniper-canopy/src/tests/unit/test_ws_security_auth.py` | Cookie + CSRF | canopy |
| `juniper-canopy/src/tests/unit/test_ws_security_schemas.py` | Pydantic | canopy |
| `juniper-canopy/src/tests/unit/test_audit_log.py` | Scrubber | canopy |
| `juniper-canopy/src/tests/integration/test_ws_security_cswsh.py` | CSWSH probe (Playwright) | canopy |
| `juniper-canopy/src/tests/integration/test_ws_security_resume_rate.py` | Resume frame limit | canopy |

### 7.3 Fuzz / chaos targets

- **Header fuzzing**: `hypothesis` generates origin strings with
  unicode, null bytes, leading spaces, CRLF injection, very long,
  empty, missing. All must route to reject, never to pass.
- **JSON fuzzing**: `atheris` on the `CommandFrame.model_validate_json`
  entry point with 64 KB random payloads. No exceptions should
  escape the handler.
- **Connection churn**: scripted 1000 open/close cycles with random
  auth states; assert `_per_ip_counts` ends at zero.
- **Resume frame chaos**: random `last_seq` / `server_instance_id`
  combinations; no exception should escape.

### 7.4 Acceptance checklist (copy into Phase B-pre PR description)

```
[ ] CSWSH probe fails (Playwright, different origin)
[ ] Origin allowlist configurable via env
[ ] Cookie session cookie attributes: HttpOnly, Secure, SameSite=Strict
[ ] CSRF first-frame enforced within 5s
[ ] Per-frame inbound caps enforced on all /ws/* endpoints
[ ] Per-IP connection cap enforced
[ ] Per-connection command rate limit enforced
[ ] Idle timeout (120s) closes stale connections
[ ] Audit log captures auth/command events with scrubbing
[ ] Prom counters exported for rejection reasons
[ ] Opaque auth-failure close-reason text (M-SEC-06)
[ ] Replay protocol works post-auth (auth frame, then resume frame)
[ ] `Settings.disable_ws_auth` bypass works for local dev
[ ] CI guardrail: prod compose rejects disable_ws_auth=True
[ ] All integration tests pass against a real cascor (not fake)
```

---

## 8. Risks introduced by the controls

This section is the flip side of §3 — what could GO WRONG because of
the hardening itself?

### 8.1 Cookie-session binding breaks JS WS client

**Risk**: the Dash frontend today may not set the session cookie at all
(canopy may be running in "session-less" mode). Adding `SessionMiddleware`
is non-trivial because it touches every route, and `SameSite=Strict`
breaks embeds (if canopy is ever iframed, the cookie won't send, and
WebSocket upgrade fails).

**Mitigation**: Phase B-pre cleanly lands the session middleware in a
standalone PR first, verified against existing REST routes, BEFORE the
WebSocket wiring. A regression test suite for the existing routes
catches surprises. Iframing is not a supported canopy deployment today;
document that explicitly.

**Mitigation**: `Settings.disable_ws_auth=True` for local dev so new
contributors don't have to set up cookies just to run the dashboard.

### 8.2 CSRF token fetch latency on first connect

**Risk**: the browser must fetch `/api/csrf` before opening the WS, adding
a round-trip to dashboard startup. On a fresh page load this might be
~50 ms.

**Mitigation**: embed the token directly into the Dash page HTML at
server-side render time. No `/api/csrf` round-trip on first load; the
endpoint exists only for token rotation.

### 8.3 Per-IP cap punishes NAT

**Risk**: 5 conns/IP means a 6-user office behind a single NATed IP gets
one user rejected.

**Mitigation**: configurable via env. Document in deployment guide.
Multi-tenant topologies should use application-level per-user caps
instead (future work; see §11-sec-3).

### 8.4 Audit log volume

**Risk**: if audit logs are noisy, disk fills up. With a training run
emitting 100 `set_params` per minute, 100 × 60 × 24 = 144 K lines/day
× ~500 B each ≈ 70 MB/day. 90-day retention ≈ 6 GB.

**Mitigation**: audit log rotation + compression. Document the disk
budget. `candidate_progress` events are not audited (§4.6 rule 7).

### 8.5 `SameSite=Strict` breaks legitimate cross-subdomain use cases

**Risk**: if canopy is ever deployed at `canopy.example.com` with
separate Dash and API subdomains, `SameSite=Strict` refuses to send
the cookie across the subdomain boundary.

**Mitigation**: document that canopy must be served from a single
origin. If the multi-origin case ever happens, revisit with `SameSite=
Lax` and stronger CSRF token verification.

### 8.6 Rate limit false positives for bulk `set_params`

**Risk**: a user who rapidly drags a slider emits many `set_params` per
second. 10 cmd/s is not much.

**Mitigation**: clientside debounce to ~5 Hz. The Dash slider component
already emits on drag-end not drag-continuous; combined with the 100 ms
clientside_callback that forwards to `cascorControlWS.send()`, typical
drag rate is ~10 cmd/s. Document the 10 cmd/s limit and recommend
client-side debounce at 5 Hz.

**Mitigation 2**: rate-limit by command *type*, not total — e.g., 10
`set_params`/s AND 5 `start|stop|reset|pause|resume`/s. Keeps slider
UX smooth while rate-limiting destructive actions.

### 8.7 CSRF rotation mid-session disconnects the dashboard

**Risk**: hourly token rotation forces a WebSocket reconnect every hour,
which may flicker the UI.

**Mitigation**: rotation is a *sliding* window — user activity
re-anchors it. An actively-used dashboard never rotates. The reconnect
on rotation is graceful (replay protocol covers the gap).

### 8.8 Adapter synthetic-auth-frame breaks uniform handler

**Risk**: §6.9 IMPL-SEC-38 introduces a special case for the canopy
adapter that skips CSRF for `X-Juniper-Role: adapter` connections. This
adds a branch in the auth logic and is an attractive attack target (if
an attacker can forge the header, they bypass CSRF).

**Mitigation**: the `X-Juniper-Role` header path ONLY activates when the
X-API-Key is also present and valid. This is the pre-upgrade HTTP
header check, which a browser CANNOT perform (custom headers forbidden
on WS upgrade from JS). So the branch is unreachable from browser
attack. Document this in a code comment.

**Alternative**: the adapter could send a real CSRF-shaped auth frame
derived from the API key (e.g., `csrf_token = hmac(api_key,
"adapter-ws")`). This avoids the branch at cost of a slightly uglier
first-frame. Decision point in §11.

### 8.9 Size caps break future large-topology broadcast

**Risk**: GAP-WS-18 (topology >64 KB) can collide with the 128 KB
outbound cap proposed in §4.4.

**Mitigation**: the outbound cap is per-frame, not per-logical-message.
GAP-WS-18 chunking solves the >64 KB case by fragmenting into multiple
frames. Document this explicitly in §6.5 of the source doc during Round
5 canonical plan.

### 8.10 JSON depth cap breaks a legitimate nested param

**Risk**: `SetParamsRequest` has flat keys today; a depth cap of 16 is
generous. But if someone adds a nested `{"optimizer": {"type": "adam",
"betas": [0.9, 0.999]}}` key later, the cap may be hit.

**Mitigation**: 16 levels is far above reasonable parameter nesting.
Document the cap as "max JSON depth = 16; deepen if truly needed."

### 8.11 TLS termination at the reverse proxy layer

**Risk**: canopy is assumed to run behind nginx/traefik in production.
If TLS is terminated at the proxy but the proxy↔canopy hop is
plaintext HTTP on localhost, the `Secure` cookie attribute can cause
cookies to be dropped by the browser (because canopy sees an HTTP
connection and `Secure` can clash with `X-Forwarded-Proto: https`
handling). Additionally, an attacker with local-network access between
proxy and canopy can read cookies in transit.

**Mitigation**:
1. Canopy trusts `X-Forwarded-Proto: https` only from a configured
   trusted-proxy IP allowlist (`Settings.trusted_proxies`).
2. When trusted-proxy sets `X-Forwarded-Proto: https`, canopy treats
   the request as HTTPS for cookie and redirect purposes.
3. If `Settings.trusted_proxies` is empty AND the request arrives via
   plain HTTP, log a loud WARNING at startup on every request
   ("canopy serving over plaintext — do not use in production").
4. Document in the deployment guide that the proxy↔canopy hop MUST be
   loopback-only (127.0.0.1 or unix socket), never over network.
5. Operators with stricter requirements can run canopy over HTTPS
   directly (uvicorn `--ssl-keyfile`), skipping the proxy.

### 8.12 `close_all()` shutdown race can leak a CSRF-bearing session

**Risk**: GAP-WS-19 notes that `close_all()` does not hold `_lock`, so
a connection racing shutdown can be orphaned. Security-adjacent
because the orphaned connection still has a valid CSRF binding. In
practice this is a <100 ms race window during shutdown.

**Mitigation**: fix GAP-WS-19 (wrap `close_all()` body in
`async with self._lock:`). Low effort, low risk. Fold into Phase B-pre
even though the source doc marks it P2 and defers to a separate PR.

---

## 9. Disagreements with the source doc

Explicit deltas from `WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md`
v1.3:

### 9.1 Effort estimate for Phase B-pre is low

**Source**: §9.2 says "Effort: 1 day."

**This proposal**: 1.5–2 days. The CSRF token plumbing (cookie
middleware, `/api/csrf` endpoint, Dash template injection), audit
logger, per-IP cap concurrency contract, and testing all add up. A
1-day estimate is plausible only if canopy already has a session
middleware (unverified) and the audit logger already exists. Round 1
consolidation should verify and adjust.

### 9.2 Phase B-pre should gate Phase B, not just Phase D

**Source**: §9.12 says "Phase B-pre before Phase B (security must
precede the browser bridge so the new attack surface is not exposed)"
— actually the source doc already says this. **Agreement**, not
disagreement. Reiterating for clarity.

### 9.3 Origin allowlist should default to a concrete list, not empty

**Source**: §2.9.2 M-SEC-01 says "Default allowlist: `http://localhost:
8050`, `http://127.0.0.1:8050`."

**This proposal**: agrees with the content but makes explicit that
empty list ≠ "allow all" — it means "reject all browser origins." The
source doc is not clear about the fail-closed semantics. Document
explicitly.

### 9.4 `disable_ws_auth` flag name is ambiguous

**Source**: §2.9.2 M-SEC-02 proposes `Settings.disable_ws_auth=True`
for local dev.

**This proposal**: rename to `Settings.ws_security_enabled=True` (with
default True) and advise setting `False` for local dev. A negative-
sense flag that defaults to insecure is a known config footgun —
`disable_auth=True` can land in a prod config by a merge accident,
and nobody notices. A positive-sense flag (`ws_security_enabled=True`)
reverses the failure mode — a merge accident would re-enable
security, not disable it.

**Counter-argument**: negative-sense flags are more common in Python
config, and renaming has ripple costs. **Accept either; flag for
reviewer decision.**

### 9.5 Per-command HMAC (M-SEC-02 point 3) is over-engineering

**Source**: §2.9.2 M-SEC-02 point 3: "each control command carries a
HMAC computed over `{command, params, timestamp}` using a
session-derived key. Prevents replay even within an authenticated
session."

**This proposal**: defer indefinitely. Within an authenticated session,
replay protection buys very little — the attacker is already inside the
session and can just issue new commands. HMAC adds complexity (key
derivation, clock-skew handling, client-side crypto in JS). The source
doc correctly marks this "advanced, optional." **This proposal moves
it out of Phase B-pre entirely**; revisit only if a multi-tab
synchronization concern emerges.

### 9.6 Replay-buffer security is understated

**Source**: §6.5 GAP-WS-13 treats the replay buffer as a correctness
feature. This proposal argues (§3.4) that it also has a security
dimension: forged low `last_seq` can amplify outbound traffic, so the
"one resume per connection" rule is a security mitigation. The source
doc does not mention this; suggest adding it to §6.5.3 edge cases.

### 9.7 Multi-tenant replay isolation is deferred but should be named

**Source**: §6.5 is silent on whether the replay buffer is shared
across clients. Implementation-wise, the buffer is a property of the
`WebSocketManager`, shared across all connections.

**This proposal**: this is fine for single-tenant (the current
deployment model), but the moment a multi-tenant deployment happens,
every authenticated client can read every other client's events via
`resume`. The source doc §11 Q1 mentions multi-tenant in the context of
backpressure but not replay. Add it explicitly as Q1-sec.

### 9.8 Audit logging is not in the source doc

**Source**: §2.9.2 M-SEC-07 mentions "logging scrubbing allowlist" but
does not prescribe an audit logger per se.

**This proposal**: §4.6 adds a dedicated audit logger separate from
the application log. This is a meaningful scope bump. Flag for
consolidation — this is new work, should Round 1 fold it into
Phase B-pre or defer?

### 9.9 New M-SEC-10, M-SEC-11, M-SEC-12 identifiers

**Source**: source doc stops at M-SEC-07 (active) and M-SEC-08/09
(deferred per §12.2).

**This proposal**: adds

- **M-SEC-10** (idle timeout, §4.5 control 5)
- **M-SEC-11** (adapter inbound validation, §4.4 control 5, §6.9)
- **M-SEC-12** (log injection escaping, §4.6 rule 10) — can fold into
  M-SEC-07 if Round 1 prefers.

Round 1 consolidation should assign these canonically or merge into
existing IDs.

---

## 10. Self-audit log

First pass of the draft produced §1-9 and a planning notes section
(previously labelled §10). This self-audit captures the planning
section's findings, applies them as Edits, and records what changed.

### 10.1 Coverage check — every M-SEC identifier

Walked through §2.9.2 of the source doc top to bottom:

- [x] M-SEC-01: covered in §4.1.
- [x] M-SEC-01b: covered in §4.1 (shared helper).
- [x] M-SEC-02: covered in §4.2 with cookie-attributes refinement,
  CSRF token lifecycle, constant-time comparison, session-fixation
  prevention.
- [x] M-SEC-03: covered in §4.4 control 1 with per-endpoint target
  table.
- [x] M-SEC-04 (per-IP + auth timeout): covered in §4.5 controls 1
  and 3.
- [x] M-SEC-05: covered in §4.5 control 4 with leaky-bucket
  parameters and command-type split.
- [x] M-SEC-06: covered in §4.2, §4.4 control 6, §4.5.
- [x] M-SEC-07: covered in §4.6, extended with rules 9-11
  (before/after diff, CRLF escaping, user-agent).
- [x] M-SEC-10 (new — idle timeout): covered in §4.5 control 5.
- [x] M-SEC-11 (new — adapter inbound validation): covered in §4.4
  control 5 and §6.9.
- [x] M-SEC-12 (new — log injection escaping): covered in §4.6
  rule 10.

### 10.2 Coverage check — GAP-WS items flagged in §2.2

- [x] GAP-WS-22: §4.4 control 4 + §6.6 IMPL-SEC-26.
- [x] GAP-WS-27: §4.5 controls 1, 3, 4.
- [x] GAP-WS-13: §4.7 explicit auth-then-resume sequence.
- [x] GAP-WS-12: §4.5 control 5 idle timeout compatible with
  heartbeat.
- [x] GAP-WS-32: §3.3 attack 5 + §4.5 controls — `command_id` is
  per-connection scoped (clarification applied).
- [x] GAP-WS-30: §4.8 jitter.
- [x] GAP-WS-31: §4.8 handshake cooldown.
- [x] GAP-WS-19: §8.12 + IMPL-SEC-43 — folded into Phase B-pre as
  security-adjacent.
- [x] GAP-WS-01: §3.6 + IMPL-SEC-44 — SDK `X-API-Key` regression
  guard.
- [x] GAP-WS-09: §6.10 IMPL-SEC-39 — security test cases added to
  Phase G scope.

### 10.3 Threat model completeness

Reviewed §3. Findings:

- CSWSH, unauth control, schema confusion, replay, DoS, adapter
  trust, browser-direct-to-cascor: all present.
- **Added attack 7 (§3.5)**: log injection via CRLF in origin /
  user-agent. Fixed by §4.6 rule 10.
- **Added attack 8 (§3.5)**: TLS termination / MITM at reverse-proxy
  layer. Fixed by §8.11.
- **Skipped**: password reuse / credential stuffing — canopy has no
  password auth today, N/A.
- **Verified**: no missing attack classes for the current threat
  scope (single-user, localhost or behind a trusted proxy).

### 10.4 Vague controls sharpened

- §4.1 Origin validation: added "HTTP 403 where supported; else
  Starlette `ws.close(1008)` or pre-accept `HTTPException(403)`" and
  flagged implementation-time verification.
- §4.5 control 4 leaky bucket: specified capacity (10 tokens), refill
  rate (10/s), initial fill (full), and the "what counts as a
  command" rule.
- §4.6 rotation: specified `TimedRotatingFileHandler(when="midnight",
  backupCount=90)` with gzip compression.
- §4.2 CSRF token: specified `secrets.token_urlsafe(32)` (43 chars,
  192 bits entropy).
- §4.2 CSRF comparison: `hmac.compare_digest`, never `==`.
- §4.2 session fixation: fresh session ID on auth.
- §4.4 control 6 (new): close-reason text must not leak internal
  state (no stack traces in `close(reason=...)`).

### 10.5 Audit/logging coverage expanded

- §4.6 rule 4: enumerated all failure reasons.
- §4.6 rule 6: rotation mechanism specified.
- §4.6 rule 9: `params_before` / `params_after` diff logged.
- §4.6 rule 10: CRLF/tab escaping for user-controlled fields.
- §4.6 rule 11: user-agent logged verbatim (escaped).
- §4.1: origin rejections explicitly audit-logged as auth events.
- §4.6 metrics: added `canopy_ws_auth_latency_ms` histogram.

### 10.6 Rate-limit specifics

- §4.5 control 4: leaky-bucket parameters and command-counting rules
  specified.
- §4.5 control 4: two-bucket option (set_params separate from
  destructive commands) noted as deferrable refinement.
- §4.5 control 6: resume frame rate limit uses close code **1003**
  (Unsupported Data) per GAP-WS-22 table.

### 10.7 Cross-references verified

- §5.6 latency instrumentation (GAP-WS-24): auth-frame latency now
  has its own histogram.
- §5.5 end-to-end frame budget: auth-phase latency is <5s (M-SEC-04
  auth timeout), well above per-frame budget; no conflict.
- §6.5 replay protocol: §4.7 sequence diagram covers auth-then-
  resume.

### 10.8 Edits applied

| # | Edit | File location |
|---|---|---|
| 1 | `command_id` per-connection scoping | §3.3 attack 5 |
| 2 | Log injection + TLS attacks | §3.5 attacks 7, 8 |
| 3 | Origin 403 clarification + audit-log note | §4.1 rejection mechanics |
| 4 | `hmac.compare_digest`, session fixation, token minting | §4.2 token lifetime |
| 5 | Close-reason leakage (control 6) | §4.4 |
| 6 | Leaky-bucket parameters and definitions | §4.5 control 4 |
| 7 | GAP-WS-22 alignment for resume frame | §4.5 control 6 |
| 8 | Rules 4, 6, 9, 10, 11 for audit logging | §4.6 |
| 9 | `canopy_ws_auth_latency_ms` histogram | §4.6 metrics |
| 10 | §8.11 TLS termination risk | §8.11 |
| 11 | §8.12 close_all() shutdown race note | §8.12 |
| 12 | M-SEC-12 canonical identifier | §9.9 |
| 13 | IMPL-SEC-43, IMPL-SEC-44 new steps | §6.11 |

### 10.9 Residual gaps flagged for Round 1 consolidation

- **Q2-sec** (adapter synthetic auth frame): needs a decision before
  Phase B-pre ships. I prefer `X-Juniper-Role: adapter` header-based
  skip, but the alternative (HMAC CSRF) avoids a branch in the
  handler. Round 1 should pick.
- **Q4-sec** (naming): `ws_security_enabled=True` vs
  `disable_ws_auth=False`. Naming nit but a footgun concern.
- **Multi-tenant replay isolation**: not in Phase B-pre scope, but
  §11 Q1-sec should be added to the source doc §11 list.
- **Effort estimate**: my 1.5-2 day estimate contradicts the source
  doc's 1 day. Round 1 should reconcile against canopy's current
  session-middleware state (verified or not).

### 10.10 What this self-audit did NOT do

- Did not run the tests (this is a proposal, not an implementation).
- Did not verify that the cited line numbers (`main.py:355`,
  `main.py:417`) are current against origin/main as of 2026-04-11 —
  relied on the source doc's 2026-04-10 reference.
- Did not read the canopy or cascor source trees directly — this is
  a round-0 proposal and the scope is the architecture doc plus the
  reviewer's specialty knowledge. Round 1 or 2 can cross-check.

---

## 11. Open questions (security-specific)

These are additions to §11 of the source doc, tagged with `sec-`:

- **Q1-sec**: Multi-tenant replay buffer isolation — per-session
  buffers, or shared? Defer until multi-tenant deployment lands.
- **Q2-sec**: Adapter synthetic auth frame — real CSRF-shaped (HMAC
  of API key) or uniform skip via `X-Juniper-Role: adapter`? Must
  decide before Phase B-pre ships, because the cascor-side handler
  changes differ.
- **Q3-sec**: Per-IP cap default (5). The source doc already flags this
  as §11 Q6. Recommend 5 for single-user deployments, 20 for
  multi-user lab VM, 100 for multi-tenant cloud — but multi-tenant is
  out of scope for Round 0.
- **Q4-sec**: `ws_security_enabled=True` vs `disable_ws_auth=False`
  naming — positive or negative sense? Footgun concern.
- **Q5-sec**: TLS termination model. Assumed to be the reverse-proxy's
  job. Document in the deployment guide.
- **Q6-sec**: Audit log destination in production (local file vs
  central log collector). Defer.
- **Q7-sec**: Where does the CSRF token get minted if canopy currently
  has no session middleware at all? Is Phase B-pre responsible for
  adding SessionMiddleware too? Yes (IMPL-SEC-14) but should Round 1
  confirm this isn't already present.

---
