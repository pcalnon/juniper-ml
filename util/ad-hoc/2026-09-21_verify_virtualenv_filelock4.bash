#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-21_verify_virtualenv_filelock4.bash
# Author:        Paul Calnon
#
# Date Created:  2026-09-21
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- investigation
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#646, pypa/virtualenv#3285
#
# Description:
#    Evidence that pypa/virtualenv's `filelock<4` cap is a defensive bound, not a real
#    incompatibility. Relevant because juniper-canopy#646 (dependabot: filelock 3.32.6 -> 4.0.0)
#    cannot resolve while `pre_commit` sits in conf/requirements_ci.txt: pre-commit requires
#    virtualenv>=20.10.0, and all 118 published virtualenv versions in that range cap `filelock<4`.
#
#    TWO INDEPENDENT ARGUMENTS, strongest first.
#
#    (1) THE BYTE-IDENTITY ARGUMENT (primary). The cap admits filelock 3.32.7 and forbids 4.0.0.
#        Those two releases ship a BYTE-IDENTICAL `filelock/_api.py` and `filelock/__init__.py`.
#        On virtualenv's entire import surface -- it imports only `FileLock` and `Timeout` from
#        `src/virtualenv/util/lock.py`, its sole filelock import site -- the cap therefore forbids
#        an artifact indistinguishable from one it permits. This is falsifiable in ten seconds by
#        anyone, and it does not depend on a test suite.
#
#    (2) The suite run (corroborating only). virtualenv's unit tests pass against filelock 4.0.1.
#
#    WHY (2) IS NOT SUFFICIENT ON ITS OWN, and why this script asserts instead of printing:
#      - The pass/skip counts are NON-DISCRIMINATING. Measured 2026-09-22: filelock 3.32.7 and
#        4.0.1 BOTH give `419 passed, 84 skipped`, with identical lock call counts. Quoting the
#        count alone is a vacuous pass -- it is exactly what the capped version produces. What
#        makes the run evidential is the version actually imported IN-PROCESS, so this script now
#        ASSERTS that version at both ends rather than echoing it.
#      - The earlier revision only printed it, and silently degraded: run against a clone whose
#        `pyproject.toml` already carried a staged `<4` -> `<5` edit, step 1 installed 4.0.1, so
#        the "baseline (capped)" leg and the "forced" leg printed the same thing and the A/B was a
#        no-op that could not fail. This revision restores `pyproject.toml` in a throwaway COPY of
#        the clone, so a staged edit cannot poison the baseline.
#
#    Usage:  bash util/ad-hoc/2026-09-21_verify_virtualenv_filelock4.bash <path-to-virtualenv-checkout>
#####################################################################################################################################################################################################

set -euo pipefail

VENV_SRC="${1:?usage: $0 <path-to-virtualenv-checkout>}"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  virtualenv x filelock 4.x compatibility evidence          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo "source:   ${VENV_SRC}"
echo "scratch:  ${WORK}"
echo

