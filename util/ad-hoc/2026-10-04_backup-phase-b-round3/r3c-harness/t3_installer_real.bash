#!/usr/bin/env bash
# Lane C round 3, task 3a (cont.): the installer WITHOUT --dry-run against a scratch prefix, as
# non-root, with stubs: id -u -> 0, install (drops -o/-g, refuses host paths), systemctl,
# systemd-analyze, and stat (answers duplicati:700 for the scratch data folder only).
# Proves the drift copy-aside really keeps the drifted bytes and the blessed file is written.
set -uo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
REPO="${INSTALLER_REPO:-$S/frozen}"
OUT="${INSTALLER_OUT:-$S/inst_real}"
rm -rf "$OUT"; mkdir -p "$OUT"
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$S/tmp"
RB="$OUT/stubbin"; mkdir -p "$RB"
for f in "$S/stubs/bin"/*; do ln -s "$f" "$RB/"; done
cat > "$RB/stat" <<'EOF'
#!/usr/bin/env bash
if [[ "$#" -eq 3 && "$1" == "-c" && "$2" == "%U:%a" && "$3" == "${STUB_DATA_FOLDER:-/nonexistent}" ]]; then
    printf 'STAT-STUB %s\n' "$*" >> "${STUB_LOG:?}"; echo "duplicati:700"; exit 0
fi
exec /usr/bin/stat "$@"
EOF
chmod 0755 "$RB/stat"

BLESSED_SOURCES=(scripts/duplicati-wrapper.bash util/systemd/duplicati.service util/systemd/duplicati.default util/yamaguchi-pre-backup-guard.bash util/ad-hoc/yamaguchi_server_db_snapshot.py util/systemd/yamaguchi-server-db-snapshot.service util/systemd/yamaguchi-server-db-snapshot.timer)
BLESSED_DESTS=(usr/local/lib/duplicati/duplicati-wrapper.bash etc/systemd/system/duplicati.service etc/default/duplicati usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py etc/systemd/system/yamaguchi-server-db-snapshot.service etc/systemd/system/yamaguchi-server-db-snapshot.timer)
P="$OUT/root"; mkdir -p "$P"
for i in "${!BLESSED_SOURCES[@]}"; do mkdir -p "$(dirname "$P/${BLESSED_DESTS[$i]}")"; cp "$REPO/${BLESSED_SOURCES[$i]}" "$P/${BLESSED_DESTS[$i]}"; done
BL="$OUT/blessed"; : > "$BL"
for i in "${!BLESSED_SOURCES[@]}"; do printf '%s  %s\n' "$(sha256sum "$REPO/${BLESSED_SOURCES[$i]}" | cut -d' ' -f1)" "$P/${BLESSED_DESTS[$i]}" >> "$BL"; done
echo 'DAEMON_OPTS="--edited-by-hand-DRIFT-MARKER"' > "$P/etc/default/duplicati"
drifted_sha="$(sha256sum "$P/etc/default/duplicati" | cut -c1-16)"

run() {
    STUB_LOG="$OUT/stub.log" STUB_UID=0 STUB_DATA_FOLDER="$P/home/duplicati/.config/Duplicati" \
        DUPLICATI_INSTALL_PREFIX="$P" DUPLICATI_INSTALL_BLESSED="$BL" PATH="$RB:$PATH" \
        bash "$REPO/util/install_duplicati_service.bash" "$@"
}
echo "--- run 1: no switch (must refuse, exit 4, write nothing)"
before="$(find "$P" -type f -exec sha256sum {} + | sort | sha256sum | cut -c1-16)"
run > "$OUT/run1.out" 2> "$OUT/run1.err"; echo "exit=$?"
after="$(find "$P" -type f -exec sha256sum {} + | sort | sha256sum | cut -c1-16)"
echo "prefix tree hash before=$before after=$after"
echo "--- run 2: --update-backup-behavior (must copy the drifted file aside, then install, then bless)"
run --update-backup-behavior > "$OUT/run2.out" 2> "$OUT/run2.err"; echo "exit=$?"
ls "$P/etc/default/" | sed 's/^/   /'
aside="$(ls "$P"/etc/default/duplicati.drifted-* 2>/dev/null | head -1)"
if [[ -n "$aside" ]]; then
    echo "aside sha16=$(sha256sum "$aside" | cut -c1-16) (drifted was $drifted_sha); marker kept: $(grep -c DRIFT-MARKER "$aside")"
else
    echo "NO ASIDE FILE"
fi
echo "installed defaults == repo: $(cmp -s "$P/etc/default/duplicati" "$REPO/util/systemd/duplicati.default" && echo yes || echo no)"
echo "blessed lines: $(wc -l < "$BL")"
grep -E "installed |blessed |NOTE" "$OUT/run2.out" "$OUT/run2.err" | sed "s#$OUT/##g" | head -12
echo "--- stub calls"
sed "s#$OUT/##g" "$OUT/stub.log" | cut -c1-200
echo "--- run 3: re-run with no switch (blessed now current: must pass with no DRIFT, and no new aside)"
run > "$OUT/run3.out" 2> "$OUT/run3.err"; echo "exit=$?"; grep -cE "DRIFT|BEHAVIOUR" "$OUT/run3.err"; find "$P/etc/default/" -mindepth 1 -maxdepth 1 -name '*drifted*' | wc -l
