# V3 design — reconciler ledger, round 2

Round 1 rejected revision 1. Round 2 ran two reviewers against revision 2: Lane A verifying the
respecified gate commands hermetically, Lane B briefed to refute — with over-correction named as the
primary hunting ground. **Both found real defects. Every blocking finding below was re-derived by
the reconciler rather than accepted.**

Target: `notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`.

## Lane A — six defects in the respecified commands, all re-derived and fixed

| # | defect | reconciler re-derivation | fix |
|---|---|---|---|
| A1 | `grep '^[SsHh]'` in G2 | `H` is `ls-files`' tag for **cached**. On this worktree `grep -c '^[SsHh]'` = **2661 of 2661** tracked files; `'^[Ssh]'` = **0**. Gate refuses 100% of trees | class → `[Ssh]` |
| A2 | G4's `$MAIN/.git/worktrees/$name/…` string-building | git **deduplicates admin-dir names** (`g4wt_orphan` → `g4wt_orphan1`), and `test ! -e` is **vacuously true** when the base path is absent, so the gate never fires if `$MAIN` is itself a linked worktree | `git -C "$WT" rev-parse --git-path <p>` |
| A3 | `\|\| continue` after `rev-parse --verify --quiet` | rc=1 means *both* "absent" (benign) and "present but unreadable" (instrument failure). Violates principle 4 — the `_is_dirty` polarity defect, in new code | separate the cases; add aggregate exit status |
| A4 | §3.3's stated **reason** | the exit-128 crash belongs to `matching`. `traditional` without `-uall` under `showUntrackedFiles=no` returns **rc=0 with EMPTY output** — a silent fail-open principle 4 does **not** catch. `-uall` is the load-bearing flag, not the `-c` pin | reason corrected |
| A5 | `update-ref` salvage remedy | **overwrites by default**, so "check the exit status" was vacuous. Verified: same day/name/ref, different SHA → **rc=0, anchor silently replaced**. Revision 1's `git branch` failed *closed* here; the fix failed *open* | empty-string old-value precondition (create-only) |
| A6 | §3.5 submodule claim | git's refusal falls to a **single `--force`** (the lock needs `-f -f`), and registered-but-empty / registered-non-repo are **not refused at all** | softened; G5 is the instrument |

**Corrections verified in both directions** by
`util/ad-hoc/2026-09-12_worktree_v3_consensus/verify_respecified_gates.bash`:
create-only write rc=0 then rc=128 with the anchor preserved, against an unguarded control that
clobbered at rc=0; `[SsHh]` matching 2 of 2 against `[Ssh]` matching 1; `--git-path` resolving
per-worktree; absent-vs-unreadable separating cleanly.

**Lane A also confirmed, decisively:** `refs/salvage/` genuinely protects an object from
`gc --prune=now` (control orphan destroyed in the same run); the move-vs-remove gc split; all four
G4 reachability cases; G5's depth arithmetic; B1's `@{upstream}` exit 128; B3's three-dot form; the
symlink non-dereference.

## Lane B — four blocking findings, all re-derived

### B-R1 — the pivot was over-corrected. CONFIRMED

Revision 2's first draft said *"≤24 h RPO with ~3-year retention"*. Measured at the destination:

- **9 filesets exist**, oldest `duplicati-20260825T102739Z`. The set was **recreated 2026-08-25**;
  **max restore depth today is 18 days**, and the 3-year tier has never been exercised.
- **08-26→08-31 and 09-02→09-04 are already thinned away.**
- Retention deletes **filesets**, not files, so a file whose whole lifetime falls between two
  survivors is in **none** of them. For worktree-resident evidence — short-lived by construction —
  real depth is **~7 days**.
- **The page cited for §0.2 says so, in a paragraph the draft omitted**: finding 4 of
  `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` — *"never staged and is
  unrecoverable — no branch, commit, stash, worktree, **backup**, dangling object…"*. Selective
  citation, in the section arguing against selective instruments.
