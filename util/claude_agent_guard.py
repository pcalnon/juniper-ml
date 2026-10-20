#!/usr/bin/env python3
"""
juniper-agent-guard: a Claude Code PreToolUse hook that denies what D11 forbids an agent on turing.

Project: juniper-ml
Sub-Project: host tooling (turing bring-up)
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: permanent utility. util/install_claude_agent_guard.bash (owner-run) installs it as a COPY,
        ~/.claude/hooks/juniper_agent_guard.py, so a branch switch in a checkout cannot change it.
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (D11 item 4,
         enforcement option (b); task C8; the H3 negative tests);
         notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md (S9, task K12: the
         GIT-SIGNING-* rules); tests/test_claude_agent_guard.py;
         util/ad-hoc/2026-10-17_turing_c8_guard_mutation_check.py,
         util/ad-hoc/2026-10-20_k12_guard_mutation_check.py

Why a hook
----------
D11 item 4 lists a deny set, and notes that pattern rules alone are not enough: ``Read(~/.ssh/**)``
does not bind Bash, and ``gh api`` takes its flags in any order. The sandbox option (a) is out
because it breaks git over ssh on macOS. A PreToolUse hook fires in every permission mode, including
``bypassPermissions``, and for every subagent tool call; a ``deny`` from it cannot be overridden by
any ``allow``.

Contract
--------
* stdin: the PreToolUse JSON payload. Unknown fields are ignored.
* A denied call prints exactly one JSON object on stdout and exits 0:
  ``{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
  "permissionDecisionReason": "..."}}``. The reason names the rule id and says the action is
  owner-run (D11).
* Any other call prints NOTHING and exits 0. The guard never emits ``allow``: an allow would
  short-circuit the normal permission flow.
* Malformed input (unparseable JSON, a non-object payload, a missing or non-string ``tool_name``, a
  covered tool without a usable ``tool_input``) exits 2 with the reason on stderr. So does an
  internal error. Both fail closed, and the settings entry also sets ``"onFailure": "block"``.
* An unknown tool name passes silently. The settings matcher decides which tools reach the guard.

Rules (``RULES`` below is the table; ``--list-rules`` prints it)
-----------------------------------------------------------------
Bash: CRED-PATH-BASH, SSH-PROBE, PRIV-ESCALATION, MACOS-DEFAULTS-WRITE, GPG-SECRET, GPG-SIGN,
GH-PR-WRITE, GH-KEY-ADMIN, GH-AUTH, GH-API-WRITE, KEYCHAIN-DUMP, SELF-PROTECT-BASH, GIT-SIGNING-CONFIG.
Read, Write, Edit, MultiEdit, NotebookEdit: CRED-PATH-FILE, and for the writers SELF-PROTECT-FILE and
GIT-SIGNING-FILE.
Grep and Glob: CRED-PATH-SEARCH.

The two GIT-SIGNING rules (commit-signing plan S9, task K12) guard the owner's signing configuration.
Once the owner's YubiKey stubs are learned, an agent that could rewrite that configuration could get the
owner's signature. It could point ``gpg.program`` or ``core.hooksPath`` at its own program, plant a
local key that outranks the owner's include, drop a ``post-commit`` hook inside a cached-touch window,
or re-enable signing past D11 with ``git -c include.path=`` or ``--config-env``.

The ``.ssh`` / ``.gnupg`` boundary
----------------------------------
A credential directory is matched as a whole path COMPONENT, case-insensitively (APFS is
case-insensitive by default, so ``~/.SSH/config`` opens ``~/.ssh/config``). The text ``.ssh`` or
``.gnupg`` matches only when the character before it is not a filename character
(``[A-Za-z0-9._-]``) and the character after it is not one either. So ``~/.ssh``, ``.ssh/``,
``../.ssh``, ``$HOME/.ssh`` and ``"$HOME"/.gnupg`` match, while ``.sshrc_backup``, ``foo.ssh.txt``,
``.ssh.bak``, ``.ssh-old`` and ``GIT_SSH_COMMAND`` do not. A glob component that can match one
counts too (``.ss?``, ``.s*h``, ``.{ssh,x}``). A bare dot-glob such as ``.*`` counts only when it
sits directly under a home directory, so ``ls -d .*`` in a repo stays allowed.

How Bash is read
----------------
The command is lexed the way bash splits it: quotes and backslashes are removed (``.s"s"h`` is
``.ssh``), ``$'...'`` is decoded, backslash-newline continuations are joined, and the text is split
into simple commands at ``;``, ``&&``, ``||``, ``|``, ``&``, newlines, ``( )`` and ``{ }``. The
bodies of ``$( )``, backticks, ``<( )`` / ``>( )``, ``bash -c`` / ``sh -c`` / ``zsh -c``, ``eval``,
``env -S``, ``watch``, ``find -exec``, here-documents and here-strings fed to a shell, and text piped
into a shell are all analysed as commands too. Each simple command's command word is found after
skipping ``NAME=value`` prefixes, reserved words (``if``, ``then``, ``do``, ``!`` ...) and wrappers
(``command``, ``env``, ``exec``, ``nohup``, ``time``, ``nice``, ``timeout``, ``xargs`` ...); its
basename is compared case-insensitively, so ``/usr/local/bin/gh`` is ``gh``. A command word built at
run time (``$X api -X POST``) is checked as if it could be any of the guarded tools.

False positives are preferred to false negatives
------------------------------------------------
The path rules read the whole command text, comments and here-document bodies included, so a
command that merely MENTIONS a denied path is denied (``echo "see ~/.ssh/config"``). ``gh`` is
matched at any word position, so ``echo gh api -X POST`` is denied too. To search files for text
that mentions these paths, use the Grep tool: its ``pattern`` is a content regex and is never
path-checked. ``gh api`` with any field flag is denied, which also blocks a read-only
``gh api graphql -f query=...``; D11 accepts that.

What this cannot see (the owner should weigh these)
---------------------------------------------------
A command-text hook sees only the text of the call. Known gaps:

1. What a script, binary or interpreter does internally: ``python3 x.py``, ``bash x.sh``, ``make``.
   That includes repo tools that call gh themselves (``util/open_signed_pr.py`` by design;
   ``util/safe_merge.py`` merges). Inline ``python3 -c`` / ``perl -e`` code is checked only for
   string literals that read as a guarded command.
2. Text assembled at run time or across calls: ``base64 -d <<< ... | bash``, a script written by
   one call (``echo 'gh api -X POST ..' > s.sh``) and run by the next.
3. Raw HTTP with the session's token (``curl -H "Authorization: token $GH_TOKEN" -X POST
   https://api.github.com/...``) and ``git credential fill``. D11 item 5's scoped PAT is the control.
4. Directory changes the text does not show: ``tar -C``/``git -C``/``make -C`` with a relative
   operand, ``cd "$(...)"``. A literal ``cd`` target, ``cd`` and ``cd -`` are followed.
5. A hard link to a key file made before the guard was installed; a symlink inside a search root
   (Grep/Glob do not walk the tree to find one).
6. Tools outside the settings matcher: MCP tools (Serena's ``read_file``, any MCP shell). Subagent
   tool calls are covered.
7. ``disableAllHooks`` in a project ``.claude/settings*.json`` turns user hooks off. The guard
   denies writing or naming that key, but not a file holding it copied into place, nor a nested
   ``claude --setting-sources project``. Managed settings (owner, sudo) close this fully.
8. Names, not contents: ``ls -R ~``, ``tree ~`` and ``du -a ~`` list file names under ``~/.ssh``.
9. A shell edit of a repository's own ``.git/config`` (``sed -i``, ``echo >>``, ``tee``). Reading that file
   is too common to deny by mention, so only ``git config`` writes and the file tools are guarded.
   ``util/configure_commit_signing.py --check`` fails a planted local signing key instead.

Home directory
--------------
``os.path.expanduser('~')`` at run time, plus the password-database home, so a changed ``$HOME`` in
the hook's environment cannot move the protected directories. ``JUNIPER_GUARD_HOME`` replaces both,
for tests only: the installed copy (any file under ``<home>/.claude/hooks/``) ignores it.

Settings entry (util/install_claude_agent_guard.bash writes it)
--------------------------------------------------------------
    "hooks": {"PreToolUse": [{"matcher": "Bash|Read|Write|Edit|MultiEdit|NotebookEdit|Grep|Glob",
      "hooks": [{"type": "command", "command": "/usr/bin/python3",
                 "args": ["-I", "<home>/.claude/hooks/juniper_agent_guard.py"],
                 "timeout": 10, "onFailure": "block"}]}]}

``-I`` (isolated mode) keeps ``PYTHONPATH`` and friends from reaching the hook. Runs on Python 3.9
(macOS ``/usr/bin/python3``) through 3.14, stdlib only.

Usage: juniper_agent_guard.py [--self-test | --list-rules | --version | --help]
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys

__version__ = "1.1.0"
GUARD_NAME = "juniper-agent-guard"
PLAN_DOC = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HOME_OVERRIDE_ENV = "JUNIPER_GUARD_HOME"
SETTINGS_MATCHER = "Bash|Read|Write|Edit|MultiEdit|NotebookEdit|Grep|Glob"
MAX_DEPTH = 12
MAX_BRACE_ALTERNATIVES = 64
EVIDENCE_LIMIT = 120


class Rule(object):
    """One row of the deny table: an id, the tool scope, what it matches, and why."""

    __slots__ = ("rule_id", "scope", "description", "reason")

    def __init__(self, rule_id: str, scope: str, description: str, reason: str) -> None:
        self.rule_id = rule_id
        self.scope = scope
        self.description = description
        self.reason = reason


# The deny table. Tune it here: ids are stable (tests and the mutation check name them), and every
# deny reason is "<description>. <reason>" plus the owner-run sentence built in deny_reason().
RULES = (
    Rule("CRED-PATH-BASH", "Bash", "the command references ~/.ssh or ~/.gnupg (a .ssh or .gnupg path component in any spelling, a glob that can match one, or a recursive tool rooted at home or above)", "Agents never read, list, copy or change SSH or GnuPG material on turing. To search files for text that mentions these paths, use the Grep tool instead"),
    Rule("SSH-PROBE", "Bash", "an ssh credential probe: ssh -T, ssh to a GitHub host, or ssh-add", "Live authentication and agent-key checks are credential probes. ssh -G <alias> prints the resolved config without connecting and is allowed"),
    Rule("PRIV-ESCALATION", "Bash", "privilege escalation: sudo, su, doas, pkexec, or osascript with administrator privileges", "Anything needing the admin password is owner-run"),
    Rule("MACOS-DEFAULTS-WRITE", "Bash", "a macOS settings change: defaults write, delete, rename or import", "Agents measure host settings; they do not change them"),
    Rule("GPG-SECRET", "Bash", "a GnuPG secret-key or smart-card operation: gpg --card-status, --card-edit, -K, --list-secret-keys, --export-secret-keys or --export-secret-subkeys; ykman; gpg-card; gpg-connect-agent learn or scd", "Agents never touch the YubiKey or enumerate secret keys"),
    Rule("GPG-SIGN", "Bash", "a signing or secret-key use that can prompt for the YubiKey PIN or touch: gpg --sign / --clearsign / --detach-sign / --decrypt; git commit|merge|rebase|cherry-pick|revert|am|pull|commit-tree -S; git tag -s / -u; git push --signed; git -c *.gpgsign=true", "Agent commits are unsigned by construction (D11 item 1); they land signed through util/open_signed_pr.py"),
    Rule("GH-PR-WRITE", "Bash", "gh pr create, gh pr new or gh pr merge", "Agents land changes only through util/open_signed_pr.py, and merges are the owner's"),
    Rule("GH-KEY-ADMIN", "Bash", "GitHub key administration: gh repo deploy-key, gh ssh-key add|delete, gh gpg-key add|delete", "Deploy-key and key administration stays in the owner's own session (D11 item 5)"),
    Rule("GH-AUTH", "Bash", "gh auth (status, token, refresh, login, logout, setup-git, switch ...)", "gh auth subcommands are credential probes or credential changes"),
    Rule("GH-API-WRITE", "Bash", "gh api with a write or field flag (-X / --method, -f / -F / --field / --raw-field, --input, a method-override header), or a gh alias that could hide one", "Agents use gh api for read-only GETs only; drop the flag (a plain gh api call is a GET). This also blocks a read-only gh api graphql -f query=..., which D11 accepts"),
    Rule("KEYCHAIN-DUMP", "Bash", "a macOS keychain read: security find-generic-password, find-internet-password, dump-keychain or export", "Keychain contents are credentials"),
    Rule("SELF-PROTECT-BASH", "Bash", "the command references the user-level Claude settings or hooks (~/.claude/settings.json, ~/.claude/settings.local.json, ~/.claude/hooks/), moves, removes or re-permissions ~/.claude itself, sets disableAllHooks, or runs util/install_claude_agent_guard.bash other than with --dry-run or --help", "The guard and its settings are changed only by the owner"),
    Rule(
        "GIT-SIGNING-CONFIG",
        "Bash",
        "a change to the owner's signing configuration or a way around D11: git -c include.* / includeIf.* / gpg.program / gpg.<format>.program, git --config-env (any key), "
        "a git config write at any scope of gpg.*, user.signingkey, commit.gpgsign, tag.gpgsign, include.*, includeIf.*, core.hooksPath, core.fsmonitor or core.sshCommand, "
        "git config --edit, removing or renaming those sections, a command that names ~/.gitconfig, ~/.config/git, git's system gitconfig or a .git/hooks path, "
        "or util/configure_commit_signing.py --apply / --remove without --dry-run",
        "The owner's signing configuration and git hooks are changed only by the owner (commit-signing plan S9, task K12); agent commits stay unsigned (D11) "
        "and land through util/open_signed_pr.py. Read config with git config --get / --list, and the files with the Read tool",
    ),
    Rule("CRED-PATH-FILE", "Read|Write|Edit|MultiEdit|NotebookEdit", "the target path, or the path a symlink resolves to, is inside ~/.ssh or ~/.gnupg (or has a .ssh or .gnupg component)", "Agents never read or change SSH or GnuPG material on turing"),
    Rule("SELF-PROTECT-FILE", "Write|Edit|MultiEdit|NotebookEdit", "a write to ~/.claude/settings.json, ~/.claude/settings.local.json or ~/.claude/hooks/, or a .claude/settings*.json write that sets disableAllHooks", "The guard and its settings are changed only by the owner. Reading them is allowed"),
    Rule("GIT-SIGNING-FILE", "Write|Edit|MultiEdit|NotebookEdit", "a write to ~/.gitconfig, anything under ~/.config/git, git's system gitconfig (/usr/local/etc, /opt/homebrew/etc, /etc), a repository's .git/config or config.worktree, or anything under a .git/hooks directory", "The owner's signing configuration and git hooks are changed only by the owner (commit-signing plan S9, task K12). Reading them is allowed"),
    Rule("CRED-PATH-SEARCH", "Grep|Glob", "the search root or path pattern reaches into ~/.ssh or ~/.gnupg, or the search root is home or above it (a recursive search would descend into them)", "Agents never read or list SSH or GnuPG material on turing; narrow the search root"),
)
RULE_BY_ID = {rule.rule_id: rule for rule in RULES}

# ---------------------------------------------------------------------------------------------
# Tunable data. Command names and verbs compare case-insensitively; option letters do not.
# ---------------------------------------------------------------------------------------------
CRED_DIR_NAMES = (".ssh", ".gnupg")
CLAUDE_DIR_NAME = ".claude"
CLAUDE_PROTECTED_CHILDREN = ("settings.json", "settings.local.json", "hooks")
CLAUDE_SETTINGS_FILES = ("settings.json", "settings.local.json")
DISABLE_HOOKS_KEY = "disableallhooks"
INSTALLER_NAME = "install_claude_agent_guard.bash"
INSTALLER_SAFE_FLAGS = ("--dry-run", "--help", "-h")
# commands that can move, remove or re-permission the ~/.claude directory as a whole
MUTATING_COMMANDS = ("mv", "rm", "rmdir", "unlink", "chmod", "chown", "chgrp", "chflags", "xattr", "ln", "cp", "rsync", "ditto", "tar", "find", "trash", "srm", "shred")

PRIV_COMMANDS = ("sudo", "su", "doas", "pkexec")
SSH_AGENT_COMMANDS = ("ssh-add",)
SSH_OPTS_WITH_ARG = "BbcDEeFIiJLlmOoPpQRSWw"
CARD_TOOLS = ("ykman", "gpg-card")
GPG_COMMANDS = ("gpg", "gpg2")
GPG_SECRET_LONG = ("card-status", "card-edit", "edit-card", "list-secret-keys", "export-secret-keys", "export-secret-subkeys")
GPG_SECRET_SHORT = "K"
GPG_SIGN_LONG = ("sign", "clearsign", "clear-sign", "detach-sign", "decrypt", "decrypt-files", "sign-key", "lsign-key", "quick-sign-key", "quick-lsign-key", "passwd", "change-passphrase", "change-pin")
GPG_SIGN_SHORT = "sbd"
GPG_SHORT_WITH_ARG = "oruRzNfF"
GPG_EXACT_ALLOWED = ("export",)
GPG_MIN_ABBREV = 4
GPG_AGENT_COMMANDS = ("gpg-connect-agent",)
GPG_AGENT_DENIED = ("learn", "scd")
GIT_SIGN_SUBCOMMANDS = ("commit", "merge", "rebase", "cherry-pick", "revert", "am", "pull", "commit-tree")
GIT_OPTS_WITH_ARG = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env")
# Commit-signing plan K12. Keys a `git -c` may not set: an include re-enables signing past D11's
# command scope, and a program key swaps the signer.
GIT_DASH_C_SIGNING_RE = re.compile(r"^(?:include\..*|includeif\..*|gpg\.(?:[^.]+\.)?program)$", re.IGNORECASE)
# Keys a `git config` may not write, at any scope: they outrank or replace the owner's signing include.
GIT_SIGNING_KEY_RE = re.compile(r"^(?:gpg\..+|user\.signingkey|commit\.gpgsign|tag\.gpgsign|include\..+|includeif\..+|core\.hookspath|core\.fsmonitor|core\.sshcommand)$", re.IGNORECASE)
GIT_SIGNING_SECTION_RE = re.compile(r"^(?:gpg|include|includeif|user|commit|tag)(?:\..*)?$", re.IGNORECASE)
GIT_CONFIG_READ_FLAGS = ("--get", "--get-all", "--get-regexp", "--get-urlmatch", "--get-color", "--get-colorbool", "-l", "--list")
GIT_CONFIG_WRITE_FLAGS = ("--add", "--replace-all", "--unset", "--unset-all", "--append")
GIT_CONFIG_SECTION_OPS = ("--remove-section", "--rename-section")
GIT_CONFIG_EDIT_FLAGS = ("-e", "--edit")
GIT_CONFIG_OPTS_WITH_ARG = ("-f", "--file", "--blob", "-t", "--type", "--default", "--comment", "--value", "--url")
# git 2.46+ spells the same operations as subcommands.
GIT_CONFIG_VERBS = {"get": "read", "list": "read", "set": "write", "unset": "write", "edit": "edit", "remove-section": "section", "rename-section": "section"}
# git's system config: Homebrew's (owner-writable on an Intel Mac) and the distribution's.
SYSTEM_GITCONFIGS = ("/usr/local/etc/gitconfig", "/opt/homebrew/etc/gitconfig", "/etc/gitconfig")
SIGNING_TOOL = "configure_commit_signing.py"
SIGNING_TOOL_WRITES = ("--apply", "--remove")
DEFAULTS_VERBS = ("write", "delete", "rename", "import")
SECURITY_VERBS = ("find-generic-password", "find-internet-password", "dump-keychain", "export")
GH_API_LONG = ("method", "field", "raw-field", "input")
GH_API_SHORT = "XfF"
GH_API_VALUE_SHORT = "Hqpt"
GH_METHOD_OVERRIDE = "method-override"
GH_PR_ACTIONS = ("create", "new", "merge")
GH_PR_OPTS_WITH_ARG = ("-R", "--repo")
GH_KEY_ADMIN = {"repo": ("deploy-key",), "ssh-key": ("add", "delete"), "gpg-key": ("add", "delete")}
GH_ALIAS_ACTIONS = ("set", "import")

SHELLS = ("bash", "sh", "zsh", "dash", "ksh", "mksh", "fish")
SHELL_OPTS_WITH_ARG = ("-o", "-O", "+o", "+O", "--rcfile", "--init-file")
INTERPRETER_RE = re.compile(r"^(?:python[0-9.]*|pypy[0-9.]*|perl[0-9.]*|ruby|node|nodejs|osascript|php|lua|tclsh|Rscript)$", re.IGNORECASE)
INTERPRETER_CODE_FLAGS = ("-c", "-e", "-E", "-r", "--eval", "-p", "--print")
FIND_EXEC_FLAGS = ("-exec", "-execdir", "-ok", "-okdir")
RECURSIVE_ALWAYS = ("rg", "ag", "ack", "find", "fd", "tar", "zip", "rsync", "ditto", "pax")
RECURSIVE_WITH_FLAG = ("grep", "egrep", "fgrep", "ggrep", "cp", "scp")
KEYWORDS = ("!", "if", "then", "else", "elif", "do", "while", "until", "coproc", "{", "}")
# wrapper -> (options that take a separate value, positional words consumed before the command)
WRAPPERS = {
    "command": ((), 0),
    "builtin": ((), 0),
    "exec": (("-a",), 0),
    "env": (("-u", "--unset", "-C", "--chdir", "-P", "-S", "--split-string"), 0),
    "nohup": ((), 0),
    "time": (("-f", "-o", "--format", "--output"), 0),
    "nice": (("-n", "--adjustment"), 0),
    "timeout": (("-s", "--signal", "-k", "--kill-after"), 1),
    "gtimeout": (("-s", "--signal", "-k", "--kill-after"), 1),
    "stdbuf": (("-i", "-o", "-e", "--input", "--output", "--error"), 0),
    "xargs": (("-I", "-J", "-L", "-n", "-P", "-R", "-S", "-s", "-E", "-a", "-d", "--max-args", "--max-procs", "--max-lines", "--max-chars", "--arg-file", "--delimiter", "--eof"), 0),
    "parallel": (("-j", "--jobs", "-S", "--sshlogin"), 0),
    "caffeinate": (("-t", "-w"), 0),
    "arch": (("-arch",), 0),
    "watch": (("-n", "--interval"), 0),
    "flock": (("-w", "--timeout", "-E", "--conflict-exit-code"), 1),
    "chronic": ((), 0),
    "unbuffer": ((), 0),
    "noglob": ((), 0),
    "nocorrect": ((), 0),
}
STDIN_ARG_WRAPPERS = ("xargs", "parallel")
GLOB_CHARS = "*?["

_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?\+?=")
_NAME_START = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_")
_NAME_CHARS = _NAME_START | frozenset("0123456789")
_SPECIAL_PARAMS = frozenset("@*#?-$!0123456789")
_CRED_COMPONENT_RE = re.compile(r"(?<![A-Za-z0-9._-])\.(?:ssh|gnupg)(?![A-Za-z0-9._-])", re.IGNORECASE)
_HOME_SPELLING_RE = re.compile(r"^(?:~[A-Za-z0-9._-]*|\$HOME(?![A-Za-z0-9_])|\$\{HOME(?:[^A-Za-z0-9_}][^}]*)?\})(?=/|$)")
_HOME_LIKE_RE = re.compile(r"^/+(?:(?:Users|home)/+[^/]+|(?:private/+)?var/+root|root)(?=/|$)", re.IGNORECASE)
_STRING_LITERAL_RE = re.compile(r"'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\"")
_MENTION_RE = re.compile(r"[a-z][a-z0-9_.-]*")
# D11 item 1 sets GIT_CONFIG_COUNT / KEY_n / VALUE_n so agent commits are unsigned; unsetting or
# overriding them re-enables signing with the owner's YubiKey.
_GIT_ENV_NAMES = r"GIT_CONFIG_(?:COUNT|KEY_\w*|VALUE_\w*|PARAMETERS)\b"
_GIT_ENV_CHANGE_RE = re.compile(r"\bunset\b[^;&|\n]*\b%s|\b%s\s*\+?=|(?:^|\s)(?:-u\s*|--unset[= ]\s*)%s" % (_GIT_ENV_NAMES, _GIT_ENV_NAMES[:-2], _GIT_ENV_NAMES))
_ANSI_SIMPLE = {"a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\", "'": "'", '"': '"', "?": "?"}


class MalformedInput(Exception):
    """The payload cannot be evaluated; the guard fails closed (exit 2)."""


class Hit(object):
    """A rule that matched, with the word or flag that made it match."""

    __slots__ = ("rule_id", "evidence")

    def __init__(self, rule_id: str, evidence: str) -> None:
        self.rule_id = rule_id
        self.evidence = evidence


# ---------------------------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------------------------
def _unique(items: list) -> list:
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def _basename(text: str) -> str:
    stripped = text.rstrip("/")
    return (stripped.rsplit("/", 1)[-1] if stripped else text).casefold()


def _is_computed(text: str) -> bool:
    return "$" in text or "`" in text


def _has_glob(text: str) -> bool:
    return any(ch in text for ch in GLOB_CHARS) or ("{" in text and ("," in text or ".." in text))


def brace_expand(text: str, limit: int = MAX_BRACE_ALTERNATIVES) -> list:
    """Expand bash brace lists and small ranges ({a,b}, {1..3}); ``${...}`` is left alone. Capped."""
    done = []
    pending = [text]
    while pending and len(done) + len(pending) <= limit:
        cur = pending.pop(0)
        span = _first_brace_group(cur)
        if span is None:
            done.append(cur)
            continue
        start, end, alternatives = span
        pending.extend(cur[:start] + alt + cur[end + 1 :] for alt in alternatives)
    return _unique([text] + done + pending)[: limit + 1]


def _first_brace_group(text: str):
    n = len(text)
    for i in range(n):
        if text[i] != "{" or (i > 0 and text[i - 1] == "$"):
            continue
        depth = 0
        parts = []
        last = i + 1
        for j in range(i, n):
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    parts.append(text[last:j])
                    if len(parts) > 1:
                        return i, j, parts
                    rng = re.match(r"^(-?\d+|[A-Za-z])\.\.(-?\d+|[A-Za-z])$", parts[0])
                    if rng:
                        return i, j, _brace_range(rng.group(1), rng.group(2))
                    break
            elif ch == "," and depth == 1:
                parts.append(text[last:j])
                last = j + 1
    return None


def _brace_range(lo: str, hi: str) -> list:
    if lo.lstrip("-").isdigit() and hi.lstrip("-").isdigit():
        a, b = int(lo), int(hi)
        step = 1 if b >= a else -1
        return [str(v) for v in range(a, b + step, step)[:MAX_BRACE_ALTERNATIVES]]  # range slices lazily
    if len(lo) == 1 and len(hi) == 1 and lo.isalpha() and hi.isalpha():
        a, b = ord(lo), ord(hi)
        step = 1 if b >= a else -1
        return [chr(v) for v in range(a, b + step, step)[:MAX_BRACE_ALTERNATIVES]]
    return ["%s..%s" % (lo, hi)]


def component_matches(pattern: str, literal: str) -> bool:
    """True when one path component (a literal or a glob, braces allowed) can match ``literal``."""
    target = literal.casefold()
    if not _has_glob(pattern):
        return pattern.casefold() == target
    for alt in brace_expand(pattern):
        if fnmatch.fnmatchcase(target, alt.replace("[^", "[!").casefold()):
            return True
    return False


def _glob_literal_chars(pattern: str) -> str:
    """The literal characters of a glob component, outside bracket expressions and brace syntax."""
    out = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "[":
            close = pattern.find("]", i + 2)
            i = len(pattern) if close < 0 else close + 1
            continue
        if ch not in "*?{},":
            out.append(ch)
        i += 1
    return "".join(out)


def _components(path: str) -> list:
    return [c for c in path.split("/") if c not in ("", ".")]


def _inside(path: str, directory: str) -> bool:
    """Case-insensitive, component-aware containment: ``path`` equal to or below ``directory``."""
    p = path.casefold().rstrip("/") or "/"
    d = directory.casefold().rstrip("/") or "/"
    if d == "/":
        return True
    return p == d or p.startswith(d + "/")


def _has_cred_component(path: str) -> bool:
    return any(c.casefold() in CRED_DIR_NAMES for c in path.split("/"))


def could_reach(pattern_parts: list, target_parts: list) -> bool:
    """True when a path at or below ``target_parts`` can match the glob ``pattern_parts`` (``**`` spans)."""
    memo = {}

    def walk(i: int, j: int) -> bool:
        key = (i, j)
        if key not in memo:
            if j == len(target_parts):
                memo[key] = True
            elif i == len(pattern_parts):
                memo[key] = False
            elif pattern_parts[i] == "**":
                memo[key] = walk(i + 1, j) or walk(i, j + 1)
            elif _is_computed(pattern_parts[i]) or component_matches(pattern_parts[i], target_parts[j]):
                memo[key] = walk(i + 1, j + 1)
            else:
                memo[key] = False
        return memo[key]

    return walk(0, 0)


# ---------------------------------------------------------------------------------------------
# The shell lexer: words and simple commands, the way bash splits them
# ---------------------------------------------------------------------------------------------
class Word(object):
    """One shell word after quote removal. Expansions ($X, ${..}, $(..), `..`) stay verbatim."""

    __slots__ = ("text", "computed", "quoted", "kind")

    def __init__(self, text: str, computed: bool, quoted: bool, kind: str) -> None:
        self.text = text
        self.computed = computed
        self.quoted = quoted
        self.kind = kind  # arg | target | herestring | heredoc | heredoc-strip


class Segment(object):
    """One simple command: its words, its pipeline group, and any here-document bodies."""

    __slots__ = ("words", "group", "piped", "heredocs")

    def __init__(self, group: int, piped: bool) -> None:
        self.words = []
        self.group = group
        self.piped = piped  # reads the previous segment's stdout
        self.heredocs = []  # (body, expanded)

    def args(self) -> list:
        return [w for w in self.words if w.kind == "arg"]

    def herestrings(self) -> list:
        return [w.text for w in self.words if w.kind == "herestring"]


def _skip_backtick(s: str, j: int) -> int:
    """Index just past the backtick that closes one opened before ``j`` (len(s) if none)."""
    n = len(s)
    while j < n:
        if s[j] == "\\":
            j += 2
            continue
        if s[j] == "`":
            return j + 1
        j += 1
    return n


def _backtick_body(s: str, j: int) -> tuple:
    end = _skip_backtick(s, j)
    closed = j < end <= len(s) and s[end - 1] == "`"
    raw = s[j : end - 1] if closed else s[j:end]
    return re.sub(r"\\([`\\$])", r"\1", raw), end


def _skip_double(s: str, j: int) -> int:
    """Index just past the double quote that closes one opened before ``j`` (len(s) if none)."""
    n = len(s)
    while j < n:
        ch = s[j]
        if ch == "\\":
            j += 2
            continue
        if ch == '"':
            return j + 1
        if ch == "`":
            j = _skip_backtick(s, j + 1)
            continue
        if ch == "$" and s[j + 1 : j + 2] in ("(", "{"):
            j = _find_close(s, j + 2, s[j + 1]) + 1
            continue
        j += 1
    return n


def _find_close(s: str, j: int, opener: str) -> int:
    """Index of the bracket that balances an ``opener`` already open before ``j`` (quote-aware)."""
    closer = ")" if opener == "(" else "}"
    depth = 1
    n = len(s)
    while j < n:
        ch = s[j]
        if ch == "\\":
            j += 2
            continue
        if ch == "'":
            k = s.find("'", j + 1)
            j = n if k < 0 else k + 1
            continue
        if ch == '"':
            j = _skip_double(s, j + 1)
            continue
        if ch == "`":
            j = _skip_backtick(s, j + 1)
            continue
        if ch == "$" and s[j + 1 : j + 2] in ("(", "{"):
            j = _find_close(s, j + 2, s[j + 1]) + 1
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return n


def _ansi_c(s: str, j: int) -> tuple:
    """Decode a ``$'...'`` body that starts at ``j``; returns (text, index past the closing quote)."""
    out = []
    n = len(s)
    while j < n:
        ch = s[j]
        if ch == "'":
            return "".join(out), j + 1
        if ch == "\\" and j + 1 < n:
            esc = s[j + 1]
            if esc in _ANSI_SIMPLE:
                out.append(_ANSI_SIMPLE[esc])
                j += 2
                continue
            if esc == "c" and j + 2 < n:
                out.append(chr(ord(s[j + 2]) & 0x1F))
                j += 3
                continue
            spec = {"x": (r"[0-9A-Fa-f]{1,2}", 16, 2), "u": (r"[0-9A-Fa-f]{1,4}", 16, 2), "U": (r"[0-9A-Fa-f]{1,8}", 16, 2)}.get(esc)
            if spec is None and esc in "01234567":
                spec = (r"[0-7]{1,3}", 8, 1)
            m = re.match(spec[0], s[j + spec[2] :]) if spec else None
            if m:
                value = int(m.group(0), spec[1]) & (0xFF if spec[1] == 8 else 0xFFFFFFFF)
                out.append(chr(value) if value <= 0x10FFFF else "?")
                j += spec[2] + m.end()
                continue
            out.append("\\" + esc)
            j += 2
            continue
        out.append(ch)
        j += 1
    return "".join(out), n


def substitutions(text: str) -> list:
    """The bodies of ``$( )`` and backtick substitutions inside text that is otherwise data."""
    out = []
    j = 0
    n = len(text)
    while j < n:
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if ch == "$" and text[j + 1 : j + 2] == "(":
            end = _find_close(text, j + 2, "(")
            out.append(text[j + 2 : end])
            j = end + 1
            continue
        if ch == "`":
            body, j = _backtick_body(text, j + 1)
            out.append(body)
            continue
        j += 1
    return out


_REDIRECT_OPS = (("<<<", "herestring"), ("<<-", "heredoc-strip"), ("<<", "heredoc"), ("&>>", "target"), ("&>", "target"), (">>", "target"), (">|", "target"), ("<>", "target"), (">&", "dup"), ("<&", "dup"), (">", "target"), ("<", "target"))


class Lexer(object):
    """Split a command string into simple commands (``Segment``) and nested command strings."""

    def __init__(self, text: str) -> None:
        self.s = text
        self.n = len(text)
        self.i = 0
        self.segments = []
        self.nested = []
        self.group = 0
        self.seg = Segment(0, False)
        self.buf = None
        self.computed = False
        self.quoted = False
        self.pending_kind = None
        self.pending_heredocs = []

    def _open_word(self) -> None:
        if self.buf is None:
            self.buf = []
            self.computed = False
            self.quoted = False

    def _add(self, text: str, computed: bool = False) -> None:
        self._open_word()
        self.buf.append(text)
        if computed:
            self.computed = True

    def _end_word(self) -> None:
        if self.buf is None:
            return
        word = Word("".join(self.buf), self.computed, self.quoted, self.pending_kind or "arg")
        self.buf = None
        self.pending_kind = None
        if word.kind in ("heredoc", "heredoc-strip"):
            self.pending_heredocs.append((word.text, word.kind == "heredoc-strip", word.quoted, self.seg))
        self.seg.words.append(word)

    def _end_segment(self, sep: str) -> None:
        self._end_word()
        self.pending_kind = None
        if self.seg.words:
            self.segments.append(self.seg)
        if sep == "|":
            self.seg = Segment(self.group, True)
        else:
            self.group += 1
            self.seg = Segment(self.group, False)

    def run(self) -> "Lexer":
        s = self.s
        while self.i < self.n:
            ch = s[self.i]
            nxt = s[self.i + 1 : self.i + 2]
            if ch == "\\":
                if nxt == "\n":
                    self.i += 2
                    continue
                self._open_word()
                self.quoted = True
                self._add(nxt or "\\")
                self.i += 2
            elif ch == "'":
                k = s.find("'", self.i + 1)
                self._open_word()
                self.quoted = True
                self._add(s[self.i + 1 :] if k < 0 else s[self.i + 1 : k])
                self.i = self.n if k < 0 else k + 1
            elif ch == '"':
                self._open_word()
                self.quoted = True
                self.i = self._double(self.i + 1)
            elif ch == "$":
                self.i = self._dollar(self.i, False)
            elif ch == "`":
                self.i = self._backtick(self.i)
            elif ch in " \t\r":
                self._end_word()
                self.i += 1
            elif ch == "\n":
                self._end_segment("\n")
                self.i += 1
                if self.pending_heredocs:
                    self._read_heredocs()
            elif ch == "#" and self.buf is None:
                k = s.find("\n", self.i)
                self.i = self.n if k < 0 else k
            elif ch in "<>" and nxt == "(":
                end = _find_close(s, self.i + 2, "(")
                self.nested.append(s[self.i + 2 : end])
                self._add(s[self.i : end + 1], computed=True)
                self.i = end + 1
            elif ch in "<>" or (ch == "&" and nxt == ">"):
                self.i = self._redirect(self.i)
            elif ch == "&":
                self._end_segment("&")
                self.i += 2 if nxt == "&" else 1
            elif ch == "|":
                self._end_segment("||" if nxt == "|" else "|")
                self.i += 2 if nxt in ("|", "&") else 1
            elif ch == ";":
                self._end_segment(";")
                self.i += 1
                while self.i < self.n and s[self.i] in ";&":
                    self.i += 1
            elif ch in "()":
                self._end_segment(ch)
                self.i += 1
            elif self.buf is None and ((ch == "{" and nxt in ("", " ", "\t", "\n")) or (ch == "}" and nxt in ("", " ", "\t", "\n", ";", "&", "|", ")"))):
                self._end_segment(ch)
                self.i += 1
            else:
                self._add(ch)
                self.i += 1
        self._end_segment("\n")
        return self

    def _double(self, j: int) -> int:
        s = self.s
        while j < self.n:
            ch = s[j]
            if ch == '"':
                return j + 1
            if ch == "\\" and j + 1 < self.n:
                nxt = s[j + 1]
                if nxt == "\n":
                    j += 2
                elif nxt in '$`"\\':
                    self._add(nxt)
                    j += 2
                else:
                    self._add("\\")
                    j += 1
            elif ch == "$":
                j = self._dollar(j, True)
            elif ch == "`":
                j = self._backtick(j)
            else:
                self._add(ch)
                j += 1
        return self.n

    def _dollar(self, i: int, in_dq: bool) -> int:
        s = self.s
        nxt = s[i + 1 : i + 2]
        if nxt == "'" and not in_dq:
            text, end = _ansi_c(s, i + 2)
            self._open_word()
            self.quoted = True
            self._add(text)
            return end
        if nxt == '"' and not in_dq:
            self._open_word()
            self.quoted = True
            return self._double(i + 2)
        if nxt in ("(", "{"):
            end = _find_close(s, i + 2, nxt)
            inner = s[i + 2 : end]
            if nxt == "(":
                self.nested.append(inner)
            else:
                self.nested.extend(substitutions(inner))
            self._add(s[i : end + 1], computed=True)
            return end + 1
        if nxt and nxt in _NAME_START:
            j = i + 1
            while j < self.n and s[j] in _NAME_CHARS:
                j += 1
            self._add(s[i:j], computed=True)
            return j
        if nxt and nxt in _SPECIAL_PARAMS:
            self._add(s[i : i + 2], computed=True)
            return i + 2
        self._add("$")
        return i + 1

    def _backtick(self, i: int) -> int:
        body, end = _backtick_body(self.s, i + 1)
        self.nested.append(body)
        self._add(self.s[i:end], computed=True)
        return end

    def _redirect(self, i: int) -> int:
        s = self.s
        if self.buf is not None:
            cur = "".join(self.buf)
            if not self.computed and not self.quoted and (cur.isdigit() or re.match(r"^\{[A-Za-z_][A-Za-z0-9_]*\}$", cur)):
                self.buf = None  # the fd number of the redirection, not a word
            else:
                self._end_word()
        kind = "target"
        for op, op_kind in _REDIRECT_OPS:
            if s.startswith(op, i):
                i += len(op)
                kind = op_kind
                break
        if kind == "dup":
            m = re.match(r"[ \t]*(?:\d+-?|-)(?![^\s;&|<>()])", s[i:])
            if m:
                return i + m.end()
            kind = "target"
        self.pending_kind = kind
        return i

    def _read_heredocs(self) -> None:
        s = self.s
        for delim, strip, quoted, seg in self.pending_heredocs:
            lines = []
            while self.i < self.n:
                k = s.find("\n", self.i)
                line = s[self.i :] if k < 0 else s[self.i : k]
                self.i = self.n if k < 0 else k + 1
                if (line.lstrip("\t") if strip else line) == delim:
                    break
                lines.append(line)
            seg.heredocs.append(("\n".join(lines), not quoted))
        self.pending_heredocs = []


# ---------------------------------------------------------------------------------------------
# Command resolution
# ---------------------------------------------------------------------------------------------
class Resolved(object):
    """Where the command word of a simple command is, which wrappers led to it, and side strings."""

    __slots__ = ("index", "wrappers", "strings", "env_cleared")

    def __init__(self) -> None:
        self.index = None
        self.wrappers = []
        self.strings = []  # command strings a wrapper runs itself (env -S, watch)
        self.env_cleared = False  # env -i / env - : D11's GIT_CONFIG_* variables are gone


def resolve_command(args: list, start: int = 0) -> Resolved:
    """Skip ``NAME=value`` prefixes, reserved words and wrappers to reach the command word."""
    res = Resolved()
    i = start
    n = len(args)
    while i < n:
        text = args[i].text
        if _ASSIGN_RE.match(text) or text in KEYWORDS:
            i += 1
            continue
        name = _basename(text)
        spec = WRAPPERS.get(name)
        if spec is None:
            res.index = i
            return res
        res.wrappers.append(name)
        opts_with_arg, positional = spec
        i += 1
        while i < n:
            t = args[i].text
            if t == "--":
                i += 1
                break
            if name == "env" and (_ASSIGN_RE.match(t) or t == "-"):
                res.env_cleared = res.env_cleared or t == "-"
                i += 1
                continue
            if not (t.startswith("-") and len(t) > 1):
                break
            opt = t.split("=", 1)[0]
            if name == "env":
                if opt in ("-i", "--ignore-environment") or (not opt.startswith("--") and "i" in opt[1:]):
                    res.env_cleared = True
                if opt in ("-S", "--split-string"):
                    res.strings.append(t.split("=", 1)[1] if "=" in t else (args[i + 1].text if i + 1 < n else ""))
                elif t.startswith("-S") and len(t) > 2:
                    res.strings.append(t[2:])
            i += 2 if (opt in opts_with_arg and "=" not in t) else 1
        if name == "watch":
            res.strings.append(" ".join(w.text for w in args[i:]))
            return res
        i += positional
    return res


def _gh_action(words: list, opts_with_arg: tuple):
    """The first non-flag word, skipping the values of ``opts_with_arg``."""
    skip = False
    for word in words:
        if skip:
            skip = False
            continue
        if word.text.startswith("-"):
            skip = word.text in opts_with_arg
            continue
        return word
    return None


def _gpg_option(name: str, table: tuple) -> bool:
    """GnuPG accepts unambiguous abbreviations of long options, so a long-enough prefix counts."""
    return any(opt == name or (len(name) >= GPG_MIN_ABBREV and opt.startswith(name)) for opt in table)


def _strip_prefix_ci(text: str, prefix: str):
    prefix = prefix.rstrip("/")
    if not prefix or len(text) < len(prefix) or text[: len(prefix)].casefold() != prefix.casefold():
        return None
    tail = text[len(prefix) :]
    return tail if (not tail or tail.startswith("/")) else None


def _claude_protected(rest: list, mutating: bool) -> bool:
    """``rest`` (components below a home) names its settings files or hooks/, or -- for a command
    that moves, removes or re-permissions things -- the ~/.claude directory itself."""
    if not rest or not component_matches(rest[0], CLAUDE_DIR_NAME):
        return False
    if len(rest) == 1:
        return mutating
    return _is_computed(rest[1]) or any(component_matches(rest[1], child) for child in CLAUDE_PROTECTED_CHILDREN)


def _token_at(text: str, pos: int) -> str:
    start = pos
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    end = pos
    while end < len(text) and not text[end].isspace():
        end += 1
    return text[start:end]


# ---------------------------------------------------------------------------------------------
# Bash rules
# ---------------------------------------------------------------------------------------------
class BashAnalyzer(object):
    """Apply the Bash rules to one command string and to every command string nested in it."""

    def __init__(self, ctx: "Context") -> None:
        self.ctx = ctx
        self.hits = []
        self.all_words = []
        self.opaque = False

    def hit(self, rule_id: str, evidence: str) -> None:
        self.hits.append(Hit(rule_id, evidence))

    def analyze(self, command: str) -> list:
        self._scan(command, 0, [self.ctx.cwd] if self.ctx.cwd else [])
        if self.opaque:
            self._opaque_fallback()
        return self.hits

    def _scan(self, text: str, depth: int, bases: list) -> None:
        if depth > MAX_DEPTH:
            raise MalformedInput("the command nests shell -c / eval / substitutions more than %d deep and cannot be analysed" % MAX_DEPTH)
        self._raw(text)
        lexer = Lexer(text).run()
        bases = self._cd_bases(lexer.segments, bases)
        for seg in lexer.segments:
            self._segment(seg, lexer.segments, depth, bases)
            for body, expanded in seg.heredocs:
                if expanded:
                    for inner in substitutions(body):
                        self._scan(inner, depth + 1, bases)
        for inner in lexer.nested:
            self._scan(inner, depth + 1, bases)

    def _raw(self, text: str) -> None:
        m = _CRED_COMPONENT_RE.search(text)
        if m:
            self.hit("CRED-PATH-BASH", _token_at(text, m.start()))
        m = self.ctx.self_protect_re().search(text)
        if m:
            self.hit("SELF-PROTECT-BASH", m.group(0))
        if DISABLE_HOOKS_KEY in text.casefold():
            self.hit("SELF-PROTECT-BASH", "disableAllHooks")
        m = _GIT_ENV_CHANGE_RE.search(text)
        if m:
            self.hit("GPG-SIGN", m.group(0).strip())
        m = self.ctx.signing_re().search(text)
        if m:
            self.hit("GIT-SIGNING-CONFIG", m.group(0))

    def _segment(self, seg: Segment, segments: list, depth: int, bases: list) -> None:
        args = seg.args()
        res = resolve_command(args)
        mutating = res.index is not None and _basename(args[res.index].text) in MUTATING_COMMANDS
        for word in seg.words:
            self.all_words.append(word.text)
            self._path_word(word.text, bases, mutating or word.kind == "target")
            # The lexed word has its quotes removed, so "$HOME"/.gitconfig reads as $HOME/.gitconfig here.
            m = self.ctx.signing_re().search(word.text)
            if m:
                self.hit("GIT-SIGNING-CONFIG", m.group(0))
        for extra in res.strings:
            self._scan(extra, depth + 1, bases)
        if res.index is not None:
            self._command(args[res.index], args[res.index + 1 :], res, seg, segments, depth, bases)
        for k, word in enumerate(args):
            if k != res.index and _basename(word.text) == "gh":
                self._check_gh(args[k + 1 :], seg, segments, res)
            if _basename(word.text) == SIGNING_TOOL:
                self._check_signing_tool(args[k + 1 :])

    def _command(self, word: Word, rest: list, res: Resolved, seg: Segment, segments: list, depth: int, bases: list) -> None:
        names = _unique([_basename(alt) for alt in brace_expand(word.text)])
        concrete = [name for name in names if not _is_computed(name)]
        if not concrete:
            self._opaque(word, rest, res, seg, segments, depth, bases)
            return
        for name in concrete:
            self._dispatch(name, rest, res, seg, segments, depth, bases)

    def _dispatch(self, name: str, rest: list, res: Resolved, seg: Segment, segments: list, depth: int, bases: list) -> None:
        if name in PRIV_COMMANDS:
            self.hit("PRIV-ESCALATION", name)
        elif name in SSH_AGENT_COMMANDS:
            self.hit("SSH-PROBE", name)
        elif name in CARD_TOOLS:
            self.hit("GPG-SECRET", name)
        elif name == "ssh":
            self._check_ssh(rest, dest_only=False)
        elif name in GPG_COMMANDS:
            self._check_gpg(rest, long_only=False)
        elif name in GPG_AGENT_COMMANDS:
            self._check_gpg_agent(rest, seg, segments)
        elif name == "git":
            self._check_git(rest, res.env_cleared)
        elif name == "defaults":
            self._check_verbs(rest, DEFAULTS_VERBS, "MACOS-DEFAULTS-WRITE", name)
        elif name == "security":
            self._check_verbs(rest, SECURITY_VERBS, "KEYCHAIN-DUMP", name)
        elif name == "gh":
            self._check_gh(rest, seg, segments, res)
        elif name in SHELLS:
            self._check_shell(rest, seg, segments, depth, bases)
        elif name == "eval":
            self._scan_generated(" ".join(w.text for w in rest), depth, bases)
        elif name in ("source", ".", INSTALLER_NAME):
            if name == INSTALLER_NAME:
                self._check_installer(rest)
            elif rest and _basename(rest[0].text) == INSTALLER_NAME:
                self._check_installer(rest[1:])
        elif name == "find":
            self._check_find_exec(rest, seg, segments, depth, bases)
        elif INTERPRETER_RE.match(name):
            self._check_interpreter(name, rest, depth, bases)
        if name in RECURSIVE_ALWAYS or name in RECURSIVE_WITH_FLAG:
            self._check_recursive(name, rest, bases)

    # -- a command word built at run time ------------------------------------------------
    def _opaque(self, word: Word, rest: list, res: Resolved, seg: Segment, segments: list, depth: int, bases: list) -> None:
        self.opaque = True
        guarded = PRIV_COMMANDS + SSH_AGENT_COMMANDS + CARD_TOOLS + GPG_COMMANDS + GPG_AGENT_COMMANDS + ("ssh", "git", "gh", "defaults", "security")
        for name in sorted(set(_MENTION_RE.findall(word.text.casefold()))):
            if name in guarded:
                self._dispatch(name, rest, res, seg, segments, depth, bases)
        self._check_gh(rest, seg, segments, res)
        self._check_git(rest, res.env_cleared)
        self._check_gpg(rest, long_only=True)
        self._check_ssh(rest, dest_only=True)

    def _opaque_fallback(self) -> None:
        for text in self.all_words:
            value = text.split("=", 1)[1] if _ASSIGN_RE.match(text) else text
            for alt in brace_expand(value):
                name = _basename(alt)
                if name in PRIV_COMMANDS:
                    self.hit("PRIV-ESCALATION", text)
                elif name in SSH_AGENT_COMMANDS:
                    self.hit("SSH-PROBE", text)
                elif name in CARD_TOOLS:
                    self.hit("GPG-SECRET", text)

    # -- per-tool checks -------------------------------------------------------------------
    def _check_ssh(self, rest: list, dest_only: bool) -> None:
        dest = None
        config_only = False
        i = 0
        while i < len(rest):
            text = rest[i].text
            if text.startswith("-") and len(text) > 1 and not text.startswith("--"):
                cluster = text[1:]
                for k, ch in enumerate(cluster):
                    if ch == "T" and not dest_only:
                        self.hit("SSH-PROBE", "ssh " + text)
                    if ch in "GV":
                        config_only = True
                    if ch in SSH_OPTS_WITH_ARG:
                        i += 1 if k == len(cluster) - 1 else 0
                        break
            elif dest is None:
                dest = text
            i += 1
        if dest is not None and not config_only and "github" in dest.casefold():
            self.hit("SSH-PROBE", "ssh " + dest)

    def _check_gpg(self, rest: list, long_only: bool) -> None:
        for word in rest:
            text = word.text
            if text.startswith("--") and len(text) > 2:
                name = text[2:].split("=", 1)[0].casefold()
                if name in GPG_EXACT_ALLOWED:
                    continue
                if _gpg_option(name, GPG_SECRET_LONG):
                    self.hit("GPG-SECRET", "gpg " + text)
                if _gpg_option(name, GPG_SIGN_LONG):
                    self.hit("GPG-SIGN", "gpg " + text)
            elif text.startswith("-") and len(text) > 1 and not long_only:
                for ch in text[1:]:
                    if ch in GPG_SECRET_SHORT:
                        self.hit("GPG-SECRET", "gpg " + text)
                    elif ch in GPG_SIGN_SHORT:
                        self.hit("GPG-SIGN", "gpg " + text)
                    if ch in GPG_SHORT_WITH_ARG:
                        break

    def _check_gpg_agent(self, rest: list, seg: Segment, segments: list) -> None:
        texts = [w.text for w in rest] + [body for body, _ in seg.heredocs] + seg.herestrings() + self._piped_texts(seg, segments)
        for text in texts:
            for line in text.splitlines() or [text]:
                first = line.strip().split(None, 1)
                if first and first[0].casefold() in GPG_AGENT_DENIED:
                    self.hit("GPG-SECRET", "gpg-connect-agent " + line.strip())

    def _check_git(self, rest: list, env_cleared: bool) -> None:
        sub = None
        i = 0
        while i < len(rest):
            text = rest[i].text
            i += 1
            if sub is None:
                if text == "-c" and i < len(rest):
                    key, _, value = rest[i].text.partition("=")
                    if "gpgsign" in key.casefold() and value.strip().casefold() not in ("false", "no", "off", "0"):
                        self.hit("GPG-SIGN", "git -c " + rest[i].text)
                    if GIT_DASH_C_SIGNING_RE.match(key.strip()):
                        self.hit("GIT-SIGNING-CONFIG", "git -c " + rest[i].text)
                    i += 1
                elif text == "--config-env" or text.startswith("--config-env="):
                    self.hit("GIT-SIGNING-CONFIG", "git " + (text if "=" in text or i >= len(rest) else text + " " + rest[i].text))
                    i += 0 if "=" in text else 1
                elif text in GIT_OPTS_WITH_ARG:
                    i += 1
                elif not text.startswith("-"):
                    sub = text.casefold()
                    if env_cleared and sub in GIT_SIGN_SUBCOMMANDS + ("tag",):
                        self.hit("GPG-SIGN", "env -i git " + sub)
                    if sub == "config":
                        self._check_git_config(rest[i:])
                        return
                continue
            short = text[1:] if text.startswith("-") and not text.startswith("--") else ""
            if sub in GIT_SIGN_SUBCOMMANDS:
                if text.startswith("--gpg-sign") or _cluster_has(short, "S", "mFCcXxp"):
                    self.hit("GPG-SIGN", "git %s %s" % (sub, text))
            elif sub == "tag":
                if text in ("--sign", "--local-user") or text.startswith(("--sign=", "--local-user=")) or _cluster_has(short, "su", "mFn"):
                    self.hit("GPG-SIGN", "git tag " + text)
            elif sub == "push" and (text == "--signed" or (text.startswith("--signed=") and text.split("=", 1)[1].casefold() not in ("false", "no", "off", "0"))):
                self.hit("GPG-SIGN", "git push " + text)

    def _check_git_config(self, rest: list) -> None:
        """A ``git config`` that writes a signing key, edits the file, or drops a signing section (K12)."""
        mode = "implicit"
        positionals = []
        i = 0
        while i < len(rest):
            text = rest[i].text
            lowered = text.casefold()
            i += 1
            if lowered in GIT_CONFIG_EDIT_FLAGS:
                self.hit("GIT-SIGNING-CONFIG", "git config " + text)
                return
            if lowered in GIT_CONFIG_READ_FLAGS:
                mode = "read" if mode == "implicit" else mode
            elif lowered in GIT_CONFIG_WRITE_FLAGS:
                mode = "write"
            elif lowered in GIT_CONFIG_SECTION_OPS:
                mode = "section"
            elif lowered in GIT_CONFIG_OPTS_WITH_ARG:
                i += 1
            elif not text.startswith("-"):
                positionals.append(text)
        if positionals and mode == "implicit" and positionals[0].casefold() in GIT_CONFIG_VERBS:
            mode = GIT_CONFIG_VERBS[positionals.pop(0).casefold()]
        if mode == "edit":
            self.hit("GIT-SIGNING-CONFIG", "git config edit")
        elif mode == "section":
            if positionals and GIT_SIGNING_SECTION_RE.match(positionals[0]):
                self.hit("GIT-SIGNING-CONFIG", "git config section " + positionals[0])
        elif positionals and GIT_SIGNING_KEY_RE.match(positionals[0]) and (mode == "write" or (mode == "implicit" and len(positionals) >= 2)):
            self.hit("GIT-SIGNING-CONFIG", "git config " + " ".join(positionals[:2]))

    def _check_signing_tool(self, rest: list) -> None:
        """util/configure_commit_signing.py writes the owner's signing configuration unless --dry-run (K12)."""
        texts = [w.text for w in rest]
        writes = [t for t in texts if t in SIGNING_TOOL_WRITES]
        if writes and "--dry-run" not in texts:
            self.hit("GIT-SIGNING-CONFIG", "%s %s" % (SIGNING_TOOL, writes[0]))

    def _check_verbs(self, rest: list, verbs: tuple, rule_id: str, name: str) -> None:
        for word in rest:
            if word.text.casefold() in verbs:
                self.hit(rule_id, "%s %s" % (name, word.text))

    def _check_gh(self, rest: list, seg: Segment, segments: list, res: Resolved) -> None:
        words = list(rest)
        if any(w in STDIN_ARG_WRAPPERS for w in res.wrappers):
            extra = seg.herestrings() + [body for body, _ in seg.heredocs] + self._piped_texts(seg, segments)
            words.extend(Word(t, False, False, "arg") for text in extra for t in text.split())
        sub_word = _gh_action(words, ())
        if sub_word is None:
            return
        opaque = sub_word.computed
        sub = sub_word.text.casefold()
        after = words[words.index(sub_word) + 1 :]
        if sub == "api" or opaque or any(w.text.casefold() == "api" for w in after):
            self._check_gh_api(words)
        if sub == "auth":
            self.hit("GH-AUTH", "gh auth")
        if sub == "pr" or opaque:
            action = _gh_action(after, GH_PR_OPTS_WITH_ARG)
            if action is not None and (action.text.casefold() in GH_PR_ACTIONS or (action.computed and not opaque)):
                self.hit("GH-PR-WRITE", "gh pr " + action.text)
        for key_sub, actions in GH_KEY_ADMIN.items():
            if sub == key_sub or opaque:
                action = _gh_action(after, GH_PR_OPTS_WITH_ARG)
                if action is not None and (action.text.casefold() in actions or (action.computed and not opaque)):
                    self.hit("GH-KEY-ADMIN", "gh %s %s" % (key_sub, action.text))
        if sub == "alias" or opaque:
            action = _gh_action(after, ())
            if action is not None and (action.text.casefold() in GH_ALIAS_ACTIONS or (action.computed and not opaque)):
                self.hit("GH-API-WRITE", "gh alias " + action.text)

    def _check_gh_api(self, words: list) -> None:
        for word in words:
            text = word.text
            if GH_METHOD_OVERRIDE in text.casefold():
                self.hit("GH-API-WRITE", "gh api " + text)
            if text.startswith("--"):
                if text[2:].split("=", 1)[0].casefold() in GH_API_LONG:
                    self.hit("GH-API-WRITE", "gh api " + text)
            elif text.startswith("-") and _cluster_has(text[1:], GH_API_SHORT, GH_API_VALUE_SHORT):
                self.hit("GH-API-WRITE", "gh api " + text)

    def _check_shell(self, rest: list, seg: Segment, segments: list, depth: int, bases: list) -> None:
        saw_c = saw_s = False
        operand = None
        i = 0
        while i < len(rest):
            text = rest[i].text
            if saw_c:
                self._scan_generated(text, depth, bases)
            elif text in SHELL_OPTS_WITH_ARG:
                i += 1
            elif text[:1] in ("-", "+") and len(text) > 1 and not text.startswith("--"):
                saw_c = saw_c or "c" in text[1:]
                saw_s = saw_s or "s" in text[1:]
            elif not text.startswith("--"):
                operand = rest[i]
                break
            i += 1
        if saw_c:
            return
        if operand is not None and _basename(operand.text) == INSTALLER_NAME:
            self._check_installer(rest[i + 1 :])
        if operand is None or operand.text == "-" or saw_s:
            for text in seg.herestrings() + [body for body, _ in seg.heredocs] + self._piped_texts(seg, segments):
                self._scan_generated(text, depth, bases)

    def _scan_generated(self, text: str, depth: int, bases: list) -> None:
        """Scan a string a shell will execute, and the words its substitutions print (``$(printf ..)``)."""
        self._scan(text, depth + 1, bases)
        for body in substitutions(text):
            for seg in Lexer(body).run().segments:
                for word in seg.args():
                    self._scan(word.text, depth + 2, bases)

    def _check_interpreter(self, name: str, rest: list, depth: int, bases: list) -> None:
        if name == "osascript" and any("administrator privileges" in w.text.casefold() for w in rest):
            self.hit("PRIV-ESCALATION", "osascript ... with administrator privileges")
        take = False
        for word in rest:
            code = None
            if take:
                code, take = word.text, False
            elif word.text in INTERPRETER_CODE_FLAGS:
                take = True
            elif name.startswith("python") and word.text.startswith("-c") and len(word.text) > 2:
                code = word.text[2:]
            if code:
                literals = [a or b for a, b in _STRING_LITERAL_RE.findall(code)][:200]
                for literal in literals:
                    if literal.strip():
                        self._scan(literal, depth + 1, bases)
                if len(literals) > 1:
                    self._scan(" ".join(literals), depth + 1, bases)

    def _check_find_exec(self, rest: list, seg: Segment, segments: list, depth: int, bases: list) -> None:
        for k, word in enumerate(rest):
            if word.text not in FIND_EXEC_FLAGS:
                continue
            sub = []
            for w in rest[k + 1 :]:
                if w.text in (";", "+"):
                    break
                sub.append(w)
            res = resolve_command(sub)
            for extra in res.strings:
                self._scan(extra, depth + 1, bases)
            if res.index is not None:
                self._command(sub[res.index], sub[res.index + 1 :], res, seg, segments, depth, bases)

    def _check_recursive(self, name: str, rest: list, bases: list) -> None:
        if name in RECURSIVE_WITH_FLAG:
            letters = "rRa" if name == "cp" else "rR"
            long_flags = ("--recursive", "--dereference-recursive", "--archive", "--directories=recurse")
            if not any(w.text in long_flags or (w.text.startswith("-") and not w.text.startswith("--") and any(ch in letters for ch in w.text[1:])) for w in rest):
                return
        operands = [w.text for w in rest if not w.text.startswith("-")]
        for text in operands:
            for alt in brace_expand(text):
                if self._home_or_above(alt, bases):
                    self.hit("CRED-PATH-BASH", "%s %s (a recursive tool rooted at home or above)" % (name, alt))
                    return
        implicit = (name not in ("find", "tar", "zip", "rsync", "ditto", "pax", "cp", "scp") and len(operands) <= 1) or (name == "find" and (not rest or rest[0].text.startswith(("-", "(", "!"))))
        if implicit and any(self._home_or_above(".", [b]) for b in bases):
            self.hit("CRED-PATH-BASH", "%s (it searches the current directory, which is home or above)" % name)

    def _check_installer(self, rest: list) -> None:
        if not any(w.text in INSTALLER_SAFE_FLAGS for w in rest):
            self.hit("SELF-PROTECT-BASH", INSTALLER_NAME)

    # -- path rules ------------------------------------------------------------------------
    def _path_word(self, text: str, bases: list, mutating: bool) -> None:
        for alt in brace_expand(text):
            if _CRED_COMPONENT_RE.search(alt):
                self.hit("CRED-PATH-BASH", alt)
                continue
            for comp in alt.split("/"):
                if comp.startswith(".") and _has_glob(comp) and _glob_literal_chars(comp).strip(".") and any(component_matches(comp, nm) for nm in CRED_DIR_NAMES):
                    self.hit("CRED-PATH-BASH", alt)
            for rest in self._home_rests(alt, bases):
                if not rest:
                    continue
                head = rest[0]
                if (head.startswith(".") and _has_glob(head) and any(component_matches(head, nm) for nm in CRED_DIR_NAMES)) or _is_computed(head):
                    self.hit("CRED-PATH-BASH", alt)
                if _claude_protected(rest, mutating):
                    self.hit("SELF-PROTECT-BASH", alt)
            # an absolute or cwd-relative word, against the resolved directories (a symlinked ~/.ssh)
            if alt.startswith("/"):
                readings = [os.path.normpath(alt)]
            elif alt and not alt.startswith(("~", "$")):
                readings = [os.path.normpath(os.path.join(b, alt)) for b in bases]
            else:
                readings = []
            if "/" in alt and not _is_computed(alt):
                readings = _unique(readings + [os.path.realpath(r) for r in readings])
            if any(_has_cred_component(r) or any(_inside(r, d) for d in self.ctx.cred_dirs) for r in readings):
                self.hit("CRED-PATH-BASH", alt)
            if self.ctx.is_protected(readings):
                self.hit("SELF-PROTECT-BASH", alt)

    def _home_rests(self, text: str, bases: list) -> list:
        """Each reading of ``text`` as a path below a home directory, as a component list."""
        rests = []
        m = _HOME_SPELLING_RE.match(text) or _HOME_LIKE_RE.match(text)
        if m:
            rests.append(_components(text[m.end() :]))
        for home in self.ctx.home_variants:
            tail = _strip_prefix_ci(text, home)
            if tail is not None:
                rests.append(_components(tail))
        first, sep, remainder = text.partition("/")
        if sep and first and _is_computed(first) and not m:
            rests.append(_components(remainder))
        if text and not text.startswith(("/", "~", "$")):
            for base in bases:
                joined = os.path.normpath(os.path.join(base, text))
                for home in self.ctx.home_variants:
                    tail = _strip_prefix_ci(joined, home)
                    if tail is not None:
                        rests.append(_components(tail))
        return rests

    def _home_or_above(self, text: str, bases: list) -> bool:
        if any(not rest for rest in self._home_rests(text, bases)):
            return True
        if text.startswith("/"):
            candidates = [os.path.normpath(text)]
        elif text.startswith(("~", "$")):
            candidates = []
        else:
            candidates = [os.path.normpath(os.path.join(b, text)) for b in bases]
        return any(_inside(home, c) for c in candidates for home in self.ctx.home_variants)

    def _cd_bases(self, segments: list, bases: list) -> list:
        """Directories a relative word may be relative to: the cwd plus every ``cd`` target."""
        out = list(bases)
        for seg in segments:
            args = seg.args()
            res = resolve_command(args)
            if res.index is None or _basename(args[res.index].text) not in ("cd", "pushd"):
                continue
            targets = [w for w in args[res.index + 1 :] if w.text == "-" or not w.text.startswith("-")]
            target = targets[0] if targets else None
            if target is None or target.text == "-" or target.computed:
                out.extend(self.ctx.home_variants)
            if target is None:
                continue
            for rest in self._home_rests(target.text, []):
                out.extend(os.path.join(home, *rest) for home in self.ctx.home_variants)
            if target.text.startswith("/"):
                out.append(os.path.normpath(target.text))
            elif not target.text.startswith(("~", "$")):
                out.extend(os.path.normpath(os.path.join(b, target.text)) for b in list(out))
        return _unique(out)

    def _piped_texts(self, seg: Segment, segments: list) -> list:
        """The words and here-documents of the segments piped into ``seg``."""
        out = []
        idx = next((k for k, s in enumerate(segments) if s is seg), -1)
        k = idx - 1
        current = seg
        while k >= 0 and current.piped and segments[k].group == seg.group:
            prev = segments[k]
            out.extend(w.text for w in prev.words if w.kind in ("arg", "herestring"))
            out.extend(body for body, _ in prev.heredocs)
            current = prev
            k -= 1
        return out


