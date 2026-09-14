# Space Needle (BB(6)) — computational extension to 100,000,000 terms

**Computed by:** Seiji — independent computation, September 2026.


**Machine:** `1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD` — "Space Needle", a BB(6) cryptid (BMO problem 6). Discovered by mxdys (Jan 2025); low-level rules by mxdys; higher-level rules by Racheline and Katelyn Doucette.

**Result (September 2026):** the associated sequence (reduced form below) has been computed to **100,000,000 terms**. **No power of 2 was encountered** — the halting condition is never met. The maximum factor-of-2 record is **v2 = 25**, first occurring at n = 23,145,881 (1-based term index; see "Indexing conventions"). The previous documented state was >17,000,000 terms with max v2 = 24 (BusyBeaverWiki page, retrieved 2026-09-14; K. Doucette, "All About Space Needle").

**Final term:** 94,125,050 bits = **28,334,464 decimal digits** (exact; see note below), FNV-1a 64 hash of limbs `fd4332e892cc1fab`.

## The sequence

Reduced form (Doucette's higher-level rule; the form used by all code here):

    b0 = 6;   b_{n+1} = b_n + v2(b_n) + (3/2) * (b_n / 2^v2(b_n) - 1);   HALT if b_n is a power of 2

Prefix: 6, 10, 17, 41, 101, 251, 626, 1095, 2736, 2995, ...

## Contents

- `code/bb6gmp.c` — C + GMP implementation (ran the full 100,000,000 terms)
- `code/bb6gmp-linux-x86_64` — the exact binary used for the run (16,840 bytes)
- `code/bb6tools_main.rs`, `code/bb6tools_Cargo.toml` — independent Rust implementation (num-bigint); its `recur_log` mode produced the cross-check run to 23,250,000 terms: `bb6tools recur_log 23250000 <outfile> 250000`
- `data/gmp_100M.csv` — 400 checkpoints (every 250,000 terms): `n, bits, max_v2_so_far, fnv1a64, elapsed_s`
- `data/gmp_100M_stdout.txt` — full run log (checkpoints, v2 record lines, final `done`)
- `data/gmp_100M_FINAL.txt` — run report + sha256 of csv/stdout
- `data/crosscheck_C_vs_Rust.txt` — the 93 overlapping checkpoints, field by field
- `data/traj_rust_2325M.csv` + `_stdout.txt` — Rust run artifacts
- `data/S1_traj_report.md|json|stdout.txt` — third independent implementation (Python, stdlib bigint)
- `data/smoke_rebuild.txt` + `smoke_rebuild.csv` + `smoke_rebuild_stdout.txt` — fresh rebuild smoke test
- `SHA256SUMS` — SHA-256 of every file in this package

## Reproduce

Requirements: any C compiler + GMP (tested: gcc 15.2.0, GMP 6.3.0, Ubuntu 26.04 under WSL2).

    gcc -O2 -o bb6gmp bb6gmp.c -lgmp
    ./bb6gmp 100000000 250000 out.csv > stdout.txt

Full run: **40.10 h** wall, single-threaded, AMD Ryzen 5 5600X (~4.6 GHz), avg 692.6 terms/s. The chain is inherently sequential — no parallel or GPU speedup exists.

**Quick validation (~75 s):** `./bb6gmp 2500000 250000 check.csv` — the 10 checkpoint rows must equal the first 10 rows of `data/gmp_100M.csv` on (n, bits, max_v2, FNV-1a 64). This exact test was performed with a fresh `gcc -O2` build: 10 rows match, 0 mismatches (`data/smoke_rebuild.txt`).

Values are compiler- and machine-independent (exact integer arithmetic). Build flags affect only speed. The original binary (hash below) was built 2026-09-11 on the run machine; a fresh rebuild reproduces the values bit-exactly.

## Verification performed

1. **Two independent implementations over an overlapping range** — C+GMP (full 100M) vs Rust num-bigint (first 23,250,000 terms): **93 overlapping checkpoints match exactly**, 0 mismatches (`data/crosscheck_C_vs_Rust.txt`). Both print the v2=25 record at the same n; checkpoint n=23,250,000 has FNV hash `00f1dc201ed33796` in both.
2. **Third implementation (Python stdlib bigint)** — independent recomputation: published prefix matches exactly (6, 10, 17, 41, 101, 251, 626, 1095, 2736, 2995); bit-length at n=1,000,000 = 941,419, identical to C+GMP; v2 statistics + growth reported (`data/S1_traj_report.md`).
3. **Fresh rebuild smoke test** — clean `gcc -O2` rebuild reproduced the first 10 checkpoints bit-exactly.
4. **Hash anchors (SHA-256):**
   - `data/gmp_100M.csv` — `2dd4c88d169f5db331598d49a7773504a18f6dd621d15482f9b497915adb3169`
   - `data/gmp_100M_stdout.txt` — `f1f579295788b228fbfe98aba9e4b09e50f494aa42689612fe0a4320ae3468f6`
   - `code/bb6gmp-linux-x86_64` — `8c3e2a4b19fd11ce3784c0cdae6612535ae5f840409df5d33ecbda5a18b71acd`
   - `code/bb6gmp.c` — `d24769d23fce76c26917791b783e495a4b43653fef9ff2872026940197b0d8db`
   - `code/bb6tools_main.rs` — `dd9e4e6362c215e57cad1f5f7dea144a96aa584b058af62334556aa7e274d05d`

## Indexing conventions (needed to re-check the numbers)

- Checkpoint rows are labeled by **number of updates applied**: row `n` describes the term after n updates (start b0 = 6).
- `V2RECORD v2=k at n=...` lines are printed when iteration n processes the **pre-update** term; `n` is therefore the 1-based position of that term in the sequence 6, 10, 17, … (6 is n=1). The v2=25 record term is the term reached after 23,145,880 updates.
- Halt condition: the term is a power of 2 iff its odd part equals 1.
- FNV-1a 64 convention: h = 0xcbf29ce484222325; for each little-endian 64-bit limb: h = (h XOR limb) * 0x100000001b3.

## What this does NOT show

This extends the computed range. It does not prove non-halting and does not resolve the machine's halting question (believed out of reach of current mathematics).

## Notes

- Decimal digit count: derived exactly from the bit-length; log10(b) in [28334463.0923, 28334463.3934) implies 28,334,464 digits (floor+1).
- The exact final value of b (a ~28.3M-digit integer) was not dumped by the run; the bit-length + FNV hash fully identify it for verification purposes.
- `data/S1_traj_report.*`: local machine paths redacted (`<local>`); computational content unchanged.
- License: code (`code/`) — MIT (see `LICENSE`); data, logs and text (`data/`, `*.md`) — CC-BY-4.0.

## Cite

Seiji (September 2026). *Space Needle (BB(6)) — computation extended to 100,000,000 terms*. https://github.com/oohzaim1-afk/space-needle-100M
