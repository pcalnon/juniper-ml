# CI-budget re-evaluation -- consensus round 4, Lane B -- find what the round-3 fixes broke

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2035 at `0ffe15dc`
- **Archived**: the lane's final report, copied verbatim from the session transcript on
  2026-09-23. Nothing below the rule is edited; the reconciliation is the handoff's
  § Validation record 2026-09-22.

---

**Round 4, Lane B: PR #2035 at `0ffe15dc` (the round-3 fixes, `ab434c9b..0ffe15dc`)**

The code fixes work. The rewritten C2 rule does not do what it says: it cannot see the fence the handoff itself cites. Main is identical to `ab434c9b`, and the follow-up reverts nothing. Below, "the handoff" is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`, cited by line at `0ffe15dc`.

### MAJOR

**M1 (action): NON-OWNER 1's C2 rule misses the fence it names, and its acceptance tests cannot notice.** This is the handoff at lines 162–179.
- The handoff justifies the lead-in clause with the SOPS fence, `notes/JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md:115`. I removed that fence pair in `r4b_c2_rule_sim.py --census`. Today's screen reports C2=1; the rule as written reports C2=0.
- Why: the fence holds `cp`, then `# Fill in values`, then `sops …`, then `git add .env.enc`. `cp` and `sops` are not in CODEY, so the line before `git add` counts as "prose". The lead-in clause only protects a command that sits directly under the `:` line.
- Of the 22 fences that open directly under a prose line, the rule cannot see 6. One is the SOPS fence. The other five sit under `**Interface.**` in `notes/JUNIPER_2026-06-25_JUNIPER-ML_AGENT-SUITE-CONVENIENCE-UTILITIES-DESIGN.md` (lines 96, 136, 169, 196, 226). The handoff says the only cost is "one command glued to mid-sentence prose", and that is wrong.
- Every stated control still passes, because the `:` control uses a one-command fence. So someone can meet ACCEPTANCE and still ship this gap.
- The rule also stops counting a prose line plus its glued command when the whole paragraph is duplicated (current screen 1, rule 0). That is the ml#1799 shape.
- What held:
  - The fixtures are unchanged (multiplicity still 2), and three glued commands count 3.
  - #1969 still fires; the line above it is a `# …:` heading.
  - #2007 clears through the skip; its previous line ends "it does not", with no `:`.
  - #1980 clears at all 7 heads, but through the whitespace rule (`git)`), not the skip. The line before it also has no `:`.
- The `(?=\s)` change also drops two real fenced commands: a bare `pytest` (`juniper-ci-tools/README.md:240`) and `python3.14 -m venv` (`notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md:72`).
- **Fix:**
  - Add the SOPS fence, verbatim, as a control, plus a corpus control: remove each of the 22 fence pairs and C2 must fire, apart from an explicit list.
  - Define "prose" positively. For example: the previous line ends mid-sentence (a letter, digit or `,` once trailing `*_\`` is stripped) and has no shell token (` -x`, `--`, `|`, `&gt;`, `$`, `=`, `&amp;&amp;`). Simulated, this misses 0 of the 22, keeps #1969, clears #1980 and #2007, and keeps every fixture. Its trade-off: it fires on a wrapped line that starts a new sentence with a command word.
  - Use `(?=\s|$)` and `python3(\.\d+)?`.
  - Correct the "remaining cost" sentence and how #1980 is explained.

### MINOR

