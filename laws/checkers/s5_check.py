#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S5 -- Verification independante du modele "lois de pas" (BB(6) Space Needle)
============================================================================
Machine (format bbchallenge) :
    1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD
Etats A..F ; chaque bloc = 2 transitions [ecrit][L/R][etat] (symbole 0 puis 1).
"---" = transition indefinie -> HALT. Ruban infini de zeros.

Config (b,c) = 0^inf <A 1^b 00 1^c 0^inf : tete sur la cellule immediatement a
GAUCHE du premier 1 du bloc de b uns (pour b=0 : juste a gauche des deux zeros
separateurs), etat A, lit 0. Un "pas" = une transition executee.

Lois testees (bloc 1) :
    L0 : (0,0)    -> (0,1)      en 10 pas
    L1 : (0,c>=1) -> (c+2,1)    en 2c+33 pas
    L2 : (1,c)    -> HALT       en 12 pas  (tout c)
    L3 : (2m+3,c) -> (m,4+m+c)  en 2(m+3)^2+1 pas             (b impair >= 3)
    L4 : (2m+2,c) -> (7+5m+c,1) en (3m+8)(m^2+7m+13)+2(c-1)   (b pair  >= 2)

Echantillon du bloc 1 :
    L0 : (0,0)
    L1 : c = 1..40
    L2 : c dans {0,5,17,1023}
    L3 : b impair 3..63  x c dans {0,5,17,1023}
    L4 : b pair   2..64  x c dans {0,5,17,1023}

Usage :
    python C:\\Users\\oohza\\bb6\\s5\\check.py        -> blocs 1..4
    python C:\\Users\\oohza\\bb6\\s5\\check.py 1      -> bloc 1 seul (idem 2,3,4)

