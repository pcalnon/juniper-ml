#!/usr/bin/env bash
# Provision one Juniper repo's deploy key and its github_juniper-<repo> ssh Host alias, idempotently.
#
# Project:    juniper-ml
# Sub-Project: host tooling (turing bring-up)
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-17
# Status:     permanent utility
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task A5, D2, §13);
#             util/juniper_clone.bash (which sends users here); tests/test_juniper_repo_ssh_setup.py
#
# Every Juniper origin is git@github_juniper-<repo>:<owner>/juniper-<repo>.git. The alias's Host block,
# with IdentitiesOnly, makes ssh offer exactly one key: that repo's deploy key (plan §4.1). For one repo:
#   1. Key. When <ssh-dir>/id_ed25519_github_juniper-<repo> is absent, it runs
#      `ssh-keygen -t ed25519 -N '' -C "<title>" -f <key>`, then sets 600 on the key and 644 on the .pub.
#      An existing key is never touched. A key not at mode 600, a .pub not at 644, a key without its .pub
#      and a .pub without its key are reported as non-compliant, with the fix.
#   2. Host block. When <ssh-dir>/config has no `Host github_juniper-<repo>` block, it appends the
#      canonical block below. The existing bytes are kept verbatim; at most a newline and one blank line
#      go in ahead of the block. The new file is built in a temp file in the same directory (mode 600),
#      evaluated with `ssh -F <temp> -G` (so a file ssh cannot parse, or one whose earlier content
#      overrides the block, is never installed), and then moved over the config with `mv`. An existing
#      block is never touched; it is compared with the canonical form, and a difference is shown as a diff.
#   3. Owner step. It prints the GitHub web-UI step: URL, title, write access, fingerprint. Deploy keys
#      go in through the web UI, never `gh repo deploy-key add`. gh ties the keys it adds to its token,
#      and they are deleted when that token is revoked (plan D2). The fixed title is what makes the
#      lost-device runbook scriptable (plan §13).
# Then `ssh -G github_juniper-<repo>` must resolve hostname github.com, exactly the block's identity file,
# and identitiesonly yes. With a --ssh-dir other than ~/.ssh the check passes `-F <ssh-dir>/config`, so it
# reads the file this run manages. `ssh -G` only evaluates the configuration; it never connects.
#
# Assess, then act. Every check runs before anything is written. Non-compliant existing state is reported,
# not fixed, and the run stops with nothing written.
#
# The canonical block is the form of turing's existing blocks, with plan A8's AddKeysToAgent no:
#   Host github_juniper-<repo>
#     HostName github.com
#     User git
#     IdentityFile ~/.ssh/id_ed25519_github_juniper-<repo>
#     IdentitiesOnly yes
#     AddKeysToAgent no
#     UseKeychain yes
# For a --ssh-dir other than ~/.ssh, IdentityFile is the key's absolute path.
#
# UseKeychain is written only when `$UNAME -s` prints Darwin. It is Apple's addition to OpenSSH. Upstream
# OpenSSH (Linux, and Homebrew's openssh on macOS) rejects it as a bad configuration option, and that is
# fatal. `IgnoreUnknown UseKeychain` inside the block does not fix it. ssh parses every line of the file,
# and an unknown keyword is an error even inside a Host block that does not match, while IgnoreUnknown
# takes effect only inside a block that does (readconf.c, OpenSSH 9.6p1). So one such block would break
# every OTHER destination on a Linux host. A working IgnoreUnknown must come before every Host block, and
# this script never edits existing content. Writing it on Darwin only also keeps the block byte-identical
# to turing's existing ten. If a Darwin host's ssh is not Apple's, the pre-install `ssh -G` fails (exit 2)
# and the config is left as it was.
#
# It never reads or prints private-key contents. The key is checked by name and mode (find -perm), and
# only the .pub is fingerprinted.
#
# Usage:
#   bash util/juniper_repo_ssh_setup.bash [--owner OWNER] [--title TITLE] [--ssh-dir DIR] [--dry-run] <repo>
#   <repo> is the short name ("k8s") or the full name ("juniper-k8s").
#
# Exit codes:
#   0 -- created what was missing, or already configured, and the ssh -G check passed
#        (with --dry-run: the plan is printed and nothing is written)
#   1 -- non-compliant existing state (reported, not fixed, nothing written), or ssh -G resolves the alias
#        differently from the block
#   2 -- usage or environment: a bad argument, a missing tool, a missing or unwritable ssh directory, a
#        title that cannot be derived, a symlinked or read-only config that would need rewriting,
#        ssh-keygen failing, or ssh unable to evaluate the configuration
#
# Environment:
#   SSH_KEYGEN, SSH, UNAME -- the ssh-keygen, ssh and uname binaries (default: from PATH); tests override them
set -euo pipefail
umask 077

