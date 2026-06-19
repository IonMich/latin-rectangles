# Touchard Cold-Start Auto-Research Plan

Date: 2026-06-11

This plan defines the first concrete auto-research objective for the repository.
It focuses on cold-start exact computation of the overall cycle-structure count
`N_1(lambda)` / `E(lambda)`, while treating faster generation of the one-cycle
Touchard values `M_s` as an important but not exclusive subproblem.

## Objective

Improve cold-start throughput for exact computation of
`count_cycle_structure_extensions(lambda)` across batches of derangement cycle
types, without regressing warm-cache queries or the rook-polynomial fallback
regimes.

In practical terms, optimize this workload:

```text
Given many cycle structures lambda_1, ..., lambda_q,
compute exact N_1(lambda_i) for every i after a fresh process/cache start.
```

Within a workload group, reuse of work across the batch is allowed and
encouraged. The "cold-start" requirement means the batch begins with no warmed
module-level caches or precomputed tables from previous benchmark groups.

This objective is better than optimizing only `M_s` because there may be wins in
the full pipeline:

- computing many needed `M_s` values faster;
- computing only the `M_s` values that matter for the batch;
- grouping repeated cycle parts before subset-sum DP;
- reusing subset-sum work across related cycle structures;
- combining subset multiplicities with `M_s` values more efficiently;
- routing some cold dense inputs away from Touchard when rook products are
  cheaper.

## Auto-Research Framework Decision

Use a repo-native custom harness first. Do not start with OpenEvolve,
CodeEvolve, GEPA, or AI Scientist.

The first implementation should be a small local pipeline:

```text
idea card -> LLM/Codex patch proposal -> clean candidate checkout
          -> exact evaluator -> scored archive -> reflection summary
          -> next idea card or candidate mutation
```

The reason is practical: for this repository, the evaluator and workload design
are more important than the evolutionary framework. A general framework can
manage populations and prompts, but it cannot decide the right mathematical
objective for exact `N_1(lambda)` throughput. We should first build the
candidate evaluator and archive, then decide whether framework machinery is
worth adding.

Planned framework path:

1. Phase 1 uses a custom harness only:
   `tools/autoresearch/evaluate_candidate.py`,
   `tools/autoresearch/benchmark_touchard_cold_start.py`, and a JSONL archive.
2. Phase 2 uses Codex/GPT-5.5 Pro manually or semi-automatically to generate
   candidate patches against the local evaluator.
3. Phase 3 adds OpenEvolve if we need population management, MAP-Elites,
   islands, and automatic mutation scheduling.
4. CodeEvolve is the fallback if we specifically need its stricter
   SEARCH/REPLACE patch style or heavier multi-process sandboxing.
5. GEPA is only for optimizing prompts or strategy text after the code
   evaluator exists; it is not the main code-search framework.

So the concrete answer is: **initially no external autoresearch framework**.
Use a local evaluator/archive with Codex or GPT-5.5 Pro generating candidates.
OpenEvolve is the first external framework to try later, once the objective is
stable.

## How The Research Bullets Become Auto-Research

The bullets above are not just implementation ideas. In the autoresearch setup,
each bullet becomes a class of candidate-generating prompts, allowed code edits,
benchmark features, and archive labels.

### Faster computation of many `M_s`

Autoresearch role: generate algorithmic candidates for the one-cycle value
engine.

Allowed patch area:

- `_OneCycleExtensionCounter._compute`
- new private helpers for batched or recurrent `M_s`
- cache prefill helpers

Evaluator signal:

- Workload C should improve strongly;
- Workload A should improve when many cycle types share `M_s` demand;
- warm-cache checks must not regress.

Example candidate prompt:

```text
Propose an exact batched method for computing all required formal one-cycle
values M_s up to max_s. Preserve integer arithmetic and the existing public API.
Only modify private Touchard helpers.
```

### Computing only the `M_s` values that matter

Autoresearch role: generate candidates that reduce unnecessary internal work
before computing `M_s`.

Allowed patch area:

- `_touchard_m_values`
- `_count_cycle_structure_extensions_touchard`
- batch-level planning helpers in the new benchmark/evaluator tool

Evaluator signal:

- unique `M_s` count and accumulation time should drop in diagnostics;
- exact result digests must match baseline;
- sparse and balanced families should not slow down.

### Grouping repeated cycle parts

Autoresearch role: generate alternative subset-count algorithms and let the
evaluator determine when to use them.

Allowed patch area:

- `_touchard_subset_counts`
- new grouped-subset helper
- route logic choosing grouped versus current DP

Evaluator signal:

- repeated-part workloads such as `transpositions`, `mostly_3_cycles`,
  `mostly_8_cycles`, and `mostly_16_cycles` should improve;
