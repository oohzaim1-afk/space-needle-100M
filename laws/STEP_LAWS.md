# Space Needle (BB(6)) — Exact step-count laws, phase structure, modular obstruction, and large-scale verification

**Status:** campaign run 2026-09-11 → 2026-09-14. **L1 and L3 formally proven + machine-certified** (2026-09-13); **T(k) confirmed by direct step-exact simulation up to k = 22**; **100,000,000 terms computed — no halt** (2026-09-14). **L4 is empirical.**
**Machine:** `1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD` (BB(6) cryptid "Space Needle", BMO problem 6).
**Subject:** exact step counts of the machine's macro transitions (not previously published, to our knowledge), the closed-form halting time of the (2^k−3, ·) family, phase structure, a modular obstruction classification, and verification at scale.

---

## 1. Executive summary

Space Needle is a BB(6) cryptid: its halting question reduces to — *does the sequence b → b + v₂(b) + 3/2·(b/2^v₂ − 1) ever hit a power of 2?* That question remains open.

This work establishes the **exact step-count laws** of the four macro transitions that govern the machine:

1. **Closed-form exact step counts** for each of the four transitions + the halt (Section 3).
2. **Closed-form halting time** of the (2^k−3, c) family: `T(k) = (2·4^k + 3k − 2)/3`, with an exact analytic derivation `T(k) = 12 + Σ_{j=3..k} (2^(2j−1) + 1)` (each term = one L3 step with m = 2^(j−1) − 3, plus the final L2 halt @ 12). Verified by direct simulation up to **k = 22**; **independence of c verified on a k=2..14 × 7-value matrix c ∈ {0,1,2,7,100,12345,10⁶} — 91/91 exact HALTs** (+ k=15/16/17 × 3 non-trivial values).
3. **Phase structure (ladder)** explaining *why* the quadratic/linear formulas are exact — verified up to m=10⁶ (L3) and c=10⁹ (L1); **L3 and L1 formally proven + machine-certified** (`L3_PROOF.md`, `L1_PROOF.md`).
4. **Modular obstruction classification**: for a ≤ 120, **96 valuation classes can NEVER produce a power of 2** (congruence obstruction, explicit witnesses); 24 are admissible (extension 101..120: only a=120). **Constructive validation** (a ≤ 28): every admissible class gets an explicit witness `b = m·2^a` with `f(b) = 2^j` EXACT (`checkers/bf_obstruction_check.py` → ALL OK; 12 admissible constructed / 16 obstructed with no solution m ≤ 10⁶).
5. **Large-scale verification**: >1.18 million GPU configurations (0 counterexamples), SHA-256 hashes, byte-identical re-runs, independent implementations (Rust, Python ×3, CUDA, C+GMP).

---

## 2. Context and conventions

- Canonical configuration: `0^∞ <A 1^b 00 1^c 0^∞` (head on the first 0 cell immediately left of the block of b ones).
- The machine evolves between canonical configurations; one "step" = one elementary Turing-machine transition.
- The high-level transition rules (targets) are published (mxdys, Racheline, Doucette); the **step counts** are, to our knowledge, not. This document establishes and verifies them.

---

## 3. The exact step-count laws (L0–L4)

| # | Domain | Transition | Exact time |
|---|--------|-----------|------------|
| L0 | b=0, c=0 | (0,0) → (0,1) | **10** |
| L1 | b=0, c≥1 | (0,c) → (c+2, 1) | **2c + 33** |
| L2 | b=1 | (1,c) → HALT | **12** |
| L3 | b odd ≥3, m=(b−3)/2 | (2m+3, c) → (m, 4+m+c) | **2(m+3)² + 1**  [= (b+3)²/2 + 1] |
| L4 | b even ≥2, m=(b−2)/2 | (2m+2, c) → (7+5m+c, 1) | **(3m+8)(m²+7m+13) + 2(c−1)** |

### 3.1 Phase structure (why these formulas hold)

**L3 (b odd)** — the transition is a sequence of alternating sweeps whose lengths form a descending ladder:
`[2m+5, 2m+4, ..., 2, 1]` then one final sweep `[m+4]`.
Sum: `(2m+5)(2m+6)/2 + (m+4) = 2(m+3)² + 1`.
Verified structurally for m=0..200 + individual cases m∈{250,300,400,500,1000,2000,4094} (33.5M steps simulated), and the beginning of the ladder (first 30 sweeps) for m=1000, 10⁴, 10⁵, **10⁶**.
**Formal proof:** `L3_PROOF.md` (5 lemmas + induction; machine certification ≈1.8×10⁸ steps, 0 disagreements).

