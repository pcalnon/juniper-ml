#!/usr/bin/env python3
"""
Open the PR that ships round 42's consolidated handoff, the register lane's own handoff, and that lane's uncommitted evidence.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use; wraps util/open_signed_pr.py
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Session 2fba4397 (worktree `fizzy-hugging-dream`) wrote two handoffs on 2026-09-24/25: its own
(`…ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`) and the consolidated one the
owner asked for (`…consolidated-both-lanes-validations-and-closes-pr-owed.md`), which merges it with the
follow-up lane's (juniper-ml#2097) and their predecessor (juniper-ml#2084). Both, their validation
reports, and the rest of the lane's uncommitted evidence ship together here.

The same worktree also holds juniper-ml#2089's files, untracked and byte-identical to that PR's head.
They must stay out: re-adding them would collide with #2089. So this names its files explicitly (plus
report globs under reports/, which cannot match #2089's paths) and refuses any path under #2089's tree.

Before opening anything it refuses when:
  * a file is missing, or is one of #2089's;
  * a file that exists on origin/main differs between HEAD and origin/main -- the upload is whole-file,
    so a stale base would silently revert whatever main changed since (run `git fetch` first);
  * an OPEN juniper-ml PR already touches one of the paths (read from the paginated REST file listing:
    `gh pr view/list --json files` stops at 100 files per PR);
  * a file carries the repository owner's configured email address (it is never printed).

`--dry-run` is forwarded to util/open_signed_pr.py.

Usage: python3 util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py --title T --message M --commit-body-file F --body-file B [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BRANCH = "docs/handoff-round42-consolidated"
REPORTS = "reports/2026-09-24_defect-register-round-42"
PROMPTS = "prompts/thread-handoff_automated-prompts"
FILES = [
    f"{PROMPTS}/HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md",
    f"{PROMPTS}/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md",
    "util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py",
    "util/ad-hoc/2026-09-24_archive_round42_reports.py",
    "util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py",
    "util/ad-hoc/2026-09-24_rebuild_round42_doc2_draft_0021z.py",
    f"{REPORTS}/owner-ruling-key-leaks-verbatim.md",
    f"{REPORTS}/data438-fixforward-pr-draft.md",
]
# Report globs: the data fix-forward's validation rounds, its executor's disposition report and its PR draft,
# every validation round of both handoffs, and the frozen handoff copies those rounds cite by line.
GLOBS = ["data438-fixforward-*.md", "handoff-2fba4397-round*-lane*.md", "handoff-consolidated-round*-lane*.md", "handoff-frozen/*.md"]
# juniper-ml#2089's paths.
PR2089 = (
    "util/ad-hoc/2026-09-24_round42_probes/",
    "util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py",
    "util/ad-hoc/2026-09-24_open_round42_session2fba4397_probes_pr.py",
    "util/ad-hoc/2026-09-24_push_round42_handoff_probes_to_2089.py",
)


def run(*cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


def blob(ref: str, path: str) -> str | None:
    r = run("git", "rev-parse", "--verify", "--quiet", f"{ref}:{path}")
    return r.stdout.strip() or None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    for flag in ("--title", "--message", "--commit-body-file", "--body-file"):
        ap.add_argument(flag, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = list(FILES)
    for g in GLOBS:
        files += sorted(str(p.relative_to(REPO)) for p in (REPO / REPORTS).glob(g) if p.is_file())
    files.append(str(Path(__file__).resolve().relative_to(REPO)))
    files = sorted(set(files))

    problems = [f"missing: {f}" for f in files if not (REPO / f).is_file()]
    problems += [f"#2089's path: {f}" for f in files if f.startswith(PR2089)]
    for f in files:
        on_main = blob("origin/main", f)
        if on_main is not None and blob("HEAD", f) != on_main:
            problems.append(f"stale base (HEAD and origin/main differ; the whole-file upload would revert main): {f}")

    # Every file of every open PR. `gh pr list/view --json files` stops at 100 files per PR (#2089 has
    # 132), so read the paginated REST listing instead.
    listing = run("gh", "pr", "list", "--repo", "pcalnon/juniper-ml", "--state", "open", "--limit", "200", "--json", "number")
    if listing.returncode != 0:
        problems.append(f"gh pr list failed: {listing.stderr.strip()}")
    else:
        wanted = set(files)
        for pr in json.loads(listing.stdout):
            got = run("gh", "api", "--paginate", f"repos/pcalnon/juniper-ml/pulls/{pr['number']}/files", "--jq", ".[].filename")
            if got.returncode != 0:
                problems.append(f"could not list the files of open PR #{pr['number']}: {got.stderr.strip()}")
                continue
            hit = wanted & set(got.stdout.split())
            if hit:
                problems.append(f"open PR #{pr['number']} already touches {sorted(hit)}")

    email = run("git", "config", "user.email").stdout.strip()
    if email:
        problems += [f"owner's email address found in: {f}" for f in files if (REPO / f).is_file() and email in (REPO / f).read_text(encoding="utf-8", errors="replace")]

    if problems:
        print("\n".join(problems))
        raise SystemExit(f"{len(problems)} problem(s); nothing opened")

    cmd = [sys.executable, str(REPO / "util/open_signed_pr.py"), "--repo", "juniper-ml", "--branch", BRANCH]
    for f in files:
        cmd += ["--add", f"{f}:{f}"]
    cmd += ["--message", args.message, "--commit-body-file", args.commit_body_file, "--title", args.title, "--body-file", args.body_file]
    if args.dry_run:
        cmd.append("--dry-run")
    print(f"{len(files)} files -> {BRANCH}")
    for f in files:
        print(f"  {f}")
    return subprocess.run(cmd, cwd=REPO).returncode


if __name__ == "__main__":
    raise SystemExit(main())
