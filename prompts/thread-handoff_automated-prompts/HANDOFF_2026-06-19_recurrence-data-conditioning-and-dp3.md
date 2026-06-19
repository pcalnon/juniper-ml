# Thread Handoff — recurrence data-conditioning follow-up + DP-3 design/build

**Date**: 2026-06-19
**Author**: Paul Calnon
**Type**: Thread-handoff prompt (continue in a fresh thread; this thread is near full context)
**Origin**: A long, very productive session — juniper-data 0.7.0 + 0.7.1 releases, the recurrence
evaluation extensions (noise sweep + real-data equities_seq), and the DP-3 ranking.

---

## Continue

Resume the **juniper-recurrence** work — **step 2 then step 3** of Paul's 2026-06-19 plan:

1. **Step 2 — data-conditioning follow-up** (task #25). The eval found the Δt-native LMU **fails** on
   `equities_seq`'s **non-stationary RAW next-day-close** target (r²≈−50) while `linear_ridge` wins
   (r² 0.985) — a target-conditioning problem, not a Δt-mechanism flaw. Add a **returns / normalized
   regression-target** option to juniper-data's equities / equities_seq generator (`y_reg` is
   `next_close` in `juniper_data/generators/equities_seq/generator.py`), then **re-bench** equities_seq
   in `juniper-recurrence/bench/` to see whether the LMU recovers with a stationary target. **Perform
   AND document** (update the findings doc) as data for future work.

2. **Step 3 — DP-3 design + build** (task #24, **design-first**). The eval ranked DP-3 (nonlinear /
   torch readout) as *not strictly needed*, but **Paul opted to build it anyway** for the added insight
   / enriched analysis. Start with a **notes/ design doc in juniper-ml** (nonlinear-readout options,
   integration with the LMU memory + `juniper-model-core` crossval, strengths / weaknesses / risks /
   guardrails, **validated by multiple independent sub-agents**), then implement in
   `juniper-recurrence-model`. Do this **after** step 2.

## What shipped this session (all verified)

- **juniper-data 0.7.0** — the Δt synthetic generators (#187/#188) + scaling-meta (#189) → PyPI
  (releases #191/#192; `v0.7.0`).
- **juniper-data 0.7.1** — fixed a packaging defect (0.7.0's wheel omitted `sp500_constituents.csv`,
  so the equities extras were non-functional from pip). PR #193; release `v0.7.1`; **verified the CSV
  ships from PyPI**. Note: merging the PR did **not** publish — the `v0.7.1` GitHub release had to be
  cut manually to trigger `publish.yml` (Paul approved the pypi gate).
- **Recurrence eval extensions** (juniper-recurrence #27, merged) — noise sweep + equities_seq; the
  Δt advantage is **noise-robust** (+57% → +51% → +38% to noise_std=0.25); equities failure as above.
- **Findings v1.1 + DP-3 ranking** (juniper-ml #477, merged) —
  `notes/JUNIPER_RECURRENCE_EVALUATION_FINDINGS_2026-06-18.md` §3.1 + §5.
- **Recurrence `[bench]` pin** → `>=0.7.0` (juniper-recurrence #25, merged).

## Open PRs for Paul (Paul approves all merges + PyPI/deploy gates)

- **juniper-data #194** — v0.7.1 release-notes archive (docs-only).
- **juniper-ml (this PR)** — this handoff prompt.

## Fresh-thread prompt (copy-paste)

```text
Continue the juniper-recurrence work — steps 2 then 3 of the 2026-06-19 plan.

Completed: juniper-data 0.7.0 + 0.7.1 are on PyPI (0.7.1 fixed the equities wheel-packaging
defect — sp500_constituents.csv now ships); the recurrence eval extensions (noise sweep +
equities_seq) and findings v1.1 (notes/JUNIPER_RECURRENCE_EVALUATION_FINDINGS_2026-06-18.md,
§3.1 + §5 DP-3 ranking) are merged.

Step 2 — Data-conditioning follow-up (task #25): the eval showed the LMU fails on equities_seq's
non-stationary RAW next-day-close target (r2~-50, linear_ridge wins) — a target-conditioning
problem. Add a returns/normalized regression-target option to juniper-data's equities/equities_seq
generator (y_reg is next_close in generators/equities_seq/generator.py); re-bench equities_seq in
juniper-recurrence/bench/ to see if the LMU recovers; document in the findings doc. Bump the
recurrence [bench] pin >=0.7.0 -> >=0.7.1 in the same re-bench PR.

Step 3 — DP-3 design+build (task #24, design-first): write a notes/ design doc in juniper-ml for a
nonlinear/torch readout on the LMU memory (options, integration w/ crossval, risks/guardrails,
validated by independent sub-agents), then implement in juniper-recurrence-model. Paul wants DP-3
built for analytical value despite the eval not mandating it.

Key context:
- Bench env: rebuild via `python3 -m venv /tmp/benchenv && /tmp/benchenv/bin/pip install -e
  <recurrence>/juniper-recurrence[bench] juniper-data[equities] pytest build` (/tmp may be reaped).
  Run: `cd <recurrence-worktree> && /tmp/benchenv/bin/python -m bench.run_benchmark`.
- CONVENTIONS (learned the hard way): use feature/** branches (chore/**+docs/** miss the push CI
  trigger; a [skip ci] ancestor from the agents-md-touch-up bot suppresses push/PR runs — squash to
  ONE clean commit). Merging a release PR does NOT publish — you must cut a GitHub release (vX.Y.Z,
  target main) to trigger publish.yml; Paul approves the pypi gate. juniper-data main uses a ruleset
  (BLOCKED shows for non-admins even when green; Paul admin-merges). Archive release notes to
  notes/releases/ per the release convention.
- Worktrees centralized in Juniper/worktrees/. Use git worktrees per repo (feature/** branch).

Verify start state: gh pr view 194 --repo pcalnon/juniper-data --json state ;
curl -fsS https://pypi.org/pypi/juniper-data/0.7.1/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
```

## Verification of start state

```bash
gh pr view 194 --repo pcalnon/juniper-data --json state --jq .state
curl -fsS https://pypi.org/pypi/juniper-data/0.7.1/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
gh pr list --repo pcalnon/juniper-recurrence --state open
```

**Git status at handoff:** all repos on `main`, clean, fast-forwarded; juniper-data #194 open (docs);
this handoff PR open. No in-progress edits.
