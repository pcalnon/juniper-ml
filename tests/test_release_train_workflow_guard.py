#!/usr/bin/env python3
"""Structural R7-privilege-boundary guard for .github/workflows/release-train.yml (plan S9.3 / S12 step 2.2).

The release-train's write identity must open PRs ONLY -- it must never touch environments,
deployments, Releases, or PyPI (plan S9.3, the R7 hard invariant: "A guard test asserts the
workflow contains no environment-mutating API calls"). This lint pins that boundary against drift
by parsing the workflow with PyYAML and asserting:

  (a) workflow-level permissions are exactly {contents: read} -- the report/detect path is read-only;
  (b) the propose job (the sole write lane) has permissions exactly {contents: write,
      pull-requests: write} -- nothing broader (no id-token, no deployments, no environments scope);
  (c) the propose job's ``if`` gates on the detect job's resolved ``mode`` output, so the write scope
      is UNREACHABLE unless mode == 'propose' (it never runs on the report/off path), with no
      always()/!cancelled() escape hatch;
  (d) no job/step references a ``secrets.`` value other than SLACK_WEBHOOK_URL -- the workflow uses
      the built-in ``github.token`` for GitHub auth, never a broad PAT/secret, so a stray privileged
      secret cannot slip in behind the write scope.

Companion to ``tests/test_release_train_propose.py`` (which guards ``propose.py``'s own cross-repo
skip -- the single-repo GITHUB_TOKEN can only open PRs in juniper-ml). Neither ``util/`` nor the
workflow YAML is pre-commit-lint-gated for this property, so this unittest IS the gate.

Portable: locates the repo root by walking up for ``.github/workflows/`` (mirrors
``test_workflow_script_paths.py``) and skips loudly if ``release-train.yml`` is absent.

Run: python3 -m unittest -v tests/test_release_train_workflow_guard.py

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-16
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

WORKFLOW_NAME = "release-train.yml"

# The built-in ``github.token`` is used for GitHub auth everywhere; the ONLY ``secrets.*`` the train
# consumes is the non-blocking Slack webhook (plan S9.4, Q-CHANNEL). A broad PAT/deploy secret slipping
# in behind the propose job's write scope is exactly what R7 forbids.
ALLOWED_SECRETS = frozenset({"SLACK_WEBHOOK_URL"})


def _find_repo_root(start: Path) -> Path:
    """First ancestor of ``start`` containing a ``.github/workflows/`` directory (the repo root)."""
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


class ReleaseTrainWorkflowGuardTest(unittest.TestCase):
    """Pin the R7 privilege boundary of release-train.yml so a refactor cannot silently widen it."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)

    # (a) --------------------------------------------------------------------------------------
    def test_workflow_level_permissions_are_read_only(self):
        self.assertEqual(
            self.doc.get("permissions"),
            {"contents": "read"},
            "workflow-level permissions must be exactly {contents: read} -- the report/detect path is read-only (R7).",
        )

    def test_detect_job_has_no_write_scope(self):
        perms = self.doc["jobs"]["detect"].get("permissions")
        self.assertIn(
            perms,
            (None, {"contents": "read"}),
            f"the detect job must not elevate above the read-only workflow default (got {perms!r}).",
        )

    # (b) --------------------------------------------------------------------------------------
    def test_propose_job_permissions_are_exactly_pr_write(self):
        propose = self.doc["jobs"].get("propose")
        self.assertIsNotNone(propose, "release-train.yml must define the propose job")
        self.assertEqual(
            propose.get("permissions"),
            {"contents": "write", "pull-requests": "write"},
            "propose job permissions must be exactly {contents: write, pull-requests: write} -- no id-token/deployments/environments (R7).",
        )

    def test_propose_needs_detect(self):
        needs = self.doc["jobs"]["propose"].get("needs")
        needs = [needs] if isinstance(needs, str) else (needs or [])
        self.assertIn("detect", needs, "propose must `needs: detect` (it consumes the detection manifest + the mode gate).")

    # (c) --------------------------------------------------------------------------------------
    def test_propose_if_gates_on_resolved_mode(self):
        cond = str(self.doc["jobs"]["propose"].get("if", ""))
        self.assertIn("needs.detect.outputs.mode", cond, "propose `if` must gate on the detect job's resolved mode output (privilege path unreachable in report mode).")
        self.assertIn("propose", cond, "propose `if` must require the resolved mode be 'propose'.")
        # no escape hatch that would run the write-scoped job on a failed / other-mode run.
        self.assertNotIn("always()", cond, "propose `if` must not use always() -- that would run the write job regardless of mode.")
        self.assertNotIn("cancelled()", cond, "propose `if` must not use !cancelled() -- same escape-hatch hazard.")

    # (d) --------------------------------------------------------------------------------------
    def test_only_allowed_secrets_referenced(self):
        referenced = set(re.findall(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)", self.raw))
        extra = referenced - ALLOWED_SECRETS
        self.assertEqual(
            extra,
            set(),
            f"unexpected secrets referenced: {sorted(extra)} -- only {sorted(ALLOWED_SECRETS)} is allowed (use the built-in github.token for GitHub auth, never a broad PAT/deploy secret behind the write scope).",
        )

    # reinforcement: the gate depends on the mode output existing -------------------------------
    def test_detect_job_exposes_mode_output(self):
        outputs = self.doc["jobs"]["detect"].get("outputs") or {}
        self.assertIn("mode", outputs, "the detect job must expose a `mode` output -- the propose gate reads needs.detect.outputs.mode.")


if __name__ == "__main__":
    unittest.main()