def _cluster_has(cluster: str, wanted: str, value_letters: str) -> bool:
    """Walk a short-option cluster: True if a ``wanted`` letter appears before a value-taking one."""
    for ch in cluster:
        if ch in wanted:
            return True
        if ch in value_letters:
            return False
    return False


# ---------------------------------------------------------------------------------------------
# Home directories and the protected paths below them
# ---------------------------------------------------------------------------------------------
def _password_home() -> str:
    try:
        import pwd

        return pwd.getpwuid(os.getuid()).pw_dir or ""
    except (ImportError, KeyError, AttributeError, OSError):
        return ""


def _is_installed_copy(pw_home: str) -> bool:
    """The copy under <home>/.claude/hooks/ ignores the test override (it is the live guard)."""
    hooks = os.path.realpath(os.path.join(pw_home or os.path.expanduser("~"), CLAUDE_DIR_NAME, "hooks"))
    return _inside(os.path.realpath(os.path.abspath(__file__)), hooks)


def resolve_homes() -> list:
    """expanduser('~') plus the password-database home; JUNIPER_GUARD_HOME replaces both in tests."""
    pw_home = _password_home()
    override = os.environ.get(HOME_OVERRIDE_ENV, "")
    if override and not _is_installed_copy(pw_home):
        return [override]
    return _unique([h for h in (os.path.expanduser("~"), pw_home) if h])


