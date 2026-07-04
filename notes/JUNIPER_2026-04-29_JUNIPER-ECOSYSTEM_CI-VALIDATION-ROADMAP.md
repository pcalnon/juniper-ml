# CI Pipeline Validation Roadmap

**Date**: 2026-04-29
**Author**: Paul Calnon (with Claude Opus 4.7)
**Companion to**: `notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-PIPELINE-ALIGNMENT-PLAN.md`
**Goal**: Now that the alignment plan is fully implemented (17 commits
across 8 repos, all on `main`), validate that every workflow runs
green, root-cause every failure that surfaces, ship the fixes, and
promote the soft-fail jobs to hard gates **per-repo** as each
repo's pipeline goes green.

---

## 0. Table of contents

- [1. Goals and non-goals](#1-goals-and-non-goals)
- [2. Inputs](#2-inputs)
- [3. Phase V0 — Inventory current run state](#3-phase-v0--inventory-current-run-state)
- [4. Phase V1 — Document issues](#4-phase-v1--document-issues)
- [5. Phase V2 — Root-cause + group fixes](#5-phase-v2--root-cause--group-fixes)
- [6. Phase V3 — Author and execute remediation](#6-phase-v3--author-and-execute-remediation)
- [7. Phase V4 — Promote soft-fail jobs to hard gates](#7-phase-v4--promote-soft-fail-jobs-to-hard-gates)
- [8. Phase V5 — Audit + close-out](#8-phase-v5--audit--close-out)
- [9. Tracking checklist](#9-tracking-checklist)

---

## 1. Goals and non-goals

### Goals

- Every workflow added or modified by the alignment plan **runs green**
  on each repo's `main` (or, where shakedown was intentional, runs
  with explicit `continue-on-error: true` until triaged).
- Every failure surfaced in this validation pass is **documented**,
  **root-caused**, and **fixed** before the soft-fail flag is removed.
- Soft-fail jobs (`integration-tests` in clients/worker, `trivy-fs`
  in deploy, first CodeQL run in every Python repo) are
  **per-repo-promoted** to hard gates only after that repo's runs are
  green.

### Non-goals

- Adding new check categories beyond what the alignment plan already
  specifies. Net-new checks belong in a follow-up alignment cycle.
- Re-litigating Appendix-A by-design exclusions (e.g. juniper-deploy
  staying off CodeQL).
- Changing branch-protection rules. Required-checks ARE updated as
  part of the soft-fail → hard-gate promotion, but the underlying
  protection rule is the user's call.

---

## 2. Inputs

- **Alignment plan**:
  `notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-PIPELINE-ALIGNMENT-PLAN.md` — gap matrix,
  templates, sequencing, validation criteria.
- **Authoritative commit map** (all on `main`):

  | Repo | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
  |---|---|---|---|---|---|
  | juniper-ml            | f9ddc06 | a0f14a7 | 2eabb34 | ad2f5bb | 036f747 |
  | juniper-canopy        | —       | 6bc6150 | —       | —       | —       |
  | juniper-cascor        | —       | 4e409d3 | —       | —       | —       |
  | juniper-data          | —       | 6586816 | —       | 64e6d13 | —       |
  | juniper-data-client   | —       | e71fdd9 | ada9b30 | —       | —       |
  | juniper-cascor-client | —       | 642fce5 | f7b4cfd | —       | —       |
  | juniper-cascor-worker | —       | b405f6a | a1ae19b | —       | —       |
  | juniper-deploy        | —       | 407f1bd | —       | d8d0dc1 | —       |

---

## 3. Phase V0 — Inventory current run state

For every repo, list the most-recent run of each *new-or-modified*
workflow and capture status, conclusion, and run URL. This
establishes the validation baseline.

### Workflows to inventory

| Workflow | Repos to check |
|---|---|
| `ci.yml` | all 8 |
| `claude.yml` | all 8 (no scheduled run; presence-only check is fine) |
| `codeql.yml` | ml, canopy, cascor, data, data-client, cascor-client, cascor-worker (7 — deploy excluded per Appx A) |
| `scheduled-tests.yml` | canopy, cascor, data, data-client, cascor-client, cascor-worker (6) |
| `lockfile-update.yml` | ml, canopy, cascor, data, cascor-client, cascor-worker (6 — deploy + data-client excluded as per file-presence audit) |
| `security-scan.yml` | all 8 (includes the deploy variant) |

### Discovery commands

```bash
# Tabular inventory across all 8 repos
for repo in ml canopy cascor data data-client cascor-client cascor-worker deploy; do
    full="pcalnon/juniper-${repo}"
    for wf in ci.yml claude.yml codeql.yml scheduled-tests.yml \
              lockfile-update.yml security-scan.yml; do
        echo -n "${full}::${wf}  "
        gh run list --repo "$full" --workflow "$wf" --limit 1 \
            --json status,conclusion,createdAt,event,headSha,url \
            --jq '.[0] | "\(.conclusion // .status // "no-runs")  \(.event)  \(.createdAt)  \(.url)"' \
            2>/dev/null || echo "  (workflow not found)"
    done
done
```

### Output expectations

- A **per-workflow row** with status (`success`/`failure`/`in_progress`/
  `no-runs`/`workflow-not-found`).
- For `claude.yml`: expected `no-runs` until someone @-mentions
  Claude. Presence-only.
- For `lockfile-update.yml`: expected `no-runs` until the next
  Monday 08:00 UTC schedule. Presence-only.
- For `scheduled-tests.yml`: expected `no-runs` until the next 06:00
  UTC schedule. Presence-only OR a one-off `gh workflow run
  scheduled-tests.yml --repo <repo>` to force a baseline run.
- For `ci.yml`: every recent push commit triggers it; the
  alignment plan commits **must** show `success` on all repos for
  Phase V1 to consider the rollout valid.
- For `codeql.yml`: the first run is the soft-fail shakedown. We
  expect to **find** issues here; the goal is to triage them, not
  to be surprised by them.
- For `security-scan.yml` (deploy variant only): the `trivy-fs` job
  has `continue-on-error: true`. The job-level result is what the
  shakedown cycle uses to decide whether to remove the flag.

---

## 4. Phase V1 — Document issues

For every workflow where Phase V0 returned `failure`, capture in a
**single new file** `notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-VALIDATION-FINDINGS.md`:

- Repo / workflow / job / run-URL.
- Failure category (one of: pre-commit, unit, integration, codeql,
  trivy, build, lockfile, docs, dependency, other).
- Verbatim error excerpt (≤ 30 lines per finding; trim aggressively).
- First diagnostic hypothesis (one sentence; revise in Phase V2).

The file is the **single source of truth** for what's actually
broken. Every fix in Phase V3 must reference a finding ID from this
document.

### Required structure

```markdown
# CI Validation Findings — <date>

## Index
| ID | Repo | Workflow | Job | Category | Status |
|----|------|----------|-----|----------|--------|
| V01 | juniper-X | ci.yml | unit-tests | unit | open |
| V02 | …
…

## V01 — <repo> / <workflow> / <job>
- Run: <gh URL>
- Category: <…>
- Excerpt:
…
- Hypothesis: <one sentence>
```

---

## 5. Phase V2 — Root-cause + group fixes

For each open finding, walk the failure to its root cause. Use
the same diagnostic discipline that drove the cascor / cascor-worker
/ pip-CVE fixes earlier this session:

1. Reproduce locally where possible (`pre-commit run --all-files`,
   `python -m pytest`, `pip-audit ...`).
2. Read the failure log carefully — distinguish "the check is
   wrong" from "the code is wrong" from "the environment is wrong."
3. Capture the root cause inline in the finding doc.
4. Group by **root cause**, not by symptom. Failures that share a
   cause get a single group ID and a single fix.

### Grouping taxonomy

- **G-CONFIG** — bad workflow YAML, mistuned hook config, missing
  secret.
- **G-CODE** — real source-side defect surfaced by the new check.
- **G-INFRA** — dep wheel ABI mismatch, runner-image drift, network
  flake.
- **G-CONTRACT** — repo expectations differ from the canonical
  template (e.g. tests live in `src/tests/` not `tests/`).

### Prioritization

| Priority | Trigger | SLA |
|---|---|---|
| **P0** | Blocks every push to `main` (e.g. `pre-commit` job hard-fails on every commit). | Same-day fix. |
| **P1** | Blocks the canonical CI on at least one common code path. | Within 2 days. |
| **P2** | Soft-fail job stays soft-fail; doesn't block merges but the shakedown cycle can't end. | Within 1 week. |
| **P3** | Cosmetic / informational. | Folded into the next release. |

---

## 6. Phase V3 — Author and execute remediation

Per repo, per fix-group, ship a single commit (direct-to-`main`
unless the user re-enables PR review). Each commit MUST:

- Reference the finding ID(s) (`V01`, `V02`, …) it closes.
- Reference the group ID(s) (`G-CONFIG`, `G-INFRA`, …) it addresses.
- State whether the fix promotes any soft-fail job to hard-gate (and
  if so, which).

### Execution discipline

- Do not bundle unrelated fixes. One root-cause group per commit.
- Validate locally before pushing where reproducible.
- After each push, re-trigger the affected workflow (`gh workflow
  run`) and confirm green before opening the next remediation
  commit.

### Commit message template

```text
fix(ci): <short description> (V01, V03 — G-CONFIG)

Resolves findings V01 and V03 from the validation pass
documented in notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-VALIDATION-FINDINGS.md. Both
share root cause G-CONFIG (<one-line summary>).

Promotes <integration-tests | trivy-fs | …> from soft-fail to
hard-gate? <yes/no — if yes, which workflow + how>.
```

---

## 7. Phase V4 — Promote soft-fail jobs to hard gates

The alignment plan deliberately introduced three classes of
soft-fail jobs to absorb the first-run shakedown:

| Soft-fail surface | Where | Promotion criterion |
|---|---|---|
| `integration-tests` exit-code-5 / `::warning::` in `required-checks` | data-client, cascor-client, cascor-worker | Two consecutive green runs on `main`. |
| `trivy-fs` `continue-on-error: true` | deploy | Two consecutive runs with no `HIGH`/`CRITICAL` ignore-unfixed findings, OR explicit `--ignore-vuln` entries cover whatever the runner image carries. |
| First CodeQL run | every Python repo | One green run with all findings either resolved or explicitly suppressed via repo's `codeql-config`. |

### Promotion mechanics

- **Per repo**, not fleet-wide. Each repo gets the promotion the
  moment its specific shakedown criteria are met. **Do not block** a
  repo whose CodeQL is green just because another repo's isn't.
- **Reversible**. If a hard gate fires false positives within the
  first 7 days, demote it back to soft-fail and re-open the finding.

---

## 8. Phase V5 — Audit + close-out

Once every soft-fail job has been promoted (or explicitly waived),
re-walk the alignment plan in full and:

1. Re-execute the Appendix-C discovery commands.
2. Confirm every Appendix-A by-design exclusion still holds.
3. Update both this document and the alignment plan with a
   "Closed" header at the top.
4. Append a short retrospective to the plan covering:
   - What worked.
   - What didn't (per finding, per fix).
   - What the next alignment cycle should bring.

---

## 9. Tracking checklist

### Phase V0 — Inventory

- [ ] Run inventory commands. Capture results inline (or as a
      separate artifact).
- [ ] Decide which repos to skip in V1 (where the inventory shows
      everything green).

### Phase V1 — Documentation

- [ ] Create `notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-VALIDATION-FINDINGS.md`.
- [ ] Populate Index table with one row per failing run.

### Phase V2 — Root-cause

- [ ] Walk each open finding to its root cause.
- [ ] Assign a group ID and priority.

### Phase V3 — Remediation

- [ ] Fix every P0 finding.
- [ ] Fix every P1 finding.
- [ ] Fix or explicitly defer every P2/P3 finding.

### Phase V4 — Promotion

- [ ] juniper-data-client: integration-tests soft → hard.
- [ ] juniper-cascor-client: integration-tests soft → hard.
- [ ] juniper-cascor-worker: integration-tests soft → hard.
- [ ] juniper-deploy: trivy-fs soft → hard.
- [ ] juniper-ml: codeql shakedown → required.
- [ ] juniper-canopy: codeql shakedown → required.
- [ ] juniper-cascor: codeql shakedown → required.
- [ ] juniper-data: codeql shakedown → required (already required
      pre-alignment; confirm).
- [ ] juniper-data-client: codeql shakedown → required.
- [ ] juniper-cascor-client: codeql shakedown → required.
- [ ] juniper-cascor-worker: codeql shakedown → required.

### Phase V5 — Close-out

- [ ] Re-run the discovery commands; sanity-check parity with the
      alignment plan.
- [ ] Append "Closed" header + retrospective to alignment plan.
- [ ] Append "Closed" header + retrospective to this document.
