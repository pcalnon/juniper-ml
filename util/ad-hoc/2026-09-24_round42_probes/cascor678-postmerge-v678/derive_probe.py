"""Feed the real juniper-data listing JSON to cascor's derive(), plus edge cases (read-only)."""
import copy
import json
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v678"
sys.path.insert(0, S + "/cascor/src")
from api.lifecycle.manager import _TruncatableGenerators  # noqa: E402

listing = json.load(open(S + "/jd_listing.json"))
print("derived from real listing:", sorted(_TruncatableGenerators.derive(listing)))

# available: false -> still derived? (juniper-data lists a schema for unavailable generators too)
l2 = copy.deepcopy(listing)
for e in l2:
    if e["name"] == "equities":
        e["available"] = False
print("equities available=false:", sorted(_TruncatableGenerators.derive(l2)))

# listing omits schema entirely for one entry
l3 = copy.deepcopy(listing)
for e in l3:
    if e["name"] == "equities":
        del e["schema"]
print("equities schema omitted:", sorted(_TruncatableGenerators.derive(l3)))

# listing omits schema for ALL entries (e.g. a producer that stops publishing it)
l4 = copy.deepcopy(listing)
for e in l4:
    e.pop("schema", None)
print("ALL schemas omitted:", sorted(_TruncatableGenerators.derive(l4)), "(empty set -> memoised as a success)")

# params_schema key instead of schema (by_alias=False serialisation)
l5 = copy.deepcopy(listing)
for e in l5:
    e["params_schema"] = e.pop("schema")
print("params_schema key instead of schema:", sorted(_TruncatableGenerators.derive(l5)))

# empty list
print("empty list:", sorted(_TruncatableGenerators.derive([])))
