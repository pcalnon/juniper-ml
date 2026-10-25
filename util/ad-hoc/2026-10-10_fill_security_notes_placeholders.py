#!/usr/bin/env python3
"""Fill the security template's advisory placeholders in a rendered release-notes body.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc — one-off (juniper-data 0.17.1 and juniper-cascor 0.12.0 cuts)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: memory reference_release_train_ceremony_traps_2026-09-09 (2026-10-08 trap 2: the
         ceremony ships the security template's placeholders and has no input to fill them)

Why
---
The ceremony renders a security-bearing release from the security template, leaving
``[PRIORITY_LEVEL]``, ``[SEVERITY]``, ``[VULNERABILITY_CLASS] ([CWE_ID])`` and
``[DEPENDABOT_ALERT_URL]`` in BOTH the Release body and the archived notes, plus a stock
intro paragraph that tells the reader to complete them. This replaces each one, optionally
relabels a MINOR release (the template always says "Security Patch"), and refuses to write if
any placeholder survives. Apply the same output to ``gh release edit --notes-file`` and to the
``release-notes/<pkg>-v<ver>`` archive branch, so the two copies stay identical.

Usage
-----
    2026-10-10_fill_security_notes_placeholders.py --in body.md --out filled.md \
        --priority "High: ..." --severity Medium --vuln-class "... ([CWE-201](...))" \
        --advisory "None. ..." --intro "This is ..." [--minor]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLACEHOLDERS = ("[PRIORITY_LEVEL]", "[SEVERITY]", "[VULNERABILITY_CLASS]", "[CWE_ID]", "[DEPENDABOT_ALERT_URL]")
_STOCK_INTRO = re.compile(r"^This is a security-bearing release of `[^`]+` v[0-9][^ ]*\. It carries a `Security`.*$", re.MULTILINE)


def fill(text: str, args: argparse.Namespace) -> str:
    out = text.replace("**Priority:** [PRIORITY_LEVEL]", f"**Priority:** {args.priority}")
    out = out.replace("## Security Impact ([SEVERITY])", f"## Security Impact ({args.severity})")
    out = out.replace("| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |", f"| **Vulnerability class** | {args.vuln_class} |")
    out = out.replace("| **Advisory** | [DEPENDABOT_ALERT_URL] |", f"| **Advisory** | {args.advisory} |")
    out, n = _STOCK_INTRO.subn(args.intro.replace("\\", r"\\"), out, count=1)
    if n != 1:
        raise SystemExit("the stock intro paragraph was not found exactly once")
    if args.minor:
        out = re.sub(r"(^# .*– :lock: )SECURITY PATCH RELEASE$", r"\1SECURITY RELEASE (MINOR)", out, count=1, flags=re.MULTILINE)
        out = out.replace("**Release Type:** Security Patch", "**Release Type:** MINOR (security-bearing)", 1)
    left = [p for p in PLACEHOLDERS if p in out]
    if left:
        raise SystemExit(f"placeholders survive: {left}")
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--priority", required=True)
    ap.add_argument("--severity", required=True)
    ap.add_argument("--vuln-class", required=True)
    ap.add_argument("--advisory", required=True)
    ap.add_argument("--intro", required=True)
    ap.add_argument("--minor", action="store_true", help="relabel the template's 'Security Patch' as a MINOR release")
    args = ap.parse_args(argv)
    text = Path(args.src).read_text(encoding="utf-8")
    filled = fill(text, args)
    Path(args.out).write_text(filled, encoding="utf-8")
    print(f"wrote {args.out}: {len(filled.splitlines())} lines, no placeholder left")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
