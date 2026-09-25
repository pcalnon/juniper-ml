#!/usr/bin/env python3
"""Round 4 lane F probe: CodeQL check-run annotations on #2089's last two heads (read-only).
Counts annotations by level, and lists the failure-level (high) ones with path:line and title."""
import collections
import json
import subprocess


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode != 0:
        return {"__error__": p.stderr.strip()[:300]}
    return json.loads(p.stdout)


for run_id in (107922271680, 107927197304):
    c = gh("api", f"repos/pcalnon/juniper-ml/check-runs/{run_id}")
    print("==", run_id, c.get("head_sha", "")[:8], c.get("conclusion"), c.get("completed_at"), "|", (c.get("output") or {}).get("title"), "| annotations_count", (c.get("output") or {}).get("annotations_count"))
    anns = gh("api", "--paginate", f"repos/pcalnon/juniper-ml/check-runs/{run_id}/annotations?per_page=100")
    lv = collections.Counter(a["annotation_level"] for a in anns)
    print("   levels:", dict(lv))
    for a in anns:
        if a["annotation_level"] == "failure":
            print("   HIGH", a["path"].split("round42_probes/")[-1], a["start_line"], "|", a.get("title"))
    dirs = collections.Counter(a["path"].split("round42_probes/")[-1].split("/")[0] for a in anns)
    print("   by dir:", dict(dirs))
