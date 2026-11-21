#!/usr/bin/env python3
"""
Run the agent guard on the GnuPG and brace-cap commands the ml-docs carrier's pages name, and record each answer
(exit code, the rule ids in a deny, the reason's wording), independently of the builder's probe.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (Cursor flood-4 session 8: the ml-docs carrier's claims-lens validation, check C)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/claude_agent_guard.py (1.3.0); docs/REFERENCE.md § GnuPG long-option abbreviations

The guard reads a PreToolUse payload on stdin. It runs with HOME set to an empty directory under --work, so no
real credential path is ever read; the commands are only evaluated, never executed.

Usage:
  2026-11-14_flood4r2_val_ml-docs_guard_probe.py --repo <juniper-ml checkout> --work <dir> --out <report.json>
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

RULE_RE = re.compile(r"\b(GPG-SECRET|GPG-SIGN|CRED-PATH-BASH|[A-Z]+(?:-[A-Z]+)+)\b")


def cases() -> list[str]:
    alts64 = ",".join(f"a{i}" for i in range(1, 64)) + ",ssh"
    alts65 = ",".join(f"a{i}" for i in range(1, 65)) + ",ssh"
    gpg = ["--export", "--EXPORT", "--export=KEYID", "--ex", "--expo", "--expo=KEYID", "--expor", "--li", "--list", "--LIST", "--list=keys",
           "--list-keys", "--list-key", "--list-secret", "--ca", "--card", "--cl", "--cle", "--clea", "--ls", "--lsi", "--si", "--sign", "--SIGN",
           "--de", "--det", "--decr", "--pa", "--qu", "--e", "--s", "--c", "--d", "--l", "-K", "-k", "-s", "-b", "-d"]
    out = [f"gpg {flag}" for flag in gpg]
    out += ["gpg2 --list", "GPG --list", "gpg --list --sign x", "bash -c 'gpg --expo'", "echo $(gpg --expo)"]
    out += [f"cat ~/.{{{alts64}}}/config", f"cat ~/.{{{alts65}}}/config", "echo {1..64}", "echo {1..65}", "for i in {1..100}; do echo $i; done", "for i in $(seq 1 100); do echo $i; done"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    home = Path(args.work) / "home"
    home.mkdir(parents=True, exist_ok=True)
    guard = Path(args.repo) / "util" / "claude_agent_guard.py"
    env = {**os.environ, "HOME": str(home)}
    rows = []
    for command in cases():
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(home)})
        done = subprocess.run([sys.executable, str(guard)], input=payload, capture_output=True, text=True, env=env, check=False)
        decision = None
        reason = ""
        if done.stdout.strip():
            try:
                body = json.loads(done.stdout)
                hso = body.get("hookSpecificOutput", {})
                decision = hso.get("permissionDecision") or body.get("decision")
                reason = hso.get("permissionDecisionReason") or body.get("reason") or ""
            except json.JSONDecodeError:
                reason = "non-JSON stdout"
        rules = sorted(set(RULE_RE.findall(reason)))
        rows.append({"command": command if len(command) < 80 else command[:40] + "..." + command[-30:], "exit": done.returncode, "decision": decision,
                     "rules": rules, "also_matched": "Also matched" in reason, "stdout_objects": done.stdout.count('"hookSpecificOutput"'),
                     "reason_head": reason[:400], "stderr_head": done.stderr.strip()[:200]})
    Path(args.out).write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(row["exit"], row["decision"], row["rules"], "ALSO" if row["also_matched"] else "", row["command"], "|", row["stderr_head"][:90])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
