# Space Needle — Formal proof of law L1 (the resurrection law, b = 0)

**Machine:** `1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD`
**Dates:** proof 2026-09-12; machine certification 2026-09-13
**Status:** **PROVEN** (finite local analysis) + **MACHINE CERTIFICATION: ALL PASS** — `checkers/l1_proof_check.py`, 0 disagreements, ≈47.4M steps checked individually (appendix at the end of this document).

---

## 1. Statement

For every c ≥ 1:

    (0, c) → (c+2, 1)      in exactly      2c + 33      steps,

decomposed into 12 sweeps: 10 constant sweeps of lengths [1,2,4,3,3,2,1,3,1,2]
(sum 22, alternating R/L starting to the right), then a right sweep of length c+6,
then a left sweep of length c+5.

Corollary: 22 + (c+6) + (c+5) = 2c+33; number of sweeps = 12, independent of c.

**Domain:** c ≥ 1 strictly. For c = 0 the trajectory branches at step 8
(C reads 0 at position 3 instead of 1): that corner is delegated to L0 — confirmed by machine.

## 2. Coordinates

Head at 0, state A. Tape: [1,2] = 00 (separator), [3, c+2] = 1^c (right block), rest 0.
(b = 0: the left block is empty.)

## 3. Boundary family — three configurations, not a ladder

- **PREF** — head at −2, state D, reads 0: [−2] = 0 (head) ; [−1, c+2] = 1^(c+4) ; rest 0.
- **TOUR** — head at c+4, state C, reads 0: [−2,−1] = 00 ; [0, c+3] = 1^(c+4) ; [c+4] = 0 (head).
- **FINAL** — head at −1, state A, reads 0: [0, c+1] = 1^(c+2) ; [c+2, c+3] = 00 ; [c+4] = 1.

(Verification: FINAL is indeed the canonical (c+2, 1).)

## 4. Lemma P — INIT → PREF, in 22 steps

The prefix only visits [−2..3]; the right block is only read at [3] (steps 8 and 14), where it
equals 1 iff c ≥ 1. Hence identical for all c ≥ 1. Complete table:

| # | pos | state | reads | writes | move | next |
|---|-----|-------|-------|--------|------|------|
| 1 | 0 | A | 0 | 1 | R | B |
| 2 | 1 | B | 0 | 1 | L | C |
| 3 | 0 | C | 1 | 1 | L | D |
| 4 | −1 | D | 0 | 0 | R | B |
| 5 | 0 | B | 1 | 0 | R | E |
| 6 | 1 | E | 1 | 1 | R | E |
| 7 | 2 | E | 0 | 1 | R | C |
| 8 | 3 | C | 1 | 1 | L | D |
| 9 | 2 | D | 1 | 0 | L | A |
| 10 | 1 | A | 1 | 1 | L | A |
| 11 | 0 | A | 0 | 1 | R | B |
| 12 | 1 | B | 1 | 0 | R | E |
| 13 | 2 | E | 0 | 1 | R | C |
| 14 | 3 | C | 1 | 1 | L | D |
| 15 | 2 | D | 1 | 0 | L | A |
| 16 | 1 | A | 0 | 1 | R | B |
| 17 | 2 | B | 0 | 1 | L | C |
| 18 | 1 | C | 1 | 1 | L | D |
| 19 | 0 | D | 1 | 0 | L | A |
| 20 | −1 | A | 0 | 1 | R | B |
| 21 | 0 | B | 0 | 1 | L | C |
| 22 | −1 | C | 1 | 1 | L | D |

Justification of the reads (everything is determined): [3]=1 ⟸ c ≥ 1 (steps 8, 14); [2]=1 at
steps 9, 15 ⟸ steps 7, 13; [0]=0 at step 11 ⟸ step 5; [1]=0 at step 16 ⟸ step 12; [−1]=0 at
step 20 (never written before). Result: [−1..c+2] = 1^(c+4), head −2 in D.
Sweeps: [1,2,4,3,3,2,1,3,1,2] ✓. ∎

## 5. Lemma M1 — PREF → TOUR, in c+6 steps (a single right sweep)

| # | pos | state | reads | writes | move | next |
|---|-----|-------|-------|--------|------|------|
| 23 | −2 | D | 0 | 0 | R | B |
| 24 | −1 | B | 1 | 0 | R | E |
| 25–27 | j = 0,1,2 | E | 1 | 1 | R | E |
| 28…27+c | j = 3,…,c+2 | E | 1 | 1 | R | E |
| 28+c | c+3 | E | 0 | 1 | R | C |

