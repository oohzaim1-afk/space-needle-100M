# Proposed wiki edit — BusyBeaverWiki "Space Needle" page, Trajectory section

Preferred: **Option B** (append — keeps the page history and existing attribution intact).

Current text (revision 7571, 2026-05-18; retrieved 2026-09-14):

> This sequence has been calculated out to over 17 million terms, with the final value of b calculated before the program was terminated reaching >10^4,800,000. No power of 2 was ever encountered (which would lead to halting), and the most factors of 2 any term had was 24.

## Option A — replace with:

> This sequence has been calculated out to 100,000,000 terms (independent computation by Seiji, September 2026). The final term has 94,125,050 bits (28,334,464 decimal digits). No power of 2 was ever encountered (which would lead to halting); the most factors of 2 any term had was 25 (first occurring at n = 23,145,881 — the previous record was 24). The full final value is published (SHA-256 anchored), and the trajectory was verified by two independent implementations over the full range (400/400 checkpoints). Code, logs and SHA-256 hashes: https://github.com/oohzaim1-afk/space-needle-100M.

## Option B — keep history, append:

> [existing paragraph unchanged]
>
> *Update (September 2026):* an independent computation (Seiji) extended the trajectory to 100,000,000 terms. No power of 2 was encountered, and the most factors of 2 any term had was 25 (first occurring at n = 23,145,881). The full final value is published with a SHA-256 anchor; artifacts and hashes: https://github.com/oohzaim1-afk/space-needle-100M.
