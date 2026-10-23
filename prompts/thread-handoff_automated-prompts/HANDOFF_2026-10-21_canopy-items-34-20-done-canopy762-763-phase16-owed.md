# HANDOFF 2026-10-21 — P2 canopy Lane A: items 34 and 20 are DONE in canopy (canopy#762: the 1-D Patch Weights parse takes spaces, as the manual says; canopy#763: F-CANOPY-065, the WS leg's partition reaches the apply toast, verified live). Phase 16, recording both, is owed. Next: Phase 16, then items 18, 19 and 21, item 27, the Linux host's 25, 28 and 29, the owner's 33 and 26

**Written**: 2026-10-21 by the session in juniper-ml worktree `.claude/worktrees/serene-splashing-wozniak` on host
turing (macOS; no trio; throwaway legs from copies of the E2 tree), at a phase boundary, as its PR was opened.
**Consensus**: none. This handoff and its records were NOT validated by consensus; they are the input to Phase 16's
rounds, which validate them.
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`, authoritative for P2.
Its items 5 and 7 and the owner batch O1–O17 carry over. This file supersedes
`HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md`.
**Merge approval**: the owner granted it for this session ("merge approval granted", 2026-10-21): its two canopy PRs
and this PR. It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (the juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_canopy-items-34-20-done-canopy762-763-phase16-owed.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried: ask before the first merge. First record Phase 16 of
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: item 34 (canopy#762) and item 20 (canopy#763,
F-CANOPY-065), with their own consensus rounds. Then items 18, 19 and 21 (canopy fixes for F-CANOPY-064, -067, -060,
-063 and -066); item 27, a demo leg serving canopy `main`, extended to click through the Live Switch modal; items 25,
28 and 29 on the Linux host; item 33 (the owner's); item 26's second step after O17; the canopy release
(owner-gated) now carries canopy#760 to #763.

**Completed:**

- **The predecessor's item 1**: juniper-ml#2303 (Phase 15) merged 2026-10-21T07:30:02Z as `398c5f5d`. At 08:35Z,
  past the one-hour re-check, `origin/main` (`fcaf5e0c`) still printed triage 80 / 63 / 1 / 2 / 14 with no open P0
  line and one `## Phase 15` header.
- **Item 34, canopy#762**, merged 2026-10-21T09:08:37Z as `11e8de90`. canopy#761's manual sentence ("Values are floats
  separated by commas or spaces", `docs/USER_MANUAL.md:500`) was wrong for `output_bias`, `hidden_unit_weights` and
  `hidden_unit_bias`. The item's second route was taken: `_parse_float_list` now splits on whitespace too, as its own
  docstring said, so the manual is unchanged and true for every target. Append Hidden Unit's weights field, the
  parser's other caller, takes spaces too. No accepted input changes meaning, because `float()` refuses a token with
  whitespace inside it. Tests: `TestParseFloatList` (+3) and the new
  `src/tests/unit/frontend/test_patch_values_manual_separators.py`, which reads the manual's sentence and drives
  `_resolve_patch_values` for every target with commas and with spaces. With the parent's parser swapped back in, 8 of
  the new tests fail. CI's unit selector on turing: 7973 passed, 10 skipped, 2 failed, both E-REQ (turing's
  `requests` 2.32.5), red on `main` too. Every CI check on canopy was green.
- **Item 20, canopy#763** (F-CANOPY-065), merged 2026-10-21T09:28:16Z as `e30010c9`. `_apply_params_hot` unwraps the `/ws/control` ack
  (`_unwrap_control_ack`: `data.result` of a `command_response` frame), and `apply_params` reads each leg's partition
  from that leg's own result and unions them. Reading `data.result` alone would not have fixed a mixed Apply, because
  the REST envelope's `data` replaces the WS frame's in the merge. Corrected along with it: the extractor's "the WS ack
  carries it flat" docstring, the N5 fake (`test_n5_apply_params_ux.py`, now the real frame), the "default off"
  comment on `use_websocket_set_params`, and the Phase C suite's "(default)" docstring. New
  `TestF065BothLegsPartitionsReachTheToast` covers A-N2's mixed Apply through the real `apply_params`, a WS-only Apply,
  the toast ("Applied 4 parameter(s); 1 skipped: nn_max_total_epochs (not-updatable)") and the unwrap. With the
  parent's adapter swapped back in, 7 fail.
  - **Live** (`reports/e2e-canopy-2026-09-02/item20-turing/README.md`): one throwaway cascor 0.12.0 leg on 8230 and
    canopy service legs on 8062, one at a time, given A-N2's five keys. `main` `aeeaf29b` answered
    `["cn_training_iterations"]` with no `skipped_detail`, both during the run and after it. The fix answered the four
    applied keys and `nn_max_total_epochs (not-updatable)`.
  - **The o3 instrument** (`util/ad-hoc/2026-10-04_phase10_o3_rederive.py`) gained a fifth arm that drives the tree's
    real `apply_params`, as item 20 asked. It prints A-N2's answer on `main` and both partitions on the fix. Its four
    Phase 10 arms are unchanged.
