# Juniper — Control-Surface Auth (SEC-F22) & Docker-NAT IP-Keyed Controls (SEC-F19) — Remediation Design of Record

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**Document Type**: Design of Record (defensive remediation)
**Status**: Decision-ready — Decisions **D1–D8** await owner ratification; nothing here is implemented
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-07-03

---

## 1. Purpose & scope

This is the remediation design-of-record for the **two live-confirmed findings** from the containerized-stack security audit
([`notes/JUNIPER_2026-07-02_JUNIPER-ECOSYSTEM_STACK-SECURITY-AUDIT-PLAN.md`](JUNIPER_2026-07-02_JUNIPER-ECOSYSTEM_STACK-SECURITY-AUDIT-PLAN.md), §4.1 / §4.7 / §5.2):

- **SEC-F22** — the canopy browser training-control gate is bypassable from any in-network foothold (confirmed live, HO-6).
- **SEC-F19** — Docker NAT defeats every IP-keyed control (confirmed live, HO-3).

It is an **authorized defensive audit of the platform owner's own stack** (owner: Paul Calnon / `@pcalnon`, sole CODEOWNER),
scoped to the containerized deployment (`juniper-deploy` compose). It enumerates options with grounded trade-offs and recommends a
path; it contains no weaponized payloads. Both findings were live-verified by Opus against an **isolated throwaway stack** (compose
project `secaudit`, loopback `127.0.0.2`) on 2026-07-02; the live `127.0.0.1` stack was untouched (audit §5.2). This document
**independently re-verified every static code claim** underlying those live results (all `file:line` anchors below re-confirmed in
the working trees on 2026-07-03); the two live-observed IPs (bridge gateway `172.23.0.1`, sidecar `172.23.0.5`) are attributed to
the audit's isolated-stack run and are **not** re-derived here.

**Repos in scope.** `juniper-canopy` (SEC-F22 gate; canopy IP controls), `juniper-cascor` (cascor IP controls), `juniper-deploy`
(compose topology, network subnets, env allowlist, the absent fronting proxy), and the shared `juniper-observability`
`MetricsAuthMiddleware`. Paths under `src/...` are repo-relative to the named repo; cross-repo paths are prefixed explicitly.

**Non-goals.** (a) The other audit findings (SEC-F01 fail-open auth, SEC-F08 SSRF, SEC-F17 torch floor, etc.) — tracked separately.
(b) Building the fronting reverse proxy itself — this document specifies *where it lands* and *what it must do*, and defers its
construction to an owner-gated milestone. (c) Changing the `CANOPY_API_KEY` secret or its rotation. (d) TLS termination (SEC-F12,
by-design-external). (e) Any deploy/env/secret change is **owner-gated** (Paul approves deployment and PyPI/deploy gates).

**Deliverable.** This one `notes/` document. No source is changed.

---

## 2. The two findings, with confirmed evidence

### 2.1 SEC-F22 — browser-control gate bypassable from any in-network foothold (Medium; CONFIRMED live, HO-6)

**What the gate is (today, live and active).** canopy's six training-control routes are **key-exempt** and authenticated by a
per-route FastAPI dependency, `require_browser_control_auth`:

- The routes carry `dependencies=[Depends(require_browser_control_auth)]`: `POST /api/train/{start,pause,resume,stop,reset}` and
  `GET /api/train/status` (`juniper-canopy/src/main.py:2917,2938,2952,2966,2980,2994`).
- They are key-exempt via the two-tier middleware split — `KEY_EXEMPT_PATH_PREFIXES = ("/api/train/",)` and
  `KEY_EXEMPT_PATHS = frozenset({"/api/csrf"})` (`src/canopy_constants.py:380-381`), applied by `_is_key_exempt`
  (`src/middleware.py:163-181`): they skip the `X-API-Key` gate but stay rate-limited, and the dependency owns authn.
- `require_browser_control_auth` (`src/security.py:308-368`) accepts on **any of**: (1) a valid `X-API-Key` (`:341-344`); (2) auth
  globally disabled (`:347-348`); or (3) the browser path — flag on (`browser_control_auth_enabled`, default **True**,
  `src/settings.py:341`), **Origin allowlisted** (`:359-360`), **and** a valid CSRF token (`:363-368`, skipped only if
  `csrf_enabled` is False; default **True**, `src/settings.py:331`).

**Why the browser-path authenticators are both forgeable by a non-browser in-network client.**

- **The Origin check is a string compare.** `browser_origin_allowed` (`src/security.py:286-305`) delegates to `is_origin_allowed`
  (`src/ws_security.py:16-36`), a **case-insensitive, trailing-slash-insensitive equality** test against
  `settings.websocket.allowed_origins` (default includes `http://127.0.0.1:8050`, `src/settings.py:135-140`). An `Origin` header is
  only trustworthy when a **browser** stamps it; a non-browser client sets it to any value it likes. A spoofed
  `Origin: http://127.0.0.1:8050` passes.
