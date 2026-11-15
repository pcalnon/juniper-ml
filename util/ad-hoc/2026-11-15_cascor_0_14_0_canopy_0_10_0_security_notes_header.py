#!/usr/bin/env python3
"""Fill the security template's advisory header in the juniper-cascor 0.14.0 and juniper-canopy 0.10.0 release notes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the juniper-cascor 0.14.0 and juniper-canopy 0.10.0 cuts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-10_fill_security_notes_placeholders.py (the filler this drives);
         util/ad-hoc/2026-11-13_juniper_ml_0_11_5_security_notes_header.py (the pattern: the same patch, floored by the meta-package);
         util/ad-hoc/2026-11-14_cascor_canopy_release_cochanges.py (the same cuts' co-changes);
         notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md (the source of the rating and the class)

Why this exists
---------------
Each release's CHANGELOG section has a ``### Security`` category, so the release train renders its notes from the
security template and leaves ``[PRIORITY_LEVEL]``, ``[SEVERITY]``, ``[VULNERABILITY_CLASS] ([CWE_ID])`` and
``[DEPENDABOT_ALERT_URL]`` in both the Release body and the archived notes, labelled "Security Patch" although both
are minor releases. The ceremony has no input for them. This holds the texts in one place, so each Release body and
its ``notes/releases/RELEASE_NOTES_<pkg>_v<version>.md`` get the same header, and the texts are on juniper-ml's
``main`` beside the archives they fill.

Each text was checked on 2026-11-15 against the release's own CHANGELOG section at its proposal head (juniper-cascor
``668f88e9``, juniper-canopy ``1c2dbd01``), and corrected after an independent outside-reader review of the rendered bodies: the exposure under juniper-observability 0.4.1 against each Security
entry, the rating and the class against 0.4.2's notes, what stays open against those notes and canopy's own entry.

Usage
-----
    python3 util/ad-hoc/2026-11-15_cascor_0_14_0_canopy_0_10_0_security_notes_header.py --package juniper-cascor --in body.md --out filled.md

The filler refuses to write while any placeholder survives.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 -- argv form, no shell
import sys
from pathlib import Path

_FILLER = Path(__file__).resolve().parent / "2026-10-10_fill_security_notes_placeholders.py"

SEVERITY = "Medium"
VULN_CLASS = "Fixed by juniper-observability 0.4.2, which this release floors and its image locks: sensitive information sent to an external service ([CWE-201](https://cwe.mitre.org/data/definitions/201.html))"
ADVISORY = (
    "None. Internal findings, fixed in juniper-observability 0.4.2, which its own notes rate Medium: round-42 finding F2 (2026-09-24) and the validation of "
    "consolidated-plan item P3-07 (2026-11-08); there is no CVE or Dependabot alert"
)

TEXTS = {
    "juniper-cascor": {
        "priority": "High: upgrade every juniper-cascor deployment that reports to Sentry (`JUNIPER_CASCOR_SENTRY_DSN` set)",
        "intro": (
            "This is a security-bearing minor release of `juniper-cascor` v0.14.0. Its image locks `juniper-observability` 0.4.2, and its wheel now "
            "floors `juniper-observability>=0.4.2`, whose `configure_sentry` scrubs transactions as well as error events and filters four more credential "
            "headers. Under 0.4.1, once `JUNIPER_CASCOR_SENTRY_DSN` was set, a request's `Sec-WebSocket-Protocol`, `X-CSRF-Token` and `X-XSRF-Token` "
            "headers reached Sentry in every error event and transaction. cascor reads no credential from any of the three (it authenticates REST and "
            "WebSocket callers by `X-API-Key` alone), so they carried a secret only when a client put one there. cascor leaves `send_pii` off, so the "
            "`X-API-Key` and cookie leaks that 0.4.2 "
            "also closes were not reachable here. It also floors `juniper-service-core>=0.7.2,<0.8.0`, a plain patch. 0.4.2 does not close every path "
            "to Sentry: its notes list what stays open for 0.4.3, query strings and Sentry Logs among them. The release also fixes a 429 that said "
            "`Retry-After: 0` (APD-ECO-016), a lifecycle that wedged in `PAUSED`, a WebSocket resume that missed broadcasts, and a start that cancelled "
            "the stop before it; it adds a keyword and a `bool` return to `WebSocketManager.promote_to_active`."
        ),
    },
    "juniper-canopy": {
        "priority": "High: upgrade every juniper-canopy deployment that reports to Sentry, first any with `ws_auth_enabled` on",
        "intro": (
            "This is a security-bearing minor release of `juniper-canopy` v0.10.0. Its image locks `juniper-observability` 0.4.2, and its wheel now "
            "floors `juniper-observability>=0.4.2,<0.5.0`, whose `configure_sentry` scrubs transactions as well as error events and filters four more "
            "credential headers. Under 0.4.1, once a Sentry DSN was set, a request's `Sec-WebSocket-Protocol`, `X-CSRF-Token` and `X-XSRF-Token` "
            "headers reached Sentry in every error event and transaction, and `Sec-WebSocket-Protocol` carries canopy's own WebSocket key "
            "(`bearer, <key>`) when the opt-in `ws_auth_enabled` is on. canopy leaves `send_pii` off, so the `X-API-Key` and cookie leaks that 0.4.2 "
            "also closes were not reachable here. It also floors `juniper-service-core>=0.7.2,<0.8.0`, a plain patch. 0.4.2 does not close every path "
            "to Sentry: its notes leave query strings, Sentry Logs, request bodies, breadcrumbs and exception values for 0.4.3. For canopy the first "
            "includes the `?api_key=` WebSocket query parameter, which reaches Sentry under the default `send_pii=False`. The second Security entry makes CI's Gitleaks step load gitleaks' built-in ruleset; it had loaded none and could not "
            "fail. The release also fixes F-CANOPY-069 (under every dash 3.x the dashboard was inert; the fix works on dash 3 too) and raises the "
            "runtime floor to `dash>=4.0.0`, the line canopy tests, so an environment still on dash 3 moves to dash 4 with it."
        ),
    },
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package", required=True, choices=sorted(TEXTS))
    ap.add_argument("--in", dest="src", required=True, help="the rendered notes (the Release body, or the archive file)")
    ap.add_argument("--out", required=True, help="where the filled notes are written")
    args = ap.parse_args()
    t = TEXTS[args.package]
    command = [sys.executable, str(_FILLER), "--in", args.src, "--out", args.out, "--priority", t["priority"], "--severity", SEVERITY, "--vuln-class", VULN_CLASS, "--advisory", ADVISORY, "--intro", t["intro"], "--minor"]
    return subprocess.run(command, check=False).returncode  # nosec B603


if __name__ == "__main__":
    sys.exit(main())
