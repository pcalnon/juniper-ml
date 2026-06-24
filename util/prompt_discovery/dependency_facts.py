"""dependency_facts: pyproject extras + version, plus ports/env from the parent AGENTS.md.

Kills invented versions / ports / env-var names by surfacing the real ``pyproject.toml``
``[project.optional-dependencies]`` surface and ``[project].version``, and the ecosystem
service-port / env table from the parent ``AGENTS.md`` (which may be absent in a single-repo
CI checkout -- that slice then degrades to ``unavailable``).
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

_KNOWN_ENV = {"JUNIPER_DATA_URL", "JUNIPER_DATA_API_KEY", "CASCOR_SERVICE_URL", "CASCOR_LOG_LEVEL"}


def _pyproject(repo_root: str) -> dict:
    path = Path(repo_root) / "pyproject.toml"
    if not path.exists() or tomllib is None:
        return {"status": "unavailable", "version": None, "extras": {}}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {"status": "unavailable", "version": None, "extras": {}}
    proj = data.get("project", {}) or {}
    extras = {k: list(v) for k, v in (proj.get("optional-dependencies", {}) or {}).items()}
    return {"status": "ok", "version": proj.get("version"), "extras": extras}


def _ports_env(repo_root: str) -> dict:
    parent = Path(repo_root).parent / "AGENTS.md"
    if not parent.exists():
        return {"status": "unavailable", "ports": {}, "env_vars": []}
    text = parent.read_text(encoding="utf-8", errors="replace")
    ports = {}
    for match in re.finditer(r"juniper-([a-z][a-z-]*).{0,40}?\b(8\d{3})\b", text):
        ports.setdefault(match.group(1), int(match.group(2)))
    env_vars = sorted({tok for tok in re.findall(r"\b[A-Z][A-Z0-9_]{3,}\b", text)} & _KNOWN_ENV)
    return {"status": "ok", "ports": ports, "env_vars": env_vars}


def probe(repo_root: str) -> dict:
    py = _pyproject(repo_root)
    pe = _ports_env(repo_root)
    return {
        "status": "ok" if py["status"] == "ok" else "partial",
        "version": py["version"],
        "extras": py["extras"],
        "ports": pe["ports"],
        "env_vars": pe["env_vars"],
        "ports_env_status": pe["status"],
    }
