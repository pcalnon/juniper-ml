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
inside a pipeline, loop, redirect or `python -c` string -- and also a loop that runs `gh` over a
variable -- and every probe below either reads git or loops over nine repos. Nothing here writes
to any repository -- except `slack --fetch`, which runs `git fetch origin main` in a sibling
checkout whose `origin/main` disagrees with GitHub (remote-tracking refs only; no working tree is
touched).

Subcommands. Each prints what it measured AND what could have made it read differently:

  structure   the whole-tree markdown structure screen over every tracked *.md at HEAD
  slack       planning margin = headroom - max(largest 30-day AGENTS.md growing commit, 2000),
              all nine repos; the rule is sourced at util/ad-hoc/2026-08-28_p5_cut.py (SLACK_FLOOR)
              and util/ad-hoc/README.md ("Size from `max`, NEVER from p90"). p90 is printed
              BESIDE max, never instead of it.
  spans       raw v2 (util/ad-hoc/2026-09-08_measure_required_check_span_v2.py) per repo against
              util/safe_merge.py REPO_TIMEOUTS -- kept for comparison; RE-RUN TAILS INFLATE IT
  first-pass  THE SIZING INSTRUMENT: each head's FIRST PASS (the first execution of every
              required context), over healthy heads, against REPO_TIMEOUTS
  alarm       pr-budget-alarm.yml on each repo's default branch, SLACK_WEBHOOK_URL presence, and
              every run's breach level, read from whether its Slack step ran
  soak        every run of `Markdown Structure (advisory soak)` on juniper-ml pull requests since
              it was wired: what it examined, what it flagged, and on which PRs
  lockfile    EVERY PR the lockfile workflow opened, and what pull_request CI each one got
  settings    allow_update_branch / allow_auto_merge per repo
  waiter      what util/wait_for_checks.py waits when --timeout is omitted, per repo

Usage (from the juniper-ml root; S is any existing directory, e.g. the session scratchpad):
    python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py all --json "$S/reprobe.json"
    python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py slack --fetch
    python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py soak --since 2026-09-18T00:37:10Z

`all` makes roughly 2,500 REST calls and takes several minutes; `first-pass`, `spans`, `soak` and
`alarm` are the slow ones. The token's REST budget is shared with every other session.

Exit: 0 every probe measured every row; 2 at least one probe or row could not be measured (a
vacuous result is refused, never scored -- the UNMEASURABLE line names it); 1 is a crash, not a
measurement.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess  # nosec B404 -- fixed-argv git / gh / python calls only; nothing is shell-interpolated
import sys
import time
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
# The soak job landed with ml#1955 (e7c191c1, 2026-09-18 00:37:10 UTC).
SOAK_WIRED = "2026-09-18T00:37:10Z"
SOAK_JOB = "Markdown Structure (advisory soak)"
LOCKFILE_BRANCH = "chore/lockfile-update"
ALARM_SLACK_STEP = "Slack notification on breach"
PASSED = {"success", "skipped", "neutral"}


class Unmeasurable(RuntimeError):
    """A probe could not produce a measurement; reported, never scored as clean."""


def run(argv: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)  # nosec B603
    if check and proc.returncode != 0:
        raise Unmeasurable(f"exit {proc.returncode}: {' '.join(argv)}\n{proc.stderr.strip()[-800:]}")
    return proc


def gh_json(path: str, attempts: int = 3):
    """One API read, retried a bounded number of times.

    A single truncated response ("unexpected end of JSON input") aborted a 600-call soak census
    on 2026-09-22. Delay-only: a failure that persists across every attempt still raises, so a
    broken probe is never scored as clean.
    """
    for attempt in range(1, attempts + 1):
        try:
            return json.loads(run(["gh", "api", path]).stdout or "null")
        except (Unmeasurable, json.JSONDecodeError) as exc:
            if attempt == attempts:
                raise Unmeasurable(f"{path}: {exc}") from exc
            time.sleep(2 * attempt)


def gh_pages(path: str, key: str | None = None, limit_pages: int = 30) -> list:
    """Manual pagination -- gh 2.46.0 has no --slurp."""
    out: list = []
    sep = "&" if "?" in path else "?"
    for page in range(1, limit_pages + 1):
        data = gh_json(f"{path}{sep}per_page=100&page={page}")
        items = data.get(key, []) if key else data
        if not items:
            break
        out.extend(items)
        if len(items) < 100:
            break
    return out


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # register before exec: a @dataclass in a path-loaded module needs it
    spec.loader.exec_module(mod)
    return mod


