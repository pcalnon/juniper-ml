#!/usr/bin/env python3
"""
Check the restored ~/.claude/mcp-servers trees against the audited state and the March npm install (turing H5).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-21
Status: ad-hoc — investigation (the evidence behind the restored-state risk analysis)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md;
         notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md;
         util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py (whose provenance functions this reuses);
         reports/2026-10-21_turing-h5-restore/ (the March baselines)

On 2026-10-21 both trees were removed at the owner's choice, then restored at the owner's reconsideration:
`git clone --revision=<audited commit>` for each, and for agi-mcp-server an offline `npm ci --ignore-scripts`
from npm's own cache, resolved with `--before` the March install. This script checks that state. Like the
inventory script it never runs code from the trees and never runs git inside them; the network use is
read-only `gh api` GETs, and the client configs are read by key name only.

Checks:
  provenance   each tree's HEAD is the audited commit, its origin the expected repository, with no command-running
               git config key and no live hook; online, every tracked file also matches upstream at HEAD (offline
               the check says the tree was not compared)
  npm-lock     agi-mcp-server's package-lock.json holds exactly the March lockfile's package@version pairs
  npm-tree     node_modules holds exactly the March install's package@version pairs
  no-scripts   no install-time code ran: every esbuild bin/esbuild is the stock node shim, not a native binary,
               and no package has a node-gyp build/config.gypi
  agot-claude  adaptive-graph-of-thoughts' tracked .claude/settings.local.json: its allow and deny counts, and
               whether it sets hooks or disableAllHooks (reported; the file is upstream's and stays a hazard)
  configured   neither server is named in, or pointed at by, a known MCP client config, and every config that
               exists parses. Project .mcp.json files are searched under ~/Development/python/Juniper only. It reads
               ~/.claude.json by key name, so only the owner's account can reproduce it
  processes    no running process names either tree, and none holds a file or working directory under the root
               (lsof +D)
  advisories   active GitHub advisories for the installed npm set, by severity (reported, not judged)

    python3 -I util/ad-hoc/2026-10-21_turing_h5_restore_check.py [--root DIR] [--json] [--offline]

Exit 0 = every judged check passed; 1 = a judged check failed; 2 = usage or environment error.
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import subprocess  # nosec B404 -- ps and gh api GETs only
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
INVENTORY = REPO / "util" / "ad-hoc" / "2026-10-21_turing_h5_mcp_server_inventory.py"
BASELINES = REPO / "reports" / "2026-10-21_turing-h5-restore"
EXPECTED = {
    "adaptive-graph-of-thoughts": ("1f7c6cee241aa387399848e323e66c665e82b7df", "SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server"),
    "agi-mcp-server": ("9eceac9e214896c3af0ba5d3f4b7bd1770cda07a", "QuixiAI/agi-mcp-server"),
}
JUNIPER_TREE = Path.home() / "Development" / "python" / "Juniper"  # where the configured check looks for project .mcp.json files
NPM_TREE = "agi-mcp-server"
AGOT = "adaptive-graph-of-thoughts"
SEVERITIES = ("critical", "high", "medium", "low")


def load_inventory() -> Any:
    sys.dont_write_bytecode = True  # read-only: no __pycache__ beside the inventory script
    spec = importlib.util.spec_from_file_location("h5_inventory", INVENTORY)
    if spec is None or spec.loader is None:
        raise SystemExit(f"error: cannot load {INVENTORY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_pairs(path: Path) -> set[str]:
    with open(path, encoding="utf-8") as fh:
        return {line.strip() for line in fh if line.strip()}


def package_roots(tree: Path) -> list[Path]:
    """The package.json of every node_modules/<name> and node_modules/@scope/<name>, at any depth."""
    roots = []
    for manifest in sorted((tree / "node_modules").rglob("package.json")):
        parts = manifest.parent.relative_to(tree).as_posix().split("/")
        if parts[-2] == "node_modules" or (len(parts) >= 3 and parts[-3] == "node_modules" and parts[-2].startswith("@")):
            roots.append(manifest)
    return roots


def installed_pairs(tree: Path, inv: Any) -> tuple[set[str], int]:
    pairs, dirs = set(), 0
    for manifest in package_roots(tree):
        meta = inv.load_json(manifest)
        if meta is not None:
            dirs += 1
            pairs.add(f"{meta.get('name')}@{meta.get('version')}")
    return pairs, dirs


def lock_pairs(tree: Path, inv: Any) -> set[str]:
    lock = inv.load_json(tree / "package-lock.json") or {}
    return {
        f"{entry.get('name') or rel.split('node_modules/')[-1]}@{entry.get('version')}"
        for rel, entry in (lock.get("packages") or {}).items()
        if rel and isinstance(entry, dict)
    }


def diff(have: set[str], want: set[str]) -> dict:
    return {"extra": sorted(have - want), "missing": sorted(want - have)}


def check_no_scripts(tree: Path) -> dict:
    shims: list[str] = []
    native: list[str] = []
    for shim in sorted((tree / "node_modules").rglob("esbuild/bin/esbuild")):
        with open(shim, "rb") as fh:
            head = fh.read(4)
        (shims if head.startswith(b"#!") else native).append(shim.relative_to(tree).as_posix())
    # node-gyp configure writes build/config.gypi; a tarball's prebuilt build/Release would not count as a build
    builds = sorted(p.parent.relative_to(tree).as_posix() for p in (tree / "node_modules").rglob("build/config.gypi"))
    return {"esbuild_shims": shims, "esbuild_native": native, "node_gyp_builds": builds, "ok": bool(shims) and not native and not builds}


def check_agot_claude(tree: Path, inv: Any) -> dict:
    path = tree / ".claude" / "settings.local.json"
    data = inv.load_json(path)
    if data is None:
        return {"present": path.exists(), "parsed": False}
    perms = data.get("permissions") or {}
    return {
        "present": True,
        "parsed": True,
        "top_level_keys": sorted(data),
        "allow": len(perms.get("allow") or []),
        "deny": len(perms.get("deny") or []),
        "sets_hooks": "hooks" in data,
        "sets_disableAllHooks": "disableAllHooks" in data,
    }


def check_processes(root: Path) -> dict:
    """No command line names a tree, and no process holds a file or working directory under the root."""
    proc = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True, check=False)  # nosec B603 B607
    needles = [str(root)] + list(EXPECTED)
    me = str(Path(__file__).name)
    hits = [line.strip()[:160] for line in proc.stdout.splitlines() if any(n in line for n in needles) and me not in line]
    # lsof exits 1 when nothing matches; +D walks the whole root, so it also sees a server started with a relative path
    lsof = subprocess.run(["lsof", "+D", str(root)], capture_output=True, text=True, timeout=300, check=False)  # nosec B603 B607
    open_files = [line[:160] for line in lsof.stdout.splitlines()[1:]]
    return {"command_lines": hits, "open_files": open_files, "ok": not hits and not open_files}


def advisories(pairs: set[str]) -> dict:
    """Active (not withdrawn) advisories affecting the given npm package@version pairs."""
    query = "advisories?ecosystem=npm&per_page=100&affects=" + ",".join(sorted(pairs))
    proc = subprocess.run(["gh", "api", "--paginate", query], capture_output=True, text=True, timeout=300, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout).strip()[:300]}
    decoder, text, pos, items = json.JSONDecoder(), proc.stdout, 0, []
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text):
            break
        page, pos = decoder.raw_decode(text, pos)
        items.extend(page if isinstance(page, list) else [page])
    names = {pair.rsplit("@", 1)[0] for pair in pairs}
    active, withdrawn = {}, 0
    for item in items:
        if item.get("withdrawn_at"):
            withdrawn += 1
            continue
        hit = sorted({v["package"]["name"] for v in item.get("vulnerabilities") or [] if (v.get("package") or {}).get("name") in names})
        active[item["ghsa_id"]] = {"severity": item.get("severity"), "cve": item.get("cve_id"), "packages": hit, "summary": (item.get("summary") or "")[:120]}
    counts = {sev: sum(1 for a in active.values() if a["severity"] == sev) for sev in SEVERITIES}
    return {"active": len(active), "by_severity": counts, "withdrawn_excluded": withdrawn, "advisories": dict(sorted(active.items()))}


def run(root: Path, offline: bool) -> dict:
    inv = load_inventory()
    collected = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result: dict = {"collected": collected, "root": str(root), "checks": {}}
    checks = result["checks"]
    prov = {}
    for name, (sha, slug) in EXPECTED.items():
        tree = root / name
        meta = inv.git_metadata(tree) if tree.is_dir() else {"git": False}
        origin = (meta.get("remotes") or {}).get("origin") or ""
        entry = {"present": tree.is_dir(), "head": meta.get("head_sha"), "head_ref": meta.get("head_ref"), "origin": origin,
                 "exec_config_keys": meta.get("exec_config_keys"), "live_hooks": meta.get("live_hooks")}
        entry["ok"] = (entry["present"] and meta.get("head_sha") == sha and inv.github_slug(origin) == slug
                       and not meta.get("exec_config_keys") and not meta.get("live_hooks"))
        entry["tree_compared"] = False
        if entry["ok"] and not offline:
            entry["tree_compared"] = True
            up = inv.upstream(slug, sha)
            remote_tree = up.get("tree")
            if remote_tree is None:
                entry["tree_compare"] = {"error": up.get("tree_error") or up.get("error")}
                entry["ok"] = False
            else:
                cmp_ = inv.compare_trees(inv.working_tree(tree), remote_tree)
                local_only = [i["path"] for i in cmp_["local_only"] if not (name == NPM_TREE and i["path"] == "package-lock.json")]
                entry["tree_compare"] = {"identical": cmp_["identical"], "modified": cmp_["modified"], "local_only": [i["path"] for i in cmp_["local_only"]], "missing_locally": cmp_["missing_locally"]}
                entry["ok"] = not cmp_["modified"] and not cmp_["missing_locally"] and not local_only
        prov[name] = entry
    checks["provenance"] = prov

    npm_tree = root / NPM_TREE
    lock = diff(lock_pairs(npm_tree, inv), read_pairs(BASELINES / "march-lockfile-packages.txt"))
    checks["npm-lock"] = {**lock, "ok": not lock["extra"] and not lock["missing"]}
    pairs, dirs = installed_pairs(npm_tree, inv)
    tree_diff = diff(pairs, read_pairs(BASELINES / "march-installed-packages.txt"))
    checks["npm-tree"] = {"package_dirs": dirs, "distinct": len(pairs), **tree_diff, "ok": not tree_diff["extra"] and not tree_diff["missing"]}
    checks["no-scripts"] = check_no_scripts(npm_tree)
    checks["agot-claude"] = check_agot_claude(root / AGOT, inv)
    configured = inv.configured(root, JUNIPER_TREE)
    matched = [item["config"] for item in configured["configs"] if item.get("matches")]
    unparsed = [item["config"] for item in configured["configs"] if item.get("exists") and item.get("parsed") is False]
    checks["configured"] = {"configs": configured["configs"], "matched": matched, "unparsed": unparsed,
                            "project_mcp_json_scope": str(JUNIPER_TREE), "ok": not matched and not unparsed}
    checks["processes"] = check_processes(root)
    if not offline:
        checks["advisories"] = advisories(pairs)
    judged = [checks["npm-lock"]["ok"], checks["npm-tree"]["ok"], checks["no-scripts"]["ok"], checks["configured"]["ok"], checks["processes"]["ok"]]
    judged += [entry["ok"] for entry in prov.values()]
    result["ok"] = all(judged)
    return result


def print_text(result: dict) -> None:
    checks = result["checks"]
    print(f"collected {result['collected']} from {result['root']}")
    for name, entry in checks["provenance"].items():
        status = "PASS" if entry["ok"] else "FAIL"
        if entry["ok"] and not entry["tree_compared"]:
            status = "PASS (HEAD, origin, config and hooks only; tree not compared)"
        print(f"{status}  provenance {name}: HEAD {entry['head']} ({entry['head_ref'] or 'detached'}), origin {entry['origin']}, "
              f"exec config keys {entry['exec_config_keys'] or 'none'}, live hooks {entry['live_hooks'] or 'none'}")
        if "tree_compare" in entry:
            print(f"      tree vs upstream@HEAD: {json.dumps(entry['tree_compare'], sort_keys=True)}")
    for key in ("npm-lock", "npm-tree", "no-scripts", "configured", "processes"):
        entry = checks[key]
        shown = {k: v for k, v in entry.items() if k not in ("ok", "configs")}
        print(f"{'PASS' if entry['ok'] else 'FAIL'}  {key}: {json.dumps(shown, sort_keys=True)}")
    print(f"INFO  agot-claude: {json.dumps(checks['agot-claude'], sort_keys=True)}")
    adv = checks.get("advisories")
    if adv:
        if "error" in adv:
            print(f"INFO  advisories: ERROR {adv['error']}")
        else:
            print(f"INFO  advisories: {adv['active']} active {json.dumps(adv['by_severity'])}, {adv['withdrawn_excluded']} withdrawn excluded")
            for ghsa, item in adv["advisories"].items():
                if item["severity"] in ("critical", "high"):
                    print(f"      {item['severity']:<8} {ghsa} {item['cve'] or '-'} {','.join(item['packages'])}: {item['summary']}")
    print(f"\nresult: {'every judged check passed' if result['ok'] else 'a judged check FAILED'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path.home() / ".claude" / "mcp-servers", help="directory holding the server trees")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    parser.add_argument("--offline", action="store_true", help="skip the GitHub GETs (no upstream tree comparison, no advisories)")
    args = parser.parse_args(argv)
    root = args.root.expanduser()
    if not all((root / name).is_dir() for name in EXPECTED):
        print(f"error: {root} does not hold both trees: {', '.join(EXPECTED)}", file=sys.stderr)
        return 2
    result = run(root, args.offline)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
