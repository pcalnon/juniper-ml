#!/usr/bin/env bash
# install_claude_agent_guard.bash -- owner-run installer for the D11 item 4 PreToolUse guard.
#
# Project:     juniper-ml
# Sub-Project: host tooling (turing bring-up, task C8)
# Author:      Paul Calnon (authored via Claude Code)
# Created:     2026-10-17
# Related:     notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (D11, C8);
#              util/claude_agent_guard.py; tests/test_claude_agent_guard.py
#
# Installs util/claude_agent_guard.py as a COPY at <hooks-dir>/juniper_agent_guard.py (mode 0644),
# with its sha256 beside it, and runs the copy's --self-test. A copy, not a symlink: a branch switch
# in a checkout must not silently change the live guard. Then it prints the settings JSON, or with
# --apply merges it: a PreToolUse hook (exec form: HOOK_PYTHON -I <copy>, timeout 10,
# onFailure block) whose matcher the guard prints (--settings-matcher: the built-in tools and,
# since task C9, Serena's edit tools), and the belt-and-braces permissions.deny rules.
#
# Usage: bash util/install_claude_agent_guard.bash [--apply | --uninstall] [--dry-run]
#            [--settings FILE] [--hooks-dir DIR] [--help]
#   (no action)   install the copy and sha256, self-test it, print the JSON to merge by hand
#   --apply       install and self-test, then merge into the settings file (backup first),
#                 then verify the result and the copy's sha256 and self-test again
#   --uninstall   remove exactly what --apply added (backup first), then the installed files
#   --dry-run     show what the chosen action would change; write nothing
#   --settings    default ~/.claude/settings.json      --hooks-dir  default ~/.claude/hooks
# Exit: 0 OK / 1 verification failed (self-test, sha256, merged result) / 2 usage or environment.
# Environment: HOOK_PYTHON (default /usr/bin/python3) is the interpreter written into the hook
# entry and used for the self-test; MERGE_PYTHON (default HOOK_PYTHON) runs the JSON merge.
#
# Run it from your own terminal. The guard denies an agent running it without --dry-run / --help.
set -euo pipefail

HOOK_PYTHON="${HOOK_PYTHON:-/usr/bin/python3}"
MERGE_PYTHON="${MERGE_PYTHON:-$HOOK_PYTHON}"
SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="${SCRIPT_DIR}/claude_agent_guard.py"
SETTINGS="${HOME}/.claude/settings.json"
HOOKS_DIR="${HOME}/.claude/hooks"
ACTION="print"
DRY_RUN=0
PROG="install_claude_agent_guard"

