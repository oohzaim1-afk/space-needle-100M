"""Independent verification of the CRT-refined obstruction classification.

For each a in 1..40:
  q = 2^(a+1)+3, r = (2a-3)*inv2 mod q.
  Claim: f(b) ≡ r (mod q) for ALL b with v2(b)=a  [verified on random b]
  Classification: a is OBSTRUCTED iff 2^j ≡ r (mod q) has NO solution j >= 0.

Rigorous method (independent re-derivation + assertions):
  * factor q (trial + pollard rho); verify: product == q and each factor prime.
  * per prime power p^e: verify r % p == 0 -> obstruction OR
    ord = exact order of 2 mod p^e (verify pow(2,ord)==1 and minimality by
    dividing out prime factors of phi); r^ord == 1 -> r ∈ <2> (cyclic units),
    then recover jp by BSGS and VERIFY pow(2,jp,pe) == r % pe.
  * CRP consistency across prime powers: if inconsistent -> obstruction.
  * For small q (<= ~2^26) also brute-force the orbit of 1 under x->2x mod q
    and check r membership directly (fully independent of factorization).

Usage: python verify_crt_classification.py
"""
import math, random

def v2(x):
    c = 0
    while x % 2 == 0:
        x //= 2; c += 1
    return c

def f(b):
    v = v2(b)
    return b + v + 3 * (b // (2 ** v) - 1) // 2

def _is_prime(n):
    if n < 2: return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n % p == 0:
            return n == p
    d = n - 1; s = 0
    while d % 2 == 0:
        d //= 2; s += 1
    for a in (2,3,5,7,11,13,17,19,23,29,31,37):
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True

def factor(n):
    fs = {}
    d = 2
    while d * d <= n and d < 10 ** 5:
        while n % d == 0:
            fs[d] = fs.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        def rec(x):
            if x == 1: return
            if _is_prime(x):
                fs[x] = fs.get(x, 0) + 1; return
            while True:
                c = random.randrange(1, x)
                xx = random.randrange(2, x); y = xx; g = 1
                while g == 1:
                    xx = (xx * xx + c) % x
                    y = (y * y + c) % x
                    y = (y * y + c) % x
                    g = math.gcd(abs(xx - y), x)
                if g != x:
                    rec(g); rec(x // g); return
        rec(n)
    return fs

def exact_ord2_mod(pe):
    """exact multiplicative order of 2 mod pe (odd), with internal checks."""
    fs = factor(pe)
    phi = 1
    for p, e in fs.items():
        assert _is_prime(p)
        phi *= (p - 1) * (p ** (e - 1))
    # verify phi by Euler
    n = phi
    for t in factor(phi):
        assert _is_prime(t)
        while n % t == 0 and pow(2, n // t, pe) == 1:
            n //= t
    assert pow(2, n, pe) == 1
    # minimality: for each prime divisor t of phi, pow(2, n//t) != 1 (n already reduced)
    for t in factor(n):
        assert pow(2, n // t, pe) != 1, "order not exact"
    return n

def bsgs(g, target, mod, order):
    m = int(math.isqrt(order)) + 1
    table = {}
    e = 1
    for j in range(m):
        table.setdefault(e, j)
        e = e * g % mod
    inv = pow(pow(g, m, mod), -1, mod)
    gamma = target % mod
    for i in range(m + 1):
        if gamma in table:
            j = (i * m + table[gamma]) % order
            assert pow(g, j, mod) == target % mod
            return j
        gamma = gamma * inv % mod
    return None

def main():
    random.seed(20260911)
    print("== independent verification of CRT classification ==")
    results = {}
    for a in range(1, 41):
        q = (1 << (a + 1)) + 3
        r = (2 * a - 3) * pow(2, -1, q) % q
        fs = factor(q)
        # verify factorization of q
        prod = 1
        for p, e in fs.items():
            assert _is_prime(p), f"p={p} not prime"
            prod *= p ** e
        assert prod == q, f"factorization product mismatch a={a}"

        parts = []
        ob = None
        for p, e in sorted(fs.items()):
            pe = p ** e
            rp = r % pe
            if rp % p == 0:
                ob = f"p={p}|r"
                break
            o = exact_ord2_mod(pe)
            ok = pow(rp, o, pe) == 1
            if not ok:
                ob = f"pe={pe}: r^ord != 1"
                break
            jp = bsgs(2, rp, pe, o)
            assert jp is not None
            parts.append((jp, o, pe))
        if ob is None and len(parts) > 1:
            rr, mm = parts[0][0], parts[0][1]
            for jp, o, pe in parts[1:]:
                g = math.gcd(mm, o)
                if (jp - rr) % g != 0:
                    ob = f"CRT fail ({rr} mod {mm} vs {jp} mod {o})"
                    break
                # combine
                m1g = mm // g
                m2g = o // g
                inv = pow(m1g, -1, m2g)
                t = ((jp - rr) // g * inv) % m2g
                rr = (rr + mm * t) % (mm // g * o)
                mm = mm // g * o
            if ob is None:
                assert pow(2, rr, q) == r
                jj, mm2 = rr, mm
            else:
                jj = None
        elif ob is None:
            jj = parts[0][0]
            mm2 = parts[0][1]
            assert pow(2, jj, q) == r
        else:
            jj = None
        # brute-force orbit check for small q
        bf = None
        if q <= 2 ** 26:
            x = 1
            seen = set()
            while x not in seen:
                seen.add(x)
                x = x * 2 % q
            bf = (r in seen)
            if jj is not None:
                assert bf is True, f"a={a}: structural admissible but orbit says no"
            else:
                assert bf is False, f"a={a}: structural obstructed but orbit says yes"
        # random f-consistency check (f(b) ≡ r mod q)
        cons = all((f((random.randrange(1, 2 ** 40) | 1) * 2 ** a) % q) == r for _ in range(20))
        assert cons, f"a={a}: f-consistency failed"
        verdict = "OBSTRUCTED" if jj is None else "ADMISSIBLE"
        results[a] = (verdict, ob)
        print(f"a={a:2d} {verdict:10s} {ob if ob else f'j={jj} mod {mm2}'}  bf={bf}")

    obs = [a for a in results if results[a][0] == "OBSTRUCTED"]
    adm = [a for a in results if results[a][0] == "ADMISSIBLE"]
    print()
    print(f"ADMISSIBLE: {adm}")
    print(f"OBSTRUCTED: {obs}")
    print(f"counts: {len(adm)} admissible / {len(obs)} obstructed of 40")
    print()
    print("VERDICT: ALL ASSERTIONS PASSED")

if __name__ == '__main__':
    main()
