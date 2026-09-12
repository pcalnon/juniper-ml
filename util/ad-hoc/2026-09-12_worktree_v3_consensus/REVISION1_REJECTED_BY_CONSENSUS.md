# Worktree Cleanup Protocol V3 — design

**Date**: 2026-09-12
**Repo**: juniper-ml (ecosystem-wide applicability)
**Author**: Paul Calnon
**Status**: DESIGN — validated by independent agent consensus; supersedes nothing until ratified
**Supersedes (on ratification)**: the removal half of
[`JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`](../../../notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md)
§ Phase 4. V2's Phases 1–3 and 5–7 are **retained unchanged** and referenced, not restated.

---

## 1. Why V3

V2 is a good *session-handoff* procedure and a poor *deletion* procedure, because it was
written against the wrong object. The defect is structural, not a matter of missing steps:

> **Every gate in V2 and in the proposed seven-check list is a BRANCH-AND-PR predicate.
> `git worktree remove` is a FILESYSTEM-AND-ADMIN-DIRECTORY operation.**

Demonstrated hermetically 2026-09-12 (throwaway repos, git 2.53.0):

| operation | branch | stash | ignored files | detached HEAD | `.git/worktrees/<n>/` |
|---|---|---|---|---|---|
| `git worktree remove` | **survives** | **survives** | **DELETED** | **orphaned** | **DELETED** |

So the checks guard two things the command does not destroy (branches, stashes) and say
nothing about the three it does. A checklist of that shape can pass 100% and deliver
approximately no protection.

### 1.1 What that costs, measured on the live population

Population: `git worktree list` = **140** entries = 1 primary + **139** worktrees
(**118** under `.claude/worktrees/`, **21** under `Juniper/worktrees/`), 2026-09-12.

| exposure | measurement |
|---|---|
| ignored payload in trees git calls **clean** | **1.27 GB across 89 trees**; of which **330 MB of `*.log` across 19 trees** |
| largest single artifacts | `dreamy-swinging-sunrise/.playwright-mcp/console-*.log` **201 MB**; `wondrous-spinning-piglet/…` **128 MB** |
| credential material | `curious-plotting-hummingbird/.env`, unencrypted |
| evidence directories | `nifty-tinkering-wave/reports/soak/runs/` — 60 files; `.gitignore` itself calls these *"the raw evidence behind one run"* |
| detached HEADs | **8 of 139**; **1** (`ed14f3a6`, `dreamy-crunching-kettle`) reachable from **no branch, remote or tag** |
| ref-unreachable SHAs anchored only in per-worktree reflogs | **740**, of which **739 still exist as objects** |
| local branches with no upstream | **121–129 of 534** (two instruments, see §8.2) |
| **tar backup coverage of `.claude/worktrees/`** | **ZERO** — `util/juniper-backup.bash:111` lists `.claude` in `EXCLUDE_DIRS` |

That last row is the one that converts "risky" into "irreversible". **All 118 session
worktrees are excluded from the tar archive wholesale**, and for the other 21 the excluded
dirs are `logs`, `reports`, `.playwright-mcp` — precisely the at-risk payload. Duplicati is
the only conceivable undo, and that arc's posture is already flagged degraded.

### 1.2 The precedent this is not the first instance of

`reference_worktree_remove_deletes_ignored_files` records the 2026-08-29 canopy incident:
seven worktrees each held an ignored `logs/system.log`; one was **the only surviving copy** of
evidence qualifying a published finding. Three measurement agents, two adversarial agents and
a reconciler had all hunted for it and missed it. Its heading is *"THE SWEEP IS WHERE EVIDENCE
DIES."*

---

## 2. Design principles

1. **Gate the destruction surface, not the workflow.** A check earns its place only if it
   names something `git worktree remove` actually destroys.
2. **Archive before delete; reversibility before safety.** The loss tail is unbounded; the
   disk pressure is 0.65% (§7.1). Ordering follows from that asymmetry, not from taste.
