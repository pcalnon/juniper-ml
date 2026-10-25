"""
Apply the tier-3 backup lane's edits to the shared files, idempotently: ci.yml, docs/REFERENCE.md, AGENTS.md, CHANGELOG.md, the design.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — one-off (the tier-3 full-set lane: owner ruling D-5 of 2026-10-25 on §7.9 of the backup design)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md (§7.9, §8 P3 step 3, §10 D-5);
         util/ad-hoc/2026-10-21_turing_h4_apply.py (the pattern this follows)

Why: the lane lands through the GitHub API as whole-file uploads, and four of these files are the busiest in the
repository. An upload built from an older base silently reverts whatever main gained since. So the edits live here,
keyed on anchors, and are re-applied to a fresh origin/main copy right before the upload.

The edits:
- ci.yml: the regression step runs tests/test_juniper_backup_tier3_lane.py right after the tier-2 suite.
- docs/REFERENCE.md: in § Juniper Project-Tree Backup, the JUNIPER_BACKUP_DIR row, the default-repos paragraph, a new
  "Scheduled lane (tier 3, full set)" subsection and three pitfall rows; the suite in "Running every suite" and its
  count history; the suite's entry in § Test Suite Reference; the runner's and the installer's utility entries.
- AGENTS.md: the suite count follows ci.yml's regression step, and **Last Updated** takes today's UTC date.
- CHANGELOG.md: an [Unreleased] / Added entry.
- The design: ONE dated as-built note at the end of §7.9, and nothing else (the owner's instruction for this change).

Each edit has a marker. When the marker is already present the edit is skipped; otherwise its anchor must occur
exactly once. A re-run on a newer main therefore applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-25_backup_tier3_shared_file_edits.py [--root REPO_ROOT] [--dry-run] [--mutants N]

--mutants N fills the mutation tally that util/ad-hoc/2026-10-25_juniper_backup_tier3_mutation_check.py reported
("N of N"); without it the text says "every one of its mutants".

Exit 0 = every edit applied or already present; 1 = an anchor is missing or ambiguous (nothing written).
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

DESIGN = "notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md"
CI = ".github/workflows/ci.yml"
REFERENCE = "docs/REFERENCE.md"
LINE = "python3 -m unittest -v tests/test_juniper_backup_tier3_lane.py"
TIER2_LINE = "python3 -m unittest -v tests/test_juniper_backup_tier2_lane.py"
DEVICE = "dee46823-4119-4914-ac15-08194ee27d81"

CI_SUITE = (
    "          # tests/test_juniper_backup_tier3_lane.py: the tier-3 full-set lane (backup design\n"
    "          # §7.9, D-5). JUNIPER_BACKUP_DIR may be a relative path (Juniper/Backups) in the runner\n"
    "          # and the scheduler, through one function whose body is byte-identical in both; the\n"
    "          # four juniper-backup-full units as written and as systemd runs them; separate locks,\n"
    "          # statuses and stamps for the two lanes; the installer's --lane full. It imports the\n"
    "          # tier-2 suite's fixture: PATH-stubbed, scratch trees only, never a real drive.\n"
    f"          {LINE}\n"
)
CI_SUITE_ANCHOR = f"          {TIER2_LINE}\n"

DIR_ROW_OLD = "| `JUNIPER_BACKUP_DIR` | `Juniper-8.0.0.python` | Directory on each drive that receives the archives. |"
DIR_ROW_NEW = (
    "| `JUNIPER_BACKUP_DIR` | `Juniper-8.0.0.python` | Directory on each drive that receives the archives, as a path relative to the drive: one or more "
    "`[A-Za-z0-9._-]+` components joined by single slashes, none of them `.` or `..`, so no leading, trailing or doubled `/`. Tier 3 uses "
    "`Juniper/Backups`. The scheduler applies the same check (one function, its body byte-identical) and records `FAILED`, exit 2. |"
)
REPOS_OLD = "A missing leaf is a WARNING skip; zero found is FATAL. `juniper-legacy` is **not** in the default list."
REPOS_NEW = (
    REPOS_OLD + " Tier 3 archives it, with the parent-level `notes`, `prompts`, `util` and `backups`, through `--repos`: "
    "[Scheduled lane (tier 3, full set)](#scheduled-lane-tier-3-full-set)."
)

TIER3_SECTION_ANCHOR = "\n### Operator pitfalls\n\n| Symptom | Cause / fix |\n|---------|-------------|\n| `tar` cannot extract a `.tbz2.gpg` |"
TIER3_SECTION = f"""
### Scheduled lane (tier 3, full set)

