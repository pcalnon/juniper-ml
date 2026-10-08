# juniper-service-core v0.7.1 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-10-09
**Release Type:** Security Patch
**Priority:** [PRIORITY_LEVEL]
**Package Affected:** juniper-service-core

---

This is a security-bearing release of `juniper-service-core` v0.7.1. It carries a `Security` Keep-a-Changelog category and was drafted by the release-train from the security template; complete the advisory details (CWE, advisory URL, affected versions) before the ceremony.

---

## Security Impact ([SEVERITY])

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-service-core` |
| **Fixed in** | 0.7.1 |
| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |
| **Advisory** | [DEPENDABOT_ALERT_URL] |

---

## Changes in v0.7.1

### Fixed

- **`APIKeyAuth.validate` no longer short-circuits its walk over the configured keys**
  (`APD-CASCOR-005`). It accumulated into `any(hmac.compare_digest(api_key, k) for k in
  self._api_keys)`, which stops at the first match, so the NUMBER of comparisons performed
  depended on where the matching key fell in the iteration. `compare_digest` already makes each
  individual comparison constant-time in the key's *content*; the iteration is the part that was
  not. Now mirrors juniper-data's reference implementation
  (`juniper_data/api/security.py`), which has never short-circuited.

  **Scope, stated honestly:** this is defence-in-depth and a convergence of four near-identical
  copies, not the repair of a live vulnerability. What `any()` leaked is the *position* of the
  matching key within the iteration, not the key; and `self._api_keys` is a `set` here, whose
  iteration order is hash-derived rather than configuration order. The reason to do it is that
  divergence between forked copies of security code is the shape that has produced five separate
  register findings (register §2.3, "Copy drift").

  **No behavioural test pins this, and none can:** the two forms return the same value for every
  input. The guard is therefore a source marker in juniper-ml's
  `tests/test_service_fork_drift.py` (`nonshortcircuit-key-compare`), which was verified to FAIL
  against the unported forks before being committed.

### Security

- **A non-ASCII `X-API-Key` is a 401, not a 500 that hands Sentry the real key.**
  `APIKeyAuth.validate` compared `str` with `hmac.compare_digest`, which raises `TypeError` when
  either side holds a non-ASCII character. Starlette decodes header bytes as latin-1, so any byte
  above 0x7f reaches `validate` as one. The validation of juniper-canopy#683 (2026-09-24) sent an
  anonymous `X-API-Key: \xa0`, which both uvicorn parsers pass. It had three consequences:
  - The `TypeError` escaped `SecurityMiddleware`'s `except HTTPException`, so the caller got a
    **500** instead of a 401.
  - Only a 401 records a failure, so a flood of such keys was **never throttled** by
    `FailedAuthThrottle`.
  - Under Sentry's default `include_local_variables=True`, the error event carried the loop's
    `candidate`, the **real configured key**.

  The `/ws/*` handshake calls the same `validate` from `ws_authenticate`, and raised the same way.
  Both sides are now compared as UTF-8 bytes. The encoding uses `surrogatepass`, the one built-in
  error handler that is both total and injective: a lone surrogate (from a JSON-decoded config
  value, say) encodes instead of raising, and no two distinct strings share bytes. So `validate`
  matches exactly when the strings are equal. `surrogateescape` fails on both counts: it raises on
  `"\ud800"`, and it maps `"\xe9"` and `"\udcc3\udca9"` to the same bytes. The
  `blank-api-key-filter` and `nonshortcircuit-key-compare` drift-gate markers are unchanged. Owner
  ruling "Fix everywhere now" (2026-09-24). juniper-observability stops Sentry capturing locals in
  the same change, and juniper-data and juniper-cascor carry the same compare in their forks.
  Pinned by 64 new tests: `tests/test_security.py` covers the non-ASCII mismatch and a 7x7
  equality matrix built to separate the candidate encodings; `tests/test_middleware.py` checks a
  raw-byte header is a 401 and is counted by the throttle; `tests/test_t2_websocket.py` checks the
  handshake closes 4001. Reverting to the `str` compare fails 63 of them: the HTTP tests with
  `assert 500 == 401`, the rest with the `TypeError`. `surrogateescape` fails 15 and strict UTF-8
  fails 33 (juniper-ml's `util/ad-hoc/2026-09-24_bytes_compare_sentry_locals_verify.py`).
- **`FailedAuthThrottle.check()` no longer grows its table by one entry per client address.**
  `check()` runs on every request, before authentication, and is documented as a read-only probe.
  But `_failures` was a `defaultdict`, so reading an unseen source IP inserted it. Pruning,
  including the 10,000-entry `_MAX_ENTRIES` cap, runs only from `record_failure()`. Under open auth
  or valid-key traffic nothing ever calls that, so the table grew without bound: one entry per
  distinct client, never removed. That is the memory denial of service the class's own cleanup
  exists to prevent. `_failures` is now a plain `dict`, and both reads use `.get(client_ip, (0, 0.0))`;
  behaviour is otherwise unchanged. Found by the 2026-10-08 Cursor flood-3 evaluation
  (`notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4). The juniper-data
  and juniper-cascor forks carry the same fix in their own repos, each pinned by its own test.
  Pinned here by `test_failed_auth_throttle_check_does_not_track_unseen_ips`: 1,000 unseen
  addresses leave the table empty. Against the previous code it fails at
  `assert len(throttle._failures) == 0`.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-ml/blob/juniper-service-core-v0.7.1/juniper-service-core/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-service-core_v0.7.1.md`
