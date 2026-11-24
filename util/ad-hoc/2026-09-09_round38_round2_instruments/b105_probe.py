#!/usr/bin/env python3
"""Bandit B105 polarity probe: a plain assignment trips it, an annotated one does not.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — investigation (round-2 validation of the round-38 defect-register handoff)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: reports/2026-09-09_round-38-consensus/; memory reference_bandit_b105_flags_token_names;
         see README.md in this directory.

Run it two ways. Executed, it prints what it declares. Scanned, it answers the question:

    bandit -t B105 util/ad-hoc/2026-09-09_round38_round2_instruments/b105_probe.py

Expected, bandit 1.9.4: **exactly one** finding, on ``B_REFUSAL_TOKEN``. ``B105``
(``hardcoded_password_string``) matches on the NAME — ``token`` / ``secret`` / ``password`` /
``pwd`` / ``pass`` — whatever the value, but it walks ``ast.Assign`` only, so an **annotated**
assignment (``ast.AnnAssign``) is invisible to it. That is why the identical marker constant failed
juniper-canopy's pre-commit as ``DATASET_SHORTFALL_REFUSAL_TOKEN = "..."`` and merged green in
juniper-cascor as ``_PROJECT_API_SHORTFALL_REFUSAL_TOKEN: str = "..."``, which a validation lane
read as a latent hook failure. It is not one; the difference is the type annotation.

Do not reach for the annotation as a fix. It blinds the scanner rather than making the name honest,
and the next constant copied from it in a plain assignment fails again. Rename to ``*_MARKER``.

One more lesson, learned the expensive way: the values below are printed rather than merely
declared because CodeQL's ``py/unused-global-variable`` blocked the PR that added this file —
a probe about one linter tripping a different one. Printing them is the honest fix; a ``# noqa`` or
a ``__all__`` here would have been a suppression standing in for a use.
"""

A_REFUSAL_TOKEN: str = "[x]"  # annotated -> B105 does NOT fire
B_REFUSAL_TOKEN = "[x]"  # plain -> B105 FIRES
C_TOKEN_MARKER: str = "[x]"  # annotated, name still matches -> no fire
D_MARKER = "[x]"  # plain, name does not match -> no fire

if __name__ == "__main__":
    for name, value, expected in (
        ("A_REFUSAL_TOKEN", A_REFUSAL_TOKEN, "clean (annotated)"),
        ("B_REFUSAL_TOKEN", B_REFUSAL_TOKEN, "B105 (plain assignment, matching name)"),
        ("C_TOKEN_MARKER", C_TOKEN_MARKER, "clean (annotated)"),
        ("D_MARKER", D_MARKER, "clean (name does not match)"),
    ):
        print(f"{name:<18} = {value!r:<8} expect: {expected}")
