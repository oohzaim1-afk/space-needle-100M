# Space Needle (BB(6)) — computational extension to 100,000,000 terms

**Computed by:** Seiji — independent computation, September 2026.


**Machine:** `1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD` — "Space Needle", a BB(6) cryptid (BMO problem 6). Discovered by mxdys (Jan 2025); low-level rules by mxdys; higher-level rules by Racheline and Katelyn Doucette.

**Result (September 2026):** the associated sequence (reduced form below) has been computed to **100,000,000 terms**. **No power of 2 was encountered** — no halt occurred anywhere in the computed range. The maximum factor-of-2 record is **v2 = 25**, first occurring at n = 23,145,881 (1-based term index; see "Indexing conventions"). The previous documented state was >17,000,000 terms with max v2 = 24 (BusyBeaverWiki "Space Needle", revision 7571 of 2026-05-18 — retrieved 2026-09-14).

**Final term:** 94,125,050 bits = **28,334,464 decimal digits** (exact), FNV-1a 64 hash of limbs `fd4332e892cc1fab`, **published in full** as `data/final_term_100M.bin` — SHA-256 `627e09c5bb1fbf93fe18ed3f2a2feaff45a16f139282364e07831337766acce1` (canonical encoding: big-endian minimal bytes, 11,765,632 bytes).

## The sequence

