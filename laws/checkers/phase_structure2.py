"""Extended phase-structure checks (Space Needle): huge-m ladders, big-c L1, L4 spots.

Complements phase_structure.py (m<=200, c<=200) and phase_l4_ext.py (L4 m<=100).
Simulates exactly total+1 steps, snapshots at `total`, verifies config + sweep structure.

Usage: python phase_structure2.py
"""
TABLE = [
    [(1, +1, 1), (1, -1, 0)],
    [(1, -1, 2), (0, +1, 4)],
    [(1, -1, 5), (1, -1, 3)],
    [(0, +1, 1), (0, -1, 0)],
    [(1, +1, 2), (1, +1, 4)],
    [None,        (0, -1, 3)],
]

def simulate(b, c, exact_total):
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
    snap = None
    runs = []
    cur_dir = 0; cur_len = 0
    prev_head = head
    halted = False
    while steps < exact_total + 1:
        if steps == exact_total:
            snap = (bytes(tape), head, state)
        v = tape[head]
        tr = TABLE[state][v]
        if tr is None:
            halted = True
            break
        w, mv, nxt = tr
        tape[head] = w
        head += mv
        state = nxt
        steps += 1
        d = head - prev_head
        if d == cur_dir:
            cur_len += 1
        else:
            if cur_len:
                runs.append(cur_len)
            cur_dir = d; cur_len = 1
        prev_head = head
    if cur_len:
        runs.append(cur_len)
    return halted, runs, snap

def check_config(tape, head, state, b, c):
    if state != 0 or tape[head] != 0:
        return False
    for i in range(head):
        if tape[i]:
            return False
    q = head + 1
    if b >= 1:
        bp = 0
        while tape[q] == 1:
            bp += 1; q += 1
        if bp != b or tape[q] != 0 or tape[q + 1] != 0:
            return False
        q += 2
        cp = 0
        while tape[q] == 1:
            cp += 1; q += 1
        if cp != c:
            return False
    else:
        if tape[q] != 0 or tape[q + 1] != 0:
            return False
        q += 2
        cp = 0
        while tape[q] == 1:
            cp += 1; q += 1
        if cp != c:
            return False
    while q < len(tape):
        if tape[q]:
            return False
        q += 1
    return True

def main():
    ok = True

    print("== L3 ladder, big m (c=1) ==")
    for m in (250, 300, 400, 500, 1000, 2000, 4094):
        b = 2 * m + 3
        total = 2 * (m + 3) ** 2 + 1
        halted, runs, snap = simulate(b, 1, total)
        pred = list(range(2 * m + 5, 0, -1)) + [m + 4]
        cfgok = snap is not None and check_config(snap[0], snap[1], snap[2], m, 5 + m)
        runsok = runs[:len(pred)] == pred and len(runs) == len(pred) + 1
        good = (not halted) and cfgok and runsok
        ok &= good
        print(f"  m={m}: total={total} halted={halted} cfg={cfgok} runs={runsok} {'OK' if good else 'BAD'}")

    print("== L3 ladder, c=0 spot ==")
    for m in (500, 2000):
        b = 2 * m + 3
        total = 2 * (m + 3) ** 2 + 1
        halted, runs, snap = simulate(b, 0, total)
        pred = list(range(2 * m + 5, 0, -1)) + [m + 4]
        cfgok = snap is not None and check_config(snap[0], snap[1], snap[2], m, 4 + m)
        runsok = runs[:len(pred)] == pred and len(runs) == len(pred) + 1
        good = (not halted) and cfgok and runsok
        ok &= good
        print(f"  m={m}: total={total} halted={halted} cfg={cfgok} runs={runsok} {'OK' if good else 'BAD'}")

    print("== L1 big c ==")
    for c in (500, 1000, 5000, 10000, 100000):
        total = 2 * c + 33
        halted, runs, snap = simulate(0, c, total)
        pred = [1, 2, 4, 3, 3, 2, 1, 3, 1, 2, c + 6, c + 5]
        cfgok = snap is not None and check_config(snap[0], snap[1], snap[2], c + 2, 1)
        runsok = runs[:len(pred)] == pred and len(runs) == len(pred) + 1
        good = (not halted) and cfgok and runsok
        ok &= good
        print(f"  c={c}: total={total} halted={halted} cfg={cfgok} runs={runsok} {'OK' if good else 'BAD'}")

    print("== L4 spots ==")
    for m in (150, 200):
        c = 1
        b = 2 * m + 2
        total = (3 * m + 8) * (m * m + 7 * m + 13) + 2 * (c - 1)
        halted, runs, snap = simulate(b, c, total)
        cfgok = snap is not None and check_config(snap[0], snap[1], snap[2], 7 + 5 * m + c, 1)
        nr = 5 * m * m + 23 * m + 31
        runok = len(runs) == nr
        good = (not halted) and cfgok and runok
        ok &= good
        print(f"  m={m}: total={total} halted={halted} cfg={cfgok} nruns={len(runs)} pred_nruns={nr} {'OK' if good else 'BAD'}")

    print("VERDICT:", "ALL OK" if ok else "FAILURES PRESENT")

if __name__ == '__main__':
    main()