**m1: OWNER DECISION 2 (handoff lines 94–115; the `util/safe_merge.py` dissent at lines 248–265).** Every premise re-derived true (`r4b_owner2_premises.py`):
- Pinned budgets have been raised 7 times and never lowered; on 09-22, 3 were raised and 6 stood.
- The default went 1800 → 900 (`c3cf3951`) and then → 2400 (`27d3fc15`).
- ml and recurrence were raised in `3cab4783` (#1851), the same commit that wrote the "do NOT raise" paragraph.
- In run 34293438446 the span starts at 00:05:45, and `Build and Validate Package` waited 12.0 minutes after that. So the within-span claim holds.
- Four budgets sit at 3300, and all four statements of the owner's ruling limit it to the three raises.

Two imprecisions remain:
- "Both past lowerings went stale within a day" is too strong. The 09-08 lowering pinned two budgets; recurrence's went stale in a day, but deploy's 700 held for 14 days.
- "Though ml's came in the same commit" implies recurrence's raise did not. Both did.

There is also a mild tilt toward HOLD: SHIP's paragraph contains a concession ("though…") and HOLD's contains none. **Fix:** correct both clauses, and either move the concession or give HOLD its own. The WITHDRAWN (2) note would serve: the span cannot separate heavier CI from contention.

**m2: The GIT STATE section (handoff ~lines 286–289) says only 5 lane scripts are tracked** and "everything else there is untracked". `0ffe15dc` tracks 7 files there, including both `round3-fix/` checks. **Fix:** list them.

**m3: PREFLIGHT line 55.** "`git log --oneline -- &lt;this file&gt;` names both" is false from any HEAD other than main. In this worktree it prints only `58a43ec7` (#1866); on `origin/main` it prints `7b226ca0`. **Fix:** add `origin/main`. The anchor on the next line, `&lt;ml#2017 mergeCommit&gt;..origin/main`, is now always non-empty (#2013, #2029, and the follow-up itself). Anchor it on the last commit that touched this file.

**m4: The measurement trap at handoff lines 243–245** says a probe's `measured_at` is "the moment it enumerated". The reprobe sets `measured_at` once, when the script starts. Under the PREFLIGHT's `all`, the soak probe runs after spans, first-pass and alarm, minutes later, so its stamp is early. **Fix:** stamp each probe separately, or say the stamp is exact only when one probe runs.

**m5: Soak probe when every run is in flight** (`r4b_soak_all_in_flight.py`). It still refuses with exit 2, which is correct, but the message "no soak check-runs found" is false: the line above it prints "in flight: N". A head with no soak check-run yet is counted nowhere. No quoted count moves: the 00:33 run had 210 check-runs, 13 unreadable (all cancelled) and exited 0, so nothing was in flight. **Fix:** say "no COMPLETED soak check-runs (N in flight)".

**m6: The two round-3 checks.**
- `check_soak_in_flight.py` passes, and its control fails for the right reason (the lost-log refusal), though it only checks that the message starts with "UNMEASURABLE".
- `check_first_pass_window.py` passes (juniper-deploy, 6 PRs: window #223–#228), but it only checks that a window exists. A wrong window, reversed or constant, would pass. On the no-healthy-head branch the probe raises before the check can read the row, so the other changed branch is never tested.
- The probe prints "listed in the JSON" even when `--json` is not given.
- **Fix:** assert `window == f"#{min}-#{max}"`, add a stubbed no-healthy-head case, and match the control's message exactly.

**m7:** The Round 4 line (handoff line 1052) says "completed before the follow-up merges". That is the same shape as the #2017 merge that the new trap forbids, and nothing enforces it. **Fix:** word it so it stays true if the PR merges first.

**m8:** Round 3's M5 (the #2017 PR body) was fixed on GitHub after the merge, but it is missing from "Corrections from consensus round 3". **Fix:** add one bullet.

### Verified clean
- **Watcher:** shellcheck 0.11.0 is clean. I drove a byte-identical copy with a fake waiter:
  - stderr holding only the budget line, empty stderr, and multi-line stderr each print one line;
  - PROBE-ERROR then TIMEOUT exits 2, TIMEOUT then PROBE-ERROR exits 2, and TIMEOUT then DONE exits 1.
- **Watcher on real PRs:**
  - #2017 prints DONE and exits 0.
  - `juniper-nonexistent-repo:1` prints PROBE-ERROR on one line with the cause visible, and exits 2.
  - `PER_PR_TIMEOUT=1` on #2033, then the nonexistent repo, exits 2.
- **Replay fetch:** `git fetch origin pull/&lt;N&gt;/head` reaches all 33 flagged heads. HEAD^1 is usable because the soak job checks out with `fetch-depth: 0`.
- **PREFLIGHT:** the `S=&lt;dir&gt;; python3 …` form works, and the exit-2 legend matches `main()`.
- **GIT STATE and Validation record:**
  - The 15 modified tracked files are byte-identical to `0ffe15dc`.
  - The local `r2a_spans.py` (`686c877f`) differs from main's (`42c3873c`), as stated.
  - All 17 of #2017's required checks were green before 01:17:13Z.
- **Item 6:** #2029 and #2013 touch none of the 9 files. `6f17aea5`'s version of `r2a_spans.py` is intact, and the diff touches exactly the 9 files it lists.

### Every round-3 finding
- **Lane B:**
  - FIXED: M1, M3, M4, m1(a–d), m2 (including the exit precedence), m3 (fetch verified), m4, m5.
  - M2: FIXED in the text, but it does not work (my M1).
  - M5: FIXED on GitHub, NOT RECORDED in the handoff.
  - M6: RECORDED.
  - The round-2 leftovers (the `sys.modules` mutation, the scratch-only 857/733 readings): ACCEPTED, and recorded.
- **Lane A:** MAJORs 1–3 and MINORs 4–6 are all FIXED.
- **Rubric:** all 7 findings FIXED.

### Verdicts
- **Code: SHIP.** m5 and m6 are polish.
- **Docs: FIX-FIRST** on M1; m1–m4, m7 and m8 are wording.

Round 4 changes a NUMBER / DISPOSITION / ACTION: yes -- ACTION (NON-OWNER 1's C2 rule and its acceptance controls must change, because the rule cannot see 6 of the 22 fences, including the SOPS fence it cites); no number or disposition changes.

**Created**, all untracked, under `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round4-laneB/`:
- `r4b_c2_rule_sim.py`
- `r4b_soak_all_in_flight.py`
- `r4b_owner2_premises.py`
- `r4b_merge_state_checks.py`
- `wait_for_checks.py` (a fake waiter)
- `fakebin/gh` (a fake `gh`)
- `wh/watch_copy.bash` (byte-identical copy of the watcher)

Also `r4b_waiter.json` in the session scratchpad.

**Worktrees:** none. The fetches (two base SHAs, and `pull/&lt;N&gt;/head` for the 10 flagged PRs) added objects and wrote `FETCH_HEAD` only. Nothing tracked changed. I ran one trivial heredoc by mistake; it printed a string and nothing else. About 50 REST calls in total.
