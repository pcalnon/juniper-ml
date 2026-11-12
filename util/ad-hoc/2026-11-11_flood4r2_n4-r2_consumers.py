#!/usr/bin/env python3
"""
Census: what each Juniper repository imports from juniper_service_core on its current main, and whether it reaches the WebSocket tier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (the consumer section of the N-4 round-2 texts)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11);
         juniper-service-core/juniper_service_core/websocket/

Usage::

    python3 <this file> --ecosystem-root <dir holding the sibling primaries> --out <json> [--repo <name> ...]

For each repository it reads GitHub's ``main`` head (``gh api repos/<owner>/<repo>/commits/main``), fetches ``origin``
in the sibling primary (a plain fetch: no prune, no unshallow, and nothing in the working tree, index or HEAD is
touched) and requires ``origin/main`` to equal GitHub's head. It then parses, with ``ast``, every ``*.py`` at
``origin/main`` that mentions ``juniper_service_core`` and records exactly which names are imported from the package
(``from juniper_service_core[.x] import a, b``, ``import juniper_service_core[.x] [as y]`` and the attributes read off
such an alias), which other mentions exist (a patched dotted path in a string, say), and where the package is
declared as a dependency. A repository reaches the WebSocket tier when it imports ``juniper_service_core.websocket``
or one of the names the package's top level re-exports from it.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

OWNER = "pcalnon"
REPOS = ["juniper-cascor", "juniper-canopy", "juniper-data", "juniper-recurrence", "juniper-cascor-worker", "juniper-cascor-client", "juniper-data-client", "juniper-deploy", "juniper-harcot"]
PACKAGE = "juniper_service_core"
#: What juniper_service_core/__init__.py re-exports lazily from its websocket sub-package.
WEBSOCKET_NAMES = {
    "CommandExecutor",
    "LifecycleCommandExecutor",
    "ReplayOutOfRange",
    "WebSocketManager",
    "attach_websocket",
    "attach_worker_pool",
    "build_websocket_router",
    "build_worker_router",
    "control_stream_handler",
    "training_stream_handler",
    "worker_stream_handler",
    "ws_authenticate",
}


def _out(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    done = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    return done.returncode, done.stdout


def _imports(source: str) -> tuple[list[str], list[str]]:
    """Names imported from the package in one file, and any that reach its WebSocket tier."""
    tree = ast.parse(source)
    names: set[str] = set()
    reach: set[str] = set()
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and (node.module == PACKAGE or node.module.startswith(PACKAGE + ".")):
            for alias in node.names:
                label = alias.name if node.module == PACKAGE else f"{node.module[len(PACKAGE) + 1 :]}.{alias.name}"
                names.add(label)
                if ".websocket" in "." + node.module[len(PACKAGE) :] or alias.name in WEBSOCKET_NAMES or alias.name == "websocket":
                    reach.add(label)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == PACKAGE or alias.name.startswith(PACKAGE + "."):
                    names.add(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
                    aliases.add(alias.asname or alias.name.split(".")[0])
                    if ".websocket" in alias.name:
                        reach.add(alias.name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
            names.add(f"<alias>.{node.attr}")
            if node.attr in WEBSOCKET_NAMES or node.attr == "websocket":
                reach.add(f"<alias>.{node.attr}")
    return sorted(names), sorted(reach)


def _census(root: Path, repo: str) -> dict:
    primary = root / repo
    row: dict = {"repo": repo}
    rc, head = _out(["gh", "api", f"repos/{OWNER}/{repo}/commits/main", "--jq", ".sha"])
    row["github_main"] = head.strip() if rc == 0 else None
    if not (primary / ".git").exists():
        row["error"] = "no sibling primary"
        return row
    row["fetch_exit"] = _out(["git", "-C", str(primary), "fetch", "origin"])[0]
    row["origin_main"] = _out(["git", "-C", str(primary), "rev-parse", "origin/main"])[1].strip()
    row["origin_main_is_github_main"] = row["origin_main"] == row["github_main"]
    listing = _out(["git", "-C", str(primary), "grep", "-l", "-e", PACKAGE, "-e", PACKAGE.replace("_", "-"), "origin/main", "--"])[1]
    files = sorted(line.split(":", 1)[1] for line in listing.splitlines() if ":" in line)
    per_file: dict[str, list[str]] = {}
    reach: dict[str, list[str]] = {}
    other: list[str] = []
    for rel in files:
        if not rel.endswith(".py"):
            other.append(rel)
            continue
        source = _out(["git", "-C", str(primary), "show", f"origin/main:{rel}"])[1]
        names, reaches = _imports(source)
        if names:
            per_file[rel] = names
        else:
            other.append(rel)
        if reaches:
            reach[rel] = reaches
    source_files = {rel: names for rel, names in per_file.items() if "/tests/" not in "/" + rel and not Path(rel).name.startswith("test_")}
    row["files_mentioning_the_package"] = len(files)
    row["python_files_importing_it"] = len(per_file)
    row["source_files_importing_it"] = sorted(source_files)
    row["imports_in_source"] = sorted({name for names in source_files.values() for name in names})
    row["imports_in_tests_only"] = sorted({name for rel, names in per_file.items() if rel not in source_files for name in names} - set(row["imports_in_source"]))
    row["imports_by_file"] = per_file
    row["mentions_without_an_import"] = other
    row["reaches_the_websocket_tier"] = reach
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--ecosystem-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repo", action="append")
    args = parser.parse_args()
    rows = [_census(args.ecosystem_root.resolve(), repo) for repo in (args.repo or REPOS)]
    args.out.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{row['repo']:24s} main {str(row.get('github_main'))[:8]} origin==github {row.get('origin_main_is_github_main')} source files {len(row.get('source_files_importing_it', []))} reaches-ws {bool(row.get('reaches_the_websocket_tier'))} imports {row.get('imports_in_source')}")
    return 0 if all(row.get("origin_main_is_github_main") for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
