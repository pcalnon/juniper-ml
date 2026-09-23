#!/usr/bin/env python
"""Read git OBJECTS (loose and packed, with deltas) directly from an object store -- no git process.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy canopy#670 round-2 review (Lane B); F-CANOPY-054

WHY. The round-2 review of canopy#670 must read the frozen local commit (85415f3c) from git objects,
not from the fix worktree's working tree (a mutation check rewrites it concurrently), and this
review session is worktree-isolated: it may not run git against another repository. Object files
are plain zlib streams, so reading them is a file read, not a git operation.

Supports: loose objects; pack files with a v2 .idx (every pack under objects/pack is scanned);
OFS_DELTA and REF_DELTA; prefix resolution; commit -> tree -> path lookup; recursive tree diff.

Usage:
    python3 util/ad-hoc/2026-09-23_f054_r2_laneB_gitobj.py --objects <.git/objects> show <commit>:<path> [--out FILE]
    python3 util/ad-hoc/2026-09-23_f054_r2_laneB_gitobj.py --objects <.git/objects> changed <commitA> <commitB>
    python3 util/ad-hoc/2026-09-23_f054_r2_laneB_gitobj.py --objects <.git/objects> commit <commit>
"""

import argparse
import struct
import sys
import zlib
from pathlib import Path

TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag", 6: "ofs_delta", 7: "ref_delta"}


