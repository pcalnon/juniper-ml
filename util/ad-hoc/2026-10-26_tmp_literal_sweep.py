#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-26_tmp_literal_sweep.py
# Author:        Paul Calnon
# Version:       0.3.0
#
# Date Created:  2026-10-26
# Last Modified: 2026-10-26
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#   Inventory every ``/tmp`` path literal across the Juniper repos, so the 2026-10-26 /tmp
#   remediation (no file is ever written under /tmp; each repo writes to its own gitignored
#   ``<repo>/tmp/``) knows what it has to change. Read-only: it runs ripgrep over each repo
#   directory and prints counts by repo and by file class, and, with --list CLASS, the hits.
#
#   File classes: code (py/bash/sh), config (toml/yaml/json/ini/units/Docker/Make), workflow
#   (.github/), agent (.claude/ skills, agents, settings, hooks), operative-doc (AGENTS.md,
#   CLAUDE.md, README, docs/, notes/ procedures and templates), record (every other notes/,
#   prompts/, reports/ file: what happened, which a remediation does not rewrite), scratch
#   (the repo's own gitignored tmp/).
#
#   Scope (the owner's revised ruling, 2026-10-26: a counting script chooses its scope
#   deliberately, never by .gitignore or a tool's defaults). By default the sweep searches
#   the repo with its own tmp/ excluded by an explicit root-anchored glob, so the exclusion
#   holds in a repo whose .gitignore does not name tmp/; a nested tmp/ is still searched.
#   --tmp-only searches the repo's tmp/ alone, every file under it whatever ignore files say,
#   and reports those hits as the scratch class. Nothing searches both.
#
# Usage:
#   python3 util/ad-hoc/2026-10-26_tmp_literal_sweep.py [--root DIR] [--list CLASS] [--repo NAME] [--tmp-only]
#####################################################################################################################################################################################################
import argparse
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Gate G-TMP's matcher (util/tmp_path_literal_check.py). The first version's lookbehind excluded `-` and it had
# no var/ or private/ form, so it never saw a ${TMPDIR:-...} fallback or a var/tmp path.
PATTERN = r"(?<![\w.~$})\]/])/(?:var/|private/)?tmp(?![\w-])"
SKIP_GLOBS = ["!.claude/worktrees/**", "!**/.venv*/**", "!**/node_modules/**", "!**/juniper-legacy/**", "!**/*.lock", "!**/*.ipynb"]
# The repo's own tmp/, anchored at the search root: measured with rg 15.1.0, "tmp/**" skips only the search root's
# tmp directory, while "tmp" and "tmp/" also skip a nested sub/tmp/, and "./tmp/**" matches nothing.
REPO_TMP_EXCLUDE = "!tmp/**"
CODE_EXT = {".py", ".bash", ".sh", ".zsh"}
CONFIG_EXT = {".toml", ".yml", ".yaml", ".json", ".ini", ".cfg", ".conf", ".service", ".timer", ".env", ".mk", ".txt"}
CONFIG_NAMES = {"Makefile", "Dockerfile", ".pre-commit-config.yaml", ".gitignore", ".dockerignore"}
RECORD_DIRS = ("notes/", "prompts/", "reports/")
OPERATIVE_NOTE = re.compile(r"(PROCEDURE|TEMPLATE|CONVENTION|README)", re.IGNORECASE)


def classify(rel: str) -> str:
    p = Path(rel)
    name = p.name
    if p.parts and p.parts[0] == "tmp":
        return "scratch"
    if rel.startswith(".github/"):
        return "workflow"
    if rel.startswith(".claude/") or "/.claude/" in rel:
        return "agent"
    if p.suffix in CODE_EXT:
        return "code"
    if p.suffix in CONFIG_EXT or name in CONFIG_NAMES or name.startswith("Dockerfile"):
        return "config"
    if name in {"AGENTS.md", "CLAUDE.md"} or rel.startswith("docs/") or "/docs/" in rel:
        return "operative-doc"
    if rel.startswith(RECORD_DIRS):
        if rel.startswith("notes/templates/") or OPERATIVE_NOTE.search(name):
            return "operative-doc"
        return "record"
    if name.upper().startswith("README"):
        return "operative-doc"
    return "other"


