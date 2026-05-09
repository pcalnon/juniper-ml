# juniper-cascor bug description

1. cascor-worker pip-audit was NOT a self-pkg issue — it's a real chain: torch hard-pins setuptools<82 and torch's wheel index (download.pytorch.org/whl/cpu) ships setuptools-70.2.0, which has PYSEC-2025-49.
    - Any Juniper repo that installs torch from PyTorch's CPU wheel index for security scanning will hit this exact issue.
    - The fix pattern (filter ^setuptools== from freeze, then pin setuptools>=78.1.1) is reusable.
2. pip freeze | grep does not robustly catch PEP 660 editable self-installs. pip list --format=freeze --exclude PKGNAME is the canonical-name-aware alternative.
3. Latent risks not yet failing CI (out of scope for this task, but worth flagging):
    - juniper-data-client/.github/workflows/ci.yml has the same plain pip install bandit pip-audit bug (line 320). Will fail next time it runs.
    - juniper-cascor-worker/.github/workflows/ci.yml Documentation Links job lacks --cross-repo skip (line 116). Currently passing because no broken cross-repo links exist in the repo's docs yet.

---
