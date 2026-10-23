# Lane 14-B — adversarial analysis review of the canopy E2E ledger's Phase 14 (item 30, F-CANOPY-069)

You are an independent validator (Lane B of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`:
review the conclusions against the evidence; assume every sentence may be wrong until you have checked it). Work
only inside the juniper-ml worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/serialized-noodling-cray`
(read-only; write scratch under `/private/tmp/claude-501/lane14B/`). Record the worktree HEAD sha you review. Do not
start any service. The worktree-isolation guard refuses `git -C`, `for` loops over tools, `awk` programs, `$(…)` in
command text and env prefixes: one plain command per call.

## What to review

1. `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` from `## Phase 14` to the end, including
   the F-CANOPY-069 entry, "What this phase cannot support", "Matrix effect and counts" and "Still owed".
2. The six rewritten headers and dated blockquotes: F-CANOPY-001 (line ~156), -018 (~263), -028 (~3079), -032
   (~3135), -012 (~3868), -013 (~3903); search `RE-DRIVEN` and `RE-DIAGNOSED`. For each: does the blockquote's every
   figure appear in the record it cites? Is the disposition (FIXED / OPEN) the one the evidence supports? Does the
   header's last 170 characters carry the token `python3 -B util/ad-hoc/e2e_finding_triage.py` reads
   (`FIXED` for five, none but `OPEN` for F-CANOPY-028 and -069), and its first severity token the intended one?
3. `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: the eleven cells that changed
   (C2.1-01/-02, C2.9-05, M-METRICS-03, M-WORKERS-02, M-PARAMETERS-04/-05/-06, M-NETWORK-EDITOR-09/-13/-17).
4. `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`,
   the SUPERSEDED banner on `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`, the
   pointer in `HANDOFF_2026-10-03_canopy-consolidated.md` (~line 126-134) and the P2 row of
   `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`.

## The evidence to check against

- Records: `reports/e2e-canopy-2026-09-02/item30-turing/*.json` and `transcripts/*.log` (read them with python,
  they are large; the demo JSON's `f028.arms` holds six arms, `early#2` is the discard with
  `pin_requests_after_reload` and `pin_request_bodies_after_reload`; the service JSON holds `m03`, `f012`, `f013`,
  `f032`, `f032_degraded`).
- Source: the E2 canopy tree `/Users/pcalnon/.local/state/juniper/turing-e2/trees/juniper-canopy` (proved to be
  canopy `main` `571743db` by `reports/e2e-canopy-2026-09-02/item30-turing/e2_tree_blob_sha_check.json`; you may
  re-run `util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py` and you may read the same files through
  `gh api -H "Accept: application/vnd.github.raw" "repos/pcalnon/juniper-canopy/contents/<path>?ref=571743db"`).
  Every `file:line` the phase cites must point at what it says.
- dash: `/usr/local/miniforge3/envs/JuniperCanopy1/lib/python3.14/site-packages/dash/` (3.3.0) and
  `/Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/lib/python3.14/site-packages/dash/`
  (4.4.1): `_utils.py` `create_callback_id`, and `dash-renderer/build/dash_renderer.dev.js` (`computeGraphs`,
  `validateDependencies`, `validate_callbacks`).
- canopy's CI: `gh api repos/pcalnon/juniper-canopy/actions/runs/39339405624/jobs`, the UI job's log
  (`gh run view --repo pcalnon/juniper-canopy --job 118356914745 --log`), `requirements.lock`, `conda_environment.yaml`,
  `conda_environment_ci.yaml`, `pyproject.toml`, `CHANGELOG.md:702` and `:1507` in the E2 tree.

## Questions you must answer

- **F-CANOPY-028.** The phase says a pin was discarded in 2 of 8 drives and names the mechanism. Is the mechanism
  what the `early#2` request bodies show, or is there another reading of a third writer firing with
  `max_iterations` unchecked 1.4 s after the click? Is the first discard (run 1) adequately described as "a
  transcript, not a record"? Is keeping the entry OPEN at P1 the right disposition, or should the rows' own PASS
  carry it? Is the fix direction consistent with `_merge_pinned_params` and `update_parameters_tables` as written?
- **F-CANOPY-032.** The entry closes FIXED with no code change of its own, on the reading that F-CANOPY-027's fix
  wave repaired it. Is that a disposition the ledger's vocabulary allows, and is the reasoning stated honestly? Is
  the degraded arm's "no alert is correct" supported by the 2026-08-27 correction and by the list route's code?
- **F-CANOPY-069.** Is P0 defensible under plan §6.3 (`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360`)
  given that the pip path, the lock and CI are on dash 4? Is the counter-reading recorded fairly? Is the
  mechanism (same `create_callback_id` in every version; dash 3 validates unconditionally; dash 4 only behind
  `config.validate_callbacks`) what the source shows? Are the three colliding pairs and their line numbers right?
  Is "every live drive this ledger records ran under dash 4.2.0" supported by the CHANGELOG lines cited, or is it
  inferred? Is the claim that canopy's own `conda_environment.yaml` produces the inert env correct?
- **F-CANOPY-012, -013, -018, -001.** For each FIXED: does the record carry the figure, and does the figure settle
  the entry's named symptom (not merely the row)? For F-012, is the residue's restatement exact?
- **Counts.** Recompute 80/61/1/2/16 and 1/5/10 from the triage; check the handoff's verification commands
  against what they actually print (run them).
- **What is stated that is inferred**, anywhere in the phase. List each.

## Report (your final message, verbatim is what gets archived)

Verdict first: SOUND / SOUND-WITH-FIXES / UNSOUND. Then each defect, numbered, marked MAJOR (changes a disposition,
a rating, a count, an item or a mechanism claim) or MINOR, with the exact text at fault and the evidence. Then the
claims you checked and found right, briefly. Then anything you could not check and why.
