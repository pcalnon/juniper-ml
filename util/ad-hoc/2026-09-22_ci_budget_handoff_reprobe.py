#!/usr/bin/env python3
"""
Re-probe every figure the CI-budget handoff's section 3 depends on, against live state, so its
re-evaluation quotes measurements rather than transcriptions.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation (handoff re-evaluation)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md
         notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md

Why a script: a worktree-isolated session's shell gate refuses any command line that names git
inside a pipeline, loop, redirect or `python -c` string, and every probe below either reads git
or loops over nine repos. Nothing here writes to any repository -- except `slack --fetch`, which
runs `git fetch origin main` in a sibling checkout whose `origin/main` disagrees with GitHub
(remote-tracking refs only; no working tree is touched).

Subcommands (each prints what it measured AND what could have made it read differently):

  structure  the whole-tree markdown structure screen over every tracked *.md at HEAD
  slack      planning margin = headroom - max(largest 30-day AGENTS.md growing commit, 2000),
             all nine repos; the rule is sourced at util/ad-hoc/2026-08-28_p5_cut.py (SLACK_FLOOR)
             and util/ad-hoc/README.md ("Size from `max`, NEVER from p90"). p90 is printed
             BESIDE max, never instead of it.
  spans      the v2 required-context CI span per repo against util/safe_merge.py REPO_TIMEOUTS:
             does each budget still clear its observed max and sit inside 4x p90?
  alarm      pr-budget-alarm.yml on each sibling's default branch, SLACK_WEBHOOK_URL presence,
             and whether any run has breached a threshold since the roll-out
  soak       every run of the `Markdown Structure (advisory soak)` job on juniper-ml pull
             requests since it was wired, how many actually EXAMINED a file, and every warning
  lockfile   the newest weekly lockfile PR: who opened it, and whether pull_request CI ran
  waiter     util/wait_for_checks.py DEFAULT_TIMEOUT against every per-repo budget

Usage:
    python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py all
    python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py slack --fetch
    python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py soak --since 2026-09-18T00:37:10Z

Exit: 0 every probe ran; 2 a probe could not measure (a vacuous result is refused, not scored).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess  # nosec B404 -- fixed-argv git / gh / python calls only; nothing is shell-interpolated
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

OWNER = "pcalnon"
ROOT = Path(__file__).resolve().parents[2]
ECOSYSTEM = Path("/home/pcalnon/Development/python/Juniper")
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
SIBLINGS = REPOS[1:]
# The soak job landed with ml#1955 (e7c191c1, 2026-09-18 00:37:10 UTC).
SOAK_WIRED = "2026-09-18T00:37:10Z"
SOAK_JOB = "Markdown Structure (advisory soak)"
LOCKFILE_TITLE = "chore(deps): refresh CI lockfiles"


class Unmeasurable(RuntimeError):
    """A probe could not produce a measurement; reported, never scored as clean."""


def run(argv: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)  # nosec B603
    if check and proc.returncode != 0:
        raise Unmeasurable(f"exit {proc.returncode}: {' '.join(argv)}\n{proc.stderr.strip()[-800:]}")
    return proc


def gh_json(path: str):
    return json.loads(run(["gh", "api", path]).stdout or "null")


def gh_pages(path: str, key: str | None = None, stop=None, limit_pages: int = 30) -> list:
    """Manual pagination -- gh 2.46.0 has no --slurp. ``stop(item)`` ends the walk early."""
    out: list = []
    sep = "&" if "?" in path else "?"
    for page in range(1, limit_pages + 1):
        data = gh_json(f"{path}{sep}per_page=100&page={page}")
        items = data.get(key, []) if key else data
        if not items:
            break
        for item in items:
            if stop is not None and stop(item):
                return out
            out.append(item)
        if len(items) < 100:
            break
    return out


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # register before exec: a @dataclass in a path-loaded module needs it
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------------------------
# structure
# --------------------------------------------------------------------------------------------
def probe_structure() -> dict:
    head = run(["git", "rev-parse", "--short=8", "HEAD"], cwd=ROOT).stdout.strip()
    files = run(["git", "ls-files", "-z"], cwd=ROOT).stdout.split("\0")
    md = [f for f in files if f.endswith(".md")]
    if not md:
        raise Unmeasurable("git ls-files returned no *.md paths")
    screen = ROOT / "util/ad-hoc/2026-09-05_markdown_structure_check.py"
    # argv directly, never xargs: xargs maps a child exit of 1-125 to 123 and would erase the
    # screen's own 1 (findings) vs 2 (refused to report) distinction.
    proc = run([sys.executable, str(screen), *md], cwd=ROOT, check=False)
    total = re.search(r"structural problems: (\d+)", proc.stdout)
    flagged = re.findall(r"^=== (.+) ===$", proc.stdout, re.MULTILINE)
    res = {
        "head": head,
        "tracked_md_paths": len(md),
        "exit": proc.returncode,
        "problems": int(total.group(1)) if total else None,
        "files_with_problems": flagged,
        "stderr_tail": proc.stderr.strip()[-600:],
    }
    print(f"[structure] HEAD {head}: {len(md)} tracked *.md paths examined by the whole-tree screen")
    print(f"            exit {proc.returncode} (0 clean / 1 findings / 2 refused); problems={res['problems']} across {len(flagged)} file(s)")
    for f in flagged:
        print(f"              {f}")
    if proc.returncode == 2:
        print(f"            REFUSED: {res['stderr_tail']}")
    print("            could it read differently? yes -- it exits 1 on any fence/H2/separator finding and 2 on an unreadable path")
    return res


# --------------------------------------------------------------------------------------------
# slack
# --------------------------------------------------------------------------------------------
def probe_slack(fetch: bool, days: int = 30) -> dict:
    p5 = load_module("p5_port_memory_budget", ROOT / "util/ad-hoc/2026-08-25_p5_port_memory_budget.py")
    cut = (ROOT / "util/ad-hoc/2026-08-28_p5_cut.py").read_text(encoding="utf-8")
    m = re.search(r"^SLACK_FLOOR = (\d+)$", cut, re.MULTILINE)
    if not m:
        raise Unmeasurable("SLACK_FLOOR not found in util/ad-hoc/2026-08-28_p5_cut.py -- the rule's source moved")
    floor = int(m.group(1))

    state = json.loads(run([sys.executable, str(ROOT / "util/ad-hoc/2026-08-26_p5_fleet_state.py"), "--json"], cwd=ROOT).stdout)
    by_repo = {row["repo"]: row for row in state}
    rows = []
    print(f"[slack] margin = headroom - max(largest {days}-day growing AGENTS.md commit, {floor}) -- p90 printed beside, never instead")
    print(f"        {'repo':<22} {'api main':<9} {'local':<9} {'headroom':>8} {'n_grew':>6} {'p90':>6} {'max':>6} {'slack':>6} {'margin':>7} {'p90-margin':>10}")
    for repo in REPOS:
        path = ECOSYSTEM / repo
        row = by_repo.get(repo)
        if row is None or not row.get("files"):
            raise Unmeasurable(f"{repo}: fleet_state returned no AGENTS.md ceiling row")
        agents = next(f for f in row["files"] if f["path"] == "AGENTS.md")
        api_main = row["main_sha"][:8]
        local = run(["git", "-C", str(path), "rev-parse", "--short=8", "origin/main"], check=False).stdout.strip()
        if local != api_main and fetch:
            run(["git", "-C", str(path), "fetch", "--quiet", "origin", "main"])
            local = run(["git", "-C", str(path), "rev-parse", "--short=8", "origin/main"]).stdout.strip()
        stale = local != api_main
        st = p5.growth_stats(path, days, "origin/main")
        mx = (st or {}).get("max") or 0
        p90 = (st or {}).get("p90") or 0
        grew = (st or {}).get("grew", 0)
        slack = max(mx, floor)
        margin = agents["headroom"] - slack
        p90_margin = agents["headroom"] - max(p90, floor)
        rows.append(
            {
                "repo": repo,
                "api_main": api_main,
                "local_origin_main": local,
                "stale_local": stale,
                "ceiling": agents["ceiling_chars"],
                "chars": agents["chars"],
                "headroom": agents["headroom"],
                "grew": grew,
                "p90": p90,
                "max": mx,
                "slack": slack,
                "margin": margin,
                "p90_margin": p90_margin,
                "memory_budget_required": row.get("memory_budget_required"),
            }
        )
        flag = "  STALE-LOCAL (growth read from an old origin/main)" if stale else ""
        print(f"        {repo:<22} {api_main:<9} {local:<9} {agents['headroom']:>8} {grew:>6} {p90:>6} {mx:>6} {slack:>6} {margin:>+7} {p90_margin:>+10}{flag}")
    neg = [r["repo"] for r in rows if r["margin"] < 0]
    zero = [r["repo"] for r in rows if r["margin"] == 0]
    print(f"        negative: {len(neg)} {neg}; exactly zero: {zero}")
    print("        could it read differently? yes -- headroom is live from the GitHub API; growth is local git history,")
    print("        so a STALE-LOCAL row measures an old window (re-run with --fetch).")
    return {"floor": floor, "days": days, "rows": rows, "negative": neg, "zero": zero}


# --------------------------------------------------------------------------------------------
# spans
# --------------------------------------------------------------------------------------------
def probe_spans(n: int = 30) -> dict:
    sm = load_module("safe_merge_probe", ROOT / "util/safe_merge.py")
    v2 = ROOT / "util/ad-hoc/2026-09-08_measure_required_check_span_v2.py"
    rows = []
    print(f"[spans] v2 required-context span, n={n} merged heads per repo, vs util/safe_merge.py REPO_TIMEOUTS")
    print(f"        {'repo':<22} {'meas':>4} {'unmeas':>6} {'p90':>6} {'max':>6} {'budget':>6} {'4xp90':>6}  verdict")
    for repo in REPOS:
        proc = run([sys.executable, str(v2), "--repo", repo, "-n", str(n)], cwd=ROOT, check=False)
        out = proc.stdout
        head = re.search(r"(\d+) heads measured, (\d+) unmeasurable", out)
        blk = out.split("v1 UNFILTERED")[0]
        p90 = re.search(r"p90\s+(\d+) s", blk)
        mx = re.search(r"max\s+(\d+) s", blk)
        budget = sm.timeout_for(repo)
        if proc.returncode != 0 or not (head and p90 and mx):
            rows.append({"repo": repo, "exit": proc.returncode, "verdict": "UNMEASURABLE"})
            print(f"        {repo:<22} UNMEASURABLE (exit {proc.returncode}) {proc.stderr.strip()[-200:]}")
            continue
        p90v, mxv = int(p90.group(1)), int(mx.group(1))
        clears = budget > mxv
        inside = budget <= 4 * p90v
        verdict = "OK" if clears and inside else ("BELOW OBSERVED MAX" if not clears else "ABOVE 4x p90")
        if repo == "juniper-cascor-client" and clears and not inside:
            verdict = "ABOVE 4x p90 -- excluded from the pin by owner ruling 2026-09-15"
        rows.append(
            {
                "repo": repo,
                "measured": int(head.group(1)),
                "unmeasurable": int(head.group(2)),
                "p90": p90v,
                "max": mxv,
                "budget": budget,
                "four_p90": 4 * p90v,
                "clears_max": clears,
                "inside_4x_p90": inside,
                "verdict": verdict,
            }
        )
        print(f"        {repo:<22} {head.group(1):>4} {head.group(2):>6} {p90v:>6} {mxv:>6} {budget:>6} {4 * p90v:>6}  {verdict}")
    print(f"        TIMEOUT_CEILING={sm.TIMEOUT_CEILING} DEFAULT_TIMEOUT={sm.DEFAULT_TIMEOUT}")
    print("        could it read differently? yes -- a budget at or below the observed max prints BELOW OBSERVED MAX;")
    print("        note the window is the last n MERGED heads, so it moves with every merge.")
    return {"n": n, "rows": rows}


# --------------------------------------------------------------------------------------------
# rerun-split
# --------------------------------------------------------------------------------------------
def _ts(s: str | None):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def probe_rerun_split(n: int = 30) -> dict:
    """v2's span, split by whether the head carried a RE-RUN.

    v2 reads `check-runs` with the API's default `filter=latest`, so a re-run REPLACES the
    first attempt and the span runs from the original start to the re-run's finish.
    canopy#653 reads 33,299 s that way: its first pass FAILED at 10:08 UTC 2026-09-22 and one
    job was re-run at 19:01. `safe_merge` would have reported the failure at 10:08, and a
    later invocation starts a fresh wait, so a re-run tail never counts against a budget.

    A head is a RE-RUN head when some required context has two check-runs where one STARTED
    after the other COMPLETED (sequential). Overlapping same-name check-runs are parallel jobs
    from different workflows, not re-runs. Spans are otherwise computed exactly as v2 does --
    min(start) to max(end) over the required contexts -- but over `filter=all`, so the
    clean-head figures are v2's own quantity with the re-run heads set aside, not a new one.
    """
    v2 = load_module("span_v2_probe", ROOT / "util/ad-hoc/2026-09-08_measure_required_check_span_v2.py")
    sm = load_module("safe_merge_probe3", ROOT / "util/safe_merge.py")
    out = []
    print(f"[rerun-split] v2 span over the last {n} merged heads, CLEAN heads vs heads carrying a sequential re-run")
    print(f"        {'repo':<22} {'clean':>5} {'rerun':>5} {'unmeas':>6} {'p90':>6} {'max':>6} {'budget':>6} {'4xp90':>6}  verdict (clean heads)   worst re-run heads")
    for repo in REPOS:
        slug = f"{OWNER}/{repo}"
        required = v2.required_contexts(slug)
        if not required:
            out.append({"repo": repo, "verdict": "UNMEASURABLE (no required contexts)"})
            print(f"        {repo:<22} UNMEASURABLE -- no required contexts read")
            continue
        prs = json.loads(run(["gh", "pr", "list", "--repo", slug, "--state", "merged", "--limit", str(n), "--json", "number,headRefOid"]).stdout)
        clean, rerun, unmeas = [], [], []
        for pr in prs:
            sha = pr["headRefOid"]
            crs = gh_pages(f"repos/{slug}/commits/{sha}/check-runs?filter=all", key="check_runs")
            runs_ = [(c["name"], _ts(c["started_at"]), _ts(c["completed_at"]), c.get("conclusion")) for c in crs if c["name"] in required]
            sts = gh_pages(f"repos/{slug}/commits/{sha}/statuses")
            stat_rows = [(s["context"], _ts(s["created_at"]), _ts(s["updated_at"]), s.get("state")) for s in sts if s["context"] in required]
            rows = runs_ + stat_rows
            starts = [r[1] for r in rows if r[1]]
            ends = [r[2] for r in rows if r[2]]
            if not starts or not ends:
                unmeas.append(pr["number"])
                continue
            span = (max(ends) - min(starts)).total_seconds()
            by_name: dict = {}
            for name, st, en, concl in runs_:
                if st and en:
                    by_name.setdefault(name, []).append((st, en, concl))
            sequential = []
            for name, items in by_name.items():
                items.sort()
                for i, (_s1, e1, c1) in enumerate(items):
                    for s2, _e2, c2 in items[i + 1 :]:
                        if s2 >= e1:
                            sequential.append({"context": name, "first": c1, "later": c2, "gap_s": round((s2 - e1).total_seconds())})
            rec = {"pr": pr["number"], "span": round(span), "reruns": sequential[:3]}
            (rerun if sequential else clean).append(rec)
        spans = sorted(r["span"] for r in clean)
        budget = sm.timeout_for(repo)
        if not spans:
            out.append({"repo": repo, "clean": 0, "rerun": len(rerun), "verdict": "UNMEASURABLE (no clean head)"})
            print(f"        {repo:<22} {0:>5} {len(rerun):>5} {len(unmeas):>6}  UNMEASURABLE -- no clean head")
            continue
        p90v, mxv = v2.p90(spans), spans[-1]
        clears, inside = budget > mxv, budget <= 4 * p90v
        verdict = "OK" if clears and inside else ("BELOW CLEAN MAX" if not clears else "ABOVE 4x p90")
        worst = sorted(rerun, key=lambda r: -r["span"])[:2]
        out.append(
            {
                "repo": repo,
                "clean": len(clean),
                "rerun": len(rerun),
                "unmeasurable": unmeas,
                "p90": round(p90v),
                "max": mxv,
                "max_pr": max(clean, key=lambda r: r["span"])["pr"],
                "budget": budget,
                "four_p90": round(4 * p90v),
                "verdict": verdict,
                "rerun_heads": sorted(rerun, key=lambda r: -r["span"]),
            }
        )
        worst_s = "; ".join(f"#{w['pr']} {w['span']}s ({w['reruns'][0]['context']}: {w['reruns'][0]['first']}->{w['reruns'][0]['later']}, gap {w['reruns'][0]['gap_s']}s)" for w in worst)
        print(f"        {repo:<22} {len(clean):>5} {len(rerun):>5} {len(unmeas):>6} {p90v:>6.0f} {mxv:>6} {budget:>6} {4 * p90v:>6.0f}  {verdict:<22} {worst_s}")
    print("        could it read differently? yes -- a clean-head max at or above the budget prints BELOW CLEAN MAX. The split can")
    print("        MISCLASSIFY a same-name job that legitimately runs twice in sequence within one pass as a re-run; check the")
    print("        named contexts before trusting a clean verdict that depends on a head it set aside.")
    return {"n": n, "rows": out}


# --------------------------------------------------------------------------------------------
# alarm
# --------------------------------------------------------------------------------------------
def probe_alarm() -> dict:
    rows = []
    print(f"[alarm] pr-budget-alarm.yml on each repo's default branch, SLACK_WEBHOOK_URL, runs since roll-out")
    for repo in REPOS:
        meta = gh_json(f"repos/{OWNER}/{repo}")
        branch = meta["default_branch"]
        wf = run(["gh", "api", f"repos/{OWNER}/{repo}/contents/.github/workflows/pr-budget-alarm.yml?ref={branch}", "--jq", ".sha"], check=False)
        present = wf.returncode == 0
        secrets = run(["gh", "secret", "list", "--repo", f"{OWNER}/{repo}"], check=False)
        secret_names = [line.split("\t")[0] for line in secrets.stdout.splitlines() if line.strip()]
        has_webhook = "SLACK_WEBHOOK_URL" in secret_names if secrets.returncode == 0 else None
        runs = []
        breaches = []
        notices = 0
        if present:
            data = gh_json(f"repos/{OWNER}/{repo}/actions/workflows/pr-budget-alarm.yml/runs?per_page=50")
            for r in data.get("workflow_runs", []):
                runs.append({"id": r["id"], "created": r["created_at"], "event": r["event"], "conclusion": r["conclusion"]})
            # A breach with no webhook surfaces ONLY as a ::warning:: annotation on the job. The
            # runner also attaches `notice`-level annotations (e.g. the ubuntu-latest migration
            # notice) to every job, so only warning/failure levels can be a breach or a query
            # failure; counting every annotation reads runner chatter as five breaches a repo.
            for r in runs[:10]:
                jobs = gh_json(f"repos/{OWNER}/{repo}/actions/runs/{r['id']}/jobs").get("jobs", [])
                for j in jobs:
                    cr = gh_json(f"repos/{OWNER}/{repo}/check-runs/{j['id']}")
                    if (cr.get("output") or {}).get("annotations_count", 0):
                        for a in gh_json(f"repos/{OWNER}/{repo}/check-runs/{j['id']}/annotations"):
                            if a.get("annotation_level") not in ("warning", "failure"):
                                notices += 1
                                continue
                            breaches.append({"run": r["id"], "created": r["created"], "level": a.get("annotation_level"), "title": a.get("title"), "message": (a.get("message") or "")[:200]})
        conclusions: dict = {}
        for r in runs:
            conclusions[r["conclusion"]] = conclusions.get(r["conclusion"], 0) + 1
        rows.append(
            {
                "repo": repo,
                "default_branch": branch,
                "alarm_present": present,
                "slack_webhook_secret": has_webhook,
                "runs_listed": len(runs),
                "first_run": runs[-1]["created"] if runs else None,
                "last_run": runs[0]["created"] if runs else None,
                "conclusions": conclusions,
                "warnings_last10": breaches,
                "notices_last10": notices,
            }
        )
        hook = {True: "yes", False: "NO", None: "unreadable"}[has_webhook]
        print(
            f"        {repo:<22} alarm={'present' if present else 'MISSING':<8} webhook={hook:<10} runs={len(runs):<3} "
            f"first={runs[-1]['created'][:10] if runs else '-'} last={runs[0]['created'][:10] if runs else '-'} {conclusions} "
            f"warnings(last10)={len(breaches)} notices(last10)={notices}"
        )
        for b in breaches:
            print(f"            {b['created']} {b['level']}: {b['title']} -- {b['message']}")
    print("        could it read differently? yes -- a missing file, a missing secret, or any annotation prints as such.")
    return {"rows": rows}


# --------------------------------------------------------------------------------------------
# soak
# --------------------------------------------------------------------------------------------
def probe_soak(since: str) -> dict:
    cutoff = datetime.fromisoformat(since.replace("Z", "+00:00"))
    runs = gh_pages(
        f"repos/{OWNER}/juniper-ml/actions/workflows/ci.yml/runs?event=pull_request&created=%3E%3D{urllib.parse.quote(since)}",
        key="workflow_runs",
    )
    heads: dict = {}
    for r in runs:
        heads.setdefault(r["head_sha"], {"runs": [], "prs": set()})
        heads[r["head_sha"]]["runs"].append(r["id"])
        for pr in r.get("pull_requests") or []:
            heads[r["head_sha"]]["prs"].add(pr["number"])
    name = urllib.parse.quote(SOAK_JOB)
    checks = []
    for sha, info in heads.items():
        data = gh_json(f"repos/{OWNER}/juniper-ml/commits/{sha}/check-runs?check_name={name}&filter=all&per_page=100")
        for cr in data.get("check_runs", []):
            started = cr.get("started_at")
            if started and datetime.fromisoformat(started.replace("Z", "+00:00")) < cutoff:
                continue
            log = run(["gh", "api", f"repos/{OWNER}/juniper-ml/actions/jobs/{cr['id']}/logs"], check=False)
            # The job log ECHOES the step's script text before running it, so every phrase the
            # script prints is also present unexpanded. Match only the EXPANDED forms -- a digit
            # count, a hex SHA, the screen's own `[ OK ]`/`[FAIL]` verdict lines -- or a bare
            # phrase match reports every run as "nothing to examine".
            examined = re.search(r"examining (\d+) changed markdown file", log.stdout)
            nothing = re.search(r"no markdown changed against [0-9a-f]{7,40} -- nothing to examine", log.stdout) is not None
            verdicts = {tag: len(re.findall(rf"\[{re.escape(tag)}\] ", log.stdout)) for tag in (" OK ", "FAIL", "NEW ", "ERR ")}
            # The screen's own finding lines: `[FAIL] <path>` then indented detail lines. Strip the
            # runner's ISO timestamp prefix so the text is comparable across runs.
            fails = []
            lines = [re.sub(r"^\S+Z ", "", ln) for ln in log.stdout.splitlines()]
            for i, ln in enumerate(lines):
                m = re.match(r"\[FAIL\] (.+)$", ln)
                if m:
                    detail = []
                    for nxt in lines[i + 1 : i + 12]:
                        if not nxt.startswith("   "):
                            break
                        detail.append(nxt.strip())
                    fails.append({"path": m.group(1).strip(), "detail": detail})
            ann = []
            if (cr.get("output") or {}).get("annotations_count", 0):
                for a in gh_json(f"repos/{OWNER}/juniper-ml/check-runs/{cr['id']}/annotations"):
                    # Only the soak's OWN warning is a finding. The runner attaches `notice`-level
                    # annotations (the ubuntu-latest migration notice) to every job, and a
                    # concurrency-cancelled job carries a `failure` annotation that is about the
                    # runner, not the markdown; counting either reads chatter as findings.
                    if a.get("annotation_level") not in ("warning", "failure") or not (a.get("title") or "").startswith("Markdown structure C1-C4"):
                        continue
                    ann.append({"level": a.get("annotation_level"), "title": a.get("title"), "message": (a.get("message") or "")[:300]})
            prs_for_head = sorted(info["prs"])
            if not prs_for_head and (ann or fails):
                # A workflow run's `pull_requests` is often empty once the PR has merged; ask the commit.
                pulled = gh_json(f"repos/{OWNER}/juniper-ml/commits/{sha}/pulls")
                prs_for_head = sorted(p["number"] for p in pulled or [])
            # The screen's exit code reaches the API only through the annotation title, which
            # the job emits on a NON-zero exit; an examined run with no annotation exited 0.
            rc = next((re.search(r"exit (\d)", a["title"] or "") for a in ann if re.search(r"exit (\d)", a["title"] or "")), None)
            checks.append(
                {
                    "head": sha[:8],
                    "prs": prs_for_head,
                    "check_run": cr["id"],
                    "conclusion": cr.get("conclusion"),
                    "log_read": log.returncode == 0,
                    "examined_files": int(examined.group(1)) if examined else 0,
                    "nothing_to_examine": nothing,
                    "verdict_lines": verdicts,
                    "screen_exit": int(rc.group(1)) if rc else (0 if examined else None),
                    "fails": fails,
                    "annotations": ann,
                }
            )
    ran = len(checks)
    unread = sum(1 for c in checks if not c["log_read"])
    examined = [c for c in checks if c["examined_files"] > 0]
    idle = [c for c in checks if c["nothing_to_examine"]]
    unclassified = [c for c in checks if c["log_read"] and not c["examined_files"] and not c["nothing_to_examine"]]
    warned = [c for c in checks if c["annotations"]]
    prs_examined = sorted({p for c in examined for p in c["prs"]})
    fail_lines = sum(c["verdict_lines"]["FAIL"] for c in examined)
    print(f"[soak] `{SOAK_JOB}` runs on juniper-ml pull_request CI since {since}")
    print(f"       ci.yml pull_request runs listed: {len(runs)} over {len(heads)} head SHAs; soak check-runs found: {ran}")
    print(f"       logs unreadable: {unread}; no markdown changed: {len(idle)}; UNCLASSIFIED (neither): {len(unclassified)}")
    print(f"       runs that EXAMINED >=1 file: {len(examined)} (PRs {prs_examined}); files examined in total: {sum(c['examined_files'] for c in examined)}; [FAIL] lines: {fail_lines}")
    for c in unclassified:
        print(f"         unclassified: PR {c['prs']} head {c['head']} check-run {c['check_run']} conclusion={c['conclusion']}")
    print(f"       runs with the soak's own warning annotation: {len(warned)}")
    # Group by (path, finding text): one PR pushed ten times is ten runs but ONE finding.
    distinct: dict = {}
    for c in checks:
        for f in c["fails"]:
            key = (f["path"], tuple(f["detail"]))
            distinct.setdefault(key, {"prs": set(), "runs": 0})
            distinct[key]["prs"].update(c["prs"])
            distinct[key]["runs"] += 1
    print(f"       DISTINCT (path, finding) pairs behind the [FAIL] lines: {len(distinct)}")
    for (path, detail), v in sorted(distinct.items(), key=lambda kv: -kv[1]["runs"]):
        print(f"         {path}  runs={v['runs']} PRs={sorted(v['prs'])}")
        for d in detail:
            print(f"             {d}")
    print("       could it read differently? yes -- any non-zero screen exit emits a ::warning:: annotation, counted here;")
    print("       a run with no markdown change examines nothing and is NOT evidence either way.")
    if ran == 0:
        raise Unmeasurable("no soak check-runs found -- refusing to report a clean soak")
    return {
        "since": since,
        "ci_runs": len(runs),
        "heads": len(heads),
        "soak_runs": ran,
        "logs_unreadable": unread,
        "idle_runs": len(idle),
        "unclassified_runs": len(unclassified),
        "examined_runs": len(examined),
        "prs_examined": prs_examined,
        "files_examined": sum(c["examined_files"] for c in examined),
        "fail_lines": fail_lines,
        "warned": len(warned),
        "distinct_findings": [{"path": p, "detail": list(d), "runs": v["runs"], "prs": sorted(v["prs"])} for (p, d), v in distinct.items()],
        "checks": checks,
    }


# --------------------------------------------------------------------------------------------
# lockfile
# --------------------------------------------------------------------------------------------
def probe_lockfile() -> dict:
    prs = json.loads(
        run(["gh", "pr", "list", "--repo", f"{OWNER}/juniper-ml", "--state", "all", "--search", f'"{LOCKFILE_TITLE}" in:title', "--limit", "5", "--json", "number,author,createdAt,state,headRefOid,mergedAt"]).stdout
    )
    if not prs:
        raise Unmeasurable("no lockfile PR found")
    rows = []
    print("[lockfile] newest weekly lockfile PRs: who opened each, and what pull_request CI the OPENING commit got, by actor")
    for pr in sorted(prs, key=lambda p: p["createdAt"], reverse=True):
        # Read the OPENING commit, not the final head. A later human push (update-branch, a
        # merge from main, a close/reopen) triggers CI as that human and replaces the head,
        # so runs on the final head say nothing about whether the WORKFLOW's own PR triggered
        # CI. The first draft of this probe read the final head and would have credited the
        # pre-fix PRs with CI a person had forced.
        commits = gh_json(f"repos/{OWNER}/juniper-ml/pulls/{pr['number']}/commits?per_page=100")
        opening = commits[0]["sha"] if commits else pr["headRefOid"]
        wr = gh_json(f"repos/{OWNER}/juniper-ml/actions/runs?head_sha={opening}&per_page=50").get("workflow_runs", [])
        at_open = [r for r in wr if r["event"] == "pull_request"]
        actors = sorted({r["actor"]["login"] for r in at_open})
        # The run LIST shows the LATEST attempt. A GITHUB_TOKEN-opened PR's runs are CREATED --
        # not suppressed -- and parked at `action_required` on attempt 1 until a maintainer
        # approves; a later approve/re-run overwrites the listed conclusion with attempt 2's.
        # And the CONCLUSION is not a discriminator either: closing the PR flips a parked run
        # to `failure` with ZERO jobs (juniper-ml#1806, 2026-09-07 13:59:38). What separates a
        # run that executed from one that never did is whether attempt 1 ran any JOB.
        first = []
        for r in at_open:
            a1 = gh_json(f"repos/{OWNER}/juniper-ml/actions/runs/{r['id']}/attempts/1")
            jobs = gh_json(f"repos/{OWNER}/juniper-ml/actions/runs/{r['id']}/attempts/1/jobs").get("total_count", 0)
            first.append({"name": r["name"], "actor": a1["actor"]["login"], "attempt1": a1["conclusion"], "attempt1_jobs": jobs, "attempts": r["run_attempt"]})
        executed = [f for f in first if f["attempt1_jobs"] > 0]
        parked = [f for f in first if f["attempt1_jobs"] == 0]
        rows.append(
            {
                "number": pr["number"],
                "created": pr["createdAt"],
                "author": pr["author"]["login"],
                "state": pr["state"],
                "opening_commit": opening[:8],
                "commits": len(commits),
                "run_actors": actors,
                "attempt1": first,
                "executed_at_open": len(executed),
                "parked_action_required": len(parked),
            }
        )
        by_actor: dict = {}
        for f in first:
            key = (f["actor"], "ran" if f["attempt1_jobs"] else "0 jobs")
            by_actor[key] = by_actor.get(key, 0) + 1
        print(
            f"           #{pr['number']} {pr['createdAt'][:16]} by {pr['author']['login']:<26} opening {opening[:8]}: "
            f"attempt 1 ran jobs in {len(executed)}/{len(first)} run(s); by (actor, outcome): {by_actor}"
        )
    print("           could it read differently? yes -- a GITHUB_TOKEN-opened PR's own runs run ZERO jobs on attempt 1;")
    print("           only a run that ran jobs on attempt 1 under the App actor proves the arm.")
    return {"rows": rows}


# --------------------------------------------------------------------------------------------
# settings
# --------------------------------------------------------------------------------------------
def probe_settings() -> dict:
    """The merge-lane settings the handoff's MERGING block depends on, per repo, from the API."""
    rows = []
    print("[settings] allow_update_branch / allow_auto_merge per repo (the handoff: update_branch FALSE fleet-wide)")
    for repo in REPOS:
        meta = gh_json(f"repos/{OWNER}/{repo}")
        row = {"repo": repo, "allow_update_branch": meta.get("allow_update_branch"), "allow_auto_merge": meta.get("allow_auto_merge")}
        rows.append(row)
        print(f"           {repo:<22} allow_update_branch={row['allow_update_branch']!s:<5} allow_auto_merge={row['allow_auto_merge']}")
    if any(r["allow_update_branch"] is None for r in rows):
        raise Unmeasurable("allow_update_branch not readable on every repo (needs admin scope) -- refusing to report a partial census")
    return {"rows": rows}


