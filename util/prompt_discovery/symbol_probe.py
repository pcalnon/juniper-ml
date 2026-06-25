"""symbol_probe: resolve named symbols to a def ``file:line`` + signature line.

A standalone, path-invoked helper cannot call the Serena MCP tools, so this probe resolves
symbols with a grep-based closed-world search (``def``/``class``/assignment). The richer
Serena ``find_symbol`` / ``find_declaration`` resolution is a Skill-layer enrichment (the
Skill runs in the main loop, which has MCP access) that can overlay these facts. Either way
the bundle records ``resolved`` with a concrete location or ``unresolved`` -- it never
invents an API (design S5.6).
"""

from __future__ import annotations

import re

from _util import run


def _resolve_one(repo_root: str, name: str) -> dict:
    pattern = r"^\s*(def|class)\s+" + re.escape(name) + r"\b|^\s*" + re.escape(name) + r"\s*[:=]"
    rc, out, _ = run(["git", "-C", repo_root, "grep", "-nE", "--", pattern])
    if rc not in (0, 1):
        rc, out, _ = run(["grep", "-rnE", "--", pattern, repo_root])
    for line in out.splitlines():
        parts = line.split(":", 2)
        if len(parts) >= 3 and parts[1].isdigit():
            return {"status": "resolved", "definition": f"{parts[0]}:{parts[1]}", "signature": parts[2].strip()[:200]}
    return {"status": "unresolved", "definition": None, "signature": None}


def probe(repo_root: str, symbols) -> dict:
    names = symbols or []
    return {"status": "ok", "symbols": {n: _resolve_one(repo_root, n) for n in names}}
