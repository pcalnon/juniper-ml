# HANDOFF 2026-10-21 — P2 canopy Lane A: Phase 15 recorded. Items 32 and 31 are DONE: F-CANOPY-069 is FIXED (canopy#760; the dash floor is 4.0.0) and F-CANOPY-028 is FIXED (canopy#761). 0 open P0, 4 open P1, 10 open P2. Next are item 34 and items 18–21 (canopy fixes), item 27, the Linux host's items 25, 28 and 29, item 26's second step and the owner's item 33

> **SUPERSEDED 2026-10-21** by `HANDOFF_2026-10-21_canopy-items-34-20-done-canopy762-763-phase16-owed.md`.
> Its item 1 (juniper-ml#2303 merged 2026-10-21T07:30:02Z, re-checked past the hour), item 2 (item 34: canopy#762,
> the 1-D Patch Weights parse takes spaces) and item 20 of the ledger's Phase 10 list (canopy#763, F-CANOPY-065) are
> done in canopy; recording them is Phase 16, owed. Its items 3 to 10 carry there.

**Written**: 2026-10-21 by the session in juniper-ml worktree `.claude/worktrees/sequential-coalescing-boot` on host
turing (macOS; no trio; throwaway legs from copies of the E2 tree), at a phase boundary, as its PR was opened. The
work ran on 2026-10-20; the consensus and the landing on 2026-10-21.
**Consensus**: round 1 on 2026-10-20, three lanes on the frozen draft. Lane 15-C finished SOUND-WITH-FIXES. An API
usage-credit error cut off Lane 15-A after it had run all five steps (its records were read and landed) and Lane
15-B before it wrote anything. Round 1 changed one action's parameter (item 27's leg must serve canopy `main`).
Round 2 on 2026-10-21, Lane 15-B re-run alone on the corrected freeze: SOUND-WITH-FIXES, five MAJORs (F-CANOPY-028's
account of why its race was not re-created, item 31b's new manual sentence, items 18–21 missing from this list,
item 33's recipe, item 27's scope) and fifteen MINORs, all applied; it changed actions and items.
Round 3 on 2026-10-21, one lane on round 2's corrections and this handoff: SOUND-WITH-FIXES, fourteen MINORs, all
applied; it changed no number, disposition or action, so the review ended there (ledger Phase 15, Consensus record).
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`, authoritative for P2.
Its items 5 and 7 and the owner batch O1–O17 carry over. This file supersedes
`HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`.
**Merge approval**: the owner granted it for this session: its two canopy PRs and this PR ("save, merge, and PR
handoff", 2026-10-21). It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (the juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried: ask before the first merge. Item 34 is a one-sentence canopy manual fix due
before the next canopy release, and items 18–21 are canopy fixes (F-CANOPY-064, -065, -067, -060, -063, -066); item
27 is a demo leg on turing serving canopy `main` (not the E2 tree, which is still `571743db`), the Live Switch
button's allow arm extended to click through the modal; items 25, 28 and 29 need the Linux host and the trio; item 33
is the owner's (turing's E2 canopy env is below canopy's floor); item 26's second step waits on the owner's O17
ruling; the canopy release that ships the fixes is owner-gated.

**Completed:**

- **juniper-ml#2291 merged** 2026-10-20T13:59:34Z: Phase 14 of
  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` and
  `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`.
