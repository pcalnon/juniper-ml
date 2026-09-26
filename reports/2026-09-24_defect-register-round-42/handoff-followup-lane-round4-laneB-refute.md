<!-- Archived verbatim 2026-09-24 from subagent acf72f155fbceaf05 of session bc31e993 (final message). -->

**v4 is not ready to publish.** Its Step 0 fallback can hand this lane's work to the register lane's handoff (MEDIUM-1). Two LOW defects should be fixed in the same edit.

I found 1 MEDIUM, 6 LOW and 4 NIT problems.

v4 is `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`; its sha256 `11ddd865…` is unchanged. The register lane's handoff is `fizzy-hugging-dream/…/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`. I edited nothing, and `hvI/` is pruned.

## Findings

**MEDIUM-1. The Step 0 fallback hands this lane the other lane's instructions (L25).**
- **Text:** "If `[24f8d8]` is gone: use the consolidated handoff if it is on `main`, else the register lane's own handoff named above."
- **Problem:** this contradicts L11, "Until then, this file governs this lane's work".
- **What that handoff says:**
  - its goal is "Continue defect-register round 42";
  - it says "**Never merge** another lane's PRs: data#440, cascor#689, cascor#690";
  - it tells its reader to ship `fizzy-hugging-dream`'s files and finish the data branch that L137 fences off.
- **Likely path:** `[24f8d8]` has already written that handoff (00:25Z).
- **Replacement:** "If `[24f8d8]` is gone, find its successor in `ListAgents` (its handoff tells it to message `[042116]`) and do the same with it. If there is none, this file governs this lane until the consolidated handoff is on `main`. The register lane's handoff is its record, not your instructions. Ask the user who consolidates."

**LOW-1. The serve script can make a fixed #690 look broken (L65-68, the script).**
- **Rate limiter:** it leaves juniper-data's limiter on (60/min, `settings.py:231`).
  - The implementer's run "hit juniper-data's rate limit (429) partway through" (`cascor690-fixup-implementation-report.md:45`).
  - A 429 prints as a plain fetch failure, which is what the old misparse looks like.
- **Inherited settings:** it keeps any `JUNIPER_DATA_CSV_IMPORT_ALLOW_TRUNCATION` and `…_MAX_BYTES` from the shell.
- **Two harnesses:** "the `realjd` harness" is ambiguous. `…_cascor690_bool_stance_realjd_probe.py` also needs a server.
- **Recipe:** it omits the `fetch` the author ran first.
- **Fix:** export `JUNIPER_DATA_RATE_LIMIT_ENABLED=false`, unset both CSV variables, write "both `realjd` harnesses", and fetch before `archive`.

**LOW-2. The probe description invites unsafe runs (L16).**
- "some write under a `work/` or `out/` directory beside themselves" is incomplete:
  - `cascor688-v688/make_nv1_tree.py:8` runs `shutil.rmtree(sys.argv[2], ignore_errors=True)`, in the directory OPEN 1 points at;
  - `fix_probe_pairs.py` rewrites the archived `compare_probe.py` in the CWD.
- **Append:** "Treat them as evidence: read each one's arguments first, and pass only fresh scratch paths (`make_nv1_tree.py` deletes its second)."

**LOW-3. The stale-comment NIT is dropped again (a round-1 regression).** It was v3 L80 (`canopy685-implementation-report.md:69`). Round-1 lane B called it "never routed", and v3 routed it. It is now in neither v4 nor the register lane's handoff. Restore it under "Canopy ledger".

**LOW-4. The APD-ECO-013 condition is stale (L128).** The register lane's handoff (`:157`) holds the row open "until data#440 and cascor#689 merge, #685's validation holds, and the peer's F2 and F3 are fixed". v4 should say so.

**LOW-5. Two amputations have consequences.**
- **v3 L10's "and again before each OPEN item" is gone.** Nothing re-checks whether the consolidated handoff has reached `main`.
- **v3 L174 lost "lacks the two probe-script commits" and "See the stray branches".** A #685 validator using that worktree would run the pre-edit probe, and the cleanup section no longer names `pr-63` or `pr-683`.

**LOW-6. Git status names three scripts only by role (L222).**
- The filename rule is mandatory, and v3 named all three: `2026-09-24_copy_followup_lane_probe_scripts.py`, `…_archive_followup_handoff_validation.py` and `…_open_followup_handoff_pr.py`.
- Nothing says what to do if the PR list prints `[]`.
- The counts are right: 92 untracked files (1 + 19 + 9 + 63), nothing staged or modified, and HEAD = `origin/main` = `5af9d722`.

**NITs**
- **L68:** "tested 2026-09-24" should be "2026-09-25 00:43Z".
- **F9:** cascor squashes with `COMMIT_MESSAGES`, so `97341680`'s "4001 close" reaches `main` anyway. Correct it in the fixup's commit body, and report it as residue.
- **L51:** the verbatim answer is "Keep while fetched splits stay (Recommended)" (transcript line 4260).
- **L169:** this round the sandbox refused a `for` loop with a variable inside a `gh` argument.

## Amputation audit

Every other removed v3 line survives:
- **Release facts:** the lock, cap and order lines moved intact (L147-157).
- **F2, F4, F10:** every "how" is kept.
- **Merged table:**
  - #688's findings and resolution are implied by "supersedes" and recorded in `cascor688-implementation-report.md`;
  - #685's squash-tree equality is moot, because L70 names `dc5ea02e`.
- **Canopy anchors:** dropping the `7ab994e5` pin is harmless. Canopy `main` still holds `:8381`, `:8410` and `:42`, and cascor still holds `:4766` and `:4841`.

**Length:** the goal span went from 1,755 to 1,695 words, and the file grew (3,140 → 3,185).

## Round-3 disposition

✓ fixed, ◐ flawed.

| Finding | v4 line | Status |
|---|---|---|
| A LOW-1 ledger | 138-145 | ✓ (attribution verified) |
| A LOW-2 `big.csv` | 66-67 | ✓ |
| A LOW-3 `pr-683` push | 118 | ✓ |
| A NIT-1 sandbox | 169-175 | ✓ (now too narrow) |
| A NIT-2 date | 131 | ✓ (recurs at L68) |
| A NIT-3 trigger / fallback | 9, 12, 25 | ◐ MEDIUM-1 |
| A NIT-4 signing | 51 | ✓ |
| B MEDIUM-1 serve | 66-68 | ◐ LOW-1 |
| B LOW-1 #690 target | 69, 95 | ✓ |
| B LOW-2 path + PR number | 9, 23 | ✓ |
| B LOW-3 README / opener | 16, 136, 217 | ◐ LOW-6 |
| B LOW-4 spy marking | 82 | ✓ |
| B LOW-5 dead scratchpad | 16 | ◐ LOW-2 |
| B NITs: signing, date, `ci.yml:287` | 51, 131, 82 | ✓ |
| B NIT F9 | 87 | ◐ |
| B NIT "owner's ruling" | 51 | ✓ |
| B length | 19-120 | ◐ |

Nothing is ✗.

## Safety

Nothing leads to a release, a deploy gate, a cleanup or a stray-branch deletion. Merges stay gated (L26), and the serve script refuses any tree with a `.git` or `.env`. The remaining risks are MEDIUM-1 and LOW-2.

**Verdict:** not ready. MEDIUM-1 blocks it; fix LOW-1 and LOW-2 in the same edit.
