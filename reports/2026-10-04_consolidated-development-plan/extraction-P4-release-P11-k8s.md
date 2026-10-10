# Extraction — P4 release & distribution (+ P11 k8s primer)

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04T20:54Z–21:09Z (PyPI JSON; `gh api` REST only, no GraphQL; worktree `git` at `cf711cf4` = origin/main)

## 0. Sources read

Keys used below → filenames (all read; `prompts/…` = `prompts/thread-handoff_automated-prompts/`):

| key | file | read |
|---|---|---|
| RD | `prompts/…/HANDOFF_2026-10-03_release-and-distribution-consolidated.md` | full |
| K8 | `prompts/…/HANDOFF_2026-10-03_k8s-primer-consolidated.md` | full |
| IDX | `prompts/…/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md` | full |
| D11 | `prompts/…/HANDOFF_2026-09-23_decision-11-round-4-0-10-0-delivered-force-kill-fixed-servers-gap-filed.md` | full |
| DH | `prompts/…/HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md` | full |
| K8S | `prompts/…/HANDOFF_2026-09-24_k8s-primer-end-to-end-secure-automated-juniper-cluster.md` | full |
| PP | `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` | L1–141, §5 (L302–431), L520–560, L690–874 |
| RP | `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` | L1–97, §7–§11 (L505–695) |
| PPP | `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` | §11 (L477–676) |
| PTP | `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` | §10 (L448–558) |
| RTP | `notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md` | Phase 5 + §13 (L607–640); grep elsewhere |
| RB | `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md` | grep for pending markers only |
| EQ | `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (ml#2116, merged after the consolidation) | grep + W1.11/W1.13/milestones/R1–R8 |
| R42 / P5H / P2H / P6H | the P3, P5, P2, P6 consolidated handoffs (`HANDOFF_2026-10-03_defect-register-round-42-…`, `…partition-arc-decision-12-…`, `…canopy-…`, `…perf-lane-…`) | dependency sections only |
| — | `util/release_train/registry.yaml`, `util/release_train/detect.py` L1–100, L908–1000 (read, not run); memory `project_container_registry_rollout_2026-09-08.md` (tail); recurrence #178 comments; ml#2062 body | as stated |

Not read: juniper-k8s contents (private, out of juniper-ml scope); GHCR tag lists (see §8).

## 1. Work items

Gate keys: S=STARTABLE, OD=OWNER-DECISION, OA=OWNER-ACTION, B=BLOCKED-ON. "detect unit" = `detect.py` counts distinct **files** with a substantive ship-path hunk, not PRs (`detect.py:951-975`).

| ID | Item | Source | Live status | Gate | Depends on | Repo(s) | Eff | Crit |
|---|---|---|---|---|---|---|---|---|
| P4-01 | Rewrite PP status block (L30-32) and §5.2 (~L720-736) as the static fail-closed guard model; record juniper-deploy#236; new PR, validated before `gh pr create` | RD item 1 | [VERIFIED 2026-10-04: grep `#236` in PP → 0; "union" L32, L722; no open ml PR for it; no `#236` anywhere in notes/, reports/, docs/] | S (merge OA) | — | juniper-ml | S | HYGIENE |
| P4-02 | Append deploy#236 to memory `project_container_registry_rollout_2026-09-08.md` (no index line) | RD item 1 | [VERIFIED 2026-10-04: `grep -c '#236'` = 0] | S | — | memory | S | HYGIENE |
| P4-03 | Optional: one scope-bounded lane judging deploy#236 against its stated scope | RD item 1; DH Remaining 4 | [VERIFIED 2026-10-04: no such report exists] | S | P8 (usage window) | juniper-deploy | S | HYGIENE |
| P4-04 | Correct PTP §10 2026-09-23 update: data#422 is RELEASED (in v0.16.0), not "not yet released" | PTP §10 L549-551 | [CHANGED SINCE HANDOFF: compare `ce436819...v0.16.0` = ahead 6/behind 0; data `[0.16.0]` records the #411 store conformance] | S | — | juniper-ml | S | DATA-INTEGRITY (record) |
| P4-05 | Ask owner to confirm the PAT also got **Actions: Read** (#431 confirm step) | RD item 2; #178 comment 09-23; P5H L98-101 | [UNVERIFIED — PAT scope not inspectable; recurrence is public, so the green "Confirm the consumer started a run" step proves nothing about it] | OA | — | juniper-data | S | HYGIENE |
| P4-06 | On next data release, verify publish.yml's own `Notify consumer repos` job + recurrence bench run both green | P5H L118 bar | [VERIFIED 2026-10-04: #178 closed on workflow_dispatch run 37114403856 (success) + bench 37114410788 (success); publish.yml:77-85 calls the same reusable workflow/secret; release path unexercised since widening] | B P4-12 | P4-12 | data, recurrence | S | UNBLOCKER |
| P4-07 | Wave 4 credential: owner runs RP §2, §5.2B-3a, §4, §5.2B-3, §6; reports 4 facts (login ok, 3a form, Docker ID, expiry) | RD item 3; RP header | [VERIFIED 2026-10-04: `environments/dockerhub/secrets` = [] in all 5 repos; variables [] in data/cascor/recurrence; data policies `tag:juniper-*-v*`,`tag:v*`; data publish-image.yml 0 `DOCKERHUB_`/`docker.io`] | OA (secrets) | — | 5 image repos | M | UNBLOCKER |
| P4-08 | Record CI-token expiry in RP §10 by PR | RD 3(a) | [VERIFIED 2026-10-04: §10 row "not set yet"] | B P4-07 | P4-07 | juniper-ml | S | HYGIENE |
| P4-09 | Names-only credential check on 5 repos (RP §5.1/§6; boolean-only username check); run drift gate locally (`JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`) | RD 3(b); DH gap | [NOT RE-PROBED — nothing registered yet] | B P4-07 | P4-07 | 5 repos | S | SAFETY |
| P4-10 | Pick Wave 4 shape (RP §3/§7: release-only job vs conditional env), then edit 5 `publish-image.yml`; release-tag job `if:`; no credential as build-arg | RD 3(c); RP §7, §10 | [VERIFIED 2026-10-04: not started] | B P4-07, P4-09 + owner go-ahead | P4-07, P4-09 | 5 repos | M | USER-FACING |
| P4-11 | Pi nodes `docker login` with a separate read-only token (expiry into RP §10) | RP §9-§10 | [NOT RE-PROBED — deployment work] | OA (host) | P4-07; P11-03 | hosts | S | SAFETY |
| P4-12 | Cut next juniper-data release (X8 #437, #436, #438, #440); pre-cut: drift check vs v0.16.0 archive, clean origin/main worktree, `--target-sha`, tag-window check | RD item 5; R42 L65, L326 | [VERIFIED 2026-10-04: PyPI 0.16.0; main 9 ahead of v0.16.0 (CHANGED: was 7; +#444, #445 CI); 4 commits / 7 .py files in `juniper_data/`; no open data PR] | OA (cut) + B P3 item 1 | P4-13; P3 item 1 (+ data F-PR) | juniper-data | M | USER-FACING |
| P4-13 | Decide whether X8's `[Unreleased]` entry carries a breaking marker (renderer computes NO; `dataset_id` changes) | R42 L320 | [VERIFIED 2026-10-04: entry under `### Changed`, no Breaking/BREAKING marker; it says "nothing breaks"] | OD | — | juniper-data | S | DATA-INTEGRITY |
| P4-14 | After P4-12: deploy pins (compose :164, :523; helm values.yaml:40), one PR per pin; raise recurrence bench cap `<0.17.0`; ml floor `juniper-data>=0.17.0`; canopy→recurrence→data smoke; parent AGENTS.md (unversioned) | EQ W1.11; DH gap | [VERIFIED 2026-10-04: compose pins 0.16.0 at :164/:523; recurrence pyproject:97,106 `<0.17.0`] | B P4-12 | P4-12; P4-20 | deploy, recurrence, ml | M | USER-FACING |
| P4-15 | Cut canopy release (EQ targets 0.9.0) | RD item 5; IDX; P2H L120-121 | [VERIFIED 2026-10-04: PyPI 0.8.1; 58 commits since v0.8.1; 42 touch ship paths (incl. src/tests); 23 .py files + runtime-dep pyproject edits (#689-#693); incl. #663, #694/#696/#697 (merged 10-03 10:14Z → 10-04 11:15Z), security #678/#683/#685; `[Unreleased]` ≈790 lines; 4 Cursor drafts #698-#701 open] | OA | soft: P3 item 2 (canopy#685 unvalidated) | juniper-canopy | M | USER-FACING |
| P4-16 | Cut cascor release (ships #672 version fix, #683 BLAS-2 default, logging P0.4/P1.x, #676, security #659/#689) | RD item 5; P6H L72 | [VERIFIED 2026-10-04: PyPI 0.11.0; 57 commits since v0.11.0; 31 touch ship paths; 19 in-scope .py files (detect 10-03: 17/1/1, NOT RE-PROBED)] | OA | soft: P3 item 2 (cascor#690 unvalidated), P3 item 4 cascor F-PR | juniper-cascor | M | USER-FACING |
| P4-17 | Release juniper-observability + juniper-service-core (Sentry key-capture fix ml#2086; sc #1974); cap PRs first if a bump crosses a cap; one session only | RD Deps; R42 L50-58, L223-230 | [VERIFIED 2026-10-04: PyPI 0.4.0 / 0.7.0; 5 / 2 commits touch pkgs; F2 `before_send_transaction` absent; caps obs `<0.5.0` canopy:109, rec:79; sc `<0.8.0` canopy:119, data:110, cascor:105, rec:51, ml:94] | OD + B P3 item 4 | P3 item 4 (ml F-PR F2/F6/F9/F10, sc F3/F5) | ml (+5 consumers) | M | SAFETY |
| P4-18 | Cut juniper-recurrence app release (EQ: 0.6.0); raise juniper-ml `[recurrence]` caps before/with it | RD item 5; P5H L63, L119; P2H L121-122; EQ W1.13 | [VERIFIED 2026-10-04: PyPI 0.5.0; 19 commits since tag; 1 touches app pkg (#172 feat); 7 .py files; data-client cap `<0.6.0` (pyproject:54); juniper-ml pyproject:104-106 caps `<0.6.0`/`<0.4.0`] | OA + content B | P5 W4; P2 Lane B 2a; EQ P1 items | juniper-recurrence, ml | M | UNBLOCKER |
| P4-19 | Decide whether to release juniper-cascor-model (worker depends on it) | RD item 5 (number only) | [VERIFIED 2026-10-04: PyPI 0.1.0 (06-14); 15 commits touch `juniper-cascor-model/` since tag; detect 10-03 7/0/0 NOT RE-PROBED] | OD | — | juniper-cascor | S | HYGIENE |
| P4-20 | juniper-ml meta release (LAST per RTP §13) carrying P4-14 floor, P4-18 caps, P4-21 fix | RTP §13; EQ target 0.11.0 | [VERIFIED 2026-10-04: PyPI 0.10.0; 72 commits since v0.10.0, 0 pyproject changes] | OA + B | P4-14, P4-18, P4-21 | juniper-ml | S | UNBLOCKER |
| P4-21 | ml#2062 `[servers]` installs no client: options (a)/(b) need a release, (c) docs only | RD item 4 | [VERIFIED 2026-10-04: OPEN, 0 comments, upd 09-23; README.md:124; test_pyproject_extras.py:149-152 pins bare form] | OD | — | juniper-ml | S | USER-FACING |
| P4-22 | ml#2065: keep one `__main__` block, last, in six test files (109 hidden methods) | RD item 8 | [VERIFIED 2026-10-04: OPEN] | S | — | juniper-ml | S | HYGIENE |
| P4-23 | Clean up worktrees wiggly-imagining-pine, cryptic-juggling-truffle, serene-swinging-beacon; `wip/{adhoc-scripts,ceremony-latest-flag,ceremony-run-data-0160,ceremony-target-sha,dockerhub-drift-gate}`; fluffy-sniffing-mochi + wip/records-0924 **ask owner** | RD item 9 (`…WORKTREE-CLEANUP-PROCEDURE-V2.md`) | [VERIFIED 2026-10-04: all present, no process; branch files on main; run-data-0160 = a main commit] [NOT RE-PROBED: cryptic's staged files] | S; fluffy OD | — | ml | S | HYGIENE |
| P4-24 | OQ-2: `:X.Y.Z-cuda` variant for cascor/worker? release or on-demand? | PP §6 | [VERIFIED 2026-10-04: unruled] | OD | — | cascor, worker | — | RESEARCH |
| P4-25 | OQ-3: Pi RAM for a torch worker (gated by P4-27) | PP §6, §5.1 | [VERIFIED 2026-10-04: unruled] | OD | P4-27 | — | — | RESEARCH |
| P4-26 | OQ-4: versioned stack manifest from juniper-deploy? | PP §6 | [VERIFIED 2026-10-04: unruled] | OD | — | deploy | — | HYGIENE |
| P4-27 | Pi pull: anonymous GHCR pull + run of newest worker (0.6.1) on 64-bit Pi OS; owed before any Pi runs a Juniper image | PP §5.1; RD Wave 4 | [VERIFIED 2026-10-04: worker 0.6.1 still newest] ["turing down 09-22": UNVERIFIED — from DH] | OA (host) | P11-03 | hosts | S | UNBLOCKER |
| P4-28 | Should `juniper-deploy-test` publish to Docker Hub? | RP §10 | [VERIFIED 2026-10-04: open] | OD | P4-10 | deploy | S | HYGIENE |
| P4-29 | Put to owner: juniper-data fetch failure → 502/503 instead of `400 Invalid request parameters` | PP §5.2 L740 | [VERIFIED: "Still open, not ruled"] ["not yet put": UNVERIFIED — from DH] | OD | — | juniper-data | S | USER-FACING |
| P4-30 | data#409 equities defaults (overlaps EQ F-P1/R1) `[ALSO P5]` | RD item 7 | [VERIFIED 2026-10-04: OPEN, upd 09-21] | OD | — | data | — | USER-FACING |
| P4-31 | cascor#582 tier parity `[ALSO P5]` | RD item 7 | [VERIFIED 2026-10-04: OPEN, upd 08-29] | OD | — | cascor | — | DATA-INTEGRITY |
| P4-32 | Decision 12 / data#423 `[ALSO P5]` | RD item 7 | [VERIFIED 2026-10-04: OPEN, upd 09-23] | OD | P5 | data | — | DATA-INTEGRITY |
| P4-33 | model-core cap `<0.4.0` kept deliberately (no action) | RD item 7 | [VERIFIED 2026-10-04: juniper-ml pyproject:92] | — | — | ml | — | — |
| P4-34 | Worker HEALTHCHECK `kill -0 1`; fix when next editing the image (chart falls back to it) | RD gaps | [VERIFIED 2026-10-04: worker Dockerfile:119-120] [chart values.yaml:336-337 NOT RE-PROBED] | S (on next edit) | P4-41 | worker, deploy | S | HYGIENE |
| P4-35 | Worker source-checkout fallback literal `"0.6.0"` at 0.6.1 | RD gaps | [VERIFIED 2026-10-04: `__init__.py:35`] | S | — | worker | S | HYGIENE |
| P4-36 | cascor#691 authkey stored twice/restored (latent) | RD gaps | [VERIFIED 2026-10-04: OPEN, upd 09-25] | track | — | cascor | M | SAFETY |
| P4-37 | Compose egress unrestricted; Docker<28 FORWARD ACCEPT exposure | RD gaps | [NOT RE-PROBED — track] | track | — | deploy | — | SAFETY |
| P4-38 | Helm rule rendered-only, IPv4-only, test's accepted limits | RD gaps | [NOT RE-PROBED — track] | track | — | deploy | — | SAFETY |
| P4-39 | Published cascor 0.11.0 reports `0.6.0`; image fails item-5 check for good | RD gaps | [VERIFIED 2026-10-04: still 0.11.0; #672 on main] | B P4-16 | P4-16 | cascor | — | USER-FACING |
| P4-40 | cascor CHANGELOG repeats category headings (preview before P4-16) | RD gaps | [NOT RE-PROBED] | track | P4-16 | cascor | S | HYGIENE |
| P4-41 | Release train ignores image-only/packaging changes; RTP Phase 5.2 Q-NONSHIP needs a dated adopt/decline | RD gaps; PP §5.2 L535-541; RTP 5.2 | [VERIFIED 2026-10-04: RTP 5.2 has no dated decision] | OD | — | ml | M | HYGIENE |
| P4-42 | Stale-pin check (deploy#226) advisory: no schedule, no `--fail-on-stale` | RD gaps | [NOT RE-PROBED] | track/OD | — | deploy | S | HYGIENE |
| P4-43 | worker#194 lock refresh never functionally tested | RD gaps | [NOT RE-PROBED] | track | — | worker | S | HYGIENE |
| P4-44 | Deploy network tables omit juniper-data from `backend` row | RD gaps | [NOT RE-PROBED] | S | — | deploy | S | HYGIENE |
| P4-45 | No wheel check covers canopy#663; re-run wheel-contract probe after releases | RD gaps | [VERIFIED: #663 on canopy main, unreleased] | B P4-15 | P4-15 | ml | S | HYGIENE |
| P4-46 | MEMORY.md at its load limit — for Paul | RD gaps | [VERIFIED 2026-10-04: `wc -m` = 24,993 of ~25,000] | OD | — | memory | — | HYGIENE |
| P11-01 | Decide whether to add juniper-k8s to parent `Juniper/CLAUDE.md` (unversioned) | K8 goal | [VERIFIED 2026-10-04: table lists 9 repos, no juniper-k8s] | OD | — | parent dir | S | HYGIENE |
| P11-02 | Clean up worktree `zany-juggling-goblet` (5af9d722) | K8 Git state (not carried) | [VERIFIED 2026-10-04: present; remote `docs/k8s-primer*` refs [] ; no process] | S (owner-asked) | — | juniper-ml | S | HYGIENE |
| P11-03 | juniper-k8s Pi cluster go-live will consume P4 images; needs P4-27 and (docker.io) P4-11 | K8 Deps | [VERIFIED 2026-10-04: k8s PRs #4-#7 (Pi inventory, kernel, kubelet/container scripts) merged 09-27..10-01; private] | track | P4-27, P4-11 | juniper-k8s | — | UNBLOCKER |

P11 closure: [VERIFIED 2026-10-04: ml#2101 merged 2026-09-25T02:17:24Z `b82d12d7`; #2098 merged 01:47:48Z; #2104 merged 2026-09-26T10:20:36Z `4b5227e3`; no primer reference in juniper-ml outside the two k8s handoffs]. K8S's hardware/currency "leads" stay [UNVERIFIED — from K8S]; superseded by the validated primer in juniper-k8s. Closed items not re-listed: token widening (DONE; recurrence#178 CLOSED 2026-10-03T10:16:15Z).

## 1b. Release queue

"since" = commits on `main` after the tag (compare API); "ship" = commits touching `ship_paths` / in-scope `.py` files (detect's unit).

| package | PyPI | latest tag / Release | changes on main since | blocking items | owner-gated? |
|---|---|---|---|---|---|
| juniper-data | 0.16.0 (09-24) | v0.16.0 @`39d1cab2` (09-24) | 9 commits; 4 ship / 7 files | P3 item 1; P4-13 | yes |
| juniper-canopy | 0.8.1 (09-18) | v0.8.1 (09-18) | 58; 42 ship (incl. tests) / 23 files + deps | soft P3 item 2 | yes |
| juniper-cascor | 0.11.0 (09-10) | v0.11.0 (09-09) | 57; 31 ship / 19 files | soft P3 items 2, 4 | yes |
| juniper-observability | 0.4.0 (06-14) | `-v0.4.0` (Release 07-20, tag commit 06-14) | 5 touch pkg | P3 item 4; caps | yes |
| juniper-service-core | 0.7.0 (08-31) | `-v0.7.0` (08-31) | 2 | P3 item 4; 5 caps if 0.8.0 | yes |
| juniper-recurrence (app) | 0.5.0 (09-11) | `-v0.5.0` (09-10) | 19; 1 ship / 7 files | P5 W4, P2 2a, EQ P1; ml caps | yes |
| juniper-cascor-model | 0.1.0 (06-14) | `-v0.1.0` (06-14) | 15 touch dir; detect 7 files | none named | yes |
| juniper-ml (meta) | 0.10.0 (09-23) | v0.10.0 (09-23) | 72; 0 pyproject | releases last | yes |
| cascor-protocol 0.2.0, cascor-client 0.8.0, cascor-worker 0.6.1, data-client 0.5.0, recurrence-model 0.3.0, recurrence-client 0.3.0, model-core 0.3.2, ci-tools 0.9.0, doc-tools 0.1.2, config-tools 0.1.0 | = tag | Releases exist for each | 0 ship-path commits (config-tools: 2, py.typed + notes = discounted) | — (EQ targets data-client 0.6.0, model 0.4.0 later) | UP_TO_DATE |

No PyPI upload or GitHub Release in any repo after 2026-09-24 [VERIFIED 2026-10-04]. Release-train cron cannot cut: run 37210667083 (today) ran detection only, ceremony/proposal skipped; `RELEASE_TRAIN_MODE` unset (only `RELEASE_TRAIN_APP_ID`) [VERIFIED 2026-10-04].

## 2. Owner decisions pending

| ID | Question | Options / source recommendation | Blocks | Source |
|---|---|---|---|---|
| D-1 | ml#2062 `[servers]` | (a) servers' own client extras — "smallest change"; (b) add `[clients]`; (c) docs only | P4-20 content | ml#2062 body |
| D-2 | Next data release: cut once P3 item 1 validates? version? X8 breaking marker? | none stated; EQ targets 0.17.0 | P4-12, P4-13 | R42 L320, L326 |
| D-3 | obs/sc releases: (1) owner prepares and cuts both, or (2) agent opens bump+notes PRs at owner-named versions; who opens cap/lock/floor PRs | verbatim options, no pick | P4-17 | R42 L230 |
| D-4/5/6 | When to cut canopy, cascor, recurrence (versions; recurrence R8 "Breaking" in 0.6.0) | EQ R8 recommends 0.6.0 with "Breaking" | P4-15/16/18 | RD item 5; EQ R8 |
| D-7 | Release cascor-model? | — | P4-19 | detect output only |
| D-8 | Wave 4 inputs: Docker ID, public default privacy, `DOCKERHUB_USERNAME` variable vs secret | variable recommended | P4-07..10 | RP §2, §5.2B-3a |
| D-9 | OQ-2, OQ-3, OQ-4; juniper-deploy-test on Docker Hub | — | P4-24..28 | PP §6; RP §10 |
| D-10 | 502/503 vs 400 on fetch failure | not yet put | P4-29 | PP §5.2 |
| D-11 | Remove fluffy-sniffing-mochi / wip/records-0924? | ask first | P4-23 | RD item 9 |
| D-12 | Q-NONSHIP toggle (and Q-META later) | default "skip" stays | P4-41 | RTP Phase 5 |
| D-13 | Confirm Actions: Read granted | — | P4-05 | RD item 2 |
| D-14 | data#409, cascor#582, data#423 | carried `[ALSO P5]` | P4-30..32 | RD item 7 |
| D-15 | List juniper-k8s in parent CLAUDE.md | — | P11-01 | K8 |

## 3. Cross-path dependencies

| from | on | nature |
|---|---|---|
| P4-12 | P3 item 1 (data fix-forward, branch `fix/conditional-requests-round4-followups` @`94ce8b1f`, no PR [VERIFIED 2026-10-04]), then P3 item 4 data F-PR (F3, F5) | must merge + validate first |
| P4-17 | P3 item 4 juniper-ml F-PR (F2, F6, F9, F10; sc F3, F5) | validate before asking D-3 |
| P4-15 / P4-16 | P3 item 2 (canopy#685, cascor#690 unvalidated) | soft |
| P5 spec v3 item 1(a); P5 owner "release cuts" | P4-12, P4-16 (#672), P4-15 (#663) | data release before W6 → block moves to ≥0.18.0 |
| P5 W10 | P4-18 (recurrence release carrying W4's data-client cap) → P4-20 | hard |
| P2 C3; P2 Lane B tail | P4-12 (X8); P4-18 after 2a; P4-15 after wave 3; deploy pin bumps; ml `[recurrence]` cap | hard |
| P6, P7 | P4-16 (BLAS-2 default needs a release-notes line; logging on PyPI); P7 content rides any obs release | soft |
| EQ (no path owner yet) W1.11/W1.13, M1 2026-11-21 (owner to confirm) | P4-12, P4-14, P4-15, P4-18, P4-20 | publication order data-client 0.6.0 → model 0.4.0 → recurrence 0.6.0 → canopy 0.9.0 |
| P11-03 (juniper-k8s) | P4-27, P4-11 | Pi go-live |
| P4-03 | P8 | usage windows |
| P1, P9, P10 | — | none found |

## 4. Hazards

- A release cut under an open PR silently merges its CHANGELOG entries into the released heading; P3's data/cascor F-PRs and Cursor drafts #698-#701 edit the same files. Use `--target-sha` (0.16.0 nearly shipped a duplicate heading).
- `ceremony.py --execute` arms the archive PR's auto-merge before cutting: owner approves both in-session; never approve a `pypi` gate; never handle a token.
- Cap before bump: obs `<0.5.0` (×2), sc `<0.8.0` (×5), ml `[recurrence]` `<0.6.0`/`<0.4.0`, data-client `<0.6.0` (canopy:192, recurrence:54) → cap PRs land before the Release, lock/floor PRs after PyPI.
- Wave 4: never name `dockerhub` unconditionally on build/merge (rejects PR/dispatch runs); build-args are public in SLSA provenance.
- A Release mints wheel and image together; image-only fixes (P4-34/35) need a release the train will not propose.
- Cleanup: never run `util/remove_stale_worktrees.bash`; `worktree remove` deletes ignored files.
- detect's "23"/"17" are file counts; PR volume is roughly 2× (canopy: 58 commits).

## 5. Discrepancies

1. RD Known gaps "data#422 closed on main but unreleased" and PTP §10's S-1 note → #422 shipped in v0.16.0 (P4-04).
2. RD item 2 "#178 can close" → CLOSED 2026-10-03T10:16:15Z.
3. RD "data main 7 ahead of v0.16.0" → 9 (#444, #445).
4. IDX "canopy release (23 unreleased changes), cascor (17)" → files, not changes; canopy gained #694/#696/#697 after the 10-03 probe without moving the count.
5. P5H's bar ("a release's own notify job") ≠ the closure basis (workflow_dispatch); see P4-06.
6. K8 "last push 2026-10-01" → pushed_at 2026-10-03T19:17:58Z (no PR after #7).

## 6. Residue not carried by RD/K8

- EQ (ml#2116, merged 2026-10-03T19:06Z) W1.11/W1.13 release work and F-P4 "Blocker (deployment)": canopy refuses Recurrence + `equities_seq` against published 0.16.0 (P4-12, P4-14).
- PTP §10 stale S-1 line (P4-04).
- RTP Phase 5.2 Q-NONSHIP dated decision (P4-41).
- cascor-model release question (P4-19).
- Parent AGENTS.md "RELEASED to PyPI" paragraph after each release; EQ says "same PR as the last pin", but the file is unversioned (P4-14).
- `zany-juggling-goblet` worktree (P11-02).

## 7. Path assessment

- **Urgency**: SAFETY: P4-17. Running services can hand Sentry a real API key until it ships, and it is gated on P3 item 4. USER-FACING: P4-12 (X8). The equities path is refused against published images, and EQ M1 needs 0.17.0. Canopy/cascor carry live-verified P0/P1 and security fixes.
- **Leverage**: P4-12 unblocks P5, P2 C3, EQ W1.11 and P4-14/20. P4-18 unblocks P5 W10 and P2 Lane B. Bundling P4-21's fix, the P4-14 floor and the P4-18 caps into one juniper-ml release saves a cycle.
- **Cost**: each cut is S–M of agent time plus owner gates. Wave 4 is owner-blocked.
- **Next actions**:
  1. P4-01 + P4-04 (one validated juniper-ml records PR) and P4-02, all startable now.
  2. Hand the owner one release-decision packet: D-1, D-2/P4-13, D-3, D-4/5/6, D-13. Use the queue in §1b, in this order: obs/sc → cascor → data → canopy → recurrence → juniper-ml last.
  3. With P3, drive P3 item 1 → P4-12 → P4-06 and P4-14.

## 8. What this report cannot support

- I did not run `detect.py` (scripts forbidden). The sub-package detect counts are the 10-03 figures [NOT RE-PROBED]. My file counts skip detect's substantive-hunk filter.
- I did not probe GHCR (the gh token lacks `read:packages`, and I avoided the registry token exchange). "No new images" is inferred from there being no new Releases.
- The PAT's scope cannot be inspected. I could not read the staged files in other worktrees, or juniper-k8s's contents.
- I inferred that data#422 is in the 0.16.0 wheel from tag containment, not from reading the wheel.
- Rulings made after 10-03 in other sessions are invisible to me. EQ's milestone dates are "owner to confirm".
