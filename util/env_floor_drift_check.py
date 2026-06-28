#!/usr/bin/env python3
"""Environment floor-drift checker (gap I-2): are the juniper-* packages installed
in a conda environment at or above the version floors the target repo's
``pyproject.toml`` declares?

Motivation. The canopy "green tests / dead app" incident was a juniper client
wheel installed BELOW the floor its pyproject required. The existing drift tools
miss this exact case -- ``util/prompt_discovery/dependency_facts.py`` reads
*declared* pins (not what is installed) and ``util/editable_install_drift_check.py``
only inspects EDITABLE installs (``direct_url.json``), never a plain wheel's
version. This checker reads every installed distribution's ``Version`` straight
from its ``*.dist-info/METADATA`` -- it does NOT invoke the environment's
interpreter, so it still works when that interpreter is itself broken (which is
exactly when the drift bites) -- and compares against the floors.

Each juniper-* floor the target repo declares is classified:

  OK           installed version >= the declared floor
  BELOW_FLOOR  installed version <  the declared floor   (the I-2 failure mode)
  MISSING      the package is not installed in the environment

Env selection NEVER hardcodes an environment name (design 5.7 / the I-2 review):

  --site-packages PATH   scan this site-packages dir directly (repeatable)
  --env NAME             resolve <conda-dir>/envs/<NAME>/lib/python*/site-packages
  (neither given)        resolve the env from
                         prompts/agent_templates/data/ecosystem.yaml by matching
                         conda_envs[].used_by to the target repo's [project].name

CI gate is STRUCTURAL ONLY. ubuntu CI has no conda environment, so
``tests/test_env_floor_drift_check.py`` drives a SYNTHETIC site-packages fixture
(dist-info METADATA files; no real pip / no real conda). Manual verification
against a real environment (run on the host, not in CI) -- pass the conda env
whose ecosystem.yaml ``used_by`` is the target repo, or omit --env to let the
tool resolve it from ecosystem.yaml:

  python util/env_floor_drift_check.py --repo-root ../juniper-canopy --env <conda-env>

Exit codes
----------
0   No BELOW_FLOOR (clean; a MISSING is a soft note unless --strict).
1   At least one BELOW_FLOOR (or, with --strict, any MISSING).
2   Invocation error (no site-packages resolved, or no juniper floors found).

Project: juniper-ml
Sub-Project: custom-agent suite / on-host environment hygiene tooling
Author: Paul Calnon
Created: 2026-06-27
Status: permanent utility
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python >= 3.11 (juniper-ml requires >= 3.12)
except ModuleNotFoundError:  # pragma: no cover - regex fallback below
    tomllib = None  # type: ignore[assignment]

try:
    from packaging.version import InvalidVersion, Version  # near-universal (pip depends on it)
except ModuleNotFoundError:  # pragma: no cover - tuple fallback below
    Version = None  # type: ignore[assignment]
    InvalidVersion = Exception  # type: ignore[assignment,misc]

DEFAULT_CONDA_DIR = os.environ.get("JUNIPER_CONDA_DIR", "/opt/miniforge3")
DEFAULT_ECOSYSTEM_DATA = "prompts/agent_templates/data/ecosystem.yaml"
JUNIPER_PREFIX = "juniper-"

STATUS_OK = "OK"
STATUS_BELOW = "BELOW_FLOOR"
STATUS_MISSING = "MISSING"

# A requirement line: name, optional [extras], then everything up to an env marker (`;`).
_REQ_RE = re.compile(r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?P<spec>[^;]*)")
# The lower bound within a specifier set (`>=X[,<Y]`); we only care about the floor.
_FLOOR_RE = re.compile(r">=\s*(?P<v>[0-9][A-Za-z0-9.\-+!]*)")


def normalize(name: str) -> str:
    """PEP 503-ish normalization (enough to compare juniper dist names)."""
    return name.strip().lower().replace("_", "-")


def _vtuple(v: str) -> tuple[int, ...]:
    """Leading numeric release of a version as an int tuple (packaging-free fallback)."""
    head = re.split(r"[^0-9.]", v, maxsplit=1)[0]
    parts = [int(p) for p in head.split(".") if p.isdigit()]
    return tuple(parts) or (0,)


def version_lt(a: str, b: str) -> bool:
    """True when version ``a`` is strictly below version ``b``.

    Uses ``packaging.version`` when available for both operands; if EITHER fails
    to parse, both fall back to a numeric-tuple comparison so the two operands are
    never compared across types.
    """
    if Version is not None:
        try:
            return Version(a) < Version(b)
        except InvalidVersion:
            pass
    return _vtuple(a) < _vtuple(b)


@dataclass(frozen=True)
class FloorFinding:
    """Classification of one declared juniper-* floor against the installed env."""

    package: str
    floor: str
    installed: "str | None"
    status: str  # OK | BELOW_FLOOR | MISSING

    def as_dict(self) -> dict[str, Any]:
        return {"package": self.package, "floor": self.floor, "installed": self.installed, "status": self.status}


# ── floor extraction (target repo's pyproject) ───────────────────────────────


def _pyproject_data(pyproject: Path) -> dict:
    if tomllib is not None:
        try:
            with pyproject.open("rb") as handle:
                return tomllib.load(handle)
        except (OSError, ValueError):
            return {}
    return {}


def _project_name(pyproject: Path) -> "str | None":
    data = _pyproject_data(pyproject)
    name = data.get("project", {}).get("name")
    if isinstance(name, str):
        return name
    # Regex fallback for the no-tomllib case.
    try:
        for line in pyproject.read_text(errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("name") and "=" in stripped:
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        return None
    return None


def parse_floor(req: str) -> "tuple[str, str] | None":
    """Return ``(normalized_name, floor)`` for a juniper-* requirement with a ``>=``
    lower bound, else ``None`` (non-juniper, a self-extra reference, or no floor)."""
    m = _REQ_RE.match(req or "")
    if not m:
        return None
    name = normalize(m.group("name"))
    if not name.startswith(JUNIPER_PREFIX):
        return None
    fm = _FLOOR_RE.search(m.group("spec") or "")
    if not fm:
        return None
    return name, fm.group("v")


def declared_floors(pyproject: Path) -> dict[str, str]:
    """Highest juniper-* ``>=`` floor declared across ``[project].dependencies`` and
    every ``[project.optional-dependencies]`` extra (the meta-package keeps them in
    extras). The self-package and floorless / extra-only refs are skipped."""
    data = _pyproject_data(pyproject)
    project = data.get("project", {}) if isinstance(data, dict) else {}
    self_name = normalize(project.get("name", "")) if isinstance(project.get("name"), str) else ""

    reqs: list[str] = list(project.get("dependencies", []) or [])
    for deps in (project.get("optional-dependencies", {}) or {}).values():
        reqs.extend(deps or [])

    floors: dict[str, str] = {}
    for req in reqs:
        parsed = parse_floor(req if isinstance(req, str) else "")
        if not parsed:
            continue
        name, floor = parsed
        if name == self_name:  # the meta-package's own [all] self-reference
            continue
        if name not in floors or version_lt(floors[name], floor):
            floors[name] = floor  # keep the most restrictive (highest) floor
    return floors


# ── installed-version reading (env site-packages, interpreter-free) ──────────


def _read_name_version(meta: Path) -> "tuple[str | None, str | None]":
    name = ver = None
    try:
        for line in meta.read_text(errors="replace").splitlines():
            if line == "":  # end of the RFC-822 header block
                break
            if line.startswith("Name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("Version:"):
                ver = line.split(":", 1)[1].strip()
    except OSError:
        return None, None
    return name, ver


def installed_juniper_versions(site_dirs: list[Path]) -> dict[str, str]:
    """Map normalized juniper-* dist name -> highest installed version found across
    the given site-packages dirs (read straight from ``*.dist-info/METADATA``)."""
    found: dict[str, str] = {}
    for sp in site_dirs:
        for meta in sp.glob("*.dist-info/METADATA"):
            name, ver = _read_name_version(meta)
            if not name or not ver:
                continue
            norm = normalize(name)
            if not norm.startswith(JUNIPER_PREFIX):
                continue
            if norm not in found or version_lt(found[norm], ver):
                found[norm] = ver
    return found


def classify(floors: dict[str, str], installed: dict[str, str]) -> list[FloorFinding]:
    findings: list[FloorFinding] = []
    for pkg in sorted(floors):
        floor = floors[pkg]
        have = installed.get(pkg)
        if have is None:
            status = STATUS_MISSING
        elif version_lt(have, floor):
            status = STATUS_BELOW
        else:
            status = STATUS_OK
        findings.append(FloorFinding(pkg, floor, have, status))
    return findings


# ── env / site-packages resolution ───────────────────────────────────────────


def site_packages_for_env(conda_dir: Path, env_name: str) -> list[Path]:
    """site-packages dirs for a named conda env (cpython + free-threaded layouts)."""
    return sorted((conda_dir / "envs" / env_name).glob("lib/python*/site-packages"))


def _load_ecosystem_envs(data_path: Path) -> dict[str, str]:
    """Map ``used_by`` package -> conda env name from ecosystem.yaml (empty on any
    failure -- PyYAML missing, file absent, or malformed; the caller degrades)."""
    try:
        import yaml  # noqa: PLC0415 - optional, only this resolution path needs it
    except ModuleNotFoundError:
        return {}
    try:
        data = yaml.safe_load(data_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    out: dict[str, str] = {}
    for env_name, meta in (data.get("conda_envs", {}) or {}).items():
        used_by = (meta or {}).get("used_by") if isinstance(meta, dict) else None
        if isinstance(used_by, str):
            out[normalize(used_by)] = env_name
    return out


def resolve_site_dirs(args: argparse.Namespace, repo_root: Path) -> "tuple[list[Path], str]":
    """Resolve the site-packages dirs to scan and a human label for them.

    Precedence: explicit --site-packages, then --env, then the ecosystem.yaml
    used_by mapping for the target repo's package. Returns ([], reason) when
    nothing resolves so the caller can exit 2 with that reason.
    """
    if args.site_packages:
        dirs = [Path(p) for p in args.site_packages]
        existing = [d for d in dirs if d.is_dir()]
        if not existing:
            return [], f"no --site-packages dir exists: {', '.join(args.site_packages)}"
        return existing, "site-packages: " + ", ".join(str(d) for d in existing)

    conda_dir = Path(args.conda_dir)
    if args.env:
        dirs: list[Path] = []
        for env_name in args.env:
            dirs.extend(site_packages_for_env(conda_dir, env_name))
        if not dirs:
            return [], f"no site-packages under {conda_dir}/envs for env(s): {', '.join(args.env)}"
        return dirs, "env(s): " + ", ".join(args.env)

    # ecosystem.yaml resolution: find the env whose used_by matches this repo's package.
    pkg = normalize(_project_name(repo_root / "pyproject.toml") or "")
    if not pkg:
        return [], f"cannot read [project].name from {repo_root / 'pyproject.toml'} (pass --env or --site-packages)"
    data_path = repo_root / DEFAULT_ECOSYSTEM_DATA
    if not data_path.is_file():
        data_path = Path(__file__).resolve().parents[1] / DEFAULT_ECOSYSTEM_DATA
    env_for = _load_ecosystem_envs(data_path)
    env_name = env_for.get(pkg)
    if not env_name:
        return [], f"no conda env maps to '{pkg}' in {data_path} (pass --env or --site-packages)"
    dirs = site_packages_for_env(conda_dir, env_name)
    if not dirs:
        return [], f"ecosystem env '{env_name}' has no site-packages under {conda_dir}/envs"
    return dirs, f"env '{env_name}' (ecosystem.yaml used_by={pkg})"


# ── reporting ─────────────────────────────────────────────────────────────────


def summary(findings: list[FloorFinding]) -> dict[str, int]:
    counts = {STATUS_OK: 0, STATUS_BELOW: 0, STATUS_MISSING: 0}
    for f in findings:
        counts[f.status] = counts.get(f.status, 0) + 1
    counts["total"] = len(findings)
    return counts


def print_report(findings: list[FloorFinding], label: str) -> None:
    print("Juniper environment floor-drift report")
    print(f"  scanned: {label}")
    print()
    if not findings:
        print("  (no juniper-* floors declared in the target pyproject)")
    else:
        print(f"  {'PACKAGE':<28} {'FLOOR':<12} {'INSTALLED':<12} STATUS")
        print(f"  {'─' * 28} {'─' * 12} {'─' * 12} {'─' * 12}")
        for f in findings:
            print(f"  {f.package:<28} {f.floor:<12} {(f.installed or '-'):<12} {f.status}")
    c = summary(findings)
    print()
    print(f"  {c['total']} floor(s): {c[STATUS_OK]} OK, {c[STATUS_BELOW]} BELOW_FLOOR, {c[STATUS_MISSING]} MISSING")


def main(argv: "list[str] | None" = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root)
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        print(f"ERROR: no pyproject.toml at {pyproject}", file=sys.stderr)
        return 2

    floors = declared_floors(pyproject)
    if not floors:
        print(f"ERROR: no juniper-* version floors declared in {pyproject}", file=sys.stderr)
        return 2

    site_dirs, label = resolve_site_dirs(args, repo_root)
    if not site_dirs:
        print(f"ERROR: {label}", file=sys.stderr)
        return 2

    installed = installed_juniper_versions(site_dirs)
    findings = classify(floors, installed)

    if args.json:
        import json
        print(json.dumps({"repo_root": str(repo_root), "scanned": label,
                          "findings": [f.as_dict() for f in findings], "summary": summary(findings)}, indent=2))
    else:
        print_report(findings, label)

    counts = summary(findings)
    if counts[STATUS_BELOW] > 0:
        return 1
    if args.strict and counts[STATUS_MISSING] > 0:
        return 1
    return 0


def parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="env_floor_drift_check.py",
        description="Detect juniper-* packages installed below the floors the target repo's pyproject declares.",
    )
    p.add_argument("--repo-root", default=".", help="target repo whose pyproject floors are the requirement (default: .)")
    p.add_argument("--site-packages", action="append", metavar="DIR",
                   help="scan this site-packages dir directly (repeatable); wins over --env")
    p.add_argument("--env", action="append", metavar="NAME",
                   help="conda env name to resolve under --conda-dir (repeatable)")
    p.add_argument("--conda-dir", default=DEFAULT_CONDA_DIR,
                   help=f"conda/miniforge install dir (default: {DEFAULT_CONDA_DIR})")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    p.add_argument("--strict", action="store_true", help="also fail (exit 1) on MISSING packages")
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
