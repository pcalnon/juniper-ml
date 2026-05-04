# A.9 + 3.2 State Analysis — Current Gaps and Proposed Fixes — 2026-05-03

**Project**: Juniper
**File Name**: A9_AND_3_2_STATE_ANALYSIS_2026-05-03.md
**Description**: Re-verifies two findings from the post-METRICS-MON observability
audit ([`OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md`](../code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md))
against current `origin/main` of all relevant repos: A.9 (12+ broad cascor
`cascor_ws_*` dead metrics) and 3.2 (Alertmanager `tickets` receiver placeholder).
Documents actual state, names what OBS-WIRE-01 (juniper-cascor#204) closed vs
left open, and proposes concrete next sub-tracks.
**Author**: Paul Calnon
**Version**: 0.1.0
**License**: MIT
**Status**: ACTIVE — entry-plan input for OBS-WIRE-02 / OBS-ROUTE-01

---

## 1. Purpose

Two of the post-METRICS-MON audit findings sit at a state-of-the-world boundary
that is hard to read from the audit doc alone after the OBS-WIRE-01 PR landed
the same day:

- **A.9** — 12+ broad `cascor_ws_*` dead metrics. OBS-WIRE-01 explicitly
  declared A.9 out of scope ("separate cleanup PR after dashboards/alerts are
  reviewed for which to keep"), but the audit doc itself does not yet reflect
  what that PR did or did not change.
- **3.2** — Alertmanager `tickets` receiver placeholder. juniper-deploy#51
  added the routing rule but left the receiver itself as a placeholder; the
  audit flagged this as a silent-drop risk for slow-burn alerts.

This doc:

1. Re-verifies each claim against the current `origin/main` of every relevant
   repo (cascor, deploy, canopy, data, ml).
2. Cites file:line for every "wired" / "still dead" assertion and shows the
   grep evidence for every "no callers" claim.
3. Proposes concrete next sub-tracks (OBS-WIRE-02, OBS-ROUTE-01) with
   estimated scope, sequencing, and entry-plan-style open questions.

This PR is **doc-only**. No code changes in cascor / deploy / canopy / data.

---

## 2. Cross-thread sync — what merged since the audit (PR juniper-ml#195)

The audit doc landed at 2026-05-03T21:29Z. Snapshot of merges across the
ecosystem since that timestamp:

| Repo | PR | Title | Merged | Touches A.9 / 3.2? |
|------|-----|-------|--------|--------------------|
| juniper-cascor | #204 | obs-wire-01: wire 5 cascor metric emission sites + lazy-init race fix | 23:39Z | A.9: explicitly out of scope; 2 of the 12+ helpers (`broadcast_send_duration_seconds`, `ws_observe_command_handler`) wired |
| juniper-cascor | #205 | fix(tests): session-end cleanup — reap orphans + flush stdout before os._exit | 23:43Z | No |
| juniper-cascor | #203 | fix(parallelism): close RC-4 candidate-training race + ring-buffer instrumentation (P-1) | 23:38Z | No (different metric family) |
| juniper-cascor | #197–202 | replay/test/network mutation work | 20:46–21:37Z | No |
| juniper-canopy | #220–223 | replay V2 + adapter work | 20:12–23:37Z | No |
| juniper-ml | #196 | feat(util): reap_pytest_orphans.bash | 23:34Z | No |
| juniper-deploy | (none since #51 at 20:37Z) | — | — | No new alertmanager / route changes |
| juniper-data | (none since 00:30Z) | — | — | No |

**Bottom line**: between the audit landing and now, OBS-WIRE-01 (juniper-cascor#204)
is the only PR that materially shifts the picture. It closed audit findings
A.1 / A.2 / A.3 / A.5 / A.6 / E.1, and explicitly *deferred* A.9. Nothing
since #51 has touched alertmanager.yml.

Verification commands used:

```bash
for r in juniper-cascor juniper-deploy juniper-canopy juniper-data juniper-ml; do
  cd /home/pcalnon/Development/python/Juniper/$r && git fetch origin
done
gh pr list --repo pcalnon/<repo> --state merged --search "merged:>=2026-05-03"
```

---

## 3. A.9 state per metric

The 12 broad WS metric helpers defined in
[`juniper-cascor/src/api/observability.py`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/observability.py)
lines 454–633. Each subsection grep is

```bash
grep -rn "<helper>" src/ --include="*.py" | grep -v "tests/" | grep -v "observability.py"
```

run inside `/home/pcalnon/Development/python/Juniper/juniper-cascor` at HEAD
`df906d0`. "Still dead" means the grep returned **zero** non-test, non-definition
matches.

Bonus: zero references to any `cascor_ws_*` metric exist anywhere in
`juniper-deploy/grafana/`, `juniper-deploy/prometheus/alert_rules.yml`, or
`juniper-deploy/prometheus/recording_rules.yml`. Confirmed via:

```bash
grep -c "cascor_ws_\|ws_broadcast\|ws_command_handler\|ws_seq\|ws_replay\|ws_resume\|ws_state_throttle\|ws_connections\|ws_command_responses" \
  prometheus/alert_rules.yml prometheus/recording_rules.yml \
  grafana/provisioning/dashboards/juniper-cascor.json
# all three: 0
```

So no dashboard / alert deletions are needed if any of these are pruned.

### 3.1 `ws_set_seq_current` — STILL DEAD — REMOVE

- Definition: `observability.py:581-583` (helper) + metric register at lines 470–474 (`cascor_ws_seq_current` Gauge)
- Production callers: **none** (grep result empty)
- Plausible wire-site: `WebSocketManager._assign_seq_and_buffer`
  ([`manager.py:304-318`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/websocket/manager.py#L304-L318))
  could call `ws_set_seq_current(seq)` after `seq = self._next_seq; self._next_seq += 1`.
- However: the value is monotonic and unbounded. As an SLI it is a poor
  signal — exposing the seq counter alone tells nothing about freshness or
  drop rate. The actually useful health signal would be a per-connection
  *seq lag* gauge, which the current scaffolding does not support.
- **Action**: REMOVE both the helper and the metric definition. Re-introduce
  later if a real SLI 4.x entry asks for it.

### 3.2 `ws_set_replay_buffer_occupancy` — STILL DEAD — WIRE (cheap)

- Definition: `observability.py:586-588` + metric at lines 475–479
- Production callers: **none**
- Wire-site (cheap): `WebSocketManager._assign_seq_and_buffer`
  ([`manager.py:312-318`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/websocket/manager.py#L312-L318))
  already holds `self._seq_lock` while doing `self._replay_buffer.append(enriched)`.
  Add `ws_set_replay_buffer_occupancy(len(self._replay_buffer))` after the append
  (still inside the lock — `len()` is O(1) on deque).
- Why useful: paired with `ws_set_replay_buffer_capacity` (3.3) gives an
  occupancy ratio gauge for "replay buffer pressure", an early warning for
  D-15 resume failures.
- **Action**: WIRE in `manager.py:317`.

### 3.3 `ws_set_replay_buffer_capacity` — STILL DEAD — WIRE (one-shot)

- Definition: `observability.py:591-593` + metric at lines 485–489
- Production callers: **none**
- Wire-site: `WebSocketManager.__init__`
  ([`manager.py:62-130`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/websocket/manager.py#L62-L130))
  after `self._replay_buffer_max_size = max_replay_buffer_size` (line 94).
  One call: `ws_set_replay_buffer_capacity(max_replay_buffer_size)`.
- **Action**: WIRE in `manager.py:94`. Guard with `try/except` matching the
  OBS-WIRE-01 pattern (defensive against test-time prometheus_client absence).

### 3.4 `ws_inc_resume_requests` — STILL DEAD — WIRE (high value)

- Definition: `observability.py:596-598` + Counter at lines 490–495 with
  `["outcome"]` label (closed set: `success`, `out_of_range`, `malformed_resume`,
  `server_restarted`, etc.).
- Production callers: **none**
- Wire-site: `_handle_resume_message` in
  [`training_stream.py:240-301`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/websocket/training_stream.py#L240-L301)
  has 4 distinct outcomes already returning early:
  - line 256 → `outcome="malformed_resume"`
  - line 269 → `outcome="server_restarted"`
  - line 283 → `outcome="out_of_range"`
  - line 300 → `outcome="success"`
- Why high value: D-15 resume is the single most safety-critical WS path
  (data continuity guarantee). A counter by outcome surfaces per-outcome
  rates without re-walking logs.
- **Action**: WIRE four `ws_inc_resume_requests("...")` calls at the cited
  sites in `training_stream.py`.

### 3.5 `ws_observe_resume_replayed` — STILL DEAD — WIRE (paired with 3.4)

- Definition: `observability.py:601-603` + Histogram at lines 496–506 with
  R4.1-tentative buckets `(0, 1, 5, 25, 100, 500, 1024)`.
- Production callers: **none**
- Wire-site: same module as 3.4, immediately before line 300 (`logger.info("Resume succeeded ...")`):
  `ws_observe_resume_replayed(len(events))`.
- **Action**: WIRE at `training_stream.py:299`. Together with 3.4 this gives
  a (rate, distribution) pair for the resume path.

### 3.6 `ws_inc_broadcast_timeout` — STILL DEAD — WIRE (paired with SLI 4.3)

- Definition: `observability.py:606-608` + Counter at lines 507–512 with
  `["type"]` label (closed-by-convention message-type set).
- Production callers: **none**
- Wire-site: [`manager.py:500-504`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/websocket/manager.py#L500-L504)
  `_send_json` `except asyncio.TimeoutError` block already classifies the
  timeout. Add `ws_inc_broadcast_timeout(msg_type)` immediately before
  `return False` (msg_type is already computed at line 493).
- Why useful: SLI 4.3 already tracks fan-out p95 via
  `broadcast_send_duration_seconds`, but a timeout-only counter is the
  numerator of an alarm-grade availability ratio without histogram-quantile
  estimation lag.
- **Action**: WIRE in the `asyncio.TimeoutError` branch at `manager.py:501`.

### 3.7 `ws_inc_state_throttle_coalesced` — STILL DEAD — WIRE (paired with GAP-WS-21)

- Definition: `observability.py:611-613` + Counter at lines 532–536 (no labels)
- Production callers: **none**
- Wire-site: [`lifecycle/manager.py:1186-1191`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/lifecycle/manager.py#L1186-L1191)
  is the GAP-WS-21 throttle. Inside the `if not force and not is_terminal:`
  branch, the `return` at line 1190 happens iff a state broadcast was
  coalesced. Call `ws_inc_state_throttle_coalesced()` immediately before
  the `return`.
- Why useful: confirms the throttle is doing its job; a sudden zero-rate
  here while broadcast count is high is a regression signal.
- **Action**: WIRE at `lifecycle/manager.py:1190`.

### 3.8 `ws_inc_broadcast_from_thread_errors` — STILL DEAD — WIRE (paired with GAP-WS-29)

- Definition: `observability.py:616-618` + Counter at lines 537–541 (no labels)
- Production callers: **none**
- Wire-site: [`manager.py:449-457`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/websocket/manager.py#L449-L457)
  `_log_broadcast_exception` is the GAP-WS-29 done-callback. The
  `if exc is not None:` branch (line 456) is the only place the error
  path is observed today (currently log-only). Call
  `ws_inc_broadcast_from_thread_errors()` immediately after the
  `logger.error(...)`.
- **Action**: WIRE at `manager.py:457`.

### 3.9 `ws_set_connections_active` — STILL DEAD — REMOVE or RE-DESIGN

- Definition: `observability.py:621-623` + Gauge at lines 547–552 with
  `["endpoint"]` label
- Production callers: **none**
- The `["endpoint"]` label is undefined at definition time — there is no
  closed enum. The natural value is `/v1/ws/training` vs `/v1/ws/control`,
  which `WebSocketManager` does not currently distinguish (a single
  `_active_connections` set holds both).
- Wire-sites that *would* work require a per-endpoint counter pair on
  `WebSocketManager`, which is a non-trivial refactor.
- Cheap alternative: the existing `connection_count` property is
  unlabeled. Define a sibling unlabeled gauge `cascor_ws_connections_active`
  (no label) and emit at every connect/disconnect/promote site
  ([`manager.py:227, 262, 281, 294-298`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/websocket/manager.py)).
- **Action**: REMOVE the labeled variant; if needed, ship a label-free
  replacement in OBS-WIRE-02 wired into the existing 4 sites that already
  log connection count changes. (Decision deferred to entry-plan Q3.)

### 3.10 `ws_inc_command_responses` — STILL DEAD — WIRE (cheap, paired with 3.11 SLI 4.4)

- Definition: `observability.py:626-628` + Counter at lines 553–558 with
  `["command", "status"]` labels (status is closed set: `success`, `error`)
- Production callers: **none**
- Wire-site: [`control_stream.py:172-186`](https://github.com/pcalnon/juniper-cascor/blob/df906d0/src/api/websocket/control_stream.py#L172-L186)
  `_handle_command_message` already branches `success` / `TimeoutError` /
  generic `Exception`, each calling `websocket.send_json(create_control_ack_message(command, "<status>", ...))`.
  Add `ws_inc_command_responses(command, "<status>")` immediately after
  each `send_json` (3 sites: line 178 success, 182 timeout-as-error, 186 error).
- Why useful: paired with `command_handler_seconds` (already wired in
  OBS-WIRE-01) gives a (rate, error-rate, latency) Tugger triple for
  control-plane SLI 4.4.
- **Action**: WIRE 3 calls in `control_stream.py:179, 183, 187`.

### 3.11 `ws_observe_command_handler` — ALREADY WIRED (since OBS-WIRE-01)

- Definition: `observability.py:631-633` + Histogram at lines 559–576 (sub-ms buckets)
- Production callers (grep result):
  ```
  src/api/websocket/control_stream.py:192:        from api.observability import ws_observe_command_handler
  src/api/websocket/control_stream.py:194:        ws_observe_command_handler(command, handler_duration)
  src/api/websocket/control_stream.py:196:        logger.debug("ws_observe_command_handler emission failed", exc_info=True)
  ```
- This was the A.3 / SLI 4.4 wire shipped in PR #204. `cascor_ws_command_handler_seconds`
  is now live.
- **Action**: NONE. Already done.

### 3.12 `cascor_ws_seq_gap_detected_total` (Counter, no helper) — STILL DEAD — KEEP-AS-IS (server-side gap detection not feasible)

- Definition: lines 542–546 (`seq_gap_detected_total`). No emission helper
  was written.
- The semantic ("sequence gaps detected — should be zero in healthy
  operation") is **client-side** truth: gaps are detected on the
  consuming side (canopy) when `received.seq != last_seen.seq + 1`. The
  server emits monotonically and has no read-back signal that would let
  it observe its own gaps.
- A self-test could synthesise a gap detection by re-walking the replay
  buffer, but that monitors the buffer's invariants, not actual on-the-wire
  gaps that would be caused by client-side packet reordering or socket-level
  drops.
- Two coherent next steps: (a) remove this server-side metric and add a
  canopy-side counter that emits on actual client-observed gaps, exposed
  via canopy's `/metrics` endpoint; or (b) keep the server-side metric
  but rename / scope it to "buffer integrity violations" wired in
  `_assign_seq_and_buffer` as an assertion.
- **Action**: KEEP-AS-IS for now, **but flag for design decision**: remove
  server-side, add client-side gap counter to canopy. (Entry-plan Q1.)

### 3.13 Bonus discovery — `broadcast_send_duration_seconds` already wired (since OBS-WIRE-01)

Audit §4.1 listed `broadcast_send_duration_seconds` as part of the dead-metric
surface. PR #204 wired it. Grep:

```
src/api/websocket/manager.py:518: _ensure_ws_metrics()["broadcast_send_duration_seconds"].labels(type=msg_type).observe(...)
```

Documented here so OBS-WIRE-02 does not re-touch it.

### 3.14 Audit-incomplete enumeration check

Re-grep for any other `ws_*` helper in `observability.py:454-633`:

```bash
grep -nE "^def ws_" src/api/observability.py
```

Yields exactly the 11 helpers covered in 3.1–3.11. No undisclosed ws_*
helpers. The seq_gap counter (3.12) is the only definition without a
helper. Total = 12 metric definitions, 11 helpers.

### 3.15 Summary table

| # | Metric / helper | Audit state | Current state (2026-05-03) | Recommended action |
|---|-----------------|-------------|----------------------------|-------------------|
| 1 | `ws_set_seq_current` | dead | dead | **REMOVE** |
| 2 | `ws_set_replay_buffer_occupancy` | dead | dead | **WIRE** at `manager.py:317` |
| 3 | `ws_set_replay_buffer_capacity` | dead | dead | **WIRE** at `manager.py:94` |
| 4 | `ws_inc_resume_requests` | dead | dead | **WIRE** at `training_stream.py:256, 269, 283, 299` |
| 5 | `ws_observe_resume_replayed` | dead | dead | **WIRE** at `training_stream.py:299` |
| 6 | `ws_inc_broadcast_timeout` | dead | dead | **WIRE** at `manager.py:501` |
| 7 | `ws_inc_state_throttle_coalesced` | dead | dead | **WIRE** at `lifecycle/manager.py:1190` |
| 8 | `ws_inc_broadcast_from_thread_errors` | dead | dead | **WIRE** at `manager.py:457` |
| 9 | `ws_set_connections_active` | dead | dead | **REMOVE** (or replace with label-free variant — entry-plan Q3) |
| 10 | `ws_inc_command_responses` | dead | dead | **WIRE** at `control_stream.py:179, 183, 187` |
| 11 | `ws_observe_command_handler` | dead | **wired by OBS-WIRE-01** (A.3) | none |
| 12 | `cascor_ws_seq_gap_detected_total` (no helper) | dead, no helper | dead, no helper | **KEEP-AS-IS pending design** (entry-plan Q1) |
| bonus | `cascor_ws_broadcast_send_duration_seconds` | dead | **wired by OBS-WIRE-01** (A.3) | none |

**Net A.9 state**: 9 helpers + 1 counter still dead (down from 12+ in the
audit). 2 helpers wired since audit landing.

---

## 4. Finding 3.2 state — Alertmanager `tickets` receiver placeholder

### 4.1 Current `alertmanager.yml` (juniper-deploy@`f48c5cc`)

Receivers section (verbatim, [`alertmanager/alertmanager.yml:39-65`](https://github.com/pcalnon/juniper-deploy/blob/f48c5cc/alertmanager/alertmanager.yml#L39-L65)):

```yaml
receivers:
  # Configure notification channels here (email, Slack, PagerDuty, etc.)
  - name: "default"

  # Critical / page receivers share this entry — high-priority routing
  # for both `severity: critical` and `severity: page` (R5.4 burn-rate
  # fast-burn / MWMBR pager alerts).  Configure with PagerDuty or
  # similar for on-call escalation.
  - name: "critical"

  # Tickets receiver — non-paging channel for `severity: ticket`
  # (R5.4 burn-rate slow-burn alerts).  Should route to a
  # ticket-tracker (Jira, GitHub Issues, low-priority Slack channel,
  # email DL) — NOT to PagerDuty.
  # PLACEHOLDER — configure before production use.  Until configured
  # this receiver silently drops alerts, which is acceptable for the
  # R5.4 30-day soak (catalog §2.6) but MUST be wired before lifting
  # log-only severity on SLO 3.3 / 3.4.
  - name: "tickets"
```

### 4.2 Verdict — STILL A PLACEHOLDER

All three receivers (`default`, `critical`, `tickets`) are name-only stubs.
The audit claim from §3.2 is fully accurate. No deploy PR has touched the
receiver definitions since juniper-deploy#51. Confirmed via:

```bash
gh pr list --repo pcalnon/juniper-deploy --state merged --search "merged:>=2026-05-03"
# returns only #46–#51, last-touched 2026-05-03T20:37Z
```

### 4.3 Sibling concern — B.1 (severity: warning / info fall-through)

Routing tree currently dispatches:

| `severity` | Receiver | Repeat |
|------------|----------|--------|
| `critical` | `critical` | 1h |
| `page` (R5.4 fast-burn) | `critical` | 1h |
| `ticket` (R5.4 slow-burn) | `tickets` | 12h |
| `warning`, `info`, anything else | `default` (the route's top-level receiver) | 4h |

So `warning` / `info` *do* land on `default` — they are not silently
unrouted. But `default` is itself a name-only stub. The B.1 finding is
therefore a special case of the same root cause as 3.2: every receiver is
a stub. A single sub-track that wires all three receivers fixes both.

### 4.4 Three concrete options for wiring real notification

**Option A — GitHub Issues webhook (recommended for ticket-tier)**

```yaml
- name: "tickets"
  webhook_configs:
    - url: "https://api.github.com/repos/pcalnon/juniper-deploy/dispatches"
      send_resolved: true
      http_config:
        bearer_token_file: /etc/alertmanager/secrets/github_token
      max_alerts: 0
```

| Trade-off | Note |
|-----------|------|
| Complexity | Medium. Requires a small webhook bridge service or a custom payload mapper — Alertmanager's native webhook payload doesn't match the GitHub `repository_dispatch` schema. The cleanest path is `prometheus-msteams`-style sidecar or a tiny FastAPI bridge. |
| Secrets | One PAT with `repo` scope. Stored via SOPS-encrypted env per the project's [`SOPS_USAGE_GUIDE.md`](../SOPS_USAGE_GUIDE.md) pattern. Mount at `/etc/alertmanager/secrets/`. |
| Operational footprint | Adds 1 sidecar container to `juniper-deploy/docker-compose.yml`. Alerts produce GitHub issues with a `slow-burn` label. |

**Option B — Email (SMTP) via Gmail relay**

```yaml
global:
  smtp_smarthost: "smtp.gmail.com:587"
  smtp_from: "juniper-alerts@example.com"
  smtp_auth_username: "juniper-alerts@example.com"
  smtp_auth_password_file: /etc/alertmanager/secrets/smtp_password
  smtp_require_tls: true

receivers:
  - name: "tickets"
    email_configs:
      - to: "overtoad.research@gmail.com"
        send_resolved: true
        headers:
          Subject: "[juniper slow-burn] {{ .GroupLabels.alertname }}"
```

| Trade-off | Note |
|-----------|------|
| Complexity | Low. Native Alertmanager support, no sidecar. |
| Secrets | One SMTP app password (Gmail) stored via SOPS. Environment var injection via docker-compose `env_file: .env.enc` pattern. |
| Operational footprint | Zero infra add. Email volume capped by Alertmanager's `repeat_interval: 12h` for slow-burn. |

**Option C — Explicit `null` receiver (acknowledge silent drop for soak window)**

```yaml
- name: "tickets"
  # Explicit no-op during the R5.4 30-day soak window (catalog §2.6).
  # Slow-burn alerts are observable via Alertmanager UI / Prometheus
  # `ALERTS{alertstate="firing"}`. Will be replaced with Option A or B
  # before soak window closes (target 2026-06-02).
```

| Trade-off | Note |
|-----------|------|
| Complexity | Trivial. Comment-only. |
| Secrets | None. |
| Operational footprint | None — but defers the real work. **Only acceptable if the soak window is actively enforced** (i.e., a calendar reminder + a CI check that flags the empty-receiver state on the 30-day deadline). |

### 4.5 Recommendation

**Ship Option B (email) for both `critical` and `tickets` immediately**, with a
follow-up to upgrade `critical` to PagerDuty once on-call rotation is
established. Rationale:

- Option C defers real work and the soak window calendar is not currently
  enforced anywhere in CI. Comment-only fixes have a track record of being
  forgotten.
- Option A's payload-mapping complexity is unjustified for a slow-burn tier
  that fires once per 12h at most.
- Option B is the smallest viable wire-up, uses Gmail's existing free SMTP
  relay, and the SOPS pattern already exists in this repo for secret
  management.
- Bonus: `default` should also switch to Option B with a longer
  `repeat_interval` so warning/info alerts (B.1) don't disappear into
  `/dev/null` either.

### 4.6 B.1 wider routing audit — no new rules since #51

Confirmed via `git log --oneline -- alertmanager/ prometheus/` on origin/main:
last commit touching either path is f48c5cc (PR #51). No new severity values
have appeared in `prometheus/alert_rules.yml` since then either.

---

## 5. Recommended next sub-tracks

### 5.1 OBS-WIRE-02 — A.9 cleanup (cascor)

**Scope**: 1 PR against `juniper-cascor`.

| Phase | Files | Action |
|-------|-------|--------|
| Wire | `src/api/websocket/manager.py` | 4 emission sites: replay-buffer occupancy, replay-buffer capacity init, broadcast timeout counter, broadcast-from-thread errors |
| Wire | `src/api/websocket/training_stream.py` | 5 emission sites: 4 outcome arms + replay count histogram |
| Wire | `src/api/websocket/control_stream.py` | 3 emission sites: command-response counter at success / timeout / error arms |
| Wire | `src/api/lifecycle/manager.py` | 1 emission site: state-throttle-coalesced counter |
| Remove | `src/api/observability.py` | Drop `ws_set_seq_current` helper + `cascor_ws_seq_current` Gauge definition; drop `ws_set_connections_active` helper + labeled `cascor_ws_connections_active` (entry-plan Q3 may swap this for a label-free replacement) |
| Test | `src/tests/unit/api/test_metrics_obs_wire_02.py` (new) | Per-helper test, mirroring OBS-WIRE-01 layout (one class per metric, success + failure + label-fallback paths) |

**Rough delta**: 9 wire calls, 2 metric removals, 1 new test file (~13–18
methods). PR count: **1**. File count: **5 cascor source + 1 new test = 6**.

**Out of scope**: 3.12 (`seq_gap_detected_total`) and the label-free
`connections_active` redesign — both deferred to entry-plan resolution.

### 5.2 OBS-ROUTE-01 — Alertmanager wire-up (deploy)

**Scope**: 1 PR against `juniper-deploy`.

| File | Action |
|------|--------|
| `alertmanager/alertmanager.yml` | Replace 3 placeholder receivers with Option B (email) configs; add `global.smtp_*` block |
| `.env.enc` (SOPS-encrypted) | Add `SMTP_PASSWORD` value (Gmail app password) |
| `docker-compose.yml` | Mount the SMTP password file into the alertmanager container |
| `notes/runbooks/SLO_ALERT_TRIAGE.md` (new) | One-pager for what an email alert means + how to silence |

**Rough delta**: 1 yaml file modified, 1 env file re-encrypted, 1 compose
file modified, 1 new runbook. PR count: **1**. File count: **4**.

**Optional follow-up sub-track OBS-ROUTE-02** (not part of the initial
PR): swap `critical` from email to PagerDuty once on-call rotation is
real. No-op until that policy decision lands.

### 5.3 Sequencing

```
            (independent — can run in parallel)
        ┌────────────────────────┐
        │                        │
        ▼                        ▼
   OBS-WIRE-02              OBS-ROUTE-01
   (cascor)                 (deploy)
        │                        │
        └─────────┬──────────────┘
                  ▼
         OBS-VERIFY-01 (optional)
         Run real cascor + deploy stack in
         juniper-deploy compose, hit
         /metrics, confirm WS gauges populate,
         force a synthetic burn-rate alert,
         confirm email lands.
```

OBS-WIRE-02 and OBS-ROUTE-01 are **independent** — they touch different
repos, no shared files, no dependency between the new wire calls and the
new alert receivers. Either can ship first. OBS-VERIFY-01 (a tiny smoke
test, not a full sub-track) gates "soak start" but is not a hard
dependency for either.

### 5.4 Open questions for entry-plan resolution

Mirroring the METRICS-MON entry-plan Q-format:

**Q1 — A.9 §3.12: server-side or client-side seq-gap detection?**
The `cascor_ws_seq_gap_detected_total` counter has no semantically valid
server-side wire-site. Options: (a) remove server-side, add client-side
gap counter to canopy emitted at `/metrics`; (b) repurpose server-side
metric to monitor replay-buffer integrity invariants; (c) leave as-is
indefinitely. **Decision needed before OBS-WIRE-02 PR opens.**

**Q2 — 3.2 receiver shape: Option A / B / C?**
This doc recommends Option B (email). User confirmation needed before
OBS-ROUTE-01 PR opens — Option A vs B is a >$0 vs $0 (Gmail free)
operational cost difference; Option C is a calendar-discipline bet.

**Q3 — A.9 §3.9: keep, replace, or remove `ws_set_connections_active`?**
Three sub-options: (a) remove the labeled gauge entirely; (b) replace
with a label-free `cascor_ws_connections_active` (no `endpoint` label)
wired into the 4 existing connect/disconnect/promote sites; (c) keep
labeled gauge and refactor `WebSocketManager` to track active set per
endpoint (large change, out of OBS-WIRE-02 scope). **Defaulting to (a)
remove — confirm before OBS-WIRE-02 PR opens.**

**Q4 — 3.12 + B.1 follow-up: a sister sub-track for canopy-side gap counter?**
Tied to Q1(a). If we go that route, OBS-WIRE-03 against juniper-canopy
would add a small Counter + emission in the WS recv loop. Out of scope
for this analysis but flagged.

**Q5 — Soak window enforcement?**
Audit §3.2 says the placeholder is "acceptable for the R5.4 30-day soak
(catalog §2.6) but MUST be wired before lifting log-only severity on
SLO 3.3 / 3.4." If we ship OBS-ROUTE-01 now, the soak window question is
moot. If we defer, we need a CI check or calendar reminder. **Recommended:
ship OBS-ROUTE-01 now.**

---

## 6. References

### Audit and prior-art docs
- juniper-ml#195 — [`OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md`](../code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md) — the parent audit doc; §4.1 + §5 (A.9 row), §3.2
- juniper-ml#192 — [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../code-review/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) — METRICS-MON close, identifies 6 residuals
- juniper-ml#187 — [`METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md`](../code-review/METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md) — Q-style entry-plan format reference
- [`SOPS_USAGE_GUIDE.md`](../SOPS_USAGE_GUIDE.md) — SOPS pattern referenced in §4.4

### Cross-thread merges (A.9-relevant)
- juniper-cascor#204 — `obs-wire-01` — wired A.3 (`broadcast_send_duration_seconds`, `command_handler_seconds`); explicitly deferred A.9 (PR body "Out of scope" section)
- juniper-cascor#205 — session-end test cleanup (no observability impact)

### Cross-thread merges (3.2-relevant)
- juniper-deploy#51 — Wave-2 fixup; added `severity: page` / `severity: ticket` routes + placeholder `tickets` receiver
- juniper-deploy#50 — R5.4 burn-rate alerts (the firing source for `severity: page` / `ticket`)

### cascor source files cited (all verified at HEAD `df906d0`)
- `src/api/observability.py:443-633` — WS metric defs + 11 helpers
- `src/api/websocket/manager.py:62-130` — `WebSocketManager.__init__`
- `src/api/websocket/manager.py:220-298` — connect / disconnect / promote
- `src/api/websocket/manager.py:304-318` — `_assign_seq_and_buffer`
- `src/api/websocket/manager.py:415-431` — `broadcast`
- `src/api/websocket/manager.py:432-457` — `broadcast_from_thread` + `_log_broadcast_exception`
- `src/api/websocket/manager.py:475-531` — `_send_json`
- `src/api/websocket/training_stream.py:240-301` — `_handle_resume_message`
- `src/api/websocket/control_stream.py:155-196` — `_handle_command_message`
- `src/api/lifecycle/manager.py:1186-1195` — GAP-WS-21 throttle in `_broadcast_state`

### deploy alertmanager / prometheus files cited (all verified at HEAD `f48c5cc`)
- `alertmanager/alertmanager.yml:1-74` — full file
- `prometheus/alert_rules.yml` — confirmed zero `cascor_ws_*` references
- `prometheus/recording_rules.yml` — confirmed zero `cascor_ws_*` references
- `grafana/provisioning/dashboards/juniper-cascor.json` — confirmed zero `cascor_ws_*` references

### Verification commands
```bash
# Sync repos
for r in juniper-cascor juniper-deploy juniper-canopy juniper-data juniper-ml; do
  cd /home/pcalnon/Development/python/Juniper/$r && git fetch origin
done

# A.9 helper grep loop
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
for fn in ws_set_seq_current ws_set_replay_buffer_occupancy ws_set_replay_buffer_capacity \
          ws_inc_resume_requests ws_observe_resume_replayed ws_inc_broadcast_timeout \
          ws_inc_state_throttle_coalesced ws_inc_broadcast_from_thread_errors \
          ws_set_connections_active ws_inc_command_responses ws_observe_command_handler; do
  echo "=== $fn ==="
  grep -rn "$fn" src/ --include="*.py" | grep -v "tests/" | grep -v "observability.py"
done

# 3.2 alertmanager check
cd /home/pcalnon/Development/python/Juniper/juniper-deploy
cat alertmanager/alertmanager.yml
gh pr list --repo pcalnon/juniper-deploy --state merged --search "merged:>=2026-05-03"

# Cross-thread merge sweep
for r in juniper-cascor juniper-deploy juniper-canopy juniper-data juniper-ml; do
  echo "=== $r ==="
  gh pr list --repo pcalnon/$r --state merged --search "merged:>=2026-05-03" \
    --json number,title,mergedAt
done
```
