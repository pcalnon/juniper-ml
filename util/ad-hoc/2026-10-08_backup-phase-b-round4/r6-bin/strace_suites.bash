#!/usr/bin/env bash
# Round 6: strace the Phase B suites for host-path access (file syscalls only); counts per sensitive prefix.
set -u
tree="$1"; shift
cd "$tree" || exit 2
for s in "$@"; do
    log="$tree/../strace.$(basename "$s").log"
    env -i PATH=/usr/bin:/bin HOME="$tree" PYTHONDONTWRITEBYTECODE=1 LANG=C.UTF-8 \
        strace -f -qq -e trace=%file -o "$log" python3 -m unittest "$s" >/dev/null 2>&1; rc=$?
    echo "$s rc=$rc"
    grep -oE '"(/mnt/Backups|/usr/lib/duplicati|/etc/credstore|/etc/duplicati|/etc/default/duplicati|/etc/systemd/system|/home/pcalnon)[^"]*"' "$log" | sort | uniq -c | head -20
done
