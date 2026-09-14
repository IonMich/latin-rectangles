# Benchmarking Algorithm Scaling

For a compact, correctness-gated benchmark with raw samples and machine metadata,
use the [verification runner](../benchmarks/verify_and_benchmark.py):
`uv run --frozen benchmarks/verify_and_benchmark.py`.
It runs the test suite before benchmarking and writes samples, exact-result
hashes, input parameters and machine metadata to the ignored local file
`benchmark_results/verification.json`. Any failed test or unequal answer stops
the run before that file is replaced. The scaling tools below provide broader
workload exploration.

## Measured method comparisons

The following historical measurements were recorded on 7 September 2026 with
an Apple M2 (8 logical CPUs, 16 GiB RAM), macOS 26.6.2, CPython 3.12.9 and
uv 0.8.2. Times are medians of seven samples in milliseconds. These are
selected workloads from the verification runner; no new benchmark run is
claimed here.

| Workload | Cache | Baseline | Candidate | Baseline ms | Candidate ms |
|---|---|---|---|---:|---:|
| Two 256-cycles, n=512 | cold | Rook | Touchard | 12.9962 | 5.2775 |
| Cycles [3,5] plus 125 transpositions, n=258 | warm | Rook | Touchard | 3.9250 | 0.7011 |
| Same n=258 cycle type | cold | Rook | Touchard | 3.9824 | 28.8683 |
| Polynomial product: 1024×1024 signed 8-bit coefficients | cold | Schoolbook | NTT/CRT | 61.9447 | 13.4221 |

Touchard is 2.46× faster for the cold two-cycle input and 5.60× faster for the
warm mixed input, but slower for that mixed input with cold caches. The 4.62×
NTT/CRT gain is for the synthetic polynomial product. All sampled Latin-counting
rook products used schoolbook fallback, so this is not an end-to-end
Latin-rectangle speedup.

Cold samples clear all four library caches. Warm samples clear them and call
the same method once before timing. Method order rotates across repetitions;
input setup, reference calculations, equality checks and hashing are outside
the timer. This was one host and process, with GC enabled, no CPU pinning or
frequency control, and no memory measurement. Rerun the command above to
generate fresh samples for your workload; raw run records remain local.

## Computational costs and limits

Let n be the number of columns and c the number of permutation cycles. The
operation counts below describe algorithm stages; Python integer operations
become more expensive as coefficients and answers grow.

| Stage | Cost and practical limit |
|---|---|
| Schoolbook combination of cycle polynomials | O(n²) coefficient additions/multiplications in total. Generating the component coefficients and applying inclusion–exclusion also require integer arithmetic. |
| Touchard subset-sum calculation | O(cn) loop iterations and O(n) count entries, followed by accumulation over reachable sums. Computing uncached one-cycle values can dominate the total time. |
| One NTT polynomial product | O(qN log N) modular operations for transforms of length N over q primes, plus prime/root setup and CRT reconstruction. Growing coefficient bounds require more primes; the implementation may fall back to schoolbook. |
| General k-row counting | Exponential in the largest forbidden component. Adding several rows also enumerates valid intermediate rows and is intended for small-n exact work. |

The cold/warm comparison explains why one speedup or fitted exponent cannot
describe every method and cycle type. The
[historical scaling report](../COMPLEXITY_ANALYSIS_REPORT.md) retains the 2025
observations with their measurement scope and units; empirical fits do not
establish asymptotic bounds. See [the method derivations](methods.md) for the
mathematical structure behind these algorithms.

## Scaling benchmark tools

This repository includes a CSV-first benchmark workflow for the specialized
`2 x n -> 3 x n` methods:

- `touchard`: `count_extensions_from_cycle_type`, using Touchard's formula on
  cycle lengths.
- `cycle_auto`: the public cycle-structure router, which chooses Touchard or
  rook schoolbook depending on cache state and cycle-type density.
- `rook_schoolbook`: `count_extensions_from_derangement(..., use_fft=False)`, using exact
  schoolbook polynomial products.
- `rook_ntt`: `count_extensions_from_derangement(..., use_fft=True)`, using exact NTT/CRT
  convolution when the transform path is beneficial and falling back to
  schoolbook multiplication otherwise.

The benchmark runner checks that every selected method returns the same integer
for every cycle type before it records timing data.

