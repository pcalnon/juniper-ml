#!/usr/bin/env python3
"""Round 4 lane F probe: compare fizzy's archiver with origin/main's on the claims r4 L36/L127/L168 make.

Prints only line numbers and REDACTED text: any '@' span or email-shaped text is replaced, and
the pattern bodies are summarised by shape (length/prefix), never printed whole. Read-only; git
runs only in fizzy (read-only `git show`)."""
import re
import subprocess

FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
REL = "util/ad-hoc/2026-09-24_archive_round42_reports.py"
EMAILISH = re.compile(r"[A-Za-z0-9._%+\\-]+(?:@|\\@|\[@\])[A-Za-z0-9.\\-]+")


def redact(s: str) -> str:
    s = EMAILISH.sub("<EMAIL-SHAPED-REDACTED>", s)
    return s


with open(f"{FIZZY}/{REL}", encoding="utf-8") as fh:
    fizzy = fh.read()
main = subprocess.run(["git", "--no-optional-locks", "show", f"origin/main:{REL}"], cwd=FIZZY, capture_output=True, text=True).stdout

for name, src in (("fizzy", fizzy), ("main", main)):
    lines = src.split("\n")
    print(f"===== {name}: {len(lines)} lines")
    for i, ln in enumerate(lines, 1):
        low = ln.lower()
        if any(k in low for k in ("session_ids", "owner-email", "owner_email", "pypi", "agei", "refuse", "credential-shaped", "p.pattern", "patterns =", "def scan", "label")):
            print(f"  {i}: {redact(ln)[:200]}")
    # count MISSING entries
    m = re.search(r"^MISSING\s*[:=].*?^}", src, re.S | re.M)
    if m:
        keys = re.findall(r'^\s*"(a[0-9a-f]{16})"\s*:', m.group(0), re.M)
        print(f"  MISSING keys: {len(keys)}")
    s = re.search(r"^SESSION_IDS\s*=\s*(.*?)$", src, re.M)
    print("  SESSION_IDS line:", s.group(0)[:200] if s else None)
