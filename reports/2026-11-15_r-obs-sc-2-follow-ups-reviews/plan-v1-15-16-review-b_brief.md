You are an independent ADVERSARIAL REVIEWER of an uncommitted record revision of a long planning document. Your angle is not line-by-line facts: a separate fact-checker does those. Yours is whether the revision leaves the document coherent, complete and honest. Do not fix anything. Your final message is your report: sub-agents here cannot write report files.

## What is under review
- Repository: juniper-ml, worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humble-humming-flask`. It is read-only to you; run your commands from there.
- The edit: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.15.15 to v1.15.16 (about 2,300 lines, 365 KB). It is uncommitted, so `git diff -- notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` shows it. The writer is `util/ad-hoc/2026-11-15_consolidated_plan_v1_15_16_r_obs_sc_2_followups.py`.
- The revision records the "R-OBS-SC-2 follow-ups" from 2026-11-09 to 2026-11-15:
  - Overtoad rulings: round 1 of 2026-11-09, the seven of 2026-11-13, and three of 2026-11-14;
  - five PRs, plus juniper-data#537;
  - juniper-ml 0.11.5;
  - register row APD-ECO-016;
  - juniper-cascor 0.14.0 and juniper-canopy 0.10.0, cut but waiting at the Overtoad's `pypi` gates;
  - the 0.4.3 design start prompt;
  - 13 findings;
  - what stays open.
- What the revision rests on: the handoffs `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md`, `…HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-five-prs-validated-opening-next.md`, `…HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md` (read its "Update, 2026-11-14" first) and `…HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md`.

## Your job
1. **Stale passages left behind.** For each topic below, grep the WHOLE plan and read every hit in context. Report every passage that is now false, or that contradicts the new text, and that the revision did not change:
   R-OBS-SC-2, R-OBS-SC-3, APD-ECO-016, APD-SVCCORE-004, telemetry, RateLimiter, `Retry-After`, 0.11.5, `[tools]`, D-03, P3-17, O13, D-4, D-5, "no register row", "no consumer has cut", "image", "restart", "fix-forward", cascor 0.14.0, canopy 0.10.0.
   Version-history bullets (old Status entries) are history and may stay as written. Say when you rely on that.
2. **Dropped open items.** Confirm each of these is still visibly open somewhere a reader of §6 or §5 would find it. Each one the revision drops, or marks done without a source, is a finding:
   - A1's open limbs: the data-client and cascor F-S10 fixes, P6 OD-2, and canopy#685 call (a);
   - who may pull the juniper-canopy primary (O13);
   - whether a fix-forward is owed for juniper-cascor 0.12.0;
   - the trio's environment upgrade, an Overtoad action;
   - the stack restart, on the condition of ruling 6 of 2026-11-13;
   - the second edit of the parent `Juniper/AGENTS.md` once both releases are on PyPI, which needs the Overtoad's word first;
   - juniper-deploy's image pins, which come after the gates;
   - worktree housekeeping, which needs the Overtoad's word worktree by worktree.
3. **Overclaims and underclaims.** Look for:
   - anything said to be shipped, published, pinned, running or fixed that is only cut, waiting or merged;
   - rulings stretched beyond their text, e.g. ruling 6 (the restart condition) and ruling 7 (O13 extended to the juniper-ml primary only).
   Quote each ruling's text from `python3 util/ad-hoc/2026-11-09_r_obs_sc_2_Overtoad_answers.py 218ff61e --full`.
4. **The author's eight judgment calls.** Give a recommendation, with a reason, for each:
   1. a new §5 release ID, R-ML-TOOLS-2, for juniper-ml 0.11.5 (it also appears in §9, order item 6 and the Status bullet), or describe 0.11.5 without an ID;
   2. the 2026-11-13 rulings numbered 1-7, with round 1's written "round 1's ruling N";
   3. the "ruling 17" CHANGELOG lines cited at the release tags (cascor `:244` at `v0.14.0`, canopy `:156` at `v0.10.0`), not on `main`;
   4. a new step 6, "The consumer releases", in Wave 1's Security delivery;
   5. P3-17 kept in Appendix A's T1 and annotated as ruled, rather than moved to Done;
   6. the review archive tool `util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py`, and four more `util/ad-hoc/2026-11-15_*` tools, not yet in the "Changed by this plan" list (they will land in the same PR);
   7. the Validation record claims no review of this draft (two reviews are now running, yours among them);
   8. v1.15.15's Status bullet "no consumer has cut…" left as history, and the v2 draft (`notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md`) left unedited, its stale `:150`, `:153` and `:322` recorded in v1.
5. **New facts.** Should v1.15.16 record these, which came after the draft, and where?
   1. juniper-ml#2574 merged at 03:29:46Z as `7914ba9f`.
   2. Both published images were pulled by digest and run with no network. Each installs juniper-observability 0.4.2 and juniper-service-core 0.7.2 on Python 3.14.10 (`util/ad-hoc/2026-11-15_probe_published_images_cascor_0_14_0_canopy_0_10_0.py`). The image indexes are cascor `sha256:6b3e64bd…` and canopy `sha256:d9a966ff…`; each revision label is its Release commit.
   3. juniper-cascor's publish run has no shared build job, so its PyPI files differ from TestPyPI's by hash, though every member is identical (measured on 0.13.0; `util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py`). canopy shares one build, and its hashes match.
   4. juniper-deploy still pins `juniper-recurrence:0.8.0` while 0.8.1 is published, so its `scripts/verify_published_images.py --fail-on-stale` exits 1 on that pin.
   5. `Overtoad_answers.py` prints "answered None" for answers whose later copy has no timestamp.
6. **Outside-reader test.** Read the new §5 note "R-OBS-SC-2's follow-ups, 2026-11-09 to 2026-11-15" and the new Status bullet as someone who has not followed the arc. Name each sentence that cannot be understood without a handoff, and each term used before it is defined.

## Severity
- **BLOCKER**: false, or a ruling misstated.
- **MAJOR**: a stale passage left, an open item dropped, or an overclaim.
- **MINOR**: unclear, or a judgment call you would reverse.
- **NIT**: wording.

## Rules
- Read-only. Do not edit, stage or commit. Do not push, comment, merge or approve. Do not message any session.
- Scratch only under the worktree's `tmp/review-b/`. Never write under `/tmp`.
- Use `command grep`, because `grep` is ugrep and honours .gitignore.
- Use plain git commands from the worktree: an isolation guard refuses `git -C` and `$(git …)`.

## Final message
1. A one-paragraph verdict.
2. Numbered findings, most severe first. Each with its severity, the current plan line number, the quoted text, why it is wrong (with evidence), and the exact fix.
3. Your recommendations on judgment calls 1-8.
4. Your recommendations on new facts 1-5.
