# Exact step-count laws for Space Needle (BB(6)) — proofs + machine certification

This folder contains the exact macro-transition step-count laws of the BB(6) cryptid **Space Needle** (`1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD`), their formal proofs, and self-contained machine-certifying checkers.

## Headline results

- Exact step counts for the four macro transitions + the halt: L0 = 10, **L1 = 2c + 33**, L2 = 12, **L3 = 2(m+3)² + 1**, L4 = (3m+8)(m²+7m+13) + 2(c−1).
- **Closed-form halting time** of the (2^k−3, ·) family: **T(k) = (2·4^k + 3k − 2)/3** — confirmed step-exact up to k = 22 (T(22) = 11 728 124 029 632 ≈ 1.17×10¹³ steps, one by one).
- **Modular obstruction classification**: among valuations a ≤ 120, **96 classes can never produce a power of 2**; 24 are admissible; infinite obstruction families via p = 5, 7, 11, 13.

## Status, honestly

- **L1 and L3 are proven** (finite local-table analysis + induction) and **machine-certified** — ≈47.4M steps individually checked for L1 (+ a complete c = 1..10⁶ sweep ≈ 1.0×10¹² steps), ≈1.8×10⁸ steps for L3.
- **L4 is empirical** (no counterexample over >1.18M GPU configurations; formal proof is open work).
- The **halting question remains open**. The obstruction classification is a rigorous constraint on any halting candidate — not a non-halting proof.

## Contents

- `STEP_LAWS.md` — main document: laws, phase structure, closed-form T(k), obstruction classification, verification at scale.
- `L1_PROOF.md`, `L3_PROOF.md` — the two formal proofs, with machine-certification appendices.
- `checkers/` — dependency-free Python 3 certifiers: `l1_proof_check.py`, `l3_proof_check.py`, `bf_obstruction_check.py`, `verify_crt_classification.py`, plus auxiliary analyses (each with its own usage header). Outputs go to `./reports` next to the script (override: `SPN_REPORTS` env var).
- `checkers/l1sweep/` — the Rust sweep used for the L1 scale certification.

## Provenance

Results obtained 2026-09-11 → 2026-09-14 (independent work; computed by Seiji), disclosed together with the 100,000,000-term computation in this repository. These exact step-count laws were, to our knowledge, not previously published — the public wiki material covers the reduced sequence, its growth constant (0.652355) and the trajectory records, not exact macro step counts. Feedback welcome.
