# Pull Request: Security Hardening — Build Attestations, Scanning, and Audit Documentation

**Date:** 2026-03-03
**Version(s):** 0.2.0 → 0.2.1
**Author:** Paul Calnon
**Status:** READY_FOR_MERGE

---

## Summary

Supply chain security and documentation for juniper-ml: enables build attestations, adds scheduled security scanning, and includes the cross-ecosystem security audit plan documenting all 24 findings across 7 repositories.

---

## Changes

### Security

- Enabled build attestations in publish workflow

### Added

- `.github/workflows/security-scan.yml` — Weekly Bandit and pip-audit scanning
- `notes/SECURITY_AUDIT_PLAN.md` — Complete security audit documentation

---

## Impact & SemVer

- **SemVer impact:** PATCH (0.2.0 → 0.2.1)
- **Breaking changes:** NO
- **Security/privacy impact:** MEDIUM — Supply chain verification; audit documentation

---

## Files Changed

- `.github/workflows/publish.yml` — Enabled build attestations
- `.github/workflows/security-scan.yml` — New scanning workflow
- `notes/SECURITY_AUDIT_PLAN.md` — Security audit plan (334 lines)

---

## Related Issues / Tickets

- Phase Documentation: `notes/SECURITY_AUDIT_PLAN.md` (this repo)
