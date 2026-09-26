#!/usr/bin/env python3
"""Round 4 lane F probe: do the open handoff PRs (#2096 canopy combined, #2100 containers, #2097
Lane F) mention the parked register rows APD-ECO-009..012 / APD-DATA-054..056 / APD-ML-007..008?
Reads each PR's changed prompts/*.md at its head via gh api (read-only), prints only matching lines."""
import base64
import json
import re
import subprocess

IDS = re.compile(r"(APD-)?(ECO-0(09|1[0-2])|DATA-05[4-6]|ML-00[78])")


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    return json.loads(p.stdout) if p.returncode == 0 and p.stdout.strip() else None


for n in (2096, 2100, 2097):
    pr = gh("pr", "view", str(n), "--repo", "pcalnon/juniper-ml", "--json", "headRefOid,state")
    files = subprocess.run(["gh", "api", "--paginate", f"repos/pcalnon/juniper-ml/pulls/{n}/files?per_page=100", "--jq", ".[].filename"], capture_output=True, text=True).stdout.split()
    handoffs = [f for f in files if f.startswith("prompts/thread-handoff_automated-prompts/")]
    print(f"== #{n} {pr['state']} {pr['headRefOid'][:8]}: {len(handoffs)} handoff file(s)")
    for f in handoffs:
        c = gh("api", f"repos/pcalnon/juniper-ml/contents/{f}?ref={pr['headRefOid']}")
        text = base64.b64decode(c["content"]).decode("utf-8", "replace") if c else ""
        hits = [(i, ln) for i, ln in enumerate(text.split("\n"), 1) if IDS.search(ln)]
        print(f"   {f.split('/')[-1][:90]}: {len(hits)} matching lines")
        for i, ln in hits[:6]:
            print(f"     L{i}: {ln[:220]}")