- **The CSRF token is anonymously mintable.** `GET /api/csrf` (`src/main.py:485-519`) refuses to mint **only** for a
  present-but-disallowed Origin: the guard at `:512` is `if api_key_auth.enabled and not _keyed and _origin is not None and not
  browser_origin_allowed(request)`. So a caller with **no Origin header** mints freely (the "same-origin bootstrap" relaxation,
  `:505-513`), **and** a caller presenting a **spoofed allowlisted Origin** also mints. Either way a valid token is obtained with no
  credential.

**Confirmed exploit chain (HO-6, audit §5.2).** From a non-loopback in-network sidecar (`172.23.0.5`): (1) anonymous `GET /api/csrf`
→ valid token; (2) `POST /api/train/start` with a spoofed `Origin: http://127.0.0.1:8050` and that token → **HTTP 200**, driving the
full training-control surface (start/pause/resume/stop/reset) with **no real credential**. Two **negative controls** prove the gate
is genuinely active (this is *not* the SEC-F01 fail-open case): no-Origin `POST` → **403** (`src/security.py:359-360`), no-CSRF
`POST` → **403** (`src/security.py:363-368`). The attacker must present both a spoofed Origin and a minted token — both trivially
obtainable by any in-network non-browser client.

**The one effective control today is the loopback bind.** In the deploy canopy publishes on
`${BIND_HOST:-127.0.0.1}:${CANOPY_PORT:-8050}` (`juniper-deploy/docker-compose.yml:557`). The design that shipped this gate
(`juniper-canopy/notes/JUNIPER_CANOPY_TRAINING-CONTROL-AUTH_DESIGN_2026-06-30.md` §7.3) **explicitly acknowledges this exact
residual** and states the load-bearing precondition: "The fix must not be shipped on a build that binds the control surface to a
public interface without a fronting auth layer" (§7.3 point 1; §12 OQ-3). SEC-F22 is that acknowledged residual, now confirmed
exploitable from a mere in-network position (not only a same-host process).

**Does the dashboard have any user authentication today? No — verified.** The dashboard page itself is served **anonymously**:
`/dashboard` is in `EXEMPT_PATH_PREFIXES` (`src/canopy_constants.py:353`), so it never sees the key gate. A repository-wide search
for a login / sign-in / password / user-session mechanism in `juniper-canopy/src/*.py` returns **nothing**. The `canopy_session`
cookie (`SessionMiddleware`) is an **anonymous** session container, not a user-identity credential — no login populates it with a
principal. The **only** credential in the system is the server `X-API-Key` (machine-to-machine), which the browser structurally
cannot hold (design C2/C3: the per-process `INTERNAL_REQUEST_TOKEN` is minted per start and never leaves the process). **The browser
holds no credential of any kind.** This fact is decisive for the SEC-F22 option analysis (§4).

### 2.2 SEC-F19 — Docker NAT defeats every IP-keyed control (Medium, architectural; CONFIRMED live, HO-3)

**Seven controls key on the raw socket peer, and none honor `X-Forwarded-For`.** Each reads the kernel-reported peer address
(`websocket.client[0]` or `request.client.host`) as the identity for a per-IP decision:

| # | Control | Reads peer at | XFF honored? |
| --- | --- | --- | --- |
| 1 | canopy WS per-IP cap (`max_connections_per_ip=5`) | `juniper-canopy/src/settings.py:141`; `src/communication/websocket_manager.py:366` (`check_per_ip_limit`), `:381` (decrement) | No |
| 2 | canopy HTTP rate limiter | `juniper-canopy/src/security.py:159` (`_get_key` → `request.client.host`) | No |
| 3 | cascor WS per-IP cap (`ws_max_connections_per_ip=5`) | `juniper-cascor/src/api/settings.py:139` | No |
| 4 | cascor control handshake cooldown / IP blocklist | `juniper-cascor/src/api/websocket/control_security.py:76-148` (`HandshakeCooldown`, keyed `client_ip`); call sites `src/api/websocket/control_stream.py:102-105` (`_get_client_ip` → `websocket.client[0]`), `:116,:123,:128,:297-299` | No |
| 5 | cascor worker per-IP connection limiter | `juniper-cascor/src/api/workers/security.py:92-153` (`ConnectionRateLimiter`); call site `src/api/websocket/worker_stream.py:53` (`websocket.client[0]`) → `:54` | No |
| 6 | cascor HTTP rate limiter | `juniper-cascor/src/api/security.py:162` (`_get_key` → `request.client.host`) | No |
| 7 | `MetricsAuthMiddleware` IP allowlist (`/metrics`) | `juniper-observability/juniper_observability/middleware/metrics_auth.py:150-185` (reads `scope["client"]`) | No |

