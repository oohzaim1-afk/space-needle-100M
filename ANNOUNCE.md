# Community announcement — draft (EN)

**Space Needle (BB(6)): computation extended to 100,000,000 terms — new max v2 = 25**

We computed the Space Needle sequence (`1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD`, in Doucette's reduced form b -> b + v2(b) + 3/2*(b/2^v2(b) - 1)) out to **100,000,000 terms**:

- **No power of 2 encountered** — no halt;
- **New max v2 = 25**, first occurring at n = 23,145,881 (previous documented max: 24, at >17M terms);
- final term: 94,125,050 bits (28,334,464 decimal digits);
- 400 checkpoints (every 250k terms) + full run log, all hashed;
- cross-checked with two independent implementations (C+GMP full range; Rust num-bigint to 23.25M) — all 93 overlapping checkpoints match exactly, including the v2 records.

Reproducible: `gcc -O2 bb6gmp.c -lgmp`; ~40 h on a single core (the chain is inherently sequential — no parallel or GPU speedup). A ~75-second run validates the first 10 checkpoints.

Code, logs, checkpoints, SHA-256s: **https://github.com/oohzaim1-afk/space-needle-100M**

*(The halting question itself remains open — consistent with its "probviously non-halting" status.)*

— Seiji

---

One-liner variant:

> Space Needle computed to 10^8 terms: no power of 2, new max v2 = 25 (first at n = 23,145,881; previous max 24). 40 h single-threaded, two independent implementations cross-checked. Code/logs/hashes: https://github.com/oohzaim1-afk/space-needle-100M
