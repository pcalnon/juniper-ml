#!/usr/bin/env bash
# Refuse to serve juniper-recurrence from an env whose recurrence dependency closure is stale.
#
# Project:      juniper-ml
# Sub-Project:  experiment tooling
# Application:  recurrence env preflight (run by util/experiment_stack.bash and util/isolated_stack.bash)
# Author:       Paul Calnon
# Version:      1.0.0
# License:      MIT License
#
# W0.2 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
# (closes F-E2 and the launcher half of F-E5). Both launchers used to accept the recurrence env on
# two signals: the `juniper-recurrence` console script existing, and `/v1/health/ready` answering.
# On 2026-10-03 the default env, JuniperCascor1, served juniper-recurrence-model 0.1.5 (no
# `derive_full_split`) and juniper-service-core 0.5.0 under an app pinned `>=0.3.0,<0.4.0` and
# `>=0.6.0,<0.8.0`. Readiness passed, and every `POST /v1/crossval` then failed 422 with
# `missing required key 'X_full'` (F-E1). This script is the check those two signals are not.
#
# Three checks. Every one runs as `<python> -s ...`, so a package in ~/.local cannot mask a gap in
# the env itself (parent AGENTS.md, Conda note), and from `/`, so the caller's working directory
# cannot shadow an installed module the way a checkout would (`-c` and `-m` put the CWD first on
# sys.path):
#
#   1. `pip check`, SCOPED to the recurrence dependency closure (CLOSURE below). A line is a
#      finding when the distribution that has the requirement, or the installed one named after
#      "but you have", is in the closure. Every other line is printed as unrelated and never
#      refuses: JuniperCascor1's `pip check` also carries CUDA conflicts ("cuda-python 13.4.1 has
#      requirement cuda-bindings~=13.4.1, but you have cuda-bindings 13.4.1a0.") that have nothing
#      to do with recurrence. A `pip check` that cannot run at all is a finding: a scan that did
#      not run is not a clean one.
#   2. Version pins: the juniper-recurrence-model and juniper-service-core specifiers declared by
#      the INSTALLED juniper-recurrence (`importlib.metadata.requires`; for an editable install
#      that is its pyproject.toml as of the last install), evaluated with `packaging` -- the
#      distribution if importable, else pip's vendored copy. With neither, the probe says so and
#      pip check's verdict stands.
#   3. Import probe: `from juniper_recurrence_model.data import derive_full_split`.
#
# A refusal prints every finding with the interpreter's own text (pip check lines and the
# exception line exactly as printed) and ends with
#   ENV PREFLIGHT REFUSED: <n> finding(s); fix the env or pass --skip-env-preflight
# `--skip` still runs every check, prints each finding as
#   WARNING: ENV PREFLIGHT SKIPPED — <finding>
# and exits 0, so an emergency launch is loud in the run's log rather than silent.
#
# This file is committed 0644 (a GitHub-signed API commit carries no file mode), so run it with
# `bash`:
#   bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python [--skip]
#
# Exit 0 clean (or --skip) · 1 refused · 2 misuse.
set -euo pipefail

SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# The distribution `serve` belongs to, and the two of its pins that F-E1 found violated.
APP_DIST="juniper-recurrence"
PINNED_DISTS=(juniper-recurrence-model juniper-service-core)

# The recurrence dependency closure (plan W0.2), as PEP 503 canonical names.
CLOSURE=(juniper-recurrence juniper-recurrence-model juniper-recurrence-client juniper-service-core juniper-observability juniper-data-client juniper-model-core)

IMPORT_PROBE="from juniper_recurrence_model.data import derive_full_split"
SKIP_MARKER="WARNING: ENV PREFLIGHT SKIPPED —"

