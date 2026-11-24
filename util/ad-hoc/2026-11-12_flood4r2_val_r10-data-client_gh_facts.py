"""
Read-only GitHub facts for the validation of the juniper-data-client ruling-10 port (every request is a REST GET).

Subcommands:
  job-log <owner/repo> <run id> <job name> <out dir> [pattern ...]   save one job's log and print the lines matching each pattern
  job-log-by-id <owner/repo> <job id> <out dir> [pattern ...]        the same, from a job id; also names the job's run and its event
  run-jobs <owner/repo> <run id>                                     the run's event and its jobs
  artifacts <owner/repo> <run id>                                    list the run's artifact names
  pr-census <owner/repo> <out json> [--local <checkout>]             every pull request's commit count and merge commits
  pr-state <owner/repo> <number> [<number> ...]                      state, merged_at, merge_commit_sha, base and head of each
  checks <owner/repo> <ref>                                          check-run names and conclusions for a ref
  rulesets <owner/repo>                                              required status checks from the repository's rulesets

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WORKERS = 4


def gh_get(path: str, raw: bool = False, paginate: bool = False) -> str:
    """One ``gh api`` GET. No field flag is ever passed, so gh never switches the method to POST."""
    argv = ["gh", "api", "--method", "GET"]
    if paginate:
        argv.append("--paginate")
    if raw:
        argv += ["-H", "Accept: application/vnd.github.raw"]
    argv.append(path)
    res = subprocess.run(argv, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"gh api GET {path} exited {res.returncode}: {res.stderr.strip()[:400]}")
    return res.stdout


def gh_json(path: str, paginate: bool = False):
    text = gh_get(path, paginate=paginate)
    if not paginate:
        return json.loads(text)
    # --paginate concatenates the pages' JSON arrays back to back.
    decoder = json.JSONDecoder()
    items, at = [], 0
    while at < len(text):
        while at < len(text) and text[at].isspace():
            at += 1
        if at >= len(text):
            break
        page, at = decoder.raw_decode(text, at)
        items.extend(page if isinstance(page, list) else [page])
    return items


def cmd_job_log(repo: str, run_id: str, job_name: str, out_dir: str, patterns: list[str]) -> int:
    jobs = gh_json(f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100")["jobs"]
    matches = [job for job in jobs if job["name"] == job_name]
    if len(matches) != 1:
        print(json.dumps({"error": f"expected one job named {job_name!r}", "jobs": [job["name"] for job in jobs]}, indent=2))
        return 1
    job = matches[0]
    log = gh_get(f"repos/{repo}/actions/jobs/{job['id']}/logs")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / f"{repo.split('/')[1]}_run{run_id}_job{job['id']}.log"
    log_path.write_text(log, encoding="utf-8")
    info = {
        "job_id": job["id"],
        "name": job["name"],
        "conclusion": job["conclusion"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
        "runner_name": job.get("runner_name"),
        "labels": job.get("labels"),
        "steps": [{"number": step["number"], "name": step["name"], "conclusion": step["conclusion"]} for step in job["steps"]],
        "log": str(log_path),
        "log_lines": len(log.splitlines()),
    }
    print(json.dumps(info, indent=2))
    for pattern in patterns:
        rx = re.compile(pattern)
        print(f"--- /{pattern}/")
        for number, line in enumerate(log.splitlines(), 1):
            if rx.search(line):
                print(f"{number}: {line[:400]}")
    return 0


def cmd_job_log_by_id(repo: str, job_id: str, out_dir: str, patterns: list[str]) -> int:
    job = gh_json(f"repos/{repo}/actions/jobs/{job_id}")
    run = gh_json(f"repos/{repo}/actions/runs/{job['run_id']}")
    log = gh_get(f"repos/{repo}/actions/jobs/{job_id}/logs")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / f"{repo.split('/')[1]}_run{job['run_id']}_job{job_id}.log"
    log_path.write_text(log, encoding="utf-8")
    info = {
        "job_id": job["id"],
        "name": job["name"],
        "conclusion": job["conclusion"],
        "started_at": job["started_at"],
        "run_id": job["run_id"],
        "run_event": run["event"],
        "run_head_branch": run["head_branch"],
        "run_head_sha": run["head_sha"],
        "run_pull_requests": [pull["number"] for pull in run.get("pull_requests", [])],
        "run_display_title": run.get("display_title"),
        "labels": job.get("labels"),
        "steps": [(step["number"], step["name"], step["conclusion"]) for step in job["steps"]],
        "log": str(log_path),
        "log_lines": len(log.splitlines()),
    }
    print(json.dumps(info, indent=1))
    for pattern in patterns:
        rx = re.compile(pattern)
        print(f"--- /{pattern}/")
        for number, line in enumerate(log.splitlines(), 1):
            if rx.search(line):
                print(f"{number}: {line[:400]}")
    return 0


def cmd_run_jobs(repo: str, run_id: str) -> int:
    run = gh_json(f"repos/{repo}/actions/runs/{run_id}")
    jobs = gh_json(f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100")["jobs"]
    print(json.dumps({"event": run["event"], "head_branch": run["head_branch"], "head_sha": run["head_sha"], "conclusion": run["conclusion"], "created_at": run["created_at"], "display_title": run.get("display_title"), "jobs": [(job["id"], job["name"], job["conclusion"]) for job in jobs]}, indent=1))
    return 0


def cmd_artifacts(repo: str, run_id: str) -> int:
    data = gh_json(f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100")
    print(json.dumps({"total_count": data["total_count"], "names": sorted(a["name"] for a in data["artifacts"])}, indent=2))
    return 0


def _is_ancestor(checkout: str, sha: str, ref: str) -> bool | None:
    res = subprocess.run(["git", "-C", checkout, "merge-base", "--is-ancestor", sha, ref], capture_output=True, text=True, check=False)
    if res.returncode in (0, 1):
        return res.returncode == 0
    return None


def cmd_pr_census(repo: str, out_json: str, local: str | None) -> int:
    pulls = gh_json(f"repos/{repo}/pulls?state=all&per_page=100", paginate=True)
    numbers = sorted(pull["number"] for pull in pulls)
    by_number = {pull["number"]: pull for pull in pulls}

    def one(number: int) -> dict:
        commits = gh_json(f"repos/{repo}/pulls/{number}/commits?per_page=100", paginate=True)
        shas = [commit["sha"] for commit in commits]
        own = set(shas)
        merges = []
        for index, commit in enumerate(commits):
            parents = [parent["sha"] for parent in commit["parents"]]
            if len(parents) < 2:
                continue
            previous = shas[index - 1] if index else None
            entry = {
                "sha": commit["sha"],
                "parents": parents,
                "n_parents": len(parents),
                "first_parent_is_previous_pr_commit": parents[0] == previous,
                "first_parent_in_pr": parents[0] in own,
                "other_parents_in_pr": [parent in own for parent in parents[1:]],
            }
            if local:
                entry["other_parents_on_base"] = [_is_ancestor(local, parent, "origin/" + by_number[number]["base"]["ref"]) for parent in parents[1:]]
            merges.append(entry)
        pull = by_number[number]
        return {"number": number, "state": pull["state"], "merged_at": pull["merged_at"], "created_at": pull["created_at"], "base": pull["base"]["ref"], "head_repo_is_fork": bool(pull["head"]["repo"] and pull["head"]["repo"]["fork"]), "user": pull["user"]["login"], "commits": len(shas), "merges": merges}

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        rows = list(pool.map(one, numbers))
    with_merge = [row for row in rows if row["merges"]]
    all_merges = [merge for row in with_merge for merge in row["merges"]]
    summary = {
        "repo": repo,
        "pull_requests": len(rows),
        "highest_number": max(numbers),
        "newest_created_at": max(row["created_at"] for row in rows),
        "max_commits": max(row["commits"] for row in rows),
        "max_commits_prs": [row["number"] for row in rows if row["commits"] == max(r["commits"] for r in rows)],
        "prs_over_30_commits": [row["number"] for row in rows if row["commits"] > 30],
        "prs_with_a_merge_commit": len(with_merge),
        "merge_commits": len(all_merges),
        "octopus_merges": sum(1 for merge in all_merges if merge["n_parents"] > 2),
        "merges_whose_first_parent_is_not_the_previous_pr_commit": [(row["number"], merge["sha"]) for row in with_merge for merge in row["merges"] if not merge["first_parent_is_previous_pr_commit"]],
        "merges_with_another_parent_inside_the_pr": [(row["number"], merge["sha"]) for row in with_merge for merge in row["merges"] if any(merge["other_parents_in_pr"])],
        "merges_whose_other_parent_is_not_on_the_base_branch": [(row["number"], merge["sha"], merge.get("other_parents_on_base")) for row in with_merge for merge in row["merges"] if local and not all(flag is True for flag in merge["other_parents_on_base"])],
        "prs_from_forks": [row["number"] for row in rows if row["head_repo_is_fork"]],
        "bases": sorted({row["base"] for row in rows}),
    }
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "rows": rows}, fh, indent=1)
        fh.write("\n")
    print(json.dumps(summary, indent=2))
    return 0


def cmd_pr_state(repo: str, numbers: list[str]) -> int:
    out = []
    for number in numbers:
        try:
            pull = gh_json(f"repos/{repo}/pulls/{number}")
        except RuntimeError as exc:
            out.append({"number": number, "error": str(exc)})
            continue
        out.append({key: pull[key] for key in ("number", "state", "draft", "merged", "merged_at", "merge_commit_sha", "title", "commits", "created_at")} | {"base_ref": pull["base"]["ref"], "base_sha": pull["base"]["sha"], "head_sha": pull["head"]["sha"], "user": pull["user"]["login"]})
    print(json.dumps(out, indent=2))
    return 0


def cmd_checks(repo: str, ref: str) -> int:
    runs = gh_json(f"repos/{repo}/commits/{ref}/check-runs?per_page=100")["check_runs"]
    print(json.dumps(sorted((run["name"], run["conclusion"], run["app"]["slug"]) for run in runs), indent=1))
    return 0


def cmd_rulesets(repo: str) -> int:
    out = []
    for ruleset in gh_json(f"repos/{repo}/rulesets"):
        detail = gh_json(f"repos/{repo}/rulesets/{ruleset['id']}")
        required = [check["context"] for rule in detail.get("rules", []) if rule["type"] == "required_status_checks" for check in rule["parameters"]["required_status_checks"]]
        out.append({"name": detail["name"], "enforcement": detail["enforcement"], "target": detail.get("target"), "include": detail.get("conditions", {}).get("ref_name", {}).get("include"), "rule_types": sorted(rule["type"] for rule in detail.get("rules", [])), "required_status_checks": required})
    print(json.dumps(out, indent=2))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    command, args = sys.argv[1], sys.argv[2:]
    if command == "job-log":
        return cmd_job_log(args[0], args[1], args[2], args[3], args[4:])
    if command == "job-log-by-id":
        return cmd_job_log_by_id(args[0], args[1], args[2], args[3:])
    if command == "run-jobs":
        return cmd_run_jobs(args[0], args[1])
    if command == "artifacts":
        return cmd_artifacts(args[0], args[1])
    if command == "pr-census":
        local = args[args.index("--local") + 1] if "--local" in args else None
        return cmd_pr_census(args[0], args[1], local)
    if command == "pr-state":
        return cmd_pr_state(args[0], args[1:])
    if command == "checks":
        return cmd_checks(args[0], args[1])
    if command == "rulesets":
        return cmd_rulesets(args[0])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
