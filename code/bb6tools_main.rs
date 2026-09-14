// bb6tools — verification toolkit for the "Space Needle" BB(6) machine and related runs.
// Machine format: blocks of 2 tokens per state, e.g. 1RB1LA_1LC0RE_---0LD
// Token: [01][LR][A-FZ]; "---" = undefined (halt when reached); next-state Z = halt after executing.
//
// Modes:
//   selftest                                 calibration machines (published values)
//   run <machine> <max_steps>                simulate from blank tape
//   detect <machine> <max_steps> [max_print] from blank; log every config-shape hit (state A)
//   trace <b> <c> <max_steps> [headrel]      from constructed config 1^b 00 1^c (headrel vs leftmost 1)
//   recur <n>                                Space Needle one-parameter recurrence (b0 = 6)
//   closedform                               E[ln growth] closed form + digit-count predictions

use num_bigint::BigUint;
use std::env;
use std::time::Instant;

const SN: &str = "1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Dir {
    L,
    R,
}

#[derive(Clone, Copy, Debug)]
struct Trans {
    write: u8,
    dir: Dir,
    next: Option<usize>,
}

struct Machine {
    states: Vec<[Option<Trans>; 2]>,
}

fn parse_token(tok: &str) -> Result<Option<Trans>, String> {
    if tok == "---" {
        return Ok(None);
    }
    let b = tok.as_bytes();
    if b.len() != 3 {
        return Err(format!("bad token: {tok}"));
    }
    let write = match b[0] {
        b'0' => 0u8,
        b'1' => 1u8,
        _ => return Err(format!("bad write: {tok}")),
    };
    let dir = match b[1] {
        b'L' => Dir::L,
        b'R' => Dir::R,
        _ => return Err(format!("bad dir: {tok}")),
    };
    let next = match b[2] {
        c @ b'A'..=b'F' => Some((c - b'A') as usize),
        b'Z' => None,
        _ => return Err(format!("bad next-state: {tok}")),
    };
    Ok(Some(Trans { write, dir, next }))
}

fn parse_machine(s: &str) -> Result<Machine, String> {
    let mut states = Vec::new();
    for block in s.split('_') {
        if block.len() != 6 {
            return Err(format!("block must be 6 chars: {block}"));
        }
        let t0 = parse_token(&block[0..3])?;
        let t1 = parse_token(&block[3..6])?;
        states.push([t0, t1]);
    }
    if states.is_empty() {
        return Err("empty machine".into());
    }
    let n = states.len();
    for st in &states {
        for slot in st.iter().flatten() {
            if let Some(nx) = slot.next {
                if nx >= n {
                    return Err(format!("next-state {nx} out of range (n={n})"));
                }
            }
        }
    }
    Ok(Machine { states })
}

struct Sim {
    m: Machine,
    tape: Vec<u8>,
    off: i64,
    head: i64,
    state: usize,
    steps: u64,
    ones: u64,
}

