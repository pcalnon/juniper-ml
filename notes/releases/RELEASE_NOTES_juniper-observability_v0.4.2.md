# juniper-observability v0.4.2 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-11-08
**Release Type:** Security Patch
**Priority:** High: upgrade every service that calls `configure_sentry`
**Package Affected:** juniper-observability

---

This is a security-bearing release of `juniper-observability` v0.4.2. `configure_sentry` now scrubs Sentry transactions as well as error events, redacts the request's parsed cookies, and filters four more credential headers. Before it, a sampled transaction carried the raw `X-API-Key` whenever `send_pii` was on; a cookie under any name the SDK's denylist lacks reached error events and transactions alike; and `Sec-WebSocket-Protocol`, `X-CSRF-Token` and `X-XSRF-Token` reached every item even with `send_pii` off. Every vector needs Sentry to be configured, and the first two also need `send_pii=True`, which only juniper-data can turn on (it is off by default), so the release is rated Medium. There is no public API change. A consumer image receives it with its next lock refresh.

---

## Security Impact (Medium)

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-observability` |
| **Fixed in** | 0.4.2 |
| **Vulnerability class** | Sensitive information sent to an external service ([CWE-201](https://cwe.mitre.org/data/definitions/201.html)) |
| **Advisory** | None. Internal findings: round-42 finding F2 (2026-09-24) and the validation of consolidated-plan item P3-07 (2026-11-08); there is no CVE or Dependabot alert |

---

## Changes in v0.4.2

### Security

- **Transactions are scrubbed too: `configure_sentry` installs its hook as
  `before_send_transaction`** (round-42 finding F2, consolidated-plan item P3-07). The SDK never
  hands a transaction to `before_send`, so the hook never saw one. Under `send_pii=True` the SDK's
  own header filter is off, and its `EventScrubber` redacts by name, with `x_api_key` on its
  denylist but not `x-api-key`. So every sampled transaction carried the raw `X-API-Key` header,
  while the error events beside it did not. The round-42 validation reproduced it on sentry-sdk
  2.58.0 and 2.70.0 (2026-09-24), and juniper-ml's
  `util/ad-hoc/2026-11-08_p3_07_sentry_wire_probe.py` on 2.74.0. The hook is installed whatever
  `traces_sample_rate` says: even at 0.0 the SDK sends a transaction that the caller's
  `sentry-trace` header marks sampled. Only juniper-data can turn `send_pii` on
  (`JUNIPER_DATA_SENTRY_SEND_PII`; opt-in and off by default, and no deploy config sets it).
  juniper-cascor and juniper-canopy never pass it, and juniper-cascor's own `sentry_sdk.init` in
  `main.py` sets `send_default_pii=False`.
- **The hook also redacts the request's parsed `cookies`.** Under `send_pii=True` the Starlette
  and FastAPI integrations add `request.cookies`, the `Cookie` header parsed into names and
  values, beside the header the hook already filtered. The SDK's denylist redacts a cookie by name
  (`session`, `csrftoken` and others), so a cookie under any other name reached the wire, in error
  events and in transactions. Every value of a non-empty `cookies` dict is now `[Filtered]`, and
  its names are kept. A non-empty `cookies` of any other shape (a raw header string, a list of
  pairs) is dropped: the protocol reads a string as a raw `Cookie` header, which a bare
  `[Filtered]` is not. An absent or empty one is left alone. This was found while reproducing F2
  (2026-11-08) and is not in the round-42 register. juniper-data neither sets nor reads a cookie,
  but a client's cookies reached its events whenever `send_pii` was on.
- **Four more headers are scrubbed: `Proxy-Authorization`, `Sec-WebSocket-Protocol`,
  `X-CSRF-Token` and `X-XSRF-Token`** (owner ruling, 2026-11-08). `Sec-WebSocket-Protocol` carries
  juniper-canopy's WebSocket key (`bearer, <key>`) when its opt-in `ws_auth_enabled` is on. It and
  the two CSRF tokens are on neither of the SDK's own lists, so they reached Sentry in every error
  event and transaction, under either `send_pii` value (measured on sentry-sdk 2.35.0 and 2.74.0).
  sentry-sdk 2.35.0 lets `Proxy-Authorization` through in both modes too; 2.74.0 filters it.
  **Still open, for 0.4.3** (a follow-up, to be designed and validated on its own): query strings,
  including juniper-canopy's `?api_key=` WebSocket parameter, which reaches Sentry under the
  default `send_pii=False`; Sentry Logs (`enable_logs=True` has no `before_send_log`, so neither
  the hook nor the SDK's scrubber sees a log record, and a uvicorn access line carries its query
  string); request bodies; breadcrumbs; exception values; and `headers` sent as a list of pairs,
  which nothing in Juniper emits.
- Pinned in `tests/test_sentry.py`, which holds 75 tests where it held 33: 3 for F6 under Fixed,
  and 40 for the three entries above and for `before_send` itself (6 of the 40 replace one older,
  unparametrized test of `before_send`).
  Both hooks are asserted on the `init` call, for both `send_pii` values at three sample
  rates. The header and cookie handling is unit-tested. `TestNoSensitiveRequestValueReachesTheWire`
  sends one request carrying a secret in the seven headers and two cookies through FastAPI and
  the real SDK into a local transport, for a transaction and for an error event. It runs four
  ways: in the production configuration, under both `send_pii` values; at
  `traces_sample_rate=0.0`, which `configure_sentry` itself is given, for an error event and for
  a transaction that a parent-sampled `sentry-trace` header marks sampled; with the SDK's own
  scrubbing turned off, so that only the hook stands between the secret and the wire; and as a
  control, which turns the hook off too and asserts that the harness sees the secret in every one
  of those headers and cookies.

### Fixed

- **The frame-locals backstop is pinned for library frames** (round-42 finding F6). No test frame
  was marked library code (the unit tests' frames carried no `in_app` key, and the wire tests'
  were `in_app: True`), so a backstop that skipped library frames stayed green. Yet a frame in an
  installed package is library code. juniper-data's image installs juniper-data itself
  (`pip install --no-deps .`), so its own `validate` frame is library code there, and an installed
  juniper-service-core's `validate` serialises as `in_app: False`. (The frame of the
  juniper-canopy#683 leak was canopy's own, which runs from source as application code.) The test
  frames are now marked `in_app: False`, a unit test mixes library, application and unmarked
  frames, and a wire test sends a library frame (via `in_app_exclude`) through the real SDK with
  `include_local_variables` on. Tests only: the hook already stripped every frame.
- **The `sentry` and `test` extras require `sentry-sdk[fastapi]>=2.35.0`, not `>=2.0.0`.**
  `configure_sentry` passes `enable_logs`, which sentry-sdk first accepts in 2.35.0. On every
  earlier release each call raised `TypeError: Unknown option 'enable_logs'`. The tests'
  `EventScrubber(pii_denylist=...)` fails on early 2.x releases too. juniper-data, juniper-cascor
  and juniper-canopy declare `sentry-sdk>=2.0.0` themselves rather than through this extra, so
  this floor does not reach them; their locks pin 2.73.0.
- **Correction to the 0.4.1 entry** (round-42 finding F10). Its sentence "Consumers inherit both on
  upgrade, with no code change" was false. No consumer needed a code change, but juniper-data,
  juniper-cascor and juniper-canopy each pinned `juniper-observability==0.4.0` in their locks.
  None received the fix until its lock was refreshed and the consumer was released again; the
  juniper-data and juniper-cascor CHANGELOGs said so. For this release: an image built from a lock
  gets 0.4.2 with that lock's next refresh, and on 2026-11-08 every consumer lock (juniper-data's,
  juniper-cascor's two, juniper-canopy's and juniper-recurrence's) pins 0.4.1. A fresh install
  gets it at once, since no consumer caps it out, and so does `pip install -U
  juniper-observability`. `pip install -U <consumer>` over an environment that holds 0.4.1 keeps
  0.4.1: no consumer requires more than 0.4.1, and pip's default upgrade strategy
  (`only-if-needed`) upgrades a dependency only when the installed version fails the requirement.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-ml/blob/juniper-observability-v0.4.2/juniper-observability/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md`
