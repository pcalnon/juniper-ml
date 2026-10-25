#!/usr/bin/env python3
"""
Value-redacted inventory of VS Code's user MCP configuration on turing (turing bring-up task H6).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — investigation (the evidence behind the H6 audit)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.2, task H6; D10);
         notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md (O-5);
         util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py (whose JSONC reader this reuses)

H6 reviews the MCP servers in VS Code's user mcp.json, which neither H0 nor H5 reviewed. Their secrets stay
unread, as in H5: this script reads the files, and what it prints is a default-deny projection of them.

  servers   per server: its name, transport type and command; each argument printed unless it is, or follows,
            a secret-bearing flag, carries KEY=value with a secret-like key, or looks like a token (then
            <redacted: N chars>); a URL as scheme://host[:port]/path, with userinfo dropped, query keys only
            and token-like path segments redacted; env and headers by KEY only, each value classified as
            input-ref, env-ref, empty or literal (N chars); any other key by name and JSON type
  inputs    the inputs array: id, type, password flag (VS Code keeps input values in its secret storage)
  settings  from the user settings.json: every chat.mcp.* and chat.tools.* key, booleans and short enum
            strings printed, objects as their keys with boolean values or value types (command patterns,
            not secrets), anything else by type
  workspace which Juniper checkouts hold a .vscode/mcp.json (existence only)

A ${input:...} or ${env:...} reference is printed as written: it names where VS Code fetches a value, not the
value. No value of an env or headers entry is ever printed, whatever it holds.

    python3 -I util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py [--mcp-json FILE] [--settings FILE] [--json]

Exit 0 = the inventory was printed; 2 = the mcp.json is missing or does not parse.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[2]
H5_INVENTORY = REPO / "util" / "ad-hoc" / "2026-10-21_turing_h5_mcp_server_inventory.py"
HOME = Path.home()
CODE_USER = HOME / "Library" / "Application Support" / "Code" / "User"
JUNIPER = HOME / "Development" / "python" / "Juniper"

SECRET_KEY = re.compile(r"token|secret|passw|pwd|api[-_]?key|apikey|auth|bearer|credential|private|session|cookie", re.IGNORECASE)
SECRET_FLAGS = ("--api-key", "--apikey", "--token", "--key", "--secret", "--password", "--auth", "--header", "-H", "--bearer")
ENV_FLAGS = ("-e", "--env")
TOKEN_PREFIX = re.compile(r"(?:^|[^A-Za-z0-9])(?:hf_|ghp_|gho_|ghs_|ghu_|github_pat_|sk-|xox[abprs]-|ctx7sk|glpat-|AKIA)[A-Za-z0-9_-]{6,}")
LONG_TOKEN = re.compile(r"[A-Za-z0-9+/=_-]{32,}")
SHA = re.compile(r"^[0-9a-f]{7,40}$")
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")  # a registry entry id, not a secret
REFERENCE = re.compile(r"\$\{(?:input|env):[^}]*\}")
SETTINGS_PREFIXES = ("chat.mcp.", "chat.tools.")
SHORT_STRING = 40


def _load_h5():
    spec = importlib.util.spec_from_file_location("h5_inventory", H5_INVENTORY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def classify_value(value: object) -> str:
    """What an env or header value is, never the value itself."""
    if not isinstance(value, str):
        return "non-string (%s)" % type(value).__name__
    if not value:
        return "empty"
    refs = REFERENCE.findall(value)
    if refs and REFERENCE.sub("", value).strip() == "":
        return "reference only: " + ", ".join(refs)
    if refs:
        return "literal text around a reference (%d chars; references: %s)" % (len(value), ", ".join(refs))
    return "literal (%d chars)" % len(value)


def _token_like(text: str) -> bool:
    if TOKEN_PREFIX.search(text):
        return True
    return any(not SHA.match(m.group(0)) for m in LONG_TOKEN.finditer(text))


def sanitize_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return "<redacted: %d chars>" % len(url) if _token_like(url) else url
    host = parts.hostname or ""
    if parts.port:
        host += ":%d" % parts.port
    segments = []
    for segment in parts.path.split("/"):
        ref, at, tail = segment.partition("@")
        if at and SHA.match(tail):  # a git ref such as repo@<sha> is the pin, not a secret
            segments.append(segment if not _token_like(ref) else "<redacted>@" + tail)
        else:
            segments.append("<redacted: %d chars>" % len(segment) if _token_like(segment) and not UUID.match(segment) else segment)
    out = "%s://%s%s%s" % (parts.scheme, "<userinfo>@" if "@" in parts.netloc else "", host, "/".join(segments))
    if parts.query:
        keys = [pair.split("=", 1)[0] for pair in parts.query.split("&") if pair]
        out += "?" + "&".join("%s=<redacted>" % k for k in keys)
    return out


def sanitize_args(args: list) -> list:
    out = []
    previous = ""
    for raw in args:
        if not isinstance(raw, str):
            out.append("<non-string %s>" % type(raw).__name__)
            previous = ""
            continue
        arg = raw
        if REFERENCE.search(arg) and not _token_like(REFERENCE.sub("", arg)):
            shown = arg
        elif previous in SECRET_FLAGS or SECRET_KEY.search(previous.lstrip("-")) and previous.startswith("-"):
            shown = "<redacted: %d chars>" % len(arg)
        elif previous in ENV_FLAGS and "=" in arg:
            shown = arg.split("=", 1)[0] + "=<redacted>"
        elif re.match(r"^[a-z][a-z0-9+.-]*://", arg, re.IGNORECASE) or arg.startswith("git+"):
            prefix = "git+" if arg.startswith("git+") else ""
            shown = prefix + sanitize_url(arg[len(prefix):])
        elif "=" in arg and SECRET_KEY.search(arg.split("=", 1)[0]):
            shown = arg.split("=", 1)[0] + "=<redacted>"
        elif _token_like(arg):
            shown = "<redacted: %d chars>" % len(arg)
        else:
            shown = arg
        out.append(shown)
        previous = arg
    return out


def describe_server(entry: object) -> dict:
    if not isinstance(entry, dict):
        return {"entry_type": type(entry).__name__}
    out: dict = {}
    for key, value in entry.items():
        if key == "type":
            out["type"] = value if isinstance(value, str) and len(value) <= SHORT_STRING else "<%s>" % type(value).__name__
        elif key == "command":
            out["command"] = value if isinstance(value, str) and not _token_like(value) else "<redacted>"
        elif key == "args":
            out["args"] = sanitize_args(value) if isinstance(value, list) else "<%s>" % type(value).__name__
        elif key == "url":
            out["url"] = sanitize_url(value) if isinstance(value, str) else "<%s>" % type(value).__name__
        elif key in ("env", "headers"):
            out[key] = {k: classify_value(v) for k, v in value.items()} if isinstance(value, dict) else "<%s>" % type(value).__name__
        elif key == "cwd" and isinstance(value, str):
            out["cwd"] = value.replace(str(HOME), "~")
        elif key == "envFile" and isinstance(value, str):
            out["envFile"] = value.replace(str(HOME), "~")
        elif key in ("gallery", "version") and isinstance(value, str):  # VS Code's MCP gallery provenance
            out[key] = sanitize_url(value) if "://" in value else (value if len(value) <= SHORT_STRING and not _token_like(value) else "<string, %d chars>" % len(value))
        else:
            out.setdefault("other_keys", {})[key] = type(value).__name__
    if "command" in out and isinstance(out["command"], str):
        out["command"] = out["command"].replace(str(HOME), "~")
    if isinstance(out.get("args"), list):
        out["args"] = [a.replace(str(HOME), "~") for a in out["args"]]
    return out


def describe_inputs(inputs: object) -> list:
    if not isinstance(inputs, list):
        return []
    return [{"id": item.get("id"), "type": item.get("type"), "password": item.get("password", False)} if isinstance(item, dict) else {"entry_type": type(item).__name__} for item in inputs]


def describe_settings(data: dict) -> dict:
    out = {}
    for key in sorted(data):
        if not key.startswith(SETTINGS_PREFIXES):
            continue
        value = data[key]
        if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
            out[key] = value
        elif isinstance(value, str):
            out[key] = value if len(value) <= SHORT_STRING and not _token_like(value) else "<string, %d chars>" % len(value)
        elif isinstance(value, dict):
            out[key] = {k: (v if isinstance(v, bool) else "<%s>" % type(v).__name__) for k, v in value.items()}
        else:
            out[key] = "<%s of %d>" % (type(value).__name__, len(value)) if isinstance(value, list) else "<%s>" % type(value).__name__
    return out


def inventory(mcp_json: Path, settings: Path) -> dict | None:
    h5 = _load_h5()
    data = h5.load_json(mcp_json, jsonc=True)
    if data is None:
        return None
    servers = {}
    for scope, table in h5.server_tables(data):
        for name, entry in table.items():
            servers["%s.%s" % (scope, name)] = describe_server(entry)
    settings_data = h5.load_json(settings, jsonc=True) if settings.exists() else None
    workspace = sorted(str(p.relative_to(JUNIPER)) for p in JUNIPER.glob("*/.vscode/mcp.json")) if JUNIPER.is_dir() else []
    return {
        "mcp_json": str(mcp_json).replace(str(HOME), "~"),
        "top_level_keys": sorted(data),
        "servers": servers,
        "inputs": describe_inputs(data.get("inputs")),
        "settings_file": str(settings).replace(str(HOME), "~"),
        "settings_parsed": settings_data is not None,
        "settings": describe_settings(settings_data or {}),
        "workspace_mcp_json": workspace,
    }


def print_text(result: dict) -> None:
    print("mcp.json  %s  (top-level keys: %s)" % (result["mcp_json"], ", ".join(result["top_level_keys"])))
    for name, entry in result["servers"].items():
        print("\nserver %s" % name)
        for key, value in entry.items():
            if isinstance(value, dict):
                print("  %-10s" % key)
                for k, v in value.items():
                    print("    %-28s %s" % (k, v))
            elif isinstance(value, list):
                print("  %-10s" % key)
                for item in value:
                    print("    %s" % item)
            else:
                print("  %-10s %s" % (key, value))
    print("\ninputs")
    for item in result["inputs"] or ["(none)"]:
        print("  %s" % item)
    print("\nsettings  %s  (parsed: %s)" % (result["settings_file"], result["settings_parsed"]))
    for key, value in result["settings"].items():
        print("  %-44s %s" % (key, json.dumps(value)))
    print("\nworkspace .vscode/mcp.json under ~/Development/python/Juniper: %s" % (", ".join(result["workspace_mcp_json"]) or "none"))


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description="Value-redacted inventory of VS Code's user MCP configuration (turing H6).")
    ap.add_argument("--mcp-json", type=Path, default=CODE_USER / "mcp.json")
    ap.add_argument("--settings", type=Path, default=CODE_USER / "settings.json")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    result = inventory(args.mcp_json, args.settings)
    if result is None:
        print("ERROR: %s is missing or does not parse as JSONC" % args.mcp_json, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
