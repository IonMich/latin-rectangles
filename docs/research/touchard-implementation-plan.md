# Touchard Implementation Plan

This plan follows from the stored research note in
`docs/research/chatgpt-5-5-extended-thinking-latin-rectangle-extension-response.md`.
The goal is to turn Touchard's Chebyshev/sign-sum identity into a tested,
maintainable improvement for the existing 2-row extension counter while keeping
the general `k -> k+1` path separate.

## Scope

Implement items 1-5 first. Items 6-7 are follow-up probes and should not block
the Touchard work.

## 1. Add Tests First

Add focused tests before changing behavior.

- Cross-check a Touchard helper against the current rook-polynomial
  implementation for every valid cycle structure through a modest `n`.
- Include explicit regression cases for the formal correction terms
  `M_0 = 2` and `M_1 = -1`.
- Preserve the examples from the research note:
  - `E(3,4) = M_7 + M_1 = 578`
  - `E(2,2,2,2) = M_8 + 4M_4 + 3M_0 = 4752`
- Keep the `count_extensions([identity, p]) == count_extensions_from_derangement(p)`
  equivalence tests, because the general path should continue to validate the
  2-row public behavior.

## 2. Add a Touchard Counting Path

Add an internal 2-row implementation based on:

```text
E(lambda) = 1/2 * sum_s multiplicity(s) * M_|s|
```

Use subset-sum dynamic programming over cycle lengths rather than enumerating
all `2^c` sign vectors:

```text
touchard_index = 2 * subset_sum - n
E(lambda) = 1/2 * sum_a count_subsets_with_sum_a(lambda) * M_|2a-n|
```

Keep the implementation exact and integer-only.

## 3. Reuse One-Cycle Counts in Cycle-Structure Enumeration

Target the Touchard path first at cycle-structure inputs and `--all`
enumeration, where one-cycle values `M_s` are reused across many cycle types.

- Cache `M_s = F(q_s)` values, with formal values `M_0 = 2` and `M_1 = -1`.
- Preserve the existing public APIs unless benchmarks justify adding an
  explicit option.
- Benchmark `enumerate_all_extensions(n)` before and after for representative
  values such as `n = 30, 40, 50`.

## 4. Fix or Deprecate the Floating FFT Path

The current `use_fft=True` path uses floating-point convolution and can return
incorrect exact counts for moderate inputs. Before claiming FFT performance:

- Add a failing regression case around all 2-cycles at `n = 40`.
- Either guard/deprecate `use_fft=True` for exact counting, or replace it with
  an exact modular convolution/NTT approach.
- Update tests and documentation so exactness expectations are clear.

## 5. Document the Polynomial Convention

Document the relation between the repo's positive rook polynomials and the
research note's signed/reversed cycle polynomials `q_l(t)`.

- Explain where the signs and degree reversal enter the inclusion-exclusion
  functional.
- State that `M_0` and `M_1` are formal correction terms, not genuine Latin
  extension counts.
- Add concise comments near any Touchard helper so the identity is auditable
  from code.

## 6. Preserve the General `k -> k+1` Boundary

Do not replace `general_extensions.py` with Touchard's formula. The
Chebyshev identity is special to the 2-row case, where forbidden components are
cycle graphs.

Use the general method only as a consistency check for 2-row inputs.

## 7. Consider Input Validation Hardening

After the Touchard work, consider adding full permutation validation to
`count_extensions`. It currently rejects fixed points but does not fully verify
that the input is a valid 1-indexed permutation.
