# Literature Synthesis

This note summarizes what the current local literature cache suggests about
the package's methods and about the historical status of the Touchard
cycle-type formula.

## Situation 1: Extension Counting Is Standard Rook/Permanent Machinery

The general one-row extension problem is already part of the standard
Latin-rectangle literature. Godsil-McKay attach a bipartite forbidden graph to
a `k x n` Latin rectangle and identify one-row extensions with perfect
matchings in the complement. Their rook/matching polynomial setup then gives
the inclusion-exclusion machinery used by this package.

Consequence:

- We should not describe the permanent, complement graph, or rook-polynomial
  framework as new.
- The general `k -> k + 1` implementation should be documented as an exact
  computational realization of this known framework.

## Situation 2: The `k = 2` Cycle Decomposition Is Immediate But Needs A Citation Check

For `k = 2`, normalize the first row to the identity and write the second row
as a derangement `pi`. The forbidden graph is the union of the identity
matching and the matching given by `pi`. A cycle of length `l` in `pi` becomes
an even cycle component `C_{2l}` in the forbidden bipartite graph.

Consequence:

- The extension count depends only on the full cycle type of `pi`.
- The product of one-cycle rook polynomials is the natural exact method.
- This statement follows directly from Godsil-McKay's graph construction, but
  we have not yet found it stated explicitly as a fixed-cycle-type theorem.

## Situation 3: The Touchard Formula Is Touchard 1934

The one-cycle `k = 2` case is the reduced menage problem. Riordan's book and
Stones et al. connect menage numbers to normalized three-line Latin rectangle
counts. Touchard 1934 has now been acquired and is stronger than mere
one-cycle background: it states a general discordant-permutation formula over
the relative cycle lengths of two given permutations.

In Touchard's notation, if the relative substitution between two given
permutations has `h` fixed points and nontrivial cycle lengths
`p_1, ..., p_s`, the count is a sum of terms
`phi(h; p_1 +/- p_2 +/- ... +/- p_s)` over `2^(s-1)` sign choices. Using
Touchard's evenness convention `phi(h; -n) = phi(h; n)`, this is exactly the
same as the package's half-sum over all sign vectors. The Latin-rectangle case
is the specialization `h = 0`, with `p_i = l_i`.

Wyman-Moser and Kaplansky-Riordan also show that formal endpoint values for
menage-related sequences are part of the classical algebraic setup.

Consequence:

- For `s >= 2`, our `M_s` can be described as the one-cycle menage/extension
  count.
- `M_0 = 2` and `M_1 = -1` must be introduced as formal values in this repo's
  Chebyshev normalization.
- Do not conflate this with Riordan's aggregate formula convention, where
  Stones et al. discuss `u_0 = 1` and the required formal value `u_1 = -1`.
- Treat the multi-cycle Touchard sum as Touchard's discordant-permutation formula
  written in this repo's `M_s` normalization, not as a new combinatorial
  theorem.

## Situation 4: The Chebyshev Step Is Known Matching-Polynomial Theory

Drake explicitly states that matching polynomials of cycles give Chebyshev
polynomials of the first kind. Kaplansky-Riordan also uses a Tchebycheff
representation for menage polynomials and derives a sign-iteration identity
that is algebraically close to our Touchard expansion.

Consequence:

- The Touchard derivation should be framed as a compact Chebyshev rewrite of
  rook/matching polynomial facts.
- It is probably not historically independent of the menage-polynomial
  literature.
- A final citation should prefer a primary matching-polynomial source if we
  acquire one, with Drake as a useful modern guide.

## Situation 5: Gessel Is Adjacent But Not A Fixed-Cycle-Type Formula

Gessel 1986 counts pairs `(pi, sigma)` such that `pi`, `sigma`, and
`pi sigma^{-1}` are derangements, refined by the number of cycles of `pi` and
the number of cycles of `sigma`. That is very close to the normalized
three-line Latin rectangle problem, but it aggregates over all derangements
with the same number of cycles.

Consequence:

- Gessel is important context but does not currently settle the fixed prescribed
  `pi` problem.
- We should avoid claiming a clean separation until the proof is read carefully
  for hidden cycle-index refinements.

## Situation 6: Touchard Is The Primary Formula Source; Shevelev Is The Latin-Rectangle Bridge

Stones et al. report that Moser generalized Riordan's formula to count
normalized three-line Latin rectangles where the second-row derangement avoids
cycle lengths from a set `S`, and that Shevelev gave a related formula where
cycle lengths belong to `S`. Shevelev 1992 has now been acquired and is stronger
than the secondary descriptions suggested: it gives an abstract `F`-parameter
generalization, a cycle-count refinement, and a fixed relative-cycle-structure
formula based on Touchard's discordant-permutation count. Touchard 1934 directly
gives the sign-combination formula; Shevelev 1992 is important because it places
that machinery back into the Latin-rectangle literature and connects it with
Moser's cycle-length sieving.

Consequence:

- Touchard 1934 is the closest acquired source for the Touchard identity
  itself.
- Shevelev 1992 is the closest acquired Latin-rectangle source using the same
  fixed relative-cycle-structure machinery.
- Moser 1982 and Shevelev 1991 still need direct acquisition, but Shevelev 1992
  already shows that the relevant fixed-cycle machinery is in the Latin-rectangle
  literature.
- The package's Touchard presentation is best treated as a modern notation and
  computational implementation of Touchard's formula, not a materially distinct
  formula.

## Current Best Claim

The current defensible wording is:

> The Touchard count is Touchard's 1934 formula for permutations discordant
> with two given permutations, specialized to the no-fixed-point relative cycle
> structure that occurs in `2 x n -> 3 x n` Latin rectangle extensions. The
> package also derives this specialization from the Godsil-McKay
> extension/perfect-matching framework: in the `k = 2` case the forbidden graph
> decomposes into even cycles, and the Chebyshev form of cycle matching
> polynomials gives the same sign-sum expression.

Avoid stronger wording such as "new formula" or "first explicit formula". That
language is not currently defensible after reading Touchard 1934 and Shevelev
1992.

## Implications For Code And Docs

- Keep both Touchard and rook-polynomial paths documented as equivalent exact
  realizations of the same inclusion-exclusion calculation.
- Cite Godsil-McKay for the general extension framework.
- Cite Touchard 1934 for the Touchard identity.
- Cite Riordan/menage sources for one-cycle values after distinguishing the
  formal-value convention.
- Cite a cycle matching-polynomial/Chebyshev source for `q_l(t)`.
- Add a "historical status" note rather than a novelty claim in public docs.
- Mention Shevelev 1992 as the closest acquired Latin-rectangle bridge for the
  fixed relative-cycle-structure machinery.