Reduced form (Doucette's higher-level rule; the form used by all code here):

    b0 = 6;   b_{n+1} = b_n + v2(b_n) + (3/2) * (b_n / 2^v2(b_n) - 1);   HALT if b_n is a power of 2

Prefix: 6, 10, 17, 41, 101, 251, 626, 1095, 2736, 2995, ...

## Step-count laws (L0–L4) & modular obstruction

The macro dynamics of the same machine are formalized in **`laws/`**: exact step counts for the four macro transitions (L0–L4), a closed-form halting time for the (2^k−3, ·) family (**T(k) = (2·4^k + 3k − 2)/3**, confirmed step-exact up to k = 22), and a modular obstruction classification (among valuations a ≤ 120, **96 classes can never produce a power of 2**; 24 admissible). **L1 and L3 are formally proven + machine-certified; L4 is empirical.** Full documents, proofs and self-contained certifying checkers: **`laws/`**.

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
- `code/bb6blocks.py` — block-affine re-derivation (composes k steps into one affine map; one multiplication per block) — reproduces the full range and dumps the final value
- `code/ref_traj.py` — third independent implementation (Python stdlib bigint) that produced the S1 statistics run
- `laws/` — exact step-count laws (L0–L4) + formal proofs (L1, L3) + closed-form halting time T(k) + modular obstruction classification + machine-certifying checkers (`laws/checkers/`)
- `data/block_100M.csv` — block re-derivation checkpoints: n, bits, max_v2, fnv1a64, decimal_digits, elapsed_s
- `data/sha256_checkpoints_100M.csv` — SHA-256 (big-endian minimal bytes) of the value at every checkpoint
- `data/hist_v2_100M.csv` — full v2 histogram over the 100,000,000 terms
- `data/final_term_100M.bin` + `data/final_term_100M.sha256` — the final value itself + its hashes
- `data/block_100M_run_info.txt` — block re-derivation log (400/400 comparison, records, timings)
- `data/LICENSE` — CC-BY-4.0 for everything under `data/`
- `SHA256SUMS` + `SHA256SUMS.sha256` — SHA-256 of every file in this package (plus a self-hash of SHA256SUMS)

## Reproduce

Requirements: any C compiler + GMP (tested: gcc 15.2.0, GMP 6.3.0, Ubuntu 26.04 under WSL2).

    gcc -O2 -o bb6gmp bb6gmp.c -lgmp
    ./bb6gmp 100000000 250000 out.csv > stdout.txt

Full run: **40.10 h** wall, single-threaded, AMD Ryzen 5 5600X (~4.6 GHz), avg 692.6 terms/s with this per-term build. The trajectory does admit an exact **block acceleration**: with v = v2(b) each step is the affine map b -> (A_v*b + C_v) >> (v+1) (A_v = 2^(v+1)+3, C_v = (2v-3)*2^v), and the v-sequence of a k-step block is determined by the low ~2k bits of b — so k steps compose into a single affine map applied with one multiplication of the full integer (`code/bb6blocks.py`). With that tool the same 100,000,000-term range re-derives in **22.3 min on one core** (Python 3.12 + gmpy2 2.3.1; 400/400 checkpoints identical, final term identical), and the 10^9-term range becomes an hours-scale question rather than months. Step-to-step dependence is preserved — this is algorithmic, not parallel, acceleration.

**Quick validation (~75 s):** `./bb6gmp 2500000 250000 check.csv` — the 10 checkpoint rows (the output starts with a `#` header line) must equal the first 10 rows of `data/gmp_100M.csv` on (n, bits, max_v2, FNV-1a 64). Performed with a fresh `gcc -O2` build: 10/10 rows match; re-runs overwrite (idempotent, "w" mode), and the final term is tested explicitly after the loop (`data/smoke_rebuild.txt`).

Values are compiler- and machine-independent (exact integer arithmetic). Build flags affect only speed. The original binary (hash below) was built 2026-09-11 on the run machine; a fresh rebuild reproduces the values bit-exactly.

## Verification performed

1. **Two independent implementations over an overlapping range** — C+GMP (full 100M) vs Rust num-bigint (first 23,250,000 terms): **93 overlapping checkpoints match exactly**, 0 mismatches (`data/crosscheck_C_vs_Rust.txt`). Both print the v2=25 record at the same n; checkpoint n=23,250,000 has FNV hash `00f1dc201ed33796` in both.
2. **Third implementation (Python stdlib bigint)** — independent recomputation: published prefix matches exactly (6, 10, 17, 41, 101, 251, 626, 1095, 2736, 2995); bit-length at n=1,000,000 = 941,419, identical to C+GMP; v2 statistics + growth reported (`data/S1_traj_report.md`; the script is published as `code/ref_traj.py`).
3. **Fresh rebuild smoke test** — clean `gcc -O2` rebuild reproduced the first 10 checkpoints bit-exactly; the final term is tested explicitly (`data/smoke_rebuild.txt`).
4. **Block-affine re-derivation (full range, independent arithmetic path)** — `code/bb6blocks.py` re-derived the entire 100,000,000-term range from scratch: **400/400 checkpoints identical** to the C+GMP CSV on (bits, max_v2, FNV-1a 64), the 13 v2 records identical, and the final term reproduced exactly (94,125,050 bits, FNV `fd4332e892cc1fab`). Runtime 22.3 min single-core; full log in `data/block_100M_run_info.txt`.
5. **Hash anchors (SHA-256):**
   - `data/gmp_100M.csv` — `2dd4c88d169f5db331598d49a7773504a18f6dd621d15482f9b497915adb3169`
   - `data/gmp_100M_stdout.txt` — `f1f579295788b228fbfe98aba9e4b09e50f494aa42689612fe0a4320ae3468f6`
   - `code/bb6gmp-linux-x86_64` — `8c3e2a4b19fd11ce3784c0cdae6612535ae5f840409df5d33ecbda5a18b71acd` (the exact binary used for the run; its source has since received corrections — see Notes)
   - `code/bb6gmp.c` — `8bfa58fbc54725c05837aa0f8734da98d28c32666a467b31e347c55a286ef5ca` (post-audit revision)
   - `code/bb6tools_main.rs` — `2e22dc1f23b229fb919b2637a044b77f62a064389a81c6ae8cf0d68732fb9063` (post-audit revision)
   - `data/final_term_100M.bin` — `627e09c5bb1fbf93fe18ed3f2a2feaff45a16f139282364e07831337766acce1`

## Indexing conventions (needed to re-check the numbers)

- Checkpoint rows are labeled by **number of updates applied**: row `n` describes the term after n updates (start b0 = 6).
- `V2RECORD v2=k at n=...` lines are printed when iteration n processes the **pre-update** term; `n` is therefore the 1-based position of that term in the sequence 6, 10, 17, … (6 is n=1). The v2=25 record term is the term reached after 23,145,880 updates.
- Halt condition: the term is a power of 2 iff its odd part equals 1.
- Halting has been tested on every term from position 1 (b0 = 6) through position 100,000,001 — the term produced by the 100,000,000th update. The original per-term build (shipped binary) tested positions 1..100,000,000 inside its loop; the final term is tested explicitly by the updated `bb6gmp.c` and by the block re-derivation.
- FNV-1a 64 convention: h = 0xcbf29ce484222325; for each little-endian 64-bit limb: h = (h XOR limb) * 0x100000001b3. The hash is representation-dependent (8-byte limbs; `sizeof(mp_limb_t)=8` on the run platform) — unlike the values themselves; it is identical across the C and Rust implementations (93/93 checkpoints).

## What this run measures

Beyond the range extension, the checkpoint data measures the trajectory's growth law:

- bit-length grew 94,125,050 - 3 bits over 10^8 steps: **0.9412505 bits/term** measured end-to-end, vs 0.9411487 from the closed-form mean ln-growth 0.6523545 cited on the wiki. The end-to-end mean ln-growth is 0.6524251 — a **+2.39σ** deviation under the random-walk expectation (σ of the mean = 0.29552/√10^8 ≈ 2.96e-5), within the normal spread for a run of this length;
- the full v2 histogram over all 10^8 terms (`data/hist_v2_100M.csv`) is compatible with the geometric law 2^-(k+1): counts 50,011,040 / 24,997,675 / 12,495,339 / 6,248,781 for k = 0..3 (expected 50,000,000 / 25,000,000 / 12,500,000 / 6,250,000).

## What this does NOT show

This extends the computed range. It does not prove non-halting and does not resolve the machine's halting question (believed out of reach of current mathematics). Under the documented heuristic (independent uniform low bits), the probability that a halt occurs beyond term n is of order 2^-(0.94114868*n); at n = 10^8 that is 2^-94,114,868, and extending from 17M to 100M multiplied the remaining halt probability by 2^-78,115,340. This run is a record plus statistics, not progress toward a proof.

## Notes

- Decimal digit count: 28,334,464 — verified exactly on the published final value (two independent methods: decimal_digits and len(str(b))).
- The final value of b is published in full: `data/final_term_100M.bin` (canonical encoding: big-endian minimal bytes) — SHA-256 `627e09c5bb1fbf93fe18ed3f2a2feaff45a16f139282364e07831337766acce1`; its decimal-string encoding has SHA-256 `ab859e95a0106e16dc52a4d6dda8d9d8373c778da508aebe878e8b32c655b0b8` (`data/final_term_100M.sha256`).
- Per-checkpoint cryptographic anchors: `data/sha256_checkpoints_100M.csv` lists the SHA-256 (big-endian minimal bytes) of the value at each of the 400 checkpoints.
- `code/bb6gmp.c` and `code/bb6tools_main.rs` carry post-audit corrections (2026-09-14): explicit final-term test, CSV header, "w" output mode, exact decimal-digit computation. The shipped 100M run was produced by the earlier build; the corrections change no values (fresh-build smoke test: 10/10 checkpoints identical).
- `data/S1_traj_report.*`: local machine paths redacted (`<local>`); computational content unchanged.
- License: code (`code/`) — MIT (see `LICENSE`); data, logs and text (`data/`, `*.md`) — CC-BY-4.0.

## Cite

Seiji (September 2026). *Space Needle (BB(6)) — computation extended to 100,000,000 terms*. https://github.com/oohzaim1-afk/space-needle-100M