The **only** `X-Forwarded-*` handling anywhere in these two services is `X-Forwarded-Proto` for HSTS emission
(`juniper-cascor/src/api/middleware.py:53`; canopy the equivalent) — never for client identity.

**Docker DNAT collapses all clients to the bridge gateway (HO-3, audit §5.2).** Six concurrent WS from distinct host clients → 5
accepted, 6th rejected, with the log `Per-IP limit reached for 172.23.0.1 (5/5)` — i.e. every host client presents as the **bridge
gateway** `172.23.0.1`. Consequences, both live-confirmed:

- **Shared-IP self-DoS.** The per-IP caps and rate buckets are shared across *all* users; one client's 5 sockets exhaust the
  cap-of-5 for everyone (the same self-DoS as UX finding F-A). This is a live availability defect, not a theoretical one.
- **Metrics allowlist is defeated by dynamic IPAM.** The compose networks declare **no** static `ipam`/`subnet`
  (`juniper-deploy/docker-compose.yml:950-960` — `backend`/`data` are `internal:true`, `frontend`/`monitoring` are not), so Docker
  assigns subnets dynamically. The workaround widens `*_METRICS_TRUSTED_IPS` to whole bridge spaces `172.18.0.0/16` …
  `172.21.0.0/16` (`juniper-deploy/.env.observability:45-47`, keyed to "the four compose networks", `:43-44`) — but the **live
  bridge was `172.23.0.0/16`, outside that range**. Either Prometheus scrapes **403** (availability failure) or the allowlist is
  widened so broadly that **any** container on the subnet may scrape (authorization failure). Prometheus itself sits on **all four**
  networks (`docker-compose.yml` per-service `networks:` for `prometheus`), so it can reach every target — the allowlist is the only
  thing nominally distinguishing "Prometheus may scrape" from "anything on the bridge may scrape", and NAT + dynamic IPAM makes that
  distinction unreliable.

**Note (already self-aware in code).** `HandshakeCooldown`'s docstring calls itself a "NAT-hostile escape hatch"
(`control_security.py:82`) — the code already knows per-IP blocking degrades under NAT. **Nuance:** controls #2, #5, #6 are
**default-disabled** — `rate_limit_enabled=False` (canopy `settings.py:293`, cascor `settings.py:276`), `worker_rate_limit_enabled`
default off (cascor `settings.py:351`, wired only `if enabled` at `src/api/app.py:124-127`). canopy's HTTP limiter is turned **on**
in the deploy (`docker-compose.yml:572`). Enabled or not, the SEC-F19 point is about the **identity key**, which is the shared
gateway regardless.

**Good-news to preserve (verified strengths, audit §4.1).** `MetricsAuthMiddleware` is **fail-closed** on an absent/unparseable
client IP (403, `metrics_auth.py:175-184`) and **fail-loud** on a bad allowlist CIDR (`parse_trusted_networks` raises at init,
`:65-84`); it unwraps IPv4-mapped IPv6 before the membership check (`normalize_client_ip`, `:87-101`); its default is loopback-only
(`METRICS_DEFAULT_TRUSTED_IPS = ("127.0.0.1", "::1")`, `:49`). The remediation must **not** regress these.

---

## 3. Shared root cause

Both findings are the same architectural fact seen from two angles:

> **The containerized stack uses network *position* as its trust boundary, but the IP-based mechanisms meant to enforce finer
> client distinctions inside that boundary are defeated by Docker NAT — every client presents as the bridge gateway IP.**

Two corollaries follow, and the remediation is organized around them:

1. **The coarse boundary is real and load-bearing.** Loopback host binds (`docker-compose.yml:557` and siblings) and `internal:true`
   networks (`:950-956`) are the actual security perimeter. SEC-F22's exploit is impossible from off-host precisely because of the
   loopback bind; SEC-F19's `internal:true` nets are genuinely unroutable from outside. **This boundary is currently an *implicit
   default*, not an *enforced invariant*** — anyone who flips `BIND_HOST=0.0.0.0` (the documented escape hatch; `.env.example:11`
   ships it commented at loopback) silently converts SEC-F22 from "same-network-only" to "internet-reachable" with no guard rail.

2. **The fine-grained IP controls are not authenticators inside the NAT.** Per-IP caps, the metrics IP allowlist, and the Origin
   string-compare all degrade to either *network-scope* (which subnet) or *spoofable* (Origin) inside the bridge. Treating any of
   them as a *per-client authenticator* is the category error. They must be either (a) **replaced** by a component that sees real
   per-client identity (a fronting proxy setting a trusted `X-Forwarded-For`, plus a real credential), or (b) **re-scoped honestly**
   as DoS-dampening / network-scope authorization and paired with the coarse boundary.

The remediation therefore has two tiers: **make the coarse boundary explicit and enforced** (cheap, high-value, deployable now), and
**stop treating the fine IP controls as authentication** — re-scope them now, and replace them with real identity only when
remote/multi-user access becomes a requirement (the fronting-proxy milestone, which is the convergence point of both findings).

