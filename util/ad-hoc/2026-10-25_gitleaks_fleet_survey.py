#!/usr/bin/env python3
"""Survey how each of the nine Juniper repos configures and invokes gitleaks, read from each REMOTE default branch.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc -- investigation (gitleaks zero-rule configuration, fleet follow-up to juniper-ml#2203)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2203 (merged as bf595395); util/ad-hoc/2026-10-10_gitleaks_probe.py (the vacuity instrument)

WHY THIS EXISTS

juniper-ml#2203 found that a `.gitleaks.toml` without an `[extend]` table loads ONLY its own `[[rules]]`, so a file
holding nothing but an `[allowlist]` loads zero rules and CI's gitleaks step can never fail. This script reads, from
each repository's remote default branch through the GitHub contents API (local checkouts lag), the facts a verdict
needs: the config's tables, the ignore file, every workflow step that runs gitleaks (action SHA, GITLEAKS_VERSION,
GITLEAKS_CONFIG, --config, its `if:`) and the events that workflow runs on, plus any gitleaks pre-commit hook.

It writes each `.gitleaks.toml` it finds to --out-dir so the probe's `vacuity` mode can be run against the exact bytes
on the default branch. It reads no secret file and prints no file content beyond the gitleaks-related lines.

Usage:
    python3 util/ad-hoc/2026-10-25_gitleaks_fleet_survey.py --out-dir DIR [--repo NAME ...]

Exit codes: 0 survey written; 1 a GitHub API call failed.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess  # nosec B404 -- runs `gh api` with a fixed argv, never a shell
import sys
import tomllib
from pathlib import Path

import yaml

OWNER = "pcalnon"
REPOS = (
    "juniper-cascor",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-canopy",
    "juniper-deploy",
    "juniper-recurrence",
    "juniper-ml",
)


class ApiError(RuntimeError):
    pass


def gh_api(path: str) -> object | None:
    """GET one REST path; None on a 404, ApiError on anything else that is not a success."""
    res = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603 B607
    if res.returncode == 0:
        return json.loads(res.stdout)
    if "Not Found" in res.stdout or "HTTP 404" in res.stderr:
        return None
    raise ApiError(f"gh api {path}: exit {res.returncode}: {res.stderr.strip()[:200]}")


def file_text(repo: str, path: str, ref: str) -> str | None:
    payload = gh_api(f"repos/{OWNER}/{repo}/contents/{path}?ref={ref}")
    if not isinstance(payload, dict) or payload.get("type") != "file":
        return None
    return base64.b64decode(payload["content"]).decode("utf-8", "replace")


def workflow_events(doc: dict) -> list[str]:
    # YAML 1.1 reads a bare `on:` key as boolean True.
    on = doc.get("on", doc.get(True))
    if isinstance(on, str):
        return [on]
    if isinstance(on, list):
        return [str(e) for e in on]
    if isinstance(on, dict):
        return [str(e) for e in on]
    return []


def gitleaks_steps(doc: dict) -> list[dict]:
    out = []
    for job_id, job in (doc.get("jobs") or {}).items():
        for step in (job or {}).get("steps") or []:
            uses = str(step.get("uses", ""))
            run = str(step.get("run", ""))
            if "gitleaks" not in uses.lower() and "gitleaks" not in run.lower():
                continue
            env = step.get("env") or {}
            out.append(
                {
                    "job": job_id,
                    "job_if": job.get("if"),
                    "step": step.get("name"),
                    "step_if": step.get("if"),
                    "uses": uses or None,
                    "run_mentions_gitleaks": "gitleaks" in run.lower(),
                    "with": step.get("with"),
                    "GITLEAKS_VERSION": env.get("GITLEAKS_VERSION"),
                    "GITLEAKS_CONFIG": env.get("GITLEAKS_CONFIG"),
                    "GITLEAKS_ENABLE_UPLOAD_ARTIFACT": env.get("GITLEAKS_ENABLE_UPLOAD_ARTIFACT"),
                    "config_flag": "--config" in run or "-c " in run,
                }
            )
    return out


def survey(repo: str, out_dir: Path) -> dict:
    meta = gh_api(f"repos/{OWNER}/{repo}")
    assert isinstance(meta, dict)
    ref = meta["default_branch"]
    head = gh_api(f"repos/{OWNER}/{repo}/commits/{ref}")
    assert isinstance(head, dict)
    row: dict = {"repo": repo, "default_branch": ref, "head": head["sha"]}

    cfg_text = file_text(repo, ".gitleaks.toml", head["sha"])
    if cfg_text is None:
        row["config"] = None
    else:
        (out_dir / f"{repo}.gitleaks.toml").write_text(cfg_text, encoding="utf-8")
        cfg = tomllib.loads(cfg_text)
        row["config"] = {
            "tables": sorted(cfg),
            "extend": cfg.get("extend"),
            "rules": len(cfg.get("rules", [])),
            "allowlist_keys": sorted(cfg.get("allowlist", {})),
            "allowlists": len(cfg.get("allowlists", [])),
        }
    ignore = file_text(repo, ".gitleaksignore", head["sha"])
    row["gitleaksignore_entries"] = None if ignore is None else sum(1 for line in ignore.splitlines() if line.strip() and not line.lstrip().startswith("#"))

    listing = gh_api(f"repos/{OWNER}/{repo}/contents/.github/workflows?ref={head['sha']}") or []
    steps = []
    env_lines = []
    row["workflows"] = sorted(e.get("name", "") for e in listing)
    for entry in listing:
        name = entry.get("name", "")
        if not name.endswith((".yml", ".yaml")):
            continue
        text = file_text(repo, f".github/workflows/{name}", head["sha"]) or ""
        # A GITLEAKS_* variable at workflow, job or step level (GITLEAKS_CONFIG / GITLEAKS_CONFIG_TOML would override
        # the auto-discovered .gitleaks.toml): name and line number only, never the value.
        for n, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("GITLEAKS_") and ":" in stripped:
                env_lines.append(f"{name}:{n}:{stripped.split(':', 1)[0]}")
        if "gitleaks" not in text.lower():
            continue
        doc = yaml.safe_load(text) or {}
        for step in gitleaks_steps(doc):
            step["workflow"] = name
            step["events"] = workflow_events(doc)
            steps.append(step)
        if not gitleaks_steps(doc):
            steps.append({"workflow": name, "note": "mentions gitleaks outside any step's uses/run"})
    row["ci"] = steps
    row["gitleaks_env_names"] = env_lines

    pre = file_text(repo, ".pre-commit-config.yaml", head["sha"])
    hooks = []
    if pre:
        for r in (yaml.safe_load(pre) or {}).get("repos", []):
            if "gitleaks" in str(r.get("repo", "")).lower():
                hooks.append({"repo": r.get("repo"), "rev": r.get("rev"), "hooks": [h.get("id") for h in r.get("hooks", [])]})
    row["pre_commit_gitleaks"] = hooks
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", required=True, help="directory for the fetched .gitleaks.toml copies and survey.json")
    ap.add_argument("--repo", action="append", default=[], help="survey only this repository (repeatable)")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        for repo in args.repo or REPOS:
            rows.append(survey(repo, out_dir))
    except ApiError as exc:
        print(exc, file=sys.stderr)
        return 1
    with open(out_dir / "survey.json", "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, default=str)
    for row in rows:
        print(json.dumps(row, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