- mixed-part workloads should not regress.

### Reusing subset-sum work across related cycle structures

Autoresearch role: generate batch-level algorithms. This is why the first
evaluator must include many `N_1(lambda)` values for fixed `n`, not only single
queries.

Allowed patch area:

- initially the new `benchmark_touchard_cold_start.py` batch helper;
- later private batch APIs if the idea proves useful.

Evaluator signal:

- Workload A improves as a batch;
- single-query Workload B is allowed to stay neutral;
- archive records whether the candidate is a batch-only optimization.

### Combining subset multiplicities with `M_s` values faster

Autoresearch role: generate candidates for the final Touchard accumulation
step, not just for the `M_s` generator.

Allowed patch area:

- `_count_cycle_structure_extensions_touchard`
- private helpers that compress multiplicities by absolute signed sum

Evaluator signal:

- accumulation time in diagnostics should drop;
- result digest and per-case exact counts must match;
- memory growth must remain bounded.

### Routing cold dense inputs away from Touchard

Autoresearch role: generate route-selector candidates that choose between
Touchard and rook products from cheap features.

Allowed patch area:

- `_choose_cycle_structure_method`
- cheap feature-estimation helpers

Evaluator signal:

- `cycle_auto` improves on cold high-`n` dense cases;
- direct `touchard` and direct `rook` methods remain available and correct;
- no regression for warm-cache Touchard cases.

This is where evolutionary search is useful: the model can propose route
features or thresholds, but the evaluator decides whether those thresholds
survive across held-out families.

## Success Metric

Primary metric: weighted geometric speedup of exact cold-start batch evaluation
relative to the current `main`/baseline implementation.

A candidate is valid only if every checked answer agrees with the baseline exact
integer. Timeouts, wrong answers, relaxed tests, or benchmark changes invalidate
the candidate.

Suggested minimum bar for promotion:

- at least `1.20x` weighted cold-batch speedup on the quick suite;
- no more than `1.10x` slowdown on any high-priority benchmark family;
- no public API change;
- no new runtime dependency unless separately approved.

## Workloads

### Workload A: Many `N_1(lambda)` Values For One Fixed `n`

This workload models exhaustive or partial enumeration of derangement cycle
types at fixed `n`.

Initial quick cases:

- all cycle types for `n = 20`;
- first 2,000 cycle types for `n = 30`, ordered by the existing benchmark
  ordering;
- stratified sample of cycle types for `n = 40`, including sparse, dense,
  repeated-part, and mixed-part examples.

Why it matters: this is where repeated exact counts may share `M_s` values or
subset-sum patterns.

### Workload B: Named High-`n` Families From A Cold Start

This workload models individual large queries across structurally different
cycle families.

Initial quick cases:

- `single_cycle`;
- `two_equal_cycles`;
- `four_equal_cycles`;
- `transpositions`;
- `mostly_3_cycles`;
- `mostly_8_cycles`;
- `mostly_16_cycles`;
- `mixed_ladder`;

for `n = 256, 512, 1024`.

Why it matters: it prevents optimizing only all-cycle-type enumeration at small
`n`.

### Workload C: Dense Touchard Stress Cases

This workload directly targets the current cold Touchard pain point.

Initial cases:

- `mixed_ladder` at `n = 1024`;
- cycle types with gcd `1` and many reachable subset sums;
- repeated-part types where grouping may help;
- balanced large cycles where only a small number of `M_s` values are needed.

Why it matters: it distinguishes "make `M_s` faster" from "avoid needing many
new `M_s` values".

## Candidate Search Space

Start with narrow evolve zones. These are the functions an auto-research agent
is allowed to modify in the first round:

- `_OneCycleExtensionCounter._compute`
- `_touchard_subset_counts`
- `_touchard_m_values`
- `_count_cycle_structure_extensions_touchard`
- `_choose_cycle_structure_method`
- new private helpers in `extension_counting.py`

Allowed changes:

- exact recurrences or batched computation for one-cycle values;
- grouped subset-count DP for repeated cycle lengths;
- batch-level cache prefill helpers;
- route-selection improvements;
- local data-structure changes that preserve exact integer arithmetic.

Disallowed in the first round:

- changing public function signatures;
- adding required dependencies;
- changing benchmark definitions used by the evaluator;
- replacing exact arithmetic with floating-point approximations;
- weakening tests or equality checks;
- broad rewrites of unrelated modules.

## Evaluator Setup

Implement a new tool:

```console
uv run tools/autoresearch/evaluate_candidate.py \
  --baseline-ref main \
  --candidate-ref HEAD \
  --suite touchard-cold-start \
  --output-dir benchmark_results/autoresearch/touchard_cold_start
```

