#!/usr/bin/env python3
"""Round 4 lane F probe: juniper-ml#2089 and #2097 live state (read-only gh GETs).

Commits (sha, time, parents, verification), paginated file list (count, lane dirs,
the round-3 probes), CodeQL check-runs on each head with their output title/summary,
merge state, auto-merge, and the consolidation PR's existence.
"""
import collections
import json
import subprocess


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode != 0:
        return {"__error__": p.stderr.strip()[:300]}
    out = p.stdout.strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


for n in (2089, 2097):
    v = gh("pr", "view", str(n), "--repo", "pcalnon/juniper-ml", "--json", "state,headRefOid,headRefName,mergeStateStatus,autoMergeRequest,isDraft,mergeCommit,createdAt,updatedAt")
    print(f"== #{n} ==", json.dumps(v))
    commits = gh("api", "--paginate", f"repos/pcalnon/juniper-ml/pulls/{n}/commits?per_page=100")
    for c in commits:
        print("  commit", c["sha"][:8], c["commit"]["committer"]["date"], "parents", [p["sha"][:8] for p in c["parents"]], "verified", c["commit"]["verification"]["verified"], c["commit"]["message"].splitlines()[0][:90])
    head = v.get("headRefOid") if isinstance(v, dict) else None
    if head:
        cr = gh("api", f"repos/pcalnon/juniper-ml/commits/{head}/check-runs?per_page=100")
        for c in cr.get("check_runs", []):
            if "codeql" in c["name"].lower():
                print("  CodeQL on head", head[:8], c["id"], c["status"], c["conclusion"], c["started_at"], c["completed_at"], "|", (c.get("output") or {}).get("title"))
    if n == 2089:
        # prior heads
        for s in ("a64d72fe", "a2fa3ad8"):
            full = gh("api", f"repos/pcalnon/juniper-ml/commits/{s}")
            if isinstance(full, dict) and "sha" in full:
                cr = gh("api", f"repos/pcalnon/juniper-ml/commits/{full['sha']}/check-runs?per_page=100")
                for c in cr.get("check_runs", []):
                    if "codeql" in c["name"].lower():
                        print("  CodeQL on", s, c["id"], c["status"], c["conclusion"], c["started_at"], c["completed_at"], "|", (c.get("output") or {}).get("title"))
        files = gh("api", "--paginate", f"repos/pcalnon/juniper-ml/pulls/{n}/files?per_page=100")
        names = [f["filename"] for f in files]
        print("  files:", len(names))
        base = "util/ad-hoc/2026-09-24_round42_probes/"
        dirs = collections.Counter()
        other = []
        for nm in names:
            if nm.startswith(base):
                rest = nm[len(base):]
                if "/" in rest:
                    dirs[rest.split("/")[0]] += 1
                else:
                    other.append(nm)
            else:
                other.append(nm)
        print("  lane dirs:", len(dirs))
        for d, k in sorted(dirs.items()):
            print(f"    {d}: {k}")
        print("  other files:", other)
        for p in ("handoff-2fba4397-round3-laneF/probe_data.py", "handoff-2fba4397-round3-laneF/probe_cascor.py", "handoff-2fba4397-round3-laneF/probe_primer.py", "data438-fixforward-round1-laneB/serve.py", "data438-fixforward-round1-laneB/common.py"):
            print("   has", p, (base + p) in names)
        print("   any laneB/scripts/ path:", any(nm.startswith(base + "data438-fixforward-round1-laneB/scripts/") for nm in names))

print("\n== consolidation PR ==")
print(gh("pr", "list", "--repo", "pcalnon/juniper-ml", "--head", "docs/handoff-round42-consolidated", "--state", "all", "--json", "number,state"))
print("\n== open PRs in data/cascor/canopy ==")
for r in ("juniper-data", "juniper-cascor", "juniper-canopy"):
    print(r, gh("pr", "list", "--repo", f"pcalnon/{r}", "--state", "open", "--json", "number,title"))
print("\n== juniper-ml main ==")
m = gh("api", "repos/pcalnon/juniper-ml/commits/main")
print(m["sha"][:8], m["commit"]["committer"]["date"], m["commit"]["message"].splitlines()[0][:100])
