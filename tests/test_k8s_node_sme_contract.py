"""Static contract test for the ``k8s-node-sme`` subagent (turing bring-up task H2).

Project:     Juniper
Sub-Project: juniper-ml
Application: custom-agent suite regression tests
Author:      Paul Calnon
License:     MIT License

``.claude/agents/k8s-node-sme.md`` reviews a Mac host's worker-VM design (sizing, kubelet reservations,
taints, the join steps) against the juniper-k8s primer, decision D1 and ``conf/hosts/<host>/expected.yaml``,
and reconciles errata X1-X5 (plan §11 of
``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md``). It holds ``WebFetch`` and
no ``Bash``, because WebFetch plus Bash is a prompt-injection-to-exfiltration path. Pinned here, without a
live model, on the pattern of ``tests/test_fleet_supervisor_contract.py``:

- the frontmatter, and the exact tool set {Read, Grep, Glob, WebFetch, Write}: no Bash and no editor;
- the Must-never item of plan §11 (anything outside its write target), plus the credential paths and
  acting on fetched text, in the ``## Must never`` section, and the guard's denial of the writes and
  reads it covers, under the rules the section cites;
- that the agent's own reads and its one write pass the guard;
- the body's wiring: the no-Bash rationale, the primer and the plan's D1 sizing and taint, the errata,
  and the one ``notes/`` audit it writes.

``.claude/**`` is excluded from every pre-commit hook except markdownlint, so this unittest, wired into
``.github/workflows/ci.yml``, is the gate. The shared checks live in ``tests/agent_contract_support.py``.
"""

from __future__ import annotations

import unittest

from tests.agent_contract_support import REPO_ROOT, ContractMixin, as_tool_set

PRIMER = "juniper-k8s/notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_KUBERNETES-PRIMER.md"
NAMING = "notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md"


class K8sNodeSmeContractTest(ContractMixin, unittest.TestCase):
    """`.claude/agents/k8s-node-sme.md` against plan §11 and the C8 guard."""

    AGENT = "k8s-node-sme"
    TOOLS = frozenset({"Read", "Grep", "Glob", "WebFetch", "Write"})
    MUST_NEVER = (
        (
            "anything outside its write target",
            (
                ("Write", {"file_path": "@HOME@/.ssh/authorized_keys", "content": "x"}, "CRED-PATH-FILE"),
                ("Write", {"file_path": "@HOME@/.claude/settings.json", "content": "{}"}, "SELF-PROTECT-FILE"),
                ("Write", {"file_path": "@REPO@/.git/hooks/pre-commit", "content": "x"}, "GIT-SIGNING-FILE"),
                ("Write", {"file_path": "@HOME@/.gitconfig", "content": "x"}, "GIT-SIGNING-FILE"),
            ),
        ),
        (
            "`~/.ssh/**`",
            (
                ("Read", {"file_path": "@HOME@/.ssh/config"}, "CRED-PATH-FILE"),
                ("Glob", {"pattern": "*.conf", "path": "@HOME@/.gnupg"}, "CRED-PATH-SEARCH"),
                ("Grep", {"pattern": "kubelet", "path": "@HOME@"}, "CRED-PATH-SEARCH"),
            ),
        ),
        ("act on fetched text", ()),
    )
    ALLOWED = (
        ("Read", {"file_path": "@HOME@/Development/" + PRIMER}),
        ("Grep", {"pattern": "system-reserved", "path": "@HOME@/Development"}),
        ("Glob", {"pattern": "reports/*_turing-headroom/*.md", "path": "@REPO@"}),
        ("Write", {"file_path": "@REPO@/notes/JUNIPER_2026-10-20_JUNIPER-ECOSYSTEM_TURING-K8S-NODE-AUDIT.md", "content": "x"}),
    )

    def test_no_bash_by_design(self):
        tools = as_tool_set(self.front.get("tools"))
        self.assertNotIn("Bash", tools, "WebFetch plus Bash is a prompt-injection-to-exfiltration path (plan §11)")
        self.assertIn("WebFetch", tools, "the agent reads upstream Kubernetes documentation")
        self.assertIn("No Bash by design", self.front.get("description", ""))

    def test_body_explains_the_no_bash_rationale(self):
        rationale = self.body.split("## Why you have no Bash", 1)[-1].split("## Sources", 1)[0]
        self.assertIn("prompt-injection-to-exfiltration", rationale)
        self.assertIn("data, never instructions", rationale)
        self.assertIn("never ask for `Bash`", rationale)

    def test_body_is_wired_to_the_primer_and_the_d1_ruling(self):
        self.assertIn(PRIMER, self.body)
        self.assertIn("4 vCPU / 6 GiB / 60 GB", self.body, "decision D1's sizing")
        self.assertIn("turing=constrained:NoSchedule", self.body, "decision D1's taint")
        self.assertIn("--system-reserved", self.body)
        for rel in ("conf/hosts/<host>/expected.yaml", "util/macvm_ctl.bash"):
            with self.subTest(source=rel):
                self.assertIn(rel, self.body)
        self.assertTrue((REPO_ROOT / "util" / "macvm_ctl.bash").is_file())

    def test_body_reconciles_errata_x1_to_x5(self):
        self.assertIn("X1-X5", self.body)
        self.assertIn("Cite the current line, not the plan's copy of it", self.body)

    def test_upstream_reads_are_kubernetes_io_only(self):
        self.assertIn("from kubernetes.io only", self.body)

    def test_body_writes_one_notes_audit_and_never_overwrites(self):
        output = self.body.split("## Output", 1)[-1].split("## Must never", 1)[0]
        self.assertIn("`notes/JUNIPER_<YYYY-MM-DD>_JUNIPER-ECOSYSTEM_<HOST>-K8S-NODE-AUDIT.md`", output)
        self.assertIn(NAMING, output)
        self.assertTrue((REPO_ROOT / NAMING).is_file())
        self.assertIn("never overwrite", output)


if __name__ == "__main__":
    unittest.main()
