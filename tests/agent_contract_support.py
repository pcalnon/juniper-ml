"""Shared support for the contract suites of the turing SME agents (bring-up task H2).

Project:     Juniper
Sub-Project: juniper-ml
Application: custom-agent suite regression tests
Author:      Paul Calnon
License:     MIT License

Plan §11 of ``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` gives each SME
agent a list of things it must never do, "enforced by D11's deny list, pinned by the contract test". A
contract suite therefore checks each item twice: the item is written in the agent's ``## Must never``
section, and ``util/claude_agent_guard.py`` (task C8, the PreToolUse hook that carries D11 item 4) denies
a representative call under the rule that section cites. A rule is cited as ``(guard: `RULE-ID`, ...)``.
The suites also check the other direction: every call the agent's procedure tells it to make must pass
the guard, or the agent would be denied on its first step once C8 is installed.

``ContractMixin`` holds the checks every SME agent shares. A suite combines it with
``unittest.TestCase`` and sets the class attributes it documents; the mixin is not a ``TestCase``
itself, so importing it adds no tests to a module.

The guard runs as a subprocess, fed a PreToolUse payload the way ``tests/test_claude_agent_guard.py``
feeds it, with ``JUNIPER_GUARD_HOME`` and ``HOME`` pointing at a temporary home that has its own
``.ssh``, ``.gnupg`` and ``.claude``. The real home is never read. ``@HOME@`` and ``@REPO@`` in a
tool input stand for that home and for a repository inside it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess  # nosec B404 - runs the guard as a subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
GUARD = REPO_ROOT / "util" / "claude_agent_guard.py"
PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
TIMEOUT_SECONDS = 60
MUTATING_TOOLS = {"Edit", "MultiEdit", "NotebookEdit"}

_CITED = re.compile(r"\(guard: ([^)]*)\)")
_RULE_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")


def split_frontmatter(text: str):
    """Return ``(frontmatter_dict_or_None, body_text)`` for a ``---``-fenced markdown file."""
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    front = yaml.safe_load(parts[1])
    return (front if isinstance(front, dict) else None), parts[2]


def as_tool_set(value) -> set:
    """Frontmatter ``tools`` may be a comma/space-separated string or a YAML list."""
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    return {tok.strip() for tok in re.split(r"[,\s]+", str(value)) if tok.strip()}


def section(body: str, heading: str) -> str:
    """The text under ``## <heading>``, up to the next ``## `` heading; empty when absent."""
    match = re.search(r"^## %s[ \t]*$(.*?)(?=^## |\Z)" % re.escape(heading), body, flags=re.M | re.S)
    return match.group(1) if match else ""


def bullets(text: str) -> list:
    """The top-level ``- `` bullets of a markdown section, each with its indented continuation lines."""
    items = []
    for line in text.splitlines():
        if line.startswith("- "):
            items.append(line)
        elif items and line.startswith(" ") and line.strip():
            items[-1] += "\n" + line
    return items


def bold_spans(text: str) -> list:
    """The ``**bold**`` spans of a markdown text. A ``**`` inside a code span (``~/.ssh/**``) is literal."""
    spans: list = []
    start = None
    in_code = False
    i = 0
    while i < len(text):
        if text[i] == "`":
            in_code = not in_code
        elif not in_code and text.startswith("**", i):
            if start is None:
                start = i + 2
            else:
                spans.append(text[start:i])
                start = None
            i += 2
            continue
        i += 1
    return spans


def cited_rules(text: str) -> list:
    """Every rule id inside a ``(guard: ...)`` group, in order, backticks stripped."""
    rules: list = []
    for group in _CITED.findall(text):
        rules.extend(tok.strip().strip("`") for tok in group.split(",") if tok.strip())
    return rules


