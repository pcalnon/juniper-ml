"""Static contract test for the ``signing-auth-sme`` subagent (turing bring-up task H2).

Project:     Juniper
Sub-Project: juniper-ml
Application: custom-agent suite regression tests
Author:      Paul Calnon
License:     MIT License

``.claude/agents/signing-auth-sme.md`` diagnoses git transport and commit signing from configuration,
file modes and read-only ``gh api`` GETs, and emits the OWNER command list for every check an agent may
not run (plan §11 of ``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md``).
Pinned here, without a live model, on the pattern of ``tests/test_fleet_supervisor_contract.py``:

- the frontmatter, and the exact tool set {Read, Grep, Glob, Bash, Write};
- each Must-never item of plan §11 (``gpg --card-status``, ``gpg -K``, ``ssh-add``, ``ssh -T``;
  PIN-bearing commands; ``gh api`` with ``-X`` / ``-f`` / ``--method``; any ``gh`` write) plus the
  credential paths, the signing configuration and the keychain, each in the ``## Must never`` section
  and each denied by ``util/claude_agent_guard.py`` under the rule the section cites;
- that every command the procedure prescribes passes the guard, the read-only ``gh api`` GETs and
  ``ssh -G`` among them;
- the wiring to the repo's non-credential checkers, the two plans of record, and the one ``reports/``
  file the agent writes, which ends with the OWNER command list.

``.claude/**`` is excluded from every pre-commit hook except markdownlint, so this unittest, wired into
``.github/workflows/ci.yml``, is the gate. The shared checks live in ``tests/agent_contract_support.py``.
"""

from __future__ import annotations

import unittest

from tests.agent_contract_support import REPO_ROOT, ContractMixin

SIGNING_PLAN = "notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md"


