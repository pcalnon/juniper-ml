#!/usr/bin/env bash
# Run Phase D's remaining root steps (AC-4 drills, retention aside copy, AC-6b) through one pinned interpreter.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-11
# Status:     ad-hoc — recovery (Phase D sitting, step 14)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/ad-hoc/2026-11-11_phase_d_finish.py (every verb and every decision lives there);
#             notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md (section 6.4 step 14);
#             tests/test_phase_d_finish.py
#
# Usage:      bash util/ad-hoc/2026-11-11_phase_d_finish.bash plan
#             bash util/ad-hoc/2026-11-11_phase_d_finish.bash drill 1
#             bash util/ad-hoc/2026-11-11_phase_d_finish.bash aside
#             bash util/ad-hoc/2026-11-11_phase_d_finish.bash drill 2
#             bash util/ad-hoc/2026-11-11_phase_d_finish.bash ac6
#             bash util/ad-hoc/2026-11-11_phase_d_finish.bash status --backup-id 2
#             bash util/ad-hoc/2026-11-11_phase_d_finish.bash shred --run-dir <dir>
#
# Why a wrapper: three times in this sitting the root shell had conda active, so `python3` was conda's
# interpreter (no python3-cryptography, another SQLite) and the block's result had to be re-argued. This
# script never looks `python3` up. It runs /usr/bin/python3 in isolated mode (-I: no user site, no
# PYTHON* variables, no script directory on sys.path) under `env -i`, with an environment built from an
# allow-list: a fixed PATH and locale, HOME, USER, LOGNAME and TERM as the caller has them, and TMPDIR.
# Nothing else of the calling shell -- a loader path, a preload, a runtime's settings -- reaches the tool
# or the binaries it starts (duplicati-cli, shred, runuser).
#
# As root TMPDIR is the run root, so nothing this tool starts writes a temporary file under the system
# temp directory. It uses no privilege-raising command: every verb but `plan` refuses unless it is
# already root.
set -euo pipefail

# First, before any command is looked up: the caller's PATH may put another `dirname` or `id` ahead.
export PATH=/usr/sbin:/usr/bin:/sbin:/bin

PY=/usr/bin/python3
ENV=/usr/bin/env
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
TOOL="$HERE/2026-11-11_phase_d_finish.py"

if [[ ! -x "$PY" ]]; then
    echo "REFUSED: $PY is missing or not executable" >&2
    exit 3
fi
if [[ ! -f "$TOOL" ]]; then
    echo "REFUSED: $TOOL is missing -- run the wrapper from a checkout that holds both files" >&2
    exit 3
fi

keep=("PATH=$PATH" LC_ALL=C.UTF-8 LANG=C.UTF-8)
for name in HOME USER LOGNAME TERM; do
    if [[ -n "${!name:-}" ]]; then
        keep+=("$name=${!name}")
    fi
done

if [[ "$(id -u)" -eq 0 ]]; then
    # Honour --run-root for TMPDIR too: the two must name the same root-only directory. The tool
    # accepts no abbreviation of the option, so these two spellings are the only ones.
    run_root=/root/phase-d-tmp
    args=("$@")
    for ((i = 0; i < ${#args[@]}; i++)); do
        case "${args[i]}" in
            --run-root)
                if ((i + 1 < ${#args[@]})); then
                    run_root="${args[i + 1]}"
                fi
                ;;
            --run-root=*)
                run_root="${args[i]#--run-root=}"
                ;;
        esac
    done
    if [[ ! -d "$run_root" ]]; then
        echo "REFUSED: the run root $run_root does not exist (create it 0700, owned by root)" >&2
        exit 3
    fi
    keep+=("TMPDIR=$run_root")
elif [[ -n "${TMPDIR:-}" ]]; then
    keep+=("TMPDIR=$TMPDIR")
fi

exec "$ENV" -i "${keep[@]}" "$PY" -I "$TOOL" "$@"
