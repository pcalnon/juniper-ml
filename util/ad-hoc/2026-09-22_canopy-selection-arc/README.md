# Canopy selection-reachability arc: the session's scratch scripts (verbatim, 2026-09-22/23)

**Project**: Juniper · **Sub-Project**: juniper-ml (ad-hoc) · **Application**: canopy selection-reachability arc ·
**Author**: Paul Calnon · **License**: MIT License

These are the scripts the session and its four sub-agents wrote while working the arc defined by
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md`.
They were authored in the session scratchpad under `/tmp/`, which the script-placement rule
forbids for anything that produces, modifies or analyses repository content. They were copied
here **unmodified**, because they are the evidence behind the PRs below and editing them would
make them something else. Hard-coded worktree paths are the ones the session used; the worktrees
are removed after merge, so pass your own paths when re-running. Each script's docstring carries
its own usage.

Results are **not** restated here. Each subdirectory names the PR whose body records what its
scripts measured.

## `item5-nn-model-mirror/` — juniper-canopy#669 (FR9, the `nn_model` request mirror)

| script | what it does |
|---|---|
| `mutate5.py` | applies one named mutation to the item-5 worktree for the mutation check in #669's body (the refusal never fires; the key forwarded to the backend; Apply Dataset not sending it; the key leaking into the applied store). It restores nothing itself: the session restored from `.bak` copies between runs |

## `registry-repairs/` — juniper-canopy#665 (handoff items 7, 10, 11, 12, 14)

| script | what it does |
|---|---|
| `equities_probe.py` | item 11: import resolution, generator version, param defaults and network reachability for `equities` |
| `equities_measure.py` | item 11 (A-N4): re-measures canopy's `equities` seed at juniper-data `origin/main` (generator 5.0.0) along the service path: `params_class` → `bind_deployment_defaults` → `generate` |
| `equities_stage1.py` | item 11 stage 1: generates canopy's `equities` seed, with and without `normalize_features`, to a six-key NPZ along the service path |
| `equities_stage2.py` | item 11 stage 2: fits `CascadeCorrelationNetwork` on the stage-1 NPZs with the same bounded probe as `../2026-09-10_rank2_cascor_fit.py`, so the numbers compare with 2026-09-10/11 |
| `equities_seq_probe.py` | adjacent to item 11: whether canopy's `equities_seq` evidence ("15,476 train windows of (64, 16)") still holds at 5.0.0 |
| `generator_defaults.py` | item 14: prints every seeded generator's size-determining param defaults at juniper-data `origin/main` |
| `registry_ast.py` | item 10: AST-reads juniper-data's `GENERATOR_REGISTRY` keys and `task_type` |
| `sweep_snap.py` | item 7c: sweeps a canopy tree for present-tense claims of the retired `enabled[0]` snap |
| `restage_seed_probe.py` | the finding behind juniper-canopy#668: builds the restart modal's re-stage payload and the sidebar Apply payload with `requests.post` mocked, showing the modal dropped the registry seed |
| `mutation_check.py` | mutation-checks #665's new and changed guard tests. The anchor must match exactly once, the file is restored in a `finally`, and the restore is verified by hash |
| `symbol_loss_worktree.py` | runs juniper-ci-tools 0.8.0's own symbol-loss classification over `origin/main` → an **uncommitted** worktree, because the CLI needs a HEAD commit |
| `save_work.py` | saves uncommitted edits (a patch plus sha256'd full-file copies) before re-basing onto a moved `origin/main` |
| `verify_reapply.py` | verifies that re-application: untouched files byte-identical, and every file's `+`/`-` line multiset equal to the original patch |
| `moved_paths.py` | per-path drift check before upload (`git log HEAD..origin/main -- <path>`) |
| `move_changelog_block.py` | moves the PR's CHANGELOG bullets to the insertion point the coordinator assigned, so concurrent PRs do not collide |
| `my_pytest.py` | lists pytest processes whose cwd is inside the agent's worktree (read-only) |
| `thread_cpu.py` | samples a pid's per-thread CPU twice, 3 s apart (read-only) |

## `timing-flakes/` — juniper-canopy#664 (WS ordering and fixed-sleep lower bounds)

| script | what it does |
|---|---|
| `ws_repeat_plugin.py` | pytest plugin: repeats selected tests N times and logs every WebSocket `receive_json()`, to catch a `state` frame read before `initial_status` |
| `run_repeat.py` | runs canopy pytest from a worktree's `src/` with that plugin loaded |
| `analyze_seq.py` | summarises a plugin log: per-test outcomes, and per session whether `state` preceded `initial_status` (the CI failure shape) |
| `cpu_burn.py` | CPU-contention generator: N busy processes for T seconds |
| `scan_sleep_count.py` | AST scanner: every fixed `sleep(<number>)` followed by a call/await-count lower-bound assertion. Its wider-scan list of instances #664 left for a follow-up is in #664's body |
| `wait_for_text.py` | blocks until a file contains a marker string, or times out |

## `selection-ui/` — juniper-canopy#671 (Y4, Y8, and the model-table half of Y7)

| script | what it does |
|---|---|
| `probe_aria.py` | which Dash components accept an `aria-describedby` prop; `dbc.Button` 2.0.4 does not, which is why #671's Select is an `html.Button` |
| `extract_js.py` | prints context windows around a needle in a minified JS bundle |

juniper-canopy#671 itself adds `util/ad-hoc/2026-09-22_y4_y7_browser_probe.py` and
`util/ad-hoc/2026-09-22_y4_y7_y8_mutation_check.py` to **juniper-canopy**. Two smaller probes,
`probe_inline.py` and `probe_tabsize.py`, were deleted from the scratchpad before this copy and are
not recoverable here.

## Not retained, and why

- Copies of files that landed in a repo: the G7/Y3 test draft (juniper-canopy#662), two test
  modules (#664), `push_signed_commit.py`'s pristine copy (juniper-ml#2036), and canopy
  source snapshots.
- A 74 KB generated runner that ran juniper-ml's Python regression step locally. It is
  mechanical output of `.github/workflows/ci.yml`'s regression step, which is the authoritative
  list, so regenerate it from there.

## Related, outside this directory

- `../2026-09-23_watch_pr_states.bash`: the `Monitor` event source the session used to shepherd
  the merge queue.
- `../2026-09-23_mutation_check_e2e_contract_helper.py`: the mutation check for
  juniper-canopy#672's NPZ contract-helper tests.
