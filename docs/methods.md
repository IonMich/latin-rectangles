# Counting Methods And Notation

This document explains the mathematical objects used by the package and how
they map to the implemented algorithms.

The package has three related counting paths:

1. the specialized `2 x n -> 3 x n` rook-polynomial method,
2. the Touchard cycle-structure method for the same `2 x n -> 3 x n`
   problem,
3. the general `k x n -> (k + 1) x n` method based on connected components of
   the forbidden bipartite graph.

The optional `use_fft=True` flag affects only polynomial multiplication. It is
exact: the implementation uses number-theoretic transforms (NTT) and Chinese
remainder reconstruction (CRT), not rounded floating-point FFT arithmetic.

## 1. Basic Objects

Let `[n] = {1, 2, ..., n}`.

A row of a Latin rectangle is represented as a permutation of `[n]`. In the
Python API, rows are 1-indexed lists of length `n + 1`, with index `0` unused.

For example:

```python
[0, 2, 3, 1]
```

represents the permutation `1 -> 2`, `2 -> 3`, `3 -> 1`.

For a `2 x n` Latin rectangle, the first row can be normalized to the identity:

```text
column:  1  2  ...  n
row 1:   1  2  ...  n
row 2:   pi(1) pi(2) ... pi(n)
```

Because the two rows must differ in every column, `pi` is a derangement:

```text
pi(i) != i for every i in [n].
```

A valid third row is a permutation `sigma` of `[n]` such that, for every
column `i`,

```text
sigma(i) != i
sigma(i) != pi(i).
```

The count of such `sigma` is denoted:

```text
E(pi)
```

or, when only the cycle lengths of `pi` matter,

```text
E(l_1, ..., l_c).
```

Here:

| Symbol | Meaning |
| --- | --- |
| `n` | number of columns and symbols |
| `pi` | second-row permutation after normalizing row 1 to identity |
| `lambda = (l_1, ..., l_c)` | cycle type of `pi` |
| `c` | number of cycles in `pi` |
| `l_r` | length of cycle `r`; for derangements, `l_r >= 2` |
| `sigma` | candidate next-row permutation |
| `E(pi)` | number of valid next rows |
| `E(l_1, ..., l_c)` | same count, expressed by cycle type |

## 2. Rook Formula For The `2 x n` Case

Define a forbidden board `B` with rows indexed by columns and columns indexed by
symbols. The forbidden squares are:

```text
(i, i)       for row 1
(i, pi(i))  for row 2
```

A valid third row is exactly a permutation matrix that avoids all forbidden
squares.

Let `r_j` be the number of ways to place `j` nonattacking rooks on the
forbidden board `B`. Equivalently, `r_j` is the number of size-`j` matchings in
the forbidden bipartite graph.

By inclusion-exclusion:

```text
E(pi) = sum_{j=0}^n (-1)^j r_j (n - j)!.
```

The package implements this functional in
`latin_rectangles.extension_counting._apply_inclusion_exclusion`.

## 3. Cycle Components And Rook Polynomials

If a cycle of `pi` has length `l`, its forbidden component is a cycle graph
with `2l` vertices, written `C_{2l}`.

Let:

```text
m_j(C_{2l}) = number of j-edge matchings in C_{2l}.
```

For `0 <= j <= l`, the matching numbers are:

```text
m_j(C_{2l}) = (2l / (2l - j)) * binom(2l - j, j).
```

The implementation stores the positive rook polynomial for one cycle as a list
of coefficients in increasing degree:

```text
R_l(x) = sum_{j=0}^l m_j(C_{2l}) x^j.
```

For a cycle type `lambda = (l_1, ..., l_c)`, the full rook polynomial is:

```text
R_lambda(x) = R_{l_1}(x) R_{l_2}(x) ... R_{l_c}(x).
```

If:

```text
R_lambda(x) = sum_{j=0}^n r_j x^j,
```

then applying the inclusion-exclusion formula above gives `E(lambda)`.

Implementation mapping:

| Function | Role |
| --- | --- |
| `get_rook_polynomial_for_cycle(l)` | compute `R_l(x)` |
| `multiply_polynomials(a, b)` | exact schoolbook product |
| `multiply_polynomials_fft(a, b)` | exact NTT/CRT product for large dense inputs |
| `count_extensions(pi)` | decompose `pi`, multiply cycle rook polynomials, apply inclusion-exclusion |

## 4. Touchard/Reversed Cycle Polynomial

The Touchard method uses a different polynomial convention for the same
cycle data.

For a cycle length `l`, define:

```text
q_l(t) = sum_{j=0}^l (-1)^j m_j(C_{2l}) t^{l - j}.
```

This is related to the positive rook polynomial by:

```text
q_l(t) = t^l R_l(-1/t).
```

Define a linear functional `F` by:

```text
F(t^d) = d!
```

and extend it linearly:

```text
F(a_0 + a_1 t + ... + a_n t^n)
  = a_0 0! + a_1 1! + ... + a_n n!.
```

For one cycle:

```text
M_l = F(q_l).
```

For `l >= 2`, `M_l` is the genuine extension count for a single `l`-cycle.
Touchard's identity also uses two formal values:

```text
M_0 = 2
M_1 = -1
```

These are not Latin rectangle counts for real 0- or 1-cycles. They are
bookkeeping values needed by the polynomial product identity.

For a full cycle type:

```text
E(l_1, ..., l_c) = F(q_{l_1}(t) q_{l_2}(t) ... q_{l_c}(t)).
```

This is the same inclusion-exclusion calculation as the positive rook
polynomial method, just expressed in reversed signed coefficients.

## 5. Derivation Of Touchard's Formula

Historically, this identity should be attributed to Touchard's 1934 formula for
permutations discordant with two given permutations. Touchard's notation sums
over `2^(c-1)` sign choices with the first sign fixed; using his evenness
convention for the one-cycle function gives the equivalent `1/2` times the sum
over all `2^c` sign vectors below. The derivation here explains why the same
formula follows from the package's rook-polynomial convention and how the
implemented `M_s` values are computed.

The key identity is:

```text
q_l(t) = 2 T_l((t - 2) / 2),
```

where `T_l` is the Chebyshev polynomial of the first kind.

Equivalently, introduce a formal auxiliary variable `y` satisfying:

```text
y + y^{-1} = t - 2.
```

Then:

```text
q_l(t) = y^l + y^{-l}.
```

For two cycle lengths `a` and `b`:

```text
q_a(t) q_b(t)
  = (y^a + y^{-a})(y^b + y^{-b})
  = y^{a+b} + y^{a-b} + y^{-a+b} + y^{-(a+b)}
  = (y^{a+b} + y^{-(a+b)}) + (y^{a-b} + y^{-(a-b)})
  = q_{a+b}(t) + q_{|a-b|}(t).
```

For many cycle lengths, expand:

```text
q_{l_1}(t) ... q_{l_c}(t)
  = product_{r=1}^c (y^{l_r} + y^{-l_r}).
```

For each cycle index `r`, choose one of the two terms:

```text
y^{l_r}   or   y^{-l_r}.
```

Encode that choice by a sign:

```text
epsilon_r in {-1, +1}.
```

A sign vector is:

```text
epsilon = (epsilon_1, ..., epsilon_c) in {-1, +1}^c.
```

For one sign vector, define the signed sum:

```text
S(epsilon) = sum_{r=1}^c epsilon_r l_r.
```

The product expansion is:

```text
q_{l_1}(t) ... q_{l_c}(t)
  = sum_{epsilon in {-1,+1}^c} y^{S(epsilon)}.
```

The opposite sign vector `-epsilon` contributes:

```text
y^{-S(epsilon)}.
```

These two terms pair to:

```text
y^{S(epsilon)} + y^{-S(epsilon)}
  = q_{|S(epsilon)|}(t).
```

If we sum `q_{|S(epsilon)|}(t)` over all sign vectors, each pair
`epsilon, -epsilon` is counted twice. Therefore:

```text
q_{l_1}(t) ... q_{l_c}(t)
  = (1/2) sum_{epsilon in {-1,+1}^c} q_{|S(epsilon)|}(t).
```

Apply the linear functional `F`:

```text
E(l_1, ..., l_c)
  = F(q_{l_1}(t) ... q_{l_c}(t))
  = (1/2) sum_{epsilon in {-1,+1}^c} F(q_{|S(epsilon)|}(t))
  = (1/2) sum_{epsilon in {-1,+1}^c} M_{|S(epsilon)|}.
```

Written without the abbreviation `S`:

```text
E(l_1, ..., l_c)
  = (1/2) sum_{epsilon in {-1,+1}^c}
      M_{|sum_{r=1}^c epsilon_r l_r|}.
```

The inner index `r` runs over cycles. The outer variable `epsilon` is the whole
sign vector. There is no separate outer sum over `i`; the signs are components
of the vector `epsilon`.

## 6. Subset-Sum Form Used In Code

Directly summing over all `2^c` sign vectors is avoidable.

Let `A` be the set of cycle indices assigned sign `+1`. Let:

```text
a = sum_{r in A} l_r
n = sum_{r=1}^c l_r.
```

Then the signed sum is:

```text
S = a - (n - a) = 2a - n.
```

So Touchard's formula becomes:

```text
E(l_1, ..., l_c)
  = (1/2) sum_{a=0}^n N(a) M_{|2a - n|},
```

where:

```text
N(a) = number of subsets of cycle lengths with total a.
```

