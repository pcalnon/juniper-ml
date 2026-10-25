#!/usr/bin/env python3
"""Re-probe the state the consolidated plan's v1.15.0 P12 rows assert: PyPI versions, publish runs, issues and PRs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — investigation (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (v1.14.0 -> v1.15.0);
         util/ad-hoc/2026-10-05_ecosystem_live_census.py (the census it complements: that one reads each package's
         LATEST version only, this one reads the specific versions and requirement lines the plan names)

Read-only: the PyPI JSON API (the version-specific endpoint, which the CDN serves fresher than the project page) and
GitHub REST through ``gh api``. No GraphQL.

Every check carries the state the plan asserts. A row prints ``OK`` when the probe agrees, ``DIFFERS`` when it does
not, and ``UNREADABLE`` when the read failed; a failed read is never reported as absent. Exit status: 0 when every row
is OK, 1 when any row DIFFERS, 3 when any row is UNREADABLE.

Usage
-----
    python3 util/ad-hoc/2026-10-25_p12_arc_state_reprobe.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

OWNER = "pcalnon"

# (package, version, expected): "served" means PyPI serves that exact version; "absent" means its endpoint is 404.
PYPI_VERSIONS = [
    ("juniper-data-client", "0.6.0", "served"),
    ("juniper-data-client", "0.5.1", "absent"),
    ("juniper-data-client", "0.6.1", "absent"),
    ("juniper-recurrence-model", "0.4.0", "served"),
    ("juniper-recurrence-model", "0.5.0", "served"),
    ("juniper-recurrence-model", "0.6.0", "served"),
    ("juniper-recurrence", "0.5.1", "absent"),
    ("juniper-recurrence", "0.6.0", "served"),
    ("juniper-recurrence", "0.6.1", "served"),
    ("juniper-recurrence", "0.7.0", "served"),
    ("juniper-recurrence", "0.8.0", "served"),
    ("juniper-recurrence-client", "0.3.0", "served"),
    ("juniper-recurrence-client", "0.3.1", "absent"),
    ("juniper-canopy", "0.9.0", "served"),
    ("juniper-ml", "0.11.0", "served"),
    ("juniper-ml", "0.11.1", "served"),
    ("juniper-data", "0.17.1", "served"),
    ("juniper-data", "0.17.2", "absent"),
    ("juniper-cascor", "0.12.0", "served"),
    ("juniper-ci-tools", "0.9.1", "served"),
    ("juniper-observability", "0.4.2", "absent"),
    ("juniper-service-core", "0.7.2", "absent"),
]

# (package, version, substring of a Requires-Dist line that must be present)
REQUIRES = [
    ("juniper-ml", "0.11.1", 'juniper-observability>=0.4.1; extra == "tools"'),
    ("juniper-ml", "0.11.1", 'juniper-service-core<0.8.0,>=0.7.1; extra == "tools"'),
    ("juniper-ml", "0.11.1", 'juniper-data>=0.17.0; extra == "servers"'),
    ("juniper-ml", "0.11.1", 'juniper-cascor>=0.11.0; extra == "servers"'),
    ("juniper-ml", "0.11.1", 'juniper-canopy>=0.9.0; extra == "servers"'),
    ("juniper-ml", "0.11.1", 'juniper-recurrence<0.9.0,>=0.8.0; extra == "recurrence"'),
    ("juniper-ml", "0.11.1", 'juniper-recurrence-model<0.7.0,>=0.6.0; extra == "recurrence"'),
    ("juniper-recurrence", "0.8.0", "juniper-recurrence-model<0.7.0,>=0.6.0"),
    ("juniper-recurrence", "0.8.0", "juniper-data-client<0.7.0,>=0.6.0"),
    ("juniper-recurrence", "0.6.1", "juniper-recurrence-model<0.5.0,>=0.4.0"),
    ("juniper-canopy", "0.9.0", "juniper-data-client"),
]

# (repo, run id, label): each publish run is expected completed/success.
RUNS = [
    ("juniper-ml", 40178692483, "juniper-ml 0.11.1 publish"),
    ("juniper-ml", 39577119562, "juniper-ml 0.11.0 publish"),
    ("juniper-cascor", 38085392643, "juniper-cascor 0.12.0 publish"),
    ("juniper-data", 38084468369, "juniper-data 0.17.1 publish"),
]

# (repo, number, expected state) — issues and PRs alike ("merged" only for a PR).
ITEMS = [
    ("juniper-ml", 2062, None),
    ("juniper-ml", 2210, "closed"),
    ("juniper-ml", 2211, "closed"),
    ("juniper-ml", 2227, "closed"),
    ("juniper-ml", 2319, "merged"),
    ("juniper-ml", 2320, "merged"),
    ("juniper-ml", 2321, "merged"),
    ("juniper-recurrence", 203, "merged"),
    ("juniper-recurrence", 221, "merged"),
    ("juniper-canopy", 735, None),
    ("juniper-canopy", 736, None),
    ("juniper-canopy", 737, None),
    ("juniper-canopy", 738, None),
    ("juniper-canopy", 751, None),
    ("juniper-deploy", 250, None),
    ("juniper-deploy", 258, "merged"),
]

ROWS: list[tuple[str, str, str]] = []  # (verdict, subject, detail)


def record(verdict: str, subject: str, detail: str) -> None:
    ROWS.append((verdict, subject, detail))


def pypi(package: str, version: str):
    """Return (status, json): status 200 with the body, 404 with None, or None with None for a failed read."""
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as exc:
        return (404, None) if exc.code == 404 else (None, None)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None, None


def gh(path: str):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return None


def check_versions() -> None:
    for package, version, expected in PYPI_VERSIONS:
        status, body = pypi(package, version)
        subject = f"pypi {package}=={version} expected {expected}"
        if status is None:
            record("UNREADABLE", subject, "the read failed")
            continue
        if status == 404:
            record("OK" if expected == "absent" else "DIFFERS", subject, "404 (not on PyPI)")
            continue
        uploads = sorted(f.get("upload_time_iso_8601", "?") for f in body.get("urls", []))
        when = uploads[0] if uploads else "no files"
        record("OK" if expected == "served" else "DIFFERS", subject, f"served; first upload {when}")


def check_requires() -> None:
    cache: dict[tuple[str, str], list[str] | None] = {}
    for package, version, needle in REQUIRES:
        key = (package, version)
        if key not in cache:
            status, body = pypi(package, version)
            cache[key] = (body["info"].get("requires_dist") or []) if status == 200 else None
        lines = cache[key]
        subject = f"requires {package}=={version} has {needle!r}"
        if lines is None:
            record("UNREADABLE", subject, "the read failed or the version is not served")
            continue
        hits = [line for line in lines if needle in line]
        record("OK" if hits else "DIFFERS", subject, "; ".join(hits) if hits else "no such line")


def check_runs() -> None:
    for repo, run_id, label in RUNS:
        body = gh(f"repos/{OWNER}/{repo}/actions/runs/{run_id}")
        subject = f"run {repo} {run_id} ({label}) expected completed/success"
        if body is None:
            record("UNREADABLE", subject, "the read failed")
            continue
        state = f"{body.get('status')}/{body.get('conclusion')}; updated {body.get('updated_at')}"
        good = body.get("status") == "completed" and body.get("conclusion") == "success"
        record("OK" if good else "DIFFERS", subject, state)


def check_items() -> None:
    for repo, number, expected in ITEMS:
        body = gh(f"repos/{OWNER}/{repo}/issues/{number}")
        subject = f"{repo}#{number} expected {expected or '(report only)'}"
        if body is None:
            record("UNREADABLE", subject, "the read failed")
            continue
        kind = "PR" if "pull_request" in body else "issue"
        state = body.get("state")
        if kind == "PR" and state == "closed":
            pr = gh(f"repos/{OWNER}/{repo}/pulls/{number}")
            if pr is None:
                record("UNREADABLE", subject, "the PR read failed")
                continue
            if pr.get("merged_at"):
                state = "merged"
        title = (body.get("title") or "")[:90]
        detail = f"{kind} {state}; closed {body.get('closed_at') or '-'}; {title}"
        if expected is None:
            record("INFO", subject, detail)
        else:
            record("OK" if state == expected else "DIFFERS", subject, detail)


def main() -> int:
    check_versions()
    check_requires()
    check_runs()
    check_items()
    for verdict, subject, detail in ROWS:
        print(f"{verdict:<10} {subject}: {detail}")
    verdicts = {verdict for verdict, _, _ in ROWS}
    if "UNREADABLE" in verdicts:
        return 3
    return 1 if "DIFFERS" in verdicts else 0


if __name__ == "__main__":
    sys.exit(main())
