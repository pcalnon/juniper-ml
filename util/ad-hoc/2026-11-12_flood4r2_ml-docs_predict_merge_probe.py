#!/usr/bin/env python3
"""
Probe ``util/fleet_triage/predict_merge.py``'s scratch repository, heal-first rule and screens: the facts the docs state.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- investigation (claim evidence for the Cursor flood-4 round-2 docs carrier: draft juniper-ml#2494,
        draft juniper-ml#2484's scratch paragraph, and the stale fleet-triage documentation the triage calls defect 4)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2);
         tests/test_predict_merge.py (whose fixture helpers this copies)

Everything runs on throwaway repositories under the session's temp root, with the user's git configuration
switched off; no network, no ``gh``. It records, as JSON:

* constants: ``PRECOMMIT_HOOKS``, ``_GIT_LOCATION_VARS``, the two console-script names;
* ``_is_heal`` on the rows the documents give;
* the scratch of a plain source and of a shallow source whose cut is BELOW the merge base (its ``alternates``,
  ``info/attributes`` and ``shallow`` files), and the verdicts;
* a shallow source whose cut is ABOVE the merge base: the error, and what the same run gives when the copy of the
  ``shallow`` file is switched off (the history the documents describe);
* an inherited ``GIT_DIR`` / ``GIT_WORK_TREE``: the verdict of a symbol-loss branch with and without them, the
  source's refs before and after, and what ``_resolve_repo_root`` (the CLI's own ``git rev-parse``) answers;
* the docs screen on a small swap, on a five-line deletion, on a deleted heading, and on a ``README.md`` outside
  ``docs/`` (the scope difference from CI's default).

Usage: 2026-11-12_flood4r2_ml-docs_predict_merge_probe.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
sys.path.insert(0, str(REPO / "util"))

from fleet_triage import predict_merge as pm  # noqa: E402  (path-invoked util import, as tests/test_predict_merge.py does)


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=60, check=False)
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    for key, value in (("user.email", "probe@example.invalid"), ("user.name", "Docs Probe"), ("commit.gpgsign", "false"), ("tag.gpgsign", "false")):
        git(path, "config", key, value)


def write(repo: Path, rel: str, content: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def commit(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def publish(repo: Path, name: str) -> None:
    git(repo, "update-ref", f"refs/remotes/origin/{name}", f"refs/heads/{name}")


def refs(repo: Path) -> str:
    return git(repo, "for-each-ref", "--format=%(objectname) %(refname)").stdout


def scratch_facts(scratch_parent: Path) -> dict:
    clone = next(scratch_parent.glob("fleet-triage-*/clone"))
    shallow = clone / ".git" / "shallow"
    facts = {
        "git_is_a_directory": (clone / ".git").is_dir(),
        "alternates": (clone / ".git" / "objects" / "info" / "alternates").read_text(encoding="utf-8"),
        "info_attributes": (clone / ".git" / "info" / "attributes").read_text(encoding="utf-8"),
        "shallow": shallow.read_text(encoding="utf-8") if shallow.is_file() else None,
    }
    shutil.rmtree(clone.parent, ignore_errors=True)
    return facts


def simulate(repo: Path, branch: str, **kwargs) -> dict:
    try:
        verdict = pm.simulate_merge(repo, branch, run_gates=False, **kwargs)
    except pm.PredictMergeError as exc:
        return {"error": str(exc)}
    return {key: verdict[key] for key in ("verdict", "behind_main", "true_delta", "gates")}


def probe_scratch(tmp: Path) -> dict:
    out: dict = {}
    plain = tmp / "plain"
    init_repo(plain)
    write(plain, "fileA.txt", "A0\n")
    commit(plain, "c0")
    publish(plain, "main")
    git(plain, "checkout", "-q", "-b", "clean")
    write(plain, "fileD.txt", "D\n")
    commit(plain, "add D")
    parent = tmp / "scratch-plain"
    parent.mkdir()
    before = refs(plain)
    out["plain_source"] = {"result": simulate(plain, "clean", keep_scratch=True, scratch_parent=parent), "scratch": scratch_facts(parent), "objects_dir": str(plain / ".git" / "objects"), "source_refs_unchanged": refs(plain) == before}

    upstream = tmp / "upstream"
    init_repo(upstream)
    write(upstream, "fileA.txt", "A0\n")
    commit(upstream, "m0")
    write(upstream, "fileB.txt", "B\n")
    commit(upstream, "m1")
    git(upstream, "checkout", "-q", "-b", "pr")
    write(upstream, "fileP.txt", "P\n")
    commit(upstream, "c1")
    write(upstream, "fileQ.txt", "Q\n")
    commit(upstream, "c2")
    git(upstream, "checkout", "-q", "main")
    write(upstream, "fileC.txt", "C\n")
    commit(upstream, "m2")
    write(upstream, "fileE.txt", "E\n")
    commit(upstream, "m3")

    # Cut BELOW the merge base (m1): depth 3 from main keeps m3, m2, m1; depth 3 from pr keeps c2, c1, m1.
    below = tmp / "below"
    git(tmp, "clone", "-q", "--depth=3", "--no-single-branch", f"file://{upstream}", str(below))
    parent = tmp / "scratch-below"
    parent.mkdir()
    out["shallow_cut_below_the_merge_base"] = {
        "source_is_shallow": git(below, "rev-parse", "--is-shallow-repository").stdout.strip(),
        "source_shallow_file": (below / ".git" / "shallow").read_text(encoding="utf-8"),
        "result": simulate(below, "origin/pr", keep_scratch=True, scratch_parent=parent),
        "scratch": scratch_facts(parent),
    }

    # A linked worktree of that shallow source: its .git is a file, and the shallow file lives in the COMMON git dir.
    linked = tmp / "below-linked"
    git(below, "worktree", "add", "-q", "--detach", str(linked))
    parent = tmp / "scratch-linked"
    parent.mkdir()
    out["linked_worktree_of_the_shallow_source"] = {
        "source_dot_git_is_a_file": (linked / ".git").is_file(),
        "result": {key: value for key, value in simulate(linked, "origin/pr", keep_scratch=True, scratch_parent=parent).items() if key != "gates"},
        "scratch": scratch_facts(parent),
    }

    # Cut ABOVE the merge base: main in full, the PR head with --depth=1 (the fixture of tests/test_predict_merge.py).
    above = tmp / "above"
    git(tmp, "clone", "-q", "--single-branch", "--branch", "main", f"file://{upstream}", str(above))
    git(above, "fetch", "-q", "--depth=1", "origin", "pr:refs/remotes/origin/pr")
    scratch_above = tmp / "scratch-above"
    scratch_above.mkdir()
    with_copy = simulate(above, "origin/pr", scratch_parent=scratch_above)
    with mock.patch.object(pm.shutil, "copyfile", lambda *args, **kwargs: None):
        without_copy = simulate(above, "origin/pr", scratch_parent=scratch_above)
    out["shallow_cut_above_the_merge_base"] = {"source_is_shallow": git(above, "rev-parse", "--is-shallow-repository").stdout.strip(), "with_the_shallow_copy": with_copy, "with_the_copy_switched_off": without_copy}
    return out


def probe_inherited_git_dir(tmp: Path) -> dict:
    repo = tmp / "symbols"
    init_repo(repo)
    write(repo, "tests/test_thing.py", "def test_one():\n    assert True\n\n\ndef test_two():\n    assert True\n")
    commit(repo, "c0")
    publish(repo, "main")
    git(repo, "checkout", "-q", "-b", "loses-a-test")
    write(repo, "tests/test_thing.py", "def test_one():\n    assert True\n")
    commit(repo, "drop test_two")
    git(repo, "checkout", "-q", "main")
    other = tmp / "other"
    init_repo(other)
    write(other, "x.txt", "x\n")
    commit(other, "x")
    plain = simulate(repo, "loses-a-test", scratch_parent=tmp)
    before = refs(repo)
    inherited = {"GIT_DIR": str(repo / ".git"), "GIT_WORK_TREE": str(repo)}
    with mock.patch.dict(os.environ, inherited):
        under_git_dir = simulate(repo, "loses-a-test", scratch_parent=tmp)
        resolved_same = str(pm._resolve_repo_root(str(repo)))
    with mock.patch.dict(os.environ, {"GIT_DIR": str(repo / ".git")}):
        under_git_dir_alone = simulate(repo, "loses-a-test", scratch_parent=tmp)
    with mock.patch.dict(os.environ, {"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other)}):
        try:
            resolved_other = str(pm._resolve_repo_root(str(repo)))
        except pm.PredictMergeError as exc:
            resolved_other = f"PredictMergeError: {exc}"

    def brief(result: dict) -> dict:
        if "error" in result:
            return result
        return {"verdict": result["verdict"], "ast_symbol_screen": result["gates"]["ast_symbol_screen"]}

    return {
        "symbol_loss_branch_plain_environment": brief(plain),
        "symbol_loss_branch_under_inherited_GIT_DIR_and_GIT_WORK_TREE": brief(under_git_dir),
        "symbol_loss_branch_under_inherited_GIT_DIR_alone": brief(under_git_dir_alone),
        "source_refs_unchanged": refs(repo) == before,
        "repo": str(repo),
        "_resolve_repo_root_under_GIT_DIR_of_the_same_repo": resolved_same,
        "_resolve_repo_root_under_GIT_DIR_of_another_repo": resolved_other,
        "other_repo": str(other),
        "symbol_loss_console_script": shutil.which(pm._SYMBOL_LOSS_CHECK),
    }


def probe_docs_screen(tmp: Path) -> dict:
    repo = tmp / "docs"
    init_repo(repo)
    body = "".join(f"line {i}\n" for i in range(1, 21))
    write(repo, "docs/GUIDE.md", "# Guide\n\n## One\n\n" + body + "\n## Two\n\ntail\n")
    write(repo, "README.md", "# Readme\n\n" + body)
    commit(repo, "c0")
    publish(repo, "main")

    def branch(name: str, rel: str, new_text: str) -> dict:
        git(repo, "checkout", "-q", "-b", name, "main")
        write(repo, rel, new_text)
        commit(repo, name)
        git(repo, "checkout", "-q", "main")
        result = simulate(repo, name, scratch_parent=tmp)
        return result if "error" in result else {"verdict": result["verdict"], "docs_additions_only": result["gates"]["docs_additions_only"]}

    guide = (repo / "docs" / "GUIDE.md").read_text(encoding="utf-8")
    readme = (repo / "README.md").read_text(encoding="utf-8")
    five_gone = "".join(line for line in guide.splitlines(keepends=True) if line.strip() not in {f"line {i}" for i in range(5, 10)})
    four_gone = "".join(line for line in guide.splitlines(keepends=True) if line.strip() not in {f"line {i}" for i in range(5, 9)})
    readme_five_gone = "".join(line for line in readme.splitlines(keepends=True) if line.strip() not in {f"line {i}" for i in range(5, 10)})
    return {
        "docs_additions_console_script": shutil.which(pm._DOCS_ADDITIONS_CHECK),
        "one_line_swapped_in_place": branch("swap", "docs/GUIDE.md", guide.replace("line 7\n", "line seven\n")),
        "four_consecutive_lines_deleted": branch("four", "docs/GUIDE.md", four_gone),
        "five_consecutive_lines_deleted": branch("five", "docs/GUIDE.md", five_gone),
        "a_heading_deleted": branch("heading", "docs/GUIDE.md", guide.replace("## Two\n", "")),
        "lines_added_only": branch("added", "docs/GUIDE.md", guide + "\nmore\n"),
        "five_lines_deleted_from_README_md_outside_docs": branch("readme", "README.md", readme_five_gone),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Probe predict_merge's scratch, heal-first rule and screens.")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    heal_rows = [
        {"title": "fix: restore gate", "branch": "origin/cursor/x"},
        {"title": "fix(triage): sort", "branch": "origin/cursor/z"},
        {"title": "FIX: caps", "branch": "origin/cursor/z"},
        {"title": "  heal canopy WS", "branch": "origin/cursor/y"},
        {"title": "healing the gate", "branch": "origin/cursor/y"},
        {"title": "feat", "branch": "origin/fix/broken-gate"},
        {"title": "feat", "branch": "origin/heal/x"},
        {"title": "feat", "branch": "origin/hotfix/urgent"},
        {"title": "feat", "branch": "origin/HOTFIX/urgent"},
        {"title": "feat", "branch": "fix/local-fixture-branch"},
        {"title": "restore the deleted section", "branch": "origin/cursor/restore-section"},
        {"title": "repair broken gate", "branch": "origin/cursor/x"},
        {"title": "feat", "branch": "origin/cursor/fix-first-docs"},
        {"title": "test(fleet): + heal tokens", "branch": "origin/cursor/t"},
        {"title": "hotfix: urgent", "branch": "origin/cursor/t"},
        {"title": "fix the gate", "branch": "origin/cursor/t"},
    ]
    order_input = [
        {"pr": 20, "title": "feat hot", "branch": "origin/cursor/hot", "true_delta": ["HOT.py"]},
        {"pr": 21, "title": "fix: repair symbol screen", "branch": "origin/cursor/repair-x", "true_delta": ["A.md"]},
        {"pr": 22, "title": "feat solo", "branch": "origin/cursor/solo", "true_delta": ["HOT.py", "SOLO.py"]},
        {"pr": 23, "title": "nudge", "branch": "origin/hotfix/y", "true_delta": ["B.md"]},
        {"pr": 19, "title": "feat lone", "branch": "origin/cursor/lone", "true_delta": ["LONE.py"]},
    ]
    report: dict = {
        "repo": str(REPO),
        "git_version": subprocess.run(["git", "--version"], capture_output=True, text=True, check=False).stdout.strip(),
        "PRECOMMIT_HOOKS": list(pm.PRECOMMIT_HOOKS),
        "_GIT_LOCATION_VARS": list(pm._GIT_LOCATION_VARS),
        "console_scripts": [pm._SYMBOL_LOSS_CHECK, pm._DOCS_ADDITIONS_CHECK],
        "_is_heal": [{**row, "heal": pm._is_heal(row)} for row in heal_rows],
        "suggest_order": pm.suggest_order(order_input, pm.build_clusters(order_input)),
    }
    quiet = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, **{name: "" for name in SENTRY_DSN_NAMES}}
    scrubbed = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    with tempfile.TemporaryDirectory(prefix="flood4r2-predict-merge-") as temp_dir, mock.patch.dict(os.environ, {**scrubbed, **quiet}, clear=True):
        tmp = Path(temp_dir).resolve()
        os.environ["GIT_CEILING_DIRECTORIES"] = str(tmp.parent)
        report["scratch"] = probe_scratch(tmp)
        report["inherited_git_dir"] = probe_inherited_git_dir(tmp)
        report["docs_screen"] = probe_docs_screen(tmp)
        report["leftover_scratch_dirs"] = sorted(str(path.name) for path in tmp.glob("fleet-triage-*"))
        text = json.dumps(report, indent=1).replace(str(tmp), "{tmp}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
