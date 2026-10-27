#!/usr/bin/env python3
"""
Apply the owner's H6 decisions to VS Code's user MCP configuration (turing bring-up task H6, the audit's §8).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-26
Status: ad-hoc — one-off (H6's application on turing; --check re-runs on any synced host)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md (§8; SER-P1, HF-P1, H6-X3 to H6-X5);
         notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.1, the 2026-10-25 ruling on H6);
         util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py (the independent, value-free verification)

The owner's ruling: the changes cover every synced host, the agent makes them, and mcp.json and settings.json are
backed up first with the token redacted. Settings Sync carries the user mcp.json (H6-X3) and both settings below (each
is window-scoped with no ignoreSync in VS Code 1.108.2), so an edit made here reaches the other hosts once VS Code runs
here with Settings Sync on, and each of them takes it at its own next sync.

  mcp.json       servers["oraios/serena"] removed (SER-P1: unpinned, and Serena's main defaults to an exec-capable REPL);
                 servers["microsoft/markitdown"] removed (MKD-T1);
                 servers["upstash/context7"] kept unchanged (§8.3);
                 servers["huggingface"]: its literal headers removed, so it runs token-less (HF-P1, §8.4). --hf
                   password-input references a read-only token through a password input instead; --hf remove drops it;
                 inputs: every input no remaining server references is deleted (H6-X5: 20 of the 21 on turing).
  settings.json  "chat.mcp.autostart": "never" and "chat.mcp.gallery.enabled": false (H6-X4).

Nothing prints a value: servers, headers, inputs and settings are named by key, and the token is counted, never shown.
The backup goes to <quarantine-root>/<date>-vscode-mcp/ (mode 0700, files 0600), with every copy of a literal header
value and every hf_-shaped token replaced by a marker. The backup is re-read, and the run stops before editing if a copy
survived. A file is rewritten only when a JSON round trip reproduces it (so no comment or layout is lost), and only
while VS Code is not running.

    python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py [--apply | --check] [--hf MODE]
        [--code-user-dir DIR] [--quarantine-root DIR] [--date YYYY-MM-DD]
    python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py --self-test

The default is a dry run. Exit 0 = applied, nothing to do, or (--check) every decision holds; 1 = (--check) a decision
does not hold, a pre-flight refused, or (--self-test) a case failed; 2 = a file is missing or does not parse.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import os
import platform
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
USER_DIRS = {
    "Darwin": HOME / "Library" / "Application Support" / "Code" / "User",
    "Linux": HOME / ".config" / "Code" / "User",
}
QUARANTINE_ROOT = HOME / ".local" / "state" / "juniper" / "quarantine"
RUNNING = {  # pgrep arguments that find a running VS Code
    "Darwin": ["-f", "Visual Studio Code.app/Contents/"],
    "Linux": ["-f", "/usr/share/code/"],
}

REMOVED = ("oraios/serena", "microsoft/markitdown")  # SER-P1, MKD-T1
KEPT = "upstash/context7"  # §8.3
HF = "huggingface"  # HF-P1, §8.4
HF_MODES = ("token-less", "password-input", "remove")
HF_INPUT = json.loads('{"id": "hf_token", "type": "promptString", "description": "Hugging Face read-only token", "password": true}')
HF_HEADER = ("Authorization", "Bearer ${input:hf_token}")
SETTINGS = (("chat.mcp.autostart", "never"), ("chat.mcp.gallery.enabled", False))  # H6-X4

REFERENCE = re.compile(r"\$\{(?:input|env):[^}]*\}")
INPUT_REFERENCE = re.compile(r"\$\{input:([^}]+)\}")
SCHEME_WORD = re.compile(r"^(?:Bearer|Basic|Token)?$", re.IGNORECASE)
HF_SHAPED = re.compile(r"(?<![A-Za-z0-9])hf_[A-Za-z0-9]{20,}")
MARKER = "<redacted: H6 apply, HF-P1>"


class Refused(Exception):
    """A pre-flight or post-write check refused; the message names the condition, never a value."""


# ------------------------------------------------------------------------------------------------ reading


def scan_jsonc(text: str) -> tuple[str, int]:
    """The text with trailing commas dropped, and the number of comments; both judged outside strings."""
    out, comments, i, n, in_string = [], 0, 0, len(text), False
    while i < n:
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            in_string = c != '"'
            i += 1
            continue
        if c == '"':
            in_string = True
        elif text.startswith("//", i) or text.startswith("/*", i):
            comments += 1
            end = text.find("\n" if text[i + 1] == "/" else "*/", i + 2)
            i = n if end < 0 else end + (0 if text[i + 1] == "/" else 2)
            continue
        elif c == ",":
            j = i + 1
            while j < n and text[j] in " \t\r\n":
                j += 1
            if j < n and text[j] in "}]":
                i += 1
                continue
        out.append(c)
        i += 1
    return "".join(out), comments


class JsonFile:
    """One VS Code JSON(C) file: its parsed data and the layout a rewrite must reproduce."""

    def __init__(self, path: Path):
        self.path = path
        self.raw = path.read_text(encoding="utf-8")
        stripped, self.comments = scan_jsonc(self.raw)
        self.data = json.loads(stripped)
        first = next((m.group(0) for m in re.finditer(r"(?m)^[ \t]+(?=\S)", self.raw)), "    ")
        self.indent = "\t" if first.startswith("\t") else len(first)
        self.newline = self.raw.endswith("\n")
        self.faithful = self.comments == 0 and "\r" not in self.raw and self.dump(self.data) == stripped

    def dump(self, data: object) -> str:
        return json.dumps(data, indent=self.indent, ensure_ascii=False) + ("\n" if self.newline else "")


def literal_values(servers: dict) -> list[str]:
    """Every env or header value of every server that is not a bare reference (the values a backup must not hold)."""
    found = []
    for entry in servers.values():
        for block in ("env", "headers"):
            table = entry.get(block) if isinstance(entry, dict) else None
            for value in (table or {}).values() if isinstance(table, dict) else ():
                if isinstance(value, str) and value and not is_reference(value):
                    found.append(value)
    return found


def is_reference(value: str) -> bool:
    return bool(REFERENCE.search(value)) and bool(SCHEME_WORD.match(REFERENCE.sub("", value).strip()))


# ------------------------------------------------------------------------------------------------ the decisions


def decide_mcp(data: dict, hf_mode: str) -> tuple[dict, list[str]]:
    """The edited mcp.json and the actions taken, by key path only."""
    data = copy.deepcopy(data)
    actions: list[str] = []
    servers = data.get("servers")
    if not isinstance(servers, dict):
        raise Refused("mcp.json has no servers table")
    for name in REMOVED:
        if name in servers:
            del servers[name]
            actions.append("servers[%s] removed" % name)
    entry = servers.get(HF)
    if isinstance(entry, dict) and hf_mode == "remove":
        del servers[HF]
        actions.append("servers[%s] removed (--hf remove)" % HF)
    elif isinstance(entry, dict):
        headers = entry.get("headers") if isinstance(entry.get("headers"), dict) else {}
        for name in [k for k, v in headers.items() if not (isinstance(v, str) and is_reference(v))]:
            del headers[name]
            actions.append("servers[%s].headers[%s] removed (a literal)" % (HF, name))
        if hf_mode == "password-input" and headers.get(HF_HEADER[0]) != HF_HEADER[1]:
            headers[HF_HEADER[0]] = HF_HEADER[1]
            actions.append("servers[%s].headers[%s] references ${input:%s}" % (HF, HF_HEADER[0], HF_INPUT["id"]))
        if headers:
            entry["headers"] = headers
        elif "headers" in entry:
            del entry["headers"]
            actions.append("servers[%s].headers removed (empty: token-less)" % HF)
        if hf_mode == "password-input":
            inputs = data.setdefault("inputs", [])
            if not any(isinstance(i, dict) and i.get("id") == HF_INPUT["id"] for i in inputs):
                inputs.append(dict(HF_INPUT))
                actions.append("inputs[%s] added (a password input)" % HF_INPUT["id"])
    referenced = set(INPUT_REFERENCE.findall(json.dumps(servers)))
    inputs = data.get("inputs")
    if isinstance(inputs, list):
        kept = [i for i in inputs if isinstance(i, dict) and i.get("id") in referenced]
        dropped = [str(i.get("id")) if isinstance(i, dict) else "<%s>" % type(i).__name__ for i in inputs if i not in kept]
        if dropped:
            data["inputs"] = kept
            actions.append("inputs: %d deleted, unreferenced (%s); kept %d (%s)" % (len(dropped), ", ".join(dropped), len(kept), ", ".join(str(i.get("id")) for i in kept) or "none"))
    return data, actions


def decide_settings(data: dict) -> tuple[dict, list[str]]:
    """The edited settings.json: each new key goes next to an existing chat.mcp. key, or at the end."""
    actions: list[str] = []
    out = dict(data)
    for key, value in SETTINGS:
        if key in out and json.dumps(out[key]) == json.dumps(value):
            continue
        if key in out:
            out[key] = value
            actions.append("settings[%s] set to %s" % (key, json.dumps(value)))
            continue
        anchor = next((k for k in out if k.startswith("chat.mcp.")), None)
        rebuilt: dict = {}
        for k, v in out.items():
            if k == anchor:
                rebuilt[key] = value
            rebuilt[k] = v
        if anchor is None:
            rebuilt[key] = value
        out = rebuilt
        actions.append("settings[%s] added as %s" % (key, json.dumps(value)))
    return out, actions


def check(mcp: dict, settings: dict, hf_mode: str) -> list[tuple[str, bool]]:
    """Each decision as (label, holds)."""
    servers = mcp.get("servers") if isinstance(mcp.get("servers"), dict) else {}
    inputs = mcp.get("inputs") if isinstance(mcp.get("inputs"), list) else []
    referenced = set(INPUT_REFERENCE.findall(json.dumps(servers)))
    ids = [i.get("id") for i in inputs if isinstance(i, dict)]
    rows = [("servers[%s] absent" % name, name not in servers) for name in REMOVED]
    rows.append(("servers[%s] present" % KEPT, KEPT in servers))
    if hf_mode == "remove":
        rows.append(("servers[%s] absent" % HF, HF not in servers))
    if hf_mode == "password-input":
        masked = [i for i in inputs if isinstance(i, dict) and i.get("id") == HF_INPUT["id"] and i.get("password") is True]
        rows.append(("inputs[%s] present and masked" % HF_INPUT["id"], len(masked) == 1))
    rows.append(("no env or header value of any server is a literal", not literal_values(servers)))
    rows.append(("no hf_-shaped token anywhere in mcp.json", not HF_SHAPED.search(json.dumps(mcp))))
    rows.append(("every input is referenced by a server (%d inputs)" % len(ids), len(ids) == len(inputs) and set(ids) <= referenced))
    for key, value in SETTINGS:
        rows.append(("settings[%s] is %s" % (key, json.dumps(value)), json.dumps(settings.get(key)) == json.dumps(value)))
    return rows


# ------------------------------------------------------------------------------------------------ writing


def redact(text: str, values: list[str]) -> tuple[str, int]:
    count = 0
    for value in sorted(set(values), key=len, reverse=True):
        for form in {value, json.dumps(value, ensure_ascii=False)[1:-1]}:
            count += text.count(form)
            text = text.replace(form, MARKER)
    text, more = HF_SHAPED.subn(MARKER, text)
    return text, count + more


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_private(path: Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def backup(files: dict[str, JsonFile], values: list[str], root: Path, date: str, actions: list[str]) -> Path:
    """Redacted copies of both files in a fresh quarantine directory; refuses if any copy of a value survives."""
    root.parent.mkdir(parents=True, exist_ok=True)
    if not root.exists():
        os.mkdir(root, 0o700)
    target = root / ("%s-vscode-mcp" % date)
    if target.exists():
        target = root / ("%s-vscode-mcp-%s" % (date, datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%SZ")))
    os.mkdir(target, 0o700)
    manifest: dict = {
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py",
        "host": platform.node(),
        "marker": MARKER,
        "actions": actions,
        "files": {},
    }
    for name, jf in files.items():
        text, count = redact(jf.raw, values)
        write_private(target / name, text)
        written = (target / name).read_text(encoding="utf-8")
        if any(v in written for v in values) or HF_SHAPED.search(written):
            (target / name).unlink()
            raise Refused("the backup of %s still held a redacted value; it was deleted and nothing was edited" % name)
        stat = jf.path.stat()
        manifest["files"][name] = {
            "source": str(jf.path).replace(str(HOME), "~"),
            "size": stat.st_size,
            "mtime_utc": datetime.datetime.fromtimestamp(stat.st_mtime, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sha256_source": sha256(jf.raw.encode("utf-8")),
            "sha256_backup": sha256(written.encode("utf-8")),
            "redactions": count,
        }
    write_private(target / "MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    return target


def replace_file(jf: JsonFile, data: dict) -> None:
    tmp = jf.path.with_name(".%s.h6-tmp" % jf.path.name)
    tmp.write_text(jf.dump(data), encoding="utf-8")
    shutil.copymode(jf.path, tmp)
    os.replace(tmp, jf.path)


def vscode_running() -> bool | None:
    args = RUNNING.get(platform.system())
    if args is None or shutil.which("pgrep") is None:
        return None
    return subprocess.run(["pgrep", *args], capture_output=True, check=False).returncode == 0


def residual_copies(user_dir: Path, values: list[str]) -> list[str]:
    """VS Code's own copies of mcp.json that still hold a literal value: sync state, its backups, local history."""
    if not values:
        return []
    candidates = sorted((user_dir / "sync" / "mcp").glob("*.json"))
    for entries in sorted((user_dir / "History").glob("*/entries.json")):
        try:
            resource = json.loads(entries.read_text(encoding="utf-8")).get("resource", "")
        except (OSError, ValueError):
            continue
        if resource.endswith("/User/mcp.json"):
            candidates += sorted(p for p in entries.parent.iterdir() if p.name != "entries.json")
    found = []
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(v in text or json.dumps(v)[1:-1] in text for v in values):
            found.append(str(path.relative_to(user_dir)))
    return found


