#!/usr/bin/env bash

CASCOR_HOST="${CASCOR_HOST:-localhost}"
CASCOR_PORT="${CASCOR_PORT:-8201}"

curl -s "http://${CASCOR_HOST}:${CASCOR_PORT}/v1/training/status" 2>&1 | python3 -m json.tool 2>/dev/null