SSH_KEYGEN="${SSH_KEYGEN:-ssh-keygen}"
SSH="${SSH:-ssh}"
UNAME="${UNAME:-uname}"

usage() {
    cat <<'EOF'
Usage: juniper_repo_ssh_setup.bash [--owner OWNER] [--title TITLE] [--ssh-dir DIR] [--dry-run] <repo>

Create the deploy key id_ed25519_github_juniper-<repo> if it is absent, append the canonical
"Host github_juniper-<repo>" block to the ssh config if it is absent, print the GitHub web-UI
step that registers the key, and check the alias with `ssh -G`. A second run writes nothing.

  <repo>         short ("k8s") or full ("juniper-k8s") repository name
  --owner OWNER  GitHub owner, for the web-UI URL (default: pcalnon)
  --title TITLE  deploy-key title and key comment (default: "Deploy Key - <Host>", where Host
                 is the short hostname with its first letter capitalized)
  --ssh-dir DIR  directory that holds the key and the config (default: $HOME/.ssh)
  --dry-run      check and print the plan; write nothing, run neither ssh-keygen nor ssh
  -h, --help     show this help

Exit codes: 0 created or already compliant, 1 non-compliant existing state (reported, not
fixed) or an ssh -G mismatch, 2 usage/environment error.
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

OWNER="pcalnon"
TITLE=""
SSH_DIR=""
DRY_RUN=0
REPO=""

# A function rather than a top-level loop: shellcheck 0.11 raises a false SC2218 on every later
# top-level call of die_usage/die_env when the loop sits at top level (0.10, the pre-commit pin, does not).
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h | --help)
                usage
                exit 0
                ;;
            --owner)
                [[ -n "${2:-}" ]] || die_usage "--owner needs a value"
                OWNER="$2"
                shift 2
                ;;
            --title)
                [[ -n "${2:-}" ]] || die_usage "--title needs a value"
                TITLE="$2"
                shift 2
                ;;
            --ssh-dir)
                [[ -n "${2:-}" ]] || die_usage "--ssh-dir needs a directory"
                SSH_DIR="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            -*)
                die_usage "unknown option: $1"
                ;;
            *)
                [[ -z "$REPO" ]] || die_usage "one repo per run (got '$REPO' and '$1')"
                REPO="$1"
                shift
                ;;
        esac
    done
}
parse_args "$@"

[[ -n "$REPO" ]] || die_usage "no repo given"

NAME="${REPO#juniper-}"
name_re='^[a-z0-9][a-z0-9-]*$'
owner_re='^[A-Za-z0-9][A-Za-z0-9-]*$'
title_re='^[A-Za-z0-9][A-Za-z0-9 ._@:+(),-]*$'
[[ "$NAME" =~ $name_re ]] || die_usage "not a Juniper repo name: '$REPO' (expected e.g. k8s or juniper-k8s)"
[[ "$OWNER" =~ $owner_re ]] || die_usage "not a GitHub owner: '$OWNER'"
if [[ -n "$TITLE" && ! "$TITLE" =~ $title_re ]]; then
    die_usage "not a usable key title: '$TITLE' (letters, digits, spaces and ._@:+(),- only)"
fi

for tool in "$SSH_KEYGEN" "$SSH" "$UNAME"; do
    command -v "$tool" >/dev/null 2>&1 || die_env "required tool not found: ${tool}"
done

