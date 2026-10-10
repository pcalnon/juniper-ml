# juniper-data v0.17.1 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-10-10
**Release Type:** Security Patch
**Priority:** High: upgrade every juniper-data deployment that reports to Sentry
**Package Affected:** juniper-data

---

This is a security patch release of `juniper-data` v0.17.1. Its image now runs `juniper-observability` 0.4.1, whose `configure_sentry` no longer sends frame-local variables to Sentry. The 0.17.0 image installed 0.4.0, so an error raised in a frame that held the real configured API key could carry the key to Sentry; `api/app.py` calls `configure_sentry`, and the vector needs Sentry to be configured. The image lock also moves `juniper-service-core` to 0.7.1, and the wheel's floors rise to `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1,<0.8.0`. No application code changed beyond the version string.

---

## Security Impact (Medium)

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-data` |
| **Fixed in** | 0.17.1 |
| **Vulnerability class** | Sensitive information sent to an external service ([CWE-201](https://cwe.mitre.org/data/definitions/201.html)) |
| **Advisory** | None. Internal finding from the validation of juniper-canopy#683 (2026-09-24), fixed in juniper-observability 0.4.1 and delivered to this image here; there is no CVE or Dependabot alert |

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
