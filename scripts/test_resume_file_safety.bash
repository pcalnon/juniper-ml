#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAKE_SCRIPT="${SCRIPT_DIR}/wake_the_claude.bash"

TMPDIR="$(mktemp -d)"
cleanup() {
    rm -rf "${TMPDIR}"
}
trap cleanup EXIT

pushd "${TMPDIR}" >/dev/null

printf 'not-a-uuid\n' > session-id.txt

set +e
bash "${WAKE_SCRIPT}" --resume session-id.txt --print >/dev/null 2>/dev/null
script_exit_code=$?
set -e

if [[ "${script_exit_code}" -eq 0 ]]; then
    echo "FAIL: invalid session file should return non-zero exit"
    exit 1
fi

if [[ ! -f session-id.txt ]]; then
    echo "FAIL: resume source file was unexpectedly deleted"
    exit 1
fi

popd >/dev/null
echo "PASS: invalid resume file is preserved"