---

## 4. SEC-F22 — options, trade-offs, recommendation

### Option A — Enforce the network boundary (loopback + startup bind-guard + documented trust)

**Mechanism.** Keep the control surface loopback-bound (already the default). Add a **startup guard** in canopy (and, symmetrically,
cascor) that **refuses to start** if the service is configured to bind a **non-loopback** interface **unless** an explicit
attestation flag (working name `JUNIPER_<SVC>_FRONTING_AUTH_ATTESTED=true`) is set — the operator asserting a fronting
authenticating proxy is present. Document the in-network trust assumption as the deployment contract.

**Grounding.** The load-bearing precondition is already stated in the auth design §7.3 / §12 OQ-3; the guard converts that prose
assumption into an enforced invariant. The bind is read from `JUNIPER_CANOPY_SERVER__HOST` (`docker-compose.yml:570`,
`0.0.0.0`inside the container) with the host-side loopback publish at `docker-compose.yml:557`; the guard belongs at app startup
where `settings.server.host` is known, complementing (not replacing) the compose-level loopback publish.

**Pros.** Matches the stack's actual trust model and the design's own conclusion; **zero UX cost** (loopback operation is
unchanged); small, self-contained code change per service; directly closes the "silent `BIND_HOST=0.0.0.0`" footgun that turns
SEC-F22 internet-facing. Independently shippable and testable.

**Cons.** Adds no real credential — multi-user/remote still requires the proxy (deferred). The attest flag is an **attestation, not a
verification**: an operator can set it without actually deploying a proxy (mitigate by loud docs + a flag name that implies
responsibility, and by making the proxy the *only* supported non-loopback path).

### Option B — App-layer real credential

Two sub-variants; the task asks specifically whether **B actually closes the hole**. It does not, except in one large form.

**B1 — signed session-bound token injected into the served dashboard page**, required by `/api/train/*` in place of the
anonymously-mintable `/api/csrf` token.

- **Honest evaluation: B1 does NOT close SEC-F22.** The dashboard page (`GET /dashboard/`) is served **anonymously**
  (`canopy_constants.py:353`; §2.1). A page-injected token is therefore obtainable by **any in-network client that can `GET
  /dashboard/`** — exactly the SEC-F22 actor. B1 merely **relocates the anonymous mint** from `/api/csrf` to `/dashboard/`: the
  attacker does `GET /dashboard/`, scrapes the injected token, and replays it. Binding the token to the `canopy_session` cookie does
  not help against this actor either, because a non-browser client controls its own cookie jar — it takes the `Set-Cookie` from the
  same anonymous `GET /dashboard/` and replays cookie + token together. Session-binding defeats a **cross-site browser** attacker
  (who cannot read the token or send the `SameSite=Strict` cookie cross-site) — but that threat is **already** defeated by the
  current Origin+CSRF design. B1 adds cost without closing the confirmed hole.

**B2 — real dashboard login** (a user credential store, a login page, a session bound to an authenticated principal, `/dashboard`
and `/api/train/*` both requiring that session).

- **B2 does close SEC-F22**, because the token/session is only issued **after** authentication, so `GET /dashboard/` is no longer an
  anonymous oracle. But it is a **large** change: the platform has **no** user-auth machinery today (no login, no user store, no
  principal-bound session — verified §2.1). It carries real **UX cost** (every dashboard user needs credentials) and a new
  credential-management surface (storage, rotation, reset). For a single-user / trusted-LAN research dashboard this is
  disproportionate **unless** genuine remote/multi-user access is a requirement — at which point the login is best terminated at the
  **fronting proxy** (§6), not hand-rolled in canopy.

**Recommendation (SEC-F22): adopt Option A now; reject B1 as insufficient; defer B2 to the fronting-proxy milestone.**
The confirmed threat actor is an in-network **non-browser** client, and the only robust defenses against that actor are (i) keep it
off the port (the network boundary — Option A) or (ii) authenticate the dashboard itself (Option B2 / proxy). A page-injected token
(B1) is security theater against this actor and should be explicitly ruled out to prevent a future "we added a token, we're fine"
misread. Option A is the high-value, low-cost, zero-UX step that makes the sole effective control (loopback) an **enforced
invariant** and closes the silent-`0.0.0.0` footgun. B2/proxy is the correct answer **if and when** remote/multi-user access is
required, and it converges with the SEC-F19 structural fix (§6).

---

## 5. SEC-F19 — options, trade-offs, recommendation

### Option A — Honor `X-Forwarded-For`, but only from a configured trusted-proxy allowlist

**Mechanism.** Add trusted-proxy-aware client-IP resolution to canopy, cascor, and `MetricsAuthMiddleware`: when the direct peer is
the configured proxy IP, take the client identity from the right-most untrusted `X-Forwarded-For` hop; otherwise use the peer.

