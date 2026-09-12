# Worktree Cleanup Protocol V3 — design (revision 2)

**Date**: 2026-09-12
**Repo**: juniper-ml. **Scope is juniper-ml only** — see §1.3; revision 1's ecosystem claim was false.
**Author**: Paul Calnon
**Status**: DESIGN, revision 2. **Revision 1 was REJECTED by independent consensus** (4 reviewers,
2026-09-12). This revision records that rejection, corrects what it broke, and reaches a materially
different recommendation. Revision 1 is preserved verbatim at
`util/ad-hoc/2026-09-12_worktree_v3_consensus/REVISION1_REJECTED_BY_CONSENSUS.md`.
**Supersedes (on ratification)**: the removal half of
[`JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`](JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md) § Phase 4.

---

## 0. What consensus did to revision 1

Four reviewers, independent entry points: git's mechanics tested hermetically plus a fresh
population census (A1); the repo's tooling re-derived from source (A2); an adversarial attack on the
gates (B1); an adversarial attack on the policy (B2). **Two of revision 1's three load-bearing
premises were false, and three of its four gates failed a negative control.**

### 0.1 The central error

Revision 1 claimed `.claude/worktrees/` had **zero backup coverage** and built its urgency on it —
*"the row that converts risky into irreversible."*

**It is backed up.** The live Duplicati job **Yamaguchi** takes Source `/home/pcalnon/` with
**44 filters, every one an exclusion, none matching** `.claude`, `worktrees`, `.playwright-mcp`,
`reports` or `.env`. Daily filesets through `duplicati-20260911T140000Z`; 859 volumes, 202 GB;
`retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M`; **no `--skip-files-larger-than`**, so even the 201 MB
console log is in every fileset. Re-derived by the reconciler with
`util/ad-hoc/2026-09-12_worktree_v3_consensus/duplicati_worktree_coverage_probe.py`.

**How the error happened, because that is the reusable lesson.** I measured the **tar** archive
(`util/juniper-backup.bash:111` does exclude `.claude`) and reported a conclusion about **backup
coverage**. One system is not the system. Lane A1 then *confirmed* the claim — using the same tar
instrument — and called it understated. **Two agreeing readings of one instrument are not
corroboration; they are the same blind spot twice.** Only B2, which went to a different system,
could refute it.

### 0.1.1 …and round 2 caught THIS section over-correcting, the same way

Revision 2's first draft concluded *"bounded at a ≤24 h RPO with ~3-year retention"*. **That is
complacent, and it repeats the original sin at a different address.** Three measured corrections:

**(a) There are NINE filesets, and the oldest is 2026-08-25.** Listed directly from the destination:

```
duplicati-20260825T102739Z   20260901   20260905   20260906
20260907   20260908   20260909   20260910   20260911
```

The set was **recreated 2026-08-25** ("with the GPGFlushError investigation settings") and the prior
archive purged. **Maximum restore depth available today is 18 days**, not three years; the 3-year
tier has never been exercised. And the gaps are already visible — **08-26→08-31 and 09-02→09-04 have
been thinned away.**

**(b) Retention deletes FILESETS, not files.** A file is restorable only from a surviving fileset
that covers its lifetime. For a continuously-resident file, "~3 years" is defensible. **For
worktree-resident evidence — short-lived by construction — the effective depth is the daily-
granularity window, ~7 days, then a lottery.** A file created 08-27 and destroyed 08-29 exists in
**no** surviving fileset.

**(c) The document I cite for §0.2 says so, in a paragraph I omitted.**
`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` finding 4, on the same page as the
recovery §0.2 quotes:

> **The suppression's source was never staged and is unrecoverable** — no branch, commit, stash,
> worktree, **backup**, dangling object, or loose object in the window.

**I quoted the half of that page that supported the correction and omitted the half that
qualifies it.** Selective citation, in the section arguing against selective instruments.

**(d) The §0.1 re-derivation was not independent.** My probe read
`~/.local/state/duplicati-server-db/Duplicati-server.sqlite` — a **root-written snapshot**
(`pcalnon`-owned, mtime 2026-09-11 08:45), not the live server DB (`/usr/lib/duplicati/data/`,
`drwx------ root root`). It is at least one run stale, which is the real explanation for the
`LastRun` discrepancy I first waved away as field lag — and its `Log` table has **0 rows**, so it
contains **no run history and no restore-test record**. §8.1 member 8 applies to §0.1 itself: I
re-derived a finding from the same artifact the reviewer read. Two readings of one sqlite file.

**Consequence — the measured statement, replacing both the over-alarm and the complacency:**

> **RPO ≤24 h. Restore depth: up to ~3 years for a continuously-resident file; ~7 days for one whose
> lifetime fits inside the daily window; and 18 days maximum available today, because the set was
> recreated 2026-08-25. Nine filesets exist. No restore drill has been run against a
> worktree-resident path.**

That is materially weaker than "covered", and materially stronger than "zero". §2 principle 2, §5
and §9's "not doing" are argued against *that* number, not the adjective.

### 0.2 The second false premise

Revision 1 §1.2 cited the 2026-08-29 canopy incident as a data loss — *"the only surviving copy"* of
evidence qualifying a published finding.

**All seven logs were recovered.** `juniper-ml/reports/e2e/_recovered/20260827-28_arc_worktree_leg_logs/`
holds exactly **7 `*_system.log` files, 2.2 MB**, written 2026-08-30. It was a **near-miss, recovered
in full**. The methodological lesson survives — three measurement agents, two adversarial agents and
a reconciler all hunted for those files and missed them — but a design may not cite a recovered
near-miss as proof of irreversibility.

### 0.3 The reversal that matters for the owner's proposal

Revision 1 said the owner's checks 4/5/7 were *"aimed at the wrong operation"*, because branches
survive `git worktree remove`. True of bare git; **false of the operation this protocol governs.**

`scripts/cleanup_session_worktrees.py` — which revision 1 nominated as V3's primary vehicle —
performs removal as **one composite operation**:

```python
r  = _run(["git", "-C", str(repo), "worktree", "remove", str(wt)])        # gated
rb = _run(["git", "-C", str(repo), "branch", "-D", branch])               # UNGATED, forced
rp = _run(["git", "-C", str(repo), "push", "origin", "--delete", branch]) # UNGATED
```

Its own comment reasons carefully against `--force` on the worktree — *"normalising it here is the
step before someone reaches for `-f -f`"* — then force-deletes the local branch **and the remote
ref** two lines later. Found independently by A2 and B2.

**Round-2 correction — the first draft of this section over-claimed, and the fix matters.** It said
the branch deletion had *"no gate at all"*. That quotes three lines out of their caller.
`_remove_worktree` is reached only after **(not self-cwd) AND (not locked) AND (not detached HEAD)
AND (not dirty) AND (`in_main` OR `merged_pr`)** — verified by reading the caller loop. The branch
deletion inherits all of those. *(Note the vehicle also already KEEPS detached-HEAD trees, so G4's
live victim `ed14f3a6` would not be swept by this tool — G4 still matters for the other tooling and
for the 21 never-locked `Juniper/worktrees/` trees.)*

**The real defects are narrower, and two of them are worse than the one I over-claimed:**

1. **`-D` where `-d` would suffice** given that gate — a removed belt, not an absent one.
2. **`_has_merged_pr` returns True if *any* PR for the branch ever merged.** So a branch with
   commits pushed *after* a merged PR has `in_main` false, `merged_pr` true, `dirty` false →
   `worktree remove` + `branch -D` + `push origin --delete`, **and those commits die.** That is
   exactly the case B1 (§6.1) exists for, and it is reachable today.
3. **`push origin --delete` destroys an armed auto-merge** and closes the PR (§6.4) — the strongest
   of the three, and invisible to every other check.

So the owner's checks are still correctly aimed; the accurate charge is *"gated by a merge test that
cannot see post-merge commits, then forced"*, not *"ungated"*.

**The owner's instinct was better than revision 1 credited.** Checks 4/5/7 were aimed at the
composite operation the tooling performs. §6 reinstates them as gates on that operation, and
**reinstates check 6 as well** (§6.4) — revision 1's argument for dropping it was self-refuting.

### 0.4 Scorecard

