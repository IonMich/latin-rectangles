# Fit To This Repository

## Current Baseline

The repository is already unusually well suited for auto-research because it has
several exact implementations and benchmark tools:

- `count_cycle_structure_extensions(..., method="touchard")` evaluates the
  Touchard formula with cached one-cycle values `M_s`.
- `count_cycle_structure_extensions(..., method="rook")` evaluates the exact
  rook-polynomial product.
- `count_extensions(..., use_fft=True)` can use exact NTT/CRT convolution, with
  guards that fall back to schoolbook multiplication when CRT cost is too high.
- `benchmarks/benchmark_cycle_type_methods.py` compares methods and checks
  integer equality before writing CSV results.
- `benchmarks/diagnose_scaling.py` decomposes Touchard and rook work into
  measurable internal steps.
- `count_extensions_k` covers the more general `k x n -> (k + 1) x n` path via
  component matching polynomials.

This means auto-research candidates can be scored without a human judging every
result.

## Existing Performance Regimes

The checked-in benchmark and diagnostic data show several regimes that an
evaluator should preserve:

- Small and warm-cache cycle-structure queries are extremely fast under
  Touchard.
- Cold dense Touchard at high `n` can be slow because many high-index `M_s`
  values must be computed.
- Rook schoolbook multiplication remains competitive at high `n` for the
  current integer coefficient sizes.
- Exact NTT/CRT is not automatically better. Earlier diagnostics found that
  balanced products could require many CRT primes, so the current implementation
  correctly falls back in many cases.
- Product trees are not obviously better; a checked diagnostic at `n=2048`
  showed sequential schoolbook around the same or faster than tree order for
  the tested mixed-ladder case.

The evaluator should therefore reward broad speedups and heavily penalize
special-case improvements that regress another regime.

## Most Promising Research Targets

1. Faster cold computation of many one-cycle values `M_s`.
   The current Touchard bottleneck for dense high-`n` inputs is repeated cold
   computation of one-cycle inclusion-exclusion values. A recurrence, batched
   computation, or generating-function method for all required `M_s` values is
   the highest-value algorithmic target.

2. Smarter Touchard subset-count handling.
   `_touchard_subset_counts` is simple and robust. There may be wins from gcd
   compression, repeated-part grouping, or early classification of sparse versus
   dense reachable sums. The challenge is preserving multiplicities exactly.

3. Multiplication-order heuristics with evidence.
   The current sequential rook product is strong. A candidate should only change
   multiplication order if it wins across families and not just one balanced
   example.

4. Better route selection.
   `_choose_cycle_structure_method` currently uses cache state, missing `M_s`
   count, and `n`. The evaluator can search for better features, but the score
   must include cold and warm cache cases.

5. General `k x n -> (k + 1) x n` component improvements.
   Candidate ideas include caching identical component polynomials, choosing the
   smaller branching side, using component signatures, and adding cheap
   diagnostic features for largest orbit and neighborhood masks.

6. Micro-optimizations inside exact pure-Python loops.
   These may help, but they should be secondary to algorithmic improvements.
   Avoid adding dependencies until the pure-Python ceiling is clear.

## Lower-Priority Or Riskier Targets

- Floating-point FFT: not suitable for exact integer counts without a careful
  reconstruction story.
- Bigger NTT push: previous evidence suggests CRT cost is the limiting factor,
  so this needs a new idea, not just lower thresholds.
- Full AI Scientist-style paper automation: too broad for the current objective.
- Model-only ideation without a patch evaluator: likely to produce attractive
  but unverifiable claims.

## Suggested Evolution Blocks

When this becomes code, start with narrow evolve zones:

- `_OneCycleExtensionCounter._compute`
- helper functions used by `_touchard_subset_counts`
- `_choose_cycle_structure_method`
- rook-polynomial product ordering in `_count_cycle_structure_extensions_rook`
- selected internals of `general_extensions.py`

Keep public APIs and exact integer outputs outside the evolve zone.