# ── (1) The byte-identity argument ───────────────────────────────────────────────────────────────
# Fetch the two wheels the cap separates and compare the only modules virtualenv can see.
echo "── (1) byte-identity: 3.32.7 (cap ALLOWS) vs 4.0.0 (cap FORBIDS) ──"
python3 -m venv "${WORK}/dl" >/dev/null
"${WORK}/dl/bin/python" -m pip install --quiet --upgrade pip
for v in 3.32.7 4.0.0; do
  "${WORK}/dl/bin/python" -m pip download --quiet --no-deps --only-binary :all: \
      "filelock==${v}" -d "${WORK}/w${v}" >/dev/null
  ( cd "${WORK}/w${v}" && unzip -q -o ./*.whl )
done
IDENTICAL=1
for f in _api.py __init__.py; do
  a="$(md5sum "${WORK}/w3.32.7/filelock/${f}" | cut -d' ' -f1)"
  b="$(md5sum "${WORK}/w4.0.0/filelock/${f}"  | cut -d' ' -f1)"
  if [ "${a}" = "${b}" ]; then
    echo "    filelock/${f}: IDENTICAL   md5=${a}"
  else
    echo "    filelock/${f}: DIFFERS     3.32.7=${a}  4.0.0=${b}"
    IDENTICAL=0
  fi
done
if [ "${IDENTICAL}" -ne 1 ]; then
  echo "    !! the byte-identity argument does NOT hold for this version pair -- do not cite it."
else
  echo "    => on virtualenv's import surface the cap forbids what it also permits."
fi
echo

# ── virtualenv's import surface, re-derived rather than asserted in prose ────────────────────────
echo "── virtualenv's filelock import sites ──"
grep -rn "^\s*\(import\|from\)\s\+filelock" "${VENV_SRC}/src" || true
echo

# ── (2) The suite run, on a PRISTINE copy so a staged edit cannot poison the baseline ────────────
cp -a "${VENV_SRC}" "${WORK}/ve_src"
git -C "${WORK}/ve_src" checkout -- pyproject.toml 2>/dev/null || true
echo "── pyproject cap under test (restored to committed state) ──"
grep -n "filelock" "${WORK}/ve_src/pyproject.toml"
echo

python3 -m venv "${WORK}/ve"
PY="${WORK}/ve/bin/python"
"${PY}" -m pip install --quiet --upgrade pip
"${PY}" -m pip install --quiet -e "${WORK}/ve_src"
"${PY}" -m pip install --quiet \
  "covdefaults>=2.3" "coverage>=7.2.7" "coverage-enable-subprocess>=1" "packaging>=23.1" \
  "pytest>=7.4" "pytest-env>=0.8.2" "pytest-mock>=3.11.1" "pytest-randomly>=3.12" \
  "pytest-rerunfailures>=15" "pytest-timeout>=2.1" "pytest-xdist>=3.5" "setuptools>=68" \
  "time-machine>=2.10"

# ASSERT the baseline is genuinely capped. A printed version cannot fail; this can.
echo "── baseline: the cap must have resolved filelock 3.x ──"
"${PY}" - <<'PY'
import sys, filelock
print(f"    resolved filelock {filelock.__version__}")
if not filelock.__version__.startswith("3."):
    sys.exit(f"FAIL: baseline is {filelock.__version__}, not a capped 3.x -- "
             "the <4 cap was not in force, so the A/B below proves nothing.")
PY

echo
echo "── forcing filelock 4.0.1 past the cap ──"
"${PY}" -m pip install --quiet --no-deps --upgrade "filelock==4.0.1"
"${PY}" - <<'PY'
import sys, filelock, virtualenv
print(f"    in-process filelock {filelock.__version__} / virtualenv {virtualenv.__version__}")
print(f"    imported from {filelock.__file__}")
if not filelock.__version__.startswith("4."):
    sys.exit(f"FAIL: still on {filelock.__version__}; the forced upgrade did not take effect.")
PY

echo
echo "── functional: create a seeded virtualenv (exercises ReentrantFileLock) ──"
"${PY}" -m virtualenv --seeder app-data "${WORK}/probe" >/dev/null
"${WORK}/probe/bin/python" -c "import sys; print('    created interpreter OK:', sys.version.split()[0])"

echo
echo "── virtualenv unit suite against filelock 4.0.1 ──"
echo "   (NOTE: the pass/skip counts are NOT discriminating -- 3.32.7 yields the same 419/84."
echo "    The evidence is the asserted in-process version above, not the number below.)"
cd "${WORK}/ve_src"
set +e
"${PY}" -m pytest tests/unit -p no:randomly -q --timeout 300 --no-header 2>&1 | tail -20
RC="${PIPESTATUS[0]}"
set -e

echo
echo "pytest exit code: ${RC}"
exit "${RC}"
