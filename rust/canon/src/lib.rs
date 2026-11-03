//! Exact port of srg.canon: same refinement, branch order, automorphisms,
//! backjumps, leaf budget, and full packed certificate. No external crates.
use std::collections::BTreeMap;
use std::panic::{catch_unwind, AssertUnwindSafe};

struct Graph {
    rows: usize,
    adj: Vec<Vec<usize>>,
    matrix: Vec<Vec<u8>>,
    weights: Vec<usize>,
    color: Vec<usize>,
}

impl Graph {
    fn build(data: &[u8], rows: usize, columns: usize) -> Result<Self, ()> {
        if rows > columns || rows.checked_mul(columns) != Some(data.len()) {
            return Err(());
        }
        for i in 0..rows {
            for j in 0..columns {
                if data[i * columns + j] > 1 {
                    return Err(());
                }
                if j < rows && data[i * columns + j] != data[j * columns + i] {
                    return Err(());
                }
            }
        }
        let mut classes = BTreeMap::<Vec<u8>, usize>::new();
        for j in rows..columns {
            let column = (0..rows).map(|i| data[i * columns + j]).collect();
            *classes.entry(column).or_default() += 1;
        }
        let n = rows + classes.len();
        let mut adj = vec![Vec::new(); n];
        let mut matrix = vec![vec![0; n]; n];
        for i in 0..rows {
            for j in 0..rows {
                if data[i * columns + j] != 0 {
                    adj[i].push(j);
                    matrix[i][j] = 1;
                }
            }
        }
        let mut weights = Vec::new();
        let mut color = vec![0; rows];
        for (c, (column, weight)) in classes.into_iter().enumerate() {
            weights.push(weight);
            color.push(1 + weight);
            for (i, value) in column.into_iter().enumerate() {
                if value != 0 {
                    adj[i].push(rows + c);
                    adj[rows + c].push(i);
                    matrix[i][rows + c] = 1;
                    matrix[rows + c][i] = 1;
                }
            }
        }
        Ok(Self {
            rows,
            adj,
            matrix,
            weights,
            color,
        })
    }

    fn certificate(&self, order: &[usize]) -> Vec<u8> {
        let mut bits = Vec::new();
        let (built, classes) = order.split_at(self.rows);
        for &c in classes {
            let weight = self.weights[c - self.rows];
            bits.extend(std::iter::repeat(1).take(weight - 1));
            bits.push(0);
        }
        for (i, &a) in built.iter().enumerate() {
            for &b in &built[i + 1..] {
                bits.push(self.matrix[a][b]);
            }
        }
        for &c in classes {
            for &b in built {
                bits.push(self.matrix[c][b]);
            }
        }
        let mut packed = vec![0; (bits.len() + 7) / 8];
        for (i, bit) in bits.into_iter().enumerate() {
            packed[i / 8] |= bit << (7 - i % 8);
        }
        packed
    }
}

fn refine(adj: &[Vec<usize>], mut color: Vec<usize>) -> Vec<usize> {
    loop {
        let signatures: Vec<_> = adj
            .iter()
            .enumerate()
            .map(|(i, neighbors)| {
                let mut colors: Vec<_> = neighbors.iter().map(|&j| color[j]).collect();
                colors.sort_unstable();
                (color[i], colors)
            })
            .collect();
        let mut ranks = signatures.clone();
        ranks.sort_unstable();
        ranks.dedup();
        let new: Vec<_> = signatures
            .iter()
            .map(|s| ranks.binary_search(s).unwrap())
            .collect();
        let mut old = color;
        old.sort_unstable();
        old.dedup();
        if ranks.len() == old.len() {
            return new;
        }
        color = new;
    }
}

fn common_prefix(a: &[usize], b: &[usize]) -> usize {
    a.iter().zip(b).take_while(|(x, y)| x == y).count()
}

