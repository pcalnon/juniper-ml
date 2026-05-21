# Readme file Normalization

## Thread Handoff

Juniper README Normalization, §12 step 8 (final)

Continue the juniper-deploy README normalization (§12 step 8 of juniper-ml/notes/README_NORMALIZATION_PLAN_2026-05-19.md, governed by §10.8). This is the final PR in the README normalization sequence.

## Completed so far (all merged)

- juniper-ml #277 (§12 step 1) — plan + logo asset
- juniper-ml #280 (§12 step 2) — Research Philosophy canonical draft at notes/RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-19.md
- juniper-ml #282 (§12 step 3) — juniper-ml README (reference implementation)
- juniper-canopy #293 (§12 step 4)
- juniper-cascor #275, juniper-data #125, juniper-cascor-worker #70 (§12 step 5a/b/c)
- juniper-data-client #67, juniper-cascor-client #51 (§12 step 6a/b)
- juniper-ml #287 (observability), juniper-ml #288 (doc-tools) (§12 step 7a/b)

## Remaining work

1. Draft juniper-deploy/README.md per §10.8 (current is 447 lines — the largest editorial step in the plan).
2. Copy logo to images/Juniper_Logo_150px.png (no .gitignore block, no LFS).
3. Run juniper-check-doc-links audit; commit with Co-Authored-By trailer; push; open PR; wait for merge.

§10.8 specifics that differ from prior PRs

- No-PyPI Distribution variant (§6) — juniper-deploy is not published; cite the no-PyPI block and point at juniper-ml for client work.
- Active Research Components → "Stack Composition" (NOT "Design Notes" — that label was used by observability/doc-tools per §10.9/10.10). Add an inline reviewer-facing note citing §10.8.
- Docker Deployment is the section of record — preserve the 447-line content with editorial trimming for the new §4 order.
- Service Configuration consolidates the env-var surface across all orchestrated services (data + cascor + canopy).
- Quick Start trimmed per §8 — direct the reader at the existing Profiles table for detail rather than duplicating it.
- Preserve the secrets-onboarding warning callout at the top (it's a real safety contract).

## Key context

- Worktree: /home/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--docs--deploy-readme-normalize-2026-05-20--20260520-1112--fd879c21. Branch docs/deploy-readme-normalize-2026-05-20 already created off origin/main (HEAD fd879c21).
- Markdownlint v0.42.0 (permissive 512-char rule) — long Research Philosophy paragraphs commit without hard-wrapping.
- Logo source: /home/pcalnon/Development/python/Juniper/juniper-canopy/src/assets/Juniper_Logo_150px.png (43,955 B).
- Canonical Research Philosophy to inline verbatim: see juniper-ml/notes/RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-19.md §2. No third paragraph for deploy (per §3.3).
- User autonomy mode: "one PR at a time, push and open PR automatically; wait for explicit 'PR merged' signal before next step." Do not run worktree cleanup until told.
- PR description style: §4 canonical-section checklist table + §11 link-audit block + §10.8 deviation note + sequencing list + Test plan. Use HEREDOC with Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com> in both commit and PR body.

## Verification commands

```bash
git -C /home/pcalnon/Development/python/Juniper/juniper-deploy log --oneline origin/main -3
ls /home/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--docs--deploy-readme-normalize-2026-05-20--20260520-1112--fd879c21
cd /home/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--docs--deploy-readme-normalize-2026-05-20--20260520-1112--fd879c21 && git status --short && PYTHONPATH=/home/pcalnon/Development/python/Juniper/juniper-ml/juniper-doc-tools python -m juniper_doc_tools --exclude templates --exclude history --exclude legacy --cross-repo skip
```

## Git status at handoff

Branch docs/deploy-readme-normalize-2026-05-20 is created and tracks origin/main (HEAD fd879c2 Merge pull request #75 from pcalnon/chore/script-placement-sop-2026-05-19). Worktree is clean; no edits made yet. Logo not yet copied. README not yet drafted.

---
