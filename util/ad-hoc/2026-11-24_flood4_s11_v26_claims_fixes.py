#!/usr/bin/env python3
"""
Build, check and preview the V26 claims lens's exact text fixes for the six ruling-26 PRs (V26 claims lens).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 26 ports, session 11, validator V26 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (the validator's proposed text fixes, checked before they are handed over)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 26);
         juniper-canopy#814 (the model fix)

What it does
------------
Holds the fixes as data ({id, finding, repo, path, old, new, note}; ``path`` is relative to ``--r26``/<repo>/, so
``texts/pr_body.md`` or ``final/CHANGELOG.md``). For each target file it starts from the builder's copy (or, for a
``final/`` file the builder did not change, from ``--clones``/<repo>/<repo path>, i.e. main), applies its fixes in
order and refuses unless each old string occurs exactly once in the text as it stands then. It writes
``--out-json`` (the fix list) and a fixed preview of every target under ``--preview``/<repo>/<path>, and checks that
every PR body still ends with the two attribution lines and every commit body with its two trailers, byte for byte.
The builder's deliverables are never modified. Exit 1 on any refusal or failed ending check.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_claims_fixes.py --r26 DIR --clones DIR --out-json FILE --preview DIR
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PORTS = ["juniper-data", "juniper-cascor", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker"]
ALL = PORTS + ["juniper-canopy"]
PR_END = "\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)\n\nhttps://claude.ai/code/session_016H76AoqeiNVxwLUzh4N2rC\n"
COMMIT_END = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_016H76AoqeiNVxwLUzh4N2rC\n"

RECORD_OLD = "does not list ruling 26 yet: its §8 on juniper-ml `main` (`c93914a7`, read 2026-11-24) holds the rulings of 2026-11-08 and 2026-11-09."
RECORD_NEW = "lists it as ruling 26 in its §8."
#: T6's sentence is found in each PR body; the temp directory it names is reused in the replacement.
T6_MARK = "<T6: resolved from the PR body>"
T6_PATTERN = re.compile(r"(as the file already did; n|N)othing was written under `([^`]+)`\.")
T6_NEW = "a listing of `{path}` (`find -newer` a marker file) before and after the runs showed nothing from them."


def _resolve_t6(fix: dict[str, str], text: str) -> None:
    """Replace T6_MARK with the PR body's own sentence and its precise replacement."""
    matches = list(T6_PATTERN.finditer(text))
    if len(matches) != 1:
        return
    match = matches[0]
    new = T6_NEW.format(path=match.group(2))
    fix["old"] = match.group(0)
    fix["new"] = "as the file already did; " + new if match.group(1).startswith("as") else new[0].upper() + new[1:]


