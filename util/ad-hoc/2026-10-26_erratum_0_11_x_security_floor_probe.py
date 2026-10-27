#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-26_erratum_0_11_x_security_floor_probe.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Grounds the 2026-10-26 erratum to the juniper-ml 0.11.1 / 0.11.2 / 0.11.3
#   security notes in PUBLISHED metadata, not a checkout. For each juniper-ml
#   release from 0.10.0 it reads `requires_dist` from PyPI, resolves the
#   extras a user names ([servers], [tools], [all], [servers]+[tools]) to the
#   Juniper members they request, then reads each member's published
#   `requires_dist` at the lowest version the floor admits. It reports, per
#   install shape:
#     - which members floor juniper-observability>=0.4.1 and
#       juniper-service-core>=0.7.1 with no extra marker the install does not
#       request (the two shared security patches);
#     - the juniper-cascor floor, since cascor's OWN fixes (#689, #710,
#       APIKeyAuth checking every key) first ship in 0.12.0.
#   "Lowest version the floor admits" is the question a security note answers:
#   which environments can a release still leave exposed.
#
# Usage:
#   python3 -I util/ad-hoc/2026-10-26_erratum_0_11_x_security_floor_probe.py
#
# Exit codes: 0 when every expectation in EXPECT holds; 1 otherwise.
# -----------------------------------------------------------------------------
"""Probe the published floors behind the 0.11.x security-notes erratum."""

import json
import sys
import urllib.request

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

ML_VERSIONS = ["0.10.0", "0.11.0", "0.11.1", "0.11.2", "0.11.3"]
SHAPES = {
    "[servers]": {"servers"},
    "[servers]+[tools]": {"servers", "tools"},
    "[tools]": {"tools"},
    "[all]": {"all"},
}
PATCHES = {"juniper-observability": Version("0.4.1"), "juniper-service-core": Version("0.7.1")}
CASCOR_OWN_FIXES = Version("0.12.0")

_cache: dict = {}


def pypi(name: str, version: str | None = None) -> dict:
    key = (name, version)
    if key not in _cache:
        url = f"https://pypi.org/pypi/{name}/{version}/json" if version else f"https://pypi.org/pypi/{name}/json"
        with urllib.request.urlopen(url, timeout=60) as resp:  # nosec B310 -- fixed https PyPI URL
            _cache[key] = json.load(resp)
    return _cache[key]


def lowest_admitted(name: str, spec: SpecifierSet) -> str | None:
    releases = sorted((Version(v) for v, files in pypi(name)["releases"].items() if files), key=lambda v: v)
    for v in releases:
        if not v.is_prerelease and v in spec:
            return str(v)
    return None


def requested(reqs: list[Requirement], extras: set[str]) -> list[Requirement]:
    """Requirements an install of `extras` applies, expanding self-references such as [all] -> juniper-ml[servers,...]."""
    out, seen, todo = [], set(), set(extras)
    while todo:
        extra = todo.pop()
        if extra in seen:
            continue
        seen.add(extra)
        for r in reqs:
            if r.marker is not None and not r.marker.evaluate({"extra": extra}):
                continue
            if r.name == "juniper-ml":
                todo |= set(r.extras)
            else:
                out.append(r)
    return out


def patch_floors(name: str, version: str, member_extras: set[str]) -> dict[str, bool]:
    """Does this member release floor each shared patch for an install that requests `member_extras`?"""
    found = {p: False for p in PATCHES}
    envs = [{"extra": e} for e in sorted(member_extras)] or [{"extra": ""}]
    for raw in pypi(name, version)["info"].get("requires_dist") or []:
        r = Requirement(raw)
        if r.name not in PATCHES:
            continue
        if r.marker is not None and not any(r.marker.evaluate(env) for env in envs):
            continue
        lows = [Version(s.version) for s in r.specifier if s.operator in (">=", "==", "~=")]
        if lows and max(lows) >= PATCHES[r.name]:
            found[r.name] = True
    return found


def main() -> int:
    rows = {}
    for ml in ML_VERSIONS:
        reqs = [Requirement(x) for x in pypi("juniper-ml", ml)["info"].get("requires_dist") or []]
        for shape, extras in SHAPES.items():
            members = requested(reqs, extras)
            via: dict[str, list[str]] = {p: [] for p in PATCHES}
            cascor_floor = None
            for r in members:
                low = lowest_admitted(r.name, r.specifier)
                if low is None:
                    continue
                if r.name == "juniper-cascor":
                    cascor_floor = low
                floors = patch_floors(r.name, low, set(r.extras))
                if r.name in PATCHES:
                    floors[r.name] = Version(low) >= PATCHES[r.name]
                label = f"{r.name}{'[' + ','.join(sorted(r.extras)) + ']' if r.extras else ''} {low}"
                for patch, floored in floors.items():
                    if floored:
                        via[patch].append(label)
            exposed = cascor_floor is not None and Version(cascor_floor) < CASCOR_OWN_FIXES
            both = all(via.values())
            rows[(ml, shape)] = (via, both, cascor_floor, exposed)
            cascor_txt = "NO " if exposed else "yes" if cascor_floor else "n/a"
            print(f"{ml:7} {shape:18} both-patches={'yes' if both else 'NO '} cascor floor={cascor_floor or '-':7} cascor-own-fixes={cascor_txt}")
            for patch, labels in via.items():
                print(f"{'':27}{patch} via: {', '.join(labels) or 'nothing'}")

    # The erratum's claims, as checks against what was just read.
    EXPECT = {
        "0.11.0 [servers] carries both patches through canopy 0.9.0": rows[("0.11.0", "[servers]")][1] and all(any(x.startswith("juniper-canopy") for x in v) for v in rows[("0.11.0", "[servers]")][0].values()),
        "0.10.0 [servers] does not carry them": not rows[("0.10.0", "[servers]")][1],
        "0.11.1 [all] can still hold cascor 0.11.0": rows[("0.11.1", "[all]")][3],
        "0.11.1 [servers]+[tools] can still hold cascor 0.11.0": rows[("0.11.1", "[servers]+[tools]")][3],
        "0.11.2 [all] floors cascor 0.12.0": not rows[("0.11.2", "[all]")][3],
        "0.11.2 [servers] floors cascor 0.12.0": not rows[("0.11.2", "[servers]")][3],
        "0.11.0 [tools] does not carry them": not rows[("0.11.0", "[tools]")][1],
        "0.11.1 [tools] carries them": rows[("0.11.1", "[tools]")][1],
        "0.11.0 [all] already carries them (0.11.1's [all] advice adds nothing)": rows[("0.11.0", "[all]")][1],
    }
    print()
    bad = 0
    for claim, ok in EXPECT.items():
        print(("PASS " if ok else "FAIL ") + claim)
        bad += not ok
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