`bash util/install_juniper_backup_timer.bash --lane full [--dry-run]` installs tier 3 under `systemd --user`: §7.9 of [the backup design](../{DESIGN}), whose default the owner ruled for D-5 on 2026-10-25. It installs the same three scripts as tier 2 and the four units below, and touches none of tier 2's units. No `--lane`, or `--lane usb`, is the tier-2 install exactly.

| Installed | From |
|-----------|------|
| `~/.local/bin/juniper-backup.bash`, `juniper-backup-scheduled.bash`, `duplicati-backup-failure.bash` | the same files as tier 2, so installing either lane updates both |
| `~/.config/systemd/user/juniper-backup-full.{{timer,path,service}}` | `util/systemd/` |
| `~/.config/systemd/user/juniper-backup-full-failure.service` | `util/systemd/` |

It then runs `systemctl --user daemon-reload` and `systemctl --user enable --now juniper-backup-full.timer juniper-backup-full.path`.

The lane is tier 2's scheduler and runner with its own environment, set in `juniper-backup-full.service`:

| Setting | Value | Why |
|---------|-------|-----|
| `JUNIPER_BACKUP_STATE_DIR` | `~/.local/state/juniper-backup-full` | Its own lock, `last-run.status` and `last-success.*` stamps. Shared with tier 2, a tier-2 success would hide a stale full set. |
| `JUNIPER_BACKUP_DEVICES` | `{DEVICE}` | "Ext WD Passport, Blackbox Part 1", by filesystem UUID, per the owner's `/etc/fstab`; it mounts at `/run/media/<user>/<UUID>`. This is the relative form under the default root, so the scheduler and the runner name one path. The fstab deprecates `/mnt/JuniperArchive`, the path §7.9 proposed. |
| `JUNIPER_BACKUP_DIR` | `Juniper/Backups` | The owner's directory on that drive. Two components, which the runner and the scheduler accept from 1.1.0. |
| `JUNIPER_BACKUP_PERIOD_DAYS` | `30` | Monthly. |
| `JUNIPER_BACKUP_STALE_DAYS` | `45` | The period plus two weeks. It must be at least the period, or a drive connected before its set is due reads `FAILED`. |

Its `ExecStart=` passes `--label full --repos "<the runner's ten APPLICATION_REPOS> juniper-legacy notes prompts util backups"`, and the scheduler hands both to the runner unchanged; the runner validates them before it probes anything. Each archive is `Juniper_full_<entry>_<uuid>_<stamp>.tbz2.gpg`, encrypted to the same two `ENCRYPT_KEYS` recipients. The timer fires on the 1st of each month at 04:00. With the drive kept offline it usually finds the drive detached, so it is the lane's staleness check; the run that writes a set is the path unit's, on connection.

**The two lanes do not interfere.** Both path units watch `/run/media/pcalnon`, so every mount or unmount starts both services. Each scheduler judges only its own drive, from its own state directory and under its own `flock` (`<state dir>/run.lock`). So one lane's held lock never makes the other skip, and one lane's success never resets the other's staleness. The device lists are disjoint, so each lane writes only its own drives. `install(1)` replaces an installed script with a new inode, so installing one lane during the other's run does not change that run.

**The first runs, in order.** The installer prints the same notes in both modes.