class SigningAuthSmeContractTest(ContractMixin, unittest.TestCase):
    """`.claude/agents/signing-auth-sme.md` against plan §11 and the C8 guard."""

    AGENT = "signing-auth-sme"
    TOOLS = frozenset({"Read", "Grep", "Glob", "Bash", "Write"})
    MUST_NEVER = (
        ("`gpg --card-status`", (("Bash", {"command": "gpg --card-status"}, "GPG-SECRET"),)),
        ("`gpg -K`", (("Bash", {"command": "gpg -K --with-keygrip"}, "GPG-SECRET"), ("Bash", {"command": "ykman openpgp info"}, "GPG-SECRET"))),
        ("`ssh-add`", (("Bash", {"command": "ssh-add -l"}, "SSH-PROBE"),)),
        ("`ssh -T`", (("Bash", {"command": "ssh -o BatchMode=yes -T github_juniper-k8s"}, "SSH-PROBE"),)),
        (
            "PIN-bearing commands",
            (
                ("Bash", {"command": "echo t | gpg --clearsign"}, "GPG-SIGN"),
                ("Bash", {"command": "git commit -S -m probe"}, "GPG-SIGN"),
                ("Bash", {"command": "git tag -s v0 -m probe"}, "GPG-SIGN"),
            ),
        ),
        (
            "`gh api` with `-X` / `-f` / `--method`",
            (
                ("Bash", {"command": "gh api -X POST repos/pcalnon/juniper-ml/issues"}, "GH-API-WRITE"),
                ("Bash", {"command": "gh api repos/pcalnon/juniper-ml/issues -f title=probe"}, "GH-API-WRITE"),
                ("Bash", {"command": "gh api --method PUT repos/pcalnon/juniper-ml/rulesets/1"}, "GH-API-WRITE"),
            ),
        ),
        (
            "any `gh` write",
            (
                ("Bash", {"command": "gh pr create --fill"}, "GH-PR-WRITE"),
                ("Bash", {"command": "gh repo deploy-key add k.pub -R pcalnon/juniper-k8s"}, "GH-KEY-ADMIN"),
                ("Bash", {"command": "gh auth refresh -s workflow"}, "GH-AUTH"),
            ),
        ),
        (
            "`~/.ssh/**`",
            (
                ("Read", {"file_path": "@HOME@/.ssh/config"}, "CRED-PATH-FILE"),
                ("Bash", {"command": "ssh-keygen -lf ~/.ssh/id_ed25519_github_juniper-k8s.pub"}, "CRED-PATH-BASH"),
                ("Grep", {"pattern": "keygrip", "path": "@HOME@/.gnupg"}, "CRED-PATH-SEARCH"),
            ),
        ),
        (
            "change the signing configuration",
            (
                ("Bash", {"command": "git config --global user.signingkey 0123456789ABCDEF!"}, "GIT-SIGNING-CONFIG"),
                ("Bash", {"command": "python3 util/configure_commit_signing.py --remove"}, "GIT-SIGNING-CONFIG"),
            ),
        ),
        ("read the keychain", (("Bash", {"command": "security find-internet-password -s github.com"}, "KEYCHAIN-DUMP"),)),
    )
    ALLOWED = (
        ("Bash", {"command": "python3 util/git_remote_alias_check.py --json"}),
        ("Bash", {"command": "ssh -G github_juniper-k8s"}),
        ("Bash", {"command": "python3 util/configure_commit_signing.py --check --json"}),
        ("Bash", {"command": "bash util/headless_signing_preflight.bash --repo ."}),
        ("Bash", {"command": "git log -5 --format='%h %G? %GK'"}),
        ("Bash", {"command": "python3 util/host_state_check.py --section G-ALIAS --section G-SIGN --json"}),
        ("Bash", {"command": "gh api repos/pcalnon/juniper-ml/rulesets"}),
        ("Bash", {"command": "gh api repos/pcalnon/juniper-ml/rules/branches/main"}),
        ("Bash", {"command": "gh api repos/pcalnon/juniper-ml/commits/main --jq .commit.verification"}),
        ("Bash", {"command": "gh api users/pcalnon/gpg_keys"}),
        ("Bash", {"command": "gh api repos/pcalnon/juniper-k8s/keys"}),
        ("Write", {"file_path": "@REPO@/reports/2026-10-20_turing-bringup/2026-10-20T1800Z_signing-auth-sme.md", "content": "x"}),
    )

    def test_description_is_on_topic(self):
        desc = self.front.get("description", "")
        for token in ("OWNER command list", "read-only gh api GETs", "reports/", "Never touches a key, a YubiKey or a PIN"):
            with self.subTest(token=token):
                self.assertIn(token, desc)

    def test_the_checkers_and_plans_exist(self):
        for rel in ("util/git_remote_alias_check.py", "util/configure_commit_signing.py", "util/headless_signing_preflight.bash", "util/host_state_check.py", SIGNING_PLAN):
            with self.subTest(path=rel):
                self.assertTrue((REPO_ROOT / rel).is_file(), "the agent is wired to %s" % rel)
        self.assertIn(SIGNING_PLAN, self.body, "the body cites the commit-signing plan by filename")

    def test_every_gh_api_call_in_the_procedure_is_a_plain_get(self):
        procedure = self.body.split("## Procedure", 1)[-1].split("## Output", 1)[0]
        calls = [tool_input["command"] for tool, tool_input in self.ALLOWED if tool == "Bash" and tool_input["command"].startswith("gh api ")]
        self.assertGreaterEqual(len(calls), 5, "rulesets, effective rules, verification, gpg keys and deploy keys")
        for call in calls:
            with self.subTest(call=call):
                self.assertIn(call, procedure)
                flags = [tok for tok in call.split()[2:] if tok.startswith("-")]
                self.assertTrue(set(flags) <= {"--jq"}, "a GET takes --jq and nothing else: %r" % call)

    def test_body_ends_its_report_with_the_owner_command_list(self):
        output = self.body.split("## Output", 1)[-1].split("## Must never", 1)[0]
        self.assertIn("Write exactly one file: `reports/<YYYY-MM-DD>_<host>-bringup/<YYYY-MM-DDTHHMMZ>_signing-auth-sme.md`", output)
        self.assertIn("never overwrite", output)
        self.assertIn("the OWNER command list, as one fenced `bash` block", output)

    def test_owner_list_draws_on_the_plan_checklist(self):
        self.assertIn("§14.1", self.body, "the owner-run operator checklist is the plan's §14.1")
        for task in ("A2", "A3", "B3", "B4", "B5", "A1"):
            with self.subTest(task=task):
                self.assertIn(task, self.body.split("**Write the OWNER command list.**", 1)[-1])

    def test_body_explains_the_deploy_key_403(self):
        self.assertIn("403", self.body, "under D11's fine-grained token the deploy-key GET is refused")
        self.assertIn("not verifiable", self.body)

    def test_body_names_the_required_signatures_rule(self):
        self.assertIn("`required_signatures`", self.body)
        self.assertIn("util/open_signed_pr.py", self.body, "agent work lands GitHub-signed through the API")


if __name__ == "__main__":
    unittest.main()
