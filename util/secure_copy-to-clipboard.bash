#!/usr/bin/env bash
set +x  # first: under `bash -x` every later line that touches the secret would be traced to stderr
# Copy a secret to the desktop clipboard WITHOUT displaying it, verify it by sha256, clear it later.
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure (Phase D step 9, key escrow)
# Author:       Paul Calnon
# Version:      1.0.0 (2026-11-04)
# License:      MIT
#
# Built for the password-manager leg of the settings-key escrow (assessment I-40,
# notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md
# section 6.4 step 9). Companion: util/key_escrow.bash.
#
# Usage (as the DESKTOP user, never root, never via sudo):
#   util/secure_copy-to-clipboard.bash --expect <sha256-prefix> [--file PATH | --stdin]
#                                      [--clear-after SECONDS] [--any-format]
#   --expect P        4-64 hex chars. The value's sha256 must start with P, or nothing is copied
#                     (exit 3). Also read from $ESCROW_EXPECT_SHA256. Required: an unverified copy
#                     is the failure this script exists to prevent.
#   --file PATH       read the secret from PATH (exact bytes; ONE trailing newline is stripped and
#                     reported). Default: a hidden prompt on the terminal.
#   --stdin           read the secret from standard input (one line).
#   --clear-after S   clear the clipboard after S seconds if it still holds this value (default
#                     60; 0 = never).
#   --any-format      skip the shape check (default: 64 base64 chars, the shape of
#                     `openssl rand -base64 48 | tr -d '\n'`, which made the settings key).
#
# Prints the source, the length, the sha256 prefix, the tool and the clear time. Never the value.
# The value reaches the clipboard tool on stdin (a bash builtin `printf` feeds the pipe), never on
# a command line, so it is not in `ps`, /proc/*/cmdline or shell history. This script writes no
# file; wl-copy's own stdin buffer is pinned to $XDG_RUNTIME_DIR (a 0700 tmpfs), never TMPDIR.
#
# Exit codes: 0 copied and read back equal; 2 usage; 3 hash mismatch or bad shape (nothing
# copied); 4 no clipboard tool / no desktop session / run as root; 5 read-back differs.
#
# Why the 2026-11-04 stub could not be pasted into a password manager (owner report): it never
# called a clipboard tool -- its only output was a label line and a hash prefix on stdout -- and
# the host has no clipboard tool installed. The one xclip on the host lives in the
# JuniperCanopy-DEPRECATED conda env, so a pipe to `xclip` worked only when that env happened to
# be on PATH, and plain `xclip` writes the PRIMARY selection (middle-click), which Ctrl+V and a
# password manager's paste never read. This script names the CLIPBOARD selection explicitly,
# prefers wl-copy on this Wayland (GNOME) session, refuses root (root does not own the user's
# Wayland clipboard), and reads the clipboard back to prove the paste will carry the value.

set -uo pipefail
umask 077
ulimit -c 0 2>/dev/null || true   # no core dump can carry the value

readonly DEFAULT_CLEAR_AFTER=60
v=""
cleanup() { v=""; unset v; }
trap cleanup EXIT
trap 'cleanup; exit 130' INT TERM HUP

usage() { sed -n '/^# Usage/,/^# Prints/p' "$0" | sed 's/^# \{0,1\}//' | sed '$d' >&2; exit 2; }
die() { local code="$1"; shift; printf 'secure-copy: %s\n' "$*" >&2; exit "$code"; }
sha() { printf '%s' "$1" | sha256sum | cut -d' ' -f1; }

expect="${ESCROW_EXPECT_SHA256:-}" src="prompt" file="" clear_after="$DEFAULT_CLEAR_AFTER" check_shape=1
while (($#)); do
    case "$1" in
        --expect)      (($# >= 2)) || usage; expect="$2"; shift 2 ;;
        --file)        (($# >= 2)) || usage; src="file"; file="$2"; shift 2 ;;
        --stdin)       src="stdin"; shift ;;
        --clear-after) (($# >= 2)) || usage; clear_after="$2"; shift 2 ;;
        --any-format)  check_shape=0; shift ;;
        -h|--help)     usage ;;
        *)             printf 'secure-copy: unknown argument (not echoed)\n' >&2; usage ;;  # it may be a pasted secret
    esac
done

expect="${expect,,}"
[[ "$expect" =~ ^[0-9a-f]{4,64}$ ]] || die 2 "--expect needs 4-64 hex characters (or ESCROW_EXPECT_SHA256)"
[[ "$clear_after" =~ ^[0-9]+$ ]] || die 2 "--clear-after needs a whole number of seconds"
((EUID != 0)) || die 4 "run as the desktop user, not root: root does not own the session clipboard"

# --- pick the tool before reading the secret, so a missing tool costs no exposure -------------
tool=""
if [[ -n "${WAYLAND_DISPLAY:-}" ]] && command -v wl-copy >/dev/null && command -v wl-paste >/dev/null; then
    tool="wl-copy"
elif [[ -n "${DISPLAY:-}" ]] && command -v xclip >/dev/null; then
    tool="xclip"
elif [[ -n "${DISPLAY:-}" ]] && command -v xsel >/dev/null; then
    tool="xsel"
fi
[[ -n "$tool" ]] || die 4 "no clipboard tool for this session (Wayland: install wl-clipboard -- 'sudo apt install wl-clipboard' in the pcalnon shell)"

if [[ "$tool" == wl-copy ]]; then
    # wl-copy buffers stdin in $TMPDIR/wl-copy-buffer-XXXXXX/stdin and unlinks it after opening
    # (wl-clipboard src/util/files.c, src/wl-copy.c). Under this repo's TMPDIR (a disk directory
    # under the user's home) the value's blocks would stay on disk, unshredded. Point it at the
    # user's private tmpfs instead, and refuse if that is not RAM-backed.
    rt="${XDG_RUNTIME_DIR:-}"
    [[ -n "$rt" && -d "$rt" && -O "$rt" ]] || die 4 "XDG_RUNTIME_DIR is unset or not yours; wl-copy would buffer the value on disk"
    [[ "$(stat -f -c %T -- "$rt")" == tmpfs ]] || die 4 "XDG_RUNTIME_DIR ($rt) is not tmpfs; wl-copy would buffer the value on disk"
    [[ "$(stat -c %a -- "$rt")" == 700 ]] || die 4 "XDG_RUNTIME_DIR ($rt) is not 0700"
fi

clip_in()  { case "$tool" in
    wl-copy) TMPDIR="$rt" wl-copy --type text/plain ;;   # no --paste-once: a clipboard manager's read would consume it
    xclip)   xclip -selection clipboard -in ;;
    xsel)    xsel --clipboard --input ;;
    esac >/dev/null 2>&1; }   # a forked server must not hold our stdout/stderr open
