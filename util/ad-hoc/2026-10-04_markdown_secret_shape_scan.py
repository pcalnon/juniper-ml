#!/usr/bin/env python3
"""
Coarse secret-SHAPE scan over markdown files — a quick tripwire, NOT a secret screen.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-04
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (XC-PRESERVE, XC-LEAKS)

It matches a handful of token shapes (GitHub, PyPI, Hugging Face, AWS, private-key headers, JWTs, Slack hooks, age
secret keys, 64-hex strings, quoted secret assignments, email addresses) and prints only a 6-character prefix and the
length of each hit. A clean result proves little: it does not know the Duplicati passphrase / settings-key classes
(B9) or anything a real scanner's default rules cover. Use the default-rules mode of
``util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py --scan-dir`` before publishing anything.

Usage
-----
    python3 util/ad-hoc/2026-10-04_markdown_secret_shape_scan.py DIR_OR_FILE...
"""
import re
import sys
from pathlib import Path

PATTERNS = {
    "github_token": r"\b(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})",
    "pypi_token": r"\bpypi-[A-Za-z0-9_\-]{40,}",
    "hf_token": r"\bhf_[A-Za-z0-9]{30,}",
    "aws_key": r"\bAKIA[0-9A-Z]{16}\b",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "jwt": r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",
    "slack_hook": r"hooks\.slack\.com/services/[A-Za-z0-9/]+",
    "age_secret": r"AGE-SECRET-KEY-1[0-9A-Z]{50,}",
    "long_hex_64": r"\b[0-9a-f]{64}\b",
    "assign_secret": r"(?i)(password|passphrase|secret|api_key|token)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]",
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
}


def files(args):
    for a in args:
        p = Path(a)
        yield from (sorted(p.rglob("*.md")) if p.is_dir() else [p])


def main() -> int:
    hits = 0
    for p in files(sys.argv[1:]):
        for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            for name, pat in PATTERNS.items():
                for m in re.finditer(pat, line):
                    hits += 1
                    s = m.group(0)
                    print(f"{p}:{n}: {name}: {s[:6]}…({len(s)} chars)")
    print("hits", hits)
    return 0 if hits == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
