# HANDOFF 2026-09-24 — round-42 follow-up lane: four PRs await validation or fix-forward, and the owner's observability release gates the Sentry fix

**Session handing off**: `bc31e993-97b0-4a01-ae04-cb39593eb647`, which `ListAgents` shows as **`defect reg [042116]`**. It wrote this file. Never message it.

**Predecessors**:
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`: this lane's previous handoff.
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`: the register lane's 11:10Z handoff, via juniper-ml#2084. **It is stale and never governs.**

**Which document governs.** The register lane (`defect reg [24f8d8]`) reports that the owner asked it to merge three handoffs into ONE validated handoff: this file, #2084's and its own. It starts once it has this file's final path and PR number.
- Once the consolidated handoff is on `main`, it governs every instruction, and this file is only an evidence index.
- Until then, this file governs this lane's work. Check `main` for the consolidated handoff again before each OPEN item.
- The register lane's own pre-consolidation handoff, marked "Superseded if consolidated", is untracked at `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`. Read it with `cat`. It is that lane's record, NOT this lane's instructions.

**Evidence**, landing in this file's `docs(handoff)` PR (branch `docs/handoff-round42-followup-lane`). Until that PR merges, the files exist only in the worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/`.
- `reports/2026-09-24_defect-register-round-42/`: every validation and implementation report of this lane, verbatim, plus this file's own validation (`handoff-followup-lane-round*-*.md`).
- `util/ad-hoc/2026-09-24_round42_probes/{cascor686-v686,canopy683-v683,cascor688-v688,bytes-compare-ml2086-data440-cascor689-vbytes}/`: the validators' 63 probe scripts. Their README rows ride juniper-ml#2089.
  - Most take a tree (and a URL) as arguments; some write under a `work/` or `out/` directory beside themselves.
  - Treat them as evidence. Read each one's arguments before running it, and pass only fresh scratch paths: `make_nv1_tree.py` deletes its second argument, and `fix_probe_pairs.py` rewrites a `compare_probe.py` in the working directory.
- `util/ad-hoc/2026-09-24_cascor688_*.py` and `2026-09-24_cascor690_*.py`: the implementer's five harnesses. OPEN item 1 maps them to commits.

## Step 0: do this first

1. **Message `defect reg [24f8d8]`**, always with the ref: two sessions are named "defect reg". It is session `2fba4397-7d9b-4929-8ca2-375b8168e1c8`, in worktree `juniper-ml/.claude/worktrees/fizzy-hugging-dream`. Load `SendMessage` with ToolSearch if it is deferred.
   - Tell it you replace `[042116]`.
   - Unless it confirms `[042116]` already sent them, send it this file's path and PR number.
   - Ask it for the consolidated handoff's path.
   - **If `[24f8d8]` is gone**, look in `ListAgents` for its successor and do the same with that session. Its handoff has it look for you too, and message `[042116]` only if that session is still listed. Tell it you replace `[042116]`.
   - **If there is no successor either**, and no consolidated handoff is on `main`, this file still governs this lane. The register lane's handoff is its record, not your instructions. Ask the user who takes over its items and who consolidates.
