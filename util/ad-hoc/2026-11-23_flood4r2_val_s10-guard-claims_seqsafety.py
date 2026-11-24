#!/usr/bin/env python3
"""
Probe the sequence-safety screens on the agent guard 1.4.0 carrier's staged tree, with and without its waiver.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- read-only validation (claims lens on the agent guard 1.4.0 texts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py; juniper-ci-tools (juniper-symbol-loss-check, juniper-docs-additions-check)

Usage:
    python3 -I 2026-11-23_flood4r2_val_s10-guard-claims_seqsafety.py <repo dir> <carrier dir> <base sha>
        <manifest.json> <staged dir> <commit_body.txt> <out dir>

The carrier's index is never used in place: its file is COPIED into <out dir>, and `git write-tree` reads the copy
(GIT_INDEX_FILE), so the carrier's index and working tree are untouched. A second tree is built from <base sha> and
the staged copies in a private index. Each probe commit is made with `git commit-tree` (no branch, no ref, never
pushed): a dangling object. The screens run with --base <base sha> --head <probe commit> and CI's symbol scope.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404 -- git plumbing and the two read-only screens
import sys
from pathlib import Path

TRAILER = "Allow-Symbol-Loss: method:BashAnalyzer._path_word"
SCOPES = ["--scope", "tests/*.py", "--scope", "util/**/*.py", "--scope", "util/**/*.bash"]


def run(argv: list, cwd: Path, env: dict = None, data: bytes = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=str(cwd), env=env, input=data, capture_output=True, check=False, timeout=180)  # nosec B603


def must(argv: list, cwd: Path, env: dict = None, data: bytes = None) -> str:
    done = run(argv, cwd, env, data)
    if done.returncode != 0:
        raise SystemExit("failed (%d): %s\n%s" % (done.returncode, " ".join(argv), done.stderr.decode("utf-8", "replace")))
    return done.stdout.decode("utf-8", "replace").strip()


def main(argv: list) -> int:
    repo, carrier, base, manifest, staged, body, out = Path(argv[1]), Path(argv[2]), argv[3], Path(argv[4]), Path(argv[5]), Path(argv[6]), Path(argv[7])
    out.mkdir(parents=True, exist_ok=True)
    result = {"base": base}
    # Tree 1: write-tree over a copy of the carrier's index.
    index_path = must(["git", "-C", str(carrier), "rev-parse", "--path-format=absolute", "--git-path", "index"], repo)
    copy = out / "carrier_index.copy"
    shutil.copyfile(index_path, copy)
    env_copy = {**os.environ, "GIT_INDEX_FILE": str(copy)}
    result["tree_from_index_copy"] = must(["git", "-C", str(carrier), "write-tree"], repo, env_copy)
    # Tree 2: base + the staged copies in a private index.
    private = out / "private.index"
    if private.exists():
        private.unlink()
    env_private = {**os.environ, "GIT_INDEX_FILE": str(private)}
    must(["git", "read-tree", base], repo, env_private)
    for entry in json.loads(manifest.read_text(encoding="utf-8"))["files"]:
        blob = must(["git", "hash-object", "-w", "--", str(staged / entry["path"])], repo)
        must(["git", "update-index", "--add", "--cacheinfo", "%s,%s,%s" % (entry.get("mode", "100644"), blob, entry["path"])], repo, env_private)
    result["tree_from_staged_copies"] = must(["git", "write-tree"], repo, env_private)
    result["trees_equal"] = result["tree_from_index_copy"] == result["tree_from_staged_copies"]
    tree = result["tree_from_staged_copies"]
    text = body.read_text(encoding="utf-8")
    messages = {
        "body_only": text,
        "body_plus_trailer_last": text.rstrip("\n") + "\n\n" + TRAILER + "\n",
        "trailer_then_attribution": text.rstrip("\n") + "\n\n" + TRAILER + "\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n",
    }
    result["probes"] = {}
    for name, message in messages.items():
        msg_file = out / ("message_%s.txt" % name)
        msg_file.write_text(message, encoding="utf-8")
        commit = must(["git", "commit-tree", tree, "-p", base, "-F", str(msg_file)], repo)
        signed = "\ngpgsig" in "\n" + must(["git", "cat-file", "commit", commit], repo)
        symbol = run(["juniper-symbol-loss-check", *SCOPES, "--base", base, "--head", commit], repo)
        docs = run(["juniper-docs-additions-check", "--base", base, "--head", commit], repo)
        (out / ("symbol_%s.log" % name)).write_bytes(symbol.stdout + symbol.stderr)
        (out / ("docs_%s.log" % name)).write_bytes(docs.stdout + docs.stderr)
        result["probes"][name] = {"commit": commit, "signed": signed, "symbol_exit": symbol.returncode, "docs_exit": docs.returncode}
        print("%-26s commit %s signed=%s symbol exit=%d docs exit=%d" % (name, commit[:12], signed, symbol.returncode, docs.returncode))
    (out / "seqsafety.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "probes"}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
