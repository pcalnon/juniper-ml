# Lane 15-A — measurement re-creation for the canopy E2E ledger's Phase 15 (items 32 and 31: F-CANOPY-069 and F-CANOPY-028 FIXED)

You are an independent validator (Lane A of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`:
re-create the observations, do not take the reconciler's word). Work only inside the juniper-ml worktree
`/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sequential-coalescing-boot` and the host state
named below. Record the worktree HEAD sha you review (`git log -1 --format=%H`). Never touch ports 8101, 8202, 8051,
8052, 8053 (the trio is not on this host, but the rule stands). Use ports 8080–8089 for your canopy legs. Run ONE leg at
a time (the host has 16 GiB) and tear every leg down when you finish.

## What Phase 15 claims (read it first)

`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` from `## Phase 15` to the end, and the dated
`FIXED` blockquotes under F-CANOPY-069 (search `**FIXED (2026-10-20, Phase 15, item 32`) and F-CANOPY-028 (search
`**FIXED (2026-10-20, Phase 15, item 31`). The records are under `reports/e2e-canopy-2026-09-02/item32-turing/` and
`item31-turing/` (JSON and logs). The scripts are `util/ad-hoc/2026-10-20_*`. The two canopy fixes are merged:
canopy#760 (`fbf01dff`) and canopy#761; the trees the legs serve are copies of the E2 tree with
`util/ad-hoc/2026-10-20_f069_apply_fix.py` and `2026-10-20_f028_apply_fix.py` applied:

- parent: `/Users/pcalnon/.local/state/juniper/turing-e2/trees/juniper-canopy` (canopy `main` `571743db`, proved by blob ids);
- item 32's fix: `…/trees/juniper-canopy-f069` (= `571743db` + #760's files);
- item 31's fix: `…/trees/juniper-canopy-f028` (= #760 + #761's files, i.e. canopy `main` now, minus the lock).

Interpreters: `/Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python` is dash 3.3.0,
`…/venvs/JuniperCanopy1-dash44/bin/python` is dash 4.4.1; both have playwright and drive Chrome 145 through the
`chrome` channel. Legs: `bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up <port> demo http://127.0.0.1:9 <python>`
for the parent and `bash util/ad-hoc/2026-10-20_f069_fix_leg.bash up <port> <python> <tree>/src <stamp-suffix>` for a
fix tree; `… down <port>` for either.

## Re-create, in this order, and compare every figure with the phase's

1. **F-CANOPY-069 on the fix, both dash lines** (item 32). Launch the item 31 tree (it carries #760's fix) under dash
   3.3.0, probe it twice, tear it down; then the same under 4.4.1:

       bash util/ad-hoc/2026-10-20_f069_fix_leg.bash up 8080 /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python /Users/pcalnon/.local/state/juniper/turing-e2/trees/juniper-canopy-f028/src +f069+f028-fix-unlanded
       /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -I util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py --base http://127.0.0.1:8080 --label lane15A-dash-3.3.0-fix --out /private/tmp/claude-501/lane15A/dash_matrix.json
       /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -I util/ad-hoc/2026-10-20_f069_pair_members_probe.py --base http://127.0.0.1:8080 --label lane15A-dash-3.3.0-fix --out /private/tmp/claude-501/lane15A/pair_members.json
       bash util/ad-hoc/2026-10-20_f069_fix_leg.bash down 8080
       ... the same on 8081 with the -dash44 interpreter, labels lane15A-dash-4.4.1-fix ...

   Expected by the phase: ALIVE on both (0 colliding ids, 0 renderer errors, 9 Parameters rows, a POST after the
   theme click), 179 callbacks served, one POST per firing on each pair, the progress alert added when the request
   leaves and removed when the response lands, nothing left open. Also confirm independently: `curl -s
   http://127.0.0.1:<port>/dashboard/_dash-dependencies` and count output ids claimed twice (expect 0) and the
   entries carrying a `running` key (expect 2: the accept callback with two props, the restart callback with one).
2. **F-CANOPY-069 on the parent under dash 4.4.1** (the entry's "first read which member runs"): leg 8082 from the
   parent tree with the `-dash44` interpreter, the pair-members probe with `--label lane15A-dash-4.4.1-parent`.
   Expected: 2 POSTs per firing, the opener's response before the worker's in both pairs, the alert added and gone.
   Report the request and response offsets you see against the phase's (+0.28/+0.64 and +0.28/+2.61 s for restart;
   +0.17/+0.93 and +0.17/+0.71 s for Live Switch) and whether the order could invert on your run.
3. **F-CANOPY-028 on the fix** (item 31): leg 8083 from the item 31 tree under 4.4.1, then

       /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python -I util/ad-hoc/2026-10-20_item30_fixwave_redrive.py --base http://127.0.0.1:8083 --step f028 --f028-arms early,mid,forced --f028-repeat 2 --out /private/tmp/claude-501/lane15A/f028_fix.json

   Expected: every arm SURVIVES (the first pin and the second both in the store after the second pin); in each arm's
   `pin_requests_after_reload` the writer fires three times (the mount render, a second render, the click) and no
   firing carries a state the next firing undoes. The `forced` arm writes the params store 150 ms after the click
   (`forced_rebuild` in the record says so); report whether a fourth writer firing appears in it and what it carried.
4. **F-CANOPY-028 on the parent, the forced arm** (the phase's instrument for the race): leg 8084 from the parent
   tree under 4.4.1, `--f028-arms forced --f028-repeat 3`. Read the phase's figure for the parent's forced arm and
   report yours; if a pin is lost, quote the firing that lost it (rendered count, checked keys, State). If none is
   lost, say so plainly and say what the phase says about it.
5. **The handler on the stale input**, no leg needed:

       cd /Users/pcalnon/.local/state/juniper/turing-e2/trees/juniper-canopy-f069/src && /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python -c "from frontend.dashboard_manager import DashboardManager as DM; ids=[{'type':'param-pin','key':k} for k in ('learning_rate','max_iterations','patience','output_epochs')]; print(DM._merge_pinned_params([True,False,False,False], ids, ['learning_rate','max_iterations']))"
       cd /Users/pcalnon/.local/state/juniper/turing-e2/trees/juniper-canopy-f028/src && ... DM._apply_pin_toggle(ids, [True,False,False,False], ids, ['learning_rate','max_iterations']) ...

   Expected: the old handler returns `['learning_rate']` (the pin gone); the new one returns `no_update`.

## Rules

- Every leg you start, you stop. Check `lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(808[0-9]) '` before you finish.
- The worktree-isolation guard refuses `git -C`, `for` loops over tools, `awk` programs, `$(…)` in command text and
  env prefixes: one plain command per call, interpreters by path.
- Do not edit any file under the worktree. Write your scratch under `/private/tmp/claude-501/lane15A/`.
- Chrome cannot fetch `cdn.jsdelivr.net` on this host; the drivers abort that request. Do not fetch it another way.
- Never print environment values, keys or the owner's email.

## Report (your final message, verbatim is what gets archived)

Verdict first: SOUND / SOUND-WITH-FIXES / UNSOUND for the phase's measurements. Then, per item above: what you ran,
the figures you got, the phase's figures, agree/disagree. Then any figure of the phase's that your data contradicts,
marked MAJOR (changes a disposition, a rating, a count or an item) or MINOR. Then what you could not re-create and why.
