#!/usr/bin/env bash
# Duplicati server launcher for duplicati.service (runs as the duplicati user).
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      2.4.0 (2026-10-08: an empty DUPLICATI_REQUIRE_MOUNT switches the mount check off; see HISTORY)
# License:      MIT
#
# Option precedence, lowest to highest -- a later source overrides an earlier one for the SAME
# option name; distinct options accumulate:
#   1. DEFAULT_OPTS below
#   2. --option lines in the env file         (/etc/duplicati/env; D13 -- outside the data folder)
#   3. DAEMON_OPTS, delivered by systemd as separate argv words (EnvironmentFile=/etc/default/duplicati)
#   4. further argv words appended after DAEMON_OPTS
# KEY=VALUE lines in the env file are exported if the name is on the allow-list below; a variable
# already present in the environment is NOT overridden (systemd's environment wins). The settings encryption key is read from
# $CREDENTIALS_DIRECTORY/settings-key when systemd supplies it (LoadCredential=), otherwise from
# SETTINGS_ENCRYPTION_KEY if the environment or the env file set it.
#
# WHAT THE ENV FILE MAY NOT CARRY (2.2.0). The server composes an environment name for EVERY option
# at runtime -- DUPLICATI__<OPTION_WITH_UNDERSCORES>, upper-case (Server/Program.cs 971-983) -- and
# honours it whenever the option is not on argv. The first allow-list admitted that whole family,
# so `DUPLICATI__DISABLE_DB_ENCRYPTION=true` in the env file -- a file the drift gate does not
# bless, by design -- would have satisfied --require-db-encryption-key and decrypted the database
# at the next start with no "Unknown option" line for AC-14 to see (Phase B validation, Lane A).
# Nothing in the contract uses that family, so it is gone from the allow-list; and an --option line
# in the env file may not name a security option either (ENV_OPTION_DENY below): the re-key delivers
# --disable-db-encryption through a RUNTIME DROP-IN on argv (precedence 4), never through this file.
# 2.3.0: a deny list alone was the wrong shape -- round 3 found it open to --parameters-file (the
# server reads that file in-process and copies every option in it OVER argv, Program.cs 230-237,
# 1680), and 2.4.0.0 has ~47 server options, many of them posture changes (remote-control
# registration, webroot, forever tokens persisted into the database, CORS, secret providers). So an
# --option line in the env file must now ALSO be on ENV_OPTION_ALLOW, a short list of tunables that
# change no security posture; anything else belongs in DAEMON_OPTS, which the drift gate blesses.
# The deny list stays, first, so the named hazards get the specific "security option" refusal.
# No eval. No word-splitting of file content. No secret value is ever printed -- including by
# the error paths, which print an option's NAME and its value's LENGTH only.
#
# Unknown options: this wrapper does NOT validate option names against the server's own list,
# and NEITHER DOES THE SERVER. 2.4.0.0's CommandLineArgumentValidator.ValidateArguments logs
# "Unknown option supplied: <name>" as a WARNING and continues; the only non-zero exits in
# Server/Program.cs are 100 (an exception caught by Main's own handler), 102/103
# (--webservice-password-init) and 200 (single-instance lock held by another server, Program.cs
# 949/960). An exception thrown BEFORE Main's try -- the data folder's 0700 gate (Program.cs 200)
# and the --parameters-file parse (:237) among them -- is rethrown by CrashlogHelper and ends the
# process as an UNHANDLED .NET exception: the exit status is the runtime's (on Linux typically a
# SIGABRT, 134), not 100. Unverified on this host (it needs the binary).
# So a typo in DAEMON_OPTS or argv is a SILENT MISCONFIGURATION, not a start failure: the service
# comes up with the option ignored, and the only trace is a warning. This fails OPEN, which is the
# opposite of what this contract wants, and it is what let the glued --daemon-opts word through
# on 09-20 (section 4.3 item 9) while the server started on 8200. (Since 2.3.0 an env-file
# --option outside ENV_OPTION_ALLOW is refused with exit 78, so a typo THERE fails closed.)
# Two consequences: (1) verify every DAEMON_OPTS option name against `duplicati-cli help advanced`
# and, for server-only names, against the string table of Duplicati.Server.Implementation.dll
# -- the spelling is `--webservice-token-duration`, hyphenated, even though the C# constant is
# OPTION_WEBSERVICE_TOKENDURATION, and a misspelling would be ignored rather than refused;
# (2) after any env-file change, grep the journal for "Unknown option supplied" before calling the
# start good. AC-14 pins that grep. (Lane B2 C6, corrected by round 2 Lane A.)
#
# HISTORY
#   2.0.0  2026-09-21  design draft (ml#1968, landed ml#1999).
#   2.1.0  2026-10-03  env file moved to /etc/duplicati/env (round 3's D13).
#   2.2.0  2026-10-03  Phase B validation fold-in (Lane A): DUPLICATI__* dropped from the export
#                      allow-list; security options refused from the env file; --print-command
#                      redacts by option NAME (password-init= and pre-auth-tokens= were missed);
#                      option names compared case-insensitively, as the server does; exit 200 named.
#   2.3.0  2026-10-08  Phase B round-3 fold-in (R3A D-1, R3C D-3, R3C N-2, R3A N-4): env-file
#                      --option lines must be on ENV_OPTION_ALLOW (tunables only); the deny list
#                      gains parameters-file and its alias parameterfile, webservice-enable-forever-
#                      token, webservice-cors-origins and the alias webservice-allowedhostnames; a
#                      settings key with a carriage return or edge whitespace is refused (the server
#                      uses the value as-is while the hand start and the gate strip it -- one file,
#                      two keys); the exit-code gloss no longer calls every crash 100.
#   2.4.0  2026-10-08  Phase B round-4 fold-in: DUPLICATI_REQUIRE_MOUNT= (set, empty) now really
#                      switches the mount check off (`-` instead of `:-`; R4A D-1 / R4C DEFECT-1);
#                      the allow-listed welcome-page tunable is webservice-suppress-welcome-page,
#                      the server's real name (R4A D-2 -- 2.3.0 allowed a name the server does not
#                      have); every trailing CR of an env-file line is stripped and a CR anywhere
#                      else refused (R4C N-7); a NUL byte in the credential is refused (R4C N-6).
set -euo pipefail

