#!/usr/bin/env bash
# Round 6: a CI runner has no /home/pcalnon. Simulate by renaming that literal to a nonexistent root dir in a
# copy of the A0 restore script and its test, then run the refusal test.
set -u
src="$1"; dst="$2"
rm -rf "$dst"; mkdir -p "$dst/util/ad-hoc" "$dst/tests"
cp "$src/util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash" "$src/util/ad-hoc/2026-09-22_confirm_a0_premise.bash" "$dst/util/ad-hoc/"
cp "$src/tests/test_a0_restore_scripts.py" "$src/tests/redacted_env.py" "$dst/tests/"
[[ -e "$src/tests/__init__.py" ]] && cp "$src/tests/__init__.py" "$dst/tests/"
sed -i 's#/home/pcalnon#/nonexistent-r6home#g' "$dst/util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash" "$dst/tests/test_a0_restore_scripts.py"
cd "$dst" || exit 2
env -i PATH=/usr/bin:/bin HOME="$dst" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
    tests.test_a0_restore_scripts.RestoreServerDbFromFileset.test_refuses_a_restore_directory_inside_the_backup_source 2>&1 | tail -15
