"""Static lint for the service-smoke Skill (custom-agent suite E-1 Stage 1).

The Skill (``.claude/skills/service-smoke/SKILL.md``) is an HTTP-only runtime
diagnostician: it boots a Juniper service in its conda env, probes ``/v1/health``,
tails the boot log, and reports a live traceback as ``file:line`` (the "green
tests / dead app" catch). Its live behaviour needs conda + the real service and so
cannot run in ubuntu CI -- correctness of the live path is covered by a documented
manual smoke-verify, not by CI.

This unittest is the *structural* gate for the Skill surface:
  * frontmatter shape -- the suite's ``opus`` + ``max`` defaults, user-only
    invocation, and the Stage-1 HTTP-only tool set ``{Read, Grep, Glob, Bash}``;
  * the **Stage-1 boundary** -- the frontmatter must NOT grant a browser MCP
    (``playwright`` / ``chrome-devtools``) or ``Agent`` delegation (those belong to
    Stage 2 / other suite units) -- the assertion that makes this lint Stage-1-shaped;
  * wiring to the real teardown utilities (each referenced path exists on disk);
  * an explicit teardown step encoding the spike's two gotchas (SIGTERM->SIGKILL
    escalation, poll-to-down, finally-style reap);
  * named terminal states and bounded behaviour (no unbounded wait-until-ready).

``.claude/**`` is git-tracked via the PR-1 ``.gitignore`` negation but excluded from
every pre-commit hook except markdownlint, so this unittest -- wired into ``ci.yml``
-- is the gate.

Design-of-record: ``notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md`` (S6.9).
Spike record: ``notes/JUNIPER_ML_E1-SERVICE-SMOKE_STAGE0-SPIKE_2026-06-29.md``.
Location-agnostic: discovers the repo root by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

# The Stage-1 HTTP-only tool grant the Skill must pre-approve.
_REQUIRED_TOOLS = {"Read", "Grep", "Glob", "Bash"}
# Tools whose presence in allowed-tools would break the Stage-1 boundary: a browser
# MCP (playwright / chrome-devtools) is Stage 2; Agent delegation is not Stage 1's job.
_FORBIDDEN_TOOLS = {"Agent", "playwright", "chrome-devtools"}
# Browser-MCP tokens that must not appear anywhere in the frontmatter block.
_FORBIDDEN_FRONTMATTER_TOKENS = ("playwright", "chrome-devtools")

# Teardown utilities the Skill must wire to by literal path -- each must appear in
# the body AND exist on disk (no dangling wiring). Reused, never reinvented.
_REFERENCED_PATHS = [
    "util/reap_pytest_orphans.bash",
    "util/kill_all_pythons.bash",
]
_TERMINAL_STATES = ("HEALTHY", "UNHEALTHY_REPORTED", "BOOT_FAILED", "TEARDOWN_ESCALATED")


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


def _split_frontmatter(text: str):
    """Return (front_dict, front_raw, body). front_raw is the YAML text between the
    first two ``---`` fences so the Stage-1 boundary can be checked on the frontmatter
    alone (the body legitimately names the Stage-2 browser MCPs)."""
    if not text.startswith("---"):
        return None, "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "", text
    front = yaml.safe_load(parts[1])
    return (front if isinstance(front, dict) else None), parts[1], parts[2]


def _as_tool_set(value):
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    return {tok.strip() for tok in re.split(r"[,\s]+", str(value)) if tok.strip()}


class ServiceSmokeSkillLintTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.skill_path = cls.repo_root / ".claude" / "skills" / "service-smoke" / "SKILL.md"
        cls.text = cls.skill_path.read_text(encoding="utf-8") if cls.skill_path.exists() else None
        cls.front, cls.front_raw, cls.body = _split_frontmatter(cls.text) if cls.text else (None, "", "")

    def setUp(self):
        if self.text is None:
            self.skipTest(f"service-smoke Skill absent at {self.skill_path}")

    def test_skill_file_exists(self):
        self.assertTrue(self.skill_path.exists(), f"missing Skill at {self.skill_path}")

    def test_frontmatter_parses(self):
        self.assertIsNotNone(self.front, "SKILL.md has no parseable YAML frontmatter")

    def test_name_matches_filename_stem(self):
        self.assertEqual(self.front.get("name"), "service-smoke", "name must equal the Skill dir/file stem")

    def test_description_substantive(self):
        desc = self.front.get("description", "")
        self.assertIsInstance(desc, str)
        self.assertGreaterEqual(len(desc), 60, "description should describe what it boots/probes and that it is HTTP-only")

    def test_argument_hint_present(self):
        self.assertTrue(str(self.front.get("argument-hint", "")).strip(), "argument-hint should be set")

    def test_allowed_tools_include_required(self):
        tools = _as_tool_set(self.front.get("allowed-tools"))
        missing = sorted(_REQUIRED_TOOLS - tools)
        self.assertEqual(missing, [], f"allowed-tools missing the Stage-1 HTTP set {missing}")

    def test_stage1_boundary_no_browser_or_agent(self):
        """Stage 1 is HTTP-only: the frontmatter must NOT grant a browser MCP
        (playwright / chrome-devtools -- Stage 2) or Agent delegation. The body may
        legitimately name those as Stage-2 work, so this checks the frontmatter only."""
        tools = _as_tool_set(self.front.get("allowed-tools"))
        granted_forbidden = sorted(t for t in tools if t in _FORBIDDEN_TOOLS or t.startswith("mcp__playwright") or t.startswith("mcp__chrome-devtools"))
        self.assertEqual(granted_forbidden, [], f"Stage-1 Skill must not grant {granted_forbidden} (browser MCP / Agent are Stage 2)")
        low = self.front_raw.lower()
        for token in _FORBIDDEN_FRONTMATTER_TOKENS:
            self.assertNotIn(token, low, f"frontmatter must not reference the browser MCP '{token}' (Stage 2)")

    def test_model_pinned_to_opus(self):
        base = str(self.front.get("model", "")).split(":")[0].strip().lower()
        self.assertTrue(base == "opus" or base.startswith("claude-opus"), f"suite default model is Opus; got {self.front.get('model')!r}")

    def test_effort_is_max(self):
        self.assertEqual(str(self.front.get("effort", "")).strip().lower(), "max", "suite default effort is 'max'")

    def test_user_only_invocation(self):
        self.assertIs(self.front.get("disable-model-invocation"), True, "Skill is user-only (it manages live processes)")

    def test_referenced_paths_exist(self):
        for rel in _REFERENCED_PATHS:
            self.assertIn(rel, self.body, f"SKILL.md should reference {rel}")
            self.assertTrue((self.repo_root / rel).exists(), f"SKILL.md references {rel} but it does not exist on disk")

    def test_probes_health_endpoint(self):
        self.assertIn("/v1/health", self.body, "Skill must probe the /v1/health endpoint")

    def test_explicit_teardown_step(self):
        """The spike's carry-forward makes teardown mandatory: a SIGTERM->SIGKILL
        escalation, poll-to-down (not assert-down-immediately), and a finally-style reap."""
        self.assertIn("SIGTERM", self.body, "teardown must escalate from SIGTERM")
        self.assertIn("SIGKILL", self.body, "teardown must escalate to SIGKILL after the timeout")
        self.assertRegex(self.body, r"finally", "teardown must run in a finally-style path")
        self.assertRegex(self.body, r"poll-to-down|poll for connection", "teardown must poll-to-down, not assert down immediately")

    def test_bounded_behaviour_documented(self):
        low = self.body.lower()
        self.assertIn("bounded", low, "Skill must document bounded waits")
        self.assertIn("timeout", low, "Skill must document a bounded timeout (no unbounded wait-until-ready)")

    def test_terminal_states_documented(self):
        for state in _TERMINAL_STATES:
            self.assertIn(state, self.body, f"Skill must document terminal state {state}")

    def test_stage_boundary_documented(self):
        self.assertIn("Stage 2", self.body, "Skill must mark the browser/UI smoke as Stage 2")
        self.assertIn("HTTP-only", self.body, "Skill must state it is HTTP-only (Stage 1)")


if __name__ == "__main__":
    unittest.main()
