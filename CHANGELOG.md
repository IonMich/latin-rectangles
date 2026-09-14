# Changelog

## 0.3.3 - 2026-09-14

- Align empty polynomial multiplication across exact methods, protect cached
  rook coefficients from caller mutation, and reject nonpositive cycle parts.
- Add independent NTT/CRT and counting verification, a reproducible benchmark
  with cold/warm samples and machine metadata, and a measured case study.
- Detect CLI option conflicts by presence, report only positive counts in the
  enumeration headline, and count arbitrary zero-width extensions without
  recursive calls.
- Explain forbidden positions, rook counts, factorial completions and
  inclusion-exclusion with responsive animation and static diagrams. Retain
  Touchard's attribution and the distinction between specialized two-row and
  general forbidden-graph methods.
- Add a PyPI description with absolute documentation and image links; keep
  generated review bundles out of the source distribution.

## 0.3.2 - 2026-06-19

- Add the autoresearch scaffold for Touchard cold-start experiments, including
  OpenEvolve/OpenRouter configuration, evaluator and benchmark helpers,
  progress plotting, usage notes, and regression tests.

## 0.3.1 - 2026-06-11

- Improve small cycle-type Touchard counting by folding complementary subset
  sums for `n <= 64`, reducing redundant cached one-cycle lookups while leaving
  larger explicit Touchard workloads on the previous summation path.

## 0.3.0

- Previous published release.
