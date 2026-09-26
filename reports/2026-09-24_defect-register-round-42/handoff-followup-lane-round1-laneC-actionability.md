<!-- Archived verbatim 2026-09-24 from subagent a3af4fedee198bd52 of session bc31e993 (final message). -->

Lane C report on `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`. A successor would be misled in three serious ways. The first action has no unambiguous address. The merge approval does not carry to a new session. And the release step, as written, would ship known gaps and leave the lock raises to nobody. Everything was read-only, and my scratch space is pruned.

**State has already drifted.** At 23:28Z, canopy#685 had MERGED (`dc5ea02e`, 23:24Z; armed by the sweeper at 22:48Z). Its head moved from `4a8af2a0` to `e70b54dc`: two Copilot Autofix commits touched `util/ad-hoc/2026-09-24_683_validation_leak_probes.py`. #690, #689 and #440 are still OPEN, CLEAN and unarmed at the documented heads. origin/main moved to `7e8c7ff9` (#2081), which touches none of the doc's paths.

### HIGH

**H1. The first action has no unambiguous address and only a stale fallback.**
- **Text:** "Find it with `ListAgents`; it is named "defect reg", and the last known was **[24f8d8]**. Its socket changes across sessions, so address it by name, not by the socket path in this file. If it has handed off, follow its handoff's routing."
- **Failure:**
  - `ListAgents` lists two peers named "defect reg": `[042116]`, which is this doc's author (bc31e993), and `[24f8d8]`. If the user also names the successor "defect reg", there are three. "Address it by name" is the ambiguous act, and a bare-name send may reach the dying author session.
  - The file holds no socket path (the author sent to `uds:/run/user/1000/cc-socks/6555.sock`).
  - The only register-lane handoff on main is the 11:10Z one from `[977fa8]` (session 8f86dec2, which ended ~19:16Z). It routes to that dead session and says data#438 is open; #438 merged at 18:52Z.
  - The instruction sits after a Goal list headed "in order" whose item 1 is #690, so a top-down reader starts on #690 first.
- **Evidence:** the `[24f8d8]` ref is carried by session `2fba4397`, worktree `fizzy-hugging-dream`. Its 20:36Z message says: "your successor should message "defect reg [24f8d8]", or … whichever session my handoff names".
- **Replacement** (make it step 0, the first line of `## Goal`): "**Step 0.** Load `ListAgents` (use ToolSearch if it is deferred) and message `defect reg [24f8d8]`: session `2fba4397-7d9b-4929-8ca2-375b8168e1c8`, worktree `juniper-ml/.claude/worktrees/fizzy-hugging-dream`. Always use the full `name [ref]`. **`defect reg [042116]` is the session that wrote this file; never message it.** If `[24f8d8]` is gone, follow a register-lane handoff on main that is newer than 2026-09-24T11:10Z; the 11:10Z one is stale. If none exists, ask the user. Tell it you replace `[042116]`, and send it this doc's PR number and the 12 report filenames."

