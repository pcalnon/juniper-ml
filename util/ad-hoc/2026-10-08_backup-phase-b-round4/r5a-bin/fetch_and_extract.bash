#!/usr/bin/env bash
# r5-A: fetch the five Duplicati sources at the tag (read-only) and re-run the fixture extractor
set -euo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/097ae87b-7a4c-4970-9f46-d052521e17c7/scratchpad/r5-A
D="$S/dup/src"; mkdir -p "$D"
B=https://raw.githubusercontent.com/duplicati/duplicati/v2.4.0.0_stable_2026-09-03
curl -sfL -o "$D/Program.cs" "$B/Duplicati/Server/Program.cs"
curl -sfL -o "$D/WebServerLoader.cs" "$B/Duplicati/Server/WebServerLoader.cs"
curl -sfL -o "$D/DataFolderManager.cs" "$B/Duplicati/Library/AutoUpdater/DataFolderManager.cs"
curl -sfL -o "$D/Util.cs" "$B/Duplicati/Library/Common/IO/Util.cs"
curl -sfL -o "$D/Options.cs" "$B/Duplicati/Library/Main/Options.cs"
PYTHONDONTWRITEBYTECODE=1 python3 -I "$S/head/util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c1_extract_server_options.py" "$D" > "$S/dup/fixture.regen"
sed '/^# .*Fetched read-only/d' "$S/dup/fixture.regen" > "$S/dup/a"
sed '/^# .*Fetched read-only/d' "$S/head/tests/fixtures/duplicati_2.4.0.0_server_options.txt" > "$S/dup/b"
cmp "$S/dup/fixture.regen" "$S/head/tests/fixtures/duplicati_2.4.0.0_server_options.txt" && echo "fixture reproduces byte-for-byte"
