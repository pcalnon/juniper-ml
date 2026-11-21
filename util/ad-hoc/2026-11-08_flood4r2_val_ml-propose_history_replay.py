#!/usr/bin/env python3
"""Replay the ml-propose carrier's docs/REFERENCE.md helpers over every past cut that moved the release sites.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (independent validation of the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507; the ml-propose carrier (util/release_train/propose.py step 5b-v)

For every commit (on ``--rev``'s first-parent history) that changed a line naming the "declares the following
pins" sentence, the "sets them to" clause or a compatibility-matrix row in docs/REFERENCE.md, this script:

* reads docs/REFERENCE.md at the commit's parent (BEFORE) and at the commit (AFTER), and pyproject.toml at both;
* runs the carrier's ``apply_reference_compat_cochanges(BEFORE, pyproject AFTER)`` (the module is imported from
  ``--propose-dir``, a directory holding the carrier's propose.py, detect.py and notes_render.py);
* compares the four release sites (Version cell, declares sentence, the matrix rows, the "sets them to" clause)
  of the replay against AFTER, and writes a unified diff of the Package Overview table and the Ecosystem
  Compatibility section (replay vs AFTER) per commit.

Every git call is a fixed argv run from ``--git-dir-cwd`` (this session's own worktree). Writes only under
``--out``. Read-only on every checkout.
"""

from __future__ import annotations

import argparse
import difflib
import importlib
import json
import re
import subprocess  # nosec B404 - fixed argv (git), no shell
import sys
import tomllib
from pathlib import Path

REF = "docs/REFERENCE.md"
PYPROJECT = "pyproject.toml"
_DECL = re.compile(r"`juniper-ml` (\d+\.\d+\.\d+) declares the following pins\.")
_SETS = re.compile(r"(\d+\.\d+\.\d+) sets them to ((?:`[^`]+`(?:, | and )?)+)")
_VCELL = re.compile(r"^\|\s*\*\*Version\*\*\s*\|\s*`([^`]+)`\s*\|", re.MULTILINE)


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False)  # nosec B603,B607 - fixed argv
    if proc.returncode != 0:
        return ""
    return proc.stdout


def section(text: str) -> str:
    """The Package Overview table plus the Ecosystem Compatibility section (to the next ## heading)."""
    lines = text.splitlines(keepends=True)
    out: list = []
    grab = False
    for line in lines:
        if re.match(r"^##\s+(Package Overview|Ecosystem Compatibility)\s*$", line.strip()):
            grab = True
            out.append(line)
            continue
        if grab and re.match(r"^##\s+", line):
            grab = False
        if grab:
            out.append(line)
    return "".join(out)


def matrix_rows(text: str) -> dict:
    rows: dict = {}
    in_sec = False
    header = None
    for line in text.splitlines():
        if re.match(r"^#{2,4}\s+Ecosystem Compatibility\s*$", line.strip()):
            in_sec = True
            continue
        if not in_sec:
            continue
        if line.startswith("#"):
            break
        if line.startswith("| juniper-ml |") and header is None:
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            continue
        if header is not None:
            if not line.startswith("|"):
                break
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            rows[cells[0]] = cells
    return {"header": header, "rows": rows}


def sites(text: str) -> dict:
    m = _SETS.findall(text)
    return {
        "version_cells": _VCELL.findall(text),
        "declares": _DECL.findall(text),
        "sets_them": [(v, re.findall(r"`([^`]+)`", body)) for v, body in m],
        "matrix": matrix_rows(text),
    }


def version_of(pyproject_text: str) -> "str | None":
    try:
        return tomllib.loads(pyproject_text)["project"]["version"]
    except Exception:  # noqa: BLE001 - a broken historical file is reported, not raised
        return None


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--git-dir-cwd", required=True)
    ap.add_argument("--rev", default="4bae7520")
    ap.add_argument("--propose-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra-commit", action="append", default=[])
    args = ap.parse_args(argv)
    cwd = Path(args.git_dir_cwd)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, args.propose_dir)
    pr = importlib.import_module("propose")

    shas: list = []
    for pattern in (r"declares the following pins", r"sets them to", r"^\| 0\.[0-9]+\.x "):
        log = git(cwd, "log", "--first-parent", "--format=%H", "-G", pattern, args.rev, "--", REF)
        for sha in log.split():
            if sha not in shas:
                shas.append(sha)
    for extra in args.extra_commit:
        full = git(cwd, "rev-parse", extra).strip()
        if full and full not in shas:
            shas.append(full)
    results = []
    for sha in shas:
        subject = git(cwd, "log", "-1", "--format=%ad %s", "--date=short", sha).strip()
        parent = git(cwd, "rev-parse", f"{sha}^").strip()
        before = git(cwd, "show", f"{parent}:{REF}")
        after = git(cwd, "show", f"{sha}:{REF}")
        py_before = git(cwd, "show", f"{parent}:{PYPROJECT}")
        py_after = git(cwd, "show", f"{sha}:{PYPROJECT}")
        replay, report = pr.apply_reference_compat_cochanges(before, py_after)
        s_after, s_replay, s_before = sites(after), sites(replay), sites(before)
        diff = "".join(difflib.unified_diff(section(after).splitlines(keepends=True), section(replay).splitlines(keepends=True), fromfile=f"AFTER {sha[:8]}", tofile=f"REPLAY {sha[:8]}"))
        real = "".join(difflib.unified_diff(section(before).splitlines(keepends=True), section(after).splitlines(keepends=True), fromfile=f"BEFORE {parent[:8]}", tofile=f"AFTER {sha[:8]}"))
        (out / f"{sha[:8]}_replay_vs_after.diff").write_text(diff, encoding="utf-8")
        (out / f"{sha[:8]}_real_before_vs_after.diff").write_text(real, encoding="utf-8")
        agree = {k: s_after[k] == s_replay[k] for k in ("version_cells", "declares", "sets_them", "matrix")}
        results.append(
            {
                "sha": sha[:8],
                "subject": subject,
                "pyproject_version": [version_of(py_before), version_of(py_after)],
                "report": {k: v for k, v in report.items()},
                "sites_before": s_before,
                "sites_after": s_after,
                "sites_replay": s_replay,
                "agree_with_after": agree,
                "section_diff_lines": sum(1 for ln in diff.splitlines() if ln[:1] in "+-" and not ln.startswith(("+++", "---"))),
            }
        )
    with open(out / "history_replay.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    for r in results:
        print(r["sha"], r["subject"][:90])
        print("   pyproject", r["pyproject_version"], "report", {k: r["report"][k] for k in ("version_cell", "declares", "matrix_row", "recurrence", "series")})
        print("   agree", r["agree_with_after"], "section diff lines", r["section_diff_lines"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
