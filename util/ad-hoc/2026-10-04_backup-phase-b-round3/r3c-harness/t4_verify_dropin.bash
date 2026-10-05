#!/usr/bin/env bash
# Lane C round 3: `systemd-analyze verify` on a COPY of the repository unit plus the exact drop-in the
# re-key writes (ExecStart reset + re-declared with --disable-db-encryption), and on the mutant drop-in
# without the reset line. ExecStart targets are rewritten to a scratch copy of the wrapper so verify
# can resolve them. Nothing is loaded into the running manager.
set -uo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
for variant in shipped mutant_no_reset; do
    V="$S/verify_dropin/$variant"; rm -rf "$V"; mkdir -p "$V/duplicati.service.d"
    cp "$S/frozen/scripts/duplicati-wrapper.bash" "$V/duplicati-wrapper.bash"; chmod 0755 "$V/duplicati-wrapper.bash"
    sed -E "s#^ExecStart=/usr/local/lib/duplicati/duplicati-wrapper.bash#ExecStart=$V/duplicati-wrapper.bash#" "$S/frozen/util/systemd/duplicati.service" > "$V/duplicati.service"
    if [[ "$variant" == shipped ]]; then
        printf '[Service]\nExecStart=\nExecStart=%s --disable-db-encryption\n' "$V/duplicati-wrapper.bash \$DAEMON_OPTS" > "$V/duplicati.service.d/zz-rekey-disable-db-encryption.conf"
    else
        printf '[Service]\nExecStart=%s --disable-db-encryption\n' "$V/duplicati-wrapper.bash \$DAEMON_OPTS" > "$V/duplicati.service.d/zz-rekey-disable-db-encryption.conf"
    fi
    echo "== $variant: drop-in = $(tr '\n' '|' < "$V/duplicati.service.d/zz-rekey-disable-db-encryption.conf" | sed "s#$V#<V>#g")"
    out="$(cd "$V" && SYSTEMD_UNIT_PATH="$V:" systemd-analyze verify --man=no "$V/duplicati.service" 2>&1)"; rc=$?
    echo "   verify exit=$rc"
    printf '%s\n' "$out" | sed "s#$V#<V>#g" | sed 's/^/   | /' | head -12
done