# ------------------------------------------------------------------------------------------------ the run


def run(user_dir: Path, mode: str, hf_mode: str, quarantine: Path, date: str, skip_running_check: bool = False) -> int:
    files = {}
    for name in ("mcp.json", "settings.json"):
        try:
            files[name] = JsonFile(user_dir / name)
        except (OSError, ValueError) as exc:  # the type only: a parse error's message can quote the file
            print("ERROR: %s/%s: %s" % (str(user_dir).replace(str(HOME), "~"), name, type(exc).__name__), file=sys.stderr)
            return 2
    mcp, settings = files["mcp.json"], files["settings.json"]
    if mode == "check":
        rows = check(mcp.data, settings.data, hf_mode)
        for label, holds in rows:
            print("  %-4s %s" % ("PASS" if holds else "FAIL", label))
        print("check: %d of %d hold (%s)" % (sum(h for _, h in rows), len(rows), str(user_dir).replace(str(HOME), "~")))
        return 0 if all(h for _, h in rows) else 1
    try:
        new_mcp, mcp_actions = decide_mcp(mcp.data, hf_mode)
    except Refused as exc:
        print("REFUSED: %s" % exc, file=sys.stderr)
        return 1
    new_settings, settings_actions = decide_settings(settings.data)
    actions = ["mcp.json: " + a for a in mcp_actions] + ["settings.json: " + a for a in settings_actions]
    values = literal_values(mcp.data.get("servers", {}))
    residual = residual_copies(user_dir, values)
    print("%s  %s  (hf mode: %s)" % ("APPLY" if mode == "apply" else "DRY RUN", str(user_dir).replace(str(HOME), "~"), hf_mode))
    for action in actions or ["nothing to do: every decision already holds"]:
        print("  " + action)
    print("  literal env/header values in mcp.json now: %d (redacted from the backup, never printed)" % len(values))
    if residual:
        print("  VS Code's own copies still holding one (not touched; inert once the token is rotated): %d" % len(residual))
        for rel in residual:
            print("    " + rel)
    if not actions:
        return 0
    refusals = [name for name, jf in files.items() if not jf.faithful]
    if refusals:
        print("REFUSED: a rewrite would change more than the decisions in %s (comments, CRLF or layout)" % ", ".join(refusals), file=sys.stderr)
        return 1
    if mode != "apply":
        print("  backup would go to %s/%s-vscode-mcp/ (redacted); re-run with --apply" % (str(quarantine).replace(str(HOME), "~"), date))
        return 0
    if not skip_running_check:
        state = vscode_running()
        if state is not False:
            print("REFUSED: VS Code is %s; quit it first" % ("running" if state else "in an unknown state (no pgrep)"), file=sys.stderr)
            return 1
    try:
        target = backup(files, values, quarantine, date, actions)
    except Refused as exc:
        print("REFUSED: %s" % exc, file=sys.stderr)
        return 1
    print("  backup: %s (MANIFEST.json, mcp.json, settings.json; mode 0700/0600)" % str(target).replace(str(HOME), "~"))
    if mcp_actions:
        replace_file(mcp, new_mcp)
    if settings_actions:
        replace_file(settings, new_settings)
    return run(user_dir, "check", hf_mode, quarantine, date)