class Context(object):
    """The homes in force, the cwd, and the protected paths below the homes (literal and real)."""

    def __init__(self, homes: list, cwd) -> None:
        self.homes = _unique([os.path.normpath(os.path.abspath(h)) for h in homes if h])
        self.cwd = cwd if isinstance(cwd, str) and cwd else None
        self.home_variants = _unique(self.homes + [os.path.realpath(h) for h in self.homes])
        self.cred_dirs = _with_real([os.path.join(h, name) for h in self.home_variants for name in CRED_DIR_NAMES])
        claude_dirs = _with_real([os.path.join(h, CLAUDE_DIR_NAME) for h in self.home_variants])
        self.protected_files = _with_real([os.path.join(d, name) for d in claude_dirs for name in CLAUDE_SETTINGS_FILES])
        self.protected_dirs = _with_real([os.path.join(d, "hooks") for d in claude_dirs])
        self.signing_files = _with_real([os.path.join(h, ".gitconfig") for h in self.home_variants] + list(SYSTEM_GITCONFIGS))
        self.signing_dirs = _with_real([os.path.join(h, ".config", "git") for h in self.home_variants])
        self._self_re = None
        self._signing_re = None

    def _home_spellings(self) -> str:
        literal = "".join("|" + re.escape(h.rstrip("/")) for h in sorted(self.home_variants, key=len, reverse=True) if h.rstrip("/"))
        return r"~[A-Za-z0-9._-]*|\$HOME(?![A-Za-z0-9_])|\$\{HOME[^}]*\}|/(?:Users|home)/[^/\s'\"]+" + literal

    def self_protect_re(self):
        """Raw-text spellings of ~/.claude, its settings files and hooks/ under any home spelling."""
        if self._self_re is None:
            self._self_re = re.compile(r"(?:%s)/+\.claude/+(?:settings(?:\.local)?\.json|hooks)(?![A-Za-z0-9._-])" % self._home_spellings(), re.IGNORECASE)
        return self._self_re

    def signing_re(self):
        """Raw-text spellings of ~/.gitconfig and ~/.config/git under any home spelling, and any .git/hooks path."""
        if self._signing_re is None:
            home = r"(?:%s)/+(?:\.gitconfig|\.config/+git)(?![A-Za-z0-9._-])" % self._home_spellings()
            hooks = r"(?<![A-Za-z0-9._-])\.git/+hooks(?![A-Za-z0-9._-])"
            system = r"(?<![A-Za-z0-9._/-])(?:/usr/local|/opt/homebrew)?/+etc/+gitconfig(?![A-Za-z0-9._-])"
            self._signing_re = re.compile(r"%s|%s|%s" % (home, hooks, system), re.IGNORECASE)
        return self._signing_re

    def is_signing_config(self, candidates: list) -> bool:
        """~/.gitconfig, anything under ~/.config/git, a repository's .git/config or config.worktree, or .git/hooks/."""
        files = [f.casefold() for f in self.signing_files]
        for c in candidates:
            if c.casefold() in files or any(_inside(c, d) for d in self.signing_dirs):
                return True
            parts = [p.casefold() for p in c.split("/")]
            if ".git" in parts:
                after = parts[parts.index(".git") + 1 :]
                if after[:1] == ["hooks"] or after in (["config"], ["config.worktree"]) or (len(after) == 3 and after[0] == "worktrees" and after[2] == "config.worktree"):
                    return True
        return False

    def in_cred_dir(self, candidates: list) -> bool:
        return any(_has_cred_component(c) or any(_inside(c, d) for d in self.cred_dirs) for c in candidates)

    def is_protected(self, candidates: list) -> bool:
        files = [f.casefold() for f in self.protected_files]
        return any(c.casefold() in files or any(_inside(c, d) for d in self.protected_dirs) for c in candidates)


