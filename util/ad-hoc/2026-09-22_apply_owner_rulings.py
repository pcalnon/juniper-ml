#!/usr/bin/env python3
"""Record the 2026-09-22 owner rulings on D-1, D-2, D-4, D-6, D-8, D-9 and D-14 in the design.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc -- document-of-record edit
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md section 10
             util/ad-hoc/2026-09-22_stage_design_artifacts.py (regenerates the artifacts these edits change)

EVERY edit asserts its anchor occurs an exact number of times and the driver writes NOTHING if any
assertion fails. That is the same contract as 2026-09-22_reconcile_backup_design.py, and it is what
makes a 2,352-line document of record safe to edit mechanically: a partial application is worse than
no application, because it leaves the design self-contradicting in a way no reader can detect.

This edits the DESIGN, not the artifacts. `util/systemd/duplicati.service`,
`util/install_duplicati_service.bash` and `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`
are all generated from tagged blocks in the design by the staging script, so changing them here and
re-staging is the only way they cannot drift apart.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DESIGN = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")

EDITS: list[tuple[str, str, str, int]] = []


def edit(tag: str, old: str, new: str, count: int = 1) -> None:
    # If `old` survives inside `new`, the anchor still matches after the edit lands and a second
    # run applies it AGAIN. That happened on the first run of this script: the drift-gate block
    # was inserted twice because its anchor was a prefix of its replacement. The ALREADY check in
    # main() cannot catch it -- the anchor count is 1, not 0 -- so the guard belongs here, where
    # the edit is declared, and it is fatal rather than a warning.
    if old in new:
        raise SystemExit(
            f"NON-IDEMPOTENT edit {tag!r}: `old` is a substring of `new`, so re-running would "
            f"apply it twice. Widen the anchor to SPAN the insertion point instead of preceding it."
        )
    EDITS.append((tag, old, new, count))


# --------------------------------------------------------------------------------------------
# D-14 -- read-only destination model. Table, prose, unit UMask, and the script that applies it.
# --------------------------------------------------------------------------------------------

edit(
    "D-14 permission table",
    """| `/mnt/Backups`, `/mnt/Backups/Ubuntu` | `pcalnon:duplicati` | `2770` | traverse for both; setgid keeps the group on new entries |
| `/mnt/Backups/Ubuntu/Dropbox` (Dropbox root) | `pcalnon:duplicati` | `2770` | Dropbox (pcalnon) owns it; the service traverses |
| `/mnt/Backups/Ubuntu/Dropbox/Backups` and every subdirectory | `pcalnon:duplicati` | `2770` + default ACL `g:duplicati:rwx` | new directories inherit; the service can create/rename/delete |
| volumes (`duplicati-*.zip.aes`) | creator`:duplicati` | `0660` | service umask `0007` produces `0660`; Dropbox reads via group |""",
    """| `/mnt/Backups`, `/mnt/Backups/Ubuntu` | `pcalnon:duplicati` | `2750` | traverse for both; setgid keeps the group on new entries |
| `/mnt/Backups/Ubuntu/Dropbox` (Dropbox root) | `pcalnon:duplicati` | `2770` | Dropbox runs as `pcalnon` and must write its own root; the service only traverses (note D-14b) |
| `/mnt/Backups/Ubuntu/Dropbox/Backups` and every subdirectory | `duplicati:duplicati` | `2750` + default ACL `g:duplicati:r-x` | the service owns and writes; `pcalnon` and Dropbox **read** through the group |
| volumes (`duplicati-*.zip.aes`) | `duplicati:duplicati` | `0640` | service `UMask=0027` produces `0640`; Dropbox reads via group and cannot unlink |""",
)

edit(
    "D-14 prose opener",
    """**The group-write model above is itself an open owner decision — D-14.** As written it grants
