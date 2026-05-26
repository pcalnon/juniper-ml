# Outstanding Work — Juniper Ecosystem (2026-05-26)

**Session**: `parsed-foraging-lollipop` (juniper-ml worktree)
**Author**: Paul Calnon (work driven via Claude Code)
**Last Updated**: 2026-05-26
**Scope**: Cross-repo status snapshot at end of the PyPI / extras / scheduled-tests / Update-Lockfiles / fastapi-MAL-2026-4750 work stream that ran 2026-05-22 → 2026-05-26.

This document captures **only what is still open or deferred** as of writing. Items that fully shipped (and the memory entries that record them) are linked but not repeated.

---

## TL;DR

- 🔴 **Active red CI**: `Security Scans` failing on juniper-data + juniper-canopy + juniper-cascor `main` due to **OSV `MAL-2026-4750`** flagging fastapi 0.136.3. Verified false positive (3 independent research angles + direct PyPI metadata check). No code fix; awaiting upstream retraction or PyPI yank.
- 🟡 **Active red CI**: `Pre-commit` failing on juniper-cascor `main` due to **end-of-file-fixer** wanting to add a trailing newline to auto-generated `src/tests/performance/baselines/baseline_20260525.json`. Owned by a concurrent thread.
- 🟢 **Recently shipped this stream**: juniper-ml v0.6.0 release, 7 README compat-matrix PRs across the ecosystem, juniper-ml `Update Lockfiles` workflow fix (compound SHA + allowlist bug), juniper-data + juniper-canopy `Scheduled Tests` install fixes, juniper-cascor-worker `requirements-cpu.lock` regen.
- ⏸️ **6 trigger-conditioned items deferred** (no urgent action; documented for future thread).

---

## Active Issues (Need Decision / Action)

### 1. fastapi 0.136.3 / MAL-2026-4750 — Security Scans red on 3 repos

**Affected**: juniper-data, juniper-canopy, juniper-cascor (all running `pip-audit --strict` in CI).

**Status**: `pip-audit` flags fastapi 0.136.3 as malicious per OSV advisory MAL-2026-4750. The advisory claims 0.136.3 added an undocumented `fastar>=0.9.0` dep to `[standard]`.

**Verified false positive**:
- Direct PyPI metadata check: `fastar>=0.9.0; extra == "standard"` is **already present in fastapi 0.136.0 and 0.136.1** (curl `pypi.org/pypi/fastapi/{0.136.0,0.136.1,0.136.3}/json`). Not new in 0.136.3.
- `fastar` is a legitimate Rust-tar wrapper: <https://github.com/DoctorJohn/fastar>, added to fastapi via [tiangolo/fastapi PR #15419](https://github.com/fastapi/fastapi/pull/15419) ~1 month ago.
- Snyk's fastapi page shows **0 vulnerabilities** for 0.136.3: <https://security.snyk.io/package/pip/fastapi>.
- No tech-journalism coverage across BleepingComputer, The Hacker News, The Register, SecurityWeek, Dark Reading, SC Media.
- No GitHub Security Advisory at fastapi/fastapi/security/advisories. No maintainer acknowledgment in tiangolo/fastapi.
- MAL-2026-4750 absent from CIRCL vulnerability index.

**Likely cause**: Amazon Inspector heuristic diffed pyproject.toml/PKG-INFO between 0.136.1 → 0.136.3 and flagged `fastar` as newly-added without realizing it was already there. OSV ingested; downstream pip-audit consumers cascaded.