impl Sim {
    fn from_blank(m: Machine) -> Self {
        Sim {
            m,
            tape: vec![0],
            off: 0,
            head: 0,
            state: 0,
            steps: 0,
            ones: 0,
        }
    }
    fn from_tape(m: Machine, tape: Vec<u8>, head: i64) -> Self {
        let ones = tape.iter().filter(|&&c| c == 1).count() as u64;
        Sim {
            m,
            tape,
            off: 0,
            head,
            state: 0,
            steps: 0,
            ones,
        }
    }
    #[inline]
    fn cell(&self, pos: i64) -> u8 {
        let idx = pos - self.off;
        if idx < 0 || idx as usize >= self.tape.len() {
            0
        } else {
            self.tape[idx as usize]
        }
    }
    fn set_cell(&mut self, pos: i64, v: u8) {
        if pos < self.off {
            let grow = (self.off - pos) as usize;
            let mut nt = vec![0u8; grow];
            nt.extend_from_slice(&self.tape);
            self.tape = nt;
            self.off = pos;
        } else if pos >= self.off + self.tape.len() as i64 {
            self.tape.resize((pos - self.off + 1) as usize, 0);
        }
        let idx = (pos - self.off) as usize;
        let old = self.tape[idx];
        if old != v {
            if v == 1 {
                self.ones += 1;
            } else {
                self.ones -= 1;
            }
            self.tape[idx] = v;
        }
    }
    /// Execute one step. Returns true if the machine halted.
    #[inline]
    fn step(&mut self) -> bool {
        let sym = self.cell(self.head) as usize;
        match self.m.states[self.state][sym] {
            None => true,
            Some(t) => {
                self.set_cell(self.head, t.write);
                self.head += match t.dir {
                    Dir::L => -1,
                    Dir::R => 1,
                };
                self.steps += 1;
                match t.next {
                    None => true,
                    Some(s) => {
                        self.state = s;
                        false
                    }
                }
            }
        }
    }
    /// Config-shape scan: tape == 1^b 0 0 1^c (all else zeros). Returns (b, c, head - L).
    fn shape(&self) -> Option<(u64, u64, i64)> {
        let mut l: Option<i64> = None;
        let mut r: Option<i64> = None;
        for (i, &v) in self.tape.iter().enumerate() {
            if v == 1 {
                let pos = self.off + i as i64;
                if l.is_none() {
                    l = Some(pos);
                }
                r = Some(pos);
            }
        }
        let (l, r) = match (l, r) {
            (Some(a), Some(b)) => (a, b),
            _ => return None,
        };
        let span = (r - l + 1) as usize;
        if span < 4 {
            return None;
        }
        let mut b = 0usize;
        while b < span && self.cell(l + b as i64) == 1 {
            b += 1;
        }
        if b == 0 || span < b + 3 {
            return None;
        }
        if self.cell(l + b as i64) != 0 || self.cell(l + b as i64 + 1) != 0 {
            return None;
        }
        let mut c = 0usize;
        while b + 2 + c < span && self.cell(l + (b + 2 + c) as i64) == 1 {
            c += 1;
        }
        if c == 0 {
            return None;
        }
        if b + 2 + c != span {
            return None;
        }
        Some((b as u64, c as u64, self.head - l))
    }
}

fn usage() {
    println!("bb6tools modes:");
    println!("  selftest");
    println!("  run <machine> <max_steps>");
    println!("  detect <machine> <max_steps> [max_print]");
    println!("  trace <b> <c> <max_steps> [headrel]");
    println!("  recur <n>");
    println!("  chain <b> <c> <n_cp> <max_steps>");
    println!("  chainb <n_cp> <max_steps>");
    println!("  grid <bmax> <cmax> <max_steps>");
    println!("  gridr <bmin> <bmax> <cmin> <cmax> <max_steps>");
    println!("  dump <b> <c> <step_to> [headrel0]");
    println!("  seq <n>");
    println!("  recur_log <n> <outfile> [check_every]");
    println!("  closedform");
    println!("  extent <b> <c> <max_steps>");
}

fn do_run(m_str: &str, max_steps: u64) {
    let m = match parse_machine(m_str) {
        Ok(m) => m,
        Err(e) => {
            println!("parse error: {e}");
            return;
        }
    };
    let mut sim = Sim::from_blank(m);
    let t0 = Instant::now();
    while sim.steps < max_steps {
        if sim.step() {
            println!(
                "HALT steps={} ones={} elapsed={:?}",
                sim.steps,
                sim.ones,
                t0.elapsed()
            );
            return;
        }
    }
    println!(
        "LIMIT steps={} ones={} elapsed={:?}",
        sim.steps,
        sim.ones,
        t0.elapsed()
    );
}

fn do_detect(m_str: &str, max_steps: u64, max_print: usize) {
    let m = match parse_machine(m_str) {
        Ok(m) => m,
        Err(e) => {
            println!("parse error: {e}");
            return;
        }
    };
    let mut sim = Sim::from_blank(m);
    let t0 = Instant::now();
    let mut total = 0usize;
    loop {
        if sim.steps >= max_steps {
            println!(
                "LIMIT steps={} ones={} elapsed={:?}",
                sim.steps,
                sim.ones,
                t0.elapsed()
            );
            break;
        }
        if sim.state == 0 {
            if let Some((b, c, hr)) = sim.shape() {
                total += 1;
                if total <= max_print {
                    println!(
                        "hit#{} step={} b={} c={} headrel={} head={}",
                        total, sim.steps, b, c, hr, sim.head
                    );
                }
            }
        }
        if sim.step() {
            println!(
                "HALT step={} ones={} elapsed={:?}",
                sim.steps,
                sim.ones,
                t0.elapsed()
            );
            break;
        }
    }
    println!("done total_hits={total} steps={} elapsed={:?}", sim.steps, t0.elapsed());
}

