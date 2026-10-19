#!/usr/bin/env python3
"""Hermetic gate for util/claude_agent_guard.py and util/install_claude_agent_guard.bash (turing bring-up C8).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

The guard is the D11 item 4 PreToolUse hook, enforcement option (b) of
``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md``. Pattern rules alone
cannot carry D11: ``Read(~/.ssh/**)`` does not bind Bash, and ``gh api`` takes its flags in any order.
Every case here feeds a PreToolUse JSON payload to the script through a subprocess, with
``JUNIPER_GUARD_HOME`` and ``HOME`` pointing at a temporary home that has its own ``.ssh``, ``.gnupg``
and ``.claude``. The real home is never read and the real ``~/.claude`` is never touched.

Pinned here:

- the plan's two H3 negative tests: ``cat ~/.ssh/config`` and a flag-first ``gh api -X POST``;
- every rule in the guard's table, each with denied and allowed cases (``RuleCoverageTest`` fails if a
  rule id has no denied case);
- every ``gh api`` write-flag spelling; ``bash -c``, ``$( )``, backticks, ``eval``, pipes, here-docs,
  ``GH_TOKEN=`` prefixes, ``/usr/local/bin/gh`` and the wrapper prefixes;
- the ``.ssh`` component boundary (``.sshrc_backup``, ``foo.ssh.txt``, ``.ssh.bak`` are allowed);
- a Read through a symlink into the temp home's ``.ssh``; self-protection on the writers while a Read
  of the settings stays allowed; Grep and Glob roots and patterns;
- malformed input exits 2 with empty stdout; an unknown tool prints nothing;
- stdout is EMPTY for every allowed case (the guard never emits ``allow``), and a deny is exactly one
  JSON object of the documented shape whose reason names the rule id and says owner-run (D11);
- the guard parses as Python 3.9 and runs under ``/usr/bin/python3`` when that exists.

The installer cases run ``/bin/bash`` (3.2 on macOS) with ``--settings`` and ``--hooks-dir`` in a temp
tree: ``--dry-run`` writes nothing; ``--apply`` keeps an existing ``cc-status`` PreToolUse hook, adds
its entry once, stays idempotent, and writes a backup; ``--uninstall`` restores the prior entry set;
the sha256 file matches; every exit code is reached.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess  # nosec B404 - drives the hook and the installer as subprocesses
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / "util" / "claude_agent_guard.py"
INSTALLER = REPO_ROOT / "util" / "install_claude_agent_guard.bash"
SYSTEM_PYTHON = "/usr/bin/python3"
BASH = "/bin/bash"
TIMEOUT_SECONDS = 60
OVERRIDE_ENV = "JUNIPER_GUARD_HOME"
MATCHER = "Bash|Read|Write|Edit|MultiEdit|NotebookEdit|Grep|Glob"
DENY_RULES = ["Read(~/.ssh/**)", "Read(~/.gnupg/**)", "Edit(~/.ssh/**)", "Edit(~/.gnupg/**)", "Bash(sudo *)", "Bash(ssh-add*)", "Bash(gpg --card-status*)", "Bash(gpg -K*)"]
CC_STATUS = {"hooks": [{"type": "command", "command": "/Users/example/.config/iterm2/cc-status"}]}


def _load_guard():
    spec = importlib.util.spec_from_file_location("claude_agent_guard", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rules_named(reason: str) -> list:
    """The primary rule id of a deny reason, then any listed under 'Also matched'."""
    primary = re.search(r"Rule ([A-Z0-9-]+):", reason)
    also = re.search(r"Also matched: ([A-Z0-9, -]+)\.", reason)
    return ([primary.group(1)] if primary else []) + ([r.strip() for r in also.group(1).split(",")] if also else [])


class GuardHarness(unittest.TestCase):
    """A temporary home (with .ssh, .gnupg, .claude), a repo inside it, and symlinks into it."""

    _tmp: tempfile.TemporaryDirectory
    root: Path
    home: Path
    repo: Path
    subs: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="claude-agent-guard-")
        cls.root = Path(cls._tmp.name)  # deliberately unresolved: /var/... vs /private/var/... on macOS
        cls.home = cls.root / "home"
        cls.repo = cls.home / "Development" / "repo"
        files = {
            ".ssh/config": "Host example\n",
            ".ssh/id_test": "not a key\n",
            ".gnupg/pubring.kbx": "x\n",
            ".gnupg/gpg-agent.conf": "x\n",
            ".sshrc_backup": "x\n",
            "foo.ssh.txt": "x\n",
            ".ssh.bak/old": "x\n",
            ".claude/settings.json": "{}\n",
            ".claude/settings.local.json": "{}\n",
            ".claude/hooks/old_hook.py": "x\n",
            ".claude/projects/x/memory/MEMORY.md": "x\n",
            "Development/repo/.claude/settings.json": "{}\n",
            "Development/repo/README.md": "x\n",
            "Development/repo/nb.ipynb": "{}\n",
        }
        for rel, body in files.items():
            path = cls.home / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        (cls.home / ".claude" / "agents").mkdir()
        elsewhere = cls.root / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "link-to-ssh").symlink_to(cls.home / ".ssh")
        (elsewhere / "cfg").symlink_to(cls.home / ".ssh" / "config")
        (elsewhere / "link-to-settings").symlink_to(cls.home / ".claude" / "settings.json")
        (elsewhere / "link-to-hooks").symlink_to(cls.home / ".claude" / "hooks")
        cls.subs = {"@HOME@": str(cls.home), "@REAL@": os.path.realpath(cls.home), "@REPO@": str(cls.repo), "@ROOT@": str(cls.root)}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def sub(self, value):
        if isinstance(value, str):
            for key, path in self.subs.items():
                value = value.replace(key, path)
            return value
        if isinstance(value, dict):
            return {k: self.sub(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.sub(v) for v in value]
        return value

    def run_guard(self, payload=None, raw=None, python=None, cwd=None) -> tuple:
        if raw is None:
            raw = json.dumps(payload).encode("utf-8")
        env = RedactedEnv(os.environ)
        env[OVERRIDE_ENV] = str(self.home)
        env["HOME"] = str(self.home)
        proc = subprocess.run(  # nosec B603 - fixed argv, temp home
            [python or sys.executable, "-I", str(GUARD)],
            input=raw,
            capture_output=True,
            env=env,
            cwd=str(cwd or self.repo),
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def decide(self, tool: str, tool_input, cwd=None, python=None) -> tuple:
        payload = {
            "session_id": "test-session",
            "transcript_path": "/dev/null",
            "hook_event_name": "PreToolUse",
            "permission_mode": "bypassPermissions",
            "tool_name": tool,
            "tool_input": self.sub(tool_input),
            "cwd": self.sub(cwd) if cwd else str(self.repo),
            "tool_use_id": "toolu_test",
        }
        return self.run_guard(payload, python=python)

    def assert_denied(self, tool: str, tool_input, rule_id: str, cwd=None, primary: bool = False) -> dict:
        code, out, err = self.decide(tool, tool_input, cwd)
        label = "%s %r" % (tool, tool_input)
        self.assertEqual(code, 0, "%s: exit %d, stderr %s" % (label, code, err))
        self.assertTrue(out.strip(), "%s: expected a deny from %s, got no output" % (label, rule_id))
        self.assertEqual(out.count("\n"), 1, "%s: a deny is exactly one JSON line" % label)
        decision = json.loads(out)
        self.assertEqual(set(decision), {"hookSpecificOutput"}, label)
        spec = decision["hookSpecificOutput"]
        self.assertEqual(set(spec), {"hookEventName", "permissionDecision", "permissionDecisionReason"}, label)
        self.assertEqual(spec["hookEventName"], "PreToolUse", label)
        self.assertEqual(spec["permissionDecision"], "deny", label)
        reason = spec["permissionDecisionReason"]
        self.assertIn("OWNER-run", reason, label)
        self.assertIn("D11", reason, label)
        named = _rules_named(reason)
        if primary:
            self.assertEqual(named[:1], [rule_id], "%s: %s" % (label, reason))
        else:
            self.assertIn(rule_id, named, "%s: %s" % (label, reason))
        return spec

    def assert_allowed(self, tool: str, tool_input, cwd=None) -> None:
        code, out, err = self.decide(tool, tool_input, cwd)
        self.assertEqual((code, out), (0, ""), "%s %r must pass silently (no output, never an allow); stderr: %s" % (tool, tool_input, err))

    def check_table(self, tool: str, table: list, key: str = "command", cwd=None) -> None:
        for value, expected in table:
            tool_input = {key: value} if isinstance(value, str) else value
            with self.subTest(tool=tool, value=value, expected=expected):
                if expected is None:
                    self.assert_allowed(tool, tool_input, cwd)
                else:
                    self.assert_denied(tool, tool_input, expected, cwd)


CRED_BASH = "CRED-PATH-BASH"
SSH_PROBE = "SSH-PROBE"
PRIV = "PRIV-ESCALATION"
DEFAULTS = "MACOS-DEFAULTS-WRITE"
GPG_SECRET = "GPG-SECRET"  # nosec B105 - a rule id, not a credential
GPG_SIGN = "GPG-SIGN"
GH_PR = "GH-PR-WRITE"
GH_KEY = "GH-KEY-ADMIN"
GH_AUTH = "GH-AUTH"
GH_API = "GH-API-WRITE"
KEYCHAIN = "KEYCHAIN-DUMP"
SELF_BASH = "SELF-PROTECT-BASH"
CRED_FILE = "CRED-PATH-FILE"
SELF_FILE = "SELF-PROTECT-FILE"
CRED_SEARCH = "CRED-PATH-SEARCH"

# (command, the rule it must trip, or None for "passes silently")
CRED_PATH_CASES = [
    ("cat $HOME/.ssh/config", CRED_BASH),
    ("cat ${HOME}/.ssh/id_test", CRED_BASH),
    ('ls "$HOME"/.gnupg', CRED_BASH),
    ("cat @HOME@/.ssh/config", CRED_BASH),
    ("cat @REAL@/.ssh/config", CRED_BASH),
    ("cat ../.ssh/config", CRED_BASH),
    ("ls .ssh/", CRED_BASH),
    ("ls -la .gnupg", CRED_BASH),
    ("cat ~/.SSH/config", CRED_BASH),
    ('cat ~/.s"s"h/config', CRED_BASH),
    ("cat ~/.s\\sh/config", CRED_BASH),
    ("cat ~/.$'\\x73'sh/config", CRED_BASH),
    ("cat ~/.{ssh,nothing}/config", CRED_BASH),
    ("cat ~/.ss?/config", CRED_BASH),
    ("cat ~/.*/config", CRED_BASH),
    ("cd ~ && cat .*/config", CRED_BASH),
    ("cd && cat .ss*/config", CRED_BASH),
    ("d=x; cat ~/${d}/config", CRED_BASH),
    ("tar czf /tmp/k.tgz -C ~ .ssh", CRED_BASH),
    ("git -C ~/.ssh status", CRED_BASH),
    ("GIT_SSH_COMMAND='ssh -i ~/.ssh/id_test' git fetch origin", CRED_BASH),
    ("grep -r PRIVATE ~", CRED_BASH),
    ("grep -rn BEGIN @HOME@", CRED_BASH),
    ("find ~ -name 'id_*'", CRED_BASH),
    ("rg BEGIN /", CRED_BASH),
    ("cd ~ && rg --hidden BEGIN", CRED_BASH),
    ("cat @ROOT@/elsewhere/link-to-ssh/config", CRED_BASH),
    ("echo 'see ~/.ssh/config'", CRED_BASH),  # a mention is enough: false positives over false negatives
    ("# cat ~/.ssh/config", CRED_BASH),
    ("cat <<'EOF'\n~/.ssh/config\nEOF", CRED_BASH),
    # the component boundary: these are other names, not the credential directories
    ("ls -la .sshrc_backup", None),
    ("cat foo.ssh.txt", None),
    ("ls ~/.ssh.bak", None),
    ("ls .ssh-old", None),
    ("echo $GIT_SSH_COMMAND", None),
    ("GIT_SSH_COMMAND='ssh -o IdentitiesOnly=yes' git fetch origin", None),
    ("ls -d .*", None),
    ("ls ~/Development", None),
    ("grep -rn sudo util/", None),
    ("find . -name '*.py'", None),
    ("rg TODO", None),
    ("du -sh ~", None),
    ("ls -a ~", None),
]

SSH_PRIV_DEFAULTS_CASES = [
    ("ssh -T git@github.com", SSH_PROBE),
    ("ssh -o BatchMode=yes -T github_juniper-ml", SSH_PROBE),
    ("ssh -vT git@github.com", SSH_PROBE),
    ("ssh git@github.com", SSH_PROBE),
    ("ssh-add -l", SSH_PROBE),
    ("/usr/bin/ssh-add -L", SSH_PROBE),
    ("ssh -G github_juniper-ml", None),
    ("ssh -G github.com", None),
    ("ssh-keyscan github.com", None),
    ("grep -rn ssh-add util/", None),
    ("ls util/ssh-add-notes.md", None),
    ("ssh yamaguchi uptime", None),
    ("sudo ls", PRIV),
    ("LC_ALL=C sudo -n true", PRIV),
    ("A=1 B=2 ssh -T git@github.com", SSH_PROBE),
    ("/usr/bin/sudo -n true", PRIV),
    ("echo x | sudo tee /etc/hosts", PRIV),
    ("true && sudo pmset -g", PRIV),
    ("if sudo -n true; then echo y; fi", PRIV),
    ("SUDO=sudo; $SUDO ls", PRIV),
    ("su - root -c id", PRIV),
    ("doas ls", PRIV),
    ("SUDO ls", PRIV),
    ("{sudo,} ls", PRIV),
    ("timeout 5 sudo true", PRIV),
    ("nohup sudo true &", PRIV),
    ("xargs sudo rm < list.txt", PRIV),
    ("find . -name x -exec sudo rm {} \\;", PRIV),
    ("osascript -e 'do shell script \"ls\" with administrator privileges'", PRIV),
    ("grep -n sudo notes/x.md", None),
    ("cat notes/sudo-usage.md", None),
    ("ls pseudo_sudo.txt", None),
    ("echo sudo", None),
    ("find util -name '*.bash' -exec grep -l sudo {} +", None),
    ("defaults write com.apple.finder AppleShowAllFiles -bool true", DEFAULTS),
    ("defaults -currentHost write com.apple.screensaver idleTime 0", DEFAULTS),
    ("defaults delete com.example.app", DEFAULTS),
    ("defaults read com.apple.finder", None),
    ('grep -rn "defaults write" notes/', None),
]

GPG_CASES = [
    ("gpg --card-status", GPG_SECRET),
    ("gpg2 --card-status", GPG_SECRET),
    ("gpg -K", GPG_SECRET),
    ("/usr/local/bin/gpg --with-colons -K", GPG_SECRET),
    ("gpg --list-secret-keys --keyid-format long", GPG_SECRET),
    ("gpg --list-secret", GPG_SECRET),
    ("gpg --export-secret-keys KEYID", GPG_SECRET),
    ("gpg --export-secret-subkeys KEYID", GPG_SECRET),
    ("gpg --card-edit", GPG_SECRET),
    ("gpg --edit-card", GPG_SECRET),
    ("ykman list", GPG_SECRET),
    ("ykman openpgp keys set-touch sig cached", GPG_SECRET),
    ("gpg-connect-agent 'scd serialno' /bye", GPG_SECRET),
    ("gpg-connect-agent learn /bye", GPG_SECRET),
    ("echo learn | gpg-connect-agent", GPG_SECRET),
    ("gpg --list-keys", None),
    ("gpg -k", None),
    ("gpg --export --armor KEYID", None),
    ("gpg --verify x.sig x", None),
    ("gpg --fingerprint KEYID", None),
    ("gpg --version", None),
    ("gpg-connect-agent reloadagent /bye", None),
    ("git commit -S -m x", GPG_SIGN),
    ("GIT_TRACE=1 git commit -S -m x", GPG_SIGN),
    ("git commit --gpg-sign=KEYID -m x", GPG_SIGN),
    ("git -c commit.gpgsign=true commit -m x", GPG_SIGN),
    ("git tag -s v1 -m x", GPG_SIGN),
    ("git tag -u KEYID v1", GPG_SIGN),
    ("git rebase -S main", GPG_SIGN),
    ("git push --signed origin main", GPG_SIGN),
    ("gpg --sign x", GPG_SIGN),
    ("gpg -s x", GPG_SIGN),
    ("gpg --clearsign x", GPG_SIGN),
    ("gpg -d secret.gpg", GPG_SIGN),
    ("unset GIT_CONFIG_COUNT; git commit -m x", GPG_SIGN),
    ("GIT_CONFIG_COUNT=0 git commit -m x", GPG_SIGN),
    ("env -u GIT_CONFIG_COUNT git commit -m x", GPG_SIGN),
    ("env -i git commit -m x", GPG_SIGN),
    ('git commit -m "Sign off"', None),
    ("git commit -s -m x", None),
    ("git log -S foo", None),
    ("git -c commit.gpgsign=false commit -m x", None),
    ("git tag -a v1 -m x", None),
    ("git config commit.gpgsign", None),  # the C8 acceptance probe itself
    ("git verify-commit HEAD", None),
    ("git merge -s ours main", None),
    ("env | grep GIT_CONFIG", None),
]

GH_CASES = [
    ("gh pr create --fill", GH_PR),
    ("gh pr new --fill", GH_PR),
    ("gh pr merge 5 --squash", GH_PR),
    ("gh pr -R pcalnon/juniper-ml merge 5", GH_PR),
    ("gh pr --repo=o/r create", GH_PR),
    ("gh pr view 5", None),
    ("gh pr checks 5", None),
    ("gh pr list --search merge", None),
    ("gh pr list --state open --json number", None),
    ("gh pr diff 5", None),
    ("gh repo deploy-key list", GH_KEY),
    ("gh repo deploy-key add k.pub --allow-write", GH_KEY),
    ("gh ssh-key add k.pub", GH_KEY),
    ("gh repo view", None),
    ("gh ssh-key list", None),
    ("gh auth status", GH_AUTH),
    ("gh auth token", GH_AUTH),
    ("gh auth refresh -s workflow", GH_AUTH),
    ("gh auth login", GH_AUTH),
    ("gh auth logout", GH_AUTH),
    ("gh auth setup-git", GH_AUTH),
    ("echo $(gh auth token)", GH_AUTH),
    ("gh api repos/o/r/contents/auth", None),
    ("security find-generic-password -s github -w", KEYCHAIN),
    ("security find-internet-password -s github.com", KEYCHAIN),
    ("security dump-keychain", KEYCHAIN),
    ("security export -k login.keychain -o x.p12", KEYCHAIN),
    ("security list-keychains", None),
    ("security find-certificate -a -c Apple", None),
]

# every spelling of a gh api write or field flag, in every position
GH_API_SPELLINGS = [
    "gh api repos/o/r/issues -X POST",
    "gh api -XPOST repos/o/r/issues",
    "gh api --method POST repos/o/r/issues",
    "gh api --method=POST repos/o/r/issues",
    "gh api -X GET repos/o/r",
    "gh api repos/o/r/issues -f title=x",
    "gh api repos/o/r/issues -ftitle=x",
    "gh api repos/o/r/issues -F n=1",
    "gh api repos/o/r/issues -Fn=1",
    "gh api repos/o/r/issues --field n=1",
    "gh api repos/o/r/issues --field=n=1",
    "gh api repos/o/r/issues --raw-field body=x",
    "gh api repos/o/r/issues --raw-field=body=x",
    "gh api repos/o/r/issues --input body.json",
    "gh api repos/o/r/issues --input=body.json",
    "gh api -iX POST repos/o/r",
    "gh api graphql -f query='{viewer{login}}'",  # read-only GraphQL is blocked too (D11 accepts it)
    "gh api -H 'X-HTTP-Method-Override: POST' repos/o/r",
    "gh alias set w 'api -X POST'",
]

# the same call through every shell construct the tokenizer must see through
GH_API_WRAPPERS = [
    "bash -c 'gh api -X POST repos/o/r/issues'",
    'sh -c "gh api --method PATCH repos/o/r"',
    "zsh -lc 'gh api -X DELETE repos/o/r'",
    "eval 'gh api -X POST repos/o/r/issues'",
    "echo $(gh api -X POST repos/o/r/issues)",
    "echo `gh api -X POST repos/o/r/issues`",
    "(gh api -X POST repos/o/r/issues)",
    "{ gh api -X POST repos/o/r/issues; }",
    "true; gh api -X POST repos/o/r/issues",
    "true && gh api -X POST repos/o/r/issues",
    "false || gh api -X POST repos/o/r/issues",
    "echo '{}' | gh api --input - repos/o/r/issues",
    "gh api -X POST repos/o/r/issues &",
    "ls\ngh api -X POST repos/o/r/issues",
    "GH_TOKEN=x gh api -X POST repos/o/r/issues",
    "/usr/local/bin/gh api -X POST repos/o/r/issues",
    "command gh api -X POST repos/o/r/issues",
    "env gh api -X POST repos/o/r/issues",
    "env GH_TOKEN=x gh api -X POST repos/o/r/issues",
    "exec gh api -X POST repos/o/r/issues",
    "gh api \\\n  -X POST repos/o/r/issues",
    "timeout 30 gh api -X POST repos/o/r/issues",
    "printf '%s\\n' -X POST | xargs gh api repos/o/r/issues",
    "x=gh; $x api -X POST repos/o/r/issues",
    'GH=gh; "$GH" api --method POST repos/o/r',
    "watch -n 5 gh api -X POST repos/o/r/issues",
    "find . -maxdepth 0 -exec gh api -X POST repos/o/r/issues \\;",
    "echo 'gh api -X POST repos/o/r/issues' | bash",
    "bash <<'EOF'\ngh api -X POST repos/o/r/issues\nEOF",
    "bash -c \"$(printf 'gh api -X POST repos/o/r/issues')\"",
    "python3 -c \"import os; os.system('gh api -X POST repos/o/r/issues')\"",
    "python3 -c \"import subprocess; subprocess.run(['gh', 'api', '-X', 'POST', 'repos/o/r/issues'])\"",
    "echo gh api -X POST repos/o/r/issues",  # a mention is enough: false positives over false negatives
]

GH_API_ALLOWED = [
    "gh api repos/o/r/pulls --jq '.[].number'",
    "gh api repos/o/r/pulls -q '.[].number'",
    "gh api -H 'Accept: application/vnd.github+json' repos/o/r",
    "gh api -H 'X-GitHub-Api-Version: 2022-11-28' repos/o/r",
    "gh api --paginate repos/o/r/issues",
    "gh api 'repos/o/r/actions/runs?per_page=5'",
    'git commit -m "fix gh api -X handling"',
    "cat > notes.md <<'EOF'\nOwner-only: gh api -X POST repos/o/r/issues\nEOF",
    "gh run list --limit 5",
    "gh pr view 5 --json title",
]

SELF_PROTECT_BASH_CASES = [
    ("cat ~/.claude/settings.json", SELF_BASH),
    ("echo '{}' > ~/.claude/settings.json", SELF_BASH),
    ("cp x $HOME/.claude/settings.local.json", SELF_BASH),
    ("rm -rf ~/.claude/hooks/", SELF_BASH),
    ("ls ${HOME}/.claude/hooks", SELF_BASH),
    ("vim @HOME@/.claude/settings.json", SELF_BASH),
    ('cat "$HOME"/.claude/settings.json', SELF_BASH),
    ("mv ~/.claude ~/.claude.off", SELF_BASH),
    ("rm -rf ~/.claude", SELF_BASH),
    ("chmod -R 000 $HOME/.claude/", SELF_BASH),
    ("cd ~ && cat .claude/settings.json", SELF_BASH),
    ("cd ~/.claude && cat settings.json", SELF_BASH),
    ("ls ~/.claude/*.json", SELF_BASH),
    ("cat ../../.claude/settings.json", SELF_BASH),
    ("cat @ROOT@/elsewhere/link-to-settings", SELF_BASH),
    ("echo '{\"disableAllHooks\": true}' > .claude/settings.local.json", SELF_BASH),
    ("python3 -c \"open(__import__('os').path.expanduser('~/.claude/settings.json'), 'w')\"", SELF_BASH),
    ("bash util/install_claude_agent_guard.bash --apply", SELF_BASH),
    ("bash util/install_claude_agent_guard.bash --uninstall", SELF_BASH),
    ("util/install_claude_agent_guard.bash", SELF_BASH),
    ("cat .claude/settings.json", None),  # project-relative, inside the repo
    ("ls .claude/agents", None),
    ("cat ~/.claude/projects/x/memory/MEMORY.md", None),
    ("ls ~/.claude/agents/", None),
    ("ls -la ~/.claude/", None),  # listing the directory is fine; moving or removing it is not
    ("cat ~/.claude/settings.json.bak-2026-10-17-pre-C8", None),
    ("cat ~/.claude.json", None),
    ("cat ~/.claude/hooks.md", None),
    ("bash util/install_claude_agent_guard.bash --dry-run --apply", None),
    ("bash util/install_claude_agent_guard.bash --help", None),
    ("shellcheck util/install_claude_agent_guard.bash", None),
]


class PlanNegativeTests(GuardHarness):
    """The plan's H3 negative tests (section 6, rows C8 and H3): both must be denied, by name."""

    def test_cat_ssh_config_is_denied(self) -> None:
        self.assert_denied("Bash", {"command": "cat ~/.ssh/config"}, CRED_BASH, primary=True)

    def test_flag_first_gh_api_post_is_denied(self) -> None:
        self.assert_denied("Bash", {"command": "gh api -X POST repos/o/r/issues"}, GH_API, primary=True)