| revision 1 claim | consensus |
|---|---|
| §1 diagnosis: V2 gates a branch predicate, `remove` is a filesystem operation | **HELD** — B1: *"the best worktree-safety diagnosis I have read in this codebase"* |
| §1 semantics table (branch survives / stash survives / ignored DELETED / detached orphaned / admin dir deleted) | **HELD**, all five, hermetically, twice |
| G1 (not locked) | **HELD**, and stronger than claimed — git refuses at no-force *and* single `--force` |
| `ed14f3a6` unreachable detached HEAD | **HELD exactly** |
| §8.2 tooling inventory | **HELD** — every claim B1 spot-checked was accurate |
| archive-by-`move` *mechanics* | **HELD** — gc protection confirmed by a decisive split test |
| **"zero backup coverage → irreversible"** | **REFUTED** (§0.1) |
| **"the only surviving copy died"** | **REFUTED** (§0.2) |
| **"checks 4/5/7 target the wrong operation"** | **REFUTED** (§0.3) |
| **G2's specified command** | **REFUTED** — two independent bypasses |
| **G3's specified command and threshold shape** | **REFUTED** — three ways, one of which fails open by crashing |
| **G4's specified command** | **REFUTED** — inverts under `-C`, misses tags |
| **archive location** | **REFUTED** — both proposed roots unbacked by tar |
| population figures "89 trees", "330 MB/19 trees", "23.4 GB", "12 live" | **REFUTED** — 118, 341 MB/84, 20.8 GB, 11 |

---

## 1. Why V3 — corrected

### 1.1 The diagnosis that survived

> **Every gate in V2 and in the original seven-check list is a BRANCH-AND-PR predicate.
> `git worktree remove` is a FILESYSTEM-AND-ADMIN-DIRECTORY operation.**

Verified hermetically twice (git 2.53.0, throwaway repos):

| operation | branch | stash | ignored files | detached HEAD | `.git/worktrees/<n>/` |
|---|---|---|---|---|---|
| `git worktree remove` | **survives** | **survives** | **DELETED, no `--force`, no warning** | **orphaned, then gc-destroyed** | **DELETED** incl. `logs/HEAD` |

`git status --porcelain` printed **nothing** for a tree holding two ignored files; `remove` returned
**0** and deleted them. The orphan was destroyed by a subsequent `gc --prune=now`. `refs/stash` is
repo-global, so stashes survive.

### 1.2 What that actually costs — measured, not asserted

Lane A1 classified the whole ignored payload by filesystem enumeration minus the tracked manifest —
a route sharing no code with `git status --ignored`. It independently reproduced the total:

| class | bytes | % | files |
|---|---:|---:|---:|
| **REGENERABLE** (caches, `venv`, `__pycache__`, `node_modules`, dist/build) | 919,369,039 | **72.1%** | 20,957 |
| **NON-REGENERABLE** | 355,154,618 | **27.9%** | 943 |
| total ignored payload | **1,274,523,657 (1.2745 GB)** | | 21,900 |

**But 96.1% of the non-regenerable bytes are Playwright browser console dumps** — 341 MB in three
trees (`dreamy-swinging-sunrise` 201 MB, `wondrous-spinning-piglet` 128 MB, `happy-yawning-boot`
10 MB). Strip those and the **genuinely irreplaceable evidence is ≈9.9–13.8 MB — about 1% of the
payload**, in ~837 files: `reports/soak/runs/` (60 files, 1.79 MB), `logs/` (5.2 MB), untracked
`reports/` evidence (2.9 MB), and one 114-byte unencrypted `.env`.

**This refutes the threshold shape revision 1 proposed.** Value runs *backwards* to size:

- The highest-value item in the population is `curious-plotting-hummingbird/.env` at **114 bytes**.
  Any non-trivial byte threshold passes it.
- The 341 MB that trips every byte threshold is browser noise.
- A threshold tuned to catch the 1.79 MB of soak evidence fires on ~60 trees of chaff and is
  disabled within a week — the exact failure mode §6.3 documents for the ancestry gate.

**G3 must gate on CLASS, never on SIZE** (§3.3).

Other measured exposure:

| exposure | measurement |
|---|---|
| detached HEADs | **8 of 139**; exactly **1** (`ed14f3a6`, `dreamy-crunching-kettle`, **unlocked**) reachable from no branch, remote or tag — carrying *"docs(handoff): archive the P5 four-ports + helper-fold handoff (session 1489a9)"*, 2026-08-26 |
| ref-unreachable SHAs anchored only in per-worktree reflogs | **754 of 1,669**, **all 1,669 still object-present** |
| local branches | **534**, of which **129** have no upstream (three independent instruments agree) |
| **backup** | **partial** — Duplicati daily, but **9 filesets, 18 days max depth, ~7 days for a short-lived file** (§0.1.1). The **tar** archive covers none of it, by two mechanisms (§5) |

### 1.3 Scope correction — this document is juniper-ml-scoped

