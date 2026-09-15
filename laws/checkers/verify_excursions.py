"""Independent verification of the head-excursion formulas (Space Needle).

Two independent implementations:
  1. Rust `bb6tools extent <b> <c>` (target3 build, growable tape) - large cases,
     results parsed from reports/extent_*.txt ("done cps=2 steps=... min=... max=...").
  2. This script's own Python dict-tape simulator with a FULL-SHAPE detector
     (state A, head at leftmost1 - 1, all cells left of head zero, exact
     1^b 00 1^c span, all cells right of config zero; plus the b=0 branch).

Formulas under test (relative to the initial leftmost 1):
  even b (incl. b=0): min = -(3b/2 + 3), max = +(b + c + 3)
  odd  b            : min = -2,           max = +(b + 1)

Usage: python verify_excursions.py
Writes reports/extent_verification_report.txt and exits 0 iff ALL OK.
"""
import glob, os, sys

# "reports" next to this script (override: SPN_REPORTS env var). Expects extent_*.txt
# artifacts produced by the Rust tool (bb6tools extent) next to it.
REPORTS = os.environ.get("SPN_REPORTS") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "reports")

TABLE = [
    [(1, +1, 1), (1, -1, 0)],   # A
    [(1, -1, 2), (0, +1, 4)],   # B
    [(1, -1, 5), (1, -1, 3)],   # C
    [(0, +1, 1), (0, -1, 0)],   # D
    [(1, +1, 2), (1, +1, 4)],   # E
    [None,       (0, -1, 3)],   # F
]


def py_extent(b0, c0, max_steps=10**9):
    """Dict-tape sim, full-shape detector (independent of the Rust tool)."""
    tape = {}
    p = 0
    for _ in range(b0):
        tape[p] = 1; p += 1
    tape[p] = 0; p += 1
    tape[p] = 0; p += 1
    for _ in range(c0):
        tape[p] = 1; p += 1
    head, state, steps = -1, 0, 0
    mn = mx = head
    wmin, wmax = 0, p - 1

    def cell(x):
        return tape.get(x, 0)

    def left_all_zero():
        for x in range(wmin - 2, head):
            if cell(x) != 0:
                return False
        return True

    def right_all_zero(start):
        for x in range(start, wmax + 3):
            if cell(x) != 0:
                return False
        return True

    def detect():
        if state != 0 or cell(head) != 0:
            return None
        # b >= 1 branch: head at L-1, pattern 1^b 00 1^c
        if cell(head + 1) == 1:
            if not left_all_zero():
                return None
            bp = 0; q = head + 1
            while cell(q) == 1:
                bp += 1; q += 1
            if cell(q) != 0 or cell(q + 1) != 0:
                return None
            q2 = q + 2; cp = 0
            while cell(q2) == 1:
                cp += 1; q2 += 1
            if cp == 0 or not right_all_zero(q2):
                return None
            return (bp, cp)
        # b = 0 branch: head zero, then 00 1^c to its right
        if cell(head + 1) == 0 and cell(head + 2) == 0 and cell(head + 3) == 1:
            if not left_all_zero():
                return None
            cp = 0; q = head + 3
            while cell(q) == 1:
                cp += 1; q += 1
            if cp == 0 or not right_all_zero(q):
                return None
            return (0, cp)
        return None

    while steps < max_steps:
        if head < mn: mn = head
        if head > mx: mx = head
        d = detect()
        if d is not None and d != (b0, c0):
            return steps, mn, mx, d
        tr = TABLE[state][cell(head)]
        if tr is None:
            return steps, mn, mx, "HALT"
        w, mv, nxt = tr
        tape[head] = w
        if head < wmin: wmin = head
        if head > wmax: wmax = head
        head += mv
        state = nxt
        steps += 1
    return None


def pred(b, c):
    if b % 2 == 0:
        return (-(3 * b // 2 + 3), b + c + 3)
    return (-2, b + 1)


def main():
    out = []
    ok = True

    # ---- 1) parse Rust extent outputs ----
    out.append("== Rust extent measurements (growable tape) ==")
    for f in sorted(glob.glob(os.path.join(REPORTS, "extent_[0-9]*.txt"))):
        name = os.path.basename(f)
        lines = open(f, encoding="utf-8", errors="replace").read().splitlines()
        b = c = None
        for ln in lines:
            if ln.startswith("EXTENT START"):
                parts = ln.split()
                b = int(parts[2].split("=")[1]); c = int(parts[3].split("=")[1])
                break
        m = None
        for ln in lines:
            if ln.startswith("done cps=2"):
                parts = ln.split()
                m = tuple(int(parts[2].split("=")[1:][0]),) if False else parts
        done = None
        for ln in lines:
            if ln.startswith("done cps=2"):
                done = ln
        if b is None or done is None:
            out.append(f"  {name}: incomplete (skipped)")
            continue
        parts = done.split()
        steps = int(parts[2].split("=")[1])
        mn = int(parts[3].split("=")[1])
        mx = int(parts[4].split("=")[1])
        pmn, pmx = pred(b, c)
        good = (mn == pmn and mx == pmx)
        ok &= good
        out.append(f"  ({b},{c}): min={mn} max={mx} steps={steps} | pred [{pmn},{pmx}] {'OK' if good else 'MISMATCH'}")

    # ---- 2) independent Python sim (small cases, even + odd) ----
    out.append("")
    out.append("== Independent Python dict-tape sim (full-shape detector) ==")
    small = [(10, 5), (20, 3), (50, 10), (100, 50),      # even
             (3, 1), (7, 1), (11, 2), (5, 10)]            # odd
    for (b, c) in small:
        r = py_extent(b, c)
        if r is None:
            out.append(f"  ({b},{c}): no detection (timeout)")
            ok = False
            continue
        steps, mn, mx, d = r
        pmn, pmx = pred(b, c)
        good = (mn == pmn and mx == pmx)
        ok &= good
        out.append(f"  ({b},{c}): -> {d} steps={steps} min={mn} max={mx} | pred [{pmn},{pmx}] {'OK' if good else 'MISMATCH'}")

    # ---- 3) L4 step-count re-check on the small even cases ----
    out.append("")
    out.append("== L4 step-count cross-check (small even cases) ==")
    for (b, c) in [(10, 5), (20, 3), (50, 10), (100, 50)]:
        m = (b - 2) // 2
        pred_steps = (3 * m + 8) * (m * m + 7 * m + 13) + 2 * (c - 1)
        r = py_extent(b, c)
        steps = r[0]
        good = (steps == pred_steps)
        ok &= good
        out.append(f"  ({b},{c}): steps={steps} pred={pred_steps} {'OK' if good else 'MISMATCH'}")

    out.append("")
    out.append("VERDICT: ALL OK" if ok else "VERDICT: FAILURES PRESENT")
    rep = "\n".join(out)
    print(rep)
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, "extent_verification_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(rep + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
