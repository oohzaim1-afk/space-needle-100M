#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L1 formal proof checker — Space Needle (1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD).

Certifie la preuve (Desktop\\SPACE_NEEDLE_L1_PROOF.md) :
    (0, c) -> (c+2, 1)  en exactement 2c+33 pas   (c >= 1)
    balayages : [1,2,4,3,3,2,1,3,1,2, c+6, c+5]  (12 runs)

Init (coordonnées de la preuve) : tête en 0, état A ; ruban tout 0 sauf [3, c+2] = 1^c.
Macro-étapes : P (22 pas) -> PREF ;  M1 (c+6) -> TOUR ;  M2 (c+5) -> FINAL = (c+2,1).

Méthode : on prédit CHAQUE pas (position, état, lecture, écriture, position suivante,
état suivant), on applique la VRAIE table de transitions et on compare ; plus les
frontières PREF/TOUR/FINAL, le total, la décomposition en balayages, l'unique visite de F.

Usage : python l1_proof_check.py [N=5000]     # c = 1..N complet, puis spots 1e4..1e7
        python l1_proof_check.py --big 7       # c unique = 10^7
"""
import sys, os, time, hashlib
from datetime import datetime

MACHINE = "1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD"

# table de transitions réelle : st -> symbole 0/1 -> (écrit, direction, suivant) ; None = halte
TABLE = {
    "A": ((1, +1, "B"), (1, -1, "A")),
    "B": ((1, -1, "C"), (0, +1, "E")),
    "C": ((1, -1, "F"), (1, -1, "D")),
    "D": ((0, +1, "B"), (0, -1, "A")),
    "E": ((1, +1, "C"), (1, +1, "E")),
    "F": (None, (0, -1, "D")),
}


class Tape:
    __slots__ = ("buf", "lo", "hi")

    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi
        self.buf = bytearray(hi - lo + 1)

    def get(self, p):
        return self.buf[p - self.lo] if self.lo <= p <= self.hi else 0

    def set(self, p, v):
        if self.lo <= p <= self.hi:
            self.buf[p - self.lo] = v

    def run_set(self, a, b, v=1):
        a = max(a, self.lo)
        b = min(b, self.hi)
        if a <= b:
            self.buf[a - self.lo:b - self.lo + 1] = bytes([v]) * (b - a + 1)

    def eq(self, other):
        return self.lo == other.lo and self.hi == other.hi and self.buf == other.buf


def _diff(a, b, limit=12):
    ds = []
    lo = max(a.lo, b.lo)
    hi = min(a.hi, b.hi)
    for p in range(lo, hi + 1):
        va, vb = a.get(p), b.get(p)
        if va != vb:
            ds.append((p, va, vb))
            if len(ds) >= limit:
                break
    return ds


# ---------------------------------------------------------------- prédictions

def preds_P():
    """Lemme P : INIT -> PREF, 22 pas (indépendant de c pour c >= 1)."""
    return [
        (0,  "A", 0, 1,  1, "B"),
        (1,  "B", 0, 1,  0, "C"),
        (0,  "C", 1, 1, -1, "D"),
        (-1, "D", 0, 0,  0, "B"),
        (0,  "B", 1, 0,  1, "E"),
        (1,  "E", 1, 1,  2, "E"),
        (2,  "E", 0, 1,  3, "C"),
        (3,  "C", 1, 1,  2, "D"),
        (2,  "D", 1, 0,  1, "A"),
        (1,  "A", 1, 1,  0, "A"),
        (0,  "A", 0, 1,  1, "B"),
        (1,  "B", 1, 0,  2, "E"),
        (2,  "E", 0, 1,  3, "C"),
        (3,  "C", 1, 1,  2, "D"),
        (2,  "D", 1, 0,  1, "A"),
        (1,  "A", 0, 1,  2, "B"),
        (2,  "B", 0, 1,  1, "C"),
        (1,  "C", 1, 1,  0, "D"),
        (0,  "D", 1, 0, -1, "A"),
        (-1, "A", 0, 1,  0, "B"),
        (0,  "B", 0, 1, -1, "C"),
        (-1, "C", 1, 1, -2, "D"),
    ]


def preds_M1(c):
    """Lemme M1 : PREF -> TOUR, c+6 pas (marche droite en état E)."""
    yield (-2, "D", 0, 0, -1, "B")
    yield (-1, "B", 1, 0,  0, "E")
    for j in range(0, c + 3):          # positions 0 .. c+2 (toutes à 1)
        yield (j, "E", 1, 1, j + 1, "E")
    yield (c + 3, "E", 0, 1, c + 4, "C")


def preds_M2(c):
    """Lemme M2 : TOUR -> FINAL, c+5 pas (marche gauche en état A)."""
    yield (c + 4, "C", 0, 1, c + 3, "F")
    yield (c + 3, "F", 1, 0, c + 2, "D")
    yield (c + 2, "D", 1, 0, c + 1, "A")
    for j in range(c + 1, -1, -1):     # positions c+1 .. 0 (toutes à 1)
        yield (j, "A", 1, 1, j - 1, "A")


def _chain(c):
    yield from preds_P()
    yield from preds_M1(c)
    yield from preds_M2(c)


def pred_runs(c):
    return [1, 2, 4, 3, 3, 2, 1, 3, 1, 2, c + 6, c + 5]


# ---------------------------------------------------------------- certification

def check(c):
    """Certifie un c >= 1. Retourne (ok, message, nb_pas)."""
    t = Tape(-64, c + 64)
    t.run_set(3, c + 2, 1)
    pos, st = 0, "A"
    runs = []
    cur = 0
    prev = 0
    fvisits = []
    n = 0
    for i, (p0, s0, rd, wr, p1, s1) in enumerate(_chain(c), 1):
        n = i
        if pos != p0 or st != s0:
            return False, f"pas {i} : tête/état ({pos},{st}) vs prédit ({p0},{s0})", i - 1
        v = t.get(pos)
        if v != rd:
            return False, f"pas {i} : lecture en {pos} = {v}, prédit {rd}", i - 1
        real = TABLE[st][v]
        if real is None:
            return False, f"pas {i} : HALTE inattendue", i - 1
        rw, d, ns = real
        if rw != wr or (pos + d) != p1 or ns != s1:
            return False, (f"pas {i} : table ({rw},{d:+d},{ns}) vs prédit "
                           f"({wr},{p1 - pos:+d},{s1})"), i - 1
        if s0 == "F":
            fvisits.append((i, v))
        t.set(pos, wr)
        pos, st = p1, s1
        if d == prev:
            cur += 1
        else:
            if cur:
                runs.append(cur)
            cur = 1
            prev = d
        if i == 22:
            e = Tape(-64, c + 64)
            e.run_set(-1, c + 2, 1)
            if not (t.eq(e) and pos == -2 and st == "D"):
                return False, f"pas {i} : frontière PREF — diffs {_diff(t, e)}", i
        elif i == 28 + c:
            e = Tape(-64, c + 64)
            e.run_set(0, c + 3, 1)
            if not (t.eq(e) and pos == c + 4 and st == "C"):
                return False, f"pas {i} : frontière TOUR — diffs {_diff(t, e)}", i
    if cur:
        runs.append(cur)
    total = 2 * c + 33
    if n != total:
        return False, f"total {n} != 2c+33 = {total}", n
    e = Tape(-64, c + 64)
    e.run_set(0, c + 1, 1)
    e.set(c + 4, 1)
    if not (t.eq(e) and pos == -1 and st == "A"):
        return False, f"frontière FINAL — diffs {_diff(t, e)} (tête {pos},{st})", n
    if runs != pred_runs(c):
        return False, f"balayages {runs} != {pred_runs(c)}", n
    if fvisits != [(30 + c, 1)]:
        return False, f"visites de F {fvisits} != [(30+c, 1)]", n
    return True, f"PASS ({n:,} pas)", n


def check_c0():
    """c = 0 : confirme la bifurcation au pas 8 (C lit 0 en 3 au lieu de 1)."""
    t = Tape(-64, 64)
    pos, st = 0, "A"
    for i, (p0, s0, rd, wr, p1, s1) in enumerate(preds_P(), 1):
        if pos != p0 or st != s0:
            return False, i, f"tête/état divergent au pas {i} (inattendu)"
        v = t.get(pos)
        if v != rd:
            ok = (i == 8 and v == 0 and rd == 1)
            return ok, i, (f"première divergence au pas {i} (cellule {pos} = {v}, "
                           f"prédit {rd})" + (" — conforme" if ok else " — INATTENDU"))
        rw, d, ns = TABLE[st][v]
        t.set(pos, rw)
        pos, st = pos + d, ns
    return False, None, "aucune divergence dans le lemme P (inattendu)"


def check_trampoline(c):
    """Bonus : (3,c) -> (c+6,1) en 2c+60 pas (L3 m=0 composée avec L1)."""
    total = 2 * c + 60
    t = Tape(-64, c + 64)
    t.run_set(0, 2, 1)          # bloc gauche 1^3
    t.run_set(5, c + 4, 1)      # bloc droit 1^c (canonique (3,c))
    pos, st = -1, "A"
    for i in range(1, total + 1):
        v = t.get(pos)
        real = TABLE[st][v]
        if real is None:
            return False, f"HALTE au pas {i}", i
        rw, d, ns = real
        t.set(pos, rw)
        pos, st = pos + d, ns
        if i == 19:
            e = Tape(-64, c + 64)
            e.run_set(1, c + 4, 1)
            if not (t.eq(e) and pos == -2 and st == "A"):
                return False, f"frontière L3 (pas 19) — diffs {_diff(t, e)}", i
    e = Tape(-64, c + 64)
    e.run_set(-2, c + 3, 1)
    e.set(c + 6, 1)
    if not (t.eq(e) and pos == -3 and st == "A"):
        return False, f"final — diffs {_diff(t, e)} (tête {pos},{st})", total
    return True, f"PASS ({total:,} pas)", total


# ---------------------------------------------------------------- main

def main():
    t0 = time.time()
    args = sys.argv[1:]
    out = []

    def log(s):
        out.append(s)
        print(s)

    log("=== L1 proof checker — Space Needle ===")
    log(f"machine: {MACHINE}")
    log(f"date: {datetime.now():%Y-%m-%d %H:%M:%S}")
    log("claim: (0,c) -> (c+2,1) en exactement 2c+33 pas (c>=1); "
        "balayages [1,2,4,3,3,2,1,3,1,2,c+6,c+5]")

    all_ok = True
    total = 0
    if args and args[0] == "--big":
        c = 10 ** int(args[1])
        ok, msg, n = check(c)
        log(f"c = {c}: {'PASS' if ok else 'FAIL'} — {msg}")
        all_ok = ok
        total = n if ok else 0
    else:
        N = int(args[0]) if args else 5000
        for c in range(1, N + 1):
            ok, msg, n = check(c)
            if not ok:
                all_ok = False
                log(f"c = {c}: FAIL — {msg}")
                break
            total += n
        if all_ok:
            log(f"c = 1..{N}: ALL PASS ({total:,} pas)")
        for c in (10**4, 10**5, 10**6, 10**7):
            if not all_ok:
                break
            ok, msg, n = check(c)
            if not ok:
                all_ok = False
                log(f"c = {c}: FAIL — {msg}")
                break
            total += n
            log(f"c = {c}: PASS ({n:,} pas)")
        ok0, i0, msg0 = check_c0()
        log(f"c = 0: {'PASS' if ok0 else 'FAIL'} — {msg0}")
        all_ok = all_ok and ok0
        for c in (1, 2, 3, 5, 10):
            okt, msgt, nt = check_trampoline(c)
            log(f"trampoline (3,{c}) -> ({c+6},1): {'PASS' if okt else 'FAIL'} — {msgt}")
            all_ok = all_ok and okt

    log(f"total pas certifiés (L1): {total:,}")
    log(f"verdict: {'ALL PASS' if all_ok else 'FAIL'}")
    log(f"[elapsed {time.time() - t0:.1f}s]")

    reports_dir = os.environ.get("SPN_REPORTS") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    rpt = os.path.join(reports_dir, "l1_proof_check_report.txt")
    with open(rpt, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    h = hashlib.sha256(open(rpt, "rb").read()).hexdigest()
    with open(os.path.join(reports_dir, "MANIFEST_sha256.txt"), "a", encoding="utf-8") as f:
        f.write(f"{h}  l1_proof_check_report.txt  ({os.path.getsize(rpt)} bytes)\n")
    print("report:", rpt)
    print("sha256:", h)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
