#!/usr/bin/env bash

CASCOR_HOST="${CASCOR_HOST:-localhost}"
CASCOR_PORT="${CASCOR_PORT:-8201}"

curl -s "http://${CASCOR_HOST}:${CASCOR_PORT}/v1/metrics/history?count=100" 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total metrics: {len(d[\"data\"])}')"
