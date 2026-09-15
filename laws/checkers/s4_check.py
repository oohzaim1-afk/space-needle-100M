#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S4 — Vérification indépendante (réécriture from scratch, Python pur, stdlib)
des lois computationnelles de la machine de Turing BB(6) « Space Needle » :
    1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD

- Aucun code existant du projet (ni Rust ni Python) n'a été lu : décodage,
  simulateur et détection de configuration sont réimplémentés intégralement
  dans ce fichier. Seule DONNÉE lue : reports/gpu_B_b511_c1023.csv (test (d)).
- Rapport écrit au fil de l'eau dans reports/S4_report.md.
- Exécution : python C:\\Users\\oohza\\bb6\\s4\\check.py

Config (b,c) = 0^inf <A 1^b 00 1^c 0^inf, tête sur la cellule immédiatement à
gauche du premier 1 du bloc b (b=0 : immédiatement à gauche des deux zéros
séparateurs), état A, lecture 0.

Détection : état A, tête lit 0, toutes les cellules à gauche de la tête = 0,
et à droite de la tête le ruban est exactement 1^b 00 1^c suivi de zéros.
Convention de pas : nombre de transitions exécutées (la détection « au pas t »
a lieu juste après la t-ième transition).
"""

import os
import sys
import time
import random
import platform
import traceback

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

BASE = r"C:\Users\oohza\bb6"
REPORT = os.path.join(BASE, "reports", "S4_report.md")
CSV_PATH = os.path.join(BASE, "reports", "gpu_B_b511_c1023.csv")
SEED = 20260911
T_START = time.time()

# ===========================================================================
# 1) Décodage de la machine
# ===========================================================================
SPEC = "1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD"
BLOCKS = SPEC.split("_")
assert len(BLOCKS) == 6, "spec invalide : %d blocs" % len(BLOCKS)

WRITE = [0] * 12   # indexé par état*2 + symbole lu (0/1)
MOVE = [0] * 12    # +1 = R, -1 = L
NEXT = [-1] * 12   # -1 = arrêt (transition indéfinie)

for _s, _blk in enumerate(BLOCKS):
    assert len(_blk) == 6, "bloc invalide : %r" % (_blk,)
    for _v in range(2):
        _tok = _blk[3 * _v:3 * _v + 3]
        _i = 2 * _s + _v
        if _tok == "---":
            NEXT[_i] = -1
        else:
            assert _tok[0] in "01" and _tok[1] in "LR" and _tok[2] in "ABCDEF", (_tok,)
            WRITE[_i] = 1 if _tok[0] == "1" else 0
            MOVE[_i] = 1 if _tok[1] == "R" else -1
            NEXT[_i] = ord(_tok[2]) - 65


def tok_str(i):
    if NEXT[i] < 0:
        return "---"
    return "%d%s%s" % (WRITE[i], "L" if MOVE[i] < 0 else "R", "ABCDEF"[NEXT[i]])


# ===========================================================================
# 2) Rapport (append au fil de l'eau)
# ===========================================================================
def report(text, mode="a"):
    d = os.path.dirname(REPORT)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(REPORT, mode, encoding="utf-8", newline="\n") as f:
        f.write(text)
    sys.stdout.write(text)


def cfg(b, c):
    return "(%d,%d)" % (b, c)


# ===========================================================================
# 3) Simulateur
# ===========================================================================
def make_tape(b, c, max_steps):
    """Ruban (bytearray) pour la config (b,c) ; marge suffisante pour max_steps."""
    size = 2 * max_steps + b + c + 256
    hp = max_steps + 128
    tape = bytearray(size)
    for i in range(b):
        tape[hp + 1 + i] = 1
    base2 = hp + b + 3
    for i in range(c):
        tape[base2 + i] = 1
    if b > 0:
        lm = hp + 1
        rm = (hp + b + 2 + c) if c > 0 else (hp + b)
    elif c > 0:
        lm = hp + 3
        rm = hp + 2 + c
    else:
        lm = None
        rm = None
    return tape, hp, lm, rm


def run(tape, hp, lm, rm, max_steps, stop_on_det):
    """Boucle principale. Retourne (steps, reason, dets, lm, rm, compteurs).

    reason : 'det' (arrêt sur détection, si stop_on_det), 'halt', 'cap'.
    lm/rm : bornes maintenues pour accélérer la détection (aucun 1 à gauche de
    lm / à droite de rm), mises à jour de façon amortie.
    """
    tp = tape
    NX = NEXT
    WR = WRITE
    MV = MOVE
    s2 = 0            # état A = 0 (on suit 2*état)
    step = 0
    dets = []
    n_pre = 0         # occurrences du préconditionnement (état A, lecture 0)
    n_lp = 0          # passages du contrôle « gauche tout à zéro »
    n_walk = 0        # cellules parcourues par les scans vers la droite / gauche
    n_down = 0        # cellules parcourues par les scans vers la gauche (rm)
    while True:
        # ---- test de détection de configuration ----
        if s2 == 0 and tp[hp] == 0:
            n_pre += 1
            okL = True
            if lm is None:
                lm = hp
            elif lm < hp:
                k = lm
                while k < hp:
                    if tp[k] == 1:
                        break
                    k += 1
                    n_walk += 1
                if k < hp:
                    lm = k          # un 1 subsiste à gauche : échec
                    okL = False
                else:
                    lm = hp
            if okL:
                n_lp += 1
                j = hp + 1
                b2 = 0
                while tp[j] == 1:
                    b2 += 1
                    j += 1
                    n_walk += 1
                if tp[j] == 0 and tp[j + 1] == 0:
                    j += 2
                    c2 = 0
                    while tp[j] == 1:
                        c2 += 1
                        j += 1
                        n_walk += 1
                    L = j - 1       # dernière position du motif 1^b2 00 1^c2
                    okR = True
                    if rm is not None and rm > L:
                        k = rm
                        while k > L:
                            if tp[k] == 1:
                                okR = False
                                break
                            k -= 1
                            n_down += 1
                        rm = k if not okR else L
                    if okR:
                        dets.append((step, b2, c2))
                        if stop_on_det and step > 0:
                            return step, "det", dets, lm, rm, (n_pre, n_lp, n_walk, n_down)
        # ---- limite de pas ----
        if step >= max_steps:
            return step, "cap", dets, lm, rm, (n_pre, n_lp, n_walk, n_down)
        # ---- transition (ou arrêt) ----
        i = s2 + tp[hp]
        ns = NX[i]
        if ns < 0:
            return step, "halt", dets, lm, rm, (n_pre, n_lp, n_walk, n_down)
        w = WR[i]
        tp[hp] = w
        if w:
            if lm is None or hp < lm:
                lm = hp
            if rm is None or hp > rm:
                rm = hp
        hp += MV[i]
        s2 = ns + ns
        step += 1


STATS = {"steps": 0, "dets": 0, "pre": 0, "lp": 0, "walk": 0, "down": 0, "sims": 0}


def sim(b, c, cap, stop_on_det, acc=True):
    tape, hp, lm, rm = make_tape(b, c, cap)
    step, reason, dets, lm2, rm2, cnt = run(tape, hp, lm, rm, cap, stop_on_det)
    if acc:
        STATS["steps"] += step
        STATS["dets"] += len(dets)
        STATS["pre"] += cnt[0]
        STATS["lp"] += cnt[1]
        STATS["walk"] += cnt[2]
        STATS["down"] += cnt[3]
        STATS["sims"] += 1
    return step, reason, dets


# ===========================================================================
# 4) Données CSV (test (d)) — seule lecture de données du projet
# ===========================================================================
def load_csv():
    """Format : 'CASE b c HIT nb nc steps' et (bloc b=1) 'CASE 1 c HALT steps'."""
    rows = {}
    with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split()
            if not parts or parts[0] != "CASE":
                continue
            if len(parts) == 7:
                b = int(parts[1])
                if b <= 256:
                    rows[(b, int(parts[2]))] = (parts[3], int(parts[4]), int(parts[5]), int(parts[6]))
            elif len(parts) == 5:
                b = int(parts[1])
                if b <= 256:
                    rows[(b, int(parts[2]))] = (parts[3], None, None, int(parts[4]))
    return rows


CSVROWS = {}
SUMMARY = {}
BLOCK_TIME = {}


def safe(name, fn):
    """Exécute un bloc, ajoute sa section au rapport, capture les exceptions."""
    s0 = dict(STATS)
    t0 = time.time()
    try:
        sec = fn()
    except Exception:
        tb = traceback.format_exc()
        report("\n## %s — ÉCHEC (exception)\n\n```\n%s\n```\n" % (name, tb))
        BLOCK_TIME[name] = (time.time() - t0, {k: STATS[k] - s0[k] for k in STATS})
        return False
    dt = time.time() - t0
    delta = {k: STATS[k] - s0[k] for k in STATS}
    sec += ("\n*Durée du bloc : %.1f s — simulations : %d — pas simulés : %d — "
            "détections : %d — contrôles (pré=%d, gauche=%d, marche=%d, descente=%d).*\n\n"
            % (dt, delta["sims"], delta["steps"], delta["dets"],
               delta["pre"], delta["lp"], delta["walk"], delta["down"]))
    BLOCK_TIME[name] = (dt, delta)
    report(sec)
    return True


# ===========================================================================
# 5) Blocs de tests
# ===========================================================================
def block_calibration():
    cap = 2_000_000
    step, reason, dets = sim(0, 0, cap, False)
    expected = [(45, 3, 1), (64, 0, 5), (107, 7, 1), (158, 2, 7),
                (274, 14, 1), (2640, 38, 1), (31346, 98, 1)]
    explist = [tuple(e) for e in expected]
    detset = set(dets)
    L = []
    L.append("\n## 0. Calibration (départ ruban vide, cap %s pas)\n" % format(cap, ",").replace(",", " "))
    L.append("\nDépart : ruban vide, tête position 0, état A. Fin : `%s` au pas %d ; "
             "%d détections.\n" % (reason, step, len(dets)))
    L.append("\n| # | pas | config détectée | statut |\n|---:|---:|:---|:---|\n")
    for idx, d in enumerate(dets):
        tag = "**attendue (brief)**" if d in explist else "additionnelle"
        L.append("| %d | %d | %s | %s |\n" % (idx + 1, d[0], cfg(d[1], d[2]), tag))
    nok = sum(1 for e in expected if e in detset)
    L.append("\n**Repères du brief : %d/7 conformes** (pas et config exacts).\n" % nok)
    for e in expected:
        if e not in detset:
            L.append("- ✘ MANQUante : %s au pas %d\n" % (cfg(e[1], e[2]), e[0]))
    extras = [d for d in dets if d not in explist]
    if extras:
        L.append("\nDétections additionnelles (non listées dans le brief) : %s.\n"
                 % ", ".join("%s@%d" % (cfg(d[1], d[2]), d[0]) for d in extras))
    L.append("\n*Note : `(0,0)@0` est la détection dégénérée du ruban vide lui-même. "
             "`(0,1)@10` et `(248,1)@434602` complètent la chaîne (lignes CSV "
             "`CASE 0 0 HIT 0 1 10`, `CASE 0 1 HIT 3 1 35`, `CASE 98 1 HIT 248 1 403256`).*\n")
    SUMMARY["calib"] = dict(n=nok, dets=list(dets), reason=reason, step=step)
    return "".join(L)


def block_a():
    CS = [0, 17, 256, 1023]
    total = 0
    ok = 0
    okcsv = 0
    viol = []
    per_c = {c: [0, 0, 0] for c in CS}   # [conformes, total, croisement CSV]
    examples = []
    steps_seen = []
    for b in range(3, 256, 2):
        m = (b - 3) // 2
        exp_steps = 2 * (m + 3) ** 2 + 1
        for c in CS:
            total += 1
            per_c[c][1] += 1
            nb_e = m
            nc_e = 4 + m + c
            cap = exp_steps + 5000
            step, reason, dets = sim(b, c, cap, True)
            got = dets[1] if len(dets) > 1 else None
            sane0 = (len(dets) >= 1 and dets[0] == (0, b, c))
            good = sane0 and (got == (exp_steps, nb_e, nc_e))
            if good:
                ok += 1
                per_c[c][0] += 1
                steps_seen.append(got[0])
            else:
                step2, reason2, dets2 = sim(b, c, cap, False)
                viol.append((b, c, reason, got, exp_steps, (nb_e, nc_e), sane0, reason2, dets2[:8]))
            r = CSVROWS.get((b, c))
            if r and r[1] is not None and got is not None and (r[1], r[2], r[3]) == (got[1], got[2], got[0]):
                okcsv += 1
                per_c[c][2] += 1
            if b in (3, 5, 127, 253, 255):
                examples.append((b, c, got, exp_steps, (nb_e, nc_e)))
    L = []
    L.append("\n## (a) Famille impaire — b impair 3..255, c ∈ {0, 17, 256, 1023}\n")
    L.append("\nLoi testée : prochaine config = `(m, 4+m+c)` avec `m=(b−3)/2`, "
             "en exactement `2(m+3)²+1` pas.\n")
    L.append("\n**Résultat : %d/%d cas conformes, %d violation(s).**\n" % (ok, total, len(viol)))
    L.append("\n| c | conformes | total | croisement CSV (3 voies) |\n|---:|---:|---:|---:|\n")
    for c in CS:
        L.append("| %d | %d | %d | %d/%d |\n" % (c, per_c[c][0], per_c[c][1], per_c[c][2], per_c[c][1]))
    if steps_seen:
        L.append("\nPas observés : min=%d, max=%d (formule : 19 … 33283).\n"
                 % (min(steps_seen), max(steps_seen)))
    L.append("\nExemples (b, c) → observé | attendu —\n\n")
    L.append("| (b,c) | observé | attendu |\n|:---|---:|:---|\n")
    for (b, c, got, exp_steps, (nb_e, nc_e)) in examples:
        g = "%s @ %d pas" % (cfg(got[1], got[2]), got[0]) if got else "AUCUNE"
        L.append("| %s | %s | %s @ %d pas |\n" % (cfg(b, c), g, cfg(nb_e, nc_e), exp_steps))
    if viol:
        L.append("\n### Violations\n\n")
        for v in viol[:20]:
            L.append("- %s : reason=%s, obtenu=%s, attendu=%s@%d, sane0=%s ; re-run reason=%s dets=%s\n"
                     % (cfg(v[0], v[1]), v[2], v[3], cfg(v[5][0], v[5][1]), v[4], v[6], v[7], v[8]))
        if len(viol) > 20:
            L.append("- … %d autres\n" % (len(viol) - 20))
    SUMMARY["a"] = dict(ok=ok, total=total, okcsv=okcsv, viol=len(viol))
    return "".join(L)


def block_b():
    CS = [0, 17, 256, 1023]
    total = 0
    ok = 0
    okcsv = 0
    viol = []
    step_mismatch_csv = []
    table = []
    for b in range(2, 65, 2):
        m = (b - 2) // 2
        row = []
        for c in CS:
            total += 1
            nb_e = 7 + 5 * m + c
            nc_e = 1
            r = CSVROWS.get((b, c))
            cap = (r[3] + 2000) if (r and r[3] is not None) else 3_000_000
            step, reason, dets = sim(b, c, cap, True)
            got = dets[1] if len(dets) > 1 else None
            sane0 = (len(dets) >= 1 and dets[0] == (0, b, c))
            good = sane0 and got is not None and got[1] == nb_e and got[2] == nc_e
            if good:
                ok += 1
            else:
                step2, reason2, dets2 = sim(b, c, cap + 5000, False)
                viol.append((b, c, reason, got, (nb_e, nc_e), sane0, reason2, dets2[:8]))
            if r and r[1] is not None and got is not None:
                if (r[1], r[2]) == (nb_e, nc_e) == (got[1], got[2]):
                    if r[3] == got[0]:
                        okcsv += 1
                    else:
                        step_mismatch_csv.append((b, c, r[3], got[0]))
            row.append(got[0] if (got and got[1] == nb_e and got[2] == nc_e) else None)
        table.append((b, m, row))
    L = []
    L.append("\n## (b) Famille paire — b pair 2..64, c ∈ {0, 17, 256, 1023}\n")
    L.append("\nLoi testée : prochaine config = `(7+5m+c, 1)` avec `m=(b−2)/2` "
             "(pas de loi sur le nombre de pas : on consigne, et on croise avec le CSV).\n")
    L.append("\n**Résultat : %d/%d configs cibles atteintes** ; %d violation(s).\n" % (ok, total, len(viol)))
    L.append("\n| b | m | pas (c=0) | pas (c=17) | pas (c=256) | pas (c=1023) |\n"
             "|---:|---:|---:|---:|---:|---:|\n")
    for (b, m, row) in table:
        cells = " | ".join(("?" if v is None else str(v)) for v in row)
        L.append("| %d | %d | %s |\n" % (b, m, cells))
    L.append("\nCroisement CSV (config ET pas identiques au simulateur) : **%d/%d**.\n" % (okcsv, total))
    if step_mismatch_csv:
        L.append("\nÉcarts de pas vs CSV (même config) : %s\n"
                 % "; ".join("%s csv=%d sim=%d" % (cfg(b, c), a, b2) for (b, c, a, b2) in step_mismatch_csv))
    ctrl = {}
    for (b, m, row) in table:
        if b in (48, 62):
            ctrl[b] = row
    if 48 in ctrl:
        s48 = ctrl[48][0]
        s62 = ctrl.get(62, [None])[0]
        L.append("\nContrôles du brief : (48,0) → (122,1) @ 54129 pas — observé @ %s : %s ; "
                 "(62,0) → (157,1) @ 110052 pas — observé @ %s : %s.\n"
                 % (s48, "✔" if s48 == 54129 else "✘", s62, "✔" if s62 == 110052 else "✘"))
    if viol:
        L.append("\n### Violations\n\n")
        for v in viol[:20]:
            L.append("- %s : reason=%s, obtenu=%s, attendu=%s ; re-run reason=%s dets=%s\n"
                     % (cfg(v[0], v[1]), v[2], v[3], cfg(v[4][0], v[4][1]), v[6], v[7]))
    SUMMARY["b"] = dict(ok=ok, total=total, okcsv=okcsv, viol=len(viol), step_mismatch=len(step_mismatch_csv))
    return "".join(L)


def block_c():
    out = []
    for k in range(2, 11):
        b = 2 ** k - 3
        exp_steps = (2 * 4 ** k + 3 * k - 2) // 3
        cap = exp_steps + 1000
        step, reason, dets = sim(b, 1, cap, False)
        out.append((k, b, exp_steps, step, reason, dets))
    # bonus : le CSV donne CASE 1 c HALT 12 pour tout c (famille d'arrêt k=2 élargie)
    bonus = []
    for c in (0, 1, 17, 256, 1023):
        step, reason, dets = sim(1, c, 100, False)
        bonus.append((c, step, reason))
    L = []
    L.append("\n## (c) Famille d'arrêt — (b, c) = (2^k − 3, 1), k = 2..10\n")
    L.append("\nLoi testée : arrêt après exactement `(2·4^k + 3k − 2)/3` pas.\n")
    L.append("\n| k | b | formule | observé | arrêt ? | détections intermédiaires |\n"
             "|---:|---:|---:|---:|:---:|:---|\n")
    nok = 0
    for (k, b, exp_steps, step, reason, dets) in out:
        okk = (reason == "halt" and step == exp_steps)
        nok += 1 if okk else 0
        interm = [d for d in dets if d[0] > 0]
        im = ", ".join("%s@%d" % (cfg(d[1], d[2]), d[0]) for d in interm[:8]) or "—"
        L.append("| %d | %d | %d | %d | %s | %s |\n"
                 % (k, b, exp_steps, step, "✔" if okk else "✘ (" + reason + ")", im))
    L.append("\n**Résultat : %d/9 conformes.**\n" % nok)
    L.append("\nBonus (extension k=2) : lignes CSV `CASE 1 c HALT 12` pour tout c — "
             "vérifié par simulation : %s.\n"
             % ", ".join("c=%d → %s @ %d" % (c, r, s) for (c, s, r) in bonus))
    SUMMARY["c"] = dict(ok=nok, total=9, bonus=[(c, s, r) for (c, s, r) in bonus])
    return "".join(L)


def block_d():
    pool = sorted([(b, c) for (b, c), v in CSVROWS.items()
                   if b <= 255 and v[0] == "HIT" and v[1] is not None and v[3] <= 2_000_000])
    rnd = random.Random(SEED)
    nreq = min(40, len(pool))
    sample = rnd.sample(pool, nreq)
    sample.sort()
    results = []
    ok = 0
    for (b, c) in sample:
        r = CSVROWS[(b, c)]
        nb_e, nc_e, st_e = r[1], r[2], r[3]
        cap = st_e + 10
        step, reason, dets = sim(b, c, cap, True)
        got = dets[1] if len(dets) > 1 else None
        sane0 = (len(dets) >= 1 and dets[0] == (0, b, c))
        good = sane0 and (got == (st_e, nb_e, nc_e))
        diag = None
        if not good:
            step2, reason2, dets2 = sim(b, c, st_e + 5000, False)
            diag = (reason, reason2, dets2[:6])
        else:
            ok += 1
        results.append(((b, c), r, got, good, diag))
    # cas explicite du brief
    b, c = 126, 1023
    r = CSVROWS.get((b, c))
    exp126 = (834498, 1340, 1)          # ordre (pas, next_b, next_c)
    cap = (r[3] + 10) if (r and r[3] is not None) else 834_500
    step, reason, dets = sim(b, c, cap, True)
    got126 = dets[1] if len(dets) > 1 else None
    good126 = (got126 == exp126)
    L = []
    L.append("\n## (d) Échantillon aléatoire du CSV `gpu_B_b511_c1023.csv`\n")
    L.append("\nFormat du fichier : `CASE b c HIT nb nc steps` (523264 lignes) et "
             "`CASE 1 c HALT steps` (1024 lignes). Tirage : %d lignes HIT avec "
             "`b ≤ 255` **et** `steps ≤ 2 000 000` (pool = %d lignes), graine `random.seed(%d)`.\n"
             % (nreq, len(pool), SEED))
    L.append("\nPour chaque ligne : re-simulation Python depuis `(b,c)` ; la **prochaine config** "
             "détectée et le **nombre de pas** doivent correspondre exactement.\n")
    L.append("\n| # | (b,c) | CSV : prochaine @ pas | Simu Python | verdict |\n"
             "|---:|:---|:---|:---|:---:|\n")
    for i, (key, rrow, gr, gg, gd) in enumerate(results, 1):
        nb_e, nc_e, st_e = rrow[1], rrow[2], rrow[3]
        g = "%s @ %d" % (cfg(gr[1], gr[2]), gr[0]) if gr else "AUCUNE (%s)" % (gd[0] if gd else "?")
        L.append("| %d | %s | %s @ %d | %s | %s |\n" % (i, cfg(key[0], key[1]), cfg(nb_e, nc_e), st_e, g, "✔" if gg else "✘"))
    L.append("\n**Résultat : %d/%d lignes conformes.**\n" % (ok, nreq))
    L.append("\nCas explicite du brief : `(126,1023)` → `(1340,1)` @ 834498 pas — "
             "observé `%s` @ %s : **%s**.\n"
             % (cfg(got126[1], got126[2]) if got126 else "AUCUNE", got126[0] if got126 else "—", "✔ conforme" if good126 else "✘ ÉCART"))
    bad = [(key, rrow, gr, gd) for (key, rrow, gr, gg, gd) in results if not gg]
    if bad:
        L.append("\n### Écarts\n\n")
        for (key, rrow, gr, gd) in bad[:20]:
            L.append("- %s : CSV (%d,%d)@%d ; simu obtenu %s ; détails reason=%s, %s, dets=%s\n"
                     % (cfg(key[0], key[1]), rrow[1], rrow[2], rrow[3], gr,
                        gd[0] if gd else "?", gd[1] if gd else "?", gd[2] if gd else "?"))
    SUMMARY["d"] = dict(ok=ok, total=nreq, pool=len(pool), ok126=good126, got126=got126)
    return "".join(L)


def build_header():
    py = platform.python_version()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    L = []
    L.append("# S4 — Vérification indépendante des lois de « Space Needle » (BB(6))\n\n")
    L.append("**Machine** : `%s` (6 états A–F, format bbchallenge ; `---` = transition "
             "indéfinie ⇒ arrêt).\n\n" % SPEC)
    L.append("Simulateur **Python réécrit intégralement de zéro** pour cette vérification "
             "(aucun code du projet — ni Rust ni Python — n'a été lu ; seule *donnée* lue : "
             "`reports/gpu_B_b511_c1023.csv`, pour le test (d)).\n\n")
    L.append("**Décodage** (bloc = 2 transitions `[écrit][L/R][état]` ; 1re = si lecture 0, "
             "2e = si lecture 1) :\n\n")
    L.append("| État | lecture 0 | lecture 1 |\n|:---:|:---:|:---:|\n")
    for s in range(6):
        L.append("| %s | %s | %s |\n" % ("ABCDEF"[s], tok_str(2 * s), tok_str(2 * s + 1)))
    L.append("\n\n**Config (b,c)** = `0^∞ ⟨A⟩ 1^b 00 1^c 0^∞` : tête sur la cellule "
             "immédiatement à gauche du premier `1` du bloc b (pour b=0 : immédiatement "
             "à gauche des deux zéros séparateurs), état A, lecture 0.\n\n")
    L.append("**Détection** : état A ∧ tête lit 0 ∧ toutes les cellules à gauche = 0 ∧ "
             "à droite de la tête le ruban est exactement `1^b 00 1^c` suivi de zéros "
             "⇒ on enregistre (b,c) au pas courant. Convention de pas : nombre de "
             "transitions exécutées (détection « au pas t » = après la t-ième transition).\n\n")
    L.append("**Environnement** : Python %s, %s ; script `C:\\Users\\oohza\\bb6\\s4\\check.py` ; "
             "commande `python C:\\Users\\oohza\\bb6\\s4\\check.py` ; graine (d) = %d ; "
             "démarrage %s.\n\n---\n" % (py, platform.platform(), SEED, now))
    return "".join(L)


def build_conclusion():
    L = []
    L.append("\n## Conclusion\n\n")
    L.append("| Bloc | Vérification | Résultat | Durée |\n|:---|:---|:---|:---:|\n")
    cal = SUMMARY.get("calib", {})
    L.append("| 0 | Calibration ruban vide (7 repères du brief) | %d/7 | %s |\n"
             % (cal.get("n", 0), "%.1f s" % BLOCK_TIME.get("Calibration", (0,))[0]))
    a = SUMMARY.get("a", {})
    L.append("| (a) | Famille impaire : 508 cas | %d/508 conformes, %d violations | %s |\n"
             % (a.get("ok", 0), a.get("viol", 0), "%.1f s" % BLOCK_TIME.get("(a) famille impaire", (0,))[0]))
    b = SUMMARY.get("b", {})
    L.append("| (b) | Famille paire : 128 cas | %d/128 conformes, %d violations | %s |\n"
             % (b.get("ok", 0), b.get("viol", 0), "%.1f s" % BLOCK_TIME.get("(b) famille paire", (0,))[0]))
    c = SUMMARY.get("c", {})
    L.append("| (c) | Famille d'arrêt : k=2..10 | %d/9 conformes | %s |\n"
             % (c.get("ok", 0), "%.1f s" % BLOCK_TIME.get("(c) famille d'arrêt", (0,))[0]))
    d = SUMMARY.get("d", {})
    L.append("| (d) | Échantillon CSV : 40 lignes + (126,1023) | %d/%d, cas 126 : %s | %s |\n"
             % (d.get("ok", 0), d.get("total", 40), "✔" if d.get("ok126") else "✘",
                "%.1f s" % BLOCK_TIME.get("(d) échantillon CSV", (0,))[0]))
    L.append("\nTotaux : %d simulations, %d pas simulés, %d détections de config ; "
             "durée totale du script : %.1f s.\n"
             % (STATS["sims"], STATS["steps"], STATS["dets"], time.time() - T_START))
    L.append("\n*Verdict : voir les sections ci-dessus (chaque bloc conclut et toute "
             "violation éventuelle y figure en détail).*\n")
    return "".join(L)


def main():
    global CSVROWS
    report(build_header(), mode="w")
    try:
        CSVROWS = load_csv()
    except Exception:
        report("\n> ⚠ Lecture du CSV impossible :\n```\n%s\n```\n" % traceback.format_exc())
    safe("Calibration", block_calibration)
    safe("(a) famille impaire", block_a)
    safe("(b) famille paire", block_b)
    safe("(c) famille d'arrêt", block_c)
    safe("(d) échantillon CSV", block_d)
    report(build_conclusion())
    print("\n=== FIN (%.1f s) ===" % (time.time() - T_START))


if __name__ == "__main__":
    main()