def _ts(s: str | None):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


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
    examined = re.search(r"examined (\d+) of (\d+) path", proc.stdout)
    flagged = re.findall(r"^=== (.+) ===$", proc.stdout, re.MULTILINE)
    res = {
        "head": head,
        "tracked_md_paths": len(md),
        "examined": examined.group(0) if examined else None,
        "exit": proc.returncode,
        "problems": int(total.group(1)) if total else None,
        "files_with_problems": flagged,
        "stderr_tail": proc.stderr.strip()[-600:],
    }
    print(f"[structure] HEAD {head}: {len(md)} tracked *.md paths passed to the whole-tree screen ({res['examined']}; symlink aliases counted once)")
    print(f"            exit {proc.returncode} (0 clean / 1 findings / 2 refused); problems={res['problems']} across {len(flagged)} file(s)")
    for f in flagged:
        print(f"              {f}")
    if proc.returncode == 2:
        print(f"            REFUSED: {res['stderr_tail']}")
    print("            could it read differently? yes -- it exits 1 on any fence/H2/separator finding and 2 on an unreadable path;")
    print("            run on bcc89c45:docs/REFERENCE.md (the ml#1746 damage) it reports 2 swallowed H2s and exits 1.")
    if proc.returncode == 2 or res["problems"] is None:
        raise Unmeasurable(f"structure screen refused to report (exit {proc.returncode})")
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
    measured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[slack] margin = headroom - max(largest {days}-day growing AGENTS.md commit, {floor}) -- p90 printed beside, never instead")
    print(f"        measured {measured_at}; git reads a date-only --since at the CURRENT time of day, so the window moves within a day")
    print(f"        {'repo':<22} {'api main':<9} {'local':<9} {'headroom':>8} {'commits':>7} {'grew':>4} {'start->end':>15} {'p90':>6} {'max':>6} {'slack':>6} {'margin':>7} {'p90-margin':>10}")
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
        st = p5.growth_stats(path, days, "origin/main") or {}
        mx = st.get("max") or 0
        p90 = st.get("p90") or 0
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
                "commits": st.get("commits", 0),
                "grew": st.get("grew", 0),
                "start": st.get("start"),
                "end": st.get("end"),
                "p90": p90,
                "max": mx,
                "slack": slack,
                "margin": margin,
                "p90_margin": p90_margin,
                "memory_budget_required": row.get("memory_budget_required"),
            }
        )
        flag = "  STALE-LOCAL (growth read from an old origin/main)" if stale else ""
        se = f"{st.get('start', '-')}->{st.get('end', '-')}"
        print(f"        {repo:<22} {api_main:<9} {local:<9} {agents['headroom']:>8} {st.get('commits', 0):>7} {st.get('grew', 0):>4} {se:>15} {p90:>6} {mx:>6} {slack:>6} {margin:>+7} {p90_margin:>+10}{flag}")
    neg = [r["repo"] for r in rows if r["margin"] < 0]
    zero = [r["repo"] for r in rows if r["margin"] == 0]
    print(f"        negative: {len(neg)} {neg}; exactly zero: {zero}")
    print("        could it read differently? yes -- headroom is live from the GitHub API; growth is local git history, so a")
    print("        STALE-LOCAL row measures an old window (re-run with --fetch) and is refused below.")
    stale_rows = [r["repo"] for r in rows if r["stale_local"]]
    if stale_rows:
        raise Unmeasurable(f"slack: {stale_rows} read growth from a local origin/main that disagrees with GitHub -- re-run with --fetch")
    return {"floor": floor, "days": days, "measured_at": measured_at, "rows": rows, "negative": neg, "zero": zero}


# --------------------------------------------------------------------------------------------
# spans (raw v2, for comparison only)
# --------------------------------------------------------------------------------------------
def probe_spans(n: int = 30) -> dict:
    sm = load_module("safe_merge_probe", ROOT / "util/safe_merge.py")
    v2 = ROOT / "util/ad-hoc/2026-09-08_measure_required_check_span_v2.py"
    rows = []
    print(f"[spans] RAW v2 required-context span, last {n} merged heads per repo -- re-run tails inflate it; size from first-pass")
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
        clears, inside = budget > mxv, budget <= 4 * p90v
        verdict = "OK" if clears and inside else ("BELOW RAW MAX" if not clears else "ABOVE 4x p90")
        rows.append({"repo": repo, "measured": int(head.group(1)), "unmeasurable": int(head.group(2)), "p90": p90v, "max": mxv, "budget": budget, "four_p90": 4 * p90v, "verdict": verdict})
        print(f"        {repo:<22} {head.group(1):>4} {head.group(2):>6} {p90v:>6} {mxv:>6} {budget:>6} {4 * p90v:>6}  {verdict}")
    print(f"        TIMEOUT_CEILING={sm.TIMEOUT_CEILING} DEFAULT_TIMEOUT={sm.DEFAULT_TIMEOUT}")
    print("        could it read differently? yes -- a budget at or below the raw max prints BELOW RAW MAX. The sample is the last n")
    print("        merged PRs by CREATION order (gh pr list), so it moves with every merge and one head at its edge can move a max.")
    bad = [r["repo"] for r in rows if r["verdict"] == "UNMEASURABLE"]
    if bad:
        raise Unmeasurable(f"spans: v2 could not measure {bad}")
    return {"n": n, "rows": rows}


