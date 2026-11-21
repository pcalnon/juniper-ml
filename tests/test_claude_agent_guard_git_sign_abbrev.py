#!/usr/bin/env python3
"""Git signing long-option abbreviations on the D11 agent guard.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_claude_agent_guard.py`` denies ``git commit --gpg-sign=KEYID`` and the exact
tag options ``--sign`` and ``--local-user``. Git also runs a shorter unambiguous prefix, and
that prefix signs (re-derived on git 2.53.0 with a recording ``gpg.program`` stub):

* ``git commit --g``, ``--gp``, ``--gpg``, ``--gpg-s``, and ``--gpg=KEY`` are ``--gpg-sign``.
  With ``commit.gpgsign`` false, each of those still calls the signing program. ``git merge --g``
  does the same for the merge commit, and so do ``rebase``, ``am``, ``pull`` and ``commit-tree``.
* ``git tag --si`` and ``--sig`` are ``--sign`` (the tag object carries a signature).
  ``git tag --lo`` and ``--loc`` are ``--local-user``.

The off switches and the neighbours that are not signing stay allowed. ``--no-gpg-sign``,
``--no-gpg``, and ``--no-g`` leave the commit unsigned. ``--signoff`` and ``-s`` add a
trailer, not a signature. ``git rebase --skip`` and ``git cherry-pick --skip`` continue a
sequence. ``git tag --s`` is ambiguous with ``--sort`` and does not run; ``--l`` is
ambiguous with ``--list``; ``--so`` and ``--sort`` sort. ``git merge --verify-signatures``
checks a signature, it does not create one.

Three spellings are denied although git does not sign with them: ``git tag --si=`` (git
refuses it: ``option `sign' takes no value``), and ``git cherry-pick --gpg`` and
``git revert --gpg`` (git 2.53 prints the usage). The guard judges any prefix of
``--gpg-sign`` a signing request on every signing subcommand, which costs nothing there.

Matching only the full spelling ``--gpg-sign`` leaves ``git commit --g`` allowed while the
existing ``--gpg-sign=KEYID`` case still passes. Treating every option that starts with
``sign`` as signing would deny ``git commit --signoff`` and ``git tag --signoff``.
"""

from __future__ import annotations

import unittest

from tests.test_claude_agent_guard import GPG_SIGN, GuardHarness

# Prefixes git 2.53 actually signs with (commit.gpgsign left false).
COMMIT_SIGNING = (
    "git commit --g -m x",
    "git commit --gp -m x",
    "git commit --gpg -m x",
    "git commit --gpg-s -m x",
    "git commit --gpg-si -m x",
    "git commit --gpg-sign -m x",
    "git commit --gpg-sign=KEY -m x",
    "git commit --gpg=KEY -m x",
    "git merge --g main",
    "git merge --gpg main",
    "git rebase --gpg main",
    "git cherry-pick --gpg-sign abc",
    "git revert --gpg-sign abc",
    "git am --gpg mbox",
    "git pull --gpg",
    "git commit-tree --gpg abc",
)

TAG_SIGNING = (
    "git tag --sign -m t v1",
    "git tag --si -m t v1",
    "git tag --sig -m t v1",
    "git tag --local-user KEY v1",
    "git tag --lo KEY v1",
    "git tag --loc KEY v1",
    "git tag --local-u KEY v1",
    "git tag --lo=KEY v1",
)

# Denied, although git does not sign with them (see the module docstring).
DENIED_NOT_RUN = (
    "git tag --si= -m t v1",
    "git cherry-pick --gpg abc",
    "git revert --gpg abc",
)

# Not a signature, and a prefix matcher aimed at the wrong name would catch them.
NOT_SIGNING = (
    "git commit --signoff -m x",
    "git commit -s -m x",
    "git commit --no-gpg-sign -m x",
    "git commit --no-gpg -m x",
    "git commit --no-g -m x",
    "git tag --s -m t v1",
    "git tag --l -m t v1",
    "git tag --so creator v1",
    "git tag --sort=refname",
    "git tag --no-sign -m t v1",
    "git tag --signoff -m t v1",
    "git tag -a v1 -m x",
    "git rebase --skip",
    "git cherry-pick --skip",
    "git am --skip",
    "git revert --skip",
    "git merge --verify-signatures main",
    "git merge --signoff main",
)


class GitSignAbbreviationTest(GuardHarness):
    """Prefixes git runs as a signing option, and the neighbours that are not one."""

    def test_a_prefix_git_signs_with_is_denied(self) -> None:
        for command in COMMIT_SIGNING + TAG_SIGNING + DENIED_NOT_RUN:
            with self.subTest(command=command):
                self.assert_denied("Bash", {"command": command}, GPG_SIGN, primary=True)

    def test_signoff_skip_sort_and_the_off_switch_stay_allowed(self) -> None:
        for command in NOT_SIGNING:
            with self.subTest(command=command):
                self.assert_allowed("Bash", {"command": command})


if __name__ == "__main__":
    unittest.main()
