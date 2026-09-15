//! L1 sweep — Space Needle (1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD).
//!
//! Certifie, pour toute une plage de c : (0,c) -> (c+2,1) en exactement 2c+33 pas,
//! avec balayages [1,2,4,3,3,2,1,3,1,2,c+6,c+5] et une unique visite de F (lisant 1).
//! Contrôles par c : frontières PREF (pas 22) et TOUR (pas 28+c), config finale,
//! total de pas, décomposition en balayages, visites de F, zéro halte inattendue.
//!
//! Usage : l1sweep.exe [max_c=1000000] [threads=6] [report_path]
use std::env;
use std::fs::File;
use std::io::Write;
use std::sync::mpsc;
use std::thread;
use std::time::Instant;

const A: usize = 0;
const B: usize = 1;
const C: usize = 2;
const D: usize = 3;
const E: usize = 4;
const F: usize = 5;

// [état][symbole] -> (écrit, direction, suivant). (255,..) = halte (ne doit jamais arriver).
static T: [[(u8, i32, usize); 2]; 6] = [
    [(1, 1, B), (1, -1, A)],   // A : 0->1RB ; 1->1LA
    [(1, -1, C), (0, 1, E)],   // B : 0->1LC ; 1->0RE
    [(1, -1, F), (1, -1, D)],  // C : 0->1LF ; 1->1LD
    [(0, 1, B), (0, -1, A)],   // D : 0->0RB ; 1->0LA
    [(1, 1, C), (1, 1, E)],    // E : 0->1RC ; 1->1RE
    [(255, 0, F), (0, -1, D)], // F : 0->HALT ; 1->0LD
];