def _with_real(paths: list) -> list:
    return _unique(paths + [os.path.realpath(p) for p in paths])


# ---------------------------------------------------------------------------------------------
# Read / Write / Edit / MultiEdit / NotebookEdit, and Grep / Glob
# ---------------------------------------------------------------------------------------------
FILE_TOOLS = ("Read", "Write", "Edit", "MultiEdit", "NotebookEdit")
SEARCH_TOOLS = ("Grep", "Glob")
COVERED_TOOLS = ("Bash",) + FILE_TOOLS + SEARCH_TOOLS


def path_candidates(path: str, ctx: Context) -> list:
    """The literal path (absolute, normalised) and the path it resolves to through symlinks."""
    if path.startswith("~"):
        tail = path.split("/", 1)[1] if "/" in path else ""
        bases = [os.path.join(h, tail) for h in ctx.homes]
    elif os.path.isabs(path):
        bases = [path]
    else:
        bases = [os.path.join(ctx.cwd or os.getcwd(), path)]
    out = []
    for base in bases:
        literal = os.path.normpath(base)
        out.extend([literal, os.path.realpath(literal)])
    return _unique(out)


def _text_of(value) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


def _new_content(tool: str, tool_input: dict) -> str:
    if tool == "Write":
        return _text_of(tool_input.get("content", ""))
    if tool == "Edit":
        return _text_of(tool_input.get("new_string", ""))
    if tool == "MultiEdit":
        edits = tool_input.get("edits", [])
        if isinstance(edits, list):
            return "\n".join(_text_of(e.get("new_string", "")) if isinstance(e, dict) else _text_of(e) for e in edits)
        return _text_of(edits)
    return _text_of(tool_input.get("new_source", ""))