- **This session's PR** carries this file, the records under `reports/e2e-canopy-2026-09-02/item20-turing/`, the two
  scripts, the SUPERSEDED banner on the predecessor, the Lane A pointer in the parent and the P2 row of
  `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`. Find it with
  `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-items-34-20 --state all`. **The ledger is not
  changed**: triage still prints 80 / 63 / 1 / 2 / 14 until Phase 16.

**Remaining, in order:**

1. **Land this session's PR** if it has not merged: `python3 util/wait_for_checks.py --pr N`, query
   `reviewThreads(isResolved:false)`, ask the owner, then `python3 util/safe_merge.py --pr N --execute`.
2. **Phase 16 of the ledger** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`), through the
   consensus procedure (`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`; Phase 15
   is the model: freeze a local commit, then validator lanes, a replayable `…_phase16_ledger_round<R>_corrections.py`
   per round, and reports archived under `reports/e2e-canopy-2026-09-02/consensus/`).
   - Record item 34: done, canopy#762. Phase 13's manual rule files a finding only if it ships unfixed, so none is
     filed. Re-check that the manual's Patch Weights bullet still says "commas or spaces" at the merge commit.
   - Record item 20: F-CANOPY-065 fixed by canopy#763, and decide its disposition. FIXED moves triage to
     80 / 64 / 1 / 2 / 13 with 3 open P1 (F-CANOPY-064, F-CASCOR-001, -002). The triage reads `FIXED` only in a
     header's last 170 characters. The rating question (O17's first limb) stays the owner's, but it no longer moves an
     open count.
   - Record item 19's partial: the sweep's N5 WS-ack fake is corrected (by canopy#763). N6's fixture (item 18),
     F-CANOPY-060's fixture and F-CANOPY-063's quote remain.
   - Correct Phase 10's item 20 text if the round agrees: its "o3 instrument" ask is done.
   - Lanes must read git OBJECTS of a frozen local commit. turing has no signing, so the freeze commits stay local and
     unsigned (never push them), and the landing goes through the API. Build every shared file from a fresh
     `origin/main` copy, as `util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py` did.
3. **Items 18, 19 and 21** (canopy code; the ledger's Phase 10 "Still owed" has their full text, found by
   `grep -n '^18\. \*\*F-CANOPY-064'`). Item 18 first decides F-CANOPY-067's rating in three drives on unfixed `main`,
   one of them with the recurrence leg up. Item 19 is F-CANOPY-060 (cut only at `" To accept it,"`; word the options
   for a cap refusal) and F-CANOPY-063 (re-sync or stop quoting cascor's sentence), plus item 16's fixture sweep. Item
   21 is F-CANOPY-066, with the selection arc's A1-iii. Canopy PRs, each verified on a leg.
4. **Item 27** (F-CANOPY-055/-025's Live Switch allow arm, extended to click the enabled switch, Accept, and read
   `live-switch-progress-alert`; the restart confirm likewise). The leg must serve canopy `main`. Use
   `~/.local/state/juniper/turing-e2/trees/juniper-canopy-main-e30010c9`: it is `-f065` with `-item34`'s three files
   copied in, and it is proved equal to `main` `e30010c9` on all 19 files canopy#760 to #763 touch
   (`reports/e2e-canopy-2026-09-02/item20-turing/blob_check_main_e30010c9.json`, ALL MATCH; `requirements.lock`, the
   lockfile workflow's, is the one that differs). `-f028` lacks #762 and #763, `-item34` lacks #763, and `-f065` lacks
   #762's three files. If `main` has moved, re-run the check with `--ref main`. Launch with
   `bash util/ad-hoc/2026-10-20_f069_fix_leg.bash up 8062 ~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python ~/.local/state/juniper/turing-e2/trees/juniper-canopy-main-e30010c9/src +tree-main e30010c92c0763788c2095c03e23ea66b7d657f3`.
   The driver recipe is unchanged; see the predecessor's item 4.
5. **Items 25 and 28** on the Linux host, against the trio (ledger Phase 12). **Item 29**, the Linux host.
6. **Item 33** (owner): bring turing's E2 canopy env to canopy's floor (`dash>=4.0.0`); the predecessor's item 6 has
   the recipe.
7. **Item 26's second step** once the owner rules (O17).
8. **The canopy release** (owner-gated, P4). It now ships canopy#760 (F-CANOPY-069), #761 (F-CANOPY-028), #762
   (item 34) and #763 (F-CANOPY-065). Item 34 no longer holds it. PyPI's canopy 0.9.0 (2026-10-17) has none of them.
   Check with `gh release list --repo pcalnon/juniper-canopy --limit 2`.
9. **Cleanup on turing**, after Phase 16 has cited them: the trees `~/.local/state/juniper/turing-e2/trees/juniper-canopy-item34`
   and `-f065` (copies; no `.git`), and the predecessor's `-f069` and `-f028`. Keep `-main-e30010c9` until item 27
   has run on it. The predecessor's worktree
   `sequential-coalescing-boot` still holds three local unsigned freeze commits: never push its branch; remove it
   through `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`. canopy deleted the fix branches on
   merge.
10. Then the parent's items 5 and 7, and the owner batch O1–O17.

**Traps learned (this session):**

- **cascor 0.12.0 refuses a start with no data**: `POST /v1/training/start` with `{}` answers 409 "Training cannot be
  started: Training data not provided". The "spiral fallback" in `util/ad-hoc/2026-10-20_turing_cascor_leg.bash`'s
  header is stale. Start with `inline_data` (the item 20 leg used a 2x1 XOR set, eight rows, `epochs: 50`). Also,
  `update_params` raises "No network exists — create a network first", so set_params needs that run first.
- **The canopy launcher truncates its log on every `up`** (`>"$LOG"`). Copy a leg's lines before the next `up` on
  that port.
- **Service legs**: `util/ad-hoc/2026-10-21_f065_service_leg.bash up <port> <python> <tree-src> <cascor-url> <suffix>
  <base-sha>`. The cascor leg allows one canopy origin on `/ws/control`, so legs for different trees share one port
  in turn.
- **A test class under canopy's `src/tests/integration/` must be marked `integration`.** CI's integration lane runs
  `-m "integration and …"` over that directory, and the unit lane never collects it, so a class there marked `unit`
  runs in no lane at all.
- **turing's Wi-Fi measured SNR 9 dB** (5 GHz ch 149) at about 08:45Z. The memory's recipe held anyway: open the PR with
  the small files, then push the 419 KB CHANGELOG through `util/ad-hoc/2026-10-17_push_signed_with_retry.py`. It
  landed on attempt 1 both times, in about 6 s.
- **Two canopy PRs that both append to `[Unreleased]` conflict.** Land the first, run
  `gh api -X PUT repos/pcalnon/juniper-canopy/pulls/N/update-branch -f expected_head_sha=<head>` on the second (GitHub
  signs the merge commit), then build its CHANGELOG from the branch head and push it.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your worktree>   # or the Linux host's path
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-items-34-20 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7   # 80 / 63 / 1 / 2 / 14 until Phase 16; open P1 4; open P2 10
gh pr view 762 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED 11e8de90
gh pr view 763 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED e30010c9
gh release list --repo pcalnon/juniper-canopy --limit 2   # v0.9.0 Latest (2026-10-17) means item 8 is still owed
gh api -H 'Accept: application/vnd.github.raw' repos/pcalnon/juniper-canopy/contents/docs/USER_MANUAL.md | grep -c 'Values are floats separated by commas or spaces'   # 1 (item 34: the sentence canopy#762 made true)
python3 -I -c "import json; print(json.load(open('reports/e2e-canopy-2026-09-02/item20-turing/live_set_params_f065_fix.json'))['skipped_detail'])"   # [{'key': 'nn_max_total_epochs', 'reason': 'not-updatable'}]
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8101|8202|8051|8052|8053|80[5-9][0-9]|8222|8230) '   # on turing: nothing; on the Linux host: the trio up (never touch it)
```

