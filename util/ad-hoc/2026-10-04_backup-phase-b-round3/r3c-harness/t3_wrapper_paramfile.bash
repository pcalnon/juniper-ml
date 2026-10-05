#!/usr/bin/env bash
# Lane C round 3: does the env file's deny list stop an option-CONTAINER? --parameters-file (and its
# alias --parameterfile, Server/Program.cs:49-51) makes the server read options from a file whose values
# OVERRIDE argv (Program.cs:230-237, 1617-1690: options[key] = value). Wrapper run with --print-command and
# DUPLICATI_SERVER=/bin/true only; the installer's contract gate in --dry-run against a scratch prefix.
set -uo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
D="$S/paramfile"; rm -rf "$D"; mkdir -p "$D/data"; chmod 0700 "$D/data"
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$S/tmp"
# DAEMON_OPTS split into words, as the unit's ExecStart splits it.
read -r -a OPTS <<< "$(sed -n 's/^DAEMON_OPTS="\(.*\)"$/\1/p' "$S/frozen/util/systemd/duplicati.default" | sed 's#--server-datafolder=[^ ]*##')"
for line in "--disable-db-encryption" "--parameters-file=/home/duplicati/.config/Duplicati/opts.txt" "--parameterfile=/home/duplicati/.config/Duplicati/opts.txt" "--PARAMETERS-FILE=/tmp/x"; do
    printf '%s\n' "$line" > "$D/env"
    out="$(DUPLICATI_ENV_FILE="$D/env" DUPLICATI_DATA_FOLDER="$D/data" DUPLICATI_REQUIRE_MOUNT="" DUPLICATI_SERVER=/bin/true SETTINGS_ENCRYPTION_KEY="" \
        bash "$S/frozen/scripts/duplicati-wrapper.bash" "${OPTS[@]}" "--server-datafolder=$D/data" --print-command 2>&1)"; rc=$?
    printf '== env-file line %-70s wrapper exit=%s\n' "$line" "$rc"
    printf '%s\n' "$out" | grep -oE "(--parameters-file|--parameterfile|--disable-db-encryption)[^ ]*|FATAL.*" | sed 's/^/   | /'
done
# the installer's contract gate on the same line
SR="$D/repo"
for rel in util/install_duplicati_service.bash scripts/duplicati-wrapper.bash util/systemd/duplicati.service util/systemd/duplicati.default util/yamaguchi-pre-backup-guard.bash util/systemd/duplicati-env.contract util/ad-hoc/yamaguchi_server_db_snapshot.py util/systemd/yamaguchi-server-db-snapshot.service util/systemd/yamaguchi-server-db-snapshot.timer; do
    mkdir -p "$SR/$(dirname "$rel")"; cp "$S/frozen/$rel" "$SR/$rel"
done
printf '%s\n' "--parameters-file=/home/duplicati/.config/Duplicati/opts.txt" >> "$SR/util/systemd/duplicati-env.contract"
mkdir -p "$D/prefix"
DUPLICATI_INSTALL_PREFIX="$D/prefix" DUPLICATI_INSTALL_BLESSED="$D/prefix/absent" bash "$SR/util/install_duplicati_service.bash" --dry-run > "$D/inst.out" 2> "$D/inst.err"
echo "== installer --dry-run with that line in the contract: exit=$?; REFUSING lines: $(grep -c REFUSING "$D/inst.err")"