fn find(parent: &mut [usize], mut x: usize) -> usize {
    while parent[x] != x {
        parent[x] = parent[parent[x]];
        x = parent[x];
    }
    x
}

#[derive(Debug)]
enum SearchError {
    Budget,
    Backjump(usize),
}

struct Search<'a> {
    graph: &'a Graph,
    budget: i64,
    first: Option<(Vec<u8>, Vec<usize>, Vec<usize>)>,
    best: Option<(Vec<u8>, Vec<usize>, Vec<usize>)>,
    generators: Vec<Vec<usize>>,
}

impl<'a> Search<'a> {
    fn automorphism(&mut self, old: &[usize], new: &[usize]) {
        let mut g = vec![0; old.len()];
        for (&a, &b) in old.iter().zip(new) {
            g[a] = b;
        }
        self.generators.push(g);
    }

    fn orbit_representatives(&self, prefix: &[usize], cell: &[usize]) -> Vec<usize> {
        let n = self.graph.adj.len();
        let mut parent: Vec<_> = (0..n).collect();
        let mut members = vec![false; n];
        for &x in cell {
            members[x] = true;
        }
        for g in &self.generators {
            if prefix.iter().any(|&x| g[x] != x) {
                continue;
            }
            for &x in cell {
                let y = g[x];
                if members[y] {
                    let a = find(&mut parent, x);
                    let b = find(&mut parent, y);
                    parent[a] = b;
                }
            }
        }
        for &x in cell {
            let _ = find(&mut parent, x);
        }
        parent
    }

    fn run(&mut self, color: Vec<usize>, prefix: &mut Vec<usize>) -> Result<(), SearchError> {
        let color = refine(&self.graph.adj, color);
        let mut cells = BTreeMap::<usize, Vec<usize>>::new();
        for (i, &c) in color.iter().enumerate() {
            cells.entry(c).or_default().push(i);
        }
        let mut target: Option<(usize, Vec<usize>)> = None;
        for (c, cell) in cells {
            if cell.len() > 1 && target.as_ref().map_or(true, |(_, t)| cell.len() < t.len()) {
                target = Some((c, cell));
            }
        }
        let Some((c, cell)) = target else {
            if self.budget <= 0 {
                return Err(SearchError::Budget);
            }
            self.budget -= 1;
            let mut order: Vec<_> = (0..color.len()).collect();
            order.sort_unstable_by_key(|&i| color[i]);
            let cert = self.graph.certificate(&order);
            if let Some((first_cert, first_order, first_path)) = &self.first {
                if cert == *first_cert {
                    let old = first_order.clone();
                    let depth = common_prefix(prefix, first_path);
                    self.automorphism(&old, &order);
                    return Err(SearchError::Backjump(depth));
                }
            } else {
                self.first = Some((cert.clone(), order.clone(), prefix.clone()));
            }
            if self.best.as_ref().map_or(true, |(best, _, _)| cert < *best) {
                self.best = Some((cert, order, prefix.clone()));
            } else if let Some((best_cert, best_order, best_path)) = &self.best {
                if cert == *best_cert {
                    let old = best_order.clone();
                    let depth = common_prefix(prefix, best_path);
                    self.automorphism(&old, &order);
                    return Err(SearchError::Backjump(depth));
                }
            }
            return Ok(());
        };
        let mut tried = Vec::new();
        for &x in &cell {
            if !tried.is_empty() && !self.generators.is_empty() {
                let mut representatives = self.orbit_representatives(prefix, &cell);
                let representative = find(&mut representatives, x);
                if tried
                    .iter()
                    .any(|&t| find(&mut representatives, t) == representative)
                {
                    continue;
                }
            }
            let next: Vec<_> = color
                .iter()
                .enumerate()
                .map(|(i, &ci)| 2 * ci + usize::from(ci == c && i != x))
                .collect();
            prefix.push(x);
            let result = self.run(next, prefix);
            prefix.pop();
            match result {
                Err(SearchError::Backjump(depth)) if depth == prefix.len() => (),
                Err(error) => return Err(error),
                Ok(()) => (),
            }
            tried.push(x);
        }
        Ok(())
    }
}