def check_file_tool(tool: str, tool_input: dict, ctx: Context) -> list:
    key = "notebook_path" if tool == "NotebookEdit" and "notebook_path" in tool_input else "file_path"
    path = tool_input.get(key)
    if not isinstance(path, str) or not path:
        raise MalformedInput("%s needs a non-empty string tool_input.%s" % (tool, key))
    candidates = path_candidates(path, ctx)
    hits = []
    if ctx.in_cred_dir(candidates):
        hits.append(Hit("CRED-PATH-FILE", path))
    if tool != "Read":
        if ctx.is_protected(candidates):
            hits.append(Hit("SELF-PROTECT-FILE", path))
        settings_like = any(os.path.basename(c).casefold() in CLAUDE_SETTINGS_FILES and os.path.basename(os.path.dirname(c)).casefold() == CLAUDE_DIR_NAME for c in candidates)
        if settings_like and DISABLE_HOOKS_KEY in _new_content(tool, tool_input).casefold():
            hits.append(Hit("SELF-PROTECT-FILE", "disableAllHooks in " + path))
        if ctx.is_signing_config(candidates):
            hits.append(Hit("GIT-SIGNING-FILE", path))
    return hits


def check_search_tool(tool: str, tool_input: dict, ctx: Context) -> list:
    path = tool_input.get("path")
    if path is not None and not isinstance(path, str):
        raise MalformedInput("%s tool_input.path must be a string" % tool)
    pattern_key = "pattern" if tool == "Glob" else "glob"
    pattern = tool_input.get(pattern_key)
    if (tool == "Glob" and not isinstance(pattern, str)) or (pattern is not None and not isinstance(pattern, str)):
        raise MalformedInput("%s needs a string tool_input.%s" % (tool, pattern_key))
    root_text = path or ctx.cwd or os.getcwd()
    roots = path_candidates(root_text, ctx)
    hits = []
    if ctx.in_cred_dir(roots):
        hits.append(Hit("CRED-PATH-SEARCH", root_text))
    if tool == "Grep" and any(_inside(d, r) for r in roots for d in ctx.cred_dirs):
        hits.append(Hit("CRED-PATH-SEARCH", "%s (a recursive search from home or above)" % root_text))
    if pattern and any(_pattern_reaches(alt, roots, ctx) for alt in brace_expand(pattern)):
        hits.append(Hit("CRED-PATH-SEARCH", pattern))
    return hits


