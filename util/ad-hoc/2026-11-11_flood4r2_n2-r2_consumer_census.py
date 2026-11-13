#!/usr/bin/env python3
"""Consumer census: does any sibling repository's main use juniper-service-core's lifecycle manager or routes?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-11
Status:      ad-hoc -- one-off (round 2 of the N-2 carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race: who a new 409 on start can reach)

For each sibling repository (a directory beside the juniper-ml primary checkout), fetches
``origin main`` (a fetch only: no checkout, no prune, nothing unshallowed) and greps the fetched
commit's Python files for the names a consumer of the lifecycle would have to use:
``juniper_service_core.lifecycle`` / ``.routes`` / ``.websocket.commands``,
``ServiceLifecycleManager``, ``LifecycleStateMachine``, ``build_routers``,
``LifecycleCommandExecutor`` and ``TrainingInterrupted``. It also lists every name the repository
imports from ``juniper_service_core`` at all, read with ``ast`` from each file that names the
package (so a parenthesised import over several lines is read whole). Prints one JSON object.

A hit is a line to read, not a verdict: a repository may define its own class of the same name
(juniper-cascor has its own ``TrainingInterrupted`` and its own lifecycle manager).

Exit status: 0 when every repository was read; 2 when one could not be fetched or is missing.

Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-11_flood4r2_n2-r2_consumer_census.py [--repo <name> ...]
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPOS = ("juniper-canopy", "juniper-cascor", "juniper-data", "juniper-recurrence")
LIFECYCLE_NAMES = r"juniper_service_core\.(lifecycle|routes|websocket\.commands)|ServiceLifecycleManager|LifecycleStateMachine|build_routers|LifecycleCommandExecutor|TrainingInterrupted"


def _ecosystem_root() -> Path:
    """The directory that holds the primary checkouts: two levels above the shared git directory."""
    common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return Path(common.stdout.strip()).parent.parent


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)


def _census(repo: Path) -> dict:
    row: dict = {"repo": repo.name}
    if not (repo / ".git").exists():
        row["error"] = "not a checkout"
        return row
    fetched = _git(repo, "fetch", "origin", "main")
    if fetched.returncode != 0:
        row["error"] = f"fetch failed: {fetched.stderr.strip()[-200:]}"
        return row
    sha = _git(repo, "rev-parse", "FETCH_HEAD").stdout.strip()
    row["main_sha"] = sha
    row["main_committed"] = _git(repo, "log", "-1", "--format=%cI", sha).stdout.strip()
    files = _git(repo, "ls-tree", "-r", "--name-only", sha).stdout.split("\n")
    row["python_files"] = sum(1 for name in files if name.endswith(".py"))
    hits = _git(repo, "grep", "-n", "-E", LIFECYCLE_NAMES, sha, "--", "*.py", "*.md")
    row["lifecycle_name_hits"] = [line.split(":", 1)[1] for line in hits.stdout.splitlines()]
    users = _git(repo, "grep", "-l", "juniper_service_core", sha, "--", "*.py").stdout.splitlines()
    names: dict[str, set[str]] = {}
    plain: set[str] = set()
    unparsed = []
    for entry in users:
        path = entry.split(":", 1)[1]
        try:
            tree = ast.parse(_git(repo, "show", f"{sha}:{path}").stdout)
        except SyntaxError:
            unparsed.append(path)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "juniper_service_core":
                names.setdefault(node.module, set()).update(alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                plain.update(alias.name for alias in node.names if alias.name.split(".")[0] == "juniper_service_core")
    row["files_naming_juniper_service_core"] = len(users)
    row["imports_from_juniper_service_core"] = {module: sorted(found) for module, found in sorted(names.items())}
    row["plain_imports"] = sorted(plain)
    row["unparsed_files"] = unparsed
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", action="append", help=f"a sibling repository directory name (default: {', '.join(DEFAULT_REPOS)})")
    args = parser.parse_args(argv)
    root = _ecosystem_root()
    rows = [_census(root / name) for name in (args.repo or DEFAULT_REPOS)]
    print(json.dumps({"repositories": rows}, indent=1))
    return 2 if any("error" in row for row in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