class BashRuleTests(GuardHarness):
    def test_credential_paths_and_the_component_boundary(self) -> None:
        self.check_table("Bash", CRED_PATH_CASES)

    def test_ssh_privilege_and_defaults(self) -> None:
        self.check_table("Bash", SSH_PRIV_DEFAULTS_CASES)

    def test_gpg_secret_and_signing(self) -> None:
        self.check_table("Bash", GPG_CASES)

    def test_gh_subcommands_and_keychain(self) -> None:
        self.check_table("Bash", GH_CASES)

    def test_every_gh_api_write_flag_spelling(self) -> None:
        self.check_table("Bash", [(c, GH_API) for c in GH_API_SPELLINGS])

    def test_gh_api_through_every_wrapper(self) -> None:
        self.check_table("Bash", [(c, GH_API) for c in GH_API_WRAPPERS])

    def test_read_only_gh_api_and_mentions_in_data_pass(self) -> None:
        self.check_table("Bash", [(c, None) for c in GH_API_ALLOWED])

    def test_self_protection(self) -> None:
        self.check_table("Bash", SELF_PROTECT_BASH_CASES)

    def test_relative_paths_resolve_against_the_payload_cwd(self) -> None:
        """No literal marker in these: only resolving against ``cwd`` tells them apart."""
        self.assert_denied("Bash", {"command": "cat ../../../.claude/settings.json"}, SELF_BASH, cwd="@REPO@/sub")
        self.assert_allowed("Bash", {"command": "cat ../.claude/settings.json"}, cwd="@REPO@/sub")
        self.assert_denied("Bash", {"command": "cat .claude/settings.json"}, SELF_BASH, cwd="@HOME@")
        self.assert_denied("Bash", {"command": "rg BEGIN"}, CRED_BASH, cwd="@HOME@")


