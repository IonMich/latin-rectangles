# OpenEvolve/Codex Auto-Research Implementation Plan

Date: 2026-06-11

This is the implementation plan for turning the Touchard cold-start objective
into a practical auto-research setup without building a full framework from
scratch.

## Decision

Use **OpenEvolve as the first external auto-research framework**. The repo-local
evaluator is the contract OpenEvolve optimizes against.

Do not build a new evolutionary framework. The repo should supply:

- a deterministic exact evaluator;
- benchmark workloads for cold-start `N_1(lambda)` throughput;
- result digests and score calculations;
- an OpenEvolve problem wrapper/config;
- Codex-friendly scripts and reports for human-in-the-loop runs.

OpenEvolve should supply:

- population management;
- candidate mutation loop;
- archive/checkpoint mechanics;
- model ensemble configuration;
- MAP-Elites/islands when useful.

## Model And Provider Strategy

The model backend must be configurable through OpenAI-compatible settings:

```yaml
models:
  cheap_codegen:
    base_url: ${OPENAI_COMPATIBLE_BASE_URL}
    api_key_env: OPENAI_COMPATIBLE_API_KEY
    model: ${AUTORESEARCH_CHEAP_MODEL}
  strong_reasoner:
    base_url: ${OPENAI_COMPATIBLE_BASE_URL}
    api_key_env: OPENAI_COMPATIBLE_API_KEY
    model: ${AUTORESEARCH_STRONG_MODEL}
```

Supported provider patterns:

- **Codex**: preferred for interactive, human-supervised candidate generation
  because the user has liberal limits.
- **OpenRouter**: preferred hosted option for quickly switching among many
  models through one OpenAI-compatible endpoint.
- **LiteLLM**: preferred if we want our own gateway, BYO provider keys, or local
  routing policies.
- **Direct OpenAI API**: acceptable for selected runs, but GPT-5.5 Pro should
  not be the default inner-loop model because cost dominates.
- **Local/OpenAI-compatible endpoints**: useful for cheap mutation batches when
  quality is good enough.

GPT-5.5 Pro, if used, belongs in rare ideation or postmortem passes, not in the
main mutation loop.

## Architecture

```text
OpenEvolve / Codex
    |
    v
candidate patch or candidate extension_counting.py
    |
    v
repo-local evaluator
    |
    +-- targeted/full tests
    +-- cold-start benchmark workloads
    +-- exact result digests
    +-- weighted score
    |
    v
JSON artifacts + archive row + reflection summary
```

The evaluator is the contract. Any framework that can run it and read the JSON
score can drive the search.

## Implementation Milestones

### Milestone 1: Cold-Start Benchmark Helper

Created:

```text
tools/autoresearch/benchmark_touchard_cold_start.py
```

Responsibilities:

- build deterministic workload groups;
- start each workload group with cold module-level caches;
- allow cache reuse inside a batch;
- compute exact `N_1(lambda)` values;
- emit JSON rows with runtime, memory, result digest, result mod sums, and cache
  stats.

Profiles:

- `smoke`: tiny and CI-safe;
- `quick`: suitable for candidate screening;
- `promotion`: larger held-out suite.

### Milestone 2: Candidate Evaluator

Created:

```text
tools/autoresearch/evaluate_candidate.py
```

Responsibilities:

- compare a baseline ref/path and a candidate ref/path;
- run the cold-start benchmark helper against both;
- optionally run pytest gates on the candidate;
- compute weighted speedup and regression penalties;
- emit one JSON report.

It should support both committed refs and local directories so Codex-created
working trees and OpenEvolve output directories can both be evaluated.

### Milestone 3: OpenEvolve Problem Wrapper

Created:

```text
tools/autoresearch/openevolve_touchard/
  initial_program.py
  evaluator.py
  config.openrouter.yaml
  config.dry.yaml
  README.md
tools/autoresearch/run_openevolve_openrouter.sh
```

The wrapper evaluates candidate code against the real package and returns
OpenEvolve metrics including:

- `combined_score`;
- `correctness`;
- `geomean_speedup`;
- `weighted_log_speedup`;
- `worst_regression`;
- `max_memory_ratio`;
- `candidate_lines`;
- per-workload speedups.

`config.openrouter.yaml` is OpenRouter-first and defaults to cheap Qwen coding
models. `config.dry.yaml` verifies OpenEvolve loading/evaluation without making
model calls.

### Milestone 4: Codex-Orchestrated Runs

Use Codex for:

- reading failed archive artifacts;
- creating idea cards;
- making targeted candidate patches;
- launching evaluator runs;
- promoting/rejecting candidates.

This path is useful before spending API budget on large automated runs.

### Milestone 5: Provider Matrix

Test the same OpenEvolve problem with:

- cheap code model through OpenRouter;
- direct OpenAI or OpenRouter strong model for selected refinement;
- optional LiteLLM gateway if we want routing and cost controls.

## Completion Criteria For This Setup

The first implementation pass is complete when:

- the implementation plan exists;
- the cold-start benchmark helper runs with `uv run`;
- the evaluator compares two local refs/paths and emits JSON;
- the OpenEvolve problem wrapper loads with `openevolve-run` dry config;
- OpenRouter-first config and env-file wrapper exist;
- smoke tests cover workload creation, digesting, and score calculation;
- docs explain how OpenEvolve, Codex, and provider routing fit together.
