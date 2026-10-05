#!/usr/bin/env bash
# Lane C round 3, task 3b: the re-key's --dry-run, unmodified (the frozen tree's file), non-root,
# with every host-touching command PATH-shadowed by a logging stub. REKEY_WORKDIR and
# DUPLICATI_DATA_FOLDER point into scratch. In --dry-run nothing but `python3 <api> --help` should run.
set -uo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
OUT="$S/rekey_dry"; rm -rf "$OUT"; mkdir -p "$OUT"
export PYTHONDONTWRITEBYTECODE=1
STUB_LOG="$OUT/stub.log" PATH="$S/stubs/bin:$PATH" REKEY_WORKDIR="$OUT/workdir" DUPLICATI_DATA_FOLDER="$OUT/data" \
    bash "$S/frozen/util/ad-hoc/2026-10-03_rekey_settings_key.bash" --dry-run > "$OUT/stdout.txt" 2> "$OUT/stderr.txt"
echo "exit=$?"
echo "--- stderr (the whole printed sequence):"
sed "s#$S/frozen/##g" "$OUT/stderr.txt"
echo "--- 'would:' lines: $(grep -c 'would: ' "$OUT/stderr.txt")"
echo "--- 'revert' anywhere in output: $(grep -c 'revert' "$OUT/stderr.txt" "$OUT/stdout.txt" | tr '\n' ' ')"
echo "--- stub calls (must be none in a dry run):"; [[ -e "$OUT/stub.log" ]] && cat "$OUT/stub.log" || echo "(no stub was called)"
echo "--- workdir created? $( [[ -e "$OUT/workdir" ]] && echo YES || echo no )"
# usage refusal
STUB_LOG="$OUT/stub.log" PATH="$S/stubs/bin:$PATH" bash "$S/frozen/util/ad-hoc/2026-10-03_rekey_settings_key.bash" --bogus > /dev/null 2> "$OUT/usage.err"; echo "bogus arg exit=$?: $(cat "$OUT/usage.err")"
# non-root real run: must refuse before anything (id -u is real here)
STUB_LOG="$OUT/stub.log" PATH="$S/stubs/bin:$PATH" REKEY_WORKDIR="$OUT/workdir" bash "$S/frozen/util/ad-hoc/2026-10-03_rekey_settings_key.bash" > /dev/null 2> "$OUT/nonroot.err"; echo "non-root real exit=$?:"; sed 's/^/   /' "$OUT/nonroot.err"
echo "--- stub calls after the non-root real run:"; [[ -e "$OUT/stub.log" ]] && cat "$OUT/stub.log" || echo "(no stub was called)"
