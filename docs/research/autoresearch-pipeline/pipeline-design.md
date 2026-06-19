# Pipeline Design

## Recommended Architecture

Start with a local custom loop, then optionally plug it into OpenEvolve or
CodeEvolve.

```text
baseline commit
    |
    v
idea queue  ->  candidate patch generator  ->  isolated candidate checkout
    ^                                             |
    |                                             v
reflection summaries  <-  evaluator artifacts <- staged evaluator
    |
    v
candidate archive / Pareto frontier
```

## Components

### 1. Baseline Manager

Pin a baseline commit and baseline benchmark JSON. Every candidate is compared
against the same baseline until a human promotes a new baseline.

Baseline artifacts should include:

- `uv run pytest` result;
- quick benchmark CSVs;
- promotion benchmark CSVs when available;
- machine metadata such as CPU, Python version, and git commit.

### 2. Idea Queue

Maintain a plain JSONL or SQLite queue of research ideas. Each idea should have:

- hypothesis;
- target files/functions;
- expected affected regimes;
- risk;
- evaluator additions needed;
- originating source: human, model, failed-candidate reflection, or literature.

Use GPT-5.5 Pro or another high-reasoning model here because idea quality and
critique matter more than token cost.

### 3. Candidate Patch Generator

Generate patches in narrow evolve zones first. The generator can be:

- Codex/manual agent work;
- a small custom script that prompts an LLM with top candidates and artifacts;
- OpenEvolve or CodeEvolve later.

The generator should not be allowed to rewrite benchmark definitions, delete
tests, relax correctness checks, or change public APIs unless the search run is
explicitly about benchmark/evaluator design.

### 4. Isolated Evaluation

Evaluate in a temporary checkout with:

- wall-clock timeout;
- memory limit when practical;
- no network for candidate code;
- captured stdout/stderr;
- exact patch and commit metadata.

This matters because LLM-written code may accidentally spawn processes, use
network access, write outside the repo, or optimize the evaluator instead of the
algorithm.

### 5. Candidate Archive

Store every candidate, not only winners. Useful archive dimensions:

- score;
- correctness status;
- changed function;
- algorithm family;
- speedup by regime;
- memory;
- changed line count;
- novelty or diversity embedding if a framework supplies it.

Keep a Pareto frontier rather than a single champion. A candidate that improves
cold dense Touchard but regresses rook products may still be useful as a parent
for a later run.

### 6. Reflection Loop

After each batch, produce a short report:

- best candidate;
- top regressions;
- repeated failure modes;
- benchmark cases that are too noisy or too easy;
- next search constraints.

Ask a strong model to critique that report and update the idea queue. This is
where "ask GPT-5.5 Pro to think" belongs.

## Framework Decision

### Start Custom

Use a custom evaluator first because the repo-specific score is the central
piece. A 200-400 line script can prove whether the metric is useful before we
import a larger framework.

### Add OpenEvolve If

- the evaluator already emits stable JSON;
- we want MAP-Elites, islands, migration, or prompt templates quickly;
- we are comfortable mapping this repo into OpenEvolve's program/evaluator
  interface.

### Add CodeEvolve If

- we want stronger sandbox/process controls and structured SEARCH/REPLACE
  diffs;
- we are running larger multi-island experiments;
- Linux-specific process controls are available or acceptable.

### Use GEPA If

- the main bottleneck becomes prompt quality rather than implementation search;
- we want to optimize prompts over execution traces and artifacts.

### Do Not Start With AI Scientist

It is too broad for this repo's immediate objective. The goal here is algorithm
and implementation improvement, not automated paper production.

## First Three Implementation Milestones

1. `tools/autoresearch/evaluate_candidate.py`
   Runs staged correctness and benchmark suites, compares against a pinned
   baseline, and emits JSON.

2. `tools/autoresearch/summarize_candidate.py`
   Converts raw pytest logs, benchmark CSVs, and diagnostics into a compact
   artifact summary suitable for model feedback.

3. `tools/autoresearch/run_batch.py`
   Applies candidate patches in temporary checkouts, runs the evaluator, stores
   JSONL archive entries, and updates a simple Pareto frontier.

Only after these exist should we wire in OpenEvolve, CodeEvolve, or a custom LLM
mutation loop.

## Initial Search Agenda

1. Batched or recurrent computation of one-cycle values `M_s`.
2. Touchard route selection that accounts for cold/warm cache and reachable
   `M_s` density.
3. Exact subset-count optimizations for repeated cycle lengths.
4. Component-DP optimizations in the general `k x n -> (k + 1) x n` path.
5. Carefully measured micro-optimizations in polynomial multiplication and
   inclusion-exclusion.

