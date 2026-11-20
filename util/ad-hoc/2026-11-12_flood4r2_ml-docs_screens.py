#!/usr/bin/env python3
"""
Build an unsigned, never-pushed probe commit of the working tree and run CI's sequence-safety and structure screens on it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2);
         .github/workflows/ci.yml (the ``sequence-safety`` job and the markdown structure step)

The probe commit is made with ``git commit-tree`` from a throwaway index file under the scratch directory, so the
worktree's own index, HEAD and branch do not move, nothing is signed, and nothing is pushed. Its tree is the base
commit's tree with the working-tree copy of every path given. Then, against ``--base``:

* ``juniper-symbol-loss-check --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash'`` (CI's flags);
* ``juniper-docs-additions-check`` (CI's flags), and once more with ``--files`` naming every changed ``.md``, which
  is how ``util/fleet_triage/predict_merge.py`` runs it (a markdown file outside docs/ is then screened too);
* ``python3 util/markdown_structure_delta.py --base <base> --head <probe>`` (CI's step).

Each is run for its text and again with ``--json``; exit statuses and outputs go to one JSON report.

Usage: 2026-11-12_flood4r2_ml-docs_screens.py --base <ref> --scratch <dir> --out <json> <path> [<path> ...]
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SYMBOL_SCOPE = ["--scope", "tests/*.py", "--scope", "util/**/*.py", "--scope", "util/**/*.bash"]
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")


def run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(REPO), capture_output=True, text=True, errors="replace", check=False, env=env)


def must(args: list[str], env: dict[str, str] | None = None) -> str:
    proc = run(args, env)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} -> {proc.returncode}: {proc.stderr.strip()[:400]}")
    return proc.stdout.strip()


def probe_commit(base: str, paths: list[str], scratch: Path) -> tuple[str, str]:
    index = scratch / "probe.index"
    index.unlink(missing_ok=True)
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    base_sha = must(["git", "rev-parse", base])
    must(["git", "read-tree", base_sha], env)
    must(["git", "add", "--", *paths], env)
    tree = must(["git", "write-tree"], env)
    identity = {"GIT_AUTHOR_NAME": "docs-carrier probe", "GIT_AUTHOR_EMAIL": "probe@juniper.invalid", "GIT_COMMITTER_NAME": "docs-carrier probe", "GIT_COMMITTER_EMAIL": "probe@juniper.invalid"}
    commit = must(["git", "-c", "commit.gpgsign=false", "commit-tree", "--no-gpg-sign", tree, "-p", base_sha, "-m", "probe: flood-4 round-2 docs carrier (local, unsigned, never pushed)"], {**os.environ, **identity})
    index.unlink(missing_ok=True)
    return base_sha, commit


def heading_lines(text: str) -> list[str]:
    """Every line that starts like an ATX heading, fenced or not: a superset, so no changed heading can hide."""
    return [line for line in text.splitlines() if HEADING_RE.match(line)]


def heading_delta(base_sha: str, probe: str, path: str) -> dict:
    before = collections.Counter(heading_lines(must(["git", "show", f"{base_sha}:{path}"])))
    after = collections.Counter(heading_lines(must(["git", "show", f"{probe}:{path}"])))
    return {"path": path, "base_heading_lines": sum(before.values()), "probe_heading_lines": sum(after.values()), "missing_from_probe": sorted((before - after).elements()), "new_in_probe": sorted((after - before).elements())}


def screen(name: str, args: list[str]) -> dict:
    text = run(args)
    as_json = run([*args, "--json"])
    try:
        report = json.loads(as_json.stdout)
    except json.JSONDecodeError:
        report = None
    return {"name": name, "command": " ".join(args), "exit": text.returncode, "stdout": text.stdout[-6000:], "stderr": text.stderr[-2000:], "json_exit": as_json.returncode, "json": report}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Probe commit + CI's sequence-safety and structure screens.")
    parser.add_argument("--base", required=True)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    args.scratch.mkdir(parents=True, exist_ok=True)
    base_sha, probe = probe_commit(args.base, args.paths, args.scratch)
    changed = must(["git", "diff", "--name-status", base_sha, probe]).splitlines()
    markdown = [line.split("\t", 1)[1] for line in changed if line.split("\t", 1)[1].endswith(".md")]
    results = [
        screen("symbol-loss (CI flags)", ["juniper-symbol-loss-check", *SYMBOL_SCOPE, "--base", base_sha, "--head", probe]),
        screen("docs-additions (CI flags)", ["juniper-docs-additions-check", "--base", base_sha, "--head", probe]),
        screen("docs-additions (every changed .md, as predict_merge passes them)", ["juniper-docs-additions-check", "--base", base_sha, "--head", probe, "--files", *markdown]),
    ]
    delta = run([sys.executable, "util/markdown_structure_delta.py", "--base", base_sha, "--head", probe])
    headings = [heading_delta(base_sha, probe, path) for path in markdown if run(["git", "cat-file", "-e", f"{base_sha}:{path}"]).returncode == 0]
    report = {
        "repo": str(REPO),
        "base": base_sha,
        "probe_commit": probe,
        "probe_tree": must(["git", "rev-parse", f"{probe}^{{tree}}"]),
        "changed": changed,
        "screens": results,
        "markdown_structure_delta": {"command": f"python3 util/markdown_structure_delta.py --base {base_sha} --head {probe}", "exit": delta.returncode, "stdout": delta.stdout[-4000:], "stderr": delta.stderr[-2000:]},
        "headings": headings,
        "head_unchanged": must(["git", "rev-parse", "HEAD"]) == base_sha,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"base {base_sha[:8]} probe {probe[:8]} ({len(changed)} paths changed)")
    for item in results:
        findings = (item["json"] or {}).get("findings", [])
        tally: dict[str, int] = {}
        for finding in findings:
            tally[finding.get("severity", "?")] = tally.get(finding.get("severity", "?"), 0) + 1
        print(f"  {item['name']}: exit {item['exit']}  findings {tally}")
        for finding in findings:
            if finding.get("severity") == "FAIL":
                print(f"    FAIL {finding.get('path')} {finding.get('reason') or finding.get('verdict')} {json.dumps(finding.get('detail'))[:300]}")
    print(f"  markdown_structure_delta: exit {delta.returncode}  {delta.stdout.strip().splitlines()[-1] if delta.stdout.strip() else delta.stderr.strip()[-200:]}")
    changed_headings = 0
    for item in headings:
        changed_headings += len(item["missing_from_probe"])
        print(f"  headings {item['path']}: {item['base_heading_lines']} -> {item['probe_heading_lines']}; missing from the probe: {item['missing_from_probe']}; new: {len(item['new_in_probe'])}")
        for line in item["new_in_probe"]:
            print(f"      + {line}")
    return 0 if all(item["exit"] == 0 for item in results) and delta.returncode == 0 and changed_headings == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
