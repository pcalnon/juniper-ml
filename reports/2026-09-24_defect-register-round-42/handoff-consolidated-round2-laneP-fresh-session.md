<!-- Archived verbatim 2026-09-24 from subagent ae082bd285e35f93b of session 2fba4397 (final message). -->

**VERDICT: PASS WITH CORRECTIONS.** There are no HIGH findings. Apply the 6 MEDIUM findings before this is used as a first prompt.

**Documents cited.** "L<n>" means line n of the frozen copy.
- **The document under test:** `hc2/consolidated_r2_frozen.md` (sha256 `79c0abb4b7dbdf15`, checked before and after this run). It is byte-identical to the untracked `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md` in `fizzy-hugging-dream`.
- **The predecessor lane:** `reports/2026-09-24_defect-register-round-42/handoff-consolidated-round1-laneP-fresh-session.md` (called "r1-P" below). I also read r1's diff against `hc1/consolidated_r1_frozen.md`.
- **Document 1:** `HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`, identical to `hc2/doc1_r2_frozen.md`.
- **Document 2:** `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, read from `origin/docs/handoff-round42-followup-lane` (sha `4ebd0143…`, identical to `hc2/doc2_peer_final_2e4917c2.md`).
- **Other files read:**
  - #2089's `util/ad-hoc/2026-09-24_round42_probes/README.md`, from its branch;
  - `data438-fixforward-pr-draft.md`;
  - `handoff-2fba4397-round3-laneF-reprobe.md`;
  - the author's tmpfs note `hc1/pending_corrections.md`, read only for knowledge that exists nowhere else.
- **Tools read:** the opener, the archiver (fizzy's copy and `origin/main`'s), `util/open_signed_pr.py`, `util/push_signed_commit.py`, `util/safe_merge.py`, `juniper-ci-tools/juniper_ci_tools/symbol_loss_check.py`, and #2097's `2026-09-24_serve_scratch_juniper_data.bash`.

## Findings

### MEDIUM

**M1. First action 2 can stall the consolidation PR, gives "silent" no time limit, and treats "nothing in flight" as given without a check.**
- **Quotes:**
  - L45: "Ask whether it is still doing any item or still writes in its worktree, and that it launch and ship nothing more. Start no item it names."
  - L46: "ask the owner to close it first: with nothing in flight, that is safe."
  - L70: "**In flight:** nothing."
- **What goes wrong:**
  - Suppose `[24f8d8]` replies that it was about to open the consolidation PR. The successor has just told it to ship nothing, and may not itself start an item `[24f8d8]` names. Then nobody opens the PR, and a document-2 successor waits for it (L53).
  - r1-P M2's replacement asked "(1) whether it will open the consolidation PR, and when". r2 dropped that question.
  - "Silent" has no time limit.
  - L45 tells the successor to announce "your lane, after a split" one step before First action 3 finds out whether there is a split.
  - "With nothing in flight, that is safe" rests on the file's own claim, and at 02:10Z that claim was false. This round's lanes `aac2e54444043de31`, `a8db50d2bc385a75e` and `ae082bd285e35f93b` were writing transcripts at 02:29–02:31Z.
  - Closing a session kills its subagents (`reference_subagents_killed_by_session_limit_resume_with_sendmessage.md`), so an unfinished validation round would be lost.
- **Replace L45-L46 with:**
  - "- **Listed:** message it first, with your name and `[ref]`. Say you are its successor; the lane split is settled at First action 3. Ask (1) whether it has opened, or will open, the consolidation PR, and when; (2) whether any of its subagents is still running; (3) whether it still writes in its worktree. If it will open the PR, let it, and wait for the PR. Otherwise ask it to launch and ship nothing more. Start no item it says it is doing."
  - "- **Listed but silent** (no reply by your next turn): carry on. Before asking the owner to close it (needed only to ship its files yourself), check that no subagent of it is running: `ls -lt /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/ | head -4` must show no transcript written in the last 15 minutes."

**M2. Lane R's inputs exist only in fizzy, and the document cites them by relative path.** r1-P L8 was applied to Lane F's #2097 files, but not to Lane R's.
- **Quotes:**
  - L72: "archived as `reports/…/data438-fixforward-round1-fix-report.md`"
  - L327: "The final draft is `reports/…/data438-fixforward-pr-draft.md`"
  - L581: "Check it against both round-1 reports and the executor's disposition report"
  - L216 cites `owner-ruling-key-leaks-verbatim.md`; L243 and L248 cite `handoff-2fba4397-round{2,3}-laneF-reprobe.md`.
- **Evidence:** my `paths_probe.py` found none of the following on `origin/main`, on #2097's branch or on #2089's branch: `data438-fixforward-round1-{laneA-reprobe,laneB-refute,fix-report}.md`, `data438-fixforward-pr-draft.md`, `owner-ruling-key-leaks-verbatim.md`, every `handoff-2fba4397-*` report, and the stall probe. They exist only untracked in fizzy.
- **What goes wrong:** every one of these paths is missing from the successor's own worktree. Work 1's lanes need them first, and so does the `gh pr create --body-file` step.
- **Add after L185:** "**Until the consolidation PR merges, these files exist ONLY in fizzy.** Read them with `cat`, and give your lanes their paths, as `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/<path>`. Once the PR is open, `git show origin/docs/handoff-round42-consolidated:<path>` also works. #2089's probes can be read the same way from `origin/chore/round42-probe-provenance-session-2fba4397`."

**M3. The "ship them yourself" fallback cannot be run as written from another worktree, and it misdescribes the opener.**
- **Quote, L186:** "run `util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py` … refuses … a stale base (…; a file that `origin/main` already holds is refused)".
- **What goes wrong:**
  - The opener exists only untracked in fizzy. It sets `REPO = Path(__file__).resolve().parents[2]`, so it works only when run by absolute path in fizzy. A copy run from another worktree reports every file as `missing`.
  - Its four required flags are not given. No title, commit headline or PR body is drafted anywhere: at 02:32Z, `hc1/dry_body.md` and `hc1/dry_commit_body.txt` hold only "placeholder".
  - The refusal is misdescribed. The code refuses a file only when the copy at fizzy's HEAD differs from `origin/main`'s. The archiver and the extractor are both on `main`, and both pass.
- **My dry run** (from fizzy): 22 files, base `main @ 3055a892`, "(nothing written)", exit 0.
- **Replace L186's first sentence with:** "run the opener from fizzy BY ABSOLUTE PATH, dry run first: `python3 /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py --title '<title>' --message '<headline>' --commit-body-file <f> --body-file <f> --dry-run`, then again without `--dry-run`. It ships fizzy's files, because it finds the repo from its own location. It refuses a missing file, any of #2089's paths, a file whose copy at fizzy's HEAD differs from `origin/main`'s, any path an open juniper-ml PR carries, and the owner's email address. Write the title and both bodies yourself, and list every shipped file by name (Appendix G)."

**M4. The archiver in the successor's worktree lacks the 15 `MISSING` entries that ride the consolidation PR.**
- **Quote, L124:** "Add your session's full UUID … to `SESSION_IDS`, and each report to `MISSING`."
- **Evidence:** fizzy's modified copy adds 15 entries after `origin/main`'s L113: the data438 fix-forward's round 1 and its fix report, `handoff-2fba4397` rounds 1-3, and `handoff-consolidated` round 1. The opener always ships fizzy's copy.
- **What goes wrong:** archiving Work 1's or Work 5's reports edits the same insertion point in a second copy of the file.
  - If the successor's copy reaches `main` first, the opener refuses fizzy's copy as a stale base.
  - If the consolidation PR is already open, whichever PR merges second conflicts. A single-parent signed commit cannot merge that away (L94).
- **Append to L124:** "Until the consolidation PR merges, fizzy holds an unshipped copy of this file with 15 more `MISSING` entries. Archive nothing into another juniper-ml PR until it merges. Or build your entries on the PR head's copy (L92), and ship them as a fixup on that PR."

**M5. The closes PR has no validation plan, and the sweeper will merge it as soon as it is green.**
- **Quotes:**
  - L81: "opened early: its gates are on ROWS, not on the PR"
  - L594: "Open it early."
  - L39: "When a validated merge matters, validate BEFORE …; otherwise, validate after merge and fix forward."
- **What goes wrong:** every earlier register PR this round was validated. #2074 and #2080 were validated after merge, and both were refuted. #2088 was validated in two rounds before it opened (L60, L501). The register also carries the status-list trap (L110). The successor has to guess, and a PR opened early merges unvalidated.
- **Add to Appendix J, Work 6** (the author's call; suggested): "Validate it with two lanes: A re-derives every filed row and residue item from source at `main`, and B refutes. This PR files rows OPEN and closes none, so validate after it merges and fix forward. A PR that CLOSES a row is validated before it reaches a PR branch."

**M6. The probes behind the validation reports that the consolidation PR ships exist only on tmpfs.**
- **Quotes:**
  - L181: "the `handoff-2fba4397-round{1,2,3}-*` and `handoff-consolidated-*` validation reports"
  - Appendix A's (a) and (b) rest on `handoff-2fba4397-round{2,3}-laneF-reprobe.md` (L243, L248).
- **Evidence:**
  - 55 finished-round probes sit only in the author's scratchpad: `hv1/laneF` (12), `hv2/laneF2` (14), `hv3/laneD` (18) and `hc1/laneF` (11). `hv3/laneD` includes `probe_{data,cascor,primer}.py`, which measured Appendix A's (a) and (b). This round's `hc2/laneF` adds 16.
  - The reports cite `surrogate_422_probe.py`, `surrogate_422_layers.py`, `real_data_surrogate.py`, `idem_surrogate.py` and `probe_pairs.py` by name.
  - Neither the opener's `FILES` and `GLOBS` nor #2089 carries any of them.
  - This is the case `Juniper/CLAUDE.md`'s script-placement rule forbids, and the reason #2081 and #2089 exist.
- **What goes wrong:** once tmpfs is reaped, Work 8 starts from nothing, and the shipped reports cite scripts nobody can re-run.
- **Fix before handing off:**
  - Copy them to a directory the opener accepts, for example `util/ad-hoc/2026-09-24_round42_handoff_probes/<lane>/`. The opener refuses `2026-09-24_round42_probes/` (`PR2089`).
  - Ship them in a separate PR: probes drew CodeQL highs on both #2089 and #2097, and the consolidation PR must land early.
  - Name them in Appendix A. If this is not done, say in Appendix A that they are tmpfs-only.

### LOW

- **L1. MOVED: #2097 and #2089 are now `BEHIND`, not `BLOCKED`.**
  - Quotes: L154 and L156 "OPEN, BLOCKED (CodeQL) at writing"; L66 "both BLOCKED by CodeQL".
  - `mergeStateStatus` shows BEHIND once `main` moves, which hides the CodeQL failure. #2098 merged at 01:47:48Z and #2090 at 02:02:04Z, so the claim was probably already stale at 02:10Z.
  - Replace both comments with: "# OPEN; BLOCKED or BEHIND: CodeQL fails either way (next line), and update-branch does not clear it".
- **L2. Work 8's launchers do not run the locked pair.**
  - The serve script runs JuniperData's python (fastapi 0.137.0, starlette 0.50.0). The cascor recipe (L602) names no environment, and JuniperCascor1 has 0.137.0 / 1.0.0. L247 says "Re-measure it on the locked pair" (0.141.1 / 1.6.0).
  - I ran round 3's three requests in-process on the serve script's interpreter (`probe_data_servescript_env.py`): the control gave 422, and both surrogate rows gave 400 `{"detail":"Invalid request parameters"}`. That is round 3's locked-pair result, so data's half is unaffected.
  - Add to Work 8: "The serve script runs fastapi 0.137.0 / starlette 0.50.0; record the pair you measured on. For cascor's locked pair, build a venv from `requirements-cpu.lock` (it pulls torch), or file cascor's half as measured in-process on 0.137.0 / 1.0.0."
- **L3. Lane B's probes cannot run as preserved** (L360: "lane B's probes, against `d1c66a11` and the new head").
  - #2089's `data438-fixforward-round1-laneB/common.py` pins `S` to `…/2fba4397…/scratchpad/r42d/laneB`.
  - It starts every server through `S/scripts/run_in_tree.bash`, which #2089 does not keep. That script survives only on tmpfs, and its `head` and `main` trees are already gone.
  - Add: "Re-point `common.py`'s `S` at your lane's scratch, and build `head` and `main` there with `git archive`. Recreate `scripts/run_in_tree.bash`: it `cd`s into the tree, sets `PYTHONPATH` and `JUNIPER_DATA_API_KEYS=""`, checks that `juniper_data` imports from the tree, and execs JuniperData's python."
- **L4. If round 2 refutes, the new executor has no brief to start from** (L585). r2 removed the pointer that r1-P L3 relied on.
  - Add: "Model its brief on the first `user` record (19:37:50Z) of `/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl`: an unsigned local scratch commit, then a whole-file signed upload, the trailers, and no PR. Extract it with a script, never with `splitlines()`."
- **L5. r1-P L6 is not applied: L70's "In flight: nothing"** is false while a validation round runs (see M1).
  - Add: "If the last round's reports are not archived (L168's count), find the transcripts with `grep -l consolidated_r /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/*.jsonl`, and archive them."
- **L6. Work 5's fix-forward has nowhere to go once the closes PR has merged.**
  - L592: "Its fix-forward either merges before the closes PR opens, or rides in it." Work 6 opens early and the sweeper merges it, so both options can be gone.
  - Add: "…or, once the closes PR has merged, in the ONE register/primer follow-up from fresh `main`."
- **L7. Both data PRs edit `CHANGELOG.md` `[Unreleased]`: Lane F's F3/F5 PR and Lane R's fix-forward.**
  - L369 ("…edits data's `CHANGELOG.md`. Lane F stays out of those.") does not say whether Lane F may add an entry.
  - Add: "Open Lane F's data PR only after the fix-forward merges, or build it on the fix-forward's head; update-branch before any merge."
- **L8. The older "dirty" worktrees hold uncommitted code.**
  - cascor `c6c848f2`: `src/api/security.py`.
  - data `tri-state-allow-truncation`: 16 entries, including `MM AGENTS.md` and `CHANGELOG.md`.
  - cascor `tri-state-truncation-prose`: 5 entries, including `src/api/lifecycle/manager.py`.
  - L480's `worktree remove` refuses a dirty tree, and nothing forbids `--force`. Add: "Diff each entry against the merged content of its PR, and name what removal would lose before you ask. Never `--force`."
- **L9. `util/safe_merge.py` cannot do everything the document asks of it.**
  - It merges only with `--execute`; without it, it is a dry run.
  - It has no subject or body option, so Appendix C's "hand-write the body" (L325) cannot go through it.
  - Add to L40: "`python3 util/safe_merge.py --repo <repo> --pr <N> --execute`; a hand-written squash body goes only through the curated re-arm (L104)."
- **L10. "Round 2" means two different things.**
  - L327: "round 2's reports must be added". But the draft already has a "## Round 2" heading at its L64, which is the executor's second fix round.
  - Write instead: "the pre-PR validation round 2's reports (`data438-fixforward-round2-lane{A-reprobe,B-refute}.md`)".
- **L11. No vehicle is named for archived reports** (L583 "archive the reports"; Work 5). Tie this to M4: "a fixup on the consolidation PR while it is open; otherwise the closes PR or its follow-up".
- **L12. #2096's keeper is not told that cascor#690 merged.**
  - L231 records that the fourth canopy item "went stale when #690 merged", but #2096 was written before that merge.
  - L234 sends only #685's validation outcome. Add: "…and tell it that cascor#690 merged at 02:06:36Z (`0fbb447a`), so canopy's copies of the fourth item are now stale."

### NIT

- **N1.** L44: replace "Its header names you" with "`ListAgents`' header line names your own session and `[ref]`".
- **N2.** The canopy-ledger fallback is stated two ways. L147 says "or to the owner"; L234 says "or record it in the ledger yourself". Pick one.
- **N3.** L274 tags #2097's CodeQL question [R], but #2097 is Lane F's PR. Tag it [R/F], or write "Lane R asks for both".
- **N4.** L282: MEMORY.md is not a question; mark it FYI. L285 never defines D-B.
- **N5.** L454's scratch-root recipe lacks the `fetch origin main` that L398 has. The shared clones' `origin/main` are current today (`0fbb447a`, `dc5ea02e`, `26491531`), but will fall behind.
- **N6.** The `const:SESSIONS` waiver (L186) is not strictly needed. `symbol_loss_check.py:80` treats a lost `const` as advisory only, and `:418` scans every line, so the waiver need not be in the last paragraph. Keeping it inside the attribution trailer block satisfies both readings.
- **N7.** L163 omits canopy, although L68 claims canopy has no open PR. Add `gh pr list --repo pcalnon/juniper-canopy --state open`, which is empty now.
- **N8.** L168's "+3 per later validation round" assumes three lanes per round. Document 1's round 3 had two.
- **N9.** L169 runs a test without the empty Sentry DSNs that L131 requires for every test run. It is harmless, since the test only reads source; either set them or exempt the line.
- **N10.** Length: the Goal (L21-L86) is 1,337 words, against the ~1,200 target. The whole document is 10,195 words, up from r1's 7,476. Appendix I (565 words) serves validators, not the successor.

## Per-step table

| Step | Verdict | Why |
|---|---|---|
| First action 1 | EXECUTABLE | All 20 lines ran. L152 prints nothing in fizzy, as expected, and is correct for a fresh worktree. L154 and L156 have moved (L1). |
| First action 2 | AMBIGUOUS | The "Listed" branch can stall the consolidation PR, "silent" has no time limit, and "nothing in flight" is never checked (M1). |
| First action 3 | EXECUTABLE | Document 2's Step 0 (its L21-L28) will message you. L4 gives the path to send, and L48 reconciles which document governs. |
| First action 4 | EXECUTABLE | About 11 questions. MEMORY.md is not one (N4). |
| First action 5 | AMBIGUOUS | The fallback's relative path and flags are missing (M3). CodeQL is gated on the owner by design. |
| Work 1 | AMBIGUOUS | Inputs exist only in fizzy (M2). Lane B's probes need adapting (L3). No brief template (L4). "Round 2" is ambiguous (L10). No archive vehicle (L11). |
| Work 2 | EXECUTABLE | The #2097 `git show` recipe works. All five harnesses and the serve script are on `origin/docs/handoff-round42-followup-lane`. |
| Work 3 | EXECUTABLE | — |
| Work 4 | EXECUTABLE | Both data PRs edit data's `CHANGELOG.md` (L7). |
| Work 5 | EXECUTABLE | `990ef3f9..2439d049` is reachable, and the diff lists exactly 7 `util/ad-hoc` files. See L6. |
| Work 6 | AMBIGUOUS | No validation plan (M5). |
| Work 7 | EXECUTABLE | Anchors `:205-209` and `:289` hold at `main` (see N5). |
| Work 8 | EXECUTABLE | The launch environments differ from the locked pair (L2), and the probes are tmpfs-only (M6). |
| Work 9 | EXECUTABLE | Live bodies match: #2080 L19, L23 (the table header), L41, L65 and L69; #2088 L47. |
| Work 10 | EXECUTABLE | See N3 and N4. |

## Verification commands (run 02:11–02:21Z from fizzy)

| Line | Comment | Actual | Match | From another worktree |
|---|---|---|---|---|
| L152 ancestry | must print | nothing, exit 1 (fizzy HEAD `ee0b9382` sits on `df21367d`) | expected here | right: the shared checkout's `main` is `09f2e677`, after `5af9d722` |
| L153 consolidation PR | this file's PR | `[]` | yes | yes |
| L154 #2097 | OPEN, BLOCKED | OPEN `2e4917c2`, **BEHIND**, not armed | MOVED (L1) | yes |
| L155 #2097 CodeQL | fail | `CodeQL fail` (run 107905207679: 45 new, 3 high, at the stated lines) | yes | yes |
| L156 #2089 | OPEN, BLOCKED | OPEN `a2fa3ad8`, **BEHIND** | MOVED (L1) | yes |
| L157 GraphQL | all MERGED, with the stated SHAs | exactly those; #690 auto-merge enabled 01:57:06Z | yes | yes |
| L158 data branch | `94ce8b1f…` | `94ce8b1fa8e2…` (verified, parent `d1c66a11`, 12 files) | yes | yes |
| L159 data branch PRs | none | empty | yes | yes |
| L160 data worktree | in sync, clean | `## fix/…round4-followups...origin/…` | yes | yes (a juniper-data path, so allowed) |
| L161 document 1 | its first lines | title and "From:" line | yes | yes (`cat`) |
| L162 #2089 CodeQL | fail | `CodeQL fail` (33 new, 4 high, `stripe_probe.py` :139, :148, :177, :205) | yes | yes |
| L163 open data and cascor PRs | none | none (canopy also none) | yes | yes |
| L164 register | 136 / 100 / 36 | `136 rows \| 100 fixed \| 36 open` | yes | yes |
| L165 crosscheck | AGREE | AGREE | yes | yes |
| L166 archiver OK count | positive | 48 | yes | 34 when `main`'s copy runs in a scratch root |
| L167 archiver errors | 0 | 0 | yes | 0 (same emulation) |
| L168 report count | 16 | 16 | yes | yes (absolute path) |
| L169 fork-drift test | "Ran 11 … OK (skipped=3)"; FORCE_LOCAL "Ran 11 … OK" | both, as stated | yes | yes |
| L170 worktrees | six plus one | 7 | yes | yes |
| L171 `/tmp` inodes | none (L132 says 83%) | 82% | yes | yes |

**Other live state.** cascor's post-merge CI on `0fbb447a` is now all green; L62 said "still running". It MOVED, and the instructions still hold. `origin/main` is now `3055a892`.

**The opener, `--dry-run` from fizzy.** 22 files, base `3055a892`, no open-PR collision, "(nothing written)", exit 0. Scratch `commit_body.txt` and `pr_body.md` were used as inputs.

**Refusals.** One: a `for` loop running `sed` with a computed program ("too complex to verify"), which L140 predicts. Everything else ran:
- `git -C` into the juniper-data, juniper-cascor and juniper-canopy clones and worktrees;
- `git show` and `git ls-tree` in fizzy;
- `gh api`.

## Round-1 disposition (r1-P)

| r1-P | r2 |
|---|---|
| H1 | APPLIED (L160 uses `--no-optional-locks`); moot now that the executor has finished |
| M1 | SUPERSEDED: the executor finished, and First action 2 was rewritten. It has a new gap (M1 above). |
| M2 | PARTLY APPLIED (L45-L48, L186). The question "will you open the consolidation PR" was dropped (M1 above). |
| M3 | APPLIED (L4) |
| M4 | APPLIED (L51, L154-L155, L276); MOVED to BEHIND (L1) |
| M5 | APPLIED (L152, L166-L167) |
| M6 | APPLIED differently (L75, Work 6 opened early, Appendix J). New gap: M5 above. |
| L1 | APPLIED (L602); the environment is not stated (L2 above) |
| L2 | APPLIED (L607-L608); verified against the live bodies |
| L3 | MOOT; for the relaunch case, see L4 above |
| L4 | APPLIED (L585) |
| L5 | APPLIED (L188, L463) |
| L6 | NOT APPLIED (L5 above) |
| L7 | APPLIED (L254, L270, L272, First action 4) |
| L8 | APPLIED for Lane F only (L389); for Lane R, see M2 above |
| N1-N7, N9 | APPLIED (L14, L169, L590, L40, L98, L44, L157/L163, L115) |
| N8 | NOT APPLIED (N10 above) |

**What I could not verify.** `ListAgents`: ToolSearch returns only SendMessage from a subagent, and I did not call SendMessage. I also could not verify how `[24f8d8]` will answer a successor's message.

**Changed: no repository file.**
- `git fetch origin` in fizzy moved the remote-tracking refs: `origin/main` went from `09f2e677` to `3055a892`, and `origin/docs/k8s-primer` was added.
- The in-process probe imported `juniper_data` from the shared checkout with `-B`. Its `git status --porcelain` stayed empty, and it wrote no logs.
- `hc2/laneP/` keeps five small files: `paths_probe.py`, `wt_state.py`, `probe_data_servescript_env.py`, `commit_body.txt` and `pr_body.md`. They are tmpfs-only, like M6's probes. All extractions are deleted.

Counts: 0 HIGH, 6 MEDIUM, 12 LOW, 10 NIT. Steps: 11 EXECUTABLE, 4 AMBIGUOUS, 0 BLOCKED. Verification lines: 20 run; 17 matched, 1 printed nothing in fizzy as expected, 2 MOVED; none refused.
