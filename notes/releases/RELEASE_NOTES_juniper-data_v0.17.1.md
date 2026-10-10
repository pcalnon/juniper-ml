# juniper-data v0.17.1 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-10-10
**Release Type:** Security Patch
**Priority:** [PRIORITY_LEVEL]
**Package Affected:** juniper-data

---

This is a security-bearing release of `juniper-data` v0.17.1. It carries a `Security` Keep-a-Changelog category and was drafted by the release-train from the security template; complete the advisory details (CWE, advisory URL, affected versions) before the ceremony.

---

## Security Impact ([SEVERITY])

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-data` |
| **Fixed in** | 0.17.1 |
| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |
| **Advisory** | [DEPENDABOT_ALERT_URL] |

---

## Changes in v0.17.1

### Security

- **The wheel's floors follow the lock**: `juniper-observability>=0.4.1` and
  `juniper-service-core>=0.7.1,<0.8.0`, so a pip install of 0.17.1 over an older environment
  upgrades both. They ride in this release PR because a PR that touches `pyproject.toml` on any
  other branch triggers `lockfile-update.yml`, which regenerates the whole lock with `--upgrade`.
- **The image picks up the two shared security patches**: `requirements.lock` moves
  `juniper-observability` 0.4.0 -> 0.4.1 and `juniper-service-core` 0.7.0 -> 0.7.1, and nothing
  else. The 0.17.0 image installs that lock (`Dockerfile:33`), so it shipped observability 0.4.0,
  whose `configure_sentry` still sends frame-local variables to Sentry. `api/app.py` calls it, and
  a frame local could hold the real API key. 0.4.1 passes `include_local_variables=False`.
  service-core 0.7.1 fixes `APIKeyAuth` and `FailedAuthThrottle`; juniper-data's own copies in
  `api/security.py` already carried both fixes in 0.17.0 (#440, #476), so that pin is consistency
  with the sibling services. The lock was regenerated with `--upgrade-package` for the two packages
  only (69 pins; the freshness gate's constraint-mode resolution reproduces them).

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-data/blob/v0.17.1/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-data_v0.17.1.md`
