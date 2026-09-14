# S1 — Space Needle : ré-exécution indépendante de la récurrence + statistiques

- **Généré (UTC)** : 2026-09-11T19:56:01Z
- **Script** : `C:\Users\<local>\bb6\py\ref_traj.py` (stdlib : json, math, os, sys, time)
- **Python** : 3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]
- **Exécutable** : `C:\python312\python.exe` — plateforme : win32
- **N pas demandés** : 1000000 — mises à jour appliquées M = 1000000 — arrêt anticipé (halt) : non
- **Calibration** : N=100000 exécuté en 0.812 s (boucle) → décision : N=1000000 pour le run final

## Récurrence testée

```
b0 = 6 ; v = v2(bn) ; m = bn >> v ;  b(n+1) = b(n) + v + (3*(m-1))//2
HALT si bn puissance de 2 <=> (bn & (bn-1)) == 0 <=> m == 1
```

## 1. Contrôle du préfixe publié (10 premiers termes)

| n | recalculé | publié | match |
|---:|---:|---:|:---:|
| 0 | 6 | 6 | oui |
| 1 | 10 | 10 | oui |
| 2 | 17 | 17 | oui |
| 3 | 41 | 41 | oui |
| 4 | 101 | 101 | oui |
| 5 | 251 | 251 | oui |
| 6 | 626 | 626 | oui |
| 7 | 1095 | 1095 | oui |
| 8 | 2736 | 2736 | oui |
| 9 | 2995 | 2995 | oui |

**Assert** : OK — les 10 termes correspondent aux valeurs publiées.

## 2. Exécution

- Boucle phase 2 : **68.323 s** pour 999991 transitions mesurées (b9 → b1000000)
- Moyenne : **68.32 µs/pas** (phase 2)
- Temps total de calcul du script : 68.413 s
- Calibration utilisée pour le choix de N : N=100000 → 0.8 s mesuré ; projection N=1e6 ≈ 81 s (loi ~N²)

## 3. Dernier terme

- b1000000 : **283396 chiffres décimaux** (bit_length = 941419 ; log10 ≈ 283395.209)
- tête : `161819134276796578918746996997253493964697365988`
- queue : `218205325854598624937085538129508762713114018629`

## 4. Valuation 2-adique v

- v max observé : **17** (au pas n=158831) — observations : 999991

| k | obs | attendu (N·2^-(k+1)) |
|---:|---:|---:|
| 0 | 499981 | 499995.5 |
| 1 | 250479 | 249997.8 |
| 2 | 124873 | 124998.9 |
| 3 | 62473 | 62499.4 |
| 4 | 30954 | 31249.7 |
| 5 | 15652 | 15624.9 |
| 6 | 7743 | 7812.4 |
| 7 | 3942 | 3906.2 |
| 8 | 1951 | 1953.1 |
| 9 | 959 | 976.6 |
| 10 | 503 | 488.3 |
| 11 | 234 | 244.1 |
| 12 | 120 | 122.1 |
| 13 | 66 | 61.0 |
| 14 | 30 | 30.5 |
| 15 | 18 | 15.3 |
| 16 | 5 | 7.6 |
| 17 | 8 | 3.8 |
| 18 | 0 | 1.9 |
| 19 | 0 | 1.0 |
| 20 | 0 | 0.5 |
| 21 | 0 | 0.2 |
| 22 | 0 | 0.1 |
| 23 | 0 | 0.1 |
| 24 | 0 | 0.0 |
| 25 | 0 | 0.0 |
| 26 | 0 | 0.0 |
| 27 | 0 | 0.0 |
| 28 | 0 | 0.0 |
| 29 | 0 | 0.0 |
| 30 | 0 | 0.0 |
| 31 | 0 | 0.0 |
| 32 | 0 | 0.0 |
| 33 | 0 | 0.0 |
| 34 | 0 | 0.0 |
| 35 | 0 | 0.0 |
| 36 | 0 | 0.0 |
| 37 | 0 | 0.0 |
| 38 | 0 | 0.0 |
| 39 | 0 | 0.0 |
| 40 | 0 | 0.0 |
| >40 | 0 | 4.547e-07 |

chi² vs géométrique 2^-(k+1) : 7.90 (df=17, regroupement k≥17) — indicatif

## 5. Croissance — empirique vs forme fermée

Fenêtre empirique : 999991 transitions de la phase 2.

| quantité | empirique | forme fermée (k=0..60) | écart |
|---|---:|---:|---:|
| E[ln G] | 0.652539452 | 0.652354548 | +1.849e-04 |
| E[ln² G] | 0.513020369 | 0.512897726 | +1.226e-04 |
| Var[ln G] | 0.087212633 | 0.087331270 | -1.186e-04 |
| σ[ln G] | 0.295317851 | 0.295518646 | -2.008e-04 |

- z-scores (approx. CLT) : z(E[lnG]) = +0.626 ; z(E[ln²G]) = +0.361
- Croissance bout-en-bout (b0 → b1000000 sur 1000000 pas) : 0.652539791979 /pas (c = 0.652354547813)

## 6. Projection N = 17 000 000 pas

- c = E[ln G] = 0.652354547813 ; σ = 0.295518646268
- chiffres ≈ N·c/ln10 = **4816337.7**
- chiffres ≈ (ln b0 + N·c)/ln10 = 4816338.4
- écart-type attendu ≈ σ·√N/ln10 = ± 529.2 chiffres (1σ)

## 7. stdout brut

```text
### ref_traj.py | Space Needle recurrence | independent run
utc                 : 2026-09-11T19:56:01Z
python              : 3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]
sys.platform        : win32
executable          : C:\python312\python.exe
N steps requested   : 1000000
probe math.log(2**4096) = 2839.130851574
self-tests v_and_odd : OK

prefix recompute    : 6, 10, 17, 41, 101, 251, 626, 1095, 2736, 2995
prefix published    : 6, 10, 17, 41, 101, 251, 626, 1095, 2736, 2995
prefix assert       : OK

run finished        : M = 1000000 mises a jour appliquees (b_0 -> b_1000000)
halted early        : no
phase2 wall time    : 68.323 s
n_ratios measured   : 999991
last term           : 283396 decimal digits | bit_length 941419 | log10 ~ 283395.209030
last term head      : 161819134276796578918746996997253493964697365988
last term tail      : 218205325854598624937085538129508762713114018629

empirical means (phase2 window, 999991 transitions):
  mean ln(G)        = 0.652539451894
  mean ln(G)^2      = 0.513020369442
  var  ln(G)        = 0.087212633164 (sd 0.295317851076)
closed form (k=0..60):
  E[ln G]           = 0.652354547813
  E[ln G^2]         = 0.512897726345
  var               = 0.087331270292 (sigma 0.295518646268)
  z(mean lnG)       = 0.626
  z(mean lnG^2)     = 0.361
end-to-end mean ln growth (b0->b_1000000 over 1000000 steps) = 0.652539791979

prediction N = 17000000 :
  digits ~ N*c/ln10           = 4816337.7
  digits ~ (ln b0 + N*c)/ln10 = 4816338.4
  sd digits (1 sigma)         = 529.2
v max = 17 at n=158831 ; v obs = 999991
chi2(v hist vs 2^-(k+1)) = 7.90 (df=17, pooled from k=17)
total compute time  : 68.413 s
```

Fichiers : `S1_traj_report.json`, `S1_traj_report.md`, `S1_traj_report.stdout.txt` dans `C:\Users\<local>\bb6\reports`.