OS="$("$UNAME" -s)" || die_env "'${UNAME} -s' failed"
if [[ -z "$TITLE" ]]; then
    node="$("$UNAME" -n)" || die_env "'${UNAME} -n' failed"
    short="${node%%.*}"
    host_re='^[A-Za-z0-9][A-Za-z0-9-]*$'
    [[ "$short" =~ $host_re ]] || die_env "cannot derive a key title from the hostname '${node}'; pass --title"
    TITLE="Deploy Key - $(printf '%s' "${short:0:1}" | tr '[:lower:]' '[:upper:]')${short:1}"
fi

if [[ -z "$SSH_DIR" ]]; then
    [[ -n "${HOME:-}" ]] || die_env "HOME is not set; pass --ssh-dir"
    SSH_DIR="${HOME}/.ssh"
fi
[[ -e "$SSH_DIR" ]] || die_env "ssh directory does not exist: ${SSH_DIR} (create it with: mkdir -m 700 '${SSH_DIR}')"
[[ -d "$SSH_DIR" ]] || die_env "not a directory: ${SSH_DIR}"
SSH_DIR="$(CDPATH='' cd -P -- "$SSH_DIR" && pwd -P)" || die_env "cannot enter ${SSH_DIR}"

HOME_SSH=""
if [[ -n "${HOME:-}" && -d "${HOME}/.ssh" ]]; then
    HOME_SSH="$(CDPATH='' cd -P -- "${HOME}/.ssh" && pwd -P)" || HOME_SSH=""
fi

FULL="juniper-${NAME}"
ALIAS="github_${FULL}"
KEY_NAME="id_ed25519_github_${FULL}"
KEY="${SSH_DIR}/${KEY_NAME}"
PUB="${KEY}.pub"
CONFIG="${SSH_DIR}/config"

if [[ "$SSH_DIR" == "$HOME_SSH" ]]; then
    # ssh_config's own "~/.ssh", as in turing's blocks: ssh expands the tilde, and the shell must not.
    # shellcheck disable=SC2088
    IDENTITY="~/.ssh/${KEY_NAME}"
    # No -F: check what ssh itself reads (its ~ is the password database's home, which is $HOME here).
    CHECK_CONFIG=""
else
    path_re='^/[A-Za-z0-9._@+/-]*$'
    [[ "$SSH_DIR" =~ $path_re ]] || die_env "an IdentityFile under ${SSH_DIR} would need quoting in ssh_config; use a directory whose path has only letters, digits and ._@+/-"
    IDENTITY="${KEY}"
    CHECK_CONFIG="${CONFIG}"
fi

CANONICAL="Host ${ALIAS}
  HostName github.com
  User git
  IdentityFile ${IDENTITY}
  IdentitiesOnly yes
  AddKeysToAgent no"
if [[ "$OS" == "Darwin" ]]; then
    CANONICAL="${CANONICAL}
  UseKeychain yes"
fi

FINDINGS=0
noncompliant() {
    echo "NONCOMPLIANT: $1" >&2
    FINDINGS=$((FINDINGS + 1))
}

# True when the permission bits of $1 are exactly the octal mode $2. find -perm, not stat: stat's flags
# differ between BSD and GNU.
mode_is() {
    [[ -n "$(find "$1" -prune -perm "$2" 2>/dev/null)" ]]
}

# How many Host lines in $CONFIG name $ALIAS as one of their patterns ("Host a b", "Host=a"; the keyword
# is case-insensitive, as ssh reads it). A name that merely contains the alias does not count.
count_blocks() {
    awk -v alias="$ALIAS" '
        { s = $0; sub(/^[ \t]+/, "", s); kw = s; sub(/[ \t=].*$/, "", kw) }
        tolower(kw) == "host" {
            rest = substr(s, length(kw) + 1)
            sub(/^[ \t]*=?[ \t]*/, "", rest)
            n = split(rest, pats, "[ \t]+")
            for (i = 1; i <= n; i++) if (pats[i] == alias) { count++; break }
        }
        END { print count + 0 }
    ' "$CONFIG"
}

