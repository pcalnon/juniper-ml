# Thread Handoff — Juniper-Recurrence Full-Audit Remediation (follow-ups: DOC-06 + gating)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Created**: 2026-06-25
**Purpose**: Close out the `juniper-recurrence` **full-audit remediation** backlog. The audit
([`notes/JUNIPER_2026-06-24_JUNIPER-RECURRENCE_FULL-AUDIT.md`](../../notes/JUNIPER_2026-06-24_JUNIPER-RECURRENCE_FULL-AUDIT.md),
shipped as juniper-ml#546) is the **source of truth** for every finding ID. As of this handoff **every
High-sev (H1, H2) and every Medium except DOC-06 is addressed.** What remains is one docs-only PR
(**DOC-06**), plus two server-side gating items that are **Paul's** to action.

---

## 0. FIRST — verify live state (repos advance same-day; multiple sessions share this backlog)

1. **Read the audit** — §4 "Medium — remaining", §6, §7 (DOC-06 = line 85/193; OBS-04 = line 79/184):

   ```bash
   sed -n '178,196p' /home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_2026-06-24_JUNIPER-RECURRENCE_FULL-AUDIT.md
   ```

2. **Confirm this session's PRs all merged** (#66–#70 + the dependabot fan-out #71–#74):

   ```bash
   for pr in 66 67 68 69 70 71 72 73 74; do gh pr view $pr -R pcalnon/juniper-recurrence \
     --json number,state --jq '"#\(.number) \(.state)"'; done
   ```

3. **Confirm recurrence `origin/main` head + worktrees swept** (expect `95a4fc6`; only `main` listed):

   ```bash
   git -C /home/pcalnon/Development/python/Juniper/juniper-recurrence fetch origin --quiet
   git -C /home/pcalnon/Development/python/Juniper/juniper-recurrence rev-parse --short origin/main
   git -C /home/pcalnon/Development/python/Juniper/juniper-recurrence worktree list
   ```

4. **Enumerate the DOC-06 gap** (tags with no archived release-notes file — expect exactly 5):

   ```bash
   REC=/home/pcalnon/Development/python/Juniper/juniper-recurrence
   comm -23 <(git -C "$REC" tag --list 'juniper-recurrence*' | sort) \
            <(ls "$REC"/notes/releases/ | sed -E 's/^RELEASE_NOTES_(.*)\.md$/\1/' | sort)
   ```

5. **Collision-check before the DOC-06 PR:** `gh pr list -R pcalnon/juniper-recurrence --state open`.

---

## 1. Already done — carry-forward (merged to recurrence `main` @ `95a4fc6`)

The prior handoff's **task 3 (Medium cluster)** + **task 4 (H2)** are COMPLETE. Paul chose **4 focused
PRs** over one combined Medium PR; all **MERGED 2026-06-25**:

- **#66 (3a)** — **TEST-02** warnings-as-errors into model+client `pyproject` (both already clean under
  `pytest -W error`; ignore list is empty `["error"]`). **CI-05** `.github/dependabot.yml` (monorepo: 3
  per-package pip dirs + github-actions). Dependabot fired immediately → **#71–#74** auto-merged same day.
- **#67 (3b)** — **OBS-03** provenance. New `juniper-recurrence/juniper_recurrence/provenance.py` (mirrors
  juniper-data's; reads `JUNIPER_RECURRENCE_GIT_SHA`/`_BUILD_DATE`), threaded into `set_build_info(...)`.
  Key fix: the Dockerfile had `ARG GIT_SHA/BUILD_DATE` for OCI labels but **no runtime `ENV`** — added the
  `ENV` stamping (else the kwargs are perpetually `None`). App coverage 97.98%.
- **#68 (3c)** — **CI-06** version-drift lint. `scripts/check_version_drift.py` + a `version-drift` **local
  pre-commit hook** (enforced by the existing `CI — pre-commit` gate; **no new workflow**). In-repo
  invariants are hard; the git-tag check is **directional + graceful** (tag-ahead=FAIL, tag-behind=OK,
  no-tags=skip) so it never flakes on shallow CI.
