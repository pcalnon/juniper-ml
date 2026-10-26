# CLAUDE.md

**Project**: juniper-ml — Meta-package for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.11.3
**Last Updated**: 2026-10-26

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

This is `juniper-ml`, a **meta-package** for the Juniper ML research platform. It provides a single `pip install juniper-ml[all]` entry point that pulls in the actual Juniper packages as dependencies, and also contains internal automation scripts used for Claude Code workflows, utility tooling for the Juniper ecosystem, and project documentation.

There is no importable Python application package in this repository. Functional behavior here is primarily package metadata (`pyproject.toml`) plus shell tooling in `scripts/` and `util/`, with regression coverage in `tests/`.

## Hazards (resident — do not relocate)

Directives whose **non-application destroys work**. Everything else in this file may
be demoted to [`docs/REFERENCE.md`](docs/REFERENCE.md) under the memory budget; these
may not, because a pointer only helps an agent that already knows to look. Adding a
new hazard here is legitimate — ratchet space out of a reference section in the same
PR rather than waiving the budget gate.

- **The orphan reaper can kill live experiments.** `util/reap_pytest_orphans.bash`
  treats reparenting to `systemd --user` as the orphan predicate — and
  `experiment_stack.bash` / `isolated_stack.bash` launch services under `nohup`, so
  healthy experiment services, orchestrators and watchdogs land there too. Two
  protection keys, either sufficient: the pid appears in a run-dir `*.pid`, or its
  cmdline references a run root. Observed 2026-08-16: a dry run called the
  orchestrator, the live cascor service and the watchdog all `WOULD REAP`.
- **`KILL_WORKERS=1` is opt-in and kills worker processes.** Default `0` in
  `util/juniper_chop_all.bash`; nohup-only, ignored under `--systemd`. Do not set it
  to "be thorough".
- **A CI-skip marker on the head commit orphans every required check.** The PR
  becomes permanently unmergeable while the aggregate rollup can still read SUCCESS —
  every context sits at "expected" forever. Never put that marker on a PR head; the
  repair is the server-side `update-branch` API, not a force-push.
- **`max_epochs` alone silently diverges the service from the CLI.** The service
  applies it only to the *initial* output pass; later passes read `output_epochs`,
  which falls back to 10000. The direct CLI aliases the two. **Any CLI-vs-service
  comparison must set both, to the same value**, or the service is quietly
  better-trained and slower than the config appears to ask for.
- **One unsigned commit makes a branch permanently unmergeable.** The repos carry
  `required_signatures` (all 9 as of 2026-08-12), and squash does not rescue it. A
  host without signing configured (turing, as of 2026-10-15) must land work through
  `util/open_signed_pr.py`, not a local commit + push. Check with
  `git log -1 --format=%G?` (`N` = unsigned). An IDE agent (Cursor, Copilot, Amp) must
  never answer a signing failure with `--no-gpg-sign` or `-c commit.gpgsign=false`: stop
  and ask the owner, who approves the run and touches the key. Owner signing for the
  Juniper tree: `util/configure_commit_signing.py`. Plans:
  `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`,
  `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`.
- **`/tmp` deletes live files.** On the Linux host it is a tmpfs that `systemd-tmpfiles-clean`
  ages daily (`q /tmp 1777 root root 10d`): a file untouched for ten days is deleted while in
  use. In the week to 2026-10-26 it emptied the E2E stack's pid files and venv three times,
  leaving seven live servers killable by the orphan reaper. Write every temp file under the
  repo's gitignored `tmp/` (§ Temporary files below); gate G-TMP blocks new literals.

---

## Build & Package Commands

