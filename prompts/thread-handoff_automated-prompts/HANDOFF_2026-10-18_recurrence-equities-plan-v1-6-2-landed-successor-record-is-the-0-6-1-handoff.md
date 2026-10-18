# Thread Handoff — Recurrence × Equities: plan v1.6.2 landed (W1.13's last two merges recorded); the arc's record of state moved to the 0.6.1 session's handoff

- **Date**: 2026-10-18
- **Session**: "recurrence equities", run on host **turing** in the juniper-ml worktree `.claude/worktrees/zippy-sprouting-reddy`
- **Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-17_recurrence-equities-w1-13-published-w1-14-done-deploy-smokes-next.md`
- **Successor of record** (a concurrent session's, not this one's): `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-18_recurrence-equities-0-6-1-published-extras-floor-and-p5-next.md`, which lands in juniper-ml#2240 together with plan **v1.7.1**. Its own predecessor, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-18_recurrence-equities-rulings-taken-249-merged-0-6-1-at-pypi-gate.md`, is on `main` (juniper-ml#2239).
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` — **v1.6.2** is this session's (juniper-ml#2236, merged as `8580153c`); `main` is at **v1.7.0** (juniper-ml#2239, `a81c93bf`); **v1.7.1** is open in juniper-ml#2240.

---

## Handoff goal

**Do not continue the arc from this file.** Three sessions edited the plan on 2026-10-18, and the current record of state is the successor handoff named above. The next thread should:

1. read `HANDOFF_2026-10-18_recurrence-equities-0-6-1-published-extras-floor-and-p5-next.md` from juniper-ml#2240's head (or from `main` once #2240 merges) and continue from **its** "Remaining work" list, whose first item is the juniper-ml `[recurrence]` floor to `juniper-recurrence>=0.6.1` (an owner ruling of 2026-10-18);
2. use this file only for what this session did and verified, and for the two merge-helper observations under Key context.

## Completed this session (2026-10-18)

- **Plan v1.6.2** — juniper-ml#2236, one GitHub-signed commit `bd996ee1`, merged 18:25Z as `8580153c`. Based on v1.6.1 (`main` at `2719f7f3`); 14 exact-string edits, 23 insertions / 12 deletions in the one file. It records:
  - **juniper-deploy#249 merged** as `aa2a6fb0` (09:40Z). Read back from juniper-deploy `main`: Compose pins juniper-data `0.17.0`, juniper-recurrence `0.6.0`, juniper-canopy `0.9.0`. F-DEP1 marked resolved; the Success Metrics "Compose pins" row marked met.
  - **juniper-ml#2232 merged** as `2719f7f3` (17:40Z): `[recurrence]` ceilings `juniper-recurrence-model<0.5.0` / `juniper-recurrence<0.7.0`; floors `juniper-canopy>=0.9.0` (`[servers]`) and `juniper-recurrence>=0.6.0`; pre-flight against real PyPI `[servers]` 61 / `[recurrence]` 32 / `[all]` 95 packages (worker 0.6.1) on Python 3.12, 3.13 and 3.14.
  - a new **Ruled 2026-10-18** block (the extras rulings: the two security floors raised; the meta-package's model floor kept at `>=0.3.0`, data-client at `>=0.5.0`), and the 2026-10-10 block's "separate decision, raised in the extras PR" line re-pointed at it;
  - Status line, Overview item 5, M1 row, W1.13 status row, roadmap Fix line, W1.13 dependency row, Progress 2026-10-18, and the 1.6.2 change-log row.
- **Facts re-read before writing** (not taken from the handoff): juniper-recurrence#206 `MERGED` `509ea25f` (04:04Z); juniper-ml#2227, #2210, #2211 and juniper-canopy#735–#738 all `OPEN`; juniper-canopy#702 is a merged PR (W0.5 / W0.7), so the 5xx-detail follow-on is #738.
- **What v1.6.2 did *not* record, because it happened during or after the merge** (all now in v1.7.0 / v1.7.1 instead):
  - juniper-ml#2234 (`500c9c01`) replaced canopy 0.9.0's condensed release-notes archive with the full Fixed section — v1.6.2's "Ruled 2026-10-17" bullet still calls that archive condensed;
  - recurrence **0.6.1**: proposal juniper-recurrence#207 (`cad03ed5`), archive juniper-ml#2238 (`20a1c802`), Release `juniper-recurrence-v0.6.1` cut 18:06Z, **on PyPI 19:02Z** with `requires_dist` `juniper-recurrence-model<0.5.0,>=0.4.0` and `juniper-data-client<0.7.0,>=0.6.0` (verified from the index in this session);
  - the owner rulings taken in the deploy-smokes session (plan "Ruled 2026-10-18, turing deploy-smokes session", v1.7.0): R1–R8 confirmed as shipped, R5's band accepted, W5.8 (B) + W5.9 + W5.10 accepted for recurrence 0.7.0 / model 0.5.0, W5.11 declined, **M1 does not wait for 0.6.1**, the `[recurrence]` floor moves to `>=0.6.1` once published, 2c reconciled.
- **Worktree** reset onto the merged `main` after the merge (the local edit was byte-identical to what landed); the PR branch was auto-deleted.

## Remaining work (in order)

1. **Merge juniper-ml#2240** (plan v1.7.1 + the successor handoff) once its three regression suites finish; they were `IN_PROGRESS` at this handoff, everything else green. Needs its own merge approval: `python3 util/safe_merge.py --pr 2240 --repo juniper-ml --execute`.
2. **Then follow the successor handoff's list**, in its order: the `[recurrence]` floor to `>=0.6.1` (lockstep files as in juniper-ml#2232, pre-flight with `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`); the owner's Compose-pin decision for 0.6.1 (check whether a `0.6.1` GHCR image exists first); the merged juniper-deploy worktree removal (owner); P5 (W5.10 → W5.8 (B) + W5.9; W5.2, W5.4; W5.7); the owner's W0.1 service-core half; the parent `Juniper/AGENTS.md` "RELEASED to PyPI" paragraph (drafted there with recurrence 0.6.1); the open follow-ups.
3. **Nothing from this session is pending**: no open PR, no local change, no scratch worth keeping.

## Key context (what this session learned, beyond the predecessor's traps)

- **`util/safe_merge.py` arms an auto-merge net and refreshes the base itself.** On #2236 it reported `BEHIND — refreshing base (cycle 1/3)`, pushed a signed merge commit of `main` onto the branch (author `Overtoad`, verified), went `BEHIND` again when another PR landed, re-synced, and the net merged once the required checks on the final head were green. Budget 2800 s for juniper-ml; the run took about 25 minutes wall-clock and the Bash call hit its 300 s foreground timeout, so run it with `run_in_background` or a longer timeout. The net is pinned to the original head and is checks-green-gated, so the merge completes even if the helper's process dies.
- **A 172 KB plan landed on the first `util/open_signed_pr.py` attempt** from turing this time; the link was idle. The retry helper `util/ad-hoc/2026-10-17_push_signed_with_retry.py` was not needed.
- **Three sessions edited the plan on one day.** Branch from the *current* `main` at the moment of landing (the dry run prints the base SHA — check it), and expect the version you based on to be superseded within hours. Record only what is merged and re-read from GitHub / PyPI, and let the later session's row carry what landed after yours.
- **The worktree guard** refused `sed -n … $P` with a variable file path and a `gh api … | base64 -d | grep` pipeline; literal paths and a `python3 -I` decoder in the scratchpad worked. `canopy#702` is not in `gh issue list`'s first 200 rows (it is a PR); use `gh issue view` / `gh pr view` by number.
- **Merge approvals do not carry over.** This session's covered juniper-ml#2236 only.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml
git log --oneline -4 origin/main                                   # a81c93bf (#2239, v1.7.0) on top of 8580153c (#2236, v1.6.2); #2240 on top once merged
grep -n '^- \*\*Version\*\*' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md   # 1.7.0 on main, 1.7.1 after #2240
gh pr view 2240 --repo pcalnon/juniper-ml --json state,mergeStateStatus     # OPEN/BLOCKED until its regression suites finish, then merge it
gh pr view 2236 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '{state,sha:.mergeCommit.oid}'   # MERGED 8580153c
curl -s https://pypi.org/pypi/juniper-recurrence/json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["info"]["version"])'   # 0.6.1
grep -n 'juniper-recurrence>=' pyproject.toml                       # >=0.6.0 until the successor's step 1 lands
```

## Git status at handoff

- **juniper-ml worktree** `zippy-sprouting-reddy`: branch `worktree-zippy-sprouting-reddy`, reset to `origin/main` at `8580153c` after the merge; `main` has since moved to `a81c93bf`. Clean tree apart from this file, which lands through the signed API path (no signing on turing). No local commits.
- **Open PRs on juniper-ml** at handoff: #2240 (the concurrent session's plan v1.7.1 + handoff) and #2237 (turing F5a, unrelated).
- **Scratch** (session-specific, gone with the sandbox): the v1.6.2 edit script `plan_v162.py` and the #2236 body.

## Documents created or modified this session

- **juniper-ml**:
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.6.2, juniper-ml#2236, merged);
  - this file.
- **Referenced**: the predecessor handoff and the two 2026-10-18 handoffs named at the top; `notes/requirements/by-area/DEP.md` (JR-ML-DEP-042, cited by #2236); `util/open_signed_pr.py`; `util/safe_merge.py`; `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`; `util/ad-hoc/2026-10-18_raise_recurrence_canopy_pins_w1_13.py`.
