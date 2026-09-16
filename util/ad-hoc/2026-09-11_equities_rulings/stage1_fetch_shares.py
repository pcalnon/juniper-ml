#!/usr/bin/env python3
"""
Stage 1 of the equities owner-rulings implementation: `_fetch_shares` becomes causal.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc — one-off (applied once to the juniper-data worktree named below)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: register rows APD-DATA-040 / -043 / -044 / -039 / -045 and their owner rulings of
         2026-09-09 (register §4.9 rulings block)

Three rulings land here, all inside one method:

* `-040` **as-of join on the filed date.** The method collapsed every fact to one row per PERIOD
  END, keeping the latest filing. The downstream join in `_condition_one` is already a correct
  as-of join on `filed` -- it indexes by `filed`, dedups `keep="last"` after a stable sort on
  `(filed, end)`, and forward-fills onto trading days. What broke causality was upstream: throwing
  away the ORIGINAL publication of a value whenever a later filing restated the same period. Rows
  between first publication and restatement then saw the previous period's figure, or nothing.
  162 of 485 cached CIKs carry such a restatement; 17,569 rows move; ADM, inside the default
  14-symbol prefix, by up to +11.55%; and 9 CIKs had their first count deferred outright (EXPE:
  521 rows NaN where the figure was public). The fix is to stop collapsing: every fact is an
  OBSERVATION keyed by (end, filed), and the existing downstream join then does the right thing.

* `-043` **causal median plus an absolute floor.** The scale-typo filter judged each point against
  the median of the WHOLE history, so which points survive depended on filings made after the rows
  they affect. It is now an expanding median over facts already filed. The floor is the half that
  actually rescues PSKY, whose two 1,000-share placeholders dominated the window judging its one
  real count and deleted it.

* `-044` **closed by that floor.** 100,000 shares, ruled: above PSKY's placeholders, below
  Berkshire's genuine Class-A low of 941,481. Five of the six unusable series die here; the sixth
  is Berkshire, whose numbers are real -- that is `APD-DATA-046`, filed and deferred.

* `-039` **versioned cache key + TTL.** The key was CIK-only with no version, TTL or mtime, so a
  June cache could disagree with the endpoint indefinitely and a warm hit skipped the rescue ladder
  while erasing provenance. The key now carries a payload version, and a stale file is re-fetched.
"""
from __future__ import annotations

import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--equities-causal-data-quality--20260911-2310--20cd6788")
GEN = W / "juniper_data/generators/equities/generator.py"

text = GEN.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: expected 1 match, found {n}")
    text = text.replace(old, new)
    print(f"  ok  {label}")


# ---- constants -------------------------------------------------------------------------------
sub(
    "_SHARES_OUTLIER_FACTOR = 100.0\n",
    "_SHARES_OUTLIER_FACTOR = 100.0\n"
    "# Absolute plausibility floor for a share count, in shares. Owner ruling 2026-09-09\n"
    "# (register APD-DATA-043 / -044). A listed issuer cannot have 1,000 shares outstanding; the\n"
    "# six unusable series in the bundled universe deliver 0, 1 or 1,000. Sited deliberately\n"
    "# between those and the smallest GENUINE count in the same cache -- Berkshire's Class-A\n"
    "# series bottoms at 941,481, and the smallest ordinary issuer, NVR, at 2,699,292. A floor\n"
    "# above 941,481 would start deleting real history.\n"
    "#\n"
    "# The floor does what the relative median filter cannot: a series whose BAD points are the\n"
    "# majority drags its own median down to meet them, which is exactly how PSKY's two 1,000-share\n"
    "# placeholders survived while its one real count (1,071,666,977) was filtered out as the\n"
    "# outlier.\n"
    "_SHARES_ABSOLUTE_FLOOR = 100_000.0\n"
    "# A share count older than this is reported but marked degraded rather than silently\n"
    "# forward-filled for years. Owner ruling 2026-09-09 (register APD-DATA-039 / -045), chosen\n"
    "# against the measured distribution of the 485-payload cache: median last-as-of age 138 days,\n"
    "# p90 180, and the count of flagged series is flat from 270d (28) through 365d (27) to 730d\n"
    "# (24), so the exact figure is not load-bearing. Anything under ~200 days measures cache age\n"
    "# rather than issuer staleness -- a 120-day bound flags 95% of the universe. Every 10-K and\n"
    "# 10-Q carries a share count, so a year of silence is the issuer, not the calendar.\n"
    "_SHARES_STALE_AFTER_DAYS = 365\n"
    "# Cache layout version, and how long a cached payload is trusted before re-fetching.\n"
    "# The key was CIK-only with neither, so a cache written in June could disagree with SEC\n"
    "# indefinitely while a warm hit skipped the rescue ladder entirely. Bump the version whenever\n"
    "# the SHAPE of the cached payload changes; the TTL covers the content going stale underneath\n"
    "# an unchanged shape.\n"
    "_SHARES_CACHE_VERSION = 2\n"
    "_SHARES_CACHE_TTL_DAYS = 7\n",
    "constants",
)

