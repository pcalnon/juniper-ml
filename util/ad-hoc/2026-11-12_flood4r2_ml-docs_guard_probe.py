#!/usr/bin/env python3
"""
Probe ``util/claude_agent_guard.py`` on the GnuPG long-option rows and the brace-cap rows the carried docs state.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- investigation (claim evidence for the Cursor flood-4 round-2 docs carrier: drafts juniper-ml#2490
        and juniper-ml#2470, both written for the guard before 1.3.0)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, rulings 8 and 3);
         tests/test_claude_agent_guard.py (``GuardTestCase.run_guard``, whose invocation this copies)

Each command is sent to the guard as a PreToolUse ``Bash`` payload on stdin (``python -I util/claude_agent_guard.py``),
with ``JUNIPER_GUARD_HOME`` and ``HOME`` pointing at a temporary home that has its own ``.ssh``, ``.gnupg`` and
``.claude``. The guard only reads the command text: NOTHING here runs gpg, git or any of the commands named. The
report records, per command, the exit status, the rule the deny names (and any "Also matched"), and the refusal
text of an exit 2. Every row carries the outcome the documents state for it; the exit status is 1 when one
differs, so a row the guard contradicts cannot be carried by accident.

Brace-cap rows are built from words that do not contain the credential directory's name, so a deny can only come
from an expanded alternative. No row is one of the open spellings the guard's docstring lists under gap 12.

Usage: 2026-11-12_flood4r2_ml-docs_guard_probe.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GUARD = REPO / "util" / "claude_agent_guard.py"
ALLOWED = "allowed"
SECRET = "GPG-SECRET"
SIGN = "GPG-SIGN"
CRED = "CRED-PATH-BASH"
REFUSED = "refused (exit 2)"
CAP_TEXT = "a brace expansion of more than 64 alternatives (MAX_BRACE_ALTERNATIVES) cannot be analysed"


def assembled(count: int) -> str:
    """A brace list of ``count`` alternatives whose LAST one, with the suffix, spells the SSH directory's name."""
    return "{" + ",".join(["n%d" % index for index in range(count - 1)] + [".ss"]) + "}h"


GPG_ROWS = [
    # exact ``export`` is allowed, in any case and with a value
    ("gpg --export", ALLOWED), ("gpg --EXPORT", ALLOWED), ("gpg --export=KEYID", ALLOWED), ("gpg --export --armor KEYID", ALLOWED),
    # every shorter prefix of two letters or more is a prefix of export-secret-keys
    ("gpg --ex", SECRET), ("gpg --exp", SECRET), ("gpg --expo", SECRET), ("gpg --expo=KEYID", SECRET), ("gpg --expor", SECRET), ("gpg --export-secret", SECRET),
    ("gpg --li", SECRET), ("gpg --list", SECRET), ("gpg --LIST", SECRET), ("gpg --list=keys", SECRET), ("gpg --list-secret", SECRET), ("gpg --list-secret-keys", SECRET),
    ("gpg --ca", SECRET), ("gpg --card", SECRET), ("gpg --card-status", SECRET), ("gpg --ed", SECRET), ("gpg2 --list", SECRET), ("GPG --list", SECRET),
    ("gpg --cl", SIGN), ("gpg --cle", SIGN), ("gpg --clea", SIGN), ("gpg --clearsign", SIGN), ("gpg --ls", SIGN), ("gpg --lsi", SIGN),
    ("gpg --si", SIGN), ("gpg --sign", SIGN), ("gpg --SIGN", SIGN), ("gpg --de", SIGN), ("gpg --det", SIGN), ("gpg --decr", SIGN), ("gpg --detach", SIGN),
    ("gpg --pa", SIGN), ("gpg --pass", SIGN), ("gpg --qu", SIGN), ("gpg --quick", SIGN), ("gpg --ch", SIGN),
    # one letter is below the floor
    ("gpg --e", ALLOWED), ("gpg --s", ALLOWED), ("gpg --c", ALLOWED), ("gpg --d x", ALLOWED), ("gpg --l", ALLOWED),
    # a longer word that no denied option starts with
    ("gpg --list-keys", ALLOWED), ("gpg --list-key", ALLOWED), ("gpg --verify x.sig x", ALLOWED), ("gpg --fingerprint KEYID", ALLOWED), ("gpg --version", ALLOWED),
    # short options are their own table, with no floor
    ("gpg -K", SECRET), ("gpg -k", ALLOWED), ("gpg -s x", SIGN), ("gpg -b x", SIGN), ("gpg -d x", SIGN),
    # nested command text is read too
    ("bash -c 'gpg --expo'", SECRET), ("echo $(gpg --expo)", SECRET),
]
BRACE_ROWS = [
    ("echo " + assembled(64), CRED),
    ("echo " + assembled(65), REFUSED),
    ("echo {1..64}", ALLOWED),
    ("echo {1..65}", REFUSED),
    ("for i in {1..100}; do echo $i; done", REFUSED),
    ("for i in $(seq 1 100); do echo $i; done", ALLOWED),
    ("echo {a,b}{c,d}", ALLOWED),
    ("echo {1..8}{1..8}", ALLOWED),
    ("echo {1..8}{1..9}", REFUSED),
    ("echo {x}y", ALLOWED),
]