# --------------------------------------------------------------------------------------------
# first-pass (the sizing instrument)
# --------------------------------------------------------------------------------------------
def first_pass_of(executions: list[dict]) -> tuple[list[dict], list[dict]]:
    """Pick each required context's FIRST execution on a head; return (first, all_deduped).

    `executions` are dicts with name/started/completed/conclusion. Exact duplicates are dropped
    first: a "re-run failed jobs" attempt COPIES the jobs that passed into the new attempt with
    their original timestamps, and those copies are not new executions.

    Why the FIRST execution: the budget is spent on one pass. A later execution of a context --
    a re-run attempt after a failure, a workflow run started by a later PR event such as
    `Guard PR base branch` on `edited` -- is not part of the pass `safe_merge` waited on. The
    rule this replaced dropped a whole head whenever any context ran twice, which set aside 13
    heads whose only repeat was a successful `Guard PR base branch` run: dropping heads can only
    LOWER a max, the unsafe direction for a "budget > max" rule.
    """
    seen, dedup = set(), []
    for e in executions:
        key = (e["name"], e["started"], e["completed"], e["conclusion"])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(e)
    by_name: dict = {}
    for e in dedup:
        if e["started"] is None:
            continue
        cur = by_name.get(e["name"])
        if cur is None or (e["started"], e["completed"] or e["started"]) < (cur["started"], cur["completed"] or cur["started"]):
            by_name[e["name"]] = e
    return list(by_name.values()), dedup


def _span(execs: list[dict]) -> float | None:
    starts = [e["started"] for e in execs if e["started"]]
    ends = [e["completed"] for e in execs if e["completed"]]
    if not starts or not ends:
        return None
    return (max(ends) - min(starts)).total_seconds()


