# Thread Handoff Procedure

**Purpose**: Preserve context fidelity during long-running Claude Code sessions by proactively handing off to a new thread before context compaction degrades output quality.

**Last Updated**: 2026-02-23

---

## Why Handoff Over Compaction

Thread compaction summarizes prior context to free token capacity. This introduces **information loss** — subtle details about decisions made, edge cases discovered, partial progress, and the reasoning behind specific implementation choices get compressed or dropped. For work on the Juniper meta-package (e.g., dependency version updates, pyproject.toml restructuring, CI/CD pipeline changes, multi-step documentation tasks), this degradation can cause:

- Repeated mistakes the thread already resolved
- Loss of discovered constraints or gotchas
- Re-reading files that were already understood
- Inconsistent changes across related files (pyproject.toml, README.md, workflows)

A **proactive handoff** transfers a curated, high-signal summary to a fresh thread with full context capacity, preserving the critical information while discarding the noise.

---

## When to Initiate a Handoff

Trigger a handoff when **any** of the following conditions are met:

| Condition                   | Indicator                                                                                                                   |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Context saturation**      | Thread has performed 15+ tool calls or edited 5+ files                                                                      |
| **Phase boundary**          | A logical phase of work is complete (e.g., planning done → implementation starting; implementation done → testing starting) |
| **Degraded recall**         | The agent re-reads a file it already read, or asks a question it already resolved                                           |
| **Multi-file transition**   | Moving between major concerns (e.g., `pyproject.toml` → CI/CD workflows → documentation)                                   |
| **User request**            | User says "hand off", "new thread", "continue in a fresh thread", or similar                                                |

**Do NOT handoff** when:

- The task is nearly complete (< 2 remaining steps)
- The current thread is still sharp and producing correct output
- The work is tightly coupled and splitting would lose critical in-flight state

---

## Handoff Protocol

### Step 1: Checkpoint Current State

Before initiating the handoff, mentally inventory:

