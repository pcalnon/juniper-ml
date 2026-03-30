#!/usr/bin/env bash

curl -s http://localhost:8201/v1/metrics/history?count=100 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total metrics: {len(d[\"data\"])}')"
