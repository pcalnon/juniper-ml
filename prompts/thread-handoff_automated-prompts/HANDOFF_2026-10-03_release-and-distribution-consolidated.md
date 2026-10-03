# HANDOFF 2026-10-03 — release & distribution (CONSOLIDATED): 0.10.0 and data 0.16.0 delivered; everything left is owner-gated except two record fixes and three cleanups

**Path**: P4 of the 2026-10-03 handoff consolidation — the decision-11 release train (juniper-ml 0.10.0, the `[servers]` gap, the `_force_kill` fix) and the container-registry rollout (juniper-data 0.16.0, the deploy egress guards, Wave 4).

**Consolidated sources** (both in `prompts/thread-handoff_automated-prompts/`):

| source | self-declared validation |
| --- | --- |
| `HANDOFF_2026-09-23_decision-11-round-4-0-10-0-delivered-force-kill-fixed-servers-gap-filed.md` (below: **the d11 handoff**) | Round 1 (three lanes) applied; the round-2 lane died at HTTP 429, so its round-1 corrections are **unchecked**: its Remaining items 4–6, its release-cut cautions, its §A rows for C-4, C-5 and UNRELEASED_CHANGES, and its §D |
| `HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md` (below: **the data handoff**) | Rounds 1–3 ran on earlier drafts; the final update was **"Updated without a validation round, at the owner's request"** (round 4 not run) |

**Supersedes**: both files above (each now carries a SUPERSEDED banner). Their predecessors were already superseded by them: `HANDOFF_2026-09-23_decision-11-round-3-0-10-0-cut-and-every-record-closed.md` and `HANDOFF_2026-09-24_data-0-16-0-cut-at-one-commit-item-5-closed-in-five-repos-wave-4-waits-on-the-token.md`.

**Live probe**: 2026-10-03, 08:34–08:45Z (PyPI JSON, anonymous GHCR `tags/list`, `gh` against every repo named, `git worktree list` / `git branch` in this checkout, `ps`).

---

## Goal statement (paste as the new thread's first prompt)

