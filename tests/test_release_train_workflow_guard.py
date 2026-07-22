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
  (d) no job/step references a ``secrets.`` value other than SLACK_WEBHOOK_URL and (Phase 4.1) the
      GitHub App private key RELEASE_TRAIN_APP_PRIVATE_KEY -- the workflow otherwise uses the built-in
      ``github.token``, so a stray privileged secret cannot slip in behind the write scope;
  (e) **Phase 4.1 App-identity boundary** -- the cross-repo write identity is fenced: the App
      private-key secret is referenced in EXACTLY ONE place (the ``create-github-app-token`` mint
      step's ``private-key`` input), the mint step + the minted token live ONLY in the propose job
      (never the read-only detect job), the mint step is gated on ``vars.RELEASE_TRAIN_APP_ID`` so an
      absent App config degrades to the built-in ``GITHUB_TOKEN``, and the action is pinned by a full
      commit SHA (fleet convention).

Companion to ``tests/test_release_train_propose.py`` (which guards ``propose.py``'s own capability-gated
cross-repo skip). Neither ``util/`` nor the workflow YAML is pre-commit-lint-gated for this property, so
this unittest IS the gate.

Portable: locates the repo root by walking up for ``.github/workflows/`` (mirrors
``test_workflow_script_paths.py``) and skips loudly if ``release-train.yml`` is absent.

Run: python3 -m unittest -v tests/test_release_train_workflow_guard.py

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-16
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

WORKFLOW_NAME = "release-train.yml"

# The built-in ``github.token`` is used for GitHub auth on the read path; the ``secrets.*`` the train
# consumes are the non-blocking Slack webhook (plan S9.4, Q-CHANNEL) and -- Phase 4.1 -- the GitHub App
# private key that mints the cross-repo write identity (plan S9.2 / S12 step 4.1). Any OTHER secret
# slipping in behind the propose job's write scope is exactly what R7 forbids.
ALLOWED_SECRETS = frozenset({"SLACK_WEBHOOK_URL", "RELEASE_TRAIN_APP_PRIVATE_KEY"})

# Phase 4.1 App-identity anchors (the cross-repo write identity, plan S9.2). These are workflow
# IDENTIFIER names (an action ref + a secret/variable NAME to search for), never credential VALUES --
# nosec B105 silences bandit's hardcoded-password heuristic on the "token"/"KEY"/"SECRET" substrings.
APP_TOKEN_ACTION = "actions/create-github-app-token"  # nosec B105 - action ref, not a credential
APP_PRIVATE_KEY_SECRET = "RELEASE_TRAIN_APP_PRIVATE_KEY"  # nosec B105 - the secret's NAME, not its value
APP_ID_VARIABLE = "RELEASE_TRAIN_APP_ID"


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

    # (e) Phase 4.1: the App cross-repo write identity is fenced to the propose job's mint step ----
    def _propose_steps(self):
        return self.doc["jobs"]["propose"].get("steps") or []

    def _mint_steps(self):
        return [s for s in self._propose_steps() if APP_TOKEN_ACTION in str(s.get("uses", ""))]

    def test_app_token_minted_and_used_in_propose_job_only(self):
        # exactly one mint step, and it is in the propose job
        self.assertEqual(len(self._mint_steps()), 1, "the propose job must mint the App token exactly once")
        # no OTHER job mints or references the App token (the read-only detect path must never see it)
        for job_name, job in self.doc["jobs"].items():
            if job_name == "propose":
                continue
            blob = json.dumps(job)
            self.assertNotIn(APP_TOKEN_ACTION, blob, f"job {job_name!r} must not mint the App token (propose-only)")
            self.assertNotIn("app-token", blob, f"job {job_name!r} must not reference the minted App token (propose-only)")

    def test_app_private_key_secret_only_in_the_mint_step(self):
        # the raw workflow references the App private-key secret EXACTLY once ...
        self.assertEqual(
            self.raw.count(f"secrets.{APP_PRIVATE_KEY_SECRET}"),
            1,
            f"secrets.{APP_PRIVATE_KEY_SECRET} must be referenced exactly once (only in the mint step).",
        )
        # ... and that one reference is the create-github-app-token step's `private-key` input
        stepwise = [s for s in self._propose_steps() if APP_PRIVATE_KEY_SECRET in json.dumps(s)]
        self.assertEqual(len(stepwise), 1, "the App private-key secret must appear in exactly one step")
        self.assertIn(APP_TOKEN_ACTION, str(stepwise[0].get("uses", "")), "the App private-key secret must appear ONLY in the mint step")
        self.assertIn("private-key", stepwise[0].get("with", {}) or {}, "the App private-key secret must be the mint step's private-key input")

    def test_mint_step_gated_on_variable_for_graceful_degradation(self):
        cond = str(self._mint_steps()[0].get("if", ""))
        self.assertIn(
            f"vars.{APP_ID_VARIABLE}",
            cond,
            "the mint step must be gated on vars.RELEASE_TRAIN_APP_ID so an absent App config degrades to the built-in GITHUB_TOKEN (in-repo only).",
        )

    def test_app_token_action_pinned_by_full_sha(self):
        uses = str(self._mint_steps()[0].get("uses", ""))
        self.assertIsNotNone(
            re.match(rf"^{re.escape(APP_TOKEN_ACTION)}@[0-9a-f]{{40}}(\s|$)", uses + " "),
            f"create-github-app-token must be pinned by a full 40-hex commit SHA (fleet convention); got {uses!r}.",
        )

    # reinforcement: the gate depends on the mode output existing -------------------------------
    def test_detect_job_exposes_mode_output(self):
        outputs = self.doc["jobs"]["detect"].get("outputs") or {}
        self.assertIn("mode", outputs, "the detect job must expose a `mode` output -- the propose gate reads needs.detect.outputs.mode.")


if __name__ == "__main__":
    unittest.main()
