#!/usr/bin/env python3
"""Fill the security template's advisory header in juniper-ml 0.11.5's rendered release notes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-13
Status: ad-hoc -- one-off (the juniper-ml 0.11.5 cut)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-10_fill_security_notes_placeholders.py (the filler this drives);
         util/ad-hoc/2026-11-13_juniper_ml_0_11_5_cut_cochanges.py (the same cut's co-changes);
         notes/releases/RELEASE_NOTES_v0.11.1.md (the last ``[tools]`` security-floor release, whose header this follows);
         notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md (the source of the rating and the class)

Why this exists
---------------
0.11.5's CHANGELOG section has a ``### Security`` category, so the release train renders its notes from the security
template and leaves ``[PRIORITY_LEVEL]``, ``[SEVERITY]``, ``[VULNERABILITY_CLASS] ([CWE_ID])`` and
``[DEPENDABOT_ALERT_URL]`` in both the Release body and the archived notes. The ceremony has no input for them. This
holds the five texts in one place, so the Release body and ``notes/releases/RELEASE_NOTES_v0.11.5.md`` get the same
header, and the texts are on ``main`` beside the release they describe.

Each text was checked on 2026-11-13: the rating, the class and what stays open against juniper-observability 0.4.2's
own notes; the ``[servers]`` and ``[recurrence]`` sentence against PyPI's ``requires_dist`` for juniper-canopy 0.9.0,
juniper-cascor 0.13.0, juniper-data 0.17.1 and juniper-recurrence 0.8.1, the newest release of each (juniper-data's
floors on the two carry ``extra == "api"``, and juniper-recurrence's on juniper-observability
``extra == "observability"``); the consumers' floors against the owner's ruling of
2026-11-09 ("In release PRs"), which the CHANGELOG's Security entry records.

Usage
-----
    python3 util/ad-hoc/2026-11-13_juniper_ml_0_11_5_security_notes_header.py --in body.md --out filled.md

The filler refuses to write while any placeholder survives.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 -- argv form, no shell
import sys
from pathlib import Path

_FILLER = Path(__file__).resolve().parent / "2026-10-10_fill_security_notes_placeholders.py"

PRIORITY = "High: upgrade every environment installed through `juniper-ml[tools]` or `juniper-ml[all]`"
SEVERITY = "Medium"
VULN_CLASS = "Fixed by juniper-observability 0.4.2, which this release floors: sensitive information sent to an external service ([CWE-201](https://cwe.mitre.org/data/definitions/201.html))"
ADVISORY = (
    "None. Internal findings, fixed in juniper-observability 0.4.2, which its own notes rate Medium: round-42 finding F2 (2026-09-24) and the validation of "
    "consolidated-plan item P3-07 (2026-11-08); there is no CVE or Dependabot alert"
)
INTRO = (
    "This is a security-bearing patch release of `juniper-ml` v0.11.5. The meta-package ships no code: its `[tools]` extra now floors "
    "`juniper-observability>=0.4.2`, the security patch that scrubs Sentry transactions, parsed cookies and four more credential headers, and "
    "`juniper-service-core>=0.7.2,<0.8.0`, so upgrading an environment through `juniper-ml[tools]` or `juniper-ml[all]` also upgrades an older release of "
    "either. juniper-observability 0.4.2 is rated Medium in its own notes, and so is this release; juniper-service-core 0.7.2 is a plain patch. 0.4.2 does "
    "not close every path to Sentry: its notes list what stays open for 0.4.3, query strings and Sentry Logs among them. `[servers]` and `[recurrence]` "
    "are unchanged: the newest juniper-canopy, juniper-cascor, juniper-data and juniper-recurrence releases still accept juniper-observability 0.4.1 and "
    "juniper-service-core 0.7.1, and each is to raise its own floors in its next release (owner ruling 2026-11-09)."
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", required=True, help="the rendered notes (the Release body, or the archive file)")
    ap.add_argument("--out", required=True, help="where the filled notes are written")
    args = ap.parse_args()
    command = [sys.executable, str(_FILLER), "--in", args.src, "--out", args.out, "--priority", PRIORITY, "--severity", SEVERITY, "--vuln-class", VULN_CLASS, "--advisory", ADVISORY, "--intro", INTRO]
    return subprocess.run(command, check=False).returncode  # nosec B603


if __name__ == "__main__":
    raise SystemExit(main())
