# Literature Attribution Notes

This is a live attribution map for the `2 x n -> 3 x n` extension-counting
formulae in this repository. It is not a finished literature review. Its main
purpose is to keep attribution and scope claims accurate while we check the
remaining sources.

## Current Position

The right public posture is:

- The permanent/rook-polynomial formulation of one-row extensions is standard.
- In the `k = 2` case, the forbidden graph decomposes into even cycles
  determined by the cycle type of the second-row derangement.
- The Touchard formula is best attributed to Touchard 1934: it is his
  formula for permutations discordant with two fixed permutations, specialized
  to a relative permutation with no fixed points.
- The package's Chebyshev/rook derivation is an implementation-oriented
  rederivation and normalization of Touchard's formula, not a claimed new
  theorem.
- Shevelev 1992 applies this fixed relative-cycle-structure machinery in the
  Latin-rectangle setting.
- Shevelev 1992 also identifies Moser's cycle-length sieving as a
  specialization.
- The strongest remaining acquisition gaps are Moser 1982 and Shevelev 1991.

Avoid language like "new formula" or "first known formula". A safer sentence is:

> This is Touchard's 1934 discordant-permutation formula specialized to the
> no-fixed-point relative cycle structure of a normalized `2 x n` Latin
> rectangle. Equivalently, it follows by specializing the Godsil-McKay
> extension/rook-polynomial framework to the case where the forbidden graph is a
> disjoint union of cycles and using the Chebyshev form of the cycle matching
> polynomial.

## Verified So Far

### Godsil-McKay Framework

Godsil and McKay associate to a `k x n` Latin rectangle `L` a `k`-regular
bipartite graph `G(L)` on column vertices and symbol vertices. Their Lemma 2.1
states that the number of one-row extensions is the number of perfect matchings
in `K_{n,n}` containing no edge of `G(L)`.

Consequences for this repo:

- The permanent-of-the-allowed-matrix view is not novel.
- The rook/matching polynomial inclusion-exclusion view is not novel.
- The general `k x n -> (k + 1) x n` implementation is aligned with this
  standard formulation.

### Specialization To `k = 2`

After normalizing the first row to the identity, the second row is a
derangement `pi`. The forbidden graph is the union of two perfect matchings:

- identity edges `(i, i)`,
- second-row edges `(i, pi(i))`.

If `pi` has cycle type `lambda = (l_1, ..., l_c)`, this graph decomposes as

```text
C_{2l_1} disjoint-union ... disjoint-union C_{2l_c}.
```

This appears to be an immediate specialization of Godsil-McKay's construction.
We have not yet found a source that states this exact sentence in this exact
form.

Consequences for this repo:

- The extension count depends only on the full cycle type of `pi`.
- Multiplying one-cycle rook polynomials is the natural component factorization.
- The Touchard method is special to `k = 2`; it should not be applied to the
  general `k -> k + 1` code path.

### Menage, Riordan, And Formal Values

The one-cycle case is the classical menage problem. Stones et al. cite the
Touchard/Riordan formula for menage numbers and explain that Riordan's formula
for `K_{3,n}` requires a formal value `u_1 = -1`, even though that does not
match the direct permutation-count interpretation.

Our Touchard normalization is related but not identical:

```text
M_s = F(q_s)
M_0 = 2
M_1 = -1
```

For `s >= 2`, `M_s` is the genuine one-cycle extension count. `M_0` and `M_1`
are formal Chebyshev/product-rule correction terms. Documentation should define
`M_s` from `q_s` rather than simply call all `M_s` "the menage numbers".

### Chebyshev Matching Polynomial

Matching polynomials of paths and cycles are classical orthogonal-polynomial
objects. In the notation used by this repo,

```text
q_l(t) = sum_{j=0}^l (-1)^j m_j(C_{2l}) t^{l-j}
       = 2 T_l((t - 2) / 2).
```

Equivalently, if `y + y^{-1} = t - 2`, then

```text
q_l(t) = y^l + y^{-l}.
```

This gives the product rule

```text
q_a(t) q_b(t) = q_{a+b}(t) + q_{|a-b|}(t),
```

and therefore Touchard's formula

```text
E(l_1, ..., l_c)
  = (1/2) sum_{epsilon in {-1,+1}^c}
      M_|epsilon_1 l_1 + ... + epsilon_c l_c|.
```

This derivation is solid, but it should be presented as a rederivation of
Touchard's formula in package notation. Touchard 1934 already contains the same
general fixed relative-cycle-structure sign-combination shape; the remaining question
is how best to describe this repo's compact `M_s` normalization and algorithmic
factorization.

## Sources To Check Next