def run_guard(command: str, home: Path, cwd: Path) -> dict:
    payload = {"session_id": "probe", "transcript_path": os.devnull, "hook_event_name": "PreToolUse", "cwd": str(cwd), "tool_name": "Bash", "tool_input": {"command": command}}
    env = dict(os.environ)
    env["JUNIPER_GUARD_HOME"] = str(home)
    env["HOME"] = str(home)
    env.pop("CLAUDE_PROJECT_DIR", None)
    proc = subprocess.run([sys.executable, "-I", str(GUARD)], input=json.dumps(payload).encode("utf-8"), capture_output=True, env=env, cwd=str(cwd), timeout=60, check=False)
    stdout = proc.stdout.decode("utf-8")
    stderr = proc.stderr.decode("utf-8")
    rules: list = []
    reason = ""
    if stdout.strip():
        reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        rules = re.findall(r"Rule ([A-Z-]+):", reason)[:1] + [rule for chunk in re.findall(r"Also matched: ([A-Z, -]+)\.", reason) for rule in chunk.split(", ")]
    if proc.returncode == 2:
        outcome = REFUSED
    elif rules:
        outcome = rules[0]
    else:
        outcome = ALLOWED
    return {"command": command if len(command) < 200 else command[:90] + " ... " + command[-60:], "exit": proc.returncode, "outcome": outcome, "rules": rules, "stdout_json_objects": len(stdout.strip().splitlines()), "stderr": stderr.strip()[:260], "reason": reason}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Probe the agent guard on the GnuPG and brace-cap rows the docs state.")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    version = subprocess.run([sys.executable, "-I", str(GUARD), "--version"], capture_output=True, text=True, check=False).stdout.strip()
    rows = []
    with tempfile.TemporaryDirectory(prefix="flood4r2-guard-") as temp_dir:
        root = Path(temp_dir).resolve()
        home = root / "home"
        repo = home / "Development" / "repo"
        for directory in (home / ".ssh", home / ".gnupg", home / ".claude" / "hooks", repo):
            directory.mkdir(parents=True)
        for command, expected in GPG_ROWS + BRACE_ROWS:
            row = run_guard(command, home, repo)
            row["expected"] = expected
            row["ok"] = row["outcome"] == expected
            if expected == REFUSED:
                row["ok"] = row["ok"] and CAP_TEXT in row["stderr"]
            if expected == ALLOWED:
                row["ok"] = row["ok"] and row["stdout_json_objects"] == 0 and row["stderr"] == ""
            rows.append(row)
        both = run_guard("gpg --list --sign x", home, repo)
        both["expected"] = "GPG-SECRET, then Also matched: GPG-SIGN"
        both["ok"] = both["rules"] == [SECRET, SIGN] and both["exit"] == 0 and both["stdout_json_objects"] == 1
        rows.append(both)
        sample = run_guard("gpg --list", home, repo)
    wording = {
        "deny_is_one_json_object_and_exit_0": sample["exit"] == 0 and sample["stdout_json_objects"] == 1,
        "reason_says_owner_run_under_D11": "OWNER-run under D11" in sample["reason"],
        "reason_says_do_not_retry_or_look_for_a_way_around": "do not retry it or look for a way around the guard" in sample["reason"],
        "sample_reason": sample["reason"],
    }
    failed = [row["command"] for row in rows if not row["ok"]] + [key for key, value in wording.items() if value is False]
    report = {"guard": str(GUARD), "guard_version": version, "rows": len(rows), "failed": failed, "wording": wording, "results": [{key: value for key, value in row.items() if key != "reason"} for row in rows]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"{version}: {len(rows)} rows, {len(failed)} differ from the documented outcome")
    for row in rows:
        marker = "ok   " if row["ok"] else "DIFF "
        print(f"{marker}{row['outcome']:<18} exit {row['exit']}  {row['command']}" + ("" if row["ok"] else f"   (documented: {row['expected']}; stderr: {row['stderr'][:160]})"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
