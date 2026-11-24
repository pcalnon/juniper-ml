"""
Decide which of the session-7 tests-lens mutants can be kept on the session-8 landing, from bytes alone (read-only).

For every mutant of the predecessor's results.json it hashes, in the new landed tree, each file the mutant edited
and the suite it ran, and compares them with the sha256 the predecessor recorded before its run. A mutant is KEPT
when every one of those files is byte-identical and none of them, nor a file its suite reads (--reads), is a file
main changed between the predecessor's base and the new one (computed with the version-control tool in --repo).
It also hashes the same files in the predecessor's own mutation copy, so a mutant left behind by a killed run
shows (a "before" mismatch there), and compares the carrier's pre-session-8 snapshot with its current manifest.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent L1b, flood-4 session 8)
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --results <results.json> --tree <landed tree> --repo <own worktree> --old-base <sha>
        --new-base <sha> --pre-s8 <carrier scratch>/pre-s8 --manifest <carrier scratch>/manifest.json --out <json>
        [--reads SUITE=PATH ...]
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

# The shared files each re-read suite takes as input besides its own bytes (used when --reads is not given).
DEFAULT_READS = (
    "tests/test_pyproject_extras.py=pyproject.toml",
    "tests/test_pyproject_extras.py=docs/REFERENCE.md",
    "tests/test_pyproject_extras.py=README.md",
    "tests/test_ci_host_tooling_macos.py=.github/workflows/ci.yml",
    "tests/test_ci_test_wiring_drift.py=.github/workflows/ci.yml",
    "tests/test_ci_test_wiring_drift.py=docs/REFERENCE.md",
)


def sha256_of(path):
    if not path.is_file():
        return "absent"
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def moved_files(repo, old, new):
    done = subprocess.run(["git", "diff", "--name-only", old, new], cwd=str(repo), capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise SystemExit("diff failed: %s" % done.stderr.strip())
    return sorted(line for line in done.stdout.splitlines() if line.strip())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--results", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--old-base", required=True)
    parser.add_argument("--new-base", required=True)
    parser.add_argument("--pre-s8", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--reads", nargs="*", default=list(DEFAULT_READS))
    args = parser.parse_args(argv)

    with open(args.results, encoding="utf-8") as fh:
        results = json.load(fh)
    before = results["before"]
    old_copy = Path(results["tree"])
    tree = Path(args.tree)
    moved = moved_files(args.repo, args.old_base, args.new_base)
    reads = {}
    for item in args.reads:
        suite, _, path = item.partition("=")
        reads.setdefault(suite, []).append(path)

    leftover = {rel: {"before": want, "old_copy_now": sha256_of(old_copy / rel)} for rel, want in before.items()}
    leftover_bad = sorted(rel for rel, row in leftover.items() if row["before"] != row["old_copy_now"])
    in_tree = {rel: sha256_of(tree / rel) for rel in before}

    rows = []
    for mutant in results["mutants"]:
        paths = sorted({edit["path"] for edit in mutant.get("edits", [])})
        suite = mutant["suite"]
        if suite.endswith(".py"):
            paths = sorted(set(paths) | {suite})
        changed = [rel for rel in paths if rel in before and in_tree[rel] != before[rel]]
        unknown = [rel for rel in paths if rel not in before]
        moved_hit = sorted({rel for rel in paths if rel in moved} | {rel for rel in reads.get(suite, []) if rel in moved})
        keep = not changed and not moved_hit
        rows.append({"id": mutant["id"], "suite": suite, "paths": paths, "result_s7": mutant["result"], "bytes_changed": changed, "not_hashed_s7": unknown, "main_moved": moved_hit, "decision": "keep" if keep else "re-run"})

    with open(Path(args.pre_s8) / "SHA256SUMS", encoding="utf-8") as fh:
        pre = dict(reversed(line.strip().split(None, 1)) for line in fh if line.strip())
    with open(args.manifest, encoding="utf-8") as fh:
        now = {entry["path"]: entry["sha256"] for entry in json.load(fh)["files"]}
    carrier_delta = {
        "changed": sorted(rel for rel in pre if rel in now and pre[rel] != now[rel]),
        "new": sorted(rel for rel in now if rel not in pre),
        "gone": sorted(rel for rel in pre if rel not in now),
    }

    out = {
        "old_base": args.old_base,
        "new_base": args.new_base,
        "main_moved": moved,
        "old_copy": str(old_copy),
        "old_copy_leftover_mismatch": leftover_bad,
        "old_copy_hashes": leftover,
        "tree": str(tree),
        "tree_hashes": in_tree,
        "carrier_pre_s8_vs_now": carrier_delta,
        "mutants": rows,
        "keep": [row["id"] for row in rows if row["decision"] == "keep"],
        "re_run": [row["id"] for row in rows if row["decision"] == "re-run"],
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print("old copy leftover mismatches:", leftover_bad)
    print("carrier pre-s8 -> now:", json.dumps(carrier_delta))
    print("keep (%d): %s" % (len(out["keep"]), " ".join(out["keep"])))
    print("re-run (%d): %s" % (len(out["re_run"]), " ".join(out["re_run"])))
    for row in rows:
        if row["decision"] == "re-run":
            print("  %s: bytes_changed=%s main_moved=%s" % (row["id"], row["bytes_changed"], row["main_moved"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
