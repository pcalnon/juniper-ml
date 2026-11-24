#!/usr/bin/env python3
"""
Replay a list of credential-reaching candidate commands through two copies of the agent guard: no denial lost.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py; the final check's candidate list (bypass.json, 378 rows, each a command that
         bash 5.3 resolved to a credential path); util/ad-hoc/2026-11-16_flood4r2_r18-guard_probe.py.

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_candidates.py <candidates.json> <scratch dir> <out.json>
        <before guard.py> <after guard.py>

<candidates.json> is a JSON object with a "rows" list whose items carry a "command", or a plain JSON list of
command strings. Each command goes through each guard's ``run_hook`` in-process (a guard reads text and runs
nothing), with a scratch home under <scratch dir> that holds a dummy ``.ssh``, ``.gnupg`` and ``.claude``. Written:
the decision of each guard for each command (pass, the rule ids denied, or refused), and the counts of every
(before, after) pair. A command the first guard denies and the second does not is a LOST denial.
"""

from __future__ import annotations

import collections
import importlib.util
import json
import re
import sys
from pathlib import Path


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def decision(guard, command: str, home: Path, cwd: Path) -> str:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}).encode("utf-8")
    code, out, err = guard.run_hook(payload, homes=[str(home)], project_dir=str(cwd))
    if code == 0 and out:
        reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
        primary = re.search(r"Rule ([A-Z0-9-]+):", reason)
        also = re.search(r"Also matched: ([A-Z0-9, -]+)\.", reason)
        rules = ([primary.group(1)] if primary else []) + ([r.strip() for r in also.group(1).split(",")] if also else [])
        return "deny " + " ".join(sorted(rules))
    if code == 0:
        return "pass"
    return "refused: " + err.split(": ", 2)[-1][:60]


def main(argv: list) -> int:
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    commands = [row["command"] for row in data["rows"]] if isinstance(data, dict) else list(data)
    scratch = Path(argv[2]).resolve()
    home = scratch / "home"
    cwd = home / "work"
    for name in (".ssh", ".gnupg", ".claude", "work", "X"):
        (home / name).mkdir(parents=True, exist_ok=True)
    before = load(argv[4], "guard_before")
    after = load(argv[5], "guard_after")
    rows = []
    pairs = collections.Counter()
    lost = []
    for command in commands:
        a = decision(before, command, home, cwd)
        b = decision(after, command, home, cwd)
        rows.append({"command": command, "before": a, "after": b})
        pairs["%s -> %s" % (a.split(" ")[0] if a.startswith("deny") else a[:9], b.split(" ")[0] if b.startswith("deny") else b[:9])] += 1
        if a.startswith("deny") and not b.startswith("deny"):
            lost.append(command)
    summary = {"commands": len(commands), "pairs (before -> after)": dict(pairs.most_common()), "lost denials": len(lost), "before passes": sum(r["before"] == "pass" for r in rows), "after passes": sum(r["after"] == "pass" for r in rows), "after refuses": sum(r["after"].startswith("refused") for r in rows)}
    Path(argv[3]).write_text(json.dumps({"summary": summary, "lost": lost, "rows": rows}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
