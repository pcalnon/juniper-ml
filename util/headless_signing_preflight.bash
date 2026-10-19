#!/usr/bin/env bash
# Report whether this host is set up to sign git commits, using non-credential checks only.
#
# Project:    juniper-ml
# Sub-Project: host tooling (turing bring-up)
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-17
# Status:     permanent utility
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task B7; D3, D11;
#             regressions R-B7a, R-B7b; gate G-SIGN);
#             notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md §5
#             (the original design); tests/test_headless_signing_preflight.py
#
# Signing on this host works only when git names exactly one signing key, gpg-agent can show
# a PIN prompt to a GUI or headless caller, and the PIN stays out of external caches (plan D3).
# This script checks the configuration behind each of those without touching a credential. It
# never signs, never talks to a card and never reads key material. gpg runs only as git's
# verifier for HEAD's %G?, which needs public keys alone. Two defects it pins:
#   R-B7a  user.signingkey without a trailing '!' lets gpg pick any signing subkey of the
#          key (the 2026-07-16 ambiguity class).
#   R-B7b  a curses or tty pinentry cannot prompt from a GUI or headless process. turing's
#          gpg-agent.conf named the curses build until plan task B1.
#
# The original design also checked the card and made a test signature (--card-timeout).
# Under plan D11 an agent never touches the YubiKey, so those checks are not implemented
# here; they stay owner-run (plan tasks B3 and B5).
#
# Usage:
#   bash util/headless_signing_preflight.bash [--repo DIR] [--require-signed-head] [--timeout SECONDS]
#
# Exit codes:
#   0 -- every check passed
#   1 -- at least one check failed; every check is reported and every failure listed
#   2 -- usage or environment: a bad argument, git or gpgconf not found, not a git
#        repository, or gpgconf could not name its directories
#
# Environment:
#   GIT, GPGCONF -- the git and gpgconf binaries (default: git, gpgconf); tests override them
#   PINENTRY     -- probe this pinentry program instead of the configured one
#   GNUPGHOME    -- the GnuPG home directory (default: what gpgconf reports)
set -euo pipefail

GIT="${GIT:-git}"
GPGCONF="${GPGCONF:-gpgconf}"
PINENTRY="${PINENTRY:-}"

