#!/usr/bin/env python3
"""Lane A: which ci.yml job and step contain a given line, and what conditions/triggers govern them.

Parses ci.yml with PyYAML if available for job-level `if:`/`needs:`; locates the job by indentation scan.
usage: a24_ci_job_of_line.py <ci.yml> <line>
"""
import re
import sys

path, target = sys.argv[1], int(sys.argv[2])
lines = open(path, encoding="utf-8").read().split("\n")
job = step = None
job_line = step_line = None
in_jobs = False
for i, ln in enumerate(lines[:target], 1):
    if re.match(r"^jobs:\s*$", ln):
        in_jobs = True
    if in_jobs and re.match(r"^  [A-Za-z0-9_-]+:\s*$", ln):
        job, job_line = ln.strip()[:-1], i
        step = None
    m = re.match(r"^      - name:\s*(.*)$", ln)
    if m:
        step, step_line = m.group(1), i
print(f"line {target}: job '{job}' (L{job_line}), step '{step}' (L{step_line})")
# job header block up to its steps:
for ln in lines[job_line - 1 : job_line + 25]:
    if re.match(r"^    (if|needs|name|runs-on|timeout-minutes):", ln):
        print("  job", ln.strip()[:160])
# step-level if:
for ln in lines[step_line - 1 : target]:
    if re.match(r"^        if:", ln):
        print("  step", ln.strip()[:160])
# triggers
start = next(i for i, ln in enumerate(lines) if re.match(r"^on:", ln))
end = next(i for i, ln in enumerate(lines[start + 1 :], start + 1) if re.match(r"^[a-z]", ln))
print("  triggers:", " | ".join(x.strip() for x in lines[start:end] if x.strip() and not x.strip().startswith("#"))[:400])
