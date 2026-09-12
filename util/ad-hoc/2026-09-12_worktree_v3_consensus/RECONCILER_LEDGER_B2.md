# V3 design — reconciler ledger, Lane B2 (policy half)

Verdict returned: **REJECT as written.** Reconciler re-derived every critical and severe
finding rather than accepting them. Results below. Target document:
`notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`.

## Critical findings — RE-DERIVED

**R1 — `.claude/worktrees/` IS backed up; the "ZERO coverage / irreversible" premise is false.**
**CONFIRMED.** Re-derived with
`util/ad-hoc/2026-09-12_worktree_v3_consensus/duplicati_worktree_coverage_probe.py`. Job
**Yamaguchi**, Source = **`/home/pcalnon/`**. **44 filters, ALL exclusions, ZERO includes.** None
matches `.claude`, `worktrees`, `.playwright-mcp`, `reports`, `.env`. The only `logs` filter is
`Juniper/logs/` — a top-level dir, not worktree subdirs. All four at-risk probe paths fall inside
Source and escape every filter. Options: `dblock-size`, `retention-policy`, `blocksize` — **no
`--skip-files-larger-than`**. Destination: **859 volumes, 202 GB**.

> **SUPERSEDED IN ROUND 2 — read `RECONCILER_LEDGER_ROUND2.md`.** This row's *coverage* finding
> stands, but the depth conclusion drawn from it ("~3-year retention") does not: there are only
> **9 filesets**, the oldest is `20260825T102739Z`, and a short-lived file has **~7 days** of real
> depth. The probe above also read a **root-written snapshot** of the server DB, not the live DB.

**R2 — "branches survive worktree removal" is false of the operation V3 governs. CONFIRMED,
LATER NARROWED.** `_remove_worktree` runs `worktree remove`, then `branch -D`, then
`push origin --delete`, in one function. Corroborated independently by Lane A2.

> **NARROWED IN ROUND 2:** the caller gates on (not self-cwd) AND (not locked) AND (not detached)
> AND (not dirty) AND (`in_main` OR `merged_pr`) before reaching it, so "no gate at all" was
> over-claimed. The accurate charge is a merge test that cannot see post-merge commits, then forced.

**Correction to B2 on R1's date:** B2 read `LastRun` as 2026-09-11 14:00 UTC; the server DB
field actually reads `1789048800` = **2026-09-10T14:00Z**. The *destination* carries a
completed `20260911T140000Z` dlist, so the DB field lags the completed run. B2's date is right
against the better instrument; my first DB-only reading was the weaker one. RPO is **≤24 h**.

## Severe findings — RE-DERIVED

| # | B2 claim | my re-derivation | verdict |
|---|---|---|---|
| **R3** | B3's unspecified "content diff" is wrong on ~191 of 192 landed branches | `git branch --merged origin/main` = **192**. On `ceiling-look` (fully merged): `git diff --quiet origin/main ceiling-look` → **exit 1** ("not landed", wrong); `git diff --quiet origin/main...ceiling-look` → **exit 0** (correct). | **CONFIRMED** |
| **R7** | §7.1's sole stated cost is a category error | `conf/memory_budget.json` contains **0** occurrences of "worktree"; top-level keys are `_README`, `files`. It caps character counts on always-loaded files. It counts no worktrees. The diverging-`AGENTS.md` effect is real but per-LIVE-SESSION and borne by the owner — it is not a cost of the stale pile. | **CONFIRMED** |
| **R9** | The §1.2 motivating incident was RECOVERED, not lost | `/home/pcalnon/Development/python/Juniper/juniper-ml/reports/e2e/_recovered/20260827-28_arc_worktree_leg_logs/` holds **exactly 7 `*_system.log` files, 2.2 MB**, dated 2026-08-30 04:19. | **CONFIRMED** |

**Correction to B2 on R9/R10's repo:** B2 looked in `juniper-canopy/notes/` and reported the
note and the `_recovered` tree as non-existent. Both exist in **juniper-ml** —
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (a canopy-subject note
filed in juniper-ml) and `juniper-ml/reports/e2e/_recovered/`. B2's substance holds; its path
attribution was wrong. Likewise B2's claim that `reference_worktree_remove_deletes_ignored_files`
"does not exist" because `.serena/memories/` is empty is **wrong** — that is a session-memory
note in `~/.claude/projects/**/memory/`, a different store from Serena's. The memory exists.
B2's underlying point survives anyway: a session-memory slug is not a repo document, a reader
cannot follow it, and the note that *should* be cited is the juniper-ml file named above.

## Consequences for the design

Both pillars of §1 are gone:

1. **"ZERO backup coverage → irreversible"** is false. The loss tail is **bounded at a ≤24 h
   RPO with ~3-year retention**, not unbounded. §2 principle 2, G3's entire value proposition,
   §5's framing and §7.1's answer to "why not do nothing" all rest on it.
2. **"the only surviving copy died"** is false. §1.2 is a **near-miss that was recovered in
   full**. The methodological lesson (a sweep is where evidence dies) survives; the loss does not.

**My own §8.1 failure, stated plainly.** I measured *"is it in the tar archive?"* and reported
*"is it backed up?"* — checking one backup system and concluding about backup coverage. That is
exactly the instrument-answers-an-adjacent-question class the document's §8.1 enumerates. It is
the eighth member of that family; R3 (two-dot vs three-dot) is the ninth, and B2's
`branch -vv | grep '\['` is the tenth. All three are inside the document that states the rule.

**The reversal that matters for the owner's original proposal.** My first draft said checks
4/5/7 were "aimed at the wrong operation". R2 shows the sanctioned vehicle performs worktree
removal, `branch -D` and `push origin --delete` as ONE composite operation. So those checks were
aimed at the operation the tooling actually performs — the owner's instinct was better than my
first analysis credited, and the correct move is to gate the composite, not to descope them.

**Check 6 should be RETAINED, re-scoped** (B2 R5). Given R2, `push origin --delete` destroys a
pending server-side auto-merge and closes the PR — a destruction surface B3 cannot see. And my
"satisfying a gate induces the action" argument is self-refuting: by that logic G1 induces
`git worktree unlock`, which §7.2 forbids outright. A gate is a predicate that refuses.

## Still to fold in

- B2 R4: state **129** no-upstream of 534; name both good instruments; add `branch -vv | grep '\['`
  to §8.1 — the bracket matches the commit SUBJECT, and two `worktree-*` branches carry `[0.5.1]`.
- B2 R6: `APPLICATION_REPOS` is a hardcoded 10-repo list and `worktrees` is not in it, so
  `Juniper/worktrees/` is outside the tar by **omission from the include set**, not by exclusion.
  The design states the wrong mechanism.
- B2 R9: add **G5 — no tracked file references this worktree path**; two documented live victims.
- B2 R8: §9 ordering is inverted; the canary in §9.1 cannot be built (a fresh CI clone has no
  worktrees; locally it is a tautology).
