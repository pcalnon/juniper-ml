#!/usr/bin/env python3
"""`git push --signed=<value>` on the D11 agent guard.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_claude_agent_guard.py`` denies the bare flag ``git push --signed`` and never
sends ``--signed=<value>``. The value form is the off-switch: an exact, casefolded
``false``, ``no``, ``off`` or ``0`` is not a signing use. Every other value is, including
git's ``if-asked``, an empty value, a longer word that only starts with an off-value, and
``00`` / ``0.0`` (the off-switch is the string ``0``, not a number).

Inverting the membership test would allow ``git push --signed=true`` while the bare-flag
case in the main suite still passed. These cases run the guard as a subprocess against a
temporary home, the same way that suite does. Production code is unchanged.
"""

from __future__ import annotations

import unittest

from tests.test_claude_agent_guard import GPG_SIGN, GuardHarness

# Exact off-values, plus one non-lowercase spelling of each word. "0" has no case.
OFF_VALUES = ("false", "no", "off", "0", "FALSE", "No", "Off")
# Anything that is not one of those four strings. Neighbours of the off-values are here
# on purpose: a prefix check or an int() read of "0" would let them through.
ON_VALUES = ("true", "TRUE", "yes", "if-asked", "1", "", "falsehood", "00", "0.0", "none")


class PushSignedValueTest(GuardHarness):
    """The ``=value`` form of ``git push --signed``, both sides of the off-switch."""

    def test_an_exact_off_value_is_not_a_signing_use(self) -> None:
        for value in OFF_VALUES:
            command = "git push --signed=%s origin main" % value
            with self.subTest(command=command):
                self.assert_allowed("Bash", {"command": command})

    def test_any_other_value_is_denied_as_a_signing_use(self) -> None:
        for value in ON_VALUES:
            command = "git push --signed=%s origin main" % value
            with self.subTest(command=command):
                self.assert_denied("Bash", {"command": command}, GPG_SIGN, primary=True)

    def test_the_bare_flag_stays_denied(self) -> None:
        self.assert_denied("Bash", {"command": "git push --signed origin main"}, GPG_SIGN, primary=True)


if __name__ == "__main__":
    unittest.main()