Count: 2 + 3 + c + 1 = c+6 ✓. The E walk only reads 1s of PREF; [c+3] was never written.
Result = TOUR. ∎

## 6. Lemma M2 — TOUR → FINAL, in c+5 steps (a single left sweep)

| # | pos | state | reads | writes | move | next |
|---|-----|-------|-------|--------|------|------|
| 29+c | c+4 | C | 0 | 1 | L | F |
| 30+c | c+3 | F | 1 | 0 | L | D |
| 31+c | c+2 | D | 1 | 0 | L | A |
| 32+c…2c+33 | j = c+1,…,0 | A | 1 | 1 | L | A |

Count: 3 + (c+2) = c+5 ✓. The unique occurrence of F in the entire L1 trajectory: it reads 1,
so there is no spurious halt. Result = FINAL = (c+2,1). ∎

## 7. Assembly

INIT —(P, 22)→ PREF —(M1, c+6)→ TOUR —(M2, c+5)→ FINAL. Total 2c+33 ∎.
Sweeps: 12, lengths [1,2,4,3,3,2,1,3,1,2, c+6, c+5] ∎.

## 8. Trampoline corollary (for the dynamics notes)

Composed with L3 (m = 0): (3, c) →(19 steps)→ (0, 4+c) →(2c+41 steps)→ (c+6, 1),
i.e. **(3,c) → (c+6,1) in 2c+60 steps, 18 sweeps**.

b = 3 is not a descent: it is a trampoline that converts all the fuel c into a fresh block.
L1 is the resurrection law: b = 0 is not absorbing; the right reservoir is reconverted into a
left block. The fuel economy is now complete: L3 stores (b→c), L4 and L1 burn (c→b).
This is where the conspiracy lives.

## 9. Testable predictions (checkers/l1_proof_check.py)

(i) steps 1–22 identical for every c ≥ 1 (table above); (ii) end of step 22: head −2, D,
[−1..c+2] all 1s; (iii) end of step 28+c: head c+4, C; (iv) total 2c+33; (v) final tape
= (c+2,1); (vi) 12 sweeps, lengths as above; (vii) exactly one visit to F
(step 30+c), reading 1.

## 10. Scope — and a control anecdote

Same philosophy as Appendix A of the L3 proof: finite local analysis, deterministic table,
integer inequalities — the machine certifies, it does not prove. Anecdote from the first
manual pass: applying C-reads-1 → 1LF instead of 1LD "discovered" a halt at step 23 for every
c — wrong, corrected; this is exactly why step-by-step certification exists.

---

## Appendix — Machine certification (2026-09-13)

`checkers/l1_proof_check.py` reconstructs the steps predicted by the three lemmas, applies the
**real transition table** at every step and compares (position, state, read, write, move, next
state), plus the PREF/TOUR/FINAL boundaries, the total count, the sweep decomposition and the
unique F visit.

Results (report: `reports/l1_proof_check_report.txt`, sha256 `7b863d56…`):

    c = 1..5000        : ALL PASS (25 170 000 steps)
    c = 10⁴            : PASS
    c = 10⁵            : PASS
    c = 10⁶            : PASS
    c = 10⁷            : PASS (20 000 033 steps)
    c = 0              : branch confirmed at step 8 (C reads 0 at 3 instead of 1)
    trampoline (3,c) → (c+6,1) : PASS for c ∈ {1,2,3,5,10}

**Total: 47 390 132 steps checked individually — 0 disagreements.**

**Scale extension (2026-09-13, Rust sweep `checkers/l1sweep`)** — c = 1..10⁶ **COMPLETE**:
1 000 034 000 000 steps + spots 10⁷/10⁸/10⁹ — **ALL PASS, 0 disagreements** (8 threads, 21.8 min,
766M steps/s; report: `reports/l1_sweep_report.txt`). Final coverage: micro-steps c=1..5000 +
full verification (boundaries/sweeps/total/F) c=1..10⁶ + spots ≤10⁹.

Reproduction:

    python checkers/l1_proof_check.py            # c = 1..5000 + spots 1e4..1e7
    python checkers/l1_proof_check.py --big 7    # single c = 10⁷

*Proof produced 2026-09-12 (delivered through an inter-harness relay); manually reviewed and
machine-certified by the main agent 2026-09-13.*