# The first such block: its Host line through the line before the next Host or Match line, less trailing
# blank and comment lines (those introduce whatever follows).
first_block() {
    awk -v alias="$ALIAS" '
        { s = $0; sub(/^[ \t]+/, "", s); kw = s; sub(/[ \t=].*$/, "", kw); kw = tolower(kw) }
        kw == "host" || kw == "match" {
            if (inblk) done = 1
            inblk = 0
            if (!done && kw == "host") {
                rest = substr(s, length(kw) + 1)
                sub(/^[ \t]*=?[ \t]*/, "", rest)
                n = split(rest, pats, "[ \t]+")
                for (i = 1; i <= n; i++) if (pats[i] == alias) inblk = 1
            }
        }
        inblk && !done { buf[++nb] = $0 }
        END {
            while (nb > 0 && (buf[nb] ~ /^[ \t]*$/ || buf[nb] ~ /^[ \t]*#/)) nb--
            for (i = 1; i <= nb; i++) print buf[i]
        }
    ' "$CONFIG"
}

# Run `ssh [-F $1] -G $ALIAS` and compare what it resolves with the block. Returns 0 for hostname
# github.com, exactly the block's identity file, and identitiesonly yes; 1 for any difference (each one
# printed); 2 when ssh cannot evaluate the configuration.
resolve_check() {
    local cfg="$1" out rc=0 host ids only bad=0
    if [[ -n "$cfg" ]]; then
        out="$("$SSH" -F "$cfg" -G "$ALIAS" </dev/null 2>&1)" || rc=$?
    else
        out="$("$SSH" -G "$ALIAS" </dev/null 2>&1)" || rc=$?
    fi
    if [[ "$rc" -ne 0 ]]; then
        echo "ERROR: '${SSH}${cfg:+ -F ${cfg}} -G ${ALIAS}' exited ${rc}; ssh cannot evaluate the configuration:" >&2
        printf '%s\n' "$out" | sed 's/^/    /' >&2
        return 2
    fi
    host="$(printf '%s\n' "$out" | awk '$1 == "hostname" && !seen { print $2; seen = 1 }')"
    ids="$(printf '%s\n' "$out" | awk '$1 == "identityfile" { sub(/^identityfile[ \t]+/, ""); print }')"
    only="$(printf '%s\n' "$out" | awk '$1 == "identitiesonly" && !seen { print $2; seen = 1 }')"
    if [[ "$host" != "github.com" ]]; then
        echo "MISMATCH: ssh -G ${ALIAS} resolves hostname '${host:-<none>}', not github.com" >&2
        bad=1
    fi
    if [[ "$ids" != "$IDENTITY" ]]; then
        echo "MISMATCH: ssh -G ${ALIAS} resolves identityfile [$(printf '%s' "$ids" | tr '\n' ',')], not exactly ${IDENTITY}" >&2
        bad=1
    fi
    if [[ "$only" != "yes" ]]; then
        echo "MISMATCH: ssh -G ${ALIAS} resolves identitiesonly '${only:-<none>}', not yes" >&2
        bad=1
    fi
    return "$bad"
}

echo "${FULL}: alias ${ALIAS}, ssh directory ${SSH_DIR}"

# --- Assess: nothing below writes until every check has run. ---

NEED_KEY=0
if [[ -L "$KEY" || -L "$PUB" ]]; then
    noncompliant "${KEY} or its .pub is a symlink; this script manages regular files only. Inspect them by hand."
elif [[ -e "$KEY" ]]; then
    if [[ ! -f "$KEY" ]]; then
        noncompliant "${KEY} exists but is not a regular file."
    elif ! mode_is "$KEY" 600; then
        noncompliant "${KEY} is not mode 600 (left untouched). Fix: chmod 600 '${KEY}'"
    fi
    if [[ ! -e "$PUB" ]]; then
        noncompliant "${PUB} is missing: the key exists without its public half. Not regenerating it; restore the .pub, or move the key aside and re-run to create a new pair."
    elif [[ ! -f "$PUB" ]]; then
        noncompliant "${PUB} exists but is not a regular file."
    elif ! mode_is "$PUB" 644; then
        noncompliant "${PUB} is not mode 644 (left untouched). Fix: chmod 644 '${PUB}'"
    fi
    [[ "$FINDINGS" -gt 0 ]] || echo "key     ${KEY}: present, mode 600, .pub mode 644 -- left untouched"
elif [[ -e "$PUB" ]]; then
    noncompliant "${PUB} exists without its key ${KEY}. It may be the key GitHub has registered; move it aside before a new pair is created."
else
    NEED_KEY=1
    echo "key     ${KEY}: absent -- will create it"
fi

NEED_BLOCK=0
if [[ -L "$CONFIG" && ! -e "$CONFIG" ]]; then
    die_env "${CONFIG} is a dangling symlink"
elif [[ -e "$CONFIG" ]]; then
    [[ -f "$CONFIG" ]] || die_env "${CONFIG} is not a regular file"
    [[ -r "$CONFIG" ]] || die_env "${CONFIG} is not readable"
    count="$(count_blocks)"
    if [[ "$count" -eq 0 ]]; then
        NEED_BLOCK=1
        echo "config  ${CONFIG}: no Host ${ALIAS} block -- will append it"
    elif [[ "$count" -gt 1 ]]; then
        noncompliant "${CONFIG} has ${count} Host blocks naming ${ALIAS}; ssh takes each option from the first block that sets it. Merge them by hand."
    else
        existing="$(first_block)"
        if [[ "$existing" == "$CANONICAL" ]]; then
            echo "config  ${CONFIG}: Host ${ALIAS} block present and canonical -- left untouched"
        else
            noncompliant "the Host ${ALIAS} block in ${CONFIG} is not the canonical form (left untouched); '-' lines are canonical, '+' lines are the file:"
            diff -U 1000 -L "canonical" -L "${CONFIG}" <(printf '%s\n' "$CANONICAL") <(printf '%s\n' "$existing") >&2 || true
        fi
    fi
else
    NEED_BLOCK=1
    echo "config  ${CONFIG}: absent -- will create it (mode 600) with the Host ${ALIAS} block"
fi

if [[ "$FINDINGS" -gt 0 ]]; then
    echo "FAIL: ${FULL}: ${FINDINGS} non-compliant item(s), reported and not fixed; nothing was written." >&2
    exit 1
fi

if [[ "$NEED_KEY" -eq 1 || "$NEED_BLOCK" -eq 1 ]]; then
    [[ -w "$SSH_DIR" ]] || die_env "ssh directory is not writable: ${SSH_DIR}"
fi
if [[ "$NEED_BLOCK" -eq 1 && -L "$CONFIG" ]]; then
    echo "ERROR: ${CONFIG} is a symlink, and replacing it atomically would break the link. Append this block to its target by hand:" >&2
    printf '%s\n' "$CANONICAL" >&2
    exit 2
fi
if [[ "$NEED_BLOCK" -eq 1 && -e "$CONFIG" && ! -w "$CONFIG" ]]; then
    die_env "${CONFIG} is read-only; refusing to replace a file whose mode protects it"
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ "$NEED_KEY" -eq 0 && "$NEED_BLOCK" -eq 0 ]]; then
        echo "DRY-RUN: ${FULL} already configured; nothing to write (--dry-run runs no ssh -G check)"
    fi
    if [[ "$NEED_KEY" -eq 1 ]]; then
        echo "DRY-RUN: would run: ${SSH_KEYGEN} -t ed25519 -N '' -C '${TITLE}' -f '${KEY}'"
        echo "         then set mode 600 on the key and 644 on the .pub"
    fi
    if [[ "$NEED_BLOCK" -eq 1 ]]; then
        echo "DRY-RUN: would append to ${CONFIG} (a temp file in the same directory, mode 600, then mv):"
        printf '%s\n' "$CANONICAL"
    fi
    echo "DRY-RUN: would print the web-UI step for https://github.com/${OWNER}/${FULL}/settings/keys/new (title '${TITLE}')"
    echo "DRY-RUN: would check: ${SSH}${CHECK_CONFIG:+ -F ${CHECK_CONFIG}} -G ${ALIAS}"
    echo "(nothing written)"
    exit 0