clip_out() { case "$tool" in
    wl-copy) wl-paste --no-newline 2>/dev/null ;;
    xclip)   xclip -selection clipboard -out 2>/dev/null ;;
    xsel)    xsel --clipboard --output 2>/dev/null ;;
    esac; }

# --- read the secret ---------------------------------------------------------------------------
case "$src" in
    prompt)
        [[ -r /dev/tty ]] || die 2 "no terminal for the hidden prompt; use --file or --stdin"
        printf 'Paste or type the value (hidden), then Enter: ' >/dev/tty
        IFS= read -rs v </dev/tty || die 2 "nothing read"
        printf '\n' >/dev/tty ;;
    stdin)
        IFS= read -r v || [[ -n "$v" ]] || die 2 "nothing on stdin" ;;
    file)
        [[ -f "$file" && -r "$file" ]] || die 2 "not a readable regular file: $file"
        size=$(stat -c %s -- "$file")
        ((size <= 4096)) || die 3 "$file is $size bytes; a key file is one line (is this the whole escrow sheet?)"
        # $(<f) would strip EVERY trailing newline silently; read exact bytes, strip at most one.
        IFS= read -r -d '' v <"$file" || true
        if [[ "$v" == *$'\n' ]]; then v="${v%$'\n'}"; printf 'secure-copy: one trailing newline stripped from the file\n'; fi ;;
esac

[[ -n "$v" ]] || die 3 "empty value"
[[ "$v" != *[$'\n\r\t ']* ]] || die 3 "the value contains whitespace or a line break (a sheet, not a key?); nothing copied"
if ((check_shape)) && ! [[ "$v" =~ ^[A-Za-z0-9+/]{64}$ ]]; then
    die 3 "shape: ${#v} chars, expected 64 base64 characters (use --any-format for another secret); nothing copied"
fi

h="$(sha "$v")"
printf 'source=%s length=%d sha256=%s\n' "$src" "${#v}" "${h:0:16}"
[[ "$h" == "$expect"* ]] || die 3 "MISMATCH: sha256 does not start with ${expect}; nothing copied"
printf 'hash MATCH (%s)\n' "$expect"

# --- copy, then prove the clipboard holds exactly the value ------------------------------------
printf '%s' "$v" | clip_in || die 4 "$tool failed"
v=""; unset v
got=""
for _ in 1 2 3 4 5; do
    got="$(clip_out | sha256sum | cut -d' ' -f1)"
    [[ "$got" == "$h" ]] && break
    sleep 0.2
done
[[ "$got" == "$h" ]] || die 5 "read-back via $tool differs from the value (another clipboard owner?)"
printf 'clipboard=%s selection=CLIPBOARD read-back sha256 MATCH\n' "$tool"

# --- clear later, only if the clipboard still holds this value ---------------------------------
if ((clear_after > 0)); then
    CLR_TOOL="$tool" CLR_HASH="$h" CLR_AFTER="$clear_after" nohup bash -c '
        set +x; sleep "$CLR_AFTER"
        case "$CLR_TOOL" in
            wl-copy) cur=$(wl-paste --no-newline 2>/dev/null | sha256sum) ;;
            xclip)   cur=$(xclip -selection clipboard -out 2>/dev/null | sha256sum) ;;
            xsel)    cur=$(xsel --clipboard --output 2>/dev/null | sha256sum) ;;
        esac
        [[ "${cur%% *}" == "$CLR_HASH" ]] || exit 0
        case "$CLR_TOOL" in
            wl-copy) wl-copy --clear ;;
            xclip)   xclip -selection clipboard -in </dev/null ;;
            xsel)    xsel --clipboard --clear ;;
        esac' >/dev/null 2>&1 </dev/null &
    disown
    printf 'paste within %ss; the clipboard is cleared then (if it still holds this value)\n' "$clear_after"
else
    printf 'no auto-clear: clear it yourself after pasting\n'
fi
exit 0