# The version-pin probe, run as `<python> -s -c "${PIN_PROBE}" <app> <dist>...`. One protocol
# line per result, which check_pins turns into prose (a specifier is empty for a bare name):
#   APP <app version> <packaging source>
#   OK|BAD|INVALID <dist> <installed> <specifier>     MISSING <dist> <specifier>
#   NOREQ <dist>     NOAPP     NOPACKAGING
# Only unconditional requirements count: `juniper-recurrence-model[torch]...; extra == "torch"`
# is not a pin `serve` needs. Its first line names it, so a test double can recognise the call.
PIN_PROBE="$(
    cat <<'PY'
# recurrence_env_preflight version-pin probe
import re
import sys
from importlib import metadata


def canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


app, pinned = sys.argv[1], sys.argv[2:]
try:
    from packaging.requirements import Requirement
    from packaging.version import InvalidVersion, Version

    source = "packaging"
except ImportError:
    try:
        from pip._vendor.packaging.requirements import Requirement
        from pip._vendor.packaging.version import InvalidVersion, Version

        source = "pip._vendor.packaging"
    except ImportError:
        print("NOPACKAGING")
        sys.exit(0)
try:
    app_version = metadata.version(app)
    declared = metadata.requires(app) or []
except metadata.PackageNotFoundError:
    print("NOAPP")
    sys.exit(0)
print("APP", app_version, source)
for name in pinned:
    reqs = []
    for raw in declared:
        try:
            req = Requirement(raw)
        except Exception:
            continue
        if canonical(req.name) != canonical(name):
            continue
        if req.marker is not None and not req.marker.evaluate({"extra": ""}):
            continue
        reqs.append(req)
    if not reqs:
        print("NOREQ", name)
        continue
    try:
        installed = metadata.version(name)
    except metadata.PackageNotFoundError:
        installed = None
    for req in reqs:
        spec = str(req.specifier)
        if installed is None:
            print("MISSING", name, spec)
            continue
        try:
            ok = req.specifier.contains(Version(installed), prereleases=True)
        except InvalidVersion:
            print("INVALID", name, installed, spec)
            continue
        print("OK" if ok else "BAD", name, installed, spec)
PY
)"

PYTHON=""
SKIP=0
FINDING_COUNT=0


usage() {
    cat <<USAGE
${SCRIPT_NAME} — refuse to serve juniper-recurrence from a stale env (plan W0.2)

Usage: bash ${SCRIPT_NAME} --python PATH [--skip]
       bash ${SCRIPT_NAME} --help

  --python PATH  The interpreter juniper-recurrence will serve from (required).
  --skip         Run every check, but report each finding as a WARNING and exit 0.
  --help,-h      Print this help.

Checks, each as 'PATH -s ...' from /:
  1. pip check, scoped to the recurrence closure: ${CLOSURE[*]}
  2. the ${PINNED_DISTS[*]} pins declared by the installed ${APP_DIST}
  3. ${IMPORT_PROBE}

Exit 0 clean (or --skip) · 1 refused · 2 misuse.
USAGE
}

say() { printf '%s\n' "$*"; }

misuse() {
    printf '%s: %s\n' "${SCRIPT_NAME}" "$*" >&2
    usage >&2
    exit 2
}

# Report one finding. Refusing mode prints it as FINDING; --skip prints the loud WARNING form.
finding() {
    FINDING_COUNT=$(( FINDING_COUNT + 1 ))
    if (( SKIP == 1 )); then
        say "${SKIP_MARKER} $1"
    else
        say "FINDING: $1"
    fi
}

# PEP 503 normalisation: case-insensitive, and runs of '-', '_' and '.' are equivalent.
canonical_name() {
    local name="${1,,}"
    name="${name//_/-}"
    name="${name//./-}"
    while [[ "${name}" == *--* ]]; do
        name="${name//--/-}"
    done
    printf '%s' "${name}"
}

in_closure() {
    local name member
    name="$(canonical_name "$1")"
    for member in "${CLOSURE[@]}"; do
        if [[ "${name}" == "${member}" ]]; then
            return 0
        fi
    done
    return 1
}

# The last non-empty line of a block of output: for a traceback, the exception line.
last_line() {
    local line last=""
    while IFS= read -r line; do
        if [[ -n "${line}" ]]; then
            last="${line}"
        fi
    done <<<"$1"
    printf '%s' "${last}"
}

