#!/usr/bin/env python3
"""L3 formal verification: boundary-family + full micro-step checks.

Coordinates: initial leftmost 1 of the (2m+3, c) config is at position 0,
head starts at -1, state A.  Machine = Space Needle (SN), table below.

Boundary family (conjectured, empirically extracted):
  init : 1^{2m+3}@[0,2m+2]; 0^2@[2m+3,2m+4]; 1^c@[2m+5,2m+4+c]; head=-1,A
  C_k  : left 1^k@[-1,k-2]; 0@[k-1]; mid 1^{2m+5-2k}@[k,2m+4-k];
         0@[2m+5-k] (head,C); right 1^{k+c-1}@[2m+6-k,2m+4+c]     (k=1..m+2)
  B_k  : left 1^k@[-1,k-2]; 0@[k-1] (head,A); mid 1^{2m+3-2k}@[k,2m+2-k];
         0^2@[2m+3-k,2m+4-k]; right 1^{k+c}@[2m+5-k,2m+4+c]        (k=1..m+1)
  D    : left 1^{m+2}@[-1,m]; 0@[m+1] (head,D); 0@[m+2]; right 1^{m+2+c}@[m+3,2m+4+c]
  B'   : same tape; head=m+2, B
  FINAL: 1^m@[-1,m-2]; 0^2@[m-1,m]; 1^{m+4+c}@[m+1,2m+4+c]; head=-2,A

Transitions and exact lengths:
  init -> C_1        : 2m+5
  C_k  -> B_k        : 2m+6-2k     (k=1..m+1)
  B_k  -> C_{k+1}    : 2m+5-2k     (k=1..m+1)
  C_{m+2} -> D       : 2
  D -> B'            : 1
  B'  -> FINAL       : m+4
  Total = sum of the above = 2(m+3)^2 + 1  (asserted at run end)

Usage:
  python l3_proof_check.py            # m=1..60 c=1 + c-spots, full checks
  python l3_proof_check.py 200        # up to m=200
  python l3_proof_check.py --big 1e4 25   # m=1e4, first 25 transitions only
"""
import sys
import time

TABLE = [
    [(1, +1, 1), (1, -1, 0)],   # A: 0->1RB, 1->1LA
    [(1, -1, 2), (0, +1, 4)],   # B
    [(1, -1, 5), (1, -1, 3)],   # C
    [(0, +1, 1), (0, -1, 0)],   # D
    [(1, +1, 2), (1, +1, 4)],   # E
    [None,        (0, -1, 3)],  # F: 0 -> HALT
]
ST = "ABCDEF"


class Tape:
    def __init__(self, m, c, pad=64):
        self.lo = -pad
        self.hi = 2 * m + 4 + c + pad
        self.buf = bytearray(self.hi - self.lo + 1)

    def get(self, p):
        return self.buf[p - self.lo] if self.lo <= p <= self.hi else 0

    def set(self, p, v):
        if self.lo <= p <= self.hi:
            self.buf[p - self.lo] = v

    def run_set(self, a, b, v):
        a = max(a, self.lo)
        b = min(b, self.hi)
        if a <= b:
            self.buf[a - self.lo:b - self.lo + 1] = bytes([v]) * (b - a + 1)

    def __eq__(self, other):
        return self.buf == other.buf


