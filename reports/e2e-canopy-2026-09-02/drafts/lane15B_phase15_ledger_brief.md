# Lane 15-B — adversarial analysis review of the canopy E2E ledger's Phase 15 (items 32 and 31: F-CANOPY-069 and F-CANOPY-028 FIXED), and of its handoff

You are an independent validator (Lane B of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`:
review the conclusions against the evidence; assume every sentence may be wrong until you have checked it). Work
only inside the juniper-ml worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sequential-coalescing-boot`
(read-only; write scratch under `/private/tmp/claude-501/lane15B2/`). Record the worktree HEAD sha you review. Do
not start any service. The worktree-isolation guard refuses `git -C`, `for` loops over tools, `awk` programs, `$(…)`
in command text and env prefixes: one plain command per call, interpreters by absolute path.

**This is round 2, and you are its only lane.** Round 1's adversarial lane was cut off by an API usage-credit error
before it wrote anything (this brief was revised for the re-run; the first version pointed at the round-1 freeze).
The artifact you review is the round-2 freeze: round 1's corrections are applied, and its consensus record is in
the phase. Three placeholders are deliberate and are filled after your round: `ROUND2_RECORD_PLACEHOLDER` (the
ledger's Consensus record), `ROUND2_SUMMARY_PLACEHOLDER`, `ROUND3_ITEM_PLACEHOLDER` and `ROUND2_FREEZE_PLACEHOLDER`
(the handoff). Do not report them as defects; do report anything else that is true only at landing and is not marked.

## What to review

1. `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` from `## Phase 15` to the end: "Who, and from
   what", "Item 32", "Item 31", "What this phase cannot support", "Consensus record", "Matrix effect and counts",
   "Still owed".
2. The two rewritten headers and dated blockquotes: F-CANOPY-069 (search `**F-CANOPY-069 —`, then
   `**FIXED (2026-10-20, Phase 15, item 32`) and F-CANOPY-028 (search `**F-CANOPY-028 —`, then
   `**FIXED (2026-10-20, Phase 15, item 31`). For each: does the blockquote's every figure appear in the record it
   cites? Is FIXED the disposition the evidence supports? Does the header's last 170 characters carry the token
   `python3 -B util/ad-hoc/e2e_finding_triage.py` reads (`FIXED`), and its first severity token the intended one
   (P0 for -069, P1 for -028)?
3. `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: M-PARAMETERS-06's cell.
4. **The handoff**, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md`,
   the SUPERSEDED banner on `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`, the pointer in
   `HANDOFF_2026-10-03_canopy-consolidated.md` (search `Phase 15 (2026-10-20`) and the P2 row of
   `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`. The owner asked for a handoff that "includes all
   remaining tasks and is verified": weigh it as the document a new session will act on with no other context.

## The evidence to check against

- Records: `reports/e2e-canopy-2026-09-02/item32-turing/` (`pair_members.json`, labels `dash-4.4.1-571743db`,
  `dash-3.3.0-f069fix`, `dash-4.4.1-f069fix`; `lane15A_pair_members.json`, round 1's Lane 15-A, labels `lane15A-*`;
  `dash_version_matrix_fix.json`; the four `blob_check_*.json`) and `item31-turing/*.json` with `logs/*.log` (the
  driver's `f028.arms.<label>.verdicts` and `pin_requests_after_reload`; the `forced_rebuild` field in forced arms;
  `lane15A_*.json` are round 1's Lane 15-A). Read them with python; they are large.
- Round 1's reports: `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase15_round1.md`, and
  the pass that applied them, `util/ad-hoc/2026-10-21_phase15_ledger_round1_corrections.py`. Check that the round-1
  consensus record says what those reports say, no more.
- The canopy fixes as merged: `gh pr view 760 --repo pcalnon/juniper-canopy --json files,mergeCommit,body` and the
  same for 761; `gh api -H "Accept: application/vnd.github.raw" "repos/pcalnon/juniper-canopy/contents/<path>?ref=main"`
  for any file. The fix trees on this host: `/Users/pcalnon/.local/state/juniper/turing-e2/trees/juniper-canopy-f069`
  and `-f028` (and the parent, `…/juniper-canopy`, canopy `main` `571743db`). The apply scripts
  `util/ad-hoc/2026-10-20_f069_apply_fix.py` and `2026-10-20_f028_apply_fix.py` carry the exact edits.
- dash: `/usr/local/miniforge3/envs/JuniperCanopy1/lib/python3.14/site-packages/dash/` (3.3.0) and
  `/Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/lib/python3.14/site-packages/dash/`
  (4.4.1): `_callback.py` (`running` on a regular callback), `dash-renderer/build/dash_renderer.dev.js`
  (`handleServerside`: `sideUpdate(running.running …)` at request start, `completeJob()` → `runningOff` before
  `finishLine`), `_callback_context.py` (`triggered_prop_ids`), `_utils.py` (`create_callback_id`).
- canopy's CI for both PRs: `gh pr checks 760 --repo pcalnon/juniper-canopy`, `gh pr checks 761 …`; the lockfile
  workflow's commit on #760's branch (`gh api repos/pcalnon/juniper-canopy/pulls/760/commits`); canopy's releases
  (`gh release list --repo pcalnon/juniper-canopy --limit 3`).
- conda-forge: `curl -s https://api.anaconda.org/package/conda-forge/dash` (the 4.4.1 build string and its
  `depends`), and the same for `comm` and `janus`.
- The arc's earlier handoffs, for the remaining-task check: the Phase 14 handoff (its "Remaining, in order"), the
  parent `HANDOFF_2026-10-03_canopy-consolidated.md` (its items, O1–O17) and the ledger's "Still owed" lists of
  Phases 13, 14 and 15.

## Questions you must answer

- **F-CANOPY-069.** Do the parent's dash 4 records (the phase's run and Lane 15-A's two) say what the blockquote
  says: both members run, the opener first on the phase's run, the Live Switch order inverted on both of Lane 15-A's
  with the alert left open, and "nothing else closes it" (check the alert's `dismissable` and every writer of
  `live-switch-progress-alert.is_open` at `571743db`)? Is the fix the `running=` idiom as dash documents it for
  regular callbacks, and does "`runningOff` is applied before the callback's own outputs in both renderer lines"
  hold in both bundles? Is the F-CANOPY-058 distinction honest (the eviction case)? Is raising the floor to
  `dash>=4.0.0` defensible, and is the counter-position recorded fairly? Are the conda file's changed lines real
  conda-forge builds whose run dependencies the file already satisfies? Is "179 callbacks served" right?
- **F-CANOPY-028.** Is the mechanism as restated (a rebuild re-creates all 22 checkboxes, every one arrives
  "changed"; the old writer merged the rendered set) what `update_parameters_tables`, `_build_table` and the old
  `_merge_pinned_params` show, and what Phase 14's `early#2` request bodies show? Does `_apply_pin_toggle` do exactly
  what the blockquote says, and can a legitimate user action trigger more than one pin input at once (it would then
  be ignored)? Is reading `triggered_prop_ids` through `CallbackContextAdapter` equivalent to
  `dash.ctx.triggered_prop_ids` for pattern-matching ids? The phase says the race was NOT re-created live (0 of 26 on
  the parent, the `forced` arm producing no writer firing): is that stated honestly everywhere, is the account of
  why supported by the records, and is FIXED the right disposition on a fix derived from one recorded loss and
  pinned by a unit test?
- **The manual (item 31b).** Does the new Patch Weights sentence match `_resolve_patch_values` and `_parse_float_rows`?
- **Counts and items.** 80 / 63 / 1 / 2 / 14, 0 P0, 4 P1, 10 P2: run `python3 -B util/ad-hoc/e2e_finding_triage.py`
  and `--open-only`. Is item 33 correctly scoped as the owner's? Does "Still owed" carry every item Phase 14 listed
  with the right status? Round 1 says it "changed one action's parameter" (item 27's tree): is that the right call
  under the procedure's stopping rule?
- **The handoff, as the document a new session acts on.** (a) Is EVERY remaining task of this arc in its
  "Remaining, in order" list, with what it needs to be done (host, tree, interpreter, owner gate)? Check against the
  Phase 14 handoff's list, the parent's items and owner batch, the ledger's Still owed (items 0–33), the canopy
  release, the cleanup of this session's trees, worktree and local commits, and the memory files. Name anything
  missing. (b) Run every command in its "Verification commands" block from the worktree; does each print what its
  comment says? (c) Is every claim in "Completed", "Traps learned", "Git state" and "Changed by this session" true
  against the records, `gh`, and `git status` / `git diff --stat 907b6b3e` in the worktree (the session's base)?
  Does the Changed list name every file the session created or modified? (d) Do the SUPERSEDED banner, the parent's
  pointer and the INDEX row agree with the handoff and the ledger?
- **Secrets and names.** Nothing in the phase, the blockquotes, the handoff or the records prints an environment
  value, a key or the owner's email.

## Rules

- Do not edit any file under the worktree. Do not start any service.
- Never print environment values, keys or the owner's email.

## Report (your final message, verbatim is what gets archived)

Verdict first: SOUND / SOUND-WITH-FIXES / UNSOUND. Then, per question: the claim, the evidence you checked, agree or
disagree, with `file:line` or record paths. Then every defect, marked MAJOR (changes a disposition, a rating, a count,
an item, a remaining task, or a claim the fix rests on) or MINOR, each with the exact sentence to change and the
replacement you propose. Then what you could not check and why.