fn do_trace(b: u64, c: u64, max_steps: u64, headrel0: i64) {
    let m = match parse_machine(SN) {
        Ok(m) => m,
        Err(e) => {
            println!("parse error: {e}");
            return;
        }
    };
    let mut tape: Vec<u8> = Vec::with_capacity((b + 2 + c) as usize);
    for _ in 0..b {
        tape.push(1);
    }
    tape.push(0);
    tape.push(0);
    for _ in 0..c {
        tape.push(1);
    }
    let mut sim = Sim::from_tape(m, tape, headrel0);
    let t0 = Instant::now();
    println!("START b={b} c={c} headrel0={headrel0}");
    let mut hits = 0usize;
    loop {
        if sim.steps >= max_steps {
            println!(
                "LIMIT steps={} ones={} elapsed={:?}",
                sim.steps,
                sim.ones,
                t0.elapsed()
            );
            break;
        }
        if sim.state == 0 {
            if let Some((bb, cc, hr)) = sim.shape() {
                if hits < 100 {
                    println!("hit step={} b={} c={} headrel={}", sim.steps, bb, cc, hr);
                }
                hits += 1;
            }
        }
        if sim.step() {
            println!(
                "HALT steps={} ones={} elapsed={:?}",
                sim.steps,
                sim.ones,
                t0.elapsed()
            );
            break;
        }
    }
    println!("hits_total={hits} final_steps={}", sim.steps);
}

fn do_recur(n: u64) {
    let mut b = BigUint::from(6u32);
    let mut max_v2 = 0u64;
    let t0 = Instant::now();
    for i in 1..=n {
        let tz = b.trailing_zeros().expect("b>0");
        if tz > max_v2 {
            max_v2 = tz;
        }
        let m = &b >> tz as usize;
        if m == BigUint::from(1u32) {
            println!("POWER_OF_2 (halt condition) at n={i}: b={b}");
            return;
        }
        let t = ((m - 1u32) * 3u32) >> 1usize;
        b = b + tz + t;
        if i % 1_000_000 == 0 {
            println!(
                "n={i} bits={} elapsed={:?} max_v2={max_v2}",
                b.bits(),
                t0.elapsed()
            );
        }
    }
    println!(
        "done n={} bits={} digits~{:.0} max_v2={} elapsed={:?}",
        n,
        b.bits(),
        b.bits() as f64 * 0.30102999566398119,
        max_v2,
        t0.elapsed()
    );
}

fn do_chain(b0: u64, c0: u64, n_cp: u64, max_steps: u64) {
    let m = match parse_machine(SN) {
        Ok(m) => m,
        Err(e) => {
            println!("parse error: {e}");
            return;
        }
    };
    let mut tape: Vec<u8> = Vec::with_capacity((b0 + 2 + c0) as usize);
    for _ in 0..b0 {
        tape.push(1);
    }
    tape.push(0);
    tape.push(0);
    for _ in 0..c0 {
        tape.push(1);
    }
    let mut sim = Sim::from_tape(m, tape, -1);
    println!("START b={b0} c={c0}");
    let mut cps = 0u64;
    let mut last: Option<(u64, u64, u64)> = None;
    loop {
        if sim.steps >= max_steps {
            println!("LIMIT steps={}", sim.steps);
            break;
        }
        if let Some((b, c)) = detect_config(&sim) {
            let dup = matches!(last, Some((pb, pc, ps)) if (pb, pc) == (b, c) && sim.steps == ps + 1);
            if !dup {
                if b == 0 {
                    println!("CP0 {} {}", c, sim.steps);
                } else {
                    println!("CP {} {} {}", b, c, sim.steps);
                }
                last = Some((b, c, sim.steps));
                cps += 1;
                if cps >= n_cp {
                    break;
                }
            }
        }
        if sim.step() {
            println!("HALT {}", sim.steps);
            break;
        }
    }
    println!("done cps={cps} steps={}", sim.steps);
}

