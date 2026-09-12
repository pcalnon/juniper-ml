# V3 design — reconciler ledger, Lane A1 (git mechanics + population census)

Entry point: hermetic throwaway repos (git 2.53.0) + independent filesystem census.
Target: `notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`.

## Q1 — ANSWERED. The design's G3 mechanism is the wrong shape

Instrument: full `find -printf '%s\t%p'` over all 118 `.claude/worktrees/` trees, minus the
tracked manifest — a route sharing no code with `git status --ignored`. It independently
reproduces the design's total: **1,274,523,657 B = 1.2745 GB** (design said 1.27 GB).

| class | bytes | % | files | trees |
|---|---:|---:|---:|---:|
| REGENERABLE (caches, venv, `__pycache__`, node_modules, dist/build) | 919,369,039 | **72.1%** | 20,957 | 104 |
| NON-REGENERABLE | 355,154,618 | **27.9%** | 943 | 118 |

**But the non-regenerable residue is 96.1% Playwright browser console dumps** (341 MB in three
trees). Strip those and the genuinely irreplaceable evidence is **13.8 MB — 1.08% of the
payload, 837 files** (≈9.9–13.8 MB after A1's own stated single-branch-manifest bias).

**This refutes G3 as drafted.** The design proposes "a configurable byte/count threshold for
evidence." The value distribution is inverted against size:

- The highest-value item in the entire population is `curious-plotting-hummingbird/.env` at
  **114 bytes**. *Any* non-trivial byte threshold passes it.
- The 341 MB that trips every byte threshold is browser noise.
- A threshold tuned to catch the 1.8 MB of soak evidence fires on ~60 trees of Playwright chaff
  and gets disabled within a week — the exact failure mode §6 documents for the ancestry gate.

**Required: G3 gates on CLASS, not SIZE** — refuse at 0 bytes on class membership (`logs/`,
`reports/soak/runs/`, `*.env`), and treat `.playwright-mcp/` as a **fourth class** ("bulky
low-value") with its own disposition. Lumping it into "evidence" is what makes G3 unbearable.

## Q2 — ANSWERED hermetically. §4's architecture is sound; one asymmetry to record

| `git worktree move` | result |
|---|---|
| locked tree | **REFUSES** (single `--force` also refuses; `-f -f` overrides) — **G1 is NOT bypassed by the archive step** |
| dirty tree | **does NOT refuse** — moves silently. Differs from `remove`. Harmless for archival, but must be recorded |
| registration | **preserved** (internal admin dir retained, only `gitdir` rewritten) |
| gc protection | **preserved** — an orphan detached-HEAD commit in a *moved* tree **survived `git gc --prune=now`** in the same run that **destroyed** the orphan from a *removed* tree |

That last row is the strongest single test in the round: one command, two outcomes, split by the
variable under test. §4's claim that `move` beats `tar` is confirmed by construction.

## Confirmed

- **§1 semantics table — all five rows**, independently: branch survives, stash survives
  (`refs/stash` is repo-global), **ignored files DELETED with no `--force` and no warning**
  (plain `remove`, exit 0, `status --porcelain` printed nothing), detached HEAD orphaned then
  destroyed by `gc --prune=now`, admin dir deleted including `logs/HEAD`.
- **Lock defeats both `remove` and `remove --force`**; only `-f -f` overrides.
- **`ed14f3a6` fires live, today.** 1 of 8 detached HEADs, **not locked**, carrying one commit no
  ref holds: *"docs(handoff): archive the P5 four-ports + helper-fold handoff (session 1489a9)"*,
  Paul Calnon, 2026-08-26. The naive `--not --all` form reports **zero** at risk.
- **`--not --all` is structurally non-discriminating** — it flipped 0→1 the instant the worktree
  was removed, proving `--all` was counting the worktree HEAD. A1 discounted it entirely.
- **lock↔liveness set-wise**, not merely count-wise: `comm` both differences empty, intersection 11.
- **129 of 534** branches without upstream — now agreed by **three** independent instruments (A1, A2, B2).
- §7.1 disk/timing/packed-refs figures; the one-filesystem claim (`/dev/sdc3`).

## Refuted / overstated — design edits required

| claim | truth |
|---|---|
| "1.27 GB across **89 trees**" | bytes right, **118 trees**. §9 step 2's scope is misstated. |
| "**330 MB** of `*.log` across **19 trees**" | `*.log` outside caches = 465.5 MB / 1,257 files / **84 trees**, of which **~119 MB is TRACKED** (`reports/e2e/_recovered/…_system.log` — the recovered canopy logs). Untracked `.log` = 341 MB, essentially all `.playwright-mcp`. "330 MB" was right by luck; "19 trees" is wrong 4×. |
| "**23.4 GB** worktree disk" | `Juniper/worktrees/` holds **150** dirs across sibling repos; only **21** are juniper-ml (3.28 GB). juniper-ml's footprint is **20.8 GB**. The figure annexes other repos. |
| §3 G4 **code block** `git branch -a --contains` | **Misses tag-anchored commits.** After tagging the orphan, `branch -a --contains` still returned empty (would falsely refuse) while `rev-list --not --branches --remotes --tags` correctly returned empty. The prose recommends rev-list; the printed block uses the weaker command. Fails safe, but violates §8.1's own negative-control rule. |
| §7.2 "12 juniper-ml worktrees held live" | **11** (164 `/proc/*/cwd` entries → 11 distinct trees). |
| "740 ref-unreachable, 739 object-present" | **754 of 1,669**, and **all 1,669 object-present**. Same order; the implied one missing object is unreproducible. |

## The reconciliation that matters: A1 and B2 disagree on backup, and BOTH are right

A1 **CONFIRMED** the zero-backup claim and called it *understated* — `EXCLUDE_DIRS` at
`util/juniper-backup.bash:111` excludes `.claude` **and** `.playwright-mcp`, `logs`, `reports`,
`.serena`, so *"every single category in my 355 MB non-regenerable table is excluded by name."*

B2 **REFUTED** it from the Duplicati server DB, which I re-derived: Source `/home/pcalnon/`,
44 filters all exclusions, none matching the worktree payload, daily filesets through
`20260911T140000Z`, 3-year retention, no size skip.

**Both measurements are correct. The inference drawn from A1's was not.** A1 and I used the
same instrument — the tar archive — and concluded about *backup coverage*. That is one system,
not the system. Agreement between two readings of the same instrument is not corroboration;
it is the same blind spot twice. This is the eighth member of the §8.1 family and it is the
one that produced the design's central error.

**Resolution: the tar archive genuinely excludes everything at risk, AND Duplicati genuinely
covers it.** The residual exposure is a **≤24 h RPO**, not irreversibility.