def sweep(repo: Path, tmp_only: bool = False):
    """Hits by repo-relative path. The scope is chosen here, never left to ignore files: the repo with its own
    tmp/ excluded (default), or that tmp/ alone (tmp_only). The two never overlap, so no hit is counted twice."""
    cmd = ["rg", "-n", "--no-messages", "--hidden", "-P", PATTERN]
    for g in SKIP_GLOBS:
        cmd += ["-g", g]
    cmd += ["-g", "!.git/**"]
    if tmp_only:
        if not (repo / "tmp").is_dir():
            return {}
        # Every file under the repo's tmp/: --no-ignore, so an ignore file inside a copy there hides nothing.
        cmd += ["--no-ignore", "tmp"]
    else:
        # The repo, its own tmp/ excluded by name; ripgrep's .gitignore handling is not what keeps tmp/ out.
        cmd += ["-g", REPO_TMP_EXCLUDE, "."]
    out = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=False).stdout
    hits = defaultdict(list)
    for line in out.splitlines():
        path, _, rest = line.partition(":")
        lineno, _, text = rest.partition(":")
        rel = path[2:] if path.startswith("./") else path
        hits[rel].append((int(lineno) if lineno.isdigit() else 0, text.strip()))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(Path.home() / "Development/python/Juniper"))
    ap.add_argument("--list", dest="list_class", default=None, help="print the hits of one class")
    ap.add_argument("--repo", default=None, help="limit to one repo directory name")
    ap.add_argument("--max-lines", type=int, default=400)
    ap.add_argument("--layout", action="store_true", help="report each repo's tmp/ directory and its ignore rules, then exit")
    ap.add_argument("--tmp-only", action="store_true", help="search each repo's tmp/ alone (default: the repo with its tmp/ excluded)")
    args = ap.parse_args()
    root = Path(args.root)
    repos = sorted(d for d in root.iterdir() if d.is_dir() and d.name.startswith("juniper-") and (d / ".git").exists())
    if args.repo:
        repos = [d for d in repos if d.name == args.repo]
    if args.layout:
        for repo in repos:
            t = repo / "tmp"
            entries = sorted(t.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True) if t.is_dir() else []
            tracked = subprocess.run(["git", "ls-files", "--", "tmp"], cwd=repo, capture_output=True, text=True, check=False).stdout.split()
            ignored = subprocess.run(["git", "check-ignore", "-v", "tmp/x"], cwd=repo, capture_output=True, text=True, check=False).stdout.strip()
            print(f"== {repo.name}: tmp/ {'exists' if t.is_dir() else 'ABSENT'}, {len(entries)} entries, {len(tracked)} tracked; ignore rule: {ignored or 'NONE'}")
            for p in entries[:4]:
                print(f"     {p.name}{'/' if p.is_dir() else ''}")
        return 0
    grand = Counter()
    printed = 0
    print("scope: " + ("each repo's tmp/ alone" if args.tmp_only else "each repo, its tmp/ excluded"))
    for repo in repos:
        hits = sweep(repo, args.tmp_only)
        files_by_class = Counter()
        lines_by_class = Counter()
        for rel, lst in hits.items():
            c = classify(rel)
            files_by_class[c] += 1
            lines_by_class[c] += len(lst)
            grand[c] += len(lst)
        gi = repo / ".gitignore"
        gi_tmp = gi.exists() and any(re.fullmatch(r"/?tmp/?(\*)?", ln.strip()) for ln in gi.read_text(errors="replace").splitlines())
        summary = " ".join(f"{c}={files_by_class[c]}f/{lines_by_class[c]}l" for c in sorted(files_by_class))
        print(f"{repo.name:24s} tmp_dir={'yes' if (repo / 'tmp').exists() else 'no ':3s} gitignore_tmp={'yes' if gi_tmp else 'no '} | {summary}")
        if args.list_class:
            for rel in sorted(hits):
                if classify(rel) != args.list_class:
                    continue
                for lineno, text in hits[rel]:
                    if printed >= args.max_lines:
                        break
                    print(f"    {repo.name}/{rel}:{lineno}: {text[:220]}")
                    printed += 1
    print("TOTAL lines by class: " + " ".join(f"{c}={n}" for c, n in sorted(grand.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
