#!/usr/bin/env python3
"""Git push --signed abbreviations on the D11 agent guard.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_claude_agent_guard.py`` denies ``git push --signed``. The full
``--signed=<value>`` off-switch is pinned separately. Git 2.43 also runs a
shorter unambiguous prefix of ``--signed``, and that prefix requests a signed
push:

* ``git push --si``, ``--sig``, ``--sign`` and ``--signed`` ask the remote for
  a signed push. So do ``--sign=true``, ``--signed=1``, ``--signed=yes`` and
  ``--si=if-asked``.
* ``--s`` is ambiguous with ``--set-upstream`` and does not run. ``--se`` is
  ``--set-upstream``. ``--si=false``, ``--si=0``, ``--signed=no`` and
  ``--no-si`` push without a certificate.

Matching only the full spelling ``--signed`` leaves ``git push --si`` allowed
while the existing ``git push --signed origin main`` case still passes.
"""

from __future__ import annotations

import unittest

from tests.test_claude_agent_guard import GPG_SIGN, GuardHarness


# Prefixes git 2.43 actually sends as a signed push.
PUSH_SIGNING = (
    "git push --si",
    "git push --sig",
    "git push --sign",
    "git push --signe",
    "git push --signed",
    "git push --si origin main",
    "git push origin --sign",
    "git push --sign=true origin",
    "git push --signed=true",
    "git push --signed=1",
    "git push --signed=yes",
    "git push --signed=on",
    "git push --signed=YES",
    "git push --si=if-asked",
    "git push --signed=if-asked origin",
    "git push --signed=",
    "git push --si=",
    "git push --signed=00",
    "git push --signed=falsehood",
)

# Not a signed push. A prefix matcher aimed at the wrong name would catch some of these.
NOT_SIGNING = (
    "git push --s",
    "git push --se origin main",
    "git push --set-upstream origin main",
    "git push --si=false",
    "git push --si=0",
    "git push --si=no",
    "git push --si=off",
    "git push --signed=false",
    "git push --signed=FALSE",
    "git push --signed=No",
    "git push --signed=off",
    "git push --signed=0 origin main",
    "git push --no-signed",
    "git push --no-si",
    "git push --no-sig origin",
    "git push origin main",
    "git push --signoff",
    "git push --force",
    "git push --follow-tags",
)


class PushSignedAbbreviationTest(GuardHarness):
    """Prefixes git runs as ``--signed``, and the neighbours that are not one."""

    def test_a_prefix_git_sends_as_a_signed_push_is_denied(self) -> None:
        for command in PUSH_SIGNING:
            with self.subTest(command=command):
                self.assert_denied("Bash", {"command": command}, GPG_SIGN, primary=True)

    def test_the_ambiguous_prefix_the_off_switch_and_set_upstream_stay_allowed(self) -> None:
        for command in NOT_SIGNING:
            with self.subTest(command=command):
                self.assert_allowed("Bash", {"command": command})


if __name__ == "__main__":
    unittest.main()
