#!/usr/bin/env python3
"""Apply the V26 lenses' fixes (and session 12's own) to COPIES of ruling 26's six frozen sets (flood-4 session 12).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (the fix pass before ruling 26's six PRs land; tmp/flood4/session12/r26/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 26); juniper-canopy#814;
    prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_flood4-session11-r55-and-record-update-landed-ruling-26-built-and-validated-landing-next.md
    (item 2); session 11's sets and lens outputs under tmp/flood4/session11/r26/

For each of the six repositories, copies session 11's set (--s11/<repo>/{final/,texts/,paths.txt,base.txt,EVIDENCE.txt})
to --out/<repo>/, seeds any new file named by --seed REPO:PATH=FILE (also appended to paths.txt), then applies every
--fixes file in the order given. A fix is {id?, repo, path, old, new}; ``path`` is relative to <repo>/ (texts/...,
final/... or EVIDENCE.txt). Each OLD must occur exactly once in the text as it stands then, or the script stops,
except in a file passed with --dup-ok: there a fix whose OLD is absent and whose NEW is already present is recorded
as already-applied (the code lens's T1a-T1f repeat the claims lens's T3). Then the session link in every PR body and
commit body is swapped (--session-old -> --session-new, exactly once each), every PR body must end with the two
attribution lines and every commit body with its two trailers, byte for byte, and final.sha256 is written in
paths.txt's order. Session 11's files are only read. The script runs no git and writes only under --out.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r26_fixpass.py --s11 DIR --out DIR --session-old URL --session-new URL \
        [--seed REPO:PATH=FILE ...] --fixes JSON [--fixes JSON ...] [--final-fixes JSON ...] [--dup-ok JSON ...]
Files apply in the order: every --fixes, then every --final-fixes, then every --dup-ok.
Writes <out>/<repo>/applied.json per repository and <out>/FIXPASS.txt. Exit 0 when every fix applied (or, in a
--dup-ok file, was already applied) and every ending check passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPOS = ["juniper-data", "juniper-cascor", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-canopy"]
COPIED = ["paths.txt", "base.txt", "EVIDENCE.txt"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--s11", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--session-old", required=True)
    parser.add_argument("--session-new", required=True)
    parser.add_argument("--seed", action="append", default=[], help="REPO:PATH=FILE, a new file of the set")
    parser.add_argument("--fixes", type=Path, action="append", default=[])
    parser.add_argument("--final-fixes", type=Path, action="append", default=[], help="as --fixes, but each path is relative to <repo>/final/ (the code lens's code_fixes_proposed.json)")
    parser.add_argument("--dup-ok", type=Path, action="append", default=[])
    args = parser.parse_args()
    pr_end = "\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)\n\n" + args.session_new + "\n"
    commit_end = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: " + args.session_new + "\n"

    report: list[str] = []
    applied: dict[str, list[dict]] = {repo: [] for repo in REPOS}
    for repo in REPOS:
        src, dst = args.s11 / repo, args.out / repo
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src / "final", dst / "final")
        shutil.copytree(src / "texts", dst / "texts")
        for name in COPIED:
            shutil.copyfile(src / name, dst / name)
    for spec in args.seed:
        repo, rest = spec.split(":", 1)
        rel, local = rest.split("=", 1)
        target = args.out / repo / "final" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local, target)
        with (args.out / repo / "paths.txt").open("a", encoding="utf-8") as fh:
            fh.write(rel + "\n")
        report.append(f"seeded {repo}:{rel} from {local} ({_sha(target)[:12]})")

    ok = True
    for fixes_file in [*args.fixes, *args.final_fixes, *args.dup_ok]:
        dup_ok = fixes_file in args.dup_ok
        prefix = "final/" if fixes_file in args.final_fixes else ""
        fixes = json.loads(fixes_file.read_text(encoding="utf-8"))
        for index, fix in enumerate(fixes):
            fid = fix.get("id") or f"{fixes_file.stem}#{index}"
            fix = {**fix, "path": prefix + fix["path"]}
            target = args.out / fix["repo"] / fix["path"]
            text = target.read_text(encoding="utf-8")
            n_old, n_new = text.count(fix["old"]), text.count(fix["new"])
            if n_old == 1:
                target.write_text(text.replace(fix["old"], fix["new"], 1), encoding="utf-8")
                status = "applied"
            elif dup_ok and n_old == 0 and n_new >= 1:
                status = "already-applied"
            else:
                status = f"REFUSED (old occurs {n_old} times, new {n_new})"
                ok = False
            applied[fix["repo"]].append({"id": fid, "source": fixes_file.name, "path": fix["path"], "status": status})
            report.append(f"{fix['repo']:22} {fid:34} {fix['path']:45} {status}")

    for repo in REPOS:
        texts = args.out / repo / "texts"
        for name, ending in (("pr_body.md", pr_end), ("commit_body.txt", commit_end)):
            path = texts / name
            text = path.read_text(encoding="utf-8")
            if text.count(args.session_old) != 1:
                report.append(f"{repo:22} {name}: session link occurs {text.count(args.session_old)} times -- REFUSED")
                ok = False
                continue
            text = text.replace(args.session_old, args.session_new, 1)
            path.write_text(text, encoding="utf-8")
            if not text.endswith(ending):
                report.append(f"{repo:22} {name}: ending check FAILED")
                ok = False
            else:
                report.append(f"{repo:22} {name}: session link swapped, ending exact")
        rels = [line.strip() for line in (args.out / repo / "paths.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
        sums = [f"{_sha(args.out / repo / 'final' / rel)}  {rel}" for rel in rels]
        (args.out / repo / "final.sha256").write_text("\n".join(sums) + "\n", encoding="utf-8")
        (args.out / repo / "applied.json").write_text(json.dumps(applied[repo], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report.append(f"{repo:22} final.sha256: {len(sums)} files")

    report.append("RESULT: " + ("OK" if ok else "REFUSALS ABOVE"))
    (args.out / "FIXPASS.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
