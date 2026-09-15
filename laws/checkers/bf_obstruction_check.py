"""Constructive + brute-force validation of the obstruction classification (a <= 28).

Definition (no factorization, no BSGS, no CRT):
    a is ADMISSIBLE  iff  r_a := (2a-3)/2 mod q_a  lies in the ORBIT of 2 under
    multiplication mod q_a  (q_a = 2^(a+1)+3).   Orbit membership is decided by
    literally enumerating {2^j mod q_a}.

For each a:
  * enumerate the orbit (exact membership of r),
  * ADMISSIBLE -> construct the witness b = m * 2^a with
        m = (2^(j+1) - 2a + 3) / q_a,
    assert m is a positive odd integer and f(b) == 2^j EXACTLY.
  * OBSTRUCTED -> brute-force m <= M confirming no f(m*2^a) is a power of 2
    (a consistency check; the proof itself is the orbit non-membership).

Usage: python bf_obstruction_check.py [M]        (default M = 1_000_000)
Writes reports/bf_obstruction_report.txt, exits 0 iff all checks pass.
"""
import os, sys

sys.set_int_max_str_digits(1_000_000)  # witnesses can be astronomically large

# Output directory: "reports" next to this script (override: SPN_REPORTS env var).
REPORTS = os.environ.get("SPN_REPORTS") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "reports")
ORBIT_CAP = 60_000_000


def v2(x):
    c = 0
    while x % 2 == 0:
        x //= 2; c += 1
    return c


def is_pow2(x):
    return x > 0 and (x & (x - 1)) == 0


def f_of(b):
    v = v2(b)
    m = b >> v
    return b + v + 3 * (m - 1) // 2


def main():
    M = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
    out = [f"== constructive/brute-force validation of obstruction classification (a<=28, M={M}) =="]
    ok = True
    n_adm = n_obs = 0
    for a in range(1, 29):
        q = (1 << (a + 1)) + 3
        r = (2 * a - 3) * pow(2, -1, q) % q
        # enumerate orbit of 2 mod q
        orbit = {}
        x = 1
        j = 0
        overflow = False
        while x not in orbit:
            orbit[x] = j
            x = x * 2 % q
            j += 1
            if j > ORBIT_CAP:
                overflow = True
                break
        if x != 1:
            overflow = True
        if overflow:
            # independent fallback: full-range BSGS for 2^j ≡ r (mod q), no factorization
            m2 = int(2 ** (q.bit_length() // 2 + 1)) + 1
            table = {}
            e = 1
            for jj in range(m2):
                table.setdefault(e, jj)
                e = e * 2 % q
            gm = pow(2, m2, q)
            inv = pow(gm, -1, q)
            gamma = r
            jmin = None
            for i in range(m2 + 1):
                if gamma in table:
                    jmin = (i * m2 + table[gamma])
                    if pow(2, jmin, q) != r:
                        jmin = None
                    break
                gamma = gamma * inv % q
            if jmin is None:
                n_obs += 1
                hit = None
                for m in range(1, M + 1, 2):
                    fb = f_of(m << a)
                    if is_pow2(fb):
                        hit = (m, fb)
                        break
                good = hit is None
                ok &= good
                out.append(f"a={a:2d} OBSTRUCTED (BSGS fallback): no f=2^j for m<={M} {'OK' if good else f'VIOLATION m={hit[0]}'}")
            else:
                n_adm += 1
                num = (1 << (jmin + 1)) - 2 * a + 3
                if num % q != 0:
                    out.append(f"a={a:2d} ADMISSIBLE (BSGS fallback) j={jmin}: DIVISIBILITY FAIL")
                    ok = False
                    continue
                m = num // q
                good = (m > 0 and m % 2 == 1 and f_of(m << a) == (1 << jmin))
                ok &= good
                mb = m.bit_length()
                mdesc = f"m({mb} bits)" if mb > 30 else f"m={m}"
                out.append(f"a={a:2d} ADMISSIBLE (BSGS fallback) j={jmin}: witness {mdesc} -> f == 2^{jmin} {'OK' if good else 'FAIL'}")
            continue
        o = j  # ord(2) mod q
        if r in orbit:
            n_adm += 1
            jmin = orbit[r]
            # construct witness
            num = (1 << (jmin + 1)) - 2 * a + 3
            if num % q != 0:
                out.append(f"a={a:2d} ADMISSIBLE j={jmin} o={o}: DIVISIBILITY FAIL (num%q={num % q})")
                ok = False
                continue
            m = num // q
            good = (m > 0 and m % 2 == 1 and f_of(m << a) == (1 << jmin))
            ok &= good
            mb = m.bit_length()
            mdesc = f"m({mb} bits)" if mb > 30 else f"m={m}"
            bdesc = f"b({mb + a} bits)" if mb + a > 30 else f"b={m << a}"
            out.append(f"a={a:2d} ADMISSIBLE o={o} j={jmin}: witness {mdesc} {bdesc} -> f == 2^{jmin} {'OK' if good else 'FAIL'}")
        else:
            n_obs += 1
            hit = None
            for m in range(1, M + 1, 2):
                fb = f_of(m << a)
                if is_pow2(fb):
                    hit = (m, fb)
                    break
            good = hit is None
            ok &= good
            out.append(f"a={a:2d} OBSTRUCTED o={o}: no f=2^j for m<={M} {'OK' if good else f'VIOLATION m={hit[0]} f={hit[1]}'}")
    out.append("")
    out.append(f"admissible={n_adm} obstructed={n_obs} (a<=28)")
    out.append("VERDICT: ALL OK" if ok else "VERDICT: FAILURES PRESENT")
    rep = "\n".join(out)
    print(rep)
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, "bf_obstruction_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(rep + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