# ---- cache read: versioned key + TTL ----------------------------------------------------------
sub(
    '        cache = _CACHE_DIR / "shares" / f"{int(cik):010d}.json"\n'
    "        data = None\n"
    "        if use_cache and cache.exists():\n"
    "            try:\n"
    "                data = json.loads(cache.read_text())\n"
    "            except (OSError, json.JSONDecodeError):\n"
    "                data = None\n",
    '        cache = _CACHE_DIR / "shares" / f"v{_SHARES_CACHE_VERSION}" / f"{int(cik):010d}.json"\n'
    "        data = None\n"
    "        if use_cache and cache.exists():\n"
    "            # A cached payload is trusted for _SHARES_CACHE_TTL_DAYS and then re-fetched. An\n"
    "            # unreadable mtime is treated as expired rather than fresh: failing towards a\n"
    "            # network call costs a request, failing towards the cache can serve a year-old\n"
    "            # figure forever, which is the defect this replaces.\n"
    "            try:\n"
    "                age_days = (time.time() - cache.stat().st_mtime) / 86400.0\n"
    "            except OSError:\n"
    "                age_days = float(\"inf\")\n"
    "            if age_days <= _SHARES_CACHE_TTL_DAYS:\n"
    "                try:\n"
    "                    data = json.loads(cache.read_text())\n"
    "                except (OSError, json.JSONDecodeError):\n"
    "                    data = None\n",
    "cache read",
)

