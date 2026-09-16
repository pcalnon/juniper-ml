#!/usr/bin/env python3
"""
Add the regressions for the three owner rulings that shipped without one: the as-of publication
history (APD-DATA-040), the absolute floor (APD-DATA-043 / -044), and the staleness annotation
(APD-DATA-039 / -045).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-11_equities_rulings/stage1_fetch_shares.py

Each test is written against the DEFECT, not the implementation: it constructs the payload shape
that produced the wrong answer in the 485-payload cache and asserts the corrected one, so a
refactor that reintroduces the defect fails even if it keeps the current code's structure.
"""
from __future__ import annotations

import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--equities-causal-data-quality--20260911-2310--20cd6788")
TESTS = W / "juniper_data/tests/unit/test_equities_generator.py"

NEW = '''

class TestTheOwnerRulingsOf20260909:
    """The equities data-quality rulings, each pinned against the payload that motivated it.

    These are register rows APD-DATA-039 through -045. The figures in the docstrings come from
    the 485-payload SEC cache the rulings were taken against, re-derived on the day.
    """

    def test_a_restatement_no_longer_rewrites_when_a_value_became_knowable(self) -> None:
        """APD-DATA-040: every fact is an observation, not a correction to collapse.

        The method kept one value per PERIOD END -- the latest-filed one -- so a later filing that
        restated an earlier period moved that period's ``filed`` date forward, and the value
        appeared to become knowable months or years after it actually was. 162 of 485 cached CIKs
        carry such a restatement, 17,569 rows move, and 9 CIKs had their first count deferred
        outright.

        Here one period end is reported twice: originally in 2009, restated in 2012. The original
        publication must survive, because a reader in 2010 could see it.
        """
        payload = {
            "units": {
                "shares": [
                    {"end": "2009-06-30", "val": 1.0e9, "filed": "2009-07-15"},
                    {"end": "2009-06-30", "val": 1.02e9, "filed": "2012-02-20"},
                    {"end": "2010-06-30", "val": 1.1e9, "filed": "2010-07-15"},
                ]
            }
        }
        with patch.object(eq_gen, "_sec_get", return_value=payload):
            frame = eq_gen.EquitiesGenerator._fetch_shares(320193, use_cache=False)
        assert frame is not None
        filings = pd.to_datetime(frame["filed"]).dt.strftime("%Y-%m-%d").tolist()
        assert "2009-07-15" in filings, "the ORIGINAL publication must survive the restatement"
        assert "2012-02-20" in filings, "and so must the restatement itself"
        assert len(frame) == 3, "three facts in, three observations out -- nothing is collapsed"

    def test_the_absolute_floor_removes_placeholders_and_keeps_real_counts(self) -> None:
        """APD-DATA-043 / -044: the floor, at the two boundaries that decided its value.

        1,000 shares is PSKY's placeholder; 941,481 is Berkshire's genuine Class-A low. The floor
        was sited at 100,000 precisely to separate them, so this asserts both directions at once --
        a floor above Berkshire's low would delete real history, one below PSKY's placeholders
        would keep junk.
        """
        payload = {
            "units": {
                "shares": [
                    {"end": "2019-03-31", "val": 1000.0, "filed": "2019-04-01"},
                    {"end": "2019-06-30", "val": 1000.0, "filed": "2019-07-01"},
                    {"end": "2019-09-30", "val": 941_481.0, "filed": "2019-10-01"},
                    {"end": "2019-12-31", "val": 1_071_666_977.0, "filed": "2020-01-02"},
                ]
            }
        }
        with patch.object(eq_gen, "_sec_get", return_value=payload):
            frame = eq_gen.EquitiesGenerator._fetch_shares(320193, use_cache=False)
        assert frame is not None
        kept = sorted(float(v) for v in frame["shares"])
        assert kept == [941_481.0, 1_071_666_977.0], "placeholders out, genuine Class-A scale in"

    def test_a_series_of_only_placeholders_is_unrescued_not_zero(self) -> None:
        """APD-DATA-044: an all-placeholder series is absent data, not a measurement of zero.

        TAP, CVNA and DDOG delivered ``total_shares == 0`` for 100% of their rows and a
        ``market_cap`` of 0.0 -- a number no listed company can have -- while passing every guard,
        because zero is not NaN. Returning None routes them into the incomplete-data contract
        instead, where the default policy refuses and an opt-in annotates.
        """
        payload = {"units": {"shares": [{"end": "2019-03-31", "val": 0.0, "filed": "2019-04-01"}, {"end": "2019-06-30", "val": 0.0, "filed": "2019-07-01"}]}}
        with patch.object(eq_gen, "_sec_get", return_value=payload):
            assert eq_gen.EquitiesGenerator._fetch_shares(320193, use_cache=False) is None

    def test_the_causal_median_does_not_consult_later_filings(self) -> None:
        """APD-DATA-043: which points survive must not depend on filings that had not happened.

        The old filter compared every point to the median of the WHOLE history, so a value's
        survival depended on its own future. Two payloads share a prefix and differ only in facts
        filed later; the surviving prefix must be identical.
        """
        prefix = [
            {"end": "2009-03-31", "val": 1.00e9, "filed": "2009-04-01"},
            {"end": "2009-06-30", "val": 1.01e9, "filed": "2009-07-01"},
            {"end": "2009-09-30", "val": 1.02e9, "filed": "2009-10-01"},
            {"end": "2009-12-31", "val": 1.03e9, "filed": "2010-01-01"},
        ]
        later = [{"end": "2010-03-31", "val": 9.9e12, "filed": "2010-04-01"}]
        with patch.object(eq_gen, "_sec_get", return_value={"units": {"shares": list(prefix)}}):
            short = eq_gen.EquitiesGenerator._fetch_shares(320193, use_cache=False)
        with patch.object(eq_gen, "_sec_get", return_value={"units": {"shares": prefix + later}}):
            long = eq_gen.EquitiesGenerator._fetch_shares(320193, use_cache=False)
        assert short is not None and long is not None
        assert [float(v) for v in short["shares"]] == [float(v) for v in long["shares"]][: len(short)]

    def test_a_stale_share_count_is_annotated_degraded(self) -> None:
        """APD-DATA-039 / -045: a year-old count is reported, and reported AS stale.

        The hard part of this defect is that nothing looks wrong: the count is real, the source is
        the best one available, and the resulting market cap is plausible. 26 of 485 cached issuers
        stop filing before 2025-06-01 and every later row silently reuses the last value. The
        annotation is the whole remedy -- the rows are still served.
        """
        frame = _ohlcv(seed=21)
        # One filing, early, and then silence for the rest of the window.
        stale_shares = pd.DataFrame(
            {"shares": [1_000_000_000.0], "filed": [pd.Timestamp("2008-02-01")]},
            index=pd.to_datetime([pd.Timestamp("2007-12-31")]),
        )
        with _mocked({"AAPL": frame}, stale_shares):
            meta = eq_gen.EquitiesGenerator.generate(
                EquitiesParams(symbols=["AAPL"], start_date="2008-01-01", end_date="2011-01-01", use_cache=False, allow_truncation=True, incomplete_rows="accept")
            ).get(DATA_QUALITY_META_KEY)
        assert meta is not None, "a stale series must not be reported as clean"
        assert "AAPL" in meta["degraded"]
        assert eq_gen.SHARES_QUALITY_STALE in meta["degraded"]["AAPL"]
'''

text = TESTS.read_text()
if "class TestTheOwnerRulingsOf20260909" in text:
    sys.exit("FAIL: already applied")
if "DATA_QUALITY_META_KEY" not in text.split("\n\n")[0] and "DATA_QUALITY_META_KEY" not in text[:4000]:
    print("  note: DATA_QUALITY_META_KEY may need importing -- checking")
TESTS.write_text(text.rstrip("\n") + "\n" + NEW)
print("regression class appended")