- **canopy#760 merged** 2026-10-20T18:58:37Z as `fbf01dff` (item 32, F-CANOPY-069). Measured first on a dash 4.4.1
  leg of `571743db`: both members of each colliding pair run on one firing, and the spinner's fate is the order of
  their responses; round 1's Lane 15-A caught the bad order twice on the Live Switch pair, the spinner left open
  (`reports/e2e-canopy-2026-09-02/item32-turing/pair_members.json`, `lane15A_pair_members.json`). The fix:
  `accept_live_switch` and `execute_restart` carry their progress alerts (and the live-swap in-flight store) as
  `running=`; the two opener callbacks and `_open_progress_alert_on_accept_handler` are gone;
  `test_f069_duplicate_callback_outputs.py` pins "no output id is claimed by two callbacks" (7 of 9 fail on
  `571743db`); the floor is `dash>=4.0.0` (`pyproject.toml`, `conf/requirements_ci.txt`) and
  `conf/conda_environment.yaml` pins dash 4.4.1 with `comm` and `janus`. Legs of the fix: ALIVE under dash 3.3.0 and
  4.4.1, one POST per firing, the alert opening on the request and closing on the response
  (`dash_version_matrix_fix.json`, `pair_members.json`). CI's unit-lane selector on turing: 7954 passed, 10
  skipped, 2 failed, the two being E-REQ (turing's `requests` 2.32.5), red on `571743db` too.
- **canopy#761 merged** 2026-10-20T19:34:02Z as `aeeaf29b` (item 31, F-CANOPY-028). The pin-store writer persists a
  user's toggle only (exactly one pin input triggered, read through `CallbackContextAdapter.get_triggered_prop_ids`);
  a rebuilt table (every input triggered at once) writes nothing; `_merge_pinned_params` became `_apply_pin_toggle`;
  `TestF028PinnedParamsPreserved` carries the stale-rebuild case; the manual's Patch Weights sentence states the row
  idiom (item 31b). Drives (`reports/e2e-canopy-2026-09-02/item31-turing/`): the parent lost no pin in 26 (14 at
  driver delays of 2–14 s, every click landing after the second render; 12 on the forced arms, a params-store write
  150 ms after the click, whose table render the renderer holds behind the click's writer, so it cannot stage early#2's
  order);
  the fix lost none in 25 (forced 12, early/mid 6, delays 7), which cannot discriminate; Lane 15-A's 9 agree. The
  race itself was not re-created live; the one live loss on the record stays Phase 14's `early#2`, whose request
  bodies the fix was derived from and which the unit test pins. Item 31b's new sentence is wrong for the three 1-D
  targets (item 34).
- **The ledger's Phase 15** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) records both, the
  F-CANOPY-069 and F-CANOPY-028 headers FIXED with a dated blockquote under each; counts 80 findings, 63 fixed, 1
  accepted, 2 withdrawn, 14 open: 0 P0, 4 P1 (F-CANOPY-064, -065, F-CASCOR-001, -002), 10 P2; new items 33 and 34; an erratum to
  Phase 14's F-CANOPY-069 text (two callback pairs, three ids; no registration overwritten).
- **This session's PR** carries the ledger, the matrix (M-PARAMETERS-06's status cell and M-PARAMETERS-04's Expected cell), this file, the SUPERSEDED banner on
  `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`, the pointer in
  `HANDOFF_2026-10-03_canopy-consolidated.md`, the P2 row of `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`,
  the records under `reports/e2e-canopy-2026-09-02/item32-turing/` and `item31-turing/` (JSON and `logs/`; the
  screenshots stay on turing), the briefs and the consensus reports, and the scripts listed under "Changed by this
  session". Find it with `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase15 --state all`.

**Remaining, in order:**

1. **Land this session's PR** if it has not merged: `python3 util/wait_for_checks.py --pr N`, query
   `reviewThreads(isResolved:false)`, ask the owner, then `python3 util/safe_merge.py --pr N --execute` and read its
   `MERGED` line. Afterwards, and again an hour later (a concurrent whole-file upload can revert a merged change, the
   #2262 trap), on a fresh `origin/main`: `python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7` prints 80 / 63 /
   1 / 2 / 14 with no open P0 line, and `git show origin/main:notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md | grep -c '^## Phase 15'`
   prints 1. A revert costs one replay:
   `python3 -I util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py --out-root <dir>` replays every pass
   (its default list carries them all) and prints the `--add` arguments.
   The consensus review ended at round 3 (it changed no number, disposition or action); nothing of it is owed.
2. **Item 34** (canopy, before the next canopy release): `docs/USER_MANUAL.md:500` says Patch Weights values are
   "floats separated by commas or spaces"; `output_bias`, `hidden_unit_weights` and `hidden_unit_bias` go through
   `_parse_float_list`, which splits on commas, semicolons and newlines only (`0.1 0.2` is refused). Say so in one
   sentence, or make `_parse_float_list` split on whitespace as its docstring claims; a canopy PR with a test.
3. **Items 18–21** (canopy code; Phase 10's list, re-stated by Phase 13; no handoff carried them before this one):
   18 F-CANOPY-064 (P1) and -067 (first decide -067's rating on unfixed `main` in three drives: W8 step 13 after a
   CasCor run with the recurrence leg up, a canopy restart on an idle cascor, and the same restart mid-run; never the
   trio), 19 F-CANOPY-060 and -063 with item 16's fixture sweep, 20 F-CANOPY-065
   (P1 on O17's first limb), 21 F-CANOPY-066 with the selection arc's A1-iii. Canopy PRs, each verified on a leg; the
   ledger's Phase 10 "Still owed" has each item's full text (`grep -n '^18\. \*\*F-CANOPY-064'` finds the first).
4. **Item 27** (F-CANOPY-055/-025's Live Switch allow arm, extended): a demo leg on turing serving canopy `main`
   (`aeeaf29b` or later). The E2 tree is still `571743db`: re-sync it from an up-to-date canopy primary (the owner
   pulls primaries; the worktree guard refuses `git -C`), or use `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028`
   after proving it equal to `main`:
   `python3 -I util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py --repo pcalnon/juniper-canopy --ref main --root ~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028 src/frontend/dashboard_manager.py pyproject.toml conf/requirements_ci.txt conf/conda_environment.yaml CHANGELOG.md docs/USER_MANUAL.md src/tests/unit/frontend/test_f069_duplicate_callback_outputs.py src/tests/unit/frontend/test_live_dataset_switch_handlers.py src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner1.py src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner2.py src/tests/unit/frontend/test_poll_gating.py src/tests/unit/frontend/test_p2_wave_batch_b.py`
   (the files canopy#760 and #761 touch; `requirements.lock`, the lockfile workflow's, is the one that differs). Launch
   `bash util/ad-hoc/2026-10-20_f069_fix_leg.bash up 8062 ~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python ~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028/src +tree-f028 aeeaf29b4f2921bae8c26b61926ca16456ff9b4c`
   (the sixth argument is the base sha the stamp carries; the guard refuses a `CANOPY_LEG_SRC=` prefix). Then
   `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py`, run with
   `~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python -I` (the interpreter the item 31 drives gave
   the driver) and adapted to the chrome channel and the CDN route (`launch`, `_route_cdn` and `new_page` in
   `2026-10-20_item30_fixwave_redrive.py`), samples the switch button's gate with the flag on and a demo run live (record it in F-CANOPY-025's and -055's
   entries). It does not open the modal: extend it to click the enabled switch, Accept, and read
   `live-switch-progress-alert` (on `main` it must close after the swap), and drive the restart confirm likewise.
   That closes F-CANOPY-069's "fired, not clicked".
5. **Items 25 and 28** on the Linux host, against the trio (ledger Phase 12). **Item 29**, the Linux host.
6. **Item 33** (owner): bring turing's E2 canopy env to canopy's floor. Re-sync the E2 tree to canopy `main`
   (`fbf01dff` or later; at `571743db` the floor `dash>=3.0.0` is met by 3.3.0), then
   `~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -m pip install -e ~/.local/state/juniper/turing-e2/trees/juniper-canopy`
   (that venv, a system-site venv over the conda env, holds the editable canopy; pip takes the newest dash 4.x with
   `comm` and `janus`). Once the owner has pulled the canopy primary to `main`,
   `python3 -I util/ad-hoc/2026-10-19_turing_e2_validate_envs.py canopy --phase all` does the re-sync, that install
   (with the `[test,juniper-cascor,observability]` extras) and the lanes the E2 record cites in one run; on this route
   the conda env itself keeps dash 3.3.0, shadowed by the venv. Or rebuild the conda env from a copy of the corrected `conf/conda_environment.yaml`
   re-specified for osx-64 as juniper-ml#2282 did (the file is a linux-64 `conda create --file` export). Then re-run
   the lanes the E2 record cites and record an erratum in the bring-up plan's E2 section; the dash 3.x scratch venvs
   (`JuniperCanopy1-dash304/-dash32/-dash34`) can go.
7. **Item 26's second step** once the owner rules (O17).
8. **The canopy release** that ships canopy#760 and #761, after item 34 (owner-gated, P4). Until it is cut, PyPI's
   canopy 0.9.0 (the newest release, 2026-10-17) keeps the colliding pairs, the Live Switch spinner that can stick
   under dash 4, the pin loss and the `dash>=3.0.0` floor. Check with `gh release list --repo pcalnon/juniper-canopy --limit 2`.
9. **Cleanup on turing**, after the PR merges: the worktree `sequential-coalescing-boot` holds three local unsigned
   freeze commits (round 1 `6f933d07`, round 2 `f65541a5`, round 3 `71417d33`): never push its branch;
   remove the worktree through `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` (owner, or a
   later session). Its untracked `reports/e2e-canopy-2026-09-02/item31-turing/shots/` (the last arm's three
   screenshots; each arm overwrote them) goes with it unless copied out. The fix trees
   `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f069` and `-f028` can go once item 27 has its own tree.
   canopy deleted both fix branches on merge.
10. Then the parent's items 5 and 7, and the owner batch O1–O17 (ledger item 22, O9's design question, is the
    parent's C4).

**Traps learned:**

- **turing has no signing**: land through `util/open_signed_pr.py` and `util/push_signed_commit.py` (one large file
  per commit). Build every shared file from a fresh `origin/main` copy:
  `util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py` replays the apply and round passes and
  byte-checks the result against the worktree.
- **`requirements.txt`, `requirements_ci.txt` and `conf/requirements.txt` are git symlinks** resolving to
  `conf/requirements_ci.txt`; root `conda_environment.yaml` is one into `conf/`. The contents API reports a symlink as
  a `file` whose `sha` is the link's own blob (sha1 of the target path) while serving the target's content, so a blob
  check "mismatches" on them. Edit and upload the target; a whole-file upload to the link's path would replace the
  link with a file.
- **The lockfile workflow pushes a signed commit to a canopy PR branch** after a `pyproject.toml` change (canopy#760
  got one re-resolving `requirements.lock`). Pin `util/push_signed_commit.py`'s
  `--expected-head` on the PR's current head (`gh pr view N --json headRefOid`), not on your last push;
  `safe_merge.py` (which has no such flag) merges the head CI passed on.
- **canopy's `addopts` carries `-q`**; a second `-q` hides pytest's summary line. Count the dots, or drop yours.
- **flake8-simplify crashes under Python 3.14** (`ast.Str`), so canopy's src flake8 profile cannot run in the E2
  env; pyflakes, pycodestyle and the tests profile run, and CI's pre-commit lanes are the judge.
- **`dash_clientside.set_props` fires callbacks for a component inside a closed modal**, which a click cannot reach;
  that is how the two F-CANOPY-069 surfaces were driven without their gates.
- **The driver's click lands seconds after its recorded pin delay**: `second_pin_at_s_after_reload` is taken before
  three page evaluates, a log line and a screenshot of a page still loading, so at every delay given the click came
  after the second table render (each click's writer read the new pin checked after the rebuild had re-created it
  unchecked). The table render a params-store write after the click requests (the forced arms) is held
  behind the click's writer by the renderer (the pin store is the writer's Output and the render's Input), so it
  cannot stage early#2's order, which needs the rebuild
  requested before the click's writer. Give every driver run its own `--out`.
- **`~/.local/state/juniper/turing-e2/legs/serving-commit` still reads `571743db`**, and
  `2026-10-20_turing_canopy_leg.bash` stamps it on `/v1/health` whenever no sha is passed. After a re-sync of the E2
  tree (items 27 and 33), launch through `2026-10-20_f069_fix_leg.bash` with its sixth argument, or rewrite that file
  only after the blob check prints ALL MATCH for the new commit.
- **An API usage-credit error stops validator lanes mid-run, and their legs keep running.** After a lane dies, check
  `lsof` on its ports and stop its legs by pidfile (`… down <port>`; Lane 15-A's leg on 8084 ran for nine hours), and
  read its scratch (`/private/tmp/claude-501/lane15*/`) before re-spawning it: Lane 15-A had run every step.
- **The archive tool takes a lane's LAST text**, and a lane cut off mid-run ends with the error string.
  `--marker "[SYSTEM NOTIFICATION - NOT USER INPUT]"` splits at the lane's first background-task notification and
  recovers the status it wrote before it.
- **The guard refuses** `for` loops over `$p/bin/python`, `awk` programs, `$(…)` in command text, env prefixes and
  compound commands naming `.github/` paths; one plain command per call, interpreters by path, logic in a script.
- **A dash 3.x venv is below canopy's floor now**; so is the E2 env (item 33). A leg from it runs dash 3.3.0 on a
  tree that excludes it.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your worktree>   # or the Linux host's path
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase15 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7   # 80 / 63 / 1 / 2 / 14; open P1 4; open P2 10; no open P0 line
python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c '^OPEN   P1 '   # 4
grep -c '^## Phase 15' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md   # 1
gh pr view 760 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED fbf01dff
gh pr view 761 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED aeeaf29b
gh release list --repo pcalnon/juniper-canopy --limit 2   # v0.9.0 Latest (2026-10-17) means item 8, the canopy release, is still owed
python3 -I -c "import json; m=json.load(open('reports/e2e-canopy-2026-09-02/item32-turing/dash_version_matrix_fix.json')); print({k: v['verdict'] for k, v in m.items()})"   # two ALIVE
python3 -I -c "import json; m=json.load(open('reports/e2e-canopy-2026-09-02/item32-turing/lane15A_pair_members.json')); print({k: v['pairs']['live_switch']['alert_after'].get('present') for k, v in m.items()})"   # True on the two parent labels (the stuck spinner), False on the fix
ls ~/.local/state/juniper/turing-e2/venvs/   # on turing: JuniperCanopy1{,-dash304,-dash32,-dash34,-dash44}, JuniperCascor1, JuniperData
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8101|8202|8051|8052|8053|80[5-9][0-9]|8222|8230) '   # on turing: nothing; on the Linux host: the trio up (never touch it)
```

## Git state

- **juniper-ml:** branch `docs/canopy-e2e-phase15`, landed from turing through the API as signed commits. The
  worktree `sequential-coalescing-boot` holds the same files plus the three local unsigned freeze commits the
  consensus rounds reviewed (`6f933d07`, `f65541a5`, `71417d33`); they never leave the host.
- **juniper-canopy:** `main` `aeeaf29b` (canopy#761 on canopy#760 `fbf01dff` on `571743db`); both squash-merged, both
  branches deleted by the repo. The fix trees `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f069` and
  `-f028` are copies of the E2 tree with the apply scripts run (no `.git`); `-f028` equals canopy `main` except
  `requirements.lock`.
- **Services:** none left on this host. Lane 15-A's leftover leg on 8084 was stopped by pid on 2026-10-21. The
  scratch venvs and the legs' logs under `~/.local/state/juniper/turing-e2/legs/` remain.

## Changed by this session

- **Created:**
  - this file;
  - `util/ad-hoc/2026-10-20_f069_pair_members_probe.py`, `util/ad-hoc/2026-10-20_f069_apply_fix.py`,
    `util/ad-hoc/2026-10-20_f069_fix_leg.bash`, `util/ad-hoc/2026-10-20_f028_apply_fix.py`,
    `util/ad-hoc/2026-10-20_item31_f028_drives.bash`, `util/ad-hoc/2026-10-20_item31_f028_drives_pass2.bash`,
    `util/ad-hoc/2026-10-20_phase15_items31_32_apply.py`,
    `util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py`,
    `util/ad-hoc/2026-10-21_phase15_ledger_round1_corrections.py`,
    `util/ad-hoc/2026-10-21_phase15_ledger_round2_corrections.py`,
    `util/ad-hoc/2026-10-21_phase15_ledger_round3_corrections.py`;
  - `reports/e2e-canopy-2026-09-02/item32-turing/` (`pair_members.json`, `dash_version_matrix_fix.json`, four
    `blob_check_*.json`, `lane15A_pair_members.json`, `lane15A_dash_matrix.json`);
  - `reports/e2e-canopy-2026-09-02/item31-turing/` (seven driver records, two `lane15A_*.json`, and their `logs/`; the
    screenshots under `shots/` are LFS PNGs, untracked, and stay on turing);
  - `reports/e2e-canopy-2026-09-02/drafts/lane15{A,B,C}_phase15_ledger_brief.md` (15-B's revised in place for its
    round-2 run) and `lane15R3_phase15_ledger_brief.md`;
  - `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase15_round1.md`,
    `2026-10-21_validator_reports_phase15_round2.md` and `2026-10-21_validator_reports_phase15_round3.md`.
- **Modified:**
  - `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py`: the `delay<N>`, `forced` and `forcedearly` f028 arms,
    `--f028-forced-gap-ms`, the `LOST_B` verdict;
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 15; the headers of F-CANOPY-069 and
    F-CANOPY-028 and a dated blockquote under each; an erratum to Phase 14's F-CANOPY-069 text (two callback pairs,
    three ids; no registration overwritten);
  - `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: M-PARAMETERS-06's status cell and
    M-PARAMETERS-04's Expected cell;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`: the Lane A pointer;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: the P2 row;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`:
    the SUPERSEDED banner.
- **In juniper-canopy** (canopy#760, #761): `src/frontend/dashboard_manager.py`, `pyproject.toml`,
  `conf/requirements_ci.txt`, `conf/conda_environment.yaml`, `CHANGELOG.md`, `docs/USER_MANUAL.md`,
  `src/tests/unit/frontend/test_f069_duplicate_callback_outputs.py` (new), `test_live_dataset_switch_handlers.py`,
  `test_dashboard_manager_gate_coverage_inner1.py`, `test_dashboard_manager_gate_coverage_inner2.py`,
  `test_poll_gating.py`, `test_p2_wave_batch_b.py`; `requirements.lock` by the lockfile workflow. Comments on
  canopy#760 (the unit-lane count) and #761 (the drives, then a correction of their account).
- **Outside the repo**, in auto-memory: `MEMORY.md` (the canopy line), `canopy-e2e-arc-state.md`.