fi

# --- Act. ---

TMP_CONFIG=""
trap '[[ -z "$TMP_CONFIG" ]] || rm -f -- "$TMP_CONFIG"' EXIT

FINGERPRINT=""
if [[ "$NEED_KEY" -eq 0 ]]; then
    if ! FINGERPRINT="$("$SSH_KEYGEN" -lf "$PUB" </dev/null 2>&1)"; then
        echo "NONCOMPLIANT: ${PUB} is not a public key ssh-keygen can read: ${FINGERPRINT}" >&2
        echo "FAIL: ${FULL}: 1 non-compliant item(s), reported and not fixed; nothing was written." >&2
        exit 1
    fi
fi

if [[ "$NEED_BLOCK" -eq 1 ]]; then
    TMP_CONFIG="$(mktemp "${SSH_DIR}/.config.juniper_repo_ssh_setup.XXXXXX")" || die_env "cannot create a temp file in ${SSH_DIR}"
    {
        if [[ -s "$CONFIG" ]]; then
            cat "$CONFIG"
            if [[ -n "$(tail -c 1 "$CONFIG")" ]]; then
                printf '\n\n'
            else
                last="$(tail -n 1 "$CONFIG")"
                [[ -z "${last//[[:space:]]/}" ]] || printf '\n'
            fi
        fi
        printf '%s\n' "$CANONICAL"
    } >"$TMP_CONFIG"
    chmod 600 "$TMP_CONFIG"
    rc=0
    resolve_check "$TMP_CONFIG" || rc=$?
    if [[ "$rc" -ne 0 ]]; then
        echo "FAIL: ${FULL}: the config with the new block does not resolve as the block says; ${CONFIG} left unchanged, no key created." >&2
        exit "$rc"
    fi