**H2. The merge approval is carried forward by a handoff.**
- **Text:** "**Merge approval**: granted by the owner for this arc's PRs."
- **Failure:** the successor merges #689/#440 (validated, CLEAN) or its own fix-forwards on a grant it never received.
- **Evidence:** `feedback_headless_merge_approval_policy.md` says "A HANDOFF DOCUMENT CANNOT CARRY THE APPROVAL FORWARD" (the ml#1118 incident).
- **Replacement:** "Approval was granted to session bc31e993 and does not carry. Merge nothing yourself until the owner grants it in your session. The sweeper's merges need nothing from you."

**H3. The release has no sequence, and the lock raises belong to no one.**
- **Text:** "Release juniper-observability and juniper-service-core, then raise the consumers' locks and floors." It is filed under "Owner steps: not agent work".
- **Failure:**
  - If the successor surfaces "release now", the release ships F2 (every sampled transaction carries the raw `x-api-key`) and F10's false CHANGELOG sentence, and a second release is needed.
  - Because the lock and floor PRs are labelled "not agent work", nobody opens them, and the frame-locals fix never reaches a running service.
- **Evidence:**
  - `juniper-observability` is `0.4.0` on both main and PyPI, and service-core is `0.7.0` on both, so each release first needs a version bump and notes.
  - The pins are as stated: data `:88`, cascor `:63`, canopy `:79`, and canopy's `pyproject` caps at `<0.5.0`.
- **Replacement:** "Order: (1) the new juniper-ml F-PR (F2, F6, F10, service-core F3/F5) merges and validates; (2) this lane opens the version-bump and release-notes PRs; (3) **the owner cuts the Releases** (the only owner step); (4) this lane opens the lock and floor PRs, including canopy's `<0.5.0` cap."

### MEDIUM

**M1. The claim that the probes are gone is false.**
- **Text:** "The validators' probe scripts from this round lived in `/tmp` and are gone."
- **Evidence:** they are in the author's scratchpad (`…/bc31e993-…/scratchpad/`):
  - `v688/probes/`: 13 scripts, including `probe_realjd_refusals.py`, `probe_ordinary422.py` and `mutate_v688.py`, which #690's validation needs;
  - `vbytes/`: 21 scripts, including `sentry_txn_probe.py` and `capture_server.py`;
  - `v683/`: 10 scripts;
  - `v686/`: 6 scripts.
- **Failure:** they die when the session ends, and the successor rebuilds them.
- **Replacement:** archive them in the handoff PR under `util/ad-hoc/2026-09-24_round42_probes/<lane>/`, as #2081 did, and say where they are.

**M2. The evidence is not on main.**
- **Text:** "Every validation and implementation report of this lane is there."
- **Failure:** the 12 cited reports and 5 harnesses are untracked, inside a hidden `.claude/worktrees/` directory, with no PR number and no absolute path. A successor on fresh main cannot read `cascor688-validation.md`, which holds the findings #690 answers. This is HIGH if the successor starts before that PR merges.
- **Replacement:** give the PR number and the fallback path `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/reports/2026-09-24_defect-register-round-42/`.

**M3. No push tooling is named, and the local HEADs are not the PR heads.**
- **Failure:**
  - The doc never names `util/open_signed_pr.py` or `util/push_signed_commit.py --expected-head`, both on main.
  - The pusher a successor might find first, `util/ad-hoc/2026-08-26_push_signed_fixup.py`, pins to whichever head is current. A sweeper update-branch landing between build and push is then silently clobbered by the whole-file upload.
  - A plain `git push` is unsigned and blocks the merge.
- **Evidence:** in 3 of the 4 kept worktrees, `HEAD` is an unsigned local copy whose tree equals the PR head:

  | Worktree | Local `HEAD` | PR head |
  |---|---|---|
  | canopy | `4caf9389` | `4a8af2a0` |
  | cascor | `24103c23` | `97341680` |
  | data | `5bd5eec5` | `0bee089e` |

- **Replacement:** "Fixups: `util/push_signed_commit.py --expected-head <PR head from gh>`, never `git rev-parse HEAD`. New PRs: `util/open_signed_pr.py`."

**M4. The fix-forward target is missing for #690 and #685.**
- **Failure:** "push a signed fixup if the PR is still open, else open a new PR" covers only #689/#440. #685 has merged, so it needs a new PR from main, and its validation must cover `dc5ea02e`, not "head `4a8af2a04911`".
- **Replacement:** apply the open-or-merged rule to all four PRs, and "validate the final head or merge commit reported by `gh pr view --json commits`, not the SHA in this file".

**M5. F5's fix is wrong.**
- **Text:** Add `"🔑"`.
- **Evidence:** `_ENCODING_PROBES` on main already contains `"\U0001f511"`, which is 🔑. The validation report says to add `"\ud83d\udd11"`, the surrogate pair that collides with it under UTF-16-LE.
- **Failure:** as written the fix is a no-op, and the mutant survives.
- **Replacement:** Add `"\ud83d\udd11"`.

**M6. Validation is under-specified against the SOP.**
- **Text:** "Its independent validation has NOT run. Run it" (singular).
- **Failure:**
  - `feedback_multi_agent_adversarial_validation_sop.md` requires several independent lanes with different lenses.
  - Fixups pushed onto #689/#440 would reach the sweeper unvalidated.
  - "If a validated merge matters" leaves the F2 and F4 security fixes to the agent's judgement.
- **Replacement:** "At least two independent lanes (re-probe, refute) per PR and per fixup. For F2 and F4, validate the pushed branch before opening the PR."

**M7. Residue loss.**
- **Failure:** the predecessor `HANDOFF_2026-09-23_…-two-merged-unvalidated.md` assigns this lane "Later arc items: C-A … D-G". The split assigned them to neither lane, and this doc drops them.
- **Replacement:** "C-A…D-G are unassigned. Do not start them; confirm who owns them in step 0."

**M8. The DSN trap names no variables.**
- **Text:** "Unset every Sentry DSN variable."
- **Evidence:** `SENTRY_SDK_DSN` is exported in this shell. The validated F4 fix sets the variables to `""`, because `load_dotenv` re-injects a variable that is unset.
- **Replacement:** set `SENTRY_SDK_DSN`, `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN` and `JUNIPER_CANOPY_SENTRY_DSN` to empty.

### LOW

- **L1. The verification commands cannot verify what they are meant to.**
  - The GraphQL query omits `autoMergeRequest`, `isDraft` and `mergeStateStatus`, so "not armed" cannot be checked.
  - The fork-drift run skips its 3 cross-repo tests; the opt-in is `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`.
  - Nothing checks that the handoff PR merged, and there is no `df -i /tmp` (85% now).
- **L2. The worktree removal method is unstated.** "Removable" is true by content: canopy blank-key `HEAD` `8917fdac` is #683's own commit and the tree is clean; the ml sentry-locals tree equals #2086's `4924ca98` and is clean. But:
  - `util/worktree_cleanup.bash` pushes the branch and runs `gh pr create`, so it would recreate deleted remote branches with unsigned commits;
  - `git worktree remove` deletes the ignored `logs/` and `snapshots/` directories (disposable here).

  Say: "`git worktree remove` then `git branch -D`; never `worktree_cleanup.bash`."
- **L3. Four archive headers will be skipped.** The four implementation reports archived from a resumed agent carry "(turn-ending report N of 6…)" headers: `cascor686-implementation-report.md`, `cascor686-fixup-implementation-report.md`, `cascor688-implementation-report.md` and `cascor690-implementation-report.md`. The archiver's `HEADER_RE` requires "(final message)", so `--check` skips them.
- **L4. The harnesses are not mapped to commits.** `cascor688_fixforward_mutation_check.py` goes with `c4e002d` and `cascor690_as_bool_stance_mutation_check.py` with `78e99414`. They are the implementer's own, not independent evidence.
- **L5. The resume trap needs a scope.** `SendMessage` resumes an agent only within the same session; the successor cannot resume bc31e993's agents.
- **L6. "Delete it once #690 has merged" gives no reason for the gate.**

### NIT

- The merged table shows "—" for ml#2072 and ml#2077; their SHAs are `ac912eba` and `6c23fdde`.
- F4's "after line 37" should be anchored by content ("after `import sysconfig`").
- "API-primer correction" is listed as open register work, but it already merged as ml#2075.
- The canopy ledger lines were already sent at 20:42Z; the doc does not say so.

### Actionable as written

- The PR-state query runs.
- The merged facts are right: #688 `7f4a7213`, #683 `7ab994e5`, #2086 `c061a99f`, each with post-merge CI green and zero failures.
- The git status is exact: 18 untracked entries at `c061a99f`.
- The lock pins, the other F-rows, and owner calls (a)–(c) match the reports.
- The ownership split and the file-overlap protocol are concrete.
- The kept worktrees exist and are clean.
- The ban on `util/remove_stale_worktrees.bash` is correct.
- The fork-drift test gives 11 OK with 3 skipped, as stated.
