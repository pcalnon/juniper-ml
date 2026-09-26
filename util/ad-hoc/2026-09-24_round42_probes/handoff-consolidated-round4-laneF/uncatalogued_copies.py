#!/usr/bin/env python3
"""Round 4 lane F probe: the handoff copies the reports cite that handoff-frozen/ does not hold.

For document 2 (the follow-up lane's handoff) and document 3 (the common predecessor):
  * sha256 of the durable copies: document 2 at juniper-ml 2e4917c2 (#2097's head, via gh api
    contents -- read-only) and document 3 at origin/main (git show in fizzy -- read-only);
  * sha256 of every file under the session scratchpad whose name suggests a copy of either, and of
    any scratch file whose sha256 starts 62f9b2bf or 4ebd0143 (the two prefixes the reports quote).
Read-only."""
import base64
import hashlib
import json
import os
import subprocess

FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
SCRATCH = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad"
DOC2 = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md"
DOC3 = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md"


def sha(b):
    return hashlib.sha256(b).hexdigest()


p = subprocess.run(["gh", "api", f"repos/pcalnon/juniper-ml/contents/{DOC2}?ref=2e4917c2727fcd57a8cb7885118782a7da1d2eef"], capture_output=True, text=True)
doc2 = base64.b64decode(json.loads(p.stdout)["content"]) if p.returncode == 0 else b""
print("doc2 @2e4917c2 sha256:", sha(doc2)[:16], len(doc2), "bytes")
q = subprocess.run(["git", "--no-optional-locks", "show", f"origin/main:{DOC3}"], cwd=FIZZY, capture_output=True)
print("doc3 @origin/main sha256:", sha(q.stdout)[:16], len(q.stdout), "bytes, rc", q.returncode)

print("\nscratch candidates:")
for root, dirs, files in os.walk(SCRATCH):
    # skip venvs and big trees
    dirs[:] = [d for d in dirs if d not in ("primer-venv", "venv", ".venv", "node_modules", "__pycache__", "site-packages", "lib", "tree", "trees", "head", "main")]
    for f in files:
        if not f.endswith(".md"):
            continue
        full = os.path.join(root, f)
        try:
            with open(full, "rb") as fh:
                b = fh.read()
        except OSError:
            continue
        s = sha(b)
        rel = os.path.relpath(full, SCRATCH)
        if ("doc2" in f or "peer" in f or "doc3" in f or "predecessor" in f or s.startswith(("62f9b2bf", "4ebd0143"))):
            tag = ""
            if b == doc2:
                tag = "== doc2@2e4917c2"
            elif b == q.stdout:
                tag = "== doc3@main"
            print(f"  {rel}  {s[:16]}  {len(b)} bytes {tag}")
