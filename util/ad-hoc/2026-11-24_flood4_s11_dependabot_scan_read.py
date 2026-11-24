"""Read the pull-request secret scan on a Dependabot PR: did the ported Gitleaks steps run, and what did they report?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — investigation (flood-4 session 11: the owed first-Dependabot-PR reads after ruling 10's Gitleaks ports)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530 and
    its ports; session 9's read of cascor#768, worker#233, canopy#824 and deploy#280 (STATE_S9.txt, 2026-11-16).

For each REPO#PR: the PR's head commit, every check run on it, and, for each job whose name names a secret scan
(Security Scan / Security Scans / Gitleaks / Secret), its log through `gh api repos/<o>/<r>/actions/jobs/<id>/logs`
(`gh run view --log` has returned empty here). The log is saved under --out, and the lines that answer the read are
printed: the engine version, the range the pull-request step scanned and how many commits the PR reports, the
engine's own "N commits scanned." and "no leaks found" / "leaks found", and the self-test tally. Read-only: GETs only.

Usage: python3 util/ad-hoc/2026-11-24_flood4_s11_dependabot_scan_read.py --out tmp/flood4/session11/dependabot_reads REPO#PR [...]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 -- fixed argv: gh api GETs
import sys
from pathlib import Path

OWNER = "pcalnon"
SCAN_JOB = re.compile(r"secur|gitleaks|secret", re.IGNORECASE)
KEY_LINES = re.compile(
    r"GITLEAKS_VERSION|gitleaks version|Scanning \d+ commit|the pull request reports|commits? scanned|no leaks found|leaks found|"
    r"passed|failed|individual user|No license key",
)


def _gh(args: list[str]) -> str:
    done = subprocess.run(["gh", *args], capture_output=True, text=True, check=False, timeout=120)  # nosec B603 B607
    if done.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)}: {done.stderr.strip()[:300]}")
    return done.stdout


def read(repo: str, pr: int, out: Path, sha: str | None = None) -> dict:
    meta = json.loads(_gh(["pr", "view", str(pr), "--repo", f"{OWNER}/{repo}", "--json", "headRefOid,author,createdAt,state,title"]))
    head = sha or meta["headRefOid"]
    runs = json.loads(_gh(["api", f"repos/{OWNER}/{repo}/commits/{head}/check-runs?per_page=100"]))["check_runs"]
    result = {"repo": repo, "pr": pr, "head": head, "author": meta["author"]["login"], "createdAt": meta["createdAt"], "state": meta["state"], "jobs": []}
    for run in runs:
        if not SCAN_JOB.search(run["name"]):
            continue
        job = {"name": run["name"], "id": run["id"], "status": run["status"], "conclusion": run["conclusion"], "lines": []}
        try:
            wf = json.loads(_gh(["api", f"repos/{OWNER}/{repo}/actions/jobs/{run['id']}"]))
            wr = json.loads(_gh(["api", f"repos/{OWNER}/{repo}/actions/runs/{wf['run_id']}"]))
            job["run"] = {"id": wr["id"], "event": wr["event"], "attempt": wr["run_attempt"], "triggering_actor": (wr.get("triggering_actor") or {}).get("login"), "started": wf.get("started_at")}
        except (RuntimeError, KeyError, json.JSONDecodeError) as exc:
            job["run"] = {"error": str(exc)[:200]}
        try:
            log = _gh(["api", f"repos/{OWNER}/{repo}/actions/jobs/{run['id']}/logs"])
        except RuntimeError as exc:
            job["log_error"] = str(exc)
            result["jobs"].append(job)
            continue
        path = out / f"{repo}_{pr}_{head[:8]}_{run['id']}.log"
        path.write_text(log, encoding="utf-8")
        job["log"] = str(path)
        seen = []
        for line in log.splitlines():
            text = line.split(" ", 1)[1] if re.match(r"^\d{4}-\d\d-\d\dT", line) else line
            if KEY_LINES.search(text) and text.strip() not in seen:
                seen.append(text.strip())
        job["lines"] = seen[:40]
        result["jobs"].append(job)
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("targets", nargs="+", help="REPO#PR or REPO#PR@SHA (a commit other than the head), e.g. juniper-ml#2598@9804dc35")
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for target in args.targets:
        repo, rest = target.split("#", 1)
        pr, _, sha = rest.partition("@")
        res = read(repo, int(pr), out, sha or None)
        results.append(res)
        print(f"== {repo}#{pr} by {res['author']} ({res['createdAt']}, {res['state']}), head {res['head'][:8]}")
        if not res["jobs"]:
            print("   NO secret-scan job on the head commit")
        for job in res["jobs"]:
            print(f"   job {job['name']!r} {job['status']}/{job['conclusion']} id {job['id']} run {job.get('run')}")
            for line in job.get("lines", []):
                print(f"     | {line[:200]}")
            if "log_error" in job:
                print(f"     ! {job['log_error']}")
    (out / "reads.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
