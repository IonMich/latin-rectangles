# Auto-Research Pipeline Investigation

Date: 2026-06-11

This folder records an investigation into whether this repository should adopt
an AlphaEvolve-style auto-research loop for discovering faster exact algorithms
or better implementations for Latin rectangle extension counting.

## Bottom Line

Set up a harness-first pipeline before adopting a full external framework.

The repo already has the hard part that makes auto-research viable: exact
oracles, deterministic benchmark families, exhaustive small cycle-type suites,
and diagnostics for method internals. The missing piece is a small evaluator
that turns candidate patches into a reproducible score and stores artifacts
that a model can use for the next attempt.

The recommended first direction is:

1. Build a local evaluator and archive for candidate patches.
2. Use GPT-5.5 Pro or a comparable high-reasoning model for periodic ideation
   and critique, not for every mutation in the inner loop.
3. Let cheaper coding models generate most implementation variants once the
   evaluator is stable.
4. Consider OpenEvolve or CodeEvolve only after the evaluator and score have
   proven useful on this repo.

## Why This Is The Right Shape

AlphaEvolve, FunSearch, OpenEvolve, CodeEvolve, and related systems all depend
on the same core pattern: represent ideas as executable code, evaluate them
automatically, keep the best and most diverse candidates, and iterate. Public
claims about "asking a frontier model to think" are plausible as an ideation
tool, but they are not a substitute for the evaluator.

For this repository, that means a useful auto-research loop should optimize
against a quick holistic metric with strict correctness gates. It should not
optimize only a single benchmark case, because the current implementation has
multiple regimes:

- warm-cache Touchard cycle-structure queries;
- cold dense Touchard queries;
- rook-polynomial schoolbook products;
- exact NTT/CRT products that often fall back because CRT reconstruction is too
  expensive;
- the separate general `k x n -> (k + 1) x n` component-DP path.

## Files

- [external-survey.md](external-survey.md): summary of the relevant public
  systems and what is credible for this repo.
- [repo-fit.md](repo-fit.md): how the current codebase and benchmark data map
  to auto-research opportunities.
- [metric-and-evaluator.md](metric-and-evaluator.md): proposed correctness
  gates, benchmark suites, scalar score, and evaluator output schema.
- [pipeline-design.md](pipeline-design.md): concrete staged pipeline design and
  tool/framework recommendation.
- [touchard-cold-start-plan.md](touchard-cold-start-plan.md): first concrete
  autoresearch setup plan, centered on cold-start exact `N_1(lambda)` batch
  throughput and the related `M_s` bottleneck.
- [openevolve-implementation-plan.md](openevolve-implementation-plan.md):
  implementation plan for the OpenEvolve/Codex-compatible evaluator scaffold,
  provider strategy, and follow-up problem wrapper.
- [../../../tools/autoresearch/openevolve_touchard/README.md](../../../tools/autoresearch/openevolve_touchard/README.md):
  runnable OpenEvolve problem package and OpenRouter-first run instructions.
- [source-notes.md](source-notes.md): source links used during the
  investigation.

## Recommended First Milestone

The first implementation milestone is now present in `tools/autoresearch`: a
cold-start benchmark helper, a candidate evaluator, and an OpenEvolve problem
package configured OpenRouter-first. The next useful step is to run a short
OpenRouter-backed OpenEvolve search and inspect whether generated candidates
produce meaningful exact speedups or just noise.
