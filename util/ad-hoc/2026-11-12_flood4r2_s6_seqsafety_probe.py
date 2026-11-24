#!/usr/bin/env python3
"""
Run CI's two sequence-safety screens on a frozen landing snapshot BEFORE the signed push, on a local probe commit that
has the tree and the commit message the pull request will have.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 6: landing the validated carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_land_snapshot.py (writes the <freeze> directory this reads),
         util/ad-hoc/2026-11-09_flood4r2_land_open_pr.py (the push this precedes),
         juniper-ci-tools (juniper-symbol-loss-check, juniper-docs-additions-check)

Why: juniper-ml#2552 was opened green on every local check and failed CI's Sequence Safety job on four test symbols
that an Overtoad ruling changes on purpose. The screens read their waivers (``Allow-Symbol-Loss:`` /
``Allow-Docs-Rewrite:``) from the COMMIT MESSAGE, a signed commit cannot be amended, and the squash must carry the
trailer to main, so a missing waiver costs a closed pull request and a re-cut. This runs the same two commands CI
runs, on the same tree and message, first.

Usage:
  2026-11-12_flood4r2_s6_seqsafety_probe.py --freeze <dir> --title <title.txt> --body <commit_body.txt> --out <dir>
      --scope <glob> [--scope <glob> ...] [--repo-dir <checkout>] [--main-ref origin/main]

Run it from (or pass ``--repo-dir`` for) a checkout of the carrier's repository whose ``--main-ref`` is fetched.
<freeze> holds paths.txt (``add <path>`` / ``delete <path>``), snapshot/ and plan.json. The probe commit's tree is
main's tree with the snapshot's paths applied; its parent is main; its message is the title, a blank line and the
body, as util/open_signed_pr.py writes it. The commit is built with a private index file under <out> and
``git commit-tree``: no working tree, no branch and no ref is touched, and nothing is pushed. It stays in the object
store as a dangling commit.

``--scope`` is the repository's own symbol-screen scope, copied from its workflow (juniper-ml:
``'tests/*.py' 'util/**/*.py' 'util/**/*.bash'``; juniper-cascor: ``'src/**/*.py'``). The docs screen uses its
default scope, as CI does.

Writes <out>/symbol.log, <out>/docs.log and <out>/result.json. Exit 0 = both screens pass on the probe commit;
1 = at least one fails (its findings are printed); 2 = the freeze does not match main, or a tool is missing.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SUMMARY_MARKS = ("files_screened", "FAIL", "WAIVED", "waived (", "OK:")


def run(argv: list[str], cwd: Path, env: dict | None = None, data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=str(cwd), env=env, input=data, capture_output=True, check=False)


def must(argv: list[str], cwd: Path, env: dict | None = None, data: bytes | None = None) -> str:
    done = run(argv, cwd, env, data)
    if done.returncode != 0:
        raise SystemExit("command failed (%d): %s\n%s" % (done.returncode, " ".join(argv), done.stderr.decode("utf-8", "replace")))
    return done.stdout.decode("utf-8", "replace").strip()


def screen(argv: list[str], cwd: Path, log: Path) -> int:
    done = run(argv, cwd)
    text = done.stdout.decode("utf-8", "replace") + done.stderr.decode("utf-8", "replace")
    log.write_text("$ %s\n%s\nexit=%d\n" % (" ".join(argv), text, done.returncode), encoding="utf-8")
    for line in text.splitlines():
        if any(mark in line for mark in SUMMARY_MARKS):
            print("   " + line.strip()[:260])
    return done.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--scope", action="append", required=True)
    parser.add_argument("--repo-dir", default=".")
    parser.add_argument("--main-ref", default="origin/main")
    args = parser.parse_args()

    repo = Path(args.repo_dir).resolve()
    freeze = Path(args.freeze).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for tool in ("juniper-symbol-loss-check", "juniper-docs-additions-check"):
        if shutil.which(tool) is None:
            print("MISSING TOOL: %s (pip install juniper-ci-tools)" % tool)
            return 2

    main_sha = must(["git", "rev-parse", args.main_ref], repo)
    plan = json.loads((freeze / "plan.json").read_text(encoding="utf-8"))
    frozen_on = next((str(plan[key]) for key in ("main_sha", "main", "main_ref_sha") if plan.get(key)), "")
    if frozen_on and not (main_sha.startswith(frozen_on) or frozen_on.startswith(main_sha)):
        print("REFUSED: %s is %s now; the freeze was built on %s -- re-freeze" % (args.main_ref, main_sha[:8], frozen_on[:8]))
        return 2

    index = out / "probe.index"
    if index.exists():
        index.unlink()
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    must(["git", "read-tree", main_sha], repo, env)
    adds = deletes = 0
    for raw in (freeze / "paths.txt").read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        action, path = raw.split(None, 1)
        path = path.strip()
        if action == "delete":
            must(["git", "update-index", "--force-remove", "--", path], repo, env)
            deletes += 1
            continue
        blob = must(["git", "hash-object", "-w", "--", str(freeze / "snapshot" / path)], repo)
        listed = must(["git", "ls-tree", main_sha, "--", path], repo)
        mode = listed.split()[0] if listed else "100644"
        must(["git", "update-index", "--add", "--cacheinfo", "%s,%s,%s" % (mode, blob, path)], repo, env)
        adds += 1
    tree = must(["git", "write-tree"], repo, env)
    index.unlink()

    title = Path(args.title).read_text(encoding="utf-8").strip()
    body = Path(args.body).read_text(encoding="utf-8")
    message = (title + "\n\n" + body).encode("utf-8")
    commit = must(["git", "commit-tree", tree, "-p", main_sha], repo, data=message)
    print("probe commit %s (tree %s; %d adds, %d deletes) on %s %s -- dangling, never pushed" % (commit[:12], tree[:12], adds, deletes, args.main_ref, main_sha[:8]))

    symbol_argv = ["juniper-symbol-loss-check"]
    for scope in args.scope:
        symbol_argv += ["--scope", scope]
    symbol_argv += ["--base", main_sha, "--head", commit]
    print("-- symbol-loss screen")
    symbol_rc = screen(symbol_argv, repo, out / "symbol.log")
    print("-- docs screen")
    docs_rc = screen(["juniper-docs-additions-check", "--base", main_sha, "--head", commit], repo, out / "docs.log")

    result = {"main": main_sha, "probe_commit": commit, "tree": tree, "adds": adds, "deletes": deletes, "scopes": args.scope, "symbol_exit": symbol_rc, "docs_exit": docs_rc}
    (out / "result.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print("symbol screen exit=%d ; docs screen exit=%d" % (symbol_rc, docs_rc))
    return 0 if symbol_rc == 0 and docs_rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
