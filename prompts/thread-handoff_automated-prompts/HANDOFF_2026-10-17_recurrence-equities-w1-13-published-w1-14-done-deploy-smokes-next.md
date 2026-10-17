# Thread Handoff — Recurrence × Equities: W1.13 published, W1.14 done; the deploy smokes and the juniper-ml extras are next

- **Date**: 2026-10-17
- **Session**: "recurrence equities", run on host **turing** in the juniper-ml worktree `.claude/worktrees/composed-meandering-avalanche`
- **Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-10_recurrence-equities-w1-11-done-w1-13-owner-next.md`
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, **v1.6.0**, which lands in this handoff's PR

---

## Handoff goal

Continue the arc from the plan v1.6.0. **All four W1.13 publications are on PyPI, and W1.14 is done.** Three things are left for M1:

1. Run the two deploy smokes and merge **juniper-deploy#249**, which carries the last W1.13 pins.
2. Open the **juniper-ml extras** PR. Both of its ceilings are escaped.
3. The owner rulings.

## Completed this session (2026-10-17)

- **W1.14 (F-S10), accepted by the owner for 0.6.0.** juniper-recurrence#203, squash `aeccd35f`.
  - `map_data_error` answers every 5xx with a fixed phrase, plus juniper-data's status when there is one. The full text stays in each route's WARNING.
  - `Settings` refuses a padded or control-character `juniper_data_api_key`, and sets `hide_input_in_errors` so no `ValidationError` prints a value.
  - Each test was checked against `origin/main`'s code: all fail there. The leak was reproduced through the real data client.
  - Found while fixing it: the leak also reached `GET /v1/training/status` (through `RecordedOperation`) and the juniper-ml driver's run manifest.
- **The W1.13 publications.** The owner approved every `pypi` gate. Each wheel was probed with a control.

  | Package | On PyPI | Release / tag commit | Notes archive | Probe |
  | --- | --- | --- | --- | --- |
  | juniper-data-client 0.6.0 | 05:16Z | `v0.6.0` (2026-10-10) | `RELEASE_NOTES_juniper-data-client_v0.6.0.md` | `util/ad-hoc/2026-10-17_verify_data_client_0_6_0_published_wheel.py`: 12/12 W1.4 rules; the 0.5.0 control fails |
  | juniper-recurrence-model 0.4.0 | 2026-10-13 | `juniper-recurrence-model-v0.4.0` | (2026-10-10) | `DEFAULT_TARGET='auto'`, and a `(W, 1)` `target_dt` is refused; the 0.3.0 control accepts it |
  | juniper-recurrence 0.6.0 | 22:08:58Z | `juniper-recurrence-v0.6.0` at `535d1e78` (`--latest`) | juniper-ml#2223 (Medium) | clean `-I` install: W1.14 present, model 0.4.0 / data-client 0.6.0 resolved; the 0.5.0 control relays the key |
  | juniper-canopy 0.9.0 | 22:08:40Z | `v0.9.0` at `bd001153` (`--latest`) | juniper-ml#2225 (High; Fixed condensed) | metadata: `[juniper-data]` admits data-client `<0.7.0`, plus the security floors |

  - **recurrence**:
    - #204 is the proposal: version, CHANGELOG move, AGENTS.md rows, and an image-lock move to model 0.4.0 and data-client 0.6.0.
    - #205 records that move in `[0.6.0]` before the cut.
    - The lock lines were moved **by hand**, because uv could not reach PyPI from turing. pip's resolver (`--python-version 3.13 --only-binary=:all:`) then accepted exactly the 31 pins.
  - **canopy**: #750 is the lock move to data-client 0.6.0.
  - **GHCR**:
    - `juniper-recurrence` index `sha256:bb2f4ac5…`; `juniper-canopy` index `sha256:b262d978…`.
    - Tags `X.Y.Z`, `X.Y` and `latest` all resolve to that index.
    - Both are amd64 + arm64, and the revision label is the tag's commit.
- **juniper-deploy#249** is open and CLEAN; CI is green.
  - It moves recurrence to `0.6.0` (compose ×1) and canopy to `0.9.0` (compose ×3, plus the Helm `canopy.image.tag`).
  - The "pinned image predates the snapshot routes" text in `docker-compose.yml`, `README.md`, `docs/REFERENCE.md` and `scripts/test_recurrence_snapshots.sh` now says 0.6.0 is the first image with them.
  - It has a CHANGELOG entry.
  - **It is held until the smokes pass** (owner ruling).
- **juniper-ml#2226** adds the two ad-hoc tools: the data-client probe and `util/ad-hoc/2026-10-17_condense_release_notes_section.py`.
- **juniper-ml#2227 (issue)**: the release-train ceremony cannot archive notes over about 97 KB.
  - `ceremony.py:838` passes the base64 as one `gh` argument, which a Linux runner caps at 128 KiB.
  - A correction comment says the turing-measured GraphQL cap of about 128 KiB may be the VPN path, not GitHub.
  - Canopy's notes were condensed because of this (owner ruling). #2224, the first canopy archive PR, was closed: it failed the archive guard (two scripts were in it) and gitleaks (a verbatim example `KEY="…"`).
- **Follow-ups**: the six the 2026-10-10 handoff called "not yet filed" were filed that day, and all are still open:
  - juniper-canopy#735, #736, #737 and #738;
  - juniper-ml#2210 and #2211.

  The seventh, recurrence's `[bench]` cap, was fixed by juniper-recurrence#195.
- **Plan v1.6.0** (this PR):
  - status rows: W1.13 rewritten, W1.14 added;
  - the M1, F-S10 and F-DEP1 rows; Overview item 5; the dependency row;
  - a **Progress 2026-10-17** paragraph;
  - **Ruled 2026-10-17** (the owner's rulings);
  - "Applied pending ruling" no longer says "nothing here is released": R2, R3, R7 and R8's alternative all ship now;
  - a 1.6.0 change-log row.
- **Cleanup**: the merged W1.14, recurrence-release and canopy-lock worktrees and local branches are removed. Their remote branches were auto-deleted on merge.

## Remaining work (in order)

1. **The deploy smokes, then merge juniper-deploy#249.**
   - **Turing's Docker daemon cannot reach any registry** (`Client.Timeout exceeded while awaiting headers`), probably because of the VPN. Its VM has about 2 GB of memory.
   - **The session's worktree hook refuses `bash <script>`**, so the **owner** runs these, on turing once Docker's network works, or on any host with working Docker:

     ```bash
     cd /Users/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--chore--pin-recurrence-0.6.0-canopy-0.9.0--20261017-1945--541e65e
     docker pull --quiet redis:7.4-alpine                       # connectivity first
     bash scripts/test_recurrence_snapshots.sh                  # W1.12 round trip; first run on a published image
     bash scripts/test_canopy_recurrence_smoke.sh --published   # the W1.11 smoke, by GHCR digest
     ```

   - Then run `python3 util/safe_merge.py --pr 249 --repo juniper-deploy --execute`, and read the `MERGED` line.
2. **The juniper-ml extras PR**, now unblocked.
   - **Ceilings**:
     - `[recurrence]` `juniper-recurrence-model>=0.3.0,<0.4.0`: model 0.4.0 is escaped;
     - `juniper-recurrence>=0.5.0,<0.6.0`: 0.6.0 is escaped.
   - **Floors, an owner decision**:
     - Recommendation: raise `[servers]` to `juniper-canopy>=0.9.0` (High security) and `[recurrence]` to `juniper-recurrence>=0.6.0` (Medium security).
     - Keep the model and data-client floors.
   - **Lockstep artifacts**:
     - `pyproject.toml:84,104-105`;
     - `tests/test_pyproject_extras.py:150,166-167`;
     - `README.md:92,95`;
     - `AGENTS.md:262,265`, plus `Last Updated`;
     - `docs/QUICK_START.md:60,63`;
     - `docs/REFERENCE.md`: the split-column table near `:177`. The file is **992 KB**, so land it with the retry driver;
     - `CHANGELOG.md`.
   - **Pre-flight against real PyPI**, as juniper-ml#2190 did: `[servers]` and `[all]` on Python 3.12, 3.13 and 3.14.
3. **Merge this handoff's docs PR**, if it is not merged yet.
4. **Follow-ups**:
   - canopy may now show 5xx details, but only against recurrence ≥ 0.6.0 (juniper-canopy#702, #738);
   - juniper-ml#2227;
   - the open six above;
   - the parent `Juniper/AGENTS.md` "RELEASED to PyPI" paragraph: absent on turing, unversioned, updated with the last pin per W1.13.
5. **Owner items** (unchanged):
   - dates;
   - R1–R8 confirmation (R2, R3, R7 and R8's alternative now *ship*; a re-ruling means a release), and R5;
   - W5.8 (B) vs W5.11; W5.9 / W5.10;
   - F-P8 Major + the W5.7 guard; re-rating F-P4;
   - the W0.1 service-core half;
   - 2c, which is still not landed (canopy Lane B).

## Key context (traps met on turing)

- **Signing.** Turing has no signing, so land with `util/open_signed_pr.py` / `util/push_signed_commit.py`.
- **GraphQL 499s through the ExpressVPN.** Large `createCommitOnBranch` calls return HTTP 499 intermittently. A 77 KB file needed 3 attempts, and a 43–46 KB file landed first time. Background downloads (uv, pip, docker) saturating the link made even small ones fail.
  - Push one file per commit.
  - Always re-read the ref after an error.
  - Prefer `util/ad-hoc/2026-10-17_push_signed_with_retry.py` (on `main` since juniper-ml#2228). It checks whether the blob landed before retrying.
- **`gh pr create` (GraphQL) also 499'd.** Create PRs through REST: `gh api -X POST repos/pcalnon/<repo>/pulls --input <json>`.
- **uv cannot reach PyPI from turing** (connect timeouts), but pip works, slowly. To verify a lock, use `pip install --dry-run --report … --python-version X --only-binary=:all: --platform manylinux_2_28_x86_64 --platform manylinux_2_17_x86_64 …` (pass several `--platform` tags).
- **The worktree hook** refuses:
  - `bash <script>` and `python3 -` heredocs;
  - git or gh commands built from variables or loops;
  - awk programs;
  - any command text containing "git…" words, for example `gitleaks`.

  Put helpers in scratchpad files and run them as `python3 -I <file>`.
- **A gitleaks `generic-api-key` hit** on an example `VAR="value"` in notes fails `Security Scan`. It scans every commit in the PR, so a fix-up commit cannot clear it: recreate the branch.
- **The archive guard** requires an archive PR to contain **only** `notes/releases/RELEASE_NOTES_*.md`.
- **Four deploy tests fail on turing** (`tests/test_snapshot_root_preflight.py`), even on untouched `main`; CI passes them.
- **Merge approvals do not carry over.** This session's covered #203, #204, #205, #750, #2223, #2225, #2226, #249 (held for the smokes) and this docs PR.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml
for p in juniper-data-client juniper-recurrence-model juniper-recurrence juniper-canopy; do curl -s https://pypi.org/pypi/$p/json | python3 -c 'import json,sys;print(json.load(sys.stdin)["info"]["version"])'; done   # 0.6.0 0.4.0 0.6.0 0.9.0
gh pr view 249 --repo pcalnon/juniper-deploy --json state,mergeStateStatus     # OPEN until the smokes pass
gh issue view 2227 --repo pcalnon/juniper-ml --json state                      # OPEN
grep -n 'juniper-recurrence' pyproject.toml                                    # <0.6.0 ceiling = the extras PR is still owed
git log --oneline -3 origin/main                                               # this handoff's PR on top once merged
```