def _pattern_reaches(pattern: str, roots: list, ctx: Context) -> bool:
    """A path pattern (absolute, ``~``-prefixed, or relative to a root) that can match into a cred dir."""
    if pattern.startswith("~"):
        tail = pattern.split("/", 1)[1] if "/" in pattern else ""
        effective = [os.path.join(h, tail) for h in ctx.homes]
    elif pattern.startswith("/"):
        effective = [pattern]
    else:
        effective = [os.path.join(r, pattern) for r in roots]
    targets = [_components(d) for d in ctx.cred_dirs]
    for eff in effective:
        parts = _components(os.path.normpath(eff))
        k = 0
        while k < len(parts) and not _has_glob(parts[k]):
            k += 1
        resolved = _components(os.path.realpath("/" + "/".join(parts[:k]))) + parts[k:]
        for cand in (parts, resolved):
            if any(c.casefold() in CRED_DIR_NAMES for c in cand) or any(could_reach(cand, t) for t in targets):
                return True
    return False


# ---------------------------------------------------------------------------------------------
# Decision and output
# ---------------------------------------------------------------------------------------------
def decide(payload, ctx: Context) -> list:
    """The rules a payload trips, first match first; ``[]`` lets the call through untouched."""
    if not isinstance(payload, dict):
        raise MalformedInput("the payload is not a JSON object")
    tool = payload.get("tool_name")
    if not isinstance(tool, str) or not tool:
        raise MalformedInput("tool_name is missing or not a string")
    if tool not in COVERED_TOOLS:
        return []
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        raise MalformedInput("%s arrived without a tool_input object" % tool)
    if tool == "Bash":
        command = tool_input.get("command")
        if not isinstance(command, str):
            raise MalformedInput("Bash needs a string tool_input.command")
        hits = BashAnalyzer(ctx).analyze(command)
    elif tool in FILE_TOOLS:
        hits = check_file_tool(tool, tool_input, ctx)
    else:
        hits = check_search_tool(tool, tool_input, ctx)
    seen = set()
    out = []
    for h in hits:
        if h.rule_id not in seen:
            seen.add(h.rule_id)
            out.append(h)
    return out