**Two PRs already closed** (this work stream):
- [juniper-data#152](https://github.com/pcalnon/juniper-data/pull/152) — closed with full counter-evidence in the close comment.
- [juniper-canopy#324](https://github.com/pcalnon/juniper-canopy/pull/324) — closed similarly.

**Options for the red CI** (no code change taken in this session; deferred for explicit decision):

| Option | Cost | Honesty |
|---|---|---|
| Wait for OSV retract or PyPI yank | CI stays red indefinitely | Highest |
| `pip-audit --ignore-vuln MAL-2026-4750` in CI yaml of all 3 affected repos, with a comment citing this doc | 1 small PR per repo; CI green immediately | High (documents the verification) |
| File an upstream challenge at github.com/pypa/advisory-database | ~30 min effort; resolution timeline TBD | Highest (helps the wider ecosystem) |
| Pyproject pin `fastapi>=0.100.0,!=0.136.3` | 1 small PR per repo | Low (propagates false framing) |

**Recommendation**: file an upstream challenge AND add the `--ignore-vuln` workaround in parallel. The challenge solves the ecosystem-wide problem; the ignore unblocks our CI without lying about a real malware version.

**Memory**: see [[verify-security-advisories-multi-source]] for the verification protocol that caught this.

---

### 2. juniper-cascor pre-commit failing on baseline-newline

**Affected**: juniper-cascor `main`. Pre-commit failing on all 3 Python versions.

**Symptom**: `end-of-file-fixer` hook reports `src/tests/performance/baselines/baseline_20260525.json` lacks a trailing newline. CI fails because pre-commit returns exit 1 when it would modify files.

**Pattern**: The performance test suite auto-generates dated baseline files at `src/tests/performance/baselines/baseline_YYYYMMDD.json`. The generator writes without a trailing newline. 19+ committed historical baseline files. The same class hit `baseline_20260522.json` earlier this week (then was un-staged, see this session's history).

**Root fix** (the right one): modify the perf-test generator script to write a trailing newline.

**Stopgap fixes** (any one works):
- Add `src/tests/performance/baselines/*.json` to `.pre-commit-config.yaml` `exclude:` pattern for `end-of-file-fixer`.
- Manually re-write `baseline_20260525.json` with a trailing newline (will re-occur next perf run).
- Switch the hook from `end-of-file-fixer` to a non-failing variant for that path.

**Coordination**: a concurrent thread (per user) owns juniper-cascor. Not touching from this thread.

---

### 3. juniper-cascor fastapi exposure (3 lockfiles + pyproject)

**Affected**: juniper-cascor.

**Files containing `fastapi==0.136.3`**:
- `requirements.lock` (the GPU lock — primary)
- `conf/requirements-pip.txt`
- `conf/requirements_ci.txt`

**Files admitting 0.136.3 via `>=`**: `pyproject.toml` `dependencies` (line 83: `"fastapi>=0.100.0"`).

**Status**: same OSV false positive as juniper-data + juniper-canopy. Pyproject pin is **NOT** warranted per the verified false-positive analysis (Active Issue #1 above).

**However**, cascor is the most-exposed repo because the lockfile already explicitly pins 0.136.3. A `pip install -r requirements.lock` would install the flagged version. **The flagged version is still functionally fine** (the trojan claim is false), but the CI-flagging will persist.

**Coordination**: concurrent thread owns cascor. Surface the false-positive analysis to that thread before they apply a defensive pin.

---

## Deferred Items (Trigger-Conditioned)

### From this work stream

| Item | Trigger to action |
|---|---|
| File upstream challenge at github.com/pypa/advisory-database for MAL-2026-4750 | When user has 30 min |
| Write `notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.6.0_2026-05-23.md` | Optional continuity with v0.5.0 walkthrough; skippable |
| `peter-evans/create-pull-request@v7.0.11` deprecation: Node.js 20 → Node.js 24 forced by GitHub on 2026-06-02 | Re-pin to v8.x when published, OR set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` (same pattern as gitleaks override) |
| Fix juniper-cascor perf-test generator to write trailing newlines | Owned by concurrent cascor thread |
| Investigate `juniper-canopy/conf/layouts/metrics_layouts.json` modification on main checkout | Concurrent-session leftover; benign for now |

### From memory (carried forward, not this stream)

| Item | Memory | Trigger |
|---|---|---|
| CFG-06 `AUTH_TOKEN_FILE` compose | [[cfg-06-shipped-2026-05-23]] | Future Helm rollout |
| CFG-06 Helm chart bump | [[cfg-06-shipped-2026-05-23]] | Same |
| `juniper-doc-tools` 0.1.1 patch + §5 drift-detection guard rails | [[juniper-doc-tools-pypi-plan]] | Bug or new requirement |
| gitleaks Node24 override removal (7 repos) | [[gitleaks-node24-override-followup]] | Upstream releases v2.3.10+ on Node 24 |
| `META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md` JR-ML-* ID assignment | (none) | Next snapshot refresh pass |
| Async-route audit centralised deny-list | [[async-route-audit-complete]] | Optional, no urgency |

---

## Recent Activity Log (this work stream's shipped PRs)

In rough chronological order.

| Date | Repo | PR | Description |
|---|---|---|---|
| 2026-05-23 | juniper-cascor-worker | [#89](https://github.com/pcalnon/juniper-cascor-worker/pull/89) | `fix(lockfile): regen requirements-cpu.lock to include juniper-config-tools==0.1.0` — closes the CFG-06 fallout the v0.4.0 release prep left in the CPU sibling lock |
| 2026-05-23 | juniper-data | [#142](https://github.com/pcalnon/juniper-data/pull/142) | README compat matrix sync (cascor 0.4.x → 0.5.x, canopy 0.4.x → 0.5.x, cascor-worker `>=0.3.0` → `>=0.4.0`) |
| 2026-05-23 | juniper-cascor | [#301](https://github.com/pcalnon/juniper-cascor/pull/301) | Same README sync |
| 2026-05-23 | juniper-canopy | [#316](https://github.com/pcalnon/juniper-canopy/pull/316) | Same README sync |
| 2026-05-23 | juniper-cascor-client | [#64](https://github.com/pcalnon/juniper-cascor-client/pull/64) | Same |
| 2026-05-23 | juniper-cascor-worker | [#90](https://github.com/pcalnon/juniper-cascor-worker/pull/90) | Same |
| 2026-05-23 | juniper-data-client | [#78](https://github.com/pcalnon/juniper-data-client/pull/78) | Same |
| 2026-05-23 | juniper-deploy | [#82](https://github.com/pcalnon/juniper-deploy/pull/82) | Same |
| 2026-05-23 | juniper-ml | [#322](https://github.com/pcalnon/juniper-ml/pull/322) | `release: juniper-ml v0.6.0 — extras floor-bump` (cascor/canopy 0.4.x → 0.5.x, cascor-worker/client 0.3.0 → 0.4.0, data-client 0.4.0 → 0.4.1). Tag `v0.6.0` published to PyPI. |
| 2026-05-24 | juniper-ml | [#324](https://github.com/pcalnon/juniper-ml/pull/324) | `fix(ci): correct bad SHA on peter-evans/create-pull-request in lockfile-update`. Hallucinated SHA `271a8d0…` had caused 3 weeks of `startup_failure` on the Monday cron. Fix only partial — see also allowlist fix below. |
| 2026-05-24 | juniper-data | [#143](https://github.com/pcalnon/juniper-data/pull/143) | `fix(ci): include [observability] in scheduled-tests install`. Install line `.[api,test]` always succeeded so the `\|\|` fallback never fired; `prometheus_client` (in `[observability]`) was never installed; integration tests failed on TestClient calls. Switched to `.[all]` matching main ci.yml. |
| 2026-05-24 | juniper-canopy | [#319](https://github.com/pcalnon/juniper-canopy/pull/319) | `fix(ci): install pytest + torch in scheduled-tests via requirements_ci.txt`. canopy has no `[test]` extra; pip warned + exited 0 on unknown extra; pytest never installed. Switched to torch + requirements_ci.txt + .e matching main ci.yml. |
| 2026-05-24 | juniper-ml allowlist | (not a PR — settings change) | Added `peter-evans/create-pull-request@*` to juniper-ml's selected-actions allowlist via `PUT /repos/pcalnon/juniper-ml/actions/permissions/selected-actions`. The SHA fix in PR #324 was necessary-but-not-sufficient — workflow still `startup_failure`'d on the allowlist gap until the settings change. |
| 2026-05-24 | juniper-ml | [#325](https://github.com/pcalnon/juniper-ml/pull/325) | Auto-opened by the now-fixed `Update Lockfiles` workflow: `chore(deps): refresh CI lockfiles` (247 lines added including new `conf/conda_environment_ci.yaml`). |
| 2026-05-26 | juniper-data | [#152](https://github.com/pcalnon/juniper-data/pull/152) | **CLOSED, not merged**: `security(deps): pin fastapi away from 0.136.3 (MAL-2026-4750)` — verified false positive. |
| 2026-05-26 | juniper-canopy | [#324](https://github.com/pcalnon/juniper-canopy/pull/324) | **CLOSED, not merged**: same as above. |

Concurrent activity (other threads) also landed during this stream — Dependabot bumps, juniper-cascor#302 (CFG-02 sentry-sdk extras move), juniper-cascor#309 (fix(tests) Settings isolation), various dep group bumps. Not enumerated here.

---

## Cross-Repo State (as of 2026-05-26 EOD)

| Repo | pyproject | tag | PyPI | Active issues |
|---|---|---|---|---|
| juniper-ml | 0.6.0 | v0.6.0 | 0.6.0 | none from this stream |
| juniper-data | 0.6.0 | v0.6.0 | 0.6.0 | Security Scans red (false-positive MAL-2026-4750) |
| juniper-cascor | 0.5.0 | v0.5.0 | 0.5.0 | Security Scans red (false positive), pre-commit red (baseline newline) |
| juniper-canopy | 0.5.0 | v0.5.0 | 0.5.0 | Security Scans red (false-positive MAL-2026-4750) |
| juniper-cascor-worker | 0.4.0 | v0.4.0 | 0.4.0 | none from this stream |
| juniper-cascor-client | 0.4.0 | v0.4.0 | 0.4.0 | none from this stream |
| juniper-data-client | 0.4.1 | v0.4.1 | 0.4.1 | none from this stream |
| juniper-deploy | n/a | v0.2.1 | (no PyPI) | none from this stream |

All main checkouts current with `origin/main`. No leftover working-branch state from this stream.

---

## Memories Saved / Updated This Stream

| Memory | Why |
|---|---|
| [[juniper-ml-extras-shipped]] | Renamed from `juniper-ml-0-5-0-extras-shipped`; refreshed to current 0.6.0 floor |
| [[verify-new-ci-workflows-before-first-cron]] | Captured the "3 workflows broken-since-inception" pattern (juniper-ml#324 SHA + allowlist, juniper-data#143 broken extras chain, juniper-canopy#319 nonexistent extra). Updated to include the selected-actions-allowlist verification step. |
| [[verify-security-advisories-multi-source]] | Captured the verification protocol that caught the MAL-2026-4750 false positive (direct PyPI metadata + 3 source classes). |

---

## Suggested Resume Plan (When Picking This Up Later)

1. **Decide on MAL-2026-4750 handling** (Active Issue #1). Recommendation: file upstream challenge + add `pip-audit --ignore-vuln MAL-2026-4750` workaround in 3 repos. ~1 hour total.
2. **Coordinate cascor false-positive analysis with the concurrent thread** before they apply a defensive pin.
3. **Optionally write the v0.6.0 release walkthrough** for continuity with the v0.5.0 doc. ~20 min.
4. **Watch for fastapi maintainer / PyPA response** to MAL-2026-4750. If OSV retracts or PyPI yanks, the workaround can be removed.
5. **Watch for peter-evans/create-pull-request@v8.x** (Node 24 compatible). Currently no fix needed; June 2026 deprecation forces action.

---

## Cross-References

- Session transcript: in Claude Code session `parsed-foraging-lollipop` (juniper-ml worktree at `.claude/worktrees/parsed-foraging-lollipop/`).
- Worktree was preserved at session end; no stale artifacts.
- Related session-handoff procedures: `notes/THREAD_HANDOFF_PROCEDURE.md`.
- Worktree cleanup procedure: `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`.
