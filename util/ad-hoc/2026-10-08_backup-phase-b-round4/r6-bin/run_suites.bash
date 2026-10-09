#!/usr/bin/env bash
# Round 6: run every Phase B suite in a tree, normally or in ci-sim (mountpoint stub exit 1 first on PATH).
# usage: run_suites.bash <tree> normal|cisim
set -u
tree="$1"; mode="$2"
cd "$tree" || exit 2
P="/usr/bin:/bin"
if [[ "$mode" == cisim ]]; then
    stub="$(dirname "$0")/../cisim-bin"
    mkdir -p "$stub"
    printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$*" >> "%s/asked.log"\nexit 1\n' "$stub" > "$stub/mountpoint"
    chmod 755 "$stub/mountpoint"
    : > "$stub/asked.log"
    P="$(cd "$stub" && pwd):$P"
fi
for s in tests/test_duplicati_wrapper_contract.py tests/test_duplicati_installer_real_path.py tests/test_backup_rekey_real_path.py \
         tests/test_a0_restore_scripts.py tests/test_clear_stop_backup_design.py tests/test_ci_test_wiring_drift.py tests/test_env_repr_safety.py; do
    out="$(env -i PATH="$P" HOME="$tree" PYTHONDONTWRITEBYTECODE=1 LANG=C.UTF-8 python3 -m unittest "$s" 2>&1)"; rc=$?
    echo "$mode $s rc=$rc :: $(printf '%s\n' "$out" | grep -E '^(Ran |OK|FAILED)' | tr '\n' ' ')"
    if (( rc != 0 )); then printf '%s\n' "$out" | grep -E '^(FAIL|ERROR):' | head -20; fi
done
if [[ "$mode" == cisim ]]; then echo "mountpoint asked (distinct): $(sort -u "$stub/asked.log" | tr '\n' ';')"; fi
