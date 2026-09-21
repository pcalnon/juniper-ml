#!/usr/bin/env python3
"""Close APD-ML-001 — the pin-capping rule is now stated beside the pins and in the contract test.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: APD-ML-001 (item M-A)

THE DEFECT WAS THE SILENCE, AND THE RULING SAID SO. "State the capping rule; leave the pins."
Rejected in the same ruling: capping consistently (which would make juniper-ml gate every sibling
0.y release) and removing the caps entirely. So NO PIN CHANGES -- verified by the contract test
`tests/test_pyproject_extras.py`, which asserts the exact pin strings across pyproject.toml and
four documents and still passes.

BUNDLED WITH THE FIX, deliberately, and consistently with how APD-CASCOR-005 was handled.
"Status is verified, not inherited" forbids closing a row whose fix is on an unmerged branch in
ANOTHER repo -- which is why the cascor close waited. Here the fix and the close are the same
commit in the same repo, so they land atomically and there is no window where the register claims
a fix that main does not have.

WHAT WAS ACTUALLY DERIVED, because "state the rule" presupposes the rule is known and it was not
written down anywhere. The register only records the primer's claim that "the pattern is coherent
even if never stated as policy". Reading the pins, it is:

    CEILING     -> shared libraries a consumer imports and must migrate to
                   (config-tools, doc-tools, model-core, service-core, recurrence x3)
    NO CEILING  -> the standalone applications and their clients
                   (canopy, cascor, data, data-client, cascor-client, cascor-worker)

AND TWO PINS DO NOT FIT -- both shared libraries the rule says should be capped:

  * juniper-ci-tools was capped `<0.2.0` when its extra was added (ml#293) and lost the ceiling in
    ml#295, IN THE SAME DIFF that folded `ci-tools` into `[tools]`, while `doc-tools` kept its
    ceiling in that same PR.
  * juniper-observability has never carried a ceiling in any revision.

That is a qualification of the primer's "coherent", not a contradiction of the ruling: the ruling
forbids changing the pins, and this records the exceptions instead of smoothing them away. The
claim is measured by `util/ad-hoc/2026-09-21_verify_pin_ceiling_rule.py`, which carries its own
`--self-test` negative control so that "matches" is not a vacuous pass.

FOUR TOUCHES, NOT FIVE -- APD-ML-001 has no §3 detail entry (`grep -c '^### APD-ML-001'` is 0).
"""

from __future__ import annotations

import sys
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

_FIXED = (
    "**FIXED (juniper-ml — this PR)** — the capping rule is now stated beside the pins "
    "(`pyproject.toml`, the block above `[project.optional-dependencies]`) and in the docstring of "
    "`tests/test_pyproject_extras.py`, the contract test that reads them. **No pin changed**, which "
    "is what the ruling required and what that test verifies. The rule, which was nowhere written "
    "down before: a `<` ceiling goes on the shared LIBRARIES a consumer imports and must migrate to "
    "(`config-tools`, `doc-tools`, `model-core`, `service-core`, the three `recurrence` packages); "
    "the standalone APPLICATIONS and clients (`canopy`, `cascor`, `data`, `data-client`, "
    "`cascor-client`, `cascor-worker`) carry a floor only, because capping them would make "
    "juniper-ml gate every sibling `0.y` release. **The primer's \"coherent\" is qualified, not "
    "confirmed: TWO pins do not fit**, and both are shared libraries the rule says should be capped. "
    "`juniper-ci-tools` *was* capped `<0.2.0` when its extra was added ([ml#293](https://github.com/pcalnon/juniper-ml/pull/293)) "
    "and lost the ceiling in [ml#295](https://github.com/pcalnon/juniper-ml/pull/295), in the same diff that folded `ci-tools` into "
    "`[tools]` — while `doc-tools` kept its ceiling in that same PR. `juniper-observability` has "
    "never carried one. Both are recorded rather than corrected, because re-capping is a dependency "
    "change and the ruling is explicit that the pins stay. — "
)

T_ROW_OLD = "| APD-ML-001  | First-party pins inconsistently capped; the pattern is coherent but unstated"
T_ROW_NEW = "| APD-ML-001  | " + _FIXED + "First-party pins inconsistently capped; the pattern is coherent but unstated"

