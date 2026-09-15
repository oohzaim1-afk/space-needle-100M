# Space Needle — Formal proof of law L3 (sweep decomposition)

**Date:** 2026-09-12
**Machine:** `1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD` (BB(6) "Space Needle")
**Status:** **PROVEN** — demonstration by local analysis of the transition table + induction;
exhaustive machine verification in support (≈1.8×10⁸ steps individually checked, 0 disagreements).

---

## 1. Statement

For b, c ∈ ℕ, let `(b, c)` denote the canonical configuration

    (b, c)  :=  0^∞ ⟨A⟩ 1^b 00 1^c 0^∞

(head on the cell immediately left of the left block, state A).

**Theorem (L3).** For all m ≥ 0, c ≥ 0:

    (2m+3, c)  →  (m, 4+m+c)      in exactly     2(m+3)² + 1     steps,

and the trajectory decomposes into 2m+6 **sweeps** (maximal runs of steps in the same
direction), of lengths

    2m+5, 2m+4, 2m+3, …, 3, 2, 1, then m+4:

the i-th sweep (1 ≤ i ≤ 2m+5) lasts 2m+6−i steps and goes right if i is odd, left if i is
even; the final sweep (i = 2m+6) goes left and lasts m+4 steps.

**Corollary.** Number of sweeps = 2m+6 (independent of c); sum of lengths =
(2m+5)(2m+6)/2 + (m+4) = 2m²+12m+19 = 2(m+3)²+1.

---

## 2. Framework and conventions

Coordinates: the leftmost cell of the initial block `1^(2m+3)` is at position 0; the head
starts at position −1. We write `1^L @ [p, q]` for an interval of L cells at 1 starting at p
(empty interval if p > q); cells outside the listed intervals are 0.

Transition table (read: symbol → write, move, next state):

| state | reads 0 | reads 1 |
|------|-------|-------|
| A | 1RB | 1LA |
| B | 1LC | 0RE |
| C | 1LF | 1LD |
| D | 0RB | 0LA |
| E | 1RC | 1RE |
| F | **HALT** | 0LD |

---

## 3. The boundary configuration family

**C_k (1 ≤ k ≤ m+2)** — head at 2m+5−k, state C, reads 0:

| interval | content |
|------------|---------|
| [−1, k−2] | 1^k |
| [k−1, k−1] | 0 |
| [k, 2m+4−k] | 1^(2m+5−2k) |
| [2m+5−k, 2m+5−k] | 0  ← **head, state C** |
| [2m+6−k, 2m+4+c] | 1^(k+c−1) |

**B_k (1 ≤ k ≤ m+1)** — head at k−1, state A, reads 0:

| interval | content |
|------------|---------|
| [−1, k−2] | 1^k |
| [k−1, k−1] | 0  ← **head, state A** |
| [k, 2m+2−k] | 1^(2m+3−2k) |
| [2m+3−k, 2m+4−k] | 0^2 |
| [2m+5−k, 2m+4+c] | 1^(k+c) |

**D** — head at m+1, state D:

| [−1, m] | [m+1] | [m+2] | [m+3, 2m+4+c] |
|---------|-------|-------|----------------|
| 1^(m+2) | 0 ← **head, state D** | 0 | 1^(m+2+c) |

**B′** — same tape as D; head at m+2, state B.

**FINAL** — head at −2, state A:

| [−1, m−2] | [m−1, m] | [m+1, 2m+4+c] |
|-----------|----------|----------------|
| 1^m | 0^2 | 1^(m+4+c) |

(Verification: FINAL is indeed the canonical configuration (m, 4+m+c), up to translation.)

---

## 4. The lemmas

Each lemma is a **finite local analysis**: the cells being read are identified by the
definition of the current configuration, and the table determines every step. The only
conditions are integer inequalities; no step depends on a particular value of m, k or c.

### Lemma 0 — initialization: init → C_1, in 2m+5 steps

Starting config: [0, 2m+2] = 1^(2m+3), [2m+3, 2m+4] = 0^2, [2m+5, 2m+4+c] = 1^c; head −1, state A.

