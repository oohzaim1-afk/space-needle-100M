#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bb6blocks.py — block-affine re-derivation of the Space Needle trajectory (BB(6)).

Reduced recurrence (Doucette's higher-level rule; see README):
    b0 = 6;  b_{n+1} = b_n + v2(b_n) + 3/2 * (b_n / 2^v2(b_n) - 1)
    HALT iff b_n is a power of 2 (odd part == 1).

For v = v2(b), one step is the exact affine map
    b -> (b * A_v + C_v) >> (v+1),    A_v = 2^(v+1) + 3,   C_v = (2*v - 3) * 2^v
so k consecutive steps compose into a single affine map b -> (A*b + C) >> S.
The v-sequence of a k-step block is determined by the low ~2k bits of b
(reduced-precision window simulation, O(k^2/64) machine words), after which
ONE large multiplication advances the full integer.  Values are identical to
the per-term recurrence; only the cost profile changes.

Modes:
    bb6blocks.py selftest
    bb6blocks.py run N [k] [check_every] [outdir] [ref_csv]

run mode outputs (in outdir/):
    checkpoints.csv         n,bits,max_v2,fnv1a64,decimal_digits,elapsed_s
    sha256_checkpoints.csv  n,bits,sha256_bigendian
    hist_v2.csv             v,count,expected_geometric   (v2 histogram, 100M terms)
    final_term.bin          final b, big-endian minimal bytes (canonical encoding)
    final_term.sha256       hashes + metadata
    run_info.txt            parameters, timings, ref comparison, records, final stats

ref_csv (optional): published checkpoint file with `n,bits,max_v2,fnv1a64`
(e.g. data/gmp_100M.csv); every overlapping checkpoint is compared and a
mismatch aborts the run.

Author: Seiji.  License: MIT.  Optional accelerator: gmpy2 (≈10x faster big
multiplications); falls back to pure-stdlib bigint when gmpy2 is unavailable.
"""

import hashlib
import math
import os
import sys
import time
from decimal import Decimal, getcontext

try:
    import gmpy2
    mpz = gmpy2.mpz
    HAVE_GMPY2 = True
except ImportError:
    gmpy2 = None
    mpz = int
    HAVE_GMPY2 = False

getcontext().prec = 80
LOG10_2 = Decimal('0.30102999566398119521373889472449302676818988146210854131')

MASK64 = (1 << 64) - 1
FNV_OFF = 0xcbf29ce484222325
FNV_PRIME = 0x100000001b3
LOGD = math.log(10.0)

EXPECTED_RECORDS = [
    (1, 1), (4, 9), (6, 15), (9, 51), (11, 398), (12, 1022), (14, 9733),
    (15, 47101), (17, 158832), (18, 1048553), (21, 1181825), (24, 1860962),
    (25, 23145881),
]


# ---------------------------------------------------------------- helpers

def v2(x):
    """2-adic valuation of x > 0."""
    return (x & -x).bit_length() - 1


def fnv1a64(ib):
    """FNV-1a 64 over little-endian 64-bit limbs of a positive int."""
    raw = ib.to_bytes(((ib.bit_length() + 63) // 64) * 8, 'little')
    h = FNV_OFF
    try:
        mv = memoryview(raw).cast('Q')
        for w in mv:
            h = ((h ^ w) * FNV_PRIME) & MASK64
    except (TypeError, ValueError):
        import struct
        for (w,) in struct.iter_unpack('<Q', raw):
            h = ((h ^ w) * FNV_PRIME) & MASK64
    return h


def sha256_bigendian(ib):
    """SHA-256 of the big-endian minimal-byte encoding of ib (canonical)."""
    nb = (ib.bit_length() + 7) // 8 or 1
    return hashlib.sha256(ib.to_bytes(nb, 'big')).hexdigest()


def decimal_digits(ib):
    """Exact number of decimal digits of ib: floor(log10(ib)) + 1.

    Uses an 80-digit Decimal estimate from the top 64 bits; falls back to an
    exact big-int comparison in the astronomically rare near-integer case.
    """
    if ib < 10:
        return 1
    bits = ib.bit_length()
    if bits <= 64:
        return len(str(ib))
    sh = bits - 64
    top = ib >> sh
    lg = Decimal(bits - 64) * LOG10_2 + (Decimal(top).ln() / Decimal(10).ln())
    d = int(lg) + 1
    frac = lg - int(lg)
    # |estimate - log10(ib)| <~ 3e-20 (truncated mantissa + Decimal rounding),
    # so any frac farther than 1e-15 from an integer is unambiguous.
    if frac < Decimal('1e-15') or frac > 1 - Decimal('1e-15'):
        p = 10 ** (d - 1)          # verify 10^(d-1) <= ib < 10^d exactly
        if ib < p:
            d -= 1
        elif ib >= p * 10:
            d += 1
    return d


def step_params(v):
    s = v + 1
    return (1 << s) + 3, ((2 * v - 3) << v), s


def block_terms(y, k, w):
    """Reduced-precision simulation of k steps on window y (low w bits of b).

    Returns (vs, A, C, S, cands) or None when the window is insufficient.
      vs    : v value per step (exact, provided the window certified it)
      (A,C,S): composed affine map b -> (A*b + C) >> S for the k steps
      cands : (j, v) where the window is the single bit 2^v (halt candidate,
              must be re-tested exactly against the full integer)
    """
    A = 1
    C = 0
    S = 0
    vs = []
    cands = []
    prec = w
    for j in range(k):
        if not y:
            return None
        t = y & -y
        v = t.bit_length() - 1
        s = v + 1
        if s > prec:
            return None
        vs.append(v)
        if y == t:
            cands.append((j, v))
        a = (1 << s) + 3
        c = (2 * v - 3) << v
        A = a * A
        C = a * C + (c << S)
        S += s
        prec -= s
        y = ((a * y + c) >> s) & ((1 << prec) - 1)
    return vs, A, C, S, cands


def compose_vs(vs):
    """Composed affine map for a list of v values (map: b -> (A*b + C) >> S)."""
    A = 1
    C = 0
    S = 0
    for v in vs:
        a, c, s = step_params(v)
        A = a * A
        C = a * C + (c << S)
        S += s
    return A, C, S


def naive_run(b0, n):
    """Direct per-term run.  Returns (b_final, vs, records, max_v2, halt_pos)."""
    b = int(b0)
    vs = []
    records = []
    mx = 0
    halt = None
    for i in range(1, n + 1):
        t = b & -b
        v = t.bit_length() - 1
        vs.append(v)
        if v > mx:
            mx = v
            records.append((v, i))
        if b == t:
            halt = i
            break
        m = b >> v
        b = b + v + 3 * (m >> 1)
    return b, vs, records, mx, halt


class HaltFound(Exception):
    def __init__(self, pos, val):
        self.pos = pos
        self.val = val


# ---------------------------------------------------------------- run

def _window_extract(b, w):
    return int(b & ((1 << w) - 1))


def _advance(b, A, C, S, where):
    num = mpz(A) * b + C
    if (num & ((mpz(1) << S) - 1)) != 0:
        raise SystemExit("ERROR: non-exact composed division at %s" % where)
    return num >> S


def main_run(N, k, ce, outdir, ref_path):
    sys.set_int_max_str_digits(0)
    t_start = time.time()
    os.makedirs(outdir, exist_ok=True)
    logf = open(os.path.join(outdir, "run_info.txt"), "w", encoding="utf-8")
    ckf = open(os.path.join(outdir, "checkpoints.csv"), "w", encoding="utf-8")
    shf = open(os.path.join(outdir, "sha256_checkpoints.csv"), "w", encoding="utf-8")

    def emit(s):
        print(s, flush=True)
        logf.write(s + "\n")
        logf.flush()

    emit("# bb6blocks.py — block-affine re-derivation")
    emit("# started        : " + time.strftime("%Y-%m-%d %H:%M:%S"))
    emit("# N=%d k=%d check_every=%d" % (N, k, ce))
    emit("# python         : " + sys.version.replace("\n", " "))
    emit("# gmpy2          : " + (gmpy2.version() if HAVE_GMPY2 else "not available (stdlib int)"))
    emit("# outdir         : " + os.path.abspath(outdir))
    ref = {}
    if ref_path and os.path.exists(ref_path):
        with open(ref_path, encoding="utf-8") as rf:
            for line in rf:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                p = line.split(",")
                if len(p) >= 4:
                    ref[int(p[0])] = (int(p[1]), int(p[2]), p[3].lower())
        emit("# reference      : %s (%d rows)" % (os.path.abspath(ref_path), len(ref)))
    else:
        emit("# reference      : none")

    ckf.write("n,bits,max_v2,fnv1a64,decimal_digits,elapsed_s\n")
    shf.write("n,bits,sha256_bigendian\n")

    b = mpz(6)
    done = 0
    max_v2 = 0
    records = []
    hist = [0] * 64
    hist_overflow = 0
    ref_match = 0
    ref_mismatch = 0
    n_ck = 0
    digits_cross_ok = True
    digits_cross_n = 0
    halted = None  # (pos, val)

    try:
        while done < N:
            next_ck = ((done // ce) + 1) * ce
            kk = min(k, N - done, next_ck - done)
            if kk <= 0:
                kk = min(k, N - done)
            # ---- window simulation (with adaptive margin)
            w = 2 * kk + 2048
            res = None
            for _attempt in range(12):
                y = _window_extract(b, w)
                res = block_terms(y, kk, w)
                if res is not None:
                    break
                w *= 2
            if res is None:
                # exact fallback (never expected in practice)
                ib = int(b)
                vs = []
                for j in range(kk):
                    t = ib & -ib
                    v = t.bit_length() - 1
                    vs.append(v)
                    if ib == t:
                        raise HaltFound(done + j + 1, ib)
                    m = ib >> v
                    ib = ib + v + 3 * (m >> 1)
                A = C = None
                b = mpz(ib)
            else:
                vs, A, C, S, cands = res
                # ---- halt candidates (exact re-test; never expected to fire)
                for (j, v) in cands:
                    A2, C2, S2 = compose_vs(vs[:j])
                    val = (mpz(A2) * b + C2) >> S2
                    if (val & (val - 1)) == 0:
                        raise HaltFound(done + j + 1, int(val))
                # ---- advance full integer
                b = _advance(b, A, C, S, "done=%d" % done)
            # ---- bookkeeping for the kk pre-update terms (positions done+1..done+kk)
            for j in range(kk):
                v = vs[j]
                if v < 64:
                    hist[v] += 1
                else:
                    hist_overflow += 1
                if v > max_v2:
                    max_v2 = v
                    records.append((v, done + j + 1))
            done += kk
            # ---- checkpoint
            if done % ce == 0:
                ib = int(b)
                bits = ib.bit_length()
                fnv = fnv1a64(ib)
                sha = sha256_bigendian(ib)
                dg = decimal_digits(ib)
                if dg <= 5_000_000:  # cheap exact cross-check when affordable
                    digits_cross_n += 1
                    if len(str(ib)) != dg:
                        digits_cross_ok = False
                        emit("DIGITS CROSS-CHECK FAILED at n=%d" % done)
                el = time.time() - t_start
                ckf.write("%d,%d,%d,%016x,%d,%.1f\n" % (done, bits, max_v2, fnv, dg, el))
                ckf.flush()
                shf.write("%d,%d,%s\n" % (done, bits, sha))
                shf.flush()
                n_ck += 1
                if done in ref:
                    rb, rmv, rfnv = ref[done]
                    if (bits, max_v2, "%016x" % fnv) != (rb, rmv, rfnv):
                        ref_mismatch += 1
                        emit("REF MISMATCH n=%d: got bits=%d max_v2=%d fnv=%016x | "
                             "expected bits=%d max_v2=%d fnv=%s" %
                             (done, bits, max_v2, fnv, rb, rmv, rfnv))
                        raise SystemExit(4)
                    ref_match += 1
                emit("ck n=%d bits=%d max_v2=%d fnv=%016x digits=%d t=%.1fs" %
                     (done, bits, max_v2, fnv, dg, el))
    except HaltFound as h:
        halted = (h.pos, h.val)
        emit("HALT_CONDITION_MET at position %d (value has %d bits)" %
             (h.pos, h.val.bit_length()))

    # ---------------------------------------------------------------- final
    ib = int(b)
    bits = ib.bit_length()
    vf = v2(ib)
    pow2 = (ib >> vf) == 1
    fnv = fnv1a64(ib)
    sha_bin = sha256_bigendian(ib)
    sdec = str(ib)
    sha_dec = hashlib.sha256(sdec.encode('ascii')).hexdigest()
    dg = len(sdec)
    dg_method = decimal_digits(ib)
    raw = ib.to_bytes((bits + 7) // 8, 'big')
    with open(os.path.join(outdir, "final_term.bin"), "wb") as f:
        f.write(raw)
    with open(os.path.join(outdir, "final_term.sha256"), "w", encoding="utf-8") as f:
        f.write("# Space Needle (BB(6)) — final term after %d updates (position %d)\n"
                % (done, done + 1))
        f.write("# canonical encoding: big-endian minimal bytes (%d bytes, %d bits)\n"
                % (len(raw), bits))
        f.write("%s  final_term.bin\n" % sha_bin)
        f.write("# decimal-string encoding (%d digits, ASCII, no separators); hash only\n" % dg)
        f.write("%s  final_term.dec.txt\n" % sha_dec)
        f.write("# FNV-1a 64 over little-endian 64-bit limbs: %016x\n" % fnv)
        f.write("# v2(final)=%d  power_of_2=%s\n" % (vf, pow2))
    with open(os.path.join(outdir, "hist_v2.csv"), "w", encoding="utf-8") as f:
        f.write("v,count,expected_geometric\n")
        n_obs = sum(hist) + hist_overflow
        for v in range(64):
            f.write("%d,%d,%.3f\n" % (v, hist[v], n_obs * 2.0 ** -(v + 1)))
        f.write("64plus,%d,%.3f\n" % (hist_overflow, n_obs * 2.0 ** -64))

    el_total = time.time() - t_start
    emit("")
    emit("# ---- summary ----")
    emit("# elapsed        : %.1f s (%.1f terms/s)" % (el_total, done / el_total))
    emit("# checkpoints    : %d written" % n_ck)
    emit("# ref matches    : %d / %d (mismatches %d)" % (ref_match, len(ref), ref_mismatch))
    emit("# digits xcheck  : %s (%d checkpoints cross-checked vs str())" %
         ("OK" if digits_cross_ok else "FAILED", digits_cross_n))
    if halted:
        emit("# HALTED at position %d" % halted[0])
    emit("# records        : %s" % (records,))
    emit("# records match expected: %s" % (records == EXPECTED_RECORDS[:len(records)]))
    emit("# final bits     : %d" % bits)
    emit("# final digits   : %d (method check: %d)" % (dg, dg_method))
    emit("# final fnv1a64  : %016x" % fnv)
    emit("# final sha256   : %s" % sha_bin)
    emit("# final sha256(decimal-string): %s" % sha_dec)
    emit("# final v2       : %d   power_of_2: %s" % (vf, pow2))
    emit("# finished       : " + time.strftime("%Y-%m-%d %H:%M:%S"))
    logf.close()
    ckf.close()
    shf.close()
    return 0


# ---------------------------------------------------------------- selftest

def selftest():
    sys.set_int_max_str_digits(0)
    fails = 0

    def check(name, cond):
        nonlocal fails
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            fails += 1

    print("bb6blocks.py selftest  (gmpy2: %s)" % (HAVE_GMPY2,))

    # 1. decimal_digits vs exact len(str())
    import random
    random.seed(20260914)
    ok = True
    for bits in (1, 5, 7, 10, 16, 63, 64, 65, 100, 1000):
        for _ in range(3):
            x = random.getrandbits(bits) | (1 << (bits - 1))
            ok &= (decimal_digits(x) == len(str(x)))
    for p in (10, 100, 1000, 10000, 100000):
        ok &= (decimal_digits(10 ** p) == p + 1)
        ok &= (decimal_digits(10 ** p - 1) == p)
    for b in (2 ** 2048, 2 ** 2_000_000, 5 ** 100000):
        ok &= (decimal_digits(b) == len(str(b)))
    check("decimal_digits == len(str())", ok)

    # 2. fnv path consistency (both implementations)
    ok = True
    for x in (6, 10, 17, 251, (1 << 64) + 12345, random.getrandbits(200) | 1):
        h1 = fnv1a64(x)
        import struct
        raw = x.to_bytes(((x.bit_length() + 63) // 64) * 8, 'little')
        h = FNV_OFF
        for (w,) in struct.iter_unpack('<Q', raw):
            h = ((h ^ w) * FNV_PRIME) & MASK64
        ok &= (h1 == h)
    check("fnv1a64 fast/slow paths agree", ok)

    # 3. block method vs naive, 60000 terms, k=1200
    T = 60000
    K = 1200
    b_naive, vs_n, rec_n, mx_n, halt_n = naive_run(6, T)
    bounds_n = {}
    b = 6
    for i in range(1, T + 1):
        t = b & -b
        v = t.bit_length() - 1
        if b == t:
            break
        m = b >> v
        b = b + v + 3 * (m >> 1)
        if i % K == 0:
            bounds_n[i] = b
    bb = mpz(6)
    vs_b = []
    rec_b = []
    mx_b = 0
    done = 0
    bounds_ok = True
    while done < T:
        kk = min(K, T - done)
        w = 2 * kk + 2048
        res = None
        for _ in range(10):
            res = block_terms(_window_extract(bb, w), kk, w)
            if res is not None:
                break
            w *= 2
        if res is None:
            bounds_ok = False
            break
        vs, A, C, S, cands = res
        if cands:
            bounds_ok = False
            break
        for j, v in enumerate(vs):
            vs_b.append(v)
            if v > mx_b:
                mx_b = v
                rec_b.append((v, done + j + 1))
        bb = _advance(bb, A, C, S, "selftest")
        done += kk
        if done in bounds_n and int(bb) != bounds_n[done]:
            bounds_ok = False
            break
    check("block vs naive: all block-boundary values", bounds_ok)
    check("block vs naive: v-sequence identical", vs_b == vs_n)
    check("block vs naive: records identical", rec_b == rec_n)
    check("block vs naive: max_v2 identical", mx_b == mx_n)
    check("block vs naive: final value identical", int(bb) == b_naive)

    # 4. known checkpoint n=250000 (as in data/gmp_100M.csv first row)
    b250, _, _, mx250, _ = naive_run(6, 250000)
    check("n=250000 bits=235224", b250.bit_length() == 235224)
    check("n=250000 max_v2=17", mx250 == 17)
    check("n=250000 fnv=03d5d5032e47181a", "%016x" % fnv1a64(b250) == "03d5d5032e47181a")

    # 5. halt detection: b0 = 4 (power of 2 -> immediate halt)
    b4, _, _, _, halt4 = naive_run(4, 4)
    check("naive detects halt at position 1 (b0=4)", halt4 == 1)
    hb = mpz(4)
    res = block_terms(_window_extract(hb, 256), 4, 256)
    got = None
    if res is not None:
        vs, A, C, S, cands = res
        for (j, v) in cands:
            A2, C2, S2 = compose_vs(vs[:j])
            val = (mpz(A2) * hb + C2) >> S2
            if (val & (val - 1)) == 0:
                got = j + 1
                break
    check("block path detects halt at position 1 (b0=4)", got == 1)

    print("")
    if fails:
        print("SELFTEST: %d FAILURE(S)" % fails)
        return 1
    print("SELFTEST: ALL PASS")
    return 0


# ---------------------------------------------------------------- main

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    mode = args[0]
    if mode == "selftest":
        return selftest()
    if mode == "run":
        if len(args) < 2:
            print("usage: bb6blocks.py run N [k] [check_every] [outdir] [ref_csv]")
            return 2
        N = int(args[1])
        k = int(args[2]) if len(args) > 2 else 25000
        ce = int(args[3]) if len(args) > 3 else 250000
        outdir = args[4] if len(args) > 4 else "bb6blocks_out"
        ref = args[5] if len(args) > 5 else None
        return main_run(N, k, ce, outdir, ref)
    print("unknown mode: %r" % mode)
    return 2


if __name__ == "__main__":
    sys.exit(main())
