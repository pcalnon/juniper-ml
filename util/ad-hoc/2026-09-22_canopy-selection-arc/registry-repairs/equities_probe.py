"""Probe for item 11: import resolution, generator version, param defaults, network. Scratch only."""

import socket

import juniper_data
from juniper_data.generators.equities import generator as eq_gen
from juniper_data.generators.equities.defaults import EQUITIES_FEATURE_COLUMNS
from juniper_data.generators.equities.params import EquitiesParams

print("juniper_data file:", juniper_data.__file__)
print("equities VERSION:", eq_gen.EquitiesGenerator.VERSION if hasattr(eq_gen.EquitiesGenerator, "VERSION") else getattr(eq_gen, "VERSION", "?"))
print("feature columns:", len(EQUITIES_FEATURE_COLUMNS), list(EQUITIES_FEATURE_COLUMNS))
params = EquitiesParams(symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"], fundamentals_fill="drop", normalize_features=True)
dump = params.model_dump()
for key in ("start_date", "end_date", "max_symbols", "allow_truncation", "use_cache", "train_ratio", "val_ratio", "one_hot_labels", "feature_columns", "fundamentals_fill", "normalize_features"):
    print(f"  {key} = {dump.get(key)!r}")

for host in ("query1.finance.yahoo.com", "www.sec.gov"):
    try:
        with socket.create_connection((host, 443), timeout=5):
            print("network OK:", host)
    except OSError as exc:
        print("network FAIL:", host, type(exc).__name__, exc)
