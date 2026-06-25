# publish juniper packages to pypi

Execute the Juniper PyPI publish plan from /home/pcalnon/.claude/plans/silly-foraging-petal.md

Completed so far:

- Full exploration of all 6 Juniper repos' CI/CD, packaging, and publish workflows
- Identified all blockers and current PyPI/TestPyPI publish status
- User approved plan with these decisions:
  - juniper-cascor: Add juniper_cascor/ wrapper package (NOT full restructure)
  - Wait period: Keep current setup (5-min timer + manual approval on pypi environment)
  - Proceed with repos that are ready; flag juniper-data-client as manual fix

Remaining work:

1. juniper-cascor: Create worktree, add juniper_cascor/__init__.py wrapper at repo root
   with __version__ = "0.3.17", add [tool.setuptools.packages.find] to pyproject.toml
   with where = [".", "src"], verify build locally, commit, push, create release v0.3.17
2. juniper-data: Create worktree, pin action SHA hashes in .github/workflows/publish.yml
   (checkout@v4 → pinned SHA, setup-python@v5 → pinned SHA, gh-action-pypi-publish@release/v1 → pinned SHA),
   commit, push, create release v0.4.2
3. Create GitHub releases via `gh release create` for both repos
4. Monitor publish workflow runs
5. Document juniper-data-client TestPyPI 403 fix (manual: reconfigure trusted publisher at test.pypi.org)

Key context:

- All repos use OIDC trusted publishing (no API tokens)
- juniper-cascor-client (v0.1.0), juniper-cascor-worker (v0.1.0), juniper-ml (v0.1.0) are ALREADY on PyPI — no action needed
- juniper-data-client v0.3.1 is BLOCKED by TestPyPI 403 — needs manual trusted publisher fix
- All repos already have publish.yml workflows triggered by release events
- All repos have pypi environment with 5-min wait timer + required_reviewers (pcalnon)
- juniper-cascor uses src/ layout with packages like cascade_correlation/, candidate_unit/ etc.
- juniper-cascor pyproject.toml has license = { text = "MIT" } (old format, still valid)
- juniper-data pyproject.toml has license = { text = "MIT" } (old format, still valid)
- Pinned SHA hashes for actions: checkout@11bd71901bbe5b1630ceea73d27597364c9af683 (v4.2.2),
  setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 (v5.6.0),
  pypa/gh-action-pypi-publish@ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e (v1.13.0)
- Worktrees go in /home/pcalnon/Development/python/Juniper/worktrees/
- Plan file: /home/pcalnon/.claude/plans/silly-foraging-petal.md

Verification:

- git status in each repo before creating worktrees
- python -m build && twine check dist/* after packaging changes
- gh run list --workflow=publish.yml after creating releases
- pip install from TestPyPI after workflow completes

Git status: All repos on main branch, clean working directories

---
