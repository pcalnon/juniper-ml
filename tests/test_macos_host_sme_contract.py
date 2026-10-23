"""Static contract test for the ``macos-host-sme`` subagent (turing bring-up task H2).

Project:     Juniper
Sub-Project: juniper-ml
Application: custom-agent suite regression tests
Author:      Paul Calnon
License:     MIT License

``.claude/agents/macos-host-sme.md`` measures a macOS host against ``conf/hosts/<host>/expected.yaml``
with ``util/host_state_check.py --json`` and explains each failing gate condition (plan §11 of
``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md``). Pinned here, without a
live model, on the pattern of ``tests/test_fleet_supervisor_contract.py``:

- the frontmatter, and the exact tool set {Read, Grep, Glob, Bash, Write};
- each Must-never item of plan §11 (``sudo``; reading ``~/.ssh/**`` or ``~/.gnupg/**``;
  ``defaults write``; changing settings) plus D11's credential probes, each in the ``## Must never``
  section and each denied by ``util/claude_agent_guard.py`` under the rule the section cites;
- that every command the procedure prescribes passes the guard;
- the wiring to the real check: its flags, the seven gates it evaluates and the three it leaves to
  others (read from ``util/host_state_check.py`` itself), the files it reads, and the one ``reports/``
  file the agent writes.

``.claude/**`` is excluded from every pre-commit hook except markdownlint, so this unittest, wired into
``.github/workflows/ci.yml``, is the gate. The shared checks live in ``tests/agent_contract_support.py``.
"""

from __future__ import annotations

import ast
import unittest

from tests.agent_contract_support import REPO_ROOT, ContractMixin


def _check_constants() -> dict:
    """The literal module-level constants of util/host_state_check.py, read without importing it."""
    tree = ast.parse((REPO_ROOT / "util" / "host_state_check.py").read_text(encoding="utf-8"))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                continue
    return constants


class MacosHostSmeContractTest(ContractMixin, unittest.TestCase):
    """`.claude/agents/macos-host-sme.md` against plan §11 and the C8 guard."""

    AGENT = "macos-host-sme"
    TOOLS = frozenset({"Read", "Grep", "Glob", "Bash", "Write"})
    MUST_NEVER = (
        ("`sudo`", (("Bash", {"command": "sudo pmset -a standby 0"}, "PRIV-ESCALATION"),)),
        (
            "`~/.ssh/**`",
            (
                ("Read", {"file_path": "@HOME@/.ssh/config"}, "CRED-PATH-FILE"),
                ("Bash", {"command": "cat ~/.ssh/config"}, "CRED-PATH-BASH"),
                ("Grep", {"pattern": "Host", "path": "@HOME@/.ssh"}, "CRED-PATH-SEARCH"),
            ),
        ),
        (
            "`~/.gnupg/**`",
            (
                ("Read", {"file_path": "@HOME@/.gnupg/gpg-agent.conf"}, "CRED-PATH-FILE"),
                ("Bash", {"command": "ls -la ~/.gnupg"}, "CRED-PATH-BASH"),
                ("Glob", {"pattern": "*.conf", "path": "@HOME@/.gnupg"}, "CRED-PATH-SEARCH"),
            ),
        ),
        ("`defaults write`", (("Bash", {"command": "defaults write com.apple.alf globalstate -int 1"}, "MACOS-DEFAULTS-WRITE"),)),
        (
            "change settings",
            (
                ("Bash", {"command": "sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on"}, "PRIV-ESCALATION"),
                ("Bash", {"command": "git config --global commit.gpgsign true"}, "GIT-SIGNING-CONFIG"),
                ("Bash", {"command": "python3 util/configure_commit_signing.py --apply"}, "GIT-SIGNING-CONFIG"),
            ),
        ),
        (
            "run a credential probe",
            (
                ("Bash", {"command": "ssh -T git@github.com"}, "SSH-PROBE"),
                ("Bash", {"command": "ssh-add -l"}, "SSH-PROBE"),
                ("Bash", {"command": "gpg --card-status"}, "GPG-SECRET"),
                ("Bash", {"command": "gpg -K"}, "GPG-SECRET"),
                ("Bash", {"command": "gh auth status"}, "GH-AUTH"),
            ),
        ),
    )
    ALLOWED = (
        ("Bash", {"command": "python3 util/host_state_check.py --json"}),
        ("Bash", {"command": "python3 util/host_state_check.py --section G-MEM --json"}),
        ("Bash", {"command": "bash util/host_state_probe.bash --json --section memory"}),
        ("Bash", {"command": "vm_stat"}),
        ("Bash", {"command": "sysctl vm.swapusage"}),
        ("Bash", {"command": "ifconfig en7"}),
        ("Bash", {"command": "git rev-parse HEAD"}),
        ("Read", {"file_path": "@REPO@/conf/hosts/turing/expected.yaml"}),
        ("Write", {"file_path": "@REPO@/reports/2026-10-20_turing-bringup/2026-10-20T1800Z_macos-host-sme.md", "content": "x"}),
    )

    def test_description_is_on_topic(self):
        desc = self.front.get("description", "")
        for token in ("expected.yaml", "util/host_state_check.py", "reports/", "Read-only"):
            with self.subTest(token=token):
                self.assertIn(token, desc)

    def test_the_check_and_its_inputs_exist(self):
        for rel in ("util/host_state_check.py", "util/host_state_probe.bash", "conf/hosts/turing/expected.yaml"):
            with self.subTest(path=rel):
                self.assertTrue((REPO_ROOT / rel).is_file(), "the agent is wired to %s" % rel)

    def test_body_names_every_gate_the_check_reports(self):
        constants = _check_constants()
        gates = list(constants["GATES"]) + [gate for gate, _ in constants["NOT_EVALUATED"]]
        self.assertEqual(len(gates), 10, "plan §9.3 has ten host gates")
        missing = [gate for gate in gates if gate not in self.body]
        self.assertEqual(missing, [], "the body names the seven evaluated gates and the three left to others")

    def test_body_reads_the_checks_json_fields(self):
        for field in ("readiness", "probe.collected_at", "conditions", "remediation", "not_evaluated"):
            with self.subTest(field=field):
                self.assertIn("`%s`" % field, self.body)

    def test_body_keeps_the_check_as_the_judge(self):
        self.assertIn("You do not re-judge a gate", self.body)
        self.assertIn("keep the check's verdict", self.body)

    def test_body_writes_one_reports_file_and_never_overwrites(self):
        output = self.body.split("## Output", 1)[-1]
        self.assertIn("Write exactly one file: `reports/<YYYY-MM-DD>_<host>-bringup/<YYYY-MM-DDTHHMMZ>_macos-host-sme.md`", output)
        self.assertIn("never overwrite", output)
        self.assertIn("±10 minutes", output, "the probe timestamp lets H3 match an independent probe run")


if __name__ == "__main__":
    unittest.main()
