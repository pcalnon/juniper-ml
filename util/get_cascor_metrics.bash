#!/usr/bin/env bash

curl -s http://localhost:8201/v1/metrics 2>&1 | python3 -m json.tool 2>/dev/null
