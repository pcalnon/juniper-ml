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

FORMERLY NOT STAGED:
  home/duplicati/.config/Duplicati/.env
      The `.env` contract was documentation of a grammar until 2026-10-03 (round 3's D13, the
      assessment's B8): it now deploys to /etc/duplicati/env from util/systemd/duplicati-env.contract --
      a name the `no-unencrypted-env` pre-commit hook does not match, and a file that carries no
      secret by contract (the installer never overwrites an existing copy).

Usage:  python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py [--check]
        python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --from-repo

DIRECTION. Without a flag the DESIGN is canonical and this script writes its tagged blocks over the
repository files -- the direction the 2026-09-22 migration needed. Since ml#1999 landed the nine
artifacts, the REPOSITORY is canonical: an artifact is changed in its repository file, reviewed and
tested there, and the design's tagged block must follow. `--from-repo` does that: it rewrites each
tagged block's body in the design from the repository file (2026-10-03, the assessment's I-33; a
Phase B change to the defaults file or the installer would otherwise read as "drift" under
`--check`, and the documented remedy -- re-stage -- would REVERT the fix). A block whose deployment path
moved is renamed by `--from-repo` through RETAG before its body is rewritten, so a moved artifact needs no
hand edit of the design. `--check` is direction-free: it reports where the two disagree and writes nothing.
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
    "etc/duplicati/env": ("util/systemd/duplicati-env.contract", 0o644),
}

SKIP: set[str] = set()   # the .env contract joined STAGE on 2026-10-03 (etc/duplicati/env)

# A tagged block whose deployment path MOVED keeps its body under the new tag. `--from-repo` renames the
# marker line first, so the rename is recorded here rather than done by hand (round 3's D13: the env
# contract left the 0700 data folder for /etc/duplicati/env on 2026-10-03).
RETAG: dict[str, str] = {
    "home/duplicati/.config/Duplicati/.env": "etc/duplicati/env",
}

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


def from_repo() -> int:
    """Rewrite each tagged block's body in the design from its repository file (repository canonical)."""
    marker_re = re.compile(r"^\s*[#;]\s*file:\s*(\S+)\s*$")
    lines = DESIGN.read_text(encoding="utf-8").split("\n")
    by_tag = {tag: Path(dest) for tag, (dest, _mode) in STAGE.items()}
    seen: dict[str, int] = {}
    changed = unchanged = retagged = 0
    i = 0
    while i < len(lines):
        if not lines[i].startswith("```"):
            i += 1
            continue
        start = i + 1
        j = start
        while j < len(lines) and not lines[j].startswith("```"):
            j += 1
        if j >= len(lines):
            print("FATAL: unterminated fence in the design", file=sys.stderr)
            return 2
        mk = marker_re.match(lines[start]) if j > start else None
        tag = mk.group(1) if mk else None
        if tag in RETAG:
            new_tag = RETAG[tag]
            lines[start] = lines[start].replace(tag, new_tag, 1)
            print(f"  ->  {tag}  (marker retagged {new_tag})")
            retagged += 1
            tag = new_tag
        if tag in by_tag:
            seen[tag] = seen.get(tag, 0) + 1
            src = by_tag[tag]
            if not src.is_file():
                print(f"MISSING repository file for {tag}: {src}", file=sys.stderr)
                return 1
            body = src.read_text(encoding="utf-8")
            if not body.endswith("\n"):
                print(f"REFUSING {src}: no trailing newline", file=sys.stderr)
                return 2
            hit = SECRET_SHAPED.search(body)
            if hit:
                print(f"REFUSING {src}: credential-shaped assignment near offset {hit.start()}", file=sys.stderr)
                return 2
            new_body = body[:-1].split("\n")
            old_body = lines[start + 1:j]
            if new_body == old_body:
                unchanged += 1
                print(f"  ==  {tag}")
            else:
                changed += 1
                print(f"  <-  {tag}  (block rewritten from {src}, {len(new_body)} lines)")
                lines[start + 1:j] = new_body
                j = start + 1 + len(new_body)
        i = j + 1
    missing = [t for t in STAGE if t not in seen]
    dupes = [t for t, n in seen.items() if n > 1]
    if missing or dupes:
        for t in missing:
            print(f"MISSING tagged block: {t}", file=sys.stderr)
        for t in dupes:
            print(f"DUPLICATE tagged block: {t} ({seen[t]}x)", file=sys.stderr)
        return 1
    if changed or retagged:
        DESIGN.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{changed} block(s) rewritten from the repository, {unchanged} already identical, {retagged} marker(s) retagged")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    ap.add_argument("--from-repo", action="store_true",
                    help="repository canonical: rewrite the design's tagged blocks from the repository files")
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    if args.from_repo and args.check:
        ap.error("--from-repo and --check are exclusive")
    if args.from_repo:
        return from_repo()

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
