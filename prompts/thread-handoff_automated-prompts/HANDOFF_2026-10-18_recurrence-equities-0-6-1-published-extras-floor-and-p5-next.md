# Thread Handoff — Recurrence × Equities: recurrence 0.6.1 is on PyPI; the `[recurrence]` floor move and P5 are next

- **Date**: 2026-10-18
- **Session**: "recurrence equities", run on host **turing** in the juniper-ml worktree `.claude/worktrees/unified-knitting-galaxy`
- **Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-18_recurrence-equities-rulings-taken-249-merged-0-6-1-at-pypi-gate.md` (same session, written before the gate)
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, **v1.7.1** (lands with this handoff)

---

## Handoff goal

Continue the arc from plan v1.7.1. **Every M1 publication is on PyPI, including recurrence 0.6.1 with the owner-ruled floors, and every open owner ruling is taken.** The next landing is the juniper-ml `[recurrence]` floor to `>=0.6.1` (an owner ruling, not a decision); after that the P5 work the rulings unblocked, with P2–P4 alongside.

## Completed since the predecessor handoff

- **recurrence 0.6.1 published.** The owner approved the `pypi` gate; run 39152653722 finished green through `Build and Validate`, `Publish to TestPyPI` and `Publish to PyPI`. Verified on the index at 2026-10-18 19:02Z:
  - `info.version` = `0.6.1`; files `juniper_recurrence-0.6.1-py3-none-any.whl` (sha256 `c63ebc79…`) and `juniper_recurrence-0.6.1.tar.gz` (`b8c27e9a…`);
  - `requires_dist` carries `juniper-recurrence-model<0.5.0,>=0.4.0` and `juniper-data-client<0.7.0,>=0.6.0` (the juniper-recurrence#206 floors 0.6.0 shipped without), plus `juniper-service-core<0.8.0,>=0.7.1` and `juniper-model-core[crossval]<0.4.0,>=0.2.0`; the `[torch]` and `[bench-torch]` extras carry `juniper-recurrence-model[torch]<0.5.0,>=0.4.0`.
  - Release `juniper-recurrence-v0.6.1` targets `cad03ed52e9e12180bed3c1ec6751d822fc1bdc5`, published 18:06:41Z; archive juniper-ml#2238 is merged; issue juniper-ml#2227 is closed.
- **Plan v1.7.1**: Status line, M1 row, P1 status row, both Progress 2026-10-18 blocks, the 0.6.1 ruling line and the 2026-10-10 floors dependency note record the publication; change-log row added.
- Everything in the predecessor's "Completed this session" list stands: the owner rulings (plan "Ruled 2026-10-18, turing deploy-smokes session"), juniper-deploy#249 merged, juniper-ml#2234 / #2238 / #2239 merged, juniper-canopy#751 and juniper-deploy#250 filed, juniper-canopy#738 / #702 annotated, Compose v5.6.0 at user level on turing.

## Remaining work (in order)

1. **juniper-ml `[recurrence]` floor to `juniper-recurrence>=0.6.1`** (owner ruling of 2026-10-18; no further approval needed for the PR, merge approval still is). Lockstep files as in juniper-ml#2232: `pyproject.toml`, `tests/test_pyproject_extras.py`, `README.md`, `AGENTS.md` (the extras table), `docs/QUICK_START.md`, `docs/REFERENCE.md`, `CHANGELOG.md`. Keep the model floor `>=0.3.0` and the data-client floor `>=0.5.0` (the extras ruling kept them; recurrence 0.6.1's own floors do the forcing). Pre-flight against real PyPI on Python 3.12, 3.13 and 3.14 with `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py` before opening the PR; `[recurrence]` resolved 32 packages for #2232, expect the same set with recurrence 0.6.1 and model 0.4.0 / data-client 0.6.0 forced. Check first that no concurrent session has an open PR touching `pyproject.toml` (`gh pr list --repo pcalnon/juniper-ml --search "pyproject"`).
2. **Owner: whether the Compose / Helm recurrence pin follows to 0.6.1** (juniper-deploy; still open on the plan's M1 row). If yes, it is a one-line pin bump in each of the two files #249 touched, plus the GHCR image, which the recurrence publish workflow does not build — check `juniper-recurrence/.github/workflows/` for the image workflow and whether a `0.6.1` image exists before pinning.
3. **Remove the merged juniper-deploy worktree** (owner, sibling-repo git is refused in agent sessions):

   ```bash
   ! git -C /Users/pcalnon/Development/python/Juniper/juniper-deploy worktree remove /Users/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--chore--pin-recurrence-0.6.0-canopy-0.9.0--20261017-1945--541e65e
   ! git -C /Users/pcalnon/Development/python/Juniper/juniper-deploy branch -D chore/pin-recurrence-0.6.0-canopy-0.9.0
   ```

4. **P5 work the rulings unblocked** (the next session's main thread once step 1 is merged): W5.10 (per-fold θ / λ / γ and `gcv_at_edge` / `null_model` in the crossval and train responses) first, then W5.8 (B) + W5.9 for recurrence 0.7.0 / model 0.5.0 (CHANGELOG Changed with the measured numbers; W5.10 may ship in a 0.6.x if ready first); W5.2 (grouped CV) and W5.4 (the acceptance facility, then the R5 band `cv_r2 ∈ [−1.0, +0.5]`, `cv_r2_std ≤ 0.5`, gate, row-scoped); W5.7 with the F-P8 guard (juniper-data). Round 3 of the CV-blowup note's review (one Lane A check of the re-derivation keys) precedes W5.4's encoding of the band. P2–P4 proceed alongside per the plan.
5. **Owner, W0.1 service-core half** (at the next cascor restart on the original host; recipe in `juniper-recurrence/AGENTS.md` § "Host environment the experiment launchers actually serve from"):

   ```bash
   PY=/opt/miniforge3/envs/JuniperCascor1/bin/python
   # stop the cascor listener on :8202 first (the canopy E2E stack), then:
   $PY -s -m pip install --no-deps -e /home/pcalnon/Development/python/Juniper/juniper-ml/juniper-service-core
   $PY -s -m pip check | grep -i juniper          # want: no output
   # restart cascor and any recurrence listener; re-run the bench as served: $PY -m pytest bench/ from the juniper-recurrence root (37 tests)
   ```

6. **Owner, the parent `Juniper/AGENTS.md` "RELEASED to PyPI" paragraph** (absent on turing; paste on the original host). PyPI as of 2026-10-18 19:02Z:

   > **RELEASED to PyPI** (checked 2026-10-18): juniper-ml 0.10.0; juniper-data 0.17.0; juniper-data-client 0.6.0; juniper-cascor 0.11.0; juniper-cascor-client 0.8.0; juniper-cascor-worker 0.6.1; juniper-cascor-protocol 0.2.0; juniper-canopy 0.9.0; juniper-recurrence 0.6.1; juniper-recurrence-model 0.4.0; juniper-recurrence-client 0.3.0; juniper-ci-tools 0.9.0; juniper-config-tools 0.1.0; juniper-doc-tools 0.1.2; juniper-model-core 0.3.2; juniper-observability 0.4.1; juniper-service-core 0.7.1.

7. **Follow-ups still open**: juniper-canopy#735–#738 and #751; juniper-ml#2210, #2211; juniper-deploy#250; a runner-side measurement of GitHub's real GraphQL body cap, to re-set `ARCHIVE_B64_MAX_DEFAULT` in `util/release_train/ceremony.py` (noted on the closed juniper-ml#2227); `docs/REFERENCE.md:177`'s pins sentence waits for the 0.11.x matrix row.

## Key context (traps, all still in force)

- **No signing on turing**: land through `util/open_signed_pr.py` (branch + signed commit + PR in one call) and `util/ad-hoc/2026-10-17_push_signed_with_retry.py` (one signed commit per file onto an existing branch, head re-read per attempt); create PRs by REST when the helper is not used; merge with `util/safe_merge.py --pr N --repo juniper-ml --execute`, which refuses on unresolved review threads (CodeQL ones resolve via GraphQL `resolveReviewThread`). The slow link is turing's Wi-Fi association, not the VPN (memory `turing-api-landing-pitfalls`); with the link idle even the 184 KB plan lands first try.
- **The worktree guard** refuses `cd … && VAR=…; sed … $VAR`, multi-statement heredoc-then-run forms and `git -C` on sibling repos; spell paths literally and split commands (memory `worktree-guard-refusals`).
- **Concurrent sessions edit the plan.** Fetch `origin/main` first, drop the local copy, fast-forward, re-apply exact-string edits that fail on a missing anchor; branch from current `main`, since a branch from older `main` conflicts even when its content incorporates `main`'s changes.
- **The archive guard is add-only**: modifying a `notes/releases/` file needs `Allow-Archive-Edit: <path>` in a commit body.
- **Four deploy tests and two launcher tests fail on turing** for host reasons (`tests/test_snapshot_root_preflight.py`; the bash 3.2 `${1,,}` in `util/recurrence_env_preflight.bash:183`), all green in CI.
- **Merge approvals do not carry over.** This session's covered juniper-deploy#249, juniper-recurrence#207, juniper-ml#2234, #2238, #2239 and the plan v1.7.1 / handoff PR. Step 1's PR needs its own.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml
git log --oneline -3 origin/main                                              # the v1.7.1 PR on top of a81c93bf (#2239)
grep -n 'Version\*\*: 1.7.1' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
curl -s https://pypi.org/pypi/juniper-recurrence/json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["info"]["version"]);print([r for r in d["info"]["requires_dist"] if r.startswith("juniper-")])'   # 0.6.1; model<0.5.0,>=0.4.0; data-client<0.7.0,>=0.6.0
gh release view juniper-recurrence-v0.6.1 --repo pcalnon/juniper-recurrence --json tagName,targetCommitish   # cad03ed5…
gh run view 39152653722 --repo pcalnon/juniper-recurrence --json conclusion   # success
grep -n 'juniper-recurrence>=' pyproject.toml                                  # >=0.6.0 until step 1 lands, then >=0.6.1
gh pr list --repo pcalnon/juniper-ml --search "pyproject" --json number,title  # concurrent extras PRs before step 1
```

## Git status at handoff

- **juniper-ml worktree** `unified-knitting-galaxy`: branch `worktree-unified-knitting-galaxy`, at `a81c93bf` = `origin/main` (juniper-ml#2239). Local modifications are exactly the plan (v1.7.1) and this handoff, pushed as signed commits through the API; nothing is committed locally.
- **Sibling worktree** `/Users/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--chore--pin-recurrence-0.6.0-canopy-0.9.0--20261017-1945--541e65e`: juniper-deploy#249's tree, merged; remove it (step 3).
- **Scratch** (session-specific, gone with the sandbox): the v1.7.1 edit script and the PR body.

## Documents created or modified this session (since the predecessor)

- **juniper-ml**:
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.1);
  - this file.
- **Referenced**: the predecessor handoff above (its "Completed this session" and document lists are the record for the rest of the session); `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11; `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md` §4; `juniper-recurrence/AGENTS.md` (the W0.1 recipe); `notes/releases/RELEASE_NOTES_juniper-recurrence_v0.6.1.md`.
