# Record the 2026-09-22 owner rulings on the seven open backup-design gates

## Summary

`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` carried
fourteen owner decisions, of which **seven blocked P0**. All seven were ruled by the owner in one
interactive session on 2026-09-22. This PR records them as binding in the document of record and
updates the three artifacts whose content the rulings change.

D-3, D-5, D-7, D-10, D-11, D-12 and D-13 remain **open** and keep their recommendations.

## The rulings

| ID | Ruling |
| --- | --- |
| D-1 | **Keep database encryption** — distinct random key, `/etc/credstore/duplicati-settings-key` 0600, `LoadCredential=`, `--require-db-encryption-key` |
| D-2 | **Rotate the passphrase and KEEP the existing sets** — scrub first, then re-encrypt all 877 volumes, staged and verified before any swap |
| D-4 | **`CAP_DAC_READ_SEARCH`**, paired with the §7.3.2 confinement set |
| D-6 | **Root-owned installed copy, plus a drift gate** — blessed sha256 per file, `--update-backup-behavior` as the escape hatch |
| D-8 | **Scrub once, after P1** |
| D-9 | **Loopback only** |
| D-14 | **Read-only destination model** — dirs `duplicati:duplicati 2750`, files `0640`, `UMask=0027` |

## Two rulings that changed the design rather than just selecting from it

**D-6 came back stronger than the recommendation.** The recommendation was a bare copy. The owner
added a no-change gate with an explicit `--update-backup-behavior` switch, which catches two things
a bare copy cannot: an installed artifact edited outside the installer, and a repository that has
moved ahead of what is deployed. A symlink form was proposed and rejected on one decisive fact —
on a fresh host the checkout does not exist yet, so a symlink at the install path is **dangling and
`ExecStart` fails**, defeating the bare-metal recovery case it was proposed for.

**D-2 required correcting two variable names before it could be recorded.** The instruction named
`SETTINGS_ENCRYPTION_KEY` / `SETTINGS_ENCRYPTION_KEY_OLD` for the backup passphrase. Verified
against this host:

- `SETTINGS_ENCRYPTION_KEY` encrypts the **server database**, not the backup volumes. The volume
  secret is the job's `PASSPHRASE`.
- `SETTINGS_ENCRYPTION_KEY_OLD` and `PASSPHRASE_OLD` **do not exist in 2.4.0.0** — 0 hits across
  1,443 files in UTF-8 *and* UTF-16LE (`util/ad-hoc/2026-09-22_duplicati_literal_scan.py`).
- §4.1 already records that on this host the active `SETTINGS_ENCRYPTION_KEY` **equals**
  `PASSPHRASE` — the same conflation, already made once, and part of what broke.

As stated it would have re-keyed the database and left all 877 volumes under the leaked passphrase.
Recorded in the corrected form, with the reasoning in note (10.1b).

## The finding that made D-2 possible

The design asserted flatly that "rotation does not re-encrypt existing volumes", which framed D-2 as
*accept the exposure* vs *abandon 202.8 GiB of history*. That is true of a rotation and **not** of
the product: `Duplicati.CommandLine.RecoveryTool.Implementation.dll` carries a `recompress` verb
taking `--reencrypt` and `--new-passphrase`. Read out of the assembly rather than by executing it
(`util/ad-hoc/2026-09-22_recoverytool_verbs.py`) — on this host `duplicati-server --version` starts
a server, so an information request is not automatically a safe one.

New §10.2 sequences the rotation and names the three hazards that ride with it: `--reupload` deletes
the destination originals; the local database must be deleted and recreated; and `--new-passphrase=`
on argv is world-readable via `/proc/*/cmdline`, the same defect class §7.3.6 already forbids.

## Changes

**Changed**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
(new §10.1 rulings and §10.2 rotation procedure; §7.4 table and script rewritten to the read-only
model; §7.3.2 `UMask=0007` → `0027`; §7.3.4 installer gains the drift gate; §8 step 0 becomes a
verification; §6 S-3 corrected and note S-3b added), `util/systemd/duplicati.service`,
`util/install_duplicati_service.bash`, `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`.

**Added**: `util/ad-hoc/2026-09-22_apply_owner_rulings.py` (the anchor-asserted edit script),
`util/ad-hoc/2026-09-22_recoverytool_verbs.py` (assembly probe),
`util/ad-hoc/2026-09-22_shepherd_automerge.bash` (contended-lane merge shepherd).

The three artifacts are **generated** from tagged blocks in the design by
`util/ad-hoc/2026-09-22_stage_design_artifacts.py`, so they are changed by editing the design and
re-staging — which is the only way they cannot drift apart.

## Verification

- `markdownlint 0.42.0` (the **pinned** hook version, not the 0.48.0 also in the cache) — exit 0.
- Snippet linter: **14 blocks, 0 failures** — `systemd-analyze verify` passed the unit carrying the
  new `UMask=0027`, `shellcheck` passed the installer carrying the drift gate.
- `util/markdown_structure_delta.py --base origin/main`: **0 → 0**, no regressions.
- Staging re-run after a rebuild from the pristine blob: **0 staged, 13 already current** — the
  design→artifact pipeline reproduces byte-identically.
- The edit script is idempotent: a second run reports every edit `ALREADY` and writes nothing.

## Two defects found and fixed in the tooling itself

1. **A non-idempotent edit applied twice.** The drift-gate edit's anchor was a *prefix* of its
   replacement, so the anchor still matched afterwards and a re-run inserted the block a second
   time. The `ALREADY` check could not catch it — the anchor count is 1, not 0. The fix is a guard
   in `edit()` that refuses any edit whose `old` is a substring of its `new`; it immediately caught
   a **second** instance in the S-3b note edit.
2. **The over-width check ran after the write.** A check after the write is a report, not a gate —
   the first run wrote the file and *then* reported a 611-char table row. It now runs before.

## Requirements

References JR-DEP-SEC-005.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_016TcEz8juUrgh8PWf2LqZGX