usage() {
    cat <<'EOF'
Usage: headless_signing_preflight.bash [--repo DIR] [--require-signed-head] [--timeout SECONDS]

Report whether this host is set up to sign git commits. Non-credential checks only: the
script never signs, never talks to a card and never reads key material. gpg runs only as
git's verifier for HEAD's %G?, which needs public keys alone. Every check is reported,
and every failure is listed.

  signing-key     user.signingkey is set and pinned with a trailing '!' (after a 16-hex
                  key id or a 40- or 64-hex fingerprint), so gpg signs with that key only
  commit-gpgsign  commit.gpgsign is true, and no D11 override disables it (below)
  tag-gpgsign     tag.gpgsign, reported only
  pinentry        the pinentry is a GUI build. The probe is the Assuan command
                  'GETINFO flavor', which never prompts. curses, tty and emacs fail, as
                  does a GUI build that falls back to one of them here, and a missing or
                  non-executable program. The program is $PINENTRY if set, else
                  pinentry-program in <homedir>/gpg-agent.conf (an absolute path), else the
                  default GnuPG would use, as 'gpgconf --list-components' names it. PATH is
                  never searched, because gpg-agent does not search it either.
  agent-socket    'gpgconf --list-dirs agent-socket' names an existing socket
  external-cache  gpg-agent.conf has an active no-allow-external-cache line; a
                  commented-out line does not count
  head-signature  git's %G? for HEAD of the repo: reported only, unless
                  --require-signed-head, which fails anything but G

The homedir is $GNUPGHOME if set, else 'gpgconf --list-dirs homedir'.

Signing disabled by construction (plan D11). Agent sessions on turing carry
GIT_CONFIG_COUNT with GIT_CONFIG_KEY_n=commit.gpgsign and GIT_CONFIG_VALUE_n=false in
their environment. git applies that over every config file, so such a session cannot
sign. The preflight reports "signing disabled by construction (D11)" and FAILS (exit 1).
That is the expected result in an agent session, which lands commits through
util/open_signed_pr.py. Run the preflight from an owner terminal to judge the host.

Owner-run, not implemented here (plan D11): the card checks of the original design,
--card-timeout (a card is present, its signature slot holds the signing subkey, and a
test signature succeeds). They need the YubiKey and its PIN, so they stay with the owner
(plan tasks B3 and B5). Passing --card-timeout exits 2.

  --repo DIR             check this repository's config and HEAD (default: the current directory)
  --require-signed-head  fail unless HEAD's signature status is G
  --timeout SECONDS      stop a probe that runs longer than this (the pinentry, and git log,
                         which runs gpg to verify HEAD); default 10
  -h, --help             show this help

Exit codes: 0 every check passed; 1 a check failed (all failures are listed);
2 usage or environment error (a bad argument, git or gpgconf not found, not a git
repository, gpgconf failed).

Environment: GIT and GPGCONF name the binaries (default git, gpgconf). PINENTRY probes
that program instead of the configured one. GNUPGHOME works as it does for GnuPG.
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

REPO="."
REQUIRE_SIGNED_HEAD=0
TIMEOUT=10

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h | --help)
            usage
            exit 0
            ;;
        --repo)
            [[ -n "${2:-}" ]] || die_usage "--repo needs a directory"
            REPO="$2"
            shift 2
            ;;
        --require-signed-head)
            REQUIRE_SIGNED_HEAD=1
            shift
            ;;
        --timeout)
            timeout_re='^[1-9][0-9]{0,3}$'
            [[ "${2:-}" =~ $timeout_re ]] || die_usage "--timeout needs whole seconds from 1 to 9999 (got '${2:-}')"
            TIMEOUT="$2"
            shift 2
            ;;
        --card-timeout | --card-timeout=*)
            die_usage "--card-timeout is not implemented: card and PIN checks are owner-run (plan D11; tasks B3 and B5)"
            ;;
        -*)
            die_usage "unknown option: $1"
            ;;
        *)
            die_usage "unexpected argument: $1"
            ;;
    esac
done

command -v "$GIT" >/dev/null 2>&1 || die_env "git not found (GIT=${GIT})"
command -v "$GPGCONF" >/dev/null 2>&1 || die_env "gpgconf not found (GPGCONF=${GPGCONF}); is GnuPG installed?"

if ! git_out="$("$GIT" -C "$REPO" rev-parse --git-dir 2>&1)"; then
    die_env "not a git repository: ${REPO} ($(printf '%s' "$git_out" | tr '\n' ' '))"
fi
TOPLEVEL="$("$GIT" -C "$REPO" rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -n "${GNUPGHOME:-}" ]]; then
    HOMEDIR="$GNUPGHOME"
    HOMEDIR_FROM="GNUPGHOME"
else
    if ! HOMEDIR="$("$GPGCONF" --list-dirs homedir 2>/dev/null)" || [[ -z "$HOMEDIR" ]]; then
        die_env "'${GPGCONF} --list-dirs homedir' failed or printed nothing"
    fi
    HOMEDIR_FROM="${GPGCONF} --list-dirs homedir"
fi
if ! AGENT_SOCKET="$("$GPGCONF" --list-dirs agent-socket 2>/dev/null)" || [[ -z "$AGENT_SOCKET" ]]; then
    die_env "'${GPGCONF} --list-dirs agent-socket' failed or printed nothing"
fi
AGENT_CONF="${HOMEDIR}/gpg-agent.conf"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/headless-signing-preflight.XXXXXX")" || die_env "mktemp failed"
trap 'rm -rf "$TMP_DIR"' EXIT

CHECKS=0
FAILURES=()

# report STATUS ID DETAIL. PASS and FAIL count as checks; INFO is reported only.
report() {
    printf '%-4s  %-14s  %s\n' "$1" "$2" "$3"
    case "$1" in
        PASS) CHECKS=$((CHECKS + 1)) ;;
        FAIL)
            CHECKS=$((CHECKS + 1))
            FAILURES+=("$2: $3")
            ;;
    esac
}

