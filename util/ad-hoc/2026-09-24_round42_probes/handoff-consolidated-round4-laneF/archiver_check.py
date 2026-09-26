#!/usr/bin/env python3
"""Round 4 lane F probe: run the archiver's --check (writes nothing) twice and count its lines:
  1. fizzy's copy, in fizzy (r4 L168 "53 in fizzy at 03:05Z");
  2. origin/main's copy, in a scratch root built with `git archive origin/main` (r4 L168 "34 in a
     worktree at origin/main").
Never prints a REFUSE line's pattern text (main's copy would print the owner's address): only the
report name before the colon. The scratch root is under this lane's scratch directory."""
import collections
import os
import shutil
import subprocess
import sys

FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
REL = "util/ad-hoc/2026-09-24_archive_round42_reports.py"
SCR = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/hc4/laneF/mainroot"


def summarise(label, proc):
    out = proc.stdout + proc.stderr
    c = collections.Counter()
    names = collections.defaultdict(list)
    for ln in out.split("\n"):
        s = ln.strip()
        if not s:
            continue
        word = s.split()[0]
        if word in ("OK", "DIFFER", "skip", "REFUSE", "exists", "add", "would"):
            key = "would add" if word == "would" else word
            c[key] += 1
            nm = s.split()[1 if key != "would add" else 2].rstrip(":")
            names[key].append(nm)
        elif "Traceback" in s:
            c["Traceback"] += 1
        elif s.startswith("session "):
            c["session-exit"] += 1
            names["session-exit"].append(s[:120])
        elif "no assistant message" in s:
            c["no-assistant"] += 1
    print(f"== {label}: exit {proc.returncode}; counts {dict(c)}")
    for k in ("DIFFER", "REFUSE", "would add", "skip", "exists", "session-exit"):
        if names.get(k):
            print(f"   {k}: {names[k]}")
    return c


p1 = subprocess.run([sys.executable, f"{FIZZY}/{REL}", "--check"], cwd=FIZZY, capture_output=True, text=True)
summarise("fizzy copy", p1)

if os.path.exists(SCR):
    shutil.rmtree(SCR)
os.makedirs(SCR)
arch = subprocess.run(["git", "--no-optional-locks", "archive", "origin/main", "reports/2026-09-24_defect-register-round-42", REL], cwd=FIZZY, capture_output=True)
tar = subprocess.run(["tar", "-x", "-C", SCR], input=arch.stdout, capture_output=True)
print("archive rc", arch.returncode, "tar rc", tar.returncode)
p2 = subprocess.run([sys.executable, f"{SCR}/{REL}", "--check"], cwd=SCR, capture_output=True, text=True)
summarise("origin/main copy (scratch root)", p2)
n_reports = len([f for f in os.listdir(f"{SCR}/reports/2026-09-24_defect-register-round-42") if f.endswith(".md")])
print("origin/main reports dir .md files:", n_reports)
shutil.rmtree(SCR)
print("scratch root removed")