def probe_first_pass(n: int = 30) -> dict:
    v2 = load_module("span_v2_probe", ROOT / "util/ad-hoc/2026-09-08_measure_required_check_span_v2.py")
    sm = load_module("safe_merge_probe3", ROOT / "util/safe_merge.py")
    out = []
    print(f"[first-pass] each head's FIRST PASS over its required contexts, last {n} merged heads per repo; healthy = every first")
    print("             execution passed (success/skipped/neutral); p90 index-based as v2; budget must be > healthy max and <= 4x p90")
    print(f"        {'repo':<22} {'healthy':>7} {'unhlthy':>7} {'unmeas':>6} {'p90':>6} {'max':>6} {'max PR':>7} {'budget':>6} {'4xp90':>6} {'raw max':>7}  verdict")
    for repo in REPOS:
        slug = f"{OWNER}/{repo}"
        required = v2.required_contexts(slug)
        if not required:
            out.append({"repo": repo, "verdict": "UNMEASURABLE (no required contexts)"})
            print(f"        {repo:<22} UNMEASURABLE -- no required contexts read")
            continue
        prs = json.loads(run(["gh", "pr", "list", "--repo", slug, "--state", "merged", "--limit", str(n), "--json", "number,headRefOid"]).stdout)
        healthy, unhealthy, unmeas, raw = [], [], [], []
        for pr in prs:
            sha = pr["headRefOid"]
            crs = gh_pages(f"repos/{slug}/commits/{sha}/check-runs?filter=all", key="check_runs")
            execs = [{"name": c["name"], "started": _ts(c["started_at"]), "completed": _ts(c["completed_at"]), "conclusion": c.get("conclusion")} for c in crs if c["name"] in required]
            have = {e["name"] for e in execs}
            # A required context reported only as a legacy commit status: one record per context,
            # earliest create to latest update, judged on its final state.
            for s in gh_pages(f"repos/{slug}/commits/{sha}/statuses"):
                if s["context"] in required and s["context"] not in have:
                    execs.append({"name": s["context"], "started": _ts(s["created_at"]), "completed": _ts(s["updated_at"]), "conclusion": s.get("state")})
            first, dedup = first_pass_of(execs)
            span = _span(first)
            if span is None:
                unmeas.append(pr["number"])
                continue
            raw_span = _span(dedup)
            raw.append(raw_span)
            failed = sorted(f"{e['name']}={e['conclusion']}" for e in first if (e["conclusion"] or "") not in PASSED)
            rec = {"pr": pr["number"], "span": round(span), "raw_span": round(raw_span or 0), "contexts": len(first), "required": len(required)}
            if failed:
                rec["first_pass_not_passed"] = failed
                unhealthy.append(rec)
            else:
                healthy.append(rec)
        budget = sm.timeout_for(repo)
        if not healthy:
            out.append({"repo": repo, "healthy": 0, "verdict": "UNMEASURABLE (no healthy head)"})
            print(f"        {repo:<22} {0:>7} {len(unhealthy):>7} {len(unmeas):>6}  UNMEASURABLE -- no healthy head")
            continue
        spans = sorted(r["span"] for r in healthy)
        p90v, mxv = v2.p90(spans), spans[-1]
        max_pr = max(healthy, key=lambda r: r["span"])["pr"]
        clears, inside = budget > mxv, budget <= 4 * p90v
        verdict = "OK" if clears and inside else ("BELOW HEALTHY MAX" if not clears else "ABOVE 4x p90")
        if repo == "juniper-cascor-client" and verdict == "ABOVE 4x p90":
            verdict += " (excluded from the pin by owner ruling 2026-09-15)"
        worst_unhealthy = max((r["span"] for r in unhealthy), default=0)
        out.append(
            {
                "repo": repo,
                "healthy": len(healthy),
                "unhealthy": unhealthy,
                "unmeasurable": unmeas,
                "p90": round(p90v),
                "max": mxv,
                "max_pr": max_pr,
                "budget": budget,
                "four_p90": round(4 * p90v),
                "raw_max": round(max(raw)) if raw else None,
                "worst_unhealthy_first_pass": worst_unhealthy,
                "margin": budget - mxv,
                "verdict": verdict,
            }
        )
        print(f"        {repo:<22} {len(healthy):>7} {len(unhealthy):>7} {len(unmeas):>6} {p90v:>6.0f} {mxv:>6} {'#' + str(max_pr):>7} {budget:>6} {4 * p90v:>6.0f} {round(max(raw)):>7}  {verdict}")
        for u in sorted(unhealthy, key=lambda r: -r["raw_span"]):
            print(f"            not healthy #{u['pr']}: first pass {u['span']} s, raw {u['raw_span']} s -- {', '.join(u['first_pass_not_passed'][:4])}")
    print("        could it read differently? yes -- a budget at or below the healthy max prints BELOW HEALTHY MAX, and an unhealthy")
    print("        head whose first pass ran longer than the healthy max is printed above with its span. The sample is the last n")
    print("        merged PRs by CREATION order, so it moves with every merge.")
    bad = [r["repo"] for r in out if str(r.get("verdict", "")).startswith("UNMEASURABLE")]
    if bad:
        raise Unmeasurable(f"first-pass: could not measure {bad}")
    return {"n": n, "rows": out}