Revision 1 was headed *"ecosystem-wide applicability"*. Every number in it came from juniper-ml's
`git worktree list`, which is **structurally blind** to sibling repos' worktrees.
`Juniper/worktrees/` holds **149 worktree directories across 9 repos** — juniper-cascor 37,
juniper-canopy 33, juniper-data 23, **juniper-ml 21**, and 35 more. **128 directories were never
measured.** *(The raw entry count is 150; one entry is a `logs` directory, not a worktree. Revision
2's first draft counted it.)*

**This document governs juniper-ml.** Extending it requires re-measuring per repo.

---

## 2. Principles (corrected)

1. **Gate the destruction surface, not the workflow.** A check earns its place only by naming
   something the operation actually destroys — where "the operation" is what the *tooling* does
   (§0.3), not what the bare git verb does.
2. **Reversibility is partial, and thinnest exactly where this protocol operates.** Revision 1 said
   the loss tail was unbounded (false); revision 2's first draft said ~3-year retention (complacent).
   Measured (§0.1.1): **RPO ≤24 h, nine filesets, 18 days maximum depth today, and ~7 days of real
   depth for a short-lived file — which is what worktree-resident evidence is.** So the residual
   exposure is *bounded but not small*, and it is largest for precisely the files G3 exists to
   protect. This raises the value of a cheap secret/evidence check and still does not justify a
   quarantine pipeline (§4).
3. **Consent is declared, not inferred.** The owning session publishes `git worktree lock`. A
   sweeper's inference about liveness is strictly weaker. **But an absent lock is not consent**
   (§3.1 limit (c)).
4. **UNKNOWN refuses — and instrument failure is UNKNOWN.** Revision 1 applied this to
   *classification* only. B1 defeated G3 by making it **exit 128 with empty stdout**, which an
   implementation reading stdout takes as "nothing found". **Every gate checks exit status; a
   non-zero exit refuses.**
5. **Every gate pins its config inputs.** A gate whose answer depends on `git config` is a gate an
   unrelated session can silently disable — and in a linked worktree `git config --local` writes to
   the **shared** config, so the blast radius is the whole repo (§3.2).
6. **Refusal carries an escape hatch and an explanation.** A gate that only says no pushes people to
   `rm -rf`. Refuse, print exactly what would be lost, name the flag that proceeds.
7. **Every gate ships with a negative control proving it can fail.** Revision 1 stated this rule and
   satisfied it for none of its four gates. §3 and §6 now carry one each.

---

## 3. The removal gates — respecified

Each gate below is the exact command, config pinned, exit status checked, with its negative control.

### 3.1 G1 — NOT LOCKED (consent). **HELD from revision 1.**

```bash
git -C "$MAIN" worktree list --porcelain | awk '/^worktree /{wt=$2} /^locked/{print wt}'
```

The harness locks every live session worktree with a reason carrying **pid and process start-time**,
so PID reuse cannot spoof it:

```
locked claude session jolly-finding-micali (pid 1756097 start 24814933)
```

**Why this is the strongest gate: git enforces it at the moment of destruction.** Measured
hermetically — `worktree remove` refuses a locked tree at **no-force** *and* at **single `--force`**
(`fatal: cannot remove a locked working tree ... use 'remove -f -f'`). Only `--force --force`
overrides. G1 is therefore the one gate that is **TOCTOU-closed**, and the protocol contributes
nothing to that — git does.

**Negative control:** lock a throwaway tree → `remove` exits 128; unlock → exits 0. Both observed.

**Correspondence, measured twice independently:** locked = 11, live-cwd set = **the same 11 names**,
0 stale, 0 missed — compared **set-wise** (`comm`, both differences empty), not by count.

**Known limits, stated rather than assumed.**

- (a) The **21** `Juniper/worktrees/` juniper-ml trees are hand-made and **never** locked, so G1 has
  **zero recall** there. Those are governed by G2–G5 plus the V2 manual procedure.
- (b) Harness lock behaviour is **measured, not promised**. If a release stops locking, G1 evaporates
  with nothing failing.
- (c) **An absent lock is NOT evidence of no work.** Revision 1 claimed *"no lock plus no live cwd is
  also no work in flight"*. B1 found live counterexamples: `tender-splashing-wigderson` is
  **unlocked**, last written 2026-09-11 14:49, and holds a **thread-handoff prompt dated yesterday**
  — the artifact type that exists specifically to be resumed. `elegant-watching-chipmunk` is unlocked
  with an ad-hoc script written 17:51. **A session that has exited pending `--resume` holds no lock
  and no cwd, and lands in the "unlocked residue" as the sweeper's first target.** Revision 1's §3 G1
  and §7.2 contradicted each other on exactly this; resolved against the sweeper in §7.2.

### 3.2 G2 — CLEAN INCLUDING UNTRACKED. **Command replaced; two bypasses closed.**

```bash
git -C "$WT" -c status.showUntrackedFiles=normal --no-optional-locks \
    status --porcelain -uall                       # must be empty AND exit 0
git -C "$WT" ls-files -v | grep '^[Ssh]'           # must be empty (skip-worktree / assume-unchanged)
```

**The character class is `[Ssh]`, NOT `[SsHh]`.** Round 2 caught revision 2 shipping `[SsHh]`, and
`H` is `ls-files`' tag for **cached** — the normal state of every tracked file. Measured on this
worktree: `grep -c '^[SsHh]'` returns **2661 of 2661** tracked files; `grep -c '^[Ssh]'` returns
**0**. The wrong class refuses **100% of trees** — the exact defect §3.3 condemns, and the same
shape that killed revision 1. Letter map, all states constructed: `H` cached, `S` skip-worktree,
`h` assume-unchanged, `s` both bits.

Revision 1 specified bare `git status --porcelain`. **That is the command §8.2 calls a defect**, and
B1 broke it twice:

- **Bypass 1 — `status.showUntrackedFiles=no`.** G2 returns empty *and* G3 exits **128 with empty
  stdout**. Both gates pass; `git worktree remove` returns **0 without `--force`** and destroys
  untracked files. Git honours the same config in its own cleanliness check, so revision 1's
  load-bearing sentence — *"This is already enforced by git"* — **is false** under it. And because
  `git config --local` inside a linked worktree writes to the **shared** `$GIT_COMMON_DIR/config`,
  one line in any one of 139 trees blinds both gates **fleet-wide**. Verified **not currently set**,
  so this is latent — but with ~11 concurrent sessions running arbitrary tooling against one shared
  config file, "latent" is a scheduling detail.
- **Bypass 2 — `skip-worktree` / `assume-unchanged`.** `git update-index --skip-worktree a.txt`
  then edit: G2 empty, G3 empty, G1 passes, G4 passes, `remove` returns **0 without `--force`**, edit
  destroyed. Not exotic — sparse-checkout sets `skip-worktree` on every path outside the cone.

**Negative control:** a tree with one untracked file must refuse; with `showUntrackedFiles=no` set,
the pinned form must still refuse (the bare form does not).

**Do not conflate G2 with G3.** `status --porcelain` does not report ignored files, and `--force` is
not required to delete them. **G2 passing is exactly the state in which the payload dies.**

### 3.3 G3 — NO IGNORED PAYLOAD OF A PROTECTED CLASS. **Instrument and shape both replaced.**

```bash
git -C "$WT" -c status.showUntrackedFiles=normal --no-optional-locks \
    status --porcelain --ignored=traditional -uall   # exit 0 required
# sizes, when needed, come from du -- NEVER from stat on a `!!` entry
```

Revision 1 specified `--ignored=matching`. B1 refuted it three ways:

1. **It does not descend into ignored directories.** `matching` reports `logs/` as one entry;
   `traditional -uall` reports `logs/.env`, `logs/top.log`, `logs/deep/deeper/big1.log`. **So the
   secret rule was unenforceable** — `logs/.env` never appears, while `logs/` *does* and classifies
   as "evidence ⇒ harvest", meaning **the specified escape hatch copies the secret into the
   archive**, which revision 1 itself called a worse outcome than losing it.
2. **Byte counting off by ~50,000×.** `stat` on a `!!` directory entry returns the inode size
   (~100 B) for megabytes of content.
3. **Inconsistent granularity** — a directory or a file depending on which matched — so no classifier
   can be written against it.

`--ignored=traditional -uall` is **correct**. Revision 1's own cited precedent,
`util/worktree_cleanup.bash`, uses a filesystem `find` — the right instrument — so revision 1
replaced a correct precedent with a broken one *while citing it as justification*.

**The load-bearing flag is `-uall`, not the `-c` pin — and revision 2's first draft got the reason
wrong even though the command was right.** Round 2 measured all three variants under
`status.showUntrackedFiles=no`:

| variant | result |
|---|---|
| `--ignored=matching` | `fatal: Unsupported combination…`, **rc=128, empty stdout** — fails open by crashing |
| `--ignored=traditional` (no `-uall`) | **rc=0, EMPTY OUTPUT** — a *silent* fail-open |
| `--ignored=traditional -uall` | full listing, rc=0 — correct |

**Principle 4 would NOT catch the middle row**: it exits 0. And with the `-c` pin but *without*
`-uall`, the command returns `!! __pycache__/` and **misses the nested `.env`**. So the crash
diagnosis in §3.2 does not transfer to G3's replacement; `-uall` is what does the work. Anyone
re-deriving this command from the stated reason alone would rebuild the hole.

**`traditional -uall` does not descend into a nested repository either** — it emits a single
`!! build/vendored/` entry, exactly as `matching` does for ignored directories. That independently
confirms G5's rationale (§3.5), and it is a counterexample to defect 3 above: granularity is *still*
inconsistent at a repository boundary, so a classifier must handle trailing-slash directory entries.

**Gate on class, at zero bytes. No size threshold** (§1.2):

| class | members | disposition |
|---|---|---|
| regenerable | `__pycache__/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `*.pyc`, `venv/`, `node_modules/`, `dist/`, `build/`, `.serena/`, `.trunk/` | ignore — **but see G5** |
| **secret** | `.env`, `.env.secrets`, anything matched by `.sops.yaml`, `*.env` | **refuse at 0 bytes.** Never auto-harvest |
| **evidence** | `logs/`, `reports/soak/runs/`, untracked files under `reports/` | **refuse at 0 bytes**; `--harvest DIR` is the escape |
| **bulky low-value** | `.playwright-mcp/` | **fourth class.** Report the size, do not refuse. Lumping 341 MB of console dumps into "evidence" is what makes G3 unbearable |
| unknown | anything else | **refuse** (principle 4) |

**Note `reports/` is NOT an ignored class.** 289 files under `reports/` are **tracked**; only
`reports/soak/runs/` is gitignored (`.gitignore:196`), whose comment calls it *"the raw evidence
behind one run"*. Revision 1's table listed `reports/` wholesale and inflated the apparent payload.

**Two round-2 corrections to that sentence, both about mechanism:**

- Revision 2's first draft said the tracked content is *"caught by G2"*. **It is not — `git status`
  reports nothing for clean tracked files.** There is nothing to catch; they are in the object store
  and survive removal. Right conclusion, wrong mechanism, in a document about instrument quality.
- The **evidence** class row above lists *"untracked files under `reports/`"*, but **any untracked
  file anywhere already refuses at G2**, so that class member can never fire at G3. Verified on a
  clean main-tip tree: 293 files under `reports/`, 293 tracked, 0 untracked. It is retained only as
  documentation of intent; it is not load-bearing.

**Method caveat for anyone re-deriving §1.2's payload figure.** `.gitattributes` puts `*.png`,
`*.jpg`, `*.svg`, `*.gif` and friends under **git-lfs**. Tracked blob sizes are 132-byte pointers
while the working files are megabytes — one tree measured 13.0 MB of `reports/` on disk against
4.66 MB of blobs. A "payload = filesystem minus tracked manifest" computation done **by byte size**
over-counts by the smudge factor. A1's path-class method is unaffected; a byte-class method is not.

**The `.gitignore` reality that forces the fourth class and an explicit allow-list.** The repo carries
**121 patterns**, ~109 of them outside revision 1's 9-item regenerable list. Under "unknown ⇒
refuse", `.vscode/`, `.idea/`, `.ipynb_checkpoints/`, `*.tmp`, `*.pid`, `*.prof`, `nohup.out` each
refuse a tree. B1 measured revision 1's G3 as refusing **84 of 118 trees (71%)**. A gate that refuses
everything is not a gate; by principle 6 it is how you get `rm -rf`. §9 makes the allow-list a
**drift test** rather than a hand-copied list.

**Round-2 correction — the "118/118 have non-empty `logs/`" figure was a placeholder artifact, and it
was mine.** Every tree carries a **tracked, 0-byte `logs/.gitkeep`** (`git ls-files logs` → exactly
that one path; it is not ignored). An `ls -A`-style non-empty test cannot separate *"holds evidence"*
from *"holds a placeholder"*. Re-measured excluding it: **7 of 118** trees have any `logs/` content,
with **4.96 MB of the 5.2 MB in just three trees**, and `reports/soak/runs/` exists in **1**.

**So the real evidence population is ~4 trees out of 118, plus the one 114-byte `.env`.** This cuts
both ways and I record both: the "G3 refuses everything" charge does **not** land on the `logs/`
class (a tracked `.gitkeep` is neither `!!` nor `??`), and the prevalence argument for generalising
the guard is **gone** — which makes §4's and §7.1's "do nothing" conclusion *stronger*, not weaker.
It also makes §5.1's targeted secret check the highest-value item in the document, because it is
aimed at the one file that actually matters rather than at a population.

**Negative control — and its precondition, which revision 2's first draft omitted.** A tree holding
only `__pycache__/` must pass; the same tree plus a 114-byte `.env` **nested inside a directory that
is itself on the regenerable list** must refuse. Constructed as `__pycache__/.env` it discriminates
cleanly: `matching` emits `!! __pycache__/` both times (passes both — the proof it does not ship),
`traditional -uall` emits `!! __pycache__/.env` (refuses).

**The enclosing directory matters.** Built instead as `logs/.env`, `matching` emits `!! logs/`, which
this table maps to *evidence ⇒ refuse* — so `matching` would refuse too and the control would not
discriminate at all. A negative control whose discriminating power depends on an unstated
precondition is not a control; state it.

### 3.4 G4 — HEAD AND EVERY PER-WORKTREE REF REACHABLE. **Command replaced; scope widened.**

```bash
# enumerate FROM INSIDE $WT; evaluate reachability FROM $MAIN
rc=0
for ref in HEAD ORIG_HEAD MERGE_HEAD REBASE_HEAD CHERRY_PICK_HEAD REVERT_HEAD \
           $(git -C "$WT" for-each-ref --format='%(refname)' refs/worktree refs/bisect); do
    # distinguish ABSENT (benign) from PRESENT-BUT-UNREADABLE (instrument failure, principle 4)
    sha=$(git -C "$WT" rev-parse --verify --quiet "$ref") || {
        [ -e "$(git -C "$WT" rev-parse --git-path "$ref")" ] && { echo "UNREADABLE: $ref"; rc=1; }
        continue
    }
    if [ -n "$(git -C "$MAIN" rev-list "$sha" --not --branches --remotes --tags)" ]; then
        echo "UNREACHABLE: $ref $sha"; rc=1
    fi
done
# refuse outright on in-progress state -- resolve paths with rev-parse --git-path,
# NEVER by string-building "$MAIN/.git/worktrees/$name/..."
for p in rebase-merge rebase-apply BISECT_LOG MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD; do
    [ -e "$(git -C "$WT" rev-parse --git-path "$p")" ] && { echo "IN-PROGRESS: $p"; rc=1; }
done
exit "$rc"
```

**Two path defects round 2 found in revision 2's first draft, both fatal:**

1. **`$name` is not `basename "$WT"`.** Git **deduplicates admin-directory names**: a worktree at
   `.../g4wt_orphan` can have its admin dir at `.git/worktrees/g4wt_orphan1`. String-building the
   path checks the wrong directory and the gate **passes while a rebase is live**.
2. **`test ! -e` is vacuously true when the base path does not exist**, so if `$MAIN` is itself a
   linked worktree (`$MAIN/.git` is a *file*), all three tests pass and the gate **silently never
   fires**. Fail-open, exactly the `_is_dirty` polarity defect in §8.2.

`git -C "$WT" rev-parse --git-path <p>` resolves both correctly — verified returning
`…/worktrees/g4wt_orphan1/rebase-merge` for the colliding tree, and per-worktree `BISECT_LOG`
correctly for each tree.

**And `|| continue` violated principle 4.** `rev-parse --verify --quiet` returns rc=1 for *both*
"ref absent" (benign) and "ref present but unreadable" — `--quiet` suppresses the distinguishing
message — so instrument failure read as "nothing to check". The loop above separates them and
carries an aggregate exit status; revision 2's first draft only `echo`ed and returned nothing.

Revision 1 specified `git -C "$MAIN" branch -a --contains "$(...)"`. Three defects:

1. **It inverts under `-C`.** Every other gate in revision 1 used `-C "$WT"`. Run from `$WT`,
   `branch -a --contains <orphan>` returns `* (no branch)` — **non-empty ⇒ G4 PASSES on the exact
   commit it exists to protect.** Isomorphic to the `rev-list --not --all` trap revision 1
   catalogues **twice**, shipped again with no negative control.
2. **It misses tag-anchored commits.** After `git tag -a tagonly <orphan>`, `branch -a --contains`
   still returns empty (falsely refuses) while the `rev-list` form correctly returns empty. Found
   independently by A1 and B1. Revision 1's own §1.1 stated the criterion as *"no branch, remote
   **or tag**"* — the normative code block contradicted the stated criterion.
3. **It is not "cheap"** as revision 1 asserted: 93 ms against 746 refs vs 31 ms for `rev-list`.

**Scope widening (B1).** HEAD is not the only per-worktree anchor. `refs/worktree/*` and
`refs/bisect/*` are **per-worktree namespaces**, live in `.git/worktrees/<n>/refs/`, are
**structurally invisible** to `git for-each-ref` run from `$MAIN`, and die with the worktree. B1
demonstrated a WIP commit saved to `refs/worktree/salvaged-experiment`, unreachable from any branch,
passing all four of revision 1's gates and destroyed by `remove`. Separately, a **rebase in progress**
passes all four gates, and removal deletes `rebase-merge/git-rebase-todo`, `done` and `orig-head` —
unresumable even though every commit survives.

**This matters because the environment's own guidance recommends a WIP commit to set work aside** —
the recommended safe practice produces exactly the artifact removal destroys. **754** ref-unreachable
SHAs sit in per-worktree reflogs today, all object-present.

**Negative control:** an on-branch commit passes; an orphan refuses; a tag-only commit passes; the
same orphan evaluated from `$WT` must still refuse (the `branch --contains` form does not).

**Remedy when G4 fails — corrected.** Revision 1 said *"mint `salvage/<worktree-name>`, then
proceed"*. B1 showed the mint **crashes on its second run** (`fatal: a branch named 'salvage/wt4'
already exists`) and on any hierarchical collision (`refs/heads/salvage/wt4` blocks
`salvage/wt4/sub`) — and if `rc` is unchecked the protocol **proceeds to delete the commit it just
failed to save**. It also creates branches that are by construction upstream-less and therefore
**permanently undeletable under §6.1**. Corrected:

```bash
# the trailing '' is the OLD-VALUE PRECONDITION: create-only, never overwrite
git -C "$MAIN" update-ref "refs/salvage/$(date +%Y%m%d)/$wtname/$refname" "$sha" '' \
    || { echo "salvage failed for $sha"; exit 1; }
```

`refs/salvage/*` sits outside `refs/heads/`, so it does not pollute `git branch` and is not subject
to §6.1. **Confirmed gc-protected by a decisive split test**: with reflogs expired and
`gc --prune=now` run once, an orphan under `refs/salvage/` **survived** while a control orphan with
no ref was **destroyed** in the same run.

**The old-value precondition is not optional.** Revision 2's first draft said *"date-scoped against
collision … check the exit status; on failure, refuse"* — but **`update-ref` overwrites by default,
so there is no failure to check.** Round 2 demonstrated it: same day, same worktree name, same ref
name, a *different* SHA → **rc=0, and the first orphan's only anchor was silently replaced.** Where
revision 1's `git branch` failed **closed** (rc=128 on a duplicate), the unguarded fix failed
**open** — a strictly worse trade. The empty-string old-value argument makes it create-only.

Note the hierarchical collision (`…/HEAD` blocking `…/HEAD/sub`) is **not** avoided by this scheme —
it returns rc=128, the same as `git branch`. That is acceptable because it is loud; revision 2's
first draft claimed it was avoided, which was overstated.

### 3.5 G5 — NO NESTED GIT REPOSITORY. **NEW — added by consensus.**

```bash
find "$WT" -mindepth 2 -name .git -print -quit    # must be empty AND exit 0
```

**The exit-status requirement is not decoration** (round 2: G5 was the only §3 gate that omitted it).
`find` returns **0 with empty stdout** if it hit an unreadable subdirectory before any match — and
"must be empty" then reads PASS. Principle 4 makes that a refusal.

Measured on the live population: **0 of 118 trees refuse**, 118 markers correctly found at depth 1
(each tree's own `.git`), none at depth ≥2, **17 ms** on the largest tree (321 MB, 1,696 files). G5
is cheap and currently silent — which is the argument for shipping it before it is needed, not after.

B1 constructed a tree where **all four** of revision 1's gates passed and destroyed two nested git
repositories holding unpushed commits — `build/vendored/.git` and `logs/nested/.git`, with `WORK.md`
("six weeks of work, never pushed") and `FINDINGS.md` ("irreplaceable analysis").

**Their objects live only in their own `.git/objects`, not in the parent store, so
`fsck --lost-found` — G4's stated recovery window — cannot reach them. There is no recovery.**

The trap is specific: `build/` is on the **regenerable** list, so G3 *affirmatively greenlights* it.
With `venv/`, `node_modules/`, `dist/` and `build/` all gitignored and 118 agent worktrees running
arbitrary tooling, "somebody cloned something into `build/`" is a when, not an if.

**Git's own submodule refusal is much weaker than revision 2's first draft implied**, so G5 is not a
supplement to it — G5 is the gate. Measured:

| case | `git worktree remove` |
|---|---|
| registered submodule, gitlink resolves as a real git dir | `fatal: working trees containing submodules cannot be moved or removed`, rc=128 |
| the same, with a **single `--force`** | **rc=0 — tree and submodule repository destroyed** |
| registered but empty directory | **rc=0, removed, no refusal** |
| registered, non-empty, not a repo | **rc=0, removed, no refusal** |

Note the asymmetry with the lock: a lock needs `-f -f`, the submodule refusal falls to a single
`--force`. **G5's `find` fires on all four cases**, which is why it is the instrument.

**Negative control:** a plain tree passes (its own `.git` is at depth 1, measured with
`find -printf '%d'`; a trailing slash on `$WT` does not shift the depth); the same tree with
`build/vendored/.git` refuses; a repo nested at depth 3 is also found.

### 3.6 Attacked and HELD

- **Symlinks out of the tree.** `wt6/logs -> ../../outside/precious`, ignored: `remove` returned 0
  and the target **survived intact**. *Caveat:* a `--harvest` implemented with `cp -r`/`mv` **would**
  follow it — harvest must use `cp -a --no-dereference` or `rsync -l`.
- **Sparse checkout / `--no-checkout`.** Not independent holes: `--no-checkout` leaves the tree as
  ` D` in status → G2 refuses; sparse reduces to the `skip-worktree` case closed in §3.2.
- **`.claude/worktrees-archive/` dirtying the repo.** It does not — `.gitignore:177` (`.claude/*`)
  already covers it.

---

## 4. Archive — mechanics sound, location wrong, pipeline dropped

`git worktree move "$WT" "$ARCHIVE_ROOT/$(basename "$WT")"`

**What held.** All roots are on one filesystem (`/dev/sdc3`), so the rename is O(1). Bookkeeping is
correct (`.git/worktrees/<n>/gitdir` and `<dest>/.git` both rewritten). And the decisive test: **an
orphan detached-HEAD commit in a *moved* tree survived `git gc --prune=now` in the same run that
destroyed the orphan from a *removed* tree.** Archive-by-move genuinely preserves gc protection;
tar-then-delete would lose it. **§10 Q2 is answered.**

**What failed.**

1. **`move` refuses locked trees** (good — G1 is not bypassed) **but does NOT refuse dirty ones.** It
   relocates a dirty tree silently, exit 0. **The archive step must be gated on G2 explicitly.** And
   `git worktree move -f -f` defeats the lock — revision 1 forbade `--force --force` only for
   `remove`. **Both are forbidden.**
2. **Both proposed archive roots are unbacked by tar.** `<repo>/.claude/worktrees-archive/` is under
   `.claude`, in `EXCLUDE_DIRS`. `Juniper/worktrees-archive/` is worse: `check_application_repos`
   iterates only `APPLICATION_REPOS`, a hard-coded 10-repo list that omits `worktrees`, so it is
   never tarred at all. Revision 1 implemented *"reversibility before safety"* as a `rename(2)` on
   the same inode into a path no tar ever reads. **It is covered by Duplicati** (§0.1) — which is the
   honest statement: the archive is a convenience for an operator who changes their mind, **not** a
   backup. Say so.
3. **A moved tree relocates a live session's cwd.** Everything held by absolute path breaks across the
   rename — `--resume` state, the harness's recorded worktree root, and this session's own sandbox
   isolation check. With §3.1 limit (c), the archive step must never touch an unlocked-but-recently-
   written tree.
4. **The archive reclaims nothing** — 0 bytes (same-filesystem rename), 0 refs, 0 entries off
   `git worktree list`. Revision 1 conceded this and then presented the T+14 reap as a *second
   measurement*. It is not: the tree was archived because it passed the gates, and 14 days later it is
   still unlocked, still clean, still holds the same bytes and the same HEAD. **Nothing can be learned
   by re-running them.** The quarantine is a pure delay.

**Verdict: retain the primitive, drop the pipeline.** Given §0.1 (Duplicati already provides the
reversibility) and point 4 (the archive reclaims nothing), a quarantine-then-reap pipeline buys a
delay against an already-bounded risk, at the cost of an archive root, a scheduler that does not
exist, and a second unmanaged pile. **Use `git worktree move` ad hoc when an operator wants one tree
set aside. Do not build the pipeline.**

---

## 5. Backup — corrected

**The tar archive covers none of the at-risk payload, by two independent mechanisms:**

- `util/juniper-backup.bash:111` — `EXCLUDE_DIRS` names `.claude`, `.playwright-mcp`, `logs`,
  `reports`, `.serena`. **Every category in the 355 MB non-regenerable table is excluded by name**,
  including for the 21 non-`.claude` trees.
- `APPLICATION_REPOS` (a hard-coded 10-repo list) omits `worktrees`, so `Juniper/worktrees/` is
  outside the tar **by omission from the include set**, not by exclusion. Revision 1 stated the wrong
  mechanism and understated the gap.

**But the tar archive is not the backup of record. Duplicati is, and it covers everything** (§0.1).

Revision 1's §5 — an "infrastructure gap" with three options — therefore dissolves. The true residual
exposure is:

| exposure | magnitude |
|---|---|
| RPO | **≤24 h** against a 14:00 UTC daily |
| filesets in existence | **9** (oldest `20260825T102739Z`; 08-26→08-31 and 09-02→09-04 already thinned) |
| max restore depth today | **18 days** — the set was recreated 2026-08-25 |
| depth for a **short-lived** file | **~7 days**, then a lottery — retention deletes *filesets*, so a file whose whole lifetime falls between two survivors is in none of them |
| restore drill against a worktree path | **never run** |

### 5.1 The one file that must not wait for rollout step 5

`…/worktrees/curious-plotting-hummingbird/.env` (114 B) is **not** an ordinary stray secret, and
revision 2's first draft buried it in a table cell. Per
`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`:

- It carries `PASSPHRASE` and `PASSPHRASE_OLD` in cleartext.
- **Live filter 43 excludes `/home/pcalnon/.config/duplicati-backup/`, so the key is not in the
  backup that it unlocks.**
- **`PASSPHRASE_OLD` has no surviving out-of-band copy at all** — *"recoverable only through
  `PASSPHRASE`, by restoring the stray `.env` from the backup."*
- The certification's **Tier 3 — BLOCKED, do not sweep** list names it explicitly as untouched and
  unproposed.

**And it passes the sweep today.** Measured: `curious-plotting-hummingbird` is **unlocked**, branch
`fix/handoff-passphrase-resolved` (upstream `[gone]`), HEAD `8f82ea5d`, and
`merge-base --is-ancestor 8f82ea5d origin/main` → **true**. So: not locked, not self-cwd, not
detached, `in_main` true. The only remaining barrier is `_is_dirty` — which §8.2 records as
**fail-open**. `git worktree remove` then deletes a gitignored file silently.

**Therefore a two-line secret refusal is rollout step 1-2, not step 5.** It does not need the rest
of G3:

```bash
find "$WT" \( -name '*.env' -o -name '.env.secrets' \) -print -quit   # non-empty ⇒ refuse
```

**Recommendation: do not change the backup system for this.** Revision 1's option B (remove `.claude`
from `EXCLUDE_DIRS`) was costed at "23.4 GB per archive cycle"; the real figure is the **17 GB** under
`.claude`, a 37% overstatement, and it would tar `__pycache__` at scale to protect ~13.8 MB Duplicati
already holds. Option A ("harvest into a backed-up path") was **circular** — it named no path, and
every obvious destination (`logs`, `reports`, `.playwright-mcp`, `resources`, `data`, `build`, `dist`,
`venv`, `.serena`) is in `EXCLUDE_DIRS`.

**The one backup change worth making is the opposite of revision 1's.** Because Duplicati covers
Source `/home/pcalnon/` with no worktree filters, all 23.4 GB — every `venv/`, `node_modules/`,
`__pycache__/` and the 201 MB console log — is versioned into a 202 GB destination with 3-year
retention. **Three Duplicati exclusion filters for the regenerable classes under worktree roots**
would reclaim most of that. One config change, and it is the only measurable ongoing cost of keeping
worktrees (§7.1).

---

## 6. Branch and remote deletion — the actually-ungated destructive operation

**This is where the owner's checks 4/5/7 belong, and it is now the highest-value part of the
document** — because §0.3 establishes that the sanctioned vehicle force-deletes the local branch
**and the remote ref** with no gate whatsoever, while revision 1 spent four gates on the removal half
that git already partly protects.

### 6.1 B1 (was check 4) — no un-pushed commits

```bash
git -C "$MAIN" rev-list --count "$EXPLICIT_REMOTE_REF..$BRANCH"     # check rc
```

Use an **explicit** ref, never `@{upstream}`: with no upstream configured `@{upstream}` exits **128**,
and a naive `| wc -l` wrapper reads **0 unpushed** — a false pass. Verified: exit 128, piped form
reads 0.

**"Absent upstream ⇒ UNKNOWN ⇒ refuse" is NOT sufficient, and as first drafted it made B1 useless.**
Round 2 measured the full split; I reproduced it exactly:

| upstream state | all branches | `worktree-*` only |
|---|---:|---:|
| none configured | 129 | 119 |
| configured but **`[gone]`** | **334** | 9 |
| configured and live | 71 | 7 |
| **total** | **534** | **135** |

A `[gone]` upstream does not resolve either, so a naive UNKNOWN⇒refuse rule refuses **463 of 534
(86.7%)** — and on the population §6 actually governs it could pass **at most 7 of 135**.

**Worse, `[gone]` is created by the success condition being gated.** The vehicle's own docstring says
*"GitHub's auto-delete-on-merge often beats the explicit push."* The branches most likely to be
safely deletable are the ones B1 would refuse hardest — **anti-correlated with its target
population**, the exact failure mode §6.3 documents for the ancestry gate, reintroduced one
subsection earlier.

**Corrected rule:**

```bash
if   remote_ref_resolves; then
        refuse unless [ "$(git rev-list --count "$REF..$BRANCH")" = 0 ]
elif git -C "$MAIN" merge-base --is-ancestor "$BRANCH" origin/main; then
        PASS                      # merged, then auto-deleted upstream -- the largest legitimate class
else    refuse                    # genuinely UNKNOWN
fi
```

*Remote ref absent **AND** branch is an ancestor of `origin/main`* is the merged-and-cleaned-up case
and must **pass**, not read as unknown.

**Add to §8.1's family:** `git branch -vv | grep -vc '\['` reads **127**, and it is **wrong**. The
`grep` matches the whole line **including the commit subject**, and exactly two upstream-less
`worktree-*` branches carry `[0.5.1]` in their subject — silently classified as *having* an upstream.
A **false pass, in the unsafe direction, on the exact population §6 governs.**

### 6.2 B2 (was check 5) — a PR exists

Retained as an **advisory signal, not a gate**. A branch with no PR simply fails B3.

### 6.3 B3 (was check 7) — content landed. **Command specified; revision 1's was wrong on 191 of 192.**

```bash
git -C "$MAIN" diff --quiet "origin/main...$BRANCH" -- <tracked paths>    # THREE dots
```

`merged: true` answers *"did a PR merge"*, not *"did this branch's content reach `main`"*. Ancestry is
false for every squash-merge. But revision 1 then said *"a content diff of tracked paths against
`origin/main`"* **without specifying two-dot or three-dot**, and the natural reading is the wrong one.
Verified on `ceiling-look`, an ancestor of `origin/main`:

```
git diff --quiet origin/main ceiling-look      -> exit 1   ("not landed" — WRONG)
git diff --quiet origin/main...ceiling-look    -> exit 0   (correct)
```

**192 branches are ancestors of `origin/main`; exactly 1 sits at its tip.** The two-dot reading
false-refuses ~191 fully-merged branches — *worse* than the ancestry gate it replaced, which is
correct on all 192. Cost is not an objection: 55 ms per branch, ~30 s for 534.

**Remaining holes, stated rather than hidden:** a merged-then-reverted branch refuses forever; a
deliberate long-lived spike refuses forever. Principle 6 requires an escape, so B3 ships with
`--allow-divergent`.

**Negative control:** a fixture branch that is behind `main` and fully merged. The two-dot form fails
it; the three-dot form passes.

### 6.4 B4 (was check 6) — no armed auto-merge. **REINSTATED.**

Revision 1 dropped this. The argument was wrong three ways:

1. **The citations pointed at docstring prose, not code.** `util/safe_merge.py:57-60` and `:62` are
   inside the module docstring. The implementing code is `repo_allows_auto_merge` (`:495-510`), its
   guard (`:654-656`), `ARMABLE_STATES` (`:553`) and the call gate (`:930-933`). Found independently
   by A2 and B2 — citing documentation as an implementation site, in a section arguing from
   implementation behaviour, is the §8.1 failure mode.
2. **The source refutes the inference.** `safe_merge.py` is the tool that **prevents** both hazards:
   `ARMABLE_STATES` excludes `CLEAN`, so it never arms an already-green PR, and it gates the fallback
   on `allow_auto_merge`. The sanctioned merge path does not exhibit the harm revision 1 attributed
   to it; only a **hand-run** `gh pr merge --auto` does.
3. **"Satisfying a gate induces the action" is self-refuting.** A gate is a predicate that refuses,
   not an instruction. By identical logic G1 "induces `git worktree unlock`" — the thing §7.2 forbids
   outright.

**And it is not redundant with B3.** An armed auto-merge net is a *live, pending, server-side merge*.
B3 says "not landed"; B4 says "and it is about to be — do not touch it." Given §0.3, the vehicle runs
`push origin --delete`, which **destroys the pending merge and closes the PR** — a destruction surface
B3 cannot see.

```bash
gh pr view "$PR" --json autoMergeRequest --jq '.autoMergeRequest != null'   # true ⇒ refuse
```

### 6.5 Preserve the admin directory before removal

Dump `.git/worktrees/<name>/logs/HEAD`, `ORIG_HEAD`, `refs/` and any `rebase-merge/` state alongside
the archive. 754 ref-unreachable SHAs are anchored only in per-worktree reflogs today.

---

## 7. What this protocol is NOT for

### 7.1 It is not a capacity measure — and "do nothing" is now stronger

| | |
|---|---|
| juniper-ml worktree disk | **20.8 GB** (17.5 GB `.claude` + 3.28 GB of juniper-ml's 21 trees in `Juniper/worktrees`). *Revision 1's 23.4 GB annexed other repos' worktrees.* |
| volume | 3.6 TB, 59% used, 1.5 TB free → **0.65% of disk** |
| `git status --porcelain` | 17 ms |
| `git worktree list` | 31 ms |
| `packed-refs` | 87,364 B |
| age | **see below — revision 2's first draft mixed denominators** |

**Age, restated over one denominator with the instrument named.** Round 2 found the first draft's row
("10 of 118 older than 30 d; 57 within 7 d") mixed populations: "57 within 7 d" reproduces exactly
over **139** `.git/worktrees/*/HEAD` mtimes, not over 118, and "10 of 118 >30 d" reproduces under no
instrument at all. Four candidate instruments disagree by up to 20 trees:

| instrument | ≤7 d | >30 d |
|---|---:|---:|
| `.claude/worktrees/*` directory mtime (n=118) | 37 | 13 |
| deepest-file mtime per tree (n=118) | 38 | 12 |
| `.git/worktrees/*/HEAD` mtime (n=139) | **57** | 13 |
| `.git/worktrees/*/gitdir` mtime (n=139) | 49 | 13 |

**This is load-bearing**, because §7.2's veto is keyed to the 7-day figure. Adopt the
deepest-file-mtime instrument over n=118 (it is the one that actually answers *"has anyone written
here"*). **Consequence: the veto, not G1, is the binding constraint** — the sweepable set after it is
roughly 118 − 38 ≈ **80 trees**, and the 11 locked are a subset of the recent.
| inode pressure | 4,124,846 / 245,178,368 = **2%** — not a cost |

**Revision 1's sole stated cost was a category error.** It claimed *"the real documented cost is the
memory budget — a diverging worktree `AGENTS.md` causes both copies to load."* `conf/memory_budget.json`
contains **zero** occurrences of "worktree"; it caps character counts on always-loaded files and counts
no worktrees. The diverging-`AGENTS.md` effect is real but **per-live-session**, borne by the owner,
and not a cost of the stale pile.

**The one real ongoing cost is backup volume** (§5), and its fix is three Duplicati filters.

### 7.2 It is not a licence for cross-session sweeping

27 distinct live cwds under `Juniper/`, 53 `claude` processes, 11 juniper-ml worktrees held live.

**Correcting revision 1's own TOCTOU argument:** it claimed a census of 140 trees *"takes minutes"*.
Measured: G2 25 ms, G3 23 ms, G4 93 ms → **a full five-gate census of 139 trees is ≈24 seconds** — off
by one to two orders of magnitude, in the section whose argument rested on the window being wide.

The honest statement is narrower and worse:

- **G1 is TOCTOU-closed** — because *git* re-validates the lock at removal, not because of anything
  the protocol does.
- **G2's tracked half is TOCTOU-closed** for the same reason — except under the two bypasses in §3.2,
  where git's own re-validation is blinded too.
- **G3, G4 and G5 are completely unvalidated at removal time.** A session that writes 200 MB of
  `.playwright-mcp/` logs, or creates a detached commit, between gate evaluation and `remove` loses it.
- **`git worktree move` re-validates the lock but not cleanliness**, so the archive path has a
  **strictly wider** TOCTOU surface than the removal path.

**Rule: a sweeper takes only the unlocked residue — and the unlocked residue is not safe.** §3.1 limit
(c) gives two live counterexamples from the last 24 hours, one holding a thread-handoff prompt.
**Resolution: recent mtime is a veto.** A tree written within the last 7 days is not swept regardless
of lock state. `--force --force` — for `remove` *and* for `move` — is forbidden outright.

---

## 8. Tooling inventory

### 8.1 Instrument-quality rule — now with ten members

A check that cannot separate the two cases it exists to separate. Revision 1 listed seven; consensus
added three, **all three inside revision 1 itself**:

1. `commitBody | length` — 0 for both `null` and `""`.
2. The soak binder's `ledger=N` — filename, not content.
3. Case-sensitive trailer matching — GitHub normalises `Co-Authored-By`.
4. Subject-in-body on single-commit PRs.
5. Stale-vintage tree comparison.
6. `orphaned = on_disk − linked` — algebra on counts, set-blind.
7. `rev-list --not --all` — includes worktree HEADs. **Structurally incapable** of returning
   "unreachable" for a live tree; it flipped 0→1 the instant the worktree was removed.
8. **NEW — "is it in the tar archive?" answering "is it backed up?"** One system read as the system.
   Two agreeing readings of the same instrument are not corroboration (§0.1).
9. **NEW — `git diff --quiet origin/main $B` (two-dot)** — reports "not landed" for 191 of 192 landed
   branches (§6.3).
10. **NEW — `git branch -vv | grep -vc '\['`** — the bracket matches the commit **subject**; two
    upstream-less branches carry `[0.5.1]` and read as having an upstream (§6.1).
11. **NEW, round 2 — `git ls-files -v | grep '^[SsHh]'`** (revision 2's own §3.2). `H` is the tag
    for **cached**, i.e. every normal tracked file. Measured here: **2661 of 2661** match; the
    corrected `[Ssh]` matches **0**. A gate that refuses the entire population.
12. **NEW, round 2 — `git update-ref <ref> <sha>` with no old-value argument** (revision 2's own
    §3.4 remedy). It **overwrites silently**, so *"check the exit status; on failure, refuse"* is
    vacuous — there is no failure. It replaced an anchor and returned 0 (§3.4).

13. **NEW, round 2 — an `ls -A`-style "directory is non-empty" test** used to claim *"118/118 trees
    hold `logs/`"* (§3.3). Every tree carries a **tracked, 0-byte `logs/.gitkeep`**, so the test
    cannot separate *holds evidence* from *holds a placeholder*. Real figure: **7 of 118**. I ran
    this one myself, while "verifying" another reviewer.
14. **NEW, round 2 — reading `~/.local/state/duplicati-server-db/…sqlite` and calling it the server
    DB.** It is a **root-written snapshot**, one run stale, with an empty `Log` table. §0.1's
    re-derivation used the same artifact as the finding it was checking — member 8 again, one level
    up (§0.1.1(d)).

**Members 11–14 were introduced by revision 2 while correcting revision 1**, and 8, 9 and 10 by
revision 1. **Seven of fourteen members of this family were authored by the document that defines
it** — and two of those seven (13, 14) were authored by the reconciler *in the act of verifying the
reviewers*. That is the argument for the rule and for the rounds, not against them: every one was
caught, none shipped, and the failure rate is the reason a single pass is not validation.

**Every gate in §3 and §6 ships with a negative control proving it can fail**, with its precondition
stated (§3.3) where discriminating power depends on one.

**The round-2 corrections were themselves verified, not asserted** — hermetically, by
`util/ad-hoc/2026-09-12_worktree_v3_consensus/verify_respecified_gates.bash`, which builds a
throwaway repo and demonstrates each fix **in both directions**:

| correction | measured |
|---|---|
| `update-ref … ''` create-only | first write rc=0; second write at a different SHA **rc=128, anchor preserved**. Control *without* the precondition: **rc=0, silently clobbered** |
| `grep '^[Ssh]'` | fixture `S a.txt` + `H b.txt` → wrong class `[SsHh]` matches **2 of 2 tracked**; corrected matches **1** (only the skip-worktree file) |
| `rev-parse --git-path rebase-merge` | from a linked worktree → `.git/worktrees/wt_a/rebase-merge`; from the main repo → `.git/rebase-merge` |
| absent vs present-but-unreadable | absent `MERGE_HEAD` → rc=1 **and** git-path does not exist ⇒ benign, continue |

A correction that is only asserted is the same class of claim as the defect it replaces.

### 8.2 Inventory

| component | state | action |
|---|---|---|
| `scripts/cleanup_session_worktrees.py` | Implements G1 (lock + self-cwd), a dirt probe, merged-PR check. **Then force-deletes the local branch and the remote ref, ungated** (§0.3) | **Split `remove` from `delete-branch`; gate the branch half on §6 — before any §3 work** |
| — its `_is_dirty` | **Fails OPEN.** `_run` never reads `returncode`; `_is_dirty` is `bool(stdout.strip())`, so a git error reads CLEAN. `_is_ancestor` directly below tests `.returncode == 0` and fails CLOSED — opposite polarity, same file | **Defect.** Check rc (principle 4) |
| — its dirt probe | Bare `status --porcelain`; no `-c status.showUntrackedFiles=normal`, no `-uall` | **Defect** — §3.2 |
| — ignored-content guard | **Absent.** `curious-plotting-hummingbird/.env` is in its passing set today: unlocked, clean, HEAD an ancestor of `origin/main`. Every gate passes; the only thing between it and deletion is a probe that cannot see it | **Gap** |
| `util/worktree_cleanup.bash` | `--force`/`-D` escalations **fixed and MERGED** — ml#1922, `5b521f7d`, 2026-09-12T10:30Z. *(A2 and B2 measured it as OPEN; it merged mid-round.)* | Adopt §3; extend its guard |
| — its ignored guard | Covers `<wt>/cascor-snapshots/*.h5` at maxdepth 1 only. **Recall zero on the governed population**: of 118 trees, **0** have `cascor-snapshots/`, while **118/118** have non-empty `.playwright-mcp/` and `logs/` | **Generalise to §3.3's classes** |
| `util/ad-hoc/worktree_sweep_survey.bash` + `_apply.bash` | `SAFE/ACTIVE/DIRTY/BROKEN` taxonomy; both pin `-c status.showUntrackedFiles=normal`; apply guards **all** ignored content and **already refuses detached HEAD** | **Closest thing to a correct implementation.** G4 has a shipping precedent here |
| — | **No liveness check in either** | Add G1 |
| `util/ad-hoc/2026-08-28_p5_worktree_cleanup.py` | `--harvest DIR`, `default=None` | Reuse as G3's escape — **but it names no destination**, and harvest must not dereference symlinks (§3.6) |
| `util/ad-hoc/2026-09-02_worktree_inuse_probe.py` | cwd + open-fd + argv; its own header says cmdline is WEAK and other users' `/proc` is unreadable | Advisory only; G1 supersedes it as the gate |
| `util/remove_stale_worktrees.bash` | No predicate; selector matches **139/140**; no `set -euo pipefail`, no dry-run; **deletes the caller's own cwd** (git 2.53.0 carries no cwd refusal — only main-worktree, submodule, dirty, locked). Description corrected in ml#1922. Its `awk -F " "` defect is **latent**: 0/139 live paths contain a space, and `-F " "` is awk's default splitting anyway | **Delete or rename** (Q3) |
| — its test | `TestRemoveStaleWorktrees` asserts removal **succeeds**; fixture builds a bare `worktrees/` and **never** a `.claude/worktrees/` case; wired into `ci.yml:246` **and** `main-verify.yml:404`. **CI pins the destructive behaviour as a contract** | Fix with the script |
| — | The same test file also covers **`util/cleanup_open_worktrees.bash`**, which revision 1 never assessed | Q3's scope is wider than stated |
| `util/worktree_new.bash` | Hardcoded to one branch name; activates conda env **`JuniperCascor`, which does not exist** (real: `JuniperCascor1`). Writes to `Juniper/worktrees`, so it created none of the 118 session trees | **Defect** — fix or retire |
| `util/juniper-backup.bash` | `:111` excludes `.claude`, `.playwright-mcp`, `logs`, `reports`, `.serena`; `APPLICATION_REPOS` omits `worktrees` | **Not the backup of record** (§5). Leave it |
| `…WORKTREE-CLEANUP-PROCEDURE-V2.md` | **Phase 4 contradicts itself**: Step 8 says *"Never pass `--force` to `git worktree remove`"*; Step 9, twelve lines later, prescribes exactly that; Step 10 prescribes `-D`. Phase 1's stash line uses the sanctioned `push -u -m` form but with a non-unique tag and no `apply <sha>` restore | Phase 4 superseded by §3; Phase 1's stash line needs a unique tag |
| `Juniper/AGENTS.md` § Worktree Procedures | *"Do not leave stale worktrees: clean up promptly after merging"* — **always loaded, with no counterweight** anywhere in the section. The strongest pro-deletion pressure in the system, and it names no hazard | **Add the counterweight.** Unversioned, so this document is the record |

### 8.3 Infrastructure gaps

1. **No manifest at creation.** The harness records nothing, so an allow-list design is not
   implementable for 118 of 139 trees — which is why G1 (the lock) is the de facto creation record.
2. **No reap scheduler** — and §4 no longer needs one.
3. **129 worktree directories in 9 sibling repos are unmeasured** (§1.3).

---

## 9. Rollout — reordered by risk reduction per unit of work

Revision 1's order was inverted: it deferred the only ungated destructive operation to step 6 of 7,
while steps 3–5 *raised the pass rate* of the sweep and therefore the firing rate of that ungated
deletion.

1. **The two-line secret refusal (§5.1)** and **`_is_dirty`'s fail-open fix**. Together these are
   ~5 lines and they close the one live, named, documented hazard: a file the Duplicati certification
   marks *"BLOCKED, do not sweep"*, which is in the vehicle's passing set today behind nothing but a
   gate that fails open. Nothing else in this list protects a file that specific.
2. **Pin `-c status.showUntrackedFiles=normal -uall` on every probe** (§3.2 bypass 1).
3. **Fix the branch half.** Either split `remove` from `delete-branch`, or gate the existing
   composite on §6 (B1/B3/B4). **Whichever is chosen, the `(in_main OR merged_pr)` test must be
   retained on the branch side** — §0.3 shows `merged_pr` alone cannot see commits pushed after a
   merged PR, so B1 must run *in addition to* it, never *instead of* it. A split that drops the merge
   test from one half is a regression, and a split that never deletes branches grows the 534-branch
   pile monotonically.
4. **Add G5** (nested `.git`). One `find`, 17 ms, currently silent; the only gate with an
   unrecoverable failure mode.
5. **Add G4** with the `rev-list` form and the widened ref set; `refs/salvage/<date>/…` with the
   create-only precondition. Note the primary vehicle already keeps detached-HEAD trees, so this is
   for the *other* tooling and the 21 never-locked `Juniper/worktrees/` trees.
6. **Add the rest of G3** with `--ignored=traditional -uall` and class-based refusal, plus a **drift
   test** that fails when `.gitignore` grows a pattern absent from the regenerable allow-list — 9
   hand-copied entries against 121 patterns will rot (§3.3). Lower priority than it looks: the real
   evidence population is ~4 trees (§3.3).
7. **Retire or rename `util/remove_stale_worktrees.bash`** and fix the CI test that pins its
   destructive behaviour — noting it also covers `util/cleanup_open_worktrees.bash`.
8. **Three Duplicati exclusion filters** for regenerable classes under worktree roots (§5).
9. **Add the counterweight** to `Juniper/AGENTS.md` § Worktree Procedures.

**Not doing:** the archive/quarantine/reap pipeline (§4), and any change to `util/juniper-backup.bash`
(§5).

### 9.1 Monitored assumptions

- **The lock↔liveness correspondence.** Two independent snapshots, both 11/11, 0 stale, 0 missed,
  compared set-wise. But both sample largely the same long-running sessions, so this is **not** an
  independent second sample — and it measures the wrong predicate. The predicate that matters is
  *"unlocked ⇒ safe to destroy"*, which has **two counterexamples in the last 24 hours** (§3.1 limit
  (c)). Hence the mtime veto in §7.2.
- **Harness lock behaviour is measured, not promised.** Revision 1 proposed a canary asserting ≥1
  locked tree during an active session. **That canary cannot be built**: a fresh CI clone has no
  worktrees, and locally it is a tautology (the session running it holds its own lock). Its negative
  control cannot be constructed either. **Withdrawn** — no monitor is proposed, and the assumption is
  recorded as unmonitored.

---

## 10. Open questions for the owner

| # | question | status |
|---|---|---|
| **Q1** | What fraction of the ignored payload is regenerable? | **ANSWERED** — 72.1% regenerable; of the 27.9% remainder, 96.1% is Playwright console dumps; genuinely irreplaceable ≈9.9–13.8 MB, ~1% (§1.2) |
| **Q2** | Does `git worktree move` refuse locked/dirty trees? | **ANSWERED** — refuses locked (G1 not bypassed), does **not** refuse dirty (§4) |
| **Q3** | Delete `util/remove_stale_worktrees.bash`, or rename it? | **OPEN.** Wider than stated: its CI test also covers `util/cleanup_open_worktrees.bash`, in two workflows |
| **Q4** | Accept §5's conclusion that no backup change is needed beyond the three Duplicati filters? | **OPEN** |
| **Q5** | Given **~7 days** of real restore depth for a short-lived file (§0.1.1), should `reports/soak/runs/` be committed rather than gitignored? | **OPEN — and the question that actually matters.** Committing the evidence closes the exposure at source and makes G3 nearly moot. §0.1.1 strengthens this considerably over revision 2's first draft |
| **Q8** | Should a restore drill be run against a worktree-resident path? | **OPEN — NEW.** None has ever been run (§5); the 2026-08-25 drills predate the current fileset and targeted other paths |
| **Q6** | Should a peer session ever sweep, or only the owner plus the mtime veto? | **OPEN.** §7.2 argues owner-plus-veto |
| **Q7** | Extend to the other 9 repos' 129 worktrees, or leave this juniper-ml-scoped? | **OPEN** (§1.3) |

---

## 11. What this design does NOT claim

- **It does not claim deletion is necessary.** §7.1's numbers and §0.1's correction support *"do
  nothing to the worktrees"* as the honest default. This document exists so that *when* deletion
  happens it is gated — and §9 is ordered so the tooling fixes land whether or not a sweep is ever run.
- **It does not claim the seven original checks were wrong.** §0.3 retracts that. They were aimed at
  the composite operation the tooling performs, and §6 reinstates four of them there.
- **It does not claim ecosystem scope.** 129 worktrees in 9 sibling repos are unmeasured (§1.3).
- **It has not been executed.** No worktree, branch, ref or stash was mutated in producing this
  document or the consensus behind it. Destructive testing was confined to throwaway repos.
- **The Playwright classification is A1's, by path class.** Its stated bias is a single-branch tracked
  manifest, over-estimating the non-regenerable figure by ≤3.9 MB.

---

## 12. Documents

- [`JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`](JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md)
  — Phase 4 superseded by §3–§4 on ratification; Phase 1's stash line needs a unique tag (§8.2).
- [`JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`](JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md)
  — creation side; §8.3 item 1 (no manifest) is a finding against it.
- [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
  — the procedure this design was validated under, and which rejected revision 1.
- [`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md)
  — the 2026-08-29 near-miss and its recovery (§0.2). *Revision 1 cited a session-memory slug here and
  named no document.*
- [`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`](JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md)
  — the backup of record (§0.1, §5); its **Tier 3 "BLOCKED, do not sweep"** list and the
  `PASSPHRASE` circularity are the basis of §5.1.
- [`JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_DUPLICATI-DB-RESTORE-RUNBOOK.md`](JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_DUPLICATI-DB-RESTORE-RUNBOOK.md)
  — restore procedure; bears on §0.1.1's "no drill against a worktree path".
- [`JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`](JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md)
  — prior archive damage; bears on §5's depth conclusion.
- `Juniper/AGENTS.md` § Worktree Procedures — carries the always-loaded *"Do not leave stale
  worktrees"* instruction whose counterweight §9 step 8 adds. **Unversioned**; this document is the
  versioned record.
- Consensus working papers, under `util/ad-hoc/2026-09-12_worktree_v3_consensus/`:
  `REVISION1_REJECTED_BY_CONSENSUS.md`, `RECONCILER_LEDGER.md`, `RECONCILER_LEDGER_A1.md`,
  `RECONCILER_LEDGER_B2.md`, `duplicati_worktree_coverage_probe.py`.
