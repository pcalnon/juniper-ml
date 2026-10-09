#!/usr/bin/env bash
# nul_key.bash <a0> <scratch>: a key file with a NUL byte -- what the wrapper exports vs what the gate/hand start read.
a0="$1"; s="$2"; mkdir -p "${s}/cred" "${s}/data"; chmod 700 "${s}/data"
printf 'abcdefghij\000klmnopqrst' > "${s}/cred/settings-key"
printf 'pw-fake-123\n' > "${s}/pw"; chmod 600 "${s}/pw" "${s}/cred/settings-key"
k="$(<"${s}/cred/settings-key")"
echo "bash \$(<file) length: ${#k}"
python3 -c 'import sys; print("python read length:", len(open(sys.argv[1], encoding="utf-8", newline="").read().rstrip("\n")))' "${s}/cred/settings-key"
env -i PATH=/usr/bin:/bin CREDENTIALS_DIRECTORY="${s}/cred" DUPLICATI_ENV_FILE="${s}/none" DUPLICATI_SERVER=/bin/true \
    DUPLICATI_DATA_FOLDER="${s}/data" bash "${a0}/scripts/duplicati-wrapper.bash" --print-command 2>&1 >/dev/null | grep -E 'settings encryption key|FATAL|null'
echo "wrapper exit: ${PIPESTATUS[0]}"
python3 "${a0}/util/ad-hoc/2026-10-03_rekey_gate.py" "${s}/none.sqlite" "${s}/cred/settings-key" 2>&1 | head -2