1. **What was the original task?** (user's request, verbatim or paraphrased)
2. **What has been completed?** (files created, files edited, versions changed)
3. **What remains?** (specific next steps, not vague summaries)
4. **What was discovered?** (gotchas, constraints, decisions, rejected approaches)
5. **What files are in play?** (paths of files read, modified, or relevant)

### Step 2: Compose the Handoff Goal

Write a **concise, actionable** goal for the new thread. Structure it as:

```bash
Continue [TASK DESCRIPTION].

Completed so far:
- [Concrete item 1]
- [Concrete item 2]

Remaining work:
- [Specific next step 1]
- [Specific next step 2]

Key context:
- [Important discovery or constraint]
- [File X was modified to do Y]
- [Approach Z was rejected because...]
```

**Rules for the goal**:

- **Be specific**: "Update juniper-cascor-client version constraint in pyproject.toml to >=0.2.0" not "finish the version bump"
- **Include file paths**: The new thread doesn't know what you've been looking at
- **State decisions made**: So the new thread doesn't re-litigate them
- **Mention verification status**: If builds/checks were run, state pass/fail
- **Keep it under ~500 words**: Dense signal, no filler

### Step 3: Execute the Handoff

Present the handoff goal to the user and recommend starting a new thread with it as the initial prompt.

---

## Handoff Goal Templates

### Template: Dependency Update

```bash
Continue updating dependencies in juniper-ml meta-package.

Completed:
- Updated [package] version in pyproject.toml to [version]
- Verified build: python -m build
- Verified package: twine check dist/*

Remaining:
- Update [other package] version constraints
- Update README.md version table if needed
- Verify CI workflow compatibility

Key context:
- [Package X] requires [constraint] because [reason]
- Verify with: python -m build && twine check dist/*
```

### Template: CI/CD Pipeline Change

```bash
Continue modifying CI/CD pipeline for juniper-ml.

Completed:
- Modified .github/workflows/publish.yml to [change]
- [Other changes]

Remaining:
- [Specific pipeline step to add/modify]
- Test workflow syntax: act -j [job-name] (if available) or validate YAML

Key context:
- Using trusted publishing (OIDC), no API tokens
- Pipeline publishes to TestPyPI first, then PyPI
- [Decision or constraint discovered]
```

### Template: Documentation / Package Restructure

```bash
Continue [restructure task] for juniper-ml meta-package.

Completed:
- Modified pyproject.toml: [specific changes]
- Updated README.md: [specific changes]

Remaining:
- [Specific next step]
- Rebuild and verify: python -m build && twine check dist/*

Key context:
- Package name on PyPI: juniper-ml
- No importable modules (meta-package only)
- [Decision or discovery]
```

### Template: Multi-Phase Task (Phase Transition)

```bash
Continue [OVERALL TASK] — starting Phase [N]: [PHASE NAME].

Phase [N-1] ([PREV PHASE NAME]) completed:
- [Deliverable 1]
- [Deliverable 2]
- Build verified: python -m build && twine check dist/*

Phase [N] scope:
- [Step 1]
- [Step 2]
- [Step 3]

Key context from prior phases:
- [Decision or discovery that affects this phase]
- [File modified in prior phase that this phase depends on]
```

---

## Best Practices

1. **Handoff early, not late** — A handoff at 70% context usage is better than compaction at 95%
2. **One handoff per phase boundary** — Don't chain 5 handoffs for one task; batch related work
3. **Include the verification command** — Always tell the new thread how to check its work (`python -m build`, `twine check dist/*`, etc.)
4. **Reference CLAUDE.md** — The new thread will read it automatically, but call out any conventions relevant to the remaining work
5. **Don't duplicate CLAUDE.md content** — The new thread already has it; only include task-specific context
6. **State the git status** — If files are staged, modified, or if a branch is in use, mention it

---

## Integration with Project Workflow

This procedure complements the existing development workflow in CLAUDE.md. When a thread handoff occurs:

- The new thread should verify it can build the package before making changes
- The new thread should re-read any file it plans to edit (fresh context, no assumptions)
- If the handoff crosses a major boundary (e.g., pyproject.toml → CI/CD), the new thread should check the relevant files for consistency

---

## Examples

### Example 1: Simple Handoff

> *Thread has updated one dependency extra but still needs to update others and rebuild.*

```bash
Continue updating dependency extras in juniper-ml meta-package.

Completed:
- Updated `clients` extra in pyproject.toml:
  juniper-data-client bumped from >=0.3.0 to >=0.4.0
- Verified build passes: python -m build

Remaining:
- Update `worker` extra: juniper-cascor-worker from >=0.1.0 to >=0.2.0
- Update README.md dependency table to reflect new versions
- Final build + twine check

Key context:
- juniper-data-client 0.4.0 added async support; no API breaking changes
- Verify with: python -m build && twine check dist/*
- On branch: main, pyproject.toml modified (unstaged)
```

### Example 2: Handoff After Discovery

> *Thread was asked to add a new extra group but discovered a version conflict.*

```bash
Continue adding `dashboard` extra to juniper-ml meta-package. Investigation
revealed a version conflict between proposed dependencies.

Findings:
- juniper-canopy>=0.2.0 requires dash>=2.15
- juniper-cascor-client>=0.1.0 pins plotly<5.18 (incompatible with dash>=2.15)
- This conflict must be resolved upstream before adding the extra

Remaining:
- Decide: either pin juniper-canopy<0.2.0 or wait for cascor-client fix
- Once resolved, add `dashboard` extra to pyproject.toml
- Update README.md with new extra documentation

Key context:
- Do NOT add the `dashboard` extra until the plotly/dash conflict is resolved
- The conflict is tracked in juniper-cascor-client issue #42
- On branch: feat/dashboard-extra, no uncommitted changes
```