def build(m, c, kind, k=None):
    t = Tape(m, c)
    if kind == 'init':
        t.run_set(0, 2 * m + 2, 1)
        t.run_set(2 * m + 5, 2 * m + 4 + c, 1)
        return t, -1, 0
    if kind == 'C':
        t.run_set(-1, k - 2, 1)
        t.run_set(k, 2 * m + 4 - k, 1)
        t.run_set(2 * m + 6 - k, 2 * m + 4 + c, 1)
        return t, 2 * m + 5 - k, 2
    if kind == 'B':
        t.run_set(-1, k - 2, 1)
        t.run_set(k, 2 * m + 2 - k, 1)
        t.run_set(2 * m + 5 - k, 2 * m + 4 + c, 1)
        return t, k - 1, 0
    if kind == 'D':
        t.run_set(-1, m, 1)
        t.run_set(m + 3, 2 * m + 4 + c, 1)
        return t, m + 1, 3
    if kind == 'Bp':
        t.run_set(-1, m, 1)
        t.run_set(m + 3, 2 * m + 4 + c, 1)
        return t, m + 2, 1
    if kind == 'FINAL':
        t.run_set(-1, m - 2, 1)
        t.run_set(m + 1, 2 * m + 4 + c, 1)
        return t, -2, 0
    raise ValueError(kind)


def preds_init(m):
    seq = [(-1, 0, 0, 0, 1), (0, 1, 1, 1, 4)]
    for j in range(1, 2 * m + 3):
        seq.append((j, 4, 1, j + 1, 4))
    seq.append((2 * m + 3, 4, 0, 2 * m + 4, 2))
    return seq


def preds_C_to_B(m, k):
    h = 2 * m + 5 - k
    seq = [(h, 2, 0, h - 1, 5), (h - 1, 5, 1, h - 2, 3), (h - 2, 3, 1, h - 3, 0)]
    for j in range(h - 3, k - 1, -1):
        seq.append((j, 0, 1, j - 1, 0))
    return seq


def preds_B_to_C(m, k):
    seq = [(k - 1, 0, 0, k, 1), (k, 1, 1, k + 1, 4)]
    for j in range(k + 1, 2 * m + 3 - k):
        seq.append((j, 4, 1, j + 1, 4))
    seq.append((2 * m + 3 - k, 4, 0, 2 * m + 4 - k, 2))
    return seq


def preds_C_to_D(m):
    return [(m + 3, 2, 0, m + 2, 5), (m + 2, 5, 1, m + 1, 3)]


def preds_D_to_Bp(m):
    return [(m + 1, 3, 0, m + 2, 1)]


def preds_Bp_to_FINAL(m):
    seq = [(m + 2, 1, 0, m + 1, 2), (m + 1, 2, 0, m, 5),
           (m, 5, 1, m - 1, 3), (m - 1, 3, 1, m - 2, 0)]
    for j in range(m - 2, -2, -1):
        seq.append((j, 0, 1, j - 1, 0))
    return seq


def check(m, c=1, firstJ=None, verbose=False):
    """Returns (ok, nsteps, message).  firstJ: only first J transitions."""
    trans = []  # (label, nextkind, nextk, preds, delta)
    trans.append(("init->C1", 'C', 1, preds_init(m), 2 * m + 5))
    kmax = m + 1
    if firstJ is not None:
        kmax = min(kmax, firstJ)
    for k in range(1, kmax + 1):
        trans.append((f"C{k}->B{k}", 'B', k, preds_C_to_B(m, k), 2 * m + 6 - 2 * k))
        trans.append((f"B{k}->C{k+1}", 'C', k + 1, preds_B_to_C(m, k), 2 * m + 5 - 2 * k))
    if firstJ is None:
        trans.append(("C->D", 'D', None, preds_C_to_D(m), 2))
        trans.append(("D->B'", 'Bp', None, preds_D_to_Bp(m), 1))
        trans.append(("B'->FINAL", 'FINAL', None, preds_Bp_to_FINAL(m), m + 4))

    t, head, st = build(m, c, 'init')
    nsteps = 0
    for label, nk, nkx, preds, delta in trans:
        if len(preds) != delta:
            return False, nsteps, f"{label}: preds count {len(preds)} != delta {delta}"
        for (pb, sb, r, pa, sa) in preds:
            if head != pb or st != sb:
                return False, nsteps, (f"{label}: step {nsteps}: expected (pos {pb}, st {ST[sb]}), "
                                       f"got (pos {head}, st {ST[st]})")
            v = t.get(head)
            if v != r:
                return False, nsteps, (f"{label}: step {nsteps}: pos {pb} read expected {r}, got {v}")
            tr = TABLE[st][v]
            if tr is None:
                return False, nsteps, f"{label}: step {nsteps}: HALT encountered unexpectedly"
            w, mv, nxt = tr
            t.set(head, w)
            head += mv
            st = nxt
            nsteps += 1
            if head != pa or st != sa:
                return False, nsteps, (f"{label}: step {nsteps}: expected after (pos {pa}, st {ST[sa]}), "
                                       f"got (pos {head}, st {ST[st]})")
        # boundary compare
        bt, bh, bs = build(m, c, nk, nkx)
        if not (t == bt) or head != bh or st != bs:
            # locate mismatch
            diffs = [p for p in range(max(t.lo, bt.lo), min(t.hi, bt.hi) + 1)
                     if t.get(p) != bt.get(p)]
            return False, nsteps, (f"{label}: boundary mismatch (head {head} vs {bh}, st {ST[st]} vs {ST[bs]}, "
                                   f"cell diffs {diffs[:12]})")
    return True, nsteps, "OK"


