#!/usr/bin/env bash
# Write a Juniper checkout's .mcp.json Serena entry: pinned, bound to the checkout, shell tool excluded.
#
# Project:    juniper-ml
# Sub-Project: host tooling (turing bring-up)
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-21
# Status:     permanent utility
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task H4, decision D10, §10);
#             notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md (A2-F1, A2-F4);
#             conf/hosts/<host>/mcp.json (the pin); tests/test_mcp_setup.py
#
# Claude Code reads a checkout's project-scope MCP servers from <checkout>/.mcp.json. Three defects this fixes:
#   A2-F1  the entry started Serena without --project, so Serena came up with no active project;
#   A2-F4  juniper-ml gitignores .mcp.json, so no worktree inherits it, and a copied file binds the wrong
#          checkout;
#   D10    `uvx --from git+https://github.com/oraios/serena` runs the repository's unpinned HEAD, with the
#          owner's keys in reach.
# It writes one entry, per checkout:
#
#   "serena": {"type": "stdio", "command": "uvx", "env": {},
#              "args": ["--from", "git+https://github.com/oraios/serena@<commit>", "serena", "start-mcp-server",
#                       "--context", "<context>", "--project", "<checkout>", "--open-web-dashboard", "False"]}
#
# <commit> and <context> come from conf/hosts/<host>/mcp.json, the host's approved pin. The commit is a full
# 40-hex sha, because a tag or a branch can move; the context is a built-in Serena context name, never a path.
# turing's pin is Serena v1.7.0, whose claude-code context lists execute_shell_command in excluded_tools, so the
# server offers no shell that would sidestep Claude Code's Bash permission rules (D10). A pin bump must re-read
# that list at the new commit. <checkout> is the checkout's absolute path with symlinks resolved.
# --open-web-dashboard False keeps Serena from opening a browser tab at every session start; the dashboard still
# runs on localhost.
#
# Every other server, and every other top-level key, of an existing .mcp.json is kept. A file that changes is
# copied to .mcp.json.bak-<UTC time> first (a -N suffix keeps two changes in one second apart). The new file is
# written to a temp file in the checkout, takes the old file's mode (a new file is 600), and is moved into place.
# A file that already matches is not touched, so a second run writes nothing.
#
# Usage:
#   bash util/mcp_setup.bash [--host NAME] [--conf FILE] [--check | --remove] [--dry-run] [checkout]
#   The checkout defaults to the one that holds this script; a worktree is a checkout.
#
# Exit codes:
#   0 -- written or already up to date; with --remove, removed or absent; with --check, the entry matches the
#        pin; with --dry-run, the plan is printed and nothing is written
#   1 -- --check only: .mcp.json or its Serena entry is missing, or the entry differs from the pin
#   2 -- usage or environment: a bad argument, a checkout that is not a git checkout or worktree, no pin for
#        the host, a pin that is not a full commit, an existing .mcp.json that is not a JSON object (it is
#        never overwritten), or no python3
#
# Environment:
#   PYTHON -- the python3 that reads and writes the JSON (default: python3); tests override it
set -euo pipefail
umask 077

PYTHON="${PYTHON:-python3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

