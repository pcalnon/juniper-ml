#!/usr/bin/env python3
"""Stage the backup design's tagged code blocks as real repository files.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc -- migration
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md section 8

Consensus round 2 (Lane B, actionability) found that section 8 tells an operator to run nine
repository paths that do not exist -- every artifact lived only as a tagged block inside the
design. `util/install_duplicati_service.bash` would have exited 2 naming the missing guard, on
the day of the recovery. This script closes that gap: it extracts each tagged block with the
design's own linter and writes it to its repository home, so P0 step -1 is a `git diff` rather
than a copy-and-paste onto a root prompt.

DELIBERATELY NOT STAGED:
  home/duplicati/.config/Duplicati/.env
      A `.env` contract, not a repository file. The `no-unencrypted-env` pre-commit hook blocks
      unencrypted `.env` files, correctly, and this one is documentation of a grammar rather
      than a deployable artifact.

Usage:  python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py [--check]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DESIGN = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")
LINTER = Path("util/ad-hoc/2026-09-21_lint_design_snippets.py")

# tagged block path  ->  (repository path, mode)
STAGE: dict[str, tuple[str, int]] = {
    "etc/default/duplicati": ("util/systemd/duplicati.default", 0o644),
    "etc/systemd/system/duplicati.service": ("util/systemd/duplicati.service", 0o644),
    "usr/local/lib/duplicati/duplicati-wrapper.bash": ("scripts/duplicati-wrapper.bash", 0o755),
    "usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash": ("util/yamaguchi-pre-backup-guard.bash", 0o755),
    "util/install_duplicati_service.bash": ("util/install_duplicati_service.bash", 0o755),
    "util/juniper-backup-scheduled.bash": ("util/juniper-backup-scheduled.bash", 0o755),
    "util/ad-hoc/2026-09-21_backup_destination_permissions.bash": (
        "util/ad-hoc/2026-09-21_backup_destination_permissions.bash", 0o755),
    "util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash": (
        "util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash", 0o755),
    "util/ad-hoc/2026-09-22_confirm_a0_premise.bash": (
        "util/ad-hoc/2026-09-22_confirm_a0_premise.bash", 0o755),
    "util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash": (
        "util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash", 0o755),
    "home/pcalnon/.config/systemd/user/juniper-backup.timer": ("util/systemd/juniper-backup.timer", 0o644),
    "home/pcalnon/.config/systemd/user/juniper-backup.path": ("util/systemd/juniper-backup.path", 0o644),
    "home/pcalnon/.config/systemd/user/juniper-backup.service": ("util/systemd/juniper-backup.service", 0o644),
}

SKIP = {"home/duplicati/.config/Duplicati/.env"}

# A value that looks like a credential must never reach a staged file. The wrapper's old header
# carried a 36-character literal; this is the screen that keeps its replacement clean.
SECRET_SHAPED = re.compile(r"""(?ix)
    (SETTINGS_ENCRYPTION_KEY|PASSPHRASE(_OLD)?|DUPLICATI_WEB_CREDENTIAL|webservice-password)
    \s*=\s*
    (?!["']?\s*$)               # not an empty assignment
    (?!["']?\$)                 # not a variable reference
    (?!["']?<)                  # not a <placeholder>
    ["']?[^\s"']{12,}
""")


def extract(workdir: Path) -> dict[str, Path]:
    workdir.mkdir(parents=True, exist_ok=True)
    rc = subprocess.run(
        [sys.executable, str(LINTER), "--doc", str(DESIGN), "--workdir", str(workdir)],
        capture_output=True, text=True,
    )
    if "failures: 0" not in rc.stdout:
        print(rc.stdout[-3000:], file=sys.stderr)
        raise SystemExit("snippet linter did not report failures: 0 -- refusing to stage")
    found: dict[str, Path] = {}
    for tag in list(STAGE) + list(SKIP):
        p = workdir / tag
        if p.is_file():
            found[tag] = p
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    # The workdir MUST be absolute. The linter rewrites each unit's Exec* target to a path
    # inside it so `systemd-analyze verify` can resolve them, and verify rejects a relative
    # ExecStart with "bad unit file setting" -- which reads as a defect in the design's unit
    # rather than in the harness. Default to a scratch tree outside the repository.
    workdir = Path(args.workdir).resolve() if args.workdir else Path(tempfile.mkdtemp(prefix="stage-extract-"))
    found = extract(workdir)

    missing = [t for t in STAGE if t not in found]
    if missing:
        for t in missing:
            print(f"MISSING tagged block: {t}", file=sys.stderr)
        return 1

    changed = unchanged = 0
    for tag, (dest_s, mode) in sorted(STAGE.items()):
        src, dest = found[tag], Path(dest_s)
        body = src.read_text(encoding="utf-8")

        hit = SECRET_SHAPED.search(body)
        if hit:
            print(f"REFUSING {dest}: credential-shaped assignment near offset {hit.start()}", file=sys.stderr)
            return 2

        same = dest.is_file() and dest.read_text(encoding="utf-8") == body
        if same:
            unchanged += 1
            print(f"  ==  {dest}")
            continue
        changed += 1
        verb = "would write" if args.check else "wrote"
        print(f"  {'->' if args.check else '++'}  {dest}  ({verb}, {len(body)} bytes, mode {oct(mode)})")
        if not args.check:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body, encoding="utf-8")
            dest.chmod(mode)

    for tag in sorted(SKIP):
        print(f"  --  {tag}  (deliberately not staged; see the module docstring)")

    if not args.workdir:
        shutil.rmtree(workdir, ignore_errors=True)

    print(f"\n{changed} staged, {unchanged} already current, {len(SKIP)} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