def main():
    t0 = time.time()
    args = sys.argv[1:]
    if args and args[0] == '--big':
        m = int(float(args[1]))
        J = int(args[2])
        ok, ns, msg = check(m, 1, firstJ=J)
        print(f"m={m} firstJ={J}: {'PASS' if ok else 'FAIL'} steps={ns} [{msg}] ({time.time()-t0:.1f}s)")
        return
    if args and args[0] == '--full':
        m = int(float(args[1]))
        ok, ns, msg = check(m, 1)
        good = ok and ns == 2 * (m + 3) ** 2 + 1
        print(f"m={m} c=1 (full ladder): {'PASS' if good else 'FAIL'} steps={ns} [{msg}] ({time.time()-t0:.1f}s)")
        return
    if args and args[0] == '--cspot':
        okc = True
        for m, c in [(5, 10**6), (10, 10**6), (100, 10**6)]:
            ok, ns, msg = check(m, c)
            good = ok and ns == 2 * (m + 3) ** 2 + 1
            okc &= good
            print(f"m={m} c={c}: {'PASS' if good else 'FAIL'} steps={ns} [{msg}]")
        print(f"cspots: {'ALL PASS' if okc else 'FAILURES'} ({time.time()-t0:.1f}s)")
        return
    mmax = int(args[0]) if args else 60
    allok = True
    for m in range(0, mmax + 1):
        ok, ns, msg = check(m, 1)
        total = 2 * (m + 3) ** 2 + 1
        exp_ns = total
        good = ok and ns == exp_ns
        allok &= good
        if not good or m in (0, 1, 2):
            print(f"m={m}: {'PASS' if good else 'FAIL'} steps={ns} (total {exp_ns}) [{msg}]")
    print(f"c=1 m=0..{mmax}: {'ALL PASS' if allok else 'FAILURES'} ({time.time()-t0:.1f}s)")
    # c-spots
    for c in (0, 2, 3, 7):
        okc = True
        for m in range(0, 12):
            ok, ns, msg = check(m, c)
            good = ok and ns == 2 * (m + 3) ** 2 + 1
            okc &= good
            if not good:
                print(f"  FAIL c={c} m={m}: {msg}")
        print(f"c={c} m=0..11: {'ALL PASS' if okc else 'FAILURES'}")
    # scale spots
    for m in (100, 500, 1000):
        ok, ns, msg = check(m, 1)
        good = ok and ns == 2 * (m + 3) ** 2 + 1
        print(f"m={m}: {'PASS' if good else 'FAIL'} steps={ns} [{msg}]")
    print(f"TOTAL {time.time()-t0:.1f}s")


if __name__ == '__main__':
    main()