2. **Get your own merge approval.** The owner granted merge approval for this arc to session bc31e993, and a handoff cannot carry it forward (`feedback_headless_merge_approval_policy.md`; the ml#1118 incident). Merge nothing until the owner grants it in YOUR session, and even then only with checks green on the current head and the validators cleared.
3. **The PR sweeper is the owner's** ("Mine: fix forward", 2026-09-24).
   - It un-drafts, arms and update-branches open PRs as `pcalnon`, and its merges are intended.
   - Commits also appear on open PRs from the owner's account: #2077 got `095a2108`, and canopy#685 got two.
   - Do not draft or disarm a PR to hold it.
   - An open PR can merge at any moment. When a validated merge matters, validate a change BEFORE it reaches a PR branch; that is always the case for F2 and F4. Otherwise, validate after merge and fix forward.

## Goal

Continue the **round-42 follow-up lane**. The split, "Split: old does follow-ups", was relayed by the register lane (`defect reg [977fa8]`). The owner's own answer in this session, "Resume both here", is consistent with it.

- **This lane:** the cascor and canopy follow-ups and the "Key leaks" PRs. The owner chose "Fix everywhere now (Recommended)", whose text ends "**Releases stay yours.**" So this lane validates and fixes forward, and surfaces the release rather than cutting it.
- **The register lane**, so start none of these:
  - the register (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`), its closes PRs and rows;
  - the API primer (#2075 and #2088, merged);
  - the `MEMORY.md` compaction;
  - the fork-drift gate (`tests/test_service_fork_drift.py` and `docs/REFERENCE.md`'s drift-gate section), including the new `surrogatepass` marker, which comes after data#440 and cascor#689 merge;
  - the later arc items C-A…D-G, which the consolidated handoff carries as owner decisions.

### Merged

Post-merge `main` CI is green on all six.

| PR | Merge | Note |
|---|---|---|
| juniper-cascor#688 | `7f4a7213` | #678's follow-up. It supersedes #686 (CLOSED): #687 conflicted, and the signing path cannot create the merge commit that would resolve that. It carries the owner's ruling "Keep while fetched splits stay (Recommended)". |
| juniper-canopy#683 | `7ab994e5` | Merged from `34e06747`, which is the validated `8917fdac` plus a main merge that overlaps it only in `CHANGELOG.md`. Its 60 non-blank CHANGELOG lines all sit under `[Unreleased]`. |
| juniper-canopy#685 | `dc5ea02e` | Merged 23:24:14Z, **unvalidated**, from `e70b54dc`. The two commits after `4a8af2a0` touch only a probe script. |
| juniper-ml#2086 | `c061a99f` | Service-core and observability: the bytes compare, `include_local_variables=False`, and frame `vars` dropped. |
| juniper-ml#2072, #2077 | `ac912eba`, `6c23fdde` | The previous handoff and its reports; the #686 and #688 harnesses. #2077's squash includes `095a2108`. |

### OPEN: this lane's work, in order

1. **Validate juniper-cascor#690.** It is on branch `fix/shortfall-688-validation` with commits `c4e002d2` and `78e99414`, and was open and not armed at writing.
   - **What it is:** #688's fix-forward, answering the 2 MEDIUM, 3 LOW and 2 NIT findings in `cascor688-validation.md`. `_as_bool_stance` now parses `allow_truncation` exactly as juniper-data's pydantic `str_as_bool` does; the old reader read `"f"` and `"n"` as true.
   - **How:** at least two independent lanes (re-probe and refute) on each commit. The implementer's evidence is not independent:
     - reports: `cascor690-implementation-report.md`, `cascor690-fixup-implementation-report.md`;
     - harnesses for `c4e002d2`: `2026-09-24_cascor688_fixforward_mutation_check.py`, `…_cascor688_realjd_error_texts.py`;
     - harnesses for `78e99414`: `2026-09-24_cascor690_bool_stance_producer_table.py`, `…_realjd_probe.py`, `…_as_bool_stance_mutation_check.py`. The last imports the `cascor688_fixforward` harness by path.
   - **Probes:** `util/ad-hoc/2026-09-24_round42_probes/cascor688-v688/`. The `probe_realjd_*.py` probes and both `realjd` harnesses need a live juniper-data.
     - Serve one with `bash util/ad-hoc/2026-09-24_serve_scratch_juniper_data.bash <tree> <scratch-dir> <port>`.
     - `<tree>` must be a scratch export, never a checkout: `git -C <juniper-data clone> fetch origin main`, then `mkdir -p <tree>`, then `git -C <juniper-data clone> archive origin/main | tar -x -C <tree>`.
     - The script refuses a checkout. It keeps storage and imports in scratch, with the probes' `big.csv`, and inherits no keys, CSV-import cap or truncation switch. Metrics, rate limiting and Sentry are off.
     - The final script was tested at 2026-09-25T01:17Z, with lower-case variants of the auth and cap variables set in the shell.
       - `/v1/health` and an anonymous `/v1/generators` returned 200, and the over-cap `csv_import` returned juniper-data's real 422 refusal.
       - `pkill -A` stopped it, and the checkout stayed clean.
   - **Then:** fix forward per "Where fixes go". When #690 merges and validates, tell the register lane: CASCOR-008 and -013 wait on it.
2. **Validate juniper-canopy#685 post-merge, at `dc5ea02e`**, with at least two lanes, and fix forward in a NEW PR from `main`.
   - **What it closes:**
     - APD-ECO-014: padded outbound keys were quoted in client errors, logs, Sentry and API bodies, including an ANONYMOUS read of the cascor key through `POST /api/train/start`'s 409 with auth on.
     - canopy's half of APD-ECO-013: the `str` `compare_digest` at `security.py:115`, `:273` and `csrf.py:91` became bytes at `:137`, `:300` and `csrf.py:97`.
     - `canopy683-validation.md`'s LOW3 and LOW4 (F-CANOPY-061 and -062).
   - **Report:** `canopy685-implementation-report.md`. It also records that the anonymous rate-limiter 500 needs `rate_limit_enabled`, which is off by default.
   - **A stale comment**, at canopy `test_cascor_service_adapter_gate_coverage.py:49-50`, says CI installs only the stub cascor client; it installs the real one. This is a NIT that can ride any later canopy PR.
3. **cascor#689 (`97341680`) and data#440 (`0bee089e`)**, both on branch `fix/bytes-compare-no-500`. Both were open, not armed, and **validated**: 0 failures over U+0000–U+10FFFF, 0 responses of 500 on real uvicorn, and a timing profile that depends only on the configured key's length. Reports: `bytes-compare-ml2086-data440-cascor689-validation.md` and `…-implementation-report.md`.
4. **The F fix-forwards from that validation.** F1 was fixed by canopy#685, and F8 (a `break` after `matched = True`) is killed by F3.

   | Item | Sev. | Where | Fix |
   |---|---|---|---|
   | F2 | MEDIUM | observability `sentry.py` | Pass `before_send_transaction=_strip_sensitive_headers`, with a test. Transactions skip `before_send`, so under `send_pii=True` (juniper-data only) they carry the raw `x-api-key`. |
   | F3 | MEDIUM | service-core, data, cascor (canopy has one) | Add a spy test: at least 2 keys, the match first, `len(calls) == len(keys)`, bytes arguments. In data, mark both the existing and the new spy test `unit`, or put the new one in the marked `TestNonAsciiApiKey` (`:206`). `TestAPIKeyAuth` (`test_security.py:37`) is unmarked, and CI's `-m "unit and not slow"` (`ci.yml:287`) deselects it. |
   | F4 | MEDIUM | cascor `src/tests/conftest.py` | After `import sysconfig` (line 37), set `SENTRY_SDK_DSN`, `JUNIPER_CASCOR_SENTRY_DSN` and `SENTRY_DSN` to `""`. Do not unset them: `load_dotenv` re-injects. Tests that `import main` start the REAL SDK. |
   | F5 | LOW | `_ENCODING_PROBES`: `juniper-service-core/tests/test_security.py:101` (main), data `juniper_data/tests/unit/test_security.py:34` (#440), cascor `src/tests/unit/api/test_api_security.py:31` (#689) | Add the surrogate PAIR as two code points, `chr(0xD83D) + chr(0xDD11)`. **Not U+1F511**, which all three already hold. The pair and U+1F511 collide under UTF-16-LE with `surrogatepass`, and that collision is what kills the mutant. The comment "only total AND injective" is false. Check the file with `od -c`: the Write, Edit and SendMessage paths turn a typed escape into U+1F511. Canopy is out of scope: its `NON_ASCII` (`:172`) is checked only against a fixed `"key1"`, so the pair is inert there. |
   | F6 | LOW | observability `tests/test_sentry.py` `_frames` | Add frames with `in_app: False` (the real frame is library code), plus one wire test with `in_app_exclude`. |
   | F7 | LOW | cascor `test_main_sentry_no_local_variables.py` | Replace the AST match (`:33-35`) with a behavioural subprocess test: `get_client().options["include_local_variables"] is False`. This is a symbol loss, so waive it with `Allow-Symbol-Loss:` in a COMMIT body. |
   | F9 | NIT | `juniper-service-core/CHANGELOG.md:58`; cascor#689's CHANGELOG and PR body | "rejected: ASGI close 4001, HTTP 403 on the wire". cascor squashes with `COMMIT_MESSAGES`, so #689's first commit message ("4001 close") reaches `main` anyway. Correct it in the fixup's commit body, and report it as residue. data#440 carries no such text. |
   | F10 | NIT | observability `CHANGELOG.md` | "Consumers inherit both on upgrade, with no code change" is false: every lock pins `==0.4.0`. |

   **Where fixes go.** Read each PR's state with `gh pr view <N> --json state,headRefOid,mergeCommit` at push time, never from this file's SHAs.
   - An **open** PR gets a signed fixup: `util/push_signed_commit.py --expected-head <FULL headRefOid from gh>`. Never pass `git rev-parse HEAD`: in three worktrees HEAD is a local copy, not the PR head.
   - A **merged** PR gets a new PR from fresh `main`: `util/open_signed_pr.py`.

   Today that means:
   - **#690:** its validation's fixes, as a fixup while it is open, or a new PR once it has merged.
   - **juniper-ml:** one new PR for F2, F6, F9, F10 and service-core's F3 and F5.
   - **cascor#689:** fixups for F3, F4, F5, F7 and F9.
   - **data#440:** fixups for F3 and F5.
   - **canopy:** none.

   Validate every fixup and every new PR with at least two lanes.
5. **Surface these to the owner; do not decide them.** Ask with verbatim options, and send the register lane the question, the options and the answer.
   - **The release. "Releases stay yours."** Until juniper-observability and juniper-service-core ship, the frame-locals fix reaches no running service. `canopy685-implementation-report.md` measured the gap: any unhandled exception during a keyed request records the caller's key.
     - Ask once the juniper-ml F-PR validates. An earlier release ships F2's leak and F10's false sentence.
     - The options:
       1. the owner prepares and cuts both releases; or
       2. this lane opens version-bump and release-notes PRs at versions the owner names, and the owner cuts the Releases.
     - Ask separately who opens the cap, lock and floor PRs (the lines are under "Release facts" below).
     - Never approve a deploy gate (`feedback_deploy_approvals_paul_manages.md`).
   - **canopy#685's judgement calls:**
     - (a) An error that carries an HTTP status still passes its upstream text through. Making it type-only is a one-line change in `src/outbound_errors.py:57-61`.
     - (b) The key rule refuses a space or tab inside a key, which the clients would send.
     - (c) A blank `*_API_KEY_FILE` that shadows a real env var now sends no key.
   - **Two stray canopy branches, `pr-63` and `pr-683`.**
     - Both point at `4caf9389`, the #685 worktree's unsigned local commit.
     - They were pushed at 22:55Z, have no PR, and no agent transcript records the push.
     - Do not delete them unasked.
     - That worktree's upstream is `refs/heads/pr-683`. A plain command-line `git push` refuses there, because the branch names differ. An IDE push, or `HEAD:pr-683`, lands on it.
   - **The live Sentry project may hold this round's test events.** The shell exports `SENTRY_SDK_DSN`, and one run ended with "Sentry is attempting to send 2 pending events".
   - **Worktree and branch cleanup**, below.

## Coordination with the register lane

- **Send each item as it lands:** the PR number, the merge SHA, a validation summary, and every owner ruling's question, options and answer, verbatim.
- **What it holds on your outputs:**
  - CASCOR-008 and -013 wait for #690 to merge AND validate.
  - APD-CASCOR-014 closes when F4 lands.
  - APD-ECO-013 stays open until data#440 and cascor#689 merge, #685's validation holds, and F2 and F3 are fixed (`…closes-pr-owed.md`, Appendix A, APD-ECO-013). F5–F10 go on its row as residue unless fixed first, so tell it which ones landed.
  - APD-ECO-014's condition is met; its validation is yours.
  - The three APD IDs are reserved, not yet filed.
- **Its gate file.** The comment at `tests/test_service_fork_drift.py:205-209` says "no behavioural test can tell them apart", which the F3 spy refutes. It agreed (2026-09-25 00:21Z) to correct the comment with the `surrogatepass` marker.
- **Archiving.** Its archiver byte-checks every file whose first line reads `<!-- Archived verbatim YYYY-MM-DD from subagent a<16 hex> of session <8 hex> (final message). -->`, followed by a blank line. Use that header, and send it the filenames. Four reports here are headed "(turn-ending report k of 5 …)"; skipping them is expected.
- **File overlaps.** Both lanes upload WHOLE files.
  - Before every push, run `git fetch` and `git log <base>..origin/main -- <paths>`.
  - For a `CHANGELOG.md` `[Unreleased]` overlap, rebuild from `main` and prove `main`'s lines are a subset of yours.
  - Stay out of the register, the gate file, `docs/REFERENCE.md`'s drift-gate section, and `util/ad-hoc/2026-09-24_round42_probes/README.md` (#2089).
  - Stay out of the register lane's juniper-data branch `fix/conditional-requests-round4-followups` (`d1c66a11`; its PR is to come). It owns `http_cache.py`, `routes/datasets.py`, `storage/*`, `test_conditional_requests.py`, `api/app.py`, `docs/REFERENCE.md` and `docs/api/JUNIPER_DATA_API.md`, and it edits data's `CHANGELOG.md`.
- **Canopy ledger.**
  - F-CANOPY-060, -061 and -062 are reserved in the canopy E2E handoff, `juniper-ml/.claude/worktrees/graceful-sprouting-panda/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md:53-66`. It is untracked there, and the same bytes are pushed on `origin/docs/canopy-e2e-handoff-2026-09-24`, which has no PR.
    - 060: the refusal cut at `" The resulting dataset"` (`dashboard_manager.py:8410`) drops juniper-data's last sentence. It has no owner.
    - 061 and 062: LOW3 and LOW4, fixed by #685.
  - The copies of #687's "Nothing was loaded" sentence have no id. They sit in the canopy-combined handoff (`…/bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md:165-170`):
    - the copies are at `src/tests/unit/frontend/test_start_fresh_refusal_and_modal_text.py:42` and `src/frontend/dashboard_manager.py:8381`;
    - they go stale when #690 merges: cascor `main` emits the sentence at `manager.py:4766`, and #690 rewords it at `:4841`.
  - The canopy E2E session has exited, per the register lane.

## Release facts

- **Locks** at `==0.4.0` / `==0.7.0`:
  - data `requirements.lock:88/:90`;
  - cascor `requirements.lock:63/:65` and `requirements-cpu.lock:129/:133` (the image's lock);
  - canopy `requirements.lock:79/:81`;
  - `juniper-recurrence/juniper-recurrence/requirements.lock:70/:74`.
- **Caps:**
  - observability `<0.5.0`: canopy `pyproject.toml:109`, recurrence `:79` and its client `:41/:46`;
  - service-core `<0.8.0`: data `:110`, cascor `:105`, canopy `:119`, recurrence `:51`, and juniper-ml `pyproject.toml:94` (`[tools]`).
- **Order** (`feedback_semver_beats_consumer_cap_2026-09-05.md`): if a bump crosses a cap, the cap PRs land BEFORE the Release. The lock and floor PRs come after the wheel is on PyPI.

## Traps learned this round

- **Signed commits are single-parent only** (GraphQL `createCommitOnBranch`), so a textual conflict with `main` cannot be merged away. Open a superseding PR from fresh `main`, as #686 → #688 did.
- **The sweeper's arms store the DEFAULT squash body.** Put any waiver trailer (`Allow-Symbol-Loss:`) in a COMMIT body in the range; main-verify's MULTILINE regex finds it there.
- **A CHANGELOG built on a release cut BEFORE update-branch mis-files silently.** The 3-way merge duplicated `## [0.16.0]` with no conflict. Run update-branch first, then push the corrected file.
- **Files move under you.** Re-read the PR head and `main`'s copy before you overwrite a file you pushed earlier.
- **Agents.** An agent the USER stopped cannot be resumed; relaunch it fresh from its WIP. One killed by a usage limit CAN be resumed with `SendMessage`, but only from the session that spawned it.
- **`/tmp` is tmpfs and short of inodes.** It was at 81% at writing and reached 100% this round. Extract only what you need, prune what you extract, and keep probes in `util/ad-hoc/`.
- **Sentry.** In every test run, set these to `""`: `SENTRY_SDK_DSN` (this shell exports it), `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN` and `JUNIPER_CANOPY_SENTRY_DSN`.
- **`pkill -f '<pattern>'` also matches the shell running it**, and kills it.
  - Use `pkill -A -f 'uvicorn.*--port 18797'`; `-A` spares the calling shell.
  - Or bracket one character (`'uvicorn.*--port 1879[7]'`) and run pkill as its own command.
  - A pattern that starts with `-` needs `--` before it.
- **The worktree sandbox's refusals are heuristic.** Refused this round:
  - `$(...)` feeding `git` or `gh`;
  - a `-C` path relative to a `cd`, and sometimes a computed `git -C "$d"`;
  - variables around `sed` or `find`;
  - sometimes, `env -u` inside a compound command;
  - the word "git", in any case, inside a `python3 -c` string or a `for` word list;
  - `bash -c` with computed text;
  - a `for` loop with a variable inside a `gh` argument;
  - `git -C`, or `cd … &&` git, into the shared juniper-ml checkout or into a sibling worktree under `juniper-ml/.claude/worktrees/`. Read files there with `cat`.

  Split into plain commands with absolute paths, or put the logic in a script file. `--commit-body "$(cat f)"` to the pushers IS accepted.

## Worktrees and branches

All the worktrees are under `/home/pcalnon/Development/python/Juniper/worktrees/`. **Remove one only with the owner's go-ahead in your session** (`feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15.md`). Before removing, re-check `git status` and `gh pr view <N> --json state,mergedAt`.

| Worktree | State at writing |
|---|---|
| `juniper-cascor--fix--shortfall-mixed-provenance-and-678-followups--20260924-0235--0e016a7c` | HEAD is #690's head. Keep it until #690 merges and validates. |
| `juniper-canopy--fix--secret-leaks-683-validation--20260924-1333--8917fdac` | #685 has merged. HEAD is the unsigned `4caf9389`, tree-equal to `4a8af2a0`. It lacks the two probe-script commits, so validate `dc5ea02e` from a fresh tree, not from here. See the stray branches in OPEN item 5. |
| `juniper-cascor--fix--bytes-compare-no-500--20260924-1337--ec8b5bdb` | #689 is open. HEAD is the signed local `24103c23`, tree-equal to `97341680`. |
| `juniper-data--fix--bytes-compare-no-500--20260924-1337--1afc3480` | #440 is open. HEAD is the unsigned `5bd5eec5`, tree-equal to `0bee089e`. |
| `juniper-canopy--fix--blank-key-678-followups--20260924-0235--e9053227` | #683 has merged. HEAD `8917fdac` is #683's commit, and the tree is clean. |
| `juniper-ml--fix--sentry-locals-and-bytes-compare--20260924-1337--48fc09e5` | ml#2086 has merged, and the tree is clean. |

- **How to remove one:** `git -C <owning repo> worktree remove <path>`, then `git branch -D <branch>`, then `git worktree prune`.
  - For the juniper-ml worktree, run `git worktree remove <path>` from your own juniper-ml worktree instead.
  - `worktree remove` also deletes ignored `logs/` and `snapshots/`, which are disposable here.
- **Never run** `util/worktree_cleanup.bash`: it pushes and runs `gh pr create`, which recreates deleted remote branches with unsigned commits. **Nor** `util/remove_stale_worktrees.bash`: it has no staleness predicate.
- **Stale branches**, under the same owner gate:
  - the remote `fix/shortfall-mixed-provenance-and-678-followups` (`e452a660`, from the closed #686);
  - the local cascor branches of that name and its `-v2`;
  - canopy's stray `pr-63` and `pr-683`, whose deletion is the owner's call (OPEN item 5).

  #686's commits stay reachable at `refs/pull/686/head`, but deleting its head branch blocks reopening it.

## Verification commands

```bash
gh api graphql -f query='query { a: repository(owner:"pcalnon", name:"juniper-cascor") { p690: pullRequest(number:690) { state isDraft mergeStateStatus headRefOid autoMergeRequest { enabledAt } mergeCommit { oid } } p689: pullRequest(number:689) { state isDraft mergeStateStatus headRefOid autoMergeRequest { enabledAt } mergeCommit { oid } } } b: repository(owner:"pcalnon", name:"juniper-canopy") { p685: pullRequest(number:685) { state headRefOid mergeCommit { oid } } } c: repository(owner:"pcalnon", name:"juniper-data") { p440: pullRequest(number:440) { state isDraft mergeStateStatus headRefOid autoMergeRequest { enabledAt } mergeCommit { oid } } } }'
gh pr list --repo pcalnon/juniper-ml --head docs/handoff-round42-followup-lane --state all --json number,state,mergeCommit   # this file's PR
gh pr view 2089 --repo pcalnon/juniper-ml --json state,mergeCommit   # carries the probe README rows
cd /home/pcalnon/Development/python/Juniper/juniper-ml && python3 -m unittest tests/test_service_fork_drift.py   # 11 OK, 3 skipped; with JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 (siblings pulled): 11 OK
ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep -e shortfall-mixed -e secret-leaks -e bytes-compare -e blank-key-678   # six rows
df -i /tmp
```

## Git status at handoff

- The juniper-ml session worktree `happy-skipping-hollerith` is on branch `worktree-happy-skipping-hollerith`, fast-forwarded to `origin/main` `5af9d722` (#2088).
- Nothing is staged, and nothing tracked is modified.
- Every new file lands in this file's `docs(handoff)` PR, which its author opens before handing off:
  - this file;
  - the new reports in `reports/2026-09-24_defect-register-round-42/`: 12 of this lane's, plus every validation round of this file;
  - the 5 harnesses;
  - the 63 probes;
  - four ad-hoc scripts in `util/ad-hoc/`: `2026-09-24_copy_followup_lane_probe_scripts.py`, `2026-09-24_archive_followup_handoff_validation.py`, `2026-09-24_open_followup_handoff_pr.py` and `2026-09-24_serve_scratch_juniper_data.bash`.
- If the `gh pr list … --head docs/handoff-round42-followup-lane` command prints `[]`, the author did not open the PR. Ask the user.