lower() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

# The spellings git reads as false.
is_false() {
    case "$(lower "$1")" in
        false | no | off | 0 | "") return 0 ;;
        *) return 1 ;;
    esac
}

# Run "$@" with stdin from $2, stdout to $3 and stderr discarded, and kill it after $1
# seconds. Bash 3.2 has no timeout builtin, and turing lacks coreutils `timeout` until plan
# task D0. Sets BOUNDED_RC and BOUNDED_TIMED_OUT.
run_bounded() {
    local secs="$1" infile="$2" outfile="$3" pid ticks=0 limit
    shift 3
    limit=$((secs * 10))
    "$@" <"$infile" >"$outfile" 2>/dev/null &
    pid=$!
    BOUNDED_TIMED_OUT=0
    while kill -0 "$pid" 2>/dev/null; do
        if [[ "$ticks" -ge "$limit" ]]; then
            kill -KILL "$pid" 2>/dev/null || true
            BOUNDED_TIMED_OUT=1
            break
        fi
        ticks=$((ticks + 1))
        sleep 0.1
    done
    BOUNDED_RC=0
    wait "$pid" 2>/dev/null || BOUNDED_RC=$?
}

# Print the value of the last active OPTION line in a gpg-agent.conf; exit 1 when there is
# none. A comment never matches: its '#' stays part of the first field, however indented.
conf_value() {
    awk -v opt="$2" '
        { sub(/\r$/, ""); sub(/^[ \t]+/, "") }
        $1 == opt {
            v = $0
            sub(/^[^ \t]+[ \t]*/, "", v)
            sub(/[ \t]+$/, "", v)
            if (v ~ /^".*"$/) v = substr(v, 2, length(v) - 2)
            val = v
            hit = 1
        }
        END { if (hit) print val; else exit 1 }
    ' "$1"
}

# The effective boolean of a git key in the repo: true, false, unset, or "not a boolean".
git_bool() {
    local out rc=0
    out="$("$GIT" -C "$REPO" config --type=bool --get "$1" 2>/dev/null)" || rc=$?
    case "$rc" in
        0) printf '%s' "$out" ;;
        1) printf 'unset' ;;
        *) printf 'not a boolean' ;;
    esac
}

