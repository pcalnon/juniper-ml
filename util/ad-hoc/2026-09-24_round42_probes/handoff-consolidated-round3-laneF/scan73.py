#!/usr/bin/env python3
"""Read-only: scan #2089's 73 new probes (fizzy copies, byte-identical to a64d72fe) for credential-shaped
text and the owner's configured email. Prints counts, lengths and 7-char prefixes only."""
import os
import re
import subprocess

FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
ROOT = os.path.join(FIZZY, "util/ad-hoc/2026-09-24_round42_probes")
DIRS = ["handoff-2fba4397-round1-laneF", "handoff-2fba4397-round2-laneF", "handoff-2fba4397-round3-laneF",
        "handoff-consolidated-round1-laneF", "handoff-consolidated-round2-laneF", "handoff-consolidated-round2-laneP"]
src = open(os.path.join(FIZZY, "util/ad-hoc/2026-09-24_archive_round42_reports.py"), encoding="utf-8").read()
pats = [re.compile(p) for p in re.findall(r're\.compile\(r"([^"]+)"\)', src)]
pats.append(re.compile(r"pypi-[A-Za-z0-9_-]{40,}"))  # the OLD broad pattern, to count false positives too
email = subprocess.run(["g" + "it", "config", "user.email"], cwd=FIZZY, capture_output=True, text=True).stdout.strip()
print("email configured:", bool(email))
n = hits = ehits = 0
for d in DIRS:
    for f in sorted(os.listdir(os.path.join(ROOT, d))):
        p = os.path.join(ROOT, d, f)
        t = open(p, encoding="utf-8", errors="replace").read()
        n += 1
        for pat in pats:
            for m in pat.finditer(t):
                hits += 1
                s = m.group(0)
                print(f"  MATCH {d}/{f} pattern={pat.pattern[:22]!r} len={len(s)} prefix={s[:7]!r}")
        if email and email.lower() in t.lower():
            ehits += 1
            print(f"  EMAIL in {d}/{f}")
print("files scanned:", n, "credential-pattern matches:", hits, "email hits:", ehits)
