#!/usr/bin/env python3
"""Drift detection for juniper editable installs across the conda environments.

A juniper package installed with ``pip install -e <path>`` records its source
path in ``<pkg>.dist-info/direct_url.json`` (PEP 610). When that path is a git
worktree that is later removed, the editable install ORPHANS: ``importlib`` /
``importlib.metadata`` still report the package, but ``import <pkg>`` fails
because the editable finder points at a directory that no longer exists. This
is the recurring failure mode behind on-host environment bit-rot (orphaned
editable installs after worktree cleanup).

This checker reads the ``direct_url.json`` files directly from each
environment's site-packages — it does NOT invoke the environment's interpreter,
so it still works when that interpreter is itself broken (which is exactly when
the drift bites). Each juniper editable install is classified:

  FRESH            target directory exists and is not inside a git worktree
  WORKTREE_PINNED  target exists but lives under a ``worktrees`` path — it will
                   orphan when that worktree is removed (soft warning)
  ORPHANED         target directory is missing — ``import`` is broken (drift)

With ``--fix`` the tool re-points ORPHANED installs (and, with
``--fix-worktree-pinned``, WORKTREE_PINNED ones) to the canonical source repo
discovered under the ecosystem root — the non-worktree checkout whose
``pyproject.toml`` ``[project].name`` matches — via
``<env>/bin/python -m pip install -e <repo> --no-deps --force-reinstall``.
``--dry-run`` prints the plan without running pip.

Exit codes
----------
0   No ORPHANED installs (clean, or only soft WORKTREE_PINNED warnings).
1   At least one ORPHANED install (or, with --strict, any WORKTREE_PINNED).
2   Invocation error (no environments found).

Project: juniper-ml
Sub-Project: on-host environment hygiene tooling
Author: Paul Calnon
Created: 2026-06-16
Status: permanent utility (graduates immediately to ``util/``)
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

try:
    import tomllib  # Python >= 3.11 (juniper-ml requires >= 3.12)
except ModuleNotFoundError:  # pragma: no cover - regex fallback below
    tomllib = None  # type: ignore[assignment]

DEFAULT_CONDA_DIR = os.environ.get("JUNIPER_CONDA_DIR", "/opt/miniforge3")
DEFAULT_ECOSYSTEM_ROOT = os.environ.get(
    "JUNIPER_ECOSYSTEM_ROOT", "/home/pcalnon/Development/python/Juniper"
)
DEFAULT_ENV_GLOB = "Juniper*"
JUNIPER_PREFIX = "juniper"

STATUS_FRESH = "FRESH"
STATUS_WORKTREE = "WORKTREE_PINNED"
STATUS_ORPHANED = "ORPHANED"

# Directory names never descended into when discovering a package's canonical
# source. ``worktrees`` (centralized) and ``.claude`` (session worktrees live in
# ``.claude/worktrees/``) are excluded so a worktree copy is never treated as
# canonical; the rest are noise that only slows the walk.
_SKIP_DIRS = {
    "worktrees", ".claude", ".git", "backups", "juniper-legacy",
    "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".mypy_cache", ".pytest_cache", "site-packages",
}


@dataclass(frozen=True)
class EditableFinding:
    """Classification of a single juniper editable install in one environment."""

    env: str
    package: str
    target: str
    status: str  # FRESH | WORKTREE_PINNED | ORPHANED
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "env": self.env,
            "package": self.package,
            "target": self.target,
            "status": self.status,
            "detail": self.detail,
        }


def normalize(name: str) -> str:
    """PEP 503-ish normalization (enough to compare juniper dist names)."""
    return name.strip().lower().replace("_", "-")


# ── discovery ───────────────────────────────────────────────────────────────


def discover_envs(conda_dir: Path, env_filter: list[str] | None,
                  include_deprecated: bool = False) -> list[Path]:
    envs_root = conda_dir / "envs"
    if not envs_root.is_dir():
        return []
    if env_filter:  # an explicit --env wins, deprecated names included
        wanted = set(env_filter)
        return sorted(d for d in envs_root.iterdir() if d.is_dir() and d.name in wanted)

    def keep(name: str) -> bool:
        if not fnmatch.fnmatch(name, DEFAULT_ENV_GLOB):
            return False
        # *-DEPRECATED envs are intentionally dead; their drift is expected noise.
        return include_deprecated or "DEPRECATED" not in name.upper()

    return sorted(d for d in envs_root.iterdir() if d.is_dir() and keep(d.name))


def site_packages_dirs(env_dir: Path) -> list[Path]:
    # Covers cpython (python3.13) and free-threaded (python3.14t) layouts.
    return sorted(env_dir.glob("lib/python*/site-packages"))


def _read_dist_name(dist_info: Path) -> str | None:
    meta = dist_info / "METADATA"
    if meta.is_file():
        for line in meta.read_text(errors="replace").splitlines():
            if line.startswith("Name:"):
                return line.split(":", 1)[1].strip()
            if line == "":  # end of the RFC-822 header block
                break
    stem = dist_info.name
    if stem.endswith(".dist-info"):
        stem = stem[: -len(".dist-info")]
    return stem.rsplit("-", 1)[0] if "-" in stem else None


def editable_installs(site_pkgs: Path) -> Iterator[tuple[str, str]]:
    """Yield (dist_name, target_path) for every editable install in site_pkgs."""
    for direct_url in site_pkgs.glob("*.dist-info/direct_url.json"):
        try:
            data = json.loads(direct_url.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or not data.get("dir_info", {}).get("editable"):
            continue
        url = data.get("url", "")
        if not url.startswith("file://"):
            continue
        name = _read_dist_name(direct_url.parent)
        if name:
            yield name, url[len("file://"):]


def classify(target: str) -> tuple[str, str]:
    path = Path(target)
    inside_worktree = "worktrees" in path.parts
    exists = path.is_dir()
    if inside_worktree:
        if exists:
            return STATUS_WORKTREE, "target exists but is inside a git worktree (re-orphans when removed)"
        return STATUS_ORPHANED, "target worktree no longer exists"
    if not exists:
        return STATUS_ORPHANED, "target directory does not exist"
    return STATUS_FRESH, "stable (non-worktree) checkout"


def collect(conda_dir: Path, env_filter: list[str] | None,
            include_deprecated: bool = False) -> list[EditableFinding]:
    findings: list[EditableFinding] = []
    for env_dir in discover_envs(conda_dir, env_filter, include_deprecated):
        seen: set[str] = set()
        for site_pkgs in site_packages_dirs(env_dir):
            for name, target in editable_installs(site_pkgs):
                norm = normalize(name)
                if not norm.startswith(JUNIPER_PREFIX) or norm in seen:
                    continue
                seen.add(norm)
                status, detail = classify(target)
                findings.append(EditableFinding(env_dir.name, norm, target, status, detail))
    findings.sort(key=lambda f: (f.env, f.package))
    return findings


# ── canonical-source discovery (for --fix) ──────────────────────────────────


def _pyproject_name(pyproject: Path) -> str | None:
    try:
        if tomllib is not None:
            with pyproject.open("rb") as handle:
                data = tomllib.load(handle)
            name = data.get("project", {}).get("name")
            if isinstance(name, str):
                return name
        for line in pyproject.read_text(errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("name") and "=" in stripped:
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        return None
    return None


def _walk_pyprojects(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        if "pyproject.toml" in filenames:
            yield Path(dirpath) / "pyproject.toml"


def discover_canonical(pkg_name: str, ecosystem_root: Path) -> tuple[Path | None, list[Path]]:
    """Return (unique_canonical_dir_or_None, all_candidate_dirs) for pkg_name."""
    want = normalize(pkg_name)
    candidates = sorted({
        py.parent for py in _walk_pyprojects(ecosystem_root)
        if (n := _pyproject_name(py)) and normalize(n) == want
    })
    return (candidates[0] if len(candidates) == 1 else None), candidates


def env_python(conda_dir: Path, env_name: str) -> Path:
    return conda_dir / "envs" / env_name / "bin" / "python"


def build_fix_plan(findings, ecosystem_root, include_worktree):
    targets = {STATUS_ORPHANED} | ({STATUS_WORKTREE} if include_worktree else set())
    plan = []
    for finding in findings:
        if finding.status not in targets:
            continue
        canonical, candidates = discover_canonical(finding.package, ecosystem_root)
        plan.append({
            "env": finding.env,
            "package": finding.package,
            "from": finding.target,
            "canonical": str(canonical) if canonical else None,
            "candidates": [str(c) for c in candidates],
            "resolvable": canonical is not None,
        })
    return plan


def run_fix(plan, conda_dir: Path, dry_run: bool):
    results = []
    for item in plan:
        if not item["resolvable"]:
            reason = ("no canonical source found" if not item["candidates"]
                      else f"ambiguous: {len(item['candidates'])} candidates")
            results.append({**item, "action": "SKIP", "reason": reason})
            continue
        cmd = [str(env_python(conda_dir, item["env"])), "-m", "pip", "install",
               "-e", item["canonical"], "--no-deps", "--force-reinstall", "-q"]
        if dry_run:
            results.append({**item, "action": "DRY_RUN", "cmd": cmd})
            continue
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            results.append({**item, "action": "FIXED", "cmd": cmd})
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", "") or str(exc)
            results.append({**item, "action": "ERROR", "cmd": cmd, "error": detail.strip()[:500]})
    return results


# ── reporting ───────────────────────────────────────────────────────────────


def summary(findings) -> dict[str, int]:
    counts = {STATUS_FRESH: 0, STATUS_WORKTREE: 0, STATUS_ORPHANED: 0}
    for finding in findings:
        counts[finding.status] = counts.get(finding.status, 0) + 1
    counts["total"] = len(findings)
    return counts


def print_report(findings, fix_results) -> None:
    print("Juniper editable-install drift report")
    print()
    if not findings:
        print("  (no juniper editable installs found)")
    else:
        print(f"  {'ENV':<16} {'PACKAGE':<26} {'STATUS':<16} TARGET")
        print(f"  {'─' * 16} {'─' * 26} {'─' * 16} {'─' * 40}")
        for f in findings:
            print(f"  {f.env:<16} {f.package:<26} {f.status:<16} {f.target}")
    counts = summary(findings)
    print()
    print(f"  {counts['total']} editable install(s): "
          f"{counts[STATUS_FRESH]} FRESH, {counts[STATUS_WORKTREE]} WORKTREE_PINNED, "
          f"{counts[STATUS_ORPHANED]} ORPHANED")
    if fix_results:
        print()
        print("  --fix:")
        for r in fix_results:
            line = f"    [{r['action']:<7}] {r['env']}/{r['package']}"
            if r.get("canonical"):
                line += f" -> {r['canonical']}"
            if r.get("reason"):
                line += f"  ({r['reason']})"
            print(line)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    conda_dir = Path(args.conda_dir)
    ecosystem_root = Path(args.ecosystem_root)

    if not discover_envs(conda_dir, args.env, args.include_deprecated):
        print(f"ERROR: no environments found under {conda_dir}/envs "
              f"(filter={args.env or DEFAULT_ENV_GLOB!r})", file=sys.stderr)
        return 2

    findings = collect(conda_dir, args.env, args.include_deprecated)

    fix_results = None
    if args.fix:
        plan = build_fix_plan(findings, ecosystem_root, args.fix_worktree_pinned)
        fix_results = run_fix(plan, conda_dir, args.dry_run)
        if not args.dry_run:
            findings = collect(conda_dir, args.env, args.include_deprecated)  # re-scan

    if args.json:
        out: dict[str, Any] = {"findings": [f.as_dict() for f in findings],
                               "summary": summary(findings)}
        if fix_results is not None:
            out["fix"] = fix_results
        print(json.dumps(out, indent=2))
    else:
        print_report(findings, fix_results)

    counts = summary(findings)
    if counts[STATUS_ORPHANED] > 0:
        return 1
    if args.strict and counts[STATUS_WORKTREE] > 0:
        return 1
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="editable_install_drift_check.py",
        description=("Detect (and optionally repair) drifted juniper editable installs "
                     "across the Juniper conda environments."),
    )
    p.add_argument("--conda-dir", default=DEFAULT_CONDA_DIR,
                   help=f"conda/miniforge install dir (default: {DEFAULT_CONDA_DIR})")
    p.add_argument("--env", action="append", metavar="NAME",
                   help=f"restrict to this environment (repeatable); default: all "
                        f"matching {DEFAULT_ENV_GLOB!r}")
    p.add_argument("--ecosystem-root", default=DEFAULT_ECOSYSTEM_ROOT,
                   help=f"root for --fix canonical-source discovery "
                        f"(default: {DEFAULT_ECOSYSTEM_ROOT})")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    p.add_argument("--include-deprecated", action="store_true",
                   help="also scan *-DEPRECATED environments (skipped by default)")
    p.add_argument("--strict", action="store_true",
                   help="also fail (exit 1) on WORKTREE_PINNED installs")
    p.add_argument("--fix", action="store_true",
                   help="re-point ORPHANED installs to their canonical source repo")
    p.add_argument("--fix-worktree-pinned", action="store_true",
                   help="with --fix, also re-point WORKTREE_PINNED installs")
    p.add_argument("--dry-run", action="store_true",
                   help="with --fix, print the pip commands without running them")
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
