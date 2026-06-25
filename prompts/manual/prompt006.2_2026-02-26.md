# Handoff Goal

Write a detailed manual procedure document for publishing juniper-cascor and juniper-data to PyPI.

This should be a step-by-step runbook covering ALL manual actions needed, including:

- Worktree creation, code changes, build/verify, commit, push, merge, cleanup for both repos
- GitHub release creation
- Workflow monitoring and environment approval
- Post-publish verification
- The juniper-data-client manual TestPyPI fix

Completed so far:

- Full exploration of all 6 Juniper repos' CI/CD, packaging, and publish workflows
- Identified all blockers and current PyPI/TestPyPI publish status
- User approved approach: juniper-cascor gets juniper_cascor/ wrapper package (NOT full restructure)
- Plan file written at /home/pcalnon/.claude/plans/groovy-scribbling-storm.md with all technical details

Key context:

- juniper-cascor needs: (1) new juniper_cascor/__init__.py at repo root with __version__ = "0.3.17",
  (2) [tool.setuptools.packages.find] added to pyproject.toml with where = [".", "src"]
- juniper-data needs: 6 action ref pins in .github/workflows/publish.yml (3 in testpypi job, 3 in pypi job)
  - actions/checkout@v4 → actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
  - actions/setup-python@v5 → actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.6.0
  - pypa/gh-action-pypi-publish@release/v1 → pypa/gh-action-pypi-publish@ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e  # v1.13.0
- juniper-data-client v0.3.1 blocked by TestPyPI 403 — needs manual trusted publisher reconfig
- All repos use OIDC trusted publishing, pypi/testpypi GitHub environments with 5-min wait + required reviewer (pcalnon)
- juniper-cascor-client (v0.1.0), juniper-cascor-worker (v0.1.0), juniper-ml (v0.1.0) already on PyPI — no action needed
- Worktrees go in /home/pcalnon/Development/python/Juniper/worktrees/ with naming convention:
"\<repo-name>--\<branch-name>--\<YYYYMMDD-HHMM>--\<short-hash>"
- Plan file: /home/pcalnon/.claude/plans/groovy-scribbling-storm.md
- Worktree procedures: each repo has notes/WORKTREE_SETUP_PROCEDURE.md and notes/WORKTREE_CLEANUP_PROCEDURE.md

Remaining work:

1. Read the plan file at /home/pcalnon/.claude/plans/groovy-scribbling-storm.md
2. Read both repos' worktree procedure docs for exact steps
3. Write a comprehensive manual procedure document (location TBD — likely notes/ or prompts/)
4. Include exact shell commands, file contents, verification checkpoints, and rollback steps

Verification:

- git status in both repos should show clean main branches
- ls /home/pcalnon/Development/python/Juniper/worktrees/ shows only juniper-canopy worktrees (no cascor/data)

Git status: Both juniper-cascor and juniper-data on main, clean working directories. juniper-cascor has one untracked .env file (not relevant).