# --------------------------------------------------------------------------------------------
# alarm
# --------------------------------------------------------------------------------------------
def probe_alarm() -> dict:
    rows = []
    print(f"[alarm] pr-budget-alarm.yml per repo; a run BREACHED iff its `{ALARM_SLACK_STEP} ...` step ran (it is skipped at level OK)")
    for repo in REPOS:
        meta = gh_json(f"repos/{OWNER}/{repo}")
        branch = meta["default_branch"]
        wf = run(["gh", "api", f"repos/{OWNER}/{repo}/contents/.github/workflows/pr-budget-alarm.yml?ref={branch}", "--jq", ".sha"], check=False)
        present = wf.returncode == 0
        secrets = run(["gh", "secret", "list", "--repo", f"{OWNER}/{repo}"], check=False)
        has_webhook = ("SLACK_WEBHOOK_URL" in [ln.split("\t")[0] for ln in secrets.stdout.splitlines()]) if secrets.returncode == 0 else None
        runs, levels = [], {}
        missing_step = 0
        if present:
            for r in gh_json(f"repos/{OWNER}/{repo}/actions/workflows/pr-budget-alarm.yml/runs?per_page=50").get("workflow_runs", []):
                if r["status"] != "completed":
                    continue
                steps = [s for j in gh_json(f"repos/{OWNER}/{repo}/actions/runs/{r['id']}/jobs").get("jobs", []) for s in j.get("steps", [])]
                slack = next((s for s in steps if s["name"].startswith(ALARM_SLACK_STEP)), None)
                if slack is None:
                    missing_step += 1
                    level = "UNREADABLE"
                else:
                    level = "OK" if slack["conclusion"] == "skipped" else f"BREACH (slack step {slack['conclusion']})"
                runs.append({"id": r["id"], "created": r["created_at"], "conclusion": r["conclusion"], "level": level})
                levels[level] = levels.get(level, 0) + 1
        rows.append({"repo": repo, "alarm_present": present, "slack_webhook_secret": has_webhook, "runs": runs, "levels": levels, "missing_step": missing_step})
        hook = {True: "yes", False: "NO", None: "unreadable"}[has_webhook]
        span = f"{runs[-1]['created'][:10]}..{runs[0]['created'][:10]}" if runs else "-"
        print(f"        {repo:<22} alarm={'present' if present else 'MISSING':<8} webhook={hook:<10} runs={len(runs):<3} {span:<22} {levels}")
        for r in runs:
            if r["level"] not in ("OK",):
                print(f"            {r['created']} run {r['id']}: {r['level']}")
    print("        could it read differently? yes -- a run whose Slack step ran prints BREACH, and a missing file, secret or step prints as")
    print("        such. On a repo WITH the webhook a breach posts to Slack and leaves no annotation, which is why this reads the step.")
    bad = [r["repo"] for r in rows if not r["alarm_present"] or r["slack_webhook_secret"] is None or r["missing_step"]]
    if bad:
        raise Unmeasurable(f"alarm: file, secret list or Slack step unreadable on {bad}")
    return {"rows": rows}


# --------------------------------------------------------------------------------------------
# soak
# --------------------------------------------------------------------------------------------
_TS = re.compile(r"^\d{4}-\d\d-\d\dT[\d:.]+Z ")


def _soak_findings(log_text: str) -> tuple[list[dict], int | None]:
    """The screen's own output in a soak job log: per-check findings, and the screen's exit code.

    The job log ECHOES the step's script before running it, so only EXPANDED output is trusted:
    the screen's `[FAIL] <path>` blocks and its final verdict line. The exit code is not taken
    from the annotation title: until 2026-09-22 ci.yml wrote `title=... (advisory, exit N)`, and a
    comma ENDS a workflow-command property, so every run before that recorded a title stopping at
    `(advisory` with the code lost.
    """
    lines = [_TS.sub("", ln) for ln in log_text.splitlines()]
    findings = []
    for i, ln in enumerate(lines):
        m = re.match(r"\[FAIL\] (.+)$", ln)
        if not m:
            continue
        path = m.group(1).strip()
        cur = None
        for nxt in lines[i + 1 : i + 40]:
            if not nxt.startswith("   "):
                break
            s = nxt.strip()
            code = re.match(r"(C\d) ", s)
            if code:
                cur = {"path": path, "check": code.group(1), "header": s, "items": []}
                findings.append(cur)
            elif cur is not None:
                cur["items"].append(s)
    rc = None
    for ln in lines:
        if ln.startswith("OK: no structural regression against the base"):
            rc = 0
        elif ln.startswith("FAIL: markdown structure regressed."):
            rc = 1
        elif ln.startswith("ERROR: ") or ln.startswith("[ERR ] base ref"):
            rc = 2
    return findings, rc


