"""
Re-probe every #N, run id, PyPI version and upstream-source claim cited by the round-2 juniper-data carriers.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 carrier validation (claims and docs lens), juniper-data data-docs / data-tests / data-code

Read-only: `gh api` GETs and PyPI JSON reads. Prints only public metadata (titles, states, dates).
Usage: python3 util/ad-hoc/2026-11-08_flood4r2_val_data-claims_refs.py <out_dir>
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

PRS = {
    "pcalnon/juniper-data": [385, 387, 391, 454, 516, 518, 519, 520, 521, 522, 523, 524],
    "pcalnon/juniper-ml": [2514, 2524, 2526, 2527],
}
RUNS = [("pcalnon/juniper-cascor-worker", 34292278641), ("pcalnon/juniper-data", 34292278641)]
PYPI = ["juniper-service-core", "juniper-data", "juniper-ci-tools"]
UPSTREAM = [("docker/metadata-action", "dc802804100637a589fabce1cb79ff13a1411302", "src/meta.ts")]


def gh(path: str) -> dict | None:
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return {"_error": (proc.stderr or proc.stdout).strip()[:300]}
    return json.loads(proc.stdout)


def main() -> int:
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {}

    for repo, numbers in PRS.items():
        for n in numbers:
            data = gh(f"repos/{repo}/pulls/{n}")
            if data and "_error" not in data:
                report[f"{repo}#{n}"] = {
                    "title": data.get("title"),
                    "state": data.get("state"),
                    "merged_at": data.get("merged_at"),
                    "head_ref": (data.get("head") or {}).get("ref"),
                    "head_sha": (data.get("head") or {}).get("sha"),
                    "draft": data.get("draft"),
                    "changed_files": data.get("changed_files"),
                }
            else:
                issue = gh(f"repos/{repo}/issues/{n}")
                report[f"{repo}#{n}"] = {"pull_error": (data or {}).get("_error"), "issue_title": (issue or {}).get("title"), "issue_state": (issue or {}).get("state")}

    for repo, run_id in RUNS:
        data = gh(f"repos/{repo}/actions/runs/{run_id}")
        if data and "_error" not in data:
            report[f"{repo} run {run_id}"] = {k: data.get(k) for k in ("name", "event", "status", "conclusion", "created_at", "head_branch", "head_sha", "path")}
        else:
            report[f"{repo} run {run_id}"] = {"error": (data or {}).get("_error")}

    for pkg in PYPI:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json", timeout=30) as resp:  # noqa: S310 - fixed https host
            data = json.load(resp)
        releases = data.get("releases", {})
        recent = sorted(releases)[-200:]
        report[f"pypi {pkg}"] = {
            "info.version": data["info"]["version"],
            "uploads": {v: min((f["upload_time_iso_8601"] for f in releases[v]), default=None) for v in recent if v.startswith(("0.7.", "0.17.", "0.9.", "0.18."))},
        }

    for repo, sha, path in UPSTREAM:
        data = gh(f"repos/{repo}/contents/{path}?ref={sha}")
        if data and "content" in data:
            text = base64.b64decode(data["content"]).decode("utf-8")
            (out_dir / f"{repo.replace('/', '_')}_{sha[:8]}_{Path(path).name}").write_text(text, encoding="utf-8")
            report[f"{repo}@{sha[:8]}:{path}"] = {"saved": True, "lines": text.count("\n")}
        else:
            report[f"{repo}@{sha[:8]}:{path}"] = {"error": (data or {}).get("_error")}

    out = out_dir / "refs.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