**write and delete** on all 877 volumes to every process running as `pcalnon` (editors, browsers,""",
    """**D-14 is RULED (2026-09-22): the read-only model above is in force** (§10.1). The rejected
alternative — the R-7/R-8 group-write form, directories `2770` and files `0660` — would have granted
**write and delete** on all 877 volumes to every process running as `pcalnon` (editors, browsers,""",
)

edit(
    "D-14 prose closer",
    """**accident and commodity malware**, not against a deliberate local adversary. D-14 is the owner's
call; the script below implements the R-7/R-8 group-write model as specified, and must be re-run
after a D-14 ruling that changes it.""",
    """**accident and commodity malware**, not against a deliberate local adversary. That limit was stated
before the ruling and the ruling was made with it in view. The script below now implements the
read-only model, and must be run once against the existing tree: it chowns the 877 volumes to
`duplicati` and drops their group-write bit, which is the step that makes a cloud-side delete fail.""",
)

edit(
    "D-14 unit UMask",
    """Group=duplicati
UMask=0007""",
    """Group=duplicati
# D-14 (RULED 2026-09-22): 0027, not 0007. New volumes land 0640 duplicati:duplicati, so pcalnon
# and the Dropbox daemon read them through the group and neither can rewrite or unlink one.
UMask=0027""",
)

edit(
    "D-14 permission script",
    """chgrp duplicati /mnt/Backups /mnt/Backups/Ubuntu /mnt/Backups/Ubuntu/Dropbox
chmod 2770 /mnt/Backups /mnt/Backups/Ubuntu /mnt/Backups/Ubuntu/Dropbox
chgrp -R duplicati "${ROOT}"
find "${ROOT}" -type d -exec chmod 2770 {} +
find "${ROOT}" -type f -exec chmod 0660 {} +
setfacl -R -m g:duplicati:rwX -m d:g:duplicati:rwX "${ROOT}\"""",
    """# D-14 RULED 2026-09-22: the READ-ONLY model. pcalnon and Dropbox read through the group; only
# the service writes. The two mount parents keep 2750, and the Dropbox root keeps 2770 because
# the sync daemon runs as pcalnon and must write its own root -- narrowing that would break sync,
# not harden it. See section 10.1 and note D-14b.
chgrp duplicati /mnt/Backups /mnt/Backups/Ubuntu /mnt/Backups/Ubuntu/Dropbox
chmod 2750 /mnt/Backups /mnt/Backups/Ubuntu
chmod 2770 /mnt/Backups/Ubuntu/Dropbox
# The destination tree passes to the service user. This chown is the step that makes a cloud-side
# or accidental local delete FAIL: unlinking a volume needs write on its directory, and after this
# only duplicati has it.
chown -R duplicati:duplicati "${ROOT}"
find "${ROOT}" -type d -exec chmod 2750 {} +
find "${ROOT}" -type f -exec chmod 0640 {} +
setfacl -R -m g:duplicati:rX -m d:g:duplicati:rX "${ROOT}\"""",
)

edit(
    "D-14 escrow note follows read-only modes",
    """    # The find above set every regular file to 0660; the escrow env must not be group-readable
    # by the service user (design section 6, S-4).""",
    """    # The find above set every regular file to 0640; the escrow env must not be group-readable
    # by the service user at all (design section 6, S-4).""",
)

# --------------------------------------------------------------------------------------------
# D-6 -- installed copy PLUS a drift gate with an explicit --update-backup-behavior escape hatch.
# --------------------------------------------------------------------------------------------

edit(
    "D-6 drift gate",
    """bash -n "${GUARD_SRC}"

install -d -m 0755 -o root -g root /usr/local/lib/duplicati""",
    """bash -n "${GUARD_SRC}"

# --- D-6 drift gate (RULED 2026-09-22) -----------------------------------------------------
# The repository is canonical and what the unit executes is a COPY. Two different things can
# therefore drift, and they mean OPPOSITE things:
#
#   * the INSTALLED file no longer matches what was blessed -> someone edited /usr/local/lib
#     outside this installer. Never overwrite that silently; it is the only evidence.
#   * the REPOSITORY no longer matches what was blessed -> an intended behaviour change. That
#     is legitimate, and is exactly what --update-backup-behavior authorises.
#
# A symlink into the checkout was considered for this job and rejected: on a fresh host the
# checkout does not exist yet, so ExecStart= would resolve to a dangling target and the service
# would not start -- failing in the bare-metal recovery case the symlink was proposed for.
BLESSED=/usr/local/lib/duplicati/.blessed.sha256
UPDATE_BEHAVIOR=0
for arg in "$@"; do
    [[ "${arg}" == "--update-backup-behavior" ]] && UPDATE_BEHAVIOR=1
done

blessed_for() { [[ -s "${BLESSED}" ]] && awk -v d="$1" '$2 == d { print $1 }' "${BLESSED}"; }

drift=0
for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}" "${GUARD_SRC}:${GUARD_DST}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    want="$(blessed_for "${dst}")"
    [[ -n "${want}" ]] || continue          # never blessed: first install, nothing to compare
    if [[ -f "${dst}" ]] && [[ "$(sha256sum "${dst}" | cut -d' ' -f1)" != "${want}" ]]; then
        echo "DRIFT: installed ${dst} does not match its blessed checksum -- changed outside this installer" >&2
        drift=1
    fi
    if [[ "$(sha256sum "${src}" | cut -d' ' -f1)" != "${want}" ]]; then
        echo "BEHAVIOUR CHANGE: ${src} differs from the blessed checksum" >&2
        drift=1
    fi
done
if (( drift == 1 && UPDATE_BEHAVIOR == 0 )); then
    echo "Refusing to install. Inspect the differences, then re-run with --update-backup-behavior" >&2
    echo "to bless the current repository contents as what this host executes." >&2
    exit 4
fi

install -d -m 0755 -o root -g root /usr/local/lib/duplicati""",
)

edit(
    "D-6 bless after install",
    """for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}" "${GUARD_SRC}:${GUARD_DST}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    cmp -s "${src}" "${dst}" || { echo "checksum mismatch after install: ${dst}" >&2; exit 1; }
    echo "installed ${dst} ($(sha256sum "${dst}" | cut -c1-16))"
done""",
    """: > "${BLESSED}.new"
for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}" "${GUARD_SRC}:${GUARD_DST}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    cmp -s "${src}" "${dst}" || { echo "checksum mismatch after install: ${dst}" >&2; exit 1; }
    printf '%s  %s\\n' "$(sha256sum "${dst}" | cut -d' ' -f1)" "${dst}" >> "${BLESSED}.new"
    echo "installed ${dst} ($(sha256sum "${dst}" | cut -c1-16))"
done
# Bless only after every copy verified. A blessed file written earlier would record a state that
# a later failure never reached, and the next run would compare against a fiction.
install -m 0644 -o root -g root "${BLESSED}.new" "${BLESSED}"
rm -f "${BLESSED}.new"
echo "blessed ${BLESSED} (re-bless deliberately with --update-backup-behavior)\"""",
)

# --------------------------------------------------------------------------------------------
# Section 8 -- the gates are ruled, so step 0 is a verification and the preamble is stale.
# --------------------------------------------------------------------------------------------

edit(
    "P0 provisional preamble",
    """phases, not of decisions**: P0 applies the recommendations of D-1 (credstore + `--require-db-encryption-key`),
D-4 (`AmbientCapabilities`), D-6 (installed copy), D-9 (loopback) **and D-14** (the §7.3.2 unit sets
`UMask=0007`, the group-write value, while D-14 recommends the read-only `0027`) before the owner has ruled on
any of them. **D-2 is a sixth**: P0 step 11 runs a full backup under the very passphrase D-2 asks whether to
retire, and P1 step 5 re-decides it afterwards. Either rule those six first, or accept that P0 applies them
**provisionally** — a contrary ruling on D-1/D-4/D-6/D-9/D-14 means re-installing the unit, and a contrary
ruling on D-2 means the first post-recovery fileset is written under a passphrase that is then replaced. Step
0 makes that explicit.""",
    """phases, not of decisions**. That distinction mattered while the gates were open; **they were ruled on
2026-09-22 and §10.1 records them**, so P0 now applies decisions rather than recommendations: D-1
(credstore + `--require-db-encryption-key`), D-4 (`AmbientCapabilities`), D-6 (installed copy **plus the
drift gate**), D-9 (loopback) and D-14 (the §7.3.2 unit now sets `UMask=0027`, the ruled read-only value).
**D-2 no longer forces a choice at this point.** It was ruled *rotate and keep*, and §10.2 sequences the
rotation to run **after** the recovery is complete and drill-verified — so P0 step 11's full backup is
written under the current passphrase deliberately, not by default, and is re-encrypted later rather than
discarded. Step 0 verifies the artifacts match §10.1 instead of asking for a decision.""",
)

edit(
    "P0 step 0 owner gates",
    """**0. Owner gates — none of these is a session's to decide.** (a) Rule D-1, D-4, D-6, D-9 **and D-14**, decide whether
D-2 is re-decided before or after the first run, or record that P0 applies their recommendations
provisionally. (b)""",
    """**0. Owner gates — RULED 2026-09-22 (§10.1); this step is now a verification, not a decision.** (a) Confirm the
installed artifacts match the rulings: `UMask=0027` in the unit (D-14), `AmbientCapabilities=CAP_DAC_READ_SEARCH`
with the §7.3.2 confinement set (D-4), `--webservice-interface=loopback` (D-9),
`--require-db-encryption-key` (D-1), and a `.blessed.sha256` written by the installer (D-6). D-2's rotation is
**not** part of P0 — it runs after recovery, per §10.2. (b)""",
)

edit(
    "UMask pending D-14",
    "`IPAddressDeny=` and `UMask=` (the last pending D-14).",
    "`IPAddressDeny=` and `UMask=` (the last now RULED at `0027`, D-14, §10.1).",
)

# --------------------------------------------------------------------------------------------
# Section 6 -- S-3's "rotation does not re-encrypt" is true of a rotation, not of the RecoveryTool.
# --------------------------------------------------------------------------------------------

edit(
    "S-3 rotation note",
    "Delete the commented lines. **Rotation does not re-encrypt existing volumes.** **D-2 must be re-decided** (note S-3a)",
    "Delete the commented lines. **Rotation does not re-encrypt existing volumes** — but the RecoveryTool's `recompress --reencrypt` does, which is what makes D-2's ruling possible (§10.2). **D-2 RULED 2026-09-22** (§10.1)",
)

# --- Follow-up: the S-3 edit above pushed its TABLE ROW to 611 chars. markdownlint's
# --- line_length 512 applies to table rows, and this document's longest pre-existing row was
# --- 511 by design. The rule is: the CELL carries the fact, a NOTE carries the argument.

edit(
    "S-3 row back under 512",
    "Delete the commented lines. **Rotation does not re-encrypt existing volumes** \u2014 but the RecoveryTool's `recompress --reencrypt` does, which is what makes D-2's ruling possible (\u00a710.2). **D-2 RULED 2026-09-22** (\u00a710.1)",
    "Delete the commented lines. **D-2 RULED 2026-09-22** (\u00a710.1); rotation alone does not re-encrypt (note S-3b)",
)

edit(
    "note S-3b",
    'Four different ways in which "local readers only" is false.\n'
    "- **(S-4a)** `dropbox exclude add` is",
    'Four different ways in which "local readers only" is false.\n'
    '- **(S-3b)** "Rotation does not re-encrypt existing volumes" is true of a rotation and **not** of the product as a whole: '
    "`Duplicati.CommandLine.RecoveryTool.Implementation.dll` carries a `recompress` verb taking `--reencrypt` and "
    "`--new-passphrase`, which rewrites existing volumes under a new passphrase. That is what makes D-2's ruling \u2014 rotate "
    "**and keep** the existing sets \u2014 achievable rather than aspirational. \u00a710.2 sequences it and names the three "
    "hazards that ride with it.\n"
    "- **(S-4a)** `dropbox exclude add` is",
)

# --------------------------------------------------------------------------------------------
# Section 10.1 / 10.2 -- the rulings themselves, inserted ahead of the validation record.
# --------------------------------------------------------------------------------------------

RULINGS = """
### 10.1 Owner rulings — 2026-09-22

All seven open gates were ruled by the owner in one interactive session on 2026-09-22. **The Ruling
column below is binding and the Recommendation column above is historical.** D-3, D-5, D-7, D-10, D-11,
D-12 and D-13 remain open and keep their recommendations.

| ID | Ruling | Effect in this document |
| --- | --- | --- |
| D-1 | **Keep database encryption.** A random key distinct from every passphrase, at `/etc/credstore/duplicati-settings-key` root:root 0600, delivered by `LoadCredential=`, made mandatory by `--require-db-encryption-key` | §7.3.5's recommendation becomes binding; the 2026-08-30 objection is accepted as the price |
| D-2 | **Rotate the passphrase and KEEP the existing sets.** Scrub first, then re-encrypt all 877 volumes with the RecoveryTool, staged and verified before any swap | §6 note S-3 corrected; new §10.2 carries the order of operations |
| D-4 | **`CAP_DAC_READ_SEARCH`**, paired with §7.3.2's confinement set | §7.1 principle 3 becomes binding; the "duplicati uid == root-read" residual stands |
| D-6 | **Root-owned installed copy, plus a drift gate.** A blessed sha256 per installed file, checked every run; `--update-backup-behavior` is the escape hatch | §7.3.4's installer gains the gate; `/home/duplicati/bin/` is deleted |
| D-8 | **Scrub once, after P1** (`--rotate` + `--vacuum-time=1s`) | unchanged from the recommendation |
| D-9 | **Loopback only**, plus `--webservice-disable-signin-tokens` once a password exists | §7.3.6 becomes binding |
| D-14 | **Read-only destination model.** Directories `duplicati:duplicati 2750`, files `0640`, `UMask=0027`, existing volumes chowned to `duplicati` | §7.4's table and its script rewritten; the unit's `UMask=` goes `0007` → `0027` |

- **(10.1a)** **D-6's ruling is stronger than the recommendation it replaces.** The recommendation was a
  bare copy. The owner added a no-change gate with an explicit `--update-backup-behavior` switch, which
  catches two things a bare copy cannot: an installed artifact edited outside the installer, and a
  repository that has moved ahead of what is deployed. The symlink form was considered and rejected on
  one decisive fact — on a fresh host the checkout does not exist yet, so a symlink at the install path
  is **dangling and `ExecStart` fails**, defeating the bare-metal recovery case it was proposed for.
- **(10.1b)** **D-2's ruling required correcting two variable names before it could be recorded.**
  `SETTINGS_ENCRYPTION_KEY` encrypts the **server database**; the backup volumes are encrypted with the
  job's **`PASSPHRASE`**. `SETTINGS_ENCRYPTION_KEY_OLD` and `PASSPHRASE_OLD` **do not exist in 2.4.0.0** —
  scanned across 1,443 files in UTF-8 and UTF-16LE, zero hits each
  (`util/ad-hoc/2026-09-22_duplicati_literal_scan.py`). Writing the new passphrase into
  `SETTINGS_ENCRYPTION_KEY` would have re-keyed the database and left all 877 volumes under the leaked
  passphrase. §4.1 records that on this host the active `SETTINGS_ENCRYPTION_KEY` **already equals
  `PASSPHRASE`** — the same conflation, already made once, and part of what broke.
- **(10.1c)** **The new passphrase does not go in `.env`.** That file is `0660 duplicati:duplicati` and the
  wrapper echoed every one of its lines into the journal and syslog — 60 echoes on 09-20, which is S-3,
  the exposure being remediated. It goes to `/etc/credstore` under `LoadCredential=`: the same custody
  model as D-1's settings key, and a **distinct value** from it.
- **(10.1d)** **D-14b.** The Dropbox root keeps `2770` while everything beneath `Backups/` moves to
  `duplicati:duplicati 2750`. The sync daemon runs as `pcalnon` and must write its own root; narrowing
  that would break synchronisation rather than harden anything. The protection comes from the
  destination tree below it, where only `duplicati` holds write on the directories — which is what an
  unlink requires.

### 10.2 D-2 execution: scrub, rotate, re-encrypt — order of operations

The owner set two criteria: **access to backup data is never lost**, and **the new passphrase does not
leak**. The sequence below is ordered by those and not by convenience. **None of it is a session's to
execute** — it is owner-gated exactly as §8 is, and it runs *after* the recovery, not during it.

**The mechanism exists in the product.** `Duplicati.CommandLine.RecoveryTool.Implementation.dll` carries a
`recompress` verb (strings read from the assembly rather than by running it —
`util/ad-hoc/2026-09-22_recoverytool_verbs.py`):

```text
recompress <targetcompression> <remoteurl> <localfolder> --reupload --reencrypt [options]
3) If --reencrypt is supplied, again reencrypts using same passphrase. If the
   --new-passphrase option is present, encryption happens using the new passphrase
4) If --reupload is supplied, files with old compression are deleted and recompressed
   files are uploaded back to remote storage
Warning: Before recompress delete local database and after recompress recreate local
database before executing any operation on backup.
```

So an existing fileset **can** cross a passphrase rotation, which is what makes "rotate without losing
the backups" a real option rather than a wish. Three hazards ride with it, and each touches one of the
owner's two criteria:

1. **`--reupload` deletes the originals at the destination.** The sole local copy sits on `sda`, a disk
   that has never had a SMART test (§12, carried). This is why the ruling is **stage → verify → swap**
   and not in-place, and why nothing here contradicts §8's rule that nothing under
   `/mnt/Backups/Ubuntu/` is deleted or moved.
2. **The local database must be deleted before and recreated after.** A Recreate across 877 volumes is
   long, and §5.3 records that an *aborted* per-job Recreate is precisely what produced the database
   this whole arc began by misreading.
3. **`--new-passphrase=` on argv is world-readable** through `/proc/*/cmdline` — the same defect class
   §7.3.6 already forbids for `duplicati-server-util change-password`. The new passphrase must reach the
   tool by a channel that is not argv, or the rotation leaks the secret it exists to protect.

| # | Step | Gate before proceeding |
| --- | --- | --- |
| 1 | SMART test `sda`; restore-drill the CURRENT set | a drill passes on the current passphrase |
| 2 | Scrub the leaked copies: the S-7 file, the `.env` comment block, and D-8's journal scrub after P1 | S-3, S-6 and S-7 counts all read zero |
| 3 | Mint the new passphrase; place it at `/etc/credstore/duplicati-passphrase` root:root 0600 | never in `.env`, never on argv, never echoed |
| 4 | Copy the 877 volumes to staging (≈203 GiB free required) | per-file hashes match the source |
| 5 | `recompress … --reencrypt --new-passphrase` against the **staging** copy only | exit 0, and every volume re-encrypted |
| 6 | Recreate the local database against staging; restore-drill from staging | a drill passes on the NEW passphrase |
| 7 | Swap staging in as the live destination | the old set is retained untouched until step 6 passed |
| 8 | Delete-forever the old ciphertext server-side (Dropbox retains deleted files 30 d on Basic/Plus/Family, 180 d on Professional) | only after step 7 is verified |

**Step 1 is first and is not optional.** Steps 4–7 are a bulk rewrite of the only local copy of
202.8 GiB, guarded by a disk whose health has never once been read. A rotation that loses the data it
was protecting has failed at the thing it was for.

---
"""

edit(
    "insert rulings before section 11",
    """  "read/write/execute as appropriate", which is exactly why it is the owner's call and not this design's.

---

## 11. Validation record (CON §7)""",
    """  "read/write/execute as appropriate", which is why it was the owner's call and not this design's.
  **Ruled 2026-09-22: the read-only form** (§10.1).

---
"""
    + RULINGS
    + """
## 11. Validation record (CON §7)""",
)


def main() -> int:
    if not DESIGN.is_file():
        print(f"FATAL: {DESIGN} not found (run from the repository root)", file=sys.stderr)
        return 2

    text = DESIGN.read_text(encoding="utf-8")
    original = text
    failures: list[str] = []
    applied = skipped = 0

    for tag, old, new, count in EDITS:
        have = text.count(old)
        if have == count:
            text = text.replace(old, new, count)
            applied += 1
            print(f"  OK       {tag}")
        elif text.count(new) >= 1 and have == 0:
            skipped += 1
            print(f"  ALREADY  {tag}")
        else:
            failures.append(f"{tag}: anchor found {have}x, expected {count}x")
            print(f"  FAIL     {tag}: found {have}x, expected {count}x", file=sys.stderr)

    if failures:
        print(f"\n{len(failures)} anchor(s) failed; NOTHING written.", file=sys.stderr)
        return 1

    if text == original:
        print(f"\nno change ({skipped} edit(s) already applied) -- idempotent")
        return 0

    # Over-width check runs BEFORE the write. .markdownlint.yaml sets line_length 512 and
    # markdownlint checks TABLE ROWS too; this document's longest pre-existing row was 511,
    # deliberately. The first run of this script wrote the file and *then* reported a 611-char
    # row -- a check after the write is a report, not a gate.
    over = [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > 512]
    for n, width in over:
        print(f"  OVER-WIDTH line {n}: {width} chars", file=sys.stderr)
    if over:
        print(f"  {len(over)} line(s) exceed 512 -- NOTHING written", file=sys.stderr)
        return 3

    DESIGN.write_text(text, encoding="utf-8")
    print(f"\napplied {applied}, already-present {skipped}; {DESIGN} now {len(text.splitlines())} lines")

    subprocess.run(["git", "diff", "--stat", "--", str(DESIGN)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
