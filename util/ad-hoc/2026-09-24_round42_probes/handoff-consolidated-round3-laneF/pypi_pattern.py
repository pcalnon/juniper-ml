#!/usr/bin/env python3
"""Read-only: does the archiver's narrowed PyPI pattern still catch token-SHAPED strings?

Builds SYNTHETIC token-shaped strings (random bytes after the real macaroon-v2 prefix bytes); no real
credential is read or printed. Prints only booleans, lengths and 7-char prefixes.
"""
import base64
import importlib.util
import os
import re
import sys

FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
path = os.path.join(FIZZY, "util/ad-hoc/2026-09-24_archive_round42_reports.py")
src = open(path, encoding="utf-8").read()
pats = re.findall(r're\.compile\(r"([^"]+)"\)', src)
pypi_pats = [p for p in pats if "pypi" in p or "AgEI" in p]
print("archiver pypi-related patterns:", pypi_pats)
new = re.compile(r"pypi-Ag[A-Za-z0-9_-]{40,}")
old = re.compile(r"pypi-[A-Za-z0-9_-]{40,}")
assert r"pypi-Ag[A-Za-z0-9_-]{40,}" in pypi_pats


def b64(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


rnd = os.urandom(150)
samples = {
    "pypi.org v2 macaroon": "pypi-" + b64(b"\x02\x01\x08pypi.org\x02\x01" + rnd),
    "test.pypi.org v2 macaroon": "pypi-" + b64(b"\x02\x01\x0dtest.pypi.org\x02\x01" + rnd),
    "v1 macaroon (hypothetical)": "pypi-" + b64(b"\x00\x0flocation pypi.org\n" + rnd),
    "token in a URL-ish context": "password=pypi-" + b64(b"\x02\x01\x08pypi.org\x02\x01" + rnd) + "&x=1",
    "the #2100 handoff filename": "HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md",
}
for name, s in samples.items():
    m_new = bool(new.search(s))
    m_old = bool(old.search(s))
    tokpart = s[s.find("pypi-"):] if "pypi-" in s else s
    print(f"{name:32s} len={len(tokpart):4d} prefix={tokpart[:7]!r:10s} old={m_old} new={m_new}")

# All archiver patterns combined, as the archiver applies them
allp = [re.compile(p) for p in pats]
fn = samples["the #2100 handoff filename"]
print("any archiver pattern matches the #2100 filename:", any(p.search(fn) for p in allp))
