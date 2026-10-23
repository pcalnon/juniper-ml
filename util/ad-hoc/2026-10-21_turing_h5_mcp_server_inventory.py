#!/usr/bin/env python3
"""
Read-only inventory of the unvetted MCP servers under ~/.claude/mcp-servers/ (turing bring-up task H5).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-21
Status: ad-hoc — investigation (the evidence behind the H5 audit)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md;
         notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§6 Arc H task H5, §10, D10)

Static only. It never runs code from the audited trees and never runs git inside them, because an
untrusted repository's config or hooks can run commands; .git metadata is read as plain files. The
network use is read-only GitHub REST GETs through `gh api` (no method or field flags). Client config
files are reported by key name and booleans only, never by value, since their env blocks hold secrets.

Sections, per server directory:
  provenance  origin URL, HEAD, reflog actions, shallow flag, command-running git config keys and live
              hooks; the upstream repository's metadata; the working tree compared blob by blob with
              the upstream tree at HEAD (node_modules excluded, it is reported by the npm section)
  npm         node_modules packages with install-time scripts or native builds, versions that differ
              from package-lock.json, and lockfile entries resolved from outside registry.npmjs.org
and once for the host:
  configured  whether either server is named in, or pointed at by, a known MCP client config

    python3 -I util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py [--root DIR] [--json] [--offline]

Exit 0 = the inventory was printed; 2 = usage or environment error (no server directories found).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess  # nosec B404 -- gh api GETs only
import sys
from pathlib import Path
from typing import Any

HOME = Path.home()
DEFAULT_ROOT = HOME / ".claude" / "mcp-servers"
GH = os.environ.get("GH", "gh")
GH_TIMEOUT = 90

# git config keys whose values git runs as commands (or that pull in more config).
EXEC_CONFIG_KEYS = re.compile(
    r"^(core\.(fsmonitor|sshcommand|pager|editor|hookspath|askpass|gitproxy)|"
    r"filter\..+\.(clean|smudge|process)|diff\..+\.(textconv|command)|merge\..+\.driver|"
    r"credential\..*helper|alias\..+|include\.path|includeif\..+\.path|uploadpack\.packobjectshook|"
    r"sequence\.editor|gpg\.program|gpg\..+\.program)$",
    re.IGNORECASE,
)
# npm runs these for a registry dependency; prepare and prepublish run only for the root package or a git dependency.
INSTALL_SCRIPTS = ("preinstall", "install", "postinstall")
SERVER_NAME_HINTS = ("graph-of-thought", "graph_of_thought", "agi-mcp", "agi_mcp")


def read_text(path: Path) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def strip_userinfo(url: str) -> str:
    """Drop any user:token@ part of a URL before it is printed."""
    return re.sub(r"(https?://)[^/@\s]+@", r"\1<userinfo>@", url)


def iso_utc(epoch: str) -> str:
    try:
        return datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return epoch


# --------------------------------------------------------------------------- git metadata, as files


def resolve_head(gitdir: Path) -> tuple[str | None, str | None]:
    head = (read_text(gitdir / "HEAD") or "").strip()
    if not head:
        return None, None
    if not head.startswith("ref: "):
        return None, head
    ref = head[5:].strip()
    loose = read_text(gitdir / ref)
    if loose and loose.strip():
        return ref, loose.strip()
    for line in (read_text(gitdir / "packed-refs") or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and not line.startswith(("#", "^")) and parts[1] == ref:
            return ref, parts[0]
    return ref, None


def parse_git_config(gitdir: Path) -> list[tuple[str, str]]:
    """(dotted key, value) pairs from .git/config, enough for remotes and the exec-key screen."""
    pairs = []
    section = ""
    for raw in (read_text(gitdir / "config") or "").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        header = re.match(r'^\[\s*([^\s\]"]+)(?:\s+"([^"]*)")?\s*\]$', line)
        if header:
            name, sub = header.group(1), header.group(2)
            section = f"{name}.{sub}" if sub is not None else name
            continue
        key, _, value = line.partition("=")
        pairs.append((f"{section}.{key.strip()}".lower() if section else key.strip().lower(), value.strip()))
    return pairs


def reflog(gitdir: Path) -> list[dict]:
    entries = []
    for line in (read_text(gitdir / "logs" / "HEAD") or "").splitlines():
        meta, _, message = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 4:  # <old> <new> <name ...> <email> <epoch> <tz>; the identity is not printed
            entries.append({"new": parts[1], "time": iso_utc(parts[-2]), "action": strip_userinfo(message.strip())})
    return entries


def live_hooks(gitdir: Path) -> list[str]:
    hooks = gitdir / "hooks"
    if not hooks.is_dir():
        return []
    return sorted(p.name for p in hooks.iterdir() if p.is_file() and not p.name.endswith(".sample"))


def git_metadata(tree: Path) -> dict:
    gitdir = tree / ".git"
    if not gitdir.is_dir():
        return {"git": False}
    config = parse_git_config(gitdir)
    remotes = {k.split(".")[1]: strip_userinfo(v) for k, v in config if k.startswith("remote.") and k.endswith(".url")}
    ref, sha = resolve_head(gitdir)
    fetch_head = gitdir / "FETCH_HEAD"
    return {
        "git": True,
        "remotes": remotes,
        "head_ref": ref,
        "head_sha": sha,
        "shallow": (gitdir / "shallow").exists(),
        "reflog": reflog(gitdir),
        "fetch_head_mtime": iso_utc(str(int(fetch_head.stat().st_mtime))) if fetch_head.exists() else None,
        "exec_config_keys": sorted({k for k, _ in config if EXEC_CONFIG_KEYS.match(k)}),
        "live_hooks": live_hooks(gitdir),
    }


# --------------------------------------------------------------------------- working tree vs upstream


def blob_sha(path: Path) -> str:
    """git's blob id: sha1 over 'blob <size>\\0' plus the content (a symlink's content is its target)."""
    if path.is_symlink():
        data = os.readlink(path).encode()
    else:
        with open(path, "rb") as fh:
            data = fh.read()
    digest = hashlib.sha1(b"blob %d\0" % len(data), usedforsecurity=False)
    digest.update(data)
    return digest.hexdigest()


def working_tree(tree: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for dirpath, dirnames, filenames in os.walk(tree, followlinks=False):
        here = Path(dirpath)
        keep = []
        for name in dirnames:
            if name in (".git", "node_modules"):
                continue
            if (here / name).is_symlink():  # git stores a symlinked directory as a blob
                filenames.append(name)
            else:
                keep.append(name)
        dirnames[:] = keep
        for name in filenames:
            path = here / name
            files[path.relative_to(tree).as_posix()] = path
    return files


def gh_json(endpoint: str) -> tuple[Any, str | None]:
    try:
        proc = subprocess.run([GH, "api", endpoint], capture_output=True, text=True, timeout=GH_TIMEOUT, check=False)  # nosec B603
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout).strip()[:300]
    try:
        return json.loads(proc.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"bad JSON: {exc}"


def github_slug(url: str) -> str | None:
    match = re.search(r"github\.com[:/]+([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", url)
    return f"{match.group(1)}/{match.group(2)}" if match else None


def upstream(slug: str, sha: str | None) -> dict:
    out: dict = {"slug": slug}
    repo, err = gh_json(f"repos/{slug}")
    if err:
        out["error"] = err
        return out
    out["repo"] = {
        key: repo.get(key)
        for key in ("full_name", "html_url", "fork", "archived", "disabled", "visibility", "default_branch",
                    "created_at", "pushed_at", "stargazers_count", "forks_count", "open_issues_count")
    }
    out["repo"]["owner"] = (repo.get("owner") or {}).get("login")
    out["repo"]["owner_type"] = (repo.get("owner") or {}).get("type")
    out["repo"]["license"] = (repo.get("license") or {}).get("spdx_id")
    out["repo"]["parent"] = (repo.get("parent") or {}).get("full_name")
    if not sha:
        return out
    commit, err = gh_json(f"repos/{slug}/commits/{sha}")
    if err:
        out["head_commit_error"] = err
    else:
        info = commit.get("commit") or {}
        out["head_commit"] = {
            "date": (info.get("committer") or {}).get("date"),
            "subject": (info.get("message") or "").splitlines()[0][:160] if info.get("message") else "",
            "author_login": (commit.get("author") or {}).get("login"),
            "verified": ((info.get("verification") or {}).get("verified")),
        }
    branch = out["repo"].get("default_branch")
    if branch:
        compare, err = gh_json(f"repos/{slug}/compare/{sha}...{branch}")
        if err:
            out["compare_error"] = err
        else:
            out["compare_to_default"] = {key: compare.get(key) for key in ("status", "ahead_by", "behind_by")}
    tree, err = gh_json(f"repos/{slug}/git/trees/{sha}?recursive=1")
    if err:
        out["tree_error"] = err
    else:
        out["tree_truncated"] = tree.get("truncated")
        out["tree"] = {e["path"]: e["sha"] for e in tree.get("tree", []) if e.get("type") == "blob"}
    return out


def compare_trees(local: dict[str, Path], remote: dict[str, str]) -> dict:
    same, modified, local_only = [], [], []
    for rel, path in sorted(local.items()):
        if rel not in remote:  # a file the host made: its mtime dates the local run that wrote it
            info = path.lstat()
            local_only.append({"path": rel, "bytes": info.st_size, "mtime": iso_utc(str(int(info.st_mtime)))})
        elif blob_sha(path) == remote[rel]:
            same.append(rel)
        else:
            modified.append(rel)
    missing = sorted(set(remote) - set(local))
    return {"identical": len(same), "modified": modified, "local_only": local_only, "missing_locally": missing}


# --------------------------------------------------------------------------- node_modules


def strip_jsonc(text: str) -> str:
    """JSONC (VS Code's mcp.json) to JSON: drop // and /* */ comments outside strings, then trailing commas."""
    out, i, in_string = [], 0, False
    while i < len(text):
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 1
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
            out.append(ch)
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = len(text) if end == -1 else end
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = len(text) if end == -1 else end + 2
            continue
        else:
            out.append(ch)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_json(path: Path, jsonc: bool = False) -> dict | None:
    text = read_text(path)
    if text is None:
        return None
    try:
        data = json.loads(strip_jsonc(text) if jsonc else text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def npm_inventory(tree: Path) -> dict | None:
    modules = tree / "node_modules"
    if not modules.is_dir():
        return None
    lock = load_json(tree / "package-lock.json") or {}
    locked = lock.get("packages") or {}
    installed, scripted, drift = 0, [], []
    for manifest in sorted(modules.rglob("package.json")):
        rel = manifest.parent.relative_to(tree).as_posix()
        parts = rel.split("/")
        # a package root is node_modules/<name> or node_modules/@scope/<name>, at any nesting depth
        if not (parts[-2] == "node_modules" or (len(parts) >= 3 and parts[-3] == "node_modules" and parts[-2].startswith("@"))):
            continue
        meta = load_json(manifest)
        if meta is None:
            continue
        installed += 1
        name_version = f"{meta.get('name')}@{meta.get('version')}"
        scripts = {k: v for k, v in (meta.get("scripts") or {}).items() if k in INSTALL_SCRIPTS}
        native = (manifest.parent / "binding.gyp").exists()
        if scripts or native:
            scripted.append({"package": name_version, "path": rel, "scripts": {k: str(v)[:200] for k, v in scripts.items()}, "binding_gyp": native})
        want = (locked.get(rel) or {}).get("version")
        if want and want != meta.get("version"):
            drift.append({"path": rel, "installed": meta.get("version"), "lockfile": want})
    foreign = sorted(
        {f"{rel}: {strip_userinfo(str(entry.get('resolved')))}" for rel, entry in locked.items()
         if isinstance(entry, dict) and entry.get("resolved") and not str(entry.get("resolved")).startswith("https://registry.npmjs.org/")}
    )
    root_scripts = (load_json(tree / "package.json") or {}).get("scripts") or {}
    marker = modules / ".package-lock.json"  # npm rewrites it on every install
    return {
        "install_marker_mtime": iso_utc(str(int(marker.stat().st_mtime))) if marker.exists() else None,
        # an `npm install` in the tree itself also runs the root package's prepare / prepublish
        "root_lifecycle_scripts": {k: str(v)[:200] for k, v in root_scripts.items() if k in INSTALL_SCRIPTS + ("prepare", "prepublish")},
        "installed_packages": installed,
        "installer": "pnpm" if (modules / ".pnpm").is_dir() else ("npm" if (modules / ".package-lock.json").exists() else "unknown"),
        "lockfiles": sorted(p.name for p in tree.iterdir() if p.name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")),
        "install_time_code": scripted,
        "lockfile_version_drift": drift,
        "non_registry_resolved": foreign,
    }


# --------------------------------------------------------------------------- client configs, keys only


def server_tables(data: dict) -> list[tuple[str, dict]]:
    """The (scope, servers) tables of the known config shapes."""
    tables = []
    for key in ("mcpServers", "servers"):
        if isinstance(data.get(key), dict):
            tables.append((key, data[key]))
    projects = data.get("projects")
    if isinstance(projects, dict):
        for project, cfg in projects.items():
            if isinstance(cfg, dict) and isinstance(cfg.get("mcpServers"), dict) and cfg["mcpServers"]:
                tables.append((f"projects[{project}].mcpServers", cfg["mcpServers"]))
    return tables


def mentions(entry: object, needles: tuple[str, ...]) -> bool:
    """True when a command/args/cwd string of a server entry contains a needle. env is never read."""
    if not isinstance(entry, dict):
        return False
    strings = [entry.get("command"), entry.get("cwd"), entry.get("url")] + list(entry.get("args") or [])
    return any(isinstance(s, str) and any(n in s.lower() for n in needles) for s in strings)


def configured(root: Path, juniper_tree: Path) -> dict:
    needles = tuple(n.lower() for n in SERVER_NAME_HINTS) + (str(root).lower(), "mcp-servers/")
    candidates = [
        ("claude-code ~/.claude.json", HOME / ".claude.json"),
        ("claude-desktop config", HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"),
        ("vscode user mcp.json", HOME / "Library" / "Application Support" / "Code" / "User" / "mcp.json"),
        ("cursor ~/.cursor/mcp.json", HOME / ".cursor" / "mcp.json"),
    ]
    for dirpath, dirnames, filenames in os.walk(juniper_tree):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", ".venv", "venv", "__pycache__")]
        if ".mcp.json" in filenames:
            path = Path(dirpath) / ".mcp.json"
            candidates.append((f"project {path.relative_to(juniper_tree.parent)}", path))
    report = []
    for label, path in candidates:
        if not path.exists():
            report.append({"config": label, "exists": False})
            continue
        data = load_json(path, jsonc=True)
        if data is None:
            report.append({"config": label, "exists": True, "parsed": False})
            continue
        tables = server_tables(data)
        hits = [
            {"scope": scope, "key": key, "name_matches": any(n in key.lower() for n in SERVER_NAME_HINTS), "points_into_mcp_servers": mentions(entry, needles)}
            for scope, servers in tables for key, entry in servers.items()
            if any(n in key.lower() for n in SERVER_NAME_HINTS) or mentions(entry, needles)
        ]
        report.append({"config": label, "exists": True, "parsed": True, "server_tables": len(tables),
                       "server_keys": sum(len(s) for _, s in tables), "matches": hits})
    extensions = HOME / "Library" / "Application Support" / "Claude" / "Claude Extensions"
    report.append({"config": "claude-desktop extensions dir", "exists": extensions.is_dir(),
                   "entries": sorted(p.name for p in extensions.iterdir()) if extensions.is_dir() else []})
    return {"configs": report}


# --------------------------------------------------------------------------- main


def inventory(root: Path, offline: bool) -> dict:
    servers = {}
    for tree in sorted(p for p in root.iterdir() if p.is_dir()):
        meta = git_metadata(tree)
        entry: dict = {"path": str(tree), "provenance": meta}
        origin = (meta.get("remotes") or {}).get("origin")
        slug = github_slug(origin) if origin else None
        if slug and not offline:
            up = upstream(slug, meta.get("head_sha"))
            remote_tree = up.pop("tree", None)
            entry["upstream"] = up
            if remote_tree is not None:
                entry["tree_compare"] = compare_trees(working_tree(tree), remote_tree)
        entry["npm"] = npm_inventory(tree)
        servers[tree.name] = entry
    return servers


def print_text(result: dict) -> None:
    for name, entry in result["servers"].items():
        print(f"== {name}  ({entry['path']})")
        prov = entry["provenance"]
        if not prov.get("git"):
            print("  provenance: no .git directory")
        else:
            print(f"  origin: {prov['remotes'].get('origin')}   other remotes: {sorted(set(prov['remotes']) - {'origin'}) or 'none'}")
            print(f"  HEAD: {prov['head_ref']} @ {prov['head_sha']}   shallow: {prov['shallow']}   FETCH_HEAD mtime: {prov['fetch_head_mtime']}")
            for item in prov["reflog"]:
                print(f"  reflog {item['time']}  {item['new'][:12]}  {item['action']}")
            print(f"  command-running git config keys: {prov['exec_config_keys'] or 'none'}   live hooks: {prov['live_hooks'] or 'none'}")
        up = entry.get("upstream")
        if up:
            if "error" in up:
                print(f"  upstream {up['slug']}: ERROR {up['error']}")
            else:
                print(f"  upstream: {json.dumps(up.get('repo'), sort_keys=True)}")
                print(f"  HEAD commit upstream: {json.dumps(up.get('head_commit') or up.get('head_commit_error'), sort_keys=True)}")
                print(f"  HEAD vs default branch: {json.dumps(up.get('compare_to_default') or up.get('compare_error'), sort_keys=True)}")
                if "tree_error" in up:
                    print(f"  upstream tree: ERROR {up['tree_error']}")
        cmp_ = entry.get("tree_compare")
        if cmp_:
            print(f"  tree vs upstream@HEAD: {cmp_['identical']} identical, {len(cmp_['modified'])} modified, "
                  f"{len(cmp_['local_only'])} local-only, {len(cmp_['missing_locally'])} missing locally")
            for rel in cmp_["modified"]:
                print(f"    modified     {rel}")
            for item in cmp_["local_only"]:
                print(f"    local-only   {item['path']}  ({item['bytes']} bytes, mtime {item['mtime']})")
            for rel in cmp_["missing_locally"]:
                print(f"    missing      {rel}")
        npm = entry.get("npm")
        if npm:
            print(f"  npm: {npm['installed_packages']} packages installed by {npm['installer']} (node_modules/.package-lock.json mtime {npm['install_marker_mtime']}); lockfiles {npm['lockfiles']}")
            print(f"    root package lifecycle scripts: {npm['root_lifecycle_scripts'] or 'none'}")
            for item in npm["install_time_code"]:
                print(f"    install-time code: {item['package']}  scripts={item['scripts']}  binding.gyp={item['binding_gyp']}")
            for item in npm["lockfile_version_drift"]:
                print(f"    version drift: {item['path']} installed {item['installed']} lockfile {item['lockfile']}")
            for item in npm["non_registry_resolved"]:
                print(f"    resolved outside registry.npmjs.org: {item}")
        print()
    print("== configured (keys and booleans only; values are never read out)")
    for item in result["configured"]["configs"]:
        print(f"  {json.dumps(item, sort_keys=True)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=f"directory holding the server trees (default {DEFAULT_ROOT})")
    parser.add_argument("--juniper-tree", type=Path, default=HOME / "Development" / "python" / "Juniper", help="tree searched for project .mcp.json files")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    parser.add_argument("--offline", action="store_true", help="skip the GitHub GETs")
    args = parser.parse_args(argv)
    root = args.root.expanduser()
    if not root.is_dir() or not any(p.is_dir() for p in root.iterdir()):
        print(f"error: no server directories under {root}", file=sys.stderr)
        return 2
    result = {
        "collected": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "servers": inventory(root, args.offline),
        "configured": configured(root, args.juniper_tree.expanduser()),
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"collected {result['collected']} from {result['root']}\n")
        print_text(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