# ---- the collapse becomes an observation table -------------------------------------------------
sub(
    "        # Keep the latest-filed value per period-end date, and the filing date\n"
    "        # that supplied it -- the sort key already orders by (end, filed), so the\n"
    "        # last write per end date wins and both facts come from the same point.\n"
    "        best: dict[str, float] = {}\n"
    '        filed_on: dict[str, str] = {}\n'
    '        for unit_points in data["units"].values():\n'
    '            for point in sorted(unit_points, key=lambda item: (item.get("end", ""), item.get("filed", ""))):\n'
    '                if point.get("val") is not None and point.get("end"):\n'
    '                    best[point["end"]] = float(point["val"])\n'
    '                    if point.get("filed"):\n'
    '                        filed_on[point["end"]] = point["filed"]\n'
    "        if not best:\n"
    "            return None\n"
    "        series = pd.Series(best)\n"
    "        series.index = pd.to_datetime(series.index)\n"
    "        series = series.sort_index()\n"
    "        # Drop XBRL filer scale errors (isolated points ~1e6x off): forward-fill\n"
    "        # then carries the last good value across the dropped point. Median is\n"
    "        # robust to the minority of bad points.\n"
    "        median = float(series.median())\n"
    "        if median > 0:\n"
    "            series = series[(series >= median / _SHARES_OUTLIER_FACTOR) & (series <= median * _SHARES_OUTLIER_FACTOR)]\n"
    "        if not len(series):\n"
    "            return None\n"
    "\n"
    '        frame = series.to_frame(name="shares")\n',
    "        # EVERY FACT IS AN OBSERVATION, not a correction to be collapsed.\n"
    "        #\n"
    "        # This used to keep one value per PERIOD END -- the latest-filed one -- which threw\n"
    "        # away the original publication whenever a later filing restated the same period. The\n"
    "        # value then appeared to become knowable on the restatement date, months or years after\n"
    "        # it was actually public, and every row in between saw the previous period's figure or\n"
    "        # nothing at all. Measured over the 485-payload cache: 162 CIKs carry such a\n"
    "        # restatement, 17,569 rows move, ADM (inside the default 14-symbol prefix) by up to\n"
    "        # +11.55%, and 9 CIKs had their first count deferred outright -- EXPE by 521 rows.\n"
    "        #\n"
    "        # Keyed by (end, filed) instead, the frame carries the full publication history and\n"
    "        # ``_condition_one``'s existing as-of join -- index by ``filed``, stable sort on\n"
    "        # (filed, end), forward-fill onto trading days -- reads exactly what was knowable on\n"
    "        # each date. That join was always right; it was being fed a rewritten past.\n"
    "        records: list[tuple[Any, Any, float]] = []\n"
    '        for unit_points in data["units"].values():\n'
    "            for point in unit_points:\n"
    '                if point.get("val") is None or not point.get("end"):\n'
    "                    continue\n"
    '                records.append((point["end"], point.get("filed") or None, float(point["val"])))\n'
    "        if not records:\n"
    "            return None\n"
    '        observations = pd.DataFrame(records, columns=["end", "filed", "shares"])\n'
    '        observations["end"] = pd.to_datetime(observations["end"], errors="coerce")\n'
    '        observations["filed"] = pd.to_datetime(observations["filed"], errors="coerce")\n'
    '        observations = observations.dropna(subset=["end"])\n'
    "        # The same (period, filing) reported twice is one observation, not two.\n"
    '        observations = observations.drop_duplicates(subset=["end", "filed"], keep="last")\n'
    "        # Stable, and ordered the way the data became knowable. ``na_position='first'`` puts\n"
    "        # facts with no filing date at the start, where they are treated as always-known --\n"
    "        # the same reading the downstream join gives them by dropping them from the as-of index.\n"
    '        observations = observations.sort_values(["filed", "end"], kind="stable", na_position="first").reset_index(drop=True)\n'
    "\n"
    "        # ABSOLUTE FLOOR FIRST, and deliberately before the relative filter: a series whose bad\n"
    "        # points are the majority drags its own median down to meet them, so the relative test\n"
    "        # cannot be trusted until the impossible values are gone. See _SHARES_ABSOLUTE_FLOOR.\n"
    '        observations = observations[observations["shares"] >= _SHARES_ABSOLUTE_FLOOR]\n'
    "        if not len(observations):\n"
    "            return None\n"
    "\n"
    "        # CAUSAL scale-typo filter. The old one compared every point to the median of the whole\n"
    "        # history, so which points survived depended on filings made after the rows they\n"
    "        # affect -- a look-ahead in the filter itself (61 of 485 CIKs lose at least one point,\n"
    "        # and 15 or 16 keep a different set under a causal median). An expanding median sees\n"
    "        # only what was already filed. ``min_periods`` keeps the opening points: a median over\n"
    "        # one or two observations is not a basis for deleting a third.\n"
    '        running_median = observations["shares"].expanding(min_periods=3).median()\n'
    "        keep = running_median.isna() | (\n"
    '            (observations["shares"] >= running_median / _SHARES_OUTLIER_FACTOR) & (observations["shares"] <= running_median * _SHARES_OUTLIER_FACTOR)\n'
    "        )\n"
    "        observations = observations[keep]\n"
    "        if not len(observations):\n"
    "            return None\n"
    "\n"
    '        frame = observations.set_index("end")[["shares"]]\n',
    "observation table",
)

# ---- provenance + filed column now come from the observation table ----------------------------
sub(
    "        # A point with no ``filed`` (rare, older filings) becomes NaT rather than\n"
    "        # a guess -- the consumer sees \"unknown\", not a fabricated date.\n"
    '        frame["filed"] = pd.to_datetime(pd.Series({pd.Timestamp(end): filed_on.get(end) for end in best}, dtype="object")).reindex(frame.index)\n'
    "        return frame\n",
    "        # A point with no ``filed`` (rare, older filings) stays NaT rather than becoming a\n"
    '        # guess -- the consumer sees "unknown", not a fabricated date. It rides the frame\n'
    "        # positionally now, because the index is no longer unique: one period end can carry\n"
    "        # several filings, which is the whole point of the change above.\n"
    '        frame["filed"] = observations["filed"].to_numpy()\n'
    "        return frame\n",
    "filed column",
)

GEN.write_text(text)
print("\nstage 1 written")