- **The §0.1 re-derivation was not independent**: the probe reads
  `~/.local/state/duplicati-server-db/…sqlite`, a **root-written snapshot** (`pcalnon`-owned, mtime
  2026-09-11 08:45), one run stale, with a **0-row `Log` table**. §8.1 member 8 applied to §0.1
  itself — two readings of one artifact.

### B-R2 — B1 as drafted refuses 86.7% of branches. CONFIRMED exactly

| upstream state | all | `worktree-*` |
|---|---:|---:|
| none | 129 | 119 |
| **`[gone]`** | **334** | 9 |
| live | 71 | 7 |
| total | **534** | **135** |

UNKNOWN⇒refuse over unresolvable refs refuses **463 of 534**, and passes at most **7 of 135** in the
governed population. Worse, `[gone]` is *created by* merge-and-auto-delete — the success condition —
so B1 is **anti-correlated with its target population**. Fix: *remote absent AND ancestor of
`origin/main`* ⇒ **PASS**.

### B-R3 — the one file that cannot wait. CONFIRMED, and graver than reported

`curious-plotting-hummingbird/.env` is **unlocked**, `in_main` **true**, and therefore in the
vehicle's passing set behind nothing but the fail-open `_is_dirty`. Per the Duplicati certification:
it holds `PASSPHRASE` and `PASSPHRASE_OLD` in cleartext; **filter 43 excludes the key's own
directory**, so the key is not in the backup it unlocks; **`PASSPHRASE_OLD` has no surviving
out-of-band copy at all** — *"recoverable only through `PASSPHRASE`, by restoring the stray `.env`
from the backup"*; and its **Tier 3 "BLOCKED, do not sweep"** list names it. Hoisted to rollout
step 1.

### B-R5 — §0.3 over-corrected the other way. CONFIRMED against me

`_remove_worktree` is reached only after (not self-cwd) AND (not locked) AND (not detached) AND
(not dirty) AND (`in_main` OR `merged_pr`). *"No gate at all"* quoted three lines out of their
caller. The accurate charge is narrower and includes a defect the draft missed: **`_has_merged_pr`
is true if *any* PR ever merged**, so commits pushed after a merged PR die. The vehicle also already
**keeps** detached-HEAD trees, so `ed14f3a6` would not be swept by it.

### B-R6 — "118/118 hold `logs/`" was a placeholder artifact, and it was mine. CONFIRMED

Every tree carries a tracked 0-byte `logs/.gitkeep`. Re-measured excluding it: **7 of 118**, with
4.96 MB of 5.2 MB in three trees and `reports/soak/runs/` in **one**. The real evidence population
is **~4 trees plus the one `.env`**. I ran that `ls -A`-style count myself while "verifying" another
reviewer — §8.1 member 13.

## Also folded in

B-R7 age denominators (three instruments disagreeing by 20 trees; "57 within 7 d" is over **139**,
not 118; the veto, not G1, is binding); B-R8 `reports/` mechanism (`git status` reports nothing for
clean tracked files, and "untracked under `reports/`" can never fire at G3 because G2 catches it
first) plus the **git-lfs smudge caveat** for any byte-based re-derivation; B-R9 149 worktree dirs,
not 150 (one entry is `logs`); B-R10 G5's missing exit-status requirement; B-R11 the working papers
**are** markdownlint-scoped (only `PR_BODY*`/`PROBE*` basenames are exempt) and the ad-hoc headers
needed `Status:`/`Retire when:`/`Related:`.

## Attacks that failed — the design's real support after two rounds

G5 refuses **0 of 118** and runs in 17 ms; the Playwright 341 MB figure; 192 ancestors with exactly
1 at tip; 129 no-upstream; the §0.2 recovery (7 files, 2,268,186 B); `ed14f3a6`; the whole census
(140/118/8/11, 17.5 GB, 0.65%); every `.gitignore` line citation; ml#1922 merged as `5b521f7d`. Two
attacks **inverted**: "the Duplicati destination is degraded" (it is healthy — 12% used, 3.1 T free;
the defect is depth, not health) and "A1's payload figure is 5× low" (that was git-lfs smudge
expansion in the attacker's own instrument).