# (tool_input, rule or None); paths use the temp home
FILE_CASES = [
    ("Read", {"file_path": "@HOME@/.ssh/config"}, CRED_FILE),
    ("Read", {"file_path": "@REAL@/.ssh/config"}, CRED_FILE),
    ("Read", {"file_path": "@HOME@/.gnupg/pubring.kbx"}, CRED_FILE),
    ("Read", {"file_path": "@HOME@/.SSH/config"}, CRED_FILE),
    ("Read", {"file_path": "@ROOT@/elsewhere/link-to-ssh/config"}, CRED_FILE),
    ("Read", {"file_path": "@ROOT@/elsewhere/cfg"}, CRED_FILE),
    ("Read", {"file_path": "~/.ssh/config"}, CRED_FILE),
    ("Read", {"file_path": "../../.ssh/config"}, CRED_FILE),
    ("Write", {"file_path": "@HOME@/.ssh/authorized_keys", "content": "x"}, CRED_FILE),
    ("Edit", {"file_path": "@HOME@/.ssh/config", "old_string": "a", "new_string": "b"}, CRED_FILE),
    ("MultiEdit", {"file_path": "@HOME@/.gnupg/gpg-agent.conf", "edits": [{"old_string": "a", "new_string": "b"}]}, CRED_FILE),
    ("NotebookEdit", {"notebook_path": "@HOME@/.ssh/x.ipynb", "new_source": "x"}, CRED_FILE),
    ("Read", {"file_path": "@HOME@/.sshrc_backup"}, None),
    ("Read", {"file_path": "@HOME@/foo.ssh.txt"}, None),
    ("Read", {"file_path": "@REPO@/README.md"}, None),
    ("Read", {"file_path": "@HOME@/.claude/settings.json"}, None),  # reading the settings is allowed
    ("Read", {"file_path": "@ROOT@/elsewhere/link-to-settings"}, None),
    ("Read", {"file_path": "@HOME@/.claude/hooks/old_hook.py"}, None),
    ("NotebookEdit", {"notebook_path": "@REPO@/nb.ipynb", "new_source": "x"}, None),
    ("Write", {"file_path": "@HOME@/.claude/settings.json", "content": "{}"}, SELF_FILE),
    ("Edit", {"file_path": "@HOME@/.claude/settings.local.json", "old_string": "a", "new_string": "b"}, SELF_FILE),
    ("MultiEdit", {"file_path": "@HOME@/.claude/settings.json", "edits": [{"old_string": "a", "new_string": "b"}]}, SELF_FILE),
    ("Write", {"file_path": "@HOME@/.claude/hooks/juniper_agent_guard.py", "content": "x"}, SELF_FILE),
    ("Write", {"file_path": "@REAL@/.claude/settings.json", "content": "{}"}, SELF_FILE),
    ("Write", {"file_path": "@ROOT@/elsewhere/link-to-settings", "content": "{}"}, SELF_FILE),
    ("Write", {"file_path": "@ROOT@/elsewhere/link-to-hooks/x.py", "content": "x"}, SELF_FILE),
    ("NotebookEdit", {"notebook_path": "@HOME@/.claude/hooks/x.ipynb", "new_source": "x"}, SELF_FILE),
    ("Write", {"file_path": "@REPO@/.claude/settings.local.json", "content": '{"disableAllHooks": true}'}, SELF_FILE),
    ("Edit", {"file_path": "@REPO@/.claude/settings.json", "old_string": "{}", "new_string": '{"disableAllHooks": true}'}, SELF_FILE),
    ("Write", {"file_path": "@REPO@/.claude/settings.json", "content": '{"permissions": {}}'}, None),
    ("Write", {"file_path": "@HOME@/.claude/projects/x/memory/y.md", "content": "x"}, None),
    ("Edit", {"file_path": "@REPO@/README.md", "old_string": "x", "new_string": "disableAllHooks is documented here"}, None),
    ("MultiEdit", {"file_path": "@REPO@/.claude/settings.json", "edits": [{"old_string": '"disableAllHooks": true', "new_string": ""}]}, None),
]

