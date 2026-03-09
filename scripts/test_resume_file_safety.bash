#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAKE_SCRIPT="${SCRIPT_DIR}/wake_the_claude.bash"

TMPDIR="$(mktemp -d)"
cleanup() {
    rm -rf "${TMPDIR}"
}
trap cleanup EXIT

SESSIONS_DIR="${TMPDIR}/sessions"
LOGS_DIR="${TMPDIR}/logs"
mkdir -p "${SESSIONS_DIR}" "${LOGS_DIR}"

export WTC_SESSIONS_DIR="${SESSIONS_DIR}"
export WTC_LOGS_DIR="${LOGS_DIR}"

pushd "${TMPDIR}" >/dev/null

printf 'not-a-uuid\n' > "${SESSIONS_DIR}/session-id.txt"

set +e
bash "${WAKE_SCRIPT}" --resume session-id.txt --print >/dev/null 2>/dev/null
script_exit_code=$?
set -e

if [[ "${script_exit_code}" -eq 0 ]]; then
    echo "FAIL: invalid session file should return non-zero exit"
    exit 1
fi

if [[ ! -f "${SESSIONS_DIR}/session-id.txt" ]]; then
    echo "FAIL: resume source file was unexpectedly deleted"
    exit 1
fi

popd >/dev/null
echo "PASS: invalid resume file is preserved"
