<!-- Archived verbatim 2026-09-24 from subagent aeb3e0b56825ec0c0 of session 2fba4397 (final message). -->

VERDICT: PASS WITH CORRECTIONS

Almost every fact in the snapshot reproduces. All 11 verification commands ran exactly as written, every output matched its note, and the sandbox refused none of them. Every PR state, SHA and merge time matched, and every file:line anchor resolved except the two findings below that name their own anchors. The problems are in what a fresh session would do next.

Two HIGH findings need fixing before this is used as a first prompt:
- **H1:** First action 3 sends the new session to a peer session that is itself handing off.
- **H2:** the executor liveness rule reads a live executor as dead, and the recovery step would then put a second executor on the same worktree.

Four MEDIUM findings should also be applied. None needs a factual rewrite.

**Documents cited.** "L<n>" means line n of the snapshot.
- The snapshot: `handoff_session_r2_frozen.md` (sha256 `6822f3ff0402793e…`, verified).
- Its live archive: `HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`.
- The procedure: `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`.
- The round-1 reports: `handoff-2fba4397-round1-laneF-reprobe.md`, `handoff-2fba4397-round1-laneO-amputation.md`, `handoff-2fba4397-round1-laneP-fresh-session.md`.
- The peer's handoff: `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, untracked in worktree `happy-skipping-hollerith`, last modified 00:21Z.
- The predecessor: `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`.
- The register: `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.
- The primer: `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`.

## Per-item table

| Item | First three actions a fresh session takes | Runnable? | Blocker |
|---|---|---|---|
| Verification commands (L113-125) | Run all 11 as written; compare each with its note; compare the `stat` time with the clock | **Yes, all 11, no refusal** (including the `&&` at L117 and the `;` at L123). Results: 13 entries; #2088 MERGED 23:41:16Z `5af9d722`; #2089 OPEN `a2fa3ad8`, BLOCKED; `136 rows \| 100 fixed \| 36 open`; AGREE; 39; `d1c66a11…`; 12 modified files; executor written 00:30:12Z (clock 00:30:19Z); data#440, cascor#689 and #690 open; /tmp inodes 83% | `stat` prints local time and no clock (N2). Nothing checks `ListAgents`, #2089's checks or the peer's PR (H1, H2, M2) |
| First action 2 / In flight 1 (executor `a46e715a6801b98ca`) | `stat` the transcript; read the data branch ref; `git -C <data worktree> status --short` | Yes. Still working at 00:44:52Z, context-compacted at 00:29:28Z, ref `d1c66a11`, 12 files dirty | The 10-minute rule calls a live executor dead (H2). The recovery step names half the brief and misses one state (M1) |
| First action 3 (re-route the peer) | Load `ListAgents`/`SendMessage` via ToolSearch; run `ListAgents`; SendMessage `defect reg [042116]` | Not run (forbidden to me). `ListAgents` does print the caller's own `name [ref]` (transcript, 19:03:13Z) | `[042116]` is handing off, and its own handoff says "Never message it" (H1) |
| First action 4 / Remaining 1 (ship; merge #2089) | `git log HEAD..origin/main -- <paths>`; `open_signed_pr.py --dry-run`; `gh pr checks 2089` | Path checks run: `main`'s copies of both scripts equal HEAD's, and the local archiver is `main` plus 5 new MISSING entries. The opener was not run (forbidden) | The old session is alive and still writing here, and the draft re-copy comes after the executor (M3). #2089's CodeQL FAILED with 4 high alerts (M2). #2089's own files are not excluded from the ship list (L4) |
| Remaining 0 (consolidate) | Look for a consolidated handoff; read the three inputs; wait for the peer's path and PR | All three inputs exist | Nothing says where to look for "that consolidated handoff". The peer's path and PR are routed to a session that will be gone (H1). "had begun" is overstated (L2) |
| Remaining 2 (#2088 delta) | `git diff --stat 990ef3f9 2439d049`; launch two background lanes in one message; add your UUID to `SESSION_IDS` plus the MISSING entries, then `--check` | Yes. `2439d049`'s parent is `990ef3f9` (11 files, +847/-77). The archiver matches the trap (`HEADER` date; the `SESSION_IDS` exit) | No path for the tmpfs venv (N5) |
| Remaining 3 (data fix-forward) | Wait, then read `last_report()`; round-2 lanes on `d1c66a11..<head>`; `gh pr create --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups …` | The `gh` syntax is valid. `open_signed_pr.py --help` confirms it refuses an existing branch (exit 1) | The executor is still running. The PR number goes to `[042116]` (H1). Title and body extraction are unstated (L6) |
| Remaining 4 / Appendix A (closes PR) | Check the gates; confirm the three new ids are free; read `bytes-compare-ml2086-data440-cascor689-validation.md` | Yes. Gates are unmet, correctly: #690 OPEN `78e99414`, canopy#685 merged `dc5ea02e` unvalidated, the data fix-forward not merged. `APD-ECO-013/-014` and `APD-CASCOR-014` are unused. All anchors resolve: cascor `:25`, `:231`, `:37`; locks data `:88`, cascor `:63`, canopy `:79`, recurrence `:70`; caps `<0.5.0`; F5 probes at service-core `:101`, data#440 `:34`, cascor#689 `:31`; exactly four "turn-ending" headers | F9's quote is the fix wording, not the defect (N7) |
| Remaining 5 / Appendix E (fork-drift) | Wait for data#440 and cascor#689 (both OPEN); add the Guard; run with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` | All anchors resolve: service-core `:88`/`:91`; canopy `:52`/`:137`/`:300`; csrf `:91`/`:97`; data#440 `:118`; cascor#689 `:87`; test `:174-182`/`:199-203`/`:205-209`; `ci.yml:500` (cron Monday 06:00) | The bare-word marker proves nothing (M4). The guard count is stated four times, not two (L1) |
| Remaining 6 (two candidates) | Read data `app.py:187-212` and cascor `:856`; start both services on free ports with DSNs `""`; POST a lone surrogate | The anchors resolve: primer 2662, 2686, 2687 and 4742-4743; data L191 "byte-identical" | Where to file each is unstated (L7) |
| Remaining 7 (PATCH #2080) | `gh pr view 2080 --json body`; read N6 in `ml2080-round1-laneA-reprobe.md:156`; `gh api -X PATCH` | The target is in the body: "Rejected, with reasons" at L65, the A-nit at L69. The PATCH was not run (forbidden) | No replacement text (L7) |
| Remaining 8 / Appendix B | Confirm each decision is still open; ask the owner with verbatim options | Yes. The later-arc ids are all open; MEMORY.md is 24,929 characters; `pr-63` and `pr-683` both point at `4caf9389` | #2089's CodeQL decision is missing (M2) |
| Appendix C | Byte-compare the durable copy with the tmpfs drafts; re-copy after the executor; check the anchors at `d1c66a11` | The copy equals `# ` + title + `\n\n` + body (18,454 B). The tmpfs drafts are unchanged since 20:46Z. All 8 anchors resolve | Re-copy order and mechanism (M3, L6) |
| Appendix D | Diff against the predecessor's L21-52 | The item mapping is correct | How #2081's CodeQL block was cleared is not carried (M2) |
| Appendix F | `git show --stat 5af9d722`; #2089's files; the memory files | Accurate. 14 of 14 files match. #2089's 132 files are byte-identical to the local copies. The new memory file exists and is linked | None |

## Findings

### HIGH

**H1. Each lane's successor is told to message the other lane's retiring session, so neither can reach the other.**
- **Quotes:**
  - L19: "SendMessage the peer lane, **"defect reg [042116]"** (session `bc31e993`) … It sends its PR numbers and SHAs to this session otherwise."
  - L57: "it sends the path and PR number."
  - L67: "send the PR number to "defect reg [042116]"."
- **Evidence:** the peer's handoff says:
  - L3: "Session handing off: `bc31e993…`, which `ListAgents` shows as `defect reg [042116]`. It wrote this file. **Never message it.**"
  - L22: "Message `defect reg [24f8d8]`". That is this old session.
  - L25: "If `[24f8d8]` is gone, ask the user which handoff governs."
  - L13 and L192: its PR will be on branch `docs/handoff-round42-followup-lane`. No such PR exists yet; #2089 is the only open juniper-ml PR.
  - So Remaining 0 (the owner's consolidation) and Appendix A's gates wait on a message addressed to a session that will be gone.
- **Replace L19 with:** "3. **Re-route the peer lane.** Load `ListAgents` and `SendMessage` with ToolSearch if they are deferred, then run `ListAgents`; its header names your own session as `<name> [<ref>]`. The peer is handing off too. Its handoff (`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, L3 and L22-25) calls `defect reg [042116]` the session handing off, says "Never message it", and tells ITS successor to message `defect reg [24f8d8]` (the session that wrote this file), or to ask the user if that one is gone. So:
   - Message the peer's SUCCESSOR, the session working that handoff, and not `[042116]`. If you cannot tell which session that is, ask the owner. Tell it you replace `[24f8d8]`, and give it your name and `[ref]`.
   - If `[042116]` is still listed, message it too, so it can pass your name on.
   - Never wait on a message for the peer's PR. `gh pr list --repo pcalnon/juniper-ml --head docs/handoff-round42-followup-lane --state all --json number,state,mergeCommit` finds it."
- **L57:** replace "it sends the path and PR number" with "take it from its PR on branch `docs/handoff-round42-followup-lane` (the command in First action 3); do not wait for a message."
- **L67:** replace `"defect reg [042116]"` with "the peer's successor (First action 3)".
- **Verification commands:** add that `gh pr list … --head docs/handoff-round42-followup-lane …` line, annotated `# [] at handoff`.

**H2. The liveness rule reads a live executor as dead, and the recovery step then launches a second executor on the same worktree.**
- **Quotes:**
  - L49: "If that file was written in the last ~10 minutes, the old session is still running … wait, or ask the owner to close that session."
  - L51: "If it died, the worktree is dirty and the ref is still `d1c66a11…`: … launch a new `task-executor` on the same worktree".
- **Evidence:**
  - In `agent-a46e715a6801b98ca.jsonl`, the executor went silent while alive for 10.0 min (20:21:04 to 20:31:04Z) and 9.7 min (20:31:33 to 20:41:13Z), each during a single tool call.
  - It then sat idle for 181.2 min (20:47:35 to 23:48:49Z), and the live parent resumed it by SendMessage.
  - "Dirty, ref at `d1c66a11`" is exactly the state of the live executor now: 12 dirty files, last record 00:44:52Z. So the mtime rule is the only discriminator, and it misfires.
  - Asking the owner to close the old session kills the executor (L46's own heading).
  - `ListAgents` shows each peer session's state ("defect reg [042116] · interactive · busy", 19:03:13Z), but the rule does not use it.
- **Replace L49 with:** "**Is it alive?** Any one of these means yes: do not touch the juniper-data worktree, and do not launch a second executor.
  - `ListAgents` still lists `defect reg [24f8d8]` in any state but offline. A live parent can resume a stopped executor, as this one was at 23:48:49Z after 181 idle minutes.
  - `find /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/ -name agent-a46e715a6801b98ca.jsonl -mmin -30` prints the file. It went silent for 10.0 and 9.7 minutes while alive, so ten minutes is no margin.
  - Its last assistant record is a `tool_use`, not the text-only disposition report.
  - Wait for it. Do not ask the owner to close the old session while it runs: that kills the executor, and its in-context state goes with it."
- **L18:** append "…or if `ListAgents` still lists `defect reg [24f8d8]`."

### MEDIUM

**M1. The recovery step passes half the brief and misses the "clean but ahead" state.**
- **Quotes:**
  - L50: "**Its full brief** is the `user` record at 2026-09-24T23:48:49Z."
  - L51: "save that brief … Tell it to review the uncommitted diff first."
- **Evidence:** the transcript holds two brief records.
  - 19:37:50.383Z, 8,881 characters. It carries:
    - the verification regime and the whole-file upload proof;
    - the commit trailers;
    - "Do NOT open, merge, arm, update-branch, draft or ready any PR" and "Stop every server you start";
    - four tmpfs spec files: `data_round4_spec.md`, `data_round4_redirect.md`, `data_round3_original_brief.md` and `old_executor_summary.md`.
  - 23:48:49.313Z, 8,561 characters. It says "Verification, same bar as before" and elides the push arguments with `...`, so it cannot stand alone.
  - Step 4 of the 19:37 brief has the executor make "an unsigned scratch commit with `git -C $W -c commit.gpgsign=false commit`". If it dies after that step, the worktree reads CLEAN and the branch is ahead of origin. Neither L51's trigger nor L121's `status --short` shows that state.
- **Replace L50-51 with:**
  - "**Its brief is TWO `user` records in that file:** 19:37:50.383Z, the task (regime, upload proof, the unsigned scratch commit, trailers, the PR prohibitions, and the four scratchpad spec files named above), and 23:48:49.313Z, the round-1 fixes, which relies on the first.
  - Read the disposition report with `last_report()`, loaded through `importlib.util.spec_from_file_location`; never read it with `splitlines()`.
  - **If it died** (not alive by every test in H2): run `git -C <data worktree> status -sb`. A death after the scratch commit reads clean with `[ahead N]`, and that commit must never be `git push`ed.
  - Dirty or ahead, with the ref still `d1c66a112e4bc70ee97496a14265f7b90e10fb88`: extract both briefs to your scratchpad with a script. Launch a new `task-executor` in your session on that worktree, with both briefs, both round-1 reports and the drafts. Tell it to review `git diff origin/fix/conditional-requests-round4-followups` first, and to push with that full `--expected-head`."
- **L121:** change `status --short` to `status -sb`, annotated "`[ahead N]` = an unsigned scratch commit; never push it".

**M2. #2089 cannot go green without an owner decision, and the snapshot does not say so.**
- **Quotes:**
  - L31: "CodeQL may flag the probes, as it did #2081's."
  - L61: "Merge #2089 once it is green".
  - L288: "#2081's CodeQL block: resolved".
- **Evidence:**
  - `gh pr checks 2089`: CodeQL **fail**, "33 new alerts including 4 high severity". The four highs are alerts 843-846, `py/overly-permissive-file`, all in `util/ad-hoc/2026-09-24_round42_probes/data438-fixforward-round1-laneB/stripe_probe.py`. All other required checks pass.
  - The predecessor (L25) called #2081's identical block "**the owner's decision**". #2081 merged only after its two highs were dismissed as "mitigated" (22:43:46Z and 22:44:26Z). No dismissal call appears in session 2fba4397's transcript.
  - The peer's handoff L29 says commits land on open PRs from the owner's account (for example `095a2108`, "improve file handling with context managers"). A commit like that on #2089 would break the byte-identity its README claims.
- **Replace L31 with:** "**CodeQL FAILED:** 33 new alerts, 4 high (`py/overly-permissive-file`, alerts 843-846, all in `…/data438-fixforward-round1-laneB/stripe_probe.py`). Clearing them is the owner's decision, as #2081's was: its two highs were dismissed 'mitigated' before it merged. Surface it (Appendix B). Re-check the branch for owner-account commits before merging."
- **L61:** "…once the owner has cleared its CodeQL alerts and it is green…".
- **Appendix B:** add "#2089's CodeQL block (`paths-ignore`, dismissal, or a tarball)".
- **Verification commands:** add `gh pr checks 2089 --repo pcalnon/juniper-ml`, annotated `# CodeQL fail at handoff`.

**M3. First action 4 races the live old session and contradicts Appendix C's ordering.**
- **Quotes:**
  - L20: "Ship the uncommitted files (Git status)."
  - L242: "Re-copy it once the executor finishes."
  - L243: "It ships with the Git status files."
- **Evidence:**
  - The old session is alive and planned "After round 2 comes the three-way consolidation" (transcript, 00:29:24Z). It will add this round's reports and MISSING entries, and re-copy the draft, in this same worktree.
  - Two sessions shipping the same paths is an add/add collision.
  - Both executor briefs run `…/fizzy-hugging-dream/util/push_signed_commit.py` and read the round-1 reports by absolute path in this worktree.
- **Replace L20 with:** "4. **Ship the uncommitted files (Git status) only when `ListAgents` no longer lists `defect reg [24f8d8]` and the executor has finished.** Until then the old session is still writing here and may ship them itself. Re-copy the PR draft first (Appendix C), then check that no open juniper-ml PR carries these paths (`gh pr list --repo pcalnon/juniper-ml --state open`, then `gh pr view <N> --json files`). Until they ship, and while the executor lives, never `git reset`, `checkout`, `clean`, `stash` or remove this worktree: the executor's briefs run `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/util/push_signed_commit.py` and read the reports here."

**M4. Appendix E's bare `surrogatepass` marker is already satisfied by a comment in every copy.**
- **Quote:** L295: "Pin a PAIR of markers …: `surrogatepass` and `compare_digest(presented,`."
- **Evidence:**
  - `guard_is_present` is a whole-file substring test (`tests/test_service_fork_drift.py:289`).
  - The word also sits in a comment or docstring at service-core `:82`, data#440 `:108`, cascor#689 `:78` and canopy `:49`.
  - So a revert to a `str` compare that keeps the comment passes, which is `APD-ML-008`'s weakness.
  - This session's own plan at 23:39Z and 23:41Z pinned `.encode("utf-8", "surrogatepass")`, and that string appears only in code.
- **Replace the marker text with:** "`encode("utf-8", "surrogatepass")` and `compare_digest(presented,`. **Not the bare word:** every copy names it in a comment (service-core `:82`, data#440 `:108`, cascor#689 `:78`, canopy `:49`), and the matcher is a substring test (`:289`). The full spelling is code-only: service-core `:88`/`:91`, canopy `:52`, data#440 `:115`/`:118`, cascor#689 `:84`/`:87`. Mutation-check it: delete the `.encode(...)` call from a copy of each site and confirm the guard fails."

### LOW

- **L1. The guard count is stated four times, not two.** L303 "**Two counts change**". The four statements on `origin/main` are `docs/REFERENCE.md:2977` and register L252, L1106 and L1751. Replace with "Four count statements change: `docs/REFERENCE.md:2977`, and the register's L252, L1106 and L1751."
- **L2. The consolidation had not begun, and there is no way to find the result.** L58 "This session had begun the consolidation." No draft exists; at 00:29:24Z the session was still waiting for the peer. Replace with "It had not started: it coordinated with the peer (23:34Z, 00:21Z) and was waiting for the peer's final version. No draft exists." In L6, add: "look in `prompts/thread-handoff_automated-prompts/` on `origin/main` and in open juniper-ml PRs."
- **L3. Counts that change with this round.** L114 "13 entries" and L119 "39 here; 34 … its 5 reports". Each report archived from this validation round adds one entry and one OK line. Recompute both after archiving.
- **L4. #2089's files are not excluded from the next PR.** L138 says they are "already on #2089's branch" but does not say to leave them out, and First action 4 says to ship "the uncommitted files". Append: "byte-identical to #2089's 132 files. **Leave them OUT of the next PR**: the same path added on two PRs is an add/add conflict."
- **L5. Re-arming is a merge action.** L106's re-arm recipe should add: "Re-arming needs your own grant, and `--auto` on a PR that is already MERGEABLE merges at once."
- **L6. Two mechanisms are unstated.**
  - L66: `--title "<draft line 1>"` should be "line 1 of the copy, without its leading `# `", and `--body-file` should be a scratch file holding line 3 onward.
  - L242: the re-copy should read "`# ` + the title file's line, a blank line, then the body file, built with a script".
- **L7. Two items say what but not where.**
  - Remaining 6: say where each candidate is filed. (a) is a register row, with its repo prefix, in the closes PR; (b) is a primer correction made in place.
  - Remaining 7: name the target: "the bullet 'A-nit on `APD-ML-008`' (#2080 body L69, under 'Rejected, with reasons' at L65); move it to the applied table, citing #2088."

### NIT

- **N1.** The Goal section (L9-84) is 1,256 words against the procedure's ~1,200. That is inside its IQR of 778–2,718.
- **N2.** L122's `stat` prints local time (-0500) with no clock to compare against. Use the `find … -mmin -30` form from H2.
- **N3.** "this session" means 2fba4397 throughout, but a successor reads L19's "to this session otherwise" as itself. Write `defect reg [24f8d8]`.
- **N4.** The trap at L110 says compound shell around git and gh is refused, yet L117 and L123 are compound. They ran here. The two refusals I hit were both my own multi-statement commands. Soften the trap to "may refuse".
- **N5.** L102 says "This session's venv is on tmpfs" but gives no path. Name it. CPython 3.13.13 is the `JuniperCanopy1` interpreter.
- **N6.** L71 "PR CI runs only `SharedPackageGuardTest` (`ci.yml:500`)". Line 500 runs the whole file; `ci.yml:496-499` says the sibling-site assertions skip there. Write "PR CI skips the sibling-site assertions".
- **N7.** L165 quotes F9's FIX wording as if it were the defect. `juniper-service-core/CHANGELOG.md:57-58` says the handshake "closes 4001". The rewording is "rejected: ASGI close 4001, HTTP 403 on the wire". "Not data#440" is correct: its diff and head commit never mention 4001.
- **N8.** Appendix B lists MEMORY.md under "owner decisions" while also saying the compaction is this lane's. Write: "Compact by retiring entries (`feedback_memory_index_target_is_20kb.md`); only a structural change is the owner's."

## Round-1 HIGH fixes

| Fix | Result |
|---|---|
| The Goal says to paste the WHOLE document and names its own file | **PASS.** Heading at L8; the file is named at L4, which a whole-document paste includes |
| The executor has a liveness check and a recovery recipe | **Present but defective** (H2, M1) |
| The PR draft copy exists and is described correctly | **PASS.** The copy is byte-equal to the drafts; the format and the 00:27Z timing are right |
| The Git status is complete | **PASS.** All 13 entries are accounted for. The three scratch commits hold exactly #2088's 14 files, byte-equal to `5af9d722` |

## Procedure compliance (`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`)

- **Goal length:** 1,256 words (N1). The whole document is 4,312.
- **Verification commands:** present, and all run and match. Gaps are covered by H1, H2 and M2.
- **Git status:** complete. Nothing is staged.
- **Archive filename:** conforms to Step 4.
- **Refusals:** the sandbox refused none of the snapshot's commands.

## What I could not verify

- Who `ListAgents` will list when a successor starts, and the name of the peer's successor. I did not call it.
- How the executor ends: its disposition report, whether it updates the drafts, and whether it leaves a local scratch commit.
- Who dismissed #2081's highs. The `pcalnon` account is shared by the owner and every session.
- Harness 62/62 and mutation check 12/12, which need the tmpfs venv. Round-1 lane F (`handoff-2fba4397-round1-laneF-reprobe.md`) reproduced them.
- Whether a session's scratchpad (drafts, spec files, venv) is deleted when the session ends.
- Whether `SENTRY_SDK_DSN` is exported (not printed, per the rules), the 0.16.0 notify-consumers 403, and canopy#685's validation status.

**Changed:** no repository file.
- **Fetches:** `git fetch` in this worktree moved `origin/chore/round42-probe-provenance-session-2fba4397` from `d8a495f7` to `a2fa3ad8`. I also fetched juniper-data, juniper-cascor, juniper-canopy and juniper-recurrence.
- **FETCH_HEAD** in juniper-data and juniper-cascor was overwritten by fetching the heads of data#440 and cascor#689.
- **Temporary ref:** `refs/remotes/origin/laneP2-pr440` was created in juniper-data and then deleted.
- **Scratch:** `hv2/laneP2/` (9 scripts and 2 brief extracts) is deleted. `laneF2` and `laneO2` were not touched.