SEARCH_CASES = [
    ("Grep", {"pattern": "x", "path": "@HOME@/.ssh"}, CRED_SEARCH),
    ("Grep", {"pattern": "x", "path": "@HOME@/.gnupg"}, CRED_SEARCH),
    ("Grep", {"pattern": "x", "path": "@HOME@"}, CRED_SEARCH),
    ("Grep", {"pattern": "x", "path": "/"}, CRED_SEARCH),
    ("Grep", {"pattern": "x", "path": "@ROOT@/elsewhere/link-to-ssh"}, CRED_SEARCH),
    ("Grep", {"pattern": "x", "path": "@REPO@", "glob": "@HOME@/.ssh/*"}, CRED_SEARCH),
    ("Grep", {"pattern": "x", "path": "~/.ssh"}, CRED_SEARCH),
    ("Glob", {"pattern": "@HOME@/.ssh/*"}, CRED_SEARCH),
    ("Glob", {"pattern": "~/.ssh/**"}, CRED_SEARCH),
    ("Glob", {"pattern": ".ssh/*", "path": "@HOME@"}, CRED_SEARCH),
    ("Glob", {"pattern": "**/*", "path": "@HOME@"}, CRED_SEARCH),
    ("Glob", {"pattern": "**/id_*", "path": "@HOME@"}, CRED_SEARCH),
    ("Glob", {"pattern": "@HOME@/.ss?/*"}, CRED_SEARCH),
    ("Glob", {"pattern": "@HOME@/.{ssh,x}/*"}, CRED_SEARCH),
    ("Glob", {"pattern": "@ROOT@/elsewhere/link-to-ssh/*"}, CRED_SEARCH),
    ("Grep", {"pattern": "~/.ssh/config", "path": "@REPO@"}, None),  # the pattern is a content regex
    ("Grep", {"pattern": "x"}, None),
    ("Grep", {"pattern": "x", "path": "@HOME@/foo.ssh.txt"}, None),
    ("Glob", {"pattern": "**/*.py", "path": "@REPO@"}, None),
    ("Glob", {"pattern": "*.txt", "path": "@HOME@"}, None),
    ("Glob", {"pattern": "**/*.md"}, None),
]