fi

CREATED=""
if [[ "$NEED_KEY" -eq 1 ]]; then
    if ! "$SSH_KEYGEN" -t ed25519 -N '' -C "$TITLE" -f "$KEY" </dev/null >/dev/null; then
        die_env "'${SSH_KEYGEN} -t ed25519 -N '' -C '${TITLE}' -f ${KEY}' failed; ${CONFIG} left unchanged"
    fi
    [[ -f "$KEY" && -f "$PUB" ]] || die_env "${SSH_KEYGEN} did not leave both ${KEY} and ${PUB}; ${CONFIG} left unchanged"
    chmod 600 "$KEY"
    chmod 644 "$PUB"
    FINGERPRINT="$("$SSH_KEYGEN" -lf "$PUB" </dev/null 2>&1)" || die_env "'${SSH_KEYGEN} -lf ${PUB}' failed on the key it just created: ${FINGERPRINT}"
    echo "key     created ${KEY} (600) and ${PUB} (644), comment '${TITLE}'"
    CREATED="key"
fi

if [[ "$NEED_BLOCK" -eq 1 ]]; then
    note=""
    if [[ -e "$CONFIG" ]] && ! mode_is "$CONFIG" 600; then
        note="; it was not mode 600 before"
    fi
    mv -f "$TMP_CONFIG" "$CONFIG"
    TMP_CONFIG=""
    echo "config  wrote the Host ${ALIAS} block to ${CONFIG} (mode 600${note})"
    CREATED="${CREATED:+${CREATED}, }Host block"
fi

echo
echo "Owner step: register the key as a deploy key in the GitHub web UI (this script does not)."
echo "  1. Open   https://github.com/${OWNER}/${FULL}/settings/keys/new"
echo "  2. Title  ${TITLE}"
echo "  3. Key    paste the contents of ${PUB}"
echo "  4. Check  \"Allow write access\", then press \"Add key\"."
echo "  Fingerprint (must equal the one GitHub lists): ${FINGERPRINT}"
echo "  Never use 'gh repo deploy-key add' instead: gh ties the keys it adds to its current token, and"
echo "  they are deleted when that token is revoked, so one token rotation would silently cut this host off (plan D2)."
echo

rc=0
resolve_check "$CHECK_CONFIG" || rc=$?
if [[ "$rc" -ne 0 ]]; then
    echo "FAIL: ${FULL}: ssh -G ${ALIAS} does not resolve as the block says." >&2
    exit "$rc"
fi
echo "verify  ${SSH}${CHECK_CONFIG:+ -F ${CHECK_CONFIG}} -G ${ALIAS}: hostname github.com, identityfile ${IDENTITY}, identitiesonly yes"

if [[ -z "$CREATED" ]]; then
    echo "OK: ${FULL} already configured; nothing written."
else
    echo "OK: ${FULL} configured (created: ${CREATED})."
fi