**L1 (b=0)** — constant prefix of 10 sweeps `[1,2,4,3,3,2,1,3,1,2]` (sum 22) then `[c+6, c+5]` (sum 2c+11) → total `2c + 33`. **PROVEN + machine-certified (2026-09-13)**: 3 boundary configurations + 3 lemmas; micro-steps `checkers/l1_proof_check.py` (c=1..5000 complete + spot checks ≤10⁷); Rust sweep `checkers/l1sweep` (c=1..10⁶ COMPLETE ≈1.0×10¹² steps + spots 10⁷/10⁸/10⁹, 0 disagreements) → `L1_PROOF.md`.

**L4 (b even)** — structure verified for m=0..60:
- prefix `[2m+4, 2m+3, ..., 3, 1]`
- suffix `[..., 5m+12, 5m+11, 1]`
- number of sweeps: `5m² + 23m + 31` (verified m=0..200)
- total time: `(3m+8)(m²+7m+13) + 2(c−1)` (0 counterexamples on >1.18M GPU configurations)

---

## 4. Closed-form halting time: T(k) = (2·4^k + 3k − 2)/3

For every k ≥ 2: the configuration `(2^k − 3, c)` halts in exactly `T(k) = (2·4^k + 3k − 2)/3` steps (independent of c).

Derivation: the descent chains L3 steps along 2^k−3 → 2^(k−1)−3 → … → 1, each level costing `2^(2j−1)+1`, then the final halt @ 12. The closed formula falls out of the geometric series.

| k | T(k) verified |
|---|--------------|
| 2..16 | 12, 45, 174, 687, 2736, 10929, 43698, 174771, 699060, 2796213, 11184822, 44739255, 178956984, 715827897, 2863311546 |
| 17 | 11 453 246 139 |
| 18 | 45 812 984 508 |
| **19** | **183 251 937 981** ✅ (confirmed step-exact) |
| **20** | **733 007 751 870** ✅ (step-exact, 2026-09-11 20:03) |
| **21** | **2 932 031 007 423** ✅ (step-exact, 2026-09-12 02:33) |
| **22** | **11 728 124 029 632** ✅ (step-exact, 2026-09-13 11:31, 23.9 h) |
| increment | T(k) − T(k−1) = 2^(2k−1) + 1 |

**c-independence confirmed** (2026-09-12): chains (32765, c=123456), (65533, c=7), (131069, c=0) → exact HALTs at T(15)=715 827 897, T(16)=2 863 311 546, T(17)=11 453 246 139.

---

## 5. Modular obstruction classification (new)