class FileAndSearchRuleTests(GuardHarness):
    def test_file_tools(self) -> None:
        for tool, tool_input, expected in FILE_CASES:
            with self.subTest(tool=tool, tool_input=tool_input):
                if expected is None:
                    self.assert_allowed(tool, tool_input)
                else:
                    self.assert_denied(tool, tool_input, expected)

    def test_search_tools(self) -> None:
        for tool, tool_input, expected in SEARCH_CASES:
            with self.subTest(tool=tool, tool_input=tool_input):
                if expected is None:
                    self.assert_allowed(tool, tool_input)
                else:
                    self.assert_denied(tool, tool_input, expected)

    def test_grep_from_home_by_default_cwd_is_denied(self) -> None:
        self.assert_denied("Grep", {"pattern": "BEGIN"}, CRED_SEARCH, cwd="@HOME@")


MALFORMED = [
    b"not json",
    b"",
    b"[]",
    b'"a string"',
    b"{}",
    b'{"tool_name": 5}',
    b'{"tool_name": "Bash"}',
    b'{"tool_name": "Bash", "tool_input": "ls"}',
    b'{"tool_name": "Bash", "tool_input": {}}',
    b'{"tool_name": "Bash", "tool_input": {"command": ["ls"]}}',
    b'{"tool_name": "Read", "tool_input": {"file_path": 7}}',
    b'{"tool_name": "Write", "tool_input": {}}',
    b'{"tool_name": "Glob", "tool_input": {}}',
    b'{"tool_name": "Grep", "tool_input": {"pattern": "x", "path": 5}}',
    b"\xff\xfe\x00",
    b'{"tool_name": "Bash", "tool_input": {"command": "' + b"$(" * 40 + b'"}}',
]


