# Record the sda SMART result, close the carried item, and fix §10.2's staging target

## Summary

§10.2 step 1 of `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
gates the D-2 passphrase rotation on a SMART test of `sda` — the disk holding the sole local copy of
the 202.8 GiB backup set, which until now had never had one. **The test ran on 2026-09-23 and
passed.** This records the result and its evidence, closes the §12 / D-12a carried item, and
corrects two things the result itself exposed.

## The result

`sda` is `WDC WD40EZAZ-00SF3B0` (4 TB). Overall health **PASSED**, and an **Extended offline**
self-test completed without error at lifetime **28,938 h** against **28,941 h** at capture — so the
scan is current and covered the surface.

That last point needed the self-test **log**, not the header: `Self-test execution status: (0)` also
means *"no self-test has ever been run"*, so the status line alone cannot distinguish a clean result
from no result at all.

Every defect-indicating attribute is zero — `Reallocated_Sector_Ct`, `Current_Pending_Sector`,
`Offline_Uncorrectable`, `Reallocated_Event_Count`, `UDMA_CRC_Error_Count` — and the ATA error log,
the Pending Defects log and all SATA Phy event counters are empty. 39 °C, under/over-limit count
0/0.

Age is the only soft spot, and it reads better than the hours suggest: **28,941 power-on hours**
(~3.3 years) but only **1,803 Head Flying Hours** and ~10.4 TB written in life — a mostly-idle disk,
not a worked one.

## Two corrections the result forced

**1. A healthy disk does not make an in-place rewrite safe.** The health report also identifies `sda`
as a **drive-managed SMR** drive ("Western Digital Blue (SMR)"). `recompress --reupload` against the
live destination is therefore a full band-rewrite of the only copy — slow enough that it must not be
mistaken for a hung operation. Hazard 1 in §10.2 said only that the disk's health was unknown; it now
says both things, and the SMR fact independently supports the stage-verify-swap ruling.

**2. §10.2 step 4 did not name a staging target, and the obvious one is wrong.** `sda1` has 3.1 TiB
free and looks like the natural choice — which is the trap, because it holds the sole local copy.
Staging there puts the original and the re-encrypted copy in **one failure domain** for the whole of
steps 4–7. A clean SMART report lowers the probability, not the consequence, and the owner's criterion
is that access is *never* lost.

Step 4 now names **`nvme0n1p5` (`/`)**: 376 GiB free against ~203 GiB needed, a different physical
device, **ext4** so ownership and modes survive for D-14's read-only model, and **outside the
`/home/pcalnon` backup source**. `sdc3` (`/home`, 1.2 TiB free) passes the failure-domain test but
fails the last one — staging there would sweep 203 GiB of ciphertext into the next fileset unless an
exclusion were added first, the same class of mistake as S-7.

## Step 1 is half done

§10.2 step 1 is *"SMART test `sda`; restore-drill the CURRENT set"*, gated on a drill passing under
the current passphrase. The SMART half is done. **The restore drill has not run**, so step 2 is not
yet unblocked, and the step table and its closing paragraph now say so explicitly rather than
implying the step is complete.

## Evidence is committed, not merely cited

The design now cites `reports/smart/smart-xall_results-sda_2026-09-23_07:53:18.out` and
`util/ad-hoc/smart_checks_backup-sda.bash`. **Neither was tracked**, so the citations would have
pointed at files existing only on one host. Both are added here, along with the eight other readings
from the same session (92 KB total) — `reports/` is this repo's per-run evidence directory, and the
intermediate readings establish when each test was started.

Screened for credential-shaped content before adding: none. The outputs carry the drive model and
serial, which is ordinary SMART content.

`util/ad-hoc/smart_checks_backup-sda.bash` needed one annotation to be committable: the repo's
shellcheck hook runs at `--severity=warning` over `\.(sh|bash)$`, and the script's `DEVICE_*` block —
a deliberate palette naming every disk so `CURRENT_DEVICE` can be repointed by editing one line —
raises **13 × SC2034**. A file-level `# shellcheck disable=SC2034` with the reason is added and
nothing else is changed; SC2034 is the **only** code shellcheck reports on the file, so no genuine
finding is suppressed.

## Changes

**Changed**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
(hazard 1 rewritten; §10.2 step 1 and step 4 rows; the closing paragraph; new notes 10.2a and 10.2b;
the §12 and D-12a carried-item lines now record the item as closed).

**Added**: `util/ad-hoc/2026-09-23_record_smart_result.py` (the anchor-asserted edit script),
`util/ad-hoc/smart_checks_backup-sda.bash`, and nine `reports/smart/*.out` readings.

## Verification

- `markdownlint 0.42.0` (the pinned hook version) — exit 0.
- Snippet linter: **14 blocks, 0 failures**.
- `util/ad-hoc/2026-09-22_stage_design_artifacts.py --check`: **0 staged, 13 already current** — these
  edits touch prose and notes only, no tagged block, so no artifact changes.
- `util/markdown_structure_delta.py --base origin/main`: **0 regressions**.
- Edit script is idempotent: a second run reports every edit `ALREADY` and writes nothing. It carries
  both guards from the 2026-09-22 run — `edit()` refuses an edit whose `old` is a substring of its
  `new`, and the over-width scan runs before the write.
- `shellcheck --severity=warning` on the added script: exit 0; `bash -n`: OK.

## Requirements

References JR-DEP-SEC-005.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_016TcEz8juUrgh8PWf2LqZGX