Ecrit de zero (stdlib seulement) ; aucun code du projet n'est lu ; seule
donnee externe lue : reports\\chainb_25.txt (bloc 2).
"""

import sys
import time
from fractions import Fraction

REPORTS = r"C:\Users\oohza\bb6\reports"
ANNEX1 = REPORTS + r"\S5_block1_cases.txt"
CHAIN_FILE = REPORTS + r"\chainb_25.txt"

# ---------------------------------------------------------------------------
# Machine : idx = 2*etat + symbole lu ; N[idx] = -1  =>  halte ("---").
# ---------------------------------------------------------------------------
W = (1, 1,   1, 0,   1, 1,   0, 0,   1, 1,   0, 0)     # symbole ecrit
D = (1, -1, -1, 1,  -1, -1,  1, -1,  1, 1,   0, -1)    # +1 = droite, -1 = gauche
N = (1, 0,   2, 4,   5, 3,   1, 0,   2, 4,  -1, 3)     # etat suivant (-1 = halte)


def run_case(b, c, cap):
    """Simulation brute depuis la config (b,c).

    bytearray + boucle de pas 100% inline (aucun appel de fonction par pas).
    S'arrete au premier checkpoint suivant, ou a la halte, ou au cap de pas.
    Retourne (halted, cps, steps) ; cps = [(b',c',pas), ...] (normalement 0 ou
    1 element : on s'arrete au premier checkpoint trouve).
    """
    need = b + c + 3
    off = cap + 64
    size = 2 * cap + need + 128
    tape = bytearray(size)
    p = off + 1
    for _ in range(b):
        tape[p] = 1
        p += 1
    p += 2                      # deux zeros separateurs
    cstart = p
    for _ in range(c):
        tape[p] = 1
        p += 1
    if c:
        hi = p - 1
    elif b:
        hi = off + b
    else:
        hi = off - 1            # rien d'ecrit (cas (0,0))
    lo = off + 1 if b else (cstart if c else off + 1)

    hd = off
    st = 0
    steps = 0
    cps = []
    halted = False

    while steps < cap:
        idx = (st << 1) | tape[hd]
        ns = N[idx]
        if ns < 0:              # transition indefinie -> halte (pas non compte)
            halted = True
            break
        tape[hd] = W[idx]
        if hd < lo:
            lo = hd
        elif hd > hi:
            hi = hd
        hd += D[idx]
        st = ns
        steps += 1
        # ---- Detection inline : etat A, lit 0, tout a gauche = 0, et a droite
        #      exactement 1^bb 00 1^cc suivi de zeros.
        if st == 0 and tape[hd] == 0:
            ok = True
            i = lo
            lim = hd if hd <= hi else hi + 1
            while i < lim:
                if tape[i]:
                    ok = False
                    break
                i += 1
            if ok:
                j = hd + 1
                bb = 0
                while tape[j] == 1:
                    bb += 1
                    j += 1
                if tape[j] == 0 and tape[j + 1] == 0:
                    j += 2
                    cc = 0
                    while tape[j] == 1:
                        cc += 1
                        j += 1
                    kk = hi + 1 if j <= hi else j
                    k = j
                    while k < kk:
                        if tape[k]:
                            ok = False
                            break
                        k += 1
                    if ok:
                        cps.append((bb, cc, steps))
                        break

    return halted, cps, steps


def expected(b, c):
    """Prediction des lois pour la config (b,c) :
    ('cp', b2, c2, pas) ou ('halt', None, None, pas)."""
    if b == 0:
        if c == 0:
            return ('cp', 0, 1, 10)
        return ('cp', c + 2, 1, 2 * c + 33)
    if b == 1:
        return ('halt', None, None, 12)
    if b & 1:
        m = (b - 3) // 2
        return ('cp', m, 4 + m + c, 2 * (m + 3) * (m + 3) + 1)
    m = (b - 2) // 2
    return ('cp', 7 + 5 * m + c, 1,
            (3 * m + 8) * (m * m + 7 * m + 13) + 2 * (c - 1))


def block1_cases():
    cases = [('L0', 0, 0)]
    for c in range(1, 41):
        cases.append(('L1', 0, c))
    for c in (0, 5, 17, 1023):
        cases.append(('L2', 1, c))
    for b in range(3, 64, 2):
        for c in (0, 5, 17, 1023):
            cases.append(('L3', b, c))
    for b in range(2, 65, 2):
        for c in (0, 5, 17, 1023):
            cases.append(('L4', b, c))
    return cases


def block1():
    print("=" * 74)
    print("BLOC 1 - re-test des lois de pas par simulation brute (from scratch)")
    print("=" * 74)
    cases = block1_cases()
    t0 = time.time()
    res = []
    for law, b, c in cases:
        kind, eb, ec, es = expected(b, c)
        cap = es + 50000
        halted, cps, steps = run_case(b, c, cap)
        if kind == 'halt':
            exp_s = "halte@%d" % es
            if halted and steps == es and not cps:
                got_s = "halte@%d" % steps
                ok = True
            elif halted:
                got_s = "halte@%d apres cp=%s (inattendu)" % (steps, cps[:2])
                ok = False
            else:
                got_s = "pas de halte (cap=%d, cps=%s)" % (cap, cps[:2])
                ok = False
        else:
            exp_s = "(%d,%d)@%d" % (eb, ec, es)
            ok = (not halted) and bool(cps) and cps[0] == (eb, ec, es)
            if halted:
                got_s = "halte@%d (inattendue)" % steps
            elif cps:
                got_s = "(%d,%d)@%d" % cps[0]
            else:
                got_s = "aucun checkpoint jusqu'a %d pas" % steps
        res.append((law, b, c, exp_s, got_s, ok))
    dt = time.time() - t0

    laws = ['L0', 'L1', 'L2', 'L3', 'L4']
    npass = sum(1 for r in res if r[5])
    print("cas       : %d" % len(res))
    print("PASS      : %d" % npass)
    print("violation : %d" % (len(res) - npass))
    print("-" * 74)
    for law in laws:
        sub = [r for r in res if r[0] == law]
        nviol = sum(1 for r in sub if not r[5])
        print("%-3s %4d cas, %4d PASS, %d violation" % (law, len(sub), len(sub) - nviol, nviol))
    print("-" * 74)
    print("echantillon (1er / milieu / dernier par loi) :")
    for law in laws:
        sub = [r for r in res if r[0] == law]
        idxs = sorted(set([0, len(sub) // 2, len(sub) - 1]))
        for i in idxs:
            law_, b, c, e, g, ok = sub[i]
            print("  %-3s b=%-4d c=%-5d attendu %-16s observe %-16s %s"
                  % (law_, b, c, e, g, "PASS" if ok else "VIOLATION"))
    viols = [r for r in res if not r[5]]
    if viols:
        print("-" * 74)
        print("VIOLATIONS (details complets) :")
        for law_, b, c, e, g, ok in viols:
            print("  %s b=%d c=%d | attendu %s | observe %s" % (law_, b, c, e, g))
    print("-" * 74)
    with open(ANNEX1, "w", encoding="utf-8") as fh:
        fh.write("S5 bloc 1 - journal complet des %d cas\n" % len(res))
        fh.write("machine: 1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD\n")
        fh.write("(b,c) = 0^inf <A 1^b 00 1^c 0^inf ; pas = transitions executees ;\n")
        fh.write("detection: etat A, lit 0, tout-a-gauche=0, a droite 1^b 00 1^c puis zeros.\n")
        fh.write("-" * 78 + "\n")
        for law_, b, c, e, g, ok in res:
            fh.write("%-3s b=%-4d c=%-5d | attendu %-18s | observe %-18s | %s\n"
                     % (law_, b, c, e, g, "PASS" if ok else "VIOLATION"))
    print("(journal complet des cas : %s)" % ANNEX1)
    print("duree bloc 1 : %.2f s" % dt)
    return res


def law_chain(n):
    """Chaine analytique : depuis (0,0)@0, applique les lois sans simulation."""
    pts = [(0, 0, 0)]
    while len(pts) < n:
        b, c, t = pts[-1]
        kind, nb, nc, dt = expected(b, c)
        if kind == 'halt':
            break
        pts.append((nb, nc, t + dt))
    return pts


def load_chain_file(path):
    """Lit chainb_25.txt comme DONNEE : lignes 'CP b c steps' (b>0) et
    'CP0 c steps' (b=0)."""
    pts = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            tk = line.split()
            if not tk:
                continue
            if tk[0] == "CP0" and len(tk) >= 3:
                pts.append((0, int(tk[1]), int(tk[2])))
            elif tk[0] == "CP" and len(tk) >= 4:
                pts.append((int(tk[1]), int(tk[2]), int(tk[3])))
    return pts


def block2():
    print("=" * 74)
    print("BLOC 2 - modele analytique vs simulation brute (chainb_25.txt)")
    print("=" * 74)
    model = law_chain(40)
    print("points du modele analytique (n, (b,c) @ pas absolu, delta) :")
    prev = 0
    for i, (b, c, t) in enumerate(model):
        print("  %2d. (%d,%d) @ %d   (+%d)" % (i + 1, b, c, t, t - prev))
        prev = t
    filepts = load_chain_file(CHAIN_FILE)
    print("-" * 74)
    print("comparaison avec le fichier (%d points lus) :" % len(filepts))
    nmatch = 0
    n = min(len(model), len(filepts))
    for i in range(n):
        mb, mc, mt = model[i]
        fb, fc, ft = filepts[i]
        ok = (mb == fb) and (mc == fc) and (mt == ft)
        if ok:
            nmatch += 1
        print("  pt %2d | fichier (%5d,%5d)@%-12d | modele (%5d,%5d)@%-12d | %s"
              % (i + 1, fb, fc, ft, mb, mc, mt, "OK" if ok else "DIFF"))
    print("correspondances exactes (config ET pas) : %d / %d" % (nmatch, n))
    if filepts:
        print("dernier point fichier : (%d,%d)@%d" % filepts[-1])
    print("-" * 74)
    print("predictions 26..40 :")
    for i in range(25, min(40, len(model))):
        b, c, t = model[i]
        print("  %2d. (%d,%d) @ %d" % (i + 1, b, c, t))
    return model, filepts, nmatch


# ---------------------------------------------------------------------------
# Blocs 3 et 4 : carte f de Doucette.
#   f(x) = (5x-3)/2                    si x impair
#   f(x) = x + k + (3/2)(m-1)          si x = 2^k * m, m impair
#   HALT si x est une puissance de 2.
# ---------------------------------------------------------------------------
def is_pow2(x):
    return (x.denominator == 1) and (x.numerator > 0) and ((x.numerator & (x.numerator - 1)) == 0)


def f_apply(x):
    """Une application de f ; suppose que x n'est pas une puissance de 2."""
    if x.denominator != 1:
        raise ValueError("valeur non entiere rencontree : %s" % x)
    n = x.numerator
    if n & 1:
        return Fraction(5 * n - 3, 2)
    k = (n & -n).bit_length() - 1
    m = n >> k
    return Fraction(2 * n + 2 * k + 3 * (m - 1), 2)


def f_trajectory(x, max_steps=200):
    seq = [x]
    for _ in range(max_steps):
        if is_pow2(seq[-1]):
            break
        seq.append(f_apply(seq[-1]))
    return seq


def show_traj(name, x0, kmax):
    print("-" * 74)
    print("%s : x0 = %s" % (name, x0))
    print("   entier ? %s" % (x0.denominator == 1))
    seq = f_trajectory(x0)
    for i, v in enumerate(seq):
        tag = ""
        if is_pow2(v):
            tag = "  <-- puissance de 2 : 2^%d" % (v.numerator.bit_length() - 1)
        elif v.denominator == 1 and (v.numerator & 1) == 0:
            n = v.numerator
            k = (n & -n).bit_length() - 1
            tag = "  [pair : k=%d, m=%d]" % (k, n >> k)
        elif v.denominator == 1:
            tag = "  [impair]"
        print("   etape %d : %s%s" % (i, v, tag))
    reached = seq[-1]
    steps = len(seq) - 1
    ok = is_pow2(reached) and steps <= kmax
    print("   -> atteint %s en %d etapes ; contrainte <=%d : %s"
          % (reached, steps, kmax, "PASS" if ok else "FAIL"))
    return ok, steps, reached


def block3():
    print("=" * 74)
    print("BLOC 3 - exemples fractionnaires (carte f de Doucette)")
    print("=" * 74)
    xa = Fraction(2 ** 85 + 243, 385)
    oka, sa, ra = show_traj("(a) x = (2^85+243)/385", xa, 3)
    xb = Fraction(2 ** 55 + 1440407, 2481875)
    okb, sb, rb = show_traj("(b) x = (2^55+1440407)/2481875", xb, 6)
    return (oka, sa, ra), (okb, sb, rb)


def block4():
    print("=" * 74)
    print("BLOC 4 - calibration : f applique a 6 doit donner la suite de reference")
    print("=" * 74)
    exp_seq = [6, 10, 17, 41, 101, 251, 626, 1095, 2736, 2995]
    seq = [Fraction(6)]
    for _ in range(len(exp_seq) - 1):
        seq.append(f_apply(seq[-1]))
    allok = True
    for i, (v, e) in enumerate(zip(seq, exp_seq)):
        ok = (v.denominator == 1) and (v.numerator == e)
        allok = allok and ok
        print("   n=%-2d : %-6s (attendu %-6d) %s" % (i, v, e, "OK" if ok else "ECART"))
    print("   (continuation) f(2995) = %s" % f_apply(seq[-1]))
    print("   verdict bloc 4 : %s" % ("PASS" if allok else "FAIL"))
    return allok, seq


def main():
    args = set(sys.argv[1:])
    which = args if args else {"1", "2", "3", "4"}
    if "1" in which:
        block1()
    if "2" in which:
        block2()
    if "3" in which:
        block3()
    if "4" in which:
        block4()


if __name__ == "__main__":
    main()