| Priority | Source | Why it matters | Current status |
| --- | --- | --- | --- |
| 1 | W. O. J. Moser, "A generalization of Riordan's formula for 3xn latin rectangles", Discrete Math. 40, 311-313 (1982). | Stones et al. say this counts normalized three-line Latin rectangles where second-row cycle lengths do not belong to a set `S`. This is the closest known source to a cycle-type-level refinement. | Bibliographic record found. Full paper still needs direct reading. |
| 1 | V. S. Shevelev, "The Riordan generalized formula for three-line Latin rectangles and its applications", DAN of the Ukraine 2, 8-12 (1991). | Stones et al. say this gives the complementary cycle-length-in-`S` generalization. | Bibliographic record found; likely Russian. Needs acquisition/translation. |
| 1 | V. S. Shevelev, "Reduced Latin rectangles and square matrices with identical sums in the rows and columns", Diskret. Mat. 4(1), 91-110 (1992). | Gives an `F`-generalized Riordan formula, a refinement by cycle count, and a fixed relative-cycle-structure formula. Also identifies Moser's cycle-sieving formula as a specialization. | PDF acquired from Math-Net; extracted text is searchable but formulae need visual checks. |
| 2 | J. Riordan, "Three-line Latin rectangles" (1944), "Three-line Latin rectangles-II" (1946), and "A recurrence relation for three-line Latin rectangles" (1952). | Establishes the classical formulae, recurrence, and normalization conventions. | References identified. Originals not yet checked. |
| 2 | J. Riordan, An Introduction to Combinatorial Analysis, especially the three-line Latin rectangle discussion. | Likely source for the standard exposition and `u_1 = -1` convention. | Reference identified. Needs direct page check. |
| 2 | I. M. Gessel, "Counting three-line Latin rectangles" (1986) and "Counting Latin rectangles" (1987). | Counts pairs of discordant derangements by number of cycles. Adjacent to fixed-`pi` extension counts, but not obviously a fixed-cycle-type formula. | PDF/records found. Needs careful proof-level reading. |
| 1 | Touchard 1934 and classical menage literature. | Primary source for the discordant-permutation sign-combination formula; the package formula is its `h = 0` specialization. | Touchard 1934 acquired from Gallica/BnF page images; OCR is searchable but formulae need visual checks. Touchard 1953 is still missing. |
| 3 | Godsil-Gutman and Godsil matching-polynomial papers; Drake 2009. | Useful for exact historical normalization of the cycle/Chebyshev matching-polynomial identity. | Secondary/modern source found; primary matching-polynomial sources still need checking. |

## Specific Questions For The Next Literature Pass

1. Does Moser 1982 give only aggregate counts over cycle-length restrictions,
   or does it contain a fixed-cycle-type or coefficient-extraction formula from
   which Touchard's formula is immediate in Latin-rectangle notation?
2. Does Shevelev refine Moser's formula in a way that records individual cycle
   counts by length?
3. Do Gessel's generating functions include enough cycle-index variables to
   recover a fixed prescribed `pi`, or only aggregate statistics such as the
   number of cycles?
4. Which source is best for citing the exact identity
   `q_l(t) = 2 T_l((t - 2) / 2)` for cycle matching polynomials?
5. Which classical source is best for the formal values in the menage sequence,
   and how should we distinguish Riordan's `u_0 = 1` convention from this repo's
   `M_0 = 2` convention?

## Documentation Consequences

When updating public-facing docs or a Math.SE answer:

- Cite Godsil-McKay for the extension/perfect-matching framework.
- Cite Touchard 1934 for Touchard's formula itself.
- State that the `k = 2` forbidden graph decomposes into `C_{2l}` components.
- Define `q_l(t)`, `F`, and `M_s` explicitly before writing Touchard's formula.
- Call `M_0 = 2` and `M_1 = -1` formal values in this normalization.
- Cite Riordan/menage sources for the one-cycle case, once checked directly.
- Mention Touchard 1934 and Shevelev 1992 directly as prior
  fixed-cycle-structure machinery, while noting that Moser 1982 and Shevelev
  1991 remain acquisition gaps.

## Links And Bibliographic Leads

- Godsil and McKay, "Asymptotic enumeration of Latin rectangles":
  <https://users.cecs.anu.edu.au/~bdm/papers/LatinRectangles.pdf>
- Stones, Lin, Liu, and Wang, "On Computing the Number of Latin Rectangles":
  <https://link.springer.com/article/10.1007/s00373-015-1643-1>
- Stones, "The Many Formulae for the Number of Latin Rectangles":
  <https://www.combinatorics.org/ojs/index.php/eljc/article/view/v17i1a1>
- Gessel, "Counting Three-Line Latin Rectangles":
  <https://people.brandeis.edu/~gessel/homepage/papers/3latin.pdf>
- DBLP record for Moser's publication list:
  <https://dblp.org/pid/64/6308.html>
- Pascal-Francis record for Moser 1982:
  <https://pascal-francis.inist.fr/vibad/index.php?action=getRecordDetail&idt=PASCAL82X0371080>
- OEIS A000186 references around Riordan, Moser, and Shevelev:
  <https://oeis.org/A000186>
- Drake, "Higher order matching polynomials and d-orthogonality":
  <https://arxiv.org/pdf/0909.1655>
