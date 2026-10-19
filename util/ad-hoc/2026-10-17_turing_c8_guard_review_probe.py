"""
Black-box review of util/claude_agent_guard.py: the lead's own allow/deny cases, independent of the agent-written suite.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: ad-hoc — investigation (review of the C8 / D11 item 4 guard before it lands)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py; tests/test_claude_agent_guard.py;
         notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (D11 item 4, task C8, H3)

Two lists. ALLOW holds the commands that this work arc's own landing and verification flow runs, which the guard must
not break. DENY holds the D11 forbidden actions, including evasions the suite might not have tried. Each case is a
PreToolUse payload piped to the guard with JUNIPER_GUARD_HOME pointing at a temp home, so nothing real is consulted.
Prints one line per case and exits 1 if any case comes out wrong.

Usage:
    python3 util/ad-hoc/2026-10-17_turing_c8_guard_review_probe.py [--guard util/claude_agent_guard.py]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

ALLOW_BASH = [
    "git status --short --branch",
    "git fetch origin",
    "git checkout -q -B land/x origin/main",
    "git log -1 --format=%G?",
    "git config --show-origin --get-all commit.gpgsign",
    "python3 util/open_signed_pr.py --repo juniper-ml --branch feat/x --add a:a --message m --title t --body-file b.md",
    "python3 util/push_signed_commit.py --repo juniper-ml --branch feat/x --expected-head abc --add a:a --message m",
    "python3 util/ad-hoc/2026-10-17_push_signed_with_retry.py --repo juniper-ml --branch feat/x --file a:a --message m",
    "python3 util/safe_merge.py --pr 12 --execute",
    "python3 util/wait_for_checks.py --pr 12",
    "gh pr view 12 --json state,mergeStateStatus",
    "gh pr checks 12",
    "gh api repos/pcalnon/juniper-ml/git/ref/heads/feat/x --jq .object.sha",
    'gh api "repos/pcalnon/juniper-ml/compare/main...feat/x" --jq .ahead_by',
    "gh search prs --owner pcalnon --state open --json repository,number,title",
    "ssh -G github_juniper-ml",
    "python3 util/git_remote_alias_check.py",
    "bash util/headless_signing_preflight.bash",
    "gpgconf --list-options gpg-agent",
    "gpg --list-keys",
    "SKIP=gitleaks pre-commit run --files util/x.bash",
    "python3 -m unittest -v tests/test_claude_agent_guard.py",
    "networksetup -getairportpower en0",
    "system_profiler SPAirPortDataType",
    "ping -c 5 192.168.50.1",
    "printenv GIT_CONFIG_COUNT",
    "cat docs/REFERENCE.md | head",
    "defaults read com.apple.dock",
]

DENY_BASH = [
    "cat ~/.ssh/config",
    "cat $HOME/.ssh/id_ed25519_github_juniper-ml",
    'cat "${HOME}"/.gnupg/gpg-agent.conf',
    "less /Users/someone/.ssh/config",
    "cd ~ && cat .ssh/config",
    "bash -c 'cat ~/.ssh/config'",
    "echo $(cat ~/.gnupg/sshcontrol)",
    "gh api -X POST repos/o/r/issues -f title=x",
    "gh api -XPOST repos/o/r/issues",
    "gh api --method=DELETE repos/o/r/git/refs/heads/x",
    "gh api repos/o/r/issues --field title=x",
    "gh api repos/o/r/contents/a --input body.json",
    "GH_TOKEN=x /usr/local/bin/gh api -X PATCH repos/o/r",
    "gh pr create --title t --body b",
    "gh pr merge 12 --squash",
    "gh auth status",
    "gh auth token",
    "gh repo deploy-key list -R pcalnon/juniper-ml",
    "ssh -T git@github.com",
    "ssh-add -l",
    "sudo ls",
    "defaults write com.apple.dock autohide -bool true",
    "gpg --card-status",
    "gpg -K",
    "gpg --list-secret-keys",
    "echo t | gpg --clearsign -u 'BA18D1A733B1831A!'",
    "git -c commit.gpgsign=true commit -m x",
    "git commit -S -m x",
    "security find-generic-password -s x -w",
    "cp ~/.claude/settings.json /tmp/x",
    "jq . ~/.claude/settings.json > ~/.claude/settings.json.new",
    "rm -rf ~/.claude/hooks",
    "ykman openpgp info",
]


def payload(tool: str, tool_input: dict) -> str:
    return json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "session_id": "review", "cwd": str(REPO)})


def run(guard: Path, home: Path, data: str) -> tuple[int, str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("JUNIPER_GUARD")}
    env.update(JUNIPER_GUARD_HOME=str(home), HOME=str(home))
    proc = subprocess.run([sys.executable, "-I", str(guard)], input=data, capture_output=True, text=True, env=env, timeout=30)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def decision(rc: int, out: str) -> str:
    if rc == 2:
        return "deny(exit2)"
    if rc != 0:
        return f"error(rc={rc})"
    if not out:
        return "allow"
    try:
        spec = json.loads(out)["hookSpecificOutput"]
    except (ValueError, KeyError, TypeError):
        return f"odd-output:{out[:60]}"
    return "deny" if spec.get("permissionDecision") == "deny" else f"decision:{spec.get('permissionDecision')}"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--guard", type=Path, default=REPO / "util" / "claude_agent_guard.py")
    args = ap.parse_args(argv)
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        for sub in (".ssh", ".gnupg", ".claude/hooks"):
            (home / sub).mkdir(parents=True)
        (home / ".ssh" / "config").write_text("Host x\n", encoding="utf-8")
        (home / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
        link = Path(tmp) / "innocent.txt"
        link.symlink_to(home / ".ssh" / "config")
        cases = [("allow", "Bash", {"command": c}) for c in ALLOW_BASH] + [("deny", "Bash", {"command": c}) for c in DENY_BASH]
        cases += [
            ("deny", "Read", {"file_path": str(home / ".ssh" / "config")}),
            ("deny", "Read", {"file_path": str(link)}),
            ("deny", "Write", {"file_path": str(home / ".claude" / "settings.json"), "content": "{}"}),
            ("deny", "Edit", {"file_path": str(home / ".claude" / "hooks" / "x.py"), "old_string": "a", "new_string": "b"}),
            ("deny", "Grep", {"pattern": "Host", "path": str(home / ".ssh")}),
            ("deny", "Glob", {"pattern": str(home / ".gnupg") + "/*"}),
            ("allow", "Read", {"file_path": str(home / ".claude" / "settings.json")}),
            ("allow", "Write", {"file_path": str(home / ".claude" / "projects" / "p" / "memory" / "m.md"), "content": "x"}),
            ("allow", "Read", {"file_path": str(REPO / "docs" / "REFERENCE.md")}),
            ("allow", "Grep", {"pattern": "~/.ssh/config", "path": str(REPO / "notes")}),
        ]
        for want, tool, tool_input in cases:
            rc, out, err = run(args.guard, home, payload(tool, tool_input))
            got = decision(rc, out)
            ok = got.startswith(want)
            bad += not ok
            shown = tool_input.get("command") or tool_input.get("file_path") or tool_input.get("path") or tool_input.get("pattern")
            print(f"{'ok  ' if ok else 'BAD '} want {want:5} got {got:12} {tool:5} {str(shown).replace(str(home), '~')[:100]}")
    print(f"\n{len(cases) - bad} of {len(cases)} cases as expected")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