## Git status at handoff

- **juniper-ml worktree** `composed-meandering-avalanche`: branch `worktree-composed-meandering-avalanche` at `0895887f`. It has no local commits, and everything was landed through the API.
  - The plan and this file are in this handoff's PR.
  - The local copies of `notes/releases/RELEASE_NOTES_juniper-{recurrence_v0.6.0,canopy_v0.9.0}.md` and the two `util/ad-hoc/2026-10-17_*` scripts are untracked duplicates of what is on `main`.
- **Sibling worktrees**: only `/Users/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--chore--pin-recurrence-0.6.0-canopy-0.9.0--20261017-1945--541e65e` is left. It is juniper-deploy#249's local tree, identical to its head `980989e9`. Keep it for the smokes, then remove it after #249 merges.

## Documents created or modified this session

- **juniper-ml**:
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.6.0) and this file, both in this PR;
  - `notes/releases/RELEASE_NOTES_juniper-recurrence_v0.6.0.md` (#2223) and `notes/releases/RELEASE_NOTES_juniper-canopy_v0.9.0.md` (#2225);
  - `util/ad-hoc/2026-10-17_verify_data_client_0_6_0_published_wheel.py` and `util/ad-hoc/2026-10-17_condense_release_notes_section.py` (#2226).
- **juniper-recurrence**:
  - `juniper-recurrence/juniper_recurrence/routers/_common.py`, `…/settings.py`, `tests/test_routes.py` and `tests/test_settings.py` (#203);
  - `juniper-recurrence/CHANGELOG.md` (#203, #204, #205);
  - `…/_version.py`, `AGENTS.md` and `juniper-recurrence/requirements.lock` (#204).
- **juniper-canopy**: `requirements.lock` (#750).
- **juniper-deploy** (#249, open): `docker-compose.yml`, `k8s/helm/juniper/values.yaml`, `README.md`, `docs/REFERENCE.md`, `scripts/test_recurrence_snapshots.sh` and `CHANGELOG.md`.
- **Referenced**: the predecessor handoff above; `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11; `notes/releases/RELEASE_NOTES_juniper-data-client_v0.6.0.md`; `notes/releases/RELEASE_NOTES_juniper-recurrence-model_v0.4.0.md`; `notes/releases/RELEASE_NOTES_juniper-data_v0.17.0.md` (the advisory precedent).
