#!/usr/bin/env bash
# r5-A: make the mount-absent ci-sim copy of the 9ce2f602 extraction
set -euo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/097ae87b-7a4c-4970-9f46-d052521e17c7/scratchpad/r5-A
rm -rf "$S/cisim"
cp -a "$S/head" "$S/cisim"
sed -i -e 's#"${DUPLICATI_REQUIRE_MOUNT-/mnt/Backups}"#"${DUPLICATI_REQUIRE_MOUNT-/nonexistent-r5a/Backups}"#' "$S/cisim/scripts/duplicati-wrapper.bash"
grep -c nonexistent-r5a "$S/cisim/scripts/duplicati-wrapper.bash"
test ! -e /nonexistent-r5a && echo "default mount absent"