## Why There Are Two Benchmark Axes

There are two different scaling questions.

Fixed cycle families can and should go to large `n`, including values in the
thousands. Examples are one `n`-cycle, all transpositions, mostly 8-cycles, or a
deterministic mixed cycle type. These measure how each algorithm scales as the
problem size grows along a controlled structural family. The family list also
includes `two_equal_cycles` and `four_equal_cycles`, which are important for
probing whether the exact NTT/CRT path helps on large balanced polynomial
products.

Exhaustive fixed-`n` cycle-type benchmarks answer a different question: for one
chosen `n`, evaluate every derangement cycle type. These are very informative
for structural sensitivity, but they cannot go to `n` in the thousands because
the number of inputs is the number of partitions of `n` with no `1` parts:

```text
T(n) = p(n) - p(n - 1)
```

Some reference values:

| n | all derangement cycle types |
|---:|---:|
| 20 | 137 |
| 30 | 1,039 |
| 40 | 6,153 |
| 50 | 30,701 |
| 60 | 134,647 |
| 70 | 533,623 |
| 80 | 1,947,826 |
| 100 | 21,339,417 |

So `n=30` or `n=40` is not a mathematical ceiling. It is just a practical
default for exhaustive all-cycle-type runs. For high-`n` scaling, use fixed
families.

## Run Benchmarks

Quick smoke run:

```console
uv run benchmarks/benchmark_cycle_type_methods.py \
  --suite both \
  --family-ns 64,128 \
  --all-cycle-ns 12 \
  --repeats 1 \
  --output-dir benchmark_results/scaling_smoke
```

High-`n` fixed-family run:

```console
uv run benchmarks/benchmark_cycle_type_methods.py \
  --suite families \
  --family-ns 128,256,512,1024,2048,4096 \
  --methods rook_schoolbook \
  --repeats 3 \
  --output-dir benchmark_results/scaling_high_n_rook
```

Use guarded runs when comparing all methods at high `n`:

```console
uv run benchmarks/benchmark_cycle_type_methods.py \
  --suite families \
  --family-ns 128,256,512,1024,2048 \
  --methods cycle_auto,touchard,rook_schoolbook,rook_ntt \
  --repeats 3 \
  --timeout-seconds 120 \
  --progress method \
  --output-dir benchmark_results/scaling_high_n_all_methods
```

The timeout is per method per cycle type. A timeout row is written to the CSV,
but that method is excluded from equality checks for that one case because no
answer was returned.

Exhaustive all-cycle-type run for selected fixed `n`:

```console
uv run benchmarks/benchmark_cycle_type_methods.py \
  --suite all-cycle-types \
  --all-cycle-ns 30,40,50 \
  --methods cycle_auto,touchard,rook_schoolbook,rook_ntt \
  --repeats 3 \
  --max-cycle-types 50000 \
  --output-dir benchmark_results/scaling_all_types
```

The exhaustive suite has a safety guard. If a requested `n` has more cycle
types than `--max-cycle-types`, the script fails before doing work. Raise the
guard, or pass `--allow-large-all-cycle-types`, only when the large run is
intentional.

## Generate Plots

Plots are generated from CSVs, not directly from live benchmark code:

```console
uv run benchmarks/plot_cycle_type_methods.py \
  --input-dir benchmark_results/scaling_high_n \
  --output-dir benchmark_plots/scaling_high_n
```

The plotter writes separate SVG files. It does not create subplots and it does
not use relative speedup plots.

For fixed cycle families it writes:

- `runtime_family_<family>.svg`
- `memory_family_<family>.svg`

For exhaustive all-cycle-type data it writes, for each benchmarked `n`:

- `runtime_all_cycle_types_n_<n>.svg`
- `runtime_vs_cycle_count_n_<n>.svg`
- `runtime_vs_largest_cycle_n_<n>.svg`

It also writes aggregate exhaustive plots:

- `runtime_total_all_cycle_types.svg`
- `runtime_worst_all_cycle_types.svg`
- `memory_worst_all_cycle_types.svg`

## CSV Fields

The benchmark CSVs include:

