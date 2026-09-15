"""L4 structural checks: prefix / suffix patterns + run-count formula.

L4: (2m+2, c) -> (7+5m+c, 1) in (3m+8)(m^2+7m+13) + 2(c-1) steps.

Empirical structure (observed m=0..2):
  prefix: [2m+4, 2m+3, ..., 3, 1]   (descending from 2m+4 to 3, then 1)
  suffix: [..., 5m+12, 5m+11, 1]    (two big sweeps then trailing 1)
  nruns = 5m^2 + 23m + 31

This script verifies prefix, suffix and nruns for m = 0..60 (c=1).

Usage: python l4_structure.py
"""
TABLE = [
    [(1, +1, 1), (1, -1, 0)],
    [(1, -1, 2), (0, +1, 4)],
    [(1, -1, 5), (1, -1, 3)],
    [(0, +1, 1), (0, -1, 0)],
    [(1, +1, 2), (1, +1, 4)],
    [None,        (0, -1, 3)],
]

def simulate_runs(b, c, total_plus=1):
    L = 65536 + b + 2 + c
    tape = bytearray(L)
    start = 32768
    p = start
    for _ in range(b):
        tape[p] = 1; p += 1
    tape[p] = 0; p += 1
    tape[p] = 0; p += 1
    for _ in range(c):
        tape[p] = 1; p += 1
    head = start - 1
    state = 0
    steps = 0
    runs = []
    cur_dir = 0; cur_len = 0
    prev = head
    while steps < total_plus:
        v = tape[head]
        tr = TABLE[state][v]
        if tr is None:
            break
        w, mv, nxt = tr
        tape[head] = w
        head += mv
        state = nxt
        steps += 1
        d = head - prev
        if d == cur_dir:
            cur_len += 1
        else:
            if cur_len:
                runs.append(cur_len)
            cur_dir = d; cur_len = 1
        prev = head
    if cur_len:
        runs.append(cur_len)
    return runs

def main():
    ok = True
    bad_prefix = bad_suffix = bad_nruns = 0
    for m in range(0, 61):
        b = 2 * m + 2
        total = (3 * m + 8) * (m * m + 7 * m + 13)
        runs = simulate_runs(b, 1, total + 1)
        pred_prefix = list(range(2 * m + 4, 2, -1)) + [1]  # 2m+4 .. 3, then 1
        # verify prefix
        if runs[:len(pred_prefix)] != pred_prefix:
            bad_prefix += 1
            print(f"PREFIX FAIL m={m}: {runs[:len(pred_prefix)+2]} vs {pred_prefix}")
        # verify suffix (last three runs: [5m+12, 5m+11, trailing])
        tail = runs[-3:]
        if tail[:2] != [5 * m + 12, 5 * m + 11]:
            bad_suffix += 1
            print(f"SUFFIX FAIL m={m}: tail={tail} expected [{5*m+12},{5*m+11},*]")
        # nruns (include the +1 trailing run counted here)
        nr = 5 * m * m + 23 * m + 31
        if len(runs) != nr:
            bad_nruns += 1
            print(f"NRUNS FAIL m={m}: got {len(runs)} want {nr}")
    print(f"prefix fails: {bad_prefix}, suffix fails: {bad_suffix}, nruns fails: {bad_nruns}")
    ok = (bad_prefix == 0 and bad_suffix == 0 and bad_nruns == 0)
    print("VERDICT:", "ALL OK" if ok else "FAILURES PRESENT")

if __name__ == '__main__':
    main()
