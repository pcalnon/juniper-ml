#!/usr/bin/env python3
"""
Probe juniper-data's pull-request Gitleaks step on merge shapes a content conflict does not cover, now that it passes --remerge-diff.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (round 2 of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
--remerge-diff makes git print, for each merge commit, the diff between a fresh re-merge of its parents (conflict
markers and all) and the commit itself, with "remerge CONFLICT" header lines. The step fails closed on any gitleaks
exit other than 0 or 2, so a merge shape whose output the engine cannot parse would turn a clean pull request red.
The validator's harness covered a content conflict with a direct engine call; this runs the step itself on a content
conflict, modify/delete, add/add, a binary conflict and a rename against a modification, each resolved honestly
(must pass, with no git error in the engine's log), plus an add/add resolution that writes a token (must be reported
under the merge's SHA).

It loads the validator's harness (scan_harness.py) by path for its Repo, token and run helpers, so it runs the
step's own run: block from the worktree's ci.yml under `bash -e`. Repositories live under $TMPDIR/val-a-m1/
synth-edge, have no remote and are never pushed; tokens are FAKE-marked, built at runtime.

Usage:
    TMPDIR=<scratch> python3 -I <this> <harness dir> <gitleaks binary> <out json>
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def load_harness(harness_dir: Path):
    spec = importlib.util.spec_from_file_location("scan_harness", harness_dir / "scan_harness.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["scan_harness"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    harness_dir, engine, out_path = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
    H = load_harness(harness_dir)
    H.OUT = H.OUT.parent / "synth-edge"
    H.OUT.mkdir(parents=True, exist_ok=True)
    engine_bin = H.OUT / "engine-bin"
    engine_bin.mkdir(exist_ok=True)
    link = engine_bin / "gitleaks"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(engine)
    step = H.extract_step()

    def scenario(name: str, prepare, resolve, expect_token: bool) -> dict:
        """prepare(r) -> builds base/pr histories and returns the base SHA with HEAD on 'pr'; resolve(r) finishes the merge."""
        r = H.Repo(H.OUT / name)
        base = prepare(r)
        merge_rc = H.subprocess.run(["git", "-C", str(r.dir), "merge", "--no-ff", "-q", "-m", "merge the base branch", base], env=H.git_env(r.home, H.next_date()), capture_output=True, text=True, timeout=120, check=False).returncode  # nosec
        resolve(r)
        r.git("commit", "-q", "--no-verify", "-m", "merge the base branch", date=H.next_date(), check=False)
        merge = r.rev("HEAD")
        head = r.commit("pr/after.txt", "after\n")
        res = H.run_fix_step(r, engine_bin, step, base, head, str(len(r.pr_list(base, head))))
        log = (r.root / "fix_step.log").read_text(encoding="utf-8")
        git_errors = [line for line in log.splitlines() if "[git]" in line or "failed to" in line.lower()]
        reported = res["reported"]
        ok = (res["exit"] == 1 and reported == [merge]) if expect_token else (res["exit"] == 0 and reported == [] and not git_errors)
        return {"scenario": name, "merge_exit": merge_rc, "merge": merge[:8], "step_exit": res["exit"], "reported": H.short(reported), "engine_commits_scanned": res["engine_commits_scanned"], "git_error_lines": git_errors[:5], "expect_token": expect_token, "verdict": "AS EXPECTED" if ok else "UNEXPECTED"}

    def put(p: Path, content: bytes | str) -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")

    def fork(r, files: dict[str, bytes | str]):
        for rel, content in files.items():
            put(r.dir / rel, content)
            r.git("add", "--", rel)
        r.git("commit", "-q", "--no-verify", "-m", "fork point", date=H.next_date())

    def on(r, branch: str, edits: dict[str, bytes | str | None], new_branch: bool = False) -> str:
        r.git("checkout", "-q", *(["-b"] if new_branch else []), branch)
        for rel, content in edits.items():
            if content is None:
                r.git("rm", "-q", "--", rel)
                continue
            put(r.dir / rel, content)
            r.git("add", "--", rel)
        r.git("commit", "-q", "--no-verify", "-m", f"edit on {branch}", date=H.next_date())
        return r.rev("HEAD")

    def build(files, pr_edits, base_edits):
        def prepare(r):
            fork(r, files)
            on(r, "pr", pr_edits, new_branch=True)
            base = on(r, "main", base_edits)
            r.git("checkout", "-q", "pr")
            return base
        return prepare

    def keep_ours(paths):
        def resolve(r):
            for rel in paths:
                r.git("checkout", "--ours", "--", rel, check=False)
                r.git("add", "--", rel)
        return resolve

    def write(rel: str, text: str):
        def resolve(r):
            (r.dir / rel).write_text(text, encoding="utf-8")
            r.git("add", "--", rel)
        return resolve

    blob_a, blob_b, blob_c = bytes(range(256)) * 4, bytes(reversed(range(256))) * 4, bytes(range(0, 256, 3)) * 8
    results = [
        scenario("content", build({"conf/s.txt": "a=1\nb=2\nc=3\n"}, {"conf/s.txt": "a=1\nb=PR\nc=3\n"}, {"conf/s.txt": "a=1\nb=BASE\nc=3\n"}), write("conf/s.txt", "a=1\nb=PR-and-BASE\nc=3\n"), False),
        scenario("modify-delete", build({"conf/f.txt": "one\ntwo\n"}, {"conf/f.txt": "one\nTWO\n"}, {"conf/f.txt": None}), keep_ours(["conf/f.txt"]), False),
        scenario("add-add", build({"conf/seed.txt": "s\n"}, {"conf/g.txt": "pr\n"}, {"conf/g.txt": "base\n"}), write("conf/g.txt", "pr\nbase\n"), False),
        scenario("binary", build({"data/b.bin": blob_a}, {"data/b.bin": blob_b}, {"data/b.bin": blob_c}), keep_ours(["data/b.bin"]), False),
        scenario("rename-vs-modify", build({"conf/h.txt": "".join(f"line {i}\n" for i in range(40))}, {"conf/h.txt": None, "conf/h2.txt": "".join(f"line {i}\n" for i in range(40))}, {"conf/h.txt": "".join(f"line {i}\n" for i in range(39)) + "line 39 changed\n"}), lambda r: None, False),
        scenario("add-add-with-token", build({"conf/seed.txt": "s\n"}, {"conf/g.txt": "pr\n"}, {"conf/g.txt": "base\n"}), write("conf/g.txt", "pr\nGITHUB_TOKEN=" + H.fake_token(83) + "\n"), True),
    ]
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for res in results:
        print(f"{res['verdict']:<11} {res['scenario']:<20} merge_exit={res['merge_exit']} step_exit={res['step_exit']} reported={res['reported']} merge={res['merge']} scanned={res['engine_commits_scanned']} git_errors={res['git_error_lines']}")
    return 0 if all(r["verdict"] == "AS EXPECTED" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
