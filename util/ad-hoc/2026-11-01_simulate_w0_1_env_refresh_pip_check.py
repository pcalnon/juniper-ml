#!/usr/bin/env python3
"""Simulate pip check's Juniper lines for JuniperCascor1 before and after a proposed W0.1 environment refresh, without installing anything.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-01
Status: ad-hoc — one-off (grounds the W0.1 option put to the owner on 2026-11-01)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/recurrence_env_preflight.bash (the check this predicts); juniper-recurrence AGENTS.md
         § "Host environment the experiment launchers actually serve from" (the W0.1 recipe)

Why
---
W0.1's service-core half (notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md)
installs juniper-service-core editable into JuniperCascor1. That env's other editable installs carry metadata from
their last install (recurrence 0.5.0, model 0.3.0, data-client 0.5.0) while the primary checkouts hold newer code, so
util/recurrence_env_preflight.bash evaluates stale pins. A wider refresh re-installs those editables with --no-deps,
which rewrites their metadata, and a refreshed requirement can collide with an old install still in the env. The
preflight refuses on any pip-check line that names a closure distribution, so the collision has to be predicted
before the owner is asked to run anything.

The script reads installed metadata through importlib.metadata and the refreshed packages' pyproject.toml files,
then evaluates every base requirement (markers evaluated with no extra) against the simulated installed set. It
installs nothing and writes nothing. Run it with the env's own interpreter and -s, so ~/.local cannot mask a gap:

Usage
-----
    PYTHONDONTWRITEBYTECODE=1 /opt/miniforge3/envs/JuniperCascor1/bin/python -s util/ad-hoc/2026-11-01_simulate_w0_1_env_refresh_pip_check.py

Exit 0 always (it reports; it gates nothing).
"""

import importlib.metadata as md
import re
import tomllib
from pathlib import Path

from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.utils import canonicalize_name
from pip._vendor.packaging.version import Version

JUNIPER = str(Path.home() / "Development" / "python" / "Juniper")

# The proposed refresh: distribution -> (pyproject.toml, _version.py when the version is dynamic).
REFRESH = {
    "juniper-service-core": (f"{JUNIPER}/juniper-ml/juniper-service-core/pyproject.toml", None),
    "juniper-observability": (f"{JUNIPER}/juniper-ml/juniper-observability/pyproject.toml", None),
    "juniper-recurrence-model": (
        f"{JUNIPER}/juniper-recurrence/juniper-recurrence-model/pyproject.toml",
        f"{JUNIPER}/juniper-recurrence/juniper-recurrence-model/juniper_recurrence_model/_version.py",
    ),
    "juniper-recurrence": (
        f"{JUNIPER}/juniper-recurrence/juniper-recurrence/pyproject.toml",
        f"{JUNIPER}/juniper-recurrence/juniper-recurrence/juniper_recurrence/_version.py",
    ),
    "juniper-recurrence-client": (
        f"{JUNIPER}/juniper-recurrence/juniper-recurrence-client/pyproject.toml",
        f"{JUNIPER}/juniper-recurrence/juniper-recurrence-client/juniper_recurrence_client/_version.py",
    ),
    "juniper-data-client": (f"{JUNIPER}/juniper-data-client/pyproject.toml", None),
}

# The preflight's closure (util/recurrence_env_preflight.bash CLOSURE), canonical names.
CLOSURE = {
    "juniper-recurrence",
    "juniper-recurrence-model",
    "juniper-recurrence-client",
    "juniper-service-core",
    "juniper-observability",
    "juniper-data-client",
    "juniper-model-core",
}


def installed_state():
    """Return {canonical name: (version, [requirement strings])} for every distribution importlib can see."""
    state = {}
    for dist in md.distributions():
        state[canonicalize_name(dist.metadata["Name"])] = (dist.version, list(dist.requires or []))
    return state


def refreshed_state(base, names):
    """Return a copy of ``base`` with each named distribution replaced by its checkout's version and base dependencies."""
    state = dict(base)
    for name in names:
        pyproject, version_file = REFRESH[name]
        with open(pyproject, "rb") as fh:
            project = tomllib.load(fh)["project"]
        version = project.get("version")
        if not isinstance(version, str):
            with open(version_file, encoding="utf-8") as fh:
                version = re.search(r'^__version__\s*=\s*"([^"]+)"', fh.read(), re.M).group(1)
        state[canonicalize_name(name)] = (version, list(project.get("dependencies", [])))
    return state


def conflicts(state):
    """Return the base-requirement conflicts in ``state`` that name a Juniper distribution, as (closure?, text)."""
    found = []
    for name, (version, requirements) in sorted(state.items()):
        for text in requirements:
            req = Requirement(text)
            if req.marker and not req.marker.evaluate({"extra": ""}):
                continue
            dep = canonicalize_name(req.name)
            if not (dep.startswith("juniper") or name.startswith("juniper")):
                continue
            in_closure = name in CLOSURE or dep in CLOSURE
            if dep not in state:
                found.append((in_closure, f"{name} {version} requires {req}, which is not installed"))
            elif req.specifier and not req.specifier.contains(Version(state[dep][0]), prereleases=True):
                found.append((in_closure, f"{name} {version} has requirement {req}, but you have {dep} {state[dep][0]}"))
    return found


def report(label, state):
    """Print one state's conflicts, marking those the preflight would count as findings."""
    found = conflicts(state)
    findings = sum(1 for in_closure, _ in found if in_closure)
    print(f"== {label}: {len(found)} Juniper conflict(s), {findings} the preflight would count")
    for in_closure, text in found:
        print(f"   {'FINDING ' if in_closure else 'unrelated'}  {text}")


def main():
    base = installed_state()
    report("BEFORE (as installed)", base)
    report("AFTER service-core only (recipe step 2)", refreshed_state(base, ["juniper-service-core"]))
    widened = refreshed_state(base, list(REFRESH))
    report("AFTER widened refresh (all six)", widened)
    for name in REFRESH:
        print(f"   after: {name} {widened[canonicalize_name(name)][0]}")


if __name__ == "__main__":
    main()
