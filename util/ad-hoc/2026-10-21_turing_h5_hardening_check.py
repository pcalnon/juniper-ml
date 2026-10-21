#!/usr/bin/env python3
"""
Check the ~/.claude/mcp-servers trees as kept under H5's option B: dormant and hardened, otherwise as restored (turing H5).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-21
Status: ad-hoc — investigation (the evidence behind H5's option B record in the turing plan, v1.4.5)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md (§7, option B);
         notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, H5);
         util/ad-hoc/2026-10-21_turing_h5_restore_check.py (whose checks this reuses);
         reports/2026-10-21_turing-h5-hardening/ (this check's output, before and after B)

On 2026-10-21 the owner chose the risk analysis' option B: keep both trees, dormant and hardened. The agent
applied B.1 to B.3, each a reversible step in place:
  B.1  adaptive-graph-of-thoughts' .claude/settings.local.json renamed to settings.local.json.h5-disabled
  B.2  its three .dxt bundles and the .zip renamed with the same .h5-disabled suffix
  B.3  agi-mcp-server/.npmrc written with ignore-scripts=true
B.4 (a standing Little Snitch rule for the Cellar node) and B.5 (`git remote remove origin` in each tree) are
the owner's. After B the restore check's provenance fails by design; this check accepts exactly option B's
deviations and judges the restore check's other checks unchanged. Like the scripts it builds on, it never runs
code from the trees and never runs git inside them.

Checks:
  b1-allow-list  the allow list is absent at its own path, and its .h5-disabled rename holds upstream's bytes
  b2-bundles     each bundle is absent at its own path, and its .h5-disabled rename holds upstream's bytes
  b3-npmrc       agi-mcp-server/.npmrc is exactly "ignore-scripts=true"
  provenance     each tree's HEAD is the audited commit, with no other remote, no command-running git config key
                 and no live hook; its origin is the expected repository, or absent once the owner has run B.5.
                 Online, the tree differs from upstream at HEAD by exactly B's renames and .npmrc, plus agi's
                 regenerated lockfile (offline the check says the tree was not compared)
  npm-lock, npm-tree, no-scripts, configured, processes
                 the restore check's own checks, judged as there (processes excludes this script's command lines)
  b5-origin      whether the owner has removed each origin (reported)
  advisories     active GitHub advisories for the installed npm set, by severity (reported; online only)
B.4 has no machine check: Little Snitch's rules are not read here.

    python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py [--root DIR] [--json] [--offline]

Exit 0 = every judged check passed; 1 = a judged check failed; 2 = usage or environment error.
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import subprocess  # nosec B404 -- ps and lsof only; the GitHub GETs run through the inventory script's helpers
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
RESTORE_CHECK = REPO / "util" / "ad-hoc" / "2026-10-21_turing_h5_restore_check.py"
AGOT = "adaptive-graph-of-thoughts"
NPM_TREE = "agi-mcp-server"
SUFFIX = ".h5-disabled"
# upstream's blob ids at the audited commit, read from the files just before B.1 and B.2 renamed them
ALLOW_LIST = {".claude/settings.local.json": "f2a0c8fc6f82197500feed1007c6131f8d6d2c62"}
BUNDLES = {
    "Adaptive-Graph-of-Thoughts-MCP-server.dxt": "f02905b36005ca4ebe8cfbb6be864f7b13c7c55c",
    "adaptive-graph-of-thoughts-v1.0.1-submission.dxt": "3f23937b5b16e60753e3b4a6dd04653ce66dc9b8",
    "adaptive-graph-of-thoughts-v1.0.2-final.dxt": "0052971aec78a40004d2db1eed80e30ab3ff1b77",
    "adaptive-graph-of-thoughts-dxt-v1.0.0-production.zip": "a470c37885ac70290864454fa48d320401011944",
}
NPMRC = ".npmrc"
NPMRC_CONTENT = b"ignore-scripts=true\n"
# B's expected differences from upstream at HEAD, per tree
EXPECTED_MISSING = {AGOT: set(ALLOW_LIST) | set(BUNDLES), NPM_TREE: set()}
EXPECTED_LOCAL_ONLY = {AGOT: {rel + SUFFIX for rel in EXPECTED_MISSING[AGOT]}, NPM_TREE: {"package-lock.json", NPMRC}}
REUSED = ("npm-lock", "npm-tree", "no-scripts", "configured", "processes")


def load_restore_check() -> Any:
    sys.dont_write_bytecode = True  # read-only: no __pycache__ beside the restore check
    spec = importlib.util.spec_from_file_location("h5_restore_check", RESTORE_CHECK)
    if spec is None or spec.loader is None:
        raise SystemExit(f"error: cannot load {RESTORE_CHECK}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_renamed(tree: Path, pinned: dict[str, str], inv: Any) -> dict:
    """Each pinned file is gone from its own path, and its rename is a regular file holding the pinned blob."""
    files = {}
    for rel, blob in pinned.items():
        original, renamed = tree / rel, tree / (rel + SUFFIX)
        regular = renamed.is_file() and not renamed.is_symlink()
        files[rel] = {
            "original_present": original.exists() or original.is_symlink(),
            "renamed_present": regular,
            "blob_matches": regular and inv.blob_sha(renamed) == blob,
        }
    ok = all(not f["original_present"] and f["renamed_present"] and f["blob_matches"] for f in files.values())
    return {"files": files, "ok": ok}


def check_npmrc(tree: Path) -> dict:
    path = tree / NPMRC
    data = path.read_bytes() if path.is_file() and not path.is_symlink() else None
    return {"present": data is not None, "ok": data == NPMRC_CONTENT}


def provenance(root: Path, rc: Any, inv: Any, offline: bool) -> dict:
    prov = {}
    for name, (sha, slug) in rc.EXPECTED.items():
        tree = root / name
        meta = inv.git_metadata(tree) if tree.is_dir() else {"git": False}
        remotes = meta.get("remotes") or {}
        origin = remotes.get("origin")
        entry = {"present": tree.is_dir(), "head": meta.get("head_sha"), "head_ref": meta.get("head_ref"), "origin": origin,
                 "other_remotes": sorted(set(remotes) - {"origin"}), "exec_config_keys": meta.get("exec_config_keys"),
                 "live_hooks": meta.get("live_hooks")}
        # B.5 removes origin; any other origin, or any second remote, is a deviation
        entry["ok"] = (entry["present"] and meta.get("head_sha") == sha and (origin is None or inv.github_slug(origin) == slug)
                       and not entry["other_remotes"] and not meta.get("exec_config_keys") and not meta.get("live_hooks"))
        entry["tree_compared"] = False
        if entry["ok"] and not offline:
            entry["tree_compared"] = True
            up = inv.upstream(slug, sha)  # the slug comes from EXPECTED, so a removed origin does not stop the comparison
            remote_tree = up.get("tree")
            if remote_tree is None:
                entry["tree_compare"] = {"error": up.get("tree_error") or up.get("error")}
                entry["ok"] = False
            else:
                cmp_ = inv.compare_trees(inv.working_tree(tree), remote_tree)
                local_only = sorted(i["path"] for i in cmp_["local_only"])
                entry["tree_compare"] = {"identical": cmp_["identical"], "modified": cmp_["modified"], "local_only": local_only,
                                         "missing_locally": cmp_["missing_locally"]}
                entry["ok"] = (not cmp_["modified"] and set(cmp_["missing_locally"]) == EXPECTED_MISSING[name]
                               and set(local_only) == EXPECTED_LOCAL_ONLY[name])
                if name == AGOT:  # the pins must still be upstream's own blobs for the original paths
                    entry["pins_match_upstream"] = all(remote_tree.get(rel) == blob for rel, blob in {**ALLOW_LIST, **BUNDLES}.items())
                    entry["ok"] = entry["ok"] and entry["pins_match_upstream"]
        prov[name] = entry
    return prov


def check_processes(root: Path, rc: Any) -> dict:
    """The restore check's process check, excluding this script's command lines instead of its own.

    A --root names the root on this script's command line, and on any shell that launched it.
    """
    proc = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True, check=False)  # nosec B603 B607
    needles = [str(root)] + list(rc.EXPECTED)
    me = Path(__file__).name
    hits = [line.strip()[:160] for line in proc.stdout.splitlines() if any(n in line for n in needles) and me not in line]
    lsof = subprocess.run(["lsof", "+D", str(root)], capture_output=True, text=True, timeout=300, check=False)  # nosec B603 B607
    open_files = [line[:160] for line in lsof.stdout.splitlines()[1:]]
    return {"command_lines": hits, "open_files": open_files, "ok": not hits and not open_files}


def run(root: Path, offline: bool) -> dict:
    rc = load_restore_check()
    inv = rc.load_inventory()
    collected = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result: dict = {"collected": collected, "root": str(root), "checks": {}}
    checks = result["checks"]
    checks["b1-allow-list"] = check_renamed(root / AGOT, ALLOW_LIST, inv)
    checks["b2-bundles"] = check_renamed(root / AGOT, BUNDLES, inv)
    checks["b3-npmrc"] = check_npmrc(root / NPM_TREE)
    checks["provenance"] = provenance(root, rc, inv, offline)
    # the restore check's npm, no-scripts and configured checks, judged as in its run()
    npm_tree = root / NPM_TREE
    lock = rc.diff(rc.lock_pairs(npm_tree, inv), rc.read_pairs(rc.BASELINES / "march-lockfile-packages.txt"))
    checks["npm-lock"] = {**lock, "ok": not lock["extra"] and not lock["missing"]}
    pairs, dirs = rc.installed_pairs(npm_tree, inv)
    tree_diff = rc.diff(pairs, rc.read_pairs(rc.BASELINES / "march-installed-packages.txt"))
    checks["npm-tree"] = {"package_dirs": dirs, "distinct": len(pairs), **tree_diff, "ok": not tree_diff["extra"] and not tree_diff["missing"]}
    checks["no-scripts"] = rc.check_no_scripts(npm_tree)
    configured = inv.configured(root, rc.JUNIPER_TREE)
    matched = [item["config"] for item in configured["configs"] if item.get("matches")]
    unparsed = [item["config"] for item in configured["configs"] if item.get("exists") and item.get("parsed") is False]
    checks["configured"] = {"configs": configured["configs"], "matched": matched, "unparsed": unparsed,
                            "project_mcp_json_scope": str(rc.JUNIPER_TREE), "ok": not matched and not unparsed}
    checks["processes"] = check_processes(root, rc)
    checks["b5-origin"] = {name: ("done" if entry["origin"] is None else "pending") for name, entry in checks["provenance"].items()}
    if not offline:
        checks["advisories"] = rc.advisories(pairs)
    judged = [checks[key]["ok"] for key in ("b1-allow-list", "b2-bundles", "b3-npmrc", *REUSED)]
    judged += [entry["ok"] for entry in checks["provenance"].values()]
    result["ok"] = all(judged)
    return result


def print_text(result: dict) -> None:
    checks = result["checks"]
    print(f"collected {result['collected']} from {result['root']}")
    for key in ("b1-allow-list", "b2-bundles"):
        entry = checks[key]
        renamed = sum(1 for f in entry["files"].values() if f["renamed_present"] and f["blob_matches"] and not f["original_present"])
        print(f"{'PASS' if entry['ok'] else 'FAIL'}  {key}: {renamed} of {len(entry['files'])} renamed to *{SUFFIX}, upstream's bytes")
        if not entry["ok"]:
            print(f"      {json.dumps(entry['files'], sort_keys=True)}")
    npmrc = checks["b3-npmrc"]
    print(f"{'PASS' if npmrc['ok'] else 'FAIL'}  b3-npmrc: {NPM_TREE}/{NPMRC} {'holds' if npmrc['ok'] else 'does not hold'} exactly ignore-scripts=true")
    for name, entry in checks["provenance"].items():
        status = "PASS" if entry["ok"] else "FAIL"
        if entry["ok"] and not entry["tree_compared"]:
            status = "PASS (HEAD, remotes, config and hooks only; tree not compared)"
        print(f"{status}  provenance {name}: HEAD {entry['head']} ({entry['head_ref'] or 'detached'}), origin {entry['origin'] or 'none (B.5 done)'}, "
              f"other remotes {entry['other_remotes'] or 'none'}, exec config keys {entry['exec_config_keys'] or 'none'}, live hooks {entry['live_hooks'] or 'none'}")
        if "tree_compare" in entry:
            print(f"      tree vs upstream@HEAD: {json.dumps(entry['tree_compare'], sort_keys=True)}")
    for key in REUSED:
        entry = checks[key]
        shown = {k: v for k, v in entry.items() if k not in ("ok", "configs")}
        print(f"{'PASS' if entry['ok'] else 'FAIL'}  {key}: {json.dumps(shown, sort_keys=True)}")
    print(f"INFO  b5-origin (owner): {json.dumps(checks['b5-origin'], sort_keys=True)}")
    print("INFO  b4-node-rule (owner): not machine-checked; Little Snitch's rules are not read here")
    adv = checks.get("advisories")
    if adv:
        if "error" in adv:
            print(f"INFO  advisories: ERROR {adv['error']}")
        else:
            print(f"INFO  advisories: {adv['active']} active {json.dumps(adv['by_severity'])}, {adv['withdrawn_excluded']} withdrawn excluded")
    print(f"\nresult: {'every judged check passed' if result['ok'] else 'a judged check FAILED'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path.home() / ".claude" / "mcp-servers", help="directory holding the server trees")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    parser.add_argument("--offline", action="store_true", help="skip the GitHub GETs (no upstream tree comparison, no advisories)")
    args = parser.parse_args(argv)
    root = args.root.expanduser()
    rc = load_restore_check()
    if not all((root / name).is_dir() for name in rc.EXPECTED):
        print(f"error: {root} does not hold both trees: {', '.join(rc.EXPECTED)}", file=sys.stderr)
        return 2
    result = run(root, args.offline)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
