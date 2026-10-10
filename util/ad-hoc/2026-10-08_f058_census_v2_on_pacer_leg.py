#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-08
# Status      : ad-hoc — instrument wrapper for one fix; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Run the F-CANOPY-058 census v2 unchanged against a leg serving canopy's request/ack pacer.

``2026-10-04_f058_census_v2_live.py`` identifies the feeder by its exact output key, ``FEED``. On canopy branch
``fix/f055-f058-f068-request-ack-pacer`` the feeder has a second Output, the ack, so its key is
``..metrics-panel-metrics-store.data...metrics-store-ack.data..``. This wrapper loads the census module, sets
``FEED`` to that key, and calls its ``main()``; nothing else in the census changes. Read its docstring for the
windows, the triggers, the verdict rule and the predictions, which were fixed for canopy ``main``.

What carries over to the pacer leg, and what does not:
  * The request lifecycle (A answered, X evicted) is read at the dispatch as before, so EVICTED counts are
    directly comparable with Phase 11's runs. The fix predicts 0 evictions in every window.
  * Watchdog fires: the fix removed the watchdog, so the census's fire detector has nothing to see; 0 is the
    structural expectation, not a measurement.
  * The triggers' TOOK predicates look for a gate write of ``false`` onto a lane that was ``true`` before it.
    On the pacer leg the gate is the lane's only writer and holds it ``false`` outside an Apply, so the
    gate and tab triggers are expected to read NO-EFFECT. T-mode's TOOK (a new feeder request while the old
    is open) is exactly what the pacer forbids, so it is expected NO-EFFECT too. A NO-EFFECT here is the
    fix's prediction, not a missed trigger; the evictions are the score.

Usage (as the census):
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 LIBTORCH= LD_LIBRARY_PATH= \\
        /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/2026-10-08_f058_census_v2_on_pacer_leg.py --out <dir>
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACER_FEED = "..metrics-panel-metrics-store.data...metrics-store-ack.data.."


def main():
    spec = importlib.util.spec_from_file_location("f058_census_v2_live", HERE / "2026-10-04_f058_census_v2_live.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.FEED = PACER_FEED
    return mod.main()


if __name__ == "__main__":
    sys.exit(main())