- `suite`, `family`, `n`, and `cycle_type`
- structural columns: `cycle_type_index`, `cycle_count`, `largest_cycle`
- `method` and `repeats`
- `status` and `error`
- `time_seconds_median` and `time_seconds_min`
- `peak_memory_mb`
- `result_bits` and `result_mod_1000000007`

The full extension count is not written to CSV because it can have thousands of
digits. Equality is still checked in memory before rows are written.

## Diagnose Surprising Scaling

Use `benchmarks/diagnose_scaling.py` when a benchmark run looks stuck or when a
method behaves contrary to expectation. It writes three CSV files:

- `touchard_diagnostics.csv`
- `rook_strategy_summary.csv`
- `rook_multiply_steps.csv`

Example:

```console
uv run benchmarks/diagnose_scaling.py \
  --ns 2048 \
  --families mixed_ladder,mostly_16_cycles,two_equal_cycles,four_equal_cycles \
  --touchard-modes cold,warm \
  --rook-strategies schoolbook_sequential,ntt_sequential,ntt_tree \
  --timeout-seconds 10 \
  --output-dir benchmark_results/diagnostics_probe
```

The Touchard diagnostics report:

- number of reachable subset sums
- number of distinct `M_s` one-cycle values requested
- cache hits and misses for `M_s`
- subset-DP time and accumulation time

The rook diagnostics report:

- one row per polynomial multiplication
- input lengths and length ratio
- whether the NTT path predicted schoolbook fallback or transform use
- NTT transform size
- coefficient-bound bit length
- number of CRT prime convolutions actually used

### Initial `n=2048` Findings

These earlier diagnostic observations predate the dated comparison above.
Their tables do not record the full host and sampling protocol, so use them
to understand the routing decisions rather than to compare timings across runs.

The first diagnostic probe explains why the advanced paths did not dominate on
`mixed_ladder`.

For `mixed_ladder` at `n=2048`, the cycle lengths have gcd `1` and the subset
sums are essentially dense: 2047 reachable subset sums. A cold Touchard run
therefore asks for many high-index one-cycle values `M_s`. Individual cold
`M_s` computations become nontrivial at this scale:

| s | cold `M_s` time |
|---:|---:|
| 512 | about 0.009 s |
| 1024 | about 0.074 s |
| 1536 | about 0.245 s |
| 2048 | about 0.547 s |

So Touchard is best interpreted as a warm-cache or repeated-query method for
large dense cycle-type families. It can still be excellent when the reachable
`M_s` set is small, e.g. balanced large cycles.

The exact NTT/CRT path also has a clear bottleneck: coefficient sizes force many
CRT primes. In the same probe, a balanced product of two degree-1024 cycle
polynomials used 92 modular convolutions. That made `ntt_sequential` slower than
schoolbook even on `two_equal_cycles` at `n=2048`:

| family | strategy | observed status |
|---|---|---|
| `mixed_ladder` | `schoolbook_sequential` | about 1.2 s |
| `mixed_ladder` | `ntt_sequential` | timed out at 10 s |
| `mixed_ladder` | `ntt_tree` | timed out at 10 s |
| `two_equal_cycles` | `schoolbook_sequential` | about 3.8 s |
| `two_equal_cycles` | `ntt_sequential` | about 9.2 s, 92 CRT prime convolutions |
| `four_equal_cycles` | `schoolbook_sequential` | about 4.4 s |
| `four_equal_cycles` | `ntt_sequential` | timed out at 10 s, over 200 CRT prime convolutions |

This led to two routing changes:

- `multiply_polynomials_fft` now estimates the number of CRT primes needed and
  falls back to schoolbook multiplication when that estimate is above its prime
  budget.
- `count_extensions_from_cycle_type(..., method="auto")` uses Touchard when
  the needed `M_s` values are already cached or few, but routes cold dense
  high-`n` cycle types to the rook-polynomial product.

The issue was not just unbalanced polynomial lengths; the CRT reconstruction
burden is large for the integer coefficient sizes that occur in this problem.

After the CRT-prime guard, the same `mixed_ladder, n=2048` diagnostic routes
`ntt_sequential` entirely through schoolbook fallback:

| strategy | post-routing status |
|---|---|
| `schoolbook_sequential` | about 0.54 s |
| `ntt_sequential` | about 0.53 s, 0 NTT steps |
| `ntt_tree` | about 1.84 s, 0 NTT steps |