**Pros.** The **only** option that restores genuine per-client identity for the caps and the allowlist. Correct long-term fix.

**Cons.** **Inert without a fronting proxy** — behind the bare bridge the peer *is* the gateway and there is no XFF to read (there is
no proxy in the compose today: a search for traefik/nginx/caddy/haproxy in `juniper-deploy/docker-compose.yml` finds none). XFF is a
**classic footgun**: honoring it from **any** source is strictly worse than nothing (an attacker sets XFF to forge identity), so it
**must** be gated to the known proxy IP. This is a canopy + cascor + observability code change **plus** the proxy (deploy).

### Option B — Absolute GLOBAL connection caps + per-session caps (immediate; no proxy needed)

**Mechanism.** Add a stack-absolute **global** WS connection cap (protects total server resource) and a **per-session** cap keyed on
the `canopy_session` cookie / a per-connection token (restores per-user fairness **without** needing real client IP), alongside the
existing per-IP cap. Document the per-IP cap as **inert-behind-NAT**.

**Pros.** Directly kills the **live self-DoS** (HO-3): the per-session cap prevents one client monopolizing the shared cap-of-5, and
the global cap bounds total load. Pure app code in canopy (`websocket_manager.py`) and cascor (`control_stream.py` /
`worker_stream.py` and settings) — **deployable today, no proxy**. Negligible UX cost (legit single users unaffected).

**Cons.** Best-effort, **not** authentication — a determined attacker rotates sessions/cookies. The per-session key needs a fallback
for a first/cookieless WS (the **global cap backstops** that case). Requires the WS handlers to read the session cookie
(`websocket.headers`/cookies), which they do not do today.

### Option C — Fix the metrics allowlist: deterministic subnets + honest scoping

**Mechanism.** Two coordinated moves. **C1 (recommended):** pin the compose network subnets statically via `ipam.config.subnet`
(`docker-compose.yml:950-960`) and set `*_METRICS_TRUSTED_IPS` (`.env.observability:45-47`) to exactly those CIDRs, so Prometheus's
address is deterministic and the 172.23-vs-172.18-21 drift cannot recur. **C2 (complementary framing):** treat the IP allowlist as
**network-scope authorization** (which subnets may scrape), backed by `internal:true` isolation on `backend`/`data` and the
**fail-closed** `MetricsAuthMiddleware` — and **stop** treating it as per-host authentication.

**Pros.** C1 removes the dynamic-IPAM ambiguity that produced both the 403 (availability) and the whole-subnet-trust (authorization)
failures; small, deploy-local, zero UX. C2 is honest about what the control is.

**Cons.** C1 still trusts the whole (now-pinned) subnet — acceptable because those are the stack's own bridges and the real
isolation for `backend`/`data` is `internal:true`. But canopy/cascor `/metrics` is **also** exposed on the non-internal `frontend`
network and on the loopback host port, so the allowlist + loopback bind remain the operative controls there (C2 alone is
insufficient; C1 is needed). Pinned subnets must be chosen to avoid collision with other host Docker networks (document the choice).

**Recommendation (SEC-F19): a combination — B + C1 now, A deferred to the proxy milestone.**

- **Now (no proxy):** **Option B** (global + per-session caps) to kill the live self-DoS, and **Option C1** (pin subnets + reframe
  the allowlist) to make the metrics boundary deterministic. Both are app/deploy-local and independently shippable.
- **Structural (proxy milestone):** **Option A** (XFF-from-trusted-proxy) to restore real per-client identity — the same proxy that
  SEC-F22 B2 needs (§6).

**Security vs best-effort labeling (state this in the docs):** the global connection cap = **availability / DoS-dampening**
(best-effort); the per-session cap = **fairness / DoS-dampening** (best-effort); the metrics allowlist (C1) = **network-scope
authorization**, real only in combination with `internal:true` + fail-closed middleware (not per-host auth); XFF-from-trusted-proxy
(A) = the **only** mechanism that restores genuine per-client identity — and only as trustworthy as the proxy. The per-IP caps were
**never** authentication and must not be documented as such.

---

## 6. Convergence — the fronting authenticating proxy solves both

The deferred structural pieces of both findings are **the same component**. A single fronting authenticating reverse proxy (owner's
choice of mechanism — e.g. an OAuth2/OIDC proxy, HTTP basic-auth, or mTLS at the edge) delivers:

- **SEC-F22 B2:** the proxy authenticates the dashboard user before any request reaches canopy, so `GET /dashboard/` is no longer an
  anonymous token oracle and the in-network-foothold bypass is closed for the remote/multi-user case.
- **SEC-F19 A:** the proxy is the single trusted source of `X-Forwarded-For`, restoring real per-client identity for the caps and the
  metrics allowlist (canopy/cascor/observability honor XFF **only** from the proxy IP).