fn canonical(data: &[u8], rows: usize, columns: usize, budget: i64) -> Result<Option<Vec<u8>>, ()> {
    let graph = Graph::build(data, rows, columns)?;
    let mut search = Search {
        graph: &graph,
        budget,
        first: None,
        best: None,
        generators: Vec::new(),
    };
    match search.run(graph.color.clone(), &mut Vec::new()) {
        Err(SearchError::Budget) => Ok(None),
        Err(SearchError::Backjump(_)) => Err(()),
        Ok(()) => Ok(search.best.map(|(certificate, _, _)| certificate)),
    }
}

#[no_mangle]
pub extern "C" fn srg_canon_abi_version() -> u32 {
    1
}

/// Status: 0 = key, 1 = leaf budget exceeded, -1 = invalid input,
/// -2 = insufficient output buffer, -3 = internal panic.
///
/// # Safety
/// Input must point to `length` readable bytes; output must point to `capacity`
/// writable bytes and output_length to one writable usize. They must not overlap
/// or be mutated concurrently. All buffers remain owned by the caller.
#[no_mangle]
pub unsafe extern "C" fn srg_canonical_key(
    input: *const u8,
    length: usize,
    rows: usize,
    columns: usize,
    budget: i64,
    output: *mut u8,
    capacity: usize,
    output_length: *mut usize,
) -> i32 {
    if input.is_null() || output.is_null() || output_length.is_null() {
        return -1;
    }
    *output_length = 0;
    let result = catch_unwind(AssertUnwindSafe(|| {
        let data = std::slice::from_raw_parts(input, length);
        match canonical(data, rows, columns, budget) {
            Ok(Some(key)) => {
                if key.len() > capacity {
                    return -2;
                }
                std::ptr::copy_nonoverlapping(key.as_ptr(), output, key.len());
                *output_length = key.len();
                0
            }
            Ok(None) => 1,
            Err(()) => -1,
        }
    }));
    result.unwrap_or(-3)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn seed_key_matches_python_fixture() {
        let data: Vec<u8> = [
            "01111111111111100000000000000",
            "10111111000000011111110000000",
        ]
        .iter()
        .flat_map(|s| s.bytes().map(|b| b - b'0'))
        .collect();
        assert_eq!(
            canonical(&data, 2, 29, 5000),
            Ok(Some(vec![0xfb, 0xf7, 0xef, 0xdc, 0x90]))
        );
    }

    #[test]
    fn budget_and_validation() {
        let triangle = [0, 1, 1, 1, 0, 1, 1, 1, 0];
        assert_eq!(canonical(&triangle, 3, 3, 0), Ok(None));
        assert_eq!(canonical(&triangle, 3, 3, 5000), Ok(Some(vec![0xe0])));
        assert!(canonical(&[0, 2, 2, 0], 2, 2, 5000).is_err());
        assert!(canonical(&[0, 1, 0, 0], 2, 2, 5000).is_err());
    }

    #[test]
    fn ffi_reports_small_buffers_and_nulls() {
        let input = [0, 1, 1, 0];
        let mut output = [0u8; 1];
        let mut length = 99;
        unsafe {
            assert_eq!(
                srg_canonical_key(
                    input.as_ptr(),
                    4,
                    2,
                    2,
                    5000,
                    output.as_mut_ptr(),
                    0,
                    &mut length
                ),
                -2
            );
            assert_eq!(length, 0);
            assert_eq!(
                srg_canonical_key(
                    std::ptr::null(),
                    4,
                    2,
                    2,
                    5000,
                    output.as_mut_ptr(),
                    1,
                    &mut length
                ),
                -1
            );
        }
    }
}
