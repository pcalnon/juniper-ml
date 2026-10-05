#!/usr/bin/env bash
# Lane C round 3: PATH-shadowing stubs. Every stub appends one line to $STUB_LOG (default: stub.log in
# the stub dir) and never touches the host. Behaviour is steered by env vars named per stub.
set -euo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
B="$S/stubs/bin"
rm -rf "$S/stubs"; mkdir -p "$B"

cat > "$B/systemctl" <<'EOF'
#!/usr/bin/env bash
# systemctl stub: logs; answers show/is-active/is-enabled from env; fails a verb named in STUB_SYSTEMCTL_FAIL.
printf 'SYSTEMCTL-STUB %s\n' "$*" >> "${STUB_LOG:?}"
# STUB_SYSTEMCTL_FAIL is ONE phrase (not split into words): any call whose argv contains it fails.
if [[ -n "${STUB_SYSTEMCTL_FAIL:-}" && "$*" == *"${STUB_SYSTEMCTL_FAIL}"* ]]; then
    exit 1
fi
if [[ "$1" == start && -n "${STUB_DROPIN:-}" ]]; then
    if [[ -e "${STUB_DROPIN}" ]]; then printf 'DROPIN-AT-START %s\n' "$(tr '\n' '|' < "${STUB_DROPIN}")" >> "${STUB_LOG}"; else echo 'DROPIN-AT-START (none)' >> "${STUB_LOG}"; fi
fi
if [[ "$1" == stop && -n "${STUB_FAIL_NTH_STOP:-}" ]]; then
    n=$(grep -c 'SYSTEMCTL-STUB stop' "${STUB_LOG}")
    (( n == STUB_FAIL_NTH_STOP )) && exit 1
fi
case "$1" in
    show) if [[ "$*" == *FragmentPath* ]]; then
              if [[ -n "${STUB_FRAGMENT_AFTER_RELOADS:-}" ]] && (( $(grep -c 'SYSTEMCTL-STUB daemon-reload' "${STUB_LOG}") >= STUB_FRAGMENT_AFTER_RELOADS )); then
                  printf '%s\n' "${STUB_FRAGMENT_LATER:?}"
              else
                  printf '%s\n' "${STUB_FRAGMENT:-}"
              fi
          fi ;;
    is-active) printf '%s\n' "${STUB_IS_ACTIVE:-inactive}" ;;
    is-enabled) printf '%s\n' "${STUB_IS_ENABLED:-disabled}" ;;
esac
exit 0
EOF

cat > "$B/journalctl" <<'EOF'
#!/usr/bin/env bash
printf 'JOURNALCTL-STUB %s\n' "$*" >> "${STUB_LOG:?}"
n=$(grep -c 'SYSTEMCTL-STUB start' "${STUB_LOG}" || true)
# STUB_START_LINE_FOR="1 2 3": which start numbers log 'Server has started'
for k in ${STUB_START_LINE_FOR:-1 2 3 4 5}; do
    if [[ "$k" == "$n" ]]; then echo "Oct 04 duplicati-server[1]: Server has started"; fi
done
[[ -n "${STUB_JOURNAL_EXTRA:-}" ]] && echo "${STUB_JOURNAL_EXTRA}"
exit 0
EOF

cat > "$B/sudo" <<'EOF'
#!/usr/bin/env bash
# sudo stub: logs, drops "-u USER" and "--", runs the rest as the CURRENT user.
printf 'SUDO-STUB %s\n' "$*" >> "${STUB_LOG:?}"
while (( $# )); do
    case "$1" in
        -u) shift 2 ;;
        --) shift; break ;;
        -*) shift ;;
        *) break ;;
    esac
done
exec "$@"
EOF

cat > "$B/duplicati-server" <<'EOF'
#!/usr/bin/env bash
printf 'DUPLICATI-SERVER-STUB %s\n' "$*" >> "${STUB_LOG:?}"
exit "${STUB_SERVER_EXIT:-0}"
EOF

cat > "$B/id" <<'EOF'
#!/usr/bin/env bash
# id stub: `id -u` (no user) answers STUB_UID if set; everything else is the real id.
if [[ "$#" -eq 1 && "$1" == "-u" && -n "${STUB_UID:-}" ]]; then printf 'ID-STUB -u -> %s\n' "${STUB_UID}" >> "${STUB_LOG:?}"; echo "${STUB_UID}"; exit 0; fi
exec /usr/bin/id "$@"
EOF

cat > "$B/chown" <<'EOF'
#!/usr/bin/env bash
printf 'CHOWN-STUB %s\n' "$*" >> "${STUB_LOG:?}"
exit 0
EOF

cat > "$B/sleep" <<'EOF'
#!/usr/bin/env bash
printf 'SLEEP-STUB %s\n' "$*" >> "${STUB_LOG:?}"
exit 0
EOF

cat > "$B/install" <<'EOF'
#!/usr/bin/env bash
# install stub: drop -o/-g (non-root), log, run the real install on scratch paths only.
printf 'INSTALL-STUB %s\n' "$*" >> "${STUB_LOG:?}"
args=()
while (( $# )); do
    case "$1" in
        -o|-g) shift 2 ;;
        *) args+=("$1"); shift ;;
    esac
done
for a in "${args[@]}"; do
    case "$a" in
        /etc/*|/usr/*|/run/systemd/*|/home/duplicati*|/root*) echo "INSTALL-STUB REFUSES a host path: $a" >&2; exit 97 ;;
    esac
done
exec /usr/bin/install "${args[@]}"
EOF

cat > "$B/systemd-analyze" <<'EOF'
#!/usr/bin/env bash
printf 'SYSTEMD-ANALYZE-STUB %s\n' "$*" >> "${STUB_LOG:?}"
exit 0
EOF

chmod 0755 "$B"/*
ls -la "$B"
