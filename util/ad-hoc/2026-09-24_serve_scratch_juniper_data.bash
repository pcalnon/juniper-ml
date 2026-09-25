#!/usr/bin/env bash
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling (defect-register provenance)
# Author:      Paul Calnon
# Created:     2026-09-24
# Status:      ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
#
# Serve a SCRATCH EXPORT of juniper-data on 127.0.0.1:<port>, for the real-juniper-data probes of the
# round-42 follow-up lane: util/ad-hoc/2026-09-24_round42_probes/cascor688-v688/probe_realjd_*.py and
# both `realjd` harnesses (util/ad-hoc/2026-09-24_cascor688_realjd_error_texts.py and
# util/ad-hoc/2026-09-24_cascor690_bool_stance_realjd_probe.py). It recreates the validator's runner
# (run_jd.bash, which lived only on tmpfs), with its safety rules made explicit:
#
#   * never a checkout: a checkout's ./.env is read, and storage would land in its ./data/datasets.
#     Export one instead:  git -C <juniper-data clone> fetch origin main
#                          mkdir -p <tree>
#                          git -C <juniper-data clone> archive origin/main | tar -x -C <tree>
#   * storage and imports go under <scratch-dir>, which gets the probes' fixture, big.csv (a small CSV
#     with a `label` column; the probes' max_bytes=40 puts it over the cap);
#   * no API keys, no auth requirement and no CSV-import cap or truncation switch are inherited from the
#     shell; metrics and rate limiting are off (a 429 mid-run reads like a fetch failure); every Sentry
#     DSN variable is set to "" (not unset: a .env loader re-injects an unset variable);
#   * the server stops by itself after 1500 s. To stop it sooner: pkill -A -f 'uvicorn.*--port <port>'
#     (-A spares the shell running pkill, whose own command line would otherwise match).
#
# Usage: bash 2026-09-24_serve_scratch_juniper_data.bash <juniper-data-tree> <scratch-dir> <port>

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "usage: $0 <juniper-data-tree> <scratch-dir> <port>" >&2
    exit 2
fi
tree="$1"
scratch="$2"
port="$3"

if [ ! -f "${tree}/juniper_data/api/app.py" ]; then
    echo "not a juniper-data tree: ${tree}" >&2
    exit 2
fi
if [ -e "${tree}/.git" ] || [ -e "${tree}/.env" ]; then
    echo "refusing: ${tree} has a .git or .env; serve a scratch export (git archive), never a checkout" >&2
    exit 2
fi

mkdir -p "${scratch}/jdstore" "${scratch}/jdimport"
if [ ! -f "${scratch}/jdimport/big.csv" ]; then
    {
        echo "x,label"
        for i in $(seq 1 20); do
            echo "${i},$((i % 2))"
        done
    } > "${scratch}/jdimport/big.csv"
fi

# juniper-data reads its settings case-insensitively (case_sensitive=False), so drop every case variant.
while read -r name; do
    case "${name^^}" in
        JUNIPER_DATA_API_KEYS | JUNIPER_DATA_API_KEYS_FILE | JUNIPER_DATA_REQUIRE_AUTH | JUNIPER_DATA_CSV_IMPORT_ALLOW_TRUNCATION | JUNIPER_DATA_CSV_IMPORT_MAX_BYTES)
            unset "${name}"
            ;;
    esac
done < <(compgen -e)
export SENTRY_SDK_DSN="" SENTRY_DSN="" JUNIPER_DATA_SENTRY_DSN="" JUNIPER_CASCOR_SENTRY_DSN="" CANOPY_SENTRY_DSN="" JUNIPER_CANOPY_SENTRY_DSN=""
export PYTHONPATH="${tree}"
export PYTHONDONTWRITEBYTECODE=1
export JUNIPER_DATA_STORAGE_PATH="${scratch}/jdstore"
export JUNIPER_DATA_IMPORT_DIR="${scratch}/jdimport"
export JUNIPER_DATA_METRICS_ENABLED=false
export JUNIPER_DATA_RATE_LIMIT_ENABLED=false

cd "${tree}"
exec timeout 1500 /opt/miniforge3/envs/JuniperData/bin/python -s -m uvicorn --factory juniper_data.api.app:create_app --host 127.0.0.1 --port "${port}" --log-level warning
