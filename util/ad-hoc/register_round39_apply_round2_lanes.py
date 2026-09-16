#!/usr/bin/env python3
"""Apply round-2 lanes A and B1's register findings.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: reports/2026-09-15_round-39-consensus/ (the lane reports);
         juniper-data#404 (merged 2026-09-16, squash 1bbb6976)

Four corrections, each re-verified against the repos before being written:

1. ``APD-DATA-049`` says the cache key orphans "the 485 payloads"; it is 486, which
   ``APD-DATA-051`` and the handoff both already say. A register that contradicts itself on a
   plain file count undermines every count it carries.
2. The ``APD-ECO-003`` ruling text says "The transport already honours it -- ``_request`` does
   ``kwargs.setdefault(...)`` -- so only the public signatures are missing." That is true of
   juniper-data-client and **false of juniper-cascor-client**, whose ``_request`` takes no
   ``**kwargs`` and passes ``timeout=self.timeout`` literally (``client.py:530`` and ``:544``).
   The ruling stands; the evidence sentence under it was over-generalised from one client.
3. The same ruling implies the recurrence client is done. It is **2 of 9**: only ``train`` and
   ``crossval`` expose a per-call timeout; ``predict``, ``training_status``, ``crossval_status``,
   ``get_model``, ``get_dataset``, ``health_check`` and ``is_ready`` do not, and no method takes
   ``**kwargs``, so the transport's ``setdefault`` is unreachable from seven of nine public calls.
4. ``APD-DATA-047``'s updated text quotes two figures that lane A and lane B1 both refuted, and
   which juniper-data#404 corrected in the code: the largest genuine count is Citigroup's 2.92e10
   (not AAPL's 1.70e10, which is the largest in the DEFAULT 14-SYMBOL PREFIX), and the (1e11, 1e13]
   band holds 18 observations across 9 series, not 24. The owner was being asked to ratify a bound
   against two wrong numbers.
"""

from __future__ import annotations

import sys
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

text = REGISTER.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    if new in text and old not in text:
        print(f"  --  {label} (already applied)")
        return
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: found {n} occurrences of:\n{old[:220]}")
    text = text.replace(old, new, 1)
    print(f"  ok  {label}")


# ------------------------------------------------------------------ 1: 485 -> 486
sub(
    "orphans the 485 payloads under the old CIK-only path",
    "orphans the 486 payloads under the old CIK-only path (this row said 485 until 2026-09-15; "
    "`find ~/.cache/juniper_data/equities/shares -maxdepth 1 -type f | wc -l` returns 486, and "
    "`APD-DATA-051` is about the numerators that do NOT follow that denominator)",
    "APD-DATA-049: 485 -> 486 payloads",
)

# ------------------------------------------------------------------ 2 + 3: APD-ECO-003
sub(
    "- `APD-ECO-003` — **RULED.** **Expose a per-call timeout** on the public client methods. Rejected:\n"
    "  per-operation default tables. The transport already honours it — `_request` does\n"
    "  `kwargs.setdefault(\"timeout\", self.timeout)` — so only the public signatures are missing.\n",
    "- `APD-ECO-003` — **RULED.** **Expose a per-call timeout** on the public client methods. Rejected:\n"
    "  per-operation default tables. *(**Corrected 2026-09-15.** This entry said \"The transport already\n"
    "  honours it — `_request` does `kwargs.setdefault(\"timeout\", self.timeout)` — so only the public\n"
    "  signatures are missing\", which generalised one client to three. The three are in three\n"
    "  different states, and round-2 validation measured each: **juniper-data-client** is as\n"
    "  described — `juniper_data_client/client.py:302` does the `setdefault`, so only signatures are\n"
    "  owed. **juniper-cascor-client is not** — `juniper_cascor_client/client.py:530` takes no\n"
    "  `**kwargs` and passes `timeout=self.timeout` literally at `:544`, so `_request` itself has to\n"
    "  change before any signature can matter. **juniper-recurrence-client is 2 of 9** — `train` and\n"
    "  `crossval` expose it; `predict`, `training_status`, `crossval_status`, `get_model`,\n"
    "  `get_dataset`, `health_check` and `is_ready` do not, and since no method takes `**kwargs` the\n"
    "  transport's `setdefault` at `client.py:265` is unreachable from seven of the nine. The\n"
    "  `APD-RCLIENT-002` close was honest about this — it says the other public calls stay on the\n"
    "  client-wide scalar — and this entry lost that qualifier. The ruling is unchanged; only the\n"
    "  estimate of what it costs was wrong.)*\n",
    "APD-ECO-003: the three clients are in three states",
)

# ------------------------------------------------------------------ 4: APD-DATA-047's figures
sub(
    "re-sited it between the largest genuine count in the bundled universe (AAPL, 1.70e10) and the "
    "smallest demonstrated typo in the cache (AIZ, 1.168e11), 18 observations across 24 series having "
    "sat in the dead band above 1e11.",
    "re-sited it between the largest genuine count in the cache (**Citigroup, 2.92e10**; NVIDIA second "
    "at 2.45e10) and the smallest demonstrated typo in it (AIZ, 1.168e11) — **3.4× of headroom**, not "
    "the 5.9× an earlier draft of this row claimed against AAPL's 1.70e10, which is the largest in the "
    "DEFAULT 14-SYMBOL PREFIX and not in the universe. 18 observations across **9** series sit in "
    "(1e11, 1e13]; the 24 belongs with the 39 observations above 1e11, and this row conflated the two "
    "bands. **What the owner is really choosing:** the four largest values that PASS the 1e11 ceiling "
    "are themselves typos — Pentair 9.84e10 (592× its own median), Packaging Corp 8.99e10 (949×), "
    "Regency Centers 8.19e10 (483×), Mid-America 7.50e10 (659×) — and the relative filter catches every "
    "one, delivering all four correctly. The ceiling cannot be tightened to reach them without crossing "
    "Citigroup's genuine 2.92e10 and deleting real mega-cap history, so the two populations overlap "
    "across any absolute bound. Its job is not to catch scale errors in general but the one case "
    "nothing relative can reach: a typo in a series' first filing.",
    "APD-DATA-047: correct the siting figures and state the real choice",
)

REGISTER.write_text(text)
print(f"\nregister updated: {REGISTER}")
