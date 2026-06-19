# Metric And Evaluator Design

The evaluator should be fast enough for iteration, strict enough to reject wrong
mathematics, and broad enough to avoid overfitting to one cycle family.

## Evaluation Contract

Each candidate patch is evaluated in a clean checkout against a pinned baseline.
The evaluator emits JSON and stores logs, benchmark CSVs, and any failure
artifacts.

A candidate receives a useful score only if it passes correctness gates. A
wrong exact count is not a slow candidate; it is invalid.

## Staged Gates

### Stage 0: Import And Targeted Tests

Run:

```console
uv run pytest tests/test_touchard.py tests/test_fft.py tests/test_benchmarks.py
```

This catches most API, exactness, routing, and benchmark-helper regressions.

### Stage 1: Full Test Suite

Run:

```console
uv run pytest
```

This is the normal correctness gate before a candidate can be considered.

### Stage 2: Quick Holistic Benchmark

Run a short benchmark suite with deterministic cases and one repeat:

```console
uv run benchmarks/benchmark_cycle_type_methods.py \
  --suite both \
  --family-ns 128,512,1024 \
  --all-cycle-ns 12,16,20 \
  --methods cycle_auto,touchard,rook_schoolbook,rook_ntt \
  --repeats 1 \
  --timeout-seconds 20 \
  --progress none \
  --output-dir benchmark_results/autoresearch_candidate
```

For inner-loop runs, `--no-track-memory` can be used if memory tracking is too
noisy. For promotion runs, keep memory tracking on.

### Stage 3: Held-Out Promotion Benchmark

Before accepting a candidate, run a broader benchmark not exposed to the inner
loop:

```console
uv run benchmarks/benchmark_cycle_type_methods.py \
  --suite families \
  --family-ns 256,512,768,1024 \
  --methods cycle_auto,touchard,rook_schoolbook,rook_ntt \
  --repeats 3 \
  --timeout-seconds 120 \
  --progress case \
  --output-dir benchmark_results/autoresearch_promotion
```

Add targeted diagnostics for any surprising result:

```console
uv run benchmarks/diagnose_scaling.py \
  --ns 1024 \
  --families mixed_ladder,mostly_16_cycles,two_equal_cycles,four_equal_cycles \
  --touchard-modes cold,warm \
  --rook-strategies schoolbook_sequential,ntt_sequential,ntt_tree \
  --timeout-seconds 20 \
  --output-dir benchmark_results/autoresearch_diagnostics
```

## Scalar Score

Use a scalar for selection, but keep raw metrics for human review and Pareto
analysis.

Definitions:

- `baseline_time_i`: baseline median or single-run time for benchmark case `i`.
- `candidate_time_i`: candidate time for the same case.
- `w_i`: case weight. Give higher weight to `cycle_auto`, cold dense cases, and
  representative high-`n` families.
- `speedup_i = baseline_time_i / candidate_time_i`.
- `log_speedup = sum(w_i * log(clamp(speedup_i, 0.20, 5.00))) / sum(w_i)`.
- `worst_regression = max(0, max_i(candidate_time_i / baseline_time_i) - 1.10)`.
- `memory_growth = max(0, max_i(candidate_peak_mb / baseline_peak_mb) - 1.25)`.
- `complexity = min(1, changed_non_test_lines / 800)`.

Suggested score:

```text
if any correctness gate fails:
    score = -1_000_000
else:
    score = 1000 * log_speedup
            - 300 * worst_regression
            - 100 * memory_growth
            - 25 * complexity
            - 50 * public_api_change
```

`public_api_change` is `1` unless the candidate intentionally changes the API
and a human approved that search direction.

This score rewards broad multiplicative speedups while preventing one huge win
from hiding a serious regression.

## JSON Output Sketch

```json
{
  "candidate_id": "2026-06-11T12-34-56Z_abcd1234",
  "base_commit": "abc123",
  "candidate_commit": "def456",
  "status": "ok",
  "score": 143.2,
  "correctness": {
    "pytest_targeted": "ok",
    "pytest_full": "ok",
    "method_agreement": "ok"
  },
  "performance": {
    "weighted_log_speedup": 0.168,
    "worst_regression": 0.03,
    "cases": [
      {
        "suite": "families",
        "family": "mixed_ladder",
        "n": 1024,
        "method": "cycle_auto",
        "baseline_seconds": 0.12,
        "candidate_seconds": 0.09,
        "speedup": 1.33
      }
    ]
  },
  "complexity": {
    "changed_non_test_lines": 112,
    "public_api_change": false
  },
  "artifacts": {
    "pytest_log": "artifacts/pytest.log",
    "benchmark_csv": "artifacts/cycle_families.csv",
    "stderr": "artifacts/stderr.log",
    "notes": "Candidate improves cold M_s cache fill but regresses transpositions."
  }
}
```

## Artifact Feedback For Models

Give the next model call concise structured feedback:

- exact failure message or timeout;
- cases with largest speedup and largest regression;
- profiler or diagnostic summary when available;
- changed files and line counts;
- whether the candidate changed semantics, API, dependencies, or formatting.

Do not feed full CSVs into every prompt. Summarize them into a small report and
link the raw artifacts.
