#!/usr/bin/env python3
"""Lane A2: re-measure required-check spans from ALL executions (not filter=latest).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc consensus-round tooling (Lane A2, CI-budget re-evaluation)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-22
Status:      ad-hoc -- single-use measurement for the 2026-09-22 CI-budget consensus round.
             Written independently: it neither imports nor reuses the v2 span tool or the
             2026-09-22 reprobe tool; only the DEFINITION of the quantity is shared.

QUANTITY (shared definition)
----------------------------
span(head) = max(completed_at) - min(started_at) over the repo's REQUIRED contexts on a merged
PR's head SHA; p90 = sorted(spans)[int(0.9 * (n - 1))]; sample = `gh pr list --state merged
--limit 30`.

WHAT IS DIFFERENT HERE (the instrument)
---------------------------------------
* Check-runs are read with `filter=all`, so every execution of a context is visible.
* Every Actions check-run is attributed to its workflow run through `check_suite.id` ->
  `actions/runs?head_sha=` (event, run_attempt, workflow path), and, for any workflow run with
  run_attempt > 1, to its ATTEMPT through `actions/runs/<id>/jobs?filter=all` (job id == check
  run id).
* Legacy commit statuses are read from `commits/<sha>/statuses` (every state change), only when
  a required context is not found among the check-runs.
* `filter=latest` is called ONLY on heads where filter=all shows a duplicate required-context
  name -- there it is the literal v2 raw input; elsewhere latest == all by construction.
* Required contexts are read BOTH ways -- union over all repo rulesets, and the rules that are
  active on `main` (`rules/branches/main`, what util/wait_for_checks.py reads) -- and compared.

Estimators computed per head (all over required contexts only):
  raw_latest  -- the v2 quantity (latest execution per context name)
  envelope    -- min start / max end over ALL executions
  first_pass  -- per context, the FIRST execution cluster only (executions that started before
                 the context's first execution completed)
Flags per head: sequential repeat of a required context, and its MECHANISM (re-run attempt of
the same workflow run / a new workflow run of the same workflow / a same-named job in a
DIFFERENT workflow / a non-Actions source), and whether the repeat extends past the first pass.

Usage
-----
    python3 span_all_attempts.py fetch            # API calls (cached; hard call cap)
    python3 span_all_attempts.py analyze          # offline, from cache
    python3 span_all_attempts.py detail --repo juniper-data --pr 405 [--jobs]
Cache: $LANEA2_CACHE (default: the session scratchpad). Call cap: $LANEA2_MAX_CALLS (1100).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OWNER = "pcalnon"
REPOS = [
    "juniper-ml",
    "juniper-canopy",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-data",
    "juniper-data-client",
    "juniper-deploy",
    "juniper-recurrence",
]
SCRATCH = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/36979dd7-9695-4932-8e7f-158acf63af9c/scratchpad/laneA2-cache"
CACHE = Path(os.environ.get("LANEA2_CACHE", SCRATCH))
MAX_CALLS = int(os.environ.get("LANEA2_MAX_CALLS", "1100"))
SAMPLE_N = 30
ACTIONS_APP_ID = 15368
PASSING = {"success", "skipped", "neutral"}
_calls = {"n": 0}


# --------------------------------------------------------------------------- fetch layer
def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _trim_check_run(cr: dict) -> dict:
    app = cr.get("app") or {}
    suite = cr.get("check_suite") or {}
    return {
        "id": cr.get("id"),
        "name": cr.get("name"),
        "status": cr.get("status"),
        "conclusion": cr.get("conclusion"),
        "started_at": cr.get("started_at"),
        "completed_at": cr.get("completed_at"),
        "check_suite_id": suite.get("id"),
        "app_id": app.get("id"),
        "app_slug": app.get("slug"),
        "details_url": cr.get("details_url"),
        "head_sha": cr.get("head_sha"),
    }


def _trim_run(r: dict) -> dict:
    return {
        "id": r.get("id"),
        "name": r.get("name"),
        "path": r.get("path"),
        "event": r.get("event"),
        "run_attempt": r.get("run_attempt"),
        "run_number": r.get("run_number"),
        "created_at": r.get("created_at"),
        "updated_at": r.get("updated_at"),
        "run_started_at": r.get("run_started_at"),
        "status": r.get("status"),
        "conclusion": r.get("conclusion"),
        "check_suite_id": r.get("check_suite_id"),
        "head_sha": r.get("head_sha"),
        "head_branch": r.get("head_branch"),
        "actor": (r.get("actor") or {}).get("login"),
        "triggering_actor": (r.get("triggering_actor") or {}).get("login"),
        "previous_attempt_url": r.get("previous_attempt_url"),
    }


def _trim_job(j: dict) -> dict:
    return {
        "id": j.get("id"),
        "run_id": j.get("run_id"),
        "run_attempt": j.get("run_attempt"),
        "name": j.get("name"),
        "status": j.get("status"),
        "conclusion": j.get("conclusion"),
        "created_at": j.get("created_at"),
        "started_at": j.get("started_at"),
        "completed_at": j.get("completed_at"),
        "workflow_name": j.get("workflow_name"),
        "runner_name": j.get("runner_name"),
        "labels": j.get("labels"),
    }


def _trim_status(s: dict) -> dict:
    return {
        "id": s.get("id"),
        "context": s.get("context"),
        "state": s.get("state"),
        "created_at": s.get("created_at"),
        "updated_at": s.get("updated_at"),
        "creator": (s.get("creator") or {}).get("login"),
        "target_url": s.get("target_url"),
    }


def _gh(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(["gh"] + args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def cached(key: str, producer, offline: bool = False):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.sha256(key.encode()).hexdigest()[:32] + ".json")
    if f.exists():
        return json.loads(f.read_text())["body"]
    if offline:
        return None
    body = producer()
    f.write_text(json.dumps({"key": key, "fetched_at": _now(), "body": body}))
    return body


def rest(path: str, offline: bool = False):
    """One REST GET (cached). Errors are returned as {'_error': ...}, never raised."""

    def produce():
        if _calls["n"] >= MAX_CALLS:
            raise SystemExit(f"REST call cap {MAX_CALLS} reached -- refusing to continue")
        _calls["n"] += 1
        rc, out, err = _gh(["api", "-H", "Accept: application/vnd.github+json", "-H", "X-GitHub-Api-Version: 2022-11-28", path])
        if rc != 0:
            return {"_error": (err or "").strip()[:400], "_stdout": (out or "")[:400]}
        return json.loads(out) if out.strip() else None

    return cached("REST " + path, produce, offline)


def rest_paged(path: str, list_key: str | None, trim, offline: bool = False) -> list | dict:
    """GET all pages of a list endpoint; returns trimmed items (or {'_error'} on failure)."""
    items: list = []
    page = 1
    sep = "&" if "?" in path else "?"
    while True:
        body = rest(f"{path}{sep}per_page=100&page={page}", offline)
        if body is None:
            return {"_error": "not cached (offline)"}
        if isinstance(body, dict) and "_error" in body:
            return body
        chunk = body[list_key] if list_key else body
        items.extend(trim(x) for x in chunk)
        total = body.get("total_count") if (list_key and isinstance(body, dict)) else None
        if len(chunk) < 100 or (total is not None and len(items) >= total):
            break
        page += 1
    return items


# --------------------------------------------------------------------------- required contexts
def required_contexts(repo: str, offline: bool = False) -> dict:
    lst = rest(f"repos/{OWNER}/{repo}/rulesets?includes_parents=true&per_page=100", offline)
    rulesets = []
    union: dict[str, set] = {}
    if isinstance(lst, list):
        for rs in lst:
            det = rest(f"repos/{OWNER}/{repo}/rulesets/{rs['id']}", offline) or {}
            ctxs = []
            for rule in det.get("rules") or []:
                if rule.get("type") == "required_status_checks":
                    for e in (rule.get("parameters") or {}).get("required_status_checks") or []:
                        ctxs.append((e.get("context"), e.get("integration_id")))
                        union.setdefault(e.get("context"), set()).add(e.get("integration_id"))
            rulesets.append(
                {
                    "id": rs.get("id"),
                    "name": rs.get("name"),
                    "target": det.get("target"),
                    "enforcement": det.get("enforcement"),
                    "include": ((det.get("conditions") or {}).get("ref_name") or {}).get("include"),
                    "n_required": len(ctxs),
                }
            )
    active = rest(f"repos/{OWNER}/{repo}/rules/branches/main?per_page=100", offline)
    active_ctx: dict[str, set] = {}
    if isinstance(active, list):
        for rule in active:
            if rule.get("type") == "required_status_checks":
                for e in (rule.get("parameters") or {}).get("required_status_checks") or []:
                    active_ctx.setdefault(e.get("context"), set()).add(e.get("integration_id"))
    classic = rest(f"repos/{OWNER}/{repo}/branches/main/protection/required_status_checks", offline)
    classic_ctx = []
    if isinstance(classic, dict) and "_error" not in classic:
        classic_ctx = [c.get("context") for c in classic.get("checks") or []] or list(classic.get("contexts") or [])
    return {
        "rulesets": rulesets,
        "union": {k: sorted(v, key=str) for k, v in union.items()},
        "active_main": {k: sorted(v, key=str) for k, v in active_ctx.items()},
        "classic": classic_ctx,
        "classic_error": classic.get("_error") if isinstance(classic, dict) else None,
    }


# --------------------------------------------------------------------------- sample
def sample(repo: str, offline: bool = False) -> list:
    def produce():
        rc, out, err = _gh(["pr", "list", "--repo", f"{OWNER}/{repo}", "--state", "merged", "--limit", str(SAMPLE_N), "--json", "number,headRefOid,mergedAt,createdAt,title,baseRefName"])
        if rc != 0:
            return {"_error": err.strip()[:400]}
        return json.loads(out)

    return cached(f"SAMPLE {repo} n={SAMPLE_N}", produce, offline)


# --------------------------------------------------------------------------- per-head data
def head_data(repo: str, sha: str, required: dict, offline: bool = False) -> dict:
    crs = rest_paged(f"repos/{OWNER}/{repo}/commits/{sha}/check-runs?filter=all", "check_runs", _trim_check_run, offline)
    runs = rest_paged(f"repos/{OWNER}/{repo}/actions/runs?head_sha={sha}", "workflow_runs", _trim_run, offline)
    out = {"check_runs": crs, "runs": runs, "jobs_by_run": {}, "statuses": None, "latest": None}
    if isinstance(runs, list):
        for r in runs:
            if (r.get("run_attempt") or 1) > 1:
                out["jobs_by_run"][str(r["id"])] = rest_paged(f"repos/{OWNER}/{repo}/actions/runs/{r['id']}/jobs?filter=all", "jobs", _trim_job, offline)
    names = {c["name"] for c in crs} if isinstance(crs, list) else set()
    if any(ctx not in names for ctx in required):
        out["statuses"] = rest_paged(f"repos/{OWNER}/{repo}/commits/{sha}/statuses", None, _trim_status, offline)
    if isinstance(crs, list):
        req_names = [c["name"] for c in crs if c["name"] in required]
        if len(req_names) != len(set(req_names)):
            out["latest"] = rest_paged(f"repos/{OWNER}/{repo}/commits/{sha}/check-runs?filter=latest", "check_runs", _trim_check_run, offline)
    return out


# --------------------------------------------------------------------------- analysis
def ts(s: str | None) -> float | None:
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def hms(t: float | None) -> str:
    return "-" if t is None else datetime.fromtimestamp(t, timezone.utc).strftime("%m-%dT%H:%M:%S")


def p90(xs: list) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    return s[int(0.9 * (len(s) - 1))]


def executions(repo: str, hd: dict, required: dict) -> dict:
    """Map required context -> list of executions (dicts), from check-runs and statuses."""
    runs = hd["runs"] if isinstance(hd["runs"], list) else []
    suite_to_run = {r["check_suite_id"]: r for r in runs}
    job_attempt = {}
    for _rid, jobs in hd["jobs_by_run"].items():
        if isinstance(jobs, list):
            for j in jobs:
                job_attempt[j["id"]] = j["run_attempt"]
    ex: dict[str, list] = {c: [] for c in required}
    for cr in hd["check_runs"] if isinstance(hd["check_runs"], list) else []:
        name = cr["name"]
        if name not in required:
            continue
        integ = [i for i in required[name] if i is not None]
        if integ and cr["app_id"] not in integ:
            continue
        run = suite_to_run.get(cr["check_suite_id"])
        ex[name].append(
            {
                "src": "check_run",
                "id": cr["id"],
                "start": ts(cr["started_at"]),
                "end": ts(cr["completed_at"]) if cr["status"] == "completed" else None,
                "conclusion": cr["conclusion"],
                "suite": cr["check_suite_id"],
                "app": cr["app_slug"],
                "run_id": run["id"] if run else None,
                "workflow": run["path"] if run else None,
                "event": run["event"] if run else None,
                "attempt": job_attempt.get(cr["id"], 1 if (run and (run.get("run_attempt") or 1) == 1) else None),
            }
        )
    if isinstance(hd.get("statuses"), list):
        by_ctx: dict[str, list] = {}
        for s in hd["statuses"]:
            if s["context"] in required:
                by_ctx.setdefault(s["context"], []).append(s)
        for ctx, sts in by_ctx.items():
            if ex[ctx]:
                continue  # already satisfied by a check-run of that name
            sts.sort(key=lambda s: (s["created_at"], s["id"]))
            cur = None
            for s in sts:
                t = ts(s["created_at"])
                if cur is None:
                    cur = {"src": "status", "id": s["id"], "start": t, "end": None, "conclusion": None, "suite": None, "app": s["creator"], "run_id": None, "workflow": None, "event": None, "attempt": None}
                if s["state"] == "pending":
                    if cur["end"] is not None:  # a new pending after a terminal state: a repeat
                        ex[ctx].append(cur)
                        cur = {"src": "status", "id": s["id"], "start": t, "end": None, "conclusion": None, "suite": None, "app": s["creator"], "run_id": None, "workflow": None, "event": None, "attempt": None}
                else:
                    if cur["end"] is not None:  # terminal after terminal, no pending between
                        ex[ctx].append(cur)
                        cur = {"src": "status", "id": s["id"], "start": t, "end": None, "conclusion": None, "suite": None, "app": s["creator"], "run_id": None, "workflow": None, "event": None, "attempt": None}
                    cur["end"] = t
                    cur["conclusion"] = s["state"]
            if cur is not None:
                ex[ctx].append(cur)
    for ctx in ex:
        ex[ctx].sort(key=lambda e: (e["start"] if e["start"] is not None else 1e18, e["id"]))
    return ex


def classify(ex: dict) -> dict:
    """Per-head spans and repeat flags from the execution map."""
    present = {c: v for c, v in ex.items() if v}
    res = {"n_required": len(ex), "n_present": len(present), "missing": sorted(c for c, v in ex.items() if not v)}
    if not present:
        res["measurable"] = False
        return res
    res["measurable"] = True
    starts_all, ends_all = [], []
    fp_starts, fp_ends, fp_ok = [], [], True
    repeats = []
    incomplete = []
    concurrent_dups = []
    carried = []
    for ctx, execs in present.items():
        for e in execs:
            if e["start"] is not None:
                starts_all.append(e["start"])
            if e["end"] is not None:
                ends_all.append(e["end"])
            else:
                incomplete.append(ctx)
        first = execs[0]
        cluster = [e for e in execs if e is first or (first["end"] is not None and e["start"] is not None and e["start"] < first["end"])]
        if first["end"] is None:
            cluster = [first]
        if any(not (e["start"] == first["start"] and e["end"] == first["end"]) for e in cluster[1:]):
            concurrent_dups.append(ctx)
        elif len(cluster) > 1:
            carried.append(ctx)
        fp_starts.append(min(e["start"] for e in cluster if e["start"] is not None))
        cl_ends = [e["end"] for e in cluster if e["end"] is not None]
        if cl_ends:
            fp_ends.append(max(cl_ends))
        if any((e["conclusion"] or "") not in PASSING for e in cluster):
            fp_ok = False
        cluster_ids = {id(e) for e in cluster}
        for idx, e in enumerate(execs):
            if id(e) in cluster_ids:
                continue
            # "Re-run failed jobs" CARRIES the passing jobs of attempt N into attempt N+1 as new
            # check-runs with the SAME started_at/completed_at (observed on canopy#653). A copy
            # is not an execution; a zero-duration copy would otherwise read as a sequential repeat.
            if any(p["start"] == e["start"] and p["end"] == e["end"] for p in execs[:idx]):
                carried.append(ctx)
                continue
            prior = [p for p in execs if p is not e and p["end"] is not None and e["start"] is not None and p["end"] <= e["start"]]
            if not prior:
                concurrent_dups.append(ctx)
                continue
            p = prior[-1]
            if e["src"] != "check_run" or p["src"] != "check_run":
                mech = "non-actions"
            elif (e["attempt"] or 1) > 1 or (e["run_id"] is not None and any(q["run_id"] == e["run_id"] for q in prior)):
                # attempt N>1 of a workflow run -- even when the immediately-prior execution of the
                # context belongs to a DIFFERENT run (recurrence#175: attempt 2 of a run whose
                # attempt 1 was cancelled, while a sibling run of the same workflow had passed)
                mech = "rerun-attempt"
            elif e["workflow"] is not None and e["workflow"] == p["workflow"]:
                mech = "new-run-same-workflow"
            elif e["workflow"] is not None and p["workflow"] is not None:
                mech = "different-workflow"
            else:
                mech = "unattributed"
            repeats.append({"ctx": ctx, "mech": mech, "event": e["event"], "attempt": e["attempt"], "start": e["start"], "end": e["end"], "conclusion": e["conclusion"], "prior_conclusion": p["conclusion"], "prior_end": p["end"]})
    # raw_latest: latest execution per name (by check-run id -- verified against the API's filter=latest where it matters)
    lat_starts, lat_ends = [], []
    for _ctx, execs in present.items():
        last = max(execs, key=lambda e: (e["id"] if e["src"] == "check_run" else -1, e["start"] or 0))
        if last["start"] is not None:
            lat_starts.append(last["start"])
        if last["end"] is not None:
            lat_ends.append(last["end"])
    res["raw_latest_emulated"] = (max(lat_ends) - min(lat_starts)) if lat_starts and lat_ends else None
    res["envelope"] = (max(ends_all) - min(starts_all)) if starts_all and ends_all else None
    res["first_pass"] = (max(fp_ends) - min(fp_starts)) if fp_starts and fp_ends else None
    res["first_pass_start"] = min(fp_starts) if fp_starts else None
    res["first_pass_end"] = max(fp_ends) if fp_ends else None
    res["first_pass_ok"] = fp_ok
    res["repeats"] = repeats
    res["repeat_mechs"] = sorted({r["mech"] for r in repeats})
    res["repeat_ctxs"] = sorted({r["ctx"] for r in repeats})
    res["repeat_extends"] = any(r["end"] is not None and res["first_pass_end"] is not None and r["end"] > res["first_pass_end"] for r in repeats)
    res["concurrent_dups"] = sorted(set(concurrent_dups))
    res["carried"] = sorted(set(carried))
    res["incomplete"] = sorted(set(incomplete))
    return res


def latest_span_from_api(hd: dict, required: dict) -> float | None:
    lat = hd.get("latest")
    if not isinstance(lat, list):
        return None
    starts, ends = [], []
    for cr in lat:
        if cr["name"] in required:
            integ = [i for i in required[cr["name"]] if i is not None]
            if integ and cr["app_id"] not in integ:
                continue
            if cr["started_at"]:
                starts.append(ts(cr["started_at"]))
            if cr["completed_at"]:
                ends.append(ts(cr["completed_at"]))
    return (max(ends) - min(starts)) if starts and ends else None


def budgets_at(commit: str = "53d05121") -> dict:
    import ast

    src = subprocess.run(["git", "show", f"{commit}:util/safe_merge.py"], capture_output=True, text=True, check=True).stdout
    tree = ast.parse(src)
    vals = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("REPO_TIMEOUTS", "TIMEOUT_CEILING", "DEFAULT_TIMEOUT"):
                vals[name] = ast.literal_eval(node.value)
    return vals


def load_all(offline: bool, repos: list[str] | None = None) -> dict:
    data = {}
    for repo in repos or REPOS:
        req = required_contexts(repo, offline)
        smp = sample(repo, offline)
        data[repo] = {"required": req, "sample": smp, "heads": {}}
        if not isinstance(smp, list):
            continue
        # the span is taken over the union of ruleset contexts (the stated definition)
        required = {k: v for k, v in req["union"].items()}
        for pr in smp:
            sha = pr["headRefOid"]
            data[repo]["heads"][pr["number"]] = head_data(repo, sha, required, offline)
    return data


def cmd_fetch(args) -> int:
    load_all(offline=False, repos=args.repos or None)
    print(f"fetch complete; REST calls this invocation: {_calls['n']}")
    return 0


def rule_verdict(budget: int, p: float | None, mx: float | None, ceiling: int) -> str:
    if p is None or mx is None:
        return "n/a"
    out = []
    out.append("OK>max" if budget > mx else "FAIL<=max")
    out.append("OK<=4p90" if budget <= 4 * p else "FAIL>4p90")
    if budget > ceiling:
        out.append("FAIL>ceiling")
    return " ".join(out)


def cmd_analyze(args) -> int:
    data = load_all(offline=True)
    b = budgets_at(args.commit)
    budgets, ceiling, default = b["REPO_TIMEOUTS"], b["TIMEOUT_CEILING"], b["DEFAULT_TIMEOUT"]
    evidence = {}
    print(f"budgets at {args.commit}: {budgets}  ceiling={ceiling} default={default}\n")
    summary_rows = []
    for repo in REPOS:
        req = data[repo]["required"]
        union, active = req["union"], req["active_main"]
        print(f"=== {repo}: rulesets={[(r['name'], r['enforcement'], r['include'], r['n_required']) for r in req['rulesets']]}")
        print(f"    union contexts={len(union)} active-on-main={len(active)} classic={req['classic'] or req['classic_error']}")
        if set(union) != set(active):
            print(f"    !! union vs active differ: only-union={sorted(set(union) - set(active))} only-active={sorted(set(active) - set(union))}")
        integ = sorted({str(i) for v in union.values() for i in v})
        print(f"    integration_ids in union: {integ}")
        smp = data[repo]["sample"]
        rows = []
        for pr in smp:
            hd = data[repo]["heads"][pr["number"]]
            if not isinstance(hd["check_runs"], list):
                rows.append({"pr": pr["number"], "error": hd["check_runs"]})
                continue
            ex = executions(repo, hd, union)
            c = classify(ex)
            c["pr"] = pr["number"]
            c["sha"] = pr["headRefOid"][:8]
            c["merged"] = pr["mergedAt"]
            c["raw_latest_api"] = latest_span_from_api(hd, union)
            c["raw"] = c["raw_latest_api"] if c.get("raw_latest_api") is not None else c.get("raw_latest_emulated")
            c["run_attempt_max"] = max([r.get("run_attempt") or 1 for r in hd["runs"]] if isinstance(hd["runs"], list) and hd["runs"] else [1])
            c["statuses_used"] = any(e["src"] == "status" for v in ex.values() for e in v)
            rows.append(c)
        meas = [r for r in rows if r.get("measurable")]
        prs = [r["pr"] for r in rows]
        print(f"    sample: n={len(rows)} PRs {min(prs)}..{max(prs)} measurable={len(meas)} partial-coverage={sum(1 for r in meas if r['n_present'] < r['n_required'])}")
        emul_mismatch = [(r["pr"], r["raw_latest_emulated"], r["raw_latest_api"]) for r in meas if r.get("raw_latest_api") is not None and abs((r["raw_latest_api"] or 0) - (r["raw_latest_emulated"] or 0)) > 0.5]
        if emul_mismatch:
            print(f"    !! latest-emulation mismatch vs API filter=latest: {emul_mismatch}")

        def stat(sel, key):
            xs = [r[key] for r in sel if r.get(key) is not None]
            return (p90(xs), max(xs) if xs else None, len(xs), max(sel, key=lambda r: r.get(key) or -1)["pr"] if sel else None)

        est = {}
        est["raw"] = stat(meas, "raw")
        est["envelope"] = stat(meas, "envelope")
        seq = [r for r in meas if not r["repeats"]]
        est["clean_noseqrepeat"] = stat(seq, "raw")
        noattempt = [r for r in meas if "rerun-attempt" not in r["repeat_mechs"]]
        est["clean_noattempt_raw"] = stat(noattempt, "raw")
        est["first_pass_all"] = stat(meas, "first_pass")
        fp_ok = [r for r in meas if r["first_pass_ok"]]
        est["first_pass_healthy"] = stat(fp_ok, "first_pass")
        seq_ok = [r for r in seq if r["first_pass_ok"]]
        est["clean_noseqrepeat_passing"] = stat(seq_ok, "raw")
        for k, (p, m, n, arg) in est.items():
            budget = budgets.get(repo, default)
            print(f"    {k:28s} p90={p!s:>7} max={m!s:>7} n={n:2d} argmax=#{arg}  budget={budget} -> {rule_verdict(budget, p, m, ceiling)}")
        summary_rows.append((repo, est))
        flagged = [r for r in meas if r["repeats"] or r["concurrent_dups"] or not r["first_pass_ok"]]
        for r in flagged:
            reps = "; ".join(f"{x['ctx']}[{x['mech']}/{x['event']}/att{x['attempt']}] {hms(x['start'])}->{hms(x['end'])} {x['conclusion']} (prior {x['prior_conclusion']} end {hms(x['prior_end'])})" for x in r["repeats"])
            print(f"      #{r['pr']} {r['sha']} raw={r['raw']} env={r['envelope']} fp={r['first_pass']} fp_ok={r['first_pass_ok']} attempt_max={r['run_attempt_max']} extends={r['repeat_extends']} conc={r['concurrent_dups']} :: {reps}")
        partial = [r for r in meas if r["n_present"] < r["n_required"]]
        for r in partial:
            print(f"      partial #{r['pr']} present {r['n_present']}/{r['n_required']} missing={r['missing']}")
        evidence[repo] = {
            "budget": budgets.get(repo, default),
            "required_union": union,
            "required_active_main": active,
            "rulesets": req["rulesets"],
            "estimators": {k: {"p90": v[0], "max": v[1], "n": v[2], "argmax_pr": v[3]} for k, v in est.items()},
            "heads": [{k: v for k, v in r.items() if k != "repeats"} | {"repeats": r.get("repeats", [])} for r in rows],
        }
        print()
    out = Path(__file__).with_name("lane_a2_evidence.json")
    out.write_text(json.dumps({"generated_at": _now(), "commit": args.commit, "budgets": budgets, "ceiling": ceiling, "repos": evidence}, indent=1, default=str))
    print(f"evidence written: {out}")
    return 0


def cmd_detail(args) -> int:
    repo, prn = args.repo, args.pr
    req = required_contexts(repo, offline=False)
    union = req["union"]
    smp = sample(repo, offline=True) or []
    pr = next((p for p in smp if p["number"] == prn), None)
    if pr is None:
        rc, out, err = _gh(["pr", "view", str(prn), "--repo", f"{OWNER}/{repo}", "--json", "number,headRefOid,mergedAt,createdAt,title"])
        pr = json.loads(out)
    sha = pr["headRefOid"]
    hd = head_data(repo, sha, union, offline=False)
    runs = hd["runs"] if isinstance(hd["runs"], list) else []
    print(f"{repo}#{prn} head {sha} merged {pr.get('mergedAt')} title={pr.get('title')!r}")
    print(f"required (union) = {len(union)}")
    print("workflow runs on head:")
    for r in sorted(runs, key=lambda r: r["created_at"]):
        print(f"  run {r['id']} {r['path']} event={r['event']} attempt={r['run_attempt']} created={r['created_at']} run_started={r['run_started_at']} updated={r['updated_at']} concl={r['conclusion']} actor={r['actor']}/{r['triggering_actor']}")
    jobs_by_id = {}
    if args.jobs:
        for r in runs:
            key = str(r["id"])
            jobs = hd["jobs_by_run"].get(key)
            if jobs is None:
                jobs = rest_paged(f"repos/{OWNER}/{repo}/actions/runs/{r['id']}/jobs?filter=all", "jobs", _trim_job)
            if isinstance(jobs, list):
                for j in jobs:
                    jobs_by_id[j["id"]] = j
    ex = executions(repo, hd, union)
    c = classify(ex)
    t0 = c.get("first_pass_start")
    print(f"raw_latest(API or emulated)={latest_span_from_api(hd, union) or c.get('raw_latest_emulated')} envelope={c.get('envelope')} first_pass={c.get('first_pass')} fp_ok={c.get('first_pass_ok')} missing={c.get('missing')}")
    print("per required context (t relative to first-pass start; q = job started - job created, from the Actions jobs API):")
    rows = []
    for ctx, execs in ex.items():
        for e in execs:
            j = jobs_by_id.get(e["id"])
            q = (ts(j["started_at"]) - ts(j["created_at"])) if j and j.get("started_at") and j.get("created_at") else None
            jc = (ts(j["created_at"]) - t0) if j and j.get("created_at") and t0 else None
            rows.append((e["start"] or 0, ctx, e, q, jc, j))
    for _start, ctx, e, q, jc, j in sorted(rows, key=lambda x: x[0]):
        rel_s = (e["start"] - t0) if (e["start"] and t0) else None
        rel_e = (e["end"] - t0) if (e["end"] and t0) else None
        dur = (e["end"] - e["start"]) if (e["end"] and e["start"]) else None
        jstart_delta = (ts(j["started_at"]) - e["start"]) if (j and j.get("started_at") and e["start"]) else None
        print(f"  {ctx[:58]:58s} {e['src'][:5]} run={e['run_id']} att={e['attempt']} ev={e['event']} start=+{rel_s} end=+{rel_e} dur={dur} {e['conclusion']} | job created=+{jc} queued={q} (job.started - cr.started={jstart_delta})")
    for x in c.get("repeats", []):
        print(f"  REPEAT {x}")
    return 0


def cmd_extra(args) -> int:
    """Measure PRs from the cached --limit 45 listing that are OUTSIDE the 30-PR sample (drift probe)."""
    repo = args.repo
    req = required_contexts(repo, offline=True)
    union = req["union"]
    smp = sample(repo, offline=True) or []
    wide = cached(f"SAMPLE-WIDE {repo} n=45", lambda: None, offline=True) or []
    inside = {p["number"] for p in smp}
    for pr in wide:
        if pr["number"] in inside and not args.all:
            continue
        hd = head_data(repo, pr["headRefOid"], union, offline=False)
        if not isinstance(hd["check_runs"], list):
            print(f"#{pr['number']}: {hd['check_runs']}")
            continue
        c = classify(executions(repo, hd, union))
        raw = latest_span_from_api(hd, union)
        raw = raw if raw is not None else c.get("raw_latest_emulated")
        tag = "IN-SAMPLE" if pr["number"] in inside else "outside"
        print(f"#{pr['number']} {tag} created {pr['createdAt']} merged {pr['mergedAt']} raw={raw} fp={c.get('first_pass')} fp_ok={c.get('first_pass_ok')} repeats={[(r['ctx'], r['mech']) for r in c.get('repeats', [])]} present={c.get('n_present')}/{c.get('n_required')}")
    print(f"REST calls this invocation: {_calls['n']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--repos", nargs="*", help="subset of repos (parallel prefetch); default all nine")
    a = sub.add_parser("analyze")
    a.add_argument("--commit", default="53d05121")
    d = sub.add_parser("detail")
    d.add_argument("--repo", required=True)
    d.add_argument("--pr", type=int, required=True)
    d.add_argument("--jobs", action="store_true", help="also fetch Actions jobs for every run on the head (queue analysis)")
    x = sub.add_parser("extra")
    x.add_argument("--repo", required=True)
    x.add_argument("--all", action="store_true", help="also print in-sample PRs")
    args = ap.parse_args()
    return {"fetch": cmd_fetch, "analyze": cmd_analyze, "detail": cmd_detail, "extra": cmd_extra}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
