# R1-B — omission / residue-loss lane (round 1)

Archived verbatim from the lane's final message (2026-09-24). The only change is transport escaping: `&amp;` decoded to `&`.
Artifact reviewed: `r1/DRAFT_r1.md`, sha256 `8c2fa29042da0c6f0168ad551a7d2009217a520b86a9c16ee21aa58eaf61898a`.

---

## Verdict

**SAFE AFTER FIXES** — every predecessor work item and all 18 ledger items (0–17) have a carrier, and the round-15 fix list is verbatim, but three MAJOR gaps would let a successor lose cited provenance, lose the handoff itself, or merge another session's PR.

## Findings

**1. MAJOR — A6's provenance table and "Three are already unreachable" under-count the ledger's local-only citations; following the table would orphan Phase 9's ten frozen review commits.**
- Where: goal statement "Three are already unreachable"; A6 "Every other cited commit is held by ONE local branch only (table below)" and row "`docs/canopy-e2e-phase9` (`graceful-sprouting-panda`) | `f6861234`".
- Source: `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` :9304–9525 ("Round 1: four lanes on the frozen `e624c281`" … "Round 10 … `b0eb4ac1`"), :8645/:8864 (`800c20bb` and its rebased copy `5a0e4ea9`), :9427 ("the FAQ's text at `b07943d6`"). Item 15's list (:9684–9688) omits all of them — a gap in the source the draft inherits.
- Evidence: `git name-rev` → the ten frozen commits are `docs/canopy-e2e-phase9~1..~10`, `5a0e4ea9` is `~14`, `f6861234` is `~11`; `merge-base --is-ancestor f6861234 e624c281` → true, so `f6861234` is *older* than all ten, and a ref at the table's commit keeps none of them — the branch tip `808b74df` does. GitHub returns 422 for all twelve and for `808b74df`. canopy `b07943d6` → `undefined` in name-rev, 422 on GitHub: a fourth unreachable cited commit. The draft's own tool (`util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py`) reports `800c20bb`/`08a1573a`/`48df689b` on `worktree-squishy-dancing-moth` and `808b74df`; the table omits all four (that row is safe only because `b54e3b3f` happens to be the tip).
- Fix (append to A6): "**Item 15's list is incomplete.** The ledger also cites commits that exist only on local `docs/canopy-e2e-phase9` (tip `808b74df`): the ten frozen review commits `e624c281`, `acf1a93a`, `3f83b9c6`, `86e82c0c`, `07aef715`, `b0b17cad`, `129f4880`, `3297131f`, `04db8614`, `b0eb4ac1`, plus `5a0e4ea9`; and `800c20bb` on `worktree-squishy-dancing-moth`. None is on GitHub. A provenance ref must point at each branch's TIP (`808b74df`, `b54e3b3f`), never at the row's commit. canopy `b07943d6` is also UNREACHABLE. Add all of these to the script's `CITED` list before answering." Goal statement: "Three" → "Four".

**2. MAJOR — The combined handoff and A6's instrument exist only untracked in `bubbly-meandering-pie`, and nothing protects that worktree.**
- Where: goal statement's repo-relative path; Session layout (Lane A → fresh worktree from main, Lane B → `idempotent-jumping-sparkle`); Verification "(any lane)" `…ledger_cited_commit_reachability.py`; Git state "No PR has been opened"; X5.
- Evidence: `git status` here: `?? …canopy-combined-e2e-y2-wave2-selection-owner-calls.md`, `?? util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py`. Neither that script nor `2026-09-24_secret_shape_check.py` exists in `idempotent-jumping-sparkle`. B's predecessor `HANDOFF_2026-09-24_y2-wave2-round-15-fix-pass.md` is likewise untracked only there, and B4 never schedules archiving it.
- Fix: goal statement — "Until its PR merges this file exists ONLY at `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`." Add `bubbly-meandering-pie` to X5 ("only copy of this handoff, the reachability script and the consensus record"). B4: "archive `HANDOFF_2026-09-24_y2-wave2-round-15-fix-pass.md` in the closing PR unless this handoff's PR carried it."

