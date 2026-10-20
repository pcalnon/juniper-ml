# Lane 14-A — measurement re-creation for the canopy E2E ledger's Phase 14 (item 30, F-CANOPY-069)

You are an independent validator (Lane A of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`:
re-create the observations, do not take the reconciler's word). Work only inside the juniper-ml worktree
`/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/serialized-noodling-cray` and the host state
named below. Record the worktree HEAD sha you review (`git log -1 --format=%H`). Never touch ports 8101, 8202, 8051,
8052, 8053 (the trio is not on this host, but the rule stands). Use ports 8070–8079 for your canopy legs and 8230 for
your cascor leg. Tear every leg down when you finish.

## What Phase 14 claims (read it first)

`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` from `## Phase 14` to the end, and the dated
blockquotes under F-CANOPY-001, -012, -013, -018, -028 and -032 (search `RE-DRIVEN` and `RE-DIAGNOSED`). The
records are under `reports/e2e-canopy-2026-09-02/item30-turing/` (JSON, transcripts, shots). The scripts are
`util/ad-hoc/2026-10-20_*`.

## Re-create, in this order, and compare every figure with the phase's

1. **The dash-version matrix (F-CANOPY-069).** Launch a demo leg under dash 3.3.0 and one under dash 4.4.1, probe
   each, tear each down:

       bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up 8070 demo http://127.0.0.1:9 /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python
       /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -I util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py --base http://127.0.0.1:8070 --label laneA-dash-3.3.0 --out /private/tmp/claude-501/lane14A/dash_matrix.json
       bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash down 8070
       bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up 8071 demo http://127.0.0.1:9 /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python
       ... probe 8071 with --label laneA-dash-4.4.1 ... down 8071

   Expected by the phase: 3.3.0 INERT (3 duplicate ids, 3 renderer errors, 0 Parameters rows, no POST), 4.4.1 ALIVE.
   Also confirm independently, without the probe: `curl -s http://127.0.0.1:<port>/dashboard/_dash-dependencies`
   and count the output ids claimed twice; read `dash/_utils.py` `create_callback_id` in the two venvs and say whether
   the hashing differs; find `validate_callbacks` in the dash 4.4.1 renderer bundle and the unconditional call in
   3.3.0's (`site-packages/dash/dash-renderer/build/dash_renderer.dev.js`).
2. **The demo-leg rows on dash 4.4.1** (leg on 8072, the `-dash44` venv):

       /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -I util/ad-hoc/2026-10-20_item30_fixwave_redrive.py --base http://127.0.0.1:8072 --step f018,f001 --out /private/tmp/claude-501/lane14A/demo.json
       /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -I util/ad-hoc/2026-10-20_item30_fixwave_redrive.py --base http://127.0.0.1:8072 --step f028 --f028-arms early,mid --f028-repeat 2 --out /private/tmp/claude-501/lane14A/demo.json

   Expected: f018 TOAST + CLEAN + RETRACK, no LATCHED; f001 SYNCED; f028's rows pass on their own expectations in
   every arm, and the phase says a pin was discarded in 2 of its 8 drives (once the first pin, once the second). Report
   how many of your 4 arms discard a pin and, for any that does, quote the writer's firings
   (`arms.<label>.pin_requests_after_reload`: rendered count, checked keys, State) so the mechanism the phase names
   (a table re-render from a stale pin set, persisted by the writer) can be checked against your own data. If none
   discards, say so plainly; the phase's claim rests on its own two.
3. **The service-leg rows** (if you have the time: the entry network takes about 10 minutes to train):

       bash util/ad-hoc/2026-10-20_turing_cascor_leg.bash up 8230 http://127.0.0.1:8073
       bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up 8073 service http://127.0.0.1:8230 /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python
       python3 -I util/ad-hoc/2026-10-20_cascor_leg_prepare_investigating.py --cascor http://127.0.0.1:8230 --max-hidden-units 3 --max-iterations 3 --epochs 800 --out /private/tmp/claude-501/lane14A/prepare.json
       /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -I util/ad-hoc/2026-10-20_item30_fixwave_redrive.py --base http://127.0.0.1:8073 --cascor http://127.0.0.1:8230 --step f012,f013 --out /private/tmp/claude-501/lane14A/service.json
       bash util/ad-hoc/2026-10-20_turing_cascor_leg.bash down 8230
       /Users/pcalnon/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -I util/ad-hoc/2026-10-20_item30_fixwave_redrive.py --base http://127.0.0.1:8073 --cascor http://127.0.0.1:8230 --step f032 --out /private/tmp/claude-501/lane14A/service.json
       bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash down 8073

   Expected: f012 all four targets land, B and C rejected `got (N, 1)`, F the count message; f013 real index and count
   (if the first append is refused at the cap, remove then append, as run 1 → run 2 did); f032 RENDERED with the
   store FILLED. Note: with a 3-hidden-unit network `output_weights` is (5, 2) = 10 values, so the figures differ
   from the phase's (6, 2) = 12; what must match is the shape of each outcome.

## Rules

- Every leg you start, you stop. Check `lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(807[0-9]|8230) '` before you finish.
- The worktree-isolation guard refuses `git -C`, `for` loops over tools, `awk` programs, `$(…)` in command text and
  env prefixes: one plain command per call, interpreters by path.
- Do not edit any file under the worktree. Write your scratch under `/private/tmp/claude-501/lane14A/`.
- Chrome cannot fetch `cdn.jsdelivr.net` on this host; the drivers abort that request. Do not fetch it another way.

## Report (your final message, verbatim is what gets archived)

Verdict first: SOUND / SOUND-WITH-FIXES / UNSOUND for the phase's measurements. Then, per item above: what you ran,
the figures you got, the phase's figures, agree/disagree. Then any figure of the phase's that your data contradicts,
marked MAJOR (changes a disposition, a rating, a count or an item) or MINOR. Then what you could not re-create and why.
