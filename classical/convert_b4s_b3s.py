#!/usr/bin/env python3
"""Convert Rapfi classical model .bin files from the 14-pattern to the 16-pattern
pcode layout (B4S/B3S refinement, 2026-07). Behavior-preserving: every new pcode
inherits the weights of its parent multiset (B4S->B4, B3S->B3).

Usage:
    python convert_b4s_b3s.py model210901.bin model220723.bin   # convert in place
    python convert_b4s_b3s.py --emit-tables   # print expanded internalConfig.cpp arrays
"""
import sys

import lz4.frame

OLD_N, NEW_N = 14, 16
OLD_PC, NEW_PC = 2380, 3876          # C(N+3, 4)
THREAT_NB = 2048
NUM_TABLES = 4                       # RULE_NB + 1 (renju has separate black/white slots)
# new pattern index -> old pattern index (B3S(9)->B3(8), B4S(13)->B4(11))
PARENT = [0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 10, 11, 11, 12, 13]

OLD_RAW = 8 + NUM_TABLES * OLD_PC * 2 + NUM_TABLES * THREAT_NB * 2 + NUM_TABLES * OLD_PC * 4
NEW_RAW = 8 + NUM_TABLES * NEW_PC * 2 + NUM_TABLES * THREAT_NB * 2 + NUM_TABLES * NEW_PC * 4
assert (OLD_RAW, NEW_RAW) == (73512, 109416)


def dense_codes(n):
    """Dense pcode of every non-decreasing 4-tuple, lexicographic order —
    replicates fillPatternCodeLUT pass 1 in game/pattern.cpp."""
    codes, c = {}, 0
    for a in range(n):
        for b in range(a, n):
            for d in range(b, n):
                for e in range(d, n):
                    codes[(a, b, d, e)] = c
                    c += 1
    return codes


def build_remap():
    old_codes, new_codes = dense_codes(OLD_N), dense_codes(NEW_N)
    assert len(old_codes) == OLD_PC and len(new_codes) == NEW_PC
    remap = [None] * NEW_PC
    for tup, nc in new_codes.items():
        parent = tuple(sorted(PARENT[x] for x in tup))  # PARENT is monotone: stays sorted
        remap[nc] = old_codes[parent]
    assert sorted(set(remap)) == list(range(OLD_PC))    # surjective onto old codes
    # identity-embedded multisets keep their values: all-DEAD maps to code 0
    assert remap[new_codes[(0, 0, 0, 0)]] == old_codes[(0, 0, 0, 0)] == 0
    return remap


def remap_block(raw, remap, unit):
    out = bytearray(len(remap) * unit)
    for nc, oc in enumerate(remap):
        out[nc * unit:(nc + 1) * unit] = raw[oc * unit:(oc + 1) * unit]
    return bytes(out)


def convert(path, remap):
    raw = lz4.frame.decompress(open(path, 'rb').read())
    if len(raw) == NEW_RAW:
        print(f'{path}: already converted ({NEW_RAW} bytes), skipping')
        return
    assert len(raw) == OLD_RAW, f'{path}: unexpected decompressed size {len(raw)}'
    out, off = bytearray(), 0
    out += raw[off:off + 8]; off += 8                                    # scaling factor
    for _ in range(NUM_TABLES):                                          # EVALS (int16)
        out += remap_block(raw[off:off + OLD_PC * 2], remap, 2); off += OLD_PC * 2
    n = NUM_TABLES * THREAT_NB * 2                                       # EVALS_THREAT: copy
    out += raw[off:off + n]; off += n
    for _ in range(NUM_TABLES):                                          # scores[pcode][2] (2x int16)
        out += remap_block(raw[off:off + OLD_PC * 4], remap, 4); off += OLD_PC * 4
    assert off == len(raw) and len(out) == NEW_RAW
    with open(path, 'wb') as f:
        f.write(lz4.frame.compress(bytes(out), content_checksum=True))
    print(f'{path}: {OLD_RAW} -> {NEW_RAW} bytes (decompressed), OK')


# ---- --emit-tables: expanded internalConfig.cpp arrays (spec section 5) ----
# Old 14-pattern values copied verbatim from Rapfi/internalConfig.cpp.
OLD_TABLE1 = [-1, 0, 0, 1, 2, 6, 6, 6, 9, 16, 20, 30, 100, 500]
OLD_TABLE2_EVAL = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 36, 41,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 36, 41,
    0, 0, 0, 1, 1, 1, 2, 9, 9, 16, 36, 41,
    0, 0, 1, 1, 1, 2, 10, 10, 17, 38, 43,
    1, 2, 2, 2, 3, 11, 11, 19, 39, 44,
    3, 3, 3, 4, 13, 13, 20, 42, 47,
    3, 3, 4, 13, 13, 20, 42, 47,
    3, 4, 13, 13, 20, 42, 47,
    5, 14, 14, 22, 43, 49,
    25, 25, 34, 57, 62,
    25, 34, 57, 62,
    43, 67, 72,
    93, 99,
    105,
]
OLD_TABLE2_EVAL_RENJU = [
    0, 0, 0, 0, 0, 1, 1, 1, 2, 9, 9, 15, 36, 40,
    0, 0, 0, 0, 1, 1, 1, 2, 9, 9, 15, 36, 40,
    0, 0, 0, 1, 1, 1, 2, 9, 9, 15, 36, 40,
    0, 0, 1, 1, 1, 2, 9, 9, 15, 37, 40,
    1, 2, 2, 2, 3, 10, 10, 17, 38, 42,
    3, 3, 3, 4, 12, 12, 18, 40, 44,
    3, 3, 4, 12, 12, 18, 40, 44,
    3, 4, 12, 12, 18, 40, 44,
    5, 13, 13, 20, 42, 46,
    23, 23, 30, 54, 58,
    23, 30, 54, 58,
    38, 63, 67,
    90, 94,
    99,
]


def tri_index(y, x, n):
    """Upper-triangular index, mirrors I(y,x) in Rapfi/config.cpp (x >= y)."""
    return y * n + x - y * (y + 1) // 2


def expand_table2(old):
    assert len(old) == tri_index(OLD_N - 1, OLD_N - 1, OLD_N) + 1 == 105
    new = [0] * 136
    for a in range(NEW_N):
        for b in range(a, NEW_N):
            pa, pb = PARENT[a], PARENT[b]
            new[tri_index(a, b, NEW_N)] = old[tri_index(min(pa, pb), max(pa, pb), OLD_N)]
    return new


def emit_tables():
    print('table1 = [' + ','.join(str(OLD_TABLE1[PARENT[i]]) for i in range(NEW_N)) + ']')
    for name, old in (('[model.eval] table2', OLD_TABLE2_EVAL),
                      ('[model.eval.renju] table2', OLD_TABLE2_EVAL_RENJU)):
        vals, idx, rows = expand_table2(old), 0, []
        for a in range(NEW_N):
            row = vals[idx:idx + NEW_N - a]
            idx += NEW_N - a
            rows.append('\t' * a + ',\t'.join(map(str, row)) + (',' if a < NEW_N - 1 else ''))
        print(f'\n# {name} (136 values)')
        print('\n'.join(rows))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == '--emit-tables':
        emit_tables()
        sys.exit(0)
    m = build_remap()
    for p in sys.argv[1:]:
        convert(p, m)