readonly DUPLICATI_SERVER="${DUPLICATI_SERVER:-/usr/bin/duplicati-server}"
readonly ENV_FILE="${DUPLICATI_ENV_FILE:-/etc/duplicati/env}"
readonly DATA_FOLDER="${DUPLICATI_DATA_FOLDER:-/home/duplicati/.config/Duplicati}"
# `-`, not `:-` (2.4.0): a SET-BUT-EMPTY value switches the mount check off, which the installer's
# contract gate and the test suites need -- with `:-` an empty value meant /mnt/Backups again, so
# both silently depended on this host's mount and would fail on a CI runner (R4A D-1, R4C DEFECT-1).
# The unit never sets it, so production keeps the check.
readonly REQUIRE_MOUNT="${DUPLICATI_REQUIRE_MOUNT-/mnt/Backups}"
readonly CRED_NAME="settings-key"
readonly ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|TMPDIR|TZ|LANG|LC_ALL)$'
# Options the env file may never set: each one weakens or replaces the credential/encryption
# posture or the UI authentication, and each belongs on argv (DAEMON_OPTS, or the re-key's drop-in).
# parameters-file / parameterfile: the server reads that file in-process and copies its options OVER
# argv (Program.cs 49-51, 230-237, 1680) -- one line here would re-open every other entry.
# webservice-enable-forever-token PERSISTS into the database (Program.cs 658-659); the alias
# webservice-allowedhostnames is honoured whenever the main name is absent (Program.cs 690-692).
readonly ENV_OPTION_DENY='^--(disable-db-encryption|require-db-encryption-key|settings-encryption-key|allow-insecure-datafolder|webservice-password|webservice-password-init|webservice-pre-auth-tokens|webservice-reset-jwt-config|webservice-disable-signin-tokens|webservice-allowed-hostnames|webservice-allowedhostnames|webservice-interface|server-datafolder|parameters-file|parameterfile|webservice-enable-forever-token|webservice-cors-origins)(=|$)'
# The ONLY options an env-file line may set (2.3.0): tunables that change no security posture.
# Everything else -- including every option not yet invented -- belongs in DAEMON_OPTS.
readonly ENV_OPTION_ALLOW='^--(webservice-port|webservice-token-duration|webservice-timezone|log-level|log-retention|ping-pong-keepalive|disable-update-check|webservice-suppress-welcome-page)(=|$)'
# --print-command redacts a word by its option NAME, not by a substring of the value's key:
# password-init= and pre-auth-tokens= slipped through the first pattern (Lane A).
readonly REDACT_NAME='^--[^=]*(password|passphrase|key|token|secret)[^=]*='
DEFAULT_OPTS=(
    "--webservice-interface=loopback"
    "--webservice-port=8300"
    "--server-datafolder=${DATA_FOLDER}"
)