This convergence is why B2 and SEC-F19-A are **not** built now: they are one milestone, owner-gated, justified **only** when genuine
remote or multi-user access is a requirement. Until then, the loopback boundary (SEC-F22 A) + the DoS-dampening caps and deterministic
allowlist (SEC-F19 B + C1) are the correct, proportionate posture.

---

## 7. Sequencing, layering, and effort

| Phase | Decision(s) | Layer | Work unit | Effort | UX cost | Owner-gated? |
| --- | --- | --- | --- | --- | --- | --- |
| **0** — Ratify posture & document | D1, D8 | docs (juniper-deploy + canopy/cascor notes) | Write the deployment contract: network position IS the trust boundary; loopback default; `BIND_HOST=0.0.0.0` requires the proxy; per-IP caps are DoS-dampening, not auth | Low | None | No (docs) |
| **1** — Startup bind-guard | D2, D3 | **canopy code** + **cascor code** | Refuse non-loopback bind unless `…_FRONTING_AUTH_ATTESTED=true`; fail-closed + loud at startup. Rule out B1 in the design record | Low | None | Merge no; any deploy roll-out yes |
| **2** — Global + per-session WS caps | D4 | **canopy code** + **cascor code** | Add global + per-session caps to the WS managers; document per-IP cap inert-behind-NAT | Low–Med | Negligible | Merge no; deploy yes |
| **3** — Deterministic metrics subnets | D5 | **juniper-deploy** (compose + `.env.observability`) | Pin `ipam.config.subnet`; align `*_METRICS_TRUSTED_IPS`; reframe allowlist as network-scope | Low | None | **Yes** (deploy/env) |
| **4** — Fronting proxy + XFF + dashboard auth | D6, D7 | **deploy** (proxy) + **canopy/cascor/observability code** (XFF-from-trusted-proxy) | Only if remote/multi-user required; the SEC-F22/SEC-F19 convergence | High | Real (login) | **Yes** |

**Minimal high-value first step.** Phase 1 (bind-guard) for SEC-F22 and Phase 2 (caps) + Phase 3 (subnet pin) for SEC-F19. These
remove the live self-DoS, make the metrics boundary deterministic, and convert the sole effective SEC-F22 control (loopback) into an
enforced invariant — all without a proxy and without UX cost. Phase 4 is the larger effort, deferred until remote/multi-user access
is an actual requirement.

**Layering summary.** *canopy code:* bind-guard, global+per-session caps, (later) XFF resolution, (much later) — but preferably
never hand-rolled — dashboard auth. *cascor code:* symmetric bind-guard, global+per-session caps for control/worker WS, (later) XFF
resolution. *juniper-observability:* (later) XFF-aware client-IP in `MetricsAuthMiddleware`, gated to the trusted proxy. *juniper-
deploy:* pin subnets + allowlist alignment (now); the fronting proxy + loopback-contract docs (proxy milestone). *docs:* the
in-network trust contract; per-IP-cap-inert-behind-NAT; the deployment contract.

---

## 8. Decisions for owner ratification (D1–D8)

Each decision is independently ratifiable. Marked **(deploy-gated)** where roll-out is an owner-approved deploy/env change.

- **D1 — Adopt the stated posture.** Ratify that, for the containerized stack in its current single-user / trusted-LAN research
  mode, **network position is the trust boundary**: the control surface stays loopback-bound and any remote/multi-user access
  **requires** a fronting authenticating proxy. *(Recommended: yes.)*
- **D2 — Startup bind-guard (SEC-F22 primary).** canopy and cascor **refuse to start** when bound to a non-loopback interface unless
  an explicit `JUNIPER_<SVC>_FRONTING_AUTH_ATTESTED=true` (final name owner's) is set; fail-closed and loud. *(Recommended: yes.)*
- **D3 — Reject page-injected token (B1) as a SEC-F22 fix.** Record that a token injected into the anonymous `/dashboard/` page does
  **not** close the in-network bypass (it relocates the anonymous mint); real dashboard auth (B2) is deferred to D7. *(Recommended:
  yes.)*
- **D4 — Global + per-session WS caps (SEC-F19 primary).** Add stack-absolute global and per-session connection caps to canopy and
  cascor; document the per-IP cap as inert-behind-NAT (DoS-dampening, not auth). *(Recommended: yes.)*
- **D5 — Deterministic metrics subnets (SEC-F19 metrics). (deploy-gated)** Pin the compose network subnets (`ipam.config.subnet`),
  align `*_METRICS_TRUSTED_IPS` to exactly those CIDRs, and reframe the allowlist as network-scope authorization backed by
  `internal:true` + fail-closed middleware. *(Recommended: yes.)*
- **D6 — Defer XFF-from-trusted-proxy (SEC-F19 structural).** Do **not** honor `X-Forwarded-For` until a fronting proxy exists;
  specify that, once it does, XFF is trusted **only** from the configured proxy IP. *(Recommended: yes — defer, with the invariant
  written down now.)*
- **D7 — Fronting authenticating proxy as the convergence milestone. (deploy-gated)** When remote/multi-user access becomes a
  requirement, adopt a single fronting authenticating reverse proxy as the shared solution to both findings (auth for SEC-F22-B2;
  trusted XFF source for SEC-F19-A). Mechanism (OIDC / basic-auth / mTLS) and scope owner's choice. *(Recommended: adopt the
  principle now; schedule the build when the requirement is real.)*