def probe_soak(since: str) -> dict:
    cutoff = _ts(since)
    runs = gh_pages(f"repos/{OWNER}/juniper-ml/actions/workflows/ci.yml/runs?event=pull_request&created=%3E%3D{urllib.parse.quote(since)}", key="workflow_runs")
    heads = sorted({r["head_sha"] for r in runs})
    pr_cache: dict = {}

    def prs_of(sha: str) -> list[int]:
        # A workflow run's `pull_requests` is EMPTY once its PR has merged, so it undercounts
        # the denominator roughly fourfold; the commit's own PR association does not.
        if sha not in pr_cache:
            pr_cache[sha] = sorted(p["number"] for p in (gh_json(f"repos/{OWNER}/juniper-ml/commits/{sha}/pulls") or []))
        return pr_cache[sha]

    name = urllib.parse.quote(SOAK_JOB)
    checks = []
    for sha in heads:
        for cr in gh_json(f"repos/{OWNER}/juniper-ml/commits/{sha}/check-runs?check_name={name}&filter=all&per_page=100").get("check_runs", []):
            if cr.get("started_at") and _ts(cr["started_at"]) < cutoff:
                continue
            # Retried like every other read: one transient failure here once scored a completed
            # run (ml#1962, which examined 2 files cleanly) as unreadable. A cancelled run's log
            # stays unreadable across every attempt, which is the honest outcome.
            for attempt in range(1, 4):
                log = run(["gh", "api", f"repos/{OWNER}/juniper-ml/actions/jobs/{cr['id']}/logs"], check=False)
                if log.returncode == 0 or cr.get("conclusion") == "cancelled" or attempt == 3:
                    break
                time.sleep(2 * attempt)
            examined = re.search(r"examining (\d+) changed markdown file", log.stdout)
            nothing = re.search(r"no markdown changed against [0-9a-f]{7,40} -- nothing to examine", log.stdout) is not None
            findings, rc = _soak_findings(log.stdout) if log.returncode == 0 else ([], None)
            checks.append(
                {
                    "head": sha,
                    "prs": prs_of(sha) if examined or findings else [],
                    "check_run": cr["id"],
                    "conclusion": cr.get("conclusion"),
                    "log_read": log.returncode == 0,
                    "examined_files": int(examined.group(1)) if examined else 0,
                    "nothing_to_examine": nothing,
                    "screen_exit": rc,
                    "findings": findings,
                }
            )
    unread = [c for c in checks if not c["log_read"]]
    examined = [c for c in checks if c["examined_files"] > 0]
    idle = [c for c in checks if c["nothing_to_examine"]]
    unclassified = [c for c in checks if c["log_read"] and not c["examined_files"] and not c["nothing_to_examine"]]
    flagged = [c for c in checks if c["findings"]]
    prs_examined = sorted({p for c in examined for p in c["prs"]})
    # DISTINCT = one per (PR, file, check, lost/added items). Keyed on the items, NOT on the
    # check's header line: the header carries counts ("count 31 -> 38") that change between
    # pushes, which made one lost heading on #1973 read as two findings.
    distinct: dict = {}
    for c in checks:
        for f in c["findings"]:
            key = (tuple(c["prs"]), f["path"], f["check"], tuple(f["items"]))
            d = distinct.setdefault(key, {"runs": 0, "heads": set()})
            d["runs"] += 1
            d["heads"].add(c["head"][:8])
    # Was each flagged PR still flagged at its FINAL head -- i.e. would a required version of this
    # check have blocked the merge itself, not just an intermediate push?
    final_head: dict = {}
    for pr in sorted({p for c in flagged for p in c["prs"]}):
        final_head[pr] = gh_json(f"repos/{OWNER}/juniper-ml/pulls/{pr}")["head"]["sha"]
    flagged_at_final = sorted({p for c in flagged for p in c["prs"] if final_head.get(p) == c["head"]})
    print(f"[soak] `{SOAK_JOB}` on juniper-ml pull_request CI since {since}")
    print(f"       ci.yml pull_request runs: {len(runs)} over {len(heads)} heads; soak check-runs: {len(checks)}")
    print(f"       logs unreadable: {len(unread)}; no markdown changed: {len(idle)}; UNCLASSIFIED: {len(unclassified)}")
    print(f"       runs that EXAMINED >=1 file: {len(examined)}, on {len(prs_examined)} distinct PRs; files examined: {sum(c['examined_files'] for c in examined)}")
    print(f"       runs with findings: {len(flagged)}; screen exits among examined runs: " + str({k: sum(1 for c in examined if c['screen_exit'] == k) for k in (0, 1, 2, None)}))
    print(f"       DISTINCT findings (PR, file, check, items): {len(distinct)}; PRs flagged at their FINAL head: {flagged_at_final}")
    for (prs, path, check, items), v in sorted(distinct.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        print(f"         PR {list(prs)} {check} {path}  runs={v['runs']} heads={sorted(v['heads'])}")
        for it in items[:6]:
            print(f"             {it}")
    for c in unclassified:
        print(f"         unclassified: head {c['head'][:8]} check-run {c['check_run']} conclusion={c['conclusion']}")
    print("       could it read differently? yes -- every [FAIL] block the screen prints is parsed and counted; a run with no markdown")
    print("       change examines nothing and is NOT evidence either way; adjudicating true vs false is NOT done here.")
    if not checks:
        raise Unmeasurable("no soak check-runs found -- refusing to report a clean soak")
    if unclassified:
        raise Unmeasurable(f"soak: {len(unclassified)} readable log(s) neither examined a file nor said why")
    return {
        "since": since,
        "ci_runs": len(runs),
        "heads": len(heads),
        "soak_runs": len(checks),
        "logs_unreadable": len(unread),
        "idle_runs": len(idle),
        "examined_runs": len(examined),
        "prs_examined": prs_examined,
        "files_examined": sum(c["examined_files"] for c in examined),
        "runs_with_findings": len(flagged),
        "distinct_findings": [{"prs": list(p), "path": pa, "check": ch, "items": list(it), "runs": v["runs"], "heads": sorted(v["heads"])} for (p, pa, ch, it), v in distinct.items()],
        "flagged_at_final_head": flagged_at_final,
        "checks": checks,
    }


# --------------------------------------------------------------------------------------------
# lockfile
# --------------------------------------------------------------------------------------------
def probe_lockfile() -> dict:
    """EVERY PR the lockfile workflow opened -- by branch, not a title search limited to the newest.

    The first draft of this probe read the five newest PRs and concluded "4 of 4 GITHUB_TOKEN PRs
    were parked, not suppressed". The branch has carried 18 GITHUB_TOKEN PRs, and five of them got
    no `pull_request` run at all -- a correct predicate over an incomplete set.
    """
    prs = json.loads(run(["gh", "pr", "list", "--repo", f"{OWNER}/juniper-ml", "--head", LOCKFILE_BRANCH, "--state", "all", "--limit", "200", "--json", "number,author,createdAt,state"]).stdout)
    if not prs:
        raise Unmeasurable(f"no PR found on {LOCKFILE_BRANCH}")
    rows = []
    print(f"[lockfile] every PR opened on {LOCKFILE_BRANCH}; the OPENING commit's pull_request runs, and whether attempt 1 ran any JOB")
    for pr in sorted(prs, key=lambda p: p["createdAt"]):
        commits = gh_json(f"repos/{OWNER}/juniper-ml/pulls/{pr['number']}/commits?per_page=100")
        opening = commits[0]["sha"] if commits else None
        wr = gh_json(f"repos/{OWNER}/juniper-ml/actions/runs?head_sha={opening}&event=pull_request&per_page=50").get("workflow_runs", []) if opening else []
        bot = [r for r in wr if r["actor"]["login"].endswith("[bot]")]
        human = [r for r in wr if not r["actor"]["login"].endswith("[bot]")]
        # The run LIST shows the LATEST attempt, and a conclusion is not evidence (closing a PR
        # flips a parked run to `failure`); whether attempt 1 ran any JOB is.
        ran, released_by = 0, set()
        for r in bot:
            if gh_json(f"repos/{OWNER}/juniper-ml/actions/runs/{r['id']}/attempts/1/jobs").get("total_count", 0) > 0:
                ran += 1
            if r["run_attempt"] >= 2:
                released_by.add(f"re-run by {r['triggering_actor']['login']}")
        events = [e.get("event") for e in gh_json(f"repos/{OWNER}/juniper-ml/issues/{pr['number']}/timeline?per_page=100")]
        if "reopened" in events and human:
            released_by.add("close/reopen")
        state = "NO RUN" if not bot else ("EXECUTED" if ran == len(bot) else ("PARKED" if ran == 0 else f"PARTIAL {ran}/{len(bot)}"))
        rows.append({"number": pr["number"], "created": pr["createdAt"], "author": pr["author"]["login"], "state": pr["state"], "opening": (opening or "")[:8], "bot_runs": len(bot), "bot_runs_with_jobs": ran, "human_runs": len(human), "result": state, "released_by": sorted(released_by)})
        print(f"           #{pr['number']:<5} {pr['createdAt'][:10]} {pr['author']['login']:<26} {state:<9} bot runs {len(bot)} (ran jobs {ran}), human runs {len(human)}  {sorted(released_by) or ''}")
    tally: dict = {}
    for r in rows:
        tally.setdefault(r["author"], {}).setdefault(r["result"], 0)
        tally[r["author"]][r["result"]] += 1
    print(f"           tally by author: {tally}")
    print("           could it read differently? yes -- NO RUN, PARKED and EXECUTED are all observed on this branch; an App-opened PR")
    print("           whose bot runs ran jobs on attempt 1 is the only evidence the App-token arm works.")
    return {"rows": rows, "tally": tally}


# --------------------------------------------------------------------------------------------
# settings
# --------------------------------------------------------------------------------------------
def probe_settings() -> dict:
    """The merge-lane settings the handoff's MERGING block depends on, per repo, from the API."""
    rows = []
    print("[settings] allow_update_branch / allow_auto_merge per repo (read with admin scope)")
    for repo in REPOS:
        meta = gh_json(f"repos/{OWNER}/{repo}")
        row = {"repo": repo, "allow_update_branch": meta.get("allow_update_branch"), "allow_auto_merge": meta.get("allow_auto_merge"), "admin": (meta.get("permissions") or {}).get("admin")}
        rows.append(row)
        print(f"           {repo:<22} allow_update_branch={row['allow_update_branch']!s:<5} allow_auto_merge={row['allow_auto_merge']!s:<5} admin={row['admin']}")
    print("           could it read differently? yes -- each field is read per repo and printed as returned; without admin scope")
    print("           GitHub omits allow_update_branch, which is refused below rather than read as false.")
    if any(r["allow_update_branch"] is None for r in rows):
        raise Unmeasurable("allow_update_branch not readable on every repo (needs admin scope) -- refusing to report a partial census")
    return {"rows": rows}


# --------------------------------------------------------------------------------------------
# waiter
# --------------------------------------------------------------------------------------------
def probe_waiter() -> dict:
    """What `util/wait_for_checks.py` actually waits when --timeout is omitted, per repo.

    The first draft compared the module's DEFAULT_TIMEOUT constant against the budgets -- which
    reads "8 of 9" whether or not the CLI uses those budgets, so it could not tell the fix from
    the defect. This calls the CLI's own resolver.
    """
    waiter = load_module("wait_for_checks_probe", ROOT / "util/wait_for_checks.py")
    sm = load_module("safe_merge_probe2", ROOT / "util/safe_merge.py")
    if not hasattr(waiter, "resolve_timeout"):
        raise Unmeasurable("util/wait_for_checks.py has no resolve_timeout -- the omitted --timeout still waits a flat default")
    rows = []
    print("[waiter] util/wait_for_checks.py with --timeout omitted: the seconds it waits, and where they come from")
    for repo in REPOS + ["juniper-not-a-measured-repo"]:
        seconds, source = waiter.resolve_timeout(repo)
        agree = seconds == sm.timeout_for(repo)
        rows.append({"repo": repo, "seconds": seconds, "source": source, "matches_safe_merge": agree})
        print(f"           {repo:<28} {seconds:>5}s  {'==' if agree else '!='} safe_merge  ({source})")
    print("           could it read differently? yes -- a CLI still waiting a flat constant prints the same seconds for every repo")
    print("           and != against safe_merge's table, or a FALLBACK source.")
    if not all(r["matches_safe_merge"] for r in rows):
        raise Unmeasurable("waiter: the omitted-timeout budget disagrees with util/safe_merge.py for some repo")
    return {"rows": rows}


PROBES = ["structure", "slack", "spans", "first-pass", "alarm", "soak", "lockfile", "settings", "waiter"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("probe", choices=PROBES + ["all"])
    ap.add_argument("--fetch", action="store_true", help="slack: fetch a sibling whose origin/main disagrees with GitHub")
    ap.add_argument("--since", default=SOAK_WIRED, help=f"soak: ISO-8601 UTC lower bound (default {SOAK_WIRED}, when the job was wired)")
    ap.add_argument("-n", type=int, default=30, help="spans / first-pass: merged heads per repo (default 30)")
    ap.add_argument("--json", type=Path, help="also write every result to this JSON file (its directory must exist)")
    args = ap.parse_args(argv)
    if args.json and not args.json.parent.is_dir():
        # Checked BEFORE the probes run: failing at the final write threw away minutes of work.
        print(f"error: --json directory {args.json.parent} does not exist", file=sys.stderr)
        return 2

    chosen = PROBES if args.probe == "all" else [args.probe]
    results: dict = {"measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    failed = []
    for name in chosen:
        try:
            fn = {
                "structure": probe_structure,
                "slack": lambda: probe_slack(args.fetch),
                "spans": lambda: probe_spans(args.n),
                "first-pass": lambda: probe_first_pass(args.n),
                "alarm": probe_alarm,
                "soak": lambda: probe_soak(args.since),
                "lockfile": probe_lockfile,
                "settings": probe_settings,
                "waiter": probe_waiter,
            }[name]
            results[name] = fn()
        except Unmeasurable as exc:
            failed.append(name)
            results[name] = {"unmeasurable": str(exc)}
            print(f"[{name}] UNMEASURABLE: {exc}", file=sys.stderr)
        print()
    if args.json:
        args.json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        print(f"wrote {args.json}")
    if failed:
        print(f"UNMEASURABLE: {failed}", file=sys.stderr)
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
