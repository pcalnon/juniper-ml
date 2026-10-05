#!/usr/bin/env bash
# Lane C round 3: the drift case with the switch, against the SAME prefix the blessed file names.
set -uo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
OUT="$S/inst"; NOSA="$S/stubs/nosa"
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$S/tmp"
d="$OUT/iii_drift"
STUB_LOG="$d/stub2.log" DUPLICATI_INSTALL_PREFIX="$d/root" DUPLICATI_INSTALL_BLESSED="$OUT/iii.blessed" PATH="$NOSA:$PATH" \
    bash "$S/frozen/util/install_duplicati_service.bash" --dry-run --update-backup-behavior > "$d/switch.stdout" 2> "$d/switch.stderr"
echo "exit=$?"
grep -nE "would: cp -p|would: install -m 0644 -o root -g root util/systemd/duplicati.default" "$d/switch.stdout" | sed "s#$OUT/##g"
grep -E "DRIFT|BEHAVIOUR" "$d/switch.stderr" | sed "s#$OUT/##g"
