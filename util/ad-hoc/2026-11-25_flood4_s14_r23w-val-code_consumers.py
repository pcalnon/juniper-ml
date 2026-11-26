"""
Scan consumer clones for every read of juniper-service-core's WebSocket tier that ruling 23's fix could change.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

For each repository directory under ECO_DIR: its HEAD commit (read from the clone's metadata), and every line in a
.py/.js/.ts/.tsx/.toml/.cfg/.txt/.yml/.yaml file (tests included, marked) that matches one of the patterns below.

Usage:
  python -I <this file> ECO_DIR --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

PATTERNS = {
    "imports_sc_websocket": r"juniper_service_core\.websocket|from juniper_service_core import [^\n]*(WebSocketManager|websocket)|juniper_service_core\s+import\s+websocket",
    "sc_handlers": r"control_stream_handler|training_stream_handler|worker_stream_handler|build_websocket_router|websocket_router",
    "manager_api": r"\b(WebSocketManager|ws_manager)\b",
    "transport_stats": r"transport_stats|unserializable_messages_total|dropped_connections|send_failures|active_connections|pending_connections|endpoint_counts",
    "connection_counts": r"connection_count|_per_ip_counts|max_connections_per_ip|connect_pending|promote_to_active",
    "control_acks": r"command_ack|control_ack|command_id|create_control_ack_message|/ws/control",
    "sc_dependency": r"juniper-service-core|juniper_service_core",
}
SUFFIXES = {".py", ".js", ".ts", ".tsx", ".toml", ".cfg", ".txt", ".yml", ".yaml", ".lock"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".mypy_cache"}


def head_of(repo: pathlib.Path) -> str:
    meta = repo / ".git"
    head = (meta / "HEAD").read_text().strip()
    if head.startswith("ref: "):
        ref = head[5:]
        ref_file = meta / ref
        if ref_file.exists():
            return f"{ref} {ref_file.read_text().strip()}"
        packed = meta / "packed-refs"
        if packed.exists():
            for line in packed.read_text().splitlines():
                if line.endswith(" " + ref):
                    return f"{ref} {line.split()[0]}"
        return ref
    return head


def walk(repo: pathlib.Path):
    for path in repo.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(repo).parts):
            continue
        if path.is_file() and path.suffix in SUFFIXES:
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("eco", type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    compiled = {k: re.compile(v) for k, v in PATTERNS.items()}
    result = {}
    for repo in sorted(p for p in args.eco.iterdir() if (p / ".git").exists()):
        hits: dict[str, list] = {k: [] for k in PATTERNS}
        for path in walk(repo):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(path.relative_to(repo))
            is_test = "/tests/" in f"/{rel}" or rel.startswith("tests/") or "test_" in path.name
            for lineno, line in enumerate(text.splitlines(), 1):
                for key, rx in compiled.items():
                    if rx.search(line):
                        hits[key].append({"file": rel, "line": lineno, "test": is_test, "text": line.strip()[:220]})
        result[repo.name] = {"head": head_of(repo), "counts": {k: len(v) for k, v in hits.items()}, "hits": hits}
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    for name, data in result.items():
        print(name, data["head"], json.dumps(data["counts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