fn do_extent(b0: u64, c0: u64, max_steps: u64) {
    let m = match parse_machine(SN) {
        Ok(m) => m,
        Err(e) => {
            println!("parse error: {e}");
            return;
        }
    };
    let mut tape: Vec<u8> = Vec::with_capacity((b0 + 2 + c0) as usize);
    for _ in 0..b0 {
        tape.push(1);
    }
    tape.push(0);
    tape.push(0);
    for _ in 0..c0 {
        tape.push(1);
    }
    let mut sim = Sim::from_tape(m, tape, -1);
    let mut min_pos: i64 = sim.head;
    let mut max_pos: i64 = sim.head;
    let mut cps = 0u64;
    let mut last: Option<(u64, u64, u64)> = None;
    println!("EXTENT START b={b0} c={c0}");
    loop {
        if sim.steps >= max_steps {
            println!("LIMIT steps={} min={} max={}", sim.steps, min_pos, max_pos);
            break;
        }
        if sim.head < min_pos {
            min_pos = sim.head;
        }
        if sim.head > max_pos {
            max_pos = sim.head;
        }
        if let Some((b, c)) = detect_config(&sim) {
            let dup = matches!(last, Some((pb, pc, ps)) if (pb, pc) == (b, c) && sim.steps == ps + 1);
            if !dup {
                println!("CP {} {} {} | min={} max={}", b, c, sim.steps, min_pos, max_pos);
                last = Some((b, c, sim.steps));
                cps += 1;
                if cps >= 2 {
                    break;
                }
            }
        }
        if sim.step() {
            println!("HALT {} min={} max={}", sim.steps, min_pos, max_pos);
            break;
        }
    }
    if sim.head < min_pos {
        min_pos = sim.head;
    }
    if sim.head > max_pos {
        max_pos = sim.head;
    }
    println!(
        "done cps={} steps={} min={} max={} span={}",
        cps,
        sim.steps,
        min_pos,
        max_pos,
        max_pos - min_pos
    );
}

// Detect the canonical (b,c) config of the Space Needle reduction:
//   state A, head reads 0, all cells left of head are 0, and to the right:
//   b>=1: 1^b 00 1^c 0^inf ; b=0: 00 1^c 0^inf (the two separator zeros included).
fn detect_config(sim: &Sim) -> Option<(u64, u64)> {
    if sim.state != 0 || sim.cell(sim.head) != 0 {
        return None;
    }
    if sim.cell(sim.head + 1) == 1 {
        if let Some((b, c, hr)) = sim.shape() {
            if hr == -1 && b >= 1 {
                return Some((b, c));
            }
        }
        return None;
    }
    if sim.cell(sim.head + 1) == 0 && sim.cell(sim.head + 2) == 0 && sim.cell(sim.head + 3) == 1 {
        let mut p = sim.head - 1;
        while p >= sim.off {
            if sim.cell(p) != 0 {
                return None;
            }
            p -= 1;
        }
        let mut cc = 0u64;
        let mut q = sim.head + 3;
        while sim.cell(q) == 1 {
            cc += 1;
            q += 1;
        }
        let end = sim.off + sim.tape.len() as i64;
        while q < end {
            if sim.cell(q) != 0 {
                return None;
            }
            q += 1;
        }
        if cc >= 1 {
            return Some((0, cc));
        }
    }
    None
}

fn do_chainb(n_cp: u64, max_steps: u64) {
    let m = match parse_machine(SN) {
        Ok(m) => m,
        Err(e) => {
            println!("parse error: {e}");
            return;
        }
    };
    let mut sim = Sim::from_blank(m);
    println!("STARTB blank tape");
    println!("CP0 0 0");
    let mut cps = 1u64;
    let mut last: Option<(u64, u64, u64)> = Some((0, 0, 0));
    loop {
        if sim.steps >= max_steps {
            println!("LIMIT steps={}", sim.steps);
            break;
        }
        if let Some((b, c)) = detect_config(&sim) {
            let dup = matches!(last, Some((pb, pc, ps)) if (pb, pc) == (b, c) && sim.steps == ps + 1);
            if !dup {
                if b == 0 {
                    println!("CP0 {} {}", c, sim.steps);
                } else {
                    println!("CP {} {} {}", b, c, sim.steps);
                }
                last = Some((b, c, sim.steps));
                cps += 1;
                if cps >= n_cp {
                    break;
                }
            }
        }
        if sim.step() {
            println!("HALT {}", sim.steps);
            break;
        }
    }
    println!("done cps={cps} steps={}", sim.steps);
}