usage() {
    cat <<'EOF'
Usage: mcp_setup.bash [--host NAME] [--conf FILE] [--check | --remove] [--dry-run] [checkout]

Write the Serena entry of <checkout>/.mcp.json: `uvx --from git+https://github.com/oraios/serena@<commit>
serena start-mcp-server --context <context> --project <checkout> --open-web-dashboard False`, with the
commit and context from the host's pin. Other servers and keys are kept; a changed file is backed up
first; a second run writes nothing.

  checkout       the git checkout or worktree to configure (default: the one that holds this script)
  --host NAME    the host whose pin to use (default: this machine's short hostname, in lower case)
  --conf FILE    the pin file (default: conf/hosts/<host>/mcp.json in this script's checkout)
  --check        exit 0 when the entry matches the pin, 1 when it is missing or differs; write nothing
  --remove       remove the Serena entry, keeping the rest; delete the file if nothing else is left
  --dry-run      print what would be written or removed; write nothing
  -h, --help     show this help

Exit codes: 0 done (or --check: matches), 1 --check: missing or differs, 2 usage/environment error.
EOF
}

die_usage() {
    echo "ERROR: $1" >&2
    echo "Run with --help for usage." >&2
    exit 2
}

die_env() {
    echo "ERROR: $1" >&2
    exit 2
}

HOST=""
CONF=""
MODE="write"
DRY_RUN=0
CHECKOUT=""

# A function rather than a top-level loop, as in util/juniper_repo_ssh_setup.bash: shellcheck 0.11 raises a
# false SC2218 on later top-level calls of die_usage when the loop sits at top level.
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h | --help)
                usage
                exit 0
                ;;
            --host)
                [[ $# -ge 2 ]] || die_usage "--host needs a value"
                HOST="$2"
                shift
                ;;
            --conf)
                [[ $# -ge 2 ]] || die_usage "--conf needs a value"
                CONF="$2"
                shift
                ;;
            --check | --remove)
                [[ "$MODE" == "write" ]] || die_usage "--check and --remove cannot be combined"
                MODE="${1#--}"
                ;;
            --dry-run) DRY_RUN=1 ;;
            -*) die_usage "unknown option: $1" ;;
            *)
                [[ -z "$CHECKOUT" ]] || die_usage "only one checkout may be given"
                CHECKOUT="$1"
                ;;
        esac
        shift
    done
}

parse_args "$@"

if [[ -z "$HOST" ]]; then
    HOST="$(hostname)"
    HOST="${HOST%%.*}"
    HOST="$(printf '%s' "$HOST" | tr '[:upper:]' '[:lower:]')"
fi
[[ "$HOST" =~ ^[a-z0-9][a-z0-9-]*$ ]] || die_usage "not a host name: '${HOST}' (pass --host)"
[[ -n "$CONF" ]] || CONF="${REPO_ROOT}/conf/hosts/${HOST}/mcp.json"
[[ -f "$CONF" ]] || die_env "no Serena pin for host '${HOST}': ${CONF} does not exist (D10: never run an unpinned Serena)"

[[ -n "$CHECKOUT" ]] || CHECKOUT="$REPO_ROOT"
[[ -d "$CHECKOUT" ]] || die_env "not a directory: ${CHECKOUT}"
CHECKOUT="$(cd "$CHECKOUT" && pwd -P)"
[[ -e "${CHECKOUT}/.git" ]] || die_env "not a git checkout or worktree (no .git): ${CHECKOUT}"
command -v "$PYTHON" >/dev/null 2>&1 || die_env "python3 not found (PYTHON=${PYTHON})"

# The JSON work is stdlib python: bash cannot merge into an existing document safely, and jq is not a
# dependency of this repository. Exit codes are the script's own.
"$PYTHON" -I - "$MODE" "$DRY_RUN" "$CHECKOUT" "$HOST" "$CONF" <<'PY'
import datetime
import json
import os
import re
import shutil
import sys
import tempfile

mode, dry_run, checkout, host, conf_path = sys.argv[1], sys.argv[2] == "1", sys.argv[3], sys.argv[4], sys.argv[5]
SOURCE = "git+https://github.com/oraios/serena"
target = os.path.join(checkout, ".mcp.json")


def fail(code, message):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(code)


try:
    with open(conf_path, encoding="utf-8") as handle:
        conf = json.load(handle)
except (OSError, ValueError) as exc:
    fail(2, "cannot read the pin file %s: %s" % (conf_path, exc))
pin = conf.get("serena") if isinstance(conf, dict) else None
if not isinstance(pin, dict):
    fail(2, "%s has no 'serena' object" % conf_path)
if conf.get("host") != host:
    fail(2, "%s is the pin of host %r, not %r" % (conf_path, conf.get("host"), host))
if pin.get("source") != SOURCE:
    fail(2, "%s: serena.source must be %s, got %r" % (conf_path, SOURCE, pin.get("source")))
