#!/usr/bin/env bash
# Lane C round 3, task 3a: the installer's dry runs (non-root) against scratch prefixes, plus one
# NON-dry-run against a scratch prefix with id/install/systemctl/systemd-analyze/stat stubs.
# Every destination is under $S/inst/<case>/root via DUPLICATI_INSTALL_PREFIX; the blessed file via
# DUPLICATI_INSTALL_BLESSED. The installer is the FROZEN tree's (REPO_DIR = the frozen tree).
set -uo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
REPO="${INSTALLER_REPO:-$S/frozen}"
INST="$REPO/util/install_duplicati_service.bash"
OUT="$S/inst"
rm -rf "$OUT"; mkdir -p "$OUT" "$S/tmp"
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$S/tmp"
# a stub dir WITHOUT systemd-analyze, so the dry run's advisory verify runs the real tool on temp copies
NOSA="$S/stubs/nosa"; rm -rf "$NOSA"; mkdir -p "$NOSA"
for f in "$S/stubs/bin"/*; do [[ "$(basename "$f")" == systemd-analyze ]] || ln -s "$f" "$NOSA/"; done

BLESSED_SOURCES=(scripts/duplicati-wrapper.bash util/systemd/duplicati.service util/systemd/duplicati.default util/yamaguchi-pre-backup-guard.bash util/ad-hoc/yamaguchi_server_db_snapshot.py util/systemd/yamaguchi-server-db-snapshot.service util/systemd/yamaguchi-server-db-snapshot.timer)
BLESSED_DESTS=(usr/local/lib/duplicati/duplicati-wrapper.bash etc/systemd/system/duplicati.service etc/default/duplicati usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py etc/systemd/system/yamaguchi-server-db-snapshot.service etc/systemd/system/yamaguchi-server-db-snapshot.timer)

blessed_equal() { # $1 prefix, $2 out file
    : > "$2"
    for i in "${!BLESSED_SOURCES[@]}"; do
        printf '%s  %s\n' "$(sha256sum "$REPO/${BLESSED_SOURCES[$i]}" | cut -d' ' -f1)" "$1/${BLESSED_DESTS[$i]}" >> "$2"
    done
}
install_repo_copies() { # $1 prefix
    for i in "${!BLESSED_SOURCES[@]}"; do
        mkdir -p "$(dirname "$1/${BLESSED_DESTS[$i]}")"; cp "$REPO/${BLESSED_SOURCES[$i]}" "$1/${BLESSED_DESTS[$i]}"
    done
}
runi() { # runi <case> <blessed> [args...]
    local c="$1" bl="$2"; shift 2
    local d="$OUT/$c"; mkdir -p "$d/root"
    STUB_LOG="$d/stub.log" DUPLICATI_INSTALL_PREFIX="$d/root" DUPLICATI_INSTALL_BLESSED="$bl" PATH="$NOSA:$PATH" \
        bash "$INST" "$@" > "$d/stdout.txt" 2> "$d/stderr.txt"
    local rc=$?
    echo "== $c ($*): exit=$rc; stub calls: $( [[ -e "$d/stub.log" ]] && wc -l < "$d/stub.log" || echo 0 )"
    return 0
}

# i. never blessed, empty prefix
runi i_first_install "$OUT/absent" --dry-run
grep -E "first install|would: install -m|would: write|would: systemctl|verify:" "$OUT/i_first_install/stdout.txt" | head -20
echo "   'would: install -m' count: $(grep -c 'would: install -m' "$OUT/i_first_install/stdout.txt")"

# ii. never blessed, but pre-existing installed files (this host's shape: defaults file + both snapshot units)
mkdir -p "$OUT/ii_first_install_over_existing/root/etc/default" "$OUT/ii_first_install_over_existing/root/etc/systemd/system"
echo 'DAEMON_OPTS="--webservice-port=8300"  # scratch stand-in, not the host file' > "$OUT/ii_first_install_over_existing/root/etc/default/duplicati"
echo '# scratch stand-in for the 08-30 snapshot unit' > "$OUT/ii_first_install_over_existing/root/etc/systemd/system/yamaguchi-server-db-snapshot.service"
echo '# scratch stand-in for the 08-30 snapshot timer' > "$OUT/ii_first_install_over_existing/root/etc/systemd/system/yamaguchi-server-db-snapshot.timer"
runi ii_first_install_over_existing "$OUT/absent" --dry-run
grep -E "DRIFT|first install|would: cp -p|would: install -m 0644 .*(duplicati.default|snapshot)" "$OUT/ii_first_install_over_existing/stdout.txt" "$OUT/ii_first_install_over_existing/stderr.txt" | sed "s#$OUT/##"
echo "   'would: cp -p' count: $(grep -c 'would: cp -p' "$OUT/ii_first_install_over_existing/stdout.txt")"

# iii. drift of one installed file
P="$OUT/iii_drift/root"; mkdir -p "$P"; install_repo_copies "$P"; echo 'DAEMON_OPTS="--edited-by-hand"' > "$P/etc/default/duplicati"
blessed_equal "$P" "$OUT/iii.blessed"
runi iii_drift "$OUT/iii.blessed" --dry-run
grep -E "DRIFT|BEHAVIOUR|Refusing" "$OUT/iii_drift/stderr.txt"
mkdir -p "$OUT/iii_drift_switch"; rm -rf "$OUT/iii_drift_switch/root"; cp -a "$OUT/iii_drift/root" "$OUT/iii_drift_switch/root"
runi iii_drift_switch "$OUT/iii.blessed" --dry-run --update-backup-behavior
grep -nE "would: cp -p|would: install -m 0644 -o root -g root util/systemd/duplicati.default" "$OUT/iii_drift_switch/stdout.txt" | sed "s#$OUT/##g"

# iv. drift of TWO installed files + a behaviour change in a third
P="$OUT/iv_drift2/root"; mkdir -p "$P"; install_repo_copies "$P"
echo 'edited' >> "$P/etc/systemd/system/duplicati.service"; echo 'edited' >> "$P/usr/local/lib/duplicati/duplicati-wrapper.bash"
blessed_equal "$P" "$OUT/iv.blessed"
sed -i "s#^[0-9a-f]\{64\}  $P/etc/systemd/system/yamaguchi-server-db-snapshot.timer#$(printf '0%.0s' {1..64})  $P/etc/systemd/system/yamaguchi-server-db-snapshot.timer#" "$OUT/iv.blessed"
runi iv_drift2 "$OUT/iv.blessed" --dry-run --update-backup-behavior
grep -E "DRIFT|BEHAVIOUR" "$OUT/iv_drift2/stderr.txt" | sed "s#$OUT/##g"
grep -cE "would: cp -p" "$OUT/iv_drift2/stdout.txt"

# v. kept-existing env contract
mkdir -p "$OUT/v_kept_env/root/etc/duplicati"; echo '--webservice-port=8311' > "$OUT/v_kept_env/root/etc/duplicati/env"
runi v_kept_env "$OUT/absent" --dry-run
grep -E "kept existing|would: install -m 0640" "$OUT/v_kept_env/stdout.txt" | sed "s#$OUT/##g"

# vi. non-root, no --dry-run: refused before anything
runi vi_nonroot_real "$OUT/absent"
cat "$OUT/vi_nonroot_real/stderr.txt"

# vii. the widened secret gate, on a scratch repository copy
SR="$OUT/vii_repo"; mkdir -p "$SR"
for rel in util/install_duplicati_service.bash scripts/duplicati-wrapper.bash util/systemd/duplicati.service util/systemd/duplicati.default util/yamaguchi-pre-backup-guard.bash util/systemd/duplicati-env.contract util/ad-hoc/yamaguchi_server_db_snapshot.py util/systemd/yamaguchi-server-db-snapshot.service util/systemd/yamaguchi-server-db-snapshot.timer; do
    mkdir -p "$SR/$(dirname "$rel")"; cp "$REPO/$rel" "$SR/$rel"
done
base="$(cat "$SR/util/systemd/duplicati-env.contract")"
for line in "SETTINGS_ENCRYPTION_KEY_OLD='abcdefghijklmnop'" "# export SETTINGS_ENCRYPTION_KEY=abcdefghijklmnop" "--settings-encryption-key=abcdefghijklmnop" "--disable-db-encryption" "--webservice-reset-jwt-config=true" "--webservice-interface=any" "--server-datafolder=/tmp/x" "--webservice-allowed-hostnames=*" "DUPLICATI__DISABLE_DB_ENCRYPTION=true" "export TMPDIR=/tmp"; do
    printf '%s\n%s\n' "$base" "$line" > "$SR/util/systemd/duplicati-env.contract"
    d="$OUT/vii_case"; rm -rf "$d"; mkdir -p "$d/root"
    STUB_LOG="$d/stub.log" DUPLICATI_INSTALL_PREFIX="$d/root" DUPLICATI_INSTALL_BLESSED="$OUT/absent" PATH="$NOSA:$PATH" bash "$SR/util/install_duplicati_service.bash" --dry-run > "$d/o" 2> "$d/e"; rc=$?
    # and what the WRAPPER does with the same file at the next start (print-command, stub server)
    STUB_LOG="$d/stub.log" DUPLICATI_ENV_FILE="$SR/util/systemd/duplicati-env.contract" DUPLICATI_DATA_FOLDER="$d/root" DUPLICATI_REQUIRE_MOUNT="" DUPLICATI_SERVER=/bin/true SETTINGS_ENCRYPTION_KEY="" bash "$SR/scripts/duplicati-wrapper.bash" --print-command > "$d/wo" 2> "$d/we"; wrc=$?
    printf '   installer exit=%s  wrapper(next start) exit=%s  line=%q\n' "$rc" "$wrc" "$line"
done
printf '%s\n' "$base" > "$SR/util/systemd/duplicati-env.contract"
echo "--- host-path writes by the install stub (must be none):"; cat "$OUT"/*/stub.log 2>/dev/null | grep -c "REFUSES" || true
echo "--- systemctl calls during dry runs (must be none):"; cat "$OUT"/*/stub.log 2>/dev/null | grep -c "SYSTEMCTL-STUB" || true