The evaluator should run in a clean temporary checkout for each ref. It should
spawn a fresh Python process for every cold-start benchmark group so module
caches do not leak across cases unless the workload explicitly measures batch
reuse.

### Evaluator Stages

1. Correctness smoke:

   ```console
   uv run pytest tests/test_touchard.py tests/test_fft.py tests/test_benchmarks.py
   ```

2. Full correctness:

   ```console
   uv run pytest
   ```

3. Cold batch benchmark:

   Use a dedicated benchmark helper rather than the existing method-comparison
   runner. The helper should emit one JSON row per workload group:

   ```json
   {
     "workload": "all_cycle_types_n_20",
     "status": "ok",
     "count_inputs": 137,
     "seconds": 0.123,
     "peak_memory_mb": 5.4,
     "result_digest": "sha256:...",
     "result_mod_sum_1000000007": 123456
   }
   ```

4. Method agreement probes:

   For small cases, compare candidate `touchard`, `rook`, `rook_ntt`, and
   `cycle_auto` results. For large cases, compare candidate results to the
   pinned baseline digest.

5. Promotion diagnostics:

   Run `benchmarks/diagnose_scaling.py` on any case with a large speedup,
   slowdown, or timeout so the archive includes a reason, not just a score.

## Scoring

Use the general scoring model from
[metric-and-evaluator.md](metric-and-evaluator.md), but set these weights for
this objective:

- `0.45`: Workload A, many exact `N_1(lambda)` values for fixed `n`;
- `0.30`: Workload B, named high-`n` cold starts;
- `0.20`: Workload C, dense Touchard stress cases;
- `0.05`: warm-cache regression check.

Add hard penalties:

- `-infinity`: wrong exact answer;
- `-infinity`: candidate edits tests or benchmark evaluator files;
- `-500`: any high-priority family slower by more than `1.25x`;
- `-200`: memory peak grows by more than `2x`;
- `-100`: changed non-test lines exceed 500 without a matching speedup above
  `1.5x`.

## First Search Prompts

Use these as high-level prompts for GPT-5.5 Pro or another strong reasoning
model before asking for code patches:

1. "Find an exact recurrence or batched algorithm for computing many formal
   one-cycle values `M_s = F(q_s)` for `s <= n`, where `q_s` is the signed
   matching polynomial of `C_{2s}` under the Touchard/Chebyshev identity."

2. "Given many cycle structures of the same `n`, design an exact way to reuse
   subset-sum multiplicities or reachable `|2a-n|` sets across structures."

3. "For a single cycle structure with many repeated parts, derive an exact
   grouped subset-count algorithm and compare its asymptotic and constant-factor
   behavior to the current one-part-at-a-time DP."

4. "Design a route selector for exact `N_1(lambda)` from a cold process using
   features available before heavy computation: `n`, cycle count, gcd, repeated
   part histogram, estimated reachable subset density, and estimated missing
   `M_s` cost."

5. "Look for algebraic identities that combine the Touchard sum directly for a
   whole `lambda`, avoiding materializing all intermediate `M_s` values when
   multiplicities or parity structure are favorable."

## Archive Fields

Every candidate should record:

- candidate id, parent id, and git diff;
- changed functions;
- exact objective hypothesis;
- correctness status;
- cold-batch score;
- per-workload speedups;
- worst regression;
- memory ratio;
- diagnostic summaries for changed regimes;
- model prompt and model response if generated by an LLM;
- human notes after review.

## Phase Plan

### Phase 1: Build The Evaluator

Create the cold-start benchmark helper and candidate evaluator. Do not run LLM
search yet. Validate that the baseline score is stable across at least five
runs.

### Phase 2: Manual Seed Ideas

Implement one or two human-written candidate branches:

- grouped subset-count DP for repeated cycle parts;
- batch prefill of `M_s` values for a fixed all-cycle-type run.

These candidates test whether the evaluator catches real wins and regressions.

### Phase 3: Model-Assisted Ideation

Use GPT-5.5 Pro to critique Phase 2 artifacts and generate a ranked idea queue.
At this point, ask for mathematical and algorithmic reasoning, not code.

### Phase 4: Candidate Generation

Use Codex or a code-generation loop to create patches inside the allowed evolve
zones. Run every candidate through the evaluator and store archive rows.

### Phase 5: Framework Decision

If the custom loop finds useful candidates but managing diversity becomes
manual work, plug the evaluator into OpenEvolve or CodeEvolve. Otherwise keep
the lightweight loop.

## Expected First Useful Outcomes

The first successful run may not discover a new formula. More realistic early
wins are:

- a better route selector for cold dense cycle structures;
- grouped subset DP that improves repeated-part workloads;
- a benchmark-backed rejection of tempting but slow `M_s` strategies;
- a precise profiler-backed statement of where a true formula-level
  improvement is needed.
