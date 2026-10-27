#!/usr/bin/env python3
"""
Read-only evidence behind H6's application record: Settings Sync's reach, the structural diff, other Serena entries.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-26
Status: ad-hoc — investigation (the evidence behind erratum E-H6-APPLY)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.3, erratum E-H6-APPLY);
         util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py (what was applied, and its --check)

The application's own script verifies the decisions. This one backs the record's other claims, and prints no value:

  sync      how VS Code's installed workbench registers chat.mcp.autostart and chat.mcp.gallery.enabled. Settings Sync
            skips a setting registered with a machine scope or ignoreSync, so a registration with neither syncs;
  diff      the backup against the live files, by leaf key path: what was removed, added or changed;
  history   how many local-history entries VS Code keeps for the user mcp.json and settings.json;
  serena    every MCP server entry in a known client config that would run Serena, and whether it pins a commit;
  wheel     whether uv's cache holds a cryptography 50 wheel, which would let an unpinned Serena 2.x start (E-H4-WHEEL).

    python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_evidence.py [--backup DIR] [--section NAME ...]

Exit 0 = every requested section was printed; 2 = a file a section needs is missing.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from pathlib import Path

HOME = Path.home()
USER_DIR = {
    "Darwin": HOME / "Library" / "Application Support" / "Code" / "User",
    "Linux": HOME / ".config" / "Code" / "User",
}.get(platform.system(), HOME / ".config" / "Code" / "User")
WORKBENCH = {
    "Darwin": Path("/Applications/Visual Studio Code.app/Contents/Resources/app/out/vs/workbench/workbench.desktop.main.js"),
    "Linux": Path("/usr/share/code/resources/app/out/vs/workbench/workbench.desktop.main.js"),
}.get(platform.system(), Path("/usr/share/code/resources/app/out/vs/workbench/workbench.desktop.main.js"))
BACKUP = HOME / ".local" / "state" / "juniper" / "quarantine" / "2026-10-26-vscode-mcp"
SETTINGS = ("chat.mcp.autostart", "chat.mcp.gallery.enabled")
SERENA_PIN = re.compile(r"github\.com/oraios/serena(?:\.git)?@[0-9a-f]{40}\b")
JUNIPER = HOME / "Development" / "python" / "Juniper"
CLIENT_CONFIGS = (
    HOME / ".claude.json",
    HOME / ".claude" / "settings.json",
    HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    HOME / ".cursor" / "mcp.json",
    HOME / ".codeium" / "windsurf" / "mcp_config.json",
    USER_DIR / "mcp.json",
    USER_DIR / "settings.json",
)


def tilde(path: Path) -> str:
    return str(path).replace(str(HOME), "~")


def load_jsonc(path: Path) -> object:
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", path.read_text(encoding="utf-8")))


def registration(bundle: str, key: str) -> list[str]:
    """Each registration of `key` in the minified workbench, as the object literal its bound variable indexes."""
    found = []
    for bind in re.finditer(r'([A-Za-z_$][\w$]*)="' + re.escape(key) + '"', bundle):
        for reg in re.finditer(r"\[" + re.escape(bind.group(1)) + r"\]:\{", bundle):
            depth, text = 0, bundle[reg.start():reg.start() + 2000]
            for i, ch in enumerate(text):
                depth += (ch == "{") - (ch == "}")
                if ch == "}" and depth == 0:
                    found.append(text[:i + 1])
                    break
    return found


def section_sync() -> int:
    if not WORKBENCH.is_file():
        print("sync: %s is missing" % WORKBENCH, file=sys.stderr)
        return 2
    bundle = WORKBENCH.read_text(encoding="utf-8", errors="replace")
    for key in SETTINGS:
        regs = registration(bundle, key)
        for reg in regs:
            scope = re.search(r"scope:([^,}]+)", reg)
            default = re.search(r"default:([^,}]+)", reg)
            print("sync  %-26s default %-18s scope %-22s ignoreSync %s" % (
                key, default.group(1) if default else "?", scope.group(1) if scope else "(none: window)", "ignoreSync:" in reg))
        if not regs:
            print("sync  %-26s no registration found" % key)
    return 0


def leaves(node: object, prefix: str = ""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from leaves(value, "%s/%s" % (prefix, key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            label = value.get("id") if isinstance(value, dict) and "id" in value else i
            yield from leaves(value, "%s/[%s]" % (prefix, label))
    else:
        yield prefix, json.dumps(node)


def section_diff(backup: Path) -> int:
    status = 0
    for name in ("mcp.json", "settings.json"):
        if not (backup / name).is_file() or not (USER_DIR / name).is_file():
            print("diff: %s is missing from %s or %s" % (name, tilde(backup), tilde(USER_DIR)), file=sys.stderr)
            status = 2
            continue
        old, new = dict(leaves(load_jsonc(backup / name))), dict(leaves(load_jsonc(USER_DIR / name)))
        gone = sorted(set(old) - set(new))
        added = sorted(set(new) - set(old))
        changed = sorted(k for k in set(old) & set(new) if old[k] != new[k])
        groups = sorted({"/".join(k.split("/")[:3]) for k in gone})
        print("diff  %-13s %d leaves before, %d after; removed %d, under %d groups; added %s; changed %s" % (
            name, len(old), len(new), len(gone), len(groups), added or "none", changed or "none"))
        for group in groups:
            print("        removed under %s" % group)
    return status


def section_history() -> int:
    counts = {"mcp.json": 0, "settings.json": 0}
    for entries in (USER_DIR / "History").glob("*/entries.json"):
        try:
            resource = json.loads(entries.read_text(encoding="utf-8")).get("resource", "")
        except (OSError, ValueError):
            continue
        for name in counts:
            counts[name] += resource.endswith("/User/" + name)
    print("history  local-history entries: %s" % ", ".join("%s %d" % item for item in counts.items()))
    return 0


def server_tables(data: object):
    if not isinstance(data, dict):
        return
    for key in ("mcpServers", "servers", "amp.mcpServers"):
        if isinstance(data.get(key), dict):
            yield key, data[key]
    projects = data.get("projects")
    if isinstance(projects, dict):
        for path, project in projects.items():
            if isinstance(project, dict) and isinstance(project.get("mcpServers"), dict):
                yield "projects[%s].mcpServers" % path.replace(str(HOME), "~"), project["mcpServers"]


def section_serena() -> int:
    configs = list(CLIENT_CONFIGS) + sorted(JUNIPER.glob("*/.mcp.json")) + sorted(JUNIPER.glob("*/.claude/worktrees/*/.mcp.json"))
    for path in configs:
        if not path.is_file():
            continue
        try:
            data = load_jsonc(path)
        except (OSError, ValueError):
            print("serena  %s: not JSON" % tilde(path))
            continue
        total, hits = 0, []
        for table_name, table in server_tables(data):
            for name, entry in table.items():
                total += 1
                if not isinstance(entry, dict):
                    continue
                words = " ".join([str(entry.get("command", "")), str(entry.get("url", ""))] + [a for a in entry.get("args", []) if isinstance(a, str)])
                if "serena" in words.lower():
                    hits.append("%s[%s] pinned=%s" % (table_name, name, "yes" if SERENA_PIN.search(words) else "NO"))
        print("serena  %s: %d server entries; Serena: %s" % (tilde(path), total, "; ".join(hits) or "none"))
    return 0


def section_wheel() -> int:
    cache = HOME / ".cache" / "uv"
    wheels = sorted(tilde(p) for p in cache.rglob("cryptography-50*.whl")) if cache.is_dir() else []
    sdists = cache / "sdists-v9" / "pypi" / "cryptography"
    print("wheel  cryptography 50 wheels in uv's cache: %s; sdist versions: %s" % (
        wheels or "none", sorted(p.name for p in sdists.iterdir()) if sdists.is_dir() else "none"))
    return 0


def main(argv: list | None = None) -> int:
    names = ("sync", "diff", "history", "serena", "wheel")
    ap = argparse.ArgumentParser(description="Read-only evidence behind H6's application record (E-H6-APPLY).")
    ap.add_argument("--backup", type=Path, default=BACKUP, help="the application's backup directory (diff)")
    ap.add_argument("--section", action="append", choices=names, help="repeatable; default: every section")
    args = ap.parse_args(argv)
    runs = {"sync": section_sync, "diff": lambda: section_diff(args.backup), "history": section_history,
            "serena": section_serena, "wheel": section_wheel}
    return max(runs[name]() for name in (args.section or names))


if __name__ == "__main__":
    sys.exit(main())