usage() {
    sed -n '2,29p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

die_usage() {
    printf '%s: %s (try --help)\n' "$PROG" "$1" >&2
    exit 2
}

die_env() {
    printf '%s: %s\n' "$PROG" "$1" >&2
    exit 2
}

fail() {
    printf '%s: VERIFY FAILED: %s\n' "$PROG" "$1" >&2
    exit 1
}

set_action() {
    if [[ "$ACTION" != "print" && "$ACTION" != "$1" ]]; then
        die_usage "--apply and --uninstall are mutually exclusive"
    fi
    ACTION="$1"
}

sha256_of() {
    "$MERGE_PYTHON" -I -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$1"
}

install_copy() {
    local src_sha tmp
    src_sha="$(sha256_of "$SOURCE")"
    mkdir -p -- "$HOOKS_DIR"
    if [[ -f "$INSTALLED" && "$(sha256_of "$INSTALLED")" == "$src_sha" ]]; then
        printf 'copy    %s unchanged (sha256 %s)\n' "$INSTALLED" "$src_sha"
    else
        tmp="$(mktemp "${HOOKS_DIR}/.juniper_agent_guard.XXXXXX")"
        cp -- "$SOURCE" "$tmp"
        chmod 0644 "$tmp"
        mv -f -- "$tmp" "$INSTALLED"
        printf 'copy    %s (sha256 %s)\n' "$INSTALLED" "$src_sha"
    fi
    chmod 0644 "$INSTALLED"
    tmp="$(mktemp "${HOOKS_DIR}/.juniper_agent_guard.sha256.XXXXXX")"
    printf '%s  %s\n' "$src_sha" "juniper_agent_guard.py" >"$tmp"
    chmod 0644 "$tmp"
    mv -f -- "$tmp" "$SHA_FILE"
}

verify_copy() {
    local want got recorded
    want="$(sha256_of "$SOURCE")"
    got="$(sha256_of "$INSTALLED")"
    recorded="$(cut -d' ' -f1 <"$SHA_FILE")"
    [[ "$got" == "$recorded" ]] || fail "installed copy sha256 $got does not match $SHA_FILE ($recorded)"
    [[ "$got" == "$want" ]] || fail "installed copy sha256 $got does not match the source $SOURCE ($want)"
    if ! "$HOOK_PYTHON" -I "$INSTALLED" --self-test; then
        fail "the installed copy's --self-test failed under $HOOK_PYTHON"
    fi
}

# The merge: stdlib JSON, Python 3.9-safe. argv: mode settings hook_python installed manifest dry_run matcher
merge_settings() {
    "$MERGE_PYTHON" -I - "$1" "$SETTINGS" "$HOOK_PYTHON" "$INSTALLED" "$MANIFEST" "$DRY_RUN" "$MATCHER" <<'PY'
import copy
import datetime
import difflib
import json
import os
import sys
import tempfile

mode, settings_path, hook_python, installed, manifest_path, dry_run, matcher = sys.argv[1:8]
DRY = dry_run == "1"
MATCHER = matcher
DENY = ["Read(~/.ssh/**)", "Read(~/.gnupg/**)", "Edit(~/.ssh/**)", "Edit(~/.gnupg/**)", "Bash(sudo *)", "Bash(ssh-add*)", "Bash(gpg --card-status*)", "Bash(gpg -K*)"]
ENTRY = {"matcher": MATCHER, "hooks": [{"type": "command", "command": hook_python, "args": ["-I", installed], "timeout": 10, "onFailure": "block"}]}
GUARD_FILE = "juniper_agent_guard.py"


def die(code, message):
    sys.stderr.write("install_claude_agent_guard: %s\n" % message)
    sys.exit(code)


def ours(entry):
    """An entry this installer wrote, at any version: one of its hooks runs juniper_agent_guard.py."""
    if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
        return False
    for hook in entry["hooks"]:
        if not isinstance(hook, dict):
            continue
        words = [hook.get("command")] + (hook.get("args") if isinstance(hook.get("args"), list) else [])
        if any(isinstance(w, str) and (w == GUARD_FILE or w.endswith("/" + GUARD_FILE)) for w in words):
            return True
    return False


def container(parent, key, kind, label, created):
    if key not in parent:
        parent[key] = kind()
        created.append(label)
    if not isinstance(parent[key], kind):
        die(2, "%s in %s is not a JSON %s; fix it by hand first" % (label, settings_path, "object" if kind is dict else "list"))
    return parent[key]


def render(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


if mode == "print":
    sys.stdout.write(render({"hooks": {"PreToolUse": [ENTRY]}, "permissions": {"deny": DENY}}))
    sys.exit(0)

exists = os.path.exists(settings_path)
original = {}
if exists:
    try:
        with open(settings_path, encoding="utf-8") as fh:
            text = fh.read()
        original = json.loads(text) if text.strip() else {}
    except (OSError, ValueError) as exc:
        die(2, "cannot read %s as JSON (%s); nothing was changed" % (settings_path, exc))
if not isinstance(original, dict):
    die(2, "%s is not a JSON object; nothing was changed" % settings_path)
manifest = {}
if os.path.exists(manifest_path):
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, ValueError):
        manifest = {}
    if not isinstance(manifest, dict):
        manifest = {}

new = copy.deepcopy(original)
notes = []
if mode == "apply":
    created = list(manifest.get("created", []))
    hooks = container(new, "hooks", dict, "hooks", created)
    pre = container(hooks, "PreToolUse", list, "hooks.PreToolUse", created)
    mine = [e for e in pre if ours(e)]
    if mine != [ENTRY]:
        pre[:] = [e for e in pre if not ours(e)] + [ENTRY]
        notes.append("hook entry " + ("updated" if mine else "added"))
    perms = container(new, "permissions", dict, "permissions", created)
    deny = container(perms, "deny", list, "permissions.deny", created)
    added = [rule for rule in DENY if rule not in deny]
    deny.extend(added)
    if added:
        notes.append("deny rules added: " + ", ".join(added))
    previous = [r for r in manifest.get("deny_added", []) if r in deny]
    manifest_out = {"version": 1, "settings": os.path.abspath(settings_path), "entry": ENTRY, "deny_added": previous + [r for r in added if r not in previous], "created": created}
elif mode == "uninstall":
    hooks = new.get("hooks")
    if isinstance(hooks, dict) and isinstance(hooks.get("PreToolUse"), list):
        before = len(hooks["PreToolUse"])
        hooks["PreToolUse"] = [e for e in hooks["PreToolUse"] if not ours(e)]
        if len(hooks["PreToolUse"]) != before:
            notes.append("hook entry removed")
    perms = new.get("permissions")
    if not manifest:
        notes.append("no install manifest at %s: permissions.deny left as it is" % manifest_path)
    elif isinstance(perms, dict) and isinstance(perms.get("deny"), list):
        drop = [r for r in manifest.get("deny_added", []) if r in perms["deny"]]
        perms["deny"] = [r for r in perms["deny"] if r not in drop]
        if drop:
            notes.append("deny rules removed: " + ", ".join(drop))
    for label in reversed(manifest.get("created", [])):
        parent_key, _, child = label.partition(".")
        parent = new.get(parent_key)
        if child and isinstance(parent, dict) and parent.get(child) in ([], {}):
            del parent[child]
        elif not child and new.get(parent_key) in ([], {}):
            del new[parent_key]
    manifest_out = None
else:
    die(2, "unknown merge mode %s" % mode)

changed = new != original
if DRY:
    print("DRY-RUN %s %s:" % (mode, settings_path))
    if changed:
        diff = difflib.unified_diff(render(original).splitlines(True), render(new).splitlines(True), "settings.json (now)", "settings.json (after %s)" % mode)
        sys.stdout.write("".join(diff))
    else:
        print("  settings unchanged")
    print("  (nothing written)")
    sys.exit(0)

if changed:
    directory = os.path.dirname(os.path.abspath(settings_path))
    if not os.path.isdir(directory):
        die(2, "settings directory does not exist: %s" % directory)
    mode_bits = 0o644
    if exists:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        suffix = "-pre-agent-guard" + ("-uninstall" if mode == "uninstall" else "")
        backup = "%s.bak-%s%s" % (settings_path, stamp, suffix)
        n = 1
        while os.path.exists(backup):
            n += 1
            backup = "%s.bak-%s-%d%s" % (settings_path, stamp, n, suffix)
        with open(settings_path, "rb") as src, open(backup, "wb") as dst:
            dst.write(src.read())
        mode_bits = os.stat(settings_path).st_mode & 0o777
        print("backup  %s" % backup)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".settings.json.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(render(new))
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, mode_bits)
        os.replace(tmp, settings_path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    with open(settings_path, encoding="utf-8") as fh:
        check = json.load(fh)
    present = [e for e in check.get("hooks", {}).get("PreToolUse", []) if ours(e)]
    if check != new or (mode == "apply" and present != [ENTRY]) or (mode == "uninstall" and present):
        die(1, "the merged %s does not read back as written" % settings_path)
for note in notes:
    print("%-7s %s" % (mode, note))
print("%-7s %s %s" % (mode, settings_path, "updated" if changed else "unchanged"))
if manifest_out is not None:
    with open(manifest_path, "w", encoding="utf-8") as fh:
        fh.write(render(manifest_out))
elif os.path.exists(manifest_path):
    os.unlink(manifest_path)
PY
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h | --help)
            usage
            exit 0
            ;;
        --apply) set_action apply ;;
        --uninstall) set_action uninstall ;;
        --dry-run) DRY_RUN=1 ;;
        --settings | --hooks-dir)
            [[ $# -ge 2 && -n "$2" ]] || die_usage "$1 needs a value"
            if [[ "$1" == "--settings" ]]; then SETTINGS="$2"; else HOOKS_DIR="$2"; fi
            shift
            ;;
        --settings=?*) SETTINGS="${1#*=}" ;;
        --hooks-dir=?*) HOOKS_DIR="${1#*=}" ;;
        *) die_usage "unknown argument: $1" ;;
    esac
    shift