class ContractTests(GuardHarness):
    def test_malformed_input_fails_closed_with_exit_2(self) -> None:
        for raw in MALFORMED:
            with self.subTest(raw=raw[:60]):
                code, out, err = self.run_guard(raw=raw)
                self.assertEqual(code, 2, "malformed input must exit 2 (fail closed)")
                self.assertEqual(out, "", "nothing on stdout for malformed input")
                self.assertIn("juniper-agent-guard", err)

    def test_unknown_tools_pass_silently(self) -> None:
        for payload in (
            {"tool_name": "WebFetch", "tool_input": {"url": "https://example.com"}},
            {"tool_name": "TodoWrite"},
            {"tool_name": "mcp__serena__read_file", "tool_input": {"relative_path": "~/.ssh/config"}},
        ):
            with self.subTest(tool=payload["tool_name"]):
                self.assertEqual(self.run_guard(payload)[:2], (0, ""))

    def test_no_case_ever_emits_allow(self) -> None:
        commands = [c for c, _ in CRED_PATH_CASES + GH_CASES] + GH_API_ALLOWED[:3] + GH_API_SPELLINGS[:3]
        for command in commands:
            with self.subTest(command=command):
                _, out, _ = self.decide("Bash", {"command": command})
                self.assertNotIn('"allow"', out)
                self.assertNotIn('"ask"', out)
                if out:
                    self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_deny_reason_names_the_rule_and_the_owner(self) -> None:
        spec = self.assert_denied("Bash", {"command": "gh pr merge 7"}, GH_PR, primary=True)
        reason = spec["permissionDecisionReason"]
        self.assertTrue(reason.startswith("juniper-agent-guard denied this Bash call. Rule GH-PR-WRITE:"), reason)
        self.assertIn("notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md", reason)
        self.assertIn("ask the owner", reason)

    def test_several_rules_are_all_named(self) -> None:
        spec = self.assert_denied("Bash", {"command": "sudo cat ~/.ssh/config"}, CRED_BASH, primary=True)
        self.assertIn(PRIV, _rules_named(spec["permissionDecisionReason"]))


