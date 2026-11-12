#!/usr/bin/env bash
set +x  # first: under `bash -x` the lines that handle the key would be traced to stderr
# Escrow the Duplicati settings key and clean up after it, verifying every copy by sha256.
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure (Phase D step 9's tail)
# Author:       Paul Calnon
# Version:      1.0.0 (2026-11-04)
# License:      MIT
#
# Formalizes step 9's tail of the Phase D runbook
# (notes/JUNIPER_2026-10-29_JUNIPER-ECOSYSTEM_BACKUP-PHASE-D-STEP0-TRIAL-AND-KEY-WRITE-RUNBOOK.md
# section 2.3) and the assessment's I-40 (notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-
# SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md section 6.4 step 9): escrow the key on a printed
# sheet, in the password manager and on the sda1 sibling, verify each copy by hash, shred lpr's
# spool copy, confirm /etc/duplicati/env carries no key, and shred the moved-aside .env.
# The password-manager leg uses util/secure_copy-to-clipboard.bash (desktop user, not root).
#
# Usage:
#   key_escrow.bash status                               (root) read-only report of every copy
#   key_escrow.bash write-sibling                        (root) copy the key to the sda1 sibling
#   key_escrow.bash print-sheet [--printer NAME] [--copies N]
#                                                        (root) print the settings-key sheet from memory
#   key_escrow.bash print-sheet --file PATH [--printer NAME] [--copies N]
#                                                        print an existing sheet file (the passphrase
#                                                        sheet); the spool report needs root
#   key_escrow.bash passphrases [--execute]              (pcalnon, not root) check the passphrase escrow
#                                                        (sda1 env vs the source, by sha256); --execute
#                                                        re-runs util/ad-hoc/yamaguchi_key_escrow.py,
#                                                        which rewrites the sda1 env + README and writes
#                                                        the CLEARTEXT passphrase sheet to ~/.cache
#   key_escrow.bash spool                                (root) list the CUPS spool, pair d/c files
#   key_escrow.bash verify-file PATH [--expect P]        hash a copy held in a file
#   key_escrow.bash verify-typed [--expect P]            hash a copy typed or pasted (hidden prompt)
#   key_escrow.bash cleanup --spool dNNNNN-NNN [...]     (root) shred named spool documents
#   key_escrow.bash cleanup --sheet [PATH]               (root or owner) shred the cleartext sheet
#   key_escrow.bash cleanup --old-env --escrow-verified  (root) shred the moved-aside .env
#
# The reference hash: as root, the sha256 of the credstore key itself (and --expect, if given,
# must agree with it); otherwise --expect P or $ESCROW_EXPECT_SHA256 (4-64 hex) is required.
# Nothing here prints the key, puts it on a command line, or writes it to a temporary file: the
# sheet goes to lpr on stdin, and the sibling copy is made by install(1) from the key file.
# Root subcommands run in the ROOT shell (the runbook forbids sudo there); the script never
# calls sudo.
#
# Exit codes: 0 ok / MATCH; 1 a check failed or a copy MISMATCHES; 2 usage; 3 refused (a guard).

set -uo pipefail
umask 077
ulimit -c 0 2>/dev/null || true

readonly KEY=/etc/credstore/duplicati-settings-key
readonly SIBLING_DIR=/mnt/Backups/Ubuntu/_yamaguchi_keys
readonly SIBLING="$SIBLING_DIR/duplicati-settings-key"
readonly SIBLING_OWNER=pcalnon
OWNER_HOME="$(getent passwd "$SIBLING_OWNER" | cut -d: -f6)"   # not ~: as root, ~ is /root
[[ -n "$OWNER_HOME" ]] || { printf 'key-escrow: no passwd entry for %s\n' "$SIBLING_OWNER" >&2; exit 2; }
readonly OWNER_HOME
readonly ENV_CONTRACT=/etc/duplicati/env
readonly OLD_ENV=/home/duplicati/.config/Duplicati.empty-2026-09-20/.env
readonly DEFAULT_SHEET="$OWNER_HOME/.cache/yamaguchi-key-escrow-sheet.txt"
readonly SPOOL=/var/spool/cups
readonly SHAPE='^[A-Za-z0-9+/]{64}$'   # openssl rand -base64 48 | tr -d '\n'
readonly DEFAULT_PRINTER=HP_OfficeJet_Pro_6970_540AC0_USB   # from the owner's 2026-11-04 stub
readonly DEFAULT_COPIES=3
readonly PASS_SRC="$OWNER_HOME/.config/duplicati-backup/env"
readonly PASS_SIBLING="$SIBLING_DIR/env"
PASS_TOOL="$(cd "$(dirname "$0")" && pwd)/ad-hoc/yamaguchi_key_escrow.py"
readonly PASS_TOOL

v=""
trap 'v=""; unset v' EXIT
trap 'v=""; exit 130' INT TERM HUP

usage() { sed -n '/^# Usage:/,/^# The reference/p' "$0" | sed 's/^# \{0,1\}//' | sed '$d' >&2; exit 2; }
die()  { local c="$1"; shift; printf 'key-escrow: %s\n' "$*" >&2; exit "$c"; }
need_root() { ((EUID == 0)) || die 3 "'$1' needs the root shell (no sudo in it, per the runbook)"; }
sha_str()  { printf '%s' "$1" | sha256sum | cut -d' ' -f1; }
sha_file() { sha256sum -- "$1" | cut -d' ' -f1; }

# reference hash: the credstore key when readable (root), else --expect / ESCROW_EXPECT_SHA256
ref="" expect="${ESCROW_EXPECT_SHA256:-}"
set_ref() {
    expect="${expect,,}"
    [[ -z "$expect" || "$expect" =~ ^[0-9a-f]{4,64}$ ]] || die 2 "--expect needs 4-64 hex characters"
    if ((EUID == 0)) && [[ -r "$KEY" ]]; then
        ref="$(sha_file "$KEY")"
        [[ -z "$expect" || "$ref" == "$expect"* ]] || die 1 "the credstore key's sha256 (${ref:0:16}) does not start with --expect $expect"
    else
        [[ -n "$expect" ]] || die 2 "not root: give --expect <sha256-prefix> (or ESCROW_EXPECT_SHA256)"
        ref="$expect"
    fi
}
verdict() {  # $1 = full hash of a candidate, $2 = label
    if [[ "$1" == "$ref"* ]]; then printf '%-28s sha256=%s MATCH\n' "$2" "${1:0:16}"; return 0; fi
    printf '%-28s sha256=%s MISMATCH (want %s)\n' "$2" "${1:0:16}" "${ref:0:16}"; return 1
}
check_key_file() {
    [[ -f "$KEY" ]] || die 1 "$KEY missing"
    local st; st="$(stat -c '%a %U:%G %s' -- "$KEY")"
    printf 'credstore key                %s\n' "$st"
    [[ "$st" == "600 root:root 64" ]] || die 1 "$KEY must be 600 root:root, 64 bytes"
    IFS= read -r -d '' v <"$KEY" || true
    [[ "$v" =~ $SHAPE ]] || { v=""; die 1 "$KEY is not 64 base64 characters on one line (no newline)"; }
    v=""
}

# --- spool helpers (names, sizes, times only; never contents) -----------------------------------
active_jobs() { lpstat -o 2>/dev/null | awk '{print $1}' | sed -E 's/.*-([0-9]+)$/\1/'; }
list_spool() {
    local f n id paired act; act=" $(active_jobs | tr '\n' ' ') "
    for f in "$SPOOL"/d*; do
        [[ -e "$f" ]] || continue
        n="${f##*/}"; id="${n#d}"; id="${id%%-*}"; id=$((10#$id))
        paired="orphan"; [[ -e "$SPOOL/c$(printf '%05d' "$id")" ]] && paired="paired"
        [[ "$act" == *" $id "* ]] && paired="$paired,ACTIVE"
        printf '  %-14s %8s B  %s  %s\n' "$n" "$(stat -c %s -- "$f")" "$(stat -c %y -- "$f" | cut -c1-19)" "$paired"
    done
}
count_env_files() {  # the stub's count: every .env* beside the moved-aside .env (nullglob, no ls|grep)
    local -a m=(); local saved; saved="$(shopt -p nullglob)"; shopt -s nullglob
    m=("${OLD_ENV%/*}"/.env*); eval "$saved"; printf '%d' "${#m[@]}"
}
spool_dnames() { local f; for f in "$SPOOL"/d*; do [[ -e "$f" ]] && printf '%s\n' "${f##*/}"; done; }

# --- subcommands --------------------------------------------------------------------------------
cmd_status() {
    need_root status; set_ref; local rc=0 n
    check_key_file
    printf 'reference                    sha256=%s\n' "${ref:0:16}"
    if [[ -f "$SIBLING" ]]; then
        printf 'sda1 sibling                 %s\n' "$(stat -c '%a %U:%G %s' -- "$SIBLING")"
        verdict "$(sha_file "$SIBLING")" "sda1 sibling" || rc=1
    else
        printf 'sda1 sibling                 ABSENT (%s)\n' "$SIBLING"; rc=1
    fi
    if [[ -f "$ENV_CONTRACT" ]]; then
        n="$(grep -cE '^[[:space:]]*#?[[:space:]]*(export[[:space:]]+)?[A-Z_]*(KEY|PASSWORD|PASSPHRASE|SECRET)[A-Z_]*[[:space:]]*=' -- "$ENV_CONTRACT")"
        printf 'env contract key assignments %s (want 0; commented ones counted)\n' "$n"
        ((n == 0)) || rc=1
    else
        printf 'env contract                 ABSENT (%s)\n' "$ENV_CONTRACT"; rc=1
    fi
    if [[ -e "$OLD_ENV" ]]; then printf 'moved-aside .env             PRESENT (shred after escrow)\n'
    else printf 'moved-aside .env             gone\n'; fi
    if [[ -e "$DEFAULT_SHEET" ]]; then printf 'cleartext sheet              PRESENT %s -- cleartext under the owner home: shred after printing\n' "$(stat -c '%a %U %s' -- "$DEFAULT_SHEET")"
    else printf 'cleartext sheet              gone\n'; fi
    printf 'spool documents:\n'; list_spool
    printf 'not checkable here: the printed sheet and the password manager -- verify-typed each\n'
    return "$rc"
}

cmd_write_sibling() {
    need_root write-sibling; set_ref; check_key_file
    [[ -d "$SIBLING_DIR" ]] || die 3 "$SIBLING_DIR missing -- stop and report; not creating it"
    [[ "$(stat -c '%a %U' -- "$SIBLING_DIR")" == "700 $SIBLING_OWNER" ]] || die 3 "$SIBLING_DIR is not 0700 $SIBLING_OWNER"
    if [[ -e "$SIBLING" ]]; then
        cmp -s -- "$KEY" "$SIBLING" && { printf 'sibling already current\n'; verdict "$(sha_file "$SIBLING")" "sda1 sibling"; return; }
        die 3 "$SIBLING exists and differs -- refusing to overwrite an escrowed key"
    fi
    install -m 0600 -o "$SIBLING_OWNER" -g "$SIBLING_OWNER" -T -- "$KEY" "$SIBLING" || die 1 "install failed"
    sync -f -- "$SIBLING" 2>/dev/null || sync
    cmp -s -- "$KEY" "$SIBLING" || die 1 "sibling differs from the key after the write"
    printf 'sda1 sibling written         %s\n' "$(stat -c '%a %U:%G %s' -- "$SIBLING")"
    verdict "$(sha_file "$SIBLING")" "sda1 sibling"
}

sheet() {  # composes the sheet on stdout; the key is read here and only here
    local i
    IFS= read -r -d '' v <"$KEY" || true
    printf 'YAMAGUCHI -- DUPLICATI SETTINGS ENCRYPTION KEY (Tier 1 server database)\n\n'
    printf 'Host: %s   Printed: %s\n' "$(hostname -s)" "$(date -u +%Y-%m-%dT%H:%MZ)"
    printf 'Installed at: %s (systemd LoadCredential settings-key)\n' "$KEY"
    printf 'Unlocks: /home/duplicati/.config/Duplicati/Duplicati-server.sqlite. It is NOT the backup passphrase.\n\n'
    printf 'Key: 64 characters in 8 groups of 8. Type the groups with no spaces and no newline.\n'
    printf 'Alphabet: A-Z a-z 0-9 + /   (watch 0/O, 1/l/I, 5/S, 8/B)\n\n'
    for i in 0 1 2 3 4 5 6 7; do printf '  %d:  %s\n' "$((i + 1))" "${v:i*8:8}"; done
    printf '\nsha256 prefix of the key: %s\n' "${ref:0:16}"
    printf 'Verify a re-typed copy:  util/key_escrow.bash verify-typed --expect %s\n' "${ref:0:16}"
    v=""
}

cmd_print_sheet() {
    local printer="$DEFAULT_PRINTER" copies="$DEFAULT_COPIES" file="" before="" after new spool_ok=0
    while (($#)); do case "$1" in
        --printer) (($# >= 2)) || usage; printer="$2"; shift 2 ;;
        --copies)  (($# >= 2)) || usage; copies="$2"; shift 2 ;;
        --file)    (($# >= 2)) || usage; file="$2"; shift 2 ;;
        *) usage ;;
    esac; done
    [[ "$copies" =~ ^[1-9]$ ]] || die 2 "--copies takes 1-9"
    command -v lpr >/dev/null && command -v lpstat >/dev/null || die 3 "lpr/lpstat not found -- stop and report"
    # preflight BEFORE the key is read: the stub's lpr would fail only after hashing and printing began
    lpstat -p "$printer" >/dev/null 2>&1 || die 3 "printer '$printer' is not a CUPS destination (lpstat -p lists them; 'No destinations added' means none)"
    if [[ -n "$file" ]]; then
        [[ -f "$file" && -r "$file" && ! -L "$file" ]] || die 2 "not a readable regular file: $file"
    else
        need_root print-sheet; set_ref; check_key_file
    fi
    [[ -r "$SPOOL" && -x "$SPOOL" ]] && spool_ok=1
    ((spool_ok)) && before="$(spool_dnames)"
    if [[ -n "$file" ]]; then
        lpr -P "$printer" -# "$copies" -T escrow-sheet <"$file" || die 1 "lpr failed"
    else
        sheet | lpr -P "$printer" -# "$copies" -T escrow-sheet || die 1 "lpr failed"
    fi
    printf 'print exit=0 printer=%s copies=%s\n' "$printer" "$copies"
    if ((spool_ok)); then
        sleep 2
        after="$(spool_dnames)"
        new="$(comm -13 <(sort <<<"$before") <(sort <<<"$after") | sed '/^$/d')"
        printf 'new spool documents (each holds the secrets):\n'
        if [[ -n "$new" ]]; then printf '  %s\n' $new; else printf '  none seen yet -- run: key_escrow.bash spool\n'; fi
    else
        printf 'spool not readable as this user: in the root shell run key_escrow.bash spool\n'
    fi
    printf 'when the sheets are in hand: (root) key_escrow.bash cleanup --spool <name> ...\n'
    [[ -n "$file" ]] && printf 'then: key_escrow.bash cleanup --sheet %s\n' "$file"
    return 0
}

cmd_passphrases() {
    ((EUID != 0)) || die 3 "run 'passphrases' as pcalnon: the source and the sheet live in pcalnon's home (as root, ~ is /root)"
    local execute=0 hs hd
    while (($#)); do case "$1" in --execute) execute=1; shift ;; *) usage ;; esac; done
    if ((execute)); then
        [[ -f "$PASS_TOOL" ]] || die 3 "$PASS_TOOL missing -- stop and report"
        python3 -I "$PASS_TOOL" --execute || die 1 "yamaguchi_key_escrow.py failed"
    fi
    [[ -f "$PASS_SRC" ]] || die 1 "$PASS_SRC missing"
    printf 'passphrase source            %s\n' "$(stat -c '%a %U:%G %s' -- "$PASS_SRC")"
    hs="$(sha_file "$PASS_SRC")"
    if [[ -f "$PASS_SIBLING" ]]; then
        printf 'passphrase sda1 copy         %s\n' "$(stat -c '%a %U:%G %s' -- "$PASS_SIBLING")"
        hd="$(sha_file "$PASS_SIBLING")"
        if [[ "$hd" == "$hs" ]]; then printf 'passphrase escrow            sha256=%s MATCH\n' "${hs:0:16}"
        else printf 'passphrase escrow            MISMATCH (source %s, copy %s)\n' "${hs:0:16}" "${hd:0:16}"; return 1; fi
    else
        printf 'passphrase sda1 copy         ABSENT (%s)\n' "$PASS_SIBLING"; return 1
    fi
    if [[ -e "$DEFAULT_SHEET" ]]; then
        printf 'passphrase sheet             PRESENT %s (CLEARTEXT: print-sheet --file it, then cleanup --sheet)\n' "$(stat -c '%a %s %y' -- "$DEFAULT_SHEET" | cut -c1-30)"
    else
        printf 'passphrase sheet             gone\n'
    fi
}

cmd_spool() { need_root spool; printf 'spool documents in %s:\n' "$SPOOL"; list_spool; }

cmd_verify_file() {
    (($# >= 1)) || usage
    local f="$1" h hs; shift
    while (($#)); do case "$1" in --expect) (($# >= 2)) || usage; expect="$2"; shift 2 ;; *) usage ;; esac; done
    set_ref
    [[ -f "$f" && -r "$f" ]] || die 2 "not a readable regular file: $f"
    printf 'file                         %s\n' "$(stat -c '%a %U:%G %s' -- "$f")"
    h="$(sha_file "$f")"
    verdict "$h" "exact bytes" && return 0
    IFS= read -r -d '' v <"$f" || true
    if [[ "$v" == *$'\n' ]]; then
        hs="$(sha_str "${v%$'\n'}")"; v=""
        verdict "$hs" "without trailing newline" && { printf 'the copy matches only after its trailing newline is removed: rewrite it without one\n'; return 1; }
    fi
    v=""; return 1
}

cmd_verify_typed() {
    while (($#)); do case "$1" in --expect) (($# >= 2)) || usage; expect="$2"; shift 2 ;; *) usage ;; esac; done
    set_ref
    [[ -r /dev/tty ]] || die 2 "no terminal for the hidden prompt"
    printf 'Type or paste the key (hidden; spaces between groups are ignored), then Enter: ' >/dev/tty
    IFS= read -rs v </dev/tty || die 2 "nothing read"; printf '\n' >/dev/tty
    v="${v//[[:space:]]/}"
    local len=${#v} shape=ok h
    [[ "$v" =~ $SHAPE ]] || shape="NOT 64 base64 chars"
    h="$(sha_str "$v")"; v=""
    printf 'length=%d shape=%s\n' "$len" "$shape"
    verdict "$h" "typed copy"
}

cmd_cleanup() {
    (($#)) || usage
    local mode="" names=() sheet_path="$DEFAULT_SHEET" escrow_ok=0 n id act f
    while (($#)); do
        case "$1" in
            --spool)   mode=spool; shift; while (($#)) && [[ "$1" != --* ]]; do names+=("$1"); shift; done ;;
            --sheet)   mode=sheet; shift; if (($#)) && [[ "$1" != --* ]]; then sheet_path="$1"; shift; fi ;;
            --old-env) mode=old-env; shift ;;
            --escrow-verified) escrow_ok=1; shift ;;
            *) usage ;;
        esac
    done
    case "$mode" in
        spool)
            need_root "cleanup --spool"; ((${#names[@]})) || usage
            act=" $(active_jobs | tr '\n' ' ') "
            for n in "${names[@]}"; do
                [[ "$n" =~ ^d[0-9]{5,}-[0-9]{3}$ ]] || die 3 "'$n' is not a spool document name (dNNNNN-NNN)"
                f="$SPOOL/$n"; [[ -f "$f" && ! -L "$f" ]] || die 3 "$f is not a regular file"
                id="${n#d}"; id=$((10#${id%%-*}))
                [[ "$act" == *" $id "* ]] && die 3 "job $id is still queued or printing; wait for it"
            done
            for n in "${names[@]}"; do
                shred -u -- "$SPOOL/$n" && [[ ! -e "$SPOOL/$n" ]] || die 1 "shred of $n failed"
                printf 'shredded %s\n' "$n"
            done
            printf 'spool now:\n'; list_spool ;;
        sheet)
            ((EUID == 0)) || [[ -O "$sheet_path" ]] || die 3 "not root and not the owner of $sheet_path"
            [[ -f "$sheet_path" && ! -L "$sheet_path" ]] || die 3 "$sheet_path is not a regular file"
            [[ "$sheet_path" == /home/* ]] || die 3 "--sheet takes a file under /home (the cleartext sheet), got $sheet_path"
            shred -u -- "$sheet_path" && [[ ! -e "$sheet_path" ]] || die 1 "shred failed"
            printf 'shredded %s\n' "$sheet_path" ;;
        old-env)
            need_root "cleanup --old-env"; set_ref
            ((escrow_ok)) || die 3 "pass --escrow-verified once the sheet and the password manager each read MATCH (verify-typed)"
            [[ -f "$SIBLING" ]] && cmp -s -- "$KEY" "$SIBLING" || die 3 "the sda1 sibling is absent or differs: escrow it first (write-sibling)"
            [[ -e "$OLD_ENV" ]] || { printf '%s already gone\n' "$OLD_ENV"; return 0; }
            [[ -f "$OLD_ENV" && ! -L "$OLD_ENV" ]] || die 3 "$OLD_ENV is not a regular file"
            printf '.env* entries before: %s\n' "$(count_env_files)"
            shred -u -- "$OLD_ENV" && [[ ! -e "$OLD_ENV" ]] || die 1 "shred failed"
            printf 'env shred exit=0; %s gone\n' "$OLD_ENV"
            printf '.env* entries after:  %s (any left are other .env* files: name them, do not shred blind)\n' "$(count_env_files)" ;;
        *) usage ;;
    esac
}

(($#)) || usage
sub="$1"; shift
case "$sub" in
    status)        cmd_status "$@" ;;
    write-sibling) cmd_write_sibling "$@" ;;
    print-sheet)   cmd_print_sheet "$@" ;;
    passphrases)   cmd_passphrases "$@" ;;
    spool)         cmd_spool "$@" ;;
    verify-file)   cmd_verify_file "$@" ;;
    verify-typed)  cmd_verify_typed "$@" ;;
    cleanup)       cmd_cleanup "$@" ;;
    -h|--help)     usage ;;
    *)             usage ;;
esac
