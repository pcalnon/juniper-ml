"""
Probe the NaN claim carried by juniper-canopy's flood-4 round-2 canopy-tests carrier (#801's correction).

The carrier's docstrings and CHANGELOG say: ``json`` parses every ``NaN`` to one shared float, which list
equality matches by identity, so a ``json_equal`` that compared arrays with ``==`` would not report a matching
NaN as drift. This script measures that with real ``json.loads`` output, for lists, dicts, tuples and nested
structures, through the C scanner and the pure-Python scanner, and through the two exact paths
util/check_juniper_data_generator_schemas.py uses (``load_fixture``'s ``json.loads(read_text())`` and
``upstream_view``'s ``json.loads(json.dumps(schema))``). It also separates container equality (which uses
PyObject_RichCompareBool and so short-circuits on identity) from an element-wise ``x == y`` (which does not).

Prints one JSON object; exit 0 always (it is a measurement, not a gate).

Usage: <python> util/ad-hoc/2026-11-08_flood4r2_val_canopy-tests_nan_identity_probe.py

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-canopy#801 (flood-4 round 2), canopy-tests carrier validation (tests/code/CI lens)
"""

from __future__ import annotations

import json
import json.decoder
import json.scanner
import platform
import sys


def _py_scanner_loads(text: str):
    """Decode with the pure-Python scanner instead of the C accelerator."""
    decoder = json.JSONDecoder()
    decoder.scan_once = json.scanner.py_make_scanner(decoder)
    value, end = decoder.raw_decode(text)
    return value


def main() -> int:
    results: dict = {"python": sys.version.split()[0], "implementation": platform.python_implementation(), "c_scanner": json.scanner.c_make_scanner is not None}

    a = json.loads("NaN")
    b = json.loads("NaN")
    results["two_loads_same_object"] = a is b
    results["loads_is_module_constant"] = a is json.decoder.NaN
    results["scalar_operator_eq_same_object"] = a == b  # float.__eq__: False even for one object
    results["py_scanner_same_object"] = _py_scanner_loads("NaN") is a

    # lists
    results["list_loads_eq"] = json.loads("[NaN]") == json.loads("[NaN]")
    results["list_fresh_floats_eq"] = [float("nan")] == [float("nan")]
    one = float("nan")
    results["list_same_fresh_object_eq"] = [one] == [one]
    # dicts
    results["dict_loads_eq"] = json.loads('{"a": NaN}') == json.loads('{"a": NaN}')
    results["dict_fresh_floats_eq"] = {"a": float("nan")} == {"a": float("nan")}
    # tuples
    results["tuple_fresh_floats_eq"] = (float("nan"),) == (float("nan"),)
    # nested
    nested = '[{"a": [NaN, {"b": NaN}]}]'
    results["nested_loads_eq"] = json.loads(nested) == json.loads(nested)
    results["nested_fresh_floats_eq"] = [{"a": [float("nan"), {"b": float("nan")}]}] == [{"a": [float("nan"), {"b": float("nan")}]}]

    # the drift script's two paths: fixture = json.loads(file text written by json.dumps); upstream = json.loads(json.dumps(schema))
    schema = {"samples": {"default": [float("nan")]}}
    fixture_side = json.loads(json.dumps({"schema": schema}))["schema"]
    upstream_side = json.loads(json.dumps(schema, ensure_ascii=False))
    results["drift_paths_same_object"] = fixture_side["samples"]["default"][0] is upstream_side["samples"]["default"][0]
    results["drift_paths_list_eq"] = fixture_side["samples"]["default"] == upstream_side["samples"]["default"]
    # an element-wise comparison with the == operator does NOT short-circuit on identity
    left, right = fixture_side["samples"]["default"], upstream_side["samples"]["default"]
    results["drift_paths_elementwise_operator_eq"] = len(left) == len(right) and all(x == y for x, y in zip(left, right, strict=True))

    # other non-finite spellings
    try:
        json.loads("-NaN")
        results["minus_nan_parses"] = True
    except ValueError:
        results["minus_nan_parses"] = False
    results["dumps_negative_nan"] = json.dumps(-float("nan"))

    print(json.dumps(results, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
