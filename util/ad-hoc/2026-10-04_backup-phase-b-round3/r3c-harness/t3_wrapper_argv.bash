#!/usr/bin/env bash
# Lane C round 3: the argv the wrapper hands the server for (1) the unit as shipped and (2) the re-key's
# decrypt start (the drop-in's ExecStart = the unit's + --disable-db-encryption), with the shipped contract
# as the env file. --server-datafolder is pointed at a scratch 0700 folder; DUPLICATI_SERVER=/bin/true.
set -uo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
D="$S/wrapper_argv"; mkdir -p "$D/data"; chmod 0700 "$D/data"
opts_line="$(grep '^DAEMON_OPTS=' "$S/frozen/util/systemd/duplicati.default")"
opts="${opts_line#DAEMON_OPTS=\"}"; opts="${opts%\"}"
read -r -a words <<< "$opts"
for i in "${!words[@]}"; do [[ "${words[$i]}" == --server-datafolder=* ]] && words[$i]="--server-datafolder=$D/data"; done
for extra in "" "--disable-db-encryption"; do
    echo "== DAEMON_OPTS (${#words[@]} words) ${extra:+plus $extra}"
    DUPLICATI_ENV_FILE="$S/frozen/util/systemd/duplicati-env.contract" DUPLICATI_DATA_FOLDER="$D/data" DUPLICATI_REQUIRE_MOUNT="" DUPLICATI_SERVER=/bin/true SETTINGS_ENCRYPTION_KEY="" \
        bash "$S/frozen/scripts/duplicati-wrapper.bash" "${words[@]}" ${extra:+"$extra"} --print-command 2>&1 | sed "s#$D#<D>#g" | tr ' ' '\n' | sed 's/^/   /'
done
