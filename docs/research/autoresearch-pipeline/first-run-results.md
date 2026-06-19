# First OpenRouter/OpenEvolve Run

Date: 2026-06-11

## Setup

- Framework: OpenEvolve.
- Provider: OpenRouter.
- Model: `qwen/qwen3-coder-flash`.
- Objective: exact `count_cycle_type(cycle_type, method="touchard")` on the
  smoke cold-start workload, with exact result digests required for nonzero
  score.
- Output directory:
  `benchmark_results/autoresearch/openevolve_touchard_smoke_flash_strict_cache_first`.

The free `qwen/qwen3-coder:free` lane was tried first at low weight and hit
OpenRouter upstream 429 rate limits. The live config now uses Flash only.

## Evaluator Correction

The first successful run exposed a metric issue: model-generated candidates
could add local `lru_cache` wrappers that survived across workload groups, while
the benchmark only cleared the package-level Touchard cache. That inflated
scores for a cold-start objective.

The benchmark now calls an optional `counter.clear_cache()` hook before each
workload. The OpenEvolve evaluator attaches this hook and clears either a
candidate-provided `clear_candidate_cache()` function or any candidate module
objects exposing `cache_clear()`.

The integer digest path was also changed to hash a byte encoding of exact
integers instead of calling `str(result)`, because quick/promotion workloads can
produce integers beyond Python's default decimal conversion digit limit.

## Corrected Smoke Run

The corrected 5-iteration smoke run completed successfully.

Best candidate:

- `combined_score`: 1.4200
- `correctness`: 1.0000
- `geomean_speedup`: 1.4200
- `worst_regression`: 0.0000
- `all_cycle_types_n_8_speedup`: 1.1875
- `named_families_n_64_speedup`: 1.5588
- `dense_touchard_n_128_speedup`: 1.8034

The candidate groups repeated cycle lengths and adds a per-call dictionary for
one-cycle values. It is an incremental implementation improvement, not a new
algorithmic breakthrough.

## Quick-Profile Validation

The corrected-run best candidate was then evaluated on the broader quick
profile:

- `correctness`: 1.0000
- `geomean_speedup`: 1.4125
- `combined_score`: 1.3926
- `fixed_n_batches_speedup`: 0.8478
- `named_high_n_families_speedup`: 2.4279
- `dense_touchard_stress_speedup`: 1.9766
- `worst_regression`: 0.1795

Conclusion: the pipeline works and can discover exact, faster variants, but
this first candidate is not ready to port because it regresses the fixed-n batch
part of the holistic quick metric.

## Next Direction

Use the corrected evaluator for longer runs, but tighten the objective before
spending more tokens:

- Keep autoresearch workloads at `n <= 1024`; a manual probe at `n=4096`
  showed even the repeated `[16] * 256` Touchard case taking about 67 seconds
  from a cold cache, and the mixed-ladder case was stopped before completion.
- Promote `quick` to the main evaluation profile once runtime is acceptable.
- Hard-penalize or reject candidates with fixed-n batch speedup below 1.0.
- Ask for repeated-part subset DP and batched `M_s` computation explicitly in
  the prompt, because the first run mostly found local implementation tweaks.
