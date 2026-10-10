# juniper-observability v0.4.1 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-10-09
**Release Type:** Security Patch
**Priority:** High: upgrade every service that calls `configure_sentry`
**Package Affected:** juniper-observability

---

This is a security-bearing release of `juniper-observability` v0.4.1. `configure_sentry` no longer sends frame-local variables to Sentry. Under the SDK default, an error event carried the local variables of every frame, and in the juniper-canopy#683 validation that included the real configured API key. The vector needs Sentry to be configured and an exception raised in a frame that holds a secret; the data goes to the operator's own Sentry project, so this is rated Medium. Fixes for the X-Request-ID, `py.typed`, typing and `__all__` issues ship in the same release.

---

## Security Impact (Medium)

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-observability` |
| **Fixed in** | 0.4.1 |
| **Vulnerability class** | Sensitive information sent to an external service ([CWE-201](https://cwe.mitre.org/data/definitions/201.html)) |
| **Advisory** | None. Internal finding from the validation of juniper-canopy#683 (2026-09-24); there is no CVE or Dependabot alert |

---

## Changes in v0.4.1

### Fixed

- **Inbound `X-Request-ID` is validated before propagation** (defect-register `APD-OBS-001`,
  [ml#1156](https://github.com/pcalnon/juniper-ml/pull/1156)). The header is attacker-controlled and
  its value flows into a process-wide `ContextVar` that any consumer may write to a line-oriented
  sink, and that is echoed back on the response. That was contained only *incidentally*, by machinery
  this package does not own: h11 caps the whole request head at `max_incomplete_event_size` (16384 by
  default, and uvicorn leaves it alone) and rejects CR/LF in header values outright. Both are h11
  defaults, so the guarantee was borrowed rather than held. Ingress validation moves it here: a new
  `MAX_REQUEST_ID_LENGTH` (128 — generous beside a 36-character UUID4 or a 55-character W3C
  `traceparent`, small enough not to bloat a log line) and an **allowlist** pattern
  `[A-Za-z0-9._:-]+`, chosen over a denylist because the set of characters safe in *every* downstream
  sink is far easier to enumerate correctly than the set dangerous in any of them. An invalid inbound
  value is replaced with a freshly generated ID rather than rejected.
- **`register_info_or_update` declares its real return type** (defect-register `APD-OBS-003`,
  [ml#1245](https://github.com/pcalnon/juniper-ml/pull/1245)). It returned `Any`, which silently
  laundered the type for every caller. It now returns `Info`, imported under `TYPE_CHECKING` only —
  `prometheus_client` is an optional extra and must never be imported at runtime here, and
  `from __future__ import annotations` makes the annotation a string, so the import costs nothing
  outside a type checker.
- **`__all__` is pinned against the module's actual public surface** (defect-register `APD-OBS-004`,
  [ml#1245](https://github.com/pcalnon/juniper-ml/pull/1245)). A guard test now fails when the two
  disagree, so an export can no longer be added or removed without the advertised surface following.
- **The `py.typed` marker is actually shipped in the wheel** (defect-register `APD-OBS-002`,
  [ml#1237](https://github.com/pcalnon/juniper-ml/pull/1237)). The package carried the
  `Typing :: Typed` classifier while the marker was not included as package data, so every consumer's
  type checker silently treated this package as untyped. Part of the six-sub-package packaging sweep.

> These four entries are a **backfill**: the changes shipped between 0.4.0 and this release with an
> empty `[Unreleased]` section, which is what the release-train detector reported as
> "CHANGELOG [Unreleased] has no feature/fix/security bullets (under-documented)". All four are
> fixes; none adds package-level public API — `is_valid_request_id` and `MAX_REQUEST_ID_LENGTH` are
> module-level and are not exported from `juniper_observability.__init__`. The bump this documents is
> therefore a **patch**, which is what `detect.py --local-git` proposes for this package.

### Security

- **`configure_sentry` no longer sends frame-local variables to Sentry.** It now passes
  `include_local_variables=False` to `sentry_sdk.init`. The SDK default is `True`, which snapshots
  every frame's locals into each error event. The validation of juniper-canopy#683 (2026-09-24)
  showed what that costs. An anonymous request with `X-API-Key: \xa0` made `hmac.compare_digest`
  raise `TypeError` inside `APIKeyAuth.validate`, and the error event carried the comparison
  loop's local `candidate`: the **real configured key**. The SDK's own `EventScrubber` did not
  catch it, because it redacts locals by name. `api_key`, the presented key, is on its default
  denylist; `candidate` is not. No name list can be complete, so no locals are captured at all, and
  there is deliberately no parameter to turn them back on. Owner ruling "Fix everywhere now"
  (2026-09-24).
- **The `before_send` hook also deletes frame `vars`**, as defence in depth. It covers every
  `exception.values[*].stacktrace`, every `threads.values[*].stacktrace` and the top-level
  `stacktrace`. The option covers the SDK's own capture paths but not the opt-in
  `PureEvalIntegration`, whose event processor writes frame `vars` without consulting it
  (sentry-sdk 2.58.0), and event processors run before `before_send`. The hook keeps its name,
  `_strip_sensitive_headers`, because juniper-data and juniper-cascor import it by that name.
- **Consumers inherit both on upgrade, with no code change.** juniper-data, juniper-canopy and
  juniper-cascor's service path all delegate to `configure_sentry`. Pinned in `tests/test_sentry.py`
  (18 new tests): the keyword is asserted, the hook is tested at every frame location, and
  `TestNoSecretLocalReachesTheWire` drives the real SDK into a local transport. There, a frame that
  dies holding the key as `candidate` puts no byte of it on the wire, through `capture_exception`
  and through the logging path uvicorn uses, with each layer disabled in turn. A control asserts
  that the harness does see the leak when both layers are off. Each of the five mutations in
  juniper-ml's `util/ad-hoc/2026-09-24_bytes_compare_sentry_locals_verify.py` fails the suite.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-ml/blob/juniper-observability-v0.4.1/juniper-observability/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.1.md`