check_interpreter() {
    if [[ -d "${PYTHON}" || ! -x "${PYTHON}" ]]; then
        finding "interpreter not found or not executable: ${PYTHON}"
        return 1
    fi
}

# 1. pip check, scoped. The grammar is pip's own (pip/_internal/commands/check.py and
# operations/check.py): "has requirement ..., but you have ...", "requires ..., which is not
# installed.", "is not supported on this platform", and the "Error parsing dependencies of ..."
# warning, which also makes pip check exit 1.
check_pip() {
    local out="" rc=0 line requiring installed recognised=0 kept=0 unrelated=0
    local conflict_re='^([^[:space:]]+) [^[:space:]]+ has requirement .+, but you have ([^[:space:]]+) [^[:space:]]+\.$'
    local missing_re='^([^[:space:]]+) [^[:space:]]+ requires [^[:space:]]+, which is not installed\.$'
    local platform_re='^([^[:space:]]+) [^[:space:]]+ is not supported on this platform\.?$'
    local parse_re='^(WARNING: )?Error parsing dependencies of ([^[:space:]:]+):'
    out="$(PIP_DISABLE_PIP_VERSION_CHECK=1 "${PYTHON}" -s -m pip check 2>&1)" || rc=$?
    while IFS= read -r line; do
        if [[ -z "${line}" || "${line}" == "No broken requirements found." ]]; then
            continue
        fi
        requiring=""
        installed=""
        if [[ "${line}" =~ ${conflict_re} ]]; then
            requiring="${BASH_REMATCH[1]}"
            installed="${BASH_REMATCH[2]}"
        elif [[ "${line}" =~ ${missing_re} ]]; then
            requiring="${BASH_REMATCH[1]}"
        elif [[ "${line}" =~ ${platform_re} ]]; then
            requiring="${BASH_REMATCH[1]}"
        elif [[ "${line}" =~ ${parse_re} ]]; then
            requiring="${BASH_REMATCH[2]}"
        else
            # Outside that grammar: a pip WARNING / DEPRECATION, or wording a later pip changed.
            # One that leads with a closure distribution is still a finding, so a reworded
            # closure conflict cannot read as clean.
            if in_closure "${line%% *}"; then
                kept=$(( kept + 1 ))
                finding "${line}"
            else
                say "ENV PREFLIGHT: pip check also said (not a finding): ${line}"
            fi
            continue
        fi
        recognised=$(( recognised + 1 ))
        if in_closure "${requiring}" || { [[ -n "${installed}" ]] && in_closure "${installed}"; }; then
            kept=$(( kept + 1 ))
            finding "${line}"
        else
            unrelated=$(( unrelated + 1 ))
            say "ENV PREFLIGHT: unrelated to recurrence (not a finding): ${line}"
        fi
    done <<<"${out}"
    if (( rc != 0 && recognised == 0 && kept == 0 )); then
        local reason
        reason="$(last_line "${out}")"
        finding "pip check could not run (exit ${rc}): ${reason:-no output}"
        return 0
    fi
    say "ENV PREFLIGHT: pip check: ${kept} recurrence-closure line(s), ${unrelated} unrelated line(s)"
}