def _evidence(text: str) -> str:
    flat = " ".join(str(text).split())
    return flat if len(flat) <= EVIDENCE_LIMIT else flat[: EVIDENCE_LIMIT - 3] + "..."


def deny_reason(hits: list, tool: str) -> str:
    rule = RULE_BY_ID[hits[0].rule_id]
    reason = "%s denied this %s call. Rule %s: %s (matched: %s). %s. This action is OWNER-run under D11 of %s: do not retry it or look for a way around the guard; ask the owner to run it in their own terminal." % (GUARD_NAME, tool, rule.rule_id, rule.description, _evidence(hits[0].evidence), rule.reason, PLAN_DOC)
    others = [h.rule_id for h in hits[1:]]
    if others:
        reason += " Also matched: %s." % ", ".join(others)
    return reason


def deny_output(hits: list, tool: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": deny_reason(hits, tool)}}


def run_hook(raw: bytes, homes=None) -> tuple:
    """(exit code, stdout, stderr) for one payload. Never produces an allow decision."""
    try:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise MalformedInput("stdin is not UTF-8 JSON (%s)" % exc.__class__.__name__)
        cwd = payload.get("cwd") if isinstance(payload, dict) else None
        ctx = Context(resolve_homes() if homes is None else homes, cwd if isinstance(cwd, str) and cwd else os.getcwd())
        hits = decide(payload, ctx)
    except MalformedInput as exc:
        return 2, "", "%s: refusing a malformed hook payload (fail closed): %s\n" % (GUARD_NAME, exc)
    except Exception as exc:  # a guard bug must block, not allow
        return 2, "", "%s: internal error, failing closed: %s: %s\n" % (GUARD_NAME, exc.__class__.__name__, exc)
    if not hits:
        return 0, "", ""
    return 0, json.dumps(deny_output(hits, payload["tool_name"])) + "\n", ""


# ---------------------------------------------------------------------------------------------
# --self-test and the CLI
# ---------------------------------------------------------------------------------------------
def self_test() -> int:
    """A small sanity table against a temporary home; the real home is never consulted."""
    import shutil
    import tempfile

    root = os.path.realpath(tempfile.mkdtemp(prefix="juniper-agent-guard-selftest-"))
    try:
        home = os.path.join(root, "home")
        repo = os.path.join(root, "repo")
        for d in (os.path.join(home, ".ssh"), os.path.join(home, ".gnupg"), os.path.join(home, ".claude", "hooks"), os.path.join(repo, ".claude")):
            os.makedirs(d)
        for name, body in ((os.path.join(home, ".ssh", "config"), "Host example\n"), (os.path.join(home, ".claude", "settings.json"), "{}\n")):
            with open(name, "w", encoding="utf-8") as fh:
                fh.write(body)
        link = os.path.join(root, "link-to-ssh")
        os.symlink(os.path.join(home, ".ssh"), link)
        cases = [
            ("Bash", {"command": "cat ~/.ssh/config"}, "CRED-PATH-BASH"),
            ("Bash", {"command": "gh api -X POST repos/o/r/issues"}, "GH-API-WRITE"),
            ("Bash", {"command": "gh api repos/o/r/issues -XPOST"}, "GH-API-WRITE"),
            ("Bash", {"command": "GH_TOKEN=x /usr/local/bin/gh api --method=PATCH repos/o/r"}, "GH-API-WRITE"),
            ("Bash", {"command": "bash -c 'sudo true'"}, "PRIV-ESCALATION"),
            ("Bash", {"command": "echo $(gpg --card-status)"}, "GPG-SECRET"),
            ("Bash", {"command": "ssh -T git@github.com"}, "SSH-PROBE"),
            ("Bash", {"command": "gh pr merge 12 --squash"}, "GH-PR-WRITE"),
            ("Bash", {"command": "gh auth token"}, "GH-AUTH"),
            ("Bash", {"command": "git commit -S -m x"}, "GPG-SIGN"),
            ("Bash", {"command": "security find-generic-password -s x"}, "KEYCHAIN-DUMP"),
            ("Bash", {"command": "defaults write com.example k v"}, "MACOS-DEFAULTS-WRITE"),
            ("Bash", {"command": 'cp x "$HOME"/.claude/settings.json'}, "SELF-PROTECT-BASH"),
            ("Bash", {"command": "gh api repos/o/r/pulls --jq '.[].number'"}, None),
            ("Bash", {"command": "ssh -G github_juniper-ml"}, None),
            ("Bash", {"command": "ls .sshrc_backup foo.ssh.txt; echo $GIT_SSH_COMMAND"}, None),
            ("Bash", {"command": "cat .claude/settings.json"}, None),
            ("Bash", {"command": "git -c include.path=/tmp/sign.inc commit -m x"}, "GIT-SIGNING-CONFIG"),
            ("Bash", {"command": "git --config-env=commit.gpgsign=V commit -m x"}, "GIT-SIGNING-CONFIG"),
            ("Bash", {"command": "git config --local gpg.program /tmp/x"}, "GIT-SIGNING-CONFIG"),
            ("Bash", {"command": "cp hook .git/hooks/post-commit"}, "GIT-SIGNING-CONFIG"),
            ("Bash", {"command": "git config --get user.signingkey"}, None),
            ("Write", {"file_path": os.path.join(repo, ".git", "hooks", "post-commit"), "content": "#!/bin/sh\n"}, "GIT-SIGNING-FILE"),
            ("Edit", {"file_path": os.path.join(home, ".gitconfig"), "old_string": "a", "new_string": "b"}, "GIT-SIGNING-FILE"),
            ("Read", {"file_path": os.path.join(home, ".gitconfig")}, None),
            ("Read", {"file_path": os.path.join(home, ".ssh", "config")}, "CRED-PATH-FILE"),
            ("Read", {"file_path": os.path.join(link, "config")}, "CRED-PATH-FILE"),
            ("Read", {"file_path": os.path.join(home, ".claude", "settings.json")}, None),
            ("Edit", {"file_path": os.path.join(home, ".claude", "settings.json"), "old_string": "a", "new_string": "b"}, "SELF-PROTECT-FILE"),
            ("Write", {"file_path": os.path.join(repo, ".claude", "settings.json"), "content": "{}"}, None),
            ("Grep", {"pattern": "x", "path": os.path.join(home, ".gnupg")}, "CRED-PATH-SEARCH"),
            ("Glob", {"pattern": os.path.join(home, ".ss?", "*")}, "CRED-PATH-SEARCH"),
            ("Glob", {"pattern": "**/*.py", "path": repo}, None),
            ("WebFetch", {"url": "https://example.com"}, None),
        ]
        failures = []
        for tool, tool_input, expected in cases:
            code, out, _ = run_hook(json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": repo}).encode("utf-8"), homes=[home])
            got = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"].split("Rule ", 1)[1].split(":", 1)[0] if out else None
            if code != 0 or got != expected:
                failures.append("%s %s: expected %s, got %s (exit %d)" % (tool, json.dumps(tool_input), expected, got, code))
        for bad in (b"not json", b"[]", b'{"tool_input": {}}', b'{"tool_name": "Bash"}', b'{"tool_name": "Read", "tool_input": {"file_path": 7}}'):
            code, out, err = run_hook(bad, homes=[home])
            if code != 2 or out or not err:
                failures.append("malformed %r: expected exit 2 with empty stdout, got exit %d" % (bad, code))
        spec = deny_output([Hit("GH-API-WRITE", "-X")], "Bash")["hookSpecificOutput"]
        if spec.get("hookEventName") != "PreToolUse" or spec.get("permissionDecision") != "deny" or "GH-API-WRITE" not in spec.get("permissionDecisionReason", ""):
            failures.append("the deny output has the wrong shape")
        total = len(cases) + 6
        for line in failures:
            print("FAIL " + line)
        print("%s %s self-test: %d of %d checks passed" % (GUARD_NAME, __version__, total - len(failures), total))
        return 0 if not failures else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


SETTINGS_HELP = (
    """\
settings entry (util/install_claude_agent_guard.bash prints it, or merges it with --apply; owner-run):
  "hooks": {"PreToolUse": [{"matcher": "%s",
    "hooks": [{"type": "command", "command": "/usr/bin/python3",
               "args": ["-I", "<home>/.claude/hooks/juniper_agent_guard.py"],
               "timeout": 10, "onFailure": "block"}]}]}

As a hook (no arguments) it reads the PreToolUse JSON on stdin. A denied call prints one deny
object and exits 0; any other call prints nothing and exits 0; malformed input exits 2.
"""
    % SETTINGS_MATCHER
)


def _cli(argv: list) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog=GUARD_NAME, description="Claude Code PreToolUse hook that denies what D11 forbids an agent on turing (%s)." % PLAN_DOC, epilog=SETTINGS_HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true", help="run the built-in sanity table against a temporary home; exit 0 or 1")
    ap.add_argument("--list-rules", action="store_true", help="print the rule table")
    ap.add_argument("--version", action="version", version="%s %s" % (GUARD_NAME, __version__))
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.list_rules:
        for rule in RULES:
            print("%-21s %-38s %s" % (rule.rule_id, rule.scope, rule.description))
        return 0
    ap.print_help()
    return 2


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        return _cli(argv)
    code, out, err = run_hook(sys.stdin.buffer.read())
    if out:
        sys.stdout.write(out)
        sys.stdout.flush()
    if err:
        sys.stderr.write(err)
    return code


if __name__ == "__main__":
    sys.exit(main())
