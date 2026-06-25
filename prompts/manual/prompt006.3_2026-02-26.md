# Handoff Goal

## Publish the following 4 Juniper packages to TestPyPI and PyPI

- juniper-ml
- juniper-data-client
- juniper-cascor-worker (if applicable — check ecosystem)
- juniper-canopy (note: not listed as an active repo in parent CLAUDE.md — may be part of juniper-deploy)
- juniper-deploy

## Correction from user's request: The 4 packages to publish are

- juniper-ml
- juniper-data-client
- juniper-canopy
- juniper-deploy

## Completed So Far (This Session)

1. Wrote notes/PYPI_PUBLISH_PROCEDURE.md — comprehensive runbook covering the full publish lifecycle
2. Published juniper-cascor v0.3.17 to PyPI (Part A complete):
    - Created juniper_cascor/__init__.py wrapper package at repo root with __version__ = "0.3.17"
    - Added [tool.setuptools.packages.find] with where = [".", "src"], exclude = ["tests*", "backups*"] to pyproject.toml
    - Branch chore/pypi-publish-packaging merged to main, worktree cleaned up
    - GitHub release v0.3.17 created, both TestPyPI and PyPI jobs passed
    - Verified: pip install juniper-cascor==0.3.17 + import works
3. Published juniper-data v0.4.2 to PyPI (Part B complete):
    - Pinned 6 GitHub Action refs to SHA hashes in .github/workflows/publish.yml
    - Branch chore/pin-publish-action-shas merged to main (fast-forward), worktree cleaned up
    - GitHub release v0.4.2 created, both TestPyPI and PyPI jobs passed
    - Verified: pip install juniper-data==0.4.2 + import works

## Remaining Work

### For each of the 4 packages above

1. Read the repo's AGENTS.md and explore its packaging state (pyproject.toml, __init__.py, .github/workflows/publish.yml)
2. Determine what code changes are needed (if any) — check for:
    - Does publish.yml exist? Are actions SHA-pinned?
    - Does pyproject.toml have correct [tool.setuptools.packages.find]?
    - Does the package expose __version__ for import verification?
    - Are PyPI/TestPyPI trusted publishers configured?
3. Create worktree, make changes, test, commit, push, merge (per procedure)
4. Create GitHub release to trigger publish workflow
5. Approve TestPyPI and PyPI environment gates
6. Verify post-publish install

### Key Context

- juniper-data-client has a known issue: v0.3.1 TestPyPI publish failed with 403 (trusted publisher mismatch). See Appendix A of notes/PYPI_PUBLISH_PROCEDURE.md for the fix. Its publish.yml already has SHA-pinned actions.
- SHA hashes for action pinning (reference): actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 (v4.2.2), actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 (v5.6.0), pypa/gh-action-pypi-publish@ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e (v1.13.0)
- Worktree procedures: Each repo has notes/WORKTREE_SETUP_PROCEDURE.md and notes/WORKTREE_CLEANUP_PROCEDURE.md
- Conda env: conda activate JuniperPython
- Procedure doc: notes/PYPI_PUBLISH_PROCEDURE.md has the full pattern to follow

## Verification Commands

### Confirm prior publishes are live

pip install juniper-cascor==0.3.17 && python -c "from juniper_cascor import __version__; print(__version__)"
pip install juniper-data==0.4.2 && python -c "import juniper_data; print(juniper_data.__version__)"

### Check repo states

cd /home/pcalnon/Development/python/Juniper/juniper-ml && git status && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-data-client && git status && git log --oneline -1
cd /home/pcalnon/Development/python/Juniper/juniper-deploy && git status && git log --oneline -1

## Git Status

- juniper-cascor: main branch, clean, up to date with remote. HEAD = ca20865
- juniper-data: main branch, clean, up to date with remote. HEAD = 1968dd3
- juniper-cascor has an active worktree: feature/7.3-api-security (unrelated, pre-existing)

---