The implementation computes the numbers `N(a)` by subset-sum dynamic
programming. This is the function:

```text
latin_rectangles.extension_counting._count_cycle_structure_extensions_touchard
```

This path is especially useful when enumerating many cycle structures for the
same `n`, because all one-cycle values `M_s` are cached.

Performance note:

- few large cycles: the Touchard method is often fastest,
- many small cycles in one isolated query: the original rook-polynomial method
  can still be faster,
- all-cycle-type enumeration: Touchard-value reuse is valuable.

## 7. Exact NTT/CRT Polynomial Multiplication

The public API still names the option `use_fft=True` for compatibility, but the
implementation is not a floating-point FFT.

The exact transform path is:

1. choose enough primes `p_i` such that each `p_i = k_i * N + 1`, where `N` is
   the transform length,
2. compute a number-theoretic transform modulo each `p_i`,
3. multiply pointwise modulo each `p_i`,
4. invert the transform modulo each `p_i`,
5. reconstruct integer coefficients by CRT,
6. convert residues larger than half the combined modulus back to negative
   integers.

The implementation chooses enough 31-bit NTT primes so that the product of
the primes exceeds twice a conservative coefficient bound:

```text
2 * min(len(a), len(b)) * max_abs(a) * max_abs(b).
```

This guarantees exact reconstruction of every coefficient.

The NTT path falls back to schoolbook multiplication when one factor is small,
the product is skinny, or the coefficient bound would require many CRT primes.
The last guard matters for rook polynomials: their coefficients become large
enough that exact reconstruction can require dozens of modular convolutions,
which can dominate the asymptotic advantage of the transform.

Implementation mapping:

| Function | Role |
| --- | --- |
| `multiply_polynomials` | schoolbook exact multiplication |
| `multiply_polynomials_fft` | exact NTT/CRT multiplication |
| `count_extensions(..., use_fft=True)` | uses exact NTT/CRT for polynomial products |
| `count_extensions_k(..., use_fft=True)` | same exact transform option for component products |

## 8. General `k x n -> (k + 1) x n` Method

For `k` existing rows, let the rows be permutations:

```text
sigma_1, sigma_2, ..., sigma_k.
```

The first row may be non-identity. The implementation standardizes it by
relabeling symbols with `sigma_1^{-1}`, so the first row becomes identity.
This does not change the number of valid extensions.

If `k = 1`, the problem is just to choose a next row that avoids the only
existing row in every column. After standardization, this is the number of
derangements of `[n]`, written `!n`. The implementation handles this case
directly in `O(n)` using:

```text
!0 = 1
!1 = 0
!n = (n - 1)(!(n - 1) + !(n - 2)).
```

The component matching dynamic program is used only when `k >= 2`.

For each column `j`, the forbidden symbols are:

```text
sigma_1(j), sigma_2(j), ..., sigma_k(j).
```

Build the forbidden bipartite graph `F`:

- left vertices are columns,
- right vertices are symbols,
- edge `(j, sigma_r(j))` is forbidden for every row `r`.

The number of extensions is the permanent of the allowed matrix, equivalently:

```text
sum_{t=0}^n (-1)^t r_t (n - t)!,
```

where `r_t` is the number of size-`t` matchings in `F`.

The rook polynomial of `F` factors over connected components. After
standardization, those components are the orbits of the group generated by:

```text
sigma_2, ..., sigma_k.
```

For each orbit/component, the implementation computes the component matching
polynomial by a memoized branching dynamic program over bit masks of remaining
left and right vertices. The component polynomials are multiplied and the same
inclusion-exclusion functional is applied.

Implementation mapping:

| Function | Role |
| --- | --- |
| `_standardize_rows` | normalize the first row to identity |
| `_compute_orbits` | find forbidden graph components via generated orbits |
| `_component_matching_polynomial` | compute one component rook polynomial |
| `count_extensions_k` | multiply components and apply inclusion-exclusion |

Complexity is exponential in the largest component size, which is expected for
the general permanent/counting problem. It is practical when components/orbits
are small.

## 9. Which Method Should Be Used?

| Task | Recommended path |
| --- | --- |
| Count one arbitrary derangement | `count_extensions(permutation)` |
| Count one cycle structure | `count_cycle_structure_extensions(cycle_lengths)`, using auto routing |
| Enumerate all cycle structures for a fixed `n` | CLI `--all`, using Touchard-value reuse |
| Count general `k x n -> (k + 1) x n` extensions | `count_extensions_k(rows)` |
| External dense polynomial products with modest coefficient bounds | pass `use_fft=True` to allow exact NTT/CRT |

The methods are intentionally kept side by side. Touchard's identity is
special to the `2 x n` case, while the general `k`-row method handles broader
inputs at the cost of exponential worst-case behavior.
