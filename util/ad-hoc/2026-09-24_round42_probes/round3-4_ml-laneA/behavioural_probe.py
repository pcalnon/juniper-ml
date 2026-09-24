"""Lane A probe: can a BEHAVIOURAL test tell the non-short-circuit `matched` loop from
`any(...)` (and from a `break` inside the loop)? The gate's comment says no: "any(...)
and the flag loop return the same value for every input, so no behavioural test can
tell them apart". Return values are identical; the number of compare_digest calls is not.

Loads service-core's real APIKeyAuth.validate source, and three mutants of it, and
counts compare_digest calls through a spy on the `hmac` module the class uses.
"""

from __future__ import annotations

import hmac
import textwrap
import types

REAL_LOOP = """
def validate(self, api_key):
    if not self._enabled:
        return True
    if api_key is None:
        return False
    matched = False
    for candidate in self._api_keys:
        if hmac.compare_digest(api_key, candidate):
            matched = True
    return matched
"""
ANY = """
def validate(self, api_key):
    if not self._enabled:
        return True
    if api_key is None:
        return False
    return any(hmac.compare_digest(api_key, k) for k in self._api_keys)
"""
BREAK = REAL_LOOP.replace("            matched = True\n", "            matched = True\n            break\n")
ASSIGNED_ANY = """
def validate(self, api_key):
    if not self._enabled:
        return True
    if api_key is None:
        return False
    matched = False
    matched = any(hmac.compare_digest(api_key, k) for k in self._api_keys)
    return matched
"""


class Spy:
    def __init__(self):
        self.calls = 0

    def compare_digest(self, a, b):
        self.calls += 1
        return hmac.compare_digest(a, b)


def build(src, spy):
    ns = {"hmac": types.SimpleNamespace(compare_digest=spy.compare_digest)}
    exec(textwrap.dedent(src), ns)
    obj = types.SimpleNamespace(_enabled=True, _api_keys=["k-first", "k-second", "k-third"])  # list: deterministic order
    return lambda key: ns["validate"](obj, key)


for name, src in (("matched-loop (real)", REAL_LOOP), ("any()", ANY), ("loop+break (markers kept)", BREAK), ("matched = any() (markers kept)", ASSIGNED_ANY)):
    spy = Spy()
    validate = build(src, spy)
    result = validate("k-first")
    print(f"{name:32s} validate('k-first') -> {result}; compare_digest calls = {spy.calls} (keys = 3)")

# A spy-based behavioural assertion: every configured key is compared, whatever matches.
print()
for name, src in (("matched-loop (real)", REAL_LOOP), ("any()", ANY), ("loop+break (markers kept)", BREAK), ("matched = any() (markers kept)", ASSIGNED_ANY)):
    spy = Spy()
    validate = build(src, spy)
    validate("k-first")
    verdict = "PASS" if spy.calls == 3 else "FAIL (short-circuit detected)"
    print(f"assert calls == len(keys)  on {name:32s}: {verdict}")
