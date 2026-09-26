#!/usr/bin/env python3
"""Round 4 lane F probe: are hazy's two differing probe files the pre-redaction copies
that #2081's commits 73dc109c and f9964d78 replaced? Read-only gh GETs; hazy read with open()."""
import hashlib
import json
import subprocess

HAZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map/"


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode != 0:
        return {"__error__": p.stderr.strip()[:300]}
    return json.loads(p.stdout)


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


for sha in ("73dc109c", "f9964d78"):
    c = gh("api", f"repos/pcalnon/juniper-ml/commits/{sha}")
    if "__error__" in c:
        print(sha, c)
        continue
    parent = c["parents"][0]["sha"]
    print("==", sha, c["sha"][:8], "parent", parent[:8], "verified", c["commit"]["verification"]["verified"], "|", c["commit"]["message"].splitlines()[0][:100])
    for f in c["files"]:
        path = f["filename"]
        before = gh("api", f"repos/pcalnon/juniper-ml/contents/{path}?ref={parent}")
        before_sha = before.get("sha") if isinstance(before, dict) else None
        try:
            with open(HAZY + path, "rb") as fh:
                hz = blob_sha(fh.read())
        except FileNotFoundError:
            hz = None
        print("  ", path.split("round42_probes/")[-1], "after", f["sha"][:8], "before", (before_sha or "?")[:8], "| hazy", (hz or "ABSENT")[:8], "hazy==before:", hz == before_sha)