fn do_grid(bmax: u64, cmax: u64, max_steps: u64) {
    let mut hits = 0u64;
    let mut halts = 0u64;
    let mut timeouts = 0u64;
    for b in 0..=bmax {
        for c in 0..=cmax {
            let m = match parse_machine(SN) {
                Ok(m) => m,
                Err(e) => {
                    println!("parse error: {e}");
                    return;
                }
            };
            let mut tape: Vec<u8> = Vec::new();
            if b == 0 {
                tape.push(0);
                tape.push(0);
                for _ in 0..c {
                    tape.push(1);
                }
            } else {
                for _ in 0..b {
                    tape.push(1);
                }
                tape.push(0);
                tape.push(0);
                for _ in 0..c {
                    tape.push(1);
                }
            }
            let mut sim = Sim::from_tape(m, tape, -1);
            let mut done = false;
            while sim.steps < max_steps {
                if let Some((bb, cc)) = detect_config(&sim) {
                    if (bb, cc) != (b, c) {
                        println!("CASE {b} {c} HIT {bb} {cc} {}", sim.steps);
                        hits += 1;
                        done = true;
                        break;
                    }
                }
                if sim.step() {
                    println!("CASE {b} {c} HALT {}", sim.steps);
                    halts += 1;
                    done = true;
                    break;
                }
            }
            if !done {
                println!("CASE {b} {c} TIMEOUT {}", sim.steps);
                timeouts += 1;
            }
        }
    }
    println!("GRID done hits={hits} halts={halts} timeouts={timeouts}");
}

fn do_gridr(bmin: u64, bmax: u64, cmin: u64, cmax: u64, max_steps: u64) {
    let mut hits = 0u64;
    let mut halts = 0u64;
    let mut timeouts = 0u64;
    for b in bmin..=bmax {
        for c in cmin..=cmax {
            let m = match parse_machine(SN) {
                Ok(m) => m,
                Err(e) => {
                    println!("parse error: {e}");
                    return;
                }
            };
            let mut tape: Vec<u8> = Vec::new();
            if b == 0 {
                tape.push(0);
                tape.push(0);
                for _ in 0..c {
                    tape.push(1);
                }
            } else {
                for _ in 0..b {
                    tape.push(1);
                }
                tape.push(0);
                tape.push(0);
                for _ in 0..c {
                    tape.push(1);
                }
            }
            let mut sim = Sim::from_tape(m, tape, -1);
            let mut done = false;
            while sim.steps < max_steps {
                if let Some((bb, cc)) = detect_config(&sim) {
                    if (bb, cc) != (b, c) {
                        println!("CASE {b} {c} HIT {bb} {cc} {}", sim.steps);
                        hits += 1;
                        done = true;
                        break;
                    }
                }
                if sim.step() {
                    println!("CASE {b} {c} HALT {}", sim.steps);
                    halts += 1;
                    done = true;
                    break;
                }
            }
            if !done {
                println!("CASE {b} {c} TIMEOUT {}", sim.steps);
                timeouts += 1;
            }
        }
    }
    println!("GRIDR done hits={hits} halts={halts} timeouts={timeouts}");
}

fn do_dump(b: u64, c: u64, headrel0: i64, step_to: u64) {
    let m = match parse_machine(SN) {
        Ok(m) => m,
        Err(e) => {
            println!("parse error: {e}");
            return;
        }
    };
    let mut tape: Vec<u8> = Vec::new();
    for _ in 0..b {
        tape.push(1);
    }
    tape.push(0);
    tape.push(0);
    for _ in 0..c {
        tape.push(1);
    }
    let mut sim = Sim::from_tape(m, tape, headrel0);
    while sim.steps < step_to {
        let lo = sim.head.min(sim.off) - 2;
        let hi = (sim.off + sim.tape.len() as i64 - 1).max(sim.head) + 2;
        let mut s = String::new();
        for p in lo..=hi {
            let ch = if sim.cell(p) == 1 { '1' } else { '0' };
            if p == sim.head {
                s.push('[');
                s.push(ch);
                s.push(']');
            } else {
                s.push(ch);
            }
        }
        let st = (b'A' + sim.state as u8) as char;
        println!(
            "step={} state={} read={} head={} tape={}",
            sim.steps,
            st,
            sim.cell(sim.head),
            sim.head,
            s
        );
        if sim.step() {
            println!("HALT at step={}", sim.steps);
            break;
        }
    }
}

fn do_seq(n: u64) {
    let mut b = BigUint::from(6u32);
    println!("{b}");
    for _ in 1..n {
        let tz = b.trailing_zeros().expect("b>0");
        let m = &b >> tz as usize;
        if m == BigUint::from(1u32) {
            println!("HALT_CONDITION_MET");
            return;
        }
        let t = ((m - 1u32) * 3u32) >> 1usize;
        b = b + tz + t;
        println!("{b}");
    }
}

