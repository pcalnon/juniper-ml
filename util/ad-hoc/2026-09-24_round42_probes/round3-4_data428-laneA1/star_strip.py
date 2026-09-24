"""Lane A1: the '*' sentinel is matched with Python str.strip(), not RFC 9110 OWS.

http_cache._well_formed and _list_names both test ``field.strip() == "*"``. Python's
str.strip() removes every Unicode whitespace char, while RFC 9110 OWS is only SP and HTAB.
So a field that is '*' plus a NON-OWS whitespace char is malformed per the RFC but is read
as '*' here. On a WRITE that fails OPEN: the module's stated contract is that a write fails
closed on a precondition it cannot read, but '*' + such a char makes a PATCH proceed.

This enumerates which of those extra chars are ALSO valid HTTP/1.1 header-value bytes (so
they reach the app rather than being rejected by the parser), then confirms the fix
``field.strip(" \\t")`` restores the RFC behaviour without changing any legal field.
"""

import sys

sys.path.insert(0, "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1/tree-3a76a4c")
from juniper_data.api import http_cache as hc  # noqa: E402

assert hc.__file__.startswith("/tmp/claude-1000/-home-pcalnon")
ETAG = hc.body_etag(b"x")

# All chars Python treats as strippable whitespace.
ws = [c for c in map(chr, range(0x100)) if c.strip() == ""]
print("chars str.strip() removes (0x00-0xFF):", " ".join(f"{ord(c):02x}" for c in ws))

# RFC 9110 field-value bytes: VCHAR (0x21-0x7E), SP (0x20), HTAB (0x09), obs-text (0x80-0xFF).
# So the reachable extra-strip set is {strippable} minus {SP, HTAB} intersected with
# {valid field-value bytes} = obs-text whitespace (0x85 NEL, 0xA0 NBSP) plus any 0x1c-0x1f
# that a lenient parser lets through.
def rfc_field_value_byte(c: str) -> bool:
    o = ord(c)
    return o == 0x09 or o == 0x20 or 0x21 <= o <= 0x7E or 0x80 <= o <= 0xFF


extra = [c for c in ws if c not in (" ", "\t")]
reachable = [c for c in extra if rfc_field_value_byte(c)]
print("over-stripped beyond OWS:", " ".join(f"{ord(c):02x}" for c in extra))
print("of those, valid HTTP field-value bytes (reach the app):", " ".join(f"{ord(c):02x}" for c in reachable))

print("\ncurrent code (str.strip): '*'+ch treated as '*'?  and the write direction:")
for c in reachable:
    star = "*" + c
    read_304 = hc.if_none_match_hits(star, ETAG)          # read: names current -> 304
    write_412 = hc.if_none_match_fails_write(star, ETAG)  # write: fails closed?
    im_fail = hc.if_match_fails(star, ETAG)               # If-Match: fails?
    proceeds = hc.write_preconditions_hold(star, star, ETAG)
    print(f"  0x{ord(c):02x}: well_formed={hc._well_formed(star)} INM_hits(read)={read_304} INM_fails_write={write_412} IM_fails={im_fail} write_preconditions_hold={proceeds}")

print("\nproposed fix -- strip only OWS (' \\t'):")
import re  # noqa: E402


def well_formed_fixed(field: str) -> bool:
    if len(field) > hc.MAX_PRECONDITION_FIELD_LENGTH:
        return False
    return field.strip(" \t") == "*" or hc._ENTITY_TAG_LIST.fullmatch(field) is not None


# every legal field keeps its verdict; every '*'+obs-ws becomes malformed
legal = ["*", "  *  ", "\t*\t", '"abc"', 'W/"abc"', '"a", "b"', '"a", , "b"', "", "   ", '"a,b"']
changed = 0
for f in legal:
    if well_formed_fixed(f) != hc._well_formed(f):
        print("  REGRESSION on legal field:", repr(f))
        changed += 1
for c in reachable:
    if well_formed_fixed("*" + c):
        print("  fix still accepts '*'+0x%02x" % ord(c))
        changed += 1
print("  legal fields unchanged, all '*'+obs-ws now malformed" if changed == 0 else f"  {changed} problems")
