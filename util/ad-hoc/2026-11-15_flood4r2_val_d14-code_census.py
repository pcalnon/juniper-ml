"""
Census, on the ten Juniper repositories' origin/main, of every caller of the resume API that D-14 changes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> --out <json path> [--no-fetch]
Fetches each sibling's origin (juniper-ml is read from the orchestrator worktree, already fetched), then runs
`git grep` against origin/main for four groups of patterns and writes every hit, tests and util included.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ORCHESTRATOR = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
SIBLINGS = (
    "juniper-cascor",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-canopy",
    "juniper-deploy",
    "juniper-recurrence",
    "juniper-harcot",
)
GROUPS = {
    "api_callers": r"replay_since|promote_to_active|replayed_through|ReplayOutOfRange",
    "resume_senders": r"[\"']type[\"'] *: *[\"']resume[\"']|type: *[\"']resume[\"']|last_seq",
    "tier_importers": r"juniper_service_core\.websocket|juniper_service_core import .*websocket|build_websocket_router|attach_websocket",
    "manager_forks": r"class +WebSocketManager|class +ConnectionManager",
}


def run(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=300, check=False)


def kind_of(path: str) -> str:
    lowered = path.lower()
    for marker, kind in (("test", "test"), ("util/", "util"), ("scripts/", "scripts"), ("notes/", "notes"), ("docs/", "docs"), ("prompts/", "prompts"), ("changelog", "changelog")):
        if marker in lowered:
            return kind
    if lowered.endswith(".md"):
        return "doc"
    return "code"


def census(repo: str, root: Path, fetch: bool) -> dict:
    out = {"root": str(root), "fetch_exit": None, "head": None, "groups": {}}
    if fetch:
        out["fetch_exit"] = run(["git", "fetch", "origin", "--quiet"], root).returncode
    head = run(["git", "rev-parse", "origin/main"], root)
    out["head"] = head.stdout.strip() if head.returncode == 0 else f"error: {head.stderr.strip()}"
    for name, pattern in GROUPS.items():
        res = run(["git", "grep", "-n", "-I", "-E", pattern, "origin/main", "--"], root)
        hits = []
        for line in res.stdout.splitlines():
            # origin/main:<path>:<line>:<text>
            _, _, rest = line.partition(":")
            path, _, rest = rest.partition(":")
            lineno, _, text = rest.partition(":")
            hits.append({"path": path, "line": lineno, "kind": kind_of(path), "text": text.strip()[:200]})
        out["groups"][name] = {"exit": res.returncode, "count": len(hits), "hits": hits}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-fetch", action="store_true")
    args = parser.parse_args()
    report = {"juniper-ml": census("juniper-ml", ORCHESTRATOR, fetch=False)}
    for repo in SIBLINGS:
        report[repo] = census(repo, JUNIPER / repo, fetch=not args.no_fetch)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    for repo, block in report.items():
        summary = ", ".join(f"{name}={group['count']}" for name, group in block["groups"].items())
        print(f"{repo}\t{block['head'][:8]}\tfetch={block['fetch_exit']}\t{summary}")
        for name in ("api_callers", "tier_importers", "manager_forks"):
            for hit in block["groups"][name]["hits"]:
                if hit["kind"] == "code":
                    print(f"    {name}\t{hit['path']}:{hit['line']}\t{hit['text'][:110]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
