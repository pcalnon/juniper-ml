#!/usr/bin/env bash
# trace_suites.bash <tree> <outdir> <suite...>: run each suite under strace (file syscalls only: paths,
# never contents) and summarise which host paths outside the scratch area it touched.
tree="$1"; out="$2"; shift 2
mkdir -p "${out}"
cd "${tree}" || exit 2
for t in "$@"; do
  b="$(basename "${t}" .py)"
  PYTHONDONTWRITEBYTECODE=1 strace -f -qq -e trace=%file -o "${out}/${b}.strace" python3 -m unittest "${t}" > "${out}/${b}.out" 2>&1
  printf '%s rc=%s\n' "${b}" "$?"
  # Paths of interest: host config / secrets / units / data folder / backup mount / real home config.
  grep -o -E '"(/etc/(duplicati|credstore|default/duplicati|systemd/system/(duplicati|yamaguchi)[^"]*)|/home/duplicati[^"]*|/home/pcalnon/\.config/[^"]*|/home/pcalnon/\.local/state/duplicati[^"]*|/mnt/Backups[^"]*|/run/systemd/system/duplicati[^"]*|/root[^"]*)[^"]*"' "${out}/${b}.strace" | sort | uniq -c | sort -rn | head -20
done
