#!/usr/bin/env bash
# Duplicati server launcher for duplicati.service (runs as the duplicati user).
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      2.0.0 (design draft 2026-09-21)
# License:      MIT
#
# Option precedence, lowest to highest -- a later source overrides an earlier one for the SAME
# option name; distinct options accumulate:
#   1. DEFAULT_OPTS below
#   2. --option lines in the .env file        (/home/duplicati/.config/Duplicati/.env)
#   3. DAEMON_OPTS, delivered by systemd as separate argv words (EnvironmentFile=/etc/default/duplicati)
#   4. further argv words appended after DAEMON_OPTS
# KEY=VALUE lines in the .env file are exported if the name is on the allow-list below; a variable
# already present in the environment is NOT overridden (systemd's environment wins). The settings encryption key is read from
# $CREDENTIALS_DIRECTORY/settings-key when systemd supplies it (LoadCredential=), otherwise from
# SETTINGS_ENCRYPTION_KEY if the environment or the .env file set it.
# No eval. No word-splitting of file content. No secret value is ever printed -- including by
# the error paths, which print an option's NAME and its value's LENGTH only.
#
# Unknown options: this wrapper does NOT validate option names against the server's own list,
# and NEITHER DOES THE SERVER. 2.4.0.0's CommandLineArgumentValidator.ValidateArguments logs
# "Unknown option supplied: <name>" as a WARNING and continues; the only non-zero exits in
# Server/Program.cs are 100 (unhandled exception) and 102/103 (--webservice-password-init).
# So a typo in .env is a SILENT MISCONFIGURATION, not a start failure: the service comes up
# with the option ignored, and the only trace is a warning. This fails OPEN, which is the
# opposite of what this contract wants, and it is what let the glued --daemon-opts word through
# on 09-20 (section 4.3 item 9) while the server started on 8200.
# Two consequences: (1) verify every .env option name against `duplicati-cli help advanced`
# and, for server-only names, against the string table of Duplicati.Server.Implementation.dll
# -- the spelling is `--webservice-token-duration`, hyphenated, even though the C# constant is
# OPTION_WEBSERVICE_TOKENDURATION, and a misspelling would be ignored rather than refused;
# (2) after any .env change, grep the journal for "Unknown option supplied" before calling the
# start good. AC-14 pins that grep. (Lane B2 C6, corrected by round 2 Lane A.)
set -euo pipefail

readonly DUPLICATI_SERVER="${DUPLICATI_SERVER:-/usr/bin/duplicati-server}"
readonly ENV_FILE="${DUPLICATI_ENV_FILE:-/home/duplicati/.config/Duplicati/.env}"
readonly DATA_FOLDER="${DUPLICATI_DATA_FOLDER:-/home/duplicati/.config/Duplicati}"
readonly REQUIRE_MOUNT="${DUPLICATI_REQUIRE_MOUNT:-/mnt/Backups}"
readonly CRED_NAME="settings-key"
readonly ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|DUPLICATI__[A-Z0-9_]+|TMPDIR|TZ|LANG|LC_ALL)$'
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
        line="${line%$'\r'}"
        line="${line#"${line%%[![:space:]]*}"}"   # drop leading whitespace
        if [[ -z "${line}" || "${line}" == \#* ]]; then
            continue
        fi
        if is_option "${line}"; then
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

load_settings_key() {
    local cred="${CREDENTIALS_DIRECTORY:-}/${CRED_NAME}" key
    if [[ -n "${CREDENTIALS_DIRECTORY:-}" && -r "${cred}" ]]; then
        key="$(<"${cred}")"
        [[ -n "${key}" ]] || die "systemd credential ${CRED_NAME} is empty"
        export SETTINGS_ENCRYPTION_KEY="${key}"
        log "settings encryption key: systemd credential ${CRED_NAME} (${#key} chars)"
    elif [[ -n "${SETTINGS_ENCRYPTION_KEY:-}" ]]; then
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
            if [[ "${word}" =~ (password|passphrase|key|token)= ]]; then
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
