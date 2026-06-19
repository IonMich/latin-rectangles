# External Survey

This survey focuses on systems that are relevant to this repository: automatic
algorithm discovery or code optimization where candidate quality can be checked
by programmatic evaluation.

## AlphaEvolve

Google DeepMind's AlphaEvolve is the closest reference point. Its public paper
describes an LLM-driven evolutionary coding agent where a user supplies an
initial program, evolution-marked code regions, evaluators, and configuration.
The system samples from a program database, asks an LLM ensemble for improved
programs, evaluates them, and adds scored candidates back to the database.

The key lesson is that AlphaEvolve is evaluator-centered. The model is not
trusted to be right; the generated code is executed and scored. The paper also
matters because it broadens the FunSearch pattern from short single functions to
larger code files, multiple functions, and longer evaluations. For this repo,
that suggests evolving implementation blocks around Touchard, rook polynomial,
and benchmark-routing code is a plausible target.

What does not transfer directly: AlphaEvolve's success cases use substantial
infrastructure, parallelism, model budget, and task-specific evaluator design.
The repo should not start by trying to recreate all of that.

## FunSearch

FunSearch is the earlier LLM plus evaluator plus program-database pattern. It
evolves short programs and promotes high-scoring candidates. Its relevance here
is conceptual: the useful artifact is executable code that can be scored
automatically, not a prose conjecture.

For `latin-rectangles`, FunSearch-style scope may actually be a good first
iteration if we expose small evolve blocks: recurrence generation, route
selection, multiplication-order heuristics, and component-DP branching
heuristics.

## OpenEvolve

OpenEvolve is an open-source AlphaEvolve-style framework. Its documented
features include LLM ensembles, evaluator artifacts, cascade evaluation,
MAP-Elites quality-diversity archives, islands, migration, and custom feature
dimensions. It can run from an initial program plus evaluator and can return
multiple metrics, not only a scalar.

OpenEvolve is a reasonable second step after this repo has a stable evaluator.
It is not the recommended first step because a framework cannot compensate for
an under-specified score. If the evaluator is good, OpenEvolve could provide
archive management and evolutionary scheduling quickly.

## CodeEvolve

CodeEvolve is another open-source evolutionary coding framework. It emphasizes
island-based evolution, structured SEARCH/REPLACE diffs, resource-limited
sandboxed evaluation, JSON metrics, migration, and optional MAP-Elites. Its
paper and repository present it as a transparent alternative for algorithmic
discovery and heuristic design.

CodeEvolve is attractive if we want a heavier multi-island search. The current
repository is small enough that a lighter custom evaluator should come first,
but CodeEvolve's architecture is a good reference for the later version:
preserve code outside evolution zones, sandbox execution, output JSON, and
separate exploration from exploitation.

## GEPA and Reflective Search

GEPA optimizes textual parameters by reflecting on execution traces rather than
collapsing everything into one sparse scalar. It is more directly a prompt or
system optimizer than a code-evolution framework, but the idea is useful:
candidate artifacts should include failure traces and profiler summaries that a
model can inspect.

For this repo, GEPA-like reflection is best used around the prompt and strategy
layer: after a batch of failed candidate patches, ask a strong model to analyze
the artifacts and propose better constraints or a new research direction.

## AI Scientist-Style Systems

The AI Scientist family targets end-to-end scientific paper generation:
ideation, literature search, experiments, plots, writeup, and review. That is
broader than this repo needs. Its strongest transferable lessons are:

- require reproducibility;
- store the exact files executed;
- sandbox LLM-written code;
- expect plausible but incorrect implementations and unfair baselines unless
  the evaluator prevents them.

It is not recommended as the initial tool for this project.

## GPT-5.5 Pro As Research Partner

As of this investigation, OpenAI describes GPT-5.5 and GPT-5.5 Pro as strong at
long-horizon coding, tool use, and scientific research workflows, with GPT-5.5
Pro using more test-time compute for higher-accuracy work. OpenAI's pricing page
also makes the practical point clear: frontier-model iterations are expensive
relative to smaller models.

The right usage pattern is therefore:

- use GPT-5.5 Pro for high-leverage ideation, critique of top candidates, and
  postmortems on failed search batches;
- use cheaper models or local variants for routine mutations once the task is
  well specified;
- never treat a prose "breakthrough" as real until the repo evaluator verifies
  it.

## What To Ignore

Public X/Twitter reports are useful trend signals but weak evidence. The
credible common denominator behind the viral stories is not one specific model
prompt. It is the combination of a capable model, a tight task framing, strong
tool use, and a verifier that gives fast feedback.