class Store:
    def __init__(self, objects_dir: str):
        self.root = Path(objects_dir)
        self.packs = []
        for idx in sorted((self.root / "pack").glob("*.idx")):
            self.packs.append(self._load_idx(idx))

    # ------------------------------------------------------------------ index
    @staticmethod
    def _load_idx(idx_path: Path):
        data = idx_path.read_bytes()
        assert data[:4] == b"\xfftOc" and struct.unpack(">I", data[4:8])[0] == 2, f"{idx_path}: not a v2 idx"
        fanout = struct.unpack(">256I", data[8 : 8 + 1024])
        n = fanout[255]
        off = 8 + 1024
        shas = [data[off + 20 * i : off + 20 * (i + 1)] for i in range(n)]
        off += 20 * n
        off += 4 * n  # crc32
        offs = list(struct.unpack(f">{n}I", data[off : off + 4 * n]))
        off += 4 * n
        large_off = off
        for i, o in enumerate(offs):
            if o & 0x80000000:
                j = o & 0x7FFFFFFF
                offs[i] = struct.unpack(">Q", data[large_off + 8 * j : large_off + 8 * (j + 1)])[0]
        return {"pack": idx_path.with_suffix(".pack"), "map": {s.hex(): o for s, o in zip(shas, offs)}, "data": None}

    # ------------------------------------------------------------------ resolve
    def resolve(self, prefix: str) -> str:
        prefix = prefix.lower()
        hits = set()
        d = self.root / prefix[:2]
        if d.is_dir():
            for f in d.iterdir():
                if (prefix[:2] + f.name).startswith(prefix):
                    hits.add(prefix[:2] + f.name)
        for p in self.packs:
            for s in p["map"]:
                if s.startswith(prefix):
                    hits.add(s)
        if len(hits) != 1:
            raise KeyError(f"{prefix}: {len(hits)} matches")
        return hits.pop()

    # ------------------------------------------------------------------ read
    def read(self, sha: str):
        sha = self.resolve(sha) if len(sha) < 40 else sha
        loose = self.root / sha[:2] / sha[2:]
        if loose.exists():
            raw = zlib.decompress(loose.read_bytes())
            header, _, body = raw.partition(b"\0")
            kind = header.split(b" ")[0].decode()
            return kind, body
        for p in self.packs:
            if sha in p["map"]:
                if p["data"] is None:
                    p["data"] = p["pack"].read_bytes()
                return self._read_packed(p, p["map"][sha])
        raise KeyError(sha)

    def _read_packed(self, p, offset):
        data = p["data"]
        pos = offset
        c = data[pos]
        pos += 1
        kind = (c >> 4) & 7
        size = c & 15
        shift = 4
        while c & 0x80:
            c = data[pos]
            pos += 1
            size |= (c & 0x7F) << shift
            shift += 7
        if kind == 6:  # OFS_DELTA
            c = data[pos]
            pos += 1
            base_off = c & 0x7F
            while c & 0x80:
                c = data[pos]
                pos += 1
                base_off = ((base_off + 1) << 7) | (c & 0x7F)
            base_kind, base = self._read_packed(p, offset - base_off)
            delta = zlib.decompressobj().decompress(data[pos:])
            return base_kind, self._apply(base, delta)
        if kind == 7:  # REF_DELTA
            base_sha = data[pos : pos + 20].hex()
            pos += 20
            base_kind, base = self.read(base_sha)
            delta = zlib.decompressobj().decompress(data[pos:])
            return base_kind, self._apply(base, delta)
        body = zlib.decompressobj().decompress(data[pos:])
        assert len(body) >= size
        return TYPES[kind], body[:size]

    @staticmethod
    def _apply(base: bytes, delta: bytes) -> bytes:
        pos = 0

        def varint():
            nonlocal pos
            val = shift = 0
            while True:
                c = delta[pos]
                pos += 1
                val |= (c & 0x7F) << shift
                shift += 7
                if not c & 0x80:
                    return val

        src_size = varint()
        dst_size = varint()
        assert src_size == len(base), (src_size, len(base))
        out = bytearray()
        while pos < len(delta):
            op = delta[pos]
            pos += 1
            if op & 0x80:
                cp_off = cp_size = 0
                for i in range(4):
                    if op & (1 << i):
                        cp_off |= delta[pos] << (8 * i)
                        pos += 1
                for i in range(3):
                    if op & (1 << (4 + i)):
                        cp_size |= delta[pos] << (8 * i)
                        pos += 1
                cp_size = cp_size or 0x10000
                out += base[cp_off : cp_off + cp_size]
            elif op:
                out += delta[pos : pos + op]
                pos += op
            else:
                raise ValueError("delta opcode 0")
        assert len(out) == dst_size
        return bytes(out)

    # ------------------------------------------------------------------ trees
    def commit(self, sha):
        kind, body = self.read(sha)
        assert kind == "commit", kind
        headers, _, msg = body.decode("utf-8", "replace").partition("\n\n")
        info = {"tree": None, "parents": [], "message": msg}
        for line in headers.split("\n"):
            if line.startswith("tree "):
                info["tree"] = line[5:]
            elif line.startswith("parent "):
                info["parents"].append(line[7:])
            elif line.startswith(("author ", "committer ")):
                info[line.split(" ")[0]] = line.split(" ", 1)[1]
        return info

    def tree(self, sha):
        kind, body = self.read(sha)
        assert kind == "tree", kind
        out, pos = [], 0
        while pos < len(body):
            sp = body.index(b" ", pos)
            nul = body.index(b"\0", sp)
            mode = body[pos:sp].decode()
            name = body[sp + 1 : nul].decode("utf-8", "replace")
            out.append((mode, name, body[nul + 1 : nul + 21].hex()))
            pos = nul + 21
        return out

    def blob_at(self, commit_sha, path):
        sha = self.commit(commit_sha)["tree"]
        parts = [x for x in path.split("/") if x]
        for i, part in enumerate(parts):
            entries = {name: (mode, s) for mode, name, s in self.tree(sha)}
            if part not in entries:
                raise KeyError(f"{path}: {part} missing")
            mode, sha = entries[part]
        kind, body = self.read(sha)
        assert kind == "blob", kind
        return sha, body

    def flat(self, tree_sha, prefix=""):
        out = {}
        for mode, name, s in self.tree(tree_sha):
            if mode.startswith("4"):  # 40000 = tree
                out.update(self.flat(s, prefix + name + "/"))
            else:
                out[prefix + name] = s
        return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--objects", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("spec")
    s.add_argument("--out")
    c = sub.add_parser("changed")
    c.add_argument("a")
    c.add_argument("b")
    m = sub.add_parser("commit")
    m.add_argument("sha")
    a = ap.parse_args()
    st = Store(a.objects)
    if a.cmd == "show":
        commit, _, path = a.spec.partition(":")
        sha, body = st.blob_at(st.resolve(commit), path)
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_bytes(body)
            print(f"{a.spec} blob {sha} -> {a.out} ({len(body)} bytes)")
        else:
            sys.stdout.buffer.write(body)
    elif a.cmd == "changed":
        fa = st.flat(st.commit(st.resolve(a.a))["tree"])
        fb = st.flat(st.commit(st.resolve(a.b))["tree"])
        for p in sorted(set(fa) | set(fb)):
            if fa.get(p) != fb.get(p):
                status = "A" if p not in fa else "D" if p not in fb else "M"
                print(f"{status} {p}")
    elif a.cmd == "commit":
        info = st.commit(st.resolve(a.sha))
        print(f"sha {st.resolve(a.sha)}\ntree {info['tree']}\nparents {' '.join(info['parents'])}\nauthor {info.get('author')}\n\n{info['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
