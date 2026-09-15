"""CRT-refined obstruction classification for a = 1..40.

For b = m*2^a (m odd):  f(b) ≡ r_a := (2a-3)/2  (mod q_a),  q_a = 2^(a+1)+3.
f(b) can be a power of 2 only if 2^j ≡ r_a (mod q_a) for some j >= 0.

Per prime power p^e || q_a:
  - if gcd(r_a, p) > 1  -> OBSTRUCTED (2^j is a unit, r is not)
  - else membership in <2> via r^ord == 1 (exact for odd p, cyclic units)
    gives a discrete log j_p (mod ord_p), computed by BSGS.
Global solvability needs CRT consistency: j ≡ j_p (mod ord_p) for all p,
solvable iff all pairs agree mod gcd(ord_p, ord_p').

Output: for each a: verdict OBSTRUCTED (witness) or ADMISSIBLE (with j mod lcm).
Plus numeric verification: for ADMISSIBLE, verify 2^j ≡ r_a (mod q_a) and
f(m*2^a) ≡ r_a (mod q_a) for random m.

Usage: python crt_obstruction.py
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
    # small trial division first
    d = 2
    while d * d <= n and d < 10 ** 6:
        while n % d == 0:
            fs[d] = fs.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        def rec(x):
            if x == 1: return
            if _is_prime(x):
                fs[x] = fs.get(x, 0) + 1; return
            import random as _r
            while True:
                c = _r.randrange(1, x)
                xx = _r.randrange(2, x); y = xx; g = 1
                while g == 1:
                    xx = (xx * xx + c) % x
                    y = (y * y + c) % x
                    y = (y * y + c) % x
                    g = math.gcd(abs(xx - y), x)
                if g != x:
                    rec(g); rec(x // g)
                    return
        rec(n)
    return fs

def ord2_mod(mod):
    fs = factor(mod)
    phi = 1
    for p, e in fs.items():
        phi *= (p - 1) * (p ** (e - 1))
    n = phi
    for t in factor(phi):
        while n % t == 0 and pow(2, n // t, mod) == 1:
            n //= t
    return n

def bsgs_log(g, target, mod, order):
    """discrete log of target base g modulo mod, assuming order = ord(g), target in <g>.
    Raises MemoryError-guard: if sqrt(order) exceeds CAP entries, raise SkipBSGS."""
    m = int(math.isqrt(order)) + 1
    if m > 5_000_000:
        raise SkipBSGS(f"sqrt(order)={m} > cap")
    table = {}
    e = 1
    for j in range(m):
        table.setdefault(e, j)
        e = e * g % mod
    # factor = g^{-m}
    gm = pow(g, m, mod)
    inv_gm = pow(gm, -1, mod)
    gamma = target
    for i in range(m + 1):
        if gamma in table:
            return (i * m + table[gamma]) % order
        gamma = gamma * inv_gm % mod
    return None


class SkipBSGS(Exception):
    pass

def crt_pair(r1, m1, r2, m2):
    """returns (r, m) or None if unsolvable."""
    g = math.gcd(m1, m2)
    if (r2 - r1) % g != 0:
        return None
    l = m1 // g * m2
    # solve r ≡ r1 mod m1, r ≡ r2 mod m2
    m1g = m1 // g
    m2g = m2 // g
    inv = pow(m1g, -1, m2g)
    t = ((r2 - r1) // g * inv) % m2g
    r = (r1 + m1 * t) % l
    return r, l

def main():
    random.seed(20260911)
    print("== CRT-refined classification, a = 1..40 ==")
    admissible = []
    obstructed = []
    undetermined = []
    for a in range(1, 41):
        q = (1 << (a + 1)) + 3
        r = (2 * a - 3) * pow(2, -1, q) % q
        fs = factor(q)
        parts = []
        ob = None
        for p, e in sorted(fs.items()):
            pe = p ** e
            rp = r % pe
            if rp % p == 0:
                ob = f"p={p} | r"
                break
            o = ord2_mod(pe)
            # exact membership test first: r^o == 1 (mod pe) iff r in <2> (units cyclic per prime power)
            if pow(rp, o, pe) != 1:
                ob = f"pe={pe} r^ord != 1"
                break
            try:
                jp = bsgs_log(2, rp, pe, o)
            except SkipBSGS:
                ob = f"SKIPPED-J pe={pe} (order too large; membership OK)"
                break
            if jp is None:
                ob = f"p^e={pe} r notin <2>"
                break
            parts.append((jp, o, p, pe))
        if ob is None and len(parts) > 1:
            # CRT consistency
            rr, mm = parts[0][0], parts[0][1]
            for jp, o, p, pe in parts[1:]:
                res = crt_pair(rr, mm, jp, o)
                if res is None:
                    ob = f"CRT fail between {parts[0][3]} and {pe}"
                    break
                rr, mm = res
            jj = rr if ob is None else None
        else:
            jj = parts[0][0] if (ob is None and parts) else None
            mm = parts[0][1] if (ob is None and parts) else None
        if ob is None:
            # numeric verify: 2^j ≡ r (mod q)
            assert jj is not None
            okj = pow(2, jj, q) == r
            # random m check
            okb = all((f((random.randrange(1, 2**40) | 1) * 2**a) % q) == r for _ in range(50))
            status = "ADMISSIBLE" if (okj and okb) else "ADMISSIBLE-BAD"
            admissible.append((a, jj, q))
            print(f"a={a:2d} ADMISSIBLE  j={jj} (mod {mm})  q={q}  verify_j={okj} verify_f={okb}")
        elif ob.startswith('SKIPPED'):
            undetermined.append((a, ob))
            print(f"a={a:2d} UNDETERMINED  {ob}")
        else:
            obstructed.append((a, ob))
            print(f"a={a:2d} OBSTRUCTED  {ob}")

    print()
    print(f"ADMISSIBLE: {[a for a,_,_ in admissible]}")
    print(f"UNDETERMINED: {[a for a,_ in undetermined]}")
    print(f"OBSTRUCTED: {[a for a,_ in obstructed]}")
    print()
    # cross-check against reference from earlier runs
    ref_ob = [1, 4, 9, 10, 13, 19, 21, 22, 23, 24, 25, 26, 31, 32, 33, 39, 40]
    got_ob = sorted([a for a, _ in obstructed])
    print(f"reference obstructed: {ref_ob}")
    print(f"computed obstructed:  {got_ob}")
    print(f"match: {ref_ob == got_ob}")

if __name__ == '__main__':
    main()
