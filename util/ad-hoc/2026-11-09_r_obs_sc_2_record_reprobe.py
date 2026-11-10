#!/usr/bin/env python3
"""
Re-probe, from GitHub and PyPI, every fact plan v1.15.15 records about R-OBS-SC-2, before the plan states it.

Project: juniper-ml
Sub-Project: ad-hoc tooling (consolidated plan record)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc -- single-use verifier
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md v1.15.15;
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-09_r-obs-sc-2-published-lock-round-merged-plan-v1-15-15-next.md
         (the handoff whose facts this checks); util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py (the rulings)

Why
---
R-OBS-SC-2 ran across four sessions, and plan v1.15.15 records it from their handoffs. A handoff is a session's
summary, not the source, so each fact the plan states is checked here against the record it names: the PRs' state,
merge commits and files; the Releases' tags; the publish runs' jobs and approvals; the `pypi` deployments' statuses;
PyPI's and TestPyPI's files; each consumer lock and `pyproject.toml` on `main`; each consumer's newest Releases; and
the source lines the follow-ups cite. Each check has an expected value and prints PASS or FAIL beside what it read.

Usage
-----
    python3 util/ad-hoc/2026-11-09_r_obs_sc_2_record_reprobe.py

Exit 0 when every check passes, 1 otherwise. It needs ``gh`` (authenticated) and network access; it writes nothing.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "pcalnon"
FAILS: list[str] = []

#: (repo, number) -> (state, merge-commit prefix or None, files expected or None)
PRS = {
    ("juniper-ml", 2523): ("MERGED", "a67061bd", None),
    ("juniper-ml", 2524): ("MERGED", "93fa1f66", None),
    ("juniper-ml", 2514): ("CLOSED", None, None),
    ("juniper-ml", 2525): ("MERGED", "a93de292", None),
    ("juniper-ml", 2526): ("MERGED", "94208d86", None),
    ("juniper-ml", 2527): ("MERGED", None, None),
    ("juniper-ml", 2528): ("MERGED", "cef03a06", None),
    ("juniper-data", 525): ("MERGED", "272ff615", {"requirements.lock", "CHANGELOG.md"}),
    ("juniper-cascor", 748): ("MERGED", "7640d420", {"requirements.lock", "requirements-cpu.lock", "CHANGELOG.md"}),
    ("juniper-canopy", 806): ("MERGED", "b4b01904", {"requirements.lock", "CHANGELOG.md"}),
    ("juniper-recurrence", 233): ("MERGED", "857efbc5", {"juniper-recurrence/requirements.lock", "juniper-recurrence/CHANGELOG.md"}),
}

#: tag -> the commit it must point at
TAGS = {"juniper-observability-v0.4.2": "a93de292", "juniper-service-core-v0.7.2": "94208d86"}

#: publish run -> (package, deployment id)
RUNS = {42500706778: ("juniper-observability", 7638679639), 42499466753: ("juniper-service-core", 7638506538)}

PYPI = {"juniper-observability": "0.4.2", "juniper-service-core": "0.7.2"}

#: (repo, lock path) -> the pins it must carry on main
LOCKS = [
    ("juniper-data", "requirements.lock"),
    ("juniper-cascor", "requirements.lock"),
    ("juniper-cascor", "requirements-cpu.lock"),
    ("juniper-canopy", "requirements.lock"),
    ("juniper-recurrence", "juniper-recurrence/requirements.lock"),
]
PYPROJECTS = [
    ("juniper-data", "pyproject.toml"),
    ("juniper-cascor", "pyproject.toml"),
    ("juniper-canopy", "pyproject.toml"),
    ("juniper-recurrence", "juniper-recurrence/pyproject.toml"),
]

#: The forks' throttles (the follow-ups): (repo, path, line, a fragment the line must hold)
FORK_LINES = [
    ("juniper-data", "juniper_data/api/security.py", 250, "reset_in = int("),
    ("juniper-data", "juniper_data/api/security.py", 254, "count - 1, int("),
    ("juniper-data", "juniper_data/api/security.py", 427, "max(1, int("),
    ("juniper-cascor", "src/api/security.py", 229, "reset_in = int("),
    ("juniper-cascor", "src/api/security.py", 233, "count - 1, int("),
    ("juniper-cascor", "src/api/security.py", 386, "max(1, int("),
    ("juniper-canopy", "src/security.py", 270, "reset_in = int("),
    ("juniper-canopy", "src/security.py", 274, "count - 1, int("),
]
#: Every throttle line computes the remainder this way; truncating it with ``int`` is the defect.
REMAINDER = "self._window - (now - window_start)"

#: The first lock PR to merge (recurrence#233); a consumer Release after it could carry the new lock.
FIRST_LOCK_MERGE = "2026-11-09T10:01:54Z"


def check(ok: bool, label: str, seen: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {seen}")
    if not ok:
        FAILS.append(label)


def gh_json(*args: str) -> object:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)}: {out.stderr.strip()[:300]}")
    return json.loads(out.stdout)


def gh_raw(repo: str, path: str) -> str:
    out = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/{OWNER}/{repo}/contents/{path}?ref=main"], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise RuntimeError(f"{repo}:{path}: {out.stderr.strip()[:300]}")
    return out.stdout


def http_json(url: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:  # nosec B310 -- fixed https PyPI URLs
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def prs() -> None:
    print("== PRs")
    for (repo, number), (state, prefix, files) in PRS.items():
        data = gh_json("pr", "view", str(number), "--repo", f"{OWNER}/{repo}", "--json", "state,mergedAt,mergeCommit,files,additions,deletions,title")
        oid = (data.get("mergeCommit") or {}).get("oid") or ""
        seen = f"{data['state']} {data.get('mergedAt')} {oid[:8]} +{data['additions']}/-{data['deletions']} {data['title'][:70]}"
        ok = data["state"] == state and (prefix is None or oid.startswith(prefix))
        check(ok, f"{repo}#{number}", seen)
        if files is not None:
            got = {f["path"] for f in data["files"]}
            check(got == files, f"{repo}#{number} files", ", ".join(sorted(got)))


def releases() -> None:
    print("== Releases")
    for tag, prefix in TAGS.items():
        rel = gh_json("api", f"repos/{OWNER}/juniper-ml/releases/tags/{tag}")
        ref = gh_json("api", f"repos/{OWNER}/juniper-ml/git/ref/tags/{tag}")
        obj = ref["object"]
        sha = obj["sha"]
        if obj["type"] == "tag":
            sha = gh_json("api", f"repos/{OWNER}/juniper-ml/git/tags/{sha}")["object"]["sha"]
        check(sha.startswith(prefix), tag, f"commit {sha[:8]}, created {rel['created_at']}, published {rel['published_at']}, latest-flag n/a")


def runs() -> None:
    print("== Publish runs, approvals and deployments")
    for run_id, (package, deployment) in RUNS.items():
        jobs = gh_json("api", f"repos/{OWNER}/juniper-ml/actions/runs/{run_id}/jobs")["jobs"]
        for job in jobs:
            check(job["conclusion"] == "success", f"run {run_id} job '{job['name']}'", f"{job['status']}/{job['conclusion']} {job['started_at']} -> {job['completed_at']}")
        approvals = gh_json("api", f"repos/{OWNER}/juniper-ml/actions/runs/{run_id}/approvals")
        for appr in approvals:
            envs = ",".join(e["name"] for e in appr.get("environments", []))
            check(appr["state"] == "approved", f"run {run_id} approval", f"{appr['state']} by {appr['user']['login']} for {envs}; comment {appr.get('comment')!r}")
        if not approvals:
            check(False, f"run {run_id} approval", "none recorded")
        statuses = gh_json("api", f"repos/{OWNER}/juniper-ml/deployments/{deployment}/statuses")
        trail = "; ".join(f"{s['state']}@{s['created_at']}" for s in sorted(statuses, key=lambda s: s["created_at"]))
        check(any(s["state"] == "success" for s in statuses), f"deployment {deployment} ({package})", trail)


def pypi() -> None:
    print("== PyPI and TestPyPI")
    for package, version in PYPI.items():
        prod = http_json(f"https://pypi.org/pypi/{package}/{version}/json")
        test = http_json(f"https://test.pypi.org/pypi/{package}/{version}/json")
        if prod is None:
            check(False, f"PyPI {package} {version}", "404")
            continue
        test_sha = {u["filename"]: u["digests"]["sha256"] for u in (test or {}).get("urls", [])}
        for u in prod["urls"]:
            same = test_sha.get(u["filename"]) == u["digests"]["sha256"]
            check(True, f"PyPI {u['filename']}", f"uploaded {u['upload_time_iso_8601']}, sha256 {u['digests']['sha256'][:12]}, TestPyPI's {'same' if same else 'DIFFERENT or absent'}")
        wheels = [u["filename"] for u in prod["urls"] if u["filename"].endswith(".whl")]
        check(len(wheels) == 1 and wheels[0].endswith("-py3-none-any.whl"), f"{package} wheel tag", ", ".join(wheels))
        print(f"        requires_dist: {prod['info'].get('requires_dist')}")
    dc = http_json("https://pypi.org/pypi/juniper-data-client/json") or {"releases": {}}
    absent = [v for v in ("0.5.1", "0.6.1") if v not in dc["releases"]]
    check(absent == ["0.5.1", "0.6.1"], "juniper-data-client 0.5.1 and 0.6.1 absent (R-DC-PATCH, R-DC-PATCH-6)", f"latest {dc.get('info', {}).get('version')}; absent {absent}")


def pin(text: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}==([^\s;\\]+)", text, flags=re.M)
    return match.group(1) if match else None


def locks() -> None:
    print("== Consumer locks and pyprojects on main")
    for repo, path in LOCKS:
        text = gh_raw(repo, path)
        obs, sc, sdk = pin(text, "juniper-observability"), pin(text, "juniper-service-core"), pin(text, "sentry-sdk")
        otel_sdk = pin(text, "opentelemetry-sdk")
        check(obs == "0.4.2" and sc == "0.7.2", f"{repo}:{path}", f"observability {obs}, service-core {sc}, sentry-sdk {sdk}, opentelemetry-sdk {otel_sdk}")
        check(otel_sdk is None, f"{repo}:{path} has no opentelemetry-sdk", str(otel_sdk))
    for repo, path in PYPROJECTS:
        text = gh_raw(repo, path)
        lines = [line.strip() for line in text.splitlines() if "juniper-observability" in line or "juniper-service-core" in line]
        check(not any("0.4.2" in line or "0.7.2" in line for line in lines), f"{repo}:{path} floors unmoved", " | ".join(lines))


def consumer_releases() -> None:
    print("== Consumer Releases (none may postdate the first lock merge)")
    for repo in ("juniper-data", "juniper-cascor", "juniper-canopy", "juniper-recurrence"):
        rels = gh_json("api", f"repos/{OWNER}/{repo}/releases?per_page=4")
        newest = [f"{r['tag_name']}@{r['published_at']}" for r in rels]
        after = [r["tag_name"] for r in rels if (r["published_at"] or "") > FIRST_LOCK_MERGE]
        check(not after, f"{repo} newest Releases", ", ".join(newest))


def fork_lines() -> None:
    print("== The forks' throttle lines on main (follow-ups)")
    cache: dict[tuple[str, str], list[str]] = {}
    for repo, path, line, fragment in FORK_LINES:
        lines = cache.setdefault((repo, path), gh_raw(repo, path).splitlines())
        text = lines[line - 1].strip() if line <= len(lines) else "<past end>"
        check(fragment in text and REMAINDER in text, f"{repo}:{path}:{line}", text[:150])


def telemetry() -> None:
    print("== FastAPI native telemetry opt-out (data#454's) in each app factory")
    for repo, path in (("juniper-data", "juniper_data/api/app.py"), ("juniper-cascor", "src/api/app.py"), ("juniper-canopy", "src/main.py")):
        try:
            text = gh_raw(repo, path)
        except RuntimeError as exc:
            check(False, f"{repo}:{path}", str(exc))
            continue
        # Non-vacuous only where the file builds the app: a factory elsewhere would pass a "no telemetry=" check.
        builds = "FastAPI(" in text
        check(builds, f"{repo}:{path} constructs FastAPI(", str(builds))
        has = "telemetry=" in text
        expected = repo == "juniper-data"
        check(has == expected, f"{repo}:{path} passes telemetry=", str(has))


#: The trio's conda environments (read in place, read-only: package metadata and files, no import of either package).
CONDA_ENVS = Path("/opt/miniforge3/envs")
ML_PRIMARY = Path.home() / "Development" / "python" / "Juniper" / "juniper-ml"
#: env -> (interpreter, the versions it must hold as plain installs); JuniperCascor1 is checked separately.
PLAIN_ENVS = {"JuniperData": ("bin/python3.14t", "0.4.0", "0.5.0"), "JuniperCanopy1": ("bin/python", "0.4.0", "0.5.0")}


def environments() -> None:
    print("== The trio's environments (2026-11-09 state; editable installs follow the juniper-ml primary)")
    site = CONDA_ENVS / "JuniperCascor1" / "lib" / "python3.14" / "site-packages"
    for dist, pkg, module in (("juniper_observability", "juniper-observability", "juniper_observability"), ("juniper_service_core", "juniper-service-core", "juniper_service_core")):
        infos = sorted(site.glob(f"{dist}-*.dist-info/direct_url.json"))
        data = json.loads(infos[0].read_text(encoding="utf-8")) if len(infos) == 1 else {}
        url = data.get("url", "")
        editable = bool(data.get("dir_info", {}).get("editable"))
        check(editable and url.endswith(f"/juniper-ml/{pkg}"), f"JuniperCascor1 {pkg} is an editable install of the juniper-ml primary", f"{[p.parent.name for p in infos]} editable={editable} {url}")
        version_file = ML_PRIMARY / pkg / module / "_version.py"
        text = version_file.read_text(encoding="utf-8") if version_file.exists() else ""
        found = re.search(r'__version__\s*=\s*"([^"]+)"', text)
        check(bool(found) and found.group(1) == PYPI[pkg], f"the primary's {pkg} _version.py reads {PYPI[pkg]}", found.group(1) if found else "absent")
    for env, (interp, obs, sc) in PLAIN_ENVS.items():
        code = "import importlib.metadata as m, json; print(json.dumps({p: m.version(p) for p in ('juniper-observability', 'juniper-service-core')}))"
        out = subprocess.run([str(CONDA_ENVS / env / interp), "-I", "-B", "-c", code], capture_output=True, text=True, check=False)
        got = json.loads(out.stdout) if out.returncode == 0 else {}
        check(got == {"juniper-observability": obs, "juniper-service-core": sc}, f"{env} ({interp})", json.dumps(got) or out.stderr.strip()[:200])


def main() -> int:
    for step in (prs, releases, runs, pypi, locks, consumer_releases, fork_lines, telemetry, environments):
        try:
            step()
        except Exception as exc:  # noqa: BLE001 -- report and carry on; the exit code still fails
            check(False, step.__name__, f"{type(exc).__name__}: {exc}")
    print(f"\n{len(FAILS)} FAIL(s)" + (": " + "; ".join(FAILS) if FAILS else ""))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