```bash
# Install locally: pip install -e ".[<extra>]" -- extras are in pyproject.toml; ".[all]" is multi-GB (pulls torch via worker)

# Run all tests -- the full ordered list of 227 `python3 -m unittest`
# commands lives in docs/REFERENCE.md -- see "Running every suite" under
# § Test Suite Reference. It is generated from ci.yml's regression step, which is
# the authoritative list; tests/test_ci_test_wiring_drift.py gates that every suite
# on disk is invoked there, and util/ad-hoc/2026-09-10_agents_md_test_list_drift.py
# reports any suite CI runs that the reference does not name.
bash scripts/test_resume_file_safety.bash
# doc-link validator regression tests live in juniper-doc-tools/tests/
# and run under the dedicated `CI -- juniper-doc-tools` workflow.

# Run pre-commit hooks
pre-commit run --all-files

# Validate documentation links (requires `pip install juniper-doc-tools`
# or `pip install -e juniper-doc-tools/` for editable local development)
juniper-check-doc-links --exclude templates --exclude history --exclude legacy --exclude pull_requests --exclude releases --exclude analysis --exclude fixes --exclude development --exclude CHANGELOG.md --exclude tmp --cross-repo skip

# Validate documentation links (including cross-repo)
juniper-check-doc-links --exclude templates --exclude history --exclude legacy --exclude pull_requests --exclude releases --exclude analysis --exclude fixes --exclude development --exclude CHANGELOG.md --exclude tmp --cross-repo check
```

## Publishing

Releases are published via GitHub Actions (`.github/workflows/publish.yml`). The workflow is triggered by a GitHub release event and publishes first to TestPyPI (with install verification), then to PyPI. Both environments use trusted publishing (OIDC, no API tokens).

