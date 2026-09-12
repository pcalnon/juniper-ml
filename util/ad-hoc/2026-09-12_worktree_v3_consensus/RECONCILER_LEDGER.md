# V3 design — consensus reconciler ledger

Target: `notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`
Round: 2026-09-12, 4 reviewers (A1 git mechanics + census, A2 tooling, B1 gates, B2 policy).
Reconciler duty (§5 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`):
lone findings are re-derived before acceptance. Those re-derivations are recorded below.

## Lane A2 findings — RE-DERIVED BY RECONCILER

| # | finding | my re-derivation | verdict |
|---|---|---|---|
| R1 | `scripts/cleanup_session_worktrees.py` `_is_dirty` fails **OPEN** | `_run` never reads `returncode`; `_is_dirty` is `bool(stdout.strip())`, so a git error reads CLEAN. `_is_ancestor` directly below it tests `.returncode == 0` and fails CLOSED. Same file, opposite polarity. | CONFIRMED — the design's unqualified "Fails closed" is WRONG |
| R2 | V2 Phase 4 contradicts itself on `--force` | V2 Step 8 blockquote: *"Never pass `--force` to `git worktree remove`: git's dirty-check is the time-of-check/time-of-use guard."* Step 9, twelve lines later: *"If removal fails (uncommitted changes): `git worktree remove --force`"*. Step 10: `git branch -d`, then `git branch -D`. | CONFIRMED verbatim |
| R3 | V2 Phase 1 recommends stashing | V2 Phase 1 Step 1: `# or: git stash push -u -m "pre-cleanup"`. **Narrowing:** this is the *tagged push* form, which is the sanctioned shape — not bare `git stash`. What it lacks is a UNIQUE tag and the `apply <sha>` / drop-by-tag restore. A2 stated this more strongly than the evidence supports. | CONFIRMED WITH NARROWING |
| R4 | the one ignored-content guard has recall ZERO on the governed population | Counted across `.claude/worktrees/*/`: **trees=118, `cascor-snapshots/`=0, `.playwright-mcp/` non-empty=118, `logs/` non-empty=118, `reports/` non-empty=111**. `util/worktree_cleanup.bash`'s guard covers `<wt>/cascor-snapshots/*.h5` at maxdepth 1 only. | CONFIRMED — sharper than "cascor-only" |
| R5 | `reports/` is NOT an ignored class | `.gitignore`: `logs`/`logs/`/`logs/*` (43-45, 107) and `.playwright-mcp/` (184) are ignored; `reports/` is NOT — only `reports/soak/runs/` (196). **289 files tracked under `reports/`**, 1 under `logs/`. So the 111 non-empty `reports/` are mostly TRACKED content that G2 already catches. | CONFIRMED — the design's G3 evidence-class table row is WRONG |
| R6 | §8.2 says ml#1922 "fixed"; it is OPEN | `gh pr view 1922` → `state:OPEN`. `origin/main` still carries the auto-escalation. The fix is staged-only in this worktree. | CONFIRMED — present tense must change |

## Design edits required

1. **§8.2 row 1** — drop the unqualified "Fails closed"; state the split polarity (R1). This is the file §8.2 nominates as V3's primary vehicle, so the claim matters.
2. **§8.2 `worktree_cleanup.bash` row** — "fixed in ml#1922" → "fix OPEN in ml#1922, NOT yet on main" (R6).
3. **§3 G3 evidence-class table** — `reports/` → `reports/soak/runs/`; add `.playwright-mcp/` and `logs/` as the measured-universal classes (R4, R5).
4. **§3 G3 rationale** — replace "cascor-only" with the recall-zero measurement (R4).
5. **§8.2 V2 row** — "Phases 1–3, 5–7 sound" is REFUTED: Phase 4 self-contradicts (R2) and Phase 1's stash line lacks a unique tag and a restore path (R3).
6. **§10 Q2** (does `worktree move` refuse locked/dirty) — A2 answers it read-only from the git binary's refusal strings. AWAIT A1's hermetic test before striking the question.
7. **§5** — `util/juniper-backup.bash:111` excludes `logs`, `reports`, `.playwright-mcp` INDEPENDENTLY of `.claude`, so option A's harvest destination is not covered unless `:111` is also amended. **Option A as written is circular.**
8. **§6** — the two `util/safe_merge.py` citations (`:57-60`, `:62`) point at DOCSTRING PROSE, not code. Re-cite to `ARMABLE_STATES` (`:553`) + the call gate (`:930-933`), and `repo_allows_auto_merge` (`:495-510`) + its guard (`:654-656`). Correct the inference too: **safe_merge is the MITIGATION, not the defect** — only a hand-run `gh pr merge --auto` reaches the hazard.
9. **§3 G4** — `util/ad-hoc/worktree_sweep_apply.bash:121-125` already refuses detached HEAD. G4 HAS a shipping precedent; credit it.
10. **§7.2 / §8.3** — `Juniper/AGENTS.md:240` (*"Do not leave stale worktrees: clean up promptly after merging"*) is always-loaded, has NO counterweight in that section, and is the strongest pro-deletion pressure in the system. Name it.
11. **§9 item 7** — `tests/test_cleanup_open_remove_stale_worktrees.py` also covers `util/cleanup_open_worktrees.bash`, which §8.2 never assessed. Scope is understated.
12. **§8.2 `remove_stale_worktrees.bash` row** — the `awk -F " "` defect is LATENT, not active: 0/139 live paths contain a space, and `-F " "` is awk's default whitespace splitting anyway. Soften.
13. **§6 B1** — use the measured figure **534 local branches, 129 with no upstream**, not the "121–129" range from two disagreeing instruments.
