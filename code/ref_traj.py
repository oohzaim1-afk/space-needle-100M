#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ref_traj.py - S1 : re-execution independante de la recurrence "Space Needle"
(Busy Beaver BB(6), bbchallenge) + statistiques exactes.

Recurrence telle qu'enoncee (a reproduire, non supposee) :
    b0 = 6
    v  = v2(bn)                  # valuation 2-adique (nb de zeros de poids faible)
    m  = bn >> v                 # partie impaire de bn
    b(n+1) = bn + v + (3*(m-1))//2
    HALT si bn est une puissance de 2 : (bn & (bn-1)) == 0
Equivalence utilisee et verifiee : (b & (b-1)) == 0  <=>  m == 1

Les 10 premiers termes publies sont assertes au demarrage :
    6, 10, 17, 41, 101, 251, 626, 1095, 2736, 2995
En cas de desaccord : arret immediat, aucune statistique calculee.

Usage : python ref_traj.py [N=100000] [stem=S1_traj_report] [calib=N:secondes]
Sorties (dans REF_TRAJ_OUT si defini, sinon le dossier du script) :
    <stem>.json, <stem>.md, <stem>.stdout.txt
Stdlib uniquement : json, math, os, sys, time.

Note (2026-09-14) : version publiee. Le chemin de sortie est parametre
(REF_TRAJ_OUT si defini, sinon le dossier du script). Le code numerique est
inchange par rapport a l'execution d'origine (cf. data/S1_traj_report.*).
"""

import json
import math
import os
import sys
import time

# Dossier de sortie : REF_TRAJ_OUT si defini, sinon le dossier du script.
# (Chemin parametre pour la publication du 2026-09-14 ; code numerique inchange.)
REPORTS_DIR = os.environ.get("REF_TRAJ_OUT") or os.path.dirname(os.path.abspath(__file__))

PUBLISHED10 = [6, 10, 17, 41, 101, 251, 626, 1095, 2736, 2995]
CHECKPOINTS = (1000, 100000)
K_MAX = 60
N_PREDICT = 17_000_000
V_BIN_MAX = 40


def v_and_odd(b):
    """(v, m) : valuation 2-adique (nb de zeros de poids faible) et partie impaire."""
    v = (b & -b).bit_length() - 1
    return v, b >> v


def main():
    t_script0 = time.perf_counter()

    N = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    stem = sys.argv[2] if len(sys.argv) > 2 else "S1_traj_report"
    calib = None
    if len(sys.argv) > 3 and sys.argv[3].startswith("calib="):
        _cn, _cs = sys.argv[3][6:].split(":", 1)
        calib = {"N": int(_cn), "seconds": float(_cs)}
    if N < 9:
        N = 9

    # desactive le plafond int<->str (Python 3.11+), requis pour len(str(bn))
    for cap in (0, 100_000_000):
        try:
            sys.set_int_max_str_digits(cap)
            break
        except AttributeError:
            break
        except ValueError:
            continue

    lines = []

    def log(s=""):
        s = str(s)
        print(s, flush=True)
        lines.append(s)

    utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    log("### ref_traj.py | Space Needle recurrence | independent run")
    log("utc                 : " + utc)
    log("python              : " + sys.version.replace("\n", " "))
    log("sys.platform        : " + sys.platform)
    log("executable          : " + sys.executable)
    log("N steps requested   : " + str(N))

    probe = math.log(1 << 4096)
    log("probe math.log(2**4096) = %.9f" % probe)
    assert v_and_odd(6) == (1, 3)
    assert v_and_odd(2736) == (4, 171)
    assert v_and_odd(1024) == (10, 1)
    log("self-tests v_and_odd : OK")
    log("")

    # ---------------- phase 1 : prefixe publie (9 mises a jour -> 10 termes) ----------------
    b = 6
    seq = [b]
    for i in range(9):
        v, m = v_and_odd(b)
        assert (m == 1) == ((b & (b - 1)) == 0)
        inc_lit = v + (3 * (m - 1)) // 2
        inc_eqv = v + 3 * (m >> 1)
        assert inc_lit == inc_eqv, "formes equivalentes divergentes (n=%d)" % i
        b = b + inc_lit
        seq.append(b)

    prefix_ok = (seq == PUBLISHED10)
    log("prefix recompute    : " + ", ".join(str(x) for x in seq))
    log("prefix published    : " + ", ".join(str(x) for x in PUBLISHED10))
    log("prefix assert       : " + ("OK" if prefix_ok else "MISMATCH"))

    if not prefix_ok:
        log("ABORT : mismatch du prefixe publie - aucune statistique calculee.")
        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)
            with open(os.path.join(REPORTS_DIR, stem + "_FAILED.json"), "w",
                      encoding="utf-8", newline="\n") as f:
                json.dump({"utc": utc, "status": "PREFIX_MISMATCH",
                           "recomputed": seq, "published": PUBLISHED10,
                           "stdout_raw": "\n".join(lines)}, f, indent=2, ensure_ascii=False)
        except OSError:
            pass
        raise SystemExit(2)

    log("")

    # ---------------- phase 2 : run principal ----------------
    v_counts = [0] * (V_BIN_MAX + 1)
    v_gt = 0
    max_v = -1
    max_v_at = None
    sum_ln = 0.0
    sum_ln2 = 0.0
    n_ratios = 0
    halted = False
    halt_n = None
    halt_b = None
    halt_v = None
    checkpoints = {}

    prev = b  # b_9
    t0 = time.perf_counter()
    for n in range(9, N):
        v, m = v_and_odd(prev)
        if v <= V_BIN_MAX:
            v_counts[v] += 1
        else:
            v_gt += 1
        if v > max_v:
            max_v = v
            max_v_at = n
        if m == 1:  # equivaut a (prev & (prev-1)) == 0
            halted = True
            halt_n = n
            halt_b = prev
            halt_v = v
            log("!!! HALT CONDITION MET : b_%d = 2^%d (puissance de 2) - arret immediat." % (n, v))
            break
        if n < 1009 or (n % 50000 == 0):
            assert ((prev & (prev - 1)) == 0) == (m == 1), "cross-check halt (n=%d)" % n
            assert (v + (3 * (m - 1)) // 2) == (v + 3 * (m >> 1))
        nxt = prev + v + 3 * (m >> 1)
        lr = math.log(nxt) - math.log(prev)
        sum_ln += lr
        sum_ln2 += lr * lr
        n_ratios += 1
        prev = nxt
        if (n + 1) in CHECKPOINTS:
            checkpoints[n + 1] = prev
    t1 = time.perf_counter()

    if not halted:
        vf, mf = v_and_odd(prev)
        if mf == 1:
            halted = True
            halt_n = N
            halt_b = prev
            halt_v = vf
            log("!!! HALT CONDITION MET au dernier terme : b_%d = 2^%d" % (N, vf))

    M = halt_n if halted else N
    last = halt_b if halted else prev
    phase2_s = t1 - t0

    if halted:
        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)
            with open(os.path.join(REPORTS_DIR, stem + "_HALT_b.txt"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write(str(halt_b) + "\n")
        except OSError:
            pass

    s_last = str(last)
    digits_last = len(s_last)
    bitlen_last = last.bit_length()
    log10_last = math.log10(last)

    log("run finished        : M = %d mises a jour appliquees (b_0 -> b_%d)" % (M, M))
    log("halted early        : " + ("YES" if halted else "no"))
    log("phase2 wall time    : %.3f s" % phase2_s)
    log("n_ratios measured   : %d" % n_ratios)
    log("last term           : %d decimal digits | bit_length %d | log10 ~ %.6f" %
        (digits_last, bitlen_last, log10_last))
    log("last term head      : " + s_last[:48])
    log("last term tail      : " + s_last[-48:])

    mean_ln = sum_ln / n_ratios if n_ratios else 0.0
    mean_ln2 = sum_ln2 / n_ratios if n_ratios else 0.0
    var_emp = mean_ln2 - mean_ln * mean_ln
    sd_emp = math.sqrt(var_emp) if var_emp > 0.0 else 0.0
    mean_e2e = (math.log(last) - math.log(6.0)) / M

    c1 = math.fsum((2.0 ** -(k + 1)) * math.log(1.0 + 3.0 * (2.0 ** -(k + 1)))
                   for k in range(K_MAX + 1))
    c2 = math.fsum((2.0 ** -(k + 1)) * (math.log(1.0 + 3.0 * (2.0 ** -(k + 1))) ** 2)
                   for k in range(K_MAX + 1))
    c4 = math.fsum((2.0 ** -(k + 1)) * (math.log(1.0 + 3.0 * (2.0 ** -(k + 1))) ** 4)
                   for k in range(K_MAX + 1))
    var_c = c2 - c1 * c1
    sigma_c = math.sqrt(var_c) if var_c > 0.0 else 0.0
    var2_c = c4 - c2 * c2
    sd2_c = math.sqrt(var2_c) if var2_c > 0.0 else 0.0
    z1 = (mean_ln - c1) / (sigma_c / math.sqrt(n_ratios)) if (n_ratios > 0 and sigma_c > 0.0) else 0.0
    z2 = (mean_ln2 - c2) / (sd2_c / math.sqrt(n_ratios)) if (n_ratios > 0 and sd2_c > 0.0) else 0.0

    ln10 = math.log(10.0)
    digits_simple = N_PREDICT * c1 / ln10
    digits_incl_b0 = (math.log(6.0) + N_PREDICT * c1) / ln10
    sd_digits = sigma_c * math.sqrt(N_PREDICT) / ln10

    n_vobs = sum(v_counts) + v_gt
    exp_counts = [n_vobs * (2.0 ** -(k + 1)) for k in range(V_BIN_MAX + 1)]
    exp_gt = n_vobs * (2.0 ** -(V_BIN_MAX + 1))

    chi2 = None
    chi2_df = None
    chi2_K = None
    if n_vobs >= 100:
        K = int(math.log2(n_vobs / 5.0))
        if K < 2:
            K = 2
        if K > V_BIN_MAX:
            K = V_BIN_MAX
        obs_b = [float(x) for x in v_counts[:K]] + [float(sum(v_counts[K:]) + v_gt)]
        exp_b = [exp_counts[i] for i in range(K)] + [sum(exp_counts[K:]) + exp_gt]
        chi2 = math.fsum((o - e) * (o - e) / e for o, e in zip(obs_b, exp_b) if e > 0.0)
        chi2_df = K
        chi2_K = K

    total_compute_s = time.perf_counter() - t_script0

    log("")
    log("empirical means (phase2 window, %d transitions):" % n_ratios)
    log("  mean ln(G)        = %.12f" % mean_ln)
    log("  mean ln(G)^2      = %.12f" % mean_ln2)
    log("  var  ln(G)        = %.12f (sd %.12f)" % (var_emp, sd_emp))
    log("closed form (k=0..%d):" % K_MAX)
    log("  E[ln G]           = %.12f" % c1)
    log("  E[ln G^2]         = %.12f" % c2)
    log("  var               = %.12f (sigma %.12f)" % (var_c, sigma_c))
    log("  z(mean lnG)       = %.3f" % z1)
    log("  z(mean lnG^2)     = %.3f" % z2)
    log("end-to-end mean ln growth (b0->b_%d over %d steps) = %.12f" % (M, M, mean_e2e))
    log("")
    log("prediction N = %d :" % N_PREDICT)
    log("  digits ~ N*c/ln10           = %.1f" % digits_simple)
    log("  digits ~ (ln b0 + N*c)/ln10 = %.1f" % digits_incl_b0)
    log("  sd digits (1 sigma)         = %.1f" % sd_digits)
    log("v max = %d at n=%s ; v obs = %d" % (max_v, str(max_v_at), n_vobs))
    if chi2 is not None:
        log("chi2(v hist vs 2^-(k+1)) = %.2f (df=%d, pooled from k=%d)" % (chi2, chi2_df, chi2_K))
    log("total compute time  : %.3f s" % total_compute_s)

    cp_ser = {}
    for idx in sorted(checkpoints):
        sval = str(checkpoints[idx])
        entry = {"index": idx, "decimal_digits": len(sval),
                 "head": sval[:48], "tail": sval[-48:]}
        if len(sval) <= 4000:
            entry["full"] = sval
        cp_ser[str(idx)] = entry

    report = {
        "task": "S1 - Space Needle recurrence independent verification + statistics",
        "generated_utc": utc,
        "script": os.path.abspath(__file__),
        "argv": list(sys.argv),
        "env": {
            "python_version": sys.version.replace("\n", " "),
            "executable": sys.executable,
            "platform": sys.platform,
            "cwd": os.getcwd(),
        },
        "recurrence": "b[n+1] = b[n] + v + (3*(m-1))//2 ; v = v2(b[n]) ; m = b[n] >> v ; b[0] = 6",
        "halt_condition": "b power of two <=> (b & (b-1)) == 0 <=> m == 1",
        "prefix_check": {"published": PUBLISHED10, "recomputed": seq, "match": prefix_ok},
        "calibration": calib,
        "run": {
            "N_steps_requested": N,
            "total_updates_applied": M,
            "halted_early": halted,
            "phase2_seconds": phase2_s,
            "total_compute_seconds": total_compute_s,
            "n_ratios": n_ratios,
            "n_v_observations": n_vobs,
        },
        "halt": {
            "halted": halted,
            "n": halt_n,
            "v": halt_v,
            "display": ("2^%d" % halt_v) if halted else None,
            "decimal_digits": len(str(halt_b)) if halted else None,
            "bit_length": halt_b.bit_length() if halted else None,
        },
        "last_term": {
            "index": M,
            "decimal_digits": digits_last,
            "bit_length": bitlen_last,
            "log10_approx": log10_last,
            "head48": s_last[:48],
            "tail48": s_last[-48:],
        },
        "valuation": {
            "max_v": max_v,
            "max_v_at_n": max_v_at,
            "histogram_v_0_40": {str(k): v_counts[k] for k in range(V_BIN_MAX + 1)},
            "count_v_gt40": v_gt,
            "expected_counts_geometric": {str(k): exp_counts[k] for k in range(V_BIN_MAX + 1)},
            "expected_gt40": exp_gt,
            "chi2_vs_geometric": chi2,
            "chi2_df": chi2_df,
            "chi2_pool_from_k": chi2_K,
        },
        "empirical": {
            "window": "phase2 transitions n=9..M-1; ratios measured = %d" % n_ratios,
            "mean_ln_G": mean_ln,
            "mean_ln_G_sq": mean_ln2,
            "var_ln_G": var_emp,
            "sd_ln_G": sd_emp,
            "mean_ln_growth_end_to_end": mean_e2e,
        },
        "closed_form": {
            "k_max": K_MAX,
            "formula": "E[f(G)] = fsum_{k=0..K} 2^-(k+1) * f(1 + 3*2^-(k+1))",
            "E_ln_G": c1,
            "E_ln_G_sq": c2,
            "var_ln_G": var_c,
            "sigma_ln_G": sigma_c,
            "E_ln_G_4th": c4,
            "var_ln_G_sq": var2_c,
            "z_mean_ln_G": z1,
            "z_mean_ln_G_sq": z2,
        },
        "prediction_N_17e6": {
            "N": N_PREDICT,
            "c_per_step": c1,
            "c_per_step_decimal_digits": c1 / ln10,
            "digits_simple": digits_simple,
            "digits_incl_b0": digits_incl_b0,
            "sd_digits": sd_digits,
        },
        "checkpoints": cp_ser,
        "stdout_raw": "\n".join(lines),
    }

    # ---------------- rapport Markdown ----------------
    md = []
    ap = md.append
    ap("# S1 — Space Needle : ré-exécution indépendante de la récurrence + statistiques")
    ap("")
    ap("- **Généré (UTC)** : " + utc)
    ap("- **Script** : `" + os.path.abspath(__file__) + "` (stdlib : json, math, os, sys, time)")
    ap("- **Python** : " + sys.version.replace("\n", " "))
    ap("- **Exécutable** : `" + sys.executable + "` — plateforme : " + sys.platform)
    ap("- **N pas demandés** : %d — mises à jour appliquées M = %d — arrêt anticipé (halt) : %s"
       % (N, M, "oui" if halted else "non"))
    if calib:
        ap("- **Calibration** : N=%d exécuté en %.3f s (boucle) → décision : N=%d pour le run final"
           % (calib["N"], calib["seconds"], N))
    ap("")
    ap("## Récurrence testée")
    ap("")
    ap("```")
    ap("b0 = 6 ; v = v2(bn) ; m = bn >> v ;  b(n+1) = b(n) + v + (3*(m-1))//2")
    ap("HALT si bn puissance de 2 <=> (bn & (bn-1)) == 0 <=> m == 1")
    ap("```")
    ap("")
    ap("## 1. Contrôle du préfixe publié (10 premiers termes)")
    ap("")
    ap("| n | recalculé | publié | match |")
    ap("|---:|---:|---:|:---:|")
    for i, (a_, b_) in enumerate(zip(seq, PUBLISHED10)):
        ap("| %d | %d | %d | %s |" % (i, a_, b_, "oui" if a_ == b_ else "NON"))
    ap("")
    ap("**Assert** : " + ("OK — les 10 termes correspondent aux valeurs publiées." if prefix_ok else "MISMATCH"))
    ap("")
    ap("## 2. Exécution")
    ap("")
    ap("- Boucle phase 2 : **%.3f s** pour %d transitions mesurées (b9 → b%d)" % (phase2_s, n_ratios, M))
    if n_ratios > 0:
        ap("- Moyenne : **%.2f µs/pas** (phase 2)" % (1e6 * phase2_s / n_ratios))
    ap("- Temps total de calcul du script : %.3f s" % total_compute_s)
    if calib:
        ap("- Calibration utilisée pour le choix de N : N=%d → %.1f s mesuré ; projection N=1e6 ≈ %.0f s (loi ~N²)"
           % (calib["N"], calib["seconds"], calib["seconds"] * 100.0))
    ap("")
    ap("## 3. Dernier terme")
    ap("")
    ap("- b%d : **%d chiffres décimaux** (bit_length = %d ; log10 ≈ %.3f)" % (M, digits_last, bitlen_last, log10_last))
    ap("- tête : `" + s_last[:48] + "`")
    ap("- queue : `" + s_last[-48:] + "`")
    if halted:
        ap("- ⚠ **ARRÊT ANTICIPÉ** : b%d = 2^%d — condition de halt atteinte." % (halt_n, halt_v))
    ap("")
    ap("## 4. Valuation 2-adique v")
    ap("")
    ap("- v max observé : **%d** (au pas n=%s) — observations : %d" % (max_v, str(max_v_at), n_vobs))
    ap("")
    ap("| k | obs | attendu (N·2^-(k+1)) |")
    ap("|---:|---:|---:|")
    for k in range(V_BIN_MAX + 1):
        ap("| %d | %d | %.1f |" % (k, v_counts[k], exp_counts[k]))
    ap("| >40 | %d | %.3e |" % (v_gt, exp_gt))
    if chi2 is not None:
        ap("")
        ap("chi² vs géométrique 2^-(k+1) : %.2f (df=%d, regroupement k≥%d) — indicatif"
           % (chi2, chi2_df, chi2_K))
    ap("")
    ap("## 5. Croissance — empirique vs forme fermée")
    ap("")
    ap("Fenêtre empirique : %d transitions de la phase 2." % n_ratios)
    ap("")
    ap("| quantité | empirique | forme fermée (k=0..60) | écart |")
    ap("|---|---:|---:|---:|")
    ap("| E[ln G] | %.9f | %.9f | %+.3e |" % (mean_ln, c1, mean_ln - c1))
    ap("| E[ln² G] | %.9f | %.9f | %+.3e |" % (mean_ln2, c2, mean_ln2 - c2))
    ap("| Var[ln G] | %.9f | %.9f | %+.3e |" % (var_emp, var_c, var_emp - var_c))
    ap("| σ[ln G] | %.9f | %.9f | %+.3e |" % (sd_emp, sigma_c, sd_emp - sigma_c))
    ap("")
    ap("- z-scores (approx. CLT) : z(E[lnG]) = %+.3f ; z(E[ln²G]) = %+.3f" % (z1, z2))
    ap("- Croissance bout-en-bout (b0 → b%d sur %d pas) : %.12f /pas (c = %.12f)" % (M, M, mean_e2e, c1))
    ap("")
    ap("## 6. Projection N = 17 000 000 pas")
    ap("")
    ap("- c = E[ln G] = %.12f ; σ = %.12f" % (c1, sigma_c))
    ap("- chiffres ≈ N·c/ln10 = **%.1f**" % digits_simple)
    ap("- chiffres ≈ (ln b0 + N·c)/ln10 = %.1f" % digits_incl_b0)
    ap("- écart-type attendu ≈ σ·√N/ln10 = ± %.1f chiffres (1σ)" % sd_digits)
    ap("")
    ap("## 7. stdout brut")
    ap("")
    ap("```text")
    md.extend(lines)
    ap("```")
    ap("")
    ap("Fichiers : `%s.json`, `%s.md`, `%s.stdout.txt` dans `%s`." % (stem, stem, stem, REPORTS_DIR))

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(os.path.join(REPORTS_DIR, stem + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(REPORTS_DIR, stem + ".md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")
    with open(os.path.join(REPORTS_DIR, stem + ".stdout.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