T_51_ANCHOR = "is a fourth copy, still short-circuiting, and the drift gate cannot express it — see the row. |"
T_51_NEW = T_51_ANCHOR + (
    "\n| APD-ML-001 | First-party pins inconsistently capped; the pattern is coherent but unstated "
    "| juniper-ml (this PR) "
    "| The rule is stated in two places a reader actually meets it: a comment block immediately above "
    "`[project.optional-dependencies]` in `pyproject.toml`, and the docstring of "
    "`tests/test_pyproject_extras.py`. **No pin changed** — `tests/test_pyproject_extras.py` asserts the "
    "exact pin strings across pyproject and four documents and passes unmodified (7 tests), which is the "
    "evidence that the ruling's \"leave the pins\" was honoured. The stated rule was **measured, not "
    "asserted from reading**: `util/ad-hoc/2026-09-21_verify_pin_ceiling_rule.py` classifies every pin "
    "and confirms 7 capped / 8 uncapped with the uncapped set equal to the six applications plus exactly "
    "two exceptions — and the 8 independently corroborates the count this register re-derived. That "
    "script carries a `--self-test` negative control (three perturbations, each required to flip the "
    "result to failure) so a \"matches\" is not a vacuous pass. **Deliberately NOT encoded as an "
    "assertion:** a test of the rule would fail on `juniper-ci-tools` and `juniper-observability`, "
    "forcing a dependency change or a waiver that the ruling forbids, and a gate that fails for a reason "
    "nobody intends to fix trains people to ignore it. |"
)

T_S2A_OLD = "and (2026-09-21) `APD-CASCOR-005` — leaving **16 open** of the primer rows"
T_S2A_NEW = "and (2026-09-21) `APD-CASCOR-005` / `APD-ML-001` — leaving **15 open** of the primer rows"

T_S2B_OLD = "**Eighty of the 96 have since been fixed**"
T_S2B_NEW = "**Eighty-one of the 96 have since been fixed**"

T_S2C_OLD = "— and seven are open — **23 open in all**, 16 primer + 7 post-primer."
T_S2C_NEW = "— and seven are open — **22 open in all**, 15 primer + 7 post-primer."

T_RULING_OLD = "- `APD-ML-001` — **RULED.** **State the capping rule; leave the pins.**"
T_RULING_NEW = (
    "- `APD-ML-001` — **RULED, and SHIPPED 2026-09-21** — stated in `pyproject.toml` and in "
    "`tests/test_pyproject_extras.py`'s docstring, with no pin changed. Writing it down surfaced that "
    "the pattern is coherent **with two exceptions** (`juniper-ci-tools`, whose ceiling was lost in "
    "ml#295's restructure, and `juniper-observability`, which never had one) — recorded, not corrected. "
    "Ruling as taken: **State the capping rule; leave the pins.**"
)

T_CONF_OLD = "~~`APD-CASCOR-005`~~ (fixed, cascor#659 + ml#1974), `APD-ML-001`)"
T_CONF_NEW = "~~`APD-CASCOR-005`~~ (fixed, cascor#659 + ml#1974), ~~`APD-ML-001`~~ (fixed, stated not actioned))"

REPLACEMENTS = (
    ("§4 table row", T_ROW_OLD, T_ROW_NEW),
    ("§5.1 verification row", T_51_ANCHOR, T_51_NEW),
    ("§2 primer fixed-list + primer open count", T_S2A_OLD, T_S2A_NEW),
    ("§2 'Eighty' -> 'Eighty-one'", T_S2B_OLD, T_S2B_NEW),
    ("§2 totals", T_S2C_OLD, T_S2C_NEW),
    ("§4.9 ruling bullet", T_RULING_OLD, T_RULING_NEW),
    ("§6 Confidence note — strikethrough the closed row", T_CONF_OLD, T_CONF_NEW),
)


def main() -> int:
    text = REGISTER.read_text(encoding="utf-8")

    for label, old, _new in REPLACEMENTS:
        count = text.count(old)
        if count != 1:
            print(f"REFUSED  {label}: anchor found {count} times, wanted exactly 1")
            print(f"         anchor: {old[:110]}")
            return 2

    for label, old, new in REPLACEMENTS:
        text = text.replace(old, new, 1)
        print(f"applied  {label}")

    REGISTER.write_text(text, encoding="utf-8")
    print(f"\nwrote {REGISTER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
