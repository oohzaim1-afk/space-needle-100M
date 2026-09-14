// bb6gmp.c — Space Needle trajectory (independent implementation, C + GMP)
// Recurrence (Katelyn Doucette): b_{n+1} = b_n + v2(b_n) + (3/2)(m-1),
// where m = odd part of b (b = 2^v2 * m).  HALT condition: b is a power of 2.
// Checkpoints: term, bit-length, running max v2, FNV-1a over little-endian
// 64-bit limbs (same convention as the Rust num-bigint implementation).
//
// usage: bb6gmp <N> <check_every> <out.csv>
#include <gmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

static uint64_t fnv_limbs(const mpz_t b) {
    uint64_t h = 0xcbf29ce484222325ull;
    size_t n = mpz_size(b);
    const mp_limb_t *limbs = mpz_limbs_read(b);
    for (size_t i = 0; i < n; i++) {
        h ^= (uint64_t)limbs[i];
        h *= 0x100000001b3ull;
    }
    return h;
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "usage: %s N check_every out.csv\n", argv[0]);
        return 1;
    }
    unsigned long long N = strtoull(argv[1], 0, 10);
    unsigned long long ce = strtoull(argv[2], 0, 10);
    if (ce == 0) ce = 250000;
    FILE *f = fopen(argv[3], "a");
    if (!f) { perror("fopen"); return 1; }

    printf("sizeof(mp_limb_t)=%zu\n", sizeof(mp_limb_t));
    fflush(stdout);

    mpz_t b, m, t;
    mpz_init_set_ui(b, 6);
    mpz_init(m);
    mpz_init(t);
    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int max_v2 = 0;
    unsigned long long i;
    for (i = 1; i <= N; i++) {
        int tz = (int)mpz_scan1(b, 0);
        if (tz > max_v2) {
            max_v2 = tz;
            printf("V2RECORD v2=%d at n=%llu\n", tz, i);
            fflush(stdout);
        }
        mpz_tdiv_q_2exp(m, b, tz);        /* m = odd part */
        if (mpz_cmp_ui(m, 1) == 0) {
            printf("HALT_CONDITION_MET at n=%llu\n", i);
            fprintf(f, "HALT_CONDITION_MET,n=%llu\n", i);
            fflush(f);
            break;
        }
        mpz_sub_ui(t, m, 1);              /* t = m-1 */
        mpz_mul_ui(t, t, 3);              /* 3(m-1) */
        mpz_tdiv_q_2exp(t, t, 1);         /* 3(m-1)/2 */
        mpz_add(b, b, t);                 /* b += t  (uses ORIGINAL b) */
        mpz_add_ui(b, b, (unsigned long)tz); /* b += v2 of ORIGINAL b */
        if (i % ce == 0) {
            struct timespec now;
            clock_gettime(CLOCK_MONOTONIC, &now);
            double el = (now.tv_sec - t0.tv_sec) + (now.tv_nsec - t0.tv_nsec) / 1e9;
            fprintf(f, "%llu,%zu,%d,%016llx,%.1f\n", i, mpz_sizeinbase(b, 2), max_v2,
                    (unsigned long long)fnv_limbs(b), el);
            fflush(f);
            printf("ck n=%llu bits=%zu t=%.0f\n", i, mpz_sizeinbase(b, 2), el);
            fflush(stdout);
        }
    }
    printf("done N=%llu\n", N);
    return 0;
}