| # | position | state | reads | writes | move | next state |
|---|----------|------|-----|-------|-------------|--------------|
| 1 | −1 | A | 0 | 1 | R | B |
| 2 | 0 | B | 1 | 0 | R | E |
| 3…2m+4 | j = 1,…,2m+2 | E | 1 | 1 | R | E |
| 2m+5 | 2m+3 | E | 0 | 1 | R | C |

Result: [−1] = 1 ; [0] = 0 ; [1, 2m+3] = 1^(2m+3) ; head at 2m+4 (reads 0) ; [2m+5, 2m+4+c] = 1^c.
This is exactly C_1 (k=1). Number of steps: 2 + 2m+2 + 1 = 2m+5. ∎

### Lemma 1 — C_k → B_k, in 2m+6−2k steps (1 ≤ k ≤ m+1)

Let h = 2m+5−k. In C_k: head at h (0) ; [k, 2m+4−k] = 1^(2m+5−2k) ; cells h−1 = 2m+4−k
and h−2 = 2m+3−k belong to the central block (since k ≤ m+1 ≤ 2m+3−k) ; [2m+6−k, 2m+4+c] = 1^(k+c−1).

| # | position | state | reads | writes | move | next state |
|---|----------|------|-----|-------|-------------|--------------|
| 1 | h | C | 0 | 1 | L | F |
| 2 | h−1 | F | 1 | 0 | L | D |
| 3 | h−2 | D | 1 | 0 | L | A |
| 4… | j = h−3, …, k | A | 1 | 1 | L | A |

Result: [k−1] = 0 (head, state A) ; [k, 2m+2−k] = 1^(2m+3−2k) ; [2m+3−k, 2m+4−k] = 0^2
(cells h−2, h−1 were just reset to 0) ; [2m+5−k, 2m+4+c] = 1^(k+c) (cell h was just written
to 1 and joins the right block). This is B_k.
Number of steps: 3 + (h−3−k+1) = 3 + (2m+3−2k) = 2m+6−2k. ∎

### Lemma 2 — B_k → C_(k+1), in 2m+5−2k steps (1 ≤ k ≤ m+1)

In B_k: head at k−1 (0) ; [k, 2m+2−k] = 1^(2m+3−2k) ; [2m+3−k, 2m+4−k] = 0^2.

| # | position | state | reads | writes | move | next state |
|---|----------|------|-----|-------|-------------|--------------|
| 1 | k−1 | A | 0 | 1 | R | B |
| 2 | k | B | 1 | 0 | R | E |
| 3… | j = k+1, …, 2m+2−k | E | 1 | 1 | R | E |
| — | 2m+3−k | E | 0 | 1 | R | C |

(range 3… is empty when k = m+1 — covered by the same formula.)
Result: [−1, k−1] = 1^(k+1) ; [k] = 0 (next head) ; [k+1, 2m+3−k] = 1^(2m+3−2k) ;
head at 2m+4−k (reads 0, state C) ; [2m+5−k, 2m+4+c] = 1^(k+c) unchanged. This is C_(k+1).
Number of steps: 2 + (2m+2−2k) + 1 = 2m+5−2k. ∎

### Lemma 3 — C_(m+2) → D, in 2 steps

In C_(m+2): h = m+3 ; central block = 1^1 @ [m+2, m+2] ; head at m+3 (0).

| # | position | state | reads | writes | move | next state |
|---|----------|------|-----|-------|-------------|--------------|
| 1 | m+3 | C | 0 | 1 | L | F |
| 2 | m+2 | F | 1 | 0 | L | D |

Result: [−1, m] = 1^(m+2) ; [m+1] = 0 (head, state D) ; [m+2] = 0 ;
[m+3, 2m+4+c] = 1^(m+2+c) (cell m+3, just written to 1, joins the right block). This is D. ∎

### Lemma 4 — D → B′, in 1 step

In D: head at m+1 (0). Step: (m+1, D, 0) → writes 0, moves right, state B. The head arrives at
m+2 (reads 0) ; the tape is unchanged. This is B′. ∎

### Lemma 5 — B′ → FINAL, in m+4 steps