**Release convention (mandatory, all packages).** Every PyPI deploy — the meta-package and every
shared / sub-package — is performed by **cutting a GitHub Release** (never a bare `git push <tag>`),
and the release notes are authored from
[`notes/templates/TEMPLATE_RELEASE_NOTES.md`](notes/templates/TEMPLATE_RELEASE_NOTES.md) and
**archived under `notes/releases/`** (`RELEASE_NOTES_v<version>.md` for the meta-package;
`RELEASE_NOTES_<pkg>_v<version>.md` for a shared / sub-package). For the meta-package the Release
event triggers `publish.yml`; for a shared / sub-package, cutting the Release **creates** the
`juniper-<pkg>-v*` tag and fires its `publish-<pkg>.yml` through `release: published` (those
workflows deliberately do **not** also subscribe to `push: tags` — that double-fire raced the
immutable TestPyPI upload in juniper-ml#555). Full steps:
[`notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11](notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md). (This convention drifted
during rapid concurrent refactoring — several sub-packages shipped tag-only — and is being restored.)

Per-package publish pipelines for the six in-repo shared packages (`juniper-ci-tools`, `juniper-config-tools`, `juniper-doc-tools`, `juniper-model-core`, `juniper-observability`, `juniper-service-core`) -- the release tag prefix, workflow and build directory for each, and the contracts they share -- are in [`docs/REFERENCE.md` § Independent Sibling Package Publish Pipelines](docs/REFERENCE.md#independent-sibling-package-publish-pipelines) — read it when working on this area.

## Shared Observability Helpers

The four idempotent `prometheus_client` registration helpers, and when to use each. Moved to [`docs/REFERENCE.md` § Shared Observability Helpers Reference](docs/REFERENCE.md#shared-observability-helpers-reference) — read it when working on this area.

## Shared Service-Core Contracts

The load-bearing invariants a well-meaning refactor silently breaks in the shared FastAPI service tier. Moved to [`docs/REFERENCE.md` § Shared Service-Core Contracts](docs/REFERENCE.md#shared-service-core-contracts) — read it when working on this area.

## Repository Structure

The fully annotated repository tree, with the purpose of every directory and key file. Moved to [`docs/REFERENCE.md` § Repository Structure Reference](docs/REFERENCE.md#repository-structure-reference) — read it when working on this area.

```bash
juniper-ml/
├── AGENTS.md                  # This file (CLAUDE.md is a symlink to it)
├── conf/                      # Project configuration, incl. memory_budget.json
├── docs/                      # User-facing documentation (REFERENCE.md is the deep reference)
├── images/                    # Project branding
├── juniper-ci-tools/          # Published sub-package: CI tooling + sequence-safety screens
├── juniper-config-tools/      # Published sub-package: env-prefix migration helpers
├── juniper-doc-tools/         # Published sub-package: markdown link validator
├── juniper-model-core/        # Published sub-package: model conformance kit
├── juniper-observability/     # Published sub-package: prometheus/middleware/logging
├── juniper-service-core/      # Published sub-package: shared FastAPI service tier
├── logs/                      # Runtime log output
├── notes/                     # Design docs, plans, procedures, audits
├── papers/                    # Research papers and references
├── prompts/                   # Claude Code session prompts
│   └── agent_templates/       # Custom-agent template library + data layer
├── reports/                   # Per-run evidence artifacts
├── resources/                 # External resources
├── scripts/                   # Launcher and session scripts
├── tests/                     # Regression suites
└── util/                      # Utility scripts and tools
```

## Key Files

### Documentation

- `docs/DOCUMENTATION_OVERVIEW.md` -- Navigation index for all juniper-ml documentation
- `docs/QUICK_START.md` -- Installation and verification guide
- `docs/REFERENCE.md` -- Technical reference: extras, compatibility matrix, service ports, environment variables
- `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` -- Quick-reference card for development tasks

### Scripts and Launchers

- `scripts/wake_the_claude.bash` -- Claude Code launcher with flag parsing, session ID persistence, resume handling, and interactive/headless execution modes
- `scripts/claude_interactive.bash` -- Main interactive Claude Code agent launcher
- `scripts/default_interactive_session_claude_code.bash` -- Configuration template for default interactive Claude sessions
- `scripts/activate_conda_env.bash` -- Conda environment activation and management
- `scripts/resume_session.bash` -- Convenience wrapper for resuming a Claude Code session
- `claudey` -- Repo-root symlink to `scripts/claude_interactive.bash` for interactive sessions

### Utilities

Per-script reference for everything in `util/`, including the failure class each guard encodes. Moved to [`docs/REFERENCE.md` § Utility Script Reference](docs/REFERENCE.md#utility-script-reference) — read it when working on this area.

### Tests

Per-suite descriptions for every regression test, and the failure class each one pins. Moved to [`docs/REFERENCE.md` § Test Suite Reference](docs/REFERENCE.md#test-suite-reference) — read it when working on this area.

### CI/CD Workflows

Per-workflow reference for every file in `.github/workflows/`, including the contract each job must not break. Moved to [`docs/REFERENCE.md` § CI/CD Workflow Inventory](docs/REFERENCE.md#cicd-workflow-inventory) — read it when working on this area.

### Configuration

- `conf/hosts/<host>/` -- Per-host target state and records: `expected.yaml`, which `util/host_state_check.py` judges `util/host_state_probe.bash`'s captures against (the host gates; turing bring-up G1), turing's conda-env specs and `hosttools-environment.yml`, and `mcp.json`, the Serena pin `util/mcp_setup.bash` reads (H4)

## CI/CD Pipelines

What each workflow does, its triggers, and the contract each job must not break. Moved to [`docs/REFERENCE.md` § CI/CD Pipeline Reference](docs/REFERENCE.md#cicd-pipeline-reference) — read it when working on this area.

### PR base-branch guard (required check)

`.github/workflows/pr-base-branch-guard.yml` fails any PR whose base is not the default
branch. Its job name -- **`Guard PR base branch`** -- is a **required status check**, so
renaming the job or deleting the file makes `main` unmergeable until it is un-required.
A stacked PR is governed by **no ruleset at all** (both are `~DEFAULT_BRANCH`-scoped), so
it merges with zero checks; this guard is the only thing that runs there. Moved to
[`docs/REFERENCE.md` § PR Base-Branch Guard](docs/REFERENCE.md#pr-base-branch-guard) --
read it when working on this area.

## Pre-commit Hooks

Setup commands and the full hook table (version, scope, and the failure each hook catches). Moved to [`docs/REFERENCE.md` § Pre-commit Hook Reference](docs/REFERENCE.md#pre-commit-hook-reference) — read it when working on this area.

## Secrets Management (SOPS)

The repository uses [SOPS](https://github.com/getsops/sops) with age encryption for secrets:

- **Encrypted files**: `.env`, `.env.secrets` (matched by `.sops.yaml`)
- **Encryption key**: age key configured in `.sops.yaml`
- **Existing encrypted file**: `.env.enc`
- **Pre-commit protection**: The `no-unencrypted-env` hook blocks unencrypted `.env` files from being committed
- **Usage guide**: `notes/JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md`

## Ecosystem Context

This repo is part of the broader Juniper ecosystem. See the parent directory's `CLAUDE.md` at `~/Development/python/Juniper/CLAUDE.md` for the full project map, dependency graph, shared conventions, and conda environment details.

### Dependency extras reference

| Extra        | Packages                                                                                                                                                                                                     |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `clients`    | `juniper-data-client>=0.5.0`, `juniper-cascor-client>=0.8.0`                                                                                                                                                 |
| `worker`     | `juniper-cascor-worker>=0.4.0`                                                                                                                                                                               |
| `servers`    | `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0`, `juniper-cascor[api,juniper-data]>=0.12.0`, `juniper-data[api]>=0.17.1`                                                                                  |
| `tools`      | `juniper-ci-tools>=0.1.0`, `juniper-config-tools>=0.1.0,<0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`, `juniper-model-core>=0.1.0,<0.4.0`, `juniper-observability>=0.4.1`, `juniper-service-core>=0.7.1,<0.8.0` |
| `doc-tools`  | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`)                                                                                                                     |
| `recurrence` | `juniper-recurrence-model>=0.6.0,<0.7.0`, `juniper-recurrence>=0.8.0,<0.9.0`, `juniper-recurrence-client>=0.3.0,<0.4.0`                                                                                      |
| `all`        | All of the above                                                                                                                                                                                             |

## Conventions

- Python >=3.12 required (classifiers include 3.12, 3.13, 3.14)
- Line length: 512 for all linters (flake8, markdownlint)
- `notes/` documents are named `JUNIPER_<YYYY-MM-DD>_JUNIPER-<REPO>_<CONTENTS-DESCRIPTION-PHRASE>.md` (REPO one of ML / CANOPY / RECURRENCE / CASCOR / CASCOR-CLIENT / CASCOR-WORKER / DATA / DATA-CLIENT / DEPLOY / ECOSYSTEM). Exempt: `notes/{templates,releases,requirements,legacy}/` and README files. Full rules + migration record: [`notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md)
- **Name every document a summary REFERENCES or CHANGES** (mandatory, ecosystem-wide, 2026-09-01; widened 2026-09-02). In a step-completion or work-arc summary:
  - every **reference** to a document carries its filename — by section number, by role ("the plan", "the analysis"), or by implication. One document cited → name it on first reference; two or more → **every** reference carries its filename.
  - the summary **lists by filename** every document the step created or modified.
  - Covers summaries, PR bodies, handoffs, issue comments. Examples + rationale: `Juniper/AGENTS.md` § Cross-Project Conventions, which is **unversioned** — this bullet is the versioned record.

### Script placement (mandatory)

Utility, single-use, temporary, and unfinished scripts MUST be created under `util/`:

| Script type                                    | Destination                    |
| ---------------------------------------------- | ------------------------------ |
| Permanent utility, regularly used              | `util/<name>.{py,bash}`        |
| Single-use, temporary, ad-hoc, or unfinished   | `util/ad-hoc/<name>.{py,bash}` |

**`/tmp/` is prohibited** as the home for any script that produces, modifies, or analyzes repository content. `/tmp/` is reaped when sessions / sandboxes / containers end, and scripts placed there are lost. Since 2026-10-26 it is no scratch workspace either: transient data goes to the repo's `tmp/` (next section), e.g. `uv pip compile -o tmp/lock && mv tmp/lock requirements.lock`.

**Incident motivating this rule**: `phase4_consolidate.py` and `v2_citation_validate.py` were authored in `/tmp/` across the v1-v4 requirements snapshot effort and are now irrecoverable. See [`notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §7](notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection) and [plan-doc §12](notes/JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md#12-open-issues--questions-discovered-during-execution).

See [`util/ad-hoc/README.md`](util/ad-hoc/README.md) for the ad-hoc-script convention (file-header requirements, when to graduate to `util/` proper).

### Temporary files: `tmp/`, never `/tmp` (mandatory)

**No file is ever written under `/tmp`** (nor `/var/tmp`) by this repo's scripts, tests, tools, services, sessions or agents (owner directive, 2026-10-26). On the Linux host `/tmp` is a tmpfs that `systemd-tmpfiles-clean` ages daily (`q /tmp 1777 root root 10d`): a file untouched for ten days is deleted while still in use, and a reboot erases the rest. In the week to 2026-10-26 it emptied a live test stack's pid files and venv three times. macOS ages `/tmp` too.

- This repo's temp root is its gitignored `tmp/`. `TMPDIR` points at the **primary** checkout's (it outlives any worktree); a worktree-isolated session writes its own scratch files into its worktree's `tmp/`.
- Sessions get `TMPDIR` from the launcher (`scripts/wake_the_claude.bash`) and a user-level SessionStart hook, so `tempfile`, `mktemp` and pytest's `tmp_path` follow it. Both also set `GIT_CEILING_DIRECTORIES` at the `tmp/` dirs: under a `TMPDIR` inside a checkout, git would otherwise find the enclosing checkout, so a test's "not a git repo" dir sets the ceiling (a proper ancestor of where git starts) in its subprocess env.
- In code: never a `/tmp/...` literal and never `${TMPDIR:-/tmp}`; tests use `tmp_path`; state another process must find (pid files, run directories) lives at a fixed path under the primary's `tmp/` (`util/juniper_repo_tmp.bash`) or `~/.local/state/`, never one derived from `TMPDIR`. Gate G-TMP (`util/tmp_path_literal_check.py`) fails a new literal.
- Out of scope: GitHub-hosted CI runners and a container's own `/tmp`.
- Ecosystem rule and rationale: [`notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md`](notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md).
- **Owner rulings, 2026-10-26** (canonical: `notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md`):
  - `juniper-check-doc-links` ignores `tmp/`: every invocation passes `--exclude tmp`.
  - pytest does not ignore `tmp/`: no `norecursedirs`, `--ignore` or `collect_ignore` entry names it.
  - A local Docker build ignores `tmp/`: the build context's `.dockerignore` lists it.
  - `tmp/` is a valid search location: a script that counts matches with `grep` or `find` includes it.
  - Full-tree copies of the repo, and copies of log files, may live in `tmp/`.
  - **Retention.** A file a work arc writes to `tmp/` is kept until it is no longer needed, no work arc (its own
    included) uses it, and it is no longer needed for documentation or reference, and, where needed, until it has
    been archived in an appropriate non-temporary directory. Only then may it be deleted.

---

## Pull Request Conventions

### Requirements (JR-ID) cross-references

Every PR description SHOULD carry a `## Requirements` section listing the `JR-<REPO>-<AREA>-<NNN>` IDs it touches, with the verbs `Closes` / `Partially closes` / `References` / `Supersedes` (the PR template pre-fills it; descriptions only, never commit messages). What each verb does, the ID lookup and the scope moved to [`docs/REFERENCE.md` § PR Requirements (JR-ID) Cross-References](docs/REFERENCE.md#pr-requirements-jr-id-cross-references) — read it when writing a PR body.

### Other PR description conventions

For larger / cross-cutting PRs, the long-form template at [`notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md`](notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md) covers Summary, Context, Priority table, Keep-a-Changelog grouping, Impact/SemVer, Testing, and rollback plans. The repo-level `.github/pull_request_template.md` is the lightweight default; the long-form template is opt-in for PRs that warrant it.

---

## Worktree Procedures (Mandatory -- Task Isolation)

Setup and cleanup procedures, directory naming, the when-to-use table, and `util/worktree_cleanup.bash`. **The mandate is not lost**: the always-loaded parent `Juniper/AGENTS.md` (`CLAUDE.md` is a symlink to it) § Worktree Procedures carries the operating instruction, the centralized worktree location and the naming convention. Moved to [`docs/REFERENCE.md` § Worktree Procedures Reference](docs/REFERENCE.md#worktree-procedures-reference) — read it when working on this area.

> Deliberately **not** a link. `Juniper/AGENTS.md` sits in the ecosystem parent directory, which is **not a git repository** — `git rev-parse` there returns *"not a git repository"*. CI clones the sibling repos under a synthetic ecosystem root and that file is not among them, so a relative link to it resolves locally and is broken in `Docs Full Check` every time. It is also why edits to that file carry no PR, no CI and no history, and are invisible to any other machine.

## Thread Handoff (Mandatory -- Replaces Thread Compaction)

> **CRITICAL OPERATING INSTRUCTION**: Thread handoff MUST be performed instead of
> thread compaction. This section defines mandatory behavior that overrides Claude
> Code's default compaction process.

### What This Is

When a long-running conversation approaches context limits, Claude Code normally
performs **thread compaction** -- summarizing prior context to free token capacity.
This introduces information loss. Instead, Claude Code instances working on this
project MUST perform a **proactive thread handoff**: transferring a curated,
high-signal summary to a fresh thread with full context capacity.

The full handoff protocol is defined in **`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`**.
Read that file when a handoff is triggered.

### When to Trigger a Handoff

**Automatic trigger (pre-compaction threshold):** Initiate a thread handoff when
token utilization reaches **95% to 99%** of the level at which thread compaction
would normally be triggered. This means the handoff fires when you are within
**1% to 5%** of the compaction threshold, ensuring the handoff completes before
compaction would occur.

Concretely:

- If compaction would trigger at N% context utilization, begin handoff at
  (N - 5)% to (N - 1)%.
- **Self-assessment rule**: At each turn where you are performing multi-step work,
  assess whether you are approaching the compaction threshold. If you estimate you
  are within 5% of it, begin the handoff protocol immediately.
- When the system compresses prior messages or you receive a context compression
  notification, treat this as a signal that handoff should have already occurred --
  immediately initiate one.

**Additional triggers** (from `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`):

| Condition                   | Indicator                                            |
| --------------------------- | ---------------------------------------------------- |
| **Context saturation**      | 15+ tool calls or 5+ files edited                    |
| **Phase boundary**          | Logical phase of work is complete                    |
| **Degraded recall**         | Re-reading files or re-asking resolved questions     |
| **Multi-file transition**   | Moving between major concerns                        |
| **User request**            | User says "hand off", "new thread", or similar       |

**Do NOT handoff** when:

- Task is nearly complete (< 2 remaining steps)
- Current thread is still sharp and producing correct output
- Work is tightly coupled and splitting would lose in-flight state

### How to Execute a Handoff

1. **Checkpoint**: Inventory what was done, what remains, what was discovered,
   and what files are in play
2. **Compose the handoff goal**: Write a concise, actionable summary
   (see templates in `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`)
3. Combine checkpoint and handoff goal to create a detailed thread handoff prompt
4. **Present to user**: Output the handoff prompt and recommend starting a new
   thread with that handoff as the initial prompt
5. Archive the thread handoff prompt to prompts/thread-handoff_automated-prompts/ dir with filename convention: HANDOFF_YYYY-MM-DD_[Session Description].md
6. **Include verification commands**: Specify how the new thread should verify
   its starting state in the handoff prompt
7. **State git status**: Mention branch, staged files, and uncommitted work in handoff prompt

### Rules

- **This is not optional.** Every Claude Code instance on this project must
  follow these rules.
- **Handoff early, not late.** A handoff at 70% context is better than
  compaction at 95%.
- **Do not duplicate CLAUDE.md content** in the handoff goal.
- **Be specific**: Include file paths, decisions made, and verification status.