# 2. The pins the installed juniper-recurrence declares.
check_pins() {
    local out="" rc=0 line kind dist installed spec rest app_version="?" protocol=0 reason
    out="$("${PYTHON}" -s -c "${PIN_PROBE}" "${APP_DIST}" "${PINNED_DISTS[@]}" 2>&1)" || rc=$?
    while IFS= read -r line; do
        if [[ -z "${line}" ]]; then
            continue
        fi
        kind="" dist="" installed="" spec="" rest=""
        read -r kind dist installed spec rest <<<"${line}"
        case "${kind}" in
            APP)
                protocol=1
                app_version="${dist}"
                say "ENV PREFLIGHT: pins declared by ${APP_DIST} ${app_version} (evaluated with ${installed})"
                ;;
            OK)
                protocol=1
                say "ENV PREFLIGHT: pin ok: ${dist} ${installed} satisfies ${dist}${spec}"
                ;;
            BAD)
                protocol=1
                finding "version pin: ${dist} ${installed} is installed; ${APP_DIST} ${app_version} requires ${dist}${spec}"
                ;;
            INVALID)
                protocol=1
                finding "version pin: ${dist} ${installed} is not a PEP 440 version, so ${APP_DIST} ${app_version}'s ${dist}${spec} cannot be checked"
                ;;
            MISSING)
                # MISSING carries no installed version, so its specifier is the third field.
                protocol=1
                finding "version pin: ${dist} is not installed; ${APP_DIST} ${app_version} requires ${dist}${installed}"
                ;;
            NOREQ)
                protocol=1
                say "ENV PREFLIGHT: ${APP_DIST} declares no unconditional requirement on ${dist}; no pin to check"
                ;;
            NOAPP)
                protocol=1
                finding "version pin: ${APP_DIST} has no distribution metadata in this interpreter, so its pins cannot be read (is this the env serve runs from?)"
                ;;
            NOPACKAGING)
                protocol=1
                say "ENV PREFLIGHT: packaging is importable neither as a distribution nor as pip's vendored copy; the pin check falls back to pip check's verdict"
                ;;
            *)
                say "ENV PREFLIGHT: pin probe also said: ${line}"
                ;;
        esac
    done <<<"${out}"
    if (( rc != 0 || protocol == 0 )); then
        reason="$(last_line "${out}")"
        finding "version-pin probe failed (exit ${rc}): ${reason:-no output}"
    fi
}

# 3. The symbol F-E1's stale model lacked.
check_import() {
    local out="" rc=0 reason
    out="$("${PYTHON}" -s -c "${IMPORT_PROBE}" 2>&1)" || rc=$?
    if (( rc == 0 )); then
        say "ENV PREFLIGHT: import ok: ${IMPORT_PROBE}"
        return 0
    fi
    reason="$(last_line "${out}")"
    finding "import probe '${IMPORT_PROBE}' failed (exit ${rc}): ${reason:-no output}"
}

verdict() {
    if (( FINDING_COUNT == 0 )); then
        if (( SKIP == 1 )); then
            say "ENV PREFLIGHT OK: no findings (--skip had nothing to override)"
        else
            say "ENV PREFLIGHT OK: no findings"
        fi
        exit 0
    fi
    if (( SKIP == 1 )); then
        say "${SKIP_MARKER} ${FINDING_COUNT} finding(s) ignored; juniper-recurrence will serve from an env that FAILED its preflight"
        exit 0
    fi
    say "ENV PREFLIGHT REFUSED: ${FINDING_COUNT} finding(s); fix the env or pass --skip-env-preflight"
    exit 1
}


while [[ $# -gt 0 ]]; do
    case "$1" in
        --python)
            if [[ -z "${2-}" || "${2-}" == --* ]]; then
                misuse "--python requires a value"
            fi
            PYTHON="$2"
            shift
            ;;
        --skip) SKIP=1 ;;
        --help | -h)
            usage
            exit 0
            ;;
        *) misuse "unknown argument '$1'" ;;
    esac
    shift
done

if [[ -z "${PYTHON}" ]]; then
    misuse "--python is required"
fi

# Absolute, WITHOUT resolving symlinks: a venv's bin/python is a symlink to its base interpreter,
# and resolving it would judge the base install instead of the venv.
if [[ "${PYTHON}" != /* ]]; then
    PYTHON="${PWD}/${PYTHON}"
fi
cd /

say "ENV PREFLIGHT: juniper-recurrence env preflight (plan W0.2) of ${PYTHON}"
if (( SKIP == 1 )); then
    say "ENV PREFLIGHT: --skip given: every finding below is reported as a WARNING and none refuses"
fi
if check_interpreter; then
    check_pip
    check_pins
    check_import
fi
verdict