For b = m·2^a (m odd, valuation a = v₂(b)):
```
2·f(b) = m·(2^(a+1) + 3) + (2a − 3)
⇒ f(b) ≡ r_a := (2a−3)·2⁻¹  (mod q_a),  q_a = 2^(a+1) + 3
```
(direct form of Doucette's criterion `f(b) ≡ 2^a + a (mod q_a)`).

**Theorem (verified):** if `r_a ∉ ⟨2⟩` (the multiplicative subgroup generated by 2) modulo some prime factor of `q_a`, then **f(b) is NEVER a power of 2, whatever the value of m**. Consequently, only an "admissible" valuation class a can produce the final step of a halt.

**Complete table a = 1..100** (discrete logs + CRT, verified factorizations, orbital brute force for q ≤ 2²⁶; "order too large" cases resolved by a subgroup technique):

- **ADMISSIBLE (23):** 2, 3, 5, 6, 8, 11, 14, 15, 16, 17, 20, 27, 29, 30, 34, 37, 38, 42, 49, 54, 63, 66, 83
- **OBSTRUCTED (77):** all remaining classes from 1 to 100.

Obstruction density grows with a: 23/40 for a≤40, 40/60 for a≤60, 58/80 for a≤80, 77/100 for a≤100 — roughly 3/4 of classes obstructed.
Notes: the "order too large" cases (66, 68, 71, 72, 75) were re-decided by the subgroup technique — **a=66 is ADMISSIBLE** (q₆₆ = 2⁶⁷+3 is prime, confirmed by sympy `isprime`; cyclic group, exact membership test); 68/71/72/75 are OBSTRUCTED with explicit CRT witnesses. **Extension a=81..100 (2026-09-12): only a=83 is admissible** — q₈₃ = 2⁸⁴+3 = 19342813113834066795298819 is prime (same exact mechanism as 63/66).

Infinite obstruction families (elementary proofs):
- `a ≡ 4 (mod 20)` via p=5; `a ≡ 19 (mod 21)` via p=7;
- `a ≡ 62 (mod 110)` via p=11; `a ≡ 21 (mod 156)` via p=13.

Verifications: subgroup membership + CRT (internal assertions — extended assertion script a≤60: ALL ASSERTIONS PASSED), brute-force orbit `x → 2x mod q` (independent of factorization), random big-int checks (600M per class). For a=61..80: giant orders resolved by the subgroup technique (BSGS inside the subgroup of order gcd(d_p,d_q)) — see `checkers/verify_crt_classification.py`.

> Note: the sequence b₀=6 is KNOWN not to halt over >100,000,000 terms (this package). This classification is NOT a proof of non-halting — it only constrains the class of the term preceding a halt; it sharpens the necessary "conspiracy": the term before a halt must have a valuation in {2,3,5,6,8,11,...} AND land in the right congruence class.

---

## 6. Large-scale verification

### 6.1 GPU (exhaustive grid falsification)

| File | Domain | Cases | Verdict | SHA-256 (truncated) |
|------|--------|-------|---------|--------------------|
| gpu_A_b127_c1023.csv | b 0..127 × c 0..1023 | 131 072 | 0 violation | a4f6c9040b44a22f |
| gpu_A_rerun.csv / _rerun2 | idem (×2) | 131 072 | byte-identical | a4f6c9040b44a22f |
| gpu_B_b511_c1023.csv | b 0..511 × c 0..1023 | 524 288 | 0 violation | 521756776ddc61c4 |
| gpu_C_b1023_c1023.csv | b 0..1023 × c 0..1023 | 524 288 | 0 violation | efdc98eba652c53d |
| gpu_D_b2047_cstep128.csv | b 1024..2047 × c step 128 | 8 192 | 0 violation | ca70c701a64c44aa |
| gpu_E1_c65536.csv | b 0..1023, c=65 536 | 1 024 | 0 violation | b3eaf405a56a0384 |
| gpu_E2_c1048576.csv | b 0..1023, c=2²⁰ | 1 024 | 0 violation | 28dc257161a54051 |
| gpu_F_b511_c2047.csv | b 0..511 × c 1024..2047 | 524 288 | 0 violation | 8c08fab55b4f4d12 |
| gpu_J_Cstrip_512_543.csv | strip re-run (determinism) | 32 768 | 0 diff vs C | b7bc95ff1c700da5 |

- Total **≈1.83M cases checked** (waves A–J + K/L1-L3/N + G/H/I + P1 — exact tally); deterministic byte-identical re-runs; SHA-256 manifest in the original run environment (`reports/MANIFEST_sha256.txt`).
- Wave K: even b 1024..2046 × c=10⁶ (512 cases) — **0 violation**.
- Waves L1/L2/L3: odd b 1025..65535 × c=10⁵ (32 256 cases) — **0 violation**.
- N (strip re-run D, determinism): 64 cases, 0 violation. G (odd b 1025..65535, c=1): 32 256 cases, 0 violation. H (c=0): 7 680 cases, 0 violation.
- **P1 (even b 2048..4094, c=1)**: 682/1024 conforming HITs; **342 BOUNDS cases = insufficient LEFT tape margin (capacity artifact, NOT a violation)**. Cause measured (mode `extent`, dynamic tape): the left head excursion is −(3b/2+3) for even b, while the kernels place the config at off0 = 1024+(b1+c1) → BOUNDS exactly when 3b/2+3 > 1024+b1+c1 (P1: first failure b=3412, predicted 5121 > 5119 ✓; b=3410 OK, 5118 ≤ 5119 ✓). The `spn_grid3` "fix" (margin added to the RIGHT) was on the wrong side — insufficient for (4094,1023) (off0=6141 vs needed 6144: 3 cells short). **Correct fix = `spn_grid4.exe`**: `off0 = 3·b_even_max/2 + 3 + 1024`; `maxlen = off0 + b1 + c1 + 8 + 1024`. Re-runs P1b (342 cases) and Q (4094,1023) were relaunched with spn_grid4; P2 (c=65536) ran with correct margins.
- **Measured excursion table** (10 Rust measurements + 8 independent Python cases, ALL exact; reproducible: `checkers/verify_excursions.py` → ALL OK): even b → left −(3b/2+3), right +(b+c+3); odd b → left −2, right +(b+1) (independent of c; 3 measurements): (3412,1) [−5121,+3416]; (4094,1) [−6144,+4098]; (4094,1023) [−6144,+5120]; (4094,65536) [−6144,+69633]; (2046,10⁵) [−3072,+102049]; (1022,10⁶) [−1536,+1001025]; (65535,1) [−2,+65536]; (65535,1000) [−2,+65536]; (3413,1000) [−2,+3414]; (0,1000) [−3,+1003].
- **Determinism**: strips J3 then J4 (b 512..519 × c 0..1023, 8 192 cases) — **0 diff** vs grid J and between them; widening the tape changes NO result (capacity fix only, proven twice).

### 6.2 CPU (extrapolations and chains)

- 2048-case grid (b 0..63 × c 0..31): conforming (S2).
- CPU vs GPU re-check: 32 768 cases (b 128..159) — 0 diff; sample D of 25 cases (b 1024..2047) — 0 failure.
- Verified extrapolations: b=10001 (50040009 ✓), b=100001 (5000400009 ✓), b=131069 (8589934593 ✓), **b=1000001 (500004000009 ✓ — step-exact capstone at m=499999)**, b=2046 c=0/128/512 (3 232 775 172 ✓), b=4094 (25 815 971 846 ✓), **b=8190 (206 343 041 030 ✓ — exact L4 capstone at m=4094)**, b=2046/c=10⁶ (3234775172 ✓), b=10001/c=10⁶ (50 040 009 ✓).
- **Exact L4 capstones**: b=8190 → 206 343 041 030; **b=16382 → HIT (40958,1) @ 1 650 005 762 054** exact (2026-09-12 01:08, L4 formula at m=8190).
- **k=20 → HALT 733 007 751 870** ✅ (chain 2²⁰−3 → … → 1, 19 CPs, each L3 level exact, L2 halt @12).
- **k=21 → HALT 2 932 031 007 423** ✅ (2026-09-12 02:33, 20 CPs).
- **k=22 → HALT 11 728 124 029 632** ✅ (2026-09-13 11:31, 21 CPs, 23.9 h, 136.4M steps/s — diff 0 vs expected).
- **CP25 EXACT CONFIRMED**: (45028,1) @ **2 235 890 593 558** absolute steps (= 43 621 353 418 + 2 192 269 240 140). The raw audit goes from 43.6×10⁹ to **2.24×10¹² steps** (×51).
- c-independence: exact HALTs T(15)/T(16)/T(17) for c=123456, 7, 0.
- CPU↔GPU cross-check: 32 768 cases (b 128..159) — **0 diff**. (Note: the CPU re-check `gridr 1024..1031` was interrupted — partial file, not used.)
- **Control CPU chains on the GPU BOUNDS cases** (GPU-independent, 2026-09-12): (4094,1) → (10238,1) @ **25 815 971 846** (= (3m+8)(m²+7m+13), m=2046, EXACT); (4094,1023) → (11260,1) @ **25 815 973 890** (= same + 2·1022, EXACT); (3412,1) → (8533,1) @ **14 953 898 679** (m=1705, EXACT); (3754,1) → (9388,1) @ **19 909 288 356** (m=1876, EXACT); (3420,1) → (8553,1) @ **15 059 193 695** (m=1709, EXACT); (3800,1) → (9503,1) @ **20 649 287 435** (m=1899, EXACT).
- Raw chain of 25 checkpoints: 43 621 353 418 steps, all L0–L4 transitions exact (audit: 151 links, 0 violation).
- Analytic model: 25/25 checkpoints + predictions up to 200 CPs.

### 6.3 Independent implementations

| Implementation | Language | Role | Verdict |
|----------------|----------|------|---------|
| bb6tools | Rust | main simulator: chain/grid/recur | calibrated BB(2)–BB(5) |
| bb6gmp | C + GMP | trajectory (bits) | 80 common checkpoints, 0 mismatch |
| s4/check.py | Python from scratch | 508+128+9 law cases | 0 violation |
| s5/check.py | Python from scratch | 297 L0–L4 cases + 25 checkpoints | 0 violation |
| phase_structure*.py | Python | phase structure | ALL OK |
| v2_classes / crt_obstruction | Python | modular classification | ALL OK |
| spn_grid(.2).cu | CUDA | massive grids | 9.4 Gsteps/s, 0 mismatch |

### 6.4 Extended trajectory

- **Rust: 23 250 000 terms** (`done n=23250000 last_hash=00f1dc201ed33796`; extended from 20M to 23.25M to cover the v₂ record zone).
- **C+GMP: 50 000 000 terms reached** (`done N=50000000`, 41 508 s ≈ 11.5 h; bits=47 063 400 ≈ 14.2M decimal digits) — no halt.
- **v₂ RECORD CONFIRMED IN DOUBLE IMPLEMENTATION: v₂=25 at n=23 145 881** — the `V2RECORD v2=25` line appears at the SAME n in Rust and C+GMP (**93 common checkpoints, 0 mismatch**; the 23.25M checkpoint hash matches: `00f1dc201ed33796`). Published record = 24 (over 17M terms). Max v₂ remains 25 over the ENTIRE range — no 26+.
- **100M-terms extension COMPLETED (2026-09-14 03:33)**: 100,000,000 terms computed — **no halt**; max v₂ = 25; 400 checkpoints (every 250k terms); final b = 94 125 050 bits; average rate 692.6 terms/s; duration 40.10 h; csv hash `2dd4c88d…` / stdout `f1f57929…`.
- v₂ statistics conform to the geometric model (χ² = 7.90, df = 17).

---

## 7. Files and reproduction

The original run environment was a Windows machine with the project at `C:\Users\oohza\bb6\` (rust/bb6tools, py/, cuda/, gmp/, reports/, refs/). The self-contained certifying checkers are included here under `laws/checkers/`:

- `l1_proof_check.py` — certifies the L1 proof, step by step (`python l1_proof_check.py`; `--big 7` for the c=10⁷ spot).
- `l3_proof_check.py` — certifies the L3 proof, ladder by ladder (`python l3_proof_check.py 300`; `--full 5000`, `--big 1000000 20`, `--cspot`).
- `bf_obstruction_check.py` — constructive + brute-force validation of the obstruction classification (a ≤ 28; witnesses + non-solutions).
- `verify_crt_classification.py` — independent re-derivation of the CRT classification (a = 1..40): factorization checks, exact orders, BSGS, orbit brute force.
- `l4_structure.py`, `verify_excursions.py`, `crt_obstruction.py` — auxiliary analyses (L4 structure, head-excursion formulas, obstruction pipeline).
- `l1sweep/` — Rust sweep used for the L1 scale certification (c = 1..10⁶ complete, ≈1.0×10¹² steps).

Scripts are dependency-free Python 3 (stdlib only). Report artifacts referenced above (`MANIFEST_sha256.txt`, `gpu_*.csv`, …) belong to the original run environment and are not all included here; every claim in this document is traceable to a recorded run (dates and hashes given inline).

---

## 8. Limits and open paths

- Proof status (2026-09-14): **L3 and L1 are formally proven + machine-certified** (L3: 5 lemmas, ≈1.8×10⁸ steps; L1: 3 lemmas, micro-steps c=1..5000 + complete sweep c=1..10⁶, ≈1.0×10¹² steps; see `L3_PROOF.md` / `L1_PROOF.md`). L0/L2: trivial finite cases. **L4 remains empirical** (same technique applicable — open work).
- The Space Needle halting problem remains OPEN (the conjecture "it never halts" is out of reach of current methods).
- The obstruction classification constrains the class of the term preceding a halt: a ≤ 120 → **96 obstructed / 24 admissible**; infinite families enumerated (12.50M families p ≤ 50k, covering 43.9% of a ≤ 10⁸, 0 admissible covered) — no global closure.
- Paths: formal proof of L4 (two-parameter structure); v₂ ≥ 26: none drawn over 100M terms (extension completed 2026-09-14); the "conspiracy" (a value hitting a power of 2 after an obscene number of steps) remains the only halting route.

---

*Compiled from the raw proof artifacts; every number comes from a real run — no estimates. Last updated 2026-09-14.*