> **Continue the Juniper release & distribution path** (decision-11 release train + container-registry rollout). Governing documents — every section reference names its file:
> `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` (**PUBLISHING-PLAN**, design of record), `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` (**REGISTRATION-PROCEDURE**, Wave 4 credential steps), `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (**PYPI-PUBLISH-PROCEDURE**, release ceremony; §11.7 Latest
> badge + `--target-sha`), `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` (**PARTITION-PLAN**, §10 release record).
> Source handoffs (in `prompts/thread-handoff_automated-prompts/`): **the d11 handoff** = `HANDOFF_2026-09-23_decision-11-round-4-0-10-0-delivered-force-kill-fixed-servers-gap-filed.md` (round-2 validation incomplete); **the data handoff** = `HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md` (final update not validated). Both are superseded by this file, `HANDOFF_2026-10-03_release-and-distribution-consolidated.md`.
>
> **Completed so far** (all VERIFIED 2026-10-03 unless tagged):
>
> - juniper-ml **0.10.0** on PyPI (uploaded 2026-09-23 19:54Z), `[servers]` = `juniper-canopy>=0.8.1, juniper-cascor>=0.11.0, juniper-data>=0.15.0`. Still the latest; no Juniper package has released since 2026-09-24.
> - ml#2046 (`_force_kill` killpg race) CLOSED 2026-09-23 by ml#2061 (`e94a2e11`); wheel-contract probe fixed by ml#2063 (`6848e11d`), 39/39 over the 0.10.0 set.
> - juniper-data **0.16.0** on PyPI (2026-09-24 18:35:40Z), GHCR `:0.16.0`/`:0.16`, pinned by juniper-deploy#230 (compose `:164`, `:523`).
> - Deploy egress: the owner ruled for **a dedicated egress network** [UNVERIFIED — from the data handoff]; #231 (compose `data-egress`), after which the stack answered `201` for equities, mnist and arc_agi [UNVERIFIED — from the data handoff]; #232 (Helm TCP 443), fix-forwards #233–#236; #236 merged 2026-09-25 01:31:51Z `b2f8a428` — guards are a static, fail-closed model.
> - Both archiving PRs merged: ml#2094 (d11 handoff, 2026-09-26 01:03Z) and ml#2100 (data handoff, 2026-09-26 08:32Z).
>
> **Remaining work, in order**
>
> 1. **[AGENT, no gate] Finish the rollout's records.** Main's PUBLISHING-PLAN still says the guards judge "the union" (status block L32; §5.2 around L722) and never names juniper-deploy#236. Rewrite both as the static fail-closed model (`HANDOFF_2026-10-03_release-and-distribution-consolidated.md` § "Context the remaining work needs" → "The egress guards as merged") and record #236. The data
>    handoff planned this on branch `docs/handoff-data-0-16-0-egress-guards-fail-closed`, but #2100 merged without it, so it now needs a **new** PR (validate the branch before `gh pr create`; merging needs the owner's approval naming it). Also append #236 to harness memory `project_container_registry_rollout_2026-09-08.md`. Optional: one scope-bounded lane judging #236 against its stated scope.
>    [VERIFIED 2026-10-03: `git show origin/main:` grep — no `#236`, "union" at L32/L722]
> 2. **[OWNER] `CROSS_REPO_DISPATCH_TOKEN` scope.** It cannot dispatch to juniper-recurrence (403; every data release's `Notify consumer repos` fails the same way). Owner adds `pcalnon/juniper-recurrence`, Contents: Read and write, to the fine-grained PAT in juniper-data. recurrence#178's last comment also asks for **Actions: Read**, so the sender's confirmation step (data#431) can list runs
>    without relying on the repo staying public. A session cannot inspect PAT scope — wait for his word. An early run only repeats the 403: one `curl` step, about 12 s, with no side effects. Then, with his approval: `gh workflow run notify-consumers.yml -R pcalnon/juniper-data -f version=0.16.0` (#178 names `0.15.0`, written before 0.16.0 existed; or replay per
>    `HANDOFF_2026-10-03_release-and-distribution-consolidated.md` § "Context the remaining work needs" → "Wave 4 specifics"). **Success = a `notify-consumers.yml` run created AFTER the owner's token change that is green, plus the `repository_dispatch` run of `CI — bench harness` in juniper-recurrence that it started, also green.** The existing green dispatch run 36046705575 (2026-09-24 19:13Z, a
>    manual replay) does **not** count. Only then close juniper-recurrence#178. [VERIFIED 2026-10-03: only run is still 35808713744 (failure, 09-23 02:01Z); #178 OPEN]
> 3. **[OWNER → AGENT] Wave 4 (Docker Hub).** Owner runs REGISTRATION-PROCEDURE §2, §5.2B step 3a, §4, §5.2B step 3, §6, then reports four facts: §4 login succeeded; which §5.2B-3a form; the Docker ID; token expiry. Then you: (a) record expiry in REGISTRATION-PROCEDURE §10 by PR; (b) verify the credential names-only on all five repos (Key context); (c) only with the owner's go-ahead, edit the five
>    `publish-image.yml` files. [VERIFIED 2026-10-03: juniper-data `environments/dockerhub` secrets `[]`, variables `[]`]
> 4. **[OWNER] ml#2062** — `[servers]` installs no Juniper client, so canopy service mode and cascor dataset fetch fail. Options (a)/(b) change `[servers]` and need a juniper-ml release; (c) is docs only. `tests/test_pyproject_extras.py` `EXPECTED_EXTRAS["servers"]` pins the bare form. [VERIFIED 2026-10-03: OPEN, last update 09-23]
> 5. **[OWNER] Releases.** Each is Paul's call. Unscoped `util/release_train/detect.py` on 2026-10-03 reports 7 packages with unreleased changes (SHIP/uncertain/discounted): cascor 17/1/1, **canopy 23/0/2**, data 7/0/0, cascor-model 7/0/0, recurrence 7/0/1, **observability 3/0/5**, service-core 1/0/0 [CHANGED SINCE HANDOFF: detect.py 2026-10-03 — canopy 23 (was 14; #676, #678–#685 merged),
>    observability 3 (was 2; ml#2086)]. Hygiene: TAG_ONLY=0, NOTES_MISSING=0 [UNVERIFIED — from the d11 handoff; today's run also prints 0/0]. Notably: **X8 (juniper-data#437, `equities_seq` 6.0.0 / `regression`) is NOT in any release** — data main is 7 commits ahead of `v0.16.0`, no 0.17.0 exists [VERIFIED 2026-10-03: compare API + PyPI]; recurrence main now admits `juniper-data<0.17.0`
>    (recurrence#188, dependabot, 10-02) but is unreleased (PyPI 0.5.0) [CHANGED SINCE HANDOFF: the cap was `<0.16.0`]; cascor#672 (version reporting) and canopy#663 are merged-unreleased. Before any cut, see Key context "Before any release cut".
> 6. **[OWNER] Still-open questions**: PUBLISHING-PLAN §6 OQ-2/OQ-3/OQ-4; the Pi pull (PUBLISHING-PLAN §5.1); whether `juniper-deploy-test` goes to Docker Hub (REGISTRATION-PROCEDURE §10); **not yet put to the owner**: should juniper-data answer a fetch failure with `502`/`503` instead of `400 Invalid request parameters` (PUBLISHING-PLAN §5.2)? [UNVERIFIED — from the data handoff]
> 7. **[OWNER/design, carried]** juniper-data#409 (equities defaults, OPEN), juniper-cascor#582 (tier parity, OPEN) `[ALSO P5]`, Decision 12 / juniper-data#423 (OPEN, v1 spec, zero code) `[ALSO P5]`, model-core cap `juniper-model-core>=0.1.0,<0.4.0` kept deliberately. [VERIFIED 2026-10-03: `gh issue view`; cap on PyPI 0.10.0 requires_dist]
> 8. **[AGENT, optional] ml#2065** — six test files end direct execution at a stray mid-file `__main__` block, hiding 109 methods; keep one `__main__` block, last. [VERIFIED 2026-10-03: OPEN]
> 9. **[AGENT, owner-asked] Worktree/branch cleanup** per `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`. Still present: `wiggly-imagining-pine` (`7fb40892`, d11 session; its handoff merged in #2094 so nothing unique should remain), `cryptic-juggling-truffle` (`f4795f17`; confirm its staged copies are on main), `serene-swinging-beacon` (`df21367d`, data session; merged in
>    #2100), `fluffy-sniffing-mochi` on `wip/records-0924` (**ask the owner first**), plus local branches `wip/adhoc-scripts`, `wip/ceremony-latest-flag`, `wip/ceremony-run-data-0160`, `wip/ceremony-target-sha`, `wip/dockerhub-drift-gate` (marked deletable once ml#2079 merged — it did). No process runs from any of the four worktrees. Check each for uncommitted and ignored files first; never run
>    `util/remove_stale_worktrees.bash`. [VERIFIED 2026-10-03: `git worktree list`, `git branch --list`, `ps`]
> 10. **Known gaps (track/fix, none time-bound)** — listed under Context. [UNVERIFIED — from the data handoff]
>
> **Key context**: releases, deploy gates and every merge are the owner's, approved in YOUR session naming the PR; never approve a `pypi` gate; never handle a token. Read `HANDOFF_2026-10-03_release-and-distribution-consolidated.md` § "Context the remaining work needs" before running commands.

---

## Dependencies on other paths

- **P5 (partition arc / Decision 12)**: P5's PRs that wait on juniper-data 0.16.0 can proceed — **0.16.0 is on PyPI (2026-09-24 18:35Z) and GHCR, pinned in deploy** [VERIFIED 2026-10-03]. Anything in P5 that needs **X8 / `equities_seq` 6.0.0** waits on the *next* juniper-data release (none exists; owner-gated, item 5 here). juniper-cascor#582 and juniper-data#423 are carried here as owner questions but belong substantively to P5 `[ALSO P5]`.
- **P3 (defect register round 42)**: P3's observability release gate overlaps item 5 — juniper-observability is still **0.4.0** on PyPI (2026-06-14) with 3 unreleased SHIP changes [CHANGED SINCE HANDOFF: detect.py 2026-10-03 — canopy 23, observability 3; was 2, ml#2086 added one]. Any observability cut runs through the same owner-gated ceremony and the cautions below; coordinate so only one session cuts it.
- **P2 (canopy)**: canopy's 23 unreleased SHIP changes [CHANGED SINCE HANDOFF: detect.py 2026-10-03 — canopy 23, observability 3; was 14] and canopy#663 ship only with a canopy release (item 5). X8 aligns `equities_seq`'s `task_type` with the label canopy already uses; canopy sees it only after the next data release.
- **P7 (logging) / P6 (perf)**: cascor's 17 unreleased SHIP changes (including cascor#672, which fixes the published 0.11.0 image reporting `0.6.0`) ship with the next cascor release — any path waiting on cascor on PyPI waits on item 5.

## Context the remaining work needs

### Rules (from the data handoff; owner-set)

- **Every merge you perform needs the owner's explicit approval naming that PR, in your session.** `gh pr merge --auto` on a MERGEABLE PR merges on the spot; `update-branch` on an armed PR completes its merge. Merge with `python3 util/safe_merge.py --repo <repo> --pr <n> --merge-method squash --execute` and read its `MERGED` line, never its exit status. Under `strict`, only once approved, a `BEHIND` PR gets `gh api -X PUT repos/pcalnon/<repo>/pulls/<n>/update-branch`, one at a time.
- **The PR sweeper is the owner's** ("Mine: fix forward"). Never draft/disarm a PR to hold it. Validate before the PR exists: `gh api -X POST repos/pcalnon/<repo>/git/refs -f ref=refs/heads/<branch> -f sha=<main sha>` → `python3 util/push_signed_commit.py --repo <repo> --branch <branch> --expected-head <main sha> …` → validate → `gh pr create`.
- **Commit only through the API** (`util/open_signed_pr.py`, `util/push_signed_commit.py`); never `git push`, never `PUT /contents` (unsigned). Helpers send whole files: re-probe `commits/main` and diff each file before every upload.
- **Search open and just-merged PRs for the same fix first.** After any head move on your PR, re-read `gh pr diff <n>`; per-file counts are only a screen (juniper-data#439: a conflict resolved in the PR's favour turned `CHANGELOG.md +26 −23` into `+0 −71` with every check green). If main already carries your fix, close your PR.
- **Never handle a token** — no `gh secret set`/`gh variable set` for Docker Hub or `CROSS_REPO_DISPATCH_TOKEN`. A token seen in chat: do not repeat it; tell the owner to delete it at the issuer (Docker Hub: REGISTRATION-PROCEDURE §8).
- **Never approve a `pypi` gate.** `util/release_train/ceremony.py --execute` only after the owner approves both the cut and the archive PR's auto-merge in your session (the tool arms that merge before it cuts).
- **A later ruling resting on a premise you are changing → ask the owner**, do not pick (happened with 0.16.0's notes, PUBLISHING-PLAN §5.2).
- **Re-probe every claim, this file's included.** Scripts go in `util/ad-hoc/`, never `/tmp`.
- **Memory index is full** (~25,000-character limit, measure with `wc -m`). Add no index line; link new memories from an indexed one. No live memory is retired to make room (owner, 2026-09-21).

### Wave 4 specifics (data handoff)

- Credential check, names only, on juniper-cascor, juniper-cascor-worker, juniper-canopy, juniper-data, juniper-recurrence (REGISTRATION-PROCEDURE §5.1): every listing carries `--jq '[.secrets[].name]'` / `--jq '[.variables[].name]'` (a bare variables GET prints values). `environments/dockerhub/secrets` = `DOCKERHUB_TOKEN` (+ `DOCKERHUB_USERNAME` if a secret), nothing else;
  `environments/dockerhub/variables` = `DOCKERHUB_USERNAME` if a variable; `actions/secrets` / `actions/variables` hold no `DOCKERHUB_*`; `environments/dockerhub/deployment-branch-policies` with `--jq '[.branch_policies[] | .type + ":" + .name]'` still shows `tag:juniper-*-v*` and `tag:v*`. A variable's value only as a boolean: `--jq '.variables[] | select(.name=="DOCKERHUB_USERNAME") |
  (.value=="<Docker ID>")'`. **Never print it.** `false` means only a mismatch; the owner looks with REGISTRATION-PROCEDURE §6.
- Workflow change: never name `dockerhub` unconditionally on the existing `build`/`merge` job (a tags-only environment rejects PR and dispatch runs). Pick a shape from REGISTRATION-PROCEDURE §3/§7; read the username from the context the owner chose (`vars.`/`secrets.`); each new job gets a job-level release-tag `if:` (`'v'`, or `'juniper-recurrence-v'` in recurrence); **never pass the credential as `--build-arg`** (published in public SLSA provenance).
- Dispatch replay (owner approval each time): `gh api -X POST repos/pcalnon/juniper-recurrence/dispatches --input <file>` with `{"event_type":"juniper-data-published","client_payload":{"source":"juniper-data","version":"<X.Y.Z>","sha":"<tag sha>"}}`; confirm a `juniper-data-published` run started (PUBLISHING-PLAN §5.2). The 0.16.0 replay's bench passed (recurrence run 36046705575). The d11 handoff
  recorded two non-blocking residual gaps in recurrence#178; **both are closed** [CHANGED SINCE HANDOFF: the concurrency group was fixed by juniper-recurrence#185 (merged 2026-09-23 20:22:55Z); the missing-listener-reads-as-success gap by juniper-data#431 (merged 2026-09-23 22:58:39Z, contained in `v0.16.0`), per #178's last comment — VERIFIED 2026-10-03: `gh pr view`, compare `v0.16.0...35b44cc1`
  = behind]. #178 itself is OPEN, because the token is not widened yet.
- After Wave 4, docker.io pulls follow REGISTRATION-PROCEDURE §9 (nodes log in with their own read-only token; nodes sharing an account share its 200 pulls / 6 h). **The Pi pull** (PUBLISHING-PLAN §5.1) is an anonymous GHCR pull of worker 0.6.1, owed before any Pi runs a Juniper image; needs 64-bit Pi OS; `turing` was reported down 09-22. [UNVERIFIED — from the data handoff]

### The egress guards as merged (the text item 1 writes into PUBLISHING-PLAN)

Guards are a **static model** of the rendered chart and `docker-compose.yml`, never a live CNI or Docker daemon, and they **fail closed**: an unmodelled construct fails a test. #236: Helm — policyTypes defaulting, namespace-aware selection (`matchExpressions` refused), `hostNetwork` and Lists refused, no other policy kinds, projected tokens, a policies-off check covering every policy type (#235
had weakened it); Compose — no `include`, no external alias, no `dns`/`extra_hosts` on juniper-data. Mutation checks at deploy `b2f8a428`: compose 25/25, Helm 34/34. The data pod mounts no service-account token (#233). [VERIFIED 2026-10-03: #236 MERGED `b2f8a428`; deploy main since then holds only two dependabot CI bumps (#237, #238)]

### Before any release cut (d11 handoff) [UNVERIFIED — round-1 correction unchecked; the cron claim re-probed]

- Run `util/ad-hoc/2026-09-23_released_section_drift.py` against the previous release's archive.
- Run the ceremony from a clean worktree at `origin/main` (it reads its own code and the CHANGELOG from `--repo-root`; dates sections in UTC).
- The daily `release-train.yml` cron cannot cut: `RELEASE_TRAIN_MODE` is unset and the ceremony/proposal jobs skip. [VERIFIED 2026-10-03: variable list shows only `RELEASE_TRAIN_APP_ID`; run 37010831363 (10-02) skipped both]
- A release cut under an open PR merges CHANGELOG entries silently into the released heading (harness memory).

### Traps

- **Run anything importing cascor with `env -u LD_LIBRARY_PATH`** (rust_mudgeon libtorch → `undefined symbol: _PyCode_SetExtra`, looks like a wheel defect).
- **Never write `killpg(getpgid(pid))` in a test helper**: a nohup'd stub shares the runner's process group. The five remaining `_force_kill` copies call `tests/process_cleanup.py::force_kill` and are handed only `setsid` leaders.
- `open_signed_pr.py` can 502 after creating the branch, leaving an empty ref at base — check the ref, recover with `util/push_signed_commit.py --expected-head <base>` then `gh pr create`.
- `git log <base>..origin/main -- <paths>` immediately before a whole-file upload (caught a near-clobber of #2056's CHANGELOG entry).
- CodeQL can block a merge on empty `except: pass` with all required checks green; after fixing, resolve threads via GraphQL once `code-scanning/alerts?ref=refs/pull/N/merge` shows `fixed`.
- Sequence Safety: waive with `Allow-Symbol-Loss: func:<a> func:<b>` in the **last trailer paragraph**; check with `git interpret-trailers --parse < body.txt`. juniper-ml/juniper-deploy squash with `COMMIT_MESSAGES`; the symbol-loss screen regex-matches every line, but git's trailer parser would not.
- Worktree-isolated shells refuse compound commands mixing `git`/`gh` (loops over `gh`, `$(cat …)` in a `gh` arg, `--jq` chained with `&&`/`;`, `docker run --entrypoint sh -c`, chained heredocs). A refused command drops its heredoc. Use single commands, `--body-file`, the Write tool.
- `docker compose down` skips profile-only services (juniper-data) without `--profile`; always pass a unique `-p <project>` (the owner's `juniper-deploy_*` volumes are on this host).
- Verify the published artifact, not the merge; pull before measuring (`2>&1 | wc -l` counts pull progress). A Helm render test can pass vacuously — the fullname helper collapses names containing `juniper`; select by label and prove the selector finds something.
- Publish the criterion beside any count (the d11 session nearly published "six" for five and a count taken after the wrong `__main__`).
- Mechanisms (PUBLISHING-PLAN §5.2; memory `reference_juniper_deploy_image_publish_traps.md`): only committed files reach a CI image; a bare `.dockerignore` pattern matches the context root only; the check unit is the context root; a `/app`-only scan passes vacuously; never blanket-add `**/logs/` (canopy's is a symlink).

### Known gaps [UNVERIFIED — from the data handoff, except where tagged]

| gap | verdict |
| --- | --- |
| Worker image `HEALTHCHECK` is `kill -0 1` (worker `Dockerfile:119-120`); chart falls back to it (deploy `k8s/helm/juniper/values.yaml:336-337`); compose overrides with `/v1/health/ready` | fix when next editing the worker image |
| juniper-cascor#691: snapshots store the manager authkey twice (incl. `config_json`) and restore it; pre-2026-03-18 ones carry the old public default; post-fix keys don't round-trip. Latent: `_start_manager`'s only call is commented out (`cascade_correlation.py:2676`) | track [VERIFIED 2026-10-03: OPEN] |
| Compose egress unrestricted (any port/destination); on Docker < 28 with FORWARD ACCEPT, a LAN host routing `172.27.0.0/16` via the Docker host can reach juniper-data | track (stated in deploy `docs/REFERENCE.md`) |
| Helm rule verified as rendered, not CNI-enforced; IPv4 only (dual-stack SEC fetch can wait out 30 s); `tests/test_helm_networkpolicy_data_egress.py` accepted limits: peerless DNS rule (port 53 any address), Redis subchart allows all egress, default values only | track |
| Published cascor 0.11.0 reports `0.6.0`; its image fails item 5's serve-and-version check for good; cascor#672 fixes from the next release | track [VERIFIED 2026-10-03: #672 MERGED, cascor still 0.11.0] |
| cascor `CHANGELOG.md` repeats category headings (cosmetic; only a repeated *version* heading harms `ceremony.py`) | track |
| Worker source-checkout fallback literal reads `"0.6.0"` at 0.6.1 (`juniper_cascor_worker/__init__.py:35`) | track |
| Stale-pin check (juniper-deploy#226) advisory: no schedule, no `--fail-on-stale` | track |
| Release train doesn't count image-only/packaging changes as SHIP (PUBLISHING-PLAN §5.2) | track |
| worker#194's lock refresh never functionally tested | track |
| `dockerhub` drift gate's live half skips in CI: `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_publish_env_policy_drift.py` | track |
| Deploy network tables omit `juniper-data` from the `backend` row (deploy `docs/REFERENCE.md` § Docker Networks, § Network Isolation; `docs/DEVELOPER_CHEATSHEET.md`) | track |
| juniper-data#422, canopy#663, cascor#672 closed on main but unreleased; the wheel probe sees data#422 (JD-6/7) and cascor#672 (CC-5); no check covers canopy#663 | track [VERIFIED 2026-10-03: canopy#663, cascor#672 MERGED; no new releases] |
| `MEMORY.md` oscillates around its ~25,000-character limit as concurrent sessions compact/undo; over the limit new sessions lose the last lines — **for Paul** | track [UNVERIFIED — d11 handoff] |

## Verification commands

```bash
# Run from a juniper-ml worktree; one gh/git command per line (isolated shells refuse compounds).
curl -s https://pypi.org/pypi/juniper-ml/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"     # 0.10.0
curl -s https://pypi.org/pypi/juniper-data/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"   # 0.16.0 (0.17.0+ => X8 may have shipped; check its CHANGELOG)
gh api repos/pcalnon/juniper-data/compare/v0.16.0...main --jq .status                                   # ahead (X8 unreleased)
gh run list -R pcalnon/juniper-data --workflow notify-consumers.yml --limit 3                          # only 35808713744 unless the token moved
gh issue view 178 -R pcalnon/juniper-recurrence --json state                                            # OPEN
gh api repos/pcalnon/juniper-data/environments/dockerhub/secrets --jq '[.secrets[].name]'              # [] until Wave 4
gh issue view 2062 -R pcalnon/juniper-ml --json state                                                   # OPEN
gh issue view 2065 -R pcalnon/juniper-ml --json state                                                   # OPEN
git show origin/main:notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md | grep -n '#236\|union'   # no #236 until item 1 lands
gh api repos/pcalnon/juniper-deploy/contents/docker-compose.yml -H "Accept: application/vnd.github.raw" > <scratch>/compose.yml   # then grep 'juniper-data:0' -> :0.16.0 at 164, 523
gh api repos/pcalnon/juniper-recurrence/contents/juniper-recurrence/pyproject.toml -H "Accept: application/vnd.github.raw" > <scratch>/rec.toml   # then grep '<0.17.0' at 97, 106
git worktree list | grep -E 'wiggly-imagining-pine|cryptic-juggling-truffle|serene-swinging-beacon|fluffy-sniffing-mochi'   # 4 lines (the unfiltered list prints ~186)
python3 util/release_train/detect.py --repo-root . --ecosystem-root /home/pcalnon/Development/python/Juniper | tail -2   # exit 1 is normal; needs network
```

## Dispositioned / closed items

| item | source | disposition | evidence |
| --- | --- | --- | --- |
| Verify 0.10.0 on PyPI + `[servers]` upgrade plan | d11 handoff | Done | PyPI 0.10.0 (09-23 19:54Z); `requires_dist` shows `juniper-data>=0.15.0`. Dry-run evidence was scratch (re-run in a venv holding `juniper-data==0.14.0` if needed) |
| ml#2046 `_force_kill` | d11 handoff | Closed by ml#2061 | issue CLOSED 09-23 21:04:38Z |
| Wheel-contract probe SKIP-as-pass | d11 handoff | Fixed, ml#2063 | merged `6848e11d`; `reports/2026-09-23_decision11-wheel-contract-probe-0.10.0/` |
| cascor-client `[Unreleased]` lockfile bullet | d11 handoff §A 5c | No release needed (no package code since v0.8.0) | d11 handoff compare; cascor-client still 0.8.0 |
| 0.15.0 wheel ships its tests; stale conda pins (don't sweep shared envs); `NPZ_SPLITS` in `.constants` | d11 handoff §A 5d | Known and bounded, no action | from `HANDOFF_2026-09-22_decision-11-re-evaluated-and-two-releases-cut.md` §3 |
| d11 handoff PR (§10 PARTITION-PLAN row + the file) | d11 handoff | Merged ml#2094 | 2026-09-26 01:03:22Z `a4bdb92d` |
| Data handoff archiving PR | data handoff item 4 | Merged ml#2100 **without** the PUBLISHING-PLAN guard rewrite → carried as item 1 | 2026-09-26 08:32:34Z `16094264`; files list |
| juniper-deploy#230 data pin 0.16.0 | data handoff | Done | compose `:164`, `:523` = `0.16.0` |
| deploy#231–#236 egress network + guards | data handoff | Merged | #236 `b2f8a428`; no later egress commits |
| juniper-data#439 (X8 to `[Unreleased]`) | data handoff | Closed unmerged (destructive head); correction comment posted | [VERIFIED 2026-10-03: gh pr view — CLOSED 09-24 19:03:54Z, not merged] |
| cascor-worker#198/#199/#200 (`.env.example` authkey; CHANGELOG corrections) | data handoff | Merged; key handling deferred to cascor#691 | [VERIFIED 2026-10-03: gh pr view — all three MERGED 09-24/25] |
| recurrence cap `juniper-data<0.16.0` | data handoff known gap | **Superseded**: recurrence#188 (dependabot, 10-02 21:23Z) raised it to `<0.17.0` on main; unreleased (PyPI 0.5.0) | recurrence `pyproject.toml:97,106` |
| Docs: Juniper/AGENTS.md Data Contract (X8 not in 0.16.0; arc_agi 4.0.0) | data handoff | Done (unversioned, owner-approved) | current AGENTS.md text |
| Owner-gate fact "PyPI deploy approved / recorded" and deploy repin | `…cut-at-one-commit-….md` items 1–2 | Done, per the data handoff | data 0.16.0 on PyPI |
| Remote branch juniper-data `docs/changelog-x8-to-unreleased` | data handoff | Deleted; `322135bd` reachable via #439 | [VERIFIED 2026-10-03: matching-refs returns `[]`] |

## Git state

- This consolidation: worktree `snappy-strolling-waterfall`, branch `docs/handoff-consolidation-2026-10-03` (from `afb02801`); this file plus SUPERSEDED banners on the two sources, uncommitted.
- Source-session worktrees still present [VERIFIED 2026-10-03: `git worktree list`]: `wiggly-imagining-pine` @ `7fb40892` (`worktree-wiggly-imagining-pine`), `cryptic-juggling-truffle` @ `f4795f17`, `serene-swinging-beacon` @ `df21367d`, `fluffy-sniffing-mochi` @ `5779e4c8` on `wip/records-0924`. No running process references any of them (`ps`).
- Local branches still present: `wip/adhoc-scripts`, `wip/ceremony-latest-flag`, `wip/ceremony-run-data-0160`, `wip/ceremony-target-sha`, `wip/dockerhub-drift-gate`, `wip/records-0924`.
- Open juniper-ml PRs: none [VERIFIED 2026-10-03]. Remote branch `docs/handoff-data-0-16-0-egress-guards-fail-closed`: merged as #2100 and deleted [VERIFIED 2026-10-03: `git/matching-refs` returns `[]`].
- Other repos' mains since the sources: juniper-data main is 7 commits ahead of `v0.16.0` (X8 #437, #438, #440 security fix, three dependabot, one more); juniper-deploy two CI bumps; juniper-recurrence #186 (09-24), #187, #188. juniper-canopy: 9 substantive merges after the d11 handoff (#676, #678–#685; 09-23/24, incl. #682 the X8 agreement pin and #678/#683/#685 security fixes) plus 5 dependabot
  merges on 10-02 (#686–#688, #690, #691). juniper-cascor: #684, #685, #687–#690 (09-24/25; #686 is not on main) plus 4 dependabot merges on 10-02 (#692–#694, #696). [VERIFIED 2026-10-03: `commits?sha=main&since=2026-09-23`]