class RuleCoverageTest(unittest.TestCase):
    def test_every_rule_has_a_denied_case(self) -> None:
        ids = {rule.rule_id for rule in _load_guard().RULES}
        covered = {rule for _, rule in CRED_PATH_CASES + SSH_PRIV_DEFAULTS_CASES + GPG_CASES + GH_CASES + SELF_PROTECT_BASH_CASES if rule}
        covered |= {rule for _, _, rule in FILE_CASES + SEARCH_CASES if rule}
        covered |= {GH_API}
        self.assertEqual(ids - covered, set(), "rules with no denied case in this suite")
        self.assertEqual(covered - ids, set(), "cases name rules the guard does not have")


class PortabilityAndCliTests(GuardHarness):
    def test_guard_parses_as_python_3_9(self) -> None:
        ast.parse(GUARD.read_text(encoding="utf-8"), filename=str(GUARD), feature_version=(3, 9))

    def test_installer_merge_program_parses_as_python_3_9(self) -> None:
        text = INSTALLER.read_text(encoding="utf-8")
        program = text.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
        ast.parse(program, filename="install_claude_agent_guard.bash:merge", feature_version=(3, 9))

    @unittest.skipUnless(os.access(SYSTEM_PYTHON, os.X_OK), "no /usr/bin/python3 on this host")
    def test_system_python_runs_the_guard(self) -> None:
        proc = subprocess.run([SYSTEM_PYTHON, "-I", str(GUARD), "--self-test"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)  # nosec B603
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assert_allowed("Read", {"file_path": "@REPO@/README.md"})
        code, out, _ = self.decide("Bash", {"command": "cat ~/.ssh/config"}, python=SYSTEM_PYTHON)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")
        code, out, _ = self.decide("Bash", {"command": "ls"}, python=SYSTEM_PYTHON)
        self.assertEqual((code, out), (0, ""))

    def run_cli(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", str(GUARD), *args], capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)  # nosec B603

    def test_self_test_passes(self) -> None:
        proc = self.run_cli("--self-test")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertRegex(proc.stdout, r"self-test: (\d+) of \1 checks passed")

    def test_version_help_and_rule_list(self) -> None:
        version = self.run_cli("--version")
        self.assertEqual(version.returncode, 0)
        self.assertRegex(version.stdout, r"^juniper-agent-guard \d+\.\d+\.\d+$")
        helptext = self.run_cli("--help")
        self.assertEqual(helptext.returncode, 0)
        for needle in (MATCHER, '"onFailure": "block"', '"timeout": 10', "/usr/bin/python3", "PreToolUse"):
            self.assertIn(needle, helptext.stdout)
        listing = self.run_cli("--list-rules")
        self.assertEqual(listing.returncode, 0)
        for rule in _load_guard().RULES:
            self.assertIn(rule.rule_id, listing.stdout)
        self.assertEqual(self.run_cli("--no-such-flag").returncode, 2)

    def test_installed_copy_ignores_the_test_override(self) -> None:
        """The live copy under <home>/.claude/hooks/ must not let an env var move the protected homes."""
        mod = _load_guard()
        fake_pw = str(self.root / "pw-home")
        with mock.patch.dict(os.environ, {OVERRIDE_ENV: str(self.home), "HOME": str(self.home)}):
            with mock.patch.object(mod, "_password_home", return_value=fake_pw):
                self.assertEqual(mod.resolve_homes(), [str(self.home)])
                mod.__file__ = os.path.join(fake_pw, ".claude", "hooks", "juniper_agent_guard.py")
                self.assertEqual(mod.resolve_homes(), [str(self.home), fake_pw])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class InstallerTests(unittest.TestCase):
    """util/install_claude_agent_guard.bash against a temp settings file and hooks dir only."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="claude-agent-guard-installer-")
        self.root = Path(self._tmp.name)
        self.home = self.root / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.settings = self.home / ".claude" / "settings.json"
        self.hooks = self.home / ".claude" / "hooks"
        self.installed = self.hooks / "juniper_agent_guard.py"
        self.original = {
            "env": {"GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "commit.gpgsign", "GIT_CONFIG_VALUE_0": "false"},
            "hooks": {"PreToolUse": [CC_STATUS], "Stop": [CC_STATUS]},
            "mcpServers": {},
            "skipDangerousModePermissionPrompt": True,
            "tui": "fullscreen",
        }
        self.write_settings(self.original)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_settings(self, data) -> None:
        self.settings.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
        self.original_bytes = self.settings.read_bytes()

    def install(self, *args, hook_python=None, extra_env=None) -> tuple:
        env = RedactedEnv(os.environ)
        env["HOME"] = str(self.home)
        env.pop("MERGE_PYTHON", None)
        env["HOOK_PYTHON"] = hook_python or sys.executable
        env.update(extra_env or {})
        proc = subprocess.run(  # nosec B603 - fixed argv, temp tree
            [BASH, str(INSTALLER), "--settings", str(self.settings), "--hooks-dir", str(self.hooks), *args],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.root),
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
        return proc.returncode, proc.stdout + proc.stderr

    def settings_now(self) -> dict:
        return json.loads(self.settings.read_text(encoding="utf-8"))

    def backups(self) -> list:
        return sorted(p.name for p in self.settings.parent.iterdir() if p.name.startswith("settings.json.bak-"))

    def our_entries(self, data: dict) -> list:
        return [e for e in data.get("hooks", {}).get("PreToolUse", []) if e is not CC_STATUS and e != CC_STATUS]

    def expected_entry(self) -> dict:
        return {"matcher": MATCHER, "hooks": [{"type": "command", "command": sys.executable, "args": ["-I", str(self.installed)], "timeout": 10, "onFailure": "block"}]}

    def test_dry_run_writes_nothing(self) -> None:
        for args in (["--dry-run"], ["--apply", "--dry-run"], ["--uninstall", "--dry-run"]):
            with self.subTest(args=args):
                code, out = self.install(*args)
                self.assertEqual(code, 0, out)
                self.assertIn("DRY-RUN", out)
                self.assertEqual(self.settings.read_bytes(), self.original_bytes)
                self.assertFalse(self.hooks.exists(), "dry-run must not create the hooks dir")
                self.assertEqual(self.backups(), [])

    def test_default_action_installs_the_copy_and_prints_the_json(self) -> None:
        code, out = self.install()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.settings.read_bytes(), self.original_bytes, "the default action must not edit settings")
        self.assertEqual(self.installed.read_bytes(), GUARD.read_bytes())
        self.assertEqual(stat.S_IMODE(self.installed.stat().st_mode), 0o644)
        self.assertFalse(self.installed.is_symlink(), "a copy, not a symlink")
        printed = json.loads(out.split("(or re-run with --apply):\n", 1)[1])
        self.assertEqual(printed, {"hooks": {"PreToolUse": [self.expected_entry()]}, "permissions": {"deny": DENY_RULES}})

    def test_default_hook_interpreter_is_usr_bin_python3(self) -> None:
        env = {"MERGE_PYTHON": sys.executable}
        code, out = self.install("--dry-run", hook_python=SYSTEM_PYTHON, extra_env=env)
        self.assertEqual(code, 0, out)
        printed = json.loads(out.split("merge into %s:\n" % self.settings, 1)[1])
        hook = printed["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertEqual((hook["command"], hook["args"], hook["timeout"], hook["onFailure"]), (SYSTEM_PYTHON, ["-I", str(self.installed)], 10, "block"))
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertIn('HOOK_PYTHON="${HOOK_PYTHON:-/usr/bin/python3}"', source)

    def test_apply_keeps_cc_status_adds_the_entry_once_and_is_idempotent(self) -> None:
        code, out = self.install("--apply")
        self.assertEqual(code, 0, out)
        data = self.settings_now()
        self.assertEqual(data["hooks"]["PreToolUse"][0], CC_STATUS, "the existing cc-status hook must stay, first")
        self.assertEqual(data["hooks"]["PreToolUse"][1:], [self.expected_entry()])
        self.assertEqual(data["hooks"]["Stop"], [CC_STATUS])
        self.assertEqual(data["permissions"]["deny"], DENY_RULES)
        for key in ("env", "mcpServers", "skipDangerousModePermissionPrompt", "tui"):
            self.assertEqual(data[key], self.original[key])
        after_first = self.settings.read_bytes()
        self.assertEqual(len(self.backups()), 1)
        self.assertRegex(self.backups()[0], r"^settings\.json\.bak-\d{8}T\d{6}Z-pre-agent-guard$")
        self.assertEqual((self.settings.parent / self.backups()[0]).read_bytes(), self.original_bytes)

        code, out = self.install("--apply")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.settings.read_bytes(), after_first, "a second --apply must change nothing")
        self.assertEqual(len(self.backups()), 1, "an unchanged apply writes no backup")
        self.assertEqual(len(self.settings_now()["hooks"]["PreToolUse"]), 2)

    def test_sha256_file_matches_the_copy_and_the_source(self) -> None:
        code, out = self.install("--apply")
        self.assertEqual(code, 0, out)
        recorded = (self.hooks / "juniper_agent_guard.py.sha256").read_text(encoding="utf-8")
        self.assertEqual(recorded, "%s  juniper_agent_guard.py\n" % _sha256(GUARD))
        self.assertEqual(_sha256(self.installed), _sha256(GUARD))

    def test_uninstall_restores_the_prior_entry_set(self) -> None:
        self.assertEqual(self.install("--apply")[0], 0)
        code, out = self.install("--uninstall")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.settings_now(), self.original)
        self.assertTrue(any(name.endswith("-pre-agent-guard-uninstall") for name in self.backups()))
        self.assertFalse(self.installed.exists())
        self.assertFalse((self.hooks / "juniper_agent_guard.py.sha256").exists())

    def test_uninstall_keeps_deny_rules_that_were_there_before(self) -> None:
        mine = dict(self.original, permissions={"deny": ["Bash(sudo *)", "Bash(rm -rf /*)"], "allow": ["Bash(ls *)"]})
        self.write_settings(mine)
        self.assertEqual(self.install("--apply")[0], 0)
        deny = self.settings_now()["permissions"]["deny"]
        self.assertEqual(sorted(deny), sorted(set(DENY_RULES) | {"Bash(rm -rf /*)"}))
        self.assertEqual(self.install("--uninstall")[0], 0)
        self.assertEqual(self.settings_now(), mine)

    def test_failed_self_test_is_exit_1_and_settings_stay_untouched(self) -> None:
        code, out = self.install("--apply", hook_python="/usr/bin/false", extra_env={"MERGE_PYTHON": sys.executable})
        self.assertEqual(code, 1, out)
        self.assertIn("VERIFY FAILED", out)
        self.assertEqual(self.settings.read_bytes(), self.original_bytes)
        self.assertEqual(self.backups(), [])

    def test_unreadable_settings_json_is_exit_2_and_untouched(self) -> None:
        self.settings.write_text("{not json", encoding="utf-8")
        code, out = self.install("--apply")
        self.assertEqual(code, 2, out)
        self.assertEqual(self.settings.read_text(encoding="utf-8"), "{not json")
        self.assertEqual(self.backups(), [])

    def test_usage_errors_exit_2(self) -> None:
        for args in (["--bogus"], ["--apply", "--uninstall"], ["--settings"]):
            with self.subTest(args=args):
                env = RedactedEnv(os.environ, HOME=str(self.home), HOOK_PYTHON=sys.executable)
                proc = subprocess.run([BASH, str(INSTALLER), *args], capture_output=True, text=True, env=env, timeout=TIMEOUT_SECONDS, check=False)  # nosec B603
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        code, out = self.install("--dry-run", hook_python="python3")
        self.assertEqual(code, 2, out)
        self.assertEqual(self.settings.read_bytes(), self.original_bytes)

    def test_help_exits_0_and_documents_the_modes(self) -> None:
        code, out = self.install("--help")
        self.assertEqual(code, 0, out)
        for needle in ("--apply", "--uninstall", "--dry-run", "--settings", "--hooks-dir", "Exit: 0"):
            self.assertIn(needle, out)


if __name__ == "__main__":
    unittest.main()
