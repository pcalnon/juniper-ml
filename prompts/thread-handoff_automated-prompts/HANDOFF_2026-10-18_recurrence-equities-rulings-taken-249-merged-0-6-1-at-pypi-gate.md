# Thread Handoff — Recurrence × Equities: the owner rulings are taken, juniper-deploy#249 is merged, recurrence 0.6.1 is at its PyPI gate

- **Date**: 2026-10-18
- **Session**: "recurrence equities", run on host **turing** in the juniper-ml worktree `.claude/worktrees/unified-knitting-galaxy`
- **Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-17_recurrence-equities-w1-13-published-w1-14-done-deploy-smokes-next.md`
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, **v1.7.0**, which lands in juniper-ml#2235 (on top of v1.6.2, juniper-ml#2236, a concurrent session's)

---

## Handoff goal

Continue the arc from plan v1.7.0. **M1's code, publication and deployment halves are complete, and every open owner ruling is taken.** What is left is the owner's `pypi` gate for recurrence 0.6.1, two merges, and the P2–P5 work the rulings unblocked.

## Completed this session (2026-10-18)

- **Owner rulings, taken interactively** (plan "Ruled 2026-10-18, turing deploy-smokes session"):
  - R1–R8 confirmed as shipped (R1's preset not commissioned); R5's amended band accepted (`cv_r2 ∈ [−1.0, +0.5]`, `cv_r2_std ≤ 0.5`, gate, row-scoped, encoded by W5.4 after W5.2);
  - W5.8 (B) + W5.9 + W5.10 accepted for **recurrence 0.7.0 / model 0.5.0** (CHANGELOG Changed; W5.10 first, may ship in a 0.6.x); W5.11 declined;
  - F-P8 Major with the W5.7 guard; F-P4 re-rated Major (resolved);
  - milestone dates confirmed as written; **M1 does not wait for 0.6.1**; the juniper-ml `[recurrence]` floor moves to `>=0.6.1` once published;
  - W0.1's service-core half: owner-run at the next cascor restart (checklist below);
  - 2c: `${RUN_DIR}/snapshots`; juniper-ml#2227: fix and re-archive; canopy 5xx (#702/#738): annotate only; the extras PR was a concurrent session's (juniper-ml#2232, merged).
- **juniper-deploy#249 merged** (squash of `980989e9`) through `util/safe_merge.py`, after the Linux-host session's smokes passed (8/8 and 3/3; outputs on #249). Compose and Helm now pin data 0.17.0 / recurrence 0.6.0 / canopy 0.9.0.
- **recurrence 0.6.1** (the floors 0.6.0 shipped without, juniper-recurrence#206):
  - proposal juniper-recurrence#207 merged as `cad03ed5` (version, CHANGELOG `[0.6.1]`, AGENTS.md rows);
  - the release-train ceremony ran from turing against the tree extracted at that commit (`--cross-repo --target-sha cad03ed5…`): archive juniper-ml#2238 (auto-merge armed), Release `juniper-recurrence-v0.6.1`, publish run parked at **PENDING_PYPI_APPROVAL** (https://github.com/pcalnon/juniper-recurrence/actions/runs/39152653722).
- **juniper-ml#2227 fixed** (`util/release_train/ceremony.py`, in #2235): `-F contents=@<file>`, `OSError` → `SourceError`, `archive-too-large` pre-write HALT (125,000 B base64 default, `JUNIPER_RELEASE_TRAIN_ARCHIVE_B64_MAX`). Five new tests; runbook §4 and `docs/REFERENCE.md` rows. The 0.6.1 ceremony was the first run on the fixed code.
- **canopy 0.9.0's full notes re-archived**: juniper-ml#2234 merged. Rebuilt from canopy's CHANGELOG with the ceremony's renderer; re-condensing reproduces the old archive byte for byte. The archive guard is add-only, so the commit carried `Allow-Archive-Edit: notes/releases/RELEASE_NOTES_juniper-canopy_v0.9.0.md` (a trailer-less first attempt, #2233, was closed).
- **2c**: `util/isolated_stack.bash` hands the `--with-recurrence` leg `JUNIPER_RECURRENCE_SNAPSHOTS_DIR=${RUN_DIR}/snapshots` and creates the dir; `tests/test_isolated_stack_script.py` pins it (#2235). juniper-canopy#751 filed for Lane B.
- **Filed / annotated**: juniper-deploy#250 (the snapshot smoke builds from `../juniper-data` instead of pulling when the image is not local); juniper-canopy#738 and #702 commented with the 0.6.0 pin and the ruling.
- **Turing**: Compose v5.6.0 installed at user level (`~/.docker/cli-plugins/docker-compose`, sha256-verified; Docker Desktop's v2.2.1 lacks `--wait-timeout`). Docker reaches GHCR, but pulls over the link fail with `unexpected EOF`; the smokes were not re-run here once the Linux host's results landed.

## Remaining work (in order)

1. **Owner: approve recurrence 0.6.1's `pypi` gate** (link above). Then verify:

   ```bash
   curl -s https://pypi.org/pypi/juniper-recurrence/json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["info"]["version"], d["info"]["requires_dist"])'   # 0.6.1; model>=0.4.0,<0.5.0 and data-client>=0.6.0,<0.7.0
   gh pr view 2238 --repo pcalnon/juniper-ml --json state     # MERGED once auto-merge fires
   ```

   Then: a juniper-ml extras PR moving `[recurrence]` to `juniper-recurrence>=0.6.1` (owner ruling; lockstep files as in juniper-ml#2232: `pyproject.toml`, `tests/test_pyproject_extras.py`, `README.md`, `AGENTS.md`, `docs/QUICK_START.md`, `docs/REFERENCE.md`, `CHANGELOG.md`; pre-flight against PyPI on 3.12–3.14), and the owner's decision on whether the Compose pin follows to 0.6.1.
2. **Merge juniper-ml#2235** once green (CI was re-run after a black/isort fix). It carries plan v1.7.0 rebased on v1.6.2, so juniper-ml#2236 must be merged first; if #2236 changes again, re-run `edit_plan_v170_on_162.py` (the scratch script is gone with the session; the edits are all exact-string replacements listed in the 1.7.0 change-log row).
3. **Remove the merged juniper-deploy worktree** (owner, sibling-repo git is refused in agent sessions):

   ```bash
   ! git -C /Users/pcalnon/Development/python/Juniper/juniper-deploy worktree remove /Users/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--chore--pin-recurrence-0.6.0-canopy-0.9.0--20261017-1945--541e65e
   ! git -C /Users/pcalnon/Development/python/Juniper/juniper-deploy branch -D chore/pin-recurrence-0.6.0-canopy-0.9.0
   ```

4. **P5 work the rulings unblocked** (next session's main thread): W5.10 (per-fold θ / λ / γ and `gcv_at_edge` / `null_model` in the crossval and train responses) first, then W5.8 (B) + W5.9 for recurrence 0.7.0 / model 0.5.0; W5.2 (grouped CV) and W5.4 (the acceptance facility, then the R5 band); W5.7 with the F-P8 guard (juniper-data). P2–P4 proceed alongside per the plan.
5. **Owner, W0.1 service-core half** (at the next cascor restart on the original host; recipe in `juniper-recurrence/AGENTS.md` § "Host environment the experiment launchers actually serve from"):

   ```bash
   PY=/opt/miniforge3/envs/JuniperCascor1/bin/python
   # stop the cascor listener on :8202 first (the canopy E2E stack), then:
   $PY -s -m pip install --no-deps -e /home/pcalnon/Development/python/Juniper/juniper-ml/juniper-service-core
   $PY -s -m pip check | grep -i juniper          # want: no output
   # restart cascor and any recurrence listener; re-run the bench as served: $PY -m pytest bench/ from the juniper-recurrence root (37 tests)
   ```

6. **Owner, the parent `Juniper/AGENTS.md` "RELEASED to PyPI" paragraph** (absent on turing; paste on the original host). PyPI as of 2026-10-18, before the 0.6.1 gate:

   > **RELEASED to PyPI** (checked 2026-10-18): juniper-ml 0.10.0; juniper-data 0.17.0; juniper-data-client 0.6.0; juniper-cascor 0.11.0; juniper-cascor-client 0.8.0; juniper-cascor-worker 0.6.1; juniper-cascor-protocol 0.2.0; juniper-canopy 0.9.0; juniper-recurrence 0.6.0 (0.6.1 at its gate); juniper-recurrence-model 0.4.0; juniper-recurrence-client 0.3.0; juniper-ci-tools 0.9.0; juniper-config-tools 0.1.0; juniper-doc-tools 0.1.2; juniper-model-core 0.3.2; juniper-observability 0.4.1; juniper-service-core 0.7.1.

7. **Follow-ups still open**: juniper-canopy#735–#738 and #751; juniper-ml#2210, #2211; juniper-deploy#250; a runner-side measurement of GitHub's real GraphQL body cap, to re-set `ARCHIVE_B64_MAX_DEFAULT` (juniper-ml#2227 can close once #2235 merges; note the measurement there).

## Key context (traps met on turing)

- **Everything in the predecessor's trap list still holds** (no signing; `open_signed_pr.py` / `push_signed_with_retry.py`; REST for PR creation; the worktree guard's refusals). Two refinements: the slow link is turing's Wi-Fi association, not the VPN (memory `turing-api-landing-pitfalls`); with the link idle, every file including the 1 MB `docs/REFERENCE.md` landed first try, while concurrent downloads made even small `gh` calls reset.
- **Concurrent sessions edit the plan.** Two sessions landed v1.6.1 and v1.6.2 under this one. Before pushing a whole-file blob, fetch `origin/main`, drop the local copy, fast-forward, and re-apply with exact-string replacements that fail loudly on a missing anchor. The two "Ruled 2026-10-18" blocks are distinguished by session in their headings.
- **The archive guard is add-only**: a PR that modifies an archived note needs `Allow-Archive-Edit: <path>` in a commit body (`open_signed_pr.py --commit-body`); `safe_merge.py`'s squash body carries the trailers.
- **The ceremony needs the sibling tree at the target commit**: `gh api repos/pcalnon/<repo>/tarball/<sha>` extracted under a scratch ecosystem root, `detect.py --json` for the manifest, `--dry-run` then `--execute --cross-repo --target-sha <40-char>`. A transient DNS failure at planning writes nothing; re-run.
- **Deploy smokes on turing**: pre-pull images (juniper-deploy#250), Compose ≥ 2.17 for `--wait-timeout`, retry pulls. Prefer the Linux host.
- **Four deploy tests and two launcher tests fail on turing** for host reasons (`tests/test_snapshot_root_preflight.py`; the bash 3.2 `${1,,}` in `util/recurrence_env_preflight.bash:183`), all green in CI.
- **Merge approvals do not carry over.** This session's covered juniper-deploy#249, juniper-recurrence#207, juniper-ml#2234 and #2235, the 0.6.1 ceremony's archive PR #2238 (auto-merge), and the 2c / 2227 edits.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml
git log --oneline -3 origin/main                                              # #2236 then #2235 on top once merged
gh pr view 2235 --repo pcalnon/juniper-ml --json state,mergeStateStatus
gh pr view 2238 --repo pcalnon/juniper-ml --json state                        # MERGED after the gate
gh release view juniper-recurrence-v0.6.1 --repo pcalnon/juniper-recurrence --json tagName,targetCommitish   # cad03ed5…
curl -s https://pypi.org/pypi/juniper-recurrence/json | python3 -c 'import json,sys;print(json.load(sys.stdin)["info"]["version"])'   # 0.6.1 once approved
gh pr view 249 --repo pcalnon/juniper-deploy --json state                     # MERGED
grep -n 'JUNIPER_RECURRENCE_SNAPSHOTS_DIR' util/isolated_stack.bash           # 2c present after #2235
grep -n 'archive-too-large' util/release_train/ceremony.py | head -3          # #2227 fix present after #2235
```