def guard_rule_ids() -> set:
    """The rule ids in the guard's own table, as ``--list-rules`` prints them."""
    proc = subprocess.run([sys.executable, "-I", str(GUARD), "--list-rules"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=True)  # nosec B603 - fixed argv
    return {line.split()[0] for line in proc.stdout.splitlines() if line.strip()}


def rules_named(reason: str) -> list:
    """The primary rule id of a deny reason, then any listed under 'Also matched'."""
    primary = re.search(r"Rule ([A-Z0-9-]+):", reason)
    also = re.search(r"Also matched: ([A-Z0-9, -]+)\.", reason)
    return ([primary.group(1)] if primary else []) + ([r.strip() for r in also.group(1).split(",")] if also else [])


class GuardHome(object):
    """A temporary home with ``.ssh``, ``.gnupg`` and ``.claude``, and a repository inside it."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="sme-agent-contract-")
        self.home = Path(self._tmp.name) / "home"
        self.repo = self.home / "Development" / "repo"
        for rel in (".ssh/config", ".gnupg/gpg-agent.conf", ".claude/settings.json", "Development/repo/README.md"):
            path = self.home / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x\n", encoding="utf-8")
        (self.repo / ".git" / "hooks").mkdir(parents=True)

    def cleanup(self) -> None:
        self._tmp.cleanup()

    def sub(self, value):
        if isinstance(value, str):
            return value.replace("@HOME@", str(self.home)).replace("@REPO@", str(self.repo))
        if isinstance(value, dict):
            return {k: self.sub(v) for k, v in value.items()}
        return value

    def decide(self, tool: str, tool_input: dict) -> list:
        """The rule ids the guard denies this call under; an empty list means it passed."""
        payload = {
            "session_id": "sme-agent-contract",
            "transcript_path": "/dev/null",
            "hook_event_name": "PreToolUse",
            "permission_mode": "bypassPermissions",
            "tool_name": tool,
            "tool_input": self.sub(tool_input),
            "cwd": str(self.repo),
            "tool_use_id": "toolu_contract",
        }
        env = RedactedEnv(os.environ)
        env["JUNIPER_GUARD_HOME"] = str(self.home)
        env["HOME"] = str(self.home)
        proc = subprocess.run(  # nosec B603 - fixed argv, temp home
            [sys.executable, "-I", str(GUARD)],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            env=env,
            cwd=str(self.repo),
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
        out = proc.stdout.decode("utf-8").strip()
        if proc.returncode != 0:
            raise AssertionError("guard exited %d on %s %r: %s" % (proc.returncode, tool, tool_input, proc.stderr.decode("utf-8")))
        if not out:
            return []
        return rules_named(json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"])


class ContractMixin(object):
    """The checks every SME agent shares. Combine with ``unittest.TestCase`` and set:

    ``AGENT``       the agent's name, which is also its file stem under ``.claude/agents/``;
    ``TOOLS``       its exact tool set (plan §11's Tools column);
    ``MUST_NEVER``  ``(item, ((tool, tool_input, rule_id), ...))`` pairs: the item is text (matched
                    without regard to case) that a bold span of a ``## Must never`` bullet must contain,
                    so a passing mention elsewhere does not count. Each call must be denied under its
                    rule, which that bullet must cite. An item with no calls is held by the prompt or
                    the tool set alone;
    ``ALLOWED``     ``(tool, tool_input)`` calls from the agent's procedure, which the guard must pass.
    """

    AGENT: str = ""
    TOOLS: frozenset = frozenset()
    MUST_NEVER: tuple = ()
    ALLOWED: tuple = ()

    agent_path: Path
    front: dict
    body: str
    must_never: str
    guard_home: GuardHome

    @classmethod
    def setUpClass(cls):
        cls.agent_path = AGENTS_DIR / ("%s.md" % cls.AGENT)
        text = cls.agent_path.read_text(encoding="utf-8") if cls.agent_path.exists() else None
        cls.front, cls.body = split_frontmatter(text) if text else (None, "")
        cls.must_never = section(cls.body, "Must never")
        cls.guard_home = GuardHome()

    @classmethod
    def tearDownClass(cls):
        cls.guard_home.cleanup()

    def test_agent_file_exists(self):
        self.assertTrue(self.agent_path.exists(), "missing %s subagent at %s" % (self.AGENT, self.agent_path))

    def test_frontmatter_shape(self):
        self.assertIsNotNone(self.front, "no parseable YAML frontmatter between '---' fences")
        self.assertEqual(self.front.get("name"), self.AGENT, "name must equal the filename stem")
        self.assertGreaterEqual(len(self.front.get("description", "")), 60, "the description says when to delegate")
        self.assertEqual(str(self.front.get("model", "")).strip().lower(), "opus", "suite default model (owner directive)")
        self.assertEqual(str(self.front.get("effort", "")).strip().lower(), "max", "suite default effort (owner directive)")

    def test_tools_are_exactly_the_plan_set(self):
        tools = as_tool_set(self.front.get("tools") if self.front else None)
        self.assertEqual(tools, set(self.TOOLS), "plan §11 pins the tool set")
        self.assertEqual(tools & MUTATING_TOOLS, set(), "an SME agent writes one new file with Write and edits nothing")

    def bullet_for(self, item: str) -> str:
        """The first ``## Must never`` bullet whose bold text contains ``item``, ignoring case; empty when none does."""
        return next((b for b in bullets(self.must_never) if any(item.lower() in span.lower() for span in bold_spans(b))), "")

    def test_must_never_section_lists_every_item(self):
        self.assertTrue(self.must_never.strip(), "the body needs a '## Must never' section")
        missing = [item for item, _ in self.MUST_NEVER if not self.bullet_for(item)]
        self.assertEqual(missing, [], "plan §11's Must-never items belong in the '## Must never' section's bullets")

    def test_cited_rules_exist_in_the_guard(self):
        cited = cited_rules(self.must_never)
        self.assertTrue(cited, "the section cites the guard rule behind each enforced item as (guard: `RULE-ID`)")
        malformed = [r for r in cited if not _RULE_ID.match(r)]
        self.assertEqual(malformed, [], "a (guard: ...) group holds rule ids only")
        unknown = sorted(set(cited) - guard_rule_ids())
        self.assertEqual(unknown, [], "every cited rule must exist in util/claude_agent_guard.py --list-rules")

    def test_guard_denies_each_item_under_the_cited_rule(self):
        for item, calls in self.MUST_NEVER:
            cited = set(cited_rules(self.bullet_for(item)))
            for tool, tool_input, rule_id in calls:
                with self.subTest(item=item, tool=tool, tool_input=tool_input):
                    self.assertIn(rule_id, cited, "the bullet for %r must cite %s, the rule that enforces it" % (item, rule_id))
                    self.assertIn(rule_id, self.guard_home.decide(tool, tool_input), "the guard must deny this under %s" % rule_id)

    def test_guard_passes_the_procedure(self):
        for tool, tool_input in self.ALLOWED:
            with self.subTest(tool=tool, tool_input=tool_input):
                self.assertEqual(self.guard_home.decide(tool, tool_input), [], "the agent's own procedure must pass the guard")

    def test_procedure_commands_appear_in_the_body(self):
        for tool, tool_input in self.ALLOWED:
            command = tool_input.get("command") if tool == "Bash" else None
            if command:
                with self.subTest(command=command):
                    self.assertIn(command, self.body, "an ALLOWED Bash call must be one the body prescribes")

    def test_body_says_a_denial_is_recorded_not_retried(self):
        low = self.body.lower()
        self.assertTrue("when the guard denies a call" in low, "the body says what to do when the guard denies a call")
        self.assertTrue("never retry" in low, "a denied call is recorded for the owner, never respelled and retried")

    def test_body_names_the_plan_of_record(self):
        self.assertIn(PLAN, self.body, "the body cites the bring-up plan by filename")
