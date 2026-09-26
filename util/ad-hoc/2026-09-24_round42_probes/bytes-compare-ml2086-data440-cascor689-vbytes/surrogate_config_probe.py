"""Can a lone surrogate actually reach APIKeyAuth through the services' own settings? (the deviation's premise)"""
import os
import sys

which, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
BS = chr(92)
json_value = '["' + BS + "ud800-key" + '", "ok-key"]'  # the JSON text  ["\ud800-key", "ok-key"]
print("env value (JSON text):", json_value)
if which == "data":
    os.environ["JUNIPER_DATA_API_KEYS"] = json_value
    from juniper_data.api.settings import Settings

    keys = Settings().api_keys
else:
    os.environ["JUNIPER_CASCOR_API_KEYS"] = json_value
    from api.settings import Settings

    keys = Settings().api_keys
print("parsed api_keys:", [ascii(k) for k in (keys or [])])
lone = [k for k in (keys or []) if any(0xD800 <= ord(c) <= 0xDFFF for c in k)]
print("a lone surrogate survived settings parsing:", bool(lone))
if lone:
    try:
        lone[0].encode("utf-8", "surrogateescape")
        print("surrogateescape: ok")
    except UnicodeEncodeError as exc:
        print("surrogateescape would RAISE on it:", type(exc).__name__)
    print("surrogatepass:", lone[0].encode("utf-8", "surrogatepass"))