In B′: head at m+2 (0) ; [−1, m] = 1^(m+2) ; [m+1] = [m+2] = 0 ; [m+3, 2m+4+c] = 1^(m+2+c).

| # | position | state | reads | writes | move | next state |
|---|----------|------|-----|-------|-------------|--------------|
| 1 | m+2 | B | 0 | 1 | L | C |
| 2 | m+1 | C | 0 | 1 | L | F |
| 3 | m | F | 1 | 0 | L | D |
| 4 | m−1 | D | 1 | 0 | L | A |
| 5… | j = m−2, …, −1 | A | 1 | 1 | L | A |

Result: [−1, m−2] = 1^m ; [m−1, m] = 0^2 ; [m+1, 2m+4+c] = 1^(m+4+c) ; head at −2 (reads 0,
state A). This is FINAL. Number of steps: 4 + m = m+4. ∎

---

## 5. Assembly (proof of the theorem)

Chain: init —(Lem0)→ C_1 —(Lem1, k=1)→ B_1 —(Lem2, k=1)→ C_2 —(Lem1, k=2)→ B_2 —(Lem2)→ … 
—→ B_(m+1) —(Lem2, k=m+1)→ C_(m+2) —(Lem3)→ D —(Lem4)→ B′ —(Lem5)→ FINAL.

The domains of the lemmas cover everything: Lem1 and Lem2 for k = 1, …, m+1 ; Lem3, Lem4,
Lem5 close the chain. The final configuration is FINAL = (m, 4+m+c), verified above.

Sweep lengths in order: the lemmas give alternately (right, left):

    init→C_1 : 2m+5                          (right)
    C_k→B_k  : 2m+6−2k                       (left)   k = 1…m+1
    B_k→C_(k+1) : 2m+5−2k                    (right)  k = 1…m+1
    C_(m+2)→D : 2                            (left)
    D→B′     : 1                             (right)
    B′→FINAL : m+4                           (left)

the sequence of lengths is 2m+5, 2m+4, 2m+3, …, 3, 2, 1, m+4 (the C→B and B→C transitions
interleave to give exactly the descent from 2m+4 down to 1).

Total: Σ = (2m+5)(2m+6)/2 + (m+4) = 2m²+12m+19 = **2(m+3)²+1**. ∎

---

## 6. Appendix A — machine verification (support, not foundation)

`checkers/l3_proof_check.py` reconstructs the boundary family, **predicts every step**
(position, state, symbol read, symbol written) from the lemmas, and compares it to the
simulator — step by step. Convention: a run = maximal sequence of steps in the same
direction; the boundary belongs to the next run.

Results (report: `reports/l3_proof_check_report.txt`, sha256 41bb8cb5…):

    m = 0..300         : COMPLETE ladders (all k) — ALL PASS
    m = 500, 1000, 2000, 5000 : idem — PASS
    m = 100 000        : first 81 transitions — PASS (16 197 165 steps)
    m = 1 000 000      : first 41 transitions — PASS (81 999 385 steps)
    c ∈ {0,2,3,7} (m ≤ 11) ; c = 10⁶ (m ∈ {5,10,100}) — PASS
    every step individually checked ; total ≈ 1.8×10⁸ steps ; 0 disagreements.

Reproduction:

    python checkers/l3_proof_check.py 300
    python checkers/l3_proof_check.py --full 5000
    python checkers/l3_proof_check.py --big 1000000 20
    python checkers/l3_proof_check.py --cspot

The program also verifies that the total = 2(m+3)²+1 at every complete run.

---

## 7. Appendix B — scope and limits

- The proof does not depend on a computer: every lemma is a finite local analysis (the table
  is deterministic; all read symbols are identified by the block definitions and integer
  inequalities). The machine certifies the statement and the absence of transcription errors.
- L1 is now **proven + machine-certified** (see `L1_PROOF.md` and `checkers/l1_proof_check.py`) ;
  L4 remains **empirically** verified (same techniques applicable; L4 has more phases).
- This result **locks the dynamics** of the machine (the step skeleton that governs the
  trajectories) ; it does not settle the halting question, which remains open (modular
  obstruction / conspiracy).
