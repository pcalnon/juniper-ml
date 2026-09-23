<!-- markdownlint-disable -->
# Round 1, lane A3

**Entry point:** repository contents at remote `main`, with its own census built first.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`, `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py` and `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py` and the PRs named in the brief.

**Ran:** 2026-09-22T19:55:12Z to 2026-09-22T20:08:53Z, read-only. Agent `agent-a7ad2af2b2e3ac827`.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are Lane A3 (measurement re-creation) in an independent-agent consensus review. Your entry point is the REPOSITORY CONTENTS at each repo's remote `main`, measured with YOUR OWN instrument, before you look at the author's instrument. "UNTRACEABLE" is an allowed answer; default to REFUTED when you cannot re-derive.

READ-ONLY RULES (hard): do not edit/create/delete files in any repo or worktree (your own scratch files are fine); do not commit, push, comment, merge or approve anything. Worktree-isolated harness: do NOT run `git` against any repo except reading `git diff`/`git show` in the juniper-ml worktree below; for the other repos use `gh api` (e.g. `gh api repos/pcalnon/<repo>/tarball/main > file.tgz`, or the contents/trees API) and python. The harness refuses shell loops over variables that touch gh/git, and refuses very complex one-liners — write a small python script into your scratch dir /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/a3/ (create it) and run it with python3.

REPOS (owner pcalnon): juniper-ml, juniper-canopy, juniper-cascor, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client, juniper-deploy, juniper-recurrence.

STEP 1 — your own census, BEFORE reading the author's script: at each repo's remote main (record the SHA), find every `juniper-ci-tools` version specifier. Report (i) the number of LIVE pins — non-comment lines in `.github/workflows/*.yml|*.yaml` — per repo and in total, and the distinct ranges among them (the claim under test: 54 live pins, all `>=0.9.0,<0.10.0`; per repo ml 13, canopy 6, cascor 6, cascor-client 5, worker 5, data 5, data-client 5, deploy 3, recurrence 6); note a pin can be written as `pip install "..."`, as a workflow-level `env:` value like `CI_TOOLS_PIN:`, or in a requirements line; (ii) every current-state DOCUMENT (AGENTS.md, README.md, docs/**, scripts, non-ad-hoc util/**) that states an install RANGE with an upper bound which differs from what that repo's CI installs. The author claims exactly these were stale before their fixes: juniper-ml `docs/REFERENCE.md` (dependency-docs job text `>=0.1.0,<0.2.0`, the lockfile-refresh "Tooling" row `>=0.1.0,<0.8.0`, the flood-remediation install hint `>=0.8.0,<0.10.0`), juniper-ml `util/fleet_triage/predict_merge.py` (three printed/docstring install hints `>=0.8.0,<0.9.0`), and juniper-canopy `AGENTS.md:517` (`>=0.5.1,<0.6.0`). Find anything the author MISSED (other repos, other phrasing such as `juniper-ci-tools 0.6.x` or `<0.7`), and anything the author flagged that is NOT actually stale.

STEP 2 — the author's instrument: read and run `python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py` from the juniper-ml worktree /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl. Compare with your Step 1. Then attack its ADEQUACY: could it report "(none)" while a stale live pin exists? Consider its regex (e.g. spaces around operators, `~=`, single vs double quotes, a pin split across YAML lines, `.yaml` vs `.yml`, a pin inside a composite action under `.github/actions/`, reusable workflows, a requirements file referenced by a workflow), its classification (anything under a `tests/` path is treated as FIXTURE and never judged; floor-only `>=X` is treated as REQUIREMENT and never judged; `KNOWN_EXAMPLES`), and its exit codes. Demonstrate any false negative concretely if you can (e.g. run its `SPEC_RE`/`classify` on a crafted line).

STEP 3 — the fixes: in the worktree, `git diff -- docs/REFERENCE.md util/fleet_triage/predict_merge.py`, and `gh pr diff 655 --repo pcalnon/juniper-canopy`. For each changed line, confirm the new range equals what the specific CI job it describes actually installs (find that job in the workflow file at main), and that nothing else in the line changed.

OUTPUT (final message only is returned): numbered findings — quoted claim, verdict (CONFIRMED / REFUTED / PARTIAL / UNTRACEABLE), severity (CRITICAL/MAJOR/MINOR/NONE), evidence. Include your own per-repo live-pin counts table. Then an overall verdict (PASS / PASS WITH FINDINGS / FAIL). Terse, no preamble.

## Final report

**Lane A3: ci-tools pin census, re-measured**

Measured at remote `main`: ml `e3186919` (main has since moved to `099a5645` via #2011, which touched only two `notes/` files, so nothing here changes), canopy `9bffaba1`, cascor `05c13d55`, cascor-client `0366f4f1`, worker `48a523e6`, data `6c81cc4c`, data-client `f7494ff1`, deploy `13ee87aa`, recurrence `749e7a35`.

**My live-pin counts** (non-comment lines in `.github/workflows/*.y*ml`; my own permissive regex, run before I read the author's script)

| repo | live pins | ranges |
|---|---|---|
| juniper-ml | 13 | `>=0.9.0,<0.10.0` |
| juniper-canopy | 6 (4 in `ci.yml` + 2 workflow-level `CI_TOOLS_PIN:`) | same |
| juniper-cascor | 6 | same |
| juniper-cascor-client | 5 | same |
| juniper-cascor-worker | 5 | same |
| juniper-data | 5 | same |
| juniper-data-client | 5 | same |
| juniper-deploy | 3 | same |
| juniper-recurrence | 6 | same |
| **Total** | **54** | **1 distinct** |

Excluded as not literal pins: ml `publish-ci-tools.yml:152` (`==${version}`), ml `ci-ci-tools.yml:116` (installs a locally built wheel), and canopy's two `pip install "${CI_TOOLS_PIN}"` lines. Those two lines read the env pins already counted. There are no composite actions, no reusable workflows, no `.yaml` workflow files, and no requirements file referenced by a workflow that contains ci-tools.

**Findings**

1. "54 live pins, all `>=0.9.0,<0.10.0`, per repo 13/6/6/5/5/5/5/3/6" — **CONFIRMED**, NONE. My instrument and the author's give identical counts.

2. The six flagged lines with a stale ceiling (`REFERENCE.md:3754` `<0.2.0`, `:6392` `<0.8.0`, `predict_merge.py:57/180/234` `<0.9.0`, canopy `AGENTS.md:517` `<0.6.0`) — **CONFIRMED**, NONE.

3. `REFERENCE.md:7072` `>=0.8.0,<0.10.0` flagged as stale — **PARTIAL**, MINOR. Its ceiling already matches CI; only the floor differs. By the upper-bound test it is not stale. The script flagged it only because it demands an exact match. The edit is harmless.

4. "Exactly these were stale" — **REFUTED**, MAJOR. Two current-state docs were missed:
   - **juniper-cascor-client `docs/REFERENCE.md:715`**: "Runs the shared `juniper-ci-tools` (`>=0.8.0,<0.9.0`) sequence-safety screens". That repo's `sequence-safety.yml` installs `>=0.9.0,<0.10.0`.
   - **juniper-ml `docs/REFERENCE.md:3023`** (the same file the author edited): "`main-verify.yml` … enforces the two new `>=0.8.0,<0.9.0` screen pins". The two pins in main-verify (jobs `symbol-screen` and `battery`) are `>=0.9.0,<0.10.0`. It is still stale in the worktree after the fix.

5. The workflow-comment report ("reported, not failed -- read each") — **REFUTED**, MINOR. It found none of the 10 stale-ceiling header comments:
   - canopy `sequence-safety.yml:27`
   - cascor `main-verify.yml:64`, `sequence-safety.yml:60`
   - cascor-client `main-verify.yml:28`, `sequence-safety.yml:28`
   - data-client `main-verify.yml:28`, `sequence-safety.yml:28`
   - deploy `main-verify.yml:69`, `sequence-safety.yml:72` (all `>=0.8.0,<0.9.0`)
   - ml `ci.yml:1879` ("Pinned <0.2.0", in the dependency-docs job)

   All 20 comments it does list are floor-only historical notes. deploy `ci.yml:242-243` is a dated history note, so NONE there.

6. Other wording (MINOR, outside the upper-bound criterion): ml `docs/QUICK_START.md:92` shows "Expected output (with `[all]`)" as `juniper-ci-tools 0.4.x`. The whole block is stale (it also shows `juniper-ml 0.6.0`; the package is at 0.9.0). The floor-only "(>=0.8.0)" install statements at ml `REFERENCE.md:2010/3253/3259/3758/4018/4193` and in `predict_merge.py` are still true, so NONE.

7. Can the script report "(none)" or exit 0 while stale entries remain? **Yes**, MAJOR for docs. I ran the author's `main()` unchanged, offline, on the saved tarballs with the three fixed files swapped in. It exits **0** and prints "current-state DOC … (none)", while findings 4 and 5 remain. The cause is that `SPEC_RE` requires the specifier to follow `juniper-ci-tools` directly.

8. The same blind spots for live pins — MINOR, latent. None of these shapes exists at any main today, so the 54/54 result stands. Crafted lines run through its `SPEC_RE` and `classify`:
   - Never seen at all: `juniper_ci_tools>=…`, `Juniper-CI-Tools>=…`, the PEP 508 form `juniper-ci-tools (>=0.8.0,<0.9.0)`, `juniper-ci-tools[x]>=…`, an env var that holds only the range, and an unpinned `pip install juniper-ci-tools`.
   - Never scanned: `.lock`, `.in`, Makefile and Dockerfile. The `.lock` branch of `LOCK_RE` can never fire, because `.lock` is missing from `TEXT_SUFFIXES`. The 8 `requirements*.lock`, 9 Makefiles and 6 Dockerfiles that exist hold no ci-tools today.
   - Counted but never judged: anything under `tests/` (FIXTURE), floor-only doc lines (REQUIREMENT), a composite action with a floor-only pin, and a `docs/release_notes/…` path (the `notes/` substring makes it HISTORICAL).
   - `KNOWN_EXAMPLES` exempts the whole of `propose.py`: a planted `<0.6.0` install hint there stays silent.
   - Two over-flags, which err on the safe side: `- # pip install …` and a trailing `# juniper-ci-tools>=…` are both treated as LIVE.
   - Exit code: only a failing `gh` call returns 2. A bad tarball, bad JSON or missing `packaging` crashes with exit 1, which looks the same as "stale found".
   - The drift guard `tests/test_ci_tools_drift.py:56` `_PIN_PATTERN` is narrower still, so CI has the same blind spots.

9. `KNOWN_EXAMPLES` entry for `propose.py:747` — NONE/MINOR. Exempting it is defensible, since it is not an install hint. But its premise is out of date: ml `AGENTS.md` no longer holds any `>=0.1.0,<0.2.0` CI-pin description. That text moved to `REFERENCE.md:3754`, which this change set rewrites.

10. The ml worktree diff — **CONFIRMED**, NONE. Six lines changed, and rebuilding each old line with the new range reproduces the new line exactly. Each new range matches the job it describes:
    - `:3754` → `ci.yml` job `dependency-docs`
    - `:6392` → `lockfile-update.yml` job `update` (which also runs `juniper-generate-dep-docs`)
    - `:7072` and `predict_merge.py` → `ci.yml` job `sequence-safety` and `main-verify.yml` job `symbol-screen`

11. canopy#655 (OPEN, MERGEABLE, head `35e78350`) — **CONFIRMED**, NONE. Line 517 changes only the range, and the new range equals canopy `ci.yml` job `unit-tests`, step "Preflight - Environment Floor-Drift Check". The only other change in the file is the `**Last Updated**` header date (2026-09-17 → 2026-09-22).

**Overall: PASS WITH FINDINGS.** The live-pin census and all seven edits hold. The claim that exactly these docs were stale fails. Before that claim is repeated, cascor-client `docs/REFERENCE.md:715` and ml `docs/REFERENCE.md:3023` need fixing. Separately, the census script needs to recognise a range that does not sit right after the package name before its exit 0 can be taken to mean "clean".

My scripts and saved tarballs are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/a3/`. The ones that back these findings are `census.py`, `window.py`, `orphan_ranges.py`, `attack.py`, `postfix_sim.py` and `job_map.py`.