# ------------------------------------------------------------------------------------------------ self-test


def _fixture(root: Path, fake: str, comment: bool = False) -> Path:
    user = root / "User"
    user.mkdir(parents=True)
    servers = {
        "microsoft/markitdown": {"type": "stdio", "command": "uvx", "args": ["markitdown-mcp==0.0.1a4"], "gallery": "https://api.mcp.github.com/x", "version": "1.0.0"},
        "upstash/context7": {"type": "http", "url": "https://mcp.context7.com/mcp", "headers": {"CONTEXT7_API_KEY": "${input:context7_api_key}"}, "version": "1.0.0"},
        "oraios/serena": {"type": "stdio", "command": "uvx", "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"]},
        "huggingface": {"url": "https://huggingface.co/mcp", "headers": {"Authorization": "Bearer " + fake}, "type": "http"},
    }
    inputs = [{"id": "context7_api_key", "type": "promptString", "description": "Context7", "password": True}]
    inputs += [{"id": "unused%d" % n, "type": "promptString", "description": "unused"} for n in range(20)]
    text = json.dumps({"inputs": inputs, "servers": servers}, indent="\t")
    text = text[:-2] + ",\n}"  # a trailing comma, as turing's mcp.json has
    if comment:
        text = "// a comment\n" + text
    (user / "mcp.json").write_text(text, encoding="utf-8")
    settings = {"editor.fontSize": 13, "chat.mcp.gallery.enabled": True, "files.trimFinalNewlines": True}
    (user / "settings.json").write_text(json.dumps(settings, indent=4), encoding="utf-8")
    hist = user / "History" / "abc"
    hist.mkdir(parents=True)
    (hist / "entries.json").write_text(json.dumps({"resource": "file://" + str(user / "mcp.json")}), encoding="utf-8")
    (hist / "x1.json").write_text(text, encoding="utf-8")
    return user


