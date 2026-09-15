# Community announcement — draft (EN)

**Space Needle (BB(6)): computation extended to 100,000,000 terms — new max v2 = 25**

We computed the Space Needle sequence (`1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD`, in Doucette's reduced form b -> b + v2(b) + 3/2*(b/2^v2(b) - 1)) out to **100,000,000 terms**:

- **No power of 2 encountered** — no halt (halting tested on every term, positions 1 through 100,000,001; the last term has 94,125,050 bits);
- **New max v2 = 25**, first occurring at n = 23,145,881 (previous documented max: 24, at >17M terms);
- the **full final value is published** (binary + SHA-256), so the last checkpoint can be checked without re-running;
- 400 checkpoints (every 250k terms), full run log, per-checkpoint SHA-256s, all hashed;
- cross-checked over the full range with two independent implementations (C+GMP per-term; block-affine re-derivation) plus a third to 23.25M — every checkpoint matches exactly, including the v2 records.

Reproducible: `gcc -O2 bb6gmp.c -lgmp`; ~40 h single core with the naive per-term build. The full range re-derives in ~22 min with `code/bb6blocks.py` (block-affine method: composes k steps into a single affine map applied with one multiplication; if this optimization is already standard in this community, I'd appreciate a pointer so I can cite it). A ~75-second run validates the first 10 checkpoints.

What this does NOT show: the halting question remains open. Under the standard heuristic (uniform low bits), the chance that a halt occurs beyond term n is ≈ 2^-0.9411*n; at n = 10^8 that is ≈ 2^-94,100,000 — extending from 17M to 100M multiplied the remaining probability by ≈ 2^-78,115,340. This run is a record + statistics, not progress toward a proof.

Code, logs, checkpoints, final value, SHA-256s: **https://github.com/oohzaim1-afk/space-needle-100M**

— Seiji

---

One-liner variant:

> Space Needle computed to 10^8 terms: no power of 2, new max v2 = 25 (first at n = 23,145,881; previous max documented 24); full final value published with SHA-256; full-range cross-check between two implementations; ~40 h naive vs ~22 min block-affine. Code/logs/hashes: https://github.com/oohzaim1-afk/space-needle-100M