**3. MAJOR — "Never merge other sessions' PRs." dropped.**
- Source: `HANDOFF_2026-09-24_y2-wave2-round-15-fix-pass.md`:5 "ONLY this session's four PRs … No deploys, images, PyPI or GitHub Releases. The juniper-recurrence release is owner-gated. Never merge other sessions' PRs."
- The draft's merge-approval paragraph quotes only the first two sentences, while Lane A tracks other sessions' PRs (`fix/secret-leaks-683-validation`, cascor#690 — both session `bc31e993`'s).
- Fix: "Rules that bind every lane": "**Never merge another session's PR**, whatever the grant — the `fix/secret-leaks-683-validation` PR and cascor#690 are session `bc31e993`'s."

**4. MINOR — The one-message owner-question batch omits standing calls.**
- Where: goal statement "The standing calls: C2 (Y7), C3 (the X8 release), A3 (ledger item 17), and the rest of A6 (the ratings and the account's later actions)."
- Missing: ledger items 3 (F-CANOPY-004's contract), 9 (M-DATASET-17..26), 10 (metrics replay drives no chart) (ledger :9612, :9624, :9626); `S/main/handoff_v4.md`:54 "making recurrence's `Settings` case-sensitive … is the owner's call"; `HANDOFF_2026-09-23_canopy-selection-queue-drained-mirror-shipped-a-n2-run-owner-rulings-open.md`:36 "retiring the ad-hoc copies needs an owner decision under the retention policy" (lost upstream); `HANDOFF_2026-09-24_canopy-selection-four-rulings-made-x11-f2-f1-x8-to-implement.md`:30–31 "It printed `HF_TOKEN` and two PyPI tokens … Token rotation is the owner's call" (B5 names only the PyPI tokens).
- Fix: add all four to the batch.

**5. MINOR — O9's source pointer is wrong; F-060–062 have no source.**
- The README's § Observations holds only O1–O8; O9 is recorded in `HANDOFF_2026-09-24_canopy-selection-four-rulings-shipped-cleanup-and-carry-forwards-remain.md`:76–81 ("Recorded as **O9**") — inherited from A's predecessor.
- F-060–062's sources: `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` Remaining item 4, and `reports/2026-09-24_defect-register-round-42/pending-items-snapshot-2026-09-24T1110Z.md`:21 (LOW 3/LOW 4). "Re-derive each finding first" needs them.
- Fix: name both in A2.

**6. MINOR — Numbering collisions break the draft's promise ("so they cannot collide").**
- "Lane B's handshake pacer" (A5) = Phase 9's review Lane B (ledger:9579), not the draft's Lane B. "Lanes C5, R4-A, A1 and B2" = review-lane names that collide with the draft's items A1/B2/C5. "harness rows for X10, X18–X21" = R15B's mutation IDs, not the claimed selection-arc X10. The draft's X1–X5 collide with the selection design's own IDs (`…SELECTION-REACHABILITY-DESIGN.md` "4.4 Model-state truth (N5 / X1)") while the draft uses X8/X10/X11 in that sense. C6's "Phase 7" is the cleanup procedure's Phase 7 (`notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`) while X4 uses the ledger's. A7 item 12's "F1" is the ledger's Phase 8 slider minor (ledger:8481), not the selection arc's F1.
- Fix: rename cross-lane IDs (e.g., K1–K5) and qualify each phrase above.

**7. MINOR — Three traps weakened.**
- Source `…four-rulings-shipped…md`:123–124: "Snapshot first, and scan the snapshot for the mutants' strings." The draft keeps only "Never upload while one runs."
- A's predecessor: quoted-literal review "by known-literal/length output", and `--allow-shape AGENT_ID=LITERAL` never excuses key material (`key_material()`); the draft: "after reviewing it".
- `…four-rulings-made…md` § Traps: "Agent briefs must forbid printing env/secrets and sending the owner's email anywhere" — dropped, though the A-N2 agent did send the email to sec.gov (`…queue-drained…md`:105). The draft's "Nothing was sent" is true only of the four lanes it names.

**8. MINOR — Verification block changed meaning.**
- The predecessor's `(cd $S/r15 && …)` was a subshell; the draft's bare `cd …/r15 && …` persists, so the next three commands' relative paths fail.
- "(any lane)" misreports from Lane B's worktree: there the ledger is 602,764 bytes (main: 791,576), so triage won't print 70/48/1/2/19, and two named scripts are missing.
- Dropped: `df -i /tmp` (`HANDOFF_2026-09-23_canopy-e2e-phase9-cuts-reviewed-f055-fix1-refuted-f058-filed.md`:147; the defect-register handoff adds "Lane trees filled it to 100% today"; R15A deleted 747 leaked dirs); C's predecessor's `du -sh …harvest…  # 174M` and `grep -c … # 0` checks.

**9. MINOR — Lane B state residue dropped.**
- Untracked `tests/process_cleanup.py` ("main's copy, needed locally, in no upload set", B's predecessor :159) and the intent-to-add state (tripwire + four `2026-09-22_*` tools, :157).
- The old tmpfs scratchpad `…/798c2868-…/scratchpad/` still exists and its `r15` has an identical digest; `S/main/lane_common_r15.md`:8 still names it as the freeze location — a round-16 brief must be re-pointed to S.
- Wave 2's known limitations (`handoff_v4.md`:50–54) are carried only by pointer; one is a live trap for Lane B's own runs (from a `worktrees/` checkout set `JUNIPER_ROOT` and `JUNIPER_E2E_PROJECT_DIR`).

**10. MINOR — The verbatim fix list keeps all 3 MAJOR / 10 MINOR headings but drops sub-fixes.**
- R15A m1's "Also missed" forms (`cd ROOT` then relative `rm`; a function piped to `xargs rm`; heredoc to `python3 -`; the experiment stack's `find "${RUN_DIR}" … -delete`); R15A m2 body line 66 "writes or deletes"; R15B n3 "drop `DOCKER_CONTEXT`"; R15C M1 `pr_addendum_ml.md`:11's "now leads", and the PLAN step should also "read every canopy merge since the pin"; R15C m1 gaps "in the docstring and the PR body"; R15C NIT "the pinned command has no `--fetch`"; R15D NIT 3 (a delta that deletes the version heading passes `check`).

**11. MINOR — "What moved" misses deploy's two new compose tests.**
- deploy main added `tests/test_compose_data_egress.py` and `tests/test_compose_metrics_subnet_alignment.py`, which read `docker-compose.yml` (a 2b upload path). The 2b worktree (base `d589dd95`) lacks them, so the delta-route re-run won't exercise them locally.

**12. MINOR — Other traps dropped.**
- The trio cascor's "fixture 2/68/2" (09-23 E2E handoff :130) — a cheap check nothing wrote it.
- LFS pointers required for PNGs in signed API commits (`…queue-drained…md`:108).
- The full canopy test recipe (`src/tests/{unit,regression,contract,performance}/`, `--timeout=60`, `LIBTORCH= LD_LIBRARY_PATH=`).

**13. MINOR — The owner's sweeper answer's scope is broadened.** Ledger item 15 and A's predecessor record that the question named data#428, ml#2032, ml#2059 and canopy#678, and "#676 is covered only by the pass's pattern". The draft states it as a general rule, and X1 leans on it for the Y2 PRs.

**14. NIT.**
- C2 "or accepts the gap" — "Accept the gap" is already option 4 in the §4.3 note.
- X10 is item 20 in § F, not § B.
- The pacer's "stale timeout" dropped; the rejected MEMORY digest move dropped.
- §11.4's order (wave 3 after wave 2) not restated.
- X1 omits R15D's other two consequences.
- `handoff_v4.md`:34–35 "truthful reason" / "no client release" dropped.
- A's predecessor's "check canopy's main-verify run on #684" dropped — checked: Post-Merge Main Verification passed on `f2147403`, so CLOSED.

## Coverage table

| Source | Examined | Carried | Dropped | Changed |
|---|---|---|---|---|
| A's predecessor (`…phase9-landed…followup-684.md`) | ~48 | ~40 | 6 (main-verify check — closed; `--allow-shape` method; squash-setting names; §4.9 routing; "grep finds none"; memory STATE block) | 2 (sweeper scope; O9 source) |
| B's predecessor (`…y2-wave2-round-15-fix-pass.md`) | ~55 | ~45 | 7 (#3; old scratchpad path; `process_cleanup.py`; intent-to-add; #183/#184 descriptions; MAJOR/MINOR/NIT tally; "proven no-op") | 3 (drafts → X1, correct; `values.yaml`, correct; subshell → `cd`, breaks) |
| C's predecessor (`…cleanup-done…owner-calls-remain.md`) | ~35 | ~29 | 5 (containers-session scope, moot; 3 verification commands; upstream facts the §4.3 note still holds) | 2 (claims-terms pointer, equivalent; C2 wording) |
| Ledger Phase 9 items 0–17 | 18 items / ~40 sub-bullets | 18/18 items | 4 sub-bullets (item 13's gaps and item 15's evidence survive only via the "ledger is authoritative" pointer) | item 15's list is incomplete in the source (finding 1) |
| `…phase9-cuts-reviewed…f058-filed.md` (09-23) | 6 items + 12 facts | items 1–2 CLOSED (verified), 3–6 carried | 5 (pacer detail, digest move, 2/68/2, `df -i`, f055 log check) | 0 |
| `…four-rulings-shipped…md` + `…queue-drained…md` | ~25 | ~18 | 7 (retention decision, HF_TOKEN, egress rule, LFS, snapshot scan, glob-redirect shape, 3 verification commands) | 0 |
| `S/main/PLAN.md` + `handoff_v4.md` | pointer targets | PLAN.md content verified; wave 3/X10/owner-gated carried | 2 details; known limitations by pointer only | 0 |
| R15A–D | 3 MAJOR, 10 MINOR, ~20 NIT | all headings (fix-list `diff` empty) | ~8 sub-fixes (finding 10) | 2 flagged overtaken (correct) |

## Could not check

- PyPI timestamps for juniper-data 0.16.0 (no web access); the GitHub release and its containment of `68c3cd7c` are confirmed.
- Git state inside other juniper-ml worktrees (rule 4) — I relied on shared refs via `name-rev` / `branch --contains` from this worktree. "graceful-sprouting-panda clean" and B's staged/intent-to-add state are unverified.
- Local-only commits cited in ledger Phases 1–8 (only Phase 9's ~60 SHAs were resolved).
- Whether any tokens were rotated; the canopy#683 validation report itself; whether 2b's compose passes deploy's new tests; the trio's state (not probed).

## Housekeeping

- Artifact sha256 at start and end: `8c2fa29042da0c6f0168ad551a7d2009217a520b86a9c16ee21aa58eaf61898a` — unchanged; the `prompts/` copy is byte-identical. All three frozen predecessors equal their live copies.
- One rule breach: two temporary files in the session scratchpad (`draft_fixlist.txt`, `pred_fixlist.txt`) to diff the fix lists — deleted; the other lanes' scratch files were left alone. No repository file modified; `git status` unchanged.
- Git (read-only only): here — `status`, `log`, `hash-object` (no `-w`), `cat-file`, `name-rev`, `merge-base`, `branch --contains`; the reachability script (here and in the canopy primary: `cat-file`, `merge-base`, `branch --contains`, `worktree list`); `--no-optional-locks status` in the Y2 recurrence/deploy worktrees; `name-rev`/`cat-file` in the canopy/cascor/data primaries. GitHub: GET only. No secrets or env values read or printed; ports 8101/8202/8051 untouched.