## Git state

- **juniper-ml:** branch `docs/canopy-e2e-items-34-20`, landed from turing through the API as signed commits. The
  worktree `serene-splashing-wozniak` holds the same files uncommitted.
- **juniper-canopy:** `main` `e30010c9` (canopy#763 on canopy#762 `11e8de90` on `aeeaf29b`); both squash-merged,
  their branches deleted by the repo. Open PRs: dependabot only (#752 to #758) when this was written.
- **Services:** none left on this host. The cascor leg on 8230 and the canopy legs on 8062 were stopped by pidfile.

## Changed by this session

- **Created:**
  - this file;
  - `util/ad-hoc/2026-10-21_f065_service_leg.bash`;
  - `reports/e2e-canopy-2026-09-02/item20-turing/` (`README.md`, `live_set_params_main_aeeaf29b.json`,
    `live_set_params_f065_fix.json`, `live_set_params_main_aeeaf29b_after_run.json`, `o3_rederive_main_aeeaf29b.txt`,
    `o3_rederive_f065_fix.txt`, `canopy-8062_main_after_run.log.txt`, `blob_check_main_e30010c9.json`).
- **Modified:**
  - `util/ad-hoc/2026-10-04_phase10_o3_rederive.py`: the fifth arm, `real_apply_params`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md`:
    the SUPERSEDED banner;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`: the Lane A pointer;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: the P2 row.
- **In juniper-canopy:**
  - canopy#762: `src/frontend/components/network_editor_panel.py`,
    `src/tests/unit/frontend/test_network_editor_panel.py`,
    `src/tests/unit/frontend/test_patch_values_manual_separators.py` (new) and `CHANGELOG.md`.
  - canopy#763: `src/backend/cascor_service_adapter.py`, `src/settings.py`,
    `src/tests/integration/test_n5_apply_params_ux.py`, `src/tests/unit/test_phase_c_set_params_adapter.py` and
    `CHANGELOG.md`.
- **Outside the repo**: in auto-memory, `MEMORY.md` (the canopy line) and `canopy-e2e-arc-state.md`. On turing, the
  trees `~/.local/state/juniper/turing-e2/trees/juniper-canopy-item34`, `-f065` and `-main-e30010c9` (item 27's).