def self_test() -> int:
    results: list[tuple[str, bool]] = []
    fake = "hf_" + secrets.token_hex(17)
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        user, quarantine = _fixture(base / "a", fake), base / "q" / "quarantine"
        before = json.loads(scan_jsonc((user / "mcp.json").read_text())[0])
        results.append(("dry run exits 0 and edits nothing", run(user, "dry-run", "token-less", quarantine, "2026-10-26") == 0 and json.loads(scan_jsonc((user / "mcp.json").read_text())[0]) == before))
        results.append(("check fails before the apply", run(user, "check", "token-less", quarantine, "2026-10-26") == 1))
        results.append(("apply exits 0 (its own check holds)", run(user, "apply", "token-less", quarantine, "2026-10-26", skip_running_check=True) == 0))
        after = json.loads((user / "mcp.json").read_text())
        backups = sorted(quarantine.glob("*-vscode-mcp*"))
        results.append(("the token is in neither the file nor the backup", fake not in (user / "mcp.json").read_text() and len(backups) == 1 and all(fake not in p.read_text() for p in backups[0].iterdir())))
        results.append(("the backup is private (0700 / 0600)", len(backups) == 1 and (backups[0].stat().st_mode & 0o777) == 0o700 and all((p.stat().st_mode & 0o777) == 0o600 for p in backups[0].iterdir())))
        results.append(("context7's entry is unchanged", after["servers"].get(KEPT) == before["servers"][KEPT]))
        results.append(("20 inputs deleted, context7_api_key kept", [i["id"] for i in after["inputs"]] == ["context7_api_key"]))
        results.append(("huggingface kept, token-less", after["servers"].get(HF) == {"url": "https://huggingface.co/mcp", "type": "http"}))
        s = json.loads((user / "settings.json").read_text())
        results.append(("settings: both keys, others kept in order", list(s) == ["editor.fontSize", "chat.mcp.autostart", "chat.mcp.gallery.enabled", "files.trimFinalNewlines"] and s["chat.mcp.autostart"] == "never" and s["chat.mcp.gallery.enabled"] is False))
        results.append(("layout kept: tabs in mcp.json, 4 spaces in settings.json", "\n\t\"" in (user / "mcp.json").read_text() and "\n    \"" in (user / "settings.json").read_text()))
        results.append(("a re-run has nothing to do and makes no second backup", run(user, "apply", "token-less", quarantine, "2026-10-26", skip_running_check=True) == 0 and len(sorted(quarantine.glob("*-vscode-mcp*"))) == 1))
        results.append(("residual copies are found by path (history)", residual_copies(_fixture(base / "r", fake), [ "Bearer " + fake]) == ["History/abc/x1.json"]))
        user_c = _fixture(base / "c", fake, comment=True)
        results.append(("a file with comments is refused", run(user_c, "apply", "token-less", base / "qc", "2026-10-26", skip_running_check=True) == 1 and not (base / "qc").exists()))
        user_p = _fixture(base / "p", fake)
        ok = run(user_p, "apply", "password-input", base / "qp", "2026-10-26", skip_running_check=True) == 0
        p = json.loads((user_p / "mcp.json").read_text())
        results.append(("password-input: header references hf_token, input masked", ok and p["servers"][HF]["headers"] == {HF_HEADER[0]: HF_HEADER[1]} and [i["id"] for i in p["inputs"]] == ["context7_api_key", "hf_token"]))
        user_r = _fixture(base / "x", fake)
        ok = run(user_r, "apply", "remove", base / "qr", "2026-10-26", skip_running_check=True) == 0
        results.append(("remove: huggingface gone", ok and HF not in json.loads((user_r / "mcp.json").read_text())["servers"]))
    for label, holds in results:
        print("  %-4s %s" % ("PASS" if holds else "FAIL", label))
    print("self-test: %d of %d passed" % (sum(h for _, h in results), len(results)))
    return 0 if all(h for _, h in results) else 1


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description="Apply the owner's H6 decisions to VS Code's user MCP configuration.")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="back up (redacted), then edit both files")
    group.add_argument("--check", action="store_true", help="verify every decision; exit 1 if one does not hold")
    group.add_argument("--self-test", action="store_true", help="run every path against synthetic fixtures")
    ap.add_argument("--hf", choices=HF_MODES, default="token-less", help="the Hugging Face entry (default: token-less, §8.4)")
    ap.add_argument("--code-user-dir", type=Path, default=USER_DIRS.get(platform.system(), USER_DIRS["Linux"]))
    ap.add_argument("--quarantine-root", type=Path, default=QUARANTINE_ROOT)
    ap.add_argument("--date", default=datetime.date.today().isoformat(), help="the backup directory's date (default: today, local)")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    mode = "apply" if args.apply else "check" if args.check else "dry-run"
    return run(args.code_user_dir, mode, args.hf, args.quarantine_root, args.date)


if __name__ == "__main__":
    sys.exit(main())