3. **Consent is declared, not inferred.** The owning session publishes `git worktree lock`.
   A sweeper's inference about liveness is strictly weaker than the owner's declaration.
4. **Every gate must be able to return UNKNOWN, and UNKNOWN must refuse.** Five instrument
   defects in this arc were checks that could not separate the two cases they existed to
   separate (§8.1). A conjunct that cannot be evaluated is a coin flip whose bias was chosen
   at design time.
5. **Refusal must carry an escape hatch and an explanation.** A gate that only says no pushes
   people to `rm -rf`, which is where the loss happens. Refuse, print exactly what would be
   lost, and name the flag that proceeds.
6. **Separate the two operations.** Worktree removal and branch deletion destroy different
   things and need different gates. V2 and the seven-check proposal both conflate them.

---

## 3. The four removal gates

Applied per worktree, in order, all four required. Each is cheap; two are free.

### G1 — NOT LOCKED (consent)

```bash
git worktree list --porcelain | awk '/^worktree /{wt=$2} /^locked/{print wt}'
```

**Rationale.** The harness locks every live session worktree with a reason string carrying
**pid and process start-time**, so PID reuse cannot spoof it:

```text
locked claude session jolly-finding-micali (pid 1756097 start 24814933)
```

Measured correspondence over the 139: **locked ∧ live-cwd = 11; locked ∧ no-live-cwd = 0;
unlocked ∧ live-cwd = 0.** No stale locks, none missed. Git enforces it — `remove` refuses a
locked tree, and so does a *single* `--force`.

**Why this replaces "worktree no longer active".** Process inspection is fail-open: the
in-use probe's own header states that other users' `/proc` entries are unreadable and skipped,
and a session between turns, or one that will be `--resume`d, holds no matching cwd at all.
The lock is the owner saying so at the moment the owner knows.

**Known limits, stated rather than assumed.** (a) A session that crashes before locking leaves
no lock — but that degrades *safe*: no lock plus no live cwd is also no work in flight, and
G2–G4 still apply. (b) The 21 `Juniper/worktrees/` trees are hand-made and **never** locked, so
G1 has zero recall there; those are governed by G2–G4 plus the V2 manual procedure. (c) The
lock is harness behaviour that was **measured, not promised** — if a future release stops
locking, this gate evaporates silently. §9.1 makes that a monitored assumption.

### G2 — CLEAN INCLUDING UNTRACKED (free)

```bash
git -C "$WT" status --porcelain          # must be empty
```

**This is already enforced by git** — `worktree remove` refuses on both tracked modifications
and untracked files. The gate exists in the protocol to make the refusal *explicit and
explained* rather than a bare `fatal:` in a loop, and to forbid the `--force` escalation that
`util/worktree_cleanup.bash` performed automatically until ml#1922.

**Do not conflate G2 with G3.** `git status --porcelain` **does not report ignored files**,
and `--force` is not required to delete them. G2 passing is exactly the state in which the
1.27 GB dies.

### G3 — NO IGNORED PAYLOAD ABOVE THRESHOLD (the gate that does not exist today)

```bash
git -C "$WT" status --porcelain --ignored=matching
```

Classify each `!!` entry against a **regenerable prefix list**, then gate on the residue:

| class | examples | disposition |
|---|---|---|
| regenerable | `__pycache__/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `*.pyc`, `venv/`, `node_modules/`, `dist/`, `build/` | ignore |
| **evidence** | `reports/`, `logs/`, `.playwright-mcp/`, `reports/soak/runs/`, `*.h5` snapshots | **harvest, then gate** |
| **secret** | `.env`, `.env.secrets`, anything matched by `.sops.yaml` | **refuse unconditionally** — never auto-harvest a decrypted secret into an archive |
| unknown | anything else | **refuse** (principle 4) |

Threshold on the residue: refuse above **0 bytes** for the secret class, and above a
configurable byte/count threshold for evidence, with `--harvest DIR` as the sanctioned
escape. Precedent exists: `util/ad-hoc/2026-08-28_p5_worktree_cleanup.py` already implements
`--harvest`, and `util/worktree_cleanup.bash:393-419` already refuses on a non-empty ignored
*snapshot* root — the ecosystem has built this guard once, for cascor `*.h5` only, and it is
blind to `.playwright-mcp/`, `logs/` and the rest.

**Open calibration question (§10, Q1).** B2 sampled 2 of 89 trees and could not classify the
1.27 GB into regenerable vs evidence. If the non-regenerable fraction is ≈0, G3 collapses to a
formality; if it is large, G3 is the single most valuable gate in this document. **Measure
before setting the threshold.**

### G4 — HEAD REACHABLE FROM A REF

```bash
test -n "$(git -C "$MAIN" branch -a --contains "$(git -C "$WT" rev-parse HEAD)")"
```

**Rationale.** A detached worktree's HEAD commit is anchored by exactly one thing:
`.git/worktrees/<name>/HEAD`. Removal deletes it, the commit becomes unreferenced, and the
next `gc --prune` past the grace window destroys it. There is a ~2-week recovery window via
`git fsck --lost-found`, which returns bare SHAs with no message index.

**This is what makes the seven-check list unsafe rather than merely incomplete.** Checks
4/5/7 are universally quantified over *"branches opened during the worktree use"*; a detached
worktree opened none, so **∀x∈∅ is true** and all three pass vacuously. Four of seven
conjuncts are satisfied by the absence of the thing that would have protected the work. The
live instance is `ed14f3a6` (§1.1).

**A trap this gate must avoid, and which caught this session's own reviewer.**
`git rev-list <sha> --not --all` returns **empty** for a live detached worktree, which reads
as "reachable" — because **`--all` includes every worktree's HEAD**. The discriminating form
excludes worktree HEADs:

```bash
git rev-list "$SHA" --not --branches --remotes --tags   # non-empty ⇒ UNREACHABLE
```

**Remedy when G4 fails:** do not refuse outright. Mint `salvage/<worktree-name>` at that SHA,
then proceed. That converts an unbounded loss into a branch someone can triage.

---

## 4. Archive before delete

`git worktree move "$WT" "$ARCHIVE_ROOT/$(basename "$WT")"`

**Why `move` and not `tar`.** All worktree roots live on one filesystem (`/dev/sdc3`), so the
rename is O(1) and free. Crucially the tree **stays a registered worktree**, which means its
objects stay protected from `gc` — a tar archive followed by deletion *loses* that protection
and makes the detached-HEAD loss case **more** likely, not less. Undo is another `move`.

**Phase structure:**

1. **Archive** — `git worktree move` into `<repo>/.claude/worktrees-archive/` (or
   `Juniper/worktrees-archive/`). Reversible, instant, reclaims nothing.
2. **Quarantine period** — configurable, default 14 days, chosen to exceed git's
   `gc.pruneExpire` default so a mistake is recoverable by `move` rather than by `fsck`.
3. **Reap** — re-run G1–G4 on the archived tree, then `git worktree remove`.

**Known failure mode, named rather than hidden:** an archive nobody reaps becomes a second
unmanaged pile, and "delete later" re-runs this decision with *less* context. §9.2 makes reap
a scheduled, reported step rather than an intention.

**Untested primitive (§10, Q2).** Whether `git worktree move` refuses dirty or locked trees
was **not** tested. It must be, before this phase ships — if it silently moves a locked tree,
G1 is bypassed by the archive step itself.

---

## 5. Backup — the infrastructure gap

**`util/juniper-backup.bash:111` excludes `.claude` from the tar archive**, so all 118 session
worktrees have no backup at all; for the other 21, `logs`, `reports` and `.playwright-mcp` are
excluded, which is exactly the at-risk payload.

This is a **gap to close, not a constraint to design around.** Three options, ranked:

| option | cost | assessment |
|---|---|---|
| **A. Harvest at G3 into a backed-up path** | small; reuses `--harvest` | **Recommended.** Targets only the residue G3 already identified, so it scales with real risk rather than with tree count |
| B. Remove `.claude` from `EXCLUDE_DIRS` | 23.4 GB per archive cycle, mostly regenerable caches | Rejected — backs up `__pycache__` at scale to protect a few MB of evidence |
| C. Narrow the exclusion to `.claude/worktrees/*/[cache dirs]` | medium; per-tree globs | Viable fallback if A proves insufficient |

**Secrets are explicitly out of scope for harvesting.** `.env` triggers an unconditional
refusal (G3), never an auto-harvest — writing a decrypted secret into a backup archive is a
worse outcome than losing it.

---

## 6. Branch cleanup — a SEPARATE protocol, where checks 4/5/7 belong

The proposed checks 4 ("no un-pushed commits"), 5 ("PRs created") and 7 ("PRs merged") guard
nothing that `git worktree remove` destroys — **branches survive worktree removal**. They are
the correct gates for a different operation: `git branch -d`/`-D`, which is where refs
actually die, and which `util/worktree_cleanup.bash` performed as an automatic `-D`
fall-through until ml#1922.

So they are **retained, re-scoped**, and applied to branch deletion only:

- **B1 (was 4) — no un-pushed commits.** Implement as `git rev-list --count <ref>..HEAD`
  against an **explicit** ref, never `@{upstream}`: `@{upstream}` exits 128 when no upstream
  is configured, and a naive `| wc -l` wrapper reads **0 unpushed** — a false pass affecting
  121–129 of 534 branches. Absent upstream ⇒ UNKNOWN ⇒ refuse (principle 4).
- **B2 (was 5) — a PR exists.** Retained as an advisory signal, not a gate; a branch with no
  PR simply fails B3.
- **B3 (was 7) — content landed, not merge-flag.** `merged: true` answers *"did a PR merge"*,
  not *"did this branch's content reach `main`"*. Ancestry (`merge-base --is-ancestor`) is
  **false for every squash-merged PR** — 81 worktree branches are not contained in
  `origin/main` today — so an ancestry gate blocks everything and gets disabled. Squash also
  drops content: ml#1877 silently lost **nine** commit messages, ml#1228 lost an
  `Allow-Symbol-Loss:` trailer and reddened `main`. **B3 must be a content diff of tracked
  paths against `origin/main`.**

**Check 6 ("PRs have activated automated merge") is DROPPED, not re-scoped.** It is redundant
with B3 in both directions — if everything is merged, an armed net is moot; if it is not, an
armed net is a promise, not a landing. And it is actively harmful: satisfying it means running
`gh pr merge --auto`, which on an already-green PR **merges on the spot**
(`util/safe_merge.py:62`), and where `allow_auto_merge` is false **silently falls back to an
immediate merge** that can land a PR whose checks never finished (`:57-60`). A
worktree-hygiene checklist that induces unreviewed merges has inverted its purpose.

**Additionally — preserve the admin directory before removal.** 740 ref-unreachable SHAs are
anchored only in per-worktree reflogs, 739 still object-present, including WIP commits. This
environment's own guidance recommends *"a temporary WIP commit to set work aside"* — the
recommended safe practice produces exactly the artifact removal destroys. Dump
`.git/worktrees/<name>/logs/HEAD` and `ORIG_HEAD` to the archive at §4 phase 1.

---

## 7. What this protocol is NOT for

### 7.1 It is not a capacity measure

| | |
|---|---|
| worktree disk | 23.4 GB (17 GB `.claude` + 6.4 GB `Juniper/worktrees`) |
| volume | 3.6 TB, 59% used, 1.5 TB free → **0.65% of disk** |
| `git status --porcelain` | 16–19 ms |
| `git worktree list` | 30–34 ms |
| `packed-refs` | 85 KB |
| age | only **13 of 139** are >30 days; **59** touched within 7 days |

There is no measurable git degradation, and worktrees *protect* objects from `gc`. The real
documented cost is the **memory budget** — a diverging worktree `AGENTS.md` causes both copies
to load. That argues for a conservative gated sweep, not an aggressive one, and it means
**"do nothing" remains a defensible option** on these numbers.

### 7.2 It is not a licence for cross-session sweeping

27 distinct live cwds under `Juniper/`, 53 `claude` processes, 12 juniper-ml worktrees held
live. **Every gate is TOCTOU**: a read-only census of 140 trees takes minutes; a serial sweep
of 128 removals is a far wider window, and session S cannot know that session T is three tool
calls from writing. G1 is the only non-TOCTOU signal because the *owner* publishes it.

**Rule: a sweeper takes only the unlocked residue.** The owning session unlocks at exit. A
peer session never overrides a lock, and `--force --force` (which defeats a lock) is forbidden
by this protocol outright.

---

## 8. Tooling inventory — what exists, what is broken, what is missing

### 8.1 Instrument-quality rule, earned the hard way

Seven checks in this arc could not separate the two cases they existed to separate:
`commitBody | length` (null vs `""`), the soak binder's `ledger=N` (filename vs content),
case-sensitive trailer matching (GitHub normalises `Co-Authored-By`), subject-in-body on
single-commit PRs, a stale-vintage tree comparison, `orphaned = on_disk − linked` (algebra,
set-blind), and `rev-list --not --all` (includes worktree HEADs). **Every gate in §3 and §6
ships with a negative control proving it can fail**, or it does not ship.

### 8.2 Inventory

| component | state | action |
|---|---|---|
| `scripts/cleanup_session_worktrees.py` | Implements G1 (lock + self-cwd), G2, B3-as-merged-PR. Fails **closed**. Tests: `test_cleanup_session_worktrees.py` | **Primary vehicle for V3.** Add G3, G4, archive phase |
| — its dirt probe (`:113`) | Uses bare `status --porcelain`, **not** `-c status.showUntrackedFiles=normal` | **Defect** — the sweep pair already fixed and pinned this; port it |
| — ignored-content guard | **Absent** | **Gap** — `curious-plotting-hummingbird/.env` is in its passing set today |
| `util/worktree_cleanup.bash` | Session-handoff tool; `--force`/`-D` escalations **fixed in ml#1922** | Adopt G3/G4; its `:393-419` snapshot guard is the G3 precedent, currently cascor-only |
| `util/ad-hoc/worktree_sweep_survey.bash` + `_apply.bash` | `SAFE/ACTIVE/DIRTY/BROKEN` taxonomy, ignored-content guard, untracked flag. **No liveness check** | Promote the taxonomy + ignored guard into V3; add G1 |
| `util/ad-hoc/2026-08-28_p5_worktree_cleanup.py` | Implements `--harvest DIR` | **Reuse as the G3 escape hatch** |
| `util/ad-hoc/2026-09-02_worktree_inuse_probe.py` | cwd + open-fd + argv. Header states cmdline is WEAK and other users' `/proc` unreadable | Advisory only; **G1 supersedes it as the gate** |
| `util/remove_stale_worktrees.bash` | No predicate at all; selector matches 139/140; no `set -euo pipefail`, no dry-run; `awk -F " "` breaks on spaces; **deletes the caller's own cwd** | **Delete, or rename to advertise what it does.** Its `TestRemoveStaleWorktrees` asserts the removal *succeeds* and is wired into `ci.yml` and `main-verify.yml` — CI currently pins the destructive behaviour as a contract, against a fixture that never builds a `.claude/worktrees/` case |
| `util/worktree_new.bash` | Hardcoded to one branch name and to conda env `JuniperCascor` (**does not exist**; real name `JuniperCascor1`) | **Defect** — fix or retire; it creates none of the 118 session trees |
| `util/juniper-backup.bash:111` | `.claude` in `EXCLUDE_DIRS` | **Gap** — §5 |
| V2 procedure | Phases 1–3, 5–7 sound | **Retain.** Replace Phase 4 with §3–§4 |

### 8.3 Infrastructure gaps

1. **No manifest at creation.** The harness writes no record of what it created;
   `.claude/` holds only `agents/ skills/ worktrees/ settings*.json`. An allow-list design
   is therefore not implementable for 118 of 139 trees — which is why G1 (the lock) is the
   de facto creation-time record.
2. **No archive root exists.** §4 needs one, on the same filesystem.
3. **No reap scheduler.** §4 phase 3 is otherwise an intention.
4. **`.claude/worktrees/` is unbacked.** §5.

---

## 9. Rollout

1. **ml#1922** (merged/in flight) — stop the `--force`/`-D` escalations; correct the false
   `remove_stale_worktrees.bash` description. *Prerequisite: without it, V3's gates are
   bypassed by the sanctioned tool itself.*
2. **Measure, then calibrate G3** (§10 Q1). Classify all 1.27 GB across 89 trees.
3. **Port the two known guards** into `scripts/cleanup_session_worktrees.py`: the untracked
   flag and an ignored-content gate. One demonstrated live victim.
4. **Add G4** + `salvage/<name>` minting. Cheapest gate, largest averted loss.
5. **Archive phase** — after testing whether `git worktree move` refuses locked/dirty trees.
6. **Branch protocol (§6)** as a separate change, with B1/B3 implemented per their notes.
7. **Retire or rename `remove_stale_worktrees.bash`**, and fix the CI test that pins its
   destructive behaviour.

### 9.1 Monitored assumptions

- **The lock↔liveness correspondence.** One snapshot: 11/11, 0 stale, 0 missed. Sample
  hourly for 7 days; if locked-but-dead trees accumulate, G1 degrades from liveness signal to
  permanent protection — which **fails safe**, but should be known.
- **Harness lock behaviour is measured, not promised.** If a release stops locking, G1
  evaporates with no test failing. A canary test asserting ≥1 locked tree during an active
  session would surface it.

---

## 10. Open questions for the owner

| # | question | why it blocks |
|---|---|---|
| **Q1** | What fraction of the 1.27 GB ignored payload is regenerable? | Sets G3's threshold. If ≈0 non-regenerable, G3 is a formality; if large, it is the most valuable gate here |
| **Q2** | Does `git worktree move` refuse locked/dirty trees? | Untested. If it silently moves a locked tree, the archive step bypasses G1 |
| **Q3** | Delete `remove_stale_worktrees.bash`, or rename it? | Deleting touches its CI test in two workflows; renaming keeps a footgun with an honest name |
| **Q4** | Adopt §5 option A (harvest into a backed-up path), or C (narrow the exclusion)? | Decides whether backup scales with risk or with tree count |
| **Q5** | Is the 14-day quarantine right? | Must exceed `gc.pruneExpire` (2 weeks default); longer costs only disk |
| **Q6** | Should a peer session ever sweep, or only the owner plus a scheduled reaper? | §7.2 argues for owner-plus-reaper; this is a policy call |

---

## 11. What this design does NOT claim

- **It does not claim the seven checks were wrong in spirit.** Seven conjuncts on an
  irreversible operation is the correct *sign*. They were aimed at the wrong operation, and
  §6 re-scopes three of them to where they are correct.
- **It does not claim deletion is necessary.** §7.1's numbers support "do nothing" as a
  defensible position. V3 exists so that *if* deletion happens it is gated — not to argue that
  it should.
- **It has not been executed.** No worktree, branch, ref or stash was mutated in producing
  this document or the consensus behind it.
- **The 1.27 GB is unclassified** (Q1), and its *value* is inferred from one prior incident,
  not asserted by anyone who currently needs those files.

---

## 12. Documents

- [`JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`](../../../notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md)
  — Phases 1–3, 5–7 retained; Phase 4 superseded by §3–§4 on ratification.
- [`JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`](../../../notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md)
  — creation side; unchanged, but §8.3 item 1 (no manifest) is a finding against it.
- [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
  — the procedure this design was validated under.
- `Juniper/AGENTS.md` § Worktree Procedures — carries the always-loaded *"Do not leave stale
  worktrees"* instruction whose counterweight §8.2 restores. **Unversioned**; this document is
  the versioned record.