- **#69 (3d)** — **CI-04** bench push-trigger parity (`[main, develop, feature/**, feat/**, fix/**,
  chore/**]`) + **TEST-03** `bench/test_run_dataset_contract.py` (run_dataset→evaluate_bands contract;
  bounded ~0.5 s via single-point `_D_GRID` + torch-off).
- **#70 (4 / H2 / TEST-01)** — torch-MLP readout coverage gate. New
  `juniper-recurrence-model/.coveragerc.torch`; `test-torch` now runs `--cov=juniper_recurrence_model
  --cov-config=.coveragerc.torch --cov-fail-under=90` (measured 95.43%). **Use package-form `--cov`** —
  the dotted `--cov=…_readout_mlp` form trips a numpy-2.x "cannot load module more than once" guard.

Earlier in the same backlog: **H1** (#61/#64), **M1** (#63), **M2/M3** (#62), and controlling-thread
tasks 1–2 (juniper-ml #560/#561, recurrence #65) were already merged (see the prior handoff).

## 2. Remaining work

1. **DOC-06 (this session's work)** — backfill the **5** missing
   `juniper-recurrence/notes/releases/` files (§0 step 4 lists them): app `v0.1.0`, app `v0.1.1`, model
   `v0.1.0`, model `v0.1.2`, **client `v0.1.0`**. Author from
   [`juniper-ml/notes/templates/TEMPLATE_RELEASE_NOTES.md`](../../notes/templates/TEMPLATE_RELEASE_NOTES.md)
   (the template lives in **juniper-ml**, not recurrence). Four of the five have a crib source in
   `juniper-ml/notes/releases/` (`…_v0.1.0`, `…_v0.1.1`, model `…_v0.1.0/_v0.1.2`); **client v0.1.0 has
   none — author fresh** from the tag's CHANGELOG/diff. **Naming nuance:** match the recurrence repo's own
   existing `RELEASE_NOTES_<pkg>-v<ver>.md` (**hyphen**-v) pattern, not juniper-ml's underscore-v.
   Docs-only PR.
2. **OBS-04 (do NOT action)** — domain train/predict counters + last-metric gauges via `register_or_reuse`.
   The audit marks it **design-deferred, a fast-follow, not a defect** (line 79/184). Mention only.

**In Paul's court (server-side — document, do NOT attempt):**

- **Promote `test-torch` → required-checks** = the **gating half of H2**. Steps are in recurrence **#70**'s
  body. The coverage half (#70) is shipped; this is a branch-protection change only Paul makes.
- **CI-07** — a required-checks aggregator job for the bench lane. Deferred as a branch-protection decision.

Standing guardrail: **PyPI deploy gates + branch-protection are Paul's; never self-approve.**

## 3. Conventions & guardrails

- **Monorepo layout:** `juniper-recurrence/` (app), `juniper-recurrence-model/`,
  `juniper-recurrence-client/`, and **`bench/` at repo root**. Validate with `pre-commit run --all-files`.
  **No `agents-md-touch-up.yml`** in recurrence → the skip-ci squash gotcha does not apply.
- **CI triggers:** PRs to main get `pull_request` CI; package CIs push-trigger on
  `feature/feat/fix/chore` branches; **bench now too** (CI-04, #69). The `version-drift` pre-commit hook
  (#68) runs inside the `CI — pre-commit` gate on every PR.
- **Worktrees** centralized at `/home/pcalnon/Development/python/Juniper/worktrees/`
  (`<repo>--<safe-branch>--<YYYYMMDD-HHMM>--<short8hash>`). Clean only after confirmed **MERGED**, then
  `git worktree prune`.
- **Commit trailers:** `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` + the `Claude-Session:`
  link. PR bodies end with the `🤖 Generated with [Claude Code]` footer. **Paul merges** (admin-bypass;
  `BLOCKED`-with-green is the normal state).
- **Local-test env gotcha:** no on-host env runs the recurrence suites cleanly — use a throwaway venv
  (`pip install -e <pkg>[test,...]`). The torch-coverage numpy-2.x gotcha is documented in §1 (#70).

## 4. Git / worktree state at handoff

- recurrence `origin/main` @ **`95a4fc6`** (short8 `95a4fc67`), past #66–#70 and dependabot #71–#74. The
  local checkout may lag (`03c2be9`) — `git fetch` / work off `origin/main`.
- **0 open recurrence PRs** from this session; all **5** worktrees (#66–#70) **removed + pruned** (verified:
  `worktree list` shows only `main`).
- This handoff was written from the juniper-ml **`fizzy-popping-hearth`** session worktree.

## 5. Recommended first move

Complete §0, then start **DOC-06**: create a worktree off **fresh recurrence `origin/main`** on a
`docs/**` (or `chore/**`) branch, draft the 5 missing release-notes from the juniper-ml template (cribbing
the 4 that have juniper-ml sources, authoring client v0.1.0 fresh), open one docs-only PR, and hand the
merge to Paul. Note **OBS-04** and the two **Paul-court** gating items (`test-torch` required-check, CI-07)
as explicitly **not this session's work**.

---

*Generated by Claude Code (Opus 4.8) as a mandatory thread handoff at the Medium-cluster/H2 → DOC-06 phase
boundary. Begin by completing §0.*