# --------------------------------------------------------------------------------------------
# waiter
# --------------------------------------------------------------------------------------------
def probe_waiter() -> dict:
    sm = load_module("safe_merge_probe2", ROOT / "util/safe_merge.py")
    text = (ROOT / "util/wait_for_checks.py").read_text(encoding="utf-8")
    m = re.search(r"^DEFAULT_TIMEOUT = (\d+)", text, re.MULTILINE)
    if not m:
        raise Unmeasurable("DEFAULT_TIMEOUT not found in util/wait_for_checks.py")
    default = int(m.group(1))
    above = {r: sm.timeout_for(r) for r in REPOS if sm.timeout_for(r) > default}
    print(f"[waiter] util/wait_for_checks.py DEFAULT_TIMEOUT={default}; per-repo budgets above it: {len(above)} of {len(REPOS)} {above}")
    return {"default": default, "above": above}


PROBES = ["structure", "slack", "spans", "rerun-split", "alarm", "soak", "lockfile", "settings", "waiter"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("probe", choices=PROBES + ["all"])
    ap.add_argument("--fetch", action="store_true", help="slack: fetch a sibling whose origin/main disagrees with GitHub")
    ap.add_argument("--since", default=SOAK_WIRED, help=f"soak: ISO-8601 UTC lower bound (default {SOAK_WIRED}, when the job was wired)")
    ap.add_argument("-n", type=int, default=30, help="spans: merged heads per repo (default 30)")
    ap.add_argument("--json", type=Path, help="also write every result to this JSON file")
    args = ap.parse_args(argv)

    chosen = PROBES if args.probe == "all" else [args.probe]
    results: dict = {"measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    failed = []
    for name in chosen:
        try:
            if name == "structure":
                results[name] = probe_structure()
            elif name == "slack":
                results[name] = probe_slack(args.fetch)
            elif name == "spans":
                results[name] = probe_spans(args.n)
            elif name == "rerun-split":
                results[name] = probe_rerun_split(args.n)
            elif name == "alarm":
                results[name] = probe_alarm()
            elif name == "soak":
                results[name] = probe_soak(args.since)
            elif name == "lockfile":
                results[name] = probe_lockfile()
            elif name == "settings":
                results[name] = probe_settings()
            elif name == "waiter":
                results[name] = probe_waiter()
        except Unmeasurable as exc:
            failed.append(name)
            results[name] = {"unmeasurable": str(exc)}
            print(f"[{name}] UNMEASURABLE: {exc}", file=sys.stderr)
        print()
    if args.json:
        args.json.write_text(json.dumps(results, indent=2, default=list), encoding="utf-8")
        print(f"wrote {args.json}")
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