## Git status at handoff

- **juniper-ml worktree** `unified-knitting-galaxy`: branch `worktree-unified-knitting-galaxy`, fast-forwarded to `origin/main` at `2719f7f3` (juniper-ml#2232). Local modifications are exactly #2235's files (pushed as signed commits through the API, one per file) plus this handoff; nothing is committed locally.
- **Sibling worktree** `/Users/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--chore--pin-recurrence-0.6.0-canopy-0.9.0--20261017-1945--541e65e`: juniper-deploy#249's tree, merged; remove it (step 3).
- **Scratch** (session-specific, gone with the sandbox): the rebuilt canopy notes, the 0.6.1 proposal files, the ceremony manifest and log, and the edit scripts.

## Documents created or modified this session

- **juniper-ml** (#2235 unless noted):
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.0) and this file;
  - `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md` (§4 `archive-too-large` row), `docs/REFERENCE.md` (release-train bullet), `CHANGELOG.md`;
  - `util/release_train/ceremony.py`, `tests/test_release_train_ceremony.py`, `util/isolated_stack.bash`, `tests/test_isolated_stack_script.py`;
  - `notes/releases/RELEASE_NOTES_juniper-canopy_v0.9.0.md` (full notes, #2234, merged);
  - `notes/releases/RELEASE_NOTES_juniper-recurrence_v0.6.1.md` (#2238, the ceremony's archive).
- **juniper-recurrence** (#207, merged): `juniper-recurrence/juniper_recurrence/_version.py`, `juniper-recurrence/CHANGELOG.md`, `AGENTS.md`.
- **Referenced**: the predecessor handoff above; `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11.7; `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` (D3); `juniper-recurrence/AGENTS.md` (the W0.1 recipe).
