import sys

astral, pair = "\U0001f511", "🔑"
print(sys.version.split()[0], "len(pair)=", len(pair), [hex(ord(c)) for c in pair])
print("astral utf-8        :", astral.encode("utf-8"))
print("pair   surrogatepass:", pair.encode("utf-8", "surrogatepass"))
print("equal:", astral.encode("utf-8") == pair.encode("utf-8", "surrogatepass"))
print("lone hi surrogatepass:", "\ud83d".encode("utf-8", "surrogatepass"), " lone lo:", "\udd11".encode("utf-8", "surrogatepass"))
print("hi+lo concatenated   :", "\ud83d".encode("utf-8", "surrogatepass") + "\udd11".encode("utf-8", "surrogatepass"))
print("decode back of pair bytes:", [hex(ord(c)) for c in pair.encode("utf-8", "surrogatepass").decode("utf-8", "surrogatepass")])