fn do_recur_log(n: u64, outfile: &str, check_every: u64) {
    use std::fs::OpenOptions;
    use std::io::Write;
    let mut b = BigUint::from(6u32);
    let mut max_v2 = 0u64;
    let mut hist = [0u64; 64];
    let mut f = match OpenOptions::new().create(true).append(true).open(outfile) {
        Ok(f) => f,
        Err(e) => {
            println!("cannot open {outfile}: {e}");
            return;
        }
    };
    let t0 = Instant::now();
    let _ = writeln!(
        f,
        "# term,bits,digits,max_v2,h0_8,h9_16,h17_24,h25_40,fnv64,elapsed_s"
    );
    let mut last_hash = 0u64;
    for i in 1..=n {
        let tz = b.trailing_zeros().expect("b>0");
        let tzb = if tz < 63 { tz as usize } else { 63 };
        hist[tzb] += 1;
        if tz > max_v2 {
            max_v2 = tz;
            println!("V2RECORD v2={tz} at n={i} bits={}", b.bits());
        }
        let m = &b >> tz as usize;
        if m == BigUint::from(1u32) {
            let _ = writeln!(f, "# HALT_CONDITION_MET term={i} b={b}");
            let _ = f.flush();
            println!("HALT_CONDITION_MET at term {i}");
            return;
        }
        let t = ((m - 1u32) * 3u32) >> 1usize;
        b = b + tz + t;
        if i % check_every == 0 {
            // log10 estimate: exact decimal conversion is too slow at multi-million digits
            let digits = (b.bits() as f64 * 0.30102999566398119521) as u64 + 1;
            let mut hsh = 0xcbf29ce484222325u64;
            for w in b.to_u64_digits() {
                hsh ^= w;
                hsh = hsh.wrapping_mul(0x100000001b3);
            }
            last_hash = hsh;
            let h0: u64 = hist[0..9].iter().sum();
            let h1: u64 = hist[9..17].iter().sum();
            let h2: u64 = hist[17..25].iter().sum();
            let h3: u64 = hist[25..].iter().sum();
            let el = t0.elapsed().as_secs();
            let _ = writeln!(
                f,
                "{i},{},{},{},{},{},{},{},{:016x},{}",
                b.bits(),
                digits,
                max_v2,
                h0,
                h1,
                h2,
                h3,
                hsh,
                el
            );
            let _ = f.flush();
            println!("checkpoint i={i} bits={} max_v2={max_v2} t={el}s", b.bits());
        }
    }
    // the loop checked terms 0..n-1 (v2 of b_i for i in 0..n-1); check final term explicitly
    {
        let tz = b.trailing_zeros();
        if let Some(t) = tz {
            if (&b >> t as usize) == BigUint::from(1u32) {
                println!("HALT_CONDITION_MET at final term n={n}: b is a power of 2");
            }
        }
    }
    let _ = f.flush();
    println!(
        "done n={n} last_hash={:016x} elapsed={:?}",
        last_hash,
        t0.elapsed()
    );
}

fn do_closedform() {
    let mut s = 0.0f64;
    for k in 0..200usize {
        let w = 2.0f64.powi(-((k + 1) as i32));
        let x = 3.0f64 * w;
        s += w * (1.0 + x).ln();
    }
    println!("E[ln G] closed form = {s:.9}");
    println!("published           = 0.652355");
    println!("digits(1.7e7) = {:.0}", 1.7e7 * s / 10.0f64.ln());
    println!(
        "digits(1.7e7, c=0.652355) = {:.0}",
        1.7e7 * 0.652355 / 10.0f64.ln()
    );
}

