#!/usr/bin/env python
"""Drive cascor's staged start against a REAL juniper-data with each spelling of ``allow_truncation``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#690's fixup (``_as_bool_stance`` reads the value as juniper-data does);
         util/ad-hoc/2026-09-24_cascor690_bool_stance_producer_table.py measured the producer's rule.

usage: 2026-09-24_cascor690_bool_stance_realjd_probe.py <cascor-tree> <juniper-data-url>

Needs a juniper-data server whose import directory holds ``big.csv`` (a small CSV with a ``label``
column); ``max_bytes=40`` puts it over the cap, so juniper-data refuses unless the request opts in.
For each value, with this service's flag off and on, it stages ``csv_import`` and starts, and prints
what the start's failure says: the refusal token, whether it says the request "explicitly refused",
or the plain fetch failure (a 400 for a value juniper-data rejects). Nothing is written except
juniper-data's own storage.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, List
from unittest.mock import patch

VALUES: List[Any] = ["f", "F", "n", "N", "no", "off", "0", 0, False, "t", "y", "true", " true", "maybe", 2]


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    tree, url = argv
    sys.path.insert(0, os.path.join(tree, "src"))
    logging.basicConfig(level=logging.CRITICAL)
    for name in ("", "api", "cascor", "juniper_cascor"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    import api.lifecycle.manager as manager_module

    os.environ["JUNIPER_DATA_URL"] = url
    for flag in ("false", "true"):
        os.environ["JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS"] = flag
        manager_module._TRUNCATABLE_GENERATORS.reset()
        print(f"=== flag={flag}")
        for value in VALUES:
            manager = manager_module.TrainingLifecycleManager()
            try:
                manager.stage_dataset_config(dataset_type="csv_import", params={"file_path": "big.csv", "max_bytes": 40, "allow_truncation": value})
                with patch.object(manager, "_run_training"):
                    try:
                        manager.start_training()
                        out = "STARTED shortfall=" + str((manager.get_status()["dataset_shortfall"] or {}).get("acceptance_source"))
                    except Exception as exc:  # noqa: BLE001 - every failure is the subject here
                        out = str(exc)
            finally:
                manager.shutdown()
            token = out.startswith("[dataset_shortfall_refused]")
            refused = "explicitly refused" in out
            status = "400" if "(400)" in out else "422" if "(422)" in out else "-"
            print(f"  {value!r:9s} jd={status} token={token!s:5s} explicitly_refused={refused!s:5s} | {out[:110]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