fn check_c(c: u32) -> Result<u64, String> {
    let off: i32 = 8;
    let ci = c as i32;
    let size = (c as usize) + 32;
    let mut tape = vec![0u8; size];
    // init : [1,2]=00 ; [3, c+2] = 1^c ; tête 0 ; état A.
    tape[(off + 3) as usize..=(off + ci + 2) as usize].fill(1);

    let mut pos: i32 = 0;
    let mut st: usize = A;
    let mut steps: u64 = 0;
    let mut runs: Vec<u64> = Vec::with_capacity(16);
    let mut run_len: u64 = 0;
    let mut last_dir: i32 = 0;
    let mut f_visits: u64 = 0;
    let mut f_read_one: u64 = 0;
    let total = 2 * (c as u64) + 33;

    while steps < total {
        let sym = tape[(pos + off) as usize] as usize;
        let (wr, dir, next) = T[st][sym];
        if wr == 255 {
            return Err(format!("c={c}: halte inattendue au pas {steps}"));
        }
        if st == F {
            f_visits += 1;
            if sym == 1 {
                f_read_one += 1;
            }
        }
        tape[(pos + off) as usize] = wr;
        pos += dir;
        st = next;
        steps += 1;

        if dir == last_dir {
            run_len += 1;
        } else {
            if run_len > 0 {
                runs.push(run_len);
            }
            run_len = 1;
            last_dir = dir;
        }

        if steps == 22 {
            // PREF : tête -2, état D ; [−1, c+2] = 1^(c+4) ; le reste 0.
            let lo = (off - 1) as usize;
            let hi = (off + ci + 2) as usize;
            let window_ok = tape[lo..=hi].iter().all(|&b| b == 1);
            let ones: usize = tape.iter().map(|&b| b as usize).sum();
            if !(pos == -2 && st == D && window_ok && ones == c as usize + 4) {
                return Err(format!("c={c}: frontière PREF invalide (pos {pos}, st {st})"));
            }
        } else if steps == 28 + (c as u64) {
            // TOUR : tête c+4, état C ; [0, c+3] = 1^(c+4).
            let window_ok = tape[off as usize..=(off + ci + 3) as usize]
                .iter()
                .all(|&b| b == 1);
            let ones: usize = tape.iter().map(|&b| b as usize).sum();
            if !(pos == ci + 4 && st == C && window_ok && ones == c as usize + 4) {
                return Err(format!("c={c}: frontière TOUR invalide (pos {pos}, st {st})"));
            }
        }
    }

    if run_len > 0 {
        runs.push(run_len);
    }
    // FINAL : tête -1, état A ; [0, c+1] = 1^(c+2) ; [c+2, c+3] = 00 ; [c+4] = 1.
    if !(pos == -1 && st == A) {
        return Err(format!("c={c}: finale pos/état {pos}/{st}"));
    }
    let lo = off as usize;
    let hi = (off + ci + 1) as usize;
    if !tape[lo..=hi].iter().all(|&b| b == 1) {
        return Err(format!("c={c}: bloc final"));
    }
    let queue_ok = tape[(off + ci + 2) as usize] == 0
        && tape[(off + ci + 3) as usize] == 0
        && tape[(off + ci + 4) as usize] == 1
        && tape[(off - 1) as usize] == 0
        && tape[(off - 2) as usize] == 0;
    if !queue_ok {
        return Err(format!("c={c}: queue finale"));
    }
    let ones: usize = tape.iter().map(|&b| b as usize).sum();
    if ones != c as usize + 3 {
        return Err(format!("c={c}: compte de 1 final ({ones})"));
    }
    let expect: [u64; 12] = [1, 2, 4, 3, 3, 2, 1, 3, 1, 2, c as u64 + 6, c as u64 + 5];
    if runs.len() != 12 || runs.iter().zip(expect.iter()).any(|(a, b)| a != b) {
        return Err(format!("c={c}: balayages {runs:?}"));
    }
    if !(f_visits == 1 && f_read_one == 1) {
        return Err(format!("c={c}: visites de F {f_visits}/{f_read_one}"));
    }
    Ok(steps)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let max_c: u32 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(1_000_000);
    let nthreads: u32 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(6);
    let rpt = args
        .get(3)
        .cloned()
        .unwrap_or_else(|| "l1_sweep_report.txt".to_string());

    let t0 = Instant::now();
    let mut lines: Vec<String> = Vec::new();
    lines.push("=== L1 sweep (Space Needle) ===".to_string());
    lines.push("machine: 1RB1LA_1LC0RE_1LF1LD_0RB0LA_1RC1RE_---0LD".to_string());
    lines.push(format!("plage: c = 1..={max_c} ; threads = {nthreads}"));

    let chunk = std::cmp::max(1, max_c / nthreads);
    let (tx, rx) = mpsc::channel::<(u32, u32, u32, Result<(u64, u64), String>)>();
    let mut handles = Vec::new();
    for k in 0..nthreads {
        let lo = k * chunk + 1;
        let hi = if k == nthreads - 1 {
            max_c
        } else {
            std::cmp::min((k + 1) * chunk, max_c)
        };
        if lo > hi {
            continue;
        }
        let tx = tx.clone();
        handles.push(thread::spawn(move || {
            let mut steps_sum: u64 = 0;
            let mut count: u64 = 0;
            for c in lo..=hi {
                match check_c(c) {
                    Ok(s) => {
                        steps_sum += s;
                        count += 1;
                    }
                    Err(e) => {
                        let _ = tx.send((k, lo, hi, Err(e)));
                        return;
                    }
                }
            }
            let _ = tx.send((k, lo, hi, Ok((count, steps_sum))));
        }));
    }
    drop(tx);

    let mut total_count: u64 = 0;
    let mut total_steps: u64 = 0;
    let mut errors: Vec<String> = Vec::new();
    for _ in 0..nthreads {
        match rx.recv() {
            Ok((k, lo, hi, Ok((count, steps_sum)))) => {
                total_count += count;
                total_steps += steps_sum;
                lines.push(format!(
                    "  thread {k}: c={lo}..{hi} OK ({count} valeurs, {steps_sum} pas)"
                ));
            }
            Ok((k, lo, hi, Err(e))) => {
                errors.push(format!("  thread {k} (c={lo}..{hi}): {e}"));
            }
            Err(_) => break,
        }
    }
    for h in handles {
        let _ = h.join();
    }

    let elapsed = t0.elapsed().as_secs_f64();
    let verdict = if errors.is_empty() && total_count == max_c as u64 {
        "ALL PASS"
    } else {
        "FAIL"
    };
    lines.push(format!(
        "total: {total_count} valeurs c certifiées, {total_steps} pas"
    ));
    if !errors.is_empty() {
        lines.push(format!("erreurs ({}):", errors.len()));
        for e in &errors {
            lines.push(e.clone());
        }
    }
    lines.push(format!("verdict: {verdict}"));
    lines.push(format!("elapsed: {elapsed:.1}s"));
    lines.push(format!(
        "rate: {:.1} M pas/s agrégé",
        (total_steps as f64 / elapsed) / 1e6
    ));

    for c in [10_000_000u32, 100_000_000, 1_000_000_000] {
        let t = Instant::now();
        match check_c(c) {
            Ok(s) => lines.push(format!(
                "spot c={c}: PASS ({s} pas, {:.1}s)",
                t.elapsed().as_secs_f64()
            )),
            Err(e) => lines.push(format!("spot c={c}: FAIL — {e}")),
        }
    }

    let text = lines.join("\n") + "\n";
    print!("{text}");
    if let Ok(mut f) = File::create(&rpt) {
        let _ = f.write_all(text.as_bytes());
        let _ = f.sync_all();
    }
}