- **D8 — Documentation.** Write the deployment contract (loopback default; the `BIND_HOST=0.0.0.0` escape hatch requires the proxy;
  per-IP caps are DoS-dampening) into `juniper-deploy` docs and the canopy/cascor security notes. *(Recommended: yes.)*

**Open questions for the owner.** (OQ-1) Final env-var name and semantics for the attestation flag (D2) — attestation vs a stronger
proxy-presence probe. (OQ-2) Whether cascor's control/worker WS need per-session caps or only the global cap (workers are keyed
callers; the browser control WS is the sharper case). (OQ-3) Chosen static subnet ranges for D5 (must avoid collision with other
host Docker networks). (OQ-4) Whether any programmatic consumer relies on `/api/train/*` today (grep the ecosystem; the key-OR path
keeps keyed callers working regardless).

---

## 9. Risks & testing strategy

**Risks.** (R1) The attest flag (D2) is an attestation, not a verification — an operator could set it without a real proxy; mitigate
with loud docs and by making the proxy the only supported non-loopback path (OQ-1). (R2) The per-session cap (D4) keyed on the
session cookie needs a cookieless-first-connection fallback; the global cap must backstop it. (R3) Pinned subnets (D5) can collide
with pre-existing host Docker networks; document and choose ranges deliberately (OQ-3). (R4) XFF trust (D6) is a footgun if ever
un-gated; the design must make "trust XFF only from the proxy IP" a hard invariant. (R5) Do not regress the verified
`MetricsAuthMiddleware` strengths (fail-closed on absent/unparseable IP, fail-loud on bad CIDR, IPv4-mapped-IPv6 unwrap).

**Testing.**

- **Bind-guard (D2):** unit tests — non-loopback host + no attest → refuse to start; non-loopback + attest → bind; loopback → bind
  regardless. Per repo (canopy, cascor).
- **Caps (D4):** unit tests — global cap saturates and rejects the N+1th connection stack-wide; per-session fairness under a shared
  peer IP (two sessions from one IP each keep their allocation); regression that a legit single user is unaffected. Re-run the HO-3
  probe on an isolated stack to confirm one client no longer self-DoSes all.
- **Metrics allowlist (D5):** the existing `MetricsAuthMiddleware` tests (fail-closed / fail-loud / IPv4-mapped) plus a **deploy
  drift check** asserting the pinned `ipam` subnets and `*_METRICS_TRUSTED_IPS` CIDRs agree (mirrors the ecosystem's existing drift
  lints; `compose config` in CI).
- **SEC-F22 posture (D2/D3):** re-run the HO-6 probe on an isolated **loopback** stack to confirm the gate behaves as the accepted
  posture describes (the Origin/CSRF bypass still "works" on the port, by design, until the proxy milestone — the point is that the
  guard now enforces that the port is loopback-only, so the actor cannot reach it off-host). Then, on a **non-loopback** isolated
  bring-up **without** the attest flag, confirm the service **refuses to start**.
