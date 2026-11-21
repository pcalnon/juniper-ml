#!/usr/bin/env python3
"""Triage, by shape only, every random-looking token in transcript-derived text: the --all half of the pre-push gate.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the masked read of reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/ before plan v1.15.16's push)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-10-05_masked_finding_shape.py (whose random_looking() and regexes this uses);
         util/ad-hoc/2026-11-15_pre_push_gate_run.bash (the two scans and the --names read)

A token that is part of a repository path (this checkout's tracked files, read from ``tmp/plan-pr/tracked.txt``; the
sibling repositories' trees at ``main``; the files under the predecessor worktrees' ``tmp/``) is a file name, and a
40-hex token, optionally ``REPO=``-prefixed, is a commit sha. Anything else is printed by shape (lengths and character
classes), never by value, for a reader to classify.

Usage: python3 -I util/ad-hoc/2026-11-15_masked_read_random_token_triage.py DIR   (from the checkout; needs gh; writes nothing)
"""

import importlib.util
import pathlib
import sys

spec = importlib.util.spec_from_file_location("m", "util/ad-hoc/2026-10-05_masked_finding_shape.py")
m = importlib.util.module_from_spec(spec)
sys.modules["m"] = m
spec.loader.exec_module(m)
import json
import re
import subprocess

corpus = pathlib.Path("tmp/plan-pr/tracked.txt").read_text(encoding="utf-8")
# the sibling repos' file trees at main, so a path in another repository also counts as a file name
for repo in ("juniper-cascor", "juniper-canopy", "juniper-data", "juniper-deploy", "juniper-recurrence"):
    out = subprocess.run(["gh", "api", f"repos/pcalnon/{repo}/" + "git" + "/trees/main?recursive=1"], capture_output=True, text=True, check=True).stdout
    corpus += "\n" + "\n".join(f"{repo}/{e['path']}" for e in json.loads(out)["tree"])
# gitignored working files the briefs name: every file under the predecessor worktrees' tmp/ dirs
for worktree in (pathlib.Path.cwd().parents[2] / ".claude" / "worktrees").iterdir():
    scratch = worktree / "tmp"
    if scratch.is_dir():
        corpus += "\n" + "\n".join(str(p) for p in scratch.rglob("*") if p.is_file())
HEX40 = re.compile(r"^(?:[a-z-]+=)?[0-9a-f]{40}$")
shas = 0
total = flagged = unexplained = 0
for f in sorted(pathlib.Path(sys.argv[1]).glob("*.md")):
    for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        total += 1
        for t in m.LONG_RUN_RE.findall(line):
            if not m.random_looking(t):
                continue
            flagged += 1
            if t in corpus:
                continue
            if HEX40.match(t):
                shas += 1
                continue
            unexplained += 1
            print(
                f"{f.name}:{n} len={len(t)} upper={sum(c.isupper() for c in t)} lower={sum(c.islower() for c in t)} "
                f"digits={sum(c.isdigit() for c in t)} seps={sum(c in '+/=_-' for c in t)} "
                f"hex={bool(m.HEX_RE.search(t))} uuid={bool(m.UUID_RE.search(t))}"
            )
print(f"lines read {total}; random-looking tokens {flagged}; part of a path {flagged - unexplained - shas}; 40-hex (a commit sha, optionally REPO=) {shas}; other {unexplained}")
