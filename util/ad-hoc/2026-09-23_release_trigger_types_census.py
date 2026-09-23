#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-09-23_release_trigger_types_census.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-09-23
# Last Modified: 2026-09-23
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#    Census, read from each repo's remote `main`, of every workflow that a
#    `release` event can fire, and of the activity types it subscribes to.
#
#    Why: moving a repo's "Latest" badge (`gh release edit <tag> --latest`) is an
#    EDIT of a Release. A workflow that subscribes to `release` with no `types:`
#    filter, or with `edited` / `released` among its types, may fire on that edit
#    -- and in this ecosystem the release-triggered workflows publish to PyPI and
#    GHCR. The worker's two publishers were checked by hand on 2026-09-22
#    (`release: [published]` only). This checks the other repos before any badge
#    is moved there, instead of assuming they match.
#
#    Exit status: 0 when every release-triggered workflow subscribes to
#    `published` only; 1 when any subscribes to anything else, or to nothing
#    (no `types:` = every activity type); 2 when a repo or file could not be read,
#    because an unreadable workflow is not evidence that it is safe.
#
# Usage:
#    python3 util/ad-hoc/2026-09-23_release_trigger_types_census.py
#    python3 util/ad-hoc/2026-09-23_release_trigger_types_census.py --repo juniper-data
#####################################################################################################################################################################################################

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys

import yaml

OWNER = "pcalnon"
REPOS = (
    "juniper-ml",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-canopy",
    "juniper-recurrence",
    "juniper-deploy",
)
SAFE_TYPES = frozenset({"published"})


def gh_json(path: str):
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path}: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def release_types(doc) -> tuple[bool, list[str] | None]:
    """Return (subscribes_to_release, types). types None = no filter = every activity type."""
    if not isinstance(doc, dict):
        return False, None
    # PyYAML reads the bare key `on` as boolean True.
    on = doc.get("on", doc.get(True))
    if on is None:
        return False, None
    if isinstance(on, str):
        return (on == "release"), None
    if isinstance(on, list):
        return ("release" in on), None
    if isinstance(on, dict) and "release" in on:
        cfg = on["release"]
        if isinstance(cfg, dict) and cfg.get("types") is not None:
            types = cfg["types"]
            return True, [types] if isinstance(types, str) else [str(t) for t in types]
        return True, None
    return False, None


def census(repo: str) -> tuple[list[str], int]:
    lines: list[str] = []
    worst = 0
    try:
        listing = gh_json(f"repos/{OWNER}/{repo}/contents/.github/workflows")
    except RuntimeError as exc:
        return [f"{repo}: UNREADABLE workflow directory ({exc})"], 2
    for entry in listing:
        name = entry.get("name", "")
        if not name.endswith((".yml", ".yaml")):
            continue
        try:
            blob = gh_json(f"repos/{OWNER}/{repo}/contents/.github/workflows/{name}")
            text = base64.b64decode(blob["content"]).decode("utf-8")
            doc = yaml.safe_load(text)
        except Exception as exc:  # noqa: BLE001 -- any failure means "not proven safe"
            lines.append(f"{repo}/{name}: UNREADABLE ({exc})")
            worst = max(worst, 2)
            continue
        subscribes, types = release_types(doc)
        if not subscribes:
            continue
        if types is None:
            lines.append(f"{repo}/{name}: release with NO types filter -- every activity type, including edited")
            worst = max(worst, 1)
        elif set(types) <= SAFE_TYPES:
            lines.append(f"{repo}/{name}: release types {types} -- an edit fires nothing")
        else:
            lines.append(f"{repo}/{name}: release types {types} -- NOT published-only")
            worst = max(worst, 1)
    if not lines:
        lines.append(f"{repo}: no release-triggered workflow")
    return lines, worst


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", help="limit to this repo (repeatable)")
    args = parser.parse_args()
    worst = 0
    for repo in args.repo or REPOS:
        lines, code = census(repo)
        worst = max(worst, code)
        for line in lines:
            print(line)
    print(f"exit={worst}")
    return worst


if __name__ == "__main__":
    sys.exit(main())