def _fixes() -> list[dict[str, str]]:
    fixes: list[dict[str, str]] = []
    # T1: the record sentence, once the record update (ruling 26 as section 8 item 26) has merged.
    for repo in ALL:
        fixes.append({"id": f"T1-{repo}", "finding": "T1", "repo": repo, "path": "texts/pr_body.md", "old": RECORD_OLD, "new": RECORD_NEW, "note": "apply only after the record update merges on juniper-ml; optionally name its PR after the path"})
    # T2: juniper-data's banner bump makes docs/ci_cd/CICD_REFERENCE.md's workflow table stale.
    fixes += [
        {"id": "T2-juniper-data-doc-row", "finding": "T2", "repo": "juniper-data", "path": "final/docs/ci_cd/CICD_REFERENCE.md", "old": "| `.github/workflows/lockfile-update.yml` | Lockfile auto-update (v0.1.0) |", "new": "| `.github/workflows/lockfile-update.yml` | Lockfile auto-update (v0.1.1) |", "note": "new file in the set: start from main's docs/ci_cd/CICD_REFERENCE.md"},
        {"id": "T2-juniper-data-doc-header", "finding": "T2", "repo": "juniper-data", "path": "final/docs/ci_cd/CICD_REFERENCE.md", "old": "**Version:** 0.4.8\n**Status:** Active\n**Last Updated:** November 15, 2026", "new": "**Version:** 0.4.9\n**Status:** Active\n**Last Updated:** November 24, 2026", "note": "the file's stamp convention (3904f58 bumped 0.4.7 -> 0.4.8 in header and footer); use the landing date"},
        {"id": "T2-juniper-data-doc-footer", "finding": "T2", "repo": "juniper-data", "path": "final/docs/ci_cd/CICD_REFERENCE.md", "old": "**Last Updated:** November 15, 2026\n**Version:** 0.4.8\n**Maintainer:** Paul Calnon", "new": "**Last Updated:** November 24, 2026\n**Version:** 0.4.9\n**Maintainer:** Paul Calnon", "note": "footer stamp"},
        {"id": "T2-juniper-data-pr-changed", "finding": "T2", "repo": "juniper-data", "path": "texts/pr_body.md",
         "old": "directly after the flood-3 lockfile empty-payload entry.\n\nNo doc changes: no file under `docs/` or `notes/` describes the step's failure output (the passages that mention the step, `docs/REFERENCE.md`, `docs/ci_cd/CICD_MANUAL.md` and `notes/DEPENDENCY_UPDATE_WORKFLOW.md`, describe its success path, which this does not change).",
         "new": "directly after the flood-3 lockfile empty-payload entry.\n- `docs/ci_cd/CICD_REFERENCE.md` (0.4.8 -> 0.4.9, Last Updated November 24, 2026, header and footer): its Workflow Files table gave `lockfile-update.yml` as v0.1.0, the banner's old version; it now gives v0.1.1.\n\nNo other doc changes: no file under `docs/` or `notes/` describes the step's failure output (the passages that mention the step, `docs/REFERENCE.md`, `docs/ci_cd/CICD_MANUAL.md`, `docs/ci_cd/CICD_REFERENCE.md` and `notes/DEPENDENCY_UPDATE_WORKFLOW.md`, describe its success path, which this does not change).",
         "note": "then re-run pre-commit on the four files and replace 'on the three files' and '16 hooks passed' in the Test plan with the measured result"},
        {"id": "T2-juniper-data-commit", "finding": "T2", "repo": "juniper-data", "path": "texts/commit_body.txt", "old": "workflow banner goes to 0.1.1.", "new": "workflow banner goes to 0.1.1, which docs/ci_cd/CICD_REFERENCE.md's\nworkflow table now gives (that doc 0.4.8 -> 0.4.9).", "note": ""},
        {"id": "T2-juniper-data-changelog", "finding": "T2", "repo": "juniper-data", "path": "final/CHANGELOG.md", "old": "(`.github/workflows/lockfile-update.yml`, banner 0.1.1).", "new": "(`.github/workflows/lockfile-update.yml`, banner 0.1.1, which `docs/ci_cd/CICD_REFERENCE.md` 0.4.9's workflow table now gives).", "note": ""},
    ]
    # T3: the pre-commit that ran the hooks is JuniperCascor1's 4.6.0, not /opt/miniforge3/bin's 4.5.1.
    for repo in ALL:
        fixes.append({"id": f"T3-{repo}", "finding": "T3", "repo": repo, "path": "texts/pr_body.md", "old": "pre-commit 4.5.1", "new": "pre-commit 4.6.0", "note": "the PATH pre-commit (JuniperCascor1) ran the hooks"})
    # T4: canopy's line 796 is not "the sentence after" the table, and line 795 holds two sentences.
    fixes += [
        {"id": "T4-canopy-pr-locate", "finding": "T4", "repo": "juniper-canopy", "path": "texts/pr_body.md", "old": "says, in the sentence after its commit-subject table (line 796):", "new": "says, in the paragraph after its commit-subject table (line 796):", "note": ""},
        {"id": "T4-canopy-pr-before", "finding": "T4", "repo": "juniper-canopy", "path": "texts/pr_body.md", "old": "which is what the manual's own sentence before it (line 795) says.", "new": "which is what the manual's line before it (line 795) says.", "note": ""},
        {"id": "T4-canopy-commit-locate", "finding": "T4", "repo": "juniper-canopy", "path": "texts/commit_body.txt", "old": "in the sentence after its", "new": "in the paragraph after its", "note": ""},
        {"id": "T4-canopy-commit-before", "finding": "T4", "repo": "juniper-canopy", "path": "texts/commit_body.txt", "old": "what the manual's sentence before says", "new": "what the manual's line before it says", "note": ""},
        {"id": "T4-canopy-changelog-locate", "finding": "T4", "repo": "juniper-canopy", "path": "final/CHANGELOG.md", "old": "The sentence after the runbook's commit-subject table said", "new": "A sentence in the paragraph after the runbook's commit-subject table said", "note": ""},
        {"id": "T4-canopy-changelog-before", "finding": "T4", "repo": "juniper-canopy", "path": "final/CHANGELOG.md", "old": "it says what the sentence\n  before says, that the tag", "new": "it says what the line\n  before it says, that the tag", "note": ""},
    ]
    # T5: data-client's "always stopped" is not true of every run; the step-level fact is.
    fixes.append({"id": "T5-data-client-latent", "finding": "T5", "repo": "juniper-data-client", "path": "texts/pr_body.md", "old": "so the step has always stopped at `No requirements.lock to commit — skipping.` and has never reached gh.", "new": "so the step stops at its `No requirements.lock to commit — skipping.` guard (the latest run, 45191635734 on 2026-11-23, logged it) and has never reached gh.", "note": ""})
    # T6: "nothing was written under" the runner temp directory claims more than a before/after listing shows.
    # The sentence and the directory it names are read from each PR body (see _t6), so no path is restated here.
    for repo in PORTS:
        fixes.append({"id": f"T6-{repo}", "finding": "T6", "repo": repo, "path": "texts/pr_body.md", "old": T6_MARK, "new": T6_MARK, "note": ""})
    # T10: data, cascor and worker state as an observed log what no run of the signed step ever produced.
    for repo in ("juniper-data", "juniper-cascor", "juniper-cascor-worker"):
        fixes.append({"id": f"T10-{repo}-pr", "finding": "T10", "repo": repo, "path": "texts/pr_body.md", "old": "The log showed only gh's one line.", "new": "A failing run would have logged only gh's one line (no run of this step has failed here yet).", "note": ""})
        fixes.append({"id": f"T10-{repo}-commit", "finding": "T10", "repo": repo, "path": "texts/commit_body.txt", "old": "never printed: the\nlog showed only gh's one line.", "new": "could never print: a\nfailing run would have logged only gh's one line (none has failed yet).", "note": ""})
        old_cl = "was unreachable and the log showed only\n  gh's line." if repo == "juniper-cascor-worker" else "was unreachable and the log showed only gh's line."
        new_cl = "was unreachable and a failing run would have logged\n  only gh's line." if repo == "juniper-cascor-worker" else "was unreachable and a failing run would have logged only gh's line."
        fixes.append({"id": f"T10-{repo}-changelog", "finding": "T10", "repo": repo, "path": "final/CHANGELOG.md", "old": old_cl, "new": new_cl, "note": ""})
    # T7: "the same text" contradicts "unchanged but for one comment line".
    for repo in PORTS:
        tail = "(only the naming comment and this step's `lockfiles` wording differ)." if repo == "juniper-cascor-worker" else "(only the naming comment differs)."
        fixes.append({"id": f"T7-{repo}", "finding": "T7", "repo": repo, "path": "texts/pr_body.md", "old": "this block is the same text.", "new": "this block's shell is the same " + tail, "note": ""})
    # T8: cascor's garbled CHANGELOG-placement parenthesis.
    fixes.append({"id": "T8-cascor-placement", "finding": "T8", "repo": "juniper-cascor", "path": "texts/pr_body.md", "old": "(the flood-3 lockfile entry it follows on is in a released section)", "new": "(the related flood-3 lockfile entry is in the released `[0.13.0]` section)", "note": ""})
    # T9 (optional): the ports inherit canopy#814's Known limit, which their bodies do not state.
    for repo in PORTS:
        words = "lockfiles NOT committed" if repo == "juniper-cascor-worker" else "lockfile NOT committed"
        locks = "the locks" if repo in ("juniper-cascor", "juniper-cascor-worker") else "the lock"
        limit = (
            "## Known limit\n\nThe one juniper-canopy#814 recorded: an `errors` body does not always prove that nothing was committed "
            "(GitHub can answer with a timeout or an internal error that carries `errors`, and the mutation may have been applied "
            f"before the request was cut off), yet the step prints `{words}`, `main`'s wording, which this keeps. The printed advice "
            f"is safe either way: a re-run checks out the branch's tip and finds {locks} up to date.\n\n## Requirements"
        )
        fixes.append({"id": f"T9-{repo}", "finding": "T9", "repo": repo, "path": "texts/pr_body.md", "old": "## Requirements", "new": limit, "note": "optional"})
    return fixes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--r26", type=Path, required=True)
    parser.add_argument("--clones", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    args = parser.parse_args()

    fixes = _fixes()
    texts: dict[tuple[str, str], str] = {}
    ok = True
    for fix in fixes:
        key = (fix["repo"], fix["path"])
        if key not in texts:
            src = args.r26 / fix["repo"] / fix["path"]
            if not src.exists() and fix["path"].startswith("final/"):
                src = args.clones / fix["repo"] / fix["path"][len("final/"):]
            texts[key] = src.read_text(encoding="utf-8")
        if fix["old"] == T6_MARK:
            _resolve_t6(fix, texts[key])
        count = texts[key].count(fix["old"])
        status = "OK" if count == 1 else f"REFUSED ({count}x)"
        print(f"{fix['id']:34} {fix['repo']:22} {fix['path']:38} {status}")
        if count != 1:
            ok = False
            continue
        texts[key] = texts[key].replace(fix["old"], fix["new"], 1)
    for (repo, path), text in texts.items():
        out = args.preview / repo / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    # endings, before and after the fixes
    for repo in ALL:
        for path, end in (("texts/pr_body.md", PR_END), ("texts/commit_body.txt", COMMIT_END)):
            before = (args.r26 / repo / path).read_text(encoding="utf-8")
            after = texts.get((repo, path), before)
            good = before.endswith(end) and after.endswith(end) and before.count(end.strip().splitlines()[-1]) == 1
            print(f"ending {repo:22} {path:24} {'OK' if good else 'BAD'}")
            ok = ok and good
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w", encoding="utf-8") as fh:
        json.dump(fixes, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"{len(fixes)} fixes; {'all applied' if ok else 'REFUSALS or bad endings above'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
