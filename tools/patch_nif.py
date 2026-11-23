#!/usr/bin/env python3
"""Apply the Nexus 60968 collision-flag edit to a prisonercarriage01.nif.

Confirmed by diffing official 60968 files against their sources:

* SMIM 2.08 source vs "Prisoner Cart Opening Fix - SMIM 2.08 Patch" 1.1
  (Nexus 60968 file 252759)
* Ruins Clutter Improved 3.2c vs "… RCI 3.2a Patch" 1.2 (file 252968)
  — payload-identical change; the 3.2a/3.2c version skew did not add
  other block-data diffs

In both pairs the only block-data change is on the root cart body:

  BSFadeNode -> bhkCollisionObject -> bhkRigidBody
    Havok Filter        "Flags and Part Numbers" (byte at block+5)  0 -> 224
    Havok Filter Copy   "Flags and Part Numbers" (byte at block+37) 0 -> 224

That packed HavokFilter uint32 goes from 0x0000000A (layer 10, flags 0)
to 0x0000E00A (layer 10, flags 224). 224 == 0b11100000, as documented
on Nexus 60968.

NifSkope re-saves also reorder the NIF type-name list (BSTriShape vs
BSLightingShaderProperty); those header index diffs are incidental and
are not copied. This script changes only the two flag bytes.
"""
from __future__ import annotations
import argparse, hashlib, struct, sys
from pathlib import Path

FLAG_OFFS = (5, 37)  # Flags and Part Numbers inside the two HavokFilter structs
VALUE = 224


def parse_blocks(data: bytes):
    nl = data.find(b"\n")
    i = nl + 1
    ver, endian, user, nblocks, user2 = struct.unpack_from("<IBIII", data, i)
    i += 17
    if ver != 0x14020007:
        raise SystemExit(f"unexpected NIF version {ver:#x}")

    def shortstring(i):
        ln = data[i]
        i += 1
        s = data[i : i + ln]
        i += ln
        return s.split(b"\x00")[0].decode("latin1", "replace"), i

    _author, i = shortstring(i)
    _e1, i = shortstring(i)
    _e2, i = shortstring(i)
    ntypes = struct.unpack_from("<H", data, i)[0]
    i += 2
    types = []
    for _ in range(ntypes):
        ln = struct.unpack_from("<I", data, i)[0]
        i += 4
        types.append(data[i : i + ln].split(b"\x00")[0].decode())
        i += ln
    tindex = list(struct.unpack_from("<" + "H" * nblocks, data, i))
    i += 2 * nblocks
    sizes = list(struct.unpack_from("<" + "I" * nblocks, data, i))
    i += 4 * nblocks
    nstr = struct.unpack_from("<I", data, i)[0]
    i += 4
    _maxlen = struct.unpack_from("<I", data, i)[0]
    i += 4
    for _ in range(nstr):
        ln = struct.unpack_from("<I", data, i)[0]
        i += 4 + ln
    ngroups = struct.unpack_from("<I", data, i)[0]
    i += 4 + 4 * ngroups
    blocks = []
    off = i
    for bi, (ti, sz) in enumerate(zip(tindex, sizes)):
        blocks.append({"i": bi, "type": types[ti], "off": off, "size": sz})
        off += sz
    return blocks


def find_root_body(data: bytes, blocks):
    fade = blocks[0]
    if fade["type"] != "BSFadeNode":
        raise SystemExit(f"block 0 is {fade['type']}, not BSFadeNode")
    blob = data[fade["off"] : fade["off"] + fade["size"]]
    coll = None
    for off in range(0, len(blob) - 3):
        v = struct.unpack_from("<i", blob, off)[0]
        if 0 <= v < len(blocks) and blocks[v]["type"] == "bhkCollisionObject":
            coll = v
            break
    if coll is None:
        raise SystemExit("BSFadeNode has no bhkCollisionObject ref")
    cblob = data[blocks[coll]["off"] : blocks[coll]["off"] + blocks[coll]["size"]]
    body = None
    for off in range(0, len(cblob) - 3):
        v = struct.unpack_from("<i", cblob, off)[0]
        if 0 <= v < len(blocks) and blocks[v]["type"] == "bhkRigidBody":
            body = v
            break
    if body is None:
        raise SystemExit("bhkCollisionObject has no bhkRigidBody ref")
    return blocks[body]


def patch(src: Path, dst: Path) -> None:
    raw = bytearray(src.read_bytes())
    body = find_root_body(bytes(raw), parse_blocks(bytes(raw)))
    locs = [body["off"] + o for o in FLAG_OFFS]
    for loc in locs:
        old = raw[loc]
        if old not in (0, VALUE):
            raise SystemExit(f"unexpected flags byte {old} at file+{loc}")
        raw[loc] = VALUE
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(raw)
    orig = src.read_bytes()
    new = bytes(raw)
    ch = [(i, orig[i], new[i]) for i in range(len(orig)) if orig[i] != new[i]]
    expected = [(locs[0], 0, VALUE), (locs[1], 0, VALUE)] if orig[locs[0]] == 0 else []
    # if already patched, ch may be empty
    print("src", src, "md5", hashlib.md5(orig).hexdigest(), "size", len(orig))
    print("dst", dst, "md5", hashlib.md5(new).hexdigest(), "size", len(new))
    print("body block", body["i"], "file offs", locs, "diffs", ch)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    args = ap.parse_args()
    patch(Path(args.src), Path(args.dst))


if __name__ == "__main__":
    main()