- **Independent cross-validation.** Given the security stakes, route the implementing PRs through an independent read-only reviewer
  (the audit's multi-agent anti-hallucination pass, §5.1) before the design is treated as ratified, and include a **live** curl/WS
  matrix in each deploy roll-out (not unit-green alone — the canopy "green tests / dead app" class applies).

---

## 10. Appendix — key `file:line` references (re-verified 2026-07-03)

**SEC-F22 (juniper-canopy, `src/` repo-relative):**

- `ws_security.py:16-36` — `is_origin_allowed`: case-insensitive, trailing-slash-insensitive string equality; fail-closed on empty.
- `main.py:485-519` — `GET /api/csrf`; mint-refusal guard `:512` (refuses **only** a present-but-disallowed Origin → no-Origin and
  spoofed-allowlisted-Origin both mint).
- `security.py:286-305` — `browser_origin_allowed` (delegates to `is_origin_allowed`).
- `security.py:308-368` — `require_browser_control_auth`: keyed pass `:341-344`; auth-disabled open `:347-348`; flag-off 401
  `:354-356`; Origin allowlist `:359-360`; CSRF `:363-368`.
- `main.py:2917,2938,2952,2966,2980,2994` — the six `/api/train/*` routes, each `dependencies=[Depends(require_browser_control_auth)]`.
- `canopy_constants.py:380-381` — `KEY_EXEMPT_PATH_PREFIXES=("/api/train/",)`, `KEY_EXEMPT_PATHS=frozenset({"/api/csrf"})`;
  `:353` — `EXEMPT_PATH_PREFIXES=("/dashboard","/metrics")` (dashboard served anonymously).
- `middleware.py:163-181` — `_is_key_exempt` two-tier split (key-exempt but still rate-limited).
- `settings.py:135-140` — `allowed_origins`; `:141` — `max_connections_per_ip=5`; `:331` — `csrf_enabled=True`; `:332` —
  `csrf_token_ttl_seconds=3600`; `:341` — `browser_control_auth_enabled=True`.
- No login mechanism in `juniper-canopy/src/*.py` (repository search: none).
- `notes/JUNIPER_CANOPY_TRAINING-CONTROL-AUTH_DESIGN_2026-06-30.md` §7.3 (acknowledged residual), §12 OQ-3 (proxy/Origin caveat).
- juniper-deploy `docker-compose.yml:557` (canopy loopback publish), `:570-571` (in-container `0.0.0.0`), `:572` (rate limit on).

**SEC-F19 (per repo):**

- canopy `src/settings.py:141` (`max_connections_per_ip=5`); `src/communication/websocket_manager.py:366` (`check_per_ip_limit` →
  `websocket.client[0]`), `:381` (decrement); `src/security.py:159` (`_get_key` → `request.client.host`), default off `:293`.
- cascor `src/api/settings.py:139` (`ws_max_connections_per_ip=5`), `:276` (`rate_limit_enabled` off), `:351`
  (`worker_rate_limit_enabled` off); `src/api/security.py:162` (`_get_key` → `request.client.host`); `src/api/app.py:124-127`
  (worker limiter wired only if enabled); `src/api/middleware.py:53` (only `X-Forwarded-Proto`, for HSTS).
- cascor `src/api/websocket/control_security.py:76-148` (`HandshakeCooldown`, keyed `client_ip`; `:82` "NAT-hostile escape hatch"),
  `:20-36` (`validate_control_origin`); `src/api/websocket/control_stream.py:102-105` (`_get_client_ip` → `websocket.client[0]`),
  `:116,:123,:128,:297-299` (cooldown call sites).
- cascor `src/api/workers/security.py:92-153` (`ConnectionRateLimiter`); `src/api/websocket/worker_stream.py:53` (peer) → `:54`
  (`rate_limiter.allow`).
- observability `juniper_observability/middleware/metrics_auth.py:150-185` (`__call__`; `scope["client"]` `:153-154`; 403
  fail-closed `:175-184`), `:65-84` (`parse_trusted_networks`, fail-loud), `:87-101` (`normalize_client_ip`), `:49`
  (`METRICS_DEFAULT_TRUSTED_IPS` loopback-only).
- juniper-deploy `.env.observability:45-47` (`172.18-21.0.0/16` + loopback), `:43-44` (keyed to the four compose networks);
  `docker-compose.yml:950-960` (`backend`/`data` `internal:true`, `frontend`/`monitoring` not; no `ipam`/`subnet`); prometheus
  attached to all four networks (per-service `networks:`); no reverse proxy present (traefik/nginx/caddy/haproxy: none);
  `.env.example:11` (`# BIND_HOST=127.0.0.1`).

**Audit-sourced live evidence (isolated `secaudit`/127.0.0.2 stack, 2026-07-02; not re-run here):**

- HO-6 (SEC-F22): sidecar `172.23.0.5` → anonymous `/api/csrf` + spoofed `Origin: http://127.0.0.1:8050` → `POST /api/train/start`
  **200**; negative controls no-Origin **403**, no-CSRF **403** — audit §5.2.
- HO-3 (SEC-F19): 6 WS → 5 accept, 6th rejected; log `Per-IP limit reached for 172.23.0.1 (5/5)` (bridge gateway); live bridge
  `172.23.0.0/16` outside the `172.18-21` metrics allowlist — audit §5.2.

**Prior work / references:** `notes/JUNIPER_2026-07-02_JUNIPER-ECOSYSTEM_STACK-SECURITY-AUDIT-PLAN.md` (§4.1, §4.7, §5.2, §8 HO-3/HO-6);
`juniper-canopy/notes/JUNIPER_CANOPY_TRAINING-CONTROL-AUTH_DESIGN_2026-06-30.md` (§7.3 residual, the shipped gate);
`juniper-deploy/notes/poc/POC_REMEDIATION_PLAN_2026-05-27.md` (`MetricsAuthMiddleware` history);
`juniper-ml/notes/legacy/SECURITY_AUDIT_PLAN.md` (24-finding baseline).

> Every `file:line` above was re-confirmed in the working trees on 2026-07-03. The two live IPs are attributed to the audit's
> isolated-stack run (§5.2) and are not re-derived. This is a defensive hardening design for the owner's own stack; it contains no
> weaponized exploit. Decisions D1–D8 await owner ratification.
