#!/usr/bin/env python3
"""`git -c *.gpgsign=<value>` on the D11 agent guard.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_claude_agent_guard.py`` denies ``git -c commit.gpgsign=true`` and allows
``=false``. Those two rows do not pin the rest of the off-switch. Git treats ``false``,
``no``, ``off`` and ``0`` as off, and ``true``, ``yes``, ``on`` and ``1`` as on. The
guard allows only the four off strings, after ``strip()`` and ``casefold()``, on a key
that contains ``gpgsign`` (also casefolded).

A prefix check would allow ``falsehood`` and ``offside``. Reading ``0`` as a number
would allow ``00`` and ``0.0``. Dropping ``strip()`` would deny a value that is ``0``
or ``false`` once whitespace is removed. Dropping the key's ``casefold()`` would allow
``commit.GPGSIGN=true``, which still turns signing on. ``git push --signed=<value>`` is
a different off-switch and is not what these cases pin.

These cases run the guard as a subprocess against a temporary home, the same way the
main suite does. Production code is unchanged.
"""

from __future__ import annotations

import unittest

from tests.test_claude_agent_guard import GPG_SIGN, GuardHarness

# Exact off-values. One non-lowercase spelling of each word; "0" has no case.
# Both commit.gpgsign and tag.gpgsign contain the substring the guard matches.
OFF_ASSIGNMENTS = (
    "commit.gpgsign=false",
    "commit.gpgsign=no",
    "tag.gpgsign=off",
    "commit.gpgsign=0",
    "commit.gpgsign=FALSE",
    "tag.gpgsign=No",
    "commit.gpgsign=Off",
)
# The same strings with whitespace the value's strip() removes, kept as one -c word.
PADDED_COMMANDS = (
    "git -c 'commit.gpgsign= false ' status",
    "git -c 'commit.gpgsign=\t0' status",
    "git -c 'tag.gpgsign= OFF ' status",
)
# Git-true spellings, an empty value, and neighbours of the off-values. A prefix
# check or an int() read of "0" would let the neighbours through.
ON_ASSIGNMENTS = (
    "commit.gpgsign=true",
    "commit.GPGSIGN=true",
    "commit.gpgsign=TRUE",
    "commit.gpgsign=yes",
    "tag.gpgsign=on",
    "commit.gpgsign=1",
    "commit.gpgsign=",
    "commit.gpgsign",
    "commit.gpgsign=falsehood",
    "commit.gpgsign=offside",
    "commit.gpgsign=00",
    "commit.gpgsign=0.0",
    "commit.gpgsign=none",
    "commit.gpgsign=nope",
)


class GpgsignOffSwitchTest(GuardHarness):
    """``git -c`` values whose key contains ``gpgsign``, both sides of the off-switch."""

    def test_an_exact_off_value_is_not_a_signing_use(self) -> None:
        commands = ["git -c %s status" % assignment for assignment in OFF_ASSIGNMENTS]
        commands.extend(PADDED_COMMANDS)
        commands.append("git -c commit.gpgsign=no commit -m x")
        for command in commands:
            with self.subTest(command=command):
                self.assert_allowed("Bash", {"command": command})

    def test_any_other_value_is_denied_as_a_signing_use(self) -> None:
        commands = ["git -c %s status" % assignment for assignment in ON_ASSIGNMENTS]
        commands.append("git -c commit.gpgsign=yes commit -m x")
        for command in commands:
            with self.subTest(command=command):
                self.assert_denied("Bash", {"command": command}, GPG_SIGN, primary=True)

    def test_a_key_without_gpgsign_stays_allowed(self) -> None:
        for value in ("true", "false", "yes", "0"):
            command = "git -c core.editor=%s status" % value
            with self.subTest(command=command):
                self.assert_allowed("Bash", {"command": command})


if __name__ == "__main__":
    unittest.main()