done

case "$HOOK_PYTHON" in
    /*) ;;
    *) die_env "HOOK_PYTHON must be an absolute path (the hook entry runs it without a shell): $HOOK_PYTHON" ;;
esac
[[ -x "$MERGE_PYTHON" ]] || die_env "MERGE_PYTHON is not executable: $MERGE_PYTHON"
if [[ "$DRY_RUN" -eq 0 && "$ACTION" != "uninstall" && ! -x "$HOOK_PYTHON" ]]; then
    die_env "HOOK_PYTHON is not executable: $HOOK_PYTHON"
fi
[[ -f "$SOURCE" ]] || die_env "guard source not found: $SOURCE"
# The matcher comes from the guard, so the hook entry names exactly the tools the guard judges.
MATCHER="$("$MERGE_PYTHON" -I "$SOURCE" --settings-matcher)" || die_env "cannot read the hook matcher from $SOURCE --settings-matcher"
MATCHER_RE='^[A-Za-z_]+([|][A-Za-z_]+)*$'
[[ "$MATCHER" =~ $MATCHER_RE ]] || die_env "unexpected hook matcher from $SOURCE: $MATCHER"
case "$HOOKS_DIR" in
    /*) ;;
    *) HOOKS_DIR="$(pwd)/${HOOKS_DIR}" ;;
esac
HOOKS_DIR="${HOOKS_DIR%/}"
INSTALLED="${HOOKS_DIR}/juniper_agent_guard.py"
SHA_FILE="${INSTALLED}.sha256"
MANIFEST="${HOOKS_DIR}/juniper_agent_guard.manifest.json"

case "$ACTION" in
    print | apply)
        if [[ "$DRY_RUN" -eq 1 ]]; then
            printf 'DRY-RUN would copy %s -> %s (mode 0644) and write %s\n' "$SOURCE" "$INSTALLED" "$SHA_FILE"
            if [[ "$ACTION" == "apply" ]]; then
                merge_settings apply
            else
                printf 'DRY-RUN would print this JSON to merge into %s:\n' "$SETTINGS"
                merge_settings print
            fi
            exit 0
        fi
        install_copy
        verify_copy
        if [[ "$ACTION" == "print" ]]; then
            printf '\nMerge this into %s (or re-run with --apply):\n' "$SETTINGS"
            merge_settings print
            exit 0
        fi
        merge_settings apply
        verify_copy
        printf 'OK      the guard is wired; settings changes apply to running sessions without a restart\n'
        ;;
    uninstall)
        merge_settings uninstall
        if [[ "$DRY_RUN" -eq 1 ]]; then
            printf 'DRY-RUN would remove %s and %s\n' "$INSTALLED" "$SHA_FILE"
            exit 0
        fi
        rm -f -- "$INSTALLED" "$SHA_FILE" "$MANIFEST"
        printf 'removed %s and %s\n' "$INSTALLED" "$SHA_FILE"
        ;;
esac