declare -A OPT_VALUE=()   # option name -> the full word ("--name=value" or bare "--name")
declare -a OPT_ORDER=()   # first-seen order, for a stable command line
PRINT_ONLY=0

log() { printf '%s: %s\n' "${0##*/}" "$*" >&2; }
die() { log "FATAL: $*"; exit 78; }   # 78 = EX_CONFIG

is_option() { [[ "$1" =~ ^--[A-Za-z0-9][A-Za-z0-9-]*(=.*)?$ ]]; }

add_opt() {
    # add_opt <source-label> <word>
    # The rejection message prints the option NAME and the value's LENGTH, never the value:
    # a mistyped --webservice-password=<secret> line in .env must not reach the journal
    # through the fail-closed path. (Lane B3 F-5.)
    local src="$1" word="$2" name
    if ! is_option "${word}"; then
        die "${src}: not a Duplicati option: '${word%%=*}' (value length ${#word})"
    fi
    name="${word%%=*}"
    name="${name,,}"   # the server's slim parser compares option names case-insensitively
    word="${name}${word:${#name}}"
    if [[ -z "${OPT_VALUE[${name}]+x}" ]]; then
        OPT_ORDER+=("${name}")
    fi
    OPT_VALUE["${name}"]="${word}"
}

strip_quotes() {
    local v="$1"
    if [[ ${#v} -ge 2 && ( "${v:0:1}" == "'" || "${v:0:1}" == '"' ) && "${v: -1}" == "${v:0:1}" ]]; then
        v="${v:1:${#v}-2}"
    fi
    printf '%s' "${v}"
}

load_env_file() {
    # Accepted lines: KEY=VALUE | export KEY=VALUE | --option[=value] | # comment | blank.
    # Anything else is a configuration error: a malformed secret line must not silently
    # become "no key".
    local file="$1" line key value n=0
    if [[ ! -e "${file}" ]]; then
        log "no env file at ${file} (skipping)"
        return 0
    fi
    [[ -r "${file}" ]] || die "env file ${file} exists but is not readable by $(id -un)"
    while IFS= read -r line || [[ -n "${line}" ]]; do
        n=$((n + 1))
        while [[ "${line}" == *$'\r' ]]; do line="${line%$'\r'}"; done   # EVERY trailing CR; 2.3.0 stripped one (R4C N-7)
        [[ "${line}" != *$'\r'* ]] || die "${file}:${n}: a carriage return inside the line (allowed only at its end)"
        line="${line#"${line%%[![:space:]]*}"}"   # drop leading whitespace
        if [[ -z "${line}" || "${line}" == \#* ]]; then
            continue
        fi
        if is_option "${line}"; then
            if [[ "${line,,}" =~ ${ENV_OPTION_DENY} ]]; then
                die "${file}:${n}: ${line%%=*} may not be set from the env file (security option; use DAEMON_OPTS or argv)"
            fi
            if [[ ! "${line,,}" =~ ${ENV_OPTION_ALLOW} ]]; then
                die "${file}:${n}: ${line%%=*} is not an env-file tunable (allowed: ${ENV_OPTION_ALLOW}); set it in DAEMON_OPTS, which the drift gate blesses"
            fi
            add_opt "${file}:${n}" "${line}"
        elif [[ "${line}" =~ ^(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[2]}"
            value="$(strip_quotes "${BASH_REMATCH[3]}")"
            # Only names the server is meant to read may be exported: this file must not be
            # able to inject LD_PRELOAD, DOTNET_STARTUP_HOOKS or PATH into a process that
            # holds CAP_DAC_READ_SEARCH.
            [[ "${key}" =~ ${ENV_EXPORT_ALLOW} ]] || die "${file}:${n}: ${key} is not an exportable name (allowed: ${ENV_EXPORT_ALLOW})"
            if [[ -n "${!key+x}" ]]; then
                log "${file}:${n}: ${key} already set in the environment; file value ignored"
            else
                export "${key}=${value}"
            fi
        else
            die "${file}:${n}: unparseable line (allowed: KEY=VALUE, export KEY=VALUE, --option[=value], # comment)"
        fi
    done < "${file}"
}

check_key_shape() {
    # check_key_shape <source-label> <key>: the server uses the value byte-for-byte (Program.cs
    # 986-987), while the password-init hand start and the re-key gate read the file in text mode,
    # which drops a CR -- so a CR (a CRLF-edited file) or edge whitespace would make one file two
    # keys (round 3 lane C N-2). Refuse both; the message names the source, never the value.
    local src="$1" key="$2"
    [[ "${key}" != *$'\r'* ]] || die "${src}: the settings key contains a carriage return; rewrite it without one"
    [[ "${key}" == "${key#[[:space:]]}" && "${key}" == "${key%[[:space:]]}" ]] || die "${src}: the settings key has leading or trailing whitespace; rewrite it without"
}

load_settings_key() {
    local cred="${CREDENTIALS_DIRECTORY:-}/${CRED_NAME}" key
    if [[ -n "${CREDENTIALS_DIRECTORY:-}" && -r "${cred}" ]]; then
        # `$(<file)` silently drops a NUL byte, while the hand start and the gate (Python) keep it:
        # one file, two keys again (R4C N-6). Refuse it before reading.
        [[ "$(wc -c < "${cred}")" -eq "$(tr -d '\000' < "${cred}" | wc -c)" ]] || die "systemd credential ${CRED_NAME} contains a NUL byte; rewrite it without one"
        key="$(<"${cred}")"
        [[ -n "${key}" ]] || die "systemd credential ${CRED_NAME} is empty"
        check_key_shape "systemd credential ${CRED_NAME}" "${key}"
        export SETTINGS_ENCRYPTION_KEY="${key}"
        log "settings encryption key: systemd credential ${CRED_NAME} (${#key} chars)"
    elif [[ -n "${SETTINGS_ENCRYPTION_KEY:-}" ]]; then
        check_key_shape "SETTINGS_ENCRYPTION_KEY" "${SETTINGS_ENCRYPTION_KEY}"
        log "settings encryption key: environment/.env (${#SETTINGS_ENCRYPTION_KEY} chars)"
    else
        log "settings encryption key: NOT SET (the server encrypts nothing new and refuses an encrypted database)"
    fi
}

preflight() {
    # preflight <effective data folder> -- the folder the server will actually receive
    # (--server-datafolder after all sources are merged), not the wrapper's default.
    local folder="$1" owner
    [[ -x "${DUPLICATI_SERVER}" ]] || die "server binary not executable: ${DUPLICATI_SERVER}"
    [[ -d "${folder}" ]] || die "data folder missing: ${folder}"
    [[ -w "${folder}" ]] || die "data folder not writable by $(id -un): ${folder}"
    owner="$(stat -c '%U' "${folder}")"
    [[ "${owner}" == "$(id -un)" ]] || die "data folder ${folder} is owned by ${owner}, not $(id -un)"
    if [[ -n "${REQUIRE_MOUNT}" ]]; then
        mountpoint -q "${REQUIRE_MOUNT}" || die "${REQUIRE_MOUNT} is not a mountpoint; refusing to start a server whose destination lives there"
    fi
}

main() {
    local word name
    local -a argv=()
    for word in "${DEFAULT_OPTS[@]}"; do add_opt "default" "${word}"; done
    load_env_file "${ENV_FILE}"
    for word in "$@"; do
        case "${word}" in
            --print-command) PRINT_ONLY=1 ;;
            *) add_opt "argv" "${word}" ;;
        esac
    done
    load_settings_key
    local eff_folder="${DATA_FOLDER}"
    if [[ -n "${OPT_VALUE[--server-datafolder]+x}" ]]; then
        eff_folder="${OPT_VALUE[--server-datafolder]#--server-datafolder=}"
    fi
    preflight "${eff_folder}"
    for name in "${OPT_ORDER[@]}"; do argv+=("${OPT_VALUE[${name}]}"); done
    if (( PRINT_ONLY )); then
        printf 'would exec: %q' "${DUPLICATI_SERVER}"
        for word in "${argv[@]}"; do
            if [[ "${word}" =~ ${REDACT_NAME} ]]; then
                printf ' %q' "${word%%=*}=<redacted>"
            else
                printf ' %q' "${word}"
            fi
        done
        printf '\n'
        exit 0
    fi
    log "exec ${DUPLICATI_SERVER} with ${#argv[@]} option(s): ${OPT_ORDER[*]}"
    exec -- "${DUPLICATI_SERVER}" "${argv[@]}"
}

main "$@"