commit, context = pin.get("commit"), pin.get("context")
if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
    fail(2, "%s: serena.commit must be a full 40-hex commit (a tag or branch can move), got %r" % (conf_path, commit))
if not isinstance(context, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", context):
    fail(2, "%s: serena.context must be a built-in context name, got %r" % (conf_path, context))

entry = {
    "type": "stdio",
    "command": "uvx",
    "args": [
        "--from",
        "%s@%s" % (SOURCE, commit),
        "serena",
        "start-mcp-server",
        "--context",
        context,
        "--project",
        checkout,
        "--open-web-dashboard",
        "False",
    ],
    "env": {},
}
label = "serena %s (%s), context %s, project %s" % (pin.get("release", "?"), commit[:12], context, checkout)

doc, existing_text = {}, None
if os.path.lexists(target):
    if os.path.islink(target) or not os.path.isfile(target):
        fail(2, "%s is not a regular file; refusing to touch it" % target)
    with open(target, encoding="utf-8") as handle:
        existing_text = handle.read()
    try:
        doc = json.loads(existing_text)
    except ValueError as exc:
        fail(2, "%s is not valid JSON (%s); refusing to overwrite it" % (target, exc))
    if not isinstance(doc, dict):
        fail(2, "%s is not a JSON object; refusing to overwrite it" % target)
servers = doc.get("mcpServers", {})
if not isinstance(servers, dict):
    fail(2, "%s: mcpServers is not a JSON object; refusing to overwrite it" % target)
others = sorted(name for name in servers if name != "serena")

if mode == "check":
    current = servers.get("serena")
    if existing_text is None:
        print("FAIL  %s does not exist; want %s" % (target, label))
        sys.exit(1)
    if current is None:
        print("FAIL  %s has no serena entry; want %s" % (target, label))
        sys.exit(1)
    if current != entry:
        print("FAIL  %s: the serena entry differs from the pin" % target)
        print("  have: " + json.dumps(current, sort_keys=True))
        print("  want: " + json.dumps(entry, sort_keys=True))
        sys.exit(1)
    print("OK    %s: %s" % (target, label))
    sys.exit(0)

if mode == "remove":
    if "serena" not in servers:
        print("ok (nothing to remove): %s has no serena entry" % target)
        sys.exit(0)
    del servers["serena"]
    if not servers:
        doc.pop("mcpServers", None)
    else:
        doc["mcpServers"] = servers
else:
    servers["serena"] = entry
    doc["mcpServers"] = servers

new_text = None if mode == "remove" and not doc else json.dumps(doc, indent=2) + "\n"
if new_text == existing_text:
    print("ok (already up to date): %s: %s" % (target, label))
    sys.exit(0)
if dry_run:
    if new_text is None:
        print("would delete %s (its only entry was serena)" % target)
    else:
        print("would write %s:" % target)
        sys.stdout.write(new_text)
    sys.exit(0)

if existing_text is not None:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = base = "%s.bak-%s" % (target, stamp)
    n = 1
    while os.path.lexists(backup):  # two changes in one second keep both backups
        backup = "%s-%d" % (base, n)
        n += 1
    shutil.copy2(target, backup)
    print("backup: %s (the previous file, any API tokens included; delete it once the new file works)" % backup)
if new_text is None:
    os.remove(target)
    print("deleted %s (its only entry was serena)" % target)
    sys.exit(0)
fd, tmp = tempfile.mkstemp(prefix=".mcp.json.", dir=checkout)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(new_text)
    if existing_text is not None:
        shutil.copymode(target, tmp)
    os.replace(tmp, target)
except BaseException:
    if os.path.exists(tmp):
        os.remove(tmp)
    raise
if mode == "remove":
    print("removed the serena entry from %s; kept: %s" % (target, ", ".join(others) or "(no servers)"))
else:
    print("wrote %s: %s" % (target, label))
    if others:
        print("kept: " + ", ".join(others))
PY