1. Connect the drive. The path unit starts the run, which takes hours. If `last-run.status` has not been written a minute after the mount, the trigger may have come before the mount completed. Start it by hand with `systemctl --user start --no-block juniper-backup-full.service`. Without `--no-block` a oneshot start blocks until the run ends. If the drive is already mounted when you install, no mount event comes at all (`PathChanged=` does not fire when the path unit starts), so start that first run by hand the same way.
2. Disconnect the drive only after `~/.local/state/juniper-backup-full/last-run.status` reads `result=OK`. The unplug starts the check again, and it then reads `SKIPPED`.
3. Until that first success, a run with the drive detached reads `FAILED` and `OnFailure=` fires. That includes the check that every plug-in or unplug of a tier-2 stick starts.
4. AC-11: restore one archive and compare it with the live tree: `gpg -d <archive> | tar -xjf - -C <an empty directory>`.

A drive connected less than 30 days after the last success reads `SKIPPED` (none due). **Retention is manual.** Keep the last three `full` sets, and delete an older set (every archive bearing its UUID) only after a restore drill of the newest passes. Nothing prunes.
"""

PITFALL_ANCHOR = "| Archive huge / includes `data/` `venv/` |"
PITFALL_ROWS = (
    "| Tier 3: a connected drive reads `SKIPPED`, none due within 30 days | The last full set is under 30 days old. Wait, or remove `~/.local/state/juniper-backup-full/last-success.<UUID>` to force one. |\n"
    "| `Backup FAILED: juniper-backup-full.service` when a tier-2 stick was plugged in | Both path units fire on every mount. Tier 3 has never succeeded, or not within 45 days. Do a full set ([Scheduled lane (tier 3, full set)](#scheduled-lane-tier-3-full-set)). |\n"
    "| `FATAL: JUNIPER_BACKUP_DIR must be a relative path …` | A leading, trailing or doubled `/`, or a `.` or `..` component. The scheduler records `FAILED`, `malformed JUNIPER_BACKUP_DIR`, exit 2. |\n"
)

RUN_LIST_ANCHOR = f"\n{TIER2_LINE}\n"
RUN_LIST_COUNT = "**224** with H4's `tests/test_mcp_setup.py`"
RUN_LIST_COUNT_NEW = RUN_LIST_COUNT + ", **225** with the tier-3 backup lane's `tests/test_juniper_backup_tier3_lane.py`"

SUITE_REF_ANCHOR = "- `tests/test_check_conda_env_torch.py` -- Hermetic exit-matrix tests for `util/check_conda_env_torch.bash`"
RUNNER_UTIL_OLD = "Every mount root must lie under `/mnt`, `/media` or `/run/media` (exit 2 otherwise), and exit 0 needs every configured device mounted."
RUNNER_UTIL_NEW = RUNNER_UTIL_OLD + " `JUNIPER_BACKUP_DIR` may be a relative path of plain components (1.1.0), checked by the same function as the scheduler's."
INSTALLER_UTIL_OLD = (
    "and the reporter (1.1.0) titles the notification with the failed unit. Operator surface: [Juniper Project-Tree Backup](#juniper-project-tree-backup).\n"
    "- `util/ad-hoc/yamaguchi_server_api.py`"
)
INSTALLER_UTIL_NEW = (
    "and the reporter (1.1.0) titles the notification with the failed unit. Operator surface: [Juniper Project-Tree Backup](#juniper-project-tree-backup). "
    "`--lane full` (installer 1.1.0) installs tier 3 instead: `util/systemd/juniper-backup-full{,-failure}.service` and `util/systemd/juniper-backup-full.{timer,path}`, "
    "the monthly full set to the offline drive under its own state directory, `~/.local/state/juniper-backup-full`. No `--lane` is `--lane usb`, the tier-2 install unchanged. "
    "Operator surface: [Scheduled lane (tier 3, full set)](#scheduled-lane-tier-3-full-set).\n"
    "- `util/ad-hoc/yamaguchi_server_api.py`"
)

CHANGELOG_ANCHOR = "## [Unreleased]\n\n"
# When a concurrent PR has already opened [Unreleased] / Added, the entry goes first under that heading instead of
# opening a second one.
CHANGELOG_ADDED_ANCHOR = "## [Unreleased]\n\n### Added\n\n"

DESIGN_ANCHOR = "- **Offline discipline**: the drive is connected for the run and disconnected afterwards; the scheduler's `.path` unit makes the run happen on connection.\n\n### 7.10 Coverage gaps"
DESIGN_NOTE = (
    "*(As built 2026-10-25, after D-5 ruled this default: the drive is the fstab's \"Blackbox Part 1\", "
    f"`JUNIPER_BACKUP_DEVICES={DEVICE}` under the default `/run/media/$USER` root, with `JUNIPER_BACKUP_DIR=Juniper/Backups` "
    "(the fstab deprecates `/mnt/JuniperArchive`); `juniper-backup-full.{timer,path,service}` run it from its own state directory, "
    "`~/.local/state/juniper-backup-full`, `bash util/install_juniper_backup_timer.bash --lane full` installs them, and deletion stays manual.)*"
)
DESIGN_REPLACEMENT = DESIGN_ANCHOR.replace("\n\n### 7.10 Coverage gaps", "\n\n" + DESIGN_NOTE + "\n\n### 7.10 Coverage gaps")


def tally(mutants):
    return f"{mutants} of {mutants} mutants" if mutants else "every one of its mutants"


def suite_entry(mutants):
    return (
        "- `tests/test_juniper_backup_tier3_lane.py` -- The tier-3 full-set lane (§7.9 and D-5 of the backup design). It imports the tier-2 suite's fixture and stages the four full units beside it, unchanged. It pins:\n"
        "  - **The backup-dir rule.** `JUNIPER_BACKUP_DIR` may be a relative path. Fifteen malformed forms (a leading, trailing or doubled `/`, `.` or `..` components, a space, a newline, glob and shell characters) "
        "are exit 2 in the runner and `FAILED`, exit 2, in the scheduler, before any drive is probed. One-component values are judged exactly as before. `is_backup_dir`'s body is byte-identical in the two scripts, and they agree on every case.\n"
        "  - **The units as written.** The service's Environment= (its own state dir, the fstab UUID, `Juniper/Backups`, 30 and 45 days, no media-root override) and its `--label full --repos` list, "
        "which is the runner's ten `APPLICATION_REPOS` plus `juniper-legacy notes prompts util backups`. The failure unit routes the shared reporter to the lane's state dir, the path unit watches tier 2's directory with `PathChanged=`, and the timer is monthly and persistent.\n"
        "  - **End to end, as systemd runs the installed unit.** The OK run writes one `Juniper_full_<entry>_…` archive per entry into the nested directory and stamps only this lane. "
        "Unplugged is `FAILED` until the first success and `SKIPPED` after it; a 45.5-day stamp is `SKIPPED` and a 46.5-day one `FAILED`; a 29.5-day stamp is not due and a 30.5-day one is. "
        "The failure unit, executed as written, records into this lane and titles `Backup FAILED: juniper-backup-full.service`.\n"
        "  - **Lane independence.** Holding one lane's lock never makes the other skip, one lane's success never hides the other's staleness, and with every drive mounted each lane writes only its own.\n"
        "  - **The installer's `--lane`.** `--lane full`'s dry run, copies, enable line, acceptance notes and refusals, and that it leaves tier 2's units alone. No `--lane` equals `--lane usb`, and an unknown or missing lane is exit 2 and writes nothing. "
        f"`util/ad-hoc/2026-10-25_juniper_backup_tier3_mutation_check.py` kills {tally(mutants)}, the three pre-change scripts among them, and runs its control under both uutils and GNU coreutils.\n"
    )


def changelog_entry(mutants, tests, heading=True):
    return ("### Added\n\n" if heading else "") + (
        "- **Tier 3: the monthly full set to the offline drive, as a scheduled lane** (owner ruling D-5, 2026-10-25, on §7.9\n"
        f"  and §8 P3 step 3 of `{DESIGN}`).\n"
        "  - **The units** (new): `util/systemd/juniper-backup-full.{timer,path,service}` and\n"
        "    `util/systemd/juniper-backup-full-failure.service`. The service runs tier 2's scheduler and runner with the lane's\n"
        "    own environment: state directory `~/.local/state/juniper-backup-full`, drive\n"
        f"    `{DEVICE}` (\"Ext WD Passport, Blackbox Part 1\" in the owner's `/etc/fstab`, mounted at\n"
        "    `/run/media/<user>/<UUID>`), directory `Juniper/Backups`, a 30-day period and a 45-day staleness limit. Its\n"
        "    `--label full --repos \"…\"` names the ten application repos, `juniper-legacy` and the parent-level\n"
        "    `notes prompts util backups`, and the scheduler hands both to the runner unchanged. The timer fires monthly and\n"
        "    the path unit on connection. The owner's fstab deprecates `/mnt/JuniperArchive`, so the path that §7.9 of\n"
        f"    `{DESIGN}` proposed\n"
        "    is superseded, and that section gains a dated as-built note. Retention stays manual: nothing prunes.\n"
        "  - **`JUNIPER_BACKUP_DIR` may be a path.** `util/juniper-backup.bash` 1.1.0 accepts a relative path of\n"
        "    `[A-Za-z0-9._-]+` components (no empty, `.` or `..` component, no leading `/`) and judges every one-component\n"
        "    value as before. `util/juniper-backup-scheduled.bash` 1.1.0, which checked nothing, runs the same function (its\n"
        "    body byte-identical) and records a malformed value as `FAILED`, exit 2, before it probes a drive.\n"
        "  - **The installer.** `util/install_juniper_backup_timer.bash` 1.1.0 gains `--lane full`: the three shared scripts\n"
        "    and the four full units, copied rather than symlinked, with `--dry-run`, then the full timer and path unit\n"
        "    enabled. No `--lane`, or `--lane usb`, is the tier-2 install unchanged. `util/duplicati_backup_failure.bash`'s\n"
        "    header lists the third caller.\n"
        "  - **The lanes are independent.** Separate state directories give each lane its own lock, status and stamps, so\n"
        "    one lane's run never blocks or skips the other's, and one lane's success never hides the other's staleness. Both\n"
        "    path units watch `/run/media/pcalnon`, so every mount starts both checks, and each judges only its own drive.\n"
        f"  - **The gate.** `tests/test_juniper_backup_tier3_lane.py` (new, {tests} tests) is wired into `ci.yml` and\n"
        "    `docs/REFERENCE.md`, which documents the lane in § Juniper Project-Tree Backup.\n"
        f"    `util/ad-hoc/2026-10-25_juniper_backup_tier3_mutation_check.py` (new) shows that it kills {tally(mutants)}.\n"
        "    The tier-2 suite passes unchanged, and `util/ad-hoc/2026-10-03_juniper_backup_tier2_mutation_check.py` still\n"
        "    kills 30 of 30. `util/ad-hoc/2026-10-25_backup_tier2_install_parity.py` (new) shows that the installer's\n"
        "    default lane installs exactly what the one it replaces did, and\n"
        "    `util/ad-hoc/2026-10-25_backup_tier3_host_resolution_probe.bash` (new) shows, read-only, that both scripts\n"
        "    resolve the drive's `Juniper/Backups` on the host from the unit's own settings.\n"
        "\n"
    )


def edits(mutants, tests, changelog_has_added=False):
    """(path, marker, anchor, replacement). The replacement keeps the anchor and adds the tier-3 text."""
    return [
        (CI, LINE, CI_SUITE_ANCHOR, CI_SUITE_ANCHOR + CI_SUITE),
        (REFERENCE, "Tier 3 uses `Juniper/Backups`. The scheduler applies the same check", DIR_ROW_OLD, DIR_ROW_NEW),
        (REFERENCE, "Tier 3 archives it, with the parent-level", REPOS_OLD, REPOS_NEW),
        (REFERENCE, "### Scheduled lane (tier 3, full set)", TIER3_SECTION_ANCHOR, TIER3_SECTION + TIER3_SECTION_ANCHOR),
        (REFERENCE, "| Tier 3: a connected drive reads `SKIPPED`", PITFALL_ANCHOR, PITFALL_ROWS + PITFALL_ANCHOR),
        (REFERENCE, f"\n{TIER2_LINE}\n{LINE}\n", RUN_LIST_ANCHOR, f"\n{TIER2_LINE}\n{LINE}\n"),
        (REFERENCE, "**225** with the tier-3 backup lane's", RUN_LIST_COUNT, RUN_LIST_COUNT_NEW),
        (REFERENCE, "- `tests/test_juniper_backup_tier3_lane.py` --", SUITE_REF_ANCHOR, suite_entry(mutants) + SUITE_REF_ANCHOR),
        (REFERENCE, "`JUNIPER_BACKUP_DIR` may be a relative path of plain components (1.1.0)", RUNNER_UTIL_OLD, RUNNER_UTIL_NEW),
        (REFERENCE, "`--lane full` (installer 1.1.0) installs tier 3 instead", INSTALLER_UTIL_OLD, INSTALLER_UTIL_NEW),
        (
            "CHANGELOG.md",
            "**Tier 3: the monthly full set to the offline drive, as a scheduled lane**",
            CHANGELOG_ADDED_ANCHOR if changelog_has_added else CHANGELOG_ANCHOR,
            (CHANGELOG_ADDED_ANCHOR if changelog_has_added else CHANGELOG_ANCHOR) + changelog_entry(mutants, tests, heading=not changelog_has_added),
        ),
        (DESIGN, "*(As built 2026-10-25, after D-5 ruled this default", DESIGN_ANCHOR, DESIGN_REPLACEMENT),
    ]


def regression_suites(ci_text):
    start = ci_text.index("- name: Run Python regression tests")
    end = ci_text.index("\n      - name: ", start)
    return len(re.findall(r"^\s+python3 -m unittest -v tests/\S+\.py$", ci_text[start:end], flags=re.M))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mutants", type=int, default=0, help="the tier-3 mutation check's kill count (N of N)")
    ap.add_argument("--tests", type=int, default=47, help="the tier-3 suite's test count")
    args = ap.parse_args(argv)

    texts, failed = {}, 0
    has_added = CHANGELOG_ADDED_ANCHOR in (args.root / "CHANGELOG.md").read_text(encoding="utf-8")
    for rel, marker, anchor, repl in edits(args.mutants, args.tests, has_added):
        text = texts.get(rel)
        if text is None:
            text = (args.root / rel).read_text(encoding="utf-8")
        if marker in text:
            print(f"present  {rel}: {marker.strip()[:60]!r}")
        elif text.count(anchor) == 1:
            text = text.replace(anchor, repl)
            print(f"apply    {rel}: {marker.strip()[:60]!r}")
        else:
            print(f"FAIL     {rel}: anchor found {text.count(anchor)} times: {anchor.strip()[:60]!r}")
            failed += 1
        texts[rel] = text

    agents = (args.root / "AGENTS.md").read_text(encoding="utf-8")
    suites = regression_suites(texts[CI])
    agents, n = re.subn(r"the full ordered list of \d+ `python3 -m unittest`", f"the full ordered list of {suites} `python3 -m unittest`", agents, count=1)
    if n != 1:
        print("FAIL     AGENTS.md: no suite-count phrase")
        failed += 1
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    agents, n = re.subn(r"^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}$", f"**Last Updated**: {today}", agents, count=1, flags=re.M)
    if n != 1:
        print("FAIL     AGENTS.md: no **Last Updated** line")
        failed += 1
    texts["AGENTS.md"] = agents
    print(f"count    AGENTS.md: {suites} suites in ci.yml's regression step; **Last Updated** = {today} (UTC)")

    if failed:
        print(f"{failed} edit(s) failed; nothing written")
        return 1
    changed = [rel for rel, text in texts.items() if (args.root / rel).read_text(encoding="utf-8") != text]
    for rel in changed:
        if not args.dry_run:
            (args.root / rel).write_text(texts[rel], encoding="utf-8")
    print(f"{'would change' if args.dry_run else 'changed'} {len(changed)} file(s): " + ", ".join(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