# The D11 override: the environment entries of GIT_CONFIG_COUNT, which git applies over
# every config file. If the last GIT_CONFIG_KEY_<n> naming key $1 (compared without case,
# as git compares section and variable names) carries a false value, print that pair.
# printenv reads exactly the exported variables that git itself sees.
env_override_false() {
    local want="$1" count="${GIT_CONFIG_COUNT:-}" i=0 key value hit=""
    [[ "$count" =~ ^[0-9]+$ ]] || return 0
    count=$((10#$count))
    while [[ "$i" -lt "$count" ]]; do
        key="$(printenv "GIT_CONFIG_KEY_${i}")" || break
        value="$(printenv "GIT_CONFIG_VALUE_${i}")" || value=""
        if [[ "$(lower "$key")" == "$want" ]]; then
            hit=""
            if is_false "$value"; then
                hit="GIT_CONFIG_KEY_${i}=${key}, GIT_CONFIG_VALUE_${i}=${value}"
            fi
        fi
        i=$((i + 1))
    done
    printf '%s' "$hit"
}

check_signing_key() {
    local key keyspec_re='^(0[xX])?([0-9A-Fa-f]{16}|[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64})$'
    if ! key="$("$GIT" -C "$REPO" config --get user.signingkey)"; then
        report FAIL signing-key "user.signingkey is unset (plan task B4 sets it, pinned with '!')"
    elif [[ "$key" != *'!' ]]; then
        report FAIL signing-key "user.signingkey=${key} is not pinned: without a trailing '!' gpg may sign with any signing subkey of that key (R-B7a)"
    elif ! [[ "${key%'!'}" =~ $keyspec_re ]]; then
        report FAIL signing-key "user.signingkey=${key}: the '!' must follow a 16-hex key id or a 40- or 64-hex fingerprint"
    else
        report PASS signing-key "user.signingkey=${key} (pinned)"
    fi
}

check_commit_gpgsign() {
    local effective override
    effective="$(git_bool commit.gpgsign)"
    override="$(env_override_false commit.gpgsign)"
    if [[ -n "$override" ]]; then
        report FAIL commit-gpgsign "signing disabled by construction (D11): ${override}. This session cannot sign; agent sessions land commits through util/open_signed_pr.py"
    elif [[ "$effective" == "true" ]]; then
        report PASS commit-gpgsign "commit.gpgsign=true"
    else
        report FAIL commit-gpgsign "commit.gpgsign is ${effective}; it must be true (plan task B4)"
    fi
}

check_tag_gpgsign() {
    local effective override
    effective="$(git_bool tag.gpgsign)"
    override="$(env_override_false tag.gpgsign)"
    if [[ -n "$override" ]]; then
        report INFO tag-gpgsign "tag.gpgsign=${effective} (disabled by construction, D11: ${override})"
    else
        report INFO tag-gpgsign "tag.gpgsign=${effective}"
    fi
}

check_pinentry() {
    local prog from flavor base fallback=""
    if [[ -n "$PINENTRY" ]]; then
        prog="$PINENTRY"
        from="the PINENTRY override"
    elif [[ -r "$AGENT_CONF" ]] && prog="$(conf_value "$AGENT_CONF" pinentry-program)"; then
        from="pinentry-program in ${AGENT_CONF}"
        if [[ "$prog" != /* ]]; then
            report FAIL pinentry "pinentry-program '${prog}' in ${AGENT_CONF} is not an absolute path, and gpg-agent does not search PATH"
            return
        fi
    else
        # gpg-agent falls back to its compiled-in default, which gpgconf lists (percent-escaped,
        # which only matters for a ':', ',' or '%' in the path).
        prog="$("$GPGCONF" --list-components 2>/dev/null | awk -F: '$1 == "pinentry" { print $3; exit }' || true)"
        from="GnuPG's default from '${GPGCONF} --list-components'; pinentry-program is unset"
        if [[ -z "$prog" ]]; then
            report FAIL pinentry "pinentry-program is unset in ${AGENT_CONF}, and '${GPGCONF} --list-components' names no default pinentry"
            return
        fi
    fi
    if [[ ! -f "$prog" || ! -x "$prog" ]]; then
        report FAIL pinentry "${prog} (${from}) is missing or not executable"
        return
    fi

    printf 'GETINFO flavor\nBYE\n' >"${TMP_DIR}/assuan.in"
    run_bounded "$TIMEOUT" "${TMP_DIR}/assuan.in" "${TMP_DIR}/assuan.out" "$prog"
    if [[ "$BOUNDED_TIMED_OUT" -eq 1 ]]; then
        report FAIL pinentry "${prog} (${from}) did not answer 'GETINFO flavor' within ${TIMEOUT}s"
        return
    fi
    flavor="$(awk '/^D / { sub(/^D /, ""); sub(/\r$/, ""); print; exit }' "${TMP_DIR}/assuan.out")"
    if [[ -z "$flavor" ]]; then
        report FAIL pinentry "${prog} (${from}) reported no flavor: it is not a pinentry, or one too old for 'GETINFO flavor'"
        return
    fi
    # A GUI build reports e.g. "gtk-2:curses" when it falls back to curses for lack of a display.
    base="${flavor%%:*}"
    if [[ "$flavor" == *:* ]]; then
        fallback="${flavor#*:}"
    fi
    case "$base" in
        curses | tty | emacs)
            report FAIL pinentry "${prog} (${from}) is the '${base}' pinentry, a terminal UI that cannot prompt from a GUI or headless process (R-B7b)"
            return
            ;;
    esac
    case "$fallback" in
        curses | tty | emacs)
            report FAIL pinentry "${prog} (${from}) reports '${flavor}': this GUI build falls back to ${fallback} here, so it cannot prompt headless (R-B7b)"
            return
            ;;
    esac
    report PASS pinentry "${prog} reports flavor '${flavor}' (${from})"
}

check_agent_socket() {
    if [[ -S "$AGENT_SOCKET" ]]; then
        report PASS agent-socket "${AGENT_SOCKET} is a socket"
    elif [[ -e "$AGENT_SOCKET" || -L "$AGENT_SOCKET" ]]; then
        report FAIL agent-socket "${AGENT_SOCKET} exists but is not a socket"
    else
        report FAIL agent-socket "no socket at ${AGENT_SOCKET}: gpg-agent is not running (start it with '${GPGCONF} --launch gpg-agent')"
    fi
}

check_external_cache() {
    if [[ ! -r "$AGENT_CONF" ]]; then
        report FAIL external-cache "no readable ${AGENT_CONF}, so no no-allow-external-cache line (plan task B1, D11 item 3)"
    elif conf_value "$AGENT_CONF" no-allow-external-cache >/dev/null; then
        report PASS external-cache "no-allow-external-cache is set in ${AGENT_CONF}"
    elif grep -Eq '^[[:space:]]*#[[:space:]]*no-allow-external-cache([[:space:]]|$)' "$AGENT_CONF"; then
        report FAIL external-cache "no-allow-external-cache is commented out in ${AGENT_CONF}, and a comment does not count"
    else
        report FAIL external-cache "${AGENT_CONF} has no no-allow-external-cache line (plan task B1, D11 item 3)"
    fi
}

describe_sig() {
    case "$1" in
        G) echo "a good signature" ;;
        U) echo "a good signature of unknown validity" ;;
        X) echo "a good signature that has expired" ;;
        Y) echo "a good signature made by an expired key" ;;
        R) echo "a good signature made by a revoked key" ;;
        B) echo "a bad signature" ;;
        E) echo "a signature that cannot be checked, for example because its key is not in the keyring" ;;
        N) echo "no signature" ;;
        *) echo "an unrecognised status" ;;
    esac
}

check_head_signature() {
    local status="INFO" hash="" sig="" key="" detail
    if [[ "$REQUIRE_SIGNED_HEAD" -eq 1 ]]; then
        status="FAIL"
    fi
    : >"${TMP_DIR}/empty.in"
    run_bounded "$TIMEOUT" "${TMP_DIR}/empty.in" "${TMP_DIR}/head.out" \
        "$GIT" -C "$REPO" --no-pager log -1 --no-show-signature '--format=%h %G? %GK' HEAD
    if [[ "$BOUNDED_TIMED_OUT" -eq 1 ]]; then
        detail="git log did not report HEAD's signature within ${TIMEOUT}s"
    elif [[ "$BOUNDED_RC" -ne 0 ]]; then
        detail="HEAD has no commit to check"
    else
        read -r hash sig key <"${TMP_DIR}/head.out" || true
        detail="HEAD ${hash} %G?=${sig}: $(describe_sig "$sig")${key:+, key ${key}}"
        if [[ "$REQUIRE_SIGNED_HEAD" -eq 1 && "$sig" == "G" ]]; then
            status="PASS"
        fi
    fi
    if [[ "$status" == "FAIL" ]]; then
        detail="${detail} (--require-signed-head needs G)"
    fi
    report "$status" head-signature "$detail"
}

echo "headless signing preflight: non-credential checks only (card and PIN checks are owner-run; see --help)"
echo "repo       ${TOPLEVEL:-$REPO}"
echo "gnupghome  ${HOMEDIR} (from ${HOMEDIR_FROM})"
echo

check_signing_key
check_commit_gpgsign
check_tag_gpgsign
check_pinentry
check_agent_socket
check_external_cache
check_head_signature

echo
if [[ "${#FAILURES[@]}" -eq 0 ]]; then
    echo "RESULT: OK -- all ${CHECKS} checks passed"
    exit 0
fi
{
    echo "RESULT: FAILED -- ${#FAILURES[@]} of ${CHECKS} checks failed:"
    for failure in "${FAILURES[@]}"; do
        echo "  - ${failure}"
    done
} >&2
exit 1