fn selftest() {
    let cases: [(&str, u64, u64); 4] = [
        ("1RB1LB_1LA1RZ", 6, 4),
        ("1RB1RZ_1LB0RC_1LC1LA", 21, 5),
        ("1RB1LB_1LA0LC_1RZ1LD_1RD0RA", 107, 13),
        ("1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA", 47_176_870, 4098),
    ];
    for (ms, exp_steps, exp_ones) in cases {
        match parse_machine(ms) {
            Ok(m) => {
                let mut sim = Sim::from_blank(m);
                let t0 = Instant::now();
                let mut halted = false;
                while sim.steps < exp_steps + 2 {
                    if sim.step() {
                        halted = true;
                        break;
                    }
                }
                let el = t0.elapsed();
                let ok = halted && sim.steps == exp_steps && sim.ones == exp_ones;
                println!(
                    "[{}] {ms} expected S={exp_steps} ones={exp_ones} | got S={} ones={} halted={halted} in {el:?}",
                    if ok { "PASS" } else { "FAIL" },
                    sim.steps,
                    sim.ones
                );
            }
            Err(e) => println!("[ERR] {ms}: {e}"),
        }
    }
    match parse_machine(SN) {
        Ok(m) => {
            let mut sim = Sim::from_blank(m);
            let t0 = Instant::now();
            let mut halted = false;
            while sim.steps < 10_000_000 {
                if sim.step() {
                    halted = true;
                    break;
                }
            }
            println!(
                "[SN blank] halted={halted} steps={} ones={} in {:?}",
                sim.steps,
                sim.ones,
                t0.elapsed()
            );
        }
        Err(e) => println!("[ERR] SN: {e}"),
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        usage();
        return;
    }
    match args[1].as_str() {
        "selftest" => selftest(),
        "run" => {
            let m = args.get(2).cloned().unwrap_or_default();
            let max: u64 = args
                .get(3)
                .and_then(|s| s.parse().ok())
                .unwrap_or(1_000_000);
            do_run(&m, max);
        }
        "detect" => {
            let m = args.get(2).cloned().unwrap_or_default();
            let max: u64 = args
                .get(3)
                .and_then(|s| s.parse().ok())
                .unwrap_or(10_000_000);
            let hits: usize = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(60);
            do_detect(&m, max, hits);
        }
        "trace" => {
            let b: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(0);
            let c: u64 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(0);
            let max: u64 = args
                .get(4)
                .and_then(|s| s.parse().ok())
                .unwrap_or(2_000_000);
            let hr: i64 = args.get(5).and_then(|s| s.parse().ok()).unwrap_or(-1);
            do_trace(b, c, max, hr);
        }
        "recur" => {
            let n: u64 = args
                .get(2)
                .and_then(|s| s.parse().ok())
                .unwrap_or(1_000_000);
            do_recur(n);
        }
        "seq" => {
            let n: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(10);
            do_seq(n);
        }
        "recur_log" => {
            let n: u64 = args
                .get(2)
                .and_then(|s| s.parse().ok())
                .unwrap_or(1_000_000);
            let out = args.get(3).cloned().unwrap_or("traj.csv".to_string());
            let ce: u64 = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(100_000);
            do_recur_log(n, &out, ce);
        }
        "chain" => {
            let b: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(3);
            let c: u64 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(1);
            let n: u64 = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(16);
            let mx: u64 = args
                .get(5)
                .and_then(|s| s.parse().ok())
                .unwrap_or(1_000_000_000);
            do_chain(b, c, n, mx);
        }
        "dump" => {
            let b: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(3);
            let c: u64 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(1);
            let st: u64 = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(130);
            let hr: i64 = args.get(5).and_then(|s| s.parse().ok()).unwrap_or(-1);
            do_dump(b, c, hr, st);
        }
        "chainb" => {
            let n: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(12);
            let mx: u64 = args
                .get(3)
                .and_then(|s| s.parse().ok())
                .unwrap_or(1_000_000_000);
            do_chainb(n, mx);
        }
        "grid" => {
            let bmax: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(63);
            let cmax: u64 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(31);
            let mx: u64 = args
                .get(4)
                .and_then(|s| s.parse().ok())
                .unwrap_or(2_000_000);
            do_grid(bmax, cmax, mx);
        }
        "gridr" => {
            let bmin: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(0);
            let bmax: u64 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(0);
            let cmin: u64 = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(0);
            let cmax: u64 = args.get(5).and_then(|s| s.parse().ok()).unwrap_or(0);
            let mx: u64 = args
                .get(6)
                .and_then(|s| s.parse().ok())
                .unwrap_or(2_000_000);
            do_gridr(bmin, bmax, cmin, cmax, mx);
        }
        "closedform" => do_closedform(),
        "extent" => {
            let b: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(3);
            let c: u64 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(1);
            let mx: u64 = args
                .get(4)
                .and_then(|s| s.parse().ok())
                .unwrap_or(1_000_000_000);
            do_extent(b, c, mx);
        }
        _ => usage(),
    }
}
